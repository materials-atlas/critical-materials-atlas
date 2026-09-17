# Does recycling answer a price spike? A pre-registered test of scrap supply response

Filed 2026-09-17, before any estimate was computed. Sample sizes below were counted first, on purpose:
they decide whether the test is worth running, and they do not depend on the answer.

This filing was revised once, on the same day and still before any estimate existed, after two
independent language models reviewed the design. What they changed is listed at the end, under
"design review"; the version they read is in the repository's history.

## The decision this serves

"Recycle more" is the standard answer to a supply shock in a critical material. For that answer to
work *as a response to a shock*, secondary supply has to rise when the price rises, within the time a
shock lasts, and by enough to matter against consumption. If it does, a price signal — or a stockpile
release, which is the same signal in reverse — brings out scrap. If it does not, recycling may still
be worth doing for other reasons, but a buyer or a ministry should not plan on it inside a shock.

## The data

United States, from the USGS *Historical Statistics for Mineral and Material Commodities* (DS 140),
read through the atlas cube (`out/cube.parquet`), which carries all three series this test needs:

- `production_secondary` — metal recovered from scrap at US plants, tonnes;
- `unit_value_real98` — the commodity's US unit value deflated to 1998 dollars, used as the price;
- `apparent_consumption` — US supply consumed, tonnes.

Materials with at least 40 years where both secondary production and a real price are positive
(16 of them, 1,418 material-years, longest series 1901–2022): silver, zinc, lead, copper, antimony,
aluminium, nickel, platinum, tin, magnesium, cobalt, industrial diamond, chromium, gold, tungsten,
mercury. Gold has no apparent-consumption series, so it appears only in the tonnage equations.

**Window: 1953–2022.** Both world wars, the Korean war and their price controls are excluded, because
an administered price cannot test a price response. Tantalum (39 years), crushed stone (29) and
selenium (8) fall below the 40-year rule and are excluded.

## The test

Δlog is the annual first difference of a log. For material *i* in year *t*:

**Headline equation — share of consumption.** The reader's question is not how many tonnes of scrap
appeared but how much of the market it covered, and a 10% rise in a scrap flow that is 5% of
consumption is not the same event as one that is 50%:

    Δ(S/C)_it = β₁ Δlog P_i,t-1 + β₂ Δlog P_i,t-2 + α_i + (γ_t) + ε_it

where S/C is secondary production over apparent consumption, in **percentage points**.

**Second equation — elasticity.** The same right-hand side with Δlog S on the left, reported beside
it, because an elasticity travels better between markets.

**Both are run twice, and both runs are headline, not robustness:**

- **with year effects γ_t:** this measures the response to a material's price moving *relative to
  other metals*. Year effects remove anything common to all metals in a year — which includes the
  broad price spikes a ministry actually faces. A real common spike that lifted every material's
  scrap equally would show here as zero.
- **without year effects:** this keeps the common movement, and with it the business cycle. A
  recession lowers price and scrap together, which inflates the estimate.

The truth is bracketed by the two, and the page will publish both rather than pick one. Where they
disagree on which row of the table below applies, that disagreement is the result.

Also filed: material effects α always; standard errors clustered by material, p from a t distribution
with G − 1 = 15 degrees of freedom; Driscoll–Kraay (maximum lag 2) reported alongside; the count of
dropped material-years reported.

**Lagged prices only in the headline.** Scrap supply and price are determined together within a year,
so a contemporaneous coefficient mixes the two. It is reported as a robustness line. Lagging does not
make this causal: a material-specific demand boom can raise price in one year and scrap in the next
(biasing up), while a supply disruption can raise price and cut the fabrication that generates scrap
(biasing down). **The estimate is predictive, not causal, and the page will say so.** The direction of
the net bias is not known in advance.

## What each outcome means, decided now

Read off the **headline share equation**, for a 50% real price rise (Δlog P = 0.405), summing the two
lags, and stated as points of apparent consumption:

