"""Extract broad grid-equipment trade baskets from local BACI archives."""
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
OUT = os.path.join(HERE, "out", "grid_trade.json")
BATCHES = [
    ("HS02", range(2002, 2017), "BACI_HS02_V202601.zip", "BACI_HS02_Y{year}_V202601.csv"),
    ("HS17", range(2017, 2025), "BACI_HS17_V202601.zip", "BACI_HS17_Y{year}_V202601.csv"),
]
GROUPS = {
    "goes": {
        "title": "Grain-oriented electrical steel",
        "codes": ["722511", "722611"],
        "boundary": "GOES sheet and strip in two width classes; broader than transformer-core end use.",
    },
    "aluminium_conductors": {
        "title": "Bare aluminium stranded conductors",
        "codes": ["761410", "761490"],
        "boundary": "Non-insulated stranded wire and cable, with or without steel core; includes non-grid uses.",
    },
    "liquid_transformers": {
        "title": "Liquid-dielectric transformers",
        "codes": ["850421", "850422", "850423"],
        "boundary": "A relatively clean equipment basket spanning small distribution through large power transformers.",
    },
    "high_voltage_cables": {
        "title": "Insulated conductors above 1 kV",
        "codes": ["854460"],
        "boundary": "Includes high-voltage conductors for grid and other uses; voltage alone does not identify a network project.",
    },
}
CODE_TO_GROUPS = defaultdict(list)
for group, definition in GROUPS.items():
    for code in definition["codes"]:
        CODE_TO_GROUPS[code].append(group)

FORCE_ISO = {"490": "TW", "516": "NA"}
FORCE_NAME = {"TW": "Taiwan", "NA": "Namibia"}


def country_maps():
    iso, names = {}, {}
    with open(COUNTRIES, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = row["country_code"].strip()
            code = (row.get("country_iso2") or "").strip()
            if code and code != "NA":
                iso[key] = code
                names[code] = (row.get("country_name") or code).strip()
    iso.update(FORCE_ISO)
    names.update(FORCE_NAME)
    return iso, names


def empty():
    return {"exp": defaultdict(float), "imp": defaultdict(float), "usd": 0.0, "tonnes": 0.0, "flows": 0}


def top(values, total, names, n=8):
    if not total:
        return []
    return [
        {"iso": iso, "name": names.get(iso, iso), "value_usd": round(value), "share": round(value / total, 4)}
        for iso, value in sorted(values.items(), key=lambda item: -item[1])[:n]
    ]


def extract():
    iso_map, names = country_maps()
    bag, vintage = {}, {}
    for hs, years, _, _ in BATCHES:
        for year in years:
            bag[year] = {group: empty() for group in GROUPS}
            vintage[year] = hs

    for hs, years, archive, member in BATCHES:
        with zipfile.ZipFile(os.path.join(ROOT, "raw", "baci", archive)) as zipped:
            for year in years:
                print("reading", year, hs, flush=True)
                with zipped.open(member.format(year=year)) as raw:
                    handle = io.TextIOWrapper(raw, encoding="utf-8", newline="")
                    next(handle)
                    for line in handle:
                        parts = line.split(",")
                        if len(parts) < 6 or parts[3] not in CODE_TO_GROUPS:
                            continue
                        exporter, importer = iso_map.get(parts[1]), iso_map.get(parts[2])
                        if not exporter or not importer or exporter == importer:
                            continue
                        try:
                            usd = float(parts[4]) * 1000
                        except ValueError:
                            continue
                        if usd <= 0:
                            continue
                        try:
                            tonnes = float(parts[5]) if parts[5].strip() not in ("", "NA", "nan") else 0.0
                        except ValueError:
                            tonnes = 0.0
                        for group in CODE_TO_GROUPS[parts[3]]:
                            row = bag[year][group]
                            row["exp"][exporter] += usd
                            row["imp"][importer] += usd
                            row["usd"] += usd
                            row["tonnes"] += max(0, tonnes)
                            row["flows"] += 1

    years = sorted(bag)
    out = {
        "source": "CEPII BACI V202601, based on UN Comtrade",
        "coverage": "2002-2024",
        "years": years,
        "vintage": {str(year): vintage[year] for year in years},
        "groups": GROUPS,
        "years_data": {},
        "series": {},
    }
    for year in years:
        out["years_data"][str(year)] = {}
        for group in GROUPS:
            row, total = bag[year][group], bag[year][group]["usd"]
            shares = [value / total for value in row["exp"].values()] if total else []
            out["years_data"][str(year)][group] = {
                "hs": vintage[year],
                "world_usd": round(total),
                "world_tonnes": round(row["tonnes"], 1),
                "n_flows": row["flows"],
                "china_export_share": round(row["exp"].get("CN", 0) / total, 4) if total else None,
                "export_hhi": round(sum(share * share for share in shares), 4) if total else None,
                "exporters": top(row["exp"], total, names),
                "importers": top(row["imp"], total, names),
            }
    for group in GROUPS:
        out["series"][group] = [
            {"year": year, **{key: out["years_data"][str(year)][group][key] for key in ("hs", "world_usd", "world_tonnes", "china_export_share", "export_hhi")}}
            for year in years
        ]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("WROTE", OUT)
    for group in GROUPS:
        first, last = out["series"][group][0], out["series"][group][-1]
        print(group, f"${first['world_usd']/1e9:.2f}B -> ${last['world_usd']/1e9:.2f}B")


if __name__ == "__main__":
    extract()
