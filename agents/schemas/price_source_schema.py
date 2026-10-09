from __future__ import annotations

import re
from typing import Any


DOCUMENT_TYPES = {
    "price_list",
    "catalog",
    "quote",
    "invoice",
    "tax_invoice",
    "delivery_note",
    "order_confirmation",
    "credit_note",
    "internal_estimate",
    "customer_quote",
    "other",
}
SOURCE_ORIGINS = {"supplier", "company_internal", "unknown"}
PRICE_CONTEXTS = {
    "public_list",
    "supplier_quote",
    "customer_transaction",
    "internal_cost_estimate",
    "customer_sale",
    "unknown",
}
VAT_MODES = {"included", "excluded", "mixed", "unknown"}
ROW_STATUSES = {"ready", "unresolved", "excluded"}
ITEM_KINDS = {"material", "operation_service", "non_material"}
IDENTITY_ATTRIBUTE_FIELDS = (
    "thickness_mm",
    "width_mm",
    "length_mm",
    "depth_mm",
    "diameter_mm",
    "primary_attribute",
    "brand",
    "brand_basis",
    "species",
    "substrate",
    "surface",
    "coating",
    "colour",
    "grade",
    "construction",
    "finish",
)
PRICE_SOURCE_CATEGORIES = (
    "Wood Sheets",
    "Solid Wood",
    "Wood Supplies",
    "Hardware",
    "Glass",
    "Plastics & Composites",
    "Metal Sheets",
    "Metal Profiles",
    "Metal Supplies",
    "Paints & Coatings",
    "Coating Supplies",
    "Other",
)
CANONICAL_UNIT_CODES = {
    "piece", "pair", "set", "dozen",
    "mm", "cm", "m", "linear_m",
    "cm2", "m2",
    "ml", "liter", "m3",
    "g", "kg", "ton",
    "sheet", "panel", "board", "roll", "pack", "box", "carton", "bag",
    "bucket", "can", "tube", "pallet",
    "other", "unknown",
}

# These are product families, not generic words for a material or finish. A
# hinge remains furniture hardware even when it is made from metal.
_HARDWARE_MARKERS = (
    "hinge", "drawer slide", "drawer runner", "drawer rail", "runner",
    "bracket", "mounting plate", "mounting bracket", "clip", "latch",
    "handle", "knob", "furniture leg", "plinth leg", "hardware",
    "ציר", "מסילה", "מגירה", "תושבת", "פלטת חיבור", "קליפ", "פרפר",
    "רגלית", "ידית", "לחצן",
)
_DRAWER_RUNNER_MARKERS = (
    "drawer slide", "drawer runner", "drawer rail", "undermount runner",
    "side-mount runner", "מסילת מגירה", "מסילה תחתית", "מסילה כפולה",
)


def _price_source_row_text(row: dict[str, Any]) -> str:
    return " ".join(
        str(row.get(key) or "")
        for key in ("raw_description", "normalized_name", "material_family")
    ).casefold()


def apply_price_source_hardware_defaults(result: dict[str, Any]) -> dict[str, Any]:
    """Classify furniture fittings and apply the agreed count-unit fallback."""
    for row in result.get("rows") or []:
        if not isinstance(row, dict) or row.get("item_kind") != "material":
            continue
        text = _price_source_row_text(row)
        if not (
            row.get("material_type") == "Hardware"
            or any(marker in text for marker in _HARDWARE_MARKERS)
        ):
            continue
        row["material_type"] = "Hardware"
        is_drawer_runner = any(marker in text for marker in _DRAWER_RUNNER_MARKERS)
        default_unit = "set" if is_drawer_runner else "piece"
        changed = False
        for key in ("purchase_unit", "calculation_unit"):
            # Drawer runners are sold and estimated as a left/right set. A
            # printed count-unit describes quantity, not a single rail.
            if is_drawer_runner or row.get(key) in {"", "unknown", "other", None}:
                row[key] = default_unit
                changed = True
        if str(row.get("raw_unit") or "").strip().casefold() in {"", "unknown", "other"}:
            row["raw_unit"] = default_unit
            changed = True
        if changed:
            row["conversion_factor"] = 1
            raw_price = row.get("raw_price")
            if isinstance(raw_price, (int, float)) and raw_price > 0:
                row["normalized_price"] = raw_price
            reasons = set(row.get("reason_codes") or [])
            reasons.difference_update({"missing_unit", "package_conversion_unresolved"})
            reasons.add(f"hardware_unit_default_{default_unit}")
            row["reason_codes"] = sorted(reasons)
    return result


