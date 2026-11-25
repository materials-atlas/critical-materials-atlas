# Optical fibre: claim and source audit

Evidence review dated 25 November 2026. The previous public page was an undated overview rendered by a
script from `out/fibre_chain.json`. Its text, evidence file and builder are in version history (the last
commit before this review). The dated source library stays at its own address, unchanged.

Every source below was opened and read on 25 November 2026. The transcribed figures are in
`evidence_inputs.json`. The builder refuses to publish if the USGS model figures do not multiply out, if
the supplier lengths do not reproduce the printed shares, or if a sentence on the page no longer matches
the numbers.

| Previous claim or framing | Source and verification | Disposition |
| --- | --- | --- |
| "~60% of refined germanium is China", labelled measured, attributed to USGS. | The USGS germanium chapter gives no world total and no China share. USGS Open-File Report 2024-1057, table 1.14, estimates 2022 primary production at 210 t, 180 t of it in China (86%). USGS Open-File Report 2026-1018 gives 154 t for 2023 and 77%, on an assumed world total of 200 t. The IEA's 2026 outlook gives 94% (table, 2025) and a chart value of about three-quarters. | **Corrected.** The page gives the range and its basis. |
| "Fibre optics is one of germanium's largest single uses." | USGS lists fibre first among US uses; 40% in the United States (2016, last reported); 30% worldwide in 2020–22 (an industry data provider's estimate quoted by USGS). | **Supported**, with the figures and their dates. |
| "The germanium in a cable is a tiny mass, so this is not a tonnage risk — it is a qualification and single-source risk." | USGS model: 0.0039 g per km of single-mode fibre, 0.19 g per km of multimode; about 5 t in US-made fibre in 2021. No source opened addresses qualification. | **Replaced** by the quantity model. The qualification claim is withdrawn. |
| "Optical fibre is ultra-pure silica with its core doped by germanium." | True of standard fibre (ITU manual; a Sumitomo data sheet for G.652.D fibre). Not true of pure-silica-core fibre, sold for submarine cables since 1988 (Sumitomo) and offered by all three makers of fibre for long submarine systems. | **Qualified.** A section on fibre without germanium in the core is added. |
| "Corning leads and supplies most submarine consortia, alongside Prysmian, YOFC and Sumitomo." | European Commission expert group, Annex, p. 49: only Corning, OFS and Sumitomo Electric make fibre for long submarine systems with repeaters. | **Corrected.** |
| "Corning's 2024 preform-capacity expansion signals how few players hold this stage." | The cited link was a general news page. Not checked. | **Withdrawn.** |
| "4 firms build essentially all the world's submarine cables." | Same Annex, figure 3.3: ASN 33.7%, SubCom 23.7%, NEC 15.1%, HMN Tech 10.2% of cable length deployed in 2020–2024, together 82.7%. Other suppliers of short systems 17.1%, Xtera 0.2%. | **Qualified** to 83% of length, with the period and the source's own word "estimated". |
| ">60% of wet-plant revenue is ASN + NEC + SubCom (2024)", from market-research summaries. | Not checked. The length shares of the same three sum to 72.5%. | **Replaced** by the length shares. |
| "~99% of intercontinental data crosses on subsea fibre." | Not checked in this review. | **Not carried forward.** |
| "ASN — a Nokia division." | Same Annex, figure 3.6: 80% French government, 20% Nokia. | **Corrected.** |
| "HMN Tech — growing via price and Belt-and-Road routes." | Not checked. | **Withdrawn.** |
| "China sits at both ends"; "two chokepoints, one country at both". | China is the largest germanium refiner on every estimate, and HMN Tech built 10.2% of cable length. | **Reduced** to the two figures. |
| Map entry: stage "Preform", holder "US · JP", labelled measured. | No source measures preform shares. A brokerage estimate quoted in the press puts China at 59% of preform output in 2025. The three-firm finding concerns fibre for long submarine systems. | **Restated** as that finding plus the supplier shares, labelled estimate. |
| The page carried `noindex,nofollow` while marked published. | Other published chain pages are indexable. | **Corrected** to `index,follow`. |

## Findings of this review

- **The USGS quantity estimate is almost all multimode fibre**: 4.9 of 4.97 t. It rests on a market
  report's split for North America (54.4% multimode, 35.5% single-mode, 10% plastic).
- **USGS table 1.24 has two slips.** The volume row is labelled cubic metres per fibre-kilometre, and the
  numbers only work as cubic centimetres. The title says fibre "laid" in 2021–22 and the row says
  "manufactured" in 2021. The page uses the mass rows, which are consistent.
- **The loss, recovery and 2.68:1 figures are from the literature** (Licht and others, 2015), quoted by
  USGS. They are not USGS measurements.
- **The IEA's two germanium figures differ** inside one report (94% in the export-control table, p. 39;
  about 74% read from the chart on p. 199). An earlier reading of the same chart for the germanium map
  entry was about 78%. It is a chart reading and the page says "about three-quarters".
- **"Others 17.3%" does not appear in the European report.** The figure shows 17.1% for other suppliers
  and 0.2% for Xtera.
- **The report is not consistent on wording**: cable "deployed", "built" and "installed" are all used for
  the same shares, and the main report speaks of three main suppliers where the Annex has four.
- **Corning's own sheets say "silica core"**, not "pure silica". The pure-silica-core description of a
  Corning product comes from a journal article.
- **OFS and Lightera.** The expert group names OFS; the product page is Lightera's. The link between
  them rests on the OFS website, which redirects permanently to lightera.com (checked 25 November 2026).
- **A draft of this review said no public source gives a world germanium total.** A fact-check found
  the USGS estimate in table 1.14 of Open-File Report 2024-1057. Corrected before publication, and the
  comparison figure now uses it (30% of 210 t).
- **HS 2825.60 holds germanium oxides with zirconium dioxide**, and germanium tetrachloride sits in
  2827.39 with other chlorides. Only national tariff lines separate them.

## What the screen is

A sensitivity calculation, labelled Modelled on the page. It multiplies the two USGS per-kilometre
figures by an assumed 500 million kilometres of fibre at different multimode shares, and applies the
2.68:1 ratio. The comparison figure is 30% of the USGS estimate of 210 t of primary germanium. The world length is implied by USGS-quoted figures for 2021 (495 and 512 million) and is
not a published statistic.

## Not done

- No measured world germanium production figure exists to test the model against. The page uses the USGS estimate of 210 t for 2022.
- No multimode share of world fibre output.
- No share of pure-silica-core fibre.
- No fibre or preform output by country from a statistical source.
- The Heraeus cladding-tube material and Corning's standard single-mode core dopant were not confirmed from a document that could be opened.
- Revenue shares and order books for submarine systems were not checked.
