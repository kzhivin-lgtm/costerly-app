"""Deterministic canonical-path completeness for company materials."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping


IdentityTone = Literal["green", "yellow", "blue", "red"]


@dataclass(frozen=True)
class MaterialIdentityStatus:
    tone: IdentityTone
    label: str
    known_path: tuple[str, ...]
    missing: tuple[str, ...]
    detail: str


_FIELD_LABELS = {
    "thickness_mm": "thickness",
    "species": "species",
    "width_mm": "width",
    "substrate": "substrate",
    "metal_type": "base metal",
    "section_profile": "section profile",
    "wall_thickness_mm": "wall thickness",
    "diameter_mm": "diameter",
    "coating_system": "coating system",
    "depth_mm": "nominal length",
}


# Required V1 endpoint facts. Brand and Product System enrich the canonical
# path but deliberately never block preliminary estimation on their own.
_REQUIRED_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "mdf": ("thickness_mm",),
    "particleboard": ("thickness_mm",),
    "hardboard": ("thickness_mm",),
    "osb": ("thickness_mm",),
    "laminated panel": ("thickness_mm",),
    "plywood": ("thickness_mm",),
    "solid timber": ("species", "thickness_mm"),
    "veneer": ("species",),
    "edge banding": ("width_mm", "thickness_mm", "substrate"),
    "glass": ("thickness_mm",),
    "acrylic sheet": ("thickness_mm",),
    "abs sheet": ("thickness_mm",),
    "polycarbonate sheet": ("thickness_mm",),
    "petg sheet": ("thickness_mm",),
    "pvc sheet": ("thickness_mm",),
    "plastic sheet": ("thickness_mm",),
    "aluminium composite panel": ("thickness_mm",),
    "composite sandwich panel": ("thickness_mm",),
    "vinyl film": ("width_mm",),
    "natural stone": ("thickness_mm",),
    "engineered quartz": ("thickness_mm",),
    "sintered stone": ("thickness_mm",),
    "porcelain": ("thickness_mm",),
    "solid surface": ("thickness_mm",),
    "terrazzo": ("thickness_mm",),
    "metal sheet": ("metal_type", "thickness_mm"),
    "metal tube": ("metal_type", "section_profile", "wall_thickness_mm"),
    "metal angle": ("metal_type", "section_profile", "wall_thickness_mm"),
    "metal channel": ("metal_type", "section_profile", "wall_thickness_mm"),
    "metal profile": ("metal_type", "section_profile", "wall_thickness_mm"),
    "metal bar": ("metal_type", "diameter_mm"),
    "powder coating": ("coating_system",),
    "epoxy coating": ("coating_system",),
    "polyurethane coating": ("coating_system",),
    "primer": ("coating_system",),
    "lacquer": ("coating_system",),
    "paint": ("coating_system",),
    "coating material": ("coating_system",),
    "drawer slide": ("depth_mm",),
    "drawer system": (),
    "hinge": (),
    "door closure": (),
    "handle": (),
    "furniture leg": (),
    "caster": (),
    "plinth profile": (),
    "drilling fixture": (),
    "furniture connector": (),
    "lift mechanism": (),
}


def _present(value: Any) -> bool:
    return value not in (None, "", 0, 0.0, [], {})


def _display(value: Any) -> str:
    return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)


def material_identity_status(item: Mapping[str, Any]) -> MaterialIdentityStatus:
    """Assess canonical-path depth without mutating source or catalog data."""
    specs = dict(item.get("specifications") or {})
    family = str(specs.get("material_family") or "").strip()
    if not family or family.casefold() in {"other", "unclassified", "unknown"}:
        return MaterialIdentityStatus("red", "Identity unresolved", (), ("material family",), "Material family is not established")

    required = _REQUIRED_BY_FAMILY.get(family, ())
    missing = tuple(_FIELD_LABELS[field] for field in required if not _present(specs.get(field)))
    path = [family]
    for field, label in (("brand", "brand"), ("product_system", "system"), *[(field, _FIELD_LABELS[field]) for field in required]):
        value = specs.get(field)
        if _present(value):
            unit = " mm" if field.endswith("_mm") else ""
            path.append(f"{label}: {_display(value)}{unit}")

    if missing:
        return MaterialIdentityStatus("yellow", "Canonical path incomplete", tuple(path), missing, f"Add {', '.join(missing)} to complete the canonical path")
    if not str(item.get("reference_material_id") or ""):
        return MaterialIdentityStatus("blue", "Israel reference link missing", tuple(path), (), "Canonical endpoint is known, but no Israel reference material is linked yet")
    return MaterialIdentityStatus("green", "Canonical link complete", tuple(path), (), "Canonical endpoint and Israel reference material are linked")
