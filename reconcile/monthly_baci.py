# -*- coding: utf-8 -*-
"""A monthly BACI: CEPII's reconciliation of mirror flows, as written in their paper, month by
month, to the latest published period.

CEPII's BACI (Gaulier & Zignago, CEPII WP 2010-23) makes one number of the two declarations of
a bilateral flow - the exporter's, FOB, and the importer's, CIF. Their procedure, and what this
script does with it (version 2, 10 Nov 2026; version 1 used published coefficients and a
different reliability model, and is in the git history):

0. DATA. Only the total line of a declaration is a flow (customs 'C00', transport 0, second
   partner 0); flows 'M' and 'X'; partner "World" dropped; the UN's numeric codes mapped to
   ISO3 with the country table BACI ships, codes it does not know dropped. "Areas not elsewhere
   specified" (partner 899) are reallocated to identified partners by the rule in the paper's
   appendix: when the exporter's declared partner total falls short of what its partners
   declare, the NES value fills that gap in proportion to the shortfalls; what is left is set
   against partners the exporter never named.
1. FREIGHT (paper section 2.3). The CIF rate of a flow is predicted from a gravity equation
   ESTIMATED ON THE DATA: ln(UVm/UVx) on ln distance, ln distance squared, contiguity, exporter
   landlocked, importer landlocked, ln world median unit value of the product, and time dummies
   - their model II: unit-value ratio, each observation weighted by min(Qx,Qm)/max(Qx,Qm).
   Cook's-distance outlier removal is approximated by a two-pass trim (ratio outside [0.2, 5],
   then residuals beyond 3 sigma). The importer's value divided by the predicted rate is its FOB
   value; not applied to countries that report imports FOB (their footnote 17: Algeria, Georgia,
   South Africa and the SACU), and to Canada only where it narrows the gap.
2. TIMING (ours, the owner's choice (c)). Monthly declarations of one shipment fall in different
   months on the two sides. Per route the importer's lag profile over 0..L months is estimated
   on all products by non-negative least squares, and the importer's series is brought onto the
   exporter's month before anything is compared. Yearly data never needed this.
3. RELIABILITY (paper section 2.4). Reporting distance RD = |ln(Vx/Vm_fob)| on two-sided flows,
   regressed on exporter, importer, time and product fixed effects (product by within
   transformation), each observation weighted by ln of the sum of the two reports; the exporter
   and importer least-square means LS_RD give sigma_i = (pi/2) (LS_RD_i - min LS_RD - 2 stderr_i),
   floored. Their equation (3) turns the two sigmas into the weight of the exporter's report.
4. RECONCILIATION. Weighted arithmetic mean of the two FOB values; a flow declared once is that
   declaration; quantities (net weight) with the same weights.

Estimation steps 1-3 pool every period in the run, as BACI pools its years; step 4 is per month.

    python reconcile/monthly_baci.py --slice raw/crm_monthly.parquet --out raw/monthly_baci_slice
    python reconcile/monthly_baci.py --periods 201908 202609 --out raw/monthly_baci     # corpus

Not done yet, and known: quantity-unit conversion to tons (the corpus carries net weight, which
BACI's step would complete for flows reported in other units); harmonisation of HS revisions,
which the full universe needs before 2022 and after can be compared product by product.
"""
import argparse
import json
import os
import sys
import time

import duckdb
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BULK = os.environ.get('CMA_BULK_DIR', os.path.join(ROOT, 'raw', 'comtrade_bulk'))
COUNTRIES = os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv')
GEO = os.path.join(ROOT, 'raw', 'geodist', 'dist_cepii.xls')

NES = 899                                  # Comtrade partner "Areas, nes"
FOB_IMPORTERS = {'DZA', 'GEO', 'ZAF', 'BWA', 'LSO', 'NAM', 'SWZ'}   # report imports FOB: no freight strip
FAS_IMPORTERS = {'CAN'}                                          # strip only where it narrows the gap
TRIM_LO, TRIM_HI = 0.2, 5.0                # a two-sided pair outside this ratio is a misclassification
LANDLOCKED = {'AFG', 'AND', 'ARM', 'AUT', 'AZE', 'BDI', 'BFA', 'BLR', 'BOL', 'BTN', 'BWA', 'CAF', 'CHE',
              'CZE', 'ETH', 'HUN', 'KAZ', 'KGZ', 'LAO', 'LIE', 'LSO', 'LUX', 'MDA', 'MKD', 'MLI', 'MNG',
              'MWI', 'NER', 'NPL', 'PRY', 'RWA', 'SMR', 'SRB', 'SSD', 'SVK', 'SWZ', 'TCD', 'TJK', 'TKM',
              'UGA', 'UZB', 'VAT', 'ZMB', 'ZWE', 'KOS'}


