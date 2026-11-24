"""Download EV customs history, monthly checks and registration context from Eurostat."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from fetch_comext_audit import INDICATORS, PARTNERS, YEARS, decode_cells, fetch, observations


OUT = Path(__file__).with_name("out") / "ev_import_context.json"
MOTOR_ENERGY = {"87038010": "ELC", "87036010": "ELC_PET_PI"}
CODES = tuple(MOTOR_ENERGY)
HISTORY = tuple(str(year) for year in range(1988, 2026))
MONTHS = tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1, 13))
UNITS = INDICATORS[:1]


def customs(freq, periods):
    url, data = fetch(freq, CODES, PARTNERS, UNITS, periods)
    cells = observations(data)
    rows = {}
    for period in periods:
        keys = [(period, code, partner, UNITS[0]) for code in CODES for partner in PARTNERS]
        if freq == "A" and all(key not in cells for key in keys):
            continue
        rows[period] = {
            code: {partner: cells[period, code, partner, UNITS[0]] for partner in PARTNERS}
            for code in CODES
        }
    labels = data["dimension"]["product"]["category"]["label"]
    return {"query": url, "updated": data["updated"], "rows": rows, "labels": labels}


def registrations():
    table = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/road_eqr_carpda"
    parameters = {"format": "JSON", "lang": "EN", "freq": "A", "unit": "NR",
                  "geo": "EU27_2020", "mot_nrg": tuple(MOTOR_ENERGY.values()), "time": YEARS}
    url = f"{table}?{urlencode(parameters, doseq=True)}"
    with urlopen(url, timeout=45) as response:
        data = json.load(response)
    cells = decode_cells(data, ("time", "mot_nrg"))
    return {
        "dataset": "Eurostat road_eqr_carpda, new passenger cars by type of motor energy",
        "query": url,
        "updated": data["updated"],
        "energy_labels": data["dimension"]["mot_nrg"]["category"]["label"],
        "rows": {year: {code: cells[year, energy] for code, energy in MOTOR_ENERGY.items()}
                 for year in YEARS},
    }


def snapshot():
    annual = customs("A", HISTORY)
    monthly = customs("M", MONTHS)
    if annual["labels"] != monthly["labels"] or annual["updated"] != monthly["updated"]:
        raise ValueError("Comext annual and monthly responses use different definitions or vintages")
    if tuple(annual["rows"]) != tuple(str(y) for y in range(2017, 2026)):
        raise ValueError("Comparable year coverage changed. Review before publishing.")
    return {
        "customs": {"dataset": "Eurostat Comext DS-045409", "reporter": "EU27_2020",
                    "flow": "imports", "unit": "vehicles", "requested_annual_years": [1988, 2025],
                    "annual": annual, "monthly": monthly},
        "registrations": registrations(),
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(snapshot(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote", OUT.name)
