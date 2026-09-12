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

def leader(share):
    """(winner, everyone level with it). The winner is picked alphabetically among ties so it is
    the same on every run; the list is returned so a tie is never presented as a result."""
    if not share:
        return None, []
    top = max(share.values())
    tied = sorted(c for c, v in share.items() if v == top)
    return tied[0], tied


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
    if not mine and not ref:
        continue                              # nothing to show at all
    # THE TIEBREAK IS NOT DECORATION. Sorting a set by value alone leaves tied countries in
    # whatever order the set happened to iterate, which changes between processes because string
    # hashing is randomised - so this file used to produce two different orderings from identical
    # data, and the reproducibility audit caught it by running the builder twice. The ISO code is
    # the tiebreak: arbitrary, but the SAME arbitrary every time, which is the whole requirement.
    countries = sorted(set(mine) | set(ref),
                       key=lambda c: (-max(mine.get(c, 0), ref.get(c, 0)), c))
    rows = []
    for c in countries:
        mm, rr = mine.get(c, 0), ref.get(c, 0)
        t = typ(mm, rr)
        if t == 'minor':
            continue
        rows.append({'iso': c, 'mine': round(mm, 1), 'refine': round(rr, 1), 'type': t})
    mlead, mtied = leader(mine)
    rlead, rtied = leader(ref)
    # Is the 7-row cut splitting a tie? Compare the last row shown with the first one dropped, on
    # the same quantity the ordering used.
    def _key(r):
        return max(r['mine'], r['refine'])
    cut_tie = bool(len(rows) > 7 and _key(rows[6]) == _key(rows[7]))
    out[m['label']] = {
        'name': nicename(m),
        # max() over a dict returns the first key it meets at the highest value, and "first" is
        # not defined when two countries are level. sorted() first makes the winner reproducible.
        'mine_leader': mlead,
        'refine_leader': rlead,
        # A tie is reported, not resolved. Iran and Spain both mine 38% of world strontium; naming
        # one of them the leader and dropping the other is a claim the data does not support.
        'mine_leader_tied': mtied if len(mtied) > 1 else None,
        'refine_leader_tied': rtied if len(rtied) > 1 else None,
        'refine_source': m.get('refined_source', ''),
        # The card shows seven rows. Where the eighth is level with the seventh the cut is a coin
        # toss, and the page must be able to say so: four countries refine 3% of world nickel and
        # only three of them fit.
        'rows_total': len(rows),
        'cut_inside_tie': cut_tie,
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
