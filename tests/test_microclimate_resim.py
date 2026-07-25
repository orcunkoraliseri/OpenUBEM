import shutil
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from openubem.microclimate.resim import (
    ResimRefusedError,
    RESIM_OUTPUT_VARIABLE,
    harvest_wall_temperatures,
    patch_idf_for_resim,
    run_resim_side_leg,
)

FIXTURE_IDF = Path("openubem/idf/templates/commercial_base.idf")
GOLDEN_SQL = Path("tests/fixtures/golden_sql/r1_single_zone.sql")


def test_patch_idf_two_edits_only(tmp_path):
    out_path = tmp_path / "patched.idf"
    result = patch_idf_for_resim(
        FIXTURE_IDF, out_path, window_start_month=7, window_start_day=15, window_n_days=7,
    )
    assert out_path.exists()

    diff = result["object_count_diff"]
    assert "OUTPUT:VARIABLE" in diff
    assert diff["OUTPUT:VARIABLE"] == (0, 1)
    # RUNPERIOD's own object COUNT doesn't change (still exactly 1) -- only its field values do,
    # so it must not appear in the count diff at all.
    assert "RUNPERIOD" not in diff
    non_output_diffs = {k: v for k, v in diff.items() if k != "OUTPUT:VARIABLE"}
    assert non_output_diffs == {}, f"unexpected object-count changes: {non_output_diffs}"

    text = out_path.read_text(encoding="utf-8", errors="replace")
    assert RESIM_OUTPUT_VARIABLE in text


def test_patch_idf_window_and_warmup_margin(tmp_path):
    out_path = tmp_path / "patched.idf"
    result = patch_idf_for_resim(
        FIXTURE_IDF, out_path, window_start_month=7, window_start_day=15,
        window_n_days=7, warmup_days=3,
    )
    begin_m, begin_d, end_m, end_d = result["window"]
    # window_start = Jul 15 -> warmup pushes begin back 3 days -> Jul 12; end = start+6 = Jul 21.
    assert (begin_m, begin_d) == (7, 12)
    assert (end_m, end_d) == (7, 21)


def test_run_resim_side_leg_refuses_annual(tmp_path):
    with pytest.raises(ResimRefusedError):
        run_resim_side_leg(
            [FIXTURE_IDF], epw_path="dummy.epw", work_root=tmp_path,
            window_mode="annual", window_start_month=7, window_start_day=15,
        )


def _seed_synthetic_wall_temp(sql_path: Path, key_value: str, hourly_values: dict):
    """hourly_values: {(month, day, hour): value_c}."""
    conn = sqlite3.connect(sql_path)
    cur = conn.cursor()
    cur.execute("SELECT MAX(ReportDataDictionaryIndex) FROM ReportDataDictionary")
    new_rdd_index = (cur.fetchone()[0] or 0) + 1
    cur.execute(
        "INSERT INTO ReportDataDictionary "
        "(ReportDataDictionaryIndex, IsMeter, Type, IndexGroup, TimestepType, KeyValue, Name, "
        "ReportingFrequency, ScheduleName, Units) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (new_rdd_index, 0, "Avg", "Zone", "Zone", key_value, RESIM_OUTPUT_VARIABLE, "Hourly", None, "C"),
    )
    cur.execute("SELECT MAX(ReportDataIndex) FROM ReportData")
    next_rd_index = (cur.fetchone()[0] or 0) + 1
    for (month, day, hour), value in hourly_values.items():
        cur.execute(
            "SELECT TimeIndex FROM Time WHERE Month=? AND Day=? AND Hour=?", (month, day, hour)
        )
        row = cur.fetchone()
        if row is None:
            continue
        time_index = row[0]
        cur.execute(
            "INSERT INTO ReportData (ReportDataIndex, TimeIndex, ReportDataDictionaryIndex, Value) "
            "VALUES (?,?,?,?)",
            (next_rd_index, time_index, new_rdd_index, value),
        )
        next_rd_index += 1
    conn.commit()
    conn.close()


def test_harvest_wall_temperatures_reads_seeded_series(tmp_path, monkeypatch):
    scratch_sql = tmp_path / "eplusout.sql"
    shutil.copy(GOLDEN_SQL, scratch_sql)
    seeded = {(1, 1, 12): 45.6, (1, 1, 13): 47.2, (1, 1, 14): 44.1}
    _seed_synthetic_wall_temp(scratch_sql, "WAY/R1_SOUTHWALL", seeded)
    # a non-wall surface (e.g. a roof) sharing the same variable name must be filtered out --
    # simulate this by seeding a second KeyValue that wall_surface_azimuths (mocked below)
    # does NOT report as a wall.
    _seed_synthetic_wall_temp(scratch_sql, "WAY/R1_ROOF", {(1, 1, 12): 60.0})

    def fake_azimuths(idf_path):
        return {"WAY/R1_SOUTHWALL": 180.0}

    monkeypatch.setattr("openubem.microclimate.resim.wall_surface_azimuths", fake_azimuths)

    df = harvest_wall_temperatures({"r1": (scratch_sql, "unused.idf")})
    assert set(df["surface_name"]) == {"WAY/R1_SOUTHWALL"}
    assert (df["azimuth_deg"] == 180.0).all()
    for (month, day, hour), expected in seeded.items():
        row = df[(df["Month"] == month) & (df["Day"] == day) & (df["Hour"] == hour)]
        assert len(row) == 1
        assert row["t_wall_c"].iloc[0] == pytest.approx(expected)
