"""Pull raw UN Comtrade bilateral trade (both flows) for our HS6 codes, for the given year(s).
One API call per (code, flow) returns the full reporter x partner matrix. Output: raw CSV per year.
Key is read from the COMTRADE_KEY env var (never hardcode/commit it).
Usage:  COMTRADE_KEY=xxx python pull_comtrade.py 2024 2025
"""
import os, sys, time, json, csv, requests

KEY  = os.environ.get('COMTRADE_KEY', '')
ROOT = os.environ.get('ATLAS_ROOT', '.')
YEARS = [int(y) for y in (sys.argv[1:] or ['2024'])]
if not KEY:
    sys.exit('set COMTRADE_KEY')

d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
def hs6(m):
    t = m['title']
    if '(' in t and ')' in t:
        c = ''.join(ch for ch in t[t.find('(')+1:t.find(')')] if ch.isdigit())
        return c[:6] if len(c) >= 6 else None
    return None
codes = sorted({hs6(m) for m in d['materials'] if hs6(m)})
print('codes', len(codes), codes, flush=True)

BASE = 'https://comtradeapi.un.org/data/v1/get/C/A/HS'
H = {'Ocp-Apim-Subscription-Key': KEY}
def pull(year, code, flow):
    for attempt in range(6):
        try:
            r = requests.get(BASE, headers=H, params={'period': year, 'cmdCode': code, 'flowCode': flow}, timeout=120)
            if r.status_code == 200:
                return r.json().get('data', []) or []
            print(f'  http {r.status_code} retry', flush=True)
        except Exception as e:
            print(f'  err {str(e)[:60]} retry', flush=True)
        time.sleep(4 + attempt*4)
    return None

for year in YEARS:
    path = os.path.join(ROOT, 'raw', 'comtrade', f'comtrade_{year}.csv')
    tot = 0; fails = []
    with open(path, 'w', newline='', encoding='utf8') as f:
        w = csv.writer(f); w.writerow(['year','reporter','partner','cmd','flow','value','netwgt','qty','qtyunit'])
        for code in codes:
            for flow in ['M', 'X']:
                rows = pull(year, code, flow)
                if rows is None:
                    print('FAIL', year, code, flow, flush=True); fails.append((code, flow)); continue
                for r in rows:
                    w.writerow([year, r['reporterCode'], r['partnerCode'], r['cmdCode'], r['flowCode'],
                                r.get('primaryValue'), r.get('netWgt'), r.get('qty'), r.get('qtyUnitCode')])
                tot += len(rows); print(year, code, flow, len(rows), 'tot', tot, flush=True)
                time.sleep(1.3)
    print('SAVED', path, 'rows', tot, 'fails', fails, flush=True)
