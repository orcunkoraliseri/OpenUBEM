import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from openubem.results import hourly as h

KWH_J = 3.6e6
GOLDEN = Path(__file__).resolve().parents[1] / "fixtures" / "golden_sql"


def _make_sql(path, variables, zones=(), days=((1, 1), (7, 1)), warmup_days=()):
    conn = sqlite3.connect(path)
    conn.executescript(
        "CREATE TABLE ReportDataDictionary (ReportDataDictionaryIndex INTEGER, KeyValue TEXT,"
        " Name TEXT, Units TEXT, ReportingFrequency TEXT);"
        "CREATE TABLE ReportData (ReportDataIndex INTEGER, TimeIndex INTEGER,"
        " ReportDataDictionaryIndex INTEGER, Value REAL);"
        "CREATE TABLE Time (TimeIndex INTEGER, Month INTEGER, Day INTEGER, Hour INTEGER,"
        " Interval INTEGER, WarmupFlag INTEGER);"
        "CREATE TABLE Zones (ZoneName TEXT, Multiplier REAL, ListMultiplier REAL);"
    )
    for z in zones:
        conn.execute("INSERT INTO Zones VALUES (?,?,?)", z)
    tindex = {}
    k = 0
    for (m, d) in list(days) + list(warmup_days):
        for hr in range(1, 25):
            k += 1
            warm = 1 if (m, d) in warmup_days else None
            conn.execute("INSERT INTO Time VALUES (?,?,?,?,60,?)", (k, m, d, hr, warm))
            tindex[(m, d, hr)] = k
    ridx = 0
    for i, (key, name, freq, fn) in enumerate(variables, start=1):
        conn.execute("INSERT INTO ReportDataDictionary VALUES (?,?,?,?,?)",
                     (i, key, name, "J", freq))
        for (m, d, hr), t in tindex.items():
            ridx += 1
            conn.execute("INSERT INTO ReportData VALUES (?,?,?,?)", (ridx, t, i, fn(m, d, hr) * KWH_J))
    conn.commit()
    conn.close()
    return path


def test_ideal_loads_zone_variables_with_multiplier(tmp_path):
    sql = _make_sql(
        tmp_path / "a.sql",
        [
            ("ZONE A IDEAL LOADS AIR SYSTEM", h.IDEAL_HEATING, "Hourly", lambda m, d, hr: 2.0),
            ("ZONE B IDEAL LOADS AIR SYSTEM", h.IDEAL_HEATING, "Hourly", lambda m, d, hr: 1.0),
            ("ZONE A IDEAL LOADS AIR SYSTEM", h.IDEAL_COOLING, "Hourly", lambda m, d, hr: 0.5),
        ],
        zones=[("Zone A", 3.0, 1.0), ("Zone B", 1.0, 2.0)],
    )
    frame, src = h.read_hourly(sql)
    assert len(frame) == 48
    assert src["heating_kwh"] == "ideal_loads_zone"
    assert src["cooling_kwh"] == "ideal_loads_zone"
    assert src["electricity_kwh"] == "absent"
    assert src["gas_kwh"] == "absent"
    assert np.allclose(frame["heating_kwh"], 2.0 * 3.0 + 1.0 * 2.0)
    assert np.allclose(frame["cooling_kwh"], 0.5 * 3.0)
    assert frame["gas_kwh"].isna().all()


def test_hourly_meters_take_priority_and_are_not_multiplied(tmp_path):
    sql = _make_sql(
        tmp_path / "b.sql",
        [
            (None, "Heating:NaturalGas", "Hourly", lambda m, d, hr: 4.0),
            (None, "Heating:Electricity", "Hourly", lambda m, d, hr: 1.0),
            ("ZONE A IDEAL LOADS AIR SYSTEM", h.IDEAL_HEATING, "Hourly", lambda m, d, hr: 99.0),
            (None, "Electricity:Facility", "Hourly", lambda m, d, hr: 7.0),
            (None, "NaturalGas:Facility", "Hourly", lambda m, d, hr: 5.0),
            ("ZONE A", h.ZONE_ELECTRICITY[0], "Hourly", lambda m, d, hr: 50.0),
        ],
        zones=[("Zone A", 10.0, 1.0)],
    )
    frame, src = h.read_hourly(sql)
    assert src["heating_kwh"] == "meter"
    assert src["electricity_kwh"] == "facility_meter"
    assert src["gas_kwh"] == "facility_meter"
    assert np.allclose(frame["heating_kwh"], 5.0)
    assert np.allclose(frame["electricity_kwh"], 7.0)
    assert np.allclose(frame["gas_kwh"], 5.0)


