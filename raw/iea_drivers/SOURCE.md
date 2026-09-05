# IEA driver-candidate datasets

Neither of these carries a mineral quantity, so neither belongs in the cube. Both are **activity
driver** candidates for the trade-independent consumption model (`demand = activity x intensity`),
which is a different intake category with different rules.

## Data_annex_Energy_and_AI.xlsx — Energy and AI report annex
- **What**: data-centre installed capacity (GW), world + region + US + China. Split by
  hyperscale / colocation / enterprise, plus IT load and power usage effectiveness.
- **Observed years**: 2020, 2023, 2024. Projections (2030, 2035) under Base / Lift-Off /
  High Efficiency scenarios — **observed only**, same rule as every other source here.
- **Why it is interesting**: the atlas has a data-centre value chain but NO data-centre driver.
  Current drivers are steel, vehicles, EV, electricity, solar, wind, cement, population,
  aluminium, drilling, fertiliser, aerospace, nuclear, semiconductors, lead, glass.
- **The blocker, stated honestly**: our intensities are back-solved from a KNOWN WORLD TOTAL
  (`intensity = KNOWN_WORLD x end_use_share / WORLD_TOTAL`). To use data-centre GW as a driver we
  need a published world total of a material consumed by data centres. Without one it can support
  a narrative but not a calibrated estimate — and an uncalibrated driver is the thing this model
  was designed to avoid.
- Licence: IEA, CC BY 4.0 (report annex).

## IEA_Energy_ValueAdded.xlsx — Energy and Emissions per Value Added Database
- **What**: sectoral VALUE ADDED by ISIC Rev.4 division, country-year, current and constant
  prices, in USD and local currency. 2000-2021. All OECD plus ~100 non-OECD countries.
  Sheets: `Manufacturing data` (ISIC divisions 10-33), `VA section data` (sections A-U).
- **Why it matters more than it looks**: the IEA's own methodology note says it models
  non-clean-energy mineral demand from "historical consumption by end-use applications, relevant
  activity drivers (GDP, industry value added, steel production) and material intensities" —
  i.e. this is the driver the IEA itself uses, and the atlas's consumption model has the same
  shape. It would let the model reach materials whose end use spreads across manufacturing
  sectors where we have no physical driver: electronics (26), machinery (28), transport
  equipment (29-30), fabricated metals (25).
- **Grain**: country-year-sector. Correct for a driver.
- **LICENCE CONSTRAINT, decisive**: "Terms of Use for Non-CC Material" — this is **NOT CC BY**.
  The atlas publishes its cube openly, so this data **must not be redistributed** in
  `out/cube.parquet` or any published file. It may be used as an input whose *derived* outputs
  are ours. Any use must keep the raw table unpublished.

## IEA EEI database - Highlights (June 2026).xlsb — Energy End-uses and Efficiency Indicators
- **What**: the `Activity data` sheet is the relevant one — country x end-use x activity measure,
  2000-2024. Carries **value added by industrial sub-sector** (food, textiles, wood, chemicals,
  non-metallic minerals, basic metals, machinery...) plus population and floor area.
  The rest of the workbook is energy consumption, emissions and efficiency indicators.
- **Why interesting**: same driver category as the Value Added database, on a longer window
  (to 2024 vs 2021) but "highlights" = reduced coverage. The two overlap and should be compared
  before either is wired in, not stacked.
- **Format**: XLSB. Needs `pyxlsb`, which is now installed.
- **LICENCE**: "Terms of Use for Non-CC Material" — **NOT CC BY**. Same constraint as the Value
  Added database: usable as an input, **must not be redistributed** in the published cube.

---

## The intake rule these three clarified

The atlas takes data in through **two doors**, and most things that look relevant fit neither:

| Door | Test | Goes to |
|---|---|---|
| **Cube** | Does a row carry a **mineral quantity** for a **country and a year**? | `cube.parquet`, published |
| **Driver** | Is it an **activity series** (country-year) that a material intensity could be applied to? | consumption model input, not published raw |
| *Neither* | Project-level, building-level, or measured only in CO2 / kWh / USD with no material link | catalogued as `declined`, with the reason |

And one hard gate on top: **a non-CC source may be used but never republished.** The atlas publishes
its cube openly, so a licence that forbids redistribution keeps that source out of `out/`,
permanently, regardless of how useful it is.
