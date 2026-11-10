# -*- coding: utf-8 -*-
"""A monthly BACI: CEPII's reconciliation of mirror flows, month by month, to the latest period.

CEPII's BACI (Gaulier & Zignago, CEPII WP 2010-23) takes the two declarations of every bilateral
flow - the exporter's, FOB, and the importer's, CIF - and makes one number of them in three steps:
strip the freight from the importer's value, measure how noisy each country is as a reporter, and
average the two declarations with those reliabilities as weights. It is yearly and lags: the
version on disk (V202601) stops at 2024. The UN bulk corpus holds the same raw declarations by
month up to the last published period, so the same three steps run here per month.

    python reconcile/monthly_baci.py --slice raw/crm_monthly.parquet --out raw/monthly_baci_slice
    python reconcile/monthly_baci.py --periods 202501 202509          # from the bulk corpus

What a month's input is. The bulk files carry every breakdown a customs office publishes:
by transport mode (motCode), customs procedure (customsCode), second partner (partner2Code).
Only the TOTAL line is a declaration of the flow: customsCode 'C00', motCode 0, partner2Code 0.
Every reporter in the corpus carries those lines (checked on the 54-code slice: 150 of 150).
Flows 'M' and 'X' only; re-exports and re-imports are not the flow between the two countries.
Partner 0 is "World" and cannot be mirrored. Reporter and partner codes are the UN's numeric
codes, mapped to ISO3 with the country table BACI itself ships; a code that table does not
know (regional aggregates, "areas nes") is dropped.

Step 1, freight. The CIF/FOB coefficient of a route comes from CEPII's own published gravity
coefficients (Gaulier, Mirza, Turban, Zignago 2008, column 4), applied to the route's distance,
contiguity, language, colonial tie and landlocked status and the product's world unit value in
that month, exactly as the atlas's reconcile.py does on its 54 codes; the level is anchored on
the same CEPII_ANCHOR and capped at FREIGHT_CEILING. The importer's value divided by that
coefficient is its FOB value. BACI estimates its coefficients on the data in hand instead; that
is the first thing to try if the validation against BACI says the freight step is where we part.

Step 2, reliability. On the flows both sides declared, d = ln(FOB_exporter) - ln(FOB_importer).
Systematic level biases come out first by alternating robust median centering per reporter and
role; then E[d^2] = v_exporter + v_importer is solved by Gauss-Seidel on winsorized squares,
shrunk toward the month's global variance with REL_K pseudo-observations. One reliability per
reporter and role per month. A country that reports nothing that month gets no weight and is
not needed: its flows exist only through its partners.

Step 3, reconciliation. Weight of the exporter's declaration w = v_importer / (v_exporter +
v_importer); the reconciled value is the weighted arithmetic mean of the two FOB values, which
is what BACI publishes. A flow declared by one side only is that declaration (FOB). Quantities
(net weight, kg) are reconciled with the same weights, no freight correction.

Output: one parquet per month in --out, columns period, exporter, importer, hs6, v (USD, FOB,
reconciled), q (kg), vx, vm, vm_fob, qx, qm, markup, w_x, basis ('both' / 'x_only' / 'm_only');
and rel_<period>.parquet with the reliabilities. validate_monthly_baci.py sums the months to
years and compares them with BACI's own yearly numbers for the overlap, which is the test of all
of this.
"""
import argparse
import io
import json
import os
import sys
import time

import duckdb
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import reconcile as R                      # CEPII coefficients, anchor, landlocked set, freight cap

BULK = os.environ.get('CMA_BULK_DIR', os.path.join(ROOT, 'raw', 'comtrade_bulk'))
COUNTRIES = os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv')
GEO = os.path.join(ROOT, 'raw', 'geodist', 'dist_cepii.xls')

REL_K = 5.0           # shrinkage pseudo-observations toward the month's global variance
REL_WINSOR = 0.95     # squared residuals above this quantile are pulled back to it
REL_FLOOR = 1e-4      # no declarant is exact
TRIM_LO, TRIM_HI = 0.2, 5.0   # a pair outside this ratio band is a misclassification, not noise


def log(msg):
    sys.stdout.write('%s  %s\n' % (time.strftime('%H:%M:%S'), msg))
    sys.stdout.flush()


def country_map():
    c = pd.read_csv(COUNTRIES, dtype=str)
    c.columns = [x.lower() for x in c.columns]
    c = c.dropna(subset=['country_iso3'])
    return pd.DataFrame({'code': c.country_code.astype(int), 'iso3': c.country_iso3})


