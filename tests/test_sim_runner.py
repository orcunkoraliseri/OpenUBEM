"""Unit tests for simulation/runner.py — no binary required (DESIGN §5.1, PLAN T08, P8)."""
from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openubem.simulation.runner import (
    _version_handshake,
    classify_outcome,
    run_energyplus,
)
from openubem.simulation.parallel import SimTask

_FIXTURES = Path(__file__).parent / "fixtures" / "sim"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_task(tmp_path: Path, osm_id: str = "way/test") -> SimTask:
    return SimTask(
        osm_id=osm_id,
        idf_path=str(tmp_path / "test.idf"),
        epw_path=str(tmp_path / "test.epw"),
        work_dir=str(tmp_path / osm_id),
    )


def _write_stub_sql(work_dir: Path) -> None:
    """Write a minimal SQLite file so sql_path existence check passes."""
    db_path = work_dir / "eplusout.sql"
    con = sqlite3.connect(str(db_path))
    con.execute("CREATE TABLE ReportData (id INTEGER)")
    con.execute("INSERT INTO ReportData VALUES (1)")
    con.commit()
    con.close()


# ── Handshake tests ───────────────────────────────────────────────────────────

class TestVersionHandshake:
    def test_matching_version_returns_version_string(self):
        mock_result = MagicMock()
        mock_result.stdout = "EnergyPlus, Version 23.1.0-12345\n"
        mock_result.stderr = ""
        with patch("openubem.simulation.runner.subprocess.run", return_value=mock_result):
            ver = _version_handshake()
        assert ver.startswith("23.1")

    def test_mismatch_raises(self):
        mock_result = MagicMock()
        mock_result.stdout = "EnergyPlus, Version 22.1.0-99999\n"
        mock_result.stderr = ""
        with patch("openubem.simulation.runner.subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="version mismatch"):
                _version_handshake()

    def test_binary_missing_raises(self):
        with patch(
            "openubem.simulation.runner.subprocess.run",
            side_effect=FileNotFoundError("not found"),
        ):
            with pytest.raises(RuntimeError, match="not found"):
                _version_handshake()

    def test_unparseable_output_raises(self):
        mock_result = MagicMock()
        mock_result.stdout = "some garbage output"
        mock_result.stderr = ""
        with patch("openubem.simulation.runner.subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="Could not parse"):
                _version_handshake()


# ── run_energyplus tests (mocked subprocess) ──────────────────────────────────

class TestRunEnergyPlus:
    def test_success_returns_dict_with_returncode(self, tmp_path):
        task = _make_task(tmp_path)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "EnergyPlus completed"
        mock_result.stderr = ""
        with patch("openubem.simulation.runner.subprocess.run", return_value=mock_result):
            result = run_energyplus(task)
        assert result["osm_id"] == "way/test"
        assert result["returncode"] == 0
        assert result["timed_out"] is False
        assert result["wall_clock_s"] >= 0.0

    def test_timeout_returns_timed_out_true(self, tmp_path):
        task = _make_task(tmp_path)
        with patch(
            "openubem.simulation.runner.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["ep"], timeout=1),
        ):
            result = run_energyplus(task, timeout_s=1)
        assert result["timed_out"] is True
        assert result["returncode"] is None
        assert result["wall_clock_s"] == 1.0

    def test_log_file_written(self, tmp_path):
        task = _make_task(tmp_path)
        wd = Path(task.work_dir)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "stdout line"
        mock_result.stderr = "stderr line"
        with patch("openubem.simulation.runner.subprocess.run", return_value=mock_result):
            run_energyplus(task)
        log = wd / "openubem_run.log"
        assert log.exists()
        text = log.read_text()
        assert "stdout line" in text
        assert "stderr line" in text


# ── classify_outcome table-driven tests (P8 stubs) ───────────────────────────

class TestClassifyOutcome:
    def _base_raw(self, osm_id: str = "way/A") -> dict:
        return {"osm_id": osm_id, "returncode": 0, "wall_clock_s": 5.0,
                "timed_out": False, "_stderr": ""}

    # F8 row 1: failed_timeout
    def test_timeout_classified(self, tmp_path):
        raw = {**self._base_raw(), "timed_out": True, "returncode": None, "wall_clock_s": 900.0}
        result = classify_outcome(raw, tmp_path)
        assert result["status"] == "failed_timeout"
        assert "killed" in result["error_summary"]

    # F8 row 2: failed_crash (no .end file)
    def test_no_end_file_is_crash(self, tmp_path):
        raw = self._base_raw()
        raw["_stderr"] = "Segmentation fault" * 20  # > 500 chars to test truncation
        result = classify_outcome(raw, tmp_path)
        assert result["status"] == "failed_crash"
        assert len(result["error_summary"]) <= 500

    # F8 row 3: failed_fatal (from stub)
    def test_fatal_end_file(self, tmp_path):
        import shutil
        wd = tmp_path / "fatal_test"
        wd.mkdir()
        shutil.copy(_FIXTURES / "end_fatal.txt", wd / "eplusout.end")
        shutil.copy(_FIXTURES / "err_fatal.txt", wd / "eplusout.err")
        raw = self._base_raw(osm_id="way/fatal")
        result = classify_outcome(raw, wd)
        assert result["status"] == "failed_fatal"
        assert "Fatal" in result["error_summary"]

    # F8 row 4: success (with sql)
    def test_success_with_sql(self, tmp_path):
        wd = tmp_path / "success_test"
        wd.mkdir()
        import shutil
        shutil.copy(_FIXTURES / "end_success.txt", wd / "eplusout.end")
        _write_stub_sql(wd)
        raw = self._base_raw(osm_id="way/ok")
        result = classify_outcome(raw, wd)
        assert result["status"] == "success"
        assert result["n_warnings"] == 12
        assert result["n_severe"] == 0

    # F8: severe > 0 stays success
    def test_success_with_severes_stays_success(self, tmp_path):
        wd = tmp_path / "success_sev"
        wd.mkdir()
        import shutil
        shutil.copy(_FIXTURES / "end_success_severe.txt", wd / "eplusout.end")
        _write_stub_sql(wd)
        raw = self._base_raw(osm_id="way/sev")
        result = classify_outcome(raw, wd)
        assert result["status"] == "success"
        assert result["n_warnings"] == 12
        assert result["n_severe"] == 3

    # F8: success .end but missing sql → crash
    def test_success_end_missing_sql_is_crash(self, tmp_path):
        wd = tmp_path / "no_sql"
        wd.mkdir()
        import shutil
        shutil.copy(_FIXTURES / "end_success.txt", wd / "eplusout.end")
        raw = self._base_raw(osm_id="way/nosql")
        result = classify_outcome(raw, wd)
        assert result["status"] == "failed_crash"

    # F8 precedence: timeout beats everything
    def test_timeout_takes_precedence_over_end_file(self, tmp_path):
        wd = tmp_path / "prec_test"
        wd.mkdir()
        import shutil
        shutil.copy(_FIXTURES / "end_success.txt", wd / "eplusout.end")
        _write_stub_sql(wd)
        raw = {**self._base_raw(), "timed_out": True, "returncode": None, "wall_clock_s": 900.0}
        result = classify_outcome(raw, wd)
        assert result["status"] == "failed_timeout"

    # F8 precedence: fatal beats success marker (shouldn't happen, but precedence test)
    def test_fatal_beats_success(self, tmp_path):
        wd = tmp_path / "prec_fatal"
        wd.mkdir()
        import shutil
        # Write a .end with BOTH markers (adversarial)
        (wd / "eplusout.end").write_text(
            "EnergyPlus Terminated--Fatal Error Detected\n"
            "EnergyPlus Completed Successfully-- 0 Warning; 0 Severe Errors\n"
        )
        shutil.copy(_FIXTURES / "err_fatal.txt", wd / "eplusout.err")
        raw = self._base_raw(osm_id="way/both")
        result = classify_outcome(raw, wd)
        assert result["status"] == "failed_fatal"

    # Count parsing: "-- 12 Warning; 3 Severe"
    def test_count_parsing(self, tmp_path):
        wd = tmp_path / "count_test"
        wd.mkdir()
        (wd / "eplusout.end").write_text(
            "EnergyPlus Completed Successfully-- 12 Warning; 3 Severe Errors; Elapsed Time=...\n"
        )
        _write_stub_sql(wd)
        raw = self._base_raw()
        result = classify_outcome(raw, wd)
        assert result["n_warnings"] == 12
        assert result["n_severe"] == 3
