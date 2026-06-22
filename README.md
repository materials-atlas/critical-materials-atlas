# EU trade-dependency pipeline (Comext)

Public-data demo: **who does the EU *really* depend on for critical raw materials?**
An atlas of **eight** critical materials — rare-earth magnets, magnesium, germanium,
graphite, gallium, tungsten, antimony and silicon — corrected for the transit-port
distortion. The pipeline is parameterised by CN code, so it generalises to any.

The point is methodological. The obvious way to read the data is the wrong one:

- **Naive — by importing member state.** Spreads "dependence" across DE / PL / NL
  and is distorted by the **Rotterdam/Antwerp effect**: goods are customs-cleared in
  NL/BE ports but bound elsewhere. This panel measures *logistics geography*, not
  dependence. It is the trap.
- **Corrected — EU as one entity, by country of origin.** For *extra-EU* imports the
  Comext `partner` field already **is** the country of origin, so this strips the
  transit distortion and shows who the EU actually relies on.

The headline chart puts the two side by side — that visible gap is the whole pitch.

## The atlas: eight critical materials (2024, corrected to origin)

The constant across every material is that **the naive member-state view is wrong**.
China is the true origin for six of the eight; antimony traces to Tajikistan and silicon
to Norway — the cases that show the method *measures* rather than confirms.

| Material | Naive top (member state) | Corrected top (origin) | HHI |
|----------|--------------------------|------------------------|----:|
| Rare-earth magnets | DE / PL / NL spread | **China 93 %** | 0.86 |
| Magnesium | **Netherlands 44 %** | **China 92 %** | 0.85 |
| Germanium | **Belgium 63 %** | **China 83 %** | 0.71 |
| Graphite | **Germany 58 %** | **China 82 %** | 0.69 |
| Gallium | **Germany 78 %** | **China 68 %** | 0.50 |
| Tungsten | **Germany 55 %** | **China 58 %**, GB 22 % | 0.40 |
| Antimony | France / Belgium 37 % each | **Tajikistan 69 %**, China 6 % | 0.49 |
| Silicon | **Germany 44 %** | **Norway 47 %**, BR 15 % | 0.26 |

Highlights: **germanium** is the cleanest trap (Belgium = Umicore's Antwerp hub, not an
origin). **Gallium** carries the geopolitics — China's origin share runs 96.8 % (2022) →
85 % (2023) → 68 % (2024) as Canada and Russia step in, China's July-2023 export controls
visible directly in customs data. **Antimony** is the credibility case: the naive view
says France/Belgium, the truth is Tajikistan. Most series run 2010–2024 (magnets only from
2023, when its CN8 code was created).

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
# 1. fetch raw value + quantity CSVs into raw/. The downloader is parameterised by CN
#    code; fetch the whole atlas at once (PowerShell):
$atlas = @{ magnets='85051110'; magnesium='81041100'; germanium='81129295';
            graphite='25049000'; gallium='81129289'; tungsten='81019400';
            antimony='81101000'; silicon='28046900' }
$atlas.GetEnumerator() | ForEach-Object { .\download_data.ps1 -Product $_.Value -Label $_.Key }
# 2. build the magnets datasets + headline chart, then the static atlas (base R)
Rscript comext-magnet-dependency-demo.R
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
- `build_static.R` — regenerates the no-install static deliverable from current code
- `methodology.html` — self-contained one-page method note (the leave-behind)
- `download_data.ps1` — fetches Comext value + quantity for one product into `raw/`
- `raw/` — downloaded Comext data (gitignored)
- `out/` — generated datasets + charts; the multi-product `index.html` + its PNGs are
  committed as a no-install deliverable (regenerate with `build_static.R`), the CSVs are
  gitignored

Public Eurostat (Comext) data only.
