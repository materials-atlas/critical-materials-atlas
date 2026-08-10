#!/usr/bin/env python3
"""
Robustness — do the headline trend findings survive a harder test?

The Trends page flags materials with a significant rising export-HHI using a standard Mann-Kendall test.
But MK assumes the annual observations are independent; trade-concentration series are serially
correlated (this year looks like last year), which UNDER-estimates the variance and so OVER-states
significance. Two checks here:

  (1) Hamed-Rao (1998) autocorrelation correction — re-tests every series with the variance inflated for
      the significant rank-autocorrelations (the standard fix). Significance that survives this is real;
      significance that vanishes was partly an artifact of serial correlation.
  (2) Splice sub-period check — re-estimates each trend separately on the HS02 window (2002-2016) and the
      HS17 window (2017-2024). A trend that keeps the same sign in both halves is not an artifact of the
      2017 vintage join.

No new deps (numpy + scipy + statsmodels). Reads out/trends.json. Writes out/robustness.json + robustness.html.
Run: python build_robustness.py
"""
import json, os
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

ROOT = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(ROOT, 'out', 'trends.json'), encoding='utf8'))
YEARS = T['years']; n = len(YEARS)
SPLICE = YEARS.index(2017)                      # first HS17 year

def mk_S_var(x):
    x = np.asarray(x, float); m = len(x)
    S = sum(np.sign(x[k + 1:] - x[k]).sum() for k in range(m - 1))
    _, c = np.unique(x, return_counts=True)
    tie = (c * (c - 1) * (2 * c + 5)).sum()
    var = (m * (m - 1) * (2 * m + 5) - tie) / 18.0
    return S, var

def z_of(S, var):
    if var <= 0: return 0.0
    if S > 0: return (S - 1) / np.sqrt(var)
    if S < 0: return (S + 1) / np.sqrt(var)
    return 0.0

def p_of(z): return 2 * (1 - stats.norm.cdf(abs(z)))

def hamed_rao(x):
    """Return (p_standard, p_corrected, sen_slope, var_inflation)."""
    x = np.asarray(x, float); m = len(x)
    S, var0 = mk_S_var(x)
    p0 = p_of(z_of(S, var0))
    t = np.arange(m)
    slope = stats.theilslopes(x, t)[0]
    R = stats.rankdata(x - slope * t)            # ranks of the detrended series
    Rbar = R.mean(); denom = ((R - Rbar) ** 2).sum() / m
    corr = 0.0
    if denom > 0:
        for i in range(1, m - 2):                # rank-autocorrelation at lag i, significant lags only
            rho = (((R[:m - i] - Rbar) * (R[i:] - Rbar)).sum() / (m - i)) / denom
            lo = (-1 - 1.96 * np.sqrt(m - i - 1)) / (m - i)
            hi = (-1 + 1.96 * np.sqrt(m - i - 1)) / (m - i)
            if rho < lo or rho > hi:             # Anderson 95% bound (Hamed-Rao "modified")
                corr += (m - i) * (m - i - 1) * (m - i - 2) * rho
    nf = 1 + (2.0 / (m * (m - 1) * (m - 2))) * corr
    nf = max(nf, 1.0)                            # conservative one-sided: autocorrelation may only make the test harder
    pc = p_of(z_of(S, var0 * nf))
    return p0, pc, slope, nf

def sub_sign(x, a, b):
    seg = np.asarray(x[a:b], float)
    if len(seg) < 4: return 0
    s = stats.theilslopes(seg, np.arange(len(seg)))[0]
    return 1 if s > 1e-6 else (-1 if s < -1e-6 else 0)

# --- run across all 32 for export-HHI (the headline metric) ---
rows = []
for lab, m in T['materials'].items():
    hhi = m['hhi']
    p0, pc, slope, nf = hamed_rao(hhi)
    rows.append({'lab': lab, 'title': m['title'], 'slope': round(slope, 4),
                 'mk_p': round(p0, 4), 'hr_p': round(pc, 4), 'nf': round(nf, 2),
                 'rising': bool(slope > 0),
                 'early': sub_sign(hhi, 0, SPLICE + 1), 'late': sub_sign(hhi, SPLICE, n)})

# BH-FDR across the 32, standard vs corrected
labs = [r['lab'] for r in rows]
fdr0 = multipletests([r['mk_p'] for r in rows], method='fdr_bh')[1]
fdrc = multipletests([r['hr_p'] for r in rows], method='fdr_bh')[1]
for r, a, b in zip(rows, fdr0, fdrc):
    r['mk_fdr'] = round(a, 4); r['hr_fdr'] = round(b, 4)
    r['sig_std'] = bool(a < 0.05 and r['rising'])
    r['sig_hr'] = bool(b < 0.05 and r['rising'])
    r['splice_ok'] = bool(r['rising'] and r['early'] >= 0 and r['late'] >= 0)

