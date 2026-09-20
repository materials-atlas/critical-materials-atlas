# Amendment C: US imports to July 2026

Filed 2026-09-18, before any value in the new data was pulled. Only the API's variable list and the
units of quantity for each product code (one month, units only) were read, to plan the design. This
amendment extends `PREREGISTRATION.md` and follows `AMENDMENT_EU_2026.md`; everything there applies
unless changed here, and it carries over the EU lessons: a check for composition breaks at the treatment
boundary, the per-unit decomposition by side (now filed in advance), and no summary rows mixed with detail.

## Data

- **US Census Bureau international trade API**, `timeseries/intltrade/imports/hs`, general imports,
  monthly, January 2012 to July 2026, at the ten-digit level, by country of origin (detail rows only;
  country groupings excluded).
- **Measures:** value (USD, customs value, which excludes duties), first quantity and second quantity
  with their units. For the transformer lines the first quantity is a **count of units** and the
  second is **kilograms**; for every comparison line the only quantity is a count of units; for GOES it
  is kilograms. Months are summed to years; **2026 is January-July**.
- **Lines:** the study's fifteen six-digit lines at their ten-digit splits. Transformers split into nine
  ten-digit codes, which is finer by rating than any source used so far.

## The tests

**1. Value per unit, transformers against comparison goods.** The filing's equation (flow and year
effects; a flow is one origin country in one six-digit line) with value per unit as the outcome, because
it is the only measure the comparison lines share. Four post periods as in amendment B. Three
comparisons: (c) motors, pumps and compressors **(headline)**; (a) the filed machinery; (b) construction
machinery only. Reading, decided now: if the headline gap excludes zero in 2025 or 2026, something about
transformers' value per unit is specific to them in US imports in that period; if not, still not
distinguishable from electrical goods generally.

**2. Whose mix moved - decided before the data, not after.** A relative per-unit gap can come from
either side. So each group's own value per unit is traced over time within flows (flow effects only,
relative to 2019), filed now as part of the test, and the headline gap is read only alongside it. For
transformers, their own **kilograms per unit** and **value per kilogram** are traced the same way, at
the ten-digit level. Reading, decided now: if transformers' own kilograms per unit rose by more than
0.10 log points from 2019 to 2025 or to 2026, the value-per-unit rise is described as partly heavier
units; if not, heavier units do not explain it.

**3. US imports of GOES** (7225.11, 7226.11): each origin's share of the value, and of the kilograms,
2019 to January-July 2026, and the share of the three largest origins, named.

## Inference and sample

As in the filing and amendment B: wild cluster bootstrap by six-digit line (Webb weights, null imposed,
9,999 draws, each estimate on its own seeded stream), errors clustered by origin country beside it,
every estimate with its interval and detectable size, the ±0.05 pre-trend rule applied to every measure.
A flow-year enters at USD 100,000 or more (x 7/12 for 2026) with a positive count; values per unit more
than ten times above or below the line's median that year are dropped. The ten-digit version of test 1,
clustered by ten-digit line, is a sensitivity.

## What this cannot say

US imports only: nothing about US production, which the literature shows expanded, or about exports.
Customs value excludes duties, so tariff changes enter only through what exporters charge; US tariff
policy changed repeatedly over the period and is not separated from anything else. Counts of units say
nothing about rating within a ten-digit code. Not causal. 2026 is seven months.

## Result - run 2026-09-18 (after deviations 1-5)

Run by `analysis_us.py`; every number is in `out/buildout_us.json`. 175 months, January 2012 to
2026-07; US general imports from 190 origin countries;
4,332 origin-line flow-years with a count of units after the filed sample rules. Gaps are
in value per unit, relative to 2012-2020, with the smallest gap each estimate could reliably detect.

