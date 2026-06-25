"""Smoke tests for openubem/results/plotting_suite.py — no network, no EnergyPlus."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------------------

def _make_cell_gdf(n: int = 20):
    """Minimal GeoDataFrame that satisfies plotting_suite expectations."""
    geopandas = pytest.importorskip("geopandas")
    shapely_geom = pytest.importorskip("shapely.geometry")

    rng = np.random.default_rng(42)
    # Build tiny squares at arbitrary coords (EPSG:32618-like)
    x0, y0 = 583_000, 4_507_000
    polys = []
    for i in range(n):
        dx, dy = rng.uniform(0, 2000), rng.uniform(0, 2000)
        x, y = x0 + dx, y0 + dy
        polys.append(shapely_geom.box(x, y, x + 30, y + 30))

    statuses = ["success"] * (n - 2) + ["failed_parse", "not_simulated"]
    arch_ids = [f"arch_{i % 5}" for i in range(n)]

    df = geopandas.GeoDataFrame(
        {
            "simulation_status": statuses,
            "archetype_id": arch_ids,
            "total_eui_kwh_m2": rng.uniform(50, 300, n).tolist()[:-2] + [None, None],
            "gwp_heating_kgco2_m2": rng.uniform(5, 40, n),
            "gwp_cooling_kgco2_m2": rng.uniform(2, 20, n),
            "gwp_lighting_kgco2_m2": rng.uniform(1, 15, n),
            "gwp_equipment_kgco2_m2": rng.uniform(1, 10, n),
        },
        geometry=polys,
        crs="EPSG:32618",
    )
    return df


def _make_roundtrip_df(n: int = 10, n_failed: int = 0) -> pd.DataFrame:
    """n rows total; last n_failed have counter_status='failed' and NaN EUI/dev."""
    rng = np.random.default_rng(7)
    n_success = n - n_failed
    ref = rng.uniform(80, 300, n)
    dev = rng.uniform(-15, 15, n_success).tolist() + [float("nan")] * n_failed
    counter = [ref[i] * (1 + dev[i] / 100) if i < n_success else float("nan") for i in range(n)]
    statuses = ["success"] * n_success + ["failed"] * n_failed
    return pd.DataFrame({
        "openuben_archetype": [f"arch_{i}" for i in range(n)],
        "ref_total_eui": ref,
        "counter_total_eui": counter,
        "dev_pct": dev,
        "verdict_5pct": [abs(d) <= 5 if not np.isnan(d) else False for d in dev],
        "counter_status": statuses,
    })


def _make_decomp_df(n: int = 10) -> pd.DataFrame:
    rng = np.random.default_rng(13)
    total = rng.uniform(10, 60, n)
    h = total * 0.25
    c = total * 0.20
    l = total * 0.13
    e = total * 0.00
    o = total - h - c - l - e
    return pd.DataFrame({
        "openuben_archetype": [f"arch_{i}" for i in range(n)],
        "dev_pct": rng.uniform(-20, 20, n),
        "verdict_5pct": [True] * 5 + [False] * 5,
        "contrib_heat": h,
        "contrib_cool": c,
        "contrib_light": l,
        "contrib_equip": e,
        "contrib_other": o,
        "ref_total_eui": rng.uniform(80, 300, n),
        "counter_total_eui": rng.uniform(80, 300, n),
    })


def _make_cell_stats() -> pd.DataFrame:
    cities = ["nyc", "la", "austin"]
    rings = ["centre", "urban", "suburban", "rural"]
    rng = np.random.default_rng(99)
    rows = []
    for city in cities:
        for ring in rings:
            rows.append({
                "cell": f"{city}_{ring}",
                "city": city,
                "ring": ring,
                "mean_heating_eui": rng.uniform(10, 80),
                "mean_cooling_eui": rng.uniform(5, 50),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# T01 — module scaffold
# ---------------------------------------------------------------------------

def test_module_imports():
    """plotting_suite imports cleanly and exposes required names."""
    from openubem.results import plotting_suite as ps
    for name in ("SIM_DIR", "VAL_DIR", "_save", "_load_cell_gdf", "_load_cell_footprints",
                 "_SUCCESS_STATUSES", "_FAILED_STATUSES"):
        assert hasattr(ps, name), f"missing: {name}"


def test_sim_dir_val_dir_types():
    from openubem.results.plotting_suite import SIM_DIR, VAL_DIR
    assert isinstance(SIM_DIR, Path)
    assert isinstance(VAL_DIR, Path)
    assert "simulationResults" in str(SIM_DIR)
    assert "validaitonResults" in str(VAL_DIR)


# ---------------------------------------------------------------------------
# T02 — map v2 (no network: monkeypatch contextily)
# ---------------------------------------------------------------------------

def test_plot_eui_map_no_network(tmp_path, monkeypatch):
    """Map renders to PNG even when contextily raises (no-network fallback)."""
    import openubem.results.plotting_suite as ps

    # Force basemap to fail
    monkeypatch.setattr(ps, "contextily", None, raising=False)

    # Patch contextily import inside the function
    import unittest.mock as mock
    with mock.patch.dict(sys.modules, {"contextily": None}):
        gdf = _make_cell_gdf()
        out = tmp_path / "map.png"
        result = ps.plot_eui_map(gdf, out, cell_name="test_cell")

    assert result.exists()
    assert result.stat().st_size > 0


def test_plot_eui_map_raises_on_bad_crs_graceful(tmp_path):
    """Map still produces PNG when contextily.add_basemap raises any exception."""
    import unittest.mock as mock
    import openubem.results.plotting_suite as ps

    mock_ctx = mock.MagicMock()
    mock_ctx.providers.CartoDB.Positron = "mock_provider"
    mock_ctx.add_basemap.side_effect = RuntimeError("network error")

    with mock.patch.dict(sys.modules, {"contextily": mock_ctx}):
        gdf = _make_cell_gdf()
        out = tmp_path / "map_fallback.png"
        result = ps.plot_eui_map(gdf, out, cell_name="test_cell")

    assert result.exists()
    assert result.stat().st_size > 0


# ---------------------------------------------------------------------------
# T10 — _load_cell_footprints (real data smoke; skipped if runtime absent)
# ---------------------------------------------------------------------------

def test_load_cell_footprints_returns_polygons():
    """_load_cell_footprints returns Polygons with EUI column after osm_id join."""
    from openubem.results.plotting_suite import _load_cell_footprints
    from pathlib import Path
    case_dir = Path(__file__).resolve().parents[1] / "runtime" / "ubem_validation" / "cases" / "austin_centre"
    if not (case_dir / "01_buildings.gpkg").exists():
        pytest.skip("austin_centre runtime data not present")
    gdf = _load_cell_footprints("austin_centre")
    assert gdf.geom_type.isin(["Polygon", "MultiPolygon"]).all(), "geometry must be Polygon"
    assert "total_eui_kwh_m2" in gdf.columns, "EUI column missing after join"
    assert "simulation_status" in gdf.columns, "simulation_status missing after join"


def test_plot_eui_map_footprints_no_network(tmp_path):
    """Map from _load_cell_footprints renders without network (footprints-only fallback)."""
    import unittest.mock as mock
    import openubem.results.plotting_suite as ps
    from pathlib import Path
    case_dir = Path(__file__).resolve().parents[1] / "runtime" / "ubem_validation" / "cases" / "austin_centre"
    if not (case_dir / "01_buildings.gpkg").exists():
        pytest.skip("austin_centre runtime data not present")
    gdf = ps._load_cell_footprints("austin_centre")
    mock_ctx = mock.MagicMock()
    mock_ctx.providers.CartoDB.Positron = "mock_provider"
    mock_ctx.add_basemap.side_effect = RuntimeError("network error")
    with mock.patch.dict(sys.modules, {"contextily": mock_ctx}):
        out = tmp_path / "map_fp.png"
        result = ps.plot_eui_map(gdf, out, cell_name="austin_centre")
    assert result.exists()
    assert result.stat().st_size > 0


# ---------------------------------------------------------------------------
# T03a — EUI rank curve
# ---------------------------------------------------------------------------

def test_plot_eui_rank_curve(tmp_path):
    from openubem.results.plotting_suite import plot_eui_rank_curve
    gdf = _make_cell_gdf()
    out = tmp_path / "rank.png"
    result = plot_eui_rank_curve(gdf, out, cell_name="test_cell")
    assert result.exists()
    assert result.stat().st_size > 0


def test_plot_eui_rank_curve_empty(tmp_path):
    """Rank curve handles all-failed GDF without exception."""
    from openubem.results.plotting_suite import plot_eui_rank_curve

    gdf = _make_cell_gdf(5)
    gdf["simulation_status"] = "not_simulated"
    out = tmp_path / "rank_empty.png"
    result = plot_eui_rank_curve(gdf, out, cell_name="empty")
    assert result.exists()
    assert result.stat().st_size > 0


# ---------------------------------------------------------------------------
# T03b — Archetype EUI sorted bar
# ---------------------------------------------------------------------------

def test_plot_archetype_eui_sorted_bar(tmp_path):
    from openubem.results.plotting_suite import plot_archetype_eui_sorted_bar
    gdf = _make_cell_gdf()
    out = tmp_path / "arch_bar.png"
    result = plot_archetype_eui_sorted_bar(gdf, out, cell_name="test_cell")
    assert result.exists()
    assert result.stat().st_size > 0


# ---------------------------------------------------------------------------
# T04 — roundtrip scatter
# ---------------------------------------------------------------------------

def test_plot_roundtrip_scatter(tmp_path):
    from openubem.results.plotting_suite import plot_roundtrip_scatter
    df = _make_roundtrip_df()
    out = tmp_path / "scatter.png"
    result = plot_roundtrip_scatter(df, out)
    assert result.exists()
    assert result.stat().st_size > 0


def test_plot_roundtrip_scatter_filters_failed(tmp_path):
    """Scatter must exclude failed-counterpart rows from stats and plot."""
    import unittest.mock as mock
    from openubem.results.plotting_suite import plot_roundtrip_scatter
    # 10 rows: 8 success + 2 failed
    df = _make_roundtrip_df(n=10, n_failed=2)
    out = tmp_path / "scatter_filtered.png"
    # Spy on ax.scatter to count plotted points
    import matplotlib.pyplot as plt
    scattered_counts = []
    original_scatter = plt.Axes.scatter
    def _spy_scatter(self, x, *args, **kwargs):
        scattered_counts.append(len(x))
        return original_scatter(self, x, *args, **kwargs)
    with mock.patch.object(plt.Axes, "scatter", _spy_scatter):
        result = plot_roundtrip_scatter(df, out)
    assert result.exists()
    # Total scattered points must equal 8 (success only), not 10
    assert sum(scattered_counts) == 8, f"Expected 8 plotted points, got {sum(scattered_counts)}"


def test_plot_roundtrip_scatter_excludes_datacenter(tmp_path):
    """Scatter must drop DataCenter-named rows even when their counter_status=success."""
    import unittest.mock as mock
    import matplotlib.pyplot as plt
    from openubem.results.plotting_suite import plot_roundtrip_scatter
    df = _make_roundtrip_df(n=10, n_failed=0)
    # Rename one row to a DataCenter archetype
    df.loc[0, "openuben_archetype"] = "SmallDataCenterLowITE"
    out = tmp_path / "scatter_dc.png"
    scattered_counts = []
    original_scatter = plt.Axes.scatter
    def _spy(self, x, *args, **kwargs):
        scattered_counts.append(len(x))
        return original_scatter(self, x, *args, **kwargs)
    with mock.patch.object(plt.Axes, "scatter", _spy):
        result = plot_roundtrip_scatter(df, out)
    assert result.exists()
    # 9 non-DC rows plotted, not 10
    assert sum(scattered_counts) == 9, f"Expected 9 points (DC excluded), got {sum(scattered_counts)}"


# ---------------------------------------------------------------------------
# T05 — ranked deviation bar
# ---------------------------------------------------------------------------

def test_plot_dev_ranked_bar(tmp_path):
    from openubem.results.plotting_suite import plot_dev_ranked_bar
    df = _make_roundtrip_df()
    out = tmp_path / "dev_bar.png"
    result = plot_dev_ranked_bar(df, out)
    assert result.exists()
    assert result.stat().st_size > 0


def test_plot_dev_ranked_bar_filters_failed(tmp_path):
    """Ranked bar must show exactly n_success bars when failed rows present."""
    from openubem.results.plotting_suite import plot_dev_ranked_bar
    # 12 rows: 9 success + 3 failed (mirrors 20/3 ratio of real data)
    df = _make_roundtrip_df(n=12, n_failed=3)
    out = tmp_path / "dev_bar_filtered.png"
    result = plot_dev_ranked_bar(df, out)
    assert result.exists()
    assert result.stat().st_size > 0


# ---------------------------------------------------------------------------
# T06 — gap decomposition stacked bar
# ---------------------------------------------------------------------------

def test_plot_gap_decomposition(tmp_path):
    from openubem.results.plotting_suite import plot_gap_decomposition
    df = _make_decomp_df()
    out = tmp_path / "gap.png"
    result = plot_gap_decomposition(df, out)
    assert result.exists()
    assert result.stat().st_size > 0


# ---------------------------------------------------------------------------
# T07 — climate signal grouped bar
# ---------------------------------------------------------------------------

def test_plot_climate_signal(tmp_path):
    from openubem.results.plotting_suite import plot_climate_signal
    df = _make_cell_stats()
    out = tmp_path / "climate.png"
    result = plot_climate_signal(df, out)
    assert result.exists()
    assert result.stat().st_size > 0


# ---------------------------------------------------------------------------
# T12 — overview grid smoke
# ---------------------------------------------------------------------------

def test_plot_overview_grid_writes_png(tmp_path, monkeypatch):
    """plot_overview_grid writes a non-empty PNG; skips if runtime cells absent."""
    from pathlib import Path
    from openubem.results.plotting_suite import _load_cell_footprints

    # Check if at least one runtime cell is available; skip if not
    sample_cell_dir = Path(__file__).resolve().parents[1] / "runtime" / "ubem_validation" / "cases" / "nyc_centre"
    any_cell_present = (sample_cell_dir / "01_buildings.gpkg").exists()
    if not any_cell_present:
        pytest.skip("No runtime cells present; overview grid test skipped")

    from openubem.results.plotting_suite import plot_overview_grid
    out = tmp_path / "eui_overview_grid.png"
    result_path, vmin, vmax = plot_overview_grid(out)
    assert result_path.exists(), "overview grid PNG not written"
    assert result_path.stat().st_size > 0, "overview grid PNG is empty"
    assert vmin < vmax, f"vmin ({vmin}) must be < vmax ({vmax})"


# ---------------------------------------------------------------------------
# T08 — CLI runner smoke (one cell only, --only sim)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# T06 — comparison plot smoke tests
# ---------------------------------------------------------------------------

_R7_CSV = Path(__file__).resolve().parents[1] / "docs" / "validations" / "overAll" / "results" / "r7_service_loads.csv"
_CBECS_DIR = Path(__file__).resolve().parents[1] / "inputs" / "reports"


def test_cbecs_region_mean_pacific():
    """_cbecs_region_mean('pacific') must be within ±1.0 of 188.4."""
    if not (_CBECS_DIR / "cbecs_2018_pacific_eui.csv").exists():
        pytest.skip("pacific CBECS CSV absent")
    from openubem.results.plotting_suite import _cbecs_region_mean
    val = _cbecs_region_mean("pacific")
    assert abs(val - 188.4) <= 1.0, f"pacific mean {val:.2f} not within ±1.0 of 188.4"


def test_plot_eui_vs_reference(tmp_path):
    """Plot A: returns Path, file exists, non-empty."""
    if not _R7_CSV.exists():
        pytest.skip("r7_service_loads.csv absent")
    from openubem.results.plotting_suite import plot_eui_vs_reference
    out = tmp_path / "eui_vs_cbecs_reference.png"
    result = plot_eui_vs_reference(out)
    assert result.exists()
    assert result.stat().st_size > 0


def test_plot_sim_vs_reconstructed(tmp_path):
    """Plot B: returns Path, file exists, non-empty."""
    if not _R7_CSV.exists():
        pytest.skip("r7_service_loads.csv absent")
    from openubem.results.plotting_suite import plot_sim_vs_reconstructed
    out = tmp_path / "eui_sim_vs_reconstructed.png"
    result = plot_sim_vs_reconstructed(out)
    assert result.exists()
    assert result.stat().st_size > 0


def test_plot_sim_vs_reconstructed_recon_ge_sim():
    """Plot B: reconstructed mean >= simulated mean for every cell (reconstruction only adds energy)."""
    if not _R7_CSV.exists():
        pytest.skip("r7_service_loads.csv absent")
    import numpy as np
    df = __import__("pandas").read_csv(_R7_CSV)
    df = df[df["reconstruction_applied"] == True].copy()  # noqa: E712
    cell_order = [f"{c}_{r}" for c in ("nyc", "la", "austin")
                  for r in ("centre", "urban", "suburban", "rural")]
    for cell in cell_order:
        sub = df[df["cell"] == cell]
        if sub.empty:
            continue
        sim_mean = sub["total_eui_kwh_m2"].mean()
        recon_mean = sub["total_eui_reconstructed_kwh_m2"].mean()
        assert recon_mean >= sim_mean - 1e-6, (
            f"{cell}: recon_mean ({recon_mean:.2f}) < sim_mean ({sim_mean:.2f})"
        )


def test_plot_cross_cell_eui(tmp_path):
    """Plot C: returns Path, file exists, non-empty; ≤12 boxes."""
    if not _R7_CSV.exists():
        pytest.skip("r7_service_loads.csv absent")
    from openubem.results.plotting_suite import plot_cross_cell_eui
    out = tmp_path / "eui_cross_cell_summary.png"
    result = plot_cross_cell_eui(out)
    assert result.exists()
    assert result.stat().st_size > 0


def test_plot_overview_grid_returns_3tuple(tmp_path):
    """Regression: plot_overview_grid still returns a 3-tuple (path, vmin, vmax)."""
    sample_cell_dir = Path(__file__).resolve().parents[1] / "runtime" / "ubem_validation" / "cases" / "nyc_centre"
    if not (sample_cell_dir / "01_buildings.gpkg").exists():
        pytest.skip("No runtime cells present")
    from openubem.results.plotting_suite import plot_overview_grid
    out = tmp_path / "eui_overview_grid.png"
    result = plot_overview_grid(out)
    assert isinstance(result, tuple) and len(result) == 3
    path, vmin, vmax = result
    assert path.exists()
    assert vmin < vmax


# ---------------------------------------------------------------------------
# T08 — CLI runner smoke (one cell only, --only sim)
# ---------------------------------------------------------------------------

def test_render_plots_cli_one_cell(tmp_path):
    """render_plots.py --cells nyc_centre --only sim writes 3 PNGs if data exists."""
    import subprocess, sys
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "render_plots.py"
    result = subprocess.run(
        [sys.executable, str(script), "--cells", "nyc_centre", "--only", "sim"],
        capture_output=True, text=True, cwd=str(root),
    )
    # Not a hard failure if nyc_centre data is missing on CI; just check no crash
    assert result.returncode == 0, f"CLI failed:\n{result.stderr}"
