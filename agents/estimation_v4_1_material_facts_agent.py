"""Bounded, evidence-indexed material extraction for Estimation V4.1.

V4.1 deliberately does not derive cut rectangles or envelope proxies.  Every
Cloud call receives a disjoint bounded subset of the immutable V4 evidence
package, and every source page must be accounted for in its response.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
import json
import re
from pathlib import Path
from types import SimpleNamespace
from threading import Thread
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
    MATERIAL_FACTS_V4_1_VERSION,
    SPECIFICATION_KEYS,
    validate_material_facts_v4_1,
)


ESTIMATION_V4_1_MATERIAL_FACTS_AGENT_VERSION = "estimation_material_facts_v4_1"
PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_v4_1_material_facts_prompt.md"
MAX_OUTPUT_TOKENS = 4_000
TIMEOUT_SECONDS = 90.0
MAX_SOURCE_PAGES_PER_CALL = 6
_EXCLUDED_MATERIAL_FAMILIES = frozenset({
    "packaging_material", "paint_lacquer_stain", "powder_coating", "primer",
    "filler_hardener_thinner", "hardware_fastener",
})
_TOPIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("hardware", re.compile(r"\b(hinge|handle|slide|runner|track|rail|bracket|mechanism|hardware|петл|ручк|направляющ|фурнитур)\b", re.I)),
    ("surfaces", re.compile(r"\b(facade|front|door|countertop|worktop|glass|stone|фасад|двер|столешниц|стекл|камн)\b", re.I)),
    ("structure", re.compile(r"\b(carcass|cabinet|shelf|panel|mdf|hdf|plywood|particleboard|корпус|шкаф|полк|панел|мдф|фанер)\b", re.I)),
    ("specification", re.compile(r"\b(specification|schedule|bom|material|finish|спецификац|ведомост|материал)\b", re.I)),
)
_MATERIAL_SIGNAL = re.compile(
    r"\b(mdf|hdf|plywood|particleboard|melamine|laminate|steel|metal|aluminium|glass|stone|hinge|handle|slide|track|rail|profile|tube|мдф|фанер|металл|стекл|камн|петл|ручк|направляющ|профил)\b",
    re.I,
)


def _create_message_with_hard_timeout(client: Any, *, timeout_seconds: float, **kwargs: Any) -> Any:
    """Bound every V4.1 cloud request without sharing V3's call binding."""
    result: list[Any] = []
    failure: list[BaseException] = []

    def invoke() -> None:
        try:
            result.append(create_claude_message(client, **kwargs))
        except BaseException as exc:
            failure.append(exc)

    request_thread = Thread(target=invoke, name="estimation-v4-1-material-facts", daemon=True)
    request_thread.start()
    request_thread.join(timeout=max(0.0, timeout_seconds))
    if request_thread.is_alive():
        raise RuntimeError(f"Estimation V4.1 material-facts request exceeded the {timeout_seconds:.0f}-second limit.")
    if failure:
        raise failure[0]
    if not result:
        raise RuntimeError("Estimation V4.1 material-facts request ended without a response.")
    return result[0]


def _json_object(text: str) -> Mapping[str, Any]:
    value = str(text or "").strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if len(lines) < 2:
            raise ValueError("V4.1 material facts returned an invalid JSON fence")
        value = "\n".join(lines[1:]).strip()
        if value.endswith("```"):
            value = value[:-3].strip()
    first, last = value.find("{"), value.rfind("}")
    if first < 0 or last < first or value[:first].strip() or value[last + 1:].strip():
        raise ValueError("V4.1 material facts must contain one raw JSON object")
    value = value[first:last + 1]
    parsed = json.loads(value)
    if not isinstance(parsed, Mapping):
        raise ValueError("V4.1 material facts must be a JSON object")
    return parsed


def _positive_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _net_unit(value: Any) -> str | None:
    normalized = " ".join(str(value or "").casefold().split())
    return {
        "m2": "m²", "m²": "m²", "sqm": "m²", "square metre": "m²", "square meter": "m²",
        "m": "m", "metre": "m", "meter": "m", "lm": "m",
        "mm": "mm", "kg": "kg", "l": "l", "piece": "piece", "sheet": "sheet",
    }.get(normalized)


