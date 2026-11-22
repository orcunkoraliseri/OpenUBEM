import csv
import time
from pathlib import Path

from openubem.gpusim.backends.numpy_ref import run_stage_a_batch
from openubem.gpusim.compile import compile_expidf_batch
from openubem.gpusim.weather import load_epw_weather
from scripts.gpusim.run_fleet_stage_a import (
    SCHED_DIR,
    load_completed_fleet_by_site,
    resolve_epw_path,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_CSV = REPO_ROOT / "openubem/outputs/gpusim_m1_bench.csv"


def run_benchmarks() -> list[dict[str, object]]:
    """Measure Stage A throughput for B = 1, 10, 100, and largest site.

    Returns:
        List of benchmark result rows written to ``gpusim_m1_bench.csv``.
    """
    grouped = load_completed_fleet_by_site()
    largest_site, entries = max(grouped.items(), key=lambda kv: len(kv[1]))
    weather = load_epw_weather(resolve_epw_path(largest_site), steps_per_hour=12)

    batch_sizes = [1, 10, 100, len(entries)]
    rows: list[dict[str, object]] = []

    for b_size in batch_sizes:
        subset = entries[:b_size]
        expidf_paths = [Path(e["expidf_path"]) for e in subset]
        cell_ids = [str(e["cell_id"]) for e in subset]
        batch = compile_expidf_batch(
            expidf_paths,
            cell_ids=cell_ids,
            epw_ids=[largest_site] * b_size,
            schedule_dirs=[SCHED_DIR],
        )

        t0 = time.perf_counter()
        run_stage_a_batch(batch, weather, record_zone_temp=False)
        wall_s = time.perf_counter() - t0
        throughput = float(b_size) / wall_s

        print(
            f"B={b_size:3d} ({largest_site}): wall={wall_s:.3f} s, "
            f"throughput={throughput:.4f} bldg-yr/s"
        )
        rows.append(
            {
                "batch_size": b_size,
                "site": largest_site,
                "wall_seconds": f"{wall_s:.3f}",
                "building_years_per_sec": f"{throughput:.6f}",
            }
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "batch_size",
                "site",
                "wall_seconds",
                "building_years_per_sec",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT_CSV}")
    return rows


if __name__ == "__main__":
    run_benchmarks()
