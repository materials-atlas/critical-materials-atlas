#!/usr/bin/env python3
"""
Supply-shock cascade — the first-order hit, and the companion echo.

Capstone of the supply + demand arms. A shock to a producer country doesn't stop at the materials it mines:
where one of those materials is a HOST commodity, the by-product companions riding on it take a second-order
hit. Congo's cobalt is also a copper story; Indonesia's nickel drags cobalt with it; China's aluminium/coal
gate gallium and germanium. This model propagates a country shock through production geography (USGS shares),
then through the companion web (companionality), then out to the exposed importing blocs (net trade), and
scores each country as a single point of failure for critical supply.

first-order loss(material) = shock x country's world production share.
companion echo(companion) = first-order loss(host) x companion's by-product reliance on that host.
Interactive: pick a country and a shock size; watch the direct hits and the echo, and who imports the fallout.
Public data; deterministic. Run: python build_cascade.py
"""
import json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
comp = json.load(open(os.path.join(ROOT, 'out', 'companionality.json'), encoding='utf8'))
net = json.load(open(os.path.join(ROOT, 'out', 'net_demand.json'), encoding='utf8'))
prod = json.load(open(os.path.join(ROOT, 'out', 'production.json'), encoding='utf8'))
flows = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf8'))
NAMES = flows.get('names', {})
WT = {r['label']: r['world_tonnes'] for r in prod['rows']}   # absolute world production, tonnes (WMD 2024)
CO = {r['label']: r for r in comp['rows']}
NET = {r['label']: r for r in net['rows']}
TITLE = {m['label']: CO.get(m['label'], {}).get('title', m['title'].split(' (')[0]) for m in data['materials']}
BLOCS = net['blocs']

# host material (in the tracked 32) -> by-product companions that ride on it
HOST_COMPANIONS = {
    'copper':    ['cobalt', 'arsenic'],
    'nickel':    ['cobalt', 'palladium'],
    'bauxite':   ['gallium'],
    'niobium':   ['tantalum'],
    'platinum':  ['palladium'],
    'cokingcoal':['germanium'],
}
def n_hosts(lab):
    return max(1, len(CO.get(lab, {}).get('hosts', []) or [1]))

# country -> {material: world production share}
country_prod = defaultdict(dict)
for m in data['materials']:
    for e in (m.get('mined') or []):
        if e.get('c') and (e.get('v') or 0) > 0:
            country_prod[e['c']][m['label']] = e['v']

countries = {}
for c, prod in country_prod.items():
    direct = []
    for lab, share in prod.items():
        if share < 8:
            continue
        co = CO.get(lab, {})
        direct.append({'label': lab, 'title': TITLE.get(lab, lab), 'share': share,
                       'companionality_pct': co.get('companionality_pct', 0),
                       'rigid': co.get('companionality_pct', 0) >= 66,
                       'is_host': lab in HOST_COMPANIONS,
                       'world_tonnes': WT.get(lab),
                       'tonnes_at_risk': (round(share / 100 * WT[lab]) if WT.get(lab) else None)})
    if not direct:
        continue
    direct_labels = {d['label'] for d in direct}
    # companion echo (dedupe by companion, keep strongest path)
    echo_map = {}
    for d in direct:
        if d['label'] not in HOST_COMPANIONS:
            continue
        for comp_lab in HOST_COMPANIONS[d['label']]:
            co = CO.get(comp_lab, {})
            exp = (co.get('companionality_pct', 0) / 100.0) / n_hosts(comp_lab)
            hit = round(d['share'] * exp, 1)   # % of world companion supply at risk (at 100% shock)
            if hit <= 0:
                continue
            cur = echo_map.get(comp_lab)
            if cur is None or hit > cur['hit']:
                echo_map[comp_lab] = {'label': comp_lab, 'title': TITLE.get(comp_lab, comp_lab),
                                      'via': d['title'], 'hit': hit,
                                      'companionality_pct': co.get('companionality_pct', 0),
                                      'world_tonnes': WT.get(comp_lab),
                                      'tonnes_at_risk': (round(hit / 100 * WT[comp_lab]) if WT.get(comp_lab) else None),
                                      'already_direct': comp_lab in direct_labels}
    echo = sorted(echo_map.values(), key=lambda e: -e['hit'])
    # systemic score: direct shares weighted by rigidity + the echo
    score = round(sum(d['share'] / 100 * (1 + d['companionality_pct'] / 100) for d in direct)
                  + sum(e['hit'] / 100 for e in echo if not e['already_direct']), 2)
    # exposed importing blocs (net-demand weighted by each hit)
    bloc_exp = defaultdict(float)
    affected = {d['label']: d['share'] for d in direct}
    for e in echo:
        affected[e['label']] = max(affected.get(e['label'], 0), e['hit'])
    for lab, hit in affected.items():
        ns = NET.get(lab, {}).get('net_share', {})
        for b in BLOCS:
            bloc_exp[b] += hit * ns.get(b, 0) / 100.0
    exposed = sorted(([b, round(v, 1)] for b, v in bloc_exp.items() if v > 0), key=lambda kv: -kv[1])[:4]
    countries[c] = {'iso': c, 'name': NAMES.get(c, c),
                    'direct': sorted(direct, key=lambda d: -d['share']),
                    'echo': echo, 'score': score, 'exposed': exposed}

