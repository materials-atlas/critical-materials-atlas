"""Maximum manufacturing throughput for one compatible crystalline-silicon route."""
from __future__ import annotations

from itertools import product
import json
from math import inf, isclose, isfinite, prod
from pathlib import Path

INPUTS = Path(__file__).with_name("evidence_inputs.json")
STAGES = ("polysilicon", "ingots", "wafers", "cells", "modules")


def throughput(capacity, months, yields, imports=None, stocks=None):
    """Compute the maximum final output in GW-equivalent during the horizon.

    Capacity and import rates are annual. Stock quantities are available once.
    A missing capacity (None) relaxes that constraint for an upper bound.
    Imports and stocks bypass domestic production at the stage they enter.
    """
    imports = imports or {}
    stocks = stocks or {}
    if not isfinite(months) or months <= 0:
        raise ValueError("The horizon must be a positive number of months")
    if set(capacity) != set(STAGES) or set(yields) != set(STAGES[1:]):
        raise ValueError("Supply one capacity per stage and one yield per conversion")
    if (imports.keys() | stocks.keys()) - set(STAGES[:-1]):
        raise ValueError("Substitute intermediate inputs only")
    rates = [value for value in capacity.values() if value is not None]
    rates += list(imports.values()) + list(stocks.values())
    if any(not isfinite(value) or value < 0 for value in rates):
        raise ValueError("Capacity, imports and stocks must be finite and nonnegative")
    if any(not 0 < value <= 1 for value in yields.values()):
        raise ValueError("Conversion yields must be in (0, 1]")

    years = months / 12
    available = inf
    stages = {}
    limiting = []
    for stage in STAGES:
        rate = capacity[stage]
        limit = inf if rate is None else rate * years
        input_limit = available * yields.get(stage, 1)
        domestic = min(limit, input_limit)
        if isfinite(limit):
            if isclose(limit, input_limit):
                limiting.append(stage)
            elif limit < input_limit:
                limiting = [stage]
        available = domestic + imports.get(stage, 0) * years + stocks.get(stage, 0)
        stages[stage] = {
            "domestic_output_ceiling": domestic,
            "available_to_next_stage": available,
        }
    return {"module_output_gw": stages["modules"]["domestic_output_ceiling"],
            "limiting_stage_capacities": limiting, "stages": stages}


def wafer_route(capacity, assumptions, exposure, scenario):
    loss = scenario["loss_fraction"] * exposure
    replacement = scenario["replace_fraction_of_lost"]
    normal = assumptions["normal_wafer_import_rate_gw_per_year"]
    unreplaced = normal * loss * (1 - replacement)
    stock_draw = min(scenario["opening_wafer_stock_gw"], unreplaced * assumptions["months"] / 12)
    return throughput(
        capacity, assumptions["months"], assumptions["yields"],
        {"wafers": normal - unreplaced}, {"wafers": stock_draw},
    )


