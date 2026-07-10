#!/usr/bin/env python3
"""
Host-shock model — when the host stumbles, the companion bleeds.

Child of companionality + risk-adjusted. By-product metals are produced only when their HOST commodity is
mined/smelted. Invert the companionality map (companion -> hosts) into host -> companions, weight each edge
by the companion's exposure to that host, and you get a systemic-risk view: which ordinary bulk commodities
silently gate the supply of critical materials. A downturn in aluminium is a gallium shock; a zinc slump is
a germanium shock. The page also lets a reader apply a shock to any host and watch the companion losses.

exposure(companion -> host) = (companionality/100) / n_hosts   (by-product share split evenly across hosts)
companion supply loss from an S% host cut = S% x exposure. Payload of a host = sum of exposure x companion
supply-risk score, i.e. how much *critical* supply hangs on that one commodity. Public data; deterministic.
Run: python build_host_shock.py
"""
import json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
comp = json.load(open(os.path.join(ROOT, 'out', 'companionality.json'), encoding='utf8'))
risk = json.load(open(os.path.join(ROOT, 'out', 'risk.json'), encoding='utf8'))
RS = {r['label']: r['score'] for r in risk['materials']}

# nice host display names
HOSTNAME = {'natural gas': 'Natural gas', 'steel slag': 'Steel slag', 'mineral sands': 'Mineral sands'}
def hn(h): return HOSTNAME.get(h, h[:1].upper() + h[1:])

hosts = defaultdict(list)   # host -> [{companion, title, exposure, comp_pct, risk}]
for r in comp['rows']:
    cp = r['companionality_pct']
    hs = r['hosts']
    if cp <= 0 or not hs:
        continue
    exp = (cp / 100.0) / len(hs)
    for h in hs:
        hosts[h].append({'label': r['label'], 'title': r['title'], 'exposure': round(exp, 3),
                         'comp_pct': cp, 'risk': RS.get(r['label'], 0)})

host_rows = []
for h, comps in hosts.items():
    comps.sort(key=lambda c: -c['exposure'] * (c['risk'] or 1))
    payload = round(sum(c['exposure'] * (c['risk'] or 0) for c in comps), 1)
    host_rows.append({
        'host': h, 'name': hn(h), 'n_companions': len(comps),
        'companions': comps,
        'critical_companions': [c['title'] for c in comps],
        'payload': payload,
    })
host_rows.sort(key=lambda r: -r['payload'])

