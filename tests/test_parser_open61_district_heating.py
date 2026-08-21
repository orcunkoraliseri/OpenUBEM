"""OPEN-61 T01/T01b: district-heating DHW folded into dhw_eui_kwh_m2 / total_eui_kwh_m2.

`total_eui_kwh_m2` silently dropped the District Heating component of Water Systems
because `METER_QUERY` names ten meters and none of them is district heating, and no
such meter exists in any `.sql` on disk (plan F1). The remedy reads the value from
ABUPS (`TabularDataWithStrings`, AnnualBuildingUtilityPerformanceSummary, End Uses,
ColumnName='District Heating', RowName='Water Systems' — F11, T01b) through a
pseudo-meter key, `_DISTRICT_HEATING_KEY`, seeded into the same zeros dict
`_parse_meters_sql` already returns, so `_compute_eui`'s existing `_m()` / 0.0-default
contract covers it for free (F5). It is folded into `dhw_kwh` (F3: 100% Water Systems on
the fleet) and NOT added as an eleventh term to the D9 total (that would double-count it).

🔴 Load-bearing case: a `.sql` with no District Heating column must produce a
`total_eui_kwh_m2` bit-identical to what the pre-OPEN-61 parser produced, because the
fleet is 96.4%+ buildings that plausibly carry no district heating at all, and every
`.sql` written before this change has to keep reading the same.

🔴 T01b, OPEN-64: T01 originally read RowName='Total End Uses', which is wrong — the
total includes district heating serving OTHER end uses (e.g. space heating), not just
DHW. F11: on all 8,152 fleet census rows 'Total End Uses' and 'Water Systems' are
identical, but three golden fixtures (`tests/fixtures/golden_sql/r1_single_zone.sql`,
`r2_one_zone_per_floor.sql`, `r6_perimeter_core.sql` — pre-Phase-D, Ideal-Loads-style
HVAC) put 100% of their district heating in the `Heating` row and 0.00 in `Water
Systems` — the mirror image of the fleet. Reading 'Water Systems' (not the total) is
what makes those three golden `total_eui` tests pass again without touching their
expected values.
"""
import json
import sqlite3
from pathlib import Path

import pandas as pd

from openubem.results.parser import (
    _compute_eui,
    _parse_meters_sql,
    _read_abups_district_heating,
    parse_building,
    _DISTRICT_HEATING_KEY,
)

GJ_TO_KWH = 1_000_000.0 / 3600.0
GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden_sql"


def _make_row(footprint=100.0, num_floors=2):
    return pd.Series({
        "footprint_area_m2": footprint,
        "levels": num_floors,
        "height_m": num_floors * 3.5,
        "num_floors_override": None,
    })


def _make_hourly_df(equipment_kwh_total=200.0, lighting_kwh_total=100.0):
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


def _create_meter_tables(conn):
    conn.execute("""CREATE TABLE ReportDataDictionary (
        ReportDataDictionaryIndex INTEGER PRIMARY KEY, Name TEXT,
        ReportingFrequency TEXT, KeyValue TEXT, Units TEXT)""")
    conn.execute("""CREATE TABLE ReportData (
        ReportDataIndex INTEGER PRIMARY KEY, ReportDataDictionaryIndex INTEGER,
        TimeIndex INTEGER, Value REAL)""")


def _insert_meter(conn, idx, name, value_j):
    conn.execute("INSERT INTO ReportDataDictionary VALUES (?,?,?,?,?)",
                 (idx, name, "Run Period", "", "J"))
    conn.execute("INSERT INTO ReportData VALUES (?,?,?,?)", (idx, idx, 1, value_j))


def _create_tabular_table(conn):
    conn.execute("""CREATE TABLE TabularDataWithStrings (
        ReportName TEXT, TableName TEXT, ColumnName TEXT, RowName TEXT, Value TEXT)""")


def _insert_district_heating_row(conn, value, row_name="Water Systems"):
    conn.execute(
        "INSERT INTO TabularDataWithStrings VALUES (?,?,?,?,?)",
        ("AnnualBuildingUtilityPerformanceSummary", "End Uses", "District Heating",
         row_name, value),
    )


class TestAbupsDistrictHeatingReader:
    def test_positive_read_converts_gj_to_kwh(self, tmp_path):
        """(1) a synthetic .sql with a District Heating Water Systems row (F11, T01b)."""
        sql = tmp_path / "eplusout.sql"
        conn = sqlite3.connect(str(sql))
        _create_meter_tables(conn)
        _create_tabular_table(conn)
        _insert_district_heating_row(conn, "12.5")  # GJ
        conn.commit()
        conn.close()

        m = _parse_meters_sql(sql)
        expected_kwh = 12.5 * GJ_TO_KWH
        assert abs(m[_DISTRICT_HEATING_KEY] - expected_kwh) < 1e-6

    def test_dhw_eui_is_gas_plus_elec_plus_district(self):
        row = _make_row(footprint=100.0, num_floors=2)  # floor_area = 200
        df = _make_hourly_df()
        meters = {
            "WaterSystems:NaturalGas": 8.0,
            "WaterSystems:Electricity": 1.0,
            _DISTRICT_HEATING_KEY: 40.0,
        }
        eui, _, missing = _compute_eui(df, row, "", meters=meters)
        assert missing is None
        assert abs(eui["dhw_district_eui_kwh_m2"] - 40.0 / 200.0) < 1e-12
        assert abs(eui["dhw_eui_kwh_m2"] - (8.0 + 1.0 + 40.0) / 200.0) < 1e-12


