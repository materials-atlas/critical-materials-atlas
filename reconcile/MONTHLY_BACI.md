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

### The two readings the paper allows, and the council (12 Nov 2026, evening)

Own weights, within 10% of BACI, 2017-2024 (all products, yearly declarations):

| reading | within 10% | within 25% |
|---|---|---|
| footnote 22 as written, year by year | 71-76% | 80-84% |
| footnote 22 skipped (`--sigma-rule ls`: sigma = LS_RD) | 72-74% | 81-84% |
| eight years pooled in one regression (eq. 5), footnote 22 | 71.5-73.1% | 80.5-81.8% |

None closes the gap; BACI's recovered constants give 82-87%. The pooled run (`~/comtrade/ya_pool`,
94 M flows, 40 M two-sided pairs, sigma medians 1.9/2.0) needs `CMA_DUCK_MEM=5500MB
CMA_DUCK_THREADS=2` (4 GB ran out in the unit conversion) and its validation must be run one
year at a time (all eight at once was killed).

Two independent reviews of the whole story: (1) "to the letter" is overstated - the paper's RD is on
FOB-adjusted imports (2.4: "mirror flows, now cleaned from CIF rates"), ours on raw ones; small
here (CIF rate ~1%) but a departure; (2) BACI's country-constant weights are what the paper
PREDICTS, so they do not show CEPII changed method - France->Germany (BACI 0.60, ours 0.01) shows
OUR weights are degenerate, not why; (3) "nothing removed from imports" was measured on pairs
pre-selected as fitting within 1% (`recover_baci_weights.py`): true for those, not proven in
general; (4) leads for sigmas 3-6x CEPII's: RD level inflated by small noisy flows (mean |ln| 1.8),
the published "unreliability" possibly a different object, the Cayman Islands (221 pairs) as
baseline; (5) 2017's 1.7 M extra flows: the equal split in the HS conversion; (6) no known source
for UN reporter metadata in the weights. The paper itself (p. 11) DROPS HK and US re-exports; the
2024 CEPII slides say they are kept - a conflict between sources, the owner's call. The UN
information the paper does use is on import valuation (CIF/FOB/FAS, fn 10 and 17), for the
freight step only.

## The trust scores on clean declarations (13 Nov 2026)

Reading pages 17-19 of the paper as images: equation (3) is misprinted (its denominator repeats
the exporter's term; the code uses the intended symmetric form, which is also BACI's measured
shape); Figures 3-4 put the paper's own footnote-22 scores at 0.2-0.8 for most countries, the
scale of CEPII's published files, against ours at ~1.9. Same formula, so the difference is in
what enters the regression. Two departures from the letter were left: the paper measures the
distance on imports "now cleaned from CIF rates" (2.4), and its data held no declaration under
1,000 USD (p. 10). With both restored (2023), footnote-22 scores stayed large (1.75/0.86; the
Cayman Islands, 181 pairs, set the minimum at 0.16 against a mean of 1.36) but the ranking moved
toward BACI's (rank correlation 0.88/0.79). Fitting BACI's recovered ln V against our
least-square means, sigma = LS_RD directly (footnote 22 skipped, which it allows) fits best
(R2 0.68; footnote 22: negative). Caveat from the review: the recovered constants fix V only up
to a common factor; the fit is evidence, not proof. Choosing "sigma = LS_RD" is OUR reading,
chosen because it matches BACI; it is labelled as such.

Engine switches: `--rel-fob-rule paper --rel-min-decl 1000 --sigma-rule ls` - the reliability
regression on freight-stripped declarations of at least 1,000 USD, sigma = least-square means;
the output on all declarations, no freight removed. France->Germany exporter weight: 0.60 (BACI
0.60; before 0.01). Runner `~/comtrade/run_clean.sh`, outputs `~/comtrade/yb_YYYY`.

