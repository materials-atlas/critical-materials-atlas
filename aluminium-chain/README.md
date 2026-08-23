# Aluminium chain pilot (unpublished)

Bauxite → alumina → smelting → the metal. Bauxite is mined roughly equally in
Australia, Guinea and China, but smelting is one of the most electricity-intensive
industrial processes there is, so the chokepoint is the smelter, not the mine —
China's share jumps from ~21% (mining) to ~59% (smelting). Isolated on
`wip/value-chains`; not linked from the live Atlas.

## The finding
Aluminium is congealed electricity. Smelting takes 12–15 MWh/tonne and is ~40% power
by cost, so smelters went where power was cheapest (China's coal, plus hydro/gas
elsewhere). The metal's carbon footprint therefore depends on the smelter's power
source — a trade variable under CBAM. Recycled aluminium needs ~5% of the energy.

## Files
- `record_aluminium.py` → `out/aluminium_chain.json` (uniform schema; 2019–2024 bauxite history).
- `extract_baci.py` → `out/aluminium_trade.json` (HS 260600/281820/760110/760120).
- `aluminium-chain.html` — research page (shared renderer).
- `NOTES.md`, `PRODUCTION.md`.
