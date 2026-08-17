# Rare-earth permanent-magnet chain pilot (unpublished)

This workspace applies the product-chain method to high-performance permanent magnets:

`mine → concentrate → separate Nd/Pr/Dy/Tb → metal/alloy → magnet → motor/generator`

It is not linked from the live Atlas and does not modify `profile-magnets.html`.

## Evidence design

| Layer | Coverage | Measure |
|---|---|---|
| World production scale | 1900–2020 | USGS all-REE output, oxide equivalent |
| Mining geography | 1992–2024 | BGS all-REE output by producing country |
| Broad global trade | 2002–2024 | BACI export value for three HS6 baskets |
| Magnet manufacturing | 2005 / 2024 | IEA China-share anchors |
| EU rare-earth magnets | 2023–2025 | Comext CN8 extra-EU imports by origin; 2025 provisional |
| Physical bottleneck | 2024 | IEA magnet-REE mining, refining and sintered magnets |

The two mine series overlap but are not spliced. Production and customs shares are never combined into a synthetic dependency score.

## Rebuild and view

From the repository root:

```text
python magnet-chain/fetch_bgs.py       # only when refreshing the official raw panel
python magnet-chain/extract_baci.py    # scans the existing BACI archives
python magnet-chain/record_magnets.py
python -m http.server 8765
```

Open `http://localhost:8765/magnet-chain/magnet-chain.html`.
