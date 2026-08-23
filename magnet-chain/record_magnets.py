"""Build the evidence JSON for the unpublished permanent-magnet chain pilot.

Production, processing, magnet manufacturing and customs trade remain separate.
Run from the repository root: python magnet-chain/record_magnets.py
"""
from __future__ import annotations

import csv
import json
import os
import re
from collections import defaultdict

import openpyxl


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "magnet_chain.json")
EU27 = {"AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "EL", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"}

SOURCES = {
    "usgs_history": {
        "title": "USGS, Historical Statistics for Mineral and Material Commodities: Rare Earths",
        "year": 2023,
        "url": "https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities",
    },
    "bgs_wms": {
        "title": "British Geological Survey, World Mineral Statistics",
        "year": 2026,
        "url": "https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/world-mineral-statistics-data-download/",
    },
    "iea_ree": {
        "title": "IEA, Rare Earth Elements — Executive summary",
        "year": 2026,
        "url": "https://www.iea.org/reports/rare-earth-elements/executive-summary",
        "licence": "CC BY 4.0",
    },
    "comext": {
        "title": "Eurostat Comext, EU trade since 1988 by HS2-4-6 and CN8",
        "year": 2026,
        "url": "https://ec.europa.eu/eurostat/web/international-trade-in-goods/database",
    },
    "baci": {
        "title": "CEPII BACI V202601, based on UN Comtrade",
        "year": 2026,
        "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37",
    },
}


def usgs_world():
    path = os.path.join(ROOT, "raw", "usgs_hist", "rare-earths.xlsx")
    sheet = openpyxl.load_workbook(path, data_only=True, read_only=True)["Rare earths"]
    rows = []
    for row in sheet.iter_rows(min_row=6, values_only=True):
        year, world = row[0], row[7]
        if isinstance(year, int) and isinstance(world, (int, float)):
            rows.append({"year": year, "world_tonnes_reo": round(world)})
    if (rows[0]["year"], rows[-1]["year"]) != (1900, 2020):
        raise SystemExit("Unexpected USGS historical coverage")
    return rows


def bgs_panel():
    path = os.path.join(ROOT, "raw", "bgs_rare_earth_oxides_1992_2024.json")
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    grouped = defaultdict(lambda: defaultdict(float))
    names = {}
    for row in raw["rows"]:
        if row["quantity"] is None or not row["country_iso3_code"]:
            continue
        year = int(row["year"][:4])
        iso = row["country_iso3_code"]
        grouped[year][iso] += float(row["quantity"])
        names[iso] = row["country_trans"]
    series = []
    for year in sorted(grouped):
        countries, world = grouped[year], sum(grouped[year].values())
        top = [{"iso": iso, "name": names.get(iso, iso), "tonnes_reo": round(value), "share": round(value / world, 4)}
               for iso, value in sorted(countries.items(), key=lambda item: -item[1])[:8]]
        series.append({
            "year": year, "world_tonnes_reo": round(world),
            "china_tonnes_reo": round(countries.get("CHN", 0)),
            "china_share": round(countries.get("CHN", 0) / world, 4) if world else None,
            "top_producers": top,
        })
    return {"unit": raw["units"], "measure": raw["measure"], "source_notes": raw["source_notes"], "series": series}


def is_aggregate(code):
    return bool(re.search(r"EU|EA|EXT|INT|WORLD|TOTAL|_", code))


