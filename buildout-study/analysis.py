# -*- coding: utf-8 -*-
"""Grid equipment in world trade, 2012-2024: runs the tests filed in PREREGISTRATION.md.

Committed before its first run. Every choice it makes is in the filing (including the two details
fixed on 2026-09-18 before any estimate); this file executes them and writes every number to
out/buildout_study.json.

Estimation: y_ft = b1 (T x P1) + b2 (T x P2) + flow effects + year effects, on log unit value or
log tonnes. Flow effects are removed by the within transformation (Frisch-Waugh: every regressor,
including the year dummies, is demeaned within flow). Inference: wild cluster bootstrap by LINE,
null imposed, Webb six-point weights, 9,999 draws; exporter-clustered standard errors beside it.

Usage:  python buildout-study/analysis.py
"""
import csv
import collections
import zlib
import json
import math
import os
import sys

import numpy as np
import openpyxl
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import baci                                                    # the one door for BACI

OUT = os.path.join(ROOT, 'out', 'buildout_study.json')
PINK = os.path.join(ROOT, 'raw', 'pink', 'pink.xlsx')
YEARS = list(range(2012, 2025))
NOM = 'HS02'                                                   # filed: one nomenclature throughout
P1, P2 = (2021, 2022), (2023, 2024)
BASE_YEAR = 2019
MIN_VALUE_KUSD = 100.0                                         # filed: USD 100,000
UV_BAND = (0.1, 10.0)
DRAWS = 9999
SEED = 20260918
SHARE_GOES, SHARE_CU = 0.25, 0.25                              # filed, verified in literature.md

TRANSFORMERS = ['850421', '850422', '850423']
GOES = ['722511', '722611']
STEEL_CTL = ['722530', '722540', '722550', '722599']
CU_WIRE, CU_CATHODE = ['740811'], ['740311']
CAPITAL_CTL = ['842810', '842649', '847420', '847431', '851531', '851539']
CONTAMINATED = ['850152', '850153', '841370', '841480']
ALL = TRANSFORMERS + GOES + STEEL_CTL + CU_WIRE + CU_CATHODE + CAPITAL_CTL + CONTAMINATED
DESCRIBE_ONLY = ['848620', '848610']                           # filed: chip equipment, not tested
EU27 = {'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN',
        'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE'}
WEBB = np.array([-math.sqrt(1.5), -1.0, -math.sqrt(0.5), math.sqrt(0.5), 1.0, math.sqrt(1.5)])


# ----------------------------------------------------------------------------- inputs
def read_csv_series(name, col):
    with open(os.path.join(HERE, 'inputs', name), encoding='utf-8') as f:
        return {int(r['year']): float(r[col]) for r in csv.DictReader(f) if r[col]}


def copper_annual():
    wb = openpyxl.load_workbook(PINK, read_only=True, data_only=True)
    ws = wb['Monthly Prices']
    header = list(ws.iter_rows(min_row=5, max_row=5, values_only=True))[0]
    j = [i for i, n in enumerate(header) if n and str(n).strip() == 'Copper'][0]
    acc = collections.defaultdict(list)
    for row in ws.iter_rows(min_row=7, values_only=True):
        d = row[0]
        if d and 'M' in str(d) and isinstance(row[j], (int, float)):
            acc[int(str(d)[:4])].append(float(row[j]))
    wb.close()
    return {y: float(np.mean(v)) for y, v in acc.items() if len(v) >= 6}


def load_flows():
    iso = baci.countries().set_index('code')['iso3'].to_dict()
    frames = []
    for y in YEARS:
        t = baci.year(y, nom=NOM)
        t['k'] = t.k.astype(str).str.zfill(6)
        t = t[t.k.isin(ALL + DESCRIBE_ONLY)].copy()
        t['q'] = pd.to_numeric(t['q'], errors='coerce')
        t['v'] = pd.to_numeric(t['v'], errors='coerce')
        t['year'] = y
        frames.append(t[['year', 'i', 'j', 'k', 'v', 'q']])
    d = pd.concat(frames, ignore_index=True)
    d['exp'] = d.i.astype(str).map(iso).fillna(d.i.astype(str))
    d['imp'] = d.j.astype(str).map(iso).fillna(d.j.astype(str))
    return d


