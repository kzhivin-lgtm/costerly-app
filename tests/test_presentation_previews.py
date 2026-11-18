"""UI preview selection, inheritance and ownership, separate from model evidence."""
from io import BytesIO
from types import SimpleNamespace

import pandas as pd
from PIL import Image
import pytest

from agents.detection_agent import _registry_to_detection_result, _select_presentation_view
from db.repositories import fetch_rfq_detected_object_presentation
from use_cases import detection_previews, estimation
from use_cases.rfq_processing import _normalize_object


def view(kind, *, group_id=None, area=100, page=1):
    return {"group_id": group_id or kind, "page_number": page,
            "representation_kind": kind,
            "bbox": {"top_left_x": 10, "top_left_y": 10,
                     "bottom_right_x": 10 + area, "bottom_right_y": 110}}


def choose(groups, *, ui=True):
    return _select_presentation_view(
        {"visual_group_ids": [g["group_id"] for g in groups]},
        visual_groups_by_id={g["group_id"]: g for g in groups},
        evidence_pages={1}, ui_preview=ui,
    )


@pytest.mark.parametrize("kind", [
    "isometric", "isometric_technical", "technical_isometric", "axonometric",
    "technical_perspective", "presentation_render", "perspective_view",
    "Axonometric", "isometric-technical",
])
def test_ui_prefers_available_axonometry_over_larger_front_or_plan(kind):
    assert choose([view("top_plan", area=800), view("front_elevation", area=600),
                   view(kind, area=100)])["representation_kind"] == kind


@pytest.mark.parametrize("kind", ["front_elevation", "orthographic_elevation", "elevation_view"])
def test_ui_uses_elevation_when_no_axonometry_exists(kind):
    assert choose([view("plan_view", area=800), view("section", area=600),
                   view(kind, area=100)])["representation_kind"] == kind


def test_plan_is_last_resort_and_missing_owned_view_stays_unavailable():
    assert choose([view("top_plan", area=800), view("unknown", area=100)])["representation_kind"] == "unknown"
    assert choose([view("top_plan")])["representation_kind"] == "top_plan"
    assert choose([view("isometric", page=2)]) is None


def test_naming_retains_its_original_selection_even_when_ui_uses_axonometry():
    groups = [view("isometric", area=800), view("front_elevation", area=100)]
    assert choose(groups)["representation_kind"] == "isometric"
    assert choose(groups, ui=False)["representation_kind"] == "front_elevation"
    # Unknown legacy Naming labels still use their accepted area tie-break.
    groups = [view("isometric_technical", area=100), view("orthographic_elevation", area=800)]
    assert choose(groups, ui=False)["representation_kind"] == "orthographic_elevation"


def test_detection_crop_is_persisted_once_and_both_screens_inherit_its_ref(monkeypatch):
    groups = [view("isometric", area=100), view("front_elevation", area=400)]
    result = _registry_to_detection_result(
        {"objects": [{"object_id": "object-1", "transport_label": "Cabinet", "quantity": 1,
                      "estimation_evidence_pages": [1],
                      "visual_group_ids": [g["group_id"] for g in groups]}]},
        company_id="company-1", file_name="cabinet.pdf", page_count=1,
        visual_map={"_registry_owned_evidence": groups},
    )
    item = result["detected_objects"][0]
    run_id = item["run_id"]
    ref = f"storage://rfq-estimation-evidence/company-1/{run_id}/object-1/crop.webp"
    image = BytesIO()
    Image.new("RGB", (1000, 800), "white").save(image, format="PNG")
    uploads = []

    def persist(**kwargs):
        uploads.append(kwargs["webp_bytes"])
        return SimpleNamespace(storage_ref=ref)

    def update(_client, **kwargs):
        item.update(kwargs["values"])

    monkeypatch.setattr(detection_previews, "persist_preview_artifact", persist)
    monkeypatch.setattr(detection_previews, "update_rfq_detected_object", update)
    monkeypatch.setattr(detection_previews, "insert_agent_usage_event", lambda *a: None)
    report = detection_previews.create_detection_previews(
        client=object(), company_id="company-1", run_id=run_id, file_name="cabinet.pdf",
        file_bytes=b"unused", objects=[item],
        ocr_package={"pages": [{"page_number": 1, "dimensions": {"width": 1000, "height": 800}}]},
        page_images=[image.getvalue()],
    )
    assert report["created"] == len(uploads) == 1
    with Image.open(BytesIO(uploads[0])) as crop:
        assert crop.size == (112, 112)
    assert _normalize_object(item)["preview_ref"] == ref
    monkeypatch.setattr(estimation, "fetch_rfq_detected_object_presentation", lambda *a, **kw: item)
    monkeypatch.setattr(estimation, "_estimation_preview_url", lambda _client, storage_ref, **kw: storage_ref)
    for _ in range(2):
        assert estimation._load_object_presentation_preview(
            object(), company_id="company-1", run_id=run_id, object_id="object-1",
        ) == ref
    assert len(uploads) == 1
    assert len(item["evidence_page_refs"][0]["regions"]) == 2


