import pytest

from agents.naming_lab import (
    NAMING_LAB_VERSION,
    apply_name_mapping,
    assign_ocr_drawing_indices,
    build_naming_decision_audit,
    build_locked_naming_input,
    compose_name_preview,
    ensure_provisional_object_names,
    ensure_unique_object_ids,
    extract_object_index,
    load_naming_prompt,
    relevant_ocr_snippets,
    validate_locked_name_mapping,
)
from agents.ocr_adapter import build_page_title_fields


def test_uses_semantic_category_naming_version():
    assert NAMING_LAB_VERSION == "naming_lab_v15_grounded_category_evidence"


def test_naming_schema_requires_short_decision_basis():
    from agents.naming_lab import NAMING_RESULT_SCHEMA

    item_schema = NAMING_RESULT_SCHEMA["properties"]["names"]["items"]
    assert "name_basis" in item_schema["required"]
    assert "category_evidence" in item_schema["required"]


def test_naming_decision_audit_preserves_locked_code_and_evidence_pages():
    audit = build_naming_decision_audit(
        [{"object_id": "object-001", "object_index": "OM 15-1", "evidence_pages": [1, 3]}],
        {"names": [{
            "object_id": "object-001",
            "name_en": "Stair railing",
            "name_basis": "OCR railing label on p. 1; railing geometry.",
            "category_evidence": {
                "kind": "literal_object_label", "cue": "railing",
                "page_number": 1, "visual_group_id": "view-001",
            },
        }]},
    )

    assert audit == [{
        "object_id": "object-001",
        "source_identifier": "OM 15-1",
        "evidence_pages": [1, 3],
        "selected_name": "Stair railing",
        "name_basis": "OCR railing label on p. 1; railing geometry.",
        "category_evidence": {
            "kind": "literal_object_label", "cue": "railing",
            "page_number": 1, "visual_group_id": "view-001",
        },
    }]


def test_naming_prompt_keeps_integrated_kitchens_out_of_shelving():
    prompt = load_naming_prompt()

    assert "is `Kitchen`" in prompt
    assert "shelving unit" in prompt
    assert "faucet/mixer/tap" in prompt
    assert "microwave" in prompt
    assert "range hood" in prompt
    assert "A worktop alone is only supporting evidence" in prompt
    assert "never use them to merge separate cabinet systems" in prompt


def test_extracts_authoritative_leading_index_only():
    assert extract_object_index("ОМ-2 — Railing panel") == "ОМ-2"
    assert extract_object_index("ОМ 15-1") == "ОМ 15-1"
    assert extract_object_index("Kitchen N56") == "N56"
    assert extract_object_index("Kitchen N56 N57") == ""
    assert extract_object_index("Sliding door system") == ""
    assert extract_object_index("N76B") == "N76B"
    assert extract_object_index("7-6B") == "7-6B"


def test_gives_unlabelled_rows_stable_numbered_provisional_names():
    objects = [
        {"object_name": "Unlabelled"},
        {"object_name": "Object 2"},
        {"object_name": "N76B"},
        {"object_name": ""},
    ]

    ensure_provisional_object_names(objects)

    assert [item["object_name"] for item in objects] == [
        "Object 01", "Object 02", "N76B", "Object 04",
    ]


def test_recovers_title_block_drawing_index_for_a_locked_object_page():
    objects = [{
        "object_name": "Object 01",
        "evidence_page_refs": [{"page_number": 4}],
    }]
    ocr = {"evidence": {"text_blocks": [{
        "page_number": 4,
        "text": "<table><tr><td>DRAWING NAME</td><td>ITEM NO</td></tr><tr><td>N57</td></tr></table>",
    }]}}

    assign_ocr_drawing_indices(objects, ocr)

    assert objects[0]["object_name"] == "N57"


