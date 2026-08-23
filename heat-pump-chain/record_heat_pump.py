"""Build evidence JSON for the unpublished heat-pump and refrigeration-chain pilot."""
from __future__ import annotations

import json
import os

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "heat_pump_chain.json")

SOURCES = {
    "iea_monitor": {"title": "IEA, Heat Pump Monitor 2026 — Key findings", "year": 2026, "url": "https://www.iea.org/reports/heat-pump-monitor-2026/key-findings", "licence": "CC BY 4.0"},
    "iea_review": {"title": "IEA, Global Energy Review 2026 — Heat pumps", "year": 2026, "url": "https://www.iea.org/reports/global-energy-review-2026/technology-heat-pumps", "licence": "CC BY 4.0"},
    "iea_future": {"title": "IEA, The Future of Heat Pumps — Executive summary", "year": 2022, "url": "https://www.iea.org/reports/the-future-of-heat-pumps/executive-summary", "licence": "CC BY 4.0"},
    "ehpa_2023": {"title": "EHPA Market Report 2023 — Executive summary", "year": 2023, "url": "https://www.ehpa.org/wp-content/uploads/2023/06/EHPA_market_report_2023_Executive-Summary.pdf"},
    "ehpa_2025": {"title": "EHPA Market Report 2025 — Executive summary", "year": 2025, "url": "https://www.ehpa.org/wp-content/uploads/2025/07/EHPA-Market-Report-2025-executive-summary.pdf"},
    "ehpa_current": {"title": "EHPA, European heat-pump market data", "year": 2026, "url": "https://ehpa.org/market-data/"},
    "unep_amendments": {"title": "UNEP Ozone Secretariat, amendments to the Montreal Protocol", "year": 2026, "url": "https://ozone.unep.org/treaties/montreal-protocol/amendments"},
    "unep_kigali": {"title": "UNEP OzonAction, HFC phase-down timeline", "year": 2026, "url": "https://www.unep.org/ozonaction/resources/toolkits-manuals-and-guides/path-kigali-hfc-phase-down-timeline"},
    "doe_systems": {"title": "US DOE, Decarbonizing Building Thermal Systems", "year": 2024, "url": "https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/87812.pdf"},
    "usgs": {"title": "USGS, Historical Statistics for Mineral and Material Commodities", "year": 2024, "url": "https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities"},
    "baci": {"title": "CEPII BACI V202601, based on UN Comtrade", "year": 2026, "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37"},
}

EU21 = [
    (2005, 446037, 1.10), (2006, 502965, 1.60), (2007, 572840, 2.17),
    (2008, 804457, 2.98), (2009, 731482, 3.71), (2010, 788605, 4.50),
    (2011, 802660, 5.30), (2012, 743883, 6.03), (2013, 757142, 6.78),
    (2014, 791538, 7.55), (2015, 892809, 8.43), (2016, 999682, 9.41),
    (2017, 1120000, 10.50), (2018, 1270000, 11.74), (2019, 1510000, 13.21),
    (2020, 1600000, 14.77), (2021, 2160000, 16.87), (2022, 3000000, 19.79),
]

