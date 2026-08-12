"""The Product Space as the iconic Hidalgo-Hausmann NETWORK — nodes = products, edges = proximity backbone
(maximum spanning tree + all links above a proximity threshold), colored by sector, sized by world exports,
with the critical-material ore->refined pairs highlighted. Builds a self-contained interactive HTML
(force-directed, zoom/pan/hover) at out/social/product-space.html. Reads the committed BACI HS17 zip.

Run:  python build_ps_network.py [year]
"""
import os, sys, io, zipfile, json
import numpy as np, pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2022
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
TOPN = 600           # keep the graph legible: the 600 products with the largest world exports
PHI_EDGE = 0.55      # add non-MST edges above this proximity (the classic product-space threshold)

# --- sector map: HS2 chapter -> (sector name, colour) ---
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

# --- critical-material ore -> refined pairs to highlight on the map ---
CROSSWALK = {'copper': ('260300', '740311'), 'nickel': ('260400', '750210'), 'cobalt': ('260500', '282200'),
             'tungsten': ('261100', '810194'), 'titanium': ('261400', '810820'), 'antimony': ('261710', '811010'),
             'bauxite': ('260600', '281820')}
# downstream extension: rare-earth midstream -> metal -> NdFeB magnet (HS 850511). This is where the
# real value + Chinese capture live. NOTE: REE HS6 codes are aggregated/dirty (284690 is a catch-all),
# so these three are ILLUSTRATIVE downstream nodes -- they show how far the magnet sits from anything
# raw -- not a clean capability claim. See methodology memory on export-RCA vs. capability.
DOWNSTREAM = {'284690': ('rare earths', 'refined', 'REE oxide'),
              '280530': ('rare earths', 'refined', 'REE metal'),
              '850511': ('magnet', 'magnet', 'NdFeB magnet')}
# unified highlight table: code -> (material, role, display-label)
HL = {}
for _lab, (_o, _r) in CROSSWALK.items():
    HL[_o] = (_lab, 'ore', _lab + ' ore'); HL[_r] = (_lab, 'refined', _lab + ' refined')
HL.update(DOWNSTREAM)

print(f'reading BACI HS17 {YEAR} …', flush=True)
with zipfile.ZipFile(BACI_ZIP) as z:
    raw = pd.read_csv(io.TextIOWrapper(z.open(f'BACI_HS17_Y{YEAR}_V202601.csv'), encoding='utf-8'),
                      dtype={'k': str}, usecols=['i', 'k', 'v'])
raw['v'] = pd.to_numeric(raw['v'], errors='coerce')
Xik = raw.groupby(['i', 'k'], as_index=False).v.sum()
M = Xik.pivot(index='i', columns='k', values='v').fillna(0.0)
# RCA -> binary Mb
tot_c = M.values.sum(1, keepdims=True); tot_p = M.values.sum(0, keepdims=True); tot = M.values.sum()
rca = np.divide(M.values / tot_c, tot_p / tot, where=(tot_c > 0) & (tot_p > 0))
share = np.divide(M.values, tot_p, where=tot_p > 0)
Mb = ((rca >= 1) & (share >= 0.001)).astype(float)
products = list(M.columns)
world_val = M.values.sum(0)                                   # world exports per product

# --- restrict to top-N products by world value (keep all our material codes) ---
must = set(HL)
order = np.argsort(-world_val)
keep = [i for i in order[:TOPN]]
kset = set(products[i] for i in keep)
for c in must:                                                # force-include material codes
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

# --- edges: maximum spanning tree (backbone) + all links with phi >= PHI_EDGE ---
mst = minimum_spanning_tree(csr_matrix(1.0 - phi + 1e-9)).toarray()   # min tree of (1-phi) == max spanning tree of phi
edges = set()
for a in range(n):
    for b in range(a + 1, n):
        if mst[a, b] or mst[b, a] or phi[a, b] >= PHI_EDGE:
            edges.add((a, b))
# node names
pc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'product_codes_HS17_V202601.csv'), dtype={'code': str})
name = dict(zip(pc.code, pc.description))
def short(desc):
    d = str(desc).split(';')[0]; return (d[:52] + '…') if len(d) > 53 else d

