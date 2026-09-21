# -*- coding: utf-8 -*-
"""Amendment A, parts A and C: who replaced China in EU imports, and how the six controls compare.

Runs what export-controls/AMENDMENT_A.md files, on the same EU data, windows and codes as analysis.py.
Production is BGS World Mineral Statistics as held in the atlas cube (out/cube.parquet), mean 2021-2023.
Writes out/export_controls_origins.json.  Usage: python export-controls/origins.py
Committed before its first run.
"""
import glob
import json
import os
import sys

import duckdb
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import baci                                                       # noqa: E402  country codes
from analysis import CONTROLS, EU, shift, months                  # noqa: E402  the study's own definitions

OUT = os.path.join(ROOT, 'out', 'export_controls_origins.json')
RES = os.path.join(ROOT, 'out', 'export_controls.json')
# BGS series per treated group, at the stage the amendment names
BGS = {'antimony': ('antimony', 'mine'), 'bismuth': ('bismuth', 'mine'), 'graphite': ('graphite', 'unspecified'),
       'gage': [('gallium', 'processed'), ('germanium', 'processed')], 'magnets': ('rare_earths', 'processed'),
       'hree': ('rare_earths', 'processed')}
PROD_YEARS = (2021, 2022, 2023)
CAND_MIN_T = 10.0                   # tonnes a month
CAND_MULT = 3.0


def eu_by_origin(codes):
    files = sorted(glob.glob(os.path.join(HERE, 'eu_data', 'comext_*.parquet')))
    con = duckdb.connect()
    d = con.execute("""select PERIOD as ym, PARTNER as par, sum(try_cast(QUANTITY_KG as double)) as kg
                       from read_parquet(?) where TRADE_TYPE = 'E' and FLOW = '1'
                         and REPORTER <> 'GB' and PARTNER not in ('GB', 'XI')
                         and list_contains(?, PRODUCT_NC)
                       group by 1, 2""", [files, codes]).df()
    return d[d.ym.str[4:6].astype(int).between(1, 12)]


def production():
    c = pd.read_parquet(os.path.join(ROOT, 'out', 'cube.parquet'),
                        columns=['source', 'measure', 'material', 'stage', 'country_iso3', 'year', 'value_t'])
    c = c[(c.source == 'BGS World Mineral Statistics') & (c.measure == 'production')]
    return c[c.country_iso3.notna() & (c.value_t > 0)]


def prod_table(P, spec):
    specs = spec if isinstance(spec, list) else [spec]
    out = {}
    for mat, stage in specs:
        s = P[(P.material == mat) & (P.stage == stage)]
        # every year 2021-2024 for the "any production recorded" test; the mean over 2021-2023 for size
        recent = set(s[s.year.between(2021, 2024)].country_iso3)
        m = s[s.year.isin(PROD_YEARS)].groupby('country_iso3').value_t.sum() / len(PROD_YEARS)
        out[mat] = {'mean_t': m, 'recorded': recent}
    return out


