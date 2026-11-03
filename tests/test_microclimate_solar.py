from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from openubem.microclimate.solar import solar_position

FIXTURE = Path(__file__).parent / "fixtures" / "solar_position_reference.csv"
EXCEL_EPOCH = pd.Timestamp("1899-12-30")


def _load_reference():
    df = pd.read_csv(FIXTURE, encoding="utf-8-sig")
    local_dt = EXCEL_EPOCH + pd.to_timedelta(df["date_serial"] + df["time_frac"], unit="D")
    utc_dt = local_dt - pd.to_timedelta(df["tz"], unit="h")
    df["utc_dt"] = utc_dt
    return df


def test_reference_table_atol_0p1_deg():
    df = _load_reference()
    max_alt_err = 0.0
    max_az_err = 0.0
    for _, row in df.iterrows():
        idx = pd.DatetimeIndex([row["utc_dt"]])
        alt, az = solar_position(idx, row["lat"], row["lon"])
        alt_err = abs(float(alt[0]) - row["elevation_deg"])
        az_err = min(abs(float(az[0]) - row["azimuth_deg"]), 360 - abs(float(az[0]) - row["azimuth_deg"]))
        max_alt_err = max(max_alt_err, alt_err)
        max_az_err = max(max_az_err, az_err)
        assert alt_err < 0.1, f"{row['scenario']} altitude err {alt_err:.4f}"
        assert az_err < 0.1, f"{row['scenario']} azimuth err {az_err:.4f}"
    print(f"max altitude err {max_alt_err:.5f} deg, max azimuth err {max_az_err:.5f} deg")


def test_solar_noon_azimuth_near_180_northern_hemisphere():
    # 12:00 clock at lon=0 is within ~4 deg hour-angle of true solar noon (equation of time,
    # +-17 min max) -- reference-table row "summer_solstice_40N" independently confirms 178.6 deg.
    idx = pd.DatetimeIndex(["2024-06-20 12:00:00"])
    alt, az = solar_position(idx, 40.0, 0.0)
    assert az[0] == pytest.approx(180.0, abs=2.0)


def test_altitude_symmetric_about_solar_noon():
    # True solar noon near lon=0 in late March is offset from 12:00 clock by the equation of
    # time (a few minutes); use the true solar-noon UTC hour for this symmetry check.
    base = pd.Timestamp("2024-03-20 12:07:00")
    idx = pd.DatetimeIndex([base - pd.Timedelta(hours=2), base, base + pd.Timedelta(hours=2)])
    alt, _az = solar_position(idx, 40.0, 0.0)
    assert alt[0] == pytest.approx(alt[2], abs=0.2)
    assert alt[1] > alt[0]


def test_equator_equinox_noon_altitude_near_90():
    idx = pd.DatetimeIndex(["2024-03-20 12:00:00"])
    alt, _az = solar_position(idx, 0.0, 0.0)
    assert alt[0] == pytest.approx(90.0, abs=2.5)


def test_night_altitude_negative():
    idx = pd.DatetimeIndex(["2024-01-01 03:00:00"])
    alt, _az = solar_position(idx, 45.0, 0.0)
    assert alt[0] < 0


def test_vectorised_matches_per_row():
    idx = pd.DatetimeIndex(pd.date_range("2024-06-01", periods=24, freq="h"))
    alt_vec, az_vec = solar_position(idx, 40.0, -75.0)
    for i in range(len(idx)):
        alt_i, az_i = solar_position(idx[i:i + 1], 40.0, -75.0)
        assert alt_vec[i] == pytest.approx(alt_i[0])
        assert az_vec[i] == pytest.approx(az_i[0])
