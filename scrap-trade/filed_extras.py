# -*- coding: utf-8 -*-
"""The three checks the scrap-trade filing named and flows.py never ran (deviation 5).

Committed before its first run. Reuses flows.py's own functions unchanged, so the published result
stays exactly reproducible and these checks run on the same sample, prices and estimator:

  (a) Leave one year out, for the two years with the largest world price moves. The filing does not
      define "world price move"; defined here, before the run: for each year, the mean across the six
      headline metals of |change in log real price| that year (the same-year price term, dp0); the two
      largest years. Each is dropped in turn from the headline sample, on both specifications.
  (b) A separate steel line (7204). Steel has no Pink Sheet scrap price; the filing names the unit value
      of Tuerkiye's own 7204 imports, deflated to 1998 dollars on the same deflator as the other
      prices. Its endogeneity is stated: Tuerkiye is the marginal buyer, so its import price and the
      world's scrap exports are driven by the same shocks. Small exporters, as in the headline.
  (c) A separate gold line (7112) on the Pink Sheet gold price. The filing reports it separately
      because 7112 is refining residues as much as scrap. Small exporters, as in the headline.

Readings use the rule the page applies (scrap-trade deviation 4): an estimate below the smallest
effect the design could detect with 80% power is not read as a response, whatever its p-value.
Writes out/scrap_trade_extras.json. Usage: python scrap-trade/filed_extras.py
"""
import collections
import json
import math
import os
import sys

import duckdb
import numpy as np
import openpyxl
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import flows as F                                              # the filed analysis, unchanged

OUT = os.path.join(F.ROOT, 'out', 'scrap_trade_extras.json')
TUR = '792'                                                    # BACI / M49 code for Tuerkiye
L3 = ['dp0', 'dp1', 'dp2']


def deflator(con):
    """The USGS-implied deflator flows.pink_annual uses, recomputed identically (same query)."""
    nom = con.execute("select material, period as y, max(value) v from read_parquet(?) "
                      "where measure='unit_value_nominal' and country_iso3='USA' group by 1,2",
                      [F.CUBE]).df()
    real = con.execute("select material, period as y, max(value) v from read_parquet(?) "
                       "where measure='unit_value_real98' and country_iso3='USA' group by 1,2",
                       [F.CUBE]).df()
    d = nom.merge(real, on=['material', 'y'], suffixes=('_n', '_r'))
    d = d[(d.v_r > 0) & (d.v_n > 0)]
    d['ratio'] = d.v_n / d.v_r
    g = d.groupby('y').ratio.agg(['median', 'size'])
    return {int(y): float(r['median']) for y, r in g.iterrows() if r['size'] >= 5}


def gold_price(defl):
    """Pink Sheet gold, monthly -> annual mean, deflated like every other price in the study."""
    wb = openpyxl.load_workbook(F.PINK, read_only=True, data_only=True)
    ws = wb['Monthly Prices']
    header = list(ws.iter_rows(min_row=5, max_row=5, values_only=True))[0]
    j = [i for i, n in enumerate(header) if n and str(n).strip() == 'Gold']
    assert len(j) == 1, 'no single Gold column in the Pink Sheet'
    acc = collections.defaultdict(list)
    for row in ws.iter_rows(min_row=7, values_only=True):
        d0 = row[0]
        if not d0 or 'M' not in str(d0):
            continue
        try:
            yr = int(str(d0)[:4])
        except ValueError:
            continue
        v = row[j[0]] if j[0] < len(row) else None
        if isinstance(v, (int, float)):
            acc[yr].append(float(v))
    wb.close()
    return {('gold', y): float(np.mean(v)) / defl[y] for y, v in acc.items() if len(v) >= 6 and y in defl}


def turkey_steel_price(defl):
    """Unit value of Tuerkiye's 7204 imports, USD per tonne, deflated to 1998 dollars."""
    out = {}
    for y in F.YEARS:
        t = F.baci.year(y)
        t['k'] = t.k.astype(str).str.zfill(6)
        t = t[t.k.str.startswith('7204') & (t.j.astype(str) == TUR)]
        q = pd.to_numeric(t['q'], errors='coerce').sum()
        v = pd.to_numeric(t['v'], errors='coerce').sum()
        if q > 0 and y in defl:
            out[('steel', y)] = (1000.0 * v / q) / defl[y]        # BACI value is thousands of USD
    return out


