# The Critical Materials Atlas — what it is, what it holds, what it computes

**Written 2 October 2026.** Every count and figure here was measured from the repository on that
date, not read off an older document. Where a number came from an existing doc rather than from the
code, it says so.

This exists because the product outgrew its own documentation. There are ten markdown files at the
root; six of them were last touched in August, and `ARCHITECTURE.md` still prints a headline
statistic that the code no longer matches (see §10). Read this one first, then the others for depth,
knowing what each is still good for.

---

## 1. What the product is, in one page

A public-data research site about the supply chains of critical raw materials — where they are
mined, who refines them, how they actually trade, and who holds each chokepoint. It is:

- **a data asset** — one harmonised long table (the "cube") assembled from seven source families,
  plus a monthly bilateral trade engine that reconciles exporter and importer declarations;
- **a body of original research** — ten pre-registered studies, most of which *failed or returned a
  null*, published anyway with dated deviation logs;
- **a website** — 217 published routes, 291 tracked HTML files, built by 114 Python builders;
- **a citable archive** — nine GitHub releases, Zenodo concept DOI `10.5281/zenodo.21948855`,
  currently resolving to v1.8 (`22940354`).

Scale, measured: 982 commits, a 531 MiB pack, 281 Python files, 149 JSON artifacts under `out/`,
26 mechanical guards in `check.py`.

**The one-sentence version of what makes it unusual:** it reconciles two sides of the same trade
flow at monthly frequency and refuses to invent a number when they disagree, and it publishes its
own failed tests.

---

## 2. The structural fact to hold onto: there are THREE trade systems, not one

This is the thing most likely to make you misread your own site. Found by one of the review
engines reading the code, and verified here.

| | What it measures | Universe | Currency / unit | Writes | Who reads it |
|---|---|---|---|---|---|
| **A. EU Comext layer** | concentration of **EU extra-EU imports** of one CN product, by origin | EU-27 imports | **EUR** | `out/data.json` | the homepage HHI, the material profile cards |
| **B. Annual world engine** (`reconcile/`) | world bilateral trade, mirror-reconciled, then nowcast | world | USD | `out/flows_2002…2026.json` | world maps, the origin gap, the 2025/26 nowcast |
| **C. Monthly pipeline** (`pipeline/`) | monthly bilateral trade from 7 feeds, two-sided reconciliation | world, monthly | USD + kg | `pipeline/data/flows*.parquet` → the cube | the cube, the DuckDB query page, ~10 builders |

Three consequences:

1. **The headline HHI on the homepage is a European import statistic in euros, not a world
   statistic.** Verified: every material record in `out/data.json` carries `total_eur`, `origins`
   (share by extra-EU partner) and `naive` (share by importing member state — the Rotterdam trap).
   So "boron 0.96" means Turkey is ~96% of extra-EU borate imports *by value*, **not** that Turkey
   mines 96% of world boron.
2. **These HHIs must never be added or compared.** EU-import HHI, world-mine HHI
   (`build_geopolrisk.py`), world-refined HHI (`build_exposure.py`) and trade-volume HHI
   (`out/volume.json`) are four different universes.
3. **There are two reconciliation engines with opposite decisions.** `pipeline/reconcile.py`
   (monthly) *refuses* reliability weighting — `RELIABILITY_WEIGHTED = False`, because v2 was
   measured and lost. `reconcile/reconcile.py` (annual) *does* inverse-variance weight and passes
   one-sided reports through. **The annual one is what the published site mostly runs on.** They are
   not the same method and were not meant to be.

**Legacy note:** there are four R files at the root (`build_static.R`, `dependency_core.R`, `app.R`,
`comext-magnet-dependency-demo.R`). They are the ancestor of layer A. `runner.py` does not reference
`.R` at all, and thirteen Python builders now write `out/data.json`. The R is history, not the live
path — one engine cited it as live, which is the one place its map is out of date.

---

## 3. The data — seven source families

Coverage below is from `out/sources.json`, which computes it from the cube and therefore cannot go
stale.