nodes = []
maxv = world_val[keep].max()
for a, c in enumerate(codes):
    s, col = sector(c)
    hl = HL.get(c)
    mat = hl[0] if hl else None
    role = hl[1] if hl else None
    lab = hl[2] if hl else None
    nodes.append({'id': a, 'code': c, 'name': short(name.get(c, c)), 'sector': s, 'color': col,
                  'val': float(world_val[keep][a]),
                  'r': float(4 + 22 * np.sqrt(world_val[keep][a] / maxv)),
                  'mat': mat, 'role': role, 'lab': lab})
links = [{'source': a, 'target': b} for (a, b) in edges]
sectors = sorted({(nd['sector'], nd['color']) for nd in nodes}, key=lambda x: x[0])
print(f'network: {n} nodes, {len(links)} edges; {sum(1 for nd in nodes if nd["role"])} material nodes', flush=True)

# --- per-country competitiveness: for each country, which of the kept products it exports with RCA>=1 ---
cc = pd.read_csv(os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv'))
num2iso = dict(zip(cc.country_code, cc.country_iso2)); num2name = dict(zip(cc.country_code, cc.country_name))
country_nums = list(M.index)                       # numeric BACI codes, row order of Mk
matset = {a for a, nd in enumerate(nodes) if nd['role']}
members, cnames, clist = {}, {}, []
for ci, num in enumerate(country_nums):
    iso = num2iso.get(int(num))
    if not iso or not isinstance(iso, str):
        continue
    ids = [a for a in range(n) if Mk[ci, a] > 0]
    if len(ids) < 3:                               # skip tiny/undiversified reporters
        continue
    members[iso] = ids; cnames[iso] = num2name.get(int(num), iso)
    clist.append({'iso': iso, 'name': cnames[iso], 'n': len(ids),
                  'mats': sum(1 for a in ids if a in matset)})
clist.sort(key=lambda x: x['name'])
print(f'countries with a portrait: {len(clist)}', flush=True)

DATA = json.dumps({'nodes': nodes, 'links': links, 'crosswalk': {lab: [o, r] for lab, (o, r) in CROSSWALK.items()},
                   'sectors': [{'name': s, 'color': c} for s, c in sectors], 'year': YEAR,
                   'members': members, 'countries': clist}, ensure_ascii=False)

D3JS = open(os.path.join(ROOT, 'vendor', 'd3.v7.min.js'), encoding='utf-8').read()

HTML = '''<!doctype html><html><head><meta charset="utf-8"><title>The Product Space</title>
<script>D3_INLINE</script>
<style>
 *{margin:0;padding:0;box-sizing:border-box} html,body{width:100%;height:100%;overflow:hidden}
 body{background:#0f1216;color:#e8eaed;font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
 #hd{position:fixed;top:0;left:0;right:0;padding:16px 22px;z-index:5;pointer-events:none}
 #hd a#back{pointer-events:auto;font-size:12.5px;color:#9aa6b2;text-decoration:none;display:inline-block;margin-bottom:6px}
 #hd a#back:hover{color:#e8eaed}
 #hd h1{font-size:26px;font-weight:800;letter-spacing:-.3px}
 #hd p{font-size:14px;color:#9aa6b2;margin-top:4px;max-width:820px}
 #legend{position:fixed;bottom:14px;left:16px;z-index:5;font-size:12px;color:#c2c8d0;
   display:flex;flex-wrap:wrap;gap:6px 14px;max-width:62%}
 #legend span{display:flex;align-items:center;gap:5px}
 #legend i{width:11px;height:11px;border-radius:50%;display:inline-block}
 #tip{position:fixed;pointer-events:none;background:#1c2128;border:1px solid #30363d;border-radius:7px;
   padding:8px 11px;font-size:13px;opacity:0;transition:opacity .1s;z-index:9;max-width:280px}
 #tip b{color:#fff} #tip .s{color:#9aa6b2;font-size:11px}
 .matlabel{font-size:12px;font-weight:700;fill:#fff;paint-order:stroke;stroke:#0f1216;stroke-width:3px}
 #hint{position:fixed;bottom:14px;right:16px;font-size:12px;color:#6b7683;z-index:5}
 #ctrl{position:fixed;top:16px;right:22px;z-index:6;text-align:right;pointer-events:auto}
 #ctrl select{background:#1c2128;color:#e8eaed;border:1px solid #3a4048;border-radius:7px;
   padding:8px 11px;font-size:14px;font-family:inherit;min-width:230px;cursor:pointer}
 #ctrl label{display:block;font-size:11px;color:#9aa6b2;margin-bottom:5px;letter-spacing:.3px;text-transform:uppercase}
 #readout{margin-top:9px;font-size:13px;color:#c2c8d0;max-width:280px;line-height:1.45}
 #readout b{color:#fff} #readout .mat{color:#e0a24a;font-weight:700}
</style></head><body>
<div id="hd"><a id="back" href="index.html">&lsaquo; Critical Materials Atlas</a><h1>The Product Space — where critical materials sit</h1>
<p>Every dot is a product in world trade; two products are linked when the same countries tend to be good at exporting both. Sized by world exports, coloured by sector. <b style="color:#e0a24a">Amber◆</b> = the ORE of a critical material, <b style="color:#9a7cff">violet◆</b> = its REFINED form, <b style="color:#35c39a">green◆</b> = the DOWNSTREAM NdFeB magnet — see how the chain climbs from the raw periphery into the complex core. Scroll to zoom, drag to pan.</p></div>
<div id="ctrl"><label>Light up one country&rsquo;s strengths</label>
<select id="csel"></select><div id="readout"></div></div>
<div id="legend"></div><div id="hint">drag a node · scroll to zoom</div><div id="tip"></div>
<svg id="svg" width="100%" height="100%"></svg>
<script>
const D=DATA_PLACEHOLDER;
const svg=d3.select("#svg"), W=window.innerWidth, H=window.innerHeight;
const g=svg.append("g");
const zoom=d3.zoom().scaleExtent([0.15,8]).on("zoom",e=>g.attr("transform",e.transform));
svg.call(zoom);
// seeded RNG -> the layout is identical on every load (reproducible, like the fixed Atlas map)
let _s=1234567; const lcg=()=>((_s=(_s*1103515245+12345)&0x7fffffff)/0x7fffffff);
const idn=new Map(D.nodes.map(d=>[d.id,d]));
const link=g.append("g").attr("stroke","#2a3038").attr("stroke-width",0.6).selectAll("line")
  .data(D.links).join("line");
const node=g.append("g").selectAll("circle").data(D.nodes).join("circle")
  .attr("r",d=>d.role?Math.max(d.r,9):d.r)
  .attr("fill",d=>d.role==='ore'?'#e0a24a':d.role==='refined'?'#9a7cff':d.role==='magnet'?'#35c39a':d.color)
  .attr("stroke",d=>d.role?'#fff':'#0f1216').attr("stroke-width",d=>d.role?2.2:0.7)
  .style("cursor","pointer")
  .call(d3.drag().on("start",ds).on("drag",dd).on("end",de));
const mats=D.nodes.filter(d=>d.role);
const mlab=g.append("g").selectAll("text").data(mats).join("text")
  .attr("class","matlabel").attr("text-anchor","middle")
  .text(d=>d.lab);
const tip=d3.select("#tip");
node.on("mousemove",(e,d)=>{tip.style("opacity",1).style("left",(e.clientX+14)+"px").style("top",(e.clientY+12)+"px")
    .html(`<b>${d.name}</b><br><span class="s">HS ${d.code} · ${d.sector}${d.lab?' · '+d.lab.toUpperCase():''}</span>`);})
  .on("mouseleave",()=>tip.style("opacity",0));
const sim=d3.forceSimulation(D.nodes).randomSource(lcg)
  .force("link",d3.forceLink(D.links).id(d=>d.id).distance(16).strength(0.35))
  .force("charge",d3.forceManyBody().strength(-55).distanceMax(520).theta(0.85))
  .force("x",d3.forceX(W/2).strength(0.02)).force("y",d3.forceY(H/2).strength(0.02))
  .force("collide",d3.forceCollide().radius(d=>Math.max(d.r,d.role?9:d.r)+2).strength(0.9))
  .on("tick",draw);
function draw(){
  link.attr("x1",l=>l.source.x).attr("y1",l=>l.source.y)
      .attr("x2",l=>l.target.x).attr("y2",l=>l.target.y);
  node.attr("cx",d=>d.x).attr("cy",d=>d.y);
  mlab.attr("x",d=>d.x).attr("y",d=>d.y-Math.max(d.r,9)-4);
}
sim.stop(); for(let i=0;i<520;i++) sim.tick(); draw();     // settle fully, then freeze
function fitView(){
  const xs=D.nodes.map(d=>d.x), ys=D.nodes.map(d=>d.y);
  const x0=Math.min(...xs), x1=Math.max(...xs), y0=Math.min(...ys), y1=Math.max(...ys);
  const pad=70, k=Math.min((W-2*pad)/(x1-x0), (H-140)/(y1-y0), 3.5);
  const tx=(W-k*(x0+x1))/2, ty=(H-k*(y0+y1))/2+30;
  svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity.translate(tx,ty).scale(k));
}
fitView(); window.addEventListener("resize",fitView);
function ds(e,d){if(!e.active)sim.alphaTarget(0.2).restart();d.fx=d.x;d.fy=d.y;}
function dd(e,d){d.fx=e.x;d.fy=e.y;}
function de(e,d){if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null;}
d3.select("#legend").selectAll("span").data(D.sectors).join("span")
  .html(s=>`<i style="background:${s.color}"></i>${s.name}`);

// --- country portrait: light up the products a country exports competitively (RCA>=1), dim the rest ---
function baseFill(d){return d.role==='ore'?'#e0a24a':d.role==='refined'?'#9a7cff':d.role==='magnet'?'#35c39a':d.color;}
const sel=d3.select("#csel"), readout=d3.select("#readout");
sel.append("option").attr("value","").text("—  the whole world  —");
sel.selectAll("option.c").data(D.countries).join("option").attr("class","c")
   .attr("value",d=>d.iso).text(d=>`${d.name}  (${d.n})`);
function applyCountry(iso){
  const set = iso ? new Set(D.members[iso]||[]) : null;
  node.attr("fill",d=> !set ? baseFill(d) : (set.has(d.id)?baseFill(d):"#333a42"))
      .attr("opacity",d=> !set ? 1 : (set.has(d.id)?1:0.12))
      .attr("stroke",d=> d.role ? (!set||set.has(d.id)?"#fff":"#555") : "#0f1216");
  link.attr("stroke","#2a3038")
      .attr("opacity",l=> !set ? 1 : ((set.has(l.source.id)&&set.has(l.target.id))?0.55:0.03));
  mlab.attr("opacity",d=> !set ? 1 : (set.has(d.id)?1:0.2));
  if(!set){ readout.html(""); return; }
  const c=D.countries.find(x=>x.iso===iso);
  const lit=D.nodes.filter(d=>d.role&&set.has(d.id));
  const ores=lit.filter(d=>d.role==='ore').map(d=>d.mat);
  const refs=lit.filter(d=>d.role==='refined').map(d=>d.lab);
  const mags=lit.filter(d=>d.role==='magnet').map(d=>d.lab);
  readout.html(`<b>${c.name}</b> is competitive in <b>${c.n}</b> of ${D.nodes.length} products.`+
    `<br><span class="mat" style="color:#e0a24a">Ore:</span> ${ores.length?ores.join(", "):"—"}`+
    `<br><span class="mat" style="color:#9a7cff">Refined:</span> ${refs.length?refs.join(", "):"—"}`+
    `<br><span class="mat" style="color:#35c39a">Magnet:</span> ${mags.length?mags.join(", "):"—"}`);
}
sel.on("change",function(){applyCountry(this.value);});
</script></body></html>'''
out = os.path.join(ROOT, 'product-space.html')     # canonical, self-contained atlas page (repo root)
open(out, 'w', encoding='utf-8').write(HTML.replace('D3_INLINE', D3JS).replace('DATA_PLACEHOLDER', DATA))
print('WROTE', out)
