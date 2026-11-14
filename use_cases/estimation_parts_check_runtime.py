"""Produce and publish Parts Check from the immutable File Review handoff."""

from contextlib import contextmanager
from datetime import UTC, datetime
from hashlib import sha256
import json
import logging
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from threading import RLock
from uuid import uuid4

from db.repositories import insert_agent_usage_event, insert_agent_usage_events
from use_cases.estimation_artifacts import _upload_immutable_artifact, download_evidence_artifact
from use_cases.estimation_detection_context_v7 import build_context
from use_cases.estimation_originals import ORIGINALS_BUCKET

VERSION = "estimation-v9.33-parts-check"
OPERATION = "estimation_v9_parts_check"
_LOCK = RLock()
_RUNNING = set()
_LOG = logging.getLogger(__name__)


class PartsCheckRequestError(RuntimeError):
    def __init__(self, stage, reason):
        self.stage = stage
        self.reason = reason
        super().__init__(f"{stage}: {reason}")


def _reports(client, company_id, run_id, estimate_id):
    return (client.table("agent_usage_events").select("status,raw_usage")
            .eq("company_id", company_id).eq("run_id", run_id).eq("operation", OPERATION)
            .eq("raw_usage->>estimate_id", estimate_id).order("created_at", desc=True).limit(1).execute().data or [])


def _source_event(client, company_id, run_id):
    rows = (client.table("agent_usage_events").select("id,company_id,run_id,raw_usage")
            .eq("company_id", company_id).eq("run_id", run_id).eq("status", "succeeded")
            .eq("operation", "rfq_detection_visual_registry")
            .order("created_at", desc=True).limit(12).execute().data or [])
    for row in rows:
        audit = row.get("raw_usage") or {}
        if isinstance(audit, dict) and audit.get("view_evidence_packages"):
            return row
    raise ValueError("Published Detection evidence is unavailable")


def _request_provider(company_id, run_id, file_name, usage_events):
    from anthropic import APIError
    from agents.anthropic_adapter import build_agent_usage_event, extract_text_from_claude_response, get_anthropic_client
    from agents.estimation_v4_1_material_facts_agent import _create_message_with_hard_timeout, _json_object

    anthropic = get_anthropic_client().with_options(timeout=120, max_retries=0)

    def invoke(stage, request, validate):
        started = datetime.now(UTC).isoformat()
        try:
            response = _create_message_with_hard_timeout(anthropic, timeout_seconds=120, **request)
        except (APIError, RuntimeError) as exc:
            raise PartsCheckRequestError(stage, type(exc).__name__) from exc
        event = build_agent_usage_event(
            agent_name="estimation", operation="estimation_v9_parts_check_request",
            company_id=company_id, run_id=run_id, file_name=file_name, object_id=None, object_name=None,
            model=request["model"], prompt_version=VERSION, response=response, started_at=started,
            finished_at=datetime.now(UTC).isoformat(),
            request_diagnostics={"stage": stage, "stop_reason": response.stop_reason},
        )
        usage_events.append(event)
        try:
            if response.stop_reason != "end_turn":
                raise PartsCheckRequestError(stage, "incomplete_response")
            return validate(_json_object(extract_text_from_claude_response(response)))
        except (KeyError, TypeError, ValueError) as exc:
            event["raw_usage"]["validation_error"] = type(exc).__name__
            raise PartsCheckRequestError(stage, "invalid_response") from exc

    return invoke


def _artifact_prefix(company_id, run_id, estimate_id):
    if not all(re.fullmatch(r"[A-Za-z0-9_-]+", part) for part in (company_id, run_id, estimate_id)):
        raise ValueError("Invalid Parts Check identity")
    return f"{company_id}/{run_id}/parts-check/{estimate_id}/"


def _read_report_payload(client, *, company_id, run_id, estimate_id, digest):
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Invalid Parts Check artifact hash")
    path = _artifact_prefix(company_id, run_id, estimate_id) + f"{digest}.json"
    payload = download_evidence_artifact(client=client, storage_ref=f"storage://{ORIGINALS_BUCKET}/{path}",
                                         bucket=ORIGINALS_BUCKET)
    if sha256(payload).hexdigest() != digest:
        raise ValueError("Parts Check artifact changed after publication")
    return payload


@contextmanager
def _running_report(key):
    with _LOCK:
        _RUNNING.add(key)
    try:
        yield
    finally:
        with _LOCK:
            _RUNNING.discard(key)


def _write_source_pdf(path, file_name, file_bytes):
    extension = Path(file_name).suffix.lower()
    if extension == ".pdf":
        path.write_bytes(file_bytes)
    elif extension in {".png", ".jpg", ".jpeg"}:
        import pymupdf

        with pymupdf.open(stream=file_bytes, filetype=extension[1:]) as image:
            path.write_bytes(image.convert_to_pdf())
    else:
        raise ValueError("Unsupported Estimation document format")


def run_parts_check_for_estimate(*, client, estimate_id, run_id, company_id, file_name, file_bytes, inputs, ocr_package):
    """Return the saved report to the same estimate worker that will price it."""
    key = (company_id, run_id, estimate_id)
    with _running_report(key):
        return _run(client=client, estimate_id=estimate_id, run_id=run_id, company_id=company_id,
                    file_name=file_name, file_bytes=file_bytes, inputs=inputs, ocr_package=ocr_package)


