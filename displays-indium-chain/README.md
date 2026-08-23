# Displays / indium chain pilot (unpublished)

The transparent conductive coating on almost every LCD and touchscreen is indium tin
oxide (ITO). Indium is a trace by-product of zinc, ~70% refined in China, and China
placed it under export control in 2025. Isolated on `wip/value-chains`; not linked from
the live Atlas.

## The finding
A trace input with one dominant refiner gates a mass-market product. Indium cannot be
scaled on its own (it rides on zinc), refining is ~70% China, and unwrought-indium
exports fell ~72% after the Feb-2025 controls. The relief valve is ITO-scrap recycling
in Japan and Korea. Honest limits: no long public production series (snapshot) and no
clean trade code (indium sits in the shared 811292 basket).

## Files
- `record_indium.py` → `out/indium_chain.json` (uniform schema; production snapshots + policy).
- `extract_baci.py` → `out/indium_trade.json` (HS 811292 basket + 901380 LCD; flagged context).
- `displays-indium-chain.html` — research page (shared renderer).
- `NOTES.md`, `PRODUCTION.md`.
