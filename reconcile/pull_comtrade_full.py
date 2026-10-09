# -*- coding: utf-8 -*-
"""Full-universe UN Comtrade crawl: ALL HS6 products, all reporters, MONTHLY, newest year first.

WHY THIS EXISTS
reconcile/reconcile.py deflates CIF imports to an FOB basis with a per-product MEDIAN markup rather
than BACI's gravity regression, and its own step 2 says why: on our 31-code slice distance is
unidentified - measured R^2 = 0.01. That is a statement about the SLICE, not the method. This crawl
fetches the universe so the question can be settled, and because a complete monthly Comtrade corpus
is an asset in its own right for work not yet specified.

THE CAP IS THE WHOLE PROBLEM, AND IT HAS NO PAGINATION
A free key returns at most 100,000 records per call and the API offers no offset/skip/page: once a
query exceeds the cap you cannot fetch the remainder, you can only ask a narrower question. So the
floor on the whole job is simply TOTAL RECORDS / 100,000, however it is sliced. Measured with
countOnly: one month of world HS6 trade is 41.9M records (26.3M imports + 15.6M exports), so
2000-2026 is ~13.6 billion records and ~136,000 calls at perfect packing.

WHICH SPLITS ACTUALLY WORK - measured, not assumed (Germany, 202301, imports = 3,732,870 records):
    period as a comma list          WORKS   '202301,202302,...'
    cmdCode as an explicit HS6 list WORKS   2 codes -> 2,040 records, 10 codes -> 3,379
    partnerCode as a comma list     WORKS as a parameter, but INSUFFICIENT on its own:
                                    Germany<-China alone is 289,318 records in one month
    cmdCode as an HS2 chapter       DOES NOT give HS6 detail - returns the aggregate line
So the primary split is the CODE LIST, which can always be subdivided further, down to one code.
Partner splitting is kept as a last resort for the pathological case of a single code in a single
month exceeding the cap.

NEVER STORE A TRUNCATED PAGE AS IF IT WERE WHOLE
The previous version's window ladder bottomed out at one month and then wrote whatever came back,
warning only to stdout. Most big reporters exceed the cap in a single month - 7 of 10 sampled, and
Germany needs ~38 splits - so that version would have silently produced an incomplete corpus that
looked complete. Here a response at the cap is never written: the chunk is subdivided and retried,
and a chunk that cannot be subdivided further is recorded in state['stuck'] rather than saved.

ASK WHO FILED BEFORE ASKING WHAT THEY FILED
Most countries never filed monthly data at all, and a sizing call per (reporter, year, flow) is
470 a year - 12,690 over 2000-2026 - most of them returning zero. The availability endpoint
(/public/v1/getDa/C/M/HS?period=YYYYMM) lists exactly which reporters filed a given month, one call
per period: 12 a year, 324 in total. That is about 32 days of budget not spent on empties.
It also shows the real shape of the corpus: 22 reporters filed for 200001, 130 for 202001.

SIZING BEFORE FETCHING
countOnly asks how many records a query WOULD return without returning them. One such call per
(reporter, year, flow) that ACTUALLY FILED is enough to choose the chunking for that whole year,
and it avoids burning big fetches on queries that were always going to be truncated.

IT MUST NOT STARVE THE NIGHTLY REFRESH
pipeline/refresh.py pulls Comtrade from the same key against the same 500/day allowance, and
adapter_comtrade.py puts an 18-month backfill at ~114 calls. The default budget here is 380.

    python reconcile/pull_comtrade_full.py --plan          # the schedule, no network
    python reconcile/pull_comtrade_full.py --size 2024     # countOnly sizing for one year
    python reconcile/pull_comtrade_full.py                 # a day's crawl, budget 380
    python reconcile/pull_comtrade_full.py --years 2026 2025 --budget 100

The key is read from pipeline/.comtrade_key or $COMTRADE_KEY and is never printed or logged.
"""
import argparse
import datetime
import io
import json
import math
import os
import sys
import time
import urllib.request

import pandas as pd

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

