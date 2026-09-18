# Does the grid bind before the chip? Price and volume in world trade for the electricity build-out

Design draft, 2026-09-18. Not yet filed: this draft goes to two independent reviewers first, and the
filing that follows it is fixed before any estimate is computed. Descriptive totals were looked at
to judge feasibility (below), and that is stated rather than hidden.

## The question

Data centres, electric vehicles, heat pumps and renewable generation all draw on the same grid
equipment: transformers, the grain-oriented electrical steel inside them, and copper conductor. Public
discussion of the AI build-out concentrates on chips. The question here is narrower and answerable:

**Between 2017 and 2024, did world trade in grid equipment show the signature of a supply
constraint - prices rising faster than volumes, relative to comparable manufactured goods - and did
chip-making equipment show it too?**

A supply constraint and a demand boom both raise the value of trade. They differ in how the value
rises. If supply can expand, volume carries most of the increase and prices stay near trend. If it
cannot, prices carry more of it. That decomposition is available in customs data for goods whose
weight means something, which is the reason for choosing these lines.

## What was seen before this design was written

World totals for 2017-2024 were computed to check feasibility: transformer tonnage and unit values
both rose after 2021; electrical-steel tonnage was nearly flat while its unit value rose sharply into
2022; chip tonnage is not a meaningful quantity (processors' reported weight quintupled while value
rose by half). The design below was written after seeing those totals. That is why its tests are at
the level of individual trade flows against control goods, not on the world totals already seen, and
why chips are excluded from the price-volume tests on the grounds, stated now, that their weights
cannot carry them.

## Data

- **Trade.** CEPII BACI, HS 2017 nomenclature for every year (one nomenclature throughout; the
  atlas's reader otherwise changes nomenclature by year), 2017-2024, value and tonnes by exporter,
  importer and six-digit code, read through the atlas's single BACI reader.
- **Treated lines (grid equipment):** liquid-dielectric transformers 8504.21, 8504.22, 8504.23;
  grain-oriented electrical steel 7225.11 and 7226.11; refined copper wire 7408.11.
- **Chip-making equipment:** 8486.20 (machines for semiconductor devices and integrated circuits),
  8486.10 (boule and wafer machines), analysed separately and not pooled with grid equipment.
- **Controls:** comparable manufactured goods sold to similar industrial buyers but not tied to grid
  or chip investment. Proposed: electric motors (8501.52, 8501.53), other flat-rolled alloy steel
  (7225.19 non-oriented electrical steel is **not** a control - it goes into motors and EVs - so the
  proposed steel control is 7208.51 hot-rolled non-alloy plate), industrial pumps (8413.70),
  compressors (8414.80). The reviewers are asked specifically whether these are good controls.
- **Prices for deflation:** the comparison is always relative to control goods in the same year, so
  general inflation cancels; no deflator is needed for the tests.

## Unit of analysis and measure

A **flow** is one exporter-importer pair in one six-digit line. Its unit value is value divided by
tonnes. Comparing a flow with itself across years holds the route and the line fixed, which removes
most of the product-mix change that makes world unit values unreliable. It does not remove mix
within a flow (a buyer switching from 20 MVA to 200 MVA transformers inside 8504.23), and the page
will say so.

Flows enter when both value and tonnes are reported and positive in consecutive years, and when the
flow is at least USD 100,000 in the earlier year. Flow unit values more than ten times or less than a
tenth of the line's median in that year are dropped as unit errors, and the count reported.

## The tests

For flow *f* in line *l*, year *t*:

    Δlog UV_ft = β · (grid_l × post_t) + α_f + γ_lt ... (see below)

Stated plainly:

1. **Prices.** The change in a flow's unit value, grid lines against control lines, 2021-2024 against
   2018-2020. Flow effects, year effects; standard errors clustered by exporter.
2. **Volumes.** The same with the change in tonnes.
3. **The signature.** A supply constraint predicts the price coefficient positive and the volume
   coefficient not larger than the controls'. A demand boom met by expanding supply predicts the
   reverse. Both are filed; either can be the finding.
4. **Chip-making equipment** gets the same two tests against the same controls, as a separate
   comparison.

Pre-specified sign and size, before any estimate: a grid price premium of at least 10 percentage
points of cumulative unit-value growth over the post period, relative to controls, is called a
material price signature; below that, measurable but small; not significant, not shown. Each
estimate must print the smallest effect it could have detected.

## Supporting analyses

- **Event years.** Year-by-year coefficients (an event-study plot) so that a single spike such as
  2022 is visible rather than averaged away, and so that pre-2021 years show whether grid and control
  goods were moving together before.
- **Who supplies the increase.** For each treated line, the change in each exporter's share and the
  number of exporters, to separate "existing suppliers charged more" from "new suppliers entered".
- **Concentration** of each line, 2017 and 2024, on the measure the atlas uses elsewhere.
- **Leave one exporter out** for the largest exporter of each line.

## What this cannot say

- Nothing about AI specifically: every buyer of grid equipment is in these flows.
- Nothing about domestic production or installation, only cross-border trade. For countries that make
  their own transformers, domestic shortages never reach these data.
- Unit values are not prices; within-flow mix change remains.
- Nothing causal about why a constraint arose.
- Nothing about chips' own prices: their weights cannot carry the test.

## Literature

To be assembled from verified sources only (each checked to exist before it is cited): the
transformer and electrical-steel supply record (government and laboratory reports), the use of trade
unit values as prices, and the separation of supply from demand shocks by the joint behaviour of
price and quantity.