def log(msg):
    sys.stdout.write('%s  %s\n' % (time.strftime('%H:%M:%S'), msg))
    sys.stdout.flush()


def country_map():
    c = pd.read_csv(COUNTRIES, dtype=str)
    c.columns = [x.lower() for x in c.columns]
    c = c.dropna(subset=['country_iso3'])
    return pd.DataFrame({'code': c.country_code.astype(int), 'iso3': c.country_iso3})


def geodist():
    g = pd.read_excel(GEO, engine='calamine') if _has_calamine() else pd.read_excel(GEO)
    g.columns = [x.lower() for x in g.columns]
    g = g[['iso_o', 'iso_d', 'dist', 'distw', 'contig']].copy()
    # the paper uses population-weighted distances where available
    g['d'] = g.distw.where(g.distw.notna() & (g.distw > 0), g.dist)
    return g[['iso_o', 'iso_d', 'd', 'contig']].dropna(subset=['d'])


def _has_calamine():
    try:
        import python_calamine  # noqa
        return True
    except Exception:
        return False


# ----------------------------------------------------------------------------------------------
# 0. data: total lines of every period in the run, as one on-disk table
# ----------------------------------------------------------------------------------------------
def load_totals(con, periods, slice_path, work):
    cmap = country_map()
    con.register('cmap', cmap)
    parts = []
    for p in periods:
        if slice_path:
            src = "read_parquet('%s') WHERE period = %d" % (slice_path.replace(chr(92), '/'), int(p))
        else:
            src = "read_parquet('%s/%s/%s_*.parquet', union_by_name=true) WHERE 1=1" % (
                BULK.replace(chr(92), '/'), str(p)[:4], p)
        parts.append("""SELECT period, reporterCode AS rep, partnerCode AS par, cmdCode AS hs6, flowCode AS flow,
                               primaryValue AS v, CASE WHEN netWgt > 0 THEN netWgt END AS q
                        FROM %s AND customsCode = 'C00' AND motCode = 0 AND partner2Code = 0
                          AND partnerCode <> 0 AND flowCode IN ('M', 'X') AND primaryValue > 0""" % src)
    tot = os.path.join(work, 'totals.parquet').replace(chr(92), '/')
    con.execute("COPY (%s) TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD)" % (' UNION ALL '.join(parts), tot))
    con.execute("""CREATE OR REPLACE TABLE tot AS
        SELECT t.period, r.iso3 AS reporter, CASE WHEN t.par = %d THEN 'NES' ELSE p.iso3 END AS partner,
               t.hs6, t.flow, SUM(t.v) AS v, SUM(t.q) AS q, COUNT(*) = COUNT(t.q) AS q_full
        FROM read_parquet('%s') t JOIN cmap r ON t.rep = r.code
             LEFT JOIN cmap p ON t.par = p.code
        WHERE (t.par = %d OR p.iso3 IS NOT NULL)
        GROUP BY 1, 2, 3, 4, 5""" % (NES, tot, NES))
    n = con.execute("SELECT count(*), count(*) FILTER (WHERE partner = 'NES') FROM tot").fetchall()[0]
    log('totals: %s declarations, %s of them to "areas nes"' % (format(n[0], ','), format(n[1], ',')))


