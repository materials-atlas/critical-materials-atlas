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
(v1 = equal-weight geomean and STILL THE DEFAULT. v2 - an out-of-sample reliability-variance
weighting - is implemented below, was measured against the same BACI ablation build.py already ran,
and did not beat v1. See RELIABILITY_WEIGHTED for the numbers and the decision.)"""

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
# ============================================================================================
# READ THIS BEFORE QUOTING ANY DISAGREEMENT RATE FROM THIS TABLE  (6 Sep 2026)
#
# The pipeline reports that 51% of two-sided flows disagree by more than 2x, and that the rate
# survives annual aggregation and the exclusion of entrepot hubs. Put to two independent reviewers,
# both said: not a finding, run the USA->CAN placebo, because US export statistics to Canada are
# largely DERIVED from Canadian import data and therefore cannot honestly conflict.
#
# The placebo failed, and tracing why found something worse than the corridor.
#
#     839 of the 1,039 matched pairs - 81% - are COMTRADE AGAINST COMTRADE.
#     907 of them are a SINGLE MONTH, December 2024.
#
# Because four of the five feeds hold exactly one month each: comtrade 202412, uscensus 202607,
# eurostat 202606. Only hmrc (25 months) and comexstat (20) have a series. So the "monthly
# five-source mirror reconciliation" is, today, one preliminary month of one source compared with
# itself, plus about 105 genuine cross-source pairs (Eurostat<->HMRC).
#
# In that month the USA->CAN corridor has an exporter side totalling $129m against an importer
# side totalling $2.5m, with cells like coal at $74.6m one way and $34.56 the other. That is not
# two statistical systems disagreeing. It is one incomplete monthly release.
#
# SO: the 51% describes preliminary Comtrade, not world trade statistics, and must not be
# published as the latter. The disagreement FLAG remains useful per flow; the RATE is not a
# finding until the feeds carry overlapping months from genuinely different compilers.
#
# THE COUNCIL'S CHECKLIST, AND WHERE EACH ITEM STANDS
#   [DONE ] run the USA->CAN placebo            - failed, and tracing it found the cause above
#   [DONE ] report share of TRADE, not of cells - 49% of cells but 30% of value; build.py now
#                                                 prints both and says which to quote
#   [TESTED, PREDICTION WRONG] "tiny cells dominate, the 428x tail is unit errors" - it does not.
#           The rate is 51% at every value floor up to $100k and still 46% above $1m. The
#           disagreements sit in mid-sized flows, not dust. Worth recording BECAUSE the reviewers
#           were confident about it and the data disagreed.
#   [DONE ] cache overwrote periods              - cache.save now merges; check_mirror_independence
#                                                  added, waived to 2026-10-31
#   [OPEN ] refresh comtrade to a real series    - the binding constraint. One month per call.
#   [OPEN ] align partner concepts across feeds  - origin vs consignment vs destination
#   [OPEN ] domestic vs total exports (re-exports) on the exporter side
#   [OPEN ] tonnes-vs-dollars test: recompute on kg after a unit-value filter. If tonnes agree
#           where dollars do not, the story is valuation, not missing trade.
#   [OPEN ] HS4-vs-HS6 collapse: if HS4 agrees where HS6 does not, it is classification shuffle
#   [NOTED] the blank rule is missing-not-at-random for anything consuming value_recon_fob alone.
#           We keep both legs, the range, the agreement score and a reason on every row, so the
#           bias is avoidable - but only by a consumer who uses them.
# ============================================================================================

HUBS_SQL = "('NLD','BEL','SGP','HKG','ARE','CHE','GBR','LUX','PAN','MYS')"   # entrepot / re-export hubs

SIDES_SQL = """
CREATE OR REPLACE TABLE sides AS
WITH canon AS (
  -- A weight of ZERO is not a weight. US Census returns 0 where it has no quantity, and
  -- treating that as a declaration scored 43,067 two-sided flows (11.6%) as weight
  -- disagreements against a side that had said nothing. NULL means 'not declared';
  -- 0 kg of a shipment that was valued at real money is the same statement.
  SELECT period, hs6, material, value_usd, CASE WHEN qty_kg > 0 THEN qty_kg END AS qty_kg,
    CASE WHEN flow='export' THEN reporter ELSE partner END AS exporter,
    CASE WHEN flow='export' THEN partner  ELSE reporter END AS importer,
    CASE WHEN flow='export' THEN 'fob' ELSE 'cif' END AS side,
    CASE source WHEN 'eurostat' THEN 1 WHEN 'comexstat' THEN 1 WHEN 'hmrc' THEN 1 WHEN 'uscensus' THEN 1
                WHEN 'baci' THEN 2 WHEN 'comtrade' THEN 2 WHEN 'mirror' THEN 3 ELSE 9 END AS rank,
    value_basis
  FROM flows
  WHERE value_usd IS NOT NULL AND value_usd > 0
    -- only RAW one-sided customs declarations can be reconciled against each other.
    -- baci is already reconciled; mirror is reconstructed FROM baci — pairing them is circular.
    AND source IN ('eurostat', 'comexstat', 'hmrc', 'uscensus', 'comtrade')
),
agg AS (                                   -- collapse CN8/HS10 to HS-6 per (flow, side, source-tier)
  SELECT period, exporter, importer, hs6, side, rank,
         any_value(material) AS material, SUM(value_usd) AS v,
         -- WEIGHT. Summing a partial set of sub-lines silently understates the total, so a
         -- group gets a weight only when EVERY line in it declared one. A missing weight must
         -- read as "we don't know", never as a smaller shipment.
         CASE WHEN COUNT(*) = COUNT(qty_kg) THEN SUM(qty_kg) END AS q,
         -- one basis per (flow, side): if a side mixes bases the aggregate is not trustworthy,
         -- so MIN/MAX disagreeing is itself the signal and we keep only an unambiguous one.
         CASE WHEN MIN(value_basis) = MAX(value_basis) THEN MIN(value_basis) END AS basis
  FROM canon GROUP BY 1,2,3,4,5,6
),
best AS (                                  -- keep the best source per (flow, side)
  SELECT *, ROW_NUMBER() OVER (PARTITION BY period, exporter, importer, hs6, side
                               ORDER BY rank, v DESC) AS rn
  FROM agg
)
SELECT period, exporter, importer, hs6, any_value(material) AS material,
       MAX(CASE WHEN side='fob' THEN v END) AS fob,   -- exporter-reported (FOB by convention)
       MAX(CASE WHEN side='cif' THEN v END) AS cif,   -- importer-reported: basis DECLARED below
       -- What the importer actually declared. NULL = the source does not say, and then the old
       -- convention (imports are CIF) applies. Canada declares imports FOB and China CIF, so
       -- assuming for everyone was wrong in both directions.
       MAX(CASE WHEN side='cif' THEN basis END) AS cif_basis,
       -- The two declared weights of the SAME physical shipment. Unlike value, these need no
       -- CIF/FOB correction: freight is a cost, not a mass. So a gap here cannot be explained
       -- away by valuation convention - it is a reporting error, and that makes weight the
       -- cleaner of the two agreement tests.
       MAX(CASE WHEN side='fob' THEN q END) AS qty_exp,
       MAX(CASE WHEN side='cif' THEN q END) AS qty_imp
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


