"""V3 material-only Object Facts extraction.

This is the active extraction boundary for the Material Resolver and Material
Engine. It deliberately has no labor, machinery, price or overhead behavior.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
import json
from pathlib import Path
import re
from typing import Any, AbstractSet, Mapping, Sequence

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_AGENT_MODEL,
    build_agent_usage_event,
    create_claude_message,
    extract_text_from_claude_response,
    get_anthropic_client,
    get_secret,
)
from use_cases.estimation_v3_material_contract import (
    COMPACT_PART_KEYS,
    MATERIAL_FACTS_V3_VERSION,
    SPECIFICATION_KEYS,
    validate_material_facts_v3,
)


# The unit and purchasable quantity belong to the selected supply candidate,
# not to the vision model.  Bump the extraction version so cached facts that
# contained model-guessed units can never feed the current Material Engine.
ESTIMATION_V3_MATERIAL_FACTS_AGENT_VERSION = "estimation_material_facts_v3_7"
PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_v3_material_facts_prompt.md"
MAX_OUTPUT_TOKENS = 8_000
TIMEOUT_SECONDS = 180.0


def _number(value: Any, *, positive: bool = False) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if not positive or result > 0 else None


def _net_unit(value: Any) -> str | None:
    """Accept only a material's net measurement, never a guessed purchase unit."""
    normalized = " ".join(str(value or "").casefold().split())
    return {
        "m2": "m²", "m²": "m²", "sqm": "m²", "square metre": "m²", "square meter": "m²",
        "m": "m", "metre": "m", "meter": "m", "lm": "m",
        "mm": "mm", "kg": "kg", "l": "l", "piece": "piece", "sheet": "sheet",
    }.get(normalized)


_FAMILY_ALIASES = {
    "metal_sheet": "sheet_metal",
    "metal_profile": "metal_profile_angle_channel",
    "metal_angle": "metal_profile_angle_channel",
}
_AREA_PROXY_FAMILIES = frozenset({
    "acrylic_pmma", "aluminium_composite_panel", "compact_laminate",
    "composite_sandwich_panel", "engineered_quartz_mineral_hybrid",
    "fibreboard_hardboard", "glass", "hpl_cpl", "lightweight_sandwich_panel",
    "mdf_hdf", "melamine_faced_particleboard", "mirror", "natural_stone_slab",
    "osb", "particleboard", "plywood", "plywood_special", "polycarbonate_petg_pvc_abs",
    "porcelain_ceramic_slab", "sheet_metal", "sheet_plastic", "sintered_ultra_compact_surface",
    "solid_surface", "terrazzo_engineered_agglomerate", "timber_solid_wood_panel",
})
_LINEAR_PROXY_FAMILIES = frozenset({
    "edge_banding", "metal_flat_bar", "metal_profile_angle_channel",
    "metal_round_bar_rod_wire", "metal_tube", "wood_veneer",
})
_EXCLUDED_MATERIAL_FAMILIES = frozenset({
    "packaging_material", "paint_lacquer_stain", "powder_coating", "primer",
    "filler_hardener_thinner", "hardware_fastener",
})


def _family_code(value: Any, families: AbstractSet[str]) -> str | None:
    normalized = re.sub(r"[\s-]+", "_", str(value or "").strip().casefold())
    normalized = _FAMILY_ALIASES.get(normalized, normalized)
    return normalized if normalized in families else None


def _positive_dimension(value: Any) -> float | None:
    return _number(value, positive=True)


def _envelope_pair(dimensions: Mapping[str, Any]) -> tuple[float, float] | None:
    width = _positive_dimension(dimensions.get("width"))
    depth = _positive_dimension(dimensions.get("depth"))
    height = _positive_dimension(dimensions.get("height"))
    for pair in ((width, height), (width, depth), (height, depth)):
        if pair[0] is not None and pair[1] is not None:
            return pair
    return None


def _deterministic_net_proxy(
    *, family: str, dimensions: Mapping[str, Any], object_quantity: float,
) -> tuple[float, str] | None:
    """Return a reviewable net-demand proxy from the detected object envelope.

    This is only used when the visual model established material identity but
    supplied neither a cut list nor a quantity. It supplies an Estimation
    assumption, never a catalog format or supplier price.
    """
    pair = _envelope_pair(dimensions)
    if family in _AREA_PROXY_FAMILIES and pair:
        return (pair[0] * pair[1] / 1_000_000 * object_quantity, "m²")
    if family in _LINEAR_PROXY_FAMILIES and pair:
        return (2 * (pair[0] + pair[1]) / 1_000 * object_quantity, "m")
    if family.startswith("hardware_") or family == "purchased_fabricated_component":
        return (object_quantity, "piece")
    return None


