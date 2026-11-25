# Phosphate reserves and fertilizer supply

The [research note](phosphate-food-chain.html) and [claim audit](PRODUCTION.md) share a dated snapshot of the evidence. Run these commands from the repository root.

    python phosphate-food-chain/record_phosphate.py
    python phosphate-food-chain/plot_phosphate.py
    python build_chokepoint_map.py

The record builder works offline and uses the standard library. Matplotlib is used for the four figures. To refresh the two public data snapshots, run `python phosphate-food-chain/fetch_phosphate_data.py` before rebuilding and review source revisions. A refresh uses the latest release of each provider for the specified years.

## Inputs and calculations

| Input | Measure | Coverage |
| --- | --- | --- |
| [USGS table transcription](usgs_2025.csv) | Thousand metric tonnes of rock | Mineral Commodity Summaries 2026, World Mine Production and Reserves. Includes all country rows, the grouped remainder and the rounded world line. |
| [Comext snapshot](out/phosphate_comext.json) | Kilograms of net product mass and nominal euros | DS-045409, 2023–2024, annual EU-27 external imports, thirteen CN8 codes listed in [products.csv](products.csv). Query, product and country labels and observation flags are retained. |
| [FAOSTAT snapshot](out/phosphate_faostat.json) | Tonnes of P₂O₅ | RFN item 3103. Production and agricultural use for EU-27 (5707). Imports and exports for EU-27 excluding intra-trade (57070). World agricultural use (5000) is also retained. |
| [Frozen BACI extract](out/phosphate_trade.json) | Nominal USD and original quantity aggregates | BACI V202601. HS02 through 2016 and HS17 from 2017 to 2024. The revised note uses only values and value-based export HHI. |

### Concentration

USGS country percentages divide by the official rounded world totals. The HHI divides each row by the sum of named rows and the grouped remainder. The lower bound includes only the squared shares of named countries. Adding the squared share of the grouped remainder places all that mass in one additional country. The bounds describe unresolved composition conditional on the published rows. They do not represent sampling error.

For each Comext country and product group, the script adds net mass across the listed CN8 codes. Aggregate partner areas and intra-EU flows are excluded. Codes for unspecified or confidential extra-EU origins remain in the denominator. The reported code-level mass and value reconcile with the sum of named and unnamed partners. Absence of a mass or value cell in an individual origin record is retained in the source snapshot. HHI divides mass by the official total for the group. Its lower bound sums the squares of named shares. Its upper bound assigns all unresolved mass to the largest named origin. The group called Other finished is a selected group of mixed products. No group is added to another stage to estimate phosphorus supply.

### Nutrient accounting

Elemental P equals P₂O₅-equivalent tonnes times 0.4364, calculated from atomic masses in the script. The DAP and MAP example applies published nominal grades under two stated assumptions. It does not estimate the composition of mixed customs headings.

Net imports equal external imports minus external exports. Apparent supply equals production plus net imports before a stock adjustment. Their ratio is a conditional measure of net import reliance in the FAOSTAT system. Agricultural use is a separate FAOSTAT series. The remaining gap is reported without allocation. The Eurostat product rows are not treated as a complete reconciliation to the FAOSTAT nutrient total.

### Stress test

The scenario cuts 2024 deliveries from the leading DAP origin by half. It subtracts assumed replacement from the lost imports and divides the remaining mass by total baseline DAP imports. Replacement can occur within the model year and all other volumes are held fixed. The model places no bounds on alternative production or shipping capacity. It does not calculate unmet agricultural demand.

The new analysis uses public aggregates in the product and year scopes above. Raw bilateral BACI and UN Comtrade data, trade mirror comparisons, actual product grades, plant capacities, inventories and demand response are outside the verified evidence.
