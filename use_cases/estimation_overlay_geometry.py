"""Exterior outlines and source-backed edges for a single drawing projection."""

from collections import defaultdict
from math import dist

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def _delta(a, b):
    return b[0] - a[0], b[1] - a[1]


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _edges(ring):
    return zip(ring, ring[1:] + ring[:1])


def _area(ring):
    return sum(_cross(a, b) for a, b in _edges(ring)) / 2


def _line_distance(a, b, p):
    return abs(_cross(_delta(a, b), _delta(a, p))) / dist(a, b)


def _simplify(path, tolerance):
    start, end = path[0], path[-1]
    if len(path) < 3:
        return path
    if start == end:
        index = max(range(1, len(path) - 1), key=lambda i: dist(path[i], start))
    else:
        index = max(range(1, len(path) - 1), key=lambda i: _line_distance(start, end, path[i]))
        if _line_distance(start, end, path[index]) <= tolerance:
            return [start, end]
    return _simplify(path[:index + 1], tolerance)[:-1] + _simplify(path[index:], tolerance)


def exterior_rings(polygons):
    """Trace the union of assigned faces without internal seams or a convex wrap."""
    if len(polygons) == 1:
        ring = polygons[0]
        return [ring if _area(ring) > 0 else ring[::-1]]
    left = int(min(x for p in polygons for x, _ in p)) - 4
    top = int(min(y for p in polygons for _, y in p)) - 4
    right = int(max(x for p in polygons for x, _ in p)) + 5
    bottom = int(max(y for p in polygons for _, y in p)) + 5
    mask = Image.new("L", (right - left, bottom - top))
    painter = ImageDraw.Draw(mask)
    for polygon in polygons:
        painter.polygon([(x - left, y - top) for x, y in polygon], fill=255)
    mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    ImageDraw.floodfill(mask, (0, 0), 128)
    inside = np.asarray(mask) != 128
    edges = defaultdict(list)
    for y, x in np.argwhere(inside[1:, :] & ~inside[:-1, :]):
        edges[x, y + 1].append((x + 1, y + 1))
    for y, x in np.argwhere(inside[:-1, :] & ~inside[1:, :]):
        edges[x + 1, y + 1].append((x, y + 1))
    for y, x in np.argwhere(inside[:, 1:] & ~inside[:, :-1]):
        edges[x + 1, y + 1].append((x + 1, y))
    for y, x in np.argwhere(inside[:, :-1] & ~inside[:, 1:]):
        edges[x + 1, y].append((x + 1, y + 1))
    rings = []
    while edges:
        start = pos = next(iter(edges))
        path = [start]
        while pos in edges:
            following = edges[pos].pop()
            if not edges[pos]:
                del edges[pos]
            pos = following
            path.append(pos)
            if pos == start:
                ring = _simplify(path, 1.2)[:-1]
                if len(ring) >= 3 and _area(ring) > 16:
                    rings.append([(float(x + left), float(y + top)) for x, y in ring])
                break
    return rings


def _ray_hits(center, direction, ring):
    for index, (a, b) in enumerate(_edges(ring)):
        edge = _delta(a, b)
        determinant = _cross(direction, edge)
        if abs(determinant) < 1e-6:
            continue
        offset = _delta(center, a)
        along = _cross(offset, edge) / determinant
        across = _cross(offset, direction) / determinant
        if along > 0 and 0 <= across <= 1:
            yield along, index, across


def volume_edges(ring, segments):
    """Find a native three-edge junction whose rays reach the shell boundary."""
    if not segments:
        return []
    min_x, max_x = min(x for x, _ in ring), max(x for x, _ in ring)
    min_y, max_y = min(y for _, y in ring), max(y for _, y in ring)
    span = min(max_x - min_x, max_y - min_y)
    min_run = max(9, .10 * span)
    nearby = [(a, b) for a, b in segments if dist(a, b) >= min_run
              and min(a[0], b[0]) <= max_x + 3 and max(a[0], b[0]) >= min_x - 3
              and min(a[1], b[1]) <= max_y + 3 and max(a[1], b[1]) >= min_y - 3]
    candidates = []
    for center in {p for segment in nearby for p in segment
                   if min_x < p[0] < max_x and min_y - 2 < p[1] < max_y + 2
                   and (p[1] - min_y < .25 * (max_y - min_y) or max_y - p[1] < .25 * (max_y - min_y))}:
        rays = []
        for a, b in nearby:
            origin, end = (a, b) if dist(a, center) <= dist(b, center) else (b, a)
            if dist(center, origin) > 3:
                continue
            direction = _delta(center, end)
            for along, index, across in sorted(_ray_hits(center, direction, ring)):
                run = along * dist(center, end)
                if run < min_run:
                    continue
                if along <= 1 + 5 / dist(center, end):
                    rays.append((run, index, across, direction))
                break
        chosen = []
        for ray in sorted(rays, reverse=True):
            direction = ray[3]
            if all(abs(_cross(direction, old[3])) / (dist((0, 0), direction) * dist((0, 0), old[3])) > .07
                   or direction[0] * old[3][0] + direction[1] * old[3][1] < 0 for old in chosen):
                chosen.append(ray)
        if len(chosen) != 3:
            continue
        # One depth/width edge runs down the cabinet. The two edges on its
        # cap point in opposite horizontal directions, rather than into a shelf.
        vertical = [ray for ray in chosen if abs(ray[3][0]) <= .2 * abs(ray[3][1])]
        if len(vertical) != 1 or vertical[0][0] < .60 * (max_y - min_y):
            continue
        sides = [ray for ray in chosen if ray not in vertical]
        if sides[0][3][0] * sides[1][3][0] >= 0:
            continue
        candidates.append((sum(ray[0] for ray in chosen), center, chosen))
    if not candidates:
        return []
    _, center, rays = max(candidates)
    return [(center, index, across) for _, index, across, _ in rays]


def _seam(a, b, c, d, tolerance):
    x, y = _delta(a, b)
    length = dist(a, b)
    other_length = dist(c, d)
    if min(length, other_length) < 6:
        return False
    u, v = _delta(c, d)
    if x * u + y * v >= 0 or abs(x * v - y * u) > .10 * length * other_length:
        return False
    if max(_line_distance(a, b, c), _line_distance(a, b, d)) > tolerance:
        return False
    positions = sorted(((p[0] - a[0]) * x / length + (p[1] - a[1]) * y / length for p in (c, d)))
    return min(length, positions[1]) - max(0, positions[0]) >= min(10, .45 * min(length, other_length))


def separate_seams(ring, neighboring_rings, offset):
    """Offset only contacting edges on the inside of each block."""
    others = [edge for other in neighboring_rings for edge in _edges(other)]
    shifted = []
    for a, b in _edges(ring):
        dx, dy = _delta(a, b)
        length = dist(a, b)
        amount = offset if length and any(_seam(a, b, c, d, 8) for c, d in others) else 0
        shifted.append(((a[0] - amount * dy / length, a[1] + amount * dx / length) if amount else a, (dx, dy)))
    path = []
    for vertex, (a, u), (b, v) in zip(ring, shifted[-1:] + shifted[:-1], shifted):
        determinant = _cross(u, v)
        if abs(determinant) <= 1e-6:
            path.append(b)
            continue
        step = _cross(_delta(a, b), v) / determinant
        intersection = (a[0] + step * u[0], a[1] + step * u[1])
        path.append(intersection if dist(vertex, intersection) <= 2.5 * offset else b)
    return path
