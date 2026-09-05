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
# documented central estimate (range 60-94; low end = USGS Minerals Yearbook 2023 table 1, printed;
# high end = the IEA export-control table), and the reporter detail stays as the provenance line.
# An earlier draft cited "IEA GCMO p.199 ~78" - that page is a scatter chart and 78 was an eyeball
# read, so it was replaced by a printed figure rather than dressed up as one. Gallium's 98 is NOT BGS — it is the USGS world figure — and carries its
# attribution so it is not the only untagged number on the page.
for m in d['materials']:
    if m['label'] == 'germanium':
        # DISPLAY is the interval, both ends dated. A bare 85 fails the standard the atlas argues
        # for in public exactly as a bare 94 does, only less visibly - neither is a measured
        # world share and no current world total exists.
        # SCALAR consumers (the supply-risk index needs one number) get 81: the midpoint of the two
        # dated anchors, which is reproducible from them. 85 was not.
        m['refined'] = [{'c': 'CN', 'v': 81}]
        m['refined_range'] = [68, 94]
        m['refined_point_note'] = ('81 = midpoint of the dated anchors (68 in 2020, 94 in 2024). '
                                   'Used only where a scalar is unavoidable; display the interval.')
        m['refined_source'] = (
            'Interval 68-94%, both ends dated; no current world total exists. '
            'LOW END 68% (2020), printed: USGS Minerals Yearbook 2023, '
            'germanium, table 1 - China 95,000 kg of 140,000 kg world refinery production (2020) = 68%; '
            'every figure in that table is flagged estimated and 2021-23 are NA, with the text saying '
            'reliable estimates could not be made and world output was put at 100,000-200,000 kg. '
            'HIGH END 94% (2024): the BGS three-reporter table - a share of reporters, not of world output. '
            'Deleting the "other" line (Belgium, Canada, Germany; US excluded) from the same 2020 row gives '
            '95,000/100,000 = 95% - which is structurally where a 94% comes from, because the BGS cells have '
            'no "other" row to carry. BGS 2024 covers 3 reporters only (CN 200 t, US 7 t, RU 5 t) and its '
            'China cell alone is 1.4x the whole USGS world estimate, so the numerators are not the same '
            'object. USGS publishes no China share of its own. '
            'Where a single number is unavoidable (the supply-risk index), 81 is used: the midpoint '
            'of the two dated anchors, reproducible from them.')
        m['refined_basis'] = 'estimate'
        m['mined_basis'] = 'estimate'
        m['mined_source'] = ('Estimate - no measured series exists: BGS carries no germanium mine series and '
                             'USGS publishes no country production table (most producers do not report).')
    elif m['label'] == 'gallium':
        m['refined_basis'] = 'estimate'
        m['mined_basis'] = 'estimate'
        m['refined_source'] = 'USGS MCS - world estimate, refined gallium (~98%). Estimated, not a measured census.'
        m['mined_source'] = ('USGS MCS 2025 - world primary low-purity gallium: China 839 t of 848 t = 98.9% '
                             '(2024). USGS states this as an estimate.')
# --- audit of the shares that had NO provenance at all. Three of them BGS can source directly,
# because the mineral is the traded product and coverage is good. Three it cannot, and saying so
# precisely beats "source not recorded": BGS publishes tantalum+niobium as one ore series and the
# PGMs as one combined series, so neither can yield a per-metal share. Those keep an explicit
# no-source flag naming the obstacle, which is what a reader needs in order to challenge it.
BGS_SOURCEABLE = {
    'fluorspar': (65, 'CN', 'fluorspar, all grades', 25, 2024),
    'feldspar':  (26, 'TR', 'feldspar', 52, 2024),
    'phosphate': (44, 'CN', 'phosphate rock', 36, 2024),
}
NO_BGS_EQUIVALENT = {
    'niobium':   'BGS publishes "tantalum and niobium minerals" as ONE combined ore series (Brazil '
                 '94% of it, 2024, 7 reporters) - it cannot yield a niobium-only refined share.',
    'platinum':  'BGS publishes the platinum-group metals as ONE combined mine series (South Africa '
                 '52%, 2024, 13 reporters) - it cannot yield a platinum-only share.',
    'palladium': 'BGS publishes the platinum-group metals as ONE combined mine series (South Africa '
                 '52%, 2024, 13 reporters) - it cannot yield a palladium-only share.',
}
for m in d['materials']:
    lab = m['label']
    if lab in BGS_SOURCEABLE and not m.get('refined_source'):
        v, iso, form, n, yr = BGS_SOURCEABLE[lab]
        m['refined'] = [{'c': iso, 'v': v}]
        m['refined_basis'] = 'reporters'
        m['refined_source'] = (f'BGS World Mineral Statistics {yr}, share of {n} reporting countries '
                               f'({form}). Replaces an unsourced figure carried since the seed data.')
    elif lab in NO_BGS_EQUIVALENT and not m.get('refined_source'):
        m['refined_basis'] = 'unsourced'
        m['refined_source'] = ('No source recorded for this figure, and it cannot be sourced from BGS: '
                               + NO_BGS_EQUIVALENT[lab]
                               + ' Treat the share as indicative until a per-metal source is cited.')

# --- fill any remaining unattributed refined/mined share from the source ledger. A share printed
# with no provenance reads as a measured fact; 12 materials were doing exactly that. The ledger
# already records where each came from, so wire it through rather than inventing an attribution -
# and mark the basis 'cited' so the renderer shows the tooltip without implying a reporter census.
try:
    _led = json.load(open(os.path.join(ROOT, 'source_ledger.json'), encoding='utf-8'))
except Exception:
    _led = {}
_filled = []
for m in d['materials']:
    ent = _led.get(m['label'])
    if not isinstance(ent, dict):
        continue
    src = ent.get('source')
    if not src:
        continue
    prov = src + (f" — {ent['claim']}" if ent.get('claim') else '')
    if ent.get('conf'):
        prov += f" [{ent['conf']}]"
    for layer in ('refined', 'mined'):
        if m.get(layer) and not m.get(f'{layer}_source'):
            m[f'{layer}_source'] = prov
            m[f'{layer}_basis'] = 'cited'
            _filled.append(f"{m['label']}/{layer}")
if _filled:
    print(f"  filled {len(_filled)} unattributed shares from the ledger: {', '.join(_filled[:8])}"
          + (' …' if len(_filled) > 8 else ''))

json.dump(d, open(os.path.join(ROOT, 'out', 'data.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
json.dump(refined_years, open(os.path.join(ROOT, 'out', 'refined_years.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print('\n'.join(report))
print(f"\nWROTE refined_years.json: {len(refined_years)} materials · updated data.json refined headlines")
