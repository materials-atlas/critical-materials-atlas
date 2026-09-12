"""Bilateral leverage map -- "how exposed is whoever's reading". The global pages say China holds the
chokepoint; this makes it personal: for each IMPORTING country, material by material, how much of ITS
supply runs through the dominant supplier, and how single-sourced it is. Two distinct vulnerabilities:

  CAPTURE (systemic)  reliance on the material's DOMINANT GLOBAL supplier -- if that leader restricts
                      exports to everyone, this is your exposure. share of i's imports of m from L_m.
  LOCK-IN (idiosyncratic)  your OWN import-source concentration (HHI) and top-source share -- you can
                      be single-sourced on a supplier that isn't the global leader, and that is your
                      private fragility even when the world at large is fine.

A leverage score per (importer, material) = capture x sqrt(import_hhi): high when you buy a lot from the
global chokepoint AND have few alternatives. Aggregated per importer into a portfolio: how many
materials it is captured on, and which bite hardest.

Reads the committed BACI zip + out/crosswalk.json + names from out/flows_2024.json. Writes out/leverage.json.
Run:  python build_leverage.py [year]
"""
import os, sys, io, json, zipfile
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import baci as _baci  # the one door for BACI (ARCHITECTURE.md phase 2)
import numpy as np, pandas as pd
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')

CW = json.load(open(os.path.join(ROOT, 'out', 'crosswalk.json'), encoding='utf-8'))
NAMES = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf-8'))['names']
cc = pd.read_csv(_baci.country_file(), keep_default_na=False, na_values=[''])  # 'NA' is Namibia, not missing
NUM2ISO = dict(zip(cc.country_code, cc.country_iso2))

REF = {lab: (m.get('refined_hs') or []) for lab, m in CW.items() if m.get('refined_hs')}
ALLCODES = sorted({c for v in REF.values() for c in v})
raw = _baci.year(YEAR, columns=['i', 'j', 'k', 'v'])
raw = raw[raw.k.isin(ALLCODES)].copy()
raw['v'] = pd.to_numeric(raw['v'], errors='coerce').fillna(0.0) * 1000.0   # BACI v is thousands USD -> USD
raw['ei'] = raw.i.map(NUM2ISO); raw['ej'] = raw.j.map(NUM2ISO)
raw = raw.dropna(subset=['ei', 'ej'])

MATNAME = {lab: lab.replace('(NdFeB)', '').replace('(ndfeb)', '').strip().title() for lab in REF}
mats = {}          # per material: leader, leader_share, code
per = {}           # importer -> material -> {...}
imp_tot = {}       # importer -> total critical-material imports (for ranking / thresholding)

for lab, codes in REF.items():
    sub = raw[raw.k.isin(codes)]
    if sub.empty:
        continue
    exp = sub.groupby('ei').v.sum(); S = float(exp.sum())
    if S <= 0:
        continue
    L = exp.idxmax()
    mats[lab] = {'name': MATNAME[lab], 'code': CW[lab].get('title_code'),
                 'leader': L, 'leader_name': NAMES.get(L, L),
                 'leader_share': round(float(exp[L] / S), 3),
                 'shared': 'shared_refined' in CW[lab].get('flags', [])}
    byimp = sub.groupby(['ej', 'ei']).v.sum()
    for imp in sub.ej.unique():
        src = byimp.loc[imp]                       # Series exporter -> value into this importer
        tot = float(src.sum())
        if tot <= 0:
            continue
        sh = (src / tot)
        hhi = float((sh ** 2).sum())
        top_iso = sh.idxmax()
        capture = float(sh.get(L, 0.0))
        cn = float(sh.get('CN', 0.0))
        top3 = [{'iso': k, 'name': NAMES.get(k, k), 'sh': round(float(v), 3)}
                for k, v in sh.sort_values(ascending=False).head(3).items()]
        per.setdefault(imp, {})[lab] = {
            'imp_usd': round(tot, 0), 'capture': round(capture, 3), 'cn': round(cn, 3),
            'hhi': round(hhi, 3), 'top_iso': top_iso, 'top_share': round(float(sh.max()), 3),
            'leader_is_top': bool(top_iso == L), 'sources': top3,
            'score': round(capture * (hhi ** 0.5), 3)}
        imp_tot[imp] = imp_tot.get(imp, 0.0) + tot

