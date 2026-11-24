"""Build the battery study and its evidence from public and explicitly modelled inputs."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from string import Template

from replacement_followup import calculate_followup
from replacement_model import calculate

HERE = Path(__file__).resolve().parent
TITLE = "When can battery factories replace disrupted inputs?"
DECK = ("Battery ingredients change with the chemistry. Usable stocks, approved suppliers "
        "and access to upstream materials determine how long a factory can keep producing.")

MATERIALS = {"cathode": "Cathode active material", "graphite": "Graphite for the anode"}
CASES = {
    "baseline": "No disruption",
    "direct": "Direct origin only",
    "traced": "Direct and upstream exposure",
    "prequalified": "Alternatives qualified at the start",
    "no_replacements": "No eligible replacement deliveries",
}
TRADE_NOTES = {
    "850760": "Lithium-ion accumulators can include cells, modules and packs across applications. The archive reports values from 2017.",
    "283691": "Lithium carbonate, all grades and uses. The export record gives no battery-grade split or mine origin.",
}


def load(path):
    return json.loads((HERE / path).read_text(encoding="utf-8"))


def pct(amount, decimals=0):
    return f"{amount:.{decimals}%}"


def num(amount, decimals=0):
    return f"{amount:,.{decimals}f}"


def row(label, *values, attributes=""):
    cells = "".join(f"<td>{escape(str(value))}</td>" for value in values)
    return f'<tr{attributes}><th scope="row">{escape(str(label))}</th>{cells}</tr>'


def trade_rows(trade):
    year = trade["years"][-1]
    annual = trade["years_data"][str(year)]
    for code, item in trade["codes"].items():
        record = annual[code]
        top = next(iter(record["exporters"]), None)
        usd = "$" + num(record["world_usd"] / 1e9, 1) + " billion" if record["world_usd"] else "—"
        yield row(f'{item["title"]} (HS {code})', usd,
                  f'{top["name"]} · {pct(top["share"])}' if top else "—", TRADE_NOTES[code],
                  attributes=f' data-trade-code="{code}"')


def model_tables(data):
    model = data["model"]
    cases = model["cases"]
    traced = cases["traced"]
    input_rows, threshold_rows, timing_rows = [], [], []
    for label, line in data["lines"].items():
        for key, lane in line["lanes"].items():
            name = f"{label} · {MATERIALS[key]}"
            step = traced[label]["supply_schedule"][key]
            direct = lane["direct_exposure_fraction"]
            indirect = step["exposed_fraction"] - direct
            first = step["first_replacement_month"]
            actual = step["qualified_increment_tonnes_per_month"]
            required = step["minimum_sustained_replacement_tonnes_per_month"]
            input_rows.append(row(
                name, num(traced[label]["tonnes_per_gwh"][key], 1), pct(direct), pct(indirect),
                num(lane["opening_stock_months_at_full_output"], 1), first or "—", num(actual),
            ))
            threshold_rows.append(row(
                name, num(step["stock_to_bridge_to_qualification_tonnes"]),
                num(required), num(actual),
            ))

    for nmc, lfp in zip(traced["NMC811"]["months"], traced["LFP"]["months"]):
        timing_rows.append(row(
            nmc["month"], num(nmc["output_gwh"], 3), pct(nmc["loss_fraction"], 1),
            ", ".join(MATERIALS[m] for m in nmc["binding_inputs"]) or "Cell limit",
            num(lfp["output_gwh"], 3), pct(lfp["loss_fraction"], 1),
            ", ".join(MATERIALS[m] for m in lfp["binding_inputs"]) or "Cell limit",
        ))
    case_rows = [
        row(label, *(pct(cases[key][chemistry]["horizon_loss_fraction"], 2) for chemistry in data["lines"]))
        for key, label in CASES.items()
    ]
    higher_stock = next(
        case["horizon_loss_fraction"] for case in model["sensitivity_cases"]
        if case["opening_stock_multiplier"] == 2 and case["extra_qualification_months"] == 0
        and case["alternative_volume_multiplier"] == 1
    )
    return {
        "nmc_higher_stock": pct(higher_stock["NMC811"]),
        "lfp_higher_stock": pct(higher_stock["LFP"]),
        "inputs": "\n".join(input_rows), "thresholds": "\n".join(threshold_rows),
        "timing": "\n".join(timing_rows), "cases": "\n".join(case_rows),
        "sensitivity": "\n".join(
            row(label, " to ".join(pct(value, 1) for value in bounds))
            for label, bounds in model["sensitivity_loss_ranges"].items()
        ),
        "nmc_month_one": pct(traced["NMC811"]["months"][0]["loss_fraction"]),
        "lfp_month_one": pct(traced["LFP"]["months"][0]["loss_fraction"]),
        "nmc_horizon_loss": pct(traced["NMC811"]["horizon_loss_fraction"], 2),
        "lfp_horizon_loss": pct(traced["LFP"]["horizon_loss_fraction"], 0),
    }


def followup_tables(addendum):
    labels = {
        "stock_scale": "Opening stock",
        "extra_lag": "Additional qualification delay",
        "replacement_scale": "Eligible replacement volume",
    }
    def describe(field, value):
        if field == "extra_lag":
            return f"+{value} months"
        return f"{value:g}× baseline"

    def losses(result):
        return (pct(round(result[chemistry], 10), 2) for chemistry in ("NMC811", "LFP"))

    one_at_a_time = [
        row(labels[field], describe(field, case["value"]), *losses(case["loss_fraction"]))
        for field, cases in addendum["one_at_a_time"].items() for case in cases
    ]
    interactions = [
        row(" · ".join(f"{labels[field]} {describe(field, value)}" for field, value in case["options"].items()),
            *losses(case["loss_fraction"]))
        for cases in addendum["interactions"].values() for case in cases
    ]
    cases = addendum["scenarios"]
    comparisons = [row("Published traced case", *losses(addendum["traced_baseline_loss_fraction"]))]
    for key, label in (
        ("gradual_ramp", "Gradual replacement ramp"),
        ("public_graphite_timing", "Graphite timing based on supplier guidance"),
    ):
        comparisons.append(row(
            label, *losses({chemistry: result["horizon_loss_fraction"]
                            for chemistry, result in cases[key].items()}),
        ))
    spans = addendum["tested_loss_spans"]
    sources = addendum["assumptions"]["sources"]
    replacements = {
        "followup_one_at_a_time": "\n".join(one_at_a_time),
        "followup_interactions": "\n".join(interactions),
        "followup_cases": "\n".join(comparisons),
        "followup_graphite_first_month": addendum["graphite_no_sales_before_month"],
        "followup_nmc_delay_span": num(100 * spans["NMC811"]["extra_lag"], 1),
        "followup_lfp_stock_span": num(100 * spans["LFP"]["stock_scale"], 1),
    }
    replacements.update({f"followup_{key}_url": escape(source["url"], quote=True)
                         for key, source in sources.items()})
    return replacements


def render(data, trade):
    replacements = model_tables(data)
    replacements.update(followup_tables(data["review_addendum"]))
    sources = data["sources"]
    replacements.update({
        "version": data["version"], "months": data["scenario_months"],
        "title": escape(TITLE), "deck": escape(DECK),
        "production": "\n".join(row(
            item["step"], item["year"], item["share"], item["scope"]
        ) for item in data["production_crosswalk"]),
        "chemistry": "\n".join(row(
            item["family"], item["year"], item["cathode_material"], item["cells"]
        ) for item in data["chemistry_crosswalk"]),
        "sources": "\n".join(
            f'<li id="source-{key}"><a href="{escape(source["url"], quote=True)}">{escape(source["title"])}</a></li>'
            for key, source in sources.items()
        ),
        "trade_year": trade["years"][-1], "trade_rows": "\n".join(trade_rows(trade)),
    })
    return Template((HERE / "article.html.in").read_text(encoding="utf-8")).substitute(replacements)


def main():
    data = load("evidence_inputs.json")
    trade = load("out/battery_trade.json")
    data.update({
        "title": "Lithium-ion battery chain",
        "h1": TITLE,
        "deck": DECK,
        "published": True,
        "sources": {k: {"title": title, "url": url} for k, (title, url) in data["sources"].items()},
        "chokepoint": {
            "product": "Battery cells",
            "stage": "Cathode and anode materials",
            "mechanism": "capability",
            "research": True,
            "physics": "Qualified active materials feed chemistry-specific cell lines. Supply is concentrated by production location.",
            "holder": "China",
            "share": "About 85% of cathode and over 90% of anode output for electric car batteries (2025)",
            "control": "—",
            "conf": "estimate",
        },
        "model": calculate(data),
        "trade_display_boundaries": TRADE_NOTES,
    })
    data["review_addendum"] = calculate_followup(data, data["model"], load("followup_inputs.json"))
    html = render(data, trade)
    (HERE / "out/battery_chain.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (HERE / "battery-chain.html").write_text(html, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
