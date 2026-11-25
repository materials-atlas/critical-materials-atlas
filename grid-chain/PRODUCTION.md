# Grid Chain claim and evidence register

Review dated 24 November 2026. The previous page, evidence and trade
extract are retained in version history. Their original Git blobs are
`7eea818a3482dc6fb3e7f2c4ab845730ce88f615` (HTML),
`767c8fb139e11ce9e87e720544833947493db48e` (evidence),
`3e21deb6d93e871db5016bd43bb534543a55eda1` (trade) and
`eca5c450716598a659020f2133a482345622afb8` (GOES evidence).
The September EU supply data are at `2ab0ed74f9dd051b6a08f17f7ee1087ac215bd1e`.

| Claim | Original evidence or status | Review and disposition |
| --- | --- | --- |
| Large transformer procurement takes up to four years. | IEA 2025, originally marked measured. | **Supported as a survey benchmark.** 2024 stakeholder survey, used in its 2025 report. Markets and specification differ. The US DOE benchmark is a separate survey and reporting basis, and ENTSO-E uses European voltage classes. |
| Cables take two to three years and specialised DC cables exceed five. | IEA 2025, originally marked measured. | **Supported on that report's scope.** Retained in the archive. The revised study narrows to transformer procurement. |
| Power-transformer prices increased about 75% relative to 2019. | IEA 2025 report, executive summary and Chapter 2. | **Supported as a survey-based real-price comparison.** Complexities and ratings influence orders. It differs from the customs unit-value estimates and the BLS producer series. |
| A large transformer takes years because of GOES and skilled winding. | IEA/DOE lead times and a measured customs HHI. | **Partly supported.** Specialised inputs, labour, testing and capacity merit attention. Orders, approved suppliers and plant schedules are needed to allocate delay to a cause. |
| GOES is the tightest node, at HHI 0.164, versus 0.073 for transformers, 0.066 for copper wire and 0.060 for high-voltage cable. | BACI HS17 V202601, 2022–24 total window. Originally marked measured. | **Reproduced as a trade ranking.** Values are pooled before shares are computed. The comparison also includes bare aluminium conductor (0.136). No common capacity ranking is available. |
| China and Japan account for 28.8% and 24.3% of GOES exports, with about 61% in the leading three and 8% from Russia. | Same pooled value window. | **Reproduced on the value basis.** The third share is geographic trade exposure. The old paragraph's policy characterization is outside the calculation. |
| GOES annual HHI was 0.111, 0.127, 0.122, 0.146, 0.167 and 0.188 in 2019–24. China went from 27.3% in 2022 to 31.7% in 2024. | BACI, same baskets by year. | **Reproduced.** The new mass series and width split are public alongside value. The separate September HS02 result shows the same rounded endpoints for China’s value share, about 12% and 32% in 2019 and 2024. |
| Export HHI is a lower bound on production HHI, with direction known. | Narrative based on domestic sales. | **Corrected.** Domestic sales, re-exports, prices and product mix can move export concentration in either direction relative to production concentration. |
| Copper and aluminium are abundant, diversified and unable to constrain buildout. | DOE conductor report, originally marked measured. | **Narrowed.** Material choices depend on design and qualification. Economy-wide mineral data leave the availability of qualifying material and components unresolved. |
| About 80 million km of grids need adding or refurbishing by 2040 and roughly 1,500 GW of renewables are in connection queues. | IEA 2023 executive summary, originally marked measured. | **Verified with vintage and boundary.** The length claim is a world expansion and renewal estimate. The 1,500 GW queue figure covers advanced-stage projects in the IEA dataset at that time. It measures neither transformer shortages nor all current queues. Retained in the source record. |
| Transformer lead times dominate project delays and more factories would accelerate completion. | Inference in the previous article. | **Revised.** IEA identifies permitting as the primary reported delay. The modelled schedules find an earlier completion only when the equipment path finishes later than all competing paths. No observed MW or completion effect is assigned. |
| Trade slider includes transformer, copper, aluminium and switchgear values. | Original trade introduction. | **Corrected.** The checked-in file contains only HS 850422 and 740811. The revised page identifies both, displays a static snapshot and retains the year picker. |
| Transformer-specific unit-value shock, +19% or +10%. | September filed model and alternate electrical-equipment comparison. | **Reproduced from raw HS02.** Both coefficients and intervals match the filed results, including the failed pre-trend check. The electrical-equipment interval includes zero. This does not show no effect. |
| China's EU GOES import-value share moved from 9% in 2019 to 52% in 2024 and 57% in 2025. | September Comext extraction as used in the published note. | **Independently cross-checked.** Same rounded shares on the later Eurostat release and an increasing mass share. The denominator is imports excluding the UK. |
| China is 9.1% of EU transformer supply and roughly 24% of EU GOES supply. | September EU apparent-supply calculation. | **Reproduced arithmetically and cross-checked from Eurostat.** These are gross-import-based value ratios in broad baskets. GOES mass gives about 26.3%. Embedded content and final absorption are unidentified. |
| The large-inverter supply share is about 73% and critical. | September table and classification. | **Reproduced and reclassified.** Use numeric exposure bands. Reporting 2024 as a round value is confirmed by the requested flag. Its source rounding base is €3 billion. Even the smaller ±10% illustration spans roughly 65.5–82.5%; grid-only and retained exposure are unresolved. |
| Import share, apparent supply, lead time and physical scarcity measure the same dependence. | Potential reading across the original pages. | **Separated in the revised analyses.** Product definitions, valuation, stock changes, commercial access and timing differ. |

