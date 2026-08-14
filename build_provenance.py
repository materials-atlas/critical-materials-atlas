"""HS-code provenance map (JRC/CN-style): for every atlas material, which HS6 codes represent which stage,
and an explicit data-quality flag so users can see exactly which codes are clean vs shared vs trade-only.
This makes the caveats auditable rather than buried in prose. Writes out/code_provenance.json.
Run: python build_provenance.py
"""
import os, sys, json, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))

def nicename(m):
    t = m['title']; return t[:t.find('(')].strip() if '(' in t else t
def hs6(t):
    c = ''.join(ch for ch in t[t.find('(') + 1:t.find(')')] if ch.isdigit()); return c[:6]

# clean ore->refined pairs (the traceable chains)
ORE = {'copper': '260300', 'nickel': '260400', 'cobalt': '260500', 'tungsten': '261100',
       'titanium': '261400', 'antimony': '261710', 'bauxite': '260600', 'tantalum': '261590',
       'niobium': '261590', 'manganese': '260200'}
BYPRODUCT = {'gallium', 'germanium', 'hafnium', 'arsenic'}         # recovered from other ores -> no ore trade line
MINE_ONLY = {'baryte', 'cokingcoal', 'helium'}                     # no distinct refined stage in our data

def stage(code):
    h2, h4 = code[:2], code[:4]
    if h4 == '8505':                    return 'permanent magnet (downstream)'
    if h4 == '2804':                    return 'refined element / metalloid / gas'
    if h2 == '26':                      return 'ore / concentrate'
    if h2 == '28':                      return 'refined compound / oxide'
    if h2 == '72':                      return 'ferro-alloy'
    if h2 == '71':                      return 'unwrought precious metal'
    if h2 in ('74', '75', '76', '78', '79', '80', '81'): return 'unwrought metal'
    if h2 == '27':                      return 'coal'
    if h2 == '25':                      return 'processed mineral'
    return 'other'

# detect HS6 codes shared by >1 material
codes = collections.defaultdict(list)
for m in d['materials']:
    codes[hs6(m['title'])].append(m['label'])
shared = {c for c, labs in codes.items() if len(labs) > 1}

out = []
for m in d['materials']:
    lab = m['label']; ref = hs6(m['title']); ore = ORE.get(lab)
    if ref in shared:
        flag = f'shared HS6 ({"/".join(sorted(codes[ref]))}) — trade signal degenerate'
    elif lab in BYPRODUCT:
        flag = 'by-product — no ore trade line (feedstock signature undefined)'
    elif lab in MINE_ONLY:
        flag = 'mine / mineral only — no distinct refined stage'
    elif ore:
        flag = 'clean ore→refined pair — full trade fingerprint'
    else:
        flag = 'refined form only — no clean ore pair (typed from physical)'
    out.append({'label': lab, 'name': nicename(m), 'ore': ore, 'refined': ref,
                'refined_stage': stage(ref), 'flag': flag})

order = {'clean ore': 0, 'refined form': 1, 'shared': 2, 'by-product': 3, 'mine /': 4}
out.sort(key=lambda r: next((v for k, v in order.items() if r['flag'].startswith(k)), 9))
cnt = collections.Counter(r['flag'].split(' —')[0].split(' (')[0] for r in out)
json.dump({'shared_codes': sorted(shared), 'materials': out},
          open(os.path.join(ROOT, 'out', 'code_provenance.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('HS-code provenance:', dict(cnt))
for r in out:
    print(f"  {r['name'][:22]:22} ore={str(r['ore']):8} refined={r['refined']} [{r['refined_stage']:26}] {r['flag']}")
print('WROTE out/code_provenance.json')
