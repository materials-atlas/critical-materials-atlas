# Niobium has one main source; for steel's other alloying metals, exposure depends on the buyer

The [research note](steel-alloys-chain.html) sets out where six alloying metals of steel are mined, where the
alloys are made and where six importing markets buy them, and reports what public sources say about use,
substitution and the main inputs of steel. The [claim register](PRODUCTION.md) records the audit of the previous page.

Run `python steel-alloys-chain/record_steel.py` from the repository root. The builder needs no network access. It reads:

- `evidence_inputs.json`: USGS tables and quotations, company and association figures, as transcribed and checked on 25 November 2026, with source links;
- `article.html.in`: the page text;
- `out/steel_exposure.json`: trade by weight and each market's suppliers, written by `extract_exposure.py` from the local BACI extract;
- `out/steel_trade.json`: trade by value, written by `extract_baci.py`.

It writes the page and `out/steel_chain.json` (inputs, results and the chokepoint-map entry).

## Calculations

- Mine shares divide each country's 2024 figure by the published USGS world total, in the unit of each chapter.
- Trade shares are by customs net weight from BACI, for 2024, with 2019 for comparison. Ferrochromium is HS 720241 plus 720249. Ferromanganese is 720211, 720219 and 720230 (ferrosilicomanganese). Ferronickel is 720260, which includes nickel pig iron.
- A market's share from the leading world exporter = that exporter's tonnage in the market's imports divided by the market's total imports. The EU is the 27 member states as one market; trade between them is left out.
- China's 2023 ferrochromium share divides the USGS country figure by the USGS world total. The 2025 figure sums the regional figures of the industry association, which prints no total.
- Grams of niobium per tonne of steel = per cent by weight times 10,000.

The builder stops if country rows do not add to the world totals, or if any sentence that states a result in
words no longer matches the data.
