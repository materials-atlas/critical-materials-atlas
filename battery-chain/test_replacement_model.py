"""Reproduce battery scenarios and check physical balances from the pinned inputs."""

import json
import math
from pathlib import Path
import unittest

from replacement_followup import calculate_followup
from replacement_model import calculate, simulate


HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


class ReplacementModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = read("evidence_inputs.json")
        cls.assumptions = read("followup_inputs.json")
        cls.released = read("out/battery_chain.json")
        cls.model = calculate(cls.inputs)
        cls.followup = calculate_followup(cls.inputs, cls.model, cls.assumptions)

    def test_reproduce_released_results(self):
        self.assertEqual(self.model, self.released["model"])
        self.assertEqual(self.followup, self.released["review_addendum"])
        for key, expected in {
            "direct": (0.125, 0.28),
            "traced": (0.2325, 0.38),
            "no_replacements": (0.6375, 0.65),
        }.items():
            for chemistry, loss in zip(("NMC811", "LFP"), expected, strict=True):
                self.assertAlmostEqual(self.model["cases"][key][chemistry]["horizon_loss_fraction"], loss)

    def test_monthly_physical_balances(self):
        cases = {**self.model["cases"], **self.followup["scenarios"]}
        for name, case in cases.items():
            for chemistry, result in case.items():
                previous_stock = {}
                capacity = self.inputs["lines"][chemistry]["monthly_cell_limit_gwh"]
                for month in result["months"]:
                    with self.subTest(case=name, chemistry=chemistry, month=month["month"]):
                        output = month["output_gwh"]
                        self.assertGreaterEqual(output, 0)
                        self.assertLessEqual(output, capacity + 1e-9)
                        for material, flow in month["materials"].items():
                            opening = flow["opening_stock_tonnes"]
                            closing = flow["closing_stock_tonnes"]
                            consumed = flow["consumed_tonnes"]
                            self.assertGreaterEqual(opening, 0)
                            self.assertGreaterEqual(closing, 0)
                            if material in previous_stock:
                                self.assertAlmostEqual(opening, previous_stock[material])
                            available = opening + flow["unaffected_tonnes"] + flow["replacement_tonnes"]
                            self.assertAlmostEqual(available, consumed + closing)
                            self.assertAlmostEqual(consumed, output * result["tonnes_per_gwh"][material])
                            first = result["supply_schedule"][material]["first_replacement_month"]
                            if first is None or month["month"] < first:
                                self.assertEqual(flow["replacement_tonnes"], 0)
                            previous_stock[material] = closing
                self.assertAlmostEqual(result["total_gwh"], sum(m["output_gwh"] for m in result["months"]))

    def test_replacement_ramp_and_guided_calendar(self):
        scenarios = self.followup["scenarios"]
        self.assertEqual(self.followup["graphite_no_sales_before_month"], 14)
        for chemistry, expected in {"NMC811": (0.33375, 0.6375), "LFP": (0.4925, 0.525)}.items():
            ramped = scenarios["gradual_ramp"][chemistry]
            guided = scenarios["public_graphite_timing"][chemistry]
            self.assertAlmostEqual(ramped["horizon_loss_fraction"], expected[0])
            self.assertAlmostEqual(guided["horizon_loss_fraction"], expected[1])
            self.assertEqual(guided["supply_schedule"]["graphite"]["first_replacement_month"], 14)
            self.assertTrue(all(m["materials"]["graphite"]["replacement_tonnes"] == 0 for m in guided["months"]))
            for material, line in ramped["supply_schedule"].items():
                first = line["first_replacement_month"] - 1
                amount = line["qualified_increment_tonnes_per_month"]
                for i, share in enumerate(self.assumptions["ramp_fractions"]):
                    replacement = ramped["months"][first + i]["materials"][material]["replacement_tonnes"]
                    self.assertAlmostEqual(replacement, amount * share)

    def test_alternative_requires_compatibility_and_upstream_independence(self):
        line = self.inputs["lines"]["NMC811"]
        graphite = line["lanes"]["graphite"]
        for gate in ("specification_compatible", "upstream_independent"):
            replacement = {**graphite["alternative"], gate: False}
            lanes = {**line["lanes"], "graphite": {**graphite, "alternative": replacement}}
            result = simulate({**line, "lanes": lanes}, self.inputs["scenario_months"])
            self.assertIsNone(result["supply_schedule"]["graphite"]["first_replacement_month"])
            self.assertTrue(all(m["materials"]["graphite"]["replacement_tonnes"] == 0 for m in result["months"]))

    def test_sensitivity_baseline_and_interactions(self):
        comparisons = self.followup["one_at_a_time"]
        for axis, base in (("stock_scale", 1), ("extra_lag", 0), ("replacement_scale", 1)):
            row = next(r for r in comparisons[axis] if r["value"] == base)
            for name, loss in row["loss_fraction"].items():
                self.assertAlmostEqual(loss, self.followup["traced_baseline_loss_fraction"][name])
        effects = self.followup["tested_loss_spans"]
        self.assertAlmostEqual(max(effects["NMC811"].values()), effects["NMC811"]["extra_lag"])
        self.assertAlmostEqual(max(effects["LFP"].values()), effects["LFP"]["stock_scale"])

        def delay_penalty(rows, axis, value, chemistry):
            minimum, maximum = [
                r["loss_fraction"][chemistry] for r in rows if r["options"][axis] == value
            ]
            return maximum - minimum

        interactions = self.followup["interactions"]
        stock = interactions["opening_stock_and_delay"]
        volume = interactions["replacement_volume_and_delay"]
        for chemistry in effects:
            self.assertAlmostEqual(delay_penalty(stock, "stock_scale", 0.5, chemistry),
                                   delay_penalty(stock, "stock_scale", 2, chemistry))
            self.assertFalse(math.isclose(delay_penalty(volume, "replacement_scale", 0.5, chemistry),
                                          delay_penalty(volume, "replacement_scale", 1, chemistry)))

    def test_parameter_evidence_categories_and_sources(self):
        provenance = self.assumptions["provenance"]
        sources = {**self.released["sources"], **self.assumptions["sources"]}
        for category in ("observed", "externally_estimated"):
            for key in provenance[category]:
                self.assertTrue(sources[key]["url"].startswith("https://"))
        dates = {path.split(".")[-1] for group in ("observed", "externally_estimated")
                 for paths in provenance[group].values() for path in paths
                 if path.startswith("graphite_milestones.")}
        self.assertEqual(dates, set(self.assumptions["graphite_milestones"]))
        for line in self.inputs["lines"].values():
            self.assertIn(line["recipe"]["source"], provenance["externally_estimated"])
            for lane in line["lanes"].values():
                for field in lane.keys() - {"alternative"}:
                    self.assertIn(f"lines.*.lanes.*.{field}", provenance["hypothetical"])
        self.assertIn("lines.*.lanes.*.alternative.*", provenance["hypothetical"])


if __name__ == "__main__":
    unittest.main()
