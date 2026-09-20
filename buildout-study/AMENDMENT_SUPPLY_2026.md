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

## Result - run 2026-09-20: **the import share overstates dependence, and the supply share is still the story**

Run by `supply.py`; every number is in `out/buildout_supply.json`. Million euro.

**Transformers (8504.21-.23 / Prodcom 27114120, 27114150, 27114180).**

| Year | EU sold production | imports | of which China | exports | apparent supply | China, share of imports | China, share of supply |
|---|---|---|---|---|---|---|---|
| 2019 | 3346 | 290 | 13 | 1086 | 2551 | 4.6% | 0.5% |
| 2020 | 3416 | 313 | 13 | 1164 | 2564 | 4.2% | 0.5% |
| 2021 | 3563 | 401 | 35 | 959 | 3005 | 8.8% | 1.2% |
| 2022 | 4401 | 585 | 55 | 1071 | 3914 | 9.5% | 1.4% |
| 2023 | 5264 | 1206 | 320 | 1577 | 4893 | 26.5% | 6.5% |
| 2024 | 6160 | 1576 | 539 | 1830 | 5907 | 34.2% | 9.1% |
| 2025 | not published | 2074 | 957 | 1566 | - | 46.1% | - |

**Grain-oriented electrical steel (7225.11, 7226.11 / Prodcom 24105310, 24105410).**

| Year | EU sold production | imports | of which China | exports | apparent supply | China, share of imports | China, share of supply |
|---|---|---|---|---|---|---|---|
| 2019 | 503 | 162 | 15 | 208 | 457 | 9.2% | 3.3% |
| 2020 | not published | 150 | 25 | 118 | - | 16.6% | - |
| 2021 | 650 | 193 | 52 | 243 | 600 | 26.9% | 8.7% |
| 2022 | 1139 | 409 | 112 | 454 | 1095 | 27.2% | 10.2% |
| 2023 | 1065 | 458 | 166 | 363 | 1159 | 36.2% | 14.3% |
| 2024 | 796 | 418 | 217 | 317 | 898 | 51.9% | 24.2% |
| 2025 | not published | 547 | 312 | 325 | - | 57.0% | - |

**The filed reading applies to both, and it is the useful correction.** In 2024, China supplied
34.2% of the EU's transformer imports from outside the EU but 9.1% of apparent supply, because EU
makers sold 6,160 million euro of transformers against 1,576 million of imports. For electrical
steel the same two numbers are 51.9% and 24.2%. Both ratios are below a half, so by the rule filed
before the pull, the note must print the supply share and must not read the import share as dependence.

**What the supply share still says.** It rose steeply: China went from 0.5% of EU transformer supply in
2019 to 9.1% in 2024, and from 3.3% to 24.2% of electrical-steel supply - a rise of about
7 times in five years for the steel. The direction the note reports is unchanged; the level is
much lower than an import share suggests.

**Two gaps, both reported rather than patched.** Prodcom has no 2025 production yet, so apparent supply
stops in 2024 while the trade record runs to July 2026. And the 2020 production of electrical steel is
missing from Prodcom (a suppressed or unpublished cell), so 2020 has no supply share; it is left
empty rather than interpolated.

## Deviations log

Every change made after this filing goes here, dated, with its reason.
