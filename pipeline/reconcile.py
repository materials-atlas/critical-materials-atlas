# -*- coding: utf-8 -*-
"""THE MOAT: reconcile mirror reports on the MONTHLY data. Every physical flow can be reported twice —
the exporter (FOB) and the importer (CIF, which includes freight+insurance). Where we have BOTH sides in
the same month, we reconcile them into one best estimate instead of picking a side (flows_best) or
trusting a raw feed (TDM). Method (a monthly, tractable cousin of CEPII BACI):
  1. canonicalize every row to (exporter, importer, hs6, period) and tag its side (FOB / CIF);
  2. keep the best SOURCE per side (deep national > wide reconciled > mirror), aggregated to HS-6;
  3. estimate the CIF/FOB (CAF/FAB) coefficient EMPIRICALLY from the matched pairs, PER PRODUCT -
     median cif/fob at HS6, falling back to HS4, HS2, then global, as BoP practice does;
  4. put both on a common FOB basis and take the geometric mean.
Output table `flows_reconciled` with `basis` = reconciled | exporter_only | importer_only_adj.
(v1 = equal-weight geomean; reliability-variance weighting is the next refinement.)"""

MIN_PAIRS = 8   # fewest matched pairs that may carry a coefficient of its own
# Ceiling on the applied coefficient, from the Douanes CAF-FAB survey: nothing it measures
# reaches 10% - 9.6% for goods from the Americas is the highest cell in the table, 8.4% for
# extra-EU raw materials, 6.1% by ship. A mirror gap of 20% is therefore not freight, and
# dividing the importer side by it would remove a real disagreement instead of a transport
# cost - turning a flow we should FLAG into one we would silently reconcile. So we deflate only
# by what could plausibly be freight and let the remainder fall through to the disagreement
# test, which is the whole point of having one. Costs 0.0025 log points against BACI - which
# runs its own CIF/FOB model and so cannot arbitrate this - and buys coherence with the rule
# the pipeline already lives by: never fabricate an agreement.
FREIGHT_CEILING = 1.10
HUBS_SQL = "('NLD','BEL','SGP','HKG','ARE','CHE','GBR','LUX','PAN','MYS')"   # entrepot / re-export hubs

SIDES_SQL = """
CREATE OR REPLACE TABLE sides AS
WITH canon AS (
  SELECT period, hs6, material, value_usd,
    CASE WHEN flow='export' THEN reporter ELSE partner END AS exporter,
    CASE WHEN flow='export' THEN partner  ELSE reporter END AS importer,
    CASE WHEN flow='export' THEN 'fob' ELSE 'cif' END AS side,
    CASE source WHEN 'eurostat' THEN 1 WHEN 'comexstat' THEN 1 WHEN 'hmrc' THEN 1 WHEN 'uscensus' THEN 1
                WHEN 'baci' THEN 2 WHEN 'comtrade' THEN 2 WHEN 'mirror' THEN 3 ELSE 9 END AS rank
  FROM flows
  WHERE value_usd IS NOT NULL AND value_usd > 0
    -- only RAW one-sided customs declarations can be reconciled against each other.
    -- baci is already reconciled; mirror is reconstructed FROM baci — pairing them is circular.
    AND source IN ('eurostat', 'comexstat', 'hmrc', 'uscensus', 'comtrade')
),
agg AS (                                   -- collapse CN8/HS10 to HS-6 per (flow, side, source-tier)
  SELECT period, exporter, importer, hs6, side, rank,
         any_value(material) AS material, SUM(value_usd) AS v
  FROM canon GROUP BY 1,2,3,4,5,6
),
best AS (                                  -- keep the best source per (flow, side)
  SELECT *, ROW_NUMBER() OVER (PARTITION BY period, exporter, importer, hs6, side
                               ORDER BY rank, v DESC) AS rn
  FROM agg
)
SELECT period, exporter, importer, hs6, any_value(material) AS material,
       MAX(CASE WHEN side='fob' THEN v END) AS fob,   -- exporter-reported (FOB)
       MAX(CASE WHEN side='cif' THEN v END) AS cif    -- importer-reported (CIF)
FROM best WHERE rn=1 GROUP BY 1,2,3,4
"""


