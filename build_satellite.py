#!/usr/bin/env python3
"""
Satellite layer — physical mine footprints from orbit, as an independent cross-check.

The atlas measures concentration from trade (Comtrade/BACI) and production shares (USGS). This adds a
THIRD, independent lens: where mining physically happens, seen from satellites. Source = Maus et al. (2022,
Scientific Data) "An update on global mining land use" — 44,929 mine-area polygons (Sentinel-2, 2019),
ISO3 + area km2 per polygon, a peer-reviewed DERIVED dataset (no imagery processing needed). We:
  (1) aggregate mine footprint (area km2, site count) per country and set it beside our critical-material
      production geography — does physical mining intensity corroborate the producer story?
  (2) curate flagship critical-material mines and snap each to its nearest mapped Maus polygon, attaching
      the real satellite footprint area.

Honest caveat: Maus polygons are ALL-COMMODITY (coal, iron, gold included) with no reliable per-commodity
label, so country footprint = total mining intensity, not critical-material-specific. The flagship sites
supply the material-specific view. Imagery vintage ~2019. Public data; deterministic. Run: python build_satellite.py
"""
import sqlite3, struct, json, os, csv, math
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import baci as _baci  # the one door for BACI (ARCHITECTURE.md phase 2)

ROOT = os.path.dirname(os.path.abspath(__file__))
GPKG = os.path.join(ROOT, 'raw', 'maus', 'maus_v2.gpkg')
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))

# ISO3 <-> ISO2 bridge (BACI country table)
iso3to2, iso2to3 = {}, {}
with _baci.country_file() as f:
    for r in csv.DictReader(f):
        a2, a3 = r.get('country_iso2'), r.get('country_iso3')
        if a2 and a3:   # 'NA' is Namibia, not missing
            iso3to2[a3] = a2; iso2to3[a2] = a3

# critical-material production role per country (ISO2) from data.json mine shares
role = {}
for m in data['materials']:
    short = m['title'].split(' (')[0]
    for e in m.get('mined', []):
        c, v = e['c'], (e.get('v') or 0)
        r = role.setdefault(c, {'all': set(), 'major': {}})
        r['all'].add(short)
        if v >= 10:
            r['major'][short] = v

con = sqlite3.connect(GPKG)
agg = con.execute('SELECT ISO3_CODE,COUNTRY_NAME,SUM(AREA),COUNT(*) FROM mining_polygons GROUP BY ISO3_CODE').fetchall()

countries = {}
for iso3, nm, area, n in agg:
    a2 = iso3to2.get(iso3)
    r = role.get(a2, {'all': set(), 'major': {}})
    maj = sorted(r['major'].items(), key=lambda kv: -kv[1])
    countries[iso3] = {'name': nm, 'iso2': a2, 'area_km2': round(area, 1), 'n_sites': n,
                       'cm_major': len(maj), 'cm_all': len(r['all']),
                       'cm_list': [k for k, _ in maj[:6]]}

# all polygon centroids (from GPKG envelope) for flagship snapping
cent = []   # (lon, lat, iso3, area)
for iso3, area, blob in con.execute('SELECT ISO3_CODE,AREA,geom FROM mining_polygons'):
    flags = blob[3]; le = '<' if (flags & 1) else '>'
    minx, maxx, miny, maxy = struct.unpack(le + '4d', blob[8:40])
    cent.append(((minx + maxx) / 2, (miny + maxy) / 2, iso3, area))

