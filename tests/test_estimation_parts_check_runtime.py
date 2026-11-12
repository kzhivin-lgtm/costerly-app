import hashlib

import pytest

from tools import probe_estimation_v9
from use_cases import estimation_parts_check_runtime as runtime
from use_cases.estimation_detection_context_v7 import build_context


def test_published_partition_accepts_singletons_and_keeps_only_bound_dimensions():
    box = dict(top_left_x=10, top_left_y=10, bottom_right_x=70, bottom_right_y=70)
    inputs = [{"input_id": "input", "input_payload": {
        "contract_version": "estimation_input_v4", "company_id": "company", "run_id": "run",
        "object": {"object_id": "object", "quantity": 1,
                   "evidence_pages": [{"page_number": 1, "regions": [box]}]},
    }}]
    event = {"id": "detection", "company_id": "company", "run_id": "run", "raw_usage": {
        "view_evidence_packages": [{"visual_group_id": "view", "page_number": 1, "bbox": box,
                                    "source_facts": [{"fact_id": "note", "source": "native_pdf_text"}]}],
        "v5_9_coordinate_frame_audit": [{"page_number": 1, "source": "mistral_page_dimensions",
                                         "fusion_dimensions": {"width": 100, "height": 100}}],
        "dimension_inventory_valid": True,
        "dimension_inventory": [{"group_id": "view", "occurrences": [
            {"occurrence_id": "datum", "value_mm": "0", "source_fact_ids": ["note"]},
            {"occurrence_id": "width", "value_mm": "510", "source_fact_ids": ["note"]},
            {"occurrence_id": "unbound", "value_mm": "720", "source_fact_ids": ["unknown"]},
        ]}],
    }}
    context = build_context(inputs=inputs, event=event, include_measurements=True, published_partition=True)
    obj, = context["objects"]
    assert obj["islands"][0]["island_id"] == "view"
    measurement, = obj["dimension_inventory"][0]["occurrences"]
    assert measurement["occurrence_id"] == "width"
    assert measurement["source_refs"] == ["detection:detection:note"]


def test_parts_check_download_is_bound_to_estimate_owner_and_content(monkeypatch):
    payload = b'{"stage":"Parts Check"}'
    digest = hashlib.sha256(payload).hexdigest()

    class EstimateQuery:
        def __init__(self):
            self.filters = {}

        def select(self, *_):
            return self

        def eq(self, key, value):
            self.filters[key] = value
            return self

        def limit(self, _):
            return self

        def execute(self):
            self.data = ([{"estimate_id": "estimate"}] if self.filters == {
                "company_id": "owner", "run_id": "run", "estimate_id": "estimate"} else [])
            return self

    class Client:
        def table(self, name):
            assert name == "rfq_estimates"
            return EstimateQuery()

    reads = []
    monkeypatch.setattr(runtime, "_reports", lambda *_: [
        {"status": "succeeded", "raw_usage": {"report_sha256": digest, "part_rows": 1}}
    ])
    monkeypatch.setattr(runtime, "download_evidence_artifact",
                        lambda **kwargs: reads.append(kwargs["storage_ref"]) or payload)
    assert runtime.load_parts_check(client=Client(), company_id="other", run_id="run",
                                    estimate_id="estimate") == {"status": "unavailable"}
    assert reads == []
    report = runtime.load_parts_check(client=Client(), company_id="owner", run_id="run", estimate_id="estimate")
    assert report == {"status": "ready", "payload": payload, "part_rows": 1}
    assert reads == [f"storage://{runtime.ORIGINALS_BUCKET}/owner/run/parts-check/estimate/{digest}.json"]


@pytest.mark.parametrize("pipeline_fails", [False, True])
def test_parts_check_status_survives_usage_write_failure(monkeypatch, pipeline_fails):
    class Client:
        def table(self, name):
            assert name == "agent_usage_events"
            return self

        def insert(self, payload):
            self.payload = payload
            return self

        def execute(self):
            if isinstance(self.payload, list):
                write_attempts.append("usage")
                raise RuntimeError("Model usage storage failed")
            write_attempts.append("status")
            statuses.append(self.payload)

    def run_pipeline(*, request_provider, **_):
        request_provider.append({"operation": "estimation_v9_parts_check_request",
                                 "input_tokens": 10, "output_tokens": 2})
        if pipeline_fails:
            raise ValueError("Invalid model response")
        return {"stage": "Parts Check", "source_coverage": "reviewed",
                "objects": {"object": {"parts": [{"role": "drawer"}]}}}

    client = Client()
    write_attempts = []
    statuses = []
    uploads = []
    monkeypatch.setattr(runtime, "get_supabase_client", lambda: client)
    monkeypatch.setattr(runtime, "_reports", lambda *_: [])
    monkeypatch.setattr(runtime, "_source_event", lambda *_: {"id": "detection"})
    monkeypatch.setattr(runtime, "build_context", lambda **_: {})
    monkeypatch.setattr(runtime, "_request_provider", lambda *args: args[-1])
    monkeypatch.setattr(runtime, "_upload_immutable_artifact", lambda **kwargs: uploads.append(kwargs))
    monkeypatch.setattr(probe_estimation_v9, "run_parts_check", run_pipeline)

    runtime._run(estimate_id="estimate", run_id="run", company_id="company", file_name="source.pdf",
                 file_bytes=b"pdf", inputs=[{"input_id": "input", "input_payload": {
                     "object": {"object_id": "object"},
                 }}], ocr_package={})

    assert write_attempts == ["status", "usage"]
    status, = statuses
    assert status["operation"] == runtime.OPERATION
    assert status["input_tokens"] == status["output_tokens"] == 0
    if pipeline_fails:
        assert status["status"] == "failed"
        assert status["raw_usage"]["failure_stage"] == "run_parts_check"
        assert status["raw_usage"]["error_type"] == "ValueError"
        assert not uploads
    else:
        upload, = uploads
        assert status["status"] == "succeeded"
        assert status["raw_usage"]["report_sha256"] == hashlib.sha256(upload["payload"]).hexdigest()
