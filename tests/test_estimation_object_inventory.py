from use_cases.estimation_object_inventory import build_object_inventory, reconcile_object_inventory


def test_inventory_keeps_all_sheets_and_keeps_evidence_with_its_owner():
    views = [
        {"view_id": "v1", "object_id": "obj", "page": 1},
        {"view_id": "v2", "object_id": "obj", "page": 2},
    ]
    analyze = {"source_audit_sha256": "src", "islands": {"v1": "Front elevation", "v2": "Top view"},
               "objects": {"obj": {
                   "front": {"faces": [{"view_id": "v1", "candidate_id": "C1", "role": "drawer"}]},
                   "planner": {
                       "blocks": [{"id": "B01", "basis": "casework", "appearances": {"v1": ["C1"]}}],
                       "object_parts": [{"id": "plinth-kit", "role": "plinth", "quantity": 1, "unit": "set",
                                         "appearances": [{"view_id": "v1"}, {"view_id": "v2"}]}],
                       "independent_elements": [{"id": "cover", "role": "window_closure",
                                                 "view_id": "v1", "annotation": "A1"}],
                       "component_callouts": [
                           {"view_id": "v1", "annotation_id": "A1", "role": "cover"},
                           {"view_id": "v2", "annotation_id": "A1", "role": "lighting"},
                       ],
                   },
               }}}
    inventory = build_object_inventory(analyze, views, page_count=3)
    assert [len(sheet["views"]) for sheet in inventory["sheets"]] == [1, 1, 0]
    assert inventory["source_coverage"] == "pending_independent_review"
    obj = inventory["objects"]["obj"]
    assert [item["id"] for item in obj["items"]] == ["B01", "plinth-kit", "cover"]
    assert obj["items"][1]["quantity"] == 1
    assert [ref["page"] for ref in obj["items"][1]["source_refs"]] == [1, 2]
    assert [row["candidate_owner_ids"] for row in obj["observations"]] == [["B01"], ["cover"], []]
    assert obj["observations"][-1]["status"] == "ownership_pending"
    assert "quantity" not in obj["observations"][-1]


def test_reconcile_does_not_count_a_supported_worktop_twice():
    inventory = {"source_audit_sha256": "src", "objects": {"obj": {"items": [
        {"id": "B03", "kind": "block", "children": [
            {"id": "P01", "kind": "element", "children": []},
        ]},
        {"id": "plinth-kit", "kind": "element", "children": []},
        {"id": "closure", "kind": "element", "children": []},
    ]}}}
    parts = {"source_audit_sha256": "src", "objects": {"obj": {
        "blocks": [{"block_id": "B03", "object_part_id": "P01",
                    "parts": [{"role": "tabletop"}, {"role": "tabletop_underlayer"}, {"role": "support_leg"}]}],
        "shared_parts": [{"id": "plinth-kit", "parts": [{"role": "plinth_front"}]}],
    }}}
    result = reconcile_object_inventory(inventory, parts)
    support, plinth, closure = result["objects"]["obj"]["items"]
    top, leg = support["children"]
    assert [part["role"] for part in top["children"]] == ["tabletop", "tabletop_underlayer"]
    assert leg["role"] == "support_leg"
    assert [part["role"] for part in plinth["children"]] == ["plinth_front"]
    assert closure["parts_status"] == "pending_decomposition"
    assert inventory["objects"]["obj"]["items"][0]["children"][0]["children"] == []
