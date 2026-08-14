#!/usr/bin/env python3
"""
Price test — does the market already show the squeeze?

Child of the demand/squeeze arm, and a falsifier for it. The squeeze thesis says: where demand rises and
supply is by-product-locked (inelastic), pressure has nowhere to go but price. So test it against the atlas's
own implied-price series — the world unit value (trade value / quantity, $/tonne) from BACI, 2002-2024. For
each material compute the recent price change (2018->2024), then correlate against the squeeze index and
companionality. Report what the data says, honestly, including where it refutes a naive reading.

Expected (and found): the story is NOT a clean correlation. Supply-locked metals under fresh supply stress
(gallium, germanium — hit by 2023 export controls) show sharp price jumps; but a by-product can also be
OVER-supplied when its host booms (cobalt crashed as Indonesian nickel surged). Same structure, opposite
prices: what companionality does not do is fix the direction. That nuance is the finding. Public data.
Run: python build_price_squeeze.py

*** SUPERSEDED IN PART — see build_price_volatility.py / price-volatility.html ***
This page's volatility claim (by-product metals more volatile, 37% vs 31%) DID NOT SURVIVE retesting and is
retracted here. Two reasons, both fatal to it:
  1. NO SIZE CONTROL. The comparison is mean-vs-mean, so it cannot separate "supply is stuck" from "market
     is small". By-product metals are ~174x smaller markets. On real USGS prices with a market-size control,
     the by-product effect collapses to noise while size takes all the significance.
  2. THE PROXY DOESN'T MEASURE IT. Trade unit-value volatility correlates with real (USGS) price volatility
     at r=0.13 (p=0.52, n=27) — indistinguishable from no relationship. For volatility specifically, unit
     values are not a noisy measure; they are not a measure.
The price-CHANGE half of this page (direction: who rose, who crashed) is unaffected — that is a level
comparison over a common window, not a second-moment estimate, and gallium/germanium's 2023 export-control
spike and cobalt's Indonesian-nickel crash are real events, not artifacts. That half is kept.

The volatility half is REMOVED from this page and its data file rather than shown struck-through: a number
this page can no longer stand behind should not be sitting in an open JSON for someone to download and reuse.
It is not a silent deletion — the full record (what was claimed, what broke it, where the corrected version
lives) is on challenge.html, and the changelog entry stays in updates.html. The page keeps a one-line pointer.
"""
import json, os, math

ROOT = os.path.dirname(os.path.abspath(__file__))
vol = json.load(open(os.path.join(ROOT, 'out', 'volume.json'), encoding='utf8'))
dem = json.load(open(os.path.join(ROOT, 'out', 'demand.json'), encoding='utf8'))
comp = json.load(open(os.path.join(ROOT, 'out', 'companionality.json'), encoding='utf8'))
YEARS = vol['years']
DE = {r['label']: r for r in dem['rows']}
CO = {r['label']: r for r in comp['rows']}
iy = {y: i for i, y in enumerate(YEARS)}


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n; my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs); syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return round(sxy / math.sqrt(sxx * syy), 2)


def series_stats(uv):
    # recent price change 2018 -> 2024. NOTE: this used to also return a volatility, which the page
    # reported as evidence that by-product metals swing harder. That claim is withdrawn (see docstring)
    # and the computation is gone with it — unit values do not measure volatility (r=0.13 vs real prices).
    def at(y):
        i = iy.get(y)
        return uv[i] if i is not None and i < len(uv) and uv[i] and uv[i] > 0 else None
    p0, p1 = at(2018), at(2024)
    chg = round((p1 / p0 - 1) * 100, 1) if p0 and p1 else None
    # cagr 2018-24
    cagr = round(((p1 / p0) ** (1 / 6) - 1) * 100, 1) if p0 and p1 else None
    return p1, chg, cagr


# gallium & germanium share one HS6 code (811292) => identical trade unit values (hafnium is separate).
# They are ONE independent price signal, not three; flag them and de-duplicate for correlations.
SHARED = {'gallium', 'germanium'}
SHARED_KEEP = 'gallium'   # representative of the shared trio in the correlation sample

rows = []
for lab, mv in vol['materials'].items():
    de = DE.get(lab); co = CO.get(lab, {})
    if not de:
        continue
    price_2024, chg, cagr = series_stats(mv.get('uv') or [])
    rows.append({
        'label': lab, 'title': co.get('title', mv.get('title', lab)),
        'price_2024': round(price_2024) if price_2024 else None,
        'chg_18_24': chg, 'cagr_18_24': cagr,
        'squeeze': de['squeeze'], 'demand_growth_2040': de['demand_growth_2040'],
        'companionality_pct': de['companionality_pct'], 'class': de['class'],
        'shared_hs6': lab in SHARED,
    })

