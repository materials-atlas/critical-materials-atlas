#!/usr/bin/env python3
"""
The refining wedge — where does control move from the mine to the furnace?

Every metal is traded twice: once as ore/concentrate, and again as refined or first-processed metal.
If the refined stage is *more* geographically concentrated than the ore stage, a chokepoint has formed at
processing, not extraction — the classic critical-materials risk ("the worry isn't who digs it, it's who
refines it"). We measure both stages from the SAME bilateral-trade source (CEPII BACI, HS-2017, 3-year mean
2022-24, by value) and compute the wedge = HHI(refined exports) - HHI(ore exports).

Honest scope: this is concentration of *tradeable* processed supply. A refiner that consumes its output
domestically (China for battery-grade cobalt/lithium, or downstream magnets) exports little refined metal and
so is understated here — that capacity shows up in the production/GeoPolRisk layers instead. This layer is
specifically about who controls the metal that actually crosses borders in processed form.
"""
import csv, os, json
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
SLIM = os.path.join(ROOT, 'raw', 'refining', 'refining_flows_slim.csv')
YEARS = 3  # 2022-24 mean already in the slim; used for the note

# ore code(s) -> refined/first-processed basket. Baskets include the dominant ferroalloy/intermediate route so
# the "refined" stage reflects the form the metal is actually traded in, not an arbitrary single HS line.
PAIRS = {
    'copper':    (['260300'], ['740311'],           'refined cathode (740311)'),
    'nickel':    (['260400'], ['750210', '720260'], 'unwrought + ferronickel'),
    'cobalt':    (['260500'], ['810520'],           'unwrought / intermediate (810520)'),
    'bauxite':   (['260600'], ['760110'],           'unwrought aluminium (760110)'),
    'chromium':  (['261000'], ['720241', '720249'], 'ferrochromium'),
    'tungsten':  (['261100'], ['810194', '284180'], 'unwrought W + APT'),
    'titanium':  (['261400'], ['810820'],           'unwrought titanium (810820)'),
    'tantalum':  (['261590'], ['810320'],           'unwrought tantalum (810320)'),
    'niobium':   (['261590'], ['720293'],           'ferro-niobium (720293)'),
    'antimony':  (['261710'], ['811010'],           'unwrought antimony (811010)'),
    'tin':       (['260900'], ['800110'],           'unwrought tin (800110)'),
    'molybdenum':(['261310'], ['810294', '720270'], 'unwrought Mo + ferromoly'),
    'manganese': (['260200'], ['811100', '720211', '720219', '720230'], 'Mn metal + ferro/silico-Mn'),
    'zinc':      (['260800'], ['790111'],           'unwrought zinc (790111)'),
    'lead':      (['260700'], ['780110'],           'refined lead (780110)'),
}
# which of these the atlas tracks as critical (for emphasis)
CRITICAL = {'nickel', 'cobalt', 'bauxite', 'chromium', 'tungsten', 'titanium', 'tantalum',
            'niobium', 'antimony', 'manganese', 'copper'}

# load slim: (hs6, iso3) -> summed value across the 3 years
val = defaultdict(float)
with open(SLIM, encoding='utf-8', newline='') as f:
    for row in csv.DictReader(f):
        val[(row['hs6'], row['exporter_iso3'])] += float(row['value_kusd'])


def concentration(codes):
    sh = defaultdict(float); tot = 0.0
    for (hs6, iso), v in val.items():
        if hs6 in codes:
            sh[iso] += v; tot += v
    if tot <= 0:
        return None
    hhi = sum((s / tot) ** 2 for s in sh.values())
    top = sorted(sh.items(), key=lambda kv: -kv[1])[:4]
    return {'hhi': round(hhi, 3), 'n_exporters': len(sh),
            'top': [{'iso3': i, 'pct': round(100 * s / tot)} for i, s in top],
            'chn': round(100 * sh.get('CHN', 0) / tot), 'total_kusd': round(tot)}


rows = []
for m, (ore_codes, ref_codes, ref_label) in PAIRS.items():
    o = concentration(ore_codes); r = concentration(ref_codes)
    if not o or not r:
        continue
    rows.append({
        'material': m, 'critical': m in CRITICAL, 'refined_form': ref_label,
        'ore': o, 'refined': r,
        'wedge': round(r['hhi'] - o['hhi'], 3),
        'ore_leader': o['top'][0], 'refined_leader': r['top'][0],
        'chn_gain': r['chn'] - o['chn'],
    })
rows.sort(key=lambda d: -d['wedge'])

