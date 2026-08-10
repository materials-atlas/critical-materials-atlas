#!/usr/bin/env python3
"""
Risk-assessment methods — three established approaches that go beyond the transparent fixed-weight index,
each implemented on the public data and cited.

  1. Entropy-weighted TOPSIS (MCDA).  The fixed-weight supply-risk index uses weights I chose. Here the
     DATA choose the weights: Shannon-entropy weighting gives each risk criterion an objective weight by
     its information content, then TOPSIS ranks materials by closeness to the worst-case. Answers the
     "arbitrary weights" objection. (Hwang & Yoon 1981; entropy weighting per Zhang et al.; criticality
     MCDA per Achzet & Helbig 2013, Schrijvers et al. 2020.)
  2. GeoPolRisk.  A literature-standard geopolitical supply-risk indicator: concentration amplified by the
     governance risk of the producers, per stage. (Gemechu, Sonnemann & Young 2016, J. Industrial Ecology;
     Santillan-Saldivar et al. 2021.)
  3. Probabilistic supply-at-risk (Monte Carlo).  Turns the deterministic shock scenarios into a
     distribution: each producer fails with a governance-derived probability and random severity; we report
     Expected Supply-at-Risk and the 95% tail (VaR/CVaR). (Risk-metric lineage: Nassar et al. 2020.)

Writes out/riskmethods.json + riskmethods.html. Public data; deterministic (fixed RNG seed).
"""
import json, os, html
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
YEAR = os.environ.get('PROFILE_YEAR', '2024')
data = json.load(open(os.path.join(ROOT, 'out', 'data.json'), encoding='utf8'))
flows = json.load(open(os.path.join(ROOT, 'out', f'flows_{YEAR}.json'), encoding='utf8'))
WGI = json.load(open(os.path.join(ROOT, 'out', 'wgi.json'), encoding='utf8'))['wgi']
try:
    RISK = {r['label']: r['score'] for r in json.load(open(os.path.join(ROOT, 'out', 'risk.json'), encoding='utf8'))['materials']}
except Exception:
    RISK = {}
NAMES = flows.get('names', {})
MATS = data['materials']
SI = {'high': 1.0, 'medium': 0.6, 'low': 0.3}
GDEF = 0.6

def cn(i): return NAMES.get(i, i)
def e(s): return html.escape(str(s), quote=True)
def strip(t): return str(t).split(' (')[0]
def flag(iso):
    if not iso or len(iso) != 2 or not iso.isalpha(): return ''
    return ''.join(chr(0x1F1E6 + ord(c.upper()) - 65) for c in iso)
def grisk(iso):
    w = WGI.get(iso)
    return GDEF if w is None else max(0.0, min(1.0, (2.5 - w) / 5.0))

def exp_shares(label):
    o, t = {}, 0.0
    for f in flows.get('materials', {}).get(label, []) or []:
        o[f['from']] = o.get(f['from'], 0.0) + f['value']; t += f['value']
    return ({k: v / t for k, v in o.items()}, t) if t else ({}, 0.0)

# ---- assemble per-material criteria (all oriented so higher = more risk) ----
labels, X, meta = [], [], {}
for m in MATS:
    lab = m['label']; mined = m.get('mined') or []; refined = m.get('refined') or []
    msum = sum(x['v'] for x in mined) or 1
    mine_hhi = sum((x['v'] / msum) ** 2 for x in mined) if mined else 0.0
    ref_share = (refined[0]['v'] / 100.0) if refined else mine_hhi
    sh, _ = exp_shares(lab)
    trade_hhi = sum(s ** 2 for s in sh.values())
    china = sh.get('CN', 0.0)
    te = max(sh, key=sh.get) if sh else None
    te_mine = next((x['v'] for x in mined if x['c'] == te), 0.0) if te else 0.0
    gap = max(0.0, (sh.get(te, 0.0) * 100 - te_mine)) / 100.0 if te else 0.0
    norecyc = 1 - (m.get('recycling') or 0) / 100.0
    subst = SI.get(m.get('substitutability'), 0.6)
    gov_exp = sum((x['v'] / 100.0) * grisk(x['c']) for x in mined)   # production-weighted governance risk
    labels.append(lab)
    X.append([mine_hhi, ref_share, trade_hhi, china, gap, norecyc, subst, gov_exp])
    meta[lab] = {'title': strip(m['title']), 'top_mine': (mined[0]['c'] if mined else None),
                 'top_exp': te, 'china': round(china * 100), 'subst': m.get('substitutability'),
                 'recyc': m.get('recycling') or 0, 'sh': sh, 'mined': mined}
