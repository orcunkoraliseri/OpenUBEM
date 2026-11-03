"""Unit tests for openubem.results.carbon (T08)."""
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


# ── eGRID loader ──────────────────────────────────────────────────────────────

class TestEgridLoader:
    def test_load_returns_dict(self):
        from openubem.results.carbon import load_egrid
        data = load_egrid()
        assert isinstance(data, dict)

    def test_51_entries(self):
        """50 states + DC = 51 entries (PLAN P2 validation)."""
        from openubem.results.carbon import load_egrid
        data = load_egrid()
        assert len(data) == 51, f"Expected 51 states+DC, got {len(data)}"

    def test_ma_factor(self):
        """MA factor per PROVENANCE.md."""
        from openubem.results.carbon import get_elec_factor, load_egrid
        factor = get_elec_factor("MA")
        exp = 0.389735
        assert math.isclose(factor, exp, rel_tol=1e-4), f"MA factor: got {factor}, expected {exp}"

    def test_all_factors_in_bounds(self):
        """All factors must be in [0.01, 1.2] kg CO₂e/kWh (PLAN P2 validation)."""
        from openubem.results.carbon import load_egrid
        data = load_egrid()
        for state, entry in data.items():
            f = float(entry["factor_kgco2_kwh"])
            assert 0.01 <= f <= 1.2, f"State {state} factor {f} out of bounds [0.01, 1.2]"

    def test_no_territories(self):
        """PR/VI/AS/GU/MP must be excluded (PLAN P2)."""
        from openubem.results.carbon import load_egrid
        data = load_egrid()
        territories = {"PR", "VI", "AS", "GU", "MP"}
        for t in territories:
            assert t not in data, f"Territory {t!r} present in egrid_2022.json"

    def test_unknown_state_raises(self):
        from openubem.results.carbon import get_elec_factor
        with pytest.raises(KeyError):
            get_elec_factor("XX")


# ── GWP computation ───────────────────────────────────────────────────────────

class TestGwpComputation:
    def _make_eui_row(self, heating=10.0, cooling=20.0, lighting=5.0, equipment=3.0):
        return {
            "heating_eui_kwh_m2": heating,
            "cooling_eui_kwh_m2": cooling,
            "lighting_eui_kwh_m2": lighting,
            "equipment_eui_kwh_m2": equipment,
        }

    def test_heating_uses_gas_factor(self):
        """Heating GWP = heating_eui × 0.181 (DESIGN §3E, load_referenced_v1)."""
        from openubem.results.carbon import compute_gwp
        row = self._make_eui_row(heating=10.0, cooling=0.0, lighting=0.0, equipment=0.0)
        result = compute_gwp(row, "MA")
        assert math.isclose(result["gwp_heating_kgco2_m2"], 10.0 * 0.181, rel_tol=1e-9)

    def test_cooling_uses_elec_factor(self):
        """Cooling GWP = cooling_eui × eGRID[MA] (no η/COP — load_referenced_v1)."""
        from openubem.results.carbon import compute_gwp, get_elec_factor
        f_elec = get_elec_factor("MA")
        row = self._make_eui_row(heating=0.0, cooling=20.0, lighting=0.0, equipment=0.0)
        result = compute_gwp(row, "MA")
        assert math.isclose(result["gwp_cooling_kgco2_m2"], 20.0 * f_elec, rel_tol=1e-9)

    def test_total_gwp_is_sum(self):
        from openubem.results.carbon import compute_gwp
        row = self._make_eui_row(10.0, 20.0, 5.0, 3.0)
        result = compute_gwp(row, "MA")
        expected_total = (
            result["gwp_heating_kgco2_m2"]
            + result["gwp_cooling_kgco2_m2"]
            + result["gwp_lighting_kgco2_m2"]
            + result["gwp_equipment_kgco2_m2"]
        )
        assert math.isclose(result["gwp_total_kgco2_m2"], expected_total, rel_tol=1e-12)

    def test_nan_eui_propagates_nan_gwp(self):
        """Failed buildings (NaN EUI) → NaN GWP (flag-don't-drop)."""
        from openubem.results.carbon import compute_gwp
        row = {
            "heating_eui_kwh_m2": float("nan"),
            "cooling_eui_kwh_m2": 0.0,
            "lighting_eui_kwh_m2": 0.0,
            "equipment_eui_kwh_m2": 0.0,
        }
        result = compute_gwp(row, "MA")
        assert math.isnan(result["gwp_total_kgco2_m2"])

    def test_different_states(self):
        """VT has much lower eGRID factor than MA (nearly all hydro/nuclear)."""
        from openubem.results.carbon import compute_gwp, get_elec_factor
        f_ma = get_elec_factor("MA")
        f_vt = get_elec_factor("VT")
        assert f_vt < f_ma * 0.2, f"VT={f_vt:.4f} expected to be <20% of MA={f_ma:.4f}"
        row = {"heating_eui_kwh_m2": 0.0, "cooling_eui_kwh_m2": 100.0,
               "lighting_eui_kwh_m2": 0.0, "equipment_eui_kwh_m2": 0.0}
        result_ma = compute_gwp(row, "MA")
        result_vt = compute_gwp(row, "VT")
        assert result_vt["gwp_cooling_kgco2_m2"] < result_ma["gwp_cooling_kgco2_m2"]


