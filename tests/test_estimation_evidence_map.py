from copy import deepcopy
from io import BytesIO

import pytest
from PIL import Image, ImageDraw

from use_cases.estimation_evidence_map import build_evidence_map, interpret_evidence_map, apply_evidence_measurements
from use_cases.estimation_dimension_graph import build_dimension_graph
from use_cases.estimation_2vn_resolver import resolve_2vn_geometry


def fixture():
    image = Image.new("RGB", (400, 200), "white")
    draw = ImageDraw.Draw(image)
    draw.line((100, 58, 300, 58), fill="gray")
    draw.line((100, 48, 100, 100), fill="gray")
    draw.line((300, 48, 300, 100), fill="gray")
    # A text-like vertical stroke near the number must not outrank the line.
    draw.line((195, 40, 195, 56), fill="black")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    row = {"input_id": "i", "input_payload": {"contract_version": "estimation_input_v4",
        "object": {"object_id": "o", "evidence_pages": [{"page_number": 1, "regions": [
            {"top_left_x": 180, "top_left_y": 160, "bottom_right_x": 620, "bottom_right_y": 360}]}]},
        "evidence": {"artifacts": [{"artifact_kind": "page", "page_number": 1, "storage_ref": "p"}],
            "ocr_blocks": [{"block_ref": "n", "page_number": 1, "text": "72 cm", "bbox": {
                "top_left_x": 370, "top_left_y": 70, "bottom_right_x": 440, "bottom_right_y": 145}}],
            "geometry_context": {"rendering": {"dpi": 144}, "page_profiles": [
                {"page_number": 1, "page_size_points": {"width": 400, "height": 200}}]}}}}
    return row, {"p": buffer.getvalue()}


def reading():
    return {"views": [{"view_id": "p1-view-001", "projection": "side_elevation", "horizontal_axis": "depth"}],
        "dimensions": [{"dimension_id": "dimension-001", "view_id": "p1-view-001", "scope_id": "z",
            "axis": "depth", "local_orientation": "horizontal", "candidate_id": None,
            "between": ["front of enclosure", "back of enclosure"], "measures": "enclosure depth"}]}


def test_raster_coordinates_are_mapped_once_and_text_boxes_do_not_cut_lines():
    row, pages = fixture()
    before = deepcopy(row)
    evidence = build_evidence_map(input_row=row, page_bytes_by_ref=pages)
    number = evidence["dimensions"][0]
    line = number["line_candidates"][0]
    assert line["orientation"] == "horizontal"
    assert line["start"] == {"x": 200, "y": 116}
    assert line["end"] == {"x": 600, "y": 116}
    assert number["interpreted_value_mm"] == 720
    assert number["ownership_status"] == "unresolved"
    assert row == before


def test_unknown_coordinate_frame_never_authorizes_raster_geometry():
    row, pages = fixture()
    row["input_payload"]["evidence"]["geometry_context"] = {}
    evidence = build_evidence_map(input_row=row, page_bytes_by_ref=pages)
    assert evidence["pages"][0]["line_status"] == "coordinate_frame_unavailable"
    assert evidence["dimensions"][0]["line_candidates"] == []


@pytest.mark.parametrize("error", ["view", "candidate", "zone", "boundaries", "duplicate"])
def test_interpretation_rejects_unknown_or_unscoped_claims(error):
    row, pages = fixture()
    evidence = build_evidence_map(input_row=row, page_bytes_by_ref=pages)
    raw = reading()
    if error == "view":
        raw["views"][0]["view_id"] = "invented"
    elif error == "candidate":
        raw["dimensions"][0]["candidate_id"] = "invented"
    elif error == "zone":
        raw["dimensions"][0]["scope_id"] = "foreign"
    elif error == "boundaries":
        raw["dimensions"][0]["between"] = ["one end only"]
    else:
        raw["dimensions"].append(deepcopy(raw["dimensions"][0]))
    with pytest.raises(ValueError):
        interpret_evidence_map(raw, source_map=evidence, zone_ids={"z"})


def test_measurement_reference_compiles_numeric_value_and_2vn_binding_without_retyping():
    row, pages = fixture()
    evidence = interpret_evidence_map(reading(), source_map=build_evidence_map(input_row=row, page_bytes_by_ref=pages), zone_ids={"z"})
    scope = {"construction_version": "v6", "evidence_map": evidence}
    result = apply_evidence_measurements({"document_unit": {"unit": "cm"}, "assemblies": [
        {"assembly_id": "z", "dimensions": {"depth": {"measurement_id": "dimension-001"}}}]}, scope=scope)
    assert result["assemblies"][0]["dimensions"]["depth"]["value"] == 72
    result["composition_scope"] = scope
    resolved, audit = resolve_2vn_geometry(dimension_graph=build_dimension_graph(input_row=row), extraction=result)
    assert resolved["assemblies"][0]["dimensions"]["depth"]["basis"] == "source"
    assert audit["dimension_witnesses"][0]["ownership_reading_agrees"] is True
    result["assemblies"][0]["panel_groups"] = [{"group_id": "ribs", "dimensions": {
        "width": {"value": 72, "unit": "cm", "basis": "source", "evidence_refs": ["n"]}}}]
    group_result, group_audit = resolve_2vn_geometry(dimension_graph=build_dimension_graph(input_row=row), extraction=result)
    assert group_result["assemblies"][0]["panel_groups"][0]["dimensions"]["width"]["basis"] == "assumption"
    assert group_audit["binding_outcomes"]["unbound_member_face"] == 1
    result["assemblies"][0]["assembly_id"] = "foreign"
    result["dimension_bindings"][0]["assembly_id"] = "foreign"
    resolved, _ = resolve_2vn_geometry(dimension_graph=build_dimension_graph(input_row=row), extraction=result)
    assert resolved["assemblies"][0]["dimensions"]["depth"]["basis"] == "assumption"


