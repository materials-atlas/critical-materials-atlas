# Data-centre and AI-infrastructure pilot

Unpublished research page separating chips, servers, IT load, facility systems, grid connection, annual electricity, digital services, materials and trade. It is isolated from the live Atlas and carries `noindex,nofollow`.

## Build

From the repository root:

```powershell
python data-centre-chain/record_data_centre.py
python data-centre-chain/extract_baci.py
python -m http.server 8765
```

Open `http://localhost:8765/data-centre-chain/data-centre-chain.html`.

## Outputs

- `out/data_centre_chain.json`: energy, equipment, grid, scenario and material evidence.
- `out/data_centre_trade.json`: BACI 2002–2024 mixed-use equipment context.

See [NOTES.md](NOTES.md) for scope warnings and [PRODUCTION.md](PRODUCTION.md) before any publication decision.
