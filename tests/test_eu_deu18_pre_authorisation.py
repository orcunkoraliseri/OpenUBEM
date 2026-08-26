"""D-EU-18 pre-authorisation bounds -- pure synthetic fixtures, never touches disk."""
from __future__ import annotations

import pytest

from openubem.acquisition.european_weather import (
    DEU18_PREAUTHORISED_FOLDS,
    evaluate_deu18_pre_authorisation,
)

_TOLERANCE_PCT = 10.0
_ALL_PASS_GATES = {"gate_1": "PASS", "gate_2": "PASS", "gate_3": "PASS", "gate_4": "PASS", "gate_6": "PASS"}


def _build_gate5_result(pairs: list[tuple[float, float]]) -> dict[str, object]:
    months = []
    offending_months: list[int] = []
    for index, (epw, benchmark) in enumerate(pairs, start=1):
        pct_difference = abs(epw - benchmark) / benchmark * 100.0
        within_tolerance = pct_difference <= _TOLERANCE_PCT
        if not within_tolerance:
            offending_months.append(index)
        months.append({
            "month": index,
            "epw_ghi_kwh_m2": epw,
            "benchmark_ghi_kwh_m2": benchmark,
            "pct_difference": pct_difference,
            "within_tolerance": within_tolerance,
        })
    return {
        "verdict": "FAIL" if offending_months else "PASS",
        "offending_months": offending_months,
        "monthly": months,
    }


def _uniform_pairs(baseline: float, replacements: dict[int, tuple[float, float]]) -> list[tuple[float, float]]:
    pairs = [(baseline, baseline)] * 12
    for index, pair in replacements.items():
        pairs[index - 1] = pair
    return pairs


def test_grant_single_offending_month_uk() -> None:
    gate5 = _build_gate5_result(_uniform_pairs(50.0, {6: (51.0, 45.0)}))
    result = evaluate_deu18_pre_authorisation(gate5, fold="uk", other_gate_verdicts=_ALL_PASS_GATES)
    assert result["granted"] is True
    assert result["granted_exception_months"] == [6]
    assert result["refusal_reasons"] == []


@pytest.mark.parametrize(
    "bench_off,epw_off,baseline",
    [
        pytest.param(42.69175108538351, 48.59175108538351, 12.72461705584608, id="fr_2023_m11"),
        pytest.param(53.65448504983389, 60.11448504983389, 262.06446830125475, id="es_2009_m12"),
        pytest.param(63.19886765746637, 72.12886765746637, 26.090655524900566, id="es_2010_m01"),
    ],
)
def test_historical_fold_years_clear_bounds(bench_off: float, epw_off: float, baseline: float) -> None:
    gate5 = _build_gate5_result(_uniform_pairs(baseline, {1: (epw_off, bench_off)}))
    result = evaluate_deu18_pre_authorisation(gate5, fold="uk", other_gate_verdicts=_ALL_PASS_GATES)
    assert result["granted"] is True


def test_bound1_other_gate_not_pass() -> None:
    gate5 = _build_gate5_result(_uniform_pairs(50.0, {6: (51.0, 45.0)}))
    gates = dict(_ALL_PASS_GATES)
    gates["gate_1"] = "FAIL"
    result = evaluate_deu18_pre_authorisation(gate5, fold="uk", other_gate_verdicts=gates)
    assert result["granted"] is False
    assert any(reason.startswith("GATE_NOT_PASS:gate_1=FAIL") for reason in result["refusal_reasons"])


def test_bound2_too_many_offending_months() -> None:
    pairs = _uniform_pairs(50.0, {1: (57.5, 50.0), 2: (57.5, 50.0), 3: (57.5, 50.0)})
    gate5 = _build_gate5_result(pairs)
    result = evaluate_deu18_pre_authorisation(gate5, fold="uk", other_gate_verdicts=_ALL_PASS_GATES)
    assert result["granted"] is False
    assert "TOO_MANY_OFFENDING_MONTHS:3" in result["refusal_reasons"]


