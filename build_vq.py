#!/usr/bin/env python3
"""
Value vs volume — separating real concentration from price effects.

Trade VALUE = price x quantity, so a rising value-concentration (HHI) can be a price effect rather than a
real shift in who ships the tonnes. BACI carries quantity (metric tons, ~94% coverage) beside value, so we
compute export concentration and China share in BOTH value and volume, per material per year (2002-2024),
streaming the BACI csvs straight from the zips. The gap between them is the price signal: where value-HHI
or value-China-share sit well above their volume counterparts, the apparent concentration is partly price.

Writes out/volume.json + volume.html.  Public data; deterministic.  Run: python build_vq.py
"""
import json, os, re, csv, zipfile, io
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import baci as _baci  # the one door for BACI (ARCHITECTURE.md phase 2)

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, 'raw', 'baci')
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
flows = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf8'))
NAMES = flows.get('names', {})
TITLES = {m['label']: m['title'].split(' (')[0] for m in data['materials']}

# HS22 code -> material label(s)
CODE2LAB = {}
for m in data['materials']:
    digits = re.sub(r'\D', '', re.search(r'\(([^)]*)\)', m['title']).group(1))
    if len(digits) >= 6:
        CODE2LAB.setdefault(digits[:6], []).append(m['label'])

# BACI numeric country code -> ISO2
num2iso = {}
with _baci.country_file() as f:
    for r in csv.DictReader(f):
        iso = r.get('country_iso2') or ''
        if iso:   # 'NA' is Namibia, not missing
            num2iso[r['country_code']] = iso

def codes_for(hs):
    """code->labels with revision crosswalks (hafnium pooled pre-HS22; boron split pre-HS2012)."""
    c2l = {k: list(v) for k, v in CODE2LAB.items()}
    if '811231' in c2l:                                   # hafnium: no distinct code before HS2022
        c2l.setdefault('811292', []).extend(c2l.pop('811231'))
    if hs == 'HS02' and '252800' in c2l:                  # boron: split 252810/252890 before HS2012
        for pc in ('252810', '252890'):
            c2l.setdefault(pc, []).extend(c2l['252800'])
        del c2l['252800']
    return c2l

def process(hs, year):
    name = f'BACI_{hs}_Y{year}_V202601.csv'
    zpath = os.path.join(RAW, f'BACI_{hs}_V202601.zip')
    c2l = codes_for(hs); codes = set(c2l)
    acc = {}                                              # label -> {iso2: [value, qty]}
    for p in _baci.year(year, columns=['i', 'k', 'v', 'q'], codes=codes, nom=hs).itertuples(index=False):
        frm = num2iso.get(str(p.i))
        if not frm:
            continue
        if p.v != p.v:
            continue
        v = p.v * 1000.0
        qv = p.q if p.q == p.q else 0.0
        for lab in c2l[p.k]:
            e = acc.setdefault(lab, {}).setdefault(frm, [0.0, 0.0])
            e[0] += v; e[1] += qv
    out = {}
    for lab, exps in acc.items():
        vtot = sum(e[0] for e in exps.values())
        qtot = sum(e[1] for e in exps.values())
        if vtot <= 0:
            continue
        vsh = {c: e[0] / vtot for c, e in exps.items()}
        rec = {'val_hhi': round(sum(s * s for s in vsh.values()), 3),
               'val_cn': round(vsh.get('CN', 0.0) * 100, 1)}
        if qtot > 0:
            qsh = {c: e[1] / qtot for c, e in exps.items() if e[1] > 0}
            tot = sum(qsh.values()) or 1
            qsh = {c: s / tot for c, s in qsh.items()}
            rec['qty_hhi'] = round(sum(s * s for s in qsh.values()), 3)
            rec['qty_cn'] = round(qsh.get('CN', 0.0) * 100, 1)
        else:
            rec['qty_hhi'] = None; rec['qty_cn'] = None
        # implied unit value (USD/tonne) — world, China, and rest-of-world
        cv, cq = exps.get('CN', [0.0, 0.0])
        rec['uv'] = round(vtot / qtot, 1) if qtot > 0 else None
        rec['china_uv'] = round(cv / cq, 1) if cq > 0 else None
        rec['row_uv'] = round((vtot - cv) / (qtot - cq), 1) if (qtot - cq) > 0 else None
        out[lab] = rec
    return out

