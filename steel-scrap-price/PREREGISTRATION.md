# Does steel scrap trade respond to a real scrap price? — pre-registration

Filed 2026-09-21, before any value of the price series was read. What was read to plan it: the FRED
series page for the price (title, units, frequency), the scrap-trade study's code and filing, and two
referee reviews of `DESIGN.md`.

## Why, after a correction

The draft was motivated by an apparent result in the scrap-trade study: steel's later price terms were
both positive once year effects were added. **That result was an artefact** — with one price per year
for a single metal, the price terms are absorbed by the year effects and the fit is not identified
(scrap-trade deviation 8, found by both referees of this draft). What remains is the question the
scrap-trade study could not ask at all: steel scrap, the largest scrap market ($44bn traded in 2024),
was left out of its headline because it had no scrap price. There is one: the US Bureau of Labor
Statistics producer price index for iron and steel scrap (FRED **WPU1012**, monthly from 1947).

## Data

- **Price:** WPU1012, monthly, averaged to the year. Nominal in the primary test (see below).
- **Flows:** CEPII BACI, HS 7204, through `baci.py`, 2002-2024. **Carbon steel scrap only** —
  7204.10, 7204.30, 7204.41, 7204.49, 7204.50 — because WPU1012 prices iron and carbon-steel scrap;
  stainless and other alloy scrap (7204.21, 7204.29) are left out. The scrap-trade study's sample rule
  (at least 12 years of positive exports, median above 1,000 t) and small-exporter headline, unchanged.
- **The other six metals** of the scrap-trade study, unchanged, on their Pink Sheet prices.

## The test — identified, because pooled

The scrap-trade study's pooled panel of six metals, with steel added as a seventh on its own price,
year effects, and a separate set of three price terms for steel. The year effects remove what is
common to all metals in a year, including general inflation, so prices enter **nominal**, which also
lets the test run to 2024 instead of stopping in 2022 with the scrap-trade study's deflator. Steel's
terms are identified because the steel scrap price moves differently from the other metals' prices
within a year; the code checks the rank of the regressor matrix and stops if it is not full. Errors
clustered by country; the same fit with errors clustered by year is reported beside it, since the
price is common to all exporters of a metal in a year.

**Primary outcome:** steel's later response, the sum of its one- and two-year terms.

## Readings, decided now (three-way)

- **Responds after the same year:** the 95% interval of the sum lies above zero and the estimate is at
  least 0.20.
- **No response of that size:** the interval's upper end is below 0.20.
- **Inconclusive:** anything else — including a large estimate whose interval reaches zero.
The same-year term and all three terms are printed; only the sum is read.

## Checks

Future-price placebo, read by the same three-way rule (it must not "respond"); errors clustered by
year; 2021 kept in the primary and a version without it as a check; large exporters separately; the
real-price version on the scrap-trade study's deflator (to 2022) beside it.

## What this cannot say

WPU1012 is a US price; exporters elsewhere face their own, though scrap prices move together
internationally. The steel-mill price and demand from Türkiye and China's scrap import rules move all
metals and are only partly removed by the year effects. BACI tonnes are estimated for many flows. Not
causal.

## Referee review of the draft, and what changed

1. **Identification:** one price for one metal is collinear with year effects. Now pooled with the
   six metals, steel on its own price, with a rank check in the code.
2. **Inference:** a common price makes errors clustered by country optimistic; year-clustered errors
   reported beside them.
3. **Reading rule:** the draft's rule could hide a large but imprecise result; now three-way, against
   the interval.
4. **Grade:** WPU1012 is carbon scrap; stainless and alloy scrap are excluded.
5. **Deflation:** nominal prices with year effects, rather than a consumer-price deflator.

## Result - run 2026-09-21

Run by `analysis.py`; every number is in `out/steel_scrap_price.json`. The regressor matrix is full
rank (28 of 28), so steel's terms are identified. 172 small-exporter country-steel pairs among
500 in the pooled panel. The price series was taken from the BLS public API rather than FRED's CSV
endpoint, which timed out (deviation 1); it is the same series.

| | estimate |
|---|---|
| **Primary: steel's later response (one- plus two-year terms), errors by country** | +0.34 (95% +0.05 to +0.63, p 0.023, detectable 0.41) - **responds after the same year** |
| Same, errors clustered by year | +0.34 (95% -0.03 to +0.70, p 0.068, detectable 0.51) - inconclusive |
| Steel's same-year term | +0.78 (95% +0.57 to +0.99, p 0.000, detectable 0.30) |
| Placebo, future prices | +0.10 (95% -0.23 to +0.43, p 0.548, detectable 0.47) - inconclusive |
| Without 2021 | +0.32 (95% +0.02 to +0.61, p 0.035, detectable 0.42) - responds after the same year |
| Large exporters | +0.01 (95% -0.49 to +0.52, p 0.956, detectable 0.71) - inconclusive |
| Real prices, to 2022 | +0.32 (95% +0.02 to +0.61, p 0.035, detectable 0.42) - responds after the same year |

Steel's three terms: same year +0.78, a year later +0.27 (p 0.010), two years later +0.07
(p 0.434).

**By the filed rule the primary reads "responds after the same year"**: the later response is +0.34
with its interval above zero, carried by the one-year term. **It does not survive the stricter errors
the filing asked for beside it**: clustered by year, which respects that the price is common to every
exporter in a year, the interval reaches zero and the reading is inconclusive. The placebo does not
respond, as it must not; the result holds without 2021 and on real prices; the large exporters show
nothing. This is the first sign in either scrap study of a response after the same year, and it is
fragile: reported, not a finding to build on.

## Deviations log

Every change made after this filing goes here, dated, with its reason.
1. **2026-09-21, before the first estimate - the price series came from the BLS API, not FRED.** FRED's
   CSV endpoint timed out repeatedly; WPU1012 is the BLS series FRED republishes, so it was taken from
   the BLS public API (320 months, January 2000 to August 2026; the August 2026 value, 580.548, matches
   FRED's). Same series, different route.
