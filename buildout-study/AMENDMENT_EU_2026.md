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

## Result - run 2026-09-18 (after deviations 5-8)

Run by `analysis_eu.py`; every number is in `out/buildout_eu.json`. 175 months, January
2012 to 2026-07; 86,342 flow-years of EU trade with countries
outside the EU, imports and exports, the United Kingdom excluded on both sides in every year
(deviation 5). Gaps are relative to 2012-2020; 2026 is January to July. This result supersedes the first
run, whose numbers and "heavier units" reading are withdrawn (deviations 5-7).

| Comparison | 2021-22 | 2023-24 | 2025 | 2026 Jan-Jul |
|---|---|---|---|---|
| (c) vs motors, pumps, compressors - value per tonne **(headline)** | +0.016 (+2%, p = 0.701) | +0.138 (+15%, p = 0.106) | +0.176 (+19%, p = 0.081) | +0.124 (+13%, p = 0.208) |
| (c) vs motors, pumps, compressors - tonnes | -0.086 (-8%, p = 0.106) | +0.104 (+11%, p = 0.371) | +0.135 (+14%, p = 0.377) | +0.372 (+45%, p = 0.109) |
| (c) vs motors, pumps, compressors - value per item | +0.292 (+34%, p = 0.077) | +0.413 (+51%, p = 0.071) | +0.417 (+52%, p = 0.077) | +0.467 (+59%, p = 0.066) |
| (c) vs motors, pumps, compressors - kilograms per item (exploratory, deviation 7) | +0.263 (+30%, p = 0.048) | +0.263 (+30%, p = 0.072) | +0.237 (+27%, p = 0.156) | +0.329 (+39%, p = 0.086) |
| (a) vs filed machinery - value per tonne | +0.011 (+1%, p = 0.716) | +0.178 (+19%, p = 0.036) | +0.247 (+28%, p = 0.043) | +0.244 (+28%, p = 0.036) |
| (a) vs filed machinery - tonnes | +0.029 (+3%, p = 0.584) | +0.254 (+29%, p = 0.034) | +0.328 (+39%, p = 0.021) | +0.478 (+61%, p = 0.044) |
| (b) vs construction only - value per tonne | +0.028 (+3%, p = 0.432) | +0.196 (+22%, p = 0.029) | +0.276 (+32%, p = 0.036) | +0.280 (+32%, p = 0.023) |
| (b) vs construction only - tonnes | +0.029 (+3%, p = 0.592) | +0.255 (+29%, p = 0.036) | +0.337 (+40%, p = 0.023) | +0.453 (+57%, p = 0.072) |
| (c) at eight digits - value per tonne (filed sensitivity) | +0.028 (+3%, p = 0.323) | +0.150 (+16%, p = 0.036) | +0.195 (+21%, p = 0.033) | +0.139 (+15%, p = 0.092) |
| (c) at eight digits - value per item (filed sensitivity) | +0.184 (+20%, p = 0.041) | +0.283 (+33%, p = 0.037) | +0.291 (+34%, p = 0.033) | +0.354 (+43%, p = 0.044) |
| (c) intra-EU trade - value per tonne (filed sensitivity) | +0.062 (+6%, p = 0.290) | +0.327 (+39%, p = 0.039) | +0.386 (+47%, p = 0.039) | +0.406 (+50%, p = 0.040) |

**Test 1, by the filed reading: still not distinguishable from electrical goods generally, in EU data
either.** No post period's interval on the headline comparison excludes zero. The smallest gap it could
reliably detect is 2021-22 0.10, 2023-24 0.24, 2025 0.29, 2026 Jan-Jul 0.27 log points, larger than the estimates, so the design cannot see a gap of the size
it estimates. Year by year, relative to 2019 (not to 2012-2020): 2023 +0.15 (p 0.095), 2024 +0.15 (p 0.075), 2025 +0.19 (p 0.072), 2026 +0.14 (p 0.135). The filed sensitivities point the
other way - at eight digits (4 transformer and 31 comparison lines) the gap excludes zero in 2023-24 and
2025, and on intra-EU trade from 2023-24 on - but the filing made the six-digit extra-EU comparison
the headline, and it stays the headline. Against the filed machinery and construction machinery alone,
the gaps in value per tonne exclude zero in every post period from 2023; in tonnes, all but construction
only in 2026 (p = 0.072).

