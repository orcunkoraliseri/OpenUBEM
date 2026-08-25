"""V8.c single-source fixed-band checks for EU-09."""
from __future__ import annotations

import pytest

from openubem.validation.step8_bands import STEP8_GATE_BANDS
from openubem.validation.step8_gates import evaluate_peak_gates, evaluate_reproducibility_gates


def test_step8_fixed_bands_are_immutable_and_match_the_parent_contract():
    assert dict(STEP8_GATE_BANDS) == {
        "G8.1.monthly_nmbe_pct": 5.0,
        "G8.2.hourly_nmbe_pct": 10.0,
        "G8.3.monthly_cvrmse_pct": 15.0,
        "G8.4.hourly_cvrmse_pct": 30.0,
        "G8.5.peak_relative_difference": 0.15,
        "G8.6.peak_timing_hours": 1,
        "G8.10.meter_balance_relative_difference": 0.005,
    }
    with pytest.raises(TypeError):
        STEP8_GATE_BANDS["G8.1.monthly_nmbe_pct"] = 6.0


def test_scorers_report_limits_from_the_imported_single_source():
    reproduction = {finding.gate: finding for finding in evaluate_reproducibility_gates(
        [100.0] * 12, [100.0] * 12, [10.0, 20.0], [10.0, 20.0],
    )}
    peak = {finding.gate: finding for finding in evaluate_peak_gates(
        [1.0, 10.0, 1.0], [1.0, 11.0, 1.0], comparison_label="fixture",
    )}
    assert "limit +/-5.0%" in reproduction["G8.1"].detail
    assert "limit +/-15%" in peak["G8.5"].detail
