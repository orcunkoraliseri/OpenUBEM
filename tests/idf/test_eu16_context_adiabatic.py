"""Acceptance tests for EU-16 T06 -- 20 m context shading -- and T07 --
adiabatic party walls -- in the European IDF path (D-EU-40 R2-R8, amended by
D-EU-41). T07's flip is a European-only pass in scripts/run_eu_s2_campaign.py;
openubem/idf/surfaces.py's set_adiabatic_surfaces (a documented no-op stub)
is never called or edited here."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import geopandas as gpd
import pytest
from geomeppy import IDF
from shapely.geometry import box

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.geometry.context import resolve_european_context_height
from openubem.idf.surfaces import extrude_geometry
from scripts.run_eu_s2_campaign import (
    EUROPEAN_CONTEXT_RADIUS_M,
    apply_adiabatic_party_walls,
    build_european_context,
)

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = ROOT / "openubem" / "idf" / "templates"
_BASE_TPL = str(TEMPLATES_DIR / "commercial_base.idf")

DISTRICT_CRS = {
    "ES-MAD-BERRUGUETE": "EPSG:32630",
    "FR-LYO-HAUTCOEURPENTES": "EPSG:32631",
    "GB-LDN-STDUNSTANS": "EPSG:32630",
    "IT-BOL-GALVANI2": "EPSG:32632",
}


def _fresh_idf() -> IDF:
    from eppy.modeleditor import IDDAlreadySetError
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(_BASE_TPL)


def _square_zone(name: str, poly, height: float = 3.0) -> dict:
    coords = list(poly.exterior.coords)[:-1]
    return {
        "name": name, "floor_polygon": poly, "coords_m": coords,
        "z_floor": 0.0, "z_ceiling": height, "height_m": height,
    }


def _synthetic_five_building_block() -> gpd.GeoDataFrame:
    """Target at origin, plus A (touching, height_m tier), C (15 m gap,
    levels tier), D (15 m gap, no height data -> district-median tier), and
    B (25 m gap -- strictly outside the 20 m buffer, must be excluded)."""
    rows = [
        {"osm_id": "target", "geometry": box(0, 0, 10, 10), "height_m": None, "levels": None},
        {"osm_id": "A_touching", "geometry": box(10, 0, 20, 10), "height_m": 12.0, "levels": None},
        {"osm_id": "B_far_25m", "geometry": box(35, 0, 45, 10), "height_m": 9.0, "levels": None},
        {"osm_id": "C_gap15m", "geometry": box(25, 0, 35, 10), "height_m": None, "levels": 4},
        {"osm_id": "D_gap15m_no_height", "geometry": box(10, 25, 20, 35), "height_m": None, "levels": None},
    ]
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:32631")


class TestT06ContextShading:
    def test_resolve_european_context_height_precedence_and_tiers(self):
        h, tier = resolve_european_context_height(12.0, 4, district_median_height_m=6.0)
        assert (h, tier) == (12.0, "height_m")
        h, tier = resolve_european_context_height(None, 4, district_median_height_m=6.0)
        assert (h, tier) == (12.0, "levels_x_floor_to_floor_m")
        h, tier = resolve_european_context_height(None, None, district_median_height_m=6.0)
        assert (h, tier) == (6.0, "district_median_residential_height")
        h, tier = resolve_european_context_height(float("nan"), float("nan"), district_median_height_m=6.0)
        assert (h, tier) == (6.0, "district_median_residential_height")

    def test_synthetic_block_emits_exactly_the_neighbours_inside_20m_and_none_outside(self):
        gdf = _synthetic_five_building_block()
        target_row = gdf.loc[gdf["osm_id"] == "target"].iloc[0]
        counter = Counter()
        context = build_european_context(
            "target", target_row.geometry, gdf, district_median_height_m=6.0,
            height_fallback_counter=counter,
        )
        names = {c["name"] for c in context}
        assert names == {"shade_A_touching", "shade_C_gap15m", "shade_D_gap15m_no_height"}
        assert "shade_B_far_25m" not in names
        assert len(context) == 3

        by_name = {c["name"]: c for c in context}
        assert by_name["shade_A_touching"]["height"] == pytest.approx(12.0)
        assert by_name["shade_C_gap15m"]["height"] == pytest.approx(4 * 3.0)
        assert by_name["shade_D_gap15m_no_height"]["height"] == pytest.approx(6.0)
        assert counter["height_m"] == 1
        assert counter["levels_x_floor_to_floor_m"] == 1
        assert counter["district_median_residential_height"] == 1

    def test_no_context_building_appears_as_a_zone_and_shading_added_after_intersect_match(self):
        gdf = _synthetic_five_building_block()
        target_row = gdf.loc[gdf["osm_id"] == "target"].iloc[0]
        context = build_european_context(
            "target", target_row.geometry, gdf, district_median_height_m=6.0,
            height_fallback_counter=Counter(),
        )
        idf = _fresh_idf()
        zones = [_square_zone("target_F0_whole", box(0, 0, 10, 10))]
        extrude_geometry(idf, zones, context)

        zone_names = {z.Name for z in idf.idfobjects["ZONE"]}
        assert zone_names == {"target_F0_whole"}
        shading_names = {s.Name for s in idf.idfobjects["SHADING:SITE:DETAILED"]}
        assert shading_names, "expected at least one Shading:Site:Detailed object"
        assert not (shading_names & zone_names)
        for name in shading_names:
            assert not name.startswith("target_F0"), f"context object collided with a zone name: {name}"
        assert any(name.startswith("shade_A_touching") for name in shading_names)
        assert any(name.startswith("shade_C_gap15m") for name in shading_names)
        assert any(name.startswith("shade_D_gap15m_no_height") for name in shading_names)
        assert not any(name.startswith("shade_B_far_25m") for name in shading_names)


class TestT06RealFleetSpatialQueryParity:
    @pytest.mark.parametrize("district", sorted(DISTRICT_CRS))
    def test_ten_named_real_buildings_shading_count_equals_spatial_query(self, district):
        buildings_clean = gpd.read_file(ROOT / f"openubem/outputs/eu02/{district}/01_buildings_clean.gpkg")
        assert str(buildings_clean.crs) == DISTRICT_CRS[district]
        manifest = gpd.read_file(ROOT / f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg")
        sample = manifest.sort_values("osm_id", kind="stable").head(10)
        assert len(sample) == 10

        # This test only checks name-set parity against an independently
        # recomputed spatial query, never a height value, so a fixed
        # placeholder is used rather than compute_district_median_residential_height_m
        # over buildings_clean (Bologna's 01_buildings_clean.gpkg carries 0/1631
        # height_m and 0/1631 levels -- its height comes from a separate CTC
        # dataset never present in this layer, so that helper would raise here).
        district_median_height_m = 9.0

        for _, target in sample.iterrows():
            osm_id = str(target["osm_id"])
            expected_idx = buildings_clean.sindex.query(
                target.geometry.buffer(EUROPEAN_CONTEXT_RADIUS_M), predicate="intersects",
            )
            expected = {
                str(buildings_clean.iloc[i]["osm_id"])
                for i in expected_idx
                if str(buildings_clean.iloc[i]["osm_id"]) != osm_id
            }
            context = build_european_context(
                osm_id, target.geometry, buildings_clean, district_median_height_m,
                height_fallback_counter=Counter(),
            )
            got = {c["name"][len("shade_"):] for c in context}
            assert got == expected, f"{district} {osm_id}: context mismatch"
            assert osm_id not in got


def _wall_xy_bounds(surface) -> tuple[float, float, float, float]:
    xs = [pt[0] for pt in surface.coords]
    ys = [pt[1] for pt in surface.coords]
    return min(xs), max(xs), min(ys), max(ys)


class TestT07AdiabaticPartyWalls:
    def test_two_touching_footprints_flip_exactly_the_shared_wall_and_nothing_else(self):
        idf = _fresh_idf()
        target_poly = box(0, 0, 10, 10)
        zones = [_square_zone("target_F0_whole", target_poly)]
        neighbour_coords = list(box(10, 0, 20, 10).exterior.coords)[:-1]
        context = [{"name": "shade_neighbour", "coords": neighbour_coords, "height": 9.0}]
        extrude_geometry(idf, zones, context)

        zone_names_before = {z.Name for z in idf.idfobjects["ZONE"]}
        walls_before = [
            s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
            if s.Surface_Type.upper() == "WALL" and s.Outside_Boundary_Condition.upper() == "OUTDOORS"
        ]
        assert len(walls_before) == 4

        stats = apply_adiabatic_party_walls(idf, context)

        zone_names_after = {z.Name for z in idf.idfobjects["ZONE"]}
        assert zone_names_after == zone_names_before, "T07 must not change zone count/names"

        walls = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        adiabatic_walls = [s for s in walls if s.Surface_Type.upper() == "WALL" and s.Outside_Boundary_Condition == "Adiabatic"]
        outdoor_walls = [s for s in walls if s.Surface_Type.upper() == "WALL" and s.Outside_Boundary_Condition.upper() == "OUTDOORS"]
        assert len(adiabatic_walls) == 1
        assert len(outdoor_walls) == 3
        assert stats["adiabatic_wall_count"] == 1

        flipped = adiabatic_walls[0]
        xmin, xmax, ymin, ymax = _wall_xy_bounds(flipped)
        assert xmin == pytest.approx(10.0) and xmax == pytest.approx(10.0), \
            "the flipped wall must be the x=10 shared face, not any other exterior wall"
        assert ymin == pytest.approx(0.0) and ymax == pytest.approx(10.0)

        # Ground-floor slab and roof/ceiling are never touched (surfaces.py:912 guard).
        floors = [s for s in walls if s.Surface_Type.upper() == "FLOOR"]
        assert floors and all(s.Outside_Boundary_Condition.lower() == "ground" for s in floors)
        roofs = [s for s in walls if s.Surface_Type.upper() in ("ROOF", "ROOFCEILING")]
        assert all(s.Outside_Boundary_Condition != "Adiabatic" for s in roofs)

    def test_a_detached_building_flips_nothing(self):
        idf = _fresh_idf()
        target_poly = box(0, 0, 10, 10)
        zones = [_square_zone("target_F0_whole", target_poly)]
        far_neighbour_coords = list(box(50, 0, 60, 10).exterior.coords)[:-1]
        context = [{"name": "shade_far", "coords": far_neighbour_coords, "height": 9.0}]
        extrude_geometry(idf, zones, context)

        stats = apply_adiabatic_party_walls(idf, context)

        assert stats["adiabatic_wall_count"] == 0
        walls = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        adiabatic_walls = [s for s in walls if s.Outside_Boundary_Condition == "Adiabatic"]
        assert adiabatic_walls == []
        outdoor_walls = [s for s in walls if s.Surface_Type.upper() == "WALL" and s.Outside_Boundary_Condition.upper() == "OUTDOORS"]
        assert len(outdoor_walls) == 4

    def test_flipped_surface_is_eplus_valid(self):
        idf = _fresh_idf()
        target_poly = box(0, 0, 10, 10)
        zones = [_square_zone("target_F0_whole", target_poly)]
        neighbour_coords = list(box(10, 0, 20, 10).exterior.coords)[:-1]
        context = [{"name": "shade_neighbour", "coords": neighbour_coords, "height": 9.0}]
        extrude_geometry(idf, zones, context)

        apply_adiabatic_party_walls(idf, context)

        walls = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        adiabatic_walls = [s for s in walls if s.Outside_Boundary_Condition == "Adiabatic"]
        assert len(adiabatic_walls) == 1
        flipped = adiabatic_walls[0]
        assert flipped.Outside_Boundary_Condition == "Adiabatic"
        assert not str(flipped.Outside_Boundary_Condition_Object or "").strip()
        assert flipped.Sun_Exposure == "NoSun"
        assert flipped.Wind_Exposure == "NoWind"

    def test_zone_count_identical_before_and_after(self):
        idf = _fresh_idf()
        target_poly = box(0, 0, 10, 10)
        zones = [
            _square_zone("target_F0_whole", target_poly),
            _square_zone("target_F1_whole", target_poly),
        ]
        neighbour_coords = list(box(10, 0, 20, 10).exterior.coords)[:-1]
        context = [{"name": "shade_neighbour", "coords": neighbour_coords, "height": 9.0}]
        extrude_geometry(idf, zones, context)

        zone_count_before = len(idf.idfobjects["ZONE"])
        apply_adiabatic_party_walls(idf, context)
        zone_count_after = len(idf.idfobjects["ZONE"])

        assert zone_count_before == zone_count_after
        assert zone_count_before == 2

    def test_no_neighbours_is_a_no_op(self):
        idf = _fresh_idf()
        target_poly = box(0, 0, 10, 10)
        zones = [_square_zone("target_F0_whole", target_poly)]
        extrude_geometry(idf, zones, [])

        stats = apply_adiabatic_party_walls(idf, [])

        assert stats["adiabatic_wall_count"] == 0
        assert stats["adiabatic_wall_area_m2"] == 0.0
        assert stats["exterior_wall_area_m2"] == pytest.approx(120.0)
