from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

import numpy as np

from openubem.gpusim.backends.numpy_ref import run_stage_a_batch
from openubem.gpusim.compile import compile_expidf_batch
from openubem.gpusim.weather import load_epw_weather
from scripts.gpusim.make_golden import (
    ENERGYPLUS_BIN,
    GOLDEN_RUNS_DIR,
    MAX_WORKERS,
    REP2_DIR,
    SEVERE_OR_FATAL_RE,
    map_windows_path,
    rewrite_schedule_paths_to_basename,
)
from scripts.gpusim.run_fleet_stage_a import (
    load_eplusout_hourly_heating,
    parse_eio_warmup_days,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FLEET_CSV = REPO_ROOT / "openubem/outputs/gpusim_m1_fleet.csv"
RECHECK_DIR = GOLDEN_RUNS_DIR / "recheck"
OUT_CSV = REPO_ROOT / "openubem/outputs/gpusim_m1_recheck.csv"
TOP_N = 5

COMPLETED_SUMMARY_RE = re.compile(
    r"EnergyPlus Completed Successfully--\s*(\d+)\s+Warning;\s*(\d+)\s+Severe Errors",
    re.IGNORECASE,
)


def select_worst_cells(
    fleet_csv: Path, count: int = TOP_N
) -> list[tuple[str, float, float]]:
    """Select the cells with the largest absolute relative difference in fleet CSV.

    Args:
        fleet_csv: Path to ``gpusim_m1_fleet.csv``.
        count: Number of worst cells to return.

    Returns:
        List of ``(cell_id, published_kwh, fleet_rel_diff)`` sorted descending by
        ``abs(fleet_rel_diff)``.

    Raises:
        FileNotFoundError: If ``fleet_csv`` does not exist.
        ValueError: If fewer than ``count`` rows exist.
    """
    if not fleet_csv.is_file():
        raise FileNotFoundError(f"Missing fleet CSV: {fleet_csv}")
    entries: list[tuple[str, float, float]] = []
    with fleet_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            entries.append(
                (
                    row["cell"].strip(),
                    float(row["annual_eplus_kwh"]),
                    float(row["rel_diff"]),
                )
            )
    if len(entries) < count:
        raise ValueError(f"Expected at least {count} rows in {fleet_csv}")
    entries.sort(key=lambda item: abs(item[2]), reverse=True)
    return entries[:count]


def prepare_recheck_cell(cell_id: str) -> tuple[Path, Path, float]:
    """Prepare one recheck run directory without modifying IDF outputs.

    Args:
        cell_id: Completed rep2 cell identifier.

    Returns:
        Tuple of ``(run_dir, epw_src_path, manifest_heating_kwh)``.

    Raises:
        FileNotFoundError: If manifest, IDF, EPW, or schedule file is missing.
    """
    manifest_path = REP2_DIR / "manifests" / f"{cell_id}.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    epw_src = map_windows_path(manifest["epw_path"])
    idf_src = REP2_DIR / "idfs" / f"{cell_id}.idf"
    sched_src = REP2_DIR / "schedules" / f"{cell_id}.csv"

    for path in (idf_src, epw_src, sched_src):
        if not path.is_file():
            raise FileNotFoundError(f"Missing required input: {path}")

    run_dir = RECHECK_DIR / cell_id
    run_dir.mkdir(parents=True, exist_ok=True)
    keep_names = {"in.idf", "in.epw", sched_src.name}
    for item in run_dir.iterdir():
        if item.name not in keep_names:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    shutil.copy2(epw_src, run_dir / "in.epw")
    shutil.copy2(sched_src, run_dir / sched_src.name)

    raw_idf = idf_src.read_text(encoding="utf-8")
    idf_text = rewrite_schedule_paths_to_basename(raw_idf)
    (run_dir / "in.idf").write_text(idf_text, encoding="utf-8")
    return run_dir, epw_src, float(manifest["heating_kwh"])


def _run_eplus_cell(cell_id: str) -> tuple[str, int, float, str]:
    """Execute EnergyPlus 23.1.0 for one prepared recheck directory.

    Args:
        cell_id: Recheck cell identifier under ``RECHECK_DIR``.

    Returns:
        Tuple of ``(cell_id, returncode, wall_seconds, stderr_tail)``.
    """
    run_dir = RECHECK_DIR / cell_id
    cmd = [
        str(ENERGYPLUS_BIN),
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
    return cell_id, proc.returncode, wall_s, err_tail


def parse_eplus_error_summary(run_dir: Path) -> tuple[int, int]:
    """Validate EnergyPlus completion and extract warning and severe error counts.

    Args:
        run_dir: Completed EnergyPlus run directory.

    Returns:
        Tuple of ``(warning_count, severe_count)``.

    Raises:
        FileNotFoundError: If required EnergyPlus outputs are missing.
        RuntimeError: If EnergyPlus failed or reported any severe/fatal error.
    """
    for name in (
        "eplusout.end",
        "eplusout.err",
        "eplusout.eio",
        "eplusout.expidf",
        "eplusout.csv",
    ):
        if not (run_dir / name).is_file():
            raise FileNotFoundError(f"Missing EnergyPlus output {run_dir / name}")

    end_text = (run_dir / "eplusout.end").read_text(encoding="utf-8", errors="replace")
    if "EnergyPlus Completed Successfully" not in end_text:
        raise RuntimeError(
            f"{run_dir.name}: eplusout.end missing completion marker: "
            f"{end_text.strip()!r}"
        )

    err_text = (run_dir / "eplusout.err").read_text(encoding="utf-8", errors="replace")
    if SEVERE_OR_FATAL_RE.search(err_text):
        raise RuntimeError(f"{run_dir.name}: eplusout.err contains Severe/Fatal error")

    match = COMPLETED_SUMMARY_RE.search(err_text)
    if match is None:
        raise RuntimeError(
            f"{run_dir.name}: eplusout.err missing final completion summary line"
        )
    warnings = int(match.group(1))
    severes = int(match.group(2))
    if severes != 0:
        raise RuntimeError(f"{run_dir.name}: eplusout.err reported {severes} severe")
    return warnings, severes


def run_recheck() -> int:
    """Re-run the 5 worst fleet cells on Mac EnergyPlus and compare with Stage A.

    Returns:
        0 if every cell passes all parity tier P1 gates, 1 otherwise.
    """
    if not ENERGYPLUS_BIN.is_file():
        raise FileNotFoundError(f"Missing EnergyPlus binary: {ENERGYPLUS_BIN}")

    worst = select_worst_cells(FLEET_CSV, count=TOP_N)
    cell_ids = [item[0] for item in worst]
    published_by_cell: dict[str, float] = {}
    epw_by_cell: dict[str, Path] = {}
    run_dir_by_cell: dict[str, Path] = {}

    print("Selected 5 worst cells from fleet CSV:")
    for cell_id, fleet_pub_kwh, fleet_rel in worst:
        run_dir, epw_src, manifest_kwh = prepare_recheck_cell(cell_id)
        if abs(manifest_kwh - fleet_pub_kwh) > 1e-3:
            raise ValueError(
                f"{cell_id}: manifest kWh {manifest_kwh} != fleet CSV {fleet_pub_kwh}"
            )
        published_by_cell[cell_id] = manifest_kwh
        epw_by_cell[cell_id] = epw_src
        run_dir_by_cell[cell_id] = run_dir
        print(f"  {cell_id}: fleet_rel={fleet_rel * 100.0:+.4f}%, epw={epw_src.name}")

    print(
        f"Running {len(cell_ids)} Mac EnergyPlus jobs (max_workers={MAX_WORKERS})..."
    )
    eplus_wall_by_cell: dict[str, float] = {}
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_run_eplus_cell, cid): cid for cid in cell_ids
        }
        for future in as_completed(futures):
            cid, rc, wall_s, err_tail = future.result()
            eplus_wall_by_cell[cid] = wall_s
            print(f"  [{rc}] {cid}: {wall_s:.3f} s", flush=True)
            if rc != 0:
                raise RuntimeError(
                    f"EnergyPlus failed for {cid} (rc={rc}): {err_tail}"
                )

    warnings_by_cell: dict[str, int] = {}
    severes_by_cell: dict[str, int] = {}
    for cid in cell_ids:
        warn_cnt, sev_cnt = parse_eplus_error_summary(run_dir_by_cell[cid])
        warnings_by_cell[cid] = warn_cnt
        severes_by_cell[cid] = sev_cnt

    expidf_paths = [run_dir_by_cell[cid] / "eplusout.expidf" for cid in cell_ids]
    epw_names = [epw_by_cell[cid].name for cid in cell_ids]
    batch = compile_expidf_batch(
        expidf_paths,
        cell_ids=cell_ids,
        epw_ids=epw_names,
    )
    weather_cache: dict[Path, object] = {}
    weather_list = []
    for cid in cell_ids:
        epw_file = run_dir_by_cell[cid] / "in.epw"
        src_key = epw_by_cell[cid]
        if src_key not in weather_cache:
            weather_cache[src_key] = load_epw_weather(
                epw_file, steps_per_hour=batch.steps_per_hour
            )
        weather_list.append(weather_cache[src_key])

    t0_sa = time.perf_counter()
    sa_res = run_stage_a_batch(batch, weather_list, record_zone_temp=False)
    sa_wall_s = time.perf_counter() - t0_sa
    print(f"Stage A batch (B={len(cell_ids)}) finished in {sa_wall_s:.3f} s")

    rows: list[dict[str, object]] = []
    gate_failures: list[str] = []

    for bi, cid in enumerate(cell_ids):
        run_dir = run_dir_by_cell[cid]
        pub_kwh = published_by_cell[cid]
        h_mac = load_eplusout_hourly_heating(run_dir / "eplusout.csv")
        mac_kwh = float(np.sum(h_mac, dtype=np.float64) / 3.6e6)
        h_sa = sa_res.hourly_heating_j[bi]
        sa_kwh = float(sa_res.annual_heating_kwh[bi])
        floor_area = float(batch.zone_floor_area[bi])

        rel_mac_pub = (mac_kwh - pub_kwh) / pub_kwh
        rel_sa_mac = (sa_kwh - mac_kwh) / mac_kwh
        abs_sa_mac_kwh_m2 = abs(sa_kwh - mac_kwh) / floor_area

        thr_j = 1.0 * floor_area * 3600.0
        active = (h_mac > thr_j) | (h_sa > thr_j)
        diff_h = h_sa[active] - h_mac[active]
        mean_mac = float(np.mean(h_mac[active]))
        cv_rmse = float(np.sqrt(np.mean(diff_h * diff_h)) / mean_mac)
        nmbe = float(np.mean(diff_h) / mean_mac)

        wu_ep = parse_eio_warmup_days(run_dir / "eplusout.eio")
        wu_sa = int(sa_res.warmup_days[bi])

        rows.append(
            {
                "cell": cid,
                "published_kwh": f"{pub_kwh:.6f}",
                "mac_eplus_kwh": f"{mac_kwh:.6f}",
                "stage_a_kwh": f"{sa_kwh:.6f}",
                "rel_mac_vs_published": f"{rel_mac_pub:.8e}",
                "rel_stage_a_vs_mac": f"{rel_sa_mac:.8e}",
                "cv_rmse": f"{cv_rmse:.8e}",
                "nmbe": f"{nmbe:.8e}",
                "warmup_days_eplus": wu_ep,
                "warmup_days_stage_a": wu_sa,
                "eplus_wall_seconds": f"{eplus_wall_by_cell[cid]:.3f}",
            }
        )

        ann_ok = (abs(rel_sa_mac) <= 0.005) or (abs_sa_mac_kwh_m2 <= 0.05)
        cv_ok = cv_rmse <= 0.01
        nmbe_ok = abs(nmbe) <= 0.001
        wu_ok = wu_sa == wu_ep
        if not (ann_ok and cv_ok and nmbe_ok and wu_ok):
            hourly_diff = h_sa - h_mac
            rel_hr = np.abs(hourly_diff) / np.maximum(np.abs(h_mac), thr_j)
            bad_hours = np.flatnonzero(rel_hr > 0.01)
            first_hr = (
                int(bad_hours[0])
                if bad_hours.size > 0
                else int(np.argmax(np.abs(hourly_diff)))
            )
            gate_failures.append(
                f"{cid}: rel_sa_mac={rel_sa_mac * 100.0:+.4f}% "
                f"({abs_sa_mac_kwh_m2:.4f} kWh/m2), cv_rmse={cv_rmse * 100.0:.4f}%, "
                f"nmbe={nmbe * 100.0:+.4f}%, wu={wu_ep}/{wu_sa}; "
                f"first diverging hour={first_hr + 1} "
                f"(Zone Ideal Loads Zone Total Heating Energy [J](Hourly): "
                f"mac={h_mac[first_hr]:.2f} J, sa={h_sa[first_hr]:.2f} J, "
                f"diff={hourly_diff[first_hr]:+.2f} J)"
            )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "cell",
        "published_kwh",
        "mac_eplus_kwh",
        "stage_a_kwh",
        "rel_mac_vs_published",
        "rel_stage_a_vs_mac",
        "cv_rmse",
        "nmbe",
        "warmup_days_eplus",
        "warmup_days_stage_a",
        "eplus_wall_seconds",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {OUT_CSV}")
    print("\n=== EnergyPlus Error Summary ===")
    for cid in cell_ids:
        print(
            f"  {cid}: {warnings_by_cell[cid]} warnings, "
            f"{severes_by_cell[cid]} severe errors"
        )

    print("\n=== Recheck Summary ===")
    for row in rows:
        print(
            f"  {row['cell']}: pub={row['published_kwh']}, "
            f"mac={row['mac_eplus_kwh']}, sa={row['stage_a_kwh']}, "
            f"mac_vs_pub={float(row['rel_mac_vs_published']) * 100.0:+.4f}%, "
            f"sa_vs_mac={float(row['rel_stage_a_vs_mac']) * 100.0:+.5f}%, "
            f"cv={float(row['cv_rmse']) * 100.0:.5f}%, "
            f"nmbe={float(row['nmbe']) * 100.0:+.5f}%, "
            f"wu={row['warmup_days_eplus']}/{row['warmup_days_stage_a']}, "
            f"eplus_s={row['eplus_wall_seconds']}"
        )

    if gate_failures:
        print("\nGATE FAILURES:")
        for msg in gate_failures:
            print(f"  {msg}")
        return 1
    print("\nAll 5 recheck cells PASSED every P1 gate.")
    return 0


def main() -> int:
    """Entry point for the T07 worst-cell Mac EnergyPlus recheck script.

    Returns:
        Process exit status code.
    """
    return run_recheck()


if __name__ == "__main__":
    sys.exit(main())
