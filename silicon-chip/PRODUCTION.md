# Who makes it at home (solar factory layer)

Unpublished. Sits next to `out/silicon_stages.json` (trade).
Reproduce: `python silicon-chip/record_iea_pv.py`
Local report: `raw/iea/IEA-PVPS-Task-1-Trends-Report-2024.pdf`

## What this layer is

IEA can see the **solar** factory. It cannot see the **chip** factory.

So this fill-in is for the solar half of the mixed trade codes — and a later solar product page. It is not a chip-production table.

## 2023 production (IEA-PVPS Trends 2024)

These are **production** shares, not capacity. That is the right match for Atlas “who makes it.”

| Stage | China | Next | World total | Chart |
|---|---|---|---|---|
| Polysilicon (PV + a little semiconductor) | **92%** | Germany 4%, US 2%, Malaysia 2% | 1.61 Mt (of which ~39 kt semiconductor) | Fig. 4.2 |
| Solar wafers | **98%** | Vietnam 2% | 682 GW (China 668 GW) | Fig. 4.3 |
| Solar cells | **92%** | Malaysia 2%, Vietnam 2% | 644 GW | Fig. 4.4 |
| Solar modules | **85%** | Vietnam 3%, India 3% | 612 GW | Fig. 4.5 |

Newer IEA text (ETP 2026, year 2024): China still about **90%** of wafer + polysilicon supply and **80%** of modules. Same picture, one year on, no full country table.

More than **98%** of all polysilicon made in 2023 went to solar. Chip-grade poly is the small remainder (~39 kt).

## Next to our 2024 trade (the Atlas point)

| | China *makes* (IEA-PVPS 2023) | China *exports* (BACI 2024) |
|---|---|---|
| High-purity silicon (280461) | 92% of polysilicon | **13%** of export value |
| Wafers (381800) | 98% of solar wafers | **22%** of export value (58% of tonnes) |

China makes almost all of the solar factory product and uses most of it at home. The customs line therefore understates the factory. Same finding as cobalt: the exporter is not the source.

Vietnam as top importer of 280461 also fits: IEA says China shipped ~70 GW of wafers to cell plants in Vietnam, Malaysia, Thailand and neighbours.

## What we still cannot say

- Who makes **chip-grade** polysilicon by country. USGS does not publish that table. IEA folds the ~39 kt into the 92% chart and labels it.
- Who makes **semiconductor wafers** (Shin-Etsu, SUMCO, …). No public IEA/USGS country series. Stays a note.

Do not put IEA solar-factory shares on a page titled “chips.”