# ── GWP golden values (integration with parser) ───────────────────────────────

class TestGwpGolden:
    _REL_TOL = 1e-6

    def _run_and_attach(self, key, fixture_name, footprint, floors, n_zones):
        from openubem.results.parser import parse_building
        from openubem.results.carbon import attach_gwp
        row = pd.Series({
            "osm_id": f"way/{key}",
            "footprint_area_m2": footprint,
            "levels": float(floors),
            "height_m": float("nan"),
            "num_zones": n_zones,
            "data_quality_flag": "",
        })
        sql = GOLDEN_DIR / fixture_name
        parsed = parse_building(sql, None, row)
        return attach_gwp(parsed, "MA")

    def test_r1_gwp_heating(self, expected):
        result = self._run_and_attach("R1", "r1_single_zone.sql", 196.0, 2, 1)
        exp = expected["R1"]["gwp"]["gwp_heating_kgco2_m2"]
        assert math.isclose(result["gwp_heating_kgco2_m2"], exp, rel_tol=self._REL_TOL)

    def test_r1_gwp_cooling(self, expected):
        result = self._run_and_attach("R1", "r1_single_zone.sql", 196.0, 2, 1)
        exp = expected["R1"]["gwp"]["gwp_cooling_kgco2_m2"]
        assert math.isclose(result["gwp_cooling_kgco2_m2"], exp, rel_tol=self._REL_TOL)

    def test_r1_gwp_total(self, expected):
        result = self._run_and_attach("R1", "r1_single_zone.sql", 196.0, 2, 1)
        exp = expected["R1"]["gwp"]["gwp_total_kgco2_m2"]
        assert math.isclose(result["gwp_total_kgco2_m2"], exp, rel_tol=self._REL_TOL)

    def test_r2_gwp_total(self, expected):
        result = self._run_and_attach("R2", "r2_one_zone_per_floor.sql", 625.0, 4, 4)
        exp = expected["R2"]["gwp"]["gwp_total_kgco2_m2"]
        assert math.isclose(result["gwp_total_kgco2_m2"], exp, rel_tol=self._REL_TOL)

    def test_r6_gwp_total(self, expected):
        result = self._run_and_attach("R6", "r6_perimeter_core.sql", 1500.0, 3, 15)
        exp = expected["R6"]["gwp"]["gwp_total_kgco2_m2"]
        assert math.isclose(result["gwp_total_kgco2_m2"], exp, rel_tol=self._REL_TOL)


