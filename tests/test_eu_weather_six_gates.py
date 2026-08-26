"""Offline tests for DR08 gates 5 and 6 (EU-07). No network, no live EnergyPlus required."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from openubem.acquisition.european_weather import (
    evaluate_energyplus_smoke_gate,
    evaluate_monthly_benchmark_gate,
    evaluate_six_gates,
)

_TOLERANCE_PCT = 10.0
_HOURS = pd.date_range("2001-01-01", periods=8760, freq="h")
_HOURS_IN_MONTH = {m: int((_HOURS.month == m).sum()) for m in range(1, 13)}


def _write_epw(path: Path, ghi_by_month: dict[int, float]) -> None:
    header = [
        "LOCATION,Test,State,Country,Source,000000,45.72,4.95,1.0,200.0",
        "DESIGN CONDITIONS,0", "TYPICAL/EXTREME PERIODS,0", "GROUND TEMPERATURES,0",
        "HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0", "COMMENTS 1,synthetic test only",
        "COMMENTS 2,no weather data claim", "DATA PERIODS,1,1,Data,Sunday,1/1,12/31",
    ]
    rows = []
    for stamp in _HOURS:
        ghi = ghi_by_month[stamp.month]
        fields = ["2001", str(stamp.month), str(stamp.day), str(stamp.hour + 1), "60", "0",
                  "10", "5", "50", "101325", "0", "0", "0", str(ghi), "0", str(ghi), "0", "0",
                  "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
                  "0", "0", "0", "0", "0"]
        rows.append(",".join(fields))
    path.write_text("\n".join(header + rows) + "\n", encoding="utf-8")


def _write_benchmark(path: Path, kwh_by_month: dict[int, float], source: str = "synthetic test benchmark") -> None:
    path.write_text(json.dumps({
        "source": source,
        "monthly_ghi_kwh_m2": [kwh_by_month[m] for m in range(1, 13)],
    }), encoding="utf-8")


def _baseline_kwh_by_month(ghi_wm2: float) -> dict[int, float]:
    return {m: _HOURS_IN_MONTH[m] * ghi_wm2 / 1000.0 for m in range(1, 13)}


def test_gate5_pass_when_every_month_within_tolerance(tmp_path: Path):
    epw = tmp_path / "matching.epw"
    _write_epw(epw, {m: 200.0 for m in range(1, 13)})
    benchmark = tmp_path / "benchmark.json"
    _write_benchmark(benchmark, _baseline_kwh_by_month(200.0))
    result = evaluate_monthly_benchmark_gate(epw, benchmark, tolerance_pct=_TOLERANCE_PCT)
    assert result["verdict"] == "PASS"
    assert result["offending_months"] == []


def test_gate5_fails_when_a_month_exceeds_tolerance_with_no_approval(tmp_path: Path):
    ghi_by_month = {m: 200.0 for m in range(1, 13)}
    ghi_by_month[7] = 240.0
    epw = tmp_path / "july_off.epw"
    _write_epw(epw, ghi_by_month)
    benchmark = tmp_path / "benchmark.json"
    _write_benchmark(benchmark, _baseline_kwh_by_month(200.0))
    result = evaluate_monthly_benchmark_gate(epw, benchmark, tolerance_pct=_TOLERANCE_PCT)
    assert result["verdict"] == "FAIL"
    assert result["offending_months"] == [7]


def test_gate5_pass_with_documented_exception_only_when_approval_matches_exactly(tmp_path: Path):
    ghi_by_month = {m: 200.0 for m in range(1, 13)}
    ghi_by_month[7] = 240.0
    epw = tmp_path / "july_off.epw"
    _write_epw(epw, ghi_by_month)
    benchmark = tmp_path / "benchmark.json"
    _write_benchmark(benchmark, _baseline_kwh_by_month(200.0))

    exact = evaluate_monthly_benchmark_gate(
        epw, benchmark, tolerance_pct=_TOLERANCE_PCT, approved_exception_months=[7],
    )
    assert exact["verdict"] == "PASS_WITH_DOCUMENTED_EXCEPTION"

    wrong = evaluate_monthly_benchmark_gate(
        epw, benchmark, tolerance_pct=_TOLERANCE_PCT, approved_exception_months=[6],
    )
    assert wrong["verdict"] == "FAIL"

    partial = evaluate_monthly_benchmark_gate(
        epw, benchmark, tolerance_pct=_TOLERANCE_PCT, approved_exception_months=[6, 7],
    )
    assert partial["verdict"] == "FAIL"


def test_gate5_raises_on_missing_or_malformed_benchmark(tmp_path: Path):
    epw = tmp_path / "matching.epw"
    _write_epw(epw, {m: 200.0 for m in range(1, 13)})

    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(ValueError, match="benchmark file not found"):
        evaluate_monthly_benchmark_gate(epw, missing, tolerance_pct=_TOLERANCE_PCT)

    not_json = tmp_path / "not_json.json"
    not_json.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        evaluate_monthly_benchmark_gate(epw, not_json, tolerance_pct=_TOLERANCE_PCT)

    missing_keys = tmp_path / "missing_keys.json"
    missing_keys.write_text(json.dumps({"source": "x"}), encoding="utf-8")
    with pytest.raises(ValueError, match="12 'monthly_ghi_kwh_m2'"):
        evaluate_monthly_benchmark_gate(epw, missing_keys, tolerance_pct=_TOLERANCE_PCT)


def test_gate6_returns_unavailable_when_energyplus_root_does_not_exist(tmp_path: Path):
    epw = tmp_path / "matching.epw"
    _write_epw(epw, {m: 200.0 for m in range(1, 13)})
    result = evaluate_energyplus_smoke_gate(epw, energyplus_root=tmp_path / "no_such_energyplus")
    assert result["verdict"] == "UNAVAILABLE_ENERGYPLUS"


def test_evaluate_six_gates_returns_exactly_the_six_registry_keys(tmp_path: Path):
    epw = tmp_path / "matching.epw"
    _write_epw(epw, {m: 200.0 for m in range(1, 13)})
    benchmark = tmp_path / "benchmark.json"
    _write_benchmark(benchmark, _baseline_kwh_by_month(200.0))
    result = evaluate_six_gates(
        epw,
        benchmark_path=benchmark,
        tolerance_pct=_TOLERANCE_PCT,
        energyplus_root=tmp_path / "no_such_energyplus",
    )
    assert set(result.keys()) == {
        "gate_1_header",
        "gate_2_8760_continuity",
        "gate_3_no_missing_mandatory_fields",
        "gate_4_physical_and_solar_bounds",
        "gate_5_monthly_national_benchmark",
        "gate_6_energyplus_smoke",
    }
    assert result["gate_1_header"] == "PASS"
    assert result["gate_5_monthly_national_benchmark"] == "PASS"
    assert result["gate_6_energyplus_smoke"] == "UNAVAILABLE_ENERGYPLUS"
