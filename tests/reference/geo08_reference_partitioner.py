"""`GEO-08` independent reference partitioner — the comparison authority, not the implementation.

`D-EU-04-F` was ruled at option F4 on 2026-08-28: the arc is Python-only, no Rhino/Grasshopper
runtime will exist, and the cross-implementation check is re-based onto a second, independently
written Python partitioner.  This module is that second implementation.

**It must import nothing from `openubem`.**  A reference that called the implementation under test
would prove nothing, and `tests/test_eu_geo08_independent_parity.py` asserts that independence
directly.  Only the standard library is used here — no shapely, no numpy — so the geometry
primitives themselves are re-derived rather than shared:

* the long axis comes from a rotating-calipers sweep over convex-hull edge directions, choosing the
  orientation of minimum bounding-box area, where the implementation asks shapely for
  `minimum_rotated_rectangle`;
* the strips are cut by a hand-written Sutherland-Hodgman half-plane clip, where the implementation
  intersects with a shapely `box`;
* areas come from the shoelace formula and rotation from explicit trigonometry, where the
  implementation uses shapely `area` and `affinity.rotate`.

What this asserts is *independent-reimplementation agreement*.  It is **not** Grasshopper parity,
which remains NOT TESTED, and it must never be written as such.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

Point = tuple[float, float]
Ring = list[Point]

EPSILON = 1e-9


@dataclass(frozen=True)
class ReferenceLayout:
    """One reference partition, in the same terms the parity comparison speaks."""

    dwellings: tuple[Ring, ...]
    areas_m2: tuple[float, ...]
    facade_contact_m: tuple[float, ...]
    adjacency: tuple[tuple[int, int], ...]
    long_axis_degrees: float

    @property
    def zone_count(self) -> int:
        return len(self.dwellings)

    @property
    def total_area_m2(self) -> float:
        return sum(self.areas_m2)


def shoelace_area(ring: Ring) -> float:
    total = 0.0
    for index in range(len(ring)):
        x0, y0 = ring[index]
        x1, y1 = ring[(index + 1) % len(ring)]
        total += x0 * y1 - x1 * y0
    return abs(total) / 2.0


def convex_hull(points: list[Point]) -> Ring:
    """Monotone-chain hull, counter-clockwise, without repeating the first vertex."""
    ordered = sorted(set(points))
    if len(ordered) <= 2:
        return ordered

    def half(sequence: list[Point]) -> list[Point]:
        chain: list[Point] = []
        for point in sequence:
            while len(chain) >= 2 and _cross(chain[-2], chain[-1], point) <= 0.0:
                chain.pop()
            chain.append(point)
        return chain

    lower = half(ordered)
    upper = half(list(reversed(ordered)))
    return lower[:-1] + upper[:-1]


def _cross(origin: Point, first: Point, second: Point) -> float:
    return ((first[0] - origin[0]) * (second[1] - origin[1])
            - (first[1] - origin[1]) * (second[0] - origin[0]))


def long_axis_degrees(ring: Ring) -> float:
    """Rotating calipers: the minimum-area bounding box, then its longer side's direction."""
    hull = convex_hull(list(ring))
    if len(hull) < 3:
        raise ValueError("a long axis needs at least three distinct vertices")
    best: tuple[float, float] | None = None
    for index in range(len(hull)):
        x0, y0 = hull[index]
        x1, y1 = hull[(index + 1) % len(hull)]
        angle = math.atan2(y1 - y0, x1 - x0)
        rotated = _rotate_ring(hull, -angle, (0.0, 0.0))
        xs = [point[0] for point in rotated]
        ys = [point[1] for point in rotated]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        area = width * height
        if best is None or area < best[0] - EPSILON:
            best = (area, angle if width >= height else angle + math.pi / 2.0)
    assert best is not None
    return math.degrees(_normalise(best[1]))


def _normalise(angle: float) -> float:
    while angle <= -math.pi / 2.0:
        angle += math.pi
    while angle > math.pi / 2.0:
        angle -= math.pi
    return angle


