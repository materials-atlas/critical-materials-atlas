# Aerospace / jet-engine superalloy chain pilot (unpublished)

This research workspace follows the aerospace propulsion chain beyond the mine:
nickel, cobalt, rhenium, hafnium and titanium → superalloys → single-crystal
turbine blades → jet engines. It is isolated on `wip/value-chains`: it is not
linked from the live Atlas and does not alter any of the 32 published material
profiles.

## Reading rule

Physical production, aerospace qualification, company control and customs trade
answer different questions. The pilot keeps them separate. In particular it
never treats titanium-sponge tonnage as aerospace-qualified supply, and it does
not read rhenium from trade (rhenium has no clean HS6 line) — it reads rhenium
from USGS production.

## The finding

The chokepoint is not the ore. Each stage downstream is *more* concentrated than
the mine:

- **Rhenium** is a copper by-product (~55% Chile); world output is only ~81 t/yr
  and cannot be scaled independently of copper. ~80% goes to turbine superalloys.
- **Titanium sponge**: China makes ~71% of tonnage, but little of it is qualified
  for critical aerospace parts; the US imports aerospace sponge from Japan (~80%),
  Saudi Arabia and Kazakhstan.
- **Single-crystal blade casting** is a low-yield capability held by a few firms.
- **Jet engines** are built almost entirely by GE Aerospace, Pratt & Whitney and
  Rolls-Royce.

## Files

- `record_aerospace.py` builds the sourced evidence layer (`out/aerospace_chain.json`).
- `extract_baci.py` builds annual customs context for HS 810820, 750210, 841112,
  841122 and 841191 from the local BACI archive (`out/aerospace_trade.json`).
- `aerospace-chain.html` is the unpublished interactive research page.
- `NOTES.md` records interpretation and rejected claims.
- `PRODUCTION.md` is the source and measure ledger.
