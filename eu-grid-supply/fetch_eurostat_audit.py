"""Fetch a dated Eurostat cross-check for the frozen EU grid component baskets."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).resolve().parent / "eurostat_audit.json"
API = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/"
TRADE_INDICATORS = ("VALUE_IN_EUROS", "QUANTITY_IN_100KG")
PRODUCTION_INDICATORS = ("PRODVAL", "PVALFLAG", "PVALBASE", "PRODQNT", "QNTUNIT", "PQNTFLAG")


def eurostat(dataset, **filters):
    query = urlencode({
        "format": "JSON", "lang": "EN", "freq": "A", "reporter": "EU27_2020", **filters
    }, doseq=True)
    with urlopen(f"{API}{dataset}?{query}", timeout=45) as response:
        return json.load(response)


def observations(dataset):
    """Unpack the JSON-stat sparse index using the published dimension order."""
    dimensions = [
        {i: code for code, i in dataset["dimension"][dim]["category"]["index"].items()}
        for dim in dataset["id"]
    ]
    for index, value in dataset["value"].items():
        index = int(index)
        coordinates = []
        for size, labels in reversed(list(zip(dataset["size"], dimensions))):
            index, offset = divmod(index, size)
            coordinates.append(labels[offset])
        yield dict(zip(dataset["id"], reversed(coordinates))), value


def get_data(components):
    codes = {
        key: [code for code in row["cn8"] if code != "85044088"]
        for key, row in components.items()
    }
    trade = eurostat(
        "DS-045409", product=sorted(set().union(*map(set, codes.values()))),
        partner=("EXT_EU27_2020", "GB", "XI", "CN"), flow=("1", "2"),
        indicators=TRADE_INDICATORS, time="2024",
    )
    production = eurostat(
        "DS-059358", product=sorted({code for row in components.values() for code in row["prodcom"]}),
        indicators=PRODUCTION_INDICATORS, time="2024",
    )
    goes = eurostat(
        "DS-045409", product=codes["goes"], partner=("EXT_EU27_2020", "GB", "XI", "CN"),
        flow="1", indicators=TRADE_INDICATORS, time=tuple(range(2019, 2026)),
    )
    return codes, trade, production, goes


def trade_values(records):
    return {
        (row["product"], row["time"], row["flow"], row["indicators"], row["partner"]): value
        for row, value in observations(records)
    }


def trade_total(values, codes, year, flow, indicator, china=False):
    totals = []
    for code in codes:
        key = code, str(year), flow, indicator
        if china:
            totals.append(values.get((*key, "CN"), 0))
        else:
            total = values.get((*key, "EXT_EU27_2020"))
            if total is None:
                return None
            uk = sum(values.get((*key, country), 0) for country in ("GB", "XI"))
            totals.append(total - uk)
    return sum(totals)


def calculate(components, codes, trade, production, goes):
    values = trade_values(trade)
    production_by_code = {}
    for row, value in observations(production):
        production_by_code.setdefault(row["product"], {})[row["indicators"]] = value
    result = {}
    for key, row in components.items():
        pc = {code: production_by_code.get(code, {}) for code in row["prodcom"]}
        result[key] = {
            "cn8": codes[key],
            "production_by_prodcom": pc,
            "extra_eu_imports_eur_excluding_uk": trade_total(values, codes[key], 2024, "1", "VALUE_IN_EUROS"),
            "extra_eu_exports_eur_excluding_uk": trade_total(values, codes[key], 2024, "2", "VALUE_IN_EUROS"),
            "imports_from_china_eur": trade_total(values, codes[key], 2024, "1", "VALUE_IN_EUROS", china=True),
        }
    series = {}
    goes_values = trade_values(goes)
    for year in range(2019, 2026):
        series[year] = {
            key: {
                "all": trade_total(goes_values, codes["goes"], year, "1", indicator),
                "china": trade_total(goes_values, codes["goes"], year, "1", indicator, china=True),
            }
            for key, indicator in zip(("eur", "hundred_kg"), TRADE_INDICATORS)
        }
    base = result["goes"]
    base["extra_eu_imports_kg_excluding_uk"] = series[2024]["hundred_kg"]["all"] * 100
    base["imports_from_china_kg"] = series[2024]["hundred_kg"]["china"] * 100
    base["extra_eu_exports_kg_excluding_uk"] = trade_total(
        values, codes["goes"], 2024, "2", "QUANTITY_IN_100KG"
    ) * 100
    return result, series


def main():
    old = json.loads((ROOT / "out/eu_grid_supply.json").read_text(encoding="utf-8"))
    codes, trade, production, goes = get_data(old["components"])
    values, series = calculate(old["components"], codes, trade, production, goes)
    audit = {
        "published_components_source": "out/eu_grid_supply.json",
        "trade": {"dataset": "DS-045409", "updated": trade["updated"]},
        "sold_production": {"dataset": "DS-059358", "updated": production["updated"]},
        "boundary": (
            "EU27_2020. Extra-EU bloc totals minus GB and XI cells where separately reported. "
            "Positive China imports are gross. An absent partner cell contributes no published flow."
        ),
        "components_2024": values,
        "goes_imports": series,
    }
    OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
