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
        """I1: zone count mismatch is tolerated under relaxed check, but lacking EUI vars yields failed_parse."""
        from openubem.results.parser import parse_building
        # R2 has 4 floors, but missing_zone fixture only has 3 zones
        row = _manifest_row("way/R2", 625.0, 4, 4)
        sql = GOLDEN_DIR / "r2_missing_zone.sql"
        result = parse_building(sql, None, row)
        assert result["parse_status"] == "failed_parse"
        assert math.isnan(result["total_eui_kwh_m2"])


# ── T14 (E-LA-05 fix): resolution_mode-aware zone-integrity gate ─────────────

class TestLayoutAssignZoneIntegrity:
    """layout_assign baseline zones keep DOE-native names (e.g. "G SW APARTMENT") that never
    encode an osm_id and structurally cannot match ZONE_RX. _check_zone_integrity() must accept
    a resolution_mode override for this mode while leaving every other mode's behavior untouched.
    """

    @staticmethod
    def _doe_zone_df() -> pd.DataFrame:
        # Native DOE baseline zone names, never renamed to the OpenUBEM {osm_id}_F{floor}_{label} convention.
        return pd.DataFrame({
            "variable_name": ["Zone Lights Electricity Energy"] * 2,
            "key_value": ["OFFICE", "G SW APARTMENT"],
        })

    def test_layout_assign_mode_passes_with_doe_zone_names(self):
        """DOE-native zone keys must pass the light sanity check under resolution_mode='layout_assign'."""
        from openubem.results.parser import _check_zone_integrity
        df = self._doe_zone_df()
        status, msg = _check_zone_integrity(df, "way/t12_local_leg_MediumOffice", 18, resolution_mode="layout_assign")
        assert status is None
        assert msg is None

    def test_layout_assigner_alias_also_passes(self):
        """'layout_assigner' spelling is accepted identically to 'layout_assign'."""
        from openubem.results.parser import _check_zone_integrity
        df = self._doe_zone_df()
        status, msg = _check_zone_integrity(df, "way/t12_local_leg_MediumOffice", 18, resolution_mode="layout_assigner")
        assert status is None
        assert msg is None

    def test_same_fixture_without_resolution_mode_still_fails(self):
        """Regression guard: default resolution_mode=None leaves every other mode's behavior
        unchanged — the same DOE-style-key fixture still fails the old ZONE_RX-based check."""
        from openubem.results.parser import _check_zone_integrity
        df = self._doe_zone_df()
        status, msg = _check_zone_integrity(df, "way/t12_local_leg_MediumOffice", 18)
        assert status == "failed_zone_mismatch"
        assert "found 0" in msg

    def test_layout_assign_corrupt_empty_sql_still_fails(self):
        """Empty/corrupt SQL (zero zone-level keys at all) must still fail even under layout_assign."""
        from openubem.results.parser import _check_zone_integrity
        df = pd.DataFrame({
            "variable_name": ["Site Outdoor Air Drybulb Temperature"],
            "key_value": ["Environment"],
        })
        status, msg = _check_zone_integrity(df, "way/t12_local_leg_MediumOffice", 18, resolution_mode="layout_assign")
        assert status == "failed_zone_mismatch"
        assert "layout_assign" in msg

    def test_parse_building_reads_resolution_mode_from_manifest_row(self):
        """parse_building() threads manifest_row['resolution_mode'] through to _check_zone_integrity();
        a layout_assign-flagged row with DOE-style zone names must not fail on zone integrity alone
        (it may still fail later on missing EUI variables — this fixture only has Lights)."""
        from openubem.results.parser import parse_building, _check_zone_integrity
        row = _manifest_row("way/t12_local_leg_MediumOffice", 8000.0, 4, 18)
        row["resolution_mode"] = "layout_assign"
        # Directly verify the gate _check_zone_integrity would apply inside parse_building()
        # (parse_building() itself needs a real SQL file; that path is covered by the standalone
        # re-run of the 6 real T12 local-leg SQL files, not a repo fixture — see T14 §8 notes).
        df = self._doe_zone_df()
        status, msg = _check_zone_integrity(
            df, str(row["osm_id"]), int(row["num_zones"]), resolution_mode=row.get("resolution_mode")
        )
        assert status is None


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


