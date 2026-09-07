# -*- coding: utf-8 -*-
"""WIDE-monthly upgrade: UN Comtrade free 'preview' endpoint — HS-6, monthly, KEYLESS (no auth) but
under a strict Fair-Usage rate limit. So this is a ROTATING CALENDAR: each run pulls a small BATCH of
reporters (ones not covered by a national adapter), chunks commodities under the 500-row preview cap,
sleeps between calls, backs off on 429, and APPENDS to an incremental cache. Coverage accumulates over
many runs. primaryValue = USD, netWgt = kg; codes are M49 -> ISO3 via BACI's numeric table."""
import os, json, time, urllib.request, urllib.error
import schema, concordance
from adapter_base import Adapter, num

BASE = "https://comtradeapi.un.org/public/v1/preview/C/M/HS"
CACHE = os.path.join(schema.ROOT, 'pipeline', 'data', 'comtrade_cache.jsonl')
STATE = os.path.join(schema.ROOT, 'pipeline', 'data', 'comtrade_state.json')
_PAUSE = 18   # seconds between calls (fair-usage); 429 -> longer backoff

# reporters to grow coverage with (M49 codes); rotated a few per run
REPORTERS = [124, 392, 699, 360, 152, 710, 410, 36, 484, 792, 704, 764, 156, 643,   # CAN JPN IND IDN CHL ZAF KOR AUS MEX TUR VNM THA CHN RUS
             842, 604, 32, 398, 496, 608, 682, 578, 616, 68, 76, 894,                # USA PER ARG KAZ MNG PHL SAU NOR POL BOL BRA ZMB
             170, 504, 818, 804, 246, 752, 458, 634, 512, 702, 376, 516]             # COL MAR EGY UKR FIN SWE MYS QAT OMN SGP ISR NAM
# ^ additions target big critical-material producers NOT already covered by a DEEP national source
# (US HS-6 breadth, Peru/Zambia copper, Argentina/Bolivia lithium, Kazakhstan uranium/chrome, Mongolia
#  coking coal, Philippines nickel; Colombia coal, Morocco/Egypt phosphate, Ukraine titanium/manganese,
#  Finland/Sweden Ni-Co-REE refining, Malaysia REE/tin, Qatar/Oman helium) — each new reporter creates
#  fresh two-sided pairs to reconcile wherever its counterparty already reports.


def _get(url, tries=5):
    for _ in range(tries):
        try:
            return json.load(urllib.request.urlopen(
                urllib.request.Request(url, headers={'User-Agent': 'critical-materials-atlas/phase3'}), timeout=60))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(_PAUSE * 2); continue
            return None
        except Exception:
            time.sleep(_PAUSE); continue
    return None


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def read_cache():
    """All rows accumulated so far (what build.py reads — no network)."""
    rows = []
    if os.path.exists(CACHE):
        for line in open(CACHE, encoding='utf8'):
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    return rows


def fetch_batch(period, n_reporters=1):
    """Pull one rotation of n_reporters and APPEND to the cache. Called by the standalone pull_comtrade.py
    (occasional / cron), NOT by build.py — this is the slow, rate-limited part, kept out of the build."""
    state = json.load(open(STATE)) if os.path.exists(STATE) else {'idx': 0}
    idx = state.get('idx', 0)
    batch = [REPORTERS[(idx + i) % len(REPORTERS)] for i in range(n_reporters)]
    state['idx'] = (idx + n_reporters) % len(REPORTERS)
    codes = sorted(concordance.tracked_hs6_set())
    pulled = 0
    with open(CACHE, 'a', encoding='utf8') as f:
        for m49 in batch:
            for flow in ('M', 'X'):
                for chunk in _chunks(codes, 10):     # keep each response under the 500-row preview cap
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
    MONTH = 202412   # Comtrade monthly lags; this month has broad coverage
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