def _reporter_quality(con, markup):
    """Variance-components (lite): from the two-sided pairs, remove SYSTEMATIC exporter/importer biases via
    robust 2-way median centering, then reliability = 1/residual-variance per reporter, SHRUNK toward the
    global residual variance so thin reporters aren't spuriously over-trusted. This separates a reporter's
    correctable systematic bias from its irreducible noise — the right basis for inverse-variance weights.
    Writes reporter_quality(reporter, n_flows, exp_bias, imp_bias, reliability)."""
    import numpy as np, collections
    pr = con.execute(f"SELECT exporter, importer, ln(fob)-ln(cif/{markup}) AS d FROM sides WHERE fob>0 AND cif>0").fetchall()
    con.execute("CREATE OR REPLACE TABLE reporter_quality(reporter VARCHAR, n_flows INTEGER, exp_bias DOUBLE, imp_bias DOUBLE, reliability DOUBLE)")
    if not pr:
        return
    exp = [p[0] for p in pr]; imp = [p[1] for p in pr]; d = np.array([float(p[2]) for p in pr])
    a = collections.defaultdict(float); b = collections.defaultdict(float)
    for _ in range(5):                                    # alternating robust 2-way median centering
        r = d - np.array([b[j] for j in imp])
        byE = collections.defaultdict(list)
        for i, v in zip(exp, r): byE[i].append(v)
        a = {i: float(np.median(v)) for i, v in byE.items()}
        r2 = d - np.array([a[i] for i in exp])
        byI = collections.defaultdict(list)
        for j, v in zip(imp, r2): byI[j].append(v)
        b = {j: float(np.median(v)) for j, v in byI.items()}
    resid = d - np.array([a[i] for i in exp]) - np.array([b[j] for j in imp])
    var_g = float(np.var(resid)) or 0.1
    byR = collections.defaultdict(list)
    for i, j, e in zip(exp, imp, resid):
        byR[i].append(e); byR[j].append(e)
    K = 3.0                                               # shrinkage pseudo-count toward the global variance
    rows = [(rep, len(es), a.get(rep, 0.0), b.get(rep, 0.0),
             1.0 / ((len(es)*float(np.var(es)) + K*var_g) / (len(es)+K) + 0.02))
            for rep, es in byR.items()]
    con.executemany("INSERT INTO reporter_quality VALUES (?,?,?,?,?)", rows)