| year | within 10% (before -> now) | within 25% (before -> now) | total / BACI |
|---|---|---|---|
| 2017 | 73.9% -> 73.9% | 83.2% -> 84.9% | 0.984 |
| 2018 | 71.3% -> 76.2% | 79.5% -> 86.6% | 0.984 |
| 2019 | 71.8% -> 77.4% | 80.6% -> 87.6% | 0.986 |
| 2020 | 75.6% -> 77.6% | 84.4% -> 87.8% | 0.989 |
| 2021 | 75.1% -> 77.5% | 83.8% -> 87.4% | 0.994 |
| 2022 | 74.9% -> 77.8% | 83.5% -> 87.7% | 1.004 |
| 2023 | 73.6% -> 75.5% | 82.4% -> 85.6% | 0.998 |
| 2024 | 73.0% -> 77.3% | 80.9% -> 87.2% | 1.007 |

Where the rest is (2024): flows one side declared, 99.0% within 25% of BACI; flows both sides
declared, 72.7%. On the yearly data the one-sided flows match: what is left is the weighting
of two-sided flows.

### Pair by pair: our weights against BACI's (2023)

BACI's weight read flow by flow on all products (two-sided flows where the two reports differ by
more than 30%, a = (BACI - M)/(X - M), median per country pair, >= 20 flows): stable within a pair
(interquartile range < 0.1) for 8,016 of 8,431 pairs, 90% of the value - one weight per country
pair, on the whole universe. Ours against it: correlation 0.80, 41% of pairs within 0.10.
**We trust exporters too much**: median exporter weight ours 0.50, BACI 0.34; China as exporter
0.56 vs 0.14, the USA 0.66 vs 0.27, Germany 0.83 vs 0.56. Equation (5) is additive, so it cannot
tell whether exporters as a group report worse than importers: the sum-to-zero constraints set
that by convention (both roles centred on one intercept). BACI evidently rates exporters worse
(the paper's own p. 11: customs watch the origin of imports more than the destination of exports).
One offset on the exporters' sigma (+0.1) takes pairs within 0.10 from 41% to 50%. Equation (4),
not additive, does identify the two roles' levels: fitting it directly is the paper's own route
to that split. Table `~/comtrade/pair_weights_2023.parquet`.

### Which side is worse as a group: the one number mirror data cannot give (13 Nov 2026)

Correction to the note above: equation (4) depends on sigma_i^2 + sigma_j^2 only, so it does
not identify the two roles' levels either. No method on mirror data can: every flow shows the two
errors summed. Something must be assumed. Footnote 22 assumes the best exporter and the best
importer are equally good (each role's minimum set to zero). We keep that assumption, with
"best" taken among reporters with at least 100,000 pairs (`--role-align 100000`): with the single
best of all (the Cayman Islands) it gives absurd weights; the cut-off was chosen on 2023 and then
held unchanged on the seven other years as the test.

Recipe: `--rel-fob-rule paper --rel-min-decl 1000 --sigma-rule ls --role-align 100000`, runner
`~/comtrade/run_align.sh` (pauses the UN download during the run; restarts it on exit), outputs
`~/comtrade/yc_YYYY`. The exporters' shift came out +0.09 to +0.12 every year; mean exporter
weight 0.36-0.38 (BACI's median pair weight 0.34).

| year | within 10% (paper as written -> clean sample -> aligned) | within 25% aligned | total / BACI |
|---|---|---|---|
| 2017 | 73.9 -> 73.9 -> 74.9% | 85.2% | 0.990 |
| 2018 | 71.3 -> 76.2 -> 78.0% | 87.8% | 0.991 |
| 2019 | 71.8 -> 77.4 -> 79.2% | 88.8% | 0.992 |
| 2020 | 75.6 -> 77.6 -> 79.7% | 89.1% | 0.995 |
| 2021 | 75.1 -> 77.5 -> 79.9% | 89.0% | 1.001 |
| 2022 | 74.9 -> 77.8 -> 80.2% | 89.5% | 1.011 |
| 2023 | 73.6 -> 75.5 -> 78.6% | 88.1% | 1.005 |
| 2024 | 73.0 -> 77.3 -> 79.0% | 88.3% | 1.012 |

The rule holds out of sample: every one of the seven years not used to choose it improves.
With BACI's own recovered constants the 2023 figure was 85.6% / 90.3%.

### One-sided flows are not "done" at 25%: the exact match (14 Nov 2026)

BACI takes a flow declared by one side as declared, so the target is the dollar, not 25%. 2023,
run yc_2023, 6.34 million one-sided flows found in BACI (3,376 bn USD), each set against the raw UN
declaration (`~/comtrade/onesided_causes.py`):

| | flows | value |
|---|---|---|
| equal to BACI within 0.1% | 76.9% | 91.6% |
| product code renumbered or split between HS editions (2,208 HS 2017 codes affected) | 8.2% | 2.9% |
| ours = the raw declaration exactly, BACI differs (median ratio 0.999, as often above as below) | 14.4% | 5.2% |
| re-export cases (ours, raw and BACI all differ) | 0.4% | 0.1% |
| raw = BACI but ours differs (our processing) | 3 flows | 0 |

Our processing changes nothing it should not. The conversion between HS editions is the fixable
part (and 2017's lag). The 14% where we equal today's UN figure and BACI does not look like
revisions after CEPII's January download: not reproducible without their snapshot.
Lesson: an analysis on the Lenovo next to the download got the download killed (oomd, 08:49,
5.6 GB peak for the pull alone): pause `comtrade-bulk.service` for ANY heavy query, not only for runs.

### The UN's own HS 2017 version of the data (14 Nov 2026)

The UN bulk service serves every year already converted to older editions (`--cl H5`): 2023 in HS
2017, 158 reporters, 205 M rows, in `~/comtrade/raw/comtrade_bulk_A_H5` (19.5 min, 158 calls). Run
yd_2023 on it (same recipe): within 10% 78.8% (78.6% on our own conversion), ours-only flows 82,121
(225,748), one-sided exact 77.1% (76.9%), one-sided on converted codes still 8.2% off. Code totals
match ours to 0.1%: the UN's conversion IS ours (same tables). CEPII converts its own way,
unpublished. A first reading blamed the UN row sending HS 2022 e-waste (8549) to processors
(854231): wrong - e-waste is a few bn USD in 2023, the 77 bn gap on 854231 is two-sided weighting
on a large product. Decision proposed: take the UN's H5 data as the yearly input (fewer phantom
flows, same accuracy); leave CEPII's own conversion (8% of one-sided flows, 3% of value) for later.

## Declarations filed in an older HS edition are not converted up (14 Nov 2026)

A web search (CEPII's own pages) found, on https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/DescriptionBACI.html:
"Conversions from newer to older revisions are possible, but not the reverse (conversions from
older to newer revisions)." We had been converting declarations filed in HS 2012 and earlier UP to
HS 2017 (equal split over candidates). Also found: release notes Feb 2021 ("flows with a value below
1000USD were removed. This is not the case anymore"); a 2022 CEPII blog post confirming a one-sided
flow takes the declared value. Nothing published on changes to the weights or on how a newer code
that maps to several older ones is handled.

Engine switch `--older-editions drop` (also `unchanged`: keep codes identical one to one; `split`:
the old behaviour). 2017: drop 82.6% within 10% / 90.5% within 25%, ours-only flows 6,327 (was
1,713,818); unchanged 75.8%; split 74.9%. So BACI HS 2017 leaves older-edition declarations out.
Runner `~/comtrade/run_cepii_old.sh`, outputs `~/comtrade/yf_YYYY` (2017: `ye_2017_drop`).

| year | within 10% (aligned -> + older editions left out) | within 25% | ours-only flows | total / BACI |
|---|---|---|---|---|
| 2017 | 74.9 -> 82.6% | 90.5% | 6,327 | 0.993 |
| 2018 | 78.0 -> 81.8% | 90.5% | 7,466 | 0.992 |
| 2019 | 79.2 -> 81.7% | 90.5% | 7,447 | 0.992 |
| 2020 | 79.7 -> 81.2% | 90.1% | 25,049 | 0.995 |
| 2021 | 79.9 -> 80.5% | 89.4% | 50,824 | 1.001 |
| 2022 | 80.2 -> 80.6% | 89.7% | 54,935 | 1.011 |
| 2023 | 78.6 -> 78.8% | 88.3% | 81,839 | 1.005 |
| 2024 | 79.0 -> 79.3% | 88.5% | 321,327 | 1.012 |

Current recipe: `--rel-fob-rule paper --rel-min-decl 1000 --sigma-rule ls --role-align 100000
--older-editions drop`, input = declarations as reported (`comtrade_bulk_A_HS`), like CEPII.

### Why the match falls in recent years: files re-published after CEPII's copy (14 Nov 2026)

The UN bulk listing gives the publication date of each reporter-year file we hold. Each matched flow
was scored by the latest date among the reporters whose declarations it uses (current recipe, same
outputs as above).

| year | flows on files unchanged since before Nov 2025 | their within 10% | flows on files re-published after Jan 2026 | their within 10% |
|---|---|---|---|---|
| 2017 | 98.9% | 82.6% | 1.0% | 82.0% |
| 2018 | 94.9% | 82.3% | 4.1% | 72.1% |
| 2019 | 98.2% | 82.0% | 1.5% | 67.3% |
| 2020 | 91.5% | 82.4% | 8.2% | 67.6% |
| 2021 | 89.8% | 81.5% | 8.7% | 70.4% |
| 2022 | 77.4% | 83.3% | 22.4% | 71.4% |
| 2023 | 62.8% | 84.2% | 33.4% | 69.4% |
| 2024 | 48.5% | 85.5% | 39.1% | 71.1% |

(The rest, Nov 2025-Jan 2026, straddles CEPII's unknown download date.) On the data CEPII and we
both saw, the match is 82-85.5% every year and slightly better for recent years. The fall comes
from the share of declarations the UN re-published after BACI V202601 was built: 1% for 2017,
39% for 2024. It is not a defect of the method; it disappears when CEPII's next release uses the
same files. "Published" is the date of the version we hold, so it covers both revisions and late
first releases.

### One set of trust scores for all years, as BACI does (14 Nov 2026)

BACI's weight on the exporter, read pair by pair as above, is the same every year: BACI 2018 vs
2023 98.2% of pairs within 0.02 (5,483 pairs), 2021 vs 2023 98.6% (2024: 91%, its declarations
being the most revised since). Ours, estimated year by year, moved: 2018 vs 2023 27% within 0.02.
So CEPII estimates the trust scores once, on all years together - equation (5) with its year term.
No transformation of our least-square means reproduces BACI's constants (best free fit R2 0.65 on
the pair logits, ours 0.60), so the remaining difference is in the regression, not in the formula
that turns scores into weights. CEPII's own published scores (2019 and 2020 releases) reproduce
the 2023 weights no better (R2 0.52-0.57).

Run: the eight years 2017-2024 pooled in one regression, recipe unchanged, the alignment cut-off
scaled to the pooled sample (best among reporters with >= 800,000 pairs = the 100,000 of one year
times eight; left at 100,000 it picks other countries and loses 7 points of pair agreement). Runner
`~/comtrade/run_pool3.sh`, output `~/comtrade/yg_pool`. Pairs within 0.10 of BACI's weight: 53-54%
(per-year scores 50%).

| year | within 10%: per-year scores -> pooled | within 25% | total / BACI |
|---|---|---|---|
| 2017 | 82.6 -> 83.6% | 91.5% | 0.990 |
| 2018 | 81.8 -> 82.3% | 90.9% | 0.991 |
| 2019 | 81.7 -> 81.8% | 90.7% | 0.992 |
| 2020 | 81.2 -> 81.2% | 90.1% | 0.995 |
| 2021 | 80.5 -> 80.8% | 89.7% | 1.002 |
| 2022 | 80.6 -> 80.7% | 89.7% | 1.010 |
| 2023 | 78.8 -> 79.4% | 88.7% | 1.006 |
| 2024 | 79.3 -> 80.1% | 89.2% | 1.013 |

Small gain, but it is CEPII's way, so it is the recipe from now on: `--periods 2017 2024` (one
run), `--rel-fob-rule paper --rel-min-decl 1000 --sigma-rule ls --role-align 800000
--older-editions drop`. Still open on the weights: our scores trust the biggest reporters (China,
USA, Germany) more, relative to small ones, than BACI does (rank correlation of the gap with the
number of pairs -0.39).

### The log weight in dollars (14 Nov 2026, evening)

Footnote 21: "Each observation is weighted with the natural log of the sum of the two reports" -
no unit. We had read it in thousand USD (the paper's data unit, p. 11). The regression was refitted
on 2023 in ten variants and each scored against BACI's 2023 pair weights (pairs within 0.10 /
R2 on the pair logits): thousand USD 50% / 0.600 (= the engine, so the refit is exact); **USD 60% /
0.698**; unweighted 58% / 0.703; weight = value 18%; sqrt(value) 30%; ln(1 + sum/1000) 51%; no
$1,000 floor 32%; both sides >= $100 47%; >= $10,000 22%; squared ln ratio 43%; |ln| capped 38%.
Only the unit helps; the $1,000 floor on each side stays. Engine switch `--rel-weight-unit usd`.
2023 alone: 78.8 -> 81.2% within 10%.

Pooled 2017-2024 with dollar weights (`~/comtrade/run_pool4.sh`, output `~/comtrade/yi_pool`):

| year | within 10% (pooled, thousand -> USD) | within 25% | within 10% on files unchanged since before Nov 2025 |
|---|---|---|---|
| 2017 | 83.6 -> 85.1% | 92.6% | 85.2% |
| 2018 | 82.3 -> 84.0% | 92.2% | 84.4% |
| 2019 | 81.8 -> 83.8% | 92.1% | 84.0% |
| 2020 | 81.2 -> 83.2% | 91.6% | 84.3% |
| 2021 | 80.8 -> 82.7% | 91.1% | 83.7% |
| 2022 | 80.7 -> 82.6% | 91.2% | 84.9% |
| 2023 | 79.4 -> 81.4% | 90.1% | 86.2% |
| 2024 | 80.1 -> 81.8% | 90.4% | 87.6% |

Recipe now: one run `--periods 2017 2024 --rel-fob-rule paper --rel-min-decl 1000 --sigma-rule ls
--role-align 800000 --older-editions drop --rel-weight-unit usd`, input as reported.

### Hunting the rest of the weight gap (14 Nov 2026, night)

Refits of equation (5) on 2023, scored by rank correlation with BACI's constants (one per country
and role, read off BACI's pair weights) and by pairs within 0.10. Our ranking: exporters 0.88,
importers 0.89 on 2023 alone; **0.92 / 0.93 with 2017-2024 pooled and dollar weights**. Our rule
for the exporter/importer level already gives the best possible shift: the gap is in the ranking.
Pattern: BACI trusts big traders (DEU, CHN, USA, NLD, GBR, MEX) less than we do, and small-flow
reporters (UKR, MKD, MDA, GEO, HRV, LSO, SWZ) more; residual vs log median flow +0.45.
Tested without closing it: flatter weights (unweighted, ln^0.5, ln^-1, sum^-0.05..-0.2: rank up to
~0.92 but the level rule then misfits), product effects at HS4/HS2/none, quantities on both sides
only, no chapters 27/71/97, squared or capped ln ratio, unweighted product demeaning, dropping
declarations revised after January 2026 (rank 0.88/0.90 -> no change).
**Each BACI edition has its own scores:** BACI HS 1992 (1995-2024) gives other weights for the same
2023 pairs (8% within 0.02, corr 0.83, trusts exporters less, median -0.20), on 3,179 codes unchanged
1992 -> 2017. So the HS 2017 scores come from the HS 2017 data - what we pool - not a long history.

**Re-exports are kept (14 Nov 2026, 22:09).** The paper (p. 11) drops Hong Kong's and the USA's
re-exports; CEPII's 2024 slides say they are kept. BACI settles it: on 2023 US exports only the US
declared, BACI equals the export figure INCLUDING re-exports on 9,463 of 9,765 flows (97%), and
X minus re-exports on 40. Engine `--reexports keep`; pooled rerun `~/comtrade/yj_pool`:

| year | within 10% | within 25% | BACI-only flows (was) | total / BACI |
|---|---|---|---|---|
| 2017 | 85.4% | 92.8% | 487 (7,218) | 0.997 |
| 2018 | 84.2% | 92.3% | 673 (6,534) | 0.997 |
| 2019 | 83.9% | 92.2% | 545 (5,747) | 0.998 |
| 2020 | 83.4% | 91.7% | 6,652 (11,695) | 1.001 |
| 2021 | 82.9% | 91.2% | 17,924 (23,023) | 1.006 |
| 2022 | 82.8% | 91.3% | 6,643 (11,724) | 1.014 |
| 2023 | 81.6% | 90.2% | 34,918 (40,161) | 1.010 |
| 2024 | 82.0% | 90.5% | 10,473 (16,390) | 1.018 |

Recipe now: `--periods 2017 2024 --rel-fob-rule paper --rel-min-decl 1000 --sigma-rule ls
--role-align 800000 --older-editions drop --rel-weight-unit usd --reexports keep`. Also tested
tonight without gain (2023 refits): ten council hypotheses - pair-balanced weights, ratio of sums
per pair or pair x HS2, size bins as an effect, ln(min) or ln x + ln m weights, RMS of signed
residuals, values rounded to thousands, the footnote 22 stderr term (median 0.008: negligible),
old-edition declarations in the regression, codes renumbered in HS 2022 left out.

## The flows furthest from BACI (15 Nov 2026)

2023 pooled yearly run (`yj_pool`) against BACI V202601, flows matched on both sides. 413,935
flows (3.5%) are off by more than a factor of 2, and they carry 35% of the total absolute gap
($1,975 bn). 343,368 of them are flows both countries declared. In 255,000 of those, **BACI equals
one declaration exactly** (to 0.1%: 84% of the "exporter" cases, 67% of the "importer" cases)
instead of the pair's usual mix. Largest cases: S19 -> CHN 854231 (CHN declares $76.9 bn, S19
$1.5 bn, BACI $1.5 bn); USA -> GBR 841112; CHE -> USA 711590; GBR -> CHE 710813.

What it is not (all tested on the far flows against the flows BACI mixes):
- not UN files re-published after CEPII's copy (47% of these flows use two files unchanged
  since before Nov 2025, the same share as for mixed flows);
- not the larger or smaller declaration (51-54% the larger);
- not a country pair, a reporter-product, a product or a reporter: within every grouping
  BACI mixes some flows and uses one side on others (impurity 15-17% for every grouping,
  baseline 17.5%);
- not the UN flags on the raw rows (classification, isOriginalClassification, isQtyEstimated,
  isNetWgtEstimated, legacyEstimationFlag, isReported/isAggregate, net weight present): same
  distribution for the declaration BACI ignored as for mixed flows;
- not the flow's own numbers: a decision tree on value gap, quantity gap, sizes, unit values
  against the product median and our weights predicts nothing (79.2% vs 78.5% always-mix).

Reading: for those flows CEPII's input most likely lacked the other declaration. That cannot be
reproduced from the files we hold. Scripts: `far.py` .. `far6.py`, `flags.py` (not kept in the repo).

## Step 2: the monthly BACI, 2017-01 to 2026-09 (15 Nov 2026)

`~/comtrade/run_monthly.sh`: one run per year on the UN's monthly declarations, same recipe,
trust scores taken from the yearly pooled run (`--reliability-from ~/comtrade/yj_pool/_fit`, one
set per edition as BACI), `--older-editions drop --reexports keep`. Output `~/comtrade/mm_<year>/`,
one parquet per month (~2 GB a year). 25-35 min a year on the Lenovo; started 13:30, done 18:34
(the first start at 09:29 died with the power cut).

Twelve months summed and compared with BACI's year:

| year | flows in both | within 10% | within 25% | total / BACI |
|---|---|---|---|---|
| 2017 | 9,253,039 | 76.4% | 85.6% | 0.999 |
| 2018 | 10,043,889 | 78.6% | 87.8% | 0.999 |
| 2019 | 10,295,704 | 78.5% | 87.5% | 0.999 |
| 2020 | 9,916,832 | 75.6% | 85.4% | 1.003 |
| 2021 | 10,468,242 | 76.6% | 86.1% | 1.009 |
| 2022 | 10,791,262 | 76.2% | 86.5% | 1.016 |
| 2023 | 10,708,982 | 76.5% | 86.2% | 1.013 |
| 2024 | 10,301,089 | 76.9% | 85.9% | 1.025 |

About 6 points below the yearly run: BACI reconciles the year, we reconcile each month and add.
2025 and 2026 have no BACI to compare. Months stay complete (4.8-5.0 m flows, ~$1.9-2.1 trn)
through 2026-04, then thin as reporters are still to file: 2026-07 3.9 m, 2026-08 2.8 m,
2026-09 0.4 m flows. Treat 2026-05 onward as provisional and 2026-08/09 as partial.

## The second edition: BACI HS 1992, 1995-2024 (17 Nov 2026)

Engine targets HS 1992 (`--hs-target H0`; UNSD tables HS1996/2002/2007 -> HS1992 added to
`raw/concordance/`, BACI's HS92 product list), 30 years pooled in one regression, same recipe
(`~/comtrade/run_hs92.sh`, output `~/comtrade/h92_pool`, 3 h on the Lenovo; grouping now one period
at a time - the 30-year aggregate ran out of memory; `ulimit -n` raised for the ~5,000 files).

Against BACI_HS92_V202601, flow by flow: 66-73% within 10%, 77-83% within 25% every year (1995
72.8%, 2005 69.1%, 2015 66.7%, 2024 67.0%); totals within 0.2-2.7%. Flows only one side declared:
**99.9% within 25%** (our input and HS conversion match CEPII's); two-sided flows: 52-55% within 25%.
1995-1999 hold exactly CEPII's flow set (ours-only 0, BACI-only 0.02-0.1%).

Why the two-sided flows miss:
- BACI-92's pair weights are **constant over 1998-2023** (98% of pairs within 0.02), as in BACI-17:
  one set of scores per edition.
- `--role-align 3000000` (the 8-year 800,000 scaled by 30/8) **found no importer with that many
  pairs (max 2.85 m) and silently switched off**; the engine now warns. Without it our exporter
  weight is +0.32 above BACI-92's on the median pair (pairs within 0.10: 10-11%; corr 0.80).
- Scanning the exporter shift on our saved LS: best +0.36 -> **83.9% of pairs within 0.10** (BACI-17's
  best: +0.06-0.08 -> 64-66%). No "best reporter" cut-off gives +0.36 (cut-offs 0.1-2.5 m give -0.08
  to +0.26), and no role statistic (means, medians, n-weighted, same-country) gives 0.08 and 0.36.
- **Footnote 22 as written, per role** (sigma = pi/2 (LS - min LS of the role - 2 stderr)): 76.1% of
  BACI-92 pairs within 0.10, but 30.8% of BACI-17's. With one min over both roles: 26.4% / 56.6%.
  Reading: the HS92 edition follows the paper's footnote closely; the HS17 edition does not.
  The exporter/importer level is not identified by equation (5) and CEPII's rule for it is undocumented.

### HS 1992 edition with footnote 22 as written (17 Nov 2026, 13:15-16:20)

Same run, `--sigma-rule footnote22` and no `--role-align` (`~/comtrade/run_hs92_fn22.sh`, output
`~/comtrade/h92_fn22`): sigma = pi/2 (LS - min LS of the role - 2 stderr), the paper's own rule.

| years | within 10% (was, LS + no alignment) | within 25% | total / BACI |
|---|---|---|---|
| 1995-1999 | 88.7-90.0% (69.7-72.8%) | 94.0-94.7% | 0.991-0.995 |
| 2000-2009 | 87.5-88.6% (68.5-70.7%) | 92.9-93.7% | 0.984-1.004 |
| 2010-2019 | 86.4-87.3% (66.7-68.4%) | 92.4-92.8% | 1.002-1.016 |
| 2020-2024 | 84.8-86.2% (65.9-67.1%) | 91.1-92.4% | 1.014-1.026 |

Two-sided flows: 52-55% -> **84% within 25%**; one-sided stay 99.9%. Best match on either edition.
The HS92 edition follows the paper's footnote 22 to the letter. The HS17 edition does not (footnote
22 per role reproduces only 31% of its pair weights): its recipe stays LS + alignment, an open question.

## Other reconciliations read (17 Nov 2026): Harvard Growth Lab, OECD BIMTS

- **Harvard Growth Lab** (WP 251, 2025; Scientific Data 2026; code github.com/harvard-growth-lab/
  comtrade-mirroring, Apache-2.0). Paper: one score per country from OLS of the pair discrepancy on
  exporter + importer dummies, at country-pair TOTALS (not products), year by year; the level is fixed by
  setting one "base" country to zero, chosen for the best R2; negatives set to 0; softmax weights; the
  bottom 10% of reporters per role are ignored (the partner's figure is used alone); CIF/FOB regression at
  aggregate level capped at 20%; HS conversion by data-driven weights (Lukaszuk-Torun). The CODE does
  something else: an iterative fixed point (25 rounds) of inverse partner-weighted discrepancies, with a
  likely exporter/importer transposition and several filters that are no-ops. Cites BACI only for CIF/FOB.
- **OECD BIMTS** (Cassimon, Gutierrez, Liberatore, Sarrazin, 2025, 57 pp.). Weight = "symmetry index"
  per reporter x PRODUCT x year: 1 - trade-weighted mean of |X - M| / (X + M), 3-year moving average;
  balanced value = (SI_x X + SI_m M) / (SI_x + SI_m); unreported flows enter as zero. Before that:
  product-code correction, confidential/4-digit trade dispatched to HS6, unspecified partners mapped,
  CIF->FOB from the OECD ITIC margins, re-exports identified and reallocated to producer countries. Says
  BACI makes no re-export correction. No code published.
- Neither says anything about BACI's undocumented steps (the HS17 exporter/importer level, the flows where
  BACI uses one declaration). Both face the same level problem and fix it by their own convention.
- Second-opinion review of the above (two independent readers, 17 Nov 2026): neither source reveals
  CEPII's implementation. Qualify three of our claims: (1) the flow headline is helped by one-sided flows;
  the test of the mixing is the two-sided figure (84% within 25% on HS92), so report it first;
  (2) "the HS17 edition uses another level rule" is a hypothesis - a different transformation, sample or
  preprocessing would look the same; (3) "CEPII's input lacked the declaration" is not established.
  Still to test for (3): declarations filed in an older HS edition and converted vs original, absolute value
  floors on the dropped side, data vintage. Already excluded: rounding (gaps > x1.3), UN flags incl.
  isOriginalClassification, sizes and quantity presence (tree). Also noted: Harvard's claim that its
  normal matrix is always singular is wrong (a signless Laplacian with an odd cycle has full rank).
