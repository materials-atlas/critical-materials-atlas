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
