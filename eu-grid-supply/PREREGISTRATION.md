# Which parts of Europe's grid come from China, on a supply basis? — pre-registration

Filed 2026-09-21, before any production or trade value for the new components was read. What was read
to plan it: the Prodcom product list (labels only), the EU CN8 code list, the transformer note's
amendment E (which established the method), and two referee reviews of `DESIGN.md`.

## Why

The transformer note found China supplied 34% of the EU's transformer imports in 2024 but 9.1% of its
supply, and 52% of its imports of grain-oriented electrical steel but 24% of supply. This applies the
same measure to the rest of the grid, component by component.

## Components and codes, locked now

Only lines that are grid equipment by their own description; low-voltage and consumer lines are left
out so that phone chargers and household fuses are not read as grid dependence.

| Component | Prodcom | CN8 |
|---|---|---|
| Liquid-dielectric transformers | 27114120, 27114150, 27114180 | 85042100, 85042210, 85042290, 85042300 |
| Grain-oriented electrical steel | 24105310, 24105410 | 72251100, 72261100 |
| Insulated conductors above 1,000 V | 27321400 | 85446010, 85446090 |
| Switchgear above 1,000 V | 27121010, 27121020, 27121030, 27121041, 27121090 | 85351000, 85352100, 85352900, 85353010, 85353090, 85354000, 85359000 |
| Switchboards above 1,000 V | 27123203, 27123205 | 85372091, 85372099 |
| Inverters above 7.5 kVA | 27904155 | 85044086 (to 2025) |
| Electricity meters | 26516370 | 90283011, 90283019, 90283090 |

The Prodcom-to-CN pairs are matched on the product descriptions, not on Eurostat's correspondence
table, and are stated as such. Meters include household smart meters, which are part of the
distribution grid; the table labels them.

## The measure

apparent supply = EU27 sold production (Prodcom DS-059358, PRODVAL, EU27_2020) + imports from
outside the EU − exports to outside the EU (Comext, the United Kingdom excluded on both sides in every
year). By value. **Headline year 2024**; 2019-2023 shown as context, and no trend is read from them
(Covid, the energy shock and the war in Ukraine all sit inside those years). Components are never
summed: transformers contain electrical steel.

**Suppressed production cells.** A missing Prodcom value is not zero, and treating it as zero would
understate EU production and overstate China's supply share. Where a component's Prodcom value is
missing, the supply share is given as a range: its upper bound with the missing codes at zero
production, and no point estimate.

## Readings, decided now (two-sided)

For each component in 2024, the ratio of China's share of supply to China's share of imports:
- below 0.5: **the import share overstates dependence**; the supply share is the number to use;
- 0.5 to 0.8: the import share **partly** overstates it; both are printed;
- 0.8 or above: the import share is **a fair guide** to dependence.

And the supply share itself, in bands: under 10% low; 10-25% material; 25-50% high; above 50%
critical. The bands describe; they do not measure strategic risk, which depends on what could replace
the supply.

## What this cannot say

Sold production excludes what a maker uses itself; production is valued at the factory gate and
imports include freight, so value shares mix price bases (a quantity check is added where Prodcom and
Comext report comparable units); apparent supply is not consumption; "outside the EU" is the EU27's own
boundary, so the United Kingdom, Norway and Switzerland count as imports, except that the United
Kingdom is excluded throughout for consistency across Brexit.

## Referee review of the draft, and what changed

1. HS6 lines mixed grid and consumer goods: narrowed to above-1,000-V switchgear and conductors,
   inverters above 7.5 kVA, and labelled meters.
2. Suppressed cells biased the result toward the finding: now a bound, not a point.
3. The reading rule was one-sided: now three ratio bands and four level bands, one headline year.
4. Brexit: the United Kingdom excluded from trade on both sides in every year; Prodcom's EU27_2020
   aggregate is used for every year.
5. No summing across components; no trend read from 2019-2023.

## Result - run 2026-09-21 (after deviations 1-3)

Run by `analysis.py`; every number is in `out/eu_grid_supply.json`. 2024, million euro. Rewritten after
two independent language models and a fact-check reviewed the first draft (deviation 3).

| Component | EU sold production | imports | from China | exports | China, share of imports | China, share of supply | ratio | reading | supply band |
|---|---|---|---|---|---|---|---|---|---|
| Liquid-dielectric transformers | 6160 | 1576 | 539 | 1830 | 34% | 9% | 0.27 | the import share overstates dependence | low |
| Grain-oriented electrical steel | 796 | 418 | 217 | 317 | 52% | 24% | 0.47 | the import share overstates dependence | material |
| Insulated conductors above 1,000 V | 7758 | 1049 | 187 | 1795 | 18% | 3% | 0.15 | the import share overstates dependence | low |
| Switchgear above 1,000 V | 5455 | 745 | 167 | 2460 | 22% | 4% | 0.20 | the import share overstates dependence | low |
| Switchboards above 1,000 V | 4593 | 692 | 198 | 1771 | 29% | 6% | 0.20 | the import share overstates dependence | low |
| Inverters above 7.5 kVA (solar, storage, industrial and grid) | 3000 | 2324 | 1912 | 2707 | 82% | 73% | 0.89 | the import share is a fair guide | critical |
| Electricity meters (incl. household smart meters) | 1033 | 528 | 323 | 203 | 61% | 24% | 0.39 | the import share overstates dependence | material |

