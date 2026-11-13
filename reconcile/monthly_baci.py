# -*- coding: utf-8 -*-
"""A monthly BACI: CEPII's reconciliation of mirror flows, as written in their paper, month by
month, to the latest published period.

CEPII's BACI (Gaulier & Zignago, CEPII WP 2010-23) makes one number of the two declarations of
a bilateral flow - the exporter's, FOB, and the importer's, CIF.

READ FIRST (10 Nov 2026, night). The 2010 paper and today's BACI are not the same thing. Read off
BACI V202601's own output against the raw annual declarations (diagnose_vs_baci.py,
recover_baci_weights.py): (1) nothing is removed from import values - BACI = a*export + b*import
with a + b = 1.0000, and a flow only the importer declared is in BACI to the dollar; (2) the
weight is exactly a ratio of two country constants, a = V_j / (V_i + V_j), the paper's equation
(3); (3) those constants can be recovered from the output. The defaults below therefore are
--fob-rule none and --timing window, and --baci-weights takes the recovered constants; with them
the slice is within 10% of BACI on 82-84% of flows. The paper's own reading stays available
(--fob-rule paper) and is 20 points worse. Their procedure, and what this
script does with it (version 2, 10 Nov 2026; version 1 used published coefficients and a
different reliability model, and is in the git history):

0. DATA. Only the total line of a declaration is a flow (customs 'C00', transport 0, second
   partner 0); flows 'M' and 'X'; partner "World" dropped; the UN's numeric codes mapped to
   ISO3 with the country table BACI ships, codes it does not know dropped. "Areas not elsewhere
   specified" (partner 899) are reallocated by the rule in the paper's appendix, exporter side:
   when the exporter's declared total to named partners falls short of what those partners
   declare, the NES value fills that gap in proportion to the shortfalls; what is left is set
   against the partners the exporter never named and reported (nothing identified changes
   there). Hong Kong's and the United States' re-exports are taken out of their exports, as BACI
   does, because their destination is not known.
1. FREIGHT (paper section 2.3). The CIF rate of a flow is predicted from a gravity equation
   ESTIMATED ON THE DATA: ln(UVm/UVx) on ln distance, ln distance squared, contiguity, exporter
   landlocked, importer landlocked, ln world median unit value of the product, and time dummies
   - their model II: unit-value ratio, each observation weighted by min(Qx,Qm)/max(Qx,Qm).
   on every usable pair (the normal equations are accumulated in the database), with their
   Cook's distance filter (D > 4/n) applied exactly before a second solve. The importer's value divided by the predicted rate is its FOB
   value; not applied to countries that report imports FOB (their footnote 17: Algeria, Georgia,
   South Africa and the SACU), and to Canada only where it narrows the gap.
2. TIMING (ours; yearly data never needed it). The two sides book one shipment in different
   months. BACI's arithmetic settles it: it weights the two sides' YEAR totals, and the monthly
   series that adds up to exactly that is w*x_t + (1-w)*m_t over every month, a month in which
   one side booked nothing counting as its zero when that side filed the month and declares the
   corridor somewhere in the year (--timing window, the default). A side that did not file, or
   never declares the corridor that year, is missing, and the flow is the other declaration, as
   in BACI. --timing match is the earlier treatment (pair orphan declarations one or two months
   apart); it left flows with alternating sides 17% above BACI and is kept for comparison.
3. RELIABILITY (paper section 2.4), exactly. Reporting distance RD = |ln(Vx/Vm)| on two-sided
   flows; equation (5), RD on exporter, importer, period and product effects with sum-to-zero
   constraints, least squares weighted by ln of the sum of the two reports, solved through the
   normal equations with the regression's own standard errors; footnote 22,
   sigma_i = (pi/2)(LS_RD_i - min LS_RD - 2 stderr_i); equation (3) for the weight. The same on
   the two reported quantities. Nothing added: an earlier version carried a threshold on the
   number of pairs and a median for small reporters, which were ours, not the paper's, and are
   gone. Where the paper is silent (a negative sigma for the best reporter) the choice is a
   visible parameter, --sigma-floor.
4. RECONCILIATION. Weighted arithmetic mean of the two FOB values; a flow declared once is that
   declaration; quantities (net weight) with the same weights.

Estimation steps 1-3 pool every period in the run, as BACI pools its years; step 4 is per month.

    python reconcile/monthly_baci.py --slice raw/crm_monthly.parquet --out raw/monthly_baci_slice
    python reconcile/monthly_baci.py --periods 201908 202609 --out raw/monthly_baci     # corpus

Every declaration is first brought to one HS edition (hs_concordance.py): HS 2017 by default,
BACI's own edition for 2017 onwards, with BACI's product list (2710 merged into 271000, no
chapter 99), so that the comparison converts nothing on BACI's side. Quantities declared in other units get
a weight from mirror-implied rates (section 2.2). Weights are in kilograms throughout.
"""
import argparse
import json
import os
import sys
import time

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hs_concordance import mapping_table   # one HS edition for every declaration

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BULK = os.environ.get('CMA_BULK_DIR', os.path.join(ROOT, 'raw', 'comtrade_bulk'))
COUNTRIES = os.path.join(ROOT, 'raw', 'baci', 'country_codes_V202601.csv')
GEO = os.path.join(ROOT, 'raw', 'geodist', 'dist_cepii.xls')

