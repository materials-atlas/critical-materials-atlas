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
                        f.write(json.dumps({k: r.get(k) for k in
                                ('reporterCode', 'partnerCode', 'cmdCode', 'flowCode', 'period', 'primaryValue', 'netWgt')}) + '\n')
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
        seen = set()
        for r in raw:
            rep = schema.NUM2ISO3.get(str(r.get('reporterCode')))
            par = schema.NUM2ISO3.get(str(r.get('partnerCode')))
            cc = r.get('cmdCode')
            if not rep or not par or not cc or not concordance.hs6_tracked(cc):
                continue                                 # unmapped codes / World aggregate / untracked
            k = (r.get('period'), rep, par, cc, r.get('flowCode'))
            if k in seen:
                continue
            seen.add(k)
            yield schema.row(
                source=self.key, freq=self.freq, period=int(r['period']),
                reporter=rep, reporter_name=schema.ISO3_NAME.get(rep, rep),
                partner=par, partner_name=schema.ISO3_NAME.get(par, par),
                flow='import' if r.get('flowCode') == 'M' else 'export',
                hs6=cc, native_code=cc, code_level=6, material=concordance.material_for(cc, 6),
                value_usd=num(r.get('primaryValue')), qty_kg=num(r.get('netWgt')), is_mirror=False)