class TestBackwardsCompatibility:
    def test_no_district_heating_column_reads_zero_and_total_unchanged(self, tmp_path):
        """(2) LOAD-BEARING: a .sql with no District Heating column (TabularDataWithStrings
        present — as in every real fleet .sql, F2 — but carrying no District Heating row,
        the shape of a non-DH building) → dhw_district_eui_kwh_m2 == 0.0 and
        total_eui_kwh_m2 bit-identical to the literal the pre-OPEN-61 parser produced
        for this exact fixture (asserted against a literal, not a re-computation)."""
        sql = tmp_path / "eplusout.sql"
        conn = sqlite3.connect(str(sql))
        _create_meter_tables(conn)
        _insert_meter(conn, 1, "Cooling:Electricity", 1.8e8)       # 50 kWh
        _insert_meter(conn, 2, "Heating:Electricity", 1.08e8)      # 30 kWh
        _insert_meter(conn, 3, "Heating:NaturalGas", 7.2e7)        # 20 kWh
        _insert_meter(conn, 4, "Fans:Electricity", 3.6e7)          # 10 kWh
        _insert_meter(conn, 5, "Pumps:Electricity", 1.8e7)         # 5 kWh
        _insert_meter(conn, 6, "WaterSystems:NaturalGas", 2.88e7)  # 8 kWh
        _insert_meter(conn, 7, "WaterSystems:Electricity", 3.6e6)  # 1 kWh
        _insert_meter(conn, 8, "InteriorEquipment:NaturalGas", 1.08e7)  # 3 kWh
        _create_tabular_table(conn)
        conn.execute(
            "INSERT INTO TabularDataWithStrings VALUES (?,?,?,?,?)",
            ("AnnualBuildingUtilityPerformanceSummary", "End Uses", "Electricity",
             "Total End Uses", "5.0"),
        )  # ABUPS present (as every real fleet .sql is), no District Heating row.
        conn.commit()
        conn.close()

        meters = _parse_meters_sql(sql)
        assert meters[_DISTRICT_HEATING_KEY] == 0.0

        row = _make_row(footprint=100.0, num_floors=2)  # floor_area = 200
        df = _make_hourly_df(equipment_kwh_total=200.0, lighting_kwh_total=100.0)
        eui, _, missing = _compute_eui(df, row, "", meters=meters, floor_area=200.0)
        assert missing is None
        assert eui["dhw_district_eui_kwh_m2"] == 0.0

        # Literal computed by hand from the meters above, BEFORE this change existed:
        # cooling=50 heating=50 lighting=100/200=0.5 equipment=200/200=1.0 fans=10
        # pumps=5 dhw=(8+1)=9 cooking=3 refrigeration=0 elevators=0, all / floor_area=200
        # except lighting/equipment already per-m2 above.
        expected_total = (
            50.0 / 200.0 + 50.0 / 200.0 + 0.5 + 1.0 + 10.0 / 200.0 + 5.0 / 200.0
            + 9.0 / 200.0 + 3.0 / 200.0 + 0.0 + 0.0
        )
        assert abs(eui["total_eui_kwh_m2"] - expected_total) < 1e-12

    def test_table_present_no_matching_row_reads_zero(self, tmp_path):
        """A .sql whose TabularDataWithStrings table exists (other ABUPS reads use it)
        but carries no District Heating row for this building — the common real-fleet
        shape for a non-DH building — also reads 0.0."""
        sql = tmp_path / "eplusout.sql"
        conn = sqlite3.connect(str(sql))
        _create_meter_tables(conn)
        _create_tabular_table(conn)
        conn.execute(
            "INSERT INTO TabularDataWithStrings VALUES (?,?,?,?,?)",
            ("AnnualBuildingUtilityPerformanceSummary", "End Uses", "Electricity",
             "Total End Uses", "5.0"),
        )
        conn.commit()
        conn.close()
        m = _parse_meters_sql(sql)
        assert m[_DISTRICT_HEATING_KEY] == 0.0


