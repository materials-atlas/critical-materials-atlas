#!/usr/bin/env python3
"""
Net demand by bloc — stripping out the re-export confound.

The demand-by-bloc page flagged its own weakness: gross imports conflate final consumption with refine-and-
re-export, so China tops tables for metals it merely processes. This fixes that the honest way available in
trade data: NET trade position per bloc = imports - exports. A pure trans-shipment hub imports and re-exports
in equal measure, so its net collapses toward zero; a genuine consumer stays net-positive; a refiner-exporter
goes net-NEGATIVE (revealed as a supplier, not a demander). We also overlay mine-production presence (USGS
shares, from data.json) so a bloc that both produces and net-imports reads as a true consumer.

This removes the RE-EXPORT distortion. It does NOT reach final consumption, and the honest reason is worth
stating precisely, because it is not the reason this page used to give. The old text blamed missing
production tonnes ("open data gives production as shares, not tonnes"); that is now superseded — the
production page added World Mining Data tonnages this session. But two deeper problems remain:

  1. Apparent consumption (production + imports - exports) using MINE tonnage is systematically WRONG for
     by-product metals: gallium/germanium mine "production" is host-country (bauxite, zinc), while the usable
     metal is recovered at refineries elsewhere at <<100% yield. Adding host-geology tonnage to metal trade
     misattributes supply. It is workable for primary Co/Ni, wrong for classic by-products.
  2. Even CORRECT apparent consumption misses DEMAND EMBODIED IN FINISHED GOODS — cobalt in an imported
     battery, gallium in an imported chip — which for critical metals is the larger unobserved channel. Two
     routes at it, and which applies is METAL-SPECIFIC:
       - MRIO / Raw Material Equivalents (EXIOBASE, Eurostat RME): captures ALL tiers but is sector-coarse
         (resolves "electronics", not gallium), so it cannot attribute per metal.
       - BOTTOM-UP material intensity: trade in the metal's dominant product (HS code) x its published
         intensity. We PROTOTYPED this for cobalt (Li-ion batteries HS 8507, BACI 2023) and stress-tested
         it, and it did NOT deliver per-country demand. It cleanly shows a trade-STAGE fact — intermediate
         cobalt is China-bound, finished battery cells are net-imported by the US and EU — but turning that
         into "cobalt demand by country" is a category error: (i) net-export clamping erases China's own
         large domestic battery/cobalt use (trade cannot see domestic consumption); (ii) raw-cobalt HS is
         product-weight of one thin form, not contained metal, so cross-stage magnitude ratios are
         meaningless; (iii) cobalt also rides in imported CARS and electronics, outside the battery code
         (the tier problem). So even cobalt — the cleanest-carrier metal — resists a per-country final-demand
         figure. Bottom-up clarifies WHERE IN THE CHAIN trade sits; it is not a demand measure.
So the honest measures are trade pull (bloc-demand) and net trade (this page), read as STAGE facts. Per-metal
final consumption is not cleanly recoverable from public trade data by any route — MRIO is too coarse,
bottom-up answers a different (stage) question. Public data; deterministic. Run: python build_net_demand.py
"""
import json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = '2024'
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))
dem = json.load(open(os.path.join(ROOT, 'out', 'demand.json'), encoding='utf8'))
comp = json.load(open(os.path.join(ROOT, 'out', 'companionality.json'), encoding='utf8'))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
bloc_demand = json.load(open(os.path.join(ROOT, 'out', 'bloc_demand.json'), encoding='utf8'))
DE = {r['label']: r for r in dem['rows']}
CO = {r['label']: r for r in comp['rows']}
DATA = {m['label']: m for m in data['materials']}
GROSS_TOP = {r['label']: r['top_bloc'] for r in bloc_demand['rows']}

EU27 = {'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT',
        'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE'}
