from __future__ import annotations

from agents.anthropic_adapter import run_anthropic_detection_agent_with_fallback, run_anthropic_detection_registry_agent
from agents.detection_page_images import build_detection_registry_regions, render_detection_pdf_pages
from agents.prompt_loader import load_detection_agent_prompt, load_detection_registry_prompt
from agents.schemas.detection_schema import validate_detection_result


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
    result = run_anthropic_detection_agent_with_fallback(
        file_name=file_name,
        company_id=company_id,
        file_bytes=file_bytes,
        ocr_package=ocr_package,
        page_images=page_images,
        page_image_diagnostics=page_image_diagnostics,
        primary_model_override=model,
        locked_registry=registry,
        allow_sonnet_fallback=False,
        focus_regions=regions,
    )

    usage_event = result.pop("_agent_usage", None)
    validated = validate_detection_result(result)
    validated["_agent_usage_events"] = [event for event in (registry_usage, usage_event) if event]
    return validated
