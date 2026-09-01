#!/usr/bin/env python3
"""Real-capacity coverage for the reallocation stress test (ot deepening).

A reviewer's fair push on the OT page: its 'can the rest cover the cut?' coverage uses an ASSUMED uniform
scale-up ceiling (kappa = survivors can 2x/3x/5x current exports). True per-country processing-capacity
ceilings do not exist in public data for most materials -- so we do the honest thing: for the 8
commodities where the USGS World Minerals Outlook DOES publish forward capacity (to 2029), we replace the
guessed kappa with the REAL projected capacity growth, and show how much of a leader-cut it could cover.

The finding is sobering and decision-relevant: USGS projects world capacity growing only ~12-30% by 2029
for these materials, so even if EVERY new tonne of capacity replaced the cut leader, it would cover only
a fraction of the gap -- far less than the abstract 'survivors double' (kappa=2). Coverage upper bound:
   cap_coverage = min(1, world_capacity_growth / leader_export_share)
i.e. new capacity to 2029, as a fraction of what the leader ships, is the most that plan can backfill.

Reads out/ot.json (leader export shares) + out/usgs_outlook.json (forward capacity).
Run: python build_ot_capacity.py  ->  out/ot_capacity.json
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
ot = json.load(open(os.path.join(ROOT, 'out', 'ot.json'), encoding='utf-8'))
OTM = ot['materials'] if isinstance(ot, dict) and 'materials' in ot else ot
if isinstance(OTM, dict):
    OTM = list(OTM.values())
OT = {m['label']: m for m in OTM}
usgs = json.load(open(os.path.join(ROOT, 'out', 'usgs_outlook.json'), encoding='utf-8'))['materials']

rows = []
for lab, u in usgs.items():
    o = OT.get(lab)
    if not o:
        continue
    fL = o.get('leader_export_share')          # leader's share of world refined exports (0..1)
    g = u.get('world_growth_pct')              # projected world capacity growth to 2029, %
    if fL is None or g is None:
        continue
    cap_cover = min(1.0, (g / 100.0) / fL) if fL > 0 else 1.0
    # the OT page's optimistic sweep, for contrast
    kappa2 = o.get('coverage', {}).get('2')
    rows.append({
        'label': lab, 'name': o.get('name', lab), 'stage': u.get('stage'),
        'leader': o.get('leader_name'), 'leader_export_share': round(fL, 3),
        'usgs_capacity_growth_pct': g, 'world_2024': u.get('world_2024'), 'world_2029': u.get('world_2029'),
        'real_cap_coverage': round(cap_cover, 3),
        'kappa2_coverage': kappa2,               # the abstract 'survivors double' figure, for comparison
    })
rows.sort(key=lambda r: r['real_cap_coverage'])
out = {'note': ('Coverage of a leader-cut under REAL USGS-projected capacity growth to 2029, for the 8 '
                'commodities USGS publishes forward capacity for. cap_coverage = min(1, capacity-growth / '
                'leader-export-share): the most that the planned new capacity could backfill. Contrast '
                'kappa2_coverage, the OT page\'s optimistic "survivors double" assumption. Where the two '
                'diverge, the abstract ceiling flatters the real plans.'),
       'materials': rows}
json.dump(out, open(os.path.join(ROOT, 'out', 'ot_capacity.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f"{len(rows)} commodities with real USGS forward capacity:")
print(f"{'material':12}{'leader%':>8}{'cap growth':>11}{'real cover':>11}{'k=2 cover':>10}")
for r in rows:
    print(f"{r['name'][:11]:12}{r['leader_export_share']*100:7.0f}%{r['usgs_capacity_growth_pct']:>10}%"
          f"{r['real_cap_coverage']*100:>10.0f}%{(r['kappa2_coverage'] or 0)*100:>9.0f}%")
print("wrote out/ot_capacity.json")
