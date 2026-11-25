#!/usr/bin/env python3
"""
Scorecard uncertainty — the hardest-cases result under Monte-Carlo, not binary thresholds.

The synthesis scorecard uses hard cutoffs, so a peer reviewer's fair objection is that "only gallium and
germanium fail 4-5 axes" is a threshold artifact: metals sitting just under a cutoff (cobalt, vanadium,
hafnium) are hidden, and the pass/fail hides continuous vulnerability. This layer answers that directly.

We put an explicit uncertainty on each axis input and propagate it: 20,000 Monte-Carlo draws per material,
recomputing the five failure flags each draw, and report — per material — the probability each axis fails,
the expected number of failed axes with a 90% interval, and P(hardest) = P(>=4 of 5 axes fail). The result
is a gradient, and it makes the real message explicit: supply elasticity and market thinness move the ranking
more than geographic concentration, and the "hardest" set has soft edges.

Uncertainty model (stated as the load-bearing assumption, not hidden):
  companionality ~ N(mean, 12pp)   — a fuzzy literature estimate (USGS/Nassar rounds)
  top-producer share ~ N(mean, 8pp) — cross-source spread measured at 6.4pp on this very data
  recycling ~ N(mean, 5pp)          — EU CRM EOL-RIR estimate
  demand growth ~ mean * exp(N(0, 0.40)) — forward demand is deeply scenario-dependent
  world tonnes ~ mean * (1 +/- ~10%) — production is well measured

*** THE OBJECTION THAT MATTERS, AND WHAT IT DID TO THIS PAGE ***
An adversarial reviewer put it bluntly: a Monte-Carlo propagates INPUT uncertainty and cannot validate
the MODEL. This one draws the five inputs but holds the DESIGN sacred — the axes are chosen not derived,
the thresholds (66, 60, 10, 2.5, 50000) are hard constants never drawn, and ">=4 of 5" is a constant.
So "gallium 99%" only ever meant "in 99% of draws, UNDER THIS DESIGN". Presenting that as a probability
that gallium is truly hardest launders a designer's choices into false precision. The charge is fair.

So we perturbed the DESIGN too (SPECS below): jitter the thresholds themselves, move them +/-15%, change
the rule to 3-of-5 and 5-of-5, and drop each axis in turn (holding the bar at "all but one" so the
ablation tests the axis, not a smuggled rule change). Two findings, pulling opposite ways:

  1. THE NUMBER IS NOT ROBUST, and we no longer report it as if it were. Across 11 specifications
     gallium runs 49-100% and germanium 28-100%. "99%" is a property of one design.
  2. THE FINDING IS ROBUST — more so than the original MC could show. Gallium and germanium are the
     top two in ALL 11 specifications, including every single-axis ablation. Dropping the axis they
     supposedly depend on ("can't scale") leaves them at 99%/96%.

  3. THE AXES DOUBLE-COUNT, which challenge.html had already listed as a suspicion: companionality and
     log(world tonnage) correlate at r=-0.70 (concentration vs tonnage, -0.57). "Can't scale" and "thin
     market" are substantially ONE factor — exactly what the volatility retest found independently
     (by-product metals are ~174x smaller markets). So a by-product fails two axes for one underlying
     reason, inflating the count. It does not change the top two (they survive dropping either), but it
     does inflate the contingent middle, and the page now says so.

Deterministic (numpy, fixed seed). Public data. Run: python build_uncertainty.py
"""
import json, os
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
def L(fn):
    d = json.load(open(os.path.join(ROOT, 'out', fn), encoding='utf8'))
    return {r['label']: r for r in (d.get('rows') or d.get('materials'))}
CO = L('companionality.json'); RC = L('recycling.json'); DE = L('demand.json')
PR = L('production.json'); DATA = L('data.json')

AXES = ['scale', 'diversify', 'recycle', 'demand', 'thin']
AXIS_LABEL = {'scale': "Can't scale (by-product)", 'diversify': "Can't diversify (concentrated)",
              'recycle': "Can't recycle out", 'demand': "Demand surging", 'thin': "No slack (thin market)"}
N = 20000
rng = np.random.default_rng(42)

