"""T09 -- Mandatory downstream-EUI impact check
(`openubem/validation/eui_impact.py`).

Input-Imputation arc, Phase B. **Comparator-math + scaffold ONLY** (PLAN §6
T09 dispatch scope) -- no EnergyPlus run happens anywhere in this file.
`compare_ab` is never invoked here; the live Simulation-A/B run (LIVE_SMOKE)
is a single later call the manager authorizes explicitly (PLAN §7 CP-2).

Load-bearing properties under test:
  (1) MBE/NMBE/CV(RMSE) are pinned to exact ASHRAE-G14-style values on
      hand-built A/B EUI arrays with known differences -- pinning the
      formula BEFORE any simulation ever runs against it;
  (2) peak-load deviation (aggregate + worst-case per-building) is pinned
      the same way;
  (3) `eui_impact_report` wires the pass/fail gates to the plan's stated
      targets (|NMBE| < 5%, CV(RMSE) < 15%) and raises on unpaired arrays;
  (4) the read-only/no-feedback invariant: this module never imports or
      references `impute_missing`/`ImputeConfig` from any function's code
      object or module globals -- the EUI numbers it computes have no path
      back into an imputer setting (zero-fitted-params, PLAN §2 rule 4).
"""
import numpy as np
import pytest

from openubem.validation import eui_impact as ei


# ── hand-built A/B arrays (values chosen for exact, hand-checkable math) ────

_EUI_OBSERVED = np.array([100.0, 200.0, 300.0, 400.0])
_EUI_IMPUTED = np.array([110.0, 190.0, 330.0, 380.0])
# diff = [10, -10, 30, -20] -> mbe=2.5, mean(obs)=250 -> nmbe=1.0%
# diff**2 = [100,100,900,400] -> mean=375 -> rmse=sqrt(375) -> cv_rmse=7.745966692414834%
_EXPECTED_EUI_MBE = 2.5
_EXPECTED_EUI_NMBE_PCT = 1.0
_EXPECTED_EUI_CVRMSE_PCT = 7.745966692414834

_PEAK_OBSERVED = np.array([50.0, 80.0, 60.0])
_PEAK_IMPUTED = np.array([55.0, 76.0, 66.0])
# diff = [5, -4, 6] -> mbe=2.3333333333333335, mean(obs)=63.333... -> nmbe=3.68421052631579%
# per-building pct = [10.0, -5.0, 10.0] -> max abs = 10.0
_EXPECTED_PEAK_MBE = 2.3333333333333335
_EXPECTED_PEAK_NMBE_PCT = 3.68421052631579
_EXPECTED_PEAK_CVRMSE_PCT = 7.999307449247718
_EXPECTED_PEAK_MAX_ABS_PCT = 10.0


class TestComparatorMath:
    def test_mbe_pinned(self):
        assert ei.mbe(_EUI_OBSERVED, _EUI_IMPUTED) == pytest.approx(_EXPECTED_EUI_MBE)

    def test_nmbe_pinned(self):
        assert ei.nmbe(_EUI_OBSERVED, _EUI_IMPUTED) == pytest.approx(_EXPECTED_EUI_NMBE_PCT)

    def test_cv_rmse_pinned(self):
        assert ei.cv_rmse(_EUI_OBSERVED, _EUI_IMPUTED) == pytest.approx(_EXPECTED_EUI_CVRMSE_PCT)

    def test_zero_error_is_zero(self):
        same = np.array([120.0, 80.0, 200.0])
        assert ei.mbe(same, same) == 0.0
        assert ei.nmbe(same, same) == 0.0
        assert ei.cv_rmse(same, same) == 0.0

    def test_nmbe_sign_convention(self):
        observed = np.array([100.0, 100.0])
        # imputed systematically ABOVE observed -> positive NMBE (predicted - measured)
        assert ei.nmbe(observed, np.array([110.0, 110.0])) == pytest.approx(10.0)
        # imputed systematically BELOW observed -> negative NMBE
        assert ei.nmbe(observed, np.array([90.0, 90.0])) == pytest.approx(-10.0)


