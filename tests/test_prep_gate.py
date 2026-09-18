from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from openubem import config
from openubem.simulation.parallel import PrepPhaseFailedError, run_neighbourhood


def _make_idf_manifest(osm_ids: list[str], statuses: list[str]) -> pd.DataFrame:
    n = len(osm_ids)
    return pd.DataFrame({
        "osm_id": osm_ids,
        "idf_path": [f"/fake/{oid}.idf" for oid in osm_ids],
        "generation_status": statuses,
        "num_zones": [2] * n,
        "data_quality_flag": [""] * n,
    })


def _make_enriched_gdf(osm_ids: list[str], epw_path: str = "/fake/boston.epw") -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"osm_id": osm_ids, "epw_path": [epw_path] * len(osm_ids)},
        geometry=[Point(0, 0)] * len(osm_ids),
    )


def _make_completed_dir(work_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "eplusout.end").write_text(
        "EnergyPlus Completed Successfully-- 0 Warning; 0 Severe Errors; Elapsed Time=...\n"
    )
    import sqlite3
    con = sqlite3.connect(str(work_dir / "eplusout.sql"))
    con.execute("CREATE TABLE ReportData (id INTEGER)")
    con.commit()
    con.close()


class TestPrepGateOffByDefault:
    def test_flag_default_is_false(self):
        assert config.PREP_ABORT_ON_FAILURE is False


class TestPrepGate:
    def test_flag_off_failures_present_no_raise(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "PREP_ABORT_ON_FAILURE", False)
        osm_ids = ["A", "B"]
        manifest = _make_idf_manifest(osm_ids, ["success", "failed_worker_exception"])
        gdf = _make_enriched_gdf(osm_ids)
        sim_root = tmp_path / "sim"
        _make_completed_dir(sim_root / "A")

        with patch("openubem.simulation.parallel._version_handshake", return_value="23.1.0"):
            result_df = run_neighbourhood(manifest, gdf, sim_root, n_jobs=1)

        assert len(result_df) == 2

    def test_flag_on_failures_present_raises_named(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "PREP_ABORT_ON_FAILURE", True)
        osm_ids = [f"B{i}" for i in range(7)]
        statuses = ["failed_worker_exception"] * 7
        manifest = _make_idf_manifest(osm_ids, statuses)
        gdf = _make_enriched_gdf(osm_ids)
        sim_root = tmp_path / "sim"

        with patch("openubem.simulation.parallel._version_handshake", return_value="23.1.0"):
            with pytest.raises(PrepPhaseFailedError) as excinfo:
                run_neighbourhood(manifest, gdf, sim_root, n_jobs=1)

        message = str(excinfo.value)
        assert "7" in message
        for oid in osm_ids[:5]:
            assert oid in message
        assert osm_ids[5] not in message
        assert osm_ids[6] not in message

    def test_flag_on_zero_failures_no_raise(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "PREP_ABORT_ON_FAILURE", True)
        osm_ids = ["A", "B"]
        manifest = _make_idf_manifest(osm_ids, ["success", "success"])
        gdf = _make_enriched_gdf(osm_ids)
        sim_root = tmp_path / "sim"
        for oid in osm_ids:
            _make_completed_dir(sim_root / oid)

        with patch("openubem.simulation.parallel._version_handshake", return_value="23.1.0"):
            result_df = run_neighbourhood(manifest, gdf, sim_root, n_jobs=1)

        assert len(result_df) == 2

    def test_raises_before_build_task_list(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "PREP_ABORT_ON_FAILURE", True)
        osm_ids = ["A"]
        manifest = _make_idf_manifest(osm_ids, ["failed_worker_exception"])
        gdf = _make_enriched_gdf(osm_ids)
        sim_root = tmp_path / "sim"

        with patch("openubem.simulation.parallel._version_handshake", return_value="23.1.0"):
            with patch("openubem.simulation.parallel.build_task_list") as mock_build:
                with pytest.raises(PrepPhaseFailedError):
                    run_neighbourhood(manifest, gdf, sim_root, n_jobs=1)

        mock_build.assert_not_called()
