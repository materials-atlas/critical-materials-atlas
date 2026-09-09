# -*- coding: utf-8 -*-
"""WIDE-monthly upgrade: UN Comtrade free 'preview' endpoint — HS-6, monthly, KEYLESS (no auth) but
under a Fair-Usage rate limit that turned out to be far looser than we assumed. So this is a ROTATING
CALENDAR: each run pulls EVERY reporter for ONE month (ones not covered by a national adapter), chunks commodities under the 500-row preview cap,
sleeps between calls, backs off on 429, and APPENDS to an incremental cache. Coverage accumulates over
many runs. primaryValue = USD, netWgt = kg; codes are M49 -> ISO3 via BACI's numeric table."""
import os, json, time, urllib.request, urllib.error
import schema, concordance
from adapter_base import Adapter, num

# THE KEYLESS ENDPOINT WAS TRUNCATING EVERY CALL AT 500 ROWS, silently. Measured 7 Sep 2026:
# the same query (Canada, 31 codes, one month, one flow) returns exactly 500 rows without a key
# and 1,111 with one. Everything Comtrade has contributed to this project so far is therefore
# incomplete by construction - not wrong, but cut off at an arbitrary line with no error and no
# flag. That is very likely part of what looked like two countries disagreeing.
#
# With a free subscription key the limit is 100,000 records per call, which changes the shape of
# the job entirely: 31 codes x 6 months x both flows came back as 10,435 rows in ONE call. The
# whole 18-month backfill is ~114 calls against a 500/day allowance, so it fits in a single run
# instead of three weeks of nightly rotation.
KEYFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.comtrade_key')
API_KEY = open(KEYFILE).read().strip() if os.path.exists(KEYFILE) else None
BASE = ("https://comtradeapi.un.org/data/v1/get/C/M/HS" if API_KEY
        else "https://comtradeapi.un.org/public/v1/preview/C/M/HS")
MONTHS_PER_CALL = 6      # measured: 6 months of 31 codes, both flows = 10,435 rows, well inside
                         # the 100k ceiling. Kept modest so one slow call cannot stall a run.
CACHE = os.path.join(schema.ROOT, 'pipeline', 'data', 'comtrade_cache.jsonl')
STATE = os.path.join(schema.ROOT, 'pipeline', 'data', 'comtrade_state.json')
# MEASURED, not guessed. 18 seconds was a cautious invention and it set the pace of the whole
# project: at 8 calls per reporter it meant 3 minutes per country, so a run could afford three
# countries and filling the 18-month gap would have taken 33 weeks. Tested against the live
# endpoint at 1-second spacing: 12 consecutive calls, zero rejections. 4 seconds is therefore
# still four times more cautious than what the service demonstrably tolerates, and it turns three
# countries per run into all thirty-six.
_PAUSE = 4
# The 429 backoff is deliberately NOT derived from _PAUSE any more. It used to be _PAUSE * 2, so
# lowering the pace would have quietly weakened the retry at exactly the moment it started to
# matter. Rate-limit recovery should be slow regardless of how fast we are going when it hits.
_BACKOFF = 45

# reporters to grow coverage with (M49 codes); rotated a few per run
REPORTERS = [124, 392, 699, 360, 152, 710, 410, 36, 484, 792, 704, 764, 156, 643,   # CAN JPN IND IDN CHL ZAF KOR AUS MEX TUR VNM THA CHN RUS
             842, 604, 32, 398, 496, 608, 682, 578, 616, 68, 76, 894,                # USA PER ARG KAZ MNG PHL SAU NOR POL BOL BRA ZMB
             170, 504, 818, 804, 246, 752, 458, 634, 512, 702, 376, 516]             # COL MAR EGY UKR FIN SWE MYS QAT OMN SGP ISR NAM
# ^ additions target big critical-material producers NOT already covered by a DEEP national source
# (US HS-6 breadth, Peru/Zambia copper, Argentina/Bolivia lithium, Kazakhstan uranium/chrome, Mongolia
#  coking coal, Philippines nickel; Colombia coal, Morocco/Egypt phosphate, Ukraine titanium/manganese,
#  Finland/Sweden Ni-Co-REE refining, Malaysia REE/tin, Qatar/Oman helium) — each new reporter creates
#  fresh two-sided pairs to reconcile wherever its counterparty already reports.


