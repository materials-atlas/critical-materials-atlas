# -*- coding: utf-8 -*-
"""Amendment B: the EU customs record to July 2026. Runs the tests filed in AMENDMENT_EU_2026.md.

Committed before its first run on the downloaded data. Reuses the estimator of analysis.py unchanged
(flow and year effects, line-level wild bootstrap with the null imposed, each estimate on its own
seeded stream), so the method is the study's; only the data and the periods differ. Writes every number
to out/buildout_eu.json.

Usage:  python buildout-study/analysis_eu.py
"""
import glob
import json
import math
import os
import sys

import duckdb
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import analysis as an                                          # the study's estimator, unchanged

OUT = os.path.join(ROOT, 'out', 'buildout_eu.json')
DATA = os.path.join(HERE, 'eu_data', 'comext_*.parquet')
POST = ((2021, 2022), (2023, 2024), (2025,), (2026,))          # filed: four post periods
POST_NAMES = ['2021-22', '2023-24', '2025', '2026 (Jan-Jul)']
MIN_EUR = 100000.0                                             # filed clarification 1
CONSTRUCTION = ['842810', '842649', '847420', '847431']
EU27 = {'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 'LV',
        'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE'}


def load(trade_type='E'):
    con = duckdb.connect()
    q = """
      select REPORTER as rep, PARTNER as par, FLOW as fl, substr(PRODUCT_NC,1,6) as k,
             PRODUCT_NC as cn8, cast(substr(PERIOD,1,4) as int) as year,
             sum(try_cast(VALUE_EUR as double)) as v, sum(try_cast(QUANTITY_KG as double)) as kg,
             sum(case when SUPPL_UNIT <> 'NO_SU' and try_cast(QUANTITY_SUPPL_UNIT as double) > 0
                      then try_cast(QUANTITY_SUPPL_UNIT as double) end) as n_items,
             sum(case when SUPPL_UNIT <> 'NO_SU' and try_cast(QUANTITY_SUPPL_UNIT as double) > 0
                      then try_cast(VALUE_EUR as double) end) as v_items,
             sum(case when SUPPL_UNIT <> 'NO_SU' and try_cast(QUANTITY_SUPPL_UNIT as double) > 0
                      then try_cast(QUANTITY_KG as double) end) as kg_items,
             count(distinct PERIOD) as months
      from read_parquet(?) where TRADE_TYPE = ? and FLOW in ('1','2')
        and cast(substr(PERIOD,5,2) as int) between 1 and 12   -- never the YYYY52 yearly totals
        and REPORTER <> 'GB' and PARTNER not in ('GB', 'XI')   -- deviation 5: EU27 on both sides, all years
      group by all"""
    d = con.execute(q, [DATA.replace('\\', '/'), trade_type]).df()
    months = con.execute("select count(distinct PERIOD) from read_parquet(?)", [DATA.replace('\\', '/')]).fetchone()[0]
    last = con.execute("select max(PERIOD) from read_parquet(?)", [DATA.replace('\\', '/')]).fetchone()[0]
    return d, int(months), last


