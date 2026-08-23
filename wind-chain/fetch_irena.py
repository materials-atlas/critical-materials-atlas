"""Fetch official IRENA wind-capacity data from the PxWeb API.

The compact derived cache contains world totals and country onshore/offshore
capacity for 2000-2025. Run from repository root: python wind-chain/fetch_irena.py
"""
from __future__ import annotations

import itertools
import json
import os
import urllib.parse
import urllib.request
from collections import defaultdict


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "raw", "irena_wind_capacity_2000_2025.json")
BASE = "https://pxweb.irena.org/api/v1/en/IRENASTAT/Power%20Capacity%20and%20Generation/"
REGION = BASE + urllib.parse.quote("Region_ELECCAP_2026_H1_v-PX 1.px")
COUNTRY = BASE + urllib.parse.quote("Country_ELECCAP_2026_H1_v-PX 1.px")
AGGREGATE_CODES = {"GLO", "RAF", "RAS", "RCC", "REA", "RER", "RME", "RNA", "ROC", "RSA", "OCA"}


def post(url, query):
    body = json.dumps({"query": query, "response": {"format": "json-stat2"}}).encode()
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def selection(code, values=None):
    return {"code": code, "selection": {"filter": "all", "values": ["*"]}} if values is None else {"code": code, "selection": {"filter": "item", "values": values}}


def categories(dataset, dimension):
    category = dataset["dimension"][dimension]["category"]
    ordered = sorted(category["index"].items(), key=lambda item: item[1])
    return [(code, category["label"].get(code, code)) for code, _ in ordered]


def records(dataset):
    dims, sizes = dataset["id"], dataset["size"]
    cats = [categories(dataset, dim) for dim in dims]
    values = dataset["value"]
    for flat, value in enumerate(values):
        if value is None:
            continue
        coords, remainder = [], flat
        for size in reversed(sizes):
            coords.append(remainder % size)
            remainder //= size
        coords.reverse()
        yield {dim: cats[i][coords[i]] for i, dim in enumerate(dims)}, value


def fetch():
    region = post(REGION, [selection("Region", ["GLO"]), selection("Technology", ["2"]), selection("Grid connection"), selection("Year")])
    world = defaultdict(float)
    for labels, value in records(region):
        world[int(labels["Year"][1])] += value

    country = post(COUNTRY, [selection("Country/area"), selection("Technology", ["4", "5", "6"]), selection("Grid connection"), selection("Year")])
    bag = defaultdict(float)
    names = {}
    tech_names = {}
    for labels, value in records(country):
        iso, name = labels["Country/area"]
        if iso in AGGREGATE_CODES:
            continue
        tech, tech_name = labels["Technology"]
        year = int(labels["Year"][1])
        bag[(iso, tech, year)] += value
        names[iso] = name
        tech_names[tech] = tech_name
    rows = [{"iso3": iso, "country": names[iso], "technology": tech_names[tech], "year": year, "capacity_mw": round(value, 2)}
            for (iso, tech, year), value in sorted(bag.items()) if value > 0]
    output = {
        "source": region["source"], "source_url": REGION, "retrieved": "2026-08-17",
        "unit": "MW, maximum net generating capacity at year end",
        "world_wind": [{"year": year, "capacity_mw": round(world[year], 2)} for year in sorted(world)],
        "country_rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("WROTE", OUT, len(rows), "country/technology/year records")
    print("World wind", output["world_wind"][0], "->", output["world_wind"][-1])


if __name__ == "__main__":
    fetch()