**For six of the seven components the import share overstates dependence on China, by a factor of two
to seven.** EU makers supply most of the transformers, high-voltage cables, switchgear and switchboards
Europe uses; China's share of supply is 3-9%. Grain-oriented electrical steel and meters sit in the
"material" band, at about a quarter of supply.

**Inverters above 7.5 kVA read "critical" by the filed rule, but the line is not clean grid equipment
and its supply share is not stable.**

- *What the line holds.* The code covers every inverter above 7.5 kVA: commercial and utility solar,
  battery storage and industrial drives as well as grid converters. The filing's selection rule (grid
  equipment by its own description) did not exclude it, and should have flagged it. From 2026 the EU
  splits inverters by function instead of power (deviation 2): in January-July 2026, at any power,
  64% of inverter imports from China were solar inverters, and China supplied 97% of EU solar
  inverter imports and 57% of the rest.
- *How stable the share is.* China's share of EU inverter imports is 67-88% in every year from
  2019. Its share of supply swings from 20% to 73%, because EU production enters as round values
  (2.0, 3.0, 6.0 billion euro in 2020, 2024 and 2023) that look like Eurostat estimates, and because
  exports are nearly as large as production, so supply is a small residual. On 2023's values the
  share was 50%; on 2024's, 73%.

| Inverters | production | imports | exports | apparent supply | China, share of imports | China, share of supply |
|---|---|---|---|---|---|---|
| 2019 | 3370 | 592 | 1852 | 2110 | 73% | 20% |
| 2020 | 2000 | 932 | 1908 | 1023 | 67% | 61% |
| 2021 | 3090 | 1252 | 1689 | 2653 | 75% | 35% |
| 2022 | 3419 | 2614 | 1937 | 4096 | 85% | 55% |
| 2023 | 6000 | 4262 | 2797 | 7465 | 88% | 50% |
| 2024 | 3000 | 2324 | 2707 | 2617 | 82% | 73% |

Read the inverter row as: China supplies most of the large inverters Europe imports; across inverters
of every power, most of what China sells Europe is solar (the 2026 split does not separate sizes). It is
not shown to be a grid-equipment dependence, and its supply share is not precise.

Suppressed production cells: grain-oriented electrical steel in 2020, where its supply share is reported
only as an upper bound. Components are not summed, and no trend is read from 2019-2023.

### What limits this

The numerator of the supply share is gross imports from China; with exports as large as they are for
inverters, some of those goods leave the EU again, so the share is not retained dependence. The quantity
check the filing mentions, where Prodcom and Comext report comparable units, was not run. The
Prodcom-to-CN pairs are description matches; they are plausible for transformers, electrical steel and
switchgear, and weakest for inverters. The API used does not return Eurostat's status flags, so estimated
production values cannot be marked as such; they can only be recognised by their round figures.

## Deviations log

Every change made after this filing goes here, dated, with its reason.

1. **2026-09-21, after the first run - the inverter trade code changed in 2023.** CN 85044086 (inverters
   above 7.5 kVA) exists only from 2023 to 2025; before 2023 the same line was 85044088. The first run
   used 85044086 alone, so inverter trade was zero in 2019-2022 and China's supply share printed as 0%
   for those years. Found by the fact-check. 85044088 is now fetched (`fetch_inverters.py`) and joined to
   the series; the 2024 headline is unchanged. Every other locked code was checked against the CN
   validity dates for 2019-2026; none has a gap.
2. **2026-09-21 - the 2026 inverter split is added as context.** From January 2026 CN splits inverters
   by function: 85044084 with maximum power point tracking (solar) and 85044087 without, at any power.
   Their January-July 2026 imports are reported beside the result to show what the inverter line holds;
   they are not part of the filed measure.
3. **2026-09-21 - result wording rewritten after review.** Two independent language models and a
   fact-check reviewed the first draft. Accepted: the inverter line is described as a broad inverter
   category, not grid equipment; its year-to-year supply shares and the round production values behind
   them are shown; exports are in the table and the gross-imports numerator is stated; the suppressed
   cell is named correctly (the first draft printed an internal key, "goes"). The filing promised a range
   for suppressed cells; only the upper bound is computable, since the missing value is unknown, and
   only the upper bound is given.
