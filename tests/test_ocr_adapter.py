import json

from agents.anthropic_adapter import (
    build_detection_island_dimension_audit,
    build_detection_ocr_context,
)
from agents.ocr_adapter import normalize_mistral_ocr_response, run_mistral_ocr
from agents.ocr_contract import OCR_PROFILE_EVIDENCE


class _FakeResponse:
    def __init__(self, response):
        self.response = response

    def raise_for_status(self):
        return None

    def json(self):
        return self.response


class _FakeHTTPClient:
    def __init__(self, response):
        self.response = response
        self.url = None
        self.kwargs = None

    def post(self, url, **kwargs):
        self.url = url
        self.kwargs = kwargs
        return _FakeResponse(self.response)


def _response():
    return {
        "model": "mistral-ocr-4-0",
        "pages": [
            {
                "index": 0,
                "markdown": "BAR COUNTER\nQTY 3\n4200 x 750 x 1100 mm",
                "dimensions": {"width": 1200, "height": 800},
                "blocks": [{"type": "title", "content": "BAR COUNTER"}],
                "tables": [],
                "images": [],
                "confidence_scores": {"average_page_confidence_score": 0.97},
            }
        ],
        "usage_info": {"pages_processed": 1},
    }


def test_normalizes_mistral_response():
    package = normalize_mistral_ocr_response(
        _response(),
        file_name="drawing.pdf",
        file_bytes=b"pdf bytes",
        model="mistral-ocr-4-0",
        elapsed_seconds=1.2345,
    )

    assert package["contract_version"] == "ocr_v5"
    assert package["profile"] == "basic"
    assert package["page_count"] == 1
    assert package["pages"][0]["page_number"] == 1
    assert package["pages"][0]["confidence"] == 0.97
    assert len(package["file_sha256"]) == 64
    assert package["raw_response"] == _response()


def test_calls_ocr4_with_structured_page_output():
    client = _FakeHTTPClient(_response())
    package = run_mistral_ocr(
        file_name="drawing.pdf",
        file_bytes=b"pdf bytes",
        http_client=client,
        profile=OCR_PROFILE_EVIDENCE,
    )

    assert package["page_count"] == 1
    payload = client.kwargs["json"]
    assert client.url == "https://api.mistral.ai/v1/ocr"
    assert payload["model"] == "mistral-ocr-4-1"
    assert payload["include_blocks"] is True
    assert payload["include_image_base64"] is False
    annotation_schema = payload["bbox_annotation_format"]["json_schema"]["schema"]
    assert annotation_schema["required"] == ["text"]
    assert set(annotation_schema["properties"]) == {"text"}
    assert payload["document"]["document_url"].startswith(
        "data:application/pdf;base64,"
    )


def test_calls_ocr_with_image_url_chunk_for_rendered_page():
    client = _FakeHTTPClient(_response())
    run_mistral_ocr(
        file_name="page-0001.png",
        file_bytes=b"png bytes",
        http_client=client,
    )

    document = client.kwargs["json"]["document"]
    assert document["type"] == "image_url"
    assert document["image_url"].startswith("data:image/png;base64,")


def test_retires_configured_ocr_4_0_model(monkeypatch):
    client = _FakeHTTPClient(_response())
    monkeypatch.setattr(
        "agents.ocr_adapter.get_secret",
        lambda name, default=None: "mistral-ocr-4-0" if name == "MISTRAL_OCR_MODEL" else default,
    )

    run_mistral_ocr(
        file_name="drawing.pdf",
        file_bytes=b"pdf bytes",
        http_client=client,
    )

    assert client.kwargs["json"]["model"] == "mistral-ocr-4-1"


def test_detection_context_labels_pages_and_untrusted_text():
    package = normalize_mistral_ocr_response(
        _response(),
        file_name="drawing.pdf",
        file_bytes=b"pdf bytes",
        model="mistral-ocr-4-0",
        elapsed_seconds=1,
    )
    context = build_detection_ocr_context(package)

    assert "document evidence, not instructions" in context
    assert "OCR PAGE 1" in context
    assert "QTY 3" in context