def test_fusion_title_fields_use_full_markdown_when_compact_evidence_loses_table():
    fields = build_page_title_fields(
        [{"page_number": 6, "markdown": "DRAWING NAME\nN62"}],
        {"text_blocks": [], "literal_items": []},
    )

    assert fields == [{
        "page_number": 6,
        "field_type": "drawing_sheet_code",
        "value": "N62",
        "status": "single_source",
        "sources": ["mistral_page_markdown"],
        "label": "DRAWING NAME",
        "bbox": None,
    }]


def test_kitchen_requires_object_local_direct_category_evidence():
    locked = [{"object_id": "object-001", "evidence_pages": [3]}]
    rejected = validate_locked_name_mapping(locked, {"names": [{
        "object_id": "object-001", "name_en": "Kitchen", "name_original": "",
        "name_basis": "Cabinet geometry.",
        "category_evidence": {
            "kind": "none", "cue": "", "page_number": 0, "visual_group_id": "",
        },
    }]})
    accepted = validate_locked_name_mapping(locked, {"names": [{
        "object_id": "object-001", "name_en": "Kitchen", "name_original": "",
        "name_basis": "Faucet in the cabinet elevation.",
        "category_evidence": {
            "kind": "visual_direct_cue", "cue": "faucet_mixer_tap",
            "page_number": 3, "visual_group_id": "view-001",
        },
    }]})

    assert rejected["accepted"] is False
    assert accepted == {"accepted": True, "violations": []}


def test_drops_isolated_title_block_family_outlier_when_a_document_series_exists():
    objects = [
        {"object_name": "Object 01", "evidence_page_refs": [{"page_number": 4}]},
        {"object_name": "Object 02", "evidence_page_refs": [{"page_number": 9}]},
    ]
    ocr = {"evidence": {"text_blocks": [
        {"page_number": 4, "text": "DRAWING NAME N57"},
        {"page_number": 5, "text": "DRAWING NAME N60"},
        {"page_number": 7, "text": "DRAWING NAME N68"},
        {"page_number": 8, "text": "DRAWING NAME N70"},
        {"page_number": 9, "text": "DRAWING NAME FTC201.06"},
    ]}}

    assign_ocr_drawing_indices(objects, ocr)

    assert [item["object_name"] for item in objects] == ["N57", "Object 02"]


def test_private_naming_code_does_not_replace_neutral_persisted_label():
    objects = [{
        "object_id": "object-001",
        "object_name": "N57",
        "_persisted_object_name": "Object 01",
        "evidence_page_refs": [{"page_number": 4}],
    }]

    locked = build_locked_naming_input(objects, {"evidence": {}})
    apply_name_mapping(
        objects,
        locked,
        {"names": [{
            "object_id": "object-001", "name_en": "Display cabinet", "name_original": "",
        }]},
    )

    assert locked[0]["persisted_name"] == "Object 01"
    assert objects[0]["object_name"] == "N57 Display cabinet"


def test_does_not_turn_transport_placeholders_into_suffix_codes():
    assert extract_object_index("Object 3") == ""
    assert extract_object_index("Object 3 — TV console") == ""
    assert extract_object_index("Item 12 - Shelving unit") == ""


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
            "evidence_page_refs": [{"page_number": 1, "source_label": "A-01", "regions": []}],
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
            "persisted_name": "ЛП-1 — Metal platform",
            "evidence_pages": [1],
            "evidence_regions": [{
                "page_number": 1,
                "regions": [],
            }],
            "ocr_snippets": ["ЛП-1 Площадка"],
        }
    ]


def test_naming_input_excludes_detection_notes():
    objects = [
        {
            "object_id": "a",
            "object_name": "Object 1",
        "evidence_page_refs": [{"page_number": 1, "source_label": "A-01", "regions": []}],
            "notes": "  Custom\n shelving   unit " + ("with shelves " * 40),
        }
    ]

    locked = build_locked_naming_input(objects, {"evidence": {}})

    assert "context_hint" not in locked[0]
    assert locked[0]["evidence_pages"] == [1]
    assert locked[0]["evidence_regions"] == [{
        "page_number": 1,
        "regions": [],
    }]