The working paper can be reviewed as a dated descriptive study. Verify
with a transformer procurement engineer the equipment and components
that can substitute for each other, and with a trade statistician the
2024 crosswalk and gross-flow interpretation. Testing a binding
capacity constraint requires validated available output and backlog for
each specification, comparable delivery dates, approved suppliers and
project timetables. The illustrative schedules do not supply those
observations. An independent specialist review remains outstanding.

## Review corrections, 24 November 2026

Every outside source was re-read. Four changes followed:

- IEA, Building the Future Transmission Grid, p. 8: "the price of power transformers rose by around 75%". The page no longer says "large", "real terms" or "survey prices"; the four-year lead time is given as the source words it ("up to four years").
- ENTSO-E 2026, p. 16: operators have "a limited view of manufacturing capacities". The page no longer says qualified capacity is unavailable. The report's own Figure 4a uses a 145–420 kV band beside the 245–420 kV text; both are noted.
- National Laboratory of the Rockies 2026 is a supplement on hydropower rehabilitation; its 30-month average cites Wood Mackenzie.
- Prodcom 27904155 to CN 85044086 is a partial correspondence (the CN code also feeds a telecom and computer power-supply line).

The September grid-trade study's filed section 4.6b-c is kept as filed; the 24 November interpretation note and sensitivity table follow it.

## Split into two papers and new evidence, 25 November 2026

The supplier-exposure analysis now has its own page, [grid-exposure](../grid-exposure.html), built by
`eu-grid-supply/build_paper.py` from the filed results. This page keeps a summary and links to it.

A section on order books and output was added. Its inputs are two files:

- `market_inputs.json`: official series copied without change on 25 November 2026 (Destatis order backlog range and
  volume index; US Census M3 unfilled orders and shipments; US producer prices; Japanese transformer orders and the
  METI production survey; Eurostat Prodcom code 27114180; the European Commission business survey for NACE 27; the
  Federal Reserve G.17 series). Each block carries its source, series identifiers and definition.
- `firm_inputs.json`: year-end order backlog and revenue of the reporting segments that contain power transformers,
  read from company results documents, with the document, page and link for each year; maker statements; capacity
  announcements that state a capacity figure; the plant-count study; and the European Commission's figures for
  grain-oriented electrical steel from Implementing Regulation (EU) 2026/2133.

`market.py` does the arithmetic and stops the build if a sentence on the page no longer matches the numbers.

| Claim before | Evidence added | Disposition |
| --- | --- | --- |
| "Is qualified output short? Unresolved across the EU and US." | EU mills for electrical steel used 71% of capacity in 2025 (Commission questionnaire data). EU units of transformers above 10 MVA: 3,792 in 2021, 3,733 in 2025. Japanese units of 100 MVA and above: 72 a year in fiscal 2015 to 2018, 48 a year in fiscal 2022 to 2025. | **Partly answered.** No shortage of electrical steel in total tonnage in the EU; the highest grades come from imports and are not measured separately. The unit counts show no rise in transformer output; larger units, higher prices and delivery lags can also explain that. Capacity by rating is still unpublished. |
| Procurement pressure "documented" from surveys. | German order-backlog range for branch 27.11: 5.9 months (end 2019), 14.1 months (September 2026). Four makers' backlogs equal 2.9 to 3.7 years of segment revenue. | **Strengthened** with official statistics and company accounts. |
| An earlier status message said no public source holds capacity or backlog data. | The sources above. | **Corrected.** Public data exist for backlogs, prices and unit output; they do not exist for deliverable capacity by rating. |

Limits. The German and US backlog series cover electrical equipment more widely than transformers. Company segments
are wider than transformers and differ between companies. The Japanese orders survey covers 13 firms. The EU unit
counts do not show unit size, and the 2025 figures come from a newer dataset than 2021. The plant-count study is a
trade-journal article. The electrical-steel figures do not separate grades.

Corrections after a second reading against the source documents, same day. The comparison for US order books now
uses the manufacturing industries that report unfilled orders (6.3 to 7.2 months) and no longer total manufacturing
shipments, which mixed two bases. Electrical equipment has a shorter order book than that average; what holds is that
it lengthened more (45% against 14%). The maker statements about filled production slots are attributed to the one
company and region they describe. The Hitachi Energy investment was removed from the list of announcements that state
a capacity figure. The Siemens Energy investment figure is given as the segment total. The electrical-steel paragraph
now carries the Commission's findings on grades (recitals 49, 62 and 63). Backlogs printed in round billions are marked
"about".