class QuotaExceeded(Exception):
    """The API says we are out of calls for the day.

    This has to be its own exception because it is the one failure that must STOP a long run
    rather than be retried or skipped. It was previously flattened into `return None` alongside
    every other HTTP error, so a backfill could not tell "this block has no data" from "you are
    not allowed to ask" - and spent 150 calls of a 150-call remainder marking blocks permanently
    complete on the strength of 403s.
    """


def _get(url, tries=5):
    for _ in range(tries):
        try:
            hdr = {'User-Agent': 'critical-materials-atlas/phase3'}
            if API_KEY:
                hdr['Ocp-Apim-Subscription-Key'] = API_KEY
            return json.load(urllib.request.urlopen(
                urllib.request.Request(url, headers=hdr), timeout=180))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(_BACKOFF); continue
            if e.code == 403:
                # "Out of call volume quota. Quota will be replenished in HH:MM:SS."
                try:
                    body = e.read().decode('utf8', 'replace')
                except Exception:
                    body = ''
                if 'quota' in body.lower():
                    raise QuotaExceeded(body.strip())
            return None
        except Exception:
            time.sleep(_PAUSE); continue
    return None


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


HISTORY = os.path.join(schema.ROOT, 'pipeline', 'data', 'comtrade_history')


def source_fingerprint():
    """What the two stores hold, by CONTENT not by clock: part count, part rows from parquet
    metadata (no data read), and the JSONL size in bytes. cache.save stamps this into the
    manifest; build.py refuses a cache whose stamp no longer matches the stores.

    Why: on 9 Sep the 2016-2024 history landed AFTER refresh had last run, build.py was run
    directly, and the cube shipped with a hole across exactly the years the export-control dates
    sit in. Nothing errored. A required order that nothing encoded. This encodes it.
    """
    import glob
    parts = sorted(glob.glob(os.path.join(HISTORY, '*.parquet'))) if os.path.isdir(HISTORY) else []
    rows = 0
    try:
        import pyarrow.parquet as pq
        for f in parts:
            rows += pq.read_metadata(f).num_rows
    except ImportError:
        rows = -1
    return {'history_parts': len(parts), 'history_rows': rows,
            'jsonl_bytes': os.path.getsize(CACHE) if os.path.exists(CACHE) else 0}


def read_cache():
    """All rows accumulated so far (what build.py reads - no network).

    Two stores, for a reason. The JSONL grew from the keyless era, when a run collected a few
    hundred rows and appending a line at a time was fine; it is already 119 MB for eighteen months
    of thirty-eight reporters and is re-parsed in full on every refresh. The long historical
    backfill - 198 months x 255 reporters - would put that past a gigabyte, so it writes PARQUET
    PARTS instead: columnar, compressed, and readable without parsing the lot.

    Both are read here so the transition needs no migration and no flag day. Duplicates across the
    two stores are harmless: normalize() keys every cell and keeps one row per key.
    """
    rows = []
    if os.path.exists(CACHE):
        for line in open(CACHE, encoding='utf8'):
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    if os.path.isdir(HISTORY):
        import glob
        try:
            import pandas as pd
            for f in sorted(glob.glob(os.path.join(HISTORY, '*.parquet'))):
                rows.extend(pd.read_parquet(f).to_dict('records'))
        except ImportError:
            pass
    return rows


