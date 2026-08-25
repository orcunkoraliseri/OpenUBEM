"""G8.15 warning-kind triage and V8.f tests."""
from __future__ import annotations

from openubem.validation.step8_gates import evaluate_warning_gate


def test_clean_and_adjudicated_warning_kinds_pass():
    report = evaluate_warning_gate("** Warning ** benign autosizing notice: zone one\n", ["benign autosizing notice"])
    assert report.passed and report.severity == "hard"


def test_single_untriaged_kind_fails_even_when_benign_kind_is_repeated():
    text = "** Warning ** benign autosizing notice: zone one\n" * 1000
    text += "** Warning ** invalid schedule reference: gain load\n"
    report = evaluate_warning_gate(text, ["benign autosizing notice"])
    assert not report.passed
    assert "invalid schedule reference" in report.detail


def test_severe_or_fatal_message_fails_hard_even_without_warnings():
    severe = evaluate_warning_gate("** Severe  ** Surface is invalid: wall\n", [])
    fatal = evaluate_warning_gate("** Fatal  ** Program terminates\n", [])
    assert not severe.passed
    assert not fatal.passed
