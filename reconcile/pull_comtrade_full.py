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
import urllib.parse
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

# MEASURED 9 Oct 2026, not guessed: a 1,923-character request URL was served and a 2,436-character
# one returned 414, so the gateway's ceiling is the usual 2,048 bytes. The limit applies to the
# WHOLE query string, which matters because a partner list alone can be 1,200 characters - the
# first attempt at this capped cmdCode at 1,800 and still got a 414, because the rest of the query
# pushed it over. 1,800 for everything leaves room for the longest base parameters.
MAX_URL_CHARS = 1800

# The axes an over-large request can be cut along, in the order they are tried: partner first
# because it is the broadest, commodity code last because its values are six characters each and
# it is the only axis that can push a URL back into a 414.
SPLIT_ORDER = ('partnerCode', 'customsCode', 'motCode', 'cmdCode')
AXIS_TAG = {'partnerCode': 'p', 'customsCode': 'u', 'motCode': 'm', 'cmdCode': 'k'}

# Rows actually delivered per call. Re-measured 9 Oct 2026 on the FULL 35-column schema:
# 239,137 rows in 10 calls. The earlier 43,162 was taken while customsCode, motCode and
# partner2Code were being dropped, so it counted collapsed rows as delivered. PROVISIONAL - it
# comes from ten calls on small reporters, and crawl_watch replaces it with the real rate once
# two full days have run.
ROWS_PER_CALL = 23914

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


def _reference_codes(st, key, filename, label):
    """A Comtrade reference list, cached in state. Keyless, and charged to no quota."""
    cached = st.setdefault('refs', {}).get(key)
    if cached:
        return list(cached)
    url = 'https://comtradeapi.un.org/files/v1/app/reference/%s.json' % filename
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        j = json.load(urllib.request.urlopen(req, timeout=120))
        rows = j.get('results') if isinstance(j, dict) else j
        got = sorted({str(r['id']) for r in rows if str(r.get('id', '')).strip() != ''})
    except Exception as e:
        raise SystemExit('cannot read the %s reference list (%s: %s) - splitting on that axis '
                         'without it could omit values, so the run stops here'
                         % (label, type(e).__name__, e))
    st['refs'][key] = got
    save_state(st)
    print('   %s: %d codes (reference file, no key, no quota)' % (label, len(got)), flush=True)
    return list(got)


def axis_values(st, axis, codes):
    """Every value of one split axis, so a partition over it cannot silently omit anything."""
    if axis == 'partnerCode':
        return partner_areas(st)
    if axis == 'customsCode':
        return _reference_codes(st, 'customs', 'CustomsCodes', 'customs procedures')
    if axis == 'motCode':
        return _reference_codes(st, 'mot', 'ModeOfTransportCodes', 'modes of transport')
    if axis == 'cmdCode':
        return list(codes)
    raise KeyError(axis)


def job_params(code, flow, periods, filt):
    """The query for one job. An axis missing from `filt` is left unrestricted."""
    p = {'period': ','.join(periods), 'reporterCode': code, 'flowCode': flow}
    p['cmdCode'] = ','.join(filt['cmdCode']) if filt.get('cmdCode') else 'AG6'
    for axis in ('partnerCode', 'customsCode', 'motCode'):
        v = filt.get(axis)
        p[axis] = ','.join(str(x) for x in v) if v else ''
    return p


def query_chars(code, flow, periods, filt):
    """How long the request URL will be, so an over-long one is cut before a call is spent."""
    return len(BASE) + 1 + len(urllib.parse.urlencode(job_params(code, flow, periods, filt)))


def split_job(st, codes, periods, filt, tag):
    """Cut one job along the first axis that can still be cut. [] means nothing is left to cut."""
    if len(periods) > 1:
        return [([m], dict(filt), m[-2:]) for m in periods]
    for axis in SPLIT_ORDER:
        cur = filt.get(axis)
        vals = list(cur) if cur else None
        if vals is None:
            vals = axis_values(st, axis, codes)
        if len(vals) > 1:
            return [(periods, dict(filt, **{axis: list(h)}),
                     '%s-%s%d' % (tag, AXIS_TAG[axis], i))
                    for i, h in enumerate(chunks(vals, 2))]
    return []


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


# Every field the API returns that carries data. The ISO and description columns are left out:
# they come back null unless separately requested, and they are lookups we already hold locally.
COLS = ['typeCode', 'freqCode', 'refPeriodId', 'refYear', 'refMonth', 'period',
        'reporterCode', 'flowCode', 'partnerCode', 'partner2Code',
        'classificationCode', 'classificationSearchCode', 'isOriginalClassification',
        'cmdCode', 'aggrLevel', 'isLeaf',
        'customsCode', 'mosCode', 'motCode',
        'qtyUnitCode', 'qty', 'isQtyEstimated',
        'altQtyUnitCode', 'altQty', 'isAltQtyEstimated',
        'netWgt', 'isNetWgtEstimated', 'grossWgt', 'isGrossWgtEstimated',
        'cifvalue', 'fobvalue', 'primaryValue',
        'legacyEstimationFlag', 'isReported', 'isAggregate']


