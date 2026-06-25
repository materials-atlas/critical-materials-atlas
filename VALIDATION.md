# Validation — spot-checks against published figures

A sanity check that the atlas's layers agree with widely-published shares. Benchmarks are approximate
and rounded (USGS Mineral Commodity Summaries 2024; IEA *Global Critical Minerals Outlook* 2024; trade
from CEPII BACI 2023). The point is order-of-magnitude agreement on the headline actor, not decimals.

## Mine production (USGS layer)

| Material | Atlas (USGS layer) | Published benchmark | Agree |
|---|---|---|:--:|
| Cobalt | DR Congo 76% | DRC ~70–74% of world mine output (USGS 2023) | ✓ |
| Niobium | Brazil 88% | Brazil ~88–90% (USGS) | ✓ |
| Gallium | China 98% | China ~98% of primary low-purity gallium (USGS/IEA) | ✓ |
| Lithium | Australia 52% | Australia ~52% of mined lithium 2023 (USGS) | ✓ |
| Platinum | South Africa 70% | South Africa ~70% of mined Pt (USGS / WPIC) | ✓ |
| Manganese | South Africa 36% | South Africa ~36% of mine output (USGS) | ✓ |
| Bauxite | Australia 27% | Australia ~27%, Guinea ~23% (USGS) | ✓ |

## Refining / processing (IEA layer)

| Material | Atlas (IEA layer) | Published benchmark | Agree |
|---|---|---|:--:|
| Cobalt | China 76% | China ~75–77% of refined cobalt (IEA / Benchmark Minerals) | ✓ |
| Lithium | China 65% | China ~65–72% of chemical lithium refining (IEA) | ✓ |
| Rare-earth magnets | China 90% | China ~90%+ of magnet/REE processing (IEA) | ✓ |
| Natural graphite | China 95% | China ~95% of spherical (anode) graphite (IEA) | ✓ |
| Gallium | China 98% | China ~98% of refined gallium (IEA) | ✓ |

## Where trade ≠ production (and why)

These are not disagreements — they show the three layers measuring different things, which is the whole
point of the atlas:

- **Bauxite** — mine output is led by **Australia (27%)**, but **Guinea dominates traded ore (~75% of
  exports)**. Australia refines most of its bauxite into alumina domestically and exports less ore;
  Guinea exports raw. *Production ≠ trade.*
- **Lithium** — mined mostly in **Australia (spodumene, 52%)**, but the top *exporter by value* of the
  carbonate code is **Chile (76%)**: Australia ships lower-value concentrate, Chile ships refined
  carbonate. *Value ≠ tonnage, and the HS code captures the refined chemical.*
- **Cobalt** — mined in **DR Congo (76%)**, refined in **China (76%)**, yet the top *exporter* of the
  oxide code is **Finland (26%)** — the classic mine → refiner → exporter split the atlas exists to show.

## Known caveat surfaced by this check

Trade-derived "refiner" includes re-export hubs. For gallium, raw BACI exports rank Hong Kong and
Singapore among the top exporters though they refine nothing — the atlas now greys the curated entrepôt
set (HK, SG, UAE, Panama, Macau, Gibraltar) so they don't read as refiners. See `methodology.html`
(Limitations).
