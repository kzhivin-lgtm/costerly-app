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
        "movento", "tandem", "telescopic runner",
        "מסילת מגירה", "מסילה למגירה", "מסילה תחתית", "מסילה כפולה",
        "מסילות מגירה", "מסילות", "מובנטו", "טנדם", "טלסקופית",
    )),
    TaxonomyRule("Hardware", "hinge", ("hinge", "hinges", "ציר", "צירים", "צירי")),
    TaxonomyRule("Hardware", "mounting plate", (
        "mounting plate", "mounting bracket", "bracket", "clip", "latch",
        "פלטת חיבור", "תושבת", "קליפ", "סוגר",
    )),
    TaxonomyRule("Hardware", "handle", ("handle", "knob", "pull", "drawer handle", "ידית", "ידיות", "כפתור", "כפתורים")),
    TaxonomyRule("Hardware", "furniture leg", (
        "furniture leg", "cabinet leg", "plinth leg", "adjustable leg", "gas lift",
        "רגלית", "רגל מתכווננת", "בוכנת גז", "בוכנה", "מנגנון קלפה",
    )),
    # Wood sheets. Twin and Okoume prove plywood, but are attributes, not brands.
    TaxonomyRule("Wood Sheets", "plywood", (
        "plywood", "lumber core", "sanded plywood", "לביד", "לבידים", "דיקט", "סנדוויץ", "סנדויץ",
        "okume", "okoume", "אוקומה", "אוקמה", "twin", "טווין", "combi", "קומבי",
    )),
    TaxonomyRule("Wood Sheets", "mdf", (
        "mdf", "m.d.f", "m d f",
        # Hebrew invoices and OCR use both the spoken abbreviation and the
        # compact printed form. Dotted and spaced forms cover OCR separating
        # the letters without turning an unrelated Hebrew word into MDF.
        "מדי אף", "אמ די אף", "מדפ", "מ.ד.פ", "מ ד פ",
    )),
    TaxonomyRule("Wood Sheets", "particleboard", (
        "particleboard", "chipboard", "melamine board", "laminated board",
        "סיבית", "מלמין", "שבבית",
    )),
    TaxonomyRule("Wood Sheets", "hardboard", ("hardboard", "hdf", "מזונית", "הארדבורד")),
    TaxonomyRule("Glass", "glass", ("glass", "mirror", "זכוכית", "מראה")),
    TaxonomyRule("Solid Wood", "solid timber", (
        "solid wood", "timber", "lumber", "plank", "board", "beam", "batten", "slat",
        "עץ מלא", "קורה", "קורות", "קרש", "קרשים", "לוח עץ", "סרגל", "לטה", "לוחות עץ",
    )),
    TaxonomyRule("Wood Supplies", "veneer", ("veneer", "פורניר")),
    TaxonomyRule("Wood Supplies", "edge banding", ("edge band", "edgeband", "קנט", "קנטים")),
    # Metal.
    TaxonomyRule("Metal Profiles", "metal profile", (
        "metal profile", "aluminium profile", "aluminum profile", "tube", "pipe", "angle", "channel",
        "פרופיל", "פרופילי", "אלומיניום", "צינור", "זווית", "זוויתן", "תעלה",
    )),
    TaxonomyRule("Metal Sheets", "metal sheet", (
        "sheet metal", "steel sheet", "aluminium sheet", "aluminum sheet", "plate", "metal plate",
        "פח", "פחים", "פלטת מתכת", "פלטות מתכת", "לוח אלומיניום", "נירוסטה",
    )),
    TaxonomyRule("Metal Supplies", "metal bar", (
        "round bar", "flat bar", "solid bar", "rod", "wire", "מוט", "פס שטוח", "חוט",
    )),
    # Coating.
    TaxonomyRule("Paints & Coatings", "paint", ("paint", "colour paint", "צבע", "צבעים", "צבע יסוד")),
    TaxonomyRule("Paints & Coatings", "lacquer", ("lacquer", "varnish", "לכה", "לכות")),
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
        ("perforated", ("perforated", "perforation", "מחורר", "מבוקע", "בקוע", "מנוקב")),
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

_IDENTITY_ATTRIBUTE_DEFAULTS: dict[str, Any] = {
    "thickness_mm": 0,
    "width_mm": 0,
    "length_mm": 0,
    "diameter_mm": 0,
    "species": "",
    "substrate": "",
    "surface": "",
    "coating": "",
    "colour": "",
    "grade": "",
    "construction": "",
    "finish": "",
}


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


JOB_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("supplier_cut_and_edge_banding", (
        "cut and edge", "cutting and edge", "cut + edge", "cutting + edge",
        "חיתוך וקנט", "חיתוך וקנטים", "חיתוך + קנט", "חיתוך + קנטים",
        "פס חיתוך וקנט", "פס חיתוך + קנט",
    )),
    ("edge_banding", ("edge band", "edgeband", "קנט", "קנטים")),
    ("cnc_vertical_drilling", ("drilling", "drill", "קידוח")),
    ("cnc_grooving", ("groove", "dado", "חריץ")),
    ("cnc_router_profile_cutting", ("router", "כרסום")),
    ("panel_saw_cutting", ("cutting", "panel saw", "חיתוך", "ניסור")),
    ("carcass_assembly", ("assembly", "הרכבה", "הרכב")),
)

