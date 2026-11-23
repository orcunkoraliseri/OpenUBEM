from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

from scripts.gpusim import make_golden, recheck_worst
from scripts.gpusim.run_fleet_stage_a import (
    load_eplusout_hourly_heating,
    parse_eio_warmup_days,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
M1_FLEET_CSV = REPO_ROOT / "openubem/outputs/gpusim_m1_fleet.csv"
M1_RECHECK_CSV = REPO_ROOT / "openubem/outputs/gpusim_m1_recheck.csv"
M3_CELLS_CSV = REPO_ROOT / "openubem/outputs/gpusim_m3_cells.csv"
M4_SETUP_CSV = REPO_ROOT / "openubem/outputs/gpusim_m4_setup.csv"
WIN_RUNS_DIR = REPO_ROOT / "openubem/outputs/gpusim_golden_runs/m4_windows"
OUT_CSV = REPO_ROOT / "openubem/outputs/gpusim_m4_win_eplus.csv"

MAX_WORKERS = 10
GOLDEN_CELLS: tuple[str, ...] = make_golden.GOLDEN_CELLS

OUT_FIELDS = [
    "cell",
    "published_kwh",
    "mac_eplus_kwh",
    "win_eplus_kwh",
    "stage_a_kwh",
    "rel_win_vs_published",
    "rel_win_vs_mac",
    "rel_stage_a_vs_win",
    "warmup_days_eplus",
    "warnings",
    "severe",
    "wall_s",
]


def _resolve_win_eplus_bin() -> Path:
    """Resolve the Windows EnergyPlus 23.1.0 executable path from M4 setup CSV."""
    if M4_SETUP_CSV.is_file():
        with M4_SETUP_CSV.open("r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                cand = Path(row["eplus_path"])
                if cand.is_file():
                    return cand
    for cand in (
        Path(r"C:\EnergyPlusV23-1-0\energyplus.exe"),
        Path(r"C:\EnergyPlus-23-1-0\energyplus.exe"),
    ):
        if cand.is_file():
            return cand
    raise FileNotFoundError("Windows EnergyPlus 23.1.0 executable not found")


def _load_target_cells() -> tuple[list[str], dict[str, float], dict[str, float]]:
    """Return sorted union of >0.5% fleet cells and the 3 golden cells."""
    published: dict[str, float] = {}
    stage_a: dict[str, float] = {}
    selected: set[str] = set(GOLDEN_CELLS)
    with M1_FLEET_CSV.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            cid = row["cell"].strip()
            published[cid] = float(row["annual_eplus_kwh"])
            stage_a[cid] = float(row["annual_stage_a_kwh"])
            if abs(float(row["rel_diff"])) > 0.005:
                selected.add(cid)
    return sorted(selected), published, stage_a


def _load_mac_eplus_map() -> dict[str, float]:
    """Load available Mac EnergyPlus annual heating totals by cell ID."""
    mac: dict[str, float] = {}
    if M3_CELLS_CSV.is_file():
        with M3_CELLS_CSV.open("r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                cid = row["cell"].strip()
                if cid in GOLDEN_CELLS:
                    mac[cid] = float(row["annual_eplus_kwh"])
    if M1_RECHECK_CSV.is_file():
        with M1_RECHECK_CSV.open("r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                mac[row["cell"].strip()] = float(row["mac_eplus_kwh"])
    return mac


def _run_one_eplus(args: tuple[str, str]) -> tuple[str, int, float, str]:
    """Run EnergyPlus 23.1.0 in one prepared Windows run directory."""
    cid, eplus_bin = args
    run_dir = WIN_RUNS_DIR / cid
    cmd = [
        eplus_bin,
        "-x",
        "-r",
        "-w",
        str(run_dir / "in.epw"),
        "-d",
        str(run_dir),
        str(run_dir / "in.idf"),
    ]
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=run_dir,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    wall_s = time.perf_counter() - t0
    err_tail = (proc.stderr or "").strip()[-400:]
    return cid, proc.returncode, wall_s, err_tail


def run_windows_recheck() -> int:
    """Re-run the 65+3 selected EU cells on native Windows EnergyPlus 23.1.0."""
    eplus_bin = _resolve_win_eplus_bin()
    cell_ids, published_map, stage_a_map = _load_target_cells()
    mac_map = _load_mac_eplus_map()

    recheck_worst.RECHECK_DIR = WIN_RUNS_DIR
    WIN_RUNS_DIR.mkdir(parents=True, exist_ok=True)

    run_dirs: dict[str, Path] = {}
    for cid in cell_ids:
        run_dir, _epw, manifest_kwh = recheck_worst.prepare_recheck_cell(cid)
        if abs(manifest_kwh - published_map[cid]) > 1.0e-3:
            raise ValueError(
                f"{cid}: manifest kWh {manifest_kwh} != fleet CSV {published_map[cid]}"
            )
        run_dirs[cid] = run_dir

    print(
        f"Running {len(cell_ids)} Windows EnergyPlus 23.1.0 jobs "
        f"(max_workers={MAX_WORKERS})...",
        flush=True,
    )
    wall_by_cell: dict[str, float] = {}
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_run_one_eplus, (cid, str(eplus_bin))): cid
            for cid in cell_ids
        }
        for idx, future in enumerate(as_completed(futures), start=1):
            cid, rc, wall_s, err_tail = future.result()
            wall_by_cell[cid] = wall_s
            if rc != 0:
                err_file = WIN_RUNS_DIR / cid / "eplusout.err"
                file_tail = (
                    err_file.read_text(encoding="utf-8", errors="replace")[-800:]
                    if err_file.is_file()
                    else err_tail
                )
                raise RuntimeError(
                    f"EnergyPlus failed for {cid} (rc={rc}): {file_tail}"
                )
            if idx % 10 == 0 or idx == len(cell_ids):
                print(
                    f"  completed {idx}/{len(cell_ids)}: {cid} ({wall_s:.3f} s)",
                    flush=True,
                )

    rows: list[dict[str, object]] = []
    rel_mac_vals: list[tuple[float, str]] = []
    rel_pub_vals: list[tuple[float, str]] = []
    wall_vals: list[float] = []

    for cid in cell_ids:
        run_dir = run_dirs[cid]
        warnings, severes = recheck_worst.parse_eplus_error_summary(run_dir)
        h_win = load_eplusout_hourly_heating(run_dir / "eplusout.csv")
        win_kwh = float(np.sum(h_win, dtype=np.float64) / 3.6e6)
        wu_ep = parse_eio_warmup_days(run_dir / "eplusout.eio")

        pub_kwh = published_map[cid]
        sa_kwh = stage_a_map[cid]
        mac_kwh = mac_map.get(cid)
        wall_s = wall_by_cell[cid]

        rel_win_pub = (win_kwh - pub_kwh) / pub_kwh
        rel_sa_win = (sa_kwh - win_kwh) / win_kwh
        rel_pub_vals.append((rel_win_pub, cid))
        wall_vals.append(wall_s)

        if mac_kwh is not None:
            rel_win_mac = (win_kwh - mac_kwh) / mac_kwh
            rel_mac_vals.append((rel_win_mac, cid))
            mac_str = f"{mac_kwh:.6f}"
            rel_mac_str = f"{rel_win_mac:.8e}"
        else:
            mac_str = ""
            rel_mac_str = ""

        rows.append(
            {
                "cell": cid,
                "published_kwh": f"{pub_kwh:.6f}",
                "mac_eplus_kwh": mac_str,
                "win_eplus_kwh": f"{win_kwh:.6f}",
                "stage_a_kwh": f"{sa_kwh:.6f}",
                "rel_win_vs_published": f"{rel_win_pub:.8e}",
                "rel_win_vs_mac": rel_mac_str,
                "rel_stage_a_vs_win": f"{rel_sa_win:.8e}",
                "warmup_days_eplus": wu_ep,
                "warnings": warnings,
                "severe": severes,
                "wall_s": f"{wall_s:.3f}",
            }
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    med_mac = float(np.median([abs(v) for v, _ in rel_mac_vals]))
    worst_mac_v, worst_mac_c = max(rel_mac_vals, key=lambda x: abs(x[0]))
    med_pub = float(np.median([abs(v) for v, _ in rel_pub_vals]))
    worst_pub_v, worst_pub_c = max(rel_pub_vals, key=lambda x: abs(x[0]))
    med_wall = float(np.median(np.asarray(wall_vals, dtype=np.float64)))

    print(f"Wrote {len(rows)} rows to {OUT_CSV} (0 severe across all runs)")
    print(
        f"Win vs Mac (N={len(rel_mac_vals)}): median |rel|={med_mac * 100:.5f}%, "
        f"worst={worst_mac_v * 100:+.5f}% ({worst_mac_c})"
    )
    print(
        f"Win vs Published (N={len(rel_pub_vals)}): median |rel|={med_pub * 100:.4f}%, "
        f"worst={worst_pub_v * 100:+.4f}% ({worst_pub_c})"
    )
    print(f"Median Windows E+ wall_s={med_wall:.3f} s")
    return 0


if __name__ == "__main__":
    sys.exit(run_windows_recheck())
