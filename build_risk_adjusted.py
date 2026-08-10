#!/usr/bin/env python3
"""
Companionality-adjusted supply risk — what happens when you admit that supply can't always respond.

Child of the companionality layer. The transparent risk index (build_risk.py) blends production/refining/
trade concentration + opacity, then discounts for recyclability. But it implicitly assumes a shortage pulls
in new supply. For by-product metals that is false: no gallium price builds a gallium mine. This layer
re-weights the risk score by a SUPPLY-RESPONSE factor derived from supply-shock economics, then re-ranks.
The point is the MOVEMENT: which materials the market's "just mine more" assumption most under-rates.

Economic grounding of the factor (not an ad-hoc linear boost):
  The scarcity impact of a supply disruption scales INVERSELY with supply elasticity — an outage bites harder
  when output can't respond. So vulnerability ~ 1/(1+eps). We infer a metal's long-run supply elasticity from
  its companionality: a primary metal can scale (eps ~ EPS0), a pure by-product cannot (eps ~ 0):
      eps(c) = EPS0 * (1 - c/100)
      factor = (1+EPS0) / (1 + eps(c))      # normalised so a primary metal = 1.0, a by-product = 1+EPS0
  EPS0 is the representative long-run supply elasticity of a scalable PRIMARY metal, calibrated to the published
  range (base-metal long-run supply is substantially elastic — Radetzki 2008; Krautkraemer 1998; Stuermer 2017).
  Note the old linear form 1 + EPS0*(c/100) is just the first-order approximation of this, so EPS0 IS the max
  amplification and has a real structural meaning (it's the primary-metal elasticity), not a free knob.
Public data; deterministic. Run: python build_risk_adjusted.py
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
risk = json.load(open(os.path.join(ROOT, 'out', 'risk.json'), encoding='utf8'))
comp = json.load(open(os.path.join(ROOT, 'out', 'companionality.json'), encoding='utf8'))
CO = {r['label']: r for r in comp['rows']}
EPS0 = 0.5  # representative long-run supply elasticity of a scalable primary metal (conservative vs the literature)

# ---- value-share refinement (open reproduction of Mineral Economics 2026 companionality-risk metric) ----
# The 2026 metric derives a companion's perceived own-price supply elasticity from its VALUE SHARE within the
# host operation, not just its by-product share: a metal that is 0.1% of a mine's revenue can't move that mine,
# but one that is 40% can. We approximate the value share from open reference figures (USGS MCS 2024 production x
# representative 2024 prices): phi = (primary fraction)x1 + (by-product fraction)x[companion rev / (companion+host rev)].
# Then eps = EPS0*phi, same inverse-elasticity form. Honest limit: the companion/host revenue ratio is GLOBAL, so it
# understates phi for geographically concentrated cases (DRC cobalt is a bigger revenue share at its own mines).
import csv as _csv
_ECON_F = os.path.join(ROOT, 'raw', 'valueshare', 'metal_econ.csv')
ECON = {}
if os.path.exists(_ECON_F):
    for _r in _csv.DictReader(open(_ECON_F, encoding='utf-8')):
        ECON[_r['name']] = (float(_r['world_prod_t']), float(_r['price_usd_per_t']))
HALIAS = {'steel slag': 'iron', 'mineral sands': 'zirconium'}
def value_share(lab, cp, hs):
    if lab not in ECON:
        return None
    Qm, Pm = ECON[lab]; comp_rev = Qm * Pm
    host = next((HALIAS.get(h, h) for h in hs if HALIAS.get(h, h) in ECON), None)
    rev_share = 0.0
    if cp > 0 and host:
        Qh, Ph = ECON[host]; rev_share = comp_rev / (comp_rev + Qh * Ph)
    return (1 - cp / 100.0) + (cp / 100.0) * rev_share   # primary fraction weight 1, by-product fraction = revenue share

base = risk['materials']
base_rank = {r['label']: i + 1 for i, r in enumerate(sorted(base, key=lambda r: -r['score']))}

rows = []
for r in base:
    lab = r['label']
    c = CO.get(lab, {})
    cp = c.get('companionality_pct', 0)
    eps = EPS0 * (1 - cp / 100.0)          # implied long-run supply elasticity: ~EPS0 for primary, ~0 for by-product
    factor = (1 + EPS0) / (1 + eps)        # supply-shock vulnerability ~ 1/(1+elasticity), normalised so primary = 1
    adj = round(r['score'] * factor, 1)
    # value-share refinement (Mineral Economics 2026 method)
    phi = value_share(lab, cp, c.get('hosts', []))
    eps_vs = EPS0 * phi if phi is not None else None
    factor_vs = round((1 + EPS0) / (1 + eps_vs), 2) if eps_vs is not None else None
    rows.append({
        'label': lab, 'title': c.get('title', r['title']),
        'base': r['score'], 'companionality_pct': cp, 'class': c.get('class', 'primary'),
        'hosts': c.get('hosts', []), 'implied_elasticity': round(eps, 2), 'factor': round(factor, 2), 'adjusted': adj,
        'value_share': round(phi, 3) if phi is not None else None,
        'implied_elasticity_vs': round(eps_vs, 3) if eps_vs is not None else None,
        'factor_vs': factor_vs,
        'adjusted_vs': round(r['score'] * factor_vs, 1) if factor_vs is not None else None,
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
# value-share vs companionality comparison: where the two methods agree, and where value-weighting refines
_vs = [r for r in rows if r.get('factor_vs') is not None and r['companionality_pct'] > 0]
_vs.sort(key=lambda r: -r['companionality_pct'])
_biggest_refine = sorted(_vs, key=lambda r: -(r['factor'] - r['factor_vs']))[:3]
out = {
    'generated': risk.get('generated') or comp.get('generated'),
    'alpha': EPS0,
    'eps0': EPS0,
    'n': len(rows),
    'n_risers': len(risers),
    'top_riser': (max(rows, key=lambda r: r['rank_delta'])['title']),
    'rows': adj_sorted,
    'levers': LEVER,
    'valueshare': _vs,
    'valueshare_refines': [r['title'] for r in _biggest_refine],
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
 .keyline{background:#f2f6f5;border:1px solid #d9e6e3;border-left:4px solid #0e7c74;border-radius:10px;padding:.9rem 1.1rem;margin:1rem 0;font-size:.9rem;line-height:1.6}
 .keyline b{color:#0e7c74}
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
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · risk · supply elasticity</div>
  <h1>When supply can&rsquo;t respond</h1>
  <p class="deck">Every supply-risk score quietly assumes the market can answer a shortage by producing more. For the <a href="companionality.html" style="color:#fff;text-decoration:underline">by-product metals</a> that assumption breaks &mdash; you can&rsquo;t open a gallium mine. This layer re-weights the <a href="risk.html" style="color:#fff;text-decoration:underline">risk index</a> by how elastic each material&rsquo;s supply actually is, and asks: which materials does &ldquo;just mine more&rdquo; most under-rate?</p>
</div></section>
<article style="max-width:1000px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>How the adjustment works</summary>
  <p>We take the transparent <a href="risk.html">risk score</a> and multiply it by a <b>supply-response factor</b> derived from supply-shock economics. The scarcity impact of a disruption scales <i>inversely</i> with supply elasticity &mdash; an outage bites harder when output can&rsquo;t respond &mdash; so vulnerability &prop; 1/(1+&epsilon;). We infer each metal&rsquo;s long-run supply elasticity from its companionality (a primary metal can scale, &epsilon; &asymp; &epsilon;<sub>0</sub>; a pure by-product cannot, &epsilon; &asymp; 0): &nbsp;<b>&epsilon;(c) = &epsilon;<sub>0</sub>(1 &minus; c/100)</b>, &nbsp;<b>factor = (1+&epsilon;<sub>0</sub>)/(1+&epsilon;(c))</b>, normalised so a primary metal is unchanged and a 100%-by-product carries the full 1+&epsilon;<sub>0</sub>. We then re-rank and report the <b>movement</b> &mdash; the rank change is the message, not the absolute value.</p>
  <p class="howto-src"><b>What makes &epsilon;<sub>0</sub> = 0.5 defensible, not arbitrary.</b> It now has a structural meaning: it is the <b>long-run supply elasticity of a scalable primary metal</b>. The literature supports the two endpoints the model rests on &mdash; every non-fuel mineral is <b>price-inelastic in the short run</b> (mines can&rsquo;t be built quickly: <a href="https://doi.org/10.1007/s13563-025-00537-3" target="_blank" rel="noopener">USGS / Fernandez 2025</a>, 74 commodities; <a href="https://econpapers.repec.org/RePEc:mns:wpaper:wp202002" target="_blank" rel="noopener">Dahl MEDS</a>), while <b>long-run primary supply is substantially elastic</b> (<a href="https://www.dallasfed.org/-/media/documents/research/papers/2014/wp1413.pdf" target="_blank" rel="noopener">Stuermer 2017</a>; Radetzki 2008; Krautkraemer 1998) &mdash; so &epsilon;<sub>0</sub>&nbsp;=&nbsp;0.5 is <i>conservative</i> (higher published values would only deepen the by-product penalty). And <b>companion supply really is host-locked</b>: the most rigorous open model of a by-product &mdash; the copper&ndash;cobalt&ndash;nickel supply-curve system (<a href="https://www.nature.com/articles/s41467-025-62570-8" target="_blank" rel="noopener">Nature Communications 2025</a>, ~99% of cobalt a by-product) &mdash; is built on exactly this mechanism. <b>Honest ceiling:</b> per-material long-run elasticities are <i>not</i> published for the critical by-products (they&rsquo;re too hard to estimate &mdash; the thesis itself), and the gold-standard structural models need proprietary cost curves. We tried estimating own-price response from 8 years of BACI trade data; too noisy (re-exports, quality mix, shared Ga/Ge/Hf HS code) to trust. So &epsilon;(c) is a <b>calibrated inference from companionality, not a measurement</b> &mdash; a re-ordering lens grounded in the economics, not a cardinal elasticity. Inputs: <a href="out/risk.json">risk.json</a> &times; <a href="out/companionality.json">companionality.json</a> &rarr; <a href="out/risk_adjusted.json">risk_adjusted.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <h2 style="margin:1.6rem 0 .3rem">Re-ranked by whether supply can actually respond</h2>
  <p class="muted" style="margin-top:0">Base = the standard risk score. Adjusted = after penalising inelastic (by-product) supply. <span class="up">▲</span> = the market under-rates this material; the lever column is what you can actually do about a shortage.</p>
  <table class="tidy" id="tab"><thead><tr><th class="n">#</th><th>Material</th><th>supply type</th><th class="n">base risk</th><th class="n">by-prod %</th><th class="n">adjusted</th><th class="n">rank Δ</th><th>mitigation lever</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.8rem 0 .4rem">Refinement: does the by-product <i>pay</i> enough to move its host?</h2>
  <p class="muted" style="margin-top:0">By-product share alone treats every companion the same. But a metal that is <b>0.1% of a mine&rsquo;s revenue can&rsquo;t move that mine, while one that is 40% can</b> — so its true supply response depends on its <b>value share</b> in the host operation. This is the method of the peer-reviewed <a href="https://link.springer.com/article/10.1007/s13563-026-00640-z" target="_blank" rel="noopener">Mineral Economics 2026</a> companionality-risk metric (perceived elasticity from revenue weight). We reproduce it on open data — production &times; price — and set it beside the companionality-only factor:</p>
  <table class="tidy" id="vstab"><thead><tr><th>Metal</th><th class="n">by-prod %</th><th class="n">value share</th><th class="n">factor: companionality</th><th class="n">factor: value-share</th></tr></thead><tbody></tbody></table>
  <div class="keyline" id="vskey"></div>

  <h2 style="margin:1.8rem 0 .3rem">What this changes, and what it spawns</h2>
  <p>The re-ranking pushes the hostage metals &mdash; gallium, germanium, cobalt, vanadium &mdash; up past materials whose risk is real but <i>addressable</i> with new mines. That has a policy edge: for the risers, building capacity is not the lever; <b>recovery yield at the host, stockpiling, and substitution</b> are. It also seeds the next layer &mdash; a <b>host-shock model</b>: if the market can only give you more gallium by smelting more aluminium, then an aluminium downturn is a gallium shock. That is the child this page asks for next.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="risk.html">Supply-risk index</a><br><a href="companionality.html">Hostage metals</a><br><a href="scenarios.html">Shock scenarios</a><br><a href="methodology.html">Methodology</a></div>
  <div><h4>Sources</h4>Risk index (USGS/IEA/trade) × companionality (USGS MCS 2024 · Nassar et al. 2015)</div>
  <div class="fineprint">A re-ordering lens: the supply-response amplitude (0.5) is a legible choice grounded in the elasticity literature (short-run supply inelastic for all minerals; long-run response low for by-products), not a per-material estimated elasticity.</div>
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
  // value-share refinement comparison
  if(S.valueshare && S.valueshare.length){
    const vt=document.querySelector('#vstab tbody');
    S.valueshare.forEach(r=>{
      const diff=r.factor-r.factor_vs, moved=diff>=0.05;
      const tr=document.createElement('tr');
      tr.innerHTML='<td><b>'+r.title+'</b></td><td class="n">'+r.companionality_pct+'%</td>'+
        '<td class="n">'+(r.value_share*100).toFixed(1)+'%</td>'+
        '<td class="n">×'+r.factor.toFixed(2)+'</td>'+
        '<td class="n" style="font-weight:700;color:'+(moved?'#0e7c74':'#5a6b68')+'">×'+r.factor_vs.toFixed(2)+(moved?' ↓':'')+'</td>';
      vt.appendChild(tr);
    });
    document.getElementById('vskey').innerHTML='<b style="color:#0e7c74">Agree on the extremes, refine the middle.</b> For the trace by-products (gallium, germanium, arsenic ~0% of their host&rsquo;s revenue) both methods give the full <b>×1.5</b> penalty — supply cannot respond either way. The value-share method <b>eases the penalty for companions that actually pay their way</b> — most for <b>'+S.valueshare_refines.join(', ')+'</b> (palladium and platinum are 38–77% of their operations&rsquo; revenue, so a price rise genuinely pulls out more). That is the economically-correct correction, and it reproduces the Mineral Economics 2026 metric on open data. <b>Honest limit:</b> the companion/host revenue ratio here is <i>global</i>, so it understates the share for geographically concentrated cases — cobalt is a far bigger slice of revenue at a DRC copper–cobalt mine than the world ratio implies, so its true factor sits between the two columns.';
  }
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'risk-adjusted.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote risk-adjusted.html')
