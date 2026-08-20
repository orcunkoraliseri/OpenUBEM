"""OPEN-48 third fleet run — twelve cells, post-OPEN-49-fix code, frozen inputs.

Same contract as open48_fleet_rerun_parallel.py: calls v12_cell_pipeline.run_cell
unchanged, one process and one log per cell. Two differences, both deliberate:

  1. output_subdir="open48_refleet3" — fresh local work dirs, fresh remote fleet
     dirs, fresh final results dir. No collision with the adopted phaseE_elevrb
     run or with run 2 (open48_refleet).

  2. The work dirs are PRE-SEEDED with run 2's cached 01_buildings.gpkg and its
     weather/ EPW before this script runs. step1_fetch loads the cache instead of
     re-fetching OSM (v12_cell_pipeline.py:138-141), so the OSM input is frozen
     byte-for-byte against run 2. step2 is NOT cached and re-runs against current
     code, which is where the OPEN-49 per-building-seed fix lives. Run 3 vs run 2
     is therefore a single-variable comparison: code only.

MAX_PARALLEL is 4, not run 2's 6. Six concurrent cells saturated the SSH link to
speed-submit2 and killed la_rural on scp and austin_urban on a squeue poll.

Usage:
    .venv\\Scripts\\python.exe scripts\\validation\\open48_fleet_run3.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
LOG_DIR = Path(r"C:\Users\o_iseri\AppData\Local\Temp\open48_run3")

CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]

OUTPUT_SUBDIR = "open48_refleet3"
MAX_PARALLEL = 4
STAGGER_S = 240
POLL_S = 30

CHILD = (
    "import sys; sys.path.insert(0, r'{repo}'); "
    "from scripts.validation.v12_cell_pipeline import run_cell; "
    "run_cell('{cell}', output_subdir='{sub}')"
)


def _preflight() -> int:
    """Refuse to start unless every cell's frozen input is in place."""
    import tempfile
    base = Path(tempfile.gettempdir()) / "ubem_validation" / OUTPUT_SUBDIR
    missing = [c for c in CELLS if not (base / c / "01_buildings.gpkg").exists()]
    if missing:
        print(f"PREFLIGHT FAILED — no seeded 01_buildings.gpkg for: {missing}", flush=True)
        print("Run 3 must not re-fetch OSM; seed the caches first.", flush=True)
        return 1
    print(f"PREFLIGHT OK — 12/12 cells carry a seeded 01_buildings.gpkg under {base}", flush=True)
    return 0


def _status(running: dict, done: dict, pending: list) -> None:
    lines = [f"open48 run 3 — {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
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
    if _preflight():
        return 2

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
    print("\n###### RUN 3 SUMMARY ######", flush=True)
    for cell in CELLS:
        print(f"  {cell}: rc={done.get(cell, 'NOT RUN')}", flush=True)
    return 0 if all(rc == 0 for rc in done.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
