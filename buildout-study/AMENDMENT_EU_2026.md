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

## Deviations log

Every change made after this filing goes here, dated, with its reason.
