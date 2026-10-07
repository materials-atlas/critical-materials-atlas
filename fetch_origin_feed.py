#!/usr/bin/env python3
"""
Fetch China's own annual import declarations for the origin-feed codes (UN Comtrade, reporter 156,
2017-2024) into raw/comtrade/china_feed_imports.json. Network and API quota: run by hand, never by
runner.py. build_origin_feed.py reads the cache and does no network work.

Why China's own declarations and not BACI: checked 7 Oct 2026 against BACI V202601, 2024. Eight of
twelve rows agree within about 2%, but BACI's reconciliation drops most of Mozambique's titanium
minerals (BACI 3.5 Mt vs China 5.1 Mt) and all of Australia's zircon from China's top suppliers
(BACI 1.05 Mt vs China 1.75 Mt), and puts natural graphite 16% above China's figure. The table
answers "where does China's imported feed come from", which is China's own record.
"""
import json, os, time, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'raw', 'comtrade', 'china_feed_imports.json')
KEY = next(l.strip() for l in open(os.path.join(ROOT, 'pipeline', '.comtrade_key')) if l.strip())
CODES = ['284610', '284690', '280530', '250410', '250490', '261100', '261710', '252921', '252922',
         '261400', '260600', '260200', '260300', '251110', '251010', '251020', '261510', '252910']
YEARS = list(range(2017, 2025))

rows = []
for i in range(0, len(CODES), 6):
    url = ('https://comtradeapi.un.org/data/v1/get/C/A/HS?reporterCode=156&flowCode=M'
           f'&period={",".join(map(str, YEARS))}&cmdCode={",".join(CODES[i:i + 6])}')
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'Ocp-Apim-Subscription-Key': KEY}), timeout=180))
    got = [o for o in r['data'] if o.get('partner2Code', 0) == 0 and o.get('motCode', 0) == 0
           and o.get('customsCode', 'C00') == 'C00' and o.get('partnerCode') != 0]
    rows += [{k: o.get(k) for k in ('period', 'cmdCode', 'partnerCode', 'partnerISO', 'netWgt', 'isNetWgtEstimated', 'primaryValue')} for o in got]
    time.sleep(2)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({'source': 'UN Comtrade annual, reporter China (156), imports, partner rows (world row excluded)',
           'fetched': time.strftime('%Y-%m-%d'), 'codes': CODES, 'years': YEARS, 'rows': rows},
          open(OUT, 'w', encoding='utf8'), ensure_ascii=False)
print(f'wrote {OUT}: {len(rows)} rows; periods {sorted({r["period"] for r in rows})}')