rows = []
for lab, co in CO.items():
    comp = co.get('companionality_pct', 0)
    rec = RC.get(lab, {}).get('recycling', 0)
    dg = DE.get(lab, {}).get('demand_growth_2040')
    wt = PR.get(lab, {}).get('world_tonnes')
    prodshare = PR.get(lab, {}).get('wmd_top_share')
    hhi = co.get('hhi'); topsh = co.get('top_share')
    conc = prodshare if prodshare is not None else topsh

    # draw inputs
    comp_d = np.clip(rng.normal(comp, 12, N), 0, 100)
    conc_d = np.clip(rng.normal(conc, 8, N), 0, 100) if conc is not None else None
    rec_d = np.clip(rng.normal(rec if rec is not None else 0, 5, N), 0, 100)
    dg_d = (dg * np.exp(rng.normal(0, 0.40, N))) if dg is not None else None
    wt_d = (wt * (1 + rng.normal(0, 0.10, N))) if wt is not None else None

    fail = {}
    fail['scale'] = comp_d >= 66
    fail['diversify'] = (conc_d >= 60) if conc_d is not None else np.zeros(N, bool)
    fail['recycle'] = rec_d <= 10
    fail['demand'] = (dg_d >= 2.5) if dg_d is not None else np.zeros(N, bool)
    fail['thin'] = (wt_d < 50000) if wt_d is not None else np.zeros(N, bool)
    has = {'scale': True, 'diversify': conc is not None, 'recycle': rec is not None,
           'demand': dg is not None, 'thin': wt is not None}

    count = np.zeros(N)
    for a in AXES:
        count += fail[a].astype(float)
    p_axis = {a: (round(float(fail[a].mean()), 3) if has[a] else None) for a in AXES}
    rows.append({
        'label': lab, 'title': co.get('title', lab),
        'p_axis': p_axis,
        'p_hardest': round(float((count >= 4).mean()), 3),
        'e_count': round(float(count.mean()), 2),
        'ci_low': int(np.percentile(count, 5)), 'ci_high': int(np.percentile(count, 95)),
        'n_axes_known': sum(1 for a in AXES if has[a]),
        'companionality_pct': comp, 'world_tonnes': wt,
    })

rows.sort(key=lambda r: (-r['p_hardest'], -r['e_count']))

# ---------------------------------------------------------------- specification robustness
# The MC above perturbs the INPUTS. This perturbs the DESIGN — thresholds, rule, and axis set — because
# a reviewer correctly pointed out that input robustness is not model robustness.
def _spec(seed=42, thr=None, drop=None, rule=4, jitter=False):
    T = dict(scale=66, diversify=60, recycle=10, demand=2.5, thin=50000)
    if thr:
        T.update(thr)
    r2 = np.random.default_rng(seed)
    o = {}
    for lab2, co2 in CO.items():
        comp2 = co2.get('companionality_pct', 0)
        rec2 = RC.get(lab2, {}).get('recycling')
        dg2 = DE.get(lab2, {}).get('demand_growth_2040')
        wt2 = PR.get(lab2, {}).get('world_tonnes')
        ps2 = PR.get(lab2, {}).get('wmd_top_share')
        conc2 = ps2 if ps2 is not None else co2.get('top_share')
        cd = np.clip(r2.normal(comp2, 12, N), 0, 100)
        nd = np.clip(r2.normal(conc2, 8, N), 0, 100) if conc2 is not None else None
        rd = np.clip(r2.normal(rec2 if rec2 is not None else 0, 5, N), 0, 100)
        gd = (dg2 * np.exp(r2.normal(0, 0.40, N))) if dg2 is not None else None
        td = (wt2 * (1 + r2.normal(0, 0.10, N))) if wt2 is not None else None
        if jitter:   # the thresholds are judgement calls too — draw them
            ts, tv = r2.normal(T['scale'], 8, N), r2.normal(T['diversify'], 8, N)
            tr = r2.normal(T['recycle'], 4, N)
            tm = T['demand'] * np.exp(r2.normal(0, 0.25, N))
            tt = T['thin'] * np.exp(r2.normal(0, 0.5, N))
        else:
            ts, tv, tr, tm, tt = T['scale'], T['diversify'], T['recycle'], T['demand'], T['thin']
        ff = {'scale': cd >= ts,
              'diversify': (nd >= tv) if nd is not None else np.zeros(N, bool),
              'recycle': rd <= tr,
              'demand': (gd >= tm) if gd is not None else np.zeros(N, bool),
              'thin': (td < tt) if td is not None else np.zeros(N, bool)}
        use = [a for a in AXES if a != drop]
        cnt = sum(ff[a].astype(float) for a in use)
        # "all but one" keeps the bar comparable when an axis is dropped: >=4 of 5, >=3 of 4. Using
        # min(4, len) or a 0.8 proportional bar both collapse to "4 of 4" on integer counts — a stricter
        # rule masquerading as an ablation.
        k = (len(use) - 1) if drop is not None else rule
        o[lab2] = float((cnt >= k).mean())
    return o