def reallocate_nes(con):
    """The paper's appendix, for the exporter side (NES destinations) and, mirrored, the importer
    side (NES origins). Only ever moves value toward identified partners; never invents a flow."""
    for role, flow, mflow in (('reporter', 'X', 'M'), ('reporter', 'M', 'X')):
        # own declared total to identified partners, the mirror total those partners declare, the NES value
        con.execute("""CREATE OR REPLACE TEMP TABLE nes AS
            WITH own AS (SELECT period, reporter, hs6, SUM(v) FILTER (WHERE partner <> 'NES') AS v_own,
                                MAX(v) FILTER (WHERE partner = 'NES') AS v_nes
                         FROM tot WHERE flow = '%s' GROUP BY 1, 2, 3 HAVING MAX(v) FILTER (WHERE partner = 'NES') > 0),
                 mir AS (SELECT period, partner AS reporter, hs6, reporter AS partner, v AS v_mir
                         FROM tot WHERE flow = '%s' AND partner <> 'NES'),
                 ownp AS (SELECT period, reporter, hs6, partner, v AS v_ownp FROM tot WHERE flow = '%s' AND partner <> 'NES')
            SELECT o.period, o.reporter, o.hs6, m.partner, m.v_mir, p.v_ownp, o.v_nes, o.v_own,
                   SUM(m.v_mir) OVER w AS v_mir_tot,
                   GREATEST(m.v_mir - COALESCE(p.v_ownp, 0), 0) AS shortfall
            FROM own o JOIN mir m USING (period, reporter, hs6)
                 LEFT JOIN ownp p ON p.period = o.period AND p.reporter = o.reporter AND p.hs6 = o.hs6 AND p.partner = m.partner
            WINDOW w AS (PARTITION BY o.period, o.reporter, o.hs6)""" % (flow, mflow, flow))
        # allocate min(v_nes, mirror total - own total) in proportion to the shortfalls
        con.execute("""CREATE OR REPLACE TEMP TABLE alloc AS
            SELECT period, reporter, hs6, partner,
                   LEAST(v_nes, GREATEST(v_mir_tot - COALESCE(v_own, 0), 0))
                   * shortfall / NULLIF(SUM(shortfall) OVER (PARTITION BY period, reporter, hs6), 0) AS add_v
            FROM nes WHERE shortfall > 0""")
        n = con.execute("SELECT count(*), SUM(add_v) FROM alloc WHERE add_v > 0").fetchall()[0]
        con.execute("""INSERT INTO tot
            SELECT period, reporter, partner, hs6, '%s', add_v, NULL, FALSE FROM alloc WHERE add_v > 0""" % flow)
        con.execute("""CREATE OR REPLACE TABLE tot AS
            SELECT period, reporter, partner, hs6, flow, SUM(v) AS v, SUM(q) AS q, BOOL_AND(q_full) AS q_full
            FROM tot GROUP BY 1, 2, 3, 4, 5""")
        log('areas nes, %s side: %s partner flows topped up with %.2f bn USD' % (
            'export' if flow == 'X' else 'import', format(n[0] or 0, ','), (n[1] or 0) / 1e9))
    con.execute("DELETE FROM tot WHERE partner = 'NES'")


def build_pairs(con):
    con.execute("""CREATE OR REPLACE TABLE pairs AS
        WITH x AS (SELECT period, reporter AS exporter, partner AS importer, hs6, v AS vx,
                          CASE WHEN q_full THEN q END AS qx FROM tot WHERE flow = 'X'),
             m AS (SELECT period, partner AS exporter, reporter AS importer, hs6, v AS vm,
                          CASE WHEN q_full THEN q END AS qm FROM tot WHERE flow = 'M')
        SELECT COALESCE(x.period, m.period) AS period, COALESCE(x.exporter, m.exporter) AS exporter,
               COALESCE(x.importer, m.importer) AS importer, COALESCE(x.hs6, m.hs6) AS hs6, vx, qx, vm, qm
        FROM x FULL JOIN m ON x.period = m.period AND x.exporter = m.exporter AND x.importer = m.importer AND x.hs6 = m.hs6
        WHERE COALESCE(x.exporter, m.exporter) <> COALESCE(x.importer, m.importer)""")
    n = con.execute("SELECT count(*), count(*) FILTER (WHERE vx IS NOT NULL AND vm IS NOT NULL) FROM pairs").fetchall()[0]
    log('pairs: %s flows, %s declared by both sides' % (format(n[0], ','), format(n[1], ',')))