OUTDIR = os.environ.get('CMA_CRAWL_DIR', os.path.join(ROOT, 'raw', 'comtrade_full'))
STATE = os.path.join(OUTDIR, '_state.json')
BASE = 'https://comtradeapi.un.org/data/v1/get/C/M/HS'
AVAIL = 'https://comtradeapi.un.org/public/v1/getDa/C/M/HS'

UA = 'Mozilla/5.0'     # the reference files are served to a browser agent
PARTNER_REF = 'https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json'

# A cmdCode list of 18,843 characters was refused outright with HTTP 414 on 9 Oct 2026. Codes are
# now only ever a LAST-resort axis, and never in groups big enough to put the query string at risk.
MAX_CMD_CHARS = 1800
CODES_PER_CALL = MAX_CMD_CHARS // 7        # 6 digits and a comma

# Rows actually delivered per call, measured 9 Oct 2026 on the partner axis: 604,274 rows in 14
# calls. Below TARGET because a response that comes back at the cap is split and refetched.
ROWS_PER_CALL = 43162

PAGE_CAP = 100000      # hard: a response at this size is truncated, never complete
TARGET = 70000         # aim per call, leaving room for uneven code density
YEAR_MAX, YEAR_MIN = 2026, 2000
DEFAULT_BUDGET = 380   # per RUN; with 2 keys use --budget 880
PER_KEY_DAY = 500      # a free key's daily allowance
REFRESH_RESERVE = 120  # left for pipeline/refresh.py, which shares key #1


def _keys():
    """Every key we may spend today, in order. One per line in pipeline/.comtrade_key, or a
    comma-separated $COMTRADE_KEY. Each free key carries its own 500/day allowance.

    Never printed or logged - the crawler refers to them as key #1, key #2."""
    raw = os.environ.get('COMTRADE_KEY', '').strip()
    if not raw:
        p = os.path.join(ROOT, 'pipeline', '.comtrade_key')
        if os.path.exists(p):
            raw = io.open(p, encoding='utf-8').read()
    out = []
    for part in raw.replace(',', '\n').splitlines():
        part = part.strip()
        if part and not part.startswith('#') and part not in out:
            out.append(part)
    if not out:
        sys.exit('No Comtrade key: set $COMTRADE_KEY or create pipeline/.comtrade_key')
    return out


def _spent_today(st, n_keys):
    """Calls spent per key today, reset on a new calendar day.

    UTC, not local. The allowance is the service's to reset, and Azure API Management - which is
    what Comtrade runs on - counts its quota windows in UTC. Keyed on the local date instead, the
    ledger clears at local midnight: at UTC+2 that is 22:00 UTC the previous day, so a run in the
    first two hours of the morning would believe it had a fresh 880 while the UN still charged it
    to yesterday, and would spend the difference collecting 429s. The scheduled 05:00 run is clear
    of that window either way, but a manual one is not, and the local date also drags the reset
    time back and forth with daylight saving twice a year.
    """
    today = time.strftime('%Y-%m-%d', time.gmtime())
    led = st.setdefault('spend', {})
    if led.get('day') != today:
        led.clear()
        led['day'] = today
    for i in range(n_keys):
        led.setdefault(str(i), 0)
    return led


def reporters():
    import baci
    cc = pd.read_csv(baci.country_file(), keep_default_na=False, na_values=[''])
    return [(int(r.country_code), r.country_iso3) for r in cc.itertuples()
            if str(r.country_iso3).isalpha() and len(str(r.country_iso3)) == 3]


def partner_areas(st):
    """Every partner area Comtrade recognises, cached in state after one keyless fetch.

    Proven exhaustive 9 Oct 2026, by countOnly on one reporter-month: partnerCode='' returned
    195,412 and the explicit list of all 310 codes returned the identical 195,412, so a partition
    over this list loses nothing.

    World (0) MUST stay in the list. The same call without it returned 128,682, because
    partnerCode='' includes the World aggregate alongside the bilateral rows - which also means
    the stored files carry both, and nothing downstream may sum over partner without excluding 0.
    """
    cached = st.get('partners')
    if cached:
        return list(cached)
    try:
        req = urllib.request.Request(PARTNER_REF, headers={'User-Agent': UA})
        rows = json.load(urllib.request.urlopen(req, timeout=120))['results']
        got = sorted({int(r['PartnerCode']) for r in rows
                      if str(r.get('PartnerCode', '')).strip() != ''})
    except Exception as e:
        raise SystemExit('cannot read the partner reference list (%s: %s) - without it a split '
                         'by partner could silently omit partners, so the run stops here'
                         % (type(e).__name__, e))
    if 0 not in got:
        raise SystemExit('the partner reference list came back without World (0); refusing to '
                         'split on an incomplete partition')
    st['partners'] = got
    save_state(st)
    print('   partner areas: %d (reference file, no key, no quota)' % len(got), flush=True)
    return list(got)


