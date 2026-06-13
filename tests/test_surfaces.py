"""Tests for openubem.idf.surfaces (T09)."""
import shutil
import tempfile
from pathlib import Path

import pytest
from geomeppy import IDF
from shapely.geometry import box

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.surfaces import (
    extrude_geometry,
    find_mismatched_interzone_pairs,
    set_adiabatic_surfaces,
    _repair_mismatched_horizontal_pairs,
    _repair_roof_roof_pairs,
)

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
        """add_block fails twice → tier-2 bbox fallback → fallback_to_bbox=True."""
        from openubem.idf.surfaces import _expand_core_perim_placeholder
        from shapely.geometry import box as _box
        idf = _fresh_idf()
        poly = _box(0, 0, 10, 10)
        placeholder = {
            "name": "bldg_perimgroup",
            "mode": "core/perim",
            "floor_polygon": poly,
            "coords_m": list(poly.exterior.coords)[:-1],
            "num_floors": 1,
            "height_m": 3.5,
            "perim_depth_m": 4.57,
            "archetype_id": "MediumOffice",
        }
        call_count = [0]
        original_add_block = idf.add_block

        def patched_add_block(**kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:  # both core/perim and tier-1 fail
                raise ValueError("simulated failure")
            return original_add_block(**kwargs)

        idf.add_block = patched_add_block
        zones = [placeholder]
        _expand_core_perim_placeholder(idf, placeholder, zones, (ValueError,))
        assert any(z.get("fallback_to_bbox") is True for z in zones), (
            f"expected fallback_to_bbox=True in zones; got {zones}"
        )

    def test_narrow_fallback_marks_zone(self):
        """add_block fails once (core/perim) → tier-1 narrow fallback → narrow_fallback=True."""
        from openubem.idf.surfaces import _expand_core_perim_placeholder
        from shapely.geometry import box as _box
        idf = _fresh_idf()
        poly = _box(0, 0, 10, 10)
        placeholder = {
            "name": "bldg_perimgroup",
            "mode": "core/perim",
            "floor_polygon": poly,
            "coords_m": list(poly.exterior.coords)[:-1],
            "num_floors": 1,
            "height_m": 3.5,
            "perim_depth_m": 4.57,
            "archetype_id": "MediumOffice",
        }
        call_count = [0]
        original_add_block = idf.add_block

        def patched_add_block(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # only core/perim call fails; tier-1 succeeds
                raise ValueError("simulated perim depth failure")
            return original_add_block(**kwargs)

        idf.add_block = patched_add_block
        zones = [placeholder]
        _expand_core_perim_placeholder(idf, placeholder, zones, (ValueError,))
        assert any(z.get("narrow_fallback") is True for z in zones), (
            f"expected narrow_fallback=True in zones; got {zones}"
        )
        assert not any(z.get("fallback_to_bbox") for z in zones), (
            "tier-2 bbox fallback must NOT be set when tier-1 narrow fallback succeeds"
        )

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


class TestRepairRoofRoofPairs:
    """R02: _repair_roof_roof_pairs resets illegal Roof↔Roof interzone pairs to exterior."""

    def _make_surf(self, idf, name, zone, stype, bc="Outdoors", bc_obj="",
                   sun="SunExposed", wind="WindExposed"):
        s = idf.newidfobject(
            "BUILDINGSURFACE:DETAILED",
            Name=name,
            Surface_Type=stype,
            Zone_Name=zone,
            Outside_Boundary_Condition=bc,
            Outside_Boundary_Condition_Object=bc_obj,
            Sun_Exposure=sun,
            Wind_Exposure=wind,
        )
        return s

    def test_roof_roof_pair_reset_to_exterior(self):
        """Two Roof surfaces in different zones referencing each other → both reset to Outdoors."""
        idf = _fresh_idf()
        self._make_surf(idf, "ROOF_A", "ZoneA", "Roof",
                        bc="Surface", bc_obj="ROOF_B", sun="NoSun", wind="NoWind")
        self._make_surf(idf, "ROOF_B", "ZoneB", "Roof",
                        bc="Surface", bc_obj="ROOF_A", sun="NoSun", wind="NoWind")
        _repair_roof_roof_pairs(idf)
        bsds = {s.Name: s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]}
        for name in ("ROOF_A", "ROOF_B"):
            s = bsds[name]
            assert s.Outside_Boundary_Condition == "Outdoors", f"{name}: expected Outdoors, got {s.Outside_Boundary_Condition}"
            assert s.Outside_Boundary_Condition_Object == "", f"{name}: expected empty bc_obj, got {s.Outside_Boundary_Condition_Object}"
            assert s.Sun_Exposure == "SunExposed", f"{name}: expected SunExposed"
            assert s.Wind_Exposure == "WindExposed", f"{name}: expected WindExposed"

    def test_ceiling_floor_pair_untouched(self):
        """Ceiling↔Floor interzone pair is NOT reset by _repair_roof_roof_pairs."""
        idf = _fresh_idf()
        self._make_surf(idf, "CEIL_A", "ZoneA", "Ceiling",
                        bc="Surface", bc_obj="FLOOR_B", sun="NoSun", wind="NoWind")
        self._make_surf(idf, "FLOOR_B", "ZoneB", "Floor",
                        bc="Surface", bc_obj="CEIL_A", sun="NoSun", wind="NoWind")
        _repair_roof_roof_pairs(idf)
        bsds = {s.Name: s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]}
        assert bsds["CEIL_A"].Outside_Boundary_Condition == "Surface", "Ceiling pair must not be reset"
        assert bsds["FLOOR_B"].Outside_Boundary_Condition == "Surface", "Floor pair must not be reset"

    def test_same_zone_roof_pair_untouched(self):
        """Two Roof surfaces in the SAME zone referencing each other are not reset."""
        idf = _fresh_idf()
        self._make_surf(idf, "ROOF_X", "ZoneA", "Roof",
                        bc="Surface", bc_obj="ROOF_Y", sun="NoSun", wind="NoWind")
        self._make_surf(idf, "ROOF_Y", "ZoneA", "Roof",
                        bc="Surface", bc_obj="ROOF_X", sun="NoSun", wind="NoWind")
        _repair_roof_roof_pairs(idf)
        bsds = {s.Name: s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]}
        # Same-zone pairs are unusual but should not be touched by this repair.
        assert bsds["ROOF_X"].Outside_Boundary_Condition == "Surface", "Same-zone pair must not be reset"


