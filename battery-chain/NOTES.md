# Battery replacement model

## Physical boundary

The illustrative lines each start with a monthly limit of 1 GWh. One
produces NMC811 and the other LFP. Each has a specified cathode and
graphite requirement. The source design coefficients divide kilograms in
Argonne's modelled BEV battery pack by its 70.6 kWh nominal energy and
multiply by 1,000 to obtain tonnes per GWh. The pack's cooling, casing
and other materials are outside the mass balance. The coefficients
illustrate a recipe on a nominal output basis. They do not measure EU
factory consumption or yields. Electrolyte, separators, power, workers
and equipment are assumed available. Cell output is measured in
nominal GWh and other markets and downstream pricing are outside scope.

## Monthly calculation

Each line and material has its own committed delivery lane and assigned
stock. If the direct fraction exposed is `d` and the fraction exposed
upstream within the remaining delivery lane is `u`, the traced exposed
share is `d + (1 - d) * u`. The direct case sets `u` to zero. This prevents
a shipment from being counted twice. Exposure removes that share of
normal monthly deliveries throughout the modelled horizon.

Specify each material's compatible alternative, nameplate quantity,
operational share, and uncommitted share of operational output. An
alternative is eligible only if the recipe can use it and its own
upstream supply remains independent of the disruption. Alternative
deliveries start the month after its qualification lag. The alternative
volume is the product of those three quantity factors, capped at the
disrupted flow. It then remains constant. The prequalified case moves
that start date forward with identical volume. No replacement capacity
is shared across lines or diverted from another buyer.

For each month, add incoming unaffected and eligible replacement tonnes
to the opening usable inventory. Divide each available input by its
recipe tonnes per GWh. Output is the smallest of the material limits
and the cell limit. Consume material at that output and carry the
unused amount forward. The model maximises the current month's output
at each step, with no demand backlogs or price responses. A binding
input is one whose constraint is active at that output. With a tie,
raising only one input may have no immediate effect.

The monthly loss is one minus disrupted output divided by no-disruption
output for the same line and month. The cumulative loss uses total
output over the whole horizon in numerator and denominator. Through
the qualification wait, the stock required for full production equals
the lost monthly input multiplied by the lag. Sustaining full output
after finite stocks run down requires the replacement of each missing
flow. Material can be accumulated separately, and every unit of stock
is accounted for once.

## What the comparisons test

- **Upstream trace.** Under the same stocks and qualification schedule,
  add exposure to otherwise non-Chinese deliveries that depend on the
  disrupted upstream route. This tests the direction and size of the
  effect conditional on the specified linkage.
- **Time and ranking.** Compare relative NMC811 and LFP losses in the
  first month and across the full horizon. Repeat on matched changes to
  stock, lag and alternative volume. The ranking can reverse with the
  horizon or the assumed inventory.
- **Eligibility.** Compare timely qualification, the stated delay and
  zero uncommitted compatible supply. The prequalified case can stay
  at full output through the horizon even if its sustainable supply
  after stocks are drawn down would be lower.

The sensitivity grid uses half and double opening stock, zero and three
additional months of qualification delay and half and full eligible
alternative volume. Each row pairs both chemistries under the same
multipliers. The extremes describe the modelled cases, with no sampling
or probability interpretation.

## Data needed for a real plant study

| Grain | Required fields | Public evidence in this release |
| --- | --- | --- |
| Plant, line and month | Location, owner, chemistry, specification, effective cell output ceiling and customer demand | Aggregate production and capacity context. Line size is an assumption. |
| Line and input grade | Material intensity, yield and losses, usable stock by location and date | Public design intensities for the example. Actual stock and yield are unknown. |
| Supplier, origin and contract lane | Final and upstream production stages, facility, origin, deliveries, alternate sourcing rights and prior commitments | Regional output estimates and one company disclosure establish context. Route-level exposure shares are assumptions. |
| Candidate supplier, buyer and month | Technical compatibility, approved commercial quantities, operational status, qualified production capacity, remaining commitments and lead time | Published qualification example describes one milestone. All alternative volumes and lags in the example are assumptions. |

The evidence JSON separates the production crosswalk, recipe source,
model inputs, scenario results and sensitivity runs. A balanced
conservation calculation validates the model arithmetic. An empirical
validation requires plant records or auditable procurement evidence.
