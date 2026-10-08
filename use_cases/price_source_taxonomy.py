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
    TaxonomyRule("Hardware", "furniture connector", (
        "connector", "cabinet connector", "cam lock", "confirmat", "dowel",
        "bolt", "furniture screw", "מחבר", "מחברי רהיט", "אקסצנטרי",
        "דיבל", "בורג רהיטים",
    )),
    TaxonomyRule("Hardware", "lift mechanism", (
        "lift mechanism", "flap lift", "stay lift", "gas strut", "gas spring",
        "מנגנון קלפה", "מנגנון הרמה", "בוכנת גז", "קפיץ גז",
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
    TaxonomyRule("Wood Sheets", "osb", ("osb", "oriented strand board", "או אס בי", "לוח שבבי עץ")),
    TaxonomyRule("Wood Sheets", "laminated panel", (
        "laminated panel", "laminated mdf", "laminated plywood", "פורמייקה",
        "לוח מצופה", "לוח למינציה",
    )),
    TaxonomyRule("Glass", "glass", ("glass", "mirror", "זכוכית", "מראה")),
    TaxonomyRule("Solid Wood", "solid timber", (
        "solid wood", "timber", "lumber", "plank", "board", "beam", "batten", "slat",
        "עץ מלא", "קורה", "קורות", "קרש", "קרשים", "לוח עץ", "סרגל", "לטה", "לוחות עץ",
    )),
    TaxonomyRule("Wood Supplies", "veneer", ("veneer", "פורניר")),
    TaxonomyRule("Wood Supplies", "edge banding", ("edge band", "edge banding", "edgeband", "קנט", "קנטים")),
    # Metal.
    TaxonomyRule("Metal Profiles", "metal profile", (
        "metal profile", "aluminium profile", "aluminum profile", "profile", "tube", "pipe", "angle", "channel",
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
        "stain", "wood filler", "putty", "hardener", "thinner", "sealer", "catalyst",
        "מרק", "שפכטל", "מדלל", "מקשה", "סילר", "זרז",
    )),
)


# The initial curated catalogue contains brands encountered in the product
# domain and brands whose official product ranges prove their department. It is
# intentionally a dictionary, not a fuzzy proper-name detector. Unknown proper
# names remain raw source evidence until they are reviewed and added here.
BRAND_RULES: tuple[BrandRule, ...] = (
    BrandRule("Blum", ("Hardware",), ("blum", "בלום")),
    BrandRule("Hettich", ("Hardware",), ("hettich", "הטיך", "הטיש")),
    BrandRule("Häfele", ("Hardware",), ("hafele", "häfele", "הפלה")),
    BrandRule("Grass", ("Hardware",), ("grass", "גראס")),
    BrandRule("FGV", ("Hardware",), ("fgv",)),
    BrandRule("Salice", ("Hardware",), ("salice", "סליצה")),
    BrandRule("EGGER", ("Wood Sheets",), ("egger", "אגר")),
    BrandRule("Kronospan", ("Wood Sheets",), ("kronospan", "קרונוספן")),
    BrandRule("Finsa", ("Wood Sheets",), ("finsa", "פינסה")),
    BrandRule("SWISS KRONO", ("Wood Sheets",), ("swiss krono", "swisskrono", "סוויס קרונו")),
    BrandRule("Outokumpu", ("Metal Sheets", "Metal Profiles"), ("outokumpu", "אאוטוקומפו")),
    BrandRule("Guardian", ("Glass",), ("guardian", "גרדיאן")),
    BrandRule("Sayerlack", ("Paints & Coatings", "Coating Supplies"), ("sayerlack", "סיירלאק")),
    BrandRule("Milesi", ("Paints & Coatings", "Coating Supplies"), ("milesi", "מילזי", "מילסי")),
    BrandRule("Renner", ("Paints & Coatings", "Coating Supplies"), ("renner", "רנר")),
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
        ("stainless", ("stainless", "נירוסטה", "נירוסט")),
        ("galvanized", ("galvanized", "zinc coated", "מגולוון", "מגלוון")),
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
    "primary_attribute": "",
    "brand": "",
    "brand_basis": "unknown",
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
    ("edge_banding", ("edge band", "edge banding", "edgeband", "קנט", "קנטים")),
    ("cnc_vertical_drilling", ("drilling", "drill", "קידוח")),
    ("cnc_grooving", ("groove", "dado", "חריץ")),
    ("cnc_router_profile_cutting", ("router", "כרסום")),
    ("panel_saw_cutting", ("cutting", "panel saw", "חיתוך", "ניסור")),
    ("carcass_assembly", ("assembly", "הרכבה", "הרכבת", "הרכב")),
    ("metal_profile_cutting", ("metal profile cutting", "tube cutting", "profile cutting", "חיתוך פרופיל", "חיתוך צינור")),
    ("sheet_laser_cutting", ("laser cutting", "laser cut", "חיתוך לייזר")),
    ("sheet_shearing", ("sheet shearing", "guillotine cutting", "חיתוך גיליוטינה")),
    ("metal_drilling", ("metal drilling", "קידוח מתכת")),
    ("metal_milling", ("metal milling", "כרסום מתכת")),
    ("metal_punching", ("metal punching", "ניקוב מתכת")),
    ("sheet_metal_bending", ("sheet bending", "press brake", "כיפוף פח")),
    ("metal_profile_bending", ("profile bending", "tube bending", "כיפוף פרופיל", "כיפוף צינור")),
    ("mig_mag_welding", ("mig welding", "mag welding", "mig mag", "רתכת mig", "ריתוך mig")),
    ("tig_welding", ("tig welding", "רתכת tig", "ריתוך tig")),
    ("metal_grinding", ("metal grinding", "grinding weld", "השחזת מתכת", "ליטוש ריתוך")),
    ("metal_polishing", ("metal polishing", "polishing metal", "ליטוש מתכת")),
    ("metal_assembly", ("metal assembly", "הרכבת מתכת")),
    ("glass_cutting", ("glass cutting", "mirror cutting", "חיתוך זכוכית", "חיתוך מראה")),
    ("glass_edge_processing", ("glass polishing", "glass edge", "ליטוש זכוכית", "עיבוד קצה זכוכית")),
    ("glass_drilling", ("glass drilling", "קידוח זכוכית")),
    ("glass_tempering", ("glass tempering", "חיסום זכוכית")),
    ("finish_surface_preparation", ("surface preparation", "finish preparation", "הכנה לצבע", "הכנת שטח")),
    ("wood_staining", ("wood staining", "staining service", "ביצוע בייץ", "צביעת בייץ")),
    ("wood_priming", ("wood priming", "priming service", "צביעת יסוד")),
    ("wood_lacquering", ("wood lacquering", "lacquering service", "צביעת לכה")),
    ("wet_spray_painting", ("spray painting", "wet painting", "צביעה רטובה", "צביעה בהתזה")),
    ("powder_coating_application", ("powder coating service", "powder painting", "צביעה באבקה", "צביעה בתנור")),
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
    ("metal_profile_cutting", ("metal profile cutting service", "tube cutting service", "עבודת חיתוך פרופיל", "שירות חיתוך צינור")),
    ("sheet_laser_cutting", ("laser cutting service", "laser cutting work", "עבודת חיתוך לייזר", "שירות חיתוך לייזר")),
    ("sheet_shearing", ("sheet shearing service", "guillotine cutting service", "עבודת חיתוך גיליוטינה")),
    ("metal_drilling", ("metal drilling service", "עבודת קידוח מתכת", "שירות קידוח מתכת")),
    ("metal_milling", ("metal milling service", "עבודת כרסום מתכת", "שירות כרסום מתכת")),
    ("metal_punching", ("metal punching service", "עבודת ניקוב מתכת", "שירות ניקוב מתכת")),
    ("sheet_metal_bending", ("sheet bending service", "press brake service", "עבודת כיפוף פח", "שירות כיפוף פח")),
    ("metal_profile_bending", ("profile bending service", "tube bending service", "עבודת כיפוף פרופיל", "שירות כיפוף צינור")),
    ("mig_mag_welding", ("mig welding service", "mag welding service", "עבודת ריתוך mig", "שירות ריתוך mig")),
    ("tig_welding", ("tig welding service", "עבודת ריתוך tig", "שירות ריתוך tig")),
    ("metal_grinding", ("metal grinding service", "עבודת השחזת מתכת", "שירות ליטוש ריתוך")),
    ("metal_polishing", ("metal polishing service", "עבודת ליטוש מתכת", "שירות ליטוש מתכת")),
    ("metal_assembly", ("metal assembly service", "עבודת הרכבת מתכת", "שירות הרכבת מתכת")),
    ("glass_cutting", ("glass cutting service", "mirror cutting service", "עבודת חיתוך זכוכית", "שירות חיתוך זכוכית")),
    ("glass_edge_processing", ("glass edge processing service", "עבודת ליטוש זכוכית", "שירות עיבוד זכוכית")),
    ("glass_drilling", ("glass drilling service", "עבודת קידוח זכוכית", "שירות קידוח זכוכית")),
    ("glass_tempering", ("glass tempering service", "עבודת חיסום זכוכית", "שירות חיסום זכוכית")),
    ("finish_surface_preparation", ("surface preparation service", "עבודת הכנה לצבע", "שירות הכנת שטח")),
    ("wood_staining", ("wood staining service", "עבודת בייץ", "שירות צביעת בייץ")),
    ("wood_priming", ("wood priming service", "עבודת צביעת יסוד", "שירות צביעת יסוד")),
    ("wood_lacquering", ("wood lacquering service", "עבודת צביעת לכה", "שירות צביעת לכה")),
    ("wet_spray_painting", ("spray painting service", "wet painting service", "עבודת צביעה רטובה", "שירות צביעה בהתזה")),
    ("powder_coating_application", ("powder coating service", "powder painting service", "עבודת צביעה באבקה", "שירות צביעה בתנור")),
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


def material_rule_for_text(text: str) -> TaxonomyRule | None:
    return next((rule for rule in MATERIAL_RULES if _has_alias(text, rule.aliases)), None)


def brand_for_text(text: str, *, category: str) -> str:
    """Return a curated brand only after the material category is proven."""
    return next(
        (
            rule.brand for rule in BRAND_RULES
            if category in rule.categories and _has_alias(text, rule.aliases)
        ),
        "",
    )


_BRAND_CANDIDATE_NOISE = frozenset({
    "aluminium", "aluminum", "assembly", "black", "blue", "box", "closure",
    "door", "drawer", "front", "glass", "grey", "high", "hinge", "internal",
    "large", "left", "mdf", "metal", "okoume", "particleboard", "plywood",
    "profile", "pure", "right", "sheet", "small", "stainless", "transparent",
    "twin", "white", "wood",
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


def job_operation_for_text(text: str) -> str | None:
    matches = [
        (len(_canonical_taxonomy_text(alias)), code)
        for code, aliases in JOB_RULES
        for alias in aliases
        if _has_alias(text, (alias,))
    ]
    return max(matches, default=(0, ""))[1] or None


def forced_operation_for_text(text: str) -> str | None:
    """Return a service code only for wording that cannot denote stock."""
    matches = [
        (len(_canonical_taxonomy_text(alias)), code)
        for code, aliases in FORCED_OPERATION_RULES
        for alias in aliases
        if _has_alias(text, (alias,))
    ]
    return max(matches, default=(0, ""))[1] or None


def _explicit_thickness_mm(text: str) -> float:
    match = re.search(
        r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*(?:mm|מ[\"״']?מ)(?!\w)",
        str(text or ""),
        flags=re.IGNORECASE,
    )
    return float(match.group(1)) if match else 0


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
    """Build a compact canonical display from structured, proven facts only."""
    family_name = "MDF" if rule.family == "mdf" else rule.family.title()
    parts = [family_name]
    if attributes.get("primary_attribute"):
        parts.append(str(attributes["primary_attribute"]))
    if attributes.get("brand"):
        parts.append(str(attributes["brand"]))
    secondary: list[str] = []
    for field in (
        "grade", "species", "construction", "finish", "surface",
        "coating", "colour",
    ):
        value = str(attributes.get(field) or "").strip()
        if not value or _canonical_taxonomy_text(value) == _canonical_taxonomy_text(rule.family):
            continue
        if field == "species":
            value = value.title()
        if value not in secondary:
            secondary.append(value)
        if len(secondary) == 4:
            break
    return " ".join(parts) + (f", {', '.join(secondary)}" if secondary else "")


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
    catalog_brand = brand_for_text(text, category=rule.category)
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
    literal_thickness = _explicit_thickness_mm(text)
    if literal_thickness:
        attributes["thickness_mm"] = literal_thickness
    if rule.category == "Wood Sheets":
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
    if technical_grade := _explicit_technical_grade(text):
        attributes["grade"] = technical_grade
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
    # surviving despite the source proving a plywood family. Other categories
    # retain an already-readable model name until the formatter has source
    # evidence for every relevant entity family.
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