X = np.array(X, float)
CRIT = ['mine HHI', 'refining conc.', 'trade HHI', 'China share', 'origin gap', 'no recycling', 'hard to substitute', 'governance risk']
n, k = X.shape

# ---- 1. entropy weights + TOPSIS ----
Xn = X / np.where(X.sum(0) == 0, 1, X.sum(0))                 # column-normalise to probabilities
with np.errstate(divide='ignore', invalid='ignore'):
    ent = -(1 / np.log(n)) * np.nansum(np.where(Xn > 0, Xn * np.log(Xn), 0.0), axis=0)
div = 1 - ent
W = div / div.sum()
# TOPSIS on min-max normalised criteria (all benefit=risk)
rng = X.max(0) - X.min(0); rng[rng == 0] = 1
Nz = (X - X.min(0)) / rng
V = Nz * W
worst = V.max(0); best = V.min(0)                            # worst = most risky, best = least
Dworst = np.sqrt(((V - worst) ** 2).sum(1)); Dbest = np.sqrt(((V - best) ** 2).sum(1))
topsis_risk = Dbest / (Dbest + Dworst)                        # closeness to worst -> higher = riskier
topsis100 = np.round(topsis_risk / topsis_risk.max() * 100, 1)

# ---- 2. GeoPolRisk (mine + trade stage) ----
geopol = {}
for i, lab in enumerate(labels):
    mined = meta[lab]['mined']; msum = sum(x['v'] for x in mined) or 1
    mh = sum((x['v'] / msum) ** 2 for x in mined) if mined else 0.0
    gpr_mine = mh * sum((x['v'] / msum) * grisk(x['c']) for x in mined) if mined else 0.0
    sh = meta[lab]['sh']; th = sum(s ** 2 for s in sh.values())
    gpr_trade = th * sum(s * grisk(c) for c, s in sh.items())
    geopol[lab] = (gpr_mine, gpr_trade)
gmax = max((max(v) for v in geopol.values()), default=1) or 1

# ---- 3. Monte-Carlo supply-at-risk (ESaR / VaR95 / CVaR95) ----
rngen = np.random.default_rng(20260629)
NS = 20000
mc = {}
for lab in labels:
    mined = meta[lab]['mined']; msum = sum(x['v'] for x in mined) or 1
    shares = np.array([x['v'] / msum for x in mined]); probs = np.array([grisk(x['c']) for x in mined])
    if len(shares) == 0:
        mc[lab] = (0, 0, 0); continue
    fail = rngen.random((NS, len(shares))) < probs                       # each producer fails w.p. governance risk
    sev = rngen.beta(2, 2, (NS, len(shares)))                            # severity 0-1, mean .5
    mit = (1 - (meta[lab]['recyc'] / 100.0)) * SI.get(meta[lab]['subst'], 0.6)  # recycling+substitution cushion
    loss = (fail * sev * shares).sum(1) * mit * 100                       # % of world supply lost (mitigated)
    var95 = np.percentile(loss, 95); cvar = loss[loss >= var95].mean() if (loss >= var95).any() else var95
    mc[lab] = (round(float(loss.mean()), 1), round(float(var95), 1), round(float(cvar), 1))

