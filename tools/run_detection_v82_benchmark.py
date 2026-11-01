"""Run one isolated Detection V8.2 benchmark without changing the default route."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
import traceback

from agents.detection_agent import run_detection_agent
from agents.detection_page_images import render_detection_pdf_pages
from agents.ocr_rendering import run_mistral_document_evidence_ocr


PDF_PATH = Path(sys.argv[1])
RUN_LABEL = sys.argv[2] if len(sys.argv) > 2 else str(int(time.time() * 1000))
REPORT_PATH = Path("/private/tmp") / f"detection_v82_{PDF_PATH.stem}_{RUN_LABEL}.json"


def _compact_pipeline(event: dict) -> dict:
    raw = event.get("raw_usage") if isinstance(event, dict) else {}
    audit = (raw or {}).get("detection_v8_2") if isinstance(raw, dict) else {}
    pipeline = audit.get("pipeline") if isinstance(audit, dict) else {}
    discovery = pipeline.get("discovery") if isinstance(pipeline, dict) else {}
    membership = pipeline.get("membership") if isinstance(pipeline, dict) else {}
    return {
        "release": audit.get("release") if isinstance(audit, dict) else None,
        "candidate_region_count": len(pipeline.get("candidate_regions") or []) if isinstance(pipeline, dict) else None,
        "object_evidence_by_page": {
            str(page): sum(1 for view in discovery.get("object_evidence") or [] if int(view.get("page_number") or 0) == page)
            for page in sorted({int(view.get("page_number") or 0) for view in discovery.get("object_evidence") or []})
        },
        "exclusions": [{
            "page_number": view.get("page_number"), "representation_kind": view.get("representation_kind"),
            "exclusion_kind": view.get("exclusion_kind"),
        } for view in discovery.get("excluded") or []],
        "resolver": pipeline.get("conflict_resolver"),
        "accepted_membership_link_count": len(membership.get("accepted_links") or []),
        "rejected_membership_links": membership.get("rejected_links"),
        "component_count": len(pipeline.get("components") or []) if isinstance(pipeline, dict) else None,
        "components": pipeline.get("components"),
        "unattached_presentation_renders": pipeline.get("excluded_unattached_presentation_renders"),
    }


def main() -> None:
    if not PDF_PATH.is_file():
        raise FileNotFoundError(PDF_PATH)
    file_bytes = PDF_PATH.read_bytes()
    started = time.monotonic()
    ocr_started = time.monotonic()
    ocr_package = run_mistral_document_evidence_ocr(file_name=PDF_PATH.name, file_bytes=file_bytes)
    ocr_seconds = time.monotonic() - ocr_started
    render_started = time.monotonic()
    page_images, page_image_diagnostics = render_detection_pdf_pages(file_bytes)
    render_seconds = time.monotonic() - render_started
    detection_started = time.monotonic()
    result = run_detection_agent(
        file_name=PDF_PATH.name,
        company_id="v82-local-benchmark",
        file_bytes=file_bytes,
        ocr_package=ocr_package,
        page_images=page_images,
        page_image_diagnostics=page_image_diagnostics,
        pipeline_version="v82",
    )
    detection_seconds = time.monotonic() - detection_started
    events = result.pop("_agent_usage_events", [])
    event = events[0] if events else {}
    report = {
        "version": "detection_v8_2_0",
        "pdf": str(PDF_PATH),
        "timing_seconds": {
            "total_wall": round(time.monotonic() - started, 3),
            "ocr": round(ocr_seconds, 3),
            "page_render": round(render_seconds, 3),
            "detection": round(detection_seconds, 3),
        },
        "provider_usage": {key: event.get(key) for key in ("model", "input_tokens", "output_tokens", "input_cost_usd", "output_cost_usd", "total_cost_usd", "duration_seconds")},
        "detected_objects": [{
            "object_id": item.get("object_id"), "quantity": item.get("quantity"), "evidence_pages": item.get("evidence_pages"),
        } for item in result.get("detected_objects") or []],
        "pipeline": _compact_pipeline(event),
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "report": str(REPORT_PATH),
        "object_count": len(report["detected_objects"]),
        "islands_by_page": report["pipeline"]["object_evidence_by_page"],
        "accepted_membership_link_count": report["pipeline"]["accepted_membership_link_count"],
        "timing_seconds": report["timing_seconds"],
        "provider_usage": report["provider_usage"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        REPORT_PATH.write_text(json.dumps({
            "version": "detection_v8_2_0", "error": repr(exc), "traceback": traceback.format_exc(),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
