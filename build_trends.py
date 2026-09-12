#!/usr/bin/env python3
"""
Trends view — the 22-year evolution, drawn.

The atlas now holds a continuous 2002-2024 measured trade series. The slider lets you scrub it and the
profile sparklines hint at it, but neither *draws* the evolution. This builds a compact time-series
(out/trends.json) and an interactive ECharts page (trends.html):

  - per material: the world-export-share lines of its main exporters over 2002-2024, plus an
    export-concentration (HHI) line — so you can watch a leader emerge (China's magnet line climb past
    Japan's, its tungsten line past everyone);
  - China's export share across the marquee materials on one chart — the "rise of China" in one picture.

Measured years only (nowcast 2025/26 excluded, matching the sparkline convention). Shares are over the
captured bilateral flows, consistent with the rest of the atlas. Public data; deterministic.

Writes out/trends.json + trends.html.  Run:  python build_trends.py
"""
import json, os, glob, re
import numpy as np
from scipy.stats import kendalltau, theilslopes
from statsmodels.stats.multitest import multipletests

ROOT = os.path.dirname(os.path.abspath(__file__))

def pettitt(x):
    """Non-parametric single change-point (Pettitt 1979): break index + approx p-value."""
    x = np.asarray(x, float); n = len(x)
    if n < 6 or np.allclose(x, x[0]):
        return None, None
    U = [sum(np.sign(x[i] - x[j]) for i in range(t + 1) for j in range(t + 1, n)) for t in range(n - 1)]
    U = np.asarray(U); k = int(np.argmax(np.abs(U))); K = abs(U[k])
    p = 2.0 * np.exp(-6.0 * K * K / (n ** 3 + n ** 2))
    return k, float(min(1.0, p))

def trendstat(series, years):
    """Mann-Kendall (via kendalltau) + Theil-Sen slope + Pettitt break, on one annual series."""
    x = np.asarray(series, float); t = np.asarray(years, float)
    if np.allclose(x, x[0]):
        return {'sen': 0.0, 'mk_p': 1.0, 'brk_year': None, 'brk_p': None, 'dir': 'flat'}
    tau, mkp = kendalltau(t, x)
    sen = float(theilslopes(x, t)[0])
    ki, pp = pettitt(x)
    brk = int(years[ki + 1]) if ki is not None else None
    d = 'rising' if (sen > 0 and mkp < 0.05) else 'falling' if (sen < 0 and mkp < 0.05) else 'flat/ns'
    return {'sen': round(sen, 3), 'mk_p': round(float(mkp), 3),
            'brk_year': brk, 'brk_p': (round(pp, 3) if pp is not None else None), 'dir': d}
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
TITLES = {m['label']: m['title'].split(' (')[0] for m in data['materials']}
LABELS = [m['label'] for m in data['materials']]

# load measured-year flows
FLOW = {}
NAMES = {}
for p in glob.glob(os.path.join(ROOT, 'out', 'flows_20*.json')):
    y = int(os.path.basename(p)[6:10])
    d = json.load(open(p, encoding='utf8'))
    if d.get('provisional') or d.get('nowcast_kind'):
        continue
    FLOW[y] = d
    NAMES.update(d.get('names', {}))
YEARS = sorted(FLOW)

def shares(year, label):
    o, tot = {}, 0.0
    for e in FLOW[year]['materials'].get(label, []) or []:
        o[e['from']] = o.get(e['from'], 0.0) + e['value']; tot += e['value']
    return ({c: v / tot * 100 for c, v in o.items()}, tot) if tot else ({}, 0.0)

