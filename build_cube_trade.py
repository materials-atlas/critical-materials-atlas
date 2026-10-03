# -*- coding: utf-8 -*-
"""The monthly trade pipeline, as cube rows. The sixth ingest.

WHY
Measured across every builder in the repository: 8 read the cube, 4 read the trade pipeline, and
ZERO read both. They share sources and no consumers - two products in one repo. The cost is
concrete: "what did this corridor ship last quarter against its ten-year average?" has no home,
because the ten-year average lives in the cube and last quarter lives in flows_reconciled.

WHAT IS AND IS NOT MERGED - REWRITTEN 3 OCT 2026
Until today this file said the grains "genuinely differ", and that forcing them into one shape
would mean "either a partner column that is null on every production row, or discarding the
bilateral detail". That was written on 13 September and it stopped being true on 2 October, when
COUNTERPART_AREA entered the cube: there IS a partner column now, production rows are not null in
it - they carry W1, the code for "all partners", as 3.0M rows already do - and the dilemma the
paragraph described had already been solved for three weeks. The comment outlived its reason, and
was still being quoted as a reason. So the monthly flows now enter BILATERALLY, at their own grain.

WHY THE PARTNER-LESS TOTALS ARE GONE, NOT KEPT BESIDE THEM
This repository's recurring fault is a total stored next to the components it is made of, where one
careless sum double counts: Comtrade's motCode, Comext's EU aggregate reporter, WLD beside the
countries in REF_AREA. The rule settled for the cube is store the parts and derive the aggregates.
So reporter-month totals are no longer emitted for this source at all. A consumer that wants one
gets it from cube_query.totals(), which refuses an aggregate/component mix; a consumer that groups
by country and sums gets the identical number it got before, because the parts add up to the total.

WHAT STILL STAYS OUT, AND WHY IT IS NOT A GRAIN PROBLEM
flows_reconciled keeps the columns that describe HOW a number was made rather than what was
observed - cif_fob_markup_raw, rel_var_exporter, w_exp_share, uv_flag and the rest. Those are
working notes of the method, not attributes of an observation. The three that ARE attributes of the
observation come in with it: the reconciliation INTERVAL (both declarations, as value_lo/value_hi
in the row's own unit), the AGREEMENT ratio, and the freight method that produced the correction.
They pass the test an SDMX attribute has to pass - single-valued for the key that identifies the
observation - which the method's internals do not.

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

# STAGE COMES FROM THE CODE LIST, NOT A CONSTANT. Every monthly row used to be written with
# stage='unspecified'. That was harmless while the monthly layer held only metal and ore codes, and
# it silently broke the compound stage the day the seven compound codes arrived (13 Sep 2026):
# 503,751 monthly rows of lithium hydroxide, nickel sulphate and the oxides landed in the cube as
# 'unspecified', sitting next to the metals - which is exactly the tonne-of-oxide-summed-with-a-
# tonne-of-metal error the compound stage exists to prevent. The annual BACI rows were right all
# along; only this path hard-coded the stage. Codes the list does not stage keep 'unspecified', so
# no existing row changes.
import json as _json
_CODES = _json.load(open(os.path.join(ROOT, 'pipeline', 'critical_codes.json'), encoding='utf-8'))['codes']
STAGE_BY_HS6 = {str(c['hs6']): c['stage'] for c in _CODES if c.get('stage')}


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

        def emit(sub, measure, valcol, unit, to_tonnes, src, locol, hicol):
            """One cube row per (country, PARTNER, period, hs6). to_tonnes=None means money.

            Bilateral since 3 Oct 2026. The partner goes in counterpart_area, so REF_AREA x
            COUNTERPART_AREA reads here the same way it already does for Comext and the annual
            world engine. No reporter-month total is emitted - see the header.
            """
            keys = [who, other, 'period', 'hs6', 'material']
            aggs = {'value': (valcol, 'sum')}
            # The interval of a sum is the sum of the ends, so lo/hi are summed over the group.
            # Agreement is a ratio, so it is averaged, never summed.
            if locol and locol in sub.columns:
                aggs['lo'] = (locol, 'sum')
            if hicol and hicol in sub.columns:
                aggs['hi'] = (hicol, 'sum')
            if 'agreement' in sub.columns:
                aggs['agree'] = ('agreement', 'mean')
            if 'cif_fob_method' in sub.columns:
                aggs['method'] = ('cif_fob_method', 'first')
            g = sub.groupby(keys, as_index=False).agg(**aggs)
            fac = to_tonnes or 1.0
            for r in g.itertuples():
                per = int(r.period)
                v = float(r.value)
                lo, hi = getattr(r, 'lo', None), getattr(r, 'hi', None)
                agree, meth = getattr(r, 'agree', None), getattr(r, 'method', None)
                # An interval counts only when BOTH ends exist and actually bracket the point. A
                # half interval is worse than none: it reads as a bound somebody measured.
                ok = (lo is not None and hi is not None
                      and lo == lo and hi == hi and lo <= v <= hi)
                note = []
                if agree is not None and agree == agree:
                    note.append('agreement %.3f' % agree)
                if meth is not None and meth == meth:
                    note.append('freight %s' % meth)
                rows.append({
                    'material': r.material, 'source_group': 'CMA monthly reconciliation',
                    'country_iso3': getattr(r, who), 'counterpart_area': getattr(r, other),
                    'year': per // 100,
                    'freq': 'M', 'period': per,
                    'measure_family': 'trade', 'measure': measure,
                    'flow_direction': 'out' if direction == 'exports' else 'in',
                    'stage': STAGE_BY_HS6.get(str(r.hs6), 'unspecified'), 'code_system': 'HS6', 'native_code': str(r.hs6),
                    'native_label': str(r.hs6), 'sub_commodity': None,
                    'value': v * fac, 'unit': unit,
                    # A weight is a real tonnage and carries its factor and basis. Money is not a
                    # tonnage and must never pretend to be one, so it carries none - and the guard
                    # in build_cube.py enforces exactly that pairing.
                    'value_t': v * to_tonnes if to_tonnes else None,
                    'conversion_factor': to_tonnes, 'basis': 'gross' if to_tonnes else None,
                    'source': src,
                    'series_id': f'CMA:{r.hs6}:{measure}:{getattr(r, who)}:{getattr(r, other)}',
                    'value_lo': float(lo) * fac if ok else None,
                    'value_hi': float(hi) * fac if ok else None,
                    'precision': ' / '.join(note) or None, 'value_flag': None,
                    'obs_status': 'A', 'conf_status': None,
                })

        # Each measure is split by ITS OWN provenance column: a flow can be two-sided on value
        # and one-sided on weight, and the licence follows the number, not the flow.
        # The interval ends differ by measure. Value carries the explicit FOB bracket the
        # reconciliation computed. Weight's two ends ARE the two declarations, because both
        # services weighed the same physical shipment - freight is a cost, not a mass.
        jobs = [(direction, 'qty_recon_kg', 'qty_basis', 'tonnes (metric)', 0.001,
                 '_qty_lo', '_qty_hi')] if have_qty else []
        jobs.append((direction + '_value', 'value_recon_fob', 'basis', 'USD', None,
                     'value_lo_fob', 'value_hi_fob'))
        for measure, valcol, bcol, unit, fac, locol, hicol in jobs:
            sub = f[f[valcol].notna()]
            if not len(sub) or bcol not in sub.columns:
                continue
            if locol == '_qty_lo':
                if set(['qty_exp', 'qty_imp']) <= set(sub.columns):
                    sub = sub.assign(_qty_lo=sub[['qty_exp', 'qty_imp']].min(axis=1),
                                     _qty_hi=sub[['qty_exp', 'qty_imp']].max(axis=1))
                else:
                    locol = hicol = None
            two = sub[sub[bcol] == 'reconciled']
            one = sub[sub[bcol] != 'reconciled']
            if len(two):
                emit(two, measure, valcol, unit, fac, TWO_SIDED, locol, hicol)
            if len(one):
                emit(one, measure, valcol, unit, fac, ONE_SIDED, locol, hicol)
    return rows


if __name__ == '__main__':
    rs = build()
    if rs:
        d = pd.DataFrame(rs)
        print('monthly trade rows for the cube: %d' % len(d))
        print('  %d materials, %d reporters, %d partners, periods %d..%d'
              % (d.material.nunique(), d.country_iso3.nunique(), d.counterpart_area.nunique(),
                 d.period.min(), d.period.max()))
        print('  W1 (partner-less) rows: %d  <- must be 0; the parts are stored, not the total'
              % (d.counterpart_area == 'W1').sum())
        print('  rows carrying an interval: %d of %d' % (d.value_lo.notna().sum(), len(d)))
        print(d.groupby(['source', 'measure']).size().to_string())
    else:
        print('nothing to add - flows_reconciled missing or has no reconciled values')
