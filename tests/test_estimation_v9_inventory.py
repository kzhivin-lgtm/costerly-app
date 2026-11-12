import unittest

from use_cases.estimation_object_inventory import build_object_inventory, reconcile_object_inventory
from use_cases.estimation_v9_inventory import (
    apply_source_findings, bind_native_components, check_inventory, check_parts, include_standalone_parts_scopes,
)


def source(page, box, *, role="lighting", scope="standalone", stage="inventory_check"):
    return {"stage": stage, "role": role, "scope": scope,
            "source": {"page": page, "bbox_normalized": box, "evidence": "drawing evidence"}}


class TestEstimation9Inventory(unittest.TestCase):
    def setUp(self):
        self.views = [
            {"view_id": "V1", "object_id": "o", "page": 1, "bbox_normalized": [.1, .1, .9, .9]},
            {"view_id": "V2", "object_id": "o", "page": 2, "bbox_normalized": [.1, .1, .9, .9]},
        ]
        self.analyze = {"source_audit_sha256": "test", "islands": {"V1": "Front elevation", "V2": "Top view"},
                        "objects": {"o": {"front": {"faces": []}, "planner": {"blocks": []}}}}
        self.draft = build_object_inventory(self.analyze, self.views, page_count=2)

    def test_review_attaches_same_target_and_keeps_cross_view_identity_open(self):
        box = [.25, .3, .55, .4]
        apply_source_findings(self.draft, self.views, [source(1, box, role="mirror", stage="front")])
        checked = check_inventory(self.draft, self.views, [
            {"page": 1, "status": "reviewed", "findings": [
                source(1, [.26, .3, .55, .4], role="mirror"),
                source(1, [.3, .5, .6, .6], role="worktop"),
            ]},
            {"page": 2, "status": "reviewed", "findings": [
                source(2, box, role="mirror"),
                source(2, [.91, .2, .98, .3], role="mirror"),
            ]},
        ])
        self.assertEqual([row["role"] for row in checked["objects"]["o"]["items"]], ["mirror", "worktop"])
        self.assertEqual(len(checked["objects"]["o"]["items"][0]["source_refs"]), 2)
        self.assertEqual(len(self.draft["objects"]["o"]["items"]), 1)
        self.assertEqual([row["status"] for row in checked["objects"]["o"]["source_review_findings"]],
                         ["assigned", "assigned", "assigned", "identity_pending"])
        self.assertEqual(checked["unassigned_source_findings"][0]["status"], "view_ownership_pending")
        self.assertEqual(checked["source_coverage"], "reviewed_with_open_findings")

    def test_plinth_and_lighting_keep_object_level_sources(self):
        for role in ("plinth", "lighting"):
            apply_source_findings(self.draft, self.views, [
                source(1, [.2, .2, .4, .4], role=role), source(2, [.4, .4, .6, .6], role=role),
            ])
        plinth, lighting = self.draft["objects"]["o"]["items"]
        self.assertEqual(plinth["quantity"], 1)
        self.assertEqual(plinth["unit"], "set")
        self.assertIsNone(lighting["quantity"])
        self.assertEqual([len(item["source_refs"]) for item in (plinth, lighting)], [2, 2])

    def test_distinct_native_plan_runs_allow_two_worktops(self):
        view = self.views[1]
        view.update(width=100, height=100, candidates=[
            {"id": "C1", "bbox": [10, 20, 40, 40]}, {"id": "C2", "bbox": [60, 20, 90, 40]},
        ])
        apply_source_findings(self.draft, self.views, [
            source(2, [.18, .26, .42, .42], role="worktop"),
            source(2, [.58, .26, .82, .42], role="worktop"),
        ])
        self.assertEqual([item["role"] for item in self.draft["objects"]["o"]["items"]],
                         ["worktop", "worktop"])

    def test_two_native_glass_boxes_stay_inside_their_block(self):
        view = self.views[0]
        view.update(width=100, height=100, candidates=[
            {"id": "C1", "bbox": [10, 20, 40, 40]}, {"id": "C2", "bbox": [60, 20, 90, 40]},
        ])
        self.analyze["objects"]["o"]["planner"]["blocks"] = [
            {"id": "B1", "basis": "display", "appearances": {"V1": ["C1", "C2"]}},
        ]
        draft = build_object_inventory(self.analyze, self.views, page_count=2)
        apply_source_findings(draft, self.views, [
            source(1, [.18, .26, .42, .42], role="glass_box", scope="block_member"),
            source(1, [.58, .26, .82, .42], role="glass_box", scope="block_member"),
            source(2, [.18, .26, .42, .42], role="glass_box", scope="block_member"),
        ])
        obj = draft["objects"]["o"]
        block, = obj["items"]
        self.assertEqual([item["id"] for item in block["children"]], ["glass-box:V1:C1", "glass-box:V1:C2"])
        self.assertEqual(obj["source_review_findings"][-1]["status"], "ownership_pending")

    def test_mirror_and_glazing_are_nested_in_the_block(self):
        obj = self.analyze["objects"]["o"]
        obj["front"]["faces"] = [{"role": "mirror", "view_id": "V1", "candidate_id": "C1"}]
        obj["planner"]["blocks"] = [{"id": "B1", "basis": "test", "appearances": {"V1": ["C1"]},
            "envelopes": {"V1": {"polygons_px": [[[0, 0], [10, 0], [10, 10], [0, 10]]]}}}]
        obj["planner"]["component_callouts"] = [
            {"id": "V1:A1", "annotation_id": "A1", "view_id": "V1", "role": "glazed_zone",
             "tips": [{"xy_px": [4, 4]}, {"xy_px": [6, 5]}]},
            {"id": "V1:A2", "annotation_id": "A2", "view_id": "V1", "role": "glazed_zone",
             "tips": [{"xy_px": [4, 4]}, {"xy_px": [14, 5]}]},
        ]
        draft = build_object_inventory(self.analyze, self.views, page_count=2)
        bind_native_components(draft, self.analyze)
        block, = draft["objects"]["o"]["items"]
        mirror, glazing = block["children"]
        self.assertEqual(mirror["attached_block_ids"], ["B1"])
        self.assertEqual(mirror["quantity"], 1)
        self.assertEqual(glazing["id"], "glazing:V1:A1")
        self.assertIsNone(glazing["quantity"])
        self.assertEqual(draft["objects"]["o"]["observations"][-1]["status"], "ownership_pending")

    def test_lighting_ownership_requires_a_continuous_contour_to_span_blocks(self):
        from use_cases.estimation_lighting_ownership import resolve_lighting_ownership

        def rectangle(left, right):
            return [[left, 0], [right, 0], [right, 100], [left, 100]]

        blocks = [{"id": block, "basis": "display", "envelopes": {"V1": {"polygons_px": [rectangle(a, b)]}}}
                  for block, a, b in (("B1", 0, 48), ("B2", 52, 100))]
        self.analyze["objects"]["o"]["planner"]["blocks"] = blocks
        view_index = {view["view_id"]: {**view, "width": 100, "height": 100, "candidates": []}
                      for view in self.views}
        geometry = {"objects": {"o": {"blocks": [
            {"block_id": row["id"], "measurements": {}} for row in blocks
        ]}}}
        for continuous in (False, True):
            with self.subTest(continuous=continuous):
                planner = self.analyze["objects"]["o"]["planner"]
                planner["component_callouts"] = [{
                    "id": "V1:A1", "view_id": "V1", "annotation_id": "A1", "role": "lighting",
                    "source_text": "LED 4000",
                    "tips": [{"xy_px": [x, 50], "contours": ["strip"] if continuous else []} for x in (25, 75)],
                }]
                view_index["V1"]["candidates"] = [{"id": "strip", "bbox": [20, 49, 80, 51]}] if continuous else []
                draft = build_object_inventory(self.analyze, self.views, page_count=2)
                bind_native_components(draft, self.analyze)
                apply_source_findings(draft, view_index.values(), [])
                resolve_lighting_ownership(draft, self.analyze, geometry, view_index)
                obj = draft["objects"]["o"]
                if continuous:
                    shared, = [item for item in obj["items"] if item["role"] == "lighting"]
                    self.assertEqual(shared["attached_block_ids"], ["B1", "B2"])
                    self.assertEqual(shared["continuous_contour_id"], "strip")
                    self.assertEqual(shared["quantity"], 1)
                    self.assertTrue(all(not item["children"] for item in obj["items"]))
                else:
                    self.assertEqual([item["id"] for item in obj["items"]], ["B1", "B2"])
                    self.assertEqual([item["children"][0]["kelvin_values"] for item in obj["items"]], [[4000], [4000]])
                self.assertEqual(obj["observations"][0]["status"], "assigned")

    def test_failed_page_and_missing_standalone_parts_remain_open(self):
        checked = check_inventory(self.draft, self.views, [
            {"page": 1, "status": "reviewed", "findings": [source(1, [.25, .3, .55, .4])]},
            {"page": 2, "status": "review_failed", "error": "unavailable", "findings": []},
        ])
        self.assertEqual(checked["source_coverage"], "incomplete_page_review")
        parts = {"source_audit_sha256": "test", "objects": {"o": {"blocks": [], "shared_parts": []}}}
        include_standalone_parts_scopes(parts, checked)
        report = check_parts(self.analyze, reconcile_object_inventory(checked, parts), parts)
        self.assertEqual(len(parts["objects"]["o"]["shared_parts"]), 1)
        self.assertEqual(report["objects"]["o"]["status"], "gaps_found")
        self.assertEqual({item["reason"] for item in report["objects"]["o"]["inventory_issues"]},
                         {"pending_decomposition", "quantity_pending"})

    def test_omitted_page_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "one review record"):
            check_inventory(self.draft, self.views, [{"page": 1, "status": "reviewed", "findings": []}])

    def test_review_reads_every_original_sheet_and_retains_unlocalized_evidence(self):
        import pymupdf
        from tools.estimation_v9_source_review import review_original_sheets

        called = []

        def invoke(stage, params, bind):
            called.append(stage)
            self.assertEqual(params["output_config"]["format"]["type"], "json_schema")
            schema = params["output_config"]["format"]["schema"]
            self.assertIn("source_text", schema["properties"]["findings"]["items"]["required"])
            self.assertEqual(len(params["messages"][0]["content"]), 2)
            if stage.endswith("002"):
                raise RuntimeError("unavailable")
            return bind({"findings": [
                {"role": "lighting", "scope": "block_member", "bbox": [0, 0, 1200, 50],
                 "evidence": "LED callout with uncertain location", "source_text": "LED 3000"},
            ]})

        def request(system, content, *, max_tokens):
            return {"messages": [{"content": content}], "output_config": {}}

        with pymupdf.open() as doc:
            doc.new_page()
            doc.new_page()
            reviews = review_original_sheets(doc, invoke, request, lambda x: x, lambda png: png)
        self.assertEqual(called, ["v9-inventory-page-001", "v9-inventory-page-002"])
        self.assertEqual([row["status"] for row in reviews], ["reviewed", "review_failed"])
        result = check_inventory(self.draft, self.views, reviews)
        unresolved, = result["unassigned_source_findings"]
        self.assertEqual(unresolved["source"]["localization_issue"], "invalid_source_target_coordinates")
        self.assertEqual(unresolved["source"]["source_text"], "LED 3000")
        self.assertEqual(unresolved["source"]["page"], 1)

    def test_parts_check_flags_same_physical_reference_across_scopes(self):
        block_rows = [{"id": ident, "basis": "test", "appearances": {}} for ident in ("B1", "B2")]
        self.analyze["objects"]["o"]["planner"]["blocks"] = block_rows
        draft = build_object_inventory(self.analyze, self.views, page_count=2)
        checked = check_inventory(draft, self.views, [
            {"page": page, "status": "reviewed", "findings": []} for page in (1, 2)
        ])
        row = {"role": "drawer_front", "instance_ref": "V1:C01", "dimensions": {}}
        envelope = {
            "width": {"mm": 1200, "basis": "printed_dimension", "refs": ["V1-D01"]},
            "depth": {"mm": None, "basis": "unresolved", "refs": []},
        }
        parts = {"source_audit_sha256": "test", "objects": {"o": {
            "blocks": [{"block_id": block["id"], "parts": [row]} for block in block_rows], "shared_parts": [],
        }}}
        parts["objects"]["o"]["blocks"][0]["envelope"] = envelope
        parts["objects"]["o"]["blocks"][0]["quantity"] = 2
        report = check_parts(self.analyze, reconcile_object_inventory(checked, parts), parts)
        self.assertEqual(report["objects"]["o"]["blocks"][0]["envelope"], envelope)
        self.assertNotIn("envelope", report["objects"]["o"]["blocks"][1])
        first, second = report["objects"]["o"]["parts"]
        self.assertEqual(first["scope_quantity"], 2)
        self.assertNotIn("scope_quantity", second)
        self.assertEqual(report["objects"]["o"]["inventory_issues"], [
            {"role": "drawer_front", "source_ref": "V1:C01", "reason": "duplicate_part_evidence"},
        ])
