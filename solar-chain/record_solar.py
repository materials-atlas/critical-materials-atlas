"""Build the static solar study and its downloadable evidence."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
from string import Template

from solar_flow import INPUTS, STAGES, evaluate, evaluate_followup

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "solar_chain.json"
TRADE = HERE / "out" / "solar_trade.json"
ARTICLE = HERE / "solar-chain.html"
TEMPLATE = HERE / "article.html.in"
TITLE = "What limits solar module manufacturing?"
DECK = ("Factories that assemble modules need compatible upstream inputs. "
        "Europe’s capacity estimates and a wafer supply stress test show where those limits can arise.")


def value(number):
    return f"{number:,.3f}".rstrip("0").rstrip(".")


def rows(data):
    return "\n".join(
        "<tr><th scope=\"row\">" + escape(str(label)) + "</th>"
        + "".join(f"<td>{escape(str(item))}</td>" for item in cells) + "</tr>"
        for label, *cells in data
    )


def source_link(sources, key, label=None):
    source = sources[key]
    return f'<a href="{escape(source["url"], quote=True)}">{escape(label or source["title"])}</a>'


def share(stage, snapshot):
    percentage = snapshot["stage_shares_pct"].get(stage)
    return f"{percentage:g}%" if percentage is not None else "—"


def interval(bounds):
    low, high = bounds
    return value(low) if low == high else f"{value(low)}–{value(high)}"


def sensitivity_rows(grid):
    outputs = grid["module_output_gw"]
    maximum = max(map(max, outputs)) or 1
    return "\n".join(
        f'<tr><th scope="row">{value(rate)}</th>'
        + "".join(f'<td style="--level:{output / maximum:.1%}">{output:.2f}</td>' for output in row)
        + "</tr>"
        for rate, row in zip(grid["usable_domestic_ingot_gw_per_year"], outputs)
    )


def render(data, trade):
    sources = data["sources"]
    production = data["concentration"]["production_2023"]
    capacity = data["concentration"]["capacity_2024"]
    annual = data["europe_capacity"]["annual_gw_equivalent"]
    result = data["flow_results"]
    policy = result["policy_comparison"]
    upper = result["closed_route"]
    intensity = data["silicon_intensity"]["values"]
    year = trade["years"][-1]

    max_capacity = max(rate for rate in annual.values() if rate is not None)
    stage_rows = []
    for stage, rate in annual.items():
        label = stage.capitalize()
        if rate is None:
            cells = "<td colspan=\"2\">Unreported</td>"
        else:
            cells = (f'<td>{value(rate)}</td><td><meter min="0" max="{max_capacity}" '
                     f'value="{rate}" aria-label="{label} capacity on a common scale"></meter></td>')
        stage_rows.append(f'<tr><th scope="row">{label}</th>{cells}</tr>')

    trade_rows = []
    for code, info in trade["codes"].items():
        item = trade["years_data"][str(year)][code]
        top = next(iter(item["exporters"]), None)
        lead = f'{top["name"]} · {top["share"]:.0%}' if top else "—"
        amount = f'${item["world_usd"] / 1e9:,.1f} billion' if item["world_usd"] else "—"
        trade_rows.append((f'{info["title"]} ({code})', amount, lead, info["boundary"]))

    scenario_rows = [
        (scenario["label"], value(scenario["point_output_gw"]),
         interval(scenario["output_range_gw"]), interval(scenario["loss_range_gw"]),
         ", ".join(scenario["point_limiting_stage_capacities"]))
        for scenario in result["scenarios"].values()
    ]
    sensitivity = result["paired_ingot_wafer_one_gw_annual_gain"]
    followup = data["review_addendum"]
    grid = followup["severe_shock_grid"]
    eu_cases = followup["eu27_sourcing_cases"]["cases"]
    replacements = {
        "title": escape(TITLE), "deck": escape(DECK), "version": data["version"],
        "capacity_rows": "\n".join(stage_rows),
        "module_capacity": value(annual["modules"]),
        "closed_ceiling": value(upper["upper_bound_gw_per_year"]),
        "ratio": f'{upper["share_of_module_nameplate"]:.1%}',
        "inverter": value(data["europe_capacity"]["inverter_gw_per_year"]),
        "share_rows": rows((stage.capitalize(), share(stage, production), share(stage, capacity))
                           for stage in STAGES),
        "intensity_rows": rows((point["year"], value(point["grams_per_wp"]), point["wafer_thickness_um"])
                               for point in intensity),
        "intensity_ratio": value(intensity[0]["grams_per_wp"] / intensity[-1]["grams_per_wp"]),
        "months": result["scenario_months"],
        "scenario_rows": rows(scenario_rows),
        "review_date": followup["date"],
        "sensitivity_header": "".join(f'<th scope="col">{exposure:.0%}</th>'
                                      for exposure in grid["exposed_share_of_assumed_wafer_imports"]),
        "sensitivity_rows": sensitivity_rows(grid),
        "normal_wafer_rate": value(grid["assumed_wafer_import_gw_per_year"]),
        "fixed_wafer_rate": value(grid["fixed_wafer_nameplate_gw_per_year"]),
        "output_with_imports": value(grid["module_output_gw"][-1][0]),
        "output_without_imports": value(grid["module_output_gw"][-1][-1]),
        "no_wafer_output": value(eu_cases[0]["module_output_gw"]),
        "full_wafer_rate": value(eu_cases[1]["qualified_wafer_import_gw_per_year"]),
        "full_wafer_output": value(eu_cases[1]["module_output_gw"]),
        "paired_gain": value(sensitivity),
        "target_fraction": f'{policy["target_fraction_of_open"]:.0%}',
        "target_gw": value(policy["target_module_output_gw"]),
        "wafer_needed": value(policy["additional_qualified_wafer_supply_gw"]),
        "wafer_rate": value(policy["additional_annual_compatible_capacity_gw"]),
        "trade_rows": rows(trade_rows), "trade_year": year,
        "europe": source_link(sources, "europe", "IEA, 29 July 2026"),
        "eu": source_link(sources, "fraunhofer_eu", "Fraunhofer ISE, p. 14"),
        "pvps": source_link(sources, "pvps", "IEA PVPS, Figures 4.2–4.5"),
        "cap_share": source_link(sources, "policy", "IEA, State of Energy Policy 2026, p. 52"),
        "etp": source_link(sources, "etp", "IEA, Energy Technology Perspectives 2026"),
        "fraun": source_link(sources, "fraunhofer", "Fraunhofer ISE, pp. 8 and 36"),
        "cost": source_link(sources, "etp_cost", "IEA, Energy Technology Perspectives 2026, executive summary"),
        "references": "\n".join(f"<li>{source_link(sources, key)} · {escape(source['vintage'])}</li>"
                                for key, source in sources.items()),
    }
    return Template(TEMPLATE.read_text(encoding="utf-8")).substitute(replacements)


def build():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    trade = json.loads(TRADE.read_text(encoding="utf-8"))
    data.update({
        "title": "Solar-PV chain", "h1": TITLE, "deck": DECK, "published": True,
        "chokepoint": {
            "product": "Solar modules", "stage": "Ingot and wafer manufacturing", "mechanism": "capability",
            "physics": "Usable supply depends on available equipment and qualified inputs",
            "holder": "China", "share": "About 87% of global wafer capacity (2024)",
            "control": "—", "conf": "estimate", "research": True,
        },
        "flow_results": evaluate(data),
        "review_addendum": evaluate_followup(data),
    })
    article = render(data, trade)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    ARTICLE.write_text(article, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build()