@pytest.mark.parametrize("ref", [
    None, "", "storage://rfq-estimation-evidence/other/run-1/object-1/crop.webp",
    "storage://rfq-estimation-evidence/company-1/run-2/object-1/crop.webp",
    "storage://rfq-estimation-evidence/company-1/run-1/object-2/crop.webp",
    "storage://rfq-estimation-evidence/company-1/run-1/object-1/../page.webp",
])
def test_missing_or_foreign_crop_never_uses_a_calculation_page(monkeypatch, ref):
    monkeypatch.setattr(estimation, "fetch_rfq_detected_object_presentation", lambda *a, **kw: {
        "evidence_page_refs": [{"preview_ref": ref}],
        "primary_preview_ref": "storage://rfq-estimation-evidence/company-1/page-1.webp",
    })

    def unexpected(*a, **kw):
        pytest.fail("Missing/foreign crop must not be signed or replaced with a page")

    monkeypatch.setattr(estimation, "_estimation_preview_url", unexpected)
    assert estimation._load_object_presentation_preview(
        object(), company_id="company-1", run_id="run-1", object_id="object-1",
    ) is None


def test_presentation_read_failure_is_logged_and_keeps_detail_actionable(monkeypatch, caplog):
    def fail(*a, **kw):
        raise RuntimeError("preview read unavailable")
    monkeypatch.setattr(estimation, "fetch_rfq_detected_object_presentation", fail)
    assert estimation._load_object_presentation_preview(
        object(), company_id="company-1", run_id="run-1", object_id="object-1",
    ) is None
    assert "Could not load saved object presentation" in caplog.text


def test_preview_repository_read_is_scoped_to_company_run_and_object():
    class Query:
        filters = {}
        def table(self, name):
            assert name == "rfq_detected_objects"
            return self
        def select(self, fields):
            assert fields == "evidence_page_refs"
            return self
        def eq(self, key, value):
            self.filters[key] = value
            return self
        def limit(self, count):
            assert count == 1
            return self
        def execute(self):
            return SimpleNamespace(data=[{"evidence_page_refs": []}])
    query = Query()
    assert fetch_rfq_detected_object_presentation(
        query, company_id="company-1", run_id="run-1", object_id="object-1",
    ) == {"evidence_page_refs": []}
    assert query.filters == {"company_id": "company-1", "run_id": "run-1", "object_id": "object-1"}


def test_real_detail_loader_inherits_detection_crop_instead_of_bom_page(monkeypatch):
    crop = "storage://rfq-estimation-evidence/company-1/run-1/object-1/crop.webp"
    monkeypatch.setattr(estimation, "get_supabase_client", lambda: object())
    monkeypatch.setattr(estimation, "_assert_screen_estimate_access", lambda *a, **kw: None)
    monkeypatch.setattr(estimation, "fetch_rfq_object_estimates", lambda *a: pd.DataFrame([{
        "object_id": "object-1", "run_id": "run-1", "company_id": "company-1",
        "object_name": "Cabinet", "quantity": 1,
    }]))
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_lines_for_object", lambda *a, **kw: pd.DataFrame())
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_material_plan", lambda *a: pd.DataFrame([{
        "plan_status": "planned", "plan_payload": {"parts_check": {"object-1": {
            "primary_preview_ref": "storage://rfq-estimation-evidence/company-1/run-1/object-1/page-1.webp",
        }}},
    }]))
    monkeypatch.setattr(estimation, "fetch_company_overhead_settings", lambda *a: pd.DataFrame())
    monkeypatch.setattr(estimation, "fetch_rfq_detected_object_presentation", lambda *a, **kw: {
        "evidence_page_refs": [{"preview_ref": crop}],
    })
    monkeypatch.setattr(estimation, "_estimation_preview_url", lambda _client, ref, **kw: ref)
    detail = estimation.load_object_detail_data(estimate_id="estimate-1", object_id="object-1")
    assert detail["preview_url"] == crop
