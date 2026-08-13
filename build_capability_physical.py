"""Physical capability typing for ALL critical materials -- the card-per-material the trade fingerprint
could only give for 7. It needs no HS ore->refined pair: it reads each country's MINE share vs REFINE
share (BGS/USGS physical, from data.json) and types the handoff directly:

  integrated (mine+refine)  mine>=10% and refine>=10%   -- does both
  import-fed refiner         refine >= 2x mine (refine>=5) -- refines far more than it digs (imports feed)
  mine-to-metal refiner      refines, roughly in line with what it mines
  raw exporter               mine>=8% and refine<3%       -- digs it, doesn't refine it

Every material with both layers (29/32) gets a card showing, per country, the mine bar vs the refine
bar -- the mine->refine handoff made visible. Writes out/capability_physical.json.
Run:  python build_capability_physical.py
"""
import os, json
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))

def nicename(m):
    t = m['title']; return t[:t.find('(')].strip() if '(' in t else t

def typ(mine, ref):
    if ref < 3:
        return 'raw exporter' if mine >= 8 else 'minor'
    if ref >= 2 * max(mine, 1):            # refines far more than it digs -> feedstock-importing
        return 'import-fed refiner'
    if mine >= 10 and ref >= 10:
        return 'integrated (mine+refine)'
    return 'mine-to-metal refiner'

out = {}
for m in d['materials']:
    mine = {x['c']: x['v'] for x in (m.get('mined') or [])}
    ref = {x['c']: x['v'] for x in (m.get('refined') or [])}
    if not ref:
        continue
    countries = sorted(set(mine) | set(ref), key=lambda c: -max(mine.get(c, 0), ref.get(c, 0)))
    rows = []
    for c in countries:
        mm, rr = mine.get(c, 0), ref.get(c, 0)
        t = typ(mm, rr)
        if t == 'minor':
            continue
        rows.append({'iso': c, 'mine': round(mm, 1), 'refine': round(rr, 1), 'type': t})
    out[m['label']] = {
        'name': nicename(m),
        'mine_leader': max(mine, key=mine.get) if mine else None,
        'refine_leader': max(ref, key=ref.get) if ref else None,
        'refine_source': m.get('refined_source', ''),
        'rows': rows[:7]}

json.dump(out, open(os.path.join(ROOT, 'out', 'capability_physical.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
# report
print(f'physical capability cards: {len(out)} materials')
from collections import Counter
tc = Counter(r['type'] for v in out.values() for r in v['rows'])
print('type counts:', dict(tc))
for lab in ['antimony', 'tungsten', 'platinum', 'lithium', 'cobalt']:
    if lab in out:
        rr = ', '.join(f"{r['iso']}(m{r['mine']:.0f}/r{r['refine']:.0f} {r['type'].split()[0]})" for r in out[lab]['rows'][:4])
        print(f"  {lab:10} {rr}")
print('WROTE out/capability_physical.json')
