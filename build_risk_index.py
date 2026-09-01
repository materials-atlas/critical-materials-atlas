#!/usr/bin/env python3
"""Reweightable supply-risk index — one page that replaces five. A product audit found the atlas had
half a dozen pages (risk, criticality, geopolrisk, risk-adjusted, volume) that all reweight the SAME
concentration index and then argue about the weights. The honest answer is not another fixed ranking; it
is to hand the reader the weights. This assembles, per material, every ingredient those pages used, so a
single interactive index can recompute and re-rank live as you toggle:

  - unit        : concentration on trade VALUE, trade VOLUME (tonnes), or MINE PRODUCTION (three HHIs)
  - governance  : weight by the top producer's governance risk (WGI) -- amplify autocracies, damp democracies
  - recycling   : discount materials with real secondary supply (a shortage you can partly recycle away)
  - substitution: discount materials with a ready substitute

The point the page makes by existing: there is NO single supply-risk number -- it depends on what you
weight -- so the atlas shows the choice instead of hiding it. Ingredients from the existing risk pages'
own outputs (geopolrisk.json, risk.json). Run: python build_risk_index.py -> out/risk_index.json
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
gp = {r['label']: r for r in json.load(open(os.path.join(ROOT, 'out', 'geopolrisk.json'), encoding='utf8'))['rows']}
rk = {m['label']: m for m in json.load(open(os.path.join(ROOT, 'out', 'risk.json'), encoding='utf8'))['materials']}

SUB = {'high': 1.0, 'medium': 0.6, 'med': 0.6, 'low': 0.2, 'none': 0.0}

rows = []
for lab, g in gp.items():
    r = rk.get(lab, {})
    recycling = r.get('recycling')            # 0-100 % secondary supply
    sub = str(r.get('substitutability', '')).lower()
    rows.append({
        'label': lab, 'title': g['title'],
        'hhi_value': round(g.get('hhi_value', 0), 3),
        'hhi_volume': round(g.get('hhi_volume', 0), 3),
        'hhi_prod': round(g.get('hhi_prod', 0), 3),
        'gov_risk': round(g.get('gov_risk', 0.5), 3),      # 0..1, higher = worse governance of top producer
        'recycling': recycling if isinstance(recycling, (int, float)) else 0,
        'substitutability': sub or 'unknown',
        'sub_ease': SUB.get(sub, 0.3),                      # 0..1, higher = easier to substitute
        'top_producer': g.get('top_producer'), 'top_share': g.get('top_share'),
    })
rows.sort(key=lambda r: -r['hhi_value'])
out = {'note': ('Ingredients for a reweightable supply-risk index. score = concentration(unit) x '
                'governance-factor x recycling-discount x substitution-discount, each toggle optional. '
                'There is no single risk number; the page lets the reader choose the weights.'),
       'n': len(rows), 'materials': rows}
json.dump(out, open(os.path.join(ROOT, 'out', 'risk_index.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f"risk_index: {len(rows)} materials assembled (value/volume/prod HHI + governance + recycling + substitutability)")
print('wrote out/risk_index.json')
