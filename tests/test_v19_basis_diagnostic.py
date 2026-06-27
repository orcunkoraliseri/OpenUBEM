"""Identity-reproduces-V19 gate + transform unit tests (T01/T02/T03/T04/T05/T06).

Uses live 05_results.gpkg data; no synthetic fixtures needed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "validation"))

from scripts.v19_rescore import load_all_cells, build_city_table, CITY_ANCHORS
from openubem.results.service_loads import load_coefficients, reconstruct_frame
from scripts.validation.v19_basis_diagnostic import (
    apply_basis_to_frame,
    score_combo,
    run_grid,
    compute_coherence,
    write_findings,
    _identity_present,
    _DELTA_KEYS,
    _PARAM_KEYS,
    _OUT_DIR,
)

# ---------------------------------------------------------------------------
# Shared fixtures (loaded once per session)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def base_df():
    return load_all_cells()


@pytest.fixture(scope="session")
def coeffs():
    return load_coefficients()


@pytest.fixture(scope="session")
def identity_result(base_df, coeffs):
    params = {"cooling_cop": 1.0, "heating_factor": 1.0, "lighting_scale": 1.0, "equipment_scale": 1.0}
    reconstructed = reconstruct_frame(base_df.copy(), coeffs, force=True)
    city_tbl = build_city_table(reconstructed)
    success_n = reconstructed[
        reconstructed["simulation_status"].str.startswith("success", na=False)
    ].shape[0]
    return city_tbl, success_n


# ---------------------------------------------------------------------------
# T01 — Harness scaffold: identity reproduces V19 (CP-1 gate)
# ---------------------------------------------------------------------------

class TestIdentityReproducesV19:
    """score_combo(identity) must reproduce V19 published deltas (F6)."""

    def _get_delta(self, city_tbl: pd.DataFrame, city: str, seg_prefix: str) -> float:
        if seg_prefix == "Overall":
            mask = (city_tbl["city"] == city) & city_tbl["segment"].str.startswith("Overall")
        else:
            mask = (city_tbl["city"] == city) & city_tbl["segment"].str.startswith(seg_prefix)
        assert mask.any(), f"Segment {city}/{seg_prefix} not found in city table"
        return float(city_tbl.loc[mask, "delta_vs_measured_pct"].iloc[0])

    def test_la_overall_within_half_pp(self, identity_result):
        city_tbl, _ = identity_result
        delta = self._get_delta(city_tbl, "la", "Overall")
        # V19 published: +38.8% (F6); tolerance ±0.5 pp
        assert abs(delta - 38.8) <= 0.5, (
            f"LA Overall delta {delta:+.1f}% not within ±0.5 pp of +38.8%"
        )

    def test_nyc_office_present(self, identity_result):
        city_tbl, _ = identity_result
        delta = self._get_delta(city_tbl, "nyc", "Office")
        # NYC Office must be present and within plausible range (V19: near pass ~+10 to +30%)
        assert -50.0 < delta < 100.0, f"NYC Office delta {delta:+.1f}% out of plausible range"

    def test_nyc_overall_approx_ten_pct(self, identity_result):
        city_tbl, _ = identity_result
        delta = self._get_delta(city_tbl, "nyc", "Overall")
        # V19: NYC Overall ~+10% (F6); ±1 pp
        assert abs(delta - 10.0) <= 1.0, (
            f"NYC Overall delta {delta:+.1f}% not within ±1 pp of +10%"
        )

    def test_success_row_count(self, identity_result):
        _, success_n = identity_result
        assert abs(success_n - 8150) <= 50, (
            f"Success-row count {success_n} not within ±50 of 8150"
        )


# ---------------------------------------------------------------------------
# T02 — apply_basis_to_frame unit tests
# ---------------------------------------------------------------------------

class TestApplyBasisToFrame:
    """Exact column arithmetic; identity returns identical values."""

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "cooling_eui_kwh_m2":   [100.0, 200.0],
            "heating_eui_kwh_m2":   [ 50.0, 100.0],
            "lighting_eui_kwh_m2":  [ 30.0,  60.0],
            "equipment_eui_kwh_m2": [ 20.0,  40.0],
            "total_eui_kwh_m2":     [200.0, 400.0],
            "other_col":            [  1.0,   2.0],
        })

    def test_identity_columns_unchanged(self, sample_df):
        out = apply_basis_to_frame(sample_df, 1.0, 1.0, 1.0, 1.0)
        for col in ["cooling_eui_kwh_m2", "heating_eui_kwh_m2",
                    "lighting_eui_kwh_m2", "equipment_eui_kwh_m2"]:
            assert out[col].tolist() == pytest.approx(sample_df[col].tolist(), abs=1e-9), (
                f"{col} changed under identity transform"
            )

    def test_identity_total_unchanged(self, sample_df):
        out = apply_basis_to_frame(sample_df, 1.0, 1.0, 1.0, 1.0)
        assert out["total_eui_kwh_m2"].tolist() == pytest.approx(
            sample_df["total_eui_kwh_m2"].tolist(), abs=1e-9
        )

    def test_identity_does_not_mutate_input(self, sample_df):
        orig_cooling = sample_df["cooling_eui_kwh_m2"].tolist()
        apply_basis_to_frame(sample_df, 1.0, 1.0, 1.0, 1.0)
        assert sample_df["cooling_eui_kwh_m2"].tolist() == orig_cooling

    def test_other_columns_untouched(self, sample_df):
        out = apply_basis_to_frame(sample_df, 3.5, 1.19, 0.8, 0.7)
        assert out["other_col"].tolist() == pytest.approx([1.0, 2.0], abs=1e-9)

    def test_cooling_cop_3p5(self, sample_df):
        out = apply_basis_to_frame(sample_df, 3.5, 1.0, 1.0, 1.0)
        assert out["cooling_eui_kwh_m2"].tolist() == pytest.approx(
            [100.0 / 3.5, 200.0 / 3.5], abs=1e-9
        )

    def test_heating_factor(self, sample_df):
        out = apply_basis_to_frame(sample_df, 1.0, 1.19, 1.0, 1.0)
        assert out["heating_eui_kwh_m2"].tolist() == pytest.approx(
            [50.0 * 1.19, 100.0 * 1.19], abs=1e-9
        )

    def test_lighting_scale(self, sample_df):
        out = apply_basis_to_frame(sample_df, 1.0, 1.0, 0.5, 1.0)
        assert out["lighting_eui_kwh_m2"].tolist() == pytest.approx(
            [15.0, 30.0], abs=1e-9
        )

    def test_equipment_scale(self, sample_df):
        out = apply_basis_to_frame(sample_df, 1.0, 1.0, 1.0, 0.7)
        assert out["equipment_eui_kwh_m2"].tolist() == pytest.approx(
            [14.0, 28.0], abs=1e-9
        )

    def test_total_recomputed_as_sum_of_four(self, sample_df):
        cop, hf, ls, es = 3.5, 1.19, 0.8, 0.7
        out = apply_basis_to_frame(sample_df, cop, hf, ls, es)
        for i, row in out.iterrows():
            expected_total = (
                row["cooling_eui_kwh_m2"]
                + row["heating_eui_kwh_m2"]
                + row["lighting_eui_kwh_m2"]
                + row["equipment_eui_kwh_m2"]
            )
            assert row["total_eui_kwh_m2"] == pytest.approx(expected_total, abs=1e-9), (
                f"Row {i}: total_eui_kwh_m2 {row['total_eui_kwh_m2']:.6f} "
                f"!= sum of four {expected_total:.6f}"
            )


# ---------------------------------------------------------------------------
# T03 — score_combo: identity reproduces V19 deltas via score_combo path
# ---------------------------------------------------------------------------

class TestScoreCombo:
    """score_combo on identity must match V19 city table within tolerance."""

    @pytest.fixture(scope="class")
    def identity_score(self, base_df, coeffs):
        params = {"cooling_cop": 1.0, "heating_factor": 1.0, "lighting_scale": 1.0, "equipment_scale": 1.0}
        return score_combo(base_df, coeffs, params)

    def test_la_overall_within_half_pp(self, identity_score):
        delta = identity_score["la_overall_delta"]
        assert abs(delta - 38.8) <= 0.5, (
            f"score_combo LA Overall {delta:+.1f}% not within ±0.5 pp of +38.8%"
        )

    def test_nyc_overall_within_one_pp(self, identity_score):
        delta = identity_score["nyc_overall_delta"]
        assert abs(delta - 10.0) <= 1.0, (
            f"score_combo NYC Overall {delta:+.1f}% not within ±1 pp of +10%"
        )

    def test_nyc_office_present(self, identity_score):
        assert "nyc_office_delta" in identity_score
        assert identity_score["nyc_office_delta"] == identity_score["nyc_office_delta"]  # not NaN

    def test_la_office_present(self, identity_score):
        assert "la_office_delta" in identity_score
        assert identity_score["la_office_delta"] == identity_score["la_office_delta"]

    def test_result_contains_all_params(self, identity_score):
        for k in ("cooling_cop", "heating_factor", "lighting_scale", "equipment_scale"):
            assert k in identity_score

    def test_result_contains_summary_metrics(self, identity_score):
        for k in ("max_abs_delta", "sumsq_delta", "n_within_15", "n_within_20"):
            assert k in identity_score

    def test_max_abs_delta_consistent(self, identity_score):
        deltas = [
            abs(identity_score[k]) for k in (
                "nyc_office_delta", "nyc_overall_delta",
                "la_office_delta", "la_overall_delta",
                "austin_office_delta", "austin_overall_delta",
            )
            if identity_score[k] == identity_score[k]  # exclude NaN
        ]
        expected_max = round(max(deltas), 2)
        assert identity_score["max_abs_delta"] == pytest.approx(expected_max, abs=0.01)


# ---------------------------------------------------------------------------
# T04 — Grid: 120 rows, identity present, required columns
# ---------------------------------------------------------------------------

class TestRunGrid:
    """T04 assertions: grid size, identity presence, column completeness."""

    @pytest.fixture(scope="class")
    def grid_df(self, base_df, coeffs):
        return run_grid(base_df, coeffs)

    def test_grid_has_120_rows(self, grid_df):
        assert len(grid_df) == 120, f"Grid has {len(grid_df)} rows, expected 120"

    def test_identity_row_present(self, grid_df):
        assert _identity_present(grid_df), "Identity combo (1,1,1,1) not in grid"

    def test_grid_has_param_columns(self, grid_df):
        for col in _PARAM_KEYS:
            assert col in grid_df.columns, f"Missing param column: {col}"

    def test_grid_has_delta_columns(self, grid_df):
        for col in _DELTA_KEYS:
            assert col in grid_df.columns, f"Missing delta column: {col}"

    def test_grid_has_summary_columns(self, grid_df):
        for col in ("max_abs_delta", "sumsq_delta", "n_within_15", "n_within_20"):
            assert col in grid_df.columns, f"Missing summary column: {col}"

    def test_csv_written_and_has_120_rows(self):
        csv_path = _OUT_DIR / "basis_sweep_combos.csv"
        assert csv_path.exists(), f"CSV not found: {csv_path}"
        df = pd.read_csv(csv_path)
        assert len(df) == 120, f"CSV has {len(df)} rows, expected 120"

    def test_grid_sorted_ascending_by_max_abs_delta(self, grid_df):
        vals = grid_df["max_abs_delta"].tolist()
        assert vals == sorted(vals), "Grid is not sorted ascending by max_abs_delta"


# ---------------------------------------------------------------------------
# T05 — Coherence: best-global <= identity; per-city <= global
# ---------------------------------------------------------------------------

class TestCoherence:
    """T05 assertions: monotonicity of ceiling hierarchy and coherence metrics."""

    @pytest.fixture(scope="class")
    def grid_and_coherence(self, base_df, coeffs):
        grid_df = run_grid(base_df, coeffs)
        coh = compute_coherence(grid_df)
        return grid_df, coh

    def test_best_global_le_identity(self, grid_and_coherence):
        grid_df, coh = grid_and_coherence
        best_max = float(grid_df.iloc[0]["max_abs_delta"])
        assert best_max <= coh["identity_max_abs"], (
            f"best-global {best_max:.2f} > identity {coh['identity_max_abs']:.2f}"
        )

    def test_per_city_ceilings_le_global_best(self, grid_and_coherence):
        grid_df, coh = grid_and_coherence
        best_max = float(grid_df.iloc[0]["max_abs_delta"])
        for city, ceiling in coh["per_city_ceiling"].items():
            assert ceiling <= best_max + 1e-6, (
                f"Per-city ceiling {city}={ceiling:.2f} > global best {best_max:.2f}"
            )

    def test_n_within_15_present(self, grid_and_coherence):
        _, coh = grid_and_coherence
        assert "n_within_15" in coh
        assert 0 <= coh["n_within_15"] <= 6

    def test_n_within_20_present(self, grid_and_coherence):
        _, coh = grid_and_coherence
        assert "n_within_20" in coh
        assert 0 <= coh["n_within_20"] <= 6

    def test_nyc_la_opposite_sign_is_bool(self, grid_and_coherence):
        _, coh = grid_and_coherence
        assert isinstance(coh["nyc_la_opposite_sign"], bool)


# ---------------------------------------------------------------------------
# T06 — Findings file: exists and has non-empty tables
# ---------------------------------------------------------------------------

class TestFindingsFile:
    """T06 assertions: RESULT file exists and all sections non-empty."""

    @pytest.fixture(scope="class")
    def result_text(self, base_df, coeffs):
        grid_df = run_grid(base_df, coeffs)
        coh = compute_coherence(grid_df)
        out_path = write_findings(grid_df, coh)
        return out_path.read_text(encoding="utf-8")

    def test_file_exists(self):
        out_path = _OUT_DIR / "RESULT_basis_diagnostic.md"
        assert out_path.exists(), f"RESULT_basis_diagnostic.md not found at {out_path}"

    def test_grid_spec_section_present(self, result_text):
        assert "## Grid specification" in result_text

    def test_caveat_section_present(self, result_text):
        assert "## Load-scaling caveat" in result_text
        assert "lower bound" in result_text

    def test_top10_table_non_empty(self, result_text):
        assert "## Top-10 combos" in result_text
        # Table must have at least header + sep + one row = 3 lines with |
        lines_with_pipe = [l for l in result_text.splitlines() if l.startswith("|")]
        assert len(lines_with_pipe) >= 3, "Top-10 table appears empty"

    def test_best_global_section_present(self, result_text):
        assert "## Best-global combo" in result_text
        assert "Six-segment signed-delta table" in result_text

    def test_per_city_ceiling_section_present(self, result_text):
        assert "## Per-city climate-aware ceiling" in result_text

    def test_coherence_metrics_section_present(self, result_text):
        assert "## Coherence verdict metrics" in result_text
        assert "n_within_15" in result_text
        assert "n_within_20" in result_text
        assert "opposite signs" in result_text
