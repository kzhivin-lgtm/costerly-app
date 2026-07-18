from agents.anthropic_adapter import build_detection_ocr_context
from agents.ocr_adapter import normalize_mistral_ocr_response, run_mistral_ocr


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

    assert package["contract_version"] == "ocr_v2"
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
    )

    assert package["page_count"] == 1
    payload = client.kwargs["json"]
    assert client.url == "https://api.mistral.ai/v1/ocr"
    assert payload["model"] == "mistral-ocr-4-0"
    assert payload["include_blocks"] is True
    assert payload["include_image_base64"] is False
    assert payload["document"]["document_url"].startswith(
        "data:application/pdf;base64,"
    )


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
    assert '"region_id":"img-1.jpeg"' in context
    assert '"text":"4130"' in context
    assert "not necessarily one product" in context


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
