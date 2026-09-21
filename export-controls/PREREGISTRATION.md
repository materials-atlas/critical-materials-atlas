# Did China's export controls bite? — pre-registration

Filed 2026-09-21, before any trade value for these goods was pulled. What was read to plan it: the
official announcements (dates and scope, listed below with their sources), the EU CN8 and US HTS10 code
lists (descriptions only), and two referee reviews of the draft in `DESIGN.md`. The draft, the reviews'
points and what changed are at the end.

## The question

China placed export controls on six groups of goods between 2023 and 2025. A control can bite in the
import records of a country that buys from China in three ways: **less comes from China, the price
rises, or less arrives in total.** It can also be diverted — China's share falls because material is
routed through a third country, while neither the price nor the total moves. The question is which of
these happened, control by control, in the EU's and the United States' own monthly import records.

## The controls (verified from the announcements)

| # | Control | Announced | In force | Source |
|---|---|---|---|---|
| C1 | Gallium and germanium | 3 Jul 2023 | 1 Aug 2023 | MOFCOM/GAC 2023 No. 23 |
| C2 | Graphite: natural flake and its products (incl. spherical), high-spec artificial | 20 Oct 2023 | 1 Dec 2023 | MOFCOM/GAC 2023 No. 39 |
| C3 | Ban in principle on gallium, germanium, antimony to the **US** | 3 Dec 2024 | 3 Dec 2024; suspended 9 Nov 2025 | MOFCOM 2024 No. 46; suspended by 2025 No. 72 |
| C4 | Seven medium/heavy rare earths, **incl. Sm-Co and Tb/Dy-containing NdFeB magnets** | 4 Apr 2025 | 4 Apr 2025 | MOFCOM/GAC 2025 No. 18 |
| C5 | Antimony | 15 Aug 2024 | 15 Sep 2024 | MOFCOM/GAC 2024 No. 33 |
| C6 | Bismuth metal (with tungsten, tellurium, molybdenum and indium compounds) | 4 Feb 2025 | 4 Feb 2025 | MOFCOM/GAC 2025 No. 10 |

The October 2025 expansions (MOFCOM 2025 Nos. 55-62) were suspended on 7 Nov 2025 (No. 70) and are
not tested.

## Goods and codes, locked now

| Control | Treated — EU CN8 | Treated — US HTS10 |
|---|---|---|
| C1, C3 | Ga 81129289; Ge 81129295 | Ga 8112921000; Ge 8112926000, 8112926500 |
| C2 | 25041000 (natural, powder or flakes) | 2504101000, 2504105000; 3801105010 (spherical artificial) |
| C4 magnets | 85051110 (metal magnets containing Nd, Pr, Dy or Sm; exists from 2023) | 8505110050 (Sm-Co), 8505110070 (NdFeB) |
| C4 rare earths | 28053031 (Gd, Tb, Dy metals), 28469060 (Gd, Tb, Dy compounds) | — (no clean US code) |
| C5 | 81101000, 81102000, 81109000, 26171000 | 8110100000, 8110200000, 8110900000 |
| C6 | 81061010, 81061090, 81069010, 81069090 | 8106100000, 8106900000 |

**Comparison goods, and why each is not treated.** Unwrought **magnesium** (EU 81041100, 81041900; US
8104110000, 8104190000) for the metal controls C1, C3, C5, C6: China dominates world supply and no
MOFCOM control found covers it, so it shares the "bought from China" exposure without the control.
**Talc and baryte** (EU 25262000, 25111000; US 2526*, 2511*) for graphite C2: bulk industrial minerals
China supplies heavily, uncontrolled. **Ferrite magnets** (EU 85051910; US 8505193000) for magnets C4:
China dominates them and they are not covered. **Light rare-earth compounds** (EU 28469040 lanthanum,
28461000 cerium) for the rare earths in C4: same heading, excluded from the April 2025 list. Indium and
bismuth are **not** comparisons: No. 10 of 2025 controls indium compounds and bismuth metal. The EU is
**not** a comparison for the US ban C3: it was treated by C1 in both markets and may absorb diversion.

## Data

EU: Eurostat Comext monthly bulk, imports of the EU27 from outside the EU, value (EUR) and kilograms,
the United Kingdom excluded on both sides in every month. US: Census general imports, HS10, value (USD)
and kilograms. January 2021 to July 2026, the last month fixed now. Months with missing or zero
kilograms are dropped for the price outcome, never imputed. Code changes inside the window (EU
artificial graphite 38011000 splitting in 2026) are summed back to the stem.

