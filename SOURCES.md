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
| **lead** | Real split | USGS — Minerals Yearbook: Lead (world refinery production, T12/T13) | per-country, annual 2004–2022 | Public domain XLS. Refined (not mined) — right distribution. ~54 countries, ~93% of world. ILZSG (consumption) is the gated gold standard; USGS is the free equivalent. |
| **glass** | Real split (**proxy**) | USGS — Minerals Yearbook: Soda Ash (world production by country) | per-country, annual 2004–2024 | **Proxy**: soda ash is glass's main raw material. Public domain XLS. ~32 countries. Flagged *proxy* on the site. |
| **aerospace** | Level-real | Airbus O&D + Boeing O&D | world, annual 2000–2025 | `world_aero.csv` = Airbus + Boeing commercial deliveries. Captures 2001–03 post-9/11, 2019 MAX grounding, 2020 COVID. Country split is *ill-posed* (deliveries misallocate the metals), not blocked — see below. |
| **semiconductors** | Level-real | WSTS/SIA world sales (level) + SEMI 2025 materials-spend (split) | world, annual 2000–2025; split 2000/2010/2023/2025 | `world_semi.csv` = WSTS/SIA billings. Country split corrected to SEMI 2025 (Taiwan #1, 16 yrs). See below. |

## Lead & glass — solved via USGS (Sep 2026)

Both were previously benchmark-only. **Lead** is now real from the **USGS Minerals Yearbook Lead** world
refinery-production tables (public-domain XLS, ~5 years per edition; editions 2008/2013/2018–2022 span
2004–2022). **Glass** is proxied by **USGS Minerals Yearbook Soda Ash** world production (soda ash is
glass's principal raw material; editions span 2004–2024), flagged *proxy* on the site. ILZSG remains the
gated gold standard for lead *consumption*, but USGS refined *production* gives the same country
distribution for free. This lifted antimony 42→90%, arsenic 52→91%, boron 41→100%, feldspar 63→100%.

## The two open drivers — the honest state of their country split

> **Correction (Sep 2026).** An earlier version of this note (and a draft post) said the per-country
> series for these "cannot be built from open data." That is **false**, and false in the same way the
> atlas's retracted refining-capacity claim was: it lists *vendor* products (WSTS, SEMI, OECD) and
> skips **national statistics offices**, which are open. The honest wording is *"no single harmonised
> open series; national sources exist but have not yet been tested for concordance,"* never "cannot be
> built."

- **semiconductors (split).** The commercial *per-country fab-capacity* panel (**SEMI World Fab Watch**)
  is licensed, and WSTS (4-region revenue, copyrighted), OECD Chip Landscape (a 2025 snapshot) and
  aggregators don't give a real annual split. **But open national sources do exist and were not
  documented as checked:** China NBS (integrated-circuit output, monthly), Taiwan MOEA / TSIA, Korea
  KOSIS, Japan METI / JEITA, US Census **NAICS 334413**, Eurostat **PRODCOM 26.11**, OECD ICIO / FIGARO,
  UNIDO INDSTAT (**ISIC 2610/3030**). None is a drop-in — they measure output *value or units*, not
  materials consumption; ISIC 2610 bundles PCB assembly with chips; cross-source comparability is the
  whole problem. **Open task:** test this NSO stitch against what the `semi` driver needs; if it
  concords, `semi` can move from level-real to a real annual split. Record the outcome here *including
  rejections and reasons.* **Caveat (D6/D7):** even a perfect NSO stitch fixes *silicon-CMOS* geography
  — it still does not locate **gallium/germanium/indium**, which are consumed at LED and compound-semi
  fabs, a different map. Those splits stay de-allocated until a compound-semi/LED series is found.
- **aerospace (split).** This is **not a paywall problem — it is an ill-posed country split.** Final
  assembly (Airbus/Boeing deliveries) is a handful of plants, but the metals live on different maps:
  titanium mill products, aero-grade aluminium, superalloys, machining and engines each have their own
  geography. Deliveries-by-country would *misallocate* the metals even with a complete series. The
  missing object is **process-level metal use**, which no one publishes. So `aero` stays a world-level
  trend (Airbus + Boeing) with the country split described as unresolved, not "blocked."

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
