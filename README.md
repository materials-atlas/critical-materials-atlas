# EU trade-dependency pipeline (Comext)

Public-data demo: **who does the EU *really* depend on for a critical product?**
Three critical products so far — rare-earth permanent magnets (CN `8505 11 10`),
gallium (`8112 92 89`) and germanium (`8112 92 95`) — and the pipeline is parameterised
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

## Headline finding (2023–2024)

Extra-EU imports of CN 8505 11 10, corrected to origin:

| Year | China share (value) | China share (tonnage) | HHI (value) |
|------|--------------------:|----------------------:|------------:|
| 2023 | 92.7 % | 91.6 % | 0.86 |
| 2024 | 92.7 % | 91.1 % | 0.86 |

A single supplier at ~93 % of value with an HHI of ~0.86 is near-total concentration.
The next origins (Philippines, Vietnam, Japan) are each under 3 %.

## More cases: gallium and germanium

The same correction, two more critical raw materials hit by China's 2023 export
controls — and the member-state trap is even starker.

| Product (2024) | Naive top (member state) | Corrected top (origin) |
|----------------|--------------------------|------------------------|
| Germanium (`8112 92 95`) | **Belgium 63 %**, DE 20 % | **China 83 %**, US 12 %, KR 4 % |
| Gallium (`8112 92 89`)   | **Germany 78 %**, NL 15 % | **China 68 %**, CA 15 %, RU 13 % |

Germanium is the cleanest trap in the set: the naive view points at Belgium (Umicore's
Antwerp refining hub — a transit/processing artefact), while the corrected view shows
China at 83 %.

These two carry **15 years of data (2010–2024)**, so the trend panel becomes a
geopolitical-shock story rather than a snapshot. Gallium's China origin share runs
2022 **96.8 %** → 2023 85 % → 2024 **68 %** as Canada and Russia step in — China's
July-2023 export controls visible directly in the customs data.

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
# 1. fetch raw value + quantity CSVs into raw/  (PowerShell on Windows).
#    The downloader is parameterised by CN code; default is magnets:
powershell -File download_data.ps1
powershell -File download_data.ps1 -Product 81129289 -Label gallium
powershell -File download_data.ps1 -Product 81129295 -Label germanium
# 2. build the magnets datasets + headline chart (base R)
Rscript comext-magnet-dependency-demo.R
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
- `methodology.html` — self-contained one-page method note (the leave-behind)
- `download_data.ps1` — fetches Comext value + quantity for one product into `raw/`
- `raw/` — downloaded Comext data (gitignored)
- `out/` — generated datasets + charts; the `dashboard.html` + headline PNGs are
  committed as a no-install deliverable, the regenerated CSVs are gitignored

Public Eurostat (Comext) data only.
