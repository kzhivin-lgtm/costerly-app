from __future__ import annotations

import base64
import copy
from decimal import Decimal
import html
import hashlib
import json
import math
import os
import re
import sys
from threading import Lock
import time
from itertools import combinations
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

import anthropic

from config import agent_cost_category, calculate_llm_cost_usd
from agents.prompt_loader import (
    load_detection_agent_prompt,
    load_detection_agent_without_naming_prompt,
    load_detection_registry_prompt,
    load_detection_visual_map_prompt,
    load_detection_visual_registry_prompt,
    load_detection_v5_discovery_prompt,
    load_detection_v5_membership_prompt,
    load_detection_v5_proposal_prompt,
    load_detection_v5_review_prompt,
    load_detection_v5_source_degraded_discovery_prompt,
    load_detection_v5_source_degraded_full_page_registry_prompt,
    load_detection_v5_source_degraded_membership_prompt,
    load_detection_v5_source_degraded_one_shot_registry_prompt,
    load_detection_v5_source_degraded_v561_consensus_prompt,
)
from agents.detection_source_capability import (
    assess_detection_source_capability,
    drop_detection_visual_only_component_only_partitions,
    validate_detection_visual_only_partitions,
)
from agents.detection_fusion_candidate_regions import (
    build_detection_fusion_candidate_regions,
    format_detection_candidate_pair_queue,
    format_detection_fusion_candidate_regions,
)
from agents.detection_page_images import DEFAULT_PAGE_IMAGE_DPI
from agents.detection_spatial_inventory import (
    build_detection_spatial_inventory,
    spatial_inventory_context,
)
from agents.schemas.detection_registry_schema import (
    REFERENCE_RELATIONSHIP,
    DETECTION_DIMENSION_CANDIDATE_DECISIONS_JSON_SCHEMA,
    DETECTION_DIMENSION_INVENTORY_JSON_SCHEMA,
    DETECTION_PAIRWISE_MERGE_PROOF_JSON_SCHEMA,
    DETECTION_REGISTRY_JSON_SCHEMA,
    DetectionRegistrySchemaError,
    derive_detection_package_decision_audit,
    derive_detection_dimension_package_candidates,
    compile_detection_v5_object_hypotheses,
    compile_detection_v5_semantic_facts,
    compile_detection_v5_visual_dimension_conflicts,
    compile_detection_v5_merge_edges,
    compile_detection_v5_dimension_graph,
    SOURCE_DEGRADED_VISUAL_SEMANTIC_EVIDENCE_TYPES,
    validate_detection_v5_final_result,
    merge_detection_relation_edges,
    derive_detection_proof_components,
    derive_detection_standalone_package_group_ids,
    derive_detection_v5_dominant_page_attachment_edges,
    compile_detection_dimension_graph,
    normalize_empty_detection_envelope_chains,
    normalize_detection_dimension_inventory_group_ids,
    validate_detection_dimension_inventory,
    validate_detection_registry,
    partition_detection_relation_edges,
)
from agents.schemas.detection_visual_map_schema import (
    DETECTION_VISUAL_MAP_JSON_SCHEMA,
    normalize_detection_visual_map_group_ids,
    validate_detection_visual_map,
)
from agents.schemas.detection_schema import (
    DETECTION_RESULT_JSON_SCHEMA,
    validate_detection_result,
)


DEFAULT_CLAUDE_DETECTION_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_CLAUDE_AGENT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_CLAUDE_FALLBACK_MODEL = "claude-sonnet-4-6"
DETECTION_PROMPT_VERSION = "detection_v4_object_evidence_handoff_v6"
DETECTION_NO_NAMING_PROMPT_VERSION = DETECTION_PROMPT_VERSION
DETECTION_VISUAL_MAP_PROMPT_VERSION = "detection_v4_visual_representation_map_v1"
DETECTION_REGISTRY_PROMPT_VERSION = "detection_v4_commercial_registry_from_visual_map_v2"
DETECTION_VISUAL_REGISTRY_PROMPT_VERSION = (
    "detection_v5_10_12_compact_coverage_dimension_halo_min20_fusion_text_recall_temperature_0"
)
# V5.0 keeps one Haiku call. Registry returns Islands, classifications, and
# sparse positive semantic facts. Runtime owns every graph and package decision.
DETECTION_VISUAL_REGISTRY_TEMPERATURE = 0.0
# The positive graph and per-group source index are linear in island count.
DETECTION_VISUAL_REGISTRY_MAX_TOKENS = 12_288
DETECTION_V5_DISCOVERY_MAX_TOKENS = 8_192
DETECTION_V5_PROPOSAL_MAX_TOKENS = 8_192
DETECTION_V5_MEMBERSHIP_MAX_TOKENS = 6_144
DETECTION_V5_MEMBERSHIP_CROP_MAX_SIDE = 768
DETECTION_V5_MEMBERSHIP_PAGE_CONTEXT_MAX_SIDE = 1024
DETECTION_V5_SOURCE_DEGRADED_DISCOVERY_MAX_TOKENS = 6_144
DETECTION_V5_SOURCE_DEGRADED_MEMBERSHIP_MAX_TOKENS = 4_096
DETECTION_V5_SOURCE_DEGRADED_PROMPT_VERSION = (
    "detection_v5_13_2_source_degraded_v4_representation_map_experimental_v1"
)
DETECTION_V5_SOURCE_DEGRADED_FULL_PAGE_REGISTRY_PROMPT_VERSION = (
    "detection_v5_14_source_degraded_full_page_visual_registry_experimental_v1"
)
DETECTION_V5_SOURCE_DEGRADED_ONE_SHOT_REGISTRY_PROMPT_VERSION = (
    "detection_v5_15_source_degraded_one_shot_visual_registry_experimental_v1"
)
DETECTION_V5_SOURCE_DEGRADED_V561_CONSENSUS_PROMPT_VERSION = (
    "detection_v5_16_source_degraded_v561_two_proposal_consensus_experimental_v1"
)
DETECTION_V5_SOURCE_DEGRADED_V518_PROMPT_VERSION = (
    "detection_v5_18_source_degraded_full_page_registry_partition_repair_v1"
)
DETECTION_V5_SOURCE_DEGRADED_MEMBERSHIP_CROP_MAX_SIDE = 1024
# Registry has already locked object identity, quantity and ordering before this
# call. Keep the evidence-packaging pass deterministic under that immutable
# contract as well.
DETECTION_LOCKED_EVIDENCE_HANDOFF_TEMPERATURE = 0.0

_NON_OBJECT_VISUAL_REPRESENTATION_KINDS = frozenset({
    "cover",
    "cover_page",
    "title_page",
    "title_block",
    "generic_floor_plan",
    "floor_plan",
    "room_layout",
    "electrical_plan",
    "plumbing_plan",
    "lighting_plan",
    "legend",
    "administrative_text",
    "generic_schedule",
    "navigation_diagram",
})

_DOCUMENT_DIMENSION_UNIT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("mm", re.compile(r"(?i)\b[HWD]\s*=\s*\d+(?:[.,]\d+)?\s*mm\b")),
    ("cm", re.compile(r"(?i)\b[HWD]\s*=\s*\d+(?:[.,]\d+)?\s*cm\b")),
    ("m", re.compile(r"(?i)\b[HWD]\s*=\s*\d+(?:[.,]\d+)?\s*m\b")),
    ("in", re.compile(r"(?i)\b[HWD]\s*=\s*\d+(?:[.,]\d+)?\s*in\b")),
    ("ft", re.compile(r"(?i)\b[HWD]\s*=\s*\d+(?:[.,]\d+)?\s*ft\b")),
    ("mm", re.compile(r"[HWD]\s*=\s*\d+(?:[.,]\d+)?\s*מ[\"״׳']?מ")),
    ("cm", re.compile(r"[HWD]\s*=\s*\d+(?:[.,]\d+)?\s*ס[\"״׳']?מ")),
)

class DetectionVisualRegistryValidationError(RuntimeError):
    """Expose a DB-ready audit event when Registry output fails validation."""

    def __init__(self, message: str, *, usage_event: dict[str, Any]):
        super().__init__(message)
        self.usage_event = usage_event


DETECTION_VISUAL_REGISTRY_OBJECTS_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "component_anchor_group_id",
            "transport_label",
            "quantity",
            "quantity_explicit",
            "identity_pages",
            "visual_identity",
            "boundary_basis",
        ],
        "properties": {
            "component_anchor_group_id": {"type": "string"},
            "transport_label": {"type": "string"},
            "quantity": {"type": "number", "minimum": 0},
            "quantity_explicit": {"type": "boolean"},
            "identity_pages": {
                "type": "array", "items": {"type": "integer", "minimum": 1},
            },
            "visual_identity": {"type": "string"},
            "boundary_basis": {"type": "string"},
        },
    },
}
DETECTION_VISUAL_REGISTRY_VISUAL_GROUPS_SCHEMA = copy.deepcopy(
    DETECTION_VISUAL_MAP_JSON_SCHEMA["properties"]["visual_groups"]
)
DETECTION_VISUAL_REGISTRY_VISUAL_GROUPS_SCHEMA["items"]["properties"].pop(
    "evidence_class"
)
DETECTION_VISUAL_REGISTRY_VISUAL_GROUPS_SCHEMA["items"]["properties"].pop(
    "owner_object_ids"
)
DETECTION_VISUAL_REGISTRY_VISUAL_GROUPS_SCHEMA["items"]["required"].append(
    "bbox"
)
DETECTION_VISUAL_REGISTRY_VISUAL_GROUPS_SCHEMA["items"]["required"].append(
    "core_bbox"
)
DETECTION_VISUAL_REGISTRY_VISUAL_GROUPS_SCHEMA["items"]["properties"]["bbox"] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y",
    ],
    "properties": {
        "top_left_x": {"type": "integer", "minimum": 0},
        "top_left_y": {"type": "integer", "minimum": 0},
        "bottom_right_x": {"type": "integer", "minimum": 1},
        "bottom_right_y": {"type": "integer", "minimum": 1},
    },
}
DETECTION_VISUAL_REGISTRY_VISUAL_GROUPS_SCHEMA["items"]["properties"]["core_bbox"] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y",
    ],
    "properties": {
        "top_left_x": {"type": "integer", "minimum": 0},
        "top_left_y": {"type": "integer", "minimum": 0},
        "bottom_right_x": {"type": "integer", "minimum": 1},
        "bottom_right_y": {"type": "integer", "minimum": 1},
    },
}
DETECTION_VISUAL_CLASSIFICATIONS_SCHEMA: dict[str, Any] = {
    "type": "array", "items": {"type": "object", "additionalProperties": False,
        "required": ["group_id", "evidence_class", "classification_reason"],
        "properties": {"group_id": {"type": "string"},
            "evidence_class": {"type": "string", "enum": ["document_context", "object_evidence"]},
            "classification_reason": {"type": "string"}}}}
DETECTION_V5_STRUCTURAL_WITNESS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["kind", "witness_view_id", "joined_parts", "connection"],
    "properties": {
        "kind": {"type": "string", "enum": [
            "endpoint_complete_view_contains_partial",
            "third_view_shows_both",
        ]},
        "witness_view_id": {"type": "string"},
        "joined_parts": {
            "type": "array", "minItems": 2, "maxItems": 3,
            "items": {"type": "string", "maxLength": 80},
        },
        "connection": {"type": "string", "maxLength": 180},
    },
}
DETECTION_V5_SEMANTIC_FACTS_SCHEMA: dict[str, Any] = {
    "type": "array", "maxItems": 48, "items": {"type": "object", "additionalProperties": False,
        "required": ["group_id_a", "group_id_b", "evidence_type", "strength", "observation", "source_fact_ids"], "properties": {
            "group_id_a": {"type": "string"}, "group_id_b": {"type": "string"},
            "evidence_type": {"type": "string", "enum": [
                "explicit_document_relation", "dimension_transform",
                "matching_topology", "unique_geometry", "direct_shared_structure",
            ]},
            "strength": {"type": "string", "enum": ["direct", "single_object_sheet", "standard"]},
            "observation": {"type": "string", "maxLength": 180},
            "source_fact_ids": {"type": "array", "maxItems": 3, "items": {"type": "string"}},
            "structural_witness": DETECTION_V5_STRUCTURAL_WITNESS_SCHEMA,
        }},
}
DETECTION_V5_SOURCE_DEGRADED_SEMANTIC_FACTS_SCHEMA = copy.deepcopy(
    DETECTION_V5_SEMANTIC_FACTS_SCHEMA,
)
DETECTION_V5_SOURCE_DEGRADED_SEMANTIC_FACTS_SCHEMA["items"]["properties"]["evidence_type"]["enum"].append(
    "visual_dimension_similarity",
)
DETECTION_V5_SOURCE_DEGRADED_DIMENSION_CONFLICTS_SCHEMA: dict[str, Any] = {
    "type": "array", "maxItems": 48,
    "items": {"type": "object", "additionalProperties": False,
        "required": [
            "group_id_a", "group_id_b", "readings_a", "readings_b",
            "observation", "source_fact_ids",
        ],
        "properties": {
            "group_id_a": {"type": "string"},
            "group_id_b": {"type": "string"},
            "readings_a": {"type": "array", "minItems": 1, "maxItems": 8,
                           "items": {"type": "string", "maxLength": 32}},
            "readings_b": {"type": "array", "minItems": 1, "maxItems": 8,
                           "items": {"type": "string", "maxLength": 32}},
            "observation": {"type": "string", "maxLength": 180},
            "source_fact_ids": {"type": "array", "maxItems": 3, "items": {"type": "string"}},
        }},
}
DETECTION_V5_SOURCE_DEGRADED_ROLE_RESOLUTIONS_SCHEMA: dict[str, Any] = {
    "type": "array", "maxItems": 24,
    "items": {"type": "object", "additionalProperties": False,
        "required": [
            "group_id", "visual_role", "parent_group_id", "observation", "source_fact_ids",
        ],
        "properties": {
            "group_id": {"type": "string"},
            "visual_role": {"type": "string", "enum": [
                "assembly_view", "component_detail", "document_context",
            ]},
            "parent_group_id": {"type": "string"},
            "observation": {"type": "string", "minLength": 30, "maxLength": 240},
            "source_fact_ids": {"type": "array", "minItems": 1, "maxItems": 3,
                                "items": {"type": "string"}},
        }},
}
DETECTION_V5_SOURCE_DEGRADED_FULL_PAGE_ROLES_SCHEMA: dict[str, Any] = {
    "type": "array", "maxItems": 64,
    "items": {"type": "object", "additionalProperties": False,
        "required": ["group_id", "visual_role", "classification_reason"],
        "properties": {
            "group_id": {"type": "string"},
            "visual_role": {"type": "string", "enum": [
                "assembly_view", "component_detail", "document_context",
            ]},
            "classification_reason": {"type": "string", "minLength": 12, "maxLength": 240},
        },
    },
}
DETECTION_V5_SOURCE_DEGRADED_VISUAL_PARTITIONS_SCHEMA: dict[str, Any] = {
    "type": "array", "minItems": 1, "maxItems": 48,
    "items": {"type": "object", "additionalProperties": False,
        "required": ["group_ids", "visual_basis"],
        "properties": {
            "group_ids": {"type": "array", "minItems": 1, "maxItems": 48,
                          "items": {"type": "string"}},
            "visual_basis": {"type": "array", "minItems": 1, "maxItems": 24,
                "items": {"type": "object", "additionalProperties": False,
                    "required": ["evidence_type", "view_ids", "observation"],
                    "properties": {
                        "evidence_type": {"type": "string", "enum": [
                            "complete_physical_envelope", "direct_continuity",
                            "alternate_projection", "visible_author_label",
                            "matching_unique_structure", "compatible_dimensions",
                        ]},
                        "view_ids": {"type": "array", "minItems": 1, "maxItems": 48,
                                     "items": {"type": "string"}},
                        "observation": {"type": "string", "minLength": 12, "maxLength": 240},
                    },
                },
            },
        },
    },
}
DETECTION_V5_SOURCE_DEGRADED_FULL_PAGE_REGISTRY_JSON_SCHEMA: dict[str, Any] = {
    "type": "object", "additionalProperties": False,
    "required": ["roles", "partitions"],
    "properties": {
        "roles": DETECTION_V5_SOURCE_DEGRADED_FULL_PAGE_ROLES_SCHEMA,
        "partitions": DETECTION_V5_SOURCE_DEGRADED_VISUAL_PARTITIONS_SCHEMA,
    },
}
DETECTION_V5_CANDIDATE_REGION_EXCEPTIONS_SCHEMA: dict[str, Any] = {
    "type": "array", "items": {"type": "object", "additionalProperties": False,
        "required": ["candidate_region_id", "reason"], "properties": {
            "candidate_region_id": {"type": "string"},
            "reason": {"type": "string"},
        }}}

DETECTION_V5_OBJECT_HYPOTHESES_SCHEMA: dict[str, Any] = {
    "type": "array", "maxItems": 24,
    "items": {"type": "object", "additionalProperties": False,
        "required": ["group_ids", "hypothesis_reason", "evidence"], "properties": {
            "group_ids": {"type": "array", "minItems": 2, "items": {"type": "string"}},
            "hypothesis_reason": {"type": "string", "maxLength": 180},
            "evidence": {"type": "array", "minItems": 1, "maxItems": 3,
                "items": {"type": "object", "additionalProperties": False,
                    "required": ["evidence_type", "strength", "observation", "source_fact_ids"],
                    "properties": {
                        "evidence_type": {"type": "string", "enum": ["explicit_document_relation", "matching_topology", "unique_geometry", "direct_shared_structure"]},
                        "strength": {"type": "string", "enum": ["direct", "single_object_sheet", "standard"]},
                        "observation": {"type": "string", "maxLength": 180},
                        "source_fact_ids": {"type": "array", "maxItems": 3, "items": {"type": "string"}},
                        "structural_witness": DETECTION_V5_STRUCTURAL_WITNESS_SCHEMA,
                    }}},
        }}}

DETECTION_V5_PAGE_COVERAGE_SCHEMA: dict[str, Any] = {
    "type": "array", "maxItems": 100,
    "items": {"type": "object", "additionalProperties": False,
        "required": ["page_number", "visual_group_ids"],
        "properties": {
            "page_number": {"type": "integer", "minimum": 1},
            "visual_group_ids": {"type": "array", "maxItems": 64,
                "items": {"type": "string"}},
        }},
}

DETECTION_V5_SOURCE_DEGRADED_ONE_SHOT_REGISTRY_JSON_SCHEMA: dict[str, Any] = {
    "type": "object", "additionalProperties": False,
    "required": ["visual_groups", "page_coverage", "roles", "partitions"],
    "properties": {
        "visual_groups": DETECTION_VISUAL_REGISTRY_VISUAL_GROUPS_SCHEMA,
        "page_coverage": DETECTION_V5_PAGE_COVERAGE_SCHEMA,
        "roles": DETECTION_V5_SOURCE_DEGRADED_FULL_PAGE_ROLES_SCHEMA,
        "partitions": DETECTION_V5_SOURCE_DEGRADED_VISUAL_PARTITIONS_SCHEMA,
    },
}

DETECTION_VISUAL_REGISTRY_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "visual_groups", "classifications", "object_hypotheses", "candidate_region_exceptions", "semantic_facts",
    ],
    "properties": {
        "visual_groups": DETECTION_VISUAL_REGISTRY_VISUAL_GROUPS_SCHEMA,
        "classifications": DETECTION_VISUAL_CLASSIFICATIONS_SCHEMA,
        "object_hypotheses": DETECTION_V5_OBJECT_HYPOTHESES_SCHEMA,
        "candidate_region_exceptions": DETECTION_V5_CANDIDATE_REGION_EXCEPTIONS_SCHEMA,
        "semantic_facts": DETECTION_V5_SEMANTIC_FACTS_SCHEMA,
    },
}

# V5.6.1 predated the core-bbox requirement.  V5.16 deliberately replays its
# one-call visual contract in an isolated source-degraded experiment, so it
# must not require geometry the historical contract never requested.
DETECTION_V5_SOURCE_DEGRADED_V561_CONSENSUS_JSON_SCHEMA = copy.deepcopy(
    DETECTION_VISUAL_REGISTRY_JSON_SCHEMA
)
_V516_CONSENSUS_GROUP_SCHEMA = (
    DETECTION_V5_SOURCE_DEGRADED_V561_CONSENSUS_JSON_SCHEMA["properties"]
    ["visual_groups"]["items"]
)
_V516_CONSENSUS_GROUP_SCHEMA["required"].remove("core_bbox")
_V516_CONSENSUS_GROUP_SCHEMA["properties"].pop("core_bbox")

DETECTION_V5_DISCOVERY_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "visual_groups", "classifications", "candidate_region_exceptions", "page_coverage",
    ],
    "properties": {
        "visual_groups": DETECTION_VISUAL_REGISTRY_VISUAL_GROUPS_SCHEMA,
        "classifications": DETECTION_VISUAL_CLASSIFICATIONS_SCHEMA,
        "candidate_region_exceptions": DETECTION_V5_CANDIDATE_REGION_EXCEPTIONS_SCHEMA,
        "page_coverage": DETECTION_V5_PAGE_COVERAGE_SCHEMA,
    },
}

DETECTION_V5_MEMBERSHIP_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["object_hypotheses"],
    "properties": {"object_hypotheses": DETECTION_V5_OBJECT_HYPOTHESES_SCHEMA},
}

DETECTION_V5_SOURCE_DEGRADED_DISCOVERY_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "visual_groups", "page_coverage",
    ],
    "properties": {
        "visual_groups": DETECTION_VISUAL_REGISTRY_VISUAL_GROUPS_SCHEMA,
        "page_coverage": DETECTION_V5_PAGE_COVERAGE_SCHEMA,
    },
}

DETECTION_V5_SOURCE_DEGRADED_MEMBERSHIP_JSON_SCHEMA: dict[str, Any] = {
    "type": "object", "additionalProperties": False,
    "required": [
        "role_resolutions", "semantic_facts", "dimension_conflicts",
    ],
    "properties": {
        "role_resolutions": DETECTION_V5_SOURCE_DEGRADED_ROLE_RESOLUTIONS_SCHEMA,
        "semantic_facts": DETECTION_V5_SOURCE_DEGRADED_SEMANTIC_FACTS_SCHEMA,
        "dimension_conflicts": DETECTION_V5_SOURCE_DEGRADED_DIMENSION_CONFLICTS_SCHEMA,
    },
}

_STREAMLIT_SECRET_CACHE: dict[str, str] = {}
_STREAMLIT_SECRET_CACHE_LOCK = Lock()


def get_secret(name: str, default: str | None = None) -> str | None:
    """
    Reads config from environment first, then Streamlit secrets.

    This keeps CLI tests working and also supports Streamlit Cloud later.
    """
    value = os.getenv(name)
    if value:
        return value

    with _STREAMLIT_SECRET_CACHE_LOCK:
        cached = _STREAMLIT_SECRET_CACHE.get(name)
    if cached:
        return cached

    try:
        import streamlit as st

        if name in st.secrets:
            value = str(st.secrets[name])
            with _STREAMLIT_SECRET_CACHE_LOCK:
                _STREAMLIT_SECRET_CACHE[name] = value
            return value
    except Exception:
        pass

    return default


def detection_input_cache_enabled() -> bool:
    """Keep provider input caching off during fresh-file benchmark testing."""
    value = str(get_secret("DETECTION_INPUT_CACHE_ENABLED", "false") or "false")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def detection_naming_split_enabled() -> bool:
    """Use the active split Naming flow unless an explicit rollback disables it."""
    if "--naming-split" in sys.argv:
        return True
    value = str(get_secret("DETECTION_NAMING_SPLIT_EXPERIMENT", "true") or "true")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_anthropic_client() -> anthropic.Anthropic:
    api_key = get_secret("ANTHROPIC_API_KEY")

    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is missing. Add it to .streamlit/secrets.toml "
            "or export it as an environment variable."
        )

    # A source extraction must fail visibly rather than leave a synchronous
    # Streamlit interaction spinning for the SDK's much longer default.
    return anthropic.Anthropic(api_key=api_key, timeout=90.0)


