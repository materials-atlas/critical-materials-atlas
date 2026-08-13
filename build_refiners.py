"""Build the 'Who actually refines' atlas page (refiners.html) from out/capability_years.json.

A capability map, not an export map: per material, who actually turns ore into refined metal --
scored by fusing the trade feedstock signature (export-control-proof) with BGS/USGS physical output
(catches the domestic-absorbing refiner). Horizontal bars per stage, coloured by capability class
(teal = refiner visible to trade, amber = domestic-absorbing / trade-blind, grey = raw exporter),
with a 2018-2024 year slider showing capability migrating. Includes the downstream NdFeB magnet stage
(trade-only). Matches the atlas chrome (assets/site.css).
"""
import os, json
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
CAP = json.load(open(os.path.join(ROOT, 'out', 'capability_years.json'), encoding='utf-8'))
EXP = json.load(open(os.path.join(ROOT, 'out', 'exposure.json'), encoding='utf-8'))
OPP = json.load(open(os.path.join(ROOT, 'out', 'opportunity.json'), encoding='utf-8'))

STAGES = [('copper', 'Copper', '260300', '740311'), ('nickel', 'Nickel', '260400', '750210'),
          ('cobalt', 'Cobalt', '260500', '282200'), ('tungsten', 'Tungsten', '261100', '810194'),
          ('titanium', 'Titanium', '261400', '810820'), ('antimony', 'Antimony', '261710', '811010'),
          ('bauxite', 'Bauxite → alumina', '260600', '281820'),
          ('magnet (NdFeB)', 'NdFeB magnet (downstream)', '2805.30/2846.90', '850511')]
DATA = json.dumps({'stages': CAP['stages'], 'years': CAP['years'], 'latest': CAP['latest'],
                   'exposure': EXP['materials'], 'exp_year': EXP['year'], 'opportunity': OPP,
                   'order': [{'key': k, 'name': n, 'ore': o, 'ref': r} for k, n, o, r in STAGES]},
                  ensure_ascii=False)

