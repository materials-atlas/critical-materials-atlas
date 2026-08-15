"""The Product Space as the Hidalgo-Hausmann NETWORK, rebuilt to STAGE ITS OWN ARGUMENT (council review).
Nodes = products, edges = proximity backbone (max spanning tree + phi>=0.55), coloured by sector, sized by
world exports. The critical-material ore->refined(->magnet) chains are highlighted AND wired to the capture
data (phi-distance, PCI gain, per-country density from mine_refine.json) so the mine->refine "canyon" is
shown, not just captioned. Layout is computed server-side (networkx, seeded) and frozen -> reproducible,
screenshot-stable. Self-contained interactive HTML at product-space.html.

Features: guided material mode (trace ore->refined->magnet with phi + dPCI + real refiners), country mode
with featured presets + a capture readout, chain edges drawn even when phi<threshold (low phi = the finding),
richer hover (PCI, phi-to-twin, physical refiners), CVD-safer role encoding, a method footer, permalink state.
Run:  python build_ps_network.py [year]
"""
import os, sys, io, zipfile, json
import numpy as np, pandas as pd, networkx as nx
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2022
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
TOPN = 600
PHI_EDGE = 0.55
MIN_VALUE = 500.0        # thousand USD -- MATCH build_productspace.py so the map's M == the analysis's M
MIN_SHARE = 0.001

def sector(code):
    h = int(code[:2])
    if h <= 5:   return ('Animal', '#8c6d3f')
    if h <= 15:  return ('Vegetable', '#4f9d69')
    if h <= 24:  return ('Food & bev.', '#79b84a')
    if h <= 27:  return ('Minerals & fuels', '#b07a2e')
    if h <= 38:  return ('Chemicals', '#8a5cf0')
    if h <= 40:  return ('Plastic & rubber', '#b39ddb')
    if h <= 43:  return ('Hides & skins', '#a15c4a')
    if h <= 49:  return ('Wood & paper', '#5c8a72')
    if h <= 63:  return ('Textiles', '#e05a8a')
    if h <= 67:  return ('Footwear & apparel', '#e07aa8')
    if h <= 71:  return ('Stone, glass, gems', '#2fae9e')
    if h <= 83:  return ('Metals', '#6b7f99')
    if h <= 85:  return ('Machinery & elec.', '#2f7ed8')
    if h <= 89:  return ('Transport', '#1f4e9c')
    return ('Instruments & misc.', '#e0863c')

CROSSWALK = {'copper': ('260300', '740311'), 'nickel': ('260400', '750210'), 'cobalt': ('260500', '282200'),
             'tungsten': ('261100', '810194'), 'titanium': ('261400', '810820'), 'antimony': ('261710', '811010'),
             'bauxite': ('260600', '281820')}
DOWNSTREAM = {'284690': ('rare earths', 'refined', 'REE oxide'),   # ILLUSTRATIVE: aggregated/dirty HS codes
              '280530': ('rare earths', 'refined', 'REE metal'),
              '850511': ('magnet', 'magnet', 'NdFeB magnet')}
HL = {}
for _lab, (_o, _r) in CROSSWALK.items():
    HL[_o] = (_lab, 'ore', _lab + ' ore'); HL[_r] = (_lab, 'refined', _lab + ' refined')
HL.update(DOWNSTREAM)
# explicit chain edges (drawn even when phi < threshold): ore -> refined for the 7, plus REE oxide->metal->magnet
CHAIN_CODES = [(o, r, lab) for lab, (o, r) in CROSSWALK.items()] + \
              [('284690', '280530', 'rare earths'), ('280530', '850511', 'rare earths')]

print(f'reading BACI HS17 {YEAR} ...', flush=True)
with zipfile.ZipFile(BACI_ZIP) as z:
    raw = pd.read_csv(io.TextIOWrapper(z.open(f'BACI_HS17_Y{YEAR}_V202601.csv'), encoding='utf-8'),
                      dtype={'k': str}, usecols=['i', 'k', 'v'])
raw['v'] = pd.to_numeric(raw['v'], errors='coerce')
Xik = raw.groupby(['i', 'k'], as_index=False).v.sum()
Xik = Xik[Xik.v >= MIN_VALUE]                                    # <-- value floor (was missing)
M = Xik.pivot(index='i', columns='k', values='v').fillna(0.0)
tot_c = M.values.sum(1, keepdims=True); tot_p = M.values.sum(0, keepdims=True); tot = M.values.sum()
rca = np.divide(M.values / tot_c, tot_p / tot, out=np.zeros_like(M.values), where=(tot_c > 0) & (tot_p > 0))
share = np.divide(M.values, tot_p, out=np.zeros_like(M.values), where=tot_p > 0)
Mb = ((rca >= 1) & (share >= MIN_SHARE)).astype(float)
products = list(M.columns)
world_val = M.values.sum(0)

must = set(HL)
order = np.argsort(-world_val)
keep = [i for i in order[:TOPN]]
kset = set(products[i] for i in keep)
for c in must:
    if c in products and c not in kset:
        keep.append(products.index(c)); kset.add(c)
keep = sorted(set(keep))
codes = [products[i] for i in keep]
Mk = Mb[:, keep]
kp = Mk.sum(0); co = Mk.T @ Mk
n = len(codes)
phi = np.zeros((n, n))
for a in range(n):
    denom = np.maximum(kp, kp[a]); denom[denom == 0] = 1
    phi[a] = co[a] / denom
np.fill_diagonal(phi, 0)
cidx = {c: a for a, c in enumerate(codes)}

# edges: max spanning tree + phi>=threshold, carrying phi + an MST flag
mst = minimum_spanning_tree(csr_matrix(1.0 - phi + 1e-9)).toarray()
edges = {}
for a in range(n):
    for b in range(a + 1, n):
        is_mst = bool(mst[a, b] or mst[b, a])
        if is_mst or phi[a, b] >= PHI_EDGE:
            edges[(a, b)] = {'phi': round(float(phi[a, b]), 3), 'mst': is_mst}

