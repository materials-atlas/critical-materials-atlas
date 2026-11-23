"""Calculate earliest commissioning and usable IT power for the documented scenarios."""
from __future__ import annotations

from datetime import date
from graphlib import TopologicalSorter
from itertools import product
import json
from pathlib import Path

ASSUMPTIONS = Path(__file__).with_name("deployment_assumptions.json")


def schedule(activities, overrides):
    """Earliest finishes under finish-to-start dependencies, with parallel paths."""
    tasks = {task["id"]: task for task in activities}
    if len(tasks) != len(activities):
        raise ValueError("Activity IDs must be unique")
    if overrides.keys() - tasks.keys():
        raise ValueError("Unknown activity in duration overrides")
    graph = {key: task["predecessors"] for key, task in tasks.items()}
    if any(set(predecessors) - tasks.keys() for predecessors in graph.values()):
        raise ValueError("Unknown predecessor")
    finishes = {}
    starts = {}
    for key in TopologicalSorter(graph).static_order():
        months = overrides.get(key, tasks[key]["months"])
        if type(months) is not int or months < 0:
            raise ValueError(f"Expected nonnegative integer months for {key}")
        starts[key] = max((finishes[parent] for parent in graph[key]), default=0)
        finishes[key] = starts[key] + months

    critical = {"commissioning"}
    for key in reversed(finishes):
        if key in critical:
            critical.update(parent for parent in graph[key] if finishes[parent] == starts[key])
    return finishes["commissioning"], [key for key in finishes if key in critical], {
        key: {"start": starts[key], "finish": finishes[key]} for key in tasks
    }


def month_at(start_month, offset):
    year, month = map(int, start_month.split("-"))
    date(year, month, 1)  # validate the configured month
    year, month_index = divmod(year * 12 + month - 1 + offset, 12)
    return f"{year:04d}-{month_index + 1:02d}"


def usable_it_load(project, pue, firm_power):
    """Capacity once the modeled phase has passed commissioning."""
    if pue < 1 or firm_power < 0:
        raise ValueError("Expected PUE >= 1 and nonnegative firm power")
    return min(project["it_load_mw"], project["cooling_it_limit_mw"],
               project["installed_it_mw"], firm_power / pue)


def evaluate(assumptions):
    project = assumptions["project"]
    activities = assumptions["activities"]
    pue = project["design_pue"]
    results = {}
    for scenario in assumptions["scenarios"]:
        month, critical, timeline = schedule(activities, scenario["durations"])
        firm = scenario.get("firm_power_mw", project["firm_power_mw"])
        results[scenario["id"]] = {
            "label": scenario["label"],
            "commissioning_month": month,
            "calendar_month": month_at(project["start_month"], month),
            "usable_it_mw": round(usable_it_load(project, pue, firm), 2),
            "critical_activities": critical,
            "timeline": timeline,
        }
    for scenario in assumptions["scenarios"]:
        comparator = scenario.get("compare_to")
        if comparator:
            result = results[scenario["id"]]
            result["compare_to"] = comparator
            result["months_earlier"] = results[comparator]["commissioning_month"] - result["commissioning_month"]
    sensitivity = assumptions["sensitivity"]
    outcomes = [
        schedule(activities, dict(zip(sensitivity, durations)))[0]
        for durations in product(*sensitivity.values())
    ]
    return {
        "version": assumptions["version"],
        "evidence_type": assumptions["evidence_type"],
        "required_facility_mw": round(project["it_load_mw"] * pue, 2),
        "scenarios": results,
        "sensitivity": {"combinations": len(outcomes), "earliest_month": min(outcomes),
                        "latest_month": max(outcomes)},
        "pue_sensitivity": [
            {"pue": value, "facility_mw": round(project["it_load_mw"] * value, 2),
             "usable_it_mw": round(usable_it_load(project, value, project["firm_power_mw"]), 2)}
            for value in assumptions["pue_sensitivity"]
        ],
    }


def build():
    return evaluate(json.loads(ASSUMPTIONS.read_text(encoding="utf-8")))


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
