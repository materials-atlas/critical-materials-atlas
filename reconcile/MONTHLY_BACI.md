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

## Why we did not match BACI, and what BACI actually does (10 Nov 2026, night)

The owner asked for the explanation, not another tuning round. It came from two places: CEPII's
own site, and BACI's own numbers set against the raw declarations they were built from.

**What CEPII publishes beyond the 2010 paper** (cepii.fr/DATA_DOWNLOAD/baci/doc/): the release
notes say "we regularly introduce minor methodological improvements"; January 2024, "we switched
to the CEPII Gravity dataset to obtain distances in the fobization step. This implied giving up
on the dummy variable for landlocked countries"; January 2026, "Fobization process was
simplified, with little effects on final outcome". The paper is still the only reference cited.
With the 2019 and 2020 releases CEPII also published its **reporter reliabilities** per country
(`reporter_reliability_*.csv`, kept in `raw/baci/`): medians of 0.34 as exporter and 0.29 as
importer. Ours at the time had medians of 1.4 and 2.1.

**What BACI's output shows** (`diagnose_vs_baci.py`, `recover_baci_weights.py`; BACI V202601
against the atlas's annual Comtrade pulls for 2022 and 2024, 31 codes, 16,241 two-sided flows):

1. *Nothing is removed from import values.* A flow only the importer declared is in BACI at its
   declared value: China's imports from the DRC, 13.7 bn USD, to the dollar; 75-82% of all such
   flows exactly, the rest moved by the data vintage (EU reporters' values differ by about 3%
   between our pull and CEPII's). On two-sided flows, BACI = a x export + b x import fits 235
   country pairs to within 1%, and there a + b = 1.0000 (p10 0.9945, p90 1.0027): the weights
   sum to one on the RAW import value. Flow by flow the implied freight factor is centred on
   1.0006. The paper strips 3.3% on average; our estimate of its equation stripped 5-6%.
2. *The weight is a ratio of two country constants.* Within a pair the weight does not move
   (France to Germany 0.60, China to the Netherlands 0.22: interquartile range 0.00-0.01), and
   logit(a_ij) = ln V_j - ln V_i fits with R2 0.998. That is the paper's equation (3),
   a = V_j / (V_i + V_j), confirmed on the output. The exporter's weight has a median of 0.39.
3. *Monthly declarations are the same data.* For the 95 reporters with twelve months of 2024,
   the months summed equal the annual declaration within 5% on 95% of lines (490.0 against
   488.8 bn USD). 34 countries report yearly only; they hold 4% of declared value.

**So the distance had three causes, in this order:**

| cause | what we did | what BACI does | effect on flows within 10% of BACI |
|---|---|---|---|
| freight | removed 5-6% from every import (the paper's step) | removes nothing detectable | about -10 points, and a median 3% low |
| weights | sigmas inflated by micro-reporters setting the baseline of footnote 22 (a country with 18 pairs), so every weight was 0 or 1; then our own estimates from 54 products | interior weights from country constants estimated on all products | about -10 points |
| timing | reconciled each month alone, so a shipment booked in two different months counted twice (+17% on such flows) | weights the two sides' year totals | totals 5-8% high |

**What the engine does now (v2.4).** `--fob-rule none`; `--timing window`: v_t = w x_t +
(1-w) m_t over every month, a month one side left empty counting as its zero when it filed the
month and declares the corridor that year, which adds up to BACI's annual arithmetic exactly;
reliabilities with the baseline taken among well-estimated reporters; and `--baci-weights`, the
country constants recovered from BACI itself, for the pairs they cover (47 exporters and 87
importers so far).

| slice, 2020-2024, against BACI | within 10% | within 25% | yearly total / BACI | median |
|---|---|---|---|---|
| the paper to the letter (v2.1, this evening) | 57-61% | 76-77% | 1.00-1.06 | 0.99 |
| v2.4, paper's freight rule, own weights | 62-66% | 82-83% | 0.96-1.00 | 0.97 |
| v2.4, no freight, own weights | 72-74% | 82-83% | 1.02-1.06 | 1.000 |
| **v2.4, no freight, BACI's recovered weights** | **82-84%** | **88-89%** | **1.01-1.05** | **1.000** |

**What is left, and is not method:** flows we hold from one side where BACI has both (the
yearly-only reporters, and declarations that arrived after our pull): 9% of one-sided flows are
more than 25% off; weights not yet recovered for a fifth of two-sided flows, because the annual
raw data in hand covers 31 codes; the 3% vintage gap on EU reporters. All three shrink with the
annual bulk series (queued behind the monthly pull): same vintage, every product, every
reporter, which will also say whether "nothing removed" holds beyond these 31 codes.

Two cautions. The recovered constants are CEPII's, read off their release; using them is the
way to splice a monthly series onto BACI, not an independent estimate, and both runs are kept.
And equation (3) with the 2020 published sigmas does not reproduce the 2026 weights well
(correlation 0.6): the reliabilities are re-estimated at each release.

## First run on ALL products: the twelve months of 2023 (10 Nov 2026, 21:22-21:51)

The 54 codes were a test bench, never the scope. The corpus already held 2019-2026 complete,
so the engine ran on every six-digit product for 2023 on the server (21 minutes for the year;
8 GB of memory, after three fixes: an on-disk work database, the reliability regression fed
integer codes instead of text, and no per-group distinct sets in an 85-million-group
aggregation).

| | |
|---|---|
| declarations (total lines, six-digit, M and X) | 85.6 million, 99% of value in HS 2022 |
| flows after pairing | 61.9 million; 23.2 million declared by both sides in the same month, 37.7 million within the year window |
| freight, CEPII's equation on 17.3 million pairs | mean CIF rate **0.9%** (5-6% on the 54 ore codes): small across all products, in line with BACI removing none |
| reconciled world trade, 2023 | 23.3-23.6 trillion USD |

Against BACI 2023, all 5,204 products, 10.6 million flows in both:

| weights | within 10% | within 25% | median | total / BACI | corr of logs |
|---|---|---|---|---|---|
| our own estimates | 70.2% | 80.1% | 1.000 | 1.017 | 0.980 |
| **BACI's recovered constants** (72% of two-sided flows covered) | **80.5%** | **86.6%** | 1.000 | **1.010** | 0.985 |

The test bench had said 82-84% and 88-89%; the universe says 80.5% and 86.6%, with the weights
of only 47 exporters and 87 importers recovered so far. One-sided flows: 89.5% within 25%.
Two-sided flows: 82.3% with BACI's constants, 66.0% with ours. 1.07 million BACI flows have no
counterpart in the monthly data (1.6% of BACI's value): the yearly-only reporters.

**What this run says is still wrong with our own weights:** on the universe their sigmas came
out large again (medians 1.6 and 1.5 against CEPII's 0.3): a threshold of 1,000 pairs for the
baseline, right for the test bench, lets micro-reporters set it when the sample is 21.7 million
pairs. The threshold has to scale with the sample. Until then the reference run uses BACI's
recovered constants, and the own-estimate run is the one to repair.

## The same run with BACI's product list, and the order of work from here (10 Nov 2026, 22:34)

Listing the flows present on one side of the comparison only showed two faults of ours, not of
the method: BACI carries refined petroleum as ONE product (271000; the UN's five 2710
subheadings merged), and has no chapter 99 ("commodities not specified"). We had 736 bn USD of
petroleum under other codes and 571 bn of code 999999. The engine now targets BACI's own
edition (HS 2017) and product list (v2.5). The rest of what BACI has and we lack, 1.07 million
flows, is small (median 1,900 USD) and involves a country that does not report monthly in 2023
(UAE, Russia, Taiwan, Iraq, Austria, Peru...).

All products, 2023, v2.5, BACI's recovered weights: 86.1 million declarations, 62.3 million
flows, **22.76 trillion USD** (BACI: 22.94); 10.71 million flows in both; **80.6% within 10%,
86.7% within 25%**, median 1.000, total on matched flows 1.007, correlation of logs 0.985.

**The owner's decision on what comes next.** The weights are to be calculated by us, with
CEPII's method; the constants recovered from BACI are a check on that calculation, not its
replacement. And the test is made in the right order, once the whole corpus is down, the yearly
series included: first CEPII's own exercise - yearly declarations, all products, our weights -
against BACI, which must land almost flow for flow if the ingredients and the method are the
same; then, and only if that holds, the monthly series with the same recipe. No further
partial experiments before the data is complete. One repair is owed before that test: the
baseline of the reliability calculation must scale with the sample.


## Step 1: CEPII's yearly exercise on the UN's yearly declarations, all products (12 Nov 2026)

The order of work decided on 10 Nov: before any monthly series, redo BACI's own yearly
calculation on the UN's **yearly** declarations (bulk pull `comtrade_bulk_A_HS`, complete for
1997-2025 on 12 Nov), all products, BACI's HS 2017 product list, our own weights, and compare
with BACI V202601 flow by flow. Runner `~/comtrade/run_annual.sh` on the Lenovo, outputs
`~/comtrade/ya_all_YYYY`, log `~/comtrade/run_annual.log`; about 5 minutes a year. The engine
needed one change: it now reads the yearly file names (`YYYY_rep.parquet`).

| year | flows in both | ours only | BACI only | own weights: within 10% / 25% / total | BACI's recovered constants: within 10% / 25% / total |
|---|---|---|---|---|---|
| 2017 | 9,944,498 | 1,713,818 | 4,347 | 73.9% / 83.2% / 0.985 | 82.2% / 87.5% / 0.989 |
| 2018 | 10,797,683 | 895,758 | 4,817 | 71.3% / 79.5% / 1.009 | 83.3% / 88.0% / 0.993 |
| 2019 | 11,205,528 | 552,518 | 4,603 | 71.8% / 80.6% / 0.969 | 85.1% / 89.8% / 0.988 |
| 2020 | 10,974,400 | 370,996 | 10,758 | 75.6% / 84.4% / 1.006 | 86.3% / 91.0% / 0.996 |
| 2021 | 11,576,480 | 320,684 | 22,205 | 75.1% / 83.8% / 1.016 | 86.1% / 90.7% / 1.003 |
| 2022 | 11,691,916 | 236,594 | 11,201 | 74.9% / 83.5% / 1.029 | 86.8% / 91.3% / 1.010 |
| 2023 | 11,741,627 | 225,748 | 39,588 | 73.6% / 82.4% / 1.024 | 85.6% / 90.3% / 1.007 |
| 2024 | 11,161,576 | 417,289 | 15,994 | 73.0% / 80.9% / 1.030 | 86.3% / 90.3% / 1.013 |

Median ratio 1.000 every year. The value of BACI's flows found on our side is 100.0% every year.

**What it says.** (1) The ingredients match: BACI's flows are on our side almost all of them
(BACI-only 4,000-40,000 of 10-12 million). (2) The step-1 test ("almost flow for flow") is NOT
passed: with our own weights 71-76% of flows are within 10%. (3) The weights cost 11-14 points
every year: BACI's recovered constants (47 exporters, 86 importers; the rest still ours) give
82-87%. (4) Even with those constants 13-18% of flows stay more than 10% off - partly the
countries whose constant is not recovered, the rest not yet explained. (5) "Ours only" is large
in 2017-2019 (1.7 million in 2017): likely the equal split of HS 2012 declarations over several
HS 2017 candidates; to check.

**Why our weights are off: the letter of footnote 22.** The transcription is exact (checked
against the paper, WP 2010-23 p. 18: sigma_i = pi/2 (LS_RD_i - min LS_RD_i - 2 stderr_i)).
On these data it gives sigma medians 1.5-3.0; CEPII's published unreliabilities (HS17 V202001)
have medians 0.34 (exporters) and 0.29 (importers). On the 97 countries in both (our 2023 run):
rank correlation 0.73 / 0.64, but CEPII's value is about 0.26 (exporters) and 0.48 (importers)
of our LS_RD - min, against the letter's 1.57. The exporter baseline (the min) is set by the
Cayman Islands (221 pairs). The paper itself says the transformation "can be ignored", and its
equation (5) pools all years (a year effect), while we estimate year by year. Under the
"a la lettre" rule no repair is made: the two readings the paper allows - pool the years;
skip footnote 22 and use the least-square means directly - are for the owner to choose.
