"""Tests for region-parametrized CBECS reference files (T03 / CP-R6-A)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPORTS = Path(__file__).parent.parent / "inputs" / "reports"

REGION_FILES = {
    "middle_atlantic": REPORTS / "cbecs_2018_middle_atlantic_eui.csv",
    "pacific": REPORTS / "cbecs_2018_pacific_eui.csv",
    "west_south_central": REPORTS / "cbecs_2018_west_south_central_eui.csv",
}

REQUIRED_COLUMNS = {"pba_code", "pba_label", "sqft", "eui_kwh_m2", "finalwt"}

NE_FILE = REPORTS / "cbecs_2018_new_england_eui.csv"
NE_EXPECTED_ROWS = 284
NE_EXPECTED_WMEAN = 220.9  # kWh/m²/yr (±0.5 tolerance)


@pytest.mark.parametrize("slug,path", REGION_FILES.items())
def test_file_exists(slug: str, path: Path) -> None:
    assert path.exists(), f"Missing: {path}"


@pytest.mark.parametrize("slug,path", REGION_FILES.items())
def test_columns(slug: str, path: Path) -> None:
    df = pd.read_csv(path)
    assert REQUIRED_COLUMNS == set(df.columns), f"{slug}: unexpected columns {set(df.columns)}"


@pytest.mark.parametrize("slug,path", REGION_FILES.items())
def test_finalwt_positive(slug: str, path: Path) -> None:
    df = pd.read_csv(path)
    assert (df["finalwt"] > 0).all(), f"{slug}: non-positive finalwt rows found"


@pytest.mark.parametrize("slug,path", REGION_FILES.items())
def test_weighted_mean_plausible(slug: str, path: Path) -> None:
    df = pd.read_csv(path)
    wmean = float(np.average(df["eui_kwh_m2"].values, weights=df["finalwt"].values))
    assert 30 <= wmean <= 1000, f"{slug}: wmean {wmean:.1f} kWh/m²/yr outside [30, 1000]"


@pytest.mark.parametrize("slug,path", REGION_FILES.items())
def test_row_count_gt_50(slug: str, path: Path) -> None:
    df = pd.read_csv(path)
    assert len(df) > 50, f"{slug}: only {len(df)} rows (need > 50)"


@pytest.mark.parametrize("slug,path", REGION_FILES.items())
def test_pba15_present(slug: str, path: Path) -> None:
    # Food-service PBA-15 must be present for archetype-aware plausibility (T08)
    df = pd.read_csv(path)
    assert 15 in df["pba_code"].values, f"{slug}: PBA-15 (food service) not found"


def test_new_england_unchanged_rows() -> None:
    assert NE_FILE.exists(), f"New England file missing: {NE_FILE}"
    df = pd.read_csv(NE_FILE)
    assert len(df) == NE_EXPECTED_ROWS, (
        f"New England row count changed: got {len(df)}, expected {NE_EXPECTED_ROWS}"
    )


def test_new_england_unchanged_wmean() -> None:
    df = pd.read_csv(NE_FILE)
    wmean = float(np.average(df["eui_kwh_m2"].values, weights=df["finalwt"].values))
    assert abs(wmean - NE_EXPECTED_WMEAN) < 0.5, (
        f"New England wmean changed: got {wmean:.4f}, expected ~{NE_EXPECTED_WMEAN}"
    )


def test_new_england_columns_intact() -> None:
    df = pd.read_csv(NE_FILE)
    assert REQUIRED_COLUMNS == set(df.columns)
