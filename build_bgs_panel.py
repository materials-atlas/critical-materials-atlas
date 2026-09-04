#!/usr/bin/env python3
"""BGS World Mineral Statistics — FULL panel puller (all ~410k records: production + imports + exports,
every commodity, per country, per year, 1970-2024). One source for the atlas's critical materials AND the
consumption model's own drivers (cement, iron & steel, bauxite/alumina/aluminium...) AND a control group
of non-critical commodities (gypsum, salt, kaolin, gold...) for the residual test. Pages the whole
collection with no erml_group filter, groups by erml_group at WRITE time, retains EVERY field, computes
NOTHING at ingest. Output: raw/bgs/panel/<group>.json + _summary.json. Run: python build_bgs_panel.py
"""
import urllib.request, json, os, time
from collections import defaultdict
API="https://ogcapi.bgs.ac.uk/collections/world-mineral-statistics/items"
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'raw','bgs','panel')
os.makedirs(OUT, exist_ok=True)
def get(url, tries=6):
    for t in range(tries):
        try: return json.load(urllib.request.urlopen(url, timeout=180))
        except Exception:
            if t==tries-1: raise
            time.sleep(5*(t+1))
groups=defaultdict(list); off=0; PAGE=5000
while True:
    d=get(f"{API}?limit={PAGE}&offset={off}&f=json")
    fs=d.get('features',[])
    for f in fs: groups[f['properties'].get('erml_group') or '_ungrouped'].append(f['properties'])
    matched=d.get('numberMatched', 0)
    got=off+len(fs)
    if off % 50000 == 0: print(f"  ...{got}/{matched}")
    if len(fs)<PAGE or got>=matched: break
    off+=PAGE; time.sleep(2)
summary={}
for g,rows in groups.items():
    safe=''.join(c if c.isalnum() else '_' for c in g.lower())
    json.dump(rows, open(os.path.join(OUT, safe+'.json'),'w'), separators=(',',':'))
    summary[g]=len(rows)
json.dump(summary, open(os.path.join(OUT,'_summary.json'),'w'), indent=1)
print(f"DONE: {len(summary)} groups | {sum(summary.values())} records")
