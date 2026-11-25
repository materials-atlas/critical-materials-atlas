"""Where each large importer buys its ferroalloys, from the local BACI extract.

extract_baci.py gives world exporter shares by value for the page's trade table. This script gives, by weight,
the world exporter shares of each ferroalloy and the supplier shares seen by six importing markets, so that a
world concentration figure can be set beside an importer's own exposure. The EU is treated as one market:
trade between member states is left out and imports are those from outside the EU.

Reads BACI only through baci.py. No network access. Run from the repository root:
    python steel-alloys-chain/extract_exposure.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import baci  # noqa: E402  the one door for BACI

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "steel_exposure.json")
YEARS = (2019, 2022, 2023, 2024)
PRODUCTS = {
    "ferroniobium": {"label": "Ferroniobium", "codes": ["720293"]},
    "ferrovanadium": {"label": "Ferrovanadium", "codes": ["720292"]},
    "ferrochromium": {"label": "Ferrochromium", "codes": ["720241", "720249"]},
    "ferromanganese": {"label": "Ferromanganese and ferrosilicomanganese", "codes": ["720211", "720219", "720230"]},
    "ferronickel": {"label": "Ferronickel", "codes": ["720260"]},
    "ferromolybdenum": {"label": "Ferromolybdenum", "codes": ["720270"]},
    "chromium_ore": {"label": "Chromium ores and concentrates", "codes": ["261000"]},
    "manganese_ore": {"label": "Manganese ores and concentrates", "codes": ["260200"]},
}
EU27 = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL",
        "PT", "RO", "SK", "SI", "ES", "SE"]
MARKETS = {"United States": ["US"], "European Union": EU27, "Japan": ["JP"], "South Korea": ["KR"], "India": ["IN"], "China": ["CN"]}
PLAIN = {"Russian Federation": "Russia", "USA": "United States", "Rep. of Korea": "South Korea", "Türkiye": "Turkey", "Viet Nam": "Vietnam",
         "China, Hong Kong SAR": "Hong Kong"}


def shares(series, n=5):
    total = float(series.sum())
    top = series.sort_values(ascending=False)
    return {"tonnes": round(total), "hhi": round(float(((top / total) ** 2).sum()) * 10000) if total else None,
            "top": [{"name": k, "share": round(float(v / total), 4)} for k, v in top.head(n).items()] if total else []}


def main():
    frame = baci.countries()
    names = {int(r.code): PLAIN.get(r.name, r.name) for r in frame.itertuples()}
    iso2 = {int(r.code): r.iso2 for r in frame.itertuples()}
    codes = [c for p in PRODUCTS.values() for c in p["codes"]]
    out = {"source": "CEPII BACI V202601, based on UN Comtrade", "unit": "tonnes (customs net weight)", "years": list(YEARS),
           "products": {k: {"label": v["label"], "codes": v["codes"]} for k, v in PRODUCTS.items()},
           "markets": {k: ("EU27, imports from outside the EU" if k == "European Union" else "national imports") for k in MARKETS},
           "by_year": {}}
    for year in YEARS:
        df = baci.year(year, codes=codes)
        df = df.assign(exporter=df["i"].map(names), ei=df["i"].map(iso2), ji=df["j"].map(iso2))
        res = {}
        for key, product in PRODUCTS.items():
            d = df[df["k"].isin(product["codes"])]
            world = shares(d.groupby("exporter")["q"].sum(), n=6)
            world["flows_without_weight"] = round(float(d["q"].isna().mean()), 4)
            leader = world["top"][0]["name"] if world["top"] else None
            markets = {}
            for market, members in MARKETS.items():
                m = d[d["ji"].isin(members) & ~d["ei"].isin(members)]
                rec = shares(m.groupby("exporter")["q"].sum())
                by = m.groupby("exporter")["q"].sum()
                rec["share_from_world_leader"] = round(float(by.get(leader, 0.0) / by.sum()), 4) if by.sum() else None
                markets[market] = rec
            res[key] = {"world": world, "world_leader": leader, "markets": markets}
        out["by_year"][str(year)] = res
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    last = out["by_year"][str(YEARS[-1])]
    print("wrote steel_exposure.json:", "; ".join(
        "%s %s %.0f%%" % (k, v["world_leader"], 100 * v["world"]["top"][0]["share"]) for k, v in last.items()))


if __name__ == "__main__":
    main()
