# Semiconductor chain pilot (unpublished)

This research workspace follows silicon beyond the mine and metal plant into
electronic-grade polysilicon, blank semiconductor wafers, and chip fabrication.
It is isolated on `wip/silicon-chip-chain`: it is not linked from the Atlas and
does not alter any of the 32 published material profiles.

## Reading rule

Physical production, company control, and customs trade answer different
questions. The pilot keeps them separate. In particular, it never treats
HS 280461 as chip-grade polysilicon or HS 381800 as semiconductor silicon
wafers: both customs lines contain products used outside chipmaking.

## Files

- `record_semiconductor.py` builds the semiconductor-specific evidence layer.
- `extract_baci.py` builds annual customs context for HS 280469, 280461, and
  381800 from the local BACI archive.
- `record_iea_pv.py` preserves the separate solar-production layer for a later
  solar chain page.
- `out/semiconductor_chain.json` contains sourced semiconductor evidence.
- `out/silicon_stages.json` contains the mixed-code BACI trade series.
- `silicon-chain.html` is the unpublished interactive research page.
- `NOTES.md` records the interpretation and rejected claims.
- `PRODUCTION.md` is the source and measure ledger.

## Time coverage

| Evidence layer | Coverage |
|---|---|
| Commercial fab-capacity geography | 1990–2032F, eleven snapshots |
| Blank semiconductor-wafer shipments | 2007–2025, annual |
| BACI silicon and mixed downstream trade | 2002–2024, annual |
| Electronic-grade polysilicon | 2023 volume and 2025 concentration snapshots |
| Operating fab capacity by chip type | September 2025 snapshot |

The asymmetry is intentional. Public longitudinal data exist for fabs and
global semiconductor-wafer shipments, but comparable country time series for
electronic-grade polysilicon and blank semiconductor wafers are not public.
The page labels those gaps rather than filling them with mixed customs codes.

## Rebuild and view

From the repository root:

```text
python silicon-chip/record_semiconductor.py
python silicon-chip/extract_baci.py
python -m http.server 8765
```

Then open `http://localhost:8765/silicon-chip/silicon-chain.html`.
