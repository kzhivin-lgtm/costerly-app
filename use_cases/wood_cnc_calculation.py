"""Preliminary drawing-based routing and edging for sheet goods and solid wood."""

from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from math import ceil, isfinite


def _positive(value, label):
    if isinstance(value, bool) or not isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a finite positive number")


@dataclass(frozen=True)
class CncParameters:
    panel_feed_m_min: float = 8
    solid_feed_m_min: float = 6
    trim_mm: float = 5
    batch_setup_min: float = 10
    sheet_load_min: float = 4
    sheet_unload_min: float = 2
    sheet_cleanup_min: float = 1
    solid_blank_handling_min: float = 10
    transition_seconds_per_pass: float = 3
    tool_change_min: float = 0.5
    drilling_area_thresholds_m2: tuple[float, float] = (0.15, 0.50)
    drilling_seconds_per_part: tuple[float, float, float] = (10, 20, 30)
    drilling_min_panel_mm: float = 8
    panel_single_pass_max_mm: float = 22
    standard_cutter_max_mm: float = 32
    two_pass_max_mm: float = 40
    automatic_profile_max_mm: float = 50
    cutter_diameters_mm: tuple[float, float, float] = (8, 16, 18)
    panel_passes: tuple[int, int, int] = (1, 2, 3)
    solid_passes: tuple[int, int] = (2, 3)

    def __post_init__(self):
        for name in ("panel_feed_m_min", "solid_feed_m_min", "solid_blank_handling_min", "drilling_min_panel_mm"):
            _positive(getattr(self, name), name)
        limits = (self.panel_single_pass_max_mm, self.standard_cutter_max_mm,
                  self.two_pass_max_mm, self.automatic_profile_max_mm)
        if not all(a < b for a, b in zip(limits, limits[1:])):
            raise ValueError("Thickness limits must be in increasing order")
        if (len(self.drilling_area_thresholds_m2) != 2 or len(self.drilling_seconds_per_part) != 3
                or len(self.cutter_diameters_mm) != 3):
            raise ValueError("The default profiles require two drilling thresholds and three cutter and drilling tiers")
        if (len(self.panel_passes) != 3 or len(self.solid_passes) != 2
                or any(type(n) is not int or n < 1 for n in (*self.panel_passes, *self.solid_passes))):
            raise ValueError("CNC profiles require positive whole pass counts")
        low, high = self.drilling_area_thresholds_m2
        if not 0 < low < high:
            raise ValueError("Drilling area thresholds must be positive and increasing")
        for name in ("trim_mm", "batch_setup_min", "sheet_load_min", "sheet_unload_min", "sheet_cleanup_min",
                     "transition_seconds_per_pass", "tool_change_min"):
            value = getattr(self, name)
            if not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        for value in (*limits, *self.cutter_diameters_mm, *self.drilling_seconds_per_part, high):
            _positive(value, "CNC profile tier")


@dataclass(frozen=True)
class EdgingParameters:
    feed_m_min: float = 7
    setup_min: float = 10
    seconds_per_side: float = 12
    adhesive: str = "EVA"
    supplier_complex_edge_multiplier: float = 1.5

    def __post_init__(self):
        _positive(self.feed_m_min, "feed_m_min")
        if any(not isfinite(v) or v < 0 for v in (self.setup_min, self.seconds_per_side)):
            raise ValueError("Edging allowances must be finite and nonnegative")
        factor = self.supplier_complex_edge_multiplier
        if not isfinite(factor) or factor < 1:
            raise ValueError("Complex edge multiplier must be finite and at least one")


DEFAULT_CNC_PARAMETERS = CncParameters()
DEFAULT_EDGING_PARAMETERS = EdgingParameters()


@dataclass(frozen=True)
class Blank:
    part_id: str
    length_mm: float
    width_mm: float
    quantity: int = 1
    rotation_allowed: bool = True

    def __post_init__(self):
        _positive(self.length_mm, "length_mm")
        _positive(self.width_mm, "width_mm")
        if type(self.quantity) is not int or self.quantity < 1:
            raise ValueError("quantity must be a positive integer")
        if not self.part_id:
            raise ValueError("part_id is required")


