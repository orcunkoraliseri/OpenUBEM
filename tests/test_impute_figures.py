"""Tests for openubem/results/impute_figures.py — DATA-constant citations + per-figure smoke.

Per plan (docs/docs_ACTIVE/input/imputation/implementation/PLAN_figures_implementation.md T01-T07):
asserts the load-bearing DATA constants equal the §5 source-of-truth values, that _style() runs,
and that all seven build_* functions produce a non-empty Figure without error and that main()
writes all 7 PNGs.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

from openubem.results import impute_figures as fig_mod


def test_results_dir_resolves_correctly():
    assert fig_mod.RESULTS_DIR == fig_mod.REPO_ROOT / "docs" / "docs_ACTIVE" / "input" / "imputation" / "results"
    assert fig_mod.REPO_ROOT.name == "OpenUBEM"


# ---------------------------------------------------------------------------
# DATA-constant citation checks (§5 source-of-truth)
# ---------------------------------------------------------------------------
def test_data_phase_a_constants():
    a = fig_mod.DATA["A"]
    assert a["tests_total"] == 76  # RESULTS_phaseA.md L19
    assert a["idfs_byte_identical"] == 25  # RESULTS_phaseA.md L22
    assert a["idfs_total"] == 25  # RESULTS_phaseA.md L22
    assert a["eui_change_kwh_m2"] == 0.0  # RESULTS_phaseA.md L22-24
    assert a["provenance_coverage_before_pct"] == 0
    assert a["provenance_coverage_after_pct"] == 100
    assert sum(a["tests_suites"].values()) == 76  # RESULTS_phaseA.md L32-37


def test_data_phase_b_constants():
    b = fig_mod.DATA["B"]
    assert b["nyc_centre"]["nmbe"] == 0.49  # RESULTS_phaseB.md L35
    assert b["nyc_centre"]["cvrmse"] == 1.71  # RESULTS_phaseB.md L35
    assert b["nyc_centre"]["n"] == 32
    assert b["la_urban"]["nmbe"] == 0.08  # RESULTS_phaseB.md L36
    assert b["la_urban"]["cvrmse"] == 0.61  # RESULTS_phaseB.md L36
    assert b["la_urban"]["n"] == 124
    assert b["gate_nmbe_pct"] == 5.0
    assert b["gate_cvrmse_pct"] == 15.0
    assert b["tests_total"] == 121


def test_data_phase_c_constants():
    c = fig_mod.DATA["C"]
    assert c["eui_nmbe"] == -5.51
    assert c["eui_nmbe_verdict"] == "FAIL"
    assert c["eui_cvrmse"] == 7.93
    assert c["eui_cvrmse_verdict"] == "PASS"
    assert c["eui_n_buildings"] == 167
    assert c["eui_mean_before"] == 149.87
    assert c["eui_mean_after"] == 141.61
    assert c["year_built_methods"]["knn"]["mae"] == 25.14
    assert c["year_built_methods"]["Phase-A"]["mae"] == 26.43


def test_data_phase_d_constants():
    d = fig_mod.DATA["D"]
    assert d["fill_rates"]["height_m"]["pct"] == 87.6
    assert d["fill_rates"]["year_built"]["pct"] == 0.0
    assert d["n_buildings"] == 1667
    assert d["gate_pass"] == 171
    assert d["gate_fail"] == 0


def test_data_phase_e_constants():
    e = fig_mod.DATA["E"]
    assert e["classical_dominates_below_n"] == 30_000
    assert e["ubem_deep_precedent_n"] == 2_200_000
    assert e["verdicts"]["LLM"] == "FIRM DISQUALIFICATION"
    assert e["verdicts"]["TabPFN"] == "NOT READY"


def test_data_arc_summary_has_five_phases():
    arc = fig_mod.DATA["ARC"]
    assert [p["phase"] for p in arc["phases"]] == ["A", "B", "C", "D", "E"]


# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
def test_style_runs():
    fig_mod._style()  # must not raise
    assert plt.rcParams["figure.facecolor"] == fig_mod.PALETTE["surface"]
    assert plt.rcParams["savefig.dpi"] == 200


def test_style_never_transparent_surface():
    assert fig_mod.PALETTE["surface"] not in ("none", "transparent", None)
    assert fig_mod.PALETTE["surface"] == "#fcfcfb"


# ---------------------------------------------------------------------------
# Per-figure smoke (all 7 builders, T01-T07 scope)
# ---------------------------------------------------------------------------
def test_build_phaseA_provenance_runs():
    fig = fig_mod.build_phaseA_provenance()
    try:
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 2
    finally:
        plt.close(fig)


def test_build_phaseB_accuracy_runs():
    fig = fig_mod.build_phaseB_accuracy()
    try:
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 2
    finally:
        plt.close(fig)


def test_build_phaseC_leaderboard_runs():
    fig = fig_mod.build_phaseC_leaderboard()
    try:
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 3  # near, far, levels-companion
    finally:
        plt.close(fig)


def test_build_phaseC_eui_beforeafter_runs():
    fig = fig_mod.build_phaseC_eui_beforeafter()
    try:
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 2  # dumbbell, verdict chips
    finally:
        plt.close(fig)


def test_build_phaseD_fillrate_runs():
    fig = fig_mod.build_phaseD_fillrate()
    try:
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 1
    finally:
        plt.close(fig)


def test_build_phaseE_scalegap_runs():
    fig = fig_mod.build_phaseE_scalegap()
    try:
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 2  # number line, verdict strip
    finally:
        plt.close(fig)


def test_build_arc_summary_runs():
    fig = fig_mod.build_arc_summary()
    try:
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 5  # one column per phase A-E
    finally:
        plt.close(fig)


def test_main_writes_all_seven_pngs(tmp_path, monkeypatch):
    monkeypatch.setattr(fig_mod, "RESULTS_DIR", tmp_path)
    written = fig_mod.main()
    assert len(written) == 7
    for p in written:
        assert p.exists()
        assert p.stat().st_size > 0
    expected_names = {
        "phaseA_quant_provenance.png",
        "phaseB_quant_accuracy.png",
        "phaseC_quant_leaderboard.png",
        "phaseC_quant_eui_beforeafter.png",
        "phaseD_quant_fillrate.png",
        "phaseE_quant_scalegap.png",
        "arc_quant_summary.png",
    }
    assert {p.name for p in written} == expected_names
