# Amendment B: the EU customs record to July 2026

Filed 2026-09-18, before any value in the new data was looked at. Only the file listing, the column
header of one monthly file and its size were read, to plan the download. This amendment extends
`PREREGISTRATION.md`; everything there still applies unless changed here.

## Why

The study's world data (CEPII BACI) stop at 2024. Two of the note's open questions can be taken
further with the EU's own customs records, which run monthly to July 2026 at the eight-digit level:
whether the transformer rise continued into 2025–26, and whether product mix explains it. The EU files
also record a **supplementary unit** where one exists, so for some lines they give a value per item, not
only per tonne.

## Data

- **Eurostat Comext**, monthly bulk files `full_v2_YYYYMM`, January 2012 to July 2026 (the latest
  published), downloaded from Eurostat's dissemination service. Each file is filtered at download to the
  study's customs lines and nothing else is kept.
- **Declarants:** the EU member states as reported in each file. **Flows:** trade with partners
  **outside the EU** only, imports and exports, as the headline. Intra-EU trade is reported under
  different rules and thresholds and is used only as a sensitivity.
- **Measures:** value in euros, net mass in kilograms, and the supplementary quantity where the line
  has one. Months are summed to years; **2026 is January–July** and is labelled as such everywhere.
- **Lines:** the study's six-digit lines at their eight-digit splits: transformers 8504.21, 8504.22,
  8504.23; GOES 7225.11, 7226.11; the filed comparison machinery (8428.10, 8426.49, 8474.20, 8474.31,
  8515.31, 8515.39); motors, pumps and compressors (8501.52, 8501.53, 8413.70, 8414.80).

## The tests

**1. The transformer pattern to 2026.** The equation of the filing, on EU extra-EU flows (a flow is one
declarant–partner–direction–six-digit line), with four post periods instead of two: 2021–22, 2023–24,
2025, and January–July 2026. Year effects absorb anything common to all lines in a year, including the
partial 2026. Three comparisons, all now filed, all reported: transformers against (a) the filed
comparison machinery, (b) construction machinery only (without welding machines), and (c) motors,
pumps and compressors. Comparison (c) is the one that decides whether anything is specific to
transformers; it is the headline comparison of this amendment.

**2. Mix.** For every transformer line whose supplementary unit is a count of items, the same
equation on the value per item. If the rise per tonne and the rise per item differ materially, product
mix is moving and the per-tonne gap is not read as price. The same equation at the eight-digit level,
clustered by eight-digit line, as a sensitivity.

**3. Electrical steel.** The share of each partner in the value of EU imports of GOES from outside the
EU, 2019 to January–July 2026, and the share of the three largest. This is the EU's view of its own
suppliers, not world exports, and will be labelled so.

## Inference and reading

As filed: flow and year effects, a wild cluster bootstrap by six-digit line (Webb weights, null imposed,
9,999 draws, each estimate on its own seeded stream), with errors clustered by declaring member state
beside it, every estimate printed with its interval and its detectable size. The pre-trend rule of the
filing applies unchanged (±0.05 log points for 2014–2018 against 2019); if it fails, the result is
described as a relative pattern, as in the note.

Reading of test 1, decided now:

| Gap against motors, pumps, compressors | Reading |
|---|---|
| positive, interval excludes zero, in 2025 or 2026 | Something specific to transformers, in the EU's imports, in that period. |
| interval includes zero | Still not distinguishable from electrical goods generally, in EU data either. |

Reading of test 2: if the per-item gap is less than half the per-tonne gap, the note's unit-value rise is
described as largely product mix in EU data.

## What this cannot say

EU trade only: nothing about US, Chinese or world trade. Nothing about production inside the EU. Not
causal. 2026 is seven months. Supplementary units are reported inconsistently across declarants and
years, and the count is reported with each result.

## Stage 2, not filed here

US Census monthly imports and UN Comtrade monthly data for other reporters are left for a later
amendment, filed before they are pulled.

## Result - run 2026-09-18

Run by `analysis_eu.py` (committed before its first run on the downloaded data); every number is in
`out/buildout_eu.json`. 175 months, January 2012 to 2026-07;
92,422 extra-EU flow-years after the filed sample rules.

