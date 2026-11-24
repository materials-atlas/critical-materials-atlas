"""Dated battery-model sensitivity and public qualification timing check."""

from datetime import date
from itertools import product

from replacement_model import simulate


def earliest_guided_lag(milestones):
    """Index modeled month one to the calendar month of the qualification sample."""
    sample = date.fromisoformat(milestones["mass_production_sample"])
    sales = date.fromisoformat(milestones["first_month_of_sales_guidance"] + "-01")
    return (sales.year - sample.year) * 12 + sales.month - sample.month


def graphite_timing_limit(line, lag):
    lanes = line["lanes"]
    graphite = lanes["graphite"]
    alternative = graphite["alternative"]
    scheduled = {**alternative, "qualification_lag_months": max(lag, alternative["qualification_lag_months"])}
    return {**line, "lanes": {**lanes, "graphite": {**graphite, "alternative": scheduled}}}


def calculate_followup(inputs, original_model, assumptions):
    lines = inputs["lines"]
    months = inputs["scenario_months"]
    baseline = original_model["cases"]["baseline"]
    start = {label: row["horizon_loss_fraction"]
             for label, row in original_model["cases"]["traced"].items()}

    def losses(options):
        return {
            label: 1 - simulate(line, months, **options)["total_gwh"] / baseline[label]["total_gwh"]
            for label, line in lines.items()
        }

    comparisons = {
        field: [{"value": value, "loss_fraction": losses({field: value})} for value in values]
        for field, values in assumptions["one_at_a_time"].items()
    }

    effects = {
        label: {
            field: max(row["loss_fraction"][label] for row in rows)
            - min(row["loss_fraction"][label] for row in rows)
            for field, rows in comparisons.items()
        } for label in lines
    }
    interactions = {}
    for name, axes in assumptions["interactions"].items():
        rows = []
        for levels in product(*axes.values()):
            options = dict(zip(axes, levels, strict=True))
            rows.append({"options": options, "loss_fraction": losses(options)})
        interactions[name] = rows

    lag = earliest_guided_lag(assumptions["graphite_milestones"])
    ramp = assumptions["ramp_fractions"]
    scenarios = {"gradual_ramp": {}, "public_graphite_timing": {}}
    for label, line in lines.items():
        for key, result in (
            ("gradual_ramp", simulate(line, months, replacement_ramp=ramp)),
            ("public_graphite_timing", simulate(graphite_timing_limit(line, lag), months)),
        ):
            result["horizon_loss_fraction"] = 1 - result["total_gwh"] / baseline[label]["total_gwh"]
            scenarios[key][label] = result

    return {
        "date": assumptions["date"],
        "scope": "Selected cathode active material and graphite flows on two hypothetical cell lines",
        "assumptions": assumptions,
        "graphite_no_sales_before_month": lag + 1,
        "traced_baseline_loss_fraction": start,
        "one_at_a_time": comparisons,
        "tested_loss_spans": effects,
        "interactions": interactions,
        "scenarios": scenarios,
    }