def bloc(iso):
    if iso == 'CN':
        return 'CN'
    if iso in EU27:
        return 'EU'
    if iso in ('US', 'JP', 'KR', 'IN'):
        return iso
    return 'Other'
BLOCS = ['CN', 'EU', 'US', 'JP', 'KR', 'IN', 'Other']

def producers(lab):
    """bloc -> summed mine-production share (USGS) for this material."""
    pr = defaultdict(float)
    for e in (DATA.get(lab, {}).get('mined') or []):
        pr[bloc(e.get('c'))] += (e.get('v') or 0)
    return {b: round(pr[b], 0) for b in BLOCS if pr[b] >= 5}

rows = []
key_labels = set(bloc_demand.get('key_metals', []))
for lab, fl in flows['materials'].items():
    de = DE.get(lab)
    imp = defaultdict(float); exp = defaultdict(float)
    for f in fl:
        imp[bloc(f['to'])] += f['value']
        exp[bloc(f['from'])] += f['value']
    net = {b: imp[b] - exp[b] for b in BLOCS}
    net_import = {b: v for b, v in net.items() if v > 0}
    tot_net_pos = sum(net_import.values())
    net_top = max(BLOCS, key=lambda b: net[b])
    gross_top = GROSS_TOP.get(lab)
    prod = producers(lab)
    rows.append({
        'label': lab, 'title': CO.get(lab, {}).get('title', de['title'] if de else lab),
        'squeeze': de['squeeze'] if de else 0,
        'driver_tech': (de['sectors'][0] if de and de.get('sectors') else None),
        'net': {b: round(net[b]) for b in BLOCS},
        'net_share': {b: (round(100 * net_import.get(b, 0) / tot_net_pos, 1) if tot_net_pos else 0) for b in BLOCS},
        'net_top': net_top, 'gross_top': gross_top,
        'flipped': (gross_top is not None and gross_top != net_top),
        'producers': prod,
        'is_key': lab in key_labels,
    })

# blocs whose gross-vs-net picture changes most = the re-export reveal
flips = [r for r in rows if r['flipped'] and r['is_key']]
# net-demand ranking across key metals
net_pull = defaultdict(float)
for r in rows:
    if not r['is_key']:
        continue
    for b in BLOCS:
        if r['net'][b] > 0:
            net_pull[b] += r['net'][b]
net_rank = sorted(([b, round(v)] for b, v in net_pull.items()), key=lambda kv: -kv[1])

# China specifically: for how many key metals is it a NET EXPORTER (supplier, not demander)?
cn_net_supplier = [r['title'] for r in rows if r['is_key'] and r['net']['CN'] < 0]

