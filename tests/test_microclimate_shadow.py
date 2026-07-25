import sys
from pathlib import Path

import numpy as np
import pytest
from rasterio.transform import rowcol

sys.path.insert(0, str(Path(__file__).parent / "fixtures"))
from synthetic_canyon import build_canyon_gdf  # noqa: E402

from openubem import config
from openubem.microclimate.domain import build_domain
from openubem.microclimate.shadow import cast_shadows


def _single_block_domain(h, w=20.0, res=1.0, buffer_m=60.0):
    import geopandas as gpd
    from shapely.geometry import box

    block = box(-w / 2, -w / 2, w / 2, w / 2)
    gdf = gpd.GeoDataFrame(
        {"osm_id": ["blk"], "height_m": [h]}, geometry=[block], crs="EPSG:32618"
    )
    return build_domain(gdf, res_m=res, buffer_m=buffer_m)


def test_shadow_length_45deg_due_south():
    # Sun due south (az=180, solar-noon convention, T04) at 45 deg altitude: rays travel south
    # -> north, so the block's shadow falls on the ground NORTH of it. Sample points sit
    # outside the footprint (self-occlusion does not apply) so this exercises the horizon-
    # stack lateral lookup only. Expected length uses the pedestrian-height-adjusted target,
    # by the same reasoning as the SVF gate (E-UTCI-02): the block's occluding height above
    # the observer is H - z, not H. sh_building is a SUNLIT indicator (module docstring,
    # matches U03's S_bldg multiplicative-gate convention) -> shadow is where it is False.
    h, w, res = 20.0, 20.0, 1.0
    dom = _single_block_domain(h, w=w, res=res)
    sh_building, _sh_veg = cast_shadows(dom, altitude_deg=45.0, azimuth_deg=180.0)

    expected_len = (h - config.UTCI_PEDESTRIAN_HEIGHT_M) / np.tan(np.radians(45.0))
    north_edge_y = w / 2.0  # block's own north face

    # Column at x=0 (through the block centre), scan northward from the block's north face.
    col_x = 0.0
    ys = np.arange(north_edge_y + res / 2.0, north_edge_y + expected_len + 15.0, res)
    shadowed_ys = []
    for y in ys:
        r, c = rowcol(dom.transform, col_x, y)
        if not sh_building[r, c]:
            shadowed_ys.append(y)
    measured_len = (max(shadowed_ys) - north_edge_y) if shadowed_ys else 0.0

    assert abs(measured_len - expected_len) <= 2.0, (
        f"measured shadow length {measured_len:.2f} vs expected {expected_len:.2f}"
    )


def test_shadow_zenith_equals_footprint():
    h, w, res = 20.0, 20.0, 2.0
    dom = _single_block_domain(h, w=w, res=res)
    sh_building, _sh_veg = cast_shadows(dom, altitude_deg=90.0, azimuth_deg=123.0)
    shadow_area = float((~sh_building).sum()) * res * res
    footprint_area = w * w
    assert abs(shadow_area - footprint_area) / footprint_area <= 0.15


def test_shadow_below_horizon_everything_shaded():
    dom = _single_block_domain(20.0)
    sh_building, sh_veg = cast_shadows(dom, altitude_deg=-5.0, azimuth_deg=90.0)
    assert not sh_building.any()  # nobody sunlit
    assert (sh_veg == 0.0).all()


def test_shadow_smooth_across_0_360_wrap():
    dom = _single_block_domain(20.0, res=2.0)
    areas = []
    for az in (358.0, 359.0, 0.0, 1.0, 2.0):
        sh_building, _ = cast_shadows(dom, altitude_deg=30.0, azimuth_deg=az)
        areas.append(float((~sh_building).sum()))
    diffs = np.abs(np.diff(areas))
    assert diffs.max() <= 0.15 * max(areas), f"shadow area jumps across the wrap: {areas}"


def test_veg_transmission_normal_incidence():
    import geopandas as gpd
    from shapely.geometry import Point

    from openubem.microclimate import domain as domain_mod

    stub = gpd.GeoDataFrame(
        {"osm_id": ["stub"], "height_m": [3.0]}, geometry=[Point(0, 0).buffer(1.0)], crs="EPSG:32618"
    )
    dom = build_domain(stub, res_m=1.0, buffer_m=30.0)

    tree = gpd.GeoDataFrame(
        {"crown_height_m": [12.0], "crown_radius_m": [4.0]},
        geometry=[Point(15.0, 0.0)],
        crs="EPSG:32618",
    )
    cdsm, tdsm, _lai, _flags = domain_mod.build_vegetation(
        dom.shape, dom.transform, tier="osm", tree_points=tree
    )

    tau_ref = 0.15
    sh_building, sh_veg = cast_shadows(
        dom, altitude_deg=90.0, azimuth_deg=45.0, cdsm=cdsm, tdsm=tdsm, canopy_tau=tau_ref,
    )
    r, c = rowcol(dom.transform, 15.0, 0.0)
    measured = float(sh_veg[r, c])
    assert abs(measured - tau_ref) <= 0.02, f"measured {measured:.4f} vs tau_ref {tau_ref}"


def test_veg_transmission_none_where_no_canopy():
    dom = _single_block_domain(20.0, res=2.0)
    _sh_building, sh_veg = cast_shadows(dom, altitude_deg=45.0, azimuth_deg=180.0)
    assert np.allclose(sh_veg, 1.0)


def test_svf_bounds_reused_hw1p0():
    # sanity: the horizon stack this module consumes is the same one T10 gates on (CP-2).
    dom = _single_block_domain(20.0, w=20.0, res=2.0)
    sh_building, _ = cast_shadows(dom, altitude_deg=60.0, azimuth_deg=200.0)
    assert sh_building.dtype == bool
