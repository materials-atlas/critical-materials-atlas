# -*- coding: utf-8 -*-
"""Phase-1 real pull: Eurostat Comext detailed trade (CN8, monthly, free, no key). Downloads the
latest monthly bulk file, filters to our critical-material 8-digit codes, and writes a Parquet the
static query page can read. The payoff vs BACI: (1) freshness — Comext is ~2 years ahead of BACI;
(2) granularity — CN8 SPLITS the HS-6 811292 gallium/germanium bundle the atlas is built around.
Outputs: pipeline/data/eurostat_cn8.parquet"""
import os, re, csv, json, urllib.request
import py7zr, duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'pipeline', 'data')
DIR_URL = "https://ec.europa.eu/eurostat/api/dissemination/files?dir=comext%2FCOMEXT_DATA%2FPRODUCTS"
FILE_URL = "https://ec.europa.eu/eurostat/api/dissemination/files?file=comext%2FCOMEXT_DATA%2FPRODUCTS%2F"

def fetch(url, timeout=180):
    req = urllib.request.Request(url, headers={'User-Agent': 'critical-materials-atlas/phase1'})
    return urllib.request.urlopen(req, timeout=timeout).read()   # urllib follows the 302 redirect

# --- 1. discover the latest monthly file ---
listing = fetch(DIR_URL).decode('utf8', 'replace')
months = sorted(set(re.findall(r'full_partxixu_v2_(\d{6})\.7z', listing)))
period = months[-1]
fn = f'full_partxixu_v2_{period}.7z'
z_path = os.path.join(DATA, f'comext_{period}.7z')
dat_path = os.path.join(DATA, 'comext_tmp', f'full_partxixu{period}.dat')
print(f'latest Comext month: {period}  ({fn})')

# --- 2. download + extract (reuse if already present) ---
if not os.path.exists(dat_path):
    if not os.path.exists(z_path):
        print('  downloading...')
        open(z_path, 'wb').write(fetch(FILE_URL + fn))
    with py7zr.SevenZipFile(z_path) as a:
        a.extractall(os.path.join(DATA, 'comext_tmp'))
print(f'  data file: {os.path.getsize(dat_path):,} bytes')

# --- 3. our critical-material 8-digit codes -> material (exact CN8 match splits the bundles) ---
codes = json.load(open(os.path.join(ROOT, 'pipeline', 'critical_codes.json')))['codes']
cn8_material = {c['code']: c['material'] for c in codes if len(c['code']) == 8}

# ISO2 -> country name (from BACI's country table)
iso2name = {}
for r in csv.DictReader(open(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'), encoding='utf8')):
    if r.get('country_iso2'):
        iso2name[r['country_iso2']] = r['country_name']
FLOW = {'1': 'import', '2': 'export'}

# --- 4. filter Comext to our CN8 codes ---
rows = []
with open(dat_path, encoding='utf8', errors='replace') as f:
    for row in csv.DictReader(f):
        nc = row['PRODUCT_NC']
        mat = cn8_material.get(nc)
        if not mat:
            continue
        rows.append((int(row['PERIOD']), row['REPORTER'], row['PARTNER'],
                     iso2name.get(row['PARTNER'], row['PARTNER']), nc, mat,
                     FLOW.get(row['FLOW'], row['FLOW']),
                     'intra-EU' if row['TRADE_TYPE'] == 'I' else 'extra-EU',
                     float(row['VALUE_EUR'] or 0), float(row['QUANTITY_KG'] or 0)))
print(f'  kept {len(rows):,} CN8 rows across {len(set(r[5] for r in rows))} materials')

# --- 5. write Parquet ---
con = duckdb.connect()
con.execute("""CREATE TABLE eu(period INTEGER, reporter VARCHAR, partner VARCHAR, partner_name VARCHAR,
  cn8 VARCHAR, material VARCHAR, flow VARCHAR, trade_type VARCHAR, value_eur DOUBLE, qty_kg DOUBLE)""")
con.executemany("INSERT INTO eu VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
pq = os.path.join(DATA, 'eurostat_cn8.parquet').replace('\\', '/')
con.execute(f"COPY (SELECT * FROM eu ORDER BY material, value_eur DESC) TO '{pq}' (FORMAT PARQUET, COMPRESSION ZSTD)")
print(f'wrote pipeline/data/eurostat_cn8.parquet  ({len(rows):,} rows, {os.path.getsize(pq)/1024:.0f} KB)')

# --- 6. the money shot: gallium vs germanium, now SEPARATE, on May-2026 data ---
print(f'\nHS-6 811292 bundle, SPLIT at CN8 (EU imports, {period}):')
for r in con.execute("""SELECT material, cn8, ROUND(SUM(value_eur)) eur, ROUND(SUM(qty_kg)) kg
  FROM eu WHERE cn8 IN ('81129289','81129295') AND flow='import' GROUP BY 1,2 ORDER BY 1""").fetchall():
    print(f'  {r[0]:<10} {r[1]}  EUR {r[2]:>12,.0f}  {r[3]:>8,.0f} kg')
