"""Build the public civil aero-engine research note from pinned estimates and BACI context."""
from __future__ import annotations

from collections import defaultdict
import csv
from html import escape
from itertools import product
import json
from pathlib import Path
from statistics import mean
from string import Template

HERE = Path(__file__).parent
OUT = HERE / "out"
VERSION = "2026-11-25"
TITLE = "Where civil aero-engine supply can tighten"
DECK = "Titanium grade changes who can supply the material. Programme approval, available capacity and stocks determine which alternatives a buyer can use."

SOURCES = {
    "jrc": {
        "title": "European Commission JRC, Titanium metal in the EU (2025), Figure 5, Box 1 and Annex 1",
        "year": 2025,
        "url": "https://publications.jrc.ec.europa.eu/repository/bitstream/JRC137082/JRC137082_01.pdf#page=17",
    },
    "usgs_rhenium": {
        "title": "USGS Mineral Commodity Summaries 2026, Rhenium",
        "year": 2026,
        "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026.pdf",
    },
    "usgs_titanium": {
        "title": "USGS Mineral Commodity Summaries 2026, Titanium and Titanium Dioxide",
        "year": 2026,
        "url": "https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-titanium.pdf",
    },
    "faa_quality": {
        "title": "FAA Advisory Circular 21-43A, §§3.3–3.5, supplier control",
        "year": 2015,
        "url": "https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_21-43A.pdf",
    },
    "boeing": {
        "title": "Boeing 2022 Form 10-K, Raw Materials, Parts and Subassemblies",
        "year": 2022,
        "url": "https://www.sec.gov/Archives/edgar/data/12927/000001292723000007/ba-20221231.htm",
    },
    "faa_ad": {
        "title": "FAA Airworthiness Directive 2024-05-11 (PW1100G and PW1400G engines)",
        "year": 2024,
        "url": "https://www.federalregister.gov/d/2024-06419",
    },
    "jetblue": {
        "title": "JetBlue Form 10-Q, quarter ended 30 June 2025, Recent Developments: Pratt & Whitney",
        "year": 2025,
        "url": "https://www.sec.gov/Archives/edgar/data/1158463/000115846325000089/jblu-20250630.htm",
    },
    "baci": {
        "title": "CEPII BACI V202601, based on UN Comtrade",
        "year": 2026,
        "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37",
    },
}

# JRC Figure 5. None indicates no aviation-grade segment was shown in the source.
JRC_SHARES = (
    ("China", 63, 12),
    ("Japan", 16, 41),
    ("Russia", 11, 30),
    ("Kazakhstan", 6, 17),
    ("Saudi Arabia", 3.8, None),
)
JRC_CAPACITY = {"all_qualities": 414, "aviation_grade": 157}
RHENIUM = {"year": 2025, "world_t": 81, "chile_t": 30, "secondary_t_range": [20, 25]}
SPONGE_OUTPUT = {"year": 2025, "china_kt": 260, "world_kt": 370}
US_SPONGE_IMPORTS = {
    "period": "2021–24", "shares_pct": {"Japan": 77, "Saudi Arabia": 13, "Kazakhstan": 8, "Other": 2}
}
SHOP_VISITS = {"period": "30 June 2025", "aircraft_grounded_reported": 8, "projected_shop_visit_days": 300}

STAGES = (
    ("Rhenium recovery", "USGS mine-linked and secondary estimates, tonnes per year.", "Global recovery capacity, usable metal stocks and programme demand."),
    ("Titanium sponge", "JRC operating capacity by country and grade, tonnes per year. USGS output and import origins.", "Approved plants, uncommitted output and accessible stock of the required grade."),
    ("Titanium melting and fabrication", "Process and grade distinctions in the JRC study.", "Compatible melt and mill routes, qualified volumes and lead times by programme."),
    ("Turbine parts", "FAA conformity requirements and a documented inspection case.", "Approved alternative facilities, part-family throughput, spare capacity and approval lead time."),
    ("Engine assembly and service", "Buyer and regulator disclosures for specific civil cases.", "Comparable delivered units by programme and owner, availability of approved replacement engines and shop slots."),
)

