"""T05: Elevators surfaced as its own end-use column in the results breakdown.

Elevators are ElectricEquipment, so their kWh is already inside the hourly
`Zone Electric Equipment Electricity Energy` (equipment_eui) and therefore already
in total. T05 breaks them out into a mutually-exclusive 10th end-use while keeping
BOTH total_eui and gwp_total numerically invariant.
"""
import sqlite3
from pathlib import Path

import pandas as pd

from openubem.results.parser import _compute_eui, _parse_meters_sql, _failed_row
from openubem.results.carbon import compute_gwp


def _make_row(footprint=100.0, num_floors=2):
    return pd.Series({
        "footprint_area_m2": footprint,
        "levels": num_floors,
        "height_m": num_floors * 3.5,
        "num_floors_override": None,
    })


def _make_hourly_df(equipment_kwh_total=200.0, lighting_kwh_total=100.0):
    """Hourly df where the equipment total INCLUDES the elevator portion (as it does
    in a real IDF — the elevator is ElectricEquipment in the zone)."""
    records = []
    eq_per_hour = equipment_kwh_total / 8760.0
    lt_per_hour = lighting_kwh_total / 8760.0
    for h in range(8760):
        records.append({"key_value": "way/123_F0_WHOLE",
                        "variable_name": "Zone Lights Electricity Energy",
                        "units": "kWh", "Month": 1, "Day": 1, "Hour": h % 24 + 1,
                        "value": lt_per_hour})
        records.append({"key_value": "way/123_F0_WHOLE",
                        "variable_name": "Zone Electric Equipment Electricity Energy",
                        "units": "kWh", "Month": 1, "Day": 1, "Hour": h % 24 + 1,
                        "value": eq_per_hour})
    return pd.DataFrame(records)


def _make_sqlite_with_elevator_meter(tmp_dir, elevator_j=2.16e8):  # 60 kWh
    tmp = Path(tmp_dir) / "eplusout.sql"
    conn = sqlite3.connect(str(tmp))
    conn.execute("""CREATE TABLE ReportDataDictionary (
        ReportDataDictionaryIndex INTEGER PRIMARY KEY, Name TEXT,
        ReportingFrequency TEXT, KeyValue TEXT, Units TEXT)""")
    conn.execute("""CREATE TABLE ReportData (
        ReportDataIndex INTEGER PRIMARY KEY, ReportDataDictionaryIndex INTEGER,
        TimeIndex INTEGER, Value REAL)""")
    conn.execute("INSERT INTO ReportDataDictionary VALUES (?,?,?,?,?)",
                 (1, "Elevators:InteriorEquipment:Electricity", "Run Period", "", "J"))
    conn.execute("INSERT INTO ReportData VALUES (?,?,?,?)", (1, 1, 1, elevator_j))
    conn.commit()
    conn.close()
    return tmp


class TestElevatorMeterParsed:
    def test_elevator_meter_read(self, tmp_path):
        sql = _make_sqlite_with_elevator_meter(str(tmp_path), elevator_j=2.16e8)
        m = _parse_meters_sql(sql)
        assert abs(m["Elevators:InteriorEquipment:Electricity"] - 60.0) < 0.01

    def test_missing_elevator_meter_is_zero(self, tmp_path):
        """A no-elevator building has no such meter → 0.0, not KeyError."""
        # SQLite with only a cooling meter, no elevators
        tmp = Path(tmp_path) / "eplusout.sql"
        conn = sqlite3.connect(str(tmp))
        conn.execute("""CREATE TABLE ReportDataDictionary (
            ReportDataDictionaryIndex INTEGER PRIMARY KEY, Name TEXT,
            ReportingFrequency TEXT, KeyValue TEXT, Units TEXT)""")
        conn.execute("""CREATE TABLE ReportData (
            ReportDataIndex INTEGER PRIMARY KEY, ReportDataDictionaryIndex INTEGER,
            TimeIndex INTEGER, Value REAL)""")
        conn.execute("INSERT INTO ReportDataDictionary VALUES (?,?,?,?,?)",
                     (1, "Cooling:Electricity", "Run Period", "", "J"))
        conn.execute("INSERT INTO ReportData VALUES (?,?,?,?)", (1, 1, 1, 3.6e9))
        conn.commit()
        conn.close()
        m = _parse_meters_sql(tmp)
        assert m["Elevators:InteriorEquipment:Electricity"] == 0.0