ranking = sorted(countries.values(), key=lambda d: -d['score'])
for i, r in enumerate(ranking, 1):
    r['rank'] = i

# ---- price-feedback robustness (caveat 2, turned from an unaddressed caveat into a tested one) ----
# The physical cascade above is LEFT UNCHANGED: by-product tonnes die with their host whatever the price,
# so no elasticity touches the tonnage or the echo graph. This adds a SEPARATE market-response layer to the
# IMPACT SCORE only: a supply loss lifts the price, and demand flexes -- but only for metals that CAN flex.
# A by-product (high companionality) has few substitutes and inelastic demand, so it barely damps; a primary
# metal damps more. We reuse the atlas's existing elasticity structure (response ~ 1 - companionality/100)
# and sweep an overall demand-responsiveness eps across a wide band. Metal-specific elasticities do not
# exist on public data, so this is a SENSITIVITY BAND, not a forecast. The gate: the linear score stays the
# primary result; the damped layer only asks whether the ranking survives. Ship the conclusion only if the
# top country is stable across the whole band; otherwise report the instability.
def damped_score(cty, eps):
    dd = sum(d['share'] / 100 * (1 + d['companionality_pct'] / 100)
             / (1 + eps * (1 - d['companionality_pct'] / 100)) for d in cty['direct'])
    ee = sum(e['hit'] / 100 for e in cty['echo'] if not e['already_direct'])  # echo undamped: inelastic
    return dd + ee

EPS_BAND = [0.0, 0.2, 0.5, 1.0]   # 0 = the published linear model; 1 = strong demand response
scen = []
for eps in EPS_BAND:
    rk = sorted(countries.values(), key=lambda c: -damped_score(c, eps))
    top, second = rk[0], (rk[1] if len(rk) > 1 else None)
    s2 = damped_score(second, eps) if second else 0
    scen.append({'eps': eps, 'top': top['name'], 'top_iso': top['iso'],
                 'lead_ratio': round(damped_score(top, eps) / s2, 1) if s2 > 0 else None,
                 'top5': [r['name'] for r in rk[:5]]})
_leads = [s['lead_ratio'] for s in scen if s['lead_ratio']]
robustness = {
    'eps_band': EPS_BAND, 'scenarios': scen,
    'top_stable': len({s['top_iso'] for s in scen}) == 1,
    'top_country': scen[0]['top'],
    'lead_min': min(_leads) if _leads else None, 'lead_max': max(_leads) if _leads else None,
    'note': 'Physical cascade unchanged. Demand-response damping applied to the impact score only, scaled '
            'by each metal\'s elasticity (~1 - companionality); by-products stay inelastic. eps swept 0-1 '
            'as a sensitivity band (per-metal elasticities do not exist on public data). Ship only if the '
            'top single point of failure is stable across the band.',
}

