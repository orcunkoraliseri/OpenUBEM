import numpy as np
import pandas as pd
import pytest
import geopandas as gpd
from shapely.geometry import Point

from openubem.microclimate.domain import build_domain
from openubem.microclimate.exposure import (
    aggregate_to_parcels,
    cumulative_thermal_stress_index,
    person_hours_extreme_heat,
)


def test_pheh_zero_when_all_below_threshold():
    stack = np.full((3, 4, 4), 30.0)
    total, name, per_cell = person_hours_extreme_heat(stack, res_m=2.0)
    assert total == 0.0
    assert name == "area_hours_extreme_heat_m2h"
    assert np.all(per_cell == 0.0)


def test_pheh_person_hours_exact_20():
    stack = np.full((2, 5, 5), 30.0)
    stack[:, :2, :5] = 50.0  # 10 cells (2 rows x 5 cols) over 46 degC, both hours
    pop = np.ones((5, 5))
    total, name, per_cell = person_hours_extreme_heat(stack, res_m=2.0, dt_hours=1.0, population_raster=pop)
    assert name == "person_hours_extreme_heat_h"
    assert total == pytest.approx(20.0)


def test_ctsi_zero_when_below_baseline():
    stack = np.full((5, 3, 3), 20.0)
    ctsi = cumulative_thermal_stress_index(stack)
    assert np.all(ctsi == 0.0)


def test_ctsi_constant_36_for_10h_is_exactly_100():
    stack = np.full((10, 2, 2), 36.0)
    ctsi = cumulative_thermal_stress_index(stack, dt_hours=1.0)
    assert np.allclose(ctsi, 100.0)


def _two_building_setup(buffer_m=10.0, res=2.0):
    b1 = Point(0, 0).buffer(3.0)
    b2 = Point(40, 0).buffer(3.0)
    gdf = gpd.GeoDataFrame(
        {"osm_id": ["b1", "b2"], "height_m": [10.0, 10.0]}, geometry=[b1, b2], crs="EPSG:32618"
    )
    dom = build_domain(gdf, res_m=res, buffer_m=30.0)
    utci_peak = np.full(dom.shape, 40.0, dtype=np.float32)
    utci_mean = np.full(dom.shape, 30.0, dtype=np.float32)
    ctsi = np.full(dom.shape, 5.0, dtype=np.float32)
    results_df = pd.DataFrame({"osm_id": ["b1", "b2"], "total_eui_kwh_m2": [100.0, 150.0]})
    return gdf, dom, utci_peak, utci_mean, ctsi, results_df, buffer_m


def test_aggregate_to_parcels_preserves_count_and_no_nan():
    gdf, dom, utci_peak, utci_mean, ctsi, results_df, buffer_m = _two_building_setup()
    out = aggregate_to_parcels(gdf, results_df, dom, utci_peak, utci_mean, ctsi, buffer_m=buffer_m)
    assert len(out) == len(gdf)
    assert out["n_valid_surrounding_pixels"].min() > 0
    assert not out["utci_peak_c"].isna().any()
    assert not out["utci_mean_c"].isna().any()
    assert not out["ctsi_degc_h"].isna().any()
    assert set(out["total_eui_kwh_m2"]) == {100.0, 150.0}


def test_aggregate_to_parcels_values_match_uniform_field():
    gdf, dom, utci_peak, utci_mean, ctsi, results_df, buffer_m = _two_building_setup()
    out = aggregate_to_parcels(gdf, results_df, dom, utci_peak, utci_mean, ctsi, buffer_m=buffer_m)
    assert np.allclose(out["utci_peak_c"], 40.0)
    assert np.allclose(out["utci_mean_c"], 30.0)
    assert np.allclose(out["ctsi_degc_h"], 5.0)
