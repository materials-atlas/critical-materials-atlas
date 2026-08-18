"""Build evidence JSON for the unpublished electric-vehicle chain pilot."""
from __future__ import annotations

import csv
import json
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "ev_chain.json")

SOURCES = {
    "iea_data": {"title": "IEA, Global EV Data Explorer 2026", "year": 2026, "url": "https://www.iea.org/data-and-statistics/data-tools/global-ev-data-explorer", "licence": "CC BY 4.0"},
    "iea_ev_2026": {"title": "IEA, Global EV Outlook 2026 — Trends in electric cars", "year": 2026, "url": "https://www.iea.org/reports/global-ev-outlook-2026/trends-in-electric-cars", "licence": "CC BY 4.0"},
    "iea_batteries_2026": {"title": "IEA, Global EV Outlook 2026 — Electric vehicle batteries", "year": 2026, "url": "https://www.iea.org/reports/global-ev-outlook-2026/electric-vehicle-batteries", "licence": "CC BY 4.0"},
    "iea_trade_2026": {"title": "IEA, Global EV Outlook 2026 — Manufacturing and trade", "year": 2026, "url": "https://www.iea.org/reports/global-ev-outlook-2026/manufacturing-and-trade", "licence": "CC BY 4.0"},
    "iea_minerals_2025": {"title": "IEA, Global Critical Minerals Outlook 2025 — Beyond NMC batteries", "year": 2025, "url": "https://www.iea.org/reports/global-critical-minerals-outlook-2025/beyond-nmc-batteries-supply-chain-issues-for-emerging-battery-technologies", "licence": "CC BY 4.0"},
    "iea_ultrafast_2026": {"title": "IEA, Ultra-fast charging batteries", "year": 2026, "url": "https://www.iea.org/reports/ultra-fast-charging-batteries", "licence": "CC BY 4.0"},
    "doe_motors": {"title": "US DOE, Electric Motors Research and Development", "year": 2026, "url": "https://www.energy.gov/cmei/vehicles/electric-motors-research-and-development"},
    "nrel_sic_2017": {"title": "NREL, John Deere hybrid vehicles benefit from wide-bandgap thermal management", "year": 2017, "url": "https://www.nrel.gov/news/detail/program/2017/john-deere-hybrid-electric-vehicles"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}


def iea_series(filename):
    rows = []
    with open(os.path.join(ROOT, "raw", filename), encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["region"] != "World" or row["category"] != "Historical":
                continue
            rows.append({"year": int(row["year"]), "powertrain": row["powertrain"], "vehicles": round(float(row["value"]))})
    years = sorted({row["year"] for row in rows})
    return {
        "coverage": f"{years[0]}-{years[-1]}",
        "unit": "vehicles",
        "series": rows,
        "boundary": "Passenger cars only. EV is the published aggregate; BEV, PHEV and FCEV are component powertrains and must not be added to EV again.",
    }


def build():
    data = {
        "title": "Electric-vehicle chain evidence",
        "status": "unpublished pilot",
        "updated": "2026-08-18",
        "principle": "Vehicle registrations, production, manufacturer headquarters, battery chemistry, component origin and customs trade are separate measures.",
        "chain": [
            {"stage": "Materials", "detail": "Battery minerals, copper, aluminium, steels, rare earths and semiconductor feedstocks"},
            {"stage": "Components", "detail": "Cells, magnets or alternative rotors, inverter, motor, wiring and thermal systems"},
            {"stage": "Powertrain", "detail": "Battery pack, power electronics, traction motor and reduction gear"},
            {"stage": "Vehicle", "detail": "Body, chassis, software and powertrain assembled and tested"},
            {"stage": "Use & charge", "detail": "Driving, charging, maintenance and interaction with the grid"},
            {"stage": "Recover", "detail": "Reuse, dismantling and recovery of battery and vehicle materials"},
        ],
        "deployment": {
            "source": "iea_data",
            "sales": iea_series("iea_ev_sales_2026.csv"),
            "stock": iea_series("iea_ev_stock_2026.csv"),
        },
        "battery_transition": {
            "sources": ["iea_minerals_2025", "iea_batteries_2026"],
            "metric": "LFP share of global EV battery deployment by capacity",
            "series": [
                {"year": 2020, "share": 0.10, "precision": "less than"},
                {"year": 2022, "share": 0.30, "precision": "just under"},
                {"year": 2024, "share": 0.50, "precision": "nearly"},
                {"year": 2025, "share": 0.55, "precision": "over"},
            ],
            "deployment_2025_twh": 1.2,
            "deployment_growth_since_2020": 7,
            "boundary": "Chemistry share is capacity in newly registered EV batteries, not vehicle count, cell production or mineral demand. Two/three-wheelers are excluded.",
        },
        "chemistry_choices": [
            {"name": "LFP", "uses": ["lithium", "iron", "phosphate", "graphite"], "avoids": ["nickel", "cobalt"], "tradeoff": "Lower cost and no nickel/cobalt; generally lower energy density than NMC."},
            {"name": "NMC / NCA", "uses": ["lithium", "nickel", "cobalt", "manganese or aluminium", "graphite"], "avoids": [], "tradeoff": "Higher energy density; mineral mix changes with cathode formulation."},
            {"name": "Sodium-ion", "uses": ["sodium", "iron or manganese", "carbon"], "avoids": ["lithium", "nickel", "cobalt"], "tradeoff": "Entering scale-up, but lower energy density limits many vehicle applications."},
        ],
        "motor_choices": {
            "source": "doe_motors",
            "types": [
                {"name": "Permanent-magnet synchronous", "exposure": "NdFeB magnets, sometimes heavy rare earths; copper windings", "advantage": "High power density and broad efficiency range"},
                {"name": "Induction", "exposure": "Copper stator plus aluminium or copper rotor; no permanent magnet", "advantage": "Reliable and magnet-free"},
                {"name": "Switched / synchronous reluctance", "exposure": "Electrical steel and copper; can be magnet-free or magnet-assisted", "advantage": "Reduces or avoids rare-earth exposure"},
                {"name": "Wound-field synchronous", "exposure": "Copper rotor excitation instead of permanent magnets", "advantage": "Controllable field and no permanent magnet"},
            ],
            "boundary": "Architecture menu, not market shares. Motor choice can differ between axles in the same vehicle.",
        },
        "power_electronics": {
            "sources": ["nrel_sic_2017", "iea_ultrafast_2026"],
            "anchors": [
                {"year": 2017, "event": "NREL reported an in-vehicle 200 kW, 1,050 V silicon-carbide inverter demonstration for heavy equipment."},
                {"year": 2025, "event": "The first 1,000 V electric-car models reached the market."},
                {"year": 2025, "event": "Cars able to charge above 250 kW remained below 5% of the global electric-car stock."},
            ],
            "boundary": "Technology milestones, not a market-share series. Higher voltage also requires cells, cooling, cables and chargers able to handle higher power.",
        },
        "vehicle_size": {
            "source": "iea_ev_2026",
            "large_and_suv_model_share": [{"year": 2020, "share": 0.55}, {"year": 2025, "share": 0.70}],
            "large_and_suv_sales_share_2025": 0.70,
            "average_bev_range_2025_km": 380,
            "boundary": "Model availability and sales share are different. Larger vehicles tend to require more material and battery capacity, but there is no universal per-vehicle increment.",
        },
        "manufacturing_2025": {
            "source": "iea_trade_2026",
            "world_electric_cars_million": 22,
            "share_traded_between_major_regions": 0.25,
            "china": {"production_million": 16, "production_share": 0.70, "exports_million_more_than": 2.5, "global_export_share": 0.40},
            "supply_chain_china_shares": {"electric_cars": 0.70, "battery_cells": 0.80, "cathode_active_material": 0.85, "anode_active_material": 0.90},
            "boundary": "Rounded physical production and trade estimates. Factory location is not manufacturer headquarters, sales location or mineral origin.",
        },
        "trade_context": {
            "source": "baci", "file": "out/ev_trade.json",
            "coverage": "2002-2024 for broad comparators; 2017-2024 for clean BEV/PHEV and lithium-ion baskets",
            "boundary": "HS introduced clean electric and plug-in-hybrid car codes in 2017. Earlier broad car trade cannot be converted into an EV series.",
        },
        "boundaries": [
            "BEVs, PHEVs and fuel-cell cars are different powertrains; this pilot focuses on plug-in electric cars while preserving the split.",
            "Battery capacity, vehicle count and mineral tonnes answer different questions.",
            "Battery chemistry, motor design, vehicle size and voltage architecture all change material exposure.",
            "Vehicle assembly location does not reveal battery, motor, chip or mineral origin.",
            "Customs classifications identify clean EVs only from 2017 onward.",
        ],
        "sources": SOURCES,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("WROTE", OUT)
    for key in ("sales", "stock"):
        ev = [row for row in data["deployment"][key]["series"] if row["powertrain"] == "EV"]
        print(key, ev[0], "->", ev[-1])


if __name__ == "__main__":
    build()
