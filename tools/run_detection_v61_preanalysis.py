"""Run one V6.1 passive-preanalysis benchmark and write a compact report."""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.detection_page_images import render_detection_pdf_pages
from agents.ocr_rendering import run_mistral_document_evidence_ocr
from agents.detection_agent import run_detection_agent
from agents.pdf_page_inspection import compact_page_profile_audit


PDF_PATH = Path(sys.argv[1])
RUN_LABEL = sys.argv[2] if len(sys.argv) > 2 else str(int(time.time() * 1000))
REPORT_PATH = Path("/private/tmp") / f"detection_v61_{PDF_PATH.stem}_{RUN_LABEL}.json"


def _compact_detection_audit(event: dict) -> dict:
    raw = event.get("raw_usage") or {}
    return {
        "route": (
            raw.get("detection_v6_12_document_category")
            or raw.get("detection_v4_2_model_route")
        ),
        "visual_group_counts_by_page": raw.get("visual_group_counts_by_page"),
        "raw_visual_group_counts_by_page": raw.get("raw_visual_group_counts_by_page"),
        "registry_object_count": raw.get("registry_object_count"),
        "proof_graph_components": raw.get("proof_graph_components"),
        "package_decisions": raw.get("package_decisions"),
        "unassigned_visual_group_count": raw.get("unassigned_visual_group_count"),
        "unassigned_object_evidence_group_count": raw.get(
            "unassigned_object_evidence_group_count"
        ),
        "fusion_page_profiles": raw.get("fusion_page_profiles"),
        "pre_discovery_region_count": raw.get("region_count"),
        "pre_discovery_region_image_bytes": raw.get("registry_crop_image_bytes"),
    }


def _compact_provider_usage(event: dict) -> dict:
    raw = event.get("raw_usage") or {}
    return {
        key: event.get(key)
        for key in (
            "model",
            "input_tokens",
            "output_tokens",
            "input_cost_usd",
            "output_cost_usd",
            "total_cost_usd",
            "duration_seconds",
        )
    } | {
        "proposal": raw.get("v5_9_proposal"),
        "review": raw.get("v5_9_review"),
    }


def main() -> None:
    started = time.monotonic()
    file_bytes = PDF_PATH.read_bytes()
    ocr_started = time.monotonic()
    ocr = run_mistral_document_evidence_ocr(
        file_name=PDF_PATH.name, file_bytes=file_bytes,
    )
    ocr_seconds = time.monotonic() - ocr_started
    render_started = time.monotonic()
    page_images, page_image_diagnostics = render_detection_pdf_pages(file_bytes)
    render_seconds = time.monotonic() - render_started
    detection_started = time.monotonic()
    result = run_detection_agent(
        file_name=PDF_PATH.name,
        company_id="v61-local-benchmark",
        file_bytes=file_bytes,
        ocr_package=ocr,
        page_images=page_images,
        page_image_diagnostics=page_image_diagnostics,
    )
    detection_seconds = time.monotonic() - detection_started
    events = result.pop("_agent_usage_events", [])
    event = events[0] if events else {}
    report = {
        "version": "V6.1-passive-page-preanalysis",
        "pdf": str(PDF_PATH),
        "timing_seconds": {
            "total_wall": round(time.monotonic() - started, 3),
            "ocr": round(ocr_seconds, 3),
            "page_render": round(render_seconds, 3),
            "detection": round(detection_seconds, 3),
            "native_page_inspection": ocr.get("native_pdf_inspection"),
        },
        "page_profiles": compact_page_profile_audit(ocr),
        "provider_usage": _compact_provider_usage(event),
        "detected_objects": [
            {
                "object_id": item.get("object_id"),
                "quantity": item.get("quantity"),
                "evidence_pages": item.get("evidence_pages"),
            }
            for item in result.get("detected_objects") or []
        ],
        "detection_audit": _compact_detection_audit(event),
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "report": str(REPORT_PATH),
        "page_profile_count": len(report["page_profiles"]),
        "object_count": len(report["detected_objects"]),
        "islands_by_page": report["detection_audit"]["visual_group_counts_by_page"],
        "timing_seconds": report["timing_seconds"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        REPORT_PATH.write_text(json.dumps({
            "version": "V6.1-passive-page-preanalysis",
            "error": repr(exc),
            "traceback": traceback.format_exc(),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
