#!/usr/bin/env python3
"""Two-stage anchor for the stage-divergent materials. The single-stage anchor mis-signals lithium and
graphite because it compares MINE production to trade at a REFINED/processed HS code. The fix is to match
stages: anchor mine output to the ORE-stage trade, refined output to the REFINED-stage trade.

Graphite splits cleanly by HS code: natural graphite (2504.10, ~the mined flake) vs processed/other graphite
(2504.90) + artificial/synthetic (3801.10). Lithium does NOT: spodumene concentrate has no dedicated HS6
(it is lumped in 2530.90 'other mineral substances'), so lithium's MINE stage is invisible in trade — only
refined carbonate/oxide (2836.91) is trackable. That invisibility is itself the finding.

Streams the full BACI 2023 file (raw/baci/BACI_HS17_Y2023...csv inside the zip), sums exports by country per
stage code, and reports the export-origin share at each stage beside the mine leader. Run: python build_two_stage.py
"""
import csv, io, json, os, zipfile
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import baci as _baci  # the one door for BACI (ARCHITECTURE.md phase 2)

ROOT = os.path.dirname(os.path.abspath(__file__))
Z = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
MEMBER = 'BACI_HS17_Y2023_V202601.csv'
prod = {r['label']: r for r in json.load(open(os.path.join(ROOT, 'out', 'production.json'), encoding='utf8'))['rows']}
I2ISO = {}
for r in csv.DictReader(_baci.country_file()):
    try: I2ISO[r['country_code']] = r['country_iso3']
    except KeyError: pass

# stage code sets we care about (HS17)
STAGES = {
 'graphite': {'ore (natural flake, 2504.10)': {'250410'},
              'processed (spherical/other 2504.90 + synthetic 3801.10)': {'250490', '380110'}},
 'lithium':  {'refined (carbonate/oxide, 2836.91)': {'283691'}},  # ore = spodumene has NO clean HS6 -> untrackable
}
WANT = {c for m in STAGES for st in STAGES[m].values() for c in st}

exp = {c: {} for c in WANT}   # exp[code][iso] = qty (tonnes)
for row in _baci.year(2023, columns=['i', 'k', 'v', 'q'], codes=WANT).itertuples(index=False):
    k = row.k
    iso = I2ISO.get(str(row.i))
    if not iso: continue
    q = row.q if row.q == row.q else row.v      # NULL q -> fall back to value, as before
    if q != q: continue
    exp[k][iso] = exp[k].get(iso, 0.0) + q

def top_shares(codes, n=6):
    agg = {}
    for c in codes:
        for iso, q in exp[c].items(): agg[iso] = agg.get(iso, 0.0) + q
    tot = sum(agg.values()) or 1
    return [{'iso': i, 'share': round(100*q/tot, 1)} for i, q in sorted(agg.items(), key=lambda kv: -kv[1])[:n]], round(tot)

out = {'note': ('Two-stage view: export-origin shares at the ORE stage vs the REFINED/processed stage, from '
                'full BACI 2023. Resolves the stage-divergent materials — the mine leader is credited at the '
                'ore stage; the refiner dominates the processed stage; and lithium’s ore stage is untrackable '
                '(spodumene has no dedicated HS6).'), 'materials': {}}
print(f"{'material/stage':52}{'top exporters (share%)':40}")
for m, stages in STAGES.items():
    p = prod.get(m, {})
    mine = {'leader': p.get('wmd_top'), 'share': round(p.get('wmd_top_share') or 0)}
    rec = {'mine_leader': mine, 'stages': []}
    for label, codes in stages.items():
        rows, tot = top_shares(codes)
        rec['stages'].append({'stage': label, 'tonnes': tot, 'top': rows})
        top = ', '.join(f"{r['iso']} {r['share']}%" for r in rows[:4])
        print(f"  {m+' | '+label:50}{top}")
    out['materials'][m] = rec
    print(f"     (mine leader per WMD: {mine['leader']} {mine['share']}%)")
json.dump(out, open(os.path.join(ROOT, 'out', 'two_stage.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('wrote out/two_stage.json')
