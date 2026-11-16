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
        self.assertEqual(result["subcontractor"][0]["bundle_ex_vat"], 245)
        self.assertEqual(result["subcontractor"][0]["machining_ex_vat"], 36)
        self.assertEqual(result["subcontractor"][0]["size_mm"], [2440, 1220])
        self.assertGreater(result["in_house"]["operator_ex_vat"], 0)

    def test_only_concealed_back_splits_and_unplaced_work_keeps_subtotal_partial(self):
        report = {"objects": {"object-001": {"parts": [_part("carcass_back"), _part("door_front")]}}}
        plan = _plan([
            _allocation("B01:carcass_back:001", length=2600),
            _allocation("B01:door_front:002", length=2600),
        ])
        layout = build_sheet_layout(report, plan)
        row = layout["groups"][0]["layout"]
        self.assertEqual(row["splits"][0]["pieces_per_part"], 2)
        self.assertEqual(row["unplaced"], {"object-001:B01:door_front:002": 1})
        result = calculate_labor_v1(layout, plan)
        self.assertEqual(result["work"]["drilled_part_count"], 0)
        self.assertEqual(result["subcontractor"][0]["bundle_ex_vat"], 245)
        self.assertIn("placed parts only", result["subcontractor"][0]["status"])
        self.assertEqual(len(result["issues"]), 1)

    def test_unknown_supplier_quote_and_changed_quantity_are_explicit(self):
        report = {"objects": {"object-001": {"parts": [_part("fixed_panel")]}}}
        plan = _plan([_allocation("B01:fixed_panel:001")], family="mdf_hdf")
        layout = build_sheet_layout(report, plan)
        result = calculate_labor_v1(layout, plan)
        self.assertIsNone(result["subcontractor"][0]["bundle_ex_vat"])
        self.assertIsNone(result["in_house"]["machine_ex_vat"])
        plan["object_quantities"]["object-001"] = 2
        with self.assertRaisesRegex(ValueError, "different quantities"):
            calculate_labor_v1(layout, plan)
