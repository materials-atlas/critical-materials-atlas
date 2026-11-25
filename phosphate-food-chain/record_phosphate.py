"""Rebuild the phosphate research note from pinned public inputs."""
from collections import Counter
import csv
from html import escape
import json
from pathlib import Path
from string import Template

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
DATE = "2026-11-25"
TITLE = "Phosphate reserves and fertilizer supply"
DECK = "Morocco leads in reported phosphate-rock reserves. China leads in mining. Import dependence varies by fertilizer and market."
YEAR = "2024"
GROUPS = ("Rock", "Acid", "DAP", "MAP and mixes", "Superphosphates", "Other finished")
P_IN_P2O5 = 2 * 30.973761998 / (2 * 30.973761998 + 5 * 15.999)
SOURCES = {
    "usgs": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-phosphate.pdf",
    "usgs_geography": "https://pubs.usgs.gov/myb/vol3/2019/myb3-2019-morocco-western-sahara.pdf",
    "baci": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37",
    "comext": "https://ec.europa.eu/eurostat/databrowser/view/DS-045409/default/table?lang=en",
    "faostat": "https://www.fao.org/faostat/en/#data/RFN",
    "faostat_method": "https://files-faostat.fao.org/production/RFN/RFN_EN_README.pdf",
    "hs2017": "https://unstats.un.org/unsd/trade/events/2017/suzhou/presentations/Agenda%20item%2017%20%28a%29%20-%20WCO.pdf",
    "dap_grade": "https://www.cropnutrition.com/resource-library/diammonium-phosphate-dap-data-sheet/",
    "map_grade": "https://www.cropnutrition.com/resource-library/monoammonium-phosphate-map/",
    "hirner": "https://doi.org/10.1016/j.resourpol.2026.106064",
    "raddant": "https://doi.org/10.3390/resources14100151",
    "barbieri": "https://doi.org/10.1038/s41893-021-00816-1",
}
LEGACY_BOUNDS = {
    "251010": "Unground natural phosphates. Ground material is under 251020.",
    "310530": "DAP. The series measures trade value.",
    "310540": "MAP and specified MAP–DAP mixtures. Grades vary.",
    "310420": "Potassium chloride. Comparator for potassium.",
    "280470": "Elemental phosphorus. Separate industrial product.",
}


def read_json(filename):
    return json.loads((OUT / filename).read_text(encoding="utf-8"))


def read_csv(filename):
    with (HERE / filename).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def concentration(masses, total):
    """HHI in points. Assign the unresolved mass to the top origin for the upper bound."""
    residual = total - sum(masses)
    if residual < 0:
        raise ValueError("Named flows exceed the reported total.")
    if total == 0:
        return [None, None]
    squares = sum(mass**2 for mass in masses)
    top = max(masses, default=0)
    scale = 10000 / total**2
    return [squares * scale, (squares + 2 * top * residual + residual**2) * scale]


def upstream():
    rows = [{k: int(v) if k.endswith("_kt") else v for k, v in r.items()} for r in read_csv("usgs_2025.csv")]
    world = next(r for r in rows if r["kind"] == "total")
    countries = [r for r in rows if r["kind"] == "named"]
    other = next(r for r in rows if r["kind"] == "other")
    fields = ("reserves_kt", "production_2025_kt")
    values = {}
    for field in fields:
        named = [r[field] for r in countries]
        summed = sum(named) + other[field]
        hhi = sum((v / summed)**2 for v in named) * 10000
        values[field] = {
            "published_total_kt": world[field], "row_total_kt": summed, "other_kt": other[field],
            "hhi_points": [hhi, hhi + (other[field] / summed)**2 * 10000],
        }
    for r in countries:
        for field in fields:
            r[field.removesuffix("_kt") + "_share"] = r[field] / world[field]
    return {"rows": rows, "summary": values}


