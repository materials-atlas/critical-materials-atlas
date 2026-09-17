# -*- coding: utf-8 -*-
"""Does recycling answer a price spike? Runs the test filed in PREREGISTRATION.md.

Committed before its first run. Everything it decides - the sample, the window, the two headline
specifications, the thresholds - is in the filing; this file only executes them and writes every
number to out/scrap_response.json.

Usage:  python scrap-response/response.py
"""
import json
import math
import os
import sys

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(HERE))
CUBE = os.path.join(ROOT, 'out', 'cube.parquet')
OUT = os.path.join(ROOT, 'out', 'scrap_response.json')

MIN_YEARS = 40                     # filed: a material needs 40 years of positive S and P
WINDOW = (1953, 2022)              # filed: after the Korean war's price controls
INVESTMENT = ['gold', 'silver', 'platinum']
RECESSIONS = [1974, 1975, 1980, 1981, 1982, 2008, 2009, 2020]
P50 = math.log(1.5)                # a 50% real price rise, in logs
# filed: the cross-material placebo pairs a material with the next one alphabetically that is not a
# by-product partner, so the placebo cannot ride on shared geology
BYPRODUCT = {
    'cobalt': {'copper', 'nickel'}, 'copper': {'cobalt', 'gold', 'silver', 'molybdenum'},
    'nickel': {'cobalt', 'platinum'}, 'platinum': {'nickel'},
    'silver': {'lead', 'zinc', 'copper', 'gold'}, 'lead': {'silver', 'zinc'},
    'zinc': {'lead', 'silver'}, 'gold': {'silver', 'copper'},
    'antimony': {'lead'}, 'tungsten': set(), 'tin': set(), 'magnesium': set(),
    'aluminium': set(), 'chromium': set(), 'mercury': set(), 'industrial_diamond': set(),
}


def series(con, measure, native_like=None):
    where = "measure = ? and country_iso3 = 'USA'"
    args = [CUBE, measure]
    if native_like:
        where += " and native_code like ?"
        args.append(native_like)
    sql = ("select material, period as year, max(value) as v from read_parquet(?) where " + where +
           " and value is not null group by 1, 2")
    return con.execute(sql, args).df()


def build(con):
    s = series(con, 'production_secondary').rename(columns={'v': 's'})
    p = series(con, 'unit_value_real98').rename(columns={'v': 'p'})
    c = series(con, 'apparent_consumption').rename(columns={'v': 'c'})
    pr = series(con, 'production', '%:Primary production').rename(columns={'v': 'prim'})

    both = s.merge(p, on=['material', 'year'])
    ok = both[(both.s > 0) & (both.p > 0)]
    keep = sorted(ok.groupby('material').size()[lambda x: x >= MIN_YEARS].index)

    d = (s.merge(p, on=['material', 'year'], how='outer')
          .merge(c, on=['material', 'year'], how='outer')
          .merge(pr, on=['material', 'year'], how='outer'))
    d = d[d.material.isin(keep)].sort_values(['material', 'year']).reset_index(drop=True)

    rows = []
    for mat, g in d.groupby('material'):
        g = g.set_index('year')
        years = range(int(g.index.min()), int(g.index.max()) + 1)
        for y in years:
            if y not in g.index:
                continue
            r = {'material': mat, 'year': y}
            cur = g.loc[y]
            r['s'], r['p'] = cur.get('s'), cur.get('p')
            r['c'], r['prim'] = cur.get('c'), cur.get('prim')
            # first differences, strictly consecutive years
            def dlog(col, y0, y1):
                if y0 in g.index and y1 in g.index:
                    a, b = g.loc[y0, col], g.loc[y1, col]
                    if pd.notna(a) and pd.notna(b) and a > 0 and b > 0:
                        return math.log(b / a)
                return np.nan
            r['ds'] = dlog('s', y - 1, y)
            r['dprim'] = dlog('prim', y - 1, y)
            for k in (0, 1, 2):
                r['dp%d' % k] = dlog('p', y - k - 1, y - k)
            r['dpf1'] = dlog('p', y, y + 1)          # placebo: next year's price move
            r['dpf2'] = dlog('p', y + 1, y + 2)
            # share of apparent consumption, in POINTS
            def share(yy):
                if yy in g.index:
                    sv, cv = g.loc[yy, 's'], g.loc[yy, 'c']
                    if pd.notna(sv) and pd.notna(cv) and cv > 0:
                        return 100.0 * sv / cv
                return np.nan
            r['sh'], r['sh_prev'] = share(y), share(y - 1)
            r['dsh'] = r['sh'] - r['sh_prev'] if pd.notna(r['sh']) and pd.notna(r['sh_prev']) else np.nan
            rows.append(r)
    panel = pd.DataFrame(rows)
    return panel[(panel.year >= WINDOW[0]) & (panel.year <= WINDOW[1])].reset_index(drop=True), keep


