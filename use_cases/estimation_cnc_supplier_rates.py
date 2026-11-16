"""Israel reference prices for sheet stock and standard cutting, before VAT."""

SUPPLIER_PROFILE_VERSION = "israel-cnc-sheet-reference-v1"
SUPPLIER_MACHINING_RATE = 12
# Installed tape, a budget estimate. Veneer has a separate tape allowance.
SUPPLIER_EDGE_RATE_PER_M = {
    ("melamine", 24): 7, ("melamine", 45): 12,
    ("pvc", 24): 7, ("pvc", 45): 12,
    ("veneer", 24): 9, ("veneer", 45): 14,
}
SUPPLIER_EDGE_RATE_INCLUDES_TAPE = True
STANDARD_FORMATS_MM = {(1220, 2400), (1220, 2440)}
# https://algolan-express.co.il/ and the Alfandari and Egoz benchmark.
# White, other or unspecified. The 17 and 28 mm lines are public references.
MELAMINE_RATES = {
    12: (185, 200), 16: (220, 235), 17: (225, 245), 18: (235, 255),
    19: (240, 260), 20: (250, 270), 25: (290, 320), 27: (300, 330), 28: (310, 340), 30: (325, 355),
}
MELAMINE_17_LARGE_FORMAT_RATES = {(1220, 2750): (250, 270), (2070, 2800): (600, 640)}
BIRCH_PLYWOOD_RATES = {4: 170, 6: 190, 12: 230, 16: 260, 18: 280, 21: 330, 24: 360, 27: 390, 30: 450}
RAW_PLYWOOD_RATES = {4: 114, 8: 140, 12: 203, 16: 205, 17: 210, 18: 225}
# Thickness, coated faces, finish class.
HPL_PLYWOOD_RATES = {(4, 1, "white"): 131, (4, 1, "decorative"): 148,
                    (12, 2, "white"): 237, (17, 1, "white"): 250,
                    (17, 2, "white"): 290, (17, 2, "decorative"): 325}
# Tsidky publishes ILS 30 for backs and ILS 60 for straight panel cutting, including VAT.
# https://etsel.tsidky.co.il/materials-and-prices/
BACK_PANEL_CUT_EX_VAT = 25.42
STANDARD_PANEL_CUT_EX_VAT = 50.85
# Algolan's finished cabinet back. Egoz publishes matching white and colored
# single-faced plywood in 2440 × 1220 mm.
FINISHED_BACKING_RATES = {"white": 130, "decorative": 140}
# Model stock from ILS 210 at 17 mm (Tsidky) and ILS 230 at 19 mm
# (Studio Leetz), both including VAT. Keep the Tsidky straight-cut charge fixed.
RAW_MDF_17_STOCK_INCL_VAT = 210
RAW_MDF_STOCK_PER_ADDED_MM_INCL_VAT = 10
RAW_MDF_CUT_INCL_VAT = 60
RAW_MDF_REFERENCE_VAT_FACTOR = 1.18
RAW_MDF_REFERENCE_RATES = {4: 118.64, 8: 156.78, 17: 228.81}
THIN_RAW_MDF_ESTIMATES = {3: 110, 5: 128, 6: 138, 10: 173, 12: 189}
GREEN_MDF_RATES = {17: 210, 19: 230, 22: 310}
WHITE_CAST_MDF_RATES = {17: 283.90, 19: 300.85}
# The virtual quote deliberately models thicknesses outside the stocked list.
# This is a price for an identified sheet, not a recommendation that it be bought.
THICK_RAW_MDF_MM = {15, 16, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28, 30, 32, 38, 40}
VENEER_MDF_MM = {8, 12, 15, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28, 30}
# Lev1 catalog: ILS 318 for 20 mm oak stock + ILS 50.85 for straight cuts.
# The difference from the same raw sheet is ILS 115. Allow ILS 125 for standard two-sided oak.
OAK_VENEER_BUDGET_ADD_PER_SHEET = 125


def _raw_mdf_rate(thickness_mm):
    if thickness_mm in RAW_MDF_REFERENCE_RATES:
        return RAW_MDF_REFERENCE_RATES[thickness_mm], "stock_plus_straight_cut"
    if thickness_mm in THIN_RAW_MDF_ESTIMATES:
        return THIN_RAW_MDF_ESTIMATES[thickness_mm], "thickness_estimate"
    if thickness_mm in THICK_RAW_MDF_MM:
        stock = RAW_MDF_17_STOCK_INCL_VAT + RAW_MDF_STOCK_PER_ADDED_MM_INCL_VAT * (thickness_mm - 17)
        rate = round((stock + RAW_MDF_CUT_INCL_VAT) / RAW_MDF_REFERENCE_VAT_FACTOR, 2)
        return rate, "stock_plus_straight_cut" if thickness_mm == 19 else "thickness_estimate"
    return None, "quote_required"


