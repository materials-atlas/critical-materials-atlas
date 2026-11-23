# Semiconductor evidence ledger

Evidence review dated 24 November 2026. The register covers the study's
numerical and interpretive claims. The linked sources give the original
definitions. The [evidence JSON](out/semiconductor_chain.json) contains the
transcribed data and source identifiers.

## Claim register

| Claim | Measure and scope | Reference period | Source and locator | Review finding |
|---|---|---|---|---|
| China produced about 85% of the world's silicon metal, approximately 4.9 million tonnes. | Share of global physical silicon-metal production by weight. | 2024 | [OECD (2026), Chapter 2, “The sand and silicate supply chain”](https://www.oecd.org/en/publications/due-diligence-for-responsible-sand-and-silicate-supply-chains_7be0093e-en/full-report/component-5.html), text before Figure 2.5. | Supported as a dated OECD estimate. Customs exports measure a separate activity. |
| Electronic-grade polysilicon requires at least 11N purity. | Silicon purity specification for semiconductor ingots and wafers. | Technical definition | [OECD (2026), Chapter 2](https://www.oecd.org/en/publications/due-diligence-for-responsible-sand-and-silicate-supply-chains_7be0093e-en/full-report/component-5.html), text before Figure 2.5. | Supported. The grade cannot be identified from the HS purity threshold. |
| About 38,800 tonnes of polysilicon were produced for semiconductor use. | Global physical production for semiconductor use. | 2023 | [IEA-PVPS (2024), p. 50](https://iea-pvps.org/wp-content/uploads/2024/10/IEA-PVPS-Task-1-Trends-Report-2024.pdf#page=52), “Polysilicon production”. | Supported as a rounded reported production estimate. |
| Semiconductor demand was forecast at 33,500 tonnes, about 2.4% of projected polysilicon demand. | Global annual demand by weight. The forecast includes 1,379,400 tonnes for solar. | 2025 | [SIA (2025), pp. 3–5, Figure 1](https://www.semiconductors.org/wp-content/uploads/2025/08/Semiconductor-Industry-Association-SIA-Comments-Polysilicon-Section-232-Investigation.pdf#page=4). | Supported as a forecast. 33,500 divided by 1,412,900 gives 2.37%, rounded to 2.4%. Production in 2023 and forecast demand in 2025 are distinct measures. |
| Germany and the United States account for about 65% of the semiconductor-grade polysilicon market, with China below 10%. | Estimated global market shares by economy for semiconductor-grade polysilicon. The underlying table and exact reference period are unavailable in the public source. | 2025 industry source cited in a 2026 report | [OECD (2026), Chapter 2](https://www.oecd.org/en/publications/due-diligence-for-responsible-sand-and-silicate-supply-chains_7be0093e-en/full-report/component-5.html), text before Figure 2.5, citing Bernreuter Research (2025). | Supported as reported estimates. The public citation does not establish plant-level shares or validate a precise split. |
| Wacker and Hemlock together represent roughly three-quarters of the semiconductor polysilicon market. | Global supplier-market share. Individual shares and the exact denominator are unspecified. | 2025 source vintage | [SIA (2025), p. 4](https://www.semiconductors.org/wp-content/uploads/2025/08/Semiconductor-Industry-Association-SIA-Comments-Polysilicon-Section-232-Investigation.pdf#page=4). | Supported as an industry association estimate. The same page identifies Wacker, Hemlock, Tokuyama, SUMCO and OCI. |
| Shin-Etsu and SUMCO supply more than half of the global silicon-wafer market. | Company shares, with the market-share basis unspecified in the OECD paragraph. | OECD 2025 citing Siltronic 2024 | [OECD (2025), “Wafer production”, p. 14](https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/06/mapping-the-semiconductor-value-chain_5ba52971/4154cdbf-en.pdf#page=14). | Supported as an attributed estimate. SIA (2025), p. 4, gives examples of US capacity at both Japan-headquartered companies. |
| The six largest suppliers hold about 92% of the global silicon-wafer market. | Company share of the global market. Individual shares, measurement basis and precise reference period are unspecified in the filing. | 2025 source vintage | [SIA (2025), p. 6](https://www.semiconductors.org/wp-content/uploads/2025/08/Semiconductor-Industry-Association-SIA-Comments-Polysilicon-Section-232-Investigation.pdf#page=6). | Supported as an attributed aggregate. Estimates for the two and six largest firms have separate sources and unspecified comparable denominators. |
| Japan, Germany, Korea, the United States and Taiwan account for around 85% of the semiconductor-grade wafer market. | Geographic market estimate as presented by OECD, with the measurement basis and exact reference period unspecified. | OECD 2026 citing SIA 2025 | [OECD (2026), Chapter 2](https://www.oecd.org/en/publications/due-diligence-for-responsible-sand-and-silicate-supply-chains_7be0093e-en/full-report/component-5.html), text before Figure 2.5. | The source says “around 85%”. The evidence JSON records an estimate, replacing an earlier lower-bound label. |
| Global semiconductor-wafer shipment area increased 5.8% in 2025 to 12,973 million square inches. Nominal wafer revenue fell 1.2% to $11.4 billion. | Global semiconductor silicon wafer area shipped and nominal USD revenue. The source excludes solar applications. | 2025 compared with 2024 | [SEMI (2026), 2025 annual results, opening paragraph and scope note](https://www.semi.org/en/semi-press-release/semi-reports-2025-annual-worldwide-silicon-wafer-shipments-and-revenue-results). | Supported with the source's reported growth rates. The 2024 totals in the series come from the [SEMI 2024 annual release](https://www.semi.org/en/semi-press-release/worldwide-silicon-wafer-shipments-and-revenue-start-recovery-in-late-2024-semi-reports). |
| The shipment chart covers annual worldwide volumes and nominal revenue from 2007 to 2025. | Million square inches and nominal USD billions. Revenue is shown at the precision used in the chart. | 2007–2025 | SEMI annual results tables for [2015](https://www.semi.org/en/another-record-year-silicon-wafer-shipment-volumes-2015), [2019](https://www.semi.org/en/news-resources/press/2019-global-silicon-shipments), [2024](https://www.semi.org/en/semi-press-release/worldwide-silicon-wafer-shipments-and-revenue-start-recovery-in-late-2024-semi-reports) and [2025](https://www.semi.org/en/semi-press-release/semi-reports-2025-annual-worldwide-silicon-wafer-shipments-and-revenue-results). | The JSON identifies the source release for each row. Shipment records measure area delivered and give no plant-location breakdown. |
| The US and European share fell from 81% to 18%. The combined share of Japan, Korea, Taiwan and China rose from 17% to 76%. | Percentage of worldwide commercial fab capacity in 300 mm-equivalent wafer starts per month. Facilities using wafers under 200 mm or with capacity below 5,000 starts per month are excluded. | 1990 and 2022 | [SIA/BCG (2024), Exhibit 7, p. 15](https://web-assets.bcg.com/25/6e/7a123efd40199020ed1b4114be84/emerging-resilience-in-the-semiconductor-supply-chain-r.pdf#page=15). | Calculated from the displayed shares. The changes are −63 and +59 percentage points. Europe is one aggregate and “Other” is a residual. |
| Regional fab-capacity shares for 2025, 2030 and 2032 were forecast in 2024. The 2025 forecast puts the five named economies at 86%. | Same commercial-fab definition. The sum covers China, Taiwan, Korea, Japan and the United States. | 2025, 2030 and 2032 forecasts | [SIA/BCG (2024), Exhibit 7, p. 15](https://web-assets.bcg.com/25/6e/7a123efd40199020ed1b4114be84/emerging-resilience-in-the-semiconductor-supply-chain-r.pdf#page=15). | Confirmed forecast vintage. The 2025 sum is 24 + 18 + 18 + 15 + 11. The exhibit reports rounded shares and the 2022 values sum to 101%. All transcribed shares retain their source precision. |
| The five named economies held 87% of operating wafer fab capacity. | Share of global in-production wafer capacity in the OECD database, excluding upcoming fabs. | September 2025 | [OECD (2025), Section 3, paragraph before Figure 1](https://www.oecd.org/en/publications/the-chip-landscape_02dbd028-en/full-report/component-6.html). | Confirmed snapshot. The OECD and SIA/BCG measures use different source dates and coverage. Their one-point difference cannot isolate forecast error. |
| Leading sites vary by chip type. China leads power/discrete, analog and mature logic. Taiwan leads advanced logic and specialty memory, and Korea leads commodity memory. | In-production capacity by fab location, in million 8-inch-equivalent wafer starts per month. OECD sets the mature/advanced logic threshold at 20 nm. | September 2025 | [OECD (2025), Section 3, Figure 4 and accompanying paragraphs](https://www.oecd.org/en/publications/the-chip-landscape_02dbd028-en/full-report/component-6.html). | Confirmed the table values and units. Fabs can appear under multiple chip types. Realized output depends on utilization and yield. |
| Customs measures cover silicon metal and broad downstream categories. | Trade value, reported tonnes and exporter/importer shares by product code. HS 280461 combines grades and HS 381800 includes other doped elements and compounds. | 2002–2024 | [CEPII BACI, V202601](https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html), HS02 through 2016 and HS17 from 2017, and [SIA (2025), pp. 3 and 6](https://www.semiconductors.org/wp-content/uploads/2025/08/Semiconductor-Industry-Association-SIA-Comments-Polysilicon-Section-232-Investigation.pdf#page=6). | The table uses the archived [trade extract](out/silicon_stages.json). An export-value share and an estimate of semiconductor-grade production have different product scopes and denominators. |
| The first test wafers at Siltronic’s 300 mm plant in Singapore date to late 2023. Early customer qualifications followed in 2024, and the annual report records key qualifications in 2025. | Progress at one wafer plant, as reported by the manufacturer. | Late 2023 through 2025 | [Siltronic FY 2024 presentation, slide 6](https://www.siltronic.com/fileadmin/investorrelations/Archiv/2024/Q4/20250306_FY_conference_call_presentation_web.pdf#page=6) and [2025 annual report, p. 6](https://www.siltronic.com/fileadmin/investorrelations/Archiv/2025/Q4/260312_Siltronic_Annual_Report_2025_safe.pdf#page=6). | Site-level evidence of distinct testing and qualification milestones. Individual approvals and usable spare capacity are unavailable in these disclosures. |


## Calculations and limits

- **Historical reallocation.** In `fab_capacity_share.series`, sum `US` and
  `Europe` for each of the 1990 and 2022 rows. Sum `Japan`, `Korea`,
  `Taiwan` and `China` for the second comparison. Subtract the earlier
  value from the later one. Use the published rounded shares directly. The
  country-level Herfindahl–Hirschman Index (HHI) would require a consistent
  breakdown of individual economies.
- **Wafer shipment area and revenue.** Dividing the rounded $11.4 billion
  by $11.5 billion gives a decline of about 0.9%. SEMI's newer release
  reports a 1.2% decline. The article uses the published rate. The public
  rounded values do not establish whether the underlying 2024 revenue was
  revised. Revenue divided by shipped area varies with grades and product
  mix, which makes it unsuitable as a wafer price index.
- **Supplier concentration.** If the combined share of Wacker and Hemlock
  were exactly 75%, the two firms would contribute at least
  `2 × (75 / 2)² = 2,812.5` to HHI on the 0–10,000 scale. Equal shares
  minimize the sum of squares and remaining suppliers can only add to it.
  The input is approximate, so this is a conditional bound. A full HHI
  requires individual shares measured on a consistent basis.
- **Substitution.** The public wafer disclosures make 300 mm wafers a
  better-documented case for studying qualification milestones. The SIA
  polysilicon filing gives a purity threshold and names suppliers, while
  the linked Siltronic reports provide a milestone timeline at a named
  site. A new-plant timeline cannot supply the lead time for switching an
  existing customer during a disruption. That calculation needs approved
  alternatives, spare capacity for the specific wafer grade, inventory and
  delivery information. The aggregate series give no supplier-to-fab flows.

## Concentration measures supported by the sources

| Measure | Public evidence |
|---|---|
| Largest economy share | The dated silicon-metal estimate and the reported or forecast regional fab series support this within their respective scopes. |
| Top supplier shares | The polysilicon evidence gives a two-supplier aggregate. Wafer sources give two- and six-supplier aggregates on unspecified bases. Individual shares or consistent top-three totals are unavailable in the cited sources. |
| HHI | The polysilicon estimate supports a conditional bound. Full supplier or country indices require complete shares within consistent markets or geographic categories. |
| Location and company control | The fab snapshot gives physical location. The supplier estimates use company markets, and the filing gives examples of plants abroad. Measuring ownership and production geography on the same basis would require consistently linked plant-level ownership and capacity. |

SIA/BCG documents the long-run relocation of fab capacity. The OECD studies
document the geography of production and the distinction from ownership. The
Atlas calculations quantify the reported historical shift and the conditional
supplier-concentration bound within their published definitions.
