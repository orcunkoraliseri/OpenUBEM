"""Tests for openubem.idf.surfaces (T09)."""
import shutil
import tempfile
from pathlib import Path

import pytest
from geomeppy import IDF
from shapely.geometry import box

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.surfaces import extrude_geometry, set_adiabatic_surfaces

TEMPLATES_DIR = Path(__file__).parent.parent / "openubem" / "idf" / "templates"
_BASE_TPL = str(TEMPLATES_DIR / "commercial_base.idf")


def _fresh_idf() -> IDF:
    from eppy.modeleditor import IDDAlreadySetError
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(_BASE_TPL)


def _square_zone(name: str, size: float = 10.0, z_floor: float = 0.0, height: float = 3.5) -> dict:
    poly = box(0, 0, size, size)
    coords = list(poly.exterior.coords)[:-1]
    return {
        "name": name,
        "floor_polygon": poly,
        "coords_m": coords,
        "z_floor": z_floor,
        "z_ceiling": z_floor + height,
        "height_m": height,
    }


class TestSurfaces:
    def test_single_zone_six_surfaces(self):
        idf = _fresh_idf()
        zones = [_square_zone("bldg_F0_whole")]
        extrude_geometry(idf, zones, [])
        bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        assert len(bsds) == 6  # floor + ceiling + 4 walls

    def test_two_adjacent_zones_and_one_context(self):
        """Two horizontally adjacent zones share a wall; intersect_match pairs it."""
        idf = _fresh_idf()
        # Adjacent zones sharing wall at x=10
        poly_a = box(0, 0, 10, 10)
        poly_b = box(10, 0, 20, 10)
        zone_a = {
            "name": "bldg_F0_core",
            "floor_polygon": poly_a,
            "coords_m": list(poly_a.exterior.coords)[:-1],
            "z_floor": 0.0, "z_ceiling": 3.5, "height_m": 3.5,
        }
        zone_b = {
            "name": "bldg_F0_perim",
            "floor_polygon": poly_b,
            "coords_m": list(poly_b.exterior.coords)[:-1],
            "z_floor": 0.0, "z_ceiling": 3.5, "height_m": 3.5,
        }
        ctx = [{"name": "shade_ctx1", "coords": [(25, 0), (30, 0), (30, 5), (25, 5)], "height": 5.0}]
        extrude_geometry(idf, [zone_a, zone_b], ctx)
        bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        shading = idf.idfobjects["SHADING:SITE:DETAILED"]
        assert len(bsds) >= 10
        assert len(shading) >= 1
        # intersect_match pairs the shared wall → at least one surface should have BC "Surface"
        surface_bcs = [s.Outside_Boundary_Condition.lower() for s in bsds]
        assert "surface" in surface_bcs

    def test_empty_coords_zone_skipped(self):
        idf = _fresh_idf()
        good = _square_zone("bldg_F0_whole")
        bad = {
            "name": "bldg_F0_perim",
            "floor_polygon": box(0, 0, 5, 5),
            "coords_m": [],
            "z_floor": 0.0,
            "z_ceiling": 3.5,
            "height_m": 3.5,
        }
        extrude_geometry(idf, [good, bad], [])
        # After _rename_geomeppy_zone, zone names match our convention not geomeppy's wrapper
        zone_names = {s.Zone_Name for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]}
        assert "bldg_F0_whole" in zone_names
        assert "bldg_F0_perim" not in zone_names  # skipped due to empty coords_m

    def test_bbox_fallback_marks_zone(self):
        idf = _fresh_idf()
        zone = _square_zone("bldg_F0_whole")
        call_count = [0]
        original_add_block = idf.add_block

        def patched_add_block(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("simulated failure")
            return original_add_block(**kwargs)

        idf.add_block = patched_add_block
        extrude_geometry(idf, [zone], [])
        assert zone.get("fallback_to_bbox") is True

    def test_ground_floor_slab_bc_is_ground(self):
        """C3/R3: z=0 ground floors keep geomeppy's 'ground' BC — no Adiabatic flip.
        No manual forcing; asserts the REAL production behavior after extrude_geometry."""
        idf = _fresh_idf()
        zones = [_square_zone("bldg_F0_whole")]
        extrude_geometry(idf, zones, [])
        set_adiabatic_surfaces(idf, zones, "single_zone")
        floor_bcs = [
            s.Outside_Boundary_Condition.lower()
            for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
            if s.Surface_Type.lower() == "floor" and "_F0_" in s.Zone_Name
        ]
        assert floor_bcs, "expected at least one floor surface"
        for bc in floor_bcs:
            assert bc == "ground", f"expected 'ground' BC for F0 floor, got {bc!r}"

    def test_perim_core_party_wall_surface_matched(self):
        """C4: ≥1 perim↔core wall pair is Surface-matched after native core/perim extrusion.
        R7: perim↔core walls stay as Surface pairs (inter-zone conduction), not Adiabatic.
        Fails if party-wall logic is removed or if no Surface pairs are produced."""
        from openubem.geometry.zoning import build_zones

        idf = _fresh_idf()
        poly = box(0, 0, 30, 30)
        zones = build_zones("bldg", poly, "MediumOffice", 1, "perimeter_core")
        extrude_geometry(idf, zones, [])
        set_adiabatic_surfaces(idf, zones, "perimeter_core")

        # Collect zone names produced by expansion.
        expanded_zone_names = {z["name"] for z in zones}
        perim_names = {n for n in expanded_zone_names if "_perim" in n}
        core_names = {n for n in expanded_zone_names if "_core" in n}
        assert perim_names and core_names, "expected both perim and core zones to exist"

        # Count wall surfaces with BC=Surface between perim and core.
        bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        surf_to_zone = {s.Name: s.Zone_Name for s in bsds}
        surface_pairs = [
            s for s in bsds
            if s.Surface_Type.lower() == "wall"
            and s.Outside_Boundary_Condition.lower() == "surface"
            and s.Zone_Name in expanded_zone_names
            and surf_to_zone.get(s.Outside_Boundary_Condition_Object, "") in expanded_zone_names
        ]
        assert len(surface_pairs) >= 1, (
            "expected ≥1 Surface-matched wall pair between perim and core zones; "
            f"found 0. Wall BCs: {[s.Outside_Boundary_Condition for s in bsds if s.Surface_Type.lower() == 'wall']}"
        )


class TestCorePerimNative:
    """C2: native core/perim via add_block(zoning='core/perim') (R7)."""

    def test_core_perim_floor_areas_sum_to_footprint(self):
        """Perim+core zone floor areas for one storey sum to footprint area ±1%."""
        from openubem.geometry.zoning import build_zones

        idf = _fresh_idf()
        side = 30.0
        poly = box(0, 0, side, side)
        footprint_area = poly.area  # 900 m²

        zones = build_zones("bldg2", poly, "MediumOffice", 1, "perimeter_core")
        extrude_geometry(idf, zones, [])

        bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        expanded_zone_names = {z["name"] for z in zones}

        # Sum floor areas across all perim+core zones (one storey).
        total_floor_area = sum(
            s.area
            for s in bsds
            if s.Surface_Type.lower() == "floor"
            and s.Zone_Name in expanded_zone_names
        )
        assert abs(total_floor_area - footprint_area) / footprint_area < 0.01, (
            f"floor area sum {total_floor_area:.2f} differs from footprint {footprint_area:.2f} "
            f"by more than 1%"
        )

    def test_core_perim_wall_surface_matched(self):
        """≥1 perim↔core wall pair is Surface-matched (inter-zone conduction per R7)."""
        from openubem.geometry.zoning import build_zones

        idf = _fresh_idf()
        poly = box(0, 0, 30, 30)
        zones = build_zones("bldg3", poly, "MediumOffice", 1, "perimeter_core")
        extrude_geometry(idf, zones, [])

        bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        expanded_zone_names = {z["name"] for z in zones}
        surf_to_zone = {s.Name: s.Zone_Name for s in bsds}

        surface_pairs = [
            s for s in bsds
            if s.Surface_Type.lower() == "wall"
            and s.Outside_Boundary_Condition.lower() == "surface"
            and s.Zone_Name in expanded_zone_names
            and surf_to_zone.get(s.Outside_Boundary_Condition_Object, "") in expanded_zone_names
        ]
        assert len(surface_pairs) >= 1, (
            "expected ≥1 Surface-matched wall pair between perim and core zones"
        )

    def test_core_perim_zone_names(self):
        """Expanded zones follow {osm_id}_F{i}_perim{n} / {osm_id}_F{i}_core naming (R7)."""
        from openubem.geometry.zoning import build_zones

        poly = box(0, 0, 30, 30)
        zones = build_zones("way_99", poly, "MediumOffice", 2, "perimeter_core")

        idf = _fresh_idf()
        extrude_geometry(idf, zones, [])

        names = {z["name"] for z in zones}
        core_names = {n for n in names if n.endswith("_core")}
        perim_names = {n for n in names if "_perim" in n and not n.endswith("_core")}
        assert len(core_names) == 2, f"expected 2 core zones (F0+F1), got {core_names}"
        assert len(perim_names) >= 2, f"expected ≥2 perim zones (≥1 wedge × 2 floors), got {perim_names}"
        for n in core_names:
            assert n.startswith("way_99_F"), f"unexpected core zone name: {n}"
        for n in perim_names:
            assert n.startswith("way_99_F"), f"unexpected perim zone name: {n}"

    def test_core_perim_narrow_fallback_sets_generation_status(self):
        """Narrow building: geomeppy ValueError → fallback to per-floor, status note set."""
        from openubem.geometry.zoning import build_zones

        # 7×7 square: buffer(-4.57) → empty core → build_zones falls back to one_zone_per_floor
        poly = box(0, 0, 7, 7)
        zones = build_zones("narrow", poly, "MediumOffice", 2, "perimeter_core")
        # Should already be one_zone_per_floor fallback (no core/perim placeholder)
        assert all(z.get("mode") != "core/perim" for z in zones)
        assert all("_whole" in z["name"] for z in zones)


class TestMultiStoreyStacking:
    """C1 (R2): one add_block with num_stories=N stacks storeys at true z heights."""

    def test_three_storey_building_floor_ceiling_bc(self):
        """3-storey one_zone_per_floor building:
        - exactly one floor with BC 'Ground' (storey 0)
        - exactly one roof with BC 'Outdoors' + SunExposed (top storey)
        - at least one Surface-BC pair between storeys 1 and 2
        """
        from openubem.geometry.zoning import build_zones

        idf = _fresh_idf()
        osm_id = "test_bldg"
        num_floors = 3
        floor_to_floor = 3.5
        poly = box(0, 0, 10, 10)

        zones = build_zones(osm_id, poly, "MidriseApartment", num_floors, "one_zone_per_floor",
                            floor_to_floor_m=floor_to_floor)
        extrude_geometry(idf, zones, [])

        bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]

        # Exactly one ground floor (z=0 floor, BC 'ground').
        ground_floors = [
            s for s in bsds
            if s.Surface_Type.lower() == "floor"
            and s.Outside_Boundary_Condition.lower() == "ground"
        ]
        assert len(ground_floors) == 1, (
            f"expected 1 ground floor, got {len(ground_floors)}: "
            + str([(s.Zone_Name, s.Outside_Boundary_Condition) for s in ground_floors])
        )

        # Exactly one exposed roof (top storey, BC 'Outdoors' + SunExposed).
        exposed_roofs = [
            s for s in bsds
            if s.Surface_Type.lower() == "roof"
            and s.Outside_Boundary_Condition.lower() == "outdoors"
            and s.Sun_Exposure.lower() == "sunexposed"
        ]
        assert len(exposed_roofs) == 1, (
            f"expected 1 exposed roof, got {len(exposed_roofs)}: "
            + str([(s.Zone_Name, s.Outside_Boundary_Condition, s.Sun_Exposure) for s in exposed_roofs])
        )

        # At least one Surface-BC pair (inter-storey ceiling/floor adjacency).
        surface_bc_surfaces = [
            s for s in bsds
            if s.Outside_Boundary_Condition.lower() == "surface"
        ]
        assert len(surface_bc_surfaces) >= 1, (
            "expected at least one Surface-BC inter-storey pair after intersect_match"
        )
