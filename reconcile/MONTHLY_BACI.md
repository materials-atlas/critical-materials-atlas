# A monthly BACI

Started 10 Nov 2026. CEPII's BACI (Gaulier & Zignago, WP 2010-23) reconciles the exporter's and
the importer's declaration of every bilateral flow once a year, with a lag: V202601 stops at
2024. The UN bulk corpus holds the same raw declarations by month up to the last published
period, so the same three steps can run per month and reach two years further. The engine is
`monthly_baci.py`; `validate_monthly_baci.py` sums its months to years and compares them with
BACI's own numbers where the two overlap, which is the test of the whole thing.

## Version 2 (10 Nov 2026): CEPII's steps as written, plus the month-end problem

Version 1 (same day, in the git history) used CEPII's published 2008 gravity coefficients with
an anchor set on 54 products, and a reliability model of our own. The owner asked for the
method to the letter; version 2 follows the paper (sections 2.3-2.4 and the appendix):

0. **Data.** Total lines only (customs `C00`, transport `0`, second partner `0`), flows `M`
   and `X`, partner "World" dropped, codes mapped to ISO3 with BACI's own country table.
   "Areas not elsewhere specified" are reallocated to identified partners by the appendix rule
   (the exporter's NES value fills the shortfall between what it declared to named partners and
   what those partners declared from it, in proportion to the shortfalls; the same mirrored for
   importers). On the slice: 14.4 bn USD moved on the export side, 3.0 bn on the import side.
1. **Freight.** The gravity equation is estimated on the data, model II of the paper:
   ln(UVm/UVx) on ln distance, ln distance squared, contiguity, exporter and importer landlocked,
   ln world median unit value of the product in the month, and month dummies; each observation
   weighted by min(Qx,Qm)/max(Qx,Qm); population-weighted distances where CEPII has them. The
   paper's Cook's-distance filter is approximated by a two-pass trim (ratio outside [0.2, 5],
   then residuals beyond 3 sigma). Not applied to importers that declare FOB (Algeria, Georgia,
   South Africa and the SACU, the paper's footnote 17); to Canada only where it narrows the gap.
   On the 54 codes: mean CIF rate **5.8%** (the paper found 3.3% over all products; ores and
   concentrates travel dearer), coefficients of the same sign and size as theirs (ln distance
   -0.020, squared +0.0034, contiguity -0.010, unit value -0.016).
2. **Timing** (ours; the owner chose the faithful treatment). A month declared by both sides is
   left alone. An exporter's declaration with no counterpart that month is matched with an
   unmatched importer's declaration on the same corridor one or two months later, nearest first,
   each used once, and the importer's value moves to the exporter's month. On the slice 35,440
   declarations (2.7%) were matched this way. A first attempt that smoothed the importer's
   series with a per-route lag profile made every other category worse and was dropped.
3. **Reliability.** Reporting distance RD = |ln(Vx / Vm_fob)|, regressed on exporter, importer,
   month and product fixed effects by weighted alternating projections (the within estimator),
   weights ln of the sum of the two reports; sigma_i = (pi/2)(LS_RD_i - min LS_RD - 2 stderr_i),
   floored at 0.01; the exporter's weight from equation (3), w = Vj / (Vi + Vj) with
   V = e^(s^2)(e^(s^2) - 1). Monthly reporting distances are larger than yearly ones (mean 0.47),
   so the sigmas are large and the weights near 0 or 1: the better reporter is taken almost
   whole. Mean exporter weight 0.14; importers are the more reliable side on these products.
4. **Reconciliation.** Weighted arithmetic mean; one side alone as declared (FOB); quantities
   (net weight) with the same weights.

## Validation: the 54-code slice against BACI, 2020-2024

Yearly sums of our months against BACI's yearly flows, same codes, same country list.

| version | yearly total, ours / BACI | median flow ratio | flows within 10% | within 25% | corr of logs |
|---|---|---|---|---|---|
| v1 (published coefficients, own reliability) | 1.02-1.07 | 1.000 | 63-66% | 75% | 0.98-0.99 |
| v2, no timing step | 0.99-1.04 | 0.995-1.000 | 57-60% | 75-76% | 0.98-0.99 |
| **v2 + orphan matching, 2 months** | **0.97-1.03** | **0.986-0.997** | **59-62%** | **79-80%** | 0.98-0.99 |

By how the flow was built (v2 + matching, flows in both, 2020-2024): declared by one side only,
median ratio 0.976 and 88% within 25%; both sides every month, 0.964 and 83%; a mix of months,
1.106 and 56%. The mixed category is where the month-end problem lives; matching halved its
excess (1.18 -> 1.11) without touching the rest. BACI's value is covered at 98-99%; the 1-2%
we lack are reporters absent from the monthly series (Congo, Russia, Australia, Zambia,
Guinea...), for which BACI works from partners alone and the yearly series will add.

Still ahead: the full universe (after the download), which is what the method is for and where
the freight equation and the reliabilities get their proper sample; HS-revision harmonisation
(needed for product comparisons across 2022); quantity-unit conversion to tons.