def apply_price_source_material_unit_defaults(result: dict[str, Any]) -> dict[str, Any]:
    """Fill an omitted unit for a purchasable, discrete material line.

    Invoice tables normally state quantity, unit price and line total once per
    row, not "one piece" repeatedly. An omitted unit therefore defaults to the
    item's natural purchase unit: ``sheet`` for sheet material and ``piece``
    for another discrete item. A stated package, metre, area, mass or container
    unit is preserved and never replaced by this rule.
    """
    unknown_units = {"", "unknown", "other", "unknown unit", "לא ברור"}
    resolved_by_default = {
        "missing_unit", "package_conversion_unresolved",
        "missing_dimensions", "unclear_dimensions",
    }
    for row in result.get("rows") or []:
        if not isinstance(row, dict) or row.get("item_kind") != "material":
            continue
        category = str(row.get("material_type") or "")
        default_unit = "sheet" if category in {
            "Wood Sheets", "Metal Sheets", "Glass", "Plastics & Composites",
        } else "piece"
        changed = False
        if str(row.get("raw_unit") or "").strip().casefold() in unknown_units:
            row["raw_unit"] = default_unit
            changed = True
        for key in ("purchase_unit", "calculation_unit"):
            if str(row.get(key) or "").strip().casefold() in unknown_units:
                row[key] = default_unit
                changed = True
        if not changed:
            continue
        row["conversion_factor"] = 1
        raw_price = row.get("raw_price")
        if isinstance(raw_price, (int, float)) and raw_price > 0:
            row["normalized_price"] = raw_price
        previous_reasons = set(row.get("reason_codes") or [])
        audit_reasons = {
            reason for reason in previous_reasons
            if reason.startswith(("taxonomy_", "hardware_unit_default_"))
        }
        remaining_reasons = previous_reasons - resolved_by_default - audit_reasons
        reasons = remaining_reasons | {f"unit_default_{default_unit}"}
        row["reason_codes"] = sorted(reasons)
        # A default can cure an otherwise valid line. It cannot bypass an
        # arithmetic, VAT, package or material-identity blocker.
        if row.get("status") == "unresolved" and not remaining_reasons:
            row["status"] = "ready"
    return result


def normalize_price_source_units(result: dict[str, Any]) -> dict[str, Any]:
    """Replace recognised source-language count units with canonical codes.

    ``יח`` is the standard Hebrew abbreviation for one item.  It is useful in
    raw OCR evidence, but it must not leak into the price UI or prevent the
    later sheet-material normaliser from recognising a full sheet.
    """
    aliases = {
        "יח": "piece",
        "יח׳": "piece",
        "יח'": "piece",
        "יחידה": "piece",
        "יחידות": "piece",
        "each": "piece",
    }
    for row in result.get("rows") or []:
        if not isinstance(row, dict):
            continue
        raw_unit = str(row.get("raw_unit") or "").strip().casefold()
        if raw_unit in aliases:
            row["raw_unit"] = aliases[raw_unit]
    return result