# keep importers with a material-diverse, non-trivial book (>= 4 materials and > $20M total)
KEEP = sorted([i for i in per if len(per[i]) >= 4 and imp_tot.get(i, 0) > 20e6],
              key=lambda i: -imp_tot[i])
profiles = {}
for i in KEEP:
    rows = per[i]
    captured = [m for m, r in rows.items() if r['capture'] >= 0.5]                 # >=50% from global leader
    cn_captured = [m for m, r in rows.items() if r['cn'] >= 0.5]
    single = [m for m, r in rows.items() if r['top_share'] >= 0.7]                 # >=70% from one source
    worst = sorted(rows.items(), key=lambda kv: -kv[1]['score'])[:6]
    profiles[i] = {
        'iso': i, 'name': NAMES.get(i, i), 'imp_usd': round(imp_tot[i], 0),
        'n_materials': len(rows),
        'n_captured': len(captured), 'n_cn_captured': len(cn_captured), 'n_single': len(single),
        'mean_capture': round(float(np.mean([r['capture'] for r in rows.values()])), 3),
        'worst': [{'label': m, 'name': mats[m]['name'], **{k: rows[m][k] for k in
                   ('capture', 'cn', 'hhi', 'top_iso', 'top_share', 'leader_is_top', 'sources', 'imp_usd', 'score')}}
                  for m, _ in worst],
        'materials': {m: rows[m] for m in rows}}

payload = {'year': YEAR, 'materials': mats,
           'note': ('Import-based exposure from the bilateral BACI matrix. CAPTURE = share of a country’s '
                    'imports of a material that comes from that material’s dominant global exporter (systemic). '
                    'LOCK-IN = the country’s own import-source concentration / top-source share (idiosyncratic). '
                    'Import shares understate a country that refines for itself (it simply imports less); a low '
                    'exposure can mean self-sufficiency, not resilience. Shared HS codes (Ga/Ge 811292) are a basket.'),
           'importers': profiles}
