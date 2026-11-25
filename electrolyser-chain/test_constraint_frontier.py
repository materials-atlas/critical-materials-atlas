"""Checks for the supplied arithmetic and the vintage balances."""
from decimal import Decimal
import json
from pathlib import Path
import unittest

from constrained_deployment import constrained_balance, evaluate_followup, market_budget
from constraint_frontier import annual_balance, evaluate, frontier, number

INPUTS = json.loads(Path(__file__).with_name("evidence_inputs.json").read_text(encoding="utf-8"))


class IridiumBalanceTests(unittest.TestCase):
    def test_frontier_matches_original_example_and_equality(self):
        rows, thresholds = frontier(INPUTS["static_scenarios"])
        self.assertEqual((len(rows), len(thresholds)), (27, 9))
        case = next(row for row in rows
                    if (row["annual_new_PEM_GW"], row["intensity_kg_Ir_per_MW"],
                        row["assumed_share_global_supply"]) == (30, 0.2, 0.3))
        self.assertEqual(case["gross_demand_t_Ir_per_year"], Decimal("6"))
        self.assertEqual(case["shortfall_t_Ir_per_year"], Decimal("3.75"))
        self.assertEqual(thresholds[4]["annual_new_PEM_GW_at_equality"], Decimal("11.25"))

        settings = {**INPUTS["static_scenarios"], "annual_new_pem_gw": [45],
                    "intensity_kg_ir_per_mw": [0.05], "assumed_primary_shares": [0.3]}
        self.assertFalse(frontier(settings)[0][0]["gross_requirement_exceeds_available"])

    def test_replacements_recover_the_earlier_loading_after_lag(self):
        path = {"new_all_electrolysis_gw_by_year": {2026: 1, 2027: 0, 2030: 0}}
        p = {**INPUTS["annual"]["assumptions"], "pem_share": 1, "plant_lifetime_years": 3,
             "operating_stack_hours": 4000, "manufacturing_yield": 1,
             "intensity_by_year": {2026: 0.2, 2027: 0.05}, "recycling_lag_years": 1}
        case = annual_balance(path, p, 7.5)
        rows = case["rows"]
        self.assertEqual(case["stack_calendar_years"], 1)
        self.assertEqual(rows[1]["replacement_stack_gw"], 1)
        self.assertEqual(rows[1]["retired_ir_t"], Decimal("0.2"))
        self.assertEqual(rows[1]["recycled_ir_arrived_t"], 0)
        self.assertEqual(rows[2]["recycled_ir_arrived_t"], Decimal("0.14"))
        self.assertEqual(rows[2]["gross_ir_input_t"], Decimal("0.05"))
        self.assertEqual(rows[2]["recycled_ir_inventory_t"], Decimal("0.09"))
        self.assertEqual(rows[3]["retired_plant_gw"], 1)
        self.assertEqual(rows[3]["replacement_stack_gw"], 0)
        self.assertEqual(rows[3]["planned_installed_pem_gw"], 0)

    def test_mass_balance_across_all_displayed_paths(self):
        result = evaluate(INPUTS)
        for case in [*result["pathways"].values(), *result["mitigation"].values()]:
            stock = in_use = number(0)
            for row in case["rows"]:
                stock += row["recycled_ir_arrived_t"] - row["recycled_ir_used_t"]
                in_use += row["embedded_ir_t"] - row["retired_ir_t"]
                self.assertEqual(stock, row["recycled_ir_inventory_t"])
                self.assertEqual(in_use, row["in_service_ir_t"])
                self.assertAlmostEqual(row["gross_ir_input_t"],
                                       row["recycled_ir_used_t"] + row["primary_ir_required_t"])
        reference = result["mitigation"]["reference"]
        self.assertEqual(reference["first_gap_year"], 2036)
        self.assertEqual(result["mitigation"]["lower_loading"]["cumulative_gap_t"], 0)
        self.assertNotEqual(reference["peak_gap_t"], result["market_supply_comparison"]["peak_gap_t"])


class ConstrainedDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.settings = {
            **INPUTS["annual"]["assumptions"], "pem_share": 1,
            "intensity_by_year": {"2026": 1}, "operating_stack_hours": 1000,
            "plant_lifetime_years": 3, "manufacturing_yield": 1,
            "recovery_fraction": 0.5, "recycling_lag_years": 1,
        }

    def test_budget_and_stock_terms(self):
        market = INPUTS["second_review"]["market"]
        self.assertEqual(market_budget(market), 2)
        self.assertEqual(market_budget({
            **market, "stock_released_t": 0.25, "external_recycling_t": 0.5, "stock_added_t": 0.75,
        }), 2)
        self.assertEqual(market_budget({**market, "other_net_demand_t": 9}), 0)

    def test_replacements_get_priority_and_only_fitted_stacks_return_metal(self):
        path = {"new_all_electrolysis_gw_by_year": {2026: 2, 2027: 1, 2028: 0, 2029: 0}}
        rows = constrained_balance(path, self.settings, 1)
        self.assertEqual([row["commissioned_new_gw"] for row in rows], [1, 0, Decimal("0.5"), 1])
        self.assertEqual([row["fitted_replacement_gw"] for row in rows], [0, 1, 1, Decimal("0.5")])
        self.assertEqual([row["fleet_ir_returned_t"] for row in rows], [0, 0, Decimal("0.5"), Decimal("0.5")])
        self.assertEqual([row["queued_new_gw"] for row in rows], [1, 2, Decimal("1.5"), Decimal("0.5")])
        empty = constrained_balance(path, self.settings, 0)
        self.assertTrue(all(row["active_pem_gw"] == row["fleet_ir_returned_t"] == 0 for row in empty))
        self.assertEqual(empty[-1]["queued_new_gw"], 3)

    def test_unreplaced_capacity_waits_only_within_plant_life(self):
        path = {"new_all_electrolysis_gw_by_year": {2026: 2, 2027: 0, 2028: 0}}
        p = {**self.settings, "intensity_by_year": {"2026": 0.5, "2027": 1}, "plant_lifetime_years": 2}
        rows = constrained_balance(path, p, 1)
        self.assertEqual([row["inactive_awaiting_replacement_gw"] for row in rows], [0, 1, 0])
        self.assertEqual([row["active_pem_gw"] for row in rows], [2, 1, 0])

    def test_displayed_deployment_and_conservation(self):
        result = evaluate_followup(INPUTS)
        historical, transition, advanced = result["loading_cases"]
        self.assertEqual([round(case["commissioned_new_gw"], 1) for case in (historical, transition, advanced)],
                         [Decimal("49.8"), Decimal("148.7"), Decimal("345.5")])
        self.assertEqual(advanced["queued_new_gw"], 0)
        self.assertIsNone(advanced["first_gap_year"])
        self.assertEqual(advanced["years"][-1]["active_pem_gw"],
                         advanced["years"][-1]["unconstrained_active_pem_gw"])
        for case in result["loading_cases"]:
            scheduled = commissioned = stock = active = number(0)
            for row in case["years"]:
                scheduled += row["scheduled_new_gw"]
                commissioned += row["commissioned_new_gw"]
                stock += row["fleet_ir_returned_t"] - row["fleet_ir_used_t"]
                active += row["commissioned_new_gw"] + row["fitted_replacement_gw"] - row["retired_stack_gw"]
                self.assertEqual(scheduled - commissioned, row["queued_new_gw"])
                self.assertEqual(stock, row["fleet_ir_stock_t"])
                self.assertEqual(active, row["active_pem_gw"])
                self.assertLessEqual(row["market_ir_used_t"], row["market_ir_available_t"])
                self.assertAlmostEqual(row["gross_ir_input_t"], row["market_ir_used_t"] + row["fleet_ir_used_t"])
        self.assertEqual(len(result["sensitivity"]), 8)
        self.assertEqual([len(group["cases"]) for group in result["interactions"]], [4, 4, 4, 4])


if __name__ == "__main__":
    unittest.main()
