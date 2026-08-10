"""Refined-stage year series from the BGS World Mineral Statistics OGC API (free, 1970s–present, by
country). BGS reports the *refined/smelter* stage for the base + a few by-product metals, which is more
authoritative than the IEA projection / single-year EU-CRM figures we had. For each mapped material this
writes out/refined_years.json (per-year country shares, recent window) and updates out/data.json's refined
layer + refined_source to the latest BGS year. Fetch via curl (BGS blocks bare urllib). No API key.

Run:  python build_bgs_refined.py
"""
import os, sys, json, subprocess, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
API = "https://ogcapi.bgs.ac.uk/collections/world-mineral-statistics/items"
UA = "Mozilla/5.0"

# our material label -> BGS refined-stage commodity name (verified to exist and be the refined form)
MAP = {
    'copper':    'copper, refined',
    'cobalt':    'cobalt, refined',
    'nickel':    'nickel, smelter/refinery',
    'bauxite':   'alumina',
    'magnesium': 'magnesium metal, primary',
    'germanium': 'germanium metal',
    'arsenic':   'arsenic, white',
}
WINDOW = 6  # number of most-recent years to keep for the slider

def fetch(commodity):
    url = f"{API}?bgs_commodity_trans={urllib.parse.quote(commodity, safe='')}&limit=5000&f=json"
    out = subprocess.run(["curl", "-s", "-A", UA, url], capture_output=True, text=True, timeout=90).stdout
    return json.loads(out).get('features', [])

def series_for(commodity):
    feats = fetch(commodity)
    by_year = {}
    for f in feats:
        p = f['properties']
        iso = p.get('country_iso2_code')
        q = p.get('quantity')
        yr = (p.get('year') or '')[:4]
        if not iso or len(iso) != 2 or not yr or q in (None, ''):
            continue  # skip aggregates / continent / world rows (no clean iso2)
        try:
            q = float(q)
        except ValueError:
            continue
        if q <= 0:
            continue
        by_year.setdefault(yr, {})
        by_year[yr][iso] = by_year[yr].get(iso, 0.0) + q
    if not by_year:
        return None
    years = sorted(by_year)[-WINDOW:]
    ser = {}
    for y in years:
        tot = sum(by_year[y].values())
        if tot <= 0:
            continue
        rows = sorted(((c, round(100 * v / tot)) for c, v in by_year[y].items()), key=lambda x: -x[1])
        rows = [{'c': c, 'v': p} for c, p in rows if p >= 1]
        if rows:
            ser[y] = rows
    return ser if len(ser) >= 3 else None

d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
refined_years = {}
report = []
for m in d['materials']:
    lab = m['label']
    if lab not in MAP:
        continue
    ser = series_for(MAP[lab])
    if not ser:
        report.append(f"  {lab:11} — no usable series")
        continue
    refined_years[lab] = ser
    latest = max(ser)
    m['refined'] = ser[latest]                       # headline = latest BGS year
    m['refined_source'] = f'BGS World Mineral Statistics {latest}'
    top = ser[latest][0]
    report.append(f"  {lab:11} {sorted(ser)} · {latest} top {top['c']} {top['v']}%  (src '{MAP[lab]}')")

json.dump(d, open(os.path.join(ROOT, 'out', 'data.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
json.dump(refined_years, open(os.path.join(ROOT, 'out', 'refined_years.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print('\n'.join(report))
print(f"\nWROTE refined_years.json: {len(refined_years)} materials · updated data.json refined headlines")
