# Sources and production record

## USGS historical series

Local source: `raw/usgs_hist/rare-earths.xlsx`, sheet `Rare earths`, last modified 27 September 2023. The pilot reads the published world-production column for 1900–2020. Unit: metric tonnes of rare-earth-oxide equivalent. It supplies scale only.

## BGS country panel

Official source: BGS World Mineral Statistics OGC API, collection `world-mineral-statistics`. Filter:

```text
erml_group = "Rare earths" AND bgs_statistic_type_trans = "Production"
```

`fetch_bgs.py` stores 274 observations for 1992–2024 in `raw/bgs_rare_earth_oxides_1992_2024.json`. BGS describes these as reported or calculated rare-earth-oxide equivalent and warns that evidence is insufficient for some producing countries. This is an all-REE series.

## IEA magnet chain

The IEA's *Rare Earth Elements* executive summary identifies Nd, Pr, Dy and Tb as magnet rare earths and reports China's 2024 shares as 60% of mining, 91% of separation/refining and 94% of sintered permanent-magnet production. It also reports that China's sintered-magnet production share rose from about 50% in 2005 to 94% in 2024. These are physical-market shares and two historical anchors, respectively.

## Global BACI trade

`extract_baci.py` reads the local CEPII BACI V202601 archives using HS02 for 2002–2016 and HS17 for 2017–2024. Values are BACI `v × 1000` US dollars. The extracted baskets are:

- 280530: rare-earth metals, scandium and yttrium, including mixtures/interalloys;
- 284690: non-cerium rare-earth compounds, including scandium, yttrium and mixtures;
- 850511: permanent magnets of metal, including rare-earth and non-rare-earth chemistries.

## EU Comext origin

The local Eurostat SDMX-CSV files contain CN 85051110, rare-earth permanent magnets. The calculation sums EU-27 reporters, removes EU partners and aggregate partner codes, and treats the extra-EU partner field as origin. Quantity in 100 kg is divided by ten for tonnes. The complete 2024 result is 92.72% China by value and 91.10% by quantity. The latest 2025 observations are retained as provisional.
