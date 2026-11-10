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

## Version 2.1 (10 Nov 2026, evening): the council's corrections

Two engines reviewed the code against the paper's text; they agreed with each other on every point below.
Its findings, and what was done with each:

| finding | verdict | done |
|---|---|---|
| the reliability step read each country's RAW mean reporting distance as its effect, not the effect adjusted for its partners, products and months | right, and the most serious | the fixed effects are now kept during the backfit and the least-square means are the effect at a common reference |
| the sigma baseline was min(LS - 2 se) instead of footnote 22's min(LS) then - 2 se_i | right | footnote 22 exactly |
| quantities were reconciled with the value weights; the paper assesses values and quantities separately | right | a second reporting-distance regression on the quantities, own weights |
| the freight step sampled 4 million pairs and trimmed by residual; the paper uses every pair and Cook's distance | right | normal equations accumulated in the database over every pair; Cook's distance with D > 4/n, one refit |
| the unit-value covariate was per product-month; the paper's UV_k is per product | right | per product over the window |
| the orphan matching paired on presence only, and the end of the window is censored | right | a match now needs the two values within the plausibility band; the last months stay provisional by construction |
| the paper does not trim before the reliability regression; the ratio band removed the most informative observations | right in principle | the band is off by default (`--rd-trim` keeps it as a declared adaptation) |
| equation (3) and the squared-distance term are implemented correctly | - | kept; the weights are computed in log space so large sigmas cannot overflow |
| not done, and named: HS-revision harmonisation, historical geography (BACI's consistent country set), quantity-unit conversion to tons, the NES residual stage, the Hong Kong / US re-export rule, a revision policy for recent months | right | listed below as the next items, in that order of weight |

The engine also proposed an **annual control**: the same code on the months summed to calendar
years, which is the paper's own frequency on our own raw data. `--annual` does that.

### Slice, 2020-2024, against BACI, after the corrections

| run | yearly total, ours / BACI | median flow ratio | within 10% | within 25% |
|---|---|---|---|---|
| v2.1 to the letter (no trim), matching 2 months | 1.00-1.06 | 0.994-1.000 | 57-61% | 76-77% |
| v2.1 with the ratio band in the reliability step | 1.00-1.05 | 0.993-1.000 | 57-61% | 77-78% |
| **v2.1 annual control** (months summed to years first) | 0.96-1.01 | 0.97-0.99 | 54-59% | 75% |
| v2 of the afternoon (biased reliabilities, band, matching) | 0.97-1.03 | 0.986-0.997 | 59-62% | 79-80% |

Two things the table says. First, **the annual control agrees with BACI no better than the
monthly runs**: the distance that remains to CEPII is not caused by working monthly, it comes
from what is still missing on the data side (classification harmonisation, the historical
country set, quantity conversion, the NES residual stage) and from choices the paper leaves
open. Second, the corrected reliabilities moved the weights from the importers (0.14 of the
weight to exporters before) to the exporters (0.64-0.82 now): the raw means had been charging
exporters with the quality of their partners. On bulk ores and concentrates the exporting
customs (Chile, Australia, Peru...) being the better reporter is plausible; the universe will say.

The afternoon's v2 agreed with BACI slightly better than the corrected v2.1. Agreement with
BACI is not the criterion when the better-agreeing version was wrong about the paper; the
reference is v2.1 to the letter, the band a reported sensitivity.

## The data-side items (10 Nov 2026, night)

Done, in the order the annual control pointed to:

- **One HS edition** (`hs_concordance.py`). The corpus mixes editions: in the 54-code slice 68%
  of value is declared in HS 2022, 31% in HS 2017, 1% in HS 2012, a trace in HS 2007 and 2002.
  The UN Statistics Division's conversion tables bring every declaration to **HS 2012**, the
  edition both HS 2017 (263 codes change number) and HS 2022 (621) convert to uniquely; the few
  older-edition reporters go up through the correlation tables, split equally where the UN lists
  several candidates (and counted). BACI's HS 2017 is converted the same way for the validation.
  The long history will take HS 1992. Tables in `raw/concordance/`, fetched from
  unstats.un.org/unsd/classifications/Econ.
- **Areas nes as the appendix writes it**: exporter side, named partners first in proportion to
  their shortfalls, then the residual set against the partners the exporter never named and
  reported. On the slice: 1.4 bn USD reallocated, 18 bn of residual, 6.8 bn taken as included
  in partners' declarations, 3.7 bn unexplained. The earlier version also did the importer side
  and used the whole mirror gap as the pot; both engines objected, and it was right to: 14 bn
  had been moved.
- **Hong Kong and US re-exports** taken out of their exports (BACI drops them: destination
  unknown).
- **Quantities in other units** converted to weight with mirror-implied rates (section 2.2:
  at least ten mirrors, dispersion of the log rates below 2.5). Nothing to convert on the ores
  slice (99.6% of value carries a weight); the universe has 12% of value without one.
- **The country set** is BACI's own table for the modern window; the historical geography
  (merged and split entities) is a long-history item, with HS 1992.

Slice after all of it, 2020-2024 against BACI in HS 2012: yearly totals 1.00-1.05, median flow
ratio 0.993-1.000, 57-61% of flows within 10%, **77%** within 25%, correlation of logs 0.98.

Still open: a revision policy for the last months (recompute the trailing three months on every
run; the matched orphans at the window's end are provisional by construction) - it belongs to
the runner that will drive the full-corpus job; the full-corpus run itself, after the download;
and the memory the reliability regression needs on the universe (the two-sided pairs are loaded
whole), which waits for the RAM or a sampling rule.

