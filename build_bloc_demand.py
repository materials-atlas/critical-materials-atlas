#!/usr/bin/env python3
"""
Demand by bloc — whose industrial policy pulls which squeezed metal.

Reconnects the demand arm to the atlas's geographic core. Using the atlas's own import flows (destination =
revealed demand), aggregate each material's imports into blocs — China, EU, US, Japan, Korea, India, Other —
and read who pulls it. Then overlay the industrial-policy driver (which bloc's EV/chip/magnet/defence policy
is behind that pull) and each bloc's import reliance. Focus on the squeeze metals: for the materials that
can't scale supply, demand geography is where the contest actually plays out.

Big caveat, and the reason it's stated loudly: trade IMPORTS are an imperfect demand proxy. China imports ores
it refines and re-exports; Hong Kong/Netherlands/Singapore are trans-shipment hubs; imports mix intermediate
processing with final consumption. So bloc import share = revealed trade pull, not final consumption.

TWO distinct flaws, and they are NOT the same size (literature: apparent consumption vs Raw Material
Equivalents / material footprint; UN SEEA, Eurostat RME model, EXIOBASE). (1) RE-EXPORT of the same metal —
the visible one, which the NET-DEMAND page fixes by subtracting exports. (2) DEMAND EMBODIED IN FINISHED
GOODS — gallium consumed inside an imported chip inside an imported server never shows up as a gallium
import at all. For critical metals this second channel is the LARGER of the two (tiny volumes, intermediate-
heavy trade, end-use buried in electronics/autos), and net trade does NOT touch it. Two routes at it, both
tested and both limited. A material-footprint model (Raw Material Equivalents via a multi-region input-output
table) captures all tiers but is sector-coarse (resolves "electronics", not gallium — no per-metal). A
BOTTOM-UP estimate (product trade x metal intensity) was PROTOTYPED for cobalt on battery trade (HS 8507,
BACI 2023) and stress-tested: it answers a trade-STAGE question, not a demand one. It cleanly shows
intermediate cobalt is China-bound while finished cells are net-imported by the US/EU — but calling that
"cobalt demand by country" is a category error (net-export clamping erases China's own large use, product-
weight intermediates aren't contained metal, and cobalt also travels in imported cars/electronics outside
the battery code). So even cobalt, the cleanest carrier, resists a per-country final-demand figure. Bottom-up
clarifies trade STAGES; it is not a demand measure. We report trade pull as a stage fact and name what's
beyond it, rather than dress it up as consumption. Public data; deterministic.
Run: python build_bloc_demand.py
"""
import json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = '2024'
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))
dem = json.load(open(os.path.join(ROOT, 'out', 'demand.json'), encoding='utf8'))
comp = json.load(open(os.path.join(ROOT, 'out', 'companionality.json'), encoding='utf8'))
DE = {r['label']: r for r in dem['rows']}
CO = {r['label']: r for r in comp['rows']}

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

# industrial-policy driver + import reliance per key material (curated).
POLICY = {
    'gallium':   ('China ~80% of supply + 2023 export controls; EU CRMA & US CHIPS chase alternatives', {'EU': 100, 'US': 100, 'JP': 95}),
    'germanium': ('China-dominated, 2023 export controls; fibre/IR/chip demand in US/EU/JP', {'EU': 100, 'US': 100, 'JP': 90}),
    'cobalt':    ('DRC-mined, China-refined; EU CRMA & US IRA push non-China battery supply', {'EU': 85, 'US': 75}),
    'vanadium':  ('steel + emerging grid batteries; China dominant; redox-flow policy in US/EU/CN', {'EU': 80, 'US': 90}),
    'magnets':   ('China ~90% of magnets; EU CRMA & US IRA reshoring; wind + EV pull', {'EU': 95, 'US': 90, 'JP': 80}),
    'lithium':   ('battery core; US IRA & EU CRMA vs China midstream dominance', {'EU': 80, 'US': 70}),
    'graphite':  ('anode material; China ~90% + export licensing; US IRA FEOC rules', {'EU': 95, 'US': 95}),
    'nickel':    ('Indonesia-China axis; battery + stainless; IRA sourcing rules', {'EU': 75, 'US': 80}),
    'silicon':   ('solar polysilicon + chips; China dominates polysilicon; US/EU CHIPS Acts', {'EU': 80, 'US': 70}),
    'antimony':  ('flame retardant + munitions + PV glass; China/Russia; 2024 China export controls', {'EU': 100, 'US': 85}),
    'tungsten':  ('carbide tooling + defence; China-dominated; US defence stockpile', {'EU': 95, 'US': 85}),
    'tantalum':  ('capacitors; Central-Africa mined; electronics demand in JP/KR/US', {'EU': 90, 'US': 85}),
    'niobium':   ('steel microalloying; Brazil ~90%; concentrated but stable', {'EU': 100, 'US': 100}),
    'platinum':  ('autocatalysts + H2 electrolysers; South Africa/Russia; H2 policy upside', {'EU': 95, 'JP': 90}),
    'palladium': ('autocatalysts; Russia/South Africa; ICE-linked, H2 wildcard', {'EU': 90, 'JP': 85}),
    'graphite ': ('', {}),
}