def _explicit_material_supplements(
    *, object_payload: Mapping[str, Any], families: AbstractSet[str], existing_families: set[str],
) -> list[tuple[str, str, dict[str, Any]]]:
    """Recover material groups explicitly named by Detection if the model omitted them."""
    text = " ".join(
        str(object_payload.get(key) or "")
        for key in ("detected_materials", "notes")
    )
    lowered = text.casefold()
    rules: tuple[tuple[str, str, str], ...] = (
        (r"\b(?:perforated\s+)?(?:metal|steel)\s+sheet\b", "sheet_metal", "perforated metal sheet"),
        (r"\b(?:metal|steel)\s+(?:square\s+)?(?:tube|profile)\b", "metal_tube", "metal tube"),
        (r"\b(?:metal|steel)\s+(?:angle|channel)\b|\bangle\s+frame\b", "metal_profile_angle_channel", "metal angle profile"),
        (r"\b(?:overhead|sliding|continuous)\s+(?:metal\s+)?track\b", "hardware_door_system", "door track system"),
        (r"\b(?:corner\s+)?bracket\b", "hardware_mounting_part", "corner bracket"),
        (r"\b(?:mdf|hdf)\b", "mdf_hdf", "MDF"),
    )
    supplements: list[tuple[str, str, dict[str, Any]]] = []
    for pattern, family, name in rules:
        if family not in families or family in existing_families or not re.search(pattern, lowered):
            continue
        specifications: dict[str, Any] = {}
        if family == "sheet_metal":
            match = re.search(r"(?:perforated\s+)?(?:metal|steel)\s+sheet\s*(\d+(?:\.\d+)?)\s*mm", lowered)
            if match:
                specifications["thickness_mm"] = float(match.group(1))
        if family == "metal_tube":
            match = re.search(r"(?:metal|steel)\s+(?:square\s+)?(?:tube|profile)\s*(\d+\s*[x×]\s*\d+)", lowered)
            if match:
                specifications["profile_section"] = re.sub(r"\s*×\s*", "x", match.group(1))
        supplements.append((family, name, specifications))
        existing_families.add(family)
    return supplements


def _identifier(value: Any, default: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9_.:-]+", "_", str(value or "").strip().casefold()).strip("_") or default
    result, suffix = base, 2
    while result in used:
        result, suffix = f"{base}_{suffix}", suffix + 1
    used.add(result)
    return result


def _sparse(value: Any) -> dict[str, Any]:
    return {
        str(key): child for key, child in value.items()
        if key in SPECIFICATION_KEYS and child not in (None, "", "unknown")
    } if isinstance(value, Mapping) else {}


def _normalise_material_specification(
    *, family: str, source_name: str, value: Any,
) -> dict[str, Any]:
    """Apply only deterministic identity facts that the source name proves.

    A bare MDF/HDF material name proves the board type.  In an object preview,
    terms such as ``white matte`` and ``color-matched`` describe the object's
    paint finish, not a purchasable MDF face.  The catalog's base sheet is raw;
    coatings remain outside this material-only contract.
    """
    specification = _sparse(value)
    if family != "mdf_hdf":
        return specification

    name = " ".join(source_name.casefold().replace("-", " ").split())
    if re.search(r"\bhdf\b|хдф|\bמדף\b", name):
        specification["board_type"] = "hdf"
    elif re.search(r"\bmdf\b|мдф|\bmdf\b", name):
        specification["board_type"] = "mdf"
    else:
        return specification

    surface = " ".join(str(specification.get("surface") or "").casefold().split())
    if not surface or any(marker in surface for marker in (
        "white matte", "white mat", "color-matched", "colour-matched",
        "paint", "wood-tone", "wood tone",
    )):
        specification["surface"] = "raw"
    return specification