PRICE_SOURCE_RESULT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "supplier_name",
        "supplier_hp",
        "source_origin",
        "document_type",
        "document_number",
        "document_date",
        "price_context",
        "currency",
        "vat_mode",
        "document_subtotal",
        "document_vat_amount",
        "document_total",
        "rows",
    ],
    "properties": {
        "supplier_name": {"type": "string"},
        "supplier_hp": {"type": "string"},
        "source_origin": {"type": "string", "enum": sorted(SOURCE_ORIGINS)},
        "document_type": {"type": "string", "enum": sorted(DOCUMENT_TYPES)},
        "document_number": {"type": "string"},
        "document_date": {"type": "string"},
        "price_context": {"type": "string", "enum": sorted(PRICE_CONTEXTS)},
        "currency": {"type": "string"},
        "vat_mode": {"type": "string", "enum": sorted(VAT_MODES)},
        "document_subtotal": {"type": "number"},
        "document_vat_amount": {"type": "number"},
        "document_total": {"type": "number"},
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "source_row_number",
                    "item_kind",
                    "material_type",
                    "material_family",
                    "identity_attributes",
                    "raw_description",
                    "raw_sku",
                    "raw_price",
                    "raw_currency",
                    "raw_unit",
                    "raw_package_quantity",
                    "raw_quantity",
                    "raw_line_total",
                    "raw_discount_percent",
                    "raw_discount_amount",
                    "raw_vat_mode",
                    "normalized_name",
                    "purchase_unit",
                    "calculation_unit",
                    "conversion_factor",
                    "normalized_price",
                    "conversion_basis",
                    "status",
                    "confidence",
                    "reason_codes",
                    "evidence_reference",
                ],
                "properties": {
                    "source_row_number": {"type": "integer"},
                    "item_kind": {"type": "string", "enum": sorted(ITEM_KINDS)},
                    "material_type": {"type": "string", "enum": list(PRICE_SOURCE_CATEGORIES)},
                    "material_family": {"type": "string"},
                    "identity_attributes": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": list(IDENTITY_ATTRIBUTE_FIELDS),
                        "properties": {
                            "thickness_mm": {"type": "number", "minimum": 0},
                            "width_mm": {"type": "number", "minimum": 0},
                            "length_mm": {"type": "number", "minimum": 0},
                            "depth_mm": {"type": "number", "minimum": 0},
                            "diameter_mm": {"type": "number", "minimum": 0},
                            "primary_attribute": {"type": "string"},
                            "brand": {"type": "string"},
                            "brand_basis": {"type": "string"},
                            "species": {"type": "string"},
                            "substrate": {"type": "string"},
                            "surface": {"type": "string"},
                            "coating": {"type": "string"},
                            "colour": {"type": "string"},
                            "grade": {"type": "string"},
                            "construction": {"type": "string"},
                            "finish": {"type": "string"},
                        },
                    },
                    "raw_description": {"type": "string"},
                    "raw_sku": {"type": "string"},
                    "raw_price": {"type": "number"},
                    "raw_currency": {"type": "string"},
                    "raw_unit": {"type": "string"},
                    "raw_package_quantity": {"type": "number"},
                    "raw_quantity": {"type": "number"},
                    "raw_line_total": {"type": "number"},
                    "raw_discount_percent": {"type": "number", "minimum": 0},
                    "raw_discount_amount": {"type": "number", "minimum": 0},
                    "raw_vat_mode": {"type": "string", "enum": sorted(VAT_MODES)},
                    "normalized_name": {"type": "string"},
                    "purchase_unit": {"type": "string", "enum": sorted(CANONICAL_UNIT_CODES)},
                    "calculation_unit": {"type": "string", "enum": sorted(CANONICAL_UNIT_CODES)},
                    "conversion_factor": {"type": "number", "minimum": 0},
                    "normalized_price": {"type": "number"},
                    "conversion_basis": {"type": "string"},
                    "status": {"type": "string", "enum": sorted(ROW_STATUSES)},
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Confidence percentage from 0 to 100, never a 0-to-1 fraction",
                    },
                    "reason_codes": {"type": "array", "items": {"type": "string"}},
                    "evidence_reference": {"type": "string"},
                },
            },
        },
    },
}


class PriceSourceSchemaError(ValueError):
    pass