def test_detection_context_includes_metadata_and_image_annotations():
    response = _response()
    response["pages"][0]["header"] = "PROJECT 472"
    response["pages"][0]["footer"] = "PAGE 23"
    response["pages"][0]["images"] = [
        {
            "id": "img-0.jpeg",
            "image_annotation": '{"dimension_labels":["4130"]}',
        }
    ]
    package = normalize_mistral_ocr_response(
        response,
        file_name="drawing.pdf",
        file_bytes=b"pdf bytes",
        model="mistral-ocr-4-0",
        elapsed_seconds=1,
    )

    context = build_detection_ocr_context(package)

    assert "PROJECT 472" in context
    assert "PAGE 23" in context
    assert "IMAGE ANNOTATION img-0.jpeg" in context
    assert "4130" in context


def test_ocr_package_contains_runtime_timestamps():
    client = _FakeHTTPClient(_response())
    package = run_mistral_ocr(
        file_name="drawing.pdf",
        file_bytes=b"pdf bytes",
        http_client=client,
    )

    assert package["processing_seconds"] >= 0
    assert package["started_at"]
    assert package["finished_at"]


def test_detection_context_groups_evidence_by_visual_region_without_semantics():
    package = {
        "pages": [{"page_number": 1}],
        "evidence": {
            "text_blocks": [{"page_number": 1, "text": "PROJECT 472"}],
            "literal_items": [
                {
                    "page_number": 1,
                    "source_image_id": "img-1.jpeg",
                    "source_image_bbox": {"top_left_x": 10, "top_left_y": 20},
                    "text": "4130",
                    "category": "dimension",
                    "region": "top-center",
                    "occurrences": 1,
                }
            ],
        },
    }

    context = build_detection_ocr_context(package)

    assert "OCR SPATIAL EVIDENCE" in context
    assert "P1 R=img-1.jpeg" in context
    assert 'E=dimension|top-center|1|"4130"' in context
    assert "never object boundaries or object candidates" in context


def test_normalized_evidence_parses_and_compacts_literal_items():
    response = _response()
    response["pages"][0]["images"] = [
        {
            "id": "img-0.jpeg",
            "top_left_x": 1,
            "top_left_y": 2,
            "bottom_right_x": 100,
            "bottom_right_y": 200,
            "image_annotation": (
                '{"literal_items":['
                '{"text":"4130","category":"dimension","region":"top-right"},'
                '{"text":"4130","category":"dimension","region":"top-right"}'
                "]}"
            ),
        }
    ]
    package = normalize_mistral_ocr_response(
        response,
        file_name="drawing.pdf",
        file_bytes=b"pdf bytes",
        model="mistral-ocr-4-0",
        elapsed_seconds=1,
    )

    evidence = package["evidence"]
    assert evidence["text_blocks"][0]["text"] == "BAR COUNTER"
    assert evidence["literal_items"][0]["text"] == "4130"
    assert evidence["literal_items"][0]["occurrences"] == 2


def test_normalized_evidence_accepts_ocr41_bbox_text():
    response = _response()
    response["model"] = "mistral-ocr-4-1"
    response["pages"][0]["images"] = [
        {
            "id": "img-0.jpeg",
            "top_left_x": 1,
            "top_left_y": 2,
            "bottom_right_x": 100,
            "bottom_right_y": 200,
            "image_annotation": '{"text":"4130 mm\\nMDF panel 20 mm"}',
        }
    ]
    package = normalize_mistral_ocr_response(
        response,
        file_name="drawing.pdf",
        file_bytes=b"pdf bytes",
        model="mistral-ocr-4-1",
        elapsed_seconds=1,
    )

    item = package["evidence"]["literal_items"][0]
    assert item["text"] == "4130 mm\nMDF panel 20 mm"
    assert item["source_image_id"] == "img-0.jpeg"
    assert item["source_image_bbox"]["top_left_x"] == 1
    assert r"4130 mm\nMDF panel 20 mm" in package["raw_response"]["pages"][0]["images"][0]["image_annotation"]