def hav(la1, lo1, la2, lo2):
    R = 6371.0; p = math.pi / 180
    a = (math.sin((la2 - la1) * p / 2) ** 2 +
         math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * R * math.asin(min(1, math.sqrt(a)))

# curated flagship critical-material mines (name, material, ISO3, lat, lon, note)
FLAG = [
 ('Bayan Obo','Rare earths','CHN',41.77,109.97,'The world’s largest rare-earth deposit — the backbone of Chinese REE supply.'),
 ('Mountain Pass','Rare earths','USA',35.48,-115.53,'The only operating US rare-earth mine (MP Materials).'),
 ('Mount Weld','Rare earths','AUS',-28.86,122.55,'Lynas’ deposit — the largest REE source outside China.'),
 ('Greenbushes','Lithium','AUS',-33.87,116.06,'The world’s largest hard-rock (spodumene) lithium mine.'),
 ('Salar de Atacama','Lithium','CHL',-23.50,-68.20,'Brine operations (SQM, Albemarle) in the lithium triangle.'),
 ('Salar del Hombre Muerto','Lithium','ARG',-25.40,-67.00,'Argentina’s flagship lithium-brine field.'),
 ('Pilgangoora','Lithium / tantalum','AUS',-21.00,118.90,'Major spodumene + tantalum operation in the Pilbara.'),
 ('Tenke Fungurume','Cobalt / copper','COD',-10.60,26.50,'One of the largest cobalt-copper mines on Earth (DRC Copperbelt).'),
 ('Mutanda','Cobalt / copper','COD',-10.75,25.97,'Among the single largest cobalt producers worldwide.'),
 ('Kamoa-Kakula','Copper','COD',-10.77,25.29,'One of the highest-grade major copper mines globally.'),
 ('Escondida','Copper','CHL',-24.27,-69.07,'The world’s largest copper mine by output.'),
 ('Norilsk','Nickel / palladium / PGM','RUS',69.33,88.20,'Dominant source of palladium and a major nickel hub.'),
 ('Sorowako','Nickel','IDN',-2.53,121.36,'PT Vale’s laterite nickel operation in Sulawesi.'),
 ('Morowali (IMIP)','Nickel','IDN',-2.74,122.13,'Centre of Indonesia’s nickel-processing boom.'),
 ('Mogalakwena','Platinum / PGM','ZAF',-24.00,28.97,'The world’s largest open-pit PGM mine (Bushveld).'),
 ('Kalahari Manganese Field','Manganese','ZAF',-27.20,22.90,'Holds the bulk of global manganese reserves.'),
 ('Moanda','Manganese','GAB',-1.55,13.20,'Comilog — one of the largest manganese mines worldwide.'),
 ('Araxá','Niobium','BRA',-19.62,-46.96,'CBMM — supplies the large majority of the world’s niobium.'),
 ('Catalão','Niobium','BRA',-18.10,-47.90,'Brazil’s second major niobium district.'),
 ('Sangarédi / Boké','Bauxite','GIN',11.10,-14.00,'Guinea’s bauxite belt — a leading global supplier.'),
 ('Weipa','Bauxite','AUS',-12.65,141.88,'One of the world’s largest bauxite operations.'),
 ('Khouribga','Phosphate','MAR',32.88,-6.91,'OCP — part of the world’s largest phosphate reserves.'),
 ('Xikuangshan','Antimony','CHN',27.74,111.46,'Known as the “antimony capital of the world.”'),
 ('Jiangxi ion-clay','Heavy rare earths','CHN',25.00,114.50,'Ion-adsorption clays — dominant source of heavy REEs.'),
 ('Olympic Dam','Copper / uranium / REE','AUS',-30.44,136.89,'Giant poly-metallic deposit (copper, uranium, rare earths).'),
 ('Grasberg','Copper','IDN',-4.06,137.11,'One of the largest copper-gold mines in the world.'),
 ('Antamina','Copper / zinc','PER',-9.53,-77.05,'A top Peruvian copper-zinc mine.'),
 ('Wodgina','Lithium / tantalum','AUS',-21.18,118.68,'Large spodumene + tantalum mine in the Pilbara.'),
 ('Balama','Graphite','MOZ',-13.30,38.60,'Syrah Resources — a leading natural-graphite mine.'),
 ('Heilongjiang graphite','Graphite','CHN',47.60,130.80,'Centre of China’s natural-graphite output.'),
 ('Jiangxi tungsten','Tungsten','CHN',25.40,114.90,'Heart of Chinese tungsten mining.'),
 ('Richards Bay','Titanium / zircon','ZAF',-28.80,32.05,'Major mineral-sands (titanium, zircon) operation.'),
 ('Spor Mountain','Beryllium','USA',39.73,-113.20,'The leading global source of beryllium.'),
 ('Bisie','Tin','COD',-1.00,27.90,'A major artisanal-to-industrial tin district.'),
 ('Spruce Pine','Silicon (high-purity quartz)','USA',35.92,-82.06,"The world's main source of ultra-pure quartz for chips and solar."),
 ('Stillwater','Palladium / PGM','USA',45.40,-109.88,"The only significant US source of palladium and platinum."),
 ('Bushveld (Brits)','Vanadium','ZAF',-25.64,27.77,"Vanadium from the Bushveld magnetite complex — a leading source."),
 ('Kırka','Borates','TUR',39.28,30.50,"Eti Maden's Kırka — the world's largest borate deposit."),
 ('Boron','Borates','USA',35.05,-117.68,"Rio Tinto's U.S. Borax mine, California — a top borate source."),
 ('Bou Craa','Phosphate','ESH',26.10,-12.85,"One of the world's largest phosphate operations (Western Sahara)."),
 ('Khibiny (Kola)','Phosphate','RUS',67.70,33.70,"Apatite from the Kola Peninsula — Russia's main phosphate source."),
 ('Kwale','Titanium / zircon','KEN',-4.28,39.40,"Base Titanium's mineral-sands mine — a major titanium source."),
 ('Kolwezi','Cobalt / copper','COD',-10.72,25.47,"Heart of the DRC Copperbelt — among the largest cobalt sources."),
 ('Rubaya','Tantalum','COD',-1.55,28.90,"A major coltan (tantalum) district in eastern DR Congo."),
 ('Fugu (Shaanxi)','Magnesium','CHN',39.03,111.07,"Centre of China's Pidgeon-process magnesium belt."),
 ('Milas','Feldspar','TUR',37.32,27.78,"Muğla/Milas — Turkey leads the world in feldspar."),
 ('Mangampeta','Baryte','IND',14.43,79.30,"Andhra Pradesh — India is a leading baryte producer."),
 ('Anzob','Antimony','TJK',39.15,68.35,"Tajikistan's antimony district — a top global exporter."),
]
flagship = []
RAD = 25.0                                            # km: sum all mapped mine area within this radius (district footprint)
for name, mat, iso3, lat, lon, note in FLAG:
    tot, npoly = 0.0, 0
    for clon, clat, ciso, area in cent:
        if abs(clat - lat) > 0.5 or abs(clon - lon) > 0.7:   # cheap bounding-box prefilter
            continue
        if hav(lat, lon, clat, clon) <= RAD:
            tot += area; npoly += 1
    flagship.append({'name': name, 'mat': mat, 'iso3': iso3, 'iso2': iso3to2.get(iso3),
                     'lat': lat, 'lon': lon, 'note': note,
                     'foot_km2': round(tot, 1) if npoly else None, 'n_poly': npoly})

# headline cross-check: of the top-15 footprint countries, how many are major critical-material producers
top = sorted(countries.items(), key=lambda kv: -kv[1]['area_km2'])
top15 = top[:15]
hub15 = sum(1 for _, c in top15 if c['cm_major'] >= 1)
tot_area = round(sum(c['area_km2'] for c in countries.values()))
tot_sites = sum(c['n_sites'] for c in countries.values())

out = {'source': 'Maus et al. 2022, Scientific Data (global mining polygons v2, Sentinel-2 ~2019)',
       'total_area_km2': tot_area, 'total_sites': tot_sites, 'n_countries': len(countries),
       'hub15': hub15, 'countries': countries, 'flagship': flagship}
json.dump(out, open(os.path.join(ROOT, 'out', 'satellite.json'), 'w', encoding='utf8'), indent=1)

print(f'total mapped mine footprint: {tot_area:,} km2 across {tot_sites:,} sites, {len(countries)} countries')
print(f'cross-check: {hub15} of the top-15 footprint countries are MAJOR critical-material producers in the atlas')
print('\nTop footprint countries (km2 | sites | major CM count):')
for iso3, c in top15:
    print(f"  {iso3} {c['name'][:20]:<20} {c['area_km2']:>8,.0f} | {c['n_sites']:>5} | CM major {c['cm_major']:>2}  {','.join(c['cm_list'][:3])}")
print(f'\nFlagship sites — mapped mine area within {int(RAD)} km (district footprint):')
for s in flagship:
    fp = f"{s['foot_km2']} km2 ({s['n_poly']} polys)" if s['foot_km2'] else 'no mapped footprint within radius'
    print(f"  {s['name'][:24]:<24} {s['mat'][:22]:<22} {fp}".encode('ascii', 'replace').decode())

# ---------------- page ----------------
HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>From orbit — satellite mine footprints · Critical Materials Atlas</title>
<meta name="description" content="An independent cross-check from space: physical mine footprints (Maus et al. 2022, Sentinel-2) for 145 countries, set beside the atlas's critical-material production geography, plus flagship mines snapped to their real satellite footprints.">
<meta property="og:title" content="From orbit — do the satellites corroborate the supply map?">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>#map{width:100%;height:460px;background:#eef3f2;border:1px solid #e3e9e8;border-radius:10px}.jvm-tooltip{font:inherit!important}.muted{color:#5a6b68;font-size:.86rem}.flegend{display:flex;gap:1rem;flex-wrap:wrap;font-size:.82rem;color:#5a6b68;margin:.5rem 0}.flegend b{color:#15323a}</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="methodology.html">Methodology</a><a href="trends.html">Trends</a>
  <a href="volume.html" class="hideable">Value vs volume</a><a href="findings.html" class="hideable">Findings</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · from orbit</div>
  <h1>Do the satellites corroborate the supply map?</h1>
  <p class="deck">Every other page measures concentration from <i>trade</i> and <i>production statistics</i>. This one adds an independent physical lens: where mining actually scars the ground, seen from space &mdash; 44,929 mapped mine polygons across 145 countries &mdash; set beside the atlas&rsquo;s critical-material producers, with flagship mines snapped to their real satellite footprints. A companion page maps <a href="mining-expansion.html" style="color:#fff;text-decoration:underline">where mining is physically expanding &rarr;</a>.</p>
</div></section>
<article style="max-width:1060px">
  <div class="callout">An independent physical check on the supply map: how much mine footprint each country actually shows from orbit, set beside the producers the atlas already names. <span id="head"></span>
  <details class="howto"><summary>Source, and the all-commodity caveat</summary>
  <p>Source: <b>Maus et al. (2022, <i>Scientific Data</i>)</b> &mdash; a peer-reviewed dataset of mine-area polygons from Sentinel-2 imagery (~2019). I aggregate <b>physical mine footprint</b> (km&sup2; and site count) per country and lay it beside the production geography the atlas already shows.</p>
  <p class="howto-src"><b>Caveat:</b> these polygons are <b>all-commodity</b> (coal, iron, gold and more) with no reliable per-mineral label, so the country map is <i>total mining intensity</i>, not critical-material-specific &mdash; the flagship sites below carry the material-specific view. We <a href="commodity-attribution.html">quantified exactly how far commodity labelling gets &rarr;</a>: even with the best open mine database bolted on, only ~4% of the mapped footprint can be tied to a tracked critical material.</p>
  </details></div>
  <h2 style="margin:1.4rem 0 .4rem">Mine footprint from space &mdash; and flagship critical-material mines</h2>
  <p class="muted" style="margin-top:0">Shading = total mapped mine area per country (darker = more). Dots = curated flagship mines, sized by their nearest mapped footprint. Hover for detail.</p>
  <div id="map"></div>
  <div class="flegend"><span><b>Shade:</b> country mine footprint (km&sup2;)</span><span><b>&#9679;</b> flagship critical-material mine (hover)</span></div>
  <h2 style="margin:1.6rem 0 .4rem">Top mine-footprint countries vs their critical-material role</h2>
  <p class="muted" style="margin-top:0">&ldquo;Major CM&rdquo; = number of the atlas&rsquo;s 32 materials for which this country holds &ge;10% of mine production. Where a big footprint lines up with a high CM count, the satellites corroborate the supply story.</p>
  <table id="tab"><thead><tr><th>Country</th><th class="n">mine area km²</th><th class="n">sites</th><th class="n">major CM</th><th>leading critical materials</th></tr></thead><tbody></tbody></table>
  <h2 style="margin:1.6rem 0 .4rem">Flagship mines, snapped to their satellite footprint</h2>
  <table id="ftab"><thead><tr><th>Mine</th><th>Material</th><th>Country</th><th class="n">footprint km²</th></tr></thead><tbody></tbody></table>
  <p class="note">Footprint = total mapped Maus mine area within <b>25 km</b> of each mine &mdash; a district-scale, all-commodity footprint, not just the single pit. Source: <a href="https://doi.org/10.1594/PANGAEA.942325">Maus et al. 2022, PANGAEA</a> &rarr; <a href="out/satellite.json">satellite.json</a>. Imagery ~2019.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="mining-expansion.html">Mining expansion</a><br><a href="volume.html">Value vs volume</a><br><a href="trends.html">Trends</a><br><a href="methodology.html">Methodology</a></div>
  <div><h4>Sources</h4>Maus et al. 2022 (mine polygons) · UN Comtrade · CEPII BACI · USGS</div>
  <div class="fineprint">Satellite footprint is all-commodity (Maus et al., Sentinel-2 ~2019); a physical cross-check, not a per-mineral measure.</div>
</div></footer>
<script>
function ld(u){return new Promise((res,rej)=>{const s=document.createElement('script');s.src=u;s.onload=res;s.onerror=rej;document.head.appendChild(s);});}
function ldc(u){const l=document.createElement('link');l.rel='stylesheet';l.href=u;document.head.appendChild(l);}
ldc('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/css/jsvectormap.min.css');
Promise.all([fetch('out/satellite.json').then(r=>r.json()),
  ld('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/js/jsvectormap.min.js')
    .then(()=>ld('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/maps/world.js'))
]).then(([S])=>{
  document.getElementById('head').innerHTML=' <b>Result:</b> '+S.hub15+' of the 15 largest mine-footprint countries are major critical-material producers in the atlas &mdash; the physical map broadly corroborates the trade-and-production story. Total mapped footprint: '+S.total_area_km2.toLocaleString()+' km² across '+S.total_sites.toLocaleString()+' sites in '+S.n_countries+' countries.';
  // choropleth values by ISO2
  const vals={}; let mx=0;
  Object.values(S.countries).forEach(c=>{if(c.iso2){vals[c.iso2]=c.area_km2; if(c.area_km2>mx)mx=c.area_km2;}});
  const markers=S.flagship.map(s=>({name:s.name+' — '+s.mat+(s.foot_km2?(' · '+s.foot_km2+' km² footprint'):''),coords:[s.lat,s.lon],fp:s.foot_km2}));
  const map=new jsVectorMap({selector:'#map',map:'world',zoomButtons:true,
    regionStyle:{initial:{fill:'#dfe7e5'}},
    series:{regions:[{attribute:'fill',scale:['#e7eeec','#0e7c74','#0a3b39'],normalizeFunction:'polynomial',values:vals,min:0,max:mx}]},
    markers:markers,
    markerStyle:{initial:{fill:'#c0392b',stroke:'#fff','stroke-width':1.4,r:5},hover:{fill:'#e0512f',r:7}},
    onRegionTooltipShow(e,t,code){const c=Object.values(S.countries).find(x=>x.iso2===code);
      if(c){t.text('<b>'+c.name+'</b><br>mine footprint '+c.area_km2.toLocaleString()+' km² · '+c.n_sites+' sites'+(c.cm_major?('<br>major producer of '+c.cm_major+' critical material'+(c.cm_major>1?'s':'')+(c.cm_list.length?': '+c.cm_list.slice(0,4).join(', '):'')):''),true);}},
    onMarkerTooltipShow(e,t,i){t.text(markers[i].name,true);}
  });
  // size flagship markers by footprint
  setTimeout(()=>{document.querySelectorAll('#map .jvm-marker').forEach((el,i)=>{const fp=markers[i]&&markers[i].fp; if(fp){const r=Math.max(4,Math.min(13,3+Math.sqrt(fp)));el.setAttribute('r',r);}});},120);
  // country table
  const tb=document.querySelector('#tab tbody');
  Object.entries(S.countries).sort((a,b)=>b[1].area_km2-a[1].area_km2).slice(0,20).forEach(([iso3,c])=>{
    const tr=document.createElement('tr');
    tr.innerHTML='<td>'+c.name+'</td><td class="n">'+Math.round(c.area_km2).toLocaleString()+'</td><td class="n">'+c.n_sites.toLocaleString()+'</td>'+
      '<td class="n" style="font-weight:700;color:'+(c.cm_major>=3?'#c0392b':c.cm_major>=1?'#b07a18':'#9aa6ad')+'">'+c.cm_major+'</td><td class="muted">'+(c.cm_list.join(', ')||'—')+'</td>';
    tb.appendChild(tr);});
  // flagship table
  const fb=document.querySelector('#ftab tbody');
  S.flagship.slice().sort((a,b)=>(b.foot_km2||-1)-(a.foot_km2||-1)).forEach(s=>{
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+s.name+'</b><br><span class="muted" style="font-size:.8rem">'+s.note+'</span></td><td>'+s.mat+'</td><td>'+s.iso3+'</td>'+
      '<td class="n">'+(s.foot_km2!=null?s.foot_km2.toLocaleString():'<span class="muted">—</span>')+'</td>';
    fb.appendChild(tr);});
  window.addEventListener('resize',()=>{try{map.updateSize();}catch(e){}});
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'satellite.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('\nwrote satellite.html')