def all_codes():
    """The HS6 universe, from the BACI product table (the one door - ARCHITECTURE.md phase 2)."""
    import baci
    p = pd.read_csv(baci.product_file(), dtype=str)
    col = [c for c in p.columns if 'code' in c.lower()][0]
    return sorted({str(c).zfill(6) for c in p[col].dropna() if str(c).strip().isdigit()})


def load_state():
    if os.path.exists(STATE):
        try:
            s = json.load(io.open(STATE, encoding='utf-8'))
        except ValueError:
            s = {}
    else:
        s = {}
    for k, v in (('done', {}), ('empty', {}), ('stuck', {}), ('size', {}),
                 ('calls', 0), ('rows', 0), ('started', None)):
        s.setdefault(k, v)
    return s


def save_state(st):
    os.makedirs(OUTDIR, exist_ok=True)
    tmp = STATE + '.tmp'
    io.open(tmp, 'w', encoding='utf-8').write(json.dumps(st, indent=1, sort_keys=True))
    os.replace(tmp, STATE)


def part_path(year, iso3, flow, tag):
    return os.path.join(OUTDIR, str(year), '%s_%s_%s.parquet' % (iso3, flow, tag))


COLS = ['period', 'reporter', 'partner', 'cmd', 'flow', 'value', 'netwgt', 'qty', 'qtyunit']


def to_frame(rows):
    return pd.DataFrame([{
        'period': r.get('period'), 'reporter': r.get('reporterCode'),
        'partner': r.get('partnerCode'), 'cmd': str(r.get('cmdCode')),
        'flow': r.get('flowCode'), 'value': r.get('primaryValue'),
        'netwgt': r.get('netWgt'), 'qty': r.get('qty'), 'qtyunit': r.get('qtyUnitCode'),
    } for r in rows], columns=COLS)