# ----------------------------------------------------------------------------------------------
# 1. freight: the gravity equation estimated on the data, model II
# ----------------------------------------------------------------------------------------------
def fit_freight(con, geo, work, max_obs=4_000_000):
    con.register('geo', geo)
    con.execute("""CREATE OR REPLACE TABLE uv AS
        SELECT period, hs6, median(vx / qx) AS uv FROM pairs WHERE qx > 0 AND vx > 0 GROUP BY 1, 2""")
    d = con.execute("""SELECT p.period, p.exporter, p.importer, p.hs6,
                              ln((vm / qm) / (vx / qx)) AS y, LEAST(qx, qm) / GREATEST(qx, qm) AS w,
                              ln(g.d) AS ld, g.contig, ln(u.uv) AS luv
                       FROM pairs p JOIN geo g ON g.iso_o = p.exporter AND g.iso_d = p.importer
                            JOIN uv u USING (period, hs6)
                       WHERE vx > 0 AND vm > 0 AND qx > 0 AND qm > 0 AND u.uv > 0
                         AND vm / vx BETWEEN %f AND %f AND (vm / qm) / (vx / qx) BETWEEN %f AND %f
                         AND NOT importer IN (%s)
                       USING SAMPLE reservoir(%d ROWS) REPEATABLE (7)""" % (
        TRIM_LO, TRIM_HI, TRIM_LO, TRIM_HI, ','.join("'%s'" % c for c in FOB_IMPORTERS), max_obs)).df()
    if len(d) < 1000:
        log('freight: only %d usable pairs - falling back to a flat 3.3%% rate' % len(d))
        return {'flat': 1.033, 'n': int(len(d))}
    periods = sorted(d.period.unique())
    pcode = pd.Categorical(d.period, categories=periods).codes
    X = np.column_stack([np.ones(len(d)), d.ld, d.ld ** 2, d.contig.fillna(0),
                         d.exporter.isin(LANDLOCKED).astype(float), d.importer.isin(LANDLOCKED).astype(float), d.luv])
    T = np.zeros((len(d), len(periods) - 1))
    T[np.arange(len(d))[pcode > 0], pcode[pcode > 0] - 1] = 1.0   # first period is the reference
    X = np.hstack([X, T])
    y = d.y.to_numpy(dtype=float); w = d.w.to_numpy(dtype=float)
    keep = np.ones(len(y), dtype=bool)
    for _ in range(2):                                   # two passes stand in for Cook's distance
        sw = np.sqrt(w[keep])
        beta, *_ = np.linalg.lstsq(X[keep] * sw[:, None], y[keep] * sw, rcond=None)
        r = y - X @ beta
        s = np.sqrt(np.average(r[keep] ** 2, weights=w[keep]))
        keep = np.abs(r) <= 3 * s
    names = ['intercept', 'ln_dist', 'ln_dist2', 'contig', 'landlocked_exp', 'landlocked_imp', 'ln_uv']
    coef = dict(zip(names, beta[:7].tolist()))
    tfe = dict(zip(periods, [0.0] + beta[7:].tolist()))
    pred = X @ beta
    out = {'coef': coef, 'time_fe': {str(k): v for k, v in tfe.items()}, 'n': int(keep.sum()),
           'dropped': int((~keep).sum()), 'mean_cif_rate': float(np.exp(pred[keep]).mean() - 1),
           'resid_sd': float(s)}
    json.dump(out, open(os.path.join(work, 'freight_fit.json'), 'w'), indent=1)
    log('freight fit on %s pairs (%s outliers out): mean CIF rate %.1f%%, ln dist %.3f, ln dist2 %.4f, '
        'contig %.3f, landlocked exp %.3f imp %.3f, ln uv %.3f' % (
            format(out['n'], ','), format(out['dropped'], ','), 100 * out['mean_cif_rate'], coef['ln_dist'],
            coef['ln_dist2'], coef['contig'], coef['landlocked_exp'], coef['landlocked_imp'], coef['ln_uv']))
    return out