MINE = {m['label']: {x['c']: x['v'] for x in (m.get('mined') or [])} for m in data['materials']}
mats = {}
used_iso = set()
gacc = {y: [] for y in YEARS}   # per-year positive origin gaps, for the aggregate index
for lab in LABELS:
    yr_sh = {y: shares(y, lab)[0] for y in YEARS}
    # pick the lines to draw: countries by their MAX share across the span (captures early leaders too)
    maxsh = {}
    for y in YEARS:
        for c, s in yr_sh[y].items():
            maxsh[c] = max(maxsh.get(c, 0), s)
    top = [c for c, _ in sorted(maxsh.items(), key=lambda kv: kv[1], reverse=True)[:6]]
    lines = {c: [round(yr_sh[y].get(c, 0.0), 1) for y in YEARS] for c in top}
    hhi = [round(sum((s / 100.0) ** 2 for s in yr_sh[y].values()), 3) for y in YEARS]
    china = [round(yr_sh[y].get('CN', 0.0), 1) for y in YEARS]
    # origin gap: the year's top exporter's world share minus that country's own (current) mine share
    gap = []
    for y in YEARS:
        s = yr_sh[y]
        g = (s[max(s, key=s.get)] - MINE[lab].get(max(s, key=s.get), 0.0)) if s else 0.0
        gap.append(round(g, 1))
    for i, y in enumerate(YEARS):
        gacc[y].append(max(0.0, gap[i]))
    # statistical trend tests + change-point on each indicator (no new deps)
    stats = {'hhi': trendstat(hhi, YEARS), 'china': trendstat(china, YEARS), 'gap': trendstat(gap, YEARS)}
    # who drove the 2002->2024 HHI change (contribution = s_2024^2 - s_2002^2 by country)
    s0, s1 = shares(YEARS[0], lab)[0], shares(YEARS[-1], lab)[0]
    cs = set(s0) | set(s1)
    contrib = {c: ((s1.get(c, 0) / 100.0) ** 2 - (s0.get(c, 0) / 100.0) ** 2) for c in cs}
    dh = sum(contrib.values())
    if contrib:
        topc = max(contrib, key=lambda c: abs(contrib[c]))
        stats['dhhi'] = {'c': topc, 'pct': (round(contrib[topc] / dh * 100) if dh else None), 'dhhi': round(dh, 3)}
    else:
        stats['dhhi'] = None
    # full country decomposition of the 2002->2024 HHI change (top contributors by |contribution|, x100)
    decomp = sorted(({'c': c, 'v': round(contrib[c] * 100, 1)} for c in contrib),
                    key=lambda x: abs(x['v']), reverse=True)[:6]
    used_iso.update(d['c'] for d in decomp)
    used_iso.update(top)
    mats[lab] = {'title': TITLES[lab], 'top': top, 'lines': lines, 'hhi': hhi, 'china': china,
                 'gap': gap, 'stats': stats, 'decomp': decomp}
# Benjamini-Hochberg FDR correction across the 32 materials, per indicator
labs = list(mats)
for ind in ('hhi', 'china', 'gap'):
    ps = [mats[l]['stats'][ind]['mk_p'] for l in labs]
    adj = multipletests(ps, method='fdr_bh')[1]
    for l, a in zip(labs, adj):
        mats[l]['stats'][ind]['mk_p_fdr'] = round(float(a), 3)
gap_index = [round(sum(gacc[y]) / len(gacc[y]), 1) if gacc[y] else 0.0 for y in YEARS]

names = {c: NAMES.get(c, c) for c in used_iso}
json.dump({'years': YEARS, 'names': names, 'gap_index': gap_index, 'materials': mats},
          open(os.path.join(ROOT, 'out', 'trends.json'), 'w', encoding='utf8'), indent=1)
print(f'wrote out/trends.json — {len(YEARS)} years ({YEARS[0]}-{YEARS[-1]}), {len(mats)} materials')
for lab in ['magnets', 'tungsten', 'bauxite']:
    c = mats[lab]['china']
    print(f"  {lab:<10} China export share {c[0]:.0f}% ({YEARS[0]}) -> {c[-1]:.0f}% ({YEARS[-1]})")
print(f"  origin-gap index: {gap_index[0]:.0f}pp ({YEARS[0]}) -> {gap_index[-1]:.0f}pp ({YEARS[-1]})")
_sig = [l for l in labs if mats[l]['stats']['hhi']['mk_p_fdr'] < 0.05 and mats[l]['stats']['hhi']['sen'] > 0]
print(f"  significant rising export-HHI (Mann-Kendall FDR<0.05): {len(_sig)}/{len(labs)} materials")
for l in sorted(_sig, key=lambda l: mats[l]['stats']['hhi']['sen'], reverse=True)[:6]:
    s = mats[l]['stats']['hhi']
    print(f"    {TITLES[l]:<22} Sen {s['sen']:+.3f}/yr  MK-FDR p={s['mk_p_fdr']}  break {s['brk_year']}")

