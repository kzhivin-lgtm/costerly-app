import unittest
from dataclasses import replace

from use_cases.wood_cnc_calculation import (
    DEFAULT_CNC_PARAMETERS, DEFAULT_EDGING_PARAMETERS, Blank, Edges, StockBatch,
    calculate_cutting, cnc_workload, drilling_minutes,
    edging_workload, in_house_cost, subcontracted_order, supplier_cost,
)


def _batch(blanks, **changes):
    return StockBatch(**{
        "stock_id": "ldsp", "kind": "sheet", "length_mm": 1300, "width_mm": 420,
        "thickness_mm": 17, "blanks": tuple(blanks), **changes,
    })


class WoodCncCalculationTest(unittest.TestCase):
    def test_machine_profiles_control_pilot_workloads(self):
        part = Blank("A", 600, 400)
        cnc = replace(DEFAULT_CNC_PARAMETERS, panel_feed_m_min=4, sheet_load_min=2,
                      drilling_seconds_per_part=(10, 30, 50))
        work = cnc_workload([_batch([part])], drilling_parts=[part], parameters=cnc)
        self.assertEqual(work["cut_minutes"], 0.5)
        self.assertEqual(work["load_minutes"], 2)
        self.assertEqual(work["drilling_minutes"], 0.5)

        edges = replace(DEFAULT_EDGING_PARAMETERS, feed_m_min=6, setup_min=2, seconds_per_side=6)
        edge_work = edging_workload([Edges(part, "ldsp", 2, 0)], parameters=edges)
        self.assertAlmostEqual(edge_work["machine_minutes"], 2.4)

    def test_supplier_complexity_applies_only_to_complex_length(self):
        work = {"edge_m": 10, "machine_minutes": 0}
        quote = dict(unit="edge_m", rate_ex_vat=6, includes_material=None)
        straight = supplier_cost(work, **quote)
        mixed = supplier_cost(work, **quote, complex_edge_m=2, edge_parameters=DEFAULT_EDGING_PARAMETERS)
        self.assertEqual(straight["cost_ex_vat"], 60)
        self.assertEqual((mixed["quantity"], mixed["billable_quantity"], mixed["cost_ex_vat"]), (10, 11, 66))
        with self.assertRaisesRegex(ValueError, "Complex edge allowance"):
            supplier_cost(work, **quote, complex_edge_m=11, edge_parameters=DEFAULT_EDGING_PARAMETERS)

    def test_common_line_and_manual_exchange_for_one_sheet(self):
        a, b = Blank("A", 600, 400), Blank("B", 600, 400)
        result = cnc_workload([_batch([a, b], common_cut=True)], drilling_parts=[a, b])
        row = result["batches"][0]
        self.assertEqual((result["sheet_count"], result["handling_minutes"], result["setup_minutes"]), (1, 10, 10))
        self.assertAlmostEqual(row["perimeter_m"], 4)
        self.assertAlmostEqual(row["common_m"], 0.4)
        self.assertAlmostEqual(row["cut_m"], 3.6)
        self.assertAlmostEqual(result["cut_minutes"], 3.6 / 8)
        self.assertAlmostEqual(result["drilling_minutes"], 40 / 60)
        self.assertEqual(result["tool_change_minutes"], 0)
        self.assertEqual(result, cnc_workload([_batch([b, a], common_cut=True)], drilling_parts=[a, b]))

    def test_overlap_on_different_sheets_or_without_consent_is_not_credited(self):
        parts = [Blank("A", 600, 400, 2)]
        a = calculate_cutting(_batch(parts))
        b = calculate_cutting(_batch(parts, length_mm=1000, common_cut=True))
        self.assertEqual((a["common_m"], b["common_m"]), (0, 0))
        self.assertAlmostEqual(a["potential_common_m"], 0.4)
        self.assertEqual(b["stock_count"], 2)

    def test_thick_stock_keeps_all_passes_and_charges_cutter_change(self):
        a, b = Blank("A", 600, 400), Blank("B", 600, 400)
        result = cnc_workload([_batch([a]), _batch([b], thickness_mm=50)])
        thick = result["batches"][1]
        self.assertEqual((thick["passes"], thick["cutter_mm"]), (3, 18))
        self.assertEqual(result["tool_change_minutes"], 0.5)
        self.assertEqual(thick["path_m"], thick["cut_m"] * 3)

    def test_solid_board_is_single_stock_piece_and_does_not_rotate(self):
        row = calculate_cutting(_batch([Blank("A", 600, 400, 2)], kind="solid_blank"))
        self.assertEqual((row["stock_count"], row["feed_m_min"], row["passes"]), (2, 6, 2))
        too_wide = calculate_cutting(_batch([Blank("B", 400, 600)], kind="solid_panel"))
        self.assertEqual(too_wide["unplaced"], {"B": 1})

    def test_drilling_size_threshold_and_unplaced_work_not_charged(self):
        self.assertEqual(drilling_minutes([Blank("small", 300, 500), Blank("large", 1000, 600)]), 40 / 60)
        too_wide = Blank("A", 1400, 600)
        work = cnc_workload([_batch([too_wide])], drilling_parts=[too_wide])
        self.assertFalse(work["geometry_complete"])
        self.assertEqual(work["drilling_minutes"], 0)
        with self.assertRaisesRegex(ValueError, "Incomplete geometry"):
            supplier_cost(work, unit="job", rate_ex_vat=800, includes_material=True)

    def test_edging_all_four_lev1_edges_and_gross_pricing(self):
        edges = edging_workload([Edges(Blank("B02", 2180, 765, 2), "veneer:20", 2, 2)])
        self.assertAlmostEqual(edges["edge_m"], 11.78)
        self.assertEqual(edges["edge_count"], 8)
        self.assertEqual(edges["setup_minutes"], 10)
        self.assertAlmostEqual(edges["feed_minutes"], 11.78 / 7)
        self.assertAlmostEqual(edges["handling_minutes"], 8 * 12 / 60)
        self.assertAlmostEqual(edges["machine_minutes"], 10 + 11.78 / 7 + 8 * 12 / 60)
        work = {"machine_minutes": 60, "manual_minutes": 44, "program_minutes": 16}
        self.assertEqual(in_house_cost(work, gross_rate_per_hour=55, machine_rate_per_hour=100),
                         {"labor_hours": 1, "gross_rate": 55, "labor_base_cost": 55, "machine_cost": 100})
        self.assertEqual(in_house_cost(work, gross_rate_per_hour=50, attendance=0)["labor_hours"], 44 / 60)

    def test_supplier_quote_units_and_no_duplicate_edging(self):
        work = cnc_workload([_batch([Blank("A", 600, 400)])])
        edge = edging_workload([Edges(Blank("A", 600, 400), "ldsp:17", 2, 2)])
        bundle = dict(unit="job", rate_ex_vat=100, includes_material=True, includes_edging=True)
        tape = dict(unit="edge_m", rate_ex_vat=6, includes_material=True)
        self.assertEqual(subcontracted_order(work, edge, cnc_quote=bundle)["total_ex_vat"], 100)
        with self.assertRaisesRegex(ValueError, "already covers"):
            subcontracted_order(work, edge, cnc_quote=bundle, edge_quote=tape)
        separate = subcontracted_order(work, edge, cnc_quote={**bundle, "includes_edging": False}, edge_quote=tape)
        self.assertEqual(separate["total_ex_vat"], 112)
        self.assertEqual(separate["cnc"]["internal_labor_hours"], 0)
