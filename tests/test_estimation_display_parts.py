import unittest

from use_cases.estimation_cb_geometry_parts import dimension
from use_cases.estimation_display_parts import (
    _coils, _lighting, _stock_notes, add_source_display_glass_parts, glass_box_parts, power_supply_watts,
)
from use_cases.estimation_v9_inventory import lighting_temperature_readings


class TestDisplayParts(unittest.TestCase):
    def test_stock_notes_keep_explicit_measurements_and_reject_conflicts(self):
        row = {"input_id": "i", "input_payload": {
            "object": {"object_id": "o"},
            "evidence": {"ocr_blocks": [{"block_ref": "note", "text":
                "1. Kapnychbui Mamepuan: Phanepe 16 MM.\n"
                "2. Фасадны мамершал: Фанера 18 мм.\n"
                "3. Front offset: 5 mm.\n"
                "4. Carcass material: 200 x 300 x 17 mm."}]}}}
        sources = {"o": {"input_id": "i"}}
        notes = _stock_notes([row], sources)["o"]
        self.assertEqual({role: value["mm"] for role, value in notes.items()}, {"carcass": 16, "facade": 18})
        self.assertEqual(notes["carcass"]["refs"], ["note"])
        row["input_payload"]["evidence"]["ocr_blocks"].append(
            {"block_ref": "other", "text": "Carcass material: 19 mm plywood."})
        self.assertNotIn("carcass", _stock_notes([row], sources)["o"])
        self.assertFalse(_stock_notes([row], {"o": {"input_id": "another"}}))

    def test_glass_box_has_five_panes_with_four_mm_stock(self):
        width, depth, height, thickness = (
            dimension(value, "test") for value in (544, 300, 123, 4)
        )
        rows = glass_box_parts(width, depth, height, thickness, scope_id="box", ref="V1:C1")
        self.assertEqual(sum(row["quantity"] for row in rows), 5)
        self.assertEqual([[d["mm"] for d in row["dimensions"].values()] for row in rows],
                         [[544, 300, 4], [544, 119, 4], [292, 119, 4]])
        self.assertTrue(all(row["inventory_item_id"] == "box" for row in rows))

    def test_source_display_glass_requires_distinct_shelves_for_each_arrow(self):
        zone = {"id": "zone", "role": "glazed_zone", "quantity": None, "source_refs": [{
            "view_id": "V1", "annotation_id": "A1", "source_text": "Витрина / Стекло",
            "tips": [{"xy_px": [15, 18]}, {"xy_px": [25, 18]}],
        }]}
        block = {"kind": "block", "id": "B1", "children": [zone]}
        inventory = {"objects": {"o": {"items": [block]}}}
        scope = {"block_id": "B1", "parts": []}
        parts = {"objects": {"o": {"blocks": [scope]}}}
        faces = [{"role": "pull_out_shelf", "view_id": "V1", "candidate_id": cid,
                  "bbox_px": box} for cid, box in [("C1", [10, 20, 30, 30]), ("C2", [40, 20, 60, 30])]]
        analyze = {"objects": {"o": {"front": {"faces": faces},
                                     "planner": {"blocks": [{"id": "B1", "members": ["C1", "C2"]}]}}}}
        add_source_display_glass_parts(parts, inventory, analyze)
        self.assertEqual(scope["parts"], [])
        zone["source_refs"][0]["tips"][1]["xy_px"] = [45, 18]
        add_source_display_glass_parts(parts, inventory, analyze)
        add_source_display_glass_parts(parts, inventory, analyze)
        self.assertEqual(zone["quantity"], 2)
        self.assertTrue(scope["construction_pending"])
        self.assertEqual(sum(row["quantity"] for row in scope["parts"]), 10)
        self.assertEqual({row["instance_ref"] for row in scope["parts"]}, {"V1:C1", "V1:C2"})
        self.assertTrue(all(row["dimensions"]["length"]["mm"] is None for row in scope["parts"]))

    def test_glass_footprint_uses_only_its_own_measured_shelf(self):
        zone = {"id": "zone", "role": "glazed_zone", "quantity": None, "source_refs": [{
            "view_id": "V1", "annotation_id": "A1", "source_text": "Витрина / Стекло",
            "tips": [{"xy_px": [15, 18]}],
        }]}
        inventory = {"objects": {"o": {"items": [{"kind": "block", "id": "B1", "children": [zone]}]}}}
        scope = {"block_id": "B1", "parts": [{"role": "pull_out_shelf", "instance_ref": "V1:C1",
                 "dimensions": {"length": dimension(544, "scaled_projection", ["width-note"]),
                                "width": dimension(300, "scaled_projection", ["depth-note"])}}]}
        parts = {"objects": {"o": {"blocks": [scope]}}}
        analyze = {"objects": {"o": {
            "front": {"faces": [{"role": "pull_out_shelf", "view_id": "V1", "candidate_id": "C1",
                                 "bbox_px": [10, 20, 30, 30]}]},
            "planner": {"blocks": [{"id": "B1", "members": ["C1"]}]},
        }}}
        add_source_display_glass_parts(parts, inventory, analyze)
        _, base, long_wall, end_wall = scope["parts"]
        self.assertEqual([d["mm"] for d in base["dimensions"].values()], [544, 300, 4])
        self.assertEqual(base["dimensions"]["length"]["basis"], "construction_assumption")
        self.assertEqual(base["dimensions"]["width"]["refs"], ["depth-note"])
        self.assertIsNone(long_wall["dimensions"]["width"]["mm"])
        self.assertIsNone(end_wall["dimensions"]["width"]["mm"])

    def test_power_supply_uses_headroom_and_steps_up_over_five_metres(self):
        self.assertEqual([power_supply_watts(length, 6) for length in (1000, 5000, 5001, 6000, 7000)],
                         [40, 40, 50, 50, 60])
        self.assertEqual(power_supply_watts(5000, 12), 80)

    def test_compatible_circuits_share_coils_with_real_cut_lengths(self):
        circuits = [
            {"kelvin": k, "watts_per_m": 6, "segment_length_mm": n, "segments": 1, "circuit_id": ident}
            for k, n, ident in [(3000, 2000, "a"), (3000, 3000, "b"), (4000, 1000, "c")]
        ]
        warm, neutral = _coils(circuits)
        self.assertEqual((warm["quantity"], warm["remaining_mm_by_coil"]), (1, [0]))
        self.assertEqual((neutral["quantity"], neutral["remaining_mm_by_coil"]), (1, [4000]))
        pieces = [{**circuits[0], "segment_length_mm": 3000, "segments": 3}]
        self.assertEqual(_coils(pieces)[0]["quantity"], 3)

    def test_lighting_temperature_follows_source_and_conflicts_stay_open(self):
        readings = lighting_temperature_readings({"source_refs": [
            {"page": 1, "view_id": "V1", "annotation_id": "A1", "source_text": "Подсветка LED 3000"},
            {"page": 1, "view_id": "V1", "annotation_id": "A2", "source_text": "LED 4000 K"},
            {"page": 2, "view_id": "V2", "source_text": None, "evidence": "Assume 'LED 5000'"},
            {"page": 2, "view_id": "V2", "source_text": "LED 3000 lm"},
            {"page": 3, "view_id": "V3", "evidence": "Printed 'LED 2700' near the edge."},
        ]})
        self.assertEqual([row["kelvin_values"] for row in readings], [[3000], [4000], [2700]])
        self.assertEqual(readings[-1]["basis"], "archived_callout_transcription")
        circuits = [
            {"id": "a", "temperature_source_views": ["V1"], "temperature_source_annotation": "A2"},
            {"id": "b", "temperature_source_views": ["V1"]},
            {"id": "c", "temperature_source_views": ["V2"]},
        ]
        for circuit in circuits:
            circuit.update(mirror_id="m", refs=[], passes=1)
        rows, lengths = _lighting(circuits, {"m": {"height": dimension(1500, "test")}}, {}, 6, "o", readings)
        strips = [row for row in rows if row["role"] == "led_strip_run"]
        self.assertEqual([row["colour_temperature_k"] for row in strips], [4000, None, None])
        self.assertEqual([row["colour_temperature_status"] for row in strips],
                         ["source_reading", "temperature_conflict", "temperature_pending"])
        self.assertEqual([row["kelvin"] for row in _coils(lengths)], [4000])