class TestElevatorsBrokenOut:
    def test_elevators_is_own_column(self):
        """(a) elevators_eui_kwh_m2 appears as its own EUI column."""
        row = _make_row(footprint=100.0, num_floors=2)  # floor_area = 200
        df = _make_hourly_df(equipment_kwh_total=200.0)
        meters = {"Elevators:InteriorEquipment:Electricity": 60.0}
        eui, _, missing = _compute_eui(df, row, "", meters=meters)
        assert missing is None
        assert "elevators_eui_kwh_m2" in eui
        assert abs(eui["elevators_eui_kwh_m2"] - 60.0 / 200.0) < 1e-9  # 0.3

    def test_elevators_defolded_from_equipment(self):
        """Equipment EUI is reduced by the elevator portion (no longer folds it in)."""
        row = _make_row(footprint=100.0, num_floors=2)  # floor_area = 200
        df = _make_hourly_df(equipment_kwh_total=200.0)
        meters = {"Elevators:InteriorEquipment:Electricity": 60.0}
        eui, _, _ = _compute_eui(df, row, "", meters=meters)
        # raw equipment hourly sum = 200 kWh / 200 m² = 1.0; minus elevators 0.3 → 0.7
        assert abs(eui["equipment_eui_kwh_m2"] - (200.0 - 60.0) / 200.0) < 1e-9

    def test_total_unchanged_vs_summing_columns(self):
        """(b) total EUI == sum of the 10 mutually-exclusive end-use columns."""
        row = _make_row(footprint=100.0, num_floors=2)
        df = _make_hourly_df(equipment_kwh_total=200.0, lighting_kwh_total=100.0)
        meters = {"Elevators:InteriorEquipment:Electricity": 60.0}
        eui, _, _ = _compute_eui(df, row, "", meters=meters)
        col_sum = (
            eui["cooling_eui_kwh_m2"] + eui["heating_eui_kwh_m2"]
            + eui["lighting_eui_kwh_m2"] + eui["equipment_eui_kwh_m2"]
            + eui["fans_eui_kwh_m2"] + eui["pumps_eui_kwh_m2"]
            + eui["dhw_eui_kwh_m2"] + eui["cooking_eui_kwh_m2"]
            + eui["refrigeration_eui_kwh_m2"] + eui["elevators_eui_kwh_m2"]
        )
        assert abs(eui["total_eui_kwh_m2"] - col_sum) < 1e-12

    def test_total_invariant_to_breakout(self):
        """total is the SAME whether elevators are broken out or left folded in equipment.

        With elevator meter = 60 kWh the total must equal the total computed with the
        elevator meter absent (0) — because the 60 kWh is inside the equipment hourly
        variable either way; the breakout only redistributes it between two columns.
        """
        row = _make_row(footprint=100.0, num_floors=2)
        df = _make_hourly_df(equipment_kwh_total=200.0, lighting_kwh_total=100.0)
        eui_broken, _, _ = _compute_eui(df, row, "", meters={"Elevators:InteriorEquipment:Electricity": 60.0})
        eui_folded, _, _ = _compute_eui(df, row, "", meters={})
        assert abs(eui_broken["total_eui_kwh_m2"] - eui_folded["total_eui_kwh_m2"]) < 1e-12
        # and in the folded case the whole 200 kWh sits in equipment, elevators = 0
        assert abs(eui_folded["elevators_eui_kwh_m2"] - 0.0) < 1e-12
        assert abs(eui_folded["equipment_eui_kwh_m2"] - 1.0) < 1e-12


class TestGwpInvariant:
    def test_gwp_total_invariant_to_breakout(self):
        """gwp_total is unchanged by the elevator breakout (elevator carbon just moves
        from gwp_equipment into gwp_elevators)."""
        row = _make_row(footprint=100.0, num_floors=2)
        df = _make_hourly_df(equipment_kwh_total=200.0, lighting_kwh_total=100.0)
        eui_broken, _, _ = _compute_eui(df, row, "", meters={"Elevators:InteriorEquipment:Electricity": 60.0})
        eui_folded, _, _ = _compute_eui(df, row, "", meters={})
        gwp_broken = compute_gwp(eui_broken, "NY")
        gwp_folded = compute_gwp(eui_folded, "NY")
        assert "gwp_elevators_kgco2_m2" in gwp_broken
        assert abs(gwp_broken["gwp_total_kgco2_m2"] - gwp_folded["gwp_total_kgco2_m2"]) < 1e-9
        # elevator carbon accounted exactly once: gwp_equipment(broken)+gwp_elevators == gwp_equipment(folded)
        assert abs(
            (gwp_broken["gwp_equipment_kgco2_m2"] + gwp_broken["gwp_elevators_kgco2_m2"])
            - gwp_folded["gwp_equipment_kgco2_m2"]
        ) < 1e-9


class TestFailedRowHasElevators:
    def test_failed_row_includes_elevators_column(self):
        import math
        row = _failed_row("way/123", "failed_parse", "err", "")
        assert "elevators_eui_kwh_m2" in row
        assert math.isnan(row["elevators_eui_kwh_m2"])