def sample(d, band=UV_BAND):
    s = d[(d.v >= MIN_VALUE_KUSD) & (d.q > 0) & d.k.isin(ALL)].copy()
    s['uv'] = s.v * 1000.0 / s.q                                # USD per tonne
    med = s.groupby(['k', 'year']).uv.transform('median')
    before = len(s)
    if band is not None:
        s = s[(s.uv >= band[0] * med) & (s.uv <= band[1] * med)]
    s['flow'] = s.exp + '|' + s.imp + '|' + s.k
    s['luv'], s['lq'] = np.log(s.uv), np.log(s.q)
    return s.reset_index(drop=True), before - len(s)


# ----------------------------------------------------------------------------- estimation
def demean_within(df, cols, group):
    g = df.groupby(group)[cols].transform('mean')
    return df[cols] - g


def own_rng(label):
    """Deviation 10: each estimate draws from its own stream, seeded by the study seed and its label,
    so a p-value does not change when another estimate is added earlier in the run."""
    return np.random.default_rng([SEED, zlib.crc32(label.encode('utf-8'))])


def estimate(df, yvar, treated, label, rng, draws=DRAWS, years=None, post=(P1, P2)):
    """Two-way FE by within-transformation; line-level wild bootstrap (null imposed) for each b."""
    rng = own_rng(label + '|' + yvar)
    d = df[df.k.isin(treated['lines'] + treated['controls'])].copy()
    if years is not None:
        d = d[d.year.isin(years)]
    d['T'] = d.k.isin(treated['lines']).astype(float)
    names = []
    for idx, per in enumerate(post):
        n = 'TxP%d' % (idx + 1)
        d[n] = d['T'] * d.year.isin(per).astype(float)
        names.append(n)
    yrs = sorted(d.year.unique())
    ydum = ['y%d' % y for y in yrs[1:]]
    for y in yrs[1:]:
        d['y%d' % y] = (d.year == y).astype(float)
    # singletons carry no within variation
    d = d[d.groupby('flow').year.transform('size') > 1].reset_index(drop=True)
    if d.empty or d.k.nunique() < 3:
        return None
    cols = [yvar] + names + ydum
    w = demean_within(d, cols, 'flow')
    X = w[names + ydum].values
    Y = w[yvar].values
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ Y
    resid = Y - X @ beta
    lines = d.k.values
    exporters = d.exp.values

    def cluster_se(groups):
        meat = np.zeros((X.shape[1], X.shape[1]))
        for g in np.unique(groups):
            m = groups == g
            s = X[m].T @ resid[m]
            meat += np.outer(s, s)
        G = len(np.unique(groups))
        if G < 2:                                            # one exporter (the China-only split)
            return np.full(X.shape[1], np.nan), G
        n, k = X.shape
        adj = G / (G - 1) * (n - 1) / max(n - k - d.flow.nunique(), 1)
        V = XtX_inv @ meat @ XtX_inv * adj
        return np.sqrt(np.clip(np.diag(V), 0, None)), G

    se_exp, g_exp = cluster_se(exporters)
    out = {'label': label, 'y': yvar, 'n': int(len(d)), 'flows': int(d.flow.nunique()),
           'lines_treated': sorted(set(treated['lines']) & set(d.k)),
           'lines_control': sorted(set(treated['controls']) & set(d.k)),
           'exporters': int(g_exp), 'coefs': {}}
    ulines = np.unique(lines)
    line_idx = np.searchsorted(ulines, lines)
    for ci, n in enumerate(names):
        # restricted model: drop the tested regressor, keep the others
        keep = [c for c in range(X.shape[1]) if c != ci]
        Xr = X[:, keep]
        br = np.linalg.pinv(Xr.T @ Xr) @ Xr.T @ Y
        fit_r = Xr @ br
        res_r = Y - fit_r
        row = XtX_inv[ci] @ X.T                              # b_ci = row . y
        base = float(row @ fit_r)
        contrib = np.bincount(line_idx, weights=row * res_r, minlength=len(ulines))
        W = WEBB[rng.integers(0, 6, size=(draws, len(ulines)))]
        bstar = base + W @ contrib
        b = float(beta[ci])
        p_boot = float((np.abs(bstar - base) >= abs(b - base)).mean())
        se_boot = float(np.std(bstar, ddof=1))
        crit = float(np.quantile(np.abs(bstar - base), 0.95))
        out['coefs'][n] = {
            'beta': round(b, 4), 'pct': round(100 * (math.exp(b) - 1), 2),
            'p_wild_line': round(p_boot, 4), 'se_wild_line': round(se_boot, 4),
            'ci95_wild_line': [round(b - crit, 4), round(b + crit, 4)],
            'mde_80': round(2.8 * se_boot, 4),
            'se_cluster_exporter': round(float(se_exp[ci]), 4),
            'lines_in_bootstrap': int(len(ulines))}
    return out


