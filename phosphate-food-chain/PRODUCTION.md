# Phosphate chain evidence audit

Reviewed 25 November 2026. The [prior article][old-page], [evidence JSON][old-evidence] and [BACI extract][old-trade] point to the reviewed commit. The public JSON files matched that commit. The revised note uses the 2026 USGS edition for the mineral baseline and 2023–2024 for matched EU trade and use.

| Claim or input in the pilot | Finding and change |
| --- | --- |
| Reserve concentration establishes a binding constraint on food supply. | The inference is unsupported. The USGS country share describes an estimated reserve base. EU import origins are concentrated to different degrees by product. No concentration index establishes unavailable replacement supply or an effect on harvests. |
| Morocco has about 68% of reserves and 13% of mine output. | USGS MCS 2026 gives 50,000 / 73,000 Mt of reported rock reserves and 36 / 250 Mt of estimated 2025 rock output. Shares are 68.5% and 14.4%. China had 44.0% of output and 4.7% of reserves. The production entry for China covers large mines. [USGS MCS 2026] |
| The latest table explicitly includes Western Sahara in Morocco. | The table labels the entry Morocco and gives no separate Western Sahara value. Earlier USGS reporting combined the two. The revised note preserves the current table label and specifies that a split cannot be recovered. [USGS MCS 2026] · [USGS Minerals Yearbook] |
| All agricultural phosphorus depends immediately on newly mined rock. | Rock is the main primary input for mineral fertilizer. Soil phosphorus, manure and recovery also contribute. The crop nutrient and its source have separate substitution questions. [Barbieri et al. (2022)] |
| Annual use is 47.8 Mt and rises to about 52 Mt by 2028. | USGS labels 47.8 Mt as estimated 2025 consumption of P₂O₅ in fertilizers and projects 51.5 Mt in 2029. The revised analysis uses FAOSTAT agricultural use in 2023 and 2024, with its own denominator and coverage. The sources cannot be treated as one time series. [USGS MCS 2026] · [FAOSTAT RFN] |
| The original BGS/USGS chart confirms the historical trajectory of the reserve base. | The Atlas input is a share series for mine output. The pilot turned missing named shares into zero and had no historical reserve series. The revised note displays all named country rows in the current source vintage. |
| The five BACI codes represent the phosphate fertilizer chain. | The frozen extract represents unground phosphates, DAP, MAP and mixes, potassium chloride and elemental phosphorus. It omits ground rock, acid and other fertilizers. Potassium chloride and elemental phosphorus are separate comparators. Values are nominal. Missing quantities were carried as zero in its world mass aggregate, and the published file did not retain bilateral quantities. The historical value selector still uses the frozen extract. [BACI] |
| Code 310310 can be carried unchanged into a modern extract. | The WCO split it into 310311 and 310319 in HS 2017. The standalone Comext query uses corresponding CN8 codes in 2023 and 2024. The Atlas trade-engine code set is frozen. [WCO] |
| Product flows can be combined into total phosphorus trade. | Product weights are compared inside the stated customs groups. Only a DAP and MAP grade illustration converts them into elemental P. No measured grade distribution is available. Counting all stages can include the same phosphorus repeatedly. |
| Mine output implies the origin or availability of processed fertilizer. | Reconciled Eurostat Comext rows give declared origin of extra-EU imports. They do not trace feedstock origin, inventories, or spare production capacity. Ranking by product mass gives a forward test of the claim that the biggest reserve holder always supplies the biggest share. It differs by group and year. [Comext] |
| FAOSTAT provides a single, closed EU phosphorus account. | EU-27 apparent supply is 2.289 Mt P₂O₅ in 2024, against 1.883 Mt reported agricultural use. The difference is unallocated. Production and external trade are estimated in the source snapshot. Neither this gap nor the reported trade balance can locate fertilizer shortages. [FAOSTAT RFN] |

## Benchmarks and publication status

