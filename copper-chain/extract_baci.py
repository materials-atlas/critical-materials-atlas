"""Extract copper-chain trade context from local BACI archives.

Trade context only: cathode and scrap route through metal hubs and refiners, so exporter shares
are trading/refining positions, not the mine base. Read as availability of the traded form.
"""
from __future__ import annotations
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))); import baci as _baci  # the one door for BACI (ARCHITECTURE.md phase 2)
import csv, io, json, os, zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNTRIES = None  # served by _baci.country_file()
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "copper_trade.json")
BATCHES = [
    ("HS02", range(2002, 2017), "BACI_HS02_V202601.zip", "BACI_HS02_Y{year}_V202601.csv"),
    ("HS17", range(2017, 2025), "BACI_HS17_V202601.zip", "BACI_HS17_Y{year}_V202601.csv"),
]
CODES = {
    "260300": {"title": "Copper ores and concentrates", "boundary": "The mined concentrate; Chile/Peru/DRC lead, routed heavily to Chinese smelters."},
    "740311": {"title": "Refined copper cathodes", "boundary": "The refined metal; Chile/DRC and hubs export, but China is the largest refiner/consumer."},
    "740811": {"title": "Copper wire, cross-section > 6 mm", "boundary": "A semi-finished form electrification uses; not all copper wire."},
    "740400": {"title": "Copper waste and scrap", "boundary": "The recycling stream; routes through hubs, and much scrap is used domestically."},
}
FORCE_ISO = {"490": "TW", "516": "NA"}
FORCE_NAME = {"TW": "Taiwan", "NA": "Namibia"}


def country_maps():
    iso, names = {}, {}
    with _baci.country_file() as handle:
        for row in csv.DictReader(handle):
            key, code = row["country_code"].strip(), (row.get("country_iso2") or "").strip()
            if code and code != "NA":
                iso[key] = code
                names[code] = (row.get("country_name") or code).strip()
    iso.update(FORCE_ISO); names.update(FORCE_NAME)
    return iso, names


def empty():
    return {"exp": defaultdict(float), "imp": defaultdict(float), "usd": 0.0, "tonnes": 0.0, "flows": 0}


def top(values, total, names, n=8):
    return [{"iso": iso, "name": names.get(iso, iso), "value_usd": round(value), "share": round(value / total, 4)}
            for iso, value in sorted(values.items(), key=lambda item: -item[1])[:n]] if total else []


def extract():
    iso_map, names = country_maps()
    bag, vintage = {}, {}
    for hs, years, _, _ in BATCHES:
        for year in years:
            bag[year] = {code: empty() for code in CODES}
            vintage[year] = hs
    for hs, years, archive, member in BATCHES:
        for year in years:
            print("reading", year, hs, flush=True)
            for p in _baci.year(year, columns=["i", "j", "k", "v", "q"], codes=CODES).itertuples(index=False):
                exporter, importer = iso_map.get(str(p.i)), iso_map.get(str(p.j))
                if not exporter or not importer or exporter == importer:
                    continue
                if p.v != p.v:
                    continue          # value NA -> the old float() raised and skipped the row
                usd = p.v * 1000
                if usd <= 0:
                    continue
                tonnes = p.q if p.q == p.q else 0.0
                row = bag[year][p.k]
                row["exp"][exporter] += usd; row["imp"][importer] += usd
                row["usd"] += usd; row["tonnes"] += max(0, tonnes); row["flows"] += 1
    years = sorted(bag)
    out = {"source": "CEPII BACI V202601, based on UN Comtrade", "years": years,
           "vintage": {str(y): vintage[y] for y in years}, "codes": CODES, "years_data": {}, "series": {}}
    for year in years:
        out["years_data"][str(year)] = {}
        for code in CODES:
            row, total = bag[year][code], bag[year][code]["usd"]
            shares = [value / total for value in row["exp"].values()] if total else []
            out["years_data"][str(year)][code] = {
                "hs": vintage[year], "world_usd": round(total), "world_tonnes": round(row["tonnes"], 1), "n_flows": row["flows"],
                "china_export_share": round(row["exp"].get("CN", 0) / total, 4) if total else None,
                "export_hhi": round(sum(s * s for s in shares), 4) if total else None,
                "exporters": top(row["exp"], total, names), "importers": top(row["imp"], total, names),
            }
    for code in CODES:
        out["series"][code] = [{"year": year, **{k: out["years_data"][str(year)][code][k]
                                for k in ("hs", "world_usd", "world_tonnes", "china_export_share", "export_hhi")}} for year in years]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=2); handle.write("\n")
    print("WROTE", OUT)
    for code in CODES:
        a, b = out["series"][code][0], out["series"][code][-1]
        ca = f"{a['china_export_share']:.1%}" if a['china_export_share'] is not None else "n/a"
        cb = f"{b['china_export_share']:.1%}" if b['china_export_share'] is not None else "n/a"
        print(code, f"${a['world_usd']/1e9:.1f}B -> ${b['world_usd']/1e9:.1f}B", f"CN {ca} -> {cb}")


if __name__ == "__main__":
    extract()