HISTORY = {
    "Copper": ("copper.xlsx", "Copper", 12, "tonnes copper content", "All mine production; not heat-pump tubing or refined copper availability."),
    "Primary aluminium": ("aluminum.xlsx", "Aluminum", 15, "tonnes aluminium content", "Primary metal production for all uses; not heat-exchanger manufacturing."),
    "Rare earths": ("rare-earths.xlsx", "Rare earths", 7, "tonnes REO equivalent", "All rare earths; only some motor designs use permanent magnets."),
    "Fluorspar": ("fluorspar.xlsx", "Fluorspar", 8, "tonnes gross weight", "All fluorspar uses; an upstream fluorine context, not refrigerant output."),
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
        "title": "Heat-pump and refrigeration-chain evidence",
        "status": "unpublished pilot",
        "updated": "2026-08-18",
        "principle": "Installed stock, annual sales, thermal capacity, factory capacity and recorded equipment trade are different measures.",
        "chain": [
            {"stage": "Materials", "detail": "Copper, aluminium, steels, polymers, refrigerant feedstocks and sometimes permanent magnets."},
            {"stage": "Components", "detail": "Compressor, heat exchangers, expansion device, valves, fan or pumps, motor and controls."},
            {"stage": "Factory", "detail": "Components are integrated into units matched to local voltage, climate, standards and building practices."},
            {"stage": "Install", "detail": "Sizing, emitters or ducts, electrical connection, pipework, commissioning and refrigerant handling."},
            {"stage": "Operate", "detail": "Efficiency depends on temperatures, controls, building demand, maintenance and electricity prices."},
            {"stage": "Recover", "detail": "Refrigerant is contained or reclaimed and metals/components enter repair, reuse or recycling routes."},
        ],
        "global_2024": {
            "source": "iea_monitor", "heat_needs_share": 0.05, "building_space_heating_share": 0.12,
            "manufacturing_capacity_gw_per_year": 145,
            "manufacturing_shares": [{"region": "China", "share": 0.35}, {"region": "United States", "share": 0.25}, {"region": "European Union", "share": 0.20}, {"region": "Other", "share": 0.20}],
            "domestic_sourcing_share_major_markets_more_than": 0.70,
            "boundary": "Heating-needs shares are service estimates. Manufacturing is nameplate thermal-output capacity, not unit sales or realised production.",
        },
        "global_recent": {
            "sources": ["iea_monitor", "iea_review"],
            "sales_peak": 2022, "sales_2025_change": -0.02,
            "employment_change_since_2015": 0.50,
            "finding": "Global building heat-pump sales peaked in 2022, slowed in 2023-24 and were broadly stable in 2025; technician shortages remained a bottleneck.",
            "boundary": "The IEA global series combines technologies and region-specific definitions; it should not be spliced to the EU-21 unit series.",
        },
        "europe_history": {
            "source": "ehpa_2023", "scope": "EU-21 as defined by EHPA's 2023 report", "coverage": "2005-2022",
            "series": [{"year": y, "sales_units": s, "stock_million": stock} for y, s, stock in EU21],
            "boundary": "EHPA market accounting includes eligible heating heat-pump categories and an assumed roughly 20-year life for stock. It is not the complete global market or a thermal-capacity series.",
        },
        "europe_snapshots": [
            {"year": 2024, "sales_million": 2.31, "stock_million": 25.5, "countries": 19, "source": "ehpa_2025"},
            {"year": 2025, "sales_million": 2.9, "stock_million": 29.3, "countries": 21, "source": "ehpa_current"},
        ],
        "snapshot_rule": "The 2024 and 2025 snapshots use different country sets and must not be treated as a like-for-like growth series.",
        "technologies": [
            {"name": "Air-to-air", "source_sink": "Outdoor air → indoor air", "system": "Often reversible heating and cooling; usually ducted or room units", "exposure": "Compressor, copper/aluminium coils, fans, electronics and refrigerant"},
            {"name": "Air-to-water", "source_sink": "Outdoor air → water circuit", "system": "Feeds radiators, underfloor heating or hot-water storage", "exposure": "Unit plus hydronic balance of plant; retrofit temperatures and emitter sizing matter"},
            {"name": "Ground/water source", "source_sink": "Ground loop or water → building", "system": "More stable source temperature but additional civil works", "exposure": "Pipe or borehole field can dominate project complexity and local content"},
            {"name": "Heat-pump water heater", "source_sink": "Ambient or exhaust heat → stored water", "system": "Dedicated hot-water appliance; CO2 systems are prominent in Japan", "exposure": "Tank, compressor, heat exchanger, refrigerant and controls"},
            {"name": "Industrial/district", "source_sink": "Waste/environmental heat → process or network", "system": "Large, engineered installations with long planning cycles", "exposure": "Temperature lift, integration and project engineering outweigh simple unit counts"},
        ],
        "component_map": [
            {"component": "Compressor and motor", "role": "Raises refrigerant pressure and temperature", "materials": "Steels, copper windings, electronics; magnet use depends on motor design"},
            {"component": "Heat exchangers", "role": "Absorb and reject heat", "materials": "Copper or aluminium tubes/fins, sometimes steel; joining and corrosion performance matter"},
            {"component": "Expansion and reversing devices", "role": "Control pressure and swap heating/cooling direction", "materials": "Precision valves, sensors, controls and mixed alloys"},
            {"component": "Refrigerant circuit", "role": "Carries heat through phase change", "materials": "Fluid choice changes pressures, safety class, servicing and factory design"},
            {"component": "Installation system", "role": "Connects the machine to building and grid", "materials": "Pipework, ducts or emitters, cables, switchgear, pumps, storage and insulation"},
        ],
        "manufacturing": {
            "source": "iea_monitor", "year": 2024,
            "finding": "More than 70% of building heat pumps sold in each major market were sourced domestically, but rotary-compressor production was mostly in China.",
            "boundary": "Final-unit localisation can coexist with upstream component concentration. Country-of-final-assembly is not component origin.",
        },
        "refrigerant_timeline": [
            {"year": 1987, "event": "Montreal Protocol adopted", "meaning": "The ozone-depleting refrigerant transition becomes an international policy process."},
            {"year": 1990, "event": "London Amendment", "meaning": "Controls and financial arrangements broaden."},
            {"year": 1992, "event": "Copenhagen Amendment", "meaning": "Phase-out controls strengthen."},
            {"year": 2016, "event": "Kigali Amendment agreed", "meaning": "The Montreal framework extends to an HFC phase-down because of climate impacts."},
            {"year": 2025, "event": "US A2L manufacturing transition", "meaning": "IEA reports new US-manufactured heat pumps had to use A2L refrigerants; product redesign affected market timing and supply."},
        ],
        "refrigerant_rule": "Refrigerant is not an interchangeable commodity: global-warming potential, flammability, pressure, efficiency, charge, standards and technician competence shape the usable choice.",
        "material_histories": {"source": "usgs", "series": histories(), "boundary": "Economy-wide production context. These series do not measure heat-pump demand, component-grade supply, refrigerant production or recycled metal."},
        "trade_context": {
            "source": "baci", "coverage": "2002-2024", "file": "out/heat_pump_trade.json",
            "boundary": "HS 841861 excludes reversible air conditioners classified in heading 8415. Compressors and heat exchangers are mixed-use. Customs value is not installations, stock or thermal capacity.",
        },
        "boundaries": [
            "A reversible air conditioner used as primary heating can be a heat pump, but regional statistics do not count these consistently.",
            "Unit sales cannot be added across categories without checking scope, capacity and country coverage.",
            "Factory GW/year, shipped units, installed stock and useful heat have different denominators.",
            "Heat-pump performance is a system outcome involving source temperature, delivery temperature, sizing, controls and the building envelope.",
            "Bulk copper, aluminium, rare-earth and fluorspar histories do not identify component or refrigerant bottlenecks.",
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
