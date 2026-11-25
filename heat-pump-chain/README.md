# Heat-pump manufacturing and compressor supply

Evidence review dated 25 November 2026. The [article](heat-pump-chain.html)
combines published manufacturing benchmarks, a conditional compressor
interruption and the existing BACI finished-equipment trade series. The
[claim register](PRODUCTION.md) records the source locations and revisions to
the original pilot.

## Reproduce the study

From the repository root:

```text
python heat-pump-chain/record_heat_pump.py
python heat-pump-chain/test_compressor_supply.py
python -m http.server 8765
```

Open [the local article](http://localhost:8765/heat-pump-chain/heat-pump-chain.html).
The builder reads the [inputs](evidence_inputs.json), the [template](article.html.in)
and the [checked-in trade data](out/heat_pump_trade.json). It writes the article
and the [evidence JSON](out/heat_pump_chain.json). The core tables are in the
initial HTML. JavaScript enables the customs year control. With the original
BACI archives available, the Atlas trade builder regenerates the frozen trade
series. See [scope notes](NOTES.md) and the [research library](library.html).

## Manufacturing benchmark

The IEA and JRC have separate technology and capacity definitions. For the
JRC comparison, multiply its mixed-technology EU nameplate estimate of
7.7 million units per year by its assumed 10 kW per unit to reproduce
77 GW of thermal nameplate per year. Hold that rate constant for comparison
with the JRC’s rounded flat annual benchmark and its growth-path requirement
for 2030. The ratio is a nameplate comparison and leaves utilisation,
technology mix and supplier availability unmeasured.

## Monthly compressor balance

The study follows one hypothetical EU-27 residential air-to-water design.
Counts are per month and shipments may be used as they arrive. Shock losses
are the exposed import units multiplied by the loss rate and rounded down
to whole compressors. During the shock, replacement arrivals are limited
by the missing deliveries and the eligible replacement rate. A delay of
three months makes additional compressors available starting in month four.
Regular supplies resume in the month after the interruption ends.

Production is the minimum of orders, assembly capacity and available
compressors divided by compressors per heat pump, rounded down. Opening
stock and receipts minus the compressors used gives closing stock. The next
month starts with that balance. Orders are counted in the month due and
the model has no backlog. Shock loss is the difference in total production
from the same case with normal receipts and the same demand, capacity and
opening stock. Unmet orders are a separate output.

The sensitivity calculation reruns all listed opening inventory, qualification
delay, qualified replacement capacity and monthly orders combinations.
The in-page grid holds qualified replacement capacity and demand at the
point settings. The evidence JSON carries all combinations and each
intervention’s monthly balances. These calculations use assumed deliveries,
compatibility and qualification times. Procurement data, plant availability,
installation and operating costs would be needed to assess an actual shock.
