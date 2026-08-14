"""OPEN-44 T02: triage the real-suite (tests/) failing/erroring nodes.

Reads the JUnit XML produced by a `pytest tests/` run and, for each
failing or erroring test, extracts: nodeid, outcome (failure/error),
exception type, and the first line of the assertion/error message.

Classification into the plan's closed set (artifact-missing,
fixture-missing, stale-expectation, real-defect, undetermined) is filled
in by hand in `_CLASSIFICATION` below, based on reading each test and the
shipped code it exercises -- this script does not guess a classification
from the exception text alone, per the plan's rule that real-defect
requires named evidence.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/open44_test_triage.py \
        <path-to-junit.xml> <path-to-output-csv>
"""
from __future__ import annotations

import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_CLASSIFICATION: dict[str, tuple[str, str, str]] = {
    "tests/test_debias.py::TestMlTierDebiasHook::test_disabled_by_default_never_calls_debias": (
        "stale-expectation",
        "Test asserts against config.IMPUTE_DEBIAS_NEWERSKEW, which does not exist in "
        "openubem/config.py (grepped in full 2026-08-13, absent). The debias functions "
        "it exercises (openubem/semantic/debias.py) exist and are tested elsewhere "
        "(TestDebiasNewerSkewMarginalAndRank etc., which pass); only the config-flag "
        "wiring the test expects was never shipped.",
        "openubem/config.py (attribute absent, confirmed by full-file read)",
    ),
    "tests/test_debias.py::TestMlTierDebiasHook::test_enabled_corrects_non_thin_stratum_and_skips_thin_stratum": (
        "stale-expectation",
        "Same missing config.IMPUTE_DEBIAS_NEWERSKEW as the row above.",
        "openubem/config.py (attribute absent)",
    ),
    "tests/test_debias.py::TestMlTierDebiasHook::test_global_fallback_fires_when_no_stratifier_column_present": (
        "stale-expectation",
        "Same missing config.IMPUTE_DEBIAS_NEWERSKEW as the row above.",
        "openubem/config.py (attribute absent)",
    ),
    "tests/test_debias.py::TestMlTierDebiasHook::test_global_fallback_noop_below_min_donors": (
        "stale-expectation",
        "Same missing config.IMPUTE_DEBIAS_NEWERSKEW as the row above.",
        "openubem/config.py (attribute absent)",
    ),
    "tests/test_debias.py::TestMlTierDebiasHook::test_disabled_for_non_knn_method_even_if_flag_set": (
        "stale-expectation",
        "Same missing config.IMPUTE_DEBIAS_NEWERSKEW as the row above.",
        "openubem/config.py (attribute absent)",
    ),
    "tests/test_draw_methods.py::TestDefaultByteIdentity::test_canonical_tier_order_and_handler_registry_wired_but_opt_in": (
        "stale-expectation",
        "AssertionError: expects imp._CANONICAL_TIER_ORDER == "
        "('fusion','spatial','ml','draw','statistical'); actual tuple has no 'draw' entry "
        "-- openubem/semantic/imputation.py:543 defines _CANONICAL_TIER_ORDER = "
        "('fusion','spatial','ml','statistical'). openubem/semantic/draw_methods.py:5-9 "
        "documents this directly: the draw tier is 'opt-in / OFF by construction ... "
        "until a future task (T07) wires _draw_tier into imputation.py's "
        "_CANONICAL_TIER_ORDER'. Not yet wired, by the module's own design note.",
        "openubem/semantic/imputation.py:543",
    ),
    "tests/test_draw_methods.py::TestDefaultByteIdentity::test_draw_method_by_target_config_default_empty": (
        "stale-expectation",
        "AttributeError: module 'openubem.config' has no attribute "
        "'IMPUTE_DRAW_METHOD_BY_TARGET' (grepped in full: absent from openubem/config.py).",
        "openubem/config.py (attribute absent)",
    ),
    "tests/test_draw_methods.py::TestDrawTierRouting::test_draw_tier_fills_with_kde_provenance_when_opted_in": (
        "stale-expectation",
        "Same missing config.IMPUTE_DRAW_METHOD_BY_TARGET as the row above.",
        "openubem/config.py (attribute absent)",
    ),
    "tests/test_draw_methods.py::TestDrawTierRouting::test_unconfigured_target_abstains_and_falls_through_to_statistical": (
        "stale-expectation",
        "Same missing config.IMPUTE_DRAW_METHOD_BY_TARGET as the row above.",
        "openubem/config.py (attribute absent)",
    ),
    "tests/test_draw_methods.py::TestDrawTierRouting::test_unknown_method_name_abstains_gracefully_never_raises": (
        "stale-expectation",
        "Same missing config.IMPUTE_DRAW_METHOD_BY_TARGET as the row above.",
        "openubem/config.py (attribute absent)",
    ),
    "tests/test_draw_methods.py::TestDrawTierRouting::test_default_cfg_still_byte_identical_even_with_draw_configured": (
        "stale-expectation",
        "Same missing config.IMPUTE_DRAW_METHOD_BY_TARGET as the row above.",
        "openubem/config.py (attribute absent)",
    ),
    "tests/test_draw_methods.py::TestDrawTierRouting::test_catfreq_routes_through_gdf_shaped_path_with_tokens": (
        "stale-expectation",
        "Same missing config.IMPUTE_DRAW_METHOD_BY_TARGET as the row above.",
        "openubem/config.py (attribute absent)",
    ),
    "tests/test_draw_methods.py::TestDrawTierRouting::test_hotdeck_routes_through_gdf_shaped_path_with_geometry": (
        "stale-expectation",
        "Same missing config.IMPUTE_DRAW_METHOD_BY_TARGET as the row above.",
        "openubem/config.py (attribute absent)",
    ),
    "tests/test_draw_methods.py::TestDrawTierDeterminism::test_same_seed_twice_run_byte_identical_across_whole_tier": (
        "stale-expectation",
        "Same missing config.IMPUTE_DRAW_METHOD_BY_TARGET as the row above.",
        "openubem/config.py (attribute absent)",
    ),
    "tests/test_impute_montage.py::test_out_dir_resolves_beside_parent_plan": (
        "artifact-missing",
        "Asserts a path resolves beside PLAN_input_imputation_implementation.md; the plan "
        "file is not present at the expected location on this machine.",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_impute_montage.py::test_expected_tile_count_per_phase": (
        "artifact-missing",
        "Phase_A source-figure folder has zero PNGs on this machine.",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_impute_montage.py::test_build_phase_montage_runs_for_every_phase": (
        "artifact-missing",
        "Same missing source PNGs as the row above.",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_impute_montage.py::test_main_writes_exactly_five_pngs": (
        "artifact-missing",
        "Same missing source PNGs as the row above (FileNotFoundError).",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_impute_montage.py::test_source_figures_untouched_by_running_main": (
        "artifact-missing",
        "Same missing source PNGs as the row above.",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_basis_diagnostic.py::TestRunGrid::test_csv_written_and_has_120_rows": (
        "artifact-missing",
        "Reads/writes into docs/docs_DONE/phaseC_combinedResim/v19_validation/, which does "
        "not exist on this machine at all.",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_basis_diagnostic.py::TestFindingsFile::test_file_exists": (
        "artifact-missing",
        "Same missing v19_validation directory as the row above.",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestGrid::test_csv_exists_with_120_rows": (
        "artifact-missing",
        "Same missing v19_validation directory as the row above.",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFile::test_file_exists": (
        "artifact-missing",
        "Same missing v19_validation directory as the row above.",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFile::test_csv_referenced_exists_with_120_rows": (
        "artifact-missing",
        "AssertionError: national_cbecs_sweep.csv not found under the missing v19_validation dir.",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestGridRecon::test_recon_csv_written_with_120_rows": (
        "artifact-missing",
        "OSError: cannot save into the non-existent v19_validation directory.",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFileRecon::test_both_csvs_exist_with_120_rows": (
        "artifact-missing",
        "Same missing v19_validation directory as the row above.",
        "n/a -- disk artifact, not shipped code",
    ),
    # -- ERROR at setup, both v19 files: every one is the `result_text` session
    # fixture calling write_findings()/write_findings_recon(), which writes
    # into docs/docs_DONE/phaseC_combinedResim/v19_validation/ -- confirmed
    # absent on this machine (same root cause as the FAILED v19 rows above).
    "tests/test_v19_basis_diagnostic.py::TestFindingsFile::test_grid_spec_section_present": (
        "artifact-missing",
        "ERROR at setup: FileNotFoundError writing RESULT_basis_diagnostic.md into the "
        "missing v19_validation directory (scripts/validation/v19_basis_diagnostic.py:351).",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_basis_diagnostic.py::TestFindingsFile::test_caveat_section_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_basis_diagnostic.py::TestFindingsFile::test_top10_table_non_empty": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_basis_diagnostic.py::TestFindingsFile::test_best_global_section_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_basis_diagnostic.py::TestFindingsFile::test_per_city_ceiling_section_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_basis_diagnostic.py::TestFindingsFile::test_coherence_metrics_section_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFile::test_grid_spec_section_present": (
        "artifact-missing",
        "ERROR at setup: FileNotFoundError writing RESULT_national_cbecs_rescore.md into "
        "the missing v19_validation directory (scripts/validation/v19_national_cbecs_rescore.py:391).",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFile::test_reconstruction_note_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFile::test_identity_baseline_section_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFile::test_top10_section_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFile::test_cross_reference_section_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFile::test_generalization_signal_in_text": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFile::test_f8_factual_cross_reference_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFileRecon::test_file_exists": (
        "artifact-missing",
        "ERROR at setup: FileNotFoundError writing RESULT_national_cbecs_rescore_reconstructed.md "
        "into the missing v19_validation directory (scripts/validation/v19_national_cbecs_rescore.py:699).",
        "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFileRecon::test_reconstruction_on_note_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFileRecon::test_identity_baseline_section_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFileRecon::test_top10_section_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFileRecon::test_head_to_head_section_present": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
    "tests/test_v19_national_cbecs_rescore.py::TestFindingsFileRecon::test_identity_nmbe_values_in_file": (
        "artifact-missing", "Same setup error as the row above.", "n/a -- disk artifact, not shipped code",
    ),
}


def _first_message_line(el: ET.Element) -> str:
    msg = el.attrib.get("message", "")
    return msg.splitlines()[0].strip() if msg else ""


import re as _re

_EXC_RE = _re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Warning|Exception))\b")


def _exception_type(el: ET.Element) -> str:
    msg = el.attrib.get("message", "")
    m = _EXC_RE.search(msg)
    if m:
        return m.group(1)
    return msg.split(":", 1)[0].strip() if msg else el.attrib.get("type", "")


def main(junit_path: str, out_csv: str) -> None:
    tree = ET.parse(junit_path)
    root = tree.getroot()
    rows = []
    seen = set()
    for testcase in root.iter("testcase"):
        classname = testcase.attrib.get("classname", "")
        name = testcase.attrib.get("name", "")
        outcome_el = testcase.find("failure")
        outcome = "failure"
        if outcome_el is None:
            outcome_el = testcase.find("error")
            outcome = "error"
        if outcome_el is None:
            continue
        parts = classname.split(".")
        if parts and parts[-1][:1].isupper():
            class_name = parts[-1]
            module_parts = parts[:-1]
        else:
            class_name = None
            module_parts = parts
        module_path = "/".join(module_parts) + ".py"
        nodeid = f"{module_path}::{class_name}::{name}" if class_name else f"{module_path}::{name}"
        if nodeid not in _CLASSIFICATION:
            raise KeyError(
                f"no classification recorded for {nodeid!r} (outcome={outcome}) -- "
                "every failing/erroring node in tests/ must be triaged by hand before "
                "this script can emit the CSV"
            )
        category, evidence, cite = _CLASSIFICATION[nodeid]
        rows.append({
            "nodeid": nodeid,
            "outcome": outcome,
            "exception_type": _exception_type(outcome_el),
            "message_first_line": _first_message_line(outcome_el),
            "category": category,
            "evidence": evidence,
            "shipped_code_citation": cite,
        })
        seen.add(nodeid)

    missing = set(_CLASSIFICATION) - seen
    if missing:
        raise AssertionError(
            f"{len(missing)} classified nodeid(s) were not found as failing/erroring in "
            f"this junit run (stale classification entries): {sorted(missing)}"
        )

    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "nodeid", "outcome", "exception_type", "message_first_line",
            "category", "evidence", "shipped_code_citation",
        ])
        writer.writeheader()
        for row in sorted(rows, key=lambda r: r["nodeid"]):
            writer.writerow(row)

    print(f"wrote {len(rows)} rows to {out_csv}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