def event_study(df, yvar, treated, rng, draws=DRAWS, label='event'):
    """Year-by-year treated gaps, base 2019. Deviation 5: the intervals use the SAME procedure as the
    headline estimates - null imposed for each year's coefficient (restricted residuals), Webb
    weights by line, 9,999 draws. The first version used unrestricted residuals and 2,999 draws,
    which drew intervals far narrower than the headline test's and made the chart look more
    certain than the result."""
    rng = own_rng(label + '|' + yvar + '|' + ','.join(treated['lines']))
    d = df[df.k.isin(treated['lines'] + treated['controls'])].copy()
    d['T'] = d.k.isin(treated['lines']).astype(float)
    yrs = sorted(d.year.unique())
    ev = ['T%d' % y for y in yrs if y != BASE_YEAR]
    for y in yrs:
        if y != BASE_YEAR:
            d['T%d' % y] = d['T'] * (d.year == y)
    ydum = ['y%d' % y for y in yrs[1:]]
    for y in yrs[1:]:
        d['y%d' % y] = (d.year == y).astype(float)
    d = d[d.groupby('flow').year.transform('size') > 1].reset_index(drop=True)
    cols = [yvar] + ev + ydum
    w = demean_within(d, cols, 'flow')
    X, Y = w[ev + ydum].values, w[yvar].values
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ Y
    ulines = np.unique(d.k.values)
    li = np.searchsorted(ulines, d.k.values)
    out = {}
    for ci, n in enumerate(ev):
        keep = [c for c in range(X.shape[1]) if c != ci]
        Xr = X[:, keep]
        br = np.linalg.pinv(Xr.T @ Xr) @ Xr.T @ Y
        fit_r = Xr @ br
        res_r = Y - fit_r
        row = XtX_inv[ci] @ X.T
        base = float(row @ fit_r)
        contrib = np.bincount(li, weights=row * res_r, minlength=len(ulines))
        W = WEBB[rng.integers(0, 6, size=(draws, len(ulines)))]
        dev = np.abs(W @ contrib)
        crit = float(np.quantile(dev, 0.95))
        b = float(beta[ci])
        p = float((dev >= abs(b - base)).mean())
        out[int(n[1:])] = {'beta': round(b, 4), 'ci95': [round(b - crit, 4), round(b + crit, 4)],
                           'p_wild_line': round(p, 4)}
    out[BASE_YEAR] = {'beta': 0.0, 'ci95': [0.0, 0.0], 'p_wild_line': None}
    return dict(sorted(out.items()))


