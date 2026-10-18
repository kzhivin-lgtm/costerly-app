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
DOCUMENT_MEASUREMENT_UNITS = frozenset({"mm", "cm", "m", "mixed", "unknown"})

DETECTION_DOCUMENT_MEASUREMENT_CONTEXT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["unit", "evidence_pages", "basis"],
    "properties": {
        "unit": {"type": "string", "enum": sorted(DOCUMENT_MEASUREMENT_UNITS)},
        "evidence_pages": {"type": "array", "items": {"type": "integer", "minimum": 1}},
        "basis": {"type": "string"},
    },
}

DETECTION_REPRESENTATION_PACKAGE_JSON_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "object_id",
            "assembly_view_group_ids",
            "supporting_component_detail_group_ids",
            "package_basis",
        ],
        "properties": {
            # Package IDs are assigned deterministically by the runtime after
            # the model has decided package membership. They are not inference.
            "object_id": {"type": "string", "minLength": 1},
            "assembly_view_group_ids": {
                "type": "array", "minItems": 1,
                "items": {"type": "string"},
            },
            "supporting_component_detail_group_ids": {
                "type": "array", "items": {"type": "string"},
            },
            "package_basis": {"type": "string"},
        },
    },
}

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


def validate_detection_document_measurement_context(
    context: object,
    *,
    page_count: int,
) -> dict[str, Any]:
    """Validate run-wide dimension convention used only for visual roles.

    This is not an object-dimensions payload and is never passed to Estimation.
    It gives the visual classifier one consistent unit convention for the file.
    """
    required = {"unit", "evidence_pages", "basis"}
    if not isinstance(context, dict) or set(context) != required:
        raise DetectionRegistrySchemaError("document measurement context fields do not match contract")
    unit = context["unit"]
    evidence_pages = context["evidence_pages"]
    if (
        unit not in DOCUMENT_MEASUREMENT_UNITS
        or not isinstance(evidence_pages, list)
        or len(evidence_pages) != len(set(evidence_pages))
        or not all(isinstance(page, int) and 1 <= page <= page_count for page in evidence_pages)
        or (unit != "unknown" and not evidence_pages)
        or not str(context["basis"] or "").strip()
    ):
        raise DetectionRegistrySchemaError("document measurement context is invalid")
    return context


