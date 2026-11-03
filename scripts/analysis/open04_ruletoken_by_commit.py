"""T10 (OPEN-04): test the tag-coverage hypothesis for the classifier accuracy drift.

Runs the classifier code from each of the four bisect commits
(7635ce2, 67ede73, 0df422e, HEAD) over the CURRENT (held-constant)
tests/fixtures/labelled_archetypes_50.csv + boston/chicago gpkg fixtures, and records
the per-commit fine top-1 accuracy and rule-token distribution.

Historical commits are read via a disposable, sparse (openubem/ only — the full
checkout hits Windows MAX_PATH on this repo's long doc filenames) git worktree under
the scratchpad, never via `git checkout` on the main tree. Worktrees are removed at
the end of the run, success or failure.

Emits openubem/outputs/comparisons/open04_ruletoken_by_commit.csv, one row per commit.

Usage: python scripts/analysis/open04_ruletoken_by_commit.py
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKER = REPO_ROOT / "scripts" / "analysis" / "open04_ruletoken_worker.py"
OUT_CSV = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open04_ruletoken_by_commit.csv"

COMMITS = ["7635ce2", "67ede73", "0df422e", "HEAD"]
KNOWN_FINE_TOP1 = {"7635ce2": 92.0, "67ede73": 84.0, "0df422e": 88.0, "HEAD": 88.0}

RULE_TOKENS = [
    "FALLBACK_SIZE_DEFAULT", "RULE_USE_CLASS_SIZE", "FALLBACK_UNKNOWN",
    "RULE_HIGHRISE", "RULE_FUNCTION_TAG", "RULE_RESIDENTIAL_TIER",
    "RULE_LODGING_TIER", "RULE_USE_CLASS", "RULE_FUNCTION_TAG_SIZE",
    "MIXED_USE_DOMINANT_TAG",
]


def _run_worker(openubem_root: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(WORKER), str(openubem_root), str(REPO_ROOT)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(proc.stdout)


def main() -> None:
    scratch_base = Path(tempfile.mkdtemp(prefix="open04_wt_"))
    worktrees: list[Path] = []
    rows_out = []
    all_rows_by_commit = {}
    try:
        for commit in COMMITS:
            if commit == "HEAD":
                data = _run_worker(REPO_ROOT)
            else:
                wt_path = scratch_base / f"wt_{commit}"
                subprocess.run(
                    ["git", "worktree", "add", "--no-checkout", "--detach", str(wt_path), commit],
                    cwd=REPO_ROOT, check=True, capture_output=True, text=True,
                )
                worktrees.append(wt_path)
                subprocess.run(["git", "sparse-checkout", "init", "--cone"], cwd=wt_path, check=True, capture_output=True, text=True)
                subprocess.run(["git", "sparse-checkout", "set", "openubem"], cwd=wt_path, check=True, capture_output=True, text=True)
                subprocess.run(["git", "checkout", commit], cwd=wt_path, check=True, capture_output=True, text=True)
                data = _run_worker(wt_path)

            all_rows_by_commit[commit] = {r["osm_id"]: r for r in data["rows"]}
            n = data["n"]
            n_match = sum(1 for r in data["rows"] if r["match"])
            fine_top1 = 100.0 * n_match / n
            from collections import Counter
            counts = Counter(r["rule_token"] for r in data["rows"])
            row = {
                "commit": commit,
                "n": n,
                "n_match": n_match,
                "fine_top1_pct": round(fine_top1, 1),
                "known_fine_top1_pct": KNOWN_FINE_TOP1[commit],
                "reproduced_known": abs(fine_top1 - KNOWN_FINE_TOP1[commit]) < 0.05,
            }
            for tok in RULE_TOKENS:
                row[f"n_{tok.lower()}"] = counts.get(tok, 0)
            rows_out.append(row)
            print(f"{commit}: fine_top1={fine_top1:.1f}% (known {KNOWN_FINE_TOP1[commit]:.1f}%) "
                  f"n_fallback_size_default={counts.get('FALLBACK_SIZE_DEFAULT', 0)}")
    finally:
        for wt in worktrees:
            subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=REPO_ROOT, capture_output=True, text=True)
        subprocess.run(["git", "worktree", "prune"], cwd=REPO_ROOT, capture_output=True, text=True)
        shutil.rmtree(scratch_base, ignore_errors=True)

    import pandas as pd
    df = pd.DataFrame(rows_out)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {OUT_CSV} ({len(df)} rows)")

    fsd = df["n_fallback_size_default"].tolist()
    print(f"\nFALLBACK_SIZE_DEFAULT across the four commits: {fsd}")
    if len(set(fsd)) == 1:
        print("CONSTANT across every commit tested -> no row ever crosses the rule-17a boundary "
              "in this range -> tag-coverage hypothesis REFUTED.")
    else:
        print("VARIES across commits -> tag-coverage hypothesis SUPPORTED (rows cross the "
              "rule-17a boundary as classifier code changes).")


if __name__ == "__main__":
    main()
