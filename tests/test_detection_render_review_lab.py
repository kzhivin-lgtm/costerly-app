import json
from types import SimpleNamespace

from agents.anthropic_adapter import DETECTION_V711_PRESENTATION_RENDER_DECISIONS_SCHEMA
from tools.detection_haiku55_autonomous_lab import technical_pages
from tools.detection_render_review import review_render_roles, review_render_rows


def provider_response(payload):
    return SimpleNamespace(stop_reason="end_turn", content=[
        SimpleNamespace(type="text", text=json.dumps(payload)),
    ])


def render_decision(render, target="", witness=""):
    return {
        "render_group_id": render,
        "disposition": "attach" if target else "no_match",
        "technical_group_id": target,
        "evidence_type": "matching_topology" if target else "none",
        "visual_witness": witness,
    }


def test_blank_render_witness_is_reviewed_without_allowing_render_to_render_edges():
    views = {
        "render": (6, "presentation_render"),
        "other-render": (6, "presentation_render"),
        "technical": (6, "elevation"),
        "technical-sibling": (6, "section"),
        "off-sheet": (7, "section"),
        "missing-crop": (7, "presentation_render"),
    }
    blocks = []
    for group in ("render", "other-render", "technical", "technical-sibling", "off-sheet"):
        blocks.extend([
            {"type": "text", "text": f"Object View {group}, PDF page {views[group][0]}"},
            {"type": "image", "source": {}},
        ])
    blocks.append({"type": "text", "text": "\n".join(
        f"{group}|P{page}|K={role}|D=Fixed crop|SRC=none"
        for group, (page, role) in views.items()
    )})
    request = {
        "model": "claude-haiku-5-5",
        "messages": [{"role": "user", "content": blocks}],
        "output_config": {"format": {"schema": {"properties": {
            "presentation_render_decisions": DETECTION_V711_PRESENTATION_RENDER_DECISIONS_SCHEMA,
        }}}},
    }
    inspected = []

    def send(focused, page):
        inspected.append(page)
        assert "off-sheet" not in str(focused["messages"])
        assert "technical + technical-sibling" in focused["messages"][0]["content"][-1]["text"]
        return provider_response({"presentation_render_decisions": [
            render_decision("render", "technical", "Both show an offset opening beside two stacked shelves."),
            render_decision("other-render", "render", "The two images have matching colors."),
        ]}), {}

    rows, calls, sources = review_render_rows(
        request, views, [render_decision("render"), render_decision("other-render")],
        send, lambda _: False, workers=1, technical_components=[["technical", "technical-sibling", "off-sheet"]],
    )
    assert inspected == [6]
    assert len(calls) == 1
    assert [(row["render_group_id"], row["disposition"], row["technical_group_id"]) for row in rows] == [
        ("missing-crop", "unresolved", ""),
        ("other-render", "unresolved", ""),
        ("render", "attach", "technical"),
    ]
    assert sources["render"] == "focused_same_page"


def test_render_role_review_changes_only_a_confirmed_fixed_role():
    thumbnail = {"group_id": "thumb", "representation_kind": "technical_detail", "bbox": {"left": 10}}
    drawing = {"group_id": "drawing", "representation_kind": "technical_detail", "bbox": {"left": 25}}
    payload = {"visual_groups": [thumbnail, drawing]}

    def send(_request):
        return provider_response({"decisions": [
            {"group_id": "thumb", "role": "presentation_render", "visual_witness": "Shaded rendered views."},
            {"group_id": "drawing", "role": "retain_original", "visual_witness": "Dimensioned line drawing."},
            {"group_id": "unknown", "role": "presentation_render", "visual_witness": "Image."},
        ]}), {}

    _, changed = review_render_roles(
        payload, {"model": "claude-haiku-5-5", "max_tokens": 2048},
        [{"group_id": group, "bytes": b"crop"} for group in ("thumb", "drawing")], send,
    )
    assert changed == {"thumb": "Shaded rendered views."}
    assert thumbnail == {"group_id": "thumb", "representation_kind": "presentation_render", "bbox": {"left": 10}}
    assert drawing["representation_kind"] == "technical_detail"


def test_render_attachment_does_not_count_as_a_technical_merge():
    resolved, unresolved = technical_pages(
        [["elevation", "render"], ["plan", "section"]],
        {"elevation": 1, "plan": 2, "section": 2},
    )
    assert resolved == {2}
    assert unresolved == {"elevation"}
