"""Draft extractor — silicon metal vs high-purity silicon vs wafers.

Reads the already-downloaded CEPII BACI HS17 V202601 zip (same source as the
live Atlas) and keeps only three HS6 codes. Does not touch out/ or the 32.

  280469  Silicon <  99.99%     — current Atlas `silicon`
  280461  Silicon >= 99.99%     — solar poly + electronic poly, mixed
  381800  Doped discs / wafers  — silicon and compound wafers, mixed

Run from repo root:  python silicon-chip/extract_baci.py
"""
from __future__ import annotations

import csv
import io
import json
import os
import zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(ROOT, "raw", "baci", "BACI_HS17_V202601.zip")
CC_PATH = os.path.join(ROOT, "raw", "baci", "country_codes_V202601.csv")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
YEARS = list(range(2018, 2025))
CODES = {
    "280469": {
        "label": "silicon_metal",
        "title": "Silicon, < 99.99%",
        "atlas": "current Atlas silicon (HS 28046900)",
        "flag": "industrial / metallurgical silicon metal",
    },
    "280461": {
        "label": "silicon_highpurity",
        "title": "Silicon, >= 99.99%",
        "atlas": "not in the 32",
        "flag": "MIXED: solar-grade polysilicon and electronic-grade polysilicon share this code",
    },
    "381800": {
        "label": "wafers",
        "title": "Doped discs / wafers for electronics",
        "atlas": "not in the 32",
        "flag": "MIXED: silicon wafers and compound-semiconductor wafers share this code",
    },
}

# Same Taiwan / Namibia patch as build_flows_years.ps1
FORCE_ISO = {"490": "TW", "516": "NA"}
FORCE_NAME = {"TW": "Taiwan", "NA": "Namibia"}