@dataclass(frozen=True)
class StockBatch:
    stock_id: str
    kind: str                 # sheet, solid_panel, solid_blank
    length_mm: float
    width_mm: float
    thickness_mm: float
    blanks: tuple[Blank, ...]
    common_cut: bool = False   # explicitly selected for this material/process
    passes: int | None = None
    cutter_mm: float | None = None


@dataclass(frozen=True)
class Placement:
    part_id: str
    sheet: int
    x: float
    y: float
    length: float
    width: float


def _layout(batch, gap, trim, *, rotate_first=False):
    """Largest-first rectangle placement with a one-cutter finished-edge gap."""
    size = batch.length_mm - 2 * trim + gap, batch.width_mm - 2 * trim + gap
    sheets, placements, unplaced = [], [], Counter()
    for blank in sorted(batch.blanks, key=lambda p: (-p.length_mm * p.width_mm, p.part_id)):
        orientations = [(blank.length_mm, blank.width_mm)]
        if blank.rotation_allowed and batch.kind == "sheet":
            orientations.append((blank.width_mm, blank.length_mm))
            if rotate_first:
                orientations.reverse()
        orientations = [(a, b) for a, b in orientations if a + gap <= size[0] and b + gap <= size[1]]
        if not orientations:
            unplaced[blank.part_id] += blank.quantity
            continue
        for _ in range(blank.quantity):
            found = None
            if batch.kind != "solid_blank":
                for index, free in enumerate(sheets):
                    for cell, (x, y, a, b) in enumerate(free):
                        fit = [(l, w) for l, w in orientations if l + gap <= a and w + gap <= b]
                        if fit:
                            l, w = min(fit, key=lambda p: (min(a - p[0], b - p[1]), max(a - p[0], b - p[1])))
                            found = index, cell, x, y, a, b, l, w
                            break
                    if found:
                        break
            if found is None:
                index, cell = len(sheets), 0
                x = y = trim
                a, b = size
                l, w = orientations[0]
                sheets.append([(x, y, a, b)])
            else:
                index, cell, x, y, a, b, l, w = found
            free = sheets[index]
            del free[cell]
            used_l, used_w = l + gap, w + gap
            if a > used_l:
                free.append((x + used_l, y, a - used_l, used_w))
            if b > used_w:
                free.append((x, y + used_w, a, b - used_w))
            placements.append(Placement(blank.part_id, index + 1, x, y, l, w))
    return placements, dict(sorted(unplaced.items()))


def shared_cut_credits(placements, diameter):
    """Assign half of each shared cut to each of its two parts, in metres."""
    lines = defaultdict(lambda: ([], []))
    r = diameter / 2
    for p in placements:
        lines[p.sheet, "x", round(p.x - r, 6)][0].append((p.y, p.y + p.width, p.part_id))
        lines[p.sheet, "x", round(p.x + p.length + r, 6)][1].append((p.y, p.y + p.width, p.part_id))
        lines[p.sheet, "y", round(p.y - r, 6)][0].append((p.x, p.x + p.length, p.part_id))
        lines[p.sheet, "y", round(p.y + p.width + r, 6)][1].append((p.x, p.x + p.length, p.part_id))
    credits = defaultdict(float)
    for first, second in lines.values():
        first.sort()
        second.sort()
        i = j = 0
        while i < len(first) and j < len(second):
            a, b, part_a = first[i]
            c, d, part_b = second[j]
            overlap = max(0, min(b, d) - max(a, c)) / 2000
            credits[part_a] += overlap
            credits[part_b] += overlap
            if b <= d:
                i += 1
            else:
                j += 1
    return credits


