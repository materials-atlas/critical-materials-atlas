# Aluminium: claim and source audit

Evidence review dated 25 November 2026. The previous public page was an undated overview rendered by a
script from `out/aluminium_chain.json`. Its text, evidence file and builder are in version history (the
last commit before this review). The dated source library stays at its own address, unchanged.

Every source below was opened and read on 25 November 2026. The transcribed tables are in
`evidence_inputs.json`. The builder refuses to publish if the USGS country rows do not add to the
published world totals, or if a sentence on the page no longer matches the numbers.

| Previous claim or framing | Source and verification | Disposition |
| --- | --- | --- |
| "China's share jumps from ~16% at the mine to ~59% at the smelter"; a chart beside it showed 21%, 58% and 59%. | USGS 2026 edition, 2024: China 18.8% of bauxite, 60.2% of alumina, 60.4% of primary aluminium. The page's two sets of figures did not agree with each other. | **Corrected.** One table, one source, one year. |
| "Australia, Guinea and China each mine about a quarter." | USGS 2026 edition, 2024: Guinea 33.2%, Australia 23.4%, China 18.8%. | **Corrected.** |
| "The smelter, not the mine, is the chokepoint." | Production is most concentrated at refining and smelting (China 60%). Trade is most concentrated at the ore stage: Guinea 67% of traded bauxite, China 87% of imports (BACI, 2024, by weight). China exported 2.2% of its alumina and 0.6% of its primary metal in unwrought form. | **Qualified.** The page gives both measures and says which stage each applies to. |
| "Smelting went where power was cheapest"; "the chokepoint is the powerline, not the pit". | The OECD (2019) says energy can be up to 40% of cost, citing a 2012 producer document. The same study measured government support of USD 20 to 70 billion to 17 firms over 2013 to 2017, the five largest recipients taking 85%, most of that at the smelting stage; especially large in China and the Gulf Cooperation Council countries. No source opened separates the two effects. | **Narrowed.** The page reports both and says the split is not estimated. |
| "12–15 MWh to smelt one tonne", attributed to USGS ("newer plants ~12, older ~15"). | The USGS aluminium chapter has no energy statement. International Aluminium Institute, 2025: 13,880 kWh per tonne world average, from 13,203 in China to 15,746 in South America (alternating current). | **Replaced** with the industry series and its definition. |
| "Roughly what an average home uses in a year, per tonne of metal." | No source. | **Withdrawn.** |
| "Smelting is ~40% electricity by cost." | OECD (2019), p. 39: "energy can represent up to 40% of the costs of production for primary aluminium, depending on local power prices". | **Qualified** to "up to 40%", attributed. |
| "Smelting draws roughly three-fifths of its electricity from coal worldwide" (57%); "China's fleet is close to 90% coal-fired". | International Aluminium Institute, 2025: coal 49.8% of its reported world total and 68.9% in China; hydro 31.0% and 19.0%. The reported total covers about 94% of world output. | **Corrected.** |
| "~16 t CO2e per tonne"; "hydro ~4 t, coal past ~20 t"; "a 5× spread". | Not checked against a source in this review. | **Not carried forward.** Listed as open. |
| "Green aluminium commands a premium"; the EU carbon border adjustment "turns the power source into a trade variable". | Not checked against a source in this review. | **Not carried forward.** |
| "Recycled aluminium needs only about 5% of the electricity." | OECD (2019), footnote 25: "The industry estimates that recycling saves as much as 95% of the energy used in smelting aluminium". | **Attributed** as an industry estimate. |
| "Scrap is a huge, growing part of supply"; "the above-ground stock cushions the chokepoint"; "infinitely recyclable". | The industry association's flow model gives recycled metal as 35.8% of 2024 production (model output). No source measures a stock that can be drawn in an interruption. | **Replaced** by the model share; the cushion claim is withdrawn. |
| "Guinea holds the largest bauxite reserves (7.4 bn t)." | USGS 2026 edition: 7,400,000 thousand tonnes of a world 29,000,000. | **Supported.** |
| "Indonesia banned raw bauxite exports to force domestic refining." | USGS yearbooks: ban from June 2023; exports about 18 Mt (2022) and about 2 Mt (2023); output 30.4 Mt (2022), 9.9 Mt (2023) and an estimated 9.9 Mt (2024), consumed at home. BACI shows no Indonesian bauxite exports in 2024 and 4.2 Mt of alumina exports. | **Supported**, with dates and tonnages. |
| Map entry: "a potline freezes solid if power drops". | Not checked against a source in this review. | **Reworded** to the measured electricity use. |
| Trade notes: alumina "China and Australia lead"; bauxite "Guinea/Australia/Indonesia lead". | BACI 2024: China 5% of alumina exports; Indonesia no bauxite exports. | **Corrected** on the page. The notes inside the frozen extract are unchanged. |
| The page's social-card title was the headline of the defence chain. | A template slip. | **Corrected.** |
| A bauxite chart for 2019–2024 "from the atlas's own data". | The series stays in the atlas (bauxite profile). | **Dropped from this page**, which now tabulates the USGS edition directly. |

