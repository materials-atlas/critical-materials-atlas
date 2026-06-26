# A BACI-faithful reconciliation of UN Comtrade — method note

This folder is a self-contained pipeline that reconstructs **complete bilateral trade** from raw UN
Comtrade for years CEPII's [BACI](http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37)
has not yet released, and validates the result against BACI where the two overlap. It exists because
BACI lags ~1.5 years; this lets the atlas nowcast 2025–2026. The method follows Gaulier & Zignago
(2010, *BACI: International Trade Database at the Product-Level*, CEPII WP 2010-23).

## The problem
Every trade flow *i → j* is reported twice: the exporter declares it (value **FOB**), the importer
declares its mirror (value **CIF**, i.e. including freight + insurance). The two rarely agree —
different valuation, misreporting, timing, one-sided reporting. A single reconciled value per
(exporter, importer, product) has to be recovered from these noisy double reports.

## The method (`reconcile.py`)
1. **Match mirrors.** For each (i, j, HS6) pair the exporter's FOB report `x_fob` and the importer's
   CIF report `m_cif`.
2. **CIF→FOB.** Deflate every import to an FOB basis. *Finding:* the gravity regression BACI uses to
   estimate CIF rates (distance, contiguity, unit value, product) is **not identifiable on our 31-code
   slice** — R² ≈ 0.01, because at HS6 the M/X ratio is dominated by valuation noise, not transport.
   BACI estimates it on the full ~5,000-product universe; we fall back to a **robust per-product median
   markup** (bounded to plausible freight). Honest negative result, documented rather than hidden.
3. **Reliability weights.** Each reporter's quality is estimated from a **variance-components**
   decomposition of the mirror discrepancy: E[(ln x_fob − ln m_fob)²] = var_i + var_j, fit by OLS on
   reporter dummies. Reporters whose declarations are internally consistent get lower variance.
4. **Reconcile.** Two-sided flows → **inverse-variance average on logs** (weight ∝ 1/var). One-sided
   flows → the single report (FOB-adjusted if it is the importer's).

## Validation against official BACI 2024 (`validate.py`)
Validated on **what the atlas displays — shares and concentration**, not just a global correlation:

| Metric | Result |
|---|---|
| Top-1 exporter match | **25 / 30** materials |
| Top-3 exporter overlap (mean) | **2.57 / 3** |
| Exporter-**share** MAE | **3.5%** (median 3.2%) |
| HHI (concentration) correlation | **0.920** |
| Flow-level log-value correlation | 0.975 (21.7k flows) |
| Level ratio (ours / BACI) | **~1.8×** — a known, consistent offset |

The shares the atlas shows are reproduced to within ~3 points and the concentration ranking is
preserved. The **level offset** is real and disclosed: current Comtrade has absorbed revisions and
late filers since BACI's early-2025 snapshot, so absolute values run high. Because it is a near-constant
multiple it cancels out of shares; for the nowcast years it is calibrated back to BACI's 2024 scale per
material. It does **not** affect who-trades-with-whom.

## Nowcasts built on this
- **2025** (`build_recon_flows.py`) — full reconciliation of partial 2025 Comtrade (~half of countries
  filed), level-calibrated to BACI. Provisional.
- **2026** (`build_2026_nowcast.py`) — only ~Q1 monthly Comtrade exists, so 2025's reconciled structure
  is carried forward and scaled per material by reporter-matched Q1 export momentum blended with the
  World Bank Pink Sheet price change. **Shares stay at 2025; only levels tilt.** Directional, not
  bilateral — a trend signal.

## Reproduce
```bash
# Comtrade key via env var only — never hardcode/commit it
COMTRADE_KEY=<key> python pull_comtrade.py 2024       # raw bilateral pull (62 calls)
python reconcile.py 2024                              # -> recon_2024.csv
python validate.py 2024                               # vs baci_2024.csv (extracted from the BACI zip)
COMTRADE_KEY=<key> python build_recon_flows.py 2025   # -> out/flows_2025.json (provisional)
COMTRADE_KEY=<key> python build_2026_nowcast.py       # -> out/flows_2026.json (directional)
```
Inputs (all public): UN Comtrade API; CEPII `dist_cepii` (gravity); CEPII BACI `country_codes` (M49 ↔
ISO); World Bank Pink Sheet (commodity prices). Raw downloads are gitignored; the scripts and outputs
are committed.