def evaluate(data):
    capacity = data["europe_capacity"]["annual_gw_equivalent"]
    assumptions = data["illustration"]
    months = assumptions["months"]
    yields = assumptions["yields"]
    point = assumptions["point"]
    for fraction in [point["exposed_import_share"], *assumptions["exposed_share_range"],
                     *[scenario[key] for scenario in assumptions["scenarios"].values()
                       for key in ("loss_fraction", "replace_fraction_of_lost")]]:
        if not 0 <= fraction <= 1:
            raise ValueError("Exposure, loss and replacement fractions must be in [0, 1]")
    # Unit yields isolate the capacity ceiling independently of the scenario yields.
    unity = dict.fromkeys(STAGES[1:], 1)
    upper = throughput(capacity, 12, unity)["module_output_gw"]
    point_capacity = {**capacity, "ingots": point["operable_ingots_gw_per_year"]}
    open_case = assumptions["scenarios"]["open"]
    point_open = wafer_route(point_capacity, assumptions, point["exposed_import_share"], open_case)["module_output_gw"]
    varied = list(product(assumptions["exposed_share_range"], assumptions["operable_ingots_range_gw_per_year"]))
    scenarios = {}
    for key, scenario in assumptions["scenarios"].items():
        outputs, changes = [], []
        for exposure, ingots in varied:
            available_capacity = {**capacity, "ingots": ingots}
            base = wafer_route(available_capacity, assumptions, exposure, open_case)["module_output_gw"]
            output = wafer_route(available_capacity, assumptions, exposure, scenario)["module_output_gw"]
            outputs.append(output)
            changes.append(base - output)
        point_flow = wafer_route(point_capacity, assumptions, point["exposed_import_share"], scenario)
        point_output = point_flow["module_output_gw"]
        scenarios[key] = {
            "label": scenario["label"], "point_output_gw": point_output,
            "point_change_from_open_gw": point_open - point_output,
            "point_limiting_stage_capacities": point_flow["limiting_stage_capacities"],
            "output_range_gw": [min(outputs), max(outputs)],
            "loss_range_gw": [min(changes), max(changes)],
        }

    severe = assumptions["scenarios"]["severe"]
    severe_output = scenarios["severe"]["point_output_gw"]
    increments = {
        stage: wafer_route({**point_capacity, stage: point_capacity[stage] + 1},
                           assumptions, point["exposed_import_share"], severe)["module_output_gw"] - severe_output
        for stage in STAGES
    }
    joint_capacity = {**point_capacity, "ingots": point_capacity["ingots"] + 1,
                      "wafers": point_capacity["wafers"] + 1}
    joint_gain = wafer_route(joint_capacity, assumptions, point["exposed_import_share"], severe)["module_output_gw"] - severe_output
    target = point_open * assumptions["policy_target_fraction"]
    wafer_needed = max(0, (target - severe_output) / prod(yields[k] for k in ("cells", "modules")))
    return {
        "closed_route": {"upper_bound_gw_per_year": upper,
                         "share_of_module_nameplate": upper / capacity["modules"]},
        "scenario_months": months, "scenarios": scenarios,
        "marginal_one_gw_annual_severe": increments,
        "paired_ingot_wafer_one_gw_annual_gain": joint_gain,
        "policy_comparison": {
            "target_fraction_of_open": assumptions["policy_target_fraction"],
            "target_module_output_gw": target,
            "additional_qualified_wafer_supply_gw": wafer_needed,
            "additional_annual_compatible_capacity_gw": wafer_needed * 12 / months,
        },
    }


def evaluate_followup(data):
    """Vary the same severe shock and calculate separate EU-27 supply cases."""
    capacity = data["europe_capacity"]["annual_gw_equivalent"]
    assumptions = data["illustration"]
    months = assumptions["months"]
    severe = assumptions["scenarios"]["severe"]
    min_share, max_share = assumptions["exposed_share_range"]
    shares = [min_share + (max_share - min_share) * step / 4 for step in range(5)]
    min_ingots, max_ingots = assumptions["operable_ingots_range_gw_per_year"]
    ingot_rates = [min_ingots + (max_ingots - min_ingots) * step / 3 for step in range(4)]
    outputs = [
        [wafer_route({**capacity, "ingots": ingots}, assumptions, share, severe)["module_output_gw"]
         for share in shares]
        for ingots in ingot_rates
    ]

    inventory = data["eu27_inventory"]
    eu_capacity = inventory["operating_gwp_per_year"]
    # Treat the compatible fraction as 100% and yields as unity to bound output.
    unity = dict.fromkeys(STAGES[1:], 1)
    wafer_rates = [0, eu_capacity["cells"]]
    eu_cases = [
        {"qualified_wafer_import_gw_per_year": rate,
         "module_output_gw": throughput(eu_capacity, months, unity, {"wafers": rate})["module_output_gw"]}
        for rate in wafer_rates
    ]
    return {
        "date": "2026-11-24",
        "status": "Modelled",
        "severe_shock_grid": {
            "region": data["europe_capacity"]["region"],
            "months": months,
            "assumed_wafer_import_gw_per_year": assumptions["normal_wafer_import_rate_gw_per_year"],
            "fixed_wafer_nameplate_gw_per_year": capacity["wafers"],
            "exposed_share_of_assumed_wafer_imports": shares,
            "usable_domestic_ingot_gw_per_year": ingot_rates,
            "module_output_gw": outputs,
        },
        "eu27_sourcing_cases": {
            "scope": inventory["scope"], "reference_month": inventory["reference_month"],
            "capacity_source": inventory["source"], "months": months, "cases": eu_cases,
            "assumptions": "Unit yields, full availability and compatibility of operating capacity, no stocks or other intermediate imports. Wafer receipts are hypothetical.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(json.loads(INPUTS.read_text(encoding="utf-8"))), indent=2))
