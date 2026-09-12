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

# ---- IEA scenario bands: real, computed g per scenario where the IEA publishes a TOTAL-demand series ----
# g is a forward DEMAND MULTIPLE, which is scenario-dependent by construction — quoting one number hides that.
# The IEA Critical Minerals Dataset (CC BY 4.0) gives total demand by mineral under STEPS / APS / NZE, so for
# the minerals it covers we COMPUTE g = total demand 2040 / 2024 in each scenario and carry the whole band
# (STEPS = low, APS = central, NZE = high) instead of a curated point. Only 6 minerals have a total-demand
# series; sheet 3.2 covers ~37 but clean-tech demand only (a different metric), so it is not used for g.
import csv as _csv
IEA_F = os.path.join(ROOT, 'raw', 'iea', 'iea_demand_scenarios.csv')
IEA_G = {}
if os.path.exists(IEA_F):
    for _r in _csv.DictReader(open(IEA_F, encoding='utf-8')):
        IEA_G[_r['material']] = {'low': float(_r['g_steps']), 'central': float(_r['g_aps']),
                                 'high': float(_r['g_nze']), 'base_2024': float(_r['base_2024'])}

# ---- bottom-up: WHICH technology pulls each metal (IEA demand by technology, 2024 vs APS-2040) ----
# A demand multiple says how much more; it doesn't say what is doing the pulling. The IEA breaks demand down by
# end-use technology, so we can decompose the growth: biggest use by 2040, and the technology adding the most
# absolute demand between 2024 and 2040 (the growth driver). This is the dMFA question answered with the
# modeller's own output rather than us rebuilding their model with worse inputs.
IEA_TECH_F = os.path.join(ROOT, 'raw', 'iea', 'iea_demand_by_tech.csv')
IEA_TECH = {}
if os.path.exists(IEA_TECH_F):
    for _r in _csv.DictReader(open(IEA_TECH_F, encoding='utf-8')):
        IEA_TECH.setdefault(_r['material'], []).append(
            {'tech': _r['technology'], 'd2024': float(_r['d2024']), 'd2040': float(_r['d2040_aps'])})
TECH_BREAKDOWN = []
for _m, _ts in IEA_TECH.items():
    _tot40 = sum(t['d2040'] for t in _ts) or 1.0
    _clean = [t for t in _ts if t['tech'].lower() != 'other uses']
    _drv = max(_ts, key=lambda t: t['d2040'] - t['d2024'])
    _top = max(_ts, key=lambda t: t['d2040'])
    TECH_BREAKDOWN.append({
        'material': _m,
        'techs': sorted([{'tech': t['tech'], 'pct_2040': round(100 * t['d2040'] / _tot40, 1),
                          'delta': round(t['d2040'] - t['d2024'], 1)} for t in _ts],
                        key=lambda d: -d['pct_2040']),
        'top_use': _top['tech'], 'top_use_pct': round(100 * _top['d2040'] / _tot40),
        'driver': _drv['tech'], 'driver_delta': round(_drv['d2040'] - _drv['d2024'], 1),
        'driver_share_of_growth': round(100 * (_drv['d2040'] - _drv['d2024']) /
                                        max(sum(max(0, t['d2040'] - t['d2024']) for t in _ts), 1e-9)),
        'cleantech_pct_2040': round(100 * sum(t['d2040'] for t in _clean) / _tot40),
    })
TECH_BREAKDOWN.sort(key=lambda d: -d['cleantech_pct_2040'])

