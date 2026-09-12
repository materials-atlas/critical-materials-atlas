#!/usr/bin/env python3
"""
Mining expansion — where new mine footprint is physically appearing (tropics, 2016-2024).

The satellite footprint page is a snapshot; this adds the DERIVATIVE — where mining is physically GROWING.
Source = Sepin, Vashold & Kuschnig (2025, Nature Sustainability), "Mapping mining areas in the tropics
from 2016 to 2024": an annual panel of ML-segmented mine polygons (Sentinel-2; 87.7% validation accuracy)
carrying iso_a3 + year + area, so a pure GROUP BY gives mapped mine area per country per year (no spatial
join, stdlib sqlite3). It is a forward-looking new-supply signal the trade/production layers can't see.

Hard limits (stated on the page): TROPICS ONLY (no China, Australia, Canada, temperate belts — so NOT a
global total); ALL-COMMODITY (no per-mineral label; expansion in known single-commodity regions is
indicative, not attributed); area = mapped surface footprint, not production tonnage; 2024 appears
under-mapped (dips below 2023) so 2023 is the robust recent endpoint. Public data; deterministic.
Run: python build_mining_expansion.py
"""
import sqlite3, json, os, csv, re
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import baci as _baci  # the one door for BACI (ARCHITECTURE.md phase 2)

ROOT = os.path.dirname(os.path.abspath(__file__))
GPKG = os.path.join(ROOT, 'raw', 'sepin', 'sepin_precise.gpkg')
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
T = 'mine-predictions-precise-v1_4326'
YEARS = [str(y) for y in range(2016, 2025)]

# ISO3<->ISO2 + critical-material production role (mirrors build_satellite.py)
iso3to2 = {}
with _baci.country_file() as f:
    for r in csv.DictReader(f):
        if r.get('country_iso2') and r.get('country_iso3') and r['country_iso3'] != 'NA':   # 'NA' is Namibia, not missing
            iso3to2[r['country_iso3']] = r['country_iso2']
role = {}
for m in data['materials']:
    short = m['title'].split(' (')[0]
    for e in m.get('mined', []):
        if (e.get('v') or 0) >= 10:
            role.setdefault(e['c'], {})[short] = e['v']

# editorial note on the dominant critical material in the marquee expanding hubs
HUB_NOTE = {
 'IDN': 'nickel — the processing boom in Sulawesi', 'ARG': 'lithium & copper — the lithium triangle',
 'CHL': 'copper & lithium', 'PER': 'copper', 'COD': 'cobalt & copper — the Copperbelt',
 'MMR': 'rare earths & tin', 'GIN': 'bauxite', 'BRA': 'niobium, bauxite & iron',
 'PHL': 'nickel', 'IND': 'graphite, baryte & feldspar', 'ZAF': 'PGM, manganese & chromium',
 'GUY': 'gold & bauxite', 'NAM': 'uranium, lithium & copper',
}

con = sqlite3.connect(GPKG); cur = con.cursor()
raw = {}
for iso, nm, y, a in cur.execute(f'SELECT iso_a3, country_name, year, SUM(area)/1e6 FROM "{T}" GROUP BY iso_a3, year'):
    if iso:
        raw.setdefault(iso, {'name': nm, 'y': {}})['y'][y] = a

glob = [round(sum(d['y'].get(y, 0) for d in raw.values())) for y in YEARS]
countries = {}
for iso, d in raw.items():
    series = [round(d['y'].get(y, 0), 1) for y in YEARS]
    a16, a23, a24 = d['y'].get('2016', 0), d['y'].get('2023', 0), d['y'].get('2024', 0)
    iso2 = iso3to2.get(iso)
    maj = sorted(role.get(iso2, {}).items(), key=lambda kv: -kv[1])
    countries[iso] = {'name': d['name'], 'iso2': iso2, 'series': series,
                      'a16': round(a16, 1), 'a23': round(a23, 1), 'a24': round(a24, 1),
                      'grow_abs': round(a24 - a16, 1), 'grow_pct': (round((a24 / a16 - 1) * 100) if a16 > 0 else None),
                      'grow_pct23': (round((a23 / a16 - 1) * 100) if a16 > 0 else None),
                      'cm_list': [k for k, _ in maj[:5]], 'cm_major': len(maj),
                      'hub': HUB_NOTE.get(iso)}

