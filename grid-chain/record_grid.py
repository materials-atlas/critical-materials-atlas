"""Build the evidence JSON for the unpublished electricity-grid chain pilot."""
from __future__ import annotations

import json
import os

import openpyxl


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "grid_chain.json")

SOURCES = {
    "usgs_copper": {"title": "USGS Historical Statistics for Mineral and Material Commodities: Copper", "year": 2023, "url": "https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities"},
    "usgs_aluminium": {"title": "USGS Historical Statistics for Mineral and Material Commodities: Aluminum", "year": 2023, "url": "https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities"},
    "iea_grids_2023": {"title": "IEA, Electricity Grids and Secure Energy Transitions", "year": 2023, "url": "https://www.iea.org/reports/electricity-grids-and-secure-energy-transitions/executive-summary"},
    "iea_investment_2024": {"title": "IEA, World Energy Investment 2024", "year": 2024, "url": "https://www.iea.org/reports/world-energy-investment-2024/overview-and-key-findings"},
    "iea_transmission_2025": {"title": "IEA, Building the Future Transmission Grid", "year": 2025, "url": "https://www.iea.org/reports/building-the-future-transmission-grid"},
    "doe_lpt_2024": {"title": "US DOE, Large Power Transformer Resilience Report", "year": 2024, "url": "https://www.energy.gov/sites/default/files/2024-10/EXEC-2022-001242%20-%20Large%20Power%20Transformer%20Resilience%20Report%20signed%20by%20Secretary%20Granholm%20on%207-10-24.pdf"},
    "doe_distribution_2024": {"title": "US DOE, DOE and Industry Team Up to Keep the Lights on for America", "year": 2024, "url": "https://www.energy.gov/oe/articles/doe-and-industry-team-keep-lights-america"},
    "doe_conductors_2023": {"title": "US DOE, Advanced Conductor Scan Report", "year": 2023, "url": "https://www.energy.gov/sites/default/files/2024-08/Advanced%20Conductor%20Report%20December%202023.pdf"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}


def usgs_series(filename, sheet, value_column, material, endpoint):
    path = os.path.join(ROOT, "raw", "usgs_hist", filename)
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = []
    for row in workbook[sheet].iter_rows(min_row=6, values_only=True):
        year, value = row[0], row[value_column - 1]
        if not isinstance(year, int) or year > endpoint or not isinstance(value, (int, float)):
            continue
        rows.append({"year": year, "tonnes": round(value)})
    return {
        "material": material,
        "metric": "world production",
        "unit": "metric tonnes of contained metal",
        "coverage": f"{rows[0]['year']}-{rows[-1]['year']}",
        "series": rows,
    }


def build():
    data = {
        "title": "Electricity-grid chain evidence",
        "status": "unpublished pilot",
        "updated": "2026-08-17",
        "principle": "Grid kilometres, investment, metal production, equipment lead times and customs trade are separate measures.",
        "chain": [
            {"stage": "Metals & steel", "detail": "Copper, aluminium and electrical steel; mining, refining and rolling are distinct."},
            {"stage": "Conductors & cores", "detail": "Wire rod, stranded conductor, cable and grain-oriented transformer steel."},
            {"stage": "Equipment", "detail": "Transformers, switchgear, insulators, converters and protection systems."},
            {"stage": "Network assets", "detail": "Substations plus overhead, underground and submarine lines."},
            {"stage": "Power system", "detail": "Transmission and distribution connect generation, storage and demand."},
            {"stage": "Operate & renew", "detail": "Maintain, uprate, replace, recover and recycle assets over decades."},
        ],
        "material_history": {
            "sources": ["usgs_copper", "usgs_aluminium"],
            "series": [
                usgs_series("copper.xlsx", "Copper", 13, "Copper", 2020),
                usgs_series("aluminum.xlsx", "Aluminum", 16, "Aluminium", 2021),
            ],
            "boundary": "Economy-wide world production, not grid consumption. The series establish long-run material scale only.",
        },
        "network_task": {
            "source": "iea_grids_2023",
            "published": 2023,
            "existing_grid_million_km": 80,
            "add_or_refurbish_by_2040_million_km": 80,
            "queued_renewables_gw": 1500,
            "queue_reference_year": 2022,
            "queue_multiple_of_2022_solar_wind_additions": 5,
            "boundary": "The 2040 figure combines new and refurbished lines; it is not 80 million kilometres of wholly new construction.",
        },
        "investment_anchors": {
            "sources": ["iea_investment_2024", "iea_grids_2023"],
            "unit": "billion USD per year",
            "points": [
                {"period": "2015-2021", "value": 300, "qualifier": "around", "meaning": "observed annual grid investment plateau"},
                {"period": "2024", "value": 400, "qualifier": "expected", "meaning": "annual grid investment"},
                {"period": "2030", "value": 600, "qualifier": "more than", "meaning": "annual investment needed"},
            ],
            "boundary": "Published anchors with different statuses, not an interpolated annual time series or a forecast of metal demand.",
        },
        "conductor_choice": {
            "source": "doe_conductors_2023",
            "facts": [
                {"statement": "Aluminium has roughly 60% of copper's electrical conductivity by equal cross-sectional area.", "implication": "An equivalent conductor generally needs more aluminium cross-section."},
                {"statement": "Aluminium can carry roughly twice as much current as copper by equal weight.", "implication": "Low weight favours aluminium in overhead spans."},
                {"statement": "Steel-reinforced aluminium conductor has been used since the early 1900s and is the world's most widely used overhead conductor type.", "implication": "Substitution is an old engineering architecture, not a recent emergency response."},
            ],
            "boundary": "Material choice depends on conductivity, strength, weight, diameter, connections, route, losses and lifetime cost; there is no universal copper-to-aluminium ratio.",
        },
        "transformer_bottleneck": {
            "global": {
                "source": "iea_transmission_2025",
                "as_of": 2025,
                "cable_procurement_years": [2, 3],
                "large_transformer_procurement_years_up_to": 4,
                "dc_cable_procurement_years_more_than": 5,
                "power_transformer_real_price_change_since_2019": 0.75,
                "cable_real_price_change_since_2019": "nearly doubled",
            },
            "us_distribution_case": {
                "source": "doe_distribution_2024",
                "series": [
                    {"year": 2019, "lead_time_months": [3, 6]},
                    {"year": 2023, "lead_time_months": [12, 30]},
                ],
                "boundary": "US distribution transformers only; not a global series and not large power transformers.",
            },
            "us_large_transformer_anatomy": {
                "source": "doe_lpt_2024",
                "inputs": ["grain-oriented electrical steel", "continuously transposed copper wire", "insulation"],
                "goes_cost_share": 0.25,
                "copper_wire_cost_share": 0.25,
                "survey_year": 2020,
                "boundary": "Approximate shares of final US large-power-transformer production cost in a Commerce survey; not physical mass shares or global values.",
            },
        },
        "trade_context": {
            "source": "baci",
            "coverage": "2002-2024",
            "file": "out/grid_trade.json",
            "boundary": "Four grouped customs baskets provide context; none measures total grid investment, production capacity or project origin.",
        },
        "boundaries": [
            "Economy-wide copper and aluminium production is not grid material demand.",
            "Overhead, underground and submarine networks use different conductor and insulation architectures.",
            "Grid investment is spending, not kilometres, tonnes or transformer output.",
            "A bottleneck can sit in specialised processing and equipment factories even when the bulk metal is available.",
            "Export concentration is not the same as production concentration or import dependence.",
        ],
        "sources": SOURCES,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("WROTE", OUT)
    for series in data["material_history"]["series"]:
        first, last = series["series"][0], series["series"][-1]
        print(series["material"], first, "->", last)
    return data


if __name__ == "__main__":
    build()
