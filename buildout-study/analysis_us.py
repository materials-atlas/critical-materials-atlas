# -*- coding: utf-8 -*-
"""Amendment C: US imports to July 2026. Runs the tests filed in AMENDMENT_US_2026.md.

Committed before its first run on the downloaded data. Uses analysis.py's estimator unchanged. Only
detail rows are read (SUMMARY_LVL = 'DET', four-digit country codes that are real countries), never the
country groupings the API returns alongside them. Writes every number to out/buildout_us.json.

Usage:  python buildout-study/analysis_us.py
"""
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import analysis as an

OUT = os.path.join(ROOT, 'out', 'buildout_us.json')
POST = ((2021, 2022), (2023, 2024), (2025,), (2026,))
POST_NAMES = ['2021-22', '2023-24', '2025', '2026 (Jan-Jul)']
MIN_USD = 100000.0
CONSTRUCTION = ['842810', '842649', '847420', '847431']
REAL_COUNTRY = re.compile(r'^[1-7]\d{3}$')                      # groupings are '-', 0xxx and 1XXX-style


def num(s):
    return pd.to_numeric(s, errors='coerce')


def load():
    frames = [pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(HERE, 'us_data', 'census_*.parquet')))]
    d = pd.concat(frames, ignore_index=True)
    d = d[(d.SUMMARY_LVL == 'DET') & d.CTY_CODE.astype(str).str.match(REAL_COUNTRY)].copy()
    d['year'] = d.month.str[:4].astype(int)
    d = d[d.month.str[4:6].astype(int).between(1, 12)]
    d['k'] = d.I_COMMODITY.str[:6]
    d['v'] = num(d.GEN_VAL_MO)
    d['n'] = np.where(d.UNIT_QY1 == 'NO', num(d.GEN_QY1_MO), np.nan)
    d['kg'] = np.where(d.UNIT_QY2 == 'KG', num(d.GEN_QY2_MO),
                       np.where(d.UNIT_QY1 == 'KG', num(d.GEN_QY1_MO), np.nan))
    return d


def panel(d, level='k'):
    g = d.groupby(['CTY_CODE', level, 'year'], as_index=False).agg(v=('v', 'sum'), n=('n', 'sum'),
                                                                   kg=('kg', 'sum'))
    thr = np.where(g.year == 2026, MIN_USD * 7 / 12, MIN_USD)
    g = g[(g.v >= thr) & (g.n > 0)].copy()
    g['pu'] = g.v / g.n
    med = g.groupby([level, 'year']).pu.transform('median')
    g = g[(g.pu >= 0.1 * med) & (g.pu <= 10 * med)].copy()
    g['k'] = g[level]
    g['flow'] = g.CTY_CODE + '|' + g[level]
    g['exp'] = g.CTY_CODE                                         # cluster: origin country
    g['lpu'] = np.log(g.pu)
    g['lkpu'] = np.where(g.kg > 0, np.log(g.kg / g.n), np.nan)
    g['lvkg'] = np.where(g.kg > 0, np.log(g.v / g.kg), np.nan)
    return g.reset_index(drop=True)


def est(df, y, lines, controls, label):
    sub = df.dropna(subset=[y])
    e = an.estimate(sub, y, {'lines': lines, 'controls': controls}, label, None, post=POST)
    if e:
        e['period_names'] = dict(zip(['TxP1', 'TxP2', 'TxP3', 'TxP4'], POST_NAMES))
    return e


def own_path(df, lines, y):
    """Filed test 2: a group's own measure over time, within flows, relative to 2019."""
    q = df[df.k.isin(lines)].dropna(subset=[y]).copy()
    q = q[q.groupby('flow').year.transform('size') > 1]
    yrs = sorted(q.year.unique())
    for yy in yrs:
        if yy != 2019:
            q['d%d' % yy] = (q.year == yy).astype(float)
    cols = [y] + ['d%d' % yy for yy in yrs if yy != 2019]
    w = an.demean_within(q, cols, 'flow')
    X, Y = w[cols[1:]].values, w[y].values
    b = np.linalg.pinv(X.T @ X) @ X.T @ Y
    out = {str(yy): round(float(v), 4) for yy, v in zip([yy for yy in yrs if yy != 2019], b)}
    out['2019'] = 0.0
    out['flow_years'] = int(len(q))
    return out