# ---- static page (no Python interpolation; data fetched at runtime) ----
HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trends — 22 years of critical-material trade — Critical Materials Atlas</title>
<meta name="description" content="The two-decade evolution of critical-material trade: export-share trend lines and concentration (HHI) for 32 materials, 2002-2024, and the rise of China across the marquee chains.">
<meta property="og:title" content="Trends — 22 years of critical-material trade">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  .chartwrap{background:#fff;border:1px solid var(--line,#e3e9e8);border-radius:10px;padding:1rem 1rem .5rem;margin:1rem 0}
  .chart{width:100%;height:420px}
  select#mat{font:inherit;padding:.4rem .6rem;border:1px solid #cdd6d4;border-radius:7px;font-weight:600}
  .muted{color:#5a6b68;font-size:.86rem}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Time · 2002&ndash;2024</div>
  <h1>Twenty-two years, drawn</h1>
  <p class="deck">A continuous measured trade series back to 2002 means the concentration story is no longer a snapshot. Pick a material and watch its exporters &mdash; and its concentration &mdash; evolve. Then see China&rsquo;s export share climb across the marquee chains in one picture.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout">Each line is a country&rsquo;s share of world exports over 2002&ndash;2024; the dashed line tracks how concentrated the trade is overall.
  <details class="howto"><summary>Reading the chart</summary>
  <p>Solid lines are each country&rsquo;s share of world exports of the material (left axis, %); the dashed line is the export-concentration Herfindahl (right axis, 0&ndash;1 &mdash; higher = more concentrated). Measured CEPII BACI, 2002&ndash;2024 (HS02 vintage through 2016, HS17 from 2017); nowcast years excluded. Shares are over the captured bilateral flows, as elsewhere in the atlas.</p>
  </details></div>

  <div class="chartwrap">
    <div style="display:flex;align-items:center;gap:.7rem;flex-wrap:wrap;margin-bottom:.4rem">
      <b>Material:</b> <select id="mat" aria-label="Material"></select>
      <span class="muted">export shares + concentration over time</span>
    </div>
    <div id="chart1" class="chart"></div>
    <p id="stat1" class="muted" style="margin:.5rem 0 0"></p>
  </div>

  <div class="chartwrap">
    <div style="font-weight:600;font-size:.92rem;margin-bottom:.2rem">What drove the 2002&ndash;2024 concentration change <span id="declabel" class="muted" style="font-weight:400"></span></div>
    <div id="chart4" class="chart" style="height:300px"></div>
    <p class="muted" style="margin:.3rem 0 0">Each country's contribution to the change in export-HHI (share&sup2;<sub>2024</sub> &minus; share&sup2;<sub>2002</sub>, &times;100). <span style="color:#c0392b">Red</span> = pushed concentration up (gained share); <span style="color:#3f9b46">green</span> = pushed it down. This is the Family-5 decomposition: it names <i>who</i> concentrated a market.</p>
  </div>

  <h2 style="margin:1.8rem 0 .4rem">The rise of China, in one picture</h2>
  <p class="muted" style="margin-top:0">China&rsquo;s share of world exports, marquee materials, 2002&ndash;2024.</p>
  <div class="chartwrap"><div id="chart2" class="chart"></div></div>

  <h2 style="margin:1.8rem 0 .4rem">The origin gap over time</h2>
  <p class="muted" style="margin-top:0">Origin gap = the top exporter&rsquo;s world export share minus that country&rsquo;s own mine share. Mine share is the current USGS snapshot held fixed, so this isolates how the <i>trade</i> map drifted from today&rsquo;s mining reality &mdash; a rising line means the refiner/hub illusion widened. Bold = average across all 32 materials; thin lines = the materials with the widest gap today. The dotted vertical marks the <b>2017 HS-vintage join</b>, where the level steps for nomenclature/coverage reasons, not signal — so read the level cautiously (an HS17-only run is the clean confirmation).</p>
  <div class="chartwrap"><div id="chart3" class="chart"></div></div>
  <p class="note">Computed from the per-year reconciled flows &rarr; <a href="out/trends.json">trends.json</a>. A broad code (e.g. magnets = all metal permanent magnets) carries that breadth across the series. Origin gap uses current USGS mine shares as a fixed reference.</p>

  <h2 style="margin:1.8rem 0 .4rem">Which trends are statistically real</h2>
  <p class="muted" style="margin-top:0">The export-concentration (HHI) trend per material, <b>tested</b> rather than eyeballed: Mann&ndash;Kendall significance (Benjamini&ndash;Hochberg FDR-corrected across the 32 materials), Theil&ndash;Sen slope, the Pettitt structural-break year, and the country that drove the 2002&ndash;2024 HHI change. Sorted by slope. The standard critical-minerals literature plots concentration but rarely tests it &mdash; with T=23, read p-values as screening evidence. Computed by <code>build_trends.py</code> (scipy + statsmodels).</p>
  <table id="ttab"><thead><tr><th>Material</th><th class="n" title="Theil-Sen robust slope, HHI points per year">Sen slope /yr</th><th class="n" title="Mann-Kendall p-value, Benjamini-Hochberg FDR-corrected across 32 materials">MK p (FDR)</th><th class="n" title="Pettitt structural-break year">break</th><th title="country contributing most to the 2002-2024 HHI change">&Delta;HHI driver</th></tr></thead><tbody></tbody></table>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>UN Comtrade · CEPII BACI (HS02 + HS17)</div>
  <div class="fineprint">Pre-2017 is the HS02 BACI vintage spliced to the HS17 recent end. Shares over captured flows.</div>
</div></footer>
<script>
const $=s=>document.querySelector(s);
const COL=['#0e7c74','#c77f0a','#6d5fb0','#b4532b','#3f9b46','#9aa6ad'];
fetch('out/trends.json').then(r=>r.json()).then(T=>{
  const years=T.years, nm=c=>T.names[c]||c;
  const sel=$('#mat');
  Object.keys(T.materials).forEach(lab=>{const o=document.createElement('option');o.value=lab;o.textContent=T.materials[lab].title;sel.appendChild(o);});
  const c1=echarts.init($('#chart1'));
  const c4=echarts.init($('#chart4'));
  function draw(lab){
    const m=T.materials[lab];
    const series=m.top.map((cc,i)=>({name:nm(cc),type:'line',smooth:true,showSymbol:false,lineWidth:2.6,data:m.lines[cc],itemStyle:{color:COL[i%6]}}));
    series.push({name:'concentration (HHI)',type:'line',smooth:true,showSymbol:false,yAxisIndex:1,lineStyle:{type:'dashed',width:1.6},itemStyle:{color:'#15323a'},data:m.hhi});
    c1.setOption({
      tooltip:{trigger:'axis',valueFormatter:v=>v==null?'':(v<=1?v.toFixed(2):v.toFixed(0)+'%')},
      legend:{top:0,type:'scroll'},
      grid:{left:48,right:54,top:34,bottom:30},
      xAxis:{type:'category',data:years,boundaryGap:false},
      yAxis:[{type:'value',name:'export share %',min:0,max:100,axisLabel:{formatter:'{value}%'}},
             {type:'value',name:'HHI',min:0,max:1,splitLine:{show:false}}],
      series
    },true);
    const st=m.stats&&m.stats.hhi;
    if(st){const sig=st.mk_p_fdr<0.05; document.getElementById('stat1').innerHTML='<b>HHI trend:</b> Theil&ndash;Sen '+(st.sen>=0?'+':'')+st.sen.toFixed(3)+'/yr · Mann&ndash;Kendall p='+st.mk_p_fdr+' (FDR) '+(sig?'<span style="color:#c0392b;font-weight:600">significant</span>':'<span style="color:#9aa6ad">not significant</span>')+(st.brk_year?(' · structural break ~'+st.brk_year):'')+((m.stats.dhhi&&m.stats.dhhi.c)?(' · ΔHHI 2002–24 mostly driven by '+nm(m.stats.dhhi.c)):'');}
    const dec=(m.decomp||[]).slice().reverse();
    c4.setOption({tooltip:{trigger:'axis',valueFormatter:v=>v==null?'':(v>=0?'+':'')+(+v).toFixed(1)},grid:{left:100,right:24,top:8,bottom:30},xAxis:{type:'value',name:'ΔHHI ×100',nameLocation:'middle',nameGap:24},yAxis:{type:'category',data:dec.map(d=>nm(d.c))},series:[{type:'bar',data:dec.map(d=>({value:d.v,itemStyle:{color:d.v>=0?'#c0392b':'#3f9b46'}}))}]},true);
    const dh=(m.stats&&m.stats.dhhi)?m.stats.dhhi.dhhi:null; const dl=document.getElementById('declabel'); if(dl) dl.textContent = dh!=null?('· total ΔHHI '+(dh>=0?'+':'')+(dh*100).toFixed(1)):'';
  }
  sel.onchange=()=>draw(sel.value);
  draw(T.materials.magnets?'magnets':Object.keys(T.materials)[0]);

  const KEY=['magnets','tungsten','graphite','cobalt','lithium','gallium','silicon','antimony'].filter(k=>T.materials[k]);
  const c2=echarts.init($('#chart2'));
  c2.setOption({
    tooltip:{trigger:'axis',valueFormatter:v=>v==null?'':v.toFixed(0)+'%'},
    legend:{top:0,type:'scroll'},
    grid:{left:48,right:20,top:34,bottom:30},
    xAxis:{type:'category',data:T.years,boundaryGap:false},
    yAxis:{type:'value',name:"China export share %",min:0,max:100,axisLabel:{formatter:'{value}%'}},
    series:KEY.map((k,i)=>({name:T.materials[k].title.replace(/,.*/,'').replace(/ \(.*/,''),type:'line',smooth:true,showSymbol:false,lineWidth:2.4,data:T.materials[k].china,itemStyle:{color:COL[i%6]}}))
  });
  const c3=echarts.init($('#chart3'));
  const gapmats=Object.keys(T.materials).map(k=>[k,T.materials[k].gap[T.materials[k].gap.length-1]]).sort((a,b)=>b[1]-a[1]).slice(0,5).map(x=>x[0]);
  c3.setOption({
    tooltip:{trigger:'axis',valueFormatter:v=>v==null?'':v.toFixed(0)+'pp'},
    legend:{top:0,type:'scroll'},
    grid:{left:48,right:20,top:34,bottom:30},
    xAxis:{type:'category',data:T.years,boundaryGap:false},
    yAxis:{type:'value',name:'origin gap (pp)',axisLabel:{formatter:'{value}'}},
    series:[{name:'avg (all 32)',type:'line',smooth:true,showSymbol:false,lineWidth:3.4,data:T.gap_index,itemStyle:{color:'#15323a'},markLine:{symbol:'none',silent:true,lineStyle:{type:'dotted',color:'#9aa6ad'},data:[{xAxis:'2017'}],label:{formatter:'HS-vintage join',fontSize:9,color:'#9aa6ad'}}}].concat(
      gapmats.map((k,i)=>({name:T.materials[k].title.replace(/,.*/,'').replace(/ \(.*/,''),type:'line',smooth:true,showSymbol:false,lineWidth:1.8,data:T.materials[k].gap,itemStyle:{color:COL[i%6]}})))
  },true);
  const tb=document.querySelector('#ttab tbody');
  Object.keys(T.materials).map(k=>[k,T.materials[k]]).filter(e=>e[1].stats&&e[1].stats.hhi)
    .sort((a,b)=>b[1].stats.hhi.sen-a[1].stats.hhi.sen)
    .forEach(e=>{const k=e[0],m=e[1],s=m.stats.hhi,d=m.stats.dhhi,sig=s.mk_p_fdr<0.05&&s.sen>0;
      const tr=document.createElement('tr');
      tr.innerHTML='<td><a href="profile-'+k+'.html">'+m.title+'</a></td>'+
        '<td class="n" style="font-weight:600;color:'+(s.sen>0?'#c0392b':s.sen<0?'#3f9b46':'#9aa6ad')+'">'+(s.sen>=0?'+':'')+s.sen.toFixed(3)+'</td>'+
        '<td class="n"'+(sig?' style="font-weight:700"':'')+'>'+s.mk_p_fdr+'</td>'+
        '<td class="n">'+(s.brk_year||'—')+'</td>'+
        '<td>'+((d&&d.c)?(nm(d.c)+(d.pct!=null?(' <span style="color:#9aa6ad">'+d.pct+'%</span>'):'')):'—')+'</td>';
      tb.appendChild(tr);});
  window.addEventListener('resize',()=>{c1.resize();c2.resize();c3.resize();c4.resize();});
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'trends.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote trends.html')
