from __future__ import annotations
from collections import defaultdict, deque
from typing import Any

DETECTION_REGISTRY_JSON_SCHEMA: dict[str, Any] = {"type":"object","additionalProperties":False,"required":["objects"],"properties":{"objects":{"type":"array","items":{"type":"object","additionalProperties":False,"required":["object_id","transport_label","quantity","quantity_explicit","identity_pages","estimation_evidence_pages","visual_group_ids","visual_identity","boundary_basis"],"properties":{"object_id":{"type":"string"},"transport_label":{"type":"string"},"quantity":{"type":"number","minimum":0},"quantity_explicit":{"type":"boolean"},"identity_pages":{"type":"array","items":{"type":"integer","minimum":1}},"estimation_evidence_pages":{"type":"array","items":{"type":"integer","minimum":1}},"visual_group_ids":{"type":"array","minItems":1,"items":{"type":"string"}},"visual_identity":{"type":"string"},"boundary_basis":{"type":"string"}}}}}}

PAIRWISE_MERGE_EVIDENCE_TYPES = frozenset({
    "explicit_document_relation",
    "matching_topology",
    "dimension_transform",
    "unique_geometry",
    "direct_shared_structure",
})
_NON_EXPLICIT_MERGE_SUPPORT_TYPES = frozenset({
    "matching_topology",
    "dimension_transform",
    "unique_geometry",
})

DETECTION_PAIRWISE_MERGE_PROOF_JSON_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "object_id",
            "from_group_id",
            "to_group_id",
            "evidence_types",
            "evidence_pages",
            "observed_fact",
            "commercial_inseparability",
        ],
        "properties": {
            "object_id": {"type": "string"},
            "from_group_id": {"type": "string"},
            "to_group_id": {"type": "string"},
            "evidence_types": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "string",
                    "enum": sorted(PAIRWISE_MERGE_EVIDENCE_TYPES),
                },
            },
            "evidence_pages": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "integer", "minimum": 1},
            },
            "observed_fact": {"type": "string"},
            "commercial_inseparability": {"type": "string"},
        },
    },
}

class DetectionRegistrySchemaError(ValueError):
    """Registry contract failure with safe deterministic diagnostics."""

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.details = details or {}

