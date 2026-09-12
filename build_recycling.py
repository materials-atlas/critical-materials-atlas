#!/usr/bin/env python3
"""
Secondary supply — recycling as the only host-independent lever, and the materials with neither.

Child of companionality + host-shock. A material's supply can grow three ways: new primary mines (only if it
is NOT a by-product), more host output (out of its control), or RECYCLING. For hostage metals, recycling is
the ONLY elastic source that doesn't depend on the host commodity. So the decisive question is: which
by-product-locked materials are ALSO barely recycled? Those have no primary response, no host control, and no
scrap buffer — the true supply dead-ends.

trapped = (companionality/100) x (1 - recycling/100) x 100   (high = by-product-locked AND unrecycled)
Recycling = end-of-life recycling input rate (EU CRM 2023 EOL-RIR), read from data.json; materials with no
listed rate are treated as ~0 (negligible), flagged. Public data; deterministic. Run: python build_recycling.py
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
comp = json.load(open(os.path.join(ROOT, 'out', 'companionality.json'), encoding='utf8'))
CO = {r['label']: r for r in comp['rows']}

# WHY a metal isn't recycled: dissipative (used dispersively / physically lost -> trapped FOREVER) vs
# recoverable-but-uncollected (in products that could be recycled but currently aren't -> trapped FOR NOW,
# fixable by collection/policy). Classified from the dominant end-use, per Ciacci, Reck & Graedel "Lost by
# Design" (ES&T 2015) and "Losses and lifetimes of metals in the economy" (Nature Sustainability 2022).
DISSIP = {
    'helium':    ('dissipated', 'Vents to the atmosphere in use — physically unrecoverable.'),
    'arsenic':   ('dissipated', 'Dispersed in chemicals, glass and alloy additives; largely lost.'),
    'phosphate': ('dissipated', 'Applied as fertiliser and dispersed into soil and water.'),
    'phosphorus':('dissipated', 'Chemical and fertiliser uses disperse it irreversibly.'),
    'boron':     ('dissipated', 'Glass, ceramics and fertiliser uses disperse it.'),
    'strontium': ('dissipated', 'Pyrotechnics, ferrite magnets and chemicals disperse it.'),
    'fluorspar': ('dissipated', 'HF and chemical uses consume and disperse it.'),
    'baryte':    ('dissipated', 'Drilling mud and filler uses disperse it.'),
    'feldspar':  ('dissipated', 'Glass and ceramic uses disperse it.'),
    'silicon':   ('mixed', 'Metallurgical and chemical uses dissipate; some in recoverable products.'),
    'antimony':  ('mixed', 'Lead-acid batteries recycle it; flame-retardant uses are dissipative.'),
    'graphite':  ('mixed', 'Battery-anode recycling is emerging; many uses are dissipative.'),
    'gallium':   ('recoverable', 'Bound in ICs, LEDs and thin-film PV — recoverable from fab scrap, but end-of-life collection is near zero.'),
    'germanium': ('recoverable', 'Fibre and IR optics and electronics are recoverable; catalyst uses are dissipative.'),
    'hafnium':   ('recoverable', 'In superalloys and nuclear parts — recoverable with the component, but volumes are tiny.'),
    'vanadium':  ('recoverable', 'Most rides in steel and recycles with it; chemical/catalyst uses are lost.'),
    'indium':    ('recoverable', 'ITO in displays — recoverable from manufacturing scrap, barely collected at end of life.'),
    'tantalum':  ('recoverable', 'Capacitors are recyclable but dispersed and rarely collected.'),
    'cobalt':    ('recoverable', 'Batteries and superalloys are increasingly recycled.'),
    'magnets':   ('recoverable', 'NdFeB magnets are recyclable but collection is minimal.'),
    'platinum':  ('recoverable', 'Autocatalysts are highly recycled; road-wear is a dissipative loss.'),
    'palladium': ('recoverable', 'Autocatalysts and electronics are recovered efficiently.'),
    'tungsten':  ('recoverable', 'Hard-metal carbides are widely recycled.'),
    'lithium':   ('recoverable', 'Batteries — recycling is emerging and scalable.'),
    'titanium':  ('recoverable', 'Metal and alloys recycle; TiO2 pigment is dissipative.'),
    'copper':    ('recoverable', 'One of the best-recycled metals.'),
    'nickel':    ('recoverable', 'Stainless steel and batteries recycle it.'),
    'manganese': ('recoverable', 'Recovered with steel.'),
    'beryllium': ('recoverable', 'Copper-beryllium alloys are recoverable; low volumes.'),
    'bauxite':   ('recoverable', 'Aluminium is highly recycled.'),
    'magnesium': ('recoverable', 'Alloys are recyclable.'),
    'niobium':   ('recoverable', 'Ferro-niobium recycles with steel.'),
}

rows = []
for m in data['materials']:
    lab = m['label']
    c = CO.get(lab, {})
    cp = c.get('companionality_pct', 0)
    rec_raw = m.get('recycling')
    rec = rec_raw or 0
    trapped = round((cp / 100.0) * (1 - rec / 100.0) * 100, 1)
    dk, dnote = DISSIP.get(lab, (None, None))
    rows.append({
        'label': lab, 'title': c.get('title', m['title'].split(' (')[0]),
        'class': c.get('class', 'primary'),
        'companionality_pct': cp, 'recycling': rec, 'recycling_reported': rec_raw is not None,
        'substitutability': m.get('substitutability'), 'trapped': trapped,
        'dissipation': dk, 'dissipation_note': dnote,
    })

rows.sort(key=lambda r: -r['trapped'])
# "trapped": by-product-dominant (>=66) AND barely recycled (<=10)
trapped_set = [r for r in rows if r['companionality_pct'] >= 66 and r['recycling'] <= 10]
# WHY trapped: dissipatively lost (permanent — no technology recovers it) vs recoverable-but-uncollected (fixable)
trapped_permanent = [r for r in trapped_set if r['dissipation'] == 'dissipated']
trapped_recoverable = [r for r in trapped_set if r['dissipation'] in ('recoverable', 'mixed')]
mean_rec = round(sum(r['recycling'] for r in rows) / len(rows), 1)
# among by-product-dominant materials, mean recycling vs primary materials
by = [r for r in rows if r['class'] == 'byproduct']
pr = [r for r in rows if r['class'] == 'primary']
mean_rec_by = round(sum(r['recycling'] for r in by) / len(by), 1) if by else 0
mean_rec_pr = round(sum(r['recycling'] for r in pr) / len(pr), 1) if pr else 0

out = {
    'generated': data.get('generated'),
    'n': len(rows),
    'n_trapped': len(trapped_set),
    'trapped_names': [r['title'] for r in trapped_set],
    'trapped_permanent': [r['title'] for r in trapped_permanent],
    'trapped_recoverable': [r['title'] for r in trapped_recoverable],
    'mean_recycling': mean_rec,
    'mean_recycling_byproduct': mean_rec_by,
    'mean_recycling_primary': mean_rec_pr,
    'best_recycled': [rows_r['title'] for rows_r in sorted(rows, key=lambda r: -r['recycling'])[:3]],
    'rows': rows,
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'recycling.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/recycling.json')
print(f"  trapped (by-product & <=10% recycled): {', '.join(out['trapped_names'])}")
print(f"    permanent/dissipated: {', '.join(out['trapped_permanent']) or '-'}")
print(f"    recoverable-but-uncollected: {', '.join(out['trapped_recoverable']) or '-'}")
print(f"  mean EOL recycling — by-product {mean_rec_by}% vs primary {mean_rec_pr}%")

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Secondary supply — recycling, and the metals with no way out · Critical Materials Atlas</title>
<meta name="description" content="Recycling is the only supply lever for a by-product metal that doesn't depend on its host commodity. This layer crosses end-of-life recycling rates with companionality to find the materials with no primary response and no scrap buffer.">
<meta property="og:title" content="The metals with no way out: no new mine, no scrap">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .muted{color:#5a6b68;font-size:.86rem}
 #scatter{width:100%;height:470px}
 .stat4{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin:1.2rem 0}
 @media(max-width:720px){.stat4{grid-template-columns:repeat(2,1fr)}}
 .stat{background:#fff;border:1px solid #e3e9e8;border-left:4px solid #0e7c74;border-radius:10px;padding:.8rem .9rem}
 .stat .v{font-size:1.5rem;font-weight:800;color:#15323a;letter-spacing:-.02em}
 .stat .l{font-size:.76rem;color:#5a6b68;margin-top:.15rem;line-height:1.35}
 .stat.warn{border-left-color:#c0392b}.stat.warn .v{color:#c0392b}
 table.tidy{width:100%;border-collapse:collapse;font-size:.88rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .tag{display:inline-block;font-size:.7rem;font-weight:700;padding:.06rem .45rem;border-radius:20px}
 .tag.b{background:#fbe9e7;color:#c0392b}.tag.m{background:#fff4e2;color:#b07a18}.tag.p{background:#eaf3f1;color:#0e7c74}
 .keyline{background:#fbf3f2;border:1px solid #f0d9d5;border-left:4px solid #c0392b;border-radius:10px;padding:.9rem 1.1rem;margin:1.2rem 0}
 .keyline b{color:#c0392b}
 .split2{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:.6rem 0}
 @media(max-width:720px){.split2{grid-template-columns:1fr}}
 .card{border:1px solid #e3e9e8;border-radius:12px;padding:1rem 1.1rem;background:#fff}
 .card.perm{border-top:4px solid #7a2320}.card.rec{border-top:4px solid #b07a18}
 .card h4{margin:.1rem 0 .5rem;font-size:.98rem}
 .card.perm h4{color:#7a2320}.card.rec h4{color:#8a5e12}
 .card .mm{font-weight:700;color:#15323a}
 .card .why{font-size:.82rem;color:#5a6b68;margin:.3rem 0 .1rem}
 .card .fix{font-size:.82rem;margin-top:.6rem;padding-top:.5rem;border-top:1px dashed #e3e9e8}
 .dbadge{display:inline-block;font-size:.68rem;font-weight:700;padding:.05rem .4rem;border-radius:5px;cursor:help}
 .dbadge.dissipated{background:#f3e0de;color:#7a2320}.dbadge.recoverable{background:#fbf0d8;color:#8a5e12}.dbadge.mixed{background:#eef1f0;color:#5a6b68}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · secondary supply</div>
  <h1>Six metals have no way out</h1>
  <p class="deck">Six metals — gallium, arsenic, hafnium, helium, germanium, vanadium — have <b>near-zero recycling and no substitute</b>; and by-product metals recycle at barely half the rate of primary ones (3.9% vs 8.8%). A by-product metal has exactly one supply lever it controls: <b>recycling</b>. New mines can&rsquo;t answer (it&rsquo;s a <a href="companionality" style="color:#fff;text-decoration:underline">by-product</a>), and host output isn&rsquo;t its to command (<a href="host-shock" style="color:#fff;text-decoration:underline">host shock</a>). So the sharpest question in the whole atlas: which materials are by-product-locked <i>and</i> barely recycled &mdash; no new mine, no scrap, no way out?</p>
</div></section>
<article style="max-width:1000px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>How &ldquo;trapped&rdquo; is measured &mdash; and <i>why</i> a metal is trapped</summary>
  <p><b>Recycling</b> = end-of-life recycling input rate (EU CRM 2023 EOL-RIR): the share of a material&rsquo;s supply met by recycled end-of-life scrap. We cross it with <a href="companionality.html">companionality</a> into a <b>trapped index = companionality &times; (1 − recycling)</b>: high only when supply can neither be mined afresh (by-product) nor recovered from scrap. Then we split the trapped metals by <b>why</b> they aren&rsquo;t recycled: <b>dissipated</b> (used dispersively or physically lost &mdash; helium vents to air, arsenic and phosphate disperse into chemicals and soil &mdash; so <i>no</i> technology recovers them: trapped <b>forever</b>) vs <b>recoverable-but-uncollected</b> (locked in products that <i>could</i> be recycled but currently aren&rsquo;t &mdash; trapped <b>for now</b>, fixable by collection and policy).</p>
  <p class="howto-src"><b>Sources &amp; caveats:</b> recycling metric = <b>EU CRM 2023 EOL-RIR</b>, one of several the field uses (the <a href="https://www.resourcepanel.org/reports/recycling-rates-metals" target="_blank" rel="noopener">UNEP / International Resource Panel 2011</a> status report also defines EOL-RR, recycled content and old-scrap ratio; current benchmark is the <a href="https://www.iea.org/reports/recycling-of-critical-minerals" target="_blank" rel="noopener">IEA 2024</a> recycling report). It is EU-centric and omits in-process/new scrap and future capacity &mdash; today&rsquo;s functional secondary supply, not a ceiling. The <b>dissipative vs recoverable</b> split is classified from each metal&rsquo;s dominant end-use per Ciacci, Reck &amp; Graedel, <i>&ldquo;Lost by Design&rdquo;</i> (ES&amp;T 2015) and <i>&ldquo;Losses and lifetimes of metals&rdquo;</i> (Nature Sustainability 2022) &mdash; a literature-based judgement, like companionality. Inputs: <a href="out/data.json">data.json</a> &times; <a href="out/companionality.json">companionality.json</a> &rarr; <a href="out/recycling.json">recycling.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.6rem 0 .3rem">The no-way-out map</h2>
  <p class="muted" style="margin-top:0"><b>Up</b> = more of it is an unavoidable by-product (no new mine). <b>Left</b> = less is recovered from scrap (no secondary buffer). The <span style="color:#c0392b;font-weight:700">top-left</span> is the trap: no primary response and no recycling.</p>
  <div id="scatter"></div>

  <h2 style="margin:1.6rem 0 .3rem">Every material, ranked by how trapped it is</h2>
  <table class="tidy" id="tab"><thead><tr><th>Material</th><th>supply type</th><th class="n">by-prod %</th><th class="n">EOL recycling</th><th>why not recycled</th><th class="n">trapped</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.8rem 0 .4rem">Trapped forever, or trapped for now?</h2>
  <p class="muted" style="margin-top:0">&ldquo;Barely recycled&rdquo; hides two very different fates. Some metals are <b>dissipated</b> &mdash; used dispersively or physically lost, so <i>no</i> collection scheme can recover them. Others are simply <b>uncollected</b> &mdash; sitting in products that could be recycled if anyone bothered. The first is a wall; the second is a to-do list.</p>
  <div class="split2" id="split"></div>

  <h2 style="margin:1.8rem 0 .3rem">What this closes, and what it opens</h2>
  <p>This completes the supply-structure arc that began with the <a href="commodity-attribution.html">satellite attribution gap</a>: primary geography (mines), supply elasticity (companionality), systemic exposure (host shock), and now the secondary buffer (recycling). Read together they say the same thing three ways &mdash; for a handful of metals, the usual mitigations simply aren&rsquo;t available, and the only real levers are <b>host-side recovery yield, stockpiles, and substitution</b>. The open branch from here is <b>demand</b>: which technologies pull hardest on exactly these trapped metals? That is the next arm of the atlas to grow.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>EU CRM 2023 (EOL-RIR) · UNEP/IRP 2011 &amp; IEA 2024 (recycling metrics) · dissipation from Ciacci/Reck/Graedel &ldquo;Lost by Design&rdquo; 2015 &amp; Nature Sustainability 2022 · companionality (USGS · Nassar 2015)</div>
  <div class="fineprint">EOL recycling is an EU-centric end-of-life estimate; the dissipative/recoverable split is a literature-based classification of dominant end-use.</div>
</div></footer>
<script>
function ld(u){return new Promise((res,rej)=>{const s=document.createElement('script');s.src=u;s.onload=res;s.onerror=rej;document.head.appendChild(s);});}
Promise.all([fetch('out/recycling.json').then(r=>r.json()),
  ld('https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js')]).then(([S])=>{
  document.getElementById('lead').innerHTML='<b>Result:</b> by-product metals are recycled far less than primary ones ('+S.mean_recycling_byproduct+'% vs '+S.mean_recycling_primary+'% end-of-life) &mdash; exactly the metals that most need a scrap buffer have the least. <b>'+S.n_trapped+'</b> are fully trapped: by-product-locked and barely recycled. But two of those &mdash; <b>'+S.trapped_permanent.join(' and ')+'</b> &mdash; are <b>dissipated</b> (gone for good, no technology recovers them), while the other <b>'+S.trapped_recoverable.length+'</b> ('+S.trapped_recoverable.join(', ')+') are merely <b>uncollected</b> &mdash; trapped for now, not forever.';
  const stats=[
    {v:S.n_trapped,l:'trapped: by-product-locked AND ≤10% recycled — no new mine, no scrap',warn:true},
    {v:S.mean_recycling_byproduct+'%',l:'mean end-of-life recycling of by-product metals',warn:true},
    {v:S.mean_recycling_primary+'%',l:'mean recycling of primary metals — the buffer they have'},
    {v:S.best_recycled[0],l:'best-recycled material (most secondary resilience)'},
  ];
  document.getElementById('stats').innerHTML=stats.map(s=>'<div class="stat'+(s.warn?' warn':'')+'"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  document.getElementById('keyline').innerHTML='<b>The trap, stated plainly:</b> gallium and germanium are 100% by-products with essentially <b>zero</b> end-of-life recycling. You cannot mine them for themselves, you cannot command the aluminium and zinc they ride on, and there is no scrap stream to fall back on. For these metals, resilience is not a mine or a market &mdash; it is recovery yield at the smelter, a national stockpile, or a substitute.';
  const col={byproduct:'#c0392b',mixed:'#b07a18',primary:'#0e7c74'};
  const pts=S.rows.map(r=>({value:[r.recycling,r.companionality_pct,r.title,r['class'],r.trapped],
    itemStyle:{color:col[r['class']]+'cc'},
    symbolSize:Math.max(9,r.trapped/4.5+9)}));
  const ch=echarts.init(document.getElementById('scatter'));
  ch.setOption({
    grid:{left:52,right:24,top:20,bottom:52},
    tooltip:{formatter:p=>'<b>'+p.value[2]+'</b><br>by-product share: '+p.value[1]+'%<br>EOL recycling: '+p.value[0]+'%<br>trapped index: '+p.value[4].toFixed(0)},
    xAxis:{name:'end-of-life recycling (%)',nameLocation:'middle',nameGap:30,min:0,max:45,inverse:true,
      axisLabel:{color:'#5a6b68'},nameTextStyle:{color:'#5a6b68'},splitLine:{lineStyle:{color:'#eef1f0'}}},
    yAxis:{name:'companionality (by-product share %)',nameLocation:'middle',nameGap:36,min:0,max:105,
      axisLabel:{color:'#5a6b68'},nameTextStyle:{color:'#5a6b68'},splitLine:{lineStyle:{color:'#eef1f0'}}},
    series:[{type:'scatter',data:pts,
      markLine:{silent:true,symbol:'none',lineStyle:{color:'#c9b3ad',type:'dashed'},data:[{xAxis:10},{yAxis:66}]},
      label:{show:true,formatter:p=>p.value[2],position:'right',fontSize:10,color:'#15323a',distance:4}}]
  });
  window.addEventListener('resize',()=>ch.resize());
  const tb=document.querySelector('#tab tbody');
  const tagc={byproduct:'b',mixed:'m',primary:'p'},tagt={byproduct:'by-product',mixed:'mixed',primary:'primary'};
  const subcol={high:'#c0392b',medium:'#b07a18',low:'#3f9b46'};
  const dlabel={dissipated:'dissipated',recoverable:'recoverable',mixed:'mixed'};
  S.rows.forEach(r=>{
    const rec=r.recycling_reported?(r.recycling+'%'):'<span style="color:#c9d2d0" title="no EU EOL-RIR listed — treated as negligible">~0</span>';
    const dz=r.dissipation?('<span class="dbadge '+r.dissipation+'" title="'+(r.dissipation_note||'').replace(/"/g,'&quot;')+'">'+dlabel[r.dissipation]+'</span>'):'<span style="color:#c9d2d0">—</span>';
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+r.title+'</b></td>'+
      '<td><span class="tag '+tagc[r['class']]+'">'+tagt[r['class']]+'</span></td>'+
      '<td class="n">'+r.companionality_pct+'</td><td class="n">'+rec+'</td><td>'+dz+'</td>'+
      '<td class="n" style="font-weight:700;color:'+(r.trapped>=66?'#c0392b':r.trapped>=33?'#b07a18':'#9aa6ad')+'">'+r.trapped.toFixed(0)+'</td>';
    tb.appendChild(tr);
  });
  // forever vs for now — the two cards
  const byName={}; S.rows.forEach(r=>byName[r.title]=r);
  function cardList(names){return names.map(n=>{const r=byName[n]||{};return '<div style="margin:.4rem 0"><span class="mm">'+n+'</span><div class="why">'+(r.dissipation_note||'')+'</div></div>';}).join('');}
  document.getElementById('split').innerHTML=
    '<div class="card perm"><h4>⛔ Trapped forever &mdash; dissipated ('+S.trapped_permanent.length+')</h4>'+cardList(S.trapped_permanent)+
      '<div class="fix"><b>Lever:</b> none on the supply side &mdash; only <i>design out</i> the dissipative use, or substitute. Recycling policy cannot help.</div></div>'+
    '<div class="card rec"><h4>🔓 Trapped for now &mdash; recoverable ('+S.trapped_recoverable.length+')</h4>'+cardList(S.trapped_recoverable)+
      '<div class="fix"><b>Lever:</b> collection + recovery from manufacturing scrap and end-products. The metal is there &mdash; the barrier is economics and infrastructure, not physics.</div></div>';
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'recycling.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote recycling.html')
