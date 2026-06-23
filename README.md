# EU trade-dependency pipeline (Comext)

**Live atlas → https://materials-atlas.github.io/eu_trade_dependency/**

Public-data demo: **who does the EU *really* depend on for critical raw materials?**
An atlas of **thirty-two** critical materials — essentially the full EU critical/strategic
raw-materials list — corrected for the transit-port distortion. The pipeline is parameterised
by CN code, so it generalises to any.

The point is methodological. The obvious way to read the data is the wrong one:

- **Naive — by importing member state.** Spreads "dependence" across DE / PL / NL
  and is distorted by the **Rotterdam/Antwerp effect**: goods are customs-cleared in
  NL/BE ports but bound elsewhere. This panel measures *logistics geography*, not
  dependence. It is the trap.
- **Corrected — EU as one entity, by country of origin.** For *extra-EU* imports the
  Comext `partner` field already **is** the country of origin, so this strips the
  transit distortion and shows who the EU actually relies on.

The headline chart puts the two side by side — that visible gap is the whole pitch.

## The atlas: thirty-two critical materials (2024, corrected to origin)

This is essentially the full EU critical/strategic raw-materials list — every material with
a clean CN8 code and recent data. The constant across all of them is that **the naive
member-state view is wrong**, and the corrected map is **global**: China is the single
largest source but the true origin of only **ten of the thirty-two** — under a third. The
two *most* concentrated dependencies aren't even China: **beryllium is 100 % US** and
**boron 98 % Turkey**. The EU leans on the US, Turkey, South Africa, Brazil, Japan, Vietnam,
Russia, Chile, Gabon, Guinea, Algeria, Qatar, Norway, Mexico, Kazakhstan, Tajikistan and
Australia — almost none visible in the member-state picture.

| Material | Naive top (member state) | Corrected top (origin) | HHI |
|----------|--------------------------|------------------------|----:|
| Beryllium (unwrought) | **Spain 63 %**, FR 28 % | **United States 100 %** | 1.00 |
| Boron (natural borates) | scattered (none > 20 %) | **Turkey 98 %** | 0.96 |
| Rare-earth magnets | DE / PL / NL spread | **China 93 %** | 0.86 |
| Magnesium | **Netherlands 44 %** | **China 92 %** | 0.85 |
| Arsenic | **Netherlands 31 %**, DE 16 % | **China 86 %** | 0.75 |
| Niobium (ferro-Nb) | **Netherlands 49 %** | **Brazil 84 %**, CA 16 % | 0.73 |
| Feldspar | **Spain 45 %**, IT 34 % | **Turkey 84 %**, MA 12 % | 0.71 |
| Germanium | **Belgium 63 %** | **China 83 %** | 0.71 |
| Graphite | **Germany 58 %** | **China 82 %** | 0.69 |
| Lithium carbonate | **Netherlands 39 %**, DE 34 % | **Chile 75 %**, US 13 % | 0.58 |
| Strontium carbonate | **Italy 21 %**, AT 17 % | **Japan 75 %**, CN 14 % | 0.58 |
| Antimony | France / Belgium 37 % each | **Tajikistan 69 %**, China 6 % | 0.49 |
| Gallium | **Germany 78 %** | **China 68 %** | 0.50 |
| Phosphorus | **Germany 49 %**, IT 40 % | **Vietnam 64 %**, CN 25 % | 0.48 |
| Cobalt (oxides) | **Belgium 43 %** | **China 62 %**, GB 28 % | 0.47 |
| Hafnium | **Germany 88 %** | **United States 60 %**, CN 21 % | 0.41 |
| Bauxite | **Ireland 35 %** | **Guinea 59 %**, BR 18 % | 0.39 |
| Tungsten | **Germany 55 %** | **China 58 %**, GB 22 % | 0.40 |
| Platinum | **Germany 43 %** | **South Africa 57 %**, GB 18 % | 0.37 |
| Baryte | **Netherlands 25 %**, IT 24 % | **China 53 %**, MA 30 % | 0.39 |
| Vanadium (ferro-V) | **Netherlands 35 %** | **South Africa 53 %**, KR 32 % | 0.40 |
| Manganese ore | **France 42 %**, ES 26 % | **Gabon 51 %**, ZA 41 % | 0.43 |
| Silicon | **Germany 44 %** | **Norway 47 %**, BR 15 % | 0.26 |
| Coking coal | **Germany 28 %**, NL 26 % | **US 44 %**, Australia 44 % | 0.39 |
| Fluorspar (>97 % CaF2) | **Italy 51 %** | **Mexico 42 %**, ZA 36 % | 0.32 |
| Phosphate rock | **Netherlands 33 %**, BE 31 % | **Russia 41 %**, MA 27 % | 0.26 |
| Palladium | **Germany 60 %** | **South Africa 40 %**, RU 20 % | 0.25 |
| Copper (cathodes) | **Italy 31 %**, DE 24 % | **Chile 39 %**, DRC 26 % | 0.24 |
| Helium | **Germany 24 %**, FR 22 % | **Algeria 37 %**, Qatar 31 % | 0.28 |
| Tantalum | **Germany 42 %**, CZ 25 % | **China 37 %**, JP 26 % | 0.26 |
| Titanium | **France 40 %** | **Kazakhstan 33 %**, US 25 % | 0.21 |
| Nickel | **Netherlands 39 %** | **Norway 33 %**, CA 18 % | 0.18 |

