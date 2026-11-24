"""Test the published threshold and addendum accounting from pinned inputs."""

import json
from pathlib import Path
import unittest

from record_nuclear import calculate, inventory_accounting, replacement_threshold, scenario_addendum


class ReplacementTests(unittest.TestCase):
    def test_delayed_eu_enrichment_using_nine_months_of_inventory(self):
        result = replacement_threshold(2735, 12, 6, 9)
        self.assertEqual(result["gross_loss"], 2735)
        self.assertEqual(result["minimum_annual_replacement"], 1367.5)
        self.assertEqual(result["uncovered_before_replacements"], 0)
        inventory = inventory_accounting(result)
        self.assertEqual(inventory["opening_compatible_inventory_assumed"], 2051.25)
        self.assertEqual(inventory["drawn_before_replacements"], 1367.5)
        self.assertEqual(inventory["drawn_by_scenario_end"], 2051.25)
        self.assertEqual(inventory["opening_reserve_remaining_at_end"], 0)
        self.assertEqual(inventory["drawn_by_scenario_end"] + 1367.5 * 6 / 12, 2735)

    def test_early_gap_cannot_be_covered_by_late_deliveries(self):
        result = replacement_threshold(2735, 12, 6, 3)
        self.assertIsNone(result["minimum_annual_replacement"])
        self.assertEqual(result["uncovered_before_replacements"], 683.75)
        inventory = inventory_accounting(result)
        self.assertEqual(inventory["drawn_before_replacements"], 683.75)
        self.assertEqual(inventory["drawn_by_scenario_end"], 683.75)
        self.assertEqual(inventory["opening_reserve_remaining_at_end"], 0)

    def test_stock_survives_when_opening_reserve_exceeds_total_loss(self):
        result = replacement_threshold(1200, 12, 18, 15)
        self.assertEqual(result["minimum_annual_replacement"], 0)
        inventory = inventory_accounting(result)
        self.assertEqual(inventory["drawn_by_scenario_end"], 1200)
        self.assertEqual(inventory["opening_reserve_remaining_at_end"], 300)

    def test_no_gap_free_rate_when_replacement_arrives_after_horizon(self):
        result = replacement_threshold(1200, 12, 18, 9)
        self.assertIsNone(result["minimum_annual_replacement"])
        self.assertEqual(result["uncovered_before_replacements"], 300)

    def test_published_cases_and_capacity_screen(self):
        data = json.loads(Path(__file__).with_name("evidence_inputs.json").read_text(encoding="utf-8"))
        data["calculated"] = calculate(data)
        addendum = scenario_addendum(data)
        self.assertEqual(len(addendum["scenarios"]["russian_enrichment"]["accounts"]), 16)
        self.assertEqual(len(addendum["scenarios"]["western_conversion"]["accounts"]), 8)
        for scenario in addendum["scenarios"].values():
            self.assertIsNone(scenario["available_qualified_uncommitted_supply"])
            self.assertIsNone(scenario["actual_shortage"])
            self.assertFalse(scenario["reactor_level_consequences_assessed"])
            for row in scenario["accounts"]:
                self.assertAlmostEqual(
                    row["opening_compatible_inventory_assumed"],
                    row["drawn_by_scenario_end"] + row["opening_reserve_remaining_at_end"],
                )
        screen = addendum["enrichment_capacity_screen"]
        self.assertEqual(screen["combined_reported_capacity"], 24700)
        self.assertEqual(screen["joint_immediate_no_stock_requirement"], 6019)
        self.assertAlmostEqual(screen["required_share_if_two_operators_alone_replace"], 0.243684210526)


if __name__ == "__main__":
    unittest.main()
