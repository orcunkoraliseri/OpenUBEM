"""G8.5--G8.7 peak and archetype-band contract tests."""
from __future__ import annotations

import pytest

from openubem.validation.step8_gates import (
    evaluate_archetype_eui_band_gate,
    evaluate_peak_gates,
)


REFERENCE = [1.0, 2.0, 10.0, 2.0, 1.0]


def test_named_peak_comparison_within_magnitude_and_timing_limits_passes():
    report = evaluate_peak_gates(REFERENCE, [1.0, 2.0, 11.0, 2.0, 1.0], comparison_label="retained reference cell")
    assert all(finding.passed for finding in report)


def test_two_hour_peak_shift_fails_timing_but_not_magnitude():
    report = {finding.gate: finding for finding in evaluate_peak_gates(
        REFERENCE, [1.0, 2.0, 1.0, 2.0, 10.0], comparison_label="retained reference cell",
    )}
    assert report["G8.5"].passed
    assert not report["G8.6"].passed


def test_peak_magnitude_over_fifteen_percent_fails_g85():
    report = {finding.gate: finding for finding in evaluate_peak_gates(
        REFERENCE, [1.0, 2.0, 12.0, 2.0, 1.0], comparison_label="retained reference cell",
    )}
    assert not report["G8.5"].passed
    assert report["G8.6"].passed


def test_g87_grades_as_modelled_band_and_keeps_empirical_comparison_informational():
    finding = evaluate_archetype_eui_band_gate(
        90.0, (80.0, 100.0), expected_floor_area_m2=75.0, reported_floor_area_m2=75.0,
        empirical_eui_kwh_m2=125.0, empirical_band_kwh_m2=(80.0, 100.0),
    )
    assert finding.passed
    assert "informational only" in finding.detail


def test_different_geometry_area_fails_g87_even_when_eui_is_plausible():
    finding = evaluate_archetype_eui_band_gate(
        90.0, (80.0, 100.0), expected_floor_area_m2=75.0, reported_floor_area_m2=112.5,
    )
    assert not finding.passed


def test_peak_gate_requires_a_named_unique_reference_peak():
    with pytest.raises(ValueError, match="comparison_label"):
        evaluate_peak_gates(REFERENCE, REFERENCE, comparison_label="")
    with pytest.raises(ValueError, match="unique peak"):
        evaluate_peak_gates([1.0, 10.0, 10.0], [1.0, 10.0, 9.0], comparison_label="reference")