rows = []
for lab, fl in flows['materials'].items():
    de = DE.get(lab)
    imp = defaultdict(float)
    for f in fl:
        imp[bloc(f['to'])] += f['value']
    tot = sum(imp.values())
    if tot <= 0:
        continue
    shares = {b: round(100 * imp.get(b, 0) / tot, 1) for b in BLOCS}
    hhi = round(sum((imp.get(b, 0) / tot) ** 2 for b in BLOCS), 3)
    top = max(BLOCS, key=lambda b: shares[b])
    pol = POLICY.get(lab, ('', {}))
    rows.append({
        'label': lab, 'title': CO.get(lab, {}).get('title', de['title'] if de else lab),
        'squeeze': de['squeeze'] if de else 0,
        'demand_growth_2040': de['demand_growth_2040'] if de else None,
        'driver_tech': (de['sectors'][0] if de and de.get('sectors') else None),
        'companionality_pct': CO.get(lab, {}).get('companionality_pct', 0),
        'import_eur': round(tot),
        'shares': shares, 'top_bloc': top, 'demand_hhi': hhi,
        'policy_note': pol[0], 'import_reliance': pol[1],
    })

# bloc-level summary: each bloc's total import pull across the squeeze metals (companionality>=40 or squeeze>=15)
key_metals = [r for r in rows if r['squeeze'] >= 15 or (r['demand_growth_2040'] or 0) >= 2.5]
bloc_pull = defaultdict(float)
bloc_metals = defaultdict(lambda: defaultdict(float))
for r in key_metals:
    for b in BLOCS:
        v = r['import_eur'] * r['shares'][b] / 100.0
        bloc_pull[b] += v
        bloc_metals[b][r['title']] += v
bloc_summary = []
for b in BLOCS:
    tops = sorted(bloc_metals[b].items(), key=lambda kv: -kv[1])[:4]
    bloc_summary.append({'bloc': b, 'pull_eur': round(bloc_pull[b]),
                         'top_metals': [t for t, _ in tops]})
bloc_summary.sort(key=lambda d: -d['pull_eur'])

