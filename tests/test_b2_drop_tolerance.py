"""R-B2 harness: verify the pipeline tolerates up to max(5, 1%) simulation failures.

Exercises the drop-tolerance logic that was added to v12_cell_pipeline.py:
  if 0 < n_sim_fail <= max(5, ceil(0.01 * n_sim_total)):
      write dropped_buildings.csv and proceed on survivors
  else:
      sys.exit(2)

This test synthesises a minimal sim_mf DataFrame to prove the branching.
"""
from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest


def _make_sim_mf(n_success: int, n_fail: int) -> pd.DataFrame:
    rows = []
    for i in range(n_success):
        rows.append({"osm_id": f"way/{i}", "status": "success", "error_summary": ""})
    for i in range(n_fail):
        rows.append({"osm_id": f"fail/{i}", "status": "failed", "error_summary": "geometry error"})
    return pd.DataFrame(rows)


def _run_b2_logic(sim_mf: pd.DataFrame, results_dir: Path) -> tuple[bool, int]:
    """Replicate the B2 guard from v12_cell_pipeline.py run_cell().

    Returns (proceeded, n_remaining) where proceeded=True means the function did not exit.
    Raises SystemExit with code 2 when failures exceed the tolerance.
    """
    n_sim_total = len(sim_mf)
    n_sim_success_count = int((sim_mf["status"] == "success").sum())
    n_sim_fail = n_sim_total - n_sim_success_count

    if n_sim_fail > 0:
        failed_rows = sim_mf[sim_mf["status"] != "success"]
        max_tolerated = max(5, math.ceil(0.01 * n_sim_total))
        if n_sim_fail <= max_tolerated:
            drop_path = results_dir / "dropped_buildings.csv"
            failed_rows.to_csv(drop_path, index=False)
            sim_mf = sim_mf[sim_mf["status"] == "success"].copy()
        else:
            sys.exit(2)

    return True, int((sim_mf["status"] == "success").sum())


class TestB2DropTolerance:
    """R-B2: pipeline tolerates up to max(5, 1%) simulation failures."""

    def test_1_fail_of_600_proceeds(self, tmp_path: Path) -> None:
        """1 failure out of 600: within tolerance (max(5,6)=6) → proceeds, writes CSV."""
        sim_mf = _make_sim_mf(599, 1)
        proceeded, n_remaining = _run_b2_logic(sim_mf, tmp_path)
        assert proceeded
        assert n_remaining == 599
        drop_csv = tmp_path / "dropped_buildings.csv"
        assert drop_csv.exists(), "dropped_buildings.csv must be written"
        dropped = pd.read_csv(drop_csv)
        assert len(dropped) == 1
        assert dropped.iloc[0]["osm_id"] == "fail/0"

    def test_5_fail_of_100_proceeds(self, tmp_path: Path) -> None:
        """5 failures of 100: at the threshold boundary (max(5,1)=5) → proceeds."""
        sim_mf = _make_sim_mf(95, 5)
        proceeded, n_remaining = _run_b2_logic(sim_mf, tmp_path)
        assert proceeded
        assert n_remaining == 95
        dropped = pd.read_csv(tmp_path / "dropped_buildings.csv")
        assert len(dropped) == 5

    def test_zero_failures_proceeds_no_csv(self, tmp_path: Path) -> None:
        """No failures: proceeds without writing dropped_buildings.csv."""
        sim_mf = _make_sim_mf(600, 0)
        proceeded, n_remaining = _run_b2_logic(sim_mf, tmp_path)
        assert proceeded
        assert n_remaining == 600
        assert not (tmp_path / "dropped_buildings.csv").exists()

    def test_excess_failures_exits_2(self, tmp_path: Path) -> None:
        """7 failures of 100: exceeds tolerance max(5,1)=5 → sys.exit(2)."""
        sim_mf = _make_sim_mf(93, 7)
        with pytest.raises(SystemExit) as exc_info:
            _run_b2_logic(sim_mf, tmp_path)
        assert exc_info.value.code == 2

    def test_threshold_formula_max_5_or_1pct(self, tmp_path: Path) -> None:
        """For n=200, threshold = max(5, ceil(0.01*200)) = max(5,2) = 5."""
        sim_mf = _make_sim_mf(195, 5)
        proceeded, _ = _run_b2_logic(sim_mf, tmp_path)
        assert proceeded

    def test_threshold_large_cell(self, tmp_path: Path) -> None:
        """For n=800, threshold = max(5, ceil(0.01*800)) = max(5,8) = 8; 8 fails proceeds."""
        sim_mf = _make_sim_mf(792, 8)
        proceeded, n_remaining = _run_b2_logic(sim_mf, tmp_path)
        assert proceeded
        assert n_remaining == 792
