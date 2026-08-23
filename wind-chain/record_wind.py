"""Build the evidence JSON for the unpublished wind-turbine chain pilot."""
from __future__ import annotations

import json
import os
from collections import defaultdict


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw", "irena_wind_capacity_2000_2025.json")
OUT = os.path.join(HERE, "out", "wind_chain.json")

SOURCES = {
    "irena_capacity": {"title": "IRENA, Renewable Capacity Statistics 2026 (PxWeb API)", "year": 2026, "url": "https://pxweb.irena.org/pxweb/en/IRENASTAT/IRENASTAT__Power%20Capacity%20and%20Generation/Region_ELECCAP_2026_H1_v-PX%201.px/"},
    "irena_cost": {"title": "IRENA, Renewable Power Generation Costs in 2024", "year": 2025, "url": "https://www.irena.org/Digital-Report/Renewable-Power-Generation-Costs-in-2024"},
    "gwec_2026": {"title": "GWEC, Wind turbine installations and suppliers in 2025", "year": 2026, "url": "https://www.gwec.net/news/gwec-records-sharp-rise-in-wind-turbine-installations-as-five-oems-exceed-100-gw"},
    "iea_manufacturing": {"title": "IEA, The State of Clean Technology Manufacturing", "year": 2023, "url": "https://www.iea.org/reports/the-state-of-clean-technology-manufacturing/analysis", "licence": "CC BY 4.0"},
    "doe_drivetrain": {"title": "US DOE, Advanced Wind Turbine Drivetrain Trends and Opportunities", "year": 2019, "url": "https://www.energy.gov/cmei/wind/articles/advanced-wind-turbine-drivetrain-trends-and-opportunities"},
    "doe_offshore_2013": {"title": "US DOE, Offshore Wind Manufacturing and Supply Chain Development", "year": 2013, "url": "https://www1.eere.energy.gov/wind/pdfs/us_offshore_wind_supply_chain_and_manufacturing_development.pdf"},
    "doe_market_2012": {"title": "US DOE, 2012 Wind Technologies Market Report", "year": 2013, "url": "https://www1.eere.energy.gov/wind/pdfs/2012_wind_technologies_market_report.pdf"},
    "jrc_materials": {"title": "European Commission JRC, Material requirements for wind turbines", "year": 2024, "url": "https://publications.jrc.ec.europa.eu/repository/handle/JRC139701"},
    "doe_recycling": {"title": "US DOE, Wind Turbine Recycling", "year": 2023, "url": "https://www.energy.gov/cmei/systems/wind-turbine-recycling"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}


def deployment():
    with open(RAW, encoding="utf-8") as handle:
        raw = json.load(handle)
    country = defaultdict(lambda: defaultdict(float))
    tech = defaultdict(lambda: defaultdict(float))
    names = {}
    for row in raw["country_rows"]:
        names[row["iso3"]] = row["country"]
        tech[(row["year"], row["technology"])][row["iso3"]] += row["capacity_mw"]
        if row["technology"] == "Wind energy":
            country[row["year"]][row["iso3"]] += row["capacity_mw"]
    world = []
    previous = None
    for row in raw["world_wind"]:
        total = row["capacity_mw"]
        countries = country[row["year"]]
        top = [{"iso": iso, "country": names[iso], "capacity_mw": round(value, 2), "world_share": round(value / total, 4)}
               for iso, value in sorted(countries.items(), key=lambda item: -item[1])[:8]]
        world.append({"year": row["year"], "capacity_mw": total, "net_addition_mw": round(total - previous, 2) if previous is not None else None, "top_countries": top})
        previous = total
    split = []
    for technology in ("Onshore wind energy", "Offshore wind energy"):
        values = tech[(2025, technology)]
        total = sum(values.values())
        split.append({
            "technology": technology.replace(" wind energy", ""), "capacity_mw": round(total, 2),
            "world_share": round(total / world[-1]["capacity_mw"], 4),
            "top_countries": [{"iso": iso, "country": names[iso], "capacity_mw": round(value, 2), "share_of_segment": round(value / total, 4)}
                              for iso, value in sorted(values.items(), key=lambda item: -item[1])[:8]],
        })
    return {"source": "irena_capacity", "unit": raw["unit"], "coverage": "2000-2025", "world_series": world, "technology_split_2025": split}


def build():
    data = {
        "title": "Wind-turbine chain evidence",
        "status": "unpublished pilot",
        "updated": "2026-08-17",
        "principle": "Installed capacity, annual commissioning, mechanical installation, manufacturing capacity, supplier origin and customs trade are separate measures.",
        "chain": [
            {"stage": "Materials", "detail": "Steel, concrete, copper, composites and—in some designs—magnet rare earths"},
            {"stage": "Components", "detail": "Blades, tower, bearings, gearbox, generator and power electronics"},
            {"stage": "Nacelle & rotor", "detail": "Drivetrain and controls integrated with hub and blades"},
            {"stage": "Turbine", "detail": "OEM supplies the complete generating system"},
            {"stage": "Wind farm", "detail": "Transport, foundations, cabling, installation and grid connection"},
            {"stage": "Operate & recover", "detail": "Maintenance, repowering, dismantling and material recovery"},
        ],
        "deployment": deployment(),
        "market_clocks_2025": {
            "sources": ["irena_capacity", "gwec_2026"], "year": 2025,
            "metrics": [
                {"metric": "Net increase in operating capacity", "value_gw": 158.7, "source": "irena_capacity"},
                {"metric": "Capacity commissioned", "value_gw": 165, "source": "gwec_2026"},
                {"metric": "Turbines mechanically installed", "value_gw": 178, "source": "gwec_2026"},
            ],
            "boundary": "Different status dates and methods; values diagnose clocks and must not be forced to match.",
        },
        "supplier_market_2025": {
            "source": "gwec_2026", "year": 2025, "installed_units": 28395, "mechanically_installed_gw": 178,
            "china_manufacturer_unit_share": 0.67, "china_oem_home_market_share": 0.934,
            "top_five_oems": [
                {"name": "Goldwind", "headquarters": "China", "installed_gw": 29.7},
                {"name": "Envision", "headquarters": "China", "installed_gw": 21.8},
                {"name": "Windey", "headquarters": "China", "installed_gw": 19.8},
                {"name": "Mingyang", "headquarters": "China", "installed_gw": 18.6},
                {"name": "SANY", "headquarters": "China", "installed_gw": 15.1},
            ],
            "boundary": "Supplier headquarters and installation country are different. Most Chinese-OEM installations remained inside China.",
        },
        "manufacturing_capacity_2025_projection": {
            "source": "iea_manufacturing", "vintage": 2023, "target_year": 2025,
            "segments": [
                {"segment": "Onshore components", "world_range_gw": [100, 110], "china_share": 0.60, "europe_share": 0.15, "north_america_share": 0.10},
                {"segment": "Offshore components", "world_gw": 30, "china_share_range": [0.70, 0.80], "note": "Most remaining capacity was in Europe."},
            ],
            "boundary": "A 2023 estimate based on announced projects for 2025—not observed 2025 output.",
        },
        "drivetrain_history": {
            "sources": ["doe_offshore_2013", "doe_market_2012"], "metric": "global share of turbine supply using direct drive",
            "series": [{"year": 2010, "share": 0.176}, {"year": 2011, "share": 0.212}, {"year": 2012, "share": 0.195}],
            "boundary": "Direct drive is not synonymous with permanent magnets; electrically excited direct drive exists, and geared/hybrid machines can use magnets.",
        },
        "design_material_intensity": {
            "source": "jrc_materials", "unit": "kg per MW", "year": 2024,
            "bulk_ranges": [
                {"material": "Concrete", "low": 300000, "high": 500000},
                {"material": "Steel", "low": 90000, "high": 130000},
                {"material": "Glass/carbon composites", "low": 6000, "high": 9000},
            ],
            "generator_types": [
                {"type": "Geared DFIG", "code": "GB-DFIG", "copper_low": 800, "copper_high": 1900, "neodymium": 12, "dysprosium": 2, "note": "Nd and Dy are central estimates with ±6 and ±1 kg/MW ranges."},
                {"type": "Direct drive, electrically excited", "code": "DD-EESG", "copper_low": 5200, "copper_high": 6200, "neodymium": 0, "dysprosium": 0, "note": "Avoids permanent-magnet rare earths but uses more copper."},
                {"type": "Direct drive, permanent magnet", "code": "DD-PMSG", "copper_low": 2200, "copper_high": 4600, "neodymium": 180, "praseodymium": 35, "dysprosium": 17, "terbium": 7, "note": "Nd and Dy are central estimates with ±30 and ±4 kg/MW ranges."},
            ],
            "boundary": "Technology estimates, not a universal bill of materials; foundations, site conditions and turbine size vary.",
        },
        "cost_change": {
            "source": "irena_cost", "metric": "global weighted-average onshore-wind LCOE", "unit": "2024 USD/kWh",
            "series": [{"year": 2010, "value": 0.089}, {"year": 2024, "value": 0.034}], "reported_decline": 0.70,
            "boundary": "Two published endpoints; not an annual reconstructed series.",
        },
        "circularity": {
            "source": "doe_recycling", "currently_recyclable_mass_share": [0.85, 0.90],
            "hard_fraction": "Composite blades and some other materials", "boundary": "Technically recyclable mass is not the same as actual collection or recycling rate.",
        },
        "trade_context": {
            "source": "baci", "coverage": "2002-2024", "file": "out/wind_trade.json",
            "boundary": "HS 850231 is the clean finished-set basket; all three component baskets include non-wind products.",
        },
        "boundaries": [
            "Installed capacity is a cumulative asset stock, not annual turbine manufacturing.",
            "Mechanical installation, commissioning and net capacity additions use different clocks.",
            "Supplier headquarters, factory location and installation country are different geographies.",
            "Direct drive does not automatically imply permanent-magnet exposure.",
            "Customs components are broader than the wind industry.",
        ],
        "sources": SOURCES,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2); handle.write("\n")
    print("WROTE", OUT)
    end = data["deployment"]["world_series"][-1]
    print("2025 world", round(end["capacity_mw"] / 1000, 1), "GW; top", end["top_countries"][0])
    return data


if __name__ == "__main__":
    build()