n_wedge = sum(1 for d in rows if d['wedge'] > 0.03)
biggest = rows[0]
chn_ref = sorted(rows, key=lambda d: -d['refined']['chn'])
out = {
    'source': 'CEPII BACI (HS-2017), 3-year mean 2022-2024, exporter value shares',
    'n_materials': len(rows),
    'n_positive_wedge': n_wedge,
    'rows': rows,
    'headline_wedge': {'material': biggest['material'], 'wedge': biggest['wedge'],
                       'refined_leader': biggest['refined_leader']},
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'refining.json'), 'w', encoding='utf8'), separators=(',', ':'))
print('wrote out/refining.json')
print(f"  {len(rows)} metals | {n_wedge} with a positive refining wedge")
for d in rows[:6]:
    rl = d['refined_leader']; ol = d['ore_leader']
    print(f"  {d['material']:11s} wedge {d['wedge']:+.2f}  ore {ol['iso3']} {ol['pct']}%  ->  refined {rl['iso3']} {rl['pct']}%")

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The refining wedge — mine vs furnace · Critical Materials Atlas</title>
<meta name="description" content="Every metal is traded as ore and again as refined metal. Where the refined stage is more geographically concentrated than the ore, control has moved from the mine to the furnace. We measure both from the same bilateral-trade source (BACI) and rank the processing chokepoints.">
<meta property="og:title" content="The refining wedge: where control moves from the mine to the furnace">
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
 table.tidy{width:100%;border-collapse:collapse;font-size:.86rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.45rem .5rem;border-bottom:1px solid #eef1f0;text-align:left;vertical-align:middle}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .stage{display:flex;align-items:center;gap:.5rem;min-width:210px}
 .stage .track{flex:1;height:16px;background:#f0f3f2;border-radius:4px;overflow:hidden;display:flex}
 .stage .seg{height:100%}
 .stage .lead{font-size:.78rem;font-weight:700;color:#15323a;white-space:nowrap}
 .wedge{font-weight:800;font-variant-numeric:tabular-nums}
 .wedge.pos{color:#c0392b}.wedge.neg{color:#2f8f6b}
 .keyline{background:#f2f6f5;border:1px solid #d9e6e3;border-left:4px solid #0e7c74;border-radius:10px;padding:.9rem 1.1rem;margin:1.2rem 0}
 .keyline b{color:#0e7c74}
 .crit{display:inline-block;font-size:.64rem;font-weight:700;color:#8f2a20;background:#fbe9e7;border-radius:4px;padding:.05rem .3rem;margin-left:.35rem;vertical-align:middle}
 .arrow{color:#9aa6ad;font-weight:700;margin:0 .1rem}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="criticality.html">Criticality</a><a href="production.html">Production</a>
  <a href="geopolrisk.html" class="hideable">GeoPolRisk</a><a href="methodology.html" class="hideable">Methodology</a>
  <a href="https://github.com/materials-atlas/comtrade-reconcile" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · mine vs furnace · the refining wedge</div>
  <h1>The refining wedge</h1>
  <p class="deck">Every metal is traded twice &mdash; once as <b>ore or concentrate</b>, and again as <b>refined or first-processed metal</b>. When the refined stage is <i>more</i> geographically concentrated than the ore, control has moved from the <b>mine to the furnace</b>: the chokepoint is who processes, not who digs. We measure both stages from the <i>same</i> bilateral-trade source and rank where that wedge is widest.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>The method, and its honest scope</summary>
  <p>For each metal we take its <b>ore/concentrate</b> HS-2017 line and its <b>refined / first-processed</b> basket (refined metal plus the dominant ferroalloy or intermediate route, so the &ldquo;refined&rdquo; stage reflects the form actually traded &mdash; e.g. ferronickel for nickel, ferrochrome for chromium). For each stage we compute the <b>exporter Herfindahl (HHI)</b> on trade <i>value</i>, then the <b>wedge = HHI(refined) &minus; HHI(ore)</b>. Positive = processing more concentrated than extraction.</p>
  <p class="howto-src"><b>Source:</b> CEPII <b>BACI</b> (HS-2017), 3-year mean 2022&ndash;2024, exporter value shares &rarr; <a href="out/refining.json">refining.json</a>. Value, not tonnage: BACI quantities carry unit artifacts (they put one EU smelter at 66% of world zinc by weight but 13% by value). <b>Honest scope:</b> this is concentration of <i>tradeable</i> processed supply. A refiner that consumes its output at home &mdash; China turning imported concentrate into battery cathode, or into magnets &mdash; exports little refined metal and is <i>understated</i> here; that capacity shows up in the <a href="geopolrisk.html">production / GeoPolRisk</a> layer instead. This page is specifically about who controls the metal that crosses borders in processed form.</p>
  </details></div>

  <div class="stat4" id="stats"></div>
  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.6rem 0 .3rem">Ore stage &rarr; refined stage, ranked by the wedge</h2>
  <p class="muted" style="margin-top:0">Each bar shows the top exporters&rsquo; value share at that stage (darker = the single leader). A wide <b class="wedge pos">positive</b> wedge means the refined bar is far more concentrated than the ore bar &mdash; a processing chokepoint. A <b class="wedge neg">negative</b> wedge means refining is <i>more</i> spread out than mining (no furnace chokepoint beyond the ore itself).</p>
  <table class="tidy" id="rtab"><thead><tr><th>Material</th><th>ore exporters</th><th>refined exporters <span class="muted" style="font-weight:400">(form)</span></th><th class="n">wedge</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.8rem 0 .3rem">The refining you <i>can&rsquo;t</i> see in trade &mdash; a capacity cross-check</h2>
  <p class="muted" style="margin-top:0">This whole page measures <b>exported</b> refined metal. That misses the refiner who imports concentrate, processes it, and consumes the output <i>at home</i> &mdash; above all China, turning ore into battery cathode, magnets and chips that leave as finished goods, not as refined metal. So for the battery chain the export wedge <b>understates</b> the real chokepoint. The authoritative capacity figures (IEA) make the gap explicit:</p>
  <table class="tidy" style="max-width:640px">
    <thead><tr><th>Material</th><th>What our export wedge shows</th><th class="n">China&rsquo;s actual refining capacity</th></tr></thead>
    <tbody>
      <tr><td><b>Cobalt</b></td><td>DR Congo leads refined-<i>intermediate</i> exports (64%)</td><td class="n">~60% of refined cobalt</td></tr>
      <tr><td><b>Lithium</b></td><td>no clean ore&harr;refined HS pair (chemical forms)</td><td class="n">~60% of refined lithium</td></tr>
      <tr><td><b>Rare earths / magnets</b></td><td>not trade-separable as ore vs metal</td><td class="n">&gt;90% of refining</td></tr>
      <tr><td><b>Graphite</b></td><td>&mdash;</td><td class="n">&gt;90% of refining</td></tr>
      <tr><td><b>Nickel</b></td><td>Indonesia 50% of refined exports &mdash; <i>captured</i></td><td class="n">Indonesia-led (pyromet route exported)</td></tr>
    </tbody>
  </table>
  <p class="muted" style="margin-top:.5rem">The contrast is the point: where the refined form is <b>traded</b> (ferronickel, ferro-niobium, refined copper) the export wedge sees the chokepoint clearly &mdash; Indonesia&rsquo;s nickel, Brazil&rsquo;s niobium, China&rsquo;s tungsten. Where it is <b>consumed at home</b> (cobalt, lithium, rare earths, graphite) trade goes quiet and only capacity data reveals it. The two are complements: this page for the tradeable stage, the <a href="geopolrisk.html">production &amp; governance</a> layer and the figures above for capacity. Source: <a href="https://www.iea.org/reports/global-critical-minerals-outlook-2025/executive-summary" target="_blank" rel="noopener">IEA, Global Critical Minerals Outlook 2025</a> (top-three refiners&rsquo; average share of key energy minerals rose 82%&rarr;86% between 2020 and 2024).</p>

  <h2 style="margin:1.8rem 0 .3rem">What it says</h2>
  <p id="closing"></p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="geopolrisk.html">GeoPolRisk</a><br><a href="production.html">Production in tonnes</a><br><a href="commodity-attribution.html">Commodity attribution</a><br><a href="methodology.html">Methodology</a></div>
  <div><h4>Sources</h4>CEPII BACI (HS-2017) bilateral trade, 2022&ndash;24 mean &middot; ore vs refined HS pairs</div>
</div></footer>
<script>
const NAME={COD:'DR Congo',BRA:'Brazil',CHN:'China',IDN:'Indonesia',ZAF:'South Africa',PHL:'Philippines',CHL:'Chile',PER:'Peru',AUS:'Australia',RUS:'Russia',GIN:'Guinea',IND:'India',JPN:'Japan',KOR:'South Korea',ESP:'Spain',TJK:'Tajikistan',RWA:'Rwanda',MMR:'Myanmar',MOZ:'Mozambique',BOL:'Bolivia',USA:'United States',CAN:'Canada',KAZ:'Kazakhstan',MEX:'Mexico',NOR:'Norway',GBR:'UK',DEU:'Germany',NLD:'Netherlands',VNM:'Vietnam',THA:'Thailand'};
const nm=i=>NAME[i]||i;
const TITLE=s=>s.charAt(0).toUpperCase()+s.slice(1);
fetch('out/refining.json').then(r=>r.json()).then(S=>{
  const hw=S.headline_wedge, rl=hw.refined_leader;
  document.getElementById('lead').innerHTML='<b>Result:</b> across '+S.n_materials+' metals, <b>'+S.n_positive_wedge+'</b> show a refining wedge &mdash; the processed stage is measurably more concentrated than the ore. The widest is <b>'+TITLE(hw.material)+'</b>: mined in a spread of countries, but <b>'+rl.pct+'% of refined exports come from '+nm(rl.iso3)+'</b>. The pattern repeats with a different controller each time &mdash; tungsten and tantalum refine toward China, nickel toward Indonesia, cobalt stays locked in DR&nbsp;Congo. The chokepoint is the furnace, and it rarely sits where the ore does.';
  // stat tiles: top 4 positive-wedge chokepoints
  const pos=S.rows.filter(d=>d.wedge>0.03).slice(0,4);
  document.getElementById('stats').innerHTML=pos.map(d=>{
    const rl=d.refined_leader;
    return '<div class="stat"><div class="v">'+rl.pct+'%</div><div class="l">'+TITLE(d.material)+' &mdash; '+nm(rl.iso3)+'&rsquo;s share of refined exports <span style="color:#c0392b">(wedge +'+d.wedge.toFixed(2)+')</span></div></div>';
  }).join('');
  document.getElementById('keyline').innerHTML='<b>The point:</b> a mine can be diversified while the furnace is not. Bauxite is dug across dozens of countries and Guinea leads its ore &mdash; yet the concentration <i>falls</i> at the aluminium stage, because smelting is everywhere. Niobium is the opposite: ore scattered, but <b>three-quarters of ferro-niobium comes from one Brazilian firm</b>. Extraction concentration and processing concentration are different risks, and only splitting the trade in two tells them apart.';
  // table
  const COL_LEAD='#0e7c74', COL_REST='#9cc5bf', COL_LEAD2='#b07a18', COL_REST2='#e3cb95';
  function bar(stage, leadCol, restCol){
    const segs=stage.top.map((t,i)=>'<span class="seg" title="'+nm(t.iso3)+' '+t.pct+'%" style="width:'+t.pct+'%;background:'+(i===0?leadCol:restCol)+'"></span>').join('');
    return '<div class="stage"><div class="track">'+segs+'</div><span class="lead">'+nm(stage.top[0].iso3)+' '+stage.top[0].pct+'%</span></div>';
  }
  const tb=document.querySelector('#rtab tbody');
  S.rows.forEach(d=>{
    const tr=document.createElement('tr');
    const wc=d.wedge>0.03?'pos':(d.wedge<-0.03?'neg':'');
    const sign=d.wedge>0?'+':'';
    tr.innerHTML='<td><b>'+TITLE(d.material)+'</b>'+(d.critical?'<span class="crit">critical</span>':'')+'</td>'+
      '<td>'+bar(d.ore,COL_LEAD,COL_REST)+'</td>'+
      '<td>'+bar(d.refined,COL_LEAD2,COL_REST2)+'<div class="muted" style="font-size:.72rem;margin-top:.1rem">'+d.refined_form+'</div></td>'+
      '<td class="n"><span class="wedge '+wc+'">'+sign+d.wedge.toFixed(2)+'</span></td>';
    tb.appendChild(tr);
  });
  const chn=S.rows.filter(d=>d.refined.chn>=20).map(d=>TITLE(d.material)+' ('+d.refined.chn+'%)');
  document.getElementById('closing').innerHTML='Read alongside the <a href="geopolrisk.html">production concentration</a> layer, this closes a loop the mine map can&rsquo;t: physical output can be spread across continents while the <i>usable</i> metal funnels through a handful of processors. Where refined exports still lean on China in this trade-visible view &mdash; '+(chn.join(', ')||'a few metals')+' &mdash; the dependence is on processing, not deposits, and no new mine fixes it. And the metals whose wedge is <i>negative</i> are a quiet reassurance: their refining is genuinely global, so an ore shock has somewhere else to go. It is the same discipline as the rest of the atlas &mdash; measure the thing where it actually happens, and let the two stages disagree out loud.';
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'refining.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote refining.html')