def _markup_table(con, glob):
    """A CIF/FOB (CAF/FAB) coefficient PER PRODUCT, not one number for everything.

    Balance-of-payments practice estimates this margin by product and transport mode, because
    freight is a far larger share of a tonne of ore than of a tonne of wire. We had one global
    figure, 1.023, and the pipeline's own ablation print already called it "too low for bulk".
    It was: estimated per HS2 the coefficient runs 1.177 for ores (HS26) against 1.011 for
    precious metals (HS71). Applying 2.3% to iron ore was never defensible.

    Estimated from the matched pairs, falling back up the nomenclature - HS6, then HS4, then HS2,
    then global - taking the first level with at least MIN_PAIRS well-behaved observations. Same
    HOW THE OFFICIAL VERSION ACTUALLY WORKS, since we got this wrong twice before checking.
    The compiler does not estimate the coefficient at all. In France the DOUANES produce it and
    the national central bank applies it ("fabisation"); INSEE computes its own from transport-ministry
    data and gets a materially lower figure. And customs does not read it off the declaration
    either: the FAB value of an import is simply not collected, only the CAF value, so the ratio
    is measured by a dedicated SURVEY of transport and insurance costs - 10,000 representative
    transactions in the 2015 round - giving a rate of 3.3% (3.2% in 2009).
    Source: Douanes / DSEE, "Enquete sur les couts de transport et d'assurance", Jan 2016,
    lekiosque.finances.gouv.fr/fichiers/Etudes/thematiques/Etude_CAF_FAB_2015.pdf

    Two things follow, and both cut against how we do it.

    FIRST, the official rate is applied as ONE AGGREGATE NUMBER, "par souci de simplicite et de
    robustesse" - so our per-product table is more granular than what the national central bank
    applies, not less. Granularity here is our choice, not a standard we are catching up to.

    SECOND, and more usefully, the survey DOES measure the variation it declines to apply, and it
    is an independent, freight-only benchmark for what we estimate from mirror gaps:

        by product   raw materials 2.0%   processed goods 3.4%   equipment 6.9%
        by mode      ship 6.1%   air 4.8%   road 2.5%   rail 2.3%
        by origin    neighbouring EU 1.1%   Americas 9.6%   Asia 7.7%
        by regime    intra-EU (DEB) 1.7%   extra-EU (DAU) 7.0%   raw materials, DAU 8.4%

    Our own coefficients run far above that ceiling: manganese ore 20.1%, tantalum 16.6%, bauxite
    15.6%, against 8.4% for extra-EU raw materials in the survey. Freight alone does not plausibly
    reach 20%. So the mirror gap we measure is NOT a freight margin - it is freight plus every
    reason two customs authorities disagree, and for bulk ores the second part dominates. The
    below-1.0 coefficients say the same thing from the other side. Treat these numbers as a
    reconciliation wedge, which is what they are, and never as a transport cost.

    That difference has a consequence worth stating rather than hiding. Two HS2 coefficients come
    out BELOW 1.0 - copper (HS74) at 0.964 and nickel (HS75) at 0.960 - and freight cannot do
    that: CIF is FOB plus transport, so the ratio cannot be less than one. What we are estimating
    is therefore not a pure freight margin; it is freight PLUS reporting asymmetry, and for those
    two the asymmetry dominates. So the APPLIED coefficient is floored at 1.0 (a coefficient that
    is impossible as freight should not be used as one), while the RAW median is kept beside it,
    because "the importer of copper systematically reports less than the exporter" is a finding,
    not an error to be clipped away.

    CEPII'S OWN METHOD, REPLICATED AND PARTLY DECLINED (6 Sep 2026)
    BACI does not take a median. It regresses the observed CIF/FOB ratio on gravity variables and
    a product-specific world median unit value, then applies the FITTED rate (Gaulier & Zignago
    2010); a companion paper computes the ratio from UNIT VALUES, each side normalised by its own
    declared quantity, which cancels the quantity-mismatch error (Gaulier, Mirza, Turban &
    Zignago 2008). Their published CIF/FOB dataset covers 1995-2004 only, so it cannot be applied
    to our window - but the method can be, and was, on our 1,039 matched pairs.

    Result 1, ADOPTED AS EVIDENCE, NOT AS CODE. The unit-value ratio is a far better behaved
    statistic than the value ratio we use:

                              median   in [1,2]   below 1 (impossible)
        value  CIF/FOB         1.002      30%          49%
        unit   CIFu/FOBu       1.071      50%          32%

    Half of our value-based ratios are below 1.0. And the unit-value median, 1.071, lands almost
    exactly on the Douanes survey's extra-EU rate of 7.0% - two independent methods agreeing, which
    is the strongest evidence in this whole file that ~7% is the real freight order of magnitude
    for extra-EU flows.

    Result 2, DECLINED. The gravity regression does not survive our sample size. On 517 usable
    observations across 30 products: R2 = 0.012, contiguity enters POSITIVE (neighbours should be
    cheaper to ship to, not dearer) and the unit-value term enters positive too (higher-value goods
    should carry a LOWER freight share). Two wrong signs and no explanatory power. BACI fits this
    on millions of flows; we have hundreds. The method is right and our sample cannot carry it.

    Result 3, WHY THE CODE DID NOT CHANGE. Switching the applied coefficient to unit-value ratios
    scores 0.6127 against BACI versus 0.6108 for the value ratios - marginally worse, though on a
    benchmark that is itself value-based and runs its own CIF/FOB model, so it cannot really
    arbitrate. More decisive: after the 1.10 ceiling the two methods barely differ - manganese ore
    x1.100 either way, bauxite x1.100 either way, copper cathode x1.000 vs x1.028. Threading
    quantities through the pipeline to move one coefficient by 0.028 is complexity that does not
    earn its keep, which is the same standard that removed reliability weighting from the
    estimator. The finding is recorded here because it is worth knowing; the code stays simple.

    Writes markup_by_hs6(hs6, markup, markup_raw, level, n_pairs).
    """
    con.execute("""CREATE OR REPLACE TABLE markup_levels AS
      SELECT 'hs6' AS level, hs6 AS k, median(cif/fob) AS m, COUNT(*) AS n FROM sides
       WHERE fob>0 AND cif>0 AND cif/fob BETWEEN 0.7 AND 1.5 GROUP BY 2
      UNION ALL
      SELECT 'hs4', substr(hs6,1,4), median(cif/fob), COUNT(*) FROM sides
       WHERE fob>0 AND cif>0 AND cif/fob BETWEEN 0.7 AND 1.5 GROUP BY 2
      UNION ALL
      SELECT 'hs2', substr(hs6,1,2), median(cif/fob), COUNT(*) FROM sides
       WHERE fob>0 AND cif>0 AND cif/fob BETWEEN 0.7 AND 1.5 GROUP BY 2""")
    cap = FREIGHT_CEILING
    con.execute(f"""CREATE OR REPLACE TABLE markup_by_hs6 AS
      WITH codes AS (SELECT DISTINCT hs6 FROM sides),
      pick AS (
        SELECT c.hs6,
               COALESCE(h6.m, h4.m, h2.m, {glob}) AS markup_raw,
               CASE WHEN h6.m IS NOT NULL THEN 'hs6' WHEN h4.m IS NOT NULL THEN 'hs4'
                    WHEN h2.m IS NOT NULL THEN 'hs2' ELSE 'global' END AS level,
               COALESCE(h6.n, h4.n, h2.n, 0) AS n_pairs
        FROM codes c
        LEFT JOIN markup_levels h6 ON h6.level='hs6' AND h6.k=c.hs6           AND h6.n >= {MIN_PAIRS}
        LEFT JOIN markup_levels h4 ON h4.level='hs4' AND h4.k=substr(c.hs6,1,4) AND h4.n >= {MIN_PAIRS}
        LEFT JOIN markup_levels h2 ON h2.level='hs2' AND h2.k=substr(c.hs6,1,2) AND h2.n >= {MIN_PAIRS})
      SELECT hs6, least(greatest(markup_raw, 1.0), {cap}) AS markup, markup_raw, level, n_pairs,
             (markup_raw > {cap}) AS markup_capped FROM pick""")
    return {r[0]: r[1] for r in con.execute(
        "SELECT level, COUNT(*) FROM markup_by_hs6 GROUP BY 1").fetchall()}