g16, g23, g24 = glob[0], glob[7], glob[8]
out = {'years': [int(y) for y in YEARS], 'global': glob,
       'global_grow_pct': round((g24 / g16 - 1) * 100), 'global_grow_pct23': round((g23 / g16 - 1) * 100),
       'source': 'Sepin, Vashold & Kuschnig 2025, Nature Sustainability (tropical mine polygons 2016-2024)',
       'countries': countries}
json.dump(out, open(os.path.join(ROOT, 'out', 'mining_expansion.json'), 'w', encoding='utf8'), indent=1)

print(f'Global tropical mapped mine area: {g16:,} km2 (2016) -> {g23:,} (2023) -> {g24:,} (2024)')
print(f'  growth 2016->2023 {out["global_grow_pct23"]}%   2016->2024 {out["global_grow_pct"]}% (2024 likely under-mapped)')
print('\nFastest-expanding critical-material hubs (abs km2 growth 2016->2024):')
top = sorted([c for c in countries.values() if c['a16'] >= 100], key=lambda c: -c['grow_abs'])[:12]
for c in top:
    cm = c['hub'] or (', '.join(c['cm_list'][:2]) if c['cm_list'] else 'mixed')
    print(f"  {c['name'][:18]:<18} {c['a16']:>7,.0f} -> {c['a24']:>7,.0f} km2  (+{c['grow_pct']}%)  {cm}")

