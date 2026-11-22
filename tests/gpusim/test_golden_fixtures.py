import importlib
import json
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = REPO_ROOT / "tests/fixtures/gpusim/golden"
EXPECTED_ROWS = 105_120
CELL1_ID = "it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100"
CELL1_T03_MAC_HEATING_KWH = 23275.422744

GOLDEN_CELL_IDS: tuple[str, ...] = (
    CELL1_ID,
    "uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000",
    "es__ES.ME.AB.01.Gen.ReEx.001.001__f000",
)

VARIANT_IDS: tuple[str, ...] = (
    "V01",
    "V03",
    "V04",
    "V06",
    "V07",
    "V09",
    "V10",
    "V11",
    "V14",
    "V15",
)

ALL_FIXTURE_RELS: tuple[str, ...] = (
    *GOLDEN_CELL_IDS,
    *(f"variants/{CELL1_ID}__{vid}" for vid in VARIANT_IDS),
)


def _find_matching_columns(columns: list[str], var_substr: str) -> list[str]:
    """Return columns whose names contain the given variable substring.

    Args:
        columns: List of Parquet column names.
        var_substr: Case-insensitive variable substring to match.

    Returns:
        List of matching column names.
    """
    needle = var_substr.casefold()
    return [col for col in columns if needle in col.casefold()]


@pytest.mark.parametrize("rel_path", ALL_FIXTURE_RELS)
def test_fixture_loads_rows_and_no_nan(rel_path: str) -> None:
    """Verify every golden cell and variant fixture loads cleanly without NaNs.

    Args:
        rel_path: Fixture directory path relative to ``GOLDEN_ROOT``.
    """
    fixture_dir = GOLDEN_ROOT / rel_path
    parquet_path = fixture_dir / "timestep.parquet"
    meta_path = fixture_dir / "meta.json"
    assert parquet_path.is_file()
    assert meta_path.is_file()

    df = pd.read_parquet(parquet_path)
    assert len(df) == EXPECTED_ROWS
    for date_col in ("month", "day", "hour", "minute"):
        assert date_col in df.columns
        assert not df[date_col].isna().any()

    cols = list(df.columns)
    heat_energy_cols = _find_matching_columns(
        cols, "Zone Ideal Loads Zone Total Heating Energy"
    )
    heat_rate_cols = _find_matching_columns(
        cols, "Zone Ideal Loads Zone Sensible Heating Rate"
    )
    zone_temp_cols = _find_matching_columns(cols, "Zone Mean Air Temperature")

    assert len(heat_energy_cols) == 1
    assert len(heat_rate_cols) == 1
    assert len(zone_temp_cols) == 1

    for col in (*heat_energy_cols, *heat_rate_cols, *zone_temp_cols):
        assert not df[col].isna().any()

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["row_count"] == EXPECTED_ROWS
    assert "manifest_heating_kwh" in meta
    assert "relative_difference" in meta
    if not rel_path.startswith("variants/"):
        assert meta["manifest_heating_kwh"] is not None
        assert meta["relative_difference"] is not None


def test_cell1_heating_matches_t03_mac_reference() -> None:
    """Verify cell 1 annual heating matches the T03 Mac reference within 1e-6."""
    fixture_dir = GOLDEN_ROOT / CELL1_ID
    df = pd.read_parquet(fixture_dir / "timestep.parquet")
    heat_cols = _find_matching_columns(
        list(df.columns), "Zone Ideal Loads Zone Total Heating Energy"
    )
    assert len(heat_cols) == 1
    parquet_kwh = float(df[heat_cols[0]].sum() / 3.6e6)

    meta = json.loads((fixture_dir / "meta.json").read_text(encoding="utf-8"))
    meta_kwh = float(meta["annual_heating_kwh"])

    rel_parquet = (
        abs(parquet_kwh - CELL1_T03_MAC_HEATING_KWH) / CELL1_T03_MAC_HEATING_KWH
    )
    rel_meta = (
        abs(meta_kwh - CELL1_T03_MAC_HEATING_KWH) / CELL1_T03_MAC_HEATING_KWH
    )
    assert rel_parquet < 1e-6
    assert rel_meta < 1e-6


@pytest.mark.parametrize("cell_id", GOLDEN_CELL_IDS)
def test_golden_cell_eio_required_blocks(cell_id: str) -> None:
    """Verify each golden cell .eio has CTF, surface-detail, and view-factor blocks.

    Args:
        cell_id: Golden cell identifier.
    """
    eio_path = GOLDEN_ROOT / cell_id / "eplusout.eio"
    assert eio_path.is_file()
    lines = eio_path.read_text(encoding="utf-8", errors="replace").splitlines()

    ctf_internal_mass = [
        line
        for line in lines
        if line.strip().startswith("Construction CTF,")
        and "EU_INTERNALMASS_CONSTRUCTION" in line.upper()
    ]
    heat_transfer_surfaces = [
        line for line in lines if line.strip().startswith("HeatTransfer Surface,")
    ]
    view_factor_lines = [
        line for line in lines if line.strip().startswith("Solar View Factor,")
    ]

    assert len(ctf_internal_mass) >= 1
    assert len(heat_transfer_surfaces) >= 1
    assert len(view_factor_lines) >= 1


@pytest.mark.xfail(strict=True, reason="M1 not built")
def test_stage_a_matches_golden() -> None:
    """Placeholder parity test that remains xfail until M1 numpy_ref exists."""
    importlib.import_module("openubem.gpusim.backends.numpy_ref")
