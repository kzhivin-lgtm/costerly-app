from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, Mapping, Sequence


IdentityStatus = Literal["resolved", "shortlist", "new_identity_or_needs_review"]

HARD_SPECIFICATION_KEYS = frozenset(
    {
        "thickness_mm",
        "diameter_mm",
        "length_mm",
        "width_mm",
        "height_mm",
        "depth_mm",
        "grade",
        "species",
        "material",
        "chemistry",
        "surface",
        "coating",
        "faces",
        "colour",
        "fastener_type",
        "hinge_type",
    }
)

_UNIT_REPLACEMENTS = (
    (r"\b(?:millimet(?:er|re)s?|мм|מ[\"״']?מ)\b", "mm"),
    (r"\b(?:centimet(?:er|re)s?|см|ס[\"״']?מ)\b", "cm"),
    (r"\b(?:kilograms?|kilogrammes?|кг|ק[\"״']?ג)\b", "kg"),
    (r"\b(?:grams?|grammes?|гр|גרם)\b", "g"),
    (r"\b(?:liters?|litres?|литр(?:а|ов)?|ליטר)\b", "l"),
    (r"\b(?:milliliters?|millilitres?|мл|מ[\"״']?ל)\b", "ml"),
)

_GENERIC_FAMILY_TOKENS = frozenset(
    {
        "board", "material", "materials", "sheet", "sheets", "solid",
        "timber", "wood", "woods", "panel", "panels",
    }
)


@dataclass(frozen=True)
class MaterialIdentityCandidate:
    material_id: str
    score: Decimal
    route: str
    matched_alias: str | None = None


@dataclass(frozen=True)
class MaterialIdentityResolution:
    status: IdentityStatus
    route: str
    normalized_phrase: str
    selected_material_id: str | None = None
    candidates: tuple[MaterialIdentityCandidate, ...] = ()
    reason_codes: tuple[str, ...] = ()
    resolver_version: str = "material_identity_v1"


