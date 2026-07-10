#!/usr/bin/env python3
"""
Demand arm — where the pull comes from, and the squeeze when it meets supply that can't respond.

The atlas has been supply-side throughout. This opens the demand side: for each material, the principal
end-use sectors, the share of demand tied to clean-energy / electrification technology, and a forward
demand-growth outlook to ~2040 (grounded in IEA Global Critical Minerals Outlook 2024 + USGS end-use).

Then the synthesis that makes the demand arm worth building here: cross projected demand growth with the
supply-structure arm's companionality. Two very different pressures fall out —
  * demand-driven (bottom-right): surging demand, but supply CAN respond (lithium, graphite) — a speed/
    geography problem, solvable with mines and money;
  * structural squeeze (top-right): surging demand AND by-product-locked supply that can't scale to its own
    price (gallium, germanium, cobalt, rare-earth magnets) — the genuinely hard cases.
squeeze = (min(demand_growth,8)/8) x (companionality/100) x 100. Public data; deterministic.
Run: python build_demand.py
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
comp = json.load(open(os.path.join(ROOT, 'out', 'companionality.json'), encoding='utf8'))
CO = {r['label']: r for r in comp['rows']}
TITLE = {m['label']: CO.get(m['label'], {}).get('title', m['title'].split(' (')[0]) for m in data['materials']}

# label -> (sectors, clean_energy_pct, demand_growth_2040 multiple, outlook)
# curated from IEA Global Critical Minerals Outlook 2024 (APS ~2040 vs today) + USGS 2024 end-uses;
# cross-checked against an independent LLM compilation (Codex). Round figures for a fuzzy forward quantity.
DEM = {
    'lithium':   (['EV & grid batteries', 'ceramics/glass'], 85, 8.0, 'very high'),
    'graphite':  (['EV battery anodes', 'steel recarburising', 'refractories'], 60, 4.5, 'very high'),
    'magnets':   (['EV traction motors', 'wind turbines', 'electronics'], 55, 3.5, 'high'),
    'cobalt':    (['EV batteries', 'superalloys', 'catalysts'], 45, 2.5, 'high'),
    'gallium':   (['semiconductors (GaN/GaAs)', 'LEDs', 'solar & radar'], 40, 2.5, 'high'),
    'silicon':   (['solar PV (polysilicon)', 'semiconductors', 'Al alloys'], 35, 2.2, 'high'),
    'nickel':    (['stainless steel', 'EV batteries', 'alloys'], 20, 2.0, 'high'),
    'germanium': (['fibre optics', 'IR optics', 'solar & electronics'], 25, 2.0, 'high'),
    'vanadium':  (['steel alloying', 'redox-flow grid batteries'], 15, 2.0, 'high'),
    'copper':    (['electrical wiring & grid', 'EVs', 'construction'], 25, 1.7, 'moderate'),
    'bauxite':   (['aluminium — transport, grid, packaging'], 15, 1.9, 'moderate'),
    'platinum':  (['autocatalysts', 'H2 electrolysers/fuel cells'], 25, 1.9, 'moderate'),
    'fluorspar': (['HF & refrigerants', 'Li-ion electrolyte (LiPF6)', 'Al/steel flux'], 20, 1.8, 'moderate'),
    'antimony':  (['flame retardants', 'PV glass clarifier', 'batteries/defence'], 20, 1.8, 'moderate'),
    'boron':     (['borosilicate glass', 'NdFeB magnet binder', 'fertiliser'], 25, 1.8, 'moderate'),
    'niobium':   (['HSLA steel microalloying', 'superalloys'], 10, 1.8, 'moderate'),
    'magnesium': (['aluminium alloys', 'auto lightweighting', 'die-casting'], 15, 1.8, 'moderate'),
    'manganese': (['steel', 'EV batteries (NMC/LMFP)'], 12, 1.7, 'moderate'),
    'titanium':  (['aerospace alloys', 'TiO2 pigment', 'medical'], 10, 1.7, 'moderate'),
    'tantalum':  (['capacitors (electronics)', 'superalloys', 'medical'], 15, 1.7, 'moderate'),
    'tungsten':  (['cemented-carbide tooling', 'alloys', 'electronics'], 10, 1.6, 'moderate'),
    'helium':    (['MRI/cryogenics', 'semiconductors', 'fibre & aerospace'], 10, 1.6, 'moderate'),
    'hafnium':   (['jet-engine superalloys', 'high-k semiconductors', 'nuclear'], 10, 1.7, 'moderate'),
    'beryllium': (['defence/aerospace alloys', 'electronics', 'telecom'], 5, 1.4, 'moderate'),
    'phosphate': (['fertiliser', 'LFP batteries'], 8, 1.4, 'moderate'),
    'phosphorus':(['fertiliser', 'chemicals', 'LFP'], 8, 1.4, 'moderate'),
    'strontium': (['ferrite magnets', 'glass', 'pyrotechnics'], 15, 1.4, 'low'),
    'arsenic':   (['GaAs semiconductors', 'alloys', 'wood preserv. (declining)'], 15, 1.2, 'low'),
    'feldspar':  (['glass', 'ceramics'], 2, 1.2, 'low'),
    'baryte':    (['oil & gas drilling mud', 'chemicals'], 2, 1.1, 'low'),
    'cokingcoal':(['steelmaking (blast furnace)'], 0, 0.8, 'low'),
}

def outlook_rank(o): return {'very high': 3, 'high': 2, 'moderate': 1, 'low': 0}[o]

rows = []
for m in data['materials']:
    lab = m['label']
    if lab not in DEM:
        continue
    sectors, ce, g, outlook = DEM[lab]
    c = CO.get(lab, {})
    cp = c.get('companionality_pct', 0)
    squeeze = round((min(g, 8.0) / 8.0) * (cp / 100.0) * 100, 1)
    rows.append({
        'label': lab, 'title': TITLE.get(lab, lab),
        'sectors': sectors, 'clean_energy_pct': ce, 'demand_growth_2040': g, 'outlook': outlook,
        'companionality_pct': cp, 'class': c.get('class', 'primary'),
        'value_eur': m.get('total_eur'), 'squeeze': squeeze,
    })

rows.sort(key=lambda r: (-r['squeeze'], -r['demand_growth_2040']))
# structural squeeze = high demand growth (>=2x) AND by-product-locked (companionality >=66)
squeeze_set = [r for r in rows if r['demand_growth_2040'] >= 2 and r['companionality_pct'] >= 66]
# demand-driven only = high demand growth but supply can respond (primary)
demand_driven = [r for r in rows if r['demand_growth_2040'] >= 3 and r['companionality_pct'] <= 33]
n_vhigh = sum(1 for r in rows if r['outlook'] == 'very high')

out = {
    'generated': data.get('generated'),
    'n': len(rows),
    'n_very_high': n_vhigh,
    'max_growth': max(r['demand_growth_2040'] for r in rows),
    'max_growth_material': max(rows, key=lambda r: r['demand_growth_2040'])['title'],
    'squeeze_set': [r['title'] for r in squeeze_set],
    'demand_driven': [r['title'] for r in demand_driven],
    'rows': rows,
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'demand.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/demand.json')
print(f"  structural squeeze (demand>=2x & by-product): {', '.join(out['squeeze_set'])}")
print(f"  demand-driven but mineable: {', '.join(out['demand_driven'])}")

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The squeeze — where surging demand meets supply that can't respond · Critical Materials Atlas</title>
<meta name="description" content="The atlas turns to the demand side: which technologies pull hardest on each critical material, and — crossed with the supply-structure arm — which materials face surging demand AND by-product-locked supply that can't scale. The structural squeeze.">
<meta property="og:title" content="The squeeze: surging demand meets supply that can't respond">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .muted{color:#5a6b68;font-size:.86rem}
 #scatter{width:100%;height:490px}
 .stat4{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin:1.2rem 0}
 @media(max-width:720px){.stat4{grid-template-columns:repeat(2,1fr)}}
 .stat{background:#fff;border:1px solid #e3e9e8;border-left:4px solid #0e7c74;border-radius:10px;padding:.8rem .9rem}
 .stat .v{font-size:1.5rem;font-weight:800;color:#15323a;letter-spacing:-.02em}
 .stat .l{font-size:.76rem;color:#5a6b68;margin-top:.15rem;line-height:1.35}
 .stat.warn{border-left-color:#c0392b}.stat.warn .v{color:#c0392b}
 table.tidy{width:100%;border-collapse:collapse;font-size:.87rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .tag{display:inline-block;font-size:.7rem;font-weight:700;padding:.06rem .45rem;border-radius:20px}
 .o3{background:#fbe3df;color:#c0392b}.o2{background:#fdeccf;color:#b07a18}.o1{background:#eef1f0;color:#5a6b68}.o0{background:#eef1f0;color:#9aa6ad}
 .keyline{background:#fbf3f2;border:1px solid #f0d9d5;border-left:4px solid #c0392b;border-radius:10px;padding:.9rem 1.1rem;margin:1.2rem 0}
 .keyline b{color:#c0392b}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="companionality.html">Hostage metals</a><a href="risk.html">Risk</a>
  <a href="recycling.html" class="hideable">Secondary supply</a><a href="methodology.html" class="hideable">Methodology</a>
  <a href="https://github.com/materials-atlas/comtrade-reconcile" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · demand · the squeeze</div>
  <h1>The squeeze</h1>
  <p class="deck">Every other page here measures <i>supply</i>. This one turns around: which technologies &mdash; batteries, magnets, chips, solar, the grid &mdash; pull hardest on each material, and how fast that pull is growing. Then the synthesis that makes it bite: cross demand growth with <a href="companionality.html" style="color:#fff;text-decoration:underline">supply elasticity</a>, and the materials in real trouble separate from the ones that just need more mines.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>How demand and the squeeze are estimated</summary>
  <p>For each material: principal end-use <b>sectors</b>, the <b>clean-energy share</b> of demand, and a <b>demand-growth multiple to ~2040</b> (demand in 2040 &divide; today) grounded in the <b>IEA Global Critical Minerals Outlook 2024</b> (Announced-Pledges scenario) and USGS end-use data. The <b>squeeze index</b> = normalised demand growth &times; companionality &mdash; high only when demand is surging <i>and</i> supply is by-product-locked and cannot scale.</p>
  <p class="howto-src"><b>Caveat:</b> forward demand is scenario-dependent and these are round, mid-scenario figures &mdash; read them as tiers, not forecasts (a different IEA scenario moves battery-metal multiples by a factor of several). Cross-checked against an independent LLM compilation (Codex). Inputs: IEA CMO 2024 + USGS &times; <a href="out/companionality.json">companionality.json</a> &rarr; <a href="out/demand.json">demand.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.6rem 0 .3rem">Demand vs supply elasticity — two very different problems</h2>
  <p class="muted" style="margin-top:0"><b>Right</b> = faster demand growth to 2040. <b>Up</b> = more by-product-locked (supply can&rsquo;t scale). <span style="color:#c0392b;font-weight:700">Top-right</span> is the structural squeeze; <span style="color:#0e7c74;font-weight:700">bottom-right</span> is demand pressure you can still answer with mines.</p>
  <div id="scatter"></div>

  <h2 style="margin:1.6rem 0 .3rem">Every material — demand pull and the squeeze</h2>
  <table class="tidy" id="tab"><thead><tr><th>Material</th><th>pulled by</th><th class="n">clean-energy %</th><th class="n">demand ×2040</th><th>outlook</th><th class="n">by-prod %</th><th class="n">squeeze</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.8rem 0 .3rem">What this opens</h2>
  <p>The demand arm turns the atlas from a snapshot of where supply sits into a map of where pressure is heading &mdash; and, joined to the supply-structure work, separates the materials that need <i>capital and time</i> (lithium, graphite: mine more) from those that need <i>a different playbook entirely</i> (gallium, germanium, rare earths: recovery yield, stockpiles, substitution, because more mines aren&rsquo;t on the menu). From here the branches are concrete: demand by <b>technology scenario</b> (what a faster EV path does to each squeeze), demand by <b>country/bloc</b> (whose industrial policy pulls which metal), and coupling demand growth to the <a href="volume.html">price series</a> to test whether the squeeze is already showing up in unit values.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="companionality.html">Hostage metals</a><br><a href="recycling.html">Secondary supply</a><br><a href="risk.html">Supply risk</a><br><a href="methodology.html">Methodology</a></div>
  <div><h4>Sources</h4>IEA Global Critical Minerals Outlook 2024 · USGS 2024 end-use × companionality</div>
  <div class="fineprint">Forward demand is scenario-dependent; figures are round mid-scenario tiers, not forecasts.</div>
</div></footer>
<script>
function ld(u){return new Promise((res,rej)=>{const s=document.createElement('script');s.src=u;s.onload=res;s.onerror=rej;document.head.appendChild(s);});}
Promise.all([fetch('out/demand.json').then(r=>r.json()),
  ld('https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js')]).then(([S])=>{
  document.getElementById('lead').innerHTML='<b>Result:</b> demand for the energy-transition metals climbs steeply to 2040 &mdash; '+S.max_growth_material+' up to ~'+S.max_growth+'&times; today &mdash; but the pressure splits in two. Materials like lithium and graphite face surging demand you can still meet with new mines; the harder cases surge <i>and</i> are by-product-locked: '+S.squeeze_set.join(', ')+'. For those, demand growth has nowhere elastic to go.';
  const stats=[
    {v:S.n_very_high,l:'materials with very-high demand-growth outlook to 2040'},
    {v:'~'+S.max_growth+'×',l:'steepest demand multiple ('+S.max_growth_material+')'},
    {v:S.squeeze_set.length,l:'in the structural squeeze: surging demand AND by-product-locked',warn:true},
    {v:S.demand_driven.length,l:'demand-driven but mineable — capital & time can answer'},
  ];
  document.getElementById('stats').innerHTML=stats.map(s=>'<div class="stat'+(s.warn?' warn':'')+'"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  document.getElementById('keyline').innerHTML='<b>The distinction that matters:</b> &ldquo;critical + high-demand&rdquo; is not one problem. Lithium demand may rise ~8&times;, but lithium can be mined &mdash; it is a race of capital and permitting. Gallium demand rises fast too, but you cannot open a gallium mine at any price; it comes only with aluminium. Policy that treats the two the same &mdash; subsidise mines &mdash; helps the first group and does nothing for the second.';
  const ocls={'very high':'o3','high':'o2','moderate':'o1','low':'o0'};
  const col={'very high':'#c0392b','high':'#d98324','moderate':'#0e7c74','low':'#9aa6ad'};
  const pts=S.rows.map(r=>({value:[r.demand_growth_2040,r.companionality_pct,r.title,r.outlook,r.squeeze],
    itemStyle:{color:col[r.outlook]+'cc'},
    symbolSize:Math.max(9,(r.clean_energy_pct||0)/6+9)}));
  const ch=echarts.init(document.getElementById('scatter'));
  ch.setOption({
    grid:{left:52,right:26,top:20,bottom:52},
    tooltip:{formatter:p=>'<b>'+p.value[2]+'</b><br>demand to 2040: ~'+p.value[0]+'×<br>by-product share: '+p.value[1]+'%<br>outlook: '+p.value[3]+'<br>squeeze: '+p.value[4].toFixed(0)},
    xAxis:{name:'demand growth to ~2040 (× today)',nameLocation:'middle',nameGap:30,min:0.5,max:8.5,
      axisLabel:{color:'#5a6b68'},nameTextStyle:{color:'#5a6b68'},splitLine:{lineStyle:{color:'#eef1f0'}}},
    yAxis:{name:'companionality (supply can’t scale →)',nameLocation:'middle',nameGap:36,min:0,max:105,
      axisLabel:{color:'#5a6b68'},nameTextStyle:{color:'#5a6b68'},splitLine:{lineStyle:{color:'#eef1f0'}}},
    series:[{type:'scatter',data:pts,
      markLine:{silent:true,symbol:'none',lineStyle:{color:'#c9b3ad',type:'dashed'},data:[{xAxis:2},{yAxis:66}]},
      label:{show:true,formatter:p=>p.value[2],position:'right',fontSize:10,color:'#15323a',distance:4}}]
  });
  window.addEventListener('resize',()=>ch.resize());
  const tb=document.querySelector('#tab tbody');
  S.rows.forEach(r=>{
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+r.title+'</b></td>'+
      '<td class="muted" style="font-size:.82rem">'+r.sectors.join(', ')+'</td>'+
      '<td class="n">'+r.clean_energy_pct+'</td>'+
      '<td class="n" style="font-weight:600">'+r.demand_growth_2040+'×</td>'+
      '<td><span class="tag '+ocls[r.outlook]+'">'+r.outlook+'</span></td>'+
      '<td class="n">'+r.companionality_pct+'</td>'+
      '<td class="n" style="font-weight:700;color:'+(r.squeeze>=50?'#c0392b':r.squeeze>=25?'#b07a18':'#9aa6ad')+'">'+r.squeeze.toFixed(0)+'</td>';
    tb.appendChild(tr);
  });
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'demand.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote demand.html')