def fetch_batch(period, n_reporters=1):
    """Pull one rotation of n_reporters and APPEND to the cache. Called by the standalone pull_comtrade.py
    (occasional / cron), NOT by build.py — this is the slow, rate-limited part, kept out of the build."""
    state = json.load(open(STATE)) if os.path.exists(STATE) else {'idx': 0, 'month_idx': 0}
    idx = state.get('idx', 0)
    batch = [REPORTERS[(idx + i) % len(REPORTERS)] for i in range(n_reporters)]
    nxt = idx + n_reporters
    state['idx'] = nxt % len(REPORTERS)
    # When the reporter rotation wraps, step to the next month. Coverage therefore grows in two
    # directions instead of one, which is what a mirror comparison needs: more countries widens
    # the panel, more months makes it a series.
    if nxt >= len(REPORTERS):
        state['month_idx'] = state.get('month_idx', 0) + 1
    codes = sorted(concordance.tracked_hs6_set())
    pulled = 0
    # With a key: ALL codes and BOTH flows in one call, and `period` may be a comma-separated list
    # of months. Without one: the old chunk-of-10, single-flow shape, because the preview endpoint
    # truncates at 500 rows and chunking is the only way to stay under it.
    if API_KEY:
        code_groups, flows = [codes], ['M,X']
    else:
        code_groups, flows = list(_chunks(codes, 10)), ['M', 'X']
    with open(CACHE, 'a', encoding='utf8') as f:
        for m49 in batch:
            for flow in flows:
                for chunk in code_groups:
                    d = _get(f"{BASE}?reporterCode={m49}&period={period}&cmdCode={','.join(chunk)}&flowCode={flow}")
                    for r in (d or {}).get('data', []):
                        # KEEP THE FIELDS THAT DECIDE WHICH ROW IS WHICH, and the declared
                        # basis. Storing only seven fields is what made one cell look like it
                        # arrived four times with four different values: motCode splits it by
                        # mode of transport and motCode=0 is the all-modes TOTAL. And
                        # fobvalue/cifvalue say what the reporter actually declared - Canada
                        # files imports FOB, China files CIF, the USA files both - which we had
                        # been guessing at by assuming every import is CIF and deflating it.
                        f.write(json.dumps({k: r.get(k) for k in
                                ('reporterCode', 'partnerCode', 'partner2Code', 'cmdCode',
                                 'flowCode', 'period', 'primaryValue', 'netWgt',
                                 'motCode', 'customsCode', 'isAggregate', 'isReported',
                                 'fobvalue', 'cifvalue')}) + '\n')
                        pulled += 1
                    time.sleep(_PAUSE)
    json.dump(state, open(STATE, 'w'))
    print(f"comtrade: pulled {pulled} rows for reporters {batch} (next idx {state['idx']})")
    return pulled