def validate_detection_registry(
    result: dict[str, Any],
    *,
    visual_group_ids: set[str] | None = None,
    visual_group_roles: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not isinstance(result, dict) or set(result) != {"objects"} or not isinstance(result["objects"], list):
        raise DetectionRegistrySchemaError("registry must contain only objects")
    required = {"object_id","transport_label","quantity","quantity_explicit","identity_pages","estimation_evidence_pages","visual_group_ids","visual_identity","boundary_basis"}
    visual_group_owners: dict[str, list[str]] = {}
    for index, item in enumerate(result["objects"], start=1):
        if not isinstance(item, dict) or set(item) != required:
            raise DetectionRegistrySchemaError("registry object fields do not match contract")
        if str(item["object_id"]) != f"object-{index:03d}":
            raise DetectionRegistrySchemaError("registry object IDs must be ordered")
        if not str(item["transport_label"]).strip() or not str(item["visual_identity"]).strip() or not str(item["boundary_basis"]).strip():
            raise DetectionRegistrySchemaError("registry identity fields are required")
        if not isinstance(item["quantity"], (int,float)) or item["quantity"] < 0 or not isinstance(item["quantity_explicit"], bool):
            raise DetectionRegistrySchemaError("registry quantity is invalid")
        if not isinstance(item["identity_pages"], list) or not all(isinstance(page,int) and page > 0 for page in item["identity_pages"]):
            raise DetectionRegistrySchemaError("registry pages are invalid")
        if not isinstance(item["estimation_evidence_pages"], list) or not item["estimation_evidence_pages"] or not all(isinstance(page,int) and page > 0 for page in item["estimation_evidence_pages"]):
            raise DetectionRegistrySchemaError("registry estimation evidence pages are invalid")
        if not set(item["identity_pages"]).issubset(item["estimation_evidence_pages"]):
            raise DetectionRegistrySchemaError("registry identity pages must be estimation evidence")
        if (
            not isinstance(item["visual_group_ids"], list)
            or not item["visual_group_ids"]
            or not all(
                isinstance(group_id, str) and group_id
                for group_id in item["visual_group_ids"]
            )
            or len(item["visual_group_ids"]) != len(set(item["visual_group_ids"]))
        ):
            raise DetectionRegistrySchemaError("registry visual groups are invalid")
        for group_id in item["visual_group_ids"]:
            visual_group_owners.setdefault(group_id, []).append(item["object_id"])
    assigned_visual_groups = set(visual_group_owners)
    if visual_group_ids is not None and not assigned_visual_groups.issubset(visual_group_ids):
        raise DetectionRegistrySchemaError("registry references an unknown visual group")
    if visual_group_roles is not None:
        non_assembly_group_ids = sorted(
            group_id
            for group_id in assigned_visual_groups
            if visual_group_roles.get(group_id) != "assembly_view"
        )
        if non_assembly_group_ids:
            raise DetectionRegistrySchemaError(
                "registry visual groups must be complete assembly views",
                details={"non_assembly_visual_group_ids": non_assembly_group_ids},
            )
    duplicate_ownership = {
        group_id: owners
        for group_id, owners in visual_group_owners.items()
        if len(owners) > 1
    }
    if duplicate_ownership:
        raise DetectionRegistrySchemaError(
            "registry visual groups must have one commercial-object owner",
            details={"duplicate_visual_group_owners": duplicate_ownership},
        )
    return result


def validate_detection_pairwise_merge_proofs(
    proofs: object,
    *,
    registry: dict[str, Any],
    page_count: int,
) -> list[dict[str, Any]]:
    """Require a minimal, evidence-backed tree for every visual merge.

    A proof is needed only when the Registry joins distinct complete assembly
    views. Standalone objects stay evidence-free here, so this is linear in
    the number of merged views rather than a quadratic all-pairs graph.
    """
    if not isinstance(proofs, list):
        raise DetectionRegistrySchemaError("pairwise merge proofs must be a list")
    objects = registry.get("objects") if isinstance(registry, dict) else None
    if not isinstance(objects, list):
        raise DetectionRegistrySchemaError("pairwise merge proofs require a registry")
    groups_by_object = {
        str(item.get("object_id") or ""): set(item.get("visual_group_ids") or [])
        for item in objects
        if isinstance(item, dict)
    }
    proofs_by_object: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_edges: set[tuple[str, tuple[str, str]]] = set()
    required = {
        "object_id", "from_group_id", "to_group_id", "evidence_types",
        "evidence_pages", "observed_fact", "commercial_inseparability",
    }
    for proof in proofs:
        if not isinstance(proof, dict) or set(proof) != required:
            raise DetectionRegistrySchemaError("pairwise merge proof fields do not match contract")
        object_id = str(proof["object_id"] or "")
        group_ids = groups_by_object.get(object_id)
        from_group_id = str(proof["from_group_id"] or "")
        to_group_id = str(proof["to_group_id"] or "")
        if (
            not group_ids
            or from_group_id == to_group_id
            or from_group_id not in group_ids
            or to_group_id not in group_ids
        ):
            raise DetectionRegistrySchemaError("pairwise merge proof groups are invalid")
        evidence_types = proof["evidence_types"]
        if (
            not isinstance(evidence_types, list)
            or not evidence_types
            or not all(isinstance(evidence_type, str) for evidence_type in evidence_types)
            or len(evidence_types) != len(set(evidence_types))
            or not set(evidence_types).issubset(PAIRWISE_MERGE_EVIDENCE_TYPES)
        ):
            raise DetectionRegistrySchemaError("pairwise merge proof evidence types are invalid")
        if "explicit_document_relation" not in evidence_types and (
            len(evidence_types) < 2
            or not set(evidence_types).intersection(_NON_EXPLICIT_MERGE_SUPPORT_TYPES)
        ):
            raise DetectionRegistrySchemaError(
                "pairwise merge without an explicit document relation needs two independent evidence types"
            )
        evidence_pages = proof["evidence_pages"]
        if (
            not isinstance(evidence_pages, list)
            or not evidence_pages
            or len(evidence_pages) != len(set(evidence_pages))
            or not all(isinstance(page, int) and 1 <= page <= page_count for page in evidence_pages)
            or not str(proof["observed_fact"] or "").strip()
            or not str(proof["commercial_inseparability"] or "").strip()
        ):
            raise DetectionRegistrySchemaError("pairwise merge proof evidence is invalid")
        edge_key = (object_id, tuple(sorted((from_group_id, to_group_id))))
        if edge_key in seen_edges:
            raise DetectionRegistrySchemaError("pairwise merge proofs repeat a relation")
        seen_edges.add(edge_key)
        proofs_by_object[object_id].append(proof)

    for object_id, group_ids in groups_by_object.items():
        object_proofs = proofs_by_object.get(object_id, [])
        expected_proof_count = max(0, len(group_ids) - 1)
        if len(object_proofs) != expected_proof_count:
            raise DetectionRegistrySchemaError(
                "pairwise merge proofs must form one minimal proof tree",
                details={
                    "object_id": object_id,
                    "expected_proof_count": expected_proof_count,
                    "actual_proof_count": len(object_proofs),
                },
            )
        if len(group_ids) < 2:
            continue
        adjacency: dict[str, set[str]] = {group_id: set() for group_id in group_ids}
        for proof in object_proofs:
            adjacency[proof["from_group_id"]].add(proof["to_group_id"])
            adjacency[proof["to_group_id"]].add(proof["from_group_id"])
        visited: set[str] = set()
        queue = deque([next(iter(group_ids))])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            queue.extend(adjacency[current] - visited)
        if visited != group_ids:
            raise DetectionRegistrySchemaError(
                "pairwise merge proofs must connect every merged assembly view",
                details={"object_id": object_id, "unconnected_group_ids": sorted(group_ids - visited)},
            )
    return proofs