def test_zone_lights_and_equipment_fallback_with_multiplier(tmp_path):
    sql = _make_sql(
        tmp_path / "c.sql",
        [
            ("ZONE A", h.ZONE_ELECTRICITY[0], "Hourly", lambda m, d, hr: 1.0),
            ("ZONE A", h.ZONE_ELECTRICITY[1], "Hourly", lambda m, d, hr: 2.0),
        ],
        zones=[("Zone A", 4.0, 1.0)],
    )
    frame, src = h.read_hourly(sql)
    assert src["electricity_kwh"] == "zone_lights_equipment"
    assert np.allclose(frame["electricity_kwh"], 12.0)


def test_run_period_only_sql_is_absent_everywhere(tmp_path):
    sql = _make_sql(
        tmp_path / "d.sql",
        [(None, "Heating:NaturalGas", "Run Period", lambda m, d, hr: 1.0)],
        days=((1, 1),),
    )
    frame, src = h.read_hourly(sql)
    assert set(src.values()) == {"absent"}
    assert frame.empty
    assert all(np.isnan(v) for v in h.annual_kwh(frame).values())
    assert all(v is None for v in h.peaks(frame).values())


def test_warmup_rows_are_excluded(tmp_path):
    sql = _make_sql(
        tmp_path / "e.sql",
        [(None, "Heating:NaturalGas", "Hourly", lambda m, d, hr: 1.0)],
        days=((1, 1),), warmup_days=((1, 2),),
    )
    frame, _ = h.read_hourly(sql)
    assert len(frame) == 24
    assert set(frame["day"]) == {1}


def test_day_profiles_and_peak(tmp_path):
    def heat(m, d, hr):
        return float(hr) if m == 1 else 0.0

    def elec(m, d, hr):
        return 100.0 if (m, d, hr) == (7, 1, 15) else 1.0

    sql = _make_sql(
        tmp_path / "f.sql",
        [(None, "Heating:NaturalGas", "Hourly", heat), (None, "Electricity:Facility", "Hourly", elec)],
    )
    frame, _ = h.read_hourly(sql)
    winter = h.winter_profile(frame)
    summer = h.summer_profile(frame)
    assert list(winter["hour"]) == list(range(1, 25))
    assert winter["n_days"].iloc[0] == 1
    assert np.allclose(winter["heating_kwh"], np.arange(1, 25))
    assert np.allclose(summer["heating_kwh"], 0.0)
    assert summer.loc[summer["hour"] == 15, "electricity_kwh"].iloc[0] == 100.0
    pk = h.peak_hour(frame, "electricity_kwh")
    assert (pk["month"], pk["day"], pk["hour"], pk["kwh"]) == (7, 1, 15, 100.0)
    assert h.peak_hour(frame, "gas_kwh") is None


def test_relative_difference():
    assert h.relative_difference(100.05, 100.0) == pytest.approx(5e-4)
    assert h.relative_difference(0.0, 0.0) == 0.0
    assert h.relative_difference(1.0, 0.0) == float("inf")


def test_aggregate_site_sums_by_timestamp_and_counts():
    keys = {"month": [1, 1], "day": [1, 1], "hour": [1, 2]}
    a = pd.DataFrame({**keys, "heating_kwh": [1.0, 2.0], "cooling_kwh": [np.nan] * 2,
                      "electricity_kwh": [3.0, 3.0], "gas_kwh": [np.nan] * 2})
    b = pd.DataFrame({**keys, "heating_kwh": [10.0, 20.0], "cooling_kwh": [np.nan] * 2,
                      "electricity_kwh": [4.0, 5.0], "gas_kwh": [np.nan] * 2})
    site, counts = h.aggregate_site([a, b])
    assert list(site["heating_kwh"]) == [11.0, 22.0]
    assert list(site["electricity_kwh"]) == [7.0, 8.0]
    assert site["cooling_kwh"].isna().all()
    assert counts == {"heating_kwh": 2, "cooling_kwh": 0, "electricity_kwh": 2, "gas_kwh": 0}
    with pytest.raises(ValueError):
        h.aggregate_site([])