def two_line_design(df, yvar, spec):
    """Deviation 1: one treated line against one control line cannot support a line-level
    bootstrap (two clusters). Same equation, exporter-clustered only, labelled as such."""
    from scipy import stats
    d = df[df.k.isin(spec['lines'] + spec['controls'])].copy()
    d['T'] = d.k.isin(spec['lines']).astype(float)
    names = ['TxP1', 'TxP2']
    for n, per in zip(names, (P1, P2)):
        d[n] = d['T'] * d.year.isin(per).astype(float)
    yrs = sorted(d.year.unique())
    yd = ['y%d' % y for y in yrs[1:]]
    for y in yrs[1:]:
        d['y%d' % y] = (d.year == y).astype(float)
    d = d[d.groupby('flow').year.transform('size') > 1].reset_index(drop=True)
    w = demean_within(d, [yvar] + names + yd, 'flow')
    X, Y = w[names + yd].values, w[yvar].values
    Xi = np.linalg.pinv(X.T @ X)
    b = Xi @ X.T @ Y
    r = Y - X @ b
    meat = np.zeros((X.shape[1], X.shape[1]))
    ex = d.exp.values
    for g in np.unique(ex):
        m = ex == g
        sc = X[m].T @ r[m]
        meat += np.outer(sc, sc)
    G = len(np.unique(ex))
    se = np.sqrt(np.diag(Xi @ meat @ Xi * G / (G - 1)))
    return {'note': 'one treated and one control line: exporter-clustered only (deviation 1)',
            'y': yvar, 'n': int(len(d)), 'exporters': int(G), 'coefs': {
                n: {'beta': round(float(b[i]), 4), 'pct': round(100 * (math.exp(b[i]) - 1), 2),
                    'se_cluster_exporter': round(float(se[i]), 4),
                    'p_cluster_exporter': round(float(2 * stats.t.sf(abs(b[i] / se[i]), G - 1)), 4)}
                for i, n in enumerate(names)}}


# ----------------------------------------------------------------------------- design C
def material_adjusted(s, cpi, copper):
    """Subtract 0.25 x real GOES world UV and 0.25 x real copper price from transformer log UVs."""
    g = s[s.k == '722511'].groupby('year').agg(v=('v', 'sum'), q=('q', 'sum'))
    goes_uv = (g.v * 1000.0 / g.q).to_dict()
    lg = {y: math.log(goes_uv[y] / cpi[y]) for y in goes_uv if y in cpi}
    lc = {y: math.log(copper[y] / cpi[y]) for y in copper if y in cpi}

    def adj(frame, sg, sc):
        f = frame.copy()
        m = f.k.isin(TRANSFORMERS)
        f.loc[m, 'luv'] = (f.loc[m, 'luv'] - sg * f.loc[m, 'year'].map(lg)
                           - sc * f.loc[m, 'year'].map(lc))
        return f.dropna(subset=['luv'])
    return adj, {'goes_real_log': lg, 'copper_real_log': lc}


# ----------------------------------------------------------------------------- descriptive
def suppliers(d, lines):
    out = {}
    for k in lines:
        out[k] = {}
        for y in (2019, 2022, 2024):
            t = d[(d.k == k) & (d.year == y)]
            ex = t.groupby('exp').v.sum()
            sh = (ex / ex.sum()).sort_values(ascending=False)
            out[k][y] = {'value_musd': round(float(t.v.sum()) / 1000.0, 1),
                         'exporters_above_1pct': int((sh > 0.01).sum()),
                         'china_share': round(float(sh.get('CHN', 0.0)), 4),
                         'russia_share': round(float(sh.get('RUS', 0.0)), 4),
                         'top3_share': round(float(sh.head(3).sum()), 4),
                         'top3': [[i, round(float(x), 3)] for i, x in sh.head(3).items()]}
    return out