def apply_freight(con, geo, fit):
    """vm_fob for every import declaration: the predicted rate, the paper's exceptions."""
    if 'flat' in fit:
        con.execute("CREATE OR REPLACE TABLE adj AS SELECT *, %f AS rate, vm / %f AS vm_fob FROM pairs" % (fit['flat'], fit['flat']))
        return
    c = fit['coef']
    tfe = pd.DataFrame({'period': [int(k) for k in fit['time_fe']], 'tfe': list(fit['time_fe'].values())})
    con.register('tfe', tfe)
    ll = pd.DataFrame({'iso3': sorted(LANDLOCKED)}); con.register('ll', ll)
    con.execute("""CREATE OR REPLACE TABLE adj AS
        WITH r AS (SELECT p.*, g.d, g.contig, u.uv, COALESCE(t.tfe, 0) AS tfe,
                          CASE WHEN le.iso3 IS NOT NULL THEN 1 ELSE 0 END AS lle,
                          CASE WHEN li.iso3 IS NOT NULL THEN 1 ELSE 0 END AS lli
                   FROM pairs p LEFT JOIN geo g ON g.iso_o = p.exporter AND g.iso_d = p.importer
                        LEFT JOIN uv u USING (period, hs6) LEFT JOIN tfe t USING (period)
                        LEFT JOIN ll le ON le.iso3 = p.exporter LEFT JOIN ll li ON li.iso3 = p.importer),
             e AS (SELECT *, CASE WHEN d IS NOT NULL AND uv > 0 THEN
                        exp(%f + %f * ln(d) + %f * ln(d) * ln(d) + %f * COALESCE(contig, 0) + %f * lle + %f * lli + %f * ln(uv) + tfe)
                      ELSE %f END AS rate_raw FROM r)
        SELECT * EXCLUDE (d, contig, uv, tfe, lle, lli, rate_raw),
               CASE WHEN importer IN (%s) THEN 1.0
                    WHEN importer IN (%s) AND vx IS NOT NULL AND abs(ln(vx) - ln(vm / rate_raw)) > abs(ln(vx) - ln(vm)) THEN 1.0
                    ELSE GREATEST(rate_raw, 1.0) END AS rate,
               vm / (CASE WHEN importer IN (%s) THEN 1.0
                          WHEN importer IN (%s) AND vx IS NOT NULL AND abs(ln(vx) - ln(vm / rate_raw)) > abs(ln(vx) - ln(vm)) THEN 1.0
                          ELSE GREATEST(rate_raw, 1.0) END) AS vm_fob
        FROM e""" % (c['intercept'], c['ln_dist'], c['ln_dist2'], c['contig'], c['landlocked_exp'], c['landlocked_imp'],
                     c['ln_uv'], 1.0 + fit['mean_cif_rate'],
                     ','.join("'%s'" % x for x in FOB_IMPORTERS), ','.join("'%s'" % x for x in FAS_IMPORTERS),
                     ','.join("'%s'" % x for x in FOB_IMPORTERS), ','.join("'%s'" % x for x in FAS_IMPORTERS)))
    s = con.execute("SELECT avg(rate), median(rate), count(*) FILTER (WHERE vm IS NOT NULL) FROM adj").fetchall()[0]
    log('freight applied: mean rate %.3f, median %.3f over %s import declarations' % (s[0], s[1], format(s[2], ',')))


# ----------------------------------------------------------------------------------------------
# 2. timing: the importer's lag profile per route, and the importer's series on the exporter's month
# ----------------------------------------------------------------------------------------------
def _nnls(A, b):
    try:
        from scipy.optimize import nnls
        x, _ = nnls(A, b)
        return x
    except Exception:
        x, *_ = np.linalg.lstsq(A, b, rcond=None)
        return np.maximum(x, 0)


