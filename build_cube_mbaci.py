# -*- coding: utf-8 -*-
"""The monthly BACI replication, as cube rows. CEPII's method, month by month, 2017 to the latest month.

WHAT THIS IS
reconcile/monthly_baci.py rebuilds CEPII's BACI (Gaulier & Zignago 2010) from raw UN Comtrade:
CIF/FOB handled as BACI does, the reliability regression (equation 5), the reliability weights
(equation 3), "areas nes" reallocated. Run on the UN's MONTHLY declarations, 2017-01 to the latest
month, every product, with the trust scores taken from the yearly run over 2017-2024 (one set per
edition, as BACI). Summed to years it lands within 10% of BACI V202601 on 76-79% of flows and within
0.1-2.5% on totals (reconcile/MONTHLY_BACI.md, "Step 2"). This file reads the atlas's codes out of
that run: out/monthly_baci_crm.parquet, written on the Lenovo from ~/comtrade/mm_<year>/ (see
MONTHLY_BACI.md for the command). The extract is an engine output, like out/flows_YYYY.json.

WHAT IT ADDS THAT THE CUBE DID NOT HAVE
The monthly layer already in the cube (build_cube_trade.py) is our simpler reconciliation of the
Comtrade cache: geometric mean when two declarations agree within 2x, no number when they do not.
This one is CEPII's rule - every two-sided flow gets a number, weighted by the two reporters'
reliability - over the whole reporter universe, from 2017. The two are two compilations of the same
flows: two observations, not a conflict, separated by `source`. Neither replaces the other.

ONE ROW PER FLOW, FROM THE EXPORTER'S SIDE
BACI is directional (exporter -> importer), so each flow enters once: REF_AREA the exporter,
COUNTERPART_AREA the importer, flow_direction 'out'. Imports are the same rows read by counterpart.
Writing an 'imports' copy too would store every flow twice and invite the double count this repo
keeps paying for.

MEASURES: money and weight apart, as everywhere in the cube.
  exports_value  USD, currency_denom USD
  exports        metric tonnes (the engine's reconciled kg / 1000), basis gross
value_lo / value_hi carry the two declarations when both exist (the reconciled value lies between
them by construction; an interval that does not bracket the point is dropped, not half-kept).

TWO SOURCES, BECAUSE THE LICENCE FOLLOWS THE NUMBER (licences.py)
  'CMA monthly BACI (two-sided)'         both customs services declared the flow; the figure is our
                                         reliability-weighted mix of the two. Derived, ours, published.
  'CMA monthly BACI (single declaration)' only one service declared it, so the figure is that
                                         service's own. Withheld, with a retrieval recipe.

STATUS
Values: obs_status 'A'. Tonnes: 'A' when every declared weight behind them was reported, 'E' when
one was a UN estimate (see the weight block below). The months from 2026-05 are thin (reporters
still to file: 3.9m flows in 2026-07 against ~5m, 0.4m in 2026-09): what is missing is flows, not
precision of the ones present, so the rows are normal observations of a partial month. Consumers
comparing months must use the same reporter set.

CHINA FILES NO MONTHLY DATA FOR 2025-2026 (zero files in the UN bulk corpus, checked 18 Nov 2026).
Flows into and out of China in those months exist only where the partner declared them, so the
atlas codes' flows to China fall from $92.8bn (2024) to $35.3bn (2025) in this layer. That is a
reporting gap, not a trade collapse; never read a China series across the 2024/2025 line.

Hafnium (811231) is absent by construction: it exists from HS 2022, and this series is in HS 2017,
where hafnium sits inside 811292.

Run:  python build_cube_mbaci.py     (called by build_cube.py; standalone for inspection)
"""
import json
import os
import sys

import pandas as pd