json.dump(payload, open(os.path.join(ROOT, 'out', 'leverage.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)

# ---------------------------------------------------------------------------
# Self-contained heatmap page (top-40 importers inlined; matches site shell + nav.js).
# ---------------------------------------------------------------------------
TOP = KEEP[:40]
page_data = {'year': YEAR, 'materials': mats,
             'importers': {i: profiles[i] for i in TOP},
             'order': TOP,
             'summary': {'n_imp': len(profiles),
                         'most_captured': max(TOP, key=lambda i: profiles[i]['n_cn_captured']),
                         'n_heavy_cn': sum(1 for i in TOP if profiles[i]['n_cn_captured'] >= 6)}}
PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Leverage map — Critical Materials Atlas</title>
<meta name="description" content="How exposed is your country: an importer-by-material heatmap of who depends on the chokepoint leader (capture) and who is single-sourced (lock-in), from the bilateral trade matrix.">
<meta property="og:title" content="Leverage map — how exposed is your country">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .sumstrip{display:flex;flex-wrap:wrap;gap:10px 14px;margin:1.1rem 0 .3rem}
 .sumstrip .s{border:1px solid var(--line);border-radius:10px;padding:9px 13px;background:var(--bg-soft);font-size:.78rem;color:var(--mut)}
 .sumstrip .s b{display:block;font-size:1.3rem;color:var(--navy);font-weight:800;font-variant-numeric:tabular-nums;line-height:1.1}
 .ctrls{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;margin:1rem 0 .3rem;font-size:.82rem;color:var(--ink-soft)}
 .seg{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
 .seg button{font:inherit;font-size:.78rem;font-weight:600;padding:5px 12px;background:var(--bg);color:var(--ink-soft);border:0;cursor:pointer}
 .seg button.on{background:var(--navy);color:#fff}
 .legend{display:flex;align-items:center;gap:7px;font-size:.72rem;color:var(--mut)}
 .legend .ramp{width:120px;height:11px;border-radius:3px;background:linear-gradient(90deg,#fde7e4,#e8907f,#b4291f)}
 .hmwrap{overflow-x:auto;margin:.4rem 0 1rem;border:1px solid var(--line);border-radius:12px}
 table.hm{border-collapse:separate;border-spacing:2px;padding:8px}
 table.hm th.col{font-size:.6rem;font-weight:600;color:var(--mut);height:88px;white-space:nowrap;vertical-align:bottom;padding:0 0 4px}
 table.hm th.col span{display:inline-block;transform:rotate(-60deg);transform-origin:left bottom;width:16px}
 table.hm th.row{font-size:.74rem;font-weight:600;text-align:right;padding:0 8px 0 6px;white-space:nowrap;cursor:pointer;color:var(--ink)}
 table.hm th.row:hover{color:var(--navy);text-decoration:underline}
 table.hm th.row.sel{color:var(--navy);font-weight:800}
 table.hm td.cell{width:17px;height:17px;border-radius:3px;cursor:pointer;position:relative}
 table.hm td.cell.na{background:var(--bg-soft);opacity:.5}
 table.hm td.cell.hot{outline:2px solid var(--navy)}
 .tip{position:fixed;pointer-events:none;background:#15323a;color:#fff;font-size:.72rem;padding:6px 9px;border-radius:7px;max-width:230px;z-index:80;opacity:0;transition:opacity .1s;line-height:1.35}
 .detail{border:1px solid var(--line);border-radius:12px;padding:15px 18px;background:var(--bg);margin:1rem 0}
 .detail h3{margin:0 0 3px;font-size:1.1rem}.detail .sub{font-size:.78rem;color:var(--mut);margin:0 0 12px}
 .drow{display:grid;grid-template-columns:130px 1fr 150px;gap:12px;align-items:center;font-size:.8rem;padding:6px 0;border-top:1px solid var(--bg-soft)}
 .drow .dm{font-weight:600;color:var(--ink)}.drow .dm small{display:block;font-weight:500;color:var(--faint);font-size:.68rem}
 .drow .track{height:14px;background:var(--bg-soft);border-radius:4px;overflow:hidden;position:relative}
 .drow .fill{display:block;height:100%;border-radius:4px}
 .drow .src{font-size:.72rem;color:var(--mut);text-align:right}
 .badge{font-size:.6rem;font-weight:700;padding:1px 6px;border-radius:20px;color:#fff;margin-left:5px}
 .b-cap{background:#b4291f}.b-single{background:#a5641a}
 @media(max-width:640px){.drow{grid-template-columns:1fr;gap:2px}}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · importer-side exposure</div>
  <h1>Leverage map</h1>
  <p class="deck">The global pages say who holds each chokepoint. This makes it <b>personal</b>: for every importing country, material by material, how much of <i>its</i> supply runs through the dominant producer — and how <b>single-sourced</b> it is. Two different vulnerabilities: <b>capture</b> (systemic — you buy from the world&rsquo;s chokepoint leader, so an export ban hits you) and <b>lock-in</b> (idiosyncratic — you depend on <i>one</i> supplier, even if it isn&rsquo;t the global giant). Click any country to see its worst exposures and who holds the leverage.</p>
</div></section>
<article style="max-width:1180px">
  <div class="callout"><b>How to read it.</b> Rows are importing countries (most China-captured at the top), columns are materials (most globally-concentrated at the left). A cell&rsquo;s darkness is how much of that country&rsquo;s imports of that material comes from the chokepoint leader — toggle between the <b>material&rsquo;s global leader</b> and <b>China specifically</b>. A pale cell is diversified supply; a dark cell is a country that has handed one supplier its whole book for that material.
  <details class="howto"><summary>Method &amp; caveats</summary>
  <p><b>Capture</b> = share of country i&rsquo;s imports of material m that comes from m&rsquo;s dominant global exporter. <b>China</b> mode shows the share from China specifically. <b>Lock-in</b> = the country&rsquo;s own import-source HHI and top-source share (≥70% from one source flags a single-source dependency). The per-country <b>score</b> = capture × √(import HHI): high when you buy heavily from the global chokepoint AND have few alternatives.</p>
  <p class="howto-src"><b>Caveats.</b> This is <b>import-based</b>: a country that refines for itself simply imports less, so a <i>low</i> exposure can mean self-sufficiency, not resilience (China&rsquo;s own row is small because it feeds itself). It captures refined-goods dependence via trade, not stockpiles, long-term contracts, or domestic mines. <b>Shared HS codes</b> (gallium/germanium 811292) are a basket. Top 40 importers by critical-material import value are shown; the open dataset covers all. Built by <code>build_leverage.py</code> on CEPII BACI. <b>See also</b> <a href="breakout.html">Break the chokepoint</a> and the <a href="ot.html">reallocation stress test</a>.</p>
  </details></div>
  <div class="sumstrip" id="sum"></div>
  <div class="ctrls">
    <span>Colour by:</span>
    <span class="seg"><button id="m-cap" class="on">Global leader (capture)</button><button id="m-cn">China only</button></span>
    <span class="legend">low <span class="ramp"></span> high — reliance on one supplier</span>
  </div>
  <div class="hmwrap"><table class="hm" id="hm"></table></div>
  <div class="detail" id="detail"></div>
</article>
<div class="tip" id="tip"></div>
<script>
const D = __DATA__;
function flag(iso){ if(!iso||iso.length!==2) return ''; return iso.toUpperCase().replace(/./g,c=>String.fromCodePoint(0x1F1E6-65+c.charCodeAt(0)))+' '; }
const M = D.materials, IMP = D.importers;
let MODE = 'capture';   // 'capture' | 'cn'
// columns: materials sorted by global leader share desc
const COLS = Object.keys(M).sort((a,b)=>M[b].leader_share-M[a].leader_share);
// rows: importers sorted by n_cn_captured desc then mean_capture
let ROWS = D.order.slice().sort((a,b)=>IMP[b].n_cn_captured-IMP[a].n_cn_captured || IMP[b].mean_capture-IMP[a].mean_capture);
function ramp(v){ if(v==null) return null;
  const stops=[[253,231,228],[232,144,127],[180,41,31]]; const t=Math.max(0,Math.min(1,v));
  const seg=t<.5?[stops[0],stops[1],t/.5]:[stops[1],stops[2],(t-.5)/.5];
  const c=seg[0].map((x,i)=>Math.round(x+(seg[1][i]-x)*seg[2])); return `rgb(${c[0]},${c[1]},${c[2]})`; }
const S=D.summary, sum=document.getElementById('sum');
sum.innerHTML=`<div class="s"><b>${IMP[S.most_captured].name}</b>most China-captured<br>${IMP[S.most_captured].n_cn_captured} materials &ge;50% from China</div>`+
  `<div class="s"><b>${S.n_heavy_cn}</b>of the top 40 importers are<br>China-captured on &ge;6 materials</div>`+
  `<div class="s"><b>${COLS.length}</b>materials &times; ${ROWS.length} importers<br>in the matrix</div>`;
const tip=document.getElementById('tip');
function showTip(e,html){ tip.innerHTML=html; tip.style.opacity=1; tip.style.left=Math.min(e.clientX+14,innerWidth-244)+'px'; tip.style.top=(e.clientY+14)+'px'; }
function hideTip(){ tip.style.opacity=0; }
let SEL=ROWS[0];
function build(){
  const t=document.getElementById('hm');
  let h='<thead><tr><th></th>'+COLS.map(c=>`<th class="col"><span title="${M[c].name}">${M[c].name}</span></th>`).join('')+'</tr></thead><tbody>';
  for(const i of ROWS){
    const p=IMP[i];
    h+=`<tr><th class="row${i===SEL?' sel':''}" data-i="${i}">${flag(i)}${p.name}</th>`;
    for(const c of COLS){
      const r=p.materials[c];
      if(!r){ h+='<td class="cell na"></td>'; continue; }
      const v=MODE==='cn'?r.cn:r.capture;
      h+=`<td class="cell" data-i="${i}" data-c="${c}" style="background:${ramp(v)}"></td>`;
    }
    h+='</tr>';
  }
  document.getElementById('hm').innerHTML=h+'</tbody>';
  // wire
  t.querySelectorAll('th.row').forEach(el=>el.onclick=()=>{ SEL=el.dataset.i; build(); detail(); });
  t.querySelectorAll('td.cell[data-i]').forEach(el=>{
    el.onmousemove=e=>{ const p=IMP[el.dataset.i], r=p.materials[el.dataset.c], m=M[el.dataset.c];
      showTip(e,`<b>${p.name} — ${m.name}</b><br>${(r.capture*100).toFixed(0)}% from ${flag(m.leader)}${m.leader_name} (leader)<br>${(r.cn*100).toFixed(0)}% from China · top source ${flag(r.top_iso)}${(r.top_share*100).toFixed(0)}%`); };
    el.onmouseleave=hideTip;
    el.onclick=()=>{ SEL=el.dataset.i; build(); detail(); };
  });
}
function detail(){
  const p=IMP[SEL], d=document.getElementById('detail');
  const worst=p.worst;
  d.innerHTML=`<h3>${flag(SEL)}${p.name}</h3><p class="sub">$${(p.imp_usd/1e9).toFixed(1)}bn of critical-material imports · captured (&ge;50% from the global leader) on <b>${p.n_captured}</b> of ${p.n_materials} · single-sourced on <b>${p.n_single}</b> · China holds &ge;50% on <b>${p.n_cn_captured}</b>. Its hardest exposures:</p>`+
    worst.map(w=>{
      const capBadge=w.capture>=.5?`<span class="badge b-cap">captured</span>`:'';
      const singleBadge=w.top_share>=.7?`<span class="badge b-single">single-source</span>`:'';
      const src=w.sources.map(s=>`${flag(s.iso)}${(s.sh*100).toFixed(0)}%`).join(' · ');
      return `<div class="drow"><div class="dm">${w.name}${capBadge}${singleBadge}<small>$${(w.imp_usd/1e6).toFixed(0)}M imported</small></div>`+
        `<div class="track"><span class="fill" style="width:${Math.max(3,w.capture*100)}%;background:${ramp(w.capture)}"></span></div>`+
        `<div class="src">${(w.capture*100).toFixed(0)}% from ${flag(M[w.label].leader)}${M[w.label].leader_name}<br><span style="color:var(--faint)">sources: ${src}</span></div></div>`;
    }).join('');
}
document.getElementById('m-cap').onclick=()=>{ MODE='capture'; document.getElementById('m-cap').classList.add('on'); document.getElementById('m-cn').classList.remove('on'); build(); };
document.getElementById('m-cn').onclick=()=>{ MODE='cn'; document.getElementById('m-cn').classList.add('on'); document.getElementById('m-cap').classList.remove('on'); build(); };
build(); detail();
</script>
</body></html>'''
PAGE = PAGE.replace('__DATA__', json.dumps(page_data, ensure_ascii=False))
open(os.path.join(ROOT, 'leverage.html'), 'w', encoding='utf-8').write(PAGE)

print(f'=== leverage {YEAR}: {len(profiles)} importers x {len(mats)} materials ===')
print(f"{'importer':22}{'$bn':>7}{'#mat':>6}{'capd':>6}{'CN-capd':>8}{'single':>7}{'meanCap':>8}")
for i in KEEP[:18]:
    p = profiles[i]
    print(f"{p['name'][:21]:22}{p['imp_usd']/1e9:7.1f}{p['n_materials']:6}{p['n_captured']:6}"
          f"{p['n_cn_captured']:8}{p['n_single']:7}{p['mean_capture']:8.2f}")
print('\nWROTE out/leverage.json')