| Response to a 50% price rise | p | Reading, as it will be published |
|---|---|---|
| ≥ 1.0 point of consumption | < 0.05 | Scrap answers a spike at a scale that matters: it covers at least a point of consumption within two years. |
| 0.2 to 1.0 point | < 0.05 | Scrap responds, but small: a fraction of a point of consumption, which will not close a shock-sized gap. |
| < 0.2 point | < 0.05 | Measurable and negligible. |
| any | ≥ 0.05 | Not demonstrated within two years. The claim will be "not shown to respond", never "does not respond". |
| negative | < 0.05 | Wrong direction; it will be published with its explanation or not at all. |

For scale, the filing records now that a point of US apparent consumption is what the table will be
read against, and the page must print each material's own secondary share so a reader can see which
markets a point means anything in.

## Supporting checks, all filed in advance

1. **Primary supply, same specification.** Δlog of US primary production on the same lagged prices,
   to say whether scrap is *more* price-responsive than new material. Noted in advance: for most of
   these materials the price is set outside the United States, so this is a comparison of two US
   responses, not of a world supply curve.
2. **Placebo, future prices.** The same regression with Δlog P at *t+1* and *t+2*. Tomorrow's price
   cannot cause today's scrap, so a response here means a trend or an anticipation the specification
   has not removed. This replaces the cross-material placebo as the main falsification test.
3. **Placebo, another material's price,** paired by a fixed rule that skips by-product pairs (cobalt
   with copper or nickel, platinum with nickel, silver with lead or zinc): the successor in the
   alphabetical list that is not a by-product partner. Reported as a weak falsification check only —
   after year effects, a zero here is the default and proves little.
4. **Leave one material out.** The sign, and which row of the table applies, must survive dropping
   any one material.
5. **Investment metals.** Gold, silver and platinum are held as bullion and their scrap responds to
   portfolio decisions as much as to industry. The headline is reported with and without them; if the
   two disagree on the row, that disagreement is the finding.
6. **Recessions.** 1974–75, 1980–82, 2008–09 and 2020 dropped, to check that a few collapses are not
   driving the estimate.
7. **Zeros kept.** Dropping years where secondary production is zero drops collapses, which are part
   of the response. A Poisson regression on levels with the same effects, which admits zeros, is run
   as a filed robustness line.

**Automatic fail:** a response identified only in levels, only contemporaneously, or only when the
window is moved. Any of these means the annual panel does not support the claim.

## What this cannot say, and will be printed on the page

- **United States only.** DS 140 has no other country, and US scrap markets are unusually deep.
  Nothing here transfers to the EU or China without the same test on their data.
- **Domestic recovery only.** `production_secondary` counts metal recovered at US plants. Scrap that
  is collected and *exported* — often the margin that actually moves when a US price rises — is not in
  it, and is not tested here.
- **New and old scrap are mixed** for most materials. Prompt scrap from fabrication is a by-product of
  making things, not of "recycling more"; DS 140 splits the two only for aluminium.
- **Unit values are not market prices.** They are value per tonne of US shipments or imports, so they
  move with product mix as well as with price. That is measurement error in the regressor, and it
  pushes the estimate toward zero.
- **Not capacity.** The test sees the supply that appeared, not what could have been recovered.
- **Not causal, and not a single material's number.** One pooled estimate over 16 materials, from a
  predictive regression.
- A null result means *not demonstrated on this data*, and nothing more.

## Design review, 2026-09-17 (before any estimate)

Two independent language models reviewed the filing above in its first form. Changes made in
response, all before the test was run:

1. Year effects were the only specification; both engines noted they remove the common price spikes
   the study is about, so a real common response would publish as a null. Both specifications are now
   headline, and the page publishes the bracket.
2. The threshold was 0.20 on the elasticity, which is meaningless without knowing how large scrap is
   in each market (10% of a 5% share is nothing). The headline is now the share equation, and the
   table is in points of apparent consumption.
3. The cross-material placebo was presented as validating the year effects; it does not, and its
   pairing crossed by-product links. It is demoted to a weak check, and a future-price placebo — which
   has real power against trends and anticipation — is now the main falsification test.
4. Causal language was removed: the estimate is predictive, and both possible directions of bias are
   stated.
5. What the dependent variable misses (exported scrap, new versus old scrap) is now on the page, not
   only in the filing.
6. Dropping zero years was discarding the collapses that identify a response; a Poisson-on-levels line
   is filed.

## Deviations log

Every change made after this filing goes here, dated, with its reason.
