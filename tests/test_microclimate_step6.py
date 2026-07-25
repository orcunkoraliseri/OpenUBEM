import sys
from pathlib import Path

import numpy as np
import rasterio
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent / "fixtures"))
from synthetic_canyon import build_canyon_gdf  # noqa: E402

from openubem.microclimate import run_step6

SYNTHETIC_EPW = Path(__file__).parent / "fixtures" / "synthetic.epw"
_DESIGN_HOURS = [(7, 15, 12), (7, 15, 13), (7, 15, 14)]  # 3-hour window, T18's own "How to test"


def _make_run_dir(tmp_path, legacy_name: bool = True) -> Path:
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    gdf = build_canyon_gdf(height_m=10.0, width_m=10.0, block_len=300.0)
    name = "01_buildings.gpkg" if legacy_name else "01_buildings_clean.gpkg"
    gdf.to_file(run_dir / name, driver="GPKG")
    return run_dir


def _run(tmp_path, **kwargs):
    run_dir = _make_run_dir(tmp_path)
    output_dir = tmp_path / "out"
    return run_step6(
        run_dir,
        output_dir=output_dir,
        epw_path=SYNTHETIC_EPW,
        res_m=8.0,
        buffer_m=30.0,
        window_mode="design_hours",
        design_hours=_DESIGN_HOURS,
        **kwargs,
    )


def test_run_step6_all_artifacts_exist(tmp_path):
    out = _run(tmp_path)
    expected = [
        "06_mc_domain_dsm.tif", "06_mc_svf.tif", "06_mc_horizon.npz",
        "06_mc_tmrt_hourly.tif", "06_mc_utci_hourly.tif", "06_mc_wind_1p1m_hourly.tif",
        "06_mc_ta_hourly.tif", "06_mc_flags_hourly.tif",
        "06_mc_utci_peak.tif", "06_mc_utci_mean.tif",
        "06_mc_utci_peak_class.tif", "06_mc_utci_mean_class.tif",
        "06_mc_ctsi.tif", "06_mc_summary.gpkg", "06_mc_exposure_metrics.json",
        "06_mc_manifest.parquet",
    ]
    for name in expected:
        assert (out / name).exists(), f"missing artifact {name}"


def test_run_step6_band_count_equals_hour_count(tmp_path):
    out = _run(tmp_path)
    for name in ("06_mc_tmrt_hourly.tif", "06_mc_utci_hourly.tif", "06_mc_wind_1p1m_hourly.tif",
                 "06_mc_ta_hourly.tif", "06_mc_flags_hourly.tif"):
        with rasterio.open(out / name) as src:
            assert src.count == len(_DESIGN_HOURS), name
            assert src.descriptions[0] is not None and "T" in src.descriptions[0]  # ISO timestamp


def test_run_step6_manifest_round_trips(tmp_path):
    out = _run(tmp_path)
    mf = pd.read_parquet(out / "06_mc_manifest.parquet")
    assert len(mf) == 1
    row = mf.iloc[0]
    assert row["window_n_hours"] == len(_DESIGN_HOURS)
    assert row["vegetation_tier"] == "none"
    assert row["wall_temp_tier"] == "empirical"
    assert row["wind_tier"] == "cost730"
    assert row["epw_resolution_step"] == "explicit_epw_path"
    assert row["n_buildings"] == 2


def test_run_step6_determinism_byte_identical(tmp_path):
    out1 = _run(tmp_path / "a")
    out2 = _run(tmp_path / "b")
    for name in ("06_mc_utci_peak.tif", "06_mc_utci_mean.tif", "06_mc_tmrt_hourly.tif", "06_mc_svf.tif"):
        b1 = (out1 / name).read_bytes()
        b2 = (out2 / name).read_bytes()
        assert b1 == b2, f"{name} not byte-identical across re-run"


def test_run_step6_accepts_legacy_and_clean_buildings_name(tmp_path):
    run_dir = tmp_path / "run_clean"
    run_dir.mkdir()
    gdf = build_canyon_gdf(height_m=10.0, width_m=10.0, block_len=300.0)
    gdf.to_file(run_dir / "01_buildings_clean.gpkg", driver="GPKG")
    out = run_step6(
        run_dir, output_dir=tmp_path / "out_clean", epw_path=SYNTHETIC_EPW,
        res_m=8.0, buffer_m=30.0, window_mode="design_hours", design_hours=_DESIGN_HOURS,
    )
    assert (out / "06_mc_utci_peak.tif").exists()


def test_run_step6_exposure_metrics_json_has_required_keys(tmp_path):
    out = _run(tmp_path)
    import json
    metrics = json.loads((out / "06_mc_exposure_metrics.json").read_text())
    assert "area_hours_extreme_heat_m2h" in metrics
    assert "ctsi_mean_degc_h" in metrics
    assert "threshold_c" in metrics and metrics["threshold_c"] == 46.0


