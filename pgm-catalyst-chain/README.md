# Platinum, palladium and rhodium have different supply maps

The [research note](pgm-catalyst-chain.html) sets out mine production, recycling, demand and customs
coverage for each metal separately. The [claim register](PRODUCTION.md) records the audit of the previous
page.

Run `python pgm-catalyst-chain/record_pgm.py` from the repository root. The builder needs no network
access. It reads:

- `evidence_inputs.json`: the USGS and Johnson Matthey tables as transcribed and checked on 25 November 2026, with source links;
- `article.html.in`: the page text;
- `out/pgm_trade.json`: the frozen BACI extract written by `extract_baci.py`;
- the atlas's `out/mined_years.json`, for the BGS all-PGM series quoted in the correction.

It writes the page and `out/pgm_chain.json` (inputs, results and the chokepoint-map entry).

## Calculations

- USGS shares divide each country's 2024 mine production by the published world total. No 2025 shares are shown because USGS rounds the 2025 totals to two figures.
- Reserve shares are of the countries listed (76,200 tonnes); USGS prints the world figure as "more than 76,000".
- The concentration index (HHI) is given as a range: the grouped "other countries" row counted as fully dispersed, or as one producer.
- Johnson Matthey figures are stored in thousand troy ounces and shown in tonnes (1,000 oz = 0.0311035 t).
- Recycled share = open-market recycling divided by primary plus recycled supply.
- Supply screen = half of a country's 2025 primary sales divided by 2025 demand.
- Demand screen = 2025 movement in stocks plus the assumed cut in automotive demand.

The builder stops if the Johnson Matthey sector figures do not add to the published totals, if the six
flagged trade records no longer explain the palladium tonnage outliers, or if the summary sentence on a
quarter-lower automotive demand no longer matches the screen.