| Comparison, value per unit | 2021-22 | 2023-24 | 2025 | 2026 Jan-Jul |
|---|---|---|---|---|
| (c) vs motors, pumps, compressors **(headline)** | +0.134 (+14%, p = 0.139, detectable 0.25) | +0.072 (+8%, p = 0.586, detectable 0.31) | +0.256 (+29%, p = 0.229, detectable 0.56) | +0.230 (+26%, p = 0.704, detectable 0.96) |
| (a) vs filed machinery | +0.178 (+20%, p = 0.505, detectable 0.67) | +0.092 (+10%, p = 0.783, detectable 0.86) | +0.350 (+42%, p = 0.314, detectable 0.91) | +0.080 (+8%, p = 0.868, detectable 1.24) |
| (b) vs construction only | +0.145 (+16%, p = 0.680, detectable 0.93) | +0.227 (+25%, p = 0.589, detectable 1.22) | +0.463 (+59%, p = 0.339, detectable 1.22) | +0.135 (+14%, p = 0.829, detectable 1.49) |
| (c) at ten digits (filed sensitivity) | +0.001 (+0%, p = 0.994, detectable 0.26) | +0.113 (+12%, p = 0.359, detectable 0.33) | +0.396 (+49%, p = 0.010, detectable 0.45) | +0.206 (+23%, p = 0.231, detectable 0.46) |

