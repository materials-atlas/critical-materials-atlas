#!/usr/bin/env python3
"""Reproduce the illustrative PEM iridium tables and annual material balance."""
from __future__ import annotations

import csv
from collections import defaultdict
from decimal import Decimal
from itertools import product
import json
from math import ceil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ZERO = Decimal(0)


def number(value):
    return Decimal(str(value))


def requirement_tonnes(annual_gw, intensity_kg_per_mw):
    return number(annual_gw) * number(intensity_kg_per_mw)


def threshold_gw_per_year(available_t, intensity_kg_per_mw):
    return number(available_t) / number(intensity_kg_per_mw)


def frontier(settings):
    supply = number(settings["primary_output_t_per_year"])
    scenarios, thresholds = [], []
    for intensity, share in product(settings["intensity_kg_ir_per_mw"], settings["assumed_primary_shares"]):
        available = supply * number(share)
        thresholds.append({
            "intensity_kg_Ir_per_MW": intensity, "assumed_share_global_supply": share,
            "available_t_Ir_per_year": available,
            "annual_new_PEM_GW_at_equality": threshold_gw_per_year(available, intensity),
        })
    for gw, intensity, share in product(settings["annual_new_pem_gw"],
                                        settings["intensity_kg_ir_per_mw"],
                                        settings["assumed_primary_shares"]):
        demand = requirement_tonnes(gw, intensity)
        available = supply * number(share)
        scenarios.append({
            "annual_new_PEM_GW": gw, "intensity_kg_Ir_per_MW": intensity,
            "gross_demand_t_Ir_per_year": demand, "assumed_share_global_supply": share,
            "assumed_available_t_Ir_per_year": available,
            "gross_requirement_exceeds_available": demand > available,
            "shortfall_t_Ir_per_year": max(ZERO, demand - available),
        })
    return scenarios, thresholds


def interpolate(points, year):
    knots = sorted((int(key), number(value)) for key, value in points.items())
    if year <= knots[0][0]:
        return knots[0][1]
    for (start, low), (end, high) in zip(knots, knots[1:]):
        if year <= end:
            return low + (high - low) * (year - start) / (end - start)
    return knots[-1][1]


def annual_balance(pathway, settings, world_primary_t):
    """Calculate iridium required by scheduled stacks, given a fixed primary allocation."""
    p = settings
    fraction_keys = ("pem_share", "primary_share", "utilisation", "manufacturing_yield", "recovery_fraction")
    fractions = {key: number(p[key]) for key in fraction_keys}
    if any(not 0 <= value <= 1 for value in fractions.values()):
        raise ValueError("Fraction inputs must be between zero and one")
    if not all((fractions["utilisation"], fractions["manufacturing_yield"])) or p["operating_stack_hours"] <= 0:
        raise ValueError("Use positive operating life, utilisation and manufacturing yield")
    if p["plant_lifetime_years"] < 1 or p["recycling_lag_years"] < 0 or number(world_primary_t) < 0:
        raise ValueError("Use a positive plant life and nonnegative recovery lag and primary supply")

    points = pathway["new_all_electrolysis_gw_by_year"]
    years = [int(key) for key in points]
    stack_years = ceil(number(p["operating_stack_hours"]) / (8760 * fractions["utilisation"]))
    primary = number(world_primary_t) * fractions["primary_share"]
    retired_stacks = defaultdict(list)
    returns = defaultdict(Decimal)
    secondary_inventory = in_service_ir = in_service_gw = ZERO
    rows = []
    for year in range(min(years), max(years) + 1):
        intensity = interpolate(p["intensity_by_year"], year)
        total_new = interpolate(points, year)
        new_pem = total_new * fractions["pem_share"]
        ending = retired_stacks.pop(year, [])
        # A stack is removed either at stack end-of-life or when the host plant closes.
        retired_ir = sum((embedded for _, embedded, _ in ending), ZERO)
        closed_pem = sum((gw for gw, _, plant_end in ending if plant_end == year), ZERO)
        replacement = [(gw, plant_end) for gw, _, plant_end in ending if plant_end > year]
        returning = retired_ir * fractions["recovery_fraction"]
        returns[year + p["recycling_lag_years"]] += returning
        received = returns.pop(year, ZERO)
        secondary_inventory += received

        fitted = [(new_pem, year + p["plant_lifetime_years"]), *replacement]
        embedded_ir = ZERO
        for gw, plant_end in fitted:
            if gw:
                embedded = gw * intensity
                retired_stacks[min(year + stack_years, plant_end)].append((gw, embedded, plant_end))
                embedded_ir += embedded
        manufacturing_input = embedded_ir / fractions["manufacturing_yield"]
        used_secondary = min(secondary_inventory, manufacturing_input)
        secondary_inventory -= used_secondary
        required_primary = manufacturing_input - used_secondary
        in_service_gw += new_pem - closed_pem
        in_service_ir += embedded_ir - retired_ir
        rows.append({
            "year": year, "all_new_electrolysis_gw": total_new, "new_pem_gw": new_pem,
            "replacement_stack_gw": sum((gw for gw, _ in replacement), ZERO),
            "retired_plant_gw": closed_pem, "planned_installed_pem_gw": in_service_gw,
            "intensity_kg_ir_per_mw": intensity, "embedded_ir_t": embedded_ir,
            "in_service_ir_t": in_service_ir, "retired_ir_t": retired_ir,
            "recycled_ir_arrived_t": received, "recycled_ir_used_t": used_secondary,
            "recycled_ir_inventory_t": secondary_inventory, "gross_ir_input_t": manufacturing_input,
            "primary_ir_required_t": required_primary, "primary_ir_available_t": primary,
            "gap_t": max(ZERO, required_primary - primary),
        })
    return {"stack_calendar_years": stack_years, "rows": rows}


