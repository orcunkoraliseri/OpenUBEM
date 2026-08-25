"""G8.10/G8.11 artefact-driven meter validation tests."""
from __future__ import annotations

from openubem.validation.step8_gates import evaluate_meter_gates, parse_mdd_meter_names


MDD = """\
Output:Meter,Electricity:Facility,hourly;
Output:Meter,NaturalGas:Facility,hourly;
Output:Meter,Heating:Electricity,hourly;
"""


def _findings(required=("Electricity:Facility", "NaturalGas:Facility"), components=None):
    return {finding.gate: finding for finding in evaluate_meter_gates(
        parse_mdd_meter_names(MDD), required,
        selected_total=100.0,
        component_values=components or {"heating": 60.0, "equipment": 40.0},
    )}


def test_mdd_parser_and_null_meter_fixture_pass_both_hard_gates():
    available = parse_mdd_meter_names(MDD)
    assert "naturalgas:facility" in available
    report = _findings()
    assert report["G8.10"].passed
    assert report["G8.11"].passed
    assert {finding.severity for finding in report.values()} == {"hard"}


def test_pre_94_gas_meter_mutation_fails_name_and_balance_gates():
    report = _findings(required=("Electricity:Facility", "Gas:Facility"))
    assert not report["G8.11"].passed
    assert not report["G8.10"].passed


def test_zero_end_use_mutation_fails_balance_but_not_name_gate():
    report = _findings(components={"heating": 100.0, "equipment": 0.0})
    assert not report["G8.10"].passed
    assert report["G8.11"].passed


def test_out_of_tolerance_balance_fails():
    report = _findings(components={"heating": 60.0, "equipment": 39.0})
    assert not report["G8.10"].passed
