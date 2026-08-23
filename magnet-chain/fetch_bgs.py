"""Fetch the compact BGS rare-earth-oxide production panel used by the pilot.

The official OGC API currently exposes country observations for 1992-2024.
The saved file is deliberately small and preserves the source notes verbatim.

Run from the repository root: python magnet-chain/fetch_bgs.py
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "raw", "bgs_rare_earth_oxides_1992_2024.json")
BASE = "https://ogcapi.bgs.ac.uk/collections/world-mineral-statistics/items"
FILTER = 'erml_group = "Rare earths" AND bgs_statistic_type_trans = "Production"'


def fetch():
    url = BASE + "?" + urllib.parse.urlencode(
        {"f": "json", "limit": 2000, "sortby": "year", "filter": FILTER}
    )
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = json.load(response)
    if payload.get("numberMatched") != 274:
        raise SystemExit(f"Unexpected BGS record count: {payload.get('numberMatched')}")

    keep = [
        "year", "country_trans", "country_iso2_code", "country_iso3_code",
        "quantity", "units", "sdmx_code", "sdmx_translation",
    ]
    rows = [{key: feature["properties"].get(key) for key in keep}
            for feature in payload["features"]]
    years = sorted({int(row["year"][:4]) for row in rows})
    if years[0] != 1992 or years[-1] != 2024:
        raise SystemExit(f"Unexpected BGS coverage: {years[0]}-{years[-1]}")

    properties = [feature["properties"] for feature in payload["features"]]
    props = next(item for item in properties if item.get("concat_table_notes_text"))
    out = {
        "source": "British Geological Survey, World Mineral Statistics OGC API",
        "source_url": BASE,
        "retrieved": "2026-08-17",
        "filter": FILTER,
        "measure": "Mine production reported or calculated as rare-earth-oxide equivalent",
        "units": props["units"],
        "source_notes": props["concat_table_notes_text"].split("|"),
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("WROTE", OUT, len(rows), "records")


if __name__ == "__main__":
    fetch()
