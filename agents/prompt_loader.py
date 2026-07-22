from __future__ import annotations

from pathlib import Path
import re


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
DETECTION_PROMPT_PATH = PROMPTS_DIR / "detection_agent_prompt.md"
ESTIMATION_PROMPT_PATH = PROMPTS_DIR / "estimation_agent_prompt.md"


def load_detection_agent_prompt() -> str:
    if not DETECTION_PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Detection prompt not found: {DETECTION_PROMPT_PATH}"
        )

    prompt = DETECTION_PROMPT_PATH.read_text(encoding="utf-8").strip()

    if not prompt:
        raise ValueError(f"Detection prompt is empty: {DETECTION_PROMPT_PATH}")

    return prompt


def load_detection_agent_without_naming_prompt() -> str:
    """Build the isolated A/B prompt that delegates all user-facing naming."""
    prompt = load_detection_agent_prompt()
    prompt = prompt.replace(
        "Detection alone makes all semantic decisions.",
        "Detection makes all object-boundary and evidence decisions. Naming is delegated downstream.",
    )
    prompt = prompt.replace(
        "Your output has six user-facing jobs:\n\n"
        "1. Extract project metadata: project name, design partner, client, author, document date, and file quality label.\n"
        "2. Detect and correctly group only the commercial objects the contractor is expected to quote.\n"
        "3. Give every object a short, unambiguous name.\n"
        "4. Determine the quantity of complete commercial units.\n"
        "5. Extract the external overall dimensions of each complete object.\n"
        "6. Write concise notes containing only estimation-relevant observations, uncertainty, assumptions, and clarification questions.",
        "Your output has five user-facing jobs:\n\n"
        "1. Extract project metadata: project name, design partner, client, author, document date, and file quality label.\n"
        "2. Detect and correctly group only the commercial objects the contractor is expected to quote.\n"
        "3. Determine the quantity of complete commercial units.\n"
        "4. Extract the external overall dimensions of each complete object.\n"
        "5. Write concise notes containing only estimation-relevant observations, uncertainty, assumptions, and clarification questions.",
    )
    prompt = re.sub(
        r"\n## 5\. Object naming\n.*?\n---\n\n## 6\. Quantity",
        """
## 5. Naming handoff placeholder

Do not create, translate, shorten, improve, or validate a user-facing product name.

The schema still requires object_name as a transport field. Set it mechanically:

- use the exact authoritative object-level index or code when one exists;
- otherwise use Object 1, Object 2, and so on in detected-object order;
- never add a product category, original-language label, description, dimensions, materials, or marketing text.

Naming is performed once by a separate downstream Naming Agent after the object set is locked.

---

## 6. Quantity""",
        prompt,
        flags=re.DOTALL,
    )
    prompt = prompt.replace(
        "- repeat the object name, quantity, dimensions, materials, or evidence pages without adding meaning;",
        "- repeat quantity, dimensions, materials, or evidence pages without adding meaning;",
    )
    prompt = prompt.replace(
        "- provide a useful name, quantity, external dimensions, materials, evidence pages, and concise notes;\n"
        "- preserve relevant object indices and original labels;",
        "- provide quantity, external dimensions, materials, evidence pages, and concise notes;\n"
        "- preserve relevant object indices as transport identifiers;",
    )
    prompt = prompt.replace(
        "- object_id values must be stable, unique, and based on the object index or concise name;",
        "- object_id values must be stable and unique: use the object index when present, otherwise object-001, object-002, and so on;",
    )
    prompt = re.sub(
        r"\n### Example A — one curtain assembly\n.*?\n### Example B — equipment inside a fabricated counter",
        """
### Example A — one curtain assembly

The document shows curtain fabric, a suspension track, brackets, anchors, and mounting details. The same system appears in plan, elevation, section, and render. The object index is NR-90.

Return one object. Set object_name mechanically to NR-90. Do not name or translate the product. Preserve quantity, overall dimensions, evidence pages, and meaningful scope questions.

Do not return separate objects for fabric, track, suspension, brackets, anchors, or individual views.

### Example B — equipment inside a fabricated counter""",
        prompt,
        flags=re.DOTALL,
    )
    prompt = prompt.replace(
        "6. Every authoritative object index is preserved in object_name.\n"
        "7. Names are short, specific, and never copied from a sheet or room title.\n"
        "8. Quantity counts complete physical units, not components or drawings.\n"
        "9. width/depth/height describe only the external object envelope.\n"
        "10. raw_text is a compact W × H × D string under 80 characters.\n"
        "11. Notes contain only actionable estimation information or specific questions.\n"
        "12. The handoff is sufficient for Estimation without performing estimation.\n"
        "13. All required schema fields are present, no extra fields or nulls exist, and status is valid.",
        "6. object_name contains only the mechanical naming-handoff placeholder.\n"
        "7. Quantity counts complete physical units, not components or drawings.\n"
        "8. width/depth/height describe only the external object envelope.\n"
        "9. raw_text is a compact W × H × D string under 80 characters.\n"
        "10. Notes contain only actionable estimation information or specific questions.\n"
        "11. The handoff is sufficient for Estimation without performing estimation.\n"
        "12. All required schema fields are present, no extra fields or nulls exist, and status is valid.",
    )
    return prompt


def load_estimation_agent_prompt() -> str:
    if not ESTIMATION_PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Estimation prompt not found: {ESTIMATION_PROMPT_PATH}"
        )

    prompt = ESTIMATION_PROMPT_PATH.read_text(encoding="utf-8").strip()

    if not prompt:
        raise ValueError(f"Estimation prompt is empty: {ESTIMATION_PROMPT_PATH}")

    return prompt