Highlights: the two sharpest dependencies are **non-China** — **beryllium** (100 % US) and
**boron** (98 % Turkey). **Hafnium** is the most extreme naive trap (Germany 88 % → the US).
New origins the member-state view erases entirely: **Guinea** (bauxite), **Gabon**
(manganese), **Japan** (strontium), **Vietnam** (phosphorus), **Algeria/Qatar** (helium),
**DRC** (copper). China is concentrated in the upper-middle (magnets, magnesium, arsenic,
germanium, graphite…), and the diffuse, low-risk cases (nickel, copper, helium, coking coal)
are themselves a finding — diversified, allied supply. Most series run 2010–2024 (magnets
only from 2023); the provisional latest year is excluded throughout.

## Method notes (the hard-to-fake bits)

- **Aggregate codes double-count.** The extract carries bloc reporters/partners
  (`EU`, `EA`, `EA21`, `EU27_2020`, `EXT_*`, `INT_*`, `WORLD`, `*_2020`) alongside the
  27 member states. If you don't drop them, origin totals inflate **~4.6×** while the
  *shares* stay ~92 % — so the error is invisible to anyone validating on shares alone.
  Both panels restrict reporters to the EU-27.
- **CN 8505 11 10 exists only from 2023** (CN8 code split / continuity break), so the
  series is deliberately short.
- **Extra-EU partner = origin.** This identity is what makes the correction possible;
  it does not hold for intra-EU flows.

## Run

Self-contained, base R only — no package installs.

```powershell
# Rebuild the whole atlas from the live Comext API — downloads every material (value +
# quantity) into raw/, then regenerates index.html and all charts. -EndPeriod defaults to
# the current year, so a new Comext release is picked up automatically:
powershell -File refresh.ps1

# To add one material: fetch it, then rebuild.
powershell -File download_data.ps1 -Product <CN8> -Label <name>
Rscript build_static.R
```

The Shiny app picks up every product fetched into `raw/` automatically — no code change.

`download_data.ps1` sends `Accept-Encoding: identity` to avoid gzip-as-text corruption
behind some proxies. Where R can reach Eurostat directly, the download can also be done
inside R — see the script header.

### Interactive dashboard

```r
# needs: shiny, ggplot2  (DT optional — enables a sortable table)
shiny::runApp(".")
```

Product + year selectors, the naive-vs-corrected chart, a multi-year trend,
value-vs-tonnage, a sortable origin table, and CSV downloads — all computed live from
`raw/` through the shared core, so the dashboard generalises to any product you fetch.

## Layout

- `comext-magnet-dependency-demo.R` — base-R batch pipeline (reads `raw/`, writes `out/`)
- `dependency_core.R` — shared base-R method (naive/corrected aggregation); sourced by
  both the pipeline and the app, so there is a single source of truth
- `app.R` — Shiny dashboard (reads `raw/` via the core)
- `index.html` — the **interactive tool** (Table / Map / Globe + a **buy-from ↔ mined-in**
  toggle that flips trade-origin to USGS mine-production), repo root = the **GitHub Pages**
  site; reads `out/data.json`
- `build_static.R` — regenerates `out/data.json` (trade origins + a USGS mine-production
  layer) + the per-product PNGs in `out/`
- `refresh.ps1` — one command: re-fetch every material + rebuild the atlas (canonical
  product list lives here; `-EndPeriod` tracks the current year)
- `methodology.html` — self-contained one-page method note (the leave-behind)
- `download_data.ps1` — fetches Comext value + quantity for one product into `raw/`
- `raw/` — downloaded Comext data (gitignored)
- `out/` — generated `data.json` + PNGs (committed as the deliverable) + datasets (CSVs
  gitignored)

Public Eurostat (Comext) data only.
