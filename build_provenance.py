"""HS-code provenance map -- now driven by the canonical out/crosswalk.json (single source of truth), so
the ore/refined codes and flags can't drift from the rest of the pipeline. For every atlas material it
reports the ore + refined HS codes, the refined stage, and a data-quality flag. Writes out/code_provenance.json.
Run: python build_provenance.py  (after build_crosswalk.py)
"""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
CW = json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf-8'))

def nicename(m):
    t = m['title']; return t[:t.find('(')].strip() if '(' in t else t
def stage(code):
    h2, h4 = code[:2], code[:4]
    if h4 == '8505':  return 'permanent magnet (downstream)'
    if h4 == '2804':  return 'refined element / metalloid / gas'
    if h2 == '26':    return 'ore / concentrate'
    if h2 == '28':    return 'refined compound / oxide'
    if h2 == '72':    return 'ferro-alloy'
    if h2 == '71':    return 'unwrought precious metal'
    if h2 in ('74', '75', '76', '78', '79', '80', '81'): return 'unwrought metal'
    if h2 == '27':    return 'coal'
    if h2 == '25':    return 'processed mineral'
    return 'other'

# flag -> human text + sort priority (most-limiting first)
FLAG = {'shared_refined': ('shared refined HS6 (gallium/germanium 811292) — trade signal degenerate', 0),
        'shared_ore':     ('shared ore HS6 (Nb-Ta 261590) — feedstock side unreliable', 1),
        'byproduct':      ('by-product — no ore trade line (feedstock signature undefined)', 3),
        'mine_only':      ('mine / mineral only — no distinct refined stage', 4),
        'magnet':         ('downstream magnet — refined form only', 2),
        'clean_pair':     ('clean ore→refined pair — full trade fingerprint', 2),
        'refined_only':   ('refined form only — no clean ore pair (typed from physical)', 3)}

out = []
for m in d['materials']:
    lab = m['label']; c = CW.get(lab, {'ore_hs': [], 'refined_hs': [''], 'flags': ['refined_only']})
    # pick the most-limiting flag for the label
    flag_key = min(c['flags'], key=lambda f: FLAG.get(f, ('', 9))[1])
    ref = (c['refined_hs'] or [''])[0]
    out.append({'label': lab, 'name': nicename(m),
                'ore': (c['ore_hs'] or [None])[0], 'refined': ref,
                'refined_all': c['refined_hs'], 'refined_stage': stage(ref),
                'flag': FLAG.get(flag_key, ('', 9))[0], 'flag_key': flag_key})

out.sort(key=lambda r: FLAG.get(r['flag_key'], ('', 9))[1])
import collections
cnt = collections.Counter(r['flag_key'] for r in out)
json.dump({'materials': out}, open(os.path.join(ROOT, 'out', 'code_provenance.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('HS-code provenance:', dict(cnt))
for r in out:
    print(f"  {r['name'][:22]:22} ore={str(r['ore']):8} refined={r['refined']} [{r['refined_stage']:26}] {r['flag']}")
print('WROTE out/code_provenance.json')
