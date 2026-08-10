# Validation — spot-checks against published figures

A sanity check that the atlas's layers agree with widely-published shares. Benchmarks are approximate
and rounded (USGS Mineral Commodity Summaries 2024; IEA *Global Critical Minerals Outlook* 2024; trade
from CEPII BACI 2023). The point is order-of-magnitude agreement on the headline actor, not decimals.

## Mine production (USGS layer)

| Material | Atlas (USGS layer) | Published benchmark | Agree |
|---|---|---|:--:|
| Cobalt | DR Congo 74% | DRC ~70–74% of world mine output (USGS 2024) | ✓ |
| Niobium | Brazil 90% | Brazil ~88–90% (USGS) | ✓ |
| Gallium | China 98% | China ~98% of primary low-purity gallium (USGS/IEA) | ✓ |
| Lithium | Australia 48% | Australia ~47–52% of mined lithium 2023 (USGS) | ✓ |
| Platinum | South Africa 67% | South Africa ~67–70% of mined Pt (USGS / WPIC) | ✓ |
| Manganese | South Africa 36% | South Africa ~36% of mine output (USGS) | ✓ |
| Bauxite | Australia 24% | Australia ~24%, Guinea ~24% (USGS 2024) | ✓ |

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

- **Bauxite** — mine output is led by **Australia (24%, tied with Guinea)**, but **Guinea dominates
  traded ore (~72% of exports)**. Australia refines most of its bauxite into alumina domestically and
  exports less ore; Guinea exports raw. *Production ≠ trade.*
- **Lithium** — mined mostly in **Australia (spodumene, 48%)**, but the top *exporter by value* of the
  carbonate code is **Chile (75%)**: Australia ships lower-value concentrate, Chile ships refined
  carbonate. *Value ≠ tonnage, and the HS code captures the refined chemical.*
- **Cobalt** — mined in **DR Congo (74%)**, refined in **China (76%)**, yet the top *exporter* of the
  oxide code is **Finland (29%)** — the classic mine → refiner → exporter split the atlas exists to show.

## Reserves, reserve life & import reliance (USGS layer, added Aug 2026)

These three layers are transcribed directly from the **USGS Mineral Commodity Summaries 2024**, so a
check against USGS is confirmation of *transcription*, not an independent second source. Two things are
worth verifying: (i) the reserve leaders match widely-cited facts, and (ii) **reserve life is
arithmetically consistent** — it must equal world reserves ÷ world annual production, computed from the
same two layers.

| Material | Reserves (atlas) | Reserve life | Sanity check | OK |
|---|---|--:|---|:--:|
| Niobium | Brazil 90% | 215 yr | Brazil holds ~90% of reserves and mines ~90% — huge base, modest output → very long life | ✓ |
| Cobalt | DR Congo 55% | 48 yr | DRC ~4.0 Mt of ~11 Mt world reserves ≈ 55%; ~48× the ~230 kt annual output | ✓ |
| Lithium | Chile 33%, Australia 22% | 156 yr | Chile has the largest reserves (~9.3 Mt), not the largest mine output — reserves ≠ production | ✓ |
| Platinum (PGM) | South Africa 89% | 158 yr | SA ~90% of PGM reserves, in line with its mine dominance | ✓ |
| Manganese | South Africa 32% | 95 yr | SA holds the largest manganese reserves (USGS) | ✓ |

**US net import reliance** (USGS NIR, share of apparent consumption from net imports): **niobium 100%**,
**gallium 100%**, **manganese 100%**, **cobalt 67%**, **bauxite >75%** — all consistent with the USGS
2024 commodity pages, which list these among the materials the US does not mine at scale. Recorded for
**28 of 32** materials; the 4 with no clean single-number NIR in the source (e.g. shared-code or
compound reports) are left blank rather than guessed.

## Known caveat surfaced by this check

Trade-derived "refiner" includes re-export hubs. For gallium, raw BACI exports rank Hong Kong and
Singapore among the top exporters though they refine nothing — the atlas now greys the curated entrepôt
set (HK, SG, UAE, Panama, Macau, Gibraltar) so they don't read as refiners. See `methodology.html`
(Limitations).