def fit(df, dv, regs, year_fe, cluster='material'):
    """One specification. Cluster by material with t on G-1 df, Driscoll-Kraay alongside."""
    formula = '%s ~ %s + C(material)%s' % (dv, ' + '.join(regs), ' + C(year)' if year_fe else '')
    d = df.dropna(subset=[dv] + regs).reset_index(drop=True)
    if d.empty or d[cluster].nunique() < 2:
        return None
    m = smf.ols(formula, d).fit(cov_type='cluster',
                               cov_kwds={'groups': pd.factorize(d[cluster])[0]}, use_t=True)
    tcode = (d['year'] - d['year'].min()).values
    try:
        dk = smf.ols(formula, d).fit(cov_type='hac-groupsum',
                                     cov_kwds={'time': tcode, 'maxlags': 2}, use_t=True)
    except Exception:
        dk = None
    cum = float(sum(m.params[r] for r in regs))
    # variance of the sum of the lag coefficients, from the clustered covariance
    idx = [list(m.params.index).index(r) for r in regs]
    v = float(np.sum(m.cov_params().values[np.ix_(idx, idx)]))
    se = math.sqrt(v) if v > 0 else float('nan')
    df_t = d[cluster].nunique() - 1
    t = cum / se if se == se and se > 0 else float('nan')
    from scipy import stats
    p = float(2 * stats.t.sf(abs(t), df_t)) if t == t else float('nan')
    crit = float(stats.t.ppf(0.975, df_t))
    out = {'dv': dv, 'regressors': regs, 'year_fe': bool(year_fe),
           'cumulative': round(cum, 4), 'se': round(se, 4), 't': round(t, 2), 'p': round(p, 4),
           'ci95': [round(cum - crit * se, 4), round(cum + crit * se, 4)],
           'per_lag': {r: round(float(m.params[r]), 4) for r in regs},
           'n': int(m.nobs), 'materials': int(d[cluster].nunique()), 'df_t': df_t,
           '_raw': {'cumulative': cum, 'p': p}}
    if dk is not None:
        v_dk = float(np.sum(dk.cov_params().values[np.ix_(idx, idx)]))
        se_dk = math.sqrt(v_dk) if v_dk > 0 else float('nan')
        out['se_driscoll_kraay'] = round(se_dk, 4)
        out['p_driscoll_kraay'] = round(float(2 * stats.t.sf(abs(cum / se_dk), df_t)), 4) if se_dk == se_dk else None
    return out


def points(fit_res):
    """The filed headline quantity: points of apparent consumption for a 50% real price rise."""
    if not fit_res:
        return None
    return round(fit_res['_raw']['cumulative'] * P50, 3)


def verdict(pts, p):
    """The filed table, read mechanically. No judgement here."""
    if p is None or p != p:
        return 'not_demonstrated'
    if p >= 0.05:
        return 'not_demonstrated'
    if pts < 0:
        return 'wrong_direction'
    if pts >= 1.0:
        return 'answers_at_scale'
    if pts >= 0.2:
        return 'responds_but_small'
    return 'measurable_and_negligible'