# ── Phase-E GWP columns (T14, D10) ───────────────────────────────────────────

class TestPhaseEGwpColumns:
    """D10: gas end-uses × 0.181; electric end-uses × eGRID factor."""

    _GAS_FACTOR = 0.181

    def _row(self, **kwargs):
        base = {
            "heating_eui_kwh_m2": 0.0,
            "cooling_eui_kwh_m2": 0.0,
            "lighting_eui_kwh_m2": 0.0,
            "equipment_eui_kwh_m2": 0.0,
        }
        base.update(kwargs)
        return base

    def test_all_nine_gwp_columns_present(self):
        """compute_gwp returns all 9 GWP columns."""
        from openubem.results.carbon import compute_gwp
        result = compute_gwp(self._row(), "MA")
        for col in ("gwp_heating_kgco2_m2", "gwp_cooling_kgco2_m2",
                    "gwp_lighting_kgco2_m2", "gwp_equipment_kgco2_m2",
                    "gwp_fans_kgco2_m2", "gwp_pumps_kgco2_m2",
                    "gwp_dhw_kgco2_m2", "gwp_cooking_kgco2_m2",
                    "gwp_refrigeration_kgco2_m2", "gwp_total_kgco2_m2"):
            assert col in result, f"Missing column: {col}"

    def test_fans_uses_elec_factor(self):
        """Fans GWP = fans_eui × eGRID[MA] (electric end-use)."""
        from openubem.results.carbon import compute_gwp, get_elec_factor
        f_elec = get_elec_factor("MA")
        result = compute_gwp(self._row(fans_eui_kwh_m2=10.0), "MA")
        assert math.isclose(result["gwp_fans_kgco2_m2"], 10.0 * f_elec, rel_tol=1e-9)

    def test_pumps_uses_elec_factor(self):
        """Pumps GWP = pumps_eui × eGRID[MA] (electric end-use)."""
        from openubem.results.carbon import compute_gwp, get_elec_factor
        f_elec = get_elec_factor("MA")
        result = compute_gwp(self._row(pumps_eui_kwh_m2=5.0), "MA")
        assert math.isclose(result["gwp_pumps_kgco2_m2"], 5.0 * f_elec, rel_tol=1e-9)

    def test_dhw_gas_uses_gas_factor(self):
        """DHW gas portion GWP = dhw_gas_eui × 0.181."""
        from openubem.results.carbon import compute_gwp
        result = compute_gwp(self._row(dhw_gas_eui_kwh_m2=20.0, dhw_elec_eui_kwh_m2=0.0), "MA")
        assert math.isclose(result["gwp_dhw_kgco2_m2"], 20.0 * self._GAS_FACTOR, rel_tol=1e-9)

    def test_dhw_elec_uses_elec_factor(self):
        """DHW electric portion GWP = dhw_elec_eui × eGRID[MA]."""
        from openubem.results.carbon import compute_gwp, get_elec_factor
        f_elec = get_elec_factor("MA")
        result = compute_gwp(self._row(dhw_gas_eui_kwh_m2=0.0, dhw_elec_eui_kwh_m2=8.0), "MA")
        assert math.isclose(result["gwp_dhw_kgco2_m2"], 8.0 * f_elec, rel_tol=1e-9)

    def test_dhw_combined_splits_by_fuel(self):
        """gwp_dhw = gas_part × f_gas + elec_part × f_elec (D10 split)."""
        from openubem.results.carbon import compute_gwp, get_elec_factor
        f_elec = get_elec_factor("MA")
        result = compute_gwp(self._row(dhw_gas_eui_kwh_m2=15.0, dhw_elec_eui_kwh_m2=5.0), "MA")
        expected = 15.0 * self._GAS_FACTOR + 5.0 * f_elec
        assert math.isclose(result["gwp_dhw_kgco2_m2"], expected, rel_tol=1e-9)

    def test_cooking_uses_gas_factor(self):
        """Cooking GWP = cooking_eui × 0.181 (gas cooking, D10)."""
        from openubem.results.carbon import compute_gwp
        result = compute_gwp(self._row(cooking_eui_kwh_m2=30.0), "MA")
        assert math.isclose(result["gwp_cooking_kgco2_m2"], 30.0 * self._GAS_FACTOR, rel_tol=1e-9)

    def test_refrigeration_uses_elec_factor(self):
        """Refrigeration GWP = refrigeration_eui × eGRID[MA] (electric compressor rack)."""
        from openubem.results.carbon import compute_gwp, get_elec_factor
        f_elec = get_elec_factor("MA")
        result = compute_gwp(self._row(refrigeration_eui_kwh_m2=50.0), "MA")
        assert math.isclose(result["gwp_refrigeration_kgco2_m2"], 50.0 * f_elec, rel_tol=1e-9)

    def test_total_includes_all_nine_enduses(self):
        """gwp_total = sum of all 9 component GWP values."""
        from openubem.results.carbon import compute_gwp
        result = compute_gwp(self._row(
            heating_eui_kwh_m2=10.0, cooling_eui_kwh_m2=20.0,
            lighting_eui_kwh_m2=5.0, equipment_eui_kwh_m2=3.0,
            fans_eui_kwh_m2=4.0, pumps_eui_kwh_m2=2.0,
            dhw_gas_eui_kwh_m2=8.0, dhw_elec_eui_kwh_m2=2.0,
            cooking_eui_kwh_m2=6.0, refrigeration_eui_kwh_m2=12.0,
        ), "MA")
        expected = sum(result[k] for k in (
            "gwp_heating_kgco2_m2", "gwp_cooling_kgco2_m2",
            "gwp_lighting_kgco2_m2", "gwp_equipment_kgco2_m2",
            "gwp_fans_kgco2_m2", "gwp_pumps_kgco2_m2",
            "gwp_dhw_kgco2_m2", "gwp_cooking_kgco2_m2",
            "gwp_refrigeration_kgco2_m2",
        ))
        assert math.isclose(result["gwp_total_kgco2_m2"], expected, rel_tol=1e-12)

    def test_pre_phasee_row_defaults_to_zero(self):
        """Pre-Phase-E row (missing Phase-E cols) → 0.0 for all new GWP columns."""
        from openubem.results.carbon import compute_gwp
        row = {
            "heating_eui_kwh_m2": 10.0,
            "cooling_eui_kwh_m2": 5.0,
            "lighting_eui_kwh_m2": 3.0,
            "equipment_eui_kwh_m2": 2.0,
        }
        result = compute_gwp(row, "MA")
        for col in ("gwp_fans_kgco2_m2", "gwp_pumps_kgco2_m2",
                    "gwp_dhw_kgco2_m2", "gwp_cooking_kgco2_m2",
                    "gwp_refrigeration_kgco2_m2"):
            assert result[col] == 0.0, f"{col} should be 0.0 for pre-Phase-E row"

    def test_nan_propagates_to_all_phasee_columns(self):
        """NaN in core EUI → NaN in all 9 GWP columns (flag-don't-drop)."""
        from openubem.results.carbon import compute_gwp
        row = {
            "heating_eui_kwh_m2": float("nan"),
            "cooling_eui_kwh_m2": 0.0,
            "lighting_eui_kwh_m2": 0.0,
            "equipment_eui_kwh_m2": 0.0,
            "fans_eui_kwh_m2": 5.0,
            "pumps_eui_kwh_m2": 2.0,
        }
        result = compute_gwp(row, "MA")
        for col in ("gwp_fans_kgco2_m2", "gwp_pumps_kgco2_m2",
                    "gwp_dhw_kgco2_m2", "gwp_cooking_kgco2_m2",
                    "gwp_refrigeration_kgco2_m2", "gwp_total_kgco2_m2"):
            assert math.isnan(result[col]), f"{col} should be NaN when core EUI is NaN"
