# Electrolyser claim and source register

Evidence review dated 25 November 2026. The previous public pilot is
archived at commit `7e6d699` in the original
`electrolyser-chain/electrolyser-chain.html` and
`electrolyser-chain/out/electrolyser_chain.json`. The source audit covered
the served page, rendered evidence JSON, trade extract, builder and Atlas
summary and map.

| Original claim or figure | Evidence and locator | Review finding |
|---|---|---|
| Installed capacity rose from about 0.6 GW in 2021 to 4 GW in 2025. | [IEA Global Hydrogen Review 2025](https://www.iea.org/reports/global-hydrogen-review-2025/executive-summary) gives 2 GW installed in 2024. [2026 review, Production](https://www.iea.org/reports/global-hydrogen-review-2026/production) says the installed stock surpassed 4 GW in 2025 and separately reports more than 2.5 GW under construction targeting 2026. | The new article uses the latest source’s 2025 wording. The pilot’s early rounded series grouped years with different source vintages and lacked a row-level source. Installed capacity includes technologies besides PEM. Announced, investment-approved, construction and operational projects have different meanings. |
| Low-emissions hydrogen is less than 1% and iridium cannot be a near-term limit. | [IEA 2026, Production](https://www.iea.org/reports/global-hydrogen-review-2026/production) describes almost 1 Mt of low-emissions production in 2025, with the share expected to exceed 1% in 2026. | The share refers to hydrogen produced and includes other low-emissions pathways. Cost, power and demand affect near-term investment. The evidence cannot establish a date at which material constraints first become relevant. |
| Iridium creates a hard geological ceiling for PEM. | [Journal of Industrial Ecology (2026), §2.5 and Fig. 7](https://link.springer.com/article/10.1007/s44498-026-00088-y) uses a roughly 7.5 t/year historical primary-output reference. [Johnson Matthey, May 2026, p. 34](https://matthey.com/documents/161599/509428/pgm-market-report-26.pdf#page=34) estimates 7.1 t primary producer supply in 2025 and 7.3 t total net demand, of which 3.1 t is electrochemical. | By-product dependence limits how quickly output can respond, and the allocation to PEM is uncertain. A published estimate of primary production, producer sales, stock changes and net demand measure different things. The electrochemical category includes uses besides water electrolysis. The model’s conditional thresholds supersede the categorical claim. |
| Iridium is concentrated in South Africa. | [Journal of Industrial Ecology (2026), §2.5](https://link.springer.com/article/10.1007/s44498-026-00088-y) for historical iridium geography. [USGS MCS 2026, Platinum-group metals](https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-platinum-group.pdf) for upstream geography and other uses. | South Africa dominates primary supply. The USGS world table reports platinum and palladium by country. Neither that table nor HS 711049 establishes the geography of iridium refining, qualified catalyst or stack output. |
| PEM needs iridium and platinum, while alkaline avoids the iridium anode. | [IRENA (2020), Table 1](https://www.irena.org/Publications/2020/Dec/Green-hydrogen-cost-reduction), [US DOE PEM targets](https://www.energy.gov/cmei/fuels/technical-targets-proton-exchange-membrane-electrolysis). | Applies to representative designs. The revised comparison covers alkaline, PEM, AEM and SOEC. Flexibility, cost and durability are design and duty-cycle issues. DOE gives combined platinum-group-metal targets, so those figures cannot be substituted for elemental iridium intensities. |
| Trade data can screen equipment and iridium exposure. | [UNSD 854330](https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2089/854330), [UNSD 711049](https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/en/32/711049). | 854330 includes electroplating and electrophoresis. 711049 covers semi-manufactured iridium, osmium and ruthenium. The extract’s codes, nomenclature vintages and observations are preserved. |

## Evidence classes and literature comparison

- [International Journal of Hydrogen Energy (2021), Table 1](https://doi.org/10.1016/j.ijhydene.2021.04.174) gives 0.67 kg Ir/MW in its initial case and 0.05 in its advanced case. The latter corresponds to 0.40 mg Ir/cm² at 8 W/cm². The article retains those classes of evidence. [ACS Catalysis (2025)](https://publikationen.bibliothek.kit.edu/1000188489/170761393) reports roughly 0.06 g Ir/kW in a low-loading electrode experiment at 2 A/cm². Such tests and hypothetical cases give design context.
- [Energy & Fuels (2023)](https://doi.org/10.1021/acs.energyfuels.3c01473) already varies loading, lifetimes and recycling under supply restrictions. [Journal of Industrial Ecology (2026), §§2–4 and Fig. 7](https://link.springer.com/article/10.1007/s44498-026-00088-y) includes stock-flow recursion, competing sector demand, stochastic replacement, recovery and capacity limits. It reports supply estimates and model outcomes under different supply and loading trajectories. The article was reviewed. The linked supplementary spreadsheet and PDF could not be independently retrieved for a numerical replication of its annual results.
- The Atlas calculation uses a smaller transparent balance, a fixed primary allocation and explicit return lag. It demonstrates how equalities and yearly material requirements depend on technology, time and accounting. It makes no new empirical estimate of market feasibility.
- The [IEA 2026 assumptions annex, p. 6](https://www.iea.org/files/c32f2c59-38ce-40d4-a424-9b20c9d7a149/GlobalHydrogenReview2026_AssumptionsAnnex1.pdf#page=6) supplies the reference operating hours. Fixed utilisation, recovery, manufacturing yield, return delays, plant life, adoption paths and allocation shares are model assumptions. The annual market cross-check varies the scale of supply while retaining the same allocation assumption.

External electrochemistry and iridium-market review remain open. A validated
forward estimate needs independently measured stack specifications,
manufacturing and recycling data, and access to supply by buyer and year.

## Previous pilot checklist

# Production checklist

- [ ] Review technology descriptions and catalyst terminology with an electrochemist.
- [ ] Add project-level capacity only from a versioned public database with status history.
- [ ] Do not convert GW to hydrogen tonnes without efficiency and utilisation assumptions.
- [ ] Add iridium-specific production only if a consistent primary historical series becomes available.
- [ ] Review whether AEM belongs in the main comparison as commercial evidence matures.
- [ ] Remove `noindex` and link from the live Atlas only after editorial approval.

## Review corrections, 25 November 2026

A second reading of the cited sources before publication found nothing wrong. Arithmetic re-done (2.25 t / 0.2 kg per MW =
11.25 GW). Two points tightened:

- The 0.2 kg Ir per MW reference loading is a scenario choice below the 0.34-2.0 range the 2026 Journal of Industrial Ecology
  review reports for 2024 (section 2.3). The page now says the reference case is optimistic about loading.
- The US DOE table gives 2022 status and 2026 targets; the source title no longer says "2026 edition".
- The page's statement that the IEA capacity figures are rated electrical input was not found on the IEA page.