# Gaulier, Mirza, Turban & Zignago, "International Transportation Costs Around the World: a New
# CIF/FoB rates Dataset", CEPII, March 2008 - Table 4, COLUMN 4, the specification its authors
# recommend reusing: "we prefer using the coefficients of column 4 to reproduce a new vector of
# CIF/FoB for all of the data at hand." Estimated on 1,501,726 observations; dependent variable
# is the ratio of UNIT values.
#
# Why borrow rather than fit. Our own attempt at this regression failed - 517 observations, R2 of
# 0.012, and two coefficients with the wrong sign: contiguity came out POSITIVE (neighbours dearer
# to ship to than distant countries) and unit value POSITIVE (expensive goods carrying MORE
# freight). Both are right in CEPII's fit, because a million and a half observations identify what
# five hundred cannot. And the slopes are what we actually need: distances between countries do not
# change, and how freight responds to distance is a relationship, not a vintage.
CEPII_2008_COL4 = {
    'dist_log': -0.021, 'dist_log2': 0.004, 'uv_log': -0.032, 'contig': -0.019,
    'comlang_off': 0.006, 'colony': -0.015, 'landlocked_exp': 0.015, 'landlocked_imp': 0.003,
}
# What does NOT transfer, and is therefore omitted: GDP, GDP per capita, infrastructure, the
# reporting-questionnaire dummies, the year effects and the intercept. Those are level terms,
# twenty years stale, and we do not hold the underlying series. So the SHAPE comes from CEPII and
# the LEVEL is set here, anchored on 1.071 - our own unit-value median, which independently lands
# on the Douanes survey's extra-EU rate of 7.0%. Three sources, one number.
CEPII_ANCHOR = 1.071
LANDLOCKED = {
    'AFG','AND','ARM','AUT','AZE','BDI','BFA','BLR','BOL','BTN','BWA','CAF','CHE','CZE','ETH',
    'HUN','KAZ','KGZ','LAO','LSO','LUX','MDA','MKD','MLI','MNG','MWI','NER','NPL','PRY','RWA',
    'SVK','SRB','SSD','SWZ','TCD','TJK','TKM','UGA','UZB','ZMB','ZWE','LIE','SMR'}