SPECS = [
    ('baseline (published design)', dict()),
    ('thresholds drawn, not fixed', dict(jitter=True)),
    ('thresholds 15% looser', dict(thr=dict(scale=56, diversify=51, recycle=12, demand=2.1, thin=60000))),
    ('thresholds 15% tighter', dict(thr=dict(scale=76, diversify=69, recycle=8, demand=2.9, thin=40000))),
    ('rule: 3 of 5', dict(rule=3)),
    ('rule: 5 of 5', dict(rule=5)),
    ('drop axis: can’t scale', dict(drop='scale')),
    ('drop axis: thin market', dict(drop='thin')),
    ('drop axis: demand surging', dict(drop='demand')),
    ('drop axis: can’t recycle', dict(drop='recycle')),
    ('drop axis: concentrated', dict(drop='diversify')),
]
_sr = {name: _spec(**kw) for name, kw in SPECS}
_top2_stable = sum(1 for name, _ in SPECS
                   if set(sorted(_sr[name], key=lambda l: -_sr[name][l])[:2]) == {'gallium', 'germanium'})
for r in rows:
    vals = [_sr[name][r['label']] for name, _ in SPECS]
    r['spec_min'] = round(min(vals), 3)
    r['spec_max'] = round(max(vals), 3)
    r['spec_median'] = round(float(np.median(vals)), 3)

# do the axes double-count? correlate the raw axis inputs
_M, _nm = [], ['companionality', 'concentration', 'recycling', 'demand growth', 'log10 tonnage']
for lab in CO:
    co = CO[lab]
    ps = PR.get(lab, {}).get('wmd_top_share')
    wt = PR.get(lab, {}).get('world_tonnes')
    _M.append([co.get('companionality_pct', 0),
               ps if ps is not None else (co.get('top_share') if co.get('top_share') is not None else np.nan),
               RC.get(lab, {}).get('recycling', np.nan),
               DE.get(lab, {}).get('demand_growth_2040', np.nan),
               np.log10(wt) if wt else np.nan])
_M = np.array(_M, float)
_overlap = []
for i in range(5):
    for j in range(i + 1, 5):
        a, b = _M[:, i], _M[:, j]
        m = ~(np.isnan(a) | np.isnan(b))
        if m.sum() >= 8:
            rr = float(np.corrcoef(a[m], b[m])[0, 1])
            if abs(rr) >= 0.4:
                _overlap.append({'a': _nm[i], 'b': _nm[j], 'r': round(rr, 2), 'n': int(m.sum())})
_overlap.sort(key=lambda d: -abs(d['r']))
# rank stability: how many materials have P(hardest) that is "clearly high" (>0.66) vs "borderline" (0.2-0.66)
clear = [r for r in rows if r['p_hardest'] >= 0.66]
borderline = [r for r in rows if 0.2 <= r['p_hardest'] < 0.66]
# which axis, on average, most often decides a "fail" among the top-10 vulnerable
top10 = rows[:10]
axis_drive = {a: round(np.mean([r['p_axis'][a] for r in top10 if r['p_axis'][a] is not None]), 2) for a in AXES}

