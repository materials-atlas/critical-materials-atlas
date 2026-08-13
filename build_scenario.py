"""Refining supply-shock stress test -- the DEFENSIBLE form of a 'scenario'. Not a forecast: a
counterfactual on the current refined-share data. For each material: if the single largest refiner
stopped supplying the world market, how much refined output is lost, is there a credible fallback, and
how concentrated is what remains? Flags single-point-of-failure materials (leader >=50% and no fallback
above a third of the leader). Reuses the BGS/USGS refined shares behind the chokepoint index.

Writes out/scenario.json. Run: python build_scenario.py
"""
import os, json
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))

def nicename(m):
    t = m['title']; return t[:t.find('(')].strip() if '(' in t else t

rows = []
for m in d['materials']:
    ref = sorted(((x['c'], x['v']) for x in (m.get('refined') or [])), key=lambda kv: -kv[1])
    if not ref:
        continue
    leader, lead_share = ref[0]
    fb, fb_share = (ref[1] if len(ref) > 1 else (None, 0.0))
    remaining = [(c, v) for c, v in ref[1:]]
    rem_tot = sum(v for _, v in remaining)
    residual_hhi = sum((v / rem_tot) ** 2 for _, v in remaining) if rem_tot > 0 else 1.0
    spof = lead_share >= 50 and fb_share < lead_share / 3.0
    rows.append({'label': m['label'], 'name': nicename(m), 'leader': leader, 'lead_share': round(lead_share, 1),
                 'fallback': fb, 'fallback_share': round(fb_share, 1), 'lost_if_removed': round(lead_share, 1),
                 'residual_hhi': round(residual_hhi, 3), 'spof': spof})

rows.sort(key=lambda r: -r['lost_if_removed'])
spof_n = sum(r['spof'] for r in rows)
cn_spof = [r for r in rows if r['spof'] and r['leader'] == 'CN']
print('=== refining supply-shock stress test: remove the top refiner ===')
print(f"{'material':24} lose  fallback              residual  SPOF")
for r in rows:
    fb = f"{r['fallback']} {r['fallback_share']:.0f}%" if r['fallback'] else '—'
    print(f"  {r['name'][:22]:22} {r['lost_if_removed']:4.0f}%  {fb:20} HHI {r['residual_hhi']:.2f}"
          f"  {'<< SINGLE POINT' if r['spof'] else ''}")
print(f"\n{spof_n}/{len(rows)} materials are refining SINGLE POINTS OF FAILURE "
      f"(leader >=50%, no fallback above a third); China is the leader in {len(cn_spof)} of them:")
print('  ', ', '.join(r['name'] for r in cn_spof))
json.dump({'materials': rows, 'spof_count': spof_n},
          open(os.path.join(ROOT, 'out', 'scenario.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('\nWROTE out/scenario.json')
