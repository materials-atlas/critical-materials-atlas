# -*- coding: utf-8 -*-
"""IEA Critical Minerals Dataset, read from the published cube instead of hand-derived CSVs.

Replaces raw/iea/iea_supply_concentration.csv, iea_demand_scenarios.csv and iea_demand_by_tech.csv,
which were derived by hand from the 2025-05 Data Explorer file. Each function reproduces its CSV
exactly from the cube (checked 16 Sep 2026), so the derivation is now code, not a spreadsheet step.
"""
import os

import pandas as pd

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
EDITION = '2025-05'          # the edition the atlas's IEA figures are pinned to
LABEL = {'rare_earths': 'magnets'}   # the atlas calls the IEA's magnet rare earths 'magnets'
# IEA sheet order: the CSVs followed it, and the builders iterate in that order.
SUPPLY_ORDER = ['copper', 'cobalt', 'lithium', 'nickel', 'graphite', 'rare_earths']
DEMAND_ORDER = ['copper', 'cobalt', 'lithium', 'nickel', 'rare_earths', 'graphite']
TECH_ORDER = ['Solar PV', 'Wind', 'Low emissions power generation',
              'Other low emissions power generation', 'Electric vehicles', 'Grid battery storage',
              'Electricity networks', 'Hydrogen technologies', 'Other uses']
_C = None


def _iea():
    global _C
    if _C is None:
        c = pd.read_parquet(os.path.join(ROOT, 'out', 'cube.parquet'),
                            columns=['source', 'source_group', 'material', 'measure', 'stage',
                                     'country_iso3', 'year', 'value', 'native_code', 'sub_commodity'])
        _C = c[(c.source == 'IEA Critical Minerals Dataset')
               & c.source_group.str.startswith('IEA %s:' % EDITION)]
    return _C


def supply_concentration():
    """Rows like iea_supply_concentration.csv: material, stage, top1_country, top1_share, top3_share, total_2024."""
    c = _iea()
    c = c[c.measure == 'production']
    out = []
    for m in SUPPLY_ORDER:
        for stage, stg in (('mining', 'mine'), ('refining', 'processed')):
            s = c[(c.material == m) & (c.stage == stg)]
            world = s[s.country_iso3 == 'WLD'].value.sum()
            g = s[s.country_iso3 != 'WLD'].groupby('country_iso3').value.sum().sort_values(ascending=False)
            if s.empty or not world:
                continue
            out.append({'material': LABEL.get(m, m), 'stage': stage, 'top1_country': g.index[0],
                        'top1_share': round(100 * g.iloc[0] / world, 1),
                        'top3_share': round(100 * g.iloc[:3].sum() / world, 1),
                        'total_2024': round(float(world), 2)})
    return out


def _demand():
    c = _iea()
    return c[c.measure.isin(['demand', 'demand_projection'])]


def demand_scenarios():
    """Rows like iea_demand_scenarios.csv: base_2024 and the 2040/base growth factor per scenario."""
    d = _demand()
    out = []
    for m in DEMAND_ORDER:
        t = d[(d.material == m) & (d.sub_commodity == 'Total demand')]
        if t.empty:
            continue
        base = float(t[t.measure == 'demand'].value.iloc[0])
        g = {s: round(float(t[(t.measure == 'demand_projection') & (t.year == 2040)
                              & t.native_code.str.endswith(':' + s)].value.iloc[0]) / base, 3)
             for s in ('STEPS', 'APS', 'NZE')}
        out.append({'material': LABEL.get(m, m), 'base_2024': round(base, 2),
                    'g_steps': g['STEPS'], 'g_aps': g['APS'], 'g_nze': g['NZE']})
    return out


def demand_by_tech():
    """Rows like iea_demand_by_tech.csv: material, technology, d2024, d2040_aps (end-use rows only)."""
    d = _demand()
    out = []
    for m in DEMAND_ORDER:
        for tech in TECH_ORDER:
            t = d[(d.material == m) & (d.sub_commodity == tech)]
            base = t[t.measure == 'demand'].value
            aps = t[(t.year == 2040) & t.native_code.str.endswith(':APS')].value
            if base.empty or aps.empty:
                continue
            out.append({'material': LABEL.get(m, m), 'technology': tech,
                        'd2024': round(float(base.iloc[0]), 3), 'd2040_aps': round(float(aps.iloc[0]), 3)})
    return out
