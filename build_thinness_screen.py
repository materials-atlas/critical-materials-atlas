#!/usr/bin/env python3
"""Ex-ante thinness screen for every tracked commodity (author-run; answers an adversarial-council
demand). Cobalt's trend was set aside as un-estimable because its tracked code (HS 2822.00) carries only
$1-5M/yr, so a few flows swing the HHI. A reviewer rightly objected that excluding cobalt AFTER it became
the inconvenient case is ad hoc unless the same rule is applied to ALL commodities BEFORE looking at
outcomes. So we screen every tracked code, up front, on three fragility signals:

  1. annual trade value (a thin market is a few flows dressed as a distribution)
  2. number of active exporters (few exporters -> HHI is mechanical, not informative)
  3. top-1 leverage: how much the HHI moves if the single largest exporter flow is dropped
     (high leverage -> one flow drives the whole concentration signal)

A commodity is flagged THIN-FRAGILE if trade value < $100M OR fewer than 8 active exporters OR the
top-1-drop moves HHI by more than 0.10. Concentration and trend claims on flagged codes should be read
as indicative, not measured. This is the ex-ante rule cobalt should have been caught by.

Run: python build_thinness_screen.py   ->  writes out/thinness_screen.json   (uses official BACI 2024)
"""
import os, csv, json
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
XW = json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf-8'))
CODE2NAME = {}
for name, e in XW.items():
    if e.get('title_code'):
        CODE2NAME.setdefault(e['title_code'], name)

exp = defaultdict(lambda: defaultdict(float))     # cmd -> exporter -> value
for r in csv.DictReader(open(os.path.join(ROOT, 'reconcile', 'baci_2024.csv'), encoding='utf-8')):
    try:
        exp[r['cmd']][r['i']] += float(r['value'])
    except (ValueError, KeyError):
        continue

def hhi(d):
    t = sum(d.values())
    return sum((v / t) ** 2 for v in d.values()) if t else None

VAL_MIN, N_MIN, LEV_MAX = 100e6, 8, 0.10
rows = []
for code, d in exp.items():
    total = sum(d.values())
    n = sum(1 for v in d.values() if v > 0)
    h = hhi(d)
    # top-1 leverage: HHI recomputed with the single biggest exporter removed
    if len(d) > 1:
        top = max(d, key=d.get)
        d2 = {k: v for k, v in d.items() if k != top}
        lev = abs(h - hhi(d2)) if hhi(d2) is not None else None
    else:
        lev = 1.0
    thin = (total < VAL_MIN) or (n < N_MIN) or (lev is not None and lev > LEV_MAX)
    reasons = []
    if total < VAL_MIN: reasons.append('low trade value')
    if n < N_MIN: reasons.append('few exporters')
    if lev is not None and lev > LEV_MAX: reasons.append('top-1 leverage')
    rows.append({'code': code, 'name': CODE2NAME.get(code, code),
                 'trade_value_musd': round(total / 1e6, 1), 'n_exporters': n,
                 'hhi': round(h, 3) if h else None,
                 'top1_leverage': round(lev, 3) if lev is not None else None,
                 'thin_fragile': bool(thin), 'reasons': reasons})

rows.sort(key=lambda r: (not r['thin_fragile'], r['trade_value_musd']))
flagged = [r for r in rows if r['thin_fragile']]
out = {'note': ('Ex-ante thinness screen on official BACI 2024. A commodity is THIN-FRAGILE if annual '
                f'trade value < ${VAL_MIN/1e6:.0f}M, or fewer than {N_MIN} active exporters, or dropping '
                f'the single largest exporter moves HHI by more than {LEV_MAX}. Concentration/trend claims '
                'on flagged codes are indicative, not measured.'),
       'thresholds': {'value_musd_min': VAL_MIN / 1e6, 'n_exporters_min': N_MIN, 'top1_leverage_max': LEV_MAX},
       'n_flagged': len(flagged), 'n_total': len(rows), 'materials': rows}
json.dump(out, open(os.path.join(ROOT, 'out', 'thinness_screen.json'), 'w', encoding='utf-8'),
          indent=1, ensure_ascii=False)

print(f"thin-fragile: {len(flagged)}/{len(rows)} commodities")
print(f"{'name':14}{'$M':>9}{'#exp':>6}{'HHI':>7}{'top1lev':>9}  flags")
for r in rows:
    mark = '  <<' if r['thin_fragile'] else ''
    print(f"{r['name'][:13]:14}{r['trade_value_musd']:9.0f}{r['n_exporters']:6}{(r['hhi'] or 0):7.2f}"
          f"{(r['top1_leverage'] or 0):9.3f}  {','.join(r['reasons'])}{mark}")
print("\nwrote out/thinness_screen.json")
