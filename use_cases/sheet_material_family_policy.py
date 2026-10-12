"""Shared Israel estimation classes for sheet-material families.

Supplier identity must stay more detailed than an estimation class.  These
policies are therefore consumed by Source resolution and Estimation resolution,
without changing a company's distinct offers or their evidence.
"""

from __future__ import annotations

from typing import Any, Mapping

from use_cases.material_identity_resolution import normalize_material_phrase


RAW = "raw"
STANDARD_FACED = "plastic_laminate_faced"
HPL_FACED = "hpl_faced"
VENEER_FACED = "veneer_faced"


def sheet_estimation_specifications(
    *,
    material_family: str,
    extracted_specifications: Mapping[str, Any],
) -> dict[str, Any]:
    """Return only the class facts that may select an Israel sheet reference.

    The original facts are intentionally retained on the company material and
    source row.  Twin, Combi and Okoume identify separate supplier offers, but
    not a different raw-plywood estimation class.  Colour identifies ordinary
    faced MDF, while HPL and veneer remain separate price-bearing classes.
    """
    result = dict(extracted_specifications)
    family = normalize_material_phrase(material_family)
    surface = normalize_material_phrase(result.get("surface"))
    coating = normalize_material_phrase(result.get("coating"))
    construction = normalize_material_phrase(result.get("construction"))
    colour = normalize_material_phrase(result.get("colour"))

    if family == "plywood":
        # Do not discard an explicit construction that is materially different
        # from raw plywood, including perforation or a recognised facing.
        if any(token in " ".join((surface, coating, construction)) for token in ("veneer", "veneered")):
            result["construction"] = VENEER_FACED
        elif any(token in " ".join((surface, coating, construction)) for token in ("hpl", "formica")):
            result["construction"] = HPL_FACED
        elif any(token in " ".join((surface, coating, construction)) for token in ("laminate", "laminated", "plastic")):
            result["construction"] = STANDARD_FACED
        elif construction != "perforated":
            result["construction"] = RAW
        result.pop("species", None)
        result.pop("plywood_variant", None)
        return result

    if family in {"mdf", "faced mdf"}:
        facts = " ".join((surface, coating, construction))
        if any(token in facts for token in ("veneer", "veneered")):
            result["construction"] = VENEER_FACED
        elif any(token in facts for token in ("hpl", "formica")):
            result["construction"] = HPL_FACED
        elif family == "faced mdf" or colour or any(
            token in facts for token in ("melamine", "laminate", "laminated", "plastic")
        ):
            # Existing Israel reference seeds label the ordinary melamine/decor
            # class as ``plastic_laminate_faced``. It is not the HPL class.
            result["construction"] = STANDARD_FACED
        else:
            result["construction"] = RAW
        # Colour/decor is evidence and display information, not a separate
        # standard-faced MDF estimate class.
        result.pop("colour", None)
        return result

    return result


def canonical_sheet_name_tokens(
    *, material_family: str, construction: str, thickness_mm: object
) -> set[str]:
    """Return the required canonical-name tokens for strict legacy bridging."""
    try:
        thickness = str(int(float(thickness_mm)))
    except (TypeError, ValueError):
        return set()
    family = normalize_material_phrase(material_family)
    required = {thickness, "mm"}
    if family == "plywood":
        required.add("plywood")
    elif family in {"mdf", "faced mdf"}:
        required.add("mdf")
    else:
        return set()
    class_tokens = {
        RAW: {"raw"},
        STANDARD_FACED: {"plastic", "laminate", "faced"},
        HPL_FACED: {"hpl", "faced"},
        VENEER_FACED: {"veneer", "faced"},
    }.get(normalize_material_phrase(construction))
    return required | (class_tokens or set())
