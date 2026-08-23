# Electricity-grid chain pilot (unpublished)

This workspace follows the product chain:

`metals and steel → conductors and cores → equipment → network assets → power system → renewal`

It is not linked from the live Atlas and does not modify the copper profile or any other live page.

## Evidence design

| Layer | Coverage | Measure |
|---|---|---|
| Material scale | 1900–2020/21 | USGS world copper and primary-aluminium production |
| Customs context | 2002–2024 | BACI grouped conductor, electrical-steel, transformer and cable baskets |
| Investment | 2015–2021 / 2024 / 2030 | Published IEA anchors, not an interpolated series |
| Network task | Baseline published 2023; task to 2040 | Existing versus added-or-refurbished line length |
| Transformer pressure | 2019–2025 evidence | Global procurement/cost indicators and a separate US distribution case |
| Engineering choice | Historical and current evidence | Copper/aluminium conductor trade-offs |

## Rebuild and view

```text
python grid-chain/record_grid.py
python grid-chain/extract_baci.py
python -m http.server 8765
```

Open `http://localhost:8765/grid-chain/grid-chain.html`.