## Findings of this review

- **The 2023 bauxite tonnage in BACI is unreliable.** The Australia to China record is 14.35 Mt at USD 90
  per tonne, against 34.4 Mt at USD 30 (2022) and 40.3 Mt at USD 46 (2024). The value is in line with the
  other years. It makes Guinea's 2023 share of exports 79%. The page leaves 2023 out. The extract is
  unchanged.
- **BACI agrees with Shanghai Metals Market for 2024** (159.4 against 158.8 Mt of imports; 110.1 against
  110.2 Mt from Guinea). The article does not name its source. BACI does not agree as closely with
  Guinea's statistics institute, and the gap changes sign: the institute is 23 Mt below BACI for 2022,
  13 Mt below for 2023 and 16 Mt above for 2024.
- **Indonesian alumina does not reconcile.** BACI has 4.2 Mt of exports in 2024; USGS estimates output
  at 1.2 Mt, a figure unchanged since 2022. The page reports both.
- **A draft of this review gave Indonesia's 2023 bauxite output as 30 Mt**, the estimate in the 2023
  yearbook. The 2024 yearbook gives 30.4 Mt for 2022 and 9.9 Mt for 2023. Corrected before publication.
- **Three "share to China" figures exist with different denominators:** USGS 70% of Guinea's bauxite and
  alumina exports (no year given), Guinea's institute 86.7% of bauxite exports (apparently by value),
  and BACI 89.8% by weight. The page uses BACI and quotes the institute.
- **The bauxite totals are about 50% above the USGS rule of thumb** (3.0 tonnes per tonne of alumina
  against 2). The page reports this and does not explain it.
- **The industry association's China production figure differs between two of its own datasets** for
  2025 (44,219 thousand tonnes in the production series, 45,016 in the power dataset). The page uses the
  production series.
- **USGS US consumption figures are not comparable across editions.** The 2026 edition leaves exported
  scrap out of apparent consumption.

## What the screen is

A first-order exposure calculation on 2024 figures, labelled Modelled on the page. It removes a quarter
or a half of Guinea's shipments to China, converts the ore to alumina at China's implied 2024 ratio and
to metal at the industry survey ratio, and holds everything else fixed. It has no stocks, no substitution
and no probability.

## Additions after a second assessment · 25 November 2026

A second assessment asked for a stated research question, a comparison of production and export concentration, balances
for more countries than China, the dependence of smelting countries on imported alumina, electricity and capacity limits,
stocks, ore quality, and a historical test. The comparison of concentration was already on the page. The rest was added
as far as public sources allow.

