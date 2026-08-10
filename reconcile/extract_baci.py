"""Build reconcile/baci_<year>.csv — the official-BACI ground truth that validate.py checks the
reconciliation against — directly from the public CEPII BACI HS17 zip. No API key, no Comtrade pull:
the only input is raw/baci/BACI_HS17_V202601.zip (a public download) plus the country-code map.

Output columns (i, j, cmd, value): exporter ISO3, importer ISO3, HS6 code, value in USD. Filtered to
the ~31 HS6 codes the atlas tracks (read from out/data.json), with the shared gallium/germanium/hafnium
code 811231 folded into 811292 exactly as validate.py folds the reconciled side.

Usage:  ATLAS_ROOT=/path/to/atlas python extract_baci.py 2024
"""
import os, sys, zipfile, io
import pandas as pd

ROOT = os.environ.get('ATLAS_ROOT', '.')
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
MEMBER   = f'BACI_HS17_Y{YEAR}_V202601.csv'

# HS6 codes the atlas tracks, from the material titles in data.json (same source validate.py uses)
import json
d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
def hs6(title):
    c = ''.join(ch for ch in title[title.find('(')+1:title.find(')')] if ch.isdigit()); return c[:6]
codes = {hs6(m['title']) for m in d['materials']}
codes.add('811231')  # keep the shared-code raw rows so we can fold them into 811292 below
print(f'tracking {len(codes)} HS6 codes', flush=True)

# BACI numeric country code -> ISO3
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
num2iso3 = dict(zip(cc.country_code, cc.country_iso3))

# stream the year member, keep only tracked codes
with zipfile.ZipFile(BACI_ZIP) as z:
    raw = pd.read_csv(io.TextIOWrapper(z.open(MEMBER), encoding='utf-8'),
                      dtype={'k': str}, usecols=['i', 'j', 'k', 'v'])
raw['k'] = raw.k.str.zfill(6)
raw = raw[raw.k.isin(codes)].copy()
print(f'raw rows in tracked codes: {len(raw)}', flush=True)

# map to ISO3, fold 811231 -> 811292, aggregate to one value per (i, j, cmd), thousands USD -> USD
raw['i'] = raw.i.map(num2iso3)
raw['j'] = raw.j.map(num2iso3)
raw = raw.dropna(subset=['i', 'j'])
raw['cmd'] = raw.k.replace('811231', '811292')
raw['value'] = pd.to_numeric(raw.v, errors='coerce') * 1000.0
out = (raw.groupby(['i', 'j', 'cmd'], as_index=False).value.sum())
out = out[out.value > 0]

dst = os.path.join(ROOT, 'reconcile', f'baci_{YEAR}.csv')
out[['i', 'j', 'cmd', 'value']].to_csv(dst, index=False)
print(f'wrote {dst}: {len(out)} flows, {out.cmd.nunique()} codes, total ${out.value.sum()/1e9:.1f}B', flush=True)
