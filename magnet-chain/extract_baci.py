"""Extract broad upstream and magnet trade baskets from local BACI archives.

The codes are context, not physical supply-chain measures:
  280530  rare-earth metals, including scandium/yttrium and mixtures
  284690  non-cerium rare-earth compounds, including scandium/yttrium
  850511  permanent magnets of metal, including non-rare-earth chemistries

Run from the repository root: python magnet-chain/extract_baci.py
"""
from __future__ import annotations

import csv
import io
import json
import os
import zipfile
from collections import defaultdict


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CC_PATH = os.path.join(ROOT, "raw", "baci", "country_codes_V202601.csv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "magnet_trade.json")
BATCHES = [
    ("HS02", range(2002, 2017), "BACI_HS02_V202601.zip", "BACI_HS02_Y{year}_V202601.csv"),
    ("HS17", range(2017, 2025), "BACI_HS17_V202601.zip", "BACI_HS17_Y{year}_V202601.csv"),
]
CODES = {
    "280530": {"title": "Rare-earth metals, scandium and yttrium", "boundary": "Includes scandium, yttrium, mixtures and interalloys; not magnet-element-specific."},
    "284690": {"title": "Other rare-earth compounds", "boundary": "Excludes cerium but includes scandium, yttrium and mixtures; not a separated Nd/Pr/Dy/Tb series."},
    "850511": {"title": "Permanent magnets of metal", "boundary": "Includes NdFeB, SmCo, AlNiCo and other metallic permanent magnets; not rare-earth-specific."},
}
FORCE_ISO = {"490": "TW", "516": "NA"}
FORCE_NAME = {"TW": "Taiwan", "NA": "Namibia"}


def countries():
    iso, names = {}, {}
    with open(CC_PATH, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key, code = row["country_code"].strip(), (row.get("country_iso2") or "").strip()
            if code and code != "NA":
                iso[key] = code
                names[code] = (row.get("country_name") or code).strip()
    iso.update(FORCE_ISO)
    names.update(FORCE_NAME)
    return iso, names


def cell():
    return {"exporters": defaultdict(float), "importers": defaultdict(float), "usd": 0.0, "tonnes": 0.0, "flows": 0}


def top(mapping, total, names, n=8):
    return [{"iso": iso, "name": names.get(iso, iso), "value_usd": round(value), "share": round(value / total, 4)}
            for iso, value in sorted(mapping.items(), key=lambda item: -item[1])[:n]] if total else []


def extract():
    iso_map, names = countries()
    bag, vintage = {}, {}
    for hs, years, _, _ in BATCHES:
        for year in years:
            bag[year] = {code: cell() for code in CODES}
            vintage[year] = hs
    for hs, years, archive, pattern in BATCHES:
        path = os.path.join(ROOT, "raw", "baci", archive)
        with zipfile.ZipFile(path) as zipped:
            for year in years:
                print("reading", year, hs, flush=True)
                with zipped.open(pattern.format(year=year)) as raw:
                    handle = io.TextIOWrapper(raw, encoding="utf-8", newline="")
                    next(handle)
                    for line in handle:
                        p = line.split(",")
                        if len(p) < 6 or p[3] not in CODES:
                            continue
                        exporter, importer = iso_map.get(p[1]), iso_map.get(p[2])
                        if not exporter or not importer or exporter == importer:
                            continue
                        try:
                            usd = float(p[4]) * 1000
                        except ValueError:
                            continue
                        if usd <= 0:
                            continue
                        try:
                            tonnes = float(p[5]) if p[5].strip() not in ("", "NA", "nan") else 0.0
                        except ValueError:
                            tonnes = 0.0
                        rec = bag[year][p[3]]
                        rec["exporters"][exporter] += usd
                        rec["importers"][importer] += usd
                        rec["usd"] += usd
                        rec["tonnes"] += max(0, tonnes)
                        rec["flows"] += 1

    years = sorted(bag)
    out = {"source": "CEPII BACI V202601, based on UN Comtrade", "coverage": "2002-2024", "codes": CODES, "years": years, "years_data": {}, "series": {}}
    for year in years:
        out["years_data"][str(year)] = {}
        for code in CODES:
            rec, total = bag[year][code], bag[year][code]["usd"]
            shares = [value / total for value in rec["exporters"].values()] if total else []
            out["years_data"][str(year)][code] = {
                "hs": vintage[year], "world_usd": round(total), "world_tonnes": round(rec["tonnes"], 1), "n_flows": rec["flows"],
                "china_export_share": round(rec["exporters"].get("CN", 0) / total, 4) if total else None,
                "export_hhi": round(sum(share * share for share in shares), 4) if total else None,
                "exporters": top(rec["exporters"], total, names), "importers": top(rec["importers"], total, names),
            }
    for code in CODES:
        out["series"][code] = [{"year": year, **{key: out["years_data"][str(year)][code][key] for key in ("hs", "world_usd", "world_tonnes", "china_export_share", "export_hhi")}} for year in years]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("WROTE", OUT)
    for code in CODES:
        a, b = out["series"][code][0], out["series"][code][-1]
        print(code, f"China export share {a['china_export_share']:.1%} -> {b['china_export_share']:.1%}")


if __name__ == "__main__":
    extract()
