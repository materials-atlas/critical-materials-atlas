#!/usr/bin/env python3
"""Out-of-sample backtest of the atlas's nowcast premise. The 2025 nowcast rests on trade structure
being persistent enough that the prior year plus current partial customs data pins the next year.
This scores that premise honestly: predict each year 2019-2024 using ONLY prior years (no peeking),
and measure how well a naive persistence model (year T ~= T-1) recovers the observed BACI. That is
the floor the reconciliation nowcast must beat, and it puts a number on 'demonstrated forecasting
skill' rather than asserting rigor. Deterministic; public per-year BACI already in out/.

Run: python build_nowcast_backtest.py
"""
import json, os, statistics

ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
LABELS = [m['label'] for m in data['materials']]
TITLE = {m['label']: m['title'].split(' (')[0] for m in data['materials']}

def load(y):
    p = os.path.join(ROOT, 'out', f'flows_{y}.json')
    return json.load(open(p, encoding='utf8')).get('materials', {}) if os.path.exists(p) else None

def shares(mats, lab):
    o, tot = {}, 0.0
    for f in (mats.get(lab) or []):
        o[f['from']] = o.get(f['from'], 0.0) + f['value']; tot += f['value']
    return {c: v / tot for c, v in o.items()} if tot else None

def hhi(sh): return sum(v * v for v in sh.values()) if sh else None
def top(sh): return max(sh, key=sh.get) if sh else None

TEST = list(range(2019, 2025))   # predict each of these out-of-sample from prior years only
per_year = []
hit = n = 0
share_mae, hhi_mae = [], []
dir_hit = dir_n = 0
by_mat = {}
chance_terms = []
for T in TEST:
    obs, prev, prev2 = load(T), load(T - 1), load(T - 2)
    if not obs or not prev:
        continue
    yhit = yn = 0
    for lab in LABELS:
        so, sp = shares(obs, lab), shares(prev, lab)
        if not so or not sp:
            continue
        at = top(so)
        n += 1; yn += 1
        _h = 1 if top(sp) == at else 0
        by_mat.setdefault(lab, []).append(_h)   # per-material blocks for the clustered bootstrap
        chance_terms.append(1.0 / len(so))       # blind-guess P(correct) = 1/#exporters that year
        if top(sp) == at:
            hit += 1; yhit += 1
        share_mae.append(abs(sp.get(at, 0) - so[at]) * 100)
        hhi_mae.append(abs(hhi(sp) - hhi(so)) * 10000)
        sp2 = shares(prev2, lab) if prev2 else None
        if sp2 and at in sp2:
            pred_dir = sp.get(at, 0) - sp2.get(at, 0)
            act_dir = so[at] - sp.get(at, 0)
            if abs(act_dir) > 0.005:
                dir_n += 1
                if (pred_dir >= 0) == (act_dir >= 0):
                    dir_hit += 1
    per_year.append((T, yhit, yn))

HIT = round(100 * hit / n)
SMAE = round(statistics.mean(share_mae), 1)
HMAE = round(statistics.mean(hhi_mae))
DIR = round(100 * dir_hit / dir_n)

# --- audit C: 95% CI via block bootstrap CLUSTERED BY MATERIAL, + a blind-guess chance baseline ---
# Material-years are not independent (a material recurs across years), so resample whole-material blocks.
import random as _rnd
_rnd.seed(42)
_mats = list(by_mat)
def _boot():
    s = [h for _ in _mats for h in by_mat[_rnd.choice(_mats)]]
    return 100 * sum(s) / len(s)
_B = sorted(_boot() for _ in range(4000))
CI_LO = round(_B[int(0.025 * len(_B))])
CI_HI = round(_B[int(0.975 * len(_B))])
CHANCE = round(100 * statistics.mean(chance_terms), 1)   # 1/#exporters averaged
import statistics as _st
MED_EX = round(1 / _st.median(chance_terms))              # median exporters per material-year
beat = round(HIT - CHANCE)
print(f"top-exporter hit {hit}/{n} = {HIT}% | share MAE {SMAE}pp | HHI MAE {HMAE} | direction {dir_hit}/{dir_n} = {DIR}%")

rows = ''.join(f'<tr><td>{T}</td><td class="n">{yh}/{yn}</td><td class="n">{round(100*yh/yn)}%</td></tr>'
               for T, yh, yn in per_year)

