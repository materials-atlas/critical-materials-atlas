#!/usr/bin/env python3
"""
Fetch World Bank Worldwide Governance Indicators (WGI) -> out/wgi.json (ISO2 -> mean governance score).

The EU/SCRREEN criticality method weights supply concentration by governance: a material concentrated in
low-governance jurisdictions is riskier than the same concentration in stable democracies. We take the mean
of the six WGI 'estimate' indicators (each ~[-2.5, 2.5]; higher = better governance) for the most recent
available year per country. Public data (World Bank, CC-BY-4.0).
"""
import json, os, urllib.request, ssl

ROOT = os.path.dirname(os.path.abspath(__file__))
ctx = ssl.create_default_context()
def get(url):
    with urllib.request.urlopen(url, timeout=45, context=ctx) as r:
        return json.load(r)

# ISO3 -> ISO2 from the World Bank country list
iso2 = {}
for c in (get('https://api.worldbank.org/v2/country?format=json&per_page=400')[1] or []):
    if c.get('id') and c.get('iso2Code'):
        iso2[c['id']] = c['iso2Code']

# WGI now lives under source 3 with GOV_WGI_ prefixes
INDS = ['GOV_WGI_VA.EST', 'GOV_WGI_PV.EST', 'GOV_WGI_GE.EST', 'GOV_WGI_RQ.EST', 'GOV_WGI_RL.EST', 'GOV_WGI_CC.EST']
latest = {}   # iso2 -> {ind: (year, value)} keep most recent non-null
for ind in INDS:
    d = get(f'https://api.worldbank.org/v2/country/all/indicator/{ind}?source=3&format=json&per_page=20000&date=2015:2024')
    for row in (d[1] or []):
        v, i3, yr = row.get('value'), row.get('countryiso3code'), row.get('date')
        if v is None or not i3:
            continue
        i2 = iso2.get(i3)
        if not i2:
            continue
        cur = latest.setdefault(i2, {}).get(ind)
        if cur is None or int(yr) > cur[0]:
            latest[i2][ind] = (int(yr), float(v))

wgi = {}
for i2, inds in latest.items():
    vals = [v for (_, v) in inds.values()]
    if len(vals) >= 4:                       # need most of the 6 for a stable mean
        wgi[i2] = round(sum(vals) / len(vals), 3)

json.dump({'source': 'World Bank Worldwide Governance Indicators (mean of 6 estimates, latest yr 2015-2024)',
           'wgi': wgi}, open(os.path.join(ROOT, 'out', 'wgi.json'), 'w', encoding='utf8'), indent=1)
print(f'wrote out/wgi.json — {len(wgi)} countries')
for k in ['NO', 'DE', 'US', 'CN', 'RU', 'CD', 'KZ']:
    print(f'  {k}: {wgi.get(k)}')
