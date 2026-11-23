# Data-centre deployment evidence register

Review version dated 24 November 2026. The audit covers the article, its
rendered trade and source panels, the chain JSON and the Value Chains card.
The original page returned an empty main heading, findings, trade rows,
methods and sources with scripting disabled. With scripting enabled, the
shared renderer populated those sections successfully from the checked-in
evidence and trade files.

Grades apply to each use of evidence. **A** = directly documented observation
or auditable descriptive calculation. **B** = source-reported estimate,
projection or disclosure with a defined scope. **C** = indirect evidence for
the claim at issue. **D** = unverified hypothesis or illustrative assumption.
Each row records the reviewed publication treatment.

| Original claim or display | Measure, period and source | Grade | Finding and correction |
|---|---|---|---|
| “The chip is ready — the power isn't”, and variants in the hero, finding, stats, chart note, method table, card and map record. | Unspecified projects, dates and denominator. [IEA 2026 summary](https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary), “Across the AI value chain”. | D | Replace the assertion of a universal binding constraint. The IEA reports tight advanced chip manufacturing and high-bandwidth memory supply alongside electrical constraints. The published record gives no distribution of binding project constraints. |
| Securing accelerators means power is the next binding input. | Implicit sequence, without installation dates or measures of ready IT capacity. | D | Replace with a question about which tasks determine the commissioning date. Procurement, grid and construction work can overlap. |
| Global data-centre electricity doubles from 485 to 950 TWh, or about 3% of global electricity. | Annual global electricity use for all data centres. Estimated 2025 base and central 2030 projection. [IEA 2026 summary](https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary), electricity demand section. | B | Retain and identify both data vintages and the 2030 denominator. The figures describe electricity use across all data centres. |
| The US history rose from 58 to 176 TWh and was labelled “measured”. | Annual US electricity estimates for 2014 and 2023. [Berkeley Lab 2024 report](https://eta-publications.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report), executive summary and Figure ES-1. [DOE release](https://www.energy.gov/articles/doe-releases-new-report-evaluating-increase-electricity-demand-data-centers), key findings. | B | Retain the two dated estimates and roughly threefold change. Berkeley Lab models historical demand using shipment and equipment data. Use a table for the two endpoints instead of drawing an intermediate year. |
| US consumption at 325–580 TWh in 2028, up to about 12% of national electricity. | Berkeley Lab 2024 scenario range, equivalent to 6.7–12% of US electricity. [Berkeley Lab](https://eta-publications.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report), executive summary and Figure ES-1. | B | Retain the range as a scenario. The national endpoint trend alone cannot identify the share caused by AI or the site-level binding constraint. |
| Three global demand values for 2035, with weaker efficiency offered as the Lift-Off driver. | Annual global TWh, [IEA 2025](https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai), “Exploring the sensitivity of future data centre electricity consumption”. | B | Keep Headwinds around 700 and Base around 1,200, present Lift-Off as above 1,700, and add High Efficiency around 970. Lift-Off assumes higher adoption, more flexible deployment and a more resilient supply chain. The scenarios give conditional outcomes rather than statistical bounds. |
| Chips, servers, facility equipment, and grid and site describe four stages. | Functional dependencies, no measured supplier-to-site flows. [IEA 2025](https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai), demand and location sections, and [silicon study](../silicon-chip/silicon-chain.html). | B | Retain the systems and explain concurrency, compatibility and commissioning. A separate numerical measure is needed for useful compute. |
| Advanced logic, HBM and packaging can affect hardware delivery. | Industry conditions and forward outlook as reported in April 2026. [IEA 2026 summary](https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary), industry bottlenecks. | B | Retain as a source-reported risk. Avoid turning a market constraint into a delay attributed to a particular site. |
| Transformers have multi-year delivery times, and grid connection queues delay capacity. | US large power transformers rated at 100 MVA or more, quoted delivery periods in 2024, and global planned capacity at risk through 2030. [US DOE 2024, p. 2](https://www.energy.gov/sites/default/files/2024-10/EXEC-2022-001242%20-%20Large%20Power%20Transformer%20Resilience%20Report%207-10-24.pdf) and [IEA 2025, Figure 2.27](https://www.iea.org/reports/energy-and-ai/ai-and-energy-security). | B | Attribute the commonly quoted 36 months to large power transformers in the DOE report. Separate equipment lead time from site installation and connection. The IEA estimates around one-fifth of planned capacity was at risk, a model result for capacity rather than observed delays or a count of projects. |
| Transformers are the emerging bottleneck for AI. | Customs unit values and tonnes in 2023–24 versus 2012–20. [Atlas grid-trade note](../grid-trade.html), §4.2 and §5. | C | Replace with the comparative evidence. The heavy-machinery gaps were +19% for unit value and +17% for tonnes. The electrical-equipment gaps were +10% and +9%, with 95% intervals that include zero. The filed pre-trend rule failed. The observations are compatible with broader electrification and cannot identify an AI-specific or transformer-specific causal effect. |
| Equipment trade shows which inputs are limiting or where qualified capacity sits. | [Atlas AI build-out](../ai-buildout.html), “World trade, 2019 and 2024”. Liquid-dielectric transformers’ market-value shares and selected chip lines, classed by HS. | C | Retain the sourcing context. The transformer lines have lower export HHI than the three chip lines in that snapshot. Export values measure shipments and re-exports, while qualification, technical specifications and spare manufacturing slots require other sources. |
| “Automatic data-processing units (servers)” for HS 847150 and processors for HS 854231. | Nominal world exports and leading exporter’s share. [CEPII BACI V202601](https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html), 2002–2024 archive, HS02 through 2016 and HS17 from 2017. | A for reported trades, C for chip or server capability | Relabel both broad lines. HS 847150 includes other processing units. HS 854231 covers processors and controllers and cannot isolate AI accelerators. Value is unavailable for the latter under the selected pre-2017 nomenclature. The pre-2017 bins are not true zeros. |
| The physical facility uses copper, steel, aluminium, batteries and water. No bulk material is uniquely limiting. | Possible facility inputs, without a site design, cooling system, quantities or sourcing. [IEA 2025](https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai), components and cooling. | C for design, D for universal material claim | Keep examples and explain cooling and backup choices vary. Remove the universal claim and any implied material bill of quantities. |
| Grid readiness stands for operating electricity and for usable computing. | Facility and IT capacity measured in MW, energy in TWh per year, and work delivered in workload-specific units. [IEA 2025](https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai), demand definitions. | D as an equivalence | Define each unit and retain separate electrical acceptance, firm service, cooling, hardware delivery and integrated commissioning. |
| China's position in transformer steel expanded. | Share of world export value of the combined wide and narrow grain-oriented electrical steel lines. [Atlas grid-trade note](../grid-trade.html), §4.4, 2019–2024. | A for the calculation, C for qualified supply | Add the move from 12% to 32% as a sourcing observation. Production capacity, approved grades and steel embedded in transformers require different data. |
| A local power approval can be a separate gate. | [TVA board minutes, pp. 8–9](https://tva-azr-eastus-cdn-ep-tvawcm-prd.azureedge.net/cdn-tvawcma/docs/default-source/about-tva/board-of-directors/february-11--2026/february-11-2026-board-meeting-minutes.pdf?sfvrsn=1658d52d_1#page=8), 11 February 2026, adopted resolution for conditional additional firm service of 150 MW at a Memphis load. | A for the adopted resolution | Use as a documented condition on firm service. The minutes give no energization date or measured project delay. |
| A project with a secured grid connection can still be waiting for permission. | [Woodlands Park appeal](https://acp.planninginspectorate.gov.uk/ViewDocument.aspx?fileid=63029892), §§1–5 of decision letter and inspector ¶5.3. Council refusal followed by planning permission on appeal, 9 July 2025. | A for the decision, B for the reported grid agreement | Add as a distinct local prerequisite. The permission and reported connection agreement do not establish the commissioning date. |

## Where the new work adds to the sources

| Question | Existing evidence | Contribution and limit |
|---|---|---|
| How much electricity might data centres use? | IEA and Berkeley Lab estimates and scenarios. | Retain their vintages and scopes. The estimates establish scale, with no claim of new demand measurement. |
| Was the transformer shock unique? | The Atlas already ran the comparative customs test. | Reuse the estimates and intervals. Shared electrification is a plausible explanation. Evidence that would test it includes order books, factory slots and lead times by rated equipment class and end user, plus comparable electrical goods. |
| Which dependency moves the commissioning date? | Public project records document selected milestones and contractual gates. | Compare what two records establish, and use an explicit dependency network to show which intervention matters under stated assumptions. This is a calculation exercise, with no empirical estimate of a typical project's lead time. |

## Publication outline and remaining evidence

The revised article opens with the commissioning question, then presents the
energy evidence, hardware and electrical systems, trade comparisons,
project records and a worked scheduling example. Static tables show the
evidence and core comparisons. The trade year control adds detail after the
page loads. A scheduling timeline with parallel tasks and a scenario
comparison by usable IT MW would be useful when matched project data exist.

A project comparison needs dated site permits, delivery and acceptance
milestones, utility service dates, equipment specifications and evidence of
other concurrent causes. The evidence above does not show how often each
constraint binds or whether shared electrical manufacturing explains the
bulk of observed delays. Those claims require matched projects or audited
industry order and capacity data.
