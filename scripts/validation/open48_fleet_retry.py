"""T04 (OPEN-48 part 2) — retry driver for cells that failed on SSH transport.

Both failures seen during the parallel pass (la_rural on scp, austin_urban on a
squeue poll) were the SSH link to speed-submit2 saturating under six concurrent
cells, not modelling or cluster-capacity failures. This driver re-runs the named
cells ONE AT A TIME, with a bounded number of attempts each, so the link carries
a single cell's traffic.

Same contract as the other two drivers: it calls v12_cell_pipeline.run_cell
unchanged with output_subdir="open48_refleet". v12_cell_pipeline.py is not
modified.

Before re-running a cell, cancel any orphaned array of ours still queued for it
(see the T04 progress log) — this driver does not do that for you.

Usage:
    .venv\\Scripts\\python.exe scripts\\validation\\open48_fleet_retry.py la_rural austin_urban
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
LOG_DIR = Path(r"C:\Users\o_iseri\AppData\Local\Temp\open48_par")

OUTPUT_SUBDIR = "open48_refleet"
MAX_ATTEMPTS = 3
BACKOFF_S = 120

CHILD = (
    "import sys; sys.path.insert(0, r'{repo}'); "
    "from scripts.validation.v12_cell_pipeline import run_cell; "
    "run_cell('{cell}', output_subdir='{sub}')"
)


def _run(cell: str, attempt: int) -> int:
    log_path = LOG_DIR / f"{cell}.retry{attempt}.log"
    with open(log_path, "w", encoding="utf-8", errors="replace") as log:
        proc = subprocess.run(
            [sys.executable, "-u", "-c",
             CHILD.format(repo=REPO, cell=cell, sub=OUTPUT_SUBDIR)],
            cwd=str(REPO), stdout=log, stderr=subprocess.STDOUT,
        )
    return proc.returncode


def main(cells: list) -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    done = {}

    for cell in cells:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            started = time.time()
            print(f"[{time.strftime('%H:%M:%S')}] retry {cell} attempt {attempt}/"
                  f"{MAX_ATTEMPTS}", flush=True)
            rc = _run(cell, attempt)
            mins = (time.time() - started) / 60.0
            print(f"[{time.strftime('%H:%M:%S')}] {cell} attempt {attempt} rc={rc} "
                  f"after {mins:.0f} min", flush=True)
            done[cell] = rc
            if rc == 0:
                break
            if attempt < MAX_ATTEMPTS:
                time.sleep(BACKOFF_S)

    print("\n###### T04 RETRY SUMMARY ######", flush=True)
    for cell in cells:
        print(f"  {cell}: rc={done.get(cell, 'NOT RUN')}", flush=True)
    return 0 if all(rc == 0 for rc in done.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