def normalize_price_source_optional_numbers(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize non-commercial numeric notation before strict row validation."""
    for row in result.get("rows") or []:
        if not isinstance(row, dict):
            continue
        for key in ("raw_discount_percent", "raw_discount_amount"):
            value = row.get(key)
            if value is None or (isinstance(value, str) and value.strip().casefold() in {"", "-", "—", "n/a", "na"}):
                row[key] = 0
            elif isinstance(value, str):
                text = value.strip().replace(",", "").replace("−", "-").replace("–", "-")
                if key == "raw_discount_percent":
                    text = text.removesuffix("%").strip()
                try:
                    # Invoices frequently print a discount as a negative
                    # deduction.  The schema stores the discount magnitude,
                    # so -10% is 10 rather than an invalid negative field.
                    row[key] = abs(float(text))
                except ValueError:
                    # A discount cell has no independent commercial meaning
                    # when it cannot be read as a number.  Keep the source row
                    # usable and treat it as no stated discount.
                    row[key] = 0
            elif isinstance(value, (int, float)):
                row[key] = abs(value)
            else:
                row[key] = 0
        # Invoice footer adjustments such as 0.02% / 0.38 ILS are rounding,
        # not a commercial discount on every material.  They must neither
        # change a line price nor appear as discount evidence.  Only a clear,
        # material-level discount of at least three percent is retained.
        try:
            discount_percent = float(row.get("raw_discount_percent") or 0)
        except (TypeError, ValueError):
            discount_percent = 0
        if discount_percent < 3:
            row["raw_discount_percent"] = 0
            row["raw_discount_amount"] = 0
        # A supplier credit or returned-goods line is source evidence but never
        # a purchasable catalog price. Preserve its signed total, make the
        # observed quantity valid for the schema, and exclude only that row.
        # One negative return must not reject the complete invoice.
        raw_quantity = row.get("raw_quantity")
        raw_line_total = row.get("raw_line_total")
        if (
            isinstance(raw_quantity, (int, float))
            and raw_quantity < 0
        ) or (
            isinstance(raw_line_total, (int, float))
            and raw_line_total < 0
        ):
            if isinstance(raw_quantity, (int, float)):
                row["raw_quantity"] = abs(raw_quantity)
            row["status"] = "excluded"
            row["reason_codes"] = sorted(
                set((row.get("reason_codes") or []) + ["return_or_credit_line"])
            )
    return result


def normalize_price_source_row_identity_fields(result: dict[str, Any]) -> dict[str, Any]:
    """Keep a supplier item code out of the internal row-position field.

    The model occasionally mistakes visible invoice product codes such as 27,
    41 or 4 for ``source_row_number``.  That silently discards SKU evidence
    and makes the same supplier item look new on a later invoice.  Row numbers
    are internal, sequential positions in the extracted set, while the visible
    code belongs in ``raw_sku``.  Preserve an explicit SKU and only recover an
    unambiguous non-sequential numeric value.
    """
    rows = result.get("rows") or []
    if not isinstance(rows, list):
        return result
    for position, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        source_number = row.get("source_row_number")
        raw_sku = str(row.get("raw_sku") or "").strip()
        if (
            not raw_sku
            and isinstance(source_number, int)
            and source_number > 0
            and source_number != position
        ):
            row["raw_sku"] = str(source_number)
        row["source_row_number"] = position
        # Schema evolution must not turn an otherwise usable extraction into a
        # failed cycle. The taxonomy may fill these literal facts later; an
        # empty value explicitly means that the source did not prove one.
        attributes = row.get("identity_attributes")
        if isinstance(attributes, dict):
            attributes.setdefault("primary_attribute", "")
            attributes.setdefault("brand", "")
            attributes.setdefault("brand_basis", "unknown")
    return result


def normalize_price_source_confidence_scale(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize a consistently fractional model response to percentage points."""
    rows = result.get("rows") or []
    values = [
        row.get("confidence")
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("confidence"), (int, float))
    ]
    positive = [float(value) for value in values if float(value) > 0]
    if not positive:
        return result
    has_fractional_scale = any(value < 1 for value in positive)
    has_percentage_scale = any(value > 1 for value in positive)
    if has_fractional_scale and has_percentage_scale:
        raise PriceSourceSchemaError("row confidence uses mixed scales")
    if not has_percentage_scale:
        for row in rows:
            confidence = row.get("confidence") if isinstance(row, dict) else None
            if isinstance(confidence, (int, float)):
                row["confidence"] = float(confidence) * 100
    return result


