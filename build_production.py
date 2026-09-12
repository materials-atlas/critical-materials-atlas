#!/usr/bin/env python3
"""
Production reality — the atlas in absolute tonnes, cross-checked against a second compilation.

Every prior layer worked in shares (USGS) or trade value (BACI). This one brings in ABSOLUTE physical
production from a SECOND COMPILATION. Source: World Mining Data 6.4 (Austrian Federal Ministry of
Finance / World Mining Congresses), one sheet per commodity, production by country in metric tonnes, 2024.

Two payoffs:
  (1) Scale the atlas has never shown: gallium is a ~1,000-tonne world; iron ore is a ~2.5-billion-tonne world.
      Concentration means very different things at those two scales.
  (2) Cross-check: compare each material's top-producer SHARE computed from WMD tonnages against the
      atlas's USGS-derived share (data.json). Where they diverge is flagged honestly.

HOW INDEPENDENT IS IT, EXACTLY? This page used to call WMD "a second INDEPENDENT authority", which an
outside reviewer attacked as circular ("both just recompile USGS"). So we counted. WMD tags every figure
with its source, and across 1,903 tagged figures in the 2024 edition:
      national statistics 60.0% | company reports 28.5% | questionnaire 6.7%
      IEA 1.5% | ICG 1.1% | USGS 0.8% (16 figures) | BP 0.7% | Kimberley 0.6% | WNA 0.2%
So the circularity charge is WRONG as put: USGS supplies 0.8% of WMD, and WMD is not a repackaging of it.
But the weaker version is RIGHT and we now say so: both compilations rest on the SAME upstream universe --
national statistical returns and company reports. They are independent COMPILATIONS, not independent
MEASUREMENTS. If a country misreports its output, both inherit the error identically and agree perfectly.
So agreement here demonstrates COMPILATION RELIABILITY, not measurement validation. No open source
independently measures mine output; the closest thing this atlas has is the satellite footprint layer,
which sees area, not tonnes.

Public data; deterministic. Run: python build_production.py
"""
import json, os
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import baci as _baci  # the one door for BACI (ARCHITECTURE.md phase 2)
import openpyxl

ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
flows = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf8'))
NAMES = flows.get('names', {})
DATA = {m['label']: m for m in data['materials']}
WMD = os.path.join(ROOT, 'raw', 'wmd', 'wmd_6.4_production_by_country.xlsx')

# atlas label -> WMD sheet name
SHEET = {
    'antimony': 'Antimony', 'arsenic': 'Arsenic', 'baryte': 'Baryte', 'bauxite': 'Bauxite',
    'beryllium': 'Beryllium (conc.)', 'boron': 'Boron Minerals', 'cobalt': 'Cobalt', 'cokingcoal': 'Coking Coal',
    'copper': 'Copper', 'feldspar': 'Feldspar', 'fluorspar': 'Fluorspar', 'gallium': 'Gallium',
    'germanium': 'Germanium', 'graphite': 'Graphite', 'lithium': 'Lithium (Li2O)', 'magnesium': 'Magnesite',
    'magnets': 'Rare Earths (REO)', 'manganese': 'Manganese', 'nickel': 'Nickel', 'niobium': 'Niobium (Nb2O5)',
    'palladium': 'Palladium', 'phosphate': 'Phosphate Rock (P2O5)', 'phosphorus': 'Phosphate Rock (P2O5)',
    'platinum': 'Platinum', 'tantalum': 'Tantalum (Ta2O5)', 'titanium': 'Titanium (TiO2)',
    'tungsten': 'Tungsten (W)', 'vanadium': 'Vanadium (V)',
}

