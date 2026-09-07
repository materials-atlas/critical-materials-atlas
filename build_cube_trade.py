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

MONEY AND WEIGHT ARE DIFFERENT MEASURES, NOT DIFFERENT COLUMNS
The first version of this file wrote USD under measure='exports'. Every other source in the cube
means TONNES by that word - BGS, BACI and USGS all do. So a customer filtering measure=='exports'
and summing would have added dollars to tonnes and got a number with no meaning, silently. The
cube caught nothing, because nothing was malformed; it was just wrong.

So weight goes under 'exports'/'imports', in tonnes, like every other source. Money goes under
'exports_value'/'imports_value', in USD, where it cannot be mistaken for a quantity. A customer who
wants both joins them on the series key, which is exactly what the key is for.

WEIGHT IS RECONCILED TOO, AND ON BETTER EVIDENCE
Both customs services weigh the same physical shipment, so - unlike value - a weight gap has no
CIF/FOB excuse available. Freight is a cost, not a mass. That makes weight the cleaner of the two
agreement tests, and it is reconciled by the same rule: two sides within 2x -> geometric mean;
further apart -> no number, and both sides stay exposed.

TWO SOURCES, BECAUSE THEY ARE TWO DIFFERENT PRODUCTS
Not every reconciled value is equally ours, and pretending otherwise is what gets a licence wrong.

  - TWO-SIDED (21,290 flows, 36% of value): both customs services declared the shipment, and the
    published number is the output of OUR method - the freight correction, the agreement test, the
    geometric mean of two independent declarations. Nobody else publishes this figure. It is a
    derived statistic and it is ours.

  - ONE-SIDED (109k flows): only one service declared it, so the number is that service's own
    figure, at most deflated by our markup. Calling that "our derivation" would be a fiction, and
    republishing it would be republishing UN Comtrade with our name on it.

So they enter the cube as two SOURCES, which the series key already separates. The two-sided layer
is published; the one-sided layer stays private and ships instead with a retrieval recipe telling
the customer the exact endpoint and parameters to pull it themselves, and why we cannot hand it
over. See licences.py.

ONLY RECONCILED ROWS COME IN. A flow where the two declarations conflict has no single value by
design, and inventing one to fill a cube row would undo the entire point of refusing it. Those
stay in flows_reconciled with both sides exposed.

Run:  python build_cube_trade.py       (also called by build_cube.py)
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
FLOWS = os.path.join(ROOT, 'pipeline', 'data', 'flows_reconciled.parquet')

# The two products, kept apart because they carry different rights. See licences.py.
TWO_SIDED = 'CMA two-sided reconciliation'
ONE_SIDED = 'CMA single-declaration passthrough'


def build():
    if not os.path.exists(FLOWS):
        return []
    f = pd.read_parquet(FLOWS)
    if 'value_recon_fob' not in f.columns:
        return []
    f = f[f.material.notna()]
    have_qty = 'qty_recon_kg' in f.columns

    rows = []
    for direction, who, other in (('exports', 'exporter', 'importer'),
                                  ('imports', 'importer', 'exporter')):

        def emit(sub, measure, valcol, unit, to_tonnes, src):
            """One cube row per (country, period, hs6). to_tonnes=None means this is money."""
            g = (sub.groupby([who, 'period', 'hs6', 'material'], as_index=False)
                    .agg(value=(valcol, 'sum'), n_partners=(other, 'nunique')))
            for r in g.itertuples():
                per = int(r.period)
                v = float(r.value)
                rows.append({
                    'material': r.material, 'source_group': 'CMA monthly reconciliation',
                    'country_iso3': getattr(r, who), 'year': per // 100,
                    'freq': 'M', 'period': per,
                    'measure_family': 'trade', 'measure': measure,
                    'flow_direction': 'out' if direction == 'exports' else 'in',
                    'stage': 'unspecified', 'code_system': 'HS6', 'native_code': str(r.hs6),
                    'native_label': str(r.hs6), 'sub_commodity': None,
                    'value': v * (to_tonnes or 1.0), 'unit': unit,
                    # A weight is a real tonnage and carries its factor and basis. Money is not a
                    # tonnage and must never pretend to be one, so it carries none - and the guard
                    # in build_cube.py enforces exactly that pairing.
                    'value_t': v * to_tonnes if to_tonnes else None,
                    'conversion_factor': to_tonnes, 'basis': 'gross' if to_tonnes else None,
                    'source': src,
                    'series_id': f'CMA:{r.hs6}:{measure}:{getattr(r, who)}',
                    'precision': f'{r.n_partners} partners reconciled', 'value_flag': None,
                    'obs_status': 'A', 'conf_status': None,
                })

        # Each measure is split by ITS OWN provenance column: a flow can be two-sided on value
        # and one-sided on weight, and the licence follows the number, not the flow.
        jobs = [(direction, 'qty_recon_kg', 'qty_basis', 'tonnes (metric)', 0.001)] if have_qty else []
        jobs.append((direction + '_value', 'value_recon_fob', 'basis', 'USD', None))
        for measure, valcol, bcol, unit, fac in jobs:
            sub = f[f[valcol].notna()]
            if not len(sub) or bcol not in sub.columns:
                continue
            two = sub[sub[bcol] == 'reconciled']
            one = sub[sub[bcol] != 'reconciled']
            if len(two):
                emit(two, measure, valcol, unit, fac, TWO_SIDED)
            if len(one):
                emit(one, measure, valcol, unit, fac, ONE_SIDED)
    return rows


if __name__ == '__main__':
    rs = build()
    if rs:
        d = pd.DataFrame(rs)
        print('monthly trade rows for the cube: %d' % len(d))
        print('  %d materials, %d countries, periods %d..%d'
              % (d.material.nunique(), d.country_iso3.nunique(), d.period.min(), d.period.max()))
        print(d.groupby(['source', 'measure']).size().to_string())
    else:
        print('nothing to add - flows_reconciled missing or has no reconciled values')
