import pytest

from use_cases.estimation_evidence import (
    EvidenceArtifact,
    build_estimation_input_v2,
    resolve_anchor_bbox,
)
from use_cases.estimation_artifacts import download_evidence_artifact


class _StorageBucket:
    def __init__(self):
        self.path = None

    def download(self, path):
        self.path = path
        return b"preview-bytes"


class _Storage:
    def __init__(self, bucket):
        self.bucket = bucket

    def from_(self, name):
        assert name == "rfq-estimation-evidence"
        return self.bucket


class _StorageClient:
    def __init__(self, bucket):
        self.storage = _Storage(bucket)


def test_private_preview_download_parses_storage_ref_without_exposing_a_public_url():
    bucket = _StorageBucket()

    payload = download_evidence_artifact(
        client=_StorageClient(bucket),
        storage_ref="storage://rfq-estimation-evidence/company/run/object/preview.webp",
    )

    assert payload == b"preview-bytes"
    assert bucket.path == "company/run/object/preview.webp"


RUN = {"run_id": "run-1", "company_id": "company-1", "file_name": "quote.pdf"}
OBJECT = {
    "object_id": "object-1",
    "object_name": "Reception desk",
    "quantity": 2,
    "quantity_explicit": True,
    "dimensions_json": {"unit": "mm", "width": 1200},
    "detected_materials": "MDF 18 mm",
    "notes": "Front elevation",
    "evidence_pages": "1, 3",
}
OCR = {
    "contract_version": "ocr_v2",
    "evidence": {
        "text_blocks": [
            {"page_number": 1, "text": "Reception desk", "bbox": {}},
            {"page_number": 2, "text": "Unrelated", "bbox": {}},
            {"page_number": 3, "text": "MDF 18 mm", "bbox": {}},
        ]
    },
}
ARTIFACTS = (
    EvidenceArtifact(
        storage_ref="storage://rfq-estimation-evidence/company-1/run-1/object-1/r1/preview.webp",
        page_number=1,
        artifact_kind="preview",
    ),
    EvidenceArtifact(
        storage_ref="storage://rfq-estimation-evidence/company-1/run-1/object-1/r1/page-3.webp",
        page_number=3,
        artifact_kind="page",
    ),
)


def test_e03_builder_freezes_only_cited_ocr_blocks_and_private_evidence_refs():
    result = build_estimation_input_v2(
        run=RUN,
        detected_object=OBJECT,
        ocr_event_id="ocr-event-1",
        ocr_package=OCR,
        evidence_artifacts=ARTIFACTS,
        versions={"detection": "v1", "material_catalog": "israel-2026-09"},
    )

    assert result["contract_version"] == "estimation_input_v2"
    assert result["object"]["evidence_pages"] == [
        {"page_number": 1, "source_label": "1"},
        {"page_number": 3, "source_label": "3"},
    ]
    assert [row["text"] for row in result["evidence"]["ocr_blocks"]] == ["Reception desk", "MDF 18 mm"]
    assert [row["block_ref"] for row in result["evidence"]["ocr_blocks"]] == [
        "ocr:ocr-event-1:p1:b0001",
        "ocr:ocr-event-1:p3:b0003",
    ]
    assert result["evidence"]["primary_preview_ref"].endswith("preview.webp")
    assert result["document"]["ocr_event_id"] == "ocr-event-1"


def test_e02_two_objects_share_one_persisted_ocr_result_without_document_reread():
    first = build_estimation_input_v2(
        run=RUN,
        detected_object=OBJECT,
        ocr_event_id="ocr-event-shared",
        ocr_package=OCR,
        evidence_artifacts=ARTIFACTS,
        versions={"detection": "v1"},
    )
    second = build_estimation_input_v2(
        run=RUN,
        detected_object={
            **OBJECT,
            "object_id": "object-2",
            "object_name": "Wall cabinet",
            "evidence_pages": "3",
        },
        ocr_event_id="ocr-event-shared",
        ocr_package=OCR,
        evidence_artifacts=(
            EvidenceArtifact(
                storage_ref="storage://rfq-estimation-evidence/company-1/run-1/object-2/r1/preview.webp",
                page_number=3,
                artifact_kind="preview",
            ),
        ),
        versions={"detection": "v1"},
    )

    assert first["document"]["ocr_event_id"] == second["document"]["ocr_event_id"]
    assert first["object"]["object_id"] != second["object"]["object_id"]
    assert [block["page_number"] for block in second["evidence"]["ocr_blocks"]] == [3]
    assert second["evidence"]["ocr_blocks"][0]["block_ref"] == "ocr:ocr-event-shared:p3:b0003"


