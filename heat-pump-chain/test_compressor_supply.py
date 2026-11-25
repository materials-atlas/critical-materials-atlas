"""Checks for the published heat-pump scenario and monthly stock balance."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from compressor_supply import compare, evaluate, simulate

MODEL = json.loads(Path(__file__).with_name("evidence_inputs.json").read_text(encoding="utf-8"))["model"]


class CompressorSupplyTests(unittest.TestCase):
    def test_single_draw_and_qualification(self):
        result = compare(MODEL["point"])
        months = result["monthly"]
        self.assertEqual([row["stock_draw"] for row in months], [150, 150, 0, 0, 0, 0, 0, 0])
        self.assertEqual([row["replacement_receipts"] for row in months], [0, 0, 0, 100, 100, 100, 0, 0])
        self.assertEqual([row["unmet_orders"] for row in months], [0, 0, 150, 50, 50, 50, 0, 0])
        self.assertEqual(result["production_lost_to_shock"], 300)

    def test_capacity_and_demand_are_separate_limits(self):
        p = MODEL["point"]
        open_case = simulate({**p, "shock_months": 0, "monthly_assembly": 700})
        self.assertEqual(open_case["production"], 5600)
        self.assertEqual(open_case["monthly"][1]["ending_stock"], 900)
        high_demand = compare({**p, "monthly_demand": 1200})
        self.assertEqual(high_demand["production"] + high_demand["unmet_orders"], 9600)
        self.assertLess(high_demand["production_lost_to_shock"], high_demand["unmet_orders"])

    def test_all_interventions_and_sensitivity(self):
        result = evaluate(MODEL)
        losses = {case["id"]: case["production_lost_to_shock"] for case in result["scenarios"]}
        self.assertEqual(losses, {"open": 0, "shock": 300, "assembly": 300, "replacement": 150,
                                  "qualified": 0, "stock": 0})
        self.assertEqual(result["production_lost_range"], [0, 900])
        self.assertEqual(len(result["sensitivity"]), 81)

    def test_exposure_cannot_exceed_imports(self):
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            simulate({**MODEL["point"], "exposed_import_receipts": 601})


if __name__ == "__main__":
    unittest.main()
