"""OPEN-45 / T02 -- sweep the live tree for hard-coded ``** Severe **`` /
``** Fatal **`` / ``** Warning **`` literals, independent of the director's
starting list in PLAN_three-new-items-2026-08-12.md §4.

Leg A: walks openubem/, scripts/, tests/ (excluding scratchpad/ and
docs_DONE/), regex-scans every .py file for the marker family, and classifies
each hit as load-bearing / one-off / already-correct against a manually
verified classification table (built by reading every file's role -- see
extra/FIX_open-45_severe-matcher.md for the reasoning behind each verdict).
Repoints the load-bearing sites at openubem.results.err_parse (T01).

Non-vacuity control (hard rule 7): a known literal is planted in a scratch
file under the scanned tree, the scanner is shown to catch it, then the
scratch file is removed -- see run_non_vacuity_control() below.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
ROOTS = [REPO / "openubem", REPO / "scripts", REPO / "tests"]
EXCLUDE_DIR_NAMES = {"scratchpad", "docs_DONE"}
OUT_CSV = REPO / "openubem" / "outputs" / "comparisons" / "open45_severe_literal_sweep.csv"

LITERAL_RE = re.compile(r"\*\*\s*(Severe|Fatal|Warning)\s*\*\*")

# Files this task itself created -- they are the fix, not a finding, and are
# excluded from the classification sweep (their marker text is a docstring /
# test fixture, not error-parsing logic).
SELF_FILES = {
    "openubem/results/err_parse.py",
    "tests/test_err_parse.py",
    "scripts/analysis/open45_severe_literal_sweep.py",
}


def iter_py_files(roots: list[Path]):
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            if any(part in EXCLUDE_DIR_NAMES for part in p.parts):
                continue
            yield p


def scan(roots: list[Path]) -> list[tuple[str, int, str]]:
    hits = []
    for p in iter_py_files(roots):
        rel = p.relative_to(REPO).as_posix()
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            m = LITERAL_RE.search(line)
            if m:
                hits.append((rel, i, line.strip()))
    return hits


def run_non_vacuity_control() -> bool:
    """Plant a known one-space literal in a scratch .py file under scripts/analysis/,
    show the scanner finds it, then remove the file. Returns True iff the control
    passed (planted line was found, then correctly gone after cleanup)."""
    scratch = REPO / "scripts" / "analysis" / "_open45_non_vacuity_scratch.py"
    scratch.write_text(
        '# non-vacuity control planted line\n'
        'severes = [l for l in x if "** Severe **" in l]\n',
        encoding="utf-8",
    )
    try:
        hits = scan([REPO / "scripts"])
        found = any(h[0].endswith("_open45_non_vacuity_scratch.py") for h in hits)
    finally:
        scratch.unlink(missing_ok=True)
    hits_after = scan([REPO / "scripts"])
    gone = not any(h[0].endswith("_open45_non_vacuity_scratch.py") for h in hits_after)
    return found and gone


# ---------------------------------------------------------------------------
# Manual classification table, built by reading each file's role (docstring,
# call sites, which artifact tree it writes to). See the T02 report for the
# reasoning behind each row. Key = (relpath, line).
# ---------------------------------------------------------------------------
CLASSIFICATION: dict[tuple[str, int], tuple[str, str, str]] = {
    ("scripts/cluster/make_manifest_from_cluster.py", 47): (
        "load-bearing",
        "repointed",
        "generic reusable Step-4 manifest adapter, referenced by "
        "scripts/cluster/fetch_r3_results.py(.sh), scripts/validation/v11_nyc_centre_pipeline.py "
        "and docs_main/docs_step-4/PLAN_step-4-cluster-offload-R4.md -- infrastructure, not a "
        "spent one-off. Repointed at openubem.results.err_parse.first_severe.",
    ),
    ("openubem/simulation/runner.py", 140): (
        "load-bearing",
        "not repointed -- out of Executor A write-scope",
        "production sim-status classifier on the path that could produce an adopted artifact. "
        "Literal is \"**  Fatal  **\" (two-space, matches the real EnergyPlus form exactly for "
        "Fatal) so it is not the one-space bug, but it is also not whitespace-TOLERANT the way "
        "T01's helper is. Left untouched: plan §6 restricts Executor A's write-set to "
        "'the load-bearing scripts/** sites' -- openubem/** is outside that set.",
    ),
    ("tests/test_sim_integration.py", 171): (
        "load-bearing",
        "not repointed -- out of Executor A write-scope",
        "integration test asserting on production failure-triage output. Literal is "
        "\"**  Severe  **\" (two-space both sides) OR \"**  Fatal  **\". The Fatal half matches "
        "real EnergyPlus output; the Severe half does NOT -- every real Severe line found on this "
        "machine is \"** Severe  **\" (one space before, two after), so this check silently misses "
        "Severe lines the same way the OPEN-45 bug does. Left untouched: tests/** is outside "
        "Executor A's write-set per plan §6 (and not one of Executor D's four named test files "
        "either) -- flagged here so it is not lost.",
    ),
    ("scripts/analysis/a3_measure_band_deletion.py", 116): (
        "one-off",
        "left alone",
        "layoutAssigner storey-matching debug script (writes to "
        "docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/results/); "
        "that arc is CLOSED per project memory and 'not certified for fleet EUI' -- cannot be on a "
        "path that produces an adopted artifact. Spent.",
    ),
    ("scripts/analysis/a3_measure_band_deletion.py", 117): (
        "one-off", "left alone", "same file/reason as line 116.",
    ),
    ("scripts/analysis/a2_parse_results.py", 98): (
        "one-off",
        "left alone",
        "same layoutAssigner storey-matching debug family as a3_measure_band_deletion.py, same "
        "closed arc. Spent. (Also note: its literal \"**  Severe  **\" two-space-both-sides never "
        "matches real output either -- every real Severe line found on this machine is one-space- "
        "before/two-space-after -- but the script is retired, so it is listed, not fixed.)",
    ),
    ("scripts/analysis/a2_parse_results.py", 99): (
        "one-off", "left alone", "same file/reason as line 98.",
    ),
    ("scripts/analysis/a2_parse_results.py", 105): (
        "one-off", "left alone", "same file/reason as line 98.",
    ),
    ("scripts/analysis/a2_parse_results.py", 106): (
        "one-off", "left alone", "same file/reason as line 98.",
    ),
    ("scripts/analysis/c01_storey_matching_regression.py", 153): (
        "already-correct",
        "left alone",
        "comment only, describing the real EnergyPlus spacing fact; no matching logic on this "
        "line.",
    ),
    ("scripts/analysis/c01_storey_matching_regression.py", 154): (
        "already-correct",
        "left alone",
        "comment only (continuation of :153); the function this documents (severe_lines(), :157) "
        "already works around the real \"** Severe  **\" spacing via a prefix+suffix check, not a "
        "hard-coded whole-literal match. Also part of the closed layoutAssigner arc (one-off in "
        "addition to already-correct) -- either way, no action needed.",
    ),
    ("scripts/analysis/open42_six_failures.py", 49): (
        "already-correct",
        "left alone",
        "prose only: the marker text appears inside a quoted report string documenting a prior "
        "finding (OPEN-42, closed), not inside parsing logic. No literal-match bug present.",
    ),
    ("scripts/analysis/e02_failure_causes_subsurface.py", 8): (
        "already-correct",
        "left alone",
        "docstring line describing the method; the actual code (FATAL_RE / SEVERE_RE at :32-33) "
        "already uses re.compile(r\"\\*\\*\\s+Fatal\\s+\\*\\*\") / r\"\\*\\*\\s+Severe\\s+\\*\\*\" -- "
        "whitespace-tolerant, matches both spacings. This is the correct pattern; T01's helper "
        "generalises it into a shared module.",
    ),
    ("scripts/diagnostics/t01_reproduce_degenerate.py", 109): (
        "one-off",
        "left alone",
        "single-building diagnostic (way/428643335), already run, per its own docstring "
        "\"reproduce degenerate-surface pathology\". Spent.",
    ),
    ("scripts/diagnostics/t06_validate_relation6374725.py", 154): (
        "already-correct",
        "left alone",
        "checks both \"** Severe **\" and \"** Severe  **\" plus a whitespace-tolerant Fatal regex "
        "-- one of the two sites the director already named as the pattern to copy. Also a spent "
        "single-relation diagnostic (one-off), but already-correct takes precedence since no fix "
        "is needed either way.",
    ),
    ("scripts/diagnostics/t04_validate_way428643335.py", 134): (
        "already-correct",
        "left alone",
        "same pattern as t06_validate_relation6374725.py:154 -- director-named already-correct "
        "site; also a spent single-building diagnostic.",
    ),
    ("scripts/validation/v12_nyc_urban_recovery.py", 258): (
        "one-off",
        "left alone",
        "V12 nyc_urban recovery pipeline for one specific incident (bad fleet.lst format); writes "
        "to docs/validations/overAll/results/cases/ (a predecessor V12 validation tree, NOT "
        "docs_VALIDATION/.../phaseE_elevrb, the adopted run's tree). Single historical use. Spent.",
    ),
    ("scripts/validation/v12_la_urban_repair_step5.py", 355): (
        "one-off",
        "left alone",
        "repairs 3 named buildings (relation/6374725, way/402036180, way/428643335) for the V12 "
        "la_urban cell, predecessor validation tree (docs/validations/overAll/results/cases/, not "
        "the adopted phaseE_elevrb tree). Single historical use. Spent.",
    ),
    ("scripts/validation/v12_la_suburban_sql_repair_step5.py", 73): (
        "one-off",
        "left alone",
        "one-time SQL-path repair for the V12 la_suburban cell (predecessor validation tree). "
        "Spent.",
    ),
    ("scripts/validation/run_v11_step5.py", 79): (
        "one-off",
        "left alone",
        "V11 NYC city-centre pilot Step-5 driver, superseded by the V12/Phase-E pipeline. Spent.",
    ),
    ("scripts/validation/v12_la_suburban_recover.py", 396): (
        "one-off",
        "left alone",
        "one-time recovery for a single dropped-sbatch-response failure (way/442763908) in the V12 "
        "la_suburban cell (predecessor validation tree). Spent.",
    ),
    ("scripts/validation/phaseE_cpb_fixtures.py", 176): (
        "already-correct",
        "left alone",
        "checks txt.count(\"** Fatal  **\") + txt.count(\"**  Fatal  **\") -- both spacings. "
        "Director-named already-correct site.",
    ),
    ("scripts/validation/phaseE_cpb_fixtures.py", 177): (
        "already-correct",
        "left alone",
        "checks txt.count(\"** Severe **\") + txt.count(\"**  Severe  **\") -- both spacings. "
        "Director-named already-correct site.",
    ),
    ("scripts/validation/v12_la_rural_repair_472961100.py", 335): (
        "one-off",
        "left alone",
        "single-building repair (way/472961100) for the V12 la_rural cell (predecessor validation "
        "tree). Spent.",
    ),
    ("scripts/validation/v12_la_centre_fetch_step5.py", 125): (
        "one-off",
        "left alone",
        "one-time fetch+Step5 run for the V12 la_centre cell (predecessor validation tree). Spent.",
    ),
    ("scripts/validation/v12_la_centre_step5_fix.py", 101): (
        "one-off",
        "left alone",
        "one-time local re-aggregation for the V12 la_centre cell (predecessor validation tree). "
        "Spent.",
    ),
}


def main() -> int:
    control_ok = run_non_vacuity_control()
    print(f"Non-vacuity control passed: {control_ok}")
    if not control_ok:
        print("FATAL: non-vacuity control failed -- scanner is not trustworthy.", file=sys.stderr)
        return 1

    hits = scan(ROOTS)
    rows = []
    unclassified = []
    for rel, line, literal in hits:
        if rel in SELF_FILES:
            continue
        key = (rel, line)
        if key not in CLASSIFICATION:
            unclassified.append(key)
            classification, action, reason = "UNCLASSIFIED", "none", "not covered by manual review -- needs attention"
        else:
            classification, action, reason = CLASSIFICATION[key]
        rows.append({
            "path": rel, "line": line, "literal": literal,
            "classification": classification, "action_taken": action, "reason": reason,
        })

    df = pd.DataFrame(rows).sort_values(["classification", "path", "line"]).reset_index(drop=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {len(df)} rows -> {OUT_CSV}")
    print(df["classification"].value_counts().to_string())

    if unclassified:
        print(f"\nWARNING: {len(unclassified)} hits not covered by CLASSIFICATION table:")
        for u in unclassified:
            print(f"  {u}")
        return 1

    n_load_bearing = int((df["classification"] == "load-bearing").sum())
    n_repointed = int(((df["classification"] == "load-bearing") & (df["action_taken"] == "repointed")).sum())
    print(f"\nload-bearing sites found: {n_load_bearing}")
    print(f"load-bearing sites repointed by this task: {n_repointed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