def layout_cutting(batch, *, parameters=DEFAULT_CNC_PARAMETERS, rotate_first=False):
    """Place parts and record the geometry used by the CNC estimate."""
    if batch.kind not in {"sheet", "solid_panel", "solid_blank"}:
        raise ValueError("Unsupported wood stock kind")
    for label in ("length_mm", "width_mm", "thickness_mm"):
        _positive(getattr(batch, label), label)
    solid = batch.kind != "sheet"
    t = batch.thickness_mm
    if t > parameters.automatic_profile_max_mm and (batch.passes is None or batch.cutter_mm is None):
        raise ValueError("Stock beyond the default thickness range requires an explicit cutter and pass estimate")
    # These are budget allowances, not tool instructions. Long cutters also
    # depend on usable flute length, holding, and compatibility with the router.
    passes = batch.passes
    if passes is None:
        deep = t > parameters.two_pass_max_mm
        if solid:
            passes = parameters.solid_passes[deep]
        else:
            passes = parameters.panel_passes[deep + (t > parameters.panel_single_pass_max_mm)]
    cutter = batch.cutter_mm
    if cutter is None:
        cutter_index = sum(t > limit for limit in (parameters.standard_cutter_max_mm, parameters.two_pass_max_mm))
        cutter = parameters.cutter_diameters_mm[cutter_index]
    if type(passes) is not int or passes < 1:
        raise ValueError("passes must be a positive integer")
    _positive(cutter, "cutter_mm")
    trim_mm = parameters.trim_mm
    placed, unplaced = _layout(batch, cutter, trim_mm, rotate_first=rotate_first)
    shared = sum(shared_cut_credits(placed, cutter).values())
    credit = shared if batch.common_cut else 0.0
    profile = sum(2 * (p.length + p.width) for p in placed) / 1000
    cut = profile - credit
    path = cut * passes
    stock_count = len({p.sheet for p in placed})
    return {
        "stock_id": batch.stock_id, "stock_kind": batch.kind, "stock_count": stock_count,
        "blank_count": len(placed), "unplaced": unplaced, "placements": placed,
        "perimeter_m": profile, "potential_common_m": shared, "common_m": credit,
        "cut_m": cut, "path_m": path, "passes": passes, "cutter_mm": cutter,
    }


def sheet_fits_part(length, width, stock_length, stock_width, *, rotation_allowed):
    trim = 2 * DEFAULT_CNC_PARAMETERS.trim_mm
    usable_length, usable_width = stock_length - trim, stock_width - trim
    return (length <= usable_length and width <= usable_width) or (
        rotation_allowed and width <= usable_length and length <= usable_width
    )


def layout_joinable_sheet(batch):
    """Lay out known geometry, splitting only parts too large for the supplied format."""
    trim = 2 * DEFAULT_CNC_PARAMETERS.trim_mm
    usable_length, usable_width = batch.length_mm - trim, batch.width_mm - trim
    if usable_length <= 0 or usable_width <= 0:
        raise ValueError("Stock has no usable area after trim")
    blanks, splits = [], []
    for blank in batch.blanks:
        length, width = blank.length_mm, blank.width_mm
        if sheet_fits_part(length, width, batch.length_mm, batch.width_mm,
                           rotation_allowed=blank.rotation_allowed):
            blanks.append(blank)
            continue
        orientations = [(usable_length, usable_width)]
        if blank.rotation_allowed:
            orientations.append((usable_width, usable_length))
        pieces, along, across, pane_l, pane_w = min(
            (nx * ny, nx, ny, length / nx, width / ny)
            for a, b in orientations
            for nx, ny in [(ceil(length / a), ceil(width / b))]
        )
        blanks.append(replace(blank, length_mm=pane_l, width_mm=pane_w, quantity=blank.quantity * pieces))
        splits.append({
            "part_id": blank.part_id, "pieces_per_part": pieces, "part_count": blank.quantity,
            "length_mm": pane_l, "width_mm": pane_w, "length_sections": along, "width_sections": across,
        })
    batch = replace(batch, blanks=tuple(blanks))
    layouts = [layout_cutting(batch)]
    if any(blank.rotation_allowed for blank in batch.blanks):
        layouts.append(layout_cutting(batch, rotate_first=True))
    layout = min(layouts, key=lambda row: (sum(row["unplaced"].values()), row["stock_count"], row["path_m"]))
    return {**layout, "splits": splits}


def cutting_work(layout, *, parameters=DEFAULT_CNC_PARAMETERS):
    feed = parameters.panel_feed_m_min if layout["stock_kind"] == "sheet" else parameters.solid_feed_m_min
    return {
        **layout,
        "feed_m_min": feed,
        "cut_minutes": layout["path_m"] / feed,
        "move_minutes": layout["blank_count"] * layout["passes"] * parameters.transition_seconds_per_pass / 60,
    }


