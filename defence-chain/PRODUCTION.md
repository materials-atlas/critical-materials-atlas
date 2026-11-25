# Defence Chain claim register

Evidence review dated 25 November 2026. The [prior page][old-page],
[evidence JSON][old-evidence] and [trade JSON][old-trade] are pinned to the
reviewed Atlas commit. The earlier pilot used a script to populate the page.

| ID | Claim or figure in the prior pilot | Review finding |
| --- | --- | --- |
| D01 | The headline inferred broad control over Western weapons. | **Withdrawn.** Global production shares and customs records describe markets. The GAO documents gaps in public and administrative records of lower-tier suppliers and country of origin. [GAO] |
| D02 | China provided about 99% of refined gallium. | **Qualified.** The comparison uses 98% of global primary refined output, in 2023, from the [USGS China study]. The [IEA controls table] reports a different 2025 market share. Subsequent products and qualification have different denominators. |
| D03 | China provided 60% of refined germanium. | **Replaced.** USGS reports 77% of global refined production in 2023. The current tracker uses the [IEA controls table]'s 94% 2025 market share and labels the stage recovery. The 2023 USGS and 2025 IEA measures cannot be treated as interchangeable. [USGS China study] |
| D04 | A single Chinese mine share for antimony, reported as 48% in the snapshot and 43% in the historical chart. | **Corrected and separated.** BGS gives 43% for 2024. The pilot’s 48% matches 40,000 / 83,000 tonnes for 2023 in MCS 2024. MCS 2025 estimates 60,000 / 100,000 tonnes for 2024. MCS 2026 revises estimates for several producers and gives 40,000 / 119,000 tonnes in 2024 and 40,000 / 110,000 tonnes in 2025, or 33.6% and 36.4%. Its published world totals exclude US mine output. [USGS 2024] · [USGS 2025] · [USGS 2026] |
| D05 | The decline in the BGS mine share proves that a constraint moved to refining. | **Unsupported.** The BGS series measures mining. A separate refining series and buyer data would be required to establish the stage that limits usable supply. |
| D06 | China accounted for about 80% of tungsten and 90% of rare-earth magnet supply. | **Qualified.** USGS gives 83% of world tungsten mine output in 2023. IEA gives 94% of world sintered permanent magnet output in 2024. The latter has a different scope from all magnets and all rare earths. [USGS China study] · [IEA magnets] |
| D07 | The selected materials were necessary across modern weapons and could not be replaced quickly. The antimony count was more than 200. | **Unsupported.** The record supplies no representative procurement data, production denominators or source for the count. The revised scope covers selected public industrial markets. Selection reflects the availability of production and policy evidence. [GAO] |
| D08 | Shipments fell 97% and prices rose 200%, presented as a demonstrated export-control effect. | **Withdrawn.** The pilot gives no reproducible origin, destination, product and time window for that pair of figures. The filed Atlas series supports comparisons for explicitly defined EU and US import baskets. The figures are descriptive. The EU series shows a fall before announcement and the later window overlaps the US-specific measures. [Atlas export-controls study] |
| D09 | All listed commodities were controlled in 2023–24 and banned outright to the US. | **Corrected.** Gallium and germanium general licensing began in August 2023. Selected antimony and superhard items followed in September 2024. The December notice used a US-specific presumption of denial with narrower product scope. Selected tungsten and medium or heavy rare-earth controls were introduced in 2025. See the dated policy-source links in the study. |
| D10 | The US-specific measures were later eased, with no duration or scope. | **Updated through 25 November 2026.** Announcement 59 extends suspension of paragraph two from 28 November 2026 through 27 January 2027. Paragraph one remains in force. General licensing remains relevant. [MOFCOM 46] · [MOFCOM 59] |
| D11 | No primary US antimony production and thin stockpiles. | **Corrected.** MCS 2026 withholds its estimate of marketable US mine output in 2025, reports an estimated 700 tonnes of primary smelter output and estimates net import reliance at 91% of apparent consumption. Its public stockpile table lists potential transactions. The pilot supplied no evidence of defence stock coverage. [USGS 2026] |
| D12 | The customs table measures availability of individual metals and components. | **Bounded.** HS 811292 groups minor metals. HS 850511 groups metal permanent magnets more broadly than CN 85051110. HS 811010 is unwrought antimony and powder. The table preserves the original codes and values. [UN HS 2017] · [BACI][old-trade] |
| D13 | A 93% share of EU magnet imports is an exposure measure. | **Defined.** For CN 85051110, declared Chinese origin in 2024 was 91.1% by net mass and 92.7% by value, each against the published extra-EU total. The category contains more than one rare-earth magnet chemistry and serves civilian and defence users. [Atlas magnet study] |
| D14 | Price evidence describes the magnitude of disruption. | **Source and timeframe added.** The MCS 2026 salient statistics table gives annual benchmark averages of USD 10.24 and 25 per pound for 2024 and 2025. The November USGS outlook reports approximately 10 and 24 and a spot price of about 12 at end-April 2026. An annual average, a spot quote and a customs unit value have different definitions. [USGS 2026] · [USGS outlook] |

