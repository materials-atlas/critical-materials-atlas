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

## Result - run 2026-09-21

Run by `analysis.py`; every number is in `out/eu_grid_supply.json`. 2024, million euro.

| Component | EU sold production | imports | from China | China, share of imports | China, share of supply | ratio | reading | supply band |
|---|---|---|---|---|---|---|---|---|
| Liquid-dielectric transformers | 6160 | 1576 | 539 | 34% | 9% | 0.27 | the import share overstates dependence | low |
| Grain-oriented electrical steel | 796 | 418 | 217 | 52% | 24% | 0.47 | the import share overstates dependence | material |
| Insulated conductors above 1,000 V | 7758 | 1049 | 187 | 18% | 3% | 0.15 | the import share overstates dependence | low |
| Switchgear above 1,000 V | 5455 | 745 | 167 | 22% | 4% | 0.20 | the import share overstates dependence | low |
| Switchboards above 1,000 V | 4593 | 692 | 198 | 29% | 6% | 0.20 | the import share overstates dependence | low |
| Inverters above 7.5 kVA | 3000 | 2324 | 1912 | 82% | 73% | 0.89 | the import share is a fair guide | critical |
| Electricity meters (incl. household smart meters) | 1033 | 528 | 323 | 61% | 24% | 0.39 | the import share overstates dependence | material |

**One component is a real dependence: inverters above 7.5 kVA.** China supplied 82% of EU imports
and 73% of EU supply in 2024; the import share is a fair guide there. For every other component the
import share overstates dependence, by a factor of two to seven: EU makers supply most of the
transformers, cables, switchgear and switchboards Europe uses. Electrical steel and meters sit in the
"material" band, at about a quarter of supply. Components are not summed, and no trend is read from
2019-2023.

Suppressed production cells: goes have at least one missing year. Where a component's Prodcom value was missing in any year, its
supply share for that year is given only as an upper bound.

## Deviations log

Every change made after this filing goes here, dated, with its reason.
