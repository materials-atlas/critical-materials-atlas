# Semiconductor evidence ledger

This file records exactly what each production-side source supports. Machine-
readable values and full URLs are in `out/semiconductor_chain.json`, generated
by `record_semiconductor.py`.

## 1. Silicon metal

OECD reports that China accounts for about 85% of global silicon-metal
production in the current supply structure. The BACI series for HS 280469
(2002–2024) is retained as trade context, not substituted for production.

## 2. Electronic-grade polysilicon

- Semiconductor-grade material is at least 11N purity; solar material is
  generally 6N–10N (SIA, 2025).
- IEA-PVPS reports 38.8 thousand tonnes for semiconductor use in 2023 within
  its broader polysilicon-production accounting.
- SIA forecasts 33.5 thousand tonnes of semiconductor demand in 2025, only
  2.4% of all polysilicon demand.
- OECD places roughly 65% of semiconductor-grade production in Germany and
  the United States combined and less than 10% in China.
- SIA identifies five major suppliers—Wacker, Hemlock, Tokuyama, SUMCO, and
  OCI—and estimates Wacker plus Hemlock at about 75% of the market.

These are dated snapshots, not a constructed annual country series. HS 280461
cannot fill the gap because it combines solar and semiconductor grades; SIA
explicitly warns that the tariff line cannot distinguish the two.

## 3. Blank semiconductor wafers

- SEMI's annual silicon shipment series covers semiconductor applications and
  explicitly excludes solar. The pilot records worldwide shipment area and
  nominal revenue for every year from 2007 through 2025.
- OECD reports that Shin-Etsu Handotai and SUMCO together supply more than half
  of the market.
- SIA reports that six firms supply about 92% of the global blank-wafer market.
- OECD places at least 85% of semiconductor-grade wafer production across
  Japan, Germany, Korea, the United States, and Taiwan.

The shipment series is global, not a country-production series. HS 381800 is
shown only as mixed trade context because it does not isolate blank silicon
semiconductor wafers.

## 4. Front-end wafer fabrication

### Long geography, 1990–2032F

SIA/BCG Exhibit 7 supplies eleven regional snapshots of commercial fab
capacity. The scope is fabs using wafers of 200 mm or larger, normalized to
300 mm-equivalent wafer starts per month; facilities below 5,000 WSPM are
excluded. Values from 2025 onward are forecasts and are visually dashed.

### Physical capacity by chip type, September 2025

OECD's World Fab Forecast analysis assigns capacity to the physical fab—not
the owner's headquarters—and normalizes it to 8-inch-equivalent wafer starts
per month. The pilot records the three largest economies for power/discrete,
analog, mature logic, advanced logic, commodity memory, and specialty memory.
The leading economy differs by chip category.

## Source set

- IEA-PVPS, *Trends in Photovoltaic Applications 2024*.
- OECD, *Mapping the Semiconductor Value Chain* (2025).
- OECD, *The Chip Landscape* (2025).
- OECD, *Due Diligence for Responsible Sand and Silicate Supply Chains* (2026).
- Semiconductor Industry Association, polysilicon Section 232 comments (2025).
- SIA/BCG, *Emerging Resilience in the Semiconductor Supply Chain* (2024).
- SEMI annual silicon-wafer shipment releases covering 2007–2025.

The generated JSON is the canonical source ledger: each observation or block
points to a source identifier with title, year, and URL.
