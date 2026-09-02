# Consumption drivers — source & provenance sheet

The consumption layer estimates each country's material demand as **demand = activity × intensity**,
where *activity* is a measurable real-world "driver" (steel made, cars built, chips sold…) and
*intensity* is back-solved from a known world total (self-calibrating, so world sums can't drift).
This sheet documents **where every driver's data comes from**, how real it is, and — for the drivers
that can't be made fully real — exactly *why*.

Three honesty tiers:

- **Real split** — a real, annual, *per-country* series. Both the level and the country distribution
  are measured. These carry the headline `real%`.
- **Level-real** — the *world total* follows a real annual curve, but the country split is a benchmark
  estimate. Labelled on the site as *"trend real, split estimated."*
- **Benchmark** — interpolated between a few real anchor years (2000 / 2010 / 2023); no open annual
  per-country series exists.

## Drivers

| Driver | Tier | Source (authoritative body) | Coverage | Notes |
|---|---|---|---|---|
| **steel** | Real split | worldsteel — *World Steel in Figures* + Steel Data Viewer | per-country, annual 2001–2025 | Built from ~15 WSIF editions; `world_steel.csv` shapes the world level. China 2004/05/13 on revised basis. |
| **vehicles** | Real split | OICA — production statistics (total vehicles) | per-country, annual 2000–2025 | Recent years via OICA Excel + Internet Archive; company-ranking files rejected (book output to HQ). |
| **EVs** | Real split | IEA — Global EV Data Explorer (open API) | per-country, annual 2010–2024 | `powertrain=EV` total row (BEV+PHEV+FCEV); no login needed. |
| **aluminium** | Real split | USGS — Mineral Commodity Summaries (smelter production) | per-country, annual 2008–2023 | Public domain; parsed from MCS editions. |
| **cement** | Real split | USGS — Mineral Commodity Summaries | per-country, annual 2008–2023 | Public domain; kt→Mt. |
| **drilling** | Real split | Baker Hughes — Rig Count | US/Canada 2001–2024; ~48 intl 2012–2024 | **Excludes China onshore + Russia** — those kept from national benchmark. |
| **electricity** | Real split | Ember / Our World in Data | per-country, annual | Generation (TWh). |
| **population** | Real split | UN / Our World in Data | per-country, annual | Proxy for dispersed end-uses. |
| **nuclear** | Real split | IAEA / Ember | per-country, annual | Nuclear generation. |
| **solar** | Real split | IRENA / Ember | per-country, annual | Capacity / generation. |
| **wind** | Real split | IRENA / Ember | per-country, annual | Capacity / generation. |
| **fertilizer** | Real split | FAOSTAT | per-country, annual | Phosphate nutrient use. |
| **aerospace** | Level-real | Airbus O&D + Boeing O&D | world, annual 2000–2025 | `world_aero.csv` = Airbus + Boeing commercial deliveries. Captures 2001–03 post-9/11, 2019 MAX grounding, 2020 COVID. Country split stays benchmark. |
| **semiconductors** | Level-real | WSTS/SIA world sales (level) + SEMI 2025 materials-spend (split) | world, annual 2000–2025; split 2000/2010/2023/2025 | `world_semi.csv` = WSTS/SIA billings. Country split corrected to SEMI 2025 (Taiwan #1, 16 yrs). See below. |
| **glass** | Benchmark | — | anchors only | No open per-country annual series exists. |
| **lead** | Benchmark | ILZSG (not used) | anchors only | ILZSG per-country data is subscription-gated. |

## The four hard drivers — why they can't be fully real

- **semiconductors (split).** The only clean *per-country annual physical* series (fab wafer capacity)
  is **SEMI World Fab Watch** — proprietary/licensed. Every free path was evaluated and falls short of
  a real annual split: **WSTS** (4-region *revenue*, copyrighted, login-gated), the **OECD Chip
  Landscape** (a single 2025 snapshot; per-economy values only as unextractable bar heights), and
  aggregator rankings (single-year, secondary). What *is* free and authoritative: **WSTS/SIA world
  sales** (the level) and **SEMI 2025 materials-spend by economy** (a recent, physical, authoritative
  *snapshot* of the split). So semiconductors is built as level-real with a SEMI-anchored split, not a
  real annual split.
- **aerospace (split).** Airbus and Boeing publish full delivery histories for free, but only as
  *maker* totals — there is no per-country series of aerospace material consumption. Hence level-real.
- **lead.** The right body (ILZSG) has per-country data behind a paid subscription.
- **glass.** No public per-country annual series exists at all.

Closing these last splits would require **paying** for SEMI World Fab Watch or ILZSG data — deferred
unless a client needs that precision.

## Reproducing / verifying

- Builders (all in the repo root): `build_consumption.py` → `out/consumption.json` (single-year,
  self-calibrating); `build_consumption_series.py` → `out/consumption_series.json` (2000–2025 matrix);
  `build_anchor.py` → `out/anchor.json`. `check.py` re-derives the anchor from inputs and guards every
  push.
- Driver data lives in `raw/activity/` (`drivers.csv`, `drivers_history.csv`, `drivers_annual.csv`,
  and the world-level curves `world_steel.csv`, `world_aero.csv`, `world_semi.csv`).
- Downloaded source files (worldsteel/OICA PDFs and spreadsheets, etc.) are archived under
  `raw/_sources/` (gitignored — they are third-party copyrighted publications; only the extracted
  factual numbers are committed).

*Standing rule: primary/authoritative sources only (USGS, worldsteel, OICA, IEA, IRENA, Ember, UN,
FAOSTAT, IAEA, SEMI, WSTS/SIA, Baker Hughes). No aggregators, no Wikipedia. Where the only source is
gated or nonexistent, the gap is flagged honestly rather than filled with a weaker proxy dressed as
precision.*
