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

## Result - run 2026-09-18 (after deviations 1-2)

Run by `analysis_us.py`; every number is in `out/buildout_us.json`. 175 months, January 2012 to
2026-07; US general imports from 190 origin countries;
4,332 origin-line flow-years with a count of units after the filed sample rules. Gaps are
in value per unit, relative to 2012-2020.

| Comparison, value per unit | 2021-22 | 2023-24 | 2025 | 2026 Jan-Jul |
|---|---|---|---|---|
| (c) vs motors, pumps, compressors **(headline)** | +0.134 (+14%, p = 0.139) | +0.072 (+8%, p = 0.586) | +0.256 (+29%, p = 0.229) | +0.230 (+26%, p = 0.704) |
| (a) vs filed machinery | +0.178 (+20%, p = 0.505) | +0.092 (+10%, p = 0.783) | +0.350 (+42%, p = 0.314) | +0.080 (+8%, p = 0.868) |
| (b) vs construction only | +0.145 (+16%, p = 0.680) | +0.227 (+25%, p = 0.589) | +0.463 (+59%, p = 0.339) | +0.135 (+14%, p = 0.829) |
| (c) at ten digits (filed sensitivity) | +0.001 (+0%, p = 0.994) | +0.113 (+12%, p = 0.359) | +0.396 (+49%, p = 0.010) | +0.206 (+23%, p = 0.231) |

**Test 1, by the filed reading: still not distinguishable from electrical goods generally, in US imports
either.** No headline interval excludes zero. The pre-trend rule fails for all three comparisons (every
year 2014-2018 outside +/-0.05), so these are relative patterns at best, and noisy ones: a count of
transformers weighs a 10 kVA unit and a 200 MVA unit the same. The ten-digit sensitivity excludes zero in
2025 only (p = 0.010), which, on a comparison whose
pre-trend rule fails, is not read.

**Test 2, the filed per-side paths.** Each group's own value per unit, within flows, relative to 2019:

- transformers: 2021 -0.19, 2022 +0.01, 2023 +0.03, 2024 +0.03, 2025 +0.21, 2026 +0.08;
- motors pumps compressors: 2021 +0.04, 2022 -0.04, 2023 +0.07, 2024 +0.28, 2025 +0.17, 2026 +0.07;
- filed machinery: 2021 -0.16, 2022 -0.31, 2023 -0.08, 2024 +0.01, 2025 -0.12, 2026 +0.02;

Transformers' own value per unit rose in 2025, and so did the comparison electrical goods' in 2024-25: the
US record, like the EU's, shows electrical goods rising together rather than transformers alone. The filed
weight test **could not be run**: the Census reports kilograms for transformer imports only from 2026
(deviation 1).

**Test 3: US imports of GOES (7225.11, 7226.11), by origin.**

| Year | USD m | tonnes | China, share of value | three largest origins, share of value | their share |
|---|---|---|---|---|---|
| 2019 | 53.0 | 27896 | 4.2% | Korea, South 49%, Japan 26%, Brazil 8% | 83% |
| 2020 | 48.6 | 25169 | 2.3% | Korea, South 51%, Japan 34%, Russia 6% | 91% |
| 2021 | 89.7 | 41991 | 1.2% | Japan 57%, Korea, South 38%, Russia 3% | 97% |
| 2022 | 67.6 | 20055 | 0.7% | Japan 50%, Korea, South 28%, Canada 14% | 92% |
| 2023 | 125.6 | 31609 | 0.6% | Japan 43%, Korea, South 41%, Canada 7% | 90% |
| 2024 | 117.8 | 36065 | 0.6% | Korea, South 44%, Japan 42%, Czech Republic 4% | 91% |
| 2025 | 64.0 | 19933 | 0.7% | Japan 59%, Korea, South 21%, Czech Republic 5% | 86% |
| 2026 | 51.7 | 16382 | 0.3% | Japan 73%, Germany 12%, Korea, South 10% | 95% |

China's share of the value of US GOES imports was between 0.3% and 1.2% in every year from
2021; Japan and South Korea supplied most of it. The concentration of world GOES exports in China does not
reach US imports. This is US imports only, not US consumption or production, and the report does not say
why.

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