def _identifier(value: Any, default: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9_.:-]+", "_", str(value or "").strip().casefold()).strip("_") or default
    candidate, suffix = base, 2
    while candidate in used:
        candidate, suffix = f"{base}_{suffix}", suffix + 1
    used.add(candidate)
    return candidate


def _family_code(value: Any, families: AbstractSet[str]) -> str | None:
    normalized = re.sub(r"[\s-]+", "_", str(value or "").strip().casefold())
    aliases = {"metal_sheet": "sheet_metal", "metal_profile": "metal_profile_angle_channel", "metal_angle": "metal_profile_angle_channel"}
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in families else None


def _sparse_specification(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): child for key, child in value.items()
        if key in SPECIFICATION_KEYS and child not in (None, "", "unknown")
    }


def _page_text(payload: Mapping[str, Any], page_number: int) -> str:
    evidence = payload.get("evidence") or {}
    values: list[str] = []
    for kind in ("ocr_blocks", "ocr_literal_items"):
        for item in evidence.get(kind) or []:
            if isinstance(item, Mapping) and item.get("page_number") == page_number:
                values.append(str(item.get("text") or ""))
    return "\n".join(values)


def _topic_for_page(text: str) -> str:
    for topic, pattern in _TOPIC_PATTERNS:
        if pattern.search(text):
            return topic
    return "general"