class Api(object):
    """Rotates across keys. per_key is each key's remaining allowance for today."""

    def __init__(self, keys, sleep=1.3, per_key=None):
        import requests
        self.s = requests.Session()
        self.keys = keys if isinstance(keys, (list, tuple)) else [keys]
        self.per_key = list(per_key) if per_key else [10 ** 9] * len(self.keys)
        self.i = 0
        self.sleep = sleep
        self.calls = 0
        self.by_key = [0] * len(self.keys)
        self.dry = 0

    @property
    def key(self):
        return self.keys[self.i]

    def exhausted(self):
        return all(self.by_key[j] >= self.per_key[j] for j in range(len(self.keys)))

    def _advance(self):
        """Move to the next key that still has allowance. Returns False if none do."""
        for _ in range(len(self.keys)):
            if self.by_key[self.i] < self.per_key[self.i]:
                return True
            self.i = (self.i + 1) % len(self.keys)
        return False

    def _charge(self):
        self.by_key[self.i] += 1
        self.calls += 1
        if self.by_key[self.i] >= self.per_key[self.i] and len(self.keys) > 1:
            nxt = (self.i + 1) % len(self.keys)
            if self.by_key[nxt] < self.per_key[nxt]:
                print('   key #%d spent, switching to key #%d' % (self.i + 1, nxt + 1), flush=True)
                self.i = nxt

    def _get(self, params):
        """_get_once, plus a count of how many requests in a row have come back with no data.

        The streak is kept out here rather than inside _get_once because that method wraps its
        body in `except Exception`, which would swallow the Throttled it is supposed to raise.
        """
        j, status = self._get_once(params)
        if status == 200:
            self.dry = 0
        elif status != -2:                 # -2 is the budget ending, which is not a failure
            self.dry += 1
            if self.dry >= DRY_GIVEUP:
                raise Throttled('%d requests in a row returned no data (last http %s)'
                                % (self.dry, status))
        return j, status

    def _get_once(self, params):
        for attempt in range(5):
            try:
                if not self._advance():
                    return None, -2                      # every key spent for today
                r = self.s.get(BASE, headers={'Ocp-Apim-Subscription-Key': self.key},
                               params=params, timeout=300)
                self._charge()
                if r.status_code == 200:
                    time.sleep(self.sleep)
                    return r.json(), 200
                if r.status_code in (429, 500, 502, 503, 504):
                    wait = 30 * (attempt + 1) if r.status_code == 429 else 6 * (attempt + 1)
                    print('      http %d, waiting %ds' % (r.status_code, wait), flush=True)
                    time.sleep(wait)
                    continue
                return None, r.status_code       # 401/403: never retry, never log the key
            except Exception as e:
                print('      %s, retrying' % type(e).__name__, flush=True)
                time.sleep(6 * (attempt + 1))
        return None, -1

    def filed(self, period):
        """Which reporters filed this month. One call, instead of one sizing call each."""
        import requests
        for attempt in range(5):
            try:
                if not self._advance():
                    return None
                r = self.s.get(AVAIL, headers={'Ocp-Apim-Subscription-Key': self.key},
                               params={'period': period}, timeout=180)
                self._charge()
                if r.status_code == 200:
                    time.sleep(self.sleep)
                    return {int(x['reporterCode']) for x in (r.json().get('data') or [])
                            if x.get('reporterCode') is not None}
                if r.status_code in (429, 500, 502, 503, 504):
                    wait = 40 * (attempt + 1) if r.status_code == 429 else 6 * (attempt + 1)
                    print('      availability http %d, waiting %ds' % (r.status_code, wait),
                          flush=True)
                    time.sleep(wait)
                    continue
                return None
            except Exception:
                time.sleep(6 * (attempt + 1))
        return None

    def count(self, periods, code, flow, cmd='AG6', partner=''):
        j, st = self._get({'period': ','.join(periods), 'reporterCode': code, 'cmdCode': cmd,
                           'flowCode': flow, 'partnerCode': partner, 'countOnly': 'true'})
        if j is None:
            return None, st
        n = j.get('count')
        return (int(n) if n is not None else None), st

    def data(self, periods, code, flow, cmd='AG6', partner=''):
        j, st = self._get({'period': ','.join(periods), 'reporterCode': code, 'cmdCode': cmd,
                           'flowCode': flow, 'partnerCode': partner})
        if j is None:
            return None, st
        return (j.get('data') or []), 200


def chunks(seq, n):
    """Split seq into n roughly equal chunks (n >= 1)."""
    n = max(1, int(n))
    k, m = divmod(len(seq), n)
    out, i = [], 0
    for j in range(n):
        size = k + (1 if j < m else 0)
        if size:
            out.append(seq[i:i + size])
            i += size
    return out