def read(f):
    if not f:
        return 'no estimate'
    if abs(f['cumulative']) >= f['mde_80pct_power']:
        return 'above its detectable size'
    if f['p'] < 0.05:
        return 'positive, but below the filed power bar, so not read'
    return 'not distinguishable from zero'


def clean(f):
    return {k: v for k, v in f.items() if k != '_raw'} if f else None


def main():
    con = duckdb.connect()
    defl = deflator(con)
    price = F.pink_annual(con)
    d = F.flows()
    p = F.panel(d, price)
    head = p[p.small & p.metal.isin(F.HEADLINE_METALS)]

    # (a) the two largest world price moves, defined on dp0 across the six headline metals
    moves = head.groupby('year').dp0.apply(lambda s: float(np.nanmean(np.abs(s.drop_duplicates()))))
    top2 = [int(y) for y in moves.sort_values(ascending=False).index[:2]]
    loo = {}
    for y in top2:
        sub = head[head.year != y]
        loo[str(y)] = {k: clean(F.fit(sub, 'dx', L3, fe)) for k, fe in
                       (('with_year_effects', True), ('without_year_effects', False))}
        for k in loo[str(y)]:
            if loo[str(y)][k]:
                loo[str(y)][k]['reading'] = read(loo[str(y)][k])

    # (b) steel on Tuerkiye's import unit value, (c) gold on the Pink Sheet price
    extra = {}
    extra.update(turkey_steel_price(defl))
    extra.update(gold_price(defl))
    price2 = dict(price)
    price2.update(extra)
    p2 = F.panel(d, price2)
    lines = {}
    for m in ('steel', 'gold'):
        sub = p2[p2.small & (p2.metal == m)]
        lines[m] = {k: clean(F.fit(sub, 'dx', L3, fe, m)) for k, fe in
                    (('with_year_effects', True), ('without_year_effects', False))}
        for k in lines[m]:
            if lines[m][k]:
                lines[m][k]['reading'] = read(lines[m][k])
        lines[m]['pairs'] = int(sub.cm.nunique())
        lines[m]['price_years'] = sum(1 for (mm, _) in extra if mm == m)

    res = {'filing': 'scrap-trade/PREREGISTRATION.md, deviation 5 (the three checks never run)',
           'rule_for_world_price_moves': 'mean |dp0| across the six headline metals, by year; top two',
           'world_price_move_by_year': {str(int(y)): (round(v, 4) if v == v else None)
                                        for y, v in moves.items()},
           'leave_one_year_out': {'years': top2, 'fits': loo},
           'steel_line': dict(lines['steel'], price='unit value of Tuerkiye 7204 imports, 1998 USD/t',
                              caveat='endogenous: Tuerkiye is the marginal buyer, so its import price '
                                     'and world scrap exports move with the same shocks'),
           'gold_line': dict(lines['gold'], price='Pink Sheet gold, spot bullion, 1998 USD',
                             caveat='7112 is refining residues as much as scrap')}
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1, default=float)

    print('largest world price moves:', top2, {y: round(moves[y], 3) for y in top2})
    for y, v in loo.items():
        for k, f in v.items():
            if f:
                print('  drop %s %-22s %+.3f (p %.3f, 95%% %+.2f to %+.2f, sees %.2f) -> %s'
                      % (y, k, f['cumulative'], f['p'], f['ci95'][0], f['ci95'][1], f['mde_80pct_power'], f['reading']))
    for m in ('steel', 'gold'):
        for k in ('with_year_effects', 'without_year_effects'):
            f = lines[m][k]
            if f:
                print('  %-5s %-22s %+.3f (p %.3f, 95%% %+.2f to %+.2f, sees %.2f, %d pairs) -> %s'
                      % (m, k, f['cumulative'], f['p'], f['ci95'][0], f['ci95'][1], f['mde_80pct_power'],
                         lines[m]['pairs'], f['reading']))
            else:
                print('  %-5s %-22s no estimate (%d pairs, %d price years)' % (m, k, lines[m]['pairs'], lines[m]['price_years']))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
