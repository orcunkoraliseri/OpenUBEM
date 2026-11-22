import csv
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from openubem.gpusim.backends.numpy_ref import run_stage_a_batch
from openubem.gpusim.compile import compile_expidf_batch
from openubem.gpusim.weather import load_epw_weather

REPO_ROOT = Path(__file__).resolve().parents[2]
REP2_DIR = REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2"
SCHED_DIR = REP2_DIR / "schedules"
OUT_CSV = REPO_ROOT / "openubem/outputs/gpusim_m1_fleet.csv"

EPW_SEARCH_DIRS: tuple[Path, ...] = (
    REPO_ROOT / "openubem/data/weather",
    REP2_DIR / "weather",
    REPO_ROOT / "tests/fixtures/gpusim/golden/weather",
    REPO_ROOT / "data/weather",
)


def resolve_epw_path(epw_file_name: str) -> Path:
    """Resolve an EPW filename across known repository weather folders.

    Args:
        epw_file_name: Basename of the EPW file.

    Returns:
        Resolved path to the EPW file.
    """
    for directory in EPW_SEARCH_DIRS:
        candidate = directory / epw_file_name
        if candidate.is_file():
            return candidate
    for found in REPO_ROOT.rglob(epw_file_name):
        if found.is_file():
            return found
    raise FileNotFoundError(f"EPW file not found: {epw_file_name}")


def parse_eio_warmup_days(eio_path: Path) -> int:
    """Parse ``Environment:WarmupDays`` from ``eplusout.eio``.

    Args:
        eio_path: Path to EnergyPlus ``eplusout.eio``.

    Returns:
        Warm-up day count, or -1 if absent.
    """
    if not eio_path.is_file():
        return -1
    for line in eio_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("Environment:WarmupDays,"):
            return int(line.split(",")[1].strip())
    return -1


def load_eplusout_hourly_heating(csv_path: Path) -> np.ndarray:
    """Read 8760 hourly Ideal Loads Total Heating Energy [J] from ``eplusout.csv``.

    Args:
        csv_path: Path to EnergyPlus ``eplusout.csv``.

    Returns:
        1D float64 array of length 8760 in Joules.
    """
    with csv_path.open("r", encoding="utf-8", errors="replace") as fh:
        reader = csv.reader(fh)
        header = [col.strip() for col in next(reader)]
        col_idx = -1
        for idx, col in enumerate(header):
            if "Zone Ideal Loads Zone Total Heating Energy [J](Hourly)" in col:
                col_idx = idx
                break
        if col_idx < 0:
            raise ValueError(f"Heating column not found in {csv_path}")
        vals = [float(row[col_idx].strip()) for row in reader if len(row) > col_idx]
    arr = np.asarray(vals, dtype=np.float64)
    if arr.shape != (8760,):
        raise ValueError(f"Expected 8760 hourly rows in {csv_path}, got {arr.shape}")
    return arr


def load_completed_fleet_by_site() -> dict[str, list[dict[str, object]]]:
    """Discover all completed rep2 cells and group them by EPW filename.

    Returns:
        Mapping from EPW filename to sorted list of cell metadata dicts.
    """
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for manifest_path in sorted((REP2_DIR / "manifests").glob("*.json")):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not data.get("completed"):
            continue
        cell_id = str(data["cell_id"])
        cell_dir = REP2_DIR / cell_id
        expidf = cell_dir / "eplusout.expidf"
        csv_path = cell_dir / "eplusout.csv"
        if not expidf.is_file() or not csv_path.is_file():
            raise FileNotFoundError(f"Missing outputs for completed cell {cell_id}")
        raw_epw = str(data["epw_path"]).replace("\\", "/")
        epw_name = Path(raw_epw).name
        grouped[epw_name].append(
            {
                "cell_id": cell_id,
                "expidf_path": expidf,
                "csv_path": csv_path,
                "eio_path": cell_dir / "eplusout.eio",
                "manifest_heating_kwh": float(data["heating_kwh"]),
            }
        )
    return dict(sorted(grouped.items()))