def test_bound3_month_not_low_irradiance() -> None:
    gate5 = _build_gate5_result(_uniform_pairs(50.0, {6: (112.0, 100.0)}))
    result = evaluate_deu18_pre_authorisation(gate5, fold="uk", other_gate_verdicts=_ALL_PASS_GATES)
    assert result["granted"] is False
    assert any(reason.startswith("MONTH_NOT_LOW_IRRADIANCE:m6=100.0000") for reason in result["refusal_reasons"])


def test_bound4_relative_delta_exceeded() -> None:
    gate5 = _build_gate5_result(_uniform_pairs(50.0, {6: (65.0, 50.0)}))
    result = evaluate_deu18_pre_authorisation(gate5, fold="uk", other_gate_verdicts=_ALL_PASS_GATES)
    assert result["granted"] is False
    assert any(reason.startswith("RELATIVE_DELTA_EXCEEDED:m6=30.0000") for reason in result["refusal_reasons"])


def test_bound5_absolute_gap_exceeded() -> None:
    gate5 = _build_gate5_result(_uniform_pairs(50.0, {6: (93.5, 78.0)}))
    result = evaluate_deu18_pre_authorisation(gate5, fold="uk", other_gate_verdicts=_ALL_PASS_GATES)
    assert result["granted"] is False
    assert any(reason.startswith("ABSOLUTE_GAP_EXCEEDED:m6=15.5000") for reason in result["refusal_reasons"])


def test_bound6_annual_delta_exceeded() -> None:
    pairs = _uniform_pairs(100.0, {6: (51.0, 45.0)})
    for index in range(1, 13):
        if index != 6:
            pairs[index - 1] = (109.0, 100.0)
    gate5 = _build_gate5_result(pairs)
    result = evaluate_deu18_pre_authorisation(gate5, fold="uk", other_gate_verdicts=_ALL_PASS_GATES)
    assert result["granted"] is False
    assert any(reason.startswith("ANNUAL_DELTA_EXCEEDED:") for reason in result["refusal_reasons"])


@pytest.mark.parametrize("fold", ["es", "fr"])
def test_fold_not_pre_authorised(fold: str) -> None:
    gate5 = _build_gate5_result(_uniform_pairs(50.0, {6: (51.0, 45.0)}))
    result = evaluate_deu18_pre_authorisation(gate5, fold=fold, other_gate_verdicts=_ALL_PASS_GATES)
    assert result["granted"] is False
    assert result["refusal_reasons"] == ["FOLD_NOT_PRE_AUTHORISED"]
    assert fold not in DEU18_PREAUTHORISED_FOLDS


def test_no_exception_needed_when_no_offending_months() -> None:
    gate5 = _build_gate5_result(_uniform_pairs(50.0, {}))
    result = evaluate_deu18_pre_authorisation(gate5, fold="uk", other_gate_verdicts=_ALL_PASS_GATES)
    assert result["granted"] is False
    assert result["refusal_reasons"] == ["NO_EXCEPTION_NEEDED"]


def test_three_bounds_breached_at_once() -> None:
    pairs = _uniform_pairs(100.0, {1: (57.5, 50.0), 2: (57.5, 50.0), 3: (57.5, 50.0)})
    for index in range(4, 13):
        pairs[index - 1] = (109.0, 100.0)
    gate5 = _build_gate5_result(pairs)
    gates = dict(_ALL_PASS_GATES)
    gates["gate_1"] = "FAIL"
    result = evaluate_deu18_pre_authorisation(gate5, fold="uk", other_gate_verdicts=gates)
    assert result["granted"] is False
    reasons = result["refusal_reasons"]
    assert any(reason.startswith("GATE_NOT_PASS:gate_1=FAIL") for reason in reasons)
    assert "TOO_MANY_OFFENDING_MONTHS:3" in reasons
    assert any(reason.startswith("ANNUAL_DELTA_EXCEEDED:") for reason in reasons)