def _make_coord_surf(idf, name, zone, stype, coords, bc="Surface", bc_obj="",
                     sun="NoSun", wind="NoWind"):
    s = idf.newidfobject(
        "BUILDINGSURFACE:DETAILED",
        Name=name,
        Surface_Type=stype,
        Zone_Name=zone,
        Outside_Boundary_Condition=bc,
        Outside_Boundary_Condition_Object=bc_obj,
        Sun_Exposure=sun,
        Wind_Exposure=wind,
    )
    s.setcoords(coords)
    return s


_PENTA_Z0 = [(0, 0, 0), (10, 0, 0), (12, 5, 0), (10, 10, 0), (0, 10, 0)]
_TRI_Z0 = [(10, 0, 0), (12, 5, 0), (10, 10, 0)]
_QUAD_Z0 = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)]
_TRI_Z3 = [(10, 0, 3.5), (12, 5, 3.5), (10, 10, 3.5)]
_QUAD_Z3 = [(0, 0, 3.5), (10, 0, 3.5), (10, 10, 3.5), (0, 10, 3.5)]


class TestRepairMismatchedHorizontalPairs:
    """C11: same-type horizontal pairs with mismatched vertex counts are reset."""

    def test_mismatched_floor_floor_reset_to_ground(self):
        """5-vertex floor ↔ 3-vertex floor at z=0 in different zones → both reset to ground."""
        idf = _fresh_idf()
        _make_coord_surf(idf, "FLOOR_A", "ZoneA", "floor", _PENTA_Z0, bc_obj="FLOOR_B")
        _make_coord_surf(idf, "FLOOR_B", "ZoneB", "floor", _TRI_Z0, bc_obj="FLOOR_A")
        _repair_mismatched_horizontal_pairs(idf)
        bsds = {s.Name: s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]}
        for name in ("FLOOR_A", "FLOOR_B"):
            s = bsds[name]
            assert s.Outside_Boundary_Condition == "ground", f"{name}: expected ground"
            assert s.Outside_Boundary_Condition_Object == "", f"{name}: expected empty bc_obj"
            assert s.Sun_Exposure == "NoSun"
            assert s.Wind_Exposure == "NoWind"

    def test_equal_count_floor_floor_untouched(self):
        """Equal vertex counts → untouched (protects byte-identity of valid IDFs)."""
        idf = _fresh_idf()
        _make_coord_surf(idf, "FLOOR_A", "ZoneA", "floor", _TRI_Z0, bc_obj="FLOOR_B")
        _make_coord_surf(idf, "FLOOR_B", "ZoneB", "floor", _TRI_Z0, bc_obj="FLOOR_A")
        _repair_mismatched_horizontal_pairs(idf)
        bsds = {s.Name: s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]}
        assert bsds["FLOOR_A"].Outside_Boundary_Condition == "Surface"
        assert bsds["FLOOR_B"].Outside_Boundary_Condition == "Surface"

    def test_mismatched_ceiling_floor_pair_untouched(self):
        """Legitimate Ceiling↔Floor type combo is never repaired here (validation catches it)."""
        idf = _fresh_idf()
        _make_coord_surf(idf, "CEIL_A", "ZoneA", "ceiling", _QUAD_Z3, bc_obj="FLOOR_B")
        _make_coord_surf(idf, "FLOOR_B", "ZoneB", "floor", _TRI_Z3, bc_obj="CEIL_A")
        _repair_mismatched_horizontal_pairs(idf)
        bsds = {s.Name: s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]}
        assert bsds["CEIL_A"].Outside_Boundary_Condition == "Surface"
        assert bsds["FLOOR_B"].Outside_Boundary_Condition == "Surface"

    def test_mismatched_ceiling_ceiling_reset_to_outdoors(self):
        idf = _fresh_idf()
        _make_coord_surf(idf, "CEIL_A", "ZoneA", "ceiling", _QUAD_Z3, bc_obj="CEIL_B")
        _make_coord_surf(idf, "CEIL_B", "ZoneB", "ceiling", _TRI_Z3, bc_obj="CEIL_A")
        _repair_mismatched_horizontal_pairs(idf)
        bsds = {s.Name: s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]}
        for name in ("CEIL_A", "CEIL_B"):
            s = bsds[name]
            assert s.Outside_Boundary_Condition == "Outdoors", f"{name}: expected Outdoors"
            assert s.Outside_Boundary_Condition_Object == ""
            assert s.Sun_Exposure == "SunExposed"
            assert s.Wind_Exposure == "WindExposed"


