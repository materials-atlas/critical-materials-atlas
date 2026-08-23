"""Master BACI extractor for the 10 ported value-chain pilots.

Reads the local BACI HS02 (2002-2016) and HS17 (2017-2024) archives ONCE and emits one
<base>_trade.json per chain in the same schema the shared renderer (chainview.js tradeRow)
expects: {source, years, vintage, codes, years_data, series}. Trade is context, not capability —
every code carries a boundary flag. Run from repo root: python extract_all_chains.py
"""
from __future__ import annotations
import csv, io, json, os, zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
COUNTRIES = os.path.join(ROOT, "raw", "baci", "country_codes_V202601.csv")
BATCHES = [
    ("HS02", range(2002, 2017), "BACI_HS02_V202601.zip", "BACI_HS02_Y{year}_V202601.csv"),
    ("HS17", range(2017, 2025), "BACI_HS17_V202601.zip", "BACI_HS17_Y{year}_V202601.csv"),
]
FORCE_ISO = {"490": "TW", "516": "NA"}
FORCE_NAME = {"TW": "Taiwan", "NA": "Namibia"}

# chain -> (out_dir, out_base, CODES{hs6: {title, boundary}})
CHAINS = {
    "solar": ("solar-chain", "solar", {
        "280461": {"title": "Silicon, >= 99.99% pure", "boundary": "Polysilicon feedstock (PV + semiconductor); the pure-silicon input, not the panel."},
        "854140": {"title": "Photosensitive / PV semiconductor devices", "boundary": "Cells and modules; the PV heading was reclassified in 2022, so later years shift codes."},
    }),
    "wind": ("wind-chain", "wind", {
        "850231": {"title": "Wind-powered generating sets", "boundary": "Complete turbines only; blades, nacelles and towers trade under generic parts and are mostly built locally."},
    }),
    "ev": ("ev-chain", "ev", {
        "870380": {"title": "Motor cars, only electric motor", "boundary": "HS2017 code; a finished EV's origin is its assembly plant, not the battery or magnet chain behind it."},
        "850760": {"title": "Lithium-ion accumulators", "boundary": "The pack/cells; origin is the cell plant, not the mine or refinery. HS2017 code, sparse before 2017."},
    }),
    "battery": ("battery-chain", "battery", {
        "850760": {"title": "Lithium-ion accumulators", "boundary": "Cells; customs origin is the assembly plant, not the refining midstream. HS2017 code, sparse before 2017."},
        "283691": {"title": "Lithium carbonate", "boundary": "A refined battery chemical; a trading/refining position, not the mine."},
    }),
    "magnet": ("magnet-chain", "magnet", {
        "850511": {"title": "Permanent magnets, of metal", "boundary": "NdFeB and other metal magnets; origin is the last shipment point, not where the ore was separated."},
        "280530": {"title": "Rare-earth metals, scandium and yttrium", "boundary": "Rare-earth metals; the concentrated separation stage is upstream and not visible in this line."},
    }),
    "nuclear": ("nuclear-chain", "nuclear", {
        "261210": {"title": "Uranium ores and concentrates", "boundary": "Mined concentrate only; conversion and enrichment are traded as services, invisible in customs data."},
        "284410": {"title": "Natural uranium and its compounds", "boundary": "Front-end uranium material; the enrichment chokepoint is a service, not a traded good."},
    }),
    "grid": ("grid-chain", "grid", {
        "850422": {"title": "Liquid-dielectric transformers, 650-10,000 kVA", "boundary": "Power transformers; origin is the assembly plant, and the years-long lead time is not visible in trade."},
        "740811": {"title": "Copper wire, cross-section > 6 mm", "boundary": "A conductor form; the metal is abundant, so this is availability of the traded form, not a chokepoint."},
    }),
    "heat_pump": ("heat-pump-chain", "heat_pump", {
        "841861": {"title": "Heat pumps (other than air conditioners)", "boundary": "HS2017 code; the binding constraint (skilled installation) is a domestic service, not a traded good."},
    }),
    "electrolyser": ("electrolyser-chain", "electrolyser", {
        "854330": {"title": "Machines for electrolysis / electroplating", "boundary": "Electrolysers scatter across machinery headings; PEM and alkaline are not separable here."},
        "711049": {"title": "Platinum-group metals, semi-manufactured", "boundary": "A PGM basket that includes iridium; the specific iridium line cannot be isolated."},
    }),
    "data_centre": ("data-centre-chain", "data_centre", {
        "847150": {"title": "Automatic data-processing units (servers)", "boundary": "Server hardware only; the binding inputs (electricity, grid connection) are not traded goods."},
        "854231": {"title": "Electronic integrated circuits, processors", "boundary": "Processors; a chip chokepoint of their own (see the silicon-chip chain), shown as context."},
    }),
}

