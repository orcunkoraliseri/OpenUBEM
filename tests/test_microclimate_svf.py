import sys
from pathlib import Path

import numpy as np
import pytest
from rasterio.transform import rowcol

sys.path.insert(0, str(Path(__file__).parent / "fixtures"))
from synthetic_canyon import build_canyon_gdf  # noqa: E402

from openubem import config
from openubem.microclimate.domain import build_domain
from openubem.microclimate.svf import compute_svf


def _mid_canyon_svf(h, w, res=2.0, n_azimuths=32):
    # block_len >> w so the canyon approximates the infinite-length case (P-14). E-UTCI-01
    # (see plan §10) showed this doesn't change the conclusion -- kept modest for test runtime.
    gdf = build_canyon_gdf(h, w, block_len=max(300.0, w * 8))
    dom = build_domain(gdf, res_m=res, buffer_m=40.0)
    svf, horizon = compute_svf(dom, n_azimuths=n_azimuths)
    # y=0 (true canyon centreline) falls exactly on a row boundary when w/res is even -- an
    # unavoidable raster edge case, not a real asymmetry. Average the two straddling rows.
    r, c = rowcol(dom.transform, 0.0, res / 2.0)
    r2, _c2 = rowcol(dom.transform, 0.0, -res / 2.0)
    mid_svf = float((svf[r, c] + svf[r2, c]) / 2.0)
    return mid_svf, svf, horizon, dom


@pytest.mark.parametrize("hw", [0.5, 1.0, 2.0])
def test_analytic_canyon_gate(hw):
    # P-14 CORRECTED 2026-07-23 (manager adjudication, E-UTCI-01; plan §9/§10): the analytic
    # 2D infinite-canyon check is Psi_sky = 1/sqrt(1+(2H/W)^2) = cos(atan(2H/W)) (Oke 1981), not
    # sqrt(1+(2H/W)^2)-2H/W -- U03 Table 2 conflated the floor-to-sky SVF with the Hottel
    # two-parallel-strips plate-to-plate configuration factor, a different radiative quantity.
    # FURTHER CORRECTED 2026-07-23 (E-UTCI-02): compute_svf measures at pedestrian height
    # z = UTCI_PEDESTRIAN_HEIGHT_M (T10's own directive), not canyon-floor z=0. The same
    # closed-form derivation with H_eff = H - z substituted gives the height-adjusted target
    # below; targets 0.7268/0.4677/0.2558 at the code's default z=1.1 m. Tolerance unchanged.
    h = 20.0
    w = h / hw
    z = config.UTCI_PEDESTRIAN_HEIGHT_M
    measured, _svf, _horizon, _dom = _mid_canyon_svf(h, w)
    analytic = 1.0 / np.sqrt(1 + (2 * (h - z) / w) ** 2)
    assert abs(measured - analytic) <= 0.03, f"H/W={hw}: measured {measured:.4f} vs analytic {analytic:.4f}"


def test_svf_bounds_0_1():
    _measured, svf, _horizon, _dom = _mid_canyon_svf(20.0, 20.0)
    assert svf.min() >= 0.0 and svf.max() <= 1.0


def test_svf_one_in_empty_domain():
    import geopandas as gpd
    gdf = gpd.GeoDataFrame({"osm_id": [], "height_m": []}, geometry=[], crs="EPSG:32618")
    gdf["geometry"] = gdf["geometry"].astype("geometry")
    from shapely.geometry import Point
    gdf = gpd.GeoDataFrame(
        {"osm_id": ["stub"], "height_m": [3.5]}, geometry=[Point(0, 0).buffer(1.0)], crs="EPSG:32618"
    )
    dom = build_domain(gdf, res_m=5.0, buffer_m=100.0)
    svf, _horizon = compute_svf(dom, n_azimuths=16)
    corner = svf[0, 0]
    assert corner > 0.98


def test_svf_decreases_with_height():
    svf_low, _, _, _ = _mid_canyon_svf(5.0, 20.0)
    svf_high, _, _, _ = _mid_canyon_svf(40.0, 20.0)
    assert svf_high < svf_low


def test_n32_vs_n64_agree_within_0p02():
    measured_32, _, _, _ = _mid_canyon_svf(20.0, 20.0, n_azimuths=32)
    measured_64, _, _, _ = _mid_canyon_svf(20.0, 20.0, n_azimuths=64)
    assert abs(measured_32 - measured_64) < 0.02
