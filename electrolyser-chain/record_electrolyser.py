"""Build the static electrolyser study, evidence and downloadable model tables."""
from __future__ import annotations

from decimal import Decimal
from html import escape
import json
from math import ceil
from pathlib import Path
from string import Template

from constraint_frontier import evaluate, summarise, write_tables

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
    article = render(evidence, trade)
    (HERE / "electrolyser-chain.html").write_text(article, encoding="utf-8", newline="\n")
    (OUT / "electrolyser_chain.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, default=serialise_decimal) + "\n",
        encoding="utf-8", newline="\n",
    )
    write_tables(OUT, evidence["results"])


if __name__ == "__main__":
    build()
