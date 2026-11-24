# Grid transformer evidence

Release dated 24 November 2026. The linked research products are the
[transformer procurement working paper](grid-chain.html) and the
[EU supplier-exposure analysis](../grid-trade.html#supplier-exposure).
The [claim register](PRODUCTION.md) records the original claims and source
audit. The [methods annex](NOTES.md) explains the calculations and limits.

## Rebuild and view

Run from the repository root.

```text
python grid-chain/record_grid.py
python build_grid_trade_paper.py
python build_chokepoint_map.py
python -m http.server 8765
```

Open [the local working paper](http://localhost:8765/grid-chain/grid-chain.html)
or [the companion analysis](http://localhost:8765/grid-trade.html#supplier-exposure).
The core article and latest trade table are in the initial HTML. The trade
year picker uses the existing checked-in extraction.

## Replicate data and estimates

The committed results build offline. For a new source check, run
`python eu-grid-supply/audit_eurostat.py` to fetch the public Eurostat tables.
That command replaces the audit input with the latest Eurostat vintage.
The dated September study inputs stay in `out/eu_grid_supply.json` and
`out/buildout_study.json`.

To repeat the raw BACI checks, use the official V202601 HS17 and HS02
archives and country codes with the Atlas extractor. Extract HS17 for
2019–2024 and HS02 for 2012–2024. An external data root can be set with
`ATLAS_ROOT`. Then run:

```text
python grid-chain/build_goes.py
python grid-chain/replicate_transformers.py
```

The GOES builder produces annual exporter shares by value and by recorded
tonnage. The transformer replication reuses the filed estimation and
event-study routines for the two headline comparison groups. The
regression evidence records whether the coefficient estimates and sample
sizes match the September results. Material-adjusted, regional and other
ancillary regressions remain in the dated source files.