def crawl_reporter_year(api, st, year, code, iso3, flow, codes, budget_left):
    """Fetch one (reporter, year, flow) completely, or stop cleanly when the budget runs out.

    Returns calls used. Nothing is written unless it came back below the cap.
    """
    used = 0
    rk = '%d|%s|%s' % (year, iso3, flow)
    if st['done'].get(rk) == 'complete' or is_empty(st, rk, year):
        return 0

    months = months_of(year)
    if not months:
        return 0

    # --- size it once, and remember, so the next year starts from a real number -------------
    sk = rk
    n = st['size'].get(sk)
    if n is None:
        if used >= budget_left:
            return used
        n, status = api.count(months, code, flow)
        used += 1
        st['calls'] += 1
        if n is None:
            print('   %d %s %s  sizing FAILED http %s' % (year, iso3, flow, status), flush=True)
            if status in (401, 403):
                raise SystemExit('the key was rejected - stopping')
            return used
        st['size'][sk] = n
    if n == 0:
        mark_empty(st, rk, year)
        print('   %d %s %s  nothing filed' % (year, iso3, flow), flush=True)
        return used

    # --- choose the shape: the split axis is PARTNER, not commodity code -------------------
    #
    # It was code until 9 Oct 2026: a chunk went out as cmdCode=<comma-separated HS6 list>, and
    # with 5,384 codes in the universe even a two-way split is 2,692 codes = 18,843 characters of
    # query string, against a gateway ceiling of a few thousand. Every chunked request could only
    # ever return HTTP 414, so no reporter filing more than TARGET records a month was reachable -
    # and the measured average reporter files 178,184. The crawl could complete only the small
    # reporters, which is all the first 3,666 calls bought.
    #
    # A partner code is three or four characters: all 310 partner areas together are 1,203, so the
    # URL is no longer the binding constraint. A job carries (periods, partners, codes, tag), where
    # None means "no restriction on this axis".
    partners = partner_areas(st)
    if n <= TARGET:
        jobs = [(months, None, None, 'y')]                  # whole year, every partner, all codes
    else:
        per_month = n / 12.0
        if per_month <= TARGET:
            jobs = [([m], None, None, m[-2:]) for m in months]
        else:
            nchunk = int(math.ceil(per_month / float(TARGET)))
            jobs = []
            for m in months:
                for ci, pg in enumerate(chunks(partners, nchunk)):
                    jobs.append(([m], pg, None, '%s-p%02d' % (m[-2:], ci)))

    # --- run them, subdividing anything that comes back at the cap --------------------------
    queue = list(jobs)
    wrote_any = False
    while queue:
        if used >= budget_left:
            return used                                     # resume here next run
        periods, pl, cl, tag = queue.pop(0)
        ck = '%s|%s' % (rk, tag)
        if st['done'].get(ck) or is_empty(st, ck, year):
            continue
        p = part_path(year, iso3, flow, tag)
        if os.path.exists(p):
            st['done'][ck] = 'on disk'
            wrote_any = True
            continue

        cmd = 'AG6' if not cl else ','.join(cl)
        partner = '' if not pl else ','.join(str(x) for x in pl)
        rows, status = api.data(periods, code, flow, cmd=cmd, partner=partner)
        used += 1
        st['calls'] += 1
        if rows is None:
            print('   %d %s %s %-10s FAILED http %s' % (year, iso3, flow, tag, status), flush=True)
            if status in (401, 403):
                raise SystemExit('the key was rejected - stopping')
            continue

        if len(rows) >= PAGE_CAP:
            # TRUNCATED. Never save it. Subdivide on the cheapest axis that is still open:
            # months first, then partners (a few characters each), and only then codes - in
            # groups small enough to keep the query string legal, which is the lesson of the 414.
            #
            # KNOWN COST, accepted: the split is not persisted, only its children's files are.
            # A later run rebuilds the job list from scratch, re-requests this parent, gets the
            # cap again and re-derives the same children - then finds their parquet on disk and
            # skips them. So each previously-split parent costs one wasted call, and one capped
            # 100,000-row response, per run that touches its reporter-year. Bounded and small
            # against ~314,000 calls, and the alternative is persisting the queue: the children
            # are only derivable by replaying the parent's own partner list, so skipping the
            # parent without storing those lists would drop the children entirely.
            if len(periods) > 1:
                for m in periods:
                    queue.insert(0, ([m], pl, cl, m[-2:]))
                print('   %d %s %s %-10s capped, splitting the year into %d months'
                      % (year, iso3, flow, tag, len(periods)), flush=True)
            elif pl is None or len(pl) > 1:
                halves = chunks(pl if pl else partner_areas(st), 2)
                for hi, h in enumerate(halves):
                    queue.insert(0, (periods, h, cl, '%s-p%d' % (tag, hi)))
                print('   %d %s %s %-10s capped, splitting partners -> %s'
                      % (year, iso3, flow, tag,
                         ' + '.join(str(len(h)) for h in halves)), flush=True)
            elif cl is None:
                groups = chunks(codes, int(math.ceil(len(codes) / float(CODES_PER_CALL))))
                for gi, g in enumerate(groups):
                    queue.insert(0, (periods, pl, g, '%s-c%02d' % (tag, gi)))
                print('   %d %s %s %-10s capped on one partner, splitting codes into %d groups '
                      'of <=%d' % (year, iso3, flow, tag, len(groups), CODES_PER_CALL), flush=True)
            elif len(cl) > 1:
                halves = chunks(cl, 2)
                for hi, h in enumerate(halves):
                    queue.insert(0, (periods, pl, h, '%s-s%d' % (tag, hi)))
                print('   %d %s %s %-10s capped, splitting %d codes -> %s'
                      % (year, iso3, flow, tag, len(cl),
                         ' + '.join(str(len(h)) for h in halves)), flush=True)
            else:
                st['stuck'][ck] = len(rows)
                print('   %d %s %s %-10s CAPPED on one partner and one code - recorded as stuck'
                      % (year, iso3, flow, tag), flush=True)
            continue

        if not rows:
            mark_empty(st, ck, year)
            continue

        df = to_frame(rows)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        df.to_parquet(p, index=False, compression='zstd')
        st['done'][ck] = len(df)
        st['rows'] += len(df)
        wrote_any = True
        print('   %d %s %s %-10s %7d rows  %4d codes' % (year, iso3, flow, tag, len(df),
                                                         df.cmd.nunique()), flush=True)

    st['done' if wrote_any else 'empty'][rk] = 'complete' if wrote_any else True
    return used