| Addition | Basis | Limit |
| --- | --- | --- |
| Three questions with their answers, and a chart of the two concentration indices. | The production and export indices already in the stage table. | The production bar is drawn at the middle of the published range. |
| Alumina made, imported and exported by each of the twelve smelting countries USGS lists by name; the largest supplier in 2024 and in 2019; a chart of origins. | USGS 2026 tables for metal and alumina output; BACI tonnage for HS 281820 by partner (`extract_tonnage.py`, block `partners`). | HS 281820 mixes smelter-grade and other alumina. "Not listed" means USGS groups the country with others. Three rows are more than a tenth away from the survey ratio of 1.91 and are named. Only the five largest suppliers are kept, so a smaller supplier counts as "other". |
| "Eight of the eleven named smelting countries outside China import more than half of their alumina", 53% of primary output outside China. | The table above. | Imports as a share of output plus imports; exports are not netted out of the share. |
| The United Arab Emirates bauxite record is incomplete in 2024. | BACI: 0.4 Mt of bauxite imports in 2024 and none from Guinea, against 10.7 Mt from Guinea in 2023; USGS alumina output of 2.5 Mt. | The record is left unchanged. It may account for part of the gap between Guinea's export figure and BACI; the size is not known. |
| A recorded interruption: Brazil, 2018. | USGS 2019 and 2020 editions (the order of February 2018, the lifting in May 2019, output of 10.9 and 8.1 Mt); BACI alumina exports of Brazil and imports of Norway and Canada by origin, 2017 and 2018. | USGS does not name the refinery. 2018 figures are the final ones of the Minerals Yearbook 2022 (Brazil alumina 8,258 kt; metal: Brazil 659, Norway 1,295, Canada 2,923 kt). Brazil's own metal output fell 18%. Prices are not examined. The Canadian figures are reported without a causal reading. |
| Unused capacity by country, 2024. | USGS 2026 edition, output and year-end capacity. | Year-end capacity against annual output; an upper limit on what could return. |
| Restarts, the EU and US statements, and the Chinese capacity limit. | Company releases and filings, the European Commission action plan of March 2025, USGS, the Chinese plan for 2025 to 2027, Xinhua. | Company statements. Alumar's 268,000 t is one owner's share of a 447,000 t plant. Hawesville has been sold (Century Aluminum, third-quarter 2026 results). The Chinese plan states no figure for the ceiling; 45 Mt comes from the state news agency, which cites no document. |
| Stocks. | Mysteel surveys for China (trade press), the Shanghai exchange report, London Metal Exchange stock as republished by a metal trader, USGS. | The Chinese figures are surveys with unstated coverage; dates differ from the 2024 flows they are set beside. The North American figure covers ingot, mill products and scrap held by producers. |
| Ore grade. | Reserve statements of three mining companies; the Indian mines bureau; the Guinean ministry's export-quality table for the first quarter of 2025. | Reserve grades, on two bases, are not shipment averages. The one ratio stated on the page compares two deposits within one company's statement. The Guinean table does not state its basis. Nothing was found for Chinese ore or Indonesia. |

A second reading of the additions against the source documents, same day, led to these changes before publication. The
San Ciprián row now carries its later status (about 65% at the end of 2025, after a pause). The sentence that idle capacity
returns "over years and not months" was replaced, because a single line at Lista returned within a year. The 2018 case no
longer says the loss was absorbed: Norway's imports were made up, and Brazil's own metal output fell. Port stocks are
described as of the same order as the ore removed in the screen, not as more than it. The grade comparison now uses two
deposits reported by one company. Two rows of the supply table are flagged as below the chemical minimum of alumina per
tonne of metal. The section heading says "smelting countries" and not "smelters".

Looked for and not found: a USGS table of smelters with their status; EU curtailed or restarted tonnage; refinery stocks of
bauxite in China; the alumina content of Chinese domestic ore as a percentage; bauxite per tonne of alumina by refinery;
moisture by origin other than Guinea.

Not done: a physically reconciled country-to-country flow model; plant-level capacity and power-cost modelling; a
disruption model with substitution; an expert review. The page's interruption screen remains a first-order calculation.

## Not done at the first review

- No aluminium content of bauxite by origin.
- No stocks of bauxite or alumina.
- No capacity or cost model of smelter location.
- No carbon intensity by power source.
- No aluminium embedded in finished goods.
- The exact day of the Indonesian ban (10 June 2023 in the USGS yearbook) was not read in an Indonesian
  official text; the page gives the month.
