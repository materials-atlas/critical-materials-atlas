# EU trade-dependency pipeline (Comext)

Public-data demo: **who does the EU *really* depend on for a critical product?**
First instance — rare-earth permanent magnets (CN `8505 11 10`).

The point is methodological. The obvious way to read the data is the wrong one:

- **Naive — by importing member state.** Spreads "dependence" across DE / PL / NL
  and is distorted by the **Rotterdam/Antwerp effect**: goods are customs-cleared in
  NL/BE ports but bound elsewhere. This panel measures *logistics geography*, not
  dependence. It is the trap.
- **Corrected — EU as one entity, by country of origin.** For *extra-EU* imports the
  Comext `partner` field already **is** the country of origin, so this strips the
  transit distortion and shows who the EU actually relies on.

The headline chart puts the two side by side — that visible gap is the whole pitch.

## Headline finding (2023–2024)

Extra-EU imports of CN 8505 11 10, corrected to origin:

| Year | China share (value) | China share (tonnage) | HHI (value) |
|------|--------------------:|----------------------:|------------:|
| 2023 | 92.7 % | 91.6 % | 0.86 |
| 2024 | 92.7 % | 91.1 % | 0.86 |

A single supplier at ~93 % of value with an HHI of ~0.86 is near-total concentration.
The next origins (Philippines, Vietnam, Japan) are each under 3 %.

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

```sh
# 1. fetch raw value + quantity CSVs into raw/  (PowerShell on Windows)
powershell -File download_data.ps1
# 2. build datasets + headline chart
Rscript comext-magnet-dependency-demo.R
```

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
- `download_data.ps1` — fetches Comext value + quantity for one product into `raw/`
- `raw/` — downloaded Comext data (gitignored)
- `out/` — generated datasets + charts; the `dashboard.html` + headline PNGs are
  committed as a no-install deliverable, the regenerated CSVs are gitignored

Public Eurostat (Comext) data only.