# An "empty" for an old year is a fact; for a recent one it is only today's reading. Comtrade is
# filed with a lag of months to years, so a reporter that has not filed 2026 yet will file it later
# - and this crawl marks empties PERMANENTLY, so without this distinction the newest and most
# valuable years would be written off during the first week and never looked at again.
DRY_GIVEUP = 30          # consecutive requests that returned no data before giving up on
                         # the run. A throttled request is charged to the budget like any other,
                         # and _get retries a 429 five times, so a service-side throttle costs
                         # five calls per chunk and delivers nothing. On 9 Oct 2026 that spent the
                         # entire 880-call day: 0 rows, 0 files, exit 0, and the run still looked
                         # healthy. Stopping early leaves the budget for a day the service is
                         # willing to answer.


class Throttled(Exception):
    """The service is refusing in bulk. Stop; do not spend the rest of the day proving it."""


EMPTY_PROVISIONAL_YEARS = 2     # the current year and the one before it
EMPTY_RECHECK_DAYS = 30


def _recent(year):
    return year >= datetime.date.today().year - (EMPTY_PROVISIONAL_YEARS - 1)


def mark_empty(st, key, year):
    """Record an empty. Recent years carry the date they were read, older ones are just True."""
    st['empty'][key] = datetime.date.today().isoformat() if _recent(year) else True


def is_empty(st, key, year):
    """True only if this empty can still be trusted.

    A dated empty on a recent year expires after EMPTY_RECHECK_DAYS so the reporter is asked
    again. A bare True on a recent year predates this logic and is treated as expired, once.
    """
    v = st['empty'].get(key)
    if not v:
        return False
    if not _recent(year):
        return True
    if v is True:
        return False
    try:
        when = datetime.date.fromisoformat(v)
    except Exception:
        return False
    return (datetime.date.today() - when).days < EMPTY_RECHECK_DAYS


def months_of(year):
    """The months of `year` that can possibly hold data: never one in the future.

    Measured 6 Oct 2026, on the second run of the first armed day: 119 calls spent, ZERO rows
    stored. The crawl works newest-first, so it opens on 2026 and was asking for 202611 and
    202612 - November and December of a year that is still in October. Those cannot be filed by
    anyone, yet each one costs a call to establish as empty, and at 235 reporters x 2 flows that
    is ~940 calls, a full day of the two-key budget, spent proving that the future has not
    happened yet.

    The current month is kept rather than dropped: a month that has just ended is sometimes filed
    by the fastest reporters, and the availability endpoint settles that cheaply. Only strictly
    future months are removed, which is a claim that needs no judgement.
    """
    last = 12
    now = datetime.date.today()
    if year > now.year:
        return []
    if year == now.year:
        last = now.month
    return ['%d%02d' % (year, m) for m in range(1, last + 1)]