class TestPeakLoadDeviation:
    def test_peak_deviation_pinned(self):
        result = ei.peak_load_deviation(_PEAK_OBSERVED, _PEAK_IMPUTED)
        assert result["n"] == 3
        assert result["peak_mbe"] == pytest.approx(_EXPECTED_PEAK_MBE)
        assert result["peak_nmbe_pct"] == pytest.approx(_EXPECTED_PEAK_NMBE_PCT)
        assert result["peak_cv_rmse_pct"] == pytest.approx(_EXPECTED_PEAK_CVRMSE_PCT)
        assert result["peak_max_abs_pct_deviation"] == pytest.approx(_EXPECTED_PEAK_MAX_ABS_PCT)
        np.testing.assert_allclose(
            result["per_building_pct_deviation"], np.array([10.0, -5.0, 10.0]),
        )

    def test_peak_deviation_zero_when_identical(self):
        same = np.array([40.0, 60.0, 90.0])
        result = ei.peak_load_deviation(same, same)
        assert result["peak_mbe"] == 0.0
        assert result["peak_nmbe_pct"] == 0.0
        assert result["peak_cv_rmse_pct"] == 0.0
        assert result["peak_max_abs_pct_deviation"] == 0.0


class TestEuiImpactReport:
    def test_report_matches_pinned_math(self):
        report = ei.eui_impact_report(_EUI_OBSERVED, _EUI_IMPUTED)
        assert report["n_buildings"] == 4
        assert report["eui_mbe"] == pytest.approx(_EXPECTED_EUI_MBE)
        assert report["eui_nmbe_pct"] == pytest.approx(_EXPECTED_EUI_NMBE_PCT)
        assert report["eui_cv_rmse_pct"] == pytest.approx(_EXPECTED_EUI_CVRMSE_PCT)
        assert report["peak"] is None

    def test_gate_targets_match_plan_thresholds(self):
        assert ei.EUI_NMBE_THRESHOLD_PCT == 5.0
        assert ei.EUI_CVRMSE_THRESHOLD_PCT == 15.0
        report = ei.eui_impact_report(_EUI_OBSERVED, _EUI_IMPUTED)
        # 1.0% < 5% and 7.75% < 15% -> both gates PASS on this hand-built pair
        assert report["eui_nmbe_pass"] is True
        assert report["eui_cv_rmse_pass"] is True

    def test_gate_fails_when_thresholds_exceeded(self):
        observed = np.array([100.0, 100.0, 100.0])
        imputed = np.array([120.0, 120.0, 120.0])  # +20% bias, +20% CV(RMSE)
        report = ei.eui_impact_report(observed, imputed)
        assert report["eui_nmbe_pct"] == pytest.approx(20.0)
        assert report["eui_cv_rmse_pct"] == pytest.approx(20.0)
        assert report["eui_nmbe_pass"] is False
        assert report["eui_cv_rmse_pass"] is False

    def test_report_includes_peak_when_provided(self):
        report = ei.eui_impact_report(
            _EUI_OBSERVED, _EUI_IMPUTED,
            peak_observed=_PEAK_OBSERVED, peak_imputed=_PEAK_IMPUTED,
        )
        assert report["peak"] is not None
        assert report["peak"]["peak_nmbe_pct"] == pytest.approx(_EXPECTED_PEAK_NMBE_PCT)

    def test_raises_on_unpaired_arrays(self):
        with pytest.raises(ValueError):
            ei.eui_impact_report(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0]))


class TestNoImputerFeedback:
    """Dedicated pin for PLAN §2 rule 4 / T09 read-only requirement: no EUI
    value computed here has any code path back into an imputer setting."""

    _FUNCS = ("mbe", "nmbe", "cv_rmse", "peak_load_deviation", "eui_impact_report", "compare_ab")
    _FORBIDDEN_NAMES = ("impute_missing", "ImputeConfig", "imputation")

    def test_module_globals_never_import_the_imputer(self):
        module_globals = vars(ei)
        for forbidden in self._FORBIDDEN_NAMES:
            assert forbidden not in module_globals, (
                f"eui_impact.py module namespace must never import '{forbidden}' "
                "-- this module is read-only on the imputer (zero-fitted-params)."
            )

    def test_no_function_code_references_the_imputer(self):
        for func_name in self._FUNCS:
            func = getattr(ei, func_name)
            referenced = set(func.__code__.co_names)
            for forbidden in self._FORBIDDEN_NAMES:
                assert forbidden not in referenced, (
                    f"{func_name} must never reference '{forbidden}' in its code "
                    "object -- the EUI comparator is read-only on the imputer "
                    "(no feedback loop, PLAN §2 rule 4)."
                )

    def test_compare_ab_is_scaffold_only_not_invoked_here(self):
        # Structural existence check only -- compare_ab is intentionally never
        # called in this test file or anywhere else in this task (T09 scope:
        # comparator-math + scaffold ONLY; the live A/B run is LIVE_SMOKE,
        # gated behind manager authorization at PLAN §7 CP-2).
        assert callable(ei.compare_ab)
        assert "compare_ab" in ei.__all__
