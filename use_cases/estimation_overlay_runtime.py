"""Publish private review PDFs independently of material calculation."""

from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
import re
from threading import RLock
from time import perf_counter

from db.repositories import insert_agent_usage_event
from db.supabase_client import get_supabase_client
from use_cases.estimation_artifacts import _upload_immutable_artifact
from use_cases.estimation_originals import ORIGINALS_BUCKET

OPERATION = "estimation_overlay_pdf"
VERSION = "estimation-v9.30-overlays"
_WORKER = ThreadPoolExecutor(max_workers=1, thread_name_prefix="estimation-overlay")
_READS = ThreadPoolExecutor(max_workers=2, thread_name_prefix="estimation-overlay-status")
_READ_LOCK = RLock()
_PENDING_READS: dict[tuple[str, ...], Future] = {}
_LOG = logging.getLogger(__name__)


def _prefix(company_id, run_id, estimate_id, revision, object_id):
    values = (company_id, run_id, estimate_id, revision, object_id)
    if not all(re.fullmatch(r"[A-Za-z0-9_-]+", value) for value in values):
        raise ValueError("Invalid overlay identity")
    return f"{company_id}/{run_id}/overlays/{estimate_id}/{revision}/{object_id}/"


def queue_overlay_pdfs(directory, *, company_id, run_id, estimate_id, revision, file_name):
    """Transfer ownership of the temporary source to the background worker."""
    _WORKER.submit(_publish, directory, company_id, run_id, estimate_id, revision, file_name)


def _publish(directory, company_id, run_id, estimate_id, revision, file_name):
    from use_cases.estimation_overlay_pdf import build_overlay_pdfs

    started = datetime.now(UTC).isoformat()
    start = perf_counter()
    paths, errors = {}, []
    render_seconds = 0
    client = None
    try:
        client = get_supabase_client()
        source = Path(directory.name)
        output = source / "output"
        result = json.loads((output / "result.json").read_text())
        geometry = json.loads((output / "geometry" / "estimation-offline-all-islands-evidence.json").read_text())
        rendering = perf_counter()
        for object_id, layer, data in build_overlay_pdfs((source / "source.pdf").read_bytes(), result,
                                                         geometry["documents"]["document"],
                                                         project_name=Path(file_name).stem):
            render_seconds += perf_counter() - rendering
            try:
                path = _prefix(company_id, run_id, estimate_id, revision, object_id) + f"{layer}.pdf"
                _upload_immutable_artifact(client=client, path=path, payload=data,
                                           content_type="application/pdf", bucket=ORIGINALS_BUCKET)
                paths.setdefault(object_id, {})[layer] = path
            except Exception:
                errors.append(f"{object_id}:{layer}")
                _LOG.exception("Could not publish Estimation %s overlay for %s", layer, estimate_id)
            rendering = perf_counter()
    except Exception:
        errors.append("render")
        _LOG.exception("Could not generate Estimation overlays for %s", estimate_id)
    finally:
        directory.cleanup()

    if client is None:
        return
    try:
        insert_agent_usage_event(client, {
            "company_id": company_id, "run_id": run_id, "file_name": file_name, "agent_name": "estimation",
            "operation": OPERATION, "model": "deterministic", "prompt_version": VERSION,
            "status": "failed" if errors else "succeeded", "input_tokens": 0, "output_tokens": 0,
            "started_at": started, "finished_at": datetime.now(UTC).isoformat(),
            "raw_usage": {"estimate_id": estimate_id, "revision": revision, "paths": paths, "errors": errors,
                          "render_seconds": round(render_seconds, 3), "duration_seconds": round(perf_counter() - start, 3)},
        })
    except Exception:
        _LOG.exception("Could not record Estimation overlay status for %s", estimate_id)


def submit_overlay_status(*, company_id, run_id, estimate_id, revision, object_id):
    key = (company_id, run_id, estimate_id, revision, object_id)
    with _READ_LOCK:
        if pending := _PENDING_READS.get(key):
            return pending
        future = _READS.submit(_load_status, *key)
        _PENDING_READS[key] = future
        future.add_done_callback(lambda completed: _finish_read(key, completed))
        return future


def _finish_read(key, future):
    with _READ_LOCK:
        if _PENDING_READS.get(key) is future:
            _PENDING_READS.pop(key)


def _load_status(company_id, run_id, estimate_id, revision, object_id):
    """Sign only the exact uploaded estimate, report revision, object and layer."""
    prefix = _prefix(company_id, run_id, estimate_id, revision, object_id)
    client = get_supabase_client()
    rows = (client.table("agent_usage_events").select("status,raw_usage")
            .eq("company_id", company_id).eq("run_id", run_id).eq("operation", OPERATION)
            .eq("raw_usage->>estimate_id", estimate_id).eq("raw_usage->>revision", revision)
            .order("created_at", desc=True).limit(1).execute().data or [])
    if not rows:
        return None
    paths = rows[0]["raw_usage"].get("paths", {}).get(object_id, {})
    allowed = {layer: path for layer, path in paths.items()
               if layer in {"front", "block"} and path == prefix + f"{layer}.pdf"}
    if not allowed:
        return {}
    signed = client.storage.from_(ORIGINALS_BUCKET).create_signed_urls(list(allowed.values()), 3600)
    urls = {row["path"]: row.get("signedURL") for row in signed if not row.get("error")}
    result = {layer: urls[path] for layer, path in allowed.items() if urls.get(path)}
    if not result:
        raise RuntimeError("Overlay URLs were not signed")
    return result