def _rotate_ring(ring: Ring, angle: float, origin: Point) -> Ring:
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    ox, oy = origin
    return [
        (
            ox + (x - ox) * cos_a - (y - oy) * sin_a,
            oy + (x - ox) * sin_a + (y - oy) * cos_a,
        )
        for x, y in ring
    ]


def _centroid(ring: Ring) -> Point:
    area = 0.0
    cx = 0.0
    cy = 0.0
    for index in range(len(ring)):
        x0, y0 = ring[index]
        x1, y1 = ring[(index + 1) % len(ring)]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    area /= 2.0
    if abs(area) < EPSILON:
        raise ValueError("a degenerate ring has no centroid")
    return (cx / (6.0 * area), cy / (6.0 * area))


def _clip_half_plane(ring: Ring, keep_greater: bool, threshold: float) -> Ring:
    """Sutherland-Hodgman clip of a convex ring against a vertical line `x = threshold`."""
    def inside(point: Point) -> bool:
        return (point[0] >= threshold - EPSILON) if keep_greater else (point[0] <= threshold + EPSILON)

    output: Ring = []
    for index in range(len(ring)):
        current = ring[index]
        previous = ring[index - 1]
        current_in = inside(current)
        previous_in = inside(previous)
        if current_in != previous_in:
            span = current[0] - previous[0]
            if abs(span) > EPSILON:
                t = (threshold - previous[0]) / span
                output.append((threshold, previous[1] + t * (current[1] - previous[1])))
        if current_in:
            output.append(current)
    return _dedupe(output)


def _dedupe(ring: Ring) -> Ring:
    cleaned: Ring = []
    for point in ring:
        if not cleaned or math.dist(point, cleaned[-1]) > EPSILON:
            cleaned.append(point)
    if len(cleaned) > 1 and math.dist(cleaned[0], cleaned[-1]) <= EPSILON:
        cleaned.pop()
    return cleaned


def partition(ring: Ring, dwelling_count: int) -> ReferenceLayout:
    """Cut a convex footprint into equal-width strips across its long axis.

    The rule is the one §4.8 and §9.8 state: strips of equal width along the long axis of the
    minimum bounding box, ordered from one end.  Everything below is derived from that statement
    alone, without consulting the implementation under test.
    """
    if dwelling_count <= 0:
        raise ValueError("dwelling_count must be positive")
    source = _dedupe(list(ring))
    if len(source) < 3:
        raise ValueError("a footprint needs at least three distinct vertices")

    angle_deg = long_axis_degrees(source)
    angle = math.radians(angle_deg)
    origin = _centroid(source)
    aligned = _rotate_ring(source, -angle, origin)
    xs = [point[0] for point in aligned]
    min_x, max_x = min(xs), max(xs)
    strip_width = (max_x - min_x) / dwelling_count

    dwellings: list[Ring] = []
    facade: list[float] = []
    for index in range(dwelling_count):
        left = min_x + index * strip_width
        right = min_x + (index + 1) * strip_width
        clipped = _clip_half_plane(aligned, True, left)
        clipped = _clip_half_plane(clipped, False, right) if clipped else clipped
        if len(clipped) < 3:
            raise ValueError(f"strip {index} degenerated; the footprint is not partitionable")
        contact = 0.0
        for position in range(len(clipped)):
            x0, y0 = clipped[position]
            x1, y1 = clipped[(position + 1) % len(clipped)]
            on_left_cut = (
                index > 0
                and abs(x0 - left) <= EPSILON and abs(x1 - left) <= EPSILON
            )
            on_right_cut = (
                index < dwelling_count - 1
                and abs(x0 - right) <= EPSILON and abs(x1 - right) <= EPSILON
            )
            if not on_left_cut and not on_right_cut:
                contact += math.dist((x0, y0), (x1, y1))
        dwellings.append(_rotate_ring(clipped, angle, origin))
        facade.append(contact)

    adjacency = tuple((index, index + 1) for index in range(dwelling_count - 1))
    return ReferenceLayout(
        dwellings=tuple(dwellings),
        areas_m2=tuple(shoelace_area(polygon) for polygon in dwellings),
        facade_contact_m=tuple(facade),
        adjacency=adjacency,
        long_axis_degrees=angle_deg,
    )