class TestNoRaiseGuards:
    def test_unreadable_or_nonexistent_path_returns_zero(self, tmp_path):
        """(3) A nonexistent path: no such file → sqlite3.connect + query raises,
        caught by the existing except-clause → 0.0, no raise."""
        sql = tmp_path / "does_not_exist.sql"
        m = _parse_meters_sql(sql)
        assert m[_DISTRICT_HEATING_KEY] == 0.0

    def test_blank_abups_value_returns_zero(self, tmp_path):
        """(4) A blank-string ABUPS value → 0.0, no raise."""
        sql = tmp_path / "eplusout.sql"
        conn = sqlite3.connect(str(sql))
        _create_meter_tables(conn)
        _create_tabular_table(conn)
        _insert_district_heating_row(conn, "")
        conn.commit()
        conn.close()
        m = _parse_meters_sql(sql)
        assert m[_DISTRICT_HEATING_KEY] == 0.0

    def test_none_abups_value_returns_zero(self, tmp_path):
        """(4) A NULL ABUPS value → 0.0, no raise."""
        sql = tmp_path / "eplusout.sql"
        conn = sqlite3.connect(str(sql))
        _create_meter_tables(conn)
        _create_tabular_table(conn)
        _insert_district_heating_row(conn, None)
        conn.commit()
        conn.close()
        m = _parse_meters_sql(sql)
        assert m[_DISTRICT_HEATING_KEY] == 0.0

    def test_reader_called_directly_on_open_connection(self, tmp_path):
        """_read_abups_district_heating() itself, called on an open connection, per F5."""
        sql = tmp_path / "eplusout.sql"
        conn = sqlite3.connect(str(sql))
        _create_tabular_table(conn)
        _insert_district_heating_row(conn, "1.0")  # 1 GJ
        conn.commit()
        result = _read_abups_district_heating(conn)
        conn.close()
        assert abs(result - GJ_TO_KWH) < 1e-9


class TestD9InvariantWithDistrictHeating:
    def test_total_equals_sum_of_ten_columns_not_double_counted(self):
        """(5) total_eui_kwh_m2 still equals the sum of the ten end-use columns, with
        district heating folded inside dhw_eui_kwh_m2 and not counted a second time."""
        row = _make_row(footprint=100.0, num_floors=2)
        df = _make_hourly_df(equipment_kwh_total=200.0, lighting_kwh_total=100.0)
        meters = {
            "Cooling:Electricity": 50.0,
            "Heating:Electricity": 30.0,
            "Heating:NaturalGas": 20.0,
            "Fans:Electricity": 10.0,
            "Pumps:Electricity": 5.0,
            "WaterSystems:NaturalGas": 8.0,
            "WaterSystems:Electricity": 1.0,
            _DISTRICT_HEATING_KEY: 40.0,
            "InteriorEquipment:NaturalGas": 3.0,
            "Refrigeration:Electricity": 0.0,
        }
        eui, _, missing = _compute_eui(df, row, "", meters=meters)
        assert missing is None
        col_sum = (
            eui["cooling_eui_kwh_m2"] + eui["heating_eui_kwh_m2"]
            + eui["lighting_eui_kwh_m2"] + eui["equipment_eui_kwh_m2"]
            + eui["fans_eui_kwh_m2"] + eui["pumps_eui_kwh_m2"]
            + eui["dhw_eui_kwh_m2"] + eui["cooking_eui_kwh_m2"]
            + eui["refrigeration_eui_kwh_m2"] + eui["elevators_eui_kwh_m2"]
        )
        assert abs(eui["total_eui_kwh_m2"] - col_sum) < 1e-12
        # district heating is inside dhw_eui_kwh_m2, not a separate summand of the total
        assert eui["dhw_eui_kwh_m2"] >= eui["dhw_district_eui_kwh_m2"]
        assert abs(
            eui["dhw_eui_kwh_m2"]
            - (eui["dhw_gas_eui_kwh_m2"] + eui["dhw_elec_eui_kwh_m2"] + eui["dhw_district_eui_kwh_m2"])
        ) < 1e-12


class TestDistrictHeatingServingSpaceHeatingNotFoldedIn:
    """OPEN-64 / T01b guard: a real .sql (tests/fixtures/golden_sql/r1_single_zone.sql) whose
    District Heating column has a non-zero Heating row and a zero Water Systems row must read
    dhw_district_eui_kwh_m2 == 0.0, and total_eui_kwh_m2 must be bit-identical to the
    no-district-heating case — the golden_expected.json total, computed before OPEN-61 existed
    and therefore with no district-heating contribution at all. This is the fixture that broke
    T01's original 'Total End Uses' read (148.24 GJ, 100% under Heating, F11) and is used here
    directly per the director's T01b instruction rather than a fresh synthetic .sql."""

    def test_r1_district_heating_serving_heating_reads_zero_and_total_matches_golden(self):
        with open(GOLDEN_DIR / "golden_expected.json", encoding="utf-8") as fh:
            expected = json.load(fh)

        sql = GOLDEN_DIR / "r1_single_zone.sql"
        m = _parse_meters_sql(sql)
        assert m[_DISTRICT_HEATING_KEY] == 0.0

        row = pd.Series({
            "osm_id": "way/R1", "footprint_area_m2": 196.0, "levels": 2.0,
            "height_m": float("nan"), "num_zones": 1, "data_quality_flag": "",
        })
        result = parse_building(sql, None, row)
        assert result["dhw_district_eui_kwh_m2"] == 0.0

        exp_total = expected["R1"]["eui"]["total_eui_kwh_m2"]
        assert abs(result["total_eui_kwh_m2"] - exp_total) < 1e-6 * abs(exp_total)