def load_countries():
    iso, name = {}, {}
    with open(CC_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            code = r["country_code"].strip()
            iso2 = (r.get("country_iso2") or "").strip()
            n = (r.get("country_name") or "").strip()
            if iso2 and iso2 != "NA":
                iso[code] = iso2
                name[iso2] = n
    iso.update(FORCE_ISO)
    name.update(FORCE_NAME)
    return iso, name


def hhi(shares):
    return round(sum(s * s for s in shares), 4)


def topn(d, total, n=8):
    if total <= 0:
        return []
    rows = []
    for k, v in sorted(d.items(), key=lambda kv: -kv[1])[:n]:
        rows.append({"iso": k, "value_usd": round(v), "share": round(v / total, 4)})
    return rows


def extract():
    iso_map, names = load_countries()
    # year -> code -> {exp: {iso: usd}, imp: {iso: usd}, q_exp, q_imp, usd, tonnes, n}
    bag = {
        y: {
            c: {
                "exp_usd": defaultdict(float),
                "imp_usd": defaultdict(float),
                "exp_t": defaultdict(float),
                "imp_t": defaultdict(float),
                "usd": 0.0,
                "tonnes": 0.0,
                "n": 0,
            }
            for c in CODES
        }
        for y in YEARS
    }

    with zipfile.ZipFile(ZIP_PATH) as z:
        for year in YEARS:
            name = f"BACI_HS17_Y{year}_V202601.csv"
            print(f"reading {name} …", flush=True)
            with z.open(name) as raw:
                fh = io.TextIOWrapper(raw, encoding="utf-8", newline="")
                header = next(fh)
                if not header.startswith("t,"):
                    raise SystemExit(f"unexpected header in {name}: {header!r}")
                for line in fh:
                    # t,i,j,k,v,q  — no quoted commas in BACI data rows
                    p = line.split(",")
                    if len(p) < 6:
                        continue
                    k = p[3]
                    if k not in bag[year]:
                        continue
                    exp = iso_map.get(p[1])
                    imp = iso_map.get(p[2])
                    if not exp or not imp or exp == imp:
                        continue
                    try:
                        usd = float(p[4]) * 1000.0
                    except ValueError:
                        continue
                    if usd <= 0:
                        continue
                    try:
                        tonnes = float(p[5]) if p[5].strip() not in ("", "NA", "nan") else 0.0
                    except ValueError:
                        tonnes = 0.0
                    cell = bag[year][k]
                    cell["exp_usd"][exp] += usd
                    cell["imp_usd"][imp] += usd
                    cell["usd"] += usd
                    cell["n"] += 1
                    if tonnes > 0:
                        cell["exp_t"][exp] += tonnes
                        cell["imp_t"][imp] += tonnes
                        cell["tonnes"] += tonnes
            print(f"  {year} done", flush=True)

    out = {
        "source": "UN Comtrade via CEPII BACI HS17 V202601",
        "years": YEARS,
        "note": (
            "Draft extraction on wip/silicon-chip-chain. "
            "Not added to the 32. Value = BACI v × 1000 USD. Quantity = metric tons."
        ),
        "codes": CODES,
        "years_data": {},
    }

    for year in YEARS:
        yout = {}
        for code, meta in CODES.items():
            cell = bag[year][code]
            usd = cell["usd"]
            tonnes = cell["tonnes"]
            exp_rows = topn(cell["exp_usd"], usd)
            imp_rows = topn(cell["imp_usd"], usd)
            # attach tonnes + unit value where we have quantity
            for row, src in ((exp_rows, cell["exp_t"]), (imp_rows, cell["imp_t"])):
                for r in row:
                    t = src.get(r["iso"], 0.0)
                    r["tonnes"] = round(t, 1)
                    r["usd_per_t"] = round(r["value_usd"] / t, 1) if t > 0 else None
                    r["name"] = names.get(r["iso"], r["iso"])
            yout[code] = {
                "label": meta["label"],
                "title": meta["title"],
                "flag": meta["flag"],
                "n_flows": cell["n"],
                "world_usd": round(usd),
                "world_tonnes": round(tonnes, 1),
                "world_usd_per_t": round(usd / tonnes, 1) if tonnes > 0 else None,
                "export_hhi": hhi([r["share"] for r in exp_rows] + (
                    # HHI on full exporter distribution, not just top 8
                    []
                )),
                "exporters": exp_rows,
                "importers": imp_rows,
            }
            # proper HHI over all exporters
            if usd > 0:
                yout[code]["export_hhi"] = hhi([v / usd for v in cell["exp_usd"].values()])
                yout[code]["import_hhi"] = hhi([v / usd for v in cell["imp_usd"].values()])
                yout[code]["china_export_share"] = round(cell["exp_usd"].get("CN", 0.0) / usd, 4)
            else:
                yout[code]["export_hhi"] = None
                yout[code]["import_hhi"] = None
                yout[code]["china_export_share"] = None
        out["years_data"][str(year)] = yout

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "silicon_stages.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("WROTE", path)
    return out


def preview(out):
    print("\n=== 2024 headline ===")
    y = out["years_data"]["2024"]
    for code, row in y.items():
        print(f"\n{code}  {row['title']}")
        print(f"  flag: {row['flag']}")
        print(f"  world ${row['world_usd']/1e9:.2f}B  {row['world_tonnes']/1e3:.1f} kt  "
              f"${row['world_usd_per_t']}/t  HHI={row['export_hhi']}  CN={row['china_export_share']}")
        print("  exporters:")
        for r in row["exporters"][:6]:
            print(f"    {r['iso']:3} {r['share']*100:5.1f}%  ${r['value_usd']/1e6:7.1f}M  "
                  f"{r['tonnes']/1e3:7.1f} kt  ${r['usd_per_t']}")
        print("  importers:")
        for r in row["importers"][:6]:
            print(f"    {r['iso']:3} {r['share']*100:5.1f}%  ${r['value_usd']/1e6:7.1f}M")


if __name__ == "__main__":
    preview(extract())