def panel(d, level='k'):
    """One row per flow-year at the six-digit (or eight-digit) level, with the filed sample rules."""
    g = d.groupby(['rep', 'par', 'fl', level, 'year'], as_index=False).agg(
        v=('v', 'sum'), kg=('kg', 'sum'), n_items=('n_items', 'sum'), v_items=('v_items', 'sum'),
        kg_items=('kg_items', 'sum'))
    thr = np.where(g.year == 2026, MIN_EUR * 7 / 12, MIN_EUR)
    g = g[(g.v >= thr) & (g.kg > 0)].copy()
    g['uv'] = g.v / (g.kg / 1000.0)                            # EUR per tonne
    med = g.groupby([level, 'year']).uv.transform('median')
    g = g[(g.uv >= 0.1 * med) & (g.uv <= 10 * med)].copy()
    g['k'] = g[level]
    g['flow'] = g.rep + '|' + g.par + '|' + g.fl + '|' + g[level]
    g['exp'] = g.rep                                           # cluster: declaring member state
    g['luv'], g['lq'] = np.log(g.uv), np.log(g.kg)
    ok = (g.n_items > 0) & (g.v_items > 0) & (g.kg_items > 0)
    g['pi'] = np.where(ok, g.v_items / g.n_items.where(ok), np.nan)
    g['kpi'] = np.where(ok, g.kg_items / g.n_items.where(ok), np.nan)
    # deviation 6: the filed 0.1-10x band, applied to value per item as it is to value per tonne
    pmed = g.groupby([level, 'year']).pi.transform('median')
    band = (g.pi >= 0.1 * pmed) & (g.pi <= 10 * pmed)
    g['lpi'] = np.where(ok & band, np.log(g.pi), np.nan)
    g['lkpi'] = np.where(ok & band, np.log(g.kpi), np.nan)
    return g.reset_index(drop=True)


def est(df, yvar, lines, controls, label):
    sub = df.dropna(subset=[yvar])
    e = an.estimate(sub, yvar, {'lines': lines, 'controls': controls}, label, None, post=POST)
    if not e:
        return None
    e['period_names'] = dict(zip(['TxP1', 'TxP2', 'TxP3', 'TxP4'], POST_NAMES))
    return e


def goes_shares(d):
    t = d[(d.k.isin(an.GOES)) & (d.fl == '1') & (d.year >= 2019)]
    out = {}
    for y, g in t.groupby('year'):
        by = g.groupby('par').v.sum().sort_values(ascending=False)
        sh = by / by.sum()
        out[int(y)] = {'value_meur': round(float(by.sum()) / 1e6, 1),
                       'china_share': round(float(sh.get('CN', 0.0)), 4),
                       'russia_share': round(float(sh.get('RU', 0.0)), 4),
                       'japan_share': round(float(sh.get('JP', 0.0)), 4),
                       'korea_share': round(float(sh.get('KR', 0.0)), 4),
                       'top3_share': round(float(sh.head(3).sum()), 4),
                       'top3': [[p, round(float(x), 4)] for p, x in sh.head(3).items()],
                       'partners_above_1pct': int((sh > 0.01).sum())}
    return out