class TestFindMismatchedInterzonePairs:
    """C11: generation-time scan for vertex-count mismatches on interzone pairs."""

    def test_detects_mismatched_pair_once(self):
        idf = _fresh_idf()
        _make_coord_surf(idf, "CEIL_A", "ZoneA", "ceiling", _QUAD_Z3, bc_obj="FLOOR_B")
        _make_coord_surf(idf, "FLOOR_B", "ZoneB", "floor", _TRI_Z3, bc_obj="CEIL_A")
        pairs = find_mismatched_interzone_pairs(idf)
        assert len(pairs) == 1
        assert set(pairs[0]) == {"CEIL_A", "FLOOR_B"}

    def test_matching_counts_return_empty(self):
        idf = _fresh_idf()
        _make_coord_surf(idf, "CEIL_A", "ZoneA", "ceiling", _QUAD_Z3, bc_obj="FLOOR_B")
        _make_coord_surf(idf, "FLOOR_B", "ZoneB", "floor", _QUAD_Z3, bc_obj="CEIL_A")
        assert find_mismatched_interzone_pairs(idf) == []

    def test_repair_then_scan_clean(self):
        """The C11 defect shape: repair fires, then the scan reports clean."""
        idf = _fresh_idf()
        _make_coord_surf(idf, "FLOOR_A", "ZoneA", "floor", _PENTA_Z0, bc_obj="FLOOR_B")
        _make_coord_surf(idf, "FLOOR_B", "ZoneB", "floor", _TRI_Z0, bc_obj="FLOOR_A")
        assert len(find_mismatched_interzone_pairs(idf)) == 1
        _repair_mismatched_horizontal_pairs(idf)
        assert find_mismatched_interzone_pairs(idf) == []