def _clip_line(ring: Ring, a: float, b: float, c: float) -> Ring:
    """Sutherland-Hodgman clip of a ring against the half-plane `a*x + b*y <= c`."""
    def value(point: Point) -> float:
        return a * point[0] + b * point[1] - c

    output: Ring = []
    for index in range(len(ring)):
        current = ring[index]
        previous = ring[index - 1]
        current_v = value(current)
        previous_v = value(previous)
        if (current_v <= EPSILON) != (previous_v <= EPSILON):
            span = current_v - previous_v
            if abs(span) > EPSILON:
                t = -previous_v / span
                output.append((
                    previous[0] + t * (current[0] - previous[0]),
                    previous[1] + t * (current[1] - previous[1]),
                ))
        if current_v <= EPSILON:
            output.append(current)
    return _dedupe(output)


def convex_intersection_area(subject: Ring, clip: Ring) -> float:
    """Area shared by two convex rings, by successive half-plane clipping."""
    result = list(subject)
    ordered = clip if _signed_area(clip) > 0.0 else list(reversed(clip))
    for index in range(len(ordered)):
        x0, y0 = ordered[index]
        x1, y1 = ordered[(index + 1) % len(ordered)]
        a, b = y1 - y0, x0 - x1
        c = a * x0 + b * y0
        result = _clip_line(result, a, b, c)
        if len(result) < 3:
            return 0.0
    return shoelace_area(result)


def _signed_area(ring: Ring) -> float:
    total = 0.0
    for index in range(len(ring)):
        x0, y0 = ring[index]
        x1, y1 = ring[(index + 1) % len(ring)]
        total += x0 * y1 - x1 * y0
    return total / 2.0


@dataclass(frozen=True)
class ReferenceCore:
    """One reference circulation core, in the terms `GEO-08` compares."""

    ring: Ring
    area_m2: float
    shared_boundary_m: float
    overlap_m2: float
    thickness_m: float


def attach_external_core(ring: Ring, requested_area_m2: float) -> ReferenceCore:
    """Attach an unconditioned circulation core outside a rectangular conditioned plate.

    The ruled semantics (`D-EU-01`): the core is **additional** unconditioned area, never carved
    out of `A_C_Ref`.  It spans the full long side, so its area is controlled by outward thickness
    alone — `thickness = requested_area / long_side_length`.

    ⚪ Which of the two long sides receives the core is NOT compared by `GEO-08` and is not asserted
    here: it is a free choice of frame orientation, and the quantities the gate compares — area,
    shared boundary length, overlap — are identical on either side.
    """
    if not math.isfinite(requested_area_m2) or requested_area_m2 <= 0.0:
        raise ValueError("requested_area_m2 must be finite and positive")
    source = _dedupe(list(ring))
    if len(source) < 3:
        raise ValueError("a plate needs at least three distinct vertices")

    angle = math.radians(long_axis_degrees(source))
    origin = _centroid(source)
    aligned = _rotate_ring(source, -angle, origin)
    xs = [point[0] for point in aligned]
    ys = [point[1] for point in aligned]
    min_x, max_x, max_y = min(xs), max(xs), max(ys)
    long_length = max_x - min_x
    if long_length <= EPSILON:
        raise ValueError("the plate has no positive long-axis length")
    if abs(shoelace_area(source) - long_length * (max_y - min(ys))) > 1e-6 * shoelace_area(source):
        raise ValueError("NON_RECTANGULAR_CONDITIONED_PLATE_UNSUPPORTED")

    thickness = requested_area_m2 / long_length
    core_aligned: Ring = [
        (min_x, max_y),
        (max_x, max_y),
        (max_x, max_y + thickness),
        (min_x, max_y + thickness),
    ]
    core = _rotate_ring(core_aligned, angle, origin)
    return ReferenceCore(
        ring=core,
        area_m2=shoelace_area(core),
        shared_boundary_m=long_length,
        overlap_m2=convex_intersection_area(core, source),
        thickness_m=thickness,
    )
