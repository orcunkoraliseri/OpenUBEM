import numpy as np
import pytest
import geopandas as gpd
from shapely.geometry import box

from openubem.microclimate.domain import build_domain
from openubem.microclimate.wind import (
    cost730_factor,
    morphometric_parameters,
    pedestrian_wind,
    pedestrian_wind_cost730,
    pedestrian_wind_macdonald,
)


def test_cost730_factor_matches_cited_0p680():
    assert abs(cost730_factor() - 0.680) < 0.001


def test_cost730_v1p1_ratio():
    v10 = 5.0
    v_1p1 = pedestrian_wind_cost730(v10, (3, 3))
    ratio = float(v_1p1[0, 0]) / v10
    assert abs(ratio - 0.680) < 0.001


def test_va10_eq_roundtrip_open_terrain():
    v10 = 5.0
    v_1p1, va10_eq, flags = pedestrian_wind(v10, (3, 3), tier="cost730")
    assert np.allclose(va10_eq, v10, atol=1e-9)
    assert np.all(flags == 0)


def test_clamp_flag_fires_below_0p5():
    v10 = 0.3
    v_1p1, va10_eq, flags = pedestrian_wind(v10, (2, 2), tier="cost730")
    assert np.all(va10_eq == 0.5)
    assert np.all(flags == 1)


def test_clamp_flag_fires_above_17():
    v10 = 30.0
    v_1p1, va10_eq, flags = pedestrian_wind(v10, (2, 2), tier="cost730")
    assert np.all(va10_eq == 17.0)
    assert np.all(flags == 1)


def _block_domain(res=5.0, buffer_m=150.0, building_height=20.0):
    building = box(-10.0, -10.0, 10.0, 10.0)
    gdf = gpd.GeoDataFrame({"osm_id": ["b1"], "height_m": [building_height]}, geometry=[building], crs="EPSG:32618")
    dom = build_domain(gdf, res_m=res, buffer_m=buffer_m)
    return gdf, dom


def test_lambda_p_zero_far_from_block():
    gdf, dom = _block_domain()
    lambda_p, lambda_f, mean_h = morphometric_parameters(gdf, dom, wind_direction_deg=270.0, window_radius_m=15.0)
    assert lambda_p[0, 0] == pytest.approx(0.0, abs=1e-9)
    assert lambda_f[0, 0] == pytest.approx(0.0, abs=1e-9)


def test_lambda_p_positive_inside_block_window():
    gdf, dom = _block_domain()
    lambda_p, lambda_f, mean_h = morphometric_parameters(gdf, dom, wind_direction_deg=270.0, window_radius_m=15.0)
    center_row, center_col = dom.shape[0] // 2, dom.shape[1] // 2
    assert lambda_p[center_row, center_col] > 0.1
    assert lambda_f[center_row, center_col] > 0.0
    assert mean_h[center_row, center_col] == pytest.approx(20.0, abs=1e-6)


def test_macdonald_open_field_reduces_to_log_profile():
    gdf, dom = _block_domain()
    lambda_p, lambda_f, mean_h = morphometric_parameters(gdf, dom, wind_direction_deg=270.0, window_radius_m=15.0)
    v10 = 5.0
    v_1p1_macdonald, domain_invalid, numerical_anomaly = pedestrian_wind_macdonald(v10, lambda_p, lambda_f, mean_h)
    v_1p1_cost730 = pedestrian_wind_cost730(v10, dom.shape)
    assert v_1p1_macdonald[0, 0] == pytest.approx(v_1p1_cost730[0, 0], rel=1e-6)
    assert domain_invalid[0, 0] == False  # noqa: E712 -- open field, lambda_p=0, never engages E-UTCI-07's fallback
    assert numerical_anomaly[0, 0] == False  # noqa: E712 -- open field never engages E-UTCI-08's postcondition check either


def test_macdonald_wind_lower_near_block_than_free_stream():
    # H=5 m keeps d well below the E-UTCI-07 fallback threshold (10 - d <= 1.1 m) at this
    # geometry's own lambda_p -- domain-valid, so this genuinely exercises the in-canopy
    # formula's own wind-reduction behaviour, not the cost730 fallback (see the H=45 m test below
    # for that case).
    gdf, dom = _block_domain(building_height=5.0)
    v10 = 5.0
    v_1p1, va10_eq, flags = pedestrian_wind(
        v10, dom.shape, tier="macdonald", buildings_gdf=gdf, domain=dom,
        wind_direction_deg=270.0, window_radius_m=15.0,
    )
    center_row, center_col = dom.shape[0] // 2, dom.shape[1] // 2
    free_stream = float(v_1p1[0, 0])
    near_block = float(v_1p1[center_row, center_col])
    assert near_block < free_stream
    assert (flags[center_row, center_col] & 0x02) == 0  # WIND_FLAG_MACDONALD_DOMAIN_INVALID not fired


