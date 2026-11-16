import json
from unittest import TestCase
from unittest.mock import patch

from use_cases.estimation_labor_v1 import build_sheet_layout, calculate_labor_v1


def _part(role, *, owner="B01", quantity=1):
    return {"role": role, "owner_id": owner, "quantity": quantity, "dimensions": {}}


def _allocation(part, *, quantity=1, length=500, width=300):
    return {
        "object_id": "object-001", "material_requirement_id": "sheet-001",
        "demand_id": f"object-001:{part}", "length_mm": length, "width_mm": width, "quantity": quantity,
    }


def _plan(allocations, *, family="melamine_faced_particleboard", thickness=17, length=2400):
    return {
        "object_quantities": {"object-001": 1},
        "lines": [{
            "selection_key": f"{family}|thickness={thickness}", "candidate_id": "stock",
            "purchase_kind": "sheet", "currency": "ILS", "display_name": "Stock",
            "price_per_purchase_unit": 180,
            "purchasable_dimensions": {"length_mm": length, "width_mm": 1220},
            "allocations": allocations,
        }],
    }


class LaborV1Test(TestCase):
    def test_item_totals_share_saved_stock_and_show_only_its_issues(self):
        report = {"objects": {
            "object-001": {"parts": [_part("door_front"), _part("door_front")]},
            "object-002": {"parts": [_part("door_front")]},
        }}
        plan = _plan([
            _allocation("B01:door_front:001"),
            _allocation("B01:door_front:002", length=None),
            {**_allocation("B01:door_front:001"),
             "object_id": "object-002", "demand_id": "object-002:B01:door_front:001"},
        ])
        plan["object_quantities"]["object-002"] = 1
        layout = build_sheet_layout(report, plan)
        estimate = calculate_labor_v1(layout, plan)
        first = calculate_labor_v1(layout, plan, object_id="object-001")
        second = calculate_labor_v1(layout, plan, object_id="object-002")
        self.assertEqual(len(first["issues"]), 1)
        self.assertEqual(second["issues"], [])
        for result in (first, second):
            self.assertEqual(result["work"]["sheet_count"], 0.5)
            self.assertEqual(result["work"]["blank_count"], 1)
            self.assertEqual(result["in_house"]["materials"][0]["stock_ex_vat"], 90)
            self.assertEqual(result["subcontractor"]["bundle_ex_vat"], 122.5)
            self.assertEqual(result["subcontractor"]["machining_ex_vat"], 12)
        for key in ("cut_m", "machine_minutes", "setup_minutes"):
            self.assertAlmostEqual(first["work"][key] + second["work"][key], estimate["work"][key])

    def test_both_routes_reuse_saved_coordinates_and_price_sheet_once(self):
        report = {"objects": {"object-001": {"parts": [
            _part("door_front", quantity=2), _part("fixed_panel", owner="common")
        ]}}}
        plan = _plan([_allocation("B01:door_front:001", quantity=2), _allocation("common:fixed_panel:001")])
        layout = json.loads(json.dumps(build_sheet_layout(report, plan)))
        positions = layout["groups"][0]["layout"]["placements"]
        self.assertEqual(len(positions), 3)
        self.assertIn("object-001:common:fixed_panel:001", {p["part_id"] for p in positions})
        with patch("use_cases.wood_cnc_calculation._layout", side_effect=AssertionError("Repacked in Calculation")):
            result = calculate_labor_v1(layout, plan, machine_rate=60)
        self.assertEqual(result["in_house"]["materials"][0]["stock_ex_vat"], 180)
        self.assertEqual(result["subcontractor"]["bundle_ex_vat"], 245)
        self.assertEqual(result["subcontractor"]["machining_ex_vat"], 36)
        self.assertEqual(result["in_house"]["operator_hours"], 1)
        self.assertEqual(result["in_house"]["operator_ex_vat"], 68.75)
        self.assertEqual(result["in_house"]["machine_ex_vat"], round(result["work"]["machine_minutes"], 2))

    def test_oversize_back_and_visible_front_are_joined_if_only_standard_stock_is_selected(self):
        report = {"objects": {"object-001": {"parts": [_part("carcass_back"), _part("door_front")]}}}
        plan = _plan([
            _allocation("B01:carcass_back:001", length=2600),
            _allocation("B01:door_front:002", length=2600),
        ])
        layout = build_sheet_layout(report, plan)
        row = layout["groups"][0]["layout"]
        self.assertEqual(row["splits"][0]["pieces_per_part"], 2)
        self.assertEqual(row["splits"][1]["pieces_per_part"], 2)
        self.assertEqual(row["unplaced"], {})
        result = calculate_labor_v1(layout, plan)
        self.assertEqual(result["work"]["drilled_part_count"], 1)
        self.assertEqual(result["subcontractor"]["bundle_ex_vat"], 490)
        self.assertEqual(result["unplaced_blanks"], 0)
        self.assertEqual(len(result["joined_parts"]), 2)

    def test_supplier_allowance_covers_same_mixed_stock_without_inventing_machine_rate(self):
        report = {"objects": {"object-001": {"parts": [
            _part("door_front"), _part("fixed_panel"), _part("carcass_back"),
        ]}}}
        plan = _plan([_allocation("B01:door_front:001")])
        plan["lines"] += _plan([_allocation("B01:fixed_panel:002")], family="mdf_hdf", thickness=20)["lines"]
        plan["lines"] += _plan([_allocation("B01:carcass_back:003")], family="fibreboard_hardboard", thickness=6)["lines"]
        layout = build_sheet_layout(report, plan)
        # Existing Parts snapshots can contain the old supplier-only subset.
        # Calculation must use the shared layout even when that field exists.
        for group in layout["groups"]:
            group["supplier_layout"] = None
        result = calculate_labor_v1(layout, plan)
        self.assertEqual(result["work"]["sheet_count"], 3)
        self.assertEqual(result["work"]["drilled_part_count"], 2)
        self.assertEqual(result["subcontractor"]["bundle_ex_vat"], 735)
        self.assertEqual(result["subcontractor"]["machining_ex_vat"], 24)
        self.assertIsNone(result["in_house"]["machine_rate"])
        self.assertIsNone(result["in_house"]["machine_ex_vat"])
        plan["object_quantities"]["object-001"] = 2
        with self.assertRaisesRegex(ValueError, "different quantities"):
            calculate_labor_v1(layout, plan)

    def test_unpriced_assumption_sheet_keeps_its_workload_and_needs_a_stock_price(self):
        report = {"objects": {"object-001": {"parts": [_part("fixed_panel")]}}}
        plan = _plan([_allocation("B01:fixed_panel:001")], family="mdf_hdf", thickness=17)
        plan["lines"][0].update(
            authority="assumption",
            selection_key="mdf_hdf|assumption_sheet=shared",
            label_specifications={"thickness_mm": 17},
            price_per_purchase_unit=200,
        )
        result = calculate_labor_v1(build_sheet_layout(report, plan), plan, object_id="object-001")
        self.assertIsNone(result["in_house"]["materials"][0]["stock_ex_vat"])
        self.assertEqual(result["work"]["sheet_count"], 1)
        self.assertEqual(result["work"]["blank_count"], 1)
        self.assertEqual(result["subcontractor"]["bundle_ex_vat"], 245)