def create_claude_message(client: anthropic.Anthropic, **kwargs: Any) -> Any:
    """Call Claude and turn SDK transport errors into actionable app errors."""
    try:
        return client.messages.create(**kwargs)
    except anthropic.APITimeoutError as exc:
        raise RuntimeError(
            "Claude request timed out before receiving a response. Try again with the same file."
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise RuntimeError(
            "Claude connection failed before receiving a response. "
            "Check network access, Anthropic service availability, and Streamlit secrets."
        ) from exc
    except anthropic.RateLimitError as exc:
        raise RuntimeError("Claude rate limit reached. Try again later.") from exc
    except anthropic.APIStatusError as exc:
        raise RuntimeError(
            f"Claude API returned HTTP {exc.status_code}: {exc.message}"
        ) from exc


def create_claude_message_streamed(
    client: anthropic.Anthropic,
    *,
    max_stream_seconds: float | None = None,
    on_stream_phase: Callable[[str, float], None] | None = None,
    cancel_requested: Callable[[], bool] | None = None,
    **kwargs: Any,
) -> tuple[Any, dict[str, Any]]:
    """Collect one streamed Message and precise request-phase diagnostics."""
    started_at = _utc_now_iso()
    started = time.perf_counter()
    first_event_seconds: float | None = None
    first_token_seconds: float | None = None
    stream_event_count = 0
    text_delta_count = 0
    request_id: str | None = None

    try:
        if cancel_requested is not None and cancel_requested():
            raise RuntimeError("Claude stream was cancelled.")
        with client.messages.stream(**kwargs) as stream:
            request_id = stream.request_id
            for event in stream:
                if cancel_requested is not None and cancel_requested():
                    raise RuntimeError("Claude stream was cancelled.")
                elapsed = time.perf_counter() - started
                if max_stream_seconds is not None and elapsed > max_stream_seconds:
                    raise RuntimeError(
                        f"Claude stream exceeded the {max_stream_seconds:.0f}-second limit. "
                        "Try the source again."
                    )
                stream_event_count += 1
                if first_event_seconds is None:
                    first_event_seconds = elapsed
                    if on_stream_phase is not None:
                        on_stream_phase("first_event", elapsed)

                if getattr(event, "type", None) != "content_block_delta":
                    continue
                delta = getattr(event, "delta", None)
                if getattr(delta, "type", None) != "text_delta":
                    continue
                if not str(getattr(delta, "text", "") or ""):
                    continue

                text_delta_count += 1
                if first_token_seconds is None:
                    first_token_seconds = elapsed
                    if on_stream_phase is not None:
                        on_stream_phase("first_token", elapsed)

            response = stream.get_final_message()
    except anthropic.APITimeoutError as exc:
        raise RuntimeError(
            "Claude request timed out before receiving a response. Try again with the same file."
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise RuntimeError(
            "Claude connection failed before receiving a response. "
            "Check network access, Anthropic service availability, and Streamlit secrets."
        ) from exc
    except anthropic.RateLimitError as exc:
        raise RuntimeError("Claude rate limit reached. Try again later.") from exc
    except anthropic.APIStatusError as exc:
        raise RuntimeError(
            f"Claude API returned HTTP {exc.status_code}: {exc.message}"
        ) from exc

    total_seconds = time.perf_counter() - started
    finished_at = _utc_now_iso()
    generation_seconds = (
        max(0.0, total_seconds - first_token_seconds)
        if first_token_seconds is not None
        else None
    )

    return response, {
        "request_id": request_id,
        "request_started_at": started_at,
        "first_event_seconds": (
            round(first_event_seconds, 6) if first_event_seconds is not None else None
        ),
        "time_to_first_token_seconds": (
            round(first_token_seconds, 6) if first_token_seconds is not None else None
        ),
        "generation_after_first_token_seconds": (
            round(generation_seconds, 6) if generation_seconds is not None else None
        ),
        "stream_total_seconds": round(total_seconds, 6),
        "request_finished_at": finished_at,
        "stream_event_count": stream_event_count,
        "text_delta_count": text_delta_count,
        "streaming": True,
    }


def strip_schema_for_claude(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Claude Structured Outputs supports JSON Schema, but not every validation
    keyword is guaranteed to be accepted in every surface/version.

    We send Claude the shape/type schema and keep strict numeric validation
    in validate_detection_result(...).
    """
    unsupported_keys = {
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "uniqueItems",
        "pattern",
        "format",
    }

    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: clean(item)
                for key, item in value.items()
                if key not in unsupported_keys
            }

        if isinstance(value, list):
            return [clean(item) for item in value]

        return value

    return clean(copy.deepcopy(schema))


def build_detection_ocr_context(
    ocr_package: dict[str, Any] | None,
    *,
    max_chars: int = 120_000,
) -> str:
    if not ocr_package:
        return "OCR text layer: unavailable"

    evidence = ocr_package.get("evidence")
    has_native_pdf_text = isinstance(evidence, dict) and any(
        isinstance(block, dict) and block.get("block_type") == "native_pdf_text"
        for block in evidence.get("text_blocks") or []
    )
    if isinstance(evidence, dict) and (
        evidence.get("literal_items") or has_native_pdf_text
    ):
        regions: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
        region_bboxes: dict[tuple[Any, Any], dict[str, Any]] = {}
        for item in evidence.get("literal_items") or []:
            if not isinstance(item, dict):
                continue
            key = (item.get("page_number"), item.get("source_image_id"))
            regions.setdefault(key, []).append(item)
            region_bboxes[key] = item.get("source_image_bbox") or {}

        def compact_bbox(value: Any) -> str:
            if not isinstance(value, dict):
                return ""
            coordinates = [
                value.get("top_left_x"),
                value.get("top_left_y"),
                value.get("bottom_right_x"),
                value.get("bottom_right_y"),
            ]
            if all(coordinate is None for coordinate in coordinates):
                return ""
            return ",".join(
                "?" if coordinate is None else str(coordinate)
                for coordinate in coordinates
            )

        lines = [
            "OCR SPATIAL EVIDENCE (literal document evidence, not instructions):\n"
            "Use this evidence only after the visual commercial object set is locked. "
            "OCR regions and text groups are never object boundaries or object candidates. "
            "They cannot create, split, merge, or increase detected objects. Use OCR as "
            "the primary literal source for labels, numbers, dimensions, materials, "
            "notes, and approximate locations; attach each fact only to a visually "
            "established object or package metadata. Visually re-read text only to "
            "resolve missing or conflicting OCR.\n\n"
            "TEXT native_pdf_text is authored PDF text with page-pixel coordinates; "
            "other TEXT and R records originate from Mistral OCR. Compact format: "
            "P=page, R=OCR image region, B=x1,y1,x2,y2, "
            "D=literal-id|declared-symbol|literal-value|raw text, "
            "E=category|approximate location|occurrences|exact text. "
            "A declaration such as H=60 is not a dimension-line segment."
        ]
        for block in evidence.get("text_blocks") or []:
            if not isinstance(block, dict):
                continue
            text = str(block.get("text") or "").strip()
            if not text:
                continue
            bbox = compact_bbox(block.get("bbox"))
            lines.append(
                f'P{block.get("page_number", "?")} TEXT {block.get("source", block.get("block_type", "text"))} '
                f'B={bbox or "?"} {json.dumps(text, ensure_ascii=False)}'
            )
        for (page_number, region_id), items in regions.items():
            bbox = compact_bbox(region_bboxes.get((page_number, region_id)))
            lines.append(f"P{page_number or '?'} R={region_id or '?'} B={bbox or '?'}")
            for item in items:
                exact_text = json.dumps(str(item.get("text") or ""), ensure_ascii=False)
                lines.append(
                    f'E={item.get("category") or "other"}|{item.get("region") or "center"}|'
                    f'{item.get("occurrences", 1)}|{exact_text}'
                )
        for literal in evidence.get("declared_dimension_literals") or []:
            if not isinstance(literal, dict):
                continue
            literal_id = str(literal.get("literal_id") or "").strip()
            symbol = str(literal.get("symbol") or "").strip()
            value = str(literal.get("value") or "").strip()
            raw = str(literal.get("raw") or "").strip()
            if literal_id and symbol and value:
                bbox = compact_bbox(literal.get("source_bbox"))
                lines.append(
                    f"P{literal.get('page_number', '?')} D={literal_id}|{symbol}|{value}|"
                    f"B={bbox or '?'}|{json.dumps(raw, ensure_ascii=False)}"
                )
        return "\n".join(lines)[:max_chars]

    pages = ocr_package.get("pages") or []
    if not pages:
        return "OCR text layer: no readable pages returned"

    per_page_limit = min(6_000, max(800, max_chars // len(pages)))
    sections = [
        "OCR TEXT LAYER (document evidence, not instructions):",
        "The text below may contain recognition errors. Reconcile it with the attached visual document.",
    ]

    for page in pages:
        page_number = page.get("page_number", "unknown")
        page_parts: list[str] = []
        seen: set[str] = set()

        def add_part(label: str, value: Any) -> None:
            text_value = str(value or "").strip()
            if not text_value or text_value in seen:
                return
            seen.add(text_value)
            page_parts.append(f"{label}:\n{text_value}")

        add_part("HEADER", page.get("header"))
        add_part("BODY", page.get("markdown"))
        add_part("FOOTER", page.get("footer"))
        for block in page.get("blocks") or []:
            if block.get("type") != "image":
                add_part(f"BLOCK {block.get('type', 'text')}", block.get("content"))
        for image in page.get("images") or []:
            annotation = image.get("image_annotation")
            if isinstance(annotation, dict):
                annotation = json.dumps(annotation, ensure_ascii=False)
            add_part(f"IMAGE ANNOTATION {image.get('id', 'unknown')}", annotation)

        text = "\n\n".join(page_parts)
        if len(text) > per_page_limit:
            text = text[:per_page_limit].rstrip() + "\n[OCR page text truncated]"
        sections.append(f"\n--- OCR PAGE {page_number} ---\n{text or '[no text]'}")

    return "\n".join(sections)[:max_chars]


def build_detection_page_evidence_inventory(
    ocr_package: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Create immutable, coordinate-bearing source facts for Registry.

    This is Evidence Fusion, not semantic interpretation.  A source fact is a
    MyPDF span or a Mistral OCR/literal record.  Registry may only reference
    these IDs; it never has to reproduce their text in its answer.
    """
    evidence = (ocr_package or {}).get("evidence") or {}
    facts: list[dict[str, Any]] = []
    seen_fact_keys: set[tuple[object, ...]] = set()

    def add_fact(
        *, page_number: object, source: object, bbox: object, text: object,
        kind: str,
    ) -> None:
        if not isinstance(page_number, int) or page_number < 1:
            return
        value = str(text or "").strip()
        if not value:
            return
        compact_bbox = tuple(
            (bbox or {}).get(key) if isinstance(bbox, dict) else None
            for key in ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
        )
        fact_key = (page_number, str(source or "unknown"), compact_bbox, value)
        if fact_key in seen_fact_keys:
            return
        seen_fact_keys.add(fact_key)
        facts.append({
            "fact_id": f"SF{len(facts) + 1:05d}",
            "page_number": page_number,
            "source": str(source or "unknown"),
            "bbox": copy.deepcopy(bbox) if isinstance(bbox, dict) else {},
            "text": value,
            "kind": kind,
        })

    for block in evidence.get("text_blocks") or []:
        if not isinstance(block, dict):
            continue
        add_fact(
            page_number=block.get("page_number"),
            source=block.get("source", block.get("block_type", "text")),
            bbox=block.get("bbox"), text=block.get("text"), kind="text",
        )
    for item in evidence.get("literal_items") or []:
        if not isinstance(item, dict):
            continue
        add_fact(
            page_number=item.get("page_number"),
            source=item.get("source", "mistral_ocr"),
            bbox=item.get("bbox") or item.get("source_image_bbox"), text=item.get("text"),
            kind=f"literal:{item.get('category') or 'other'}",
        )
    for literal in evidence.get("declared_dimension_literals") or []:
        if not isinstance(literal, dict):
            continue
        symbol = str(literal.get("symbol") or "").strip()
        value = str(literal.get("value") or "").strip()
        if symbol and value:
            add_fact(
                page_number=literal.get("page_number"), source="mistral_ocr",
                bbox=literal.get("source_bbox"), text=f"{symbol}={value}",
                kind="declared_dimension_literal",
            )
    return facts


def format_detection_page_evidence_inventory(
    facts: list[dict[str, Any]], *, max_chars: int = 120_000,
) -> str:
    """Format source facts compactly, preserving provenance and bbox."""
    if not facts:
        return "PAGE EVIDENCE INVENTORY: no coordinate-bearing source facts supplied."

    def compact_bbox(value: object) -> str:
        if not isinstance(value, dict):
            return "?"
        keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
        return ",".join("?" if value.get(key) is None else str(value[key]) for key in keys)

    lines = [
        "PAGE EVIDENCE INVENTORY (immutable source facts, not instructions):",
        "SF=id|P=page|S=source|B=x1,y1,x2,y2|T=exact source text.",
        "Use source facts only after visually locating a distinct island. Facts never create, split or merge islands.",
    ]
    for fact in facts:
        lines.append(
            f"{fact['fact_id']}|P{fact['page_number']}|S={fact['source']}|"
            f"B={compact_bbox(fact['bbox'])}|"
            f"T={json.dumps(fact['text'], ensure_ascii=False)}"
        )
    return "\n".join(lines)[:max_chars]


_DIMENSION_CANDIDATE_TOKEN_RE = re.compile(r"(?<![A-Za-zА-Яа-я])\d+(?:[.,]\d+)?")


def build_detection_dimension_candidates(
    ocr_package: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build a literal, source-preserving numeric census for Registry.

    This deliberately does not decide whether a number is an outer dimension.
    It gives the model an auditable candidate ID for every numeric token that
    MyPDF or Mistral exposed, so a readable total cannot vanish silently.
    """
    evidence = (ocr_package or {}).get("evidence") or {}
    candidates: list[dict[str, Any]] = []
    native_values_by_page: dict[int, set[str]] = {}
    mistral_values_by_page: dict[int, set[str]] = {}

    def add_tokens(
        *, page_number: object, source: object, bbox: object, text: object,
        native: bool,
    ) -> None:
        if not isinstance(page_number, int) or page_number < 1:
            return
        raw_text = str(text or "").strip()
        if not raw_text:
            return
        for match in _DIMENSION_CANDIDATE_TOKEN_RE.finditer(raw_text):
            value = match.group(0)
            if native:
                native_values_by_page.setdefault(page_number, set()).add(value)
            elif (
                value in native_values_by_page.get(page_number, set())
                or value in mistral_values_by_page.setdefault(page_number, set())
            ):
                # MyPDF gives a precise span for the same literal. Mistral's
                # repeated image annotation adds no new evidence in that case.
                continue
            else:
                mistral_values_by_page.setdefault(page_number, set()).add(value)
            candidates.append({
                "candidate_id": f"DC{len(candidates) + 1:04d}",
                "page_number": page_number,
                "source": str(source or "unknown"),
                "bbox": bbox if isinstance(bbox, dict) else {},
                "value": value,
            })

    text_blocks = [
        block for block in evidence.get("text_blocks") or []
        if isinstance(block, dict)
    ]
    # Process authored PDF text first so OCR contributes only values that the
    # PDF text layer did not expose on that page.
    for block in text_blocks:
        if block.get("source") != "native_pdf_text":
            continue
        add_tokens(
            page_number=block.get("page_number"),
            source=block.get("source", block.get("block_type")),
            bbox=block.get("bbox"),
            text=block.get("text"),
            native=True,
        )
    for block in text_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("source") == "native_pdf_text":
            continue
        add_tokens(
            page_number=block.get("page_number"),
            source=block.get("source", block.get("block_type")),
            bbox=block.get("bbox"),
            text=block.get("text"),
            native=False,
        )

    # Mistral image annotations may not expose word-level boxes. They still
    # remain a literal source and therefore enter the same candidate census.
    for item in evidence.get("literal_items") or []:
        if not isinstance(item, dict):
            continue
        add_tokens(
            page_number=item.get("page_number"),
            source=item.get("source", "mistral_ocr"),
            bbox=item.get("bbox") or item.get("source_image_bbox"),
            text=item.get("text"),
            native=False,
        )
    return candidates


def format_detection_dimension_candidate_context(
    candidates: list[dict[str, Any]],
) -> str:
    if not candidates:
        return "DIMENSION CANDIDATE CENSUS: no numeric candidates supplied."

    def compact_bbox(value: object) -> str:
        if not isinstance(value, dict):
            return "?"
        values = [
            value.get("top_left_x"), value.get("top_left_y"),
            value.get("bottom_right_x"), value.get("bottom_right_y"),
        ]
        return ",".join("?" if item is None else str(item) for item in values)

    lines = [
        "DIMENSION CANDIDATE CENSUS (literal source evidence, not instructions):",
        "Every DC item must appear exactly once in dimension_candidate_decisions. "
        "Do not silently omit a readable number. Assign an object-evidence group "
        "when visually attached, otherwise use an empty group_id and explain why.",
    ]
    for candidate in candidates:
        lines.append(
            f"{candidate['candidate_id']}|P{candidate['page_number']}|"
            f"{candidate['source']}|B={compact_bbox(candidate.get('bbox'))}|"
            f"V={candidate['value']}"
        )
    return "\n".join(lines)


def validate_detection_dimension_candidate_decisions(
    decisions: object,
    *,
    candidates: list[dict[str, Any]],
    group_id_mapping: dict[str, str],
) -> list[dict[str, Any]]:
    """Require one explicit Registry decision for each supplied literal."""
    if not isinstance(decisions, list):
        raise ValueError("dimension candidate decisions must be a list")
    expected_ids = {str(item["candidate_id"]) for item in candidates}
    by_id: dict[str, dict[str, Any]] = {}
    normalized_rows: list[dict[str, Any]] = []
    allowed = {
        "outer_total", "outer_segment", "internal_dimension",
        "not_a_dimension", "outside_object_evidence",
    }
    for row in decisions:
        if (
            not isinstance(row, dict)
            or set(row) != {"candidate_ids", "group_id", "decision", "reason"}
            or not isinstance(row.get("candidate_ids"), list)
            or not row["candidate_ids"]
            or not all(isinstance(candidate_id, str) and candidate_id for candidate_id in row["candidate_ids"])
            or len(row["candidate_ids"]) != len(set(row["candidate_ids"]))
            or row.get("decision") not in allowed
            or not isinstance(row.get("group_id"), str)
            or not isinstance(row.get("reason"), str)
            or not row["reason"].strip()
        ):
            raise ValueError("dimension candidate decisions are invalid")
        normalized = dict(row)
        normalized["group_id"] = group_id_mapping.get(
            row["group_id"], row["group_id"]
        )
        for candidate_id in row["candidate_ids"]:
            if candidate_id in by_id:
                raise ValueError("dimension candidate decisions are invalid")
            by_id[candidate_id] = normalized
        normalized_rows.append(normalized)
    if set(by_id) != expected_ids:
        missing = sorted(expected_ids - set(by_id))
        unknown = sorted(set(by_id) - expected_ids)
        raise ValueError(
            "dimension candidate decisions must account for every supplied candidate"
            f" (missing={missing[:5]}, unknown={unknown[:5]})"
        )
    return normalized_rows


def validate_detection_candidate_chain_consistency(
    decisions: list[dict[str, Any]],
    *,
    candidates: list[dict[str, Any]],
    dimension_inventory: list[dict[str, Any]],
) -> None:
    """An outer-candidate decision must be represented in that group's chain."""
    values_by_candidate_id = {
        str(candidate["candidate_id"]): str(candidate["value"])
        for candidate in candidates
    }
    chain_values_by_group: dict[str, set[str]] = {}
    for row in dimension_inventory:
        group_id = str(row.get("group_id") or "")
        values: set[str] = set()
        for chain in row.get("envelope_chains") or []:
            values.update(str(value) for value in chain.get("segments") or [])
            total = str(chain.get("direct_total") or "").strip()
            if total:
                values.add(total)
        chain_values_by_group[group_id] = values
    for row in decisions:
        if row["decision"] not in {"outer_total", "outer_segment"}:
            continue
        group_id = str(row["group_id"] or "")
        chain_values = chain_values_by_group.get(group_id, set())
        if not group_id or any(
            values_by_candidate_id[candidate_id] not in chain_values
            for candidate_id in row["candidate_ids"]
        ):
            raise ValueError(
                "outer dimension candidate decisions must appear in the group's envelope chains"
            )


def build_detection_island_dimension_audit(
    *,
    visual_groups: list[dict[str, Any]],
    dimension_inventory: list[dict[str, Any]],
    ocr_package: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Expose OCR literals and the Registry's chains side by side per island.

    OCR literals enter an island only through the Registry's explicit
    ``ocr_literal_ids`` references.  Same-page literals which the model did
    not attribute remain visible separately, so this audit never presents a
    page-level guess as object-specific evidence.
    """
    literals_by_id = {
        str(item.get("literal_id")): item
        for item in ((ocr_package or {}).get("evidence") or {}).get(
            "declared_dimension_literals", []
        )
        if isinstance(item, dict) and str(item.get("literal_id") or "").strip()
    }
    inventory_by_group_id = {
        str(row.get("group_id")): row
        for row in dimension_inventory
        if isinstance(row, dict) and str(row.get("group_id") or "").strip()
    }
    result: list[dict[str, Any]] = []
    for group in visual_groups:
        if not isinstance(group, dict):
            continue
        group_id = str(group.get("group_id") or "")
        page_number = group.get("page_number")
        row = inventory_by_group_id.get(group_id, {})
        literal_ids = [
            str(value) for value in row.get("ocr_literal_ids") or []
            if str(value).strip()
        ]
        attributed = [
            literals_by_id[literal_id]
            for literal_id in literal_ids
            if literal_id in literals_by_id
        ]
        unknown_ids = [
            literal_id for literal_id in literal_ids if literal_id not in literals_by_id
        ]
        same_page_unattributed = [
            item for item in literals_by_id.values()
            if item.get("page_number") == page_number
            and item.get("literal_id") not in literal_ids
        ]
        result.append({
            "visual_group_id": group_id,
            "page_number": page_number,
            "location_hint": group.get("location_hint"),
            "ocr_declared_literals": attributed,
            "unattributed_ocr_literals_on_page": same_page_unattributed,
            "unknown_ocr_literal_ids": unknown_ids,
            "model_envelope_chains": list(row.get("envelope_chains") or []),
        })
    return result


def extract_detection_document_dimension_unit_profile(
    ocr_package: dict[str, Any] | None,
) -> dict[str, Any]:
    """Read one document-level unit only from explicit OCR dimension markers.

    Bare dimensions inherit the profile only when every explicit marker found
    in the document agrees. This is deterministic OCR parsing, not a model
    guess, and intentionally does not convert any value.
    """
    matches: dict[str, set[int]] = {}
    for page in (ocr_package or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        try:
            page_number = int(page.get("page_number"))
        except (TypeError, ValueError):
            continue
        strings = [
            page.get("header"), page.get("footer"), page.get("markdown"),
        ]
        strings.extend(
            block.get("content")
            for block in page.get("blocks") or []
            if isinstance(block, dict)
        )
        for image in page.get("images") or []:
            if not isinstance(image, dict):
                continue
            annotation = image.get("image_annotation")
            if isinstance(annotation, dict):
                annotation = json.dumps(annotation, ensure_ascii=False)
            strings.append(annotation)
        for text in strings:
            source = str(text or "")
            for unit, pattern in _DOCUMENT_DIMENSION_UNIT_PATTERNS:
                if pattern.search(source):
                    matches.setdefault(unit, set()).add(page_number)

    if len(matches) == 1:
        unit, pages = next(iter(matches.items()))
        return {
            "unit": unit,
            "status": "one_explicit_document_unit",
            "evidence_pages": sorted(pages),
        }
    if not matches:
        return {
            "unit": "unknown",
            "status": "no_explicit_document_unit",
            "evidence_pages": [],
        }
    return {
        "unit": "unknown",
        "status": "conflicting_explicit_document_units",
        "evidence_pages": sorted({page for pages in matches.values() for page in pages}),
        "explicit_units": sorted(matches),
    }


def format_detection_document_dimension_unit_profile(
    profile: dict[str, Any],
) -> str:
    """Give Registry a short deterministic unit fact, never a new decision."""
    unit = str(profile.get("unit") or "unknown")
    status = str(profile.get("status") or "unknown")
    pages = ", ".join(str(page) for page in profile.get("evidence_pages") or [])
    if unit == "unknown":
        return (
            "DOCUMENT DIMENSION UNIT PROFILE: unknown. Do not infer a unit; "
            "return only literal numeric readings."
        )
    return (
        f"DOCUMENT DIMENSION UNIT PROFILE: {unit}, determined from explicit OCR "
        f"markers on page(s) {pages or '?'}. Bare numeric dimensions in this "
        "document use this one profile."
    )


def build_detection_user_text(
    file_name: str,
    company_id: str,
    ocr_package: dict[str, Any] | None = None,
    *,
    include_spatial_inventory: bool = False,
) -> str:
    ocr_context = build_detection_ocr_context(ocr_package)
    spatial_context = (
        "\n\n" + spatial_inventory_context(
            build_detection_spatial_inventory(ocr_package)
        )
        if include_spatial_inventory else ""
    )

    return f"""
You are running the RFQ Detection Agent for a custom fabrication estimate system.

Company ID:
{company_id}

Uploaded file name:
{file_name}

{ocr_context}
{spatial_context}

Task:
Analyze the attached RFQ / drawing package and return ONLY the structured JSON object required by the schema.
""".strip()


def build_detection_system_content(
    *,
    cache_enabled: bool = False,
    prompt: str | None = None,
) -> list[dict[str, Any]]:
    """Build the business contract, optionally enabling provider input caching."""
    if prompt is None:
        prompt = (
            load_detection_agent_without_naming_prompt()
            if detection_naming_split_enabled()
            else load_detection_agent_prompt()
        )
    block = {
        "type": "text",
        "text": (
            "You are the RFQ Detection Agent for a custom fabrication "
            "estimate system. Follow this business logic contract exactly:\n\n"
            f"{prompt}"
        ),
    }
    if cache_enabled:
        block["cache_control"] = {"type": "ephemeral"}
    return [block]


def encode_pdf_bytes(file_bytes: bytes) -> str:
    if not file_bytes:
        raise ValueError("file_bytes is empty")

    return base64.standard_b64encode(file_bytes).decode("utf-8")


def build_uploaded_file_content_block(
    file_name: str,
    file_bytes: bytes,
    *,
    cache_enabled: bool = False,
) -> dict[str, Any]:
    """Build the Claude content block for supported RFQ upload formats."""
    if not file_bytes:
        raise ValueError("file_bytes is empty")

    suffix = Path(file_name).suffix.lower()
    encoded = base64.standard_b64encode(file_bytes).decode("utf-8")

    if suffix == ".pdf":
        block = {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": encoded,
            },
        }
        if cache_enabled:
            block["cache_control"] = {"type": "ephemeral"}
        return block

    if suffix in {".jpg", ".jpeg"}:
        block = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": encoded,
            },
        }
        if cache_enabled:
            block["cache_control"] = {"type": "ephemeral"}
        return block

    if suffix == ".png":
        block = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": encoded,
            },
        }
        if cache_enabled:
            block["cache_control"] = {"type": "ephemeral"}
        return block

    raise ValueError("Unsupported RFQ file type. Upload PDF, JPEG, or PNG.")


def build_detection_content_blocks(
    *,
    file_name: str,
    file_bytes: bytes,
    user_text: str,
    page_images: list[bytes] | None = None,
    page_image_numbers: list[int] | None = None,
    cache_enabled: bool = False,
) -> list[dict[str, Any]]:
    """Build one ordered package from an inline file or rendered PDF pages."""
    if page_images:
        blocks: list[dict[str, Any]] = []
        for position, page_bytes in enumerate(page_images, start=1):
            page_number = page_image_numbers[position - 1] if page_image_numbers else position
            blocks.append({"type": "text", "text": f"PDF page {page_number}"})
            blocks.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64.standard_b64encode(page_bytes).decode("ascii"),
                    },
                }
            )
    else:
        blocks = [
            build_uploaded_file_content_block(
                file_name,
                file_bytes,
                cache_enabled=cache_enabled,
            )
        ]
    blocks.append({"type": "text", "text": user_text})
    return blocks

def build_detection_registry_content_blocks(*, file_name: str, file_bytes: bytes, user_text: str, page_images: list[bytes], regions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocks = build_detection_content_blocks(file_name=file_name, file_bytes=file_bytes, user_text="", page_images=page_images)
    blocks.pop()
    for region in regions:
        blocks.append({"type":"text", "text":f"PDF page {region['page_number']} enlarged region: {region['region']}"})
        blocks.append({"type":"image", "source":{"type":"base64","media_type":"image/jpeg","data":base64.standard_b64encode(region["bytes"]).decode("ascii")}})
    blocks.append({"type":"text", "text":user_text})
    return blocks


def _detection_bbox(value: object) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
    try:
        bbox = {key: int(value[key]) for key in keys}
    except (KeyError, TypeError, ValueError):
        return None
    if bbox["bottom_right_x"] <= bbox["top_left_x"] or bbox["bottom_right_y"] <= bbox["top_left_y"]:
        return None
    return bbox


def _detection_bbox_area(bbox: dict[str, int]) -> int:
    return (bbox["bottom_right_x"] - bbox["top_left_x"]) * (
        bbox["bottom_right_y"] - bbox["top_left_y"]
    )


def build_detection_v5_review_coordinate_frames(
    *,
    ocr_package: dict[str, Any] | None,
    page_images: list[bytes],
) -> tuple[dict[int, dict[str, Any]], list[dict[str, Any]]]:
    """Map Fusion's OCR pixel frame onto the smaller Registry review images.

    Fusion facts, Candidate Regions and Registry bboxes use the Mistral-rendered
    page frame (normally 200 dpi). Registry pages are deliberately rendered at
    96 dpi to bound provider input. Review crops and overlays must transform
    bboxes between those frames rather than treating the coordinates as equal.
    """
    try:
        from PIL import Image
    except ImportError:
        return {}, [{"reason": "Pillow unavailable"}]

    source_pages: dict[int, dict[str, Any]] = {}
    for page in (ocr_package or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        try:
            page_number = int(page.get("page_number"))
        except (TypeError, ValueError):
            continue
        if page_number >= 1:
            source_pages[page_number] = page

    rendering = (ocr_package or {}).get("rendering") or {}
    try:
        fusion_dpi = float(rendering.get("dpi") or 200)
    except (TypeError, ValueError):
        fusion_dpi = 200.0
    frames: dict[int, dict[str, Any]] = {}
    audit: list[dict[str, Any]] = []
    for page_number, page_bytes in enumerate(page_images, start=1):
        try:
            with Image.open(BytesIO(page_bytes)) as image:
                review_width, review_height = image.size
        except Exception as exc:
            audit.append({
                "page_number": page_number,
                "reason": f"review page unavailable: {type(exc).__name__}",
            })
            continue

        dimensions = (source_pages.get(page_number) or {}).get("dimensions")
        try:
            fusion_width = int(round(float((dimensions or {}).get("width"))))
            fusion_height = int(round(float((dimensions or {}).get("height"))))
        except (AttributeError, TypeError, ValueError):
            fusion_width = fusion_height = 0
        source = "mistral_page_dimensions"
        if fusion_width <= 0 or fusion_height <= 0:
            fusion_width = max(1, round(review_width * fusion_dpi / DEFAULT_PAGE_IMAGE_DPI))
            fusion_height = max(1, round(review_height * fusion_dpi / DEFAULT_PAGE_IMAGE_DPI))
            source = "dpi_ratio_fallback"

        frame = {
            "page_number": page_number,
            "fusion_dimensions": {"width": fusion_width, "height": fusion_height},
            "review_dimensions": {"width": review_width, "height": review_height},
            "scale_x": round(review_width / fusion_width, 9),
            "scale_y": round(review_height / fusion_height, 9),
            "source": source,
        }
        frames[page_number] = frame
        audit.append(copy.deepcopy(frame))
    return frames, audit


def build_detection_v5_visual_page_frames(
    page_images: list[bytes],
) -> tuple[dict[int, dict[str, int]], list[dict[str, Any]]]:
    """Describe the rendered-pixel frame used by the source-degraded route."""
    try:
        from PIL import Image
    except ImportError:
        return {}, [{"reason": "Pillow unavailable"}]
    frames: dict[int, dict[str, int]] = {}
    audit: list[dict[str, Any]] = []
    for page_number, page_bytes in enumerate(page_images, start=1):
        try:
            with Image.open(BytesIO(page_bytes)) as image:
                frame = {"width": int(image.width), "height": int(image.height)}
        except Exception as exc:
            audit.append({
                "page_number": page_number,
                "reason": f"rendered page unavailable: {type(exc).__name__}",
            })
            continue
        frames[page_number] = frame
        audit.append({"page_number": page_number, **frame})
    return frames, audit


def _source_dimensions_by_page(
    ocr_package: dict[str, Any] | None,
) -> dict[int, tuple[int, int]]:
    dimensions: dict[int, tuple[int, int]] = {}
    for page in (ocr_package or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        try:
            page_number = int(page.get("page_number"))
            width = int(round(float((page.get("dimensions") or {}).get("width"))))
            height = int(round(float((page.get("dimensions") or {}).get("height"))))
        except (TypeError, ValueError):
            continue
        if page_number >= 1 and width > 0 and height > 0:
            dimensions[page_number] = (width, height)
    return dimensions


def _validate_source_degraded_visual_geometry(
    visual_groups: list[dict[str, Any]],
    *,
    page_frames: dict[int, dict[str, int]],
) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, int]]]:
    """Keep visual-only Discovery in the explicit rendered-page frame."""
    identity_mapping = {
        str(group.get("group_id") or ""): str(group.get("group_id") or "")
        for group in visual_groups if isinstance(group, dict)
    }
    envelopes = _normalize_registry_group_bboxes(
        visual_groups, group_id_mapping=identity_mapping,
    )
    cores = _normalize_registry_group_core_bboxes(
        visual_groups, group_id_mapping=identity_mapping,
        evidence_envelopes=envelopes,
    )
    for group in visual_groups:
        group_id = str(group.get("group_id") or "")
        page_number = group.get("page_number")
        frame = page_frames.get(page_number) if isinstance(page_number, int) else None
        bbox = envelopes.get(group_id)
        if frame is None or bbox is None:
            raise ValueError("source-degraded visual group has no rendered page frame")
        if (
            bbox["bottom_right_x"] > frame["width"]
            or bbox["bottom_right_y"] > frame["height"]
        ):
            raise ValueError("source-degraded visual group bbox exceeds rendered page")
    return envelopes, cores


def format_detection_v5_coordinate_frame_context(
    frames: dict[int, dict[str, Any]],
) -> str:
    """State the output bbox frame explicitly when page images use another dpi."""
    if not frames:
        return "PAGE COORDINATE FRAMES: unavailable."
    lines = [
        "PAGE COORDINATE FRAMES:",
        "All returned Island bbox coordinates must use the FUSION frame, not image pixels.",
        "FRAME=P|FUSION=widthxheight|IMAGE=widthxheight.",
    ]
    for page_number, frame in sorted(frames.items()):
        fusion = frame["fusion_dimensions"]
        review = frame["review_dimensions"]
        lines.append(
            f"P{page_number}|FUSION={fusion['width']}x{fusion['height']}|"
            f"IMAGE={review['width']}x{review['height']}"
        )
    return "\n".join(lines)


def _scale_detection_bbox_to_review_image(
    bbox: dict[str, int],
    *,
    frame: dict[str, Any] | None,
    review_width: int,
    review_height: int,
) -> dict[str, int] | None:
    """Convert one Fusion-frame bbox to a concrete review-image bbox."""
    if frame is None:
        return copy.deepcopy(bbox)
    fusion = frame.get("fusion_dimensions") if isinstance(frame, dict) else None
    try:
        fusion_width = float(fusion["width"])
        fusion_height = float(fusion["height"])
    except (KeyError, TypeError, ValueError):
        return None
    if fusion_width <= 0 or fusion_height <= 0:
        return None

    def scale_x(value: int) -> int:
        return round(value * review_width / fusion_width)

    def scale_y(value: int) -> int:
        return round(value * review_height / fusion_height)

    left = max(0, min(review_width - 1, scale_x(bbox["top_left_x"])))
    top = max(0, min(review_height - 1, scale_y(bbox["top_left_y"])))
    right = max(left + 1, min(review_width, scale_x(bbox["bottom_right_x"])))
    bottom = max(top + 1, min(review_height, scale_y(bbox["bottom_right_y"])))
    return {
        "top_left_x": left,
        "top_left_y": top,
        "bottom_right_x": right,
        "bottom_right_y": bottom,
    }


def _detection_bbox_centre_inside(
    inner: dict[str, int], outer: dict[str, int],
) -> bool:
    centre_x = (inner["top_left_x"] + inner["bottom_right_x"]) / 2
    centre_y = (inner["top_left_y"] + inner["bottom_right_y"]) / 2
    return (
        outer["top_left_x"] <= centre_x <= outer["bottom_right_x"]
        and outer["top_left_y"] <= centre_y <= outer["bottom_right_y"]
    )


def build_detection_v5_membership_view_crops(
    *,
    page_images: list[bytes],
    visual_groups: list[dict[str, Any]],
    coordinate_frames: dict[int, dict[str, Any]] | None = None,
    max_side: int = DETECTION_V5_MEMBERSHIP_CROP_MAX_SIDE,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Crop fixed Object Views for the membership-only Registry input."""
    try:
        from PIL import Image
    except ImportError:
        return [], [{"reason": "Pillow unavailable"}]

    crops: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    for group in visual_groups:
        if group.get("evidence_class") != "object_evidence":
            continue
        group_id = str(group.get("group_id") or "")
        try:
            page_number = int(group.get("page_number"))
        except (TypeError, ValueError):
            audit.append({"group_id": group_id, "reason": "invalid page number"})
            continue
        bbox = _detection_bbox(group.get("bbox"))
        if not group_id or bbox is None or not 1 <= page_number <= len(page_images):
            audit.append({"group_id": group_id, "reason": "invalid group bbox"})
            continue
        try:
            with Image.open(BytesIO(page_images[page_number - 1])) as image:
                width, height = image.size
                review_bbox = _scale_detection_bbox_to_review_image(
                    bbox,
                    frame=(coordinate_frames or {}).get(page_number),
                    review_width=width,
                    review_height=height,
                )
                if review_bbox is None:
                    raise ValueError("review coordinate frame unavailable")
                margin_x = max(8, round((review_bbox["bottom_right_x"] - review_bbox["top_left_x"]) * 0.04))
                margin_y = max(8, round((review_bbox["bottom_right_y"] - review_bbox["top_left_y"]) * 0.04))
                left = max(0, min(width - 1, review_bbox["top_left_x"] - margin_x))
                top = max(0, min(height - 1, review_bbox["top_left_y"] - margin_y))
                right = max(left + 1, min(width, review_bbox["bottom_right_x"] + margin_x))
                bottom = max(top + 1, min(height, review_bbox["bottom_right_y"] + margin_y))
                crop = image.crop((left, top, right, bottom))
                crop.thumbnail(
                    (max_side,) * 2,
                    Image.Resampling.LANCZOS,
                )
                output = BytesIO()
                crop.save(output, format="JPEG", quality=80)
        except Exception as exc:
            audit.append({"group_id": group_id, "reason": f"crop unavailable: {type(exc).__name__}"})
            continue
        crops.append({
            "group_id": group_id,
            "page_number": page_number,
            "bytes": output.getvalue(),
        })
        audit.append({
            "group_id": group_id,
            "page_number": page_number,
            "source_bbox": bbox,
            "review_bbox": review_bbox,
            "crop_bbox": {
                "top_left_x": left, "top_left_y": top,
                "bottom_right_x": right, "bottom_right_y": bottom,
            },
            "crop_dimensions": {"width": crop.width, "height": crop.height},
            "coordinate_frame": "fusion_to_review",
        })
    return crops, audit


def build_detection_v5_membership_page_context_images(
    *,
    page_images: list[bytes],
    page_numbers: set[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Supply low-resolution page geometry to Membership without new inventory."""
    try:
        from PIL import Image
    except ImportError:
        return [], [{"reason": "Pillow unavailable"}]

    contexts: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    for page_number in sorted(page_numbers):
        if not 1 <= page_number <= len(page_images):
            audit.append({"page_number": page_number, "reason": "page unavailable"})
            continue
        try:
            with Image.open(BytesIO(page_images[page_number - 1])) as image:
                page = image.convert("RGB")
                page.thumbnail(
                    (DETECTION_V5_MEMBERSHIP_PAGE_CONTEXT_MAX_SIDE,) * 2,
                    Image.Resampling.LANCZOS,
                )
                output = BytesIO()
                page.save(output, format="JPEG", quality=70)
        except Exception as exc:
            audit.append({"page_number": page_number, "reason": f"context unavailable: {type(exc).__name__}"})
            continue
        contexts.append({"page_number": page_number, "bytes": output.getvalue()})
    return contexts, audit


def build_detection_v5_review_page_context_images(
    *,
    page_images: list[bytes],
    visual_groups: list[dict[str, Any]],
    coordinate_frames: dict[int, dict[str, Any]] | None = None,
    max_side: int = DETECTION_V5_MEMBERSHIP_PAGE_CONTEXT_MAX_SIDE,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Render bounded full-page review context with immutable Island labels."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return [], [{"reason": "Pillow unavailable"}]

    groups_by_page: dict[int, list[dict[str, Any]]] = {}
    for group in visual_groups:
        if group.get("evidence_class") != "object_evidence":
            continue
        try:
            page_number = int(group.get("page_number"))
        except (TypeError, ValueError):
            continue
        if _detection_bbox(group.get("bbox")) is not None:
            groups_by_page.setdefault(page_number, []).append(group)

    contexts: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    palette = ("#D00000", "#0057B8", "#008A2E", "#9B1C9B", "#A15C00", "#006D77")
    for page_number, groups in sorted(groups_by_page.items()):
        if not 1 <= page_number <= len(page_images):
            audit.append({"page_number": page_number, "reason": "page unavailable"})
            continue
        try:
            with Image.open(BytesIO(page_images[page_number - 1])) as image:
                page = image.convert("RGB")
                original_width, original_height = page.size
                if max_side > 0:
                    page.thumbnail(
                        (max_side,) * 2,
                        Image.Resampling.LANCZOS,
                    )
                scale_x = page.width / original_width
                scale_y = page.height / original_height
                draw = ImageDraw.Draw(page)
                overlay_audit: list[dict[str, Any]] = []
                for index, group in enumerate(sorted(groups, key=lambda row: str(row.get("group_id") or ""))):
                    bbox = _detection_bbox(group.get("bbox"))
                    if bbox is None:
                        continue
                    review_bbox = _scale_detection_bbox_to_review_image(
                        bbox,
                        frame=(coordinate_frames or {}).get(page_number),
                        review_width=original_width,
                        review_height=original_height,
                    )
                    if review_bbox is None:
                        continue
                    colour = palette[index % len(palette)]
                    box = (
                        round(review_bbox["top_left_x"] * scale_x),
                        round(review_bbox["top_left_y"] * scale_y),
                        round(review_bbox["bottom_right_x"] * scale_x),
                        round(review_bbox["bottom_right_y"] * scale_y),
                    )
                    draw.rectangle(box, outline=colour, width=3)
                    label = str(group.get("group_id") or "")
                    label_box = (box[0], max(0, box[1] - 13), box[0] + max(46, len(label) * 6), box[1])
                    draw.rectangle(label_box, fill=colour)
                    draw.text((box[0] + 2, max(0, box[1] - 12)), label, fill="white")
                    overlay_audit.append({
                        "group_id": str(group.get("group_id") or ""),
                        "source_bbox": bbox,
                        "review_bbox": review_bbox,
                        "overlay_bbox": {
                            "top_left_x": box[0], "top_left_y": box[1],
                            "bottom_right_x": box[2], "bottom_right_y": box[3],
                        },
                    })
                output = BytesIO()
                page.save(output, format="JPEG", quality=70)
        except Exception as exc:
            audit.append({"page_number": page_number, "reason": f"review context unavailable: {type(exc).__name__}"})
            continue
        contexts.append({"page_number": page_number, "bytes": output.getvalue()})
        audit.append({
            "page_number": page_number,
            "coordinate_frame": "fusion_to_review",
            "overlays": overlay_audit,
        })
    return contexts, audit


def format_detection_v5_membership_handoff(
    *,
    visual_groups: list[dict[str, Any]],
    source_facts: list[dict[str, Any]],
    max_facts_per_view: int = 6,
    max_fact_characters: int = 120,
) -> str:
    """Make a compact, View-local membership handoff without page-wide OCR."""
    context_by_page: dict[int, list[str]] = {}
    object_lines: list[str] = []
    for group in visual_groups:
        group_id = str(group.get("group_id") or "")
        try:
            page_number = int(group.get("page_number"))
        except (TypeError, ValueError):
            continue
        bbox = _detection_bbox(group.get("bbox"))
        if not group_id or bbox is None:
            continue
        description = " ".join(str(group.get("visual_description") or "").split())[:240]
        kind = str(group.get("representation_kind") or "")[:80]
        if group.get("evidence_class") == "document_context":
            context_by_page.setdefault(page_number, []).append(
                f"{group_id}|{kind}|{description}"
            )
            continue
        local_facts: list[str] = []
        for fact in source_facts:
            if fact.get("page_number") != page_number:
                continue
            fact_bbox = _detection_bbox(fact.get("bbox"))
            directly_assigned = str(fact.get("visual_group_id") or "") == group_id
            if fact_bbox is None or (
                not directly_assigned
                and not _detection_bbox_centre_inside(fact_bbox, bbox)
            ):
                continue
            # A source span substantially larger than the View is page scope,
            # never local proof for this membership decision.
            if (
                not directly_assigned
                and _detection_bbox_area(fact_bbox) > _detection_bbox_area(bbox) * 2
            ):
                continue
            fact_id = str(fact.get("fact_id") or "")
            text = " ".join(str(fact.get("text") or "").split())[:max_fact_characters]
            if fact_id and text:
                local_facts.append(
                    f"[{fact_id}] {json.dumps(text, ensure_ascii=False)}"
                )
            if len(local_facts) >= max_facts_per_view:
                break
        object_lines.append(
            f"{group_id}|P{page_number}|K={kind}|D={description}|"
            f"SRC=registry_view:{group_id}{';' + ';'.join(local_facts) if local_facts else ''}"
        )
    context_lines = [
        f"P{page_number}|{' || '.join(entries)}"
        for page_number, entries in sorted(context_by_page.items())
    ]
    return "\n".join([
        "FIXED OBJECT VIEW INVENTORY (IDs are immutable):",
        *object_lines,
        "DOCUMENT CONTEXT MAP (orientation only, never identity evidence):",
        *(context_lines or ["none"]),
    ])


def format_detection_v5_review_handoff(
    *,
    visual_groups: list[dict[str, Any]],
    source_facts: list[dict[str, Any]],
    draft_hypotheses: object,
) -> str:
    """Give review the locked Views and untrusted first-pass group sets."""
    lines = [format_detection_v5_membership_handoff(
        visual_groups=visual_groups, source_facts=source_facts,
    )]
    proposal_lines: list[str] = []
    if isinstance(draft_hypotheses, list):
        for index, hypothesis in enumerate(draft_hypotheses, start=1):
            group_ids = hypothesis.get("group_ids") if isinstance(hypothesis, dict) else None
            if isinstance(group_ids, list) and len(group_ids) >= 2:
                proposal_lines.append(f"H{index:03d}|{'|'.join(str(group_id) for group_id in group_ids)}")
    lines.extend([
        "UNTRUSTED DRAFT MULTI-VIEW PROPOSALS (review, do not copy blindly):",
        *(proposal_lines or ["none"]),
    ])
    return "\n".join(lines)


def build_detection_v5_membership_content_blocks(
    *,
    user_text: str,
    view_crops: list[dict[str, Any]],
    page_context_images: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for page in page_context_images:
        blocks.append({
            "type": "text",
            "text": (
                f"PDF page {page['page_number']} full-page context. "
                "It orients fixed View relationships only."
            ),
        })
        blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": base64.standard_b64encode(page["bytes"]).decode("ascii"),
            },
        })
    for crop in view_crops:
        blocks.append({
            "type": "text",
            "text": f"Object View {crop['group_id']}, PDF page {crop['page_number']}",
        })
        blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": base64.standard_b64encode(crop["bytes"]).decode("ascii"),
            },
        })
    blocks.append({"type": "text", "text": user_text})
    return blocks


def build_detection_v5_registry_visual_sources(
    visual_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Expose each fixed Object View as a traceable semantic source."""
    sources: list[dict[str, Any]] = []
    for group in visual_groups:
        if group.get("evidence_class") != "object_evidence":
            continue
        group_id = str(group.get("group_id") or "")
        bbox = _detection_bbox(group.get("bbox"))
        try:
            page_number = int(group.get("page_number"))
        except (TypeError, ValueError):
            continue
        if not group_id or bbox is None:
            continue
        sources.append({
            "fact_id": f"registry_view:{group_id}",
            "page_number": page_number,
            "bbox": bbox,
            "text": " ".join(str(group.get("visual_description") or "").split()),
            "source": "registry_membership_crop",
        })
    return sources


def summarize_detection_provider_call(
    *,
    response: Any,
    diagnostics: dict[str, Any],
    prompt_characters: int,
    context_characters: int,
    image_count: int,
    image_bytes: int,
) -> dict[str, Any]:
    """Keep each V5.8 Registry call independently measurable."""
    usage = getattr(response, "usage", None)
    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    costs = calculate_llm_cost_usd(
        model=str(getattr(response, "model", "") or DEFAULT_CLAUDE_DETECTION_MODEL),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    started = str(diagnostics.get("request_started_at") or "")
    finished = str(diagnostics.get("request_finished_at") or "")
    duration_seconds: float | None = None
    try:
        duration_seconds = round(
            max(0.0, (datetime.fromisoformat(finished) - datetime.fromisoformat(started)).total_seconds()),
            3,
        )
    except ValueError:
        pass
    return {
        "model": str(getattr(response, "model", "") or ""),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": costs["input_cost_usd"],
        "output_cost_usd": costs["output_cost_usd"],
        "total_cost_usd": costs["total_cost_usd"],
        "duration_seconds": duration_seconds,
        "prompt_characters": prompt_characters,
        "context_characters": context_characters,
        "image_count": image_count,
        "image_bytes": image_bytes,
    }

def append_detection_focus_regions(blocks: list[dict[str, Any]], regions: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not regions:
        return blocks
    user_text = blocks.pop()["text"]
    for region in regions:
        blocks.append({"type":"text", "text":f"Enlarged drawing region, PDF page {region['page_number']}: {region['region']}"})
        blocks.append({"type":"image", "source":{"type":"base64","media_type":"image/jpeg","data":base64.standard_b64encode(region["bytes"]).decode("ascii")}})
    blocks.append({"type":"text", "text":user_text})
    return blocks

def run_anthropic_detection_visual_map_agent(*, file_name: str, company_id: str, file_bytes: bytes, page_images: list[bytes], regions: list[dict[str, Any]], ocr_package: dict[str, Any] | None, model: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    selected_model = model or get_secret("CLAUDE_DETECTION_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL)
    prompt = load_detection_visual_map_prompt()
    user_text = build_detection_user_text(file_name=file_name, company_id=company_id, ocr_package=ocr_package)
    schema = strip_schema_for_claude(DETECTION_VISUAL_MAP_JSON_SCHEMA)
    content = build_detection_registry_content_blocks(
        file_name=file_name, file_bytes=file_bytes, user_text=user_text,
        page_images=page_images, regions=regions,
    )

    def request_visual_map(max_tokens: int) -> tuple[Any, dict[str, Any]]:
        return create_claude_message_streamed(
            get_anthropic_client(), model=selected_model, max_tokens=max_tokens,
            system=build_detection_system_content(prompt=prompt),
            messages=[{"role": "user", "content": content}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )

    response, diagnostics = request_visual_map(5000)
    try:
        payload = json.loads(extract_text_from_claude_response(response))
    except json.JSONDecodeError:
        # A truncated structured response is transport failure, not a visual
        # interpretation. Retry once with the provider's full response budget.
        response, diagnostics = request_visual_map(8192)
        diagnostics["retry_after_truncated_json"] = True
        try:
            payload = json.loads(extract_text_from_claude_response(response))
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Detection visual-map response remained invalid JSON after retry: "
                f"{exc}"
            ) from exc
    try:
        visual_map = validate_detection_visual_map(
            normalize_detection_visual_map_group_ids(payload)
        )
    except ValueError as exc:
        raise RuntimeError(f"Detection visual-map response failed validation: {exc}") from exc
    diagnostics.update({"visual_group_count": len(visual_map["visual_groups"]), "region_count": len(regions), "page_count": len(page_images), "attempt_label": "visual_map_regions"})
    usage = build_agent_usage_event(agent_name="detection",operation="rfq_detection_visual_map",company_id=company_id,run_id=None,file_name=file_name,object_id=None,object_name=None,model=selected_model,prompt_version=DETECTION_VISUAL_MAP_PROMPT_VERSION,response=response,started_at=diagnostics["request_started_at"],finished_at=diagnostics["request_finished_at"],request_diagnostics=diagnostics)
    return visual_map, usage


def _apply_page_coverage_to_registry(
    objects: list[dict[str, Any]], page_coverage: object, *, page_count: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Make Evidence completeness an explicit, auditable page-level contract.

    The model accounts for every uploaded physical page once.  Evidence pages
    are derived from that account rather than being a separate, lossy list
    optimised for material calculations.
    """
    if (
        not isinstance(objects, list)
        or not all(isinstance(item, dict) for item in objects)
        or not isinstance(page_coverage, list)
    ):
        raise ValueError("page coverage and objects must be lists")
    object_ids = {str(item.get("object_id") or "") for item in objects}
    coverage_by_page: dict[int, list[str]] = {}
    for entry in page_coverage:
        if not isinstance(entry, dict) or set(entry) != {
            "page_number", "object_ids", "evidence_reason",
        }:
            raise ValueError("page coverage fields do not match contract")
        page_number = entry["page_number"]
        covered_ids = entry["object_ids"]
        if (
            not isinstance(page_number, int)
            or not 1 <= page_number <= page_count
            or page_number in coverage_by_page
            or not isinstance(covered_ids, list)
            or len(covered_ids) != len(set(covered_ids))
            or not all(isinstance(object_id, str) and object_id in object_ids for object_id in covered_ids)
            or not isinstance(entry["evidence_reason"], str)
            or not entry["evidence_reason"].strip()
        ):
            raise ValueError("page coverage is invalid")
        coverage_by_page[page_number] = covered_ids
    if set(coverage_by_page) != set(range(1, page_count + 1)):
        raise ValueError("page coverage must account for every uploaded page exactly once")
    reconciled_object_ids: list[str] = []
    if page_count == 1:
        # Every Registry object in a one-page upload has necessarily been
        # evidenced on that only physical page. This repairs a lossy coverage
        # enumeration, not the model's commercial-object decision.
        covered_ids = coverage_by_page[1]
        for item in objects:
            object_id = str(item.get("object_id") or "")
            if object_id and object_id not in covered_ids:
                covered_ids.append(object_id)
                reconciled_object_ids.append(object_id)
    # Descriptive metadata cannot make an identity page disappear from the
    # handoff. Add it to Evidence rather than rejecting an otherwise complete
    # graph because the model forgot to repeat the same page in coverage.
    for item in objects:
        object_id = str(item.get("object_id") or "")
        for page_number in item.get("identity_pages") or []:
            if object_id and object_id not in coverage_by_page[page_number]:
                coverage_by_page[page_number].append(object_id)
                if object_id not in reconciled_object_ids:
                    reconciled_object_ids.append(object_id)
    enriched = copy.deepcopy(objects)
    for item in enriched:
        object_id = str(item["object_id"])
        item["estimation_evidence_pages"] = [
            page_number
            for page_number in range(1, page_count + 1)
            if object_id in coverage_by_page[page_number]
        ]
    return enriched, reconciled_object_ids


def _normalize_component_anchor_group_ids(
    payload: dict[str, Any], group_id_mapping: dict[str, str],
) -> dict[str, Any]:
    """Normalize provider-facing component anchors to canonical view IDs."""
    normalized = copy.deepcopy(payload)
    objects = normalized.get("objects")
    if isinstance(objects, list):
        for item in objects:
            if isinstance(item, dict):
                raw_group_id = str(item.get("component_anchor_group_id") or "")
                item["component_anchor_group_id"] = group_id_mapping.get(
                    raw_group_id, raw_group_id
                )
    relation_edges = normalized.get("relation_edges")
    if isinstance(relation_edges, list):
        for edge in relation_edges:
            if not isinstance(edge, dict):
                continue
            for field in ("group_id_a", "group_id_b"):
                raw_group_id = str(edge.get(field) or "")
                edge[field] = group_id_mapping.get(raw_group_id, raw_group_id)
            if str(edge.get("group_id_a") or "") > str(edge.get("group_id_b") or ""):
                edge["group_id_a"], edge["group_id_b"] = (
                    edge["group_id_b"], edge["group_id_a"],
                )
    page_coverage = normalized.get("page_coverage")
    if isinstance(page_coverage, list):
        for entry in page_coverage:
            if not isinstance(entry, dict) or not isinstance(
                entry.get("component_anchor_group_ids"), list
            ):
                continue
            entry["component_anchor_group_ids"] = [
                group_id_mapping.get(str(group_id), str(group_id))
                for group_id in entry["component_anchor_group_ids"]
            ]
    return normalized


def _derive_registry_from_proof_components(
    objects: object,
    components: list[list[str]],
    *,
    page_number_by_group_id: dict[str, int],
    page_count: int,
    source_labels_by_component_anchor: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, str], list[str], dict[str, Any]]:
    """Derive packages from graph components and overlay valid model metadata.

    The proof graph is the sole boundary authority.  ``objects`` can enrich a
    proven component with a source label and quantity, but it cannot create,
    remove, or invalidate a package.  This prevents a missing duplicate
    descriptor from turning a usable Detection result into a failed upload.
    """
    required = {
        "component_anchor_group_id", "transport_label", "quantity",
        "quantity_explicit", "identity_pages", "visual_identity", "boundary_basis",
    }
    component_anchor_by_group_id = {
        group_id: component[0]
        for component in components
        for group_id in component
    }
    objects_by_component_anchor: dict[str, dict[str, Any]] = {}
    discarded_metadata_rows: list[dict[str, str]] = []
    if not isinstance(objects, list):
        discarded_metadata_rows.append({
            "declared_anchor_group_id": "",
            "reason": "objects metadata is not an array",
        })
        objects = []
    for item in objects:
        if not isinstance(item, dict) or set(item) != required:
            discarded_metadata_rows.append({
                "declared_anchor_group_id": "",
                "reason": "objects metadata fields do not match contract",
            })
            continue
        declared_anchor = str(item.get("component_anchor_group_id") or "")
        component_anchor = component_anchor_by_group_id.get(declared_anchor)
        if not component_anchor:
            discarded_metadata_rows.append({
                "declared_anchor_group_id": declared_anchor,
                "reason": "metadata anchor is not a proven component group",
            })
            continue
        if component_anchor in objects_by_component_anchor:
            discarded_metadata_rows.append({
                "declared_anchor_group_id": declared_anchor,
                "reason": "duplicate metadata for proven component",
            })
            continue
        quantity = item.get("quantity")
        identity_pages = item.get("identity_pages")
        if (
            not str(item.get("transport_label") or "").strip()
            or not isinstance(quantity, (int, float))
            or not math.isfinite(float(quantity))
            or quantity < 1
            or not isinstance(item.get("quantity_explicit"), bool)
            or not isinstance(identity_pages, list)
            or not identity_pages
            or not all(
                isinstance(page, int) and 1 <= page <= page_count
                for page in identity_pages
            )
            or not str(item.get("visual_identity") or "").strip()
            or not str(item.get("boundary_basis") or "").strip()
        ):
            discarded_metadata_rows.append({
                "declared_anchor_group_id": declared_anchor,
                "reason": "metadata values are incomplete or invalid",
            })
            continue
        objects_by_component_anchor[component_anchor] = item

    registry_objects: list[dict[str, Any]] = []
    anchor_to_object_id: dict[str, str] = {}
    fallback_object_ids: list[str] = []
    fallback_component_anchor_group_ids: list[str] = []
    source_labels_by_component_anchor = source_labels_by_component_anchor or {}
    for index, component in enumerate(components, start=1):
        component_anchor = component[0]
        object_id = f"object-{index:03d}"
        source = objects_by_component_anchor.get(component_anchor)
        if source is None:
            fallback_object_ids.append(object_id)
            fallback_component_anchor_group_ids.append(component_anchor)
            source_label = source_labels_by_component_anchor.get(
                component_anchor, "Unlabelled",
            )
            source = {
                "transport_label": source_label,
                "quantity": 1,
                "quantity_explicit": False,
                "identity_pages": sorted({
                    page_number_by_group_id[group_id]
                    for group_id in component
                    if group_id in page_number_by_group_id
                }),
                "visual_identity": (
                    "Proven graph component without complete descriptive metadata"
                ),
                "boundary_basis": (
                    "Package membership derives only from accepted graph proof; "
                    "descriptive metadata is incomplete and requires review."
                ),
            }
        registry_objects.append({
            "object_id": object_id,
            "transport_label": source["transport_label"],
            "quantity": source["quantity"],
            "quantity_explicit": source["quantity_explicit"],
            "identity_pages": copy.deepcopy(source["identity_pages"]),
            "visual_group_ids": component,
            "visual_identity": source["visual_identity"],
            "boundary_basis": source["boundary_basis"],
        })
        for group_id in component:
            anchor_to_object_id[group_id] = object_id
    return registry_objects, anchor_to_object_id, fallback_object_ids, {
        "accepted_component_anchor_group_ids": sorted(objects_by_component_anchor),
        "fallback_component_anchor_group_ids": fallback_component_anchor_group_ids,
        "source_labels_by_component_anchor": source_labels_by_component_anchor,
        "discarded_metadata_rows": discarded_metadata_rows,
    }


_SOURCE_OBJECT_CODE_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё0-9])(?:[A-Za-zА-Яа-яЁё]{1,4}\s*[- ]?\s*\d+[A-Za-zА-Яа-яЁё]*(?:[-./][A-Za-zА-Яа-яЁё0-9]+){0,3}|\d{1,3}[A-ZА-ЯЁ][A-ZА-ЯЁ0-9]*(?:[-./][A-Za-zА-Яа-яЁё0-9]+){0,3})(?![A-Za-zА-Яа-яЁё0-9])"
)

_DRAWING_NAME_MARKER_RE = re.compile(
    r"(?:DRAWING\s*NAME|שם\s*התכנית)", re.IGNORECASE,
)


def _canonical_source_object_code(value: str) -> str:
    return re.sub(r"\s+", "", value).upper()


def extract_detection_page_drawing_codes(
    ocr_package: dict[str, Any] | None,
) -> dict[int, str]:
    """Extract one literal DRAWING NAME code from each OCR title block.

    These are source-root facts, not visual islands and not Estimation Evidence.
    The extractor deliberately reads only title-block tables with an explicit
    DRAWING NAME field, never arbitrary component labels such as VEN-01.
    """
    if not isinstance(ocr_package, dict):
        return {}
    page_codes: dict[int, str] = {}
    for page in ocr_package.get("pages") or []:
        if not isinstance(page, dict):
            continue
        page_number = page.get("page_number")
        if not isinstance(page_number, int) or page_number < 1:
            continue
        candidates: list[str] = []
        for block in page.get("blocks") or []:
            if not isinstance(block, dict) or block.get("type") != "table":
                continue
            content = html.unescape(str(block.get("content") or ""))
            text = re.sub(r"<[^>]+>", " ", content)
            for marker in _DRAWING_NAME_MARKER_RE.finditer(text):
                fragment = text[marker.end():marker.end() + 280]
                for match in _SOURCE_OBJECT_CODE_RE.finditer(fragment):
                    candidates.append(_canonical_source_object_code(match.group(0)))
        unique = list(dict.fromkeys(candidates))
        if len(unique) == 1:
            page_codes[page_number] = unique[0]
    return page_codes


def _component_source_labels_from_page_codes(
    components: list[list[str]],
    *,
    page_number_by_group_id: dict[str, int],
    page_drawing_codes: dict[int, str],
) -> dict[str, str]:
    """Use a unique page-level drawing code as fallback package label."""
    labels: dict[str, str] = {}
    for component in components:
        codes = {
            page_drawing_codes[page_number_by_group_id[group_id]]
            for group_id in component
            if group_id in page_number_by_group_id
            and page_number_by_group_id[group_id] in page_drawing_codes
        }
        if len(codes) == 1:
            labels[component[0]] = next(iter(codes))
    return labels


def _apply_reference_root_suffixes(
    registry_objects: list[dict[str, Any]],
    *,
    proof_components: list[list[str]],
    reference_links: list[dict[str, Any]],
    shared_reference_group_ids: set[str],
) -> list[dict[str, Any]]:
    """Preserve one authored root code while naming its split child packages."""
    object_id_by_group_id = {
        group_id: registry_objects[index]["object_id"]
        for index, component in enumerate(proof_components)
        for group_id in component
    }
    linked_object_ids = {
        object_id_by_group_id[other_group_id]
        for link in reference_links
        for group_id_a, group_id_b in [
            (str(link.get("group_id_a") or ""), str(link.get("group_id_b") or ""))
        ]
        for shared_group_id, other_group_id in (
            (group_id_a, group_id_b), (group_id_b, group_id_a)
        )
        if shared_group_id in shared_reference_group_ids
        and other_group_id in object_id_by_group_id
    }
    siblings_by_root: dict[str, list[dict[str, Any]]] = {}
    for item in registry_objects:
        if item["object_id"] not in linked_object_ids:
            continue
        candidates = {
            match.group(0).replace(" ", "").upper()
            for match in _SOURCE_OBJECT_CODE_RE.finditer(
                str(item.get("transport_label") or "")
            )
        }
        if len(candidates) == 1:
            siblings_by_root.setdefault(next(iter(candidates)), []).append(item)
    for root_code, siblings in siblings_by_root.items():
        if len(siblings) < 2 or len(siblings) > 26:
            continue
        for position, item in enumerate(siblings):
            item["transport_label"] = f"{root_code}{chr(ord('A') + position)}"
    return registry_objects


def _resolve_component_page_coverage(
    page_coverage: object,
    *,
    anchor_to_object_id: dict[str, str],
    page_number_by_group_id: dict[str, int],
    page_count: int,
    reference_links: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Resolve coverage while making complete Evidence independent of repetition.

    Model coverage remains useful enrichment, but page membership is already
    known from the accepted graph. A malformed or incomplete coverage row must
    not discard a commercial package. Every package keeps the pages of its own
    groups, and a reference link contributes the linked depiction's page to
    both related packages as shared Evidence.
    """
    resolved_by_page = {
        page_number: {
            "page_number": page_number,
            "object_ids": [],
            "evidence_reason": "No retained object-specific Evidence on this page.",
        }
        for page_number in range(1, page_count + 1)
    }
    coverage_audit: list[dict[str, Any]] = []
    if not isinstance(page_coverage, list):
        coverage_audit.append({
            "row_index": None,
            "reason": "page coverage is not an array; graph-derived coverage applied",
        })
    else:
        seen_pages: set[int] = set()
        for row_index, entry in enumerate(page_coverage):
            if not isinstance(entry, dict) or set(entry) != {
                "page_number", "component_anchor_group_ids", "evidence_reason",
            }:
                coverage_audit.append({
                    "row_index": row_index,
                    "reason": "page coverage fields do not match contract",
                })
                continue
            page_number = entry.get("page_number")
            anchors = entry.get("component_anchor_group_ids")
            reason = str(entry.get("evidence_reason") or "").strip()
            if (
                not isinstance(page_number, int)
                or page_number not in resolved_by_page
                or page_number in seen_pages
                or not isinstance(anchors, list)
                or not reason
            ):
                coverage_audit.append({
                    "row_index": row_index,
                    "reason": "page coverage row is incomplete or duplicated",
                })
                continue
            seen_pages.add(page_number)
            retained_anchors = [
                anchor for anchor in anchors
                if isinstance(anchor, str) and anchor in anchor_to_object_id
            ]
            if len(retained_anchors) != len(set(retained_anchors)):
                retained_anchors = list(dict.fromkeys(retained_anchors))
                coverage_audit.append({
                    "row_index": row_index,
                    "reason": "duplicate or unknown coverage anchors were discarded",
                })
            entry_out = resolved_by_page[page_number]
            entry_out["object_ids"] = list(dict.fromkeys(
                anchor_to_object_id[anchor] for anchor in retained_anchors
            ))
            entry_out["evidence_reason"] = reason

    graph_page_coverage_supplements: list[dict[str, Any]] = []

    def add_object_page(
        *, page_number: int | None, object_id: str | None,
        source: str, visual_group_id: str,
    ) -> None:
        if page_number not in resolved_by_page or not object_id:
            return
        entry = resolved_by_page[page_number]
        if object_id not in entry["object_ids"]:
            entry["object_ids"].append(object_id)
            graph_page_coverage_supplements.append({
                "page_number": page_number,
                "object_id": object_id,
                "visual_group_id": visual_group_id,
                "source": source,
            })

    for group_id, object_id in anchor_to_object_id.items():
        add_object_page(
            page_number=page_number_by_group_id.get(group_id),
            object_id=object_id,
            source="component_group",
            visual_group_id=group_id,
        )
    for link in reference_links:
        group_id_a = str(link.get("group_id_a") or "")
        group_id_b = str(link.get("group_id_b") or "")
        object_id_a = anchor_to_object_id.get(group_id_a)
        object_id_b = anchor_to_object_id.get(group_id_b)
        if not object_id_a or not object_id_b or object_id_a == object_id_b:
            continue
        add_object_page(
            page_number=page_number_by_group_id.get(group_id_b),
            object_id=object_id_a,
            source="reference_link",
            visual_group_id=group_id_b,
        )
        add_object_page(
            page_number=page_number_by_group_id.get(group_id_a),
            object_id=object_id_b,
            source="reference_link",
            visual_group_id=group_id_a,
        )
    return (
        [resolved_by_page[page_number] for page_number in range(1, page_count + 1)],
        graph_page_coverage_supplements,
        coverage_audit,
    )


def _visual_map_from_registry_groups(groups: object) -> dict[str, Any]:
    """Drop Registry-only fields before validating the visual inventory."""
    required_visual_fields = (
        "group_id",
        "page_number",
        "location_hint",
        "visual_description",
        "representation_kind",
    )
    if not isinstance(groups, list):
        return {"visual_groups": groups}
    return {
        "visual_groups": [
            {field: group.get(field) for field in required_visual_fields}
            if isinstance(group, dict)
            else group
            for group in groups
        ]
    }


def _validate_and_apply_visual_registry_classifications(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate complete phase-two classifications, then attach them in code."""
    groups = payload.get("visual_groups")
    classifications = payload.get("classifications")
    if not isinstance(groups, list) or not isinstance(classifications, list):
        raise ValueError("visual registry classifications are invalid")
    raw_group_ids = [str(group.get("group_id") or "") for group in groups if isinstance(group, dict)]
    if len(raw_group_ids) != len(groups) or len(raw_group_ids) != len(set(raw_group_ids)):
        raise ValueError("visual registry classifications are invalid")
    expected = set(raw_group_ids)
    by_group_id: dict[str, dict[str, Any]] = {}
    for item in classifications:
        if (
            not isinstance(item, dict)
            or set(item) != {"group_id", "evidence_class", "classification_reason"}
            or not isinstance(item.get("group_id"), str)
            or item["group_id"] not in expected
            or item["group_id"] in by_group_id
            or item.get("evidence_class") not in {"object_evidence", "document_context"}
            or not str(item.get("classification_reason") or "").strip()
        ):
            raise ValueError("visual registry classifications are invalid")
        by_group_id[item["group_id"]] = item
    if set(by_group_id) != expected:
        raise ValueError("visual registry must classify every visual group exactly once")
    enriched = copy.deepcopy(payload)
    # A whole-level architectural plan is document navigation, not an object
    # depiction.  This applies to any document and depends on the Registry's
    # own declared representation and description, never on a page number.
    generic_plan_markers = re.compile(
        r"\b(?:complete|overall|whole|level|rooms?|layouts?|spatial|"
        r"architectural|circulation|walls?|door\s+swings?|multiple\s+spaces?)\b",
        re.IGNORECASE,
    )
    for group in enriched["visual_groups"]:
        decision = by_group_id[group["group_id"]]
        representation = str(group.get("representation_kind") or "").lower()
        description = " ".join((
            str(group.get("visual_description") or ""),
            str(decision["classification_reason"]),
        ))
        # Registry occasionally emits its evidence-class name in
        # representation_kind.  A real whole-level floor plan must still be
        # context, so use the concrete description as a deterministic fallback.
        describes_floor_plan = bool(re.search(
            r"\b(?:architectural\s+)?(?:floor|level)\s+plan\b|\broom\s+layouts?\b",
            description,
            re.IGNORECASE,
        ))
        generic_plan = (
            representation in {"floor_plan", "location_plan"} or describes_floor_plan
        ) and len(set(generic_plan_markers.findall(description))) >= 3
        if decision["evidence_class"] == "object_evidence" and generic_plan:
            group["evidence_class"] = "document_context"
            group["classification_reason"] = (
                "Whole-level architectural plan is document context, not an isolated fabricated item."
            )
        else:
            group["evidence_class"] = decision["evidence_class"]
            group["classification_reason"] = decision["classification_reason"]
    audit = [
        {"group_id": group["group_id"], "page_number": group["page_number"],
         "representation_kind": group["representation_kind"],
         "evidence_class": group["evidence_class"],
         "classification_reason": group["classification_reason"]}
        for group in enriched["visual_groups"]
    ]
    return enriched, audit


def validate_detection_v5_source_degraded_role_resolutions(
    resolutions: object,
    *,
    visual_groups: list[dict[str, Any]],
    source_facts: list[dict[str, Any]],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Validate Review's one-time role reconciliation before graph creation."""
    represented_groups = {
        str(group.get("group_id") or ""): group
        for group in visual_groups
    }
    if not represented_groups or not isinstance(resolutions, list):
        raise ValueError("source-degraded role resolutions are invalid")
    source_ids = {
        str(fact.get("fact_id") or "") for fact in source_facts
        if isinstance(fact, dict)
    }
    by_group_id: dict[str, dict[str, Any]] = {}
    for item in resolutions:
        if (
            not isinstance(item, dict)
            or set(item) != {
                "group_id", "visual_role", "parent_group_id", "observation", "source_fact_ids",
            }
            or not isinstance(item.get("group_id"), str)
            or item["group_id"] not in represented_groups
            or item["group_id"] in by_group_id
            or item.get("visual_role") not in {
                "assembly_view", "component_detail", "document_context",
            }
            or not isinstance(item.get("parent_group_id"), str)
            or len(str(item.get("observation") or "").strip()) < 30
            or not isinstance(item.get("source_fact_ids"), list)
        ):
            raise ValueError("source-degraded role resolutions are invalid")
        cited_ids = [str(value) for value in item["source_fact_ids"] if str(value).strip()]
        if not cited_ids or any(value not in source_ids for value in cited_ids):
            raise ValueError("source-degraded role resolution has unknown source")
        own_source = f"registry_view:{item['group_id']}"
        if own_source not in cited_ids:
            raise ValueError("source-degraded role resolution must cite its representation")
        by_group_id[item["group_id"]] = copy.deepcopy(item)
    if set(by_group_id) != set(represented_groups):
        raise ValueError("source-degraded Review must resolve every representation")

    roles = {
        group_id: str(resolution["visual_role"])
        for group_id, resolution in by_group_id.items()
    }
    audit: list[dict[str, Any]] = []
    for group_id, resolution in sorted(by_group_id.items()):
        role = roles[group_id]
        parent_group_id = str(resolution["parent_group_id"] or "")
        if role in {"assembly_view", "document_context"}:
            if parent_group_id:
                raise ValueError("source-degraded assembly/context role cannot have a parent")
        else:
            parent = represented_groups.get(parent_group_id)
            if (
                parent is None
                or parent_group_id == group_id
                or roles.get(parent_group_id) != "assembly_view"
                or parent.get("page_number") != represented_groups[group_id].get("page_number")
            ):
                raise ValueError("source-degraded component_detail needs one same-page assembly parent")
            parent_source = f"registry_view:{parent_group_id}"
            if parent_source not in resolution["source_fact_ids"]:
                # The explicit parent ID is already the model's relation claim.
                # Add the matching visual source deterministically so an omitted
                # redundant token does not turn a recoverable review into a
                # user-visible failure.
                resolution["source_fact_ids"].append(parent_source)
        audit.append({
            "group_id": group_id,
            "final_visual_role": role,
            "parent_group_id": parent_group_id or None,
            "observation": resolution["observation"],
            "source_fact_ids": list(resolution["source_fact_ids"]),
        })
    if not any(role == "assembly_view" for role in roles.values()):
        raise ValueError("source-degraded Review found no assembly view")
    return roles, audit


def _normalize_source_degraded_registry_view_ids(
    source_fact_ids: object,
    *,
    group_id_mapping: dict[str, str],
) -> list[str]:
    """Normalize a model's exact View shorthand into its visual source ID."""
    if not isinstance(source_fact_ids, list):
        return []
    result: list[str] = []
    for value in source_fact_ids:
        source_id = str(value or "").strip()
        if not source_id:
            continue
        if source_id.startswith("registry_view:"):
            group_id = source_id.removeprefix("registry_view:")
            result.append(f"registry_view:{group_id_mapping.get(group_id, group_id)}")
        elif source_id in group_id_mapping:
            result.append(f"registry_view:{group_id_mapping[source_id]}")
        else:
            result.append(source_id)
    return result


def validate_detection_v5_source_degraded_full_page_roles(
    roles: object,
    *,
    visual_groups: list[dict[str, Any]],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Validate a complete V4-style representation-role decision."""
    expected = {
        str(group.get("group_id") or "") for group in visual_groups
        if isinstance(group, dict) and str(group.get("group_id") or "")
    }
    if not expected or not isinstance(roles, list):
        raise ValueError("source-degraded full-page roles are invalid")
    by_group_id: dict[str, dict[str, Any]] = {}
    allowed_roles = {"assembly_view", "component_detail", "document_context"}
    for role in roles:
        if (
            not isinstance(role, dict)
            or set(role) != {"group_id", "visual_role", "classification_reason"}
            or not isinstance(role.get("group_id"), str)
            or role["group_id"] not in expected
            or role["group_id"] in by_group_id
            or role.get("visual_role") not in allowed_roles
            or len(str(role.get("classification_reason") or "").strip()) < 12
        ):
            raise ValueError("source-degraded full-page roles are invalid")
        by_group_id[role["group_id"]] = copy.deepcopy(role)
    if set(by_group_id) != expected:
        raise ValueError("source-degraded full-page Registry must role-classify every representation")
    return (
        {group_id: str(role["visual_role"]) for group_id, role in by_group_id.items()},
        [
            {
                "group_id": group_id,
                "visual_role": role["visual_role"],
                "classification_reason": role["classification_reason"],
            }
            for group_id, role in sorted(by_group_id.items())
        ],
    )


def validate_detection_v5_discovery_page_coverage(
    coverage: object,
    *,
    visual_groups: object,
    page_count: int,
) -> list[dict[str, Any]]:
    """Require an explicit Island-discovery decision for every supplied page."""
    if not isinstance(coverage, list) or not isinstance(visual_groups, list):
        raise ValueError("proposal page coverage is invalid")
    groups_by_id: dict[str, dict[str, Any]] = {}
    for group in visual_groups:
        if not isinstance(group, dict):
            raise ValueError("proposal visual group is invalid")
        group_id = str(group.get("group_id") or "")
        if not group_id or group_id in groups_by_id:
            raise ValueError("proposal visual group IDs are invalid")
        groups_by_id[group_id] = group

    expected_pages = set(range(1, page_count + 1))
    coverage_by_page: dict[int, dict[str, Any]] = {}
    covered_ids: set[str] = set()
    audit: list[dict[str, Any]] = []
    for item in coverage:
        if not isinstance(item, dict) or set(item) != {"page_number", "visual_group_ids"}:
            raise ValueError("proposal page coverage entry is invalid")
        page_number = item.get("page_number")
        if not isinstance(page_number, int) or page_number not in expected_pages:
            raise ValueError("proposal page coverage has an invalid page")
        if page_number in coverage_by_page:
            raise ValueError("proposal page coverage duplicates a page")
        group_ids = item.get("visual_group_ids")
        if not isinstance(group_ids, list) or len(group_ids) != len(set(group_ids)):
            raise ValueError("proposal page coverage group IDs are invalid")
        normalized_ids = [str(group_id) for group_id in group_ids]
        for group_id in normalized_ids:
            group = groups_by_id.get(group_id)
            if group is None or int(group.get("page_number") or 0) != page_number:
                raise ValueError("proposal page coverage references the wrong island")
            if group_id in covered_ids:
                raise ValueError("proposal page coverage duplicates an island")
            covered_ids.add(group_id)
        coverage_by_page[page_number] = item
        audit.append({
            "page_number": page_number,
            "visual_group_ids": normalized_ids,
        })
    if set(coverage_by_page) != expected_pages:
        raise ValueError("proposal page coverage omits a supplied page")
    if covered_ids != set(groups_by_id):
        raise ValueError("proposal page coverage omits or invents an island")
    return sorted(audit, key=lambda item: item["page_number"])


def _normalize_registry_group_bboxes(
    groups: object,
    *,
    group_id_mapping: dict[str, str],
) -> dict[str, dict[str, int]]:
    """Validate Registry's island geometry in the rendered-page pixel frame."""
    if not isinstance(groups, list):
        raise ValueError("visual registry group geometry is invalid")
    result: dict[str, dict[str, int]] = {}
    keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError("visual registry group geometry is invalid")
        group_id = group_id_mapping.get(str(group.get("group_id") or ""), "")
        bbox = group.get("bbox")
        if (
            not group_id or group_id in result or not isinstance(bbox, dict)
            or set(bbox) != set(keys)
            or not all(isinstance(bbox[key], int) for key in keys)
            or bbox["top_left_x"] < 0 or bbox["top_left_y"] < 0
            or bbox["bottom_right_x"] <= bbox["top_left_x"]
            or bbox["bottom_right_y"] <= bbox["top_left_y"]
        ):
            raise ValueError("visual registry group geometry is invalid")
        result[group_id] = {key: int(bbox[key]) for key in keys}
    return result


def _normalize_registry_group_core_bboxes(
    groups: object,
    *,
    group_id_mapping: dict[str, str],
    evidence_envelopes: dict[str, dict[str, int]],
) -> dict[str, dict[str, int]]:
    """Validate physical Island cores inside their Registry evidence envelopes."""
    if not isinstance(groups, list):
        raise ValueError("visual registry group core geometry is invalid")
    result: dict[str, dict[str, int]] = {}
    keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError("visual registry group core geometry is invalid")
        group_id = group_id_mapping.get(str(group.get("group_id") or ""), "")
        bbox = group.get("core_bbox")
        envelope = evidence_envelopes.get(group_id) or {}
        if (
            not group_id or group_id in result or not isinstance(bbox, dict)
            or set(bbox) != set(keys)
            or not all(isinstance(bbox[key], int) for key in keys)
            or bbox["top_left_x"] < envelope.get("top_left_x", 1)
            or bbox["top_left_y"] < envelope.get("top_left_y", 1)
            or bbox["bottom_right_x"] > envelope.get("bottom_right_x", -1)
            or bbox["bottom_right_y"] > envelope.get("bottom_right_y", -1)
            or bbox["bottom_right_x"] <= bbox["top_left_x"]
            or bbox["bottom_right_y"] <= bbox["top_left_y"]
        ):
            raise ValueError("visual registry group core geometry is invalid")
        result[group_id] = {key: int(bbox[key]) for key in keys}
    return result


def _bbox_overlaps(left: dict[str, int], right: dict[str, int]) -> bool:
    return not (
        left["bottom_right_x"] < right["top_left_x"]
        or right["bottom_right_x"] < left["top_left_x"]
        or left["bottom_right_y"] < right["top_left_y"]
        or right["bottom_right_y"] < left["top_left_y"]
    )


def build_detection_candidate_region_audit(
    *,
    candidate_regions: list[dict[str, Any]],
    candidate_region_exceptions: object,
    visual_groups: list[dict[str, Any]],
    group_bboxes: dict[str, dict[str, int]],
    group_id_mapping: dict[str, str],
) -> list[dict[str, Any]]:
    """Account for Fusion recall candidates without making them Islands."""
    if not isinstance(candidate_region_exceptions, list):
        raise ValueError("candidate region exceptions are invalid")
    candidate_ids = {
        str(candidate["candidate_region_id"])
        for candidate in candidate_regions
    }
    exceptions: dict[str, str] = {}
    for row in candidate_region_exceptions:
        if (
            not isinstance(row, dict)
            or set(row) != {"candidate_region_id", "reason"}
            or not isinstance(row.get("candidate_region_id"), str)
            or row["candidate_region_id"] not in candidate_ids
            or row["candidate_region_id"] in exceptions
            or not str(row.get("reason") or "").strip()
        ):
            raise ValueError("candidate region exceptions are invalid")
        exceptions[row["candidate_region_id"]] = str(row["reason"]).strip()
    page_by_group_id = {
        group_id_mapping[str(group.get("group_id") or "")]: group.get("page_number")
        for group in visual_groups if isinstance(group, dict)
    }
    audit: list[dict[str, Any]] = []
    for candidate in candidate_regions:
        candidate_id = str(candidate["candidate_region_id"])
        covered_group_ids = sorted(
            group_id for group_id, bbox in group_bboxes.items()
            if (
                page_by_group_id.get(group_id) == candidate["page_number"]
                and _bbox_overlaps(candidate["bbox"], bbox)
            )
        )
        exception_reason = exceptions.get(candidate_id)
        audit.append({
            **copy.deepcopy(candidate),
            "covered_group_ids": covered_group_ids,
            "exception_reason": exception_reason,
            "status": (
                "covered_by_island" if covered_group_ids
                else "explained_non_island" if exception_reason
                else "unexplained"
            ),
        })
    return audit


def map_detection_candidate_q_pairs_to_islands(
    candidate_pairs: list[dict[str, Any]],
    *,
    candidate_regions: list[dict[str, Any]],
    group_bboxes: dict[str, dict[str, int]],
    page_by_group_id: dict[str, int],
    include_audit: bool = False,
) -> set[tuple[str, str]] | tuple[set[tuple[str, str]], list[dict[str, Any]]]:
    """Map pre-Registry Q endpoints onto the retained final Island IDs.

    Q is created from Fusion regions before Registry sees the page.  Registry
    may tighten or split those regions, so a queue pair maps to every
    same-page final-Island pair whose bounds overlap its two endpoints.  This
    is a boundary translation, never a new candidate search.
    """
    candidate_by_id = {
        str(row.get("candidate_region_id") or ""): row
        for row in candidate_regions if isinstance(row, dict)
    }

    def mapped_groups(candidate_id: str) -> set[str]:
        candidate = candidate_by_id.get(candidate_id) or {}
        bbox = candidate.get("bbox") or {}
        page_number = candidate.get("page_number")
        if not isinstance(bbox, dict) or not isinstance(page_number, int):
            return set()
        return {
            group_id for group_id, group_bbox in group_bboxes.items()
            if page_by_group_id.get(group_id) == page_number
            and _bbox_overlaps(bbox, group_bbox)
        }

    allowed: set[tuple[str, str]] = set()
    audit: list[dict[str, Any]] = []
    for row in candidate_pairs:
        if not isinstance(row, dict):
            continue
        left_candidate_id = str(row.get("group_id_a") or "")
        right_candidate_id = str(row.get("group_id_b") or "")
        left = mapped_groups(left_candidate_id)
        right = mapped_groups(right_candidate_id)
        mapped_pairs = {
            tuple(sorted((left_id, right_id)))
            for left_id in left for right_id in right if left_id != right_id
        }
        audit.append({
            "candidate_group_id_a": left_candidate_id,
            "candidate_group_id_b": right_candidate_id,
            "mapped_group_ids_a": sorted(left),
            "mapped_group_ids_b": sorted(right),
            "mapped_final_pair_count": len(mapped_pairs),
            "mapped_final_pairs": [
                {"group_id_a": pair[0], "group_id_b": pair[1]}
                for pair in sorted(mapped_pairs)
            ],
        })
        allowed.update(mapped_pairs)
    if include_audit:
        return allowed, audit
    return allowed


_DIMENSION_HALO_TEXT_RE = re.compile(
    r"^\s*(?:[A-Za-z]+\s*=\s*)?(?P<value>\d+(?:[.,]\d+)?)\s*(?:mm|cm|m)?\s*$",
    re.IGNORECASE,
)
_DIMENSION_HALO_MIN_VALUE = Decimal("20")
_DIMENSION_HALO_MIN_PX = 80
_DIMENSION_HALO_MAX_PX = 180
_DIMENSION_HALO_SHORT_SIDE_RATIO = 0.12


def _detection_v5_dimension_halo(
    bbox: dict[str, Any],
) -> dict[str, float] | None:
    """Return the bounded whitespace that may hold an outer dimension."""
    keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
    if not all(isinstance(bbox.get(key), (int, float)) for key in keys):
        return None
    width = float(bbox["bottom_right_x"] - bbox["top_left_x"])
    height = float(bbox["bottom_right_y"] - bbox["top_left_y"])
    if width <= 0 or height <= 0:
        return None
    margin = min(
        _DIMENSION_HALO_MAX_PX,
        max(
            _DIMENSION_HALO_MIN_PX,
            round(min(width, height) * _DIMENSION_HALO_SHORT_SIDE_RATIO),
        ),
    )
    return {
        "top_left_x": bbox["top_left_x"] - margin,
        "top_left_y": bbox["top_left_y"] - margin,
        "bottom_right_x": bbox["bottom_right_x"] + margin,
        "bottom_right_y": bbox["bottom_right_y"] + margin,
    }


def build_detection_view_evidence_packages(
    *,
    visual_groups: list[dict[str, Any]],
    group_bboxes: dict[str, dict[str, int]],
    source_facts: list[dict[str, Any]],
    group_core_bboxes: dict[str, dict[str, int]] | None = None,
) -> list[dict[str, Any]]:
    """Build complete per-Island evidence packages by deterministic geometry.

    Registry identifies an Island's physical core and evidence envelope. It
    never owns fact attribution. Every fact has at most one owner: an envelope
    match wins when unique, otherwise the core resolves overlap, then a unique
    nearest core. Exact ties remain unowned instead of being duplicated.

    Printed outer dimensions often sit just outside an otherwise valid evidence
    envelope. A bounded halo may claim such a numeric fact only when exactly
    one Island contains it in its halo. The halo never changes Island geometry
    and never resolves an overlap, so it cannot turn a nearby Island's number
    into duplicate evidence.
    """
    keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
    core_bboxes = group_core_bboxes or group_bboxes

    def centre(value: dict[str, Any]) -> tuple[float, float] | None:
        if not all(isinstance(value.get(key), (int, float)) for key in keys):
            return None
        return (
            (value["top_left_x"] + value["bottom_right_x"]) / 2,
            (value["top_left_y"] + value["bottom_right_y"]) / 2,
        )

    def contains(bbox: dict[str, Any], point: tuple[float, float]) -> bool:
        return (
            bbox["top_left_x"] <= point[0] <= bbox["bottom_right_x"]
            and bbox["top_left_y"] <= point[1] <= bbox["bottom_right_y"]
        )

    def squared_distance_to_bbox(point: tuple[float, float], bbox: dict[str, Any]) -> float:
        dx = max(bbox["top_left_x"] - point[0], 0, point[0] - bbox["bottom_right_x"])
        dy = max(bbox["top_left_y"] - point[1], 0, point[1] - bbox["bottom_right_y"])
        return dx * dx + dy * dy

    groups_by_page: dict[int, list[dict[str, Any]]] = {}
    for group in visual_groups:
        try:
            groups_by_page.setdefault(int(group["page_number"]), []).append(group)
        except (KeyError, TypeError, ValueError):
            continue

    owned_facts: dict[str, list[dict[str, Any]]] = {
        str(group["group_id"]): [] for group in visual_groups
    }
    halo_fact_ids: dict[str, list[str]] = {
        str(group["group_id"]): [] for group in visual_groups
    }
    for fact in source_facts:
        if not isinstance(fact, dict):
            continue
        point = centre(fact.get("bbox") if isinstance(fact.get("bbox"), dict) else {})
        if point is None:
            continue
        page_groups = groups_by_page.get(fact.get("page_number"), [])
        envelope_candidates = [
            group for group in page_groups
            if (
                isinstance(group_bboxes.get(str(group.get("group_id") or "")), dict)
                and contains(group_bboxes[str(group.get("group_id") or "")], point)
            )
        ]
        if len(envelope_candidates) == 1:
            owner = envelope_candidates[0]
        elif len(envelope_candidates) > 1:
            core_candidates = [
                group for group in envelope_candidates
                if contains(core_bboxes.get(str(group.get("group_id") or ""), {}), point)
            ]
            if len(core_candidates) == 1:
                owner = core_candidates[0]
            else:
                distances = sorted(
                    (
                        squared_distance_to_bbox(
                            point, core_bboxes.get(str(group.get("group_id") or ""), {}),
                        ),
                        str(group.get("group_id") or ""), group,
                    )
                    for group in envelope_candidates
                )
                owner = (
                    distances[0][2]
                    if len(distances) == 1 or distances[0][0] < distances[1][0]
                    else None
                )
        else:
            owner = None
        halo_owner = False
        halo_match = _DIMENSION_HALO_TEXT_RE.fullmatch(str(fact.get("text") or ""))
        if (
            owner is None
            and halo_match is not None
            and Decimal(halo_match["value"].replace(",", ".")) >= _DIMENSION_HALO_MIN_VALUE
        ):
            halo_candidates = [
                group for group in page_groups
                if (
                    (halo := _detection_v5_dimension_halo(
                        group_bboxes.get(str(group.get("group_id") or ""), {})
                    ))
                    is not None and contains(halo, point)
                )
            ]
            if len(halo_candidates) == 1:
                owner = halo_candidates[0]
                halo_owner = True
        if owner is not None:
            group_id = str(owner["group_id"])
            owned_facts[group_id].append(copy.deepcopy(fact))
            if halo_owner:
                halo_fact_ids[group_id].append(str(fact["fact_id"]))

    packages: list[dict[str, Any]] = []
    for group in visual_groups:
        group_id = str(group["group_id"])
        facts = owned_facts.get(group_id, [])
        packages.append({
            "visual_group_id": group_id,
            "page_number": group["page_number"],
            "bbox": group_bboxes.get(group_id, {}),
            "core_bbox": core_bboxes.get(group_id, {}),
            "evidence_class": group.get("evidence_class"),
            "source_fact_ids": [str(fact["fact_id"]) for fact in facts],
            "source_facts": facts,
            "dimension_halo_source_fact_ids": halo_fact_ids.get(group_id, []),
            "membership_basis": "unique_evidence_envelope_or_core_nearest_owner",
        })
    return packages


def assign_detection_page_local_view_labels(
    view_evidence_packages: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Give each retained View a human-readable number restarting per page.

    ``visual_group_id`` remains the immutable internal key. ``page_view_ref`` is
    purely a page-local diagnostic reference, so removal of an empty Island
    does not alter provenance or graph keys while people can read `P04.V1`
    instead of a document-wide counter.
    """
    count_by_page: dict[int, int] = {}
    labels: dict[str, dict[str, Any]] = {}
    for package in view_evidence_packages:
        page_number = int(package["page_number"])
        sequence = count_by_page.get(page_number, 0) + 1
        count_by_page[page_number] = sequence
        label = f"P{page_number:02d}.V{sequence}"
        package["page_view_ref"] = label
        # Transitional display alias. New audit consumers must use
        # ``page_view_ref``; graph code must use ``visual_group_id``.
        package["view_label"] = label
        labels[str(package["visual_group_id"])] = {
            "page_number": page_number,
            "page_view_ref": label,
            "view_label": label,
        }
    return labels


_DIMENSION_LITERAL_TEXT_RE = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*$")


def build_detection_dimension_fingerprints(
    view_evidence_packages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create per-Island numeric fingerprints without model interpretation.

    A Registry Island establishes the spatial boundary.  From that point this
    routine uses only immutable MyPDF/Mistral facts in its View Evidence
    Package. Each printed numeric occurrence is retained with its normalized
    bbox. Near-coincident MyPDF and Mistral readings of the *same* printed
    occurrence are fused into one occurrence with both provenance IDs, so two
    OCR sources cannot artificially inflate a similarity score. We deliberately
    do not infer rows, sums, exterior dimensions or product orientation.
    """
    bbox_keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")

    def numeric_fact(
        fact: dict[str, Any], *, island_bbox: dict[str, Any],
    ) -> dict[str, Any] | None:
        match = _DIMENSION_LITERAL_TEXT_RE.match(str(fact.get("text") or ""))
        bbox = fact.get("bbox")
        if (
            not match
            or not isinstance(bbox, dict)
            or not isinstance(island_bbox, dict)
            or not all(isinstance(bbox.get(key), (int, float)) for key in bbox_keys)
            or not all(isinstance(island_bbox.get(key), (int, float)) for key in bbox_keys)
        ):
            return None
        width = island_bbox["bottom_right_x"] - island_bbox["top_left_x"]
        height = island_bbox["bottom_right_y"] - island_bbox["top_left_y"]
        if width <= 0 or height <= 0:
            return None

        def normalized_x(value: float) -> float:
            return round(min(1.0, max(0.0, (value - island_bbox["top_left_x"]) / width)), 6)

        def normalized_y(value: float) -> float:
            return round(min(1.0, max(0.0, (value - island_bbox["top_left_y"]) / height)), 6)

        normalized_bbox = {
            "top_left_x": normalized_x(float(bbox["top_left_x"])),
            "top_left_y": normalized_y(float(bbox["top_left_y"])),
            "bottom_right_x": normalized_x(float(bbox["bottom_right_x"])),
            "bottom_right_y": normalized_y(float(bbox["bottom_right_y"])),
        }
        if (
            normalized_bbox["bottom_right_x"] <= normalized_bbox["top_left_x"]
            or normalized_bbox["bottom_right_y"] <= normalized_bbox["top_left_y"]
        ):
            return None
        return {
            "fact_id": str(fact["fact_id"]),
            "value": match.group(1).replace(",", "."),
            "normalized_bbox": normalized_bbox,
        }

    def bbox_center(candidate: dict[str, Any]) -> tuple[float, float]:
        bbox = candidate["normalized_bbox"]
        return (
            (bbox["top_left_x"] + bbox["bottom_right_x"]) / 2,
            (bbox["top_left_y"] + bbox["bottom_right_y"]) / 2,
        )

    def same_printed_occurrence(
        left: dict[str, Any], right: dict[str, Any],
    ) -> bool:
        """Fuse only same-value readings whose centres are nearly coincident."""
        if left["value"] != right["value"]:
            return False
        left_x, left_y = bbox_center(left)
        right_x, right_y = bbox_center(right)
        return abs(left_x - right_x) <= 0.025 and abs(left_y - right_y) <= 0.025

    inventory: list[dict[str, Any]] = []
    for package in view_evidence_packages:
        group_id = str(package.get("visual_group_id") or "")
        island_bbox = package.get("bbox") or {}
        raw_occurrences = [
            candidate
            for fact in package.get("source_facts") or []
            if isinstance(fact, dict)
            if (candidate := numeric_fact(fact, island_bbox=island_bbox)) is not None
        ]
        raw_occurrences.sort(key=lambda item: (
            float(item["value"]), *reversed(bbox_center(item)), item["fact_id"],
        ))
        occurrences: list[dict[str, Any]] = []
        for candidate in raw_occurrences:
            matched = next((
                occurrence for occurrence in occurrences
                if same_printed_occurrence(occurrence, candidate)
            ), None)
            if matched is None:
                occurrences.append({**candidate, "source_fact_ids": [candidate["fact_id"]]})
            else:
                matched["source_fact_ids"].append(candidate["fact_id"])
        chains: list[dict[str, Any]] = []
        for occurrence_index, occurrence in enumerate(occurrences, start=1):
            chains.append({
                "chain_id": f"{group_id}-dimension-occurrence-{occurrence_index:03d}",
                "axis": "unknown",
                "segments": [],
                "direct_total": occurrence["value"],
                "normalized_bbox": occurrence["normalized_bbox"],
                "source_fact_ids": sorted(set(occurrence["source_fact_ids"])),
            })
        inventory.append({"group_id": group_id, "envelope_chains": chains})
    return inventory


_V5_DIMENSION_TEXT_RE = re.compile(
    r"^\s*(?:[A-Za-z]+\s*=\s*)?(\d+(?:[.,]\d+)?)\s*(mm|cm|m)?\s*$",
    re.IGNORECASE,
)

_V5_COMMON_BARE_MM_VALUES = frozenset({300, 400, 450, 500, 600})


def infer_detection_v5_bare_dimension_unit(
    view_evidence_packages: list[dict[str, Any]], *, document_unit: str,
) -> tuple[str, str]:
    """Infer only the safe document basis needed for bare V5 dimensions.

    An explicit document marker always wins. A bare value above 600 cannot be
    centimetres in the furniture-document envelope. Otherwise, a non-standard
    100..600 value, such as 211 or 331, establishes centimetres for this file.
    Common-only values remain unresolved rather than being silently inflated.
    """
    if document_unit in {"mm", "cm", "m"}:
        return document_unit, "explicit_document_unit"
    bare_values: list[Decimal] = []
    for package in view_evidence_packages:
        for fact in package.get("source_facts") or []:
            match = _V5_DIMENSION_TEXT_RE.match(str(fact.get("text") or "").strip())
            if match and not match.group(2):
                bare_values.append(Decimal(match.group(1).replace(",", ".")))
    if any(value > 600 for value in bare_values):
        return "mm", "bare_value_over_600"
    if any(
        Decimal("100") <= value <= Decimal("600")
        and value == value.to_integral_value()
        and int(value) not in _V5_COMMON_BARE_MM_VALUES
        for value in bare_values
    ):
        return "cm", "nonstandard_100_to_600_value"
    return "unknown", "insufficient_bare_dimension_context"


def build_detection_v5_dimension_fingerprints(
    view_evidence_packages: list[dict[str, Any]], *, document_unit: str,
) -> list[dict[str, Any]]:
    """Create V5 occurrence fingerprints without chains or inferred W/D/H."""
    conversion = {"mm": Decimal("1"), "cm": Decimal("10"), "m": Decimal("1000")}
    bbox_keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
    fingerprints: list[dict[str, Any]] = []
    for package in view_evidence_packages:
        bbox = package.get("bbox") or {}
        width = bbox.get("bottom_right_x", 0) - bbox.get("top_left_x", 0)
        height = bbox.get("bottom_right_y", 0) - bbox.get("top_left_y", 0)
        occurrences: list[dict[str, Any]] = []
        excluded: list[dict[str, str]] = []
        if width <= 0 or height <= 0:
            fingerprints.append({"group_id": str(package["visual_group_id"]), "occurrences": [], "excluded": [{"reason": "invalid_view_bbox"}]})
            continue
        for fact in package.get("source_facts") or []:
            text = str(fact.get("text") or "").strip()
            match = _V5_DIMENSION_TEXT_RE.match(text)
            if not match:
                continue
            raw_value = Decimal(match.group(1).replace(",", "."))
            explicit_unit = (match.group(2) or "").lower()
            if explicit_unit:
                value_mm = raw_value * conversion[explicit_unit]
            elif document_unit in conversion:
                value_mm = raw_value * conversion[document_unit]
            else:
                excluded.append({"fact_id": str(fact.get("fact_id") or ""), "reason": "unresolved_unit"})
                continue
            fact_bbox = fact.get("bbox") or {}
            if not all(isinstance(fact_bbox.get(key), (int, float)) for key in bbox_keys):
                excluded.append({"fact_id": str(fact.get("fact_id") or ""), "reason": "invalid_fact_bbox"})
                continue
            normalized_bbox = {
                "top_left_x": round((fact_bbox["top_left_x"] - bbox["top_left_x"]) / width, 6),
                "top_left_y": round((fact_bbox["top_left_y"] - bbox["top_left_y"]) / height, 6),
                "bottom_right_x": round((fact_bbox["bottom_right_x"] - bbox["top_left_x"]) / width, 6),
                "bottom_right_y": round((fact_bbox["bottom_right_y"] - bbox["top_left_y"]) / height, 6),
            }
            candidate = {"value_mm": str(value_mm), "original_text": text, "unit_basis": explicit_unit or document_unit, "source_fact_ids": [str(fact["fact_id"])], "normalized_bbox": normalized_bbox}
            centre = ((normalized_bbox["top_left_x"] + normalized_bbox["bottom_right_x"]) / 2, (normalized_bbox["top_left_y"] + normalized_bbox["bottom_right_y"]) / 2)
            merged = next((item for item in occurrences if item["value_mm"] == candidate["value_mm"] and abs(item["centre"][0] - centre[0]) <= 0.025 and abs(item["centre"][1] - centre[1]) <= 0.025), None)
            if merged:
                merged["source_fact_ids"].extend(candidate["source_fact_ids"])
                continue
            candidate["centre"] = centre
            # OCR providers can disagree on one printed reading.  The same
            # local slot is an alternative, never two independent matches.
            candidate["ambiguity_key"] = f"{package['visual_group_id']}:{round(centre[0] / 0.025)}:{round(centre[1] / 0.025)}"
            occurrences.append(candidate)
        for index, occurrence in enumerate(occurrences, start=1):
            occurrence["occurrence_id"] = f"{package['visual_group_id']}-D{index:03d}"
            occurrence.pop("centre")
        fingerprints.append({"group_id": str(package["visual_group_id"]), "occurrences": occurrences, "excluded": excluded})
    return fingerprints


def build_detection_view_dimension_audit(
    view_evidence_packages: list[dict[str, Any]],
    dimension_inventory: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach deterministic numeric chains to immutable per-View packages."""
    inventory_by_group_id = {
        str(row.get("group_id") or ""): row
        for row in dimension_inventory if isinstance(row, dict)
    }
    result: list[dict[str, Any]] = []
    for package in view_evidence_packages:
        group_id = str(package.get("visual_group_id") or "")
        result.append({
            **copy.deepcopy(package),
            "deterministic_dimension_chains": copy.deepcopy(
                inventory_by_group_id.get(group_id, {}).get("envelope_chains") or []
            ),
        })
    return result


def _discard_non_object_visual_registry_groups(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Remove title and generic-plan material before it can claim ownership.

    These pages may help Detection orient itself, but are never object Evidence.
    The model's original output remains in the decision audit. The effective
    payload cannot pass a generic plan into the proof graph, candidate objects,
    identity pages, or Estimation page coverage.
    """
    groups = payload.get("visual_groups")
    if not isinstance(groups, list):
        return payload, []
    discarded_groups = [
        group for group in groups
        if isinstance(group, dict)
        and (
            group.get("evidence_class") == "document_context"
            or str(group.get("representation_kind") or "").strip().lower()
            in _NON_OBJECT_VISUAL_REPRESENTATION_KINDS
        )
    ]
    if not discarded_groups:
        return payload, []

    discarded_group_ids = {
        str(group.get("group_id") or "") for group in discarded_groups
    }
    discarded_pages = {
        group.get("page_number") for group in discarded_groups
        if isinstance(group.get("page_number"), int)
    }
    effective = copy.deepcopy(payload)
    effective["visual_groups"] = [
        group for group in groups
        if not isinstance(group, dict)
        or str(group.get("group_id") or "") not in discarded_group_ids
    ]
    retained_group_pages = {
        group.get("page_number")
        for group in effective["visual_groups"]
        if isinstance(group, dict) and isinstance(group.get("page_number"), int)
    }
    retained_group_ids = {
        str(group.get("group_id") or "")
        for group in effective["visual_groups"]
        if isinstance(group, dict)
    }
    classifications = effective.get("classifications")
    if isinstance(classifications, list):
        effective["classifications"] = [
            row for row in classifications
            if not isinstance(row, dict)
            or str(row.get("group_id") or "") not in discarded_group_ids
        ]
    relation_edges = effective.get("relation_edges")
    if isinstance(relation_edges, list):
        effective["relation_edges"] = [
            edge for edge in relation_edges
            if not isinstance(edge, dict)
            or (
                str(edge.get("group_id_a") or "") in retained_group_ids
                and str(edge.get("group_id_b") or "") in retained_group_ids
            )
        ]
    dimension_inventory = effective.get("dimension_inventory")
    if isinstance(dimension_inventory, list):
        effective["dimension_inventory"] = [
            row for row in dimension_inventory
            if not isinstance(row, dict)
            or str(row.get("group_id") or "") in retained_group_ids
        ]
    semantic_facts = effective.get("semantic_facts")
    if isinstance(semantic_facts, list):
        effective["semantic_facts"] = [
            row for row in semantic_facts
            if not isinstance(row, dict)
            or (
                str(row.get("group_id_a") or "") in retained_group_ids
                and str(row.get("group_id_b") or "") in retained_group_ids
            )
        ]

    page_coverage = effective.get("page_coverage")
    if isinstance(page_coverage, list):
        for entry in page_coverage:
            if not isinstance(entry, dict) or entry.get("page_number") not in discarded_pages:
                continue
            if entry.get("page_number") not in retained_group_pages:
                entry["component_anchor_group_ids"] = []
                entry["evidence_reason"] = (
                    "non-object source page excluded from Estimation Evidence"
                )

    objects = effective.get("objects")
    if isinstance(objects, list):
        effective["objects"] = [
            item for item in objects
            if not isinstance(item, dict)
            or str(item.get("component_anchor_group_id") or "") not in discarded_group_ids
        ]
        for item in effective["objects"]:
            if not isinstance(item, dict) or not isinstance(item.get("identity_pages"), list):
                continue
            item["identity_pages"] = [
                page_number for page_number in item["identity_pages"]
                if (
                    page_number not in discarded_pages
                    or page_number in retained_group_pages
                )
            ]
    return effective, discarded_groups


def _discard_empty_evidence_visual_registry_groups(
    payload: dict[str, Any],
    *,
    raw_group_ids: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Drop a Registry Island with no deterministic source evidence.

    An Island is proposed by Registry vision, but its evidence package is
    assembled exclusively from immutable MyPDF and Mistral facts. A package
    with no facts from either source cannot support a commercial object,
    dimension chain, or Estimation handoff. Preserve the original Registry
    response in the decision audit, but remove this false-positive candidate
    before inventory validation and graph construction.
    """
    if not raw_group_ids:
        return payload, []
    groups = payload.get("visual_groups")
    if not isinstance(groups, list):
        return payload, []
    discarded_groups = [
        group for group in groups
        if isinstance(group, dict) and str(group.get("group_id") or "") in raw_group_ids
    ]
    if not discarded_groups:
        return payload, []
    effective = copy.deepcopy(payload)
    effective["visual_groups"] = [
        group for group in groups
        if not isinstance(group, dict)
        or str(group.get("group_id") or "") not in raw_group_ids
    ]
    for key in ("classifications", "dimension_inventory"):
        rows = effective.get(key)
        if isinstance(rows, list):
            effective[key] = [
                row for row in rows
                if not isinstance(row, dict)
                or str(row.get("group_id") or "") not in raw_group_ids
            ]
    semantic_facts = effective.get("semantic_facts")
    if isinstance(semantic_facts, list):
        effective["semantic_facts"] = [
            row for row in semantic_facts
            if not isinstance(row, dict)
            or (
                str(row.get("group_id_a") or "") not in raw_group_ids
                and str(row.get("group_id_b") or "") not in raw_group_ids
            )
        ]
    return effective, discarded_groups


def _scan_json_object_properties(
    value: str,
) -> tuple[list[tuple[str, int, int]], int | None]:
    """Return completed JSON object keys and an unterminated-string offset.

    The scanner intentionally records structure only. It never persists model
    text, document content, or the values attached to a key.
    """
    properties: list[tuple[str, int, int]] = []
    depth = 0
    index = 0
    length = len(value)

    while index < length:
        character = value[index]
        if character in "{[":
            depth += 1
            index += 1
            continue
        if character in "}]":
            depth = max(0, depth - 1)
            index += 1
            continue
        if character != '"':
            index += 1
            continue

        string_start = index
        index += 1
        while index < length:
            if value[index] == "\\":
                index += 2
                continue
            if value[index] == '"':
                break
            index += 1
        if index >= length:
            return properties, string_start

        string_end = index
        probe = string_end + 1
        while probe < length and value[probe].isspace():
            probe += 1
        if probe < length and value[probe] == ":":
            try:
                key = json.loads(value[string_start:string_end + 1])
            except json.JSONDecodeError:
                key = None
            if isinstance(key, str):
                properties.append((key, string_start, depth))
        index = string_end + 1

    return properties, None


def _summarize_incomplete_visual_registry_json(
    raw_text: str,
    error: json.JSONDecodeError,
    response: Any,
    *,
    max_tokens: int,
) -> dict[str, Any]:
    """Persist a privacy-safe structural trace for a truncated Registry JSON."""
    properties, open_string_start = _scan_json_object_properties(raw_text)
    top_level_sections = [
        (key, offset)
        for key, offset, depth in properties
        if depth == 1
    ]
    section_character_counts = []
    for index, (section, offset) in enumerate(top_level_sections):
        next_offset = (
            top_level_sections[index + 1][1]
            if index + 1 < len(top_level_sections)
            else len(raw_text)
        )
        section_character_counts.append({
            "section": section,
            "characters_observed": max(0, next_offset - offset),
        })

    usage = getattr(response, "usage", None)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    terminal_property = properties[-1] if properties else None
    return {
        "registry_json_failure_observer_version": "v1",
        "raw_response_persisted": False,
        "json_error_character_offset": error.pos,
        "json_error_line": error.lineno,
        "json_error_column": error.colno,
        "top_level_sections_started": [section for section, _ in top_level_sections],
        "top_level_sections_before_terminal": [
            section for section, _ in top_level_sections[:-1]
        ],
        "terminal_top_level_section": (
            top_level_sections[-1][0] if top_level_sections else None
        ),
        "top_level_section_characters_observed": section_character_counts,
        "terminal_json_property_key": (
            terminal_property[0] if terminal_property else None
        ),
        "terminal_json_property_depth": (
            terminal_property[2] if terminal_property else None
        ),
        "terminal_response_ends_inside_string": open_string_start is not None,
        "terminal_open_string_start_character": open_string_start,
        "output_token_budget_utilization_percent": round(
            100 * output_tokens / max_tokens, 3
        ) if max_tokens else None,
        "response_characters_per_output_token": round(
            len(raw_text) / output_tokens, 3
        ) if output_tokens else None,
    }


def run_anthropic_detection_v5_source_degraded_visual_experiment(
    *,
    file_name: str,
    company_id: str,
    file_bytes: bytes,
    page_images: list[bytes],
    ocr_package: dict[str, Any] | None,
    model: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run the isolated V5.13.2 route for documents without spatial evidence.

    This experimental path is deliberately not wired into the product router.
    It is gated by source capability, not document identity. It bypasses Fusion
    Candidates. Discovery maps neutral visual representations. Membership
    resolves their roles before deciding which assembly views may enter the graph, then
    evaluates visual dimensional similarity without claiming an OCR-like
    deterministic Dimension Fingerprint where the source does not support it.
    """
    if not page_images:
        raise ValueError("source-degraded visual route requires rendered pages")
    selected_model = model or get_secret(
        "CLAUDE_DETECTION_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL,
    )
    if "haiku" not in selected_model.lower():
        raise ValueError("source-degraded visual route requires a Haiku model")

    source_facts = build_detection_page_evidence_inventory(ocr_package)
    source_capability = assess_detection_source_capability(
        source_facts=source_facts,
        page_count=len(page_images),
        page_dimensions=_source_dimensions_by_page(ocr_package),
    )
    if not source_capability["route_eligible"]:
        raise ValueError(
            "source-degraded visual route is ineligible: "
            f"{source_capability['route_reason']}"
        )
    page_frames, page_frame_audit = build_detection_v5_visual_page_frames(page_images)
    if len(page_frames) != len(page_images):
        raise ValueError("source-degraded visual route cannot inspect every rendered page")
    coordinate_context = "\n".join([
        "RENDERED PAGE PIXEL FRAMES:",
        *(f"P{page_number}|{frame['width']}x{frame['height']}"
          for page_number, frame in sorted(page_frames.items())),
    ])
    discovery_prompt = load_detection_v5_source_degraded_discovery_prompt()
    membership_prompt = load_detection_v5_source_degraded_membership_prompt()
    discovery_content = build_detection_content_blocks(
        file_name=file_name,
        file_bytes=file_bytes,
        page_images=page_images,
        user_text=(
            "SOURCE CAPABILITY: no page has usable coordinate-bearing evidence. "
            "Use visual evidence only. Full rendered pages are the sole image "
            "input.\n\n" + coordinate_context
        ),
    )
    discovery_response, discovery_diagnostics = create_claude_message_streamed(
        get_anthropic_client(),
        model=selected_model,
        max_tokens=DETECTION_V5_SOURCE_DEGRADED_DISCOVERY_MAX_TOKENS,
        temperature=DETECTION_VISUAL_REGISTRY_TEMPERATURE,
        system=build_detection_system_content(prompt=discovery_prompt),
        messages=[{"role": "user", "content": discovery_content}],
        output_config={"format": {"type": "json_schema", "schema": strip_schema_for_claude(
            DETECTION_V5_SOURCE_DEGRADED_DISCOVERY_JSON_SCHEMA,
        )}},
    )
    discovery_raw_text = extract_text_from_claude_response(discovery_response)
    try:
        discovery_payload = json.loads(discovery_raw_text)
        if not isinstance(discovery_payload, dict) or set(discovery_payload) != {
            "visual_groups", "page_coverage",
        }:
            raise ValueError("source-degraded Discovery response fields are invalid")
        page_coverage = validate_detection_v5_discovery_page_coverage(
            discovery_payload["page_coverage"],
            visual_groups=discovery_payload["visual_groups"],
            page_count=len(page_images),
        )
        raw_visual_groups = discovery_payload["visual_groups"]
        raw_group_bboxes, raw_group_core_bboxes = _validate_source_degraded_visual_geometry(
            raw_visual_groups, page_frames=page_frames,
        )
        visual_map = validate_detection_visual_map(
            normalize_detection_visual_map_group_ids(
                _visual_map_from_registry_groups(raw_visual_groups),
            ),
            require_evidence_class=False,
        )
        raw_to_normalized_id = {
            str(raw["group_id"]): normalized["group_id"]
            for raw, normalized in zip(
                raw_visual_groups, visual_map["visual_groups"], strict=True,
            )
        }
        view_id_mapping = {
            **raw_to_normalized_id,
            **{group_id: group_id for group_id in raw_to_normalized_id.values()},
        }
        normalized_visual_groups = []
        for raw_group, normalized_group in zip(
            raw_visual_groups, visual_map["visual_groups"], strict=True,
        ):
            normalized_visual_groups.append({
                **copy.deepcopy(raw_group),
                **copy.deepcopy(normalized_group),
                # Discovery is deliberately neutral. Every representation is
                # supplied to Review, including title/context candidates;
                # Review is the one authority that assigns its final role.
                "evidence_class": "object_evidence",
            })
        normalized_group_bboxes = {
            raw_to_normalized_id[raw_group_id]: bbox
            for raw_group_id, bbox in raw_group_bboxes.items()
        }
        review_visual_groups = list(normalized_visual_groups)
        if not review_visual_groups:
            raise ValueError("source-degraded Discovery found no fabrication representation")
        semantic_allowed_pairs = {
            tuple(sorted((left["group_id"], right["group_id"])))
            for left, right in combinations(review_visual_groups, 2)
            if left["page_number"] == right["page_number"]
        }
        registry_visual_sources = build_detection_v5_registry_visual_sources(
            review_visual_groups,
        )
    except (json.JSONDecodeError, KeyError, ValueError, DetectionRegistrySchemaError) as exc:
        raise DetectionVisualRegistryValidationError(
            f"Source-degraded Discovery failed validation: {exc}",
            usage_event={
                "agent_name": "detection",
                "operation": "rfq_detection_v5_source_degraded_visual",
                "file_name": file_name,
                "company_id": company_id,
                "status": "failed",
                "validation_stage": "v5_13_2_discovery",
                "source_capability": source_capability,
                "error_message": str(exc),
            },
        ) from exc

    # Source-degraded Discovery has no coordinate authority.  Do not let its
    # approximate boxes cut or label the full-page evidence before Review.
    page_context_images = [
        {"page_number": page_number, "bytes": page_bytes}
        for page_number, page_bytes in enumerate(page_images, start=1)
    ]
    page_context_audit = [
        {"page_number": page_number, "mode": "full_page_without_discovery_overlay"}
        for page_number in range(1, len(page_images) + 1)
    ]
    membership_crops: list[dict[str, Any]] = []
    membership_crop_audit = [{
        "mode": "disabled_source_degraded_discovery_coordinates_not_authoritative",
    }]
    membership_handoff = format_detection_v5_membership_handoff(
        visual_groups=normalized_visual_groups,
        source_facts=registry_visual_sources,
    )
    semantic_pair_text = "\n".join([
        "ALLOWED SEMANTIC VIEW PAIRS:",
        *(f"{left}|{right}" for left, right in sorted(semantic_allowed_pairs)),
    ])
    membership_content = build_detection_v5_membership_content_blocks(
        user_text=(
            membership_handoff
            + "\n" + semantic_pair_text
            + "\nSOURCE CAPABILITY: visual-only. registry_view IDs are visual "
              "sources, not OCR or Fusion facts."
        ),
        view_crops=membership_crops,
        page_context_images=page_context_images,
    )
    membership_response, membership_diagnostics = create_claude_message_streamed(
        get_anthropic_client(),
        model=selected_model,
        max_tokens=DETECTION_V5_SOURCE_DEGRADED_MEMBERSHIP_MAX_TOKENS,
        temperature=DETECTION_VISUAL_REGISTRY_TEMPERATURE,
        system=build_detection_system_content(prompt=membership_prompt),
        messages=[{"role": "user", "content": membership_content}],
        output_config={"format": {"type": "json_schema", "schema": strip_schema_for_claude(
            DETECTION_V5_SOURCE_DEGRADED_MEMBERSHIP_JSON_SCHEMA,
        )}},
    )
    membership_raw_text = extract_text_from_claude_response(membership_response)
    membership_payload: Any = None
    try:
        membership_payload = json.loads(membership_raw_text)
        if not isinstance(membership_payload, dict) or set(membership_payload) != {
            "role_resolutions", "semantic_facts", "dimension_conflicts",
        }:
            raise ValueError("source-degraded Membership response fields are invalid")
        normalized_role_resolutions: list[dict[str, Any]] = []
        for resolution in membership_payload["role_resolutions"]:
            if not isinstance(resolution, dict):
                normalized_role_resolutions.append(resolution)
                continue
            normalized_resolution = copy.deepcopy(resolution)
            normalized_resolution["group_id"] = raw_to_normalized_id.get(
                str(resolution.get("group_id") or ""),
                str(resolution.get("group_id") or ""),
            )
            normalized_resolution["parent_group_id"] = raw_to_normalized_id.get(
                str(resolution.get("parent_group_id") or ""),
                str(resolution.get("parent_group_id") or ""),
            )
            normalized_resolution["source_fact_ids"] = (
                _normalize_source_degraded_registry_view_ids(
                    resolution.get("source_fact_ids"),
                    group_id_mapping=view_id_mapping,
                )
            )
            normalized_role_resolutions.append(normalized_resolution)
        final_roles, role_resolution_audit = (
            validate_detection_v5_source_degraded_role_resolutions(
                normalized_role_resolutions,
                visual_groups=normalized_visual_groups,
                source_facts=registry_visual_sources,
            )
        )
        final_object_groups = [
            {
                **group,
                "visual_role": final_roles[str(group["group_id"])],
                "evidence_class": "object_evidence",
            }
            for group in review_visual_groups
            if final_roles[str(group["group_id"])] == "assembly_view"
        ]
        if not final_object_groups:
            raise ValueError("source-degraded Membership removed every assembly view")
        final_object_view_ids = {
            str(group["group_id"]) for group in final_object_groups
        }
        final_registry_visual_sources = build_detection_v5_registry_visual_sources(
            final_object_groups,
        )
        final_semantic_allowed_pairs = {
            tuple(sorted((left["group_id"], right["group_id"])))
            for left, right in combinations(final_object_groups, 2)
            if left["page_number"] == right["page_number"]
        }
        final_group_bboxes = {
            group_id: bbox for group_id, bbox in normalized_group_bboxes.items()
            if group_id in final_object_view_ids
        }
        semantic_facts_outside_allowed_pairs: list[dict[str, Any]] = []
        eligible_semantic_facts: list[dict[str, Any]] = []
        for index, fact in enumerate(membership_payload["semantic_facts"]):
            if not isinstance(fact, dict):
                eligible_semantic_facts.append(fact)
                continue
            normalized_fact = copy.deepcopy(fact)
            normalized_fact["group_id_a"] = raw_to_normalized_id.get(
                str(fact.get("group_id_a") or ""), str(fact.get("group_id_a") or ""),
            )
            normalized_fact["group_id_b"] = raw_to_normalized_id.get(
                str(fact.get("group_id_b") or ""), str(fact.get("group_id_b") or ""),
            )
            normalized_fact["source_fact_ids"] = _normalize_source_degraded_registry_view_ids(
                fact.get("source_fact_ids"), group_id_mapping=view_id_mapping,
            )
            if isinstance(normalized_fact.get("structural_witness"), dict):
                witness = copy.deepcopy(normalized_fact["structural_witness"])
                witness["witness_view_id"] = raw_to_normalized_id.get(
                    str(witness.get("witness_view_id") or ""),
                    str(witness.get("witness_view_id") or ""),
                )
                normalized_fact["structural_witness"] = witness
            pair = tuple(sorted((
                str(normalized_fact["group_id_a"] or ""),
                str(normalized_fact["group_id_b"] or ""),
            )))
            if pair not in final_semantic_allowed_pairs:
                semantic_facts_outside_allowed_pairs.append({
                    "index": index,
                    "reason": (
                        "references_component_detail"
                        if any(final_roles.get(group_id) == "component_detail" for group_id in pair)
                        else "outside_visual_semantic_pair_queue"
                    ),
                    "group_id_a": pair[0],
                    "group_id_b": pair[1],
                })
                continue
            eligible_semantic_facts.append(normalized_fact)
        dimension_conflicts_outside_allowed_pairs: list[dict[str, Any]] = []
        eligible_dimension_conflicts: list[dict[str, Any]] = []
        for index, conflict in enumerate(membership_payload["dimension_conflicts"]):
            if not isinstance(conflict, dict):
                eligible_dimension_conflicts.append(conflict)
                continue
            normalized_conflict = copy.deepcopy(conflict)
            normalized_conflict["group_id_a"] = raw_to_normalized_id.get(
                str(conflict.get("group_id_a") or ""), str(conflict.get("group_id_a") or ""),
            )
            normalized_conflict["group_id_b"] = raw_to_normalized_id.get(
                str(conflict.get("group_id_b") or ""), str(conflict.get("group_id_b") or ""),
            )
            normalized_conflict["source_fact_ids"] = _normalize_source_degraded_registry_view_ids(
                conflict.get("source_fact_ids"), group_id_mapping=view_id_mapping,
            )
            pair = tuple(sorted((
                str(normalized_conflict["group_id_a"] or ""),
                str(normalized_conflict["group_id_b"] or ""),
            )))
            if pair not in final_semantic_allowed_pairs:
                dimension_conflicts_outside_allowed_pairs.append({
                    "index": index,
                    "reason": (
                        "references_component_detail"
                        if any(final_roles.get(group_id) == "component_detail" for group_id in pair)
                        else "outside_visual_semantic_pair_queue"
                    ),
                    "group_id_a": pair[0],
                    "group_id_b": pair[1],
                })
                continue
            eligible_dimension_conflicts.append(normalized_conflict)
        accepted_semantic_facts, semantic_ledger_audit = (
            compile_detection_v5_semantic_facts(
                eligible_semantic_facts,
                visual_groups=final_object_groups,
                source_facts=final_registry_visual_sources,
                allowed_evidence_types=SOURCE_DEGRADED_VISUAL_SEMANTIC_EVIDENCE_TYPES,
            )
        )
        dimension_conflict_pairs, dimension_conflict_audit = (
            compile_detection_v5_visual_dimension_conflicts(
                eligible_dimension_conflicts,
                visual_groups=final_object_groups,
                source_facts=final_registry_visual_sources,
                allowed_pairs=final_semantic_allowed_pairs,
            )
        )
        semantic_ledger_audit["outside_visual_semantic_pair_queue"] = (
            semantic_facts_outside_allowed_pairs
        )
        dimension_conflict_audit["outside_visual_semantic_pair_queue"] = (
            dimension_conflicts_outside_allowed_pairs
        )
        positive_relation_edges, v5_merge_audit = compile_detection_v5_merge_edges(
            [],
            accepted_semantic_facts,
            visual_groups=final_object_groups,
            group_bboxes=final_group_bboxes,
            merge_blocked_pairs=dimension_conflict_pairs,
            allow_batch_confirmation=False,
        )
        accepted_merge_edges = [
            edge for edge in positive_relation_edges
            if edge["relationship"] == "same_object_view"
        ]
        proof_components = derive_detection_proof_components(
            accepted_merge_edges, visual_group_ids=final_object_view_ids,
        )
        page_number_by_view_id = {
            group["group_id"]: int(group["page_number"])
            for group in visual_map["visual_groups"]
        }
        registry_objects = []
        for index, component in enumerate(proof_components, start=1):
            group_ids = sorted(component)
            pages = sorted({page_number_by_view_id[group_id] for group_id in group_ids})
            registry_objects.append({
                "object_id": f"object-{index:03d}",
                "transport_label": f"Object {index}",
                "quantity": 1,
                "quantity_explicit": False,
                "identity_pages": pages,
                "estimation_evidence_pages": pages,
                "visual_group_ids": group_ids,
                "visual_identity": "Source-degraded visual evidence graph component",
                "boundary_basis": (
                    "Deterministic component from typed visual semantic facts."
                ),
            })
        registry = validate_detection_registry(
            {"objects": registry_objects},
            visual_group_ids=final_object_view_ids,
            object_evidence_group_ids=final_object_view_ids,
        )
        registry = validate_detection_v5_final_result(
            registry,
            visual_groups=final_object_groups,
            graph_edges=positive_relation_edges,
            source_facts=final_registry_visual_sources,
        )
    except (json.JSONDecodeError, KeyError, ValueError, DetectionRegistrySchemaError) as exc:
        raise DetectionVisualRegistryValidationError(
            f"Source-degraded Membership failed validation: {exc}",
            usage_event={
                "agent_name": "detection",
                "operation": "rfq_detection_v5_source_degraded_visual",
                "file_name": file_name,
                "company_id": company_id,
                "status": "failed",
                "validation_stage": "v5_13_2_membership",
                "source_capability": source_capability,
                "discovery_decision_audit": discovery_payload,
                "membership_decision_audit": membership_payload,
                "error_message": str(exc),
            },
        ) from exc

    discovery_summary = summarize_detection_provider_call(
        response=discovery_response,
        diagnostics=discovery_diagnostics,
        prompt_characters=len(discovery_prompt),
        context_characters=len(coordinate_context),
        image_count=len(page_images),
        image_bytes=sum(len(image) for image in page_images),
    )
    membership_summary = summarize_detection_provider_call(
        response=membership_response,
        diagnostics=membership_diagnostics,
        prompt_characters=len(membership_prompt),
        context_characters=len(membership_handoff),
        image_count=len(page_context_images) + len(membership_crops),
        image_bytes=sum(
            len(context["bytes"]) for context in page_context_images
        ) + sum(len(crop["bytes"]) for crop in membership_crops),
    )
    duration_seconds = round(
        float(discovery_summary.get("duration_seconds") or 0)
        + float(membership_summary.get("duration_seconds") or 0),
        6,
    )
    usage = {
        "operation": "rfq_detection_v5_source_degraded_visual",
        "prompt_version": DETECTION_V5_SOURCE_DEGRADED_PROMPT_VERSION,
        "model": selected_model,
        "duration_seconds": duration_seconds,
        "input_tokens": int(discovery_summary.get("input_tokens") or 0)
        + int(membership_summary.get("input_tokens") or 0),
        "output_tokens": int(discovery_summary.get("output_tokens") or 0)
        + int(membership_summary.get("output_tokens") or 0),
        "input_cost_usd": round(
            float(discovery_summary.get("input_cost_usd") or 0)
            + float(membership_summary.get("input_cost_usd") or 0), 8,
        ),
        "output_cost_usd": round(
            float(discovery_summary.get("output_cost_usd") or 0)
            + float(membership_summary.get("output_cost_usd") or 0), 8,
        ),
    }
    usage["total_cost_usd"] = round(
        usage["input_cost_usd"] + usage["output_cost_usd"], 8,
    )
    usage["source_capability"] = source_capability
    usage["page_frame_audit"] = page_frame_audit
    usage["discovery"] = discovery_summary
    usage["membership"] = membership_summary
    usage["membership_page_context_audit"] = page_context_audit
    usage["membership_crop_audit"] = membership_crop_audit
    usage["visual_dimension_route"] = "model_typed_similarity_and_conflict_only"
    usage["dimension_conflict_audit"] = dimension_conflict_audit
    usage["role_resolution_audit"] = role_resolution_audit
    usage["semantic_ledger_audit"] = semantic_ledger_audit
    usage["merge_audit"] = v5_merge_audit
    usage["positive_relation_edges"] = positive_relation_edges
    usage["discovery_decision_audit"] = discovery_payload
    usage["membership_decision_audit"] = membership_payload
    return {
        "route": "v5_13_2_source_degraded_v4_representation_map_experimental",
        "visual_groups": final_object_groups,
        "discovery_visual_groups": raw_visual_groups,
        "component_detail_groups": [
            group for group in normalized_visual_groups
            if final_roles.get(str(group.get("group_id") or "")) == "component_detail"
        ],
        "document_context_groups": [
            group for group in normalized_visual_groups
            if final_roles.get(str(group.get("group_id") or "")) == "document_context"
        ],
        "role_resolution_audit": role_resolution_audit,
        "page_coverage": page_coverage,
        "proof_components": proof_components,
        "registry": registry,
    }, usage


def run_anthropic_detection_v5_source_degraded_full_page_registry_experiment(
    *,
    file_name: str,
    company_id: str,
    file_bytes: bytes,
    page_images: list[bytes],
    ocr_package: dict[str, Any] | None,
    model: str | None,
    post_discovery_view_crops: bool = False,
    component_only_partition_repair: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run V5.14's V4-style global object partition for source-degraded files.

    Discovery is deliberately only a navigational visual map.  Review receives
    the complete pages again and owns roles plus the exclusive object partition.
    The runtime validates that partition and materializes its graph.  This is
    isolated from ordinary V5, where Fusion and deterministic dimensions remain
    authoritative inputs to the graph.
    """
    if not page_images:
        raise ValueError("source-degraded full-page Registry requires rendered pages")
    selected_model = model or get_secret(
        "CLAUDE_DETECTION_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL,
    )
    if "haiku" not in selected_model.lower():
        raise ValueError("source-degraded full-page Registry requires a Haiku model")

    source_facts = build_detection_page_evidence_inventory(ocr_package)
    source_capability = assess_detection_source_capability(
        source_facts=source_facts,
        page_count=len(page_images),
        page_dimensions=_source_dimensions_by_page(ocr_package),
    )
    if not source_capability["route_eligible"]:
        raise ValueError(
            "source-degraded full-page Registry is ineligible: "
            f"{source_capability['route_reason']}"
        )
    page_frames, page_frame_audit = build_detection_v5_visual_page_frames(page_images)
    if len(page_frames) != len(page_images):
        raise ValueError("source-degraded full-page Registry cannot inspect every rendered page")
    coordinate_context = "\n".join([
        "RENDERED PAGE PIXEL FRAMES:",
        *(f"P{page_number}|{frame['width']}x{frame['height']}"
          for page_number, frame in sorted(page_frames.items())),
    ])
    discovery_prompt = load_detection_v5_source_degraded_discovery_prompt()
    registry_prompt = load_detection_v5_source_degraded_full_page_registry_prompt()
    discovery_content = build_detection_content_blocks(
        file_name=file_name,
        file_bytes=file_bytes,
        page_images=page_images,
        user_text=(
            "SOURCE CAPABILITY: no page has usable coordinate-bearing evidence. "
            "Create only an advisory visual representation map. Full rendered "
            "pages are the sole image input.\n\n" + coordinate_context
        ),
    )
    discovery_response, discovery_diagnostics = create_claude_message_streamed(
        get_anthropic_client(),
        model=selected_model,
        max_tokens=DETECTION_V5_SOURCE_DEGRADED_DISCOVERY_MAX_TOKENS,
        temperature=DETECTION_VISUAL_REGISTRY_TEMPERATURE,
        system=build_detection_system_content(prompt=discovery_prompt),
        messages=[{"role": "user", "content": discovery_content}],
        output_config={"format": {"type": "json_schema", "schema": strip_schema_for_claude(
            DETECTION_V5_SOURCE_DEGRADED_DISCOVERY_JSON_SCHEMA,
        )}},
    )
    discovery_raw_text = extract_text_from_claude_response(discovery_response)
    discovery_payload: Any = None
    try:
        discovery_payload = json.loads(discovery_raw_text)
        if not isinstance(discovery_payload, dict) or set(discovery_payload) != {
            "visual_groups", "page_coverage",
        }:
            raise ValueError("source-degraded Discovery response fields are invalid")
        page_coverage = validate_detection_v5_discovery_page_coverage(
            discovery_payload["page_coverage"],
            visual_groups=discovery_payload["visual_groups"],
            page_count=len(page_images),
        )
        raw_visual_groups = discovery_payload["visual_groups"]
        _validate_source_degraded_visual_geometry(
            raw_visual_groups, page_frames=page_frames,
        )
        visual_map = validate_detection_visual_map(
            normalize_detection_visual_map_group_ids(
                _visual_map_from_registry_groups(raw_visual_groups),
            ),
            require_evidence_class=False,
        )
        raw_to_normalized_id = {
            str(raw["group_id"]): normalized["group_id"]
            for raw, normalized in zip(
                raw_visual_groups, visual_map["visual_groups"], strict=True,
            )
        }
        visual_groups: list[dict[str, Any]] = []
        for raw_group, normalized_group in zip(
            raw_visual_groups, visual_map["visual_groups"], strict=True,
        ):
            visual_groups.append({
                **copy.deepcopy(raw_group),
                **copy.deepcopy(normalized_group),
                # The map is neutral.  Only the full-page Registry determines
                # the final role and which representations are object evidence.
                "evidence_class": "object_evidence",
            })
        if not visual_groups:
            raise ValueError("source-degraded Discovery found no visual representation")
    except (json.JSONDecodeError, KeyError, ValueError, DetectionRegistrySchemaError) as exc:
        raise DetectionVisualRegistryValidationError(
            f"Source-degraded V5.14 Discovery failed validation: {exc}",
            usage_event={
                "agent_name": "detection",
                "operation": "rfq_detection_v5_source_degraded_full_page_registry",
                "file_name": file_name,
                "company_id": company_id,
                "status": "failed",
                "validation_stage": "v5_14_discovery",
                "source_capability": source_capability,
                "error_message": str(exc),
            },
        ) from exc

    # Discovery bboxes are never an authority for an object boundary.  V5.17
    # may use them only after the map is frozen to supply an auxiliary local
    # inspection image.  The original full page remains the authoritative
    # spatial context for the Registry's role and partition decision.
    registry_map = [
        {
            "group_id": group["group_id"],
            "page_number": group["page_number"],
            "location_hint": group["location_hint"],
            "visual_description": group["visual_description"],
            "representation_kind": group["representation_kind"],
        }
        for group in visual_groups
    ]
    registry_user_text = (
        "ADVISORY VISUAL REPRESENTATION MAP:\n"
        + json.dumps(registry_map, ensure_ascii=False, separators=(",", ":"))
        + "\n\nSOURCE CAPABILITY: visual-only. Evaluate the complete page "
          "yourself. The map is not an object inventory and its rectangles "
          "are not authority for a boundary."
    )
    registry_view_crops: list[dict[str, Any]] = []
    registry_crop_audit: list[dict[str, Any]] = [{
        "mode": "disabled",
        "reason": "full_page_registry_baseline",
    }]
    registry_page_context_images: list[dict[str, Any]] = []
    if post_discovery_view_crops:
        registry_view_crops, registry_crop_audit = (
            build_detection_v5_membership_view_crops(
                page_images=page_images,
                visual_groups=visual_groups,
            )
        )
        registry_page_context_images = [
            {"page_number": page_number, "bytes": page_bytes}
            for page_number, page_bytes in enumerate(page_images, start=1)
        ]
        registry_content = build_detection_v5_membership_content_blocks(
            user_text=registry_user_text,
            page_context_images=registry_page_context_images,
            view_crops=registry_view_crops,
        )
    else:
        registry_content = build_detection_content_blocks(
            file_name=file_name,
            file_bytes=file_bytes,
            page_images=page_images,
            user_text=registry_user_text,
        )
    registry_response, registry_diagnostics = create_claude_message_streamed(
        get_anthropic_client(),
        model=selected_model,
        max_tokens=DETECTION_V5_SOURCE_DEGRADED_MEMBERSHIP_MAX_TOKENS,
        temperature=DETECTION_VISUAL_REGISTRY_TEMPERATURE,
        system=build_detection_system_content(prompt=registry_prompt),
        messages=[{"role": "user", "content": registry_content}],
        output_config={"format": {"type": "json_schema", "schema": strip_schema_for_claude(
            DETECTION_V5_SOURCE_DEGRADED_FULL_PAGE_REGISTRY_JSON_SCHEMA,
        )}},
    )
    registry_raw_text = extract_text_from_claude_response(registry_response)
    registry_payload: Any = None
    partition_repair_audit: list[dict[str, Any]] = []
    try:
        registry_payload = json.loads(registry_raw_text)
        if not isinstance(registry_payload, dict) or set(registry_payload) != {
            "roles", "partitions",
        }:
            raise ValueError("source-degraded full-page Registry response fields are invalid")

        def normalize_group_id(value: object) -> str:
            group_id = str(value or "")
            return raw_to_normalized_id.get(group_id, group_id)

        normalized_roles: list[dict[str, Any]] = []
        for role in registry_payload["roles"]:
            if not isinstance(role, dict):
                normalized_roles.append(role)
                continue
            normalized_role = copy.deepcopy(role)
            normalized_role["group_id"] = normalize_group_id(role.get("group_id"))
            normalized_roles.append(normalized_role)
        final_roles, role_audit = validate_detection_v5_source_degraded_full_page_roles(
            normalized_roles,
            visual_groups=visual_groups,
        )
        assembly_groups = [
            {
                **group,
                "visual_role": final_roles[str(group["group_id"])],
                "evidence_class": "object_evidence",
            }
            for group in visual_groups
            if final_roles[str(group["group_id"])] == "assembly_view"
        ]
        if not assembly_groups:
            raise ValueError("source-degraded full-page Registry found no assembly view")
        assembly_ids = {str(group["group_id"]) for group in assembly_groups}
        normalized_partitions: list[dict[str, Any]] = []
        for partition in registry_payload["partitions"]:
            if not isinstance(partition, dict):
                normalized_partitions.append(partition)
                continue
            normalized_partition = copy.deepcopy(partition)
            normalized_partition["group_ids"] = [
                normalize_group_id(value) for value in partition.get("group_ids") or []
            ]
            normalized_bases: list[dict[str, Any]] = []
            for basis in partition.get("visual_basis") or []:
                if not isinstance(basis, dict):
                    normalized_bases.append(basis)
                    continue
                normalized_basis = copy.deepcopy(basis)
                normalized_basis["view_ids"] = [
                    normalize_group_id(value) for value in basis.get("view_ids") or []
                ]
                normalized_bases.append(normalized_basis)
            normalized_partition["visual_basis"] = normalized_bases
            normalized_partitions.append(normalized_partition)
        if component_only_partition_repair:
            normalized_partitions, partition_repair_audit = (
                drop_detection_visual_only_component_only_partitions(
                    normalized_partitions,
                    known_view_ids={
                        str(group["group_id"]) for group in visual_groups
                    },
                    object_view_ids=assembly_ids,
                )
            )
        partitions = validate_detection_visual_only_partitions(
            normalized_partitions,
            object_view_ids=assembly_ids,
        )

        visual_sources = build_detection_v5_registry_visual_sources(assembly_groups)
        page_number_by_group_id = {
            str(group["group_id"]): int(group["page_number"])
            for group in assembly_groups
        }
        edges_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
        for partition in partitions:
            for basis in partition["visual_basis"]:
                view_ids = sorted(str(value) for value in basis["view_ids"])
                for left, right in combinations(view_ids, 2):
                    pair = (left, right)
                    fact = {
                        "evidence_type": str(basis["evidence_type"]),
                        "evidence_pages": sorted({
                            page_number_by_group_id[view_id] for view_id in view_ids
                        }),
                        "observation": str(basis["observation"]),
                        "source_fact_ids": [
                            f"registry_view:{view_id}" for view_id in view_ids
                        ],
                    }
                    edge = edges_by_pair.setdefault(pair, {
                        "group_id_a": left,
                        "group_id_b": right,
                        "relationship": "same_object_view",
                        "evidence_facts": [],
                        "commercial_inseparability": (
                            "V5.14 full-page Registry exclusive visual partition."
                        ),
                    })
                    edge["evidence_facts"].append(fact)
        positive_relation_edges = [
            edges_by_pair[pair] for pair in sorted(edges_by_pair)
        ]
        proof_components = derive_detection_proof_components(
            positive_relation_edges,
            visual_group_ids=assembly_ids,
        )
        registry_objects: list[dict[str, Any]] = []
        for index, partition in enumerate(partitions, start=1):
            group_ids = sorted(partition["group_ids"])
            pages = sorted({page_number_by_group_id[group_id] for group_id in group_ids})
            registry_objects.append({
                "object_id": f"object-{index:03d}",
                "transport_label": f"Object {index}",
                "quantity": 1,
                "quantity_explicit": False,
                "identity_pages": pages,
                "estimation_evidence_pages": pages,
                "visual_group_ids": group_ids,
                "visual_identity": "V5.14 full-page visual Registry partition",
                "boundary_basis": " ".join(
                    str(basis["observation"])
                    for basis in partition["visual_basis"]
                ),
            })
        registry = validate_detection_registry(
            {"objects": registry_objects},
            visual_group_ids=assembly_ids,
            object_evidence_group_ids=assembly_ids,
        )
        registry = validate_detection_v5_final_result(
            registry,
            visual_groups=assembly_groups,
            graph_edges=positive_relation_edges,
            source_facts=visual_sources,
        )
    except (json.JSONDecodeError, KeyError, ValueError, DetectionRegistrySchemaError) as exc:
        raise DetectionVisualRegistryValidationError(
            f"Source-degraded V5.14 full-page Registry failed validation: {exc}",
            usage_event={
                "agent_name": "detection",
                "operation": "rfq_detection_v5_source_degraded_full_page_registry",
                "file_name": file_name,
                "company_id": company_id,
                "status": "failed",
                "validation_stage": "v5_14_full_page_registry",
                "source_capability": source_capability,
                "discovery_decision_audit": discovery_payload,
                "full_page_registry_decision_audit": registry_payload,
                "partition_repair_audit": partition_repair_audit,
                "error_message": str(exc),
            },
        ) from exc

    discovery_summary = summarize_detection_provider_call(
        response=discovery_response,
        diagnostics=discovery_diagnostics,
        prompt_characters=len(discovery_prompt),
        context_characters=len(coordinate_context),
        image_count=len(page_images),
        image_bytes=sum(len(image) for image in page_images),
    )
    registry_image_count = (
        len(registry_page_context_images) + len(registry_view_crops)
        if post_discovery_view_crops else len(page_images)
    )
    registry_image_bytes = (
        sum(len(page["bytes"]) for page in registry_page_context_images)
        + sum(len(crop["bytes"]) for crop in registry_view_crops)
        if post_discovery_view_crops else sum(len(image) for image in page_images)
    )
    registry_summary = summarize_detection_provider_call(
        response=registry_response,
        diagnostics=registry_diagnostics,
        prompt_characters=len(registry_prompt),
        context_characters=len(json.dumps(registry_map, ensure_ascii=False)),
        image_count=registry_image_count,
        image_bytes=registry_image_bytes,
    )
    usage = {
        "operation": "rfq_detection_v5_source_degraded_full_page_registry",
        "prompt_version": (
            DETECTION_V5_SOURCE_DEGRADED_V518_PROMPT_VERSION
            if component_only_partition_repair
            else DETECTION_V5_SOURCE_DEGRADED_FULL_PAGE_REGISTRY_PROMPT_VERSION
        ),
        "model": selected_model,
        "duration_seconds": round(
            float(discovery_summary.get("duration_seconds") or 0)
            + float(registry_summary.get("duration_seconds") or 0),
            6,
        ),
        "input_tokens": int(discovery_summary.get("input_tokens") or 0)
        + int(registry_summary.get("input_tokens") or 0),
        "output_tokens": int(discovery_summary.get("output_tokens") or 0)
        + int(registry_summary.get("output_tokens") or 0),
        "input_cost_usd": round(
            float(discovery_summary.get("input_cost_usd") or 0)
            + float(registry_summary.get("input_cost_usd") or 0), 8,
        ),
        "output_cost_usd": round(
            float(discovery_summary.get("output_cost_usd") or 0)
            + float(registry_summary.get("output_cost_usd") or 0), 8,
        ),
        "source_capability": source_capability,
        "page_frame_audit": page_frame_audit,
        "discovery": discovery_summary,
        "full_page_registry": registry_summary,
        "full_page_review_input": (
            "full_rendered_pages_plus_post_discovery_view_crops"
            if post_discovery_view_crops
            else "full_rendered_pages_without_discovery_crops_or_overlays"
        ),
        "post_discovery_view_crop_audit": registry_crop_audit,
        "partition_repair_audit": partition_repair_audit,
        "role_audit": role_audit,
        "positive_relation_edges": positive_relation_edges,
        "discovery_decision_audit": discovery_payload,
        "full_page_registry_decision_audit": registry_payload,
    }
    usage["total_cost_usd"] = round(
        usage["input_cost_usd"] + usage["output_cost_usd"], 8,
    )
    return {
        "route": (
            "v5_18_source_degraded_full_page_registry_partition_repair"
            if component_only_partition_repair
            else (
                "v5_17_source_degraded_full_page_registry_post_discovery_crops_experimental"
                if post_discovery_view_crops
                else "v5_14_source_degraded_full_page_registry_experimental"
            )
        ),
        "visual_groups": assembly_groups,
        "discovery_visual_groups": raw_visual_groups,
        "component_detail_groups": [
            group for group in visual_groups
            if final_roles.get(str(group.get("group_id") or "")) == "component_detail"
        ],
        "document_context_groups": [
            group for group in visual_groups
            if final_roles.get(str(group.get("group_id") or "")) == "document_context"
        ],
        "role_audit": role_audit,
        "page_coverage": page_coverage,
        "partitions": partitions,
        "proof_components": proof_components,
        "registry": registry,
    }, usage


def run_anthropic_detection_v5_source_degraded_one_shot_registry_experiment(
    *,
    file_name: str,
    company_id: str,
    file_bytes: bytes,
    page_images: list[bytes],
    ocr_package: dict[str, Any] | None,
    model: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run V5.15's single-context V4-style visual Registry.

    In a source-degraded document, a prior model-produced representation map
    can itself become a false boundary.  This route keeps map, roles and object
    partition in one full-page visual decision, then validates and materializes
    the decision deterministically.  It is isolated from normal V5.
    """
    if not page_images:
        raise ValueError("source-degraded one-shot Registry requires rendered pages")
    selected_model = model or get_secret(
        "CLAUDE_DETECTION_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL,
    )
    if "haiku" not in selected_model.lower():
        raise ValueError("source-degraded one-shot Registry requires a Haiku model")
    source_facts = build_detection_page_evidence_inventory(ocr_package)
    source_capability = assess_detection_source_capability(
        source_facts=source_facts,
        page_count=len(page_images),
        page_dimensions=_source_dimensions_by_page(ocr_package),
    )
    if not source_capability["route_eligible"]:
        raise ValueError(
            "source-degraded one-shot Registry is ineligible: "
            f"{source_capability['route_reason']}"
        )
    page_frames, page_frame_audit = build_detection_v5_visual_page_frames(page_images)
    if len(page_frames) != len(page_images):
        raise ValueError("source-degraded one-shot Registry cannot inspect every rendered page")
    coordinate_context = "\n".join([
        "RENDERED PAGE PIXEL FRAMES:",
        *(f"P{page_number}|{frame['width']}x{frame['height']}"
          for page_number, frame in sorted(page_frames.items())),
    ])
    prompt = load_detection_v5_source_degraded_one_shot_registry_prompt()
    content = build_detection_content_blocks(
        file_name=file_name,
        file_bytes=file_bytes,
        page_images=page_images,
        user_text=(
            "SOURCE CAPABILITY: no page has usable coordinate-bearing evidence. "
            "Use visual evidence only. Full rendered pages are the sole image "
            "input.\n\n" + coordinate_context
        ),
    )
    response, diagnostics = create_claude_message_streamed(
        get_anthropic_client(),
        model=selected_model,
        max_tokens=DETECTION_V5_SOURCE_DEGRADED_DISCOVERY_MAX_TOKENS,
        temperature=DETECTION_VISUAL_REGISTRY_TEMPERATURE,
        system=build_detection_system_content(prompt=prompt),
        messages=[{"role": "user", "content": content}],
        output_config={"format": {"type": "json_schema", "schema": strip_schema_for_claude(
            DETECTION_V5_SOURCE_DEGRADED_ONE_SHOT_REGISTRY_JSON_SCHEMA,
        )}},
    )
    raw_text = extract_text_from_claude_response(response)
    payload: Any = None
    try:
        payload = json.loads(raw_text)
        if not isinstance(payload, dict) or set(payload) != {
            "visual_groups", "page_coverage", "roles", "partitions",
        }:
            raise ValueError("source-degraded one-shot Registry response fields are invalid")
        raw_visual_groups = payload["visual_groups"]
        page_coverage = validate_detection_v5_discovery_page_coverage(
            payload["page_coverage"],
            visual_groups=raw_visual_groups,
            page_count=len(page_images),
        )
        _validate_source_degraded_visual_geometry(
            raw_visual_groups, page_frames=page_frames,
        )
        visual_map = validate_detection_visual_map(
            normalize_detection_visual_map_group_ids(
                _visual_map_from_registry_groups(raw_visual_groups),
            ),
            require_evidence_class=False,
        )
        raw_to_normalized_id = {
            str(raw["group_id"]): normalized["group_id"]
            for raw, normalized in zip(
                raw_visual_groups, visual_map["visual_groups"], strict=True,
            )
        }
        visual_groups = [
            {
                **copy.deepcopy(raw_group),
                **copy.deepcopy(normalized_group),
                "evidence_class": "object_evidence",
            }
            for raw_group, normalized_group in zip(
                raw_visual_groups, visual_map["visual_groups"], strict=True,
            )
        ]
        if not visual_groups:
            raise ValueError("source-degraded one-shot Registry found no visual representation")

        def normalize_group_id(value: object) -> str:
            group_id = str(value or "")
            return raw_to_normalized_id.get(group_id, group_id)

        normalized_roles: list[dict[str, Any]] = []
        for role in payload["roles"]:
            if not isinstance(role, dict):
                normalized_roles.append(role)
                continue
            normalized_role = copy.deepcopy(role)
            normalized_role["group_id"] = normalize_group_id(role.get("group_id"))
            normalized_roles.append(normalized_role)
        final_roles, role_audit = validate_detection_v5_source_degraded_full_page_roles(
            normalized_roles,
            visual_groups=visual_groups,
        )
        assembly_groups = [
            {
                **group,
                "visual_role": final_roles[str(group["group_id"])],
                "evidence_class": "object_evidence",
            }
            for group in visual_groups
            if final_roles[str(group["group_id"])] == "assembly_view"
        ]
        if not assembly_groups:
            raise ValueError("source-degraded one-shot Registry found no assembly view")
        assembly_ids = {str(group["group_id"]) for group in assembly_groups}
        normalized_partitions: list[dict[str, Any]] = []
        for partition in payload["partitions"]:
            if not isinstance(partition, dict):
                normalized_partitions.append(partition)
                continue
            normalized_partition = copy.deepcopy(partition)
            normalized_partition["group_ids"] = [
                normalize_group_id(value) for value in partition.get("group_ids") or []
            ]
            normalized_bases: list[dict[str, Any]] = []
            for basis in partition.get("visual_basis") or []:
                if not isinstance(basis, dict):
                    normalized_bases.append(basis)
                    continue
                normalized_basis = copy.deepcopy(basis)
                normalized_basis["view_ids"] = [
                    normalize_group_id(value) for value in basis.get("view_ids") or []
                ]
                normalized_bases.append(normalized_basis)
            normalized_partition["visual_basis"] = normalized_bases
            normalized_partitions.append(normalized_partition)
        partitions = validate_detection_visual_only_partitions(
            normalized_partitions,
            object_view_ids=assembly_ids,
        )
        visual_sources = build_detection_v5_registry_visual_sources(assembly_groups)
        page_number_by_group_id = {
            str(group["group_id"]): int(group["page_number"])
            for group in assembly_groups
        }
        edges_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
        for partition in partitions:
            for basis in partition["visual_basis"]:
                view_ids = sorted(str(value) for value in basis["view_ids"])
                for left, right in combinations(view_ids, 2):
                    pair = (left, right)
                    fact = {
                        "evidence_type": str(basis["evidence_type"]),
                        "evidence_pages": sorted({
                            page_number_by_group_id[view_id] for view_id in view_ids
                        }),
                        "observation": str(basis["observation"]),
                        "source_fact_ids": [
                            f"registry_view:{view_id}" for view_id in view_ids
                        ],
                    }
                    edge = edges_by_pair.setdefault(pair, {
                        "group_id_a": left,
                        "group_id_b": right,
                        "relationship": "same_object_view",
                        "evidence_facts": [],
                        "commercial_inseparability": (
                            "V5.15 one-shot Registry exclusive visual partition."
                        ),
                    })
                    edge["evidence_facts"].append(fact)
        positive_relation_edges = [
            edges_by_pair[pair] for pair in sorted(edges_by_pair)
        ]
        proof_components = derive_detection_proof_components(
            positive_relation_edges,
            visual_group_ids=assembly_ids,
        )
        registry_objects: list[dict[str, Any]] = []
        for index, partition in enumerate(partitions, start=1):
            group_ids = sorted(partition["group_ids"])
            pages = sorted({page_number_by_group_id[group_id] for group_id in group_ids})
            registry_objects.append({
                "object_id": f"object-{index:03d}",
                "transport_label": f"Object {index}",
                "quantity": 1,
                "quantity_explicit": False,
                "identity_pages": pages,
                "estimation_evidence_pages": pages,
                "visual_group_ids": group_ids,
                "visual_identity": "V5.15 one-shot full-page visual Registry partition",
                "boundary_basis": " ".join(
                    str(basis["observation"])
                    for basis in partition["visual_basis"]
                ),
            })
        registry = validate_detection_registry(
            {"objects": registry_objects},
            visual_group_ids=assembly_ids,
            object_evidence_group_ids=assembly_ids,
        )
        registry = validate_detection_v5_final_result(
            registry,
            visual_groups=assembly_groups,
            graph_edges=positive_relation_edges,
            source_facts=visual_sources,
        )
    except (json.JSONDecodeError, KeyError, ValueError, DetectionRegistrySchemaError) as exc:
        raise DetectionVisualRegistryValidationError(
            f"Source-degraded V5.15 one-shot Registry failed validation: {exc}",
            usage_event={
                "agent_name": "detection",
                "operation": "rfq_detection_v5_source_degraded_one_shot_registry",
                "file_name": file_name,
                "company_id": company_id,
                "status": "failed",
                "validation_stage": "v5_15_one_shot_registry",
                "source_capability": source_capability,
                "one_shot_registry_decision_audit": payload,
                "error_message": str(exc),
            },
        ) from exc

    summary = summarize_detection_provider_call(
        response=response,
        diagnostics=diagnostics,
        prompt_characters=len(prompt),
        context_characters=len(coordinate_context),
        image_count=len(page_images),
        image_bytes=sum(len(image) for image in page_images),
    )
    usage = {
        "operation": "rfq_detection_v5_source_degraded_one_shot_registry",
        "prompt_version": DETECTION_V5_SOURCE_DEGRADED_ONE_SHOT_REGISTRY_PROMPT_VERSION,
        "model": selected_model,
        "duration_seconds": float(summary.get("duration_seconds") or 0),
        "input_tokens": int(summary.get("input_tokens") or 0),
        "output_tokens": int(summary.get("output_tokens") or 0),
        "input_cost_usd": float(summary.get("input_cost_usd") or 0),
        "output_cost_usd": float(summary.get("output_cost_usd") or 0),
        "source_capability": source_capability,
        "page_frame_audit": page_frame_audit,
        "one_shot_registry": summary,
        "full_page_review_input": "full_rendered_pages_without_crops_or_overlays",
        "role_audit": role_audit,
        "positive_relation_edges": positive_relation_edges,
        "one_shot_registry_decision_audit": payload,
    }
    usage["total_cost_usd"] = round(
        usage["input_cost_usd"] + usage["output_cost_usd"], 8,
    )
    return {
        "route": "v5_15_source_degraded_one_shot_registry_experimental",
        "visual_groups": assembly_groups,
        "discovery_visual_groups": raw_visual_groups,
        "component_detail_groups": [
            group for group in visual_groups
            if final_roles.get(str(group.get("group_id") or "")) == "component_detail"
        ],
        "document_context_groups": [
            group for group in visual_groups
            if final_roles.get(str(group.get("group_id") or "")) == "document_context"
        ],
        "role_audit": role_audit,
        "page_coverage": page_coverage,
        "partitions": partitions,
        "proof_components": proof_components,
        "registry": registry,
    }, usage


def _detection_bbox_intersection_area(
    left: dict[str, int], right: dict[str, int],
) -> int:
    width = max(0, min(left["bottom_right_x"], right["bottom_right_x"])
                - max(left["top_left_x"], right["top_left_x"]))
    height = max(0, min(left["bottom_right_y"], right["bottom_right_y"])
                 - max(left["top_left_y"], right["top_left_y"]))
    return width * height


def _detection_bbox_agreement(
    left: dict[str, int], right: dict[str, int],
) -> tuple[float, float]:
    intersection = _detection_bbox_intersection_area(left, right)
    left_area = _detection_bbox_area(left)
    right_area = _detection_bbox_area(right)
    union = left_area + right_area - intersection
    iou = intersection / union if union else 0.0
    containment = intersection / min(left_area, right_area) if min(left_area, right_area) else 0.0
    return round(iou, 6), round(containment, 6)


def _normalize_detection_v516_v561_proposal(
    payload: object,
    *,
    page_frames: dict[int, dict[str, int]],
) -> dict[str, Any]:
    """Normalize one V5.6.1-style proposal without inventing evidence."""
    fields = {
        "visual_groups", "classifications", "object_hypotheses",
        "candidate_region_exceptions", "semantic_facts",
    }
    if not isinstance(payload, dict) or set(payload) != fields:
        raise ValueError("V5.16 visual proposal has invalid fields")
    if payload["candidate_region_exceptions"] != []:
        raise ValueError("V5.16 source-degraded proposal cannot return candidate exceptions")
    if payload["semantic_facts"] != []:
        raise ValueError("V5.16 source-degraded proposal cannot return source semantic facts")

    classified, classification_audit = _validate_and_apply_visual_registry_classifications(
        copy.deepcopy(payload)
    )
    raw_groups = classified["visual_groups"]
    raw_group_ids = [str(group.get("group_id") or "") for group in raw_groups]
    visual_map = validate_detection_visual_map(
        normalize_detection_visual_map_group_ids(
            _visual_map_from_registry_groups(raw_groups)
        ),
        require_evidence_class=False,
    )
    group_id_mapping = {
        raw_group_id: normalized["group_id"]
        for raw_group_id, normalized in zip(
            raw_group_ids, visual_map["visual_groups"], strict=True,
        )
    }
    group_bboxes = _normalize_registry_group_bboxes(
        raw_groups, group_id_mapping=group_id_mapping,
    )
    visual_groups: list[dict[str, Any]] = []
    for raw_group, normalized_group in zip(
        raw_groups, visual_map["visual_groups"], strict=True,
    ):
        group_id = str(normalized_group["group_id"])
        page_number = int(normalized_group["page_number"])
        frame = page_frames.get(page_number)
        bbox = group_bboxes[group_id]
        if (
            frame is None
            or bbox["bottom_right_x"] > frame["width"]
            or bbox["bottom_right_y"] > frame["height"]
        ):
            raise ValueError("V5.16 visual proposal bbox exceeds rendered page")
        visual_groups.append({
            **copy.deepcopy(raw_group),
            **copy.deepcopy(normalized_group),
            "bbox": copy.deepcopy(bbox),
            "evidence_class": raw_group["evidence_class"],
            "classification_reason": raw_group["classification_reason"],
        })

    normalized_hypotheses: list[dict[str, Any]] = []
    for hypothesis in classified["object_hypotheses"]:
        if not isinstance(hypothesis, dict):
            normalized_hypotheses.append(hypothesis)
            continue
        row = copy.deepcopy(hypothesis)
        if isinstance(row.get("group_ids"), list):
            row["group_ids"] = [
                group_id_mapping.get(str(value or ""), str(value or ""))
                for value in row["group_ids"]
            ]
        normalized_hypotheses.append(row)
    object_groups = [
        group for group in visual_groups
        if group["evidence_class"] == "object_evidence"
    ]
    accepted_hypotheses, hypothesis_audit = compile_detection_v5_object_hypotheses(
        normalized_hypotheses, visual_groups=visual_groups,
    )
    return {
        "visual_groups": visual_groups,
        "object_groups": object_groups,
        "accepted_hypotheses": accepted_hypotheses,
        "classification_audit": classification_audit,
        "hypothesis_audit": hypothesis_audit,
        "raw_payload": copy.deepcopy(payload),
    }


def _match_detection_v516_v561_object_groups(
    primary_groups: list[dict[str, Any]],
    secondary_groups: list[dict[str, Any]],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Match only unambiguous same-page Islands across both proposals."""
    candidates: list[tuple[float, float, str, str, dict[str, Any]]] = []
    for primary in primary_groups:
        for secondary in secondary_groups:
            if primary.get("page_number") != secondary.get("page_number"):
                continue
            iou, containment = _detection_bbox_agreement(
                primary["bbox"], secondary["bbox"],
            )
            if iou < 0.50 and containment < 0.80:
                continue
            candidates.append((
                iou, containment, str(primary["group_id"]),
                str(secondary["group_id"]),
                {
                    "primary_group_id": str(primary["group_id"]),
                    "secondary_group_id": str(secondary["group_id"]),
                    "page_number": int(primary["page_number"]),
                    "iou": iou,
                    "containment": containment,
                },
            ))
    candidates.sort(key=lambda row: (-row[0], -row[1], row[2], row[3]))
    matched_primary: set[str] = set()
    matched_secondary: set[str] = set()
    mapping: dict[str, str] = {}
    audit: list[dict[str, Any]] = []
    for _, _, primary_id, secondary_id, row in candidates:
        if primary_id in matched_primary or secondary_id in matched_secondary:
            row["status"] = "rejected_ambiguous_or_duplicate"
            audit.append(row)
            continue
        matched_primary.add(primary_id)
        matched_secondary.add(secondary_id)
        mapping[secondary_id] = primary_id
        row["status"] = "accepted"
        audit.append(row)
    for group in primary_groups:
        group_id = str(group["group_id"])
        if group_id not in matched_primary:
            audit.append({
                "primary_group_id": group_id,
                "page_number": int(group["page_number"]),
                "status": "unmatched_primary_island",
            })
    for group in secondary_groups:
        group_id = str(group["group_id"])
        if group_id not in matched_secondary:
            audit.append({
                "secondary_group_id": group_id,
                "page_number": int(group["page_number"]),
                "status": "unmatched_secondary_island",
            })
    return mapping, audit


def _detection_v516_hypothesis_pairs(
    hypotheses: list[dict[str, Any]],
    *,
    group_id_mapping: dict[str, str] | None = None,
) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for hypothesis in hypotheses:
        group_ids = [str(value) for value in hypothesis.get("group_ids") or []]
        if group_id_mapping is not None:
            if any(group_id not in group_id_mapping for group_id in group_ids):
                continue
            group_ids = [group_id_mapping[group_id] for group_id in group_ids]
        for left, right in combinations(sorted(set(group_ids)), 2):
            pairs.add((left, right))
    return pairs


def _compile_detection_v516_v561_consensus(
    *,
    primary: dict[str, Any],
    secondary: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Materialize only membership links present in both full-page proposals."""
    primary_groups = list(primary["object_groups"])
    secondary_groups = list(secondary["object_groups"])
    secondary_to_primary, island_agreement = _match_detection_v516_v561_object_groups(
        primary_groups, secondary_groups,
    )
    primary_pairs = _detection_v516_hypothesis_pairs(
        primary["accepted_hypotheses"],
    )
    secondary_pairs = _detection_v516_hypothesis_pairs(
        secondary["accepted_hypotheses"],
        group_id_mapping=secondary_to_primary,
    )
    consensus_pairs = sorted(primary_pairs.intersection(secondary_pairs))
    group_by_id = {
        str(group["group_id"]): group for group in primary_groups
    }
    visual_sources = build_detection_v5_registry_visual_sources(primary_groups)
    edges: list[dict[str, Any]] = []
    for left, right in consensus_pairs:
        pages = sorted({
            int(group_by_id[left]["page_number"]),
            int(group_by_id[right]["page_number"]),
        })
        edges.append({
            "group_id_a": left,
            "group_id_b": right,
            "relationship": "same_object_view",
            "evidence_facts": [{
                "evidence_type": "visual_consensus",
                "evidence_pages": pages,
                "observation": (
                    "Both independent V5.6.1-style full-page proposals declared "
                    "these Islands alternate Views of one item."
                ),
                "source_fact_ids": [
                    f"registry_view:{left}", f"registry_view:{right}",
                ],
            }],
            "commercial_inseparability": (
                "V5.16 requires independent full-page membership agreement."
            ),
        })
    components = derive_detection_proof_components(
        edges, visual_group_ids=set(group_by_id),
    )
    objects: list[dict[str, Any]] = []
    for index, group_ids in enumerate(components, start=1):
        pages = sorted({int(group_by_id[group_id]["page_number"]) for group_id in group_ids})
        objects.append({
            "object_id": f"object-{index:03d}",
            "transport_label": f"Object {index}",
            "quantity": 1,
            "quantity_explicit": False,
            "identity_pages": pages,
            "estimation_evidence_pages": pages,
            "visual_group_ids": group_ids,
            "visual_identity": "V5.16 independent full-page visual consensus",
            "boundary_basis": (
                "Independent V5.6.1-style proposals agreed on the retained "
                "same-object membership edges."
                if len(group_ids) > 1 else
                "No same-object membership edge was agreed by both independent proposals."
            ),
        })
    registry = validate_detection_registry(
        {"objects": objects},
        visual_group_ids=set(group_by_id),
        object_evidence_group_ids=set(group_by_id),
    )
    registry = validate_detection_v5_final_result(
        registry,
        visual_groups=primary_groups,
        graph_edges=edges,
        source_facts=visual_sources,
    )
    audit = {
        "compiler_version": "v5_16_two_independent_v561_full_page_proposals",
        "island_agreement": island_agreement,
        "primary_hypothesis_pairs": [list(pair) for pair in sorted(primary_pairs)],
        "secondary_hypothesis_pairs_mapped": [list(pair) for pair in sorted(secondary_pairs)],
        "consensus_pairs": [list(pair) for pair in consensus_pairs],
    }
    return {
        "visual_groups": primary_groups,
        "graph_edges": edges,
        "proof_components": components,
        "registry": registry,
    }, audit


def run_anthropic_detection_v5_source_degraded_v561_consensus_experiment(
    *,
    file_name: str,
    company_id: str,
    file_bytes: bytes,
    page_images: list[bytes],
    ocr_package: dict[str, Any] | None,
    model: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run two V5.6.1-style full-page proposals and retain their overlap only.

    This source-degraded experiment has no pre-Discovery crops or effect on
    ordinary V5. It does not manufacture deterministic source evidence.
    """
    if not page_images:
        raise ValueError("V5.16 source-degraded consensus requires rendered pages")
    selected_model = model or get_secret(
        "CLAUDE_DETECTION_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL,
    )
    if "haiku" not in selected_model.lower():
        raise ValueError("V5.16 source-degraded consensus requires a Haiku model")
    source_facts = build_detection_page_evidence_inventory(ocr_package)
    source_capability = assess_detection_source_capability(
        source_facts=source_facts,
        page_count=len(page_images),
        page_dimensions=_source_dimensions_by_page(ocr_package),
    )
    if not source_capability["route_eligible"]:
        raise ValueError(
            "V5.16 source-degraded consensus is ineligible: "
            f"{source_capability['route_reason']}"
        )
    page_frames, page_frame_audit = build_detection_v5_visual_page_frames(page_images)
    if len(page_frames) != len(page_images):
        raise ValueError("V5.16 source-degraded consensus cannot inspect every page")
    prompt = load_detection_v5_source_degraded_v561_consensus_prompt()
    coordinate_context = "\n".join([
        "RENDERED PAGE PIXEL FRAMES:",
        *(f"P{page_number}|{frame['width']}x{frame['height']}"
          for page_number, frame in sorted(page_frames.items())),
    ])
    content = build_detection_content_blocks(
        file_name=file_name,
        file_bytes=file_bytes,
        page_images=page_images,
        user_text=(
            "SOURCE CAPABILITY: no page has usable coordinate-bearing evidence. "
            "Inspect the complete rendered pages. Candidate Regions and "
            "Dimension Queue are empty in this route.\n\n" + coordinate_context
        ),
    )

    proposal_results: list[dict[str, Any]] = []
    proposal_summaries: list[dict[str, Any]] = []
    for proposal_number in (1, 2):
        response, diagnostics = create_claude_message_streamed(
            get_anthropic_client(),
            model=selected_model,
            max_tokens=DETECTION_VISUAL_REGISTRY_MAX_TOKENS,
            temperature=DETECTION_VISUAL_REGISTRY_TEMPERATURE,
            system=build_detection_system_content(prompt=prompt),
            messages=[{"role": "user", "content": content}],
            output_config={"format": {"type": "json_schema", "schema": strip_schema_for_claude(
                DETECTION_V5_SOURCE_DEGRADED_V561_CONSENSUS_JSON_SCHEMA,
            )}},
        )
        raw_text = extract_text_from_claude_response(response)
        raw_payload: object = None
        try:
            raw_payload = json.loads(raw_text)
            proposal = _normalize_detection_v516_v561_proposal(
                raw_payload, page_frames=page_frames,
            )
        except (json.JSONDecodeError, ValueError, DetectionRegistrySchemaError) as exc:
            raise DetectionVisualRegistryValidationError(
                f"V5.16 proposal {proposal_number} failed validation: {exc}",
                usage_event={
                    "agent_name": "detection",
                    "operation": "rfq_detection_v5_source_degraded_v561_consensus",
                    "file_name": file_name,
                    "company_id": company_id,
                    "status": "failed",
                    "proposal_number": proposal_number,
                    "source_capability": source_capability,
                    "raw_payload": raw_payload,
                    "error_message": str(exc),
                },
            ) from exc
        proposal_results.append(proposal)
        proposal_summaries.append(summarize_detection_provider_call(
            response=response,
            diagnostics=diagnostics,
            prompt_characters=len(prompt),
            context_characters=len(coordinate_context),
            image_count=len(page_images),
            image_bytes=sum(len(image) for image in page_images),
        ))

    consensus, consensus_audit = _compile_detection_v516_v561_consensus(
        primary=proposal_results[0], secondary=proposal_results[1],
    )
    usage = {
        "operation": "rfq_detection_v5_source_degraded_v561_consensus",
        "prompt_version": DETECTION_V5_SOURCE_DEGRADED_V561_CONSENSUS_PROMPT_VERSION,
        "model": selected_model,
        "proposal_count": 2,
        "source_capability": source_capability,
        "page_frame_audit": page_frame_audit,
        "full_page_review_input": "two_independent_full_rendered_page_proposals_without_crops",
        "proposals": proposal_summaries,
        "duration_seconds": round(sum(
            float(summary.get("duration_seconds") or 0) for summary in proposal_summaries
        ), 6),
        "input_tokens": sum(int(summary.get("input_tokens") or 0) for summary in proposal_summaries),
        "output_tokens": sum(int(summary.get("output_tokens") or 0) for summary in proposal_summaries),
        "input_cost_usd": round(sum(
            float(summary.get("input_cost_usd") or 0) for summary in proposal_summaries
        ), 8),
        "output_cost_usd": round(sum(
            float(summary.get("output_cost_usd") or 0) for summary in proposal_summaries
        ), 8),
        "consensus_audit": consensus_audit,
    }
    usage["total_cost_usd"] = round(
        usage["input_cost_usd"] + usage["output_cost_usd"], 8,
    )
    return {
        "route": "v5_16_source_degraded_v561_two_proposal_consensus_experimental",
        "proposal_a": proposal_results[0],
        "proposal_b": proposal_results[1],
        **consensus,
    }, usage


def run_anthropic_detection_visual_registry_agent(*, file_name: str, company_id: str, file_bytes: bytes, page_images: list[bytes], regions: list[dict[str, Any]], ocr_package: dict[str, Any] | None, model: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run V5.10.12 Island discovery, then a bounded membership review."""
    selected_model = model or get_secret("CLAUDE_DETECTION_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL)
    prompt_version = DETECTION_VISUAL_REGISTRY_PROMPT_VERSION
    proposal_prompt = load_detection_v5_proposal_prompt()
    review_prompt = load_detection_v5_review_prompt()
    document_dimension_unit_profile = (
        extract_detection_document_dimension_unit_profile(ocr_package)
    )
    source_facts = build_detection_page_evidence_inventory(ocr_package)
    review_coordinate_frames, review_coordinate_frame_audit = (
        build_detection_v5_review_coordinate_frames(
            ocr_package=ocr_package,
            page_images=page_images,
        )
    )
    coordinate_frame_text = format_detection_v5_coordinate_frame_context(
        review_coordinate_frames
    )
    candidate_regions = build_detection_fusion_candidate_regions(
        ocr_package, source_facts,
    )
    candidate_visual_groups = [{
        "group_id": str(candidate["candidate_region_id"]),
        "page_number": candidate["page_number"],
        "evidence_class": "object_evidence",
    } for candidate in candidate_regions]
    candidate_group_bboxes = {
        str(candidate["candidate_region_id"]): candidate["bbox"]
        for candidate in candidate_regions
    }
    candidate_packages = build_detection_view_evidence_packages(
        visual_groups=candidate_visual_groups,
        group_bboxes=candidate_group_bboxes,
        source_facts=source_facts,
    )
    candidate_unit, candidate_unit_reason = infer_detection_v5_bare_dimension_unit(
        candidate_packages,
        document_unit=str(document_dimension_unit_profile.get("unit") or "unknown"),
    )
    candidate_dimension_inventory = build_detection_v5_dimension_fingerprints(
        candidate_packages, document_unit=candidate_unit,
    )
    _, candidate_dimension_audit = compile_detection_v5_dimension_graph(
        candidate_dimension_inventory,
        visual_groups=candidate_visual_groups,
        group_bboxes=candidate_group_bboxes,
    )
    candidate_pair_queue = list(
        candidate_dimension_audit.get("dimension_similarity_candidates") or []
    )
    candidate_pair_queue_audit = {
        "compiler_version": "v5_10_4_same_page_all_pairs_threshold_25",
        "input_candidate_count": len(candidate_pair_queue),
        "selected_candidate_count": len(candidate_pair_queue),
        "same_page_selected_count": sum(
            bool(row.get("same_page")) for row in candidate_pair_queue
        ),
        "cross_page_strong_selected_count": sum(
            not bool(row.get("same_page"))
            and float(row.get("dimension_similarity_score") or 0) >= 85
            for row in candidate_pair_queue
        ),
        "excluded_candidate_count": 0,
    }
    candidate_dimension_baskets = list(
        candidate_dimension_audit.get("provisional_components") or []
    )
    candidate_pair_queue_audit["input_basket_count"] = len(candidate_dimension_baskets)
    candidate_pair_queue_audit["selected_basket_count"] = len(candidate_dimension_baskets)
    candidate_region_audit: list[dict[str, Any]] = []
    fusion_candidate_region_text = format_detection_fusion_candidate_regions(
        candidate_regions
    )
    page_evidence_inventory_text = format_detection_page_evidence_inventory(source_facts)
    proposal_user_text = build_detection_user_text(
        file_name=file_name, company_id=company_id, ocr_package=None,
    ).replace("OCR text layer: unavailable", page_evidence_inventory_text)
    proposal_user_text += "\n\n" + fusion_candidate_region_text
    proposal_user_text += "\n\n" + format_detection_candidate_pair_queue(
        candidate_pair_queue, candidate_dimension_baskets,
    )
    proposal_user_text += "\n\n" + format_detection_document_dimension_unit_profile(
        document_dimension_unit_profile,
    )
    proposal_user_text += "\n\n" + coordinate_frame_text
    proposal_content = build_detection_registry_content_blocks(
        file_name=file_name, file_bytes=file_bytes, user_text=proposal_user_text,
        page_images=page_images, regions=regions,
    )
    proposal_response, proposal_diagnostics = create_claude_message_streamed(
        get_anthropic_client(), model=selected_model,
        max_tokens=DETECTION_V5_PROPOSAL_MAX_TOKENS,
        temperature=DETECTION_VISUAL_REGISTRY_TEMPERATURE,
        system=build_detection_system_content(prompt=proposal_prompt),
        messages=[{"role": "user", "content": proposal_content}],
        output_config={"format": {"type": "json_schema", "schema": strip_schema_for_claude(DETECTION_V5_DISCOVERY_JSON_SCHEMA)}},
    )
    proposal_raw_text = extract_text_from_claude_response(proposal_response)
    try:
        proposal_raw_payload = json.loads(proposal_raw_text)
    except json.JSONDecodeError as exc:
        failure_diagnostics = dict(proposal_diagnostics)
        failure_diagnostics.update({
            "fusion_candidate_regions": candidate_regions,
            "document_dimension_unit_profile": document_dimension_unit_profile,
            **_summarize_incomplete_visual_registry_json(
                proposal_raw_text, exc, proposal_response,
                max_tokens=DETECTION_V5_PROPOSAL_MAX_TOKENS,
            ),
            "validation_error": str(exc),
            "validation_stage": "v5_9_proposal_json",
            "attempt_label": "v5_9_proposal_json_parse_failed",
            "response_character_count": len(proposal_raw_text),
            "response_text_sha256": _sha256_text(proposal_raw_text),
            "max_tokens": DETECTION_V5_PROPOSAL_MAX_TOKENS,
        })
        failure_usage = build_agent_usage_event(
            agent_name="detection", operation="rfq_detection_visual_registry",
            company_id=company_id, run_id=None, file_name=file_name,
            object_id=None, object_name=None, model=selected_model,
            prompt_version=prompt_version, response=proposal_response,
            started_at=proposal_diagnostics["request_started_at"],
            finished_at=proposal_diagnostics["request_finished_at"],
            request_diagnostics=failure_diagnostics,
        )
        failure_usage["status"] = "failed"
        failure_usage["error_message"] = str(exc)
        raise DetectionVisualRegistryValidationError(
            f"Detection proposal response failed validation: {exc}",
            usage_event=failure_usage,
        ) from exc
    discovery_fields = {
        "visual_groups", "classifications", "candidate_region_exceptions", "page_coverage",
    }
    legacy_proposal_fields = {
        "visual_groups", "classifications", "candidate_region_exceptions",
        "object_hypotheses", "semantic_facts",
    }
    if not isinstance(proposal_raw_payload, dict) or set(proposal_raw_payload) not in (
        discovery_fields, legacy_proposal_fields,
    ):
        raise DetectionVisualRegistryValidationError(
            "Detection proposal response failed the V5.10.1 discovery contract"
        )
    if set(proposal_raw_payload) == discovery_fields:
        proposal_page_coverage = validate_detection_v5_discovery_page_coverage(
            proposal_raw_payload["page_coverage"],
            visual_groups=proposal_raw_payload["visual_groups"], page_count=len(page_images),
        )
    else:
        proposal_page_coverage = [{
            "status": "legacy_response_without_page_coverage",
            "page_count": len(page_images),
        }]
    proposal_discovery_payload = {
        field: proposal_raw_payload[field]
        for field in discovery_fields - {"page_coverage"}
    }
    proposal_for_review, _ = _validate_and_apply_visual_registry_classifications(
        proposal_discovery_payload
    )
    registry_visual_sources = build_detection_v5_registry_visual_sources(
        proposal_for_review["visual_groups"]
    )
    membership_crops, membership_crop_audit = build_detection_v5_membership_view_crops(
        page_images=page_images, visual_groups=proposal_for_review["visual_groups"],
        coordinate_frames=review_coordinate_frames,
    )
    review_page_context_images, review_page_context_audit = (
        build_detection_v5_review_page_context_images(
            page_images=page_images, visual_groups=proposal_for_review["visual_groups"],
            coordinate_frames=review_coordinate_frames,
        )
    )
    review_handoff = format_detection_v5_review_handoff(
        visual_groups=proposal_for_review["visual_groups"], source_facts=source_facts,
        draft_hypotheses=[],
    )
    review_content = build_detection_v5_membership_content_blocks(
        user_text=review_handoff, view_crops=membership_crops,
        page_context_images=review_page_context_images,
    )
    review_response, review_diagnostics = create_claude_message_streamed(
        get_anthropic_client(), model=selected_model,
        max_tokens=DETECTION_V5_MEMBERSHIP_MAX_TOKENS,
        temperature=DETECTION_VISUAL_REGISTRY_TEMPERATURE,
        system=build_detection_system_content(prompt=review_prompt),
        messages=[{"role": "user", "content": review_content}],
        output_config={"format": {"type": "json_schema", "schema": strip_schema_for_claude(DETECTION_V5_MEMBERSHIP_JSON_SCHEMA)}},
    )
    review_raw_text = extract_text_from_claude_response(review_response)
    try:
        review_raw_payload = json.loads(review_raw_text)
    except json.JSONDecodeError as exc:
        failure_diagnostics = dict(review_diagnostics)
        failure_diagnostics.update({
            **_summarize_incomplete_visual_registry_json(
                review_raw_text, exc, review_response,
                max_tokens=DETECTION_V5_MEMBERSHIP_MAX_TOKENS,
            ),
            "validation_error": str(exc),
            "validation_stage": "v5_9_review_json",
            "attempt_label": "v5_9_review_json_parse_failed",
            "response_character_count": len(review_raw_text),
            "response_text_sha256": _sha256_text(review_raw_text),
        })
        failure_usage = build_agent_usage_event(
            agent_name="detection", operation="rfq_detection_visual_registry",
            company_id=company_id, run_id=None, file_name=file_name,
            object_id=None, object_name=None, model=selected_model,
            prompt_version=prompt_version, response=review_response,
            started_at=review_diagnostics["request_started_at"],
            finished_at=review_diagnostics["request_finished_at"],
            request_diagnostics=failure_diagnostics,
        )
        failure_usage["status"] = "failed"
        failure_usage["error_message"] = str(exc)
        raise DetectionVisualRegistryValidationError(
            f"Detection review response failed validation: {exc}",
            usage_event=failure_usage,
        ) from exc
    if not isinstance(review_raw_payload, dict) or not isinstance(
        review_raw_payload.get("object_hypotheses"), list,
    ):
        raise DetectionVisualRegistryValidationError(
            "Detection review response failed the V5.9 review contract"
        )
    payload = {
        "visual_groups": proposal_raw_payload["visual_groups"],
        "classifications": proposal_raw_payload["classifications"],
        "object_hypotheses": review_raw_payload["object_hypotheses"],
        "candidate_region_exceptions": proposal_discovery_payload["candidate_region_exceptions"],
        "semantic_facts": [],
    }
    diagnostics = dict(review_diagnostics)
    diagnostics["v5_10_proposal_page_coverage"] = proposal_page_coverage
    diagnostics.update({
        "request_started_at": proposal_diagnostics["request_started_at"],
        "request_finished_at": review_diagnostics["request_finished_at"],
        "temperature": DETECTION_VISUAL_REGISTRY_TEMPERATURE,
        "page_evidence_source_fact_count": len(source_facts),
        "v5_9_coordinate_frame_audit": review_coordinate_frame_audit,
        "v5_9_coordinate_frame_context_characters": len(coordinate_frame_text),
        "v5_9_registry_visual_source_count": len(registry_visual_sources),
        "page_evidence_inventory_characters": len(page_evidence_inventory_text),
        "fusion_candidate_region_characters": len(fusion_candidate_region_text),
        "candidate_pair_queue_characters": len(format_detection_candidate_pair_queue(candidate_pair_queue, candidate_dimension_baskets)),
        "document_unit_profile_characters": len(format_detection_document_dimension_unit_profile(document_dimension_unit_profile)),
        "fusion_candidate_region_count": len(candidate_regions),
        "candidate_pair_queue_count": len(candidate_pair_queue),
        "candidate_pair_queue_audit": candidate_pair_queue_audit,
        "candidate_dimension_basket_count": len(candidate_dimension_baskets),
        "candidate_dimension_unit": candidate_unit,
        "candidate_dimension_unit_reason": candidate_unit_reason,
        "rendered_page_image_bytes": sum(len(image) for image in page_images),
        "rendered_page_image_count": len(page_images),
        "registry_crop_image_count": len(regions),
        "registry_crop_image_bytes": sum(len(region.get("bytes") or b"") for region in regions),
        "registry_system_prompt_characters": len(proposal_prompt) + len(review_prompt),
        "v5_9_proposal": summarize_detection_provider_call(
            response=proposal_response, diagnostics=proposal_diagnostics,
            prompt_characters=len(proposal_prompt), context_characters=len(proposal_user_text),
            image_count=len(page_images) + len(regions),
            image_bytes=sum(len(image) for image in page_images) + sum(len(region.get("bytes") or b"") for region in regions),
        ),
        "v5_9_review": summarize_detection_provider_call(
            response=review_response, diagnostics=review_diagnostics,
            prompt_characters=len(review_prompt), context_characters=len(review_handoff),
            image_count=len(review_page_context_images) + len(membership_crops),
            image_bytes=(
                sum(len(page["bytes"]) for page in review_page_context_images)
                + sum(len(crop["bytes"]) for crop in membership_crops)
            ),
        ),
        "v5_9_review_crop_audit": membership_crop_audit,
        "v5_9_review_page_context_audit": review_page_context_audit,
        "v5_9_proposal_decision_audit": copy.deepcopy(proposal_raw_payload),
        "v5_9_review_decision_audit": copy.deepcopy(review_raw_payload),
    })
    # Preserve the composed decision before runtime normalizes IDs and derives
    # deterministic graph and Evidence pages.
    registry_decision_audit = copy.deepcopy(payload)
    discarded_non_object_groups: list[dict[str, Any]] = []
    discarded_empty_evidence_groups: list[dict[str, Any]] = []
    classification_decisions: list[dict[str, Any]] = []
    positive_relation_edges: list[dict[str, Any]] = []
    accepted_merge_edges: list[dict[str, Any]] = []
    reference_links: list[dict[str, Any]] = []
    rejected_relation_candidates: list[dict[str, Any]] = []
    dimension_inventory_audit: list[dict[str, Any]] = []
    dimension_inventory_valid = False
    dimension_inventory_error: str | None = None
    group_bboxes: dict[str, dict[str, int]] = {}
    group_core_bboxes: dict[str, dict[str, int]] = {}
    view_evidence_packages: list[dict[str, Any]] = []
    page_local_view_labels: dict[str, dict[str, Any]] = {}
    island_dimension_comparison_audit: list[dict[str, Any]] = []
    empty_envelope_chain_group_ids: list[str] = []
    dimension_conflicts: list[dict[str, Any]] = []
    dimension_graph_audit: dict[str, Any] = {}
    semantic_ledger_audit: dict[str, Any] = {}
    package_decisions: list[dict[str, Any]] = []
    dimension_package_candidate_components: list[list[str]] = []
    dimension_package_candidate_decisions: list[dict[str, Any]] = []
    page_coverage_audit: list[dict[str, Any]] = []
    graph_page_coverage_supplements: list[dict[str, Any]] = []
    fallback_registry_object_ids: list[str] = []
    registry_metadata_audit: dict[str, Any] = {}
    registry_graph_review_required_object_ids: list[str] = []
    classified_visual_groups: list[dict[str, Any]] = []
    try:
        if isinstance(payload, dict):
            payload, classification_decisions = (
                _validate_and_apply_visual_registry_classifications(payload)
            )
            classified_visual_groups = copy.deepcopy(payload["visual_groups"])
            all_group_bboxes = _normalize_registry_group_bboxes(
                classified_visual_groups,
                group_id_mapping={
                    str(group.get("group_id") or ""): str(group.get("group_id") or "")
                    for group in classified_visual_groups
                },
            )
            candidate_region_audit = build_detection_candidate_region_audit(
                candidate_regions=candidate_regions,
                candidate_region_exceptions=payload["candidate_region_exceptions"],
                visual_groups=classified_visual_groups,
                group_bboxes=all_group_bboxes,
                group_id_mapping={
                    str(group.get("group_id") or ""): str(group.get("group_id") or "")
                    for group in classified_visual_groups
                },
            )
            payload, discarded_non_object_groups = (
                _discard_non_object_visual_registry_groups(payload)
            )
        if not isinstance(payload, dict) or set(payload) != {
            "visual_groups", "classifications", "object_hypotheses", "candidate_region_exceptions", "semantic_facts",
        }:
            raise ValueError(
                "visual registry must contain visual groups, classifications, hypotheses and semantic facts"
            )
        raw_groups = payload["visual_groups"]
        raw_group_ids = [str(group.get("group_id") or "") for group in raw_groups]
        visual_map = validate_detection_visual_map(
            normalize_detection_visual_map_group_ids(
                _visual_map_from_registry_groups(raw_groups)
            ), require_evidence_class=False,
        )
        group_id_mapping = {
            raw_group_id: normalized["group_id"]
            for raw_group_id, normalized in zip(raw_group_ids, visual_map["visual_groups"], strict=True)
        }
        semantic_validation_groups = [
            {
                "group_id": group_id_mapping[str(group.get("group_id") or "")],
                "evidence_class": group.get("evidence_class"),
            }
            for group in raw_groups
        ]
        group_bboxes = _normalize_registry_group_bboxes(
            raw_groups, group_id_mapping=group_id_mapping,
        )
        group_core_bboxes = _normalize_registry_group_core_bboxes(
            raw_groups,
            group_id_mapping=group_id_mapping,
            evidence_envelopes=group_bboxes,
        )
        page_by_group_id = {
            str(group["group_id"]): int(group["page_number"])
            for group in visual_map["visual_groups"]
        }
        candidate_q_final_pairs, candidate_q_mapping_audit = map_detection_candidate_q_pairs_to_islands(
            candidate_pair_queue,
            candidate_regions=candidate_regions,
            group_bboxes=group_bboxes,
            page_by_group_id=page_by_group_id,
            include_audit=True,
        )
        visual_group_ids = {
            group["group_id"] for group in visual_map["visual_groups"]
        }
        view_evidence_packages = build_detection_view_evidence_packages(
            visual_groups=visual_map["visual_groups"], group_bboxes=group_bboxes,
            group_core_bboxes=group_core_bboxes, source_facts=source_facts,
        )
        page_local_view_labels = assign_detection_page_local_view_labels(
            view_evidence_packages
        )
        normalized_hypotheses = []
        for hypothesis in payload["object_hypotheses"]:
            if isinstance(hypothesis, dict) and isinstance(hypothesis.get("group_ids"), list):
                hypothesis = copy.deepcopy(hypothesis)
                hypothesis["group_ids"] = [
                    group_id_mapping.get(str(group_id or ""), str(group_id or ""))
                    for group_id in hypothesis["group_ids"]
                ]
                normalized_evidence = []
                for evidence in hypothesis.get("evidence") or []:
                    if not isinstance(evidence, dict):
                        normalized_evidence.append(evidence)
                        continue
                    normalized_evidence_row = copy.deepcopy(evidence)
                    if isinstance(normalized_evidence_row.get("structural_witness"), dict):
                        witness = copy.deepcopy(normalized_evidence_row["structural_witness"])
                        witness["witness_view_id"] = group_id_mapping.get(
                            str(witness.get("witness_view_id") or ""),
                            str(witness.get("witness_view_id") or ""),
                        )
                        normalized_evidence_row["structural_witness"] = witness
                    normalized_evidence.append(normalized_evidence_row)
                hypothesis["evidence"] = normalized_evidence
            normalized_hypotheses.append(hypothesis)
        accepted_hypotheses, object_hypothesis_audit = compile_detection_v5_object_hypotheses(
            normalized_hypotheses, visual_groups=semantic_validation_groups,
        )
        semantic_facts_outside_dimension_queue: list[dict[str, Any]] = []
        semantic_facts: list[dict[str, Any]] = []
        for hypothesis in accepted_hypotheses:
            root, *members = hypothesis["group_ids"]
            for member in members:
                pair = tuple(sorted((root, member)))
                for evidence in hypothesis["evidence"]:
                    semantic_facts.append({
                        "group_id_a": pair[0], "group_id_b": pair[1], **evidence,
                    })
                if pair not in candidate_q_final_pairs:
                    semantic_facts_outside_dimension_queue.append({
                        "reason": "derived_semantic_fact_outside_dimension_queue_accepted",
                        "group_id_a": pair[0], "group_id_b": pair[1],
                    })
        effective_dimension_unit, dimension_unit_reason = infer_detection_v5_bare_dimension_unit(
            view_evidence_packages,
            document_unit=str(document_dimension_unit_profile.get("unit") or "unknown"),
        )
        payload["dimension_inventory"] = build_detection_v5_dimension_fingerprints(
            view_evidence_packages,
            document_unit=effective_dimension_unit,
        )
        dimension_inventory_audit = payload["dimension_inventory"]
        dimension_inventory_valid = True
        island_dimension_comparison_audit = []
        page_drawing_codes = extract_detection_page_drawing_codes(ocr_package)
        dimension_relation_edges, dimension_graph_audit = compile_detection_v5_dimension_graph(
            dimension_inventory_audit, visual_groups=visual_map["visual_groups"],
            group_bboxes=group_bboxes,
            allowed_pairs=candidate_q_final_pairs,
        )
        # Title-block codes remain naming metadata only.  Retain this audit
        # trail to prove they never become identity edges.
        dimension_graph_audit.update({
            "page_local_view_labels": page_local_view_labels,
            "effective_document_dimension_unit": effective_dimension_unit,
            "effective_document_dimension_unit_reason": dimension_unit_reason,
            "page_drawing_codes": {str(page): code for page, code in page_drawing_codes.items()},
            "source_root_merge_edge_count": 0,
            "candidate_pair_queue_count": len(candidate_pair_queue),
            "candidate_pair_queue_final_pair_count": len(candidate_q_final_pairs),
            "candidate_pair_queue_mapping_audit": candidate_q_mapping_audit,
            "candidate_pair_queue_final_pairs": [
                {"group_id_a": pair[0], "group_id_b": pair[1]}
                for pair in sorted(candidate_q_final_pairs)
            ],
        })
        accepted_semantic_facts, semantic_ledger_audit = compile_detection_v5_semantic_facts(
            semantic_facts, visual_groups=semantic_validation_groups,
            source_facts=[*source_facts, *registry_visual_sources],
        )
        semantic_ledger_audit["outside_dimension_queue"] = semantic_facts_outside_dimension_queue
        semantic_ledger_audit["rejected"].extend(
            object_hypothesis_audit["rejected"]
        )
        semantic_ledger_audit["object_hypotheses"] = object_hypothesis_audit
        positive_relation_edges, v5_merge_audit = compile_detection_v5_merge_edges(
            dimension_relation_edges, accepted_semantic_facts,
            visual_groups=visual_map["visual_groups"], group_bboxes=group_bboxes,
        )
        accepted_merge_edges = [
            edge for edge in positive_relation_edges
            if edge["relationship"] == "same_object_view"
        ]
        base_proof_components = derive_detection_proof_components(
            accepted_merge_edges, visual_group_ids=visual_group_ids,
        )
        dominant_page_edges, dominant_page_attachment_audit = (
            derive_detection_v5_dominant_page_attachment_edges(
                base_proof_components, visual_groups=visual_map["visual_groups"],
            )
        )
        positive_relation_edges.extend(dominant_page_edges)
        accepted_merge_edges.extend(dominant_page_edges)
        semantic_ledger_audit["dominant_page_attachment"] = dominant_page_attachment_audit
        reference_links = []
        rejected_relation_candidates = list(semantic_ledger_audit["rejected"])
        dimension_package_candidate_components = (
            derive_detection_dimension_package_candidates(
                positive_relation_edges, visual_group_ids=visual_group_ids,
            )
        )
        dimension_package_candidate_decisions = derive_detection_package_decision_audit(
            dimension_package_candidate_components
        )
        # Only accepted merge edges decide package membership. Every omitted,
        # weak or rejected relation therefore remains a singleton rather than
        # aborting the document or disappearing from Estimation Evidence.
        proof_components = derive_detection_proof_components(
            accepted_merge_edges, visual_group_ids=visual_group_ids,
        )
        standalone_package_group_ids = derive_detection_standalone_package_group_ids(
            proof_components
        )
        package_decisions = derive_detection_package_decision_audit(proof_components)
        page_number_by_group_id = {
            str(group["group_id"]): int(group["page_number"])
            for group in visual_map["visual_groups"]
        }
        (
            registry_objects_input,
            anchor_to_object_id,
            fallback_registry_object_ids,
            registry_metadata_audit,
        ) = _derive_registry_from_proof_components(
            [],
            proof_components,
            page_number_by_group_id=page_number_by_group_id,
            page_count=len(page_images),
            source_labels_by_component_anchor=(
                _component_source_labels_from_page_codes(
                    proof_components,
                    page_number_by_group_id=page_number_by_group_id,
                    page_drawing_codes=page_drawing_codes,
                )
            ),
        )
        (
            resolved_page_coverage,
            graph_page_coverage_supplements,
            page_coverage_audit,
        ) = _resolve_component_page_coverage(
            [],
            anchor_to_object_id=anchor_to_object_id,
            page_number_by_group_id=page_number_by_group_id,
            page_count=len(page_images),
            reference_links=reference_links,
        )
        registry_objects, reconciled_object_ids = _apply_page_coverage_to_registry(
            registry_objects_input, resolved_page_coverage, page_count=len(page_images),
        )
        registry_graph_review_required_object_ids = sorted({
            *(
                anchor_to_object_id[group_id]
                for group_id in standalone_package_group_ids
                if group_id in anchor_to_object_id
            ),
            *(
                anchor_to_object_id[group_id]
                for candidate in rejected_relation_candidates
                for group_id in (
                    str(candidate.get("group_id_a") or ""),
                    str(candidate.get("group_id_b") or ""),
                )
                if group_id in anchor_to_object_id
            ),
            *(
                anchor_to_object_id[group_id]
                for edge in accepted_merge_edges
                if any(
                    fact.get("evidence_type") == "explicit_document_relation"
                    for fact in edge.get("evidence_facts") or []
                )
                for group_id in (
                    str(edge.get("group_id_a") or ""),
                    str(edge.get("group_id_b") or ""),
                )
                if group_id in anchor_to_object_id
            ),
        })
        registry_payload = {"objects": registry_objects}
        registry = validate_detection_registry(
            registry_payload,
            visual_group_ids=visual_group_ids,
            object_evidence_group_ids=visual_group_ids,
        )
        registry = validate_detection_v5_final_result(
            registry,
            visual_groups=visual_map["visual_groups"],
            graph_edges=positive_relation_edges,
            source_facts=[*source_facts, *registry_visual_sources],
        )
    except (KeyError, ValueError) as exc:
        failure_diagnostics = dict(diagnostics)
        failure_diagnostics.update({
            "fusion_candidate_regions": candidate_regions,
            "candidate_region_audit": candidate_region_audit,
            "registry_decision_audit": registry_decision_audit,
            "discarded_non_object_visual_groups": discarded_non_object_groups,
            "discarded_empty_evidence_visual_groups": discarded_empty_evidence_groups,
            "classification_decisions": classification_decisions,
            "page_evidence_source_fact_count": len(source_facts),
            "view_evidence_packages": view_evidence_packages,
            "page_local_view_labels": page_local_view_labels,
            "positive_relation_edges": positive_relation_edges,
            "dimension_inventory": dimension_inventory_audit,
            "dimension_inventory_valid": dimension_inventory_valid,
            "dimension_inventory_error": dimension_inventory_error,
            "island_dimension_comparison_audit": island_dimension_comparison_audit,
            "empty_envelope_chain_group_ids": empty_envelope_chain_group_ids,
            "document_dimension_unit_profile": document_dimension_unit_profile,
            "dimension_conflicts": dimension_conflicts,
            "dimension_graph_audit": dimension_graph_audit,
            "semantic_ledger_audit": semantic_ledger_audit,
            "v5_merge_audit": v5_merge_audit,
            "dimension_package_candidate_components": dimension_package_candidate_components,
            "dimension_package_candidate_decisions": dimension_package_candidate_decisions,
            "accepted_merge_edges": accepted_merge_edges,
            "reference_links": reference_links,
            "rejected_relation_candidates": rejected_relation_candidates,
            "page_coverage_audit": page_coverage_audit,
            "validation_error": str(exc),
            "validation_stage": "visual_registry",
            "attempt_label": "visual_registry_validation_failed",
        })
        if isinstance(exc, DetectionRegistrySchemaError) and exc.details:
            failure_diagnostics["validation_details"] = exc.details
        failure_usage = build_agent_usage_event(
            agent_name="detection",
            operation="rfq_detection_visual_registry",
            company_id=company_id,
            run_id=None,
            file_name=file_name,
            object_id=None,
            object_name=None,
            model=selected_model,
            prompt_version=prompt_version,
            response=response,
            started_at=diagnostics["request_started_at"],
            finished_at=diagnostics["request_finished_at"],
            request_diagnostics=failure_diagnostics,
        )
        failure_usage["status"] = "failed"
        failure_usage["error_message"] = str(exc)
        raise DetectionVisualRegistryValidationError(
            f"Detection visual-registry response failed validation: {exc}",
            usage_event=failure_usage,
        ) from exc
    assigned_visual_group_ids = {
        group_id
        for item in registry["objects"]
        for group_id in item["visual_group_ids"]
    }
    object_evidence_group_ids = {group["group_id"] for group in visual_map["visual_groups"]}
    diagnostics.update({
        "visual_group_count": len(visual_map["visual_groups"]),
        "registry_object_count": len(registry["objects"]),
        "unassigned_visual_group_count": len(visual_group_ids - assigned_visual_group_ids),
        "unassigned_object_evidence_group_count": len(
            visual_group_ids - assigned_visual_group_ids
        ),
        "proof_component_count": len(proof_components),
        "page_coverage_count": len(resolved_page_coverage),
        "unassigned_page_count": sum(
            not entry["object_ids"] for entry in resolved_page_coverage
        ),
        "registry_decision_audit": registry_decision_audit,
        "discarded_non_object_visual_groups": discarded_non_object_groups,
        "discarded_empty_evidence_visual_groups": discarded_empty_evidence_groups,
        "classification_decisions": classification_decisions,
        "page_evidence_source_fact_count": len(source_facts),
        "view_evidence_packages": view_evidence_packages,
        "page_local_view_labels": page_local_view_labels,
        "positive_relation_edges": positive_relation_edges,
        "dimension_inventory": dimension_inventory_audit,
        "dimension_inventory_valid": dimension_inventory_valid,
        "dimension_inventory_error": dimension_inventory_error,
        "island_dimension_comparison_audit": island_dimension_comparison_audit,
        "empty_envelope_chain_group_ids": empty_envelope_chain_group_ids,
        "document_dimension_unit_profile": document_dimension_unit_profile,
        "dimension_inventory_group_count": len(dimension_inventory_audit),
        "dimension_conflicts": dimension_conflicts,
        "dimension_graph_audit": dimension_graph_audit,
        "semantic_ledger_audit": semantic_ledger_audit,
        "v5_merge_audit": v5_merge_audit,
        "dimension_package_candidate_components": dimension_package_candidate_components,
        "dimension_package_candidate_decisions": dimension_package_candidate_decisions,
        "positive_relation_edge_count": len(positive_relation_edges),
        "positive_dimension_equality_count": sum(
            fact.get("evidence_type") == "dimension_equality"
            for edge in positive_relation_edges
            for fact in edge["evidence_facts"]
        ),
        "positive_dimension_transform_count": sum(
            fact.get("evidence_type") == "dimension_transform"
            for edge in positive_relation_edges
            for fact in edge["evidence_facts"]
        ),
        "accepted_merge_edges": accepted_merge_edges,
        "accepted_merge_edge_count": len(accepted_merge_edges),
        "rejected_relation_candidates": rejected_relation_candidates,
        "rejected_relation_candidate_count": len(rejected_relation_candidates),
        "reference_links": reference_links,
        "reference_link_count": len(reference_links),
        "package_decisions": package_decisions,
        "standalone_package_group_ids": standalone_package_group_ids,
        "registry_metadata_fallback_object_ids": fallback_registry_object_ids,
        "registry_graph_review_required_object_ids": registry_graph_review_required_object_ids,
        "registry_metadata_audit": registry_metadata_audit,
        "graph_page_coverage_supplements": graph_page_coverage_supplements,
        "page_coverage_audit": page_coverage_audit,
        "proof_graph_components": [
            {
                "canonical_anchor_group_id": component[0],
                "visual_group_ids": component,
            }
            for component in proof_components
        ],
        "region_count": len(regions),
        "fusion_candidate_regions": candidate_regions,
        "candidate_region_audit": candidate_region_audit,
        "unexplained_candidate_region_count": sum(
            row["status"] == "unexplained" for row in candidate_region_audit
        ),
        "visual_group_counts_by_page": {
            str(page_number): sum(
                group["page_number"] == page_number
                for group in visual_map["visual_groups"]
            )
            for page_number in range(1, len(page_images) + 1)
        },
        "raw_visual_group_counts_by_page": {
            str(page_number): sum(
                group.get("page_number") == page_number
                for group in classified_visual_groups
            )
            for page_number in range(1, len(page_images) + 1)
        },
        "raw_object_evidence_counts_by_page": {
            str(page_number): sum(
                group.get("page_number") == page_number
                and group.get("evidence_class") == "object_evidence"
                for group in classified_visual_groups
            )
            for page_number in range(1, len(page_images) + 1)
        },
        "page_count": len(page_images),
        "attempt_label": "v5_9_full_proposal_full_page_review",
    })
    if reconciled_object_ids:
        diagnostics["single_page_coverage_reconciled_object_ids"] = reconciled_object_ids
    usage = build_agent_usage_event(agent_name="detection",operation="rfq_detection_visual_registry",company_id=company_id,run_id=None,file_name=file_name,object_id=None,object_name=None,model=selected_model,prompt_version=prompt_version,response=review_response,started_at=diagnostics["request_started_at"],finished_at=diagnostics["request_finished_at"],request_diagnostics=diagnostics)
    proposal_usage = diagnostics["v5_9_proposal"]
    review_usage = diagnostics["v5_9_review"]
    total_input_tokens = int(proposal_usage["input_tokens"]) + int(review_usage["input_tokens"])
    total_output_tokens = int(proposal_usage["output_tokens"]) + int(review_usage["output_tokens"])
    total_costs = calculate_llm_cost_usd(
        model=selected_model,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
    )
    usage.update({
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "input_cost_usd": total_costs["input_cost_usd"],
        "output_cost_usd": total_costs["output_cost_usd"],
        "total_cost_usd": total_costs["total_cost_usd"],
    })
    usage["raw_usage"].update({
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "v5_9_total_provider_duration_seconds": round(
            sum(float(call.get("duration_seconds") or 0) for call in (
                proposal_usage, review_usage,
            )),
            3,
        ),
    })
    return visual_map, registry, usage


def run_anthropic_detection_registry_agent(*, file_name: str, company_id: str, file_bytes: bytes, page_images: list[bytes], visual_map: dict[str, Any], ocr_package: dict[str, Any] | None, model: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    selected_model = model or get_secret("CLAUDE_DETECTION_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL)
    prompt = load_detection_registry_prompt()
    user_text = build_detection_user_text(file_name=file_name, company_id=company_id, ocr_package=ocr_package)
    user_text += "\n\nVISUAL REPRESENTATION MAP (navigation only, not object decisions):\n"
    user_text += json.dumps(visual_map, ensure_ascii=False)
    schema = strip_schema_for_claude(DETECTION_REGISTRY_JSON_SCHEMA)
    content = build_detection_registry_content_blocks(
        file_name=file_name,
        file_bytes=file_bytes,
        user_text=user_text,
        page_images=page_images,
        regions=[],
    )

    def request_registry(max_tokens: int) -> tuple[Any, dict[str, Any]]:
        return create_claude_message_streamed(
            get_anthropic_client(),
            model=selected_model,
            max_tokens=max_tokens,
            system=build_detection_system_content(prompt=prompt),
            messages=[{"role": "user", "content": content}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )

    response, diagnostics = request_registry(5000)
    try:
        payload = json.loads(extract_text_from_claude_response(response))
    except json.JSONDecodeError as initial_error:
        # A truncated structured response is transport failure, not a commercial
        # object decision. Retry once with the provider's full response budget.
        response, diagnostics = request_registry(8192)
        diagnostics["retry_after_truncated_json"] = True
        try:
            payload = json.loads(extract_text_from_claude_response(response))
        except json.JSONDecodeError as retry_error:
            raise RuntimeError(
                "Detection registry response remained invalid JSON after retry: "
                f"{retry_error}"
            ) from retry_error
    try:
        registry = validate_detection_registry(
            payload,
            visual_group_ids={group["group_id"] for group in visual_map["visual_groups"]},
        )
    except ValueError as exc:
        raise RuntimeError(f"Detection registry response failed validation: {exc}") from exc
    assigned_visual_group_ids = {
        group_id
        for item in registry["objects"]
        for group_id in item["visual_group_ids"]
    }
    visual_group_ids = {group["group_id"] for group in visual_map["visual_groups"]}
    diagnostics.update({
        "registry_object_count": len(registry["objects"]),
        "visual_group_count": len(visual_map["visual_groups"]),
        "unassigned_visual_group_count": len(visual_group_ids - assigned_visual_group_ids),
        "page_count": len(page_images),
        "attempt_label": "registry_from_visual_map",
    })
    usage = build_agent_usage_event(agent_name="detection",operation="rfq_detection_registry",company_id=company_id,run_id=None,file_name=file_name,object_id=None,object_name=None,model=selected_model,prompt_version=DETECTION_REGISTRY_PROMPT_VERSION,response=response,started_at=diagnostics["request_started_at"],finished_at=diagnostics["request_finished_at"],request_diagnostics=diagnostics)
    return registry, usage


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


_CYRILLIC_TO_LATIN = str.maketrans({
    "А": "A", "а": "a", "Б": "B", "б": "b", "В": "V", "в": "v",
    "Г": "G", "г": "g", "Д": "D", "д": "d", "Е": "E", "е": "e",
    "Ё": "Yo", "ё": "yo", "Ж": "Zh", "ж": "zh", "З": "Z", "з": "z",
    "И": "I", "и": "i", "Й": "Y", "й": "y", "К": "K", "к": "k",
    "Л": "L", "л": "l", "М": "M", "м": "m", "Н": "N", "н": "n",
    "О": "O", "о": "o", "П": "P", "п": "p", "Р": "R", "р": "r",
    "С": "S", "с": "s", "Т": "T", "т": "t", "У": "U", "у": "u",
    "Ф": "F", "ф": "f", "Х": "Kh", "х": "kh", "Ц": "Ts", "ц": "ts",
    "Ч": "Ch", "ч": "ch", "Ш": "Sh", "ш": "sh", "Щ": "Shch", "щ": "shch",
    "Ъ": "", "ъ": "", "Ы": "Y", "ы": "y", "Ь": "", "ь": "",
    "Э": "E", "э": "e", "Ю": "Yu", "ю": "yu", "Я": "Ya", "я": "ya",
})


def _latinize_project_name(value: Any) -> str:
    """Enforce Latin spelling for a source-language project identifier.

    The model remains responsible for translating a descriptive project title.
    This deterministic final step protects the address and proper-name case
    when a Russian identifier is returned unchanged.
    """
    name = str(value or "").strip()
    return name.translate(_CYRILLIC_TO_LATIN) if name else name


def normalize_detection_identity_fields(
    result: dict[str, Any],
    *,
    company_id: str,
    file_name: str,
) -> dict[str, Any]:
    """Make transport identity fields authoritative before schema validation."""
    rfq_run = result.get("rfq_run")
    detected_objects = result.get("detected_objects")
    if not isinstance(rfq_run, dict) or not isinstance(detected_objects, list):
        return result

    run_id = rfq_run.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        return result

    rfq_run["company_id"] = company_id
    rfq_run["file_name"] = file_name
    rfq_run["project_name"] = _latinize_project_name(rfq_run.get("project_name"))

    # File quality is advisory technical metadata. Claude's structured-output
    # transport receives the integer shape but not JSON Schema min/max, so an
    # out-of-range provider value must not discard an otherwise valid object
    # registry and evidence package.
    quality_by_label = {
        "unreadable": 0,
        "very_low_information": 1,
        "partial_information": 2,
        "detailed_drawings": 3,
        "production_ready": 4,
    }
    label_by_quality = {value: key for key, value in quality_by_label.items()}
    label = str(rfq_run.get("file_quality_label") or "").strip().casefold()
    raw_quality = rfq_run.get("file_quality_level")
    quality: int | None = None
    if isinstance(raw_quality, int) and not isinstance(raw_quality, bool):
        quality = raw_quality
    elif isinstance(raw_quality, float) and raw_quality.is_integer():
        quality = int(raw_quality)
    if quality is None or not 0 <= quality <= 4:
        quality = quality_by_label.get(label)
    if quality is None:
        quality = 0 if rfq_run.get("status") == "unreadable" else 2
    rfq_run["file_quality_level"] = quality
    if label not in quality_by_label:
        rfq_run["file_quality_label"] = label_by_quality[quality]

    raw_confidence = rfq_run.get("file_quality_confidence")
    try:
        confidence = float(raw_confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    rfq_run["file_quality_confidence"] = (
        min(100.0, max(0.0, confidence)) if math.isfinite(confidence) else 0.0
    )
    for detected_object in detected_objects:
        if not isinstance(detected_object, dict):
            continue
        detected_object["run_id"] = run_id
        detected_object["company_id"] = company_id

    return result


def discard_degenerate_evidence_regions(result: dict[str, Any]) -> dict[str, Any]:
    """Keep full-page evidence when the model returns a zero-area retrieval box.

    Evidence regions are optional retrieval aids. A cited page remains valid and
    useful to Estimation without one, while a zero-area region can never be
    inspected. Do not conceal malformed coordinates here: strict validation
    continues to reject non-numeric, negative, missing, or extra coordinates.
    """
    objects = result.get("detected_objects")
    if not isinstance(objects, list):
        return result

    bbox_keys = {
        "top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y",
    }

    def is_degenerate_bbox(value: Any) -> bool:
        if not isinstance(value, dict) or set(value) != bbox_keys:
            return False
        if any(
            not isinstance(value[key], (int, float)) or value[key] < 0
            for key in bbox_keys
        ):
            return False
        return (
            value["bottom_right_x"] <= value["top_left_x"]
            or value["bottom_right_y"] <= value["top_left_y"]
        )

    for detected_object in objects:
        if not isinstance(detected_object, dict):
            continue
        for page_ref in detected_object.get("evidence_page_refs") or []:
            if not isinstance(page_ref, dict):
                continue
            regions = page_ref.get("regions")
            if isinstance(regions, list):
                page_ref["regions"] = [
                    region for region in regions if not is_degenerate_bbox(region)
                ]
            if is_degenerate_bbox(page_ref.get("presentation_preview_bbox")):
                page_ref.pop("presentation_preview_bbox", None)
    return result


def apply_benchmark_run_suffix(result: dict[str, Any]) -> dict[str, Any]:
    """Isolate parallel benchmark persistence without changing the Claude request."""
    suffix = str(os.getenv("BENCHMARK_RUN_SUFFIX", "") or "").strip()
    if not suffix:
        return result

    safe_suffix = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in suffix
    ).strip("_")
    if not safe_suffix:
        return result

    rfq_run = result.get("rfq_run")
    detected_objects = result.get("detected_objects")
    if not isinstance(rfq_run, dict) or not isinstance(detected_objects, list):
        return result

    run_id = str(rfq_run.get("run_id") or "").strip()
    if not run_id:
        return result

    unique_suffix = ""
    unique_enabled = str(os.getenv("BENCHMARK_UNIQUE_RUN_ID", "false") or "false")
    if unique_enabled.strip().lower() in {"1", "true", "yes", "on"}:
        unique_suffix = "_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    benchmark_run_id = f"{run_id}_{safe_suffix}{unique_suffix}"
    rfq_run["run_id"] = benchmark_run_id
    for detected_object in detected_objects:
        if isinstance(detected_object, dict):
            detected_object["run_id"] = benchmark_run_id
    return result


def build_agent_usage_event(
    *,
    agent_name: str,
    operation: str,
    company_id: str,
    run_id: str | None,
    file_name: str | None,
    object_id: str | None,
    object_name: str | None,
    model: str,
    prompt_version: str,
    response: Any,
    started_at: str,
    finished_at: str,
    request_diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a DB-ready usage event from Anthropic response metadata."""
    usage = getattr(response, "usage", None)
    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    cache_creation_input_tokens = int(
        getattr(usage, "cache_creation_input_tokens", 0) or 0
    )
    cache_read_input_tokens = int(getattr(usage, "cache_read_input_tokens", 0) or 0)
    costs = calculate_llm_cost_usd(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    started = datetime.fromisoformat(started_at)
    finished = datetime.fromisoformat(finished_at)
    duration_seconds = round(max(0.0, (finished - started).total_seconds()), 3)

    raw_usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_creation_input_tokens": cache_creation_input_tokens,
        "cache_read_input_tokens": cache_read_input_tokens,
        "duration_seconds": duration_seconds,
        "cost_category": agent_cost_category(agent_name),
    }
    if request_diagnostics:
        raw_usage.update(request_diagnostics)

    generation_seconds = raw_usage.get("generation_after_first_token_seconds")
    if isinstance(generation_seconds, (int, float)) and generation_seconds > 0:
        raw_usage["output_tokens_per_generation_second"] = round(
            output_tokens / generation_seconds,
            3,
        )

    return {
        "company_id": company_id,
        "run_id": run_id,
        "file_name": file_name,
        "object_id": object_id,
        "object_name": object_name,
        "agent_name": agent_name,
        "operation": operation,
        "model": model,
        "prompt_version": prompt_version,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": costs["input_cost_usd"],
        "output_cost_usd": costs["output_cost_usd"],
        "total_cost_usd": costs["total_cost_usd"],
        "status": "succeeded",
        "duration_seconds": duration_seconds,
        "started_at": started_at,
        "finished_at": finished_at,
        "raw_usage": raw_usage,
    }


def extract_text_from_claude_response(response: Any) -> str:
    """
    Anthropic Messages responses usually return JSON text in response.content[0].text.
    This function is defensive in case the SDK returns multiple content blocks.
    """
    texts: list[str] = []

    for block in response.content:
        block_type = getattr(block, "type", None)

        if block_type == "text":
            text = getattr(block, "text", "")
            if text:
                texts.append(text)

    raw_text = "\n".join(texts).strip()

    if not raw_text:
        raise RuntimeError("Claude returned no text content")

    return raw_text


def run_anthropic_detection_agent(
    *,
    file_name: str,
    company_id: str,
    file_bytes: bytes,
    ocr_package: dict[str, Any] | None = None,
    page_images: list[bytes] | None = None,
    page_image_diagnostics: dict[str, Any] | None = None,
    model: str | None = None,
    attempt_label: str = "primary",
    locked_registry: dict[str, Any] | None = None,
    focus_regions: list[dict[str, Any]] | None = None,
    page_image_numbers: list[int] | None = None,
) -> dict:
    """
    Real Claude-backed Detection Agent.

    Input:
    - file_name: original uploaded file name
    - company_id: current company id
    - file_bytes: uploaded PDF bytes

    Output:
    - validated detection_result dict compatible with Supabase repositories
    """
    selected_model = model or get_secret(
        "CLAUDE_DETECTION_MODEL",
        DEFAULT_CLAUDE_DETECTION_MODEL,
    )

    if not selected_model:
        selected_model = DEFAULT_CLAUDE_DETECTION_MODEL

    client = get_anthropic_client()
    cache_enabled = detection_input_cache_enabled()
    prompt = (
        load_detection_agent_without_naming_prompt()
        if detection_naming_split_enabled()
        else load_detection_agent_prompt()
    )
    user_text = build_detection_user_text(
        file_name=file_name,
        company_id=company_id,
        ocr_package=ocr_package,
    )
    if locked_registry is not None:
        user_text += "\n\nLOCKED OBJECT REGISTRY:\n" + json.dumps(locked_registry, ensure_ascii=False) + "\nReturn exactly these objects in this order. Preserve object_id, transport_label as object_name, quantity and quantity_explicit. Do not add, remove, split or merge objects."
    claude_schema = strip_schema_for_claude(DETECTION_RESULT_JSON_SCHEMA)
    system_content = build_detection_system_content(
        cache_enabled=cache_enabled,
        prompt=prompt,
    )
    prompt_sha256 = _sha256_text(prompt)
    schema_sha256 = _sha256_text(_canonical_json(claude_schema))
    system_content_sha256 = _sha256_text(_canonical_json(system_content))
    user_text_sha256 = _sha256_text(user_text)
    pdf_sha256 = _sha256_bytes(file_bytes)
    document_route = "jpeg_pages_96dpi" if page_images else "inline_base64"
    request_fingerprint = _sha256_text(
        _canonical_json(
            {
                "model": selected_model,
                "max_tokens": 8192,
                "temperature": DETECTION_LOCKED_EVIDENCE_HANDOFF_TEMPERATURE,
                "prompt_sha256": prompt_sha256,
                "schema_sha256": schema_sha256,
                "system_content_sha256": system_content_sha256,
                "user_text_sha256": user_text_sha256,
                "pdf_sha256": pdf_sha256,
                "document_route": document_route,
                "cache_enabled": cache_enabled,
                "streaming": True,
            }
        )
    )

    response, stream_diagnostics = create_claude_message_streamed(
        client,
        model=selected_model,
        max_tokens=8192,
        temperature=DETECTION_LOCKED_EVIDENCE_HANDOFF_TEMPERATURE,
        system=system_content,
        messages=[
            {
                "role": "user",
                "content": append_detection_focus_regions(build_detection_content_blocks(
                    file_name=file_name,
                    file_bytes=file_bytes,
                    user_text=user_text,
                    page_images=page_images,
                    page_image_numbers=page_image_numbers,
                    cache_enabled=cache_enabled,
                ), focus_regions),
            }
        ],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": claude_schema,
            }
        },
    )
    stream_diagnostics["temperature"] = DETECTION_LOCKED_EVIDENCE_HANDOFF_TEMPERATURE
    raw_text = extract_text_from_claude_response(response)

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Claude returned invalid JSON. Raw response starts with: {raw_text[:500]}"
        ) from exc

    result = normalize_detection_identity_fields(
        result,
        company_id=company_id,
        file_name=file_name,
    )
    result = discard_degenerate_evidence_regions(result)
    result = apply_benchmark_run_suffix(result)
    validated = validate_detection_result(result)
    response_usage = getattr(response, "usage", None)
    usage_details = (
        response_usage.model_dump(mode="json")
        if hasattr(response_usage, "model_dump")
        else {}
    )
    stream_diagnostics.update(
        {
            "prompt_sha256": prompt_sha256,
            "schema_sha256": schema_sha256,
            "effective_prompt_text": prompt,
            "claude_output_schema": claude_schema,
            "system_content_sha256": system_content_sha256,
            "user_text_sha256": user_text_sha256,
            "pdf_sha256": pdf_sha256,
            "document_route": document_route,
            "page_image_diagnostics": dict(page_image_diagnostics or {}),
            "request_fingerprint": request_fingerprint,
            "response_id": str(getattr(response, "id", "") or ""),
            "response_model": str(getattr(response, "model", "") or ""),
            "stop_reason": str(getattr(response, "stop_reason", "") or ""),
            "stop_sequence": getattr(response, "stop_sequence", None),
            "response_character_count": len(raw_text),
            "detected_object_count": len(validated["detected_objects"]),
            "max_tokens": 8192,
            "cache_enabled": cache_enabled,
            "benchmark_variant": str(os.getenv("BENCHMARK_VARIANT", "") or ""),
            "benchmark_source_id": str(
                os.getenv("BENCHMARK_SOURCE_ID", "") or ""
            ),
            "benchmark_run_suffix": str(
                os.getenv("BENCHMARK_RUN_SUFFIX", "") or ""
            ),
            "attempt_label": attempt_label,
            "sdk_usage": usage_details,
        }
    )
    validated["_agent_usage"] = build_agent_usage_event(
        agent_name="detection",
        operation="rfq_detection",
        company_id=company_id,
        run_id=validated["rfq_run"].get("run_id"),
        file_name=file_name,
        object_id=None,
        object_name=None,
        model=selected_model,
        prompt_version=(
            DETECTION_NO_NAMING_PROMPT_VERSION
            if detection_naming_split_enabled()
            else DETECTION_PROMPT_VERSION
        ),
        response=response,
        started_at=stream_diagnostics["request_started_at"],
        finished_at=stream_diagnostics["request_finished_at"],
        request_diagnostics=stream_diagnostics,
    )
    return validated


def run_anthropic_detection_agent_with_fallback(
    *,
    file_name: str,
    company_id: str,
    file_bytes: bytes,
    ocr_package: dict[str, Any] | None = None,
    page_images: list[bytes] | None = None,
    page_image_diagnostics: dict[str, Any] | None = None,
    primary_model_override: str | None = None,
    locked_registry: dict[str, Any] | None = None,
    focus_regions: list[dict[str, Any]] | None = None,
    page_image_numbers: list[int] | None = None,
    allow_sonnet_fallback: bool = False,
) -> dict:
    """
    First tries Haiku. If anything breaks, retries once with Sonnet.
    """
    primary_model = primary_model_override or get_secret(
        "CLAUDE_DETECTION_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL
    )
    fallback_model = get_secret(
        "CLAUDE_DETECTION_FALLBACK_MODEL",
        DEFAULT_CLAUDE_FALLBACK_MODEL,
    )

    try:
        return run_anthropic_detection_agent(
            file_name=file_name,
            company_id=company_id,
            file_bytes=file_bytes,
            ocr_package=ocr_package,
            page_images=page_images,
            page_image_diagnostics=page_image_diagnostics,
            model=primary_model,
            attempt_label="primary",
            locked_registry=locked_registry,
            focus_regions=focus_regions,
            page_image_numbers=page_image_numbers,
        )
    except Exception as primary_error:
        print(f"[Detection Agent] Primary Claude model failed: {primary_error}")

        if not allow_sonnet_fallback or not fallback_model or fallback_model == primary_model:
            raise

        return run_anthropic_detection_agent(
            file_name=file_name,
            company_id=company_id,
            file_bytes=file_bytes,
            ocr_package=ocr_package,
            page_images=page_images,
            page_image_diagnostics=page_image_diagnostics,
            model=fallback_model,
            attempt_label="fallback",
            locked_registry=locked_registry,
            focus_regions=focus_regions,
            page_image_numbers=page_image_numbers,
        )


def run_anthropic_detection_agent_from_path(
    *,
    pdf_path: str | Path,
    company_id: str,
) -> dict:
    """
    Useful for terminal tests with a local PDF.
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    return run_anthropic_detection_agent_with_fallback(
        file_name=path.name,
        company_id=company_id,
        file_bytes=path.read_bytes(),
        ocr_package=None,
    )