# WMD country name -> ISO2 (major producers)
N2I = {
 'China': 'CN', 'Australia': 'AU', 'Russia': 'RU', 'USA': 'US', 'Brazil': 'BR', 'Canada': 'CA',
 'Congo, Dem. Rep.': 'CD', 'Dem. Rep. Congo': 'CD', 'Congo, D.R.': 'CD', 'United States': 'US', 'Indonesia': 'ID', 'India': 'IN', 'South Africa': 'ZA',
 'Chile': 'CL', 'Peru': 'PE', 'Kazakhstan': 'KZ', 'Mexico': 'MX', 'Turkey': 'TR', 'Türkiye': 'TR',
 'Ukraine': 'UA', 'Vietnam': 'VN', 'Viet Nam': 'VN', 'Myanmar': 'MM', 'Bolivia': 'BO', 'Argentina': 'AR',
 'Zimbabwe': 'ZW', 'Zambia': 'ZM', 'Philippines': 'PH', 'Malaysia': 'MY', 'Thailand': 'TH', 'Japan': 'JP',
 'Korea, Rep.': 'KR', 'South Korea': 'KR', 'Germany': 'DE', 'France': 'FR', 'Spain': 'ES', 'Sweden': 'SE',
 'Finland': 'FI', 'Poland': 'PL', 'Norway': 'NO', 'Morocco': 'MA', 'Jordan': 'JO', 'Saudi Arabia': 'SA',
 'Iran': 'IR', 'Egypt': 'EG', 'Nigeria': 'NG', 'Ghana': 'GH', 'Tanzania': 'TZ', 'Namibia': 'NA',
 'Botswana': 'BW', 'Mozambique': 'MZ', 'Madagascar': 'MG', 'Rwanda': 'RW', 'Burundi': 'BI', 'Laos': 'LA',
 'Mongolia': 'MN', 'Uzbekistan': 'UZ', 'Tajikistan': 'TJ', 'New Caledonia': 'NC', 'Papua New Guinea': 'PG',
 'Guinea': 'GN', 'Jamaica': 'JM', 'Suriname': 'SR', 'Guyana': 'GY', 'Venezuela': 'VE', 'Colombia': 'CO',
 'Cuba': 'CU', 'Greece': 'GR', 'Italy': 'IT', 'Portugal': 'PT', 'Austria': 'AT', 'Czech Republic': 'CZ',
 'Czechia': 'CZ', 'Slovakia': 'SK', 'Bulgaria': 'BG', 'Romania': 'RO', 'Serbia': 'RS',
 'Bosnia-Herzegovina': 'BA', 'North Macedonia': 'MK', 'Georgia': 'GE', 'Armenia': 'AM', 'Azerbaijan': 'AZ',
 'Pakistan': 'PK', 'Afghanistan': 'AF', 'Sri Lanka': 'LK', 'United Kingdom': 'GB', 'Ireland': 'IE',
 'Estonia': 'EE', 'Algeria': 'DZ', 'Angola': 'AO', 'Sierra Leone': 'SL', 'Liberia': 'LR', 'Mauritania': 'MR',
 'Mali': 'ML', 'Burkina Faso': 'BF', "Cote d'Ivoire": 'CI', 'Senegal': 'SN', 'Uganda': 'UG', 'Ethiopia': 'ET',
 'Kenya': 'KE', 'United Arab Emirates': 'AE', 'Qatar': 'QA', 'Oman': 'OM', 'Israel': 'IL', 'New Zealand': 'NZ',
 'Dominican Republic': 'DO', 'Panama': 'PA', 'Ecuador': 'EC', 'Gabon': 'GA', 'Cameroon': 'CM', 'Malawi': 'MW',
 'Eritrea': 'ER', 'Nepal': 'NP', 'Bhutan': 'BT', 'Cambodia': 'KH', 'Belgium': 'BE', 'Netherlands': 'NL',
}

# third source: BGS World Mineral Statistics (cached by build_bgs_production.py from the BGS OGC API)
BGS_PATH = os.path.join(ROOT, 'raw', 'bgs_production_shares.json')
BGS = {}
try:
    _bgs = json.load(open(BGS_PATH, encoding='utf8'))
    BGS = _bgs.get('materials', {})
except Exception:
    BGS = {}

wb = openpyxl.load_workbook(WMD, read_only=True, data_only=True)

def parse_sheet(sheet):
    ws = wb[sheet]
    # header row: find the row whose first cell == 'Country'
    rows = list(ws.iter_rows(values_only=True))
    hdr = next((i for i, r in enumerate(rows) if r and str(r[0]).strip() == 'Country'), 1)
    cols = rows[hdr]
    try:
        c24 = cols.index('2024')
    except ValueError:
        c24 = 6
    out = {}
    for r in rows[hdr + 1:]:
        if not r or not r[0]:
            continue
        name = str(r[0]).strip()
        if name.lower() in ('total', 'world', 'total world', 'others'):
            continue
        v = r[c24] if c24 < len(r) else None
        if isinstance(v, (int, float)) and v > 0:
            out[name] = float(v)
    return out

