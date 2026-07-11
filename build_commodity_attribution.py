#!/usr/bin/env python3
"""
Commodity attribution of the satellite footprint — and its hard limit.

The satellite page (build_satellite.py) maps 44,929 Maus (2022) mine polygons but flags that they are
ALL-COMMODITY: no per-mineral label. This page asks the obvious next question — can we label them? — and
measures exactly how far the best OPEN data gets us.

Method: overlay the peer-reviewed, georeferenced Jasansky et al. (2023, Scientific Data; Zenodo
10.5281/zenodo.7369478) mine-facility database — 2,413 facilities carrying a `primary_commodity` — onto the
Maus footprint. For each facility point we (tier 1) test point-in-polygon against the Maus polygons, else
(tier 2) attach the nearest polygon within 5 km. Each polygon is assigned to at most one commodity
(inside beats near; nearer wins ties). We then aggregate attributed footprint (km2) by commodity, map it to
the atlas's 32 critical materials, and report how much of the footprint can — and cannot — be labelled.

The honest result is the point of the page: only ~17% of mapped footprint sits at a commodity-labelled
facility, ~95% of that is coal/copper/gold/iron, and barely 4% of the whole footprint ties to a tracked
critical material (almost all copper). Lithium, cobalt, rare earths, tantalum, tungsten and the rest are not
even separable classes in the open data — they are folded into "Other mine" / "Other (poly)-metallic". This
is precisely why the atlas builds material-level geography from trade + USGS/IEA production shares, not
imagery. Public data; deterministic. Run: python build_commodity_attribution.py
"""
import sqlite3, struct, math, json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
MAUS = os.path.join(ROOT, 'raw', 'maus', 'maus_v2.gpkg')
JAS  = os.path.join(ROOT, 'raw', 'jasansky', 'facilities.gpkg')
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))

# atlas's 32 material labels -> clean display names (not the HS trade-product titles)
_PRETTY = {'magnets': 'Rare earths / magnets', 'cokingcoal': 'Coking coal',
           'bauxite': 'Bauxite / aluminium', 'phosphate': 'Phosphate rock'}
LABELS = {m['label']: _PRETTY.get(m['label'], m['label'][:1].upper() + m['label'][1:])
          for m in data['materials']}

# Jasansky primary_commodity  ->  atlas material label (only tracked criticals map)
CRIT = {
    'Lithium': 'lithium', 'Cobalt': 'cobalt', 'Nickel': 'nickel', 'Graphite': 'graphite',
    'Rare earth elements': 'magnets', 'Rare earths': 'magnets', 'REE': 'magnets',
    'Tantalum': 'tantalum', 'Niobium': 'niobium', 'Tungsten': 'tungsten', 'Titanium': 'titanium',
    'Vanadium': 'vanadium', 'Manganese': 'manganese', 'Magnesium': 'magnesium',
    'Platinum': 'platinum', 'Palladium': 'palladium', 'Platinum-group metals': 'platinum', 'PGM': 'platinum',
    'Antimony': 'antimony', 'Arsenic': 'arsenic', 'Beryllium': 'beryllium', 'Gallium': 'gallium',
    'Germanium': 'germanium', 'Boron': 'boron', 'Borates': 'boron',
    'Fluorspar': 'fluorspar', 'Fluorite': 'fluorspar', 'Baryte': 'baryte', 'Barite': 'baryte',
    'Phosphate': 'phosphate', 'Phosphorus': 'phosphorus', 'Feldspar': 'feldspar',
    'Strontium': 'strontium', 'Silicon': 'silicon', 'Hafnium': 'hafnium', 'Helium': 'helium',
    'Bauxite': 'bauxite', 'Aluminium': 'bauxite', 'Copper': 'copper',
}
BUF_KM = 5.0
CELL = 0.5

# ---------- GPKG WKB helpers (stdlib only) ----------
def _hdr_off(blob):
    flags = blob[3]; env = (flags >> 1) & 0x07
    return 8 + {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}.get(env, 0)

def read_point(blob):
    if blob is None: return None
    off = _hdr_off(blob); le = '<' if blob[off] == 1 else '>'
    gt = struct.unpack(le + 'I', blob[off + 1:off + 5])[0] & 0xffff; p = off + 5
    if gt == 1:
        return struct.unpack(le + 'dd', blob[p:p + 16])
    if gt == 4:  # multipoint -> centroid of member points
        n = struct.unpack(le + 'I', blob[p:p + 4])[0]; p += 4
        if n == 0: return None
        xs = ys = 0.0
        for _ in range(n):
            ple = '<' if blob[p] == 1 else '>'; p += 5
            x, y = struct.unpack(ple + 'dd', blob[p:p + 16]); p += 16; xs += x; ys += y
        return (xs / n, ys / n)
    return None

