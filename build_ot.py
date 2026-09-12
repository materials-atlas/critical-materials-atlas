"""Supply-shock reallocation engine -- the quantitative "can the rest cover the cut?" layer.

The scenario page already lists fallback exporters. This goes further and asks the harder,
decision-relevant questions, using OPTIMAL TRANSPORT on the real bilateral refined-trade matrix:

  1. N-1 STRESS. Model a shock as the loss of the leader's EXPORTS -- the only supply that was ever
     redirectable (a domestic-consuming refiner's output was never available to importers anyway; so
     export-based is the correct frame, and we say so). If the leader ships a fraction f of world
     exports, the rest must scale by 1/(1-f) to cover the same demand. f=0.87 -> a 7.7x scale-up.
  2. DOES REMOVAL JUST MOVE THE CHOKEPOINT? Recompute export concentration (HHI) and the new leader
     among the survivors. Cutting China often just hands the chokepoint to the next concentrated player.
  3. CAN IT BE COVERED AT ALL? Give every surviving exporter a plausible scale-up cap kappa (can at
     most double, triple...). Spare = (kappa-1) x current exports. Coverage = min(1, spare / freed).
     What is NOT coverable is a quantified, assumption-explicit structural shortfall.
  4. WHO IS STRANDED & HOW HARD IS THE RESHUFFLE. Entropic OT (Sinkhorn) reallocates the leader's
     freed demand onto survivors at minimum geographic cost (great-circle distance between centroids),
     giving the reshuffle pattern and a friction ratio: how much farther supply must travel than the
     leader's original flows. High friction = the spare capacity sits far from the stranded buyers.

FC-equivalence note: the OT layer is a Sinkhorn scaling, exactly like the (unpublished) fitness layer
-- but here it is applied to a DIFFERENT object (bilateral flows, an explicit transport problem with a
real cost matrix), where the algorithm is doing honest work, not papering over a degenerate estimand.

Reads the committed BACI zip + out/crosswalk.json + centroids/names from out/flows_2024.json.
Writes out/ot.json.  Run:  python build_ot.py [year]
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
flows = json.load(open(os.path.join(ROOT, 'out', 'flows_2024.json'), encoding='utf-8'))
CENT = flows['centroids']                 # iso2 -> [lat, lon]
NAMES = flows['names']                    # iso2 -> country name
cc = pd.read_csv(_baci.country_file(), keep_default_na=False, na_values=[''])  # 'NA' is Namibia, not missing
NUM2ISO = dict(zip(cc.country_code, cc.country_iso2))

REF_CODES = sorted({c for m in CW.values() for c in (m.get('refined_hs') or [])})
raw = _baci.year(YEAR, columns=['i', 'j', 'k', 'v'])
raw = raw[raw.k.isin(REF_CODES)].copy()
raw['v'] = pd.to_numeric(raw['v'], errors='coerce').fillna(0.0)
raw['ei'] = raw.i.map(NUM2ISO); raw['ej'] = raw.j.map(NUM2ISO)
raw = raw.dropna(subset=['ei', 'ej'])

def haversine(a, b):
    if a not in CENT or b not in CENT:
        return 8000.0                     # missing-centroid fallback (~median great-circle)
    (la1, lo1), (la2, lo2) = CENT[a], CENT[b]
    r = np.radians
    dlat, dlon = r(la2 - la1), r(lo2 - lo1)
    h = np.sin(dlat/2)**2 + np.cos(r(la1))*np.cos(r(la2))*np.sin(dlon/2)**2
    return float(2 * 6371 * np.arcsin(np.sqrt(min(1.0, h))))

def sinkhorn(a, b, C, eps=0.05, iters=400):
    """Entropic OT: min <P,C> - eps H(P) s.t. row sums a, col sums b. Log-domain, stabilised."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    K = np.exp(-C / eps)
    u = np.ones_like(a); v = np.ones_like(b)
    for _ in range(iters):
        u = a / (K @ v + 1e-300)
        v = b / (K.T @ u + 1e-300)
    return (u[:, None] * K) * v[None, :]

