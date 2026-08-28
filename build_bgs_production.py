"""Fetch latest-year mine-production shares per material from the BGS World Mineral Statistics OGC API
(free, national-returns compilation) and cache them to raw/bgs_production_shares.json. This is the THIRD
production source for the cross-check on production.html: USGS shares (data.json) x World Mining Data
tonnes (raw/wmd) x BGS shares (here). Caching keeps build_production.py deterministic and offline —
re-run this only to refresh from BGS. Fetch via curl (BGS blocks bare urllib).

Run:  python build_bgs_production.py
"""
import os, sys, json, subprocess, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.abspath(__file__))
API = "https://ogcapi.bgs.ac.uk/collections/world-mineral-statistics/items"
UA = "Mozilla/5.0"
PREFER = [2024, 2023, 2022, 2021, 2020]   # newest first; use the newest recent year with enough countries

# atlas label -> BGS bgs_commodity_trans candidates (first that returns a usable year wins)
MAP = {
    'antimony': ['antimony, mine'], 'arsenic': ['arsenic, white', 'arsenic'], 'baryte': ['barytes'],
    'bauxite': ['bauxite'], 'beryllium': ['beryl'], 'boron': ['boron minerals', 'borates', 'boron'],
    'cobalt': ['cobalt, mine'], 'copper': ['copper, mine'], 'fluorspar': ['fluorspar'],
    'gallium': ['gallium'], 'germanium': ['germanium'], 'graphite': ['graphite'],
    'lithium': ['lithium minerals'], 'magnesium': ['magnesite'], 'magnets': ['rare earth minerals'],
    'manganese': ['manganese ore'], 'nickel': ['nickel, mine'], 'niobium': ['niobium', 'columbium'],
    'phosphate': ['phosphate rock'], 'phosphorus': ['phosphate rock'],
    'platinum': ['platinum'], 'palladium': ['palladium'],
    'strontium': ['strontium minerals'], 'tantalum': ['tantalum'],
    'titanium': ['titanium minerals', 'ilmenite'], 'tungsten': ['tungsten, mine'], 'vanadium': ['vanadium'],
}

def fetch(commodity):
    url = f"{API}?bgs_commodity_trans={urllib.parse.quote(commodity, safe='')}&limit=6000&f=json"
    out = subprocess.run(["curl", "-s", "-A", UA, url], capture_output=True, text=True, timeout=120).stdout
    try:
        return json.loads(out).get('features', [])
    except Exception:
        return []

def by_year(feats):
    by = {}
    for f in feats:
        p = f['properties']
        iso, q, yr = p.get('country_iso2_code'), p.get('quantity'), (p.get('year') or '')[:4]
        if not iso or len(iso) != 2 or not yr.isdigit() or q in (None, ''):
            continue
        try:
            q = float(q)
        except (ValueError, TypeError):
            continue
        if q <= 0:
            continue
        by.setdefault(int(yr), {})
        by[int(yr)][iso] = by[int(yr)].get(iso, 0.0) + q
    return by

out = {'source': 'British Geological Survey, World Mineral Statistics (OGC API)',
       'source_url': API, 'retrieved': '2026-08-28',
       'note': 'Latest-year mine production by country; top-producer shares computed from BGS tonnages. '
               'BGS is a compilation of national statistical returns — independent of USGS as a COMPILATION, '
               'not as a measurement (both rest on the same national returns).',
       'materials': {}}
report = []
for lab, cands in MAP.items():
    got = None
    for c in cands:
        by = by_year(fetch(c))
        yr = next((y for y in PREFER if y in by and len(by[y]) >= 3 and sum(by[y].values()) > 0), None)
        if yr is None:  # fall back to the newest RECENT year (>=2020) with >=3 countries; a stale series
            # (e.g. BGS stopped reporting RE minerals after 2011) is not a fair check against 2024 and is dropped
            cand_years = sorted((y for y in by if y >= 2020 and len(by[y]) >= 3 and sum(by[y].values()) > 0), reverse=True)
            yr = cand_years[0] if cand_years else None
        if yr is None:
            continue
        tot = sum(by[yr].values())
        top = sorted(by[yr].items(), key=lambda kv: -kv[1])
        got = {'commodity': c, 'year': yr, 'world_tonnes': round(tot),
               'top5': [{'iso': i, 'tonnes': round(t), 'share': round(100 * t / tot, 1)} for i, t in top[:5]]}
        break
    if got:
        out['materials'][lab] = got
        report.append(f"  {lab:11} BGS '{got['commodity']}' {got['year']}: "
                      f"{got['top5'][0]['iso']} {got['top5'][0]['share']}% (world {got['world_tonnes']:,} t)")
    else:
        report.append(f"  {lab:11} — no usable BGS series")

json.dump(out, open(os.path.join(ROOT, 'raw', 'bgs_production_shares.json'), 'w', encoding='utf-8'),
          indent=1, ensure_ascii=False)
print('\n'.join(report))
print(f"\nwrote raw/bgs_production_shares.json — {len(out['materials'])} materials")