Raddant et al. reconstruct national phosphate flows through 2022 using mining, trade and agricultural-use data. Their reconstructed 2022 EU flows have a wider scope and different timing from the 2024 customs observations here. Hirner et al. map five product groups across 235 countries in 2001–2023 (checked against the abstract and an index of the text; the full paper could not be opened) and examine alternative trading partners. Barbieri et al. trace fertilizer phosphorus linked to food exports and examine soil and mineral stocks. The present result is a source-linked comparison for one importing bloc. The literature comparison checks scope and overlap. It does not reproduce the three studies' bilateral estimates. [Raddant et al. (2025)] · [Hirner et al. (2026)] · [Barbieri et al. (2022)]

The revision is suitable for editorial review as a descriptive evidence note. A global material-flow study still needs an internally consistent set of processing outputs and yields, bilateral partner records, import and export agreement checks, actual nutrient grades, stock changes and allocation between uses. The one-product stress test states a hypothetical import gap under assumed reallocation. Crop, shortage and recovery outcomes remain unmeasured.

[old-page]: https://github.com/materials-atlas/critical-materials-atlas/blob/e26edbd84acff409d025225470b17d0c601d4bc0/phosphate-food-chain/phosphate-food-chain.html
[old-evidence]: https://github.com/materials-atlas/critical-materials-atlas/blob/e26edbd84acff409d025225470b17d0c601d4bc0/phosphate-food-chain/out/phosphate_chain.json
[old-trade]: https://github.com/materials-atlas/critical-materials-atlas/blob/e26edbd84acff409d025225470b17d0c601d4bc0/phosphate-food-chain/out/phosphate_trade.json
[USGS MCS 2026]: https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-phosphate.pdf
[USGS Minerals Yearbook]: https://pubs.usgs.gov/myb/vol3/2019/myb3-2019-morocco-western-sahara.pdf
[FAOSTAT RFN]: https://files-faostat.fao.org/production/RFN/RFN_EN_README.pdf
[BACI]: https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37
[Comext]: https://ec.europa.eu/eurostat/databrowser/view/DS-045409/default/table?lang=en
[WCO]: https://unstats.un.org/unsd/trade/events/2017/suzhou/presentations/Agenda%20item%2017%20%28a%29%20-%20WCO.pdf
[Raddant et al. (2025)]: https://doi.org/10.3390/resources14100151
[Hirner et al. (2026)]: https://doi.org/10.1016/j.resourpol.2026.106064
[Barbieri et al. (2022)]: https://doi.org/10.1038/s41893-021-00816-1

## Review corrections, 25 November 2026

This study was completed and published by the main review after its author's work stopped before the final commit. A second
reading of every cited source found the USGS table identical cell for cell (26 rows, three columns), the Eurostat and FAOSTAT
snapshots identical to a fresh download, and all three papers in place. Five wordings were tightened:

- Barbieri et al. (2022): the abstract names soil phosphorus stocks and domestic rock reserves, not manure or recycled
  materials; the page now attributes only the first two to the paper. The body of the paper could not be read.
- Morocco and Western Sahara: USGS summaries of 2020 and 2021 label the 50 billion tonnes "Morocco and Western Sahara"; later
  editions label the same figure "Morocco". The 2019 yearbook gives Bou Craa 800 million tonnes, about 2%. The page now says so.
- MAP grade: the linked specification gives 48-61% P2O5 for MAP, most commonly 52%. The 46% case is the DAP grade applied to
  the DAP mixtures inside heading 310540; the page now says so.
- FAOSTAT coverage: nutrient totals exclude rock and intermediates, so FAOSTAT is wider than the Comext list on finished
  fertilizers and narrower upstream. EU production and trade are flagged as estimates. In the same file, world 2024 exports
  (27.08 Mt) exceed imports (22.57 Mt), so the 2024 unallocated gap of 0.406 Mt should be read with care.
- Reserves: the USGS definition is in Appendix C of the 2026 summaries. Reserve figures are not strictly like for like: some
  are reported as ore tonnage, and USGS notes that Australia's JORC-compliant reserves were 120 million tonnes against the
  800 million listed.
- Shares use the rounded world totals (250 Mt, 73 billion t); on row sums Morocco would be 14.7% and China 44.8% of output.
- Charts redrawn in the atlas's colours; data unchanged. The proposed edits to the site-wide thesis paragraphs on the Value
  chains page and the chokepoint map were not applied; they are the owner's decision.
