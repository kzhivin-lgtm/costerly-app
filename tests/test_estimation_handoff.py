from io import BytesIO

from PIL import Image

from use_cases.estimation_handoff import persist_estimation_v2_shadow_inputs
from use_cases.estimation_originals import describe_estimation_original


class _Response:
    def __init__(self, data): self.data = data


class _Query:
    def __init__(self, client, table): self.client, self.table, self.value = client, table, None
    def insert(self, value): self.value = value; return self
    def execute(self):
        self.client.rows[self.table] = self.value
        if self.table == "rfq_estimation_object_inputs":
            return _Response([{"input_id": "input-1"}])
        return _Response(self.value if isinstance(self.value, list) else [self.value])


class _Bucket:
    def __init__(self, client): self.client = client
    def upload(self, path, data, file_options): self.client.uploads.append((path, data, file_options))


class _Storage:
    def __init__(self, client): self.client = client
    def from_(self, _name): return _Bucket(self.client)


class _Client:
    def __init__(self): self.rows, self.uploads, self.storage = {}, [], _Storage(self)
    def table(self, name): return _Query(self, name)


def _image_bytes():
    image = Image.new("RGB", (100, 100), "white")
    output = BytesIO(); image.save(output, "PNG"); return output.getvalue()


def test_shadow_handoff_persists_preview_input_and_artifact():
    source = _image_bytes()
    client = _Client()
    result = persist_estimation_v2_shadow_inputs(
        client=client,
        run={"run_id": "run-1", "company_id": "company-1", "file_name": "drawing.png"},
        objects=[{
            "object_id": "object-1", "object_name": "Desk", "quantity": 1,
            "quantity_explicit": True, "dimensions_json": {}, "detected_materials": "MDF",
            "notes": "", "evidence_pages": "A-01",
            "evidence_page_refs": [{"page_number": 1, "source_label": "A-01"}],
            "evidence_anchors": [{"page_number": 1, "text": "DC-01"}],
        }],
        ignored_object_ids=set(), file_name="drawing.png", file_bytes=source,
        ocr_event_id="ocr-1",
        ocr_package={"contract_version": "ocr_v2", "pages": [{"page_number": 1, "dimensions": {"width": 100, "height": 100}}],
                     "evidence": {"text_blocks": [{"page_number": 1, "text": "DC-01", "bbox": {"top_left_x": 10, "top_left_y": 10, "bottom_right_x": 50, "bottom_right_y": 50}}]}},
        original=describe_estimation_original(company_id="company-1", file_name="drawing.png", file_bytes=source),
        versions={"detection": "test"},
    )

    assert result["created_input_ids"] == ["input-1"]
    assert result["skipped"] == {}
    assert result["created_inputs"] == [{
        "input_id": "input-1",
        "object_input_revision": 1,
        "input_payload": client.rows["rfq_estimation_object_inputs"]["input_payload"],
    }]
    assert client.uploads[0][0].endswith(".webp")
    assert client.rows["rfq_estimation_object_inputs"]["object_id"] == "object-1"
    assert client.rows["rfq_estimation_evidence_artifacts"][0]["source_label"] == "A-01"


def test_shadow_handoff_uses_source_page_when_image_only_ocr_cannot_resolve_anchor():
    source = _image_bytes()
    client = _Client()
    result = persist_estimation_v2_shadow_inputs(
        client=client,
        run={"run_id": "run-1", "company_id": "company-1", "file_name": "drawing.png"},
        objects=[{
            "object_id": "object-1", "object_name": "Shelving", "quantity": 1,
            "quantity_explicit": True, "dimensions_json": {},
            "detected_materials": "Steel profile", "notes": "",
            "evidence_page_refs": [{"page_number": 1, "source_label": "A-01"}],
            "evidence_anchors": [{"page_number": 1, "text": "20 x 20 profile"}],
        }],
        ignored_object_ids=set(), file_name="drawing.png", file_bytes=source,
        ocr_event_id="ocr-1",
        ocr_package={
            "contract_version": "ocr_v2",
            "pages": [{"page_number": 1, "dimensions": {"width": 100, "height": 100}}],
            "evidence": {"text_blocks": [{
                "page_number": 1,
                "text": "Drawing title",
                "block_type": "header",
                "bbox": {
                    "top_left_x": 0, "top_left_y": 90,
                    "bottom_right_x": 100, "bottom_right_y": 100,
                },
            }]},
        },
        original=describe_estimation_original(
            company_id="company-1", file_name="drawing.png", file_bytes=source
        ),
        versions={"detection": "test"},
    )

    assert result["created_input_ids"] == ["input-1"]
    assert result["skipped"] == {}
    assert client.uploads[0][0].endswith(".webp")
    assert client.rows["rfq_estimation_object_inputs"]["input_payload"]["evidence"][
        "ocr_blocks"
    ] == []
