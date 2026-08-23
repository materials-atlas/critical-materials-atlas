# Sources and production record

## IRENA deployment panel

`fetch_irena.py` queries IRENA's official PxWeb API, April 2026 vintage. It retrieves world wind capacity and country-level total, onshore and offshore capacity for 2000–2025, summing on-grid and off-grid observations. Region aggregates embedded in the country table are removed. The resulting raw cache is ignored under the repository's existing `raw/` policy; `out/wind_chain.json` contains the compact evidence used by the page.

Capacity is maximum net generating capacity at calendar year end. Annual net change is the difference between consecutive stocks; it is not gross turbine commissioning.

## Manufacturing and suppliers

The IEA's 2023 manufacturing briefing estimated prospective 2025 component capacity from announced projects: 100–110 GW for onshore components, with about 60% in China, and about 30 GW offshore, with 70–80% in China. These are vintage-2023 capacity estimates.

GWEC's 2026 supply-side release reports 28,395 turbines and 178 GW mechanically installed in 2025, with 165 GW commissioned. Its five largest OEMs by installed capacity were Chinese. Supplier headquarters and installation location remain separate.

## Drivetrains and materials

DOE's 2013 offshore supply-chain study reports global direct-drive shares of 17.6% in 2010 and 21.2% in 2011; the 2012 DOE market report cites 19.5% for 2012. Direct drive includes permanent-magnet and non-permanent-magnet architectures.

The JRC 2024 note supplies kg/MW estimates. The pilot compares geared doubly-fed induction, direct-drive electrically excited and direct-drive permanent-magnet systems. It preserves ranges and treats the values as technology cases, not universal recipes.

## BACI trade

`extract_baci.py` applies the same HS02 2002–2016 / HS17 2017–2024 stitch used elsewhere in the Atlas. Values are BACI `v × 1000` US dollars.

- 850231: wind-powered generating sets—the cleanest finished-turbine basket.
- 730820: iron or steel towers and lattice masts, including non-wind uses.
- 841290: parts of heading 8412 engines and motors, including non-wind uses.
- 850300: parts for motors and generators across many applications.

Only HS 850231 is interpreted as wind equipment. The other codes provide broad customs context.
