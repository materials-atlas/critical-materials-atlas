"""Monthly material balance for one compatible heat-pump design."""
from __future__ import annotations

from itertools import product


def simulate(settings, *, recovery=None):
    """Meet orders using receipts and stock, with optional carryover and recovery."""
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
    backlog = 0
    for month in range(1, p["months"] + 1):
        lost = interrupted if month <= p["shock_months"] else 0
        replacement = min(lost, p["replacement_capacity_per_month"]) if month > p["qualification_delay_months"] else 0
        receipts = normal - lost + replacement
        extra = recovery["extra_receipts"] if recovery and month >= recovery["starts_in"] else 0
        receipts += extra
        due = p["monthly_demand"] + backlog
        production = min(due, p["monthly_assembly"], (stock + receipts) // p["compressors_per_unit"])
        ending = stock + receipts - production * p["compressors_per_unit"]
        unfilled = due - production
        row = {
            "month": month, "opening_stock": stock, "lost_receipts": lost,
            "replacement_receipts": replacement, "total_receipts": receipts,
            "stock_draw": max(0, stock - ending), "ending_stock": ending,
            "production": production,
        }
        if recovery is None:
            row["unmet_orders"] = unfilled
        else:
            requested = recovery["requested_cancellations"] if month == recovery["cancel_in"] else 0
            cancelled = min(requested, unfilled)
            opening_backlog = backlog
            backlog = unfilled - cancelled
            row.update(opening_backlog=opening_backlog, new_orders=p["monthly_demand"],
                       extra_receipts=extra, cancelled_orders=cancelled, closing_backlog=backlog)
        monthly.append(row)
        stock = ending
    if recovery is not None:
        return {
            "production": sum(row["production"] for row in monthly),
            "cancelled_orders": sum(row["cancelled_orders"] for row in monthly),
            "closing_backlog": backlog,
            "monthly": monthly,
        }
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


def evaluate_recovery(point, assumptions):
    initial_months = point["months"]
    if assumptions["through_month"] <= initial_months:
        raise ValueError("The follow-up must extend beyond the original horizon")
    settings = {**point, "months": assumptions["through_month"]}
    cases = []
    for option in assumptions["cases"]:
        if any(type(option[key]) is not int or option[key] < 0 for key in ("extra_receipts", "cancellations")):
            raise ValueError("Extra receipts and cancellations must be nonnegative integer quantities")
        recovery = {
            "starts_in": initial_months + 1,
            "extra_receipts": option["extra_receipts"],
            "requested_cancellations": option["cancellations"],
            "cancel_in": initial_months,
        }
        result = simulate(settings, recovery=recovery)
        monthly = result["monthly"]
        initial = monthly[:initial_months]
        later = monthly[initial_months:]
        backlog_at_end = initial[-1]["closing_backlog"]
        cleared = next((row["month"] for row in later if row["closing_backlog"] == 0), None)
        cases.append({
            "label": option["label"],
            "assumptions": recovery,
            **result,
            "delivered_by_initial_horizon": sum(row["production"] for row in initial),
            "backlog_at_initial_horizon": backlog_at_end,
            "peak_backlog": max(row["closing_backlog"] for row in monthly),
            "clearance_month": cleared if backlog_at_end else None,
        })
    return {"status": "Modelled", "initial_months": initial_months, **assumptions, "cases": cases}
