# A monthly BACI

Started 10 Nov 2026. CEPII's BACI (Gaulier & Zignago, WP 2010-23) reconciles the exporter's and
the importer's declaration of every bilateral flow once a year, with a lag: V202601 stops at
2024. The UN bulk corpus holds the same raw declarations by month up to the last published
period, so the same three steps can run per month and reach two years further. The engine is
`monthly_baci.py`; `validate_monthly_baci.py` sums its months to years and compares them with
BACI's own numbers where the two overlap, which is the test of the whole thing.

## The three steps, as implemented

1. **Freight.** Only the total line of a declaration is a flow (customs `C00`, transport `0`,
   second partner `0`; flows `M` and `X`; partner "World" dropped). The importer's CIF value is
   divided by a route coefficient: CEPII's own published gravity shape (2008, column 4) on
   distance, contiguity, language, colonial tie, landlocked status and the product's world unit
   value that month, anchored and capped as in `pipeline/reconcile.py`.
2. **Reliability.** On the flows both sides declared, d = ln FOB_exporter - ln FOB_importer,
   trimmed to a ratio band of 0.2-5. Level biases out by alternating robust median centering per
   reporter and role; then E[d^2] = v_exporter + v_importer by Gauss-Seidel on winsorized
   squares, shrunk toward the month's global variance. One variance per reporter, role and month.
3. **Reconciliation.** Exporter weight w = v_importer / (v_exporter + v_importer); the value is
   the weighted arithmetic mean of the two FOB values, as BACI publishes. One side only: that
   side. Quantities with the same weights.

## First validation: the 54-code slice against BACI, 2020-2024

| year | flows in both | BACI value covered | median ours/BACI | within 10% | within 25% | corr of logs | total ours/BACI |
|---|---|---|---|---|---|---|---|
| 2020 | 34,648 | 98.2% | 1.000 | 62.6% | 74.3% | 0.984 | 1.034 |
| 2021 | 36,798 | 98.5% | 1.000 | 64.5% | 75.2% | 0.987 | 1.065 |
| 2022 | 38,180 | 98.5% | 1.000 | 62.7% | 75.0% | 0.987 | 1.061 |
| 2023 | 37,423 | 98.4% | 1.000 | 64.1% | 74.9% | 0.987 | 1.019 |
| 2024 | 35,780 | 99.1% | 1.000 | 65.7% | 75.0% | 0.978 | 1.029 |

2019 holds only Aug-Dec in the corpus and is not comparable. Where the two depart, and why:

- **Timing across month ends is the real problem.** A flow declared by the exporter in some
  months and by the importer in others comes out 30% above BACI in the year. A shipment the
  exporter books in month t and the importer in t+1 is two flows to a per-month reconciliation
  and one to a yearly one. Flows with both sides every month sit at 1.025, one-sided flows at
  0.98-1.00; the excess is concentrated in flows with 4-11 months of data (1.13-1.20).
- **Importer-only flows are 5.5% below BACI** (median 0.945): our freight coefficient is
  higher than what BACI strips. The anchor was set on 54 products; the universe will say
  whether it, or BACI's data-estimated rate, is the right level.
- **Monthly reporting misses some exporters altogether** (Congo, Russia, Australia, Zambia,
  Guinea...), 1-2% of BACI's value: countries that report yearly or not at all, for which BACI
  works from partners' declarations only. The yearly series now being pulled closes part of it;
  the rest is a question of which partners publish monthly.

## Open design decision (for the owner)

How to treat the month-end timing. The candidates: (a) reconcile on a rolling three-month
window; (b) reconcile the year as BACI does and distribute it over months by the two sides'
monthly profiles, with a trailing twelve months for the current year; (c) match each shipment
across t-1..t+1 before reconciling. (b) is BACI-consistent by construction and the simplest to
validate; (a) keeps the monthly engine but blurs turning points; (c) is the most faithful and
the most work.
