from pathlib import Path

import numpy as np
import pandas as pd

from openubem.microclimate.epw_hourly import read_epw_hourly

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic.epw"


def test_row_count():
    df = read_epw_hourly(FIXTURE)
    assert len(df) == 8760


def test_index_monotonic_and_naive():
    df = read_epw_hourly(FIXTURE)
    assert df.index.is_monotonic_increasing
    assert df.index.tz is None
    assert isinstance(df.index, pd.DatetimeIndex)


def test_value_ranges():
    df = read_epw_hourly(FIXTURE)
    dry_bulb = df["dry_bulb_c"].dropna()
    assert dry_bulb.between(-60, 60).all()
    for col in ("global_horizontal_wm2", "direct_normal_wm2", "diffuse_horizontal_wm2"):
        vals = df[col].dropna()
        assert (vals >= 0).all()
    rh = df["relative_humidity_pct"].dropna()
    assert rh.between(0, 100).all()


def test_first_and_last_row_hand_checked():
    df = read_epw_hourly(FIXTURE)
    # First data line (1-based EPW indices 7/8/9/10/13/14/15/16/21/22):
    # 2001,1,1,1,60,...,-33.1,-36.9,68,101550,0,0,158,0,0,0,0,0,0,0,34,0.7,7,8,...
    first = df.iloc[0]
    assert first["dry_bulb_c"] == -33.1
    assert first["dew_point_c"] == -36.9
    assert first["relative_humidity_pct"] == 68
    assert first["atmospheric_pressure_pa"] == 101550
    assert first["horizontal_infrared_wm2"] == 158
    assert first["wind_direction_deg"] == 34
    assert first["wind_speed_ms"] == 0.7
    assert first.name == pd.Timestamp("2001-01-01 00:00:00")

    # Last data line: 2001,12,31,24,60,...,-33.0,-36.7,69,101745,...,161,...,83,3.3,0,1,...
    last = df.iloc[-1]
    assert last["dry_bulb_c"] == -33.0
    assert last["dew_point_c"] == -36.7
    assert last["relative_humidity_pct"] == 69
    assert last["atmospheric_pressure_pa"] == 101745
    assert last["horizontal_infrared_wm2"] == 161
    assert last["wind_direction_deg"] == 83
    assert last["wind_speed_ms"] == 3.3
    assert last.name == pd.Timestamp("2001-12-31 23:00:00")


def test_sentinel_becomes_nan_and_flags(tmp_path):
    header = FIXTURE.read_text(encoding="utf-8").splitlines(keepends=True)[:8]
    bad_row = (
        "2001,1,1,1,60,X,99.9,99.9,999,999999,0,0,9999,9999,9999,9999,0,0,0,0,"
        "999,999,99,99,10.0,77777,9,999999999,6,0.0850,0,88,0.080,0.0,0.0\n"
    )
    rest = FIXTURE.read_text(encoding="utf-8").splitlines(keepends=True)[9:]
    p = tmp_path / "bad.epw"
    p.write_text("".join(header) + bad_row + "".join(rest), encoding="utf-8")

    df = read_epw_hourly(p)
    first = df.iloc[0]
    assert np.isnan(first["dry_bulb_c"])
    assert np.isnan(first["dew_point_c"])
    assert np.isnan(first["relative_humidity_pct"])
    assert np.isnan(first["atmospheric_pressure_pa"])
    assert np.isnan(first["horizontal_infrared_wm2"])
    assert np.isnan(first["global_horizontal_wm2"])
    assert bool(first["dq_flag"]) is True


def test_leap_year_8784_rows(tmp_path):
    header = FIXTURE.read_text(encoding="utf-8").splitlines(keepends=True)[:8]
    body_lines = FIXTURE.read_text(encoding="utf-8").splitlines(keepends=True)[8:]
    # Duplicate Feb 29 (24 extra hours) using a Jan 1 template row shape, to hit 8784 rows.
    extra = [ln.replace("2001,1,1,", "2001,2,29,", 1) for ln in body_lines[:24]]
    p = tmp_path / "leap.epw"
    p.write_text("".join(header) + "".join(body_lines) + "".join(extra), encoding="utf-8")
    df = read_epw_hourly(p)
    assert len(df) == 8784
