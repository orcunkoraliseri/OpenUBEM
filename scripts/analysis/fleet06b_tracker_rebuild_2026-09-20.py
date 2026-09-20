"""Rebuild results.csv/progress.json for FLEET-06b from disk (tracker only, no sim touched).

Written 2026-09-20 after the live run's own checkpoint thread inside
`fleet06b_local_run_2026-09-18.py cmd_full()` froze around 2026-09-19 13:55 (last
run_log.txt / progress.json write) while the EnergyPlus worker pool kept finishing
cases unrecorded -- see PROMPT_MANAGER_techtransfer_2026-09-18.md section 7b for the
incident writeup. Run this again any time results.csv looks stale relative to disk
(compare its row count to `find .../out -name eplusout.end | wc -l`).

Read-only against the live run: only appends rows to results.csv that are not already
present, and only for work_dirs that carry a genuine eplusout.end. Classification logic
mirrors openubem.simulation.runner.classify_outcome exactly (success marker + sql/sql.gz
presence, fatal marker, else crash), so rebuilt rows are consistent with rows the live
process would have written itself. Note: a background disk-cleanup script
(sweep_fleet06b.ps1, not part of the official pipeline) gzip-compresses some finished
cases' eplusout.sql to eplusout.sql.gz and deletes the original -- this script still
counts those as "success" (sql.gz counts), but the codebase's own `is_completed()` /
`classify_outcome()` only check for eplusout.sql, so any case whose sql was swept will
look incomplete to the live run itself and to the eventual FLEET-06c harvest step until
that mismatch is fixed or the harvest is taught to accept .sql.gz.
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import time
from pathlib import Path

TEMP = Path(os.environ["TEMP"])
OUT_ROOT = TEMP / "ubem_validation" / "fleet06b_local_2026-09-18"
OUT_DIR = OUT_ROOT / "out"
RESULTS_CSV = OUT_ROOT / "results.csv"
PROGRESS_JSON = OUT_ROOT / "progress.json"
MANIFEST_CSV = TEMP / "ubem_validation" / "fleet06a_campaign_2026-09-18" / "manifest_65112.csv"

RESULTS_FIELDS = [
    "building_id", "cell_name", "geo_cell", "epw_path", "idf_path", "work_dir",
    "status", "n_warnings", "n_severe", "wall_clock_s", "error_summary",
]

SUCCESS_MARKER = "EnergyPlus Completed Successfully"
FATAL_MARKER = "EnergyPlus Terminated--Fatal Error Detected"
END_COUNT_RE = re.compile(r"(\d+)\s+Warning.*?(\d+)\s+Severe", re.IGNORECASE)


def parse_end_counts(text: str) -> tuple[int | None, int | None]:
    m = END_COUNT_RE.search(text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def main() -> None:
    with MANIFEST_CSV.open(newline="", encoding="utf-8") as f:
        total = sum(1 for _ in csv.DictReader(f))

    recorded: set[tuple[str, str]] = set()
    with RESULTS_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            recorded.add((row["cell_name"], row["building_id"]))
    existing_rows = len(recorded)

    backup = RESULTS_CSV.with_suffix(".csv.bak_rebuild")
    shutil.copy2(RESULTS_CSV, backup)

    new_rows: list[dict] = []
    gz_success = 0
    unfinished_seen = 0
    for cell_dir in sorted(p for p in OUT_DIR.iterdir() if p.is_dir()):
        cell_name = cell_dir.name
        for b_dir in cell_dir.iterdir():
            if not b_dir.is_dir():
                continue
            building_id = b_dir.name
            key = (cell_name, building_id)
            if key in recorded:
                continue
            end_file = b_dir / "eplusout.end"
            if not end_file.exists():
                unfinished_seen += 1
                continue
            end_text = end_file.read_text(errors="replace")
            n_warn = n_sev = None
            err_summary = ""
            if FATAL_MARKER in end_text:
                status = "failed_fatal"
                n_warn, n_sev = parse_end_counts(end_text)
                err_file = b_dir / "eplusout.err"
                if err_file.exists():
                    err_summary = err_file.read_text(errors="replace")[-500:]
            elif SUCCESS_MARKER in end_text:
                sql = b_dir / "eplusout.sql"
                sqlgz = b_dir / "eplusout.sql.gz"
                if sql.exists() or sqlgz.exists():
                    status = "success"
                    n_warn, n_sev = parse_end_counts(end_text)
                    if sqlgz.exists() and not sql.exists():
                        gz_success += 1
                else:
                    status = "failed_crash"
                    err_summary = "eplusout.sql missing despite success marker"
            else:
                status = "failed_crash"
                err_summary = end_text[-500:]
            new_rows.append({
                "building_id": building_id,
                "cell_name": cell_name,
                "geo_cell": "",
                "epw_path": "",
                "idf_path": "",
                "work_dir": str(b_dir),
                "status": status,
                "n_warnings": n_warn,
                "n_severe": n_sev,
                "wall_clock_s": "",
                "error_summary": err_summary,
            })
            recorded.add(key)

    with RESULTS_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RESULTS_FIELDS)
        for r in new_rows:
            w.writerow({k: r.get(k, "") for k in RESULTS_FIELDS})

    with RESULTS_CSV.open(newline="", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))
    done = len(all_rows)
    failed = sum(1 for r in all_rows if r["status"] != "success")

    PROGRESS_JSON.write_text(json.dumps({
        "done": done, "failed": failed, "remaining": total - done,
        "total": total, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rebuilt_from_disk": True, "rebuilt_new_rows": len(new_rows),
        "rebuilt_gz_success_cases": gz_success,
    }, indent=2), encoding="utf-8")

    print(f"existing_rows={existing_rows} new_rows={len(new_rows)} "
          f"unfinished_dirs_skipped={unfinished_seen} gz_success_among_new={gz_success}")
    print(f"final results.csv rows={done} failed={failed} total_manifest={total} "
          f"remaining={total - done}")
    print(f"backup written to {backup}")


if __name__ == "__main__":
    main()
