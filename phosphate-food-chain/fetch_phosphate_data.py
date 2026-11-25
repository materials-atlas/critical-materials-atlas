"""Snapshot annual EU phosphate imports and FAOSTAT nutrient balances."""
from decimal import Decimal
from io import BytesIO, TextIOWrapper
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
YEARS = ("2023", "2024")
COMEXT = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409"
FAOSTAT = "https://bulks-faostat.fao.org/production/Inputs_FertilizersNutrient_E_All_Data_(Normalized).zip"
EU = set("AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE".split())
EXTRA = "EXT_EU27_2020"
UNNAMED_EXTRA = set("QP QQ QS QU QW QX QZ".split())
UNNAMED_INTRA = {"QR", "QV", "QY"}
MEASURES = {"QUANTITY_IN_100KG": ("mass_kg", 100), "VALUE_IN_EUROS": ("eur", 1)}
FAO_ELEMENTS = {
    "5707": {"5510", "5157"},
    "57070": {"5610", "5910"},
    "5000": {"5157"},
}


def fetch_comext():
    with (HERE / "products.csv").open(encoding="utf-8", newline="") as f:
        codes = [row["cn8"] for row in csv.DictReader(f)]
    query = urlencode({"format": "JSON", "lang": "EN", "freq": "A", "reporter": "EU27_2020",
                       "flow": "1", "product": codes, "indicators": tuple(MEASURES), "time": YEARS}, doseq=True)
    url = f"{COMEXT}?{query}"
    with urlopen(url, timeout=60) as response:
        data = json.load(response, parse_float=Decimal)
    dimensions = [
        {index: code for code, index in data["dimension"][dim]["category"]["index"].items()} for dim in data["id"]
    ]
    cells = {}
    for position, value in data["value"].items():
        index = int(position)
        coordinates = []
        for size, lookup in reversed(list(zip(data["size"], dimensions))):
            index, offset = divmod(index, size)
            coordinates.append(lookup[offset])
        row = dict(zip(data["id"], reversed(coordinates)))
        code, year, partner = (row[dim] for dim in ("product", "time", "partner"))
        if partner != EXTRA and (len(partner) != 2 or partner in EU or partner in UNNAMED_INTRA):
            continue
        measure, factor = MEASURES[row["indicators"]]
        converted = value * factor
        if converted < 0 or int(converted) != converted:
            raise ValueError(f"Unusable observation at {year}/{code}/{partner}/{measure}: {converted}")
        cell = cells.setdefault((year, code, partner), {})
        cell[measure] = int(converted)
        cell[f"{measure}_flag"] = data.get("status", {}).get(position)
    partner_labels = data["dimension"]["partner"]["category"]["label"]
    return {
        "dataset": "Eurostat Comext DS-045409", "updated": data["updated"], "query": url,
        "reporter": "EU27_2020", "flow": "imports", "frequency": "annual",
        "products": data["dimension"]["product"]["category"]["label"],
        "partners": {p: partner_labels[p] for p in sorted({key[2] for key in cells})},
        "rows": [
            {"year": int(year), "cn8": code, "origin": partner,
             "kind": "total" if partner == EXTRA else "unnamed" if partner in UNNAMED_EXTRA else "named", **cell}
            for (year, code, partner), cell in sorted(cells.items())
        ],
    }


def fetch_faostat():
    with urlopen(FAOSTAT, timeout=60) as response:
        payload = response.read()
        modified = response.headers["Last-Modified"]
    expected = {(int(y), a, e) for y in YEARS for a, elements in FAO_ELEMENTS.items() for e in elements}
    rows = []
    with ZipFile(BytesIO(payload)) as z:
        member = next(n for n in z.namelist() if n.endswith("(Normalized).csv"))
        with z.open(member) as f:
            for row in csv.DictReader(TextIOWrapper(f, encoding="latin-1")):
                if row["Year"] not in YEARS or row["Item Code"] != "3103":
                    continue
                key = int(row["Year"]), row["Area Code"], row["Element Code"]
                if key in expected and row["Unit"] == "t":
                    rows.append({"year": key[0], "area_code": key[1], "element_code": key[2], "area": row["Area"],
                                 "element": row["Element"], "p2o5_t": float(row["Value"]),
                                 "flag": row["Flag"], "note": row["Note"]})
    if len(rows) != len(expected) or {(r["year"], r["area_code"], r["element_code"]) for r in rows} != expected:
        raise ValueError("FAOSTAT snapshot is incomplete.")
    return {"dataset": "FAOSTAT RFN", "query": FAOSTAT, "last_modified": modified,
            "source_sha256": hashlib.sha256(payload).hexdigest(),
            "rows": sorted(rows, key=lambda r: (r["year"], r["area_code"], r["element_code"]))}


def main():
    snapshots = {"phosphate_comext.json": fetch_comext(), "phosphate_faostat.json": fetch_faostat()}
    for filename, data in snapshots.items():
        (OUT / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(filename, len(data["rows"]), "observations")


if __name__ == "__main__":
    main()
