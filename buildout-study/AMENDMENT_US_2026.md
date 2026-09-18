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

## Deviations log

Every change made after this filing goes here, dated, with its reason.
