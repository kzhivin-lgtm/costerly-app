from __future__ import annotations

from typing import Any


DETECTION_ASSEMBLY_CORRESPONDENCE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["assembly_candidates", "non_assembly_representation_ids"],
    "properties": {
        "assembly_candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "candidate_id",
                    "representation_ids",
                    "visual_identity",
                    "correspondence_basis",
                ],
                "properties": {
                    "candidate_id": {"type": "string"},
                    "representation_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "visual_identity": {"type": "string"},
                    "correspondence_basis": {"type": "string"},
                },
            },
        },
        "non_assembly_representation_ids": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}


class DetectionAssemblyCorrespondenceSchemaError(ValueError):
    pass


def normalize_detection_assembly_candidate_ids(result: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize provider candidate IDs before validating their partition.

    Candidate IDs are internal join keys. The physical partition is expressed
    by the member representation IDs, so a provider's harmless label variance
    must not reject an otherwise complete correspondence result.
    """
    if not isinstance(result, dict) or not isinstance(result.get("assembly_candidates"), list):
        return result
    candidates = result["assembly_candidates"]
    raw_ids: list[str] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            return result
        candidate_id = str(candidate.get("candidate_id") or "").strip()
        if not candidate_id:
            return result
        raw_ids.append(candidate_id)
    if len(raw_ids) != len(set(raw_ids)):
        return result
    for index, candidate in enumerate(candidates, start=1):
        candidate["candidate_id"] = f"assembly-{index:03d}"
    return result


def validate_detection_assembly_correspondence(
    result: dict[str, Any],
    *,
    representation_ids: set[str],
) -> dict[str, Any]:
    """Validate an exhaustive, non-overlapping physical-assembly partition."""
    if (
        not isinstance(result, dict)
        or set(result) != {"assembly_candidates", "non_assembly_representation_ids"}
        or not isinstance(result["assembly_candidates"], list)
        or not isinstance(result["non_assembly_representation_ids"], list)
    ):
        raise DetectionAssemblyCorrespondenceSchemaError(
            "assembly correspondence fields do not match contract"
        )

    assigned_ids: list[str] = []
    for index, candidate in enumerate(result["assembly_candidates"], start=1):
        required = {
            "candidate_id",
            "representation_ids",
            "visual_identity",
            "correspondence_basis",
        }
        if not isinstance(candidate, dict) or set(candidate) != required:
            raise DetectionAssemblyCorrespondenceSchemaError(
                "assembly candidate fields do not match contract"
            )
        if str(candidate["candidate_id"]) != f"assembly-{index:03d}":
            raise DetectionAssemblyCorrespondenceSchemaError(
                "assembly candidate IDs must be ordered"
            )
        candidate_representation_ids = candidate["representation_ids"]
        if (
            not isinstance(candidate_representation_ids, list)
            or not candidate_representation_ids
            or len(candidate_representation_ids) != len(set(candidate_representation_ids))
            or not all(
                isinstance(representation_id, str)
                and representation_id in representation_ids
                for representation_id in candidate_representation_ids
            )
            or not str(candidate["visual_identity"]).strip()
            or not str(candidate["correspondence_basis"]).strip()
        ):
            raise DetectionAssemblyCorrespondenceSchemaError(
                "assembly candidate is invalid"
            )
        assigned_ids.extend(candidate_representation_ids)

    non_assembly_ids = result["non_assembly_representation_ids"]
    if (
        len(non_assembly_ids) != len(set(non_assembly_ids))
        or not all(
            isinstance(representation_id, str)
            and representation_id in representation_ids
            for representation_id in non_assembly_ids
        )
    ):
        raise DetectionAssemblyCorrespondenceSchemaError(
            "non-assembly representations are invalid"
        )
    assigned_ids.extend(non_assembly_ids)
    if len(assigned_ids) != len(set(assigned_ids)):
        raise DetectionAssemblyCorrespondenceSchemaError(
            "representation belongs to multiple correspondence outcomes"
        )
    if set(assigned_ids) != representation_ids:
        raise DetectionAssemblyCorrespondenceSchemaError(
            "correspondence must account for every representation exactly once"
        )
    return result
