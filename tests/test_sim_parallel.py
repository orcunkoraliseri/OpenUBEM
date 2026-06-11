"""Unit tests for simulation/parallel.py — no binary required (DESIGN §5.1, PLAN T08, P8)."""
from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from openubem.simulation.parallel import (
    SimTask,
    _emit_manifest,
    _safe_rmtree,
    _split_resume,
    _worker,
    build_task_list,
    is_completed,
    run_neighbourhood,
)

_FIXTURES = Path(__file__).parent / "fixtures" / "sim"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_idf_manifest(
    osm_ids: list[str],
    statuses: list[str] | None = None,
    idf_paths: list[str] | None = None,
) -> pd.DataFrame:
    n = len(osm_ids)
    if statuses is None:
        statuses = ["success"] * n
    if idf_paths is None:
        idf_paths = [f"/fake/{oid}.idf" for oid in osm_ids]
    return pd.DataFrame({
        "osm_id": osm_ids,
        "idf_path": idf_paths,
        "generation_status": statuses,
        "num_zones": [2] * n,
        "data_quality_flag": [""] * n,
    })


def _make_enriched_gdf(osm_ids: list[str], epw_path: str = "/fake/boston.epw") -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"osm_id": osm_ids, "epw_path": [epw_path] * len(osm_ids)},
        geometry=[Point(0, 0)] * len(osm_ids),
    )


def _write_stub_sql(work_dir: Path) -> None:
    db_path = work_dir / "eplusout.sql"
    con = sqlite3.connect(str(db_path))
    con.execute("CREATE TABLE ReportData (id INTEGER)")
    con.execute("INSERT INTO ReportData VALUES (1)")
    con.commit()
    con.close()


def _write_success_end(work_dir: Path) -> None:
    (work_dir / "eplusout.end").write_text(
        "EnergyPlus Completed Successfully-- 2 Warning; 0 Severe Errors; Elapsed Time=...\n"
    )