**Test 1: no headline interval excludes zero, and the test has little power.** The smallest detectable
gap on the headline comparison is 0.31 to 0.96 log points over the post periods, so
a gap the size of the one estimated in the EU would go undetected. This is not evidence of absence. Value
per unit is also mostly a product-mix index here: one unit can be a small distribution transformer or a
large power transformer, and a small pump or a large compressor. The filed reading ("still not
distinguishable") is applied, with the power stated beside it. The ten-digit sensitivity excludes zero in
2025 (+0.396, p = 0.010); the pre-trend rule, now run on it too (deviation 3), fails
for it as for every US comparison, so it is reported and not read. The US evidence on transformers is
unstable rather than null.

**Test 2, the filed per-side paths.** Each group's own value per unit, within flows, relative to 2019:

- transformers: 2018 -0.43, 2021 -0.19, 2022 +0.01, 2023 +0.03, 2024 +0.03, 2025 +0.21, 2026 +0.08;
- motors pumps compressors: 2018 +0.04, 2021 +0.04, 2022 -0.04, 2023 +0.07, 2024 +0.28, 2025 +0.17, 2026 +0.07;
- filed machinery: 2018 -0.07, 2021 -0.16, 2022 -0.31, 2023 -0.08, 2024 +0.01, 2025 -0.12, 2026 +0.02;

Both groups' own value per unit rose in some years after 2022, but not in the same years: the comparison
goods mainly in 2024, transformers mainly in 2025. These paths carry no intervals and rest on the same
mix-sensitive denominator; they are not read as a common movement. The filed weight test could not be run
(deviation 1).

**Test 3: direct US imports of GOES (7225.11, 7226.11), by origin.**

| Year | USD m | tonnes | China, share of value | three largest origins, share of value |
|---|---|---|---|---|
| 2019 | 53.0 | 27896 | 4.2% | Korea, South 49%, Japan 26%, Brazil 8% |
| 2020 | 48.6 | 25169 | 2.3% | Korea, South 51%, Japan 34%, Russia 6% |
| 2021 | 89.7 | 41991 | 1.2% | Japan 57%, Korea, South 38%, Russia 3% |
| 2022 | 67.6 | 20055 | 0.7% | Japan 50%, Korea, South 28%, Canada 14% |
| 2023 | 125.6 | 31609 | 0.6% | Japan 43%, Korea, South 41%, Canada 7% |
| 2024 | 117.8 | 36065 | 0.6% | Korea, South 44%, Japan 42%, Czech Republic 4% |
| 2025 | 64.0 | 19933 | 0.7% | Japan 59%, Korea, South 21%, Czech Republic 5% |
| 2026 | 51.7 | 16382 | 0.3% | Japan 73%, Germany 12%, Korea, South 10% |

China's share of the value of direct US GOES imports was between 0.3% and 1.2% in every year from
2021; Japan and South Korea supplied most of it. **This is direct imports of GOES as steel only.** They are
a small part of US use (deviation 4): most GOES used in the United States arrives inside imported cores and
transformers, whose steel is not observed. For that reason the origins of US transformer imports are
reported beside it (deviation 4, descriptive):

| Year | US transformer imports, USD m | three largest origins | China |
|---|---|---|---|
| 2019 | 1532 | Mexico 41%, Austria 14%, Canada 11% | 1.2% |
| 2020 | 1810 | Mexico 44%, Canada 10%, Austria 10% | 2.8% |
| 2021 | 1796 | Mexico 44%, Canada 12%, Korea, South 10% | 0.7% |
| 2022 | 2426 | Mexico 49%, Canada 10%, Korea, South 9% | 2.0% |
| 2023 | 3976 | Mexico 40%, Korea, South 14%, Canada 8% | 2.5% |
| 2024 | 5922 | Mexico 31%, Korea, South 20%, Brazil 7% | 3.4% |
| 2025 | 7491 | Mexico 29%, Korea, South 22%, Brazil 9% | 3.5% |
| 2026 | 4507 | Mexico 30%, Korea, South 18%, Brazil 9% | 4.5% |

By weight the picture is the same: China's share of the kilograms of direct US GOES imports was at most
1.1% in any year from 2021. Direct GOES imports in 2025 (64 million dollars,
19933 tonnes) were about half their 2023-24 level; this report does not say why.

**Composition check (deviation 5).** Across 2012-2026 no study line changes its ten-digit codes or its unit
of quantity, except 8504.23, which was split from one ten-digit code into two in 2013-14, inside the
pre-period; the transformer lines therefore run on ten ten-digit codes, not the nine the filing stated.

**In hindsight.** A count of units was a weak basis for the headline: the filing could have made value per
unit within ten-digit rating classes the headline and kept the six-digit version as the sensitivity. That
is recorded here rather than changed, because the filing came first.

Nothing here says why China's share of direct GOES imports is so small - tariffs, trade remedies, supply
relationships and domestic supply are all candidates and none is tested.

## Deviations log

Every change made after this filing goes here, dated, with its reason.

1. **2026-09-18, after the first run - the weight test cannot be run.** The Census API reports the
   second quantity (kilograms) for transformer imports only from January 2026; every month from 2012 to
   2025 carries zero. The filed test of transformers' own kilograms per unit therefore has no 2019 base
   and no 2025, and cannot be run. Found on the first run.
2. **2026-09-18, after the first run - a default reading removed.** The first run's code turned the
   missing path into the reading "heavier units do not explain it". A rule must never be read off data
   that do not exist; the code now reports the test as not runnable. No other number depended on it.
3. **2026-09-18, after review - the pre-trend rule run on the ten-digit sensitivity, and empty paths
   reported as such.** The first run dismissed the ten-digit result "on a comparison whose pre-trend
   rule fails" without running the rule on that comparison; it is now run. A path with no observations
   is now reported as not runnable instead of carrying a dummy 2019 = 0.
4. **2026-09-18, descriptive, after review - where US transformer imports come from.** Direct US imports
   of GOES are a small part of US use (about 25,000 tonnes in 2020 against consumption the IEA puts at
   0.15 Mt; the single domestic producer meets 12-20% of demand). Most GOES used in the US therefore
   arrives inside imported cores and transformers. The origins of US transformer imports (8504.21-.23) are
   now reported so that the GOES table is not read as the whole of US exposure. Descriptive, unfiled.
5. **2026-09-18, after review - the composition-break check put in the code.** The filing said it carried
   over amendment B's check for composition breaks; the first run did not contain one (the fact-checker
   ran it by hand). It is now in `analysis_us.py` (`checks.composition_breaks`) and finds one change, the
   2013-14 split of 8504.23, inside the pre-period. The filing's "nine ten-digit codes" is corrected to ten.
6. **2026-09-20, descriptive, after the result - the monthly series.** A twelve-month rolling total
   of US transformer imports (8504.21-.23) was added beside the EU's, from the same download, by
   `origins_monthly.py` (`out/buildout_origins.json`): USD 1.3bn in the twelve months to December 2019
   against USD 7.7bn in the twelve months to July 2026. Descriptive, unfiled; it exists so that 2026
   can be read without comparing a part-year with a year. No estimate changed.