TRADE_BOUNDARIES = {
    "810820": "Sponge, ingot and powders. The heading does not identify grade or end use.",
    "750210": "Unalloyed nickel for many uses. The heading does not identify aerospace buyers.",
    "841112": "Turbojets traded as goods in this thrust category. Engines delivered in aircraft are outside this heading.",
    "841122": "Turboprop engines traded as goods in this power category.",
    "841191": "Parts as traded. The export country may be a repair or distribution hub.",
}

SCENARIO_INPUTS = {
    "monthly_demand": 100,
    "monthly_supply_lost": 25,
    "months": 12,
    "opening_stock_options": [0, 75],
    "months_before_deliveries_options": [3, 9],
    "replacement_per_month_options": [10, 25],
}


# These fractions are assumptions, not observations of access or approval.
ACCESS_CASES = (
    ("all", "All displayed capacity", 100, {}),
    ("half_all", "Half of each country's capacity included", 50, {}),
    ("half_japan", "Half of Japan's capacity included", 100, {"Japan": 50}),
    ("no_china", "China segment omitted", 100, {"China": 0}),
    ("no_russia", "Russia segment omitted", 100, {"Russia": 0}),
    ("no_china_russia", "China and Russia segments omitted", 100, {"China": 0, "Russia": 0}),
)


def concentration(shares):
    ranked = sorted((share or 0 for share in shares), reverse=True)
    return {
        "hhi": round(sum(share ** 2 for share in ranked), 2),
        "top_two_pct": sum(ranked[:2]),
    }


def titanium_capacity():
    shares = [*JRC_SHARES, ("Other", round(100 - sum(row[1] for row in JRC_SHARES), 1), None)]
    all_grades = concentration(row[1] for row in shares)
    aviation = concentration(row[2] for row in shares)
    return {
        "source": "jrc",
        "kind": "Source estimates and calculated",
        "year": 2023,
        "quantity": "Operating capacity",
        "total_kt_per_year": JRC_CAPACITY,
        "shares_pct": [
            {"geography": name, "all_qualities": total, "aviation_grade": grade}
            for name, total, grade in shares
        ],
        "rounding_note": "Other is the residual of the rounded all-quality labels. Null means no displayed segment and is treated as zero when computing HHI only.",
        "all_qualities": all_grades,
        "aviation_grade": aviation,
        "aviation_grade_fraction": JRC_CAPACITY["aviation_grade"] / JRC_CAPACITY["all_qualities"],
        "hhi_fraction_lower": 1 - aviation["hhi"] / all_grades["hhi"],
    }


def simulate(opening_stock, lag, replacement):
    demand = SCENARIO_INPUTS["monthly_demand"]
    remaining_supply = demand - SCENARIO_INPUTS["monthly_supply_lost"]
    stock = opening_stock
    cumulative_unmet = 0
    periods = []
    for month in range(1, SCENARIO_INPUTS["months"] + 1):
        new_supply = replacement if month > lag else 0
        gap = max(0, demand - remaining_supply - new_supply)
        withdrawal = min(stock, gap)
        stock -= withdrawal
        unmet = gap - withdrawal
        cumulative_unmet += unmet
        periods.append({
            "month": month, "demand": demand, "continuing_supply": remaining_supply,
            "alternative_supply": new_supply, "stock_withdrawn": withdrawal,
            "ending_stock": stock, "unmet": unmet, "cumulative_unmet": cumulative_unmet,
        })
    return periods


def scenarios():
    opening = SCENARIO_INPUTS["opening_stock_options"]
    delays = SCENARIO_INPUTS["months_before_deliveries_options"]
    deliveries = SCENARIO_INPUTS["replacement_per_month_options"]
    results, paths = [], []
    for stock, lag, replacement in product(opening, delays, deliveries):
        inputs = {
            "opening_stock": stock, "months_before_deliveries": lag,
            "replacement_units_per_month": replacement,
        }
        periods = simulate(stock, lag, replacement)
        paths.extend({**inputs, **period} for period in periods)
        results.append({
            **inputs,
            "first_shortage": next((period["month"] for period in periods if period["unmet"]), None),
            "unmet_units": periods[-1]["cumulative_unmet"],
        })
    return results, paths


