#!/usr/bin/env python3
"""Origin ledger — the complete per-material mine -> exporter trace (flagship-deepening).

A reviewer's fair poke at the origin gap: the headline "for 17 of 32 materials the top exporter never
mined it" was backed by a full per-material ORE-TRADE trace for only 6 materials (those carrying both an
ore-HS and a refined-HS series); the other 11 were flagged "data-limited". This closes that flank by
tracing every gap material to its origin the RIGHT way -- to the MINE (production), not to an ore-trade
series that is itself re-exportable. For each material we set the largest mine producer (World Mining
Data) beside the largest exporter (reconciled trade): where they are different countries, that IS the
origin gap, now enumerated material by material. The separate ore-trade cross-check (6 materials) becomes
a bonus corroboration, not the load-bearing evidence.

Run: python build_origin_ledger.py  ->  out/origin_ledger.json  (+ prints the table)
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
prod = {r['label']: r for r in json.load(open(os.path.join(ROOT, 'out', 'production.json'), encoding='utf8'))['rows']}
flows = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf8'))
NAMES = flows['names']
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
TITLES = {m['label']: m['title'].split(' (')[0] for m in data['materials']}

# the 6 materials with a SEPARATE ore-HS series, where the ore->refined hand-off is directly corroborated
ORE_TRADE = {'antimony', 'bauxite', 'nickel', 'tantalum', 'titanium', 'manganese'}

rows = []
for lab, fl in flows['materials'].items():
    by = {}
    for f in fl:
        by[f['from']] = by.get(f['from'], 0) + f['value']
    t = sum(by.values())
    p = prod.get(lab)
    if not t or not p or not p.get('wmd_top'):
        continue
    exp_iso = max(by, key=by.get)
    exp_name, exp_sh = NAMES.get(exp_iso, exp_iso), round(100 * by[exp_iso] / t)
    mine_name, mine_sh, mine_iso = p['wmd_top'], round(p.get('wmd_top_share') or 0), p.get('wmd_top_iso')
    gap = bool(mine_iso and exp_iso and mine_iso != exp_iso
               and mine_name.split(',')[0].lower() not in exp_name.lower())
    rows.append({'label': lab, 'title': TITLES.get(lab, lab),
                 'mine': mine_name, 'mine_share': mine_sh,
                 'exporter': exp_name, 'export_share': exp_sh,
                 'gap': gap, 'ore_trade_corroborated': lab in ORE_TRADE})

gaps = [r for r in rows if r['gap']]
gaps.sort(key=lambda r: -r['mine_share'])
out = {'note': ('Complete mine -> exporter trace. For each material the largest mine producer (World '
                'Mining Data) beside the largest exporter (reconciled trade 2024); "gap" = different '
                'countries = the origin gap, enumerated. ore_trade_corroborated marks the materials that '
                'ALSO carry a separate ore-HS series confirming the hand-off directly.'),
       'n_gap': len(gaps), 'n_ore_corroborated': sum(r['ore_trade_corroborated'] for r in gaps),
       'materials': gaps}
json.dump(out, open(os.path.join(ROOT, 'out', 'origin_ledger.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

print(f"origin gap (mine leader != export leader): {len(gaps)} materials; "
      f"{out['n_ore_corroborated']} also corroborated by a separate ore-trade series")
for r in gaps:
    mark = ' [ore-trade ok]' if r['ore_trade_corroborated'] else ''
    print(f"  {r['title'][:24]:24} mine {r['mine'][:14]:14} {r['mine_share']:>3}%  ->  exports "
          f"{r['exporter'][:14]:14} {r['export_share']:>3}%{mark}")
print('wrote out/origin_ledger.json')
