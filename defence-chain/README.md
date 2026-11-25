# Materials and trade in defence supply chains

The [research note](defence-chain.html) compares public production,
import-origin and trade evidence. The [claim register](PRODUCTION.md) pins the
prior release and records the audit and remaining gaps.

Run `python defence-chain/record_defence.py` from the repository root. It also reads `pathway_inputs.json`: the documented uses, sourcing law, supplier evidence, evidence grades, USGS country rows and stockpile figures for the five materials, each with its source link. The builder stops if a grade is missing, if a source key is not in the list, or if the country rows do not add to the published world total within 2%.
The builder uses the static template, the frozen BACI extract, the Atlas BGS
mine series, the existing export-controls series and the magnet study's
Comext audit. It writes the article, the evidence JSON and
`out/defence_antimony_monthly.csv`. It requires no network access. To regenerate the chart from the CSV, run
`python defence-chain/plot_antimony.py` with Matplotlib installed.

## Antimony comparison

The builder takes the EU and US antimony cases from `out/export_controls.json`.
The earlier period is August 2022 through July 2024. The later period is April
through September 2025, months seven through twelve after the September 2024
entry into force. Month zero is September 2024. The EU basket uses
CN 81101000, 81102000, 81109000 and 26171000 in extra-EU data. The filed
analysis excludes UK and Northern Ireland partner codes. The US basket uses
8110100000, 8110200000 and 8110900000 from US Census general imports.
Neither basket includes antimony oxide.

The monthly averages weight months equally. The pooled unit value weights each
monthly customs unit value by the same month's reported import mass. The
published monthly extraction rounds the inputs. Recomputed summaries may
therefore differ slightly from the underlying analysis. The downloadable CSV
retains the available months and distinguishes EUR/kg and USD/kg. Monthly
unit values reflect prices, product mix and customs reporting.

The BGS and USGS mine estimates are each reported with their source and year.
There is no interpolated series across source vintages. The magnet benchmark
divides Chinese-origin entries by the official extra-EU aggregate from the
same Eurostat query, once for net mass and once for value.

The customs series cover aggregate markets. Programme exposure and the
effects of export controls on defence procurement need separate evidence.
Rebuilding the filed antimony series or the BACI trade extract requires the
raw data used by the original builders.