def read_comext(filename):
    rows = []
    with open(os.path.join(ROOT, "raw", filename), encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                value = float(row["OBS_VALUE"])
            except (TypeError, ValueError):
                continue
            rows.append({"year": int(row["TIME_PERIOD"]), "reporter": row["reporter"], "partner": row["partner"], "value": value})
    return rows


def comext_origin():
    values = read_comext("magnets_85051110_value.csv")
    quantities = read_comext("magnets_85051110_qty.csv")
    val, qty = defaultdict(float), defaultdict(float)
    for row in values:
        if row["reporter"] in EU27 and row["partner"] not in EU27 and not is_aggregate(row["partner"]):
            val[(row["year"], row["partner"])] += row["value"]
    for row in quantities:
        if row["reporter"] in EU27 and row["partner"] not in EU27 and not is_aggregate(row["partner"]):
            qty[(row["year"], row["partner"])] += row["value"] / 10
    output = []
    for year in sorted({key[0] for key in val}):
        origins = {partner: amount for (y, partner), amount in val.items() if y == year}
        total = sum(origins.values())
        total_qty = sum(amount for (y, _), amount in qty.items() if y == year)
        top = [{"origin": origin, "value_eur": round(amount), "tonnes": round(qty.get((year, origin), 0), 1), "value_share": round(amount / total, 4)}
               for origin, amount in sorted(origins.items(), key=lambda item: -item[1])[:8]]
        output.append({
            "year": year, "total_eur": round(total), "total_tonnes": round(total_qty, 1),
            "china_value_share": round(origins.get("CN", 0) / total, 4),
            "china_quantity_share": round(qty.get((year, "CN"), 0) / total_qty, 4) if total_qty else None,
            "origin_hhi": round(sum((amount / total) ** 2 for amount in origins.values()), 4), "top_origins": top,
        })
    return output


def build():
    data = {
        "title": "Rare-earth permanent-magnet chain evidence",
        "status": "unpublished pilot",
        "updated": "2026-08-17",
        "principle": "Mine output, separation/refining, magnet production and customs origin are different measures.",
        "chain": [
            {"stage": "Mine", "detail": "Ore containing many rare-earth elements"},
            {"stage": "Beneficiate", "detail": "Concentrate the rare-earth minerals"},
            {"stage": "Separate", "detail": "Produce individual Nd, Pr, Dy and Tb oxides"},
            {"stage": "Metal & alloy", "detail": "Refine metals and make NdFeB alloy"},
            {"stage": "Magnet", "detail": "Press, sinter, machine, coat and magnetise"},
            {"stage": "Motor & generator", "detail": "Integrate magnets into EVs, wind turbines and industry"},
        ],
        "usgs_world_production": {
            "coverage": "1900-2020", "unit": "metric tonnes, rare-earth-oxide equivalent",
            "source": "usgs_history", "series": usgs_world(),
            "boundary": "World total only. The source workbook ends in 2020; it is not extended with BGS values.",
        },
        "bgs_mine_production": {
            "coverage": "1992-2024", "source": "bgs_wms", **bgs_panel(),
            "boundary": "All rare earths expressed as oxide equivalent, not only the four magnet rare earths.",
        },
        "magnet_specific_2024": {
            "year": 2024, "source": "iea_ree", "scope": "magnet rare earths (Nd, Pr, Dy and Tb)",
            "stages": [
                {"stage": "Mining", "china_share": 0.60},
                {"stage": "Separation and refining", "china_share": 0.91},
                {"stage": "Sintered permanent magnets", "china_share": 0.94},
            ],
            "boundary": "The stages are shares of different physical markets; they are not additive.",
        },
        "magnet_manufacturing_history": {
            "source": "iea_ree", "metric": "China share of global sintered permanent-magnet production",
            "series": [{"year": 2005, "share": 0.50, "precision": "approximately"}, {"year": 2024, "share": 0.94, "precision": "reported"}],
            "boundary": "Two published anchors, not an annual interpolated series.",
        },
        "global_trade": {
            "coverage": "2002-2024", "source": "baci", "file": "out/magnet_trade.json",
            "boundary": "HS 850511 covers all metallic permanent magnets, not only rare-earth magnets. Upstream codes are also broad.",
        },
        "eu_rare_earth_magnet_imports": {
            "coverage": "2023-2025; latest year provisional", "source": "comext", "code": "CN 85051110",
            "measure": "EU-27 extra-EU imports by partner/origin", "series": comext_origin(),
            "headline_rule": "Use 2024 as the latest complete year; 2025 is retained but marked provisional.",
            "boundary": "Clean rare-earth permanent-magnet product code, but only the EU's extra-EU import market—not global production or trade.",
        },
        "comparison_warning": {
            "items": [
                "BGS 2024: China's share of mine production for all rare earths (REO equivalent).",
                "IEA 2024: China's share at magnet-specific physical stages.",
                "BACI 2024: China's share of global export value under broad HS 850511.",
                "Comext 2024: China's origin share of EU extra-EU imports under clean CN 85051110.",
            ],
            "rule": "These percentages answer different questions and must not be subtracted or averaged.",
        },
        "sources": SOURCES,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("WROTE", OUT)
    mine = data["bgs_mine_production"]["series"][-1]
    eu = next(row for row in data["eu_rare_earth_magnet_imports"]["series"] if row["year"] == 2024)
    print("2024 BGS all-REE mine share, China:", f"{mine['china_share']:.1%}")
    print("2024 EU CN8 import-origin share, China:", f"{eu['china_value_share']:.1%}")
    return data


if __name__ == "__main__":
    build()
