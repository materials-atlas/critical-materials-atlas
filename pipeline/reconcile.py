# -*- coding: utf-8 -*-
"""THE MOAT: reconcile mirror reports on the MONTHLY data. Every physical flow can be reported twice —
the exporter (FOB) and the importer (CIF, which includes freight+insurance). Where we have BOTH sides in
the same month, we reconcile them into one best estimate instead of picking a side (flows_best) or
trusting a raw feed (TDM). Method (a monthly, tractable cousin of CEPII BACI):
  1. canonicalize every row to (exporter, importer, hs6, period) and tag its side (FOB / CIF);
  2. keep the best SOURCE per side (deep national > wide reconciled > mirror), aggregated to HS-6;
  3. estimate the CIF/FOB freight markup EMPIRICALLY from the matched pairs (median cif/fob);
  4. put both on a common FOB basis and take the geometric mean.
Output table `flows_reconciled` with `basis` = reconciled | exporter_only | importer_only_adj.
(v1 = equal-weight geomean; reliability-variance weighting is the next refinement.)"""

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
    _reporter_quality(con, markup)   # variance-components: de-bias reporter effects + shrinkage-regularized reliabilities
    con.execute(f"""CREATE OR REPLACE TABLE flows_reconciled AS
      WITH s AS (SELECT *, cif/{markup} AS fob_from_cif FROM sides)
      SELECT s.period, s.exporter, s.importer, s.hs6, s.material,
        (s.exporter IN {HUBS_SQL} OR s.importer IN {HUBS_SQL}) AS via_entrepot,
        s.fob, s.cif, {markup} AS cif_fob_markup,
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
    return markup, stats
