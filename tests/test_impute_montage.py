"""Tests for openubem/results/impute_montage.py — per-phase montage builder.

Per plan §10 T13 (docs/docs_ACTIVE/input/imputation/implementation/
PLAN_figures_implementation.md): asserts main() writes exactly 5 PNGs (one per
phase A-E), each non-empty, and that the builder tiled the expected file count
per phase (the CP-F3-landed inventory: A=5, B=6, C=8, D=5, E=5).
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from openubem.results import impute_montage as mon_mod

_PLAN_MD = mon_mod.OUT_DIR / "PLAN_input_imputation_implementation.md"

_SKIP_NO_PLAN_MD = pytest.mark.skipif(
    not _PLAN_MD.exists(),
    reason=f"OPEN-44: artifact-missing -- {_PLAN_MD} does not exist on this machine.",
)

_SKIP_NO_RESULTS_DIR = pytest.mark.skipif(
    not mon_mod.RESULTS_DIR.exists(),
    reason=(
        f"OPEN-44: artifact-missing -- {mon_mod.RESULTS_DIR} does not exist on this "
        "machine (phase_A..E source-figure PNGs are not checked in as repo artifacts)."
    ),
)


def test_out_dir_resolves_beside_parent_plan():
    assert mon_mod.OUT_DIR == mon_mod.REPO_ROOT / "docs" / "docs_ACTIVE" / "input" / "imputation"


@_SKIP_NO_PLAN_MD
def test_out_dir_plan_md_exists():
    assert (mon_mod.OUT_DIR / "PLAN_input_imputation_implementation.md").exists()


def test_phases_are_a_through_e():
    assert mon_mod.PHASES == ["A", "B", "C", "D", "E"]


# ---------------------------------------------------------------------------
# Sort key — deterministic tile order (schematic, then quant, then scatter)
# ---------------------------------------------------------------------------
def test_sort_key_orders_schematic_then_quant_then_scatter():
    from pathlib import Path

    paths = [
        Path("phaseC_scatter_year_built.png"),
        Path("phaseC_quant_leaderboard.png"),
        Path("phaseC_leaderboard.png"),
        Path("phaseC_scatter_levels.png"),
        Path("phaseC_quant_eui_beforeafter.png"),
        Path("phaseC_cp3_verdict.png"),
    ]
    ordered = sorted(paths, key=mon_mod._sort_key)
    ordered_names = [p.stem for p in ordered]
    assert ordered_names == [
        "phaseC_cp3_verdict",
        "phaseC_leaderboard",
        "phaseC_quant_eui_beforeafter",
        "phaseC_quant_leaderboard",
        "phaseC_scatter_levels",
        "phaseC_scatter_year_built",
    ]


# ---------------------------------------------------------------------------
# Per-phase tile counts — the CP-F3-landed inventory (plan §10 T13)
# ---------------------------------------------------------------------------
@_SKIP_NO_RESULTS_DIR
def test_expected_tile_count_per_phase():
    expected = {"A": 5, "B": 6, "C": 8, "D": 5, "E": 5}
    for phase, n_expected in expected.items():
        pngs = list(mon_mod._phase_dir(phase).glob("*.png"))
        assert len(pngs) == n_expected, f"phase_{phase} has {len(pngs)} PNGs, expected {n_expected}"


@_SKIP_NO_RESULTS_DIR
def test_build_phase_montage_runs_for_every_phase():
    expected = {"A": 5, "B": 6, "C": 8, "D": 5, "E": 5}
    for phase, n_expected in expected.items():
        fig = mon_mod.build_phase_montage(phase)
        try:
            assert isinstance(fig, plt.Figure)
            assert len(fig.axes) == n_expected
        finally:
            plt.close(fig)


# ---------------------------------------------------------------------------
# main() — writes exactly 5 PNGs
# ---------------------------------------------------------------------------
@_SKIP_NO_RESULTS_DIR
def test_main_writes_exactly_five_pngs(tmp_path, monkeypatch):
    monkeypatch.setattr(mon_mod, "OUT_DIR", tmp_path)
    written = mon_mod.main()
    assert len(written) == 5
    for p in written:
        assert p.exists()
        assert p.stat().st_size > 0
    expected_names = {f"phase_{p}_all_figures.png" for p in "ABCDE"}
    assert {p.name for p in written} == expected_names


@_SKIP_NO_RESULTS_DIR
def test_source_figures_untouched_by_running_main(tmp_path, monkeypatch):
    """Read-only guarantee: running main() must not modify any source PNG
    under results/phase_<X>/ (mtimes/sizes unchanged)."""
    import os

    before = {}
    for phase in mon_mod.PHASES:
        for p in mon_mod._phase_dir(phase).glob("*.png"):
            before[p] = (p.stat().st_mtime_ns, p.stat().st_size)

    monkeypatch.setattr(mon_mod, "OUT_DIR", tmp_path)
    mon_mod.main()

    after = {}
    for phase in mon_mod.PHASES:
        for p in mon_mod._phase_dir(phase).glob("*.png"):
            after[p] = (p.stat().st_mtime_ns, p.stat().st_size)

    assert before == after