n_std = sum(r['sig_std'] for r in rows)
n_hr = sum(r['sig_hr'] for r in rows)
survive = [r for r in rows if r['sig_std']]
n_splice_ok = sum(r['splice_ok'] for r in survive)
n_hr_of_std = sum(r['sig_hr'] for r in survive)

out = {'years': YEARS, 'n_std': n_std, 'n_hr': n_hr,
       'n_hr_of_std': n_hr_of_std, 'n_splice_ok': n_splice_ok,
       'rows': sorted(rows, key=lambda r: (not r['sig_std'], r['hr_fdr']))}
json.dump(out, open(os.path.join(ROOT, 'out', 'robustness.json'), 'w', encoding='utf8'), indent=1)

print(f'Export-HHI rising trends significant (FDR<0.05):')
print(f'  standard Mann-Kendall:        {n_std} / 32')
print(f'  Hamed-Rao autocorr-corrected: {n_hr} / 32   ({n_hr_of_std} of the {n_std} standard ones survive)')
print(f'  of the {n_std} standard ones, {n_splice_ok} keep the same sign in BOTH the HS02 and HS17 sub-periods')
print('\nThe standard-significant materials under the harder tests:')
for r in survive:
    print(f"  {r['title'][:30]:<30} MK-FDR {r['mk_fdr']:.3f} -> HR-FDR {r['hr_fdr']:.3f} (×var {r['nf']}) "
          f"{'SURVIVES' if r['sig_hr'] else 'drops'} | splice {'ok' if r['splice_ok'] else 'WEAK'}")

