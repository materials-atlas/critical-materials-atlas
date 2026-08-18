# Electrolyser and hydrogen chain pilot (unpublished)

This workspace follows:

`materials → stack → electrolyser system → hydrogen plant → conversion/transport → use/recovery`

It is isolated from the live Atlas and does not modify any existing material or product-chain page.

## Evidence design

| Layer | Coverage | Measure |
|---|---|---|
| Material context | 1900/1944–2019/22 | Economy-wide USGS world production histories |
| Electrolyser deployment | 2021–2025 | Operating water-electrolysis capacity |
| Project clocks | 2025–2030 | Operating, construction, committed and announced statuses |
| Manufacturing | 2021–2024 evidence | Factory capacity, output and domestic demand |
| Hydrogen system | 2025 | Total demand versus low-emissions production |
| Customs context | 2002–2024 | Broad equipment and material baskets; no clean electrolyser code |

## Rebuild and view

```text
python electrolyser-chain/record_electrolyser.py
python electrolyser-chain/extract_baci.py
python -m http.server 8765
```

Open `http://localhost:8765/electrolyser-chain/electrolyser-chain.html`.

