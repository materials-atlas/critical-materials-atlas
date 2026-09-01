#!/usr/bin/env python3
"""Real-capacity coverage for the reallocation stress test (ot deepening) — CONSISTENT PRODUCTION BASIS.

A reviewer's fair push on the OT page: its 'can the rest cover the cut?' coverage uses an ASSUMED uniform
scale-up ceiling (kappa = survivors double/triple current output). True per-country processing-capacity
ceilings do not exist in public data for most materials -- so for the 8 commodities where the USGS World
Minerals Outlook DOES publish forward capacity (to 2029), we ground the ceiling in the real number.

IMPORTANT (v2, corrected): everything here is on ONE consistent basis -- PRODUCTION. The dominant
producer's share of world capacity P and the projected world capacity growth g both come from the same
USGS Outlook. (An earlier version wrongly divided production-capacity growth by the TRADE export-leader's
share -- a different country for e.g. cobalt, where the refined-export leader is Finland but the real
producer is the DRC -- which made the numbers incoherent.) We report two apples-to-apples figures:

  real_coverage = min(1, g / P)               how much a cut of the dominant producer real capacity plans
                                              could backfill by 2029
  double_coverage = min(1, (1 - P) / P)       the naive 'everyone else doubles' hope, same basis

The finding: where P is huge (gallium 87%, magnesium 89%, cobalt 75%) even doubling barely dents the gap;
and where doubling WOULD help (palladium, platinum, helium; leaders < 75%), USGS says the capacity to do
it is not being built (g ~ 0). Either way a cut of the dominant producer is far less coverable than a
naive read suggests. Only lithium (+111%) is genuinely building enough.

Reads out/usgs_outlook.json. Run: python build_ot_capacity.py -> out/ot_capacity.json
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
usgs = json.load(open(os.path.join(ROOT, 'out', 'usgs_outlook.json'), encoding='utf-8'))['materials']

NAME = {'cobalt': 'Cobalt', 'gallium': 'Gallium', 'helium': 'Helium', 'lithium': 'Lithium',
        'magnesium': 'Magnesium', 'palladium': 'Palladium', 'platinum': 'Platinum', 'titanium': 'Titanium'}
CN = {'CD': 'DR Congo', 'CN': 'China', 'US': 'United States', 'AU': 'Australia', 'ZA': 'South Africa'}

rows = []
for lab, u in usgs.items():
    g = u.get('world_growth_pct')
    P = u.get('top_share')            # dominant PRODUCER share of world capacity (USGS)
    if g is None or not P:
        continue
    real = max(0.0, min(1.0, (g / 100.0) / (P / 100.0)))   # coverage floored at 0 (can't be negative)
    dbl = min(1.0, (1 - P / 100.0) / (P / 100.0))
    rows.append({'label': lab, 'name': NAME.get(lab, lab.title()), 'stage': u.get('stage'),
                 'producer': CN.get(u.get('top'), u.get('top')), 'producer_share': round(P),
                 'capacity_growth_pct': g, 'capacity_shrinking': g < 0,
                 'world_2024': u.get('world_2024'), 'world_2029': u.get('world_2029'),
                 'real_coverage': round(real, 3), 'double_coverage': round(dbl, 3)})
rows.sort(key=lambda r: r['real_coverage'])
out = {'note': ('OPTIMISTIC UPPER BOUND on covering a dominant-producer cut, on a consistent PRODUCTION '
                'basis, for the 8 commodities USGS publishes forward capacity for. real_coverage = '
                'max(0, min(1, capacity-growth / producer-share)) -- generous, because it assumes ALL '
                'projected gross capacity growth to 2029 is spare, exportable, and OUTSIDE the cut '
                'country, ignoring baseline demand growth. Even so it is small for the concentrated '
                'materials. double_coverage = min(1, (1-producer-share)/producer-share) is the naive '
                '"everyone else doubles" hope. Not a forecast; a bound.'),
       'materials': rows}
json.dump(out, open(os.path.join(ROOT, 'out', 'ot_capacity.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f"{'material':11}{'producer':>14}{'growth':>8}{'real cover':>11}{'if doubled':>12}")
for r in rows:
    print(f"{r['name'][:10]:11}{r['producer'][:9]+' '+str(r['producer_share'])+'%':>14}{r['capacity_growth_pct']:>7}%"
          f"{round(r['real_coverage']*100):>10}%{round(r['double_coverage']*100):>11}%")
print("wrote out/ot_capacity.json")
