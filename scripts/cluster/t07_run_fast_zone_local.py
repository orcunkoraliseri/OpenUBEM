"""T07 — run the fast_zone pilot LOCALLY on Windows with EnergyPlus 23.1.

Mirrors the cluster submit_fleet.sbatch flow exactly:
  copy Energy+.idd + IDF->in.idf into OUTDIR, run ExpandObjects, then run
  energyplus on expanded.idf (if produced) else in.idf.

Produces eplusout.sql/.err/.end per building under:
  <tmp>/ubem_t07_pilot/sim_out_fast_zone/<stem>/

Usage:
    py -3 scripts/cluster/t07_run_fast_zone_local.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

EP_DIR = Path(r"C:\EnergyPlusV23-1-0")
EP_EXE = EP_DIR / "energyplus.exe"
EXPAND_EXE = EP_DIR / "ExpandObjects.exe"
EP_IDD = EP_DIR / "Energy+.idd"

WORK_BASE = Path(tempfile.gettempdir()) / "ubem_t07_pilot"
IDF_DIR = WORK_BASE / "step3_fast_zone" / "idfs"
SIM_OUT = WORK_BASE / "sim_out_fast_zone"
EPW = WORK_BASE / "weather" / "weather" / "USA_CA_Lancaster-Fox.Field.723816_TMYx.2011-2025.epw"


def run_one(idf_path_str: str) -> tuple[str, str, int]:
    idf_path = Path(idf_path_str)
    stem = idf_path.stem
    outdir = SIM_OUT / stem
    outdir.mkdir(parents=True, exist_ok=True)

    shutil.copy(str(EP_IDD), str(outdir / "Energy+.idd"))
    shutil.copy(str(idf_path), str(outdir / "in.idf"))

    # ExpandObjects (writes expanded.idf if HVACTemplate present)
    subprocess.run([str(EXPAND_EXE)], cwd=str(outdir),
                   capture_output=True, text=True, timeout=300)
    run_idf = outdir / "expanded.idf"
    if not run_idf.exists():
        run_idf = outdir / "in.idf"

    proc = subprocess.run(
        [str(EP_EXE), "-w", str(EPW), "-d", str(outdir), str(run_idf)],
        cwd=str(outdir), capture_output=True, text=True, timeout=3600,
    )
    rc = proc.returncode
    (outdir / "task.rc").write_text(str(rc))

    status = "unknown"
    end_path = outdir / "eplusout.end"
    if end_path.exists():
        txt = end_path.read_text(errors="replace")
        status = "success" if "EnergyPlus Completed Successfully" in txt else "failed"
    else:
        status = f"no-end(rc={rc})"
    return stem, status, rc


def main() -> None:
    if not EP_EXE.exists():
        sys.exit(f"FATAL: EnergyPlus not found at {EP_EXE}")
    if not EPW.exists():
        sys.exit(f"FATAL: EPW not found at {EPW}")
    idfs = sorted(IDF_DIR.glob("*.idf"))
    if not idfs:
        sys.exit(f"FATAL: no IDFs in {IDF_DIR}")
    print(f"Running {len(idfs)} fast_zone IDFs locally with EnergyPlus 23.1")
    print(f"  EP:  {EP_EXE}")
    print(f"  EPW: {EPW}")
    print(f"  OUT: {SIM_OUT}")

    SIM_OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    results = []
    # 4 parallel workers (desktop has cores to spare; each E+ run is ~10-30s)
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(run_one, str(p)): p.stem for p in idfs}
        for fut in as_completed(futs):
            stem, status, rc = fut.result()
            results.append((stem, status, rc))
            print(f"  [{status:18s}] {stem} (rc={rc})")

    elapsed = time.monotonic() - t0
    n_ok = sum(1 for _, s, _ in results if s == "success")
    print(f"\nDone: {n_ok}/{len(results)} success in {elapsed:.1f}s")
    failed = [(s, st, rc) for s, st, rc in results if st != "success"]
    if failed:
        print("FAILED:")
        for s, st, rc in failed:
            print(f"  {s}: {st} (rc={rc})")


if __name__ == "__main__":
    main()
