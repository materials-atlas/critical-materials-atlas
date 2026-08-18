"""Build evidence JSON for the unpublished nuclear fuel-chain pilot."""
from __future__ import annotations

import json
import os

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "nuclear_chain.json")

SOURCES = {
    "iaea_pris": {"title": "IAEA PRIS, World trend in electrical production", "year": 2026, "url": "https://pris.iaea.org/PRIS/WorldStatistics/WorldTrendinElectricalProduction.aspx"},
    "iaea_2024": {"title": "IAEA, Nuclear Power Reactors in the World 2025 edition", "year": 2025, "url": "https://www-pub.iaea.org/MTCD/publications/PDF/p15942-25-02880E_RDS-1-45_web.pdf"},
    "nea_redbook": {"title": "OECD NEA and IAEA, Uranium 2024: Resources, Production and Demand", "year": 2025, "url": "https://cms.oecd-nea.org/jcms/pl_103179/uranium-2024-resources-production-and-demand"},
    "nea_haleu": {"title": "OECD NEA, High-Assay Low-Enriched Uranium: Drivers, Implications and Security of Supply", "year": 2024, "url": "https://oecd-nea.org/jcms/pl_96126/high-assay-low-enriched-uranium-drivers-implications-and-security-of-supply"},
    "doe_enrichment": {"title": "US DOE, Uranium Enrichment Explained", "year": 2024, "url": "https://www.energy.gov/ne/articles/uranium-enrichment-explained"},
    "iaea_cycle": {"title": "IAEA Nuclear Fuel Cycle Simulation System, fuel-cycle description", "year": 2026, "url": "https://infcis.iaea.org/nfcss/modeling"},
    "iaea_smr": {"title": "IAEA, Advances in Small Modular Reactor Technology Developments 2024", "year": 2024, "url": "https://aris.iaea.org/Publications/SMR_catalogue_2024.pdf"},
    "usgs": {"title": "USGS, Historical Statistics for Mineral and Material Commodities", "year": 2024, "url": "https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities"},
    "usgs_zh": {"title": "USGS, Zirconium and Hafnium Statistics and Information", "year": 2026, "url": "https://www.usgs.gov/centers/national-minerals-information-center/zirconium-and-hafnium-statistics-and-information"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

PRIS = [
    (2006, 371, 442, 2660.85), (2007, 371, 438, 2608.18),
    (2008, 369, 436, 2597.81), (2009, 369, 436, 2558.06),
    (2010, 372, 438, 2629.82), (2011, 375, 442, 2517.98),
    (2012, 356, 419, 2346.19), (2013, 355, 416, 2358.86),
    (2014, 354, 414, 2410.37), (2015, 364, 423, 2441.34),
    (2016, 370, 426, 2477.30), (2017, 372, 427, 2502.82),
    (2018, 379, 432, 2562.76), (2019, 379, 429, 2657.16),
    (2020, 375, 422, 2553.24), (2021, 375, 420, 2653.34),
    (2022, 374, 416, 2486.83), (2023, 377, 418, 2552.07),
    (2024, 379, 421, 2617.53), (2025, 379, 420, 2635.25),
]

HISTORY = {
    "Zircon mineral concentrates": ("zirconium.xlsx", "Zirconium", 10, "tonnes gross weight", "All zircon mineral-concentrate uses; not nuclear-grade zirconium metal or cladding."),
    "Boron minerals": ("boron.xlsx", "Boron", 7, "tonnes gross weight", "All boron mineral uses; boron control and coolant applications depend on reactor design."),
    "Natural graphite": ("graphite.xlsx", "Graphite", 8, "tonnes gross weight", "All natural graphite uses; graphite is a moderator only in some reactor families."),
}


def histories():
    result = []
    for material, (filename, sheet_name, column, unit, boundary) in HISTORY.items():
        path = os.path.join(ROOT, "raw", "usgs_hist", filename)
        sheet = openpyxl.load_workbook(path, read_only=True, data_only=True)[sheet_name]
        values = {}
        for row in sheet.iter_rows(min_row=6, values_only=True):
            if isinstance(row[0], int) and isinstance(row[column], (int, float)) and row[column] > 0:
                values[row[0]] = row[column]
        rows = [{"year": year, "world_tonnes": round(value, 3)} for year, value in sorted(values.items())]
        result.append({"material": material, "unit": unit, "coverage": f"{rows[0]['year']}-{rows[-1]['year']}", "series": rows, "boundary": boundary})
    return result


def build():
    data = {
        "title": "Nuclear fuel-chain evidence",
        "status": "unpublished pilot",
        "updated": "2026-08-18",
        "principle": "A uranium mine, conversion plant, enrichment plant, fuel factory, reactor and spent-fuel facility are different capabilities measured in different units.",
        "chain": [
            {"stage": "Mine & mill", "detail": "Ore becomes uranium concentrate (U3O8 or yellowcake), reported in tonnes of uranium."},
            {"stage": "Convert", "detail": "Concentrate is purified and commonly converted to UF6 for enrichment."},
            {"stage": "Enrich", "detail": "U-235 concentration rises; capacity is a service measured in separative work, not mined tonnes."},
            {"stage": "Fabricate", "detail": "Fuel chemistry, pellets, rods and assemblies must match a licensed reactor design."},
            {"stage": "Operate", "detail": "Reactors turn fuel and plant availability into electricity over decades."},
            {"stage": "Back end", "detail": "Spent fuel is stored, possibly reprocessed, and ultimately managed or disposed."},
        ],
        "pris": {
            "source": "iaea_pris",
            "coverage": "2006-2025",
            "series": [{"year": y, "capacity_gwe": c, "reactors_with_generation_data": r, "electricity_twh": e} for y, c, r, e in PRIS],
            "boundary": "PRIS annual capacity and reactor counts cover units that supplied production data during the year. They are not end-of-year operational-fleet counts.",
        },
        "status_2024": {
            "source": "iaea_2024", "date": "2024-12-31",
            "operational_reactors": 417, "operational_capacity_gwe": 377.0,
            "under_construction_reactors": 62, "under_construction_capacity_gwe": 64.5,
            "older_than_30_years": {"reactors": 284, "capacity_gwe": 254.7, "capacity_share": 0.67},
            "boundary": "A fixed end-2024 status snapshot. Do not combine its reactor count with the PRIS 2025 count of reactors reporting generation.",
        },
        "uranium_production": {
            "source": "nea_redbook", "unit": "tonnes uranium (tU)",
            "world": [{"year": 2020, "value": 47588}, {"year": 2021, "value": 47361}, {"year": 2022, "value": 49490}, {"year": 2023, "value": 54597}],
            "producers_2023": [
                {"country": "Kazakhstan", "value": 21112}, {"country": "Canada", "value": 10986},
                {"country": "Namibia", "value": 6985}, {"country": "Uzbekistan", "value": 4000},
                {"country": "Russia", "value": 2600}, {"country": "China", "value": 1600},
                {"country": "Niger", "value": 1130}, {"country": "India", "value": 485},
                {"country": "Ukraine", "value": 300}, {"country": "South Africa", "value": 200},
                {"country": "Brazil", "value": 171},
            ],
            "finding": "Among countries with installed nuclear generation, Canada alone produced enough uranium in 2023 to meet its own annual reactor requirements.",
            "boundary": "Mining output is not conversion, enrichment, fabricated-fuel availability or reactor fuel inventory.",
        },
        "front_end_concentration": {
            "source": "nea_haleu", "year": 2022,
            "conversion_capacity_shares": [
                {"supplier": "Rosatom", "share": 0.286}, {"supplier": "Cameco", "share": 0.252},
                {"supplier": "CNNC", "share": 0.250}, {"supplier": "Orano", "share": 0.212},
            ],
            "enrichment_context": {"source": "doe_enrichment", "year": 2024, "russia_global_services_share_about": 0.44},
            "boundary": "Conversion shares are a 2022 capacity snapshot. The Russian figure is a 2024 US DOE estimate for global enrichment services; the two percentages have different denominators.",
        },
        "reactor_families": [
            {"name": "Light-water reactors", "fuel": "Usually low-enriched uranium dioxide", "materials": "Water moderator/coolant; zirconium-alloy cladding is widespread", "exposure": "Conversion, enrichment and design-qualified fuel fabrication"},
            {"name": "Heavy-water reactors", "fuel": "Can use natural uranium", "materials": "Heavy water and pressure tubes; fuel architecture differs from LWRs", "exposure": "Can reduce enrichment dependence but not mining, conversion or fabrication needs"},
            {"name": "Graphite-moderated reactors", "fuel": "Varies by design", "materials": "Nuclear-grade graphite is a functional reactor material", "exposure": "Graphite quality and component supply matter; bulk natural graphite is only context"},
            {"name": "Advanced reactors and SMRs", "fuel": "Design-dependent: conventional LEU, HALEU or other fuels", "materials": "May use TRISO, graphite, specialised alloys or familiar LWR materials", "exposure": "Do not assume every SMR needs HALEU; licensing and qualification can be the bottleneck"},
        ],
        "fuel_definitions": {
            "source": "nea_haleu", "haleu_u235": "above 5% and below 20%",
            "rule": "HALEU is a fuel specification used by some advanced designs, not a synonym for SMR fuel.",
        },
        "material_histories": {"source": "usgs", "series": histories(), "excluded": "Hafnium has a reactor-control use, but the local USGS workbook lacks a world-production series; no global line is shown.", "boundary": "Economy-wide mineral production is not nuclear-grade material output, reactor demand or qualified manufacturing capacity."},
        "trade_context": {
            "source": "baci", "coverage": "2002-2024", "file": "out/nuclear_trade.json",
            "boundary": "Customs value is not physical fuel-cycle capacity. Sensitive or confidential nuclear flows may be incomplete, and enrichment services are not fully represented by traded material codes.",
        },
        "boundaries": [
            "Tonnes of uranium cannot be added to separative-work capacity, fabricated fuel or reactor GW.",
            "A reactor under construction is not an operating unit; an announced design is not a project.",
            "Natural uranium and enriched uranium trade codes do not reveal enrichment services or inventory drawdown.",
            "Zirconium, graphite, boron and hafnium roles vary by reactor architecture and nuclear-grade specification.",
            "The back end branches: storage, reprocessing and disposal are distinct choices and facilities.",
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
