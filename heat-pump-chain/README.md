# Heat-pump and refrigeration-chain pilot

Unpublished research page separating heat-pump sales, installed stock, factory capacity, technology types, components, refrigerants, installation and trade. It is isolated from the live Atlas and carries `noindex,nofollow`.

## Build

From the repository root:

```powershell
python heat-pump-chain/record_heat_pump.py
python heat-pump-chain/extract_baci.py
python -m http.server 8765
```

Open `http://localhost:8765/heat-pump-chain/heat-pump-chain.html`.

## Outputs

- `out/heat_pump_chain.json`: sourced market, manufacturing, refrigerant, technology and material evidence.
- `out/heat_pump_trade.json`: BACI 2002–2024 customs context.

See [NOTES.md](NOTES.md) for scope warnings and [PRODUCTION.md](PRODUCTION.md) for publication requirements.
