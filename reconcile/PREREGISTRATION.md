# Pre-registration — the 2025 nowcast vs official BACI

**Filed 2026-06-26, before CEPII BACI for 2025 exists.** This document commits, in advance, to how the
provisional **2025\*** nowcast (`out/flows_2025.json`, built by `build_recon_flows.py` from partial UN
Comtrade) will be scored once the official reconciliation is published — so the test is genuinely
out-of-sample and cannot be retrofitted.

## The instrument

CEPII releases BACI roughly a year and a half in arrears; the release covering trade-year **2025** is
anticipated in **late 2026 / 2027**. When it lands:

```
# drop the official 2025 BACI into raw/baci/, build the reference flows, then:
python validate.py 2025      # same script, same metrics as the 2024 validation
```

`validate.py` compares our `flows_2025.json` (frozen now, in git history at this commit) against the
official BACI 2025 on **shares**, both sides of the market, with exactly the metrics already reported for
2024: top-1 exporter hit count, share MAE, HHI correlation; and the importer-side equivalents.

## Pre-registered expectations (the bet)

Anchored to two things measured *before* the fact: the **2024 validation** (exporter top-1 25/30, share
MAE 3.5%, HHI corr 0.92) and the **out-of-sample persistence backtest** over 2018–2024
(`backtest.py` → 85% year-over-year top-exporter persistence; a leader's annual share move of P50 3.5pp,
P90 8.7pp). We commit to these thresholds for the 2025 comparison:

| Metric (exporter side) | Pre-registered threshold | Basis |
|---|---|---|
| Top-1 exporter correct | **≥ 22 / 30** (~73%) | scored on the 30 validatable materials (gallium/germanium/hafnium share one HS6); below 2024's 25/30 because 2025 uses *partial* Comtrade |
| Share MAE | **≤ 5.0 pp** | 2024 was 3.5pp; the P90 annual drift is 8.7pp, so a one-year-ahead MAE under 5pp is a real claim |
| HHI correlation | **≥ 0.88** | 2024 was 0.92 |
| Leader within ±8.7pp of truth | **≥ 90% of materials** | the backtest P90 band |

We expect the **least-predictable** materials from the backtest (arsenic, beryllium, hafnium, germanium,
gallium, fluorspar) and any leaning on non-reporting producers (bauxite/Guinea) to drive most of the
misses; the **most-predictable** (magnets, coking coal, bauxite-by-value, manganese, boron, niobium)
should be near-exact.

## Commitments

1. **No edits to `flows_2025.json` after today.** Its content is fixed by this commit's history.
2. **Publish the result either way.** When BACI 2025 is released, the `validate.py 2025` output is
   committed to `results/` and linked from the method note — pass *or* fail. A miss is a finding, not a
   thing to hide.
3. **Same for 2026\*\*** once BACI 2026 exists, with the caveat that 2026 is only a *directional* tilt
   (shares held at 2025), so it is scored on level/direction, not structure.

The point of the atlas is not that the nowcast is right; it is that the nowcast is **falsifiable on a
fixed date by a one-line command**, and the bet is written down here first.
