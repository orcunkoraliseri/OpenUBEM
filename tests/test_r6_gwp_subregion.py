"""Tests for T07b: eGRID subregion GWP recompute (R6-2 / B2).

DEVIATION FLAG: The plan (T07b) asserts "NYC cell total GWP strictly DECREASES
because NYCW<NY". The actual eGRID 2022 data shows NYCW=0.402146 kg/kWh vs
NY state=0.222872 kg/kWh (ratio=1.806), so NYCW > NY and NYC GWP INCREASES.
The test below asserts the factually correct direction (increase). Manager must
resolve whether the plan's narrative was based on incorrect prior data or
whether a different metric/column was intended.

All other assertions from the plan are implemented as specified.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

from scripts.validation.r6_rescore_cells import (
    CITY_STATE,
    CITY_SUBREGION,
    EGRID_STATE_PATH,
    EGRID_SUBREGION_PATH,
    compute_gwp_subregion,
    _load_egrid_factors,
    _cell_city,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_df(
    footprint: float,
    levels: float | None,
    height_m: float | None,
    gwp_heating: float,
    gwp_cooling: float,
    gwp_lighting: float,
    gwp_equipment: float,
) -> pd.DataFrame:
    """One-building synthetic DataFrame matching 05_results.csv schema (minimal)."""
    gwp_total = gwp_heating + gwp_cooling + gwp_lighting + gwp_equipment
    return pd.DataFrame([{
        "footprint_area_m2": footprint,
        "levels": levels,
        "height_m": height_m,
        "gwp_heating_kgco2_m2": gwp_heating,
        "gwp_cooling_kgco2_m2": gwp_cooling,
        "gwp_lighting_kgco2_m2": gwp_lighting,
        "gwp_equipment_kgco2_m2": gwp_equipment,
        "gwp_total_kgco2_m2": gwp_total,
    }])


# ── T07b assertion 1: ratio applied only to electricity components ──────────

class TestRatioAppliedOnlyToElectricity:
    def test_electricity_components_rescaled_heating_unchanged(self):
        """Heating GWP must remain byte-identical; elec GWP scales by ratio."""
        f_state = 0.222872      # NY
        f_subregion = 0.402146  # NYCW
        ratio = f_subregion / f_state

        df = _make_df(100.0, 5, None, gwp_heating=10.0, gwp_cooling=5.0,
                      gwp_lighting=3.0, gwp_equipment=2.0)
        floor_area = 100.0 * 5

        # Expected: heating unchanged, electricity scaled
        gwp_elec_old = 5.0 + 3.0 + 2.0  # = 10.0
        expected_total_new = (10.0 + gwp_elec_old * ratio) * floor_area

        gwp_r5, gwp_r6, delta_pct = compute_gwp_subregion(df, f_state, f_subregion)

        expected_r5 = (10.0 + 10.0) * floor_area  # gwp_total_kgco2_m2 = 20.0
        assert abs(gwp_r5 - expected_r5) < 1e-6, f"R5: {gwp_r5} != {expected_r5}"
        assert abs(gwp_r6 - expected_total_new) < 1e-6, f"R6: {gwp_r6} != {expected_total_new}"


# ── T07b assertion 2: heating GWP byte-identical pre/post ──────────────────

class TestHeatingGWPUnchanged:
    def test_heating_component_invariant_across_ratio(self):
        """heating GWP contribution must equal pre-recompute value regardless of ratio."""
        f_state = 0.372828
        f_subregion = 0.351215  # ERCT < ERCT (Austin decreases)
        ratio = f_subregion / f_state

        gwp_heating = 8.0
        df = _make_df(200.0, 3, None, gwp_heating=gwp_heating,
                      gwp_cooling=4.0, gwp_lighting=2.0, gwp_equipment=1.0)
        floor_area = 200.0 * 3

        gwp_r5, gwp_r6, _ = compute_gwp_subregion(df, f_state, f_subregion)

        # heating contribution is gwp_heating * floor_area in both R5 and R6
        heating_contribution_r5 = gwp_heating * floor_area
        heating_contribution_r6 = gwp_heating * floor_area

        # gwp_elec in R5 = (4+2+1) * floor = 7 * floor
        # gwp_elec in R6 = 7 * ratio * floor
        gwp_elec_r5 = 7.0 * floor_area
        gwp_elec_r6 = 7.0 * ratio * floor_area

        assert abs(gwp_r5 - (heating_contribution_r5 + gwp_elec_r5)) < 1e-6
        assert abs(gwp_r6 - (heating_contribution_r6 + gwp_elec_r6)) < 1e-6


# ── T07b assertion 3: zero-electricity building unchanged ──────────────────

class TestZeroElectricityGWPUnchanged:
    def test_zero_elec_gwp_building_unchanged(self):
        """A building with all-zero cooling/lighting/equipment GWP is unchanged."""
        f_state = 0.222872
        f_subregion = 0.402146  # NYCW > NY — would normally increase
        ratio = f_subregion / f_state
        assert ratio > 1.0  # confirm the ratio would increase elec GWP

        gwp_heating = 15.0
        df = _make_df(100.0, 2, None, gwp_heating=gwp_heating,
                      gwp_cooling=0.0, gwp_lighting=0.0, gwp_equipment=0.0)
        floor_area = 100.0 * 2

        gwp_r5, gwp_r6, delta_pct = compute_gwp_subregion(df, f_state, f_subregion)

        expected = gwp_heating * floor_area
        assert abs(gwp_r5 - expected) < 1e-6
        assert abs(gwp_r6 - expected) < 1e-6, (
            f"Zero-electricity building should be unchanged: r5={gwp_r5:.2f} r6={gwp_r6:.2f}"
        )
        assert abs(delta_pct) < 1e-9, f"delta_pct should be 0 for zero-elec building: {delta_pct}"


# ── T07b assertion 4 (DEVIATION): NYC cell GWP direction ───────────────────

class TestNYCCellGWPDirection:
    """Plan says NYC strictly DECREASES because NYCW<NY — FACTUALLY WRONG.

    eGRID 2022 data: NYCW=0.402146 > NY=0.222872 (ratio=1.806).
    NYC GWP INCREASES. This test asserts the correct, data-driven direction.
    Manager must review this deviation and decide whether B2 intent was to use
    a different eGRID metric, or to accept the factual correction.
    """
    def test_nycw_factor_greater_than_ny_state(self):
        """NYCW > NY state factor in eGRID 2022 total-output rate."""
        with open(EGRID_STATE_PATH, encoding="utf-8") as fh:
            state_data = json.load(fh)
        with open(EGRID_SUBREGION_PATH, encoding="utf-8") as fh:
            sr_data = json.load(fh)

        f_ny = state_data["NY"]["factor_kgco2_kwh"]
        f_nycw = sr_data["NYCW"]["factor_kgco2_kwh"]
        assert f_nycw > f_ny, (
            f"NYCW ({f_nycw}) should be > NY ({f_ny}) per eGRID 2022 SRC2ERTA "
            f"(NOTE: plan expected NYCW < NY — this is the data-driven correction)"
        )

    def test_nyc_cells_gwp_increases_in_r6(self):
        """All 4 NYC cells must show INCREASED GWP with NYCW subregion factor.

        DEVIATION from plan: plan says 'strictly DECREASES because NYCW<NY'.
        Actual eGRID 2022 data shows ratio=1.806 (NYCW/NY), so GWP increases.
        """
        summary = pd.read_csv(
            REPO / "docs" / "validations" / "overAll" / "results" / "r6_rescore_summary.csv"
        )
        nyc_cells = summary[summary["cell"].str.startswith("nyc")]
        assert len(nyc_cells) == 4, f"Expected 4 NYC cells, got {len(nyc_cells)}"
        for _, row in nyc_cells.iterrows():
            assert row["gwp_delta_pct"] > 0, (
                f"{row['cell']}: expected GWP increase with NYCW>NY, "
                f"got delta={row['gwp_delta_pct']:.2f}%"
            )


# ── T07b assertion 5: 05_results.csv not mutated ───────────────────────────

class TestNoMutationOf05ResultsCSV:
    def test_05_results_csv_not_modified(self, tmp_path):
        """compute_gwp_subregion must not write to or modify 05_results.csv."""
        cases_dir = REPO / "docs" / "validations" / "overAll" / "results" / "cases"
        cell = "nyc_centre"
        csv_path = cases_dir / cell / "05_results.csv"

        stat_before = csv_path.stat()
        mtime_before = stat_before.st_mtime

        f_state = 0.222872
        f_subregion = 0.402146
        df = pd.read_csv(csv_path)
        from scripts.validation.r6_rescore_cells import SUCCESS_STATUSES
        df_success = df[df["simulation_status"].isin(SUCCESS_STATUSES)].copy()
        compute_gwp_subregion(df_success, f_state, f_subregion)

        stat_after = csv_path.stat()
        assert stat_after.st_mtime == mtime_before, (
            f"05_results.csv mtime changed: recompute must be in-memory only"
        )


# ── T07b assertion 6: R5 GWP shipped artifacts not overwritten ─────────────

class TestR5ShippedGWPNotOverwritten:
    def test_neighbourhood_summary_gwp_unchanged(self):
        """neighbourhood_gwp_total_kgco2 in 05_neighbourhood_summary.json must equal V13 values."""
        v13_totals = {
            "nyc_centre": 332809487,
            "nyc_urban": 40317055,
            "nyc_suburban": 8464410,
            "nyc_rural": 2567219,
            "la_centre": 119015264,
            "la_urban": 101280696,
            "la_suburban": 14052830,
            "la_rural": 4488260,
            "austin_centre": 242610785,
            "austin_urban": 64368469,
            "austin_suburban": 17946122,
            "austin_rural": 10891760,
        }
        cases_dir = REPO / "docs" / "validations" / "overAll" / "results" / "cases"
        for cell, v13_gwp in v13_totals.items():
            summary_path = cases_dir / cell / "05_neighbourhood_summary.json"
            with open(summary_path, encoding="utf-8") as fh:
                summary = json.load(fh)
            actual = summary["neighbourhood_gwp_total_kgco2"]
            assert abs(actual - v13_gwp) < 1, (
                f"{cell}: neighbourhood_summary GWP changed from V13! "
                f"Expected ~{v13_gwp:,}, got {actual:,.0f}"
            )

    def test_r5_gwp_in_summary_csv_column_matches_v13(self):
        """gwp_r5_state_kgco2e in r6_rescore_summary.csv must match V13 totals (within rounding)."""
        v13_totals = {
            "nyc_centre": 332809487,
            "nyc_urban": 40317055,
            "nyc_suburban": 8464410,
            "nyc_rural": 2567219,
            "la_centre": 119015264,
            "la_urban": 101280696,
            "la_suburban": 14052830,
            "la_rural": 4488260,
            "austin_centre": 242610785,
            "austin_urban": 64368469,
            "austin_suburban": 17946122,
            "austin_rural": 10891760,
        }
        summary = pd.read_csv(
            REPO / "docs" / "validations" / "overAll" / "results" / "r6_rescore_summary.csv"
        )
        assert "gwp_r5_state_kgco2e" in summary.columns, "Missing gwp_r5_state_kgco2e column"
        assert "gwp_r6_subregion_kgco2e" in summary.columns, "Missing gwp_r6_subregion_kgco2e column"
        assert "gwp_delta_pct" in summary.columns, "Missing gwp_delta_pct column"

        for cell, v13 in v13_totals.items():
            row = summary[summary["cell"] == cell].iloc[0]
            r5_val = row["gwp_r5_state_kgco2e"]
            pct_diff = abs(r5_val - v13) / v13 * 100
            assert pct_diff < 0.01, (
                f"{cell}: R5 state GWP {r5_val:,.0f} differs from V13 {v13:,} by {pct_diff:.4f}%"
            )


# ── Subregion factor range validation ──────────────────────────────────────

class TestSubregionFactors:
    def test_three_factors_present_and_in_range(self):
        """NYCW, CAMX, ERCT must be present with factors in (0.01, 1.2)."""
        with open(EGRID_SUBREGION_PATH, encoding="utf-8") as fh:
            sr_data = json.load(fh)
        for acronym in ("NYCW", "CAMX", "ERCT"):
            assert acronym in sr_data, f"{acronym} missing from subregions JSON"
            f = sr_data[acronym]["factor_kgco2_kwh"]
            assert 0.01 < f < 1.2, f"{acronym}: {f} outside (0.01, 1.2)"

    def test_load_egrid_factors_returns_state_and_subregion(self):
        state_f, sr_f = _load_egrid_factors()
        assert "NY" in state_f
        assert "CA" in state_f
        assert "TX" in state_f
        assert "NYCW" in sr_f
        assert "CAMX" in sr_f
        assert "ERCT" in sr_f
        # Verify known values
        assert abs(state_f["NY"] - 0.222872) < 1e-5
        assert abs(state_f["CA"] - 0.207512) < 1e-5
        assert abs(state_f["TX"] - 0.372828) < 1e-5
        assert abs(sr_f["NYCW"] - 0.402146) < 1e-4
        assert abs(sr_f["CAMX"] - 0.226469) < 1e-4
        assert abs(sr_f["ERCT"] - 0.351215) < 1e-4

    def test_austin_gwp_decreases(self):
        """Austin cells should decrease: ERCT (0.351215) < TX (0.372828)."""
        with open(EGRID_STATE_PATH, encoding="utf-8") as fh:
            state_data = json.load(fh)
        with open(EGRID_SUBREGION_PATH, encoding="utf-8") as fh:
            sr_data = json.load(fh)
        f_tx = state_data["TX"]["factor_kgco2_kwh"]
        f_erct = sr_data["ERCT"]["factor_kgco2_kwh"]
        assert f_erct < f_tx, f"ERCT ({f_erct}) should be < TX ({f_tx})"

        summary = pd.read_csv(
            REPO / "docs" / "validations" / "overAll" / "results" / "r6_rescore_summary.csv"
        )
        austin_cells = summary[summary["cell"].str.startswith("austin")]
        assert len(austin_cells) == 4
        for _, row in austin_cells.iterrows():
            assert row["gwp_delta_pct"] < 0, (
                f"{row['cell']}: expected GWP decrease (ERCT<TX), got {row['gwp_delta_pct']:.2f}%"
            )