NES = 899                                  # Comtrade partner "Areas, nes"
BACI_PRODUCTS = os.path.join(ROOT, 'raw', 'baci', 'product_codes_HS17_V202601.csv')
# BACI carries refined petroleum as ONE product: the five 2710 subheadings are merged into 271000
BACI_CODE = "CASE WHEN left(COALESCE(h.code_to, t.hs6), 4) = '2710' THEN '271000' ELSE COALESCE(h.code_to, t.hs6) END"
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
def load_totals(con, periods, slice_path, work, annual=False, hs_target='H5', min_decl=0.0):
    cmap = country_map()
    con.register('cmap', cmap)
    parts = []
    for p in periods:
        if slice_path:
            src = "read_parquet('%s') WHERE period = %d" % (slice_path.replace(chr(92), '/'), int(p))
        else:
            src = "read_parquet('%s/%s/%s_*.parquet', union_by_name=true) WHERE 1=1" % (
                BULK.replace(chr(92), '/'), str(p)[:4], p)
        parts.append("""SELECT period, reporterCode AS rep, partnerCode AS par, cmdCode AS hs6, classificationCode AS ver,
                               flowCode AS flow, primaryValue AS v, CASE WHEN netWgt > 0 THEN netWgt END AS q,
                               CASE WHEN qty > 0 THEN qty END AS qty, qtyUnitCode AS unit
                        FROM %s AND customsCode = 'C00' AND motCode = 0 AND partner2Code = 0
                          AND partnerCode <> 0 AND flowCode IN ('M', 'X', 'RX') AND primaryValue > 0
                          AND primaryValue >= %f
                          AND length(cmdCode) = 6""" % (src, min_decl))   # the corpus also carries the 2- and 4-digit aggregates
    tot = os.path.join(work, 'totals.parquet').replace(chr(92), '/')
    con.execute("COPY (%s) TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD)" % (' UNION ALL '.join(parts), tot))
    # one HS edition: the target's own codes pass through, newer editions convert uniquely,
    # older ones go up (split equally where the UN table lists several candidates)
    hm = mapping_table(hs_target)
    con.register('hsmap', hm[['ver', 'code_from', 'code_to', 'share']])
    con.execute("""CREATE OR REPLACE TABLE tot AS
        SELECT %s AS period, r.iso3 AS reporter, CASE WHEN t.par = %d THEN 'NES' ELSE p.iso3 END AS partner,
               %s AS hs6, t.flow,
               SUM(t.v * COALESCE(h.share, 1.0)) AS v, SUM(t.q * COALESCE(h.share, 1.0)) AS q,
               COUNT(*) = COUNT(t.q) AS q_full,
               CASE WHEN MIN(t.unit) = MAX(t.unit) THEN MAX(t.unit) END AS unit,
               CASE WHEN MIN(t.unit) = MAX(t.unit) AND COUNT(*) = COUNT(t.qty) THEN SUM(t.qty * COALESCE(h.share, 1.0)) END AS qty
        FROM read_parquet('%s') t JOIN cmap r ON t.rep = r.code
             LEFT JOIN cmap p ON t.par = p.code
             LEFT JOIN hsmap h ON h.ver = t.ver AND h.code_from = t.hs6
        WHERE (t.par = %d OR p.iso3 IS NOT NULL) AND left(COALESCE(h.code_to, t.hs6), 2) <> '99'
        GROUP BY 1, 2, 3, 4, 5""" % ('t.period // 100' if annual else 't.period', NES, BACI_CODE, tot, NES))
    # BACI's product list: the UN's HS 2017 with the 2710 subheadings merged into 271000 and no
    # chapter 99. Anything else that is not on it after conversion is counted and dropped.
    if hs_target == 'H5' and os.path.exists(BACI_PRODUCTS):
        bp = pd.read_csv(BACI_PRODUCTS, dtype=str); bp.columns = [c.lower() for c in bp.columns]
        con.register('bprod', pd.DataFrame({'code': bp.iloc[:, 0].str.zfill(6)}))
        off = con.execute("SELECT count(*), COALESCE(sum(v), 0) / 1e9 FROM tot WHERE hs6 NOT IN (SELECT code FROM bprod)").fetchall()[0]
        con.execute("DELETE FROM tot WHERE hs6 NOT IN (SELECT code FROM bprod)")
        log('products: BACI\'s HS 2017 list (2710 merged into 271000, chapter 99 out); %s declarations (%.1f bn USD) on no BACI code dropped' % (
            format(off[0], ','), off[1]))
    # BACI: "re-exportations for Hong Kong and USA are also dropped since there is no way to know the
    # final destination". Their X total includes re-exports; the RX line is taken out of it.
    con.execute("""CREATE OR REPLACE TABLE tot AS
        WITH rx AS (SELECT period, reporter, partner, hs6, v AS v_rx, q AS q_rx FROM tot WHERE flow = 'RX' AND reporter IN ('HKG', 'USA'))
        SELECT t.period, t.reporter, t.partner, t.hs6, t.flow,
               CASE WHEN t.flow = 'X' AND rx.v_rx IS NOT NULL THEN GREATEST(t.v - rx.v_rx, 0) ELSE t.v END AS v,
               CASE WHEN t.flow = 'X' AND rx.v_rx IS NOT NULL AND t.q IS NOT NULL AND rx.q_rx IS NOT NULL THEN GREATEST(t.q - rx.q_rx, 0) ELSE t.q END AS q,
               t.q_full, t.unit, t.qty
        FROM tot t LEFT JOIN rx ON rx.period = t.period AND rx.reporter = t.reporter AND rx.partner = t.partner AND rx.hs6 = t.hs6
        WHERE t.flow IN ('M', 'X')""")
    con.execute("DELETE FROM tot WHERE v <= 0")
    hs = con.execute("""SELECT t.ver, count(*) AS lines, round(100.0 * sum(t.v) / (SELECT sum(v) FROM read_parquet('%s')), 2) AS pct_value,
                               count(*) FILTER (WHERE t.ver <> '%s' AND h.code_to IS NULL) AS unmapped
                        FROM read_parquet('%s') t LEFT JOIN hsmap h ON h.ver = t.ver AND h.code_from = t.hs6
                        GROUP BY 1 ORDER BY 3 DESC""" % (tot, hs_target, tot)).fetchall()
    log('HS editions in the input (target %s): %s' % (hs_target, '; '.join('%s %.1f%% of value, %s lines%s' % (
        v, pv, format(n_, ','), ', %s unmapped kept as is' % format(u, ',') if u else '') for v, n_, pv, u in hs)))
    n = con.execute("SELECT count(*), count(*) FILTER (WHERE partner = 'NES') FROM tot").fetchall()[0]
    log('totals: %s declarations, %s of them to "areas nes"' % (format(n[0], ','), format(n[1], ',')))


def reallocate_nes(con, sides=('X',)):
    """The paper's appendix, written for the exporter's "Area nes" flows (the importer side is
    available but off: the appendix does not do it, and doing both can assign one gap twice).
    Stage 1: if the exporter's declared total to named partners falls short of what those
    partners declare from it, min(V_nes, shortfall) goes to them in proportion to the
    per-partner shortfalls. Stage 2: what is left of V_nes is set against the partners' flows
    the exporter never named: if the residual is smaller it is taken as included in them (set
    to zero), else those flows are subtracted from it. Either way no identified flow changes in
    stage 2; it is reported so the size of the unexplained NES value is known."""
    for flow, mflow in (('X', 'M'), ('M', 'X')):
        if flow not in sides:
            continue
        con.execute("""CREATE OR REPLACE TEMP TABLE nes AS
            WITH own AS (SELECT period, reporter, hs6, SUM(v) FILTER (WHERE partner <> 'NES') AS v_own,
                                MAX(v) FILTER (WHERE partner = 'NES') AS v_nes
                         FROM tot WHERE flow = '%s' GROUP BY 1, 2, 3 HAVING MAX(v) FILTER (WHERE partner = 'NES') > 0),
                 mir AS (SELECT period, partner AS reporter, hs6, reporter AS partner, v AS v_mir
                         FROM tot WHERE flow = '%s' AND partner <> 'NES'),
                 ownp AS (SELECT period, reporter, hs6, partner, v AS v_ownp FROM tot WHERE flow = '%s' AND partner <> 'NES')
            SELECT o.period, o.reporter, o.hs6, m.partner, m.v_mir, p.v_ownp, o.v_nes, o.v_own,
                   SUM(m.v_mir) FILTER (WHERE p.v_ownp IS NOT NULL) OVER w AS v_mir_named,
                   SUM(m.v_mir) FILTER (WHERE p.v_ownp IS NULL) OVER w AS v_mir_unnamed,
                   CASE WHEN p.v_ownp IS NOT NULL THEN GREATEST(m.v_mir - p.v_ownp, 0) ELSE 0 END AS shortfall
            FROM own o JOIN mir m USING (period, reporter, hs6)
                 LEFT JOIN ownp p ON p.period = o.period AND p.reporter = o.reporter AND p.hs6 = o.hs6 AND p.partner = m.partner
            WINDOW w AS (PARTITION BY o.period, o.reporter, o.hs6)""" % (flow, mflow, flow))
        # stage 1: named partners only, in proportion to their shortfalls
        con.execute("""CREATE OR REPLACE TEMP TABLE alloc AS
            SELECT period, reporter, hs6, partner,
                   LEAST(v_nes, GREATEST(COALESCE(v_mir_named, 0) - COALESCE(v_own, 0), 0))
                   * shortfall / NULLIF(SUM(shortfall) OVER (PARTITION BY period, reporter, hs6), 0) AS add_v
            FROM nes WHERE shortfall > 0""")
        n = con.execute("SELECT count(*), SUM(add_v) FROM alloc WHERE add_v > 0").fetchall()[0]
        # stage 2: the residual against the unnamed partners' declarations
        r = con.execute("""WITH s1 AS (SELECT period, reporter, hs6, SUM(add_v) AS added FROM alloc GROUP BY 1, 2, 3),
                                 g AS (SELECT DISTINCT period, reporter, hs6, v_nes, COALESCE(v_mir_unnamed, 0) AS unnamed FROM nes)
                           SELECT SUM(GREATEST(v_nes - COALESCE(added, 0), 0)) AS residual,
                                  SUM(CASE WHEN GREATEST(v_nes - COALESCE(added, 0), 0) < unnamed THEN GREATEST(v_nes - COALESCE(added, 0), 0) ELSE 0 END) AS covered,
                                  SUM(CASE WHEN GREATEST(v_nes - COALESCE(added, 0), 0) >= unnamed THEN GREATEST(v_nes - COALESCE(added, 0), 0) - unnamed ELSE 0 END) AS unexplained
                           FROM g LEFT JOIN s1 USING (period, reporter, hs6)""").fetchall()[0]
        con.execute("""INSERT INTO tot
            SELECT period, reporter, partner, hs6, '%s', add_v, NULL, FALSE, NULL, NULL FROM alloc WHERE add_v > 0""" % flow)
        con.execute("""CREATE OR REPLACE TABLE tot AS
            SELECT period, reporter, partner, hs6, flow, SUM(v) AS v, SUM(q) AS q, BOOL_AND(q_full) AS q_full,
                   CASE WHEN MIN(unit) = MAX(unit) THEN MAX(unit) END AS unit,
                   CASE WHEN MIN(unit) = MAX(unit) AND COUNT(*) = COUNT(qty) THEN SUM(qty) END AS qty
            FROM tot GROUP BY 1, 2, 3, 4, 5""")
        log('areas nes, %s side: stage 1 topped up %s named-partner flows with %.2f bn USD; residual %.2f bn, of which '
            '%.2f bn taken as included in unnamed partners\' declarations and %.2f bn unexplained' % (
                'export' if flow == 'X' else 'import', format(n[0] or 0, ','), (n[1] or 0) / 1e9,
                (r[0] or 0) / 1e9, (r[1] or 0) / 1e9, (r[2] or 0) / 1e9))
    con.execute("DELETE FROM tot WHERE partner = 'NES'")