def _json_object(text: str) -> Mapping[str, Any]:
    value = str(text or "").strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if len(lines) < 3 or lines[-1].strip() != "```":
            raise ValueError("V3 material facts returned an invalid JSON fence")
        value = "\n".join(lines[1:-1]).strip()
    parsed = json.loads(value)
    if not isinstance(parsed, Mapping):
        raise ValueError("V3 material facts must be a JSON object")
    return parsed


def _expand(
    compact: Mapping[str, Any], row: Mapping[str, Any], families: AbstractSet[str],
) -> dict[str, Any]:
    payload = row["input_payload"]
    object_payload = payload["object"]
    preview = str((payload.get("evidence") or {}).get("primary_preview_ref") or "")
    materials, reviews, material_ids = [], [], set()
    for index, raw in enumerate(compact.get("m") or [], start=1):
        if not isinstance(raw, Mapping):
            continue
        family = _family_code(raw.get("f"), families)
        if family is None or family in _EXCLUDED_MATERIAL_FAMILIES:
            continue
        requirement_id = _identifier(raw.get("id"), f"m{index}", material_ids)
        source_name = str(raw.get("n") or family)
        materials.append({
            "requirement_id": requirement_id,
            "source_name": source_name,
            "family": family,
            "specification": _normalise_material_specification(
                family=family, source_name=source_name, value=raw.get("s"),
            ),
            # This is a net physical requirement, never a guessed supplier
            # pack, bar or sheet. Resolver supplies the purchasable form.
            "quantity": _number(raw.get("q"), positive=True),
            "unit": _net_unit(raw.get("u")),
            "evidence_refs": [preview],
        })
    for family, source_name, specification in _explicit_material_supplements(
        object_payload=object_payload,
        families=families,
        existing_families={str(material["family"]) for material in materials},
    ):
        materials.append({
            "requirement_id": _identifier(None, f"m{len(materials) + 1}", material_ids),
            "source_name": source_name,
            "family": family,
            "specification": _normalise_material_specification(
                family=family, source_name=source_name, value=specification,
            ),
            "quantity": None,
            "unit": None,
            "evidence_refs": [preview],
        })
    parts, part_ids = [], set()
    for index, raw in enumerate(compact.get("p") or [], start=1):
        if not isinstance(raw, Mapping):
            continue
        material_id = str(raw.get("m") or "")
        quantity = _number(raw.get("q"), positive=True)
        length, width = _number(raw.get("l"), positive=True), _number(raw.get("w"), positive=True)
        if material_id not in material_ids or quantity is None or length is None or width is None:
            continue
        parts.append({
            "part_id": _identifier(raw.get("id"), f"p{index}", part_ids),
            "material_requirement_id": material_id,
            "quantity": quantity,
            "length_mm": length,
            "width_mm": width,
            "rotation_allowed": str(raw.get("r") or "yes").casefold() != "no",
            "evidence_refs": [preview],
        })
    object_dimensions = dict(object_payload.get("dimensions") or {})
    object_quantity = _number(object_payload.get("quantity"), positive=True) or 1.0
    material_ids_with_parts = {str(part["material_requirement_id"]) for part in parts}
    for material in materials:
        if material["quantity"] is not None or material["requirement_id"] in material_ids_with_parts:
            continue
        proxy = _deterministic_net_proxy(
            family=str(material["family"]), dimensions=object_dimensions,
            object_quantity=object_quantity,
        )
        if proxy is None:
            continue
        material["quantity"], material["unit"] = proxy
        reviews.append({
            "code": "material_net_demand_assumption",
            "severity": "warning",
            "path": f"materials.{material['requirement_id']}",
            "message": "Net demand is an object-envelope assumption pending detailed geometry",
            "evidence_refs": [preview],
        })
    if not materials:
        reviews.append({
            "code": "material_requirement_missing", "severity": "blocking",
            "path": "materials", "message": "No valid material demand was extracted",
            "evidence_refs": [preview],
        })
    dimensions = list(compact.get("d") or []) + [0, 0, 0]
    facts = {
        "contract_version": MATERIAL_FACTS_V3_VERSION,
        "input_id": str(row["input_id"]),
        "object_input_revision": int(row.get("object_input_revision") or 1),
        "run_id": payload["run_id"], "company_id": payload["company_id"],
        "object_id": object_payload["object_id"], "object_name": object_payload["object_name"],
        "quantity": object_payload.get("quantity") or 1,
        "status": "review_required" if reviews else "ready",
        "dimensions_mm": {
            key: _number(value, positive=True) if value else None
            for key, value in zip(("width", "depth", "height"), dimensions[:3])
        },
        "materials": materials,
        "parts": parts,
        "review_items": reviews,
        "primary_preview_ref": preview,
    }
    return validate_material_facts_v3(facts, allowed_material_families=families)


