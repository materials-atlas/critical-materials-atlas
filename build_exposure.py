"""Refining-chokepoint & exposure index -- the headline metric the capability map was built for.

For each material:
  CHOKEPOINT = how concentrated the REFINING stage is. HHI over refined-production shares (BGS/USGS
    physical, from data.json; for the magnet stage, over 850511 export shares since no physical series),
    plus the single largest holder and its share. HHI in [0,1]: >0.25 concentrated, >0.5 extreme.
  RELIANT IMPORTERS = the exposed consumers: biggest NET importers of the refined form (ref_imp-ref_exp)
    that have ~no domestic refining capability. Exposure rises with own reliance x global chokepoint.

Writes out/exposure.json (consumed by build_refiners.py to badge each material card).
Run:  python build_exposure.py [year]
"""
import os, sys, io, zipfile, json
import pandas as pd
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
CROSSWALK = {'copper': ('260300', '740311'), 'nickel': ('260400', '750210'), 'cobalt': ('260500', '282200'),
             'tungsten': ('261100', '810194'), 'titanium': ('261400', '810820'), 'antimony': ('261710', '811010'),
             'bauxite': ('260600', '281820')}
MAGNET_DOWN = '850511'
REF_CODES = [r for _, r in CROSSWALK.values()] + [MAGNET_DOWN]
EPS = 1e-9

cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
num2iso = dict(zip(cc.country_code, cc.country_iso2)); num2name = dict(zip(cc.country_code, cc.country_name))
d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
cur_ref = {m['label']: {x['c']: x['v'] for x in (m.get('refined') or [])} for m in d['materials']}
cap = json.load(open(os.path.join(ROOT, 'out', 'capability.json'), encoding='utf-8'))
cap_lat = {stage: {r['iso']: r['cap'] for r in rows} for stage, rows in cap.items()}

with zipfile.ZipFile(BACI_ZIP) as z:
    raw = pd.read_csv(io.TextIOWrapper(z.open(f'BACI_HS17_Y{YEAR}_V202601.csv'), encoding='utf-8'),
                      dtype={'k': str}, usecols=['i', 'j', 'k', 'v'])
raw = raw[raw.k.isin(REF_CODES)].copy(); raw['v'] = pd.to_numeric(raw['v'], errors='coerce').fillna(0.0)
exp = raw.groupby(['j', 'k']).v.sum()   # importer j (net-import side)
xpo = raw.groupby(['i', 'k']).v.sum()   # exporter i

def band(hhi):
    return 'extreme' if hhi >= 0.5 else 'high' if hhi >= 0.25 else 'moderate' if hhi >= 0.15 else 'diffuse'

exposure = {}
for lab, (ore, ref) in list(CROSSWALK.items()) + [('magnet (NdFeB)', (None, MAGNET_DOWN))]:
    # concentration of the refining stage
    if lab in cur_ref and cur_ref[lab]:
        shares = cur_ref[lab]; src = 'BGS/USGS refined output'
    else:  # magnet: use refined export shares
        tot = sum(float(xpo.get((c, ref), 0.0)) for c in {i for (i, _) in xpo.index}) + EPS
        shares = {num2iso.get(int(c)): float(xpo.get((c, ref), 0.0)) / tot * 100
                  for (c, k) in xpo.index if k == ref and isinstance(num2iso.get(int(c)), str)}
        src = 'HS 850511 export shares (trade-only)'
    s = sorted(shares.items(), key=lambda kv: -kv[1])
    hhi = sum((v / 100.0) ** 2 for _, v in s)   # true world-share HHI; unlisted residual ~atomistic
    top_iso, top_share = (s[0][0], round(s[0][1], 1)) if s else (None, 0)
    # reliant importers: biggest net importers of the refined form with ~no domestic capability
    imp = {}
    for (c, k) in exp.index:
        if k != ref:
            continue
        iso = num2iso.get(int(c))
        if not isinstance(iso, str):
            continue
        net = float(exp.get((c, ref), 0.0)) - float(xpo.get((c, ref), 0.0))
        if net > 0 and cap_lat.get(lab, {}).get(iso, 0) < 0.03:
            imp[iso] = net
    reliant = sorted(imp.items(), key=lambda kv: -kv[1])[:6]
    exposure[lab] = {'hhi': round(hhi, 3), 'band': band(hhi), 'top': top_iso,
                     'top_name': num2name.get({v: k for k, v in num2iso.items()}.get(top_iso, -1), top_iso),
                     'top_share': top_share, 'src': src,
                     'reliant': [{'iso': i, 'name': num2name.get({v: k for k, v in num2iso.items()}.get(i, -1), i)}
                                 for i, _ in reliant]}

print(f'refining chokepoint {YEAR}:')
for lab, e in exposure.items():
    print(f"  {lab:16} HHI {e['hhi']:.2f} [{e['band']:8}]  top {e['top']} {e['top_share']:.0f}%  "
          f"reliant: {', '.join(r['iso'] for r in e['reliant'][:5])}")
json.dump({'year': YEAR, 'materials': exposure},
          open(os.path.join(ROOT, 'out', 'exposure.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('WROTE out/exposure.json')
