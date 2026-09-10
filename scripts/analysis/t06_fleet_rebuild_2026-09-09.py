"""T06 (accuracy-restatement plan) -- fleet-wide rebuild orchestrator.

Launches scripts/analysis/t06_cell_rebuild_2026-09-09.py for all 12 cells of the
published fleet IN PARALLEL (one subprocess per cell, all launched together --
never one cell after another), local only, no Speed cluster, no EnergyPlus.
Mirrors the existing scripts/validation/open48_fleet_run4.py launcher pattern
(the harness that produced run 4) but stops after Steps 1-3, since T07
(re-simulation) is a separate, CP-2-gated task.

Usage: py t06_fleet_rebuild_2026-09-09.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PY = REPO / ".venv" / "Scripts" / "python.exe"
CHILD = REPO / "scripts" / "analysis" / "t06_cell_rebuild_2026-09-09.py"
EVIDENCE = REPO / "evidence" / "open48_refleet"
OUTPUT_SUBDIR = "t06_rebuild_2026-09-09"
LOG_DIR = Path(tempfile.gettempdir()) / "t06_rebuild_logs"

CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]


def _preflight() -> int:
    import geopandas as gpd
    total = 0
    missing = []
    for c in CELLS:
        p = EVIDENCE / c / "01_buildings.gpkg"
        if not p.exists():
            missing.append(c)
            continue
        total += len(gpd.read_file(str(p)))
    if missing:
        print(f"PREFLIGHT FAILED -- missing frozen evidence for: {missing}")
        return 1
    print(f"PREFLIGHT OK -- 12/12 cells carry frozen 01_buildings.gpkg under {EVIDENCE}, "
          f"total raw rows = {total} (expect 8160)")
    if total != 8160:
        print(f"PREFLIGHT WARNING -- frozen total {total} != 8160, proceeding but flag this before CP-2")
    return 0


def main() -> int:
    if _preflight():
        return 2

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    procs = {}
    t_start = time.monotonic()
    for cell in CELLS:
        log = open(LOG_DIR / f"{cell}.log", "w", encoding="utf-8", errors="replace")
        proc = subprocess.Popen(
            [str(PY), str(CHILD), cell, OUTPUT_SUBDIR],
            stdout=log, stderr=subprocess.STDOUT, cwd=str(REPO),
        )
        procs[cell] = (proc, log)
        print(f"launched {cell} pid={proc.pid}", flush=True)

    results = {}
    while procs:
        for cell in list(procs.keys()):
            proc, log = procs[cell]
            rc = proc.poll()
            if rc is not None:
                log.close()
                results[cell] = rc
                elapsed = time.monotonic() - t_start
                print(f"[{time.strftime('%H:%M:%S')}] {cell} finished rc={rc} (+{elapsed:.0f}s)", flush=True)
                del procs[cell]
        if procs:
            time.sleep(5)

    print("\n=== ALL CELLS FINISHED ===")
    for cell in CELLS:
        print(f"  {cell}: rc={results.get(cell, 'NOT RUN')}")

    total_raw = total_enriched = total_manifest = total_success = 0
    per_cell = {}
    import tempfile as _tf
    base = Path(_tf.gettempdir()) / "ubem_validation" / OUTPUT_SUBDIR
    for cell in CELLS:
        sp = base / cell / "t06_summary.json"
        if not sp.exists():
            print(f"MISSING SUMMARY for {cell} at {sp}")
            continue
        s = json.loads(sp.read_text(encoding="utf-8"))
        per_cell[cell] = s
        total_raw += s["n_raw"]
        total_enriched += s["n_enriched"]
        total_manifest += s["n_manifest"]
        total_success += s["n_idf_success"]

    print(f"\nTOTAL raw={total_raw} enriched={total_enriched} manifest_rows={total_manifest} "
          f"idf_success={total_success}")
    (base / "t06_fleet_summary.json").write_text(
        json.dumps({"per_cell": per_cell, "totals": {
            "raw": total_raw, "enriched": total_enriched,
            "manifest": total_manifest, "idf_success": total_success,
        }}, indent=2), encoding="utf-8")
    print(f"Fleet summary written to {base / 't06_fleet_summary.json'}")
    return 0 if all(rc == 0 for rc in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