def run_estimation_v3_material_facts_agent(
    *, inputs: Sequence[Mapping[str, Any]], allowed_material_families: AbstractSet[str],
    preview_bytes_by_input: Mapping[str, bytes],
    pricing_key_fields_by_family: Mapping[str, Sequence[str]] | None = None,
    family_alias_context: Mapping[str, Mapping[str, Any]] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    if not inputs:
        raise ValueError("inputs are required")
    selected_model = model or get_secret("CLAUDE_ESTIMATION_V3_PAGE_MODEL", DEFAULT_CLAUDE_AGENT_MODEL)
    targets = [{
        "id": row["input_payload"]["object"]["object_id"],
        "name": row["input_payload"]["object"]["object_name"],
        "quantity": row["input_payload"]["object"].get("quantity") or 1,
        "evidence_backed_object_handoff": {
            "dimensions": row["input_payload"]["object"].get("dimensions"),
            "description": row["input_payload"]["object"].get("notes"),
            "detected_materials": row["input_payload"]["object"].get("detected_materials"),
        },
    } for row in inputs]
    request = {
        "targets": targets, "allowed_material_families": sorted(allowed_material_families),
        "specification_keys": list(SPECIFICATION_KEYS), "part_keys": list(COMPACT_PART_KEYS),
        "pricing_key_fields_by_family": {
            str(family): list(fields)
            for family, fields in sorted((pricing_key_fields_by_family or {}).items())
        },
        "family_alias_context": {
            str(family): dict(context)
            for family, context in sorted((family_alias_context or {}).items())
        },
    }
    content: list[dict[str, Any]] = []
    for row in inputs:
        input_id = str(row["input_id"])
        preview = preview_bytes_by_input.get(input_id)
        if not preview:
            raise ValueError(f"source preview is missing for input {input_id}")
        content.extend([
            {"type": "text", "text": json.dumps({"source_preview_for_object_id": row["input_payload"]["object"]["object_id"]})},
            {"type": "image", "source": {"type": "base64", "media_type": "image/webp", "data": base64.b64encode(preview).decode("ascii")}},
        ])
    content.append({"type": "text", "text": json.dumps(request, ensure_ascii=False, separators=(",", ":"))})
    started_at = datetime.now(UTC).isoformat()
    response = create_claude_message(
        get_anthropic_client().with_options(timeout=TIMEOUT_SECONDS, max_retries=0),
        model=selected_model, max_tokens=MAX_OUTPUT_TOKENS, temperature=0,
        system=PROMPT_PATH.read_text(encoding="utf-8").strip(),
        messages=[{"role": "user", "content": content}],
    )
    compact = _json_object(extract_text_from_claude_response(response))
    by_object = {str(item.get("id") or ""): item for item in compact.get("objects") or [] if isinstance(item, Mapping)}
    facts_by_input, failed = {}, {}
    for row in inputs:
        input_id, object_id = str(row["input_id"]), str(row["input_payload"]["object"]["object_id"])
        try:
            facts_by_input[input_id] = _expand(by_object.get(object_id) or {}, row, allowed_material_families)
        except Exception as exc:
            failed[input_id] = f"{type(exc).__name__}: {exc}"
    first = inputs[0]["input_payload"]
    usage = build_agent_usage_event(
        agent_name="estimation_v3_material_facts", operation="material_fact_extraction",
        company_id=str(first.get("company_id") or ""), run_id=str(first.get("run_id") or ""),
        file_name=str((first.get("document") or {}).get("file_name") or ""),
        object_id="page-batch", object_name=f"{len(inputs)} objects", model=selected_model,
        prompt_version=ESTIMATION_V3_MATERIAL_FACTS_AGENT_VERSION, response=response,
        started_at=started_at, finished_at=datetime.now(UTC).isoformat(),
        request_diagnostics={"object_count": len(inputs), "material_only": True},
    )
    return {"facts_by_input": facts_by_input, "failed": failed, "usage_event": usage}
