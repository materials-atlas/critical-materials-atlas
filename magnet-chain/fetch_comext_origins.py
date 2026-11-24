"""Refresh the magnet study's annual Comext import mass by declared origin."""

from decimal import Decimal
import json
from pathlib import Path

from fetch_comext_audit import CODE, YEARS, fetch, observations


OUT = Path(__file__).with_name("out") / "comext_origins.json"
MASS = "QUANTITY_IN_100KG"
EXTRA_EU = "EXT_EU27_2020"
EU = set("AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE".split())
UNNAMED = set("QP QQ QS QU QW QX QZ".split())
INTRA_SPECIAL = {"QR", "QV", "QY"}


def kilograms(cell):
    value = Decimal(str(cell["value"])) * 100
    if value < 0 or value != value.to_integral_value():
        raise ValueError(f"Unexpected net mass in {cell}")
    return {"kg": int(value), "status": cell["status"]}


def snapshot():
    url, dataset = fetch("A", YEARS, partners=(), indicators=(MASS,))
    labels = dataset["dimension"]["partner"]["category"]["label"]
    cells = observations(dataset)
    years = {}
    used_codes = {EXTRA_EU}
    for year in YEARS:
        total = kilograms(cells[year, EXTRA_EU, MASS])
        named = {}
        unnamed = {}
        for (period, partner, indicator), cell in sorted(cells.items()):
            if period != year or indicator != MASS:
                continue
            # Aggregate partners have longer codes. Keep individual Comext
            # countries and territories, plus the extra-EU residual codes.
            if len(partner) != 2 or partner in EU or partner in INTRA_SPECIAL:
                continue
            group = unnamed if partner in UNNAMED else named
            group[partner] = kilograms(cell)
        if sum(row["kg"] for row in (*named.values(), *unnamed.values())) != total["kg"]:
            raise ValueError(f"Partner mass does not reconcile to the extra-EU total for {year}")
        if "CN" not in named:
            raise ValueError(f"China-origin mass is missing for {year}")
        used_codes.update(named)
        used_codes.update(unnamed)
        years[year] = {"total": total, "named": named, "unnamed": unnamed}
    return {
        "dataset": "Eurostat Comext DS-045409",
        "updated": dataset["updated"],
        "query": url,
        "reporter": "EU27_2020",
        "product": CODE,
        "unit": "kg net mass",
        "source_unit": "100 kg net mass",
        "classification": "2026 Eurostat Geonomenclature",
        "partners": {code: labels[code] for code in sorted(used_codes)},
        "years": years,
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(snapshot(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote", OUT.name)