def validate_detection_representation_packages(
    packages: object,
    *,
    visual_groups: list[dict[str, Any]],
    registry: dict[str, Any],
) -> list[dict[str, Any]]:
    """Validate the explicit bridge from depictions to commercial objects.

    A visual group describes one depiction. A representation package records
    the product-level collection that is evaluated before an object is locked.
    This prevents an isolated component classification from silently deciding
    that a separately evidenced product cannot exist.
    """
    if not isinstance(packages, list):
        raise DetectionRegistrySchemaError("representation packages must be a list")
    if not isinstance(visual_groups, list):
        raise DetectionRegistrySchemaError("representation packages require visual groups")
    objects = registry.get("objects") if isinstance(registry, dict) else None
    if not isinstance(objects, list):
        raise DetectionRegistrySchemaError("representation packages require a registry")

    groups_by_id = {
        str(group.get("group_id") or ""): group
        for group in visual_groups
        if isinstance(group, dict)
    }
    assembly_group_ids = {
        group_id
        for group_id, group in groups_by_id.items()
        if group.get("commercial_role") == "assembly_view"
    }
    object_groups = {
        str(item.get("object_id") or ""): list(item.get("visual_group_ids") or [])
        for item in objects
        if isinstance(item, dict)
    }
    required = {
        "package_id", "object_id", "assembly_view_group_ids",
        "supporting_component_detail_group_ids", "package_basis",
    }
    packaged_assembly_owners: dict[str, list[str]] = {}
    supporting_component_owners: dict[str, list[str]] = {}
    commercial_package_owners: dict[str, list[str]] = {}

    for index, package in enumerate(packages, start=1):
        if not isinstance(package, dict) or set(package) != required:
            raise DetectionRegistrySchemaError("representation package fields do not match contract")
        package_id = str(package["package_id"] or "")
        if package_id != f"package-{index:03d}":
            raise DetectionRegistrySchemaError("representation package IDs must be ordered")
        object_id = str(package["object_id"] or "")
        assembly_ids = package["assembly_view_group_ids"]
        supporting_ids = package["supporting_component_detail_group_ids"]
        if (
            not isinstance(assembly_ids, list)
            or not assembly_ids
            or len(assembly_ids) != len(set(assembly_ids))
            or not all(isinstance(group_id, str) and group_id for group_id in assembly_ids)
            or not isinstance(supporting_ids, list)
            or len(supporting_ids) != len(set(supporting_ids))
            or not all(isinstance(group_id, str) and group_id for group_id in supporting_ids)
            or set(assembly_ids).intersection(supporting_ids)
            or not object_id
            or not str(package["package_basis"] or "").strip()
        ):
            raise DetectionRegistrySchemaError("representation package is invalid")
        if any(
            groups_by_id.get(group_id, {}).get("commercial_role") != "assembly_view"
            for group_id in assembly_ids
        ):
            raise DetectionRegistrySchemaError(
                "representation package assembly groups must be assembly views"
            )
        if any(
            groups_by_id.get(group_id, {}).get("commercial_role") != "component_detail"
            for group_id in supporting_ids
        ):
            raise DetectionRegistrySchemaError(
                "representation package support groups must be component details"
            )
        for group_id in assembly_ids:
            packaged_assembly_owners.setdefault(group_id, []).append(package_id)
        for group_id in supporting_ids:
            supporting_component_owners.setdefault(group_id, []).append(package_id)
        commercial_package_owners.setdefault(object_id, []).append(package_id)
        if object_groups.get(object_id) != assembly_ids:
            raise DetectionRegistrySchemaError(
                "registry object must use exactly its package assembly views",
                details={"object_id": object_id, "package_id": package_id},
            )

    if set(packaged_assembly_owners) != assembly_group_ids:
        raise DetectionRegistrySchemaError(
            "representation packages must account for every assembly view exactly once",
            details={
                "unpackaged_assembly_view_ids": sorted(
                    assembly_group_ids - set(packaged_assembly_owners)
                ),
                "unknown_packaged_assembly_view_ids": sorted(
                    set(packaged_assembly_owners) - assembly_group_ids
                ),
            },
        )
    duplicate_assembly_packages = {
        group_id: owners
        for group_id, owners in packaged_assembly_owners.items()
        if len(owners) > 1
    }
    if duplicate_assembly_packages:
        raise DetectionRegistrySchemaError(
            "assembly view cannot belong to multiple representation packages",
            details={"duplicate_assembly_view_packages": duplicate_assembly_packages},
        )
    duplicate_support_packages = {
        group_id: owners
        for group_id, owners in supporting_component_owners.items()
        if len(owners) > 1
    }
    if duplicate_support_packages:
        raise DetectionRegistrySchemaError(
            "component detail cannot support multiple representation packages",
            details={"duplicate_component_detail_packages": duplicate_support_packages},
        )
    if set(commercial_package_owners) != set(object_groups):
        raise DetectionRegistrySchemaError(
            "representation packages must account for every commercial object exactly once",
            details={
                "unpackaged_object_ids": sorted(set(object_groups) - set(commercial_package_owners)),
                "unknown_packaged_object_ids": sorted(set(commercial_package_owners) - set(object_groups)),
            },
        )
    duplicate_object_packages = {
        object_id: owners
        for object_id, owners in commercial_package_owners.items()
        if len(owners) > 1
    }
    if duplicate_object_packages:
        raise DetectionRegistrySchemaError(
            "commercial object cannot belong to multiple representation packages",
            details={"duplicate_object_packages": duplicate_object_packages},
        )
    return packages

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