## Outcomes — one primary per control, the rest in order

1. **Primary: kilograms imported from China** of the treated goods, relative to the comparison.
2. Total kilograms imported, all origins, relative to the comparison.
3. Unit value of all imports of the treated goods (value per kg), relative to the comparison.

## Design

For each control and importer: monthly log outcomes for the treated and the comparison series,
series fixed effects and calendar-month-by-year effects (so common shocks cancel), and treatment
indicators for the anticipation window (announcement to entry into force) and for event-time bins of
0-3, 4-6 and 7-12 months after entry into force. The **post-period is the 7-12 bin where it exists**,
else the latest available bin, stated. Pre-period: the 24 months before announcement, **except** that
months inside an earlier control's post-period for the same goods are excluded (C3's pre-period is
therefore Aug 2023 to Nov 2024). Newey-West errors, six lags. For every estimate, the smallest effect
detectable at 80% power, computed from the same errors.

## Readings, decided now

For each control and importer, on the post-period:
- **Bit:** China kilograms fell by at least 30% relative to the comparison (log −0.36), with the 95%
  interval below zero, **and** either total kilograms fell by at least 20% or the unit value rose by at
  least 20%, each with its interval excluding zero.
- **Diverted:** China kilograms fell at least 30% with the interval below zero, but neither total
  kilograms nor unit value moved by the threshold.
- **No visible effect:** the China-kilograms interval excludes a 30% fall.
- **Untestable:** the smallest detectable effect on China kilograms exceeds 30%. Said per control;
  never reported as a null.

**Many tests.** Six controls, up to two importers each: the primary p-values are Holm-adjusted across
the family, and a reading of "bit" or "diverted" needs the adjusted p below 0.05.

## What this cannot say

Customs value is not a contract price; monthly unit values of small-volume goods are noisy; general
imports include goods re-exported; licences granted are not observed; material shipped ahead of a
control shows as anticipation; routing through a third country is inferred from the pattern, not seen.
Not causal beyond the comparison stated.

## Referee review of the draft, and what changed

Two independent language models reviewed `DESIGN.md` (committed before review). Changes:
1. The "bit" rule fired on diversion (share down with no supply loss): now a joint rule, with
   diversion its own reading.
2. Comparisons were weak or missing: indium dropped (controlled in 2025), EU dropped as the US-ban
   comparison (co-treated), graphite given one, rare-earth compounds split from magnets and given
   their own; magnesium chosen as uncontrolled and China-dominated.
3. One primary outcome per control, hierarchical, with a family-wise correction.
4. Timing: event-time bins, an anticipation window, and overlapping controls excluded from each
   other's pre-periods.
5. Measurement: codes and the last month locked, missing kilograms dropped rather than imputed,
   code changes summed to the stem.
6. Two more controls, verified in the announcements: antimony (C5) and bismuth (C6).

## Result - run 2026-09-21 (after deviations 1-10)

Run by `analysis.py`; every number is in `out/export_controls.json`. Post-period: months 7-12 after
entry into force. Rewritten after two independent language models and a fact-check reviewed the first
draft of this section (deviation 10); no estimate changed.

**As filed, no EU control reads "bit".** Five of the six EU controls read "untestable at a 30% fall"
and the magnets read "no visible effect". The filed rule checks power before the estimate, and the
monthly China-origin series are thin enough that the design could not reliably have seen a 30% fall.
**The US half of the study does not work** with the comparisons filed for it (deviations 3 and 7) and
has no reading; its numbers are in the output file and are not reported here.

### The estimates (EU, against the filed comparison)

China and total quantities are differences of the inverse hyperbolic sine of kilograms. They are not
percentages, and where a series approaches zero they are not log changes either (deviation 4). The unit
value is a true log difference, with its percentage.

| | control | China quantity | total quantity | unit value | reading as filed | corrected order (dev. 5, exploratory) |
|---|---|---|---|---|---|---|
| C1 | gallium and germanium | -0.40 [-0.83, +0.04] | -0.10 [-0.42, +0.23] | +0.78 [+0.42, +1.13] (+117%) | untestable at a 30% fall | untestable at a 30% fall |
| C2 | graphite | +0.00 [-0.32, +0.33] | -0.10 [-0.30, +0.11] | -0.04 [-0.19, +0.12] (-4%) | untestable at a 30% fall | no visible effect |
| C4 | rare-earth magnets | +0.25 [+0.16, +0.34] | +0.21 [+0.10, +0.32] | -0.00 [-0.09, +0.08] (-0%) | no visible effect | no visible effect |
| C4r | Gd, Tb, Dy metals and compounds | +0.06 [-0.97, +1.08] | -0.80 [-1.15, -0.44] | +1.09 [+0.57, +1.61] (+197%) | untestable at a 30% fall | untestable at a 30% fall |
| C5 | antimony | -4.04 [-4.93, -3.15] | +0.20 [+0.05, +0.36] | +1.83 [+1.67, +2.00] (+526%) | untestable at a 30% fall | bit |
| C6 | bismuth | -0.94 [-1.29, -0.59] | -0.41 [-0.78, -0.03] | +1.31 [+1.06, +1.56] (+270%) | untestable at a 30% fall | bit |

