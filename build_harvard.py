"""Independent trade reconciliation cross-check via the Harvard Growth Lab Atlas API (public GraphQL).
The Atlas cleans UN Comtrade with the Bustos-Yildirim method -- a DIFFERENT reconciliation from CEPII's
BACI -- so agreement between the two is genuine belt-and-braces on the refining-concentration figures.
Queries exporter shares for our refined HS6 codes (mapped to Atlas HS12 product IDs) and writes
out/harvard.json {code: {top, top_share, hhi}}.  Run: python build_harvard.py [year]
"""
import os, sys, json, subprocess
import pandas as pd
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2022
API = "https://atlas.hks.harvard.edu/api/graphql"
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'), encoding='utf-8')
num2iso = dict(zip(cc.country_code, cc.country_iso2))       # Atlas countryId = M49 = BACI country_code

# refined HS6 -> Atlas HS12 product IDs (from productHs12(productLevel:6))
PID = {'740311': 8680, '750210': 8730, '282200': 6102, '810194': 8803, '810820': 8828,
       '811010': 8834, '281820': 6094, '810320': 8813, '720293': 8403, '850511': 9490}

def query(pid, year):
    q = ('{ countryProductYear(productClass:HS12, productLevel:6, productId:%d, yearMin:%d, yearMax:%d)'
         '{ countryId exportValue } }') % (pid, year, year)
    out = subprocess.run(['curl', '-s', '-X', 'POST', API, '-H', 'Content-Type: application/json',
                          '-A', 'Mozilla/5.0', '-d', json.dumps({'query': q})],
                         capture_output=True, text=True, timeout=60).stdout
    return json.loads(out).get('data', {}).get('countryProductYear') or []

res = {}
for code, pid in PID.items():
    rows = query(pid, YEAR)
    sh = {}
    for r in rows:
        cid = int(str(r['countryId']).replace('country-', ''))
        iso = num2iso.get(cid)
        v = r.get('exportValue') or 0
        if isinstance(iso, str) and v > 0:
            sh[iso] = sh.get(iso, 0.0) + v
    if not sh:
        continue
    tot = sum(sh.values()) + 1e-9
    s = sorted(((k, v / tot) for k, v in sh.items()), key=lambda kv: -kv[1])
    res[code] = {'top': s[0][0], 'top_share': round(s[0][1] * 100, 1), 'hhi': round(sum(v * v for _, v in s), 3)}
    print(f"  {code}  {res[code]['top']} {res[code]['top_share']:.0f}%  HHI {res[code]['hhi']:.2f}")

json.dump({'year': YEAR, 'source': 'Harvard Growth Lab Atlas (Bustos-Yildirim reconciliation), HS12',
           'materials': res},
          open(os.path.join(ROOT, 'out', 'harvard.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print(f'\nWROTE out/harvard.json ({len(res)} codes, {YEAR})')
