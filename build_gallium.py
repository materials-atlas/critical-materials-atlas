#!/usr/bin/env python3
"""
Gallium, followed end to end — one metal, one mass balance, explicit bias bounds.

The depth exercise. Instead of another cross-material index, trace a single metal's supply chain physically,
from host ore to export, and put hard numbers (with bounds) on the atlas's central claim that a by-product
"can't scale to its own price." Gallium is the sharpest case: it is recovered only from the Bayer liquor of
alumina refining (and some zinc circuits), and only where a plant has built the recovery step.

The mass balance (2024, World Mining Data + stated constants):
  world bauxite mined                       ~414 Mt
  x gallium content of bauxite ~50 ppm      -> ~20,700 t of gallium embedded in mined bauxite
  x share processed to alumina (~85%)       -> ~17,600 t of gallium passing through alumina circuits
  actual primary gallium recovered          ~987 t (WMD; other estimates 300-760 t)
  => ~94% of the gallium that flows through the world's alumina refineries is discarded to red mud,
     NOT for want of gallium but for want of recovery capacity. Supply is capped by refinery retrofits
     (multi-year), so no price spike can summon it quickly. That is "can't scale", quantified.

Also handles the trade-data problem specific to gallium: it exports under HS 811292, shared with germanium
(identical unit values); 811292 is a customs catch-all also nominally covering hafnium/indium/niobium/rhenium/vanadium, so "gallium trade" is a bundle -- bounded here.
Public data; constants stated inline. Run: python build_gallium.py
"""
import json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
prod = {r['label']: r for r in json.load(open(os.path.join(ROOT, 'out', 'production.json'), encoding='utf8'))['rows']}
flows = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf8'))
NAMES = flows.get('names', {})

BAUXITE_T = prod['bauxite']['world_tonnes']          # ~414 Mt (WMD 2024)
GALLIUM_T = prod['gallium']['world_tonnes']          # ~987 t (WMD 2024)
GA_TOP = prod['gallium']['wmd_top']; GA_TOP_SHARE = prod['gallium']['wmd_top_share']

# stated constants (with ranges) — the load-bearing assumptions, exposed
PPM = {'low': 30, 'central': 50, 'high': 80}         # gallium in bauxite, ppm (USGS / literature)
ALUMINA_SHARE = 0.85                                  # share of mined bauxite processed to alumina (Bayer)
PROD_EST = {'low': 300, 'central': GALLIUM_T, 'high': GALLIUM_T}  # primary gallium production estimates (t)

def embedded(ppm):
    return BAUXITE_T * ppm / 1e6
def through(ppm):
    return embedded(ppm) * ALUMINA_SHARE

emb = {k: round(embedded(v)) for k, v in PPM.items()}
thr = {k: round(through(v)) for k, v in PPM.items()}
rec_rate = {  # recovery rate = recovered / through-alumina, across ppm x production-estimate bounds
    'central': round(100 * GALLIUM_T / through(PPM['central']), 1),
    'low': round(100 * PROD_EST['low'] / through(PPM['high']), 1),     # least favourable
    'high': round(100 * GALLIUM_T / through(PPM['low']), 1),           # most favourable
}
discard_pct = {
    'central': round(100 * (1 - GALLIUM_T / through(PPM['central'])), 1),
    'low': round(100 * (1 - GALLIUM_T / through(PPM['low'])), 1),
    'high': round(100 * (1 - PROD_EST['low'] / through(PPM['high'])), 1),
}

# trade: gallium importers (revealed demand) + the shared-HS6 bundle
imp = defaultdict(float)
for f in flows['materials']['gallium']:
    imp[f['to']] += f['value']
tot = sum(imp.values())
importers = [{'iso': k, 'name': NAMES.get(k, k), 'share': round(100 * v / tot, 1)}
             for k, v in sorted(imp.items(), key=lambda kv: -kv[1])[:6]]
ge_t = prod.get('germanium', {}).get('world_tonnes')   # 150 t — the co-coded metal

