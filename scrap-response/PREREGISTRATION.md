# Does recycling answer a price spike? A pre-registered test of scrap supply response

Filed 2026-09-17, before any estimate was computed. Sample sizes below were counted first, on purpose:
they decide whether the test is worth running, and they do not depend on the answer.

## The decision this serves

"Recycle more" is the standard answer to a supply shock in a critical material. For that answer to
work *as a response to a shock*, secondary supply has to rise when the price rises, within the time a
shock lasts. If it rises usefully within a year or two, a price signal — or a stockpile release, which
is the same signal in reverse — calls out scrap. If it does not, recycling may still be worth doing
for other reasons, but it is not an instrument for a shock, and a buyer or a ministry should not plan
as though it were.

## The data

United States, from the USGS *Historical Statistics for Mineral and Material Commodities* (DS 140),
read through the atlas cube (`out/cube.parquet`), which carries all three series this test needs:

- `production_secondary` — metal recovered from scrap, tonnes;
- `unit_value_real98` — the commodity's US unit value deflated to 1998 dollars, the price;
- `apparent_consumption` — US supply consumed, tonnes (used only in a robustness check).

Materials with at least 40 years where both secondary production and a real price are positive
(16 of them, 1,418 material-years in total, longest series 1901–2022):

silver, zinc, lead, copper, antimony, aluminium, nickel, platinum, tin, magnesium, cobalt,
industrial diamond, chromium, gold, tungsten, mercury.

**Window: 1953–2022.** Both world wars, the Korean war and their price controls are excluded, because
an administered price cannot test a price response. Tantalum (39 years), crushed stone (29) and
selenium (8) fall below the 40-year rule and are excluded.

## The test

For material *i* and year *t*, with Δlog the annual first difference:

    Δlog S_it = β₁ Δlog P_i,t-1 + β₂ Δlog P_i,t-2 + α_i + γ_t + ε_it

- `S` is secondary production, `P` the real unit value.
- Material effects α and year effects γ. Year effects absorb the business cycle and anything common
  to all metals in a year; material effects absorb each material's own trend.
- **Lagged prices only.** Scrap supply and price are determined together within a year — more scrap
  pushes the price down — so a contemporaneous coefficient mixes supply response with that feedback.
  The contemporaneous term is reported as a robustness line, never as the headline.
- Standard errors clustered by material, p from a t distribution with G − 1 = 15 degrees of freedom.
  Driscoll–Kraay (maximum lag 2) reported alongside.
- A material-year is dropped when either series is zero or missing, so the log exists; the count of
  dropped years is reported.

**The headline quantity is the two-year cumulative response β₁ + β₂.**

## What each outcome means, decided now

| Cumulative β₁ + β₂ | p | Reading, as it will be published |
|---|---|---|
| ≥ 0.20 | < 0.05 | Scrap answers a price spike usefully: a 50% real price rise brings out at least 10% more secondary supply within two years. |
| > 0 but < 0.20 | < 0.05 | Scrap responds, but too little to matter in a shock: under 10% more supply for a 50% price rise. |
| any | ≥ 0.05 | Not shown to respond within two years. The claim will be "not demonstrated", never "does not respond". |
| ≤ 0 | < 0.05 | Scrap supply moves the wrong way — a result that would need an explanation before publication. |

## Supporting checks, all filed in advance

1. **Primary supply, same specification.** Δlog of US primary (mine or smelter) production on the same
   lagged prices. This says whether scrap is *more* price-responsive than new material, which is the
   comparison a reader actually wants.
2. **Placebo.** The same regression with each material's price replaced by another material's price,
   paired by a fixed rule (alphabetical successor within the sample, wrapping around). The cumulative
   response should not differ from zero. A placebo that passes means year effects are not absorbing
   what they should.
3. **Leave one material out.** The sign and the side of the 0.20 line must survive dropping any one
   material.
4. **Investment metals.** Gold, silver and platinum are held as bullion and their scrap flows respond
   to portfolio decisions as much as to industry. The headline is reported both with and without them,
   and if the two disagree on which row of the table applies, that disagreement *is* the finding.
5. **Recessions.** 1974–75, 1980–82, 2008–09 and 2020 dropped, as a check that a few collapses are not
   driving the estimate.
6. **Scrap share.** The same test with the share of apparent consumption met by secondary supply as
   the dependent variable, which asks the question in the form a reader cares about.

**Automatic fail:** a response identified only in levels, only contemporaneously, or only when the
window is moved. Any of these means the annual panel does not support the claim.

## What this cannot say

- It is the **United States** only. DS 140 has no other country, and US scrap markets are unusually
  deep. Nothing here generalises to the EU or China without the same test on their data.
- Unit values are not market prices: they are value per tonne of US shipments or imports, which moves
  with product mix as well as with price.
- A two-year window tests a shock response, not whether recycling grows a supply base over decades.
- Nothing here measures *capacity* to recycle, only the supply that appeared.

## Deviations log

Every change made after filing goes here, dated, with its reason.
