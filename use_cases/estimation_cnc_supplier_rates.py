"""Israel reference prices for sheet stock and standard cutting, before VAT."""

STANDARD_FORMATS_MM = {(1220, 2400), (1220, 2440)}
# https://algolan-express.co.il/ and the Alfandari and Egoz benchmark.
MELAMINE_RATES = {17: (225, 245), 28: (310, 340)}  # White, other or unspecified.
BIRCH_PLYWOOD_RATES = {4: 170, 6: 190, 12: 230, 16: 260, 18: 280, 21: 330, 24: 360, 27: 390, 30: 450}
RAW_PLYWOOD_17_RATE = 210
# Tsidky publishes ILS 30 for backs and ILS 60 for straight panel cutting, including VAT.
# https://etsel.tsidky.co.il/materials-and-prices/
BACK_PANEL_CUT_EX_VAT = 25.42
STANDARD_PANEL_CUT_EX_VAT = 50.85


def supplier_sheet_rate(family, *, thickness_mm, size_mm, specs, stock_rate):
    """Return a bundled sheet rate and its basis for this stock group."""
    if tuple(sorted(size_mm)) not in STANDARD_FORMATS_MM:
        return None, "quote_required"
    surface = str(specs.get("surface") or "").casefold()
    coating = str(specs.get("coating") or "").casefold()
    if family == "melamine_faced_particleboard" and thickness_mm in MELAMINE_RATES:
        white, standard = MELAMINE_RATES[thickness_mm]
        color = str(specs.get("color") or specs.get("colour") or specs.get("color_family") or "").casefold()
        return (white if color == "white" else standard), "published_reference"

    if surface not in {"", "raw", "uncoated"} or coating not in {"", "raw", "none", "uncoated"}:
        return None, "quote_required"
    is_hdf = family == "fibreboard_hardboard" or (
        family == "mdf_hdf" and specs.get("board_type") == "hdf"
    )
    if is_hdf and thickness_mm == 6 and stock_rate is not None:
        return round(stock_rate + BACK_PANEL_CUT_EX_VAT, 2), "stock_plus_straight_cut"

    if family == "plywood":
        species = str(specs.get("species") or "").casefold()
        if species in {"birch", "baltic_birch"}:
            rate = BIRCH_PLYWOOD_RATES.get(thickness_mm)
            return (rate, "published_reference") if rate is not None else (None, "quote_required")
        if not species and thickness_mm == 17:
            return RAW_PLYWOOD_17_RATE, "published_reference"
        if stock_rate is not None:
            return round(stock_rate + STANDARD_PANEL_CUT_EX_VAT, 2), "stock_plus_straight_cut"
    return None, "quote_required"
