"""Build the evidence layer for the unpublished lithium-ion battery-chain pilot."""
from __future__ import annotations

import json
import os

import openpyxl


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "battery_chain.json")

SOURCES = {
    "usgs_history": {"title": "USGS, Historical Statistics for Mineral and Material Commodities", "year": 2024, "url": "https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities"},
    "iea_2023": {"title": "IEA, Global EV Outlook 2023 — Trends in batteries", "year": 2023, "url": "https://www.iea.org/reports/global-ev-outlook-2023/trends-in-batteries", "licence": "CC BY 4.0"},
    "iea_secure_2024": {"title": "IEA, Batteries and Secure Energy Transitions", "year": 2024, "url": "https://www.iea.org/reports/batteries-and-secure-energy-transitions/status-of-battery-demand-and-supply", "licence": "CC BY 4.0"},
    "iea_ev_2025": {"title": "IEA, Global EV Outlook 2025 — Electric vehicle batteries", "year": 2025, "url": "https://www.iea.org/reports/global-ev-outlook-2025/electric-vehicle-batteries", "licence": "CC BY 4.0"},
    "iea_minerals_2025": {"title": "IEA, Global Critical Minerals Outlook 2025 — Beyond NMC batteries", "year": 2025, "url": "https://www.iea.org/reports/global-critical-minerals-outlook-2025/beyond-nmc-batteries-supply-chain-issues-for-emerging-battery-technologies", "licence": "CC BY 4.0"},
    "iea_ev_2026": {"title": "IEA, Global EV Outlook 2026 — Manufacturing and trade", "year": 2026, "url": "https://www.iea.org/reports/global-ev-outlook-2026/manufacturing-and-trade", "licence": "CC BY 4.0"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

HISTORY_SPECS = {
    "lithium": {"file": "lithium.xlsx", "sheet": "Lithium statistics", "column": 8, "unit": "tonnes lithium content"},
    "cobalt": {"file": "cobalt.xlsx", "sheet": "Cobalt", "column": 12, "unit": "tonnes cobalt content"},
    "nickel": {"file": "nickel.xlsx", "sheet": "Nickel", "column": 9, "unit": "tonnes nickel content"},
    "graphite": {"file": "graphite.xlsx", "sheet": "Graphite", "column": 8, "unit": "tonnes natural graphite, gross weight"},
    "manganese": {"file": "manganese.xlsx", "sheet": "Manganese", "column": 10, "unit": "tonnes manganese content"},
}


def histories():
    output = {}
    for mineral, spec in HISTORY_SPECS.items():
        path = os.path.join(ROOT, "raw", "usgs_hist", spec["file"])
        sheet = openpyxl.load_workbook(path, data_only=True, read_only=True)[spec["sheet"]]
        values = {}
        for row in sheet.iter_rows(min_row=6, values_only=True):
            if isinstance(row[0], int) and isinstance(row[spec["column"]], (int, float)):
                values[row[0]] = row[spec["column"]]  # last published duplicate wins
        series = [{"year": year, "world_tonnes": round(value)} for year, value in sorted(values.items())]
        output[mineral] = {
            "unit": spec["unit"], "coverage": f"{series[0]['year']}-{series[-1]['year']}",
            "source": "usgs_history", "series": series,
            "boundary": "Total world mineral output across all end uses; not battery demand or battery-grade supply.",
        }
    return output


def build():
    data = {
        "title": "Lithium-ion battery chain evidence",
        "status": "unpublished pilot",
        "updated": "2026-08-17",
        "principle": "Mineral output, battery-grade refining, active-material production, cell output, capacity and trade are separate measures.",
        "chain": [
            {"stage": "Mine", "detail": "Lithium, nickel, cobalt, manganese and natural graphite"},
            {"stage": "Refine", "detail": "Battery-grade chemicals, metals and spherical graphite"},
            {"stage": "Active materials", "detail": "Cathode powders and graphite-based anode materials"},
            {"stage": "Cell", "detail": "Electrodes, separator and electrolyte assembled into cells"},
            {"stage": "Pack", "detail": "Cells integrated with cooling, controls and structure"},
            {"stage": "Use & recover", "detail": "EVs and storage, followed by reuse or recycling"},
        ],
        "mineral_histories": histories(),
        "battery_demand_share": {
            "source": "iea_2023", "metric": "share of each mineral's demand used for EV batteries",
            "years": {
                "2017": {"lithium": 0.15, "cobalt": 0.10, "nickel": 0.02},
                "2022": {"lithium": 0.60, "cobalt": 0.30, "nickel": 0.10},
            },
            "boundary": "EV batteries only; excludes other batteries and non-battery uses.",
        },
        "mine_to_refine_2023": {
            "source": "iea_ev_2025", "year": 2023,
            "rows": [
                {"material": "Lithium", "mine": "Australia + Chile + China", "mine_share": 0.85, "refine": "China", "refine_share": 0.65, "note": "Chile supplied another 25% of refining."},
                {"material": "Nickel", "mine": "Indonesia", "mine_share": 0.50, "mine_precision": "over", "refine": "China + Indonesia", "refine_share": 0.60, "refine_precision": "over"},
                {"material": "Cobalt", "mine": "DR Congo", "mine_share": 0.65, "mine_precision": "almost", "refine": "China", "refine_share": 0.75},
                {"material": "Graphite", "mine": "China", "mine_share": 0.80, "refine": "China", "refine_share": 0.90, "refine_precision": "over"},
            ],
            "boundary": "Graphite refining is battery-grade; other refining measures follow the IEA definitions. Shares are rounded source claims.",
        },
        "downstream_production_2025": {
            "source": "iea_ev_2026", "year": 2025, "scope": "EV battery supply chain",
            "stages": [
                {"stage": "Cathode active material", "china_share": 0.85, "precision": "about"},
                {"stage": "Anode active material", "china_share": 0.90, "precision": "more than"},
                {"stage": "Battery cells", "china_share": 0.80, "precision": "over"},
                {"stage": "Electric cars", "china_share": 0.70, "precision": "reported"},
            ],
        },
        "cell_capacity_2024": {
            "source": "iea_ev_2025", "year": 2024, "world_twh_per_year": 3.3,
            "china_capacity_share": 0.85, "china_production_share": 0.80,
            "demand_multiple": 3.0,
            "boundary": "Nameplate cell capacity, actual cell production and EV/storage demand are different measures.",
        },
        "chemistry_transition": {
            "source_2022": "iea_2023", "source_2024": "iea_ev_2025", "source_lfp_production": "iea_minerals_2025",
            "lfp_share": [{"year": 2022, "share": 0.29, "precision": "just under"}, {"year": 2024, "share": 0.49, "precision": "nearly"}],
            "2022_market": {"NMC": 0.60, "LFP": 0.29, "NCA": 0.08, "Other": 0.03},
            "lfp_china_2024": {"cathode_material_share": 0.98, "cell_share": 0.98, "precision": "over"},
            "boundary": "Chemistry shares describe EV battery deployment; LFP production shares describe physical production.",
        },
        "cost_change": {
            "source": "iea_secure_2024", "metric": "average battery costs", "series": [{"year": 2010, "index": 100}, {"year": 2023, "index": 10}],
            "claim": "Average battery costs fell by about 90% from 2010 to 2023.",
            "boundary": "Indexed two-point claim, not an annual price series.",
        },
        "trade_context": {
            "source": "baci", "coverage": "2017-2024", "classification": "HS17", "file": "out/battery_trade.json",
            "boundary": "HS 850760 mixes cells, modules and packs. Mineral chemical codes cover all grades and end uses.",
        },
        "boundaries": [
            "The five mineral histories cover all end uses and have different terminal years.",
            "Mine concentration cannot be substituted for battery-grade refining concentration.",
            "Capacity is potential annual output; production is realised output.",
            "Cathode chemistry changes which minerals matter, so there is no timeless single battery basket.",
            "Customs value does not locate factories or measure GWh capacity.",
        ],
        "sources": SOURCES,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("WROTE", OUT)
    for mineral, row in data["mineral_histories"].items():
        print(mineral, row["coverage"], len(row["series"]), "observations")
    return data


if __name__ == "__main__":
    build()
