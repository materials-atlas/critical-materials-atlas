# -*- coding: utf-8 -*-
"""THE EVALUATION BEHIND `RELIABILITY_WEIGHTED = False`: v1 (equal-weight geomean) against v2
(out-of-sample reliability-variance weighting), on the benchmark build.py already ran, plus the
tests build.py has no business carrying - a sign test, a Wilcoxon, a seeded bootstrap, and three
post-hoc probes of WHY v2 fails.

Run it after pipeline/build.py has written pipeline/data/:
    python pipeline/eval_reliability.py            # the benchmark + the paired tests
    python pipeline/eval_reliability.py --probes    # ... and re-fit the weights three other ways

THE PROTOCOL IS NOT MINE TO CHOOSE. It is the one build.py has printed since before this weighting
existed: median |ln(estimate / BACI monthly average)| over the matched 2024 flows whose basis is
'reconciled', comparing exporter-only, importer-only, and the two-sided estimators on the SAME
flows with the SAME importer-side construction (cif / cif_fob_markup). Everything here is the
VALUE basis, in USD. The tonnage reconciliation is a separate measure, is NOT weighted, and no
number in this file says anything about it.

WHAT THE BENCHMARK CANNOT DO, said first: BACI is annual, divided by twelve to meet a monthly
estimate, so its own error against any of these estimators is ~1.166 log points - a factor of 3.2.
The gap between v1 and v2 is ~0.0004. A benchmark whose noise is three orders of magnitude above
the effect can refuse a refinement; it cannot certify one. It is also CEPII's own reconciliation of
the same mirror reports, with a CIF/FOB model of its own, so it is not ground truth either.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duckdb
import numpy as np

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pipeline', 'data')
# the ablation, with the two weight expressions left as placeholders so a probe can substitute its
# own without the rest of the query drifting from build.py's version
ABL = """WITH b AS (SELECT reporter AS exporter, partner AS importer, hs6, SUM(value_usd)/12 AS bmo
      FROM flows WHERE source='baci' GROUP BY 1,2,3)
      SELECT abs(ln(r.fob/b.bmo)) AS e_exp,
             abs(ln((r.cif/r.cif_fob_markup)/b.bmo)) AS e_imp,
             abs(ln(sqrt(r.fob*r.cif/r.cif_fob_markup)/b.bmo)) AS e_v1,
             abs(ln(exp(W_E*ln(r.fob) + W_I*ln(r.cif/r.cif_fob_markup))/b.bmo)) AS e_v2,
             r.w_exp_share AS w
      FROM flows_reconciled r JOIN b USING(exporter,importer,hs6)
      WHERE r.basis='reconciled' AND r.period BETWEEN 202401 AND 202412 AND b.bmo>0
        AND r.fob>0 AND r.cif>0
      ORDER BY r.period, r.exporter, r.importer, r.hs6"""


def _paired(d):
    """The comparison that holds the flow fixed. Two medians a thousandth apart are not evidence;
    which estimator is closer ON THE SAME FLOW, counted, is."""
    diff = d.e_v2.to_numpy() - d.e_v1.to_numpy()
    w = int((diff < 0).sum()); l = int((diff > 0).sum()); t = int((diff == 0).sum())
    return diff, w, l, t


def _score(con, w_exp='r.w_exp_share', w_imp='r.w_imp_share'):
    return con.execute(ABL.replace('W_E', w_exp).replace('W_I', w_imp)).df()


def main(probes=False):
    con = duckdb.connect()
    for t in ('flows', 'flows_reconciled'):
        p = os.path.join(DATA, t + '.parquet').replace('\\', '/')
        if not os.path.exists(p):
            raise SystemExit('%s is missing - run python pipeline/build.py first' % p)
        con.execute("CREATE VIEW %s AS SELECT * FROM '%s'" % (t, p))

    d = _score(con)
    n = len(d)
    print('BENCHMARK (build.py protocol, VALUE basis USD, %d matched 2024 reconciled flows)' % n)
    for col, label in (('e_exp', 'exporter-only (FOB)'), ('e_imp', 'importer-only (CIF adj)'),
                       ('e_v1', 'v1 equal-weight geomean'), ('e_v2', 'v2 reliability-weighted')):
        print('  median |ln(est/BACI)| %-26s %.6f   (mean %.6f)'
              % (label, np.median(d[col]), d[col].mean()))
    diff, w, l, t = _paired(d)
    print('PAIRED, same flows: v2 closer on %d, v1 closer on %d, %d exact ties -> v2 wins %.2f%%'
          % (w, l, t, 100.0 * w / (w + l)))
    print('  median per-flow difference |err v2| - |err v1| = %+.6f (positive = v1 closer)'
          % np.median(diff))
    z = (w - (w + l) / 2.0) / np.sqrt((w + l) / 4.0)
    print('  sign test z = %+.2f' % z)
    try:
        from scipy import stats
        print('  binomial p = %.3g   Wilcoxon signed-rank p = %.3g'
              % (stats.binomtest(w, w + l, 0.5).pvalue,
                 stats.wilcoxon(d.e_v2.to_numpy(), d.e_v1.to_numpy(), zero_method='zsplit').pvalue))
    except Exception as ex:
        print('  (scipy absent, so no exact p-values: %s)' % ex)
    # SEEDED, because a bootstrap with an unseeded generator is a number nobody else can reproduce.
    rng = np.random.default_rng(20260924)
    idx = rng.integers(0, n, size=(1000, n))
    bm = (np.median(d.e_v2.to_numpy()[idx], axis=1) - np.median(d.e_v1.to_numpy()[idx], axis=1))
    print('  bootstrap 1000x (seed 20260924): median(v2) - median(v1) = %+.6f, 95%% CI [%+.6f, %+.6f]'
          % (np.median(d.e_v2) - np.median(d.e_v1), np.quantile(bm, 0.025), np.quantile(bm, 0.975)))
    print('  benchmark scale for comparison: median |ln| %.3f = a factor of %.2f'
          % (np.median(d.e_v1), np.exp(np.median(d.e_v1))))

    mv = con.execute("""SELECT COUNT(*), median(abs(ln(value_recon_fob_wv2/value_recon_fob))),
            quantile_cont(abs(ln(value_recon_fob_wv2/value_recon_fob)), 0.95),
            min(w_exp_share), median(w_exp_share), max(w_exp_share),
            100.0*AVG(CASE WHEN abs(w_exp_share-0.5)<0.01 THEN 1.0 ELSE 0.0 END)
          FROM flows_reconciled WHERE basis='reconciled' AND value_recon_fob>0
            AND value_recon_fob_wv2>0""").fetchone()
    print('DO THE WEIGHTS BITE? %d reconciled flows: median |ln(v2/v1)| %.5f (p95 %.4f); exporter '
          'share min/median/max %.3f/%.3f/%.3f; %.1f%% within 0.01 of equal weighting'
          % (mv[0], mv[1], mv[2], mv[3], mv[4], mv[5], mv[6]))
    print('  weight source (exporter/importer cell level): ' + str(con.execute(
        "SELECT rel_level, COUNT(*) FROM flows_reconciled WHERE basis='reconciled' "
        "GROUP BY 1 ORDER BY 2 DESC").fetchall()))

    rel = os.path.join(DATA, 'reporter_reliability.parquet').replace('\\', '/')
    if os.path.exists(rel):
        print('WHAT THE VARIANCES SAY ANYWAY (fold 0, reporter-level, >=500 pairs, lower = tighter):')
        for order, label in (('', 'tightest'), (' DESC', 'loosest ')):
            rows = con.execute("SELECT reporter, ROUND(var_resid,3) FROM '%s' WHERE fold=0 AND "
                               "role='exp' AND hs2='' AND reporter<>'' AND n_pairs>=500 "
                               "ORDER BY var_resid%s LIMIT 5" % (rel, order)).fetchall()
            print('  %s exporters: %s' % (label, ', '.join('%s %.2f' % r for r in rows)))

    print('THE RULES, asserted on the built table (all four must read 0):')
    for label, sql in (
            ('a 0 kg declaration treated as a declaration',
             "SELECT COUNT(*) FROM flows_reconciled WHERE qty_exp = 0 OR qty_imp = 0"),
            ('weights outside (0,1) or not summing to 1',
             "SELECT COUNT(*) FROM flows_reconciled WHERE w_exp_share IS NULL OR w_imp_share IS NULL"
             " OR w_exp_share <= 0 OR w_exp_share >= 1 OR abs(w_exp_share+w_imp_share-1) > 1e-9"),
            ('flows multiplied by the weight join',
             "SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT period, exporter, importer,"
             " hs6 FROM flows_reconciled)) FROM flows_reconciled"),
            ('reconciled rows with no estimate but two declarations',
             "SELECT COUNT(*) FROM flows_reconciled WHERE basis='reconciled' AND "
             "(value_recon_fob IS NULL OR value_recon_fob_wv2 IS NULL)")):
        print('  %-48s %d' % (label, con.execute(sql).fetchone()[0]))

    if not probes:
        return
    # POST-HOC, and labelled post-hoc: these ran AFTER the verdict, to diagnose the failure rather
    # than to shop for a variant that wins. None of them is a candidate default.
    print('POST-HOC PROBES (run after the verdict; diagnosis, not selection)')
    import reconcile
    clamp = ('least(greatest(r.w_exp_share,0.25),0.75)', '(1.0-least(greatest(r.w_exp_share,0.25),0.75))')
    for label, over in (('as shipped', {}), ('reporter-level cells only', {'MIN_REL_PAIRS_HS2': 10 ** 9}),
                        ('heavier shrinkage K=50', {'REL_K': 50.0})):
        keep = {k: getattr(reconcile, k) for k in over}
        for k, v in over.items():
            setattr(reconcile, k, v)
        c2 = duckdb.connect()
        c2.execute("CREATE TABLE flows AS SELECT * FROM '%s'"
                   % os.path.join(DATA, 'flows.parquet').replace('\\', '/'))
        reconcile.reconcile(c2)
        for tag, (we, wi) in (('', ('r.w_exp_share', 'r.w_imp_share')), (' + clamped [0.25,0.75]', clamp)):
            dd = _score(c2, we, wi)
            _, w2, l2, _ = _paired(dd)
            print('  %-28s%-24s v1 %.6f  v2 %.6f  (v2-v1 %+.6f)  v2 closer on %.2f%%'
                  % (label, tag, np.median(dd.e_v1), np.median(dd.e_v2),
                     np.median(dd.e_v2) - np.median(dd.e_v1), 100.0 * w2 / (w2 + l2)))
        c2.close()
        for k, v in keep.items():
            setattr(reconcile, k, v)


if __name__ == '__main__':
    main(probes='--probes' in sys.argv)
