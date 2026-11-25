"""Build the static electrolyser study, evidence and downloadable model tables."""
from __future__ import annotations

from decimal import Decimal
from html import escape
import json
from math import ceil
from pathlib import Path
from string import Template

from constrained_deployment import evaluate_followup
from constraint_frontier import evaluate, summarise, write_csv, write_tables

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
TITLE = "When could iridium limit PEM electrolysis?"
DECK = ("New capacity, catalyst loading and the share of supply available to PEM determine "
        "annual iridium requirements. Stack replacement and recycling change them over time.")


def fmt(value, places=2):
    number = f"{value:,.{places}f}"
    return number.rstrip("0").rstrip(".") if places else number


def rows(items):
    return "\n".join(
        f'<tr><th scope="row">{escape(str(label))}</th>'
        + "".join(f"<td>{escape(str(item))}</td>" for item in cells) + "</tr>"
        for label, *cells in items
    )


def render_sensitivity(followup, last_year):
    reference = followup["reference"]
    metrics = ("first_gap_year", "gross_demand_t", "sum_annual_gaps_t")
    cases = followup["sensitivity"]

    def position(value, domain):
        bottom, top = domain
        return (value - bottom) / (top - bottom) if top > bottom else 0.5

    def plot_value(value):
        return last_year + 1 if value is None else value

    domains = {}
    for key in metrics:
        values = [plot_value(reference[key])]
        values.extend(plot_value(row[bound][key]) for row in cases for bound in ("low", "high"))
        domains[key] = (min(values), max(values))

    def cell(case, key):
        low, high = (case[bound][key] for bound in ("low", "high"))
        left, right = sorted(position(plot_value(value), domains[key]) for value in (low, high))
        baseline = position(plot_value(reference[key]), domains[key])
        values = " / ".join("No gap" if value is None else fmt(value, 0 if key == "first_gap_year" else 1)
                            for value in (low, high))
        return (
            f'<td>{values}<span class="sensitivity-track" aria-hidden="true">'
            f'<span class="sensitivity-interval" style="left:{left:.2%};width:{right-left:.2%}"></span>'
            f'<span class="sensitivity-reference" style="left:{baseline:.2%}"></span></span></td>'
        )

    ordered = sorted(cases, key=lambda row: abs(
        row["high"]["sum_annual_gaps_t"] - row["low"]["sum_annual_gaps_t"]), reverse=True)
    return "\n".join(
        f'<tr><th scope="row">{escape(case["label"])}<br>'
        f'<span class="note">{fmt(case["low"]["value"])} / {fmt(case["high"]["value"])}</span></th>'
        + "".join(cell(case, key) for key in metrics) + "</tr>"
        for case in ordered
    )


def render_followup(data, citations, last_year):
    settings = data["second_review"]
    result = settings["results"]
    cases = result["loading_cases"]
    by_id = {case["id"]: case for case in cases}
    transition, advanced = by_id["transition"], by_id["advanced"]
    interaction = next(pair for pair in result["interactions"]
                       if pair["parameters"] == ["ir_kg_per_mw", "operating_stack_hours"])
    short_life = settings["sensitivity"]["operating_stack_hours"]["low"]
    advanced_short = next(case for case in interaction["cases"]
                          if case["left"] == advanced["ir_kg_per_mw"] and case["right"] == short_life)
    source = settings["capacity_definition"]
    deployment_rows = "\n".join(
        f'<tr><th scope="row">{escape(case["label"])}<br>'
        f'<span class="note">{escape(case["detail"])} {citations[case["source"]]}.</span></th>'
        f'<td>{fmt(case["ir_kg_per_mw"])}</td><td>{case["first_gap_year"] or "No gap"}</td>'
        f'<td>{fmt(case["commissioned_new_gw"], 1)}</td><td>{fmt(case["queued_new_gw"], 1)}</td></tr>'
        for case in cases
    )
    labels = settings["sensitivity"]
    interaction_rows = rows(
        (pair["label"], f'{labels[pair["parameters"][0]]["label"]}: {fmt(case["left"])}',
         f'{labels[pair["parameters"][1]]["label"]}: {fmt(case["right"])}',
         case["first_gap_year"] or "No gap", fmt(case["sum_annual_gaps_t"], 1), fmt(case["queued_new_gw"], 1))
        for pair in result["interactions"] for case in pair["cases"]
    )
    return {
        "review_date": settings["date"],
        "capacity_definition": f'<a href="{escape(source["url"], quote=True)}">{escape(source["title"])}</a>',
        "mine_output": fmt(settings["market"]["mine_output_t"]),
        "competing_demand": fmt(settings["market"]["other_net_demand_t"]),
        "market_budget": fmt(transition["market_budget_t_per_year"]),
        "deployment_rows": deployment_rows, "scheduled_new": fmt(transition["scheduled_new_gw"], 1),
        "transition_loading": fmt(transition["ir_kg_per_mw"]),
        "transition_fitted": fmt(transition["commissioned_new_gw"], 1),
        "transition_queued": fmt(transition["queued_new_gw"], 1),
        "advanced_loading": fmt(advanced["ir_kg_per_mw"]),
        "advanced_short_gap": advanced_short["first_gap_year"],
        "advanced_short_queue": fmt(advanced_short["queued_new_gw"], 1),
        "short_life": fmt(short_life, 0),
        "sensitivity_ranges": render_sensitivity(result, last_year),
        "interaction_rows": interaction_rows,
    }


