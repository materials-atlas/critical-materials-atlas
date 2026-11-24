"""Refresh the EV study's standalone Eurostat Comext evidence."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


OUT = Path(__file__).with_name("out") / "comext_audit.json"
API = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409"
CODES = {
    "87038010": "New battery-electric cars",
    "87038090": "Used battery-electric cars",
    "87036010": "New petrol plug-in hybrid cars",
    "87036090": "Used petrol plug-in hybrid cars",
}
YEARS = ("2024", "2025")
MONTHS = tuple(f"2025-{month:02d}" for month in range(1, 13))
PARTNERS = ("CN", "EXT_EU27_2020")
INDICATORS = ("SUPPLEMENTARY_QUANTITY", "VALUE_IN_EUROS")


def fetch(freq, products, partners, indicators, periods):
    query = urlencode({
        "format": "JSON", "lang": "EN", "freq": freq,
        "reporter": "EU27_2020", "flow": "1", "product": products,
        "partner": partners, "indicators": indicators, "time": periods,
    }, doseq=True)
    url = f"{API}?{query}"
    with urlopen(url, timeout=45) as response:
        dataset = json.load(response)
    return url, dataset


def decode_cells(dataset, dimensions_to_keep):
    """Decode sparse Eurostat observations on the requested dimensions."""
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
        key = tuple(row[dim] for dim in dimensions_to_keep)
        cells[key] = {"value": value, "status": flags.get(position) or None}
    return cells


def observations(dataset):
    """Return the published Comext cells and observation flags."""
    return decode_cells(dataset, ("time", "product", "partner", "indicators"))


def snapshot():
    annual_url, annual = fetch("A", tuple(CODES), PARTNERS, INDICATORS, YEARS)
    monthly_url, monthly = fetch("M", ("87038010", "87036010"), ("CN",), INDICATORS[:1], MONTHS)
    annual_cells, monthly_cells = observations(annual), observations(monthly)
    # Index each required key directly so a missing cell stops the refresh.
    return {
        "dataset": "Eurostat Comext DS-045409",
        "reporter": "EU27_2020",
        "flow": "1 (imports)",
        "unit": {"SUPPLEMENTARY_QUANTITY": "vehicles", "VALUE_IN_EUROS": "nominal euros"},
        "products": CODES,
        "annual": {
            "query": annual_url,
            "updated": annual["updated"],
            "rows": {
                year: {
                    code: {
                        partner: {
                            indicator: annual_cells[year, code, partner, indicator]
                            for indicator in INDICATORS
                        } for partner in PARTNERS
                    } for code in CODES
                } for year in YEARS
            },
        },
        "monthly": {
            "query": monthly_url,
            "updated": monthly["updated"],
            "rows": {
                month: {
                    code: monthly_cells[month, code, "CN", "SUPPLEMENTARY_QUANTITY"]
                    for code in ("87038010", "87036010")
                } for month in MONTHS
            },
        },
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(snapshot(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote", OUT.name)