def _run(*, client, estimate_id, run_id, company_id, file_name, file_bytes, inputs, ocr_package):
    usage_events = []
    status = "failed"
    started = datetime.now(UTC).isoformat()
    input_ids = sorted(row["input_id"] for row in inputs)
    original_sha256 = sha256(file_bytes).hexdigest()
    details = {"estimate_id": estimate_id, "input_ids": input_ids, "source_pdf_sha256": original_sha256}
    stage = "load_detection"
    report = None
    directory = None
    try:
        prior = _reports(client, company_id, run_id, estimate_id)
        if (prior and prior[0]["status"] == "succeeded" and prior[0]["raw_usage"].get("input_ids") == input_ids
                and prior[0]["raw_usage"].get("source_pdf_sha256") == original_sha256):
            return json.loads(_read_report_payload(
                client, company_id=company_id, run_id=run_id, estimate_id=estimate_id,
                digest=prior[0]["raw_usage"].get("report_sha256"),
            ))
        detection = _source_event(client, company_id, run_id)
        context = build_context(inputs=inputs, event=detection, ocr_package=ocr_package,
                                include_measurements=True, published_partition=True)
        details["detection_event_id"] = detection["id"]
        stage = "run_parts_check"
        from tools.probe_estimation_v9 import run_parts_check

        directory = TemporaryDirectory(prefix="costerly-parts-check-")
        folder = Path(directory.name)
        pdf = folder / "source.pdf"
        _write_source_pdf(pdf, file_name, file_bytes)
        report = run_parts_check(pdf=pdf, detection_context=context, output=folder / "output",
                                 inputs=inputs, request_provider=_request_provider(
                                     company_id, run_id, file_name, usage_events))
        expected_objects = {row["input_payload"]["object"]["object_id"] for row in inputs}
        if report["stage"] != "Parts Check" or set(report["objects"]) != expected_objects:
            raise ValueError("Parts Check must report every accepted File Review object")
        report.update(estimation_version=VERSION, run_id=run_id, estimate_id=estimate_id,
                      source_pdf_sha256=original_sha256, detection_event_id=detection["id"], input_ids=input_ids)
        if (folder / "output" / "result.json").exists():
            report["overlay_revision"] = uuid4().hex
        payload = (json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
        digest = sha256(payload).hexdigest()
        stage = "publish_parts_check"
        path = _artifact_prefix(company_id, run_id, estimate_id) + f"{digest}.json"
        _upload_immutable_artifact(client=client, path=path, payload=payload, content_type="application/json",
                                   bucket=ORIGINALS_BUCKET)
        details.update(report_sha256=digest, source_coverage=report["source_coverage"],
                       part_rows=sum(len(obj["parts"]) for obj in report["objects"].values()))
        status = "succeeded"
        if "overlay_revision" in report:
            try:
                from use_cases.estimation_overlay_runtime import queue_overlay_pdfs

                queue_overlay_pdfs(directory, company_id=company_id, run_id=run_id, estimate_id=estimate_id,
                                   revision=report["overlay_revision"], file_name=file_name)
                directory = None
            except Exception:
                _LOG.exception("Could not queue Estimation overlays for %s", estimate_id)
    except Exception as exc:
        details.update(failure_stage=stage, error_type=type(exc).__name__)
        if isinstance(exc, PartsCheckRequestError):
            details.update(request_stage=exc.stage, request_error=exc.reason)
        _LOG.warning("Parts Check %s failed for run %s: %s", stage, run_id, exc if isinstance(
            exc, PartsCheckRequestError) else type(exc).__name__)
    finally:
        if directory is not None:
            directory.cleanup()
    # The status makes the report discoverable. Publish it independently of model metrics.
    insert_agent_usage_event(client, {
        "company_id": company_id, "run_id": run_id, "file_name": file_name, "agent_name": "estimation",
        "operation": OPERATION, "model": "deterministic", "prompt_version": VERSION, "status": status,
        "input_tokens": 0, "output_tokens": 0,
        "started_at": started, "finished_at": datetime.now(UTC).isoformat(), "raw_usage": details,
    })
    try:
        insert_agent_usage_events(client, usage_events)
    except Exception as exc:
        _LOG.warning("Parts Check usage persistence failed for run %s: %s", run_id, type(exc).__name__)
    return report if status == "succeeded" else None


def load_parts_check(*, client, company_id, run_id, estimate_id):
    """Load only a report attached to this tenant's exact estimate and upload."""
    estimates = (client.table("rfq_estimates").select("estimate_id").eq("company_id", company_id)
                 .eq("run_id", run_id).eq("estimate_id", estimate_id).limit(1).execute().data or [])
    if not estimates:
        return {"status": "unavailable"}
    with _LOCK:
        if (company_id, run_id, estimate_id) in _RUNNING:
            return {"status": "running"}
    rows = _reports(client, company_id, run_id, estimate_id)
    if not rows:
        return {"status": "unavailable"}
    event = rows[0]
    if event["status"] != "succeeded":
        return {"status": "failed", "stage": event["raw_usage"].get("failure_stage")}
    details = event["raw_usage"]
    payload = _read_report_payload(client, company_id=company_id, run_id=run_id, estimate_id=estimate_id,
                                   digest=details["report_sha256"])
    return {"status": "ready", "payload": payload, "part_rows": details["part_rows"],
            "input_ids": details.get("input_ids", ())}