# code -> list of chains that use it
CODE_TO_CHAINS = defaultdict(list)
for ch, (_, _, codes) in CHAINS.items():
    for code in codes:
        CODE_TO_CHAINS[code].append(ch)
ALL_CODES = set(CODE_TO_CHAINS)


def country_maps():
    iso, names = {}, {}
    with open(COUNTRIES, encoding="utf-8") as handle:
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
    # bag[chain][year][code]
    bag, vintage = {}, {}
    for ch, (_, _, codes) in CHAINS.items():
        bag[ch] = {}
        for _, years, _, _ in BATCHES:
            for year in years:
                bag[ch][year] = {code: empty() for code in codes}
                vintage[year] = None
    for hs, years, archive, member in BATCHES:
        for year in years:
            vintage[year] = hs
        with zipfile.ZipFile(os.path.join(ROOT, "raw", "baci", archive)) as zipped:
            for year in years:
                print("reading", year, hs, flush=True)
                with zipped.open(member.format(year=year)) as raw:
                    handle = io.TextIOWrapper(raw, encoding="utf-8", newline="")
                    next(handle)
                    for line in handle:
                        p = line.split(",")
                        if len(p) < 6:
                            continue
                        code = p[3]
                        if code not in ALL_CODES:
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
                        for ch in CODE_TO_CHAINS[code]:
                            row = bag[ch][year][code]
                            row["exp"][exporter] += usd; row["imp"][importer] += usd
                            row["usd"] += usd; row["tonnes"] += max(0, tonnes); row["flows"] += 1
    for ch, (out_dir, out_base, codes) in CHAINS.items():
        years = sorted(bag[ch])
        out = {"source": "CEPII BACI V202601, based on UN Comtrade", "years": years,
               "vintage": {str(y): vintage[y] for y in years}, "codes": codes, "years_data": {}, "series": {}}
        for year in years:
            out["years_data"][str(year)] = {}
            for code in codes:
                row, total = bag[ch][year][code], bag[ch][year][code]["usd"]
                shares = [v / total for v in row["exp"].values()] if total else []
                out["years_data"][str(year)][code] = {
                    "hs": vintage[year], "world_usd": round(total), "world_tonnes": round(row["tonnes"], 1), "n_flows": row["flows"],
                    "china_export_share": round(row["exp"].get("CN", 0) / total, 4) if total else None,
                    "export_hhi": round(sum(s * s for s in shares), 4) if total else None,
                    "exporters": top(row["exp"], total, names), "importers": top(row["imp"], total, names),
                }
        for code in codes:
            out["series"][code] = [{"year": year, **{k: out["years_data"][str(year)][code][k]
                                    for k in ("hs", "world_usd", "world_tonnes", "china_export_share", "export_hhi")}} for year in years]
        path = os.path.join(ROOT, out_dir, "out", out_base + "_trade.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(out, handle, ensure_ascii=False, indent=2); handle.write("\n")
        latest = out["years_data"][str(years[-1])]
        tot = sum(latest[c]["world_usd"] for c in codes)
        print("WROTE", os.path.relpath(path, ROOT), f"| {years[-1]} world ~${tot/1e9:.1f}B across {len(codes)} code(s)")


if __name__ == "__main__":
    extract()
