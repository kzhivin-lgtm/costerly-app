"""Match printed dimensions to consecutive spans on native PDF dimension lines."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from functools import cache
from math import hypot
from typing import Any


# PDF points. These tolerances apply to drawn marks and text placement, not
# to the numerical equality of a chain sum and the printed total.
_TICK_TOLERANCE = 0.45
_MAX_PAGE_CONTENT_BYTES = 8_000_000
Point = tuple[float, float]


@dataclass(frozen=True)
class DimensionSpan:
    axis: int
    start: Point
    end: Point


@dataclass(frozen=True)
class PageDimensionSpans:
    width: float
    height: float
    spans: tuple[DimensionSpan, ...]


@dataclass(frozen=True)
class SpanReading:
    span: DimensionSpan
    value_mm: Decimal
    source_fact_ids: frozenset[str]


@dataclass(frozen=True)
class DimensionChainMatch:
    page: int
    chain_view: str
    total_view: str
    chain: tuple[SpanReading, ...]
    printed_total: SpanReading

    @property
    def source_fact_ids(self) -> frozenset[str]:
        return self.printed_total.source_fact_ids.union(*(part.source_fact_ids for part in self.chain))


def _native_dimension_spans(drawings: list[dict[str, Any]], transform: Callable) -> tuple[DimensionSpan, ...]:
    ticks: set[Point] = set()
    lines: set[tuple[int, Point, Point]] = set()
    for drawing in drawings:
        x0, y0, x1, y1 = drawing["rect"]
        compact = 0.8 <= x1 - x0 <= 6 and 0.8 <= y1 - y0 <= 6
        stroked = drawing["type"] in {"s", "fs"}
        if not compact and not stroked:
            continue
        for item in drawing["items"]:
            if item[0] != "l":
                continue
            first, last = item[1], item[2]
            dx, dy = abs(last[0] - first[0]), abs(last[1] - first[1])
            if compact and min(dx, dy) >= 0.8 and max(dx, dy) <= 2.2 * min(dx, dy):
                centre = transform(((x0 + x1) / 2, (y0 + y1) / 2))
                ticks.add(tuple(round(value, 1) for value in centre))
                break
            if stroked and max(dx, dy) >= 4 and min(dx, dy) <= 0.15:
                first, last = transform(first), transform(last)
                axis = 0 if abs(last[0] - first[0]) > abs(last[1] - first[1]) else 1
                start, end = sorted((first, last), key=lambda point: point[axis])
                lines.add((axis, start, end))

    ticks_by_line: dict[tuple[int, int], list[Point]] = defaultdict(list)
    for tick in sorted(ticks):
        for axis in (0, 1):
            ticks_by_line[axis, round(tick[1 - axis] / _TICK_TOLERANCE)].append(tick)
    for (axis, _), marks in ticks_by_line.items():
        marks.sort(key=lambda tick: tick[axis])
    spans = set()
    for axis, start, end in lines:
        across = (start[1 - axis] + end[1 - axis]) / 2
        band = round(across / _TICK_TOLERANCE)
        marks = []
        for offset in (-1, 0, 1):
            aligned = ticks_by_line.get((axis, band + offset))
            if not aligned:
                continue
            lower = bisect_left(aligned, start[axis] - _TICK_TOLERANCE, key=lambda tick: tick[axis])
            upper = bisect_right(aligned, end[axis] + _TICK_TOLERANCE, key=lambda tick: tick[axis])
            marks.extend(tick for tick in aligned[lower:upper] if abs(tick[1 - axis] - across) <= _TICK_TOLERANCE)
        if len(marks) < 2:
            continue
        first = min(marks, key=lambda tick: (hypot(tick[0] - start[0], tick[1] - start[1]), tick))
        last = min(marks, key=lambda tick: (hypot(tick[0] - end[0], tick[1] - end[1]), tick))
        if (hypot(first[0] - start[0], first[1] - start[1]) > _TICK_TOLERANCE
                or hypot(last[0] - end[0], last[1] - end[1]) > _TICK_TOLERANCE):
            continue
        interior = sorted(
            {tick for tick in marks if first[axis] + _TICK_TOLERANCE < tick[axis] < last[axis] - _TICK_TOLERANCE},
            key=lambda tick: (tick[axis], tick),
        )
        ticks_on_span = [first, *interior, last]
        for a, b in zip(ticks_on_span, ticks_on_span[1:]):
            if b[axis] - a[axis] >= 4:
                spans.add(DimensionSpan(axis, a, b))
    return tuple(sorted(spans, key=lambda span: (span.axis, span.start, span.end)))


def native_dimension_span_reader(file_bytes: bytes) -> Callable[[int], PageDimensionSpans | None]:
    """Cache compact, tick-bounded spans per page for the current RFQ only."""
    @cache
    def read(page_number: int) -> PageDimensionSpans | None:
        try:
            import pymupdf

            with pymupdf.open(stream=file_bytes, filetype="pdf") as document:
                page = document[page_number - 1]
                size = 0
                for xref in page.get_contents():
                    size += len(document.xref_stream(xref))
                    if size > _MAX_PAGE_CONTENT_BYTES:
                        return None
                a, b, c, d, e, f = page.rotation_matrix

                def transform(point: Point) -> Point:
                    x, y = point
                    return a * x + c * y + e, b * x + d * y + f

                spans = _native_dimension_spans(page.get_cdrawings(), transform)
                return PageDimensionSpans(page.rect.width, page.rect.height, spans)
        except (AttributeError, ImportError, IndexError, KeyError, RuntimeError, TypeError, ValueError):
            return None

    return read


def _bind_readings(
    occurrences: list[dict[str, Any]], bbox: dict[str, Any], source_size: tuple[int, int],
    geometry: PageDimensionSpans,
) -> list[SpanReading]:
    view_start = bbox["top_left_x"], bbox["top_left_y"]
    view_size = bbox["bottom_right_x"] - view_start[0], bbox["bottom_right_y"] - view_start[1]
    scale = geometry.width / source_size[0], geometry.height / source_size[1]
    candidates: dict[DimensionSpan, list[SpanReading]] = defaultdict(list)
    for occurrence in occurrences:
        local = occurrence.get("normalized_bbox")
        sources = frozenset(occurrence.get("source_fact_ids") or ())
        value = Decimal(occurrence["value_mm"])
        if not local or not sources or value <= 0:
            continue
        centre = tuple(
            (view_start[i] + view_size[i] * (local[f"top_left_{axis}"] + local[f"bottom_right_{axis}"]) / 2)
            * scale[i] for i, axis in enumerate(("x", "y"))
        )
        text_size = tuple(
            view_size[i] * (local[f"bottom_right_{axis}"] - local[f"top_left_{axis}"]) * scale[i]
            for i, axis in enumerate(("x", "y"))
        )
        aligned = []
        for span in geometry.spans:
            axis = span.axis
            along = abs(centre[axis] - (span.start[axis] + span.end[axis]) / 2)
            across = abs(centre[1 - axis] - (span.start[1 - axis] + span.end[1 - axis]) / 2)
            if along <= max(1.5, text_size[axis] * 0.4) and across <= min(14, max(5, text_size[1 - axis] * 1.2)):
                aligned.append((along + across, span))
        aligned.sort(key=lambda row: row[0])
        if aligned and (len(aligned) == 1 or aligned[1][0] - aligned[0][0] >= 1):
            span = aligned[0][1]
            candidates[span].append(SpanReading(span, value, sources))
    return [readings[0] for readings in candidates.values() if len(readings) == 1]


def _consecutive_chains(readings: list[SpanReading]):
    by_start = defaultdict(list)
    for reading in readings:
        by_start[reading.span.axis, reading.span.start].append(reading)
    for first in readings:
        chain = [first]
        source_ids = first.source_fact_ids
        axis = first.span.axis
        origin = first.span.start[1 - axis]
        scale = (first.span.end[axis] - first.span.start[axis]) / float(first.value_mm)
        while True:
            following = by_start.get((axis, chain[-1].span.end), ())
            if len(following) != 1:
                break
            next_reading = following[0]
            next_span = next_reading.span
            next_scale = (next_span.end[axis] - next_span.start[axis]) / float(next_reading.value_mm)
            if (source_ids & next_reading.source_fact_ids
                    or abs(next_span.end[1 - axis] - origin) > _TICK_TOLERANCE
                    or abs(next_scale - scale) > 0.03 * scale):
                break
            chain.append(next_reading)
            source_ids |= next_reading.source_fact_ids
            yield tuple(chain)


def build_dimension_chain_matches(
    fingerprints: list[dict[str, Any]], view_packages: list[dict[str, Any]], *,
    page_dimensions: dict[int, tuple[int, int]], excluded_views: set[str],
    read_spans: Callable[[int], PageDimensionSpans | None],
) -> dict[tuple[str, str], list[DimensionChainMatch]]:
    by_view = {row["group_id"]: row["occurrences"] for row in fingerprints}
    packages_by_page = defaultdict(list)
    for package in view_packages:
        view = package["visual_group_id"]
        if view not in excluded_views and by_view.get(view) and package["page_number"] in page_dimensions:
            packages_by_page[package["page_number"]].append(package)
    matches = defaultdict(list)
    for page, packages in packages_by_page.items():
        if len(packages) < 2 or max(len(by_view[p["visual_group_id"]]) for p in packages) < 2:
            continue
        geometry = read_spans(page)
        if not geometry or not geometry.spans:
            continue
        readings = {
            p["visual_group_id"]: _bind_readings(
                by_view[p["visual_group_id"]], p["bbox"], page_dimensions[page], geometry,
            )
            for p in packages
        }
        starts = {(span.axis, span.start) for span in geometry.spans}
        ends = {(span.axis, span.end) for span in geometry.spans}
        printed = defaultdict(list)
        for view, spans in readings.items():
            for reading in spans:
                span = reading.span
                if (span.axis, span.start) not in ends and (span.axis, span.end) not in starts:
                    printed[span.axis, reading.value_mm].append((view, reading))
        witnesses = []
        chain_views_by_target = defaultdict(set)
        for view, spans in readings.items():
            for chain in _consecutive_chains(spans):
                total = sum(span.value_mm for span in chain)
                targets = [(peer, span) for peer, span in printed[chain[0].span.axis, total] if peer != view]
                if len({peer for peer, _ in targets}) != 1:
                    continue
                source_ids = frozenset().union(*(span.source_fact_ids for span in chain))
                for peer, printed_total in targets:
                    if source_ids & printed_total.source_fact_ids:
                        continue
                    witnesses.append(DimensionChainMatch(page, view, peer, chain, printed_total))
                    chain_views_by_target[peer, printed_total].add(view)
        for match in witnesses:
            if len(chain_views_by_target[match.total_view, match.printed_total]) == 1:
                matches[tuple(sorted((match.chain_view, match.total_view)))].append(match)
    return dict(matches)
