"""Checks for the supplied arithmetic and the vintage balances."""
from decimal import Decimal
import json
from pathlib import Path
import unittest

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


if __name__ == "__main__":
    unittest.main()
