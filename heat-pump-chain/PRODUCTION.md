# Heat-pump chain claim register

Evidence review dated 25 November 2026. The previous public pilot, including
its rendered content and sources, is preserved at commit `939baa4` in
`heat-pump-chain/heat-pump-chain.html` and `heat-pump-chain/out/heat_pump_chain.json`.
The review checked both files and the full linked customs extract.

| Original claim or implication | Source and locator | Evidence and conclusion |
|---|---|---|
| No scarce metal or other input can constrain a heat pump. | [JRC (2025), §4.4, Table 8](https://publications.jrc.ec.europa.eu/repository/handle/JRC144191). | Supported for the input descriptions. JRC identifies steel, copper and some uses of neodymium. Confidence in a universal scarcity claim is low. No material-grade demand and available-supply test was documented for the previous pilot. The review uses the type and scope of input as its finding. |
| China holds about 35% and the US about 25% of heat-pump factory capacity. | [IEA (2026), p. 24](https://iea.blob.core.windows.net/assets/f29fd3c4-f022-4e94-953f-48e274f6215b/HeatPumpMonitor2026.pdf#page=24). | Supported as rounded 2024 estimates for finished units. The original chart used the residual of 40% elsewhere. The current table displays the source’s three stated regional shares, including the EU share of about 20%. The global estimate is about 145 GW per year. |
| Distributed factories imply a diffuse supply chain. Assembly is the industrial bottleneck. | [IEA (2026), p. 32](https://iea.blob.core.windows.net/assets/f29fd3c4-f022-4e94-953f-48e274f6215b/HeatPumpMonitor2026.pdf#page=32), [Commission (2025), §3.6](https://publications.europa.eu/resource/cellar/13267a9f-f429-11ef-b7db-01aa75ed71a1.0001.03/DOC_1), [Commission (2026), Figure HP](https://data.consilium.europa.eu/doc/document/ST-7009-2026-ADD-4/en/pdf) and [JRC (2025), Tables 5–6](https://publications.jrc.ec.europa.eu/repository/handle/JRC144191). | Strong evidence of an assembly and component distinction. The Commission identifies spare hydronic assembly capacity and deficits in selected components. The IEA estimates roughly 90% of global rotary capacity in China across applications. It finds more dispersed scroll capacity. Available quantities that fit European products are unresolved. |
| The Kigali phase-down is the only input pressure and can be described as purely regulatory. | [UNEP timetable](https://www.unep.org/ozonaction/resources/toolkits-manuals-and-guides/path-kigali-hfc-phase-down-timeline), [EU Regulation 2024/573, Annex IV](https://eur-lex.europa.eu/eli/reg/2024/573/oj/eng) and [Implementing Regulation 2026/2486](https://eur-lex.europa.eu/eli/reg_impl/2026/2486/oj/eng). | Strong evidence of the rules. Kigali establishes an HFC phase-down. EU rules restrict equipment by design, refrigerant and date and provide safety exceptions and specific derogations. Whether suitable components or refrigerants are available for a plant is a separate empirical question. |
| A universal installer shortage caps deployment. | [IEA (2026), p. 23](https://iea.blob.core.windows.net/assets/f29fd3c4-f022-4e94-953f-48e274f6215b/HeatPumpMonitor2026.pdf#page=23) and [JRC (2025), workforce discussion](https://publications.jrc.ec.europa.eu/repository/handle/JRC144191). | Supported as a risk affecting installation and maintenance. JRC documents variation across countries. The original causal ranking lacked country-level workforce, demand and backlog data. |
| Heat pumps meet about 12% of building space heating “today.” | [IEA (2022), executive summary](https://www.iea.org/reports/the-future-of-heat-pumps/executive-summary) and [IEA (2026), buildings section](https://www.iea.org/reports/heat-pump-monitor-2026/key-findings). | The pilot supplied no geography, observation year or denominator for the figure. In the 2026 Monitor, a nearby European 12% figure refers to a natural-gas counterfactual, not space-heating market share. The statistic is omitted from the revised study. |
| The customs chart covers equipment under HS 8415 and 8418 and shows who can deploy heat pumps. | [CEPII BACI V202601](https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html) and the checked-in [trade extract](out/heat_pump_trade.json). | Confirmed the displayed series has HS6 841861 only, from 2002 through 2024, in the frozen HS02 and HS17 vintages. It measures finished equipment excluding air conditioners of heading 8415. The 2024 record gives USD 4.15 billion of world export value and China leading with 21.5%. These values do not resolve plant capacity, compressor origin or installations. |

## What this adds to published evidence

| Comparison | Established in the literature | Contribution and observable test |
|---|---|---|
| Final assembly versus component supply | The IEA compares global equipment and compressor concentration. The Commission and JRC document EU assembly and component capacity separately. | The article compares the JRC’s same assembly estimate against two deployment paths. Test the result with annual capacity and demand for the same technology and region, along with actual operating availability. |
| Material versus component constraints | JRC documents material use and risks, including inputs specific to some designs. | Product-level material usage, competing demand and available grade-specific supply would be needed to identify a binding material constraint. |
| Replacement under disruption | [IEA Energy Technology Perspectives 2026](https://www.iea.org/reports/energy-technology-perspectives-2026/supply-chain-risks-and-industrial-competitiveness) already models losing the largest exporter at an aggregate level. [Copeland’s product case](https://www.copeland.com/en-de/products-solutions/compression-technologies-systems/heat-pump-systems) identifies a qualified component configuration. | The Atlas adds a reproducible monthly balance for one design, comparing stock, assembly, qualified deliveries and timing under the same assumed shock. Matched purchasing, stock and alternate-supplier records would show whether actual factory lines behave this way. |

The publication scope is an evidence review with a modelled illustration.
Installing more systems and comparing intervention costs are separate
questions. An independent HVAC manufacturing review and representative
procurement and operating data remain open.

## Earlier pilot checklist

# Publication checklist

This pilot is not ready for live publication by default.

1. Recheck IEA 2026 market and manufacturing values against the cited edition.
2. Preserve EHPA country coverage and technology definitions in every chart label.
3. Audit BACI classification continuity at the HS02/HS17 boundary.
4. Obtain HVAC subject-matter review of component, refrigerant and performance wording.
5. Add country installation and building-stock evidence only when definitions are comparable.
6. Do not infer refrigerant demand from fluorspar output or installation share from equipment exports.
7. Remove `noindex,nofollow` and link from navigation only after review.

## Review corrections, 25 November 2026

A second reading of the cited sources before publication found nothing wrong and tightened three points:

- HS 841861 means "heat pumps other than air conditioning machines of heading 8415" only from the 2007 and 2017 editions. In the
  HS 2002 edition, which the trade archive uses for 2002-2016, the code covers compression-type units whose condensers are heat
  exchangers. The page and the trade table now say so; the statement above that the whole 2002-2024 series measures finished heat
  pumps holds from 2017 only.
- EU assembly capacity: the Commission's 2025 report gives about 24 GW thermal of existing final-assembly capacity in 2023 (its
  "on track" wording is in the executive summary); the JRC gives 77 GW. The page now states the gap.
- JRC names neodymium in brushless DC motors that some heat pumps use, not specifically in compressor motors.
- Not retrievable for this check: Implementing Regulation 2026/2486 (EUR-Lex blocks automated reading; no archived copy).
