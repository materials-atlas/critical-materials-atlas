# Aluminium production is concentrated in China, and bauxite trade in Guinea

The [research note](aluminium-chain.html) sets out production and trade at each stage from bauxite to
metal, checks whether the published tonnages fit together, and reports what public sources say about
electricity and recycling. The [claim register](PRODUCTION.md) records the audit of the previous page.

Run `python aluminium-chain/record_aluminium.py` from the repository root. The builder needs no network
access. It reads:

- `evidence_inputs.json`: the USGS, International Aluminium Institute and OECD figures as transcribed and checked on 25 November 2026, with source links;
- `article.html.in`: the page text;
- `out/aluminium_tonnage.json`: trade by weight, written by `extract_tonnage.py` from the local BACI extract;
- `out/aluminium_trade.json`: trade by value, written by `extract_baci.py`.

It writes the page and `out/aluminium_chain.json` (inputs, results and the chokepoint-map entry).

## Calculations

- Production shares divide each country's 2024 figure by the published USGS world total. The world bauxite total excludes the United States.
- The concentration index (HHI, zero to 10,000) for production is a range: the grouped "other countries" row counted as fully dispersed, or as one producer.
- Trade shares are by customs net weight from BACI. Unwrought aluminium is HS 760110 plus 760120. Semi-finished aluminium is every six-digit code under HS 7604 to 7608.
- Traded as share of produced = BACI world trade divided by USGS world production. Approximate: customs weight can include moisture, and unwrought metal in trade includes alloys and remelted metal.
- China's bauxite supply = USGS domestic output plus BACI imports.
- Implied ratios: bauxite per tonne of alumina = bauxite output (plus net imports for China) divided by alumina output. Alumina per tonne of aluminium, world = International Aluminium Institute smelter-grade alumina divided by its primary aluminium figure; for China, USGS alumina plus net imports divided by USGS primary metal.
- Screen = a fraction of Guinea's shipments to China, divided by China's implied bauxite-to-alumina ratio, then by 1.909 tonnes of alumina per tonne of metal.
- Power shares = each source's gigawatt-hours divided by the total, 2025.
- Capacity use = 2024 production divided by year-end 2024 capacity.
- Alumina supply of a smelting country = USGS alumina output plus BACI imports of HS 281820. Imports as a share of supply = imports divided by that sum. Alumina available per tonne of metal = (output plus imports less exports) divided by USGS primary metal output; a row is flagged when it is more than a tenth away from 1.909.
- Brazil, 2018 = BACI exports of HS 281820 from Brazil, and imports of Norway and Canada by origin, in 2017 and 2018.
- Unused capacity = year-end 2024 capacity less 2024 output, zero where negative.
- Stock comparisons divide a stock at its own date by a 2024 flow (imports, output) and are for scale only.

The builder stops if the country rows do not add to the world totals, if the power sources do not add to
their total, or if any of the sentences that state a number in words no longer matches the data. It also
stops if the 2023 bauxite record changes, so that the note on that year is reviewed.