def group_eu_imports(data, products):
    lookup = {row["cn8"]: row["group"] for row in products}
    all_years = {}
    for year in sorted({str(r["year"]) for r in data["rows"]}):
        by_code = {code: [] for code in lookup}
        for row in data["rows"]:
            if str(row["year"]) == year:
                by_code[row["cn8"]].append(row)
        result = {}
        for group in GROUPS:
            named_kg = Counter()
            total_kg = 0
            total_eur = 0
            residual_codes = Counter()
            for code, rows in by_code.items():
                if lookup[code] != group:
                    continue
                total = next(row for row in rows if row["kind"] == "total")
                details = [r for r in rows if r["kind"] != "total"]
                for field in ("mass_kg", "eur"):
                    if total[field] != sum(row.get(field, 0) for row in details):
                        raise ValueError(f"Comext {field} did not reconcile for {year}/{code}.")
                total_kg += total["mass_kg"]
                total_eur += total["eur"]
                for row in details:
                    if "mass_kg" in row:
                        bucket = named_kg if row["kind"] == "named" else residual_codes
                        bucket[row["origin"]] += row["mass_kg"]
            origin_kg = dict(named_kg.most_common())
            result[group] = {
                "total_kg": total_kg, "total_eur": total_eur, "named_kg": origin_kg,
                "unnamed_kg": dict(residual_codes),
                "hhi_points": concentration(list(origin_kg.values()), total_kg),
            }
        all_years[year] = result
    return all_years


def nutrient_balance(snapshot):
    categories = {"production_t": ("5707", "5510"), "agricultural_use_t": ("5707", "5157"),
                  "imports_t": ("57070", "5610"), "exports_t": ("57070", "5910"),
                  "world_agricultural_use_t": ("5000", "5157")}
    years = {}
    for year in sorted({str(r["year"]) for r in snapshot["rows"]}):
        values = {(r["area_code"], r["element_code"]): r["p2o5_t"]
                  for r in snapshot["rows"] if str(r["year"]) == year}
        row = {key: values[code] for key, code in categories.items()}
        row["net_imports_t"] = row["imports_t"] - row["exports_t"]
        row["apparent_supply_t"] = row["production_t"] + row["net_imports_t"]
        row["supply_less_agricultural_use_t"] = row["apparent_supply_t"] - row["agricultural_use_t"]
        row["net_import_share_of_apparent_supply"] = (
            row["net_imports_t"] / row["apparent_supply_t"] if row["apparent_supply_t"] > 0 else None
        )
        years[year] = row
    return years


def grade_illustration(groups, products):
    nominal = {r["group"]: float(r["nominal_p2o5_fraction"]) for r in products if r["nominal_p2o5_fraction"]}
    return [
        {"dap_fraction": nominal["DAP"], "map_mix_fraction": fraction,
         "elemental_p_t": (groups["DAP"]["total_kg"] * nominal["DAP"]
                           + groups["MAP and mixes"]["total_kg"] * fraction) / 1000 * P_IN_P2O5}
        for fraction in (nominal["DAP"], nominal["MAP and mixes"])
    ]


def stress_test(dap):
    # Keep the experiment within one customs product and one year of reported imports.
    origin, origin_kg = next(iter(dap["named_kg"].items()))
    lost = origin_kg / 2
    return {
        "year": int(YEAR), "origin": origin, "lost_fraction_of_origin": .5,
        "baseline_kg": dap["total_kg"], "lost_kg": lost,
        "rows": [{"replacement_fraction": r, "remaining_gap_kg": lost * (1 - r),
                  "gap_share_of_baseline_imports": lost * (1 - r) / dap["total_kg"]} for r in (0, .5, 1)],
    }


def build_evidence():
    comext, faostat = read_json("phosphate_comext.json"), read_json("phosphate_faostat.json")
    products = read_csv("products.csv")
    eu = group_eu_imports(comext, products)
    legacy = read_json("phosphate_trade.json")
    latest = str(legacy["years"][-1])
    return {
        "title": TITLE, "h1": TITLE, "deck": DECK, "published": True, "version": DATE,
        "chokepoint": {
            "product": "Phosphate fertilizer", "stage": "Reserve concentration",
            "mechanism": "geological", "physics": "Reserves, mine output and fertilizer origins differ. The binding stage remains untested.",
            "holder": "Morocco (USGS reserves)", "share": "68.5% of reserves; binding stage not established", "control": "—",
            "conf": "snapshot", "research": True,
        },
        "sources": SOURCES, "upstream": upstream(),
        "comext_partners": comext["partners"], "eu_imports": eu,
        "p_fraction_in_p2o5": P_IN_P2O5,
        "grade_illustration_2024": grade_illustration(eu[YEAR], products),
        "faostat_balance": nutrient_balance(faostat),
        "stress_test": stress_test(eu[YEAR]["DAP"]),
        "baci_legacy": {"year": int(latest), "products": legacy["years_data"][latest]},
    }