def accessibility(capacity):
    shares = {row["geography"]: row["aviation_grade"]
              for row in capacity["shares_pct"] if row["aviation_grade"] is not None}
    total_capacity = capacity["total_kt_per_year"]["aviation_grade"]
    cases = []
    for case_id, name, default, overrides in ACCESS_CASES:
        weights = {country: overrides.get(country, default) for country in shares}
        included = {country: share * weights[country] / 100 for country, share in shares.items()}
        pool = sum(included.values())
        accessible_shares = {country: quantity * 100 / pool
                             for country, quantity in included.items()} if pool else {}
        cases.append({
            "id": case_id, "case": name, "assumed_access_pct_by_country": weights,
            "share_of_capacity_included_pct": round(pool, 4),
            "capacity_included_kt_per_year": round(total_capacity * pool / 100, 4),
            "included_country_shares_pct": {country: round(share, 4)
                                            for country, share in accessible_shares.items()},
            "country_hhi": concentration(accessible_shares.values())["hhi"] if pool else None,
        })
    return cases


def matched_effects(results):
    stock = SCENARIO_INPUTS["opening_stock_options"]
    wait = SCENARIO_INPUTS["months_before_deliveries_options"]
    rate = SCENARIO_INPUTS["replacement_per_month_options"]
    factors = (
        ("opening_stock", "Add opening stock", "units", min(stock), max(stock)),
        ("months_before_deliveries", "Shorten the wait for alternatives", "months", max(wait), min(wait)),
        ("replacement_units_per_month", "Raise the replacement rate", "units per month", min(rate), max(rate)),
    )
    effects = []
    for factor, label, unit, before, after in factors:
        controls = tuple(key for key, *_ in factors if key != factor)
        groups = defaultdict(dict)
        for row in results:
            groups[tuple(row[key] for key in controls)][row[factor]] = row["unmet_units"]
        matches = [
            {"held_constant": dict(zip(controls, key, strict=True)),
             "unmet_initial": outcomes[before], "unmet_after_change": outcomes[after],
             "reduction": outcomes[before] - outcomes[after]}
            for key, outcomes in groups.items()
        ]
        reductions = [match["reduction"] for match in matches]
        effects.append({
            "factor": factor, "label": label, "unit": unit, "initial_setting": before,
            "changed_setting": after, "mean_reduction": mean(reductions),
            "min_reduction": min(reductions), "max_reduction": max(reductions), "matches": matches,
        })
    return sorted(effects, key=lambda row: row["mean_reduction"], reverse=True)


def import_export_ratio(items):
    def us_value(side):
        return next((row["value_usd"] for row in items[side] if row["iso"] == "US"), None)

    imports, exports = us_value("importers"), us_value("exporters")
    return imports / exports if imports is not None and exports else None


def evidence(trade, results):
    year = trade["years"][-1]
    latest = trade["years_data"][str(year)]
    return {
        "title": "Civil aero-engine supply",
        "h1": TITLE, "deck": DECK, "published": True, "version": VERSION,
        "chokepoint": {
            "product": "Civil aircraft",
            "stage": "Qualified engine parts and supply",
            "mechanism": "capability",
            "physics": "Engine parts must meet the approved design. Spare qualified capacity depends on the programme.",
            "holder": "programme-specific", "share": "—", "control": "—",
            "conf": "snapshot", "research": True,
        },
        "titanium_capacity": titanium_capacity(),
        "sponge_output": {"source": "usgs_titanium", **SPONGE_OUTPUT},
        "us_sponge_imports": {"source": "usgs_titanium", **US_SPONGE_IMPORTS},
        "rhenium": {"source": "usgs_rhenium", **RHENIUM},
        "shop_visits": {"sources": ["faa_ad", "jetblue"], **SHOP_VISITS},
        "stages": [
            {"stage": stage, "evidence": available, "missing": missing}
            for stage, available, missing in STAGES
        ],
        "supply_sensitivity": {
            "kind": "Modelled",
            "scope": "Hypothetical qualified input for a civil buyer. Assumptions are not calibrated to either historical case.",
            "inputs": SCENARIO_INPUTS, "results": results, "paths_csv": "out/aerospace_supply_scenarios.csv",
        },
        "trade": {
            "source": "baci", "year": year, "coverage": TRADE_BOUNDARIES,
            "us_import_export_value_ratio": {
                code: import_export_ratio(latest[code]) for code in ("810820", "841112")
            },
            "turbojet_exporter_hhi": round(10000 * latest["841112"]["export_hhi"]),
        },
        "sources": SOURCES,
    }


def source_link(key, label):
    return f'<a href="{escape(SOURCES[key]["url"])}">{escape(label)}</a>'


