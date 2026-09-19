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

## Result - run 2026-09-17: **NOT DEMONSTRATED, and the test cannot tell the filed outcomes apart**

Run by `response.py` (committed before its first run); every number is in `out/scrap_response.json`.
The panel is 16 materials and 1,104 material-years (1953-2022). The **headline share equation
estimates on 959 of them, over 15 materials** - gold has no apparent-consumption series - so its t
distribution has 14 degrees of freedom, not the 15 the filing assumed.

| Share of consumption, +50% real price over two years | Estimate | 95% interval | p |
|---|---|---|---|
| with year effects | -0.71 points | -2.59 to +1.17 | 0.4309 |
| without year effects | +0.23 points | -1.41 to +1.87 | 0.764 |

| Elasticity of secondary tonnes | Estimate | 95% interval | p |
|---|---|---|---|
| with year effects | -0.090 | -0.40 to +0.22 | 0.5429 |
| without year effects | -0.053 | -0.24 to +0.14 | 0.5632 |

**Both land on the filed "not demonstrated" row - but the decisive fact is that this design could
never have landed anywhere else without a very large effect.** With these standard errors, the
smallest response the share equation would detect four times in five is **2.6 points** with year
effects and **2.3 points** without. The filing's own thresholds - 1.0 point matters, 0.2 points
is negligible - sit far inside that. The 95% interval with year effects, -2.59 to +1.17 points, contains
**both** the "answers at scale" cutoff and zero. The honest verdict is therefore not "scrap does not
respond" but: **seventy years of the best public US data cannot tell a useful scrap response from
none.** The elasticity equation is sharper - it would detect 0.43 with year effects, 0.27 without -
and still shows nothing.

**The two lags cancel, and the second one is not noise.** With year effects the first lag is
+0.71 points (p = 0.455) and the second is -1.42 points (p = 0.001). A share that falls two
years after a price rise is as likely to be the denominator moving - consumption recovering faster
than scrap recovery - as anything about scrap supply. It is reported because it is there, not because
this design can interpret it.

**The supporting checks, as filed.**

| Check | Result | Reading |
|---|---|---|
| Primary supply, same specification | elasticity +0.21, 95% interval -0.03 to +0.45, p = 0.0882 | Positive but **not significant** on the filed 5% rule, and its difference from the scrap elasticity (-0.090) was never tested. It cannot carry a claim that new material responds more. |
| Placebo, future prices | +0.02 points, -2.22 to +2.26, p = 0.983 | Nothing shows - but with an interval this wide that is weak evidence, not a pass. |
| Placebo, another material's price | +0.85 points, p = 0.1957 | Larger than the headline itself. It cannot be called a pass. |
| Leave one material out | -0.30 to -1.30 points, every p > 0.07 | No single material drives the result. |
| Excluding gold, silver, platinum | -0.97 points, p = 0.1615 | Same row. |
| Excluding recessions | -1.32 points, p = 0.2421 | Same row. |
| Contemporaneous price added | -0.15 points, p = 0.9305 | Same row. |
| Window 1973-2022 | -0.02 points, p = 0.9843 | Same row. |
| Window 1953-1990 | -0.73 points, p = 0.4983 | Same row. |
| Poisson on levels | log price -0.562, p = 0.0426 | Not the filed check: there were no zero years to keep, and this is a contemporaneous levels association. It carries no weight. |

**What the result says.** On US data for 16 mature metals, 1953-2022, a rise in a material's real
price is **not shown to be followed** by more scrap-derived supply within two years, in tonnes or as a
share of consumption. It says nothing stronger, because the design cannot: a response of the size
that would matter to a ministry sits inside the interval. Raw means agree with the estimate - sorting
material-years into five bins by the previous year's price move, secondary production growth is flat
across the bins while primary production growth runs from -7.3% in the biggest price falls to +3.2%
in the biggest rises - but that contrast is suggestive, not significant.

**What it does not say.** Not that recycling does not respond to price. Not that scrap supply is
price-inelastic. Not that responses of 0.2 to 1.0 points of consumption are ruled out; they are not.
Not that primary supply is more responsive; that was not established. Not anything causal: this is a
predictive regression. Not anything about scrap collected and exported rather than recovered in the
United States, about new versus old scrap, about recycling *capacity*, about non-US markets, or about
the newer critical materials, which have no such series. And these metals already meet a median 19.4%
of US consumption from scrap (lead 59%, antimony 46%, aluminium 40%): the test is about the change
within two years, not the level.

