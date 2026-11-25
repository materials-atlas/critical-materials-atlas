"""Build the heat-pump evidence review and model from pinned public inputs."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
from string import Template

from compressor_supply import evaluate

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "evidence_inputs.json"
TRADE = HERE / "out" / "heat_pump_trade.json"
TITLE = "What limits heat-pump supply?"
DECK = ("Europe has substantial heat-pump assembly capacity. Compatible compressors can still limit "
        "factory output, while trained installers affect how quickly equipment reaches buildings.")


def rows(items):
    return "\n".join(
        "<tr>" + f'<th scope="row">{escape(str(label))}</th>'
        + "".join(f"<td>{escape(str(cell))}</td>" for cell in cells) + "</tr>"
        for label, *cells in items
    )


def render(data, trade):
    model = data["model"]
    point = model["point"]
    result = data["model_results"]
    target = data["benchmarks"]["eu_assembly"]
    global_capacity = data["benchmarks"]["global_final_assembly"]
    scenarios = {case["id"]: case for case in result["scenarios"]}
    base_case = scenarios["shock"]
    changes = {
        "open": "Normal receipts", "shock": "Base interruption",
        "assembly": f'{scenarios["assembly"]["settings"]["monthly_assembly"]:,} units/month',
        "replacement": f'{scenarios["replacement"]["settings"]["replacement_capacity_per_month"]:,} compressors/month after qualification',
        "qualified": "No qualification delay",
        "stock": f'{scenarios["stock"]["settings"]["opening_stock"]:,} compressors at start',
    }
    scenario_rows = rows(
        (case["label"], changes[case["id"]], f'{case["production"]:,}', f'{case["unmet_orders"]:,}',
         f'{case["production_lost_to_shock"]:,}')
        for case in scenarios.values()
    )
    month_rows = rows(
        (row["month"], row["total_receipts"], row["replacement_receipts"],
         row["stock_draw"], row["ending_stock"], row["production"], row["unmet_orders"])
        for row in base_case["monthly"]
    )
    stocks = model["sensitivity"]["opening_stock"]
    delays = model["sensitivity"]["qualification_delay_months"]
    at_point = [case for case in result["sensitivity"]
                if case["monthly_demand"] == point["monthly_demand"]
                and case["replacement_capacity_per_month"] == point["replacement_capacity_per_month"]]
    losses = {(case["opening_stock"], case["qualification_delay_months"]): case["production_lost_to_shock"]
              for case in at_point}
    sources = data["sources"]
    links = {key: f'<a href="{escape(source["url"], quote=True)}">{escape(source["title"])}</a>'
             for key, source in sources.items()}
    year = trade["years"][-1]
    code, item = next(iter(trade["codes"].items()))
    snapshot = trade["years_data"][str(year)][code]
    lead = snapshot["exporters"][0]
    values = {
        "title": escape(TITLE), "deck": escape(DECK), "date": data["date"],
        "world_gw": global_capacity["global_gw_per_year"],
        "region_rows": rows((region, f"{share}%") for region, share in global_capacity["share_pct"].items()),
        "rotary_share": data["benchmarks"]["rotary_compressors"]["china_share_pct"],
        "nameplate_count": f'{target["units_per_year"] / 1e6:g}',
        "assumed_kw": target["assumed_average_kw_thermal"],
        "eu_nameplate_gw": target["reported_gw_thermal_per_year"],
        "flat_gw": target["flat_annual_deployment_gw_thermal"],
        "growth_gw": target["growth_path_2030_deployment_gw_thermal"],
        "flat_ratio": f'{data["assembly_comparison"]["coverage_of_flat_path"]:.0%}',
        "growth_ratio": f'{data["assembly_comparison"]["coverage_of_growth_path_in_2030"]:.0%}',
        "scenario_rows": scenario_rows, "month_rows": month_rows,
        "local_share": global_capacity["local_sourcing_pct_lower_bound"],
        "lost_imports_per_month": point["exposed_import_receipts"] * point["shock_cut_pct"] // 100,
        "assembly_loss": f'{scenarios["assembly"]["production_lost_to_shock"]:,}',
        "min_replacement": min(model["sensitivity"]["replacement_capacity_per_month"]),
        "max_replacement": max(model["sensitivity"]["replacement_capacity_per_month"]),
        "min_orders": f'{min(model["sensitivity"]["monthly_demand"]):,}',
        "max_orders": f'{max(model["sensitivity"]["monthly_demand"]):,}',
        **{key: f"{value:,}" for key, value in point.items()},
        "delay_head": "".join(f'<th scope="col">{delay} months</th>' for delay in delays),
        "loss_grid": rows((f"{stock:,}", *(f"{losses[stock, delay]:,}" for delay in delays)) for stock in stocks),
        "low_loss": f'{result["production_lost_range"][0]:,}',
        "high_loss": f'{result["production_lost_range"][1]:,}',
        "trade_code": escape(code), "trade_title": escape(item["title"]),
        "trade_boundary": escape(item["boundary"]), "trade_year": year,
        "trade_value": f'{snapshot["world_usd"] / 1e9:.2f}',
        "trade_lead": f'{escape(lead["name"])} · {lead["share"]:.1%}',
        **links,
    }
    return Template((HERE / "article.html.in").read_text(encoding="utf-8")).substitute(values)


def build():
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    trade = json.loads(TRADE.read_text(encoding="utf-8"))
    target = data["benchmarks"]["eu_assembly"]
    capacity_rate = target["units_per_year"] * target["assumed_average_kw_thermal"] / 1_000_000
    if capacity_rate != target["reported_gw_thermal_per_year"]:
        raise ValueError("The JRC nameplate conversion should reproduce its published benchmark")
    data.update({
        "title": "Heat-pump chain", "h1": TITLE, "deck": DECK, "published": True,
        "chokepoint": {
            "product": "Heat pumps", "stage": "Compatible compressors", "mechanism": "capability",
            "physics": "Compressor supply depends on the refrigerant, operating range, drive and qualification",
            "holder": "China (rotary)", "share": "About 90% of rotary capacity (2024)",
            "control": "—", "conf": "estimate", "research": True,
        },
        "assembly_comparison": {
            "status": "Calculated with 2025 mixed-technology capacity held constant",
            "coverage_of_flat_path": capacity_rate / target["flat_annual_deployment_gw_thermal"],
            "coverage_of_growth_path_in_2030": capacity_rate / target["growth_path_2030_deployment_gw_thermal"],
        },
        "model_results": evaluate(data["model"]),
    })
    article = render(data, trade)
    (HERE / "out" / "heat_pump_chain.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (HERE / "heat-pump-chain.html").write_text(article, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build()