def test_measurement_cannot_copy_an_overall_dimension_to_a_subassembly():
    row, pages = fixture()
    raw = reading()
    raw["dimensions"][0]["scope_id"] = None
    evidence = interpret_evidence_map(raw, source_map=build_evidence_map(input_row=row, page_bytes_by_ref=pages), zone_ids={"z"})
    with pytest.raises(ValueError, match="ownership"):
        apply_evidence_measurements({"assemblies": [{"assembly_id": "z", "dimensions": {
            "depth": {"measurement_id": "dimension-001"}}}]}, scope={"evidence_map": evidence})


def test_index_links_retain_cross_page_definition_without_claiming_applicability():
    row, pages = fixture()
    row["input_payload"]["evidence"]["ocr_blocks"].append({"block_ref": "callout", "page_number": 1, "text": "VN11"})
    row["input_payload"]["document_context"] = {"ocr_blocks": [
        {"block_ref": "legend", "page_number": 2, "text": "VN11: oak veneer"}]}
    evidence = build_evidence_map(input_row=row, page_bytes_by_ref=pages)
    assert evidence["index_links"] == [{"index": "VN11", "evidence_refs": ["callout", "legend"],
        "relation": "same_literal_index_candidate"}]
    assert next(n for n in evidence["text_nodes"] if n["block_ref"] == "legend")["page_number"] == 2


def test_conflicting_axis_readings_remain_assumptions_and_auditable():
    row, pages = fixture()
    row["input_payload"]["evidence"]["ocr_blocks"].append({
        **deepcopy(row["input_payload"]["evidence"]["ocr_blocks"][0]), "block_ref": "n2", "text": "145 cm"})
    raw = reading()
    raw["dimensions"].append({**deepcopy(raw["dimensions"][0]), "dimension_id": "dimension-002"})
    evidence = interpret_evidence_map(raw, source_map=build_evidence_map(input_row=row, page_bytes_by_ref=pages), zone_ids={"z"})
    assert evidence["status"] == "needs_review"
    assert evidence["conflicts"][0]["reason"] == "multiple_values_for_one_assembly_axis"
    assert all(r["ownership_status"] == "conflicting" for r in evidence["dimension_readings"])
    scope = {"construction_version": "v6", "evidence_map": evidence}
    result = apply_evidence_measurements({"assemblies": [{"assembly_id": "z", "dimensions": {
        "depth": {"measurement_id": "dimension-001"}}}]}, scope=scope)
    assert result["assemblies"][0]["dimensions"]["depth"]["basis"] == "assumption"
    assert result["dimension_bindings"] == []
    assert result["omissions"]


def test_native_lines_require_matching_declared_coordinate_basis():
    row, pages = fixture()
    geometry = row["input_payload"]["evidence"]["geometry_context"]
    geometry["vector_line_segments"] = [{"segment_id": "native", "page_number": 1,
        "orientation": "horizontal", "start": {"x": 200, "y": 116}, "end": {"x": 600, "y": 116},
        "coordinate_basis": "native_pdf_vector_rendered_pixels"}]
    evidence = build_evidence_map(input_row=row, page_bytes_by_ref={})
    assert evidence["pages"][0]["line_status"] == "native_candidates"
    geometry["vector_line_segments"][0]["coordinate_basis"] = "native_pdf_points"
    evidence = build_evidence_map(input_row=row, page_bytes_by_ref={})
    assert evidence["pages"][0]["line_status"] == "page_image_unavailable"
    assert evidence["dimensions"][0]["line_candidates"] == []


def test_scope_handoff_preserves_authoritative_map_but_compacts_model_transport():
    from use_cases.estimation_composition_scope import validate_composition_scope, geometry_scope
    row, pages = fixture()
    evidence = interpret_evidence_map(reading(), source_map=build_evidence_map(input_row=row, page_bytes_by_ref=pages), zone_ids={"z"})
    scope = {"contract_version": "estimation_composition_scope_v1", "input_id": "i", "object_id": "o",
        "construction_version": "v6", "material_palette": {}, "evidence_map": evidence,
        "zones": [{"scope_id": "z", "assembly_role": "drawer_bank", "operability": "drawer",
                   "counts": {"drawers": 3}, "material_roles": []}]}
    validated = validate_composition_scope(scope=scope, input_id="i")
    assert validated["evidence_map"] == evidence
    compact = geometry_scope(validated)["evidence_map"]
    assert compact["dimension_readings"] == evidence["dimension_readings"]
    assert "dimensions" not in compact  # Raw graph is already supplied separately.
    assert "dimensions" in validated["evidence_map"]  # Persisted provenance is intact.