def summarise(balance):
    rows = balance["rows"]
    return {
        "stack_calendar_years": balance["stack_calendar_years"],
        "cumulative_primary_ir_required_t": sum(row["primary_ir_required_t"] for row in rows),
        "cumulative_gap_t": sum(row["gap_t"] for row in rows),
        "peak_gap_t": max(row["gap_t"] for row in rows),
        "first_gap_year": next((row["year"] for row in rows if row["gap_t"] > 0), None),
    }


def evaluate(inputs):
    static = inputs["static_scenarios"]
    scenarios, thresholds = frontier(static)
    supply = static["primary_output_t_per_year"]
    settings = inputs["annual"]
    reference = settings["assumptions"]
    middle = settings["pathways"]["middle"]
    pathways = {key: annual_balance(path, reference, supply) for key, path in settings["pathways"].items()}
    mitigation = {}
    for key, case in settings["mitigation"].items():
        dataset = annual_balance(middle, {**reference, **case["changes"]}, supply)
        mitigation[key] = {"label": case["label"], **summarise(dataset), "rows": dataset["rows"]}
    sensitivity = []
    axes = settings["sensitivity"]
    for values in product(*axes.values()):
        combination = dict(zip(axes, values))
        case = annual_balance(middle, {**reference, **combination}, supply)
        sensitivity.append({**combination, **summarise(case)})
    market_case = annual_balance(middle, reference, inputs["benchmarks"]["market"]["primary_supply_t"])
    return {
        "status": "Illustrative model",
        "scenario_matrix": scenarios, "thresholds": thresholds, "pathways": pathways,
        "mitigation": mitigation, "annual_sensitivity": sensitivity,
        "market_supply_comparison": summarise(market_case),
    }


def csv_value(value):
    if isinstance(value, Decimal):
        return f"{value:.6f}".rstrip("0").rstrip(".") or "0"
    return value


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: csv_value(value) for key, value in row.items()} for row in rows)


def write_tables(directory, result):
    write_csv(directory / "illustrative_scenario_matrix.csv", result["scenario_matrix"])
    write_csv(directory / "illustrative_thresholds.csv", result["thresholds"])
    write_csv(directory / "illustrative_annual_flows.csv", [
        {"pathway": name, **row} for name, path in result["pathways"].items() for row in path["rows"]
    ])
    write_csv(directory / "illustrative_mitigation.csv", [
        {"case": name, **row} for name, case in result["mitigation"].items() for row in case["rows"]
    ])
    write_csv(directory / "illustrative_sensitivity.csv", result["annual_sensitivity"])


if __name__ == "__main__":
    data = json.loads((HERE / "evidence_inputs.json").read_text(encoding="utf-8"))
    write_tables(HERE / "out", evaluate(data))