def render(data, trade):
    result = data["results"]
    static = data["static_scenarios"]
    annual = data["annual"]
    benchmarks = data["benchmarks"]
    reference = annual["assumptions"]
    example = static["display_example"]
    pathways = result["pathways"]
    names = {key: path["label"] for key, path in annual["pathways"].items()}
    citations = {key: f'<a href="{escape(source["url"], quote=True)}">{escape(source["title"])}</a>'
                 for key, source in data["sources"].items()}

    thresholds = {(row["intensity_kg_Ir_per_MW"], row["assumed_share_global_supply"]):
                  row["annual_new_PEM_GW_at_equality"] for row in result["thresholds"]}
    shares = static["assumed_primary_shares"]
    choices = static["intensity_kg_ir_per_mw"]
    gw = example["annual_new_pem_gw"]
    example_pair = (example["intensity_kg_ir_per_mw"], example["assumed_primary_share"])
    scenario = next(row for row in result["scenario_matrix"]
                    if (row["annual_new_PEM_GW"], row["intensity_kg_Ir_per_MW"],
                        row["assumed_share_global_supply"]) == (gw, *example_pair))
    series = [path["rows"] for path in pathways.values()]
    first, last = series[0][0]["year"], series[0][-1]["year"]
    markers = (first, 2030, 2040, last)
    primary = series[0][0]["primary_ir_available_t"]
    max_annual = max(entry["primary_ir_required_t"] for entries in series for entry in entries)
    ceiling = max(5, 5 * ceil(max(max_annual, primary) / 5))
    charts = []
    for label, entries in zip(names.values(), series, strict=True):
        bars = "".join(f'<i style="height:{row["primary_ir_required_t"] / ceiling:.2%}"></i>' for row in entries)
        charts.append(f'<div><b>{escape(label)}</b><div class="series" style="--supply:{primary / ceiling:.2%}">'
                      f'{bars}</div><div class="time-axis"><span>{first}</span><span>{last}</span></div></div>')
    yearly_rows = rows(
        (year, fmt(primary), *(fmt(entries[year - first]["primary_ir_required_t"]) for entries in series))
        for year in markers
    )
    first_gaps = rows((names[key], summarise(path)["first_gap_year"] or "None") for key, path in pathways.items())

    mitigation = result["mitigation"]
    ref = mitigation["reference"]
    mitigation_rows = rows(
        (case["label"], fmt(case["cumulative_primary_ir_required_t"], 1),
         fmt(case["cumulative_gap_t"], 1), case["first_gap_year"] or "None")
        for case in mitigation.values()
    )
    annual_sensitivity = [case["cumulative_gap_t"] for case in result["annual_sensitivity"]]
    market = benchmarks["market"]
    intensity_rows = "\n".join(
        f'<tr><th scope="row">{escape(item["label"])}</th><td>{"–".join(fmt(v) for v in item["values_kg_per_mw"])}</td>'
        f'<td>{escape(item["status"])}</td><td>{escape(item["detail"])} {citations[item["source"]]}.</td></tr>'
        for item in benchmarks["loadings"]
    )

    year = trade["years"][-1]
    trade_rows = []
    for code, item in trade["codes"].items():
        row = trade["years_data"][str(year)][code]
        exporter = row["exporters"][0]
        trade_rows.append(
            f'<tr data-trade-code="{escape(code, quote=True)}"><th scope="row">{escape(item["title"])}<br>'
            f'<span class="note">HS {escape(code)}</span></th><td>USD {fmt(row["world_usd"] / 1e9)} billion</td>'
            f'<td>{escape(exporter["name"])} · {exporter["share"]:.1%}</td><td>{escape(item["boundary"])}</td></tr>'
        )

    def options(values, selected, percent=False):
        return "".join(
            f'<option value="{value}"{" selected" if value == selected else ""}>'
            f'{f"{value:.0%}" if percent else fmt(value)}</option>'
            for value in values
        )

    values = {
        "title": TITLE, "deck": DECK, "date": data["date"],
        "market_primary": fmt(market["primary_supply_t"]),
        "market_demand": fmt(market["total_net_demand_t"]),
        "electrochemical_demand": fmt(market["net_demand_t"]["Electrochemical"]),
        "market_rows": rows((key, fmt(v)) for key, v in market["net_demand_t"].items()),
        "intensity_rows": intensity_rows,
        "capacity_stock": benchmarks["deployment"]["installed_gw_lower_bound"],
        "construction": benchmarks["deployment"]["construction_targeting_2026_gw_lower_bound"],
        "reference_supply": fmt(static["primary_output_t_per_year"]),
        "share_columns": "".join(f'<th scope="col">{share:.0%}</th>' for share in shares),
        "threshold_rows": rows((fmt(intensity), *(fmt(thresholds[intensity, share]) for share in shares))
                               for intensity in choices),
        "gw_default": gw, "example_loading": fmt(example_pair[0]), "example_share": f"{example_pair[1]:.0%}",
        "intensity_options": options(choices, example_pair[0]),
        "share_options": options(shares, example_pair[1], percent=True),
        "gross": fmt(scenario["gross_demand_t_Ir_per_year"]),
        "available": fmt(scenario["assumed_available_t_Ir_per_year"]),
        "gap": fmt(scenario["shortfall_t_Ir_per_year"]),
        "equality": fmt(thresholds[example_pair]),
        "loading_at_equality": fmt(scenario["assumed_available_t_Ir_per_year"] / gw, 3),
        "primary_allocation": fmt(primary), "start": first, "end": last, "ceiling": ceiling,
        "charts": "\n".join(charts),
        "annual_headers": "".join(f'<th scope="col">{escape(name)}</th>' for name in names.values()),
        "yearly_rows": yearly_rows, "first_gaps": first_gaps, "mitigation_rows": mitigation_rows,
        "cumulative_ref_gap": fmt(ref["cumulative_gap_t"], 1),
        "cumulative_market_gap": fmt(result["market_supply_comparison"]["cumulative_gap_t"], 1),
        "low_sensitivity": fmt(min(annual_sensitivity), 1), "high_sensitivity": fmt(max(annual_sensitivity), 1),
        "operating_hours": fmt(reference["operating_stack_hours"], 0), "utilisation": f'{reference["utilisation"]:.0%}',
        "calendar_stack": ref["stack_calendar_years"], "plant_years": reference["plant_lifetime_years"],
        "ref_share": f'{reference["pem_share"]:.0%}', "primary_share": f'{reference["primary_share"]:.0%}',
        "ref_intensity": fmt(reference["intensity_by_year"][str(first)]),
        "manufacturing_yield": f'{reference["manufacturing_yield"]:.0%}',
        "recovery": f'{reference["recovery_fraction"]:.0%}', "lag": reference["recycling_lag_years"],
        "trade_year": year, "trade_rows": "\n".join(trade_rows),
        **citations,
        **render_followup(data, citations, last),
    }
    return Template((HERE / "article.html.in").read_text(encoding="utf-8")).substitute(values)


