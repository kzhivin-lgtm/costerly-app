"""Find potential render/drawing role errors in the fixed Discovery inventory."""

from collections import Counter
from io import BytesIO
import re
from typing import Any

from PIL import Image


RENDER_ROLE = "presentation_render"
TECHNICAL_ROLES = ("plan", "elevation", "section", "detail", "isometric")
RENDER_CUE = re.compile(
    r"\b(?:render(?:ed|ing)?s?|photos?|photographs?|thumbnails?|perspectives?|visuali[sz]ations?)\b",
    re.IGNORECASE,
)

RENDER_ROLE_PROMPT = """\
Review the visual medium of each fixed crop. A shaded render, photograph, or stack
of rendered thumbnails showing fabricated parts is presentation_render. A straight-on
render can still have realistic lighting, material textures and filled backgrounds.
An orthogonal or isometric technical drawing shows intentional linework, construction
notation, dimensions or hatching. A photograph and a shaded render both have the
role presentation_render. Use retain_original if the crop mixes media or it is
unclear whether it is a technical drawing. Return one decision per supplied View ID
with a short visual witness naming the visible medium and subject. Do not change
boxes, decide membership, or identify objects across crops. Return only schema JSON."""

RENDER_ROLE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["presentation_role_decisions"],
    "properties": {"presentation_role_decisions": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["group_id", "role", "visual_witness"],
        "properties": {
            "group_id": {"type": "string"},
            "role": {"type": "string", "enum": [RENDER_ROLE, *TECHNICAL_ROLES, "retain_original"]},
            "visual_witness": {"type": "string"},
        },
    }}},
}


def select_presentation_role_crops(groups: list[dict[str, Any]], crops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Use shading and Discovery's own descriptions to select crops for review."""
    by_id = {group["group_id"]: group for group in groups}
    selected = []
    for crop in crops:
        group = by_id[crop["group_id"]]
        is_render = group["representation_kind"] == RENDER_ROLE
        description = " ".join(str(group.get(key) or "") for key in (
            "representation_kind", "visual_description", "location_hint",
        )).replace("_", " ")
        if not is_render and RENDER_CUE.search(description):
            selected.append(crop)
            continue
        with Image.open(BytesIO(crop["bytes"])) as image:
            sample = image.convert("L")
            sample.thumbnail((96, 96), Image.Resampling.BOX)
        # Downsampling suppresses fine drawing lines. Shading only selects a crop for review.
        shaded = 3 * sum(sample.histogram()[:210]) >= sample.width * sample.height
        if shaded != is_render:
            selected.append(crop)
    return selected


def presentation_role_corrections(
    groups: list[dict[str, Any]], visible_ids: set[str], decisions: object,
) -> dict[str, dict[str, str]]:
    """Accept only unambiguous switches between render and technical drawing."""
    if not isinstance(decisions, list):
        raise ValueError("Presentation role review did not return decisions")
    previous = {group["group_id"]: group["representation_kind"] for group in groups}
    valid_ids = [
        row["group_id"] for row in decisions
        if isinstance(row, dict) and isinstance(row.get("group_id"), str) and row["group_id"] in visible_ids
    ]
    counts = Counter(valid_ids)
    corrections = {}
    for row in decisions:
        if not isinstance(row, dict) or not isinstance(row.get("group_id"), str):
            continue
        group_id = row["group_id"]
        role, witness = row.get("role"), row.get("visual_witness")
        if (
            counts[group_id] == 1
            and role in (RENDER_ROLE, *TECHNICAL_ROLES)
            and (previous[group_id] == RENDER_ROLE) != (role == RENDER_ROLE)
            and isinstance(witness, str) and witness.strip()
        ):
            corrections[group_id] = {
                "previous_role": previous[group_id], "role": role, "visual_witness": witness.strip(),
            }
    return corrections