# spearman vs fixed index
def spearman(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ra = a.argsort().argsort(); rb = b.argsort().argsort()
    return round(float(np.corrcoef(ra, rb)[0, 1]), 2)
common = [(topsis100[i], RISK[labels[i]]) for i in range(n) if labels[i] in RISK]
rho_fixed = spearman([c[0] for c in common], [c[1] for c in common]) if len(common) > 2 else None

rows = []
for i, lab in enumerate(labels):
    rows.append({'label': lab, 'title': meta[lab]['title'], 'topsis': float(topsis100[i]),
                 'fixed': RISK.get(lab), 'gpr_mine': round(geopol[lab][0] / gmax * 100, 1),
                 'gpr_trade': round(geopol[lab][1] / gmax * 100, 1),
                 'esar': mc[lab][0], 'var95': mc[lab][1], 'cvar95': mc[lab][2],
                 'top_mine': meta[lab]['top_mine'], 'top_exp': meta[lab]['top_exp'],
                 'crit': [round(float(v), 3) for v in Nz[i]]})   # min-max criteria (0-1, higher=riskier) for the index builder
weights = [{'crit': CRIT[j], 'w': round(float(W[j]), 3)} for j in range(k)]
json.dump({'year': YEAR, 'weights': weights, 'criteria': CRIT, 'spearman_vs_fixed': rho_fixed, 'materials': rows},
          open(os.path.join(ROOT, 'out', 'riskmethods.json'), 'w', encoding='utf8'), indent=1)

print(f'wrote out/riskmethods.json — TOPSIS vs fixed-index Spearman {rho_fixed}')
print('entropy weights:', {CRIT[j]: round(float(W[j]), 2) for j in range(k)})
print('\nTOP by entropy-TOPSIS:')
for r in sorted(rows, key=lambda r: r['topsis'], reverse=True)[:6]:
    print(f"  {r['title']:<22} TOPSIS {r['topsis']:.0f}  (fixed {r['fixed']})  CVaR95 {r['cvar95']:.0f}%")
print('\nTOP by tail risk (CVaR95):')
for r in sorted(rows, key=lambda r: r['cvar95'], reverse=True)[:6]:
    print(f"  {r['title']:<22} ESaR {r['esar']:.0f}%  VaR95 {r['var95']:.0f}%  CVaR95 {r['cvar95']:.0f}%")

# ---- page ----
def col(v, hi=66, mid=40): return '#c0392b' if v >= hi else '#b35e16' if v >= mid else '#3f9b46'
motif = ('<svg class="hero-motif" viewBox="0 0 560 560" fill="none" aria-hidden="true"><g stroke="#7fd2c8" stroke-opacity=".15" stroke-width="1.1"><circle cx="280" cy="280" r="232"/><ellipse cx="280" cy="280" rx="232" ry="62"/><ellipse cx="280" cy="280" rx="232" ry="132"/><ellipse cx="280" cy="280" rx="232" ry="196"/><ellipse cx="280" cy="280" rx="62" ry="232"/><ellipse cx="280" cy="280" rx="132" ry="232"/><ellipse cx="280" cy="280" rx="196" ry="232"/><line x1="280" y1="48" x2="280" y2="512"/><line x1="48" y1="280" x2="512" y2="280"/></g><g stroke="#9be3da" stroke-opacity=".26" stroke-width="1.4" fill="none"><path d="M120 360 Q 300 110 472 248"/><path d="M158 196 Q 322 300 442 422"/><path d="M120 360 Q 268 430 442 422"/></g><g fill="#bff0e8" fill-opacity=".55"><circle cx="120" cy="360" r="4.2"/><circle cx="472" cy="248" r="4.2"/><circle cx="158" cy="196" r="4.2"/><circle cx="442" cy="422" r="4.2"/></g></svg>')
wbar = ''.join(f'<span style="display:inline-block;margin:.15rem .5rem .15rem 0"><b style="color:#0e7c74">{e(w["crit"])}</b> <span style="color:#9aa6ad">{w["w"]:.2f}</span></span>' for w in sorted(weights, key=lambda x: -x['w']))
mc_sorted = sorted(rows, key=lambda r: r['cvar95'], reverse=True)
trows = ''.join(
    f'<tr><td><a href="profile-{e(r["label"])}.html">{e(r["title"])}</a></td>'
    f'<td class="n" style="font-weight:700;color:{col(r["topsis"])}">{r["topsis"]:.0f}</td>'
    f'<td class="n" style="color:#9aa6ad">{r["fixed"] if r["fixed"] is not None else "—"}</td>'
    f'<td class="n">{r["gpr_mine"]:.0f}</td><td class="n">{r["gpr_trade"]:.0f}</td>'
    f'<td class="n">{r["esar"]:.0f}%</td><td class="n" style="font-weight:700;color:{col(r["cvar95"],50,25)}">{r["cvar95"]:.0f}%</td></tr>'
    for r in sorted(rows, key=lambda r: r['topsis'], reverse=True))

out = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Risk assessment — Critical Materials Atlas</title>
<meta name="description" content="Three established risk-assessment methods on public data: entropy-weighted TOPSIS (data-driven weights), GeoPolRisk (governance-weighted geopolitical supply risk), and a Monte-Carlo supply-at-risk with VaR/CVaR tail metrics.">
<meta property="og:title" content="Critical-materials risk assessment — MCDA, GeoPolRisk, tail risk">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="methodology.html">Methodology</a><a href="risk.html">Risk index</a>
  <a href="network.html" class="hideable">Network</a><a href="scenarios.html" class="hideable">Scenarios</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero">{motif}<div class="wrap">
  <div class="eyebrow">Method · risk assessment</div>
  <h1>Three ways to score the risk — letting the data, not me, decide</h1>
  <p class="deck">The transparent supply-risk index uses weights I chose. Here are three established alternatives from the criticality literature, each computed on the same public data: a data-driven composite (entropy-TOPSIS), a governance-weighted geopolitical indicator (GeoPolRisk), and a probabilistic supply-at-risk with tail metrics.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout">Three established ways to score supply risk &mdash; each letting the data or the criticality literature, not the weights I chose, decide.
  <details class="howto"><summary>The three methods</summary>
  <p><b>1 &middot; Entropy-weighted TOPSIS (data-driven weights).</b> Shannon entropy gives each criterion a weight by how much it varies across the 32 materials, then TOPSIS ranks each by closeness to the worst case (Hwang &amp; Yoon 1981; Achzet &amp; Helbig 2013). The weights it produces: {wbar}. The ranking <b>diverges moderately</b> from my fixed-weight index (Spearman <b>ρ {rho_fixed}</b>) &mdash; the data load most weight on <b>China-share</b> and <b>origin-gap</b>, pushing tungsten, magnesium and magnets up.</p>
  <p><b>2 &middot; GeoPolRisk</b> (Gemechu et al. 2016) &mdash; stage concentration &times; the governance risk of the producers, for the mine and trade stages.</p>
  <p><b>3 &middot; Monte-Carlo supply-at-risk</b> &mdash; each producer fails with a governance-derived probability and a random severity; over 20,000 draws I report the mean loss (<b>ESaR</b>) and the 95% tail (<b>VaR/CVaR</b>) &mdash; the shock scenarios made probabilistic.</p>
  <p class="howto-src"><b>Caveat:</b> entropy rewards <i>dispersion</i>, not importance, so it nearly zeroes near-uniform criteria like recycling &mdash; read TOPSIS as a data-driven <i>complement</i> to the fixed index, not a verdict. All on public data, deterministic (fixed seed); disruption probabilities are governance-derived assumptions, not forecasts.</p>
  </details></div>
  <table>
    <thead><tr><th>Material</th>
      <th class="n" title="entropy-weighted TOPSIS risk, 0-100 (data-driven weights)">TOPSIS</th>
      <th class="n" title="my transparent fixed-weight index, for comparison">fixed</th>
      <th class="n" title="GeoPolRisk, mine stage (0-100)">GPR mine</th>
      <th class="n" title="GeoPolRisk, trade stage (0-100)">GPR trade</th>
      <th class="n" title="Expected Supply-at-Risk: mean % of world supply lost in a Monte-Carlo disruption">ESaR</th>
      <th class="n" title="CVaR95: average loss in the worst 5% of simulations (tail risk)">CVaR95</th></tr></thead>
    <tbody>{trows}</tbody>
  </table>
  <p class="note">Computed by <code>build_riskmethods.py</code> from <a href="out/data.json">data.json</a> + <a href="out/flows_{YEAR}.json">flows_{YEAR}.json</a> + <a href="out/wgi.json">wgi.json</a> → <a href="out/riskmethods.json">riskmethods.json</a>. Tail risk highest: {', '.join(e(r['title']) for r in mc_sorted[:4])}. A screening panel — the Monte-Carlo probabilities are transparent governance-based assumptions, not predictions.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="risk.html">Supply-risk index</a><br><a href="criticality.html">Governance-weighted criticality</a><br><a href="scenarios.html">Shock scenarios</a><br><a href="technical-note.html">Technical note</a></div>
  <div><h4>Methods</h4>Entropy-TOPSIS (Hwang &amp; Yoon)<br>GeoPolRisk (Gemechu 2016)<br>Monte-Carlo VaR/CVaR</div>
  <div class="fineprint">Established risk-assessment methods on public data; a screening panel, not forecasts. Disruption probabilities are governance-derived assumptions.</div>
</div></footer>
</body></html>'''
open(os.path.join(ROOT, 'riskmethods.html'), 'w', encoding='utf8', newline='\n').write(out)
print('wrote riskmethods.html')
