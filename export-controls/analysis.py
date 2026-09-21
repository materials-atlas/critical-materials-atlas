# -*- coding: utf-8 -*-
"""Did China's export controls bite? Runs the tests filed in export-controls/PREREGISTRATION.md.

Committed before its first run on the downloaded data.

For each control and importer, the treated and comparison series are built monthly from the EU's and
the US's own import records. With two series, series fixed effects plus one effect per calendar month
is the same as regressing the monthly DIFFERENCE between treated and comparison on the event windows,
which is what is done here: D_t = y_treated,t - y_comparison,t on an anticipation window and event bins
0-3, 4-6 and 7-12 months after entry into force, relative to the pre-period, with Newey-West errors
(six lags). Quantities use the inverse hyperbolic sine (deviation 1): it keeps months with no imports
from China, which are the strongest possible bite, where a log would drop them.

Writes out/export_controls.json. Usage: python export-controls/analysis.py
"""
import glob
import json
import math
import os
import re

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'out', 'export_controls.json')
LAST = '202607'
THR_CHINA = math.log(0.70)          # a 30% fall
THR_TOTAL = math.log(0.80)          # a 20% fall
THR_PRICE = math.log(1.20)          # a 20% rise
REAL_COUNTRY = re.compile(r'^[1-7]\d{3}$')

EU = {
    'gage': ['81129289', '81129295'], 'graphite': ['25041000'],
    'magnets': ['85051110'], 'hree': ['28053031', '28469060'],
    'antimony': ['81101000', '81102000', '81109000', '26171000'],
    'bismuth': ['81061010', '81061090', '81069010', '81069090'],
    'magnesium': ['81041100', '81041900'], 'talc_baryte': ['25262000', '25111000'],
    'ferrite': ['85051910'], 'lree': ['28469040', '28461000'],
}
US = {
    'gage': ['8112921000', '8112926000', '8112926500'],
    # deviation 2: 3801105000 split into 3801105010 (spherical) and 3801105090 inside the window; the
    # filing's rule sums code changes back to the stem, so the whole of 38011050 is used throughout
    'graphite': ['2504101000', '2504105000', '38011050*'],
    'magnets': ['8505110050', '8505110070'],
    'antimony': ['8110100000', '8110200000', '8110900000'],
    'bismuth': ['8106100000', '8106900000'],
    'magnesium': ['8104110000', '8104190000'], 'talc_baryte': ['2526*', '2511*'],
    'ferrite': ['8505193000'],
}
# (id, importer, treated, comparison, announced, in force, post ends [inclusive], label)
CONTROLS = [
    ('C1', 'EU', 'gage', 'magnesium', '202307', '202308', None, 'gallium and germanium'),
    ('C1', 'US', 'gage', 'magnesium', '202307', '202308', None, 'gallium and germanium'),
    ('C2', 'EU', 'graphite', 'talc_baryte', '202310', '202312', None, 'graphite'),
    ('C2', 'US', 'graphite', 'talc_baryte', '202310', '202312', None, 'graphite'),
    ('C3', 'US', 'gage', 'magnesium', '202412', '202412', '202510', 'ban on Ga, Ge to the US'),
    ('C4', 'EU', 'magnets', 'ferrite', '202504', '202504', None, 'rare-earth magnets'),
    ('C4', 'US', 'magnets', 'ferrite', '202504', '202504', None, 'rare-earth magnets'),
    ('C4r', 'EU', 'hree', 'lree', '202504', '202504', None, 'Gd, Tb, Dy metals and compounds'),
    ('C5', 'EU', 'antimony', 'magnesium', '202408', '202409', None, 'antimony'),
    ('C5', 'US', 'antimony', 'magnesium', '202408', '202409', None, 'antimony'),
    ('C6', 'EU', 'bismuth', 'magnesium', '202502', '202502', None, 'bismuth'),
    ('C6', 'US', 'bismuth', 'magnesium', '202502', '202502', None, 'bismuth'),
]
# deviation 3: US imports of magnesium FROM CHINA fell about 90% across the window (2.6 Mt in 2021 to
# 0.2 Mt in 2025), so they cannot serve as the comparison for the China-origin outcome in the US; that
# outcome is reported as not interpretable wherever the US comparison is magnesium. Total kilograms and
# unit values use all origins, where US magnesium imports are stable, and are kept.
BROKEN_CHINA_COMPARISON = {('US', 'magnesium')}
# the filing's overlap rule: C3's pre-period starts when C1's control on the same goods took effect
PRE_START = {'C3': '202308'}