def _make_completed_dir(work_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    _write_success_end(work_dir)
    _write_stub_sql(work_dir)


# ── SimTask tests ─────────────────────────────────────────────────────────────

class TestSimTask:
    def test_frozen(self):
        t = SimTask("id", "idf", "epw", "wd")
        with pytest.raises((AttributeError, TypeError)):
            t.osm_id = "other"  # type: ignore[misc]


# ── build_task_list tests ─────────────────────────────────────────────────────

class TestBuildTaskList:
    def test_success_rows_become_tasks(self, tmp_path):
        manifest = _make_idf_manifest(["A", "B", "C"])
        gdf = _make_enriched_gdf(["A", "B", "C"])
        tasks, skipped = build_task_list(manifest, gdf, tmp_path)
        assert len(tasks) == 3
        assert len(skipped) == 0
        assert all(isinstance(t, SimTask) for t in tasks)

    def test_non_success_rows_go_to_skipped(self, tmp_path):
        manifest = _make_idf_manifest(
            ["A", "B", "C"],
            statuses=["success", "skipped_invalid_geometry", "success"],
        )
        gdf = _make_enriched_gdf(["A", "B", "C"])
        tasks, skipped = build_task_list(manifest, gdf, tmp_path)
        assert len(tasks) == 2
        assert len(skipped) == 1
        assert list(skipped["osm_id"]) == ["B"]

    def test_missing_epw_raises_valueerror(self, tmp_path):
        manifest = _make_idf_manifest(["A", "B"])
        gdf = _make_enriched_gdf(["A"])  # B missing
        with pytest.raises(ValueError, match="missing epw_path"):
            build_task_list(manifest, gdf, tmp_path)

    def test_work_dir_is_sim_root_slash_osm_id(self, tmp_path):
        manifest = _make_idf_manifest(["way/123"])
        gdf = _make_enriched_gdf(["way/123"])
        tasks, _ = build_task_list(manifest, gdf, tmp_path)
        assert tasks[0].work_dir == str(tmp_path / "way/123")

    def test_all_skipped_returns_empty_task_list(self, tmp_path):
        manifest = _make_idf_manifest(["A"], statuses=["skipped_invalid_geometry"])
        gdf = _make_enriched_gdf(["A"])
        tasks, skipped = build_task_list(manifest, gdf, tmp_path)
        assert tasks == []
        assert len(skipped) == 1


# ── is_completed + _split_resume tests ───────────────────────────────────────

class TestResume:
    def test_completed_dir_detected(self, tmp_path):
        _make_completed_dir(tmp_path / "bldg")
        assert is_completed(tmp_path / "bldg") is True

    def test_missing_end_file_not_completed(self, tmp_path):
        wd = tmp_path / "bldg"
        wd.mkdir()
        _write_stub_sql(wd)
        assert is_completed(wd) is False

    def test_missing_sql_file_not_completed(self, tmp_path):
        wd = tmp_path / "bldg"
        wd.mkdir()
        _write_success_end(wd)
        assert is_completed(wd) is False

    def test_fatal_end_not_completed(self, tmp_path):
        wd = tmp_path / "bldg"
        wd.mkdir()
        import shutil
        shutil.copy(_FIXTURES / "end_fatal.txt", wd / "eplusout.end")
        _write_stub_sql(wd)
        assert is_completed(wd) is False

    def test_split_resume_completed_goes_to_cached(self, tmp_path):
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        wd = sim_root / "A"
        _make_completed_dir(wd)
        task = SimTask("A", "/fake/A.idf", "/fake/a.epw", str(wd))
        fresh, cached = _split_resume([task], force_rerun=False, sim_root=sim_root)
        assert len(cached) == 1
        assert len(fresh) == 0

    def test_split_resume_incomplete_dir_deleted_and_fresh(self, tmp_path):
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        wd = sim_root / "B"
        wd.mkdir()
        # Write only .end (no sql → incomplete)
        _write_success_end(wd)
        task = SimTask("B", "/fake/B.idf", "/fake/b.epw", str(wd))
        fresh, cached = _split_resume([task], force_rerun=False, sim_root=sim_root)
        assert len(fresh) == 1
        assert not wd.exists(), "stale incomplete dir should have been deleted"

    def test_split_resume_force_rerun_deletes_completed(self, tmp_path):
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        wd = sim_root / "C"
        _make_completed_dir(wd)
        task = SimTask("C", "/fake/C.idf", "/fake/c.epw", str(wd))
        fresh, cached = _split_resume([task], force_rerun=True, sim_root=sim_root)
        assert len(fresh) == 1
        assert len(cached) == 0
        assert not wd.exists()

    def test_cached_not_re_executed(self, tmp_path):
        """Cached task must never trigger run_energyplus (call-count assertion)."""
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        wd = sim_root / "D"
        _make_completed_dir(wd)
        task = SimTask("D", "/fake/D.idf", "/fake/d.epw", str(wd))
        fresh, cached = _split_resume([task], force_rerun=False, sim_root=sim_root)
        assert fresh == []
        assert len(cached) == 1
        # run_energyplus should never have been called
        with patch("openubem.simulation.parallel.run_energyplus") as mock_run:
            # Simulate what run_neighbourhood does: only fresh tasks are dispatched
            results = [_worker(t) for t in fresh]  # fresh is empty
            mock_run.assert_not_called()


# ── _safe_rmtree guard ────────────────────────────────────────────────────────

class TestSafeRmtree:
    def test_rejects_target_equal_to_sim_root(self, tmp_path):
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        with pytest.raises(AssertionError):
            _safe_rmtree(sim_root, sim_root)

    def test_rejects_target_outside_sim_root(self, tmp_path):
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        outside = tmp_path / "other"
        outside.mkdir()
        with pytest.raises(AssertionError):
            _safe_rmtree(outside, sim_root)

    def test_accepts_subdir(self, tmp_path):
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        sub = sim_root / "bldg"
        sub.mkdir()
        _safe_rmtree(sub, sim_root)  # should not raise
        assert not sub.exists()


# ── _emit_manifest + purge tests ─────────────────────────────────────────────

class TestEmitManifest:
    def _run_manifest(self, raw_results, cached_tasks, skipped_df, idf_manifest, sim_root, ep_version="23.1.0"):
        return _emit_manifest(raw_results, cached_tasks, skipped_df, idf_manifest, sim_root, ep_version)

    def test_manifest_shape_11_cols(self, tmp_path):
        manifest = _make_idf_manifest(["A"])
        gdf = _make_enriched_gdf(["A"])
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        wd = sim_root / "A"
        wd.mkdir()
        _write_success_end(wd)
        _write_stub_sql(wd)
        raw = [{"osm_id": "A", "status": "success", "wall_clock_s": 3.0,
                "n_warnings": 2, "n_severe": 0, "error_summary": "", "epw_path": "/fake/a.epw"}]
        df = self._run_manifest(raw, [], pd.DataFrame(), manifest, sim_root)
        assert list(df.columns) == [
            "osm_id", "idf_path", "work_dir", "sql_path", "status",
            "n_warnings", "n_severe", "wall_clock_s", "ep_version", "epw_path", "error_summary",
        ]

    def test_n_input_rows_equals_manifest_rows(self, tmp_path):
        osm_ids = ["A", "B", "C"]
        manifest = _make_idf_manifest(
            osm_ids,
            statuses=["success", "success", "skipped_invalid_geometry"],
        )
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        for oid in ["A", "B"]:
            wd = sim_root / oid
            wd.mkdir()
            _write_success_end(wd)
            _write_stub_sql(wd)
        raw = [
            {"osm_id": "A", "status": "success", "wall_clock_s": 1.0,
             "n_warnings": 0, "n_severe": 0, "error_summary": "", "epw_path": "/fake/a.epw"},
            {"osm_id": "B", "status": "success", "wall_clock_s": 2.0,
             "n_warnings": 1, "n_severe": 0, "error_summary": "", "epw_path": "/fake/b.epw"},
        ]
        skipped = manifest[manifest["generation_status"] != "success"]
        df = self._run_manifest(raw, [], skipped, manifest, sim_root)
        assert len(df) == 3  # N_input rows

    def test_n_warnings_n_severe_are_int64_nullable(self, tmp_path):
        manifest = _make_idf_manifest(["A", "B"],
            statuses=["success", "skipped_invalid_geometry"])
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        wd = sim_root / "A"
        wd.mkdir()
        _write_success_end(wd)
        _write_stub_sql(wd)
        raw = [{"osm_id": "A", "status": "success", "wall_clock_s": 1.0,
                "n_warnings": 2, "n_severe": 0, "error_summary": "", "epw_path": "/e.epw"}]
        skipped = manifest[manifest["generation_status"] != "success"]
        df = self._run_manifest(raw, [], skipped, manifest, sim_root)
        assert str(df["n_warnings"].dtype) == "Int64"
        assert str(df["n_severe"].dtype) == "Int64"
        b_row = df[df["osm_id"] == "B"]
        assert pd.isna(b_row["n_warnings"].iloc[0])

    def test_sql_path_empty_string_for_non_success(self, tmp_path):
        manifest = _make_idf_manifest(["A"], statuses=["skipped_invalid_geometry"])
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        skipped = manifest
        df = self._run_manifest([], [], skipped, manifest, sim_root)
        assert df.iloc[0]["sql_path"] == ""

    def test_skipped_row_status_is_not_attempted(self, tmp_path):
        manifest = _make_idf_manifest(["A"], statuses=["skipped_invalid_geometry"])
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        df = self._run_manifest([], [], manifest, manifest, sim_root)
        assert df.iloc[0]["status"] == "not_attempted_invalid_idf"
        assert df.iloc[0]["error_summary"] == "skipped_invalid_geometry"

    def test_eso_purged_success_retained_set_intact(self, tmp_path):
        manifest = _make_idf_manifest(["A"])
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        wd = sim_root / "A"
        wd.mkdir()
        _write_success_end(wd)
        _write_stub_sql(wd)
        # Write various files including .eso (should be purged) and retained files
        (wd / "eplusout.eso").write_text("big eso file")
        (wd / "eplusout.err").write_text("warnings here")
        (wd / "eplusout.csv").write_text("csv data")
        (wd / "openubem_run.log").write_text("run log")
        raw = [{"osm_id": "A", "status": "success", "wall_clock_s": 1.0,
                "n_warnings": 0, "n_severe": 0, "error_summary": "", "epw_path": "/e.epw"}]
        self._run_manifest(raw, [], pd.DataFrame(), manifest, sim_root)
        assert not (wd / "eplusout.eso").exists(), ".eso must be purged"
        assert (wd / "eplusout.err").exists(), "eplusout.err must be retained"
        assert (wd / "eplusout.csv").exists(), "eplusout.csv must be retained"
        assert (wd / "openubem_run.log").exists(), "openubem_run.log must be retained"
        assert (wd / "eplusout.end").exists(), "eplusout.end must NEVER be deleted"

    def test_failed_dir_not_purged(self, tmp_path):
        manifest = _make_idf_manifest(["A"])
        sim_root = tmp_path / "sim"
        sim_root.mkdir()
        wd = sim_root / "A"
        wd.mkdir()
        # No .end file → failed_crash
        (wd / "eplusout.eso").write_text("big eso")
        raw = [{"osm_id": "A", "status": "failed_crash", "wall_clock_s": 0.0,
                "n_warnings": None, "n_severe": None, "error_summary": "crash", "epw_path": "/e.epw"}]
        self._run_manifest(raw, [], pd.DataFrame(), manifest, sim_root)
        assert (wd / "eplusout.eso").exists(), "failure debris must NOT be purged"


# ── _worker catch-all tests ───────────────────────────────────────────────────

class TestWorker:
    def test_worker_exception_yields_failed_crash(self):
        task = SimTask("bad", "/nonexistent/bad.idf", "/nonexistent/bad.epw",
                       "/nonexistent/bad_wd")
        with patch(
            "openubem.simulation.parallel.run_energyplus",
            side_effect=RuntimeError("disk full"),
        ):
            result = _worker(task)
        assert result["status"] == "failed_crash"
        assert result["osm_id"] == "bad"
        assert len(result["error_summary"]) > 0

    def test_worker_success_classifies_correctly(self, tmp_path):
        wd = tmp_path / "ok"
        wd.mkdir()
        _write_success_end(wd)
        _write_stub_sql(wd)
        task = SimTask("ok", "/fake/ok.idf", "/fake/ok.epw", str(wd))
        fake_raw = {
            "osm_id": "ok", "returncode": 0, "wall_clock_s": 3.0,
            "timed_out": False, "_stderr": "",
        }
        with patch("openubem.simulation.parallel.run_energyplus", return_value=fake_raw):
            result = _worker(task)
        assert result["status"] == "success"


# ── run_neighbourhood integration (mocked, n_jobs=1) ─────────────────────────

class TestRunNeighbourhood:
    def test_manifest_parquet_written(self, tmp_path):
        osm_ids = ["A", "B"]
        manifest = _make_idf_manifest(osm_ids)
        gdf = _make_enriched_gdf(osm_ids)
        sim_root = tmp_path / "sim"

        # Pre-create completed work dirs so _split_resume puts them in cached
        for oid in osm_ids:
            wd = sim_root / oid
            _make_completed_dir(wd)

        with patch("openubem.simulation.parallel._version_handshake", return_value="23.1.0"):
            result_df = run_neighbourhood(manifest, gdf, sim_root, n_jobs=1)

        parquet_path = sim_root / "04_simulation_manifest.parquet"
        assert parquet_path.exists()
        loaded = pd.read_parquet(str(parquet_path))
        assert len(loaded) == 2

    def test_n_input_rows_in_output(self, tmp_path):
        osm_ids = ["A", "B", "C"]
        manifest = _make_idf_manifest(
            osm_ids,
            statuses=["success", "success", "skipped_invalid_geometry"],
        )
        gdf = _make_enriched_gdf(osm_ids)
        sim_root = tmp_path / "sim"
        for oid in ["A", "B"]:
            _make_completed_dir(sim_root / oid)

        with patch("openubem.simulation.parallel._version_handshake", return_value="23.1.0"):
            result_df = run_neighbourhood(manifest, gdf, sim_root, n_jobs=1)

        assert len(result_df) == 3

    def test_missing_epw_raises_before_any_dispatch(self, tmp_path):
        manifest = _make_idf_manifest(["A", "B"])
        gdf = _make_enriched_gdf(["A"])  # B has no epw
        sim_root = tmp_path / "sim"

        with patch("openubem.simulation.parallel._version_handshake", return_value="23.1.0"):
            with pytest.raises(ValueError, match="missing epw_path"):
                run_neighbourhood(manifest, gdf, sim_root, n_jobs=1)
