# -*- coding: utf-8 -*-
"""Read BACI's reconciliation off its own output.

Where we hold the raw annual declarations BACI was built from, every two-sided BACI flow is
    v_BACI = a_ij * (exporter's value) + b_ij * (importer's value)
and the pair's (a, b) can be solved from its flows. Found on 10 Nov 2026 (2024 data, 31 codes):
  - a + b = 1.0000 for the pairs that fit exactly: the weights sum to one on the RAW import value,
    i.e. no freight is removed from it;
  - logit(a_ij) = ln V_j(importer) - ln V_i(exporter) with R2 0.9998: the weight is the ratio of
    two country constants, a = V_j / (V_i + V_j), which is the paper's equation (3).
This script does that fit on every year for which raw/comtrade/comtrade_<year>.csv exists,
writes the country constants BACI is using (raw/baci/recovered_weights_V202601.csv: country,
lnV_exporter, lnV_importer) and prints the freight evidence flow by flow.

    python reconcile/recover_baci_weights.py [--years 2022 2024]
"""
import argparse
import os
import sys
import zipfile

import duckdb
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from hs_concordance import conversion

BACI_ZIP = os.path.join(ROOT, 'raw', 'baci', 'BACI_HS17_V202601.zip')
COUNTRIES = os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv')
OUT = os.path.join(ROOT, 'raw', 'baci', 'recovered_weights_V202601.csv')