def months(a, b):
    y, m = int(a[:4]), int(a[4:])
    out = []
    while '%04d%02d' % (y, m) <= b:
        out.append('%04d%02d' % (y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def shift(ym, k):
    y, m = int(ym[:4]), int(ym[4:]) + k
    while m > 12:
        y, m = y + 1, m - 12
    while m < 1:
        y, m = y - 1, m + 12
    return '%04d%02d' % (y, m)


def eu_monthly():
    files = sorted(glob.glob(os.path.join(HERE, 'eu_data', 'comext_*.parquet')))
    con = duckdb.connect()
    d = con.execute("""select PRODUCT_NC as code, PERIOD as ym, PARTNER as par,
                              sum(try_cast(VALUE_EUR as double)) as v, sum(try_cast(QUANTITY_KG as double)) as kg
                       from read_parquet(?) where TRADE_TYPE = 'E' and FLOW = '1'
                         and REPORTER <> 'GB' and PARTNER not in ('GB', 'XI')
                       group by 1, 2, 3""", [files]).df()
    d = d[d.ym.str[4:6].astype(int).between(1, 12)]
    d['china'] = d.par == 'CN'
    out = {}
    for g, codes in EU.items():
        s = d[d.code.isin(codes)]
        out[g] = s
    return out


def us_monthly():
    fs = sorted(glob.glob(os.path.join(HERE, 'us_data', 'census_*.parquet')))
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    d = d[(d.SUMMARY_LVL == 'DET') & d.CTY_CODE.astype(str).str.match(REAL_COUNTRY)].copy()
    d['v'] = pd.to_numeric(d.GEN_VAL_MO, errors='coerce')
    q1, q2 = pd.to_numeric(d.GEN_QY1_MO, errors='coerce'), pd.to_numeric(d.GEN_QY2_MO, errors='coerce')
    d['kg'] = np.where(d.UNIT_QY1 == 'KG', q1, np.where(d.UNIT_QY2 == 'KG', q2, np.nan))
    d['ym'] = d.month
    d['code'] = d.I_COMMODITY.astype(str)
    d['china'] = d.CTY_NAME == 'CHINA'
    out = {}
    for g, codes in US.items():
        exact = [c for c in codes if not c.endswith('*')]
        pref = tuple(c[:-1] for c in codes if c.endswith('*'))
        m = d.code.isin(exact) | (d.code.str.startswith(pref) if pref else False)
        out[g] = d[m]
    return out


def series(s, span):
    g = s.groupby('ym').agg(v=('v', 'sum'), kg=('kg', 'sum'))
    c = s[s.china].groupby('ym').agg(kg_cn=('kg', 'sum'))
    t = pd.DataFrame(index=span).join(g).join(c).fillna({'v': 0.0, 'kg': 0.0, 'kg_cn': 0.0})
    t['y_china'] = np.arcsinh(t.kg_cn)
    t['y_total'] = np.arcsinh(t.kg)
    t['y_price'] = np.where((t.kg > 0) & (t.v > 0), np.log(t.v / t.kg.where(t.kg > 0)), np.nan)
    t['kg_missing_share'] = float(s.kg.isna().mean()) if len(s) else 1.0
    return t


def estimate(ctrl, data):
    cid, imp, tr, cp, ann, eff, post_end, label = ctrl
    pre_start = PRE_START.get(cid, shift(ann, -24))
    end = min(post_end or LAST, shift(eff, 12), LAST)          # the filed 7-12 bin ends at month 12
    span = months(pre_start, end)
    T, C = series(data[imp][tr], span), series(data[imp][cp], span)
    res = {'control': cid, 'importer': imp, 'label': label, 'treated': tr, 'comparison': cp,
           'announced': ann, 'in_force': eff, 'window': [pre_start, end],
           'treated_kg_unreported_share': round(float(T.kg_missing_share.iloc[0]), 3),
           'treated_months_with_china_imports_pre': int((T.loc[[m for m in span if m < ann], 'kg_cn'] > 0).sum()),
           'outcomes': {}}
    ev = pd.DataFrame(index=span)
    ev['antic'] = [(ann <= m < eff) for m in span]
    # months 0-3 after entry into force (the month it took effect is 0), then 4-6, then 7-12
    ev['b0_3'] = [shift(eff, 0) <= m <= shift(eff, 3) for m in span]
    ev['b4_6'] = [shift(eff, 4) <= m <= shift(eff, 6) for m in span]
    ev['b7_12'] = [shift(eff, 7) <= m <= shift(eff, 12) for m in span]
    bins = [b for b in ('b0_3', 'b4_6', 'b7_12') if ev[b].sum() > 0]
    post_bin = 'b7_12' if 'b7_12' in bins else bins[-1]
    res['post_bin'] = post_bin
    res['post_months'] = int(ev[post_bin].sum())
    for out in ('y_china', 'y_total', 'y_price'):
        if out == 'y_china' and (imp, cp) in BROKEN_CHINA_COMPARISON:
            res['outcomes'][out] = None
            res['china_outcome_not_interpretable'] = 'comparison broken: China-origin magnesium collapsed (deviation 3)'
            continue
        D = (T[out] - C[out]).rename('D')
        X = ev[['antic'] + bins].astype(float)
        dd = pd.concat([D, X], axis=1).dropna()
        if len(dd) < 18 or dd[post_bin].sum() == 0:
            res['outcomes'][out] = None
            continue
        m = sm.OLS(dd.D, sm.add_constant(dd[['antic'] + bins])).fit(cov_type='HAC', cov_kwds={'maxlags': 6})
        b, se = float(m.params[post_bin]), float(m.bse[post_bin])
        dfree = int(m.df_resid)
        crit = float(stats.t.ppf(0.975, dfree))
        res['outcomes'][out] = {
            'estimate': round(b, 4),
            # deviation 4: a percentage is meaningful for the log unit value, not for asinh quantities
            # whose series touch zero; those are reported in log points only
            'pct': round(100 * (math.exp(b) - 1), 1) if out == 'y_price' else None, 'se': round(se, 4),
            'p': round(float(2 * stats.t.sf(abs(b / se), dfree)), 4) if se > 0 else None,
            'ci95': [round(b - crit * se, 4), round(b + crit * se, 4)],
            'mde_80': round(float((crit + stats.t.ppf(0.80, dfree)) * se), 4),
            'months': int(len(dd)),
            'bins': {k: round(float(m.params[k]), 4) for k in ['antic'] + bins}}
    return res


def read(r, p_adj):
    c, t, pr = (r['outcomes'].get(k) for k in ('y_china', 'y_total', 'y_price'))
    if not c:
        return 'no estimate'
    if c['mde_80'] > abs(THR_CHINA):
        return 'untestable at a 30% fall'
    fell = c['estimate'] <= THR_CHINA and c['ci95'][1] < 0 and p_adj is not None and p_adj < 0.05
    if fell:
        tot = bool(t and t['estimate'] <= THR_TOTAL and t['ci95'][1] < 0)
        pri = bool(pr and pr['estimate'] >= THR_PRICE and pr['ci95'][0] > 0)
        return 'bit' if (tot or pri) else 'diverted'
    if c['ci95'][0] > THR_CHINA:
        return 'no visible effect'
    return 'inconclusive'


def read_corrected(r, p_adj):
    """Deviation 5, post-hoc and labelled: the filed rule checks 'untestable' first, so a 98% fall with
    a tight interval reads 'untestable at a 30% fall'. The precedence a reader would expect: an
    interval that already clears the threshold decides the reading whatever the design's power."""
    c, t, pr = (r['outcomes'].get(k) for k in ('y_china', 'y_total', 'y_price'))
    if not c:
        return 'not interpretable' if r.get('china_outcome_not_interpretable') else 'no estimate'
    tot = bool(t and t['estimate'] <= THR_TOTAL and t['ci95'][1] < 0)
    pri = bool(pr and pr['estimate'] >= THR_PRICE and pr['ci95'][0] > 0)
    if c['ci95'][1] < THR_CHINA and p_adj is not None and p_adj < 0.05:
        return 'bit' if (tot or pri) else 'diverted'
    if c['ci95'][0] > THR_CHINA:
        return 'no visible effect'
    if c['mde_80'] > abs(THR_CHINA):
        return 'untestable at a 30% fall'
    return 'inconclusive'


def holm(ps):
    idx = sorted(range(len(ps)), key=lambda i: ps[i] if ps[i] is not None else 2)
    adj, run = [None] * len(ps), 0.0
    n = sum(1 for p in ps if p is not None)
    for rank, i in enumerate(idx):
        if ps[i] is None:
            continue
        run = max(run, min(1.0, (n - rank) * ps[i]))
        adj[i] = round(run, 4)
    return adj


def main():
    data = {'EU': eu_monthly(), 'US': us_monthly()}
    results = [estimate(c, data) for c in CONTROLS]
    ps = [r['outcomes']['y_china']['p'] if r['outcomes'].get('y_china') else None for r in results]
    adj = holm(ps)
    for r, a in zip(results, adj):
        r['p_china_holm'] = a
        r['reading_as_filed'] = read(r, a)
        r['reading_corrected_precedence'] = read_corrected(r, a)
    out = {'filing': 'export-controls/PREREGISTRATION.md', 'last_month': LAST,
           'thresholds': {'china_kg_fall': '30%', 'total_kg_fall': '20%', 'unit_value_rise': '20%'},
           'results': results}
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, default=float)
    for r in results:
        c = r['outcomes'].get('y_china')
        t = r['outcomes'].get('y_total')
        p = r['outcomes'].get('y_price')
        f = lambda o: ('%+.2f [%+.2f,%+.2f] mde %.2f' % (o['estimate'], o['ci95'][0], o['ci95'][1], o['mde_80'])) if o else '      n/a'
        print('%-3s %s %-26s | China %s | total %s | price %s | holm %s | filed: %s | corrected: %s' % (
            r['control'], r['importer'], r['label'][:26], f(c), f(t), f(p), r['p_china_holm'],
            r['reading_as_filed'], r['reading_corrected_precedence']))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