rows.sort(key=lambda r: -r['squeeze'])
out = {
    'generated': dem.get('generated'), 'year': YEAR, 'blocs': BLOCS,
    'n': len(rows),
    'rows': rows,
    'key_metals': sorted(key_labels),
    'n_flipped': len(flips),
    'flipped_names': [r['title'] for r in flips],
    'net_rank': net_rank,
    'cn_net_supplier': cn_net_supplier,
    'caveat': 'Net trade = imports - exports (value); removes re-export hubs but is not consumption. Two '
              'gaps remain: apparent consumption using mine tonnage misattributes by-products (metal '
              'recovered far from where the host is mined), and demand embodied in imported finished goods '
              '(gallium in a chip) is unobservable per metal without a material-footprint/RME model, which '
              'public MRIO resolves only at sector level (electronics, not gallium).',
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'net_demand.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/net_demand.json')
print('  net-demand rank (key metals):', ', '.join(f"{b} {round(v/1e9,1)}B" for b, v in net_rank))
print(f"  gross->net top-bloc FLIPPED for: {', '.join(out['flipped_names']) or 'none'}")
print(f"  China is a NET SUPPLIER (net exporter) of: {', '.join(cn_net_supplier) or 'none'}")

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Net demand by bloc — stripping out the re-exports · Critical Materials Atlas</title>
<meta name="description" content="The demand-by-bloc page conflated consumption with re-export. This nets it out: imports minus exports per bloc, so trans-shipment hubs collapse and refiner-exporters like China are revealed as net suppliers, not demanders, of the metals they process.">
<meta property="og:title" content="Net demand by bloc: who really pulls the metal once re-exports are removed">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .muted{color:#5a6b68;font-size:.86rem}
 .stat4{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin:1.2rem 0}
 @media(max-width:720px){.stat4{grid-template-columns:repeat(2,1fr)}}
 .stat{background:#fff;border:1px solid #e3e9e8;border-left:4px solid #0e7c74;border-radius:10px;padding:.8rem .9rem}
 .stat .v{font-size:1.4rem;font-weight:800;color:#15323a;letter-spacing:-.02em}
 .stat .l{font-size:.76rem;color:#5a6b68;margin-top:.15rem;line-height:1.35}
 .legend{display:flex;flex-wrap:wrap;gap:.8rem;font-size:.78rem;color:#5a6b68;margin:.5rem 0}
 .legend span b{display:inline-block;width:.7rem;height:.7rem;border-radius:2px;margin-right:.3rem;vertical-align:middle}
 .mrow{margin:.7rem 0}
 .mrow .top{font-size:.86rem;margin-bottom:.2rem}
 .mrow .top b{color:#15323a}.mrow .top .drv{color:#5a6b68;font-size:.78rem}
 .dbar{position:relative;height:24px;background:linear-gradient(90deg,#fbeceb 0 50%,#eaf3f1 50% 100%);border-radius:5px}
 .dbar .mid{position:absolute;left:50%;top:-2px;bottom:-2px;width:1px;background:#c9d2d0}
 .dbar i{position:absolute;top:3px;height:18px;border-radius:3px;display:flex;align-items:center;font-size:.66rem;color:#fff;font-weight:600;padding:0 .25rem;overflow:hidden;white-space:nowrap}
 .flip{font-size:.76rem;color:#b07a18;margin-top:.15rem}
 table.tidy{width:100%;border-collapse:collapse;font-size:.86rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .keyline{background:#f2f6f5;border:1px solid #d9e6e3;border-left:4px solid #0e7c74;border-radius:10px;padding:.9rem 1.1rem;margin:1.2rem 0}
 .keyline b{color:#0e7c74}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · demand · net trade</div>
  <h1>Who really pulls the metal</h1>
  <p class="deck">The <a href="bloc-demand.html" style="color:#fff;text-decoration:underline">demand-by-bloc</a> page admitted its flaw: gross imports count the metal China buys to refine and ship straight back out. So net it. Imports <i>minus</i> exports collapses the trans-shipment hubs and reveals the refiner-exporters for what they are &mdash; net <b>suppliers</b>, not demanders, of the very metals they dominate.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>Net trade, and why it still isn't full apparent consumption</summary>
  <p>For each material and bloc: <b>net = imports − exports</b> (value, <span id="yr"></span>). A pure re-export hub imports and exports in equal measure, so its net &rarr; 0; a genuine consumer stays net-positive; a refiner-exporter goes net-<i>negative</i>. We overlay <b>mine-production presence</b> (USGS shares) so a bloc that both produces and net-imports reads as a true consumer.</p>
  <p class="howto-src"><b>Honest limit &mdash; and it is not the one this page used to claim.</b> Net <i>trade</i> is not final consumption, but the reason is no longer &ldquo;we lack production tonnes&rdquo; (the <a href="production.html">production page</a> added World Mining Data tonnages). Two real reasons remain. <b>Apparent consumption breaks for by-products:</b> gallium/germanium mine tonnage is host-country (bauxite, zinc), while the usable metal is recovered elsewhere &mdash; adding it to trade misattributes supply. And <b>even correct apparent consumption misses demand embodied in finished goods</b> (gallium in an imported chip), which for critical metals is the bigger channel; capturing it needs <b>Raw Material Equivalents</b> via a multi-region input-output model (EXIOBASE, Eurostat RME), and public MRIO resolves &ldquo;electronics&rdquo;, not gallium. So per-metal consumption is not observable in open data; netting is the honest ceiling. Inputs: flows × <a href="out/bloc_demand.json">bloc_demand.json</a> × <a href="out/data.json">data.json</a> &rarr; <a href="out/net_demand.json">net_demand.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.6rem 0 .3rem">Net trade position by bloc &mdash; demand right, supply left</h2>
  <div class="legend" id="legend"></div>
  <div id="mlist"></div>

  <h2 style="margin:1.8rem 0 .3rem">Net-demand ranking &mdash; who pulls most once re-exports are removed</h2>
  <table class="tidy" id="ntab"><thead><tr><th>Bloc</th><th class="n">net import pull, key metals</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.8rem 0 .3rem">Where the demand arm lands</h2>
  <p>Netting out re-exports is the correction the whole demand arm was building toward: it separates the countries that <i>use</i> a metal from the ones that merely <i>move</i> it. The result sharpens the strategic picture &mdash; the West and the East-Asian manufacturers are the net pullers of the squeezed metals, while the dominant processor is, in net terms, their supplier. <b>What it is not, stated plainly:</b> this is a re-export correction, not a consumption model. Two things sit beyond it, and neither is closed by more trade data. Full apparent consumption would need <i>refined-form</i> production by country &mdash; mine tonnage misattributes by-products like gallium, whose usable metal is recovered far from where its host is dug. And final consumption proper would need to trace the metal <i>embodied in finished goods</i> (cobalt in an imported battery). We tried. A full <b>material-footprint</b> model (Raw Material Equivalents via a multi-region input-output table) captures every tier but is sector-coarse &mdash; it sees &ldquo;electronics&rdquo;, not gallium. And a <b>bottom-up</b> estimate (product trade &times; metal intensity), which we prototyped for cobalt on battery trade, turned out to answer a <i>different</i> question: it cleanly shows a trade-<b>stage</b> fact &mdash; intermediate cobalt is China-bound, finished cells are net-imported by the US and EU &mdash; but calling that &ldquo;cobalt demand by country&rdquo; is a category error, because net-export clamping erases China&rsquo;s own large use, product-weight intermediates don&rsquo;t convert to contained metal, and cobalt also rides in imported cars and electronics outside the battery code. So even cobalt resists a per-country final-demand figure. This page reads trade pull as a <b>stage</b> fact and names what sits beyond it, rather than dressing net trade as consumption.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>Reconciled net trade (imports − exports) × USGS mine-production shares</div>
  <div class="fineprint">Net trade removes re-export hubs but is not consumption: apparent consumption misattributes by-products via mine tonnage, and demand embodied in finished goods needs a material-footprint/RME model that public MRIO resolves only by sector.</div>
</div></footer>
<script>
fetch('out/net_demand.json').then(r=>r.json()).then(S=>{
  const f=n=>Number(n).toLocaleString();
  const COL={CN:'#c0392b',EU:'#2b6fb0',US:'#15323a',JP:'#7d5fb0',KR:'#2f8f6b',IN:'#d98324',Other:'#c2ccca'};
  const NAME={CN:'China',EU:'EU',US:'US',JP:'Japan',KR:'Korea',IN:'India',Other:'Other'};
  document.getElementById('yr').textContent=S.year;
  const key=S.rows.filter(r=>r.is_key);
  document.getElementById('lead').innerHTML='<b>Result:</b> netting out re-exports splits the picture in two. For <b>'+S.n_flipped+'</b> key metals the biggest <i>net</i> puller differs from the biggest gross importer, and China is a net <b>supplier</b> (net exporter) of <b>'+S.cn_net_supplier.length+'</b> of the squeezed metals it is said to &ldquo;dominate demand&rdquo; for &mdash; it exports the refined output it imported as ore. China still tops the net table only because it net-imports raw <i>ores</i> to process; the <i>finished</i> squeezed metals are pulled by the manufacturers &mdash; the EU, US, Japan and Korea.';
  document.getElementById('keyline').innerHTML='<b>The correction:</b> a country can top the import table and still be a net exporter &mdash; that is a processor, not a consumer. Netting imports against exports is the cheapest available proxy for &ldquo;who actually uses this,&rdquo; and it flips the reading for the metals where one bloc refines for the world. It is a re-export correction, not a consumption model &mdash; demand embodied in finished goods stays beyond what per-metal trade data can see.';
  const nr=S.net_rank;
  const stats=[
    {v:NAME[nr[0][0]],l:'largest NET importer of the key squeezed metals (true demand pull)'},
    {v:S.n_flipped,l:'key metals where net top-puller ≠ gross top-importer (re-export reveal)'},
    {v:S.cn_net_supplier.length,l:'squeezed metals for which China is a net SUPPLIER, not a demander'},
    {v:key.length,l:'key metals analysed'},
  ];
  document.getElementById('stats').innerHTML=stats.map(s=>'<div class="stat"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  document.getElementById('legend').innerHTML=S.blocs.map(b=>'<span><b style="background:'+COL[b]+'"></b>'+NAME[b]+'</span>').join('')+'<span style="color:#9aa6ad">◆ = also a mine producer</span>';
  // per-metal diverging net bars (scaled to each metal's max |net|)
  document.getElementById('mlist').innerHTML=key.map(r=>{
    const vals=S.blocs.map(b=>({b,v:r.net[b]}));
    const mx=Math.max.apply(null,vals.map(x=>Math.abs(x.v)),1);
    // stack net-importers to the right, net-exporters to the left, largest nearest centre
    let ri=50, le=50, seg='';
    vals.filter(x=>x.v>0).sort((a,b)=>b.v-a.v).forEach(x=>{const w=Math.abs(x.v)/mx*50;seg+='<i style="left:'+ri+'%;width:'+w+'%;background:'+COL[x.b]+'" title="'+NAME[x.b]+' net +€'+f(Math.round(x.v/1e6))+'M">'+(w>7?NAME[x.b]:'')+'</i>';ri+=w;});
    vals.filter(x=>x.v<0).sort((a,b)=>a.v-b.v).forEach(x=>{const w=Math.abs(x.v)/mx*50;le-=w;seg+='<i style="left:'+le+'%;width:'+w+'%;background:'+COL[x.b]+';opacity:.55" title="'+NAME[x.b]+' net −€'+f(Math.round(-x.v/1e6))+'M (supplier)">'+(w>7?NAME[x.b]:'')+'</i>';});
    const prod=Object.keys(r.producers||{}).map(b=>NAME[b]+' &#9670;').join(' ');
    return '<div class="mrow"><div class="top"><b>'+r.title+'</b> <span class="drv">'+(r.driver_tech||'')+' &middot; net demand: '+NAME[r.net_top]+(prod?' &middot; mined in: '+prod:'')+'</span></div>'+
      '<div class="dbar"><div class="mid"></div>'+seg+'</div>'+
      (r.flipped?'<div class="flip">↳ gross importer was '+NAME[r.gross_top]+', but net demand leads with '+NAME[r.net_top]+' once re-exports are removed</div>':'')+'</div>';
  }).join('');
  const tb=document.querySelector('#ntab tbody');
  nr.forEach(([b,v])=>{const tr=document.createElement('tr');
    tr.innerHTML='<td><b style="color:'+COL[b]+'">'+NAME[b]+'</b></td><td class="n">&euro;'+f(Math.round(v/1e6))+'M</td>';
    tb.appendChild(tr);});
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'net-demand.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote net-demand.html')