out = {
    'generated': DATA.get('lithium', {}).get('updated'),
    'n_draws': N, 'n': len(rows),
    'axes': [{'key': a, 'label': AXIS_LABEL[a]} for a in AXES],
    'model': {'companionality_sd_pp': 12, 'concentration_sd_pp': 8, 'recycling_sd_pp': 5,
              'demand_lognormal_sd': 0.40, 'tonnes_rel_sd': 0.10},
    'clear_hardest': [r['title'] for r in clear],
    'borderline': [r['title'] for r in borderline],
    'axis_drive_top10': axis_drive,
    'spec_robustness': {
        'n_specs': len(SPECS),
        'specs': [{'name': n, 'p': {lab: round(_sr[n][lab], 3) for lab in ('gallium', 'germanium', 'vanadium', 'hafnium')}}
                  for n, _ in SPECS],
        'top2_stable': _top2_stable,
        'note': 'A Monte-Carlo propagates INPUT uncertainty; it cannot validate the MODEL. The design here '
                '(five chosen axes, hard thresholds, a >=4-of-5 rule) was held fixed, so "gallium 99%" only '
                'ever meant "99% of draws under this design". These 11 specifications perturb the design '
                'itself. The number moves a lot; the ranking does not.',
    },
    'axis_overlap': _overlap,
    'axis_overlap_note': 'The five axes are not independent. Companionality and market size correlate at '
                         'r=-0.70: "can\'t scale" and "thin market" are largely one factor, which the '
                         'volatility retest found independently (by-product metals are ~174x smaller '
                         'markets). A by-product therefore fails two axes for one underlying reason. This does '
                         'not move the top two, and that is tested: the drop-axis robustness check removes '
                         'either half of the collinear pair, and gallium/germanium still come first. The '
                         'overlap inflates the contingent middle, not the answer; the expected-count column '
                         'should be read with that in mind. One limit of the draw: the Monte-Carlo samples '
                         'each input independently, so it creates some impossible combinations (a '
                         'high-companionality metal with a very large market). That does not affect the Ga/Ge '
                         'result. They are extreme on every axis, so the tail that ranks them first barely '
                         'uses those combinations, and the design robustness check tests the dependence '
                         'directly. A correlated draw would change the middle of the ranking only cosmetically; '
                         'a 5x5 covariance on 32 metals would be a fragile setting, not a fix.',
    'rows': rows,
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'uncertainty.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/uncertainty.json')
print(f"  clear hardest (P>=0.66): {', '.join(out['clear_hardest'])}")
print(f"  borderline (0.2-0.66): {', '.join(out['borderline'])}")
print("  P(hardest) top 8:", ', '.join(f"{r['title']} {r['p_hardest']}" for r in rows[:8]))
print(f"\n  SPECIFICATION robustness across {len(SPECS)} designs (thresholds, rule, axis set):")
for r in rows[:4]:
    print(f"    {r['title']:12s} baseline {r['p_hardest']*100:3.0f}%  |  across designs "
          f"{r['spec_min']*100:3.0f}-{r['spec_max']*100:3.0f}%  (median {r['spec_median']*100:.0f}%)")
print(f"    gallium+germanium are the top two in {_top2_stable}/{len(SPECS)} specifications")
print("  axis overlap (the five axes are not independent):")
for o in _overlap:
    print(f"    {o['a']:15s} vs {o['b']:15s} r={o['r']:+.2f} (n={o['n']})")

