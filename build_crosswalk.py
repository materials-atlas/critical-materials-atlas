"""Canonical material crosswalk -- the single source of truth for HS codes + data-quality flags, so the
ore/refined codes and shared/by-product handling can no longer drift between builders (the council's #1
finding). Every consumer (exposure, scenario, provenance, feedstock typing) should read out/crosswalk.json
rather than parse HS codes from data.json titles.

For each material: ore_hs[] (upstream), refined_hs[] (the traded refined basket), and flags:
  clean_pair       distinct ore + distinct refined -> full trade feedstock fingerprint
  shared_ore       ore HS6 shared with another material (Ta/Nb 261590) -> feed side unreliable
  shared_refined   refined HS6 shared (Ga/Ge 811292) -> trade signal degenerate
  byproduct        recovered from other ores, no ore trade line
  mine_only        no distinct refined stage
  refined_only     a refined form with no clean ore pair (typed from physical)
  magnet           downstream NdFeB
Run: python build_crosswalk.py
"""
import os, json
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))

def hs6(t):
    c = ''.join(ch for ch in t[t.find('(') + 1:t.find(')')] if ch.isdigit()); return c[:6]

# clean ore -> refined basket (distinct, non-shared). Refined baskets match build_feedstock/build_refining.
CLEAN = {'copper': (['260300'], ['740311']), 'nickel': (['260400'], ['750210', '720260']),
         'cobalt': (['260500'], ['282200']), 'tungsten': (['261100'], ['810194', '284180']),
         'titanium': (['261400'], ['810820']), 'antimony': (['261710'], ['811010']),
         'bauxite': (['260600'], ['281820']),                                   # refined = ALUMINA, not the ore
         'manganese': (['260200'], ['811100', '720211', '720219', '720230'])}   # refined = Mn metal + ferro/silico-Mn
SHARED_ORE = {'tantalum': (['261590'], ['810320']), 'niobium': (['261590'], ['720293'])}  # share the Nb-Ta ore
SHARED_REFINED = {'gallium', 'germanium'}          # both HS6 811292
MINE_ONLY = {'baryte', 'cokingcoal', 'helium'}
BYPRODUCT = {'arsenic', 'hafnium'}                 # + gallium/germanium (flagged shared_refined instead)
MAGNET_ORE = ['280530', '284690']

out = {}
for m in d['materials']:
    lab = m['label']; title_code = hs6(m['title'])
    if lab in CLEAN:
        ore, ref = CLEAN[lab]; flags = ['clean_pair']
    elif lab in SHARED_ORE:
        ore, ref = SHARED_ORE[lab]; flags = ['shared_ore']
    elif lab == 'magnets':
        ore, ref = MAGNET_ORE, ['850511']; flags = ['magnet']
    elif lab in SHARED_REFINED:
        ore, ref = [], [title_code]; flags = ['shared_refined', 'byproduct']
    elif lab in MINE_ONLY:
        ore, ref = [], [title_code]; flags = ['mine_only']
    elif lab in BYPRODUCT:
        ore, ref = [], [title_code]; flags = ['byproduct']
    else:
        ore, ref = [], [title_code]; flags = ['refined_only']
    out[lab] = {'ore_hs': ore, 'refined_hs': ref, 'title_code': title_code, 'flags': flags}

json.dump(out, open(os.path.join(ROOT, 'out', 'crosswalk.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
from collections import Counter
c = Counter(f for v in out.values() for f in v['flags'])
print('crosswalk:', dict(c))
for lab, v in out.items():
    print(f"  {lab:12} ore={v['ore_hs']} refined={v['refined_hs']} {v['flags']}")
print('WROTE out/crosswalk.json')
