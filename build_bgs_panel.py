#!/usr/bin/env python3
"""BGS World Mineral Statistics — full PANEL puller (production + imports + exports, per country, per year,
1970-2024), the source the per-metal apparent-consumption builds should have used all along. Pulls by
erml_group (which returns every form and all three statistic types together), pages FULLY (the existing
BGS builders' limit=6000 truncates: copper alone has ~13,800 records), RETAINS EVERY FIELD, and computes
NOTHING at pull time (transformation-at-ingest is exactly why the atlas kept only top-5-one-year before).
Output: raw/bgs/panel/<group>.json. Run: python build_bgs_panel.py
"""
import urllib.request, urllib.parse, json, os, time
API = "https://ogcapi.bgs.ac.uk/collections/world-mineral-statistics/items"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw', 'bgs', 'panel')
os.makedirs(OUT, exist_ok=True)
# erml_group candidates present in BGS (verified: Copper/Gallium/Germanium/'Platinum group metals'; others best-guess)
GROUPS = ['Copper','Lead','Zinc','Tin','Nickel','Cobalt','Aluminium','Bauxite','Manganese','Tungsten',
          'Molybdenum','Vanadium','Antimony','Arsenic','Bismuth','Beryllium','Boron','Barytes','Baryte',
          'Feldspar','Fluorspar','Gallium','Germanium','Graphite','Lithium','Magnesium','Magnesite',
          'Platinum group metals','Rare earths','Strontium','Titanium','Phosphate rock','Silver','Chromium']

def get(url, tries=5):
    for t in range(tries):
        try:
            return json.load(urllib.request.urlopen(url, timeout=120))
        except Exception as e:
            if t == tries-1: raise
            time.sleep(4*(t+1))

def pull(group):
    props=[]; off=0
    while True:
        url=f"{API}?erml_group={urllib.parse.quote(group)}&limit=5000&offset={off}&f=json"
        d=get(url); fs=d.get('features',[])
        props += [f['properties'] for f in fs]
        matched=d.get('numberMatched', len(props))
        if len(fs)<5000 or len(props)>=matched: break
        off += 5000; time.sleep(1.5)
    return props

summary={}
for g in GROUPS:
    try:
        p=pull(g)
    except Exception as e:
        print(f"  {g}: ERR {str(e)[:50]}"); continue
    if p:
        safe=g.lower().replace(' ','_')
        json.dump(p, open(os.path.join(OUT, safe+'.json'),'w'), separators=(',',':'))
        st={}
        for r in p: st[r.get('bgs_statistic_type_trans')]=st.get(r.get('bgs_statistic_type_trans'),0)+1
        summary[g]=len(p)
        print(f"  {g}: {len(p)} records  {st}")
    else:
        print(f"  {g}: 0 (name mismatch or absent)")
    time.sleep(2)
json.dump(summary, open(os.path.join(OUT,'_summary.json'),'w'), indent=1)
print("total groups with data:", len(summary), "| total records:", sum(summary.values()))
