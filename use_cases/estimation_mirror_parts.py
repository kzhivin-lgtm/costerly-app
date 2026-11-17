"""Price made-to-size mirrors as purchased parts."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from math import isfinite
import re


MIRROR_SET_REQUIREMENT = "cb-finished-mirror-set"
MIRROR_QUOTE_REQUIREMENT = "cb-finished-mirror-quote"
MIRROR_SET_NAME = "Finished mirrors"
_CENT = Decimal("0.01")
_ALLOWANCE_ILS_M2 = Decimal(325)
_STANDARD_PROCESSING = "Cut to size, polished edges"
_SPECIAL_SPEC = re.compile(
    r"\b(?:round|oval|arch(?:ed)?|bevel(?:led|ed)?|faceted|low[ -]iron|extra[ -]clear|bronze|"
    r"tinted|smoked|antique|tempered|laminated|backed|holes?|cutouts?|notch(?:es)?)\b"
    r"|фацет|фигур|овальн|кругло|арочн|отверсти|бронз|тонир|закал|מושחר|עגול|פאזה|קדח",
    re.IGNORECASE,
)


def _positive(value):
    return type(value) in (int, float) and isfinite(value) and value > 0


def _supplier_price(offers, *, length, width, thickness, area):
    """Use only a matching rectangular silver mirror offer with both operations included."""
    prices = []
    today = date.today().isoformat()
    for offer in offers:
        spec = offer.get("conversion_basis") or {}
        if (
            offer.get("status") not in {"active", "candidate"}
            or offer.get("source_currency") != "ILS"
            or offer.get("vat_mode") != "included"
            or offer.get("delivery_included") is not False
            or set(offer.get("included_services") or ()) != {"cut_to_size", "flat_edge_polishing"}
            or (offer.get("valid_from") or today) > today
            or (offer.get("valid_to") or today) < today
            or spec.get("pricing_basis") != "per_finished_piece_using_its_area"
            or spec.get("thickness_mm") != thickness
            or spec.get("shape") != "rectangle"
            or spec.get("grade") != "silver"
            or spec.get("installation_included") is not False
            or spec.get("heat_treatment")
            or spec.get("optical_surcharge_gross_ils_m2")
            or spec.get("gross_area_surcharge_ils_m2")
        ):
            continue
        bounds = spec.get("dimensions_mm")
        if (
            not isinstance(bounds, (list, tuple)) or len(bounds) != 2
            or any(not isinstance(axis, (list, tuple)) or len(axis) != 2
                   or not all(_positive(mm) for mm in axis) for axis in bounds)
        ):
            continue
        (min_a, max_a), (min_b, max_b) = bounds
        if not any(min_a <= a <= max_a and min_b <= b <= max_b for a, b in ((length, width), (width, length))):
            continue
        rate = spec.get("base_gross_rate_ils_m2")
        minimum = spec.get("min_gross_ils_per_piece")
        vat = spec.get("vat_percent")
        if not (_positive(rate) and _positive(vat) and (minimum == 0 or _positive(minimum))):
            continue
        gross = max(area * Decimal(str(rate)), Decimal(str(minimum)))
        net = gross / (1 + Decimal(str(vat)) / 100)
        prices.append((net, str(offer.get("supplier_name") or "Israel Reference"), str(offer.get("market_offer_id") or "")))
    return min(prices) if prices else None


def finished_mirror_part(row, measurements, *, multiplier, offers):
    length, width, thickness = (measurements.get(axis, {}).get("mm") for axis in ("length", "width", "thickness"))
    count = row.get("quantity")
    note = (row.get("material_note") or {}).get("source_text")
    thickness_assumed = not _positive(thickness)
    if thickness_assumed:
        thickness = 4
    special = (
        row.get("shape") not in (None, "", "rectangle", "rectangular")
        or row.get("edge_finish") not in (None, "", "flat_polished", "polished", "flat_edge_polishing")
        or any(row.get(key) for key in ("holes", "hole_count", "cutouts", "corner_radius_mm", "bevel", "special_processing"))
        or _SPECIAL_SPEC.search(" ".join(str(text) for text in (row.get("material_hint"), note) if text))
    )
    price = total = None
    authority = supplier = offer_id = None
    processing = "Quote required"
    if not special and all(_positive(value) for value in (length, width, count)):
        area = Decimal(str(length)) * Decimal(str(width)) / 1_000_000
        if matched := _supplier_price(offers, length=length, width=width, thickness=thickness, area=area):
            price, supplier, offer_id = matched
            authority = "israel_reference"
            processing = f"{_STANDARD_PROCESSING} · {supplier}"
        elif thickness == 4:
            price = area * _ALLOWANCE_ILS_M2
            authority = "assumption"
            processing = f"{_STANDARD_PROCESSING} (estimate)"
        else:
            processing = f"{_STANDARD_PROCESSING} · quote required"
        if price is not None:
            price = price.quantize(_CENT, rounding=ROUND_HALF_UP)
            total = price * Decimal(str(count * multiplier))
    return {
        "label": "Mirror", "block_id": row.get("block_id"),
        "length_mm": length, "width_mm": width, "thickness_mm": thickness,
        "thickness_estimated": thickness_assumed,
        "quantity": count * multiplier if _positive(count) else None,
        "processing": processing, "authority": authority, "supplier": supplier, "offer_id": offer_id,
        "unit_price": float(price) if price is not None else None,
        "total": float(total) if total is not None else None,
    }


def finished_mirror_set(parts):
    priced = all(part["total"] is not None for part in parts)
    return {
        "parts": parts,
        "piece_count": sum(part["quantity"] for part in parts) if all(part["quantity"] is not None for part in parts) else None,
        "set_price": float(sum(Decimal(str(part["total"])) for part in parts)) if priced else None,
        "authority": "israel_reference" if all(part["authority"] == "israel_reference" for part in parts) else "assumption",
    }