# ── T03: multi-floor EUI regression (bug-catch) ──────────────────────────────

class TestMultiFloorEuiRegression:
    """lighting_eui must be INDEPENDENT of num_floors; only total energy scales.

    This is the assertion that would have caught the single_zone multi-floor defect:
    a 1-floor and a 4-floor building with the same LPD and footprint must yield
    equal lighting_eui_kwh_m2 — if single_zone collapses all floors into one zone
    carrying only one floor of lighting load, the EUI comes out ÷4 for 4 floors.
    """

    def _make_df(self, num_floors: int, footprint_m2: float, lpd_w_m2: float) -> pd.DataFrame:
        """Synthetic hourly DataFrame mimicking one-zone-per-floor output.

        Each floor zone contributes lighting kWh proportional to its floor area
        (footprint × 1 floor × lpd × 8760 h). The parser sums all zones.
        """
        from openubem.results.parser import J_TO_KWH

        # lighting kWh per floor-zone per year: area × W/m² × 8760 h / 1000
        kwh_per_floor = footprint_m2 * lpd_w_m2 * 8760 / 1000.0
        # equipment: half of lighting for simplicity
        equip_per_floor = kwh_per_floor * 0.5
        # heating/cooling: same per floor
        heat_per_floor = kwh_per_floor * 0.3
        cool_per_floor = kwh_per_floor * 0.2

        rows = []
        for f in range(num_floors):
            zone = f"way/TEST_F{f}_WHOLE"
            for var, kwh in [
                ("Zone Lights Electricity Energy", kwh_per_floor),
                ("Zone Electric Equipment Electricity Energy", equip_per_floor),
                ("Zone Ideal Loads Zone Total Heating Energy", heat_per_floor),
                ("Zone Ideal Loads Zone Total Cooling Energy", cool_per_floor),
            ]:
                rows.append({
                    "key_value": zone,
                    "variable_name": var,
                    "units": "kWh",
                    "Month": 1, "Day": 1, "Hour": 1,
                    "value": kwh,
                })
        return pd.DataFrame(rows)

    def _run_compute_eui(self, num_floors: int, footprint_m2: float, lpd_w_m2: float) -> dict:
        from openubem.results.parser import _compute_eui
        df = self._make_df(num_floors, footprint_m2, lpd_w_m2)
        row = _manifest_row("way/TEST", footprint_m2, num_floors, num_floors)
        eui, _, missing = _compute_eui(df, row, "")
        assert missing is None, f"Missing variable: {missing}"
        return eui

    def test_lighting_eui_independent_of_num_floors(self):
        """1-floor and 4-floor same-LPD buildings must yield equal lighting_eui_kwh_m2."""
        eui_1 = self._run_compute_eui(num_floors=1, footprint_m2=200.0, lpd_w_m2=10.0)
        eui_4 = self._run_compute_eui(num_floors=4, footprint_m2=200.0, lpd_w_m2=10.0)
        assert math.isclose(eui_1["lighting_eui_kwh_m2"], eui_4["lighting_eui_kwh_m2"], rel_tol=1e-9), (
            f"lighting_eui depends on num_floors: 1-floor={eui_1['lighting_eui_kwh_m2']:.4f}, "
            f"4-floor={eui_4['lighting_eui_kwh_m2']:.4f} — defect still present?"
        )

    def test_total_energy_scales_with_floors(self):
        """Total energy (kWh) must scale linearly with num_floors; EUI must not."""
        footprint = 200.0
        lpd = 10.0
        eui_1 = self._run_compute_eui(num_floors=1, footprint_m2=footprint, lpd_w_m2=lpd)
        eui_4 = self._run_compute_eui(num_floors=4, footprint_m2=footprint, lpd_w_m2=lpd)

        # EUI must be equal (invariant to floor count)
        assert math.isclose(eui_1["total_eui_kwh_m2"], eui_4["total_eui_kwh_m2"], rel_tol=1e-9), (
            f"total_eui differs: 1-floor={eui_1['total_eui_kwh_m2']:.4f}, "
            f"4-floor={eui_4['total_eui_kwh_m2']:.4f}"
        )

        # Total energy = EUI × floor_area; 4-floor has 4× the floor area → 4× total energy
        total_kwh_1 = eui_1["total_eui_kwh_m2"] * footprint * 1
        total_kwh_4 = eui_4["total_eui_kwh_m2"] * footprint * 4
        assert math.isclose(total_kwh_4, 4.0 * total_kwh_1, rel_tol=1e-9), (
            f"4-floor total energy should be 4× 1-floor: got {total_kwh_4:.1f} vs {4*total_kwh_1:.1f}"
        )

    def test_lighting_eui_value_matches_lpd(self):
        """Spot-check: lighting_eui = lpd_w_m2 × 8760 h / 1000."""
        lpd = 10.0
        expected_eui = lpd * 8760 / 1000.0  # kWh/m²
        for n in [1, 2, 4]:
            eui = self._run_compute_eui(num_floors=n, footprint_m2=200.0, lpd_w_m2=lpd)
            assert math.isclose(eui["lighting_eui_kwh_m2"], expected_eui, rel_tol=1e-9), (
                f"num_floors={n}: lighting_eui={eui['lighting_eui_kwh_m2']:.4f}, expected={expected_eui:.4f}"
            )


