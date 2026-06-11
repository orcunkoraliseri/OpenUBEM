"""Unit tests for openubem.results.parser (T08)."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import pytest

GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden_sql"
EXPECTED_JSON = GOLDEN_DIR / "golden_expected.json"


@pytest.fixture(scope="module")
def expected():
    with open(EXPECTED_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def _manifest_row(osm_id: str, footprint_m2: float, num_floors: int, num_zones: int) -> pd.Series:
    return pd.Series({
        "osm_id": osm_id,
        "footprint_area_m2": footprint_m2,
        "levels": float(num_floors),
        "height_m": float("nan"),
        "num_zones": num_zones,
        "data_quality_flag": "",
    })


# ── T04/T05 parse_building_sql ────────────────────────────────────────────────

class TestParseBuildingSql:
    def test_returns_dataframe(self):
        from openubem.results.parser import parse_building_sql
        sql = GOLDEN_DIR / "r1_single_zone.sql"
        df = parse_building_sql(sql)
        assert isinstance(df, pd.DataFrame)
        assert set(["key_value", "variable_name", "units", "Month", "Day", "Hour", "value"]).issubset(df.columns)

    def test_no_j_units_remaining(self):
        """J→kWh conversion must happen exactly once at parse boundary (DESIGN §3A)."""
        from openubem.results.parser import parse_building_sql
        sql = GOLDEN_DIR / "r1_single_zone.sql"
        df = parse_building_sql(sql)
        assert "J" not in df["units"].values, "J units still present after conversion"

    def test_energy_values_are_small_positive(self):
        """After J→kWh, energy values must be << 1e6 (if in J they would be ~1e9)."""
        from openubem.results.parser import parse_building_sql
        sql = GOLDEN_DIR / "r1_single_zone.sql"
        df = parse_building_sql(sql)
        energy_rows = df[df["variable_name"].str.contains("Energy")]
        assert energy_rows["value"].max() < 1e6, "Suspiciously large value — J→kWh conversion may have been skipped or doubled"

    def test_j_to_kwh_single_conversion(self):
        """Verify J→kWh factor is exactly 1/3.6e6 (not applied twice)."""
        from openubem.results.parser import J_TO_KWH, parse_building_sql
        assert abs(J_TO_KWH - 1.0 / 3.6e6) < 1e-20
        # Load and check that the total heating kWh is in a plausible range
        sql = GOLDEN_DIR / "r1_single_zone.sql"
        df = parse_building_sql(sql)
        heat = df[df["variable_name"] == "Zone Ideal Loads Zone Total Heating Energy"]["value"].sum()
        # Plausibility: 196 m² × 2 floors × [10, 500] kWh/m²
        assert 10 * 392 < heat < 500 * 392, f"Heating kWh={heat:.1f} implausible; likely double-conversion"


class TestZoneRx:
    def test_single_zone_pattern(self):
        from openubem.results.parser import ZONE_RX
        m = ZONE_RX.match("WAY/R1_F1_WHOLE")
        assert m is not None
        assert m["osm_id"] == "WAY/R1"
        assert m["floor"] == "1"
        assert m["label"] == "WHOLE"

    def test_perimeter_core_pattern(self):
        from openubem.results.parser import ZONE_RX
        m = ZONE_RX.match("WAY/R6_F2_PERIM")
        assert m is not None
        assert m["osm_id"] == "WAY/R6"
        assert m["floor"] == "2"
        assert m["label"] == "PERIM"

    def test_block_prefix_stripped(self):
        from openubem.results.parser import ZONE_RX
        m = ZONE_RX.match("BLOCK WAY/R6_F1_CORE")
        assert m is not None
        assert m["osm_id"] == "WAY/R6"

    def test_non_zone_key_returns_none(self):
        from openubem.results.parser import resolve_zone
        assert resolve_zone("WHOLE BUILDING") is None
        assert resolve_zone("Outdoor Air") is None

    def test_foreign_osm_id_detected(self):
        from openubem.results.parser import resolve_zone
        parsed = resolve_zone("WAY/FOREIGN_F1_WHOLE")
        assert parsed is not None
        assert parsed["osm_id_uc"] == "WAY/FOREIGN"


# ── T05: integrity checks ─────────────────────────────────────────────────────

class TestIntegrityChecks:
    def test_foreign_osm_id_raises(self):
        """I2 breach: SQL contains a zone belonging to a different building → RuntimeError."""
        from openubem.results.parser import parse_building
        row = _manifest_row("way/R1", 196.0, 2, 1)
        sql = GOLDEN_DIR / "r1_foreign_osm_id.sql"
        with pytest.raises(RuntimeError, match="I2 breach"):
            parse_building(sql, None, row)

    def test_missing_zone_returns_failed_status(self):
        """I1: zone count mismatch → failed_zone_mismatch (not exception)."""
        from openubem.results.parser import parse_building
        # R2 has 4 floors, but missing_zone fixture only has 3 zones
        row = _manifest_row("way/R2", 625.0, 4, 4)
        sql = GOLDEN_DIR / "r2_missing_zone.sql"
        result = parse_building(sql, None, row)
        assert result["parse_status"] == "failed_zone_mismatch"
        assert math.isnan(result["total_eui_kwh_m2"])


# ── T04: CSV fallback ─────────────────────────────────────────────────────────

class TestCsvFallback:
    def test_csv_fallback_triggers(self):
        """CSV path used when SQL is absent; parse_status = success_csv_fallback."""
        from openubem.results.parser import parse_building
        row = _manifest_row("way/R1", 196.0, 2, 1)
        # Pass a non-existent SQL path so fallback is triggered
        result = parse_building(
            sql_path=GOLDEN_DIR / "nonexistent.sql",
            csv_path=GOLDEN_DIR / "r1_single_zone.csv",
            manifest_row=row,
        )
        assert result["parse_status"] == "success_csv_fallback"
        assert "RESULTS_CSV_FALLBACK" in result["data_quality_flag"]

    def test_no_sql_no_csv_failed_parse(self):
        """Both missing → failed_parse status."""
        from openubem.results.parser import parse_building
        row = _manifest_row("way/R1", 196.0, 2, 1)
        result = parse_building(
            sql_path=GOLDEN_DIR / "nonexistent.sql",
            csv_path=None,
            manifest_row=row,
        )
        assert result["parse_status"] == "failed_parse"
        assert math.isnan(result["total_eui_kwh_m2"])


# ── C3: P10 missing-variable guard (C3-enforced: failed_parse, never 0.0) ────

class TestP10MissingVariable:
    def test_missing_lighting_gives_failed_parse(self):
        """C3/P10: absent required EUI variable → failed_parse + variable named in error_summary."""
        from openubem.results.parser import parse_building
        import math
        row = _manifest_row("way/R1", 196.0, 2, 1)
        # r1_missing_lighting.sql has Zone Lights Electricity Energy removed
        result = parse_building(GOLDEN_DIR / "r1_missing_lighting.sql", None, row)
        assert result["parse_status"] == "failed_parse"
        assert "Zone Lights Electricity Energy" in result["error_summary"]
        assert math.isnan(result["total_eui_kwh_m2"])

    def test_missing_variable_all_metrics_nan(self):
        """C3/P10: failed_parse → all five EUI columns NaN (no silent zeros)."""
        from openubem.results.parser import parse_building
        import math
        row = _manifest_row("way/R1", 196.0, 2, 1)
        result = parse_building(GOLDEN_DIR / "r1_missing_lighting.sql", None, row)
        for col in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
                    "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
            assert math.isnan(result[col]), f"{col} should be NaN on failed_parse"


# ── T06: EUI golden values ────────────────────────────────────────────────────

class TestEuiGolden:
    _REL_TOL = 1e-6

    def _run(self, key, fixture_name, footprint, floors, n_zones):
        from openubem.results.parser import parse_building
        row = _manifest_row(f"way/{key}", footprint, floors, n_zones)
        sql = GOLDEN_DIR / fixture_name
        return parse_building(sql, None, row)

    def test_r1_heating_eui(self, expected):
        result = self._run("R1", "r1_single_zone.sql", 196.0, 2, 1)
        exp = expected["R1"]["eui"]["heating_eui_kwh_m2"]
        assert math.isclose(result["heating_eui_kwh_m2"], exp, rel_tol=self._REL_TOL), \
            f"R1 heating EUI: got {result['heating_eui_kwh_m2']}, expected {exp}"

    def test_r1_cooling_eui(self, expected):
        result = self._run("R1", "r1_single_zone.sql", 196.0, 2, 1)
        exp = expected["R1"]["eui"]["cooling_eui_kwh_m2"]
        assert math.isclose(result["cooling_eui_kwh_m2"], exp, rel_tol=self._REL_TOL)

    def test_r1_lighting_eui(self, expected):
        result = self._run("R1", "r1_single_zone.sql", 196.0, 2, 1)
        exp = expected["R1"]["eui"]["lighting_eui_kwh_m2"]
        assert math.isclose(result["lighting_eui_kwh_m2"], exp, rel_tol=self._REL_TOL)

    def test_r1_total_eui(self, expected):
        result = self._run("R1", "r1_single_zone.sql", 196.0, 2, 1)
        exp = expected["R1"]["eui"]["total_eui_kwh_m2"]
        assert math.isclose(result["total_eui_kwh_m2"], exp, rel_tol=self._REL_TOL)

    def test_r2_heating_eui(self, expected):
        result = self._run("R2", "r2_one_zone_per_floor.sql", 625.0, 4, 4)
        exp = expected["R2"]["eui"]["heating_eui_kwh_m2"]
        assert math.isclose(result["heating_eui_kwh_m2"], exp, rel_tol=self._REL_TOL)

    def test_r2_total_eui(self, expected):
        result = self._run("R2", "r2_one_zone_per_floor.sql", 625.0, 4, 4)
        exp = expected["R2"]["eui"]["total_eui_kwh_m2"]
        assert math.isclose(result["total_eui_kwh_m2"], exp, rel_tol=self._REL_TOL)

    def test_r6_heating_eui(self, expected):
        result = self._run("R6", "r6_perimeter_core.sql", 1500.0, 3, 15)
        exp = expected["R6"]["eui"]["heating_eui_kwh_m2"]
        assert math.isclose(result["heating_eui_kwh_m2"], exp, rel_tol=self._REL_TOL)

    def test_r6_cooling_eui(self, expected):
        result = self._run("R6", "r6_perimeter_core.sql", 1500.0, 3, 15)
        exp = expected["R6"]["eui"]["cooling_eui_kwh_m2"]
        assert math.isclose(result["cooling_eui_kwh_m2"], exp, rel_tol=self._REL_TOL)

    def test_r6_total_eui(self, expected):
        result = self._run("R6", "r6_perimeter_core.sql", 1500.0, 3, 15)
        exp = expected["R6"]["eui"]["total_eui_kwh_m2"]
        assert math.isclose(result["total_eui_kwh_m2"], exp, rel_tol=self._REL_TOL)


# ── T06: IOD golden values ────────────────────────────────────────────────────

class TestIodGolden:
    _REL_TOL = 1e-5

    def _run(self, key, fixture_name, footprint, floors, n_zones):
        from openubem.results.parser import parse_building
        row = _manifest_row(f"way/{key}", footprint, floors, n_zones)
        sql = GOLDEN_DIR / fixture_name
        return parse_building(sql, None, row)

    def test_r1_iod(self, expected):
        result = self._run("R1", "r1_single_zone.sql", 196.0, 2, 1)
        exp = expected["R1"]["iod"]
        assert exp is not None
        assert math.isclose(result["iod"], exp, rel_tol=self._REL_TOL), \
            f"R1 IOD: got {result['iod']}, expected {exp}"

    def test_r2_iod(self, expected):
        result = self._run("R2", "r2_one_zone_per_floor.sql", 625.0, 4, 4)
        exp = expected["R2"]["iod"]
        assert exp is not None
        assert math.isclose(result["iod"], exp, rel_tol=self._REL_TOL)

    def test_r6_iod(self, expected):
        result = self._run("R6", "r6_perimeter_core.sql", 1500.0, 3, 15)
        exp = expected["R6"]["iod"]
        assert exp is not None
        assert math.isclose(result["iod"], exp, rel_tol=self._REL_TOL)

    def test_zero_occupancy_gives_nan_iod(self):
        """Zero occupancy → iod=NaN + IOD_NO_OCCUPIED_HOURS flag."""
        from openubem.results.parser import parse_building
        row = _manifest_row("way/R1", 196.0, 2, 1)
        result = parse_building(GOLDEN_DIR / "r1_zero_occupancy.sql", None, row)
        assert math.isnan(result["iod"])
        assert "IOD_NO_OCCUPIED_HOURS" in result["data_quality_flag"]
