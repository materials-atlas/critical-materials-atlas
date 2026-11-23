# Data-centre deployment study

Evidence and model version dated 24 November 2026. The
[claim register](PRODUCTION.md) audits the previous article, records the
sources and grades each use of evidence. The [article](data-centre-chain.html)
includes its findings and tables in the initial HTML. The trade controls
let readers explore older years after the data load.

## Reproduce the article

From the repository root:

```text
python data-centre-chain/record_data_centre.py
python -m http.server 8765
```

Open [the local study](http://localhost:8765/data-centre-chain/data-centre-chain.html).
The builder uses [article.html.in](article.html.in), the checked-in transformer
study and the published [customs extract](out/data_centre_trade.json). It writes
the static article and [machine-readable evidence](out/data_centre_chain.json).
The customs extract uses CEPII BACI V202601, HS02 through 2016 and HS17 from
2017. The central `build_chain_trade.py` regenerates the customs data with the
original archives available.

## Commissioning model

The [assumptions](deployment_assumptions.json) give the activity IDs, durations,
prerequisites, capacity assumptions and scenario changes. Every duration is
illustrative and measured in whole months from the assumed project start.
The records from Memphis and Iver document individual milestones and do not
supply those durations.

```text
python data-centre-chain/project_readiness.py
```

The script prints each activity's start and finish, the commissioning month,
its calendar equivalent, critical activities, usable IT MW and the change
relative to the indicated comparator. Its inputs and schedule algorithm
are independent of the article renderer.

- **Boundary.** An accelerator-heavy data-centre phase with 100 MW of planned
  IT load in an unspecified region. Accelerator logic and high-bandwidth
  memory enter packaging before server delivery. The model allows work on
  the facility, equipment and utility connection to overlap. It assumes
  qualifying conditions for electrical and integrated acceptance.
- **Power.** A design PUE of 1.25 approximates facility overhead at design load,
  giving a requirement of 125 MW of facility power for 100 MW of IT load.
  Usable IT capacity at commissioning is the minimum of installed IT power,
  cooling capacity, target IT load and deliverable firm power divided by
  design PUE. This simplifies how facility overhead varies with load. The
  capacity calculation does not estimate annual electricity consumption.
- **Schedule.** A task starts at the latest finish among its prerequisites,
  or month zero when it has none. Its finish is that start plus its duration.
  Integrated commissioning waits for electrical acceptance, cooling and
  server and network installation. Tasks on tied longest paths all count as
  critical. The model assumes permits and equipment specifications stay
  compatible with the build and has no resource-sharing or financing model.
- **Reliability.** Uninterruptible and backup power are assumed and tested as
  part of the phase. Firm power denotes service deliverable under the assumed
  utility agreement. The model does not assign an uptime target or a
  redundancy class and gives no workload throughput forecast.
- **Sensitivity.** The schedule tests all combinations of the input grid,
  transformer and memory duration values. The displayed range is the minimum
  and maximum across combinations. There is no statistical weighting. The
  PUE comparison varies facility overhead independently. The reduced-power
  example assumes approval at the reduced capacity on the same schedule.

See [research notes](NOTES.md) for boundaries when interpreting the trade
and demand evidence.
