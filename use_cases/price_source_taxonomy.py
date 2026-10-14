"""Bilingual deterministic taxonomy for supplier price-source rows.

This module deliberately knows nothing about supplier identity, H.P. numbers,
issuer OCR or merge candidates. It receives one extracted line and can only
refine its material category, family and literal product attributes.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from use_cases.material_normalization import (
    canonical_material_display_name,
    normalize_identity_attributes,
)
from use_cases.material_identity_resolution import normalize_material_phrase
from use_cases.catalog_aliases import PriceSourceAliasContext


@dataclass(frozen=True)
class TaxonomyRule:
    category: str
    family: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class BrandRule:
    """A recognised manufacturer, deliberately scoped to proven categories.

    A brand is preservation evidence, never category evidence.  For example,
    the word ``Blum`` cannot turn unrelated source text into Hardware; it can
    only be retained after ordinary wording already proved a Hardware family.
    """

    brand: str
    categories: tuple[str, ...]
    aliases: tuple[str, ...]


def _price_source_category_for_catalog_family(
    family_code: str,
    category_name: str,
) -> str:
    """Return the established source display category for one catalog Family.

    This is a presentation bridge, not alias vocabulary.  Family recognition
    itself is supplied only by ``PriceSourceAliasContext``.
    """
    code = str(family_code or "")
    if code.startswith("hardware_"):
        return "Hardware"
    if code == "sheet_metal":
        return "Metal Sheets"
    if code in {"metal_flat_bar", "metal_round_bar_rod_wire"}:
        return "Metal Supplies"
    if code.startswith("metal_"):
        return "Metal Profiles"
    if code in {"glass", "mirror"}:
        return "Glass"
    if code in {
        "acrylic_pmma", "polycarbonate_petg_pvc_abs", "sheet_plastic",
        "vinyl_film", "aluminium_composite_panel", "composite_sandwich_panel",
    }:
        return "Plastics & Composites"
    if code in {
        "natural_stone_slab", "engineered_quartz_mineral_hybrid",
        "sintered_ultra_compact_surface", "porcelain_ceramic_slab",
        "solid_surface", "terrazzo_engineered_agglomerate",
    }:
        return "Stone"
    if code in {"paint_lacquer_stain", "primer", "powder_coating", "filler_hardener_thinner"}:
        return "Coating Supplies" if code == "filler_hardener_thinner" else "Paints & Coatings"
    if code in {"edge_banding", "decorative_film_foil", "wood_veneer", "hpl_cpl"}:
        return "Wood Supplies"
    if code == "packaging_material":
        return "Packaging"
    if code == "timber_solid_wood_panel":
        return "Solid Wood"
    return "Wood Sheets" if category_name else "Other"


def product_system_for_text(
    text: str,
    *,
    material_family: str,
    catalog_brand: str,
    alias_context: PriceSourceAliasContext,
) -> tuple[str, str] | None:
    """Return an exact recognised Hardware Product System and its brand.

    The caller must independently establish the Hardware family first. A
    system is never extracted from a supplier SKU and never supplies a length,
    capacity, price or a physical-model variant.
    """
    matches = [
        (len(_canonical_taxonomy_text(alias)), system)
        for alias, system in alias_context.product_system_aliases.items()
        if _has_alias(text, (alias,))
        and (not catalog_brand or system[1].casefold() == str(catalog_brand).casefold())
    ]
    selected = max(matches, default=(0, None), key=lambda match: match[0])[1]
    return (selected[0], selected[1]) if selected else None


# The curated catalogue is deliberately multilingual. Each entry has one
# English canonical display name and recognises Latin spelling, Israeli Hebrew
# transliteration, and only safe OCR variants. It is still not a fuzzy
# proper-name detector: an unknown name is preserved as candidate evidence,
# rather than being silently lost or permitted to select a material category.
#
# Israeli distributors are not listed merely because they sell a brand. These
# are product manufacturers or product-system brands. A supplier name belongs
# to supplier matching, not material identity.
def _literal_sheet_dimensions(text: str) -> tuple[int, int]:
    """Return only dimensions actually written in the source line.

    Some Israeli invoices use ``2* 3100`` or ``1* 3100`` beside sheet names.
    The star is a sheet notation, not a second dimension. A second side is
    accepted only from an explicit ``x`` or ``×`` separator. Otherwise retain
    the single proven span and never invent a square 3100×3100 sheet.
    """
    explicit_pair = re.search(
        r"(?<!\d)([1-5]\d{3})\s*(?:x|×)\s*([1-5]\d{3})(?!\d)",
        text,
        flags=re.IGNORECASE,
    )
    if explicit_pair:
        return int(explicit_pair.group(1)), int(explicit_pair.group(2))
    spans = [
        int(value)
        for value in re.findall(r"(?<!\d)([1-5]\d{3})(?!\d)", text)
    ]
    return (0, spans[0]) if spans else (0, 0)


def source_row_text(row: Mapping[str, Any]) -> str:
    # Taxonomy is grounded in source wording. A model-supplied family from a
    # previous pass must not create a false species/category proof.
    return " ".join(
        str(value or "")
        for value in (
            row.get("raw_description") or row.get("normalized_name") or "",
            # Structured workbook columns are literal row evidence. They are
            # transient processing context, not a replacement for the source
            # description shown to the user or a model-produced attribute.
            row.get("_source_table_evidence") or "",
        )
    ).casefold()


_HEBREW_FINAL_FORMS = str.maketrans({
    "ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ",
})
_TAXONOMY_NOISE_RE = re.compile(r"[\u0591-\u05c7'\"׳״`.,;:/\\|()[\]{}+=*_\-]+")
_TAXONOMY_CONNECTORS = {"and", "plus", "with", "ו"}
_OCR_NEAR_COLLISIONS = frozenset({frozenset({"glass", "gloss"})})


def _canonical_taxonomy_text(value: object) -> str:
    """Make literal Hebrew and English evidence comparable without translation.

    Invoice OCR varies punctuation, niqqud, Hebrew final forms and the joined
    conjunction ``ו``. Normalising those forms is deterministic evidence
    handling, unlike guessing a category from an unrelated brand name.
    """
    text = str(value or "").casefold().translate(_HEBREW_FINAL_FORMS)
    text = _TAXONOMY_NOISE_RE.sub(" ", text)
    return " ".join(text.split())


def _without_hebrew_conjunction(token: str) -> str:
    return token[1:] if len(token) > 2 and token.startswith("ו") else token


def _edit_distance_at_most_one(left: str, right: str) -> bool:
    """Return whether two short OCR tokens differ by at most one edit."""
    if left == right:
        return True
    if abs(len(left) - len(right)) > 1:
        return False
    if len(left) == len(right):
        mismatches = sum(a != b for a, b in zip(left, right))
        return mismatches <= 1
    shorter, longer = (left, right) if len(left) < len(right) else (right, left)
    index = 0
    while index < len(shorter) and shorter[index] == longer[index]:
        index += 1
    return shorter[index:] == longer[index + 1:]


def _compound_alias_matches(text: str, alias: str) -> bool:
    """Allow one OCR typo only when a phrase has multiple corroborating words."""
    alias_tokens = [
        token for token in _canonical_taxonomy_text(alias).split()
        if token not in _TAXONOMY_CONNECTORS
    ]
    if len(alias_tokens) < 2:
        return False
    text_tokens = [
        _without_hebrew_conjunction(token)
        for token in _canonical_taxonomy_text(text).split()
    ]
    for alias_token in alias_tokens:
        candidate_tokens = [token for token in text_tokens if token == alias_token]
        if candidate_tokens:
            continue
        # A one-character OCR error in a short Hebrew root is acceptable only
        # because another independent word in the same compound phrase must
        # match too. Single-word aliases never use this fallback.
        if not any(
            len(alias_token) >= 3
            and frozenset({token, alias_token}) not in _OCR_NEAR_COLLISIONS
            and _edit_distance_at_most_one(token, alias_token)
            for token in text_tokens
        ):
            return False
    return True


def _has_alias(text: str, aliases: tuple[str, ...]) -> bool:
    canonical_text = _canonical_taxonomy_text(text)
    for alias in aliases:
        canonical_alias = _canonical_taxonomy_text(alias)
        # A taxonomy token must not match inside another word. In particular,
        # ``stain`` in ``stainless`` is not coating evidence.
        if canonical_alias and re.search(
            rf"(?<!\w){re.escape(canonical_alias)}(?!\w)", canonical_text,
            flags=re.UNICODE,
        ):
            return True
        if _compound_alias_matches(canonical_text, canonical_alias):
            return True
    return False


def material_rule_for_text(
    text: str,
    *,
    alias_context: PriceSourceAliasContext,
) -> TaxonomyRule | None:
    # Product-system words are long and OCR-prone. Unlike broad family words,
    # they must match literally here: ``Mario Box`` cannot become MERIVOBOX.
    # Exact recognised systems are still classified before raw "glass" or
    # "profile" wording takes the line into a material department.
    system_matches = [
        (len(_canonical_taxonomy_text(alias)), alias, system)
        for alias, system in alias_context.product_system_aliases.items()
        if _has_alias(text, (alias,))
    ]
    if system_matches:
        _length, alias, system = max(system_matches, key=lambda match: match[0])
        family_code = system[2]
        return TaxonomyRule(
            _price_source_category_for_catalog_family(
                family_code, alias_context.family_categories.get(family_code, ""),
            ),
            family_code,
            (alias,),
        )
    matches: list[tuple[int, TaxonomyRule]] = []
    for family_code, aliases in alias_context.family_aliases.items():
        matched_aliases = [
            alias for alias in aliases
            if _canonical_taxonomy_text(alias) not in alias_context.ambiguous_family_aliases
            and _has_alias(text, (alias,))
        ]
        if not matched_aliases:
            continue
        category = _price_source_category_for_catalog_family(
            family_code, alias_context.family_categories.get(family_code, ""),
        )
        matches.append((
            max(len(_canonical_taxonomy_text(alias)) for alias in matched_aliases),
            TaxonomyRule(category, family_code, tuple(matched_aliases)),
        ))
    return max(matches, default=(0, None), key=lambda match: match[0])[1]


def brand_for_text(
    text: str,
    *,
    category: str,
    alias_context: PriceSourceAliasContext,
) -> str:
    """Return a curated brand only after the material category is proven."""
    matches = [
        (len(_canonical_taxonomy_text(alias)), brand)
        for alias_key, brand in alias_context.brand_aliases.items()
        for alias in (alias_key,)
        if _has_alias(text, (alias,))
    ]
    return max(matches, default=(0, ""), key=lambda match: match[0])[1]


_BRAND_CANDIDATE_NOISE = frozenset({
    "abs", "aluminium", "aluminum", "assembly", "black", "blue", "box", "carbon", "closure", "edge",
    "door", "drawer", "front", "glass", "grey", "high", "hinge", "internal",
    "large", "left", "mdf", "metal", "okoume", "particleboard", "plywood",
    "gas", "polyurethane", "powder", "profile", "pvc", "pure", "right", "sheet", "small",
    "solid", "stainless", "steel", "twin", "white", "wood", "natural",
})


def _brand_candidate_from_text(text: str) -> str:
    """Keep an unlisted Latin proper-name candidate without classifying by it.

    The catalog is deliberately incomplete. A final two-word title-cased or
    uppercase run such as ``Mario Box`` is useful brand evidence, while
    ordinary title-cased product prose such as ``Glass Door`` is not. The
    candidate remains low-confidence metadata and never changes a category.
    """
    tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9-]*\b", str(text or ""))
    runs: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        is_proper = (
            (len(token) > 1 and token.isupper())
            or (len(token) > 1 and token[0].isupper())
        )
        if is_proper:
            current.append(token)
            continue
        if current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    for run in reversed(runs):
        for index, token in enumerate(run):
            # Product codes are SKU evidence, not a candidate manufacturer.
            # Keeping one in the identity would recreate the same material
            # merely because an invoice has an unknown stock code.
            if any(character.isdigit() for character in token):
                continue
            if token.casefold() in _BRAND_CANDIDATE_NOISE:
                continue
            candidate = run[index:index + 2]
            return " ".join(candidate)
    return ""


def _explicit_technical_grade(text: str) -> str:
    """Extract standards and alloy grades, never treating them as brands."""
    match = re.search(
        r"\b(?:aisi\s*[- ]?)?(?:304l?|316l?|201|430|s[0-9]{3}|st\s*[- ]?37|"
        r"al\s*[- ]?(?:6061|6063|5083))\b",
        str(text or ""),
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    value = match.group(0).upper().replace("-", " ")
    if value.startswith("AISI"):
        digits = re.sub(r"\D", "", value)
        return f"AISI {digits}" if digits else ""
    return re.sub(r"\s+", "", value)


def _explicit_profile_primary_attribute(text: str) -> str:
    """Use an explicit profile section as the primary display attribute."""
    match = re.search(
        r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*(?:x|×)\s*(\d{1,3}(?:\.\d+)?)\s*(?:mm|מ[\"״']?מ)?",
        str(text or ""),
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    return f"{match.group(1)}×{match.group(2)} mm"


def _decimal_label(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def _metric_dimension(value: str, unit: str | None) -> float:
    parsed = float(value)
    normalized_unit = str(unit or "mm").casefold()
    return parsed * 10 if normalized_unit in {"cm", 'ס"מ', "ס׳מ", "ס״מ", "סמ"} else parsed


def _profile_dimensions(text: str) -> tuple[float, float, float]:
    """Read ``section × section × wall`` only when it is printed as one run."""
    match = re.search(
        r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*(?:x|×)\s*"
        r"(\d{1,3}(?:\.\d+)?)\s*(?:x|×)\s*"
        r"(\d{1,2}(?:\.\d+)?)\s*(mm|m\.?m\.?|cm|ס[\"״']?מ)?(?!\w)",
        str(text or ""),
        flags=re.IGNORECASE,
    )
    if not match:
        return 0, 0, 0
    unit = match.group(4)
    return (
        _metric_dimension(match.group(1), unit),
        _metric_dimension(match.group(2), unit),
        _metric_dimension(match.group(3), unit),
    )


def _round_tube_dimensions(text: str) -> tuple[float, float]:
    value = str(text or "")
    match = re.search(
        r"(?:round\s+tube|round\s+pipe|צינור\s+עגול)[^\d]{0,32}"
        r"(\d{1,3}(?:\.\d+)?)\s*(mm|m\.?m\.?|cm|ס[\"״']?מ)?\s*(?:x|×)\s*"
        r"(\d{1,2}(?:\.\d+)?)\s*(mm|m\.?m\.?|cm|ס[\"״']?מ)?",
        value,
        flags=re.IGNORECASE,
    )
    if not match:
        return 0, 0
    return (
        _metric_dimension(match.group(1), match.group(2)),
        _metric_dimension(match.group(3), match.group(4) or match.group(2)),
    )


def _edge_banding_dimensions(text: str) -> tuple[float, float]:
    match = re.search(
        r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*(mm|m\.?m\.?|cm|ס[\"״']?מ)?\s*"
        r"(?:x|×)\s*(\d{1,2}(?:\.\d+)?)\s*(mm|m\.?m\.?|cm|ס[\"״']?מ)?",
        str(text or ""),
        flags=re.IGNORECASE,
    )
    if not match:
        return 0, 0
    return (
        _metric_dimension(match.group(1), match.group(2)),
        _metric_dimension(match.group(3), match.group(4) or match.group(2)),
    )


def _catalog_value_for_text(
    text: str,
    *,
    values: Mapping[str, tuple[str, ...]],
) -> str:
    """Return the longest catalogued Pricing Key value proven by text."""
    matches = [
        (len(_canonical_taxonomy_text(alias)), canonical)
        for canonical, aliases in values.items()
        for alias in aliases
        if _has_alias(text, (alias,))
    ]
    return max(matches, default=(0, ""), key=lambda match: match[0])[1]


def _pricing_key_values_for_family(
    family: str,
    alias_context: PriceSourceAliasContext,
) -> Mapping[str, Mapping[str, tuple[str, ...]]]:
    return alias_context.attribute_value_aliases.get(str(family or ""), {})


def _apply_family_pricing_facts(
    attributes: dict[str, Any],
    *,
    family: str,
    text: str,
    alias_context: PriceSourceAliasContext,
) -> None:
    """Populate only deterministic Pricing Key facts for the proven family."""
    pricing_key_values = _pricing_key_values_for_family(family, alias_context)
    if family in {"sheet_metal", "metal_tube", "metal_profile_angle_channel", "metal_flat_bar", "metal_round_bar_rod_wire"}:
        metal_type = _catalog_value_for_text(text, values=pricing_key_values.get("metal_type", {}))
        if metal_type:
            attributes["metal_type"] = metal_type
    if family == "metal_tube":
        # The first number in ``40×20×2`` or ``25×1.5`` is a section, not a
        # sheet thickness. Do not carry that accidental generic parser value
        # into later price matching.
        attributes["thickness_mm"] = 0
        explicit_section = _catalog_value_for_text(
            text, values=pricing_key_values.get("section_profile", {}),
        )
        if explicit_section:
            attributes["section_profile"] = explicit_section
        first, second, wall = _profile_dimensions(text)
        if first and second and wall:
            if not attributes.get("section_profile"):
                attributes["section_profile"] = "square tube" if first == second else "rectangular tube"
            attributes["primary_attribute"] = f"{_decimal_label(first)}×{_decimal_label(second)} mm"
            attributes["wall_thickness_mm"] = wall
        else:
            diameter, wall = _round_tube_dimensions(text)
            if diameter and wall:
                attributes["section_profile"] = "round tube"
                attributes["primary_attribute"] = f"Ø{_decimal_label(diameter)} mm"
                attributes["diameter_mm"] = diameter
                attributes["wall_thickness_mm"] = wall
    elif family == "metal_profile_angle_channel":
        attributes["thickness_mm"] = 0
        profile = _catalog_value_for_text(
            text, values=pricing_key_values.get("section_profile", {}),
        )
        attributes["section_profile"] = profile
        first, second, wall = _profile_dimensions(text)
        if first and second:
            attributes["primary_attribute"] = f"{_decimal_label(first)}×{_decimal_label(second)} mm"
        if wall:
            attributes["wall_thickness_mm"] = wall
    elif family == "metal_flat_bar":
        width, thickness = _edge_banding_dimensions(text)
        if width and thickness:
            attributes["width_mm"] = width
            attributes["thickness_mm"] = thickness
            attributes["primary_attribute"] = f"{_decimal_label(width)}×{_decimal_label(thickness)} mm"
            attributes["section_profile"] = "flat bar"
    elif family == "metal_round_bar_rod_wire":
        diameter = _explicit_thickness_mm(text)
        if diameter:
            # A round bar's printed dimension is a diameter, never sheet
            # thickness. This is the only price-bearing dimensional axis for
            # this family.
            attributes["thickness_mm"] = 0
            attributes["diameter_mm"] = diameter
            attributes["primary_attribute"] = f"Ø{_decimal_label(diameter)} mm"
    elif family == "natural_stone_slab":
        attributes["finish"] = ""
        stone_type = _catalog_value_for_text(text, values=pricing_key_values.get("stone_type", {}))
        if stone_type:
            attributes["stone_type"] = stone_type
    elif family in {"powder_coating", "paint_lacquer_stain", "primer"}:
        attributes["coating_system"] = _catalog_value_for_text(
            text, values=pricing_key_values.get("coating_system", {}),
        )
    elif family == "edge_banding":
        width, thickness = _edge_banding_dimensions(text)
        if width and thickness:
            attributes["width_mm"] = width
            attributes["thickness_mm"] = thickness
            attributes["primary_attribute"] = f"{_decimal_label(width)}×{_decimal_label(thickness)} mm"
        canonical_text = _canonical_taxonomy_text(text)
        if "pvc" in canonical_text or "פי וי סי" in canonical_text:
            attributes["substrate"] = "pvc"
        elif "abs" in canonical_text or "איי בי אס" in canonical_text:
            attributes["substrate"] = "abs"


def job_operation_for_text(
    text: str,
    *,
    alias_context: PriceSourceAliasContext,
) -> str | None:
    matches = [
        (len(_canonical_taxonomy_text(alias)), payload)
        for alias, payload in alias_context.operation_aliases.items()
        if _has_alias(text, (alias,))
    ]
    return str(max(matches, default=(0, {}), key=lambda match: match[0])[1].get("operation_code") or "") or None


def _explicit_thickness_mm(text: str) -> float:
    """Read source-proven thickness, including common Hebrew/English aliases.

    A number becomes a thickness only when it has a physical unit, an explicit
    thickness label, or immediately follows a known sheet-material token.
    Gauge and cal are intentionally not converted here: their millimetre
    equivalent depends on material and standard.
    """
    value = str(text or "")
    explicit = re.search(
        r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*"
        r"(mm|m\.?m\.?|millimet(?:er|re)s?|מ[\"״']?מ|ס[\"״']?מ|cm|centimet(?:er|re)s?)(?!\w)",
        value,
        flags=re.IGNORECASE,
    )
    if explicit:
        thickness = float(explicit.group(1))
        unit = explicit.group(2).casefold()
        if unit.startswith(("cm", "ס")) or "centimet" in unit:
            thickness *= 10
        return thickness if 0.1 <= thickness <= 10_000 else 0

    labelled = re.search(
        # ``t`` is an accepted drawing abbreviation, but it must be an
        # independent token.  Without these boundaries the final letter of
        # ``lift 100 N`` was read as a thickness label.
        r"(?:(?<!\w)(?:thickness|thk|th\.?|t\.?)(?!\w)|עובי)\s*[:=]?\s*(\d{1,3}(?:\.\d+)?)(?!\d)",
        value,
        flags=re.IGNORECASE,
    )
    if labelled:
        thickness = float(labelled.group(1))
        return thickness if 0.1 <= thickness <= 100 else 0

    compact_sheet = re.search(
        r"(?:\b(?:mdf|hdf|plywood|particleboard|osb|hardboard|twin|combi)\b|"
        r"מדפ|לביד|דיקט|סיבית|מזונית|טווין|קומבי)\s*(\d{1,2}(?:\.\d+)?)(?!\d)",
        value,
        flags=re.IGNORECASE,
    )
    if compact_sheet:
        thickness = float(compact_sheet.group(1))
        return thickness if 0.1 <= thickness <= 100 else 0
    return 0


def _drawer_slide_depth_mm(text: str) -> float:
    """Return a drawer runner's explicit nominal depth in millimetres.

    This is intentionally narrower than generic dimension parsing. A bare
    number in a supplier SKU is not a depth, while a stated 55/75/76 cm runner
    length is the identity-defining attribute for this Hardware family.
    """
    match = re.search(
        r"(?<!\d)(\d{2,4}(?:\.\d+)?)\s*"
        r"(mm|cm|מ[\"״']?מ|ס[\"״']?מ|ס)(?!\w)",
        str(text or ""),
        flags=re.IGNORECASE,
    )
    if not match:
        return 0
    value = float(match.group(1))
    unit = match.group(2).casefold()
    # Some Hebrew invoice OCR drops the final ``מ`` from ``ס״מ``. This parser
    # runs only after the line is proven to be a drawer slide, so a bare Hebrew
    # ``ס`` after a plausible nominal length is safely a centimetre signal.
    depth = value * 10 if unit in {"cm", 'ס"מ', "ס׳מ", "ס״מ", "סמ", "ס"} else value
    return depth if 250 <= depth <= 1_200 else 0


def apply_operation_taxonomy(
    row: dict[str, Any],
    *,
    alias_context: PriceSourceAliasContext,
) -> str | None:
    """Repair a material-vs-service model error from literal source wording.

    This deterministic pass has no supplier inputs. It promotes only explicit
    service phrases, preserving bare product phrases such as a PVC edge-band
    roll for the material taxonomy.
    """
    text = source_row_text(row)
    matches = [
        (len(_canonical_taxonomy_text(alias)), payload)
        for alias, payload in alias_context.operation_aliases.items()
        if payload.get("service_only") and _has_alias(text, (alias,))
    ]
    operation_code = str(max(matches, default=(0, {}), key=lambda match: match[0])[1].get("operation_code") or "")
    if not operation_code:
        return None
    row["item_kind"] = "operation_service"
    row["material_type"] = "Other"
    row["material_family"] = "supplier processing"
    if operation_code == "supplier_cut_and_edge_banding":
        row["normalized_name"] = "Cutting and edge banding"
    row["reason_codes"] = sorted(
        set(row.get("reason_codes") or []) | {"taxonomy_operation_service"}
    )
    return operation_code


def _taxonomy_material_name(
    rule: TaxonomyRule,
    attributes: Mapping[str, Any],
    *,
    alias_context: PriceSourceAliasContext,
) -> str:
    """Build the shared compact display from structured, proven facts only."""
    return canonical_material_display_name(
        alias_context.family_names.get(rule.family, rule.family.replace("_", " ")),
        attributes,
    )


def _discard_redundant_plywood_brand(attributes: dict[str, Any]) -> None:
    """Keep plywood trade variants once, as a secondary source fact.

    Twin, Combi and Okoume are often emitted by extraction as a candidate
    brand as well as a variant or species. They are not hardware-style brands
    and must neither appear twice in a company material name nor affect the
    generic raw-plywood estimation class.
    """
    brand = normalize_material_phrase(attributes.get("brand"))
    if not brand:
        return
    non_brand_terms = {
        normalize_material_phrase(attributes.get("plywood_variant")),
        normalize_material_phrase(attributes.get("species")),
        "okuma",
        "okume",
        "okoume",
        "twin",
        "combi",
    }
    if brand in non_brand_terms:
        attributes["brand"] = ""
        attributes["brand_basis"] = "unknown"


def apply_material_taxonomy(
    row: dict[str, Any],
    *,
    alias_context: PriceSourceAliasContext,
) -> bool:
    """Apply only literal bilingual evidence to one material row.

    Unknown terms are intentionally retained in the raw line. They cannot undo
    a category independently proven by the remaining text.
    """
    if row.get("item_kind") != "material":
        return False
    text = source_row_text(row)
    rule = material_rule_for_text(text, alias_context=alias_context)
    if not rule:
        return False

    source_attributes = dict(row.get("identity_attributes") or {})
    # Taxonomy is now deliberately applied before schema validation. Preserve
    # the strict identity contract even when a rule clears an unsupported model
    # guess or only proves one field.
    attributes = normalize_identity_attributes(source_attributes)
    # A structured field must be explicitly source-proved. The normalizer does
    # not keep stale agent guesses merely because they are grammatical words.
    # They remain in raw evidence, but never identity, merge or display.
    catalog_attribute_rules = alias_context.attribute_value_aliases.get(rule.family, {})
    attribute_fields = tuple(catalog_attribute_rules)
    for field in attribute_fields:
        attributes.pop(field, None)
    # Dimensions generated by a prior model pass are not source evidence.
    # The taxonomy below restores only dimensions proven by deterministic
    # source parsing, so they can safely participate in the universal name.
    for field in ("thickness_mm", "width_mm", "length_mm", "depth_mm", "diameter_mm"):
        attributes[field] = 0
    # Display identity must be reconstructed from source evidence as well.
    # A previous model phrase can be helpful context in raw evidence, but it
    # must not keep arbitrary prose alive as an identity attribute.
    attributes["primary_attribute"] = ""
    attribute_rules = (
        (field, tuple((canonical, aliases) for canonical, aliases in values.items()))
        for field, values in catalog_attribute_rules.items()
    )
    for field, values in attribute_rules:
        for canonical, aliases in values:
            if _has_alias(text, aliases):
                if field == "construction":
                    # Construction facts compose. A Twin sheet may also be
                    # perforated, and both distinctions belong to its merge
                    # identity, rather than whichever alias appears first.
                    attributes[field] = " ".join(sorted({
                        *str(attributes.get(field) or "").split(), canonical,
                    }))
                    continue
                attributes[field] = canonical
                break
    catalog_brand = brand_for_text(text, category=rule.category, alias_context=alias_context)
    existing_brand = str(attributes.get("brand") or "").strip()
    if catalog_brand:
        attributes["brand"] = catalog_brand
        attributes["brand_basis"] = "catalog"
    elif existing_brand:
        # The extractor can retain a source-proved brand that has not reached
        # our curated catalogue yet. It is a candidate, never a category cue.
        attributes["brand"] = existing_brand
        attributes["brand_basis"] = "candidate"
    elif candidate_brand := _brand_candidate_from_text(str(row.get("raw_description") or "")):
        attributes["brand"] = candidate_brand
        attributes["brand_basis"] = "candidate"
    if rule.category == "Hardware":
        product_system = product_system_for_text(
            text,
            material_family=rule.family,
            catalog_brand=(
                str(attributes.get("brand") or "")
                if attributes.get("brand_basis") == "catalog" else ""
            ),
            alias_context=alias_context,
        )
        if product_system:
            system_name, system_brand = product_system
            attributes["product_system"] = system_name
            # The exact recognised system is curated, family-scoped evidence
            # of its manufacturer. It may never classify a non-Hardware line.
            if attributes.get("brand_basis") != "catalog":
                attributes["brand"] = system_brand
                attributes["brand_basis"] = "catalog"
    literal_thickness = _explicit_thickness_mm(text)
    if literal_thickness:
        attributes["thickness_mm"] = literal_thickness
    sheet_categories = {
        "Wood Sheets", "Metal Sheets", "Glass", "Plastics & Composites", "Stone",
    }
    if rule.category in sheet_categories:
        try:
            thickness = float(attributes.get("thickness_mm") or 0)
        except (TypeError, ValueError):
            thickness = 0
        if thickness:
            attributes["primary_attribute"] = (
                f"{int(thickness) if thickness.is_integer() else thickness} mm"
            )
    elif rule.category == "Metal Profiles":
        attributes["primary_attribute"] = _explicit_profile_primary_attribute(text)
    elif rule.family == "hardware_drawer_slide":
        # The supplier SKU can encode a model such as 55B or 76B. Those are
        # not runner lengths, and a model/agent numeric guess must never make
        # a slide look complete. Retain only an explicit length printed in the
        # source text, for example 550 mm or 55 cm.
        attributes["depth_mm"] = 0
        attributes["length_mm"] = 0
        attributes["width_mm"] = 0
        depth = _drawer_slide_depth_mm(text)
        if depth:
            attributes["depth_mm"] = depth
            attributes["primary_attribute"] = (
                f"{int(depth) if depth.is_integer() else depth} mm"
            )
    elif rule.category == "Hardware" and not str(attributes.get("primary_attribute") or "").strip():
        try:
            first_dimension = _explicit_thickness_mm(text)
        except (TypeError, ValueError):
            first_dimension = 0
        if first_dimension:
            attributes["primary_attribute"] = (
                f"{int(first_dimension) if first_dimension.is_integer() else first_dimension} mm"
            )
    if technical_grade := _explicit_technical_grade(text):
        attributes["grade"] = technical_grade
    _apply_family_pricing_facts(
        attributes, family=rule.family, text=text, alias_context=alias_context,
    )
    # For ordinary catalogue MDF, a stated decor or colour denotes a faced
    # board. Through-coloured MDF is exceptional and requires explicit source
    # evidence, so it must not be inferred from a colour word alone.
    if rule.family == "mdf_hdf" and str(attributes.get("colour") or "").strip():
        attributes["construction"] = "plastic laminate faced"
    if rule.family == "plywood":
        _discard_redundant_plywood_brand(attributes)
    attributes = normalize_identity_attributes(attributes)
    if rule.category in sheet_categories or rule.family == "timber_solid_wood_panel":
        # Model-generated dimensions are not source evidence. Rebuild this
        # pair from literal text so a single 3100 span cannot become 3100×3100
        # or acquire an unrelated 2400 side. Solid timber panels use the same
        # explicit pair grammar, but retain their distinct Family policy.
        attributes["width_mm"], attributes["length_mm"] = _literal_sheet_dimensions(text)
    row["identity_attributes"] = attributes
    row["material_type"] = rule.category
    row["material_family"] = rule.family
    canonical_name = _taxonomy_material_name(rule, attributes, alias_context=alias_context)
    # Every ingestion route converges on this compact canonical form. Raw
    # supplier prose remains intact in ``raw_description`` for evidence, but
    # secondary non-attributes can neither leak into the catalog nor split a
    # material identity downstream.
    row["normalized_name"] = canonical_name
    reasons = set(row.get("reason_codes") or [])
    reasons.discard("unknown_product_term")
    reasons.add(f"taxonomy_{rule.category.casefold().replace(' ', '_')}")
    row["reason_codes"] = sorted(reasons)
    # Do not override a real pricing, VAT, unit, or arithmetic blocker.  A
    # row unresolved solely because the model did not recognise a term that
    # the deterministic taxonomy does recognise is safe to continue.
    if row.get("status") == "unresolved" and not (reasons & {
        "missing_unit", "ambiguous_unit", "package_conversion_unresolved",
        "line_total_inconsistent", "unit_price_mismatch", "vat_basis_unknown",
        "document_total_mismatch", "ambiguous_material",
    }):
        row["status"] = "ready"
    return True


def normalize_sheet_name(name: object) -> str:
    return re.sub(r"\s+", " ", re.sub(
        r"\b(?:sheet|sheets|panel|board|\d+\s*[- ]?sheet)\b", "", str(name or ""), flags=re.I,
    )).strip(" ,-")
