"""OPEN-53 T02 -- why 874 harvest directories have no eplusout.sql and no eplusout.end.

Measurement only. Walks the full local E02 harvest (HARVEST_ROOT), one row per
building directory, and records whether eplusout.sql / eplusout.end are present,
the size and terminal state of eplusout.err, and a terminal_class for every
directory.

For directories that are short a .sql or a .end ("short directories"), the
terminal_class is derived by reading the tail of eplusout.err:
    fatal      - contains a `**  Fatal  **` marker (whitespace-tolerant, via
                 openubem/results/err_parse.py)
    completed  - contains "EnergyPlus Completed Successfully"
    truncated  - neither of the above; the file ends mid-run
    empty      - eplusout.err is 0 bytes

Step 2 of the plan requires reproducing the exact census that opened OPEN-53
(40,800 dirs / 40,800 .eio / 40,800 .err / 39,926 .sql / 39,925 .end) before
anything else is trusted. That reproduction is printed first.

Step 5 requires an obligatory control: the same classifier run over a random
sample of 200 directories that DO have both .sql and .end, so the short
directories' class distribution can be judged against a healthy background
rather than in isolation.

No fix, no code change, no simulation, no cluster access. Diagnosis only.

Writes: openubem/outputs/comparisons/open53_missing_sql_census.csv
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from openubem.results.err_parse import FATAL_RE, SEVERE_RE  # noqa: E402

HARVEST_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest")
OUT_CSV = REPO_ROOT / "openubem/outputs/comparisons/open53_missing_sql_census.csv"

RANDOM_SEED = 53  # OPEN-53, fixed for reproducibility
CONTROL_SAMPLE_SIZE = 200

COMPLETED_MARKER = "EnergyPlus Completed Successfully"


def classify_err(err_path: Path) -> dict:
    """Read eplusout.err and return terminal_class, err_bytes, err_last_line, severe_line."""
    if not err_path.is_file():
        return {
            "err_bytes": 0,
            "err_last_line": "",
            "terminal_class": "missing_err_file",
            "severe_line": "",
        }

    err_bytes = err_path.stat().st_size
    if err_bytes == 0:
        return {
            "err_bytes": 0,
            "err_last_line": "",
            "terminal_class": "empty",
            "severe_line": "",
        }

    text = err_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    non_blank = [ln for ln in lines if ln.strip() != ""]
    last_line = non_blank[-1].strip() if non_blank else ""

    has_fatal = bool(FATAL_RE.search(text))
    has_completed = COMPLETED_MARKER in text

    if has_fatal:
        terminal_class = "fatal"
    elif has_completed:
        terminal_class = "completed"
    else:
        terminal_class = "truncated"

    severe_line = ""
    if has_fatal:
        fatal_line_no = None
        for i, line in enumerate(lines):
            if FATAL_RE.match(line):
                fatal_line_no = i + 1
                break
        severe_hits = [(i + 1, line.strip()) for i, line in enumerate(lines) if SEVERE_RE.match(line)]
        if fatal_line_no is not None:
            preceding = [h for h in severe_hits if h[0] <= fatal_line_no]
            if preceding:
                severe_line = preceding[-1][1]

    return {
        "err_bytes": err_bytes,
        "err_last_line": last_line,
        "terminal_class": terminal_class,
        "severe_line": severe_line,
    }


def walk_harvest():
    """Yield one row per building directory across the whole harvest."""
    rows = []
    for cell_mode_dir in sorted(HARVEST_ROOT.iterdir()):
        if not cell_mode_dir.is_dir():
            continue
        name = cell_mode_dir.name
        parts = name.rsplit("_", 1)
        candidates = [
            ("austin_centre", "auto"), ("austin_centre", "building"), ("austin_centre", "fast_zone"),
            ("austin_centre", "floor"), ("austin_centre", "layout_assign"),
        ]
        # cell/mode split: mode is one of the five known tokens, possibly two-word
        # ("fast_zone", "layout_assign"); cell is everything before it.
        for mode_token in ("layout_assign", "fast_zone", "auto", "building", "floor"):
            suffix = "_" + mode_token
            if name.endswith(suffix):
                cell = name[: -len(suffix)]
                mode = mode_token
                break
        else:
            raise ValueError(f"Cannot parse cell/mode from directory name: {name}")

        for building_dir in sorted(cell_mode_dir.iterdir()):
            if not building_dir.is_dir():
                continue
            stem = building_dir.name
            eio_path = building_dir / "eplusout.eio"
            err_path = building_dir / "eplusout.err"
            sql_path = building_dir / "eplusout.sql"
            end_path = building_dir / "eplusout.end"

            has_eio = eio_path.is_file()
            eio_empty = has_eio and eio_path.stat().st_size == 0
            has_err = err_path.is_file()
            has_sql = sql_path.is_file()
            has_end = end_path.is_file()

            rows.append({
                "cell": cell,
                "mode": mode,
                "stem": stem,
                "has_eio": has_eio,
                "eio_empty": eio_empty,
                "has_err": has_err,
                "has_sql": has_sql,
                "has_end": has_end,
                "dir_path": str(building_dir),
            })
    return rows


def main():
    print(f"Walking harvest at {HARVEST_ROOT} ...")
    rows = walk_harvest()

    n_dirs = len(rows)
    n_eio = sum(1 for r in rows if r["has_eio"])
    n_eio_empty = sum(1 for r in rows if r["eio_empty"])
    n_err = sum(1 for r in rows if r["has_err"])
    n_sql = sum(1 for r in rows if r["has_sql"])
    n_end = sum(1 for r in rows if r["has_end"])

    print("=== STEP 2: reproduction of the census that opened OPEN-53 ===")
    print(f"n_dirs={n_dirs}  n_eio={n_eio}  n_eio_empty={n_eio_empty}  "
          f"n_err={n_err}  n_sql={n_sql}  n_end={n_end}")
    pinned = {"n_dirs": 40800, "n_eio": 40800, "n_eio_empty": 0, "n_err": 40800,
              "n_sql": 39926, "n_end": 39925}
    reproduced = {"n_dirs": n_dirs, "n_eio": n_eio, "n_eio_empty": n_eio_empty,
                  "n_err": n_err, "n_sql": n_sql, "n_end": n_end}
    if reproduced != pinned:
        print("MISMATCH against pinned census (fact 1). STOP required by plan step 2.")
        print(f"  pinned:     {pinned}")
        print(f"  reproduced: {reproduced}")
    else:
        print("MATCH: reproduced census equals the pinned figures in plan §5 fact 1.")

    short_rows = [r for r in rows if not r["has_sql"] or not r["has_end"]]
    healthy_rows = [r for r in rows if r["has_sql"] and r["has_end"]]
    print(f"\nn_short (missing .sql or .end) = {len(short_rows)}")
    print(f"n_healthy (has both) = {len(healthy_rows)}")

    print("\n=== Classifying short directories via eplusout.err ===")
    for r in short_rows:
        err_path = Path(r["dir_path"]) / "eplusout.err"
        r.update(classify_err(err_path))

    class_counts = {}
    for r in short_rows:
        c = r["terminal_class"]
        class_counts[c] = class_counts.get(c, 0) + 1
    print("Target (short-directory) terminal_class counts:")
    for c, n in sorted(class_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {c}: {n}")

    print("\n=== STEP 5: control -- 200 random directories that DO have .sql and .end ===")
    rng = random.Random(RANDOM_SEED)
    control_sample = rng.sample(healthy_rows, min(CONTROL_SAMPLE_SIZE, len(healthy_rows)))
    for r in control_sample:
        err_path = Path(r["dir_path"]) / "eplusout.err"
        r.update(classify_err(err_path))

    control_counts = {}
    for r in control_sample:
        c = r["terminal_class"]
        control_counts[c] = control_counts.get(c, 0) + 1
    print(f"Control sample size: {len(control_sample)}")
    print("Control terminal_class counts:")
    for c, n in sorted(control_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {c}: {n}")

    print("\n=== Fatal cause classes among short directories ===")
    fatal_rows = [r for r in short_rows if r["terminal_class"] == "fatal"]
    severe_counts = {}
    for r in fatal_rows:
        s = r["severe_line"] if r["severe_line"] else "NO_SEVERE_FOUND_BEFORE_FATAL"
        severe_counts[s] = severe_counts.get(s, 0) + 1
    print(f"n_fatal = {len(fatal_rows)}")
    for s, n in sorted(severe_counts.items(), key=lambda kv: -kv[1]):
        print(f"  [{n}] {s}")

    print("\n=== Concentration by (cell, mode) among short directories ===")
    cellmode_counts = {}
    for r in short_rows:
        key = (r["cell"], r["mode"])
        cellmode_counts[key] = cellmode_counts.get(key, 0) + 1
    cellmode_totals = {}
    for r in rows:
        key = (r["cell"], r["mode"])
        cellmode_totals[key] = cellmode_totals.get(key, 0) + 1
    for key, n in sorted(cellmode_counts.items(), key=lambda kv: -kv[1]):
        total = cellmode_totals[key]
        print(f"  {key[0]}_{key[1]}: {n} / {total} short ({100.0 * n / total:.1f}%)")

    # write all rows (short + control, tagged) plus every other row with minimal info
    all_out_rows = []
    control_ids = {id(r) for r in control_sample}
    for r in rows:
        out = {
            "cell": r["cell"],
            "mode": r["mode"],
            "stem": r["stem"],
            "has_sql": r["has_sql"],
            "has_end": r["has_end"],
            "err_bytes": r.get("err_bytes", ""),
            "err_last_line": r.get("err_last_line", ""),
            "terminal_class": r.get("terminal_class", ""),
            "severe_line": r.get("severe_line", ""),
            "is_short": (not r["has_sql"] or not r["has_end"]),
            "is_control_sample": id(r) in control_ids,
        }
        all_out_rows.append(out)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["cell", "mode", "stem", "has_sql", "has_end", "err_bytes",
                  "err_last_line", "terminal_class", "severe_line", "is_short",
                  "is_control_sample"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_out_rows:
            writer.writerow(row)
    print(f"\nWrote {len(all_out_rows)} rows to {OUT_CSV}")


if __name__ == "__main__":
    main()