def _cepii_markup(con):
    """A freight coefficient per ROUTE, not per product - which is what freight actually is.

    A product median cannot know that Brazil to China is 17,600 km and Singapore to Malaysia is
    316. The same bauxite on those two journeys does not carry the same freight, and no amount of
    per-product estimation will ever say so. CEPII's coefficients do, because distance is in them.

    Writes markup_route(exporter, importer, hs6, markup_cepii). Missing distance -> no row, and
    the per-product median from markup_by_hs6 stands in.
    """
    import os
    import pandas as pd, numpy as np
    geo = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'raw', 'geodist', 'dist_cepii.xls')
    if not os.path.exists(geo):
        con.execute("CREATE OR REPLACE TABLE markup_route(exporter VARCHAR, importer VARCHAR, "
                    "hs6 VARCHAR, markup_cepii DOUBLE)")
        return 0
    g = pd.read_excel(geo)
    g.columns = [c.lower() for c in g.columns]
    g = g[['iso_o', 'iso_d', 'dist', 'contig', 'comlang_off', 'colony']]

    # the routes we actually need a coefficient for
    d = con.execute("SELECT DISTINCT exporter, importer, hs6 FROM sides").df()
    # world unit value per product, from the export side of the raw flows (BACI excluded: it is
    # already reconciled, and using it here would feed our own benchmark back into the estimate)
    uv = con.execute("""SELECT hs6, median(value_usd/qty_kg) AS u FROM flows
                        WHERE flow='export' AND qty_kg>0 AND value_usd>0 AND source<>'baci'
                        GROUP BY 1""").df()
    d = d.merge(g, left_on=['exporter', 'importer'], right_on=['iso_o', 'iso_d'], how='left')
    d = d.merge(uv, on='hs6', how='left').dropna(subset=['dist', 'u'])
    if not len(d):
        con.execute("CREATE OR REPLACE TABLE markup_route(exporter VARCHAR, importer VARCHAR, "
                    "hs6 VARCHAR, markup_cepii DOUBLE)")
        return 0
    d = d.rename(columns={'u': 'uv'})
    B, ln = CEPII_2008_COL4, np.log
    pred = (B['dist_log'] * ln(d.dist) + B['dist_log2'] * ln(d.dist) ** 2
            + B['uv_log'] * ln(d.uv) + B['contig'] * d.contig.fillna(0)
            + B['comlang_off'] * d.comlang_off.fillna(0) + B['colony'] * d.colony.fillna(0)
            + B['landlocked_exp'] * d.exporter.isin(LANDLOCKED).astype(float)
            + B['landlocked_imp'] * d.importer.isin(LANDLOCKED).astype(float))
    d['markup_cepii'] = np.exp(pred - pred.median() + np.log(CEPII_ANCHOR))
    out = d[['exporter', 'importer', 'hs6', 'markup_cepii']]
    con.register('_route', out)
    con.execute("CREATE OR REPLACE TABLE markup_route AS SELECT * FROM _route")
    return len(out)


