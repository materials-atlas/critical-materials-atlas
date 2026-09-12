#!/usr/bin/env python3
"""
Host coupling — does a companion's price track its HOST, or just the commodity cycle?

Child of the price test, which claimed a by-product metal's price direction is set by its host's cycle.
This tests that mechanism. The FIRST version of this page reported a mean best-host correlation of ~0.29
and named five metals that "beat the control". All three of those legs turned out to be broken, and this
rewrite retracts them in place:

  1. THE CONTROL WAS NOT A CONTROL. It compared corr(companion, host) with corr(companion, base index) and
     called the pair host-specific if the difference exceeded an arbitrary 0.1. Subtracting two correlations
     is not residualisation and has no sampling theory behind it. The correct statistic is the PARTIAL
     correlation — regress the common cycle out of BOTH series, then correlate the residuals. Doing it
     properly takes the mean from +0.27 to +0.03. The coupling was the macro cycle all along. Watch it
     happen per metal: antimony +0.58 -> -0.05, molybdenum +0.56 -> +0.03, silver +0.50 -> -0.01,
     cobalt +0.47 -> -0.23. Those were pure cycle, credited to the host.
  2. IT WAS NEVER SIGNIFICANT. At n~21 annual points the 5% critical correlation is |r| ~ 0.44. A mean of
     0.29 is below it. The page reported noise as a finding. It also chose the BEST-MATCHING host out of
     two or three candidates and then tested at 5%, which is cherry-picking: ~30 such tests manufacture
     ~1.5 false positives by chance. Hosts are now PRE-SPECIFIED (one per companion, from where the metal
     actually comes from) and p-values carry a Benjamini-Hochberg FDR correction across the 18 tests.
  3. IT TESTED THE WRONG CHANNEL. Joint production says the host's OUTPUT drags the companion out of the
     ground involuntarily: host output up -> companion supply up -> companion price DOWN. That is a claim
     about the host's QUANTITY. Correlating against the host's PRICE cannot identify it — host price is
     dominated by the common demand cycle, which pushes every metal the same way. So we now also run the
     test the theory actually implies (dlog companion price ~ dlog host production), and report that it
     finds nothing: only 4/17 even have the theory's negative sign and none is significant. The tilt is in
     fact significantly POSITIVE (sign test p=0.049) — which is not evidence against joint production so
     much as a sign that host output is procyclical and the cycle control is imperfect. Either way, the
     channel the theory names does not show up.

What survives: bismuth <- lead (partial r=0.68, p=0.001), a genuinely strong host link. And the honest
finding underneath — companion prices track the GENERAL commodity cycle, not their specific host.

Prices are now real USGS series (Data Series 140, constant 1998 US$) instead of trade unit values, which
the volatility retest showed track real prices at r=0.13. Coal and natural gas have no USGS series (DS-140
is nonfuel), so those hosts come from the World Bank Pink Sheet, deflated onto the same 1998 basis using
the deflator implied by USGS's own nominal/real pair. Public data; deterministic.
Run: python build_host_coupling.py
"""
import json, os, math, csv, collections
import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.abspath(__file__))
comp = json.load(open(os.path.join(ROOT, 'out', 'companionality.json'), encoding='utf8'))
CO = {r['label']: r for r in comp['rows']}
Y0, Y1 = 2000, 2023
MIN_N = 12

# ---- real USGS prices + world production ------------------------------------
P, W, NOM = collections.defaultdict(dict), collections.defaultdict(dict), collections.defaultdict(dict)
for r in csv.DictReader(open(os.path.join(ROOT, 'raw', 'usgs_hist', 'usgs_prices_slim.csv'), encoding='utf8')):
    y = int(r['year'])
    if r['uv_98']:
        P[r['commodity']][y] = float(r['uv_98'])
    if r['uv_nominal']:
        NOM[r['commodity']][y] = float(r['uv_nominal'])
    if r['world_production']:
        W[r['commodity']][y] = float(r['world_production'])

# USGS publishes each series in nominal AND constant-1998 dollars, so their ratio IS the deflator.
# Take the median across commodities per year — that lets us put Pink Sheet (nominal) on the same basis.
_d = collections.defaultdict(list)
for c in NOM:
    for y in NOM[c]:
        if y in P[c] and P[c][y] > 0:
            _d[y].append(NOM[c][y] / P[c][y])
DEFL = {y: float(np.median(v)) for y, v in _d.items() if len(v) >= 5}

