"""Build evidence JSON for the unpublished electrolyser/hydrogen chain pilot."""
from __future__ import annotations

import json
import os

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "electrolyser_chain.json")

SOURCES = {
    "iea_2026_production": {"title": "IEA, Global Hydrogen Review 2026 — Production", "year": 2026, "url": "https://www.iea.org/reports/global-hydrogen-review-2026/production", "licence": "CC BY 4.0"},
    "iea_2026_demand": {"title": "IEA, Global Hydrogen Review 2026 — Demand", "year": 2026, "url": "https://www.iea.org/reports/global-hydrogen-review-2026/demand", "licence": "CC BY 4.0"},
    "iea_2025_summary": {"title": "IEA, Global Hydrogen Review 2025 — Executive summary", "year": 2025, "url": "https://www.iea.org/reports/global-hydrogen-review-2025/executive-summary", "licence": "CC BY 4.0"},
    "iea_2025_questions": {"title": "IEA, Global Hydrogen Review 2025 — Five key questions about hydrogen", "year": 2025, "url": "https://www.iea.org/reports/global-hydrogen-review-2025/five-key-questions-about-hydrogen", "licence": "CC BY 4.0"},
    "iea_2024_dashboard": {"title": "IEA, Global Hydrogen Review 2024 — Progress dashboard", "year": 2024, "url": "https://www.iea.org/reports/global-hydrogen-review-2024/progress-summary-dashboard", "licence": "CC BY 4.0"},
    "iea_2024_production": {"title": "IEA, Global Hydrogen Review 2024 — Hydrogen production", "year": 2024, "url": "https://www.iea.org/reports/global-hydrogen-review-2024/hydrogen-production", "licence": "CC BY 4.0"},
    "iea_minerals": {"title": "IEA, The Role of Critical Minerals in Clean Energy Transitions", "year": 2021, "url": "https://www.iea.org/reports/the-role-of-critical-minerals-in-clean-energy-transitions/mineral-requirements-for-clean-energy-transitions", "licence": "CC BY 4.0"},
    "irena_2020": {"title": "IRENA, Green Hydrogen Cost Reduction", "year": 2020, "url": "https://www.irena.org/publications/2020/Dec/Green-hydrogen-cost-reduction"},
    "usgs": {"title": "USGS, Historical Statistics for Mineral and Material Commodities", "year": 2024, "url": "https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

HISTORY = {
    "Nickel": ("nickel.xlsx", "Nickel", 9, "tonnes nickel content", "All nickel uses; world production."),
    "Platinum-group metals": ("platinum-group-metals.xlsx", "Platinum-group metals", 12, "tonnes PGM content", "Combined PGM production; not an iridium or platinum series."),
    "Zircon mineral concentrates": ("zirconium.xlsx", "Zirconium", 10, "tonnes gross weight", "Mineral-concentrate output; not electrolyser-grade zirconia."),
    "Rare earths": ("rare-earths.xlsx", "Rare earths", 7, "tonnes REO equivalent", "All rare earths; not yttrium or lanthanum specifically."),
}


def histories():
    result = []
    for material, (filename, sheet_name, column, unit, boundary) in HISTORY.items():
        sheet = openpyxl.load_workbook(os.path.join(ROOT, "raw", "usgs_hist", filename), read_only=True, data_only=True)[sheet_name]
        values = {}
        for row in sheet.iter_rows(min_row=6, values_only=True):
            if isinstance(row[0], int) and isinstance(row[column], (int, float)):
                values[row[0]] = row[column]
        rows = [{"year": year, "world_tonnes": round(value, 3)} for year, value in sorted(values.items())]
        result.append({"material": material, "unit": unit, "coverage": f"{rows[0]['year']}-{rows[-1]['year']}", "series": rows, "boundary": boundary})
    return result


def build():
    data = {
        "title": "Electrolyser and hydrogen chain evidence",
        "status": "unpublished pilot",
        "updated": "2026-08-18",
        "principle": "Total hydrogen, low-emissions hydrogen, installed electrolysis, projects, factory capacity and equipment trade are separate measures.",
        "chain": [
            {"stage": "Materials", "detail": "Nickel, platinum, iridium, titanium, zirconium, rare earths, steels and polymers"},
            {"stage": "Stack", "detail": "Electrodes, catalysts, membranes or electrolyte, separators and bipolar plates"},
            {"stage": "System", "detail": "Stacks plus rectifier, water treatment, cooling, gas purification and controls"},
            {"stage": "Hydrogen plant", "detail": "Electricity and water supply integrated with compression and storage"},
            {"stage": "Conversion & transport", "detail": "Pipeline, vessel or conversion to ammonia, methanol and synthetic fuels"},
            {"stage": "Use & recover", "detail": "Refining, fertiliser, steel, fuels and recovery of scarce catalyst materials"},
        ],
        "hydrogen_system_2025": {
            "sources": ["iea_2026_production", "iea_2026_demand"],
            "total_demand_mt_more_than": 100,
            "low_emissions_production_mt_almost": 1,
            "low_emissions_share": 0.01,
            "traditional_uses": ["oil refining", "ammonia", "methanol", "fossil-based direct reduced iron"],
            "boundary": "Low-emissions hydrogen includes electrolysis with low-emissions electricity and fossil routes with sufficiently effective carbon capture; it is not synonymous with electrolysis.",
        },
        "installed_electrolysis": {
            "sources": ["iea_2024_dashboard", "iea_2025_summary", "iea_2026_production"],
            "unit": "GW electrical input",
            "series": [
                {"year": 2021, "value": 0.6, "status": "observed"},
                {"year": 2022, "value": 0.7, "status": "observed"},
                {"year": 2023, "value": 1.4, "status": "observed"},
                {"year": 2024, "value": 2.0, "status": "observed"},
                {"year": 2025, "value": 4.0, "status": "more than"},
            ],
            "boundary": "Operating installed water-electrolyser capacity. The 2024 value is the later observed estimate, not the earlier 5.2 GW project-based forecast.",
        },
        "project_clocks": {
            "source": "iea_2026_production",
            "as_of": 2026,
            "items": [
                {"clock": "Operating at end-2025", "value_gw": 4.0, "precision": "more than"},
                {"clock": "Under construction for 2026", "value_gw": 2.5, "precision": "more than"},
                {"clock": "Announced capacity at risk of missing 2030", "value_gw": 100, "precision": "more than"},
            ],
            "production_2030_mtpa": {"committed": 4.3, "strong_potential_more_than": 6, "full_pipeline": 27},
            "boundary": "The GW values describe electrolyser electrical-input capacity; the Mtpa values describe low-emissions hydrogen from all eligible production routes. They cannot be added or converted without project-level assumptions.",
        },
        "technology_source": "irena_2020",
        "technologies": [
            {"name": "Alkaline", "temperature_c": "70–90", "materials": "Nickel-coated steel electrodes, nickel meshes, potassium hydroxide and zirconia-containing separator", "strength": "Mature and generally lower equipment cost", "constraint": "Large footprint and traditionally less dynamic operation"},
            {"name": "PEM", "temperature_c": "50–80", "materials": "Iridium-oxide anode catalyst, platinum cathode, titanium transport layers and fluorinated membrane", "strength": "Compact, flexible and suited to variable operation", "constraint": "Exposure to very scarce iridium and other expensive materials"},
            {"name": "Solid oxide", "temperature_c": "700–850", "materials": "Nickel, yttria-stabilised zirconia and lanthanum-containing ceramics", "strength": "High efficiency when high-temperature heat is available; potentially reversible", "constraint": "Earlier commercial stage and demanding thermal cycling"},
            {"name": "AEM", "temperature_c": "40–60", "materials": "Nickel or nickel-iron-cobalt catalysts with an anion-exchange polymer membrane", "strength": "Aims to combine flexible operation with fewer precious metals", "constraint": "Emerging durability and scale-up evidence"},
        ],
        "material_specific": {
            "source": "iea_minerals",
            "pem_platinum_kg_per_mw": 0.3,
            "rule": "Platinum is only one PEM input; do not infer iridium demand from this value.",
            "boundary": "Indicative technology-era intensity from the source, not a timeless bill of materials. Catalyst loading is an active innovation target.",
        },
        "material_histories": {"source": "usgs", "series": histories(), "boundary": "Economy-wide production context. None of these series measures electrolyser demand or usable catalyst supply."},
        "manufacturing": {
            "sources": ["iea_2024_production", "iea_2025_summary", "iea_2025_questions"],
            "world": {"year": 2023, "capacity_gw_per_year": 25, "output_gw": 2.5, "utilisation_implied": 0.10},
            "china": {"year": 2024, "capacity_gw_per_year": 20, "domestic_demand_gw": 2, "global_capacity_share": 0.60},
            "installed_stack_cost_share": [0.15, 0.20],
            "boundary": "Nameplate factory capacity, factory output, domestic demand and installed-system cost are different. The stack is only 15–20% of total installed investment in the IEA comparison.",
        },
        "water_context": {
            "source": "iea_2024_production", "planned_projects_in_water_stressed_regions_share": 0.40,
            "boundary": "Share of planned low-emissions hydrogen projects, not operating electrolysers. Water treatment, cooling and local availability matter beyond reaction stoichiometry.",
        },
        "trade_context": {
            "source": "baci", "coverage": "2002-2024", "file": "out/electrolyser_trade.json",
            "boundary": "No clean global HS code identifies water electrolysers. All four baskets are upstream or mixed-use context and must not be labelled electrolyser trade.",
        },
        "boundaries": [
            "Most hydrogen today is fossil-based and used in established industry.",
            "Electrolysis capacity in GW is not hydrogen production in tonnes; utilisation and efficiency are required.",
            "An announcement is not a final investment decision, construction site or operating plant.",
            "Alkaline, PEM, solid-oxide and AEM systems have different material recipes.",
            "Bulk mineral production does not reveal catalyst-grade or component availability.",
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
