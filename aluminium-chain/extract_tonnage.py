"""Tonnage view of aluminium-chain trade, from the local BACI extract.

extract_baci.py gives shares by value for the page's trade table. This script gives the same trade by
weight, stage by stage, because the study compares tonnes traded with tonnes produced. It also follows
Guinea's bauxite exports, China's bauxite imports and Indonesia's exports through the years.

Reads BACI only through baci.py. No network access. Run from the repository root:
    python aluminium-chain/extract_tonnage.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import baci  # noqa: E402  the one door for BACI

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "aluminium_tonnage.json")
YEARS = list(range(2002, 2025))
STAGES = {
    "bauxite": {"label": "Bauxite", "codes": ["260600"]},
    "alumina": {"label": "Alumina", "codes": ["281820"]},
    "unwrought": {"label": "Unwrought aluminium", "codes": ["760110", "760120"]},
    "semis": {"label": "Semi-finished aluminium (bars, wire, plate, foil, tubes)",
              "codes": ["760410", "760421", "760429", "760511", "760519", "760521", "760529", "760611", "760612",
                        "760691", "760692", "760711", "760719", "760720", "760810", "760820"]},
}
GUINEA, CHINA, INDONESIA = 324, 156, 360
PLAIN = {"Russian Federation": "Russia", "USA": "United States", "Rep. of Korea": "South Korea",
         "Lao People's Dem. Rep.": "Laos", "Türkiye": "Turkey", "Viet Nam": "Vietnam"}


def main():
    names = {int(r.code): PLAIN.get(r.name, r.name) for r in baci.countries().itertuples()}
    all_codes = [c for s in STAGES.values() for c in s["codes"]]
    out = {"source": "CEPII BACI V202601, based on UN Comtrade", "unit": "tonnes (customs net weight)",
           "nomenclature": {str(y): baci.nomenclature(y) for y in YEARS},
           "stages": {k: {"label": v["label"], "codes": v["codes"]} for k, v in STAGES.items()},
           "series": {k: [] for k in STAGES}, "latest": {}}
    for year in YEARS:
        df = baci.year(year, codes=all_codes)
        for key, stage in STAGES.items():
            d = df[df["k"].isin(stage["codes"])]
            total = float(d["q"].sum())
            ex = d.groupby("i")["q"].sum().sort_values(ascending=False)
            im = d.groupby("j")["q"].sum().sort_values(ascending=False)
            rec = {
                "year": year, "world_tonnes": round(total), "n_flows": int(len(d)),
                "flows_without_weight": round(float(d["q"].isna().mean()), 4),
                "export_hhi": round(float(((ex / total) ** 2).sum()) * 10000),
                "import_hhi": round(float(((im / total) ** 2).sum()) * 10000),
                "leading_exporter": names[int(ex.index[0])], "leading_exporter_share": round(float(ex.iloc[0] / total), 4),
                "china_exports": round(float(ex.get(CHINA, 0.0))), "china_imports": round(float(im.get(CHINA, 0.0))),
                "guinea_exports": round(float(ex.get(GUINEA, 0.0))), "indonesia_exports": round(float(ex.get(INDONESIA, 0.0))),
            }
            if key == "bauxite":
                rec["guinea_to_china"] = round(float(d[(d["i"] == GUINEA) & (d["j"] == CHINA)]["q"].sum()))
            out["series"][key].append(rec)
            if year == YEARS[-1]:
                out["latest"][key] = {
                    "year": year,
                    "exporters": [{"name": names[int(k)], "tonnes": round(float(v)), "share": round(float(v / total), 4)}
                                  for k, v in ex.head(8).items()],
                    "importers": [{"name": names[int(k)], "tonnes": round(float(v)), "share": round(float(v / total), 4)}
                                  for k, v in im.head(6).items()],
                }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    last = {k: v[-1] for k, v in out["series"].items()}
    print("wrote aluminium_tonnage.json:", ", ".join(
        "%s %.1f Mt (%s %.0f%%)" % (k, r["world_tonnes"] / 1e6, r["leading_exporter"], 100 * r["leading_exporter_share"])
        for k, r in last.items()))


if __name__ == "__main__":
    main()