# ── T13 (Phase-E): new EUI columns + D9 total ────────────────────────────────

class TestPhaseEEuiColumns:
    """Verify _compute_eui returns pumps/dhw/cooking/refrigeration EUIs and D9 total."""

    def _make_df(self, footprint_m2: float = 400.0, num_floors: int = 1) -> pd.DataFrame:
        """Minimal zone df with lighting + equipment only."""
        rows = []
        zone = f"way/PHSE_F0_WHOLE"
        kwh = 1000.0  # arbitrary
        for var in ["Zone Lights Electricity Energy",
                    "Zone Electric Equipment Electricity Energy"]:
            rows.append({
                "key_value": zone,
                "variable_name": var,
                "units": "kWh",
                "Month": 1, "Day": 1, "Hour": 1,
                "value": kwh,
            })
        return pd.DataFrame(rows)

    def _manifest(self, footprint: float = 400.0, floors: int = 1) -> pd.Series:
        return pd.Series({
            "osm_id": "way/PHSE",
            "footprint_area_m2": footprint,
            "levels": float(floors),
            "height_m": float("nan"),
            "num_zones": floors,
            "data_quality_flag": "",
        })

    def test_new_columns_present(self):
        from openubem.results.parser import _compute_eui
        df = self._make_df()
        row = self._manifest()
        meters = {  # values in kWh (already converted — _parse_meters_sql does J→kWh)
            "Pumps:Electricity": 1.0,
            "WaterSystems:NaturalGas": 2.0,
            "WaterSystems:Electricity": 1.0,
            "InteriorEquipment:NaturalGas": 1.0,
            "Refrigeration:Electricity": 1.0,
        }
        eui, _, missing = _compute_eui(df, row, "", meters)
        assert missing is None
        for col in ["pumps_eui_kwh_m2", "dhw_eui_kwh_m2",
                    "cooking_eui_kwh_m2", "refrigeration_eui_kwh_m2"]:
            assert col in eui, f"Missing column: {col}"

    def test_pumps_eui_correct(self):
        from openubem.results.parser import _compute_eui
        df = self._make_df(footprint_m2=400.0)
        row = self._manifest(footprint=400.0, floors=1)
        meters = {"Pumps:Electricity": 400.0}  # kWh; EUI = 400/400 = 1.0 kWh/m²
        eui, _, _ = _compute_eui(df, row, "", meters)
        assert math.isclose(eui["pumps_eui_kwh_m2"], 1.0, rel_tol=1e-9)

    def test_dhw_eui_combines_gas_and_elec(self):
        from openubem.results.parser import _compute_eui
        df = self._make_df(footprint_m2=200.0)
        row = self._manifest(footprint=200.0, floors=1)
        meters = {
            "WaterSystems:NaturalGas": 100.0,   # kWh gas
            "WaterSystems:Electricity": 50.0,   # kWh elec
        }
        eui, _, _ = _compute_eui(df, row, "", meters)
        assert math.isclose(eui["dhw_eui_kwh_m2"], 150.0 / 200.0, rel_tol=1e-9)

    def test_cooking_eui_is_gas_only(self):
        from openubem.results.parser import _compute_eui
        df = self._make_df(footprint_m2=200.0)
        row = self._manifest(footprint=200.0, floors=1)
        meters = {"InteriorEquipment:NaturalGas": 80.0}  # kWh gas cooking
        eui, _, _ = _compute_eui(df, row, "", meters)
        assert math.isclose(eui["cooking_eui_kwh_m2"], 80.0 / 200.0, rel_tol=1e-9)

    def test_refrigeration_eui_from_compressor_rack(self):
        from openubem.results.parser import _compute_eui
        df = self._make_df(footprint_m2=4000.0)
        row = self._manifest(footprint=4000.0, floors=1)
        meters = {"Refrigeration:Electricity": 500_000.0}  # kWh compressor rack
        eui, _, _ = _compute_eui(df, row, "", meters)
        assert math.isclose(eui["refrigeration_eui_kwh_m2"], 500_000.0 / 4000.0, rel_tol=1e-9)

    def test_d9_total_equals_sum_of_all_nine(self):
        """D9: total_eui = sum of all 9 end-use EUIs."""
        from openubem.results.parser import _compute_eui
        df = self._make_df(footprint_m2=400.0, num_floors=2)
        row = self._manifest(footprint=400.0, floors=2)
        meters = {  # all in kWh
            "Cooling:Electricity":          200.0,
            "Heating:Electricity":           50.0,
            "Heating:NaturalGas":           100.0,
            "Fans:Electricity":              80.0,
            "Pumps:Electricity":             40.0,
            "WaterSystems:NaturalGas":       30.0,
            "WaterSystems:Electricity":      10.0,
            "InteriorEquipment:NaturalGas":  60.0,
            "Refrigeration:Electricity":     20.0,
        }
        eui, _, _ = _compute_eui(df, row, "", meters)
        floor_area = 400.0 * 2
        # lighting=1kWh/400m²  equipment=1kWh/400m² (from df), plus meters above
        expected_total = (
            eui["cooling_eui_kwh_m2"]
            + eui["heating_eui_kwh_m2"]
            + eui["lighting_eui_kwh_m2"]
            + eui["equipment_eui_kwh_m2"]
            + eui["fans_eui_kwh_m2"]
            + eui["pumps_eui_kwh_m2"]
            + eui["dhw_eui_kwh_m2"]
            + eui["cooking_eui_kwh_m2"]
            + eui["refrigeration_eui_kwh_m2"]
        )
        assert math.isclose(eui["total_eui_kwh_m2"], expected_total, rel_tol=1e-12)

    def test_missing_meters_default_to_zero(self):
        """Phase-E meters absent from SQL return 0.0, not NaN (not failed_parse)."""
        from openubem.results.parser import _compute_eui
        df = self._make_df()
        row = self._manifest()
        eui, _, missing = _compute_eui(df, row, "", meters={})
        assert missing is None
        for col in ["pumps_eui_kwh_m2", "dhw_eui_kwh_m2",
                    "cooking_eui_kwh_m2", "refrigeration_eui_kwh_m2"]:
            assert eui[col] == 0.0, f"{col} should be 0.0 when meter absent"

    def test_meter_query_includes_new_meters(self):
        """METER_QUERY must include all 9 Phase-E meter names."""
        from openubem.results.parser import METER_QUERY
        for name in ["Pumps:Electricity", "WaterSystems:NaturalGas",
                     "WaterSystems:Electricity", "InteriorEquipment:NaturalGas",
                     "Refrigeration:Electricity"]:
            assert name in METER_QUERY, f"Missing from METER_QUERY: {name}"