steps = [
    {'label': 'Gallium embedded in mined bauxite', 'tonnes': emb['central'],
     'lo': emb['low'], 'hi': emb['high'], 'note': f"{BAUXITE_T/1e6:.0f} Mt bauxite × ~50 ppm"},
    {'label': 'Passing through alumina refineries', 'tonnes': thr['central'],
     'lo': thr['low'], 'hi': thr['high'], 'note': f"~{int(ALUMINA_SHARE*100)}% of bauxite processed to alumina"},
    {'label': 'Actually recovered as primary gallium', 'tonnes': GALLIUM_T,
     'lo': PROD_EST['low'], 'hi': GALLIUM_T, 'note': f"WMD {GALLIUM_T} t; other estimates 300–760 t"},
    {'label': 'Discarded to red mud (unrecovered)', 'tonnes': thr['central'] - GALLIUM_T,
     'lo': thr['low'] - GALLIUM_T, 'hi': thr['high'] - PROD_EST['low'],
     'note': f"~{discard_pct['central']}% of the gallium that flowed through alumina"},
]

out = {
    'generated': None, 'year': 2024,
    'bauxite_world_mt': round(BAUXITE_T / 1e6),
    'gallium_world_t': GALLIUM_T, 'gallium_top': GA_TOP, 'gallium_top_share': GA_TOP_SHARE,
    'ppm': PPM, 'alumina_share': ALUMINA_SHARE, 'prod_est_t': PROD_EST,
    'embedded_t': emb, 'through_t': thr,
    'recovery_rate_pct': rec_rate, 'discard_pct': discard_pct,
    'steps': steps, 'importers': importers, 'germanium_world_t': ge_t,
    'sources': 'World Mining Data 2026 (bauxite, gallium); USGS/literature (gallium content of bauxite ~30–80 ppm, Bayer recovery); reconciled trade (HS 811292).',
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'gallium.json'), 'w', encoding='utf8'), separators=(',', ':'))
print('wrote out/gallium.json')
print(f"  embedded ~{emb['central']:,} t | through alumina ~{thr['central']:,} t | recovered {GALLIUM_T} t "
      f"| discarded {discard_pct['central']}% | recovery {rec_rate['central']}%")

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gallium, followed end to end — one metal, one mass balance · Critical Materials Atlas</title>
<meta name="description" content="A single-metal deep dive: gallium traced physically from bauxite through alumina refining to recovery and export, with explicit bias bounds. ~94% of the gallium passing through the world's alumina refineries is discarded — supply is capped by refinery retrofits, not price. 'Can't scale', quantified.">
<meta property="og:title" content="Gallium end to end: why 94% is thrown away, and supply can't answer price">
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
 .stat.warn{border-left-color:#c0392b}.stat.warn .v{color:#c0392b}
 .stat .l{font-size:.76rem;color:#5a6b68;margin-top:.15rem;line-height:1.35}
 .step{margin:.5rem 0}
 .step .top{display:flex;justify-content:space-between;align-items:baseline;font-size:.9rem;margin-bottom:.2rem}
 .step .top b{color:#15323a}.step .top .t{font-weight:800;font-variant-numeric:tabular-nums}
 .step .bar{position:relative;background:#eef3f2;border-radius:5px;height:30px;overflow:hidden}
 .step .fill{height:100%;border-radius:5px}
 .step .ci{position:absolute;top:0;bottom:0;background:rgba(21,50,58,.10);border-left:1px dashed #9aa6ad;border-right:1px dashed #9aa6ad}
 .step .note{font-size:.76rem;color:#9aa6ad;margin-top:.12rem}
 table.tidy{width:100%;border-collapse:collapse;font-size:.86rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .keyline{background:#fbf3f2;border:1px solid #f0d9d5;border-left:4px solid #c0392b;border-radius:10px;padding:.9rem 1.1rem;margin:1.2rem 0}
 .keyline b{color:#c0392b}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Deep dive · one metal, followed to the bottom</div>
  <h1>Gallium, end to end</h1>
  <p class="deck">Every other page compares metals. This one follows just <b>one</b> &mdash; physically, from the bauxite it hides in to the chip it ends up in &mdash; and puts hard numbers, with bounds, on the claim the whole atlas rests on: that a by-product <a href="companionality" style="color:#fff;text-decoration:underline">can&rsquo;t scale to its own price</a>. Gallium is where that claim is provable, not asserted.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>The mass balance, and every constant it rests on</summary>
  <p>World bauxite production (<b>World Mining Data 2024</b>) &times; the gallium content of bauxite (<b>~50 ppm</b>, literature range 30&ndash;80) gives the gallium <i>embedded</i> in mined ore. Times the share of bauxite processed to alumina (<b>~85%</b>) gives the gallium <i>passing through</i> alumina refineries &mdash; the only place it is economically recoverable. Against that we set <i>actual</i> primary gallium production (<b>WMD ~987 t</b>; other estimates 300&ndash;760 t, because China, ~99% of supply, does not report). The gap is what&rsquo;s thrown away.</p>
  <p class="howto-src"><b>Bias bounds (shown, not buried):</b> the ppm and production figures are the uncertain terms; every step below carries its low&ndash;high bracket. Gallium production statistics are genuinely contested &mdash; that uncertainty is part of the finding, not smoothed over. Trade caveat: gallium exports under <b>HS 811292</b>, shared with germanium (identical unit values) &mdash; 811292 is a customs catch-all also nominally covering hafnium/indium/niobium/rhenium/vanadium &mdash; so &ldquo;gallium trade&rdquo; is a bundle &mdash; see below. Inputs: <a href="out/production.json">production.json</a> + reconciled trade &rarr; <a href="out/gallium.json">gallium.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <h2 style="margin:1.6rem 0 .3rem">The mass balance — where the gallium goes</h2>
  <p class="muted" style="margin-top:0">From the gallium embedded in world bauxite down to what&rsquo;s actually recovered. Bars to scale; the shaded bracket is the low&ndash;high bound at each step.</p>
  <div id="steps"></div>
  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.6rem 0 .3rem">Why price can&rsquo;t fix it</h2>
  <p>The gallium exists &mdash; tens of thousands of tonnes of it flow through alumina refineries every year. What&rsquo;s missing is <i>recovery capacity</i>: the extraction step is built at only a handful of plants, and adding it means retrofitting a refinery, a multi-year capital project. So when gallium&rsquo;s price <a href="price-squeeze.html">quadrupled</a> after China&rsquo;s 2023 export controls, world supply could not follow &mdash; there was no idle capacity to switch on, and the raw material&rsquo;s economics are set by <i>aluminium</i>, not gallium. This is the difference the atlas keeps drawing between a metal you can mine more of and one you can only <i>recover more of, eventually</i>. Gallium is the cleanest proof: a supply chain that is 94% waste by design, capped upstream by a host it cannot command.</p>

  <p class="howto-src"><b>Does published work agree?</b> Yes &mdash; and this is a check, not a citation for its own sake. Peer-reviewed gallium material-flow studies put Bayer-liquor losses at roughly <b>95&ndash;96%</b> and find that <b>~90% of primary gallium</b> comes from that one Bayer route. This atlas built its <b>~94% discarded</b> figure independently, from bauxite tonnage and recovery bounds, and it lands in the same place. When a number assembled from raw trade and mining data matches the specialist literature it never consulted, the mechanism is real, not an artefact of one method. <span class="muted">One caveat worth stating plainly: gallium <i>can</i> be recovered at much higher rates from <b>new manufacturing scrap</b> (offcuts from making GaAs wafers &mdash; recovery near 27%). That looks like an escape valve, but it isn&rsquo;t a second mine: new scrap is a fixed fraction of gallium <i>already produced and sold</i>, so it scales with demand, not against a shortage. It cannot open a new primary fountain &mdash; the recycling story lives on its own <a href="companionality.html">page</a>, not here.</span></p>

  <h2 style="margin:1.6rem 0 .3rem">And the trade data lies about it</h2>
  <p class="muted" style="margin-top:0">Who imports gallium (revealed demand, 2024). But note the coding problem this metal exposes:</p>
  <table class="tidy" id="imptab"><thead><tr><th>Importer</th><th class="n">share of gallium imports</th></tr></thead><tbody></tbody></table>
  <p class="muted" id="alias" style="margin-top:.5rem"></p>

  <h2 style="margin:1.8rem 0 .3rem">Why one metal, done deep, matters</h2>
  <p>A scorecard across 32 materials shows breadth; a single chain followed to the bottom shows the mechanism is real. Gallium, traced physically, turns every abstract axis of the <a href="synthesis.html">hardest-cases</a> scorecard into a number you can check: <i>can&rsquo;t scale</i> becomes &ldquo;94% discarded, capped by refinery retrofits&rdquo;; <i>concentrated</i> becomes &ldquo;99% from one country that doesn&rsquo;t report&rdquo;; <i>thin market</i> becomes &ldquo;under 1,000 tonnes a year&rdquo;; <i>trade illusion</i> becomes &ldquo;bundled with germanium under one catch-all HS code.&rdquo; The atlas&rsquo;s thesis is not a correlation across a spreadsheet &mdash; here it is one metal&rsquo;s physical reality, with the error bars drawn in.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>World Mining Data 2026 · USGS/literature (Ga in bauxite, Bayer recovery) · reconciled trade · cross-checked against published gallium material-flow studies (Bayer loss ~95%)</div>
  <div class="fineprint">Gallium production statistics are contested (China unreported); constants (ppm, recovery) are literature ranges, shown with bounds. The ~94%-discarded finding is independently reproduced by peer-reviewed gallium MFA work (~95&ndash;96% Bayer-liquor loss).</div>
</div></footer>
<script>
fetch('out/gallium.json').then(r=>r.json()).then(S=>{
  const f=n=>Number(Math.round(n)).toLocaleString();
  document.getElementById('lead').innerHTML='<b>The number:</b> about <b>'+f(S.through_t.central)+' tonnes</b> of gallium pass through the world&rsquo;s alumina refineries each year, embedded in the bauxite. Only <b>~'+S.gallium_world_t+' tonnes</b> are recovered. The other <b>~'+S.discard_pct.central+'%</b> is discarded to red mud &mdash; not because the gallium isn&rsquo;t there, but because the recovery step is built at only a few plants. Supply is capped upstream, by aluminium&rsquo;s economics, not gallium&rsquo;s price.';
  const st=[
    {v:'~'+f(S.through_t.central)+' t',l:'gallium passing through alumina refineries each year'},
    {v:S.gallium_world_t+' t',l:'actually recovered as primary gallium (WMD 2024)'},
    {v:'~'+S.discard_pct.central+'%',l:'of that gallium discarded to red mud — a chain that is mostly waste by design',warn:true},
    {v:S.gallium_top_share+'%',l:'from '+S.gallium_top+' alone, which does not report its output',warn:true},
  ];
  document.getElementById('stats').innerHTML=st.map(s=>'<div class="stat'+(s.warn?' warn':'')+'"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  // steps
  const mx=S.steps[0].hi;
  const cols=['#15323a','#1d4a52','#0e7c74','#c0392b'];
  document.getElementById('steps').innerHTML=S.steps.map((s,i)=>{
    const w=100*s.tonnes/mx, lo=100*s.lo/mx, hi=100*s.hi/mx;
    return '<div class="step"><div class="top"><b>'+s.label+'</b><span class="t">'+f(s.tonnes)+' t</span></div>'+
      '<div class="bar"><div class="fill" style="width:'+Math.max(1,w)+'%;background:'+cols[i]+'"></div>'+
      '<div class="ci" style="left:'+lo+'%;width:'+Math.max(1,hi-lo)+'%" title="bound '+f(s.lo)+'–'+f(s.hi)+' t"></div></div>'+
      '<div class="note">'+s.note+' &middot; range '+f(s.lo)+'–'+f(s.hi)+' t</div></div>';
  }).join('');
  document.getElementById('keyline').innerHTML='<b>Recovery rate: ~'+S.recovery_rate_pct.central+'%</b> (bounds '+S.recovery_rate_pct.low+'–'+S.recovery_rate_pct.high+'%). A supply chain that recovers one part in twenty of its own key metal, and where the other nineteen leave in the tailings, is the definition of a by-product: its output tracks the host, and no price it commands can change that on any short horizon.';
  const tb=document.querySelector('#imptab tbody');
  S.importers.forEach(m=>{const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+m.name+'</b></td><td class="n">'+m.share+'%</td>';tb.appendChild(tr);});
  document.getElementById('alias').innerHTML='<b>The coding problem:</b> gallium is exported under HS&nbsp;811292, a code it shares with <b>germanium</b> (~'+(S.germanium_world_t||150)+' t/yr); 811292 is a customs catch-all (also nominally hafnium, indium, niobium, rhenium, vanadium). Gallium and germanium carry <i>identical</i> unit values here, so any &ldquo;gallium&rdquo; trade figure is a bundle. By mass gallium dominates it, but by value it does not &mdash; which is why this atlas treats gallium&rsquo;s <i>trade</i> numbers as a bounded proxy and leans on <i>production</i> tonnages (above) for the real story.';
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'gallium.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote gallium.html')