def filers_for_year(api, st, year):
    """M49 codes that filed ANY month of this year. 12 calls, cached in state forever after."""
    key = str(year)
    cached = st.setdefault('filers', {}).get(key)
    if cached is not None:
        return set(cached)
    if api is None:
        return None                       # --plan has no API; caller falls back to all reporters
    got = set()
    for period in months_of(year):
        s = api.filed(period)
        if s is None:
            return None                   # could not establish it; do not cache a half answer
        got |= s
    st['filers'][key] = sorted(got)
    save_state(st)
    print('   %d: %d reporters filed monthly data' % (year, len(got)), flush=True)
    return got


def pending(years, st, api=None):
    out = []
    for y in years:
        filers = filers_for_year(api, st, y)
        for code, iso3 in reporters():
            if filers is not None and code not in filers:
                continue                  # never filed this year - do not spend a call finding out
            for flow in ('M', 'X'):
                rk = '%d|%s|%s' % (y, iso3, flow)
                if st['done'].get(rk) == 'complete' or is_empty(st, rk, y):
                    continue
                out.append((y, code, iso3, flow))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--budget', type=int, default=DEFAULT_BUDGET)
    ap.add_argument('--years', type=int, nargs='*', default=None)
    ap.add_argument('--plan', action='store_true')
    ap.add_argument('--size', type=int, default=None, help='countOnly sizing for one year only')
    ap.add_argument('--sleep', type=float, default=1.3)
    ap.add_argument('--reset-ledger', action='store_true',
                    help="clear today's per-key spend before starting, to re-arm a day whose "
                         "budget went on refusals rather than data")
    a = ap.parse_args()

    years = a.years or list(range(YEAR_MAX, YEAR_MIN - 1, -1))
    st = load_state()

    if a.plan:
        reps = len(reporters())
        cds = len(all_codes())
        todo = pending(years, st)
        print('full-universe MONTHLY Comtrade crawl - PLAN ONLY, no calls made')
        print('  endpoint     %s' % BASE)
        print('  output       %s' % OUTDIR)
        print('  years        %d..%d (newest first)' % (years[0], years[-1]))
        print('  reporters    %d x 2 flows = %d reporter-year-flows per year' % (reps, reps * 2))
        print('  HS6 codes    %d' % cds)
        print('  per call     cap %s, aiming for %s' % (format(PAGE_CAP, ','), format(TARGET, ',')))
        print('  budget       %d calls/run' % a.budget)
        print()
        print('  measured: one month of world HS6 trade = 41,873,260 records')
        print('            so 27 years ~= 13.6 billion records, ~139 GB as parquet')
        # Not 13.57e9 / TARGET: that assumes every response comes back packed to TARGET, which
        # none do - a response at the cap is split and refetched, so the realised figure measured
        # on the partner axis is ROWS_PER_CALL. The TARGET version read 203,550 and was the reason
        # the watcher once reported 1.81% done when it was 0.04%.
        est = int(13.57e9 / ROWS_PER_CALL)
        print('  estimated calls at the measured %s rows/call: ~%s'
              % (format(ROWS_PER_CALL, ','), format(est, ',')))
        print('  at %d/run that is ~%.0f runs (~%.1f years of daily runs)'
              % (a.budget, est / float(a.budget), est / float(a.budget) / 365))
        print()
        print('  reporter-year-flows outstanding : %d' % len(todo))
        print('  calls made so far               : %s' % format(st.get('calls', 0), ','))
        print('  rows stored so far              : %s' % format(st.get('rows', 0), ','))
        print('  chunks recorded STUCK           : %d' % len(st.get('stuck', {})))
        return 0

    keys = _keys()
    led = _spent_today(st, len(keys))
    if a.reset_ledger:
        # A day's budget can go entirely on refusals - 9 Oct 2026 charged 880 calls and stored
        # nothing - and the ledger cannot tell a throttled request from one that delivered rows.
        # This re-arms the day, through save_state so the write stays atomic. It spends a real
        # allowance against a public service, so it is never the default and never automatic.
        for i in range(len(keys)):
            led[str(i)] = 0
        save_state(st)
        print('ledger cleared for today', flush=True)
    # --budget is the TOTAL for this run; each key may spend at most its own cap minus what it
    # already spent today, so a second run on the same day does not double-spend a key.
    #
    # KEY #1 IS CAPPED LOWER, and this is the line that actually enforces REFRESH_RESERVE.
    # It did not, until 6 Oct 2026: the reserve was subtracted from the run TOTAL (880 = 380+500)
    # while every key was still capped at the full PER_KEY_DAY, so the rotation spent key #1 to
    # 500 and only then moved to key #2 - the ledger after the first armed run read 500 and 381,
    # exactly backwards from the intent. The refresh survived purely because it runs at 03:00,
    # two hours ahead of the crawl: protected by the timetable, not by this code. On a day the
    # refresh ran late or needed more, they would have collided and the crawl would have spent
    # its morning absorbing 429s on an exhausted key.
    #
    # Key #1 is the one pipeline/adapter_comtrade.py uses (it reads line 1 of .comtrade_key), so
    # key #1 is the one that has to keep something back.
    caps = [PER_KEY_DAY - (REFRESH_RESERVE if i == 0 else 0) for i in range(len(keys))]
    remaining = [max(0, caps[i] - int(led.get(str(i), 0))) for i in range(len(keys))]
    print('keys available: %d   remaining today: %s   run budget: %d'
          % (len(keys), remaining, a.budget), flush=True)
    api = Api(keys, sleep=a.sleep, per_key=remaining)
    codes = all_codes()

    if a.size:
        y = a.size
        print('countOnly sizing for %d (one call per reporter-flow)...' % y)
        tot = 0
        for code, iso3 in reporters():
            for flow in ('M', 'X'):
                n, status = api.count(months_of(y), code, flow)
                if n is None:
                    print('   %s %s  http %s' % (iso3, flow, status)); continue
                st['size']['%d|%s|%s' % (y, iso3, flow)] = n
                tot += n
                if n:
                    print('   %s %s  %12s records  -> %d calls'
                          % (iso3, flow, format(n, ','), max(1, int(math.ceil(n / float(TARGET))))))
        save_state(st)
        print('\n%d total records for %d; ~%d calls to fetch'
              % (tot, y, int(math.ceil(tot / float(TARGET)))))
        return 0

    os.makedirs(OUTDIR, exist_ok=True)
    st['started'] = st.get('started') or time.strftime('%Y-%m-%d %H:%M')
    todo = pending(years, st, api)
    used, t0 = 0, time.time()
    _charged_in_loop = [0]
    _charged_by_key = [0] * len(keys)

    def _charge_keys():
        """Write each key's spend to the ledger NOW, not when the run ends.

        Only the run total reached the ledger, in the finally block below, so a run that never
        got there - the task's time limit, a reboot, a kill - left the ledger reading zero for
        the rest of the day while the UN had already charged every call made. The next run then
        saw a full allowance on a drained key and spent it collecting 429s, which is the very
        thing _spent_today and REFRESH_RESERVE exist to prevent. Idempotent: it charges only the
        delta since the last call, so the finally block can run it again safely.
        """
        for i, n in enumerate(api.by_key):
            d = n - _charged_by_key[i]
            if d:
                led[str(i)] = int(led.get(str(i), 0)) + d
                _charged_by_key[i] = n

    try:
        for (y, code, iso3, flow) in todo:
            if api.calls >= a.budget or api.exhausted():
                print('budget of %d calls reached' % a.budget)
                break
            before = st.get('calls', 0)
            used += crawl_reporter_year(api, st, y, code, iso3, flow, codes,
                                        max(0, a.budget - api.calls))
            _charged_in_loop[0] += st.get('calls', 0) - before
            _charge_keys()
            save_state(st)
    except Throttled as e:
        print('STOPPING: %s' % e, flush=True)
        print('the service is throttling; the remaining budget is kept for the next run',
              flush=True)
    finally:
        st['calls'] = int(st.get('calls', 0)) + max(0, api.calls - _charged_in_loop[0])
        _charge_keys()
        save_state(st)

    left = len(pending(years, st, api))
    print()
    print('this run: %d calls in %.1f min. total %s calls, %s rows stored'
          % (api.calls, (time.time() - t0) / 60, format(st.get('calls', 0), ','),
             format(st.get('rows', 0), ',')))
    print('reporter-year-flows outstanding: %d' % left)
    if st.get('stuck'):
        print('STUCK chunks (capped on a single code, not saved): %d - these need partner splitting'
              % len(st['stuck']))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
