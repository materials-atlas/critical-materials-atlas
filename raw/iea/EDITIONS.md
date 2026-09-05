# IEA Critical Minerals Dataset — edition tracker

Four editions exist. Each one publishes its own **observed base year** in the first column of
sheet "2 Total supply for key minerals", so collecting them turns a single snapshot into a
short time series — and lets us see how much the IEA revises a year after first publishing it.

Download page (free IEA account required):
https://www.iea.org/data-and-statistics/data-product/critical-minerals-dataset

| Edition   | Released   | Observed base year | Held? | Save as                            |
|-----------|------------|--------------------|-------|------------------------------------|
| July 2023 | 11/07/2023 | ~2022              | NO    | `CM_Data_Explorer_2023-07.xlsx`    |
| May 2024  | 17/05/2024 | ~2023              | NO    | `CM_Data_Explorer_2024-05.xlsx`    |
| May 2025  | 21/05/2025 | 2024               | YES   | `CM_Data_Explorer.xlsx` (current)  |
| July 2026 | 27/07/2026 | ~2025              | NO    | `CM_Data_Explorer_2026-07.xlsx`    |

Licence: CC BY 4.0, attribution required.

## What happens once they are here
`build_cube_iea.py` already parses the base-year column of a workbook. Adding the other editions
needs one change: read every file matching `CM_Data_Explorer*.xlsx`, take each one's own base-year
column, and tag the rows with the edition so the same (material, country, year) can appear from two
editions without colliding — i.e. **edition becomes a vintage dimension**, exactly like `basis` and
`stage`. Two editions reporting the same year differently is not a conflict to resolve; it is a
revision, and being able to show it is the point.

## Why this is worth doing
- 2022–2025 of country-level MINE **and REFINING** production for the six energy-transition
  minerals. Refining-by-country is the layer where BGS is thinnest.
- A measured revision history: how much does a published "observation" move once the next
  edition restates it? Nobody can answer that from one file, and it bears directly on how much
  weight any single-year figure should carry.