| Comparison | 2021-22 | 2023-24 | 2025 | 2026 Jan-Jul |
|---|---|---|---|---|
| (c) vs motors, pumps, compressors - unit value per tonne **(headline)** | +0.007 (+1%, p = 0.846) | +0.135 (+14%, p = 0.111) | +0.176 (+19%, p = 0.079) | +0.133 (+14%, p = 0.169) |
| (c) vs motors, pumps, compressors - tonnes | -0.095 (-9%, p = 0.079) | +0.100 (+11%, p = 0.418) | +0.120 (+13%, p = 0.514) | +0.380 (+46%, p = 0.111) |
| (c) vs motors, pumps, compressors - value per item | +0.250 (+28%, p = 0.081) | +0.465 (+59%, p = 0.064) | +0.497 (+64%, p = 0.068) | +0.565 (+76%, p = 0.059) |
| (a) vs filed machinery - unit value per tonne | +0.004 (+0%, p = 0.881) | +0.180 (+20%, p = 0.040) | +0.250 (+28%, p = 0.042) | +0.249 (+28%, p = 0.037) |
| (a) vs filed machinery - tonnes | +0.021 (+2%, p = 0.643) | +0.241 (+27%, p = 0.042) | +0.309 (+36%, p = 0.029) | +0.486 (+63%, p = 0.044) |
| (b) vs construction only - unit value per tonne | +0.018 (+2%, p = 0.515) | +0.204 (+23%, p = 0.028) | +0.279 (+32%, p = 0.036) | +0.285 (+33%, p = 0.025) |
| (b) vs construction only - tonnes | +0.024 (+2%, p = 0.650) | +0.237 (+27%, p = 0.047) | +0.315 (+37%, p = 0.032) | +0.460 (+58%, p = 0.071) |
| (c) at eight digits - unit value per tonne | +0.025 (+2%, p = 0.384) | +0.147 (+16%, p = 0.037) | +0.194 (+21%, p = 0.033) | +0.143 (+15%, p = 0.069) |
| (c) at eight digits - value per item | +0.167 (+18%, p = 0.039) | +0.362 (+44%, p = 0.035) | +0.359 (+43%, p = 0.031) | +0.446 (+56%, p = 0.036) |

**Test 1, by the filed reading: still not distinguishable.** Against motors, pumps and compressors, the
transformer unit-value gap is positive in every post period after 2022, but no period's interval
excludes zero. Year by year: 2023 +0.16 (p 0.088), 2024 +0.16 (p 0.075), 2025 +0.20 (p 0.069), 2026 +0.16 (p 0.101). The filed pre-trend rule **passes** for this comparison (no year from
2014 to 2018 outside +/-0.05), as it does for comparison (a) - unlike in the world data - so these are
clean relative comparisons; they are simply not precise enough to clear the filed bar with seven customs
lines. Against the filed machinery and against construction machinery alone, the transformer rise
continued and grew into 2025 and 2026, in unit value and in tonnes, and all but one of those gaps
clear it (construction-only tonnes in 2026: p = 0.071).

**Test 2, by the filed rule: product mix is moving.** Against the same electrical goods, value per
transformer rose far more than value per tonne (+0.46 against +0.14 in 2023-24). The two differ
materially, so the per-tonne gap is not read as price: the average transformer the EU trades became
heavier - larger units - and part of what looked like a price rise per tonne is a shift in what is
shipped. The filed "less than half" rule was written for the opposite case (per-item rising less) and
does not apply; the general rule in the same paragraph does. Item counts are reported for 97% to 100% of
transformer flow-years in every year (`checks.per_item_coverage`).

**Test 3: the EU's electrical-steel imports from outside the EU.**

| Year | EUR m | China | Japan | Russia | Korea | top 3 | partners >1% |
|---|---|---|---|---|---|---|---|
| 2019 | 162 | 9% | 34% | 19% | 16% | 71% | 6 |
| 2020 | 151 | 16% | 36% | 19% | 19% | 74% | 7 |
| 2021 | 194 | 27% | 36% | 18% | 11% | 81% | 6 |
| 2022 | 410 | 27% | 29% | 28% | 8% | 84% | 6 |
| 2023 | 458 | 36% | 47% | 3% | 4% | 87% | 8 |
| 2024 | 418 | 52% | 33% | 0% | 9% | 93% | 5 |
| 2025 | 547 | 57% | 32% | 0% | 5% | 94% | 5 |
| 2026 | 336 | 52% | 33% | 0% | 11% | 96% | 4 |

China replaced Russia as the EU's second source and then became its first: from 9% of the value of EU
GOES imports from outside the EU in 2019 to 52% in 2024 and 57% in 2025, while Russia went from 19% to
none. This is the EU's view of its own imports, and 2026 is January to July.

**Intra-EU sensitivity (filed).** On trade between member states, the transformer gap against motors,
pumps and compressors is +0.327 (p = 0.039) in 2023-24,
+0.387 (p = 0.039) in 2025 and +0.406
(p = 0.040) in 2026. It is a sensitivity, not the headline: intra-EU
quantities are reported under different rules and thresholds, which is why the filing kept them out.

## Deviations log

Every change made after this filing goes here, dated, with its reason.

**2026-09-18, before any estimate - details the amendment left open, fixed now.**
1. **The minimum flow size** is the filing's USD 100,000 applied in euros (EUR 100,000), and for 2026,
   which has seven months, EUR 100,000 x 7/12, so that part-year flows are not dropped for being part-year.
2. **The value-per-item test** can only run against comparison (c): the machinery lines have no
   supplementary unit, while motors, pumps and compressors are counted in pieces, as transformers are.
3. **Periods** are coded exactly as filed: 2021-22, 2023-24, 2025, 2026 (January-July).
4. **Yearly totals excluded.** The download picked up Eurostat's fourteen yearly-total files (period
   YYYY52) alongside the 175 months, because they share the file-name pattern. Read together they would
   have double-counted every year. Found by counting files before any estimate; the yearly files were
   moved aside, and both the fetcher and the analysis now refuse periods outside 01-12.