**Pre-trend rule.** Passes for value per tonne against all three comparisons (c_price, a_price, b_price); fails for
c_volume (2014, 2015, 2016); c_per_item (2014, 2017, 2018); a_volume (2017); b_volume (2017); c_kg_per_item (2014, 2015, 2016, 2017). Passing is weak evidence with seven lines: deviation 3 of the main filing showed noise
alone can cross the band.

**Test 2: the filed general clause was triggered, and it is uninformative about transformers.** Value per
item and value per tonne diverge against motors, pumps and compressors, which by the filed test paragraph
means the per-tonne gap is not read as price ("materially" had no filed threshold; the divergence is
+0.41 against +0.14 in 2023-24, and their difference was not tested). The
exploratory decomposition (deviation 7) shows where the divergence comes from. Each group's own weight
per item, relative to 2019, within flows:

- transformers: 2021 +0.04, 2022 +0.10, 2023 +0.06, 2024 +0.04, 2025 -0.03, 2026 +0.06;
- motors, pumps and compressors: 2021 -0.15, 2022 -0.20, 2023 -0.20, 2024 -0.21, 2025 -0.24, 2026 -0.25.

Transformers' weight per item stayed within about 10% of 2019 in every year (point values, no intervals); the comparison goods became about a fifth lighter per
item. The relative "per item" gap is therefore a fact about motors, pumps and compressors, not about
transformers, and the first run's reading - that the average transformer became heavier - is withdrawn.
What the decomposition does say about transformers is narrower: in EU trade, the per-tonne rise was not
accompanied by heavier units, so heavier units do not explain it. Other kinds of mix - higher efficiency
or higher specification at similar weight - are not ruled out.

Value per item is usable, after the cleaning of deviation 6, for 89% to 94% of transformer
flow-years each year (`checks.per_item_coverage`).

**Test 3: the value of EU imports of GOES (7225.11, 7226.11) from outside the EU.**

| Year | EUR m | China | Japan | Russia | Korea | three largest | their share |
|---|---|---|---|---|---|---|---|
| 2019 | 162 | 9% | 34% | 19% | 16% | JP, RU, US | 71% |
| 2020 | 150 | 17% | 36% | 19% | 19% | JP, KR, RU | 74% |
| 2021 | 193 | 27% | 36% | 18% | 11% | JP, CN, RU | 81% |
| 2022 | 409 | 27% | 29% | 28% | 8% | JP, RU, CN | 84% |
| 2023 | 458 | 36% | 47% | 3% | 4% | JP, CN, KR | 87% |
| 2024 | 418 | 52% | 33% | 0% | 9% | CN, JP, KR | 94% |
| 2025 | 547 | 57% | 32% | 0% | 5% | CN, JP, KR | 94% |
| 2026 | 336 | 52% | 33% | 0% | 11% | CN, JP, KR | 96% |

China's share of this import value went from 9% in 2019 to 57% in 2025; Russia's from 19% to none; the
three largest partners' share - whoever they were in the year - from 71% to 94%. China was second in 2021
and 2023, third in 2022 (behind Japan and Russia), and first from 2024. This is the EU's imports of
grain-oriented electrical steel by value, not all electrical steel, not tonnes and not EU consumption.

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
5. **2026-09-18, after the first result - the UK removed from both sides, all years.** The UK was a
   declaring member until January 2020 and an extra-EU partner from 2020, so the "extra-EU" sample
   changed composition exactly at the treatment boundary. Found by Codex and the fact-checker. The UK is
   now excluded as declarant and as partner in every year, so "outside the EU" means the same partners
   throughout. The earlier numbers are superseded.
6. **2026-09-18, after the first result - value per item cleaned.** Value per item was value over all
   months divided by the count over months that report one, so a month with value and no count inflated
   it; and no outlier band was applied to it. Now value, weight and count are all summed over months that
   report a count, and the filed 0.1-10x band applies to value per item as to value per tonne.
7. **2026-09-18, exploratory, after the first result - whose weight moved.** The fact-checker showed that
   a relative per-item gap can come from either side: its rough check found transformer weight per item
   flat and motors, pumps and compressors lighter. Each group's own weight per item is now traced over
   time (flow effects only, relative to 2019), and the relative kg-per-item gap is estimated with the
   filed method. Exploratory: the filing named neither.
8. **2026-09-18 - pre-trend rule run for every comparison and measure.** The first run applied it only
   to four of them.