out = {
    'generated': comp.get('generated'),
    'default_shock_pct': 25,
    'n_hosts': len(host_rows),
    'top_host': host_rows[0]['name'] if host_rows else None,
    'hosts': host_rows,
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'host_shock.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/host_shock.json')
print('  most systemic hosts:', ', '.join(f"{r['name']} ({r['n_companions']} criticals)" for r in host_rows[:5]))

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Host-shock model — when the host stumbles, the companion bleeds · Critical Materials Atlas</title>
<meta name="description" content="By-product metals are produced only when their host commodity is. This layer inverts the map — host commodity to the criticals riding on it — and lets you shock any host to watch the companion supply losses cascade.">
<meta property="og:title" content="Host-shock: the bulk commodities that secretly gate critical supply">
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
 table.tidy{width:100%;border-collapse:collapse;font-size:.88rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left;vertical-align:top}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .sim{background:#f4f7f6;border:1px solid #e3e9e8;border-radius:12px;padding:1.1rem 1.2rem;margin:1rem 0}
 .sim .ctl{display:flex;gap:1.2rem;align-items:center;flex-wrap:wrap;margin-bottom:.6rem}
 .sim select,.sim input[type=range]{accent-color:#0e7c74}
 .sim select{padding:.3rem .5rem;border:1px solid #cdd8d5;border-radius:6px;font:inherit}
 .barrow{display:grid;grid-template-columns:150px 1fr 66px;align-items:center;gap:.6rem;margin:.25rem 0;font-size:.86rem}
 .barrow .nm{text-align:right;font-weight:600;color:#15323a}
 .barrow .track{background:#e7ecea;border-radius:5px;height:18px;overflow:hidden}
 .barrow .fill{height:100%;background:#c0392b;border-radius:5px}
 .barrow .v{text-align:right;color:#c0392b;font-weight:700;font-variant-numeric:tabular-nums}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="companionality.html">Hostage metals</a><a href="scenarios.html">Scenarios</a>
  <a href="risk-adjusted.html" class="hideable">Adjusted risk</a><a href="methodology.html" class="hideable">Methodology</a>
  <a href="https://github.com/materials-atlas/comtrade-reconcile" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · systemic · host dependency</div>
  <h1>When the host stumbles</h1>
  <p class="deck">A by-product metal is hostage to the commodity it rides on. So the real supply shock for gallium isn&rsquo;t a gallium event &mdash; it&rsquo;s an <i>aluminium</i> event. This layer &mdash; child of the <a href="companionality.html" style="color:#fff;text-decoration:underline">hostage-metals</a> page &mdash; inverts the map to expose the ordinary bulk commodities that silently gate critical supply, and lets you shock any one of them.</p>
</div></section>
<article style="max-width:1000px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>How the host-shock is modelled</summary>
  <p>For every by-product material we split its by-product share evenly across its named hosts: <b>exposure(companion&rarr;host) = companionality/100 ÷ number of hosts</b>. Inverting gives, for each host commodity, the critical materials riding on it. A shock of <b>S%</b> to a host cuts each rider&rsquo;s supply by <b>S% &times; exposure</b>. A host&rsquo;s <b>payload</b> weights those exposures by each companion&rsquo;s supply-risk score &mdash; how much <i>critical</i> supply hangs on that one commodity.</p>
  <p class="howto-src"><b>Caveat:</b> even host-splitting is a simplification (real shares vary by deposit and are often undocumented), and it assumes a linear pass-through from host output to companion recovery. A first-order systemic map, not a calibrated model. Inputs: <a href="out/companionality.json">companionality.json</a> &times; <a href="out/risk.json">risk.json</a> &rarr; <a href="out/host_shock.json">host_shock.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <div class="sim">
    <h3 style="margin:.1rem 0 .5rem;font-size:1rem;color:#15323a">Shock a host, watch the companions bleed</h3>
    <div class="ctl">
      <label>Host commodity &nbsp;<select id="host"></select></label>
      <label>Shock &nbsp;<input type="range" id="shock" min="5" max="60" step="5" value="25"> <b id="shockv">25%</b> output cut</label>
    </div>
    <div id="simout"></div>
  </div>

  <h2 style="margin:1.6rem 0 .3rem">The bulk commodities that gate critical supply</h2>
  <p class="muted" style="margin-top:0">Ranked by payload = critical supply riding on each host (exposure &times; each companion&rsquo;s risk score). These are the single points a systemic supply map should watch.</p>
  <table class="tidy" id="tab"><thead><tr><th>Host commodity</th><th class="n">critical riders</th><th>which materials (by exposure)</th><th class="n">payload</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.8rem 0 .3rem">What this spawns</h2>
  <p>The host map turns an abstract list of &ldquo;critical&rdquo; metals into a small set of chokepoint commodities &mdash; aluminium, zinc, copper, nickel, natural gas &mdash; whose ordinary market cycles propagate into the critical layer. The next children write themselves: a <b>recovery-yield / recycling</b> lens (secondary supply is the only source that <i>doesn&rsquo;t</i> depend on the host), and a coupling of this map to real <a href="scenarios.html">shock scenarios</a> and the <a href="trends.html">price series</a> &mdash; do historic aluminium slumps actually show up as gallium squeezes?</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="companionality.html">Hostage metals</a><br><a href="risk-adjusted.html">Adjusted risk</a><br><a href="scenarios.html">Shock scenarios</a><br><a href="methodology.html">Methodology</a></div>
  <div><h4>Sources</h4>Companionality (USGS MCS 2024 · Nassar et al. 2015) × supply-risk index</div>
  <div class="fineprint">A first-order systemic map: host shares are split evenly and pass-through assumed linear.</div>
</div></footer>
<script>
fetch('out/host_shock.json').then(r=>r.json()).then(S=>{
  const H=S.hosts;
  document.getElementById('lead').innerHTML='<b>Result:</b> the critical-materials list collapses onto a handful of ordinary host commodities. <b>'+S.top_host+'</b> carries the most critical supply of any single commodity; a market cycle there is a critical-materials event whether or not anyone calls it one.';
  const withRiders=H.filter(h=>h.n_companions>0);
  const stats=[
    {v:S.n_hosts,l:'host commodities that gate at least one critical material'},
    {v:S.top_host,l:'most systemic host (highest critical payload)'},
    {v:Math.max.apply(null,H.map(h=>h.n_companions)),l:'most critical riders on a single host'},
    {v:H.filter(h=>h.n_companions>=2).length,l:'hosts carrying 2+ critical materials'},
  ];
  document.getElementById('stats').innerHTML=stats.map(s=>'<div class="stat"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  // simulator
  const sel=document.getElementById('host');
  H.forEach((h,i)=>{const o=document.createElement('option');o.value=i;o.textContent=h.name+' — '+h.n_companions+' rider'+(h.n_companions>1?'s':'');sel.appendChild(o);});
  const shock=document.getElementById('shock'),shockv=document.getElementById('shockv'),simout=document.getElementById('simout');
  function render(){
    const h=H[+sel.value], s=+shock.value; shockv.textContent=s+'%';
    const rows=h.companions.map(c=>({t:c.title,loss:s*c.exposure})).sort((a,b)=>b.loss-a.loss);
    const mx=Math.max.apply(null,rows.map(r=>r.loss),1);
    simout.innerHTML='<p class="muted" style="margin:.2rem 0 .5rem">A <b>'+s+'%</b> cut to <b>'+h.name+'</b> output &rarr; estimated by-product supply loss:</p>'+
      rows.map(r=>'<div class="barrow"><div class="nm">'+r.t+'</div><div class="track"><div class="fill" style="width:'+Math.max(2,100*r.loss/mx)+'%"></div></div><div class="v">−'+r.loss.toFixed(1)+'%</div></div>').join('');
  }
  sel.value=0; sel.onchange=render; shock.oninput=render; render();
  // table
  const tb=document.querySelector('#tab tbody');
  H.forEach(h=>{
    const list=h.companions.map(c=>c.title+' <span style="color:#9aa6ad">('+(c.exposure*100).toFixed(0)+'%)</span>').join(', ');
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+h.name+'</b></td><td class="n">'+h.n_companions+'</td><td class="muted">'+list+'</td><td class="n" style="font-weight:700">'+h.payload.toFixed(0)+'</td>';
    tb.appendChild(tr);
  });
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'host-shock.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote host-shock.html')