def tr(head, *cells, attrs=""):
    return (f"<tr{attrs}><th scope=\"row\">{escape(str(head))}</th>"
            + "".join(f"<td>{escape(str(cell))}</td>" for cell in cells) + "</tr>")


def hhi_label(bounds):
    low, high = (round(n) for n in bounds)
    return f"{low:,}" if low == high else f"{low:,} to {high:,}"


def tonnes(kg):
    return f"{kg / 1000:,.0f}"


def render(data, trade):
    all_eu = data["eu_imports"]
    eu = all_eu[YEAR]
    usgs = data["upstream"]
    places = {row["country"]: row for row in usgs["rows"] if row["kind"] == "named"}
    fao = data["faostat_balance"]
    scenario = data["stress_test"]
    partner = data["comext_partners"]
    morocco = places["Morocco"]
    china = places["China"]
    dap = eu["DAP"]
    trade_rows = []
    for code, row in data["baci_legacy"]["products"].items():
        lead = row["exporters"][0]
        trade_rows.append(tr(f"{trade['codes'][code]['title']} ({code})",
                             f"USD {row['world_usd'] / 1e6:,.1f}m", f"{lead['name']} · {lead['share']:.1%}",
                             LEGACY_BOUNDS[code], attrs=f' data-trade-code="{code}"'))
    values = {
        "title": TITLE, "deck": DECK, "date": DATE, **data["sources"],
        "ma_reserve": f"{morocco['reserves_share']:.1%}", "ma_mine": f"{morocco['production_2025_share']:.1%}",
        "cn_mine": f"{china['production_2025_share']:.1%}", "cn_reserve": f"{china['reserves_share']:.1%}",
        "ma_dap": f"{dap['named_kg']['MA'] / dap['total_kg']:.1%}",
        "ma_rock": f"{eu['Rock']['named_kg']['MA'] / eu['Rock']['total_kg']:.1%}",
        "reserve_hhi": hhi_label(usgs["summary"]["reserves_kt"]["hhi_points"]),
        "mine_hhi": hhi_label(usgs["summary"]["production_2025_kt"]["hhi_points"]),
        "mine_rows": "\n".join(
            tr(r["country"], f"{r['reserves_kt'] / 1000:,.2f}", f"{r['reserves_share']:.1%}",
               f"{r['production_2025_kt'] / 1000:,.2f}", f"{r['production_2025_share']:.1%}")
            for r in sorted(places.values(), key=lambda r: -r["reserves_kt"])
        ),
        "trade_rows": "\n".join(trade_rows), "trade_year": data["baci_legacy"]["year"],
        "eu_rows": "\n".join(
            tr(group, tonnes(g["total_kg"]), partner[next(iter(g["named_kg"]))].split(" (")[0],
               f"{max(g['named_kg'].values()) / g['total_kg']:.1%}", hhi_label(g["hhi_points"]),
               hhi_label(all_eu["2023"][group]["hhi_points"]),
               f"{sum(g['unnamed_kg'].values()) / g['total_kg']:.2%}")
            for group, g in eu.items()
        ),
        "fao_rows": "\n".join(
            tr(year, *(f"{r[k] / 1e6:.3f}" for k in ("production_t", "imports_t", "exports_t", "apparent_supply_t",
                                                    "agricultural_use_t", "supply_less_agricultural_use_t")),
               f"{r['net_import_share_of_apparent_supply']:.1%}") for year, r in fao.items()
        ),
        "grade_low": f"{data['grade_illustration_2024'][0]['elemental_p_t']:,.0f}",
        "grade_high": f"{data['grade_illustration_2024'][1]['elemental_p_t']:,.0f}",
        "scenario_rows": "\n".join(
            tr(f"{r['replacement_fraction']:.0%}", tonnes(r["remaining_gap_kg"]), f"{r['gap_share_of_baseline_imports']:.1%}")
            for r in scenario["rows"]
        ),
        "scenario_origin": partner[scenario["origin"]].split(" (")[0],
        "scenario_lost": tonnes(scenario["lost_kg"]),
        "scenario_baseline": tonnes(scenario["baseline_kg"]),
    }
    return Template((HERE / "article.html.in").read_text(encoding="utf-8")).substitute(values)


def build():
    data = build_evidence()
    html = render(data, read_json("phosphate_trade.json"))
    (OUT / "phosphate_chain.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                                              encoding="utf-8", newline="\n")
    (HERE / "phosphate-food-chain.html").write_text(html, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build()
