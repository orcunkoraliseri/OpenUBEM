"""Tests for Phase-D metered EUI parsing (T06 — test_parser_hvac_metered.py).
Asserts _compute_eui maps four RunPeriod meters → EUI columns, fans separate.
Authorized deviation §0.1: cooling/heating from meters, not ideal-loads vars.
"""
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from openubem.results.parser import (
    _compute_eui,
    _parse_meters_sql,
    _failed_row,
)


def _make_row(footprint=100.0, num_floors=2):
    return pd.Series({
        "footprint_area_m2": footprint,
        "levels": num_floors,
        "height_m": num_floors * 3.5,
        "num_floors_override": None,
    })


def _make_hourly_df():
    """Minimal hourly DataFrame with lighting and equipment rows for 2 zones."""
    records = []
    for zone in ("way/123_F0_WHOLE", "way/123_F1_WHOLE"):
        for var in ("Zone Lights Electricity Energy", "Zone Electric Equipment Electricity Energy"):
            for h in range(8760):
                records.append({
                    "key_value": zone,
                    "variable_name": var,
                    "units": "kWh",
                    "Month": 1, "Day": 1, "Hour": h % 24 + 1,
                    "value": 1.0,  # 1 kWh per hour per zone
                })
    return pd.DataFrame(records)


def _make_sqlite_with_meters(
    tmp_dir: str,
    cooling_j=3.6e9,    # 1000 kWh
    heating_elec_j=0.0,
    heating_gas_j=7.2e9,  # 2000 kWh
    fans_j=1.8e9,         # 500 kWh
) -> Path:
    """Build a minimal SQLite with ReportData/ReportDataDictionary mimicking E+ meter output."""
    tmp = Path(tmp_dir) / "eplusout.sql"
    conn = sqlite3.connect(str(tmp))
    conn.execute("""
        CREATE TABLE ReportDataDictionary (
            ReportDataDictionaryIndex INTEGER PRIMARY KEY,
            Name TEXT,
            ReportingFrequency TEXT,
            KeyValue TEXT,
            Units TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE ReportData (
            ReportDataIndex INTEGER PRIMARY KEY,
            ReportDataDictionaryIndex INTEGER,
            TimeIndex INTEGER,
            Value REAL
        )
    """)
    meters = [
        (1, "Cooling:Electricity", cooling_j),
        (2, "Heating:Electricity", heating_elec_j),
        (3, "Heating:NaturalGas", heating_gas_j),
        (4, "Fans:Electricity", fans_j),
    ]
    for idx, name, val in meters:
        conn.execute(
            "INSERT INTO ReportDataDictionary VALUES (?,?,?,?,?)",
            (idx, name, "Run Period", "", "J"),
        )
        conn.execute(
            "INSERT INTO ReportData VALUES (?,?,?,?)",
            (idx, idx, 1, val),
        )
    conn.commit()
    conn.close()
    return tmp


class TestParseMetersSql:
    def test_reads_all_four_meters(self, tmp_path):
        sql = _make_sqlite_with_meters(
            str(tmp_path), cooling_j=3.6e9, heating_elec_j=0.0, heating_gas_j=7.2e9, fans_j=1.8e9
        )
        m = _parse_meters_sql(sql)
        assert abs(m["Cooling:Electricity"] - 1000.0) < 0.01
        assert abs(m["Heating:NaturalGas"] - 2000.0) < 0.01
        assert abs(m["Fans:Electricity"] - 500.0) < 0.01
        assert m["Heating:Electricity"] == 0.0

    def test_missing_meter_returns_zero(self, tmp_path):
        """All-electric building has no Heating:NaturalGas → 0.0, not KeyError."""
        sql = _make_sqlite_with_meters(str(tmp_path), cooling_j=3.6e9, heating_elec_j=3.6e8, heating_gas_j=0.0, fans_j=0.0)
        m = _parse_meters_sql(sql)
        assert m["Heating:NaturalGas"] == 0.0
        assert m["Heating:Electricity"] > 0

    def test_nonexistent_sql_returns_zeros(self):
        m = _parse_meters_sql(Path("/nonexistent/path.sql"))
        assert all(v == 0.0 for v in m.values())


