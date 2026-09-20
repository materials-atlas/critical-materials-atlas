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

## Result - run 2026-09-20

Run by `ai-buildout/comtrade_extend.py`; every number is in `out/buildout_comtrade.json`. The pull
covers January 2024 to 2026-06. **The panel is 83 importers** - those that filed every
month of 2024 and of 2025 - and it holds 86% of 2024 world imports of the steel lines and
83% of the transformer lines in BACI. China, India and Taiwan do not file every month and are
therefore outside the panel as importers; as suppliers they are counted, because the panel's members
report where their imports came from.

**Question 1: the concentration continued into 2025.** Of the panel's imports of grain-oriented
electrical steel, China supplied 36% in 2024 and 39% in 2025; the three largest suppliers
went from 70% to 72% (China 39%, Japan 26%, Germany 6% in 2025). Russia went from
5.1% to 5.0%, Japan from 25.8% to 26.4%. The filed reading applies: the concentration
continued into 2025, as reported by importers.

**The first half of 2026 does not extend it.** On the panel that filed every month of both half-years
(52 importers, 57% of 2024 world imports), China's share was 29% in January-June 2025 and
28% in January-June 2026, with Japan first (Japan 29%, China 28%, the United States 11%). That panel is much
thinner than the annual one and its months are first releases, so this is recorded, not read as a turn.

**Question 2: transformers rose faster than both comparison groups in 2025.** Change from 2024 to
2025, on the panel that filed every month of both years:

| Panel imports, 2024 to 2025 | value | value per kg | importers | coverage of 2024 world imports |
|---|---|---|---|---|
| Transformers (8504.21-.23) | +28.5% | +5.5% | 83 | 83% |
| The filed heavy machinery | +3.6% | -4.1% | 83 | 74% |
| Motors, pumps, compressors | +7.0% | +2.8% | 83 | 79% |

Transformer import value rose +28.5% against +3.6% for the filed heavy machinery and
+7.0% for motors, pumps and compressors, and transformers' value per kilogram rose
+5.5% while the heavy machinery's fell 4.1% and the motors' rose 2.8%. This is one
year against one year, with no flow-level design, no interval and no baseline: it is consistent with
the note's earlier gap continuing into 2025, and it cannot establish that, exactly as this amendment
said before the data were pulled.

**Not part of either question, recorded because the same pull answers it:** memory chips (8542.32)
were up 224% in January-June 2026 against the same months of 2025 on a 34% panel, which is the
same movement the EU's and the United States' own records show.

## Deviations log

Every change made after this filing goes here, dated, with its reason.

1. **2026-09-20 - the half-year panel is much thinner than the annual one.** The filing said the panel
   would be importers that reported every month compared, and it is; it did not anticipate how many
   countries have not yet filed 2026. The annual comparison rests on 83 importers and 86% of world
   imports, the half-year one on 52 and 57%. Both are reported, with their sizes; the half-year
   result is not read as a change of direction.
