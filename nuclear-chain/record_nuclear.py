"""Build the dated civilian nuclear-fuel study and its evidence JSON."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from string import Template

HERE = Path(__file__).resolve().parent
TITLE = "What makes nuclear fuel supply hard to replace?"
DECK = (
    "Enrichment capacity is concentrated among a few operators. What utilities can replace "
    "after a supply interruption also depends on contracts, usable stocks and fuel qualification."
)


def concentration(capacity):
    total = sum(capacity.values())
    shares = {name: amount / total for name, amount in capacity.items()}
    return {
        "row_sum": total,
        "shares": shares,
        "hhi": 10_000 * sum(share**2 for share in shares.values()),
        "top_three_share": sum(sorted(shares.values(), reverse=True)[:3]),
    }


def replacement_threshold(annual_loss, months, lag_months, usable_stock_months):
    """Minimum constant qualified supply after the lag that prevents any service shortfall."""
    horizon_loss = annual_loss * months / 12
    bridge = annual_loss * min(months, lag_months) / 12
    stock = annual_loss * usable_stock_months / 12
    remaining_months = max(0, months - lag_months)

    # Deliveries arriving after the lag cannot retrospectively serve the earlier months.
    annual_rate = None
    if stock >= horizon_loss:
        annual_rate = 0.0
    elif stock >= bridge:
        annual_rate = (horizon_loss - stock) * 12 / remaining_months

    return {
        "gross_loss": horizon_loss,
        "usable_opening_stock": stock,
        "stock_required_before_replacements": bridge,
        "uncovered_before_replacements": max(0, bridge - stock),
        "minimum_annual_replacement": annual_rate,
    }


def calculate(data):
    conversion = concentration(data["world_conversion"]["rows"])
    enrichment = {
        key: concentration(series["rows"])
        for key, series in data["world_enrichment"].items()
    }
    historical = {
        stage: concentration(data["world_capacity_shares_2022"][stage])
        for stage in ("conversion", "enrichment")
    }
    wna = data["world_enrichment"]["wna_2025"]["rows"]
    conversion_rows = data["world_conversion"]["rows"]
    factors = data["sensitivity"]["cnnc_capacity_factors"]
    cn_sensitivity = {}
    for factor in factors:
        cn_sensitivity[str(factor)] = {
            "conversion_hhi": concentration({
                **conversion_rows,
                "CNNC (estimated)": conversion_rows["CNNC (estimated)"] * factor,
            })["hhi"],
            "enrichment_hhi": concentration({**wna, "CNNC": wna["CNNC"] * factor})["hhi"],
        }

    scenarios = {}
    for key, scenario in data["scenarios"].items():
        markets = []
        for market in scenario["markets"]:
            by_year = {}
            for year, exposed in market["exposed"].items():
                by_year[year] = [
                    replacement_threshold(
                        exposed, scenario["months"], case["lag_months"], case["usable_stock_months"]
                    )
                    for case in data["sensitivity"]["cases"]
                ]
            markets.append({"label": market["label"], "by_baseline_year": by_year})
        scenarios[key] = {"unit": scenario["unit"], "horizon_months": scenario["months"], "markets": markets}

    annual_loss = data["scenarios"]
    eu_enrichment, us_enrichment = annual_loss["russian_enrichment"]["markets"]
    eu_conversion = annual_loss["western_conversion"]["markets"][0]
    conversion_months = annual_loss["western_conversion"]["months"]
    residual = replacement_threshold(eu_conversion["exposed"]["2025"], conversion_months, 0, 3)
    return {
        "conversion": conversion,
        "nea_capacity_concentration_2022": historical,
        "enrichment": enrichment,
        "wna_2025_enrichment_row_difference": enrichment["wna_2025"]["row_sum"]
        - data["world_enrichment"]["wna_2025"]["published_total"],
        "cnnc_capacity_sensitivity": cn_sensitivity,
        "scenarios": scenarios,
        "joint_enrichment_threshold": {
            year: eu_enrichment["exposed"][year] + us_enrichment["exposed"][year]
            for year in eu_enrichment["exposed"]
        },
        "reversal_example": {
            "eu_conversion_uncovered_share_at_zero_replacement": (
                (residual["gross_loss"] - residual["usable_opening_stock"])
                / (eu_conversion["delivery_baseline"]["2025"] * conversion_months / 12)
            ),
            "eu_enrichment_uncovered_share_at_full_immediate_replacement": 0,
        },
    }


def inventory_accounting(result):
    """Track the original opening reserve on the model's minimum-supply path."""
    opening = result["usable_opening_stock"]
    # An early gap uses the whole reserve before replacements arrive. For a
    # feasible path, the minimum replacement rate uses stock up to gross loss.
    drawn = min(opening, result["gross_loss"])
    return {
        "opening_compatible_inventory_assumed": opening,
        "drawn_before_replacements": min(opening, result["stock_required_before_replacements"]),
        "drawn_by_scenario_end": drawn,
        "opening_reserve_remaining_at_end": opening - drawn,
    }


