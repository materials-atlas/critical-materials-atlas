"""Directional 2026 nowcast: carry the reconciled 2025 bilateral structure forward, scaled per material
by reporter-matched Q1-2026 vs Q1-2025 export momentum (same set of reporters each year, to strip out
coverage changes). Optional price overlay (Pink Sheet) is applied if reconcile/pink_momentum.json exists.
Shares stay at 2025 (one partial quarter can't credibly predict structural shifts); levels move.
Output: out/flows_2026.json (provisional, year-to-date momentum).
"""
import os, sys, time, json
import requests, pandas as pd, numpy as np
ROOT = os.environ.get('ATLAS_ROOT', '.')
KEY = os.environ.get('COMTRADE_KEY', '')
if not KEY: sys.exit('set COMTRADE_KEY')

d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
def hs6(m):
    t = m['title']; c = ''.join(ch for ch in t[t.find('(')+1:t.find(')')] if ch.isdigit()); return c[:6]
codes = sorted({hs6(m) for m in d['materials']})
code2lab = {}
for m in d['materials']:
    c = hs6(m); c = '811292' if c == '811231' else c
    code2lab.setdefault(c, []).append(m['label'])

B = 'https://comtradeapi.un.org/data/v1/get/C/M/HS'; H = {'Ocp-Apim-Subscription-Key': KEY}
def pull(ym):
    for a in range(6):
        try:
            r = requests.get(B, headers=H, params={'period': ym, 'cmdCode': ','.join(codes), 'flowCode': 'X'}, timeout=120)
            if r.status_code == 200:
                return r.json().get('data', []) or []
        except Exception as e:
            print('  retry', ym, str(e)[:40], flush=True)
        time.sleep(5 + a*5)
    print('FAIL', ym, flush=True); return []

rows = []
for ym in ['202501', '202502', '202503', '202601', '202602', '202603']:
    data = pull(ym)
    yr = 2025 if ym.startswith('2025') else 2026
    for x in data:
        if x.get('partnerCode') == 0: continue                # drop World aggregate
        v = x.get('primaryValue')
        if v: rows.append((yr, x['reporterCode'], str(x['cmdCode']).zfill(6), float(v)))
    print(ym, 'rows', len(data), flush=True); time.sleep(2.5)
df = pd.DataFrame(rows, columns=['year', 'reporter', 'cmd', 'value'])
df['cmd'] = df.cmd.replace('811231', '811292')

# reporter-matched Q1 momentum per material
mom = {}; diag = []
for cmd, labs in code2lab.items():
    sub = df[df.cmd == cmd]
    e25 = sub[sub.year == 2025].groupby('reporter').value.sum()
    e26 = sub[sub.year == 2026].groupby('reporter').value.sum()
    common = e25.index.intersection(e26.index)
    if len(common) >= 3 and e25[common].sum() > 0:
        f = float(e26[common].sum() / e25[common].sum())
        f = min(max(f, 0.4), 2.5)                              # cap implausible swings
        src = f'Q1 trade ({len(common)} reporters)'
    else:
        f = 1.0; src = 'persistence (thin Q1 coverage)'
    for lab in labs: mom[lab] = f
    diag.append((labs[0] if len(labs)==1 else '/'.join(labs), round(f, 2), src))

# optional price overlay
pink = {}
pp = os.path.join(ROOT, 'reconcile', 'pink_momentum.json')
if os.path.exists(pp):
    pink = json.load(open(pp))
    for lab, pf in pink.items():
        if lab in mom and mom[lab] != 1.0:
            mom[lab] = float(np.sqrt(mom[lab] * pf))          # blend trade & price momentum (geo-mean)
        elif lab in mom:
            mom[lab] = float(pf)                              # price-only where trade was thin
# conservative final clamp: priced materials may move more (price-corroborated); unpriced kept near
# persistence so a single noisy quarter (e.g. lithium x2.5) can't drive a large call.
for lab in list(mom):
    lo, hi = (0.5, 2.6) if lab in pink else (0.7, 1.5)
    mom[lab] = float(min(max(mom[lab], lo), hi))

# build flows_2026 = flows_2025 * momentum
F25 = json.load(open(os.path.join(ROOT, 'out', 'flows_2025.json'), encoding='utf8'))
materials = {}; used = set()
for lab, flows in F25['materials'].items():
    f = mom.get(lab, 1.0)
    nf = [{'from': x['from'], 'to': x['to'], 'value': int(round(x['value'] * f))} for x in flows]
    materials[lab] = nf
    for x in nf: used.add(x['from']); used.add(x['to'])
out = {'year': 2026, 'provisional': True, 'nowcast_kind': 'directional-q1',
       'source': 'DIRECTIONAL 2026 NOWCAST — 2025 reconciled structure scaled by reporter-matched Q1-2026 vs Q1-2025 export momentum' + (' + Pink Sheet prices' if pink else '') + '. Shares = 2025; levels indicative only.',
       'centroids': F25['centroids'], 'names': F25['names'], 'iso': F25['iso'], 'materials': materials}
json.dump(out, open(os.path.join(ROOT, 'out', 'flows_2026.json'), 'w', encoding='utf8'), separators=(',', ':'), ensure_ascii=False)
print('\nfinal 2026 momentum factors (Q1 trade + Pink Sheet price, clamped):')
for lab, f in sorted(mom.items(), key=lambda x: -x[1]):
    print(f'  {lab:22s} x{f:.2f}  [{"price+trade" if lab in pink else "trade/persistence"}]')
print(f'\nflows_2026.json written: {len(materials)} materials, {sum(len(v) for v in materials.values())} flows')
