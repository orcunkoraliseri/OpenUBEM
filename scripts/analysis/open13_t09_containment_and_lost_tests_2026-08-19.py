"""T09 (PLAN_twenty-items-2026-08-19.md) -- OPEN-13: (a) verify E-UTCI-12 containment at HEAD,
(b) independently verify the 43 tests the 2026-08-12 containment traded away are still present
and passing at HEAD (rather than quoting the register's own account of the 2026-08-13 fix).

Compares test_draw_methods.py's test-function set at the pre-containment commit (25924dd, the
parent of a3bf4d9 which added the module-level skip) against HEAD, and classifies each of the 53
as deleted / renamed / skipped / still-present-and-passing based on a fresh `pytest -v` run.
"""
import csv
import re
import subprocess
import sys

REPO = r"C:\Users\o_iseri\Desktop\OpenUBEM"
PRE_CONTAINMENT_COMMIT = "25924dd"  # parent of a3bf4d9, before the module-level skip landed
OUT_CSV = REPO + r"\openubem\outputs\comparisons\open13_t09_containment_and_lost_tests.csv"


def sh(*args):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, check=True).stdout


def main():
    pre_src = sh("git", "show", f"{PRE_CONTAINMENT_COMMIT}:tests/test_draw_methods.py")
    head_src = open(REPO + r"\tests\test_draw_methods.py", encoding="utf-8").read()

    pre_names = sorted(set(re.findall(r"def (test_\w+)", pre_src)))
    head_names = sorted(set(re.findall(r"def (test_\w+)", head_src)))

    print(f"pre-containment ({PRE_CONTAINMENT_COMMIT}) test functions: {len(pre_names)}")
    print(f"HEAD test functions: {len(head_names)}")
    only_pre = sorted(set(pre_names) - set(head_names))
    only_head = sorted(set(head_names) - set(pre_names))
    print(f"present pre-containment, absent at HEAD (deleted/renamed): {only_pre}")
    print(f"present at HEAD, absent pre-containment (new): {only_head}")

    out = sh(
        str(REPO) + r"\.venv\Scripts\python.exe", "-m", "pytest",
        "tests/test_draw_methods.py", "-v", "--no-header",
    )
    lines = [l for l in out.splitlines() if "PASSED" in l or "SKIPPED" in l]
    print(f"\nHEAD run: {sum('PASSED' in l for l in lines)} passed, "
          f"{sum('SKIPPED' in l for l in lines)} skipped, {len(lines)} total")

    rows = []
    for line in lines:
        m = re.match(r"tests/test_draw_methods\.py::(\S+)\s+(PASSED|SKIPPED)", line)
        if not m:
            continue
        node_id, status = m.groups()
        func_name = node_id.split("::")[-1]
        if func_name in only_pre:
            cls = "deleted_or_renamed_MISMATCH"
        elif status == "PASSED":
            cls = "still_present_and_passing"
        else:
            cls = "skipped_future_feature_pin"
        rows.append({"node_id": node_id, "status": status, "classification": cls})

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["node_id", "status", "classification"])
        w.writeheader()
        w.writerows(rows)

    n_present_passing = sum(r["classification"] == "still_present_and_passing" for r in rows)
    n_skipped = sum(r["classification"] == "skipped_future_feature_pin" for r in rows)
    print(f"\nclassified: {n_present_passing} still_present_and_passing, "
          f"{n_skipped} skipped_future_feature_pin, "
          f"{len(rows) - n_present_passing - n_skipped} other")


if __name__ == "__main__":
    main()