| Source | Rows | Materials | Geographies | Years | What it is |
|---|---|---|---|---|---|
| CMA single-declaration passthrough | 1,856,030 | 33 | 232 | 2000–2026 | one-sided Comtrade, **withheld from the public extract** |
| CMA two-sided reconciliation | 590,418 | 33 | 155 | 2000–2026 | our own reconciled estimate — the original asset |
| BGS World Mineral Statistics | 275,297 | 60 | 192 | 1970–2024 | national production returns, the long series |
| CEPII BACI (HS02) | 207,366 | 30 | 229 | 2002–2024 | externally reconciled annual trade; our QA benchmark |
| USGS Historical Statistics (DS 140) | 67,084 | 79 | 2 | 1900–2023 | US-only deep history: consumption, stocks, unit values |
| World Mining Data | 9,187 | 64 | 167 | 2020–2024 | recent world mine production |
| IEA Critical Minerals | 1,055 | 6 | 30 | 2024–2050 | demand projections |

**Monthly feeds behind the pipeline** (`pipeline/adapter_*.py`), with the months each actually holds
as of today:

| Adapter | Months held | Span | Units | API key |
|---|---|---|---|---|
| `comtrade` | **318** | 200001–202606 | value + kg | optional, **but keyless is silently truncated at 500 rows** |
| `hmrc` (UK) | 28 | 202404–202607 | value + kg | no |
| `comexstat` (Brazil) | 20 | 202501–202608 | value + kg | no |
| `uscensus` | 6 | 202602–202607 | **value only, no tonnes** | yes |
| `eurostat` (Comext) | 4 | 202604–202607 | value + kg | no |
| `baci` | 3 years | 2022–2024 | value + kg | no (local zip) |
| `mirror` | 3 years | 2022–2024 | value + kg | **not an independent source** — BACI partner reports re-labelled |

Also feeding the compute layer but not adapters: ECB FX (`pipeline/fx.py`), OECD ITIC CIF/FOB
margins (`pipeline/fetch_itic.py` — note ~95% of its cells are gravity imputations), and the USGS
Mineral Commodity Summaries PDFs (`pipeline/fetch_usgs_mcs.py` → `usgs_mcs_history.parquet`, which
is production and reserves, not trade).

`DATA_SOURCES.md` lists StatCan, ABS, Japan and Korea as sources. **No adapters exist for those.**
Seven is the real number.

---

## 4. The stores — raw, assembled, published

**Raw caches** (network pulls, not published): `pipeline/data/cache/<source>.parquet` (merge on
refresh), `comtrade_cache.jsonl` (485 MB, the recent calendar window),
`comtrade_history/*.parquet` (the 2000–2024 backfill), rotation cursors in `comtrade_state.json`,
and `raw/baci/BACI_HS17_V202601.zip`.

**Assembled** by `pipeline/build.py` — and the distinction between the first three matters:

| File | Rows | What it is |
|---|---|---|
| `flows.parquet` | 3,241,238 | the union of all feeds. **Summing this double-counts** — the same shipment appears from several sources. |
| `flows_best.parquet` | 2,514,937 | de-duplication only: one row per directed flow, keeping the best source per flow (deep national > wide > mirror). **Does not average the two sides.** |
| `flows_reconciled.parquet` | 2,413,307 | the two-sided estimate. This is the engine. |

Plus `reporter_quality`, `reporter_reliability`, `reliability_weights` (v2, diagnostic only),
`material_confidence` (exact / dominant / proxy / compound / basket) and `coverage`.

**The cube, in two copies — this trips people up:**

- `pipeline/data/cube.parquet` — **full**, ~2.98M rows, 7 source families.
- `out/cube.parquet` — the **published extract**, measured today at **1,150,407 rows, 6 source
  families**. The single-declaration Comtrade passthrough is withheld under the licence policy.

They are not the same table, by design. 30 columns; identity is
`(source, measure, stage, basis, unit)` — *a material name alone is not a query.* 27 distinct
measures, from `production` and `exports` through `apparent_consumption`, `net_import_reliance`,
`stocks_government` and `unit_value_real98`.

**Published site artifacts** — 149 JSON files under `out/`, mostly one per analysis page, written by
41 builders. `out/data.json` is the shared material record and is written by **thirteen** different
builders, which is why the derived-output drift guard exists.

---

## 5. What is actually computed

### The reconciliation engine (`pipeline/reconcile.py`) — the moat

Every physical flow can be declared twice: by the exporter (FOB) and the importer (CIF, which
includes freight and insurance). Where both sides exist in the same month:

1. keep only **raw one-sided customs** feeds — BACI and mirror are excluded, because pairing them
   would be circular;
