from agents.detection_agent import _normalize_evidence_source_labels


def test_detection_replaces_model_description_with_physical_page_reference():
    result = {
        "detected_objects": [{
            "evidence_page_refs": [{
                "page_number": 1,
                "source_label": "Modular storage console with teal accent",
                "regions": [],
            }],
        }],
    }
    ocr = {"evidence": {"text_blocks": [{"page_number": 1, "text": "Furniture for living room"}]}}

    normalized = _normalize_evidence_source_labels(result, ocr)

    assert normalized["detected_objects"][0]["evidence_page_refs"][0]["source_label"] == "P1"


def test_detection_retains_literal_source_label_from_ocr():
    result = {
        "detected_objects": [{
            "evidence_page_refs": [{
                "page_number": 1,
                "source_label": "Kitchen assembly plan",
                "regions": [],
            }],
        }],
    }
    ocr = {"evidence": {"literal_items": [{"page_number": 1, "text": "Kitchen Assembly Plan, sheet K-01"}]}}

    normalized = _normalize_evidence_source_labels(result, ocr)

    assert normalized["detected_objects"][0]["evidence_page_refs"][0]["source_label"] == "Kitchen assembly plan"
