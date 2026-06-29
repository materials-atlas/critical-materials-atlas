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

ROOT = os.path.dirname(os.path.abspath(__file__))
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
    used_iso.update(top)
    mats[lab] = {'title': TITLES[lab], 'top': top, 'lines': lines, 'hhi': hhi, 'china': china, 'gap': gap}
gap_index = [round(sum(gacc[y]) / len(gacc[y]), 1) if gacc[y] else 0.0 for y in YEARS]

names = {c: NAMES.get(c, c) for c in used_iso}
json.dump({'years': YEARS, 'names': names, 'gap_index': gap_index, 'materials': mats},
          open(os.path.join(ROOT, 'out', 'trends.json'), 'w', encoding='utf8'), indent=1)
print(f'wrote out/trends.json — {len(YEARS)} years ({YEARS[0]}-{YEARS[-1]}), {len(mats)} materials')
for lab in ['magnets', 'tungsten', 'bauxite']:
    c = mats[lab]['china']
    print(f"  {lab:<10} China export share {c[0]:.0f}% ({YEARS[0]}) -> {c[-1]:.0f}% ({YEARS[-1]})")
print(f"  origin-gap index: {gap_index[0]:.0f}pp ({YEARS[0]}) -> {gap_index[-1]:.0f}pp ({YEARS[-1]})")

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
<link rel="stylesheet" href="assets/site.css">
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
  <nav class="topnav"><a href="./">Atlas</a><a href="methodology.html">Methodology</a><a href="findings.html">Findings</a>
  <a href="network.html" class="hideable">Network</a><a href="casestudies.html" class="hideable">Cases</a>
  <a href="https://github.com/materials-atlas/comtrade-reconcile" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Time · 2002&ndash;2024</div>
  <h1>Twenty-two years, drawn</h1>
  <p class="deck">A continuous measured trade series back to 2002 means the concentration story is no longer a snapshot. Pick a material and watch its exporters &mdash; and its concentration &mdash; evolve. Then see China&rsquo;s export share climb across the marquee chains in one picture.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><b>What you are seeing.</b> Solid lines are each country&rsquo;s share of world exports of the
  material (left axis, %); the dashed line is the export-concentration Herfindahl (right axis, 0&ndash;1 &mdash; higher
  = more concentrated). Measured CEPII BACI, 2002&ndash;2024 (HS02 vintage through 2016, HS17 from 2017); nowcast
  years excluded. Shares are over the captured bilateral flows, as elsewhere in the atlas.</div>

  <div class="chartwrap">
    <div style="display:flex;align-items:center;gap:.7rem;flex-wrap:wrap;margin-bottom:.4rem">
      <b>Material:</b> <select id="mat" aria-label="Material"></select>
      <span class="muted">export shares + concentration over time</span>
    </div>
    <div id="chart1" class="chart"></div>
  </div>

  <h2 style="margin:1.8rem 0 .4rem">The rise of China, in one picture</h2>
  <p class="muted" style="margin-top:0">China&rsquo;s share of world exports, marquee materials, 2002&ndash;2024.</p>
  <div class="chartwrap"><div id="chart2" class="chart"></div></div>

  <h2 style="margin:1.8rem 0 .4rem">The origin gap over time</h2>
  <p class="muted" style="margin-top:0">Origin gap = the top exporter&rsquo;s world export share minus that country&rsquo;s own mine share. Mine share is the current USGS snapshot held fixed, so this isolates how the <i>trade</i> map drifted from today&rsquo;s mining reality &mdash; a rising line means the refiner/hub illusion widened. Bold = average across all 32 materials; thin lines = the materials with the widest gap today.</p>
  <div class="chartwrap"><div id="chart3" class="chart"></div></div>
  <p class="note">Computed from the per-year reconciled flows &rarr; <a href="out/trends.json">trends.json</a>. A broad code (e.g. magnets = all metal permanent magnets) carries that breadth across the series. Origin gap uses current USGS mine shares as a fixed reference.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="./">Interactive atlas</a><br><a href="findings.html">The origin gap</a><br><a href="network.html">Network chokepoints</a><br><a href="casestudies.html">Case studies</a></div>
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
    series:[{name:'avg (all 32)',type:'line',smooth:true,showSymbol:false,lineWidth:3.4,data:T.gap_index,itemStyle:{color:'#15323a'}}].concat(
      gapmats.map((k,i)=>({name:T.materials[k].title.replace(/,.*/,'').replace(/ \(.*/,''),type:'line',smooth:true,showSymbol:false,lineWidth:1.8,data:T.materials[k].gap,itemStyle:{color:COL[i%6]}})))
  },true);
  window.addEventListener('resize',()=>{c1.resize();c2.resize();c3.resize();});
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'trends.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote trends.html')