# These phrases are unambiguously paid work even when the commercial model
# calls the line a material. They are intentionally narrower than JOB_RULES:
# a bare "edge band" can still be an edge-band roll and must remain a material.
FORCED_OPERATION_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("supplier_cut_and_edge_banding", JOB_RULES[0][1]),
    ("edge_banding", (
        "edge banding service", "edge-banding service", "edge banding application",
        "הדבקת קנט", "הדבקת קנטים", "עבודת קנט", "עבודת קנטים",
    )),
    ("cnc_vertical_drilling", ("drilling service", "drilling work", "עבודת קידוח", "שירות קידוח")),
    ("cnc_grooving", ("grooving service", "grooving work", "עבודת חריץ", "שירות חריץ")),
    ("cnc_router_profile_cutting", ("router service", "routing service", "עבודת כרסום", "שירות כרסום")),
    ("carcass_assembly", ("assembly service", "assembly work", "עבודת הרכבה", "שירות הרכבה")),
)


def source_row_text(row: Mapping[str, Any]) -> str:
    # Taxonomy is grounded in source wording. A model-supplied family from a
    # previous pass must not create a false species/category proof.
    return str(row.get("raw_description") or row.get("normalized_name") or "").casefold()


_HEBREW_FINAL_FORMS = str.maketrans({
    "ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ",
})
_TAXONOMY_NOISE_RE = re.compile(r"[\u0591-\u05c7'\"׳״`.,;:/\\|()[\]{}+=*_\-]+")
_TAXONOMY_CONNECTORS = {"and", "plus", "with", "ו"}


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
            and _edit_distance_at_most_one(token, alias_token)
            for token in text_tokens
        ):
            return False
    return True


def _has_alias(text: str, aliases: tuple[str, ...]) -> bool:
    canonical_text = _canonical_taxonomy_text(text)
    for alias in aliases:
        canonical_alias = _canonical_taxonomy_text(alias)
        if canonical_alias and canonical_alias in canonical_text:
            return True
        if _compound_alias_matches(canonical_text, canonical_alias):
            return True
    return False


def material_rule_for_text(text: str) -> TaxonomyRule | None:
    return next((rule for rule in MATERIAL_RULES if _has_alias(text, rule.aliases)), None)


def job_operation_for_text(text: str) -> str | None:
    return next((code for code, aliases in JOB_RULES if _has_alias(text, aliases)), None)


def forced_operation_for_text(text: str) -> str | None:
    """Return a service code only for wording that cannot denote stock."""
    return next((code for code, aliases in FORCED_OPERATION_RULES if _has_alias(text, aliases)), None)


def apply_operation_taxonomy(row: dict[str, Any]) -> str | None:
    """Repair a material-vs-service model error from literal source wording.

    This deterministic pass has no supplier inputs. It promotes only explicit
    service phrases, preserving bare product phrases such as a PVC edge-band
    roll for the material taxonomy.
    """
    operation_code = forced_operation_for_text(source_row_text(row))
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


def _taxonomy_material_name(rule: TaxonomyRule, attributes: Mapping[str, Any]) -> str:
    """Build a canonical display name from facts proven by the source text."""
    family_name = "MDF" if rule.family == "mdf" else rule.family.title()
    parts = [family_name]
    if attributes.get("species"):
        parts.append(str(attributes["species"]).title())
    if attributes.get("construction"):
        construction = set(str(attributes["construction"]).split())
        # Display order is fixed even though identity storage is order-free.
        # “Twin perforated” reads as one construction, not two arbitrary tags.
        parts.extend(token for token in ("twin", "perforated") if token in construction)
        parts.extend(sorted(construction - {"twin", "perforated"}))
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

    source_attributes = dict(row.get("identity_attributes") or {})
    # Taxonomy is now deliberately applied before schema validation. Preserve
    # the strict identity contract even when a rule clears an unsupported model
    # guess or only proves one field.
    attributes = {
        field: source_attributes.get(field, default)
        for field, default in _IDENTITY_ATTRIBUTE_DEFAULTS.items()
    }
    # These descriptive fields participate in merge identity. Do not retain a
    # model guess that the source wording does not support.
    for field in ATTRIBUTE_RULES:
        attributes.pop(field, None)
    for field, values in ATTRIBUTE_RULES.items():
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
    attributes = {
        field: attributes.get(field, default)
        for field, default in _IDENTITY_ATTRIBUTE_DEFAULTS.items()
    }
    if rule.category == "Wood Sheets":
        # Model-generated dimensions are not source evidence. Rebuild this
        # pair from literal text so a single 3100 span cannot become 3100×3100
        # or acquire an unrelated 2400 side.
        attributes["width_mm"], attributes["length_mm"] = _literal_sheet_dimensions(text)
    row["identity_attributes"] = attributes
    row["material_type"] = rule.category
    row["material_family"] = rule.family
    current_name = str(row.get("normalized_name") or "").strip()
    canonical_name = _taxonomy_material_name(rule, attributes)
    # A literal Wood Sheets rule is the source of truth for its customer-facing
    # identity. This prevents a model label such as “Acrylic Okoume” from
    # surviving despite the source proving a plywood family. The source wording
    # and every omitted decor/finish detail remain in raw_description and the
    # structured attributes, so no evidence is lost.
    # Other categories keep a usable model name unless it is visibly from a
    # conflicting family, avoiding a wider display-name rewrite.
    has_conflicting_family_word = (
        rule.family != "glass"
        and any(word in current_name.casefold().split() for word in ("glass", "mirror"))
    )
    if (
        not current_name
        or current_name.casefold().startswith("unclassified")
        or has_conflicting_family_word
        or rule.category == "Wood Sheets"
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
