# comtrade-reconcile

[![validate](https://github.com/materials-atlas/critical-materials-atlas/actions/workflows/engine-validate.yml/badge.svg)](https://github.com/materials-atlas/critical-materials-atlas/actions/workflows/engine-validate.yml)

**A share-faithful reconstruction of bilateral trade from raw UN Comtrade (BACI-style) — plus a nowcast
for the recent years BACI has not released yet.**

> Scope claim, stated precisely: this reproduces BACI's **shares, ranks and concentration** (validated
> below), *not* its exact levels — current Comtrade runs ~1.5–1.8× above BACI's published values (the
> "level offset", diagnosed below). It is Comtrade-mirror reconciliation in BACI's spirit, not a
> bit-for-bit BACI replica.

CEPII's [BACI](http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37) is the standard "clean"
bilateral trade dataset, but it lags ~1.5 years. This is a small, self-contained pipeline that
reconstructs the same thing from **raw UN Comtrade** — matching the two mirror reports of every flow,
correcting CIF/FOB, weighting reporters by reliability, and reconciling — then **validates the result
against official BACI** and uses it to nowcast the missing recent years.

Built as the trade engine behind the [critical-materials-atlas](https://criticalmaterialsatlas.org/)
(where it powers the 2025–2026 layers), but it is general — it works for any HS6 codes. Method follows
**Gaulier & Zignago (2010)**, *BACI: International Trade Database at the Product-Level*, CEPII WP 2010-23.

📄 Full technical note (method, validation, nowcast, pre-registration, origin-gap finding):
[HTML](https://criticalmaterialsatlas.org/technical-note.html) ·
[PDF](https://criticalmaterialsatlas.org/technical-note.pdf).

## The problem

Every flow *i → j* is reported twice: the exporter declares it **FOB**, the importer declares its mirror
**CIF** (with freight + insurance). The two rarely agree — valuation, misreporting, timing, one-sided
reporting. A single reconciled value has to be recovered from these noisy double reports.

## The method (`reconcile.py`)

1. **Match mirrors** — pair `x_fob` (exporter) and `m_cif` (importer) for each (i, j, HS6).
2. **CIF → FOB** — deflate imports to an FOB basis. *Finding:* the gravity regression BACI uses to
   estimate CIF rates is **not identifiable on a narrow product slice** (R² ≈ 0.01 on ~31 codes — at HS6
   the M/X ratio is dominated by valuation noise, not transport). BACI estimates it on the full
   ~5,000-product universe; here we fall back to a robust per-product median markup, bounded to plausible
   freight (2%–30%). An honest negative result, kept rather than hidden.
3. **Reliability weights** — each reporter's quality from a **variance-components** decomposition of the
   mirror discrepancy: E[(ln x_fob − ln m_fob)²] = var_i + var_j (OLS on reporter dummies).
4. **Reconcile** — two-sided flows → **inverse-variance average on logs**; one-sided flows → the single
   report (FOB-adjusted if it is the importer's).

Output: `reconcile/recon_<year>.csv` with columns `i, j, cmd, value` plus diagnostics to stdout.

## Validation against official BACI (`validate.py`)

Validated on **what matters downstream — exporter- and importer-side shares and concentration**, not just
a global level correlation. As reported in `results/` for the settled year 2022 and the still-settling
2024, the reconstruction reproduces BACI's top-1 exporters, top-3 overlap, share MAE and HHI closely
(exporter top-1 **25/30** with share MAE ~3.5% in 2024; **22/30** with ~3.9% in 2022), while the level
runs a near-constant multiple above BACI. Both years reproduce **key-free from committed fixtures** —
`ATLAS_ROOT=fixtures python reconcile.py <year> && python validate.py <year>` — and the CI runs both on
every push. Validating a *new* year needs only its raw Comtrade CSV in `raw/comtrade/` (already pulled
when the nowcast for that year was built) plus BACI having released it; neither step needs an extra pull.

### The level offset — diagnosed honestly

Reconciled totals run **~1.8× BACI for 2024 and ~1.5× for the settled year 2022**. A flow-level
diagnostic shows it is **not a method artefact**: on flows where both raw Comtrade reports and BACI exist,
the raw exporter report is already ~1.94× BACI and the importer ~1.81×, while the reconciled value (~1.67×)
falls *between and below* the two raw reports. The engine faithfully reconciles what Comtrade reports;
**current Comtrade simply runs above BACI's published values.** Because it is a near-constant multiple, it
**cancels out of shares** — which is what is validated. For the nowcast years, levels are calibrated back
to BACI's scale per material; shares are untouched.

## Nowcasts

- **2025** (`build_recon_flows.py`) — full reconciliation of partial 2025 Comtrade, level-calibrated
  per material to BACI 2024, emitted to the atlas `flows_2025.json` schema. Provisional.
- **2026** (`build_2026_nowcast.py`) — only ~Q1 monthly Comtrade exists, so 2025's reconciled structure
  is carried forward and scaled per material by reporter-matched Q1 export momentum, optionally blended
  (geometric mean) with the World Bank Pink Sheet price change from `pink_momentum.json`. Shares stay at
  2025; only levels tilt. Directional, not bilateral.

## Out-of-sample evaluation & pre-registration

- `backtest.py` — tests the nowcast's core assumption (last year's shares predict this year's) on the
  measured 2018–2024 reconciled series: for each material and consecutive year pair, score year T-1's
  shares against realised year T. Reports year-over-year top-exporter persistence, share MAE, and the
  P50/P90 uncertainty bands used for the nowcast. Pure stdlib, no key, no network. Writes
  `results/backtest.json`.
- `findings.py` — computes the atlas's headline **origin-gap** finding: per material, the gap between the
  top exporter's trade share and that country's mine share (USGS reference), aggregated into a
  "refiner-illusion league table". Writes `results/findings.json`.
- [`PREREGISTRATION.md`](PREREGISTRATION.md) locks, **before BACI 2025 exists**, how the frozen 2025
  nowcast will be scored when it does (`python validate.py 2025`), with numeric thresholds — so the test
  is genuinely out-of-sample and the result will be published pass or fail.

## Quick start — reproduce end-to-end, no key

Runs on a fresh clone with **no API key**. Raw UN Comtrade for 2024 is committed (gzipped, columns
trimmed, ~0.9 MB) under [`fixtures/raw/`](fixtures/raw/), so the reconciliation **regenerates from raw**
and is then scored against official BACI — only the initial network pull (`pull_comtrade.py`) needs a key.
Pure Python; cross-platform (paths use `os.path.join`; run on Linux CI and Windows).

```bash
pip install -r requirements.txt
ATLAS_ROOT=fixtures python reconcile.py 2024   # raw Comtrade fixture -> reconcile/recon_2024.csv (the engine)
ATLAS_ROOT=fixtures python validate.py 2024    # regenerated recon vs official BACI 2024
python backtest.py                             # out-of-sample persistence bands  -> results/backtest.json
python findings.py                             # the origin-gap finding           -> results/findings.json
```

On **Windows PowerShell**, set the env var separately:

```powershell
pip install -r requirements.txt
$env:ATLAS_ROOT = 'fixtures'
python reconcile.py 2024 ; python validate.py 2024
python backtest.py ; python findings.py
```

The `reconcile.py → validate.py` chain above is **exactly what CI runs on every push** (badge above), so
the green badge proves the code *regenerates* the reconciliation from raw and that it matches BACI — not
merely that a pre-committed file does.

## Refresh from live Comtrade (needs a key + the atlas data tree)

```bash
export ATLAS_ROOT=/path/to/critical-materials-atlas   # provides out/data.json, raw/baci/country_codes…
COMTRADE_KEY=<key> python pull_comtrade.py 2024        # raw bilateral pull (one call per code×flow)
python reconcile.py 2024                               # -> reconcile/recon_2024.csv
python validate.py 2024                                # vs BACI (results/ has saved output)
```

`COMTRADE_KEY` is read from the environment — never hardcode or commit it.

## Data sources (all public)

- **UN Comtrade API** — raw bilateral trade, both flows (`pull_comtrade.py`, `build_2026_nowcast.py`).
- **CEPII BACI** — the validation reference, plus the `country_codes` M49 ↔ ISO crosswalk.
- **CEPII `dist_cepii`** — gravity geography (distance, contiguity); kept for diagnostics only.
- **World Bank Pink Sheet** — commodity prices, for the optional 2026 price overlay.
- **USGS reference shares** — mine-production shares consumed by `findings.py` (via the atlas `data.json`).

Raw downloads are gitignored; `fixtures/` holds a committed slice for no-key reproduction and `results/`
holds the committed validation and findings output.

## Project structure

```text
.
├── pull_comtrade.py        ← raw UN Comtrade pull (needs COMTRADE_KEY)
├── reconcile.py            ← the reconciliation engine -> reconcile/recon_<year>.csv
├── validate.py             ← recon vs official BACI (exporter/importer shares, HHI)
├── build_recon_flows.py    ← reconciled CSV -> atlas flows_<year>.json (2025 nowcast)
├── build_2026_nowcast.py   ← directional 2026 nowcast from Q1 momentum (+ Pink Sheet)
├── backtest.py             ← out-of-sample persistence backtest -> results/backtest.json
├── findings.py             ← origin-gap / refiner-illusion table -> results/findings.json
├── pink_momentum.json      ← per-material price-momentum factors for the 2026 overlay
├── PREREGISTRATION.md       ← locked-in-advance scoring plan for the 2025 nowcast
├── requirements.txt
├── fixtures/               ← no-key reproduction slice
│   ├── raw/comtrade/comtrade_2024.csv.gz
│   ├── raw/baci/country_codes_V202601.csv
│   ├── reconcile/{baci_2024.csv, recon_2024.csv}
│   └── out/{data.json, flows_2018..2024.json}
└── results/                ← committed output (backtest.json, findings.json, validation_*.txt)
```

Paths are resolved under `ATLAS_ROOT` (default `.`); the fixtures tree mirrors the layout the atlas
provides at `out/`, `raw/` and `reconcile/`.

## Tech stack

Python 3 — `pandas`, `numpy`, `statsmodels` (variance-components OLS), `requests` (Comtrade API),
`openpyxl` / `xlrd` (CEPII Excel). `backtest.py` and `findings.py` are pure standard library. CI runs the
reconcile → validate chain on every push.

## Status

Working and CI-validated. The 2024 reconstruction is validated against official BACI; the 2025 nowcast is
frozen and pre-registered, awaiting BACI 2025 (expected late 2026 / 2027) for out-of-sample scoring; the
2026 nowcast is directional only. Independent work, public data only.