def test_macdonald_never_exceeds_or_reverses_free_stream():
    """E-UTCI-07/E-UTCI-08, T15's updated 'How to test': every macdonald-tier output value must
    satisfy 0 <= v_1p1 <= v10 -- a physically necessary bound (in-canopy wind cannot exceed or
    reverse the free-stream reference). Swept across heights spanning domain-valid and
    domain-invalid (E-UTCI-07 fallback) regimes; the old (pre-E-UTCI-07) test only checked two
    cells and only compared them against each other, which is exactly the sign/magnitude-blind gap
    that let the original defect ship undetected. E-UTCI-07's fallback alone left a residual,
    differently-rooted defect (E-UTCI-08) in between the low-rise and very-tall regimes -- this
    test was xfail(strict=True) until E-UTCI-08's postcondition sanity check (module docstring,
    `pedestrian_wind_macdonald`'s numerical_anomaly branch) was implemented, which guarantees the
    bound by construction for every cell regardless of route, closing the gap for real. No longer
    xfail: this now passes genuinely."""
    v10 = 5.0
    for height in (2.0, 5.0, 8.0, 15.0, 20.0, 45.0, 100.0, 397.0):
        gdf, dom = _block_domain(building_height=height)
        v_1p1, va10_eq, flags = pedestrian_wind(
            v10, dom.shape, tier="macdonald", buildings_gdf=gdf, domain=dom,
            wind_direction_deg=270.0, window_radius_m=15.0,
        )
        assert np.all(v_1p1 >= 0.0), f"height={height}: negative wind speed present"
        assert np.all(v_1p1 <= v10 + 1e-9), f"height={height}: wind speed exceeds free-stream v10"


def test_macdonald_tall_building_engages_domain_invalid_fallback():
    """E-UTCI-07, T15's updated 'How to test': a real, tall (H > 30 m) building matching
    nyc_centre's own regime (mean height 41.9 m) must engage the fallback and return the sane
    cost730-equivalent value, not blow up."""
    gdf, dom = _block_domain(building_height=45.0)
    v10 = 5.0
    lambda_p, lambda_f, mean_h = morphometric_parameters(
        gdf, dom, wind_direction_deg=270.0, window_radius_m=15.0
    )
    v_1p1, domain_invalid, numerical_anomaly = pedestrian_wind_macdonald(v10, lambda_p, lambda_f, mean_h)
    center_row, center_col = dom.shape[0] // 2, dom.shape[1] // 2
    v_1p1_cost730 = pedestrian_wind_cost730(v10, dom.shape)
    assert bool(domain_invalid[center_row, center_col]) is True
    assert v_1p1[center_row, center_col] == pytest.approx(v_1p1_cost730[center_row, center_col], rel=1e-6)
    # E-UTCI-08: a domain-invalid cell already carries the cost730 fallback, which always
    # satisfies the bound, so it must never ALSO trip the separate numerical-anomaly check.
    assert bool(numerical_anomaly[center_row, center_col]) is False

    v_1p1_disp, va10_eq, flags = pedestrian_wind(
        v10, dom.shape, tier="macdonald", buildings_gdf=gdf, domain=dom,
        wind_direction_deg=270.0, window_radius_m=15.0,
    )
    assert (flags[center_row, center_col] & 0x02) != 0  # WIND_FLAG_MACDONALD_DOMAIN_INVALID fired
    assert (flags[center_row, center_col] & 0x04) == 0  # WIND_FLAG_MACDONALD_NUMERICAL_ANOMALY not fired


def test_macdonald_dispatcher_requires_geometry_args():
    with pytest.raises(ValueError):
        pedestrian_wind(5.0, (3, 3), tier="macdonald")


def test_unknown_tier_raises():
    with pytest.raises(ValueError):
        pedestrian_wind(5.0, (3, 3), tier="not_a_tier")