HTML = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Who actually refines — Critical Materials Atlas</title>
<meta name="description" content="A capability map, not an export map: fusing the trade feedstock signature (imports ore, exports refined) with BGS/USGS physical output to show who actually turns ore into refined metal for 7 critical materials plus NdFeB magnets, 2018-2024.">
<meta property="og:title" content="Who actually refines — capability map">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .capgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:20px;margin:1.2rem 0}
 .capcard{border:1px solid var(--line);border-radius:12px;padding:14px 16px 16px;background:var(--bg)}
 .capcard h3{font-size:1rem;margin:0 0 2px;display:flex;justify-content:space-between;align-items:baseline;gap:8px}
 .capcard h3 .hs{font-size:.66rem;color:var(--faint);font-weight:500;letter-spacing:.2px}
 .capcard .lead{font-size:.76rem;color:var(--mut);margin:0 0 8px;min-height:2.1em}
 .capcard .lead b{color:var(--ink)}
 .choke{display:flex;align-items:center;gap:7px;font-size:.72rem;color:var(--mut);margin:0 0 9px;flex-wrap:wrap}
 .choke .pill{font-size:.64rem;font-weight:700;text-transform:uppercase;letter-spacing:.3px;
   padding:2px 7px;border-radius:20px;color:#fff}
 .pill-extreme{background:#b4291f} .pill-high{background:#d1701a} .pill-moderate{background:#c79a1a} .pill-diffuse{background:#8a94a0}
 .choke b{color:var(--ink-soft)}
 .row{display:flex;align-items:center;gap:8px;margin:5px 0;font-size:.8rem}
 .row .who{width:118px;flex:0 0 118px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
 .row .track{flex:1;height:15px;background:var(--bg-soft);border-radius:4px;position:relative;overflow:hidden}
 .row .fill{height:100%;border-radius:4px 3px 3px 4px}
 .row .val{width:34px;flex:0 0 34px;text-align:right;font-variant-numeric:tabular-nums;color:var(--ink-soft);font-weight:600}
 .row .tag{font-size:.64rem;color:var(--mut);white-space:nowrap}
 .cf-refiner{background:#0e8f83} .cf-absorb{background:#e08a1f} .cf-raw{background:#8a94a0}
 .ct-refiner{color:#0b6f66} .ct-absorb{color:#a5641a} .ct-raw{color:#6b7681}
 .controls{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:.4rem 0 .2rem;
   padding:12px 16px;border:1px solid var(--line);border-radius:10px;background:var(--bg-soft)}
 .controls input[type=range]{flex:1;min-width:180px;accent-color:var(--accent)}
 .controls .yr{font-size:1.5rem;font-weight:800;color:var(--navy);font-variant-numeric:tabular-nums;min-width:74px}
 .controls .hint{font-size:.74rem;color:var(--mut)}
 .caplegend{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:.78rem;color:var(--ink-soft);margin:.2rem 0 0}
 .caplegend span{display:flex;align-items:center;gap:6px} .caplegend i{width:12px;height:12px;border-radius:3px;display:inline-block}
 .cand{font-size:.72rem;color:var(--mut);margin:9px 0 0;padding-top:8px;border-top:1px dashed var(--line)}
 .cand span{color:var(--faint)}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="methodology.html">Methodology</a><a href="findings.html">Findings</a>
  <a href="product-space.html" class="hideable">Product space</a><a href="complexity.html" class="hideable">Complexity</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · capability, not exports</div>
  <h1>Who actually refines</h1>
  <p class="deck">The refiner is not the miner &mdash; but the exporter is not always the refiner either. This is a <b>capability map</b>: for each material it fuses two lenses to show who genuinely turns ore into refined metal. The <b>trade feedstock signature</b> (a country that <i>imports ore and exports refined</i> is transforming it &mdash; a fingerprint that survives export controls) plus <b>BGS/USGS physical output</b>, which catches the <i>domestic-absorbing</i> refiner &mdash; a giant like China that refines enormous volumes but consumes them at home, so it never shows up in refined exports.</p>
</div></section>
<article style="max-width:1180px">
  <div class="callout">A country scores as capable if <i>either</i> lens sees it: <code>cap = max(physical share, trade score)</code>. Colour marks the class that matters most &mdash; can the trade data even see it? <span class="ct-refiner"><b>Teal</b></span> = a refiner visible in trade (it exports refined). <span class="ct-absorb"><b>Amber</b></span> = a domestic-absorbing refiner only physical data catches. <span class="ct-raw"><b>Grey</b></span> = a raw exporter (ships ore, no refining). The sub-type on each bar says <i>how</i>: integrated (mines + refines), import-fed (refines imported ore), or mine-to-metal.
  <details class="howto"><summary>How it&rsquo;s measured &amp; caveats</summary>
  <p>From the BACI bilateral matrix, per country &times; material: <code>net_down = (refined_exp &minus; refined_imp)/(refined_exp + refined_imp)</code> (&gt;0 = net exporter of refined), <code>feedstock_import = ore_imp/(ore_imp+ore_exp)</code> (~1 = sources ore by import), and <code>trade_score = refined_world_share &times; max(net_down,0)</code> &mdash; a robust, re-export-penalised, export-control-proof marker. Physical refined share is BGS/USGS from the atlas data. <code>cap = max(physical, trade_score)</code>.</p>
  <p class="howto-src"><b>Caveats:</b> the <b>physical share is a single recent vintage</b>, so the year slider moves the <i>trade</i> signal, not the physical one &mdash; migration is clearest where trade carries the story (e.g. the magnet stage). The <b>NdFeB magnet stage is trade-only</b> (no physical magnet series), so premium magnet makers that net-import magnets (Japan, Germany) are undercounted &mdash; the same trade-blindness, now without a physical rescue. REE feedstock codes (2805.30 / 2846.90) are aggregated. Built by <code>build_feedstock.py</code>; see also the <a href="product-space.html">product-space map</a> and <a href="complexity.html">complexity</a>.</p>
  </details></div>

  <div class="controls">
    <span class="yr" id="yr"></span>
    <input type="range" id="slider" min="0" step="1">
    <span class="hint">drag to watch capability migrate, 2018&rarr;2024</span>
  </div>
  <div class="caplegend">
    <span><i style="background:#0e8f83"></i> refiner (visible in trade)</span>
    <span><i style="background:#e08a1f"></i> domestic-absorbing (physical only)</span>
    <span><i style="background:#8a94a0"></i> raw exporter</span>
  </div>

  <div class="capgrid" id="grid"></div>

  <p class="note">Reading it: the <b>miner and the refiner are usually different countries</b>, and the refiner sits downstream where the value is. The amber bars are the story the export data alone would miss &mdash; China refining copper, alumina and titanium sponge for its own industry, invisible to any trade metric. At the <b>magnet stage</b>, capability collapses onto a single country: watch China climb from 0.39 (2018) to 0.58 (2024) as the rest of the world stays near zero.</p>
  <p class="note" style="color:var(--faint);font-size:.76rem">Method lineage: Hidalgo &amp; Hausmann product space / economic complexity; feedstock-signature capability mapping addresses the export-RCA-&ne;-capability critique (constrain with physical output; read the direction of transformation). Cf. the product-space paper on China&rsquo;s critical minerals (Frontiers Env. Sci. 2023) and the Fitness-Criticality algorithm (Valverde-Carbonell, Pietrobelli &amp; Men&eacute;ndez, Resources Policy 2024).</p>
</article>
<script>
const D=DATA_PLACEHOLDER;
const S=document.getElementById('slider'), YR=document.getElementById('yr'), GRID=document.getElementById('grid');
S.max=D.years.length-1; S.value=D.years.indexOf(D.latest);
function flag(iso){ if(!iso||iso.length!==2) return ''; return iso.toUpperCase().replace(/./g,c=>String.fromCodePoint(0x1F1E6-65+c.charCodeAt(0)))+' '; }
function cls(t){ if(t.startsWith('domestic-absorbing')) return 'absorb'; if(t==='raw exporter'||t==='feedstock exporter') return 'raw'; return 'refiner'; }
function subtype(t){ return t.replace(' refiner','').replace('domestic-absorbing','domestic-absorbing').replace('mine-to-metal','mine→metal'); }
const SCALE=0.9;   // cap is ~world-share; fixed scale so years/materials compare
function render(){
  const yi=+S.value, year=D.years[yi]; YR.textContent=year;
  GRID.innerHTML='';
  for(const st of D.order){
    const rows=(D.stages[st.key]&&D.stages[st.key][year])||[];
    const shown=rows.filter(r=>r.cap>=0.03).slice(0,7);
    const top=shown[0];
    const card=document.createElement('div'); card.className='capcard';
    let lead='';
    if(top){ const basis = top.basis==='both'?'trade + physical confirm it':top.basis.startsWith('physical')?'<b>only physical data sees it</b> (absorbs output)':'trade signature';
      lead=`Top: <b>${flag(top.iso)}${top.name}</b> &mdash; ${basis}.`; }
    else lead='No country clears the capability floor.';
    const ex=D.exposure[st.key]; let choke='';
    if(ex){ const rel=(ex.reliant||[]).slice(0,4).map(r=>flag(r.iso).trim()).join(' ');
      choke=`<div class="choke"><span class="pill pill-${ex.band}">${ex.band} chokepoint</span>`+
        `<span>HHI <b>${ex.hhi.toFixed(2)}</b> · ${flag(ex.top)}<b>${ex.top}</b> ${ex.top_share.toFixed(0)}%`+
        `${rel?` · reliant: ${rel}`:''}</span></div>`; }
    card.innerHTML=`<h3>${st.name}<span class="hs">${st.ore} → ${st.ref}</span></h3><p class="lead">${lead}</p>${choke}`;
    for(const r of shown){
      const c=cls(r.type); const w=Math.max(3,Math.min(100,r.cap/SCALE*100));
      const row=document.createElement('div'); row.className='row';
      row.innerHTML=`<span class="who" title="${r.name}">${flag(r.iso)}${r.name}</span>`+
        `<span class="track"><span class="fill cf-${c}" style="width:${w}%"></span></span>`+
        `<span class="val">${r.cap.toFixed(2)}</span>`+
        `<span class="tag ct-${c}">${subtype(r.type)}</span>`;
      card.appendChild(row);
    }
    const op=D.opportunity[st.key];
    if(op&&op.candidates&&op.candidates.length){
      const cands=op.candidates.slice(0,5).map(c=>flag(c.c).trim()).join(' ');
      const f=document.createElement('p'); f.className='cand';
      f.innerHTML=`<span>closest non-refiners (product-space density → could build it):</span> ${cands}`;
      card.appendChild(f);
    }
    GRID.appendChild(card);
  }
}
S.addEventListener('input',render); render();
</script>
</body></html>'''

out = os.path.join(ROOT, 'refiners.html')
open(out, 'w', encoding='utf-8').write(HTML.replace('DATA_PLACEHOLDER', DATA))
print('WROTE', out)
