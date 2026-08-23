# Nuclear fuel-chain pilot

Unpublished research page separating uranium mining, conversion, enrichment, fuel fabrication, reactor operation and the back end. It is deliberately isolated from the live Atlas and carries `noindex,nofollow`.

## Build

From the repository root:

```powershell
python nuclear-chain/record_nuclear.py
python nuclear-chain/extract_baci.py
python -m http.server 8765
```

Then open `http://localhost:8765/nuclear-chain/nuclear-chain.html`.

## Outputs

- `out/nuclear_chain.json`: sourced fleet, uranium, fuel-cycle and material evidence.
- `out/nuclear_trade.json`: BACI 2002–2024 customs context.

The page does not alter existing material profiles or site navigation. See [NOTES.md](NOTES.md) for interpretive limits and [PRODUCTION.md](PRODUCTION.md) for publication requirements.