def convert_units(con, min_pairs=10, max_sd=2.5):
    """Paper section 2.2. A declaration with no weight but a quantity in another unit (pieces,
    litres, m2...) gets a weight from the rate implied by mirror flows: for each product and
    unit, the pairs where one side declared weight and the other that unit give rates
    weight/quantity; the median rate is kept if at least min_pairs pairs exist and the standard
    deviation of their logs is below max_sd (the paper says "standard deviation inferior to 2.5"
    without the scale; the log scale is our reading, the only one that is unit-free). Unknown
    units (-1) and kWh (code 11) are not converted, as the paper does."""
    con.execute("""CREATE OR REPLACE TEMP TABLE rates AS
        WITH x AS (SELECT period, reporter AS e, partner AS i, hs6, q, unit, qty FROM tot WHERE flow = 'X'),
             m AS (SELECT period, partner AS e, reporter AS i, hs6, q, unit, qty FROM tot WHERE flow = 'M'),
             pr AS (SELECT x.hs6, m.unit AS unit, x.q / m.qty AS rate FROM x JOIN m USING (period, e, i, hs6)
                    WHERE x.q > 0 AND m.qty > 0 AND m.q IS NULL AND m.unit NOT IN (-1, 11, 8)
                    UNION ALL
                    SELECT m.hs6, x.unit, m.q / x.qty FROM x JOIN m USING (period, e, i, hs6)
                    WHERE m.q > 0 AND x.qty > 0 AND x.q IS NULL AND x.unit NOT IN (-1, 11, 8))
        SELECT hs6, unit, median(rate) AS rate, count(*) AS n, stddev_samp(ln(rate)) AS sd
        FROM pr WHERE rate > 0 GROUP BY 1, 2 HAVING count(*) >= %d AND stddev_samp(ln(rate)) < %f""" % (min_pairs, max_sd))
    con.execute("""CREATE OR REPLACE TABLE tot AS
        SELECT t.period, t.reporter, t.partner, t.hs6, t.flow, t.v,
               CASE WHEN t.q IS NULL AND t.qty > 0 AND r.rate IS NOT NULL THEN t.qty * r.rate ELSE t.q END AS q,
               CASE WHEN t.q IS NULL AND t.qty > 0 AND r.rate IS NOT NULL THEN TRUE ELSE t.q_full END AS q_full,
               t.unit, t.qty,
               CASE WHEN t.q IS NULL AND t.qty > 0 AND r.rate IS NOT NULL THEN TRUE ELSE FALSE END AS q_converted
        FROM tot t LEFT JOIN rates r ON r.hs6 = t.hs6 AND r.unit = t.unit""")
    s_ = con.execute("""SELECT (SELECT count(*) FROM rates), count(*) FILTER (WHERE q_converted),
                               round(100.0 * sum(v) FILTER (WHERE q IS NOT NULL) / sum(v), 1) FROM tot""").fetchall()[0]
    log('units: %d product-unit rates from mirrors; %s declarations given a weight; value with a weight now %.1f%%' % (
        s_[0], format(s_[1], ','), s_[2]))