# --- server-side layout: networkx spring on the REAL proximity edges (chain edges excluded so the ore->refined
# canyon is NOT collapsed), seeded + frozen -> identical every load, screenshot-stable. ---
G = nx.Graph()
G.add_nodes_from(range(n))
for (a, b), e in edges.items():
    G.add_edge(a, b, weight=e['phi'])
pos = nx.spring_layout(G, seed=42, k=1.4 / np.sqrt(n), iterations=260, weight='weight')
px = np.array([pos[a][0] for a in range(n)]); py = np.array([pos[a][1] for a in range(n)])
px = (px - px.mean()) / (px.std() + 1e-9) * 460; py = (py - py.mean()) / (py.std() + 1e-9) * 300

pc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'product_codes_HS17_V202601.csv'), dtype={'code': str})
name = dict(zip(pc.code, pc.description))
def short(desc):
    d = str(desc).split(';')[0]; return (d[:52] + '…') if len(d) > 53 else d

# PCI (from productspace.json) -> node "core-ness"; percentile for the gradient/readout
try:
    PS = json.load(open(os.path.join(ROOT, 'out', 'productspace.json'), encoding='utf-8'))
    PCI = PS.get('PCI', {})
except Exception:
    PCI = {}
pci_vals = np.array([PCI.get(c, 0.0) for c in codes])
pci_rank = {c: int(100 * (pci_vals < PCI.get(c, 0.0)).mean()) for c in codes}

nodes = []
maxv = world_val[keep].max()
for a, c in enumerate(codes):
    s, col = sector(c)
    hl = HL.get(c)
    nodes.append({'id': a, 'code': c, 'name': short(name.get(c, c)), 'sector': s, 'color': col,
                  'val': float(world_val[keep][a]), 'r': float(4 + 22 * np.sqrt(world_val[keep][a] / maxv)),
                  'mat': hl[0] if hl else None, 'role': hl[1] if hl else None, 'lab': hl[2] if hl else None,
                  'pci': round(float(PCI.get(c, 0.0)), 2), 'pcp': pci_rank.get(c, 0),
                  'x': round(float(px[a]), 1), 'y': round(float(py[a]), 1)})
links = [{'source': a, 'target': b, 'phi': e['phi'], 'mst': e['mst']} for (a, b), e in edges.items()]
chain_links = [{'source': cidx[o], 'target': cidx[r], 'phi': round(float(phi[cidx[o], cidx[r]]), 3), 'mat': lab}
               for (o, r, lab) in CHAIN_CODES if o in cidx and r in cidx]

# capability (who actually refines) on the material nodes
try:
    cap = json.load(open(os.path.join(ROOT, 'out', 'capability.json'), encoding='utf-8'))
except Exception:
    cap = {}
capkey = {'magnet': 'magnet (NdFeB)'}
for nd in nodes:
    if not nd.get('role'):
        continue
    rows = cap.get(capkey.get(nd['mat'], nd['mat']), [])
    nd['refiners'] = [{'n': r['name'], 'cap': r['cap'], 't': r['type']} for r in rows[:3] if r['cap'] >= 0.03]

# mine->refine capture data (phi distance, PCI gain, per-country density) for the guided/compare modes
try:
    MR = json.load(open(os.path.join(ROOT, 'out', 'mine_refine.json'), encoding='utf-8'))
except Exception:
    MR = {}
# OBSERVED physical downstream (real trade, material-specific HS codes) -- the TRUE chain beyond refined,
# where clean codes exist. Rendered SOLID (vs B's dashed estimate). It stops at the last material-specific
# code: end-products (motors, EVs, chips, cans) are shared across many inputs and are NOT attributable -- a
# stated data wall. Aluminium is the clean showcase: bauxite ore -> alumina -> Al metal -> Al sheet.
# Only codes that (a) are material-specific and (b) exist as product-space NODES can be drawn. That limits
# the observable chain to aluminium & copper; nickel/titanium/tungsten/cobalt/antimony have NO clean
# downstream node (their next stage is shared, non-competitive, or a different ore-branch) -- a real wall.
OBSERVED_DOWN = {'bauxite': ['760110', '760612', '760711'],   # alumina -> Al unwrought -> sheet -> foil
                 'copper':  ['740811', '854411']}             # cathode -> Cu wire -> insulated winding wire
chains = []
for lab, (o, r) in CROSSWALK.items():
    if o not in cidx or r not in cidx:
        continue
    mr = MR.get(lab, {})
    a, b = cidx[o], cidx[r]                                       # proximity under alternative metrics
    coab, ka, kb = float(co[a, b]), float(kp[a]), float(kp[b])
    phi_cos = round(coab / (ka * kb) ** 0.5, 2) if ka * kb > 0 else 0.0
    phi_jac = round(coab / (ka + kb - coab), 2) if (ka + kb - coab) > 0 else 0.0
    observed = [{'id': cidx[c], 'code': c, 'lab': short(name.get(c, c)),
                 'pci': round(float(PCI.get(c, 0.0)), 2)} for c in OBSERVED_DOWN.get(lab, []) if c in cidx]
    chains.append({'mat': lab, 'ore_id': cidx[o], 'refined_id': cidx[r], 'observed': observed,
                   'ore_pci': round(float(PCI.get(o, 0.0)), 2), 'refined_pci': round(float(PCI.get(r, 0.0)), 2),
                   'phi': mr.get('phi_distance'), 'phi_cos': phi_cos, 'phi_jac': phi_jac, 'pci_gain': mr.get('pci_gain'),
                   'refiners': [{'n': x['name'], 'cap': x['cap']} for x in cap.get(lab, [])[:3] if x['cap'] >= 0.03],
                   'miners': {m['c']: {'mine': m['mines'], 'refine': m['refines'], 'density': m['density']}
                              for m in (mr.get('miners') or [])}})

sectors = sorted({(nd['sector'], nd['color']) for nd in nodes}, key=lambda x: x[0])
print(f'network: {n} nodes, {len(links)} edges, {len(chain_links)} chain edges; layout frozen', flush=True)