# ---- Pink Sheet, for the two hosts USGS cannot supply (coal, natural gas) ----
import openpyxl
PINK = os.path.join(ROOT, 'raw', 'pink', 'pink.xlsx')
PCOLS = {'coal': 5, 'natural gas': 7}
_acc = {k: {} for k in PCOLS}
_wb = openpyxl.load_workbook(PINK, read_only=True, data_only=True)
for row in _wb['Monthly Prices'].iter_rows(min_row=7, values_only=True):
    d = row[0]
    if not d or 'M' not in str(d):
        continue
    try:
        yr = int(str(d)[:4])
    except ValueError:
        continue
    for k, j in PCOLS.items():
        v = row[j] if j < len(row) else None
        if isinstance(v, (int, float)):
            s = _acc[k].setdefault(yr, [0.0, 0]); s[0] += v; s[1] += 1
_wb.close()
for k, yrs in _acc.items():
    for y, s in yrs.items():
        if s[1] >= 6 and y in DEFL:
            P[k][y] = (s[0] / s[1]) / DEFL[y]      # nominal -> constant 1998 $, same basis as USGS

# ---- pairs: companion -> its production host --------------------------------
# ONE host per companion, PRE-SPECIFIED from where the metal actually comes from — not chosen by
# whichever correlates best. That matters: the old page reported the "best-matching host" out of two or
# three candidates, which is cherry-picking. Testing 18 companions against ~30 candidate hosts and keeping
# the winners would throw up roughly 1.5 false positives at 5% by chance alone — enough to manufacture the
# handful of "host-specific" metals it claimed. Secondary hosts are still computed, but flagged exploratory
# and kept out of the headline. 'q' is the USGS commodity whose WORLD PRODUCTION is the host output.
PAIRS = {
    'gallium':    {'host': 'aluminum',    'also': ['zinc'],          'q': 'aluminum',   'atlas': True},
    'germanium':  {'host': 'zinc',        'also': ['coal'],          'q': 'zinc',       'atlas': True},
    'cobalt':     {'host': 'copper',      'also': ['nickel'],        'q': 'copper',     'atlas': True},
    'vanadium':   {'host': 'iron-ore',    'also': [],                'q': 'iron-ore',   'atlas': True},
    'arsenic':    {'host': 'copper',      'also': ['lead', 'gold'],  'q': 'copper',     'atlas': True},
    'antimony':   {'host': 'lead',        'also': ['zinc', 'gold'],  'q': 'lead',       'atlas': True},
    'tantalum':   {'host': 'tin',         'also': [],                'q': 'tin',        'atlas': True},
    'rare-earths':{'host': 'iron-ore',    'also': [],                'q': 'iron-ore',   'atlas': True},
    'helium':     {'host': 'natural gas', 'also': [],                'q': None,         'atlas': True},
    'hafnium':    {'host': 'zirconium',   'also': [],                'q': 'zirconium',  'atlas': True},
    # classic by-products outside the atlas's 32, included because they are the literature's own test cases
    # (zinc->germanium, zinc->cadmium, lead->selenium, lead->bismuth, copper->molybdenum) and they widen a
    # very thin sample. Flagged so the atlas's own materials stay readable.
    'indium':     {'host': 'zinc',        'also': [],                'q': 'zinc',       'atlas': False},
    'cadmium':    {'host': 'zinc',        'also': [],                'q': 'zinc',       'atlas': False},
    'selenium':   {'host': 'copper',      'also': [],                'q': 'copper',     'atlas': False},
    'tellurium':  {'host': 'copper',      'also': [],                'q': 'copper',     'atlas': False},
    'rhenium':    {'host': 'molybdenum',  'also': [],                'q': 'molybdenum', 'atlas': False},
    'bismuth':    {'host': 'lead',        'also': [],                'q': 'lead',       'atlas': False},
    'silver':     {'host': 'lead',        'also': ['copper'],        'q': 'lead',       'atlas': False},
    'molybdenum': {'host': 'copper',      'also': [],                'q': 'copper',     'atlas': False},
}
TITLE = {'rare-earths': 'Rare earths / magnets', 'iron-ore': 'iron ore', 'aluminum': 'aluminium'}
# Palladium is deliberately absent: USGS publishes ONE aggregate platinum-group series, so correlating
# palladium against platinum would correlate a series with itself. The old page's palladium result came
# from trade unit values against a Pink Sheet platinum price; we would rather drop the pair than fake it.
DROPPED = [{'label': 'palladium', 'why': 'USGS publishes a single aggregate platinum-group price series, so '
                                         'palladium vs platinum would be a series against itself'}]