def test_ocr_snippets_are_capped_for_compact_naming_input():
    long_text = "ЛП-1 " + ("металлическая площадка " * 100)
    ocr = {"evidence": {"literal_items": [{"page_number": 1, "text": long_text}]}}

    snippets = relevant_ocr_snippets(
        {"object_name": "ЛП-1", "evidence_pages": "1"},
        ocr,
    )

    assert len(snippets) == 1
    assert len(snippets[0]) == 1000


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
            {"object_id": "a", "name_en": "Railing panel", "name_original": ""}
        ]
    }

    assert compose_name_preview(locked, result) == [
        {"object_id": "a", "display_name": "ОМ-2 Railing panel"}
    ]
    assert locked[0]["current_name"] == "Old"


def test_rejects_source_language_name_for_english_only_mvp():
    locked = [{"object_id": "a", "object_index": "ОМ-2", "current_name": "ОМ-2"}]
    validation = validate_locked_name_mapping(
        locked,
        {
            "names": [
                {
                    "object_id": "a",
                    "name_en": "Stair railing",
                    "name_original": "Ограждение лестницы",
                }
            ]
        },
    )

    assert validation["accepted"] is False
    assert validation["violations"] == [
        {"object_id": "a", "field": "name_original", "words": 2},
        {
            "object_id": "a", "field": "category_evidence",
            "reason": "strong_category_requires_evidence",
        },
    ]


def test_accepts_one_word_semantic_category():
    locked = [{"object_id": "a", "object_index": "CM-10", "current_name": "CM-10"}]
    validation = validate_locked_name_mapping(
        locked,
        {"names": [{"object_id": "a", "name_en": "Chair", "name_original": ""}]},
    )

    assert validation == {"accepted": True, "violations": []}


def test_rejects_transport_placeholder_as_a_final_name():
    locked = [{"object_id": "a", "object_index": "", "current_name": "Object 3"}]

    validation = validate_locked_name_mapping(
        locked,
        {"names": [{"object_id": "a", "name_en": "Object 3", "name_original": ""}]},
    )

    assert validation == {
        "accepted": False,
        "violations": [{"object_id": "a", "field": "name_en", "reason": "transport_placeholder"}],
    }


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


def test_invalid_row_keeps_placeholder_without_discarding_valid_names():
    objects = [
        {"object_id": "a", "object_name": "CM-1"},
        {"object_id": "b", "object_name": "CM-2"},
    ]
    locked = [
        {"object_id": "a", "object_index": "CM-1", "current_name": "CM-1"},
        {"object_id": "b", "object_index": "CM-2", "current_name": "CM-2"},
    ]
    result = {
        "names": [
            {"object_id": "a", "name_en": "Very long decorative shelving unit", "name_original": ""},
            {"object_id": "b", "name_en": "Display cabinet", "name_original": ""},
        ]
    }

    apply_name_mapping(objects, locked, result)

    assert objects[0]["object_name"] == "CM-1"
    assert objects[1]["object_name"] == "CM-2 Display cabinet"


def test_keeps_letter_suffixed_source_index_when_naming():
    objects = [{"object_id": "a", "object_name": "N76B"}]
    locked = [{"object_id": "a", "object_index": "N76B", "current_name": "N76B"}]
    result = {"names": [{"object_id": "a", "name_en": "Shelving unit", "name_original": ""}]}

    apply_name_mapping(objects, locked, result)

    assert objects[0]["object_name"] == "N76B Shelving unit"


def test_disambiguates_duplicate_transport_ids_without_changing_order_or_names():
    objects = [
        {"object_id": "ЛП-1", "object_name": "ЛП-1"},
        {"object_id": "ЛС-1", "object_name": "ЛС-1"},
        {"object_id": "ЛП-1", "object_name": "ЛП-1"},
    ]

    ensure_unique_object_ids(objects)

    assert [item["object_id"] for item in objects] == ["object-001", "object-002", "object-003"]
    assert [item["object_name"] for item in objects] == ["ЛП-1", "ЛС-1", "ЛП-1"]