HTML = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png"><link rel="icon" type="image/png" sizes="48x48" href="/favicon-48.png"><link rel="icon" href="/favicon.ico" sizes="any"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="https://criticalmaterialsatlas.org/nowcast-backtest">
<title>Does last year predict this year? An out-of-sample nowcast backtest — Critical Materials Atlas</title>
<meta name="description" content="An out-of-sample test of the atlas's nowcast premise: predicting each year 2019-2024 from prior years only recovers the top exporter {HIT}% of the time — but that is the NAIVE benchmark, not skill; the model has no skill at the direction of year-over-year moves ({DIR}%), and whether the engine beats persistence is pre-registered, not yet proven.">
<meta property="og:title" content="Out-of-sample nowcast backtest — Critical Materials Atlas">
<meta property="og:description" content="{HIT}% is the naive persistence benchmark, not proof of skill. No skill at turning points ({DIR}%); engine-vs-naive pre-registered, unproven.">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 :root{{--acc:#0e7c74}}
 article{{max-width:940px}}
 .stat4{{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin:1.4rem 0}}
 @media(max-width:720px){{.stat4{{grid-template-columns:repeat(2,1fr)}}}}
 .stat{{background:var(--bg);border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:10px;padding:.85rem 1rem}}
 .stat .v{{font-size:1.7rem;font-weight:800;color:var(--navy);letter-spacing:-.02em;line-height:1}}
 .stat.warn{{border-left-color:#b4532b}}
 .stat .l{{font-size:.78rem;color:var(--mut);margin-top:.3rem;line-height:1.35}}
 table.data{{border-collapse:collapse;width:100%;font-size:.9rem;margin:1rem 0;max-width:420px}}
 table.data th,table.data td{{padding:.45rem .7rem;border-bottom:1px solid var(--line);text-align:left}}
 table.data td.n,table.data th.n{{text-align:right;font-variant-numeric:tabular-nums}}
 table.data thead th{{color:var(--navy);border-bottom:2px solid var(--navy)}}
 .rule{{background:var(--bg-soft);border-left:4px solid var(--acc);border-radius:8px;padding:.9rem 1.1rem;margin:1.3rem 0;line-height:1.6}}
 .rule b{{color:var(--navy)}}
 h2.sec{{font-size:1.2rem;color:var(--navy);border-top:1px solid var(--line);padding-top:1.4rem;margin:2rem 0 .5rem}}
 .note{{color:var(--mut);font-size:.86rem;line-height:1.55;max-width:82ch}}
</style>
</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<main id="main">
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · rigor · out-of-sample validation</div>
  <h1>Does last year predict this year?</h1>
  <p class="deck">The atlas nowcasts the newest trade year before the official data lands, on the premise that supply structure is <b>persistent</b>. That premise is testable. Predicting each year <b>2019&ndash;2024 from prior years only</b>, a naive persistence model recovers the top exporter <b>{HIT}%</b> of the time. But read that honestly: <b>{HIT}% is the naive benchmark, not a measure of skill</b> &mdash; and the verdict that matters is what persistence <i>can&rsquo;t</i> do (below), plus the fact that whether the atlas&rsquo;s engine beats this benchmark is <b>not yet proven</b>.</p>
</div></section>
<article>
  <p class="note">The 2025 figure on the slider is a <a href="methodology#nowcast">nowcast</a>, not measured BACI. Its defensibility rests on one empirical question: how much does the prior year actually tell you about the next? This page answers it the only honest way &mdash; by hiding the answer and scoring the prediction. No model here sees the year it predicts.</p>

  <div class="stat4">
    <div class="stat"><div class="v">{HIT}%</div><div class="l">the prior year names the <b>same top exporter</b> as the observed year (out-of-sample, 2019&ndash;2024, {n} material-years). <b>95% CI {CI_LO}&ndash;{CI_HI}%</b>, bootstrap clustered by material.</div></div>
    <div class="stat"><div class="v">{SMAE} pp</div><div class="l">mean absolute error on that top exporter&rsquo;s <b>share</b></div></div>
    <div class="stat"><div class="v">{HMAE}</div><div class="l">mean absolute error on <b>concentration</b> (HHI, 0&ndash;10,000 scale)</div></div>
    <div class="stat warn"><div class="v">{DIR}%</div><div class="l"><b>direction</b> of the year-over-year change called correctly &mdash; ~a coin flip</div></div>
  </div>

  <h2 class="sec">What it means</h2>
  <p>Two things, and the atlas states both. <b>The structure is highly persistent.</b> Last year alone pins this year&rsquo;s leading exporter {HIT}% of the time and its share to within about {SMAE} points &mdash; which is precisely why a nowcast that carries the prior year forward and reconciles the current year&rsquo;s partial customs data is a <i>defensible provisional estimate</i>, not a guess. This persistence baseline is the floor the reconciliation engine improves on by adding real current-year data.</p>
  <p><b>But {HIT}% is the naive benchmark, not proof of skill — and that distinction is the whole point.</b> In forecasting, the <i>persistence</i> (no-change) model is the mandatory baseline every method must beat, and it is famously <i>hard</i> to beat &mdash; Meese &amp; Rogoff (1983) showed a random walk out-forecasts structural exchange-rate models. Our {HIT}% <b>is</b> that persistence baseline, so it measures how <b>stable</b> trade structure is, not how clever the engine is. Comparing it to blind random guessing (which we did earlier) was a strawman, now dropped: nobody&rsquo;s alternative is a random draw. Two honest caveats even on the {HIT}% itself: the material-clustered 95% interval is <b>{CI_LO}&ndash;{CI_HI}%</b>; and because one country (China) tops many materials at once, the material-years share shocks &mdash; the true effective sample is smaller than 32 and that interval is, if anything, optimistic. <span style="color:var(--mut);font-size:.9em">(Rewritten after an adversarial audit flagged the strawman baseline; see the <a href="updates">changelog</a>.)</span></p>

  <div class="rule"><b>The honest limit.</b> Persistence is good at <i>levels</i> and poor at <i>turning points</i>. It calls the direction of a year-over-year move correctly only <b>{DIR}%</b> of the time &mdash; no better than chance. So read the nowcast as &ldquo;the structure of last year carried forward and re-measured,&rdquo; <b>not</b> &ldquo;a forecast of where shares are heading.&rdquo; When a share genuinely turns, a persistence-grounded nowcast is the last thing to see it. The atlas nowcast mitigates this by reconciling actual current-year Comtrade rather than extrapolating &mdash; but the limit is real and named here rather than buried.</p>

  <h2 class="sec">The harder test, pre-registered</h2>
  <p>Honesty requires naming what this backtest does <i>not</i> prove. Because top exporters rarely change, {HIT}% is a <b>high base rate</b> &mdash; persistence is a strong baseline, not a low bar cleared. The open question is whether the reconciliation engine, which folds in the current year&rsquo;s <i>partial</i> customs data, actually <b>beats</b> that baseline. It clearly <i>moves</i>: the engine&rsquo;s 2025 nowcast departs substantially from simply carrying 2024 forward, so it is incorporating new information &mdash; but whether those moves are signal or noise cannot be known until the truth arrives.</p>
  <div class="rule" style="border-left-color:#2f6fae"><b>Pre-registration.</b> The atlas&rsquo;s <b>2025 nowcast is frozen and public now</b>. When CEPII releases official BACI&nbsp;2025 (trade data lags ~1.5 years, so around 2027), we will score the frozen nowcast against it <b>and</b> against the naive-persistence baseline &mdash; with <b>MASE</b> (a scaled error where &lt;1 means it beats naive, &gt;1 means it doesn&rsquo;t) and a <b>Diebold&ndash;Mariano</b> test for whether any edge is significant &mdash; and publish the result here, win or lose. Until then, the honest statement is that the engine&rsquo;s skill <i>over</i> persistence is <b>unproven</b>. The prediction exists before the answer does; that is the difference between a forecast and a fit.</p>

  <h2 class="sec">Can a smarter model beat persistence? We tried nine.</h2>
  <p>Rather than assume persistence is best, we ran a bake-off the standard methods for a short, persistent, compositional, low-N series. Each predicts every year 2019&ndash;2024 from prior years only, scored the same way:</p>
  <div class="tblwrap" style="overflow-x:auto"><table class="data" style="max-width:560px">
    <thead><tr><th>Model</th><th class="n">top-exporter hit</th><th class="n">share error</th></tr></thead>
    <tbody>
      <tr><td><b>Persistence (naive)</b></td><td class="n"><b>84.4%</b></td><td class="n">4.83pp</td></tr>
      <tr><td>3-year moving average</td><td class="n">83.3%</td><td class="n">4.96pp</td></tr>
      <tr><td>5-year moving average</td><td class="n">81.8%</td><td class="n">5.74pp</td></tr>
      <tr><td>Exponential smoothing</td><td class="n">81.8%</td><td class="n">5.06pp</td></tr>
      <tr><td>Shrink 70% &rarr; 5-yr mean</td><td class="n">82.3%</td><td class="n"><b>4.66pp</b></td></tr>
      <tr><td>Linear trend</td><td class="n">82.3%</td><td class="n">5.75pp</td></tr>
      <tr><td>ETS damped (state-space)</td><td class="n">83.9%</td><td class="n">6.12pp</td></tr>
      <tr><td>Panel-Ridge (borrows across materials)</td><td class="n">82.3%</td><td class="n">4.85pp</td></tr>
      <tr><td><b>Compositional (CLR shrinkage)</b></td><td class="n">83.9%</td><td class="n"><b>4.51pp</b></td></tr>
      <tr><td><b>Bayesian Dirichlet (BDARMA-core)</b></td><td class="n"><b>84.9%</b></td><td class="n"><b>4.56pp</b></td></tr>
    </tbody>
  </table></div>
  <div class="rule"><b>The verdict, after testing nine models across every relevant family.</b> The sophisticated methods the statistics literature recommends for share data &mdash; <i>compositional</i> log-ratio models (Aitchison), state-space (ETS), a hierarchical panel model that borrows across all 32 materials, and a <b>Bayesian Dirichlet</b> model (the core of BDARMA) &mdash; <b>do beat naive persistence, but only modestly</b>. On the leader&rsquo;s <i>share</i> the error falls from <b>4.83 to ~4.5pp</b> (~7%); the Bayesian Dirichlet model even edges persistence on <i>who</i> leads (<b>84.9% vs 84.4%</b>), though by less than a percentage point &mdash; within noise. So the honest reading is not &ldquo;persistence is unbeatable&rdquo; but &ldquo;<b>a series this persistent leaves almost nothing for a cleverer model to add</b>&rdquo; &mdash; exactly the Meese&ndash;Rogoff result, now on our own data across nine models. The real lever is not the forecasting model at all; it is the reconciliation engine&rsquo;s use of <i>current-year</i> data, which is the pre-registered test above. <span style="color:var(--mut);font-size:.9em">(Reproducible: <code>build_nowcast_models.py</code>; methods: Aitchison 1986 compositional data; Snyder/Ord state-space; Bayesian Dirichlet ARMA.)</span></div>

  <h2 class="sec">Hit rate by test year</h2>
  <p class="note" style="margin-top:0">Top-exporter hit rate when each year is predicted from the year before, across all materials with data in both years.</p>
  <table class="data"><thead><tr><th>Predicted year</th><th class="n">correct</th><th class="n">hit rate</th></tr></thead><tbody>{rows}</tbody></table>

  <h2 class="sec">Method</h2>
  <p class="note">For each test year T (2019&ndash;2024) and each material, the &ldquo;prediction&rdquo; is the observed structure of year T&minus;1 (reconciled CEPII BACI), scored against the observed structure of year T. Metrics: whether the top exporter matches; absolute error on that exporter&rsquo;s trade share; absolute error on the exporter-side HHI; and, using year T&minus;2 as the basis for a trend, whether the sign of the year-over-year change is called correctly. A 3-year-mean baseline performs the same to within a point, so the persistence result is not an artifact of one model. This tests <i>forward persistence</i> of observed BACI &mdash; the premise under the nowcast &mdash; not the reconciliation engine&rsquo;s accuracy, which is validated separately against official BACI (top-1 exporter 25/30, 3.5% share error) on the <a href="methodology">methodology</a> page. Reproducible: <code>python build_nowcast_backtest.py</code>.</p>
  <div class="ftr" style="margin-top:1.5rem"><a href="methodology">Methodology &amp; validation</a> · <a href="method">Method hub</a> · <a href="limitations">Limitations</a></div>
</article>
</main>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>Public-data value-chain research.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>UN Comtrade · CEPII BACI</div>
  <div class="fineprint">Out-of-sample backtest of the nowcast premise; no model sees the year it predicts.</div>
</div></footer>
</body></html>'''
open(os.path.join(ROOT, 'nowcast-backtest.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote nowcast-backtest.html')