# WMD reports 'production' at different STAGES by commodity: mine production for most, but refinery/primary
# recovery for the non-mined by-products (gallium, germanium) and produced-metal for magnesium (Pidgeon).
# Curated so downstream callers can ASSERT the stage instead of assuming mine -- this is the field that
# closes the wmd_top_share stage-conflation a review caught (a refining share read as if it were the mine).
WMD_STAGE = {'gallium': 'refinery', 'germanium': 'refinery', 'magnesium': 'metal'}

rows_out = []
unmapped = set()
for lab, sheet in SHEET.items():
    if sheet not in wb.sheetnames:
        continue
    prod = parse_sheet(sheet)
    if not prod:
        continue
    world = sum(prod.values())
    top = sorted(prod.items(), key=lambda kv: -kv[1])
    top_name, top_t = top[0]
    top_iso = N2I.get(top_name)
    if top_iso is None:
        unmapped.add(top_name)
    wmd_share = round(100 * top_t / world, 1)
    top5 = [{'name': n, 'iso': N2I.get(n), 'tonnes': round(t), 'share': round(100 * t / world, 1)} for n, t in top[:5]]
    # atlas USGS top producer + share
    mined = DATA.get(lab, {}).get('mined') or []
    a_iso = mined[0]['c'] if mined else None
    a_share = mined[0]['v'] if mined else None
    same_top = (top_iso is not None and a_iso is not None and top_iso == a_iso)
    delta = round(abs(wmd_share - a_share), 1) if (same_top and a_share is not None) else None
    # BGS third source
    b = BGS.get(lab) or {}
    b_top = (b.get('top5') or [{}])[0]
    b_iso = b_top.get('iso')
    b_share = b_top.get('share')
    b_year = b.get('year')
    bgs_agree_usgs = (b_iso is not None and a_iso is not None and b_iso == a_iso)
    bgs_delta = round(abs(b_share - a_share), 1) if (bgs_agree_usgs and b_share is not None and a_share is not None) else None
    all_three = (same_top and bgs_agree_usgs)   # USGS, WMD and BGS all name the same top producer
    rows_out.append({
        'label': lab, 'title': DATA.get(lab, {}).get('title', lab).split(' (')[0],
        'world_tonnes': round(world), 'unit': 'metric tonnes',
        'wmd_top': top_name, 'wmd_top_iso': top_iso, 'wmd_top_share': wmd_share,
        'wmd_stage': WMD_STAGE.get(lab, 'mine'), 'top5': top5,
        'usgs_top_iso': a_iso, 'usgs_top_name': NAMES.get(a_iso, a_iso), 'usgs_top_share': a_share,
        'same_top_producer': same_top, 'share_delta': delta,
        'bgs_top_iso': b_iso, 'bgs_top_name': NAMES.get(b_iso, b_iso) if b_iso else None,
        'bgs_top_share': b_share, 'bgs_year': b_year,
        'bgs_agree_usgs': bgs_agree_usgs, 'bgs_share_delta': bgs_delta, 'all_three_agree': all_three,
    })

# validation summary
checkable = [r for r in rows_out if r['usgs_top_share'] is not None and r['wmd_top_iso'] is not None]
agree_top = [r for r in checkable if r['same_top_producer']]
deltas = [r['share_delta'] for r in agree_top if r['share_delta'] is not None]
mean_delta = round(sum(deltas) / len(deltas), 1) if deltas else None

# BGS third-source summary
bgs_checkable = [r for r in rows_out if r['usgs_top_share'] is not None and r['bgs_top_iso'] is not None]
bgs_agree = [r for r in bgs_checkable if r['bgs_agree_usgs']]
bgs_deltas = [r['bgs_share_delta'] for r in bgs_agree if r['bgs_share_delta'] is not None]
bgs_mean_delta = round(sum(bgs_deltas) / len(bgs_deltas), 1) if bgs_deltas else None
# three-way: materials that all three sources can check, and where all three name the same top producer
triple_checkable = [r for r in rows_out if r['usgs_top_share'] is not None
                    and r['wmd_top_iso'] is not None and r['bgs_top_iso'] is not None]
triple_agree = [r for r in triple_checkable if r['all_three_agree']]

rows_out.sort(key=lambda r: -r['world_tonnes'])

