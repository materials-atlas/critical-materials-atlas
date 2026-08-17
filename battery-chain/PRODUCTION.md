# Sources and production record

## USGS mineral histories

`record_battery.py` reads the local USGS historical-statistics workbooks for lithium, cobalt, nickel, natural graphite and manganese. Published units and terminal years are retained. Four series begin around 1900; the comparable lithium-content series begins in 2000. Duplicate nickel year 2019 is resolved by retaining the last published workbook row. These histories cover all end uses.

## IEA demand, chemistry and chain stages

The 2017 and 2022 mineral-demand anchors come from *Global EV Outlook 2023*: EV batteries represented about 15%→60% of lithium demand, 10%→30% of cobalt demand and 2%→10% of nickel demand.

The 2023 mine/refine claims and 2024 cell-capacity measures come from *Global EV Outlook 2025*. The page preserves the source's rounded language. Capacity exceeded 3 TWh/year, was roughly three times EV and storage demand, and was 85% located in China; China's actual cell-production share was 80%.

The 2025 cathode, anode, cell and electric-car production shares come from *Global EV Outlook 2026*. They describe production location, not corporate ownership.

The chemistry anchors use *Global EV Outlook 2023* and *2025*: LFP was just under 30% of EV batteries in 2022 and nearly half in 2024. The 2025 critical-minerals report states that China produced over 98% of LFP cathode material and cells in 2024.

## BACI trade

`extract_baci.py` scans the local CEPII BACI HS17 archive for 2017–2024. It intentionally does not splice a broader HS02 accumulator code onto HS 850760. Values are BACI `v × 1000` US dollars.

- 250410: natural graphite in powder or flakes; all grades and uses.
- 282520: lithium oxide and hydroxide; all grades and uses.
- 283691: lithium carbonate; all grades and uses.
- 850760: lithium-ion accumulators, potentially including cells, modules and packs.

Trade is a cross-border ledger. It is not interpreted as GWh production, operating capacity or company ownership.