BASE = ['aluminum', 'copper', 'lead', 'nickel', 'tin', 'zinc']


def dlog(series):
    ys = sorted(y for y in series if Y0 <= y <= Y1)
    return {b: math.log(series[b] / series[a]) for a, b in zip(ys, ys[1:])
            if b == a + 1 and series[a] > 0 and series[b] > 0}


_bd = [dlog(P[m]) for m in BASE]
CYCLE = {}
for y in range(Y0, Y1 + 1):
    v = [d[y] for d in _bd if y in d]
    if len(v) >= 4:
        CYCLE[y] = sum(v) / len(v)


def partial_corr(x, y, z):
    """corr(x, y) with z regressed out of BOTH — the valid control. NOT r_xy - r_xz, which is what the
    first version of this page did and which is not a control at all."""
    def resid(a, b):
        A = np.column_stack([np.ones(len(b)), b])
        return np.asarray(a, float) - A @ np.linalg.lstsq(A, np.asarray(a, float), rcond=None)[0]
    rx, ry = resid(x, z), resid(y, z)
    r, _ = stats.pearsonr(rx, ry)
    n, df = len(x), len(x) - 3
    t = r * math.sqrt(df / max(1e-9, 1 - r * r))
    p = 2 * (1 - stats.t.cdf(abs(t), df))
    # Fisher z 95% CI
    zf = 0.5 * math.log((1 + r) / (1 - r)) if abs(r) < 0.999 else 0.0
    se = 1 / math.sqrt(max(1, n - 4))
    lo, hi = (math.tanh(zf - 1.96 * se), math.tanh(zf + 1.96 * se))
    return round(float(r), 2), round(float(p), 4), n, round(lo, 2), round(hi, 2)


def _pair(cd, h):
    hd = dlog(P.get(h, {}))
    yrs = sorted(set(cd) & set(hd) & set(CYCLE))
    if len(yrs) < MIN_N:
        return None
    x = [cd[y] for y in yrs]; yy = [hd[y] for y in yrs]; z = [CYCLE[y] for y in yrs]
    raw, _ = stats.pearsonr(x, yy)
    pr, p, n, lo, hi = partial_corr(x, yy, z)
    return {'host': TITLE.get(h, h), 'raw_r': round(float(raw), 2), 'partial_r': pr,
            'p': p, 'n': n, 'ci_lo': lo, 'ci_hi': hi}


rows = []
for lab, cfg in PAIRS.items():
    cd = dlog(P.get(lab, {}))
    if not cd:
        continue
    pri = _pair(cd, cfg['host'])
    if not pri:
        continue
    co = CO.get(lab, {})
    rows.append({
        'label': lab, 'title': co.get('title', TITLE.get(lab, lab.replace('-', ' ').title())),
        'atlas_material': cfg['atlas'], 'companionality_pct': co.get('companionality_pct'),
        'best_host': pri['host'],           # pre-specified, NOT selected on the outcome
        'best_raw': pri['raw_r'], 'best_partial': pri['partial_r'], 'best_p': pri['p'],
        'ci_lo': pri['ci_lo'], 'ci_hi': pri['ci_hi'], 'n': pri['n'],
        'secondary': [s for s in (_pair(cd, h) for h in cfg['also']) if s],
    })

# Benjamini-Hochberg FDR across the 18 pre-specified tests. Eighteen tests at 5% expect ~1 false
# positive; without this correction a lone "survivor" is exactly what noise looks like.
_ord = sorted(range(len(rows)), key=lambda i: rows[i]['best_p'])
_m = len(rows)
_thr = 0.0
for _k, _i in enumerate(_ord, start=1):
    if rows[_i]['best_p'] <= 0.05 * _k / _m:
        _thr = 0.05 * _k / _m
for r in rows:
    r['host_specific'] = bool(r['best_p'] <= _thr) if _thr else False
    r['survives_fdr'] = r['host_specific']
    r['nominally_sig'] = bool(r['best_p'] < 0.05)