def apply_price_source_document_defaults(
    result: dict[str, Any], *, source_kind: str,
) -> dict[str, Any]:
    """Apply the approved Israeli currency and VAT defaults to missing evidence."""
    currency = str(result.get("currency") or "").strip().upper() or "ILS"
    result["currency"] = currency
    # HP is an Israeli company identifier, exactly nine digits and never has a
    # leading zero.  Israeli phone numbers commonly do, so a leading zero is
    # a hard exclusion rather than a weak supplier-match candidate.
    # only when the model can tie it to the seller, so malformed or annotated
    # text becomes unknown rather than a false supplier-match key.
    hp_raw = str(result.get("supplier_hp") or "").strip()
    hp_digits = re.sub(r"\D", "", hp_raw)
    result["supplier_hp"] = (
        hp_digits
        if (
            len(hp_digits) == 9
            and not hp_digits.startswith("0")
            and re.fullmatch(r"[\s\d().-]+", hp_raw)
        )
        else ""
    )
    rows = [row for row in result.get("rows") or [] if isinstance(row, dict)]
    for row in rows:
        if not str(row.get("raw_currency") or "").strip():
            row["raw_currency"] = currency
    subtotal, vat_amount, total = (
        result.get("document_subtotal"), result.get("document_vat_amount"), result.get("document_total"),
    )
    reconciles = all(isinstance(value, (int, float)) and value > 0 for value in (subtotal, vat_amount, total)) and abs((float(subtotal) + float(vat_amount)) - float(total)) <= max(0.02, abs(float(total)) * 0.005)
    invoice_excludes_vat = result.get("document_type") in {"invoice", "tax_invoice"} and reconciles
    website_includes_vat = source_kind == "url" and result.get("source_origin") == "supplier" and result.get("vat_mode") == "unknown"
    if invoice_excludes_vat and result.get("vat_mode") == "unknown":
        result["vat_mode"] = "excluded"
    elif website_includes_vat:
        result["vat_mode"] = "included"
    for row in rows:
        if row.get("raw_vat_mode") != "unknown":
            continue
        if invoice_excludes_vat:
            row["raw_vat_mode"] = "excluded"
            row["reason_codes"] = sorted(set(row.get("reason_codes") or []) | {"vat_inferred_from_document_total"})
        elif website_includes_vat:
            row["raw_vat_mode"] = "included"
            row["reason_codes"] = sorted(set(row.get("reason_codes") or []) | {"vat_inferred_for_supplier_website"})
    return result


def guard_price_source_row_activation(result: dict[str, Any]) -> dict[str, Any]:
    """Keep rows with missing critical pricing evidence out of active pricing."""
    for row in result.get("rows") or []:
        if not isinstance(row, dict) or row.get("status") != "ready":
            continue
        if row.get("item_kind") == "non_material":
            row["status"] = "excluded"
            row["reason_codes"] = sorted(
                set((row.get("reason_codes") or []) + ["non_material_row"])
            )
            continue
        if result.get("price_context") == "customer_sale":
            row["status"] = "excluded"
            row["reason_codes"] = sorted(
                set((row.get("reason_codes") or []) + ["customer_sale_not_material_cost"])
            )
            continue
        blockers: list[str] = []
        if row.get("raw_vat_mode") == "unknown":
            blockers.append("vat_basis_unknown")
        if (
            row.get("purchase_unit") in {"unknown", "other"}
            or row.get("calculation_unit") in {"unknown", "other"}
        ):
            # The agent may correctly identify a purchasable line without
            # proving its estimation unit. Keep it in Review instead of
            # allowing a later schema assertion to discard the whole source.
            blockers.append("missing_unit")
        # A quantity greater than one on an invoice is a line quantity, not
        # evidence that the listed price is for an opaque package. When the
        # document already proves the same canonical purchase and calculation
        # unit with a factor of one, keep that row active. A real package that
        # cannot be converted must instead arrive with an unknown unit or
        # factor and is still routed to Review above.
        if blockers:
            row["status"] = "unresolved"
            row["reason_codes"] = sorted(
                set((row.get("reason_codes") or []) + blockers)
            )
    return result


_LINE_TOTAL_REPAIR_REASONS = {
    "line_total_inconsistent",
    "unit_price_mismatch",
}


def _numbers_close(left: float, right: float) -> bool:
    tolerance = max(0.01, abs(right) * 0.01)
    return abs(left - right) <= tolerance


