# Data library

Every external dataset the project holds: **31 sources, 3.44 GB**.

The files live under `raw/`, which is gitignored - they are large and all re-downloadable
from the sources below. **This record is committed**, so the repository always knows what
was collected, under what licence, and why it was kept, even where the files are absent.

Not being in the cube does not make a dataset useless. There are three intakes:

| Intake | Test |
|---|---|
| **cube** | a mineral quantity for a country and a year |
| **driver** | an activity series per country-year that an intensity can apply to |
| **reference** | everything a future question might need |

**A non-CC licence permits use but never redistribution in `out/`.**

| Folder | Dataset | Licence | Status | Files | MB | Why we might need it |
|---|---|---|---|---|---|---|
| `raw/baci` | CEPII BACI bilateral trade, HS02 and HS17 vintages | Free for research | in cube (partly) | 7 | 2848.9 | HS02 gives 2002-2024 on one nomenclature. Only the 47 mapped codes are ingested; the rest is deliberate ballast left out. |
| `raw/bgs` | BGS World Mineral Statistics full panel | Open Government Licence | in cube | 64 | 400.7 | The spine: 410k records, production + trade by country, 1970-2024. |
| `raw/_sources` | Primary PDFs and source-of-record documents | various | reference | 135 | 50.8 | Where a cited figure can be re-checked against the document it came from. |
| `raw/iea_drivers` | IEA activity datasets: Energy & AI annex, Value Added DB, EEI Highlights | MIXED - Energy&AI is CC BY 4.0; Value Added and EEI are NOT CC | driver candidates | 3 | 31.5 | Country-year ACTIVITY series for the consumption model (demand = activity x intensity). Value added by ISIC division is the driver the IEA itself uses. The non-CC two may be used but never redistributed in out/. |
| `raw/usgs_mcs` | USGS Mineral Commodity Summaries PDFs | US public domain | partly extracted | 33 | 23.3 | RESERVES, refinery output, import reliance and recycling are still unextracted - the largest known unopened box in the library. |
| `raw/comtrade` | UN Comtrade extracts | UN, free | in use | 3 | 22.4 | Mirror side of the trade reconciliation. |
| `raw/mrds` | USGS Mineral Resources Data System | US public domain | reference | 1 | 16.9 | Deposit records, site grain. |
| `raw/iea` | IEA Critical Minerals Dataset + report PDFs | CC BY 4.0 | in cube (driver too) | 8 | 11.0 | Base-year supply by country at mine AND refining stage - the layer where BGS is thinnest. Two editions held, two missing. |
| `raw/geodist` | CEPII GeoDist country distances | Free for research | in use | 2 | 10.2 | Distance/contiguity for trade-gravity and reallocation work. |
| `raw/iea_rdd` | IEA Energy Technology RD&D Budgets (public + private), 1974-2025 | NOT CC - Terms of Use for Non-CC Material | reference | 2 | 6.6 | Country-year-technology R&D SPEND. Money, not an activity a material intensity can multiply, so not a driver. Kept because it is the best public measure of how hard a country is trying on a technology - a possible leading indicator for deployment, and a possible read on SUBSTITUTION effort, which the atlas already has a layer for. Not redistributable. |
| `raw/eucrm` | EU Critical Raw Materials assessment | EU, reuse permitted | reference | 2 | 5.9 | Criticality scores and end-use shares - indicators ABOUT materials, so a dimension rather than cube rows. Also the list vintages used for the ex-ante freeze test. |
| `raw/usgs_hist` | USGS Historical Statistics (DS 140), 84 workbooks | US public domain | in cube | 85 | 4.3 | Depth to 1900 and world production totals. Found by the catalog after sitting unused except for its price column. |
| `raw/surveys` | National geological survey extracts | mixed public | reference | 1 | 3.5 | Country-specific reserves and production where a survey publishes better than the global compilations. |
| `raw/activity` | Activity drivers: steel, vehicles, EV, electricity, solar, wind, cement, population, aerospace, semiconductors... | mixed public | in use | 7 | 1.7 | The inputs to the consumption model. Any new driver lands here. |
| `raw/osm` | OpenStreetMap extracts | ODbL | reference | 1 | 1.5 | Infrastructure geometry (ports, rail) for logistics work. |
| `raw/iea_etp` | IEA Energy Technology Perspectives 2017 summaries | RESTRICTED - fee required for use in modelling / derived products | HELD, NOT USABLE | 3 | 1.1 | LICENCE-BLOCKED, not merely non-CC: the terms require a paid Licence Agreement to use this data "in any type of modelling for the purpose of creating derived data or derived products" - which is exactly what every page here is. Held for reference so the decision is inspectable and nobody re-downloads it to ask again. Also a 2018-vintage scenario set, superseded several times. |
| `raw/apparent` | Per-metal apparent-consumption inputs | derived | in use | 6 | 0.9 | Feeds build_apparent.py, which is retained because the cube cannot yet do lithium. |
| `raw/pink` | World Bank Pink Sheet commodity prices | World Bank, CC BY 4.0 | reference | 1 | 0.6 | Annual public price series - the licence-safe option if a price sidecar is ever built. |
| `raw/icmm` | ICMM member and site data | ICMM terms | reference | 2 | 0.4 | Industry-side context. |
| `raw/wmd` | World Mining Data 6.4, production by country | Free, attribution | in cube | 1 | 0.3 | The only source that marks every cell reported vs estimated. |
| `raw/bottomup` | Bottom-up capacity compilations | derived | in use | 1 | 0.2 | Facility-level buildup behind selected chains. |
| `raw/iea_energy_econ` | IEA Fossil Fuel Subsidies Database, 2010-2024 | CC BY 4.0 | reference | 1 | 0.2 | Consumption subsidies by country-year. Not a material series - but energy price support is one of the real reasons SMELTING locates where it does (aluminium and silicon are power-cost industries). If the chokepoint map is ever pushed from "where refining is" to "why it is there", this is an input to that argument. |
| `raw/ipis` | IPIS artisanal mining site data (DRC) | CC BY-SA | reference | 1 | 0.2 | DIRECTLY relevant to the cobalt gap: BGS under-reports DRC precisely because artisanal output does not enter national returns. |
| `raw/refining` | Refinery and smelter capacity references | mixed | in use | 1 | 0.2 | The midstream layer behind the chokepoint map. |
| `raw/usgs_outlook` | USGS Outlook tables | US public domain | in use | 2 | 0.2 | Refining concentration where USGS measures it directly. |
| `raw/wikidata` | Wikidata entity extracts | CC0 | reference | 1 | 0.2 | Entity reconciliation helper. |
| `raw/usgs_critmin` | USGS critical-minerals deposit map (PP1802) | US public domain | reference | 1 | 0.1 | Deposit points, no time dimension. Site-level grain, so not cube material. |
| `raw/au_ozmin` | Geoscience Australia OZMIN | CC BY 4.0 | reference | 1 | 0.0 | Australian deposits and resources - a strong reserves source if a reserves layer is built. |
| `raw/geopolrisk` | GeoPolRisk inputs (governance indicators) | mixed | in use | 1 | 0.0 | Governance weighting for the criticality layer. |
| `raw/jasansky` | Jasansky et al. mine-level dataset | CC BY 4.0 | reference | 1 | 0.0 | Asset-level mine production - different grain from the cube, but the best public route to a bottom-up check. |
| `raw/valueshare` | Value-share references | derived | in use | 1 | 0.0 | Stage value distribution along chains. |

---

*Generated by `build_library.py`. Sizes and file counts are scanned from disk; the
dataset, licence and reason are written by hand, because a script cannot infer why a
file was kept. Anything unwritten shows as UNDOCUMENTED rather than being omitted.*