def test_extract_writes_csv_and_sidecar(tmp_path):
    sql = _make_sql(tmp_path / "g.sql", [(None, "Heating:NaturalGas", "Hourly", lambda m, d, hr: 2.0)])
    out = tmp_path / "o" / "x.csv.gz"
    summary = h.extract(sql, out)
    back = pd.read_csv(out)
    assert len(back) == 48
    assert back["heating_kwh"].sum() == pytest.approx(96.0)
    side = json.loads((tmp_path / "o" / "x.json").read_text(encoding="utf-8"))
    assert side["annual_kwh"]["heating_kwh"] == pytest.approx(96.0)
    assert side["sources"]["heating_kwh"] == "meter"
    assert summary["hours"] == 48


@pytest.mark.skipif(not (GOLDEN / "r1_single_zone.sql").exists(), reason="golden fixture missing")
def test_real_energyplus_sql_hourly_sum_equals_run_period_meters():
    sql = GOLDEN / "r1_single_zone.sql"
    frame, src = h.read_hourly(sql)
    assert len(frame) == 8760
    assert src["heating_kwh"] == "ideal_loads_zone"
    conn = sqlite3.connect(f"file:{sql}?mode=ro", uri=True)
    try:
        meters = dict(conn.execute(
            "SELECT d.Name, r.Value FROM ReportData r JOIN ReportDataDictionary d "
            "ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex "
            "WHERE d.ReportingFrequency = 'Run Period'"
        ).fetchall())
    finally:
        conn.close()
    heating_ref = (meters.get("Heating:NaturalGas", 0.0) + meters.get("Heating:Electricity", 0.0)) / KWH_J
    cooling_ref = meters["Cooling:Electricity"] / KWH_J
    annual = h.annual_kwh(frame)
    assert h.relative_difference(annual["heating_kwh"], heating_ref) < 1e-3
    assert h.relative_difference(annual["cooling_kwh"], cooling_ref) < 1e-3


def test_district_hot_water_series_is_reported_apart_from_the_adopted_four(tmp_path):
    sql = _make_sql(
        tmp_path / "d.sql",
        [
            ("", h.FACILITY_ELECTRICITY, "Hourly", lambda m, d, hr: 4.0),
            ("", h.FACILITY_GAS, "Hourly", lambda m, d, hr: 1.0),
            ("", h.DISTRICT_HOT_WATER, "Hourly", lambda m, d, hr: 0.5),
            ("", h.DISTRICT_HOT_WATER, "Run Period", lambda m, d, hr: 0.0),
        ],
    )
    frame, src = h.read_hourly(sql)
    assert src[h.DISTRICT_COLUMN] == "meter"
    assert frame[h.DISTRICT_COLUMN].sum() == pytest.approx(0.5 * 48)
    assert frame["electricity_kwh"].sum() == pytest.approx(4.0 * 48)
    assert h.COLUMNS == ("heating_kwh", "cooling_kwh", "electricity_kwh", "gas_kwh")
    assert h.DISTRICT_COLUMN not in h.peaks(frame)


def test_district_series_absent_when_no_meter(tmp_path):
    sql = _make_sql(tmp_path / "e.sql", [("", h.FACILITY_GAS, "Hourly", lambda m, d, hr: 1.0)])
    frame, src = h.read_hourly(sql)
    assert src[h.DISTRICT_COLUMN] == "absent"
    assert frame[h.DISTRICT_COLUMN].isna().all()


def test_run_period_values_in_kwh_and_sidecar(tmp_path):
    sql = _make_sql(
        tmp_path / "r.sql",
        [
            ("", "Heating:NaturalGas", "Run Period", lambda m, d, hr: 10.0 / 48.0),
            ("", h.FACILITY_GAS, "Hourly", lambda m, d, hr: 1.0),
        ],
    )
    rp = h.run_period_kwh(sql)
    assert rp["heating_kwh"] == pytest.approx(10.0)
    assert np.isnan(rp["cooling_kwh"]) and np.isnan(rp[h.DISTRICT_COLUMN])
    summary = h.extract(sql, tmp_path / "o" / "x.csv.gz")
    assert summary["run_period_kwh"]["heating_kwh"] == pytest.approx(10.0)
    side = json.loads((tmp_path / "o" / "x.json").read_text())
    assert side["run_period_kwh"]["heating_kwh"] == pytest.approx(10.0)
    assert "district_hot_water_kwh" in side["sources"]