def reconcile_price_source_arithmetic(result: dict[str, Any]) -> dict[str, Any]:
    """Reconcile a row's quantity, unit price, and line total conservatively.

    Printed source prices are authoritative. Currency rounding can make a
    printed two-decimal unit price and its printed line total differ slightly,
    so compatible values pass unchanged. A conflicting value is never repaired
    by deriving a more precise unit price from ``line_total / quantity``. It
    stays in Review until a source-grounded reread establishes the three cells.
    """
    for row in result.get("rows") or []:
        if not isinstance(row, dict) or row.get("status") == "excluded":
            continue
        raw_price = row.get("raw_price")
        raw_quantity = row.get("raw_quantity")
        raw_line_total = row.get("raw_line_total")
        has_line_arithmetic = all(
            isinstance(value, (int, float)) and value > 0
            for value in (raw_price, raw_quantity, raw_line_total)
        )
        if has_line_arithmetic:
            expected_total = float(raw_price) * float(raw_quantity)
            if not _numbers_close(expected_total, float(raw_line_total)):
                if row.get("status") == "ready":
                    row["status"] = "unresolved"
                    row["reason_codes"] = sorted(
                        set(row.get("reason_codes") or []) | {"line_total_inconsistent"}
                    )

        if row.get("status") != "ready":
            continue
        raw_price = row.get("raw_price")
        conversion_factor = row.get("conversion_factor")
        if not isinstance(raw_price, (int, float)) or not isinstance(
            conversion_factor, (int, float)
        ):
            continue
        if raw_price <= 0 or conversion_factor <= 0:
            continue
        expected_price = raw_price / conversion_factor
        current_price = row.get("normalized_price")
        tolerance = max(0.01, abs(expected_price) * 0.01)
        if (
            not isinstance(current_price, (int, float))
            or abs(current_price - expected_price) > tolerance
        ):
            row["normalized_price"] = expected_price
            row["reason_codes"] = sorted(
                set((row.get("reason_codes") or []) + ["normalized_price_recalculated"])
            )
    return result


def guard_price_source_document_totals(result: dict[str, Any]) -> dict[str, Any]:
    """Downgrade rows when explicit subtotal, VAT, and total do not reconcile."""
    subtotal = result.get("document_subtotal")
    vat_amount = result.get("document_vat_amount")
    total = result.get("document_total")
    values = (subtotal, vat_amount, total)
    if not all(isinstance(value, (int, float)) and value > 0 for value in values):
        return result
    expected_total = float(subtotal) + float(vat_amount)
    tolerance = max(0.02, abs(float(total)) * 0.005)
    if abs(expected_total - float(total)) <= tolerance:
        return result
    for row in result.get("rows") or []:
        if not isinstance(row, dict) or row.get("status") == "excluded":
            continue
        row["confidence"] = max(0.0, float(row.get("confidence") or 0) - 20.0)
        row["reason_codes"] = sorted(
            set((row.get("reason_codes") or []) + ["document_total_mismatch"])
        )
    return result


