"""Estimate straight-through cuts and handling from the selected sheet stock."""

from collections import Counter, defaultdict
from dataclasses import dataclass, replace

from use_cases.wood_cnc_calculation import StockBatch, _layout


@dataclass(frozen=True)
class PanelSawParameters:
    kerf_mm: float = 3.2
    trim_per_axis_mm: float = 10
    feed_m_min: float = 6
    setup_min: float = 3
    standard_load_min: float = 2.5
    large_load_min: float = 4
    thin_plywood_load_min: float = 1.5
    stop_seconds: float = 40
    sheet_turn_seconds: float = 30
    piece_turn_seconds: float = 15
    long_pass_mm: float = 1000
    long_handling_seconds: float = 15
    short_handling_seconds: float = 8
    sort_seconds: float = 12
    cleanup_min: float = 1


DEFAULT_PANEL_SAW = PanelSawParameters()
_EPSILON = 1e-6


@dataclass(frozen=True)
class _Cut:
    axis: str
    target_mm: float
    cut_mm: float
    predecessor: int | None
    turn_piece: bool = False
    trim: bool = False

    @property
    def stop(self):
        return self.axis, self.trim, round(self.target_mm, 6)


def _sheet_cuts(placements, length, width, params):
    """Follow the free rectangles created by ripping first and crosscutting the strip."""
    trim = params.trim_per_axis_mm
    cuts = [_Cut("cross", trim, width, None, trim=True),
            _Cut("rip", trim, length - trim, 0, trim=True)]
    free = {}

    def add_region(x, y, a, b, origin):
        if a > _EPSILON and b > _EPSILON:
            free[round(x, 6), round(y, 6)] = a, b, origin

    add_region(trim / 2, trim / 2, length - trim, width - trim, 1)
    for part in placements:
        location = round(part.x, 6), round(part.y, 6)
        a, b, origin = free.pop(location)
        l, w = part.length, part.width
        if w < b - _EPSILON:
            cuts.append(_Cut("rip", w, a, origin, cuts[origin].axis != "rip"))
            origin = len(cuts) - 1
            add_region(part.x, part.y + w + params.kerf_mm, a, b - w - params.kerf_mm, origin)
        if l < a - _EPSILON:
            cuts.append(_Cut("cross", l, w, origin, cuts[origin].axis != "cross"))
            add_region(part.x + l + params.kerf_mm, part.y, a - l - params.kerf_mm, w, len(cuts) - 1)
    return cuts


def _stop_changes(cuts, starting_stops, *, group_repeated):
    """Batch ready cuts at the same stop while retaining every parent cut dependency."""
    children = defaultdict(list)
    for index, cut in enumerate(cuts):
        children[cut.predecessor].append(index)
    ready = children[None].copy()
    stops = starting_stops.copy()
    count = 0
    while ready:
        if group_repeated:
            occurrences = Counter(cuts[index].stop for index in ready)

            def priority(index):
                cut = cuts[index]
                return stops.get(cut.axis) != cut.stop, -occurrences[cut.stop], index

            index = min(ready, key=priority)
        else:
            index = min(ready)
        ready.remove(index)
        cut = cuts[index]
        count += stops.get(cut.axis) != cut.stop
        stops[cut.axis] = cut.stop
        ready.extend(children[index])
    return count, stops


def panel_saw_group(group, blanks, *, family, parameters=DEFAULT_PANEL_SAW):
    """Measure the same sized blanks using a saw-specific arrangement and kerf."""
    splits = {row["part_id"]: row for row in group["layout"]["splits"]}
    sized = []
    for part in blanks:
        split = splits.get(part.part_id)
        if split:
            part = replace(part, length_mm=split["length_mm"], width_mm=split["width_mm"],
                           quantity=part.quantity * split["pieces_per_part"])
        sized.append(part)
    length, width = group["size_mm"]
    batch = StockBatch(group["candidate_id"], "sheet", length, width, group["thickness_mm"], tuple(sized))
    candidates = []
    for rotate_first in (False, True) if any(part.rotation_allowed for part in sized) else (False,):
        placed, unplaced = _layout(batch, parameters.kerf_mm, parameters.trim_per_axis_mm / 2,
                                   rotate_first=rotate_first)
        sheets = defaultdict(list)
        for part in placed:
            sheets[part.sheet].append(part)
        sequences = [(parts, _sheet_cuts(parts, length, width, parameters)) for parts in sheets.values()]
        candidates.append((unplaced, sequences))
    unplaced, sequences = min(candidates, key=lambda row: (
        sum(row[0].values()), len(row[1]), sum(len(cuts) for _, cuts in row[1]),
    ))
    if family in {"plywood", "plywood_special"} and group["thickness_mm"] <= 5:
        load = parameters.thin_plywood_load_min
    elif max(length, width) > 2440 or min(length, width) > 1220:
        load = parameters.large_load_min
    else:
        load = parameters.standard_load_min
    stops = {}
    measured = []
    for parts, cuts in sequences:
        changes, stops = min((_stop_changes(cuts, stops, group_repeated=policy) for policy in (True, False)),
                             key=lambda result: result[0])
        cut_metres = sum(cut.cut_mm for cut in cuts) / 1000
        handling_seconds = sum(parameters.long_handling_seconds if cut.cut_mm >= parameters.long_pass_mm
                               else parameters.short_handling_seconds for cut in cuts)
        work = {
            "setup": parameters.setup_min / len(sequences),
            "load": load,
            "stops": changes * parameters.stop_seconds / 60,
            "turns": (parameters.sheet_turn_seconds + sum(cut.turn_piece for cut in cuts)
                      * parameters.piece_turn_seconds) / 60,
            "handling": handling_seconds / 60,
            "cutting": cut_metres / parameters.feed_m_min,
            "cleanup": parameters.cleanup_min,
        }
        measured.append({"placements": parts, "minutes": work, "cuts": len(cuts),
                         "cut_metres": cut_metres, "stop_changes": changes})
    return {"sheets": measured, "unplaced": unplaced}