def bls_validation(d, ppi):
    t = d[(d.imp == 'USA') & d.k.isin(TRANSFORMERS) & (d.q > 0)]
    g = t.groupby('year').agg(v=('v', 'sum'), q=('q', 'sum'))
    uv = (g.v * 1000.0 / g.q).to_dict()
    yrs = [y for y in YEARS if y in uv and y - 1 in uv and y in ppi and y - 1 in ppi]
    a = [math.log(uv[y] / uv[y - 1]) for y in yrs]
    b = [math.log(ppi[y] / ppi[y - 1]) for y in yrs]
    lev = [y for y in YEARS if y in uv and y in ppi]
    return {'years': yrs,
            'corr_annual_changes': round(float(np.corrcoef(a, b)[0, 1]), 3),
            'corr_levels': round(float(np.corrcoef([math.log(uv[y]) for y in lev],
                                                    [math.log(ppi[y]) for y in lev])[0, 1]), 3),
            'us_import_uv_usd_t': {y: round(uv[y], 1) for y in lev},
            'ppi': {y: ppi[y] for y in lev}}


def describe_chip_equipment():
    """Deviation 6: HS 8486 was created in HS 2007, so it does not exist in the HS 2002 panel and the
    filed description returned zeros. It is read in HS 2017, where the codes exist, for 2017 and
    2024 only. Description, not a test."""
    iso = baci.countries().set_index('code')['iso3'].to_dict()
    out = {}
    for y in (2017, 2024):
        t = baci.year(y, nom='HS17')
        t['k'] = t.k.astype(str).str.zfill(6)
        for k in DESCRIBE_ONLY:
            g = t[t.k == k]
            ex = g.groupby('i').v.sum()
            sh = (ex / ex.sum()).sort_values(ascending=False)
            out.setdefault(k, {})[y] = {
                'value_musd': round(float(g.v.sum()) / 1000.0, 1),
                'hhi': round(float((sh ** 2).sum()), 3),
                'top3': [[iso.get(str(i), str(i)), round(float(x), 4)] for i, x in sh.head(3).items()]}
    return out


def suppliers_combined(d, lines, label):
    """Deviation 7: supplier structure for a group of lines taken together (GOES = 7225.11 + 7226.11),
    because the study defines GOES as both lines and one line alone overstated its concentration."""
    out = {'lines': lines}
    for y in (2019, 2022, 2024):
        t = d[d.k.isin(lines) & (d.year == y)]
        ex = t.groupby('exp').v.sum()
        sh = (ex / ex.sum()).sort_values(ascending=False)
        out[y] = {'value_musd': round(float(t.v.sum()) / 1000.0, 1),
                  'exporters_above_1pct': int((sh > 0.01).sum()),
                  'china_share': round(float(sh.get('CHN', 0.0)), 4),
                  'russia_share': round(float(sh.get('RUS', 0.0)), 4),
                  'japan_share': round(float(sh.get('JPN', 0.0)), 4),
                  'top3_share': round(float(sh.head(3).sum()), 4),
                  'top3': [[i, round(float(x), 4)] for i, x in sh.head(3).items()]}
    return out


