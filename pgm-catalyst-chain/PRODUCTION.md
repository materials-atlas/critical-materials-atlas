# Platinum-group metals: claim and source audit

Evidence review dated 25 November 2026. The previous public page was an undated overview rendered by a
script from `out/pgm_chain.json`. Its text, evidence file and builder are in version history (the last
commit before this review). The dated source library stays at its own address, unchanged.

Every source below was opened and read on 25 November 2026. The transcribed tables are in
`evidence_inputs.json`; the builder refuses to publish if the Johnson Matthey sector figures do not add
to their published totals.

| Previous claim or framing | Source and verification | Disposition |
| --- | --- | --- |
| A chart titled "Platinum mine production: a two-country base, 2000–2024", South Africa 47% (2000) to 57% (2024), Russia 46% to 24%. | The series is the atlas's BGS line "platinum group metals, mine" (`build_bgs_mined.py`), all six metals added together. USGS editions give platinum alone: South Africa 73.5% (2000), 77.9% (2005), 77.1% (2010), 73.5% (2015), 67.5% (2020), 70.4% (2024); Russia 19.4% to 12.3%. | **Corrected.** The page now tabulates platinum and palladium separately from USGS and says what the earlier series was. |
| "South Africa held ~57–60% throughout." | The same series starts at 47% in 2000. | **Withdrawn.** Inconsistent with its own data. |
| "Their mine supply comes from essentially two places"; "essentially the only two large mine sources". | USGS 2026 edition, 2024: South Africa plus Russia mined 82.7% of platinum and 79.1% of palladium. Zimbabwe 10.3% and 7.0%, Canada 3.2% and 7.8%, United States 1.7% and 4.7%. | **Qualified.** Two countries mine about four-fifths; the page gives every listed country. |
| "South Africa leads platinum (~71% of mine output)." | USGS 2026 edition: 126,000 of 179,000 kg in 2024, 70.4%. Johnson Matthey 2025 producer sales: 71.2%. | **Supported.** Both figures are shown with their definitions. |
| "Palladium is Russia-led"; "Russia and South Africa co-lead". | USGS: Russia 41.0%, South Africa 38.1% in 2024. Johnson Matthey 2025 sales: Russia 44.8%, South Africa 34.1%. | **Supported**, with the year-by-year table added (Russia 54% in 2000). |
| "~83% of world PGM reserves are in South Africa", labelled measured. | USGS 2026 edition: 63,000,000 of the 76,200,000 kg listed by country, 82.7%; world printed as "more than 76,000,000". Reserves were revised between editions (Russia 16,000,000 to 11,000,000 kg). | **Supported**, now with the denominator and the revision stated. |
| "~1/4+ of supply comes back as recycled catalytic-converter scrap." | Johnson Matthey 2025, open-market recycling as a share of supply: platinum 21.8%, palladium 32.2%, rhodium 30.8%. Vehicle scrap is 73%, 85% and 100% of that. | **Replaced** by the three measured shares and the definition (open-loop only). |
| "A supply shock is cushioned by an above-ground stock that grows every year"; "stock-in-use is a hidden reserve". | No source measures a stock that can be drawn in a shock. The industry association puts vehicle end of life at 15–18 years; Johnson Matthey reports weak recycling in 2023–24 because vehicles were kept longer. | **Withdrawn.** The page says recycled volume follows past sales and scrappage, not a current shortage. |
| "The real threat is demand, not supply"; "a structural demand cliff". | Johnson Matthey: all three metals were in deficit in 2025. Automotive share of demand: platinum 41.5%, palladium 81.1%, rhodium 84.6%. No source ranks the two risks. | **Replaced** by a labelled screen of the market balance at lower automotive demand, with its two omitted effects named. |
| "Unlike gallium or germanium, PGMs are not a processing chokepoint." | No public source gives refining capacity by country for these metals. | **Narrowed.** The page lists refining capacity as an open question and makes no claim about it. |
| The trade panel reads catalyst trade from HS 711510. | WCO HS 2017: 7115.10 is "catalysts in the form of wire cloth or grill, of platinum" (any PGM, Chapter Note 4(B)). Converters sat in 8421.39 until HS 2022 created 8421.32; supported catalysts are 38.15. | **Corrected.** The page says the four codes exclude vehicle converters. |
| Palladium trade tonnage (HS 711021) of 3,923 t in 2002 and 5,255 t in 2009. | Six bilateral records in the BACI extract carry about USD 0.01 per gram: five imports into Canada in 2002 (from the United Kingdom, South Africa, Belgium, Russia, Norway) and United Kingdom to Cyprus in 2009. Without them: 442 t and 406 t, against 384–509 t in other years. | **Flagged.** The page uses values only and tells readers not to use tonnage for those years. The extract itself is unchanged. |
| The page carried `noindex,nofollow` while marked published. | Other published chain pages are indexable. | **Corrected** to `index,follow`. |

## What the two screens are

Both are first-order exposure calculations on the 2025 Johnson Matthey balance, labelled Modelled on the
page. The supply screen removes half of one country's primary sales and reports the loss as a share of
2025 demand. The demand screen lowers automotive demand by 10%, 25% and 50% and reports the balance. They
hold everything else fixed and carry no probability. They do not model mine economics, co-production,
refining capacity or the later fall in vehicle scrap.

## Not done

- No mine-level co-production model: whether lower palladium demand would cut platinum and rhodium output is untested.
- No refining capacity by country.
- No vehicle-fleet model of future scrap.
- Rhodium, iridium and ruthenium have no USGS mine production by country; their geography rests on producer-sales estimates.
- The BACI tonnage outliers are documented, not repaired.
- The atlas's BGS series labelled "platinum" in `out/mined_years.json` is the all-PGM line. It also feeds the year slider on the platinum profile. That label is a separate fix.
