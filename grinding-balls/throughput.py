# -*- coding: utf-8 -*-
"""Grinding balls, step 2: the throughput test (grinding-balls/PREREGISTRATION.md).

In the tier-A countries from the gate, does the growth of forged-ball apparent consumption track
the growth of ore milled?  dlog AC_it = b * dlog Q_it + country FE + year FE.
Every pass condition, band and control was filed before this ran. Appends to out/grinding_balls.json.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import duckdb  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.formula.api as smf  # noqa: E402
import baci  # noqa: E402

YEARS = list(range(2002, 2025))
ORE = {'copper': (0.0060, 0.85), 'gold': (1.5e-6, 0.88), 'leadzinc': (0.06, 0.85)}
BETA_BAND, LOO_BAND = (0.4, 1.5), (0.3, 1.7)
SCREEN = (0.4, 3.0)
OUT = os.path.join(ROOT, 'out', 'grinding_balls.json')


def wmedian(vals, weights):
    pairs = sorted(zip(vals, weights))
    half, acc = sum(weights) / 2.0, 0.0
    for v, w in pairs:
        acc += w
        if acc >= half:
            return v
    return pairs[-1][0]


def apparent(con, codes, num2iso, basis='q'):
    """AC (imports - exports, floored at 0) by iso-year for a set of HS6 codes, screened per code-year."""
    acc = {}
    for yr in YEARS:
        p = baci.path(yr, 'HS02').replace(os.sep, '/')
        for code in codes:
            flows = [f for f in con.execute("select i, j, v, q from read_parquet('%s') where k='%s'" % (p, code)).fetchall() if f[3]]
            if not flows:
                continue
            med = wmedian([f[2] / f[3] for f in flows], [f[3] for f in flows])
            for i, j, v, q in flows:
                if not (SCREEN[0] * med <= v / q <= SCREEN[1] * med):
                    continue
                x = q if basis == 'q' else v
                ej, ei = num2iso.get(str(j)), num2iso.get(str(i))
                if ej:
                    acc.setdefault((ej, yr), [0.0, 0.0])[0] += x
                if ei:
                    acc.setdefault((ei, yr), [0.0, 0.0])[1] += x
    return {k: max(0.0, m - x) for k, (m, x) in acc.items()}


def series(con, material_sql):
    rows = con.execute("""select country_iso3, year, material, sum(value_t) from read_parquet(?)
        where source='BGS World Mineral Statistics' and stage='mine' and measure='production'
          and material in (%s) and year between 2002 and 2024 and country_iso3 is not null group by 1,2,3""" % material_sql,
                       [os.path.join(ROOT, 'out', 'cube.parquet')]).fetchall()
    return rows


def ore_milled(con):
    q = {}
    for iso, yr, mat, t in series(con, "'copper','gold','lead','zinc'"):
        g = 'leadzinc' if mat in ('lead', 'zinc') else mat
        q[(iso, yr)] = q.get((iso, yr), 0.0) + (t or 0.0) / (ORE[g][0] * ORE[g][1])
    return q


def panel(ac, q, isos, extra=None):
    rows = []
    for iso in isos:
        for yr in YEARS[1:]:
            a1, a0 = ac.get((iso, yr), 0), ac.get((iso, yr - 1), 0)
            q1, q0 = q.get((iso, yr), 0), q.get((iso, yr - 1), 0)
            r = {'iso': iso, 'year': yr, 'ok': a1 > 0 and a0 > 0 and q1 > 0 and q0 > 0}
            if r['ok']:
                r['dac'], r['dq'] = math.log(a1 / a0), math.log(q1 / q0)
                if extra:
                    e1, e0 = extra.get((iso, yr)), extra.get((iso, yr - 1))
                    r['dx'] = math.log(e1 / e0) if e1 and e0 else np.nan
            rows.append(r)
    return pd.DataFrame(rows)


def fit(df, formula, var='dq'):
    d = df.dropna(subset=[c for c in ('dac', 'dq', 'dx') if c in formula]).reset_index(drop=True)
    m_cl = smf.ols(formula, d).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(d['iso'])[0]}, use_t=True)
    tcode = d['year'] - d['year'].min()
    m_dk = smf.ols(formula, d).fit(cov_type='hac-groupsum', cov_kwds={'time': tcode.values, 'maxlags': 2}, use_t=True)
    b = m_cl.params[var]
    ci = m_cl.conf_int().loc[var].tolist()
    return {'_raw': {'beta': float(b), 'p': float(m_cl.pvalues[var]), 't': float(m_cl.tvalues[var])},'beta': round(b, 3), 'se_cluster': round(m_cl.bse[var], 3), 'p_cluster': round(m_cl.pvalues[var], 4),
            'ci95_cluster': [round(ci[0], 3), round(ci[1], 3)], 't_cluster': round(m_cl.tvalues[var], 2),
            'se_driscoll_kraay': round(m_dk.bse[var], 3), 'p_driscoll_kraay': round(m_dk.pvalues[var], 4),
            'n': int(m_cl.nobs), 'countries': int(d['iso'].nunique()), '_model': m_cl}


def main():
    doc = json.load(open(OUT, encoding='utf-8'))
    tier_a = [r['iso3'] for r in doc['countries'] if r['tier'] == 'A']
    con = duckdb.connect()
    cc = baci.countries()
    num2iso = {str(k): v for k, v in cc['iso3'].items() if v}
    q = ore_milled(con)
    ac = apparent(con, ['732611'], num2iso)
    FE = ' + C(iso) + C(year)'

    base = panel(ac, q, tier_a)
    dropped = int((~base['ok']).sum())
    main_fit = fit(base[base['ok']], 'dac ~ dq' + FE)
    cond1 = BETA_BAND[0] <= main_fit['_raw']['beta'] <= BETA_BAND[1] and main_fit['_raw']['p'] < 0.05

    loo = {}
    for iso in tier_a:
        sub = base[base['ok'] & (base['iso'] != iso)]
        loo[iso] = fit(sub, 'dac ~ dq' + FE)['_raw']['beta']
    cond2 = all(LOO_BAND[0] <= b <= LOO_BAND[1] for b in loo.values())

    cem = json.load(open(os.path.join(HERE, 'cement_usgs_kt.json'), encoding='utf-8'))['kt']
    cemd = {(iso, int(y)): v for iso, s in cem.items() for y, v in s.items() if v}
    hr = panel(ac, q, tier_a, extra=cemd)
    hr = hr[hr['ok'] & (hr['year'] <= 2023)]
    hr_fit = fit(hr, 'dac ~ dq + dx' + FE)
    m = hr_fit.pop('_model')
    t_cem_raw = float(m.tvalues['dx'])
    t_cem = round(t_cem_raw, 2)
    hr_fit.update({'beta_cement': round(float(m.params['dx']), 3), 't_cement': t_cem,
                   'p_cement': round(float(m.pvalues['dx']), 4)})
    cond3 = (BETA_BAND[0] <= hr_fit['_raw']['beta'] <= BETA_BAND[1]) and abs(hr_fit['_raw']['t']) > abs(t_cem_raw)

    ac_pl = apparent(con, ['731815'], num2iso)
    pl = panel(ac_pl, q, tier_a)
    pl_fit = fit(pl[pl['ok']], 'dac ~ dq' + FE)
    cond4 = not (BETA_BAND[0] <= pl_fit['_raw']['beta'] <= BETA_BAND[1]) or pl_fit['_raw']['p'] >= 0.05

    iron = {(iso, yr): t for iso, yr, mat, t in series(con, "'iron'") if t}
    au = panel(ac, q, ['AUS'], extra=iron)
    au = au[au['ok']].dropna(subset=['dx'])
    m_au = smf.ols('dac ~ dx + dq', au).fit(cov_type='HC1', use_t=True)
    ci_au = m_au.conf_int().loc['dx'].tolist()
    neg = {'beta_iron': round(float(m_au.params['dx']), 3), 'ci95_hc1': [round(ci_au[0], 3), round(ci_au[1], 3)],
           'beta_q': round(float(m_au.params['dq']), 3), 'n': int(m_au.nobs)}
    cond5 = ci_au[0] <= 0 <= ci_au[1]

    # robustness the filing names as automatic-fail checks
    lv = []
    for iso in tier_a:
        for yr in YEARS:
            a, qq = ac.get((iso, yr), 0), q.get((iso, yr), 0)
            if a > 0 and qq > 0:
                lv.append({'iso': iso, 'year': yr, 'dac': math.log(a), 'dq': math.log(qq)})
    lv_fit = fit(pd.DataFrame(lv), 'dac ~ dq' + FE)
    acv = apparent(con, ['732611'], num2iso, basis='v')
    v = panel(acv, q, tier_a)
    v_fit = fit(v[v['ok']], 'dac ~ dq' + FE)
    acp = apparent(con, ['732611', '732591'], num2iso)
    pp = panel(acp, q, tier_a)
    pp_fit = fit(pp[pp['ok']], 'dac ~ dq' + FE)
    for f in (main_fit, lv_fit, v_fit, pp_fit, pl_fit, hr_fit):
        f.pop('_model', None)
        f.pop('_raw', None)

    conds = {'1_beta_in_band_and_significant': bool(cond1), '2_leave_one_out_in_band': bool(cond2),
             '3_horse_race_cement': bool(cond3), '4_placebo_731815_fails': bool(cond4),
             '5_australia_iron_ore_ci_includes_zero': bool(cond5)}
    passed = all(conds.values())
    doc['throughput_test'] = {
        'tier_a': tier_a, 'years': [YEARS[1], YEARS[-1]], 'dropped_zero_ac_country_years': dropped,
        'main': main_fit, 'leave_one_out_beta': {k: round(b, 3) for k, b in loo.items()},
        'horse_race_cement_2003_2023': hr_fit, 'placebo_731815': pl_fit, 'negative_control_australia': neg,
        'robustness': {'levels_with_fe': lv_fit, 'values_not_tonnes': v_fit, 'pooled_with_732591': pp_fit},
        'conditions': conds, 'result': 'PASS' if passed else 'FAIL',
    }
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    def show(label, f):
        print('%-26s beta %6.3f  se %5.3f  p %.4f  ci [%6.3f, %6.3f]  DK p %.4f  n %d' % (
            label, f['beta'], f['se_cluster'], f['p_cluster'], f['ci95_cluster'][0], f['ci95_cluster'][1],
            f['p_driscoll_kraay'], f['n']))
    show('MAIN dlog AC ~ dlog Q', main_fit)
    print('  dropped country-years (AC=0):', dropped)
    print('  leave-one-out:', {k: round(b, 2) for k, b in loo.items()})
    show('horse race (with cement)', hr_fit)
    print('  cement beta %.3f t %.2f p %.4f | Q t %.2f' % (hr_fit['beta_cement'], t_cem, hr_fit['p_cement'], hr_fit['t_cluster']))
    show('placebo 731815', pl_fit)
    print('negative control AUS: iron beta %.3f ci %s  (Q beta %.3f, n %d)' % (neg['beta_iron'], neg['ci95_hc1'], neg['beta_q'], neg['n']))
    show('robust: levels + FE', lv_fit)
    show('robust: values', v_fit)
    show('robust: + cast 732591', pp_fit)
    print('CONDITIONS', conds)
    print('RESULT', doc['throughput_test']['result'])


if __name__ == '__main__':
    main()
