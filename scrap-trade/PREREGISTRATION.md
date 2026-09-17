# Does scrap move across borders when the price rises? A pre-registered test

Filed 2026-09-17, before any estimate was computed. Companion to `scrap-response/PREREGISTRATION.md`,
which asked whether US *recovery* responds to price and found that in the two metals whose data can
answer — aluminium and lead — it does not. This filing asks the question the open data can answer at
scale: whether the scrap that already exists **moves**.

## The decision this serves

If a price rise does not bring more metal out of scrap (the companion study), the next question a buyer
or a ministry has is whether it at least **redirects** the scrap that exists. Scrap is traded: about
$37bn of copper scrap, $23bn of aluminium scrap and $44bn of steel scrap crossed borders in 2024. If
those flows respond to price within a year or two, then a price signal reallocates supply between
countries even when it creates none — which matters to anyone who expects to buy scrap in a shock, and
to anyone whose recycling industry depends on imported feed. If they do not, then export controls and
import bans, not prices, are what moves scrap.

## The data

- **Flows.** CEPII BACI (HS 2002), 2002–2024, through the atlas's single door (`baci.py`), which
  applies the atlas's own quantity repairs and misclassification flags. Tonnes, by exporter, importer,
  code and year.
- **Codes**, one per metal, all of them "waste and scrap": 7204 steel, 7404 copper, 7602 aluminium,
  7503 nickel, 7802 lead, 7902 zinc, 8002 tin, 7112 precious metal.
- **Prices.** World Bank Pink Sheet monthly, averaged to the year, deflated to 1998 dollars on the same
  basis as the companion study, for the six metals it covers: aluminium, copper, lead, nickel, tin,
  zinc. Gold covers the 7112 line and is reported separately because that line is refining residues as
  much as scrap. **Steel has no Pink Sheet scrap price**; the iron-ore price is not a scrap price, so
  7204 is excluded from the headline and reported only in a separate line using the unit value of
  Turkey's own 7204 imports, the world's marginal scrap buyer, with its endogeneity stated.

## The sample, fixed now

A country-metal pair enters if, over 2002–2024, it has **at least 12 years of positive exports** and a
**median export above 1,000 tonnes** — small and intermittent flows are mostly noise in BACI quantity.
The headline restricts to exporters that are **under 5% of world exports of that metal** in the base
year 2003, because a large exporter moves the price it is being tested against. Large exporters are
reported separately, never in the headline.

## The test

For exporter *c*, metal *m*, year *t*, with Δlog the annual first difference:

    Δlog X_cmt = β₀ Δlog P_mt + β₁ Δlog P_m,t-1 + β₂ Δlog P_m,t-2 + α_cm + (γ_t) + ε_cmt

- `X` is exports in tonnes; `P` is the real metal price.
- Country-metal effects α always. Year effects γ in one of the two headline runs and not the other,
  exactly as in the companion study: with them the estimate is the response to a metal's price moving
  relative to other metals in that year; without them it keeps the common cycle, and with it the world
  business cycle. Both are published.
- **The contemporaneous term is in the headline here**, unlike the companion study: a small exporter's
  shipments do not move the world price, which is why the headline is restricted to small exporters.
  The lagged-only version is reported beside it.
- Standard errors clustered by **country** (hundreds of clusters, not fifteen). Driscoll–Kraay
  (maximum lag 2) reported alongside.
- The headline quantity is the cumulative response β₀ + β₁ + β₂, and each specification must publish
  the smallest effect it could have detected. **A threshold that the design cannot reach is not a
  finding** — that is the lesson of the companion study, and it is filed here before the run.

## What each outcome means, decided now

| Cumulative response | p | Reading, as it will be published |
|---|---|---|
| ≥ 0.5 | < 0.05 | Scrap shipments follow price strongly: a 50% real price rise moves exports by a fifth or more. |
| 0.2 to 0.5 | < 0.05 | A real but modest reallocation. |
| > 0 but < 0.2 | < 0.05 | Measurable and small. |
| any | ≥ 0.05, and the design could detect 0.2 | Not shown to respond. |
| any | ≥ 0.05, and the design could not detect 0.2 | Untestable, reported as such. |
| negative | < 0.05 | Wrong direction; published only with an explanation. |

## Supporting checks, all filed in advance

1. **Imports as the dependent variable.** The same regression on Δlog imports. Exports and imports of
   the same world flow cannot both rise with price in the same year without stocks changing, so the two
   together say whether this is reallocation or measurement.
2. **Placebo, future prices.** Δlog P at *t+1* and *t+2*. A response there is a trend or an
   anticipation the specification has not removed.
3. **Placebo, another metal's price**, paired by a fixed rule: the next metal alphabetically that is
   not a by-product partner of the first (lead–zinc, lead–silver, copper–gold, nickel–cobalt skipped).
4. **Leave one metal out**, and **leave one year out** for the two years with the largest world price
   moves, so the result is not one episode.
5. **Large exporters**, reported separately: the same regression on the exporters excluded from the
   headline.
6. **China's scrap import restrictions.** China restricted imports of several scrap categories from
   2018 and banned more from 2021. The sample is split at 2018 and the two halves reported. This is a
   description of two periods, not a difference-in-differences design, and will not be called one.
7. **Value instead of tonnes.** BACI quantity is weaker than value for high-value-density goods, and
   the atlas's own store-defect work found exactly that. If tonnes and value disagree, the disagreement
   is reported and the tonnage headline is withdrawn.
8. **Unit-value sanity.** The implied unit value of each metal's scrap trade is compared with the metal
   price it is tested against; a line whose unit value does not track the metal at all is dropped from
   the headline with its reason.

**Automatic fail:** a response that appears only contemporaneously *and* reverses at the first lag, or
only in value and not in tonnes, or only with large exporters included.

## What this cannot say, and will be printed on the page

- **Trade is not recovery.** More scrap exported is not more scrap recovered: it can be the same scrap
  going to a different melter, or stocks being drawn down. This study measures movement, and the page
  will say so in its first sentence.
- **Prompt scrap never crosses a border** in most cases, and home scrap never does; what is measured is
  the merchant trade.
- **Policy moves this market too.** Import bans, export licences and customs classification changes are
  in these series and are not separated from price, except for the filed 2018 split.
- **BACI quantity is estimated for many flows**, and its weaknesses are documented in this repository.
- **Not causal.** A predictive regression with a plausibly exogenous price for small exporters is not
  an identified supply curve.
- **Nothing about the newer critical materials.** Lithium, cobalt and rare-earth scrap have no
  distinct customs code over this period.

## Deviations log

Every change made after filing goes here, dated, with its reason.