def serialise_decimal(value):
    if isinstance(value, Decimal):
        return float(round(value, 6))
    raise TypeError(f"Cannot serialise {type(value).__name__}")


def build():
    evidence = json.loads((HERE / "evidence_inputs.json").read_text(encoding="utf-8"))
    trade = json.loads((OUT / "electrolyser_trade.json").read_text(encoding="utf-8"))
    evidence.update({
        "title": "Electrolyser / hydrogen chain", "h1": TITLE, "deck": DECK, "published": True,
        "chokepoint": {
            "product": "Water electrolysis", "stage": "Iridium supply for PEM", "mechanism": "byproduct",
            "physics": "Iridium is recovered with other PGMs. PEM exposure depends on loading, supply allocation and recycling.",
            "holder": "South Africa (primary supply)", "share": "—", "control": "—", "conf": "estimate",
        },
        "results": evaluate(evidence),
    })
    followup = evidence["second_review"]
    followup["results"] = evaluate_followup(evidence)
    article = render(evidence, trade)
    (HERE / "electrolyser-chain.html").write_text(article, encoding="utf-8", newline="\n")
    (OUT / "electrolyser_chain.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, default=serialise_decimal) + "\n",
        encoding="utf-8", newline="\n",
    )
    write_tables(OUT, evidence["results"])
    write_csv(OUT / "constrained_annual_deployment.csv", [
        {"loading_case": case["id"], **row}
        for case in followup["results"]["loading_cases"] for row in case["years"]
    ])


if __name__ == "__main__":
    build()
