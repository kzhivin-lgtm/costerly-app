"""Shared structured material and operation normalisation contract.

This module is intentionally independent of a specific ingestion route.  A
Price Source row, a company material, a global material and an Estimation
requirement may have different persistence schemas, but all must first reduce
to the same identity: entity, primary attribute, optional brand, then only
identity-bearing secondary attributes.  Raw source prose is evidence, never
an identity field.
"""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any



# This is an allowlist by design. A new key is a domain decision, not something
# a source parser may add because it happens to see another adjective.
IDENTITY_ATTRIBUTE_DEFAULTS: dict[str, Any] = {
    "thickness_mm": 0,
    "width_mm": 0,
    "length_mm": 0,
    "depth_mm": 0,
    "diameter_mm": 0,
    "wall_thickness_mm": 0,
    "primary_attribute": "",
    "brand": "",
    "brand_basis": "unknown",
    "product_system": "",
    "plywood_variant": "",
    "species": "",
    "substrate": "",
    "board_type": "",
    "surface": "",
    "coating": "",
    "colour": "",
    "grade": "",
    "construction": "",
    "finish": "",
    # Price-bearing facts outside the sheet-material vocabulary.  These stay
    # explicitly allowlisted: a source may not promote arbitrary prose into
    # an identity merely because it is a descriptive adjective.
    "metal_type": "",
    "section_profile": "",
    "stone_type": "",
    "coating_system": "",
    "chemistry_product_type": "",
    "component_type": "",
    "packaging_type": "",
}

SECONDARY_ATTRIBUTE_ORDER: tuple[str, ...] = (
    "product_system", "grade", "species", "plywood_variant", "substrate", "construction", "finish", "surface",
    "coating", "metal_type", "section_profile", "wall_thickness_mm",
    "stone_type", "coating_system", "colour",
)

_ENTITY_DISPLAY_OVERRIDES = {
    "abs sheet": "ABS Sheet",
    "mdf": "MDF",
    "hdf": "HDF",
    "osb": "OSB",
    "pvc": "PVC",
    "pvc sheet": "PVC Sheet",
    "petg sheet": "PETG Sheet",
    "pmma sheet": "PMMA Sheet",
}


def _title_case_catalog_label(value: object) -> str:
    """Give source-provided catalog labels one calm, uniform display case."""
    return " ".join(str(value or "").strip().title().split())


def _canonical_brand_name(value: object) -> str:
    """Format source-proven brand text without maintaining a second alias list.

    Catalog recognition happens in the shared alias context.  The normalizer
    must not quietly recognise another spelling before that deterministic
    catalog pass has run.
    """
    return _title_case_catalog_label(value)


def _canonical_product_system_name(value: object) -> str:
    """Format source-proven system text without maintaining a second alias list."""
    return _title_case_catalog_label(value)