def main():
    d, months, last = load('E')
    p6 = panel(d, 'k')
    res = {'filing': 'buildout-study/AMENDMENT_EU_2026.md', 'source': 'Eurostat Comext monthly CN8, extra-EU',
           'months_on_disk': months, 'last_period': last, 'post_periods': POST_NAMES,
           'sample_flow_years': int(len(p6)), 'tests': {}, 'checks': {}}
    T, CAP, CON = an.TRANSFORMERS, an.CAPITAL_CTL, an.CONTAMINATED

    R = res['tests']
    for tag, ctrl in (('c_vs_motors_pumps_compressors', CON), ('a_vs_filed_machinery', CAP),
                      ('b_vs_construction_only', CONSTRUCTION)):
        R[tag] = {'price': est(p6, 'luv', T, ctrl, 'EU ' + tag + ' price'),
                  'volume': est(p6, 'lq', T, ctrl, 'EU ' + tag + ' volume')}
    R['c_per_item'] = est(p6, 'lpi', T, CON, 'EU c per item')
    p8 = panel(d, 'cn8')
    t8 = sorted(p8.k[p8.k.str[:6].isin(T)].unique())
    c8 = sorted(p8.k[p8.k.str[:6].isin(CON)].unique())
    R['c_price_cn8_lines'] = est(p8, 'luv', t8, c8, 'EU c price cn8')
    R['c_per_item_cn8_lines'] = est(p8, 'lpi', t8, c8, 'EU c per item cn8')
    res['cn8_lines'] = {'transformers': t8, 'motors_pumps_compressors': c8}

    C = res['checks']
    C['event_study'] = {
        'c_price': an.event_study(p6, 'luv', {'lines': T, 'controls': CON}, None, label='EU ev c'),
        'c_volume': an.event_study(p6, 'lq', {'lines': T, 'controls': CON}, None, label='EU ev c'),
        'c_per_item': an.event_study(p6.dropna(subset=['lpi']), 'lpi', {'lines': T, 'controls': CON}, None, label='EU ev c item'),
        'a_price': an.event_study(p6, 'luv', {'lines': T, 'controls': CAP}, None, label='EU ev a'),
    }
    for tag, ctrl in (('a', CAP), ('b', CONSTRUCTION)):
        C['event_study'][tag + '_volume'] = an.event_study(p6, 'lq', {'lines': T, 'controls': ctrl}, None, label='EU ev ' + tag)
    C['event_study']['b_price'] = an.event_study(p6, 'luv', {'lines': T, 'controls': CONSTRUCTION}, None, label='EU ev b')
    C['event_study']['c_kg_per_item'] = an.event_study(p6.dropna(subset=['lkpi']), 'lkpi', {'lines': T, 'controls': CON}, None, label='EU ev c kg')
    R['c_kg_per_item'] = est(p6, 'lkpi', T, CON, 'EU c kg per item')
    # Deviation 7, exploratory: each group's OWN weight per item over time, flow effects only (no
    # comparison group), relative to 2019 - so a relative per-item gap can be traced to its side.
    own = {}
    for name, lines in (('transformers', T), ('motors_pumps_compressors', CON)):
        q = p6[p6.k.isin(lines)].dropna(subset=['lkpi']).copy()
        q = q[q.groupby('flow').year.transform('size') > 1]
        yrs = sorted(q.year.unique())
        for y in yrs:
            if y != 2019:
                q['d%d' % y] = (q.year == y).astype(float)
        cols = ['lkpi'] + ['d%d' % y for y in yrs if y != 2019]
        w = an.demean_within(q, cols, 'flow')
        X, Y = w[cols[1:]].values, w['lkpi'].values
        b = np.linalg.pinv(X.T @ X) @ X.T @ Y
        own[name] = {str(y): round(float(v), 4) for y, v in zip([y for y in yrs if y != 2019], b)}
        own[name]['2019'] = 0.0
        own[name]['flow_years'] = int(len(q))
    C['own_kg_per_item_rel_2019'] = own
    C['pretrend_rule'] = {k: {'years_outside_0.05': [y for y in range(2014, 2019) if y in ev and abs(ev[y]['beta']) > 0.05]}
                          for k, ev in C['event_study'].items()}
    for k in C['pretrend_rule']:
        C['pretrend_rule'][k]['did_language_allowed'] = not C['pretrend_rule'][k]['years_outside_0.05']
    items = p6[p6.k.isin(T)]
    C['per_item_coverage'] = {int(y): {'flow_years': int(len(g)), 'with_item_counts': int(g.lpi.notna().sum())}
                              for y, g in items.groupby('year')}
    C['goes_eu_import_shares'] = goes_shares(d)
    di, _, _ = load('I')
    pi = panel(di, 'k')
    C['intra_eu_sensitivity_c_price'] = est(pi, 'luv', T, CON, 'EU intra c price')

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1, default=float)

    def show(tag, e):
        if not e:
            print('%-34s no estimate' % tag)
            return
        print('%-34s ' % tag + '  '.join('%s %+.3f p=%.3f' % (e['period_names'][n], v['beta'], v['p_wild_line'])
                                          for n, v in e['coefs'].items()))
    for tag, v in R.items():
        if isinstance(v, dict) and 'coefs' not in v:
            for side, e in v.items():
                show(tag + ' ' + side, e)
        else:
            show(tag, v)
    print('pretrend:', {k: v['did_language_allowed'] for k, v in C['pretrend_rule'].items()})
    print('wrote', OUT, '| months', months, '| last', last)


if __name__ == '__main__':
    main()
