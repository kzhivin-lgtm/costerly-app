import pytest

from agents.naming_lab import (
    apply_name_mapping,
    build_locked_naming_input,
    compose_name_preview,
    ensure_unique_object_ids,
    extract_object_index,
    relevant_ocr_snippets,
    validate_locked_name_mapping,
)


def test_extracts_authoritative_leading_index_only():
    assert extract_object_index("ОМ-2 — Railing panel") == "ОМ-2"
    assert extract_object_index("Sliding door system") == ""


def test_ocr_snippets_prefer_exact_index_and_fallback_to_evidence_page():
    ocr = {
        "evidence": {
            "literal_items": [
                {"page_number": 1, "text": "ЛП-1 Площадка металлическая"},
                {"page_number": 2, "text": "Стеллаж с полками"},
            ]
        }
    }
    indexed = {"object_name": "ЛП-1 — Metal platform", "evidence_pages": "1"}
    unindexed = {"object_name": "Shelving unit", "evidence_pages": "2"}

    assert relevant_ocr_snippets(indexed, ocr) == ["ЛП-1 Площадка металлическая"]
    assert relevant_ocr_snippets(unindexed, ocr) == ["Стеллаж с полками"]


def test_builds_minimal_locked_input_without_mutable_object_fields():
    objects = [
        {
            "object_id": "lp-1",
            "object_name": "ЛП-1 — Metal platform",
            "evidence_pages": "1",
            "quantity": 7,
            "dimensions_json": {"width": 1000},
        }
    ]
    ocr = {"evidence": {"literal_items": [{"page_number": 1, "text": "ЛП-1 Площадка"}]}}

    locked = build_locked_naming_input(objects, ocr)

    assert locked == [
        {
            "object_id": "lp-1",
            "object_index": "ЛП-1",
            "current_name": "ЛП-1 — Metal platform",
            "evidence_pages": "1",
            "materials": "",
            "dimensions": {"width": 1000},
            "notes": "",
            "ocr_snippets": ["ЛП-1 Площадка"],
        }
    ]


def test_rejects_changed_object_sequence_and_reports_word_limits():
    locked = [
        {"object_id": "a", "object_index": "", "current_name": "Shelf"},
        {"object_id": "b", "object_index": "", "current_name": "Door"},
    ]
    with pytest.raises(ValueError, match="object_id sequence changed"):
        validate_locked_name_mapping(
            locked,
            {"names": [{"object_id": "b", "name_en": "Sliding door", "name_original": ""}]},
        )

    validation = validate_locked_name_mapping(
        locked,
        {
            "names": [
                {"object_id": "a", "name_en": "Very long decorative shelving unit", "name_original": ""},
                {"object_id": "b", "name_en": "Sliding door", "name_original": ""},
            ]
        },
    )
    assert validation["accepted"] is False
    assert validation["violations"] == [{"object_id": "a", "field": "name_en", "words": 5}]


def test_preview_is_composed_without_mutating_locked_objects():
    locked = [{"object_id": "a", "object_index": "ОМ-2", "current_name": "Old"}]
    result = {
        "names": [
            {"object_id": "a", "name_en": "Railing panel", "name_original": "Панель ограждения"}
        ]
    }

    assert compose_name_preview(locked, result) == [
        {"object_id": "a", "display_name": 'ОМ-2 — Railing panel ("Панель ограждения")'}
    ]
    assert locked[0]["current_name"] == "Old"


def test_applies_validated_names_without_changing_object_identity():
    objects = [{"object_id": "a", "object_name": "Object 1", "quantity": 2}]
    locked = [{"object_id": "a", "object_index": "", "current_name": "Object 1"}]
    result = {
        "names": [
            {"object_id": "a", "name_en": "Display cabinet", "name_original": ""}
        ]
    }

    apply_name_mapping(objects, locked, result)

    assert objects == [{"object_id": "a", "object_name": "Display cabinet", "quantity": 2}]


def test_disambiguates_duplicate_transport_ids_without_changing_order_or_names():
    objects = [
        {"object_id": "ЛП-1", "object_name": "ЛП-1"},
        {"object_id": "ЛС-1", "object_name": "ЛС-1"},
        {"object_id": "ЛП-1", "object_name": "ЛП-1"},
    ]

    ensure_unique_object_ids(objects)

    assert [item["object_id"] for item in objects] == ["object-001", "object-002", "object-003"]
    assert [item["object_name"] for item in objects] == ["ЛП-1", "ЛС-1", "ЛП-1"]