Reproduction covers the checked-in BACI extract, the Atlas BGS series, the
magnet study's scoped Eurostat query and the stored monthly aggregates from
the filed export-controls analysis. Raw bilateral and monthly files are
required to repeat the underlying aggregations. Data on approved supplier
origins, inventories and outcomes for individual defence programmes remain
unavailable. The revised article can be reviewed as a public materials-market
note. A defence-production risk assessment would require different evidence.

[old-page]: https://github.com/materials-atlas/critical-materials-atlas/blob/2b6215c7b356fa800091f4a774084c8425fbc41b/defence-chain/defence-chain.html
[old-evidence]: https://github.com/materials-atlas/critical-materials-atlas/blob/2b6215c7b356fa800091f4a774084c8425fbc41b/defence-chain/out/defence_chain.json
[old-trade]: https://github.com/materials-atlas/critical-materials-atlas/blob/2b6215c7b356fa800091f4a774084c8425fbc41b/defence-chain/out/defence_trade.json
[GAO]: https://www.gao.gov/products/gao-25-107283
[USGS China study]: https://pubs.usgs.gov/of/2026/1018/ofr20261018_pamphlet.pdf
[USGS 2024]: https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-antimony.pdf?v=101202
[USGS 2025]: https://pubs.usgs.gov/periodicals/mcs2025/mcs2025.pdf
[USGS 2026]: https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-antimony.pdf
[USGS outlook]: https://pubs.usgs.gov/publication/sir20265081/full
[IEA controls table]: https://www.iea.org/reports/global-critical-minerals-outlook-2026
[IEA magnets]: https://www.iea.org/reports/rare-earth-elements/executive-summary
[Atlas export-controls study]: ../export-controls.html
[Atlas magnet study]: ../magnet-chain/magnet-chain.html
[MOFCOM 46]: https://www.mofcom.gov.cn/zfxxgk/gkml/art/2024/art_99f5d51bbe6a412ca309d5818c4dee52.html
[MOFCOM 59]: https://aqygzj.mofcom.gov.cn/qdml/art/2026/art_98ae61c2a60f43638304f2e6a43f952f.html
[UN HS 2017]: https://unstats.un.org/unsd/classifications/Econ/Detail/EN/2089/811292

## Review corrections, 25 November 2026

A second reading of every cited source before publication found no wrong claim. MOFCOM announcement 59 of 2026 (published
24 November 2026) was read in Chinese: it suspends the second paragraph of announcement 46 of 2024 from 28 November 2026 to
27 January 2027, as announcement 72 of 2025 had done to 27 November 2026. Four wordings were tightened:

- Neither suspension notice mentions the first paragraph of announcement 46 or the licensing rules; that they remain in force
  is a reading of the three texts together, and the page now says so. The tracker no longer calls the suspended paragraph
  "the US-specific paragraph", since the first paragraph is US-specific too. Announcement 46 also has an unnumbered third
  paragraph (liability of third-country parties who pass items to the US), not suspended and not discussed on the page.
- Antimony: USGS revised 2023 itself to 58.8% (62,300 of 106,000 t) in its 2025 edition, so the pilot's 48% was superseded for
  2023 as well. The page now says so.
- Germanium: the USGS 77% for 2023 rests on an assumed world total of 200 t carried over from 2020 (Open-File Report 2026-1018,
  Table 3, footnote 4). Both it and the IEA's 94% (2025) are refining-stage figures.
- Row D09 above: "presumption of denial" fits the Chinese text of the second paragraph; the first paragraph is an outright
  prohibition for US military users and uses.