YEARS = list(range(2002, 2017)) + list(range(2017, 2025))
vq = {y: process('HS02' if y <= 2016 else 'HS17', y) for y in YEARS}
for y in YEARS:
    print(f'  {y}: {len(vq[y])} materials')

# assemble per-material series
mats = {}
for m in data['materials']:
    lab = m['label']
    s = {'title': TITLES[lab], 'val_hhi': [], 'qty_hhi': [], 'val_cn': [], 'qty_cn': [],
         'uv': [], 'china_uv': [], 'row_uv': []}
    for y in YEARS:
        r = vq[y].get(lab, {})
        s['val_hhi'].append(r.get('val_hhi'))
        s['qty_hhi'].append(r.get('qty_hhi'))
        s['val_cn'].append(r.get('val_cn'))
        s['qty_cn'].append(r.get('qty_cn'))
        s['uv'].append(r.get('uv'))
        s['china_uv'].append(r.get('china_uv'))
        s['row_uv'].append(r.get('row_uv'))
    # price-effect score (latest year): value-HHI minus volume-HHI (positive = value more concentrated than volume)
    vh, qh = s['val_hhi'][-1], s['qty_hhi'][-1]
    s['price_gap'] = round((vh - qh), 3) if (vh is not None and qh is not None) else None
    vc, qc = s['val_cn'][-1], s['qty_cn'][-1]
    s['china_gap'] = round((vc - qc), 1) if (vc is not None and qc is not None) else None
    mats[lab] = s

json.dump({'years': YEARS, 'materials': mats},
          open(os.path.join(ROOT, 'out', 'volume.json'), 'w', encoding='utf8'), indent=1)
print('\nLargest value>volume CONCENTRATION gaps (price effect in HHI):')
for lab, s in sorted(mats.items(), key=lambda kv: (kv[1]['price_gap'] or -9), reverse=True)[:6]:
    print(f"  {s['title']:<22} val_HHI {s['val_hhi'][-1]} vs qty_HHI {s['qty_hhi'][-1]}  gap +{s['price_gap']}")
print('Largest value>volume CHINA-SHARE gaps:')
for lab, s in sorted(mats.items(), key=lambda kv: (kv[1]['china_gap'] or -99), reverse=True)[:6]:
    print(f"  {s['title']:<22} val_CN {s['val_cn'][-1]}% vs qty_CN {s['qty_cn'][-1]}%  gap +{s['china_gap']}")

