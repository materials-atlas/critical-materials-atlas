# -*- coding: utf-8 -*-
"""The monthly trade pipeline, as cube rows. The sixth ingest.

WHY
Measured across every builder in the repository: 8 read the cube, 4 read the trade pipeline, and
ZERO read both. They share sources and no consumers - two products in one repo. The cost is
concrete: "what did this corridor ship last quarter against its ten-year average?" has no home,
because the ten-year average lives in the cube and last quarter lives in flows_reconciled.

WHAT IS AND IS NOT MERGED
The grains genuinely differ. The cube is one country, one period, one material - trade is already
summed over partners. flows_reconciled is exporter x importer x month. Forcing them into one shape
would mean either a partner column that is null on every production row, or discarding the
bilateral detail that makes the monthly data worth having.

So this brings the monthly flows in AT THE CUBE'S OWN GRAIN - aggregated to reporter-month,
exactly as the cube already treats BACI - and leaves flows_reconciled as the bilateral detail,
joinable on (country, period, native_code). One question each, neither answer damaged.

FREQ WAS ALREADY THERE
The SDMX structure we published declares a FREQ dimension and we have only ever written 'A' into
it. Monthly rows are 'M'. That is not a coincidence: the standard demanded the dimension before we
had a use for it, which is what a standard is for.

ONLY RECONCILED ROWS COME IN. A flow where the two declarations conflict has no single value by
design, and inventing one to fill a cube row would undo the entire point of refusing it. Those
stay in flows_reconciled with both sides exposed.

Run:  python build_cube_trade.py       (also called by build_cube.py)
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
FLOWS = os.path.join(ROOT, 'pipeline', 'data', 'flows_reconciled.parquet')


def build():
    if not os.path.exists(FLOWS):
        return []
    f = pd.read_parquet(FLOWS)
    # value_recon_fob is NULL exactly where the two sides disagreed: that is the refusal, and it
    # must not be back-filled here.
    col = 'value_recon_fob' if 'value_recon_fob' in f.columns else None
    if col is None:
        return []
    f = f[f[col].notna() & f.material.notna()]
    if not len(f):
        return []

    rows = []
    for direction, who, other in (('exports', 'exporter', 'importer'),
                                  ('imports', 'importer', 'exporter')):
        g = (f.groupby([who, 'period', 'hs6', 'material'], as_index=False)
              .agg(value=(col, 'sum'), n_partners=(other, 'nunique')))
        for r in g.itertuples():
            per = int(r.period)
            rows.append({
                'material': r.material, 'source_group': 'CMA monthly reconciliation',
                'country_iso3': getattr(r, who), 'year': per // 100,
                'freq': 'M', 'period': per,
                'measure_family': 'trade', 'measure': direction,
                'flow_direction': 'out' if direction == 'exports' else 'in',
                'stage': 'unspecified', 'code_system': 'HS6', 'native_code': str(r.hs6),
                'native_label': str(r.hs6), 'sub_commodity': None,
                'value': float(r.value), 'unit': 'USD',
                # USD is not a tonnage and must not pretend to be one: no factor, no basis, so
                # the value_t guard in build_cube.py leaves it alone rather than inventing weight.
                'value_t': None, 'conversion_factor': None, 'basis': None,
                'source': 'CMA monthly mirror reconciliation',
                'series_id': f'CMA:{r.hs6}:{direction}:{getattr(r, who)}',
                'precision': f'{r.n_partners} partners reconciled', 'value_flag': None,
                'obs_status': 'A', 'conf_status': None,
            })
    return rows


if __name__ == '__main__':
    rs = build()
    if rs:
        d = pd.DataFrame(rs)
        print('monthly trade rows for the cube: %d' % len(d))
        print('  %d materials, %d countries, periods %d..%d'
              % (d.material.nunique(), d.country_iso3.nunique(), d.period.min(), d.period.max()))
        print(d.groupby('measure').size().to_string())
    else:
        print('nothing to add - flows_reconciled missing or has no reconciled values')
