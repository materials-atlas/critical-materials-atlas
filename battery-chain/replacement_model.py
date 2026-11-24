"""Monthly mass balance for separately contracted NMC and LFP cell lines."""

from __future__ import annotations

from itertools import product
from math import isclose

CASES = {
    "baseline": {"disruption": False},
    "direct": {"trace_upstream": False},
    "traced": {},
    "prequalified": {"prequalified": True},
    "no_replacements": {"replacement_scale": 0},
}


def intensity(recipe):
    """Convert a source design's kilograms per nominal kWh to tonnes per GWh."""
    return {
        material: 1000 * mass_kg / recipe["design_energy_kwh"]
        for material, mass_kg in recipe["mass_kg"].items()
    }


def exposed_share(lane, trace_upstream):
    direct = lane["direct_exposure_fraction"]
    upstream = lane["upstream_exposure_within_other_fraction"] if trace_upstream else 0
    return direct + (1 - direct) * upstream


def replacement_share(lane):
    alternative = lane["alternative"]
    if not (alternative["specification_compatible"] and alternative["upstream_independent"]):
        return 0.0
    return (alternative["nameplate_fraction_of_line_need"]
            * alternative["operational_fraction"]
            * alternative["uncommitted_fraction_of_operational"])


def simulate(line, months, *, disruption=True, trace_upstream=True,
             stock_scale=1, extra_lag=0, replacement_scale=1, prequalified=False):
    unit_mass = intensity(line["recipe"])
    capacity = line["monthly_cell_limit_gwh"]
    needs = {material: amount * capacity for material, amount in unit_mass.items()}
    lanes = line["lanes"]
    stock = {material: needs[material] * lane["opening_stock_months_at_full_output"] * stock_scale
             for material, lane in lanes.items()}
    scheduled = {}
    for material, lane in lanes.items():
        exposed = exposed_share(lane, trace_upstream) if disruption else 0
        lag = 0 if prequalified else lane["alternative"]["qualification_lag_months"] + extra_lag
        safe_new = min(exposed, replacement_share(lane) * replacement_scale)
        scheduled[material] = {
            "normal_need_tonnes": needs[material],
            "unaffected_tonnes_per_month": (1 - exposed) * needs[material],
            "qualified_increment_tonnes_per_month": safe_new * needs[material],
            "first_replacement_month": lag + 1 if safe_new else None,
            "exposed_fraction": exposed,
            "stock_to_bridge_to_qualification_tonnes": (
                exposed * lag * needs[material] if safe_new else None
            ),
            "minimum_sustained_replacement_tonnes_per_month": exposed * needs[material],
            "residual_shortfall_tonnes_per_month_after_qualification": (exposed - safe_new) * needs[material],
        }

    rows = []
    for month in range(1, months + 1):
        material_flow = {}
        for material, supply in scheduled.items():
            first = supply["first_replacement_month"]
            replacement = supply["qualified_increment_tonnes_per_month"] if first and month >= first else 0
            material_flow[material] = {
                "opening_stock_tonnes": stock[material],
                "unaffected_tonnes": supply["unaffected_tonnes_per_month"],
                "replacement_tonnes": replacement,
            }
        available = {material: sum(flow.values()) for material, flow in material_flow.items()}
        limits = {material: available[material] / unit_mass[material] for material in available}
        output = min(capacity, *limits.values())
        binding = [m for m, limit in limits.items() if isclose(output, limit, abs_tol=1e-9)]
        for material, flow in material_flow.items():
            consumed = output * unit_mass[material]
            stock[material] = max(0.0, available[material] - consumed)
            flow.update({"consumed_tonnes": consumed, "closing_stock_tonnes": stock[material]})
        rows.append({"month": month, "output_gwh": output, "binding_inputs": binding, "materials": material_flow})

    total = sum(row["output_gwh"] for row in rows)
    return {"tonnes_per_gwh": unit_mass, "supply_schedule": scheduled, "months": rows, "total_gwh": total}


def calculate(inputs):
    lines = inputs["lines"]
    months = inputs["scenario_months"]
    cases = {
        key: {label: simulate(line, months, **options) for label, line in lines.items()}
        for key, options in CASES.items()
    }
    for lines_in_case in cases.values():
        for label, case in lines_in_case.items():
            baseline = cases["baseline"][label]
            case["horizon_loss_fraction"] = max(0.0, 1 - case["total_gwh"] / baseline["total_gwh"])
            for row, reference in zip(case["months"], baseline["months"]):
                row["loss_fraction"] = max(0.0, 1 - row["output_gwh"] / reference["output_gwh"])

    grid = []
    for stock, delay, availability in product(
        inputs["sensitivity"]["opening_stock_multipliers"],
        inputs["sensitivity"]["extra_qualification_months"],
        inputs["sensitivity"]["alternative_volume_multipliers"],
    ):
        grid.append({
            "opening_stock_multiplier": stock,
            "extra_qualification_months": delay,
            "alternative_volume_multiplier": availability,
            "horizon_loss_fraction": {
                label: max(0.0, 1 - simulate(
                    line, months, stock_scale=stock, extra_lag=delay, replacement_scale=availability,
                )["total_gwh"] / cases["baseline"][label]["total_gwh"])
                for label, line in lines.items()
            },
        })
    return {
        "cases": cases,
        "sensitivity_cases": grid,
        "sensitivity_loss_ranges": {
            label: [
                min(case["horizon_loss_fraction"][label] for case in grid),
                max(case["horizon_loss_fraction"][label] for case in grid),
            ]
            for label in lines
        },
    }