def build_v4_1_evidence_batches(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Index every immutable source page once and form disjoint bounded calls."""
    object_payload = payload.get("object") or {}
    evidence = payload.get("evidence") or {}
    artifacts_by_page = {
        int(item.get("page_number")): dict(item)
        for item in evidence.get("artifacts") or []
        if isinstance(item, Mapping) and item.get("artifact_kind") == "page"
        and str(item.get("storage_ref") or "")
    }
    pages: list[dict[str, Any]] = []
    for page_ref in object_payload.get("evidence_pages") or []:
        if not isinstance(page_ref, Mapping):
            continue
        try:
            page_number = int(page_ref.get("page_number"))
        except (TypeError, ValueError):
            continue
        artifact = artifacts_by_page.get(page_number)
        if artifact is None:
            raise ValueError(f"V4.1 input has no full-page artifact for page {page_number}")
        text = _page_text(payload, page_number)
        pages.append({
            "page_number": page_number,
            "storage_ref": str(artifact["storage_ref"]),
            "regions": [dict(region) for region in page_ref.get("regions") or [] if isinstance(region, Mapping)],
            "topic": _topic_for_page(text),
            "material_signal_hint": "keyword" if _MATERIAL_SIGNAL.search(text) else "none",
            "ocr_blocks": [dict(item) for item in evidence.get("ocr_blocks") or [] if isinstance(item, Mapping) and item.get("page_number") == page_number],
            "ocr_literal_items": [dict(item) for item in evidence.get("ocr_literal_items") or [] if isinstance(item, Mapping) and item.get("page_number") == page_number],
        })
    if not pages:
        raise ValueError("V4.1 input has no evidence pages")
    if len({page["page_number"] for page in pages}) != len(pages):
        raise ValueError("V4.1 input repeats an evidence page")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for page in sorted(pages, key=lambda row: row["page_number"]):
        grouped.setdefault(str(page["topic"]), []).append(page)
    batches: list[dict[str, Any]] = []
    for topic in sorted(grouped):
        for start in range(0, len(grouped[topic]), MAX_SOURCE_PAGES_PER_CALL):
            selected = grouped[topic][start:start + MAX_SOURCE_PAGES_PER_CALL]
            batches.append({
                "batch_id": f"{topic}-{start // MAX_SOURCE_PAGES_PER_CALL + 1}",
                "topic": topic,
                "pages": selected,
            })
    covered = [page["page_number"] for batch in batches for page in batch["pages"]]
    if sorted(covered) != sorted(page["page_number"] for page in pages) or len(covered) != len(set(covered)):
        raise RuntimeError("V4.1 evidence batching did not preserve one-to-one page coverage")
    return batches


def _batch_request(
    *, batch: Mapping[str, Any], allowed_material_families: AbstractSet[str],
    pricing_key_fields_by_family: Mapping[str, Sequence[str]], family_alias_context: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    content: list[dict[str, Any]] = []
    pages = []
    for page in batch["pages"]:
        content.extend((
            {"type": "text", "text": json.dumps({"source_evidence_ref": page["storage_ref"], "page_number": page["page_number"]})},
            {"type": "image", "source": {"type": "base64", "media_type": "image/webp", "data": base64.b64encode(page["bytes"]).decode("ascii")}},
        ))
        pages.append({
            "page_number": page["page_number"], "source_evidence_ref": page["storage_ref"],
            "regions": page["regions"], "topic": page["topic"], "material_signal_hint": page["material_signal_hint"],
            "ocr_blocks": page["ocr_blocks"], "ocr_literal_items": page["ocr_literal_items"],
        })
    request = {
        "batch_id": batch["batch_id"], "topic": batch["topic"], "pages": pages,
        "allowed_material_families": sorted(allowed_material_families),
        "specification_keys": sorted(SPECIFICATION_KEYS),
        "pricing_key_fields_by_family": {str(key): list(value) for key, value in sorted(pricing_key_fields_by_family.items())},
        "family_alias_context": {str(key): dict(value) for key, value in sorted(family_alias_context.items())},
    }
    content.append({"type": "text", "text": json.dumps(request, ensure_ascii=False, separators=(",", ":"))})
    return content, request


def _response_for_batch(
    *, response: Mapping[str, Any], batch: Mapping[str, Any], families: AbstractSet[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if response.get("batch_id") != batch["batch_id"]:
        raise ValueError("V4.1 response batch_id does not match its request")
    pages = response.get("pages")
    if not isinstance(pages, list):
        raise ValueError("V4.1 response must account for every requested page")
    expected_pages = {int(page["page_number"]) for page in batch["pages"]}
    page_rows = {int(item.get("page_number")): item for item in pages if isinstance(item, Mapping) and str(item.get("page_number") or "").isdigit()}
    if set(page_rows) != expected_pages or len(page_rows) != len(pages):
        raise ValueError("V4.1 response page coverage is incomplete or duplicated")
    allowed_refs_by_page = {
        int(page["page_number"]): {
            str(page["storage_ref"]),
            *(str(item.get("block_ref")) for item in page["ocr_blocks"] + page["ocr_literal_items"] if item.get("block_ref")),
        }
        for page in batch["pages"]
    }
    raw_claims = response.get("claims")
    if not isinstance(raw_claims, list):
        raise ValueError("V4.1 response claims must be a list")
    claims_by_id = {str(item.get("id") or ""): item for item in raw_claims if isinstance(item, Mapping) and str(item.get("id") or "")}
    if len(claims_by_id) != len(raw_claims):
        raise ValueError("V4.1 response claim ids must be unique")
    reviews: list[dict[str, Any]] = []
    declared_claim_ids: set[str] = set()
    for page_number, page_row in page_rows.items():
        signal = str(page_row.get("material_signal") or "").casefold()
        claim_ids = page_row.get("claim_ids")
        if signal not in {"yes", "no", "uncertain"} or not isinstance(claim_ids, list) or not all(str(value) in claims_by_id for value in claim_ids):
            raise ValueError("V4.1 response page coverage has an invalid material declaration")
        if signal in {"yes", "uncertain"} and not claim_ids:
            reviews.append({
                "code": "material_signal_unresolved", "severity": "blocking", "path": f"pages[{page_number}]",
                "message": "Source page may contain material evidence without an extractable demand",
                "evidence_refs": [next(iter(allowed_refs_by_page[page_number]))],
            })
        declared_claim_ids.update(str(claim_id) for claim_id in claim_ids)
    if declared_claim_ids != set(claims_by_id):
        raise ValueError("V4.1 response claims must be assigned to a source page")
    claims: list[dict[str, Any]] = []
    for raw in raw_claims:
        refs = raw.get("e")
        if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) for ref in refs):
            raise ValueError("V4.1 material claims require exact evidence refs")
        batch_refs = set().union(*allowed_refs_by_page.values())
        if not all(ref in batch_refs for ref in refs):
            raise ValueError("V4.1 material claim cites evidence outside its batch")
        family = _family_code(raw.get("f"), families)
        if family is None or family in _EXCLUDED_MATERIAL_FAMILIES:
            continue
        claims.append({
            "raw": raw, "family": family, "evidence_refs": list(dict.fromkeys(refs)),
        })
    return claims, reviews


def _facts_from_claims(
    *, row: Mapping[str, Any], claims: Sequence[Mapping[str, Any]], reviews: list[dict[str, Any]],
    families: AbstractSet[str],
) -> dict[str, Any]:
    payload = row["input_payload"]
    object_payload = payload["object"]
    artifact_refs = [
        str(item.get("storage_ref")) for item in (payload.get("evidence") or {}).get("artifacts") or []
        if isinstance(item, Mapping) and item.get("artifact_kind") == "page" and item.get("storage_ref")
    ]
    used_ids: set[str] = set()
    materials: list[dict[str, Any]] = []
    fingerprints: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for index, claim in enumerate(claims, start=1):
        raw = claim["raw"]
        requirement_id = _identifier(raw.get("id"), f"m{index}", used_ids)
        quantity, unit = _positive_number(raw.get("q")), _net_unit(raw.get("u"))
        if quantity is None:
            unit = None
            reviews.append({
                "code": "material_quantity_unsupported", "severity": "warning", "path": f"materials[{requirement_id}]",
                "message": "Material identity is evidenced but its net consumption is not explicit",
                "evidence_refs": list(claim["evidence_refs"]),
            })
        material = {
            "requirement_id": requirement_id,
            "source_name": str(raw.get("n") or claim["family"]),
            "family": claim["family"], "specification": _sparse_specification(raw.get("s")),
            "quantity": quantity, "unit": unit, "evidence_refs": list(claim["evidence_refs"]),
        }
        materials.append(material)
        key = (material["family"], json.dumps(material["specification"], sort_keys=True), str(material["unit"] or ""))
        fingerprints.setdefault(key, []).append(material)
    for duplicated in fingerprints.values():
        if len(duplicated) > 1:
            for material in duplicated:
                material["quantity"], material["unit"] = None, None
            reviews.append({
                "code": "material_scope_overlap", "severity": "blocking", "path": "materials",
                "message": "Repeated material claims have overlapping or unresolved physical scope; no quantity was combined",
                "evidence_refs": list(dict.fromkeys(ref for material in duplicated for ref in material["evidence_refs"])),
            })
    if not materials:
        reviews.append({
            "code": "material_requirement_missing", "severity": "blocking", "path": "materials",
            "message": "No valid material demand was extracted", "evidence_refs": artifact_refs[:1],
        })
    facts = {
        "contract_version": MATERIAL_FACTS_V4_1_VERSION, "input_id": str(row["input_id"]),
        "object_input_revision": int(row.get("object_input_revision") or 1),
        "run_id": str(payload["run_id"]), "company_id": str(payload["company_id"]),
        "object_id": str(object_payload["object_id"]), "object_name": str(object_payload["object_name"]),
        "quantity": object_payload.get("quantity") or 1,
        "status": "review_required" if reviews else "ready",
        "dimensions_mm": {"width": None, "depth": None, "height": None},
        "materials": materials, "parts": [], "review_items": reviews,
        "primary_preview_ref": artifact_refs[0],
    }
    return validate_material_facts_v4_1(facts, allowed_material_families=families)


def _run_one_input(
    *, row: Mapping[str, Any], allowed_material_families: AbstractSet[str],
    evidence_page_bytes_by_ref: Mapping[str, bytes], pricing_key_fields_by_family: Mapping[str, Sequence[str]],
    family_alias_context: Mapping[str, Mapping[str, Any]], model: str,
) -> tuple[dict[str, Any], list[Any], list[dict[str, Any]]]:
    batches = build_v4_1_evidence_batches(row["input_payload"])
    responses, claims, reviews, diagnostics = [], [], [], []
    client = get_anthropic_client().with_options(timeout=TIMEOUT_SECONDS, max_retries=0)
    for batch in batches:
        resolved_pages = []
        for page in batch["pages"]:
            content = evidence_page_bytes_by_ref.get(page["storage_ref"])
            if not content:
                raise ValueError(f"full source evidence is missing for {page['storage_ref']}")
            resolved_pages.append({**page, "bytes": content})
        content, _request = _batch_request(
            batch={**batch, "pages": resolved_pages}, allowed_material_families=allowed_material_families,
            pricing_key_fields_by_family=pricing_key_fields_by_family, family_alias_context=family_alias_context,
        )
        response = _create_message_with_hard_timeout(
            client, timeout_seconds=TIMEOUT_SECONDS, model=model, max_tokens=MAX_OUTPUT_TOKENS, temperature=0,
            system=PROMPT_PATH.read_text(encoding="utf-8").strip(), messages=[{"role": "user", "content": content}],
        )
        batch_claims, batch_reviews = _response_for_batch(
            response=_json_object(extract_text_from_claude_response(response)), batch=batch,
            families=allowed_material_families,
        )
        responses.append(response)
        claims.extend(batch_claims)
        reviews.extend(batch_reviews)
        diagnostics.append({"batch_id": batch["batch_id"], "topic": batch["topic"], "page_numbers": [page["page_number"] for page in batch["pages"]]})
    return _facts_from_claims(row=row, claims=claims, reviews=reviews, families=allowed_material_families), responses, diagnostics


def run_estimation_v4_1_material_facts_agent(
    *, inputs: Sequence[Mapping[str, Any]], allowed_material_families: AbstractSet[str],
    evidence_page_bytes_by_ref: Mapping[str, bytes], pricing_key_fields_by_family: Mapping[str, Sequence[str]] | None = None,
    family_alias_context: Mapping[str, Mapping[str, Any]] | None = None, model: str | None = None,
) -> dict[str, Any]:
    if not inputs:
        raise ValueError("inputs are required")
    selected_model = model or get_secret("CLAUDE_ESTIMATION_V4_1_PAGE_MODEL", DEFAULT_CLAUDE_AGENT_MODEL)
    started_at = datetime.now(UTC).isoformat()
    facts_by_input, failed, all_responses, batch_diagnostics = {}, {}, [], []
    for row in inputs:
        input_id = str(row.get("input_id") or "")
        try:
            facts, responses, diagnostics = _run_one_input(
                row=row, allowed_material_families=allowed_material_families,
                evidence_page_bytes_by_ref=evidence_page_bytes_by_ref,
                pricing_key_fields_by_family=pricing_key_fields_by_family or {}, family_alias_context=family_alias_context or {},
                model=selected_model,
            )
            facts_by_input[input_id] = facts
            all_responses.extend(responses)
            batch_diagnostics.extend(diagnostics)
        except Exception as exc:
            failed[input_id or "unknown"] = f"{type(exc).__name__}: {exc}"
    total_input = sum(int(getattr(getattr(response, "usage", None), "input_tokens", 0) or 0) for response in all_responses)
    total_output = sum(int(getattr(getattr(response, "usage", None), "output_tokens", 0) or 0) for response in all_responses)
    aggregate_response = SimpleNamespace(usage=SimpleNamespace(input_tokens=total_input, output_tokens=total_output, cache_creation_input_tokens=0, cache_read_input_tokens=0))
    first = inputs[0]["input_payload"]
    usage = build_agent_usage_event(
        agent_name="estimation_v4_1_material_facts", operation="bounded_material_fact_extraction",
        company_id=str(first.get("company_id") or ""), run_id=str(first.get("run_id") or ""),
        file_name=str((first.get("document") or {}).get("file_name") or ""), object_id="page-batches",
        object_name=f"{len(inputs)} objects", model=selected_model,
        prompt_version=ESTIMATION_V4_1_MATERIAL_FACTS_AGENT_VERSION, response=aggregate_response,
        started_at=started_at, finished_at=datetime.now(UTC).isoformat(),
        request_diagnostics={"object_count": len(inputs), "batch_count": len(all_responses), "batches": batch_diagnostics, "material_only": True},
    )
    return {"facts_by_input": facts_by_input, "failed": failed, "usage_event": usage}
