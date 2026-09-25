from __future__ import annotations

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
    "other",
}
PRICE_CONTEXTS = {"public_list", "supplier_quote", "customer_transaction", "unknown"}
VAT_MODES = {"included", "excluded", "mixed", "unknown"}
ROW_STATUSES = {"ready", "unresolved", "excluded"}
PRICE_SOURCE_CATEGORIES = (
    "Wood Sheets",
    "Solid Wood",
    "Wood Supplies",
    "Glass",
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

PRICE_SOURCE_RESULT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "supplier_name",
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
                    "material_type",
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
                    "material_type": {"type": "string", "enum": list(PRICE_SOURCE_CATEGORIES)},
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


def guard_price_source_row_activation(result: dict[str, Any]) -> dict[str, Any]:
    """Keep rows with unresolved package-to-unit conversion out of active pricing."""
    for row in result.get("rows") or []:
        if not isinstance(row, dict) or row.get("status") != "ready":
            continue
        package_quantity = row.get("raw_package_quantity")
        conversion_factor = row.get("conversion_factor")
        if (
            isinstance(package_quantity, (int, float))
            and package_quantity > 1
            and row.get("purchase_unit") == row.get("calculation_unit")
            and isinstance(conversion_factor, (int, float))
            and conversion_factor == 1
        ):
            row["status"] = "unresolved"
            row["reason_codes"] = sorted(
                set((row.get("reason_codes") or []) + ["package_conversion_unresolved"])
            )
    return result


def reconcile_price_source_arithmetic(result: dict[str, Any]) -> dict[str, Any]:
    """Make price division deterministic while preserving the model's evidence choices."""
    for row in result.get("rows") or []:
        if not isinstance(row, dict) or row.get("status") != "ready":
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
    if result["price_context"] not in PRICE_CONTEXTS:
        raise PriceSourceSchemaError("unsupported price context")
    if result["vat_mode"] not in VAT_MODES:
        raise PriceSourceSchemaError("unsupported VAT mode")
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