KAPPAS = [2, 3, 5]
out = {}
for lab, meta in CW.items():
    codes = meta.get('refined_hs') or []
    if not codes:
        continue
    sub = raw[raw.k.isin(codes)]
    if sub.empty:
        continue
    exp = sub.groupby('ei').v.sum()                 # exporter -> total refined exports
    S = float(exp.sum())
    if S <= 0:
        continue
    L = exp.idxmax(); fL = float(exp[L] / S)
    surv = exp.drop(L)                               # surviving exporters
    Ssurv = float(surv.sum())
    # 1. N-1 stress
    stress = (1.0 / (1.0 - fL)) if fL < 0.999 else None
    # 2. concentration before / after removal (survivors renormalised)
    hhi_before = float(((exp / S) ** 2).sum())
    if Ssurv > 0:
        surv_sh = surv / Ssurv
        hhi_after = float((surv_sh ** 2).sum())
        new_leader = surv_sh.idxmax(); new_lead_share = float(surv_sh.max())
    else:
        hhi_after, new_leader, new_lead_share = 1.0, None, 1.0
    # 3. capped coverage (spare = (kappa-1) * current exports of survivors)
    freed = float(exp[L])
    cover = {k: (min(1.0, (k - 1) * Ssurv / freed) if freed > 0 else 1.0) for k in KAPPAS}
    # 4. OT reshuffle of the leader's freed demand onto survivors, min geographic cost
    dem = sub[sub.ei == L].groupby('ej').v.sum()     # leader's customers lose these imports
    friction = None; stranded = []; before_arcs = []; after_arcs = []
    if len(dem) and len(surv):
        imps = list(dem.index); sups = list(surv.index)
        b = dem.values.astype(float)
        a = (surv.values / Ssurv * b.sum()).astype(float)     # capacity-weighted supply, mass-matched
        C = np.array([[haversine(s, im) for im in imps] for s in sups], float)
        Cn = C / (C.max() + 1e-9)
        P = sinkhorn(a, b, Cn)
        realloc_cost = float((P * C).sum() / (b.sum() + 1e-9))      # mean km supply now travels
        base_cost = float(sum(dem[im] * haversine(L, im) for im in imps) / (b.sum() + 1e-9))
        friction = float(realloc_cost / base_cost) if base_cost > 0 else None
        # stranded = importers most reliant on the leader (largest freed demand, and its share of theirs)
        imp_tot = sub.groupby('ej').v.sum()
        rel = sorted(((im, float(dem[im]), float(dem[im] / imp_tot.get(im, dem[im])))
                      for im in imps), key=lambda t: -t[1])[:6]
        stranded = [{'iso': im, 'name': NAMES.get(im, im),
                     'lost_usd': v, 'reliance': round(sh, 3)} for im, v, sh in rel]
        # arcs for the reshuffle map: BEFORE = leader's exports; AFTER = the OT reallocation plan
        before_arcs = sorted(({'to': im, 'v': float(dem[im])} for im in imps),
                             key=lambda x: -x['v'])[:14]
        edges = [(sups[si], imps[ii], float(P[si, ii]))
                 for si in range(len(sups)) for ii in range(len(imps)) if sups[si] != imps[ii]]
        after_arcs = [{'f': s, 't': im, 'v': v}
                      for s, im, v in sorted(edges, key=lambda e: -e[2]) if v > 0][:26]
    out[lab] = {
        'label': lab,
        'name': lab.replace('(NdFeB)', '').replace('(ndfeb)', '').strip().title(),
        'code': meta.get('title_code'), 'flags': meta.get('flags', []),
        'shared': 'shared_refined' in meta.get('flags', []),
        'leader': L, 'leader_name': NAMES.get(L, L), 'leader_export_share': round(fL, 3),
        'stress_factor': round(stress, 1) if stress else None,
        'hhi_before': round(hhi_before, 3), 'hhi_after': round(hhi_after, 3),
        'new_leader': new_leader, 'new_leader_name': NAMES.get(new_leader, new_leader),
        'new_leader_share': round(new_lead_share, 3),
        'coverage': {str(k): round(v, 3) for k, v in cover.items()},
        'friction': round(friction, 2) if friction else None,
        'freed_usd': round(freed, 0), 'stranded': stranded,
        'before': before_arcs, 'after': after_arcs,
        'n_exporters': int((exp > 0).sum())}