def validate_price_source_result(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise PriceSourceSchemaError("price source result must be an object")
    required = set(PRICE_SOURCE_RESULT_JSON_SCHEMA["required"])
    if set(result) != required:
        raise PriceSourceSchemaError("price source result fields do not match the contract")
    if result["document_type"] not in DOCUMENT_TYPES:
        raise PriceSourceSchemaError("unsupported document type")
    if result["source_origin"] not in SOURCE_ORIGINS:
        raise PriceSourceSchemaError("unsupported source origin")
    if result["price_context"] not in PRICE_CONTEXTS:
        raise PriceSourceSchemaError("unsupported price context")
    if result["vat_mode"] not in VAT_MODES:
        raise PriceSourceSchemaError("unsupported VAT mode")
    if not isinstance(result["supplier_hp"], str) or (
        result["supplier_hp"] and not re.fullmatch(r"[1-9]\d{8}", result["supplier_hp"])
    ):
        raise PriceSourceSchemaError("supplier HP must be exactly nine digits")
    for key in ("document_subtotal", "document_vat_amount", "document_total"):
        if not isinstance(result[key], (int, float)) or result[key] < 0:
            raise PriceSourceSchemaError(f"{key} must be a non-negative number")
    if not isinstance(result["rows"], list):
        raise PriceSourceSchemaError("rows must be a list")

    row_fields = set(PRICE_SOURCE_RESULT_JSON_SCHEMA["properties"]["rows"]["items"]["required"])
    seen_numbers: set[int] = set()
    for row in result["rows"]:
        if not isinstance(row, dict) or set(row) != row_fields:
            raise PriceSourceSchemaError("price source row fields do not match the contract")
        number = row["source_row_number"]
        if not isinstance(number, int) or number < 1 or number in seen_numbers:
            raise PriceSourceSchemaError("source row numbers must be unique positive integers")
        seen_numbers.add(number)
        if row["material_type"] not in PRICE_SOURCE_CATEGORIES:
            raise PriceSourceSchemaError("unsupported row material type")
        if row["item_kind"] not in ITEM_KINDS:
            raise PriceSourceSchemaError("unsupported row item kind")
        attributes = row["identity_attributes"]
        if not isinstance(attributes, dict) or set(attributes) != set(IDENTITY_ATTRIBUTE_FIELDS):
            raise PriceSourceSchemaError("identity attributes do not match the contract")
        for key in ("thickness_mm", "width_mm", "length_mm", "depth_mm", "diameter_mm"):
            if not isinstance(attributes[key], (int, float)) or attributes[key] < 0:
                raise PriceSourceSchemaError(f"{key} must be a non-negative number")
        for key in set(IDENTITY_ATTRIBUTE_FIELDS) - {
            "thickness_mm", "width_mm", "length_mm", "depth_mm", "diameter_mm"
        }:
            if not isinstance(attributes[key], str):
                raise PriceSourceSchemaError(f"{key} must be a string")
        if row["status"] not in ROW_STATUSES:
            raise PriceSourceSchemaError("unsupported row status")
        if row["raw_vat_mode"] not in VAT_MODES:
            raise PriceSourceSchemaError("unsupported row VAT mode")
        if row["purchase_unit"] not in CANONICAL_UNIT_CODES:
            raise PriceSourceSchemaError("unsupported purchase unit")
        if row["calculation_unit"] not in CANONICAL_UNIT_CODES:
            raise PriceSourceSchemaError("unsupported calculation unit")
        confidence = row["confidence"]
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 100:
            raise PriceSourceSchemaError("row confidence must be between 0 and 100")
        for key in (
            "raw_package_quantity",
            "raw_quantity",
            "raw_discount_percent",
            "raw_discount_amount",
            "conversion_factor",
            "normalized_price",
        ):
            if not isinstance(row[key], (int, float)) or row[key] < 0:
                raise PriceSourceSchemaError(f"{key} must be a non-negative number")
        for key in ("raw_price", "raw_line_total"):
            if not isinstance(row[key], (int, float)):
                raise PriceSourceSchemaError(f"{key} must be a number")
            if row[key] < 0 and row["status"] != "excluded":
                raise PriceSourceSchemaError(f"negative {key} must be excluded")
        if row["status"] == "ready":
            if row["item_kind"] not in {"material", "operation_service"}:
                raise PriceSourceSchemaError("only material or operation-service rows may be ready")
            if not str(row["normalized_name"]).strip():
                raise PriceSourceSchemaError("ready row requires a normalized name")
            if row["normalized_price"] <= 0:
                raise PriceSourceSchemaError("ready row requires a normalized unit price")
            if row["purchase_unit"] in {"unknown", "other"} or row["calculation_unit"] in {"unknown", "other"}:
                raise PriceSourceSchemaError("ready row requires canonical units")
            if row["conversion_factor"] <= 0:
                raise PriceSourceSchemaError("ready row requires a positive conversion factor")
            expected_price = row["raw_price"] / row["conversion_factor"]
            tolerance = max(0.01, abs(expected_price) * 0.01)
            if abs(row["normalized_price"] - expected_price) > tolerance:
                raise PriceSourceSchemaError("normalized price does not match the conversion factor")
            if not str(row["raw_currency"] or result["currency"]).strip():
                raise PriceSourceSchemaError("ready row requires an identified currency")
    return result
