# Critical raw materials — mine ▸ refinery ▸ trade atlas

**Live → https://criticalmaterialsatlas.org/**

A public-data atlas of **32 critical raw materials**: for each one, where it is **mined**, where it is
**refined**, and the **real global trade** between every country pair — both directions, for any country
you pick. Built to make one thing visible that most trade dashboards hide: **the refiner is usually not
the source.** An apparent China dependence on cobalt is, upstream, a Congo *mining* dependence funnelled
through a Chinese refinery — China is the chokepoint, not the mine.

It's a single static HTML file (vanilla JS, no build step) served from GitHub Pages, plus a small data
pipeline. No backend.

**Headline finding → [`FINDINGS.md`](FINDINGS.md):** across 32 critical materials, the top *exporter* is
not the top *miner* in **19 of 32** of them — import-origin statistics systematically overstate how
diversified supply really is. Reproduce with [`reconcile/findings.py`](reconcile/findings.py).

## What it shows

Four layers per material, from public sources:

| Layer | Source | What it is |
|---|---|---|
| **Reserves / potential** | USGS Mineral Commodity Summaries (approx.) | world reserve shares — where it *could* come from, exploited or not |
| **Mined** | USGS Mineral Commodity Summaries (approx.) | world mine-production shares |
| **Refined** | IEA Critical Minerals Outlook (approx.) | where the raw material is processed |
| **Traded** | **UN Comtrade**, via **CEPII BACI** HS17 V202601, **2018–2024** (year-selectable) | complete reconciled bilateral trade — ~16k flows/yr, ~210 countries |
| **Traded — 2025\*** | raw UN Comtrade, **self-reconciled** (`reconcile/`), provisional | a nowcast: our BACI-validated reconciliation of partial 2025 data — indicative only |
| **Traded — 2026\*\*** | Q1 monthly Comtrade momentum + Pink Sheet prices, directional | 2025 structure scaled by per-material momentum — shares = 2025, only levels tilt; a trend signal |

Four views over the same data: **Flow** (Sankey), **Map** (choropleth + curved trade arrows), **Globe**
(animated arcs), **Table** (each material `mined ▸ refined ▸ top exporter · top importer`, with a
"country domination" sort that arranges rows into an approximate triangular matrix to dramatise
concentration). Arrows/arcs are coloured by product stage: amber = raw ore, violet = refined product.

The European Union is available as **one lens among others** (per-material EU import-origin correction);
it is no longer the frame. See [`MATERIALS.md`](MATERIALS.md) for the full material → HS-code → stage
crosswalk and the headline figure from each layer.

## How country roles are derived

Country fills on the map/globe are **derived from the trade data**, not a hardcoded top-N list:

- a **miner** (amber) = a country that actually **exports the raw ore** (for raw-ore materials);
- a **refiner** (violet) = a country that actually **exports the refined product** (for refined materials);
- where the relevant form isn't in that trade stream (e.g. an ore's refined form sits under a different
  HS code), it falls back to the USGS/IEA reference shares.

**Caveat:** customs trade can't separate a true refiner from a re-export hub — Hong Kong, Singapore, the
Netherlands can surface as "refiners" of material they merely trans-ship. The role colours are *trade
exposure*, not proof of physical processing. The full set of caveats (mixing trade with approximate
reference shares, value-vs-tonnage, structural Sankey links, sqrt colouring) is in
[`methodology.html`](methodology.html) → **Limitations**.

## Build pipeline

```powershell
# 1. Global bilateral trade → out/flows_2018.json … flows_2024.json
#    Streams the CEPII BACI HS17 yearly CSVs (downloaded into raw/baci/, gitignored), filters to the 32
#    HS6 codes, maps BACI country codes → ISO2, keeps top suppliers/customers per country. BOM-free JSON.
powershell -File build_flows_years.ps1

# 2. Mine/refine reference layers + the EU Comext lens → out/data.json + per-material PNGs
Rscript build_static.R
```

`index.html` reads `out/data.json` (mine/refine shares + EU lens) and `out/flows_<year>.json` (global
trade, picked by the year slider) — no code change to add a material once its data is present.

## Layout

- `index.html` — the interactive tool (Flow / Map / Globe / Table); repo root = the GitHub Pages site
- `out/data.json` — mine (USGS) + refine (IEA) shares + EU Comext import-origin lens
- `out/flows_2018.json … flows_2024.json` — complete BACI bilateral trade, one file per year (committed)
- `build_flows_years.ps1` — BACI HS17 yearly CSVs → `out/flows_<year>.json` (multi-year, one nomenclature)
- `reconcile/` — **Python nowcast engine** (BACI-style reconciliation of raw Comtrade for years BACI
  lacks) — see **[reconcile/README.md](reconcile/README.md)** for the full method note + validation:
  `pull_comtrade.py` (raw bilateral pull) → `reconcile.py` (CIF/FOB + reliability weights + mirror
  averaging) → `validate.py` (vs official BACI 2024: top-1 exporter **25/30**, share MAE **3.5%**, HHI
  corr **0.92**) → `build_recon_flows.py` (→ `out/flows_2025.json`) → `build_2026_nowcast.py`
  (→ `out/flows_2026.json`, directional)
- `build_baci_flows.ps1` — single-year HS22 builder (legacy; superseded by the multi-year script)
- `build_static.R` — regenerates `out/data.json` + the per-material PNGs in `out/`
- `methodology.html` — one-page method note: the three layers, the refiner-vs-source correction,
  the EU Comext origin correction, and the Limitations
- `MATERIALS.md` — material → HS6 → stage crosswalk with headline figures per layer
- `VALIDATION.md` — spot-checks of each layer against published USGS/IEA figures
- `raw/` — downloaded source data (BACI zip/CSV, Comext), gitignored

## Provenance & scope

Independent demonstration from public data — USGS, IEA, UN Comtrade (CEPII BACI), Eurostat Comext. Not
affiliated with, nor representing, any institution. Figures are approximate and rounded; read each row as
an overlay of three different measures, not one observed supply chain.