def table_row(values, *, attrs="", shares=False, row_header=True):
    cells = []
    for index, value in enumerate(values):
        if shares and index:
            cell = "—" if value is None else (
                f'{value:g}%<meter min="0" max="100" value="{value:g}" aria-hidden="true"></meter>'
            )
        else:
            cell = escape(str(value))
        cells.append(f'<th scope="row">{cell}</th>' if index == 0 and row_header else f'<td>{cell}</td>')
    return f"        <tr{attrs}>" + "".join(cells) + "</tr>"


def trade_table(trade, year):
    for code, product_info in trade["codes"].items():
        item = trade["years_data"][str(year)][code]
        leader = item["exporters"][0] if item["exporters"] else None
        leading = f'{leader["name"]} · {leader["share"]:.0%}' if leader else "—"
        yield table_row((
            f'{product_info["title"]} ({code})', f'${item["world_usd"] / 1e9:,.1f}B',
            leading, TRADE_BOUNDARIES[code],
        ), attrs=f' data-trade-code="{escape(code)}"', row_header=False)


def render_followup(review):
    access = review["accessibility"]
    effects = review["matched_effects"]
    by_id = {case["id"]: case for case in access}
    full, half = by_id["all"], by_id["half_all"]
    half_japan, restricted = by_id["half_japan"], by_id["no_china_russia"]
    effect_rows = "\n".join(table_row((
        row["label"], f'{row["initial_setting"]} to {row["changed_setting"]} {row["unit"]}',
        f'{row["mean_reduction"]:g}', f'{row["min_reduction"]} to {row["max_reduction"]}'
        if row["min_reduction"] != row["max_reduction"] else f'{row["min_reduction"]} in every case',
    )) for row in effects)
    return {
        "review_date": review["date"],
        "access_rows": "\n".join(table_row((
            case["case"], f'{case["share_of_capacity_included_pct"]:g}%',
            f'{case["capacity_included_kt_per_year"]:,.1f}',
            f'{case["country_hhi"]:,.0f}' if case["country_hhi"] is not None else "None",
        )) for case in access),
        "full_capacity_hhi": f'{full["country_hhi"]:,.0f}',
        "half_capacity": f'{half["capacity_included_kt_per_year"]:,.1f}',
        "half_japan_hhi": f'{half_japan["country_hhi"]:,.0f}',
        "restricted_pool": f'{restricted["share_of_capacity_included_pct"]:g}%',
        "restricted_hhi": f'{restricted["country_hhi"]:,.0f}',
        "effect_rows": effect_rows,
    }