# ---- the test the theory actually implies: host OUTPUT -> companion price ----
def quantity_test():
    out = []
    for lab, cfg in PAIRS.items():
        h = cfg['q']
        if not h:
            continue
        cd, qd = dlog(P.get(lab, {})), dlog(W.get(h, {}))
        yrs = sorted(set(cd) & set(qd) & set(CYCLE))
        if len(yrs) < MIN_N:
            continue
        y = np.array([cd[t] for t in yrs])
        X = np.column_stack([np.ones(len(yrs)), [qd[t] for t in yrs], [CYCLE[t] for t in yrs]])
        XtXi = np.linalg.inv(X.T @ X)
        b = XtXi @ X.T @ y
        e = y - X @ b
        hlev = np.diag(X @ XtXi @ X.T)
        se = np.sqrt(np.diag(XtXi @ (X.T @ np.diag(e ** 2 / (1 - hlev) ** 2) @ X) @ XtXi))
        t = b / se
        p = 2 * (1 - stats.t.cdf(np.abs(t), len(yrs) - 3))
        out.append({'label': lab, 'title': TITLE.get(lab, lab.title()), 'host': TITLE.get(h, h),
                    'beta_host_output': round(float(b[1]), 2), 'p': round(float(p[1]), 3),
                    'beta_cycle': round(float(b[2]), 2), 'p_cycle': round(float(p[2]), 3),
                    'n': len(yrs), 'atlas_material': cfg['atlas']})
    return out


QT = quantity_test()
q_neg = [q for q in QT if q['beta_host_output'] < 0]
q_sig = [q for q in QT if q['p'] < 0.05]
q_sign_p = float(stats.binomtest(len(q_neg), len(QT), 0.5).pvalue) if QT else None
cyc_sig = [q for q in QT if q['p_cycle'] < 0.05]

mean_raw = round(float(np.mean([r['best_raw'] for r in rows])), 2)
mean_partial = round(float(np.mean([r['best_partial'] for r in rows])), 2)
spec = [r for r in rows if r['host_specific']]
_n = int(np.median([r['n'] for r in rows]))
_crit = stats.t.ppf(0.975, _n - 3)
crit_r = round(float(_crit / math.sqrt(_n - 3 + _crit ** 2)), 2)

rows.sort(key=lambda r: -abs(r['best_partial']))
out = {
    'generated': comp.get('generated'),
    'window': f'{Y0}-{Y1}',
    'n': len(rows), 'n_atlas': sum(1 for r in rows if r['atlas_material']),
    'mean_raw_corr': mean_raw,
    'mean_partial_corr': mean_partial,
    'n_host_specific': len(spec),
    'host_specific_names': [r['title'] for r in spec],
    'n_nominally_sig': sum(1 for r in rows if r['nominally_sig']),
    'nominally_sig_names': [r['title'] for r in rows if r['nominally_sig']],
    'fdr_note': 'Hosts are PRE-SPECIFIED (one per companion, from where the metal actually comes from), '
                'not chosen by which correlates best — the old page reported the best-matching host of two '
                'or three, which is cherry-picking. p-values carry a Benjamini-Hochberg FDR correction '
                'across the 18 tests: at 5% across 18 tests you expect about one false positive, so an '
                'uncorrected lone survivor is exactly what noise looks like.',
    'critical_r': crit_r, 'median_n': _n,
    'quantity_test': sorted(QT, key=lambda q: q['beta_host_output']),
    'q_n_negative': len(q_neg), 'q_n_total': len(QT), 'q_n_significant': len(q_sig),
    'q_sign_test_p': round(q_sign_p, 3) if q_sign_p else None,
    'q_mean_beta': round(float(np.mean([q['beta_host_output'] for q in QT])), 2) if QT else None,
    'q_cycle_significant': [q['title'] for q in cyc_sig],
    'dropped': DROPPED,
    'rows': rows,
    'source': 'USGS Historical Statistics (Data Series 140), real prices in constant 1998 US$; World Bank '
              'Pink Sheet for coal and natural gas, deflated onto the same basis.',
    'retraction': 'The first version of this page reported a mean best-host correlation of ~0.29 and named '
                  'palladium, gallium, germanium, helium and rare earths as beating the control. That is '
                  'withdrawn. The control (r_host - r_base) was not a control — subtracting two '
                  'correlations is not residualisation. With a valid PARTIAL correlation the mean falls '
                  f'from {mean_raw} to {mean_partial}, and only {len(spec)} pair clears significance. The '
                  f'0.29 was never significant either: at n~{_n} the 5% critical correlation is {crit_r}. '
                  'And the test targeted the wrong channel: joint production is a claim about the host\'s '
                  'OUTPUT, not its price. Run on output, it finds nothing.',
    'verdict': 'Companion prices track the GENERAL commodity cycle, not their specific host. Once the '
               'cycle is properly removed, host coupling is indistinguishable from zero for every pair but '
               'bismuth<-lead. The "host decides the direction" mechanism is not visible in annual data. '
               'The specific EPISODES behind it remain real (gallium/germanium on 2023 export controls, '
               'cobalt on Indonesian nickel) — those are documented events, not artifacts. What is not '
               'supported is the general law.',
}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out', 'host_coupling.json'), 'w', encoding='utf8'),
          separators=(',', ':'))
