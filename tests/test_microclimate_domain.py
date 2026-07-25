import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import Point, Polygon

sys.path.insert(0, str(Path(__file__).parent / "fixtures"))
from synthetic_canyon import build_canyon_gdf  # noqa: E402

from openubem.microclimate.domain import build_domain, build_vegetation, deciduous_transmissivity

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_canyon.gpkg"


def test_dsm_equals_height_inside_footprint_and_dem_outside():
    gdf = build_canyon_gdf(20.0, 20.0)
    dom = build_domain(gdf, res_m=2.0, buffer_m=30.0)
    # north block occupies y in [10,40]; sample a pixel well inside it, and one far outside.
    from rasterio.transform import rowcol
    r_in, c_in = rowcol(dom.transform, 0.0, 25.0)
    r_out, c_out = rowcol(dom.transform, 0.0, 0.0)  # mid-canyon, outside any footprint
    assert dom.dsm[r_in, c_in] == pytest.approx(20.0)
    assert dom.dsm[r_out, c_out] == pytest.approx(0.0)
    assert dom.dem[r_out, c_out] == pytest.approx(0.0)


def test_mask_matches_footprint_area_within_one_pixel():
    gdf = build_canyon_gdf(20.0, 20.0)
    res = 2.0
    dom = build_domain(gdf, res_m=res, buffer_m=30.0)
    footprint_area = gdf.geometry.area.sum()
    mask_area = dom.building_mask.sum() * res * res
    assert abs(mask_area - footprint_area) / footprint_area < 0.05


def test_rasters_share_transform_crs_shape():
    gdf = build_canyon_gdf(20.0, 20.0)
    dom = build_domain(gdf, res_m=2.0, buffer_m=30.0)
    assert dom.dsm.shape == dom.dem.shape == dom.building_mask.shape == dom.albedo.shape == dom.emissivity.shape
    assert dom.shape == dom.dsm.shape


def test_res_m_changes_shape_not_bounds():
    gdf = build_canyon_gdf(20.0, 20.0)
    dom_coarse = build_domain(gdf, res_m=5.0, buffer_m=30.0)
    dom_fine = build_domain(gdf, res_m=1.0, buffer_m=30.0)
    assert dom_coarse.shape != dom_fine.shape
    assert dom_coarse.bounds[0] == pytest.approx(dom_fine.bounds[0], abs=5.0)
    assert dom_coarse.bounds[2] == pytest.approx(dom_fine.bounds[2], abs=5.0)


def test_missing_height_excluded_and_flagged():
    gdf = build_canyon_gdf(20.0, 20.0)
    gdf.loc[1, "height_m"] = None
    dom = build_domain(gdf, res_m=2.0, buffer_m=30.0)
    assert "canyon_south" in dom.excluded_building_ids
    assert dom.dsm.max() == pytest.approx(20.0)  # north block still present


def test_dem_source_flag_assumed_flat():
    gdf = build_canyon_gdf(20.0, 20.0)
    dom = build_domain(gdf, res_m=2.0, buffer_m=30.0)
    assert dom.dem_source == "assumed_flat"
    assert np.allclose(dom.dem, 0.0)


def test_fixture_file_loads_and_matches_builder():
    gdf = gpd.read_file(FIXTURE)
    assert len(gdf) == 2
    assert set(gdf["height_m"]) == {20.0}


# ── T09 vegetation ──────────────────────────────────────────────────────────────────────────

def test_vegetation_none_tier_all_zero():
    gdf = build_canyon_gdf(20.0, 20.0)
    dom = build_domain(gdf, res_m=2.0, buffer_m=30.0)
    cdsm, tdsm, lai, manifest = build_vegetation(dom.shape, dom.transform, tier="none")
    assert np.allclose(cdsm, 0.0) and np.allclose(tdsm, 0.0) and np.allclose(lai, 0.0)
    assert manifest["vegetation_tier"] == "none"


def test_vegetation_osm_tree_crown_pixel_count():
    gdf = build_canyon_gdf(20.0, 20.0)
    res = 1.0
    dom = build_domain(gdf, res_m=res, buffer_m=30.0)
    trees = gpd.GeoDataFrame(
        {"crown_height_m": [10.0, 10.0, 10.0], "crown_radius_m": [4.0, 4.0, 4.0]},
        geometry=[Point(0, 0), Point(20, 20), Point(-20, -20)],
        crs=dom.crs,
    )
    cdsm, tdsm, lai, manifest = build_vegetation(dom.shape, dom.transform, tier="osm", tree_points=trees)
    expected_px_per_tree = np.pi * 4.0 ** 2 / (res * res)
    n_crown_px = (cdsm > 0).sum()
    assert abs(n_crown_px - 3 * expected_px_per_tree) / (3 * expected_px_per_tree) < 0.15
    assert (tdsm[cdsm > 0] <= cdsm[cdsm > 0]).all()
    assert np.allclose(tdsm[cdsm == 0], 0.0)
    assert manifest["vegetation_source"] == "osm_synthetic"


def test_deciduous_transmissivity_higher_in_january_than_july():
    assert deciduous_transmissivity(1) > deciduous_transmissivity(7)