def run_fleet() -> list[dict[str, object]]:
    """Run Stage A across all 346 completed fleet cells batched by EPW site.

    Returns:
        List of per-cell result rows written to ``gpusim_m1_fleet.csv``.
    """
    grouped = load_completed_fleet_by_site()
    all_rows: list[dict[str, object]] = []

    for epw_name, entries in grouped.items():
        weather = load_epw_weather(resolve_epw_path(epw_name), steps_per_hour=12)
        expidf_paths = [Path(e["expidf_path"]) for e in entries]
        cell_ids = [str(e["cell_id"]) for e in entries]
        batch = compile_expidf_batch(
            expidf_paths,
            cell_ids=cell_ids,
            epw_ids=[epw_name] * len(cell_ids),
            schedule_dirs=[SCHED_DIR],
        )

        t0 = time.perf_counter()
        res = run_stage_a_batch(batch, weather, record_zone_temp=False)
        wall_s = time.perf_counter() - t0
        print(
            f"Site {epw_name}: B={len(entries)}, wall={wall_s:.2f} s, "
            f"throughput={len(entries) / wall_s:.3f} bldg-yr/s"
        )

        for bi, entry in enumerate(entries):
            cid = str(entry["cell_id"])
            ann_ep = float(entry["manifest_heating_kwh"])
            ann_sa = float(res.annual_heating_kwh[bi])
            floor_area = float(batch.zone_floor_area[bi])
            rel_diff = (ann_sa - ann_ep) / ann_ep
            abs_kwh_m2 = abs(ann_sa - ann_ep) / floor_area

            h_ep = load_eplusout_hourly_heating(Path(entry["csv_path"]))
            h_sa = res.hourly_heating_j[bi]
            thr_j = 1.0 * floor_area * 3600.0
            active = (h_ep > thr_j) | (h_sa > thr_j)
            diff_h = h_sa[active] - h_ep[active]
            mean_ep = float(np.mean(h_ep[active]))
            cv_rmse = float(np.sqrt(np.mean(diff_h * diff_h)) / mean_ep)
            nmbe = float(np.mean(diff_h) / mean_ep)

            wu_ep = parse_eio_warmup_days(Path(entry["eio_path"]))
            wu_sa = int(res.warmup_days[bi])

            all_rows.append(
                {
                    "cell": cid,
                    "site": epw_name,
                    "floor_area_m2": floor_area,
                    "annual_eplus_kwh": ann_ep,
                    "annual_stage_a_kwh": ann_sa,
                    "rel_diff": rel_diff,
                    "abs_kwh_m2": abs_kwh_m2,
                    "cv_rmse": cv_rmse,
                    "nmbe": nmbe,
                    "warmup_days_eplus": wu_ep,
                    "warmup_days_stage_a": wu_sa,
                    "wall_seconds": wall_s,
                }
            )

    all_rows.sort(key=lambda r: str(r["cell"]))
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "cell",
        "annual_eplus_kwh",
        "annual_stage_a_kwh",
        "rel_diff",
        "cv_rmse",
        "nmbe",
        "warmup_days_eplus",
        "warmup_days_stage_a",
        "wall_seconds",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(
                {
                    "cell": row["cell"],
                    "annual_eplus_kwh": f"{float(row['annual_eplus_kwh']):.6f}",
                    "annual_stage_a_kwh": f"{float(row['annual_stage_a_kwh']):.6f}",
                    "rel_diff": f"{float(row['rel_diff']):.8e}",
                    "cv_rmse": f"{float(row['cv_rmse']):.8e}",
                    "nmbe": f"{float(row['nmbe']):.8e}",
                    "warmup_days_eplus": int(row["warmup_days_eplus"]),
                    "warmup_days_stage_a": int(row["warmup_days_stage_a"]),
                    "wall_seconds": f"{float(row['wall_seconds']):.3f}",
                }
            )

    rel_signed = np.array([float(r["rel_diff"]) for r in all_rows], dtype=np.float64)
    rel_abs = np.abs(rel_signed)
    abs_m2 = np.array([float(r["abs_kwh_m2"]) for r in all_rows], dtype=np.float64)
    cv_arr = np.array([float(r["cv_rmse"]) for r in all_rows], dtype=np.float64)
    nmbe_abs = np.abs(np.array([float(r["nmbe"]) for r in all_rows], dtype=np.float64))

    fail_med = int(np.sum((rel_abs > 0.0005) & (abs_m2 > 0.02)))
    fail_p99 = int(np.sum(rel_abs > 0.002))
    fail_worst = int(np.sum((rel_abs > 0.005) & (abs_m2 > 0.05)))
    fail_cv = int(np.sum(cv_arr > 0.01))
    fail_nmbe = int(np.sum(nmbe_abs > 0.001))

    print(f"\nFleet summary (N={len(all_rows)}):")
    print(f"  signed median rel_diff: {float(np.median(rel_signed)) * 100:+.4f}%")
    print(
        f"  |rel_diff| median={float(np.median(rel_abs)) * 100:.4f}%, "
        f"p99={float(np.percentile(rel_abs, 99)) * 100:.4f}%, "
        f"worst={float(np.max(rel_abs)) * 100:.4f}%"
    )
    print(
        f"  CV(RMSE) median={float(np.median(cv_arr)) * 100:.4f}%, "
        f"p99={float(np.percentile(cv_arr, 99)) * 100:.4f}%, "
        f"worst={float(np.max(cv_arr)) * 100:.4f}%"
    )
    print(
        f"  |NMBE|   median={float(np.median(nmbe_abs)) * 100:.4f}%, "
        f"p99={float(np.percentile(nmbe_abs, 99)) * 100:.4f}%, "
        f"worst={float(np.max(nmbe_abs)) * 100:.4f}%"
    )
    print(
        f"  Threshold exceedances (vs Windows M4 gates): "
        f"median_thr={fail_med}, p99_thr={fail_p99}, worst_thr={fail_worst}, "
        f"cv_thr={fail_cv}, nmbe_thr={fail_nmbe}"
    )

    worst_order = sorted(
        all_rows,
        key=lambda r: abs(float(r["rel_diff"])),
        reverse=True,
    )
    print("  5 worst cells by |rel_diff|:")
    for r in worst_order[:5]:
        print(
            f"    {r['cell']}: rel={float(r['rel_diff']) * 100:+.4f}%, "
            f"abs={float(r['abs_kwh_m2']):.4f} kWh/m2, "
            f"cv={float(r['cv_rmse']) * 100:.4f}%, "
            f"nmbe={float(r['nmbe']) * 100:+.4f}%"
        )
    print(f"Wrote {OUT_CSV}")
    return all_rows


if __name__ == "__main__":
    run_fleet()