# == RELIABILITY-VARIANCE WEIGHTING (v2) ======================================================
# The equal-weight geomean says every declarant is equally good. Two customs services are not: some
# track their partner to within a per cent month after month, some are out by a factor. Weighting
# each declaration by 1/(the variance of its own error) is the textbook answer, and the geomean is
# its w=0.5 special case - so v2 NESTS v1 and can differ from it only through the estimated
# variances. Three things make it harder than the textbook version, and each is a decision recorded
# here rather than a line of code to be taken on trust.
#
# 1. WE NEVER OBSERVE ONE SIDE'S ERROR. A mirror pair gives the DIFFERENCE of two errors,
#    d = ln(fob) - ln(fob_from_cif), whose variance is v_exporter + v_importer. The per-side
#    variances have to be DECOMPOSED out of the pair variances - a two-way variance-components
#    problem - and cannot be read off any single reporter's rows. _reporter_quality already did the
#    lite version of this and then charged the whole pair variance to BOTH reporters, which is
#    exactly the step that makes a noisy reporter's partner look noisy too.
# 2. A VARIANCE FITTED ON A FLOW MUST NOT WEIGHT THAT FLOW. Fit on everything and the weights have
#    already seen the disagreement they are about to adjudicate - which flatters v2 on precisely the
#    comparison we want to run, and is how a refinement gets "validated" by its own training data.
#    So the fit runs REL_FOLDS times, each time holding out one fifth of the CORRIDORS
#    (exporter x importer x hs6), and a flow is only ever weighted by a fit that never saw its
#    corridor. The fold is md5 of the corridor key - not a random draw - so the folds are identical
#    on every machine and every rerun, with no hash seed anywhere in them.
# 3. SQUARED RESIDUALS HAVE A TAIL THAT EATS THE MEAN. A single 400x mirror gap contributes a
#    squared log-residual of ~36 against a typical 0.5, and one such flow can halve a reporter's
#    weight on its own. So squares are winsorized at REL_WINSOR before any averaging, and thin
#    cells are shrunk toward the level above them (chapter -> reporter -> global) instead of being
#    trusted. Robustness chosen on the shape of the residuals - not on the benchmark score.
#
# A weight is a SHARE of a declaration, never a licence to drop one: both weights stay strictly
# inside (0,1) by construction (a variance floor, and a prior fallback), and a missing reliability
# falls back to 0.5/0.5 rather than to zero. Same rule as the qty_kg zero at the top of SIDES_SQL:
# "we don't know" must never be read as "nothing".
#
# NOT THE FIRST WEIGHTING IN THIS REPO, and the difference is the point. The ANNUAL engine that
# reproduces BACI (reconcile/reconcile.py, step 3) already inverse-variance weights: it regresses
# squared mirror discrepancies on reporter dummies, averages each country's two roles into one
# variance, and weights with it - fitted on the same flows it then weights, one variance per
# reporter, no product grain. This is that idea done for the MONTHLY engine and done more
# carefully: roles kept apart, a chapter grain where the data carries one, and the fit held out of
# the corridors it is applied to. Which is also why the two cannot be compared on their scores.
REL_FOLDS = 5             # out-of-sample folds, by CORRIDOR: no flow is weighted by its own corridor
MIN_REL_PAIRS = 30        # fewest pairs before a reporter-role cell may carry a variance of its own
MIN_REL_PAIRS_HS2 = 100   # ... and per reporter x HS2 chapter, where the failure modes differ most
REL_K = 5.0               # shrinkage pseudo-count toward the level above (chapter -> reporter -> global)
REL_WINSOR = 0.95         # squared residuals above this quantile are pulled back to it before averaging
REL_FLOOR = 1e-4          # variance floor: no declarant is exact, and 1/0 is not a weight
# -- THE VERDICT: MEASURED, AND NOT ADOPTED (24 Sep 2026) -------------------------------------
# Scored through build.py's OWN ablation, unchanged: median |ln(estimate / BACI monthly average)| on
# the 23,467 matched 2024 reconciled flows, VALUE basis (USD), same protocol, same flows and the same
# importer-side construction as the equal-weight figure it is compared with. One run, with the
# constants above fixed BEFORE it; nothing here was tuned on this benchmark.
#
#     exporter-only 1.164581   importer-only 1.169377   v1 equal-weight 1.165602   v2 weighted 1.165197
#
# TWO READINGS OF THE SAME BENCHMARK, POINTING OPPOSITE WAYS, which is the whole finding:
#   - the HEADLINE median is 0.000406 log points LOWER for v2 (0.03% of an error of 1.166), and a
#     seeded 1,000-resample bootstrap puts that difference's 95% interval at [-0.0029, +0.0028].
#     It straddles zero by a factor of seven. On this statistic the two estimators are the same.
#   - the PAIRED comparison, which is the more powerful test because it holds the flow fixed, says
#     v1: v1 is closer on 12,064 flows against v2's 11,389 (v2 wins 48.6%, binomial p = 1.1e-05,
#     Wilcoxon p = 0.003), and the median per-flow difference is +0.00013 in v1's favour.
# So v2 does NOT beat v1. Where the benchmark can distinguish them at all it prefers v1, and where
# it cannot it says nothing. RELIABILITY_WEIGHTED therefore stays False: value_recon_fob remains the
# equal-weight geomean, and the weighted estimate ships BESIDE it in value_recon_fob_wv2 with the
# weights and variances that produced it, so a reader can check this instead of believing a comment.
#
# THE FAILURE IS NOT A DEGENERATE-WEIGHT ARTEFACT. The weights bite: the applied exporter share runs
# 0.01 to 0.99 with a median of 0.502, only 4.7% of the benchmark flows (4.9% of all reconciled
# flows) land within 0.01 of equal weighting, and v2 moves the published number by a median 1.4%
# (p95 11%). Three post-hoc probes, run AFTER the
# verdict and recorded as probes rather than as a search for a winner, all land in the same place:
# reporter-level cells only (v2-v1 -0.0013, paired 48.3%), heavier shrinkage K=50 (-0.0002, 48.6%),
# and weights clamped to [0.25, 0.75] (-0.0010, 48.6%). Not one of them reverses the paired test.
#
# WHY, as far as the data can say. Weighting moves the estimate toward the side with the smaller
# mirror-residual variance, which is a ~1% effect; against an ANNUAL benchmark divided by twelve the
# error is ~1.166 log points - a factor of 3.2 - and that is the lumpiness of one month against a
# twelfth of a year, not the choice of side. The benchmark's own noise is three orders of magnitude
# above the thing being tested. It can REFUSE a refinement; it cannot certify one.
# Flip this to True only with a benchmark that can tell the two apart - a MONTHLY external series,
# not an annual one - and only with the ablation rerun and this block rewritten to its numbers.
#
# WHAT THE WEIGHTS ARE WORTH ANYWAY, and why they ship. The variance components rediscover, from
# nothing but mirror gaps, exactly the structure the rest of this file had to be told about: the
# noisiest exporters are NLD 3.27, HKG 4.40, LUX 3.86, IRL 3.09, HUN 3.19 - the entrepot and
# processing hubs already hard-coded in HUBS_SQL - and the tightest are MKD 0.15, URY 0.17, BOL 0.39
# (fold 0, reporter-level residual variance, >=500 pairs). A per-reporter noise measure that finds
# the re-export problem on its own is a data-quality instrument worth publishing even when it is not
# a better estimator.
RELIABILITY_WEIGHTED = False