# de-duplicated sample for correlations: drop germanium & hafnium (keep gallium)
def dedup(rs):
    return [r for r in rs if not (r['shared_hs6'] and r['label'] != SHARED_KEEP)]
valid_chg = dedup([r for r in rows if r['chg_18_24'] is not None])
corr_sq_chg = pearson([r['squeeze'] for r in valid_chg], [r['chg_18_24'] for r in valid_chg])
corr_dg_chg = pearson([r['demand_growth_2040'] for r in valid_chg], [r['chg_18_24'] for r in valid_chg])


# the 7 by-product-locked metals: how their prices actually moved (the directional split)
locked = [r for r in rows if r['companionality_pct'] >= 66 and r['chg_18_24'] is not None]
up = [r for r in locked if r['chg_18_24'] > 20]
down = [r for r in locked if r['chg_18_24'] < -20]

rows.sort(key=lambda r: -(r['chg_18_24'] if r['chg_18_24'] is not None else -999))
out = {
    'generated': dem.get('generated'),
    'window': '2018-2024',
    'n': len(rows),
    'corr_squeeze_pricechange': corr_sq_chg,           # de-duplicated of the shared HS6 trio
    'corr_demandgrowth_pricechange': corr_dg_chg,
    'n_locked': len(locked),
    'locked_up': [r['title'] for r in up],
    'locked_down': [r['title'] for r in down],
    'shared_note': 'gallium & germanium share HS6 811292 — identical unit values; counted once in correlations (hafnium is separate).',
    'withdrawn_note': 'An earlier version of this page also reported a volatility comparison (by-product 37% '
                      'vs primary 31%). It is withdrawn and removed from this dataset: there was no control '
                      'for market size, and trade unit values do not track real price volatility (r=0.13 vs '
                      'USGS real prices). See price_volatility.json for the replacement, and challenge.html '
                      'for the full record.',
    'rows': rows,
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'price_squeeze.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/price_squeeze.json')
print(f"  corr(squeeze, price change 18-24, deduped) = {corr_sq_chg}")
print(f"  by-product-locked metals UP: {', '.join(out['locked_up'])} | DOWN: {', '.join(out['locked_down'])}")

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Does the market show the squeeze? — a price test · Critical Materials Atlas</title>
<meta name="description" content="A falsifiable test of the atlas's own squeeze thesis: do the by-product-locked, high-demand metals actually show it in their prices? We check the implied trade-price series 2018-2024 and report what the data says, including where it refutes a naive reading.">
<meta property="og:title" content="Does the market already show the squeeze? A price test">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .muted{color:#5a6b68;font-size:.86rem}
 #scatter{width:100%;height:480px}
 .stat4{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin:1.2rem 0}
 @media(max-width:720px){.stat4{grid-template-columns:repeat(2,1fr)}}
 .stat{background:#fff;border:1px solid #e3e9e8;border-left:4px solid #0e7c74;border-radius:10px;padding:.8rem .9rem}
 .stat .v{font-size:1.5rem;font-weight:800;color:#15323a;letter-spacing:-.02em}
 .stat .l{font-size:.76rem;color:#5a6b68;margin-top:.15rem;line-height:1.35}
 table.tidy{width:100%;border-collapse:collapse;font-size:.87rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .keyline{background:#f2f6f5;border:1px solid #d9e6e3;border-left:4px solid #0e7c74;border-radius:10px;padding:.9rem 1.1rem;margin:1.2rem 0}
 .keyline b{color:#0e7c74}
 .note{background:#f7f9f9;border:1px solid #e3e9e8;border-left:3px solid #b7c4c1;border-radius:8px;padding:.6rem .85rem;margin:1rem 0;font-size:.84rem;color:#5a6b68}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="demand.html">The squeeze</a><a href="volume.html">Prices</a>
  <a href="companionality.html" class="hideable">Hostage metals</a><a href="limitations.html" class="hideable">Limitations</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · demand · falsification</div>
  <h1>Does the market already show the squeeze?</h1>
  <p class="deck">The <a href="demand.html" style="color:#fff;text-decoration:underline">squeeze thesis</a> predicts that where demand rises and supply is by-product-locked, pressure escapes into price. That is a testable claim &mdash; so test it. This page checks the atlas&rsquo;s own implied-price series against the squeeze, and reports what the data says, including where it <i>refuses</i> to cooperate.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>How the price test is built (and its limits)</summary>
  <p>Price = the <b>implied world unit value</b> (trade value &divide; quantity, $/tonne) from BACI, per material, 2002&ndash;2024 &mdash; the same series behind the <a href="volume.html">value-vs-volume page</a>. We take the 2018&rarr;2024 change and correlate it across materials against the <a href="demand.html">squeeze index</a> and companionality.</p>
  <p class="howto-src"><b>Limits (important):</b> trade unit values are <i>not</i> spot prices &mdash; they mix grade, product form and contract lags, are <b>nominal</b> (not inflation-adjusted), and are noisy for thinly-traded materials. <b>Gallium and germanium share one HS6 code (811292)</b>, so they carry <i>identical</i> unit values (marked ⛓) &mdash; counted once in the correlations, not twice (hafnium is a separate line). This is a directional corroboration test, not a price model; a weak or mixed correlation is a real result, not a bug. Inputs: <a href="out/volume.json">volume.json</a> &times; <a href="out/demand.json">demand.json</a> &rarr; <a href="out/price_squeeze.json">price_squeeze.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.6rem 0 .3rem">Squeeze vs realised price change, 2018&ndash;2024</h2>
  <p class="muted" style="margin-top:0"><b>Right</b> = higher squeeze index (surging demand + inelastic supply). <b>Up</b> = the implied price actually rose over 2018&ndash;24. If the thesis were mechanical, everything would sit on a rising diagonal &mdash; watch where it doesn&rsquo;t.</p>
  <div id="scatter"></div>

  <h2 style="margin:1.6rem 0 .3rem">The price record, material by material</h2>
  <table class="tidy" id="tab"><thead><tr><th>Material</th><th class="n">2024 unit value $/t</th><th class="n">change 18–24</th><th class="n">squeeze</th><th>what the price says</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.8rem 0 .3rem">What the test refines</h2>
  <p>The clean result would have been &ldquo;squeeze predicts price.&rdquo; The real one is sharper: what companionality changes is the <i>direction</i> of price outcomes &mdash; or rather, who decides it. Gallium and germanium &mdash; by-product-locked and hit by 2023 export controls &mdash; spiked; cobalt, equally by-product-locked, <i>fell</i> as Indonesian nickel dragged a flood of by-product cobalt to market. Same structure, opposite prices, because in each case the host&rsquo;s cycle decided. That is exactly why the <a href="host-shock.html">host-shock</a> layer matters, and it pointed to the next child: track each squeeze metal&rsquo;s price <i>against its host&rsquo;s</i> output.</p>
  <p><b>That child came back with bad news, and it belongs here.</b> The <a href="host-coupling.html">host-coupling test</a> looked for &ldquo;the host decides&rdquo; as a <i>general law</i> and could not find it: on real prices with a valid control, the average companion&ndash;host coupling is <b>0.03</b>, and only bismuth&larr;lead survives. Testing the channel the theory actually names &mdash; the host&rsquo;s <i>output</i> &mdash; finds nothing at all. So this paragraph is narrowed to what it can carry: <b>in these episodes</b>, host and policy shocks set the direction. Gallium&rsquo;s 2023 spike and cobalt&rsquo;s Indonesian crash are documented events and are not in doubt. What is not supported is the stronger claim that companion prices <i>systematically</i> track their hosts. They track the commodity cycle, like everything else.</p>
  <div class="note">This page once carried a second claim &mdash; that companionality also raises price <i>volatility</i>. Retesting withdrew it, and it has been removed from this page and its dataset rather than left standing: on real price series with a market-size control the gap belongs to market size, and trade unit values turn out not to measure volatility at all. The replacement is <a href="price-volatility.html">here</a>; the full record of what broke and why is on <a href="challenge.html">the error record</a>.</div>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="price-volatility.html">Volatility, retested</a><br><a href="demand.html">The squeeze</a><br><a href="volume.html">Value vs volume</a><br><a href="host-shock.html">Host shock</a><br><a href="limitations.html">Limitations</a></div>
  <div><h4>Sources</h4>Implied trade unit values (BACI) × squeeze index (IEA/USGS × companionality)</div>
  <div class="fineprint">Trade unit values are nominal, noisy proxies for price; a directional corroboration test, not a price model.</div>
</div></footer>
<script>
function ld(u){return new Promise((res,rej)=>{const s=document.createElement('script');s.src=u;s.onload=res;s.onerror=rej;document.head.appendChild(s);});}
Promise.all([fetch('out/price_squeeze.json').then(r=>r.json()),
  ld('https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js')]).then(([S])=>{
  const cc=S.corr_squeeze_pricechange;
  document.getElementById('lead').innerHTML='<b>Result:</b> of the '+S.n_locked+' by-product-locked metals, '+S.locked_up.length+' saw implied prices <b>surge</b> ('+S.locked_up.join(', ')+' — three of them the single Ga/Ge/Hf trade code) and '+S.locked_down.length+' <b>crash</b> ('+S.locked_down.join(', ')+') over 2018–24. Same structural inelasticity, opposite outcomes &mdash; in each case because a host or policy shock, not the metal&rsquo;s own demand, set the direction.';
  const stats=[
    {v:(cc>0?'+':'')+cc,l:'correlation: squeeze vs 2018–24 price change (deduped for the shared Ga/Ge/Hf code)'},
    {v:S.n_locked,l:'by-product-locked metals tested (companionality ≥ 66%)'},
    {v:S.window,l:'price window — implied trade unit values, BACI'},
    {v:S.locked_up.length+'↑ / '+S.locked_down.length+'↓',l:'by-product-locked metals that surged vs crashed — the split'},
  ];
  document.getElementById('stats').innerHTML=stats.map(s=>'<div class="stat"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  document.getElementById('keyline').innerHTML='<b>Read it honestly:</b> the raw squeeze&harr;price correlation (+'+cc+') is modest, and even that leans on gallium, germanium and hafnium &mdash; which share one HS6 code and so post the <i>identical</i> +454%, one signal masquerading as three. Strip the double-counting and what is left is <b>direction, not turbulence</b>: prices rise when supply is restricted (gallium, germanium — 2023 export controls) and fall when the host floods the market (cobalt via Indonesian nickel). In each episode a host or policy shock decided it.';
  const col={byproduct:'#c0392b',mixed:'#b07a18',primary:'#0e7c74'};
  const pts=S.rows.filter(r=>r.chg_18_24!=null).map(r=>({
    value:[r.squeeze, r.chg_18_24, r.title, r['class']],
    itemStyle:{color:col[r['class']]+'cc'}, symbolSize:11}));
  const ch=echarts.init(document.getElementById('scatter'));
  ch.setOption({
    grid:{left:58,right:26,top:20,bottom:52},
    tooltip:{formatter:p=>'<b>'+p.value[2]+'</b><br>squeeze: '+p.value[0].toFixed(0)+'<br>price change 18–24: '+p.value[1]+'%<br>'+p.value[3]},
    xAxis:{name:'squeeze index',nameLocation:'middle',nameGap:30,min:0,
      axisLabel:{color:'#5a6b68'},nameTextStyle:{color:'#5a6b68'},splitLine:{lineStyle:{color:'#eef1f0'}}},
    yAxis:{name:'implied price change 2018→24 (%)',nameLocation:'middle',nameGap:44,
      axisLabel:{color:'#5a6b68'},nameTextStyle:{color:'#5a6b68'},splitLine:{lineStyle:{color:'#eef1f0'}}},
    series:[{type:'scatter',data:pts,
      markLine:{silent:true,symbol:'none',lineStyle:{color:'#c9b3ad',type:'dashed'},data:[{yAxis:0}]},
      label:{show:true,formatter:p=>p.value[2],position:'right',fontSize:10,color:'#15323a',distance:4}}]
  });
  window.addEventListener('resize',()=>ch.resize());
  const tb=document.querySelector('#tab tbody');
  S.rows.forEach(r=>{
    const chg=r.chg_18_24;
    const chgcell=chg==null?'<span style="color:#c9d2d0">—</span>':
      '<span style="color:'+(chg>15?'#c0392b':chg<-15?'#3f9b46':'#5a6b68')+';font-weight:600">'+(chg>0?'+':'')+chg+'%</span>';
    let says='&mdash;';
    const locked=r.companionality_pct>=66;
    if(chg!=null){ if(locked&&chg>20) says='inelastic + supply squeezed — price up';
      else if(locked&&chg<-20) says='inelastic but host oversupplied — price down';
      else if(locked) says='inelastic, price flat';
      else if(chg>40) says='demand-driven price rise';
      else if(chg<-40) says='oversupply / demand soft';
      else says='—'; }
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+r.title+'</b>'+(r.shared_hs6?' <span title="shares HS6 811292 with Ga/Ge/Hf — identical unit values" style="color:#b07a18">⛓</span>':'')+'</td>'+
      '<td class="n">'+(r.price_2024!=null?Number(r.price_2024).toLocaleString():'—')+'</td>'+
      '<td class="n">'+chgcell+'</td>'+
      '<td class="n" style="font-weight:600">'+r.squeeze.toFixed(0)+'</td>'+
      '<td class="muted" style="font-size:.82rem">'+says+'</td>';
    tb.appendChild(tr);
  });
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'price-squeeze.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote price-squeeze.html')