class ComtradeAdapter(Adapter):
    key = 'comtrade'
    freq = 'M'
    note = 'UN Comtrade free preview — HS-6, monthly, keyless (rate-limited, rotating calendar)'
    MONTH = 202412   # the month build.py reads; kept for the cache's canonical period

    # The gap this whole monthly layer exists to fill. BACI is reconciled, excellent, and ANNUAL -
    # and it stops at 2024. Everything after that is unreconciled until CEPII catches up, which
    # takes about two years. That gap is the only space a monthly product occupies.
    BACI_LAST_YEAR = 2024
    LAG_MONTHS = 3     # measured, not assumed: Comtrade served 202606 when tested in Sep 2026

    @staticmethod
    def calendar():
        """The months we actually need, newest first.

        CORRECTED 7 Sep 2026, after the user asked what span we were even targeting. The first
        version took "18 months ending 8 months ago", which was wrong in both directions: it
        reached back to 202408, re-fetching months BACI already covers reconciled and better, and
        it stopped at 202601, discarding the five most recent months - the fresher-than-BACI
        months that are the entire reason for doing this.

        The right window starts the month after BACI's last year and runs to the newest month the
        source actually serves. Probed before changing it: 202602 through 202606 all return data,
        so the real lag is about three months, not eight.
        """
        import datetime
        # +1: BACI covers THROUGH its last year, so the gap starts the January after it.
        first = (ComtradeAdapter.BACI_LAST_YEAR + 1) * 100 + 1     # 2024 -> 202501
        d = datetime.date.today().replace(day=1)
        for _ in range(ComtradeAdapter.LAG_MONTHS):
            d = (d - datetime.timedelta(days=1)).replace(day=1)
        out = []
        while True:
            p = d.year * 100 + d.month
            if p < first:
                break
            out.append(p)
            d = (d - datetime.timedelta(days=1)).replace(day=1)
        return out
    BATCH = 1        # reporters pulled per run (conservative for the strict free-tier rate limit)

    def discover(self):
        return [self.MONTH]

    def pull(self, period):
        return read_cache()   # READ-ONLY in the build; growing the cache is pull_comtrade.py's job

    def normalize(self, raw, period):
        """One cell, several rows: keep the TOTAL, not whichever arrived first.

        THE BUG THIS FIXES (found 7 Sep 2026, and it was expensive). Comtrade's preview endpoint
        returns a (reporter, partner, commodity, flow, period) cell MORE THAN ONCE - broken out by
        fields we do not request and therefore cannot see, such as customs procedure or mode of
        transport - and it returns the aggregate alongside its own components. Canada's December
        2024 coal imports from the USA came back as four rows:

            34.563  +  134,675.909  +  67,717,507.625  =  67,852,218.097

        The first three are components; the fourth is their exact total. This method used a
        first-seen `seen` set, so it kept 34.563 - $34 for a shipment of 417,000 tonnes - and
        discarded the real figure. The US side reported $74.6m for the same coal, so the pipeline
        recorded a 2,000,000x "disagreement" between two countries that actually agree to within
        10%.

        That single defect is a large part of why 51% of matched flows appeared to disagree, and
        the number was one day from being published as a finding about world trade statistics.

        Summing is WRONG here - the components are already inside the total, so summing would
        double it. Taking the maximum is right, and provably so on this cell: the largest row
        equals the sum of the others to the cent. Where a cell genuinely arrives only once, max is
        that row, so the rule is safe everywhere.
        """
        best = {}
        for r in raw:
            # Prefer the all-modes total explicitly where the field is present: motCode=0 IS
            # the aggregate. The max-value rule below was a lucky proxy for it - the total
            # happens to be the largest row - and stays only for rows cached before this
            # field was kept.
            mot = r.get('motCode')
            if mot is not None and str(mot) != '0':
                continue
            p2 = r.get('partner2Code')
            if p2 is not None and str(p2) not in ('0', str(r.get('partnerCode'))):
                continue
            rep = schema.NUM2ISO3.get(str(r.get('reporterCode')))
            par = schema.NUM2ISO3.get(str(r.get('partnerCode')))
            cc = r.get('cmdCode')
            if not rep or not par or not cc or not concordance.hs6_tracked(cc):
                continue                                 # unmapped codes / World aggregate / untracked
            k = (r.get('period'), rep, par, cc, r.get('flowCode'))
            # Rank on (value, does-this-row-carry-the-new-fields). The JSONL accumulates, so a
            # cell can appear both as an old 7-field row and a new wide one with identical value.
            # Comparing on value alone let the OLD row win every tie simply by being written
            # first, and the declared basis never reached a single flow. Ties now go to the row
            # that knows more.
            v = num(r.get('primaryValue')) or 0
            informative = 1 if (r.get('fobvalue') is not None or r.get('cifvalue') is not None) else 0
            rank_new = (v, informative)
            cur = best.get(k)
            rank_cur = ((num(cur.get('primaryValue')) or 0),
                        1 if (cur.get('fobvalue') is not None or cur.get('cifvalue') is not None)
                        else 0) if cur else (-1, -1)
            if rank_new > rank_cur:
                best[k] = r
        for r in best.values():
            rep = schema.NUM2ISO3[str(r['reporterCode'])]
            par = schema.NUM2ISO3[str(r['partnerCode'])]
            cc = r['cmdCode']
            yield schema.row(
                source=self.key, freq=self.freq, period=int(r['period']),
                reporter=rep, reporter_name=schema.ISO3_NAME.get(rep, rep),
                partner=par, partner_name=schema.ISO3_NAME.get(par, par),
                flow='import' if r.get('flowCode') == 'M' else 'export',
                hs6=cc, native_code=cc, code_level=6, material=concordance.material_for(cc, 6),
                value_usd=num(r.get('primaryValue')), qty_kg=num(r.get('netWgt')), is_mirror=False,
                # The reporter's OWN valuation, straight off the record. Comtrade populates
                # fobvalue and/or cifvalue according to what the country actually filed, so this
                # is read rather than assumed. Rows cached before these fields were kept return
                # None, which the reconciliation treats as "unknown, use the convention".
                value_basis=('cif' if r.get('cifvalue') is not None
                             else 'fob' if r.get('fobvalue') is not None else None))