- The chart was redrawn in the atlas's colours; its data are unchanged.

## Additions, 25 November 2026: evidence by material, replacement and adjustment

A second assessment asked for three things the page did not have: a table from material to military use with a stated
confidence, evidence on what could replace Chinese supply, and resilience scenarios. The first two were added. The third
was added only as far as the public record allows.

| ID | Addition | Basis | Limit |
| --- | --- | --- | --- |
| D15 | A table of documented uses, sourcing law and observed supplier relationships for the five materials, with three grades each. | US statute and regulation, USGS 2026 chapters, Department of Defense and Department of War releases, GAO reports, the NATO list and the European Commission research centre study, all read on 25 November 2026. Quotations and links are in `pathway_inputs.json`. | The grades (A to D) are editorial. The scale is the one proposed in the assessment. No link is graded above B, because no source gives defence purchases by supplier. |
| D16 | "Chinese supply inside a defence supply chain is on public record in two cases." (Antimony: the sole qualified source of one product; purchases are not documented.) | GAO-24-106959, p. 26: funding in fiscal 2020 to qualify a US company sourcing antimony trisulfide from Mexico "to replace the only qualified source located in China". GAO-25-107283, p. 18: F-35 "6-month production stoppages, in 2023 and 2024, when Chinese magnets were identified on the aircraft and had to be replaced". | The second is a defence official's statement reported by GAO, which describes a pause to identify alternative suppliers and two national security waivers. Whether the Mexican-sourced supplier was qualified is not stated. |
| D17 | Supply outside China, and outside the four nations named in 10 U.S.C. 4872(f)(2). | USGS 2026 country rows for gallium, antimony, tungsten and rare earths (2025 estimates). | Shares use the sum of the listed rows. The statute does not cover antimony, has waivers and exceptions, and reaches mining only from 1 January 2027 (Public Law 119-60, section 848). Rare-earth mine output is not magnet output. The Mineral Commodity Summaries give no germanium tonnage by country. |
| D18 | Substitutes, the fiscal 2025 stockpile purchase plan and announced capacity. | USGS 2026 chapters; Defense Logistics Agency Annual Materials Plan for fiscal 2025; company releases, marked as company statements. | The plan gives ceilings for purchases and sales, not quantities held. The fiscal 2026 plan was not released. Announced capacity is not operating capacity. |
| D19 | "Modelled": the antimony purchase ceiling of 700 tonnes equals about 9 days of 2024 US apparent consumption (28,600 tonnes). | Arithmetic on two USGS figures. | A size comparison. It is not a stock-cover estimate, because the quantity held is not public. |
| D20 | In the EU series other origins rose by more than China-origin imports fell; in the US series other origins fell too. | The two windows already on the page: later-window average less earlier-window average, China origin and all other origins. | Descriptive. The windows, baskets and caveats are those of the existing table. The US basket leaves out oxide, whose imports rose from 24,000 to an estimated 39,000 tonnes between 2024 and 2025 (USGS). |

Not done, with the reason. No quantified scenario for defence production was built. GAO reports that the Department of
Defense itself cannot trace component origins in its procurement data and had country-of-origin information for under 10%
of the suppliers behind the F-35 parts it had mapped; a scenario would need defence consumption, qualified suppliers and
stocks, none of which is public. No time to qualify a new supplier was found in any source read. The count of weapon
systems using each material, and the "920 pounds of rare earth materials in an F-35" figure, were not used: the latter
reaches the Congressional Research Service at third hand from a report of about 2012 that was not found.

A second reading of the two new sections against the source documents, same day, led to these changes before publication.
The statements about 1 January 2027 now follow the statute as amended by Public Law 119-60, section 848, and no longer the
2024 regulation. The statute's waivers and exceptions are stated. The F-35 sentence reports what GAO describes and drops an
inference about supply. The magnet quantity is dated and labelled as a rare-earth figure from Department of Defense
estimates reported in 2016. The antimony row no longer says the White House table lists only civil uses: it lists four
application areas, none of them munitions. The qualification cost is attributed as GAO gives it. Three company statements
were reworded to match the releases, and USGS capacity for gallium and two further magnet makers were added. The date of
the 2022 Department of Defense release is given as the year only, because the copy read prints October and its text
points to December.
