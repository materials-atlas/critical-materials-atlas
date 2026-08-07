import os
"""Convert a reconciled HS6 flow file (recon_<year>.csv) into the atlas flows_<year>.json schema.
Levels are calibrated per-material to BACI's 2024 scale (recon runs ~1.6x high vs BACI, a consistent
multiple that doesn't affect shares); shares are unchanged. Keeps top-6 suppliers/customers per country.
Marks the output provisional. Usage: python build_recon_flows.py 2025
"""
import sys, json
import pandas as pd, numpy as np
ROOT = os.environ.get('ATLAS_ROOT', '.')
YEAR = int(sys.argv[1]); TOP = 6

d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
def hs6(m):
    t = m['title']; c = ''.join(ch for ch in t[t.find('(')+1:t.find(')')] if ch.isdigit()); return c[:6]
code2lab = {}
for m in d['materials']:
    c = hs6(m); c = '811292' if c == '811231' else c
    code2lab.setdefault(c, []).append(m['label'])

cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
i3_i2 = dict(zip(cc.country_iso3, cc.country_iso2))
ref = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf8'))   # reuse country reference
cen, nm, isomap = ref['centroids'], ref['names'], ref['iso']

# per-material level calibration: BACI_2024 / recon_2024 (so nowcast levels match the reconciled series)
def mat_totals(df):
    df = df.copy(); df['cmd'] = df.cmd.str.zfill(6).replace('811231', '811292')
    g = df.groupby('cmd').value.sum()
    return {lab: float(g.get(cmd, 0.0)) for cmd, labs in code2lab.items() for lab in labs}
b24 = mat_totals(pd.read_csv(os.path.join(ROOT, 'reconcile', 'baci_2024.csv'),  dtype={'cmd': str}))
r24 = mat_totals(pd.read_csv(os.path.join(ROOT, 'reconcile', 'recon_2024.csv'), dtype={'cmd': str}))
calib = {lab: (b24[lab] / r24[lab]) if r24.get(lab, 0) > 0 else 1.0 for lab in b24}

r = pd.read_csv(os.path.join(ROOT, 'reconcile', f'recon_{YEAR}.csv'), dtype={'cmd': str})
r['cmd'] = r.cmd.str.zfill(6).replace('811231', '811292')
r['i2'] = r.i.map(i3_i2); r['j2'] = r.j.map(i3_i2); r = r.dropna(subset=['i2', 'j2'])

materials = {}; used = set()
for cmd, labs in code2lab.items():
    agg = r[r.cmd == cmd].groupby(['i2', 'j2'], as_index=False).value.sum()
    if not len(agg):
        for lab in labs: materials[lab] = []
        continue
    for lab in labs:
        a = agg.copy(); a['value'] = a.value * calib.get(lab, 1.0)
        keep = set()
        for _, grp in a.groupby('j2'): keep |= set(zip(grp.nlargest(TOP, 'value').i2, grp.nlargest(TOP, 'value').j2))
        for _, grp in a.groupby('i2'): keep |= set(zip(grp.nlargest(TOP, 'value').i2, grp.nlargest(TOP, 'value').j2))
        amap = {(t.i2, t.j2): t.value for t in a.itertuples()}
        flows = sorted(({'from': i, 'to': j, 'value': int(round(amap[(i, j)]))} for (i, j) in keep if amap.get((i, j), 0) > 0),
                       key=lambda x: -x['value'])
        materials[lab] = flows
        for fl in flows: used.add(fl['from']); used.add(fl['to'])

out = {'year': YEAR, 'provisional': True,
       'source': 'UN Comtrade (raw) self-reconciled — BACI-validated method, levels calibrated to BACI 2024 — PROVISIONAL NOWCAST (partial reporting)',
       'centroids': {k: cen[k] for k in cen if k in used},
       'names': {k: nm[k] for k in nm if k in used},
       'iso': isomap, 'materials': materials}
json.dump(out, open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), 'w', encoding='utf8'), separators=(',', ':'), ensure_ascii=False)
print(f'flows_{YEAR}.json: {len(materials)} materials, {sum(len(v) for v in materials.values())} flows, {len(used)} countries (PROVISIONAL)')
