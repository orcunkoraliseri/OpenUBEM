import numpy as np
import geopandas as gpd
from shapely.geometry import Point

from openubem.microclimate.domain import build_domain
from openubem.microclimate.figures import (
    plot_diurnal_curve,
    plot_five_panel,
    plot_stress_histogram,
    required_caption,
)


def _dom(res=5.0, buffer_m=30.0):
    gdf = gpd.GeoDataFrame({"osm_id": ["b1"], "height_m": [10.0]}, geometry=[Point(0, 0).buffer(4.0)], crs="EPSG:32618")
    return build_domain(gdf, res_m=res, buffer_m=buffer_m)


def test_required_caption_contains_all_fields():
    cap = required_caption(
        cell="nyc_centre", date_hour="2001-07-28 12:00", res_m=2.0,
        vegetation_tier="none", wall_temp_tier="empirical", wind_tier="cost730",
    )
    for expected in ["nyc_centre", "2001-07-28 12:00", "res=2.0 m", "vegetation_tier=none",
                      "wall_temp_tier=empirical", "wind_tier=cost730"]:
        assert expected in cap


def test_plot_five_panel_writes_nontrivial_file_with_10_class_colourbar(tmp_path):
    dom = _dom()
    shape = dom.shape
    rng = np.random.default_rng(0)
    ta = np.full(shape, 34.0)
    e = np.full(shape, 2.4)
    v = rng.uniform(0.5, 3.0, size=shape)
    tmrt = rng.uniform(30.0, 65.0, size=shape)
    utci = rng.uniform(20.0, 45.0, size=shape)
    caption = required_caption(cell="test", date_hour="2001-01-01 12:00", res_m=dom.res_m,
                                vegetation_tier="none", wall_temp_tier="empirical", wind_tier="cost730")
    out = plot_five_panel(ta_c=ta, e_kpa=e, v_1p1=v, tmrt_c=tmrt, utci_c=utci, domain=dom,
                           caption=caption, out_path=tmp_path / "five_panel.png")
    assert out.exists()
    assert out.stat().st_size > 5_000


def test_plot_diurnal_curve_writes_file(tmp_path):
    dom = _dom()
    n_hours = 4
    stack = np.random.default_rng(1).uniform(20.0, 45.0, size=(n_hours, *dom.shape))
    timestamps = [f"2001-07-28T{h:02d}:00:00" for h in range(9, 13)]
    r, c = dom.shape[0] // 2, dom.shape[1] // 2
    caption = required_caption(cell="test", date_hour="2001-07-28", res_m=dom.res_m,
                                vegetation_tier="none", wall_temp_tier="empirical", wind_tier="cost730")
    out = plot_diurnal_curve(utci_stack_c=stack, timestamps=timestamps, points_rc={"midpoint": (r, c)},
                              caption=caption, out_path=tmp_path / "diurnal.png")
    assert out.exists()
    assert out.stat().st_size > 3_000


def test_plot_stress_histogram_writes_file(tmp_path):
    dom = _dom()
    utci = np.random.default_rng(2).uniform(-10.0, 45.0, size=dom.shape)
    caption = required_caption(cell="test", date_hour="2001-07-28 12:00", res_m=dom.res_m,
                                vegetation_tier="none", wall_temp_tier="empirical", wind_tier="cost730")
    out = plot_stress_histogram(utci_c=utci, domain=dom, res_m=dom.res_m, caption=caption,
                                 out_path=tmp_path / "hist.png")
    assert out.exists()
    assert out.stat().st_size > 3_000
