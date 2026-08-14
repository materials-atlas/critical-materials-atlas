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

CW = json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf-8'))

# clean ISO2 -> display name: prefer current names, drop historical parentheticals, fix key ones
_PREF = {'DE': 'Germany', 'TR': 'Türkiye', 'RU': 'Russia', 'KR': 'South Korea', 'CD': 'DR Congo',
         'US': 'United States', 'GB': 'United Kingdom', 'CZ': 'Czechia', 'VN': 'Viet Nam', 'IR': 'Iran',
         'BO': 'Bolivia', 'BE': 'Belgium', 'LA': 'Laos', 'SY': 'Syria', 'TW': 'Taiwan'}
_iso_name = {}
for _num, _iso in num2iso.items():
    if not isinstance(_iso, str):
        continue
    _nm = str(num2name.get(_num, _iso))
    if _iso not in _iso_name or ('(' in _iso_name[_iso] and '(' not in _nm):
        _iso_name[_iso] = _nm
def disp(iso):
    return _PREF.get(iso, _iso_name.get(iso, iso))

# material -> refined-code BASKET (from canonical crosswalk) + physical shares + flags
MATS = {}
for m in d['materials']:
    ref = {x['c']: x['v'] for x in (m.get('refined') or [])}
    if not ref:
        continue
    cw = CW.get(m['label'], {})
    codes = cw.get('refined_hs') or [hs6(m['title'])]
    MATS[m['label']] = {'name': nicename(m), 'codes': codes, 'shares': ref, 'flags': cw.get('flags', [])}
REF_CODES = sorted({c for v in MATS.values() for c in v['codes']})

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

def fexp(c, k): return float(xpo.get((c, k), 0.0))
def fimp(c, k): return float(exp.get((c, k), 0.0))
countries = sorted({c for (c, _) in exp.index} | {c for (c, _) in xpo.index})

exposure = {}
for lab, info in MATS.items():
    codes, shares, flags = info['codes'], info['shares'], info['flags']
    shared = 'shared_refined' in flags                    # Ga/Ge 811292: trade fallbacks degenerate
    s = sorted(shares.items(), key=lambda kv: -kv[1])
    listed = sum(v for _, v in s)                          # coverage of the physical breakdown
    hhi = sum((v / 100.0) ** 2 for _, v in s)
    top_iso, top_share = (s[0][0], round(s[0][1], 1)) if s else (None, 0)
    capk = CAP_KEY.get(lab, lab)
    imp = {}
    if not shared:
        for c in countries:
            iso = num2iso.get(int(c))
            if not isinstance(iso, str):
                continue
            net = sum(fimp(c, k) - fexp(c, k) for k in codes)
            if net > 0 and cap_lat.get(capk, {}).get(iso, 0) < 0.03:
                imp[iso] = net
    reliant = sorted(imp.items(), key=lambda kv: -kv[1])[:6]
    exposure[lab] = {'name': info['name'], 'code': codes[0], 'codes': codes,
                     'hhi': round(hhi, 3), 'band': band(hhi), 'listed_pct': round(listed),
                     'top': top_iso, 'top_name': disp(top_iso), 'top_share': top_share, 'shared': shared,
                     'reliant': [{'iso': i, 'name': disp(i)} for i, _ in reliant]}

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
