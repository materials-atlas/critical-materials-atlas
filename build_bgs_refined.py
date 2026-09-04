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
STEPS = [2000, 2005, 2010, 2015, 2020, 2021, 2022, 2023, 2024]  # long-run + recent, keeps the slider readable

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
        return None, None
    ser, counts = {}, {}
    for y in STEPS:
        ys = str(y)
        if ys not in by_year:
            continue
        tot = sum(by_year[ys].values())
        if tot <= 0:
            continue
        rows = sorted(((c, round(100 * v / tot)) for c, v in by_year[ys].items()), key=lambda x: -x[1])
        rows = [{'c': c, 'v': p} for c, p in rows if p >= 1]
        if rows:
            ser[ys] = rows
            counts[ys] = len(by_year[ys])   # ALL positive reporters, before the >=1% display cut
    return (ser, counts) if len(ser) >= 3 else (None, None)

d = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf-8'))
refined_years = {}
report = []
for m in d['materials']:
    lab = m['label']
    if lab not in MAP:
        continue
    ser, counts = series_for(MAP[lab])
    if not ser:
        report.append(f"  {lab:11} — no usable series")
        continue
    refined_years[lab] = ser
    latest = max(ser)
    m['refined'] = ser[latest]                       # headline = latest BGS year
    # BGS is a compilation of national returns: these are shares of the countries that REPORT, not of
    # world output. For broad-coverage metals (copper, nickel) that is nearly the same thing; for thin
    # by-products it is not — germanium 2024 has THREE reporters (CN/US/RU), so "China 94%" is 94% of
    # reporters while USGS says most producers do not report and credible world figures span ~60-94%.
    # The reporter count travels with the source string so every renderer shows it.
    n_rep = counts[latest]
    m['refined_source'] = f'BGS World Mineral Statistics {latest}, share of {n_rep} reporting countries'
    m['refined_basis'] = 'reporters'
    top = ser[latest][0]
    report.append(f"  {lab:11} {sorted(ser)} · {latest} top {top['c']} {top['v']}%  n={n_rep}  (src '{MAP[lab]}')")

# --- estimate overrides & attributions. Rule: a label does not repair a number that answers a
# different question. BGS germanium 2024 covers THREE reporters (CN 200 t / US 7 t / RU 5 t), so the
# computed 94 is 200/212 — a share of reporters, not of world output. The headline therefore shows the
# documented central estimate (basis.json: credible range 60-94; IEA export-control table 94 vs IEA
# GCMO p.199 chart ~78; USGS: 'most producers do not publicly report'), and the reporter detail stays
# as the provenance line. Gallium's 98 is NOT BGS — it is the USGS world figure — and carries its
# attribution so it is not the only untagged number on the page.
for m in d['materials']:
    if m['label'] == 'germanium':
        m['refined'] = [{'c': 'CN', 'v': 85}]
        m['refined_source'] = ('central estimate ~85% (credible range 60-94: IEA export-control table 94, '
                               'IEA GCMO 2026 p.199 chart ~78; USGS publishes no share). Provenance: BGS 2024 '
                               'covers 3 reporters only - CN 200 t, US 7 t, RU 5 t')
        m['refined_basis'] = 'estimate'
        m['mined_source'] = ('estimate - no measured series exists: BGS carries no germanium mine series and '
                             'USGS publishes no country table (most producers do not report)')
    elif m['label'] == 'gallium':
        m['refined_source'] = 'USGS MCS - world estimate, refined gallium (~98%)'
        m['mined_source'] = 'USGS MCS 2025 - world primary low-purity gallium: China 839/848 t = 98.9% (2024)'
json.dump(d, open(os.path.join(ROOT, 'out', 'data.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
json.dump(refined_years, open(os.path.join(ROOT, 'out', 'refined_years.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print('\n'.join(report))
print(f"\nWROTE refined_years.json: {len(refined_years)} materials · updated data.json refined headlines")
