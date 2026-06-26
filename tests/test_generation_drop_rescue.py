"""T03 — generation-drop rescue tests (PLAN_geometry_generation_drops.md).

Covers the CP-1 ruling fix-set:
  1. Regression — the 3 already-rescued real la_urban footprints (way/388772955,
     relation/6356830, way/427270590) extrude to a valid one_zone/core-perim IDF at HEAD
     (no exception, zones produced, zero degenerate surfaces, zero interzone mismatches).
  2. Complexity gate — the high-M hang building (way/427274629, M=97×15=1455 > T=800) routes
     directly to one_zone_per_floor WITHOUT building core/perim zones, fast (no intersect_match
     hang). A clean low-M core/perim building stays core/perim (no false trigger).
  3. Genuinely-unbuildable footprint still drops cleanly (run_step3 records a failed row, never
     fabricates an IDF — rule 4).
  4. Serial-path isolation — a raising building in the n_jobs=1 loop is recorded as
     failed_worker_exception and the loop continues (no whole-run crash).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError
from shapely.geometry import Polygon

from openubem.config import ENERGYPLUS_IDD_PATH, FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M
from openubem.geometry.zoning import build_zones
from openubem.idf.surfaces import (
    COREPERIM_COMPLEXITY_THRESHOLD,
    extrude_geometry,
    find_mismatched_interzone_pairs,
    _distinct_vertices_after_collapse,
    _is_coreperim_zone,
)
from openubem.idf import builder as builder_mod
from openubem.idf.builder import run_step3, BuildingIDF

try:
    IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass

_TEMPLATE = Path(__file__).parent.parent / "openubem" / "idf" / "templates" / "commercial_base.idf"


def _make_idf() -> IDF:
    return IDF(str(_TEMPLATE))


def _count_degenerate_surfaces(idf: IDF) -> int:
    count = 0
    for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        coords = list(surf.coords)
        if len(coords) < 3 or _distinct_vertices_after_collapse(coords) < 3:
            count += 1
    return count


# ── Real la_urban footprints (translated-to-origin, dp_05-simplified) ────────────
# Extracted from runtime/ubem_validation/cases/la_urban/01_buildings.gpkg.

# way/388772955 (LargeOffice, 22 verts, 4 floors, M=88) — rescued by the T03 intersect_match
# exception handler (NotImplementedError → one_zone_per_floor).
_B1_COORDS = [
    (-28.099088, -24.510846), (-32.252487, -24.479886), (-32.005716, 22.220373),
    (-27.649156, 22.197903), (-27.631299, 25.757826), (-30.824850, 25.776505),
    (-30.805432, 29.458407), (31.921576, 29.132922), (31.636759, -24.897864),
    (26.984845, -24.871646), (26.964435, -27.189364), (29.834983, -27.203892),
    (29.843055, -25.850917), (30.996840, -25.854581), (30.982540, -28.416375),
    (27.133560, -28.400425), (27.129034, -29.476176), (-5.434525, -29.303672),
    (-5.459189, -32.674963), (-9.031297, -32.662540), (-9.015718, -29.280041),
    (-28.121902, -29.179786),
]
_B1_N_FLOORS = 4

# relation/6356830 (Courthouse, 38 verts, 14 floors, M=532) — rescued by the courtyard /
# degenerate reroute chain.
_B3_COORDS = [
    (17.857492, -30.012406), (8.520030, -29.716284), (8.761629, -21.600906),
    (7.045465, -21.545822), (6.236898, -24.884960), (4.943428, -26.432319),
    (1.017588, -28.112583), (-3.251122, -26.993610), (-5.645424, -23.647034),
    (-5.959692, -21.502519), (-12.905369, -21.846770), (-12.736237, -25.242698),
    (-10.160651, -25.219984), (-10.324754, -30.142204), (-18.564111, -29.871104),
    (-17.599105, -21.487652), (-17.918792, -19.043617), (-19.145962, -19.005835),
    (-18.831854, -0.832042), (-17.530714, -0.859673), (-17.192642, 19.199248),
    (-19.084430, 19.234388), (-18.823108, 33.981802), (9.021916, 33.738766),
    (9.007399, 32.596601), (10.557856, 32.576895), (10.538829, 31.079882),
    (9.052834, 31.087677), (9.010266, 26.285911), (12.286671, 26.255361),
    (12.273492, 24.492094), (9.080146, 24.521590), (9.016364, 17.324485),
    (18.605779, 17.246975), (18.466180, 1.178213), (20.782362, 1.126596),
    (20.467122, -22.226573), (18.084922, -22.285025),
]
_B3_N_FLOORS = 14

# way/427270590 (RetailStandalone, no_floors, 41 verts, 6 floors, M=246) — rescued by the
# degenerate-coreperim reroute.
_B4_COORDS = [
    (-39.366175, -32.153260), (-42.858874, -25.898065), (-45.221884, -25.901325),
    (-45.211704, -18.559361), (-46.033072, -18.548928), (-45.670644, 19.432374),
    (-44.719935, 19.431390), (-45.253878, 21.722871), (-46.098207, 21.378691),
    (-46.778335, 24.514928), (-45.337882, 28.189861), (-40.862630, 30.983348),
    (-40.860591, 31.870584), (-30.570055, 31.773160), (-30.552451, 33.159284),
    (-26.270147, 33.115990), (-26.287750, 31.729866), (-4.402256, 32.494487),
    (1.227467, 30.981205), (4.136039, 28.881393), (4.471563, 31.317103),
    (18.460877, 31.017501), (18.483901, 32.104105), (23.734526, 31.993087),
    (23.711642, 30.917573), (26.627521, 30.847286), (26.670049, 32.743268),
    (30.684155, 32.659041), (30.661413, 31.594616), (37.084095, 31.468728),
    (37.106132, 32.477708), (45.613336, 31.504651), (45.595662, 30.839429),
    (42.919451, 30.884487), (42.879037, 29.154839), (45.508101, 25.394971),
    (46.018119, 22.671259), (46.627220, 22.663529), (46.069528, -15.459464),
    (42.830203, -15.418351), (42.621140, -32.617483),
]
_B4_N_FLOORS = 6

# way/427274629 (LargeOffice, no_floors, 97 verts, 15 floors, M=1455 > T=800) — THE HANG.
# Must route through the complexity gate to one_zone_per_floor without building core/perim.
_HANG_COORDS = [
    (-12.216279, -36.317971), (-10.860036, -34.194731), (-10.038516, -34.194109),
    (-10.024572, -32.375396), (-10.827492, -32.365165), (-13.529908, -27.129147),
    (-13.557771, -24.245186), (-9.869667, -23.116559), (-9.900127, -21.885093),
    (-13.591568, -21.826962), (-11.700365, -16.838024), (-9.817659, -16.862015),
    (-9.787755, -15.964042), (-11.660755, -14.454008), (-11.567175, -10.007793),
    (-9.766683, -9.964191), (-9.744454, -8.944122), (-11.636105, -8.897835),
    (-9.738943, -8.511651), (-11.967066, -6.620005), (-13.342461, -6.624660),
    (-13.355963, -4.062515), (-10.463048, 0.580935), (-10.586221, 1.780310),
    (-16.190814, 3.093899), (-16.088938, 8.915268), (-14.371544, 11.854624),
    (-13.961407, 15.065727), (-13.921971, 20.333351), (-15.870729, 20.968179),
    (-15.690195, 31.513223), (-10.486453, 32.788896), (-10.521303, 31.502808),
    (-6.885962, 31.389939), (-6.804775, 34.139421), (0.908088, 33.120606),
    (0.829684, 31.313806), (3.108517, 31.229316), (5.099423, 33.178110),
    (5.056946, 31.293216), (6.902444, 31.247521), (6.928017, 33.254628),
    (9.514224, 31.214244), (9.520869, 33.909222), (18.889334, 33.878590),
    (18.877649, 27.889711), (17.068642, 27.901667), (17.055500, 24.696596),
    (18.832958, 22.932697), (18.733744, 20.216717), (16.613068, 18.225210),
    (16.639345, 20.287763), (15.051972, 20.307986), (15.026825, 18.334145),
    (13.058103, 20.300116), (11.813047, 20.382524), (11.759976, 17.665956),
    (12.855013, 16.676015), (12.857411, 14.690732), (11.831916, 13.894170),
    (11.695269, 12.587198), (13.786935, 10.852567), (11.602593, 7.486614),
    (11.375768, 1.999562), (12.584052, 1.928714), (12.560325, 4.413354),
    (15.357538, 4.444261), (15.368130, 3.102140), (13.940980, -2.413982),
    (12.584327, -2.396698), (12.593227, -1.698092), (11.385413, -2.314879),
    (12.721531, -5.392960), (9.084003, -9.073122), (11.360764, -14.392437),
    (11.355064, -16.288889), (9.065860, -16.292996), (9.065341, -17.058254),
    (11.362078, -17.187333), (9.374886, -17.394921), (9.360991, -19.934535),
    (11.345357, -19.948727), (12.866337, -25.180776), (8.869491, -25.185309),
    (8.827394, -26.316033), (12.786194, -26.399742), (12.731947, -28.484120),
    (9.541685, -32.558158), (8.812879, -32.526691), (8.779773, -34.400613),
    (11.102927, -36.803640), (7.834358, -39.778692), (-2.736579, -38.490562),
    (-2.727120, -39.921395), (-5.033649, -37.662756), (-7.276572, -37.656357),
    (-9.145681, -39.462521),
]
_HANG_N_FLOORS = 15

_ARCH = "LargeOffice"


# ── (1) Regression: the 3 already-rescued footprints generate clean geometry at HEAD ─────

class TestAlreadyRescuedRegression:
    """The 3 buildings rescued by 075934c must keep generating valid geometry at HEAD."""

    @pytest.mark.parametrize("coords,n_floors,osm_id", [
        (_B1_COORDS, _B1_N_FLOORS, "way/388772955"),
        (_B3_COORDS, _B3_N_FLOORS, "relation/6356830"),
        (_B4_COORDS, _B4_N_FLOORS, "way/427270590"),
    ])
    def test_rescued_footprint_extrudes_without_exception(self, coords, n_floors, osm_id):
        """No exception, zones produced, zero degenerate surfaces, zero interzone mismatches."""
        idf = _make_idf()
        poly = Polygon(coords)
        zones = build_zones(osm_id, poly, _ARCH, n_floors, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])  # must not raise
        zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
        assert len(zone_names) >= 1, f"{osm_id}: no zones extruded"
        assert _count_degenerate_surfaces(idf) == 0, f"{osm_id}: degenerate surfaces remain"
        assert find_mismatched_interzone_pairs(idf) == [], (
            f"{osm_id}: residual interzone vertex mismatches (would be E+ Fatal)"
        )


# ── (2) Complexity gate ──────────────────────────────────────────────────────────

class TestComplexityGate:
    """The hang building routes through the M>T gate to one_zone_per_floor; clean builds don't."""

    def test_hang_building_M_exceeds_threshold(self):
        M = len(_HANG_COORDS) * _HANG_N_FLOORS
        assert M == 1455
        assert M > COREPERIM_COMPLEXITY_THRESHOLD, (
            f"hang M={M} must exceed gate threshold {COREPERIM_COMPLEXITY_THRESHOLD}"
        )

    def test_hang_building_routes_to_one_zone_per_floor(self):
        """The gate fires: only _F{i}_whole zones, no core/perim zones, no degenerate surfaces."""
        idf = _make_idf()
        poly = Polygon(_HANG_COORDS)
        zones = build_zones("way/427274629", poly, _ARCH, _HANG_N_FLOORS, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
        assert len(zone_names) == _HANG_N_FLOORS, (
            f"expected {_HANG_N_FLOORS} whole-floor zones, got {len(zone_names)}"
        )
        for i in range(_HANG_N_FLOORS):
            assert f"way/427274629_F{i}_whole" in zone_names, (
                f"expected _F{i}_whole zone; got {zone_names[:5]}..."
            )
        assert not any(_is_coreperim_zone(n) for n in zone_names), (
            f"core/perim zones must not be built for the hang building: {zone_names[:5]}..."
        )
        assert _count_degenerate_surfaces(idf) == 0

    def test_gate_records_complexity_note(self):
        """The gate-routed zones carry the coreperim_complexity_gate note."""
        idf = _make_idf()
        poly = Polygon(_HANG_COORDS)
        zones = build_zones("way/427274629", poly, _ARCH, _HANG_N_FLOORS, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        notes = {z.get("generation_status_note") for z in zones if z.get("extruded")}
        assert "coreperim_complexity_gate" in notes

    def test_clean_low_M_building_stays_core_perim(self):
        """A clean low-M (M=12) rectangular core/perim building is NOT gated (no false trigger)."""
        idf = _make_idf()
        # 50 m × 40 m = 2000 m², 3 floors → 4 verts × 3 floors = M=12 < 800
        poly = Polygon([(0, 0), (50, 0), (50, 40), (0, 40)])
        zones = build_zones("clean/1", poly, "MediumOffice", 3, "perimeter_core",
                            FLOOR_TO_FLOOR_M, PERIMETER_DEPTH_M)
        extrude_geometry(idf, zones, [])
        zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
        assert any("_core" in n for n in zone_names), (
            f"clean low-M building must stay core/perim; got {zone_names}"
        )
        notes = {z.get("generation_status_note") for z in zones if z.get("extruded")}
        assert "coreperim_complexity_gate" not in notes


# ── (3) Genuinely-unbuildable footprint still drops cleanly (rule 4) ───────────────

def _min_enriched_row(osm_id: str, geom: Polygon, archetype_id: str = "MediumOffice") -> dict:
    """Minimal enriched-row dict sufficient for BuildingIDF.build()."""
    from tests.fixtures.synthetic_10_buildings import _COMMON
    d = {"osm_id": osm_id, "archetype_id": archetype_id, "geometry": geom,
         "levels": 2, "height_m": float("nan"), "footprint_area_m2": geom.area}
    d.update(_COMMON)
    return d


class TestGenuinelyUnbuildableDropsCleanly:
    """A degenerate footprint must drop (failed/skip status), never fabricate a wrong IDF."""

    def test_zero_area_footprint_drops(self):
        # Near-collinear sliver: area ≈ 0 → validate_simplified rejects it (skip), no IDF.
        sliver = Polygon([(0, 0), (100, 0), (100, 0.0001), (0, 0.0001)])
        row = _min_enriched_row("way/sliver", sliver)
        gdf = gpd.GeoDataFrame([row], geometry=[row["geometry"]])
        schedule_lib = _schedule_lib_for(["MediumOffice"])
        with tempfile.TemporaryDirectory() as tmp:
            manifest = run_step3(gdf, schedule_lib, Path(tmp), n_jobs=1)
            assert len(manifest) == 1
            status = manifest.iloc[0]["generation_status"]
            assert status != "success", (
                f"degenerate sliver must not report success; got {status}"
            )
            # No fabricated IDF for a dropped building.
            assert not manifest.iloc[0]["idf_path"], (
                f"dropped building must have empty idf_path; got {manifest.iloc[0]['idf_path']!r}"
            )


# ── (4) Serial-path isolation: one raising building does not crash the loop ────────

def _schedule_lib_for(arch_ids: list[str]) -> dict:
    from openubem.semantic.schedules import build_schedule_library
    return {a: build_schedule_library(a) for a in arch_ids}


class TestSerialPathIsolation:
    """A building that raises inside the n_jobs=1 loop is recorded failed; loop continues."""

    def test_raising_building_isolated_serial(self, monkeypatch):
        good = Polygon([(0, 0), (30, 0), (30, 30), (0, 30)])   # 900 m²
        bad = Polygon([(100, 0), (130, 0), (130, 30), (100, 30)])
        rows = [
            _min_enriched_row("way/good1", good),
            _min_enriched_row("way/bad", bad),
            _min_enriched_row("way/good2", good),
        ]
        gdf = gpd.GeoDataFrame(rows, geometry=[r["geometry"] for r in rows])
        schedule_lib = _schedule_lib_for(["MediumOffice"])

        real_build = BuildingIDF.build

        def patched_build(self, gdf_arg, sched, out_dir):
            if str(self.row["osm_id"]) == "way/bad":
                raise RuntimeError("synthetic build failure")
            return real_build(self, gdf_arg, sched, out_dir)

        monkeypatch.setattr(BuildingIDF, "build", patched_build)

        with tempfile.TemporaryDirectory() as tmp:
            manifest = run_step3(gdf, schedule_lib, Path(tmp), n_jobs=1)

        assert len(manifest) == 3, "all 3 rows must be recorded (loop did not crash)"
        by_id = {str(r["osm_id"]): r for _, r in manifest.iterrows()}
        assert by_id["way/bad"]["generation_status"] == "failed_worker_exception"
        assert by_id["way/good1"]["generation_status"] in ("success", "fallback_bbox")
        assert by_id["way/good2"]["generation_status"] in ("success", "fallback_bbox")