def main():
    res = {r['control']: r for r in json.load(open(RES, encoding='utf-8'))['results'] if r['importer'] == 'EU'}
    cc = baci.countries()
    i2to3 = {r2: r3 for r2, r3 in zip(cc['iso2'], cc['iso3']) if r2 and r3}
    i3name = dict(zip(cc['iso3'], cc['name']))
    P = production()
    out = {'filing': 'export-controls/AMENDMENT_A.md', 'production_years': list(PROD_YEARS), 'controls': {}}
    for cid, imp, tr, cp, ann, eff, post_end, label in CONTROLS:
        if imp != 'EU':
            continue
        pre = months(shift(ann, -24), shift(ann, -1))
        post = months(shift(eff, 7), shift(eff, 12))
        d = eu_by_origin(EU[tr])
        pv = d.pivot_table(index='par', columns='ym', values='kg', aggfunc='sum').fillna(0.0)
        for m in pre + post:
            if m not in pv.columns:
                pv[m] = 0.0
        pre_t = pv[pre].mean(axis=1) / 1000
        post_t = pv[post].mean(axis=1) / 1000
        ch = (post_t - pre_t).drop('CN', errors='ignore')
        repl = float(ch[ch > 0].sum())
        prod = prod_table(P, BGS[tr])
        rows, cum = [], 0.0
        for par, v in ch[ch > 0].sort_values(ascending=False).items():
            if repl <= 0 or cum >= 0.8 * repl:
                break
            cum += v
            i3 = i2to3.get(par)
            # producer: at least twelve times its post-period monthly EU exports, summed over the series'
            # materials (gallium and germanium together)
            p_mean = sum(float(pr['mean_t'].get(i3, 0.0)) for pr in prod.values())
            recorded = any(i3 in pr['recorded'] for pr in prod.values())
            producer = recorded and p_mean >= 12 * float(post_t[par])
            cand = (not producer) and v >= CAND_MIN_T and (pre_t[par] == 0 or post_t[par] >= CAND_MULT * pre_t[par])
            rows.append({'origin': par, 'iso3': i3, 'name': i3name.get(i3, par),
                         'pre_t_month': round(float(pre_t[par]), 2), 'post_t_month': round(float(post_t[par]), 2),
                         'change_t_month': round(float(v), 2), 'share_of_replacement': round(float(v) / repl, 3),
                         'production_t_year_mean_2021_23': round(p_mean, 1), 'production_recorded_2021_24': recorded,
                         'class': 'producer' if producer else 'non-producer', 'transit_candidate': bool(cand)})
        from_prod = sum(r['change_t_month'] for r in rows if r['class'] == 'producer')
        # part C: world production shares
        world = {mat: float(pr['mean_t'].sum()) for mat, pr in prod.items()}
        cn = {mat: float(pr['mean_t'].get('CHN', 0.0)) for mat, pr in prod.items()}
        n5 = {mat: int(((pr['mean_t'] / world[mat]) >= 0.05).sum() - (1 if cn[mat] / world[mat] >= 0.05 else 0))
              for mat, pr in prod.items() if world[mat] > 0}
        lvl = res[cid]['levels']['treated']
        out['controls'][cid] = {
            'label': label, 'treated': tr, 'pre': [pre[0], pre[-1]], 'post': [post[0], post[-1]],
            'china_t_month': [round(float(pre_t.get('CN', 0.0)), 2), round(float(post_t.get('CN', 0.0)), 2)],
            'others_t_month': [round(float(pre_t.drop('CN', errors='ignore').sum()), 2),
                               round(float(post_t.drop('CN', errors='ignore').sum()), 2)],
            'replacement_t_month': round(repl, 2),
            'replacement_share_from_producers': round(from_prod / repl, 3) if repl > 0 else None,
            'origins': rows,
            'transit_candidates': [r['origin'] for r in rows if r['transit_candidate']],
            'comparison': {
                'china_share_world_production': {m: round(cn[m] / world[m], 3) for m in world if world[m] > 0},
                'other_countries_5pct': n5,
                'china_share_eu_imports_pre': round(lvl['pre']['china_t_per_month'] / lvl['pre']['total_t_per_month'], 3),
                'china_tonnes_after_over_before': round(lvl['post']['china_t_per_month'] / lvl['pre']['china_t_per_month'], 3)
                if lvl['pre']['china_t_per_month'] > 0 else None,
                'unit_value_multiple': round(lvl['post']['unit_value_per_kg'] / lvl['pre']['unit_value_per_kg'], 3)}}
    json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1)
    for cid, c in out['controls'].items():
        print('%-4s %-34s China %s  others %s  replacement %.1f t/m, from producers %s  candidates %s'
              % (cid, c['label'], c['china_t_month'], c['others_t_month'], c['replacement_t_month'],
                 c['replacement_share_from_producers'], c['transit_candidates']))
        for r in c['origins']:
            print('      %-3s %-24s %8.1f -> %8.1f  (+%.1f, %.0f%%)  prod %.0f t/yr  %s%s'
                  % (r['origin'], r['name'][:24], r['pre_t_month'], r['post_t_month'], r['change_t_month'],
                     100 * r['share_of_replacement'], r['production_t_year_mean_2021_23'], r['class'],
                     '  TRANSIT CANDIDATE' if r['transit_candidate'] else ''))
        print('      comparison', c['comparison'])
    print('wrote', OUT)


if __name__ == '__main__':
    main()