# per-country RCA>=1 membership + featured presets
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
num2iso = dict(zip(cc.country_code, cc.country_iso2)); num2name = dict(zip(cc.country_code, cc.country_name))
_PREF = {'DE': 'Germany', 'TR': 'Türkiye', 'RU': 'Russia', 'KR': 'South Korea', 'CD': 'DR Congo',
         'US': 'United States', 'GB': 'United Kingdom', 'CZ': 'Czechia', 'VN': 'Viet Nam', 'IR': 'Iran',
         'BO': 'Bolivia', 'BE': 'Belgium'}
_iso_name = {}
for _num, _iso in num2iso.items():
    if not isinstance(_iso, str):
        continue
    _nm = str(num2name.get(_num, _iso))
    if _iso not in _iso_name or ('(' in _iso_name[_iso] and '(' not in _nm):
        _iso_name[_iso] = _nm
def disp(iso): return _PREF.get(iso, _iso_name.get(iso, iso))
FEATURED = ['CD', 'CN', 'CL', 'ID', 'AU', 'US', 'DE', 'JP']
country_nums = list(M.index)
matset = {a for a, nd in enumerate(nodes) if nd['role']}
members, clist = {}, []
for ci, num in enumerate(country_nums):
    iso = num2iso.get(int(num))
    if not iso or not isinstance(iso, str):
        continue
    ids = [a for a in range(n) if Mk[ci, a] > 0]
    if len(ids) < 3:
        continue
    members[iso] = ids
    clist.append({'iso': iso, 'name': disp(iso), 'n': len(ids),
                  'mats': sum(1 for a in ids if a in matset), 'feat': iso in FEATURED})
clist.sort(key=lambda x: x['name'])
print(f'countries: {len(clist)}', flush=True)

# --- B: estimated "next rung" — the capability-adjacent, HIGHER-complexity products just above each
# refined node in the space. This is an ESTIMATE (product-space proximity), not observed downstream trade:
# it answers "if you refine this, what are you nearest to making next?" Full coverage, lower certainty --
# rendered as dashed/estimate edges, and A (observed end-products) will later validate it. ---
PCI_arr = pci_vals
phi_rowsum = phi.sum(1) + 1e-9
iso_by_ci = {ci: num2iso.get(int(num)) for ci, num in enumerate(country_nums)}
def near_countries(p, k=3):
    dens = (Mk @ phi[:, p]) / phi_rowsum[p]          # density of each country's basket to product p
    out = []
    for ci in np.argsort(-dens):
        if Mk[ci, p] > 0:                            # skip countries that already make it competitively
            continue
        iso = iso_by_ci.get(int(ci))
        if not iso or not isinstance(iso, str):
            continue
        out.append({'iso': iso, 'name': disp(iso), 'd': round(float(dens[ci]), 3)})
        if len(out) >= k:
            break
    return out
# 2-hop, sector-filtered climb: keep only industrial "climb" sectors (drops food/ag/textiles/wood + raw ores,
# which is where the co-export artifacts live -- salmon, whisky, plywood, iron ore). hop-1 = this material's
# next rung; hop-2 = the rung beyond it. Still a proximity ESTIMATE, not a verified value chain.
KEEP_SECT = {'Chemicals', 'Plastic & rubber', 'Stone, glass, gems', 'Metals',
             'Machinery & elec.', 'Transport', 'Instruments & misc.'}
def _sect(a): return sector(codes[a])[0]
NOISE_CH = {92, 93, 94, 95, 96, 97}   # music/arms/furniture/toys/misc/art — the "Instruments & misc." tail
def rung_neighbors(src, base_pci, exclude, k):
    cand = [a for a in range(n) if a not in exclude and a not in matset
            and _sect(a) in KEEP_SECT and int(codes[a][:2]) not in NOISE_CH
            and PCI_arr[a] > base_pci and phi[src, a] > 0]
    cand.sort(key=lambda a: -phi[src, a])
    return cand[:k]
def rung_node(a, parent, hop):
    return {'id': a, 'code': codes[a], 'lab': short(name.get(codes[a], codes[a])), 'hop': hop,
            'sect': _sect(a), 'pci': round(float(PCI_arr[a]), 2),
            'dpci': round(float(PCI_arr[a] - PCI_arr[parent]), 2),
            'phi': round(float(phi[parent, a]), 3), 'near': near_countries(a)}
for ch in chains:
    rr = ch['refined_id']; used = {rr} | matset
    h1 = rung_neighbors(rr, PCI_arr[rr], used, 3); used |= set(h1)
    nr = []
    for a in h1:
        h2 = rung_neighbors(a, PCI_arr[a], used, 2); used |= set(h2)
        nd = rung_node(a, rr, 1); nd['next'] = [rung_node(c, a, 2) for c in h2]
        nr.append(nd)
    ch['next_rung'] = nr
print('next-rung (B) 2-hop for ' + str(sum(1 for c in chains if c.get('next_rung'))) + ' chains', flush=True)

# A -- observable-downstream validation of B (from build_avalidate.py)
try:
    AVAL = json.load(open(os.path.join(ROOT, 'out', 'avalidate.json'), encoding='utf-8'))
except Exception:
    AVAL = None

DATA = json.dumps({'nodes': nodes, 'links': links, 'chain_links': chain_links, 'chains': chains,
                   'sectors': [{'name': s, 'color': c} for s, c in sectors], 'year': YEAR,
                   'members': members, 'countries': clist, 'featured': FEATURED, 'aval': AVAL}, ensure_ascii=False)
D3JS = open(os.path.join(ROOT, 'vendor', 'd3.v7.min.js'), encoding='utf-8').read()

HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Product Space</title><script>D3_INLINE</script>
<style>
 *{margin:0;padding:0;box-sizing:border-box} html,body{width:100%;height:100%;overflow:hidden}
 body{background:#0f1216;color:#e8eaed;font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
 svg{position:fixed;top:0;left:0;width:100vw;height:100vh;display:block}
 #hd{position:fixed;top:0;left:0;right:0;padding:14px 20px;z-index:5;pointer-events:none}
 #hd a#back{pointer-events:auto;font-size:12.5px;color:#9aa6b2;text-decoration:none}
 #hd a#back:hover{color:#e8eaed}
 #hd h1{font-size:23px;font-weight:800;letter-spacing:-.3px;margin-top:3px}
 #hd p{font-size:13px;color:#9aa6b2;margin-top:3px;max-width:760px;line-height:1.45}
 #panel{position:fixed;top:14px;right:18px;z-index:6;width:288px;pointer-events:auto}
 .card{background:#161b22;border:1px solid #2b3240;border-radius:9px;padding:11px 13px;margin-bottom:9px}
 .card label{display:block;font-size:10.5px;color:#8a97a5;letter-spacing:.4px;text-transform:uppercase;margin-bottom:5px}
 select,input{width:100%;background:#0f1216;color:#e8eaed;border:1px solid #3a4048;border-radius:6px;
   padding:7px 9px;font-size:13.5px;font-family:inherit}
 .presets{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}
 .presets button{background:#1c2230;color:#c2c8d0;border:1px solid #333c4a;border-radius:20px;
   padding:3px 9px;font-size:11.5px;cursor:pointer}
 .presets button:hover,.presets button.on{background:#2a3446;color:#fff;border-color:#4a5a72}
 #readout{font-size:12.5px;color:#c2c8d0;line-height:1.5}
 #readout b{color:#fff} #readout table{width:100%;border-collapse:collapse;margin-top:6px;font-size:11.5px}
 #readout td{padding:2px 3px;border-bottom:1px solid #232a34} #readout .r{text-align:right;font-variant-numeric:tabular-nums}
 #legend{position:fixed;bottom:34px;left:16px;z-index:5;font-size:11px;color:#aeb6c0;
   display:flex;flex-wrap:wrap;gap:4px 12px;max-width:56%}
 #legend span{display:flex;align-items:center;gap:5px} #legend i{width:10px;height:10px;border-radius:50%;display:inline-block}
 #foot{position:fixed;bottom:12px;left:16px;right:16px;z-index:5;font-size:10.5px;color:#5f6b78;pointer-events:none}
 #foot a{color:#7f8b98;pointer-events:auto}
 #tip{position:fixed;pointer-events:none;background:#1c2128;border:1px solid #30363d;border-radius:7px;
   padding:8px 11px;font-size:12.5px;opacity:0;transition:opacity .1s;z-index:9;max-width:270px}
 #tip b{color:#fff} #tip .s{color:#9aa6b2;font-size:11px}
 .matlabel{font-size:11.5px;font-weight:700;fill:#fff;paint-order:stroke;stroke:#0f1216;stroke-width:3px;pointer-events:none}
 .chip{display:inline-block;background:#20283a;border:1px solid #38445a;border-radius:5px;padding:1px 6px;margin:2px 3px 0 0;font-size:11px}
 @media(max-width:760px){#panel{position:static;width:auto;margin:150px 12px 0}#hd p{max-width:none}#legend{display:none}}
</style></head><body>
<svg id="svg"></svg>
<div id="hd"><a id="back" href="index.html">&lsaquo; Critical Materials Atlas</a>
<h1>The Product Space — the mine ▸ refine climb</h1>
<p>Every dot is a product in world trade; two are linked when the same countries competitively export both. The <b>chain</b> for each critical material — <b style="color:#E69F00">ore ◆</b> in the raw periphery, <b style="color:#CC79A7">refined ●</b> pulled toward the complex core, <b style="color:#009E73">NdFeB magnet ■</b> deepest in — is drawn as a dashed line. Pick a <b>material</b> to trace it, or a <b>country</b> to see what it competitively exports.</p></div>
<div id="panel">
 <div class="card"><label>Trace a material's chain</label>
   <select id="msel"><option value="">— none —</option></select></div>
 <div class="card"><label>Light up a country</label>
   <select id="csel"><option value="">— the whole world —</option></select>
   <div class="presets" id="cpre"></div>
   <select id="vsel" style="margin-top:7px"><option value="">— compare with… —</option></select></div>
 <div class="card"><label>Find a product</label>
   <input id="search" placeholder="product name or HS code…" autocomplete="off"></div>
 <div class="card" id="valcard" style="display:none"></div>
 <div class="card" id="rocard" style="display:none"><div id="readout"></div></div>
</div>
<div id="legend"></div><div id="tip"></div>
<div id="foot"></div>
<script>
const D=DATA_PLACEHOLDER;
const OKA={ore:'#E69F00',refined:'#CC79A7',magnet:'#009E73'};   // Okabe-Ito, CVD-safe roles
const svg=d3.select("#svg"), W=()=>window.innerWidth, H=()=>window.innerHeight;
const g=svg.append("g");
const zoom=d3.zoom().scaleExtent([0.1,10]).on("zoom",e=>g.attr("transform",e.transform));
svg.call(zoom);
const idn=new Map(D.nodes.map(d=>[d.id,d]));
D.links.forEach(l=>{l.s=idn.get(l.source);l.t=idn.get(l.target);});
D.chain_links.forEach(l=>{l.s=idn.get(l.source);l.t=idn.get(l.target);});
function baseFill(d){return d.role?OKA[d.role]:d.color;}
function flag(iso){return (iso&&iso.length===2)?iso.toUpperCase().replace(/./g,c=>String.fromCodePoint(0x1F1E6-65+c.charCodeAt(0))):'';}

// edges: opacity/width by phi (strong links look strong)
const link=g.append("g").selectAll("line").data(D.links).join("line")
  .attr("x1",l=>l.s.x).attr("y1",l=>l.s.y).attr("x2",l=>l.t.x).attr("y2",l=>l.t.y)
  .attr("stroke","#2a3038").attr("stroke-width",l=>0.4+l.phi*1.6).attr("stroke-opacity",l=>0.25+l.phi*0.5);
// chain edges: always drawn, dashed; low phi = a visible canyon
const chain=g.append("g").selectAll("line").data(D.chain_links).join("line")
  .attr("x1",l=>l.s.x).attr("y1",l=>l.s.y).attr("x2",l=>l.t.x).attr("y2",l=>l.t.y)
  .attr("stroke","#7f8b98").attr("stroke-width",1.1).attr("stroke-dasharray","3 4").attr("stroke-opacity",0.5);
// observed physical downstream (A, solid) + estimated next-rung (B, dashed), populated per material
const obsg=g.append("g"), obslab=g.append("g"), nextg=g.append("g"), nextlab=g.append("g");
function clearNext(){ nextg.selectAll("line").remove(); nextlab.selectAll("text").remove();
  obsg.selectAll("line").remove(); obslab.selectAll("text").remove(); }
const node=g.append("g").selectAll("circle").data(D.nodes).join("circle")
  .attr("cx",d=>d.x).attr("cy",d=>d.y).attr("r",d=>d.role?Math.max(d.r,8.5):d.r)
  .attr("fill",baseFill).attr("stroke",d=>d.role?'#fff':'#0f1216').attr("stroke-width",d=>d.role?2.2:0.6)
  .style("cursor","pointer");
const mats=D.nodes.filter(d=>d.role);
const mlab=g.append("g").selectAll("text").data(mats).join("text").attr("class","matlabel")
  .attr("text-anchor","middle").attr("x",d=>d.x).attr("y",d=>d.y-Math.max(d.r,9)-4).text(d=>d.lab);
// three landmark nodes for scale
const big=[...D.nodes].sort((a,b)=>b.val-a.val).slice(0,3);
g.append("g").selectAll("text").data(big).join("text").attr("class","matlabel")
  .style("fill","#7f8b98").style("stroke-width","3px").attr("text-anchor","middle")
  .attr("x",d=>d.x).attr("y",d=>d.y-d.r-3).text(d=>d.name.slice(0,16));

const tip=d3.select("#tip");
node.on("mousemove",(e,d)=>{
  let h=`<b>${d.name}</b><br><span class="s">HS ${d.code} · ${d.sector} · PCI ${d.pci} (top ${100-d.pcp}%)`;
  if(d.lab) h+=` · <b style="color:${OKA[d.role]}">${d.lab.toUpperCase()}</b>`;
  h+='</span>';
  if(d.refiners&&d.refiners.length) h+=`<br><span class="s">actually refined by: ${d.refiners.map(r=>r.n+' '+r.cap.toFixed(2)).join(' · ')}</span>`;
  tip.style("opacity",1).style("left",(e.clientX+14)+"px").style("top",(e.clientY+12)+"px").html(h);
}).on("mouseleave",()=>tip.style("opacity",0));

function fitView(ids){
  const ns=ids?D.nodes.filter(d=>ids.has(d.id)):D.nodes;
  const xs=ns.map(d=>d.x),ys=ns.map(d=>d.y);
  const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys),pad=90;
  const k=Math.min((W()-2*pad)/(x1-x0||1),(H()-200)/(y1-y0||1),ids?4:3.2);
  svg.transition().duration(600).call(zoom.transform,d3.zoomIdentity.translate((W()-k*(x0+x1))/2,(H()-k*(y0+y1))/2+40).scale(k));
}
fitView(); window.addEventListener("resize",()=>fitView());

// ---------- legend + footer ----------
d3.select("#legend").selectAll("span").data(D.sectors).join("span").html(s=>`<i style="background:${s.color}"></i>${s.name}`);
// A-validation card: does B's density actually predict realized downstream capability?
if(D.aval&&D.aval.windows){
  const L=D.aval.windows.long, R=D.aval.windows.recent;
  document.getElementById("valcard").innerHTML=`<label>Does the estimated climb hold up?</label>`+
    `<div style="font-size:11.5px;color:#aeb6c0;line-height:1.5">Does density predict which countries <b>acquired</b> a downstream product (RCA crossed 1) years later? Tested on the HS2002 panel, <b>2002→2024</b> (${L.n_entrants} country-entries). <span style="color:#7f8b98">AUC 0.5 = no skill, 1 = perfect.</span>`+
    `<div style="margin:6px 0 0;padding:5px 7px;background:#152a26;border-radius:5px"><b style="color:#4fd0c0">Capability-driven ✓ AUC ${L.by_tier.cap.auc}</b> <span style="color:#7f8b98">(0.88 in 2016→24)</span><br><span style="color:#8a97a5;font-size:10.5px">specialty alloys & manufactured goods (magnets, solar, ferro-V/W, TiO₂, Ti, Ni powder…) — density predicts it. ${L.by_tier.cap.n_products} products, ${L.by_tier.cap.n_entrants} entries.</span></div>`+
    `<div style="margin:5px 0 0;padding:5px 7px;background:#2a2320;border-radius:5px"><b style="color:#c79a6a">Commodity / energy-sited ✗ AUC ${L.by_tier.com.auc}</b> <span style="color:#7f8b98">(0.72 in 2016→24)</span><br><span style="color:#8a97a5;font-size:10.5px">bulk smelting & ferroalloys (ferro-Si, Al unwrought…) — sited by cheap power & ore, <b>not</b> capability, so density does <b>not</b> predict it. ${L.by_tier.com.n_products} products, ${L.by_tier.com.n_entrants} entries.</span></div>`+
    `<div style="color:#8a97a5;margin-top:6px;font-size:10.5px">The climb is real where capability decides it — and it holds across a 22-yr and an 8-yr window. Batteries (HS2012 code): AUC 0.93, 2017→24. Exploratory. <a href="out/avalidate.json" style="color:#7f8b98">data</a></div></div>`;
  document.getElementById("valcard").style.display="block";
}
document.getElementById("foot").innerHTML=`${D.year} BACI HS17 · M = RCA≥1 & ≥0.1% world share & ≥$500k · edges = max-spanning-tree + φ≥0.55 · dashed grey = ore→refined→magnet chain (drawn even at low φ — the canyon is the point) · <b style="color:#f0b429">solid amber = OBSERVED downstream</b> (real trade, material-specific codes — bauxite→alumina→Al→sheet, copper→wire; stops where end-products go shared) · <b style="color:#2bb3a3">dashed teal = ESTIMATED 2-hop climb</b> (proximity estimate, not a verified chain) · node size = √world exports · REE oxide/metal & HS 850511 magnet are aggregated/illustrative · <a href="methodology.html">methods</a> · <a href="refiners.html">who refines</a>`;

// ---------- material (guided) mode ----------
const msel=d3.select("#msel"), csel=d3.select("#csel"), ro=d3.select("#readout"), rocard=document.getElementById("rocard");
msel.selectAll("option.m").data(D.chains).join("option").attr("class","m").attr("value",d=>d.mat)
  .text(d=>d.mat.charAt(0).toUpperCase()+d.mat.slice(1)+(d.phi!=null?`  (φ ${d.phi})`:''));
function clearHi(){ node.attr("opacity",1).attr("fill",baseFill).attr("stroke",d=>d.role?'#fff':'#0f1216').attr("stroke-width",d=>d.role?2.2:0.6).attr("stroke-dasharray",null);
  link.attr("stroke","#2a3038").attr("stroke-width",l=>0.4+l.phi*1.6).attr("stroke-opacity",l=>0.25+l.phi*0.5);
  chain.attr("stroke","#7f8b98").attr("stroke-width",1.1).attr("stroke-opacity",0.5); mlab.attr("opacity",1); clearNext(); }
// only one mode at a time: clear the OTHER controls (without firing their handlers)
function resetControls(keep){
  if(keep!=='m') d3.select("#msel").property("value","");
  if(keep!=='c'){ d3.select("#csel").property("value",""); d3.select("#vsel").property("value","");
    document.querySelectorAll("#cpre button").forEach(b=>b.classList.remove("on")); }
  if(keep!=='s'){ const s=document.getElementById("search"); if(s) s.value=""; }
}
function showMaterial(mat){
  resetControls('m');
  if(!mat){ clearHi(); rocard.style.display="none"; fitView(); syncURL(); return; }
  const ch=D.chains.find(c=>c.mat===mat); if(!ch){return;}
  const chainIds=new Set([ch.ore_id,ch.refined_id]);
  const nr=ch.next_rung||[];
  const obs=ch.observed||[]; const obsIds=new Set(obs.map(o=>o.id));
  const h1ids=new Set(nr.map(x=>x.id));
  const h2list=[]; nr.forEach(x=>(x.next||[]).forEach(c=>h2list.push(c)));
  const h2ids=new Set(h2list.map(c=>c.id));
  const rungIds=new Set([...h1ids,...h2ids]);
  const visIds=new Set([...chainIds,...obsIds,...rungIds]);
  node.attr("opacity",d=>(chainIds.has(d.id)||obsIds.has(d.id))?1:(h1ids.has(d.id)?0.92:(h2ids.has(d.id)?0.6:0.08)))
      .attr("stroke",d=>obsIds.has(d.id)?'#E69F00':(rungIds.has(d.id)?'#2bb3a3':(d.role?'#fff':'#0f1216')))
      .attr("stroke-width",d=>obsIds.has(d.id)?2.4:(h1ids.has(d.id)?2:(h2ids.has(d.id)?1.2:(d.role?2.2:0.6))))
      .attr("stroke-dasharray",d=>(obsIds.has(d.id)||!rungIds.has(d.id))?null:'2 2');
  link.attr("stroke-opacity",0.04);
  chain.attr("stroke",l=>l.mat===mat?'#fff':'#3a4048').attr("stroke-width",l=>l.mat===mat?2.4:0.8)
       .attr("stroke-opacity",l=>l.mat===mat?0.95:0.15);
  mlab.attr("opacity",d=>chainIds.has(d.id)?1:0.12);
  // estimated 2-hop climb: hop-1 = material's next rung (bright), hop-2 = the rung beyond (fainter)
  clearNext(); const rp=idn.get(ch.refined_id);
  // OBSERVED physical downstream (A) — solid amber, real trade: refined -> obs0 -> obs1 -> ...
  let oprev=rp; const oedges=[];
  obs.forEach(o=>{ oedges.push({s:oprev,t:idn.get(o.id)}); oprev=idn.get(o.id); });
  obsg.selectAll("line").data(oedges).join("line")
    .attr("x1",d=>d.s.x).attr("y1",d=>d.s.y).attr("x2",d=>d.t.x).attr("y2",d=>d.t.y)
    .attr("stroke","#E69F00").attr("stroke-width",2.4).attr("stroke-opacity",0.92);
  obslab.selectAll("text").data(obs).join("text").attr("class","matlabel").style("fill","#f0b429")
    .attr("text-anchor","middle").attr("x",d=>idn.get(d.id).x).attr("y",d=>idn.get(d.id).y-idn.get(d.id).r-3)
    .text(d=>d.lab.slice(0,20));
  const edges=[];
  nr.forEach(x=>{ edges.push({s:rp,t:idn.get(x.id),hop:1}); (x.next||[]).forEach(c=>edges.push({s:idn.get(x.id),t:idn.get(c.id),hop:2})); });
  nextg.selectAll("line").data(edges).join("line")
    .attr("x1",d=>d.s.x).attr("y1",d=>d.s.y).attr("x2",d=>d.t.x).attr("y2",d=>d.t.y)
    .attr("stroke","#2bb3a3").attr("stroke-dasharray",d=>d.hop===1?"2 5":"1 5")
    .attr("stroke-width",d=>d.hop===1?1.5:0.85).attr("stroke-opacity",d=>d.hop===1?0.85:0.45);
  const labs=[...nr.map(x=>({id:x.id,lab:x.lab,hop:1})),...h2list.map(c=>({id:c.id,lab:c.lab,hop:2}))];
  nextlab.selectAll("text").data(labs).join("text").attr("class","matlabel")
    .style("fill",d=>d.hop===1?"#4fd0c0":"#3a8f85").style("font-size",d=>d.hop===1?"11px":"9px")
    .attr("text-anchor","middle").attr("x",d=>idn.get(d.id).x).attr("y",d=>idn.get(d.id).y-idn.get(d.id).r-3)
    .text(d=>d.lab.slice(0,d.hop===1?22:15));
  const rf=ch.refiners.map(r=>`${r.n} ${r.cap.toFixed(2)}`).join(" · ")||"—";
  const nrhtml=nr.length?nr.map(x=>{
      const kids=(x.next||[]).map(c=>`<div style="margin:1px 0 1px 15px;color:#7f8b98">↳ ${c.lab} <span style="color:#6b7580">+${c.dpci} · φ${c.phi}</span></div>`).join('');
      return `<div style="margin-top:5px">⇢ <b style="color:#cfeeea">${x.lab}</b> <span style="color:#8a97a5">+${x.dpci} PCI · φ${x.phi} · near ${x.near.map(c=>flag(c.iso)).join(' ')}</span>${kids}</div>`;
    }).join(''):'<div style="color:#8a97a5">—</div>';
  const obshtml=obs.length?`<div style="margin-top:8px;padding-top:6px;border-top:1px solid #232a34"><b style="color:#f0b429">Observed downstream — real trade ▬</b> <span style="color:#8a97a5">material-specific HS codes; the chain stops where end-products (motors, EVs, cans) become shared &amp; unattributable.</span>`+obs.map(o=>`<div style="margin-top:2px">▬ <b style="color:#f5d79a">${o.lab}</b> <span style="color:#8a97a5">PCI ${o.pci}</span></div>`).join('')+`</div>`:'';
  ro.html(`<b>${mat.charAt(0).toUpperCase()+mat.slice(1)}</b> — the mine→refine jump<br>`+
    `<table><tr><td>proximity φ(ore,refined)</td><td class="r"><b>${ch.phi!=null?ch.phi:'—'}</b></td></tr>`+
    `<tr><td>&nbsp;&nbsp;<span style="color:#8a97a5">robustness: cosine · Jaccard</span></td><td class="r" style="color:#8a97a5">${ch.phi_cos} · ${ch.phi_jac}</td></tr>`+
    `<tr><td>PCI: ore → refined</td><td class="r">${ch.ore_pci} → ${ch.refined_pci}</td></tr>`+
    `<tr><td>complexity gain ΔPCI</td><td class="r"><b>${ch.pci_gain!=null?(ch.pci_gain>0?'+':'')+ch.pci_gain:'—'}</b></td></tr></table>`+
    `<div style="margin-top:6px;color:#9aa6b2">φ near 0 = the ore and its refined form share almost no capabilities — a real jump. Actually refined by: <b style="color:#fff">${rf}</b>.</div>`+
    obshtml+
    `<div style="margin-top:8px;padding-top:6px;border-top:1px solid #232a34"><b style="color:#2bb3a3">Estimated 2-hop climb ⇢</b> <span style="color:#8a97a5">hop&nbsp;1 = this material&rsquo;s next rung; ↳ = the rung beyond. Industrial sectors only — a capability-proximity <i>estimate</i>, not a verified value chain. &ldquo;near&rdquo; = countries closest by density.</span>${nrhtml}</div>`);
  rocard.style.display="block"; fitView(visIds); syncURL();
}
msel.on("change",function(){showMaterial(this.value);});

// ---------- country mode + capture readout ----------
csel.selectAll("option.c").data(D.countries).join("option").attr("class","c").attr("value",d=>d.iso)
  .text(d=>`${d.name} (${d.n})`);
const cpre=d3.select("#cpre");
cpre.selectAll("button").data(D.countries.filter(c=>c.feat)).join("button")
  .text(d=>flag(d.iso)+' '+d.iso).on("click",function(_,d){showCountry(d.iso);});
function showCountry(iso){
  resetControls(iso?'c':null); document.getElementById("search").value="";
  d3.select("#vsel").property("value","");
  document.querySelectorAll("#cpre button").forEach(b=>b.classList.toggle("on",b.textContent.trim().endsWith(iso)));
  csel.property("value",iso||"");
  if(!iso){ clearHi(); rocard.style.display="none"; fitView(); syncURL(); return; }
  clearNext();
  const set=new Set(D.members[iso]||[]);
  node.attr("fill",d=>set.has(d.id)?baseFill(d):"#333a42").attr("opacity",d=>set.has(d.id)?1:0.10)
      .attr("stroke",d=>d.role?(set.has(d.id)?"#fff":"#555"):"#0f1216").attr("stroke-dasharray",null);
  link.attr("stroke-opacity",l=>(set.has(l.source)&&set.has(l.target))?0.5:0.03);
  chain.attr("stroke-opacity",0.3); mlab.attr("opacity",d=>set.has(d.id)?1:0.15);
  const c=D.countries.find(x=>x.iso===iso);
  let rows='';
  for(const ch of D.chains){
    const m=ch.miners[iso];
    const oreRCA=set.has(ch.ore_id), refRCA=set.has(ch.refined_id);
    if(!m && !oreRCA && !refRCA) continue;
    rows+=`<tr><td>${ch.mat}</td><td class="r">${m?m.mine+'%':(oreRCA?'✓':'·')}</td>`+
          `<td class="r">${m&&m.refine?m.refine+'%':(refRCA?'✓':'·')}</td>`+
          `<td class="r">${m?m.density.toFixed(2):'·'}</td></tr>`;
  }
  // per-country validation: did THIS country's density-near downstream products actually materialise 2002->2024?
  const pcv=(D.aval&&D.aval.windows&&D.aval.windows.long&&D.aval.windows.long.per_country)?D.aval.windows.long.per_country[iso]:null;
  let pcHtml='';
  if(pcv&&(pcv.gained.length||pcv.near.length)){
    const g=pcv.gained.map(x=>`<div style="margin:1px 0">✓ <b style="color:#cfeeea">${x.label}</b> <span style="color:#8a97a5">${x.pred?'density-predicted ✓':'surprise (low density)'}</span></div>`).join('');
    const nro=pcv.near.slice(0,5).map(x=>`<div style="margin:1px 0;color:#9aa6b2">◦ ${x.label}</div>`).join('');
    pcHtml=`<div style="margin-top:8px;padding-top:6px;border-top:1px solid #232a34"><b style="color:#4fd0c0">Downstream climbs 2002→2024 <span style="color:#8a97a5;font-weight:400">(A-validation, this country)</span></b>`+
      (pcv.gained.length?`<div style="margin-top:3px;color:#8a97a5;font-size:10.5px">acquired (RCA crossed 1):</div>${g}`:`<div style="color:#8a97a5;font-size:10.5px;margin-top:3px">no new downstream acquisitions in the tracked set.</div>`)+
      (pcv.near.length?`<div style="margin-top:4px;color:#8a97a5;font-size:10.5px">density-near in 2002, still open — its live opportunities:</div>${nro}`:'')+
      `</div>`;
  }
  ro.html(`<b>${c.name}</b> competitively exports <b>${c.n}</b> of ${D.nodes.length} products (${c.mats} are critical-material nodes).`+
    (rows?`<table><tr style="color:#8a97a5"><td>material</td><td class="r">mine</td><td class="r">refine</td><td class="r">density→refined</td></tr>${rows}</table>`+
      `<div style="margin-top:6px;color:#9aa6b2">A miner with low <b>density</b> sits far from being able to refine (DR Congo cobalt ≈ 0.01); a refiner sits in the complex core.</div>`:'')+pcHtml);
  rocard.style.display="block"; fitView(set.size?set:null); syncURL();
}
// compare-with select (overlay two countries)
const vsel=d3.select("#vsel");
vsel.selectAll("option.v").data(D.countries).join("option").attr("class","v").attr("value",d=>d.iso)
  .text(d=>`${d.name} (${d.n})`);
function compareMode(a,b){
  resetControls('c');
  const A=new Set(D.members[a]||[]),B=new Set(D.members[b]||[]);
  node.attr("fill",d=>{const x=A.has(d.id),y=B.has(d.id);return x&&y?'#ffffff':x?'#E69F00':y?'#0072B2':'#333a42';})
      .attr("opacity",d=>(A.has(d.id)||B.has(d.id))?1:0.08).attr("stroke",d=>d.role?'#fff':'#0f1216');
  link.attr("stroke-opacity",0.03); chain.attr("stroke-opacity",0.3);
  mlab.attr("opacity",d=>(A.has(d.id)||B.has(d.id))?1:0.12);
  const ca=D.countries.find(x=>x.iso===a),cb=D.countries.find(x=>x.iso===b);
  let rows='';
  for(const ch of D.chains){ const ma=ch.miners[a],mb=ch.miners[b];
    if(!ma&&!mb&&!A.has(ch.ore_id)&&!A.has(ch.refined_id)&&!B.has(ch.ore_id)&&!B.has(ch.refined_id)) continue;
    rows+=`<tr><td>${ch.mat}</td><td class="r">${ma?ma.density.toFixed(2):'·'}</td><td class="r">${mb?mb.density.toFixed(2):'·'}</td></tr>`; }
  ro.html(`<b style="color:#E69F00">${ca.name}</b> vs <b style="color:#0072B2">${cb.name}</b> — density toward each refined product`+
    (rows?`<table><tr style="color:#8a97a5"><td>material</td><td class="r">${a}</td><td class="r">${b}</td></tr>${rows}</table>`:'')+
    `<div style="margin-top:6px;color:#9aa6b2"><span style="color:#E69F00">amber</span> = only ${ca.name}, <span style="color:#0072B2">blue</span> = only ${cb.name}, white = both. A country with high <b>density</b> toward a refined product can plausibly make it; DR Congo cobalt ≈ 0.01 = stuck at the mine.</div>`);
  rocard.style.display="block"; fitView(new Set([...A,...B])); syncURL();
}
function routeCountry(){ const a=csel.property("value"),b=vsel.property("value");
  if(a&&b) compareMode(a,b); else showCountry(a); }
csel.on("change",routeCountry); vsel.on("change",routeCountry);

// ---------- search ----------
const search=document.getElementById("search");
search.addEventListener("input",function(){
  const q=this.value.trim().toLowerCase();
  resetControls('s'); rocard.style.display="none";
  if(!q){ clearHi(); return; }
  const hit=new Set(D.nodes.filter(d=>d.name.toLowerCase().includes(q)||d.code.includes(q)).map(d=>d.id));
  if(!hit.size){ clearHi(); return; }          // no match -> keep the full graph, don't blank it
  node.attr("fill",baseFill).attr("opacity",d=>hit.has(d.id)?1:0.07)
      .attr("stroke",d=>hit.has(d.id)?'#fff':(d.role?'#fff':'#0f1216')).attr("stroke-width",d=>hit.has(d.id)?2.2:(d.role?2.2:0.6));
  link.attr("stroke-opacity",0.03); chain.attr("stroke-opacity",0.25);
  mlab.attr("opacity",d=>hit.has(d.id)?1:0.12);
  if(hit.size&&hit.size<=10) fitView(hit);
});

// ---------- permalink (?m=cobalt / ?c=CD) ----------
function syncURL(){ const p=new URLSearchParams(); const m=msel.property("value"),c=csel.property("value"),v=vsel.property("value");
  if(m)p.set("m",m); if(c)p.set("c",c); if(c&&v)p.set("v",v);
  history.replaceState(null,"",p.toString()?("?"+p):location.pathname); }
(function initURL(){ const p=new URLSearchParams(location.search);
  if(p.get("m")){ msel.property("value",p.get("m")); showMaterial(p.get("m")); }
  else if(p.get("c")){ csel.property("value",p.get("c")); if(p.get("v"))vsel.property("value",p.get("v")); routeCountry(); } })();
</script></body></html>'''
out = os.path.join(ROOT, 'product-space.html')
open(out, 'w', encoding='utf-8').write(HTML.replace('D3_INLINE', D3JS).replace('DATA_PLACEHOLDER', DATA))
print('WROTE', out)