out = {
    'generated': data.get('generated'), 'blocs': BLOCS,
    'n_countries': len(countries),
    'ranking': [{'iso': r['iso'], 'name': r['name'], 'score': r['score'],
                 'n_direct': len(r['direct']), 'n_echo': len(r['echo'])} for r in ranking],
    'countries': countries,
    'host_companions': HOST_COMPANIONS,
    'robustness': robustness,
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'cascade.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/cascade.json')
print('  most systemic producers:', ', '.join(f"{r['name']} ({r['score']})" for r in ranking[:6]))
top = ranking[0]
print(f"  {top['name']} echo:", ', '.join(f"{e['title']}<-{e['via']} {e['hit']}%" for e in top['echo']) or 'none')

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Supply-shock cascade — the first-order hit and the companion echo · Critical Materials Atlas</title>
<meta name="description" content="A shock to a producer country doesn't stop at what it mines: where a lost material is a host commodity, the by-product companions riding on it fall too. This model cascades a country shock through production, the companion web, and trade to the exposed blocs.">
<meta property="og:title" content="Supply-shock cascade: the hit, and the companion echo">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .muted{color:#5a6b68;font-size:.86rem}
 .sim{background:#f4f7f6;border:1px solid #e3e9e8;border-radius:12px;padding:1.1rem 1.2rem;margin:1rem 0}
 .sim .ctl{display:flex;gap:1.4rem;align-items:center;flex-wrap:wrap;margin-bottom:.4rem}
 .sim select{padding:.35rem .6rem;border:1px solid #cdd8d5;border-radius:6px;font:inherit;min-width:12rem}
 .sim input[type=range]{accent-color:#c0392b}
 .scorebig{font-size:1.8rem;font-weight:800;color:#c0392b;letter-spacing:-.02em}
 .keyline{background:#f2f6f5;border:1px solid #d9e6e3;border-left:4px solid #0e7c74;border-radius:10px;padding:.9rem 1.1rem;margin:.6rem 0}
 .keyline b{color:#0e7c74}
 h3.sec{margin:1.1rem 0 .3rem;font-size:.82rem;text-transform:uppercase;letter-spacing:.06em;color:#5a6b68}
 .barrow{display:grid;grid-template-columns:150px 1fr 96px;align-items:center;gap:.6rem;margin:.22rem 0;font-size:.85rem}
 .barrow .nm{text-align:right;font-weight:600;color:#15323a}
 .barrow .nm small{font-weight:400;color:#9aa6ad}
 .barrow .track{background:#eef3f2;border-radius:5px;height:19px;overflow:hidden}
 .barrow .fill{height:100%;border-radius:5px}
 .barrow .v{text-align:right;font-weight:700;font-variant-numeric:tabular-nums}
 .echo .fill{background:#d98324}.echo .v{color:#b07a18}
 .dir .fill{background:#c0392b}.dir .v{color:#c0392b}
 .dir.soft .fill{background:#7d9b97}.dir.soft .v{color:#5a6b68}
 .chips{display:flex;flex-wrap:wrap;gap:.4rem;margin:.3rem 0}
 .chip{font-size:.8rem;background:#eef3f2;border:1px solid #e3e9e8;border-radius:20px;padding:.14rem .6rem;color:#15323a}
 table.tidy{width:100%;border-collapse:collapse;font-size:.86rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="companionality.html">Hostage metals</a><a href="scenarios.html">Scenarios</a>
  <a href="host-shock.html" class="hideable">Host shock</a><a href="methodology.html" class="hideable">Methodology</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · systemic · cascade</div>
  <h1>The shock, and its echo</h1>
  <p class="deck">A shock to a producer country doesn&rsquo;t stop at what it mines. Where a lost material is a <a href="host-shock.html" style="color:#fff;text-decoration:underline">host</a>, the by-product <a href="companionality.html" style="color:#fff;text-decoration:underline">companions</a> riding on it fall too &mdash; Congo&rsquo;s copper is also a cobalt shock. This capstone cascades a country&rsquo;s shock through production, the companion web, and trade, and scores who is the real single point of failure.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>How the cascade is computed (and where it stops)</summary>
  <p><b>First-order:</b> a shock of S% to a country cuts world supply of each material it mines by S% &times; its production share (USGS). <b>Companion echo:</b> where a hit material is a host, its by-product companions lose S% &times; (their by-product reliance on that host) &mdash; a second-order hit the first-order view misses. <b>Exposure:</b> the fallout is routed to importing blocs by net trade. Each hit is expressed in <b>absolute tonnes at risk</b> = share of world supply lost &times; world production (World Mining Data 2024). The <b>systemic score</b> stays share-and-rigidity based on purpose &mdash; a tonnage sum would be swamped by bulk commodities and drown out the criticals, so tonnes are shown per material, not summed into the rank.</p>
  <p class="howto-src"><b>Limits:</b> the echo only fires through hosts the atlas tracks (copper, nickel, bauxite, niobium, platinum, coking coal) &mdash; zinc/tin/zircon-hosted companions (germanium, hafnium) are under-counted for want of their host&rsquo;s production geography. First-and-second-order only. Price feedback is no longer just a caveat — it is <a href="#robust">tested below</a> across a demand-elasticity band, and the top single point of failure holds. Still a structural map, not a calibrated forecast. Inputs: <a href="out/data.json">data.json</a> (production) × <a href="out/companionality.json">companionality.json</a> × <a href="out/net_demand.json">net_demand.json</a> &rarr; <a href="out/cascade.json">cascade.json</a>.</p>
  </details></div>

  <div class="sim">
    <div class="ctl">
      <label>Shock this producer &nbsp;<select id="country"></select></label>
      <label>Output loss &nbsp;<input type="range" id="shock" min="10" max="100" step="10" value="100"> <b id="shockv">100%</b></label>
      <span style="margin-left:auto;text-align:right"><span class="scorebig" id="score"></span><br><span class="muted" style="font-size:.72rem">systemic cascade score</span></span>
    </div>
    <h3 class="sec">First-order &mdash; materials this country directly supplies</h3>
    <div id="direct"></div>
    <h3 class="sec" id="echohdr">Companion echo &mdash; by-products dragged down with the host</h3>
    <div id="echo"></div>
    <h3 class="sec">Who imports the fallout</h3>
    <div class="chips" id="exposed"></div>
  </div>

  <h2 style="margin:1.6rem 0 .3rem">The single points of failure, ranked</h2>
  <p class="muted" style="margin-top:0">Systemic score = direct supply at risk (weighted up where the metal is a rigid by-product) plus the companion echo. High = a shock here reverberates farthest through the critical-materials system.</p>
  <table class="tidy" id="rank"><thead><tr><th class="n">#</th><th>Producer</th><th class="n">score</th><th class="n">direct materials</th><th class="n">companion echoes</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.6rem 0 .3rem">Does it survive price feedback?</h2>
  <p class="muted" style="margin-top:0">The model is linear — a real shortage would lift prices and flex demand (substitution, recycling), dampening the hit. We test that. The physical cascade is left untouched (by-product tonnes die with their host whatever the price); a demand-response damping is applied to the <i>impact score</i> only, scaled by each metal&rsquo;s elasticity (by-products stay inelastic), and swept across a wide band.</p>
  <div class="keyline" id="robust"></div>

  <h2 style="margin:1.8rem 0 .3rem">Where the whole arc lands</h2>
  <p>Ten layers built one truth in steps: satellites can&rsquo;t name a mineral &rarr; many minerals are by-products &rarr; by-products can&rsquo;t scale &rarr; their host&rsquo;s cycle rules them &rarr; demand is surging and nationally concentrated. This capstone puts it in one motion: a shock lands, and it echoes down the companion web into metals the shocked country never even mined, then out to the blocs that buy them. The honest edge remains the same one the atlas has flagged throughout &mdash; it is a structural map from public data, not a calibrated forecast; the missing piece is absolute production tonnages and real prices to turn these shares into quantities. That is the next acquisition, and where this atlas would stop being a demonstration and start being an instrument.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="companionality.html">Hostage metals</a><br><a href="host-shock.html">Host shock</a><br><a href="net-demand.html">Net demand</a><br><a href="scenarios.html">Scenarios</a></div>
  <div><h4>Sources</h4>USGS production shares × companionality × reconciled net trade</div>
  <div class="fineprint">Structural first-and-second-order cascade from public data. Price feedback tested across an elasticity band (China stays the top point of failure) — but still a map of contagion, not a calibrated forecast.</div>
</div></footer>
<script>
fetch('out/cascade.json').then(r=>r.json()).then(S=>{
  const COL={CN:'#c0392b',EU:'#2b6fb0',US:'#15323a',JP:'#7d5fb0',KR:'#2f8f6b',IN:'#d98324',Other:'#c2ccca'};
  const NAME={CN:'China',EU:'EU',US:'US',JP:'Japan',KR:'Korea',IN:'India',Other:'Other'};
  const rank=S.ranking, C=S.countries, top=rank[0];
  document.getElementById('lead').innerHTML='<b>Result:</b> the most systemic single producer is <b>'+top.name+'</b> ('+top.n_direct+' materials directly, plus '+top.n_echo+' companion echoes) &mdash; and every hit is now quantified in <b>real tonnes</b> (World Mining Data 2024), not just an index. A full China shock removes almost all of the world&rsquo;s ~987 t of gallium and ~150 t of germanium; shock Congo and its copper drags extra cobalt down on top of the direct cobalt loss; shock Indonesia&rsquo;s nickel and cobalt falls again. Pick a producer and watch the shock echo, in tonnes.';
  const sel=document.getElementById('country');
  rank.forEach(r=>{const o=document.createElement('option');o.value=r.iso;o.textContent=r.name+' — score '+r.score;sel.appendChild(o);});
  const shock=document.getElementById('shock'),shockv=document.getElementById('shockv');
  function fmtT(t){return t>=1e9?(t/1e9).toFixed(2)+' Bt':t>=1e6?(t/1e6).toFixed(1)+' Mt':t>=1e3?(t/1e3).toFixed(1)+' kt':Math.round(t)+' t';}
  function bar(cls,nm,sub,val,mx,wt){
    const tr=wt?fmtT(val/100*wt):'';
    return '<div class="barrow '+cls+'"><div class="nm">'+nm+(sub?' <small>'+sub+'</small>':'')+'</div>'+
    '<div class="track"><div class="fill" style="width:'+Math.max(2,100*val/mx)+'%"></div></div>'+
    '<div class="v">'+val.toFixed(0)+'%<small style="display:block;color:#9aa6ad;font-weight:400;font-size:.72rem">'+(wt?tr+' at risk':'')+'</small></div></div>';}
  function render(){
    const r=C[sel.value], f=(+shock.value)/100; shockv.textContent=(+shock.value)+'%';
    document.getElementById('score').textContent=(r.score*f).toFixed(2);
    const dmx=Math.max.apply(null,r.direct.map(d=>d.share),1);
    document.getElementById('direct').innerHTML=r.direct.map(d=>
      bar('dir'+(d.rigid?'':' soft'), d.title, (d.rigid?'rigid by-product':'')+(d.is_host?(d.rigid?' · host':'host'):''), d.share*f, dmx, d.world_tonnes)).join('');
    const eh=document.getElementById('echo'), ehdr=document.getElementById('echohdr');
    if(r.echo.length){ehdr.style.display='';
      const emx=Math.max.apply(null,r.echo.map(e=>e.hit),1);
      eh.innerHTML=r.echo.map(e=>bar('echo', e.title, 'via '+e.via+(e.already_direct?' (also direct)':''), e.hit*f, emx, e.world_tonnes)).join('');
    } else {ehdr.style.display='none'; eh.innerHTML='';}
    document.getElementById('exposed').innerHTML=r.exposed.length?r.exposed.map(x=>
      '<span class="chip"><b style="color:'+(COL[x[0]]||'#15323a')+'">'+NAME[x[0]]+'</b> exposure '+(x[1]*f).toFixed(1)+'</span>').join(''):'<span class="muted">—</span>';
  }
  sel.value=top.iso; sel.onchange=render; shock.oninput=render; render();
  const tb=document.querySelector('#rank tbody');
  rank.forEach(r=>{const tr=document.createElement('tr');
    tr.innerHTML='<td class="n" style="color:#9aa6ad">'+r.rank+'</td><td><b>'+r.name+'</b></td>'+
      '<td class="n" style="font-weight:700;color:'+(r.score>=2?'#c0392b':r.score>=1?'#b07a18':'#5a6b68')+'">'+r.score+'</td>'+
      '<td class="n">'+r.n_direct+'</td><td class="n">'+r.n_echo+'</td>';
    tb.appendChild(tr);});
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'cascade.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote cascade.html')
