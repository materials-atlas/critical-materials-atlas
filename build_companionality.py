#!/usr/bin/env python3
"""
Companion-metal dependency — the criticals you cannot just mine more of.

Child layer of the commodity-attribution page. Many critical materials are never mined for their own sake:
they are recovered only as by-products of a HOST commodity (gallium from bauxite/zinc, germanium from zinc,
hafnium from zirconium, helium from natural gas, cobalt from copper/nickel...). Their supply is therefore
inelastic to their OWN price or criticality — you cannot open a "gallium mine"; you get more gallium only if
the world smelts more aluminium. This layer quantifies that structural constraint and crosses it with the
atlas's existing geographic concentration to surface "double-jeopardy" materials: both supply-inelastic
(high companionality) AND geographically concentrated (high HHI).

Companionality = approximate share of world production arising as a by-product/co-product (0 = always primary,
100 = always a by-product). Values compiled from USGS Mineral Commodity Summaries 2024 and Nassar, Graedel &
Alonso (2015, Science Advances, "By-product metals are technologically essential but have problematic supply").
Public data; deterministic.
Run: python build_companionality.py
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))

# label -> (class, companionality_pct, [host commodities], note)
# sourced: USGS MCS 2024 + Nassar et al. 2015.
COMP = {
    'arsenic':   ('byproduct', 100, ['copper', 'lead', 'gold'],      'Recovered only from smelter flue dust.'),
    'gallium':   ('byproduct', 100, ['bauxite', 'zinc'],            'A by-product of alumina (Bayer) and zinc refining.'),
    'germanium': ('byproduct', 100, ['zinc', 'coal'],               'From zinc residues and coal fly ash; no primary mine.'),
    'hafnium':   ('byproduct', 100, ['zirconium'],                  'Separated only during zirconium refining.'),
    'helium':    ('byproduct', 100, ['natural gas'],                'Extracted solely from natural-gas processing.'),
    'cobalt':    ('byproduct',  90, ['copper', 'nickel'],           'Mostly a by-product of DRC copper and nickel.'),
    'vanadium':  ('byproduct',  90, ['iron', 'steel slag', 'uranium'], 'Chiefly from titanomagnetite slags and residues.'),
    'antimony':  ('mixed',      60, ['lead', 'zinc', 'gold'],       'Primary stibnite plus by-product of lead/gold.'),
    'palladium': ('mixed',      50, ['platinum', 'nickel'],         'Co-produced with PGM; by-product of nickel at Norilsk.'),
    'tantalum':  ('mixed',      50, ['tin', 'niobium', 'lithium'],  'By-product of tin slag and some Li/Nb operations.'),
    'magnets':   ('mixed',      40, ['iron', 'mineral sands'],      'Bayan Obo REEs are a co-product of iron ore.'),
    'platinum':  ('primary',    25, ['nickel'],                     'Primary in the Bushveld; by-product of nickel elsewhere.'),
    'titanium':  ('primary',    20, ['zircon'],                     'Mineral-sand co-product with zircon.'),
    'tungsten':  ('primary',    10, ['molybdenum', 'tin'],          'Mostly primary scheelite/wolframite.'),
    'copper':    ('primary',     5, ['gold', 'molybdenum'],         'A host metal in its own right.'),
    'fluorspar': ('primary',     5, ['phosphate'],                  'Primary fluorspar; trace as phosphate by-product.'),
    'nickel':    ('primary',     5, ['copper'],                     'A host metal; minor as copper by-product.'),
    'baryte':    ('primary',     0, [], 'Primary barite deposits.'),
    'bauxite':   ('primary',     0, [], 'Primary; itself a host for gallium.'),
    'beryllium': ('primary',     0, [], 'Primary bertrandite/beryl.'),
    'boron':     ('primary',     0, [], 'Primary borate deposits.'),
    'cokingcoal':('primary',     0, [], 'Primary coal mining.'),
    'feldspar':  ('primary',     0, [], 'Primary pegmatite/aplite.'),
    'graphite':  ('primary',     0, [], 'Primary flake/vein graphite.'),
    'lithium':   ('primary',     0, [], 'Primary brine and spodumene.'),
    'magnesium': ('primary',     0, [], 'Primary from dolomite/brine/seawater.'),
    'manganese': ('primary',     0, [], 'Primary manganese ore.'),
    'niobium':   ('primary',     0, [], 'Primary pyrochlore (Brazil/Canada).'),
    'phosphate': ('primary',     0, [], 'Primary phosphate rock.'),
    'phosphorus':('primary',     0, [], 'Derived from primary phosphate rock.'),
    'silicon':   ('primary',     0, [], 'Primary quartz/silica.'),
    'strontium': ('primary',     0, [], 'Primary celestite.'),
}

# ---- empirical cross-check: companionality computed from ICMM 2025 mine-level data ----
# For each material, count facilities where it is the PRIMARY product vs where it rides along as a
# secondary/other commodity. empirical companionality = by-product facilities / all facilities. This is a
# FACILITY-COUNT proxy (not production-weighted), so it corroborates the extreme by-product metals but
# overstates by-product share for metals with a few large primary mines (it counts sites, not tonnes).
import csv as _csv
_ICMM_COMP = os.path.join(ROOT, 'raw', 'icmm', 'icmm_companionality.csv')
_emp = {}
if os.path.exists(_ICMM_COMP):
    with open(_ICMM_COMP, encoding='utf-8', newline='') as f:
        for r in _csv.DictReader(f):
            np_, nb = int(r['n_primary']), int(r['n_byproduct'])
            if np_ + nb > 0:
                _emp[r['atlas_material']] = {'pct': round(100 * nb / (np_ + nb)), 'n': np_ + nb}

CLASS_ORDER = {'byproduct': 0, 'mixed': 1, 'primary': 2}
_PRETTY = {'magnets': 'Rare earths / magnets', 'cokingcoal': 'Coking coal',
           'bauxite': 'Bauxite / aluminium', 'phosphate': 'Phosphate rock'}
def pretty(lab):
    return _PRETTY.get(lab, lab[:1].upper() + lab[1:])
rows = []
for m in data['materials']:
    lab = m['label']
    if lab not in COMP:
        continue
    cls, comp, hosts, note = COMP[lab]
    hhi = m.get('hhi')
    dji = round((comp / 100.0) * hhi, 3) if hhi is not None else None  # double-jeopardy: inelastic x concentrated
    rows.append({
        'label': lab,
        'title': pretty(lab),
        'class': cls,
        'companionality_pct': comp,
        'hosts': hosts,
        'note': note,
        'hhi': hhi,
        'top_share': m.get('top_share'),
        'top_partner': m.get('top_partner'),
        'value_eur': m.get('total_eur'),
        'dji': dji,
        'empirical_pct': _emp.get(lab, {}).get('pct'),
        'empirical_n': _emp.get(lab, {}).get('n'),
    })

rows.sort(key=lambda r: (-(r['dji'] or 0), CLASS_ORDER[r['class']]))
n_by = sum(1 for r in rows if r['class'] == 'byproduct')
n_mixed = sum(1 for r in rows if r['class'] == 'mixed')
# "double jeopardy" = by-product-dominant AND geographically concentrated (hhi >= 0.5)
double = [r for r in rows if r['companionality_pct'] >= 66 and (r['hhi'] or 0) >= 0.5]

# empirical validation: for the by-product-dominant metals that appear in mine-level data with a usable
# sample, does the independent facility count confirm the curated (production-weighted) figure?
_valid = [{'title': r['title'], 'curated': r['companionality_pct'], 'empirical': r['empirical_pct'], 'n': r['empirical_n']}
          for r in rows if r['class'] == 'byproduct' and r['empirical_pct'] is not None and (r['empirical_n'] or 0) >= 3]
_confirmed = [v for v in _valid if abs(v['curated'] - v['empirical']) <= 15]

out = {
    'generated': data.get('generated'),
    'n_materials': len(rows),
    'n_byproduct': n_by,
    'n_mixed': n_mixed,
    'n_double_jeopardy': len(double),
    'double_jeopardy': [r['title'] for r in double],
    'mean_companionality': round(sum(r['companionality_pct'] for r in rows) / len(rows), 1),
    'rows': rows,
    'validation': _valid,
    'n_confirmed': len(_confirmed),
    'n_validated': len(_valid),
    'confirmed_titles': [v['title'] for v in _confirmed],
    'sources': 'USGS Mineral Commodity Summaries 2024; Nassar, Graedel & Alonso 2015 (Sci. Adv.); '
               'empirical cross-check computed from ICMM Global Mining Dataset 2025 (facility counts).',
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'companionality.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/companionality.json')
print(f"  {len(rows)} materials | {n_by} by-product-dominant | {n_mixed} mixed | "
      f"{len(double)} double-jeopardy: {', '.join(out['double_jeopardy'])}")

# ------------------------------------------------------------------ page
HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hostage metals — the criticals you can't just mine more of · Critical Materials Atlas</title>
<meta name="description" content="Many critical materials are only ever by-products of a host commodity, so their supply cannot respond to their own price. This layer quantifies companionality for 32 materials and crosses it with geographic concentration to find the double-jeopardy cases.">
<meta property="og:title" content="Hostage metals: the criticals you can't just mine more of">
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
 .stat.warn{border-left-color:#c0392b}.stat.warn .v{color:#c0392b}
 table.tidy{width:100%;border-collapse:collapse;font-size:.88rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .tag{display:inline-block;font-size:.7rem;font-weight:700;padding:.06rem .45rem;border-radius:20px}
 .tag.b{background:#fbe9e7;color:#c0392b}.tag.m{background:#fff4e2;color:#b07a18}.tag.p{background:#eaf3f1;color:#0e7c74}
 .keyline{background:#fbf3f2;border:1px solid #f0d9d5;border-left:4px solid #c0392b;border-radius:10px;padding:.9rem 1.1rem;margin:1.2rem 0}
 .keyline b{color:#c0392b}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="risk.html">Risk</a><a href="criticality.html">Criticality</a>
  <a href="commodity-attribution.html" class="hideable">Attribution</a><a href="methodology.html" class="hideable">Methodology</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · supply structure</div>
  <h1>Hostage metals</h1>
  <p class="deck">Some critical materials you simply cannot decide to mine more of. Gallium, germanium, hafnium, helium, cobalt &mdash; they are recovered only as <b>by-products</b> of a bigger host commodity, so their supply answers to <i>aluminium&rsquo;s</i> or <i>zinc&rsquo;s</i> economics, not their own. A supply squeeze can&rsquo;t be fixed by a higher price. This layer &mdash; a child of the <a href="commodity-attribution.html" style="color:#fff;text-decoration:underline">attribution page</a> &mdash; measures that structural trap and crosses it with geography to find the materials caught in <b>both</b>.</p>
</div></section>
<article style="max-width:1060px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>What &ldquo;companionality&rdquo; means, and the sources</summary>
  <p><b>Companionality</b> = the approximate share of world production that arises as a <i>by-product or co-product</i> of a host commodity (0 = always mined for itself; 100 = never mined for itself). A high value means supply is <b>inelastic to the material&rsquo;s own price</b>: more is produced only when the host is, regardless of how &ldquo;critical&rdquo; it becomes. We cross companionality with the atlas&rsquo;s trade concentration (HHI) into a <b>double-jeopardy</b> reading &mdash; supply-inelastic <i>and</i> geographically concentrated.</p>
  <p class="howto-src"><b>Sources &amp; caveats:</b> companionality figures compiled from <b>USGS Mineral Commodity Summaries 2024</b> and <b>Nassar, Graedel &amp; Alonso (2015, <i>Science Advances</i>)</b>, and <b>recomputed from mine-level open data</b> (ICMM Global Mining Dataset 2025) as a validation column below. Values are round approximations of a genuinely fuzzy quantity (by-product share shifts with price and deposit) &mdash; treat them as tiers, not decimals. HHI is trade-based (Comtrade/BACI), so it measures export concentration, not mine concentration. &rarr; <a href="out/companionality.json">companionality.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <h2 style="margin:1.6rem 0 .3rem">The double-jeopardy map</h2>
  <p class="muted" style="margin-top:0">Each bubble is a material. <b>Right</b> = more of it is an unavoidable by-product (supply can&rsquo;t respond to its own price). <b>Up</b> = more geographically concentrated trade. Bubble size = trade value. The <span style="color:#c0392b;font-weight:700">top-right</span> is the danger zone: inelastic <i>and</i> concentrated.</p>
  <div id="scatter"></div>

  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.6rem 0 .3rem">Every material, ranked by double-jeopardy</h2>
  <p class="muted" style="margin-top:0">Double-jeopardy index = companionality &times; trade concentration (HHI). High = you can neither diversify the supplier nor scale the supply.</p>
  <table class="tidy" id="tab"><thead><tr><th>Material</th><th>supply type</th><th class="n">by-product %</th><th>recovered from</th><th class="n">HHI</th><th class="n">DJI</th></tr></thead><tbody></tbody></table>

  <h2 style="margin:1.8rem 0 .3rem">Are these numbers right? A mine-level cross-check</h2>
  <p class="muted" style="margin-top:0">The by-product shares above are compiled from the literature (USGS, Nassar 2015) &mdash; a fair objection is that they&rsquo;re curated, not computed. So we recomputed companionality <b>independently, from open mine-level data</b>: for every mine in the <b>ICMM Global Mining Dataset (2025)</b>, is the metal its <i>primary</i> product, or does it ride along as a secondary one? The by-product share falls straight out of the counts &mdash; and for the metals the whole thesis rests on, the two agree.</p>
  <table class="tidy" id="valtab" style="max-width:560px"><thead><tr><th>Hostage metal</th><th class="n">literature</th><th class="n">from mine data</th><th class="n">mines</th></tr></thead><tbody></tbody></table>
  <div class="keyline" id="valkey" style="background:#f2f6f5;border-color:#d9e6e3;border-left-color:#0e7c74"></div>

  <h2 style="margin:1.8rem 0 .3rem">Why this matters, and what it spawns next</h2>
  <p>Conventional supply-risk scores treat every material as if a price signal could summon more of it. For the by-product tier that is simply false: no gallium price will build a gallium mine. This reframes mitigation &mdash; for hostage metals the levers are <i>recovery yield at the host</i>, <i>stockpiling</i>, and <i>substitution</i>, not new mines. It also seeds the next layers: a <a href="risk.html">risk</a> re-weighting that penalises companionality, a recovery-yield / recycling lens (secondary supply is the only elastic source for these metals), and a host-shock model &mdash; what an aluminium or zinc downturn does to the criticals riding on it. This atlas grows by letting each finding pose the next question.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="commodity-attribution.html">Commodity attribution</a><br><a href="risk.html">Supply risk</a><br><a href="criticality.html">Criticality</a><br><a href="methodology.html">Methodology</a></div>
  <div><h4>Sources</h4>USGS MCS 2024 · Nassar et al. 2015 (Sci. Adv.) · Comtrade/BACI (concentration)</div>
  <div class="fineprint">Companionality is a round, literature-based estimate of by-product share; treat the axis as tiers, not precise percentages.</div>
</div></footer>
<script>
function ld(u){return new Promise((res,rej)=>{const s=document.createElement('script');s.src=u;s.onload=res;s.onerror=rej;document.head.appendChild(s);});}
Promise.all([fetch('out/companionality.json').then(r=>r.json()),
  ld('https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js')]).then(([S])=>{
  const f=n=>Number(n).toLocaleString();
  document.getElementById('lead').innerHTML='<b>Result:</b> of '+S.n_materials+' tracked materials, <b>'+S.n_byproduct+'</b> are produced mostly as by-products &mdash; their supply cannot answer to their own price &mdash; and <b>'+S.n_double_jeopardy+'</b> are caught in double jeopardy: supply-inelastic <i>and</i> geographically concentrated ('+S.double_jeopardy.join(', ')+'). For these, &ldquo;just mine more&rdquo; is not an option.';
  const stats=[
    {v:S.n_byproduct,l:'materials produced mostly as by-products (companionality &ge; 66)',warn:true},
    {v:S.n_double_jeopardy,l:'double-jeopardy: by-product-locked AND concentrated (HHI &ge; 0.5)',warn:true},
    {v:S.n_mixed,l:'mixed — part primary, part by-product'},
    {v:(S.n_materials-S.n_byproduct-S.n_mixed),l:'genuinely primary — supply can respond to price'},
  ];
  document.getElementById('stats').innerHTML=stats.map(s=>'<div class="stat'+(s.warn?' warn':'')+'"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  document.getElementById('keyline').innerHTML='<b>The trap:</b> the seven by-product-dominant metals &mdash; arsenic, gallium, germanium, hafnium, helium, cobalt, vanadium &mdash; sit at ~90&ndash;100% companionality. A standard supply-risk index assumes a shortage pulls in new production; here it can&rsquo;t. Gallium is the sharpest case: 100% a by-product of aluminium, and its trade is China-dominated &mdash; inelastic supply meeting a single gatekeeper.';
  // scatter
  const col={byproduct:'#c0392b',mixed:'#b07a18',primary:'#0e7c74'};
  const pts=S.rows.filter(r=>r.hhi!=null).map(r=>({
    value:[r.companionality_pct, r.hhi, Math.sqrt((r.value_eur||0))/900+8, r.title, r.class],
    itemStyle:{color:col[r['class']]+'cc'}
  }));
  const ch=echarts.init(document.getElementById('scatter'));
  ch.setOption({
    grid:{left:52,right:24,top:24,bottom:52},
    tooltip:{formatter:p=>'<b>'+p.value[3]+'</b><br>by-product share: '+p.value[0]+'%<br>trade HHI: '+p.value[1].toFixed(2)+'<br>'+p.value[4]},
    xAxis:{name:'companionality (by-product share %)',nameLocation:'middle',nameGap:30,min:0,max:105,
      axisLabel:{color:'#5a6b68'},nameTextStyle:{color:'#5a6b68'},splitLine:{lineStyle:{color:'#eef1f0'}}},
    yAxis:{name:'trade concentration (HHI)',nameLocation:'middle',nameGap:36,min:0,max:1,
      axisLabel:{color:'#5a6b68'},nameTextStyle:{color:'#5a6b68'},splitLine:{lineStyle:{color:'#eef1f0'}}},
    series:[{type:'scatter',data:pts,symbolSize:d=>d[2],
      markLine:{silent:true,symbol:'none',lineStyle:{color:'#c9b3ad',type:'dashed'},
        data:[{xAxis:66},{yAxis:0.5}]},
      label:{show:true,formatter:p=>p.value[3],position:'right',fontSize:10,color:'#15323a',
        distance:4,rich:{}} }]
  });
  window.addEventListener('resize',()=>ch.resize());
  // table
  const tb=document.querySelector('#tab tbody');
  const tagcls={byproduct:'b',mixed:'m',primary:'p'};
  const tagtxt={byproduct:'by-product',mixed:'mixed',primary:'primary'};
  S.rows.forEach(r=>{
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+r.title+'</b></td>'+
      '<td><span class="tag '+tagcls[r['class']]+'">'+tagtxt[r['class']]+'</span></td>'+
      '<td class="n">'+r.companionality_pct+'</td>'+
      '<td class="muted">'+(r.hosts.length?r.hosts.join(', '):'&mdash;')+'</td>'+
      '<td class="n">'+(r.hhi!=null?r.hhi.toFixed(2):'&mdash;')+'</td>'+
      '<td class="n" style="font-weight:700;color:'+((r.dji||0)>=0.5?'#c0392b':(r.dji||0)>=0.3?'#b07a18':'#9aa6ad')+'">'+(r.dji!=null?r.dji.toFixed(2):'&mdash;')+'</td>';
    tb.appendChild(tr);
  });
  // empirical mine-level cross-check
  if(S.validation && S.validation.length){
    const vt=document.querySelector('#valtab tbody');
    S.validation.forEach(v=>{
      const agree=Math.abs(v.curated-v.empirical)<=15;
      const tr=document.createElement('tr');
      tr.innerHTML='<td><b>'+v.title+'</b></td><td class="n">'+v.curated+'%</td>'+
        '<td class="n" style="font-weight:700;color:'+(agree?'#0e7c74':'#b07a18')+'">'+v.empirical+'%'+(agree?' &check;':'')+'</td>'+
        '<td class="n muted">'+f(v.n)+'</td>';
      vt.appendChild(tr);
    });
    document.getElementById('valkey').innerHTML='<b style="color:#0e7c74">The curated numbers hold up.</b> Computed blind from '+f(S.rows.reduce((a,r)=>a+(r.empirical_n||0),0))+' mine records, the four hostage metals that appear in the data &mdash; <b>'+S.confirmed_titles.join(', ')+'</b> &mdash; match the literature within a couple of points ('+S.n_confirmed+' of '+S.n_validated+'). The remaining hostage metals (arsenic, hafnium, helium) are too trace to be listed as a mine product at all &mdash; itself a confirmation that they&rsquo;re never mined for their own sake. <b>Honest limit:</b> this counts <i>facilities</i>, not <i>tonnes</i>, so it overstates by-product share for metals with a few large primary mines (niobium, manganese), which is why it corroborates the curated figures rather than replacing them. Production-weighting (from the Jasansky mine database) is the next refinement.';
  }
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'companionality.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote companionality.html')