2. pick the best source per side;
3. put the importer side on an FOB basis, using an empirically estimated CIF/FOB coefficient per
   product (HS6 → HS4 → HS2 → global fallback), **capped at 1.10** for our own estimates — because
   the French customs CAF-FAB survey finds nothing above ~9.6%, so a 20% gap is not freight and
   deflating by it would erase a real disagreement;
4. if the two sides agree within 2×, publish the **equal-weight geometric mean**;
5. **if they disagree, publish nothing** — the value is NULL, `basis='disagreement'`, and both sides
   plus the range stay on the row.

What it refuses to do: fabricate a value for a disagreement; use BACI as an input (BACI is the
external benchmark); treat a declared 0 kg as a real weight; weight by reliability (v2 was built,
measured against the same BACI ablation, lost, and ships *beside* the published number).

**How real is the moat today?** Measured, because this is the claim the product rests on:

- 724,409 matched two-sided pairs exist, but **98.4% are Comtrade against Comtrade** — the same
  compiler on both sides, which is the historical backfill, not a cross-check.
- **11,926 pairs are cross-source**; removing `baci ↔ mirror` (not independent) leaves
  **~9,060 genuinely cross-compiler pairs**, spread across roughly 20 months. Largest blocks:
  HMRC ↔ Comtrade (5,284), US Census ↔ Comtrade (1,584), Comexstat ↔ Comtrade (1,168),
  Eurostat ↔ HMRC (489).

**This matters and is an action item.** The big warning comment at the top of `reconcile.py` says
the layer is "one preliminary month of one source compared with itself, plus about 105 genuine
cross-source pairs." That was true on 6 September. It is now ~9,060 pairs over ~20 months. **The
comment understates the asset by about ninety-fold and should be updated.**

The same comment's other warning is still binding and should stay: the **51% disagreement rate is
not a finding about world trade statistics** — it describes preliminary Comtrade. Quote share of
value (30%), not share of cells (49%), and say which cache.

### The derived measures

- **HHI / concentration** — four different ones, listed in §2. Do not mix.
- **The origin gap** (the flagship) — the top mining country ≠ the top exporting country. 17 materials
  by value, 18 by tonnes. The tonnes check is what makes it more than a unit artifact. A second,
  traced form re-attributes a flow to the dominant mine when the named supplier mines <5%.
- **Apparent consumption** — refined production + imports − exports. Only copper is tier A; cobalt
  double-counts DRC hydroxide feedstock, nickel misses NPI/ferronickel, and lithium cannot be done
  from the cube at all (BGS gives lithium *minerals*, the trade code gives *carbonate*).
- **The nowcast** — two years, two methods. 2025 is a full annual reconciliation of partial Comtrade,
  level-calibrated to BACI 2024. 2026 freezes 2025 *shares* and scales levels by Q1 momentum. So a
  2026 "top exporter" is last year's structure. Persistence of the top exporter is ~84% out of
  sample; that is the **naive floor, not skill**, and whether the engine beats it is pre-registered
  and **still unproven** — it resolves when CEPII BACI 2025 appears.
- **Chokepoint scoring** — *not* computed from the trade tables. The chokepoint map copies a
  hand-authored `chokepoint` object out of each of the 57 chain records. It is a curated catalogue
  with declared confidence, not a formula.
- **Risk indices** — six of them, same ingredients, different weights (transparent atlas risk,
  GeoPolRisk producer, GeoPolRisk importer, EU-style SR, Graedel-style, and a reader-reweightable
  index that deliberately returns no single number).

---

## 6. The research — ten pre-registered studies

The pattern, and the reusable asset: **file the hypothesis and thresholds before looking at the
data, commit the code before running it, and log every deviation with a date.** Most of these
returned a null or a failure and were published anyway.