# label -> (sectors, clean_energy_pct, demand_growth_2040 multiple, outlook)
# g curated from IEA Global Critical Minerals Outlook + USGS 2024 end-uses (round figures for a fuzzy forward
# quantity) — but OVERRIDDEN by the computed IEA scenario band above wherever available.
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
    sectors, ce, g_curated, outlook = DEM[lab]
    c = CO.get(lab, {})
    cp = c.get('companionality_pct', 0)
    band = IEA_G.get(lab)
    # computed IEA scenario band wins over the curated point estimate where it exists
    g = band['central'] if band else g_curated
    sq = lambda gg: round((min(gg, 8.0) / 8.0) * (cp / 100.0) * 100, 1)
    rows.append({
        'label': lab, 'title': TITLE.get(lab, lab),
        'sectors': sectors, 'clean_energy_pct': ce, 'demand_growth_2040': round(g, 2), 'outlook': outlook,
        'companionality_pct': cp, 'class': c.get('class', 'primary'),
        'value_eur': m.get('total_eur'), 'squeeze': sq(g),
        # scenario band: computed from IEA STEPS/APS/NZE where published, else None (curated point)
        'g_source': 'IEA computed (STEPS/APS/NZE)' if band else 'curated (literature)',
        'g_low': round(band['low'], 2) if band else None,
        'g_high': round(band['high'], 2) if band else None,
        'g_curated_prev': g_curated if band else None,
        'squeeze_low': sq(band['low']) if band else None,
        'squeeze_high': sq(band['high']) if band else None,
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
    'tech_breakdown': TECH_BREAKDOWN,
    'tech_source': 'IEA Critical Minerals Dataset (CC BY 4.0) — demand by end-use technology, 2024 vs APS 2040',
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
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · demand · the squeeze</div>
  <h1>The squeeze</h1>
  <p class="deck">Lithium demand could rise <b>5.9&times;</b> by 2040 &mdash; the biggest multiple here &mdash; but demand growth alone is not the squeeze. Cross it with supply that <i>cannot respond</i>, and the structural squeeze lands on <b>gallium, germanium and vanadium</b>: high pull, and no way to add supply quickly. Every other page here measures <i>supply</i>. This one turns around: which technologies &mdash; batteries, magnets, chips, solar, the grid &mdash; pull hardest on each material, and how fast that pull is growing. Then the synthesis that makes it bite: cross demand growth with <a href="companionality" style="color:#fff;text-decoration:underline">supply elasticity</a>, and the materials in real trouble separate from the ones that just need more mines.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>How demand and the squeeze are estimated</summary>
  <p>For each material: principal end-use <b>sectors</b>, the <b>clean-energy share</b> of demand, and a <b>demand-growth multiple to ~2040</b> (demand in 2040 &divide; today) grounded in the <b>IEA Global Critical Minerals Outlook 2024</b> (Announced-Pledges scenario) and USGS end-use data. The <b>squeeze index</b> = normalised demand growth &times; companionality &mdash; high only when demand is surging <i>and</i> supply is by-product-locked and cannot scale.</p>
  <p class="howto-src"><b>Scenario-dependence, handled explicitly.</b> A forward demand multiple is scenario-dependent by construction, so quoting one number hides the real uncertainty. For the six minerals where the IEA publishes a <i>total-demand</i> series, we no longer curate a point estimate &mdash; we <b>compute <i>g</i> in all three scenarios</b> from the <a href="https://www.iea.org/data-and-statistics/data-product/critical-minerals-dataset" target="_blank" rel="noopener">IEA Critical Minerals Dataset</a> (CC&nbsp;BY&nbsp;4.0): <b>STEPS</b> (stated policies) &rarr; <b>APS</b> (announced pledges, our central) &rarr; <b>NZE</b> (net zero), and carry the whole band into the squeeze. The remaining materials keep a <b>curated literature estimate</b>, labelled as such in the table &mdash; the IEA&rsquo;s 37-mineral sheet covers <i>clean-tech</i> demand only, which is a different quantity from total demand and would overstate <i>g</i>. Inputs: IEA Critical Minerals Dataset + USGS &times; <a href="out/companionality.json">companionality.json</a> &rarr; <a href="out/demand.json">demand.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.6rem 0 .3rem">Demand vs supply elasticity — two very different problems</h2>
  <p class="muted" style="margin-top:0"><b>Right</b> = faster demand growth to 2040. <b>Up</b> = more by-product-locked (supply can&rsquo;t scale). <span style="color:#c0392b;font-weight:700">Top-right</span> is the structural squeeze; <span style="color:#0e7c74;font-weight:700">bottom-right</span> is demand pressure you can still answer with mines.</p>
  <div id="scatter"></div>

  <h2 style="margin:1.6rem 0 .3rem">Every material — demand pull and the squeeze</h2>
  <table class="tidy" id="tab"><thead><tr><th>Material</th><th>pulled by</th><th class="n">clean-energy %</th><th class="n">demand ×2040</th><th>outlook</th><th class="n">by-prod %</th><th class="n">squeeze</th></tr></thead><tbody></tbody></table>

  <div class="keyline" id="iea-note" style="background:#f2f6f5;border-color:#d9e6e3;border-left-color:#0e7c74"></div>

  <h2 style="margin:1.8rem 0 .4rem">What is actually doing the pulling?</h2>
  <p class="muted" style="margin-top:0">A multiple says <i>how much more</i>; it doesn&rsquo;t say <i>what wants it</i>. The IEA breaks demand down by end-use technology, so we can decompose the growth rather than assert it: the <b>biggest use by 2040</b>, and the technology adding the most <b>absolute</b> demand between 2024 and 2040 &mdash; the growth driver.</p>
  <table class="tidy" id="techtab" style="max-width:820px"><thead><tr><th>Mineral</th><th>demand mix in 2040</th><th class="n">clean-tech share</th><th>growth driver 2024&rarr;2040</th></tr></thead><tbody></tbody></table>
  <div class="keyline" id="techkey" style="background:#f2f6f5;border-color:#d9e6e3;border-left-color:#0e7c74"></div>

  <h2 style="margin:1.8rem 0 .3rem">What this opens</h2>
  <p>The demand arm turns the atlas from a snapshot of where supply sits into a map of where pressure is heading &mdash; and, joined to the supply-structure work, separates the materials that need <i>capital and time</i> (lithium, graphite: mine more) from those that need <i>a different playbook entirely</i> (gallium, germanium, rare earths: recovery yield, stockpiles, substitution, because more mines aren&rsquo;t on the menu). From here the branches are concrete: demand by <b>technology scenario</b> (what a faster EV path does to each squeeze), demand by <b>country/bloc</b> (whose industrial policy pulls which metal), and coupling demand growth to the <a href="volume.html">price series</a> to test whether the squeeze is already showing up in unit values.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
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
      '<td class="n" style="font-weight:600">'+r.demand_growth_2040+'×'+
        (r.g_low?'<div class="muted" style="font-weight:400;font-size:.7rem" title="IEA STEPS → NZE scenario band (computed)">'+r.g_low+'–'+r.g_high+'× <span style="color:#0e7c74">IEA</span></div>'
              :'<div class="muted" style="font-weight:400;font-size:.7rem" title="curated literature estimate — no IEA total-demand series">curated</div>')+'</td>'+
      '<td><span class="tag '+ocls[r.outlook]+'">'+r.outlook+'</span></td>'+
      '<td class="n">'+r.companionality_pct+'</td>'+
      '<td class="n" style="font-weight:700;color:'+(r.squeeze>=50?'#c0392b':r.squeeze>=25?'#b07a18':'#9aa6ad')+'">'+r.squeeze.toFixed(0)+
        (r.squeeze_low!=null&&r.squeeze_high>0?'<div class="muted" style="font-weight:400;font-size:.7rem">'+r.squeeze_low.toFixed(0)+'–'+r.squeeze_high.toFixed(0)+'</div>':'')+'</td>';
    tb.appendChild(tr);
  });
  // what pulls each metal: IEA demand-by-technology decomposition
  (function(){
    const TB=S.tech_breakdown; if(!TB||!TB.length) return;
    const COL={'Electric vehicles':'#c0392b','Other uses':'#c9d3d1','Electricity networks':'#3f6fb0',
      'Solar PV':'#e0a92a','Wind':'#0e7c74','Grid battery storage':'#8a2f3f','Hydrogen technologies':'#7d5fb0',
      'Other low emissions power generation':'#2f8f6b','Low emissions power generation':'#2f8f6b'};
    const col=t=>COL[t]||'#9aa6ad';
    const tt=document.querySelector('#techtab tbody');
    TB.forEach(d=>{
      const bars=d.techs.filter(t=>t.pct_2040>0.5).map(t=>'<span title="'+t.tech+': '+t.pct_2040+'% of 2040 demand" style="display:inline-block;height:15px;width:'+t.pct_2040+'%;background:'+col(t.tech)+'"></span>').join('');
      const tr=document.createElement('tr');
      tr.innerHTML='<td><b>'+TITLE(d.material)+'</b></td>'+
        '<td><div style="display:flex;width:100%;border-radius:3px;overflow:hidden;font-size:0">'+bars+'</div>'+
          '<div class="muted" style="font-size:.7rem;margin-top:.15rem">biggest: '+d.top_use.toLowerCase()+' '+d.top_use_pct+'%</div></td>'+
        '<td class="n"><b>'+d.cleantech_pct_2040+'%</b></td>'+
        '<td><b style="color:#c0392b">'+d.driver+'</b><div class="muted" style="font-size:.7rem">'+d.driver_share_of_growth+'% of all growth</div></td>';
      tt.appendChild(tr);
    });
    const evAll=TB.every(d=>/electric vehicle/i.test(d.driver));
    document.getElementById('techkey').innerHTML='<b style="color:#0e7c74">It is one technology.</b> '+(evAll?'For <b>every one</b> of these six minerals':'For most of these minerals')+' the growth driver 2024&rarr;2040 is the same thing: the <b>electric vehicle</b> &mdash; copper, cobalt, lithium, nickel, magnet rare earths and graphite alike. Note the split it creates: for copper, cobalt, nickel and magnets, clean tech is still a <i>minority</i> of 2040 demand (the bulk is ordinary industrial &ldquo;other uses&rdquo;) &mdash; yet EVs supply essentially <b>all of the growth</b>. Lithium and graphite are the exceptions where EVs dominate the level too. So the whole critical-minerals demand story reduces, to first order, to <b>how many electric cars get built</b> &mdash; which is exactly why the scenario band above is wide, and why a single number would have been a fiction. Source: IEA Critical Minerals Dataset, CC BY 4.0.';
  })();
  // IEA computed-band note + the correction it forced
  (function(){
    const iea=S.rows.filter(r=>r.g_low), cut=iea.filter(r=>r.g_curated_prev && r.g_curated_prev>r.g_high);
    const el=document.getElementById('iea-note'); if(!el||!iea.length) return;
    el.innerHTML='<b style="color:#0e7c74">Real scenarios beat a round number &mdash; and they corrected us.</b> For the <b>'+iea.length+'</b> minerals where the IEA publishes a total-demand series, <i>g</i> is now <b>computed in all three scenarios</b> rather than curated, so the table shows a band (e.g. lithium <b>4.5&ndash;7.5&times;</b>, graphite <b>2.3&ndash;3.9&times;</b>) instead of a false decimal. Doing that <b>caught our own numbers running hot</b>: '+cut.length+' of them sat <i>above even the Net-Zero scenario</i> &mdash; magnets were carried at 3.5&times; when the IEA&rsquo;s most aggressive case is 1.9&times;, cobalt at 2.5&times; vs 1.98&times;. Those were 2024-report headlines on a 2023 base; the dataset is the May-2025 update on a 2024 base, and the IEA revised down. <b>The correction bites:</b> cobalt no longer clears the <i>g</i>&nbsp;&ge;&nbsp;2 bar, so it drops out of the structural-squeeze set. <b>The headline survives it:</b> gallium and germanium remain the <a href="synthesis.html">hardest cases</a> (99% / 96% under <a href="uncertainty.html">Monte-Carlo</a>) &mdash; they were never propped up by the numbers that moved. Source: IEA Critical Minerals Dataset, CC BY 4.0.';
  })();
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'demand.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote demand.html')
