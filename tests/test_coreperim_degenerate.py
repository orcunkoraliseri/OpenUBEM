"""T03 — unit test for core/perim degenerate-surface detection and reroute.

Tests:
  1. Many-edge footprint (52 vertices, 6924 m², 3 floors) → triggers sliver wedges
     after intersect_match → _rebuild_degenerate_coreperim fires → zero degenerate
     surfaces, zones follow _F{i}_whole naming, note="coreperim_degenerate_fallback".
  2. Clean rectangular core/perim footprint (4 vertices, 2000 m², 3 floors) → NO
     trigger → stays as core/perim (_core / _perimN zones), no false-positive.

T06 — interior-ring (courtyard) guard:
  3. Holed footprint (square with square hole, area ≥ 500 m², 3 floors, perimeter_core
     strategy) → build_zones reroutes to one_zone_per_floor (no core/perim donut built),
     IDF has _whole zones, zero degenerate surfaces.
  4. Clean no-hole rectangular footprint still builds as perimeter_core (no false trigger).

T09 — new pathology classes (Phase C fan-out failures):
  5. TestSliverInvertedReroute — way/381810546 (austin_urban, 675 m², 15 vertices): tiny
     perim zone (0.0645 m²) triggers _coreperim_has_tiny_zone_area → reroutes.
     Detector: area-tiny (_coreperim_has_tiny_zone_area).
  6. TestInterzoneMismatchReroute — way/427817502 (la_centre, 543 m², 16 vertices):
     interzone ceiling/floor vertex-count mismatch triggers reroute in builder.
     Detector: intersect_match-exception or interzone-mismatch (find_mismatched_interzone_pairs).
  7. TestThermalDivergenceReroute — way/427817541 (la_centre, 951 m², 19 vertices):
     thermal divergence from degenerate core/perim geometry → reroutes via tiny-area detector.
     Detector: area-tiny (_coreperim_has_tiny_zone_area).
  8. TestMultiPolygonCoercion — synthetic 2-part MultiPolygon → largest part extracted,
     dq flag set; no exception.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError
from shapely.geometry import MultiPolygon, Polygon

from openubem.config import ENERGYPLUS_IDD_PATH, FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M
from openubem.idf.surfaces import (
    _coreperim_has_degenerate_surfaces,
    _coreperim_has_tiny_zone_area,
    _distinct_vertices_after_collapse,
    _surface_3d_area,
    extrude_geometry,
)
from openubem.geometry.zoning import build_zones
from openubem.idf.builder import _coerce_to_polygon

try:
    IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass

_TEMPLATE = Path(__file__).parent.parent / "openubem" / "idf" / "templates" / "commercial_base.idf"

# Translated-to-origin coords for way/428643335 (52 vertices after dp-simplification,
# area ≈ 6924 m²).  This is the verified trigger for the sliver-wedge pathology.
_DEGENERATE_COORDS = [
    (-65.94336449465482, -26.038497619796544),
    (-65.71901596529642, 26.46238961769268),
    (-56.96906412875978, 26.417704266961664),
    (-55.67594857694348, 25.758001702837646),
    (-55.658818570838775, 27.831759284250438),
    (-51.210011317860335, 27.808481758926064),
    (-51.21903894544812, 25.6458950038068),
    (-49.917674065509345, 26.361344723030925),
    (-10.072496774315368, 26.132231707219034),
    (-8.826791358238552, 25.373321140185),
    (-8.818759758782107, 27.45828477293253),
    (-4.379323018190917, 27.42405760800466),
    (-4.387917227402795, 25.294738059863448),
    (-3.0574601128464565, 26.120732193347067),
    (38.670429878809955, 25.867903512436897),
    (40.12967389629921, 25.20610426319763),
    (40.14819129847456, 27.39075126964599),
    (44.67082925239811, 27.366581171751022),
    (44.66083771077683, 25.126372050493956),
    (45.90583491808502, 25.764915192034096),
    (66.9128977151704, 25.642314010299742),
    (66.79449039802421, 5.414251019246876),
    (64.81919594178908, 5.417152780573815),
    (64.79282157542184, -0.29425938334316015),
    (66.53696885256795, -0.32749821338802576),
    (66.46139942371519, -12.093846425414085),
    (64.63404771510977, -12.070641862228513),
    (64.52339094033232, -23.692364370450377),
    (62.586133146309294, -23.601219231728464),
    (62.48921806149883, -26.87176588131115),
    (47.777386382746045, -26.740386749617755),
    (46.44790388055844, -26.035874020773917),
    (46.43734126893105, -26.86754772765562),
    (42.339355157047976, -26.837682210374624),
    (42.35034064872889, -25.972741549368948),
    (41.5935574619798, -25.96312971971929),
    (41.076522628660314, -26.69964457862079),
    (-1.086069839366246, -26.49676672834903),
    (-1.8060080197756179, -25.766719262115657),
    (-2.4614124742220156, -25.769482743460685),
    (-2.4624685465241782, -26.579095810186118),
    (-6.532908942783251, -26.56064983922988),
    (-6.531148038280662, -25.695591845549643),
    (-7.92339801217895, -26.298985100816935),
    (-50.0306221282226, -26.096592194400728),
    (-50.70469322009012, -25.389305400662124),
    (-51.35086873313412, -25.392182795796543),
    (-51.35249279724667, -26.246151911560446),
    (-55.47830820904346, -26.22698097769171),
    (-55.475838044134434, -25.306477948091924),
    (-56.16801794094499, -25.297679466195405),
    (-56.80560226429952, -26.07702003698796),
]

_N_FLOORS_DEGEN = 3   # reduced from 17 for test speed; still triggers the pathology
_ARCH = "LargeOffice"


def _count_degenerate_surfaces(idf: IDF) -> int:
    count = 0
    for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        coords = list(surf.coords)
        if len(coords) < 3 or _distinct_vertices_after_collapse(coords) < 3:
            count += 1
    return count


class TestDegenCorePerimReroute:
    def _make_idf(self) -> IDF:
        return IDF(str(_TEMPLATE))

    def test_many_edge_footprint_zero_degenerate_after_fix(self):
        """Degenerate-trigger building produces ZERO degenerate surfaces with fix."""
        idf = self._make_idf()
        poly = Polygon(_DEGENERATE_COORDS)
        zones = build_zones("way/428643335", poly, _ARCH, _N_FLOORS_DEGEN, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        assert _count_degenerate_surfaces(idf) == 0, "degenerate surfaces remain after fix"

    def test_many_edge_footprint_zones_follow_whole_naming(self):
        """After reroute: all zones use _F{i}_whole naming (one_zone_per_floor)."""
        idf = self._make_idf()
        poly = Polygon(_DEGENERATE_COORDS)
        zones = build_zones("way/428643335", poly, _ARCH, _N_FLOORS_DEGEN, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
        assert len(zone_names) == _N_FLOORS_DEGEN
        for i in range(_N_FLOORS_DEGEN):
            expected = f"way/428643335_F{i}_whole"
            assert expected in zone_names, f"expected zone {expected!r}, got {zone_names}"

    def test_many_edge_footprint_fallback_note_set(self):
        """After reroute: zone dict carries coreperim_degenerate_fallback note."""
        idf = self._make_idf()
        poly = Polygon(_DEGENERATE_COORDS)
        zones = build_zones("way/428643335", poly, _ARCH, _N_FLOORS_DEGEN, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        notes = {z.get("generation_status_note") for z in zones if z.get("extruded")}
        assert "coreperim_degenerate_fallback" in notes

    def test_no_core_perim_zones_remain_after_reroute(self):
        """After reroute: no _core or _perim zone names survive in the IDF."""
        idf = self._make_idf()
        poly = Polygon(_DEGENERATE_COORDS)
        zones = build_zones("way/428643335", poly, _ARCH, _N_FLOORS_DEGEN, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
        has_cp = any("_core" in n or "_perim" in n for n in zone_names)
        assert not has_cp, f"core/perim zone names still present: {zone_names}"


class TestCleanRectNoFalseTrigger:
    """A clean rectangular 2000 m² footprint must stay as perimeter_core."""

    def _make_idf(self) -> IDF:
        return IDF(str(_TEMPLATE))

    def _rect_poly(self) -> Polygon:
        # 50 m × 40 m = 2000 m²
        return Polygon([(0, 0), (50, 0), (50, 40), (0, 40)])

    def test_rect_stays_core_perim_has_core_zones(self):
        """Rectangular 2000 m² building keeps _core zones (no false trigger)."""
        idf = self._make_idf()
        poly = self._rect_poly()
        zones = build_zones("rect/1", poly, "MediumOffice", 3, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
        has_core = any("_core" in n for n in zone_names)
        assert has_core, f"expected _core zones for healthy rect building; got {zone_names}"

    def test_rect_zero_degenerate(self):
        """Rectangular building has zero degenerate surfaces."""
        idf = self._make_idf()
        poly = self._rect_poly()
        zones = build_zones("rect/1", poly, "MediumOffice", 3, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        assert _count_degenerate_surfaces(idf) == 0

    def test_rect_no_fallback_note(self):
        """Rectangular building must NOT carry coreperim_degenerate_fallback note."""
        idf = self._make_idf()
        poly = self._rect_poly()
        zones = build_zones("rect/1", poly, "MediumOffice", 3, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        notes = {z.get("generation_status_note") for z in zones if z.get("extruded")}
        assert "coreperim_degenerate_fallback" not in notes


class TestCourtyardInteriorRingGuard:
    """T06 — footprints with interior rings must NOT enter geomeppy core/perim."""

    def _make_idf(self) -> IDF:
        return IDF(str(_TEMPLATE))

    def _holed_poly(self) -> Polygon:
        # 40 m × 30 m outer shell (1200 m²) with a 4 m × 4 m interior hole → area 1184 m²
        outer = [(0, 0), (40, 0), (40, 30), (0, 30)]
        inner = [(18, 13), (22, 13), (22, 17), (18, 17)]
        return Polygon(outer, [inner])

    def _no_hole_poly(self) -> Polygon:
        # Same outer shell but no hole — should still build as core/perim
        return Polygon([(0, 0), (40, 0), (40, 30), (0, 30)])

    def test_holed_poly_does_not_build_coreperim_donut(self):
        """Holed footprint routed to one_zone_per_floor — no core/perim zones in IDF."""
        idf = self._make_idf()
        poly = self._holed_poly()
        zones = build_zones("courtyard/1", poly, "MediumOffice", 3, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
        has_cp = any("_core" in n or "_perim" in n for n in zone_names)
        assert not has_cp, f"core/perim zones present for holed footprint: {zone_names}"

    def test_holed_poly_whole_zone_naming(self):
        """Holed footprint produces _F{i}_whole zones (one_zone_per_floor)."""
        idf = self._make_idf()
        poly = self._holed_poly()
        zones = build_zones("courtyard/1", poly, "MediumOffice", 3, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
        assert len(zone_names) == 3
        for i in range(3):
            assert f"courtyard/1_F{i}_whole" in zone_names, (
                f"expected courtyard/1_F{i}_whole, got {zone_names}"
            )

    def test_holed_poly_zero_degenerate_surfaces(self):
        """Holed footprint IDF has zero degenerate surfaces."""
        idf = self._make_idf()
        poly = self._holed_poly()
        zones = build_zones("courtyard/1", poly, "MediumOffice", 3, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        assert _count_degenerate_surfaces(idf) == 0

    def test_no_hole_rect_still_builds_coreperim(self):
        """No-hole 40×30 m footprint stays as core/perim — interior-ring guard is targeted."""
        idf = self._make_idf()
        poly = self._no_hole_poly()
        zones = build_zones("noholetest/1", poly, "MediumOffice", 3, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
        has_core = any("_core" in n for n in zone_names)
        assert has_core, f"expected _core zones for healthy no-hole rect building; got {zone_names}"


# ---------------------------------------------------------------------------
# T09 — Phase C fan-out pathology classes
# ---------------------------------------------------------------------------

# Translated-to-origin coords for way/381810546 (austin_urban, 675 m², 15 vertices).
# Detector: area-tiny — a sliver perimeter zone (0.0645 m²) triggers
# _coreperim_has_tiny_zone_area(min_area=0.5) → reroute to one_zone_per_floor.
_SLIVER_COORDS = [
    (11.954981, -11.094686),
    (5.472817, -7.619913),
    (3.210601, -11.746174),
    (0.017600, -10.008250),
    (-3.562499, -16.698498),
    (-18.945607, -8.445751),
    (-10.559980, 7.165172),
    (-6.012120, 4.666436),
    (1.713922, 19.050789),
    (5.777284, 16.879189),
    (6.909005, 18.886906),
    (13.682099, 15.193691),
    (7.746113, 4.154454),
    (17.710983, -1.165853),
    (12.245926, -11.313130),
]

# Translated-to-origin coords for way/427817502 (la_centre, 543 m², 16 vertices).
# Detector: intersect_match-exception or interzone-mismatch (find_mismatched_interzone_pairs).
# A non-convex parallelogram-like footprint whose core/perim decomposition yields
# ceiling/floor vertex-count mismatches detected by find_mismatched_interzone_pairs.
_INTERZONE_MISMATCH_COORDS = [
    (-19.433282, 6.243540),
    (-18.588458, 7.397801),
    (-20.747943, 8.976649),
    (-14.900274, 16.935285),
    (-12.777442, 15.379064),
    (-11.979577, 16.467353),
    (-6.837291, 12.689705),
    (-6.996756, 12.480918),
    (6.582040, 2.523431),
    (7.267260, 3.457819),
    (20.242003, -6.070887),
    (17.425937, -9.918436),
    (19.374214, -11.405991),
    (17.128306, -14.672653),
    (15.106053, -13.195292),
    (12.290117, -17.031750),
]

# Translated-to-origin coords for way/427817541 (la_centre, 951 m², 19 vertices).
# Detector: area-tiny — the same class as way/381810546; a narrow protrusion in the
# footprint creates a degenerate core/perim zone below the 0.5 m² threshold.
_THERMAL_DIV_COORDS = [
    (-16.384532, -6.963182),
    (-14.999496, -5.416215),
    (-21.232289, -0.205745),
    (0.237895, 25.474633),
    (1.270695, 24.619235),
    (2.151511, 25.695427),
    (3.933126, 24.165522),
    (3.061406, 23.078130),
    (9.632220, 17.575226),
    (2.578609, 9.143227),
    (11.991683, 1.265776),
    (13.226744, 2.626027),
    (18.025186, -1.347079),
    (16.853796, -2.785736),
    (20.437654, -5.668341),
    (6.065238, -23.083661),
    (-13.316049, -6.667670),
    (-14.572668, -8.282738),
    (-15.230794, -7.742415),
]

_N_FLOORS_T09 = 3  # reduced for test speed; sufficient to trigger the pathology
_ARCH_T09 = "MediumOffice"


class TestSliverInvertedReroute:
    """way/381810546 (austin_urban): tiny perim zone triggers area-tiny detector → reroutes."""

    def _make_idf(self) -> IDF:
        return IDF(str(_TEMPLATE))

    def test_sliver_reroutes_to_whole_zones(self):
        """Sliver building reroutes: IDF has only _F{i}_whole zones (one_zone_per_floor)."""
        idf = self._make_idf()
        poly = Polygon(_SLIVER_COORDS)
        # perimeter_core requested; detector fires → one_zone_per_floor fallback.
        zones = build_zones("way/381810546", poly, _ARCH_T09, _N_FLOORS_T09, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
        assert len(zone_names) == _N_FLOORS_T09
        for i in range(_N_FLOORS_T09):
            assert f"way/381810546_F{i}_whole" in zone_names, (
                f"expected _F{i}_whole zone; got {zone_names}"
            )

    def test_sliver_zero_tiny_zone_area(self):
        """After reroute: no tiny zone areas remain (area-tiny detector is clean)."""
        idf = self._make_idf()
        poly = Polygon(_SLIVER_COORDS)
        zones = build_zones("way/381810546", poly, _ARCH_T09, _N_FLOORS_T09, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        assert not _coreperim_has_tiny_zone_area(idf), "tiny zone areas still present after reroute"

    def test_sliver_zero_degenerate_surfaces(self):
        """After reroute: zero degenerate surfaces."""
        idf = self._make_idf()
        poly = Polygon(_SLIVER_COORDS)
        zones = build_zones("way/381810546", poly, _ARCH_T09, _N_FLOORS_T09, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        assert _count_degenerate_surfaces(idf) == 0


class TestInterzoneMismatchReroute:
    """way/427817502 (la_centre): non-convex footprint → reroutes to one_zone_per_floor.

    Detector: degenerate/tiny surface post-intersect (_coreperim_has_tiny_zone_area or
    _coreperim_has_degenerate_surfaces fires inside extrude_geometry after intersect_match,
    because the non-convex footprint creates degenerate core/perim zones).  In the full
    builder.py path, find_mismatched_interzone_pairs (T05) also covers this class.
    Either way: the IDF must have _whole zones, no core/perim zones remain.
    """

    def _make_idf(self) -> IDF:
        return IDF(str(_TEMPLATE))

    def test_interzone_reroutes_to_whole_zones(self):
        """Interzone-mismatch building reroutes: IDF has only _F{i}_whole zones."""
        idf = self._make_idf()
        poly = Polygon(_INTERZONE_MISMATCH_COORDS)
        zones = build_zones("way/427817502", poly, _ARCH_T09, _N_FLOORS_T09, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
        # After any reroute path fires, only _whole zones remain.
        has_cp = any("_core" in n or "_perim" in n for n in zone_names)
        assert not has_cp, f"core/perim zones still present after reroute: {zone_names}"
        for i in range(_N_FLOORS_T09):
            assert f"way/427817502_F{i}_whole" in zone_names, (
                f"expected _F{i}_whole zone; got {zone_names}"
            )

    def test_interzone_zero_degenerate_surfaces(self):
        """After reroute: zero degenerate surfaces."""
        idf = self._make_idf()
        poly = Polygon(_INTERZONE_MISMATCH_COORDS)
        zones = build_zones("way/427817502", poly, _ARCH_T09, _N_FLOORS_T09, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        assert _count_degenerate_surfaces(idf) == 0


class TestThermalDivergenceReroute:
    """way/427817541 (la_centre): thermal divergence from degenerate core/perim → reroutes.

    Detector: area-tiny (_coreperim_has_tiny_zone_area) — same class as way/381810546.
    A narrow protrusion creates a degenerate zone below 0.5 m².
    """

    def _make_idf(self) -> IDF:
        return IDF(str(_TEMPLATE))

    def test_thermal_div_reroutes_to_whole_zones(self):
        """Thermal-divergence building reroutes: IDF has only _F{i}_whole zones."""
        idf = self._make_idf()
        poly = Polygon(_THERMAL_DIV_COORDS)
        zones = build_zones("way/427817541", poly, _ARCH_T09, _N_FLOORS_T09, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
        assert len(zone_names) == _N_FLOORS_T09
        for i in range(_N_FLOORS_T09):
            assert f"way/427817541_F{i}_whole" in zone_names, (
                f"expected _F{i}_whole zone; got {zone_names}"
            )

    def test_thermal_div_zero_degenerate_surfaces(self):
        """After reroute: zero degenerate surfaces."""
        idf = self._make_idf()
        poly = Polygon(_THERMAL_DIV_COORDS)
        zones = build_zones("way/427817541", poly, _ARCH_T09, _N_FLOORS_T09, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        assert _count_degenerate_surfaces(idf) == 0


class TestMultiPolygonCoercion:
    """Synthetic 2-part MultiPolygon → coerced to largest part; dq flag set; no exception."""

    def test_largest_part_selected(self):
        """_coerce_to_polygon takes the larger polygon from a 2-part MultiPolygon."""
        small = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])   # area 25
        large = Polygon([(10, 10), (50, 10), (50, 50), (10, 50)])  # area 1600
        mp = MultiPolygon([small, large])
        result_geom, result_dq = _coerce_to_polygon(mp, "")
        assert result_geom.geom_type == "Polygon", "result must be a Polygon"
        assert abs(result_geom.area - large.area) < 1e-6, (
            f"expected large polygon (area={large.area}), got area={result_geom.area}"
        )

    def test_dq_flag_set_on_coercion(self):
        """dq flag records the coercion when a MultiPolygon is coerced."""
        small = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
        large = Polygon([(10, 10), (50, 10), (50, 50), (10, 50)])
        mp = MultiPolygon([small, large])
        _, dq = _coerce_to_polygon(mp, "existing_flag")
        assert "multipolygon_coerced_to_largest_part" in dq, (
            f"expected coercion flag in dq, got: {dq!r}"
        )

    def test_polygon_passthrough(self):
        """A plain Polygon passes through _coerce_to_polygon unchanged."""
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        result_geom, result_dq = _coerce_to_polygon(poly, "")
        assert result_geom is poly
        assert result_dq == ""