def scenario_addendum(data):
    """Preserve the original results and attach the scope and inventory accounts."""
    calculated = data["calculated"]
    cases = data["sensitivity"]["cases"]
    scenarios = {}
    for key, scenario in calculated["scenarios"].items():
        accounts = []
        for market in scenario["markets"]:
            for year, results in market["by_baseline_year"].items():
                for case, result in zip(cases, results, strict=True):
                    accounts.append({
                        "market": market["label"],
                        "baseline_year": int(year),
                        "replacement_delay_months": case["lag_months"],
                        "assumed_opening_stock_months": case["usable_stock_months"],
                        "gross_loss": result["gross_loss"],
                        **inventory_accounting(result),
                        "early_service_gap": result["uncovered_before_replacements"],
                        "minimum_annual_replacement": result["minimum_annual_replacement"],
                    })
        scenarios[key] = {
            "unit": scenario["unit"],
            "available_qualified_uncommitted_supply": None,
            "actual_shortage": None,
            "reactor_level_consequences_assessed": False,
            "inventory_basis": "Assumed compatible service-equivalent opening reserve",
            "accounts": accounts,
        }
    rows = data["world_enrichment"]["esa_2025"]["rows"]
    capacity = {operator: rows[operator] for operator in ("Urenco", "Orano")}
    combined = sum(capacity.values())
    requirement = calculated["joint_enrichment_threshold"]["2025"]
    return {
        "date": "2026-11-24",
        "scenarios": scenarios,
        "enrichment_capacity_screen": {
            "source": "ESA 2025 Annual Report, Table 8",
            "unit": "thousand SWU/year",
            "reported_operator_capacity": capacity,
            "combined_reported_capacity": combined,
            "joint_immediate_no_stock_requirement": requirement,
            "required_share_if_two_operators_alone_replace": requirement / combined,
        },
    }


def account_rows(addendum, key):
    for row in addendum["scenarios"][key]["accounts"]:
        if row["baseline_year"] != 2025:
            continue
        rate = row["minimum_annual_replacement"]
        stock_months = row["assumed_opening_stock_months"]
        stock_label = f"{stock_months} months of stock" if stock_months else "No stock"
        yield (
            f'{row["market"]} · {stock_label}',
            row["replacement_delay_months"],
            display_number(row["gross_loss"], 2),
            display_number(row["opening_compatible_inventory_assumed"], 2),
            display_number(row["drawn_before_replacements"], 2),
            display_number(row["drawn_by_scenario_end"], 2),
            display_number(row["opening_reserve_remaining_at_end"], 2),
            display_number(row["early_service_gap"], 2),
            "No early-gap-free rate" if rate is None else display_number(rate, 2),
        )


def display_number(value, places=0):
    return f"{value:,.{places}f}"


def pct(value):
    return f"{value:.2%}"


def table_rows(values):
    cells = []
    for title, *row in values:
        cells.append(
            f'<tr><th scope="row">{escape(str(title))}</th>'
            + "".join(f"<td>{escape(str(value))}</td>" for value in row)
            + "</tr>"
        )
    return "\n".join(cells)