def load_year(con, y, cm, conv):
    raw = os.path.join(ROOT, 'raw', 'comtrade', 'comtrade_%d.csv' % y).replace(chr(92), '/')
    con.execute("""CREATE OR REPLACE TEMP TABLE ann AS
        SELECT reporter, partner, lpad(CAST(cmd AS VARCHAR), 6, '0') AS k, flow, max(value) AS v
        FROM read_csv('%s', header=true, types={'cmd': 'VARCHAR'}) WHERE partner <> 0 AND flow IN ('M', 'X') AND value > 0
        GROUP BY 1, 2, 3, 4""" % raw)
    con.execute("""CREATE OR REPLACE TEMP TABLE pairs AS
        WITH x AS (SELECT e.country_iso3 AS exporter, i.country_iso3 AS importer, COALESCE(c.k17, a.k) AS k, sum(v) AS vx
                   FROM ann a JOIN cm e ON a.reporter = e.code JOIN cm i ON a.partner = i.code LEFT JOIN conv c ON c.k22 = a.k WHERE flow = 'X' GROUP BY 1, 2, 3),
             m AS (SELECT e.country_iso3 AS exporter, i.country_iso3 AS importer, COALESCE(c.k17, a.k) AS k, sum(v) AS vm
                   FROM ann a JOIN cm i ON a.reporter = i.code JOIN cm e ON a.partner = e.code LEFT JOIN conv c ON c.k22 = a.k WHERE flow = 'M' GROUP BY 1, 2, 3)
        SELECT exporter, importer, k, vx, vm FROM x JOIN m USING (exporter, importer, k) WHERE exporter <> importer""")
    codes = [r[0] for r in con.execute("SELECT DISTINCT k FROM pairs").fetchall()]
    z = zipfile.ZipFile(BACI_ZIP); fr = []
    with z.open('BACI_HS17_Y%d_V202601.csv' % y) as fh:
        for ch in pd.read_csv(fh, dtype={'k': str}, chunksize=2_000_000):
            fr.append(ch[ch.k.isin(codes)])
    con.register('braw', pd.concat(fr))
    return con.execute("""SELECT %d AS t, p.exporter, p.importer, p.k, p.vx, p.vm, b.vb FROM pairs p
        JOIN (SELECT e.country_iso3 AS exporter, i.country_iso3 AS importer, k, sum(v) * 1000.0 AS vb
              FROM braw JOIN cm e ON braw.i = e.code JOIN cm i ON braw.j = i.code GROUP BY 1, 2, 3) b USING (exporter, importer, k)
        WHERE b.vb > 0""" % y).df()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, nargs='*')
    ap.add_argument('--min-flows', type=int, default=5)
    a = ap.parse_args()
    years = a.years or [y for y in range(2017, 2025) if os.path.exists(os.path.join(ROOT, 'raw', 'comtrade', 'comtrade_%d.csv' % y))]
    con = duckdb.connect(); con.execute("SET memory_limit = '3GB'")
    cm = pd.read_csv(COUNTRIES, dtype=str); cm.columns = [c.lower() for c in cm.columns]
    cm = cm.dropna(subset=['country_iso3']); cm['code'] = cm.country_code.astype(int)
    con.register('cm', cm[['code', 'country_iso3']])
    conv = conversion(2022, 2017); con.register('conv', pd.DataFrame({'k22': list(conv.keys()), 'k17': list(conv.values())}))
    d = pd.concat([load_year(con, y, cm, conv) for y in years], ignore_index=True)
    d = d[np.abs(np.log(d.vx / d.vm)) > 0.05]              # the two reports must differ for the weights to show
    print('years %s: %s two-sided BACI flows with both raw declarations in hand' % (years, format(len(d), ',')))

    rows = []
    for (e, i), h in d.groupby(['exporter', 'importer']):
        if len(h) < a.min_flows:
            continue
        X = np.column_stack([h.vx / h.vb, h.vm / h.vb])
        (wa, wb), *_ = np.linalg.lstsq(X, np.ones(len(h)), rcond=None)
        rmse = float(np.sqrt(np.mean((X @ np.array([wa, wb]) - 1) ** 2)))
        rows.append((e, i, len(h), wa, wb, rmse))
    r = pd.DataFrame(rows, columns=['exporter', 'importer', 'n', 'a', 'b', 'rmse'])
    ex = r[r.rmse < 0.01].copy()
    print('pairs with >= %d flows: %d; BACI = a*export + b*import to within 1%%: %d pairs (%s flows)' % (a.min_flows, len(r), len(ex), format(int(ex.n.sum()), ',')))
    print('  a + b over those pairs: p10 %.4f  median %.4f  p90 %.4f   (1 = nothing removed from the import value)' % (
        (ex.a + ex.b).quantile(.1), (ex.a + ex.b).median(), (ex.a + ex.b).quantile(.9)))
    print('  the exporter\'s weight a: p10 %.2f  median %.2f  p90 %.2f' % (ex.a.quantile(.1), ex.a.median(), ex.a.quantile(.9)))

    f = ex[(ex.a > 0.005) & (ex.a < 0.995)].copy()
    f['lo'] = np.log(f.a / (1 - f.a))
    E = sorted(set(f.exporter)); I = sorted(set(f.importer))
    X = np.zeros((len(f) + 1, len(E) + len(I)))
    for k, t in enumerate(f.itertuples()):
        X[k, E.index(t.exporter)] = -1; X[k, len(E) + I.index(t.importer)] = 1
    X[len(f), :len(E)] = 1.0 / len(E)                       # normalisation: exporters' ln V average zero
    yv = np.append(f.lo.to_numpy(), 0.0)
    wts = np.append(np.sqrt(f.n.to_numpy()), 10.0)
    coef, *_ = np.linalg.lstsq(X * wts[:, None], yv * wts, rcond=None)
    res = f.lo.to_numpy() - X[:-1] @ coef
    print('  logit(a_ij) = lnV_importer_j - lnV_exporter_i: %d pairs, %d exporters, %d importers, residual sd %.3f, R2 %.4f' % (
        len(f), len(E), len(I), res.std(), 1 - res.var() / f.lo.var()))
    out = pd.DataFrame({'country': sorted(set(E) | set(I))})
    out['lnV_exporter'] = out.country.map(dict(zip(E, coef[:len(E)])))
    out['lnV_importer'] = out.country.map(dict(zip(I, coef[len(E):])))
    out.to_csv(OUT, index=False)
    print('  written: %s (%d countries; %d with an exporter constant, %d with an importer constant)' % (
        OUT, len(out), out.lnV_exporter.notna().sum(), out.lnV_importer.notna().sum()))

    # freight, flow by flow, on every pair whose two country constants are known
    lve = dict(zip(E, coef[:len(E)])); lvi = dict(zip(I, coef[len(E):]))
    g = d[d.exporter.isin(lve) & d.importer.isin(lvi)].copy()
    g['w'] = 1.0 / (1.0 + np.exp(g.exporter.map(lve) - g.importer.map(lvi)))
    den = g.vb - g.w * g.vx
    g = g[(den > 0) & (g.w < 0.97)]
    g['c'] = (1 - g.w) * g.vm / (g.vb - g.w * g.vx)
    g = g[(g.c > 0.5) & (g.c < 2)]
    print()
    print('freight, flow by flow (%s flows on pairs whose constants are known): implied factor c = (1-w) * import / (BACI - w * export)' % format(len(g), ','))
    print('  c: p10 %.4f  p25 %.4f  median %.4f  p75 %.4f  p90 %.4f' % tuple(g.c.quantile(q) for q in (.1, .25, .5, .75, .9)))
    for lab, m in (('within 0.5% of 1 (nothing removed)', (g.c - 1).abs() <= 0.005), ('between 1.005 and 1.15 (a freight strip)', (g.c > 1.005) & (g.c <= 1.15)),
                   ('below 0.995', g.c < 0.995), ('above 1.15', g.c > 1.15)):
        print('    %-44s %.1f%% of flows' % (lab, 100 * m.mean()))
    eu = {'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD',
          'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE'}
    for lab, m in (('EU importers', g.importer.isin(eu)), ('other importers', ~g.importer.isin(eu))):
        h = g[m]
        print('    %-16s n=%-6s nothing removed: %.1f%%   median c %.4f' % (lab, format(len(h), ','), 100 * ((h.c - 1).abs() <= 0.005).mean(), h.c.median()))


if __name__ == '__main__':
    main()
