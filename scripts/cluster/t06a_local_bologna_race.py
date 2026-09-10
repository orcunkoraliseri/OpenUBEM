"""T06a local Bologna race — run the 139 Galvani II (IT-BOL-GALVANI2) buildings
locally on the Windows desktop, as an additive race against the Speed cluster
array job 1314067. Purely additive: writes only under a new local_out/ subdir,
never touches anything under scripts/cluster/*.sbatch or ssh/SLURM tooling.

Reads:
    openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_recut_2026-09-08/recut_simulate_list.csv
    openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_recut_2026-09-08/idfs/<stem>.idf
    openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_recut_2026-09-08/weather/it_bologna_2013_2014_y2014.epw

Writes:
    openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_recut_2026-09-08/local_out/<stem>/...
    openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_recut_2026-09-08/local_out/progress.log

Resumable: skip a building if local_out/<stem>/eplusout.end already exists.

Usage:
    py -3 scripts/cluster/t06a_local_bologna_race.py                 # full 139
    py -3 scripts/cluster/t06a_local_bologna_race.py --stems <stem>   # smoke test, one building
    py -3 scripts/cluster/t06a_local_bologna_race.py --n-workers 20
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent

DISTRICT_DIR = (
    REPO / "openubem" / "outputs" / "eu_evidence" / "EU-11" / "IT-BOL-GALVANI2_recut_2026-09-08"
)
IDF_DIR = DISTRICT_DIR / "idfs"
SIMULATE_LIST_CSV = DISTRICT_DIR / "recut_simulate_list.csv"
EPW_PATH = DISTRICT_DIR / "weather" / "it_bologna_2013_2014_y2014.epw"
LOCAL_OUT_DIR = DISTRICT_DIR / "local_out"
PROGRESS_LOG = LOCAL_OUT_DIR / "progress.log"

EP_DIR = Path(r"C:\EnergyPlusV23-1-0")
EP_EXE = EP_DIR / "energyplus.exe"
EP_IDD = EP_DIR / "Energy+.idd"

N_WORKERS_DEFAULT = 20


def load_stems() -> list[str]:
    df = pd.read_csv(SIMULATE_LIST_CSV)
    return [str(s) for s in df["stem"].tolist()]


def is_done(stem: str) -> bool:
    return (LOCAL_OUT_DIR / stem / "eplusout.end").exists()


def _append_progress(stem: str, status: str, elapsed_s: float) -> None:
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    line = f"{ts}\t{stem}\t{status}\t{elapsed_s:.1f}\n"
    LOCAL_OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def _run_one_ep(args: tuple[str, str, str, str]) -> tuple[str, str, int, float]:
    idf_path_str, outdir_str, ep_exe_str, epw_str = args
    idf_path = Path(idf_path_str)
    outdir = Path(outdir_str)
    outdir.mkdir(parents=True, exist_ok=True)

    t0 = time.monotonic()

    ep_idd = Path(ep_exe_str).parent / "Energy+.idd"
    shutil.copy(str(ep_idd), str(outdir / "Energy+.idd"))
    shutil.copy(str(idf_path), str(outdir / "in.idf"))

    expand_exe = Path(ep_exe_str).parent / "ExpandObjects.exe"
    subprocess.run(
        [str(expand_exe)], cwd=str(outdir), capture_output=True, text=True, timeout=300
    )
    run_idf = outdir / "expanded.idf"
    if not run_idf.exists():
        run_idf = outdir / "in.idf"

    proc = subprocess.run(
        [ep_exe_str, "-w", epw_str, "-d", str(outdir), str(run_idf)],
        cwd=str(outdir), capture_output=True, text=True, timeout=7200,
    )
    rc = proc.returncode
    (outdir / "task.rc").write_text(str(rc))

    end_path = outdir / "eplusout.end"
    if end_path.exists():
        txt = end_path.read_text(errors="replace")
        status = "COMPLETED" if "EnergyPlus Completed Successfully" in txt else "FAILED"
    else:
        status = f"FAILED(no-end,rc={rc})"

    elapsed = time.monotonic() - t0
    return idf_path.stem, status, rc, elapsed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stems", nargs="*", default=None,
                     help="Run only these stems (smoke test). Default: all 139 from the CSV.")
    ap.add_argument("--n-workers", type=int, default=N_WORKERS_DEFAULT)
    args = ap.parse_args()

    if not EP_EXE.exists():
        sys.exit(f"FATAL: EnergyPlus not found at {EP_EXE}")
    if not EP_IDD.exists():
        sys.exit(f"FATAL: Energy+.idd not found at {EP_IDD}")
    if not EPW_PATH.exists():
        sys.exit(f"FATAL: EPW not found at {EPW_PATH}")
    if not SIMULATE_LIST_CSV.exists():
        sys.exit(f"FATAL: task list not found at {SIMULATE_LIST_CSV}")

    all_stems = load_stems()
    stems = args.stems if args.stems else all_stems

    missing_idf = [s for s in stems if not (IDF_DIR / f"{s}.idf").exists()]
    if missing_idf:
        sys.exit(f"FATAL: missing IDF(s) for stems: {missing_idf[:5]} ...")

    pending = [s for s in stems if not is_done(s)]
    already_done = len(stems) - len(pending)
    print(f"[t06a] {len(stems)} requested, {already_done} already done, {len(pending)} pending "
          f"(n_workers={args.n_workers})")

    if not pending:
        print("[t06a] nothing to do")
        return

    LOCAL_OUT_DIR.mkdir(parents=True, exist_ok=True)

    args_list = [
        (str(IDF_DIR / f"{s}.idf"), str(LOCAL_OUT_DIR / s), str(EP_EXE), str(EPW_PATH))
        for s in pending
    ]

    n_workers = min(args.n_workers, len(args_list))
    t0 = time.monotonic()
    n_ok = 0
    n_fail = 0

    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        futs = {}
        pending_iter = iter(args_list)
        for _ in range(n_workers):
            a = next(pending_iter, None)
            if a is None:
                break
            futs[ex.submit(_run_one_ep, a)] = a[0]

        while futs:
            done, _ = wait(list(futs.keys()), return_when=FIRST_COMPLETED)
            for fut in done:
                futs.pop(fut)
                stem, status, rc, elapsed = fut.result()
                _append_progress(stem, status, elapsed)
                if status == "COMPLETED":
                    n_ok += 1
                else:
                    n_fail += 1
                print(f"  [{stem}] {status} rc={rc} elapsed={elapsed:.1f}s")

                a = next(pending_iter, None)
                if a is not None:
                    futs[ex.submit(_run_one_ep, a)] = a[0]

    elapsed_total = time.monotonic() - t0
    print(f"[t06a] done: {n_ok} ok, {n_fail} failed, {already_done} prior, "
          f"{elapsed_total:.1f}s total")


if __name__ == "__main__":
    main()
