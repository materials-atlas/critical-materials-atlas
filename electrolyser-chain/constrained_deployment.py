"""Illustrative PEM deployment with a budget for metal obtained outside the fleet."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_DOWN
from itertools import product
from math import ceil

from constraint_frontier import ZERO, annual_balance, interpolate, number, summarise


def market_budget(market):
    """All flows are on the same annual basis and exclude returns from this fleet."""
    primary, releases, external, competing, stock = (
        number(market[name]) for name in (
            "mine_output_t", "stock_released_t", "external_recycling_t",
            "other_net_demand_t", "stock_added_t",
        )
    )
    if any(flow < 0 for flow in (primary, releases, external, competing, stock)):
        raise ValueError("Enter each market flow as a nonnegative quantity")
    return max(ZERO, primary + releases + external - competing - stock)


def constrained_balance(pathway, settings, available_t):
    """Fit replacements before new projects. Defer any capacity without metal."""
    p = settings
    available_t = number(available_t)
    points = pathway["new_all_electrolysis_gw_by_year"]
    start, end = min(map(int, points)), max(map(int, points))
    yield_fraction = number(p["manufacturing_yield"])
    stack_years = ceil(number(p["operating_stack_hours"]) / (8760 * number(p["utilisation"])))
    recovery_fraction = number(p["recovery_fraction"])
    retirements = defaultdict(list)
    returns = defaultdict(Decimal)
    pending_replacements = []
    new_queue = recovered_stock = active = ZERO
    rows = []

    for year in range(start, end + 1):
        scheduled_new = interpolate(points, year) * number(p["pem_share"])
        intensity = interpolate(p["intensity_by_year"], year)
        if intensity <= 0:
            raise ValueError("This PEM model requires positive elemental iridium loading")

        retired = retirements.pop(year, [])
        retired_gw = sum((gw for gw, _, _ in retired), ZERO)
        retired_ir = sum((metal for _, _, metal in retired), ZERO)
        returns[year + p["recycling_lag_years"]] += retired_ir * recovery_fraction
        received = returns.pop(year, ZERO)
        recovered_stock += received

        # A plant with an expired stack remains eligible for replacement until it closes.
        pending_replacements = [(gw, year_end) for gw, year_end in pending_replacements if year_end > year]
        pending_replacements.extend((gw, year_end) for gw, year_end, _ in retired if year_end > year)
        replacement_due = sum((gw for gw, _ in pending_replacements), ZERO)
        new_queue += scheduled_new

        requested_gw = replacement_due + new_queue
        gross_if_all_fitted = requested_gw * intensity / yield_fraction
        resources = available_t + recovered_stock
        if gross_if_all_fitted <= resources:
            capacity_left = requested_gw
        else:
            capacity_left = (resources * yield_fraction / intensity).quantize(
                Decimal("0.000000001"), rounding=ROUND_DOWN
            )

        fitted, still_pending = [], []
        for gw, year_end in pending_replacements:
            allocated = min(gw, capacity_left)
            capacity_left -= allocated
            if allocated:
                fitted.append((allocated, year_end))
            if allocated < gw:
                still_pending.append((gw - allocated, year_end))
        pending_replacements = still_pending
        replacement_gw = sum((gw for gw, _ in fitted), ZERO)

        commissioned = min(new_queue, capacity_left)
        new_queue -= commissioned
        if commissioned:
            fitted.append((commissioned, year + p["plant_lifetime_years"]))
        for gw, year_end in fitted:
            retirements[min(year + stack_years, year_end)].append((gw, year_end, gw * intensity))

        gross_input = (commissioned + replacement_gw) * intensity / yield_fraction
        recycled_used = min(recovered_stock, gross_input)
        recovered_stock -= recycled_used
        active += commissioned + replacement_gw - retired_gw

        rows.append({
            "year": year, "scheduled_new_gw": scheduled_new, "commissioned_new_gw": commissioned,
            "queued_new_gw": new_queue, "replacement_due_gw": replacement_due,
            "fitted_replacement_gw": replacement_gw, "retired_stack_gw": retired_gw,
            "inactive_awaiting_replacement_gw": sum((gw for gw, _ in pending_replacements), ZERO),
            "active_pem_gw": active, "retired_ir_t": retired_ir,
            "fleet_ir_returned_t": received, "fleet_ir_used_t": recycled_used,
            "fleet_ir_stock_t": recovered_stock, "gross_ir_input_t": gross_input,
            "market_ir_used_t": gross_input - recycled_used, "market_ir_available_t": available_t,
        })
    return rows


def evaluate_followup(inputs):
    followup = inputs["second_review"]
    base = followup["reference"]
    market_inputs = followup["market"]
    reference = inputs["annual"]["assumptions"]
    points = inputs["annual"]["pathways"]["middle"]["new_all_electrolysis_gw_by_year"]
    first_year = str(min(map(int, points)))

    def comparison(changes=None, *, detail=False):
        settings = {**base, **(changes or {})}
        market = {key: settings.get(key, value) for key, value in market_inputs.items()}
        budget = market_budget(market)
        # Use a common budget for the original demand calculation and the constrained alternative.
        p = {**reference, **{key: value for key, value in settings.items() if key in reference},
             "primary_share": 1, "intensity_by_year": {first_year: settings["ir_kg_per_mw"]}}
        pathway = {"new_all_electrolysis_gw_by_year": {
            year: number(value) * number(settings["deployment_scale"])
            for year, value in points.items()
        }}
        demand = annual_balance(pathway, p, budget)
        constrained = constrained_balance(pathway, p, budget)
        demand_rows = demand["rows"]
        totals = summarise(demand)
        result = {
            "market_budget_t_per_year": budget,
            "first_gap_year": totals["first_gap_year"],
            "gross_demand_t": sum(row["gross_ir_input_t"] for row in demand_rows),
            "sum_annual_gaps_t": totals["cumulative_gap_t"],
            "scheduled_new_gw": sum(row["scheduled_new_gw"] for row in constrained),
            "commissioned_new_gw": sum(row["commissioned_new_gw"] for row in constrained),
            "queued_new_gw": constrained[-1]["queued_new_gw"],
            "active_gw": constrained[-1]["active_pem_gw"],
            "inactive_awaiting_replacement_gw": constrained[-1]["inactive_awaiting_replacement_gw"],
        }
        if detail:
            result.update(years=[
                {**row, "unconstrained_gross_ir_t": demand_row["gross_ir_input_t"],
                 "unconstrained_market_ir_required_t": demand_row["primary_ir_required_t"],
                 "unconstrained_gap_t": demand_row["gap_t"],
                 "unconstrained_active_pem_gw": demand_row["planned_installed_pem_gw"]}
                for row, demand_row in zip(constrained, demand_rows, strict=True)
            ])
        return result

    cases = [
        {**case, **comparison({"ir_kg_per_mw": case["ir_kg_per_mw"]}, detail=True)}
        for case in followup["loading_cases"]
    ]
    factors = followup["sensitivity"]
    sensitivity = [
        {"parameter": key, "label": bounds["label"],
         "low": {"value": bounds["low"], **comparison({key: bounds["low"]})},
         "high": {"value": bounds["high"], **comparison({key: bounds["high"]})}}
        for key, bounds in factors.items()
    ]
    interactions = []
    for pair in followup["interactions"]:
        left, right = pair["parameters"]
        cases_for_pair = [
            {"left": a, "right": b, **comparison({left: a, right: b})}
            for a, b in product((factors[left]["low"], factors[left]["high"]),
                                (factors[right]["low"], factors[right]["high"]))
        ]
        interactions.append({**pair, "cases": cases_for_pair})
    return {"status": "Modelled", "reference": comparison(), "loading_cases": cases,
            "sensitivity": sensitivity, "interactions": interactions}