def test_run_step6_summary_gpkg_preserves_building_count(tmp_path):
    out = _run(tmp_path)
    import geopandas as gpd
    summary = gpd.read_file(out / "06_mc_summary.gpkg")
    assert len(summary) == 2


def test_run_step6_macdonald_wind_tier_runs(tmp_path):
    out = _run(tmp_path, wind_tier="macdonald")
    with rasterio.open(out / "06_mc_wind_1p1m_hourly.tif") as src:
        assert src.count == len(_DESIGN_HOURS)


def test_run_step6_tier2_wall_temps_wiring_with_mocked_resim(tmp_path, monkeypatch):
    """T13's resim.py is exercised end-to-end elsewhere (test_microclimate_resim.py); this test
    exercises T18's own GLUE — call order, sql-hour-convention conversion (ts.hour+1, T02's own
    "hour 24 -> 23:00" mapping inverted), and the cos(incidence)-weighted reduction to one scalar
    per hour — via mocks, the same style test_microclimate_resim.py itself already uses (no real
    EnergyPlus invocation, matching T22's own scope which does not name wall_temp_tier=energyplus)."""
    run_dir = _make_run_dir(tmp_path)
    (run_dir / f"{run_dir.name}_step3_idfs_archive.zip").write_bytes(b"dummy-not-a-real-zip")

    from openubem.microclimate import resim as resim_mod

    calls = {}

    def fake_extract(archive, scratch_dir):
        calls["extract_archive"] = archive
        return [Path("b1.idf")]

    def fake_run_resim(idf_paths, epw_path, work_root, **kwargs):
        calls["run_resim_kwargs"] = kwargs
        return [{"status": "success", "sql_path": "b1.sql"}]

    def fake_harvest(sql_paths_by_building):
        calls["sql_paths_by_building"] = sql_paths_by_building
        # ts.hour for _DESIGN_HOURS = 12,13,14 -> sql_hour = ts.hour+1 = 13,14,15
        rows = [
            {"building_id": "b1", "surface_name": "W1", "azimuth_deg": 180.0,
             "Month": 7, "Day": 15, "Hour": h, "t_wall_c": 40.0}
            for h in (13, 14, 15)
        ]
        return pd.DataFrame(rows)

    def fake_quarantine(work_root, keep=False):
        calls["quarantine_keep"] = keep

    monkeypatch.setattr(resim_mod, "extract_idf_archive", fake_extract)
    monkeypatch.setattr(resim_mod, "run_resim_side_leg", fake_run_resim)
    monkeypatch.setattr(resim_mod, "harvest_wall_temperatures", fake_harvest)
    monkeypatch.setattr(resim_mod, "quarantine_or_delete", fake_quarantine)

    out = run_step6(
        run_dir, output_dir=tmp_path / "out_tier2", epw_path=SYNTHETIC_EPW,
        res_m=8.0, buffer_m=30.0, window_mode="design_hours", design_hours=_DESIGN_HOURS,
        wall_temp_tier="energyplus",
    )
    assert "extract_archive" in calls
    assert set(calls["sql_paths_by_building"].keys()) == {"b1"}
    assert calls["sql_paths_by_building"]["b1"][0] == "b1.sql"
    assert calls["quarantine_keep"] is False
    mf = pd.read_parquet(out / "06_mc_manifest.parquet")
    row = mf.iloc[0]
    assert row["wall_temp_tier"] == "energyplus"
    assert row["tier2_n_hours_harvested"] == len(_DESIGN_HOURS)


def test_run_step6_svf_cache_reused_on_rerun(tmp_path):
    run_dir = _make_run_dir(tmp_path)
    output_dir = tmp_path / "out"
    run_step6(
        run_dir, output_dir=output_dir, epw_path=SYNTHETIC_EPW, res_m=8.0, buffer_m=30.0,
        window_mode="design_hours", design_hours=_DESIGN_HOURS,
    )
    cache_mtime_1 = (output_dir / "06_mc_horizon.npz").stat().st_mtime_ns
    run_step6(
        run_dir, output_dir=output_dir, epw_path=SYNTHETIC_EPW, res_m=8.0, buffer_m=30.0,
        window_mode="design_hours", design_hours=[(7, 16, 12)],
    )
    cache_bytes_1 = (output_dir / "06_mc_horizon.npz").read_bytes()
    run_step6(
        run_dir, output_dir=output_dir, epw_path=SYNTHETIC_EPW, res_m=8.0, buffer_m=30.0,
        window_mode="design_hours", design_hours=[(7, 17, 12)],
    )
    cache_bytes_2 = (output_dir / "06_mc_horizon.npz").read_bytes()
    assert cache_bytes_1 == cache_bytes_2  # same domain -> identical cached SVF/horizon content
