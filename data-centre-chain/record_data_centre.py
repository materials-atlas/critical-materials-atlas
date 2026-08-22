"""Build evidence JSON for the unpublished data-centre and AI-infrastructure pilot."""
from __future__ import annotations

import json
import os

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "data_centre_chain.json")

SOURCES = {
    "iea_demand": {"title": "IEA, Energy and AI — Energy demand from AI", "year": 2025, "url": "https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai", "licence": "CC BY 4.0"},
    "iea_summary": {"title": "IEA, Energy and AI — Executive summary", "year": 2025, "url": "https://www.iea.org/reports/energy-and-ai/executive-summary", "licence": "CC BY 4.0"},
    "iea_supply": {"title": "IEA, Energy and AI — Energy supply for AI", "year": 2025, "url": "https://www.iea.org/reports/energy-and-ai/energy-supply-for-ai", "licence": "CC BY 4.0"},
    "iea_update": {"title": "IEA, Key Questions on Energy and AI — Executive summary", "year": 2026, "url": "https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary", "licence": "CC BY 4.0"},
    "iea_grid": {"title": "IEA, Building the Future Transmission Grid — Executive summary", "year": 2025, "url": "https://www.iea.org/reports/building-the-future-transmission-grid/executive-summary", "licence": "CC BY 4.0"},
    "doe_lbnl": {"title": "US DOE, 2024 Report on U.S. Data Center Energy Use — release", "year": 2024, "url": "https://www.energy.gov/articles/doe-releases-new-report-evaluating-increase-electricity-demand-data-centers"},
    "usgs": {"title": "USGS, Historical Statistics for Mineral and Material Commodities", "year": 2024, "url": "https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

HISTORY = {
    "Copper": ("copper.xlsx", "Copper", 12, "tonnes copper content", "All mine output; not data-centre cable, busbar or refined copper availability."),
    "Primary aluminium": ("aluminum.xlsx", "Aluminum", 15, "tonnes aluminium content", "All primary metal; not heat sinks, racks, cable or recycled aluminium."),
    "Tin": ("tin.xlsx", "Tin", 11, "tonnes tin content", "All mine output; solder is only one use and electronics-grade supply is not isolated."),
    "Rare earths": ("rare-earths.xlsx", "Rare earths", 7, "tonnes REO equivalent", "All rare earths; magnet exposure varies across drives, motors and cooling equipment."),
}


def histories():
    result = []
    for material, (filename, sheet_name, column, unit, boundary) in HISTORY.items():
        sheet = openpyxl.load_workbook(os.path.join(ROOT, "raw", "usgs_hist", filename), read_only=True, data_only=True)[sheet_name]
        values = {}
        for row in sheet.iter_rows(min_row=6, values_only=True):
            if isinstance(row[0], int) and isinstance(row[column], (int, float)) and row[column] > 0:
                values[row[0]] = row[column]
        rows = [{"year": year, "world_tonnes": round(value, 3)} for year, value in sorted(values.items())]
        result.append({"material": material, "unit": unit, "coverage": f"{rows[0]['year']}-{rows[-1]['year']}", "series": rows, "boundary": boundary})
    return result


def build():
    data = {
        "title": "Data-centre and AI-infrastructure evidence",
        "status": "unpublished pilot",
        "updated": "2026-08-18",
        "principle": "Compute hardware, IT power, facility capacity, grid connection, electricity use and digital service output are separate measures.",
        "chain": [
            {"stage": "Materials & chips", "detail": "Semiconductors, substrates, memory, copper, aluminium, tin, steels, polymers and specialised components."},
            {"stage": "Servers & network", "detail": "CPUs/accelerators, memory, storage and switches are integrated into boards, servers and racks."},
            {"stage": "Facility systems", "detail": "UPS, batteries, switchgear, transformers, cooling, water systems, controls and backup generation."},
            {"stage": "Grid & site", "detail": "Land, fibre, substations, transmission capacity, generation and permits connect concentrated load."},
            {"stage": "Operate", "detail": "Workload, utilisation, hardware/software efficiency and cooling determine electricity per service."},
            {"stage": "Refresh & recover", "detail": "Short IT refresh cycles coexist with longer buildings and power assets; reuse and material recovery differ."},
        ],
        "global_2024": {
            "source": "iea_demand", "electricity_twh": 415, "world_electricity_share": 0.015,
            "annual_growth_previous_five_years": 0.12,
            "regions": [{"region": "United States", "share": 0.45}, {"region": "China", "share": 0.25}, {"region": "Europe", "share": 0.15}, {"region": "Other", "share": 0.15}],
            "boundary": "Modelled electricity consumption by data centres. Regional shares are rounded and do not measure installed compute or investment.",
        },
        "electricity_outlook": {
            "source": "iea_update", "vintage": 2026,
            "points": [{"year": 2025, "twh": 485, "status": "estimate"}, {"year": 2030, "twh": 950, "status": "central projection"}],
            "world_share_2030": 0.03,
            "boundary": "A later IEA modelling vintage than the 415 TWh 2024 estimate. The values are presented as a separate outlook, not a measured annual series.",
        },
        "uncertainty_2035": {
            "source": "iea_summary", "vintage": 2025, "unit": "TWh",
            "headwinds": 700, "base": 1200, "lift_off": 1700,
            "boundary": "Scenario results, not a confidence interval. The cases vary AI uptake, efficiency, supply-chain resilience and energy bottlenecks.",
        },
        "facility_electricity": {
            "source": "iea_demand",
            "items": [
                {"component": "Servers", "share": 0.60, "precision": "around"},
                {"component": "Storage", "share": 0.05, "precision": "around"},
                {"component": "Networking", "share": 0.05, "precision": "up to"},
                {"component": "Cooling", "share_min": 0.07, "share_max": 0.30, "precision": "range"},
            ],
            "boundary": "Illustrative modern-facility shares. Cooling varies from efficient hyperscale to less-efficient enterprise sites; these items are not a universal balance summing to 100%.",
        },
        "growth_drivers_2024_2030": {
            "source": "iea_demand",
            "items": [{"driver": "Accelerated servers", "net_growth_share": 0.50, "precision": "almost"}, {"driver": "Conventional servers", "net_growth_share": 0.20, "precision": "around"}, {"driver": "Cooling and other infrastructure", "net_growth_share": 0.20, "precision": "around"}, {"driver": "Other IT equipment", "net_growth_share": 0.10, "precision": "around"}],
            "boundary": "Approximate contributions to the net increase in the IEA 2025 Base Case, not shares of total 2030 consumption.",
        },
        "us_history": {
            "source": "doe_lbnl", "observed": [{"year": 2014, "twh": 58}, {"year": 2023, "twh": 176}],
            "forecast_2028": {"low_twh": 325, "high_twh": 580, "electricity_share_low": 0.067, "electricity_share_high": 0.12},
            "boundary": "National model endpoints and a forecast range; intermediate years are not interpolated. Cryptocurrency mining is handled according to the source methodology.",
        },
        "power_supply_2024": {
            "source": "iea_supply", "basis": "physical electricity supply, not contractual procurement",
            "shares": [{"source": "Coal", "share": 0.30}, {"source": "Renewables", "share": 0.27}, {"source": "Natural gas", "share": 0.26}, {"source": "Nuclear", "share": 0.15}, {"source": "Other/rounding", "share": 0.02}],
            "boundary": "Global physical supply mix estimated by IEA. Power-purchase agreements do not by themselves change the local electricity physically consumed.",
        },
        "capacity_clocks": [
            {"clock": "Compute", "measure": "accelerators, FLOP/s or workload throughput", "warning": "Chip counts ignore utilisation, memory and network bottlenecks."},
            {"clock": "IT load", "measure": "MW delivered to servers, storage and network", "warning": "Excludes cooling and power losses."},
            {"clock": "Facility load", "measure": "MW at the meter", "warning": "Depends on cooling, UPS and operating efficiency."},
            {"clock": "Electricity", "measure": "MWh or TWh over time", "warning": "Requires load factor; a nameplate MW is not annual use."},
            {"clock": "Digital service", "measure": "training runs, tokens, queries or stored data", "warning": "Definitions and quality change quickly."},
        ],
        "grid_constraint": {
            "source": "iea_grid", "data_centre_build_years": "2–3", "cable_lead_years": "2–3", "large_transformer_lead_years": "up to 4",
            "price_change_since_2019": {"cables": "nearly doubled", "power_transformers": "+75%"},
            "boundary": "Grid-industry survey values, not data-centre-specific procurement guarantees. Project siting and permitting can add further delay.",
        },
        "material_histories": {"source": "usgs", "series": histories(), "boundary": "Economy-wide production context. These series do not measure data-centre demand, refined/component-grade availability or recycled material."},
        "trade_context": {
            "source": "baci", "coverage": "2002-2024", "file": "out/data_centre_trade.json",
            "boundary": "No clean HS basket isolates data-centre or AI equipment. Processing units, storage, converters and heat exchangers serve many end uses; services, domestic production and facility construction are omitted.",
        },
        "boundaries": [
            "A GPU shipment is not a commissioned rack, and a commissioned rack is not a grid-connected data centre.",
            "IT MW, facility MW, annual TWh and compute output cannot be converted without utilisation and efficiency assumptions.",
            "Cooling share depends strongly on facility type, climate, density and system design.",
            "Global electricity share can look small while local grid impacts are large because capacity clusters geographically.",
            "Forecast ranges are scenarios shaped by AI adoption, efficiency, supply chains and energy infrastructure—not observations.",
        ],
        "sources": SOURCES,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("WROTE", OUT)
    for row in data["material_histories"]["series"]:
        print(row["material"], row["coverage"], len(row["series"]))


if __name__ == "__main__":
    build()
