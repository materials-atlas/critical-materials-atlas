# IEA Global Critical Minerals Outlook 2026 — full archive

Complete, agent-consultable capture of the **IEA Global Critical Minerals Outlook 2026** (published 16 July 2026, CC BY 4.0), transcribed during the Aug-2026 verification pass that cross-checked every Critical Materials Atlas chokepoint figure against it.

**What the IEA is:** the International Energy Agency — a Paris-based intergovernmental organisation (within the OECD family, founded 1974), the leading public authority on energy and, increasingly, critical minerals. Its figures sit alongside USGS and worldsteel as the atlas's ground-truth sources.

**What the report is:** the IEA's annual assessment of critical-mineral supply chains — 2025 market review, demand/supply projections to 2040/2050, per-mineral chapters, policy pathways, and a Latin America focus. Core thesis (same as the atlas): the vulnerability is refining/processing concentration, overwhelmingly China, and 2025 was the year export controls made that risk real.

## Files
| File | Contents |
|---|---|
| `report-narrative.md` | Full narrative text + every chart described, section by section (Exec summary → Latin America → Annex) |
| `annex-supply-demand.json` | The 12 annex "Key projection results" tables — exact tonnages by country/year/scenario for copper, lithium, nickel, cobalt, graphite, rare earths (mining + refining + demand) |
| `concentration-and-controls.json` | Export-control market-share table (p.39), refined shares (p.31), mining shares (p.32), prose shares (p.121), battery supply chain (p.73), minor-minerals scatter (p.199), nuclear fuel cycle (p.224-228), other scattered shares |
| `byproducts-and-costs.json` | By-product "roots" map (p.367-368), material cost shares, economic value-at-risk, diversification economics |
| `../iea_gcmo_2026_data.md` | The original atlas-relevant summary (which figures the atlas uses, and where IEA disagrees with USGS) |

## How the atlas uses it
Every atlas chokepoint figure is triangulated across USGS + worldsteel + this report. The verification pass changed 11 figures (germanium 60→85%, manganese 90→95%, graphite anode 100→95% & flake 74→80%, rare earths 90→85%, cobalt DRC 75→70%, lithium 70→75%, steel 54→52%, gallium 98→99%, tantalum 70→68%, bismuth 85→88%, nuclear → Russia ~45%) and added cross-reference notes where IEA disagreed with USGS (antimony, indium, bismuth, germanium, nickel). Rare earths ~85% was confirmed four independent ways; indium 70% three ways.

**Caveat:** the numeric tables are transcribed verbatim from the report; chart values read off stacked bars are approximate (±1-2pp) and flagged as such in the JSON. Data is © IEA, CC BY 4.0 — attribute the IEA when reused.