# ---- page (static; fetches volume.json at runtime) ----
HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Value vs volume — Critical Materials Atlas</title>
<meta name="description" content="Separating real concentration from price effects: export concentration and China share computed in both trade value and physical volume (tonnes) for 32 critical materials, 2002-2024.">
<meta property="og:title" content="Value vs volume — is the concentration real or a price effect?">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>.chartwrap{background:#fff;border:1px solid #e3e9e8;border-radius:10px;padding:1rem 1rem .5rem;margin:1rem 0}.chart{width:100%;height:380px}select#mat{font:inherit;padding:.4rem .6rem;border:1px solid #cdd6d4;border-radius:7px;font-weight:600}.muted{color:#5a6b68;font-size:.86rem}</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · value vs volume</div>
  <h1>The concentration is real, not a price mirage</h1>
  <p class="deck">Trade value is price &times; quantity, so a concentration measured in dollars <i>could</i> be a price story. It mostly isn&rsquo;t. Measured in physical <b>tonnes</b>, the export concentration <b>holds for 28 of 32 materials</b> &mdash; only 4 (beryllium, tungsten, helium, niobium) are meaningfully inflated by high prices, and 6 are actually <i>more</i> concentrated in tonnes than in dollars. The chokepoints are real quantity concentration, not a dollar illusion &mdash; the same robustness the <a href="findings">origin gap</a> shows.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout">Where a material&rsquo;s value-share sits above its volume-share, the apparent concentration is partly <b>price</b>, not tonnage &mdash; lithium is the textbook case: its value exploded in the 2021&ndash;22 price spike while tonnage barely moved.
  <details class="howto"><summary>How it&rsquo;s computed</summary>
  <p>For each material and year I compute the export Herfindahl and China&rsquo;s export share in <b>value</b> (USD) and in <b>volume</b> (metric tons, from BACI quantity, ~94% coverage), 2002&ndash;2024. When value-HHI sits above volume-HHI &mdash; or value-China-share above volume-China-share &mdash; a high-priced producer or material is weighing more in dollars than in tonnes.</p>
  <p class="howto-src"><b>Caveat:</b> ~6% of flows lack reported quantity (the volume series is computed over reported-tonnage flows); BACI quantities are partly estimated. Computed by <code>build_vq.py</code>.</p>
  </details></div>
  <div class="chartwrap">
    <div style="display:flex;align-items:center;gap:.7rem;flex-wrap:wrap;margin-bottom:.4rem">
      <b>Material:</b> <select id="mat" aria-label="Material"></select>
      <span class="muted">export concentration (HHI) &amp; China share — value vs volume</span></div>
    <div id="c1" class="chart"></div>
    <p id="lab" class="muted" style="margin:.4rem 0 0"></p>
  </div>
  <div class="chartwrap">
    <div style="font-weight:600;font-size:.92rem;margin-bottom:.2rem">Implied unit value (price) <span id="uvlab" class="muted" style="font-weight:400"></span></div>
    <div id="c2" class="chart" style="height:300px"></div>
    <p class="muted" style="margin:.3rem 0 0">Implied price = export value &divide; tonnage (USD/tonne), derived from the trade data itself. <span style="color:#c0392b">China</span> vs the <span style="color:#0e7c74">rest of the world</span>: where China's $/tonne sits <i>above</i> the rest, it is exporting the higher-value <b>processed</b> form rather than ore &mdash; which is precisely why its value-share can exceed its volume-share. (Unit values from trade data are noisy &mdash; quality/product mix varies &mdash; so read trends, not the exact level.)</p>
  </div>
  <h2 style="margin:1.6rem 0 .4rem">Where value overstates concentration (the price effect)</h2>
  <p class="muted" style="margin-top:0">Materials ranked by how much more concentrated they look in <i>value</i> than in <i>volume</i> in the latest year (HHI gap, &times;100, and China-share gap). A large positive gap means the value figure is partly price.</p>
  <table id="tab"><thead><tr><th>Material</th><th class="n">value HHI</th><th class="n">volume HHI</th><th class="n">price gap (×100)</th><th class="n">China value%</th><th class="n">China volume%</th></tr></thead><tbody></tbody></table>
  <p class="note">Computed from BACI HS02 + HS17 (value &amp; quantity) &rarr; <a href="out/volume.json">volume.json</a>. Volume = metric tons; value = USD. The dotted line in the chart marks the 2017 HS-vintage join.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>UN Comtrade · CEPII BACI (value &amp; quantity)</div>
  <div class="fineprint">Volume from BACI quantity (~94% coverage, partly estimated). Value = price × quantity.</div>
</div></footer>
<script>
const $=s=>document.querySelector(s);
fetch('out/volume.json').then(r=>r.json()).then(V=>{
  const ys=V.years, sel=$('#mat');
  Object.keys(V.materials).forEach(k=>{const o=document.createElement('option');o.value=k;o.textContent=V.materials[k].title;sel.appendChild(o);});
  const c=echarts.init($('#c1'));
  const c2=echarts.init($('#c2'));
  const mk={symbol:'none',silent:true,lineStyle:{type:'dotted',color:'#cbd5d3'},data:[{xAxis:'2017'}]};
  function draw(k){
    const m=V.materials[k];
    c.setOption({tooltip:{trigger:'axis'},legend:{top:0},grid:{left:48,right:54,top:30,bottom:28},
      xAxis:{type:'category',data:ys,boundaryGap:false},
      yAxis:[{type:'value',name:'HHI',min:0,max:1},{type:'value',name:'China %',min:0,max:100,position:'right',splitLine:{show:false},axisLabel:{formatter:'{value}%'}}],
      series:[
        {name:'HHI — value',type:'line',smooth:true,showSymbol:false,lineWidth:2.6,data:m.val_hhi,itemStyle:{color:'#c0392b'},markLine:mk},
        {name:'HHI — volume',type:'line',smooth:true,showSymbol:false,lineWidth:2.6,lineStyle:{type:'dashed'},data:m.qty_hhi,itemStyle:{color:'#0e7c74'}},
        {name:'China — value',type:'line',smooth:true,showSymbol:false,yAxisIndex:1,lineWidth:1.6,data:m.val_cn,itemStyle:{color:'#e08a3c'}},
        {name:'China — volume',type:'line',smooth:true,showSymbol:false,yAxisIndex:1,lineWidth:1.6,lineStyle:{type:'dashed'},data:m.qty_cn,itemStyle:{color:'#6d5fb0'}}
      ]},true);
    const pg=m.price_gap, cg=m.china_gap;
    $('#lab').innerHTML = (pg!=null? '<b>Price effect:</b> value-HHI is '+(pg>=0?'+':'')+(pg*100).toFixed(0)+' (×100) vs volume-HHI'+(cg!=null?(' · China is '+(cg>=0?'+':'')+cg.toFixed(0)+'pp higher by value than by volume'):'')+'. Solid = value, dashed = volume.' : 'volume data limited for this material.');
    c2.setOption({tooltip:{trigger:'axis',valueFormatter:v=>v==null?'':('$'+Math.round(v).toLocaleString()+'/t')},legend:{top:0},grid:{left:66,right:20,top:30,bottom:28},xAxis:{type:'category',data:ys,boundaryGap:false},yAxis:{type:'value',name:'$/tonne',scale:true},series:[{name:'world',type:'line',smooth:true,showSymbol:false,lineWidth:2.4,data:m.uv,itemStyle:{color:'#15323a'},markLine:mk},{name:'China',type:'line',smooth:true,showSymbol:false,lineWidth:2,data:m.china_uv,itemStyle:{color:'#c0392b'}},{name:'rest of world',type:'line',smooth:true,showSymbol:false,lineWidth:2,data:m.row_uv,itemStyle:{color:'#0e7c74'}}]},true);
    const cu=m.china_uv.at(-1), ru=m.row_uv.at(-1); const ul=document.getElementById('uvlab'); if(ul) ul.textContent=(cu!=null&&ru!=null&&ru>0)?('· China $'+Math.round(cu).toLocaleString()+'/t vs RoW $'+Math.round(ru).toLocaleString()+'/t ('+(cu>=ru?'+':'')+Math.round((cu/ru-1)*100)+'%'+(cu>ru*1.1?' — China exports the higher-value form':'')+')'):'';
  }
  sel.onchange=()=>draw(sel.value);
  draw(V.materials.lithium?'lithium':Object.keys(V.materials)[0]);
  const tb=document.querySelector('#tab tbody');
  Object.keys(V.materials).map(k=>[k,V.materials[k]]).filter(e=>e[1].price_gap!=null)
    .sort((a,b)=>b[1].price_gap-a[1].price_gap)
    .forEach(e=>{const k=e[0],m=e[1];const tr=document.createElement('tr');
      tr.innerHTML='<td><a href="profile-'+k+'.html">'+m.title+'</a></td>'+
        '<td class="n">'+(m.val_hhi.at(-1)??'—')+'</td><td class="n">'+(m.qty_hhi.at(-1)??'—')+'</td>'+
        '<td class="n" style="font-weight:700;color:'+(m.price_gap>0.05?'#c0392b':m.price_gap<-0.05?'#3f9b46':'#9aa6ad')+'">'+(m.price_gap>=0?'+':'')+(m.price_gap*100).toFixed(0)+'</td>'+
        '<td class="n">'+(m.val_cn.at(-1)??'—')+'%</td><td class="n">'+(m.qty_cn.at(-1)??'—')+'%</td>';
      tb.appendChild(tr);});
  window.addEventListener('resize',()=>{c.resize();c2.resize();});
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'volume.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote volume.html')