### What the raw series show (EU, before and after)

Pre-period mean against months 7-12, per month; unit value in euro per kilogram, all origins.

| | control | from China, t | all origins, t | unit value, treated | unit value, comparison |
|---|---|---|---|---|---|
| C1 | gallium and germanium | 4.8 → 3.5 | 5.3 → 4.3 | 494.3 → 702.0 (×1.4) | 4.68 → 2.90 (×0.62) |
| C2 | graphite | 2495.9 → 2859.3 | 8359.5 → 7586.3 | 1.4 → 1.3 (×0.9) | 0.26 → 0.25 (×0.98) |
| C4 | rare-earth magnets | 1532.1 → 2009.3 | 1649.1 → 2127.3 | 41.3 → 37.4 (×0.9) | 4.50 → 4.06 (×0.90) |
| C4r | Gd, Tb, Dy metals and compounds | 5.6 → 2.3 | 22.4 → 11.5 | 124.5 → 400.0 (×3.2) | 2.26 → 2.66 (×1.18) |
| C5 | antimony | 190.3 → 8.4 | 1663.7 → 1718.8 | 11.4 → 47.0 (×4.1) | 3.63 → 2.35 (×0.65) |
| C6 | bismuth | 131.5 → 56.9 | 144.8 → 102.3 | 9.9 → 25.5 (×2.6) | 3.09 → 2.28 (×0.74) |

### Reading

- **Antimony and bismuth are consistent with a bite, as an exploratory reading only.** Under the
  reading order corrected after the data (deviation 5) both read "bit", with Holm-adjusted p below 0.05
  over any family of the filed size. The raw series are unambiguous about what happened: EU imports of
  antimony from China fell from 190 to 8.4 tonnes a month and the unit value of all antimony imports
  rose 4.1-fold; bismuth from China fell from 132 to 57 tonnes a month and its unit value rose
  2.6-fold. The larger multiples in the estimates (about six-fold and 3.7-fold) are relative to
  magnesium, whose own unit value fell over the same months. **Antimony was not a supply shortfall:**
  total EU antimony imports did not fall (other origins replaced China), so its "bit" rests on price.
  Total bismuth imports did fall.
- **Rare-earth magnets show no visible fall in China-origin imports** by months 7-12, as filed;
  **graphite** is untestable as filed and shows no visible fall only under the exploratory order. The
  EU graphite code is natural graphite only (25041000); the synthetic and spherical graphite the control
  also covers is not in the locked codes, so this says nothing about them. Magnet imports from China
  rose relative to ferrite magnets; that rules out a 30% fall relative to ferrite, not any effect.
- **Gallium and germanium, and the heavy rare earths, are untestable.** The heavy rare earths' secondary
  outcomes did move: total imports fell and the unit value rose roughly three-fold; with China-origin
  untestable, that is a price and volume move, not a bite attributed to China-origin supply.

### What limits this

Magnesium, the comparison for the metal controls, is itself bought almost entirely from China and its
EU unit value rose from about 2 euro per kilogram in early 2021 to above 6 in 2022 before falling back,
inside the pre-periods; every unit-value estimate against it carries that slide. Talc and baryte are coarse
comparisons for graphite; ferrite magnets are the closest, and a switch toward ferrite would move the
comparison. These are differences against coarse, uncontrolled, China-exposed goods, not causal effects.

## Deviations log

Every change made after this filing goes here, dated, with its reason.
1. **2026-09-21, before the first run - quantities in inverse hyperbolic sine, not logs.** The filing
   says monthly log outcomes. A month with no imports from China at all is the strongest possible bite,
   and a log would drop it. The two quantity outcomes therefore use asinh(kg), which behaves like a log
   for large values and keeps zeros; the unit-value outcome stays in logs, with months of missing or
   zero kilograms dropped as filed. Decided and committed before any estimate.
