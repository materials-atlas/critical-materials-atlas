# From silicon to chips

This Critical Materials Atlas study compares silicon metal, electronic-grade
polysilicon, blank silicon wafers and front-end chip fabrication. The article
and evidence were reviewed on 24 November 2026. The [claim and source
register](PRODUCTION.md) records the definitions, calculations and limits.

## Reading the study

Physical production, supplier market share, fab capacity and customs trade
answer different questions. HS 280461 combines solar and semiconductor grades.
HS 381800 includes other doped elements and compounds alongside silicon wafers.
The four stages describe the production sequence. The available statistics
cover each stage separately.

| Evidence layer | Coverage |
|---|---|
| Commercial fab-capacity geography | Reported snapshots from 1990 to 2022 and forecasts for 2025, 2030 and 2032, from SIA/BCG's 2024 report |
| Blank semiconductor-wafer shipments | Annual worldwide shipment area and nominal revenue from 2007 to 2025 |
| BACI silicon and mixed downstream trade | Annual trade from 2002 to 2024 |
| Electronic-grade polysilicon | Reported 2023 production, forecast 2025 demand and dated market estimates |
| Operating fab capacity by chip type | September 2025 OECD snapshot |

## Rebuild and view

From the repository root, regenerate the semiconductor evidence and serve the
study over local HTTP:

```text
python silicon-chip/record_semiconductor.py
python -m http.server 8765
```

Open [the local study](http://localhost:8765/silicon-chip/silicon-chain.html).
The page uses the checked-in [semiconductor evidence](out/semiconductor_chain.json)
and [BACI trade extract](out/silicon_stages.json). With the original BACI
archives available, `python silicon-chip/extract_baci.py` rebuilds the trade
context. `record_iea_pv.py` maintains the separate solar evidence.
[Interpretation notes](NOTES.md) document the discarded trade proxies.