def bars(values, max_value, format_value):
    lines = []
    for label, value in values:
        lines.append(
            f'<div class="barrow"><span>{escape(label)}</span>'
            f'<span class="track" aria-hidden="true"><span class="fill" '
            f'style="width:{value / max_value:.3%}"></span></span>'
            f'<span class="num">{format_value(value)}</span></div>'
        )
    return "\n".join(lines)


def source_links(sources):
    return {
        key: f'<a id="source-{key}" href="{escape(url, quote=True)}">{escape(label)}</a>'
        for key, (label, url) in sources.items()
    }


def trade_rows(trade):
    year = trade["years"][-1]
    for code, item in trade["codes"].items():
        annual = trade["years_data"][str(year)][code]
        top = next(iter(annual["exporters"]), None)
        yield (
            f'{item["title"]} ({code})',
            f'${annual["world_usd"] / 1e9:,.1f} billion' if annual["world_usd"] else "—",
            f'{top["name"]} · {top["share"]:.0%}' if top else "—",
            item["boundary"],
        )


def historical_rows(data):
    for scenario, item in data["scenarios"].items():
        stage = "Enrichment" if scenario == "russian_enrichment" else "Conversion"
        provider = "Russia" if stage == "Enrichment" else "ConverDyn"
        for market in item["markets"]:
            for year, annual in market["delivery_baseline"].items():
                exposed = market["exposed"][year]
                yield (
                    f'{market["label"]} · {stage}', year, f'{item["unit"]}/year',
                    display_number(annual), provider, display_number(exposed), pct(exposed / annual),
                )


def sensitivity_rows(data, results, key):
    markets = results["scenarios"][key]["markets"]
    for index, case in enumerate(data["sensitivity"]["cases"]):
        cells = []
        for market in markets:
            result = market["by_baseline_year"]["2025"][index]
            rate = result["minimum_annual_replacement"]
            if rate is None:
                cells.append(f'Early gap of {display_number(result["uncovered_before_replacements"], 1)}')
            else:
                cells.append(display_number(rate, 1))
        yield case["label"], *cells