def render(data, trade):
    capacity = data["titanium_capacity"]
    results = data["supply_sensitivity"]["results"]
    year = data["trade"]["year"]
    ratios = data["trade"]["us_import_export_value_ratio"]
    imports = US_SPONGE_IMPORTS["shares_pct"]
    buffer = SCENARIO_INPUTS["opening_stock_options"][-1]
    short_delay, long_delay = SCENARIO_INPUTS["months_before_deliveries_options"]
    full_replacement = SCENARIO_INPUTS["monthly_supply_lost"]
    full_supply_rows = {
        row["months_before_deliveries"]: row["unmet_units"] for row in results
        if row["opening_stock"] == buffer and row["replacement_units_per_month"] == full_replacement
    }
    ratios_shown = []
    for code, digits in (("810820", 1), ("841112", 2)):
        ratio = ratios[code]
        value = f"{ratio:.{digits}f}" if ratio is not None else "unavailable in the published country totals"
        ratios_shown.append(f"HS {code}, {value}")
    values = {
        **render_followup(data["second_review"]),
        "title": escape(TITLE), "deck": escape(DECK), "version": VERSION,
        "hhi_all": f'{capacity["all_qualities"]["hhi"]:,.0f}',
        "hhi_aviation": f'{capacity["aviation_grade"]["hhi"]:,.0f}',
        "hhi_change": f'{capacity["hhi_fraction_lower"]:.1%}',
        "capacity_fraction": f'{capacity["aviation_grade_fraction"]:.0%}',
        "all_kt": JRC_CAPACITY["all_qualities"], "aviation_kt": JRC_CAPACITY["aviation_grade"],
        "top_two_all": f'{capacity["all_qualities"]["top_two_pct"]:g}%',
        "top_two_aviation": f'{capacity["aviation_grade"]["top_two_pct"]:g}%',
        "capacity_rows": "\n".join(table_row(
            (row["geography"], row["all_qualities"], row["aviation_grade"]), shares=True,
        ) for row in capacity["shares_pct"]),
        "china_output_kt": SPONGE_OUTPUT["china_kt"], "world_output_kt": SPONGE_OUTPUT["world_kt"],
        "output_year": SPONGE_OUTPUT["year"],
        "china_output_share": f'{SPONGE_OUTPUT["china_kt"] / SPONGE_OUTPUT["world_kt"]:.0%}',
        "import_period": US_SPONGE_IMPORTS["period"],
        "japan_import_share": f'{imports["Japan"]}%', "saudi_import_share": f'{imports["Saudi Arabia"]}%',
        "kazakh_import_share": f'{imports["Kazakhstan"]}%',
        "stage_rows": "\n".join(table_row(row) for row in STAGES),
        "rhenium_world_t": RHENIUM["world_t"], "rhenium_year": RHENIUM["year"],
        "rhenium_chile_t": RHENIUM["chile_t"], "rhenium_chile_share": f'{RHENIUM["chile_t"] / RHENIUM["world_t"]:.0%}',
        "rhenium_secondary_range": "–".join(str(value) for value in RHENIUM["secondary_t_range"]),
        "grounded": SHOP_VISITS["aircraft_grounded_reported"], "shop_days": SHOP_VISITS["projected_shop_visit_days"],
        "demand": SCENARIO_INPUTS["monthly_demand"], "loss": SCENARIO_INPUTS["monthly_supply_lost"],
        "months": SCENARIO_INPUTS["months"], "buffer": buffer,
        "short_delay": short_delay, "long_delay": long_delay,
        "early_shortfall": full_supply_rows[short_delay], "late_shortfall": full_supply_rows[long_delay],
        "scenario_rows": "\n".join(table_row((
            row["opening_stock"], row["months_before_deliveries"], row["replacement_units_per_month"],
            row["first_shortage"] or "None", row["unmet_units"],
        ), row_header=False) for row in results),
        "trade_year": year, "trade_rows": "\n".join(trade_table(trade, year)),
        "us_ratios": escape(" and ".join(ratios_shown)),
        "engine_export_hhi": f'{data["trade"]["turbojet_exporter_hhi"]:,}',
        "history_rows": "\n".join(table_row((item["year"], f'{item["china_export_share"]:.1%}'))
                                  for item in trade["series"]["810820"]),
        "jrc": source_link("jrc", "JRC Figure 5 and Annex 1."),
        "usgs_titanium": source_link("usgs_titanium", "USGS titanium summary."),
        "faa_quality": source_link("faa_quality", "FAA production guidance."),
        "usgs_rhenium": source_link("usgs_rhenium", "USGS rhenium summary."),
        "boeing": source_link("boeing", "Boeing 2022 Form 10-K."),
        "faa_ad": source_link("faa_ad", "FAA directive."),
        "jetblue": source_link("jetblue", "JetBlue’s June 2025 filing."),
        "baci": source_link("baci", "CEPII BACI."),
        "source_items": "\n".join(f'    <li>{source_link(key, info["title"])}</li>' for key, info in SOURCES.items()),
    }
    return Template((HERE / "article.html.in").read_text(encoding="utf-8")).substitute(values)


def build():
    trade = json.loads((OUT / "aerospace_trade.json").read_text(encoding="utf-8"))
    results, paths = scenarios()
    data = evidence(trade, results)
    data["second_review"] = {
        "date": "2026-11-25",
        "reviewed_commit": "ac6f0abb4eda3305332ea307b64f378b5a4dc43d",
        "kind": "Modelled",
        "capacity_source": "JRC Figure 5, aviation-grade titanium sponge operating capacity, 2023",
        "scope": "Illustrative weights on displayed country shares. No approval, spare capacity, or trade access is observed.",
        "accessibility": accessibility(data["titanium_capacity"]),
        "matched_effects": matched_effects(results),
    }
    article = render(data, trade)
    (HERE / "aerospace-chain.html").write_text(article, encoding="utf-8", newline="\n")
    (OUT / "aerospace_chain.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n",
    )
    with (OUT / "aerospace_supply_scenarios.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(paths[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(paths)


if __name__ == "__main__":
    build()