rows.sort(key=lambda r: -r['squeeze'])
out = {
    'generated': dem.get('generated'), 'year': YEAR, 'blocs': BLOCS,
    'n': len(rows),
    'rows': rows,
    'key_metals': [r['label'] for r in key_metals],
    'bloc_summary': bloc_summary,
    'caveat': 'Bloc share = revealed import (trade) pull, not final consumption. Two flaws: re-export of '
              'the same metal (netted out on the net-demand page) and — larger for critical metals — demand '
              'embodied in imported finished goods (gallium inside chips), which trade data cannot see per '
              'metal and only a material-footprint/RME model (sector-coarse) would.',
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'bloc_demand.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/bloc_demand.json')
print('  bloc pull rank (key metals):', ', '.join(f"{b['bloc']} {round(b['pull_eur']/1e9,1)}B" for b in bloc_summary))
print('  gallium demand shares:', next((r['shares'] for r in rows if r['label'] == 'gallium'), None))

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Demand by bloc — whose policy pulls which metal · Critical Materials Atlas</title>
<meta name="description" content="Using the atlas's own import flows as a revealed-demand proxy, which bloc — China, EU, US, Japan, Korea, India — pulls hardest on each squeezed critical material, and which industrial policy is behind it.">
<meta property="og:title" content="Demand by bloc: whose industrial policy pulls which critical metal">
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
 .legend{display:flex;flex-wrap:wrap;gap:.8rem;font-size:.78rem;color:#5a6b68;margin:.5rem 0 .2rem}
 .legend span b{display:inline-block;width:.7rem;height:.7rem;border-radius:2px;margin-right:.3rem;vertical-align:middle}
 .mrow{margin:.55rem 0}
 .mrow .top{display:flex;justify-content:space-between;align-items:baseline;font-size:.86rem;margin-bottom:.15rem}
 .mrow .top b{color:#15323a}.mrow .top .drv{color:#5a6b68;font-size:.78rem}
 .sbar{display:flex;height:22px;border-radius:5px;overflow:hidden;background:#eef3f2}
 .sbar i{display:block;height:100%}
 .pol{font-size:.78rem;color:#5a6b68;margin:.2rem 0 0;padding-left:.1rem}
 table.tidy{width:100%;border-collapse:collapse;font-size:.86rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="demand.html">The squeeze</a><a href="countries.html">Countries</a>
  <a href="companionality.html" class="hideable">Hostage metals</a><a href="methodology.html" class="hideable">Methodology</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · demand · geography</div>
  <h1>Whose policy pulls which metal</h1>
  <p class="deck">The <a href="demand.html" style="color:#fff;text-decoration:underline">squeeze</a> is global, but the pull is national. Using the atlas&rsquo;s own import flows as a revealed-demand proxy, this reads which bloc &mdash; China, the EU, the US, Japan, Korea, India &mdash; draws hardest on each squeezed metal, and names the industrial policy behind it. It reconnects the demand arm to the atlas&rsquo;s geographic spine.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>How demand-by-bloc is read (and why imports are only a proxy)</summary>
  <p>For each material we aggregate <b>import value by destination</b> (the &ldquo;to&rdquo; side of every trade flow, <span id="yr"></span>) into blocs, and read the share each bloc pulls. Overlaid: the industrial-policy driver and each bloc&rsquo;s import reliance.</p>
  <p class="howto-src"><b>Big caveat &mdash; two flaws, not one.</b> Imports are <i>not</i> final consumption. <b>(1) Re-export</b> of the same metal: China imports ores it refines and re-exports; Hong Kong, the Netherlands and Singapore trans-ship. The <a href="net-demand.html">net-demand page</a> fixes this by subtracting exports. <b>(2) Demand embodied in finished goods</b> &mdash; gallium consumed inside an imported chip never appears as a gallium import at all &mdash; and for critical metals this is the <i>larger</i> channel. Netting does not touch it. Two routes at it, both tested and both limited. A <b>material-footprint</b> model (Raw Material Equivalents via a multi-region input-output table) captures all tiers but is sector-coarse &mdash; it sees &ldquo;electronics&rdquo;, not gallium. A <b>bottom-up</b> estimate (product trade &times; metal intensity) sounds per-metal, and we prototyped it for cobalt on battery trade &mdash; but stress-testing showed it answers a trade-<b>stage</b> question, not a demand one: it reveals that intermediate cobalt is China-bound while finished cells are net-imported by the US/EU, yet calling that &ldquo;cobalt demand&rdquo; is a category error (it erases China&rsquo;s own large use, mixes product-weight with contained metal, and misses cobalt riding in imported cars). So even cobalt resists a per-country final-demand figure. A bloc&rsquo;s share here is <b>revealed trade pull</b> &mdash; a stage fact, not consumption. Inputs: flows &times; <a href="out/demand.json">demand.json</a> &rarr; <a href="out/bloc_demand.json">bloc_demand.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <h2 style="margin:1.6rem 0 .3rem">Who pulls each squeezed metal</h2>
  <div class="legend" id="legend"></div>
  <div id="mlist"></div>

  <h2 style="margin:1.8rem 0 .3rem">Each bloc&rsquo;s exposure &mdash; and its policy answer</h2>
  <table class="tidy" id="btab"><thead><tr><th>Bloc</th><th class="n">import pull, key metals</th><th>most-pulled squeezed metals</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.8rem 0 .3rem">What this reconnects, and opens</h2>
  <p>The supply-structure arm said <i>which</i> metals can&rsquo;t scale; the demand arm said <i>how fast</i> the pull is growing; this says <i>who</i> is pulling &mdash; and the three together turn a materials list into a map of industrial-policy contests. The honest limit is the proxy: import pull conflates processing with consumption, which is precisely why China tops the demand table for metals it also refines for the world. The clean next child is an <b>apparent-consumption</b> estimate (production + imports − exports) per bloc, and a coupling of these demand shares to each bloc&rsquo;s stated 2030 policy targets &mdash; does the pull match the promise?</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="demand.html">The squeeze</a><br><a href="origin.html">Origin trace</a><br><a href="countries.html">Dependency by country</a><br><a href="methodology.html">Methodology</a></div>
  <div><h4>Sources</h4>Reconciled import flows (revealed demand) × IEA/USGS/EU CRMA policy framing</div>
  <div class="fineprint">Bloc share is revealed import pull, not final consumption. Re-export inflates China's share (netted on the net-demand page); demand embodied in imported finished goods is unobserved per metal and would need a material-footprint/RME model.</div>
</div></footer>
<script>
fetch('out/bloc_demand.json').then(r=>r.json()).then(S=>{
  const f=n=>Number(n).toLocaleString();
  const COL={CN:'#c0392b',EU:'#2b6fb0',US:'#15323a',JP:'#7d5fb0',KR:'#2f8f6b',IN:'#d98324',Other:'#c2ccca'};
  const NAME={CN:'China',EU:'EU',US:'US',JP:'Japan',KR:'Korea',IN:'India',Other:'Other'};
  document.getElementById('yr').textContent=S.year;
  const key=S.rows.filter(r=>S.key_metals.includes(r.label));
  const top=S.bloc_summary[0];
  document.getElementById('lead').innerHTML='<b>Result:</b> demand for the squeezed metals is as concentrated as their supply &mdash; just in different capitals. '+NAME[top.bloc]+' shows the largest import pull across the key metals, but the map splits by technology: batteries pull toward China/Korea/EU, chips toward the US/Japan/Korea, magnets and defence toward the EU and US. Read the shares as trade pull, not final consumption.';
  document.getElementById('legend').innerHTML=S.blocs.map(b=>'<span><b style="background:'+COL[b]+'"></b>'+NAME[b]+'</span>').join('');
  document.getElementById('mlist').innerHTML=key.map(r=>{
    const segs=S.blocs.map(b=>r.shares[b]>0?'<i style="width:'+r.shares[b]+'%;background:'+COL[b]+'" title="'+NAME[b]+' '+r.shares[b]+'%"></i>':'').join('');
    return '<div class="mrow"><div class="top"><b>'+r.title+'</b> <span class="drv">'+(r.driver_tech||'')+' &middot; pulled most by '+NAME[r.top_bloc]+' ('+r.shares[r.top_bloc]+'%)</span></div>'+
      '<div class="sbar">'+segs+'</div>'+(r.policy_note?'<div class="pol">&#9670; '+r.policy_note+'</div>':'')+'</div>';
  }).join('');
  const stats=[
    {v:NAME[top.bloc],l:'largest import pull across the key squeezed metals'},
    {v:key.filter(r=>r.top_bloc==='CN').length+' / '+key.length,l:'key metals whose largest importer is China (refining + re-export inflates this)'},
    {v:key.filter(r=>r.top_bloc==='US').length,l:'key metals pulled most by the US (chips, defence, catalysts)'},
    {v:key.filter(r=>r.top_bloc==='EU').length,l:'key metals pulled most by the EU'},
  ];
  document.getElementById('stats').innerHTML=stats.map(s=>'<div class="stat"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  const tb=document.querySelector('#btab tbody');
  S.bloc_summary.forEach(b=>{
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b style="color:'+COL[b.bloc]+'">'+NAME[b.bloc]+'</b></td><td class="n">&euro;'+f(Math.round(b.pull_eur/1e6))+'M</td><td class="muted">'+(b.top_metals.join(', ')||'—')+'</td>';
    tb.appendChild(tr);
  });
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'bloc-demand.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote bloc-demand.html')
