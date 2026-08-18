# Electric-vehicle chain pilot (unpublished)

This workspace follows:

`materials → components → electric powertrain → vehicle → use and charging → recovery`

It is isolated from the live Atlas. It does not modify the battery, magnet, semiconductor, copper or grid pilots.

## Longitudinal design

| Layer | Coverage | Measure |
|---|---|---|
| Electric-car deployment | 2010–2025 | IEA world sales and operating stock by powertrain |
| Customs context | 2002–2024 / 2017–2024 | Broad car/converter comparators and clean BEV/PHEV/battery baskets |
| Battery chemistry | 2020–2025 anchors | LFP share of EV battery deployment by capacity |
| Power electronics | 2017–2025 anchors | SiC demonstration and high-voltage market milestones |
| Vehicle design | 2020 / 2025 | Large-car and SUV model availability |
| Manufacturing | 2025 | Physical car and battery-chain output estimates |

## Rebuild and view

```text
python ev-chain/fetch_iea.py
python ev-chain/record_ev.py
python ev-chain/extract_baci.py
python -m http.server 8765
```

Open `http://localhost:8765/ev-chain/ev-chain.html`.