def geodist():
    g = pd.read_excel(GEO)
    g.columns = [x.lower() for x in g.columns]
    g = g[['iso_o', 'iso_d', 'dist', 'contig', 'comlang_off', 'colony']].dropna(subset=['dist'])
    return g


def month_source(period, slice_path):
    if slice_path:
        return "read_parquet('%s') WHERE period = %d" % (slice_path.replace(chr(92), '/'), int(period))
    d = os.path.join(BULK, str(period)[:4]).replace(chr(92), '/')
    return "read_parquet('%s/%s_*.parquet', union_by_name=true) WHERE 1=1" % (d, period)


def reliability(d_exp, d_imp, d):
    """Per-reporter variance components from the two-sided pairs of one month. Returns two dicts,
    exporter-role and importer-role variance, and the month's global residual variance."""
    exps, ecode = np.unique(d_exp, return_inverse=True)
    imps, icode = np.unique(d_imp, return_inverse=True)
    n_e, n_i = len(exps), len(imps)
    a = np.zeros(n_e); b = np.zeros(n_i)
    for _ in range(5):                                   # alternating robust median centering
        r = d - b[icode]
        a = pd.Series(r).groupby(ecode, sort=True).median().reindex(range(n_e)).fillna(0).to_numpy()
        r2 = d - a[ecode]
        b = pd.Series(r2).groupby(icode, sort=True).median().reindex(range(n_i)).fillna(0).to_numpy()
    resid = d - a[ecode] - b[icode]
    sq = resid ** 2
    cap = np.quantile(sq, REL_WINSOR) if len(sq) > 20 else sq.max()
    sq = np.minimum(sq, cap)
    g = float(sq.mean()) if len(sq) else 0.1
    ve = np.full(n_e, g / 2); vi = np.full(n_i, g / 2)
    ne = np.bincount(ecode, minlength=n_e); ni = np.bincount(icode, minlength=n_i)
    for _ in range(25):                                  # Gauss-Seidel on E[r^2] = ve + vi
        se = np.bincount(ecode, weights=sq - vi[icode], minlength=n_e)
        ve = np.maximum((se + REL_K * g / 2) / (ne + REL_K), REL_FLOOR)
        si = np.bincount(icode, weights=sq - ve[ecode], minlength=n_i)
        vi = np.maximum((si + REL_K * g / 2) / (ni + REL_K), REL_FLOOR)
    return (dict(zip(exps, ve)), dict(zip(imps, vi)), dict(zip(exps, ne)), dict(zip(imps, ni)),
            g, dict(zip(exps, a)), dict(zip(imps, b)))