**What would answer the question.** More materials would not help much - the standard error is driven
by how differently materials move, not by how many years there are. What would: a price series that is
a market price rather than a unit value; scrap collected *and* exported as the dependent variable; and
identification from named supply shocks rather than from the price itself.

## Amendment A, 2026-09-17: the same question, tested per metal on market prices

Filed after the first run and before the second, with the first result standing above, unchanged.

**Why.** The first design pooled 16 materials and clustered on material, so its precision came from 15
clusters while a century of annual observations per metal went unused; and its price was a USGS unit
value, which carries product mix as well as price. Both are fixable without new data.

**What changes.**
1. **One estimate per metal, not a pooled one.** Each metal is its own time series: 1960-2022, up to 63
   annual changes, Newey-West standard errors with three lags.
2. **The price is the World Bank Pink Sheet market price** (monthly, averaged to the year, deflated onto
   the USGS 1998 basis by the deflator implied by USGS's own nominal/real pair), for the seven metals it
   covers that also have US secondary production: aluminium, copper, lead, nickel, tin, zinc, gold.
3. **The unit-value version is run beside it**, on the same metals and years, so that the effect of
   changing the price measure is visible rather than assumed.
4. **Summary across metals** is the mean of the seven cumulative responses with its standard error from
   their spread (six degrees of freedom), reported as a summary and never as the headline. Each metal is
   reported with its own interval and its own smallest detectable effect.

**Unchanged:** the dependent variables (secondary tonnes, and secondary as a share of apparent
consumption in points), two lags of the price, lags only, the 50%-price-rise reading, the decision
table, and every "what this cannot say" line. Gold keeps no share equation.

**Decided now, before the run:** a metal counts as responding if its cumulative two-year elasticity is
at least 0.2 with p < 0.05 - the threshold the first filing used - and the page must print, for each
metal, the smallest response that metal's own series could have detected. Where a metal cannot detect
0.2, it is reported as untestable rather than as a null.

## Result of Amendment A - run 2026-09-17: **the two metals whose data can answer show no response at the filed threshold**

Run by `per_metal.py` (committed before its first run); every number is in
`out/scrap_response_per_metal.json`. One estimate per metal, 1960-2022, Newey-West standard errors
with three lags, on World Bank Pink Sheet market prices deflated to 1998 dollars.

| Metal | Two-year elasticity | 95% interval | p | Smallest it could see | Same on USGS unit values | Reading |
|---|---|---|---|---|---|---|
| aluminium | +0.01 | -0.09 to +0.12 | 0.81 | 0.15 | -0.03 | not shown to respond |
| lead | +0.01 | -0.09 to +0.11 | 0.80 | 0.14 | +0.01 | not shown to respond |
| nickel | -0.08 | -0.23 to +0.08 | 0.34 | 0.22 | -0.07 | untestable at 0.2 |
| copper | -0.03 | -0.23 to +0.16 | 0.73 | 0.28 | +0.02 | untestable at 0.2 |
| zinc | -0.13 | -0.43 to +0.17 | 0.39 | 0.42 | -0.16 | untestable at 0.2 |
| gold | +0.20 | -0.25 to +0.64 | 0.38 | 0.63 | +0.20 | untestable at 0.2 |
| tin | +0.21 | -0.26 to +0.68 | 0.37 | 0.67 | +0.22 | untestable at 0.2 |

**Aluminium and lead can see the filed threshold, and show no response at it.** Their own series would have
detected a two-year elasticity of 0.15 and 0.14; the filed threshold is 0.20. Both come in at
+0.01 (0.81) and +0.01 (0.80), with intervals that exclude a response of 0.2. These are the two
metals where recycling is largest: scrap is about 40% of US aluminium consumption and 59% of lead.
The other five cannot see 0.20 on their own and are reported as untestable, not as nulls. What is
ruled out for aluminium and lead is a response *at the filed threshold*: their intervals still admit
small positive responses, and "not shown to respond" is the strongest reading the filing allows.

**Across the seven metals** the mean two-year elasticity is +0.028 (95% interval -0.09 to +0.15),
so a common response above about 0.15 is ruled out.

**The price measure barely matters.** Running the same tests on the USGS unit values the first design
used moves no estimate by more than 0.05 and changes one reading (corrected 2026-09-19, deviation 7): on
unit values lead could only have seen 0.22, so it would read as untestable rather than as not responding. On these seven metals, then,
measuring price by a unit value rather than a market price does not explain the result - which is
weaker than saying measurement error has been ruled out in general, and is all seven comparisons can
support.

### Exploratory, added after the run and not filed: where the adjustment goes instead

The filed share equation says something the filed tonnage equation does not - the recycled share rises
by about 4 points after a 50% price rise (aluminium +4.5, p = 0.06; lead +3.9, p = 0.04) while the
tonnes do not move at all. A share can only rise with a flat numerator if the denominator falls, so
the same specification was run on consumption and on primary production. That was not filed and is
therefore exploratory; it is reported because it explains the filed result rather than adding to it:

| Metal | Secondary supply | US consumption | US primary production |
|---|---|---|---|
| aluminium | +0.01 (p 0.81) | **-0.19 (p 0.01)** | **+0.29 (p 0.01)** |
| lead | +0.01 (p 0.80) | **-0.16 (p 0.02)** | -0.06 (p 0.41) |
| copper | -0.03 (p 0.74) | **-0.21 (p 0.05)** | -0.05 (p 0.62) |
| zinc | -0.13 (p 0.39) | -0.17 (p 0.09) | -0.10 (p 0.18) |
| nickel | -0.08 (p 0.34) | -0.11 (p 0.06) | not testable |
| tin | +0.21 (p 0.37) | -0.07 (p 0.44) | not testable |

Read down the columns: in the three largest metals, higher prices are followed by **lower
consumption**, and for aluminium by **higher primary output**, while secondary supply sits still. That
is consistent with the filed share equation rising because its denominator falls rather than because
more scrap returns - but these are unfiled, post-hoc regressions on the same data that raised the
question, they are predictive and not causal, and one of the two share results (aluminium, p = 0.06)
would not clear the filing's own 5% rule. It is a hypothesis for a separate pre-registered test on
other countries, and nothing on any page will be built on it.

### Sub-period checks, also exploratory

Aluminium and lead were re-run on 1960-1990, on 1991-2022, and with the recession years dropped. The
tonnage elasticity stays within +0.04 of zero in every split, and is never significant.

### What Amendment A does and does not change

It replaces "not demonstrated, and the test cannot tell the filed outcomes apart" with something
sharper **for two metals**: aluminium and lead do not bring out more scrap within two years of a price
rise, and their data are good enough to have seen it if they had. Everything else is unchanged: the
other five metals remain untestable at the filed threshold, the estimates are predictive and not
causal, and all of it is the United States and domestic recovery only, so scrap collected and exported
is still outside the test.

## Deviations log

Every change made after this filing goes here, dated, with its reason.

**2026-09-17 — three details the filing left open or got wrong, recorded after the run.**
1. **The zeros check had nothing to keep.** The filing added a Poisson-on-levels line so that years
   with zero secondary production would not be dropped. There are none in the sample: the 87 dropped
   material-years are years missing from the source, not zeros. The Poisson line is reported as what
   it actually is — a contemporaneous levels association (log price -0.562, p = 0.0426) — and carries no
   weight.
2. **Gold is not in the share equation.** DS 140 gives it no apparent-consumption series, as the
   filing noted; leaving it out therefore changes nothing (its leave-one-out row equals the baseline).
   It stays in the tonnage equation.
3. **The by-product-skipping placebo pairing** resolved to the alphabetical successor for every
   material except where a by-product partner was skipped; the pairs are listed in
   `out/scrap_response.json` under `checks.placebo_other_material.pairs`.
4. **Power was not filed, and it should have been.** The review after the run showed the design's
   smallest detectable response is about 2.6 points of consumption, far above the filing's own
   1.0-point threshold, so the decision table was unreachable in practice. The result is reported
   with its interval and that detectable size, and no filed threshold is claimed to be ruled out.
   Per-lag standard errors and the detectable size were added to `response.py` after the run; that
   adds output only and changes no estimate.
5. **The estimation sample is 959 material-years over 15 materials** for the share equation (gold has
   no consumption series), so its t distribution has 14 degrees of freedom, not the filed 15.
6. **Amendment A's exploratory extension, 2026-09-17.** The consumption and sub-period equations in the
   Amendment A result were not filed. They were run only after the filed share and tonnage equations
   disagreed, to find out which side of the ratio was moving, and they are labelled exploratory
   wherever they appear. The primary-production equation was filed (check 1).
7. **2026-09-19 - a sentence in the Amendment A result corrected, after a fact-check.** The result said
   the unit-value run "moves no estimate by more than 0.04, and changes no reading". The largest move is
   0.05 (aluminium, +0.013 on market prices against -0.033 on unit values), and lead's reading changes:
   its detectable size on unit values is 0.22, so it reads as untestable at 0.2
   (`out/scrap_response_per_metal.json`, `metals.lead.unit_value.reading`). No estimate changed.