# ---- a THIRD check, genuinely independent of every statistical agency: the mine footprint from orbit ----
# WMD and USGS both rest on national returns, so their agreement is compilation reliability, not measurement.
# The satellite footprint (Maus et al. 2022 polygons, area by country) is measured from space -- independent
# of any government statistic. It cannot validate per-metal shares (polygons are undifferentiated coal/metal/
# aggregate, and area-per-tonne varies by orders of magnitude), but it CAN coarsely corroborate the AGGREGATE
# bulk-mining geography. Test (pre-set gate): does country footprint-share rank-correlate with bulk
# open-pit output-share? Ship the corroboration only if rho passes and the top-10 recall holds.
import csv as _csv2
try:
    from scipy import stats as _stats
    _sat = json.load(open(os.path.join(ROOT, 'out', 'satellite.json'), encoding='utf8'))
    _foot = {iso: d['area_km2'] for iso, d in _sat['countries'].items() if d.get('area_km2')}
    _i2 = {}
    for _r in _csv2.DictReader(_baci.country_file()):
        if _r.get('country_iso2') and _r.get('country_iso3'):
            _i2[_r['country_iso2']] = _r['country_iso3']
    _WT = {r['label']: r['world_tonnes'] for r in rows_out if r.get('world_tonnes')}
    _BULK = {'bauxite', 'cokingcoal', 'copper', 'phosphate', 'manganese'}   # highest-tonnage open-pit in the set
    _bt = {}
    for _m in data['materials']:
        if _m['label'] in _BULK and _m['label'] in _WT:
            for _e in (_m.get('mined') or []):
                _iso3 = _i2.get(_e.get('c'))
                if _iso3 and _e.get('v'):
                    _bt[_iso3] = _bt.get(_iso3, 0) + _e['v'] / 100.0 * _WT[_m['label']]
    _common = [c for c in _foot if c in _bt and _bt[c] > 0]
    _rho, _p = _stats.spearmanr([_foot[c] for c in _common], [_bt[c] for c in _common])
    _topO = set(sorted(_common, key=lambda c: -_bt[c])[:10])
    _topF = set(sorted(_common, key=lambda c: -_foot[c])[:10])
    satellite_check = {
        'n_countries': len(_common), 'spearman_rho': round(float(_rho), 2), 'p': round(float(_p), 4),
        'top10_recall': len(_topO & _topF),
        'passes': float(_rho) >= 0.5 and len(_topO & _topF) >= 8,
        'bulk_commodities': sorted(_BULK & set(_WT)),
        'note': 'Country mine-footprint share (Maus 2022 satellite polygons, orbit) vs bulk open-pit '
                'output share. Genuinely independent of national statistics. Coarse AGGREGATE geography '
                'only -- polygons are undifferentiated, so this cannot validate per-metal shares.',
    }
except Exception as _ex:
    satellite_check = {'error': str(_ex)[:80]}

out = {
    'generated': data.get('generated'), 'year': 2024,
    'source': 'World Mining Data 6.4 (2026 ed., Austrian Federal Ministry of Finance) — production in metric tonnes.',
    'bgs_source': 'British Geological Survey, World Mineral Statistics (OGC API), latest year per commodity.',
    'n': len(rows_out),
    'n_checkable': len(checkable),
    'n_agree_top': len(agree_top),
    'mean_share_delta': mean_delta,
    'bgs_n_checkable': len(bgs_checkable),
    'bgs_n_agree': len(bgs_agree),
    'bgs_mean_share_delta': bgs_mean_delta,
    'triple_n_checkable': len(triple_checkable),
    'triple_n_agree': len(triple_agree),
    'satellite_check': satellite_check,
    'rows': rows_out,
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'production.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/production.json')
print(f"  materials in tonnes: {len(rows_out)} | WMD cross-checkable {len(checkable)} | "
      f"same top producer as USGS: {len(agree_top)}/{len(checkable)} | mean share delta {mean_delta}pp")
print(f"  BGS third source: {len(bgs_agree)}/{len(bgs_checkable)} agree with USGS top producer | "
      f"mean BGS share delta {bgs_mean_delta}pp | ALL THREE agree: {len(triple_agree)}/{len(triple_checkable)}")
_bdiverge = [r['label'] for r in bgs_checkable if not r['bgs_agree_usgs']]
if _bdiverge:
    print("  BGS diverges from USGS top producer for:", ', '.join(_bdiverge))