def normalize_identity_attributes(values: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return only attributes allowed to affect a material identity.

    Dropped source words are deliberately not returned. Callers retain their
    immutable raw source/evidence separately if an agent needs the original
    wording later.
    """
    source = values or {}
    normalized = {
        field: source.get(field, default)
        for field, default in IDENTITY_ATTRIBUTE_DEFAULTS.items()
    }
    normalized["brand"] = _canonical_brand_name(normalized["brand"])
    normalized["product_system"] = _canonical_product_system_name(normalized["product_system"])
    return normalized


def display_entity(entity: object) -> str:
    value = " ".join(str(entity or "material").strip().split())
    if not value:
        return "Material"
    return _ENTITY_DISPLAY_OVERRIDES.get(value.casefold(), value.title())


def _display_mm(value: object) -> str:
    try:
        numeric = float(value or 0)
    except (TypeError, ValueError):
        return ""
    if numeric <= 0:
        return ""
    return str(int(numeric)) if numeric.is_integer() else str(numeric)


def _key_dimension_label(identity: Mapping[str, Any]) -> str:
    """Render proven physical dimensions as a universal second key attribute."""
    length = _display_mm(identity.get("length_mm"))
    width = _display_mm(identity.get("width_mm"))
    depth = _display_mm(identity.get("depth_mm"))
    diameter = _display_mm(identity.get("diameter_mm"))
    if length and width:
        return f"{length} × {width} mm"
    if length:
        return f"{length} mm"
    if width:
        return f"{width} mm"
    if depth:
        return f"{depth} mm"
    if diameter:
        return f"Ø{diameter} mm"
    return ""


def _secondary_attribute_display(field: str, value: object) -> str:
    """Render the small set of non-sheet pricing facts without source prose."""
    text = str(value or "").strip()
    if not text:
        return ""
    if field == "wall_thickness_mm":
        dimension = _display_mm(value)
        return f"{dimension} mm wall" if dimension else ""
    if field in {"metal_type", "section_profile", "stone_type"}:
        return _title_case_catalog_label(text)
    if field == "substrate" and text.casefold() in {"abs", "pvc", "hpl", "petg", "pmma"}:
        return text.upper()
    return text


def canonical_display_name(
    entity: object,
    attributes: Mapping[str, Any] | None,
    *,
    maximum_secondary_attributes: int = 4,
) -> str:
    """Render `entity -> primary -> brand -> meaningful secondaries`.

    The caller owns entity classification. This renderer never attempts to
    infer a category from brand or from discarded source prose.
    """
    identity = normalize_identity_attributes(attributes)
    parts = [display_entity(entity)]
    primary = str(identity["primary_attribute"] or "").strip()
    if not primary:
        thickness = _display_mm(identity.get("thickness_mm"))
        if thickness:
            primary = f"{thickness} mm"
    source = attributes or {}
    brand_basis = str(source.get("brand_basis") or "").strip().casefold()
    brand = "" if brand_basis == "candidate" else str(identity["brand"] or "").strip()
    key_dimension = _key_dimension_label(identity)
    # A profile or edge band already renders its compound physical key as the
    # primary attribute (for example ``40×20 mm`` or ``22×2 mm``). Do not
    # repeat its first side as an unrelated second key dimension.
    if "×" in primary or "x" in primary.casefold():
        key_dimension = ""
    if primary:
        parts.append(primary)
    if key_dimension and key_dimension != primary:
        parts.append(key_dimension)
    if brand:
        parts.append(brand)

    secondary: list[str] = []
    for field in SECONDARY_ATTRIBUTE_ORDER:
        value = _secondary_attribute_display(field, identity[field])
        if not value or value.casefold() == str(entity or "").strip().casefold():
            continue
        if field == "coating_system" and value.casefold() in display_entity(entity).casefold():
            continue
        if field == "grade" and value.casefold() in str(identity.get("metal_type") or "").casefold():
            continue
        if field in {"species", "plywood_variant"}:
            value = value.title()
        if value not in secondary:
            secondary.append(value)
        if len(secondary) >= maximum_secondary_attributes:
            break
    return " ".join(parts) + (f", {', '.join(secondary)}" if secondary else "")


def canonical_material_display_name(
    entity: object,
    attributes: Mapping[str, Any] | None,
    *,
    fallback: object = "",
) -> str:
    """Return the one display name for every processed material projection.

    A recognised material family must always render through the canonical
    entity/attributes formatter, regardless of whether it is shown in the
    catalog, Review, a source-detail row, or a later estimation projection.
    An unknown family cannot truthfully be reformatted, so its persisted
    normalized label remains the explicit fallback until the row is resolved.
    """
    family = " ".join(str(entity or "").strip().split())
    if family and family.casefold() not in {"other", "unclassified", "unknown"}:
        return canonical_display_name(family, attributes)
    return " ".join(str(fallback or "Material").strip().split()) or "Material"


_SHEET_SIZE = re.compile(
    r"(?<![\d.])\d+(?:\.\d+)?\s*(?:mm|cm|m)?\s*[×xх]\s*\d+(?:\.\d+)?"
    r"\s*(?:mm|cm|m|millimet(?:res?|ers?))\b",
    re.IGNORECASE,
)
_BOARD_NAME = re.compile(r"\b(?:plywood|mdf|hdf|osb|ldsp|hardboard|particleboard|fibreboard|fiberboard)\b", re.I)
_LED_STRIP_LABEL = re.compile(
    r"^(?:COB\s+)?LED\s+(?:(?:flexible\s+)?strip\b(?!\s+(?:connector|adapter|clip|mount)\b)|\d{4}(?:/\d{4})*\s*K\b)",
    re.I,
)
_HDF_EXPANSION = re.compile(r"\bhigh[\s-]+density[\s-]+(?:fibre|fiber)[\s-]*board\b", re.I)
_MM = re.compile(r"\b(\d+(?:\.\d+)?)\s*mm\b", re.I)
_SECTIONS = {
    "round_tube": "Round Tube", "rectangular_tube": "Rectangular Tube", "square_tube": "Square Tube",
    "angle": "Angle", "flat_bar": "Flat Bar", "metal_flat_bar": "Flat Bar",
    "metal_profile_angle_channel": "", "metal_round_bar_rod_wire": "", "metal_tube": "",
}
_SHEET_FAMILIES = {
    "plywood": "Plywood", "plywood_special": "Plywood", "mdf_hdf": "", "melamine_faced_particleboard": "LDSP",
    "particleboard": "Particleboard", "fibreboard_hardboard": "Hardboard", "osb": "OSB",
    "gypsum_board": "Gypsum board", "timber_solid_wood_panel": "Solid Timber Panel",
    "aluminium_composite_panel": "Aluminium Composite Panel",
    "composite_sandwich_panel": "Sandwich Panel", "lightweight_sandwich_panel": "Lightweight Panel",
    "glass": "Glass", "mirror": "Mirror", "acrylic_pmma": "Acrylic",
    "polycarbonate_petg_pvc_abs": "", "sheet_plastic": "", "hpl_cpl": "",
    "compact_laminate": "Compact Laminate", "natural_stone_slab": "",
    "engineered_quartz_mineral_hybrid": "Quartz", "sintered_ultra_compact_surface": "Sintered Surface",
    "porcelain_ceramic_slab": "Porcelain", "solid_surface": "Solid Surface",
    "terrazzo_engineered_agglomerate": "Terrazzo", "sheet_metal": "",
}
_DEFAULT_TRAITS = {"raw", "standard", "standard indoor", "standard steel", "mill finish", "low iron", "silver"}
_SHEET_TRAITS = {
    "plywood_special": ("functional_subtype", "plywood_variant", "construction", "surface"),
    "mdf_hdf": ("surface", "grade"),
    "melamine_faced_particleboard": ("surface", "grade"),
    "particleboard": ("binder_type", "construction", "grade"),
    "fibreboard_hardboard": ("surface", "grade"),
    "osb": ("grade", "service_class"),
    "gypsum_board": ("grade", "service_class"),
    "timber_solid_wood_panel": ("construction",),
    "aluminium_composite_panel": ("fire_class",),
    "composite_sandwich_panel": ("core_type",),
    "lightweight_sandwich_panel": ("core_type",),
    "glass": ("treatment", "glass_type", "surface"),
    "mirror": ("tint", "backing", "treatment"),
    "acrylic_pmma": ("construction", "grade"),
    "polycarbonate_petg_pvc_abs": ("grade",),
    "sheet_plastic": ("grade",),
    "hpl_cpl": ("grade", "service_class"),
    "compact_laminate": ("core_type", "core_colour"),
    "natural_stone_slab": ("price_tier", "finish"),
    "engineered_quartz_mineral_hybrid": ("price_tier",),
    "sintered_ultra_compact_surface": ("price_tier",),
    "porcelain_ceramic_slab": ("price_tier",),
    "solid_surface": ("chemistry_product_type", "price_tier"),
    "terrazzo_engineered_agglomerate": ("binder_type",),
    "sheet_metal": ("functional_subtype", "grade"),
}
# Catalog entries predating structured subtype attributes use their canonical words.
_LEGACY_SHEET_TRAITS = {
    "plywood_special": r"aircraft.grade|aluminium.faced|hpl.faced|phenolic (?:film.faced|anti.slip)|flexible|decorative veneer.faced|fire.retardant|marine(?:\s+BS 1088)?",
    "mdf_hdf": r"moisture.resistant|fire.retardant|deep.routing|low.density lightweight|black core|through.coloured|bending|exterior|veneered|veneer|laminated|lacquered|melamine|acrylic",
    "melamine_faced_particleboard": r"single.sided|one.sided|\bP[3-7]\b",
    "particleboard": r"cement.bonded|moisture.resistant|fire.retardant",
    "fibreboard_hardboard": r"oil.tempered|perforated",
    "osb": r"(?:OSB\s*/|(?<!\w)/)\s*[2-4]\b",
    "gypsum_board": r"moisture.resistant|fire.resistant",
    "timber_solid_wood_panel": r"edge.glued|finger.jointed|solid slab",
    "aluminium_composite_panel": r"fire.retardant|\bA2\b",
    "composite_sandwich_panel": r"(?:balsa|foam|aluminium|paper)[- ](?:core|honeycomb)",
    "lightweight_sandwich_panel": r"(?:aluminium|paper) honeycomb|tubular.core",
    "glass": r"tempered safety|laminated safety|heat.strengthened|clear float|back.painted|ceramic printed|acid.etched|textured patterned|frosted|low.iron|wire reinforced|tinted",
    "mirror": r"safety.backed|bronze tinted|grey tinted|antique",
    "acrylic_pmma": r"cast|extruded",
    "polycarbonate_petg_pvc_abs": r"uv.stabilized|hard.coated|foam|solid|multiwall",
    "sheet_plastic": r"uv.stabilized|foam|corrugated",
    "hpl_cpl": r"chemical.resistant|exterior.grade|fire.retardant|postforming|anti.fingerprint",
    "compact_laminate": r"(?:black|white|kraft|through.coloured) core",
    "natural_stone_slab": r"(?:economy|standard|premium|luxury)(?: colour)? tier|polished|honed|leathered",
    "engineered_quartz_mineral_hybrid": r"(?:economy|standard|premium|luxury)(?: colour)? tier",
    "sintered_ultra_compact_surface": r"(?:economy|standard|premium|luxury)(?: colour)? tier",
    "porcelain_ceramic_slab": r"(?:economy|standard|premium|luxury)(?: colour)? tier",
    "solid_surface": r"acrylic|polyester|(?:economy|standard|premium|luxury)(?: colour)? tier",
    "terrazzo_engineered_agglomerate": r"cement.based|resin.based",
    "sheet_metal": r"perforated|chequered|checker|expanded|galvanized|(?:DX51D|S350GD)\+Z|S(?:235|275|355)",
}
_COMPONENT_FIELDS = {
    "hardware_drawer_slide": ("mechanism", "mounting_type", "nominal_length", "load_kg", "feature"),
    "hardware_hinge": ("hinge_type", "mounting_type", "cup_diameter_mm", "opening_angle_deg", "feature"),
    "hardware_lift_system": ("lift_type", "force_n", "load_class"),
    "hardware_door_system": ("mechanism", "nominal_size", "load_kg"),
    "hardware_drawer_system": ("system_type", "nominal_length", "side_height_mm"),
    "hardware_storage_system": ("system_type", "working_width_mm", "capacity"),
    "hardware_furniture_system": ("system_type", "working_width_mm", "working_height_mm"),
    "hardware_handle": ("handle_type", "hole_spacing_mm", "finish"),
    "hardware_lock_latch": ("component_type", "mechanism"),
    "hardware_connector": ("component_type", "diameter_mm", "mating_size"),
    "hardware_fastener": ("component_type", "fastener_size", "metal_type", "corrosion_class"),
    "hardware_mounting_part": ("component_type", "diameter_mm", "mating_size"),
    "hardware_leg_caster": ("component_type", "height_mm", "wheel_diameter_mm", "load_kg"),
    "hardware_electrical_component": ("component_type", "voltage_v", "power_w", "wire_gauge", "core_count"),
    "paint_lacquer_stain": ("coating_system", "finish"),
    "primer": ("coating_system", "substrate"),
    "powder_coating": ("coating_system", "finish", "colour_class"),
    "filler_hardener_thinner": ("component_type", "chemistry_product_type", "coating_system"),
    "packaging_material": ("packaging_type", "grade"),
    "purchased_fabricated_component": ("component_type", "functional_subtype", "mating_size"),
}


def _label_text(value: object) -> str:
    text = re.sub(r"(?<=\d),(?=\d)", ".", str(value or ""))
    return " ".join(text.replace(",", " ").replace("_", " ").split())


def _fact(specs: Mapping[str, Any], *keys: str) -> object:
    for key in keys:
        value = specs.get(key)
        if isinstance(value, (str, int, float)) and value and not isinstance(value, bool):
            return value
    return None


def _match(pattern: str, label: str) -> str:
    match = re.search(pattern, label, re.I)
    return match[0] if match else ""


def _number_with_unit(value: object, unit: str) -> str:
    number = _display_mm(value)
    return f"{number} {unit}" if number else ""


def _joined(*values: str) -> str:
    parts = []
    for value in values:
        if value and f" {_label_phrase(value)} " not in f" {_label_phrase(' '.join(parts))} ":
            parts.append(" ".join(value.split()))
    return " ".join(parts)


def _label_phrase(value: str) -> str:
    return re.sub(r"[^\w.°]+", " ", value.casefold()).strip()


def _thickness(specs: Mapping[str, Any], label: str) -> str:
    match = _MM.search(label)
    value = _fact(specs, "thickness_mm", "thickness") or (match[1] if match else None)
    return _number_with_unit(value, "mm")


def _sheet_label(family: str, label: str, specs: Mapping[str, Any]) -> str:
    entity = _SHEET_FAMILIES[family]
    if family == "mdf_hdf":
        board = _fact(specs, "board_type") or _match(r"\b(?:mdf|hdf)\b", label)
        if not board:
            return ""
        entity = str(board).upper() if str(board).casefold() in {"mdf", "hdf"} else _label_text(board)
    elif family in {"polycarbonate_petg_pvc_abs", "sheet_plastic"}:
        entity = _label_text(_fact(specs, "polymer", "substrate")) or _match(
            r"\b(?:polycarbonate|PETG|ABS|PVC|HDPE|LDPE|polyethylene|polypropylene|PTFE|POM|nylon)\b", label
        )
    elif family == "hpl_cpl":
        entity = _match(r"\b(?:HPL|CPL)\b", label)
    elif family == "natural_stone_slab":
        entity = _label_text(_fact(specs, "stone_type")).title() or _match(r"granite|marble|quartzite|limestone|travertine|slate|onyx", label)
    elif family == "sheet_metal":
        entity = _label_text(_fact(specs, "metal_type")).title() or _match(r"galvanized steel|stainless steel|steel|aluminium|brass|copper", label)
        entity = _joined(entity, "Sheet") if entity else ""
    elif family == "timber_solid_wood_panel":
        species = _label_text(_fact(specs, "species")).title()
        if not species:
            return ""
        entity = _joined(species, entity)
    elif family == "engineered_quartz_mineral_hybrid" and _match(r"mineral hybrid", label):
        entity = "Mineral Hybrid"
    elif family == "porcelain_ceramic_slab" and _match(r"\bceramic\b", label):
        entity = "Ceramic"
    elif family == "terrazzo_engineered_agglomerate" and not _match(r"terrazzo", label):
        entity = "Agglomerate"
    size = _thickness(specs, label)
    if not entity or not size:
        return ""
    if family == "plywood":
        service = _fact(specs, "required_service_class", "service_class")
        return _joined(entity, size, _label_text(service).title(),
                       _label_text(specs.get("required_species")).title(),
                       _label_text(specs.get("required_grade")).title())
    traits = [_label_text(specs.get(field)) for field in _SHEET_TRAITS.get(family, ())]
    pattern = _LEGACY_SHEET_TRAITS.get(family, "")
    if pattern:
        traits.extend(match[0] for match in re.finditer(r"(?<!\w)(?:" + pattern + r")(?!\w)", label, re.I))
    traits = [item for item in traits if item and item.casefold().replace("-", " ") not in _DEFAULT_TRAITS]
    if family == "osb" and traits:
        grade = re.search(r"[2-4]", traits[0])
        return _joined(f"OSB/{grade[0]}" if grade else entity, size)
    if family == "plywood_special" and not traits:
        return ""
    if family == "mdf_hdf":
        surface = _label_text(specs.get("surface"))
        sides = _match(r"(?:one|two)[- ]sided", surface or label)
        if any("veneer" in item.casefold() for item in traits):
            traits = [item for item in traits if "veneer" not in item.casefold()]
            entity = "Veneered " + entity
        traits = [re.sub(r"\s+(one|two) sided$", r" \1-sided", item, flags=re.I) for item in traits]
        if sides:
            traits.append(sides.replace(" ", "-"))
    return _joined(entity, size, *traits)


def _profile_label(family: str, label: str, specs: Mapping[str, Any]) -> str:
    entity = _SECTIONS[family] or _match(r"round tube|rectangular tube|square tube|round bar|flat bar|tube|rod|wire|angle|channel", label).title()
    if family == "metal_flat_bar":
        dimensions = specs.get("width_thickness")
        if isinstance(dimensions, Mapping):
            specs = {**dimensions, **specs}
    nominal = str(_fact(specs, "nominal_size", "profile_section", "section_profile") or "")
    pair = _match(r"\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?", nominal or label)
    diameter = _match(r"(?:ø|[dD])\s*\d+(?:\.\d+)?", nominal or label)
    if not pair and family in {"flat_bar", "metal_flat_bar"}:
        width = _display_mm(_fact(specs, "width_mm", "width"))
        thickness = _display_mm(_fact(specs, "thickness_mm", "thickness"))
        pair = f"{width} × {thickness}" if width and thickness else ""
    if pair:
        size = re.sub(r"\s*[x×]\s*", " × ", pair, flags=re.I) + " mm"
    else:
        diameter_value = re.sub(r"^[dø]\s*", "", diameter, flags=re.I) or _display_mm(_fact(specs, "diameter_mm", "diameter"))
        size = f"Ø{diameter_value} mm" if diameter_value else ""
    metal = _label_text(_fact(specs, "material_subfamily", "metal_type")) or _match(r"stainless|aluminium|copper|brass", label)
    if metal.casefold() in {"steel", "standard steel"}:
        metal = ""
    wall = _number_with_unit(_fact(specs, "wall_thickness_mm", "wall_thickness"), "mm")
    return _joined(metal.title(), entity, size, f"{wall} wall" if wall else "") if entity and size else ""


def _component_label(family: str, label: str, specs: Mapping[str, Any]) -> str:
    values = []
    for field in _COMPONENT_FIELDS.get(family, ()):
        keys = (field, "nominal_length_mm", "depth_mm") if field == "nominal_length" else (field,)
        value = _fact(specs, *keys)
        unit = {
            "nominal_length": "mm", "opening_angle_deg": "°", "force_n": "N",
            "load_kg": "kg", "voltage_v": "V", "power_w": "W",
        }.get(field, "mm" if field.endswith("_mm") else "")
        text = _number_with_unit(value, unit) if unit else _label_text(value)
        if text:
            values.append(text)
    if family == "hardware_hinge":
        label = re.sub(r"\s*\bdegree(?:s)?\b", "°", label, flags=re.I)
        values = [value.replace(" °", "°") for value in values]
    return _joined(label, *values)


def material_catalog_display_label(
    name: object,
    *,
    family: str = "",
    purchase_kind: str = "",
    specifications: Mapping[str, Any] | None = None,
) -> str:
    """Render the approved Family attributes without modifying the pricing identity."""
    specs = specifications or {}
    label = re.sub(r"(?<=\d),(?=\d)", ".", str(name or "Material").strip())
    if _LED_STRIP_LABEL.search(label):
        temperature = _fact(specs, "colour_temperature_k") or _match(r"\b\d{4}(?:/\d{4})*(?=\s*K\b)", label)
        if not temperature and (options := specs.get("colour_temperatures_k")):
            if isinstance(options, (tuple, list)):
                temperature = "/".join(filter(None, map(_display_mm, options)))
        watts = _fact(specs, "rated_w_per_m", "watts_per_m")
        if not watts and not re.search(r"standard output", label, re.I):
            watts = _match(r"\b\d+(?:\.\d+)?(?=\s*W\s*/\s*m\b)", label)
        volts = _fact(specs, "voltage_v") or _match(r"\b\d+(?:\.\d+)?(?=\s*V(?:DC)?\b)", label)
        if temperature or watts or volts:
            return _joined("LED", f"{temperature} K" if temperature else "",
                           _number_with_unit(watts, "W/m"), _number_with_unit(volts, "V"))
        return _label_text(label)
    if re.search(r"\bLED driver\b", label, re.I):
        volts = _fact(specs, "voltage_v") or _match(r"\b\d+(?:\.\d+)?(?=\s*V(?:DC)?\b)", label)
        watts = _fact(specs, "power_w", "led_driver_watts") or _match(r"\b\d+(?:\.\d+)?(?=\s*W\b)", label)
        if watts:
            return _joined("LED Driver", _number_with_unit(volts, "V"), _number_with_unit(watts, "W"))
    if family in _SECTIONS and (profile := _profile_label(family, label, specs)):
        return profile
    if purchase_kind == "sheet" or _BOARD_NAME.search(label) or family in _SHEET_FAMILIES:
        label = _SHEET_SIZE.sub("", label)
    if _HDF_EXPANSION.search(label):
        label = _HDF_EXPANSION.sub("" if re.search(r"\bHDF\b", label, re.I) else "HDF", label)
    if family in _SHEET_FAMILIES and (sheet := _sheet_label(family, label, specs)):
        return sheet
    if family == "edge_banding":
        combined = specs.get("width_thickness")
        dimensions = {**combined, **specs} if isinstance(combined, Mapping) else specs
        width = _display_mm(_fact(dimensions, "width_mm", "width"))
        thickness = _display_mm(_fact(dimensions, "thickness_mm", "thickness"))
        substrate = _label_text(_fact(specs, "substrate", "material_type")) or _match(r"\b(?:ABS|PVC|PP|Veneer|Melamine|Acrylic)\b", label)
        if substrate and width and thickness:
            if substrate.casefold() in {"abs", "pvc", "pp"}:
                substrate = substrate.upper()
            elif substrate.casefold() == "veneer":
                substrate = "Veneer"
            # In legacy records the upper band and "over" band share a numeric key.
            width_range = _match(r"over\s+\d+(?:\.\d+)?\s*mm\s*wide", label)
            return _joined(substrate, "Edge Banding", f"{width} × {thickness} mm",
                           _label_text(specs.get("finish")), width_range)
    if family == "wood_veneer" and (species := _label_text(_fact(specs, "species"))):
        backing = _label_text(_fact(specs, "backing", "construction")) or _match(r"paper.backed|fleece.backed", label)
        return _joined(species.title(), "Veneer", backing)
    if family in {"decorative_film_foil", "vinyl_film"}:
        kind = _label_text(_fact(specs, "film_type", "substrate")) or _match(r"PVC thermofoil|PET decorative foil|vinyl film|decorative film", label)
        if kind:
            width = _number_with_unit(_fact(specs, "working_width_mm", "width_mm", "width"), "mm")
            finish = _label_text(_fact(specs, "finish")) or _match(r"super.matt|high.gloss|matt|smooth", label)
            return _joined(kind, width, finish)
    if re.search(r"\b(?:plywood|hdf)\b", label, re.I):
        label = re.sub(r"\braw\b", "", label, flags=re.I)
    if re.match(r"mirror\b", label, re.I):
        label = re.sub(r"\blow[- ]iron\b", "", label, flags=re.I)
    label = " ".join(label.replace(",", " ").split())
    return _component_label(family, label, specs) or "Material"