ROOT = os.environ.get('ATLAS_ROOT', os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import schema        # the one ISO door
import concordance   # the one HS6 -> material map

EXTRACT = os.path.join(ROOT, 'out', 'monthly_baci_crm.parquet')
TWO_SIDED = 'CMA monthly BACI (two-sided)'
ONE_SIDED = 'CMA monthly BACI (single declaration)'
_CODES = json.load(open(os.path.join(ROOT, 'pipeline', 'critical_codes.json'), encoding='utf-8'))['codes']
STAGE_BY_HS6 = {str(c['hs6']): c['stage'] for c in _CODES if c.get('stage')}


def _iso3(s):
    m = {c: schema.iso3(c) for c in s.dropna().unique()}
    out = s.map(m)
    ok = out.str.len().eq(3) & out.str.isalpha() & out.str.isupper()
    return out.where(ok)


def build():
    if not os.path.exists(EXTRACT):
        return pd.DataFrame()
    f = pd.read_parquet(EXTRACT)
    f['exporter'] = _iso3(f['exporter'])
    f['importer'] = _iso3(f['importer'])
    f = f[f.exporter.notna() & f.importer.notna() & (f.exporter != f.importer)]
    f['material'] = f['hs6'].map(lambda h: concordance.material_for(h, 6))
    f = f[f.material.notna()]
    f['source'] = f['basis'].map(lambda b: TWO_SIDED if b == 'both' else ONE_SIDED)
    period = f['period'].astype('int64')
    common = pd.DataFrame({
        'material': f.material, 'source_group': 'CMA monthly BACI replication',
        'country_iso3': f.exporter, 'counterpart_area': f.importer,
        'year': period // 100, 'freq': 'M', 'period': period,
        'measure_family': 'trade', 'flow_direction': 'out',
        'stage': f.hs6.map(lambda h: STAGE_BY_HS6.get(h, 'unspecified')),
        'code_system': 'HS6', 'native_code': f.hs6, 'native_label': f.hs6, 'sub_commodity': None,
        'source': f.source, 'precision': None, 'value_flag': None, 'source_obs_status': None,
        'obs_status': 'A', 'conf_status': None, 'native_group': None, 'native_country': f.exporter,
    })

    def interval(lo, hi, v):
        both = lo.notna() & hi.notna()
        a, b = lo.where(lo <= hi, hi), hi.where(lo <= hi, lo)
        ok = both & (a <= v * (1 + 1e-9)) & (v <= b * (1 + 1e-9))
        return a.where(ok), b.where(ok)

    lo_v, hi_v = interval(f.vx, f.vm, f.v)
    money = common.assign(measure='exports_value', value=f.v.astype(float), unit='USD',
                          currency_denom='USD', value_t=None, conversion_factor=None, basis=None,
                          value_lo=lo_v, value_hi=hi_v)
    # WEIGHT ONLY WITH ITS PROVENANCE. The UN fills missing monthly net weights with its own
    # estimates and flags them (isNetWgtEstimated); the engine reads netWgt without the flag. China
    # 2017, bauxite from Guinea: the monthly files carry 4.8 Mt ESTIMATED where the yearly file
    # carries 27.6 Mt REPORTED, same $1,453m. So the extract must carry est_x / est_m (whether the
    # exporter's / importer's declared weight was a UN estimate, ~/comtrade/est_flags.py), a tonne
    # built on an estimate enters with obs_status 'E', and without the flags no tonnes enter at all.
    if {'est_x', 'est_m'} <= set(f.columns):
        w = f.q.notna() & (f.q > 0)
        ex = f.est_x.fillna(0).astype(bool) & f.qx.notna()
        em = f.est_m.fillna(0).astype(bool) & f.qm.notna()
        est = (ex | em) & w
        lo_q, hi_q = interval(f.qx / 1000.0, f.qm / 1000.0, f.q / 1000.0)
        weight = common[w].assign(measure='exports', value=(f.q[w] / 1000.0).astype(float),
                                  unit='tonnes (metric)', currency_denom='_T',
                                  value_t=(f.q[w] / 1000.0).astype(float), conversion_factor=1.0,
                                  basis='gross', value_lo=lo_q[w], value_hi=hi_q[w])
        weight['obs_status'] = est[w].map({True: 'E', False: 'A'})
    else:
        print('  monthly BACI: no estimated-weight flags in the extract - tonnes NOT ingested')
        weight = common.iloc[0:0].assign(measure='exports', value=None, unit=None, currency_denom=None,
                                         value_t=None, conversion_factor=None, basis=None,
                                         value_lo=None, value_hi=None)
    # How far apart the two declarations were, stated on the row. BACI's mix of two declarations
    # 50x apart is a number nobody measured (2023: Mexico's 65 kt of US helium against the US's
    # 0.3 kt gives 38 kt; China's $340m of nickel oxide to Korea against Korea's $1m). The interval
    # already holds both ends; this says it in words, so a reader of one row cannot miss it.
    for d in (money, weight):
        r = (d.value_hi / d.value_lo).where(d.value_lo > 0)
        d['precision'] = ('declarations x' + r.round(1).astype(str) + ' apart').where(r >= 2)
    if len(weight):
        e = weight['obs_status'] == 'E'
        weight.loc[e, 'precision'] = weight.loc[e, 'precision'].fillna('').radd('UN-estimated net weight; ').str.rstrip('; ')
    out = pd.concat([money, weight], ignore_index=True)
    out['series_id'] = ('CMA-MBACI:' + out.native_code + ':' + out.measure + ':'
                        + out.country_iso3 + ':' + out.counterpart_area)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    d = build()
    if not len(d):
        print('nothing to add - %s missing' % EXTRACT)
        raise SystemExit(0)
    print('monthly BACI replication rows for the cube: %d' % len(d))
    print('  %d materials, %d exporters, %d importers, periods %d..%d'
          % (d.material.nunique(), d.country_iso3.nunique(), d.counterpart_area.nunique(),
             d.period.min(), d.period.max()))
    print('  rows carrying an interval: %d of %d' % (d.value_lo.notna().sum(), len(d)))
    print(d.groupby(['source', 'measure']).size().to_string())
    k = ['series_id', 'period']
    print('  duplicate series keys: %d  <- must be 0' % d.duplicated(k).sum())