def run_month(con, period, slice_path, out_dir, cmap, geo, landlocked):
    t0 = time.time()
    src = month_source(period, slice_path)
    con.execute("CREATE OR REPLACE TEMP TABLE raw AS "
                "SELECT reporterCode AS rep, partnerCode AS par, cmdCode AS hs6, flowCode AS flow, "
                "       primaryValue AS v, CASE WHEN netWgt > 0 THEN netWgt END AS q "
                "FROM %s AND customsCode = 'C00' AND motCode = 0 AND partner2Code = 0 "
                "  AND partnerCode <> 0 AND flowCode IN ('M', 'X') AND primaryValue > 0" % src)
    n_raw = con.execute("SELECT count(*) FROM raw").fetchall()[0][0]
    if not n_raw:
        log('%s: no total lines - skipped' % period)
        return None
    con.register('cmap', cmap)
    con.execute("""CREATE OR REPLACE TEMP TABLE pairs AS
        WITH x AS (SELECT r.iso3 AS exporter, p.iso3 AS importer, hs6, SUM(v) AS vx, SUM(q) AS qx,
                          COUNT(*) = COUNT(q) AS qx_full
                   FROM raw JOIN cmap r ON raw.rep = r.code JOIN cmap p ON raw.par = p.code
                   WHERE flow = 'X' GROUP BY 1, 2, 3),
             m AS (SELECT p.iso3 AS exporter, r.iso3 AS importer, hs6, SUM(v) AS vm, SUM(q) AS qm,
                          COUNT(*) = COUNT(q) AS qm_full
                   FROM raw JOIN cmap r ON raw.rep = r.code JOIN cmap p ON raw.par = p.code
                   WHERE flow = 'M' GROUP BY 1, 2, 3)
        SELECT COALESCE(x.exporter, m.exporter) AS exporter, COALESCE(x.importer, m.importer) AS importer,
               COALESCE(x.hs6, m.hs6) AS hs6, vx, CASE WHEN qx_full THEN qx END AS qx,
               vm, CASE WHEN qm_full THEN qm END AS qm
        FROM x FULL JOIN m ON x.exporter = m.exporter AND x.importer = m.importer AND x.hs6 = m.hs6
        WHERE COALESCE(x.exporter, m.exporter) <> COALESCE(x.importer, m.importer)""")
    # step 1: freight per route and product, CEPII's shape, the atlas's anchor
    uv = con.execute("SELECT hs6, median(vx / qx) AS uv FROM pairs WHERE qx > 0 AND vx > 0 GROUP BY 1").df()
    routes = con.execute("SELECT DISTINCT exporter, importer, hs6 FROM pairs WHERE vm IS NOT NULL").df()
    routes = routes.merge(geo, left_on=['exporter', 'importer'], right_on=['iso_o', 'iso_d'], how='left')
    routes = routes.merge(uv, on='hs6', how='left')
    B = R.CEPII_2008_COL4
    ok = routes.dist.notna() & routes.uv.notna() & (routes.uv > 0)
    pred = np.full(len(routes), np.nan)
    rr = routes[ok]
    pred[ok.to_numpy()] = (B['dist_log'] * np.log(rr.dist) + B['dist_log2'] * np.log(rr.dist) ** 2
                           + B['uv_log'] * np.log(rr.uv) + B['contig'] * rr.contig.fillna(0)
                           + B['comlang_off'] * rr.comlang_off.fillna(0) + B['colony'] * rr.colony.fillna(0)
                           + B['landlocked_exp'] * rr.exporter.isin(landlocked).astype(float)
                           + B['landlocked_imp'] * rr.importer.isin(landlocked).astype(float))
    med = np.nanmedian(pred) if ok.any() else 0.0
    markup = np.exp(pred - med + np.log(R.CEPII_ANCHOR))
    markup = np.where(np.isnan(markup), R.CEPII_ANCHOR, markup)
    routes['markup'] = np.clip(markup, 1.0, R.FREIGHT_CEILING)
    con.register('routes', routes[['exporter', 'importer', 'hs6', 'markup']])
    con.execute("""CREATE OR REPLACE TEMP TABLE adj AS
        SELECT p.*, COALESCE(r.markup, %f) AS markup, vm / COALESCE(r.markup, %f) AS vm_fob
        FROM pairs p LEFT JOIN routes r USING (exporter, importer, hs6)""" % (R.CEPII_ANCHOR, R.CEPII_ANCHOR))
    # step 2: reliabilities from the two-sided pairs inside the plausible band
    both = con.execute("""SELECT exporter, importer, ln(vx) - ln(vm_fob) AS d FROM adj
                          WHERE vx > 0 AND vm_fob > 0 AND vx / vm_fob BETWEEN %f AND %f
                          ORDER BY exporter, importer, hs6""" % (TRIM_LO, TRIM_HI)).df()
    n_both = len(both)
    if n_both >= 50:
        ve, vi, ne, ni, g, bias_e, bias_i = reliability(both.exporter.to_numpy(), both.importer.to_numpy(),
                                                       both.d.to_numpy(dtype=float))
    else:
        ve, vi, ne, ni, g, bias_e, bias_i = {}, {}, {}, {}, 0.1, {}, {}
    rel = pd.DataFrame([(period, 'exporter', k, int(ne[k]), float(v), float(bias_e[k])) for k, v in ve.items()]
                       + [(period, 'importer', k, int(ni[k]), float(v), float(bias_i[k])) for k, v in vi.items()],
                       columns=['period', 'role', 'reporter', 'n_pairs', 'var_resid', 'bias'])
    con.register('rel_e', rel[rel.role == 'exporter'][['reporter', 'var_resid']].rename(columns={'reporter': 'exporter', 'var_resid': 've'}))
    con.register('rel_i', rel[rel.role == 'importer'][['reporter', 'var_resid']].rename(columns={'reporter': 'importer', 'var_resid': 'vi'}))
    # step 3: reconcile. A reporter without a fitted variance gets the global one (unknown
    # reliability is not zero reliability).
    con.execute("""CREATE OR REPLACE TEMP TABLE recon AS
        SELECT %d AS period, exporter, importer, hs6,
               CASE WHEN vx IS NOT NULL AND vm_fob IS NOT NULL THEN w * vx + (1 - w) * vm_fob
                    WHEN vx IS NOT NULL THEN vx ELSE vm_fob END AS v,
               CASE WHEN qx IS NOT NULL AND qm IS NOT NULL THEN w * qx + (1 - w) * qm
                    WHEN qx IS NOT NULL THEN qx ELSE qm END AS q,
               vx, vm, vm_fob, qx, qm, markup,
               CASE WHEN vx IS NOT NULL AND vm_fob IS NOT NULL THEN w END AS w_x,
               CASE WHEN vx IS NOT NULL AND vm_fob IS NOT NULL THEN 'both'
                    WHEN vx IS NOT NULL THEN 'x_only' ELSE 'm_only' END AS basis
        FROM (SELECT a.*, COALESCE(vi, %f) / (COALESCE(ve, %f) + COALESCE(vi, %f)) AS w
              FROM adj a LEFT JOIN rel_e USING (exporter) LEFT JOIN rel_i USING (importer))""" % (int(period), g / 2, g / 2, g / 2))
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, '%s.parquet' % period).replace(chr(92), '/')
    tmp = dest + '.part'
    con.execute("COPY (SELECT * FROM recon ORDER BY exporter, importer, hs6) TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD)" % tmp)
    os.replace(tmp, dest)
    rel.to_parquet(os.path.join(out_dir, 'rel_%s.parquet' % period), index=False)
    s = con.execute("""SELECT count(*), count(*) FILTER (WHERE basis = 'both'), round(sum(v) / 1e9, 2),
                              count(DISTINCT exporter), count(DISTINCT importer) FROM recon""").fetchall()[0]
    log('%s: %s total lines -> %s flows (%s two-sided, %d pairs fitted, global var %.4f), %s bn USD, '
        '%d exporters / %d importers, %.0fs' % (period, format(n_raw, ','), format(s[0], ','),
                                                  format(s[1], ','), n_both, g, s[2], s[3], s[4], time.time() - t0))
    for t in ('raw', 'pairs', 'adj', 'recon'):
        con.execute('DROP TABLE IF EXISTS %s' % t)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--periods', nargs='*', help='YYYYMM ... or FROM TO (inclusive); default: all in the source')
    ap.add_argument('--slice', help='a single parquet of total lines (development), instead of the corpus')
    ap.add_argument('--out', default=os.environ.get('CMA_MONTHLY_DIR', os.path.join(ROOT, 'raw', 'monthly_baci')))
    ap.add_argument('--force', action='store_true', help='recompute months that already have an output')
    a = ap.parse_args()
    con = duckdb.connect()
    con.execute("SET memory_limit = '%s'" % os.environ.get('CMA_DUCK_MEM', '3GB'))
    con.execute("SET threads = %d" % int(os.environ.get('CMA_DUCK_THREADS', '3')))
    con.execute("SET preserve_insertion_order = false")
    if a.slice:
        pers = [r[0] for r in con.execute("SELECT DISTINCT period FROM read_parquet('%s') ORDER BY 1"
                                          % a.slice.replace(chr(92), '/')).fetchall()]
    else:
        pers = sorted({os.path.basename(f)[:6] for y in os.listdir(BULK) if y.isdigit()
                       for f in os.listdir(os.path.join(BULK, y)) if f.endswith('.parquet')})
    pers = [str(p) for p in pers]
    if a.periods:
        if len(a.periods) == 2 and a.periods[0] < a.periods[1]:
            pers = [p for p in pers if a.periods[0] <= p <= a.periods[1]]
        else:
            pers = [p for p in pers if p in set(a.periods)]
    cmap, geo, landlocked = country_map(), geodist(), set(R.LANDLOCKED)
    log('monthly BACI: %d period(s) %s..%s -> %s' % (len(pers), pers[0] if pers else '-', pers[-1] if pers else '-', a.out))
    done = 0
    for p in pers:
        if not a.force and os.path.exists(os.path.join(a.out, '%s.parquet' % p)):
            continue
        if run_month(con, p, a.slice, a.out, cmap, geo, landlocked) is not None:
            done += 1
    log('done: %d period(s) computed' % done)


if __name__ == '__main__':
    main()