class TestComputeEuiMetered:
    def test_cooling_and_heating_from_meters(self):
        """cooling_eui and heating_eui come from meter dict, not hourly df."""
        row = _make_row(footprint=100.0, num_floors=2)  # floor_area = 200 m²
        df = _make_hourly_df()
        meters = {
            "Cooling:Electricity": 2000.0,   # kWh
            "Heating:Electricity": 0.0,
            "Heating:NaturalGas": 4000.0,    # kWh
            "Fans:Electricity": 1000.0,
        }
        eui, dq, missing = _compute_eui(df, row, "", meters=meters)
        assert missing is None
        assert abs(eui["cooling_eui_kwh_m2"] - 10.0) < 1e-6   # 2000/200
        assert abs(eui["heating_eui_kwh_m2"] - 20.0) < 1e-6   # 4000/200
        assert abs(eui["fans_eui_kwh_m2"] - 5.0) < 1e-6       # 1000/200

    def test_fans_in_total_phaseE(self):
        """Phase-E D9: total_eui INCLUDES fans (+pumps/dhw/cooking/refrig) exactly once.
        Supersedes the Phase-D 'fans-excluded' expectation — CP-4 resolved to the D9
        whole-building site-energy total (parser.py:256, _compute_eui sums all 9 end-uses)."""
        row = _make_row(footprint=100.0, num_floors=2)
        df = _make_hourly_df()
        meters = {
            "Cooling:Electricity": 2000.0,
            "Heating:Electricity": 0.0,
            "Heating:NaturalGas": 4000.0,
            "Fans:Electricity": 1000.0,
        }
        eui, _, _ = _compute_eui(df, row, "", meters=meters)
        # Phase-E total = all 9 end-uses; only nonzero terms here are
        # cooling+heating+lighting+equipment+fans (pumps/dhw/cooking/refrig meters absent → 0).
        expected_total = (
            eui["cooling_eui_kwh_m2"]
            + eui["heating_eui_kwh_m2"]
            + eui["lighting_eui_kwh_m2"]
            + eui["equipment_eui_kwh_m2"]
            + eui["fans_eui_kwh_m2"]
        )
        assert abs(eui["total_eui_kwh_m2"] - expected_total) < 1e-9
        # fans counted exactly ONCE (P1 guard): total minus the four non-fans terms == fans
        non_fans = (
            eui["cooling_eui_kwh_m2"]
            + eui["heating_eui_kwh_m2"]
            + eui["lighting_eui_kwh_m2"]
            + eui["equipment_eui_kwh_m2"]
        )
        assert abs((eui["total_eui_kwh_m2"] - non_fans) - eui["fans_eui_kwh_m2"]) < 1e-9
        assert abs(eui["fans_eui_kwh_m2"] - 5.0) < 1e-6

    def test_missing_meter_is_zero_not_nan(self):
        """Absent meter (e.g. no gas) → 0.0 in EUI, not NaN, not failed_parse."""
        row = _make_row(footprint=100.0, num_floors=1)
        df = _make_hourly_df()
        # Empty meters dict — all meters absent
        eui, _, missing = _compute_eui(df, row, "", meters={})
        assert missing is None
        assert eui["cooling_eui_kwh_m2"] == 0.0
        assert eui["heating_eui_kwh_m2"] == 0.0
        assert eui["fans_eui_kwh_m2"] == 0.0

    def test_missing_lighting_variable_fails_parse(self):
        """Missing Zone Lights Electricity Energy → failed_parse (P10 C3)."""
        row = _make_row()
        # df with only equipment, no lighting
        df = pd.DataFrame([{
            "key_value": "way/123_F0_WHOLE",
            "variable_name": "Zone Electric Equipment Electricity Energy",
            "units": "kWh", "Month": 1, "Day": 1, "Hour": 1, "value": 1.0,
        }])
        eui, _, missing = _compute_eui(df, row, "", meters={})
        assert eui is None
        assert missing == "Zone Lights Electricity Energy"

    def test_heating_all_fuels_sum(self):
        """heating_eui_kwh_m2 = Heating:Electricity + Heating:NaturalGas."""
        row = _make_row(footprint=100.0, num_floors=1)
        df = _make_hourly_df()
        meters = {
            "Cooling:Electricity": 0.0,
            "Heating:Electricity": 500.0,
            "Heating:NaturalGas": 1500.0,
            "Fans:Electricity": 0.0,
        }
        eui, _, _ = _compute_eui(df, row, "", meters=meters)
        # floor_area = 100 * 1 = 100; heating = (500+1500)/100 = 20
        assert abs(eui["heating_eui_kwh_m2"] - 20.0) < 1e-6


class TestFailedRowHasFans:
    def test_failed_row_includes_fans_column(self):
        row = _failed_row("way/123", "failed_parse", "test error", "")
        assert "fans_eui_kwh_m2" in row
        import math
        assert math.isnan(row["fans_eui_kwh_m2"])
