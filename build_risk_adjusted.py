#!/usr/bin/env python3
"""
Companionality-adjusted supply risk — what happens when you admit that supply can't always respond.

Child of the companionality layer. The transparent risk index (build_risk.py) blends production/refining/
trade concentration + opacity, then discounts for recyclability. But it implicitly assumes a shortage pulls
in new supply. For by-product metals that is false: no gallium price builds a gallium mine. This layer
re-weights the risk score by a SUPPLY-RESPONSE factor = 1 + 0.5 x companionality/100 (a 100%-by-product metal
carries +50% because its supply cannot answer its own price), then re-ranks. The point is the MOVEMENT: which
materials the market's "just mine more" assumption most under-rates. Public data; deterministic.
Run: python build_risk_adjusted.py
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
risk = json.load(open(os.path.join(ROOT, 'out', 'risk.json'), encoding='utf8'))
comp = json.load(open(os.path.join(ROOT, 'out', 'companionality.json'), encoding='utf8'))
CO = {r['label']: r for r in comp['rows']}
ALPHA = 0.5  # max amplification at 100% companionality

base = risk['materials']
base_rank = {r['label']: i + 1 for i, r in enumerate(sorted(base, key=lambda r: -r['score']))}

rows = []
for r in base:
    lab = r['label']
    c = CO.get(lab, {})
    cp = c.get('companionality_pct', 0)
    factor = 1 + ALPHA * cp / 100.0
    adj = round(r['score'] * factor, 1)
    rows.append({
        'label': lab, 'title': c.get('title', r['title']),
        'base': r['score'], 'companionality_pct': cp, 'class': c.get('class', 'primary'),
        'hosts': c.get('hosts', []), 'factor': round(factor, 2), 'adjusted': adj,
    })

adj_sorted = sorted(rows, key=lambda r: -r['adjusted'])
for i, r in enumerate(adj_sorted, 1):
    r['adj_rank'] = i
    r['base_rank'] = base_rank[r['label']]
    r['rank_delta'] = r['base_rank'] - r['adj_rank']   # positive = rose in the ranking

# levers per supply class (what you actually do about it)
LEVER = {'byproduct': 'recovery yield at host · stockpile · substitute (no new mine possible)',
         'mixed': 'partial: some new primary supply, plus recovery/stockpile',
         'primary': 'new mines can respond to price'}

risers = [r for r in adj_sorted if r['rank_delta'] >= 2]
out = {
    'generated': risk.get('generated') or comp.get('generated'),
    'alpha': ALPHA,
    'n': len(rows),
    'n_risers': len(risers),
    'top_riser': (max(rows, key=lambda r: r['rank_delta'])['title']),
    'rows': adj_sorted,
    'levers': LEVER,
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'risk_adjusted.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/risk_adjusted.json')
print('  biggest risers:', ', '.join(f"{r['title']} (+{r['rank_delta']})"
      for r in sorted(rows, key=lambda r: -r['rank_delta'])[:5]))

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>When supply can't respond — companionality-adjusted risk · Critical Materials Atlas</title>
<meta name="description" content="Standard supply-risk scores assume a shortage summons new production. For by-product metals it can't. This layer re-weights the risk index by supply elasticity and shows which materials the market most under-rates.">
<meta property="og:title" content="When supply can't respond: risk the market under-rates">
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
 .stat.warn{border-left-color:#c0392b}.stat.warn .v{color:#c0392b}
 table.tidy{width:100%;border-collapse:collapse;font-size:.88rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .up{color:#c0392b;font-weight:700}.dn{color:#3f9b46}.fl{color:#9aa6ad}
 .tag{display:inline-block;font-size:.7rem;font-weight:700;padding:.06rem .45rem;border-radius:20px}
 .tag.b{background:#fbe9e7;color:#c0392b}.tag.m{background:#fff4e2;color:#b07a18}.tag.p{background:#eaf3f1;color:#0e7c74}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="risk.html">Risk</a><a href="companionality.html">Hostage metals</a>
  <a href="riskmethods.html" class="hideable">Risk methods</a><a href="methodology.html" class="hideable">Methodology</a>
  <a href="https://github.com/materials-atlas/comtrade-reconcile" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · risk · supply elasticity</div>
  <h1>When supply can&rsquo;t respond</h1>
  <p class="deck">Every supply-risk score quietly assumes the market can answer a shortage by producing more. For the <a href="companionality.html" style="color:#fff;text-decoration:underline">by-product metals</a> that assumption breaks &mdash; you can&rsquo;t open a gallium mine. This layer re-weights the <a href="risk.html" style="color:#fff;text-decoration:underline">risk index</a> by how elastic each material&rsquo;s supply actually is, and asks: which materials does &ldquo;just mine more&rdquo; most under-rate?</p>
</div></section>
<article style="max-width:1000px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>How the adjustment works</summary>
  <p>We take the transparent <a href="risk.html">risk score</a> and multiply it by a <b>supply-response factor</b> = 1 + 0.5 &times; companionality/100. A material mined for itself (companionality 0) is unchanged; a 100%-by-product metal is amplified 50%, because its supply cannot respond to its own price no matter how high risk climbs. We then re-rank and report the <b>movement</b> &mdash; the rank change is the message, not the absolute value.</p>
  <p class="howto-src"><b>Caveat:</b> the 0.5 amplitude is a deliberate, legible choice, not an estimated elasticity; treat this as a re-ordering lens, not a new cardinal score. Inputs: <a href="out/risk.json">risk.json</a> &times; <a href="out/companionality.json">companionality.json</a> &rarr; <a href="out/risk_adjusted.json">risk_adjusted.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <h2 style="margin:1.6rem 0 .3rem">Re-ranked by whether supply can actually respond</h2>
  <p class="muted" style="margin-top:0">Base = the standard risk score. Adjusted = after penalising inelastic (by-product) supply. <span class="up">▲</span> = the market under-rates this material; the lever column is what you can actually do about a shortage.</p>
  <table class="tidy" id="tab"><thead><tr><th class="n">#</th><th>Material</th><th>supply type</th><th class="n">base risk</th><th class="n">by-prod %</th><th class="n">adjusted</th><th class="n">rank Δ</th><th>mitigation lever</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.8rem 0 .3rem">What this changes, and what it spawns</h2>
  <p>The re-ranking pushes the hostage metals &mdash; gallium, germanium, cobalt, vanadium &mdash; up past materials whose risk is real but <i>addressable</i> with new mines. That has a policy edge: for the risers, building capacity is not the lever; <b>recovery yield at the host, stockpiling, and substitution</b> are. It also seeds the next layer &mdash; a <b>host-shock model</b>: if the market can only give you more gallium by smelting more aluminium, then an aluminium downturn is a gallium shock. That is the child this page asks for next.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="risk.html">Supply-risk index</a><br><a href="companionality.html">Hostage metals</a><br><a href="scenarios.html">Shock scenarios</a><br><a href="methodology.html">Methodology</a></div>
  <div><h4>Sources</h4>Risk index (USGS/IEA/trade) × companionality (USGS MCS 2024 · Nassar et al. 2015)</div>
  <div class="fineprint">A re-ordering lens: the supply-response amplitude (0.5) is a legible choice, not an estimated elasticity.</div>
</div></footer>
<script>
fetch('out/risk_adjusted.json').then(r=>r.json()).then(S=>{
  document.getElementById('lead').innerHTML='<b>Result:</b> once you penalise supply that can&rsquo;t respond to price, <b>'+S.n_risers+'</b> materials climb the risk ranking &mdash; led by <b>'+S.top_riser+'</b>. The move is systematic: by-product metals rise past materials whose risk, however high, can at least be answered with new mines.';
  const stats=[
    {v:S.n_risers,l:'materials the standard risk score under-rates (rise ≥2 ranks)',warn:true},
    {v:'+'+Math.max.apply(null,S.rows.map(r=>r.rank_delta)),l:'biggest jump ('+S.top_riser+')',warn:true},
    {v:S.rows.filter(r=>r['class']==='byproduct').length,l:'by-product-locked materials, all amplified'},
    {v:'×'+(1+S.alpha),l:'maximum amplification (at 100% companionality)'},
  ];
  document.getElementById('stats').innerHTML=stats.map(s=>'<div class="stat'+(s.warn?' warn':'')+'"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  const tagc={byproduct:'b',mixed:'m',primary:'p'},tagt={byproduct:'by-product',mixed:'mixed',primary:'primary'};
  const tb=document.querySelector('#tab tbody');
  S.rows.forEach(r=>{
    const d=r.rank_delta;
    const dcell=d>0?'<span class="up">▲ '+d+'</span>':d<0?'<span class="dn">▼ '+(-d)+'</span>':'<span class="fl">—</span>';
    const tr=document.createElement('tr');
    tr.innerHTML='<td class="n fl">'+r.adj_rank+'</td>'+
      '<td><b>'+r.title+'</b></td>'+
      '<td><span class="tag '+tagc[r['class']]+'">'+tagt[r['class']]+'</span></td>'+
      '<td class="n">'+r.base+'</td>'+
      '<td class="n">'+r.companionality_pct+'</td>'+
      '<td class="n" style="font-weight:700">'+r.adjusted+'</td>'+
      '<td class="n">'+dcell+'</td>'+
      '<td class="muted" style="font-size:.8rem">'+S.levers[r['class']]+'</td>';
    tb.appendChild(tr);
  });
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'risk-adjusted.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote risk-adjusted.html')