def render(data, trade):
    result = data["calculated"]
    wna_enrichment = result["enrichment"]["wna_2025"]
    esa_enrichment = result["enrichment"]["esa_2025"]
    historical = result["nea_capacity_concentration_2022"]
    conversion = result["conversion"]
    world_mining = data["world_mining"]
    world_fabrication = data["world_fabrication"]
    eu_enrichment = data["procurement"]["eu_enrichment_2025"]
    us_enrichment = data["procurement"]["us_enrichment_2025"]
    conversion_rows = data["world_conversion"]["rows"]
    wna_rows = data["world_enrichment"]["wna_2025"]["rows"]
    esa_rows = data["world_enrichment"]["esa_2025"]["rows"]
    cn_sensitivity = result["cnnc_capacity_sensitivity"].values()
    markets = result["scenarios"]
    west = markets["western_conversion"]["markets"][0]["by_baseline_year"]

    addendum = data["scenario_addendum"]
    screen = addendum["enrichment_capacity_screen"]
    replacements = {
        "enrichment_account_rows": table_rows(account_rows(addendum, "russian_enrichment")),
        "conversion_account_rows": table_rows(account_rows(addendum, "western_conversion")),
        "addendum_requirement": display_number(screen["joint_immediate_no_stock_requirement"] / 1_000, 3),
        "addendum_reported_capacity": display_number(screen["combined_reported_capacity"] / 1_000, 1),
        "addendum_capacity_share": f'{screen["required_share_if_two_operators_alone_replace"]:.1%}',
        "title": escape(TITLE),
        "deck": escape(DECK),
        "version": data["version"],
        "sources": "\n".join(f"<li>{link}</li>" for link in source_links(data["sources"]).values()),
        "hhi_bars": bars([
            ("Conversion · WNA 2024", conversion["hhi"]),
            ("Conversion · NEA 2022", historical["conversion"]["hhi"]),
            ("Enrichment · NEA 2022", historical["enrichment"]["hhi"]),
            ("Enrichment · WNA 2025", wna_enrichment["hhi"]),
            ("Enrichment · ESA 2025", esa_enrichment["hhi"]),
        ], 10_000, display_number),
        "conversion_top_three": pct(conversion["top_three_share"]),
        "enrichment_top_three": pct(wna_enrichment["top_three_share"]),
        "conversion_hhi_low": display_number(min(s["conversion_hhi"] for s in cn_sensitivity)),
        "conversion_hhi_high": display_number(max(s["conversion_hhi"] for s in cn_sensitivity)),
        "enrichment_hhi_low": display_number(min(s["enrichment_hhi"] for s in cn_sensitivity)),
        "enrichment_hhi_high": display_number(max(s["enrichment_hhi"] for s in cn_sensitivity)),
        "mine_rows": table_rows(
            (country, display_number(amount), pct(amount / world_mining["wna_reported_total"]))
            for country, amount in world_mining["rows"].items()
        ),
        "conversion_rows": table_rows(
            (name, display_number(amount), pct(conversion["shares"][name]))
            for name, amount in conversion_rows.items()
        ),
        "enrichment_rows": table_rows(
            (name, display_number(amount), pct(wna_enrichment["shares"][name]),
             display_number(esa_rows[name]), pct(esa_enrichment["shares"][name]))
            for name, amount in wna_rows.items()
        ),
        "fabrication_rows": table_rows(
            (country, display_number(amount))
            for country, amount in world_fabrication["lwr_listed_by_plant_country"].items()
        ),
        "exposure_bars": bars([
            ("Rosatom · world capacity", wna_enrichment["shares"]["Rosatom"]),
            ("Russia · EU deliveries", eu_enrichment["rows"]["Russia"] / eu_enrichment["total"]),
            ("Russia · US purchases", us_enrichment["rows"]["Russia"] / us_enrichment["total"]),
        ], 1, pct),
        "historical_rows": table_rows(historical_rows(data)),
        "enrichment_threshold_rows": table_rows(sensitivity_rows(data, result, "russian_enrichment")),
        "conversion_threshold_rows": table_rows(sensitivity_rows(data, result, "western_conversion")),
        "joint_enrichment": display_number(result["joint_enrichment_threshold"]["2025"] / 1_000, 3),
        "joint_enrichment_previous": display_number(result["joint_enrichment_threshold"]["2024"] / 1_000, 3),
        "conversion_loss_recent": display_number(west["2025"][0]["gross_loss"], 1),
        "conversion_loss_previous": display_number(west["2024"][0]["gross_loss"], 1),
        "reversal_share": pct(result["reversal_example"]["eu_conversion_uncovered_share_at_zero_replacement"]),
        "trade_year": trade["years"][-1],
        "trade_rows": table_rows(trade_rows(trade)),
    }
    return Template((HERE / "article.html.in").read_text(encoding="utf-8")).substitute(replacements)


def main():
    data = json.loads((HERE / "evidence_inputs.json").read_text(encoding="utf-8"))
    trade = json.loads((HERE / "out" / "nuclear_trade.json").read_text(encoding="utf-8"))
    data.update({
        "title": "Nuclear fuel chain",
        "published": True,
        "h1": TITLE,
        "deck": DECK,
        "chokepoint": {
            "product": "Reactor fuel",
            "stage": "Conversion / enrichment / fabrication",
            "mechanism": "capability",
            "secondary": "policy",
            "research": True,
            "physics": "Concentrated fuel services and design-specific fabrication. Replacement depends on the market and disruption.",
            "holder": "Rosatom leads enrichment",
            "share": "43–44% of global enrichment capacity",
            "control": "—",
            "conf": "estimate",
        },
        "calculated": calculate(data),
    })
    data["scenario_addendum"] = scenario_addendum(data)
    html = render(data, trade)
    data["sources"] = {key: {"title": label, "url": url} for key, (label, url) in data["sources"].items()}
    (HERE / "out" / "nuclear_chain.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (HERE / "nuclear-chain.html").write_text(html, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