| Study | Filed | Verdict | Deviations | Page |
|---|---|---|---|---|
| `reconcile` | 26 Jun | **pending, not scored** — a frozen commitment to how the 2025 nowcast will be scored against official BACI 2025 when it lands. A falsifiability bet, not a result. | 0 | `/technical-note`, `/methodology` |
| `grinding-balls` | 13 Sep | **FAIL** — grinding-ball imports do not proxy ore milled; the elasticity test misses and robustness does not rescue it. The grade test was never run: no suitable grade series exists. | 5 | `/grinding` |
| `scrap-response` | 17 Sep | **not demonstrated** — the pooled test is underpowered, and the two answerable metal-specific tests miss the filed threshold. | 7 | `/scrap` |
| `scrap-trade` | 17 Sep | **same-year comovement only** — no lagged response. Imports rise too, which weakens any reallocation story. | 8 | `/scrap` |
| `steel-scrap-price` | 21 Sep | **inconclusive** — positive under country-clustered errors, crosses zero under year-clustered. The stricter reading does not pass. | 2 | `/scrap` |
| `buildout-study` | 18 Sep | **descriptive note, not a passed causal test** — every filed pre-trend design failed, the GOES placebo failed, and the page withdraws its diff-in-diff language. | 11 | `/grid-trade` |
| `eu-grid-supply` | 21 Sep | **descriptive measurement** — import share usually *overstates* dependence; the one "critical" inverter bucket is too broad to read. China 9% → 57% of EU GOES import value. | 3 | `/grid-trade` |
| `export-controls` | 21 Sep | **as filed, no control is certified as biting**. The later antimony/bismuth signals are explicitly exploratory, not pre-registered wins. | 11 | `/export-controls` |
| `usgs-revisions` | 23 Sep | **descriptive measurement, no pass/fail test** — copper is firm (1.4%), several minor materials soft (antimony 11.3%); no filed direction is established. | 15 | `/revisions` |
| `self-audit` | 24 Sep | **mostly robust, with caveats** — three claims survive the proxy audit; molybdenum, titanium and tungsten are fragile. | 7 | `/self-audit` |

**Ten filings collapse into seven pages**, which hides the map: all three scrap filings live on
`/scrap`, both grid filings on `/grid-trade`, and `/ai-buildout` overlaps the buildout study
thematically without being one of the filings. Worth a filing→page index on the site.

Note what the column of verdicts says: **one outright fail, two not-demonstrated, one inconclusive,
three descriptive-only, one pending, one mostly-robust.** Nothing here is a clean confirmation of a
prior hypothesis. That is the product working as designed, not a disappointing run of luck — and it
is the single most defensible thing about it.

**The self-audit is the most interesting thing here**, because it turns the method on the atlas
itself: it resamples USGS-measured revisions into our own concentration finding and recounts. Result
(2,000 draws, seed pinned in the filing): the ex-ante 2011 claim holds on **7 of 7** materials
(median −0.096, sign retained in 99.9% of draws), the divergence claim at 99.7%, the full-set median
at 99.7%. Three materials are **fragile** — molybdenum, titanium, tungsten. And it states the limit
honestly: it clears the number of measurement error and leaves the *selection* problem untouched.

---

## 7. The site — 217 routes

| Category | Count | Built by | Examples |
|---|---|---|---|
| Value-chain layer | 59 | `*/record_*.py` → 57 chain JSONs; HTML shells largely hand-written | `/value-chains`, `/battery-chain`, `/grid-chain` |
| Material + country profiles | 61 | `build_profiles.py` (materials); country pages hand-written | `/profile-lithium`, `/profile-country-US` |
| Generated analytic pages | 53 | mostly one `build_*.py` each, recorded in `out/graph.json` | `/origin`, `/refiners`, `/price-volatility` |
| Pre-registered research pages | 7 | one builder each | `/grid-trade`, `/scrap`, `/grinding` |
| Narrative reports | 8 | **hand-written** — no `build_report*.py` exists | `/report-origin-gap`, `/report-product-space` |
| Navigation, method, data, trust | 22 | hand-written | `/analysis`, `/method`, `/data` |
| Retired stubs | 4 | builders deleted; pages are "moved" notices **still in the sitemap** | `/bloc-demand`, `/host-shock`, `/scenarios`, `/commodity-attribution` |
| Internal project diagrams | 3 | `build_scheme.py` | `/project-scheme`, `/project-map`, `/project-formulas` |

Builders split into two tiers, which is why so many have no HTML target: **41 analysis builders
write JSON** into `out/`, and page builders consume that JSON. `build_ot.py` alone touches eleven
pages; `build_insights.py` eight.

### Reachability and search — two measured defects

A crawl from `/` reaches **214 of 217** routes. The three unreachable ones are
the internal diagrams `/project-scheme`, `/project-map` and `/project-formulas`: they are in the
public sitemap but nothing links to them. Either link them deliberately or drop them from the
sitemap.

The site search is worse, and this is verified here, not inferred:

- `out/search-index.json` holds **203 entries against 217 routes**.
- **All 27 country profiles are missing from it.** They are in the sitemap and reachable through
  `/countries`, but a visitor searching for "France" or "Japan" on the site will not find them.
- **16 entries are not pages at all** — the `share/card-*.html` social-card templates. They are
  indexed and can surface as search results.

Separately, four retired pages (`/bloc-demand`, `/commodity-attribution`, `/host-shock`,
`/scenarios`) are "moved" notices whose builders were deleted, yet they remain sitemap routes.

---

## 8. The machinery

- **`runner.py`** — dependency-ordered rebuild. Fingerprints imported modules by *source*, not
  bytecode. Runs post-passes (canonicals, head tags, search index) after any page rebuild.
  **Never run it with `--force`.**
- **`check.py`** — 26 mechanical guards: `drift, datasets, links, js, scrub, etapes, withdrawn,
  builders, chokepoint, ledger, basis, anchor, dim, key, sdmx, mirror, withheld, engine, baci_door,
  stale, register, usgs_mcs, self_audit, head, weights, refresh`. It must pass before a push, and it
  says of itself that it proves nothing about whether the claims are *true*.
- **Scheduled, on this machine:** `CMA-trade-refresh` (daily 03:00, 3h limit — pull Comtrade,
  refresh all caches, rebuild parquets; takes ~2h); `CMA-refresh-watch` (daily 13:00 — toasts when
  the refresh stops working, writes `pipeline/data/refresh_status.txt`);
  `CMA-export-controls-watch-2027` (fires 15 Feb 2027). `atlas-comtrade-ai-finish` is a spent
  one-shot and can be deleted.
- **Releases** — v1.0 (15 Aug) through v1.8 (24 Sep), Zenodo-archived, watched daily by
  `zenodo-archive-watch`. **v1.9 is owed**: v1.8 predates the self-audit, the widened USGS panel and
  the PGM split.

---

## 9. The traps — where a number goes wrong

Mostly found by an engine review of the code; each is enforced or documented somewhere in the repo.

- **Three trade databases.** EU-Comext euros, annual world USD, monthly reconciled USD+kg. Adding
  across them is meaningless.
- **Never sum `flows.parquet`**, and never sum sources for one flow anywhere.
- **BACI and mirror are not independent** of each other, and must not enter the monthly engine.
- **HS-6 baskets.** 811292 is gallium *and* germanium at HS-6 (only CN-8 splits them). 270112 is all
  bituminous coal, not coking. 280429 is "rare gases other than argon". 850511 is magnets *of metal*
  and bundles NdFeB with alnico. 283329 is a cobalt-sulphate basket. Graphite 250490 misses flake and
  synthetic.
- **Stage and form.** Lithium carbonate is not spodumene is not hydroxide. Nickel 750210 is class-I
  metal, not NPI.
- **Gross tonnes vs contained metal.** `value_t` is filled only when convertible; `basis` says
  `gross` or `content`. Carats and m³ are never coerced.
- **CIF vs FOB.** Canada files imports FOB, China CIF, the US both. Deflating an already-FOB import
  understates it by the whole freight margin.
- **US Census has no tonnage.** Any kg total including it is incomplete by construction. A declared
  0 kg once scored 43,067 false disagreements.
- **Keyless Comtrade truncates at 500 rows, silently** — incompleteness then looks like
  disagreement. And take `motCode=0`; summing transport modes double-counts.
- **BACI units.** Value is thousands of USD, quantity is tonnes. Forget the ×1000 and every figure
  is off by three orders of magnitude.
