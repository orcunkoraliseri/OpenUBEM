"""Frozen Table 17 cross-tab contract for EU-09 local mutation fixtures."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from openubem.validation.step8_gates import (
    GateFinding,
    PERTURBATION_MATRIX,
    evaluate_perturbation_coverage,
)


ROOT = Path(__file__).parents[1]
MATRIX_CSV = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "content" / "eu_09_perturbation_matrix.csv"
CHECKPOINTS = (
    "G8.1", "G8.3", "G8.5", "G8.6", "G8.7", "G8.8", "G8.9", "G8.10", "G8.11",
    "G8.12", "G8.12.assignment", "G8.12.value", "G8.13", "G8.14", "G8.16",
)


def _findings(failed=()):
    failed = set(failed)
    return tuple(GateFinding(gate, gate not in failed, "local fixture") for gate in CHECKPOINTS)


def _passing_probes():
    return {
        expectation.identifier: _findings(expectation.must_fail)
        for expectation in PERTURBATION_MATRIX
    }


def test_machine_readable_matrix_matches_the_frozen_code_contract():
    with MATRIX_CSV.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert [row["perturbation_id"] for row in rows] == [entry.identifier for entry in PERTURBATION_MATRIX]
    assert [tuple(filter(None, row["must_fail"].split("|"))) for row in rows] == [entry.must_fail for entry in PERTURBATION_MATRIX]
    assert [tuple(filter(None, row["must_stay_clean"].split("|"))) for row in rows[:-1]] == [
        entry.must_stay_clean for entry in PERTURBATION_MATRIX[:-1]
    ]
    assert rows[-1]["must_stay_clean"] == "all observed checkpoints"


def test_every_pre_registered_transition_and_null_probe_passes_the_cross_tab():
    report = evaluate_perturbation_coverage(_findings(), _passing_probes())
    assert len(report) == 12
    assert all(result.passed for result in report)


def test_missing_required_failure_or_dirty_clean_checkpoint_fails_its_probe():
    probes = _passing_probes()
    probes["P10"] = _findings(("G8.1",))
    probes["P09"] = _findings(("G8.6", "G8.5"))
    report = {result.identifier: result for result in evaluate_perturbation_coverage(_findings(), probes)}
    assert report["P10"].missing_failures == ("G8.3",)
    assert report["P09"].dirty_clean_gates == ("G8.5",)


def test_missing_or_extra_probe_cannot_silently_shrink_the_coverage_matrix():
    probes = _passing_probes()
    probes.pop("P11")
    with pytest.raises(ValueError, match="missing=P11"):
        evaluate_perturbation_coverage(_findings(), probes)
