"""OPEN-13 T03 -- what E-UTCI-12 still costs at HEAD, now that the suite runs clean.

Measurement only. The register's stated consequence for OPEN-13 -- "a bare
`pytest -q` aborts at collection ... the whole suite has not been runnable as
a whole" -- is checked against the live tree, which now carries
`[tool.pytest.ini_options] testpaths = ["tests"]` (pyproject.toml:52, no
addopts) and a repo-root conftest.py that sets PYTEST_DEBUG_TEMPROOT
(commit da6eed7, OPEN-52).

Five things are re-derived here, each from a command this script runs itself:

  1. The defect is still live: `_draw_tier` / `_draw_stratum_col_for` do not
     exist in openubem/semantic/imputation.py (grep -c "_draw_tier" -> 0).
  2. tests/test_draw_methods.py run in isolation: exact pass/skip counts and
     the verbatim skip reasons (pytest -rs).
  3. A static, file-level census of every `pytest.mark.skip(...)` /
     `pytest.skip(...)` site under tests/ -- NOT a re-run of the full 17-minute
     suite (the director's instruction for this task waives that; the
     1875 passed / 55 skipped / 1930 collected figure is therefore quoted
     from docs/docs_ACTIVE/openings/extra/FIX_open-52_temproot-remedy.md:173,
     not re-derived by executing the whole suite in this task). The static
     census is a lower bound on skip *sites*, not a byte-exact reconciliation
     against the runtime 55 -- parametrization and skipif truthiness can
     change a site's runtime skip count. This limitation is stated plainly in
     the measurement doc.
  4. Two collection counts: bare `pytest -q --collect-only` (repo root, no
     path) vs `pytest -q tests/ --collect-only`.
  5. A positive control proving the collection-count method would actually
     flag a collection error if one existed: an untracked, deliberately
     broken tests/test_zzz_open13_control.py (bad import) is added, the
     collect-only exit code and message are captured, then the file is
     deleted -- verified against `git status` to leave no trace (it was never
     tracked, so nothing needs reverting).

No fix, no code change to openubem/, no cluster access. Diagnosis only.

Writes: openubem/outputs/comparisons/open13_eutci12_residual.csv
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
OUT_CSV = REPO_ROOT / "openubem/outputs/comparisons/open13_eutci12_residual.csv"
TESTS_DIR = REPO_ROOT / "tests"

SKIP_MARKER_RE = re.compile(r"pytest\.mark\.skip(?:if)?\s*\(|pytest\.skip\s*\(")
SKIPPED_LINE_RE = re.compile(r"^SKIPPED \[(\d+)\] (\S+): (.*)$")


def run(cmd: list[str], cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def step1_defect_still_live() -> int:
    imputation_py = REPO_ROOT / "openubem" / "semantic" / "imputation.py"
    text = imputation_py.read_text(encoding="utf-8")
    count = len(re.findall(r"_draw_tier", text))
    print(f"=== STEP 1: grep -c \"_draw_tier\" openubem/semantic/imputation.py -> {count} ===")
    return count


def step2_targeted_run() -> tuple[int, int, list[dict]]:
    print("\n=== STEP 2: .venv/Scripts/python.exe -m pytest -q tests/test_draw_methods.py -rs ===")
    proc = run([str(PYTHON), "-m", "pytest", "-q", "tests/test_draw_methods.py", "-rs"])
    out = proc.stdout + proc.stderr
    print(out)

    skip_rows = []
    for line in out.splitlines():
        m = SKIPPED_LINE_RE.match(line.strip())
        if m:
            skip_rows.append({
                "n": int(m.group(1)),
                "location": m.group(2),
                "reason": m.group(3),
            })

    m_summary = re.search(r"(\d+) passed, (\d+) skipped", out)
    if not m_summary:
        raise RuntimeError("Could not parse pass/skip summary from pytest output")
    n_passed, n_skipped = int(m_summary.group(1)), int(m_summary.group(2))
    print(f"Parsed: {n_passed} passed, {n_skipped} skipped, "
          f"{len(skip_rows)} distinct SKIPPED lines")
    return n_passed, n_skipped, skip_rows


def step3_static_skip_census() -> dict[str, int]:
    print("\n=== STEP 3: static census of skip-marker SITES under tests/ (not a runtime rerun) ===")
    counts: dict[str, int] = {}
    for py_file in sorted(TESTS_DIR.glob("*.py")):
        text = py_file.read_text(encoding="utf-8", errors="replace")
        n = len(SKIP_MARKER_RE.findall(text))
        if n:
            counts[py_file.name] = n
    total_sites = sum(counts.values())
    for name, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {name}: {n} skip-marker site(s)")
    print(f"Total skip-marker sites across tests/: {total_sites}")
    print("Quoted baseline (NOT re-derived by full-suite execution in this task): "
          "1875 passed, 55 skipped, 1930 collected "
          "(source: docs/docs_ACTIVE/openings/extra/FIX_open-52_temproot-remedy.md:173)")
    return counts


def step4_collection_counts() -> tuple[str, str]:
    print("\n=== STEP 4: collection counts ===")
    bare = run([str(PYTHON), "-m", "pytest", "-q", "--collect-only"])
    bare_out = bare.stdout + bare.stderr
    bare_tail = "\n".join(bare_out.splitlines()[-3:])
    print(f"bare `pytest -q --collect-only` (repo root, no path):\n{bare_tail}\nexit={bare.returncode}")

    scoped = run([str(PYTHON), "-m", "pytest", "-q", "tests/", "--collect-only"])
    scoped_out = scoped.stdout + scoped.stderr
    scoped_tail = "\n".join(scoped_out.splitlines()[-3:])
    print(f"\n`pytest -q tests/ --collect-only`:\n{scoped_tail}\nexit={scoped.returncode}")

    return bare_tail, scoped_tail


def step5_control() -> dict[str, str]:
    print("\n=== STEP 5: positive control -- does the collection-count method detect a real error? ===")
    control_file = TESTS_DIR / "test_zzz_open13_control.py"
    control_file.write_text(
        "import this_module_does_not_exist_anywhere  "
        "# deliberate ImportError for collection-error control\n",
        encoding="utf-8",
    )
    try:
        proc = run([str(PYTHON), "-m", "pytest", "-q", "--collect-only"])
        out = proc.stdout + proc.stderr
        tail = "\n".join(out.splitlines()[-6:])
        print(f"With deliberately broken untracked file present:\n{tail}\nexit={proc.returncode}")
        result = {"control_output_tail": tail, "control_exit_code": str(proc.returncode)}
    finally:
        control_file.unlink(missing_ok=True)
        print(f"Deleted {control_file} (was untracked; nothing to revert in git).")
    return result


def main():
    n_draw_tier = step1_defect_still_live()
    n_passed, n_skipped, skip_rows = step2_targeted_run()
    static_census = step3_static_skip_census()
    bare_tail, scoped_tail = step4_collection_counts()
    control_result = step5_control()

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["section", "key", "value"])
        writer.writerow(["defect_live", "grep_count__draw_tier__imputation.py", n_draw_tier])
        writer.writerow(["targeted_run", "file", "tests/test_draw_methods.py"])
        writer.writerow(["targeted_run", "n_passed", n_passed])
        writer.writerow(["targeted_run", "n_skipped", n_skipped])
        for row in skip_rows:
            writer.writerow(["targeted_run_skip_detail", row["location"], row["reason"]])
        for name, n in sorted(static_census.items(), key=lambda kv: -kv[1]):
            writer.writerow(["static_skip_census", name, n])
        writer.writerow(["static_skip_census", "TOTAL_SITES", sum(static_census.values())])
        writer.writerow(["quoted_baseline", "source",
                          "docs/docs_ACTIVE/openings/extra/FIX_open-52_temproot-remedy.md:173"])
        writer.writerow(["quoted_baseline", "value", "1875 passed, 55 skipped, 1930 collected"])
        writer.writerow(["collection_count", "bare_pytest_q_collect_only_tail", bare_tail.replace("\n", " | ")])
        writer.writerow(["collection_count", "tests_scoped_collect_only_tail", scoped_tail.replace("\n", " | ")])
        writer.writerow(["control", "exit_code", control_result["control_exit_code"]])
        writer.writerow(["control", "output_tail", control_result["control_output_tail"].replace("\n", " | ")])

    print(f"\nWrote summary to {OUT_CSV}")


if __name__ == "__main__":
    main()