def reconcile(con):
    """Given a DuckDB connection with a `flows` table, build `flows_reconciled`. Returns (markup, stats).

    Robust + HONEST (per an adversarial review): a single global freight markup is a ROUGH PLACEHOLDER
    (real CIF/FOB is route/commodity/mode-specific). It's estimated only from well-behaved pairs (cif/fob
    in 0.7-1.5) so asymmetries don't distort it. Each two-sided flow is CLASSIFIED: if the two FOB-basis
    estimates agree (within 2x) -> reconcile with a SIMPLE geometric mean of the two sides. (We PREVIOUSLY
    used a reliability-inverse-variance-weighted geomean, but an ablation against the BACI benchmark showed
    equal weighting is marginally BETTER on ~180 flows — the weighting was complexity that didn't earn its
    keep at this sample size. The reliability metrics w_exporter/w_importer and exp_bias/imp_bias are STILL
    computed and EXPOSED as diagnostics of reporter behaviour; they just no longer drive the point estimate.
    Revisit weighting once the two-sided set is large enough for it to help.) If they DISAGREE we DO NOT fabricate a number (no 'keep-larger', which biases up and
    rewards misreporting): value_recon_fob = NULL, and both sides + the [lo,hi] range stay exposed with
    basis='disagreement'. For critical materials these conflicts are mostly HS ambiguity / re-exports /
    confidentiality, not freight — so exposing them (not smoothing them) is the actual value vs TDM (raw)
    and BACI (annual). BACI is kept as an EXTERNAL QA benchmark, never as an input to the estimate."""
    con.execute(SIDES_SQL)
    markup = con.execute("SELECT median(cif/fob) FROM sides WHERE fob>0 AND cif>0 AND cif/fob BETWEEN 0.7 AND 1.5").fetchone()[0] or 1.05
    levels = _markup_table(con, markup)   # per-product fallback
    n_route = _cepii_markup(con)          # per-ROUTE, from CEPII's published coefficients
    _reporter_quality(con, markup)   # variance-components: de-bias reporter effects + shrinkage-regularized reliabilities
    cap = FREIGHT_CEILING
    con.execute(f"""CREATE OR REPLACE TABLE flows_reconciled AS
      WITH s AS (SELECT sides.*, mk.markup_raw, mk.level AS markup_level,
                        -- route coefficient first, product median only where no distance exists
                        least(greatest(COALESCE(rt.markup_cepii, mk.markup), 1.0), {cap}) AS markup,
                        CASE WHEN rt.markup_cepii IS NOT NULL THEN 'cepii_route'
                             ELSE 'product_median' END AS markup_method,
                        cif / least(greatest(COALESCE(rt.markup_cepii, mk.markup), 1.0), {cap})
                          AS fob_from_cif
                 FROM sides LEFT JOIN markup_by_hs6 mk USING (hs6)
                 LEFT JOIN markup_route rt USING (exporter, importer, hs6))
      SELECT s.period, s.exporter, s.importer, s.hs6, s.material,
        (s.exporter IN {HUBS_SQL} OR s.importer IN {HUBS_SQL}) AS via_entrepot,
        s.fob, s.cif, s.markup AS cif_fob_markup, s.markup_raw AS cif_fob_markup_raw,
        s.markup_level AS cif_fob_markup_level, s.markup_method AS cif_fob_method,
        re.reliability AS w_exporter, ri.reliability AS w_importer,
        CASE WHEN s.fob IS NOT NULL AND s.cif IS NOT NULL THEN least(s.fob, s.fob_from_cif) END AS value_lo_fob,
        CASE WHEN s.fob IS NOT NULL AND s.cif IS NOT NULL THEN greatest(s.fob, s.fob_from_cif) END AS value_hi_fob,
        -- how tightly the two customs sides agree (0..1): honest per-flow confidence, exposed not hidden
        CASE WHEN s.fob IS NOT NULL AND s.cif IS NOT NULL
             THEN ROUND(least(s.fob, s.fob_from_cif) / greatest(s.fob, s.fob_from_cif), 3) END AS agreement,
        CASE WHEN s.fob IS NULL THEN s.fob_from_cif
             WHEN s.cif IS NULL THEN s.fob
             WHEN s.fob_from_cif/s.fob BETWEEN 0.5 AND 2                             -- agree -> SIMPLE geometric mean of the two FOB-basis sides
               THEN sqrt(s.fob * s.fob_from_cif)                                     -- ABLATION-DRIVEN: equal-weight beats the reliability-weighted
             ELSE NULL END AS value_recon_fob,                                       --   version against BACI on ~180 flows; weights kept only as exposed diagnostics. disagree -> NULL.
        CASE WHEN s.fob IS NULL THEN 'importer_only_adj'
             WHEN s.cif IS NULL THEN 'exporter_only'
             WHEN s.fob_from_cif/s.fob BETWEEN 0.5 AND 2 THEN 'reconciled'
             ELSE 'disagreement' END AS basis,
        -- WHY a disagreement (honesty with receipts, per council): name the LIKELY cause instead of just refusing
        CASE WHEN s.fob IS NOT NULL AND s.cif IS NOT NULL AND s.fob_from_cif/s.fob NOT BETWEEN 0.5 AND 2 THEN
             CASE WHEN (s.exporter IN {HUBS_SQL} OR s.importer IN {HUBS_SQL}) THEN 'entrepot / re-export leg'
                  WHEN s.cif/s.fob > 3 THEN 'importer reports >>3x (exporter under-invoicing or re-export inflation)'
                  WHEN s.fob/s.cif > 3 THEN 'exporter reports >>3x (importer under-reporting or confidentiality)'
                  WHEN COALESCE(re.n_flows,0) < 5 OR COALESCE(ri.n_flows,0) < 5 THEN 'thin / low-reliability reporter'
                  ELSE 'unexplained (likely HS-code ambiguity or monthly timing mismatch)' END
        END AS disagree_reason
      FROM s LEFT JOIN reporter_quality re ON s.exporter = re.reporter LEFT JOIN reporter_quality ri ON s.importer = ri.reporter""")
    stats = {r[0]: (r[1], r[2]) for r in con.execute(
        "SELECT basis, COUNT(*), ROUND(SUM(value_recon_fob)/1e9,2) FROM flows_reconciled GROUP BY 1").fetchall()}
    stats["_markup_levels"] = levels
    stats["_n_route"] = n_route
    return markup, stats