print('wrote out/host_coupling.json')
print(f"  mean RAW corr     = {mean_raw}   <- what the old page reported (~0.29)")
print(f"  mean PARTIAL corr = {mean_partial}   <- valid control: the coupling vanishes")
print(f"  nominally significant (p<0.05, uncorrected): {out['n_nominally_sig']}/{len(rows)} -> {', '.join(out['nominally_sig_names']) or 'NONE'}")
print(f"  survives BH-FDR across {len(rows)} tests:        {len(spec)}/{len(rows)} -> {', '.join(out['host_specific_names']) or 'NONE'}")
print(f"  critical |r| at n~{_n} is {crit_r} — the old 0.29 was never significant")
print(f"  quantity test (theory: NEGATIVE): {len(q_neg)}/{len(QT)} negative, {len(q_sig)} significant, "
      f"sign-test p={out['q_sign_test_p']}, mean beta={out['q_mean_beta']}")
print(f"  companions that DO track the common cycle: {', '.join(out['q_cycle_significant']) or 'none'}")

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Does the companion follow its host? &mdash; a mechanism test that failed &middot; Critical Materials Atlas</title>
<meta name="description" content="Does a by-product metal's price track its host? Tested properly — real prices, a valid partial correlation, the host's output rather than its price — the coupling vanishes. Companion prices track the general commodity cycle, not their host. One pair survives: bismuth and lead.">
<meta property="og:title" content="Does a by-product metal's price track its host? Mostly, no.">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>
 .muted{color:#5a6b68;font-size:.86rem}
 .stat4{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin:1.2rem 0}
 @media(max-width:720px){.stat4{grid-template-columns:repeat(2,1fr)}}
 .stat{background:#fff;border:1px solid #e3e9e8;border-left:4px solid #0e7c74;border-radius:10px;padding:.8rem .9rem}
 .stat.dead{border-left-color:#c0392b}
 .stat .v{font-size:1.5rem;font-weight:800;color:#15323a;letter-spacing:-.02em}
 .stat .l{font-size:.76rem;color:#5a6b68;margin-top:.15rem;line-height:1.35}
 table.tidy{width:100%;border-collapse:collapse;font-size:.87rem;margin:.4rem 0}
 table.tidy th,table.tidy td{padding:.4rem .5rem;border-bottom:1px solid #eef1f0;text-align:left}
 table.tidy th.n,table.tidy td.n{text-align:right;font-variant-numeric:tabular-nums}
 .cbar{display:grid;grid-template-columns:150px 1fr 168px;align-items:center;gap:.6rem;margin:.28rem 0;font-size:.86rem}
 .cbar .nm{text-align:right;font-weight:600;color:#15323a}
 .cbar .track{position:relative;background:#eef3f2;border-radius:5px;height:20px}
 .cbar .zero{position:absolute;left:50%;top:0;bottom:0;width:1px;background:#c9d2d0}
 .cbar .fill{position:absolute;top:0;bottom:0;border-radius:4px}
 .cbar .meta{color:#5a6b68;font-size:.78rem}
 .keyline{background:#f2f6f5;border:1px solid #d9e6e3;border-left:4px solid #0e7c74;border-radius:10px;padding:.9rem 1.1rem;margin:1.2rem 0}
 .keyline b{color:#0e7c74}
 .note{background:#f7f9f9;border:1px solid #e3e9e8;border-left:3px solid #b7c4c1;border-radius:8px;padding:.6rem .85rem;margin:1rem 0;font-size:.84rem;color:#5a6b68}
 .sig{font-weight:700;color:#0e7c74}.nsig{color:#a8b5b2}
</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="explorer">Explore</a><a href="value-chains">Value Chains</a><a href="analysis">Analysis</a><a href="reports">Reports</a><a href="method">Method</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method &middot; mechanism &middot; falsification</div>
  <h1>Does the companion follow its host?</h1>
  <p class="deck">The <a href="price-squeeze.html" style="color:#fff;text-decoration:underline">price test</a> claimed a by-product metal&rsquo;s direction is set by its host&rsquo;s cycle. That is a mechanism, and mechanisms can be checked. We checked it &mdash; properly this time &mdash; and it is <b>not there</b>. What companions actually track is the commodity cycle in general, not the metal they ride on. One pair survives.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout"><span id="lead"></span>
  <details class="howto"><summary>How the coupling is measured, and what was wrong before</summary>
  <p><b>Prices.</b> Real USGS series (Data Series 140, constant 1998 dollars) for both companion and host. The previous version used the atlas&rsquo;s trade unit values for the companion side &mdash; the same proxy the <a href="price-volatility.html">volatility retest</a> found tracks real price volatility at r=0.13. Coal and natural gas have no USGS series (DS-140 is nonfuel), so those two hosts come from the <b>World Bank Pink Sheet</b>, deflated onto the same 1998 basis using the deflator implied by USGS&rsquo;s own nominal/real pair.</p>
  <p><b>The control, done properly.</b> Everything in commodities co-moves, so a raw correlation is mostly the macro cycle. The old page handled this by computing corr(companion, host) &minus; corr(companion, base index) and calling the pair host-specific if the gap beat 0.1. <b>That is not a control.</b> Subtracting two correlations is not residualisation, has no sampling theory, and the 0.1 was arbitrary. The correct statistic is the <b>partial correlation</b>: regress the base-metals cycle out of <i>both</i> series, then correlate what is left. That is what this page now does.</p>
  <p><b>The channel, corrected.</b> Joint production says the host drags the companion out of the ground whether anyone wants it or not: host output up &rarr; companion supply up &rarr; companion price <i>down</i>. That is a claim about the host&rsquo;s <b>output</b>, not its price &mdash; and host price is dominated by the same demand cycle that lifts every metal at once, so a price-price correlation cannot identify it. We therefore also run the regression the theory implies, on host <b>production</b>.</p>
  <p class="howto-src"><b>Limits:</b> ~20 annual points per pair, so only large effects are visible. Palladium is dropped: USGS publishes one aggregate platinum-group price, so palladium against platinum would be a series against itself &mdash; the old page&rsquo;s palladium result came from trade unit values and we would rather drop the pair than fake it. Non-atlas by-products are included and flagged: they are the literature&rsquo;s own test cases and this sample is thin. Input: USGS DS-140 &times; Pink Sheet &rarr; <a href="out/host_coupling.json">host_coupling.json</a>.</p>
  </details></div>

  <div class="stat4" id="stats"></div>

  <div class="keyline" id="keyline"></div>

  <h2 style="margin:1.6rem 0 .3rem">Coupling, before and after a real control</h2>
  <p class="muted" style="margin-top:0">Grey bar = the <b>raw</b> correlation with the best-matching host &mdash; what the old page reported. Coloured bar = the <b>partial</b> correlation, after the common commodity cycle is regressed out of both series. The gap between them is the macro cycle, which the old method credited to the host.</p>
  <div id="bars"></div>

  <h2 style="margin:1.6rem 0 .3rem">Every pair, with honest intervals</h2>
  <table class="tidy" id="tab"><thead><tr><th>Companion</th><th>best host</th><th class="n">raw r</th><th class="n">partial r</th><th class="n">95% CI</th><th class="n">p</th><th>verdict</th></tr></thead><tbody></tbody></table>
  <p class="muted">&#9733; = one of the atlas&rsquo;s own 32 materials; the rest are classic by-products included because the sample is thin and they are the pairs the literature itself tests.</p>

  <h2 style="margin:1.8rem 0 .3rem">The test the theory actually implies</h2>
  <p>If a companion is dragged out of the ground by its host, then when the <b>host produces more</b>, the companion&rsquo;s price should <b>fall</b>. That is the joint-production channel, and it is a statement about tonnes, not dollars. So: regress each companion&rsquo;s annual price change on its host&rsquo;s annual <b>output</b> change, controlling for the commodity cycle. The theory predicts a negative coefficient.</p>
  <table class="tidy" id="qtab"><thead><tr><th>Companion</th><th>host output</th><th class="n">&beta; host output</th><th class="n">p</th><th class="n">&beta; cycle</th><th class="n">p</th></tr></thead><tbody></tbody></table>
  <div class="keyline" id="qkey"></div>

  <div class="note">An earlier version of this page reported a mean best-host coupling of ~0.29 and named five metals as beating the control. That finding is withdrawn &mdash; the control was not a valid control, the result was never significant, and it tested the host&rsquo;s price where the theory is about the host&rsquo;s output. This page is the corrected version; the full record is on <a href="challenge.html">the error record</a>.</div>

  <h2 style="margin:1.8rem 0 .3rem">What this does and does not overturn</h2>
  <p><b>The episodes are real.</b> Gallium and germanium did spike when China restricted exports in 2023. Cobalt did crash while Indonesian nickel flooded the market. Those are documented events, not statistical artifacts, and nothing here touches them.</p>
  <p><b>The general law is not supported.</b> &ldquo;Companion prices systematically track their host&rsquo;s cycle&rdquo; is a much stronger claim than &ldquo;in these episodes, host and policy shocks dominated&rdquo; &mdash; and it is the strong version this page was built to test. It fails: with a valid control the coupling is indistinguishable from zero everywhere but bismuth, and the channel the theory names shows nothing at all. So the <a href="price-squeeze.html">price test&rsquo;s</a> &ldquo;the host decides the direction&rdquo; is narrowed to the episodic claim its evidence supports.</p>
  <p><b>Why it might still be true and invisible.</b> Honestly stated: host output moves a few percent a year while companion prices swing thirty to fifty. A structural multi-year surge &mdash; Indonesia&rsquo;s nickel build-out &mdash; is not a year-on-year wiggle, and an annual log-return test is poorly shaped to catch it. Absence of evidence here is not proof of absence. But the claim was ours to prove, and we have not.</p>
  <p><b>Why not a VAR, or GARCH, or a spillover index?</b> Because they cannot be run honestly on this data. The literature&rsquo;s frontier for main/by-product linkage &mdash; Toda&ndash;Yamamoto causality, cointegration, TVP-VAR, multiscale nonlinear Granger &mdash; needs monthly or daily series with hundreds of observations. The minor metals have no open high-frequency prices at all; USGS is annual, and twenty points will not support a VAR. Fitting one anyway would produce output, not evidence. The binding constraint here is data, not method, and we would rather say so than dress twenty points in a technique that implies we have two thousand.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="explorer">Explore</a><br><a href="value-chains">Value Chains</a><br><a href="analysis">Analysis</a><br><a href="reports">Reports</a><br><a href="method">Method</a></div>
  <div><h4>Sources</h4>USGS Historical Statistics (DS-140), constant 1998 US$ · World Bank Pink Sheet (coal, gas)</div>
  <div class="fineprint">~20 annual points per pair: only large effects are visible, and the 5% critical correlation is about 0.46. A null here is weak evidence of absence — but it is not evidence of presence, which is what this page originally claimed.</div>
</div></footer>
<script>
fetch('out/host_coupling.json').then(r=>r.json()).then(S=>{
  const f=v=>(v>0?'+':'')+v.toFixed(2);
  document.getElementById('lead').innerHTML='<b>Result:</b> after regressing out the commodity cycle the way it should have been done, the average companion&ndash;host coupling is <b>'+S.mean_partial_corr+'</b> &mdash; nothing. Of '+S.n+' pairs, <b>'+S.n_host_specific+'</b> clears significance: '+(S.host_specific_names.join(', ')||'none')+'. A raw coupling is <b>the macro cycle wearing a host costume</b>: everything in commodities rises and falls together, and only a proper partial correlation tells them apart. Running the test the theory actually implies &mdash; does the host&rsquo;s <i>output</i> push the companion&rsquo;s price down? &mdash; finds <b>'+S.q_n_significant+' of '+S.q_n_total+'</b> significant, and only '+S.q_n_negative+'/'+S.q_n_total+' even have the right sign.';

  const stats=[
    {v:S.mean_raw_corr,l:'raw mean coupling with the host — almost all of it is the common commodity cycle',c:''},
    {v:S.mean_partial_corr,l:'the same thing once the cycle is <b>properly</b> removed — the coupling is gone',c:''},
    {v:S.n_host_specific+' / '+S.n,l:'pairs where the host link survives a real control',c:''},
    {v:'|r| '+S.critical_r,l:'the correlation you would need at n≈'+S.median_n+' before claiming anything at all',c:''},
  ];
  document.getElementById('stats').innerHTML=stats.map(s=>'<div class="stat'+s.c+'"><div class="v">'+s.v+'</div><div class="l">'+s.l+'</div></div>').join('');

  const surv=S.rows.filter(r=>r.host_specific);
  document.getElementById('keyline').innerHTML='<b>What actually survives:</b> '+(surv.length?surv.map(r=>'<b>'+r.title.toLowerCase()+' &larr; '+r.best_host+'</b> (partial r='+r.best_partial+', p='+r.best_p+')').join(', '):'nothing')+'. That is a real, strong host link and worth keeping &mdash; lead and bismuth genuinely move together beyond the cycle, and it is one of the pairs the published literature independently identifies. But one surviving pair out of '+S.n+' is not the mechanism the price test claimed; it is an exception. The rest of the companions are not following their hosts. They are following <b>everything</b>, along with everything else.';

  const mk=r=>{
    const pw=Math.abs(r.best_partial)*50, pl=r.best_partial>=0?50:50-pw;
    const rw=Math.abs(r.best_raw)*50, rl=r.best_raw>=0?50:50-rw;
    const col=r.host_specific?'#0e7c74':'#c9d2d0';
    return '<div class="cbar"><div class="nm">'+(r.atlas_material?'★ ':'')+r.title+'</div>'+
      '<div class="track"><div class="zero"></div>'+
      '<div class="fill" style="left:'+rl+'%;width:'+rw+'%;background:#dde5e3" title="raw r='+r.best_raw+' (mostly the macro cycle)"></div>'+
      '<div class="fill" style="left:'+pl+'%;width:'+pw+'%;background:'+col+';opacity:.95" title="partial r='+r.best_partial+'"></div></div>'+
      '<div class="meta">'+r.best_raw.toFixed(2)+' &rarr; <b>'+r.best_partial.toFixed(2)+'</b> vs '+r.best_host+(r.host_specific?' <b style="color:#0e7c74">·real</b>':'')+'</div></div>';
  };
  document.getElementById('bars').innerHTML=S.rows.map(mk).join('');

  const tb=document.querySelector('#tab tbody');
  S.rows.forEach(r=>{
    const v=r.host_specific?'<b style="color:#0e7c74">host link survives the control</b>':'not distinguishable from zero';
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+(r.atlas_material?'★ ':'')+r.title+'</b></td><td class="muted">'+r.best_host+'</td>'+
      '<td class="n nsig">'+r.best_raw.toFixed(2)+'</td>'+
      '<td class="n"><span class="'+(r.host_specific?'sig':'nsig')+'">'+r.best_partial.toFixed(2)+'</span></td>'+
      '<td class="n muted" style="font-size:.78rem">'+r.ci_lo.toFixed(2)+' … '+r.ci_hi.toFixed(2)+'</td>'+
      '<td class="n"><span class="'+(r.host_specific?'sig':'nsig')+'">'+r.best_p.toFixed(3)+'</span></td>'+
      '<td class="muted" style="font-size:.82rem">'+v+'</td>';
    tb.appendChild(tr);
  });

  const qb=document.querySelector('#qtab tbody');
  S.quantity_test.forEach(q=>{
    const good=q.beta_host_output<0;
    const tr=document.createElement('tr');
    tr.innerHTML='<td><b>'+(q.atlas_material?'★ ':'')+q.title+'</b></td><td class="muted">'+q.host+'</td>'+
      '<td class="n"><span style="color:'+(good?'#0e7c74':'#c0392b')+'">'+f(q.beta_host_output)+'</span></td>'+
      '<td class="n"><span class="'+(q.p<0.05?'sig':'nsig')+'">'+q.p.toFixed(3)+'</span></td>'+
      '<td class="n muted">'+f(q.beta_cycle)+'</td>'+
      '<td class="n"><span class="'+(q.p_cycle<0.05?'sig':'nsig')+'">'+q.p_cycle.toFixed(3)+'</span></td>';
    qb.appendChild(tr);
  });
  document.getElementById('qkey').innerHTML='<b>Nothing.</b> The theory predicts a negative coefficient on host output; only <b>'+S.q_n_negative+' of '+S.q_n_total+'</b> are even negative (a coin flip would give '+(S.q_n_total/2).toFixed(1)+'), <b>none</b> is significant, and the mean coefficient is '+f(S.q_mean_beta)+' &mdash; the <i>wrong sign</i>, and the positive tilt is itself borderline significant (sign test p='+S.q_sign_test_p+'). We will not oversell that: a positive tilt is most likely just host output being <b>procyclical</b> &mdash; booms lift output and prices together &mdash; which means our cycle control is imperfect rather than that joint production runs backwards. The honest reading is narrower: <b>the channel the theory names does not show up.</b> Meanwhile the <b>commodity cycle</b> is significant for '+S.q_cycle_significant.join(', ')+'. That is the finding underneath all of this: these metals are not being pushed around by their hosts&rsquo; output. They are being pushed around by the same thing that pushes every commodity at once.';
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'host-coupling.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('wrote host-coupling.html')
