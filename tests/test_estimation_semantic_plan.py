from copy import deepcopy

import pytest

from use_cases.estimation_semantic_plan import SEMANTIC_PLAN_VERSION, compile_semantic_plan
from use_cases.estimation_construction_plan import normalize_palette, normalize_construction_scope

REF = "ocr:run:p1:b1"
PAGE = "storage://page"


def fixture():
    row = {"input_id": "i", "input_payload": {"contract_version": "estimation_input_v4", "company_id": "c", "run_id": "r",
        "object": {"object_id": "o"}, "evidence": {"ocr_blocks": [
            {"block_ref": REF, "page_number": 1, "text": "4 cm", "bbox": {
                "top_left_x": 1, "top_left_y": 1, "bottom_right_x": 20, "bottom_right_y": 10}}]}}}
    raw = {"contract_version": SEMANTIC_PLAN_VERSION, "objects": [{"input_id": "i", "object_id": "o", "summary": "Fixture",
        "zones": [
            {"id": "s", "kind": "screen", "material_id": "V", "thickness": {"ref": REF}, "evidence_refs": [PAGE],
             "members": [{"id": "ribs", "role": "decorative_rib", "count": 6}]},
            {"id": "b", "kind": "drawer_cabinet", "material_id": "V", "thickness": {"same_as": "s"},
             "front_count": 3, "front_arrangement": "side_by_side", "evidence_refs": [PAGE]},
            {"id": "t", "kind": "worktop", "material_id": "P", "thickness": {"same_as": "s"}, "evidence_refs": [PAGE]},
            {"id": "l", "kind": "supports", "material_id": "L", "quantity": 2, "evidence_refs": [PAGE]}]}],
        "materials": [{"id": "V", "kind": "veneered_mdf", "basis": "visual_assumption"},
                      {"id": "P", "kind": "painted_mdf", "basis": "visual_assumption"},
                      {"id": "L", "kind": "purchased_leg", "basis": "visual_assumption"}]}
    return raw, row


def test_semantic_compiler_derives_layers_edges_roles_and_finish_without_duplicate_face_veneer():
    raw, row = fixture()
    original = deepcopy(raw)
    result = compile_semantic_plan(raw, inputs=[row])
    families = ["mdf_hdf", "edge_banding", "paint_lacquer_stain", "hardware_leg_caster"]
    palette = normalize_palette(result["material_palette"], allowed_refs={REF, PAGE}, families=families)
    scoped = normalize_construction_scope(result["object_scopes"][0], palette=palette, allowed_refs={REF, PAGE})
    screen, base, top, legs = scoped["zones"]
    assert palette["V"]["specification"]["thickness_mm"] == 20
    visible = screen["material_roles"][0]
    assert (visible["finished_thickness_mm"], visible["layer_count"], visible["thickness_basis"]) == (40, 2, "source")
    assert visible["edge_material"]["specification"]["width_mm"] == 40
    assert base["front_groups"] == [{"front_kind": "drawer_front", "quantity": 3, "arrangement": "side_by_side"}]
    hidden = next(m for m in base["material_roles"] if m["role"] == "internal_sheet")
    assert hidden["material_id"] == "V" and hidden["layer_count"] == 1 and hidden["finished_thickness_mm"] == 20
    finish = next(m for m in top["material_roles"] if m["role"] == "finish")
    assert finish["applies_to_roles"] == ["worktop_sheet"]
    assert legs["quantity"] == 2 and legs["construction"] == "purchased"
    assert not any(m["family"] == "veneer" for m in palette.values())
    assert raw == original


def test_semantic_compiler_keeps_linked_legend_and_explicit_stock():
    raw, row = fixture()
    raw["objects"][0]["zones"] = [raw["objects"][0]["zones"][0]]
    raw["objects"][0]["zones"][0]["thickness"] = {"mm": 18, "reason": "Specified stock used as one layer"}
    m = raw["materials"][0]
    m.update(kind="plywood", stock_thickness_mm=18, basis="linked_source", evidence_chain=[
        {"ref": PAGE, "kind": "callout", "observation": "VN11"},
        {"ref": "legend", "kind": "definition", "observation": "VN11 birch plywood 18 mm"}])
    result = compile_semantic_plan(raw, inputs=[row])
    assert result["material_palette"][0]["specification"]["thickness_mm"] == 18
    assert result["material_palette"][0]["evidence_chain"] == m["evidence_chain"]
    assert result["object_scopes"][0]["zones"][0]["material_assignments"][0]["layer_count"] == 1


@pytest.mark.parametrize("stock_mm, layers", [(20, 2), (40, 1)])
def test_finished_40_does_not_claim_a_unique_purchased_stock_thickness(stock_mm, layers):
    raw, row = fixture()
    raw["materials"][0]["stock_thickness_mm"] = stock_mm
    result = compile_semantic_plan(raw, inputs=[row])
    screen = result["object_scopes"][0]["zones"][0]
    role = screen["material_assignments"][0]
    assert role["finished_thickness_mm"] == 40
    assert role["layer_count"] == layers
    assert role["thickness_evidence_refs"] == [REF]
    palette = {m["material_id"]: m for m in result["material_palette"]}
    assert palette["V"]["specification"]["thickness_mm"] == stock_mm
    assert palette[role["edge_material_id"]]["specification"]["width_mm"] == 40


def test_assumed_minor_stock_variation_reuses_source_driven_stock_with_audit():
    raw, row = fixture()
    raw["objects"][0]["zones"][1]["thickness"] = {"mm": 18, "reason": "Generic cabinet default"}
    result = compile_semantic_plan(raw, inputs=[row])
    roles = result["object_scopes"][0]["zones"][1]["material_assignments"]
    assert roles[0]["finished_thickness_mm"] == 20 and roles[0]["layer_count"] == 1
    assert "18-mm thickness aligned to 20 mm" in roles[0]["reason"]
    source = result["object_scopes"][0]["zones"][0]["material_assignments"][0]
    assert source["finished_thickness_mm"] == 40 and source["thickness_basis"] == "source"


@pytest.mark.parametrize("error", ["cycle", "stock", "identity", "fractional_count"])
def test_semantic_compiler_rejects_contradictions(error):
    raw, row = fixture()
    if error == "cycle":
        raw["objects"][0]["zones"][0]["thickness"] = {"same_as": "b"}
    elif error == "stock":
        raw["materials"][0]["stock_thickness_mm"] = 18
    elif error == "identity":
        raw["objects"][0]["object_id"] = "invented"
    else:
        raw["objects"][0]["zones"][1]["front_count"] = 2.5
    with pytest.raises(ValueError):
        compile_semantic_plan(raw, inputs=[row])
