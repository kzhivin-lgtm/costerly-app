from concurrent.futures import Future
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from agents import detection_coordinate_ocr as reader
from agents.detection_source_capability import assess_detection_source_capability
from agents.anthropic_adapter import build_detection_page_evidence_inventory
from agents.detection_agent import _audit_coordinate_fingerprints


def test_rotated_label_boxes_stay_local_and_feed_the_fingerprint(monkeypatch):
    rotated = [[70, 10], [80, 10], [80, 40], [70, 40]]
    output = SimpleNamespace(
        boxes=[rotated, rotated, rotated],
        txts=["1830", "LED 4000", "1830"],
        scores=[0.92, 0.99, 0.97],
    )
    monkeypatch.setattr(reader, "_engine", lambda _: lambda image: output)
    png = BytesIO()
    Image.new("RGB", (200, 100)).save(png, format="PNG")

    size, labels = reader.read_page_labels(png.getvalue(), Path("/unused"))
    assert size == (200, 100)
    assert len(labels) == 1
    bbox = {"top_left_x": 10, "top_left_y": 20, "bottom_right_x": 40, "bottom_right_y": 30}
    assert labels[0]["bbox"] == bbox
    assert labels[0]["confidence"] == 0.97

    package = {"evidence": {"numeric_labels": [{**labels[0], "page_number": 1}]}}
    route_facts = build_detection_page_evidence_inventory(package)
    source_capability = assess_detection_source_capability(source_facts=route_facts, page_count=1)
    assert source_capability["source_fact_count"] == 0
    assert source_capability["route_eligible"] is True

    locked_view = {
        "page_number": 1, "group_id": "view-001",
        "bbox": {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 50, "bottom_right_y": 50},
    }
    audit = _audit_coordinate_fingerprints(
        ocr_package=package, visual_map={"_registry_owned_evidence": [locked_view]},
        page_images=[], use_review_frame=False, existing_unit="mm",
    )
    dimension = audit["view_fingerprints"][0]["occurrences"][0]
    assert dimension["value_mm"] == "1830"
    assert dimension["source_fact_ids"] == ["COCR00001"]
    assert dimension["normalized_bbox"] == {
        "top_left_x": 0.2, "top_left_y": 0.4, "bottom_right_x": 0.8, "bottom_right_y": 0.6,
    }


def test_collect_keeps_finished_pages_and_cancels_queued_work(monkeypatch):
    monkeypatch.setattr(reader, "_MAX_WAIT_SECONDS", 0)
    job = reader.CoordinateOCR()
    job.enabled = job.available = True
    completed, queued = Future(), Future()
    completed.set_result(((100, 100), [{
        "text": "220",
        "bbox": {"top_left_x": 10, "top_left_y": 20, "bottom_right_x": 30, "bottom_right_y": 40},
    }]))
    job.pending = {completed: 1, queued: 2}

    labels, audit = job.collect([
        {"page_number": 1, "dimensions": {"width": 200, "height": 200}},
        {"page_number": 2, "dimensions": {"width": 200, "height": 200}},
    ])

    assert labels == [{
        "page_number": 1, "text": "220",
        "bbox": {"top_left_x": 20, "top_left_y": 40, "bottom_right_x": 60, "bottom_right_y": 80},
    }]
    assert audit["status"] == "partial"
    assert audit["pages_unavailable"] == {2: "timeout"}
    assert queued.cancelled()


def test_image_detection_ocr_preserves_provider_evidence_and_adds_local_labels(monkeypatch):
    from agents.ocr_rendering import run_mistral_document_evidence_ocr

    monkeypatch.setattr(Path, "is_file", lambda self: True)
    monkeypatch.setattr(reader, "read_page_labels", lambda page_bytes, directory: (
        (100, 100), [{
            "text": "220",
            "source": "test_coordinate_reader",
            "bbox": {"top_left_x": 10, "top_left_y": 20, "bottom_right_x": 30, "bottom_right_y": 40},
        }],
    ))

    def provider(**kwargs):
        return {
            "pages": [{"page_number": 1, "dimensions": {"width": 100, "height": 100}}],
            "evidence": {"text_blocks": [{"text": "cabinet elevation"}]},
            "usage": {"pages_processed": 1},
        }

    package = run_mistral_document_evidence_ocr(
        file_name="drawing.png", file_bytes=b"fixture", page_ocr=provider,
    )
    assert package["evidence"]["text_blocks"] == [{"text": "cabinet elevation"}]
    assert package["evidence"]["numeric_labels"][0]["page_number"] == 1
    assert package["coordinate_ocr"]["status"] == "complete"
    assert package["usage"]["pages_processed"] == 1