def normalize_material_phrase(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    text = text.replace("×", "x").replace("✕", "x")
    text = re.sub(r"(?<=\d),(?=\d)", ".", text)
    text = re.sub(r"(?<=\d)(?=[a-zа-яא-ת])", " ", text)
    text = re.sub(r"(?<=[a-zа-яא-ת])(?=\d)", " ", text)
    for pattern, replacement in _UNIT_REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"[^\w.]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def normalize_supplier_sku(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"[^\w]+", "", text, flags=re.UNICODE)


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _specification_equal(requested: Any, stored: Any) -> bool:
    requested_number = _decimal(requested)
    stored_number = _decimal(stored)
    if requested_number is not None and stored_number is not None:
        return requested_number == stored_number
    if isinstance(stored, (list, tuple, set)):
        return any(_specification_equal(requested, item) for item in stored)
    if isinstance(requested, (list, tuple, set)):
        return any(_specification_equal(item, stored) for item in requested)
    return normalize_material_phrase(requested) == normalize_material_phrase(stored)


def _hard_compatibility(
    material: Mapping[str, Any],
    *,
    category_code: str | None,
    specifications: Mapping[str, Any],
) -> tuple[bool, int]:
    if category_code and str(material.get("category_code") or "") != category_code:
        return False, 0
    stored = material.get("specifications") or {}
    matched = 0
    for key, value in specifications.items():
        if key not in HARD_SPECIFICATION_KEYS or value in (None, "", []):
            continue
        # Catalog V1 deliberately leaves some dimensions unrecorded. Absence is
        # uncertainty, not a contradictory material property. Only an explicit
        # incompatible stored value may eliminate a shortlist candidate.
        if key not in stored:
            continue
        if not _specification_equal(value, stored[key]):
            return False, matched
        matched += 1
    return True, matched


def _candidate(
    material_id: str,
    *,
    score: str,
    route: str,
    matched_alias: str | None = None,
) -> MaterialIdentityCandidate:
    return MaterialIdentityCandidate(
        material_id=material_id,
        score=Decimal(score),
        route=route,
        matched_alias=matched_alias,
    )


def _unique_material_ids(rows: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(sorted({str(row.get("material_id") or "") for row in rows if row.get("material_id")}))


def _family_tokens(value: str | None) -> set[str]:
    """Keep only material-identifying words from the extractor's family label."""
    return {
        token
        for token in normalize_material_phrase(value).split()
        if len(token) > 2 and token not in _GENERIC_FAMILY_TOKENS
    }


def _material_family_matches(material: Mapping[str, Any], family_tokens: set[str]) -> bool:
    if not family_tokens:
        return True
    specifications = material.get("specifications") or {}
    corpus = normalize_material_phrase(" ".join(
        str(value or "")
        for value in (
            material.get("canonical_name"),
            specifications.get("subcategory_en"),
            specifications.get("category_en"),
        )
    ))
    tokens = set(corpus.split())
    # Supplier lists commonly call glued solid-wood panels "laminated" while
    # the canonical catalog names that same purchasable family butcher-block.
    # This is a retrieval synonym only, never an automatic identity link.
    if family_tokens in ({"laminated"}, {"lami"}):
        return {"butcher", "block"}.issubset(tokens)
    return family_tokens.issubset(tokens)


def resolve_material_identity(
    *,
    phrase: str,
    alternate_phrases: Sequence[str] = (),
    market_code: str,
    materials: Sequence[Mapping[str, Any]],
    reference_aliases: Sequence[Mapping[str, Any]],
    company_aliases: Sequence[Mapping[str, Any]] = (),
    market_offers: Sequence[Mapping[str, Any]] = (),
    supplier_name: str | None = None,
    supplier_id: str | None = None,
    supplier_sku: str | None = None,
    category_code: str | None = None,
    specifications: Mapping[str, Any] | None = None,
    material_family: str | None = None,
    candidate_departments: Sequence[str] = (),
    shortlist_limit: int = 5,
) -> MaterialIdentityResolution:
    """Resolve identity by exact routes before returning a bounded shortlist."""

    if shortlist_limit < 1 or shortlist_limit > 5:
        raise ValueError("shortlist_limit must be between 1 and 5")
    normalized_phrase = normalize_material_phrase(phrase)
    if not normalized_phrase:
        return MaterialIdentityResolution(
            status="new_identity_or_needs_review",
            route="empty_phrase",
            normalized_phrase="",
            reason_codes=("material_phrase_missing",),
        )
    market = str(market_code or "").strip().upper()
    normalized_phrases = tuple(
        dict.fromkeys(
            value
            for value in (
                normalized_phrase,
                *(normalize_material_phrase(item) for item in alternate_phrases),
            )
            if value
        )
    )
    requested_specs = dict(specifications or {})
    shortlist_departments = {
        str(value).strip() for value in candidate_departments if str(value).strip()
    }
    material_by_id = {
        str(row.get("material_id")): row
        for row in materials
        if row.get("material_id") and row.get("active", True)
    }

    def compatible(material_id: str) -> bool:
        material = material_by_id.get(material_id)
        return bool(
            material
            and _hard_compatibility(
                material,
                category_code=category_code,
                specifications=requested_specs,
            )[0]
        )

    def exact_compatible(material_id: str) -> bool:
        """Reject an exact identity only on an explicit conflicting attribute."""
        material = material_by_id.get(material_id)
        if not material:
            return False
        stored = material.get("specifications") or {}
        for key, value in requested_specs.items():
            if (
                key in HARD_SPECIFICATION_KEYS
                and key in stored
                and value not in (None, "", [])
                and not _specification_equal(value, stored[key])
            ):
                return False
        return True

    normalized_sku = normalize_supplier_sku(supplier_sku)
    normalized_supplier = normalize_material_phrase(supplier_name)
    if normalized_sku and normalized_supplier:
        sku_rows = [
            row
            for row in market_offers
            if str(row.get("market_code") or "") == market
            and normalize_supplier_sku(row.get("supplier_sku")) == normalized_sku
            and normalize_material_phrase(row.get("supplier_name")) == normalized_supplier
            and exact_compatible(str(row.get("material_id") or ""))
        ]
        sku_ids = _unique_material_ids(sku_rows)
        if len(sku_ids) == 1:
            return MaterialIdentityResolution(
                status="resolved",
                route="exact_supplier_sku",
                normalized_phrase=normalized_phrase,
                selected_material_id=sku_ids[0],
                candidates=(_candidate(sku_ids[0], score="100", route="exact_supplier_sku"),),
            )

    company_rows = [
        row
        for row in company_aliases
        if row.get("active", True)
        and normalize_material_phrase(row.get("alias_text")) in normalized_phrases
        and (not row.get("supplier_id") or str(row.get("supplier_id")) == str(supplier_id or ""))
        and exact_compatible(str(row.get("material_id") or ""))
    ]
    company_ids = _unique_material_ids(company_rows)
    if len(company_ids) == 1:
        return MaterialIdentityResolution(
            status="resolved",
            route="exact_company_alias",
            normalized_phrase=normalized_phrase,
            selected_material_id=company_ids[0],
            candidates=(
                _candidate(
                    company_ids[0],
                    score="100",
                    route="exact_company_alias",
                    matched_alias=phrase,
                ),
            ),
        )

    alias_rows = [
        row
        for row in reference_aliases
        if row.get("active", True)
        and str(row.get("market_code") or "") == market
        and normalize_material_phrase(row.get("alias_text")) in normalized_phrases
        and row.get("exact_identity") is True
        and exact_compatible(str(row.get("material_id") or ""))
    ]
    alias_ids = _unique_material_ids(alias_rows)
    if len(alias_ids) == 1:
        return MaterialIdentityResolution(
            status="resolved",
            route="exact_market_alias",
            normalized_phrase=normalized_phrase,
            selected_material_id=alias_ids[0],
            candidates=(
                _candidate(
                    alias_ids[0],
                    score="100",
                    route="exact_market_alias",
                    matched_alias=phrase,
                ),
            ),
        )

    compatible_materials: list[tuple[Mapping[str, Any], int]] = []
    for material in material_by_id.values():
        if (
            shortlist_departments
            and str(material.get("department") or "") not in shortlist_departments
        ):
            continue
        is_compatible, matched_specs = _hard_compatibility(
            material,
            category_code=category_code,
            specifications=requested_specs,
        )
        if is_compatible:
            compatible_materials.append((material, matched_specs))
    family_tokens = _family_tokens(material_family)
    family_known_in_catalog = any(
        _material_family_matches(material, family_tokens)
        and (
            not shortlist_departments
            or str(material.get("department") or "") in shortlist_departments
        )
        for material in material_by_id.values()
    )
    family_materials = [
        item
        for item in compatible_materials
        if _material_family_matches(item[0], family_tokens)
    ]
    # An unfamiliar extractor label must not make all candidates disappear.
    # But if the family is known, a missing compatible variant is a real gap in
    # the catalog, never a reason to suggest another material family.
    if family_materials or family_known_in_catalog:
        compatible_materials = family_materials
    if category_code and requested_specs:
        hard_matches = [
            material
            for material, matched_specs in compatible_materials
            if matched_specs > 0
        ]
        if len(hard_matches) == 1:
            material_id = str(hard_matches[0]["material_id"])
            return MaterialIdentityResolution(
                status="resolved",
                route="compatible_hard_attributes",
                normalized_phrase=normalized_phrase,
                selected_material_id=material_id,
                candidates=(
                    _candidate(
                        material_id,
                        score="95",
                        route="compatible_hard_attributes",
                    ),
                ),
            )

    phrase_token_sets = [set(value.split()) for value in normalized_phrases]
    aliases_by_material: dict[str, list[str]] = {}
    for row in reference_aliases:
        if row.get("active", True) and str(row.get("market_code") or "") == market:
            aliases_by_material.setdefault(str(row.get("material_id") or ""), []).append(
                str(row.get("alias_text") or "")
            )
    ranked: list[MaterialIdentityCandidate] = []
    for material, matched_specs in compatible_materials:
        material_id = str(material["material_id"])
        names = [str(material.get("canonical_name") or ""), *aliases_by_material.get(material_id, ())]
        best_alias = None
        best_overlap = Decimal("0")
        for name in names:
            tokens = set(normalize_material_phrase(name).split())
            if not tokens:
                continue
            overlap = max(
                Decimal(len(phrase_tokens & tokens))
                / Decimal(len(phrase_tokens | tokens))
                for phrase_tokens in phrase_token_sets
            )
            if overlap > best_overlap:
                best_overlap = overlap
                best_alias = name
        score = best_overlap * Decimal("70") + Decimal(matched_specs * 10)
        if category_code:
            score += Decimal("10")
        if score <= 0:
            continue
        ranked.append(
            MaterialIdentityCandidate(
                material_id=material_id,
                score=min(score, Decimal("94")),
                route="compatible_shortlist",
                matched_alias=best_alias,
            )
        )
    ranked.sort(key=lambda row: (-row.score, row.material_id))
    shortlist = tuple(ranked[:shortlist_limit])
    if shortlist:
        return MaterialIdentityResolution(
            status="shortlist",
            route="compatible_shortlist",
            normalized_phrase=normalized_phrase,
            candidates=shortlist,
            reason_codes=("identity_confirmation_required",),
        )
    return MaterialIdentityResolution(
        status="new_identity_or_needs_review",
        route="no_compatible_identity",
        normalized_phrase=normalized_phrase,
        reason_codes=("no_compatible_reference_material",),
    )
