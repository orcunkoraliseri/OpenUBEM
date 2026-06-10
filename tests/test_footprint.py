"""Tests for openubem.geometry.footprint (T05)."""
import math

import numpy as np
import pandas as pd
import pytest
import shapely
from shapely.geometry import Point, Polygon

from openubem.geometry.footprint import (
    _append_flag,
    _n_exterior_verts,
    compute_form_factor,
    derive_num_floors,
    simplify_footprint,
    translate_to_origin,
    validate_simplified,
)


class TestFootprint:
    def test_n_exterior_verts_square(self):
        sq = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        assert _n_exterior_verts(sq) == 4

    def test_simplify_dp05_50_vertex_poly(self):
        angles = np.linspace(0, 2 * math.pi, 51)[:-1]
        coords = [(10 * math.cos(a), 10 * math.sin(a)) for a in angles]
        poly = Polygon(coords)
        result_poly, flag, status = simplify_footprint(poly, "")
        assert status == "dp_05"
        assert _n_exterior_verts(result_poly) <= 120

    def test_simplify_dp15_path(self):
        # Polygon with 500 vertices on a large circle perturbed by 0.8 m (> DP_TOLERANCE 0.5, < DP_COARSE 1.5).
        # DP 0.5 cannot remove those bumps so output > 120 verts; DP 1.5 removes them → ≤ 120 verts.
        n = 500
        angles = np.linspace(0, 2 * math.pi, n + 1)[:-1]
        coords = [
            (50 * math.cos(a) + 0.8 * math.sin(20 * a), 50 * math.sin(a) + 0.8 * math.cos(20 * a))
            for a in angles
        ]
        poly = Polygon(coords)
        # Verify our fixture actually triggers the dp_15 path
        import shapely as _shp
        from openubem.config import DP_TOLERANCE_M, MAX_VERTICES
        t1 = _shp.simplify(poly, tolerance=DP_TOLERANCE_M, preserve_topology=True)
        if _n_exterior_verts(t1) <= MAX_VERTICES:
            pytest.skip("Fixture polygon is too simple — DP 0.5 already reduces below MAX_VERTICES on this shapely version")
        result_poly, flag, status = simplify_footprint(poly, "")
        assert status == "dp_15"
        assert "idf_dp_coarse" in flag
        assert _n_exterior_verts(result_poly) <= 120

    def test_simplify_bbox_path(self, monkeypatch):
        # The bbox path is the 4th tier: shapely's convex_hull of any reasonable polygon
        # typically has far fewer than 120 verts, so we cannot reach Tier 4 with geometry alone.
        # Monkeypatch the Polygon class to force convex_hull to return a high-vertex polygon
        # so Tier 3 also exceeds MAX_VERTICES, exercising Tier 4 (minimum_rotated_rectangle).
        import shapely.geometry
        from openubem.geometry import footprint as fp_module

        n = 500
        angles = np.linspace(0, 2 * math.pi, n + 1)[:-1]
        # Use a large circle with 0.8 m bumps to exceed DP 0.5 → same as dp_15 fixture
        coords = [
            (50 * math.cos(a) + 0.8 * math.sin(20 * a), 50 * math.sin(a) + 0.8 * math.cos(20 * a))
            for a in angles
        ]
        poly = Polygon(coords)
        import shapely as _shp
        from openubem.config import DP_TOLERANCE_M, MAX_VERTICES
        t1 = _shp.simplify(poly, tolerance=DP_TOLERANCE_M, preserve_topology=True)
        if _n_exterior_verts(t1) <= MAX_VERTICES:
            pytest.skip("Fixture polygon is too simple for bbox monkeypatch test")

        # Monkeypatch convex_hull on this specific polygon instance to return a > MAX_VERTICES polygon
        fat_ring_coords = [(100 * math.cos(a), 100 * math.sin(a)) for a in np.linspace(0, 2*math.pi, 200+1)[:-1]]
        fat_poly = Polygon(fat_ring_coords)

        original_convex_hull = poly.__class__.convex_hull.fget

        class _PatchedPoly(Polygon):
            @property
            def convex_hull(self):
                return fat_poly

        patched = _PatchedPoly(coords)

        result_poly, flag, status = simplify_footprint(patched, "")
        # If shapely's convex_hull on fat_poly still <= 120, test gracefully falls to hull path
        hull_verts = _n_exterior_verts(fat_poly.convex_hull)
        if hull_verts <= MAX_VERTICES:
            assert status in ("hull", "bbox")
        else:
            assert status == "bbox"
            assert "idf_bbox_simplification" in flag

    def test_validate_simplified_small_area(self):
        tiny = Polygon([(0, 0), (1, 0), (1, 0.1), (0, 0.1)])
        result = validate_simplified(tiny)
        assert result == "skipped_invalid_geometry"

    def test_validate_simplified_valid_large(self):
        big = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        assert validate_simplified(big) is None

    def test_derive_num_floors_levels_observed(self):
        row = pd.Series({"levels": 3, "height_m": float("nan")})
        assert derive_num_floors(row) == 3

    def test_derive_num_floors_height_fallback(self):
        row = pd.Series({"levels": float("nan"), "height_m": 10.5})
        assert derive_num_floors(row) == 3

    def test_derive_num_floors_both_nan(self):
        row = pd.Series({"levels": float("nan"), "height_m": float("nan")})
        assert derive_num_floors(row) == 1

    def test_derive_num_floors_levels_zero_clamp(self):
        row = pd.Series({"levels": 0, "height_m": float("nan")})
        assert derive_num_floors(row) == 1

    def test_derive_num_floors_levels_42(self):
        row = pd.Series({"levels": 42, "height_m": float("nan")})
        assert derive_num_floors(row) == 42

    def test_translate_to_origin_centroid(self):
        sq = Polygon([(10, 10), (20, 10), (20, 20), (10, 20)])
        local, cx, cy = translate_to_origin(sq)
        assert abs(cx - 15.0) < 1e-9
        assert abs(cy - 15.0) < 1e-9
        lx, ly = local.centroid.coords[0]
        assert abs(lx) < 1e-9
        assert abs(ly) < 1e-9

    def test_append_flag_empty(self):
        assert _append_flag("", "foo") == "foo"

    def test_append_flag_add_new(self):
        assert _append_flag("foo", "bar") == "foo,bar"

    def test_append_flag_idempotent(self):
        result = _append_flag("foo,bar", "bar")
        assert result == "foo,bar"

    def test_append_flag_nan(self):
        assert _append_flag(float("nan"), "foo") == "foo"


    def test_simplify_hull_path_direct(self, monkeypatch):
        """Monkeypatch shapely.simplify to force Tier 3 (hull) of the §3A 4-tier fallback chain."""
        import openubem.geometry.footprint as fp_module
        from openubem.config import MAX_VERTICES

        base = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        fat_angles = np.linspace(0, 2 * math.pi, 201)[:-1]
        fat_poly = Polygon([(100 * math.cos(a), 100 * math.sin(a)) for a in fat_angles])
        assert _n_exterior_verts(fat_poly) > MAX_VERTICES

        monkeypatch.setattr(fp_module.shapely, "simplify", lambda *args, **_: fat_poly)

        result_poly, flag, status = simplify_footprint(base, "")
        assert status == "hull"
        assert "idf_hull_simplification" in flag
        assert result_poly.equals(base.convex_hull)
        assert _n_exterior_verts(result_poly) <= MAX_VERTICES

    def test_simplify_bbox_path_direct(self, monkeypatch):
        """Force Tier 4 (bbox) by patching _n_exterior_verts inside the footprint module.
        Shapely 2's convex_hull is a C-level property that Python subclassing cannot override,
        so we patch the vertex-count gate directly — all tiers see >MAX_VERTICES and fall through."""
        import openubem.geometry.footprint as fp_module
        from openubem.config import MAX_VERTICES

        base = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])

        # Replace the vertex-counter used inside simplify_footprint; test-local import is unaffected.
        monkeypatch.setattr(fp_module, "_n_exterior_verts", lambda poly: MAX_VERTICES + 1)

        result_poly, flag, status = simplify_footprint(base, "")
        assert status == "bbox"
        assert "idf_bbox_simplification" in flag
        assert _n_exterior_verts(result_poly) <= MAX_VERTICES


class TestFormFactor:
    def test_form_factor_fixture(self):
        # 100 m^2 footprint, 40 m perimeter, 4 floors, 3.5 m/floor
        floor_area, envelope, ff = compute_form_factor(100.0, 40.0, 4, 3.5)
        assert floor_area == 400.0
        # (40 * 4 * 3.5) + (2 * 100) = 560 + 200 = 760
        assert abs(envelope - 760.0) < 1e-6
        assert abs(ff - 1.9) < 1e-6

    def test_form_factor_single_floor(self):
        floor_area, envelope, ff = compute_form_factor(50.0, 28.0, 1, 3.5)
        assert floor_area == 50.0
        assert abs(envelope - (28.0 * 1 * 3.5 + 2 * 50.0)) < 1e-6

    def test_form_factor_ratio_always_positive(self):
        _, _, ff = compute_form_factor(200.0, 60.0, 3, 3.5)
        assert ff > 0
