"""G8.1--G8.4 same-cell re-run tests."""
from __future__ import annotations

from openubem.validation.step8_gates import REPRODUCIBILITY_DISCLAIMER, evaluate_reproducibility_gates


REFERENCE_MONTHLY = [100.0] * 12
REFERENCE_HOURLY = [10.0, 20.0, 30.0, 40.0]


def test_identical_rerun_passes_all_reproducibility_gates():
    report = evaluate_reproducibility_gates(
        REFERENCE_MONTHLY, REFERENCE_MONTHLY, REFERENCE_HOURLY, REFERENCE_HOURLY,
    )
    assert all(finding.passed and finding.severity == "hard" for finding in report)
    assert "not a validation" in REPRODUCIBILITY_DISCLAIMER


def test_annual_energy_scale_mutation_fails_monthly_and_hourly_nmbe():
    scaled_monthly = [value * 1.2 for value in REFERENCE_MONTHLY]
    scaled_hourly = [value * 1.2 for value in REFERENCE_HOURLY]
    report = {finding.gate: finding for finding in evaluate_reproducibility_gates(
        REFERENCE_MONTHLY, scaled_monthly, REFERENCE_HOURLY, scaled_hourly,
    )}
    assert not report["G8.1"].passed
    assert not report["G8.3"].passed