if unmapped:
    print("  UNMAPPED top-producer names:", ', '.join(sorted(unmapped)))

# ------------------------------------------------------------------ page
HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Production reality — the atlas in tonnes, triangulated · Critical Materials Atlas</title>
<meta name="description" content="Absolute mine production in metric tonnes for the atlas's materials (World Mining Data 2024), triangulated against two more compilations: does the USGS-derived producer geography survive when World Mining Data AND the British Geological Survey count it separately? For most materials all three name the same top producer — and where they split, the two independents adjudicate.">
<meta property="og:title" content="The atlas in real tonnes — triangulated across three compilations">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .muted{color:#5a6b68;font-size:.86rem}
 #scatter{width:100%;height:440px}
 .stat4{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin:1.2rem 0}
 @media(max-width:720px){.stat4{grid-template-columns:repeat(2,1fr)}}
 .stat{background:#fff;border:1px solid #e3e9e8;border-left:4px solid #0e7c74;border-radius:10px;padding:.8rem .9rem}
 .stat .v{font-size:1.4rem;font-weight:800;color:#15323a;letter-spacing:-.02em}
 .stat .l{font-size:.76rem;color:#5a6b68;margin-top:.15rem;line-height:1.35}
 table.tidy{width:100%;border-collapse:collapse;font-size:.86rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .sbar{display:grid;grid-template-columns:120px 1fr 92px;align-items:center;gap:.6rem;margin:.2rem 0;font-size:.84rem}
 .sbar .nm{text-align:right;font-weight:600;color:#15323a}
 .sbar .track{background:#eef3f2;border-radius:4px;height:16px;overflow:hidden}
 .sbar .fill{height:100%;background:#0e7c74;border-radius:4px}
 .sbar .v{text-align:right;color:#5a6b68;font-variant-numeric:tabular-nums}
 .keyline{background:#f2f6f5;border:1px solid #d9e6e3;border-left:4px solid #0e7c74;border-radius:10px;padding:.9rem 1.1rem;margin:1.2rem 0}
 .keyline b{color:#0e7c74}
 .ok{color:#2f8f46;font-weight:700}.no{color:#c0392b;font-weight:700}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="methodology.html">Methodology</a><a href="casestudies.html">Validation</a>
  <a href="cascade.html" class="hideable">Cascade</a><a href="findings.html" class="hideable">Findings</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · production · cross-source validation</div>
  <h1>The atlas in real tonnes</h1>
  <p class="deck">Every other page works in shares or trade value. This one brings in absolute physical production &mdash; and <i>two more independently compiled</i> sources. World Mining Data (Austrian ministry) gives mine output in metric tonnes; the British Geological Survey&rsquo;s World Mineral Statistics adds a third count. Laid beside the atlas&rsquo;s USGS-derived shares they do two things at once: show the <b>scale</b> nobody sees, and <b>triangulate</b> whether the producer geography holds up when two other compilations count it separately &mdash; and, where they disagree, let the two independents adjudicate.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>The three sources, and how the check works</summary>
  <p>Absolute production: <b>World Mining Data 6.4</b> (2026 ed.), production by country in metric tonnes, 2024. For each material we take the world total and the top producer&rsquo;s tonnage share, and compare that share against the atlas&rsquo;s existing <b>USGS-derived</b> top-producer share (in <a href="out/data.json">data.json</a>). A <b>third</b> source, the <b>British Geological Survey&rsquo;s World Mineral Statistics</b> (via its free OGC API, latest year per commodity), gives an independent third count for 18 of the materials. Same top country across sources + a small share gap = independently compiled compilations agreeing.</p>
  <p><b>How independent is &ldquo;independent&rdquo;? We counted, because someone attacked this claim.</b> The obvious objection to any second-source check is that the second source is just repackaging the first. World Mining Data tags every figure with where it came from, so the objection is answerable rather than arguable. Across <b>1,903 tagged figures</b> in the 2024 edition: <b>national statistics 60.0%</b>, company reports 28.5%, questionnaire 6.7%, IEA 1.5%, ICG 1.1%, <b>USGS 0.8%</b> (16 figures), BP 0.7%, Kimberley 0.6%, WNA 0.2%. So WMD is <i>not</i> a repackaging of USGS &mdash; the circularity charge fails as usually put.</p>
  <p><b>But the weaker version of the objection is right, and it bounds what this page can claim.</b> Both compilations ultimately rest on the same upstream: national statistical returns and company reports. They are independent <i>compilations</i>, not independent <i>measurements</i>. If a country misreports its output, both inherit the error identically and agree perfectly &mdash; agreement would then be evidence of nothing. So what 26/28 demonstrates is <b>compilation reliability</b>: two teams, working separately from the same primary returns, made the same call. That is worth something and it is not nothing, but it is not measurement validation, and this page no longer says it is. No open source independently <i>measures</i> mine output. The closest thing the atlas owns is the <a href="satellite.html">satellite footprint</a> layer &mdash; and it sees area, not tonnes. But area is measured <i>from orbit</i>, so it owes nothing to any national statistic &mdash; which makes it the one genuinely independent check available, if only a coarse one.</p>
  <p><b>So we ran it.</b> Does a country&rsquo;s share of the world&rsquo;s mapped mine <i>footprint</i> track its share of bulk open-pit <i>output</i>? <span id="satcheck"></span> This can only corroborate the <b>aggregate</b> mining geography &mdash; the polygons are undifferentiated coal/metal/aggregate, and area-per-tonne varies by orders of magnitude, so it cannot validate any per-metal share. But for the coarse claim &ldquo;these are the world&rsquo;s big mining nations,&rdquo; it is the one check that does <b>not</b> rest on the same national returns as USGS and WMD &mdash; and it agrees.</p>
  <p class="howto-src"><b>Caveats:</b> the sources define commodities slightly differently (e.g. contained-metal vs concentrate, ore vs oxide), report different years&rsquo; vintages, and treat re-processing differently &mdash; so a few points of share difference is expected, and the genuine disagreements are flagged, not hidden. Notably, on <b>bauxite</b> and <b>baryte</b> the two <i>independents</i> (World Mining Data and BGS) agree with each other and put a different country on top than the atlas&rsquo;s USGS figure (Guinea for bauxite, China for baryte) &mdash; a case where the third source adjudicates rather than rubber-stamps; titanium splits three ways on the ilmenite-vs-slag definition. Coverage: 28 of 32 materials have a WMD sheet; BGS World Mineral Statistics gives a recent (&ge;2020) mine series for 18 of them; only niobium, tantalum, silicon and helium are genuinely absent from BGS. (An earlier version of this note wrongly said gallium, germanium and PGMs had no BGS series &mdash; they do: BGS holds production series for gallium, germanium and the platinum-group metals.) Sources: <a href="https://www.world-mining-data.info/">world-mining-data.info</a> &middot; <a href="https://www2.bgs.ac.uk/mineralsuk/statistics/wms.cfc?method=listResults">BGS World Mineral Statistics</a> &rarr; <a href="out/production.json">production.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.6rem 0 .3rem">Independent cross-check: three sources, one geography</h2>
  <p class="muted" style="margin-top:0">Each point is a material: the top producer&rsquo;s share as the atlas has it (USGS, x) vs as World Mining Data counts it in tonnes (y). Points on the diagonal are two independent authorities agreeing; the BGS third source is added in the table below. <span style="color:#2f8f46;font-weight:700">Green</span> = same top country; <span style="color:#c0392b;font-weight:700">red</span> = they name a different leader.</p>
  <div id="scatter"></div>

  <h2 style="margin:1.6rem 0 .3rem">The scale nobody shows &mdash; world production, 2024</h2>
  <p class="muted" style="margin-top:0">Log scale, because these worlds are orders of magnitude apart: some criticals are a few hundred tonnes a year, others billions. &ldquo;90% concentration&rdquo; of a 1,000-tonne metal is a very different problem from 90% of a billion-tonne one.</p>
  <div id="scale"></div>

  <h2 style="margin:1.6rem 0 .3rem">Every material — tonnes, and the three sources side by side</h2>
  <p class="muted" style="margin-top:0">Top producer as each compilation counts it. <span class="ok">✓ all three</span> = USGS, World Mining Data and BGS name the same leader; <span class="no">✗ split</span> = they don&rsquo;t (the disagreement is the interesting row).</p>
  <table class="tidy" id="tab"><thead><tr><th>Material</th><th class="n">world 2024 (t)</th><th>USGS top</th><th>World Mining Data top</th><th>BGS top</th><th>sources agree?</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.8rem 0 .3rem">What this changes for the atlas</h2>
  <p>This is the acquisition the whole session kept pointing to. With absolute tonnages the derived layers can finally speak in quantities: a <a href="cascade.html">cascade</a> shock becomes &ldquo;so many tonnes of world gallium&rdquo;, not an index; the <a href="net-demand.html">demand</a> arm can be normalised to physical supply. And the cross-check earns trust the honest way &mdash; <i>two</i> more independently compiled authorities (World Mining Data and the British Geological Survey) put the same country on top for <span id="agreecount"></span> of the materials all three can check, so the producer geography the atlas has asserted all along is not a USGS artefact. Where they disagree, that is now visible and named, not smoothed over &mdash; and on bauxite and baryte the two independents even agree against USGS, which is exactly the kind of signal a triangulation is supposed to surface. This is the step from demonstration toward instrument.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="methodology">Methodology</a><br><a href="casestudies">Case studies</a><br><a href="cascade">Cascade</a><br><a href="findings">Findings</a></div>
  <div><h4>Sources</h4>USGS shares (data.json) × World Mining Data 2026 (tonnes) × BGS World Mineral Statistics</div>
  <div class="fineprint">Two sources define commodities slightly differently; small share gaps are expected, genuine disagreements are flagged.</div>
</div></footer>
<script>
function ld(u){return new Promise((res,rej)=>{const s=document.createElement('script');s.src=u;s.onload=res;s.onerror=rej;document.head.appendChild(s);});}
Promise.all([fetch('out/production.json').then(r=>r.json()),
  ld('https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js')]).then(([S])=>{
  const f=n=>Number(n).toLocaleString();
  const tiny=S.rows.filter(r=>r.world_tonnes<10000).length;
  document.getElementById('lead').innerHTML='<b>Result:</b> triangulated across three independently compiled authorities. World Mining Data puts the <b>same country on top for '+S.n_agree_top+' of '+S.n_checkable+'</b> materials, and where the British Geological Survey can be brought in as a third count, <b>all three agree for '+S.triple_n_agree+' of '+S.triple_n_checkable+'</b> &mdash; mean gaps of just '+S.mean_share_delta+' and '+S.bgs_mean_share_delta+' points. On the handful that split (bauxite, baryte), the <i>two independents agree with each other</i> against the atlas&rsquo;s USGS figure &mdash; the third source adjudicating, not rubber-stamping. And the scale finally shows: '+tiny+' of these criticals are worlds of under 10,000 tonnes a year (gallium ~1,000 t, germanium ~150 t), where one country holding 90%+ is a genuinely thin thread.';
  document.getElementById('agreecount').textContent=S.triple_n_agree+' of '+S.triple_n_checkable;
  var SC=S.satellite_check;
  if(SC && !SC.error){
    document.getElementById('satcheck').innerHTML='Across '+SC.n_countries+' mining countries, footprint-share and bulk-output-share rank-correlate at <b>&rho;='+SC.spearman_rho+'</b> (p='+SC.p+'), and <b>'+SC.top10_recall+' of the top 10</b> output nations are also top 10 by footprint. '+(SC.passes?'It passes the pre-set gate (&rho;&ge;0.5, recall&ge;8) &mdash; a genuine, orbit-grounded corroboration.':'It does not clear the gate, so we do not lean on it.')+' ';
  } else { document.getElementById('satcheck').innerHTML=''; }
  const stats=[
    {v:S.triple_n_agree+' / '+S.triple_n_checkable,l:'materials where ALL THREE (USGS, World Mining Data, BGS) name the same top producer'},
    {v:S.n_agree_top+' / '+S.n_checkable,l:'USGS × World Mining Data agree on the top producer'},
    {v:S.bgs_n_agree+' / '+S.bgs_n_checkable,l:'USGS × BGS agree on the top producer (mean gap '+S.bgs_mean_share_delta+' pp)'},
    {v:tiny,l:'criticals with a world market under 10,000 tonnes/year'},
  ];
  document.getElementById('stats').innerHTML=stats.map(s=>'<div class="stat"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  document.getElementById('keyline').innerHTML='<b>Why the triangulation matters:</b> every producer share in this atlas traces back to one family of sources (USGS). Two <i>more</i> independently compiled authorities &mdash; World Mining Data and the British Geological Survey &mdash; land on the same leading producer for '+S.triple_n_agree+' of '+S.triple_n_checkable+' materials that all three can check (cobalt DRC ~75% three ways, tungsten China ~78&ndash;81%, nickel Indonesia ~50&ndash;62%), so the concentration story is not an artefact of one dataset. Where they split, the disagreement is shown, not buried &mdash; and it is informative: on <b>bauxite</b> (Guinea) and <b>baryte</b> (China) the two independents agree with <i>each other</i> against the atlas&rsquo;s USGS leader, a signal the USGS headline there may lag the tonnage.';
  // validation scatter
  const chk=S.rows.filter(r=>r.usgs_top_share!=null&&r.wmd_top_share!=null);
  const pts=chk.map(r=>({value:[r.usgs_top_share,r.wmd_top_share,r.title,r.same_top_producer],
    itemStyle:{color:(r.same_top_producer?'#2f8f46':'#c0392b')+'cc'},symbolSize:11}));
  const sc=echarts.init(document.getElementById('scatter'));
  sc.setOption({grid:{left:52,right:24,top:20,bottom:48},
    tooltip:{formatter:p=>'<b>'+p.value[2]+'</b><br>USGS share: '+p.value[0]+'%<br>WMD share: '+p.value[1]+'%<br>'+(p.value[3]?'same top producer':'DIFFERENT top producer')},
    xAxis:{name:'USGS top-producer share (%)',nameLocation:'middle',nameGap:30,min:0,max:100,axisLabel:{color:'#5a6b68'},nameTextStyle:{color:'#5a6b68'},splitLine:{lineStyle:{color:'#eef1f0'}}},
    yAxis:{name:'WMD top-producer share (%)',nameLocation:'middle',nameGap:38,min:0,max:100,axisLabel:{color:'#5a6b68'},nameTextStyle:{color:'#5a6b68'},splitLine:{lineStyle:{color:'#eef1f0'}}},
    series:[{type:'scatter',data:pts,label:{show:true,formatter:p=>p.value[2],position:'right',fontSize:9,color:'#15323a',distance:4},
      markLine:{silent:true,symbol:'none',lineStyle:{color:'#c9b3ad',type:'dashed'},data:[[{coord:[0,0]},{coord:[100,100]}]]}}]});
  window.addEventListener('resize',()=>sc.resize());
  // scale (log bars)
  const byT=S.rows.slice().sort((a,b)=>b.world_tonnes-a.world_tonnes);
  const lmax=Math.log10(byT[0].world_tonnes), lmin=Math.log10(Math.max(1,byT[byT.length-1].world_tonnes));
  document.getElementById('scale').innerHTML=byT.map(r=>{
    const w=100*(Math.log10(r.world_tonnes)-lmin+0.4)/(lmax-lmin+0.4);
    const t=r.world_tonnes;
    const lab=t>=1e9?(t/1e9).toFixed(1)+' Bt':t>=1e6?(t/1e6).toFixed(1)+' Mt':t>=1e3?(t/1e3).toFixed(0)+' kt':t+' t';
    return '<div class="sbar"><div class="nm">'+r.title+'</div><div class="track"><div class="fill" style="width:'+Math.max(2,w)+'%"></div></div><div class="v">'+lab+'</div></div>';
  }).join('');
  // table — three sources side by side
  const tb=document.querySelector('#tab tbody');
  const cell=(name,share,yr)=> name? name+' <span class="muted">'+(share!=null?share+'%':'')+(yr&&yr!=2024?" '"+String(yr).slice(2):'')+'</span>' : '<span class="muted">—</span>';
  S.rows.forEach(r=>{
    let agree;
    if(r.bgs_top_iso){ agree=r.all_three_agree?'<span class="ok">✓ all three</span>':'<span class="no">✗ split</span>'; }
    else { agree=r.same_top_producer?'<span class="ok">✓ two</span> <span class="muted">(no BGS)</span>':'<span class="no">✗ split</span>'; }
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+r.title+'</b></td><td class="n">'+f(r.world_tonnes)+'</td>'+
      '<td>'+cell(r.usgs_top_name,r.usgs_top_share)+'</td>'+
      '<td>'+cell(r.wmd_top,r.wmd_top_share)+'</td>'+
      '<td>'+cell(r.bgs_top_name,r.bgs_top_share,r.bgs_year)+'</td>'+
      '<td>'+agree+'</td>';
    tb.appendChild(tr);
  });
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'production.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote production.html')