def goes(d):
    t = d[d.k.isin(an.GOES) & (d.year >= 2019)]
    out = {}
    for y, g in t.groupby('year'):
        byv = g.groupby('CTY_NAME').v.sum().sort_values(ascending=False)
        byk = g.groupby('CTY_NAME').kg.sum().sort_values(ascending=False)
        sv, sk = byv / byv.sum(), byk / byk.sum()
        out[int(y)] = {'value_musd': round(float(byv.sum()) / 1e6, 1), 'tonnes': round(float(byk.sum()) / 1000, 0),
                       'top3_value': [[c, round(float(x), 4)] for c, x in sv.head(3).items()],
                       'top3_value_share': round(float(sv.head(3).sum()), 4),
                       'top3_kg': [[c, round(float(x), 4)] for c, x in sk.head(3).items()],
                       'china_value_share': round(float(sv.get('CHINA', 0.0)), 4),
                       'china_kg_share': round(float(sk.get('CHINA', 0.0)), 4)}
    return out


def main():
    d = load()
    p6 = panel(d, 'k')
    T, CAP, CON = an.TRANSFORMERS, an.CAPITAL_CTL, an.CONTAMINATED
    res = {'filing': 'buildout-study/AMENDMENT_US_2026.md', 'source': 'US Census, general imports, HS10',
           'months': int(d.month.nunique()), 'last_month': str(d.month.max()),
           'countries': int(d.CTY_CODE.nunique()), 'sample_flow_years': int(len(p6)),
           'post_periods': POST_NAMES, 'tests': {}, 'checks': {}}
    R, C = res['tests'], res['checks']
    for tag, ctrl in (('c_vs_motors_pumps_compressors', CON), ('a_vs_filed_machinery', CAP),
                      ('b_vs_construction_only', CONSTRUCTION)):
        R[tag + '_per_unit'] = est(p6, 'lpu', T, ctrl, 'US ' + tag + ' per unit')
    p10 = panel(d, 'I_COMMODITY')
    t10 = sorted(p10.k[p10.k.str[:6].isin(T)].unique())
    c10 = sorted(p10.k[p10.k.str[:6].isin(CON)].unique())
    R['c_per_unit_hs10_lines'] = est(p10, 'lpu', t10, c10, 'US c per unit hs10')
    res['hs10_lines'] = {'transformers': t10, 'motors_pumps_compressors': c10}

    C['own_value_per_unit_rel_2019'] = {'transformers': own_path(p6, T, 'lpu'),
                                        'motors_pumps_compressors': own_path(p6, CON, 'lpu'),
                                        'filed_machinery': own_path(p6, CAP, 'lpu')}
    C['transformers_own_kg_per_unit_rel_2019_hs10'] = own_path(p10, t10, 'lkpu')
    C['transformers_own_value_per_kg_rel_2019_hs10'] = own_path(p10, t10, 'lvkg')
    kp = C['transformers_own_kg_per_unit_rel_2019_hs10']
    C['test2_reading'] = ('partly heavier units' if max(kp.get('2025', 0), kp.get('2026', 0)) > 0.10
                          else 'heavier units do not explain it')
    C['event_study'] = {
        'c_per_unit': an.event_study(p6, 'lpu', {'lines': T, 'controls': CON}, None, label='US ev c'),
        'a_per_unit': an.event_study(p6, 'lpu', {'lines': T, 'controls': CAP}, None, label='US ev a'),
        'b_per_unit': an.event_study(p6, 'lpu', {'lines': T, 'controls': CONSTRUCTION}, None, label='US ev b'),
    }
    C['pretrend_rule'] = {k: {'years_outside_0.05': [y for y in range(2014, 2019) if y in ev and abs(ev[y]['beta']) > 0.05]}
                          for k, ev in C['event_study'].items()}
    for k in C['pretrend_rule']:
        C['pretrend_rule'][k]['did_language_allowed'] = not C['pretrend_rule'][k]['years_outside_0.05']
    tr = p6[p6.k.isin(T)]
    C['kg_coverage_transformers'] = {int(y): round(float((g.kg > 0).mean()), 3) for y, g in tr.groupby('year')}
    C['goes_us_imports'] = goes(d)

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1, default=float)
    for tag, e in R.items():
        if e:
            print('%-40s ' % tag + '  '.join('%s %+.3f p=%.3f' % (e['period_names'][n], v['beta'], v['p_wild_line'])
                                              for n, v in e['coefs'].items()))
    print('test 2:', C['test2_reading'], {y: kp[y] for y in ('2021', '2022', '2023', '2024', '2025', '2026') if y in kp})
    print('pretrend:', {k: v['did_language_allowed'] for k, v in C['pretrend_rule'].items()})
    print('wrote', OUT, '| months', res['months'], '| last', res['last_month'], '| countries', res['countries'])


if __name__ == '__main__':
    main()