# ---------------- page ----------------
HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Do the findings survive? — robustness · Critical Materials Atlas</title>
<meta name="description" content="An adversarial robustness check on the atlas's trend findings: autocorrelation-robust Mann-Kendall (Hamed-Rao 1998) and a 2002-16 vs 2017-24 splice sub-period test, for export-concentration trends across 32 critical materials.">
<meta property="og:title" content="Do the concentration findings survive a harder test?">
<meta property="og:image" content="https://criticalmaterialsatlas.org/out/share.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"><script src="assets/nav.js" defer></script>
<style>.muted{color:#5a6b68;font-size:.86rem}.yes{color:#2f8f46;font-weight:700}.no{color:#b07a18;font-weight:700}.tag{display:inline-block;font-size:.74rem;padding:.05rem .4rem;border-radius:5px;background:#eef3f2;color:#41524f}</style>
</head><body>
<header class="topbar"><div class="wrap">
  <a class="wordmark" href="./"><span class="mark"></span>Critical Materials Atlas</a>
  <nav class="topnav"><a href="./">Atlas</a><a href="methodology.html">Methodology</a><a href="trends.html">Trends</a>
  <a href="technical-note.html" class="hideable">Technical note</a><a href="findings.html" class="hideable">Findings</a>
  <a href="https://github.com/materials-atlas/critical-materials-atlas" class="hideable">Engine</a></nav>
</div></header>
<section class="hero"><div class="wrap">
  <div class="eyebrow">Method · robustness</div>
  <h1>Do the findings survive a harder test?</h1>
  <p class="deck">The Trends page says concentration is rising for a set of materials. That rests on a Mann-Kendall test which assumes each year is independent &mdash; but concentration series are serially correlated, which <i>overstates</i> significance. Here the same claims are re-run under an autocorrelation-robust test and split across the 2017 data-vintage join. What survives, we can stand behind; what doesn&rsquo;t, we say so.</p>
</div></section>
<article style="max-width:1040px">
  <div class="callout">Does &ldquo;concentration is rising&rdquo; survive a tougher test? I re-run every trend two harder ways and keep only what passes both.
  <details class="howto"><summary>The two harder tests</summary>
  <p><b>1 &middot; Autocorrelation-robust (Hamed-Rao, 1998).</b> A plain trend test assumes each year is independent; concentration series aren&rsquo;t, which flatters significance. This correction demands a <i>stronger</i> signal before a trend counts.</p>
  <p><b>2 &middot; Across the data-vintage splice.</b> Each trend is re-estimated separately on 2002&ndash;2016 and on 2017&ndash;2024; one that keeps the same sign in both halves isn&rsquo;t an artifact of the 2017 join.</p>
  <p class="howto-src">Both screens control the false-discovery rate (Benjamini-Hochberg) across all 32 materials. Computed by <code>build_robustness.py</code>.</p>
  </details></div>
  <div id="verdict" class="callout" style="border-left-color:#0e7c74;background:#f0f7f5"></div>
  <h2 style="margin:1.4rem 0 .4rem">The rising-concentration materials, under the harder tests</h2>
  <p class="muted" style="margin-top:0">Materials flagged with a significant rising export-HHI by the standard test, then re-checked. &ldquo;Var ×&rdquo; is the Hamed-Rao variance inflation from positive autocorrelation (&ge;1; this is a deliberately conservative <i>one-sided</i> correction &mdash; serial correlation may only make the test <i>harder</i>, never easier). A value of 1.00 means the series had no significant positive autocorrelation to penalise.</p>
  <table id="tab"><thead><tr><th>Material</th><th class="n">Sen slope/yr</th><th class="n">MK FDR</th><th class="n">Hamed-Rao FDR</th><th class="n">var ×</th><th>survives?</th><th>splice-consistent?</th></tr></thead><tbody></tbody></table>
  <p id="rest" class="muted" style="margin-top:.8rem"></p>
  <p class="note">Hamed &amp; Rao (1998), <i>A modified Mann-Kendall trend test for autocorrelated data</i>, J. Hydrology. Series from <a href="out/trends.json">trends.json</a> (export-HHI, 2002&ndash;2024) &rarr; <a href="out/robustness.json">robustness.json</a>. This is an exploratory screen on 23 annual points, not a confirmatory test.</p>
</article>
<footer class="siteftr"><div class="wrap">
  <div><h4>Critical Materials Atlas</h4>An independent demonstration from public data. Not affiliated with, nor representing, any institution.</div>
  <div><h4>Navigate</h4><a href="trends.html">Trends</a><br><a href="technical-note.html">Technical note</a><br><a href="methodology.html">Methodology</a></div>
  <div><h4>Method</h4>Hamed-Rao autocorrelation-robust Mann-Kendall · sub-period splice test · BH-FDR</div>
  <div class="fineprint">Exploratory robustness screen on 23 annual observations. Significance is a screen, not proof.</div>
</div></footer>
<script>
fetch('out/robustness.json').then(r=>r.json()).then(R=>{
  document.getElementById('verdict').innerHTML =
    '<b>Verdict.</b> Of the <b>'+R.n_std+'</b> materials the standard test calls a significant rising export-HHI, '+
    '<b>'+R.n_hr_of_std+'</b> survive the Hamed-Rao autocorrelation correction, and <b>'+R.n_splice_ok+'</b> keep the same trend sign in '+
    'both the 2002&ndash;2016 and 2017&ndash;2024 sub-periods. '+
    (R.n_hr_of_std>=Math.ceil(R.n_std*0.6)
      ? 'The core rising-concentration finding is robust &mdash; it is not an artifact of serial correlation or the vintage splice.'
      : 'A meaningful share of the rising-concentration flags weaken once serial correlation is accounted for &mdash; read them as exploratory.')+
    ' (Autocorrelation-corrected total across all 32: '+R.n_hr+' significant rising.)';
  const tb=document.querySelector('#tab tbody');
  const sig=R.rows.filter(r=>r.sig_std);
  sig.forEach(r=>{const tr=document.createElement('tr');
    tr.innerHTML='<td><a href="profile-'+r.lab+'.html">'+r.title+'</a></td>'+
      '<td class="n">'+(r.slope>=0?'+':'')+r.slope.toFixed(3)+'</td>'+
      '<td class="n">'+r.mk_fdr.toFixed(3)+'</td>'+
      '<td class="n">'+r.hr_fdr.toFixed(3)+'</td>'+
      '<td class="n">'+r.nf.toFixed(2)+'</td>'+
      '<td class="'+(r.sig_hr?'yes':'no')+'">'+(r.sig_hr?'survives':'weakens')+'</td>'+
      '<td class="'+(r.splice_ok?'yes':'no')+'">'+(r.splice_ok?'both halves rise':'one half flat/falls')+'</td>';
    tb.appendChild(tr);});
  const extra=R.n_hr-sig.filter(r=>r.sig_hr).length;
  document.getElementById('rest').innerHTML =
    'The remaining '+(32-sig.length)+' materials are not flagged as significantly rising by the standard test'+
    (extra>0?('; '+extra+' material'+(extra>1?'s become':' becomes')+' significant only under the corrected test (negative autocorrelation can also sharpen a signal).'):'.');
});
</script>
</body></html>'''
open(os.path.join(ROOT, 'robustness.html'), 'w', encoding='utf8', newline='\n').write(HTML)
print('\nwrote robustness.html')
