from __future__ import annotations

import math

from shapely.geometry import Polygon, box

import openubem.geometry.european_nocore as nc


def _jittery_square(side=20.0, per_side=15, jitter=0.01):
    pts = []
    for s in range(4):
        for n in range(per_side):
            t = side * n / per_side
            off = jitter if n % 2 else -jitter
            if n == 0:
                off = 0.0
            if s == 0:
                pts.append((t, off))
            elif s == 1:
                pts.append((side - off, t))
            elif s == 2:
                pts.append((side - t, side - off))
            else:
                pts.append((off, side - t))
    return Polygon(pts)


def test_shape_pass_slides_thin_flat_to_pass_c11():
    poly = box(0, 0, 30, 8)
    flats = [box(0, 0, 26, 8), box(26, 0, 30, 8)]
    base = nc._score_cut(poly, flats, 2)
    assert not base["checks"]["C11"]["pass"]
    out, rec = nc._shape_pass(poly, flats, 2, base)
    assert rec["checks"]["C11"]["pass"]
    assert nc._strictly_better(base, rec)
    assert abs(sum(f.area for f in out) - poly.area) < 1e-6


def test_simplify_pass_reduces_points_and_keeps_coverage():
    poly = _jittery_square()
    assert len(poly.exterior.coords) - 1 == 60
    flats = [poly]
    base = nc._score_cut(poly, flats, 1)
    assert not base["checks"]["C5"]["pass"]
    out, rec = nc._simplify_pass(poly, flats, 1, base)
    assert rec["checks"]["C5"]["pass"]
    assert rec["checks"]["C1"]["pass"]
    assert max(len(f.exterior.coords) - 1 for f in out) <= 40


def test_clean_cut_comes_back_as_the_same_objects():
    poly = box(0, 0, 20, 10)
    flats = [box(0, 0, 10, 10), box(10, 0, 20, 10)]
    rec = nc._score_cut(poly, flats, 2)
    assert rec["verdict"] == "PASS"
    checks, verdict = rec["checks"], rec["verdict"]
    result = nc.improve_cut_nocore(poly, flats, checks, verdict, 2)
    assert result[0] is poly and result[1] is flats and result[2] is checks and result[3] is verdict
    same_flats, same_base = nc._shape_pass(poly, flats, 2, rec)
    assert same_flats is flats and same_base is rec
    same_flats, same_base = nc._simplify_pass(poly, flats, 2, rec)
    assert same_flats is flats and same_base is rec
    same_flats, same_base = nc._wide_search_pass(poly, flats, 2, rec)
    assert same_flats is flats and same_base is rec


def test_wide_search_restores_theta_cap():
    poly = box(0, 0, 30, 8)
    flats = [box(0, 0, 26, 8), box(26, 0, 30, 8)]
    base = nc._score_cut(poly, flats, 2)
    before = nc.MAX_THETA_OFFSETS
    nc._wide_search_pass(poly, flats, 2, base)
    assert nc.MAX_THETA_OFFSETS == before
    assert math.isclose(nc.WIDE_THETA_OFFSETS, 24)