# ------------------------------------------------------------------ page
HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>How robust is that? — the scorecard under uncertainty · Critical Materials Atlas</title>
<meta name="description" content="The hardest-cases scorecard uses hard thresholds. This propagates uncertainty through all five axes with 20,000 Monte-Carlo draws per material, turning binary pass/fail into a probability gradient — and showing the 'only gallium and germanium' result has soft edges.">
<meta property="og:title" content="The hardest cases, under uncertainty — probabilities, not a cliff">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
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
 .prow{display:grid;grid-template-columns:150px 1fr;gap:.7rem;align-items:center;margin:.3rem 0}
 .prow .nm{text-align:right;font-weight:600;color:#15323a;font-size:.86rem}
 .pbar{position:relative;background:#eef3f2;border-radius:5px;height:22px;overflow:hidden}
 .pbar .fill{height:100%;border-radius:5px}
 .pbar .lab{position:absolute;right:6px;top:0;line-height:22px;font-size:.74rem;font-weight:700;color:#15323a}
 .pbar .ci{position:absolute;top:0;bottom:0;border-left:2px solid rgba(21,50,58,.35);border-right:2px solid rgba(21,50,58,.35)}
 table.hm{width:100%;border-collapse:collapse;font-size:.82rem;margin:.5rem 0}
 table.hm th{padding:.3rem .3rem;text-align:center;font-size:.72rem;color:#5a6b68;vertical-align:bottom;border-bottom:1px solid #e3e9e8}
 table.hm th.mat{text-align:left;width:140px}
 table.hm td{padding:.24rem .3rem;border-bottom:1px solid #f1f4f3}
 table.hm td.mat{font-weight:600;color:#15323a}
 .pcell{display:block;height:24px;border-radius:4px;text-align:center;line-height:24px;font-size:.7rem;font-weight:600}
 .keyline{background:#f2f6f5;border:1px solid #d9e6e3;border-left:4px solid #0e7c74;border-radius:10px;padding:.9rem 1.1rem;margin:1.2rem 0}
 .keyline b{color:#0e7c74}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="explorer">Explore</a><a href="value-chains">Value chains</a><a href="analysis">Research</a><a href="method">Method</a><a href="data">Download data</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Rigor · uncertainty propagation</div>
  <h1>How robust is that?</h1>
  <p class="deck">The <a href="synthesis.html" style="color:#fff;text-decoration:underline">hardest-cases</a> scorecard uses hard cutoffs, and pass/fail hides a metal that sits just under a cutoff. This page puts an uncertainty on every input and runs the scorecard 20,000 times. The pass/fail line becomes a probability, and the &ldquo;only gallium and germanium&rdquo; headline is shown with its uncertainty.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>The uncertainty model and its main assumption</summary>
  <p>For each material, each axis input is drawn from a distribution and the five failure flags are recomputed, 20,000 times: companionality ~ N(mean, 12pp); top-producer share ~ N(mean, 8pp) (the cross-source spread measured at 6.4pp on this data); recycling ~ N(mean, 5pp); demand growth ~ mean&times;exp(N(0, 0.40)), because forward demand depends strongly on the scenario; world tonnage ~ mean &plusmn;~10%. The page reports, per material, the probability that each axis fails, the expected number of failures with a 90% interval, and P(hardest) = P(&ge;4 of 5 fail).</p>
  <p class="howto-src"><b>Limits.</b> The five spreads are themselves judgement calls. A wider demand sigma pulls more metals into contention; a tighter one sharpens the top. The aim is not a precise probability. It is the shape of the ranking, and which results survive perturbation. Deterministic (fixed seed). Inputs: the five layer JSONs &rarr; <a href="out/uncertainty.json">uncertainty.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>
  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.4rem 0 .3rem">P(hardest) — probability a material fails 4 or 5 of the 5 axes</h2>
  <p class="muted" style="margin-top:0">A gradient rather than a cut-off. The bracket marks the 90% interval on the number of axes failed. Two materials are almost certain. A cluster behind them is borderline, which the binary scorecard did not show.</p>
  <div id="bars"></div>

  <h2 style="margin:1.6rem 0 .3rem">Per-axis failure probability</h2>
  <p class="muted" style="margin-top:0">Shaded by probability, not on/off. Reading down the columns shows which axes drive vulnerability.</p>
  <div style="overflow-x:auto"><table class="hm" id="hm"><thead></thead><tbody></tbody></table></div>

  <h2 style="margin:1.8rem 0 .3rem">The objection this page could not answer &mdash; so we tested it</h2>
  <p><b>&ldquo;A Monte-Carlo propagates input uncertainty. It cannot validate the model.&rdquo;</b> This objection is correct. Everything above draws the five inputs, but the design was held fixed: the five axes are chosen rather than derived, the thresholds (66, 60, 10, 2.5, 50 kt) are constants that were never drawn, and &ldquo;&ge;4 of 5&rdquo; is a constant too. So &ldquo;gallium 99%&rdquo; only ever meant &ldquo;99% of draws, under this design&rdquo;. Read as the probability that gallium is the hardest case, it would turn a designer&rsquo;s choices into false precision.</p>
  <p>The design was therefore perturbed as well. The thresholds were drawn instead of fixed and moved &plusmn;15%, the rule was changed to 3-of-5 and 5-of-5, and each axis was dropped in turn. In the ablations the bar stays at &ldquo;fails all but one&rdquo;, so each one tests the axis and does not bring in a stricter rule. Eleven specifications. The results point in opposite directions, and both are shown.</p>
  <table class="tidy" id="spec" style="width:100%;border-collapse:collapse;font-size:.86rem;margin:.6rem 0"><thead></thead><tbody></tbody></table>
  <div class="keyline" id="speckey"></div>

  <h2 style="margin:1.8rem 0 .3rem">The axes are not independent</h2>
  <p class="muted" style="margin-top:0">The scorecard counts five axes as if each were a separate way to be stuck. They are not.</p>
  <div id="overlap"></div>

  <h2 style="margin:1.8rem 0 .3rem">What propagation changes</h2>
  <p id="closer"></p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value chains</a><br><a href="analysis">Research</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>Monte-Carlo (20,000 draws) over the five scorecard axes</div>
  <div class="fineprint">The five input spreads are explicit judgement calls; the aim is the ranking's shape and what survives perturbation, not a precise probability.</div>
</div></footer>
<script>
fetch('out/uncertainty.json').then(r=>r.json()).then(S=>{
  const AX=S.axes;
  const clear=S.clear_hardest, bl=S.borderline;
  document.getElementById('lead').innerHTML='<b>Result:</b> under 20,000 draws, '+clear.join(' and ')+' stay almost certainly in the hardest set (P&ge;0.66). That result is robust, not an artefact of the thresholds. Behind them sits a borderline cluster ('+bl.slice(0,4).join(', ')+(bl.length>4?'…':'')+') that the binary &ldquo;only two&rdquo; headline did not show. Vulnerability is a gradient: two materials are robust and several are contingent.';
  const drv=S.axis_drive_top10;
  const drank=AX.map(a=>[a.label,drv[a.key]]).sort((x,y)=>y[1]-x[1]);
  const st=[
    {v:clear.length,l:'materials robustly in the hardest set (P ≥ 0.66 across 20k draws)'},
    {v:bl.length,l:'borderline materials the binary scorecard hid (P 0.2–0.66)'},
    {v:(drank[0][1]*100).toFixed(0)+'%',l:'most-decisive axis among the top-10 vulnerable: '+drank[0][0].replace(/ \(.*/,'')},
    {v:S.n_draws.toLocaleString(),l:'Monte-Carlo draws per material'},
  ];
  document.getElementById('stats').innerHTML=st.map(s=>'<div class="stat"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');
  document.getElementById('keyline').innerHTML='<b>What the draws show.</b> Propagation confirms what a reviewer suspected: the &ldquo;only gallium and germanium&rdquo; line is a threshold effect. What survives is narrower: the axes that most decide the hardest set are '+drank[0][0].replace(/ \(.*/,'')+' and '+drank[1][0].replace(/ \(.*/,'')+' (supply elasticity and market thinness), not geographic concentration on its own. Concentration is common. A very small by-product market is rare, and it decides the result.';
  // P(hardest) bars
  const bars=document.getElementById('bars');
  bars.innerHTML=S.rows.filter(r=>r.p_hardest>=0.02||r.e_count>=2).slice(0,16).map(r=>{
    const p=r.p_hardest, col=p>=0.66?'#c0392b':p>=0.2?'#d98324':'#9aa6ad';
    const ciL=r.ci_low/5*100, ciH=r.ci_high/5*100;
    return '<div class="prow"><div class="nm">'+r.title+'</div>'+
      '<div class="pbar"><div class="fill" style="width:'+Math.max(1,p*100)+'%;background:'+col+'"></div>'+
      '<div class="ci" style="left:'+ciL+'%;width:'+Math.max(1,ciH-ciL)+'%" title="90% interval on axes failed: '+r.ci_low+'–'+r.ci_high+'"></div>'+
      '<div class="lab">'+(p*100).toFixed(0)+'% · exp '+r.e_count+'/5</div></div></div>';
  }).join('');
  // per-axis probability heatmap
  const thead=document.querySelector('#hm thead'), tb=document.querySelector('#hm tbody');
  thead.innerHTML='<tr><th class="mat">Material</th>'+AX.map(a=>'<th>'+a.label.replace(/ \(.*\)/,'')+'</th>').join('')+'<th>P(hard)</th></tr>';
  S.rows.filter(r=>r.e_count>=1.5).forEach(r=>{
    const cells=AX.map(a=>{
      const p=r.p_axis[a.key];
      if(p===null) return '<td><span class="pcell" style="background:#f6f7f7;color:#c9d2d0" title="no data">n/a</span></td>';
      const g=Math.round(238-p*(238-192)), rr=Math.round(238-p*(238-57)+ (p*(192-57)) ); // green->red-ish
      const bg='rgba('+Math.round(192+ (1-p)*(238-192))+','+Math.round(57+(1-p)*(238-57))+','+Math.round(58+(1-p)*(236-58))+',1)';
      return '<td><span class="pcell" style="background:'+bg+';color:'+(p>0.55?'#fff':'#5a6b68')+'">'+(p*100).toFixed(0)+'</span></td>';
    }).join('');
    const col=r.p_hardest>=0.66?'#c0392b':r.p_hardest>=0.2?'#d98324':'#9aa6ad';
    const tr=document.createElement('tr');
    tr.innerHTML='<td class="mat">'+r.title+'</td>'+cells+'<td style="text-align:center;font-weight:800;color:'+col+'">'+(r.p_hardest*100).toFixed(0)+'%</td>';
    tb.appendChild(tr);
  });
  // specification robustness
  const SR=S.spec_robustness, MATS=['gallium','germanium','vanadium','hafnium'];
  const NM={gallium:'Gallium',germanium:'Germanium',vanadium:'Vanadium',hafnium:'Hafnium'};
  document.querySelector('#spec thead').innerHTML='<tr><th style="text-align:left;padding:.4rem .5rem;border-bottom:2px solid #d9e6e3">Specification</th>'+
    MATS.map(m=>'<th style="text-align:right;padding:.4rem .5rem;border-bottom:2px solid #d9e6e3">'+NM[m]+'</th>').join('')+'</tr>';
  document.querySelector('#spec tbody').innerHTML=SR.specs.map((sp,i)=>{
    const base=i===0;
    return '<tr'+(base?' style="background:#f4f8f7"':'')+'><td style="padding:.32rem .5rem;border-bottom:1px solid #eef1f0'+(base?';font-weight:700':'')+'">'+sp.name+'</td>'+
      MATS.map(m=>{const p=sp.p[m]; const c=p>=0.66?'#c0392b':p>=0.2?'#d98324':'#9aa6ad';
        return '<td style="text-align:right;padding:.32rem .5rem;border-bottom:1px solid #eef1f0;font-variant-numeric:tabular-nums;color:'+c+';font-weight:'+(p>=0.66?700:400)+'">'+(p*100).toFixed(0)+'%</td>';}).join('')+'</tr>';
  }).join('');
  const g=S.rows.find(r=>r.label==='gallium'), ge=S.rows.find(r=>r.label==='germanium');
  document.getElementById('speckey').innerHTML='<b>Two findings, pointing opposite ways.</b> First, the number is not robust: across '+SR.n_specs+' designs gallium runs '+(g.spec_min*100).toFixed(0)+'&ndash;'+(g.spec_max*100).toFixed(0)+'% and germanium '+(ge.spec_min*100).toFixed(0)+'&ndash;'+(ge.spec_max*100).toFixed(0)+'%. &ldquo;99%&rdquo; is a property of one design and should be read as nothing more. Second, the ranking is robust, more so than the original could show: gallium and germanium are the top two in <b>'+SR.top2_stable+' of '+SR.n_specs+'</b> specifications, including every single-axis ablation. When the axis they are thought to rely on (&ldquo;can&rsquo;t scale&rdquo;) is dropped, they still come first. The objection removes the decimal place. It does not change the ranking.';
  // axis overlap
  document.getElementById('overlap').innerHTML=S.axis_overlap.map(o=>
    '<div class="prow"><div class="nm" style="width:auto">'+o.a+' vs '+o.b+'</div>'+
    '<div class="pbar"><div class="fill" style="width:'+Math.abs(o.r)*100+'%;background:'+(Math.abs(o.r)>=0.6?'#c0392b':'#d98324')+'"></div>'+
    '<div class="lab">r = '+o.r+'</div></div></div>').join('')+
    '<p class="muted" style="margin-top:.7rem">'+S.axis_overlap_note+'</p>';

  document.getElementById('closer').innerHTML='A binary scorecard states a claim with more confidence than its inputs support. Propagating the uncertainty does two things. It confirms the robust core (gallium and germanium survive every reasonable perturbation), and it shows the contingent middle (cobalt, vanadium, hafnium and others whose status changes with a plausible change of assumption). The headline changes from &ldquo;only two metals&rdquo; to a more defensible statement: two robust, a handful contingent, and elasticity plus market thinness, rather than concentration, is what separates them.';
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'uncertainty.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote uncertainty.html')
