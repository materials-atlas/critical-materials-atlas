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
