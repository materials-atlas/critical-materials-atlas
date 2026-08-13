"""Refining-chokepoint & exposure index -- across ALL critical materials with a refined breakdown.

For each material:
  CHOKEPOINT = how concentrated the REFINING/processing stage is. HHI over refined-production shares
    (BGS/USGS physical, from data.json; for the NdFeB magnet stage, over 850511 export shares since no
    physical series), plus the largest holder and its share. HHI in [0,1]: >=.5 extreme, >=.25 high.
  RELIANT IMPORTERS = the exposed consumers: biggest NET importers of the refined HS6 that have ~no
    domestic refining capability (capability known only for the 7 clean ore->refined chains; else 0).

Coverage: chokepoint needs only refined shares, so it spans all 29 materials that have them (the deep
feedstock/mine->refine analysis needs a clean ore->refined HS6 PAIR, which only 7 materials have).
Writes out/exposure.json (per-material, for the refiners.html cards + the all-materials ranking).
Run:  python build_exposure.py [year]
"""
import os, sys, io, zipfile, json
import pandas as pd
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
MAGNET_DOWN = '850511'
EPS = 1e-9

cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
num2iso = dict(zip(cc.country_code, cc.country_iso2)); num2name = dict(zip(cc.country_code, cc.country_name))
iso2num = {v: k for k, v in num2iso.items()}
d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))

def hs6(t):
    c = ''.join(ch for ch in t[t.find('(') + 1:t.find(')')] if ch.isdigit()); return c[:6]
def nicename(m):
    t = m['title']; return t[:t.find('(')].strip() if '(' in t else t

# material -> (display name, refined HS6, refined shares dict). 'magnets' -> 850511 (its traded form).
MATS = {}
for m in d['materials']:
    ref = {x['c']: x['v'] for x in (m.get('refined') or [])}
    if not ref:
        continue
    MATS[m['label']] = {'name': nicename(m), 'code': hs6(m['title']), 'shares': ref}
REF_CODES = sorted({v['code'] for v in MATS.values()})

cap = json.load(open(os.path.join(ROOT, 'out', 'capability.json'), encoding='utf-8'))
cap_lat = {stage: {r['iso']: r['cap'] for r in rows} for stage, rows in cap.items()}
CAP_KEY = {'magnets': 'magnet (NdFeB)'}   # capability-map key for the magnet material

with zipfile.ZipFile(BACI_ZIP) as z:
    raw = pd.read_csv(io.TextIOWrapper(z.open(f'BACI_HS17_Y{YEAR}_V202601.csv'), encoding='utf-8'),
                      dtype={'k': str}, usecols=['i', 'j', 'k', 'v'])
raw = raw[raw.k.isin(REF_CODES)].copy(); raw['v'] = pd.to_numeric(raw['v'], errors='coerce').fillna(0.0)
exp = raw.groupby(['j', 'k']).v.sum()   # importer j
xpo = raw.groupby(['i', 'k']).v.sum()   # exporter i

def band(h):
    return 'extreme' if h >= 0.5 else 'high' if h >= 0.25 else 'moderate' if h >= 0.15 else 'diffuse'

exposure = {}
for lab, info in MATS.items():
    code, shares = info['code'], info['shares']
    s = sorted(shares.items(), key=lambda kv: -kv[1])
    hhi = sum((v / 100.0) ** 2 for _, v in s)
    top_iso, top_share = (s[0][0], round(s[0][1], 1)) if s else (None, 0)
    capk = CAP_KEY.get(lab, lab)
    imp = {}
    for (c, k) in exp.index:
        if k != code:
            continue
        iso = num2iso.get(int(c))
        if not isinstance(iso, str):
            continue
        net = float(exp.get((c, code), 0.0)) - float(xpo.get((c, code), 0.0))
        if net > 0 and cap_lat.get(capk, {}).get(iso, 0) < 0.03:
            imp[iso] = net
    reliant = sorted(imp.items(), key=lambda kv: -kv[1])[:6]
    exposure[lab] = {'name': info['name'], 'code': code, 'hhi': round(hhi, 3), 'band': band(hhi),
                     'top': top_iso, 'top_name': num2name.get(iso2num.get(top_iso, -1), top_iso),
                     'top_share': top_share,
                     'reliant': [{'iso': i, 'name': num2name.get(iso2num.get(i, -1), i)} for i, _ in reliant]}

if 'magnets' in exposure:                       # alias so the magnet card (keyed 'magnet (NdFeB)') resolves
    exposure['magnet (NdFeB)'] = exposure['magnets']
ranking = sorted([(l, e) for l, e in exposure.items() if l != 'magnet (NdFeB)'], key=lambda kv: -kv[1]['hhi'])
print(f'refining chokepoint {YEAR} -- all {len(exposure)} materials with a refined breakdown:')
for lab, e in ranking:
    print(f"  {e['name'][:22]:22} HHI {e['hhi']:.2f} [{e['band']:8}] top {str(e['top']):3} {e['top_share']:4.0f}%"
          f"  reliant: {', '.join(r['iso'] for r in e['reliant'][:4])}")
n_extreme = sum(1 for _, e in ranking if e['band'] == 'extreme')
cn = sum(1 for _, e in ranking if e['top'] == 'CN')
print(f"\n{n_extreme}/{len(ranking)} materials are EXTREME chokepoints; China is the top refiner of {cn}.")
json.dump({'year': YEAR, 'materials': exposure,
           'ranking': [{'label': lab, **e} for lab, e in ranking]},
          open(os.path.join(ROOT, 'out', 'exposure.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('WROTE out/exposure.json')
