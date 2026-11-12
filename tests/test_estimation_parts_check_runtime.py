import hashlib

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
