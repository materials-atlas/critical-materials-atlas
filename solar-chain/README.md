# Solar manufacturing chain pilot (unpublished)

This workspace applies the product-chain method to solar photovoltaics:

`silicon metal → PV polysilicon → ingots/wafers → cells → modules → systems`

It is not linked from the live Atlas and does not alter the 32 material
profiles. The semiconductor pilot remains separate in `silicon-chip/`.

## Evidence design

The page does not force unlike data into one line:

| Layer | Coverage | Measure |
|---|---|---|
| Module-production geography | 1990–2025 | Regional production shares |
| Broad customs context | 2002–2024 | Annual trade value and exporters |
| Silicon intensity | 2004 / 2024 | Grams per watt-peak |
| Manufacturing capacity | 2010 / 2021 / 2024 | Nameplate capacity shares |
| Physical stage production | 2023 | Actual output by stage |

The long module series is the historical backbone. The 2010 and 2021 IEA
matrices provide the cleanest like-for-like view of how concentration moved
upstream. The 2023 IEA-PVPS table supplies physical production. Each remains a
separate measure.

## Files

- `record_solar.py` builds `out/solar_chain.json`.
- `solar-chain.html` is the unpublished interactive page.
- `PRODUCTION.md` records sources, measures, and exact claims.
- `NOTES.md` records the interpretation and exclusions.
- `../silicon-chip/extract_baci.py` builds the shared BACI context, including
  broad code 854140.

## Rebuild and view

From the repository root:

```text
python solar-chain/record_solar.py
python silicon-chip/extract_baci.py
python -m http.server 8765
```

Open `http://localhost:8765/solar-chain/solar-chain.html`.