- **Country codes.** BGS shipped Republic of Congo as `COD`. BACI has no Taiwan (it is `S19`, "Other
  Asia, nes"). `ZAR` is not `COD`, so filtering on COD drops 1970–91 DRC cobalt.
- **Money and tonnes are separate measures.** The chain JSONs are value-based; the cube is
  tonnage-based. China's tungsten ore share is 1.13% by value and 0.45% by tonnes. **Always state the
  basis.**
- **Intervals are intervals.** Germanium's refining share is 68–94%; the 81 in the risk index is a
  midpoint of two dated anchors that are not the same object.
- **Derived copies do not inherit corrections.** A number in `risk.json` can be older than the
  `data.json` it came from. This is what the `drift` guard is for.

---

## 10. The state of the documentation (read this before trusting the other docs)

| Doc | Lines | Last touched | Verdict |
|---|---|---|---|
| `ARCHITECTURE.md` | 591 | 17 Sep | Richest doc, but **line 20 is stale**: it prints "analysis families that read the cube — 0 of 13". Measured today: **10 builders read it** (9 via the `*_cube` helpers, 1 directly). Line 256 explains why full migration was *deliberately* not done — for most analyses, reading raw is correct. Fix line 20. |
| `DATA_LIBRARY.md` | 156 | 16 Sep | Good on what each source *is*, including the ITIC imputation caveat. |
| `CADENCE.md` | 85 | 16 Sep | Release cadence. Current. |
| `DATA_SOURCES.md` | 85 | — | **Lists sources with no adapters** (StatCan, ABS, Japan, Korea). Aspirational, reads as factual. |
| `SOURCES.md` | 91 | 2 Sep | Overlaps `DATA_SOURCES.md` and `DATA_LIBRARY.md`. Three docs, one subject. |
| `FINDINGS.md` / `FINDINGS-2.md` | 74 / 121 | 16 Aug / 2 Sep | Predate six of the ten studies. Historical. |
| `MATERIALS.md` | 47 | 14 Aug | Predates the panel widening. |
| `VALIDATION.md` | 70 | 10 Aug | Predates most of the 26 guards. |
| `README.md` | 128 | 16 Aug | Predates everything above. |

**That is the honest reason you feel lost.** Six of the ten root documents describe a repository
that has roughly doubled since they were written, and three of them cover the same subject.

---

## 11. What the product actually is, and what to do next

**Load-bearing — original research that could not be read off a source:**
the two-sided monthly reconciliation engine; the origin gap (because it holds in tonnes); the ten
pre-registered studies, especially the self-audit and the USGS revision study; the harmonised cube
with its honest schema (basis, stage, confidence, source ledger).

**Presentation of other people's numbers** — valuable, but not the asset: most risk indices, the
IEA demand projections, the country and material profile cards, the chokepoint catalogue (curated,
not computed).

**Open items, in the order I would take them:**

1. **Update the `reconcile.py` warning comment.** It understates the cross-source asset ninety-fold
   (§5). Anyone reading the code — including you in a month — will conclude the moat is 105 pairs.
2. **Cut `ARCHITECTURE.md` line 20 and the `DATA_SOURCES.md` phantom sources.** Both read as fact.
3. **Release v1.9.** The concept DOI currently resolves to a version without the self-audit or the
   widened panel.
4. **The "32" sweep** — 71 pages still assert a count that no external list supports.
5. **Rare earths are not in the material set at all.** No wording fix addresses this, and it is the
   substantive gap behind the "32" question.
6. **Fix the site search** — 27 country profiles are unsearchable and 16 social-card templates are
   indexed as if they were pages. This is the cheapest visible win on the list.
7. **Consolidate the three source docs into one**, and mark `FINDINGS*`, `MATERIALS`, `VALIDATION`
   and `README` as historical rather than current.
8. **Decide about the orphans** — link the three `project-*` diagrams or drop them from the sitemap,
   and drop the four retired stubs from it.
9. **Add a filing→page index**, because ten pre-registrations presenting as seven pages makes the
   research look smaller than it is.

---

*Built with two independent language models as reviewers, and neither was taken at face value.*

**Engine A** mapped the data and compute layer from the code with file:line evidence — §2, §5 and §9
are substantially its work. It found the three-trade-systems split, which is the most useful
structural fact in this document. Corrected in one place: it cited the legacy R scripts as the live
producer of `out/data.json`, but `runner.py` never invokes R and thirteen Python builders write that
file now. Its substantive claim — that the headline HHI is an EU import statistic in euros — was
verified here and is right.

**Engine B** mapped the studies and the site. Its deviation counts and verdict wordings are sharper
than the first draft's and are used above; it **corrected one row of the study table** (the
`reconcile` filing had been written up as the v1-vs-v2 engine decision; it is in fact the frozen
2025-nowcast-vs-BACI bet, which the file's own first line confirms). It also found the orphan pages
and the search-index gap, both verified here — the search gap turned out to be larger than it
reported.

**Measured against the live repository:** all counts and row totals, the period spans per feed, the
cross-source pair measurement in §5, the cube extract shape, the search-index diff, and the
staleness of `ARCHITECTURE.md` line 20.
