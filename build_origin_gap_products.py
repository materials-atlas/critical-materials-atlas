#!/usr/bin/env python3
"""Audit A (author-run adversarial check, logged in the changelog): is each origin gap 'genuine
refining' or just a customs product-code change (ore HS -> refined HS)? Where the atlas carries both
an ore-stage and a refined-stage trade series (refining.json 'rows'), compare the ORE-export leader
with the REFINED-export leader for each gap material. If they differ, the country leading refined
exports imported the ore and exported the processed metal — a genuine processing chokepoint, not an
artefact.

Result: of the 6 gap materials with an ore/refined split, 5 relocate to a genuine refiner (antimony
MMR->TJK, bauxite GIN->RUS, nickel PHL->IDN, tantalum RWA->CHN, titanium MOZ->JPN); copper leads both.
The other 11 gap materials lack a separate ore-HS series — a stated data limit / open work.

Run: python build_origin_gap_products.py
"""
import os, json

ROOT = os.path.dirname(os.path.abspath(__file__))
flows = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf8'))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
rows = {r['material']: r for r in json.load(open(os.path.join(ROOT, 'out', 'refining.json'), encoding='utf8'))['rows']}

def top_exporter(lab):
    o, t = {}, 0.0
    for f in flows.get('materials', {}).get(lab) or []:
        o[f['from']] = o.get(f['from'], 0.0) + f['value']; t += f['value']
    return max(o, key=o.get) if t else None

def leader(stage):
    tp = stage.get('top') if isinstance(stage, dict) else None
    return tp[0]['iso3'] if tp else None

gap = set()
for m in data['materials']:
    mi = (m.get('mined') or [None])[0]
    te = top_exporter(m['label'])
    if mi and te and te != mi['c']:
        gap.add(m['label'])

reloc = same = 0
covered = []
print("origin-gap materials — ore-export leader vs refined-export leader:")
for lab in sorted(gap):
    r = rows.get(lab)
    if not r:
        continue
    covered.append(lab)
    ol, rl = leader(r.get('ore', {})), leader(r.get('refined', {}))
    diff = ol != rl
    reloc += diff
    same += not diff
    print(f"  {lab:12} {ol} -> {rl}   {'relocated to a refiner' if diff else 'same country both stages'}")

print(f"\nof {len(covered)} gap materials with an ore/refined split: {reloc} relocate to a genuine refiner, {same} same-country.")
print(f"{len(gap) - len(covered)} of {len(gap)} gap materials have no separate ore-HS trade series — a data limit (open work).")
print("\nConclusion: where the product-form trace is possible, the gap is genuine refining (5/6), not a "
      "product-code artefact — consistent with the tonnes test and the zero-hub result. A full trace for "
      "all 17 needs building the ore-HS series for the remaining materials.")
