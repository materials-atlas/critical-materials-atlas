#!/usr/bin/env python3
"""
Trend re-test - do the rising-concentration findings survive a harder test?

The Trends page flags materials with a significant rising export-HHI using a standard Mann-Kendall test.
But MK assumes the annual observations are independent; trade-concentration series are serially
correlated (this year looks like last year), which UNDER-estimates the variance and so OVER-states
significance. Two checks here:

  (1) Hamed-Rao (1998) autocorrelation correction - re-tests every series with the variance inflated for
      the significant rank-autocorrelations (the standard fix). Significance that survives this is real;
      significance that vanishes was partly an artifact of serial correlation.
  (2) Splice sub-period check - re-estimates each trend separately on the HS02 window (2002-2016) and the
      HS17 window (2017-2024). A trend that keeps the same sign in both halves is not an artifact of the
      2017 vintage join.

HISTORY, AND WHY THE FILE NAME. This test was first written as build_robustness.py -> out/robustness.json
(29 Jun 2026). On 14 Aug 2026 a different script took the same name and the same output file (a trade
cross-check), and robustness.html and limitations.html went on reading fields that no longer existed:
an empty table and "undefined of undefined" on the live site until 22 Nov 2026, found by an outside
review. Restored here under its own name with its own output. TWO BUILDERS NEVER SHARE AN OUTPUT FILE.

Reads out/trends.json. Writes out/trend_autocorr.json (read by robustness.html and limitations.html;
the pages themselves are hand-maintained and are not written here).
Run: python build_trend_autocorr.py
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

# --- run across every material in trends.json, for export-HHI (the headline metric) ---
rows = []
for lab, m in T['materials'].items():
    hhi = m['hhi']
    p0, pc, slope, nf = hamed_rao(hhi)
    rows.append({'lab': lab, 'title': m['title'], 'slope': round(slope, 4),
                 'mk_p': round(p0, 4), 'hr_p': round(pc, 4), 'nf': round(nf, 2),
                 'rising': bool(slope > 0),
                 'early': sub_sign(hhi, 0, SPLICE + 1), 'late': sub_sign(hhi, SPLICE, n)})

# BH-FDR across all materials, standard vs corrected
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

out = {'years': YEARS, 'n_all': len(rows), 'n_std': n_std, 'n_hr': n_hr,
       'n_hr_of_std': n_hr_of_std, 'n_splice_ok': n_splice_ok,
       'rows': sorted(rows, key=lambda r: (not r['sig_std'], r['hr_fdr']))}
json.dump(out, open(os.path.join(ROOT, 'out', 'trend_autocorr.json'), 'w', encoding='utf8', newline='\n'), indent=1)

print(f'Export-HHI rising trends significant (FDR<0.05):')
print(f'  standard Mann-Kendall:        {n_std} / {len(rows)}')
print(f'  Hamed-Rao autocorr-corrected: {n_hr} / {len(rows)}   ({n_hr_of_std} of the {n_std} standard ones survive)')
print(f'  of the {n_std} standard ones, {n_splice_ok} keep the same sign in BOTH the HS02 and HS17 sub-periods')
print('\nThe standard-significant materials under the harder tests:')
for r in survive:
    print(f"  {r['title'][:30]:<30} MK-FDR {r['mk_fdr']:.3f} -> HR-FDR {r['hr_fdr']:.3f} (var x {r['nf']}) "
          f"{'SURVIVES' if r['sig_hr'] else 'drops'} | splice {'ok' if r['splice_ok'] else 'WEAK'}")