2. **2026-09-21, after the first run - the US artificial-graphite code split was not summed to its
   stem.** US 3801105000 splits into 3801105010 (spherical) and 3801105090 inside the window. The
   filing's rule sums code changes back to the stem; the first run used only 3801105010, which starts
   mid-window and faked a collapse and a price jump. The whole of 38011050 is now used throughout. An
   implementation error against the filed rule, not a change of design.
3. **2026-09-21, after the first run - US magnesium cannot be the comparison for the China-origin
   outcome.** US imports of magnesium from China fell by about 90% across the window (2.6 Mt in 2021,
   0.2 Mt in 2025), so any treated good's China-origin imports look like they rose against it (the
   first run printed +626,203% for antimony). The China-origin outcome is therefore reported as not
   interpretable wherever the US comparison is magnesium (C1, C3, C5, C6 in the US). No substitute
   comparison is chosen after seeing the data. Total kilograms and unit values use all origins, where
   US magnesium imports are stable, and are kept. In the EU, magnesium comes almost entirely from
   China throughout, and the comparison stands.
4. **2026-09-21, after the first run - no percentages for the quantity outcomes.** A percentage of an
   inverse-hyperbolic-sine difference is not meaningful where a series touches zero; quantities are
   reported in log points. The unit value, a true log, keeps its percentage.
5. **2026-09-21, after the first run - the reading rule's order was wrong.** As filed, "untestable"
   is checked first, so an estimate whose whole interval lies far beyond the threshold (a 98% fall)
   reads "untestable at a 30% fall" because the design could not reliably have seen a 30% fall.
   The reading as filed is still reported for every control. Beside it, labelled as post-hoc, a
   reading with the expected order: an interval that clears the threshold (with Holm-adjusted p below
   0.05) decides the reading whatever the power; only otherwise does low power make it untestable.
6. **2026-09-21, after the second run - US quantities in tonnes were dropped.** Several US codes
   (baryte, crushed talc) report quantity in metric tonnes; the code read only kilograms and silently
   left them out. Tonnes are now converted to kilograms. An implementation error.
7. **2026-09-21, after the second run - two more US comparisons fail on the data.** A screen of every
   series for breaks in recorded quantity and unit value found: US uncrushed talc (2526100000) jumping
   six-fold in recorded kilograms in 2023 with its value flat, a recording change, which breaks the US
   graphite comparison; and US ferrite magnets (8505193000) recorded only as a count of pieces, never
   in kilograms, so the US magnets comparison has no quantity at all. Both US comparisons are declared
   not interpretable for every outcome. With deviation 3, **the US half of this study does not work with
   the comparisons filed for it**; no replacement comparisons are chosen after seeing the data. Every
   EU series passes the same screen (the 2025 unit-value jumps for antimony and bismuth are the price
   rises that followed the controls, with quantities steady).

8. **2026-09-21, after the council review of the results - raw levels added; empty anticipation column
   dropped.** The output now carries, for every control, the pre-period and months 7-12 means of tonnes
   from China, tonnes from all origins and the unit value, for treated and comparison goods, so that no
   multiple in the text rests on an asinh gap. Where entry into force is the month of announcement
   (C4, C6) the anticipation column was all zeros and was left to the pseudo-inverse; it is now dropped.
   No estimate or reading changed (checked against the previous output).
9. **2026-09-21 - the Holm family changed and is stated.** The filing adjusts across "six controls, up
   to two importers each". After deviations 3 and 7 no US China-origin estimate exists, so the adjustment
   runs over the six EU tests. Antimony and bismuth have unadjusted p below 0.0001 and would survive
   adjustment over all twelve.
10. **2026-09-21 - result wording rewritten after review.** Two independent language models and a
   fact-check reviewed the first draft of the result section. Accepted: the filed reading leads and the
   corrected order is exploratory; asinh quantities are not described as percentages or log points;
   raw tonnes and unit values are shown; unit-value multiples are given raw, with the magnesium-relative
   figure named as such; antimony's total imports rose, so its reading rests on price; EU graphite is
   natural graphite only; the heavy rare earths' secondary outcomes are reported; US numbers are removed
   from the result table. Deviation 7's "quantities steady" meant no break in recording, not no change in
   supply. The first draft also gave the gallium and germanium unit-value rise as 118%; it is 117%.
   One inconsistency in the filing, noted and without effect: C3's pre-period (August 2023 to November
   2024) contains C1's post-period, which the overlap rule meant to exclude; the US rows carry no reading.
