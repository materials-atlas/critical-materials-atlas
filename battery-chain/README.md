# Battery input replacement

Evidence release dated 24 November 2026. The [study](battery-chain.html)
presents the production evidence and monthly comparison in the initial HTML.
The original trade extract supplies the year control and static snapshot.

## Reproduce the study

From the repository root:

```text
python battery-chain/record_battery.py
python build_chokepoint_map.py
python -m http.server 8765
```

Open [the local study](http://localhost:8765/battery-chain/battery-chain.html).
The builder reads [evidence and assumptions](evidence_inputs.json), the
[article template](article.html.in) and the [compiled trade data](out/battery_trade.json).
It writes the article and [evidence and results](out/battery_chain.json). The
repository can rebuild the checked-in customs baskets from its BACI inputs with
`build_chain_trade.py`.

The [claim register](PRODUCTION.md) records the original article and source
audit. The [model methods](NOTES.md) explain the mass balance, what was
verified and which operating data are still needed.

## Qualification follow-up

Added 24 November 2026. The [follow-up inputs](followup_inputs.json) pin the
supplier and customer disclosures, evidence classes and sensitivity settings.
The calendar begins in the month of the sample for the timing case. The
earliest month in the supplier's guided sales window gates replacement of
graphite alone. Guidance is subject to qualification. The other inputs remain
hypothetical. The gradual case multiplies the original qualified monthly
volume by the specified profile starting in its first eligible month. Once
at full ramp the volume is held there.

Run from the repository root.

```text
python battery-chain/record_battery.py
python battery-chain/test_replacement_model.py
```

The test regenerates both sets of model results from the input JSON. It
checks balances, carryover, eligibility gates, recovery timing and reported
losses. The dated supplement is in the `review_addendum` section of the
evidence JSON.
