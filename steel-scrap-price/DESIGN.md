# Does steel scrap trade respond to a real scrap price? — design draft (not yet filed)

Draft, 2026-09-21. Not a filing; the series ID marked [VERIFY] is being confirmed and the design goes
to two referees before it is filed. No value of the price series has been read.

## Why

In the scrap-trade study, steel (HS 7204) was the one line whose two later terms were both positive
once year effects removed the common cycle (+0.20 and +0.17). It was not read, because its price was
the unit value of Türkiye's own scrap imports: the marginal buyer's price moves with the same shocks as
the exports it is meant to explain. Steel scrap is also by far the largest scrap market ($44bn traded
in 2024). A real, independently set scrap price would settle it.

## Data

- **Price:** the US Bureau of Labor Statistics producer price index for iron and steel scrap
  [VERIFY series ID, e.g. WPU1012 on FRED], monthly, averaged to the year, deflated by the US consumer
  price index (World Bank FP.CPI.TOTL) so the series runs to 2024 rather than stopping in 2022.
- **Flows:** CEPII BACI, HS 7204 exports in tonnes, 2002-2024, through `baci.py`; the scrap-trade
  study's sample rule (at least 12 years of positive exports, median above 1,000 t) and its
  small-exporter headline, unchanged.

## The test

The scrap-trade study's estimator, unchanged (country-metal fixed effects, three price terms: same
year, one and two years later, errors clustered by country). **The primary outcome is the later
response: the sum of the one- and two-year terms, with year effects** — because the question is whether
the later response survives removing the common cycle, which is where steel stood out.

**Reading, decided now.** If that sum is at least its own smallest detectable effect at 80% power and
p < 0.05, steel scrap trade responds to price after the same year. If the sum is below its detectable
size, the test is untestable at that size. Otherwise, not shown. The same-year term and the
specification without year effects are reported beside it and not read as the answer.

## Checks

Future-price placebo; the Türkiye unit-value result from the scrap-trade study printed beside it; the
2021 price spike left out; large exporters separately.

## What this cannot say

The PPI is a US price; exporters elsewhere face their own, though scrap prices move together
internationally. Not causal. Grade mix within 7204 changes, and BACI tonnes are estimated for many
flows.