def read_ring(blob):
    off = _hdr_off(blob); le = '<' if blob[off] == 1 else '>'
    gt = struct.unpack(le + 'I', blob[off + 1:off + 5])[0] & 0xffff; p = off + 5
    if gt != 3: return None
    nr = struct.unpack(le + 'I', blob[p:p + 4])[0]; p += 4
    if nr == 0: return None
    npts = struct.unpack(le + 'I', blob[p:p + 4])[0]; p += 4
    co = struct.unpack(le + f'{2 * npts}d', blob[p:p + 16 * npts])
    return [(co[2 * i], co[2 * i + 1]) for i in range(npts)]

def pip(x, y, ring):
    inside = False; n = len(ring); j = n - 1
    for i in range(n):
        xi, yi = ring[i]; xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi):
            inside = not inside
        j = i
    return inside

def km(dlat, dlon, lat):
    return math.hypot(dlat * 111.0, dlon * 111.0 * math.cos(math.radians(lat)))

# ---------- load Maus polygons ----------
con = sqlite3.connect(MAUS)
polys = []  # [minx,miny,maxx,maxy,cx,cy,area,iso,ring]
for iso, area, blob in con.execute('SELECT ISO3_CODE,AREA,geom FROM mining_polygons'):
    r = read_ring(blob)
    if not r: continue
    xs = [c[0] for c in r]; ys = [c[1] for c in r]
    polys.append([min(xs), min(ys), max(xs), max(ys),
                  (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, area, iso, r])
con.close()
tot_area = sum(p[6] for p in polys)
grid = defaultdict(list)
for i, p in enumerate(polys):
    grid[(math.floor(p[4] / CELL), math.floor(p[5] / CELL))].append(i)

# ---------- load Jasansky facilities ----------
con = sqlite3.connect(JAS)
facs = []            # (x,y,primary,iso)
prim_all = defaultdict(int); prim_coord = defaultdict(int)
fac_products = []    # (primary, commodities_products, has_coords) for byproduct analysis
for prim, prod, iso, blob in con.execute(
        'SELECT primary_commodity,commodities_products,GID_0,geom FROM facilities'):
    prim_all[prim] += 1
    pt = read_point(blob)
    ok = bool(pt and pt[0] == pt[0] and pt[1] == pt[1] and abs(pt[0]) <= 180 and abs(pt[1]) <= 90)
    if ok:
        prim_coord[prim] += 1
        facs.append((pt[0], pt[1], prim, iso))
    fac_products.append((prim, prod, ok))
con.close()

# ---------- load USGS MRDS (augments Jasansky; US-dense, includes occurrences/prospects) ----------
import csv as _csv
MRDS_FILE = os.path.join(ROOT, 'raw', 'mrds', 'mrds_slim.csv')
def mrds_crit(name):
    s = (name or '').lower()
    for k, v in (('copper', 'copper'), ('cobalt', 'cobalt'), ('nickel', 'nickel'), ('lithium', 'lithium'),
                 ('graphite', 'graphite'), ('manganese', 'manganese'), ('tungsten', 'tungsten'),
                 ('titanium', 'titanium'), ('vanadium', 'vanadium'), ('antimony', 'antimony'),
                 ('beryllium', 'beryllium'), ('tantalum', 'tantalum'), ('arsenic', 'arsenic'),
                 ('gallium', 'gallium'), ('germanium', 'germanium'), ('strontium', 'strontium'),
                 ('silicon', 'silicon'), ('boron', 'boron'), ('bauxite', 'bauxite'), ('aluminum', 'bauxite'),
                 ('hafnium', 'hafnium'), ('helium', 'helium'), ('feldspar', 'feldspar')):
        if k in s:
            return v
    if 'niobium' in s or 'columbium' in s: return 'niobium'
    if 'rare earth' in s or 'rare-earth' in s: return 'magnets'
    if 'platinum' in s: return 'platinum'
    if 'palladium' in s: return 'palladium'
    if 'fluor' in s: return 'fluorspar'
    if 'barite' in s or 'baryte' in s or 'barium' in s: return 'baryte'
    if 'magnesi' in s: return 'magnesium'
    if 'phosph' in s: return 'phosphate'
    return None
mrds_pts = []   # (x, y, atlas_label_or_None, is_producer)
if os.path.exists(MRDS_FILE):
    with open(MRDS_FILE, encoding='utf-8', newline='') as f:
        for row in _csv.DictReader(f):
            try:
                x = float(row['lon']); y = float(row['lat'])
            except (ValueError, KeyError):
                continue
            if not (abs(x) <= 180 and abs(y) <= 90):
                continue
            mrds_pts.append((x, y, mrds_crit(row.get('commod1')), 'producer' in (row.get('dev_stat') or '').lower()))

# ---------- spatial join: one commodity per polygon (parametrised by buffer) ----------
def run_join(buf_km):
    """Return assignment {poly_idx: (rank, dist, primary, iso)} for a given tier-2 buffer."""
    assign = {}
    for x, y, prim, iso in facs:
        gx = math.floor(x / CELL); gy = math.floor(y / CELL)
        cand = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cand += grid.get((gx + dx, gy + dy), [])
        inside = None
        for idx in cand:
            p = polys[idx]
            if p[0] <= x <= p[2] and p[1] <= y <= p[3] and pip(x, y, p[8]):
                inside = idx; break
        if inside is not None:
            cur = assign.get(inside)
            if cur is None or cur[0] > 0:
                assign[inside] = (0, 0.0, prim, iso)
            continue
        if buf_km <= 0:
            continue
        best = None; bd = 1e9
        for idx in cand:
            p = polys[idx]; d = km(y - p[5], x - p[4], y)
            if d < bd: bd = d; best = idx
        if best is not None and bd <= buf_km:
            cur = assign.get(best)
            if cur is None or (cur[0] == 1 and cur[1] > bd):
                assign[best] = (1, bd, prim, iso)
    return assign

def summarise(assign):
    """Return (attributed_area, critical_area) for an assignment."""
    ma = ca = 0.0
    for idx, (rank, d, prim, iso) in assign.items():
        a = polys[idx][6]; ma += a
        if CRIT.get(prim): ca += a
    return ma, ca

# ---------- coverage: how far do public registers get us? (Jasansky vs +MRDS) ----------
def coverage_join(points, buf_km=BUF_KM):
    """points: iterable of (x, y, atlas_label_or_None); one label per polygon (inside beats near)."""
    assign = {}
    for x, y, lab in points:
        gx = math.floor(x / CELL); gy = math.floor(y / CELL); cand = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cand += grid.get((gx + dx, gy + dy), [])
        inside = None
        for idx in cand:
            p = polys[idx]
            if p[0] <= x <= p[2] and p[1] <= y <= p[3] and pip(x, y, p[8]):
                inside = idx; break
        if inside is not None:
            cur = assign.get(inside)
            if cur is None or cur[0] > 0:
                assign[inside] = (0, 0.0, lab)
            continue
        if buf_km <= 0:
            continue
        best = None; bd = 1e9
        for idx in cand:
            p = polys[idx]; d = km(y - p[5], x - p[4], y)
            if d < bd: bd = d; best = idx
        if best is not None and bd <= buf_km:
            cur = assign.get(best)
            if cur is None or (cur[0] == 1 and cur[1] > bd):
                assign[best] = (1, bd, lab)
    ma = sum(polys[i][6] for i in assign)
    ca = sum(polys[i][6] for i, (rk, d, lab) in assign.items() if lab)
    ca_us = sum(polys[i][6] for i, (rk, d, lab) in assign.items() if lab and polys[i][7] == 'USA')
    return {'attributed_pct': round(100 * ma / tot_area, 1), 'critical_pct': round(100 * ca / tot_area, 2),
            'critical_us_share': (round(100 * ca_us / ca, 0) if ca else 0), 'n_poly': len(assign)}

jas_pts = [(x, y, CRIT.get(prim)) for (x, y, prim, iso) in facs]
mrds_all = [(x, y, lab) for (x, y, lab, prod) in mrds_pts]
mrds_prod = [(x, y, lab) for (x, y, lab, prod) in mrds_pts if prod]
registers = {
    'n_mrds': len(mrds_pts),
    'jasansky': coverage_join(jas_pts),
    'jasansky_mrds': coverage_join(jas_pts + mrds_all),
    'mrds_producer_only': coverage_join(jas_pts + mrds_prod),
}

# sensitivity across tier-2 buffers (inside-only .. 25 km) — shows the headline is a band, not a bound
sensitivity = []
for b in (0, 2, 5, 10, 25):
    aj = run_join(b); ma, ca = summarise(aj)
    sensitivity.append({'buffer_km': b, 'attributed_pct': round(100 * ma / tot_area, 1),
                        'critical_pct': round(100 * ca / tot_area, 2), 'n_poly': len(aj)})

# ---------- headline aggregate (buffer = BUF_KM) ----------
assign = run_join(BUF_KM)
area_by_prim = defaultdict(float)
tier1 = tier2 = 0
crit_area = defaultdict(float)
crit_polys = defaultdict(int)
crit_country = defaultdict(lambda: defaultdict(float))
matched_area = 0.0
for idx, (rank, d, prim, iso) in assign.items():
    a = polys[idx][6]; matched_area += a
    area_by_prim[prim] += a
    tier1 += (rank == 0); tier2 += (rank == 1)
    lab = CRIT.get(prim)
    if lab:
        crit_area[lab] += a; crit_polys[lab] += 1; crit_country[lab][iso] += a

# ---------- byproduct analysis: does the richer free-text field name the criticals? ----------
# Attributing AREA to a byproduct would double-count (a Cu mine's footprint is copper's), so we DON'T —
# but we report how often each critical appears as a secondary product, for full transparency.
SECONDARY_KW = {
    'lithium': ['lithium'], 'cobalt': ['cobalt'], 'magnets': ['rare earth', 'monazite', 'neodym',
    'praseodym', 'dysprosium', 'cerium', 'lanthan'], 'tantalum': ['tantal', 'coltan'],
    'niobium': ['niob', 'columb'], 'tungsten': ['tungsten', 'wolfram', 'scheelite'],
    'antimony': ['antimony', 'stibnite'], 'graphite': ['graphite'], 'vanadium': ['vanadium'],
    'titanium': ['titanium', 'ilmenite', 'rutile'], 'manganese': ['manganese'],
    'platinum': ['platinum', 'palladium', 'pgm'], 'boron': ['boron', 'borate'],
    'baryte': ['baryt', 'barit'], 'fluorspar': ['fluor'], 'beryllium': ['beryl'], 'silicon': ['silic'],
}
byproduct = {}
for lab, kws in SECONDARY_KW.items():
    n = nc = 0
    for prim, prod, ok in fac_products:
        s = ((prod or '') + ' ' + (prim or '')).lower()
        if any(k in s for k in kws):
            n += 1
            if ok: nc += 1
    if n:
        byproduct[lab] = {'label': lab, 'title': LABELS.get(lab, lab), 'n_mentions': n, 'n_coords': nc,
                          'primary': lab in {CRIT.get(p) for p, _, _ in fac_products}}

# per-commodity list (11 Jasansky classes), flag which map to a tracked critical
by_commodity = []
for prim, a in sorted(area_by_prim.items(), key=lambda kv: -kv[1]):
    lab = CRIT.get(prim)
    by_commodity.append({
        'commodity': prim, 'area_km2': round(a, 1),
        'pct_total': round(100 * a / tot_area, 2),
        'critical': bool(lab), 'atlas_label': lab,
    })

# critical-material rows: which of the 32 are resolvable here (by primary_commodity), which are not
resolvable = {}
for lab, a in crit_area.items():
    tops = sorted(crit_country[lab].items(), key=lambda kv: -kv[1])[:4]
    resolvable[lab] = {'label': lab, 'title': LABELS.get(lab, lab),
                       'area_km2': round(a, 1), 'n_polygons': crit_polys[lab],
                       'top_countries': [{'iso3': i, 'area_km2': round(v, 1)} for i, v in tops]}
unresolved = sorted(LABELS[l] for l in LABELS if l not in resolvable)

crit_total = sum(crit_area.values())
out = {
    'generated': data.get('generated'),
    'method': {'buffer_km': BUF_KM, 'tiers': 'point-in-polygon, else nearest polygon within 5 km',
               'one_commodity_per_polygon': True},
    'maus_total_area_km2': round(tot_area),
    'maus_n_polygons': len(polys),
    'jasansky_n_facilities': sum(prim_all.values()),
    'jasansky_n_with_coords': len(facs),
    'jasansky_n_classes': len(prim_all),
    'jasansky_classes': sorted(
        [{'commodity': k, 'n_all': prim_all[k], 'n_coords': prim_coord.get(k, 0),
          'critical': bool(CRIT.get(k)), 'atlas_label': CRIT.get(k)} for k in prim_all],
        key=lambda d: -d['n_all']),
    'attributed_area_km2': round(matched_area),
    'attributed_pct': round(100 * matched_area / tot_area, 1),
    'unattributed_pct': round(100 * (1 - matched_area / tot_area), 1),
    'n_poly_matched': len(assign),
    'tier1_inside': tier1, 'tier2_near': tier2,
    'by_commodity': by_commodity,
    'critical_area_km2': round(crit_total, 1),
    'critical_pct_of_attributed': round(100 * crit_total / matched_area, 1),
    'critical_pct_of_total': round(100 * crit_total / tot_area, 2),
    'critical_resolved': sorted(resolvable.values(), key=lambda d: -d['area_km2']),
    'critical_unresolved': unresolved,
    'n_critical_resolved': len(resolvable),
    'n_critical_total': len(LABELS),
    'sensitivity': sensitivity,
    'byproduct': sorted(byproduct.values(), key=lambda d: -d['n_mentions']),
    'temporal_note': 'Maus imagery ~2019; Jasansky facilities compiled to ~2021-2023.',
    'registers': registers,
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'commodity_attribution.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/commodity_attribution.json')
print(f"  footprint {out['maus_total_area_km2']:,} km2 | attributed {out['attributed_pct']}% | "
      f"critical {out['critical_pct_of_total']}% ({out['n_critical_resolved']}/{out['n_critical_total']} materials resolved)")

# ------------------------------------------------------------------ page
HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Which mineral? The limit of satellite mine maps · Critical Materials Atlas</title>
<meta name="description" content="Can satellite mine polygons be labelled by commodity? We overlay the best open, peer-reviewed georeferenced mine database (Jasansky et al. 2023) onto the Maus footprint and measure exactly how far commodity attribution gets — and why it fails for the critical materials that matter most.">
<meta property="og:title" content="Which mineral is that mine? The hard limit of satellite maps">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .muted{color:#5a6b68;font-size:.86rem}
 .stat4{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin:1.2rem 0}
 @media(max-width:720px){.stat4{grid-template-columns:repeat(2,1fr)}}
 .stat{background:#fff;border:1px solid #e3e9e8;border-left:4px solid #0e7c74;border-radius:10px;padding:.8rem .9rem}
 .stat .v{font-size:1.5rem;font-weight:800;color:#15323a;letter-spacing:-.02em}
 .stat .l{font-size:.76rem;color:#5a6b68;margin-top:.15rem;line-height:1.35}
 .stat.warn{border-left-color:#c0392b}.stat.warn .v{color:#c0392b}
 .bars{margin:.6rem 0 0}
 .bar{display:grid;grid-template-columns:130px 1fr 78px;align-items:center;gap:.6rem;margin:.28rem 0;font-size:.86rem}
 .bar .nm{text-align:right;color:#15323a;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
 .bar .track{background:#eef3f2;border-radius:5px;height:20px;overflow:hidden}
 .bar .fill{height:100%;background:#9aa6ad;border-radius:5px}
 .bar.crit .fill{background:#0e7c74}.bar.crit .nm{color:#0e7c74}
 .bar .val{text-align:right;color:#5a6b68;font-variant-numeric:tabular-nums}
 table.tidy{width:100%;border-collapse:collapse;font-size:.88rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .chips{display:flex;flex-wrap:wrap;gap:.35rem;margin:.5rem 0 0}
 .chip{font-size:.78rem;background:#f4f7f6;border:1px solid #e3e9e8;border-radius:20px;padding:.12rem .6rem;color:#5a6b68}
 .keyline{background:#fbf3f2;border:1px solid #f0d9d5;border-left:4px solid #c0392b;border-radius:10px;padding:.9rem 1.1rem;margin:1.2rem 0}
 .keyline b{color:#c0392b}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="methodology.html">Methodology</a><a href="satellite.html">Satellite</a>
  <a href="limitations.html" class="hideable">Limitations</a><a href="findings.html" class="hideable">Findings</a>
  <a href="https://github.com/materials-atlas/comtrade-reconcile" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · satellite &middot; the commodity question</div>
  <h1>Which mineral is that mine?</h1>
  <p class="deck">The <a href="satellite.html" style="color:#fff;text-decoration:underline">satellite page</a> maps where mining scars the earth &mdash; but the polygons are <b>all-commodity</b>: they can&rsquo;t tell lithium from coal. So we asked the obvious next question and <i>measured the answer</i>: overlay the best open, peer-reviewed, georeferenced mine database onto the footprint and see how much of it can actually be labelled. The result is the honest case for why this atlas builds material-level geography from <i>production statistics and trade</i>, using imagery only as a physical cross-check.</p>
</div></section>
<article style="max-width:1060px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>How the attribution works, and every caveat</summary>
  <p>We overlay <b>Jasansky et al. (2023, <i>Scientific Data</i>)</b> &mdash; a peer-reviewed, georeferenced database of <span id="njas"></span> mine facilities, each carrying a <code>primary_commodity</code> &mdash; onto the <b>Maus (2022)</b> all-commodity polygons. For each facility we test <b>point-in-polygon</b>; failing that, we attach the <b>nearest polygon within 5&nbsp;km</b>. Each polygon is assigned to at most one commodity (inside beats near; nearer wins ties). Attributed footprint is then summed by commodity and mapped to the atlas&rsquo;s 32 critical materials.</p>
  <p class="howto-src"><b>Caveats (stated in full):</b> Jasansky covers 2,413 large, company-reported mines &mdash; not the artisanal/small sites that make up much of the Maus polygon count, so low coverage is <i>expected and is part of the finding</i>. We attribute footprint area by <code>primary_commodity</code>, the mine&rsquo;s main product; the database also carries a free-text <code>commodities_products</code> field naming <i>secondary</i> products &mdash; we report those separately below but do <b>not</b> credit area to them, because a copper mine&rsquo;s footprint is copper&rsquo;s even when it yields trace cobalt. Generic &ldquo;Coal&rdquo; is not split into coking vs thermal, so it is <b>not</b> counted as the atlas&rsquo;s <i>coking coal</i>. The 17% / 4% headline is a tier-2-buffer estimate, not a hard bound &mdash; see the sensitivity band below (inside-only to 25&nbsp;km). Distances use nearest-centroid on WGS84 degrees (screening-grade, not projected). Temporal offset: Maus imagery ~2019, Jasansky compiled ~2021&ndash;23; the two share an author (V. Maus), so this is a consistency overlay, not a fully independent check. Sources: Maus et al. 2022 (<a href="https://doi.org/10.1594/PANGAEA.942325">PANGAEA</a>) &middot; Jasansky et al. 2023 (<a href="https://doi.org/10.5281/zenodo.7369478">Zenodo</a>, CC-BY) &rarr; <a href="out/commodity_attribution.json">commodity_attribution.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>
  <p class="muted" id="sens" style="margin:.2rem 0 0"></p>

  <h2 style="margin:1.6rem 0 .3rem">What the labelled footprint actually is</h2>
  <p class="muted" style="margin-top:0">Attributed mine area (km&sup2;) by the facility database&rsquo;s commodity classes. <span style="color:#0e7c74;font-weight:700">Green</span> = maps to one of the atlas&rsquo;s 32 critical materials; grey = not tracked (coal, gold, iron, silver, zinc, &ldquo;other&rdquo;).</p>
  <div class="bars" id="bars"></div>

  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.6rem 0 .3rem">The 32 critical materials: what open mine data can and can&rsquo;t see</h2>
  <p class="muted" style="margin-top:0">Of the atlas&rsquo;s 32 tracked materials, only these are resolvable as a distinct commodity with mapped footprint in the open database:</p>
  <table class="tidy" id="restab"><thead><tr><th>Material</th><th class="n">footprint km²</th><th class="n">polygons</th><th>where (top countries)</th></tr></thead><tbody></tbody></table>
  <p class="muted" id="unres" style="margin-top:.8rem"></p>
  <div class="chips" id="unreschips"></div>

  <h2 style="margin:1.6rem 0 .3rem">&ldquo;But those mines yield lithium and cobalt too&rdquo; &mdash; as byproducts, yes</h2>
  <p class="muted" style="margin-top:0">A fair objection: the same database has a free-text <code>commodities_products</code> field that <i>mentions</i> more minerals. It does &mdash; but only as <b>secondary products of a handful of large mines</b>, and crediting a mine&rsquo;s whole footprint to a trace byproduct would double-count. Here is every mention, coordinates or not, so you can judge:</p>
  <table class="tidy" id="bytab"><thead><tr><th>Critical material</th><th class="n">mines mentioning it</th><th class="n">with coordinates</th><th>as</th></tr></thead><tbody></tbody></table>
  <p class="muted" style="margin-top:.5rem">Tungsten, graphite, vanadium, beryllium and others don&rsquo;t appear at all &mdash; not even in the free text. So the richer field doesn&rsquo;t rescue a lithium or rare-earth <i>footprint</i>; it confirms these minerals surface, at most, as bylines in copper/nickel/gold operations.</p>

  <h2 style="margin:1.8rem 0 .3rem">How far do the best public registers get us?</h2>
  <p class="muted" style="margin-top:0">The obvious question &mdash; would a bigger phonebook of mines help? &mdash; tested directly. We stack the largest public mine register (<b>USGS MRDS</b>, <span id="nmrds"></span> georeferenced sites with a commodity) onto Jasansky and re-run the join. It roughly doubles the labelling &mdash; and then hits a wall.</p>
  <table class="tidy" id="regtab"><thead><tr><th>Register(s) joined to the satellite footprint</th><th class="n">footprint labelled</th><th class="n">ties to a critical material</th></tr></thead><tbody></tbody></table>
  <p class="muted" id="regnote" style="margin-top:.5rem"></p>

  <h2 style="margin:1.8rem 0 .3rem">Why the atlas reads production and trade, not imagery</h2>
  <p>Satellite polygons prove <i>where</i> the earth is disturbed, and the <a href="satellite.html">footprint page</a> uses them exactly that way &mdash; as a physical cross-check on the producer story. But this page shows their ceiling for <i>identity</i>: even with the two largest public mine registers stacked on (above), well over half the mapped footprint stays unlabelled, and the minerals at the centre of every supply-risk debate &mdash; lithium, cobalt, rare earths, tantalum, tungsten &mdash; barely register as primary products in open mine data. Part of that 4% is an artifact of a large-mine registry meeting an all-commodity footprint; but the deeper limit is structural &mdash; the open taxonomy resolves ~11 broad classes and won&rsquo;t name the criticals no matter how the buffer is tuned. So <i>material identity</i> has to come from sources that <i>do</i> resolve all 32 minerals: <a href="findings.html">USGS &amp; IEA production shares</a> for the geography, reconciled <a href="methodology.html">bilateral trade</a> for the flows. Imagery corroborates the footprint; it doesn&rsquo;t name the mineral. This page is the receipt for that design choice.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="satellite.html">Satellite footprint</a><br><a href="mining-expansion.html">Mining expansion</a><br><a href="limitations.html">Limitations</a><br><a href="methodology.html">Methodology</a></div>
  <div><h4>Sources</h4>Maus et al. 2022 (mine polygons) · Jasansky et al. 2023 (facility commodities) · USGS · IEA</div>
  <div class="fineprint">Commodity attribution overlays 2,413 open, peer-reviewed mine facilities on the all-commodity satellite footprint; it quantifies a limitation, it is not a per-mineral map.</div>
</div></footer>
<script>
fetch('out/commodity_attribution.json').then(r=>r.json()).then(S=>{
  const f=n=>Number(n).toLocaleString();
  document.getElementById('njas').textContent=f(S.jasansky_n_facilities);
  document.getElementById('p1').textContent=S.unattributed_pct;
  document.getElementById('lead').innerHTML='<b>Result:</b> of '+f(S.maus_total_area_km2)+' km² of satellite-mapped mine footprint, only <b>'+S.attributed_pct+'%</b> sits at a commodity-labelled facility &mdash; and most of that is coal, copper, gold and iron. Just <b>'+S.critical_pct_of_total+'%</b> of the whole footprint ties to one of the atlas&rsquo;s 32 critical materials, almost all of it copper. The minerals that define &ldquo;criticality&rdquo; &mdash; lithium, cobalt, rare earths &mdash; barely register.';
  // stat tiles
  const stats=[
    {v:f(S.maus_total_area_km2)+' km²',l:'total mapped mine footprint (Maus 2022, '+f(S.maus_n_polygons)+' polygons)'},
    {v:S.attributed_pct+'%',l:'of footprint attributable to any commodity ('+f(S.n_poly_matched)+' polygons, '+f(S.tier1_inside)+' inside + '+f(S.tier2_near)+' within 5 km)'},
    {v:S.critical_pct_of_total+'%',l:'of footprint ties to a tracked critical material',warn:true},
    {v:S.n_critical_resolved+' / '+S.n_critical_total,l:'critical materials resolvable as a distinct labelled commodity',warn:true},
  ];
  document.getElementById('stats').innerHTML=stats.map(s=>'<div class="stat'+(s.warn?' warn':'')+'"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  // sensitivity band — headline is an estimate, not a hard bound
  if(S.sensitivity){
    const band=S.sensitivity.map(s=>(s.buffer_km===0?'inside-only':s.buffer_km+' km')+': '+s.attributed_pct+'% / '+s.critical_pct+'%').join(' &nbsp;·&nbsp; ');
    document.getElementById('sens').innerHTML='<b>Sensitivity</b> (tier-2 buffer &rarr; attributed% / critical%): '+band+'. The headline uses 5 km; the critical share stays ~3&ndash;5% across the whole range &mdash; widening the buffer never surfaces the missing minerals.';
  }
  // bars
  const mx=Math.max.apply(null,S.by_commodity.map(d=>d.area_km2));
  document.getElementById('bars').innerHTML=S.by_commodity.map(d=>{
    const nm=d.critical?(LABEL(d.atlas_label)):d.commodity;
    return '<div class="bar'+(d.critical?' crit':'')+'"><div class="nm" title="'+d.commodity+'">'+nm+'</div>'+
      '<div class="track"><div class="fill" style="width:'+Math.max(1.5,100*d.area_km2/mx)+'%"></div></div>'+
      '<div class="val">'+f(Math.round(d.area_km2))+'</div></div>';
  }).join('');
  function LABEL(lab){const m=(S.critical_resolved.find(x=>x.label===lab));return m?m.title:lab;}
  // keyline
  document.getElementById('keyline').innerHTML='<b>The tell:</b> the open database&rsquo;s <i>primary</i> label resolves to just '+S.jasansky_n_classes+' broad classes &mdash; coal, gold, iron, copper, zinc, aluminium, nickel, silver, and two literal &ldquo;other&rdquo; buckets. Lithium, cobalt, rare earths, tantalum, tungsten, antimony, graphite and the rest are <b>never a primary class</b> &mdash; they are folded into &ldquo;Other mine&rdquo; and &ldquo;Other (poly)-metallic&rdquo; (and, as the next table shows, surface only as sparse byproduct mentions). You cannot map a footprint the data never attributes.';
  // resolved table
  const tb=document.querySelector('#restab tbody');
  S.critical_resolved.forEach(m=>{
    const where=m.top_countries.map(c=>c.iso3+' ('+f(Math.round(c.area_km2))+')').join(', ');
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+m.title+'</b></td><td class="n">'+f(Math.round(m.area_km2))+'</td><td class="n">'+m.n_polygons+'</td><td class="muted">'+where+'</td>';
    tb.appendChild(tr);
  });
  // unresolved
  document.getElementById('unres').innerHTML='The other <b>'+(S.n_critical_total-S.n_critical_resolved)+'</b> tracked materials have <b>no distinct primary footprint</b> in the open mine data &mdash; not because they aren&rsquo;t mined, but because the open database never labels them as a mine&rsquo;s main product:';
  document.getElementById('unreschips').innerHTML=S.critical_unresolved.map(t=>'<span class="chip">'+t+'</span>').join('');
  // byproduct table
  const byb=document.querySelector('#bytab tbody');
  (S.byproduct||[]).forEach(m=>{
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+m.title+'</b></td><td class="n">'+m.n_mentions+'</td><td class="n">'+m.n_coords+'</td><td class="muted">'+(m.primary?'primary at some sites + byproduct':'byproduct only &mdash; never a primary product')+'</td>';
    byb.appendChild(tr);
  });
  // registers: how far do public mine registers get us?
  const R=S.registers;
  if(R){
    document.getElementById('nmrds').textContent=f(R.n_mrds);
    const rt=document.querySelector('#regtab tbody');
    const rows=[['Jasansky only (this page&rsquo;s baseline)',R.jasansky],
      ['+ USGS MRDS (all sites)',R.jasansky_mrds],
      ['+ MRDS, producing mines only (conservative)',R.mrds_producer_only]];
    rows.forEach((rw,i)=>{const x=rw[1];const tr=document.createElement('tr');
      const strong=i==1;
      tr.innerHTML='<td'+(strong?' style="font-weight:700"':'')+'>'+rw[0]+'</td>'+
        '<td class="n"'+(strong?' style="font-weight:700"':'')+'>'+x.attributed_pct+'%</td>'+
        '<td class="n" style="font-weight:700;color:'+(x.critical_pct>=8?'#0e7c74':'#5a6b68')+'">'+x.critical_pct+'%</td>';
      rt.appendChild(tr);});
    const jm=R.jasansky_mrds;
    document.getElementById('regnote').innerHTML='So the honest answer to &ldquo;would more registers help?&rdquo; is <b>yes, up to a point</b>: the best public data roughly <b>doubles</b> labelling (17&rarr;'+jm.attributed_pct+'%) and critical-material coverage (4&rarr;'+jm.critical_pct+'%), and only ~'+jm.critical_us_share+'% of that critical area is in the US, so it&rsquo;s a genuine global gain, not a US artefact. But <b>~'+Math.round(100-jm.attributed_pct)+'% of the footprint still can&rsquo;t be labelled</b> &mdash; that residual is the irreducible gap: artisanal and small-scale mines that appear in <i>no</i> register (much of the world&rsquo;s cobalt, gold, tantalum, tin), plus the by-product problem above. MRDS also leans on non-producing occurrences; the conservative producing-only read is '+R.mrds_producer_only.attributed_pct+'% / '+R.mrds_producer_only.critical_pct+'%.';
  }
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'commodity-attribution.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote commodity-attribution.html')