def to_frame(rows):
    """All 35 data-carrying fields, in a fixed column order.

    The nine-column schema this replaces dropped customsCode, motCode and partner2Code, so rows
    differing only in those - a free-zone entry against a home-use one, air against road, China
    via the UK against China via the USA - were written to parquet as byte-identical rows.
    Measured on one stored file: 544 rows, 62 distinct on the five keys that survived. The detail
    was not merely lost; the file became unsummable, because adding those rows multiplies the
    trade by the number of collapsed combinations - up to 26x for Germany.

    `isAggregate`, kept here, is what separates a total from its components; so do partnerCode 0
    (World), customsCode C00 and motCode 0, which are all TOTAL rows sitting beside their parts.
    Nothing downstream may sum across a dimension without first picking one level of it.
    """
    df = pd.DataFrame(rows)
    for c in COLS:
        if c not in df.columns:
            df[c] = None
    return df[COLS]


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
                if r.status_code in (401, 403):
                    # Retire this key for the run and carry on with the rotation. Raising instead
                    # is what ended the 9 Oct afternoon run at 13:05 - key #1 was refused and the
                    # whole crawl stopped while key #2 was still answering 200.
                    print('      key #%d refused (http %d) - retiring it for this run'
                          % (self.i + 1, r.status_code), flush=True)
                    self.per_key[self.i] = self.by_key[self.i]
                    if not self.exhausted():
                        self._advance()
                        continue
                return None, r.status_code       # never log the key itself
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

    def data_params(self, params):
        """A data request from a ready-made parameter dict, so the caller owns the filters."""
        j, status = self._get(params)
        if j is None:
            return None, status
        return (j.get('data') or []), 200

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

    A job is (periods, filt, tag), where filt maps a split axis to the values it is restricted to
    and an absent axis means no restriction. Anything too big - or too long to send - is cut by
    split_job along partner, then customs procedure, then mode of transport, then commodity code.
    """
    used = 0
    rk = '%d|%s|%s' % (year, iso3, flow)
    if st['done'].get(rk) == 'complete' or is_empty(st, rk, year):
        return 0

    months = months_of(year)
    if not months:
        return 0

    # --- size it once, and remember, so the next year starts from a real number -------------
    n = st['size'].get(rk)
    if n is None:
        if used >= budget_left:
            return used
        n, status = api.count(months, code, flow)
        used += 1
        st['calls'] += 1
        if n is None:
            print('   %d %s %s  sizing FAILED http %s' % (year, iso3, flow, status), flush=True)
            if api.exhausted():
                raise SystemExit('every key has been refused or spent - stopping')
            return used
        st['size'][rk] = n
    if n == 0:
        mark_empty(st, rk, year)
        print('   %d %s %s  nothing filed' % (year, iso3, flow), flush=True)
        return used

    # --- the opening shape: whole year, or per month, or per month x partner group ----------
    if n <= TARGET:
        jobs = [(months, {}, 'y')]
    else:
        per_month = n / 12.0
        if per_month <= TARGET:
            jobs = [([m], {}, m[-2:]) for m in months]
        else:
            nchunk = int(math.ceil(per_month / float(TARGET)))
            partners = partner_areas(st)
            jobs = [([m], {'partnerCode': list(pg)}, '%s-p%02d' % (m[-2:], ci))
                    for m in months for ci, pg in enumerate(chunks(partners, nchunk))]

    queue = list(jobs)
    wrote_any = False

    def push(children):
        for kid in reversed(children):
            queue.insert(0, kid)

    while queue:
        if used >= budget_left:
            return used                                     # resume here next run
        periods, filt, tag = queue.pop(0)
        ck = '%s|%s' % (rk, tag)
        if st['done'].get(ck) or is_empty(st, ck, year):
            continue
        p = part_path(year, iso3, flow, tag)
        if os.path.exists(p):
            st['done'][ck] = 'on disk'
            wrote_any = True
            continue

        # Too long to send? Cut it now. This costs no call, and it is the check whose absence
        # made every chunked request a certain 414.
        if query_chars(code, flow, periods, filt) > MAX_URL_CHARS:
            kids = split_job(st, codes, periods, filt, tag)
            if not kids:
                st['stuck'][ck] = 'url too long with nothing left to split'
                print('   %d %s %s %-22s STUCK: url too long, no axis left'
                      % (year, iso3, flow, tag), flush=True)
                continue
            push(kids)
            continue

        rows, status = api.data_params(job_params(code, flow, periods, filt))
        used += 1
        st['calls'] += 1
        if rows is None:
            print('   %d %s %s %-22s FAILED http %s' % (year, iso3, flow, tag, status), flush=True)
            if api.exhausted():
                raise SystemExit('every key has been refused or spent - stopping')
            continue

        if len(rows) >= PAGE_CAP:
            # TRUNCATED. Never save it: subdivide and come back to the parts.
            kids = split_job(st, codes, periods, filt, tag)
            if not kids:
                st['stuck'][ck] = len(rows)
                print('   %d %s %s %-22s CAPPED with no axis left to split - stuck'
                      % (year, iso3, flow, tag), flush=True)
                continue
            axis = [a for a in SPLIT_ORDER
                    if kids[0][1].get(a) != filt.get(a)] or ['period']
            print('   %d %s %s %-22s capped, splitting %s -> %s'
                  % (year, iso3, flow, tag, axis[0],
                     ' + '.join(str(len(k[1].get(axis[0]) or k[0])) for k in kids)), flush=True)
            push(kids)
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
        print('   %d %s %s %-22s %7d rows  %4d codes' % (year, iso3, flow, tag, len(df),
                                                         df.cmdCode.nunique()), flush=True)

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
