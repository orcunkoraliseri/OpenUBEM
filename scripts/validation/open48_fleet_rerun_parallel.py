"""T04 (OPEN-48 part 2) — parallel driver for the remaining cells of the fleet
re-run. Same contract as open48_fleet_rerun.py: calls v12_cell_pipeline.run_cell
unchanged with output_subdir="open48_refleet". The only difference is that cells
run concurrently, each in its own process with its own log file, instead of one
after another.

Local IDF generation is n_jobs=1 serial (v12_cell_pipeline.py:210-212), so each
cell occupies one core here; MAX_PARALLEL is well under this machine's 20. Each
cell submits its own sbatch array capped at %32 by submit_cluster_array.

Usage:
    .venv\\Scripts\\python.exe scripts\\validation\\open48_fleet_rerun_parallel.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
LOG_DIR = Path(r"C:\Users\o_iseri\AppData\Local\Temp\open48_par")

CELLS = [
    "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]

OUTPUT_SUBDIR = "open48_refleet"
MAX_PARALLEL = 6
STAGGER_S = 180
POLL_S = 30

CHILD = (
    "import sys; sys.path.insert(0, r'{repo}'); "
    "from scripts.validation.v12_cell_pipeline import run_cell; "
    "run_cell('{cell}', output_subdir='{sub}')"
)


def _status(running: dict, done: dict, pending: list) -> None:
    lines = [f"open48 parallel re-run — {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    for cell, (proc, started) in sorted(running.items()):
        mins = (time.time() - started) / 60.0
        lines.append(f"  RUNNING  {cell:16s} pid={proc.pid} {mins:.0f} min")
    for cell, rc in sorted(done.items()):
        lines.append(f"  {'DONE   ' if rc == 0 else 'FAILED '}  {cell:16s} rc={rc}")
    for cell in pending:
        lines.append(f"  PENDING  {cell}")
    (LOG_DIR / "STATUS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    pending = list(CELLS)
    running: dict = {}
    done: dict = {}
    last_launch = 0.0

    while pending or running:
        for cell in [c for c, (p, _) in running.items() if p.poll() is not None]:
            proc, started = running.pop(cell)
            done[cell] = proc.returncode
            print(f"[{time.strftime('%H:%M:%S')}] {cell} finished rc={proc.returncode} "
                  f"after {(time.time() - started) / 60.0:.0f} min", flush=True)

        if (pending and len(running) < MAX_PARALLEL
                and time.time() - last_launch >= STAGGER_S):
            cell = pending.pop(0)
            log = open(LOG_DIR / f"{cell}.log", "w", encoding="utf-8", errors="replace")
            proc = subprocess.Popen(
                [sys.executable, "-u", "-c",
                 CHILD.format(repo=REPO, cell=cell, sub=OUTPUT_SUBDIR)],
                cwd=str(REPO), stdout=log, stderr=subprocess.STDOUT,
            )
            running[cell] = (proc, time.time())
            last_launch = time.time()
            print(f"[{time.strftime('%H:%M:%S')}] launched {cell} pid={proc.pid} "
                  f"({len(running)} running, {len(pending)} pending)", flush=True)

        _status(running, done, pending)
        time.sleep(POLL_S)

    _status(running, done, pending)
    print("\n###### T04 PARALLEL SUMMARY ######", flush=True)
    for cell in CELLS:
        print(f"  {cell}: rc={done.get(cell, 'NOT RUN')}", flush=True)
    return 0 if all(rc == 0 for rc in done.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
