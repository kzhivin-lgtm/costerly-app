"""Bilingual deterministic taxonomy for supplier price-source rows.

This module deliberately knows nothing about supplier identity, H.P. numbers,
issuer OCR or merge candidates. It receives one extracted line and can only
refine its material category, family and literal product attributes.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping


@dataclass(frozen=True)
class TaxonomyRule:
    category: str
    family: str
    aliases: tuple[str, ...]


# Keep the four product areas represented by the existing catalog categories:
# Wood (sheets, solid timber, supplies and fittings), Metal, Coating and the
# separate Material Jobs lane.  English and Hebrew aliases resolve to exactly
# the same canonical category/family.
MATERIAL_RULES: tuple[TaxonomyRule, ...] = (
    # Wood, furniture fittings first so a metal hinge never becomes Metal.
    TaxonomyRule("Hardware", "drawer slide", (
        "drawer slide", "drawer runner", "drawer rail", "undermount", "runner",
        "מסילת מגירה", "מסילה למגירה", "מסילה תחתית", "מסילה כפולה",
    )),
    TaxonomyRule("Hardware", "hinge", ("hinge", "hinges", "ציר", "צירים")),
    TaxonomyRule("Hardware", "mounting plate", (
        "mounting plate", "mounting bracket", "bracket", "clip", "latch",
        "פלטת חיבור", "תושבת", "קליפ", "סוגר",
    )),
    TaxonomyRule("Hardware", "handle", ("handle", "knob", "pull", "ידית", "כפתור")),
    TaxonomyRule("Hardware", "furniture leg", (
        "furniture leg", "cabinet leg", "plinth leg", "adjustable leg", "gas lift",
        "רגלית", "רגל מתכווננת", "בוכנת גז", "מנגנון קלפה",
    )),
    # Wood sheets. Twin and Okoume prove plywood, but are attributes, not brands.
    TaxonomyRule("Wood Sheets", "plywood", (
        "plywood", "lumber core", "sanded plywood", "לביד", "דיקט", "סנדוויץ",
        "okume", "okoume", "אוקומה", "אוקמה", "twin", "טווין", "combi", "קומבי",
    )),
    TaxonomyRule("Wood Sheets", "mdf", ("mdf", "מדי אף", "אמ די אף")),
    TaxonomyRule("Wood Sheets", "particleboard", (
        "particleboard", "chipboard", "melamine board", "laminated board",
        "סיבית", "מלמין", "שבבית",
    )),
    TaxonomyRule("Wood Sheets", "hardboard", ("hardboard", "hdf", "מזונית", "הארדבורד")),
    TaxonomyRule("Glass", "glass", ("glass", "mirror", "זכוכית", "מראה")),
    TaxonomyRule("Solid Wood", "solid timber", (
        "solid wood", "timber", "lumber", "plank", "board", "beam", "batten", "slat",
        "עץ מלא", "קורה", "קורות", "קרש", "קרשים", "לוח עץ", "סרגל", "לטה",
    )),
    TaxonomyRule("Wood Supplies", "veneer", ("veneer", "פורניר")),
    TaxonomyRule("Wood Supplies", "edge banding", ("edge band", "edgeband", "קנט", "קנטים")),
    # Metal.
    TaxonomyRule("Metal Profiles", "metal profile", (
        "metal profile", "aluminium profile", "aluminum profile", "tube", "pipe", "angle", "channel",
        "פרופיל", "אלומיניום", "צינור", "זווית", "תעלה",
    )),
    TaxonomyRule("Metal Sheets", "metal sheet", (
        "sheet metal", "steel sheet", "aluminium sheet", "aluminum sheet", "plate", "metal plate",
        "פח", "פלטת מתכת", "לוח אלומיניום", "נירוסטה",
    )),
    TaxonomyRule("Metal Supplies", "metal bar", (
        "round bar", "flat bar", "solid bar", "rod", "wire", "מוט", "פס שטוח", "חוט",
    )),
    # Coating.
    TaxonomyRule("Paints & Coatings", "paint", ("paint", "colour paint", "צבע", "צבע יסוד")),
    TaxonomyRule("Paints & Coatings", "lacquer", ("lacquer", "varnish", "לכה")),
    TaxonomyRule("Paints & Coatings", "primer", ("primer", "יסוד", "פריימר")),
    TaxonomyRule("Paints & Coatings", "powder coating", ("powder coat", "powder coating", "צביעה בתנור")),
    TaxonomyRule("Coating Supplies", "coating material", (
        "stain", "wood filler", "putty", "hardener", "thinner", "מרק", "שפכטל", "מדלל",
    )),
)


ATTRIBUTE_RULES: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "species": (
        ("okoume", ("okume", "okoume", "אוקומה", "אוקמה")),
        ("birch", ("birch", "בירץ", "ליבנה")),
        ("pine", ("pine", "אורן")),
        ("oak", ("oak", "אלון")),
        ("poplar", ("poplar", "צפצפה")),
    ),
    "construction": (
        ("twin", ("twin", "טווין", "combi", "קומבי")),
        ("perforated", ("perforated", "perforation", "מחורר", "מבוקע")),
    ),
    "finish": (
        ("glossy", ("high gloss", "glossy", "gloss", "מבריק")),
        ("matte", ("matte", "matt", "מט")),
        ("rough", ("rough", "textured", "texture", "מחוספס", "טקסטור")),
        ("sanded", ("sanded", "sanding", "שיוף", "משויף")),
        ("polished", ("polished", "polish", "מלוטש")),
        ("mirror", ("mirror", "mirrored", "מראה")),
    ),
    "grade": (
        ("treated", ("treated", "impregnated", "מטופל", "מחוטא")),
        ("kiln-dried", ("kiln dried", "dried", "יבש", "מיובש")),
        ("rough-sawn", ("rough sawn", "unplaned", "לא מוקצע", "מנוסר")),
        ("planed", ("planed", "מוקצע")),
    ),
}


JOB_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("supplier_cut_and_edge_banding", ("cut and edge", "חיתוך וקנטים", "חיתוך + קנטים")),
    ("edge_banding", ("edge band", "edgeband", "קנט", "קנטים")),
    ("cnc_vertical_drilling", ("drilling", "drill", "קידוח")),
    ("cnc_grooving", ("groove", "dado", "חריץ")),
    ("cnc_router_profile_cutting", ("router", "כרסום")),
    ("panel_saw_cutting", ("cutting", "panel saw", "חיתוך", "ניסור")),
    ("carcass_assembly", ("assembly", "הרכבה", "הרכב")),
)


def source_row_text(row: Mapping[str, Any]) -> str:
    # Taxonomy is grounded in source wording. A model-supplied family from a
    # previous pass must not create a false species/category proof.
    return str(row.get("raw_description") or row.get("normalized_name") or "").casefold()


def _has_alias(text: str, aliases: tuple[str, ...]) -> bool:
    return any(alias in text for alias in aliases)


def material_rule_for_text(text: str) -> TaxonomyRule | None:
    return next((rule for rule in MATERIAL_RULES if _has_alias(text, rule.aliases)), None)


def job_operation_for_text(text: str) -> str | None:
    return next((code for code, aliases in JOB_RULES if _has_alias(text, aliases)), None)


def _taxonomy_material_name(rule: TaxonomyRule, attributes: Mapping[str, Any]) -> str:
    """Build a canonical display name from facts proven by the source text."""
    parts = [rule.family.title()]
    if attributes.get("species"):
        parts.append(str(attributes["species"]).title())
    if attributes.get("construction"):
        parts.extend(str(attributes["construction"]).split())
    try:
        thickness = float(attributes.get("thickness_mm") or 0)
    except (TypeError, ValueError):
        thickness = 0
    if thickness:
        parts.append(f"{int(thickness) if thickness.is_integer() else thickness} mm")
    return " ".join(parts)


def apply_material_taxonomy(row: dict[str, Any]) -> bool:
    """Apply only literal bilingual evidence to one material row.

    Unknown terms are intentionally retained in the raw line. They cannot undo
    a category independently proven by the remaining text.
    """
    if row.get("item_kind") != "material":
        return False
    text = source_row_text(row)
    rule = material_rule_for_text(text)
    if not rule:
        return False

    attributes = dict(row.get("identity_attributes") or {})
    # These descriptive fields participate in merge identity. Do not retain a
    # model guess that the source wording does not support.
    for field in ATTRIBUTE_RULES:
        attributes.pop(field, None)
    for field, values in ATTRIBUTE_RULES.items():
        for canonical, aliases in values:
            if _has_alias(text, aliases):
                attributes[field] = canonical
                break
    row["identity_attributes"] = attributes
    row["material_type"] = rule.category
    row["material_family"] = rule.family
    current_name = str(row.get("normalized_name") or "").strip()
    canonical_name = _taxonomy_material_name(rule, attributes)
    # A taxonomy rule is stronger than a model-only name from another material
    # family.  For example, אוקמה proves plywood, so a hallucinated “Glass
    # Aukma” name must never remain visible or block the row from activation.
    has_conflicting_family_word = (
        rule.family != "glass"
        and any(word in current_name.casefold().split() for word in ("glass", "mirror"))
    )
    if (
        not current_name
        or current_name.casefold().startswith("unclassified")
        or has_conflicting_family_word
    ):
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
