from __future__ import annotations

from typing import Any


STATUS_VALUES = {"intake_parsed", "intake_failed", "unreadable"}
REQUIRED_RUN_FIELDS = {
    "run_id", "company_id", "project_name", "file_name", "source_type",
    "design_partner", "client", "author", "document_date", "pages_detected",
    "language", "file_quality_level", "file_quality_label", "file_quality_confidence",
    "file_quality_notes", "status", "created_at",
}
REQUIRED_OBJECT_FIELDS = {
    "run_id", "company_id", "object_id", "object_name", "quantity",
    "quantity_explicit", "review_required", "evidence_pages", "evidence_page_refs",
    "approved", "created_at",
}
_BBOX_KEYS = {"top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y"}

DETECTION_RESULT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object", "additionalProperties": False,
    "required": ["rfq_run", "detected_objects"],
    "properties": {
        "rfq_run": {
            "type": "object", "additionalProperties": False,
            "required": sorted(REQUIRED_RUN_FIELDS),
            "properties": {
                "run_id": {"type": "string"}, "company_id": {"type": "string"},
                "project_name": {"type": "string"}, "file_name": {"type": "string"},
                "source_type": {"type": "string"}, "design_partner": {"type": "string"},
                "client": {"type": "string"}, "author": {"type": "string"},
                "document_date": {"type": "string"}, "pages_detected": {"type": "integer", "minimum": 0},
                "language": {"type": "string"}, "file_quality_level": {"type": "integer", "minimum": 0, "maximum": 4},
                "file_quality_label": {"type": "string"}, "file_quality_confidence": {"type": "number", "minimum": 0, "maximum": 100},
                "file_quality_notes": {"type": "string"}, "status": {"type": "string", "enum": sorted(STATUS_VALUES)},
                "created_at": {"type": "string"},
            },
        },
        "detected_objects": {
            "type": "array", "items": {
                "type": "object", "additionalProperties": False,
                "required": sorted(REQUIRED_OBJECT_FIELDS),
                "properties": {
                    "run_id": {"type": "string"}, "company_id": {"type": "string"},
                    "object_id": {"type": "string"}, "object_name": {"type": "string"},
                    "quantity": {"type": "number", "minimum": 1}, "quantity_explicit": {"type": "boolean"},
                    "review_required": {"type": "boolean"}, "evidence_pages": {"type": "string"},
                    "evidence_page_refs": {"type": "array", "minItems": 1, "items": {
                        "type": "object", "additionalProperties": False,
                        "required": ["page_number", "source_label", "regions"],
                        "properties": {
                            "page_number": {"type": "integer", "minimum": 1},
                            "source_label": {"type": "string"},
                            "regions": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": sorted(_BBOX_KEYS), "properties": {key: {"type": "number", "minimum": 0} for key in _BBOX_KEYS}}},
                            "presentation_preview_bbox": {"type": "object", "additionalProperties": False, "required": sorted(_BBOX_KEYS), "properties": {key: {"type": "number", "minimum": 0} for key in _BBOX_KEYS}},
                        },
                    }},
                    "approved": {"type": "boolean"}, "created_at": {"type": "string"},
                },
            },
        },
    },
}

class DetectionSchemaError(ValueError):
    pass

def _dict(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict): raise DetectionSchemaError(f"{name} must be dict")
    return value

def _list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list): raise DetectionSchemaError(f"{name} must be list")
    return value

def _keys(value: dict[str, Any], required: set[str], name: str) -> None:
    missing, extra = required - set(value), set(value) - required
    if missing: raise DetectionSchemaError(f"{name} missing keys: {sorted(missing)}")
    if extra: raise DetectionSchemaError(f"{name} has extra keys: {sorted(extra)}")

def _bbox(value: Any, name: str) -> None:
    bbox = _dict(value, name); _keys(bbox, _BBOX_KEYS, name)
    if any(not isinstance(bbox[key], (int, float)) or bbox[key] < 0 for key in _BBOX_KEYS):
        raise DetectionSchemaError(f"{name} must contain non-negative numeric coordinates")
    if bbox["bottom_right_x"] <= bbox["top_left_x"] or bbox["bottom_right_y"] <= bbox["top_left_y"]:
        raise DetectionSchemaError(f"{name} must have positive area")

def validate_detection_result(result: dict[str, Any]) -> dict[str, Any]:
    result = _dict(result, "detection_result"); _keys(result, {"rfq_run", "detected_objects"}, "detection_result")
    run, objects = _dict(result["rfq_run"], "rfq_run"), _list(result["detected_objects"], "detected_objects")
    _keys(run, REQUIRED_RUN_FIELDS, "rfq_run")
    if run["status"] not in STATUS_VALUES: raise DetectionSchemaError("rfq_run.status is invalid")
    if not isinstance(run["pages_detected"], int): raise DetectionSchemaError("rfq_run.pages_detected must be integer")
    if not isinstance(run["file_quality_level"], int) or not 0 <= run["file_quality_level"] <= 4: raise DetectionSchemaError("rfq_run.file_quality_level is invalid")
    if not isinstance(run["file_quality_confidence"], (int, float)) or not 0 <= run["file_quality_confidence"] <= 100: raise DetectionSchemaError("rfq_run.file_quality_confidence is invalid")
    if run["status"] in {"unreadable", "intake_failed"} and objects: raise DetectionSchemaError("failed run must not contain objects")
    for index, raw in enumerate(objects):
        name, obj = f"detected_objects[{index}]", _dict(raw, f"detected_objects[{index}]")
        _keys(obj, REQUIRED_OBJECT_FIELDS, name)
        if obj["run_id"] != run["run_id"] or obj["company_id"] != run["company_id"]: raise DetectionSchemaError(f"{name} must belong to rfq_run")
        if not isinstance(obj["quantity"], (int, float)) or not 1 <= obj["quantity"] <= 999999: raise DetectionSchemaError(f"{name}.quantity must be positive")
        if not isinstance(obj["quantity_explicit"], bool) or not isinstance(obj["review_required"], bool) or not isinstance(obj["approved"], bool): raise DetectionSchemaError(f"{name} boolean field is invalid")
        refs = _list(obj["evidence_page_refs"], f"{name}.evidence_page_refs")
        if not refs: raise DetectionSchemaError(f"{name}.evidence_page_refs must not be empty")
        for ref_index, raw_ref in enumerate(refs):
            ref_name, ref = f"{name}.evidence_page_refs[{ref_index}]", _dict(raw_ref, f"{name}.evidence_page_refs[{ref_index}]")
            allowed = {"page_number", "source_label", "regions", "presentation_preview_bbox"}
            if {"page_number", "source_label", "regions"} - set(ref) or set(ref) - allowed: raise DetectionSchemaError(f"{ref_name} has invalid keys")
            if not isinstance(ref["page_number"], int) or ref["page_number"] < 1 or not isinstance(ref["source_label"], str): raise DetectionSchemaError(f"{ref_name} is invalid")
            for region_index, region in enumerate(_list(ref["regions"], f"{ref_name}.regions")): _bbox(region, f"{ref_name}.regions[{region_index}]")
            if "presentation_preview_bbox" in ref: _bbox(ref["presentation_preview_bbox"], f"{ref_name}.presentation_preview_bbox")
    return result
