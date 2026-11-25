"""Monthly material balance for one compatible heat-pump design."""
from __future__ import annotations

from itertools import product


def simulate(settings):
    """Use compressors received or drawn from stock to meet local orders."""
    p = settings
    if any(type(value) is not int or value < 0 for value in p.values()):
        raise ValueError("Model inputs must be nonnegative integer quantities")
    if not p["months"] or not p["compressors_per_unit"]:
        raise ValueError("A positive horizon and compressors per unit are required")
    if p["shock_months"] > p["months"] or p["shock_cut_pct"] > 100:
        raise ValueError("The loss must fit within the horizon and between 0% and 100%")
    if p["exposed_import_receipts"] > p["normal_import_receipts"]:
        raise ValueError("Exposed imports cannot exceed normal imports")

    stock = p["opening_stock"]
    normal = p["normal_domestic_receipts"] + p["normal_import_receipts"]
    interrupted = p["exposed_import_receipts"] * p["shock_cut_pct"] // 100
    monthly = []
    for month in range(1, p["months"] + 1):
        lost = interrupted if month <= p["shock_months"] else 0
        replacement = min(lost, p["replacement_capacity_per_month"]) if month > p["qualification_delay_months"] else 0
        receipts = normal - lost + replacement
        production = min(p["monthly_demand"], p["monthly_assembly"],
                         (stock + receipts) // p["compressors_per_unit"])
        ending = stock + receipts - production * p["compressors_per_unit"]
        monthly.append({
            "month": month, "opening_stock": stock, "lost_receipts": lost,
            "replacement_receipts": replacement, "total_receipts": receipts,
            "stock_draw": max(0, stock - ending), "ending_stock": ending,
            "production": production, "unmet_orders": p["monthly_demand"] - production,
        })
        stock = ending
    return {
        "production": sum(row["production"] for row in monthly),
        "unmet_orders": sum(row["unmet_orders"] for row in monthly),
        "monthly": monthly,
    }


def compare(settings):
    normal = simulate({**settings, "shock_months": 0})
    result = simulate(settings)
    return {**result, "matched_open_production": normal["production"],
            "production_lost_to_shock": normal["production"] - result["production"]}


def evaluate(model):
    point = model["point"]
    draws = model["sensitivity"]
    scenarios = [
        {"id": item["id"], "label": item["label"], "settings": {**point, **item["changes"]},
         **compare({**point, **item["changes"]})}
        for item in model["interventions"]
    ]
    cases = []
    fields = ("opening_stock", "qualification_delay_months", "replacement_capacity_per_month", "monthly_demand")
    for values in product(*(draws[field] for field in fields)):
        parameters = dict(zip(fields, values))
        case = compare({**point, **parameters})
        cases.append({**parameters, "production": case["production"],
                      "unmet_orders": case["unmet_orders"],
                      "production_lost_to_shock": case["production_lost_to_shock"]})
    losses = [case["production_lost_to_shock"] for case in cases]
    return {"status": "Modelled", "scenarios": scenarios, "sensitivity": cases,
            "production_lost_range": [min(losses), max(losses)]}