def calculate_cutting(batch, *, parameters=DEFAULT_CNC_PARAMETERS):
    layout = layout_cutting(batch, parameters=parameters)
    return cutting_work(layout, parameters=parameters)


def drilling_minutes(parts, *, parameters=DEFAULT_CNC_PARAMETERS):
    """A coarse size-based allowance once per physical part sent to drilling."""
    def seconds(part):
        area = part.length_mm * part.width_mm / 1_000_000
        tier = sum(area > limit for limit in parameters.drilling_area_thresholds_m2)
        return parameters.drilling_seconds_per_part[tier]
    return sum(seconds(p) * p.quantity for p in parts) / 60


def cnc_workload(batches, *, drilling_parts=(), tool_changes=None, parameters=DEFAULT_CNC_PARAMETERS):
    return cnc_workload_from_layout(
        (layout_cutting(batch, parameters=parameters) for batch in batches),
        drilling_parts=drilling_parts, tool_changes=tool_changes, parameters=parameters,
    )


def cnc_workload_from_layout(layouts, *, drilling_parts=(), tool_changes=None, parameters=DEFAULT_CNC_PARAMETERS):
    if tool_changes is not None and (type(tool_changes) is not int or tool_changes < 0):
        raise ValueError("tool_changes must be a nonnegative integer")
    results = [cutting_work(layout, parameters=parameters) for layout in layouts]
    active = [r for r in results if r["stock_count"]]
    sheets = sum(r["stock_count"] for r in active if r["stock_kind"] != "solid_blank")
    blanks = sum(r["stock_count"] for r in active if r["stock_kind"] == "solid_blank")
    # Panel handling and solid blank handling use separate assumptions.
    load = sheets * parameters.sheet_load_min
    unload = sheets * parameters.sheet_unload_min
    cleanup = sheets * parameters.sheet_cleanup_min
    solid_handling = blanks * parameters.solid_blank_handling_min
    handling = load + unload + cleanup + solid_handling
    placed_ids = {p.part_id for batch in active for p in batch["placements"]}
    routed_drilling = [part for part in drilling_parts if part.part_id in placed_ids]
    drill = drilling_minutes(routed_drilling, parameters=parameters)
    cut = sum(r["cut_minutes"] for r in active)
    moves = sum(r["move_minutes"] for r in active)
    setup = sum(r.get("batch_share", 1) for r in active) * parameters.batch_setup_min
    if tool_changes is None:
        tool_changes = max(0, len({r["cutter_mm"] for r in active}) - 1)
    changes = tool_changes * parameters.tool_change_min if active else 0
    return {
        "batches": results, "sheet_count": sheets, "solid_stock_count": blanks,
        "blank_count": sum(r["blank_count"] for r in active),
        "drilled_part_count": sum(p.quantity for p in routed_drilling),
        "cut_m": sum(r["cut_m"] for r in active), "path_m": sum(r["path_m"] for r in active),
        "setup_minutes": setup, "handling_minutes": handling, "cut_minutes": cut,
        "load_minutes": load, "unload_minutes": unload, "cleanup_minutes": cleanup,
        "solid_handling_minutes": solid_handling,
        "move_minutes": moves, "drilling_minutes": drill, "tool_change_minutes": changes,
        "tool_changes": tool_changes,
        "manual_minutes": setup + handling + changes,
        "program_minutes": cut + moves + drill,
        "machine_minutes": setup + handling + cut + moves + drill + changes,
        "geometry_complete": not any(r["unplaced"] for r in results),
    }


@dataclass(frozen=True)
class Edges:
    part: Blank
    tape_group: str           # includes tape, finish and finished panel thickness
    along_length: int
    along_width: int


