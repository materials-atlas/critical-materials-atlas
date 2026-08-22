"""Extract mixed-use data-centre equipment trade context from local BACI archives."""
from __future__ import annotations

import csv
import io
import json
import os
import zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
COUNTRIES = os.path.join(ROOT, "raw", "baci", "country_codes_V202601.csv")
OUT = os.path.join(HERE, "out", "data_centre_trade.json")
BATCHES = [
    ("HS02", range(2002, 2017), "BACI_HS02_V202601.zip", "BACI_HS02_Y{year}_V202601.csv"),
    ("HS17", range(2017, 2025), "BACI_HS17_V202601.zip", "BACI_HS17_Y{year}_V202601.csv"),
]
GROUPS = {
    "processing_units": {"title": "Digital processing units", "codes": ["847150"], "boundary": "Processing units for automatic data-processing systems; not a clean server, GPU or data-centre category."},
    "storage_units": {"title": "Computer storage units", "codes": ["847170"], "boundary": "Storage units for all computer systems and end uses; cloud capacity and services are not measured."},
    "static_converters": {"title": "Static converters", "codes": ["850440"], "boundary": "Includes UPS and power supplies used in many industries; it does not isolate data-centre power systems."},
    "heat_exchange_units": {"title": "Heat-exchange units", "codes": ["841950"], "boundary": "Broad industrial equipment; data-centre air and liquid cooling are not separately identified."},
}
CODE_GROUP = {code: group for group, spec in GROUPS.items() for code in spec["codes"]}
FORCE_ISO = {"490": "TW", "516": "NA"}
FORCE_NAME = {"TW": "Taiwan", "NA": "Namibia"}


def country_maps():
    iso, names = {}, {}
    with open(COUNTRIES, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            code = (row.get("country_iso2") or "").strip()
            if code and code != "NA":
                iso[row["country_code"].strip()] = code
                names[code] = (row.get("country_name") or code).strip()
    iso.update(FORCE_ISO)
    names.update(FORCE_NAME)
    return iso, names


def empty():
    return {"exp": defaultdict(float), "imp": defaultdict(float), "usd": 0.0, "tonnes": 0.0}


def leaders(values, total, names):
    if not total:
        return []
    return [{"iso": key, "name": names.get(key, key), "value_usd": round(value), "share": round(value / total, 4)}
            for key, value in sorted(values.items(), key=lambda item: -item[1])[:8]]


def extract():
    iso, names = country_maps()
    bag = {year: {group: empty() for group in GROUPS} for _, years, _, _ in BATCHES for year in years}
    vintage = {year: hs for hs, years, _, _ in BATCHES for year in years}
    for hs, years, archive, member in BATCHES:
        with zipfile.ZipFile(os.path.join(ROOT, "raw", "baci", archive)) as zipped:
            for year in years:
                print("reading", year, hs, flush=True)
                with zipped.open(member.format(year=year)) as raw:
                    handle = io.TextIOWrapper(raw, encoding="utf-8", newline="")
                    next(handle)
                    for line in handle:
                        parts = line.split(",")
                        group = CODE_GROUP.get(parts[3]) if len(parts) >= 6 else None
                        if not group:
                            continue
                        exporter, importer = iso.get(parts[1]), iso.get(parts[2])
                        if not exporter or not importer or exporter == importer:
                            continue
                        try:
                            usd = float(parts[4]) * 1000
                        except ValueError:
                            continue
                        if usd <= 0:
                            continue
                        try:
                            tonnes = float(parts[5]) if parts[5].strip() not in ("", "NA", "nan") else 0
                        except ValueError:
                            tonnes = 0
                        row = bag[year][group]
                        row["exp"][exporter] += usd
                        row["imp"][importer] += usd
                        row["usd"] += usd
                        row["tonnes"] += max(0, tonnes)
    output = {"source": "CEPII BACI V202601, based on UN Comtrade", "years": sorted(bag),
              "vintage": {str(year): vintage[year] for year in bag}, "groups": GROUPS,
              "years_data": {}, "series": {}}
    for year in output["years"]:
        output["years_data"][str(year)] = {}
        for group in GROUPS:
            row, total = bag[year][group], bag[year][group]["usd"]
            shares = [value / total for value in row["exp"].values()] if total else []
            output["years_data"][str(year)][group] = {
                "world_usd": round(total), "world_tonnes": round(row["tonnes"], 1),
                "export_hhi": round(sum(value * value for value in shares), 4) if total else None,
                "exporters": leaders(row["exp"], total, names), "importers": leaders(row["imp"], total, names),
            }
    for group in GROUPS:
        output["series"][group] = [{"year": year, **output["years_data"][str(year)][group]} for year in output["years"]]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("WROTE", OUT)
    for group, rows in output["series"].items():
        print(group, f"${rows[0]['world_usd']/1e9:.2f}B -> ${rows[-1]['world_usd']/1e9:.2f}B")


if __name__ == "__main__":
    extract()