def _reliability_weights(con):
    """Per-declarant inverse-variance weights, estimated OUT OF SAMPLE. Writes two tables.

    reporter_reliability(fold, role, reporter, hs2, n_pairs, var_resid) - the variance components:
      what one declaration by this reporter, in this role (exporter / importer), in this chapter,
      contributes to a mirror disagreement. hs2='' is the reporter-level cell, reporter='' the
      fold's global prior. Every row is fitted WITHOUT the corridors of its own fold.
    reliability_weights(exporter, importer, hs6, fold, var_exp, var_imp, w_exp, w_imp, rel_level) -
      one row per corridor: the weights actually applied, and which level of cell supplied them.

    Method. d = ln(fob) - ln(fob_from_cif) over the two-sided pairs, on the freight-adjusted sides
    (sides_adj), so the residual is disagreement AFTER the CIF/FOB correction - which is what the
    weights are about. Systematic level bias comes out first, by alternating robust two-way median
    centering (a reporter that is always 3% high is BIASED, not noisy, and only the noise belongs in
    a variance); then E[resid^2] = var_exp[i] + var_imp[j] is solved by Gauss-Seidel on winsorized
    squares with shrinkage. A side's weight is its reliability over the sum of the two, and with
    reliability = 1/variance that is w_exp = var_imp / (var_exp + var_imp).
    """
    import hashlib
    import numpy as np, pandas as pd

    con.execute("CREATE OR REPLACE TABLE reporter_reliability(fold INTEGER, role VARCHAR, "
                "reporter VARCHAR, hs2 VARCHAR, n_pairs INTEGER, var_resid DOUBLE)")
    con.execute("CREATE OR REPLACE TABLE reliability_weights(exporter VARCHAR, importer VARCHAR, "
                "hs6 VARCHAR, fold INTEGER, var_exp DOUBLE, var_imp DOUBLE, w_exp DOUBLE, "
                "w_imp DOUBLE, rel_level VARCHAR)")
    # ORDER BY, not because the fit needs it - medians and bincounts do not care about row order -
    # but because an unordered DuckDB scan may hand back a different order on another machine, and
    # a pinned weight that depends on that is not a pinned weight.
    d = con.execute("""SELECT exporter, importer, hs6, ln(fob) - ln(fob_from_cif) AS d
                       FROM sides_adj WHERE fob > 0 AND fob_from_cif > 0
                       ORDER BY exporter, importer, hs6, period""").df()
    corridors = con.execute("""SELECT DISTINCT exporter, importer, hs6 FROM sides_adj
                               ORDER BY exporter, importer, hs6""").df()
    if not len(d) or not len(corridors):
        return 0

    def _fold(frame):
        """md5 of the corridor key mod REL_FOLDS - hashed once per DISTINCT corridor. Python's own
        hash() is seeded per process and must never decide which data trains which weight."""
        key = (frame.exporter.astype(str) + '|' + frame.importer.astype(str) + '|'
               + frame.hs6.astype(str))
        uniq = {k: int(hashlib.md5(k.encode('utf-8')).hexdigest()[:8], 16) % REL_FOLDS
                for k in sorted(set(key))}
        return key.map(uniq).to_numpy()

    d['fold'] = _fold(d)
    corridors['fold'] = _fold(corridors)
    # factorize with sort=True: a reporter's integer code is a function of its NAME, not of which
    # row happened to arrive first.
    ecode, exps = pd.factorize(d.exporter.astype(str), sort=True)
    icode, imps = pd.factorize(d.importer.astype(str), sort=True)
    hcode, hs2s = pd.factorize(d.hs6.astype(str).str[:2], sort=True)
    dv = d.d.to_numpy(dtype=float)
    fold = d.fold.to_numpy()
    n_e, n_i, n_h = len(exps), len(imps), len(hs2s)

    def _median_by(x, code, n):
        out = np.zeros(n)
        s = pd.Series(x).groupby(code, sort=True).median()
        out[np.asarray(s.index, dtype=int)] = s.to_numpy()
        return out

    def _shrunk_mean_by(x, code, n, prior, floor_n):
        """Cell mean of x shrunk toward `prior` with REL_K pseudo-observations. A cell thinner than
        floor_n is not trusted with a value of its own at all - it returns NaN and the caller falls
        back to the level above."""
        tot = np.bincount(code, weights=x, minlength=n)
        cnt = np.bincount(code, minlength=n).astype(float)
        val = (tot + REL_K * prior) / (cnt + REL_K)
        return np.where(cnt >= floor_n, np.maximum(val, REL_FLOOR), np.nan), cnt

    rows, wrows = [], []
    for k in range(REL_FOLDS):
        fit = fold != k                  # <- the hold-out: this fold's corridors are NOT fitted
        if fit.sum() < MIN_REL_PAIRS:
            continue
        ec, ic, hc, x = ecode[fit], icode[fit], hcode[fit], dv[fit]
        a = np.zeros(n_e); b = np.zeros(n_i)
        for _ in range(5):               # robust two-way median centering: BIAS out, noise left in
            a = _median_by(x - b[ic], ec, n_e)
            b = _median_by(x - a[ec], ic, n_i)
        resid = x - a[ec] - b[ic]
        sq = resid ** 2
        sq = np.minimum(sq, float(np.quantile(sq, REL_WINSOR)))   # the tail does not set a weight
        prior = max(float(sq.mean()) / 2.0, REL_FLOOR)            # ONE side's share of a pair variance
        v_imp_r = np.full(n_i, prior)
        v_exp_c = v_imp_c = None
        for _ in range(4):               # Gauss-Seidel on E[resid^2] = var_exp[i] + var_imp[j]
            t_e = np.maximum(sq - v_imp_r[ic], REL_FLOOR)
            v_exp_c, cnt_e = _shrunk_mean_by(t_e, ec, n_e, prior, MIN_REL_PAIRS)
            v_exp_r = np.where(np.isnan(v_exp_c), prior, v_exp_c)
            t_i = np.maximum(sq - v_exp_r[ec], REL_FLOOR)
            v_imp_c, cnt_i = _shrunk_mean_by(t_i, ic, n_i, prior, MIN_REL_PAIRS)
            v_imp_r = np.where(np.isnan(v_imp_c), prior, v_imp_c)
        # per reporter x CHAPTER where there is enough data for it: freight and misreporting are not
        # the same problem for ore as for wire, and a reporter can be sound on one and not the
        # other. Shrunk toward its OWN reporter-level cell, so a thin chapter stays close to it.
        veh, cnt_eh = _shrunk_mean_by(t_e, ec * n_h + hc, n_e * n_h,
                                      np.repeat(v_exp_r, n_h), MIN_REL_PAIRS_HS2)
        vih, cnt_ih = _shrunk_mean_by(t_i, ic * n_h + hc, n_i * n_h,
                                      np.repeat(v_imp_r, n_h), MIN_REL_PAIRS_HS2)
        rows.append((k, 'exp', '', '', int(fit.sum()), prior))
        rows.append((k, 'imp', '', '', int(fit.sum()), prior))
        for idx in np.nonzero(~np.isnan(v_exp_c))[0]:
            rows.append((k, 'exp', str(exps[idx]), '', int(cnt_e[idx]), float(v_exp_c[idx])))
        for idx in np.nonzero(~np.isnan(v_imp_c))[0]:
            rows.append((k, 'imp', str(imps[idx]), '', int(cnt_i[idx]), float(v_imp_c[idx])))
        for idx in np.nonzero(~np.isnan(veh))[0]:
            rows.append((k, 'exp', str(exps[idx // n_h]), str(hs2s[idx % n_h]),
                         int(cnt_eh[idx]), float(veh[idx])))
        for idx in np.nonzero(~np.isnan(vih))[0]:
            rows.append((k, 'imp', str(imps[idx // n_h]), str(hs2s[idx % n_h]),
                         int(cnt_ih[idx]), float(vih[idx])))

        def _pick(reporter_cell, chapter_cell, ridx, hidx):
            """chapter cell -> reporter cell -> fold prior, and a level label for each. A reporter
            this fit never saw (all of its corridors held out) gets the PRIOR, not a zero: unknown
            reliability is not zero reliability, and a zero weight would delete a declaration from
            the estimate exactly the way a 0 kg quantity once deleted one from the weight test."""
            v = np.full(len(ridx), np.nan)
            lvl = np.full(len(ridx), 'prior', dtype=object)
            safe_r = np.maximum(ridx, 0)
            rv = np.where(ridx >= 0, reporter_cell[safe_r], np.nan)
            lvl = np.where(~np.isnan(rv), 'reporter', lvl)
            v = np.where(~np.isnan(rv), rv, v)
            safe_h = np.maximum(hidx, 0)
            hv = np.where((ridx >= 0) & (hidx >= 0), chapter_cell[safe_r * n_h + safe_h], np.nan)
            lvl = np.where(~np.isnan(hv), 'chapter', lvl)
            v = np.where(~np.isnan(hv), hv, v)
            return np.maximum(np.where(np.isnan(v), prior, v), REL_FLOOR), lvl

        cw = corridors[corridors.fold == k]   # held OUT of this fit = the corridors it may weight
        if not len(cw):
            continue
        hidx = pd.Index(hs2s).get_indexer(cw.hs6.astype(str).str[:2])
        ve, lve = _pick(v_exp_c, veh, pd.Index(exps).get_indexer(cw.exporter.astype(str)), hidx)
        vi, lvi = _pick(v_imp_c, vih, pd.Index(imps).get_indexer(cw.importer.astype(str)), hidx)
        w_exp = vi / (ve + vi)       # reliability = 1/variance, so a side's share is the OTHER variance
        wrows.extend(zip(cw.exporter.astype(str), cw.importer.astype(str), cw.hs6.astype(str),
                         [int(k)] * len(cw), ve.tolist(), vi.tolist(), w_exp.tolist(),
                         (1.0 - w_exp).tolist(),
                         [f'{p}/{q}' for p, q in zip(lve, lvi)]))

    con.executemany("INSERT INTO reporter_reliability VALUES (?,?,?,?,?,?)", rows)
    con.executemany("INSERT INTO reliability_weights VALUES (?,?,?,?,?,?,?,?,?)", wrows)
    return len(wrows)


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
    the Banque de France applies it ("fabisation"); INSEE computes its own from transport-ministry
    data and gets a materially lower figure. And customs does not read it off the declaration
    either: the FAB value of an import is simply not collected, only the CAF value, so the ratio
    is measured by a dedicated SURVEY of transport and insurance costs - 10,000 representative
    transactions in the 2015 round - giving a rate of 3.3% (3.2% in 2009).
    Source: Douanes / DSEE, "Enquete sur les couts de transport et d'assurance", Jan 2016,
    lekiosque.finances.gouv.fr/fichiers/Etudes/thematiques/Etude_CAF_FAB_2015.pdf

    Two things follow, and both cut against how we do it.

    FIRST, the official rate is applied as ONE AGGREGATE NUMBER, "par souci de simplicite et de
    robustesse" - so our per-product table is more granular than what the Banque de France
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
# ANCHOR = 1.049, and the arithmetic behind it, because this is the weakest link in the chain.
# It is the median of the unit-value ratios - importer price-per-kg over exporter price-per-kg -
# across the 990 pairs where both sides declared a value AND a quantity, TRIMMED to the same
# plausible band [0.7, 1.5] used everywhere else in this file.
#
# The trim is not cosmetic. Untrimmed the median is 1.071; trimmed it is 1.049, and the raw
# distribution is wild enough to make the difference real - the middle half alone spans -4% to
# +48%. An earlier version anchored on the untrimmed 1.071, which was inconsistent: every other
# estimate here trims, and there is no reason the anchor should not.
#
# The trimmed figure is also the better match to the external benchmark, once the benchmark is
# read properly. The Douanes survey gives 7.0% for EXTRA-EU imports but 1.7% for intra-EU, and
# 3.3% overall. Our flows are a mix of both - Eurostat and HMRC contribute a lot of intra-EU
# trade - so the right comparator is not the 7.0% cell, it is somewhere between 1.7% and 7.0%.
# 4.9% sits there. 7.1% only matched by picking the single most favourable cell in their table,
# which is how a coincidence gets mistaken for a confirmation.
#
# Sensitivity, stated because the anchor moves the output more than anything else here: at 1.02,
# 47% of route coefficients land on the floor; at 1.10, 43% land on the ceiling. At 1.049 the
# distribution sits inside its bounds rather than piled against one of them.
CEPII_ANCHOR = 1.049
# THE BETTER ANSWER, FOUND 6 SEP 2026: OECD-ITIC. NOT YET INGESTED.
# Asked to go and find the missing year effect, the search turned up something better than an
# extrapolation - the maintained successor to the CEPII dataset itself.
#
#   OECD "International Transport and Insurance Costs of merchandise trade" (ITIC)
#   SDMX dataflow OECD.SDD.TPS:DSD_ITIC@DF_ITIC
#   CIF/FOB margins by REPORTER x PARTNER x HS2017 PRODUCT x YEAR, 200+ economies,
#   1,200+ products, 1995-2022, and HS6 codes are present (HS17_260200 etc).
#   Method: reported CIF and FOB from ~30 economies, gravity model for the rest - CEPII's
#   design, maintained. Published global margin 4.9% in 2022, up from 4.3% in 2015-19.
#
# That 4.9% is the number this file already anchors on, arrived at independently from our own
# trimmed mirror median. Two methods, same figure - which is the confirmation the earlier 7.1%
# only pretended to have.
#
# If ingested, ITIC would replace nearly everything below: no borrowed 2008 coefficients, no
# locally-set level, no freight ceiling of our own invention. A published margin per
# product-partner-year, on the same HS2017 nomenclature our BACI data already uses.
#
# BLOCKED ON THE API, NOT ON THE DECISION. The OECD SDMX endpoint errors on this dataflow:
# version 1.0 returns "doesn't contain a mapping set", 1.1 returns "Object reference not set to
# an instance of an object" across three accept formats, and the unversioned form is ambiguous.
# Server-side, not query-side. The data is downloadable from the OECD Data Explorer UI, which is
# the next route to try.
#
# CAN THE LEVEL ITSELF BE BORROWED FROM CEPII, INSTEAD OF ANCHORED HERE? Tested, and no - for a
# structural reason rather than a missing-file one.
#
# Their intercept is not a free-standing number. It sits in an equation with YEAR EFFECTS covering
# 1995-2004, so the level it implies is the level OF THOSE YEARS. There is no 2024 dummy to apply,
# and the years since include the most extreme freight episode in modern shipping. The level is
# precisely the part of that model that is time-varying, so it is precisely the part that cannot
# travel. Geography could be borrowed because distance does not move; the constant cannot, for the
# same reason in reverse.
#
# Of the four blocks we omit, two ARE obtainable - World Bank GDP and GDP per capita cover 97% of
# our routes - and adding them was tested with CEPII's own coefficients (GDP_exp -0.005, GDP_imp
# -0.011, GDPpc_exp -0.047, GDPpc_imp +0.070). Not adopted, for two reasons:
#   - it pushes 70% of routes onto a bound (35% floor + 35% ceiling, against 58% before), so the
#     clipping would be doing more of the work than the model;
#   - the largest of the four, importer GDP per capita at +0.070, is explained by CEPII themselves
#     as a DEMAND effect, not a transport cost. We are trying to remove freight so two declarations
#     can be compared. Removing a demand effect is not that.
# Dropping just that one term and keeping the rest would be cherry-picking inside someone else's
# specification, which is worse than declining the block. The other two, infrastructure and the
# reporting-questionnaire dummies, we do not hold at all.
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


def _itic_markup(con):
    """The published CIF/FOB margin, per importer-exporter-product, from OECD-ITIC.

    This supersedes everything below it. The per-product medians, the borrowed CEPII 2008
    coefficients, the locally-anchored level and the freight ceiling of our own invention all
    existed because we believed no current published series covered this. One does, it is
    maintained, and it is built the way CEPII built theirs - reported CIF and FOB from ~30
    economies, gravity model for the rest - eighteen years further on.

    Two of our own numbers do not survive contact with it, and both were wrong in the same
    direction. We anchored on 4.9%, the OECD's headline GLOBAL margin - but that is across all
    products, and our basket is not all products. Across the 22 headings our trade actually uses,
    the 2022 median is 7.4%, and the bulk minerals run to 13%: phosphates 13.0, barytes 12.7,
    feldspar 12.5, borates 12.4, coal 12.0, bauxite 11.6. Against 3.2% for platinum and 3.7% for
    nickel. Our 10% ceiling was below the true margin for a whole class of the materials this
    atlas is about, and we would have gone on quietly clipping them.

    GRAIN: ITIC products are HS2017 HEADINGS. A 6-digit code takes its 4-digit parent's margin -
    HS17_2602 has data, HS17_260200 returns 404. Fallback order is pair-and-product, then product
    median across pairs, then the CEPII route model, then the per-product median from mirror data.

    Writes markup_itic(exporter, importer, hs6, markup_itic, itic_status).
    """
    import os, csv
    import pandas as pd
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'raw', 'oecd_itic', 'itic_margins.csv')
    if not os.path.exists(path):
        con.execute("CREATE OR REPLACE TABLE markup_itic(exporter VARCHAR, importer VARCHAR, "
                    "hs6 VARCHAR, markup_itic DOUBLE, itic_status VARCHAR)")
        return 0
    d = pd.read_csv(path)
    d = d[d.TIME_PERIOD == d.TIME_PERIOD.max()]          # latest year ITIC publishes
    d['hs4'] = d.COMM_HS2017.str.replace('HS17_', '', regex=False)
    # ITIC's REF_AREA is the IMPORTER and COUNTERPART_AREA the EXPORTER: the margin is a share of
    # the importer's CIF value. Getting this backwards would apply Chile's inbound freight to
    # Chile's exports.
    pair = (d.groupby(['COUNTERPART_AREA', 'REF_AREA', 'hs4'])
             .agg(m=('OBS_VALUE', 'median'), st=('OBS_STATUS', 'first')).reset_index()
             .rename(columns={'COUNTERPART_AREA': 'exporter', 'REF_AREA': 'importer'}))
    prod = d.groupby('hs4').OBS_VALUE.median().rename('m_prod').reset_index()

    routes = con.execute("SELECT DISTINCT exporter, importer, hs6 FROM sides").df()
    routes['hs4'] = routes.hs6.astype(str).str[:4]
    r = routes.merge(pair, on=['exporter', 'importer', 'hs4'], how='left') \
               .merge(prod, on='hs4', how='left')
    r['itic_status'] = r.m.notna().map({True: 'itic_pair', False: 'itic_product'})
    r.loc[r.m.isna() & r.m_prod.isna(), 'itic_status'] = None
    r['margin'] = r.m.fillna(r.m_prod)
    r = r.dropna(subset=['margin'])
    r['markup_itic'] = 1.0 + r.margin / 100.0
    out = r[['exporter', 'importer', 'hs6', 'markup_itic', 'itic_status']]
    con.register('_itic', out)
    con.execute("CREATE OR REPLACE TABLE markup_itic AS SELECT * FROM _itic")
    return len(out)


# The freight-adjusted sides, materialized ONCE. It used to be an inline CTE inside the
# flows_reconciled statement; the reliability fit needs exactly the same fob_from_cif that the
# estimator uses, and the way two copies of a COALESCE chain go wrong is that one of them is
# updated. One table, two readers, no drift. (Same columns, same values as the CTE it replaces -
# v1's output is unchanged by this move, and the check pins that.)
SIDES_ADJ_SQL = """
CREATE OR REPLACE TABLE sides_adj AS
SELECT sides.*, mk.markup_raw, mk.level AS markup_level,
       -- PUBLISHED margin first (OECD-ITIC); our own estimates only where
       -- it has no cell. The ceiling applies ONLY to our estimates - a
       -- published margin of 13% for phosphate rock is not ours to clip.
       COALESCE(it.markup_itic,
                least(greatest(COALESCE(rt.markup_cepii, mk.markup), 1.0), {cap})) AS markup,
       COALESCE(it.itic_status,
                CASE WHEN rt.markup_cepii IS NOT NULL THEN 'cepii_route'
                     ELSE 'product_median' END) AS markup_method,
       -- THE FIX. An import the reporter already declared FOB carries no
       -- freight to remove; dividing it by a margin understates it by that
       -- margin. Only deflate when the basis is CIF or unknown.
       CASE WHEN sides.cif_basis = 'fob' THEN cif
            ELSE cif / COALESCE(it.markup_itic,
                       least(greatest(COALESCE(rt.markup_cepii, mk.markup), 1.0), {cap}))
            END AS fob_from_cif
FROM sides LEFT JOIN markup_by_hs6 mk USING (hs6)
LEFT JOIN markup_route rt USING (exporter, importer, hs6)
LEFT JOIN markup_itic it USING (exporter, importer, hs6)
"""


def reconcile(con):
    """Given a DuckDB connection with a `flows` table, build `flows_reconciled`. Returns (markup, stats).

    Robust + HONEST (per an adversarial review): a single global freight markup is a ROUGH PLACEHOLDER
    (real CIF/FOB is route/commodity/mode-specific). It's estimated only from well-behaved pairs (cif/fob
    in 0.7-1.5) so asymmetries don't distort it. Each two-sided flow is CLASSIFIED: if the two FOB-basis
    estimates agree (within 2x) -> reconcile with a SIMPLE geometric mean of the two sides. (Reliability-variance weighting - v2 - was
    tried a first time on ~180 flows, lost to equal weighting, and was left as an exposed diagnostic. It has
    now been rebuilt properly on 712,413 two-sided pairs: variance components decomposed per reporter and
    per reporter x HS2 chapter, fitted OUT OF SAMPLE on five corridor folds, in _reliability_weights. It
    lost again - see RELIABILITY_WEIGHTED for the numbers - so the published estimate is still the
    equal-weight geomean, and the weighted one rides beside it in value_recon_fob_wv2 with the weights and
    variances that produced it. A missing weight means EQUAL weights, never a zero: an unknown reliability
    must not delete a declaration.) If they DISAGREE we DO NOT fabricate a number (no 'keep-larger', which biases up and
    rewards misreporting): value_recon_fob = NULL, and both sides + the [lo,hi] range stay exposed with
    basis='disagreement'. For critical materials these conflicts are mostly HS ambiguity / re-exports /
    confidentiality, not freight — so exposing them (not smoothing them) is the actual value vs TDM (raw)
    and BACI (annual). BACI is kept as an EXTERNAL QA benchmark, never as an input to the estimate."""
    con.execute(SIDES_SQL)
    markup = con.execute("SELECT median(cif/fob) FROM sides WHERE fob>0 AND cif>0 AND cif/fob BETWEEN 0.7 AND 1.5").fetchone()[0] or 1.05
    levels = _markup_table(con, markup)   # per-product fallback
    n_route = _cepii_markup(con)          # per-ROUTE, from CEPII's published coefficients
    n_itic = _itic_markup(con)            # PRIMARY: the published OECD-ITIC margin
    cap = FREIGHT_CEILING
    con.execute(SIDES_ADJ_SQL.format(cap=cap))   # the freight-adjusted sides, once, for both readers
    _reporter_quality(con, markup)   # variance-components: de-bias reporter effects + shrinkage-regularized reliabilities
    n_rel = _reliability_weights(con)  # v2: OUT-OF-SAMPLE inverse-variance weights, per corridor
    # ONE line decides which estimator is PUBLISHED, and it is the same expression the ablation in
    # build.py scores. COALESCE(...,0.5) is the zero rule again in another costume: a corridor with
    # no fitted weight is reconciled 50/50, never by dropping the side we know less about.
    recon_expr = ("exp(COALESCE(rw.w_exp,0.5)*ln(s.fob) + COALESCE(rw.w_imp,0.5)*ln(s.fob_from_cif))"
                  if RELIABILITY_WEIGHTED else "sqrt(s.fob * s.fob_from_cif)")
    con.execute(f"""CREATE OR REPLACE TABLE flows_reconciled AS
      WITH s AS (SELECT * FROM sides_adj)
      SELECT s.period, s.exporter, s.importer, s.hs6, s.material,
        (s.exporter IN {HUBS_SQL} OR s.importer IN {HUBS_SQL}) AS via_entrepot,
        s.fob, s.cif, s.markup AS cif_fob_markup, s.markup_raw AS cif_fob_markup_raw,
        s.markup_level AS cif_fob_markup_level, s.markup_method AS cif_fob_method,
        s.cif_basis AS importer_declared_basis,
        re.reliability AS w_exporter, ri.reliability AS w_importer,
        CASE WHEN s.fob IS NOT NULL AND s.cif IS NOT NULL THEN least(s.fob, s.fob_from_cif) END AS value_lo_fob,
        CASE WHEN s.fob IS NOT NULL AND s.cif IS NOT NULL THEN greatest(s.fob, s.fob_from_cif) END AS value_hi_fob,
        -- how tightly the two customs sides agree (0..1): honest per-flow confidence, exposed not hidden
        CASE WHEN s.fob IS NOT NULL AND s.cif IS NOT NULL
             THEN ROUND(least(s.fob, s.fob_from_cif) / greatest(s.fob, s.fob_from_cif), 3) END AS agreement,
        CASE WHEN s.fob IS NULL THEN s.fob_from_cif
             WHEN s.cif IS NULL THEN s.fob
             WHEN s.fob_from_cif/s.fob BETWEEN 0.5 AND 2                             -- agree -> the PUBLISHED estimator (RELIABILITY_WEIGHTED picks it)
               THEN {recon_expr}                                                     -- ABLATION-DRIVEN: equal-weight geomean, because the
             ELSE NULL END AS value_recon_fob,                                       --   out-of-sample weighted version does not beat it. disagree -> NULL.
        -- v2 BESIDE v1 on every row, whichever is published: this is the reliability-weighted
        -- estimate, exp(w_exp*ln(fob) + w_imp*ln(fob_from_cif)), which is the same geometric mean
        -- with the weights moved off 0.5. Equal when the two variances are equal, so a reader can
        -- see how far the weighting actually moves a number instead of taking a claim about it.
        CASE WHEN s.fob IS NULL THEN s.fob_from_cif
             WHEN s.cif IS NULL THEN s.fob
             WHEN s.fob_from_cif/s.fob BETWEEN 0.5 AND 2
               THEN exp(COALESCE(rw.w_exp,0.5)*ln(s.fob) + COALESCE(rw.w_imp,0.5)*ln(s.fob_from_cif))
             ELSE NULL END AS value_recon_fob_wv2,
        -- ... and the weights themselves, with the variance each came from and which level of cell
        -- supplied it (chapter / reporter / prior), so the estimate above is auditable per flow.
        COALESCE(rw.w_exp, 0.5) AS w_exp_share, COALESCE(rw.w_imp, 0.5) AS w_imp_share,
        rw.var_exp AS rel_var_exporter, rw.var_imp AS rel_var_importer,
        rw.rel_level AS rel_level, rw.fold AS rel_fold,
        -- ── WEIGHT, reconciled the same way and on the same evidence ──────────────────
        s.qty_exp, s.qty_imp,
        CASE WHEN s.qty_exp IS NOT NULL AND s.qty_imp IS NOT NULL
             THEN ROUND(least(s.qty_exp, s.qty_imp) / greatest(s.qty_exp, s.qty_imp), 3)
             END AS qty_agreement,
        CASE WHEN s.qty_exp IS NULL THEN s.qty_imp
             WHEN s.qty_imp IS NULL THEN s.qty_exp
             WHEN s.qty_imp / s.qty_exp BETWEEN 0.5 AND 2 THEN sqrt(s.qty_exp * s.qty_imp)
             ELSE NULL END AS qty_recon_kg,
        CASE WHEN s.qty_exp IS NULL AND s.qty_imp IS NULL THEN 'no_weight_declared'
             WHEN s.qty_exp IS NULL THEN 'importer_only'
             WHEN s.qty_imp IS NULL THEN 'exporter_only'
             WHEN s.qty_imp / s.qty_exp BETWEEN 0.5 AND 2 THEN 'reconciled'
             ELSE 'disagreement' END AS qty_basis,
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
      FROM s LEFT JOIN reporter_quality re ON s.exporter = re.reporter LEFT JOIN reporter_quality ri ON s.importer = ri.reporter
      -- reliability_weights holds exactly ONE row per (exporter, importer, hs6), so this LEFT JOIN
      -- can only annotate rows, never multiply them. Never a sum across sources, never a fan-out:
      -- the row count of flows_reconciled must equal the row count of sides, and check.py asserts it.
      LEFT JOIN reliability_weights rw ON s.exporter = rw.exporter AND s.importer = rw.importer
                                      AND s.hs6 = rw.hs6""")
    # UNIT-VALUE SANITY, flagged not dropped. A reader found Belgium importing unwrought tungsten
    # at $1,123/t in Q1-2025 against ~$50,000/t everywhere else. Traced: GBR->BEL, Feb 2025,
    # $1,694 for 4,000 kg, identical in HMRC and in Comtrade (which is HMRC's data) - a filer
    # weight-unit error, faithfully ingested. It is real in the source and wrong in the world, and
    # it drags a value-weighted aggregate 3x. So every two-sided flow carries its USD/t and a
    # flag when it sits outside [median/20, median*20] of its own HS6 that period-year. The row
    # stays; the flag lets a page exclude it and say so. 20 of 485 tungsten rows in that quarter
    # fell below $5,000/t.
    con.execute("""CREATE OR REPLACE TABLE _uv_med AS
      SELECT hs6, CAST(period AS INTEGER) // 100 AS yr,
             median(value_recon_fob / (qty_recon_kg / 1000.0)) AS med_usd_t, count(*) AS n
      FROM flows_reconciled
      WHERE basis = 'reconciled' AND qty_basis = 'reconciled' AND qty_recon_kg > 0 AND value_recon_fob > 0
      GROUP BY 1, 2""")
    con.execute("""CREATE OR REPLACE TABLE _fr AS
      SELECT r.*,
             CASE WHEN r.qty_recon_kg > 0 AND r.value_recon_fob > 0
                  THEN r.value_recon_fob / (r.qty_recon_kg / 1000.0) END AS usd_per_t,
             CASE WHEN m.n >= 10 AND r.qty_recon_kg > 0 AND r.value_recon_fob > 0
                       AND (r.value_recon_fob / (r.qty_recon_kg / 1000.0) < m.med_usd_t / 20
                            OR r.value_recon_fob / (r.qty_recon_kg / 1000.0) > m.med_usd_t * 20)
                  THEN 'implausible' END AS uv_flag
      FROM flows_reconciled r
      LEFT JOIN _uv_med m ON m.hs6 = r.hs6 AND m.yr = CAST(r.period AS INTEGER) // 100""")
    con.execute("DROP TABLE flows_reconciled")
    con.execute("ALTER TABLE _fr RENAME TO flows_reconciled")
    con.execute("DROP TABLE _uv_med")
    n_uv = con.execute("SELECT count(*) FROM flows_reconciled WHERE uv_flag IS NOT NULL").fetchone()[0]
    print("  unit-value flags: %d two-sided flows outside [median/20, median*20] of their HS6-year" % n_uv)
    stats = {r[0]: (r[1], r[2]) for r in con.execute(
        "SELECT basis, COUNT(*), ROUND(SUM(value_recon_fob)/1e9,2) FROM flows_reconciled GROUP BY 1").fetchall()}
    stats["_markup_levels"] = levels
    stats["_n_route"] = n_route
    stats["_n_itic"] = n_itic
    stats["_n_rel"] = n_rel
    return markup, stats
