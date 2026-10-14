import json

import agents.estimation_v3_material_facts_agent as agent
from agents.estimation_v3_material_facts_agent import _expand
from use_cases.estimation_v3_material_facts import (
    _family_alias_context_by_resolver_family,
    _pricing_key_fields_by_resolver_family,
)


def test_v3_expands_only_material_demands_and_cut_geometry():
    facts = _expand(
        {
            "d": [1200, 600, 720],
            "m": [{"id": "m1", "n": "MDF panel", "f": "mdf", "q": 2.4, "u": "m²", "s": {"thickness_mm": 18}}],
            "p": [{"id": "p1", "m": "m1", "q": 2, "l": 1200, "w": 600, "r": "yes"}],
        },
        {"input_id": "input-1", "object_input_revision": 1, "input_payload": {
            "run_id": "run-1", "company_id": "company-1",
            "object": {"object_id": "object-1", "object_name": "Cabinet", "quantity": 1},
            "evidence": {"primary_preview_ref": "storage://rfq-estimation-evidence/company-1/a.webp"},
        }},
        {"mdf"},
    )

    assert facts["contract_version"] == "estimation_material_facts_v3"
    assert facts["materials"][0]["family"] == "mdf"
    assert facts["materials"][0]["quantity"] == 2.4
    assert facts["materials"][0]["unit"] is None
    assert facts["parts"][0]["material_requirement_id"] == "m1"
    assert set(facts) == {
        "contract_version", "input_id", "object_input_revision", "run_id",
        "company_id", "object_id", "object_name", "quantity", "status",
        "dimensions_mm", "materials", "parts", "review_items", "primary_preview_ref",
    }


def test_v3_ignores_model_guessed_purchase_units_for_geometry_free_materials():
    facts = _expand(
        {
            "m": [{
                "id": "profile", "n": "square steel tube", "f": "metal tube",
                "q": 1, "u": "piece", "s": {"profile_section": "20x20 mm square"},
            }],
        },
        {"input_id": "input-1", "object_input_revision": 1, "input_payload": {
            "run_id": "run-1", "company_id": "company-1",
            "object": {"object_id": "object-1", "object_name": "Shelf", "quantity": 1},
            "evidence": {"primary_preview_ref": "storage://rfq-estimation-evidence/company-1/a.webp"},
        }},
        {"metal tube"},
    )

    material = facts["materials"][0]
    assert material["family"] == "metal tube"
    assert material["quantity"] == 1
    assert material["unit"] is None


def test_v3_exposes_only_existing_pricing_key_facts_to_extraction():
    requirements = _pricing_key_fields_by_resolver_family(
        families={"mdf", "metal tube"},
        material_families=[
            {"family_id": "mdf", "family_code": "mdf_hdf", "active": True},
            {"family_id": "tube", "family_code": "metal_tube", "active": True},
        ],
        material_pricing_policies=[
            {"family_id": "mdf", "pricing_key_attribute_codes": ["thickness"], "active": True},
            {
                "family_id": "tube",
                "pricing_key_attribute_codes": ["metal_type", "section_profile"],
                "active": True,
            },
        ],
    )

    assert requirements == {
        "mdf": ("thickness_mm", "thickness"),
        "metal tube": ("metal_type", "profile_section"),
    }


def test_v3_builds_multilingual_intake_context_for_allowed_families():
    context = _family_alias_context_by_resolver_family(
        families={"mdf", "metal profile"},
        pricing_key_fields_by_family={
            "mdf": ("thickness_mm",),
            "metal profile": ("profile_section", "metal_type"),
        },
    )

    assert set(context) == {"mdf", "metal profile"}
    assert context["mdf"]["catalog_family"] == "mdf_hdf"
    assert "панель мдф" in context["mdf"]["family_aliases"]
    assert "толщина" in context["mdf"]["pricing_key_aliases"]["thickness_mm"]
    assert context["metal profile"]["catalog_family"] == "metal_profile_angle_channel"
    assert "профиль металлический" in context["metal profile"]["family_aliases"]


def test_v3_sends_bounded_multilingual_alias_context_to_the_agent(monkeypatch):
    captured = {}

    class _Client:
        def with_options(self, **_kwargs):
            return self

    class _Response:
        usage = None
        stop_reason = "end_turn"

    monkeypatch.setattr(agent, "get_anthropic_client", lambda: _Client())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")
    monkeypatch.setattr(agent, "create_claude_message", lambda *_args, **kwargs: captured.update(kwargs) or _Response())
    monkeypatch.setattr(
        agent,
        "extract_text_from_claude_response",
        lambda _response: json.dumps({"objects": [{"id": "object-1", "d": [0, 0, 0], "m": [], "p": []}]}),
    )

    agent.run_estimation_v3_material_facts_agent(
        inputs=[{
            "input_id": "input-1",
            "object_input_revision": 1,
            "input_payload": {
                "run_id": "run-1", "company_id": "company-1",
                "object": {"object_id": "object-1", "object_name": "Shelf", "quantity": 1},
                "evidence": {"primary_preview_ref": "storage://rfq-estimation-evidence/company-1/a.webp"},
            },
        }],
        allowed_material_families={"mdf"},
        preview_bytes_by_input={"input-1": b"preview"},
        pricing_key_fields_by_family={"mdf": ("thickness_mm",)},
        family_alias_context={
            "mdf": {
                "catalog_family": "mdf_hdf",
                "family_aliases": ["mdf", "мдф", "מדפ"],
                "pricing_key_aliases": {"thickness_mm": ["thickness", "толщина", "עובי"]},
            },
        },
    )

    request = json.loads(captured["messages"][0]["content"][-1]["text"])
    assert request["family_alias_context"] == {
        "mdf": {
            "catalog_family": "mdf_hdf",
            "family_aliases": ["mdf", "мдф", "מדפ"],
            "pricing_key_aliases": {"thickness_mm": ["thickness", "толщина", "עובי"]},
        },
    }