def test_builder_rejects_missing_preview_instead_of_using_source_file():
    with pytest.raises(ValueError, match="preview"):
        build_estimation_input_v2(
            run=RUN,
            detected_object=OBJECT,
            ocr_event_id="ocr-event-1",
            ocr_package=OCR,
            evidence_artifacts=(ARTIFACTS[1],),
            versions={},
        )


def test_builder_rejects_non_private_storage_reference():
    with pytest.raises(ValueError, match="private evidence bucket"):
        build_estimation_input_v2(
            run=RUN,
            detected_object=OBJECT,
            ocr_event_id="ocr-event-1",
            ocr_package=OCR,
            evidence_artifacts=(
                EvidenceArtifact(
                    storage_ref="storage://public/preview.webp",
                    page_number=1,
                    artifact_kind="preview",
                ),
            ),
            versions={},
        )


def test_builder_uses_detection_vnext_page_reference_for_drawing_labels():
    result = build_estimation_input_v2(
        run=RUN,
        detected_object={
            **OBJECT,
            "evidence_pages": "A-01",
            "evidence_page_refs": [{"page_number": 2, "source_label": "A-01"}],
        },
        ocr_event_id="ocr-event-1",
        ocr_package=OCR,
        evidence_artifacts=(
            EvidenceArtifact(
                storage_ref="storage://rfq-estimation-evidence/company-1/run-1/object-1/r1/preview.webp",
                page_number=2,
                artifact_kind="preview",
            ),
        ),
        versions={},
    )

    assert result["object"]["evidence_pages"] == [
        {"page_number": 2, "source_label": "A-01"}
    ]


def test_builder_preserves_vnext_evidence_roles_and_preview_bbox():
    result = build_estimation_input_v2(
        run=RUN,
        detected_object={
            **OBJECT,
            "evidence_page_refs": [{
                "page_number": 1, "source_label": "A-01",
                "roles": ["identity", "overall_dimensions"],
                "preview_bbox": {
                    "top_left_x": 1, "top_left_y": 2,
                    "bottom_right_x": 30, "bottom_right_y": 40,
                },
            }],
        },
        ocr_event_id="ocr-event-1",
        ocr_package=OCR,
        evidence_artifacts=(ARTIFACTS[0],),
        versions={},
    )

    assert result["object"]["evidence_pages"] == [{
        "page_number": 1, "source_label": "A-01",
        "roles": ["identity", "overall_dimensions"],
        "preview_bbox": {
            "top_left_x": 1, "top_left_y": 2,
            "bottom_right_x": 30, "bottom_right_y": 40,
        },
    }]


def test_anchor_bbox_requires_one_exact_ocr_match():
    result = resolve_anchor_bbox(
        anchor={"page_number": 1, "text": "Reception desk"},
        ocr_package={
            "evidence": {
                "text_blocks": [
                    {
                        "page_number": 1,
                        "text": "Reception desk",
                        "bbox": {"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 3, "bottom_right_y": 4},
                    }
                ]
            }
        },
    )

    assert result == {
        "page_number": 1,
        "text": "Reception desk",
        "bbox": {"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 3, "bottom_right_y": 4},
    }


def test_anchor_bbox_rejects_ambiguous_or_partial_text():
    package = {
        "evidence": {
            "text_blocks": [
                {"page_number": 1, "text": "DC-01", "bbox": {}},
                {"page_number": 1, "text": "DC-01", "bbox": {}},
            ]
        }
    }

    assert resolve_anchor_bbox(anchor={"page_number": 1, "text": "DC"}, ocr_package=package) is None
    assert resolve_anchor_bbox(anchor={"page_number": 1, "text": "DC-01"}, ocr_package=package) is None
