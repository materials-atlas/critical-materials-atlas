# Amendment D: world trade after 2024, from importers' monthly reports (descriptive)

Filed 2026-09-19, before any value in the new data was pulled. Only the list of countries that
reported monthly to UN Comtrade in 2025 (for other products, already on disk) was read, to plan it.
This amendment extends `PREREGISTRATION.md`, `AMENDMENT_EU_2026.md` and `AMENDMENT_US_2026.md`.

## Why, and why it is descriptive

The world record (CEPII BACI) ends in 2024. UN Comtrade publishes countries' own monthly customs
reports, which run into 2026. The filed test cannot be extended with them: it compares 2021-2026 with
2012-2020, and a series that starts in 2024 has no baseline, while splicing it onto BACI would change
the source at the treatment boundary. So nothing here is a test. It asks two descriptive questions on
one consistent basis, 2024 against 2025 and January-June 2026.

## Data

- **UN Comtrade, monthly, HS 6-digit, imports as reported by the importer**, January 2024 to the
  latest month available, totals only (all modes of transport, all customs procedures, no second
  partner). Pulled by `ai-buildout/fetch_comtrade_ai.py`.
- **A fixed panel.** Only importers that report every month compared are used, so a country that has
  not yet filed cannot look like a fall in trade. Its size is stated as a share of the same lines'
  2024 world imports in BACI.
- Raw Comtrade records are not redistributed (the atlas's licence policy); only derived totals and
  shares are written to `out/`.

## The two questions

1. **Did the concentration of grain-oriented electrical steel (7225.11 + 7226.11) continue?** The
   share of the panel's imports, by value, supplied by China, by Russia, by Japan and by the three
   largest suppliers, in 2024, 2025 and January-June 2026. Reading, decided now: this is described,
   not tested; if China's 2025 share is higher than its 2024 share on this basis, the note says the
   concentration continued into 2025 "as reported by importers"; if not, it says it did not.
2. **Did transformers keep rising faster than the comparison goods?** For the panel, the change in
   import value and in value per kilogram from 2024 to 2025, for transformers (8504.21-.23), for the
   filed heavy machinery, and for motors, pumps and compressors, each summed over its lines. Reported
   side by side, with no interval and no claim of a transformer-specific effect: two years of one
   source cannot carry one.

## What this cannot say

Imports as reported by importers are valued CIF, BACI reconciles to FOB, so levels are not comparable
with the rest of the note and are not compared. China, India and Taiwan do not report monthly in the
data on disk, so their imports are missing from the panel; as suppliers they are visible through their
partners. Not causal. The latest months are first releases and will be revised.

## Deviations log

Every change made after this filing goes here, dated, with its reason.