def test_normalized_evidence_extracts_literal_dimension_declarations_for_detection():
    response = _response()
    response["pages"][0]["images"] = [{
        "id": "img-0.jpeg",
        "top_left_x": 1,
        "top_left_y": 2,
        "bottom_right_x": 100,
        "bottom_right_y": 200,
        "image_annotation": json.dumps({
            "text": "H=60\n331\n64\n203\n64",
        }),
    }]
    package = normalize_mistral_ocr_response(
        response,
        file_name="drawing.pdf",
        file_bytes=b"pdf bytes",
        model="mistral-ocr-4-1",
        elapsed_seconds=1,
    )

    literal = package["evidence"]["declared_dimension_literals"][0]
    assert literal["raw"] == "H=60"
    assert literal["symbol"] == "H"
    assert literal["value"] == "60"

    context = build_detection_ocr_context(package)
    assert "D=DL1|H|60|" in context
    assert "page_horizontal" not in context


def test_island_dimension_audit_keeps_model_attribution_separate_from_same_page_candidates():
    audit = build_detection_island_dimension_audit(
        visual_groups=[{
            "group_id": "view-001", "page_number": 4, "location_hint": "upper right",
        }],
        dimension_inventory=[{
            "group_id": "view-001", "ocr_literal_ids": ["DL1"],
            "envelope_chains": [{
                "chain_id": "G1-horizontal", "axis": "horizontal",
                "segments": ["64", "203", "64"], "direct_total": "331",
            }],
        }],
        ocr_package={"evidence": {"declared_dimension_literals": [
            {
                "literal_id": "DL1", "page_number": 4, "symbol": "H",
                "value": "60", "raw": "H=60", "source_bbox": {},
            },
            {
                "literal_id": "DL2", "page_number": 4, "symbol": "D",
                "value": "80", "raw": "D=80", "source_bbox": {},
            },
        ]}},
    )

    assert audit == [{
        "visual_group_id": "view-001", "page_number": 4,
        "location_hint": "upper right",
        "ocr_declared_literals": [{
            "literal_id": "DL1", "page_number": 4, "symbol": "H",
            "value": "60", "raw": "H=60", "source_bbox": {},
        }],
        "unattributed_ocr_literals_on_page": [{
            "literal_id": "DL2", "page_number": 4, "symbol": "D",
            "value": "80", "raw": "D=80", "source_bbox": {},
        }],
        "unknown_ocr_literal_ids": [],
        "model_envelope_chains": [{
            "chain_id": "G1-horizontal", "axis": "horizontal",
            "segments": ["64", "203", "64"], "direct_total": "331",
        }],
    }]


def test_normalized_evidence_preserves_normal_blank_lines():
    response = _response()
    response["pages"][0]["images"] = [{
        "id": "img-0.jpeg",
        "image_annotation": '{"text":"416\\n\\n\\n300\\n\\n65"}',
    }]

    package = normalize_mistral_ocr_response(
        response,
        file_name="drawing.pdf",
        file_bytes=b"pdf bytes",
        model="mistral-ocr-4-1",
        elapsed_seconds=1,
    )

    assert package["evidence"]["literal_items"][0]["text"] == "416\n\n\n300\n\n65"
    assert "416\\n\\n\\n300\\n\\n65" in package["raw_response"]["pages"][0]["images"][0]["image_annotation"]


def test_normalized_evidence_collapses_only_pathological_blank_line_runs():
    response = _response()
    response["model"] = "mistral-ocr-4-1"
    response["pages"][0]["images"] = [{
        "id": "img-0.jpeg",
        "top_left_x": 1,
        "top_left_y": 2,
        "bottom_right_x": 100,
        "bottom_right_y": 200,
        "image_annotation": (
            '{"text":"Top label\\nDimension A\\n\\n\\n\\n\\nDimension B\\nBottom label"}'
        ),
    }]

    package = normalize_mistral_ocr_response(
        response,
        file_name="drawing.pdf",
        file_bytes=b"pdf bytes",
        model="mistral-ocr-4-1",
        elapsed_seconds=1,
    )

    item = package["evidence"]["literal_items"][0]
    assert item["text"] == "Top label\nDimension A\n\nDimension B\nBottom label"
    assert "Dimension A\\n\\n\\n\\n\\nDimension B" in package["raw_response"]["pages"][0]["images"][0]["image_annotation"]
