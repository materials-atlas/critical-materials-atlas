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
   on every usable pair (the normal equations are accumulated in the database), with their
   Cook's distance filter (D > 4/n) applied exactly before a second solve. The importer's value divided by the predicted rate is its FOB
   value; not applied to countries that report imports FOB (their footnote 17: Algeria, Georgia,
   South Africa and the SACU), and to Canada only where it narrows the gap.
2. TIMING (ours, the owner's choice (c)). The two sides book one shipment in different months,
   departure on one side and arrival on the other, and a per-month reconciliation then counts it
   twice. A month declared by both sides is left alone. An exporter's declaration with no
   counterpart in its month is matched with an unmatched importer's declaration on the same
   corridor one or two months later, nearest first, and the importer's value is brought onto the
   exporter's month. Yearly data never needed this.
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
    for c in ('dist', 'distw', 'contig'):            # the xls holds '..' for missing, read as text
        g[c] = pd.to_numeric(g[c], errors='coerce')
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
def fit_freight(con, geo, work):
    """The paper's model II on EVERY usable pair, not a sample: the normal equations X'WX and
    X'Wy are accumulated inside DuckDB (per-period sums of weighted cross-products, which is all
    the month dummies need), solved in numpy, and the paper's Cook's-distance filter is applied
    exactly - leverage per observation from (X'WX)^-1, D_i > 4/n dropped - before a second
    solve. Nothing leaves the database but the moments."""
    con.register('geo', geo)
    con.execute("""CREATE OR REPLACE TABLE uv AS
        SELECT period, hs6, median(vx / qx) AS uv FROM pairs WHERE qx > 0 AND vx > 0 GROUP BY 1, 2""")
    ll = pd.DataFrame({'iso3': sorted(LANDLOCKED)}); con.register('ll', ll)
    con.execute("""CREATE OR REPLACE TABLE fobs AS
        SELECT p.period, ln((vm / qm) / (vx / qx)) AS y, LEAST(qx, qm) / GREATEST(qx, qm) AS w,
               ln(g.d) AS c1, ln(g.d) * ln(g.d) AS c2, COALESCE(g.contig, 0) AS c3,
               CASE WHEN le.iso3 IS NULL THEN 0 ELSE 1 END AS c4, CASE WHEN li.iso3 IS NULL THEN 0 ELSE 1 END AS c5,
               ln(u.uv) AS c6, TRUE AS keep
        FROM pairs p JOIN geo g ON g.iso_o = p.exporter AND g.iso_d = p.importer JOIN uv u USING (period, hs6)
             LEFT JOIN ll le ON le.iso3 = p.exporter LEFT JOIN ll li ON li.iso3 = p.importer
        WHERE vx > 0 AND vm > 0 AND qx > 0 AND qm > 0 AND u.uv > 0 AND NOT p.importer IN (%s)""" % (
        ','.join("'%s'" % c for c in FOB_IMPORTERS)))
    n_all = con.execute("SELECT count(*) FROM fobs").fetchall()[0][0]
    if n_all < 1000:
        log('freight: only %d usable pairs - falling back to a flat 3.3%% rate' % n_all)
        return {'flat': 1.033, 'n': int(n_all)}
    periods = [r[0] for r in con.execute("SELECT DISTINCT period FROM fobs ORDER BY 1").fetchall()]
    T = len(periods); K = 7 + T - 1
    cols = ['1', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6']

    def moments():
        """per period: sum w, sum w*c_a, sum w*c_a*c_b, sum w*y, sum w*c_a*y, sum w*y*y, count"""
        terms = ['SUM(w) AS sw', 'SUM(w*y) AS swy', 'SUM(w*y*y) AS swyy', 'COUNT(*) AS cnt']
        for i, ca in enumerate(cols):
            terms.append('SUM(w*%s) AS m%d' % (ca, i))
            terms.append('SUM(w*%s*y) AS my%d' % (ca, i))
            for j, cb in enumerate(cols):
                if j >= i:
                    terms.append('SUM(w*%s*%s) AS m%d_%d' % (ca, cb, i, j))
        return con.execute("SELECT period, %s FROM fobs WHERE keep GROUP BY period ORDER BY period" % ', '.join(terms)).df().set_index('period')

    def solve(M):
        XtWX = np.zeros((K, K)); XtWy = np.zeros(K)
        for t, p in enumerate(periods):
            if p not in M.index:
                continue
            r = M.loc[p]
            for i in range(7):
                XtWy[i] += r['my%d' % i]
                for j in range(7):
                    XtWX[i, j] += r['m%d_%d' % (min(i, j), max(i, j))]
            if t > 0:                                   # the period's dummy column
                d = 7 + t - 1
                XtWX[d, d] += r['sw']; XtWy[d] += r['swy']
                for i in range(7):
                    XtWX[i, d] += r['m%d' % i]; XtWX[d, i] += r['m%d' % i]
        beta = np.linalg.solve(XtWX, XtWy)
        rss = float(M['swyy'].sum() - 2 * beta @ XtWy + beta @ XtWX @ beta)
        n = int(M['cnt'].sum())
        return beta, XtWX, rss / max(n - K, 1), n

    beta, XtWX, s2, n = solve(moments())
    # Cook's distance: D = r^2 h / (K s2 (1-h)^2), h = w x'(X'WX)^-1 x, per observation in SQL
    A = np.linalg.inv(XtWX)
    cc = ' + '.join('%r*%s*%s' % (float(A[i, j]) * (1 if i == j else 2), cols[i], cols[j]) for i in range(7) for j in range(i, 7))
    per = pd.DataFrame({'period': periods, 'tdiag': [0.0] + [A[7 + t - 1, 7 + t - 1] for t in range(1, T)],
                        **{'tc%d' % i: [0.0] + [2 * A[i, 7 + t - 1] for t in range(1, T)] for i in range(7)}})
    con.register('per', per)
    bexpr = ' + '.join('%r*%s' % (float(beta[i]), cols[i]) for i in range(7))
    tfe = pd.DataFrame({'period': periods, 'tfe': [0.0] + beta[7:].tolist()}); con.register('tfe0', tfe)
    con.execute("""CREATE OR REPLACE TABLE fobs2 AS
        SELECT f.* EXCLUDE (keep),
               (f.w * ((%s) + per.tdiag + %s)) AS h,
               (f.y - (%s) - t.tfe) AS r
        FROM fobs f JOIN per USING (period) JOIN tfe0 t USING (period)""" % (
        cc, ' + '.join('per.tc%d*%s' % (i, cols[i]) for i in range(7)), bexpr))
    con.execute("""CREATE OR REPLACE TABLE fobs AS
        SELECT * EXCLUDE (h, r), (r*r*h / (%d * %r * (1 - h) * (1 - h))) <= %r AS keep FROM fobs2""" % (K, float(s2), float(4.0 / n)))
    con.execute("DROP TABLE fobs2")
    beta, XtWX, s2, n2 = solve(moments())
    names = ['intercept', 'ln_dist', 'ln_dist2', 'contig', 'landlocked_exp', 'landlocked_imp', 'ln_uv']
    coef = dict(zip(names, beta[:7].tolist()))
    tfe = dict(zip(periods, [0.0] + beta[7:].tolist()))
    tfe_df = pd.DataFrame({'period': periods, 'tfe': [0.0] + beta[7:].tolist()}); con.register('tfe1', tfe_df)
    mean_rate = con.execute("""SELECT avg(exp((%s) + t.tfe)) - 1 FROM fobs f JOIN tfe1 t USING (period) WHERE keep""" % (
        ' + '.join('%r*%s' % (float(beta[i]), cols[i]) for i in range(7)))).fetchall()[0][0]
    out = {'coef': coef, 'time_fe': {str(k): v for k, v in tfe.items()}, 'n': int(n2), 'dropped': int(n - n2),
           'mean_cif_rate': float(mean_rate), 'resid_sd': float(np.sqrt(s2))}
    json.dump(out, open(os.path.join(work, 'freight_fit.json'), 'w'), indent=1)
    log('freight fit on %s pairs (%s out by Cook distance > 4/n): mean CIF rate %.1f%%, ln dist %.3f, ln dist2 %.4f, '
        'contig %.3f, landlocked exp %.3f imp %.3f, ln uv %.3f' % (
            format(out['n'], ','), format(out['dropped'], ','), 100 * out['mean_cif_rate'], coef['ln_dist'],
            coef['ln_dist2'], coef['contig'], coef['landlocked_exp'], coef['landlocked_imp'], coef['ln_uv']))
    con.execute("DROP TABLE fobs")
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
def align_timing(con, lags, work):
    """Shipment matching at the level the data allow. A month where both sides declared the
    corridor is a matched month and is left alone. An exporter's declaration with no importer
    counterpart that month (an orphan) is matched with an importer's orphan on the same corridor
    1..lags months LATER - the goods were booked on departure by one side and on arrival by the
    other - and the importer's value is brought onto the exporter's month. Nearest lag first, each
    orphan used once. Nothing is smoothed and nothing is moved that already agrees."""
    con.execute("""CREATE OR REPLACE TABLE adj2 AS
        SELECT *, (period // 100) * 12 + period % 100 AS m, vm_fob AS vm_al, qm AS qm_al,
               CAST(NULL AS INTEGER) AS matched_lag FROM adj""")
    moved = 0
    for l in range(1, max(lags, 0) + 1):
        con.execute("""CREATE OR REPLACE TEMP TABLE mt AS
            SELECT x.exporter, x.importer, x.hs6, x.m AS mx, y.m AS my
            FROM adj2 x JOIN adj2 y ON y.exporter = x.exporter AND y.importer = x.importer AND y.hs6 = x.hs6 AND y.m = x.m + %d
            WHERE x.vx IS NOT NULL AND x.vm_al IS NULL AND x.matched_lag IS NULL
              AND y.vm_al IS NOT NULL AND y.vx IS NULL AND y.matched_lag IS NULL""" % l)
        n = con.execute("SELECT count(*) FROM mt").fetchall()[0][0]
        if not n:
            continue
        # move the importer's orphan onto the exporter's month, and retire the importer's month
        con.execute("""UPDATE adj2 SET vm_al = y.vm_fob, qm_al = y.qm, matched_lag = %d
                       FROM mt JOIN adj2 y ON y.exporter = mt.exporter AND y.importer = mt.importer AND y.hs6 = mt.hs6 AND y.m = mt.my
                       WHERE adj2.exporter = mt.exporter AND adj2.importer = mt.importer AND adj2.hs6 = mt.hs6 AND adj2.m = mt.mx""" % l)
        con.execute("""UPDATE adj2 SET vm_al = NULL, qm_al = NULL, matched_lag = -%d
                       FROM mt WHERE adj2.exporter = mt.exporter AND adj2.importer = mt.importer AND adj2.hs6 = mt.hs6 AND adj2.m = mt.my""" % l)
        moved += n
        log('timing: lag %d - %s importer orphans matched to an exporter month' % (l, format(n, ',')))
    con.execute("DELETE FROM adj2 WHERE vx IS NULL AND vm_al IS NULL")
    con.execute("ALTER TABLE adj2 DROP COLUMN m")
    s = con.execute("SELECT count(*), count(*) FILTER (WHERE vx IS NOT NULL AND vm_al IS NOT NULL) FROM adj2").fetchall()[0]
    log('timing: %s flows after matching, %s two-sided (%s moved)' % (format(s[0], ','), format(s[1], ','), format(moved, ',')))
    return moved


# ----------------------------------------------------------------------------------------------
# 3. reliability: the paper's reporting-distance regression and sigma transformation
# ----------------------------------------------------------------------------------------------
def fit_reliability(con, work):
    # every two-sided pair: the paper trims nothing here
    d = con.execute("""SELECT exporter, importer, period, hs6, abs(ln(vx) - ln(vm_al)) AS rd,
                              ln((vx + vm_al) / 1000.0) AS w
                       FROM adj2 WHERE vx > 0 AND vm_al > 0
                       ORDER BY exporter, importer, period, hs6""").df()
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
               vx, vm, vm_fob, vm_al, qx, qm, rate AS markup, matched_lag,
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
