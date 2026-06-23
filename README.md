# EU trade-dependency pipeline (Comext)

**Live atlas → https://materials-atlas.github.io/eu_trade_dependency/**

Public-data demo: **who does the EU *really* depend on for critical raw materials?**
An atlas of **twenty-two** critical materials — rare-earth magnets, magnesium, germanium,
graphite, gallium, tungsten, cobalt, niobium, boron, feldspar, vanadium, manganese, bauxite,
baryte, phosphate rock, lithium, antimony, platinum, palladium, fluorspar, titanium and
silicon — corrected for the transit-port distortion. The pipeline is parameterised by CN
code, so it generalises to any.

The point is methodological. The obvious way to read the data is the wrong one:

- **Naive — by importing member state.** Spreads "dependence" across DE / PL / NL
  and is distorted by the **Rotterdam/Antwerp effect**: goods are customs-cleared in
  NL/BE ports but bound elsewhere. This panel measures *logistics geography*, not
  dependence. It is the trap.
- **Corrected — EU as one entity, by country of origin.** For *extra-EU* imports the
  Comext `partner` field already **is** the country of origin, so this strips the
  transit distortion and shows who the EU actually relies on.

The headline chart puts the two side by side — that visible gap is the whole pitch.

## The atlas: twenty-two critical materials (2024, corrected to origin)

The constant across every material is that **the naive member-state view is wrong** — and
the dependency map is strikingly diverse. China is the single largest source, but the true
origin of only **eight of the twenty-two** — far from a majority. The EU also leans on Turkey
(boron, feldspar), South Africa (PGMs, vanadium), Gabon and Guinea (manganese, bauxite),
Brazil (niobium), Russia (phosphate), Chile, Mexico, Kazakhstan, Tajikistan and Norway —
none of them visible in the member-state view.

| Material | Naive top (member state) | Corrected top (origin) | HHI |
|----------|--------------------------|------------------------|----:|
| Boron (natural borates) | scattered (none > 20 %) | **Turkey 98 %** | 0.96 |
| Rare-earth magnets | DE / PL / NL spread | **China 93 %** | 0.86 |
| Magnesium | **Netherlands 44 %** | **China 92 %** | 0.85 |
| Niobium (ferro-Nb) | **Netherlands 49 %** | **Brazil 84 %**, CA 16 % | 0.73 |
| Feldspar | **Spain 45 %**, IT 34 % | **Turkey 84 %**, MA 12 % | 0.71 |
| Germanium | **Belgium 63 %** | **China 83 %** | 0.71 |
| Graphite | **Germany 58 %** | **China 82 %** | 0.69 |
| Lithium carbonate | **Netherlands 39 %**, DE 34 % | **Chile 75 %**, US 13 % | 0.58 |
| Antimony | France / Belgium 37 % each | **Tajikistan 69 %**, China 6 % | 0.49 |
| Gallium | **Germany 78 %** | **China 68 %** | 0.50 |
| Cobalt (oxides) | **Belgium 43 %** | **China 62 %**, GB 28 % | 0.47 |
| Bauxite | **Ireland 35 %** | **Guinea 59 %**, BR 18 % | 0.39 |
| Tungsten | **Germany 55 %** | **China 58 %**, GB 22 % | 0.40 |
| Platinum | **Germany 43 %** | **South Africa 57 %**, GB 18 % | 0.37 |
| Baryte | **Netherlands 25 %**, IT 24 % | **China 53 %**, MA 30 % | 0.39 |
| Vanadium (ferro-V) | **Netherlands 35 %** | **South Africa 53 %**, KR 32 % | 0.40 |
| Manganese ore | **France 42 %**, ES 26 % | **Gabon 51 %**, ZA 41 % | 0.43 |
| Silicon | **Germany 44 %** | **Norway 47 %**, BR 15 % | 0.26 |
| Fluorspar (>97 % CaF2) | **Italy 51 %** | **Mexico 42 %**, ZA 36 % | 0.32 |
| Phosphate rock | **Netherlands 33 %**, BE 31 % | **Russia 41 %**, MA 27 % | 0.26 |
| Palladium | **Germany 60 %** | **South Africa 40 %**, RU 20 % | 0.25 |
| Titanium | **France 40 %** | **Kazakhstan 33 %**, US 25 % | 0.21 |

Highlights: **boron** (~98 %) and **feldspar** (~84 %) are twin Turkey near-monopolies the
naive view scatters across member states. **Niobium** is a ~84 % Brazil monopoly behind a
Rotterdam (NL 49 %) façade; **bauxite** traces to **Guinea** and **manganese** to **Gabon** —
African origins that vanish in the member-state picture (Ireland, France). **Germanium** is
the cleanest China trap (Belgium = Umicore's Antwerp hub); **palladium** the sharpest
(Germany 60 % → South Africa + Russia). **Phosphate** carries a Russia (sanctions) exposure.
Most series run 2010–2024 (magnets only from 2023, when its CN8 code was created); the
provisional latest year is excluded.

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
- `index.html` — the multi-product atlas (repo root, so it is the **GitHub Pages** site);
  regenerate with `build_static.R`
- `build_static.R` — regenerates `index.html` + the per-product PNGs in `out/`
- `refresh.ps1` — one command: re-fetch every material + rebuild the atlas (canonical
  product list lives here; `-EndPeriod` tracks the current year)
- `methodology.html` — self-contained one-page method note (the leave-behind)
- `download_data.ps1` — fetches Comext value + quantity for one product into `raw/`
- `raw/` — downloaded Comext data (gitignored)
- `out/` — generated PNGs (committed as the no-install deliverable) + datasets (CSVs
  gitignored)

Public Eurostat (Comext) data only.