def edging_workload(edges, *, parameters=DEFAULT_EDGING_PARAMETERS):
    feed_m_min, setup_min, seconds_per_side = parameters.feed_m_min, parameters.setup_min, parameters.seconds_per_side
    groups = defaultdict(lambda: {"metres": 0.0, "sides": 0})
    for edge in edges:
        a, b = edge.along_length, edge.along_width
        if any(type(n) is not int or not 0 <= n <= 2 for n in (a, b)) or not a + b:
            raise ValueError("Edges require one to four valid sides")
        part = edge.part
        group = groups[edge.tape_group]
        group["metres"] += part.quantity * (a * part.length_mm + b * part.width_mm) / 1000
        group["sides"] += part.quantity * (a + b)
    metres = sum(g["metres"] for g in groups.values())
    sides = sum(g["sides"] for g in groups.values())
    for group in groups.values():
        group["setup_minutes"] = setup_min
        group["feed_minutes"] = group["metres"] / feed_m_min
        group["handling_minutes"] = group["sides"] * seconds_per_side / 60
        group["machine_minutes"] = sum(group[key] for key in (
            "setup_minutes", "feed_minutes", "handling_minutes",
        ))
    setup = len(groups) * setup_min
    feed = metres / feed_m_min
    handling = sides * seconds_per_side / 60
    occupied = setup + feed + handling
    return {
        "groups": dict(sorted(groups.items())), "edge_m": metres, "edge_count": sides,
        "setup_minutes": setup, "feed_minutes": feed, "handling_minutes": handling,
        "machine_minutes": occupied, "manual_minutes": occupied, "program_minutes": 0,
    }


def in_house_cost(work, *, gross_rate_per_hour, machine_rate_per_hour=None, attendance=1.0):
    _positive(gross_rate_per_hour, "gross_rate_per_hour")
    if not 0 <= attendance <= 1:
        raise ValueError("attendance must be between zero and one")
    if machine_rate_per_hour is not None:
        _positive(machine_rate_per_hour, "machine_rate_per_hour")
    hours = (work["manual_minutes"] + work["program_minutes"] * attendance) / 60
    return {
        "labor_hours": hours, "gross_rate": gross_rate_per_hour,
        "labor_base_cost": round(hours * gross_rate_per_hour, 2),
        "machine_cost": (
            None if machine_rate_per_hour is None
            else round(work["machine_minutes"] / 60 * machine_rate_per_hour, 2)
        ),
    }


def supplier_cost(work, *, unit, rate_ex_vat, includes_material, includes_edging=False,
                  complex_edge_m=0, edge_parameters=None):
    """Apply a supplier's specific basis. Bundled work is one purchase."""
    _positive(rate_ex_vat, "rate_ex_vat")
    if not work.get("geometry_complete", True):
        raise ValueError("Incomplete geometry cannot price the entire supplier scope")
    drivers = {
        "job": 1, "sheet": work.get("sheet_count"), "part": work.get("blank_count"),
        "drilled_part": work.get("drilled_part_count"),
        "cut_m": work.get("cut_m"), "path_m": work.get("path_m"),
        "edge_m": work.get("edge_m"), "machine_hour": work["machine_minutes"] / 60,
    }
    if unit not in drivers or drivers[unit] is None:
        raise ValueError(f"Unsupported quote unit for this operation: {unit}")
    quantity = drivers[unit]
    billable = quantity
    if complex_edge_m:
        if unit != "edge_m" or not 0 < complex_edge_m <= quantity or edge_parameters is None:
            raise ValueError("Complex edge allowance requires edge metres and an estimating profile")
        factor = edge_parameters.supplier_complex_edge_multiplier
        billable += (factor - 1) * complex_edge_m
    return {
        "unit": unit, "quantity": quantity, "cost_ex_vat": round(billable * rate_ex_vat, 2),
        **({"complex_edge_m": complex_edge_m, "billable_quantity": billable} if complex_edge_m else {}),
        "includes_material": includes_material, "includes_edging": includes_edging,
        "internal_labor_hours": 0,
    }


def subcontracted_order(cnc, edging, *, cnc_quote, edge_quote=None):
    """Price a CNC/edging bundle or a pair of disjoint supplier quotes."""
    priced_cnc = supplier_cost(cnc, **cnc_quote)
    included = priced_cnc["includes_edging"]
    if included and edge_quote is not None:
        raise ValueError("The CNC quote already covers edging")
    priced_edge = supplier_cost(edging, **edge_quote) if edge_quote is not None else None
    known_scope = included or priced_edge is not None or (
        edging.get("geometry_complete", True) and edging["edge_count"] == 0
    )
    return {
        "cnc": priced_cnc,
        "edging": priced_edge,
        "total_ex_vat": round(priced_cnc["cost_ex_vat"] + (priced_edge or {}).get("cost_ex_vat", 0), 2)
        if known_scope else None,
    }
