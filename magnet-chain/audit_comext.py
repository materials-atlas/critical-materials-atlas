"""Refresh the magnet study's standalone Eurostat Comext evidence."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


OUT = Path(__file__).with_name("out") / "comext_audit.json"
API = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409"
CODE = "85051110"
YEARS = ("2023", "2024", "2025")
MONTHS = tuple(f"{year}-{month:02d}" for year in (2024, 2025) for month in range(1, 13))
PARTNERS = ("CN", "EXT_EU27_2020")
INDICATORS = ("QUANTITY_IN_100KG", "VALUE_IN_EUROS")


def fetch(freq, periods):
    query = urlencode({
        "format": "JSON", "lang": "EN", "freq": freq,
        "reporter": "EU27_2020", "flow": "1", "product": CODE,
        "partner": PARTNERS, "indicators": INDICATORS, "time": periods,
    }, doseq=True)
    url = f"{API}?{query}"
    with urlopen(url, timeout=45) as response:
        dataset = json.load(response)
    return url, dataset


def observations(dataset):
    """Return the published cells, preserving any Eurostat observation flags."""
    sizes = dataset["size"]
    dimensions = [
        {index: code for code, index in dataset["dimension"][dim]["category"]["index"].items()}
        for dim in dataset["id"]
    ]
    flags = dataset.get("status", {})
    cells = {}
    for position, value in dataset["value"].items():
        index = int(position)
        coordinates = []
        for size, labels in reversed(list(zip(sizes, dimensions))):
            index, offset = divmod(index, size)
            coordinates.append(labels[offset])
        row = dict(zip(dataset["id"], reversed(coordinates)))
        key = tuple(row[dim] for dim in ("time", "partner", "indicators"))
        cells[key] = {"value": value, "status": flags.get(position) or None}
    return cells


def period_data(freq, periods):
    url, dataset = fetch(freq, periods)
    cells = observations(dataset)
    # Require every requested observation. Missing values never become zeros.
    return {
        "query": url, "updated": dataset["updated"],
        "rows": {
            period: {
                partner: {indicator: cells[period, partner, indicator] for indicator in INDICATORS}
                for partner in PARTNERS
            } for period in periods
        },
    }, dataset["dimension"]["product"]["category"]["label"][CODE]


def snapshot():
    annual, label = period_data("A", YEARS)
    monthly, monthly_label = period_data("M", MONTHS)
    if label != monthly_label:
        raise ValueError("Product coverage differs across frequencies")
    return {
        "dataset": "Eurostat Comext DS-045409",
        "reporter": "EU27_2020",
        "product": CODE,
        "product_label": label,
        "flow": "1 (imports)",
        "units": {"QUANTITY_IN_100KG": "100 kg net mass", "VALUE_IN_EUROS": "nominal euros"},
        "annual": annual,
        "monthly": monthly,
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(snapshot(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote", OUT.name)