def main():
    con = duckdb.connect()
    panel, keep = build(con)
    lags = ['dp1', 'dp2']

    res = {'filing': 'scrap-response/PREREGISTRATION.md',
           'window': list(WINDOW), 'materials': keep,
           'n_material_years': int(len(panel)),
           'dropped_no_log': int(panel['ds'].isna().sum())}

    head = {}
    for fe in (True, False):
        k = 'with_year_effects' if fe else 'without_year_effects'
        share = fit(panel, 'dsh', lags, fe)
        elast = fit(panel, 'ds', lags, fe)
        head[k] = {'share_points_per_50pct': points(share), 'share': share, 'elasticity': elast,
                   'verdict': verdict(points(share), share['_raw']['p'] if share else None)}
    res['headline'] = head

    checks = {}
    checks['primary_supply'] = {k: fit(panel, 'dprim', lags, fe)
                                for k, fe in (('with_year_effects', True), ('without_year_effects', False))}
    checks['placebo_future_prices'] = {k: fit(panel, 'dsh', ['dpf1', 'dpf2'], fe)
                                       for k, fe in (('with_year_effects', True), ('without_year_effects', False))}

    pairs, mats = {}, keep
    for i, m in enumerate(mats):                       # next alphabetically that is not a by-product partner
        for j in range(1, len(mats)):
            cand = mats[(i + j) % len(mats)]
            if cand != m and cand not in BYPRODUCT.get(m, set()):
                pairs[m] = cand
                break
    px = panel.copy()
    pmap = panel.set_index(['material', 'year'])[['dp1', 'dp2']]
    px['dp1x'] = [pmap['dp1'].get((pairs.get(m), y), np.nan) for m, y in zip(px.material, px.year)]
    px['dp2x'] = [pmap['dp2'].get((pairs.get(m), y), np.nan) for m, y in zip(px.material, px.year)]
    checks['placebo_other_material'] = {'pairs': pairs,
                                        'with_year_effects': fit(px, 'dsh', ['dp1x', 'dp2x'], True)}

    loo = {}
    for m in keep:
        f = fit(panel[panel.material != m], 'dsh', lags, True)
        loo[m] = {'points_per_50pct': points(f), 'p': f['p'] if f else None} if f else None
    checks['leave_one_out'] = loo

    ex_inv = panel[~panel.material.isin(INVESTMENT)]
    checks['excluding_investment_metals'] = {k: fit(ex_inv, 'dsh', lags, fe)
                                             for k, fe in (('with_year_effects', True), ('without_year_effects', False))}
    checks['excluding_recessions'] = fit(panel[~panel.year.isin(RECESSIONS)], 'dsh', lags, True)
    checks['contemporaneous'] = fit(panel, 'dsh', ['dp0', 'dp1', 'dp2'], True)
    checks['window_1973_2022'] = fit(panel[panel.year >= 1973], 'dsh', lags, True)
    checks['window_1953_1990'] = fit(panel[panel.year <= 1990], 'dsh', lags, True)

    lv = panel.dropna(subset=['s', 'p']).copy()
    lv['logp'] = np.log(lv['p'])
    lv = lv[lv['p'] > 0]
    try:
        pm = smf.glm('s ~ logp + C(material) + C(year)', lv, family=sm.families.Poisson()).fit(
            cov_type='cluster', cov_kwds={'groups': pd.factorize(lv['material'])[0]})
        checks['poisson_levels_keeps_zeros'] = {'beta_logp': round(float(pm.params['logp']), 4),
                                                'p': round(float(pm.pvalues['logp']), 4),
                                                'n': int(pm.nobs),
                                                'zeros_kept': int((lv['s'] == 0).sum())}
    except Exception as e:
        checks['poisson_levels_keeps_zeros'] = {'error': '%s: %s' % (type(e).__name__, e)}

    shares = {}
    for m, g in panel.groupby('material'):
        g2 = g.dropna(subset=['sh'])
        if len(g2):
            shares[m] = {'median_secondary_share_pct': round(float(g2['sh'].median()), 1),
                         'latest_year': int(g2['year'].max()),
                         'latest_secondary_share_pct': round(float(g2.sort_values('year')['sh'].iloc[-1]), 1),
                         'years': int(len(g2))}
    res['secondary_share_by_material'] = shares
    res['checks'] = checks

    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items() if k != '_model'}
        if isinstance(o, list):
            return [strip(v) for v in o]
        return o

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(strip(res), f, indent=1, sort_keys=False, default=float)
    print('materials %d | material-years %d' % (len(keep), len(panel)))
    for k, v in head.items():
        print('%-22s %s points per +50%% price, p = %s -> %s'
              % (k, v['share_points_per_50pct'], v['share']['p'] if v['share'] else None, v['verdict']))
    print('wrote', OUT)


if __name__ == '__main__':
    sys.exit(main())
