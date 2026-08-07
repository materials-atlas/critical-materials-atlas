# -*- coding: utf-8 -*-
"""Phase-1 PoC step 1: freeze the critical-material code list and convert real bilateral trade
(BACI HS17, latest year) into a compact Parquet file that a static browser page can query with
DuckDB-WASM. Proves the architecture: ad-hoc SQL over trade data, no backend, guardrail intact.
Outputs: pipeline/critical_codes.json  +  pipeline/data/trade.parquet"""
import os, re, csv, io, zipfile, json, collections
import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'raw')
OUT = os.path.join(ROOT, 'pipeline')
os.makedirs(os.path.join(OUT, 'data'), exist_ok=True)

# --- 1. freeze the code list from the atlas's own raw/<material>_<code>_value.csv files ---
# NOTE: several materials share an HS-6 (e.g. gallium + germanium under 811292). BACI is HS-6, so
# that bundle can't be split here — the label is the honest union. Splitting it is exactly what the
# 8-digit national-line codes (col 'code') buy you, and the whole point of the Phase-1 pull.
hs6_materials = collections.defaultdict(list)   # hs6 -> [materials sharing it]
codes = []
for f in sorted(os.listdir(RAW)):
    m = re.match(r'(.+)_(\d{6,10})_value\.csv$', f)
    if not m:
        continue
    material, code = m.group(1), m.group(2)
    hs6 = code[:6]
    hs6_materials[hs6].append(material)
    codes.append({'material': material, 'code': code, 'hs6': hs6})
hs6_label = {h: '+'.join(sorted(set(ms))) for h, ms in hs6_materials.items()}
bundles = {h: sorted(set(ms)) for h, ms in hs6_materials.items() if len(set(ms)) > 1}
json.dump({'source': 'raw/<material>_<code>_value.csv filenames', 'n_codes': len(codes),
           'n_hs6': len(hs6_label), 'codes': codes, 'hs6_bundles_needing_8digit': bundles},
          open(os.path.join(OUT, 'critical_codes.json'), 'w', encoding='utf8'), indent=2)
CRIT = set(hs6_label)
print(f'froze {len(codes)} codes across {len(CRIT)} HS-6 -> pipeline/critical_codes.json')
if bundles:
    print(f'  {len(bundles)} HS-6 bundle(s) that HS-6 can\'t split (need 8-digit): {bundles}')

# --- 2. country numeric -> iso3 / name ---
num2iso, num2name = {}, {}
for r in csv.DictReader(open(os.path.join(RAW, 'baci', 'country_codes_V202601.csv'), encoding='utf8')):
    num2iso[r['country_code']] = r['country_iso3']
    num2name[r['country_code']] = r['country_name']

# --- 3. stream the latest BACI HS17 year, keep only critical-material rows ---
zpath = os.path.join(RAW, 'baci', 'BACI_HS17_V202601.zip')
z = zipfile.ZipFile(zpath)
yearfiles = [(int(re.search(r'_Y(\d{4})_', n).group(1)), n) for n in z.namelist() if re.search(r'_Y\d{4}_', n)]
year, member = max(yearfiles)
print(f'reading {member} (latest year {year}) and filtering to critical codes...')

rows, kept = [], 0
with z.open(member) as fh:
    r = csv.reader(io.TextIOWrapper(fh, 'utf8'))
    next(r)  # header: t,i,j,k,v,q
    for t, i, j, k, v, q in r:
        if k in CRIT:
            try:
                val = float(v)
            except ValueError:
                val = None
            try:
                qty = float(q)
            except ValueError:
                qty = None
            rows.append((int(t), num2iso.get(i, i), num2name.get(i, i), num2iso.get(j, j),
                         num2name.get(j, j), k, hs6_label[k], val, qty))
            kept += 1
print(f'kept {kept:,} bilateral flows across {len(CRIT)} codes')

# --- 4. write Parquet via DuckDB (same engine the browser uses) ---
con = duckdb.connect()
con.execute("""CREATE TABLE trade(
  year INTEGER, exporter VARCHAR, exporter_name VARCHAR, importer VARCHAR, importer_name VARCHAR,
  hs6 VARCHAR, material VARCHAR, value_kusd DOUBLE, qty_t DOUBLE)""")
con.executemany("INSERT INTO trade VALUES (?,?,?,?,?,?,?,?,?)", rows)
pq = os.path.join(OUT, 'data', 'trade.parquet').replace('\\', '/')
con.execute(f"COPY (SELECT * FROM trade ORDER BY material, value_kusd DESC) TO '{pq}' (FORMAT PARQUET, COMPRESSION ZSTD)")
size = os.path.getsize(pq)
print(f'wrote pipeline/data/trade.parquet  ({kept:,} rows, {size/1024:.0f} KB)')
# quick sanity: top gallium exporters
print('\nsanity — top gallium exporters by value:')
for row in con.execute("""SELECT exporter_name, ROUND(SUM(value_kusd)/1000,1) AS m_usd
  FROM trade WHERE material='gallium' GROUP BY 1 ORDER BY 2 DESC LIMIT 5""").fetchall():
    print(f'  {row[0]:<20} {row[1]:>8} M$')
