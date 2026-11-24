# Solar manufacturing study

Evidence and model release dated 24 November 2026. The [claim register](PRODUCTION.md)
records the original claims, source vintages and old file checksums. The
[study](solar-chain.html) contains the findings and core tables in its
initial HTML. Its trade year control can explore the checked-in customs series.

## Reproduce the article and model

From the repository root:

```text
python solar-chain/record_solar.py
python solar-chain/solar_flow.py
python -m http.server 8765
```

Open [the local study](http://localhost:8765/solar-chain/solar-chain.html).
The builder reads the [evidence and scenario inputs](evidence_inputs.json),
the [article template](article.html.in) and the checked-in
[trade extract](out/solar_trade.json). It writes the static article and the
[calculated evidence JSON](out/solar_chain.json). The main Atlas copy can
rebuild the original trade values from raw BACI using `build_chain_trade.py`.
The same HS02 and HS17 categories are used in this release.

## Scope and units

The model follows a single compatible crystalline-silicon route. The IEA
gives approximate annual stage ratings for Europe in 2025. The illustration
normalizes the rates to GW-equivalent of module output. This comparison assumes
compatible facilities and full available nameplate capacity at each listed
stage. The IEA note omits an ingot rate and does not publish a region-to-country
bridge or upstream conversion factors. The Fraunhofer EU-27 inventory is
kept separate. Raw feedstock, non-cell module components, energy, labor and
finished-module demand are assumed available.

## Throughput and interruptions

1. Multiply each annual nameplate rate and each available annual import rate
   by elapsed months divided by twelve. Opening inventory is a one-time
   quantity. Each step can make at most its time-scaled capacity or the
   prior step’s available output multiplied by its assumed yield, whichever
   is smaller. Qualified inbound supply and a stock draw at that stage are
   available for the next step. This forward calculation gives the maximum
   feasible module output for a serial route with no competing uses.
2. For the annual closed-route ceiling, use zero trade and zero stocks and
   unit yields. Relax only the unknown ingot constraint. The remaining
   minimum is 1.5 GW-equivalent per year. Division by 33 gives about 4.5%
   of nominal module capacity. Enforcing an ingot or other omitted limit
   can only lower this ceiling for the same route.
3. The six-month open example assumes an annual wafer import rate of 8.5
   GW-equivalent. This is the rate that fills 10 GW/year of cell capacity
   alongside 1.5 GW/year of domestic wafers at the point assumptions.
   Point cases assume that the entire imported wafer lane is exposed and
   1.5 GW/year of operable ingot capacity feeds domestic wafers. All
   conversions use unit yields. Other kinds of imports, including qualified
   cells, are excluded from the wafer experiment.
4. The shocks remove half or all of the exposed China-origin wafer supply
   for the horizon. Replacement shipments restore the stated fraction of
   the lost input. Opening stocks cover up to the remaining shortfall.
   The buffered illustration replaces half the lost input and makes 0.5
   GW-equivalent of stock available. Stocks are not annualized.
5. Scenario ranges vary the route’s China-origin share from 0 to 100% and
   the available ingot rate from zero to 1.5 GW/year. The paired differences
   use the open case with the same ingot rate and origin share. These
   endpoints are sensitivity assumptions. They carry no statistical
   probabilities and describe no observed sourcing mix.

The reported stage limits are capacity constraints active at the illustrative
point. More than one may be active at the same time. A small increase to one
stage can therefore have zero marginal gain. The policy calculation uses
80% of the open point output as a common physical target. Integrated capacity,
replacement shipments and stocks achieve that target only if the assumed
compatible wafer quantities are available on time.

## Evidence needed for a real disruption estimate

The public inputs do not establish how much of IEA’s Europe capacity can
operate, how it converts across factories, or which companies can replace
which wafer supplies. Estimating actual losses or the cost of achieving
resilience needs same-region ingot and wafer capacity, plant utilization and
yields, qualified input flows and contracts, inventory, costs and replacement
lead times. The assessment ends at factory output. It does not estimate
installed capacity, electricity generation or disruption probabilities.

## Sourcing and capacity sensitivity, 24 November 2026

The addendum uses the same severe interruption and holds the assumed
pre-shock wafer import rate, wafer nameplate, yields and horizon fixed.
Columns vary the China-origin share of the assumed import lane, with that
share entirely lost. Rows vary the usable ingot rate from zero to the
rate needed to fill domestic wafer nameplate. Each cell is module output
over the horizon, in GW-equivalent. The grid explores the assumed range.

The separate EU-27 calculation uses only Fraunhofer’s August 2025 inventory.
Its two cases assume no qualified wafer arrivals or enough arrivals to
fill the reported operating cell rate. Both assume no stocks or other
imported intermediates, full use of compatible active lines and unit yields.
These are boundary cases, with no observed importer share or arrival rate.
The same builder writes both calculations to the evidence JSON.
