"""D-EU-109 a/b/c ring-cleanup unit tests (T02, PLAN_eu-dwelling-division-recovery-2026-09-07)."""
from __future__ import annotations

from scripts.run_eu_s2_campaign import (
    COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG,
    NEAR_DUPLICATE_VERTEX_TOLERANCE_M,
    _drop_redundant_ring_vertices,
)


def _shoelace(points):
    n = len(points)
    total = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def test_midpoint_vertex_on_square_edge_is_removed():
    ring = [(0.0, 0.0), (5.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    result = _drop_redundant_ring_vertices(ring)
    assert result == [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    assert len(result) == 4
    assert _shoelace(result) == _shoelace(ring)


def test_three_consecutive_collinear_points_all_removed_in_one_call():
    ring = [(0.0, 0.0), (2.0, 0.0), (4.0, 0.0), (6.0, 0.0), (6.0, 6.0), (0.0, 6.0)]
    result = _drop_redundant_ring_vertices(ring)
    assert result == [(0.0, 0.0), (6.0, 0.0), (6.0, 6.0), (0.0, 6.0)]
    assert _shoelace(result) == _shoelace(ring)


def test_vertex_over_chord_distance_budget_is_refused():
    base, bulge_height, width = 40.0, 0.015, 10.0
    ring = [(0.0, 0.0), (base / 2.0, bulge_height), (base, 0.0), (base, width), (0.0, width)]
    assert bulge_height > 0.010
    result = _drop_redundant_ring_vertices(ring)
    assert result == ring
    assert len(result) == 5


def test_vertex_over_per_removal_area_budget_is_refused():
    base, bulge_height, width = 20.0, 0.008, 3.0
    ring = [(0.0, 0.0), (base / 2.0, bulge_height), (base, 0.0), (base, width), (0.0, width)]
    without_bulge_vertex = [(0.0, 0.0), (base, 0.0), (base, width), (0.0, width)]
    relative_change_if_removed = abs(_shoelace(without_bulge_vertex) - _shoelace(ring)) / _shoelace(ring)
    assert bulge_height <= 0.010
    assert relative_change_if_removed > 1e-3
    result = _drop_redundant_ring_vertices(ring)
    assert result == ring
    assert len(result) == 5


def test_within_both_budgets_vertex_is_removed():
    base, bulge_height, width = 20.0, 0.008, 10.0
    ring = [(0.0, 0.0), (base / 2.0, bulge_height), (base, 0.0), (base, width), (0.0, width)]
    result = _drop_redundant_ring_vertices(ring)
    assert result == [(0.0, 0.0), (base, 0.0), (base, width), (0.0, width)]
    assert len(result) == 4


def test_cumulative_area_budget_refuses_later_removal_on_same_ring():
    n_bulges, b, h, gap, width = 10, 25.0, 0.0095, 100.0, 1.0
    ring = [(0.0, 0.0)]
    x = 0.0
    for _ in range(n_bulges):
        ring.append((x, 0.0))
        ring.append((x + b / 2.0, h))
        ring.append((x + b, 0.0))
        x += b + gap
    ring.append((x, 0.0))
    ring.append((x, width))
    ring.append((0.0, width))
    starting_area = _shoelace(ring)
    n_apex_before = sum(1 for p in ring if p[1] == h)
    result = _drop_redundant_ring_vertices(ring)
    final_area = _shoelace(result)
    n_apex_after = sum(1 for p in result if p[1] == h)
    assert 0 < n_apex_after < n_apex_before
    relative_change = abs(final_area - starting_area) / starting_area
    assert relative_change <= 2e-3 + 1e-9


def test_triangle_never_drops_below_three_vertices():
    ring = [(0.0, 0.0), (10.0, 0.0), (5.0, 0.0001)]
    result = _drop_redundant_ring_vertices(ring)
    assert result == ring
    assert len(result) == 3


def test_proximity_sub_case_adjacent_edge_removed():
    ring = [(0.0, 0.0), (0.004, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    assert 0.004 < NEAR_DUPLICATE_VERTEX_TOLERANCE_M
    result = _drop_redundant_ring_vertices(ring)
    assert result == [(0.004, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    assert len(result) == 4


def test_already_clean_ring_returned_byte_identical():
    ring = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    result = _drop_redundant_ring_vertices(ring)
    assert result == ring
    assert result is not ring


def test_closed_ring_closure_is_preserved():
    ring = [(0.0, 0.0), (5.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
    result = _drop_redundant_ring_vertices(ring)
    assert result == [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
    assert result[0] == result[-1]


def test_frozen_tolerances_unchanged():
    assert NEAR_DUPLICATE_VERTEX_TOLERANCE_M == 0.005
    assert COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG == 0.1
