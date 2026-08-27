# IEA Global Critical Minerals Outlook 2026 — extracted data

Source: IEA, *Global Critical Minerals Outlook 2026* (published 16 July 2026, revised July 2026),
CC BY 4.0. `https://www.iea.org/reports/global-critical-minerals-outlook-2026`

Reference sheet of the concentration figures and context relevant to the Critical Materials Atlas,
transcribed from the report during the Aug-2026 verification pass. Used to anchor `basis.json` notes
and cross-check `source_ledger.json`. **These are IEA figures — where they disagree with USGS, the
atlas keeps the USGS-quoted number for `measured` tags and records the disagreement.**

## Country market shares, 2025 (export-control table, p.39)

Country that controls / leads each stage, with the IEA "market share (2025)" figure:

| Material | Country | Share (2025) | Note |
|---|---|---|---|
| Aluminium (bauxite) | Guinea | 34% | share of mining |
| Antimony | China | 44% | **share of refining** (notably lower than industry's ~75-90%) |
| Bismuth | China | 73% | (vs USGS verbatim 88%) |
| Cobalt | DRC | 66% | mine (vs atlas BGS/USGS ~75%) |
| Gallium | China | 99% | confirms atlas |
| Germanium | China | 94% | atlas was ~60% — corrected up to ~90% |
| Graphite (mined) | Mozambique | 4% | |
| Graphite (refined) | China | 94% | atlas anode was ~100% — tightened to ~95% |
| Indium | China | 86% | (vs USGS verbatim 70%) |
| Lithium | Zimbabwe | 10% | (mine, a specific controlling country) |
| Manganese | Gabon | 25% | (mine; China refining is ~95-97% per p.31) |
| Molybdenum | China | 41% | atlas: not a chokepoint (diversified) — consistent |
| Nickel | Philippines | 11% | (Indonesia is the ~75% refiner, p.31) |
| Rare Earths | China | 91% | atlas ~90% (chart p.31 shows ~85% & declining) |
| Sulphuric acid | China | 34% | |
| Tellurium | China | 73% | |
| Tungsten | China | 76% | atlas ~79% (USGS mine) |
| Batteries (LFP) | China | 99% | share of cell manufacturing |
| Lithium refining | China | 71% | confirms atlas "most" |

## Refined-production shares, 2025 (chart p.31, "Share of refined material production by country")

China (or top refiner) share of REFINED output, 2025, with 2023 top-producer dot:
- Copper ~45%
- Lithium ~68-70% (China chemical conversion)
- Nickel ~75% (Indonesia; up from ~41% in 2023)
- Cobalt ~75% (China) — **confirms atlas ~75%**
- Graphite ~93-95% (China, battery-grade)
- Manganese ~97% (China, sulphate) — **atlas raised ~90% → ~95%**
- Rare earths ~85% (China) — DOWN from ~91% in 2023; the one chain where concentration fell
  (MP Materials US + Lynas Malaysia came online)

## Mining shares, 2025 (chart p.32, "Share of mined output by country")

China/top-miner share of MINED output, 2025:
- Copper ~stable, top miner ~25%
- Lithium ~25% China (Australia + Chile larger) — mining diversified
- Nickel ~65% Indonesia (up)
- Cobalt ~75% DRC
- Graphite ~80% China (mined natural graphite)
- Manganese ~63% Africa
- Rare earths ~65-70% China (declining; dot ~57% in 2023)

## Battery supply chain, 2025 (p.73)

Verbatim: *"China processed 70-95% of global lithium, cobalt, phosphate, manganese and graphite
and produced 98% of LFP cathode materials, two-thirds of nickel-based cathode material, over 90%
of anode material and 80% of global battery cells. It also accounts for 95% of global cathode
material precursor production capacity."*
- Battery cells: China **80%** — **confirms atlas ~80%**
- Anode material: China **>90%** (refined graphite 94% per p.39)
- LFP cathode: China 98%; cathode precursor: China 95%
- Battery recycling: China ~85% pre-treatment, ~90% material recovery
- LFP = 55% of global EV batteries sold in 2025 (80% within China)

## Other data points (context / corroboration)

- **Refining concentration**: excluding rare earths, average share of the top refined supplier rose
  to **72% in 2025** (from 70% in 2020/2023). Rare earths the only decliner.
- **Copper smelting**: China 15% → **50% of global capacity** (2005→2025); >90% of capacity growth.
  Copper benchmark smelter TC/RCs settled at $0/t in 2026 (record low) → smelters lean on by-products.
- **Nuclear fuel cycle**: top three countries ~three-quarters of uranium mining, **~70% of conversion
  and enrichment capacity** (Russia the largest) — corroborates atlas nuclear (Russia ~35-45% SWU).
- **Aluminium**: China ~**60%** of primary aluminium (and alumina); bauxite ~20% China.
  Middle East = 8% of primary aluminium (one-fifth ex-China). China 45 Mt production cap hit in 2025.
- **Sulphur / sulphuric acid**: Middle East ~25% of sulphur supply; half of seaborne sulphur trade via
  Strait of Hormuz. China produces **40% of world sulphuric acid**, ~one-third of demand.
- **Helium**: US ~45%, **Qatar ~35%** of production; Qatar >half of imports for CN/IN/KR/Taiwan.
- **Strontium**: *"Iran produces more than half of global strontium supply"* — **confirms atlas ~56%**.
- **Silver in solar**: ~60% of PV cell cost, 10% of module cost (confirms atlas silver framing).
- **c-Si** = ~98% of solar PV production (technology share, NOT a China share).
- **Cost shares**: minerals ~25% of battery cell cost but ~3% of an EV; rare earths ~40% of a magnet's
  cost but <1% of a vehicle. Tripling RE prices → +0.1% car cost; tripling battery materials → +5% EV.
- **Export controls**: China-controlled tariff codes tripled since 2023; value of controlled exports
  >USD 11bn in 2025. Apr & Oct 2025 rare-earth controls; Oct 2025 battery-supply-chain controls
  (graphite anode, LFP cathode, precursors, equipment) — suspended to Nov 2026.
- **G7 target (2026)**: reduce dependence on a single non-G7 supplier for rare earths + magnets to
  below 60% by 2030.

## Atlas changes this pass drove (all committed)

- Germanium ~60% → ~90%; Manganese ~90% → ~95%; Graphite ~100% → ~95%; Steel ~54% → ~52% (worldsteel 2025).
- Confirmed unchanged: battery 80%, gallium 99%, cobalt 75%, lithium ~71%, aluminium ~60%, strontium
  >50% Iran, tungsten, nuclear top-3 ~70%.
- Cross-reference notes where IEA disagrees with USGS: bismuth (73 vs 88), indium (86 vs 70),
  antimony (44 refining vs industry 75-90) — kept `measured` on USGS quotes, disagreement recorded.