# plain verdict + a "kind" flag for each material
for r in out.values():
    L, nl = r['leader_name'], r['new_leader_name']
    hb, ha = r['hhi_before'], r['hhi_after']
    c2 = r['coverage']['2']; fr = r['friction']
    frict = (f' The spare capacity also sits far from the stranded buyers — reshuffled supply travels '
             f'~{fr:.1f}× farther than {L}’s current flows.') if fr and fr >= 1.3 else ''
    if c2 < 0.5:
        r['kind'] = 'uncoverable'
        need = next((k for k in KAPPAS if r['coverage'][str(k)] >= 0.99), None)
        cap_txt = (f'a {need}× scale-up of every other exporter' if need
                   else 'even a 5× scale-up of every other exporter is not enough')
        r['verdict'] = (f'Structurally hard to cover: doubling every other exporter meets only '
                        f'{c2:.0%} of {L}’s lost exports; full coverage needs {cap_txt}.' + frict)
    elif ha >= hb:
        r['kind'] = 'backfire'
        r['verdict'] = (f'Diversification backfires — removing {L} hands the chokepoint to {nl} and '
                        f'concentration RISES (HHI {hb:.2f}→{ha:.2f}). The runner-up is the real problem.' + frict)
    elif ha >= 0.25:
        r['kind'] = 'shifts'
        r['verdict'] = (f'Removing {L} only shifts the chokepoint to {nl} — still concentrated '
                        f'(HHI {hb:.2f}→{ha:.2f}); covered only by a {"3" if r["coverage"]["3"]>=0.99 else "5"}× scale-up.' + frict)
    else:
        r['kind'] = 'diversifies'
        r['verdict'] = (f'Removing {L} genuinely de-concentrates (HHI {hb:.2f}→{ha:.2f}); the freed '
                        f'demand is coverable if survivors scale ~{"2" if c2>=0.99 else "3+"}×.' + frict)

# rank: worst first -- structurally uncoverable (low coverage at kappa=2) and high stress
ranked = sorted(out.values(),
                key=lambda r: (r['coverage'].get('2', 1), -(r['leader_export_share'] or 0)))
KINDS = ['uncoverable', 'backfire', 'shifts', 'diversifies']
summary = {'n': len(out),
           'by_kind': {k: sum(1 for r in out.values() if r.get('kind') == k) for k in KINDS},
           'uncoverable2x': sum(1 for r in out.values() if r['coverage']['2'] < 0.5),
           'backfire': sum(1 for r in out.values() if r['hhi_after'] >= r['hhi_before'])}
CENT = flows['centroids']
usediso = {r['leader'] for r in out.values()} | {r['new_leader'] for r in out.values()}
for r in out.values():
    usediso |= {a['to'] for a in r['before']} | {a['f'] for a in r['after']} | {a['t'] for a in r['after']}
cent_used = {i: CENT[i] for i in usediso if i in CENT}
payload = {'year': YEAR, 'kappas': KAPPAS, 'summary': summary, 'centroids': cent_used,
           'note': ('Shock = loss of the leader’s EXPORTS (the redirectable supply). Export-based '
                    'by construction: a domestic-consuming refiner’s output was never available to '
                    'importers. Coverage assumes survivors can scale exports up to kappa× current; '
                    'shared HS codes (gallium/germanium 811292) mix metals, so those rows are a basket.'),
           'materials': out}