def align_timing(con, lags, work, min_months=12, min_pairs=60):
    """theta_l = share of the exporter's month-t shipments the importer records in month t+l.
    Estimated per route on the product-level series of the two sides (both-sided corridors), by
    NNLS with theta >= 0 and sum theta = 1. The aligned importer value for exporter month t is
    sum_l theta_l * vm_fob(t+l), renormalised over the lags that exist in the data."""
    if lags <= 0:
        con.execute("CREATE OR REPLACE TABLE adj2 AS SELECT *, vm_fob AS vm_al, qm AS qm_al, 1.0 AS theta0 FROM adj")
        return {}
    d = con.execute("""SELECT exporter, importer, hs6, period, vx, vm_fob FROM adj
                       WHERE vx > 0 OR vm_fob > 0 ORDER BY exporter, importer, hs6, period""").df()
    d['m'] = (d.period // 100) * 12 + d.period % 100
    thetas = {}
    for (e, i), g in d.groupby(['exporter', 'importer'], sort=True):
        if g.m.nunique() < min_months:
            continue
        # per corridor: exporter series and the importer series shifted by 0..lags
        rows_x, rows_m = [], []
        for _, h in g.groupby('hs6', sort=True):
            if h.period.nunique() < 3:
                continue
            mi = pd.Series(h.vm_fob.to_numpy(dtype=float), index=h.m.to_numpy()).fillna(0)
            xi = pd.Series(h.vx.to_numpy(dtype=float), index=h.m.to_numpy()).fillna(0)
            months = xi[xi > 0].index.to_numpy()
            months = months[months + lags <= mi.index.max()]     # the whole lag window must exist
            if not len(months):
                continue
            rows_x.append(xi.reindex(months).to_numpy())
            rows_m.append(np.column_stack([mi.reindex(months + l, fill_value=0).to_numpy() for l in range(lags + 1)]))
        if not rows_x:
            continue
        y = np.concatenate(rows_x); A = np.vstack(rows_m)
        if len(y) < min_pairs or A.sum() == 0:
            continue
        sc = y.mean() or 1.0
        th = _nnls(A / sc, y / sc)
        if th.sum() <= 0:
            continue
        thetas[(e, i)] = (th / th.sum()).tolist()
    tdf = pd.DataFrame([(e, i, l, t) for (e, i), ths in thetas.items() for l, t in enumerate(ths)],
                       columns=['exporter', 'importer', 'lag', 'theta'])
    if not len(tdf):
        con.execute("CREATE OR REPLACE TABLE adj2 AS SELECT *, vm_fob AS vm_al, qm AS qm_al, 1.0 AS theta0 FROM adj")
        log('timing: no route had enough data; importer series left as declared')
        return {}
    tdf.to_parquet(os.path.join(work, 'route_lags.parquet'), index=False)
    con.register('lagsT', tdf)
    con.execute("""CREATE OR REPLACE TABLE adj2 AS
        WITH base AS (SELECT *, (period // 100) * 12 + period %% 100 AS m FROM adj),
             mser AS (SELECT exporter, importer, hs6, m, vm_fob, qm FROM base WHERE vm_fob IS NOT NULL),
             maxm AS (SELECT exporter, importer, MAX(m) AS mmax FROM base GROUP BY 1, 2),
             al AS (SELECT b.exporter, b.importer, b.hs6, b.m,
                           SUM(t.theta * s.vm_fob) AS vm_num, SUM(t.theta * s.qm) AS qm_num,
                           SUM(t.theta) FILTER (WHERE b.m + t.lag <= x.mmax) AS th_avail,
                           SUM(t.theta) FILTER (WHERE s.vm_fob IS NOT NULL) AS th_hit
                    FROM base b JOIN lagsT t USING (exporter, importer) JOIN maxm x USING (exporter, importer)
                         LEFT JOIN mser s ON s.exporter = b.exporter AND s.importer = b.importer AND s.hs6 = b.hs6 AND s.m = b.m + t.lag
                    GROUP BY 1, 2, 3, 4)
        SELECT b.* EXCLUDE (m),
               CASE WHEN a.exporter IS NULL OR a.th_avail IS NULL OR a.th_avail <= 0 THEN b.vm_fob
                    WHEN a.th_hit IS NULL OR a.th_hit = 0 THEN NULL
                    ELSE a.vm_num / a.th_avail END AS vm_al,
               CASE WHEN a.exporter IS NULL OR a.th_avail IS NULL OR a.th_avail <= 0 THEN b.qm
                    WHEN a.th_hit IS NULL OR a.th_hit = 0 THEN NULL
                    ELSE a.qm_num / a.th_avail END AS qm_al,
               COALESCE((SELECT theta FROM lagsT t WHERE t.exporter = b.exporter AND t.importer = b.importer AND t.lag = 0), 1.0) AS theta0
        FROM base b LEFT JOIN al a USING (exporter, importer, hs6, m)""")
    share0 = float(tdf[tdf.lag == 0].theta.mean())
    log('timing: lag profiles for %d routes (mean share recorded the same month %.2f); importer series aligned' % (len(thetas), share0))
    return thetas


# ----------------------------------------------------------------------------------------------
# 3. reliability: the paper's reporting-distance regression and sigma transformation
# ----------------------------------------------------------------------------------------------
def fit_reliability(con, work):
    d = con.execute("""SELECT exporter, importer, period, hs6, abs(ln(vx) - ln(vm_al)) AS rd,
                              ln((vx + vm_al) / 1000.0) AS w
                       FROM adj2 WHERE vx > 0 AND vm_al > 0 AND vx / vm_al BETWEEN %f AND %f
                       ORDER BY exporter, importer, period, hs6""" % (TRIM_LO, TRIM_HI)).df()
    d = d[d.w > 0]
    n = len(d)
    if n < 500:
        log('reliability: only %d two-sided pairs - equal weights' % n)
        return pd.DataFrame(columns=['role', 'reporter', 'n', 'ls_rd', 'stderr', 'sigma'])
    y = d.rd.to_numpy(dtype=float); w = d.w.to_numpy(dtype=float)
    fac = {}
    for k in ('exporter', 'importer', 'period', 'hs6'):
        codes, uniq = pd.factorize(d[k], sort=True)
        fac[k] = (codes, len(uniq), uniq)
    # weighted alternating projections: y and the dummies demeaned within each factor until
    # convergence, which is the within estimator with four sets of fixed effects
    r = y.copy()
    for it in range(60):
        r_old = r.copy()
        for k in fac:
            codes, n_k, _ = fac[k]
            m = np.bincount(codes, weights=w * r, minlength=n_k) / np.maximum(np.bincount(codes, weights=w, minlength=n_k), 1e-12)
            r = r - m[codes]
        if np.max(np.abs(r - r_old)) < 1e-9:
            break
    resid_var = float(np.average(r ** 2, weights=w))
    gmean = float(np.average(y, weights=w))
    out = []
    for role in ('exporter', 'importer'):
        codes, n_k, uniq = fac[role]
        # the factor's effect = weighted mean of (y - all other effects): recovered as the within
        # mean of y minus the residual, by factor
        eff_num = np.bincount(codes, weights=w * (y - r), minlength=n_k)
        eff_den = np.maximum(np.bincount(codes, weights=w, minlength=n_k), 1e-12)
        ls = eff_num / eff_den                              # least-square mean of RD for the reporter
        cnt = np.bincount(codes, minlength=n_k)
        stderr = np.sqrt(resid_var / np.maximum(cnt, 1))
        base = np.min(ls - 2 * stderr)
        sigma = (np.pi / 2) * np.maximum(ls - base - 2 * stderr, 0.0)
        sigma = np.maximum(sigma, 0.01)
        out.append(pd.DataFrame({'role': role, 'reporter': uniq, 'n': cnt, 'ls_rd': ls, 'stderr': stderr, 'sigma': sigma}))
    rel = pd.concat(out, ignore_index=True)
    rel.to_parquet(os.path.join(work, 'reliability.parquet'), index=False)
    log('reliability on %s pairs: mean RD %.3f, residual sd %.3f; sigma exporter median %.3f [%.3f..%.3f], '
        'importer median %.3f' % (format(n, ','), gmean, np.sqrt(resid_var),
                                   rel[rel.role == 'exporter'].sigma.median(), rel[rel.role == 'exporter'].sigma.min(),
                                   rel[rel.role == 'exporter'].sigma.max(), rel[rel.role == 'importer'].sigma.median()))
    return rel


def weight_expr():
    """The paper's equation (3): w = Vj / (Vi + Vj) with V = e^s2 (e^s2 - 1), the log-normal variance
    of a report's error. Unknown sigma -> the median of the known ones."""
    return ("(exp(si2) * (exp(si2) - 1)) / ((exp(se2) * (exp(se2) - 1)) + (exp(si2) * (exp(si2) - 1)))")


# ----------------------------------------------------------------------------------------------
# 4. reconcile and write
# ----------------------------------------------------------------------------------------------
def reconcile(con, rel, out_dir, periods):
    if len(rel):
        re_ = rel[rel.role == 'exporter'][['reporter', 'sigma']].rename(columns={'reporter': 'exporter', 'sigma': 'se'})
        ri_ = rel[rel.role == 'importer'][['reporter', 'sigma']].rename(columns={'reporter': 'importer', 'sigma': 'si'})
        med_e = float(re_.se.median()); med_i = float(ri_.si.median())
    else:
        re_ = pd.DataFrame({'exporter': [], 'se': []}); ri_ = pd.DataFrame({'importer': [], 'si': []})
        med_e = med_i = 0.5
    con.register('re_', re_); con.register('ri_', ri_)
    con.execute("""CREATE OR REPLACE TABLE recon AS
        SELECT period, exporter, importer, hs6,
               CASE WHEN vx IS NOT NULL AND vm_al IS NOT NULL THEN w * vx + (1 - w) * vm_al
                    WHEN vx IS NOT NULL THEN vx ELSE vm_al END AS v,
               CASE WHEN qx IS NOT NULL AND qm_al IS NOT NULL THEN w * qx + (1 - w) * qm_al
                    WHEN qx IS NOT NULL THEN qx ELSE qm_al END AS q,
               vx, vm, vm_fob, vm_al, qx, qm, rate AS markup, theta0,
               CASE WHEN vx IS NOT NULL AND vm_al IS NOT NULL THEN w END AS w_x,
               CASE WHEN vx IS NOT NULL AND vm_al IS NOT NULL THEN 'both'
                    WHEN vx IS NOT NULL THEN 'x_only' ELSE 'm_only' END AS basis
        FROM (SELECT a.*, %s AS w
              FROM (SELECT a0.*, POWER(COALESCE(e.se, %f), 2) AS se2, POWER(COALESCE(i.si, %f), 2) AS si2
                    FROM adj2 a0 LEFT JOIN re_ e USING (exporter) LEFT JOIN ri_ i USING (importer)) a)
        WHERE vx IS NOT NULL OR vm_al IS NOT NULL""" % (weight_expr(), med_e, med_i))
    os.makedirs(out_dir, exist_ok=True)
    for p in periods:
        dest = os.path.join(out_dir, '%s.parquet' % p).replace(chr(92), '/')
        con.execute("COPY (SELECT * FROM recon WHERE period = %d ORDER BY exporter, importer, hs6) TO '%s.part' (FORMAT PARQUET, COMPRESSION ZSTD)" % (int(p), dest))
        os.replace(dest + '.part', dest)
    s = con.execute("""SELECT count(*), count(*) FILTER (WHERE basis = 'both'), round(sum(v) / 1e9, 1),
                              avg(w_x), count(DISTINCT period) FROM recon""").fetchall()[0]
    log('reconciled: %s flows over %d periods, %s two-sided (mean exporter weight %.3f), %s bn USD -> %s' % (
        format(s[0], ','), s[4], format(s[1], ','), s[3] or 0, s[2], out_dir))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--periods', nargs='*', help='YYYYMM ... or FROM TO (inclusive); default: all in the source')
    ap.add_argument('--slice', help='a single parquet of raw lines (development), instead of the corpus')
    ap.add_argument('--out', default=os.environ.get('CMA_MONTHLY_DIR', os.path.join(ROOT, 'raw', 'monthly_baci')))
    ap.add_argument('--lags', type=int, default=2, help='importer lag window in months for the timing step (0 = off)')
    ap.add_argument('--no-nes', action='store_true', help='skip the areas-nes reallocation')
    a = ap.parse_args()
    work = os.path.join(a.out, '_fit'); os.makedirs(work, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit = '%s'" % os.environ.get('CMA_DUCK_MEM', '3GB'))
    con.execute("SET threads = %d" % int(os.environ.get('CMA_DUCK_THREADS', '3')))
    con.execute("SET temp_directory = '%s'" % os.path.join(work, 'duck_tmp').replace(chr(92), '/'))
    con.execute("SET preserve_insertion_order = false")
    if a.slice:
        pers = [str(r[0]) for r in con.execute("SELECT DISTINCT period FROM read_parquet('%s') ORDER BY 1"
                                               % a.slice.replace(chr(92), '/')).fetchall()]
    else:
        pers = sorted({os.path.basename(f)[:6] for y in os.listdir(BULK) if y.isdigit()
                       for f in os.listdir(os.path.join(BULK, y)) if f.endswith('.parquet')})
    if a.periods:
        if len(a.periods) == 2 and a.periods[0] < a.periods[1]:
            pers = [p for p in pers if a.periods[0] <= p <= a.periods[1]]
        else:
            pers = [p for p in pers if p in set(a.periods)]
    log('monthly BACI v2: %d period(s) %s..%s, lags %d -> %s' % (len(pers), pers[0], pers[-1], a.lags, a.out))
    t0 = time.time()
    load_totals(con, pers, a.slice, work)
    if not a.no_nes:
        reallocate_nes(con)
    build_pairs(con)
    geo = geodist()
    fit = fit_freight(con, geo, work)
    apply_freight(con, geo, fit)
    align_timing(con, a.lags, work)
    rel = fit_reliability(con, work)
    reconcile(con, rel, a.out, pers)
    log('done in %.0f s' % (time.time() - t0))


if __name__ == '__main__':
    main()