# ----------------------------------------------------------------------------- main
def main():
    rng = np.random.default_rng(SEED)
    cpi = read_csv_series('us_cpi_worldbank.csv', 'cpi_2010_100')
    ppi = read_csv_series('bls_wpu117409_annual.csv', 'ppi_annual_mean')
    copper = copper_annual()
    raw = load_flows()
    s, dropped = sample(raw)

    A_goes = {'lines': GOES, 'controls': STEEL_CTL}
    A_cu = {'lines': CU_WIRE, 'controls': CU_CATHODE}
    B = {'lines': TRANSFORMERS, 'controls': CAPITAL_CTL}

    res = {'filing': 'buildout-study/PREREGISTRATION.md', 'nomenclature': NOM,
           'years': [YEARS[0], YEARS[-1]], 'post_periods': {'P1': list(P1), 'P2': list(P2)},
           'sample': {'flow_years': int(len(s)), 'dropped_by_uv_band': int(dropped),
                      'min_value_usd': 100000, 'uv_band': list(UV_BAND)},
           'designs': {}, 'checks': {}}

    D = res['designs']
    for tag, spec in (('A_goes', A_goes), ('B_transformers', B)):
        D[tag] = {'price': estimate(s, 'luv', spec, tag + ' price', rng),
                  'volume': estimate(s, 'lq', spec, tag + ' volume', rng)}
    D['A_copper_wire'] = {'price': two_line_design(s, 'luv', A_cu),
                          'volume': two_line_design(s, 'lq', A_cu)}
    for k in TRANSFORMERS:
        spec = {'lines': [k], 'controls': CAPITAL_CTL}
        D['B_' + k] = {'price': estimate(s, 'luv', spec, k + ' price', rng),
                       'volume': estimate(s, 'lq', spec, k + ' volume', rng)}

    adj, series = material_adjusted(s, cpi, copper)
    D['C_net_of_materials'] = {'price': estimate(adj(s, SHARE_GOES, SHARE_CU), 'luv', B, 'C price', rng)}
    for sh in (0.20, 0.30):
        D['C_shares_%.2f' % sh] = {'price': estimate(adj(s, sh, sh), 'luv', B, 'C price %.2f' % sh, rng)}
    # Deviation 8 (added after referee review): the filed design C nets copper and GOES from the
    # treated lines only, although the controls contain copper and ordinary steel too. GOES is the
    # one input the controls do not use, so netting GOES alone is the cleaner variant; reported
    # beside the filed one as a sensitivity.
    D['C_goes_only'] = {'price': estimate(adj(s, SHARE_GOES, 0.0), 'luv', B, 'C price, GOES only', rng)}
    res['material_series'] = {k: {int(y): round(v, 4) for y, v in d.items()} for k, d in series.items()}

    C = res['checks']
    C['event_study'] = {
        'A_goes_price': event_study(s, 'luv', A_goes, rng, label='ev A_goes'),
        'A_goes_volume': event_study(s, 'lq', A_goes, rng, label='ev A_goes'),
        'B_price': event_study(s, 'luv', B, rng, label='ev B'),
        'B_volume': event_study(s, 'lq', B, rng, label='ev B'),
        'C_price': event_study(adj(s, SHARE_GOES, SHARE_CU), 'luv', B, rng, label='ev C'),
    }
    pre = {}
    for k, ev in C['event_study'].items():
        viol = [y for y in range(2014, 2019) if y in ev and abs(ev[y]['beta']) > 0.05]
        pre[k] = {'years_outside_0.05': viol, 'did_language_allowed': not viol}
    C['pretrend_rule'] = pre

    for tag, spec in (('A_goes', A_goes), ('B_transformers', B)):
        C['placebo_2015_16_' + tag] = estimate(s, 'luv', spec, 'placebo ' + tag, rng,
                                               years=list(range(2012, 2017)), post=((2015, 2016),))
    C['uv_band_0.2_5'] = estimate(sample(raw, (0.2, 5.0))[0], 'luv', B, 'B price band 0.2-5', rng)
    C['uv_band_none'] = estimate(sample(raw, None)[0], 'luv', B, 'B price no band', rng)
    C['bls_validation'] = bls_validation(raw, ppi)
    C['suppliers'] = suppliers(raw, TRANSFORMERS + GOES + CU_WIRE)
    C['suppliers_goes_combined'] = suppliers_combined(raw, GOES, 'GOES')

    for name, m in (('USA', s.imp == 'USA'), ('EU27', s.imp.isin(EU27)),
                    ('rest', ~(s.imp == 'USA') & ~s.imp.isin(EU27))):
        C['importer_' + name] = {
            'B_price': estimate(s[m], 'luv', B, 'B price into ' + name, rng),
            'B_volume': estimate(s[m], 'lq', B, 'B volume into ' + name, rng),
            'C_price': estimate(adj(s[m], SHARE_GOES, SHARE_CU), 'luv', B, 'C price into ' + name, rng)}
    for name, m in (('China', s.exp == 'CHN'), ('not_China', s.exp != 'CHN')):
        C['exporter_' + name] = {'B_price': estimate(s[m], 'luv', B, 'B price from ' + name, rng),
                                 'B_volume': estimate(s[m], 'lq', B, 'B volume from ' + name, rng)}
    C['leave_one_line_out'] = {}
    for spec_tag, spec in (('A_goes', A_goes), ('B_transformers', B)):
        for k in spec['lines'] + spec['controls']:
            sub = {'lines': [x for x in spec['lines'] if x != k],
                   'controls': [x for x in spec['controls'] if x != k]}
            if not sub['lines']:
                continue
            e = estimate(s, 'luv', sub, '%s without %s' % (spec_tag, k), rng, draws=2999)
            C['leave_one_line_out']['%s_without_%s' % (spec_tag, k)] = (
                {n: v['beta'] for n, v in e['coefs'].items()} if e else None)
    med = s[s.k.isin(TRANSFORMERS + CAPITAL_CTL)].uv.median()
    C['freight_heavy_low_uv'] = estimate(s[s.uv <= med], 'luv', B, 'B price, UV below median', rng)
    C['freight_light_high_uv'] = estimate(s[s.uv > med], 'luv', B, 'B price, UV above median', rng)
    C['contaminated_controls'] = {
        'price': estimate(s, 'luv', {'lines': TRANSFORMERS, 'controls': CONTAMINATED}, 'B vs contaminated', rng),
        'volume': estimate(s, 'lq', {'lines': TRANSFORMERS, 'controls': CONTAMINATED}, 'B vs contaminated vol', rng)}
    res['chip_equipment_described_only'] = describe_chip_equipment()

    # Deviation 9 - EXPLORATORY, NOT FILED, run after the referees asked it: did other electrical
    # equipment rise against the same construction machinery? And transformers against the
    # construction-only controls (welding machines, which are electrical, removed). Written to a
    # separate file so it can never be mistaken for a filed result.
    cons = ['842810', '842649', '847420', '847431']
    ex = {'note': 'exploratory, not filed; see deviation 9 in PREREGISTRATION.md'}
    for yv in ('luv', 'lq'):
        ex[yv] = estimate(s, yv, {'lines': CONTAMINATED, 'controls': CAPITAL_CTL},
                          'exploratory electrical vs construction', rng)['coefs']
        ex['transformers_vs_construction_only_' + yv] = estimate(
            s, yv, {'lines': TRANSFORMERS, 'controls': cons}, 'exploratory transformers vs construction only', rng)['coefs']
    with open(os.path.join(HERE, 'exploratory_electrical_boom.json'), 'w', encoding='utf-8') as f:
        json.dump(ex, f, indent=1, default=float)

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1, default=float)

    def show(tag, e):
        if not e:
            print('%-26s no estimate' % tag)
            return
        c = e['coefs']
        print('%-26s ' % tag + '  '.join(
            '%s %+.3f (%+.0f%%) p=%.3f' % (n, v['beta'], v['pct'],
                                          v.get('p_wild_line', v.get('p_cluster_exporter')))
            for n, v in c.items()) + '  [n %d]' % e['n'])
    for tag, v in D.items():
        for side, e in v.items():
            show('%s %s' % (tag, side), e)
    print('pretrend rule:', {k: v['did_language_allowed'] for k, v in pre.items()})
    print('BLS validation:', C['bls_validation']['corr_annual_changes'], C['bls_validation']['corr_levels'])
    print('wrote', OUT)


if __name__ == '__main__':
    main()