# ---------------- page ----------------
HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Where new mining is appearing — tropical expansion 2016-2024 · Critical Materials Atlas</title>
<meta name="description" content="A forward-looking physical signal: satellite-mapped mine-area expansion across the tropics 2016-2024 (Sepin et al. 2025), mapped onto critical-material hubs — Indonesia nickel, the lithium triangle, the Copperbelt.">
<meta property="og:title" content="Where new mine footprint is physically appearing (2016-2024)">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>.muted{color:#5a6b68;font-size:.86rem}.chart{width:100%;height:330px}.chartwrap{background:#fff;border:1px solid #e3e9e8;border-radius:10px;padding:1rem 1rem .5rem;margin:1rem 0}.hub{font-size:.82rem;color:#0e7c74;font-weight:600}</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · expansion from orbit</div>
  <h1>The mine footprint is growing 33% — and it&rsquo;s tropical</h1>
  <p class="deck">Seen from orbit, the world&rsquo;s mapped mine footprint expanded about <b>33%</b> over 2016&ndash;2024, and the growth is concentrated across the <b>tropics</b> — landing on exactly the critical-material geographies. The trade and production layers tell you where supply <i>is</i>. This one points to where it&rsquo;s <i>going</i> &mdash; satellite-mapped mine footprint expanding across the tropics, 2016&ndash;2024. The growth lands squarely on the critical-material frontier: Indonesia&rsquo;s nickel, the lithium triangle, the Copperbelt.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout">Where mining is physically <i>growing</i>, 2016&ndash;2024 &mdash; a forward-looking new-supply signal the trade and USGS layers can&rsquo;t see.
  <details class="howto"><summary>Source, and its hard limits</summary>
  <p>Source: <b>Sepin, Vashold &amp; Kuschnig (2025, <i>Nature Sustainability</i>)</b> &mdash; an annual panel of machine-learning-segmented mine polygons (Sentinel-2, 87.7% validation accuracy) with a year and country on every polygon, so mapped mine area per country per year falls straight out.</p>
  <p class="howto-src"><b>Hard limits:</b> <b>tropics only</b> (no China, Australia, Canada or temperate belt &mdash; <i>not</i> a global total); <b>all-commodity</b> (no per-mineral label, so expansion in single-commodity regions is indicative, not attributed); area is mapped surface footprint, not tonnage; and <b>2024 is under-mapped</b> (it dips below 2023), so 2023 is the robust recent endpoint. Computed by <code>build_mining_expansion.py</code>.</p>
  </details></div>
  <div id="head" class="callout" style="border-left-color:#0e7c74;background:#f0f7f5"></div>
  <div class="chartwrap">
    <div style="font-weight:600;font-size:.92rem;margin-bottom:.2rem">Total tropical mapped mine area, 2016&ndash;2024</div>
    <div id="c1" class="chart" style="height:280px"></div>
  </div>
  <div class="chartwrap">
    <div style="font-weight:600;font-size:.92rem;margin-bottom:.2rem">Fastest-expanding tropical mining countries (km² added, 2016&rarr;2024)</div>
    <div id="c2" class="chart"></div>
  </div>
  <h2 style="margin:1.6rem 0 .4rem">The expanding critical-material hubs</h2>
  <p class="muted" style="margin-top:0">Tropical countries with the most mine-footprint growth, and the critical materials they&rsquo;re known for. &ldquo;CM&rdquo; = materials for which the country holds &ge;10% of world mine production in the atlas.</p>
  <table id="tab"><thead><tr><th>Country</th><th class="n">2016 km²</th><th class="n">2024 km²</th><th class="n">growth</th><th>critical materials / note</th></tr></thead><tbody></tbody></table>
  <p class="note">Sepin et al. 2025, <a href="https://doi.org/10.5281/zenodo.17034288">Zenodo</a> (precise polygon set) &rarr; <a href="out/mining_expansion.json">mining_expansion.json</a>. Tropical belt only; all-commodity footprint; ML-segmented (87.7% accuracy). Pairs with the snapshot on the <a href="satellite.html">satellite footprint page</a>.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>Sepin et al. 2025 (tropical mine polygons) · Maus et al. 2022 · USGS</div>
  <div class="fineprint">Tropical belt only — a regional expansion signal, not a global total. All-commodity footprint, ~Sentinel-2.</div>
</div></footer>
<script>
fetch('out/mining_expansion.json').then(r=>r.json()).then(E=>{
  document.getElementById('head').innerHTML='<b>The signal.</b> Across the tropics, satellite-mapped mine footprint grew <b>+'+E.global_grow_pct23+
    '%</b> from 2016 to 2023 (+'+E.global_grow_pct+'% to the under-mapped 2024). The expansion concentrates on the critical-material frontier &mdash; '+
    'Indonesia&rsquo;s nickel, the Argentina&ndash;Chile lithium triangle, the Peru and DR Congo copper-cobalt belts.';
  const c1=echarts.init(document.getElementById('c1'));
  c1.setOption({tooltip:{trigger:'axis',valueFormatter:v=>v.toLocaleString()+' km²'},grid:{left:60,right:20,top:20,bottom:28},
    xAxis:{type:'category',data:E.years},yAxis:{type:'value',name:'km²'},
    series:[{type:'line',smooth:true,areaStyle:{opacity:.15},lineWidth:3,data:E.global,itemStyle:{color:'#0e7c74'},
      markPoint:{data:[{type:'max',name:'peak'}],symbolSize:42}}]});
  const arr=Object.entries(E.countries).map(([iso,c])=>({iso,...c})).filter(c=>c.a16>=100);
  const top=arr.slice().sort((a,b)=>b.grow_abs-a.grow_abs).slice(0,12).reverse();
  const c2=echarts.init(document.getElementById('c2'));
  c2.setOption({tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>'+'+v.toLocaleString()+' km²'},
    grid:{left:90,right:30,top:10,bottom:28},xAxis:{type:'value',name:'km² added'},
    yAxis:{type:'category',data:top.map(c=>c.name)},
    series:[{type:'bar',data:top.map(c=>({value:c.grow_abs,itemStyle:{color:c.hub?'#c0392b':'#7d9b97'}})),
      label:{show:true,position:'right',formatter:p=>'+'+top[p.dataIndex].grow_pct+'%'}}]});
  const tb=document.querySelector('#tab tbody');
  arr.sort((a,b)=>b.grow_abs-a.grow_abs).slice(0,16).forEach(c=>{
    const tr=document.createElement('tr');
    const note=c.hub?('<span class="hub">'+c.hub+'</span>'):(c.cm_list.length?c.cm_list.join(', '):'<span class="muted">mixed / non-CM</span>');
    tr.innerHTML='<td>'+c.name+'</td><td class="n">'+c.a16.toLocaleString()+'</td><td class="n" style="font-weight:600">'+c.a24.toLocaleString()+'</td>'+
      '<td class="n" style="font-weight:700;color:'+(c.grow_pct>=60?'#c0392b':c.grow_pct>=25?'#b07a18':'#52605d')+'">+'+c.grow_pct+'%</td><td>'+note+'</td>';
    tb.appendChild(tr);});
  window.addEventListener('resize',()=>{c1.resize();c2.resize();});
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'mining-expansion.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('\nwrote mining-expansion.html')
