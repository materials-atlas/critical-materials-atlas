# Amendment E: from share of imports to share of EU supply (descriptive)

Filed 2026-09-20, before any production value was read. Only Eurostat's product list for the Prodcom
dataset was retrieved, to find the right codes; the slice used to retrieve it carried 2024 sold-production
values for every product, which were not read or used, and the values below come from a later, filed
pull. This amendment extends `PREREGISTRATION.md` and `AMENDMENT_EU_2026.md`.

## Why

The note reports that China supplies 57% of the value of EU imports of grain-oriented electrical steel
from outside the EU, and 46% of EU imports of transformers. Twice on the page we say what that does not
mean: imports are not consumption, because EU producers supply part of both. The first question any
reader asks is therefore unanswered - **how much of what the EU actually uses comes from China?** -
and the data to answer it are public.

## Data

- **EU production.** Eurostat Prodcom, dataset `DS-059358` ("Sold production, exports and imports"),
  indicator `PRODVAL` (sold production, euro), reporter `EU27_2020`, annual.
  Lines: transformers **27114120** (liquid dielectric, <= 650 kVA), **27114150** (> 650 to 10 000 kVA),
  **27114180** (> 10 000 kVA); grain-oriented electrical steel **24105310** (>= 600 mm wide) and
  **24105410** (< 600 mm). These are the Prodcom counterparts of the study's HS lines 8504.21-.23 and
  7225.11 / 7226.11, matched on the product descriptions, not on a published concordance.
- **EU trade.** The Comext download already used for amendment B: imports from outside the EU and
  exports to outside the EU, same lines, the United Kingdom excluded in every year on both sides.

## The measure

For each year and each of the two groups:

    apparent supply = EU sold production + imports from outside the EU - exports to outside the EU

and, beside it, **China's share of apparent supply** = imports from China / apparent supply, with
China's share of imports repeated so the two can be read together.

Reading, decided now: if China's share of apparent supply is at least half its share of imports, the
note says the import share is a fair guide to dependence; if it is much smaller, the note says the
import share overstates dependence and gives the supply share instead. Either way both numbers are
printed, and neither is called a measure of dependence on its own.

## What this cannot say

Prodcom is **sold** production: what a firm makes and uses itself, or transfers within a group, is out.
Production is valued at the factory gate and imports include freight, so the two sides of the sum are
not on the same price basis. Prodcom suppresses cells for confidentiality, so a year may be incomplete
rather than small, and a missing year is reported as missing, never as zero. The Prodcom-to-HS match
rests on product descriptions. Apparent supply is not consumption: stocks and re-exports are not
observed. Nothing here is causal, and nothing here measures physical volumes - it is all value.

## Deviations log

Every change made after this filing goes here, dated, with its reason.
