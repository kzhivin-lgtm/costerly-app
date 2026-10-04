from __future__ import annotations

from agents.anthropic_adapter import run_anthropic_detection_agent_with_fallback, run_anthropic_detection_registry_agent
from agents.detection_page_images import build_detection_registry_regions, render_detection_pdf_pages
from agents.prompt_loader import load_detection_agent_prompt, load_detection_registry_prompt
from agents.schemas.detection_schema import validate_detection_result


def _enforce_shared_track_door_system_quantity(registry: dict) -> dict:
    """Resolve an internal registry contradiction for a shared-track door set.

    This is a domain invariant, not a Page 23 special case: leaves on one
    continuous track are construction components of one commercial door system.
    The registry has already identified that boundary in ``boundary_basis``;
    this guard prevents a conflicting leaf count from becoming the quote count.
    """
    shared_track_markers = (
        "continuous track", "shared track", "common track", "same track",
        "single track", "one track", "overhead track", "continuous guide",
        "shared guide", "common guide", "same guide", "single guide",
    )
    door_markers = ("door", "leaf", "leaves", "sliding")
    for item in registry.get("objects") or []:
        if not isinstance(item, dict):
            continue
        basis = " ".join(
            str(item.get(key) or "")
            for key in ("transport_label", "visual_identity", "boundary_basis")
        ).casefold()
        if (
            float(item.get("quantity") or 0) > 1
            and any(marker in basis for marker in shared_track_markers)
            and any(marker in basis for marker in door_markers)
        ):
            item["quantity"] = 1
            item["quantity_explicit"] = False
    return registry


def _merge_registry_evidence(result: dict, registry: dict) -> dict:
    """Preserve the compact visual dossier while retaining Estimation evidence.

    The registry intentionally selects only a small set of pages for the
    second Detection pass.  Those pages are not the object evidence boundary:
    a kitchen's block and assembly sheets, for example, remain required by
    Estimation even when Detection did not need to inspect every sheet again.
    """
    registry_objects = {
        str(item["object_id"]): item
        for item in registry["objects"]
    }
    for detected in result.get("detected_objects") or []:
        if not isinstance(detected, dict):
            continue
        locked_object = registry_objects.get(str(detected.get("object_id")))
        if not isinstance(locked_object, dict):
            continue
        # The registry locks the commercial-object boundary and complete-unit
        # quantity before the richer dossier pass sees component dimensions.
        # Do not let a leaf, panel, view, or repeated detail replace that
        # locked quantity in the final commercial object.
        detected["quantity"] = locked_object["quantity"]
        detected["quantity_explicit"] = locked_object["quantity_explicit"]
        required_pages = set(locked_object["estimation_evidence_pages"])
        refs_by_page: dict[int, dict] = {}
        for raw_ref in detected.get("evidence_page_refs") or []:
            if not isinstance(raw_ref, dict):
                continue
            try:
                page_number = int(raw_ref.get("page_number"))
            except (TypeError, ValueError):
                continue
            if page_number > 0:
                refs_by_page[page_number] = dict(raw_ref)
        for page_number in sorted(required_pages):
            ref = refs_by_page.get(page_number)
            if ref is None:
                refs_by_page[page_number] = {
                    "page_number": page_number,
                    "source_label": str(page_number),
                    "roles": ["construction"],
                }
                continue
            roles = list(ref.get("roles") or [])
            if "construction" not in roles:
                roles.append("construction")
            ref["roles"] = roles
            refs_by_page[page_number] = ref
        refs = [refs_by_page[page_number] for page_number in sorted(refs_by_page)]
        detected["evidence_page_refs"] = refs
        detected["evidence_pages"] = ",".join(
            str(ref["page_number"]) for ref in refs
        )
    return result


def get_secret(name: str, default: str | None = None) -> str | None:
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass

    return default


def run_detection_agent(
    file_name: str,
    company_id: str = "001",
    file_bytes: bytes | None = None,
    ocr_package: dict | None = None,
    page_images: list[bytes] | None = None,
    page_image_diagnostics: dict | None = None,
    model: str | None = None,
) -> dict:
    """
    Detection Agent entrypoint.

    Runs the real Claude-backed Detection Agent.
    """

    # Fail loudly if the prompt file is missing or empty.
    _prompt = load_detection_agent_prompt()
    _registry_prompt = load_detection_registry_prompt()

    if file_bytes is None:
        raise ValueError("Detection Agent requires uploaded file bytes.")

    registry_images = page_images
    if registry_images is None and file_name.lower().endswith(".pdf"):
        registry_images, _ = render_detection_pdf_pages(file_bytes)
    elif registry_images is None:
        registry_images = [file_bytes]
    if not registry_images:
        raise ValueError("Detection registry requires rendered PDF pages.")
    regions = build_detection_registry_regions(registry_images)
    registry, registry_usage = run_anthropic_detection_registry_agent(
        file_name=file_name, company_id=company_id, file_bytes=file_bytes,
        page_images=registry_images, regions=regions,
        ocr_package=ocr_package, model=model,
    )
    registry = _enforce_shared_track_door_system_quantity(registry)
    dossier_page_numbers = sorted({page for item in registry["objects"] for page in item["dossier_pages"]})
    dossier_images = [registry_images[page - 1] for page in dossier_page_numbers if page <= len(registry_images)]
    dossier_regions = [region for region in regions if region["page_number"] in dossier_page_numbers]
    result = run_anthropic_detection_agent_with_fallback(
        file_name=file_name,
        company_id=company_id,
        file_bytes=file_bytes,
        ocr_package=ocr_package,
        page_images=dossier_images,
        page_image_diagnostics=page_image_diagnostics,
        primary_model_override=model,
        locked_registry=registry,
        allow_sonnet_fallback=False,
        focus_regions=dossier_regions,
        page_image_numbers=dossier_page_numbers,
    )

    usage_event = result.pop("_agent_usage", None)
    validated = validate_detection_result(_merge_registry_evidence(result, registry))
    validated["_agent_usage_events"] = [event for event in (registry_usage, usage_event) if event]
    return validated
