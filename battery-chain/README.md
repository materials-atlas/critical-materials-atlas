# Lithium-ion battery chain pilot (unpublished)

This workspace follows the product chain:

`minerals → battery-grade refining → cathode/anode materials → cells → packs → use/recovery`

It is not linked from the live Atlas and does not modify the lithium, cobalt, nickel, graphite or manganese profiles.

## Evidence design

| Layer | Coverage | Measure |
|---|---|---|
| Mineral history | 1900–2022, varying | USGS world output across all end uses |
| Battery demand shift | 2017 / 2022 | EV-battery share of mineral demand |
| Global customs context | 2017–2024 | BACI HS17 trade value and exporters |
| Mine versus refine | 2023 | Rounded IEA physical-production shares |
| Chemistry | 2022 / 2024 | LFP share of EV battery deployment |
| Cell capacity | 2024 | Nameplate capacity, output and demand |
| Downstream production | 2025 | Cathode, anode, cells and electric cars |

The page does not create a composite battery-dependency score. Chemistry and measurement boundaries change along the chain.

## Rebuild and view

```text
python battery-chain/record_battery.py
python battery-chain/extract_baci.py
python -m http.server 8765
```

Open `http://localhost:8765/battery-chain/battery-chain.html`.