def supplier_sheet_rate(
    family, *, thickness_mm, size_mm, specs, stock_rate, stock_name="", variant="", stock_authority=None,
):
    """Return a bundled sheet rate and its basis for this stock group."""
    size = tuple(sorted(size_mm))
    color = str(specs.get("color") or specs.get("colour") or specs.get("color_family") or "").casefold()
    if family == "melamine_faced_particleboard" and thickness_mm == 17 and size in MELAMINE_17_LARGE_FORMAT_RATES:
        white, standard = MELAMINE_17_LARGE_FORMAT_RATES[size]
        return (white if color == "white" else standard), "format_estimate"
    if size not in STANDARD_FORMATS_MM:
        return None, "quote_required"
    surface = str(specs.get("surface") or "").casefold()
    coating = str(specs.get("coating") or "").casefold()
    name = stock_name.casefold()
    if (family == "plywood_special" and thickness_mm == 5 and variant in FINISHED_BACKING_RATES
            and name.removesuffix(f", {variant}") == "plywood, 5 mm, hpl-faced"):
        return FINISHED_BACKING_RATES[variant], "published_reference"
    if family == "melamine_faced_particleboard" and thickness_mm in MELAMINE_RATES:
        white, standard = MELAMINE_RATES[thickness_mm]
        basis = "published_reference" if thickness_mm in {17, 28} else "thickness_estimate"
        return (white if color == "white" else standard), basis

    if (family == "mdf_hdf" and specs.get("board_type") == "mdf") or family == "faced_mdf":
        if surface == "white_cast_coated" and thickness_mm in WHITE_CAST_MDF_RATES:
            return WHITE_CAST_MDF_RATES[thickness_mm], "stock_plus_straight_cut"
        if surface == "veneer_two_sided":
            species = str(specs.get("species") or "").casefold()
            if thickness_mm in VENEER_MDF_MM and species in {"", "oak", "natural_oak"} and specs.get("finish") in {None, "", "raw", "unfinished"}:
                rate, _ = _raw_mdf_rate(thickness_mm)
                return round(rate + OAK_VENEER_BUDGET_ADD_PER_SHEET, 2), "veneer_estimate"
            if stock_authority == "company" and stock_rate is not None:
                return round(stock_rate + STANDARD_PANEL_CUT_EX_VAT, 2), "stock_plus_straight_cut"
        if surface == "raw":
            if specs.get("moisture_resistant") is True or "moisture-resistant" in name:
                if thickness_mm in GREEN_MDF_RATES:
                    return GREEN_MDF_RATES[thickness_mm], "published_reference"
            elif "standard, raw" in name or specs.get("grade") == "standard":
                return _raw_mdf_rate(thickness_mm)

    if family in {"plywood", "plywood_special"} and (surface.startswith("hpl") or coating.startswith("hpl")):
        faces = {"hpl_one_side": 1, "hpl_one_sided": 1, "hpl_two_sides": 2, "hpl_two_sided": 2}.get(surface)
        faces = faces or {"one_sided": 1, "two_sided": 2}.get(specs.get("facing"))
        if faces is None:
            faces = 1 if surface == "hpl_one_face" else 2 if surface == "hpl_two_faces" else None
        finish = "white" if color == "white" or variant == "white" else "decorative" if color or variant else ""
        rate = HPL_PLYWOOD_RATES.get((thickness_mm, faces, finish))
        if rate is not None:
            basis = "stock_plus_straight_cut" if thickness_mm < 17 or finish == "decorative" else "published_reference"
            return rate, basis

    if surface not in {"", "raw", "uncoated"} or coating not in {"", "raw", "none", "uncoated"}:
        return None, "quote_required"
    is_hdf = family == "fibreboard_hardboard" or (
        family == "mdf_hdf" and specs.get("board_type") == "hdf"
    )
    if is_hdf and thickness_mm in {3.2, 6}:
        if stock_rate is not None:
            return round(stock_rate + BACK_PANEL_CUT_EX_VAT, 2), "stock_plus_straight_cut"
        if thickness_mm == 6:
            return 120, "thickness_estimate"

    if family == "plywood":
        species = str(specs.get("species") or "").casefold()
        if species in {"birch", "baltic_birch"}:
            rate = BIRCH_PLYWOOD_RATES.get(thickness_mm)
            return (rate, "published_reference") if rate is not None else (None, "quote_required")
        if not species and thickness_mm in RAW_PLYWOOD_RATES:
            basis = "published_reference" if thickness_mm == 17 else "thickness_estimate" if thickness_mm in {16, 18} else "stock_plus_straight_cut"
            return RAW_PLYWOOD_RATES[thickness_mm], basis
        if stock_rate is not None:
            return round(stock_rate + STANDARD_PANEL_CUT_EX_VAT, 2), "stock_plus_straight_cut"
    return None, "quote_required"
