"""Rebuild out/flows_<year>.json for the measured years directly from the BACI HS17 zip, with the
country-mapping bug fixed: BACI code 490 -> TW (Taiwan) and 516 -> NA (Namibia) were being dropped
because their ISO-2 was blank/NA, silently excluding all their trade and distorting shares (China's
tungsten share inflated ~74% -> ~62%, cobalt ~19% -> ~12%, etc.). Reproduces the exact schema of the
old PowerShell builder (build_flows_years.ps1): top-6 suppliers/customers per country node, value in
USD, centroids [lat,lon]. Attaches qty (tonnes) for 2024 only, matching the prior state.

Run: python build_flows_fix.py
"""
import os, io, zipfile, json, re
import pandas as pd

ROOT = '.'
YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
TOP = 6
VER, HS = 'V202601', 'HS17'
BACI = os.path.join(ROOT, 'raw', 'baci', f'BACI_{HS}_{VER}.zip')

# code -> material label(s), from data.json titles; fold hafnium 811231 into the broad 811292 group
d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
def title_code(t):
    m = re.search(r'\(([^)]*)\)', t); return re.sub(r'\D', '', m.group(1))[:6] if m else ''
code2labels = {}
for m in d['materials']:
    c = title_code(m['title'])
    if len(c) >= 6:
        code2labels.setdefault(c, []).append(m['label'])
if '811231' in code2labels:
    code2labels.setdefault('811292', []).extend(code2labels.pop('811231'))
CODES = set(code2labels)

# numeric country code -> ISO-2  (keep_default_na=False so Namibia 'NA' is NOT read as NaN; CSV now has 490->TW)
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', f'country_codes_{VER}.csv'), keep_default_na=False)
num2iso = {int(r.country_code): r.country_iso2 for r in cc.itertuples() if r.country_iso2}
iso_map = {str(int(r.country_code)): r.country_iso2 for r in cc.itertuples() if r.country_iso2}
# CEPII leaves these ISO-2 blank ('Other Asia, nes'=Taiwan) or as 'NA' (Namibia, read as NaN); without
# this override their trade is silently dropped, inflating other countries' shares (China tungsten +12pp).
num2iso[490] = 'TW'; iso_map['490'] = 'TW'   # Taiwan
num2iso[516] = 'NA'; iso_map['516'] = 'NA'   # Namibia

# reuse centroids/names from the existing 2024 flows, add Taiwan + Namibia
ref = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf-8'))
CEN = dict(ref['centroids']); NMS = dict(ref['names'])
CEN.setdefault('TW', [23.6978, 120.9605]); NMS['TW'] = 'Taiwan'
CEN.setdefault('NA', [-22.9576, 18.4904]); NMS['NA'] = 'Namibia'

def build_year(year):
    member = f'BACI_{HS}_Y{year}_{VER}.csv'
    cols = ['i', 'j', 'k', 'v'] + (['q'] if year == 2024 else [])
    with zipfile.ZipFile(BACI) as z:
        raw = pd.read_csv(io.TextIOWrapper(z.open(member), encoding='utf-8'), dtype={'k': str}, usecols=cols)
    raw['k'] = raw.k.str.zfill(6)
    raw = raw[raw.k.isin(CODES)].copy()
    raw['fr'] = raw.i.map(num2iso); raw['to'] = raw.j.map(num2iso)
    raw = raw.dropna(subset=['fr', 'to'])
    raw = raw[raw.fr != raw.to]
    raw['value'] = pd.to_numeric(raw.v, errors='coerce').fillna(0.0) * 1000.0
    raw = raw[raw.value > 0]
    if year == 2024:
        raw['qty'] = pd.to_numeric(raw.q, errors='coerce').fillna(0.0)

    materials, used = {}, set()
    for code, labs in code2labels.items():
        sub = raw[raw.k == code]
        if not len(sub):
            for lab in labs: materials[lab] = []
            continue
        agg = sub.groupby(['fr', 'to'], as_index=False).agg(value=('value', 'sum'),
                                                            qty=('qty', 'sum') if year == 2024 else ('value', 'size'))
        # keep top-TOP edges per importer node AND per exporter node (union)
        keep = set()
        for _, g in agg.groupby('to'): keep |= set(g.nlargest(TOP, 'value').index)
        for _, g in agg.groupby('fr'): keep |= set(g.nlargest(TOP, 'value').index)
        kept = agg.loc[sorted(keep)].sort_values('value', ascending=False)
        for lab in labs:
            edges = []
            for r in kept.itertuples():
                e = {'from': r.fr, 'to': r.to, 'value': int(round(r.value))}
                if year == 2024: e['qty'] = int(round(r.qty))
                edges.append(e); used.add(r.fr); used.add(r.to)
            materials[lab] = edges
    out = {'year': year, 'source': f'UN Comtrade (primary) via CEPII BACI {HS} {VER}',
           'centroids': {k: CEN[k] for k in sorted(used) if k in CEN},
           'names': {k: NMS.get(k, k) for k in sorted(used)},
           'iso': iso_map, 'materials': materials}
    json.dump(out, open(os.path.join(ROOT, 'out', f'flows_{year}.json'), 'w', encoding='utf-8'),
              separators=(',', ':'), ensure_ascii=False)
    tw = 'TW' in used
    nfl = sum(len(v) for v in materials.values())
    print(f'flows_{year}.json: {len(materials)} materials, {nfl} flows, {len(used)} countries, Taiwan={tw}')

for y in YEARS:
    build_year(y)
print('DONE')