def build_pairs(con, window_fill=True):
    con.execute("CREATE OR REPLACE TABLE filed AS SELECT DISTINCT period, reporter, flow FROM tot")
    con.execute("""CREATE OR REPLACE TABLE pairs AS
        WITH x AS (SELECT period, reporter AS exporter, partner AS importer, hs6, v AS vx,
                          CASE WHEN q_full THEN q END AS qx FROM tot WHERE flow = 'X'),
             m AS (SELECT period, partner AS exporter, reporter AS importer, hs6, v AS vm,
                          CASE WHEN q_full THEN q END AS qm FROM tot WHERE flow = 'M')
        SELECT COALESCE(x.period, m.period) AS period, COALESCE(x.exporter, m.exporter) AS exporter,
               COALESCE(x.importer, m.importer) AS importer, COALESCE(x.hs6, m.hs6) AS hs6, vx, qx, vm, qm,
               FALSE AS zero_filled
        FROM x FULL JOIN m ON x.period = m.period AND x.exporter = m.exporter AND x.importer = m.importer AND x.hs6 = m.hs6
        WHERE COALESCE(x.exporter, m.exporter) <> COALESCE(x.importer, m.importer)""")
    n = con.execute("SELECT count(*), count(*) FILTER (WHERE vx IS NOT NULL AND vm IS NOT NULL) FROM pairs").fetchall()[0]
    log('pairs: %s flows, %s declared by both sides in the same period' % (format(n[0], ','), format(n[1], ',')))
    monthly = con.execute("SELECT max(period) FROM pairs").fetchall()[0][0] > 9999
    if window_fill and monthly:
        # BACI weights the two sides' YEAR totals. The monthly series that adds up to exactly that
        # treats a month in which one side booked nothing as that side's zero - when that side
        # filed the month and declares the corridor somewhere in the year. Otherwise it is missing.
        con.execute("""CREATE OR REPLACE TABLE pairs AS
            WITH win AS (SELECT exporter, importer, hs6, period // 100 AS y, count(vx) AS nx, count(vm) AS nm
                         FROM pairs GROUP BY 1, 2, 3, 4)
            SELECT p.period, p.exporter, p.importer, p.hs6,
                   CASE WHEN p.vx IS NULL AND w.nx > 0 AND fx.reporter IS NOT NULL THEN 0.0 ELSE p.vx END AS vx,
                   CASE WHEN p.vx IS NULL AND w.nx > 0 AND fx.reporter IS NOT NULL THEN 0.0 ELSE p.qx END AS qx,
                   CASE WHEN p.vm IS NULL AND w.nm > 0 AND fm.reporter IS NOT NULL THEN 0.0 ELSE p.vm END AS vm,
                   CASE WHEN p.vm IS NULL AND w.nm > 0 AND fm.reporter IS NOT NULL THEN 0.0 ELSE p.qm END AS qm,
                   (p.vx IS NULL AND w.nx > 0 AND fx.reporter IS NOT NULL) OR (p.vm IS NULL AND w.nm > 0 AND fm.reporter IS NOT NULL) AS zero_filled
            FROM pairs p JOIN win w ON w.exporter = p.exporter AND w.importer = p.importer AND w.hs6 = p.hs6 AND w.y = p.period // 100
                 LEFT JOIN filed fx ON fx.period = p.period AND fx.reporter = p.exporter AND fx.flow = 'X'
                 LEFT JOIN filed fm ON fm.period = p.period AND fm.reporter = p.importer AND fm.flow = 'M'""")
        n2 = con.execute("SELECT count(*) FILTER (WHERE zero_filled), count(*) FILTER (WHERE vx IS NOT NULL AND vm IS NOT NULL) FROM pairs").fetchall()[0]
        log('year window: %s one-sided months are the other side\'s zero (it filed the month and declares the corridor that year); '
            '%s flows now carry both sides' % (format(n2[0], ','), format(n2[1], ',')))


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
    # UV_k in the paper is the product's world median unit value, one per product: here the median
    # over the whole window of the exporter-declared unit values (a product-month median moved with
    # whoever happened to report that month - the council's point)
    con.execute("""CREATE OR REPLACE TABLE uv AS
        SELECT hs6, median(vx / qx) AS uv FROM pairs WHERE qx > 0 AND vx > 0 GROUP BY 1""")
    ll = pd.DataFrame({'iso3': sorted(LANDLOCKED)}); con.register('ll', ll)
    con.execute("""CREATE OR REPLACE TABLE fobs AS
        SELECT p.period, ln((vm / qm) / (vx / qx)) AS y, LEAST(qx, qm) / GREATEST(qx, qm) AS w,
               ln(g.d) AS c1, ln(g.d) * ln(g.d) AS c2, COALESCE(g.contig, 0) AS c3,
               CASE WHEN le.iso3 IS NULL THEN 0 ELSE 1 END AS c4, CASE WHEN li.iso3 IS NULL THEN 0 ELSE 1 END AS c5,
               ln(u.uv) AS c6, TRUE AS keep
        FROM pairs p JOIN geo g ON g.iso_o = p.exporter AND g.iso_d = p.importer JOIN uv u USING (hs6)
             LEFT JOIN ll le ON le.iso3 = p.exporter LEFT JOIN ll li ON li.iso3 = p.importer
        WHERE vx > 0 AND vm > 0 AND qx > 0 AND qm > 0 AND u.uv > 0 AND NOT p.importer IN (%s)""" % (
        ','.join("'%s'" % c for c in FOB_IMPORTERS)))
    n_all = con.execute("SELECT count(*) FROM fobs").fetchall()[0][0]
    if n_all < 1000:
        log('freight: only %d usable pairs - falling back to a flat 3.3%% rate (the paper\'s mean), applied with the same exceptions' % n_all)
        return {'coef': {'intercept': float(np.log(1.033)), 'ln_dist': 0.0, 'ln_dist2': 0.0, 'contig': 0.0,
                         'landlocked_exp': 0.0, 'landlocked_imp': 0.0, 'ln_uv': 0.0},
                'time_fe': {}, 'n': int(n_all), 'dropped': 0, 'mean_cif_rate': 0.033, 'resid_sd': float('nan')}
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
        beta = np.linalg.lstsq(XtWX, XtWy, rcond=None)[0]   # a period emptied by the filter leaves a zero column
        rss = float(M['swyy'].sum() - 2 * beta @ XtWy + beta @ XtWX @ beta)
        n = int(M['cnt'].sum())
        return beta, XtWX, rss / max(n - K, 1), n

    beta, XtWX, s2, n = solve(moments())
    # Cook's distance: D = r^2 h / (K s2 (1-h)^2), h = w x'(X'WX)^-1 x, per observation in SQL
    A = np.linalg.pinv(XtWX)
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
        SELECT * EXCLUDE (h, r), (r*r*h / (CAST(%d AS DOUBLE) * CAST(%r AS DOUBLE) * (1 - h) * (1 - h))) <= CAST(%r AS DOUBLE) AS keep FROM fobs2""" % (K, float(s2), float(4.0 / n)))
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


def apply_freight(con, geo, fit, rule='none'):
    """The importer's FOB value. rate_pred is the gravity prediction for every import declaration
    (1 for importers that declare FOB). Which declarations it is applied to:

    rule='observed' (default) - what BACI's output shows (diagnose_vs_baci.py): a flow only the
        importer declared keeps its declared value, and where both sides declared the strip is
        applied only if it brings the two reports closer (the paper's "never worsen").
    rule='paper' - the 2010 text read literally: every CIF import is stripped, one-sided ones
        included (its footnote 23), Canada only where it narrows the gap.
    rule='none' - nothing is removed. This is what BACI V202601 does on the flows we could check
        (recover_baci_weights.py: BACI = a*export + b*import with a + b = 1.0000 on the raw import
        value; flow by flow the implied factor is centred on 1.0006)."""
    c = fit['coef']
    tfe = pd.DataFrame({'period': pd.Series([int(k) for k in fit['time_fe']], dtype='int64'),
                        'tfe': pd.Series(list(fit['time_fe'].values()), dtype='float64')})
    con.register('tfe', tfe)
    ll = pd.DataFrame({'iso3': sorted(LANDLOCKED)}); con.register('ll', ll)
    con.execute("""CREATE OR REPLACE TABLE adj AS
        WITH r AS (SELECT p.*, g.d, g.contig, u.uv, COALESCE(t.tfe, 0) AS tfe,
                          CASE WHEN le.iso3 IS NOT NULL THEN 1 ELSE 0 END AS lle,
                          CASE WHEN li.iso3 IS NOT NULL THEN 1 ELSE 0 END AS lli
                   FROM pairs p LEFT JOIN geo g ON g.iso_o = p.exporter AND g.iso_d = p.importer
                        LEFT JOIN uv u USING (hs6) LEFT JOIN tfe t USING (period)
                        LEFT JOIN ll le ON le.iso3 = p.exporter LEFT JOIN ll li ON li.iso3 = p.importer),
             e AS (SELECT *, CASE WHEN d IS NOT NULL AND uv > 0 THEN
                        exp(%f + %f * ln(d) + %f * ln(d) * ln(d) + %f * COALESCE(contig, 0) + %f * lle + %f * lli + %f * ln(uv) + tfe)
                      ELSE %f END AS rate_raw FROM r),
             f AS (SELECT * EXCLUDE (d, contig, uv, tfe, lle, lli, rate_raw),
                       CASE WHEN importer IN (%s) THEN 1.0 ELSE GREATEST(rate_raw, 1.0) END AS rate_pred FROM e)
        SELECT *, %s AS rate, vm / (%s) AS vm_fob FROM f""" % (
        c['intercept'], c['ln_dist'], c['ln_dist2'], c['contig'], c['landlocked_exp'], c['landlocked_imp'],
        c['ln_uv'], 1.0 + fit['mean_cif_rate'], ','.join("'%s'" % x for x in FOB_IMPORTERS),
        _applied_rate(rule), _applied_rate(rule)))
    s = con.execute("""SELECT avg(rate_pred) FILTER (WHERE vm IS NOT NULL), count(*) FILTER (WHERE vm IS NOT NULL),
                              count(*) FILTER (WHERE vm IS NOT NULL AND rate > 1), count(*) FILTER (WHERE vm IS NOT NULL AND vx IS NOT NULL)
                       FROM adj""").fetchall()[0]
    log('freight (%s rule): predicted rate %.3f on average; applied to %s of %s import declarations (%s are two-sided)' % (
        rule, s[0], format(s[2], ','), format(s[1], ','), format(s[3], ',')))


def _applied_rate(rule, vx='vx', vm='vm', pred='rate_pred'):
    narrows = "(%s > 0 AND %s > 0 AND abs(ln(GREATEST(%s, 1e-9)) - ln(GREATEST(%s, 1e-9) / %s)) < abs(ln(GREATEST(%s, 1e-9)) - ln(GREATEST(%s, 1e-9))))" % (
        vx, vm, vx, vm, pred, vx, vm)
    if rule == 'none':
        return "1.0"
    if rule == 'paper':
        return ("CASE WHEN %s IS NULL THEN 1.0 WHEN importer IN (%s) AND %s IS NOT NULL AND NOT (%s) THEN 1.0 ELSE %s END"
                % (vm, ','.join("'%s'" % x for x in FAS_IMPORTERS), vx, narrows, pred))
    return "CASE WHEN %s IS NOT NULL AND %s IS NOT NULL AND %s > 1 AND %s THEN %s ELSE 1.0 END" % (vx, vm, pred, narrows, pred)


# ----------------------------------------------------------------------------------------------
# 2. timing: the importer's lag profile per route, and the importer's series on the exporter's month
# ----------------------------------------------------------------------------------------------
def align_timing(con, lags, work, rule='none'):
    """Shipment matching at the level the data allow. A month where both sides declared the
    corridor is a matched month and is left alone. An exporter's declaration with no importer
    counterpart that month (an orphan) is matched with an importer's orphan on the same corridor
    1..lags months LATER - the goods were booked on departure by one side and on arrival by the
    other - and the importer's value is brought onto the exporter's month. Nearest lag first, each
    orphan used once. Nothing is smoothed and nothing is moved that already agrees."""
    con.execute("""CREATE OR REPLACE TABLE adj2 AS
        SELECT *, CASE WHEN period > 9999 THEN (period // 100) * 12 + period % 100 ELSE period END AS m, vm_fob AS vm_al, qm AS qm_al,
               CAST(NULL AS INTEGER) AS matched_lag FROM adj""")
    moved = 0
    for l in range(1, max(lags, 0) + 1):
        con.execute("""CREATE OR REPLACE TEMP TABLE mt AS
            SELECT x.exporter, x.importer, x.hs6, x.m AS mx, y.m AS my
            FROM adj2 x JOIN adj2 y ON y.exporter = x.exporter AND y.importer = x.importer AND y.hs6 = x.hs6 AND y.m = x.m + %d
            WHERE x.vx IS NOT NULL AND x.vm_al IS NULL AND x.matched_lag IS NULL
              AND y.vm_al IS NOT NULL AND y.vx IS NULL AND y.matched_lag IS NULL
              -- compatible values only: presence alone would pair a 10k declaration with a 10m one
              AND x.vx / y.vm_al BETWEEN %f AND %f""" % (l, TRIM_LO, TRIM_HI))
        n = con.execute("SELECT count(*) FROM mt").fetchall()[0][0]
        if not n:
            continue
        # move the importer's orphan onto the exporter's month, and retire the importer's month
        # the import now has a counterpart: the strip applies to it by the same rule as any two-sided flow
        moved_val = ("y.vm / (%s)" % _applied_rate(rule, 'adj2.vx', 'y.vm', 'y.rate_pred').replace('importer IN', 'adj2.importer IN')
                     if rule == 'observed' else "y.vm_fob")   # 'none' and 'paper': vm_fob already is what applies
        con.execute("""UPDATE adj2 SET vm_al = %s, qm_al = y.qm, matched_lag = %d
                       FROM mt JOIN adj2 y ON y.exporter = mt.exporter AND y.importer = mt.importer AND y.hs6 = mt.hs6 AND y.m = mt.my
                       WHERE adj2.exporter = mt.exporter AND adj2.importer = mt.importer AND adj2.hs6 = mt.hs6 AND adj2.m = mt.mx""" % (moved_val, l))
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
def fit_reliability(con, work, kind='value', trim=None, floor=0.0, rule='footnote22', rel_fob='same', rel_min=0.0, role_align=0):
    """Paper section 2.4, exactly, for values (kind='value') and, separately, for quantities.

    Reporting distance RD = |ln(V_exporter / V_importer)| on every flow both sides declared.
    Equation (5): RD = alpha_i + beta_j + lambda_t + gamma_k + e, with the sums of each set of
    effects equal to zero, estimated by least squares with each observation weighted by the
    natural log of the sum of the two reports (thousand USD; tons for quantities). The
    least-square means LS_RD_i (exporters) and LS_RD_j (importers) are the effect plus the
    intercept, the other effects being at their zero mean; stderr is the standard error of that
    least-square mean from the regression's covariance matrix s2 (X'WX)^-. Footnote 22:
        sigma_i = (pi / 2) (LS_RD_i - min LS_RD - 2 stderr_i).
    Nothing else: no threshold on the number of observations, no substitution for small
    reporters, no trimming unless `trim` is passed explicitly.

    Two points the paper does not settle, left visible rather than filled in silently:
    (1) the formula gives the best reporter a NEGATIVE sigma (-pi * stderr); `floor` is what such
        values are raised to (0 by default, i.e. the weight formula sees sigma^2 of 0);
    (2) "min" is read as the minimum over the same role (exporters among exporters).

    Solved through the normal equations: the only things read from the data are the weighted
    cross-tables of the four factors, so the sample size does not matter for memory."""
    vx_, vm_ = ('vx', 'vm_al') if kind == 'value' else ('qx', 'qm_al')
    if kind == 'value' and rel_fob != 'same':
        # the reliability sample may strip freight by its own rule (the paper: the reporting distance
        # is measured on imports "now cleaned from CIF rates") while the output keeps another
        vm_ = "(vm_al * rate / (%s))" % _applied_rate(rel_fob)
    cond = "%s > 0 AND %s > 0 AND ln((%s + %s) / 1000.0) > 0" % (vx_, vm_, vx_, vm_)
    if rel_min > 0:
        # the paper's data held no declaration below 1,000 USD (p. 10): the regression sees none
        cond += " AND vx >= %f AND vm >= %f" % (rel_min, rel_min)
    if trim:
        cond += " AND %s / %s BETWEEN %f AND %f" % (vx_, vm_, trim[0], trim[1])
    cols = ['role', 'reporter', 'n', 'ls_rd', 'stderr', 'sigma_raw', 'sigma', 'kind']
    names = ('exporter', 'importer', 'period', 'hs6')
    uniq = {}
    for k in names:
        con.execute("CREATE OR REPLACE TEMP TABLE dim_%s AS SELECT %s AS v, (row_number() OVER (ORDER BY %s) - 1)::INTEGER AS id "
                    "FROM (SELECT DISTINCT %s FROM adj2 WHERE %s)" % (k, k, k, k, cond))
        uniq[k] = np.array([r_[0] for r_ in con.execute("SELECT v FROM dim_%s ORDER BY id" % k).fetchall()], dtype=object)
    con.execute("""CREATE OR REPLACE TEMP TABLE rdt AS
        SELECT de.id AS f0, di.id AS f1, dp.id AS f2, dh.id AS f3,
               abs(ln(%s) - ln(%s)) AS y, ln((%s + %s) / 1000.0) AS w
        FROM adj2 a JOIN dim_exporter de ON de.v = a.exporter JOIN dim_importer di ON di.v = a.importer
             JOIN dim_period dp ON dp.v = a.period JOIN dim_hs6 dh ON dh.v = a.hs6
        WHERE %s""" % (vx_, vm_, vx_, vm_, cond))
    n, sw, swy, swyy = con.execute("SELECT count(*), sum(w), sum(w * y), sum(w * y * y) FROM rdt").fetchall()[0]
    if not n or n < 500:
        log('reliability (%s): only %d two-sided pairs - equal weights' % (kind, n or 0))
        return pd.DataFrame(columns=cols)
    sizes = [len(uniq[k]) for k in names]
    off = [1]
    for z in sizes[:-1]:
        off.append(off[-1] + z)
    P = 1 + sum(sizes)
    A = np.zeros((P + 4, P + 4)); rhs = np.zeros(P + 4)
    A[0, 0] = sw; rhs[0] = swy
    cnt = {}
    for f in range(4):                                       # margins
        r_ = con.execute("SELECT f%d AS f, sum(w) AS m, sum(w * y) AS my, count(*) AS c FROM rdt GROUP BY 1" % f).fetchnumpy()
        idx = off[f] + np.asarray(r_['f'], dtype=np.int64)
        m = np.asarray(r_['m'], dtype=float)
        A[idx, idx] = m; A[0, idx] = m; A[idx, 0] = m
        rhs[idx] = np.asarray(r_['my'], dtype=float)
        c = np.zeros(sizes[f], dtype=np.int64); c[np.asarray(r_['f'], dtype=np.int64)] = np.asarray(r_['c'], dtype=np.int64)
        cnt[f] = c
        A[P + f, off[f]:off[f] + sizes[f]] = 1.0             # the paper's constraint: effects sum to zero
        A[off[f]:off[f] + sizes[f], P + f] = 1.0
    for f in range(4):                                       # cross-tables
        for g in range(f + 1, 4):
            r_ = con.execute("SELECT f%d AS a, f%d AS b, sum(w) AS m FROM rdt GROUP BY 1, 2" % (f, g)).fetchnumpy()
            ia = off[f] + np.asarray(r_['a'], dtype=np.int64); ib = off[g] + np.asarray(r_['b'], dtype=np.int64)
            m = np.asarray(r_['m'], dtype=float)
            A[ia, ib] = m; A[ib, ia] = m
    # A symmetric generalised inverse by eigen-decomposition. A plain inverse returns garbage, without
    # complaint, when two effects cannot be told apart (a country whose only partner trades only
    # with it); the generalised inverse gives such a pair the minimum-norm split and leaves the
    # identified effects exact.
    lam, Q = np.linalg.eigh(A)
    tol = np.abs(lam).max() * 1e-11
    keep = np.abs(lam) > tol
    Ainv = (Q[:, keep] / lam[keep]) @ Q[:, keep].T
    if (~keep).any():
        log('reliability (%s): %d combination(s) of effects are not identified by the data (minimum-norm solution for those)' % (kind, int((~keep).sum())))
    theta = (Ainv @ rhs)[:P]
    rss = float(swyy - theta @ rhs[:P])
    dof = n - (P - 4)
    s2 = rss / max(dof, 1)
    C = Ainv[:P, :P] * s2                                    # covariance of the constrained estimates
    out = []
    for f, role in ((0, 'exporter'), (1, 'importer')):
        sl = slice(off[f], off[f] + sizes[f])
        ls = theta[0] + theta[sl]                            # least-square mean: intercept + effect
        var = C[0, 0] + np.diag(C)[sl] + 2 * C[0, sl]
        stderr = np.sqrt(np.maximum(var, 0))
        if rule == 'ls':                                     # footnote 22: "can be ignored" - the least-square means used directly
            raw = ls.copy()
        else:
            raw = (np.pi / 2) * (ls - ls.min() - 2 * stderr) # footnote 22, as written
        out.append(pd.DataFrame({'role': role, 'reporter': uniq[role], 'n': cnt[f], 'ls_rd': ls, 'stderr': stderr,
                                 'sigma_raw': raw, 'sigma': np.maximum(raw, floor), 'kind': kind}))
    rel = pd.concat(out, ignore_index=True)
    if role_align > 0:
        # Mirror data identify only the SUM of the two sides' errors: whether exporters as a group
        # report worse than importers is not in the regression (sum-to-zero sets it by convention).
        # The paper's footnote 22 settles it by treating the best exporter and the best importer as
        # equally good; here "best" is taken among reporters with at least `role_align` pairs.
        ex, im = rel.role == 'exporter', rel.role == 'importer'
        be = rel.loc[ex & (rel.n >= role_align), 'ls_rd'].min(); bi = rel.loc[im & (rel.n >= role_align), 'ls_rd'].min()
        if np.isfinite(be) and np.isfinite(bi):
            rel.loc[ex, 'sigma_raw'] = rel.loc[ex, 'sigma_raw'] + (bi - be)
            rel['sigma'] = np.maximum(rel['sigma_raw'], floor)
            log('reliability (%s): roles aligned on their best reporter with >= %d pairs (exporters %.3f, importers %.3f): exporters shifted %+.3f'
                % (kind, role_align, be, bi, bi - be))
    rel['well_estimated'] = True
    rel.to_parquet(os.path.join(work, 'reliability_%s.parquet' % kind), index=False)
    e = rel[rel.role == 'exporter']; i = rel[rel.role == 'importer']
    log('reliability (%s, sigma by %s), the paper\'s regression solved exactly on %s pairs%s: intercept %.3f, residual sd %.3f; '
        'exporters %d: sigma median %.3f, max %.2f, %d at or below zero; importers %d: sigma median %.3f, max %.2f, %d at or below zero' % (
            kind, rule, format(n, ','), ' (trimmed to [%g, %g])' % trim if trim else '', theta[0], np.sqrt(s2),
            len(e), e.sigma.median(), e.sigma.max(), int((e.sigma_raw <= 0).sum()),
            len(i), i.sigma.median(), i.sigma.max(), int((i.sigma_raw <= 0).sum())))
    con.execute("DROP TABLE IF EXISTS rdt")
    return rel


def cepii_reliability(path, kind):
    """CEPII published its reporter (un)reliabilities with the 2019-2021 releases: columns c (the
    UN country code), v_unreliability_i / _j (as exporter / importer), q_unreliability_i / _j.
    Returned in the shape fit_reliability produces, for a like-for-like diagnostic run."""
    d = pd.read_csv(path)
    cm = country_map()
    d = d.merge(cm, left_on='c', right_on='code')
    pre = 'v' if kind == 'value' else 'q'
    out = []
    for role, col in (('exporter', pre + '_unreliability_i'), ('importer', pre + '_unreliability_j')):
        out.append(pd.DataFrame({'role': role, 'reporter': d.iso3, 'n': 0, 'ls_rd': np.nan, 'stderr': np.nan,
                                 'sigma': np.maximum(d[col].to_numpy(dtype=float), 0.01), 'well_estimated': True, 'kind': kind}))
    return pd.concat(out, ignore_index=True)


def weight_expr(se2='se2', si2='si2'):
    """The paper's equation (3): the exporter's weight is Vi / (Ve + Vi), V(s) = e^(s^2) (e^(s^2) - 1),
    the variance of a log-normal report error. A sigma of zero is a variance of zero: that report
    is taken whole; two zeros are an even split."""
    V = lambda x: "(exp(LEAST(%s, 300)) * (exp(LEAST(%s, 300)) - 1))" % (x, x)
    ve, vi = V(se2), V(si2)
    return "CASE WHEN %s + %s <= 0 THEN 0.5 ELSE %s / (%s + %s) END" % (ve, vi, vi, ve, vi)


# ----------------------------------------------------------------------------------------------
# 4. reconcile and write
# ----------------------------------------------------------------------------------------------
def reconcile(con, rel_v, rel_q, out_dir, periods, baci_weights=None):
    def sig(rel, role, col):
        if len(rel):
            r = rel[rel.role == role][['reporter', 'sigma']].rename(columns={'reporter': role, 'sigma': col})
            return r, float(r[col].median())
        return pd.DataFrame({role: pd.Series(dtype='str'), col: pd.Series(dtype='float64')}), 0.5
    rev, mev = sig(rel_v, 'exporter', 'sev'); riv, miv = sig(rel_v, 'importer', 'siv')
    req, meq = sig(rel_q, 'exporter', 'seq'); riq, miq = sig(rel_q, 'importer', 'siq')
    for name, df in (('rev', rev), ('riv', riv), ('req', req), ('riq', riq)):
        con.register(name, df)
    # BACI's own country constants, where recovered: w = 1 / (1 + exp(lnV_exporter - lnV_importer))
    if baci_weights:
        bw = pd.read_csv(baci_weights)
        con.register('bwe', bw.dropna(subset=['lnV_exporter'])[['country', 'lnV_exporter']].rename(columns={'country': 'exporter'}))
        con.register('bwi', bw.dropna(subset=['lnV_importer'])[['country', 'lnV_importer']].rename(columns={'country': 'importer'}))
    else:
        con.register('bwe', pd.DataFrame({'exporter': pd.Series(dtype='str'), 'lnV_exporter': pd.Series(dtype='float64')}))
        con.register('bwi', pd.DataFrame({'importer': pd.Series(dtype='str'), 'lnV_importer': pd.Series(dtype='float64')}))
    con.execute("""CREATE OR REPLACE TABLE recon AS
        SELECT period, exporter, importer, hs6,
               CASE WHEN vx IS NOT NULL AND vm_al IS NOT NULL THEN w * vx + (1 - w) * vm_al
                    WHEN vx IS NOT NULL THEN vx ELSE vm_al END AS v,
               CASE WHEN qx IS NOT NULL AND qm_al IS NOT NULL THEN wq * qx + (1 - wq) * qm_al
                    WHEN qx IS NOT NULL THEN qx ELSE qm_al END AS q,
               vx, vm, vm_fob, vm_al, qx, qm, qm_al, rate AS markup, matched_lag, zero_filled,
               CASE WHEN vx IS NOT NULL AND vm_al IS NOT NULL THEN w END AS w_x,
               CASE WHEN qx IS NOT NULL AND qm_al IS NOT NULL THEN wq END AS w_xq,
               CASE WHEN vx IS NOT NULL AND vm_al IS NOT NULL THEN 'both'
                    WHEN vx IS NOT NULL THEN 'x_only' ELSE 'm_only' END AS basis
        FROM (SELECT a.*, CASE WHEN lve IS NOT NULL AND lvi IS NOT NULL THEN 1.0 / (1.0 + exp(lve - lvi)) ELSE %s END AS w, %s AS wq
              FROM (SELECT a0.*, POWER(COALESCE(e.sev, %f), 2) AS se2, POWER(COALESCE(i.siv, %f), 2) AS si2,
                           POWER(COALESCE(eq.seq, %f), 2) AS seq2, POWER(COALESCE(iq.siq, %f), 2) AS siq2,
                           be.lnV_exporter AS lve, bi.lnV_importer AS lvi
                    FROM adj2 a0 LEFT JOIN rev e USING (exporter) LEFT JOIN riv i USING (importer)
                         LEFT JOIN req eq USING (exporter) LEFT JOIN riq iq USING (importer)
                         LEFT JOIN bwe be USING (exporter) LEFT JOIN bwi bi USING (importer)) a)
        WHERE vx IS NOT NULL OR vm_al IS NOT NULL""" % (weight_expr('se2', 'si2'), weight_expr('seq2', 'siq2'),
                                                         mev, miv, meq, miq))
    os.makedirs(out_dir, exist_ok=True)
    for p in periods:
        dest = os.path.join(out_dir, '%s.parquet' % p).replace(chr(92), '/')
        con.execute("COPY (SELECT * FROM recon WHERE period = %d ORDER BY exporter, importer, hs6) TO '%s.part' (FORMAT PARQUET, COMPRESSION ZSTD)" % (int(p), dest))
        os.replace(dest + '.part', dest)
    if baci_weights:
        cov = con.execute("""SELECT count(*) FILTER (WHERE be.exporter IS NOT NULL AND bi.importer IS NOT NULL), count(*)
                             FROM recon r LEFT JOIN bwe be USING (exporter) LEFT JOIN bwi bi USING (importer) WHERE basis = 'both'""").fetchall()[0]
        log('BACI\'s recovered constants weight %s of %s two-sided flows; the rest use the estimated reliabilities' % (format(cov[0], ','), format(cov[1], ',')))
    s = con.execute("""SELECT count(*), count(*) FILTER (WHERE basis = 'both'), round(sum(v) / 1e9, 1),
                              avg(w_x), avg(w_xq), count(DISTINCT period) FROM recon""").fetchall()[0]
    log('reconciled: %s flows over %d periods, %s two-sided (mean exporter weight %.3f on values, %.3f on quantities), '
        '%s bn USD -> %s' % (format(s[0], ','), s[5], format(s[1], ','), s[3] or 0, s[4] or 0, s[2], out_dir))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--periods', nargs='*', help='YYYYMM ... or FROM TO (inclusive); default: all in the source')
    ap.add_argument('--slice', help='a single parquet of raw lines (development), instead of the corpus')
    ap.add_argument('--out', default=os.environ.get('CMA_MONTHLY_DIR', os.path.join(ROOT, 'raw', 'monthly_baci')))
    ap.add_argument('--timing', choices=['window', 'match', 'none'], default='window',
                    help="'window': a month one side left empty is its zero when it filed the month and declares the corridor that year (BACI's annual arithmetic, month by month); 'match': pair orphan declarations across months; 'none'")
    ap.add_argument('--lags', type=int, default=2, help="months of lag searched by --timing match")
    ap.add_argument('--no-nes', action='store_true', help='skip the areas-nes reallocation')
    ap.add_argument('--nes-both-sides', action='store_true', help='also reallocate importers\' NES origins (not in the paper)')
    ap.add_argument('--rd-trim', type=float, nargs=2, metavar=('LO', 'HI'),
                    help='ratio band kept in the reliability regressions (the paper trims nothing; monthly data may need it)')
    ap.add_argument('--fob-rule', choices=['none', 'observed', 'paper'], default='none',
                    help="which import declarations the freight strip applies to: 'observed' = two-sided flows where it narrows the gap (what BACI's output shows); 'paper' = every CIF import (the 2010 text)")
    ap.add_argument('--baci-weights', help='country constants recovered from BACI itself (recover_baci_weights.py); used for the pairs they cover')
    ap.add_argument('--cepii-reliability', help='diagnostic: use the reliabilities CEPII published (a reporter_reliability_*.csv) instead of estimating them')
    ap.add_argument('--sigma-floor', type=float, default=0.0, help='what a sigma below zero is raised to (footnote 22 gives the best reporter a negative one; the paper does not say)')
    ap.add_argument('--min-decl', type=float, default=0.0,
                    help="drop declarations below this value in USD before anything else (the paper, p. 10: 'Data do not include flows below 1,000 dollars')")
    ap.add_argument('--rel-fob-rule', choices=['same', 'none', 'observed', 'paper'], default='same',
                    help="freight rule for the reliability sample only (default: the output's --fob-rule)")
    ap.add_argument('--rel-min-decl', type=float, default=0.0,
                    help="leave declarations below this value in USD out of the reliability regression only (they stay in the output)")
    ap.add_argument('--role-align', type=int, default=0,
                    help="treat the best exporter and the best importer as equally good (footnote 22's assumption), 'best' among reporters with at least this many pairs; 0 = off")
    ap.add_argument('--sigma-rule', choices=['footnote22', 'ls'], default='footnote22',
                    help="footnote22: sigma = pi/2 (LS_RD - min LS_RD - 2 stderr), as written; ls: the least-square means used directly (the paper: the transformation 'can be ignored')")
    ap.add_argument('--hs-target', default='H5', help="HS edition every declaration is brought to (H5 = HS 2017, BACI's own for 2017 onwards)")
    ap.add_argument('--reuse', action='store_true', help='restart from the saved work database at the reliability step (after a crash there)')
    ap.add_argument('--annual', action='store_true',
                    help='control run: the months summed to calendar years before anything else, the paper\'s own frequency')
    a = ap.parse_args()
    work = os.path.join(a.out, '_fit'); os.makedirs(work, exist_ok=True)
    dbfile = os.path.join(work, 'work.duckdb')
    reuse = a.reuse and os.path.exists(dbfile)
    if not reuse:
        for f in (dbfile, dbfile + '.wal'):
            if os.path.exists(f):
                os.remove(f)
    con = duckdb.connect(dbfile)            # on disk: the tables of an all-products run do not fit in 8 GB
    con.execute("SET memory_limit = '%s'" % os.environ.get('CMA_DUCK_MEM', '2500MB'))
    con.execute("SET threads = %d" % int(os.environ.get('CMA_DUCK_THREADS', '3')))
    con.execute("SET temp_directory = '%s'" % os.path.join(work, 'duck_tmp').replace(chr(92), '/'))
    con.execute("SET preserve_insertion_order = false")
    if a.slice:
        pers = [str(r[0]) for r in con.execute("SELECT DISTINCT period FROM read_parquet('%s') ORDER BY 1"
                                               % a.slice.replace(chr(92), '/')).fetchall()]
    else:
        # monthly files are YYYYMM_rep.parquet, the UN's yearly ones YYYY_rep.parquet
        pers = sorted({os.path.basename(f).split('_')[0] for y in os.listdir(BULK) if y.isdigit()
                       for f in os.listdir(os.path.join(BULK, y)) if f.endswith('.parquet')})
    if a.periods:
        if len(a.periods) == 2 and a.periods[0] < a.periods[1]:
            pers = [p for p in pers if a.periods[0] <= p <= a.periods[1]]
        else:
            pers = [p for p in pers if p in set(a.periods)]
    if not pers:
        log('no periods selected'); return
    if a.annual or a.timing != 'match':
        a.lags = 0
    log('monthly BACI v2.1: %d period(s) %s..%s, lags %d%s -> %s' % (
        len(pers), pers[0], pers[-1], a.lags, ', ANNUAL control' if a.annual else '', a.out))
    t0 = time.time()
    if reuse:
        log('reusing the saved work database: straight to the reliability step')
        if a.annual:
            pers = sorted({p[:4] for p in pers})
    else:
        load_totals(con, pers, a.slice, work, annual=a.annual, hs_target=a.hs_target, min_decl=a.min_decl)
        if a.annual:
            pers = sorted({p[:4] for p in pers})
        if not a.no_nes:
            reallocate_nes(con, ('X', 'M') if a.nes_both_sides else ('X',))
        convert_units(con)
        build_pairs(con, window_fill=(a.timing == 'window'))
        geo = geodist()
        fit = fit_freight(con, geo, work)
        apply_freight(con, geo, fit, a.fob_rule)
        align_timing(con, a.lags, work, a.fob_rule)
    trim = tuple(a.rd_trim) if a.rd_trim else None
    rel_v = fit_reliability(con, work, 'value', trim, a.sigma_floor, a.sigma_rule, a.rel_fob_rule, a.rel_min_decl, a.role_align)
    rel_q = fit_reliability(con, work, 'quantity', trim, a.sigma_floor, a.sigma_rule, a.rel_fob_rule, a.rel_min_decl, a.role_align)
    # our own weights against the constants read off BACI: the test that the METHOD is reproduced
    bwf = a.baci_weights or os.path.join(ROOT, 'raw', 'baci', 'recovered_weights_V202601.csv')
    if len(rel_v) and os.path.exists(bwf):
        bw = pd.read_csv(bwf)
        lnv = lambda sg: np.maximum(sg, 1e-3) ** 2 + np.log(np.expm1(np.maximum(sg, 1e-3) ** 2))
        for role, col in (('exporter', 'lnV_exporter'), ('importer', 'lnV_importer')):
            m = rel_v[(rel_v.role == role) & rel_v.well_estimated].merge(bw.dropna(subset=[col]), left_on='reporter', right_on='country')
            if len(m) >= 8:
                ours = lnv(m.sigma.to_numpy(dtype=float)); theirs = m[col].to_numpy(dtype=float)
                log('own weights vs BACI\'s recovered constants, %ss: %d countries, rank correlation %.2f; spread of ln V (sd): ours %.2f, BACI %.2f' % (
                    role, len(m), pd.Series(ours).corr(pd.Series(theirs), method='spearman'), ours.std(), theirs.std()))
    if a.cepii_reliability:
        ours = rel_v
        rel_v = cepii_reliability(a.cepii_reliability, 'value'); rel_q = cepii_reliability(a.cepii_reliability, 'quantity')
        m = ours[ours.well_estimated].merge(rel_v, on=['role', 'reporter'], suffixes=('_ours', '_cepii'))
        log('DIAGNOSTIC: reconciling with CEPII\'s published reliabilities (%d countries). Against ours, well-estimated reporters: '
            'rank correlation %.2f; median sigma ours %.2f, CEPII %.2f' % (
                rel_v.reporter.nunique(), m.sigma_ours.corr(m.sigma_cepii, method='spearman'), m.sigma_ours.median(), m.sigma_cepii.median()))
    reconcile(con, rel_v, rel_q, a.out, pers, a.baci_weights)
    log('done in %.0f s' % (time.time() - t0))


if __name__ == '__main__':
    main()