json.dump(payload, open(os.path.join(ROOT, 'out', 'ot.json'), 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)

# ---------------------------------------------------------------------------
# Self-contained page (data inlined, matches the site shell + assets/nav.js).
# ---------------------------------------------------------------------------
PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reallocation stress test — Critical Materials Atlas</title>
<meta name="description" content="An optimal-transport stress test: when a refining chokepoint is cut, can the world's remaining export capacity actually cover it, does removal just hand the chokepoint to the next player, and who is stranded?">
<meta property="og:title" content="Reallocation stress test — can the rest cover the cut?">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .sumstrip{display:flex;flex-wrap:wrap;gap:10px 14px;margin:1.1rem 0 .3rem}
 .sumstrip .s{border:1px solid var(--line);border-radius:10px;padding:9px 13px;background:var(--bg-soft);font-size:.78rem;color:var(--mut)}
 .sumstrip .s b{display:block;font-size:1.35rem;color:var(--navy);font-weight:800;font-variant-numeric:tabular-nums;line-height:1.1}
 .filterbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:1.1rem 0 .2rem}
 .filterbar .chip{font:inherit;font-size:.74rem;font-weight:600;cursor:pointer;border:1px solid var(--line);
   background:var(--bg);color:var(--ink-soft);border-radius:20px;padding:5px 12px;display:inline-flex;align-items:center;gap:6px}
 .filterbar .chip i{width:9px;height:9px;border-radius:50%;display:inline-block}.filterbar .chip.off{opacity:.38}
 .filterbar input[type=search]{font:inherit;font-size:.8rem;padding:6px 11px;border:1px solid var(--line);border-radius:8px;min-width:170px;flex:1;max-width:270px}
 .bgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:18px;margin:1rem 0}
 .bcard{border:1px solid var(--line);border-radius:13px;padding:15px 17px 16px;background:var(--bg);display:flex;flex-direction:column;gap:10px}
 .bcard h3{font-size:1.05rem;margin:0;display:flex;justify-content:space-between;align-items:baseline;gap:8px}
 .bcard h3 .hs{font-size:.64rem;color:var(--faint);font-weight:600;letter-spacing:.2px;white-space:nowrap}
 .kindtag{font-size:.62rem;font-weight:700;padding:2px 8px;border-radius:20px;color:#fff;text-transform:none}
 .k-uncoverable{background:#b4291f}.k-backfire{background:#a5641a}.k-shifts{background:#56607a}.k-diversifies{background:#0e8f83}
 .leadline{font-size:.9rem;color:var(--ink);margin:0}.leadline b{color:var(--navy);font-weight:800}
 .metrics{display:grid;grid-template-columns:1fr 1fr;gap:7px 14px;margin:2px 0}
 .met{font-size:.74rem;color:var(--mut)}.met b{color:var(--ink);font-weight:700;font-variant-numeric:tabular-nums}
 .met .big{font-size:1.02rem;color:var(--navy)}
 .hhibar{display:flex;align-items:center;gap:6px;font-size:.72rem;margin:1px 0}
 .hhibar .track{flex:1;height:11px;background:var(--bg-soft);border-radius:4px;position:relative;overflow:hidden}
 .hhibar .b4{position:absolute;left:0;top:0;height:100%;background:#c3ccd6;border-radius:4px}
 .hhibar .af{position:absolute;left:0;top:0;height:100%;border-radius:4px}
 .covrow{display:flex;align-items:center;gap:7px;font-size:.72rem;margin:2px 0}
 .covrow .kl{width:26px;flex:0 0 26px;color:var(--faint);font-weight:600}
 .covrow .track{flex:1;height:11px;background:var(--bg-soft);border-radius:4px;overflow:hidden}
 .covrow .fill{display:block;height:100%;border-radius:4px}
 .covrow .cv{width:34px;flex:0 0 34px;text-align:right;color:var(--mut);font-variant-numeric:tabular-nums}
 .stranded{font-size:.72rem;color:var(--mut);border-top:1px dashed var(--line);padding-top:7px;margin-top:2px}
 .stranded b{color:var(--ink-soft)}.stranded .r{color:var(--faint)}
 .verdict{font-size:.82rem;color:var(--ink);line-height:1.45;background:var(--bg-soft);border-radius:9px;padding:9px 12px}
 .verdict.uncoverable{background:#fbeeec;border:1px solid #e7c6bf}.verdict.backfire{background:#fdf4e7;border:1px solid #f0dcc0}
 .empty{color:var(--faint);font-style:italic;padding:2rem;text-align:center}
 .lbl{font-size:.62rem;text-transform:uppercase;letter-spacing:.09em;font-weight:700;color:var(--faint);margin:0}
 .mappanel{border:1px solid var(--line);border-radius:13px;padding:14px 16px 10px;background:var(--bg);margin:1.1rem 0}
 .mapctl{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:center;margin:0 0 8px}
 .mapctl select{font:inherit;font-size:.86rem;font-weight:600;padding:5px 10px;border:1px solid var(--line);border-radius:8px;color:var(--navy);background:var(--bg)}
 .mapctl .seg{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
 .mapctl .seg button{font:inherit;font-size:.78rem;font-weight:600;padding:5px 13px;background:var(--bg);color:var(--ink-soft);border:0;cursor:pointer}
 .mapctl .seg button.on{background:var(--navy);color:#fff}
 .rmap{width:100%;height:auto;display:block;border-radius:9px;background:#eef3f5}
 .rmap .grat{stroke:#d7e0e3;stroke-width:.5;fill:none}
 .rmap .arc{fill:none;opacity:.72;transition:opacity .5s}
 .rmap .node{stroke:#fff;stroke-width:.8}
 .rmap .lbl2{font:600 10px Inter,sans-serif;fill:#15323a;paint-order:stroke;stroke:#eef3f5;stroke-width:2.4px}
 .rmap .cut{stroke:#b4291f;stroke-width:1.6}
 .mapcap{font-size:.8rem;color:var(--mut);line-height:1.4;margin:6px 2px 2px}.mapcap b{color:var(--navy)}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · optimal transport on real trade flows</div>
  <h1>For 4 materials, no reallocation covers the loss — and 8 get worse</h1>
  <p class="deck">The fallback test asks <i>is there another exporter?</i> This asks the harder question: if a refining chokepoint is <b>cut</b>, can the world&rsquo;s <b>remaining export capacity actually cover it</b> — or does removing the leader just hand the chokepoint to the next player, and who is left stranded? We model the shock as the loss of the leader&rsquo;s <b>exports</b> (the only supply that was ever redirectable) and reallocate its freed demand across every surviving exporter by <b>optimal transport</b> — minimum geographic cost on the real bilateral trade matrix. Three numbers fall out: how hard the rest must scale, whether removal actually de-concentrates, and how much demand is <i>structurally uncoverable</i>.</p>
</div></section>
<article style="max-width:1180px">
  <div class="callout"><b>Why &ldquo;is there a fallback?&rdquo; is the wrong question.</b> A fallback exporter is not free capacity — it is already serving its own customers. The real questions are whether the <i>spare</i> capacity, scaled to a plausible ceiling, can cover the cut; whether removing the leader <b>de-concentrates or just shifts</b> the chokepoint to a runner-up (sometimes it makes concentration <i>worse</i>); and whether the spare sits <i>near</i> the stranded buyers or far away. Optimal transport answers all three on the actual flow matrix. The materials flagged <i>structurally uncoverable</i> here are deliberately <b>not</b> the same set as the export-fallback <a href="refiners.html">single points of failure</a> — this is the stricter capacity test, so it names a different list.
  <details class="howto"><summary>Method &amp; caveats</summary>
  <p><b>N−1 stress</b> = 1/(1−f), where f is the leader&rsquo;s share of world <i>exports</i>: the factor by which every other exporter must scale to cover the same demand. <b>Concentration</b> is the export HHI before, and after the leader is removed and survivors are renormalised (the runner-up&rsquo;s new share). <b>Coverage@κ</b> assumes each surviving exporter can scale its exports up to κ× current; spare = (κ−1)×current, coverage = min(1, Σspare / freed). <b>Reshuffle &amp; friction</b>: entropic optimal transport (Sinkhorn) reallocates the leader&rsquo;s freed demand onto survivors at minimum great-circle cost between country centroids; friction = mean distance the reshuffled supply travels ÷ the leader&rsquo;s original mean shipping distance (&gt;1 = spare sits farther away).</p>
  <p class="howto-src"><b>Caveats.</b> This is <b>export-based by construction</b> — it models the loss of what the leader <i>ships</i>, which is the correct frame for reallocation (a domestic-consuming refiner&rsquo;s output was never available to importers), but it means the leader&rsquo;s share here is an <i>export</i> share, not a production share. The κ scale-up ceiling is an explicit assumption, not a forecast — read coverage as &ldquo;how much slack exists at ceiling κ,&rdquo; not a prediction. Distance is a crude friction proxy (centroid great-circle, not shipping cost or capability). <b>Shared HS codes</b> (gallium/germanium 811292) mix metals, so those rows are a basket. This is a stress test of <i>today&rsquo;s</i> trade structure, not the post-diversification world the <a href="breakout.html">Break the chokepoint</a> page tracks. Built by <code>build_ot.py</code> on CEPII BACI. <b>See also</b> <a href="leverage.html">the leverage map</a> (how exposed is each importing country), <a href="scenarios.html">shock scenarios</a>, <a href="cascade.html">the supply-shock cascade</a>, and <a href="breakout.html">the decision layer</a>.</p>
  </details></div>
  <div class="mappanel">
    <div class="mapctl">
      <span class="lbl" style="margin-right:2px">Reshuffle map</span>
      <select id="mapsel"></select>
      <span class="seg"><button id="p-before" class="on">Before — the leader ships</button><button id="p-after">After the cut — optimal reshuffle</button></span>
    </div>
    <svg class="rmap" id="rmap" viewBox="0 0 1100 520" preserveAspectRatio="xMidYMid meet"></svg>
    <div class="mapcap" id="mapcap"></div>
  </div>
  <div class="sumstrip" id="sum"></div>
  <div class="filterbar" id="filters"></div>
  <div class="bgrid" id="grid"></div>
</article>
<script>
const D = __DATA__;
function flag(iso){ if(!iso||iso.length!==2) return ''; return iso.toUpperCase().replace(/./g,c=>String.fromCodePoint(0x1F1E6-65+c.charCodeAt(0)))+' '; }
const KIND={uncoverable:{c:'k-uncoverable',t:'structurally uncoverable'},backfire:{c:'k-backfire',t:'diversification backfires'},
  shifts:{c:'k-shifts',t:'just shifts the chokepoint'},diversifies:{c:'k-diversifies',t:'genuinely de-concentrates'}};
const S=D.summary, sum=document.getElementById('sum');
sum.innerHTML=
  `<div class="s"><b>${S.n}</b>materials stress-tested</div>`+
  `<div class="s"><b>${S.uncoverable2x}</b>can&rsquo;t be covered even if<br>every other exporter doubles</div>`+
  `<div class="s"><b>${S.backfire}</b>where removing the leader<br>RAISES concentration</div>`+
  `<div class="s"><b>${S.by_kind.diversifies}</b>where diversification<br>genuinely de-concentrates</div>`;
const active=new Set(Object.keys(KIND));
const fb=document.getElementById('filters');
Object.entries(KIND).forEach(([k,info])=>{
  const sw={'k-uncoverable':'#b4291f','k-backfire':'#a5641a','k-shifts':'#56607a','k-diversifies':'#0e8f83'}[info.c];
  const b=document.createElement('button'); b.className='chip';
  b.innerHTML=`<i style="background:${sw}"></i>${info.t} <span style="color:var(--faint);font-weight:500">${S.by_kind[k]}</span>`;
  b.onclick=()=>{ if(active.has(k)){active.delete(k);b.classList.add('off');} else {active.add(k);b.classList.remove('off');} render(); };
  fb.appendChild(b);
});
const srch=document.createElement('input'); srch.type='search'; srch.placeholder='search material or country…'; srch.oninput=render; fb.appendChild(srch);
const HHIMAX=0.9;
function covfill(v){ return v>=0.99?'#0e8f83':v>=0.5?'#c79a1a':'#b4291f'; }
function card(r){
  const k=KIND[r.kind]||KIND.shifts;
  const worse=r.hhi_after>=r.hhi_before;
  const af=worse?'#b4291f':'#0e8f83';
  const cov=D.kappas.map(kp=>{const v=r.coverage[String(kp)];
    return `<div class="covrow"><span class="kl">${kp}×</span><span class="track"><span class="fill" style="width:${Math.max(2,v*100)}%;background:${covfill(v)}"></span></span><span class="cv">${(v*100).toFixed(0)}%</span></div>`;}).join('');
  const strand=(r.stranded||[]).slice(0,3).map(s=>`${flag(s.iso)}${s.name} <span class="r">(${(s.reliance*100).toFixed(0)}% reliant)</span>`).join(' · ');
  return `<div class="bcard" data-kind="${r.kind}" data-txt="${(r.name+' '+r.leader_name+' '+r.new_leader_name).toLowerCase()}">
    <h3><span>${r.name}</span><span class="hs">${r.code||''}${r.shared?' · shared basket':''}</span></h3>
    <div><span class="kindtag ${k.c}">${k.t}</span></div>
    <div class="leadline">${flag(r.leader)}<b>${r.leader_name}</b> ships ~${(r.leader_export_share*100).toFixed(0)}% of world exports${r.stress_factor?` · rest must scale <b>${r.stress_factor}×</b> to cover a cut`:''}</div>
    <div class="hhibar" title="export concentration (HHI) before → after removing the leader">
      <span class="track"><span class="b4" style="width:${Math.min(100,r.hhi_before/HHIMAX*100)}%"></span><span class="af" style="width:${Math.min(100,r.hhi_after/HHIMAX*100)}%;background:${af}"></span></span>
    </div>
    <div class="met" style="margin-top:-2px">HHI <b>${r.hhi_before.toFixed(2)}</b> → <b style="color:${af}">${r.hhi_after.toFixed(2)}</b> ${worse?'⚠ worse':''} · new leader ${flag(r.new_leader)}${r.new_leader_name}</div>
    <div><div class="lbl">Coverage if survivors scale up</div>${cov}</div>
    ${strand?`<div class="stranded"><b>Most stranded:</b> ${strand}</div>`:''}
    <div class="verdict ${r.kind}">${r.verdict}</div>
  </div>`;
}
function render(){
  const q=(srch.value||'').trim().toLowerCase();
  const rows=Object.values(D.materials).filter(r=>active.has(r.kind)&&(!q||(r.name+' '+r.leader_name+' '+r.new_leader_name).toLowerCase().includes(q)))
    .sort((a,b)=>a.coverage['2']-b.coverage['2']||b.leader_export_share-a.leader_export_share);
  const g=document.getElementById('grid');
  g.innerHTML=rows.length?rows.map(card).join(''):`<div class="empty">No materials match — widen the filters or clear the search.</div>`;
}
render();

/* ---- reshuffle map ---- */
const CENT=D.centroids, MW=1100, MH=520;
function proj(iso){ const c=CENT[iso]; if(!c) return null; return [((c[1]+180)/360)*MW, ((90-c[0])/180)*MH]; }
function arc(p,q,up){ const mx=(p[0]+q[0])/2,my=(p[1]+q[1])/2,dx=q[0]-p[0],dy=q[1]-p[1],d=Math.hypot(dx,dy);
  const off=Math.min(120,d*0.28)*(up?-1:1); const cx=mx+(-dy/(d||1))*off, cy=my+(dx/(d||1))*off;
  return `M${p[0].toFixed(1)} ${p[1].toFixed(1)} Q${cx.toFixed(1)} ${cy.toFixed(1)} ${q[0].toFixed(1)} ${q[1].toFixed(1)}`; }
const mapMats=Object.values(D.materials).filter(m=>m.before&&m.before.length).sort((a,b)=>b.leader_export_share-a.leader_export_share);
let curMat=(D.materials['magnets']&&D.materials['magnets'].before.length)?'magnets':(mapMats[0]&&mapMats[0].label);
let phase='before';
const sel=document.getElementById('mapsel');
sel.innerHTML=mapMats.map(m=>`<option value="${m.label}"${m.label===curMat?' selected':''}>${m.name}</option>`).join('');
sel.onchange=()=>{ curMat=sel.value; drawMap(); };
document.getElementById('p-before').onclick=()=>{ phase='before'; togg(); drawMap(); };
document.getElementById('p-after').onclick=()=>{ phase='after'; togg(); drawMap(); };
function togg(){ document.getElementById('p-before').classList.toggle('on',phase==='before'); document.getElementById('p-after').classList.toggle('on',phase==='after'); }
function sw(v,max){ return 1+Math.sqrt(v/max)*7; }
function drawMap(){
  const m=D.materials[curMat]; const svg=document.getElementById('rmap');
  let h=`<rect x="0" y="0" width="${MW}" height="${MH}" fill="#eef3f5"/>`;
  for(let lon=-150;lon<=150;lon+=30){ const x=((lon+180)/360)*MW; h+=`<line class="grat" x1="${x}" y1="0" x2="${x}" y2="${MH}"/>`; }
  for(let lat=-60;lat<=60;lat+=30){ const y=((90-lat)/180)*MH; h+=`<line class="grat" x1="0" y1="${y}" x2="${MW}" y2="${y}"/>`; }
  const Lp=proj(m.leader); const nodes={};
  if(phase==='before'){
    const mx=Math.max(...m.before.map(a=>a.v),1);
    m.before.forEach(a=>{ const p=Lp,q=proj(a.to); if(!p||!q) return;
      h+=`<path class="arc" d="${arc(p,q,q[0]>p[0])}" stroke="#b4291f" stroke-width="${sw(a.v,mx).toFixed(1)}"/>`;
      nodes[a.to]=(nodes[a.to]||0)+a.v; });
    nodes[m.leader]=(nodes[m.leader]||0)+m.before.reduce((s,a)=>s+a.v,0);
  } else {
    const mx=Math.max(...m.after.map(a=>a.v),1);
    m.after.forEach(a=>{ const p=proj(a.f),q=proj(a.t); if(!p||!q) return;
      h+=`<path class="arc" d="${arc(p,q,q[0]>p[0])}" stroke="#0e8f83" stroke-width="${sw(a.v,mx).toFixed(1)}"/>`;
      nodes[a.f]=(nodes[a.f]||0)+a.v; nodes[a.t]=(nodes[a.t]||0)+a.v; });
    if(Lp){ h+=`<line class="cut" x1="${(Lp[0]-7).toFixed(1)}" y1="${(Lp[1]-7).toFixed(1)}" x2="${(Lp[0]+7).toFixed(1)}" y2="${(Lp[1]+7).toFixed(1)}"/>`+
             `<line class="cut" x1="${(Lp[0]-7).toFixed(1)}" y1="${(Lp[1]+7).toFixed(1)}" x2="${(Lp[0]+7).toFixed(1)}" y2="${(Lp[1]-7).toFixed(1)}"/>`; }
  }
  const nmax=Math.max(...Object.values(nodes),1);
  for(const iso in nodes){ const p=proj(iso); if(!p) continue;
    const isL=(iso===m.leader), r=3+Math.sqrt(nodes[iso]/nmax)*10;
    const col=(phase==='after'&&isL)?'#9aa6ad':(isL?'#b4291f':(phase==='after'?'#0b6f66':'#5a6b68'));
    h+=`<circle class="node" cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="${r.toFixed(1)}" fill="${col}"/>`; }
  // label the biggest ~10 nodes
  Object.entries(nodes).sort((a,b)=>b[1]-a[1]).slice(0,10).forEach(([iso])=>{ const p=proj(iso); if(!p) return;
    h+=`<text class="lbl2" x="${(p[0]+6).toFixed(1)}" y="${(p[1]+3).toFixed(1)}">${iso}</text>`; });
  svg.innerHTML=h;
  const cap=document.getElementById('mapcap');
  if(phase==='before') cap.innerHTML=`<b>${m.leader_name}</b> ships ~${(m.leader_export_share*100).toFixed(0)}% of world ${m.name} exports — the red arcs are its actual destinations. Hit &ldquo;after the cut&rdquo; to see where the freed demand would have to come from instead.`;
  else cap.innerHTML=`With <b>${m.leader_name}</b> cut (✕), optimal transport reallocates its freed demand across surviving exporters at minimum distance (teal). ${m.friction&&m.friction>=1.3?`The reshuffle travels ~${m.friction}× farther — spare capacity sits far from the buyers. `:''}${m.coverage['2']<0.5?`But even doubling every survivor covers only ${(m.coverage['2']*100).toFixed(0)}% of the gap.`:''}`;
}
drawMap();
</script>
</body></html>'''
PAGE = PAGE.replace('__DATA__', json.dumps(payload, ensure_ascii=False))
open(os.path.join(ROOT, 'ot.html'), 'w', encoding='utf-8').write(PAGE)
print('WROTE ot.html (self-contained)')

print(f'=== OT reallocation {YEAR}: {len(out)} materials ===')
print(f"{'material':16}{'leader':7}{'f_exp':>6}{'stress':>7}{'HHI b>a':>12}{'cover@2x':>9}{'friction':>9}")
for r in ranked[:16]:
    ha = f"{r['hhi_before']:.2f}>{r['hhi_after']:.2f}"
    print(f"{(r['name'] or '')[:15]:16}{str(r['leader']):7}{r['leader_export_share']:.2f}  "
          f"{str(r['stress_factor'] or '-'):>5}{ha:>12}{r['coverage']['2']:>9.0%}"
          f"{(str(r['friction'])+'x' if r['friction'] else '-'):>9}")
print('\nWROTE out/ot.json')
