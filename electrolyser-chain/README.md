# Iridium and PEM electrolysis

Evidence review dated 25 November 2026. The [article](electrolyser-chain.html)
compares published deployment, loading and supply evidence with a gross
one-year threshold and an illustrative annual material balance. The
[claim audit](PRODUCTION.md) identifies the public pilot and records the
literature comparison and scope.

## Reproduce the article and tables

From the repository root:

```text
python electrolyser-chain/record_electrolyser.py
python electrolyser-chain/test_constraint_frontier.py
python -m http.server 8765
```

Open [the local study](http://localhost:8765/electrolyser-chain/electrolyser-chain.html).
The builder reads the pinned [evidence and assumptions](evidence_inputs.json),
the [article template](article.html.in) and the [BACI extract](out/electrolyser_trade.json).
It generates static HTML, [evidence JSON](out/electrolyser_chain.json), the
[one-year scenario matrix](out/illustrative_scenario_matrix.csv) and
[equality thresholds](out/illustrative_thresholds.csv), plus
[annual flows](out/illustrative_annual_flows.csv),
[mitigation curves](out/illustrative_mitigation.csv) and
[sensitivity summaries](out/illustrative_sensitivity.csv).
Running `python electrolyser-chain/constraint_frontier.py` regenerates the
CSV files alone. Both scripts use the standard library.

## One-year threshold

Multiply annual new PEM GW by elemental kg Ir per MW. The factors of
1,000 for GW to MW and kg to tonnes cancel. Gross demand equals the
contained metal in new stacks. The available primary allocation is the
assumed fraction of the 7.5 t/year literature reference. Dividing the
allocation by intensity gives annual new PEM GW at equality. The result
is the equality point for that pair of assumptions. This version omits
stack replacements, manufacturing loss and recycling.

## Annual model

The slower, middle and faster paths are hypothetical global additions.
Each path interpolates annual all-technology additions between the
specified years, then allocates a fraction to PEM. This preserves the
difference between annual additions and installed stock. The zero opening
stock applies to the illustrative facility fleet and to recovered iridium.
There is no pre-2026 fleet in the balance. All capacity is rated electrical
input on a comparable stack basis. The alternative technology share
changes capacity allocation and implies no particular hydrogen output.

Convert stack operating hours to whole model years by dividing by 8,760
times assumed annual utilisation and rounding up. Each vintage carries
its capacity, contained metal and host plant end year. At stack end of life,
the plant gets a new stack with the contemporary loading if it is still
open. At plant retirement, the final stack leaves service without a
replacement. Apply the combined collection and recovery fraction to the
metal in the removed vintage and return it after the chosen lag. This
illustration applies one combined rate per case. Unused recovered metal
carries forward. Manufacturing yield converts contained metal to gross
factory input. Production scrap exits the model. Recycled metal reduces
gross input before comparison with the annual primary allocation.

An annual gap is the positive difference between primary metal required
and assumed primary supply allocated to PEM. Available primary material
below that allocation in one year is not carried forward. For remaining
sectors the model reserves the rest of primary supply without simulating
their demand or prices. The reported sum of gaps adds the positive annual
differences. It is conditional on scheduled capacity going ahead, even if
a year has a gap, so subsequent metal returns are conditional as well.
The lower-loading and lower-PEM-share cases interact through the returned
metal. Varying the levers one at a time is not an additive decomposition.

## What would calibrate the balance

A calibrated projection needs project vintages by technology and status,
elemental iridium loadings and rated power, stack hours across duty cycles,
manufacturing yield, firm demand from other uses, access to inventoried
metal, and collection and refining capacity with contractual delivery times.
The current article supports an evidence review and reproducible comparisons
of explicit assumptions.

## Follow-up on the material budget, 25 November 2026

The dated addendum compares the middle schedule against a second model
that allows only the capacity that available material can support.
The annual material budget adds mine-linked supply, releases of outside
stocks and external recycled metal. It subtracts net demand from other
applications and additions to outside stocks. Fleet returns are separate.
The reference inputs are constant over the study years. Unused
outside supply does not carry over. Unused recovered metal from the fleet does.

Each year, new and replacement stacks draw from the fleet's recovered
stock first, then the market budget. The model serves outstanding
replacements for plants that remain open before commissioning new
capacity. An expired stack stops operating until replaced. The plant
lifetime starts at commissioning. New projects wait if their material
is unavailable and are counted separately from existing capacity awaiting
replacement. Fractional GW are allowed. In a scarce year the capacity
budget is rounded down to the nearest watt. Replacements and recycling
follow only stacks fitted in the constrained calculation. There is no
pre-existing fleet, cancellation or switch to another technology.

The main builder also writes [matched annual deployment and metal flows](out/constrained_annual_deployment.csv).
The [evidence JSON](out/electrolyser_chain.json) holds one-at-a-time tests
and the pairs of assumptions. Gross input and annual metal gaps in the
sensitivity figure come from the demand calculation. Waiting GW and
commissioned GW come from the constrained calculation. The tested ranges
are illustrative. This is not an estimate of future PEM project delivery.
