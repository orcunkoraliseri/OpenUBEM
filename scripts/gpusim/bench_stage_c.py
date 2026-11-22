import csv
import json
import sys
import time
from dataclasses import fields
from pathlib import Path

import numpy as np
import torch

from openubem.gpusim.backends.kernel.pack import PackedBatch, deduplicate_weather, pack
from openubem.gpusim.backends.kernel.s0_metal import (
    compile_metal_s0_shader,
    launch_s0_chunk_mps,
    upload_packed_to_mps,
)
from openubem.gpusim.backends.stage_c import run_packed_stage_c_mps
from openubem.gpusim.compile import BatchSpec, compile_expidf_batch
from openubem.gpusim.weather import WeatherSeries, load_epw_weather

REPO_ROOT = Path(__file__).resolve().parents[2]
REP2_DIR = REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2"
SCHED_DIR = REP2_DIR / "schedules"
M0_TIMING_CSV = REPO_ROOT / "openubem/outputs/gpusim_m0_timing.csv"
M1_BENCH_CSV = REPO_ROOT / "openubem/outputs/gpusim_m1_bench.csv"
OUT_CSV = REPO_ROOT / "openubem/outputs/gpusim_m3_bench.csv"

BATCH_SIZES: tuple[int, ...] = (1, 10, 100, 1000)
N_REPEATS: int = 3
PROBE_TARGET_S: float = 0.70

EPW_SEARCH_DIRS: tuple[Path, ...] = (
    REPO_ROOT / "openubem/data/weather",
    REP2_DIR / "weather",
    REPO_ROOT / "tests/fixtures/gpusim/golden/weather",
    REPO_ROOT / "data/weather",
)


def resolve_epw_path(epw_file_name: str) -> Path:
    """Resolve an EPW filename across repository weather directories.

    Args:
        epw_file_name: Basename of the EPW weather file.

    Returns:
        Resolved filesystem path to the EPW file.

    Raises:
        FileNotFoundError: If no matching EPW file exists in the repository.
    """
    for directory in EPW_SEARCH_DIRS:
        candidate = directory / epw_file_name
        if candidate.is_file():
            return candidate
    for found in REPO_ROOT.rglob(epw_file_name):
        if found.is_file():
            return found
    raise FileNotFoundError(f"EPW file not found: {epw_file_name}")


def load_completed_fleet_entries() -> list[dict[str, object]]:
    """Load the 346 completed fleet cell entries sorted by ``cell_id``.

    Returns:
        Sorted list of dicts containing ``cell_id``, ``expidf_path``, and
        ``epw_name``.

    Raises:
        FileNotFoundError: If a completed cell lacks ``eplusout.expidf``.
    """
    entries: list[dict[str, object]] = []
    for manifest_path in sorted((REP2_DIR / "manifests").glob("*.json")):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not data.get("completed"):
            continue
        cell_id = str(data["cell_id"])
        expidf_path = REP2_DIR / cell_id / "eplusout.expidf"
        if not expidf_path.is_file():
            raise FileNotFoundError(f"Missing expidf for cell {cell_id}")
        raw_epw = str(data["epw_path"]).replace("\\", "/")
        entries.append(
            {
                "cell_id": cell_id,
                "expidf_path": expidf_path,
                "epw_name": Path(raw_epw).name,
            }
        )
    entries.sort(key=lambda item: str(item["cell_id"]))
    return entries


def load_eplus_sizing_off_rate(csv_path: Path) -> tuple[float, float]:
    """Compute measured 1-process and computed 4-process E+ rates.

    Args:
        csv_path: Path to ``gpusim_m0_timing.csv``.

    Returns:
        Tuple ``(median_wall_s, rate_1proc_bldg_yr_per_s)``.
    """
    walls: list[float] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if str(row["variant"]) == "sizing_off":
                walls.append(float(row["wall_s"]))
    med_wall = float(np.median(np.asarray(walls, dtype=np.float64)))
    return med_wall, 1.0 / med_wall


def load_stage_a_bench_rates(csv_path: Path) -> dict[int, float]:
    """Load measured Stage A throughput rates by batch size.

    Args:
        csv_path: Path to ``gpusim_m1_bench.csv``.

    Returns:
        Mapping from Stage A benchmark batch size to ``building_years_per_sec``.
    """
    rates: dict[int, float] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            rates[int(row["batch_size"])] = float(row["building_years_per_sec"])
    return rates


def match_stage_a_rate(batch_size: int, rates: dict[int, float]) -> tuple[int, float]:
    """Select the matching or nearest Stage A benchmark batch size and rate.

    Args:
        batch_size: Stage C benchmark batch size.
        rates: Stage A rates keyed by benchmark batch size.

    Returns:
        Tuple ``(matched_stage_a_batch_size, stage_a_rate)``.
    """
    if batch_size in rates:
        return batch_size, rates[batch_size]
    nearest = min(rates.keys(), key=lambda b: (abs(b - batch_size), -b))
    return nearest, rates[nearest]


def tile_batch_spec(base: BatchSpec, target_b: int) -> BatchSpec:
    """Tile a compiled distinct-cell ``BatchSpec`` cyclically to ``target_b``.

    Args:
        base: Compiled ``BatchSpec`` covering distinct cells.
        target_b: Desired total batch size ``B``.

    Returns:
        New ``BatchSpec`` of size ``target_b`` with tiled arrays and lists.
    """
    if base.batch_size == target_b:
        return base
    n_base = base.batch_size
    idx = np.arange(target_b, dtype=np.int64) % n_base
    kwargs: dict[str, object] = {}
    for fld in fields(BatchSpec):
        name = fld.name
        val = getattr(base, name)
        if name == "batch_size":
            kwargs[name] = target_b
        elif name in ("max_surfaces", "steps_per_hour"):
            kwargs[name] = val
        elif name == "surf_names":
            kwargs[name] = [list(val[int(i)]) for i in idx]
        elif isinstance(val, list):
            kwargs[name] = [val[int(i)] for i in idx]
        elif isinstance(val, np.ndarray):
            kwargs[name] = np.ascontiguousarray(val[idx])
        else:
            kwargs[name] = val
    return BatchSpec(**kwargs)


def _probe_chunk_launch_s(packed: PackedBatch, chunk_days: int) -> float:
    """Measure one synthetic run-period chunk launch duration on MPS.

    Args:
        packed: Packed host batch for the target ``batch_size``.
        chunk_days: Number of days in the single test kernel launch.

    Returns:
        Synchronized single-launch wall time in seconds.
    """
    lib = compile_metal_s0_shader()
    bufs = upload_packed_to_mps(packed, record_zone_temp=False)
    steps_per_day = 24 * packed.steps_per_hour
    dt_zone_hr = 1.0 / float(packed.steps_per_hour)
    limit_num_sys = max(1, int(round(dt_zone_hr / (1.0 / 60.0))))
    step_end = min(chunk_days * steps_per_day, packed.n_run_steps)
    torch.mps.synchronize()
    t0 = time.perf_counter()
    launch_s0_chunk_mps(
        lib=lib,
        bufs=bufs,
        step_start=0,
        step_end=step_end,
        is_warmup=False,
        warmup_day=0,
        record_zone_temp=False,
        rec_step_offset=0,
        limit_num_sys=limit_num_sys,
    )
    torch.mps.synchronize()
    return time.perf_counter() - t0


def select_safe_chunk_days(packed: PackedBatch) -> int:
    """Choose the largest run chunk in ``1..7`` days staying under 1.0 s/launch.

    Args:
        packed: Representative packed batch at the target ``batch_size``.

    Returns:
        Selected ``run_chunk_days`` between 1 and 7 inclusive.
    """
    one_day_s = _probe_chunk_launch_s(packed, 1)
    if one_day_s >= PROBE_TARGET_S:
        return 1
    candidate = min(7, max(1, int(PROBE_TARGET_S / max(one_day_s, 1.0e-6))))
    while candidate > 1:
        probe_s = _probe_chunk_launch_s(packed, candidate)
        if probe_s <= PROBE_TARGET_S:
            return candidate
        candidate -= 1
    return 1


def run_benchmark() -> list[dict[str, object]]:
    """Run Stage C throughput benchmarks across ``BATCH_SIZES``.

    Returns:
        List of 4 benchmark summary rows written to ``gpusim_m3_bench.csv``.

    Raises:
        RuntimeError: If any launch exceeds the 1.0 s macOS watchdog ceiling.
    """
    entries = load_completed_fleet_entries()
    n_fleet = len(entries)
    eplus_med_wall_s, eplus_1proc_rate = load_eplus_sizing_off_rate(M0_TIMING_CSV)
    eplus_4proc_rate = 4.0 * eplus_1proc_rate
    stage_a_rates = load_stage_a_bench_rates(M1_BENCH_CSV)

    weather_cache: dict[str, WeatherSeries] = {}
    for entry in entries:
        epw_name = str(entry["epw_name"])
        if epw_name not in weather_cache:
            weather_cache[epw_name] = load_epw_weather(
                resolve_epw_path(epw_name),
                steps_per_hour=12,
            )

    _ = compile_metal_s0_shader()
    full_compile_cache: tuple[BatchSpec, float] | None = None
    rows: list[dict[str, object]] = []

    for b_size in BATCH_SIZES:
        n_distinct = min(b_size, n_fleet)
        distinct_entries = entries[:n_distinct]
        distinct_paths = [Path(e["expidf_path"]) for e in distinct_entries]
        distinct_ids = [str(e["cell_id"]) for e in distinct_entries]
        distinct_epws = [str(e["epw_name"]) for e in distinct_entries]

        t_comp0 = time.perf_counter()
        if b_size >= n_fleet and full_compile_cache is not None:
            base_batch, distinct_comp_s = full_compile_cache
        else:
            base_batch = compile_expidf_batch(
                distinct_paths,
                cell_ids=distinct_ids,
                epw_ids=distinct_epws,
                schedule_dirs=[SCHED_DIR],
            )
            distinct_comp_s = time.perf_counter() - t_comp0
            if n_distinct == n_fleet:
                full_compile_cache = (base_batch, distinct_comp_s)

        t_tile0 = time.perf_counter()
        tiled_batch = tile_batch_spec(base_batch, b_size)
        tile_s = time.perf_counter() - t_tile0
        compile_s = distinct_comp_s + tile_s

        tiled_weather = [
            weather_cache[str(entries[i % n_fleet]["epw_name"])]
            for i in range(b_size)
        ]

        weather_by_site, site_index = deduplicate_weather(tiled_weather, b_size)
        probe_packed = pack(tiled_batch, weather_by_site, site_index, ctf=None)
        run_chunk_days = select_safe_chunk_days(probe_packed)
        del probe_packed

        repeats: list[dict[str, float]] = []
        for _rep in range(N_REPEATS):
            t_pk0 = time.perf_counter()
            w_sites, s_idx = deduplicate_weather(tiled_weather, b_size)
            packed = pack(tiled_batch, w_sites, s_idx, ctf=None)
            pack_s = time.perf_counter() - t_pk0

            _, timings = run_packed_stage_c_mps(
                packed=packed,
                cell_ids=tiled_batch.cell_ids,
                record_zone_temp=False,
                force_warmup_days=None,
                run_chunk_days=run_chunk_days,
            )
            upload_s = pack_s + timings["upload_s"]
            gpu_s = timings["gpu_s"]
            download_s = timings["download_s"]
            total_s = compile_s + upload_s + gpu_s + download_s
            max_launch_s = timings["max_launch_s"]
            repeats.append(
                {
                    "upload_s": upload_s,
                    "gpu_s": gpu_s,
                    "download_s": download_s,
                    "total_s": total_s,
                    "max_launch_s": max_launch_s,
                }
            )
            if max_launch_s >= 1.0:
                raise RuntimeError(
                    f"Launch exceeded 1.0 s watchdog at B={b_size}: "
                    f"max_launch_s={max_launch_s:.4f}, chunk={run_chunk_days}"
                )

        repeats_sorted = sorted(repeats, key=lambda item: item["total_s"])
        med = repeats_sorted[N_REPEATS // 2]
        rate = float(b_size) / med["total_s"]
        sa_b, sa_rate = match_stage_a_rate(b_size, stage_a_rates)

        row: dict[str, object] = {
            "batch_size": b_size,
            "compile_s": f"{compile_s:.6f}",
            "upload_s": f"{med['upload_s']:.6f}",
            "gpu_s": f"{med['gpu_s']:.6f}",
            "download_s": f"{med['download_s']:.6f}",
            "total_s": f"{med['total_s']:.6f}",
            "max_launch_s": f"{med['max_launch_s']:.6f}",
            "run_chunk_days": run_chunk_days,
            "building_years_per_s": f"{rate:.6f}",
            "speedup_vs_eplus_1proc": f"{rate / eplus_1proc_rate:.6f}",
            "speedup_vs_eplus_4proc": f"{rate / eplus_4proc_rate:.6f}",
            "speedup_vs_stage_a": f"{rate / sa_rate:.6f}",
        }
        rows.append(row)
        print(
            f"B={b_size:5d} (chunk={run_chunk_days}d, SA_ref=B{sa_b}): "
            f"compile={compile_s:.3f}s, upload={med['upload_s']:.3f}s, "
            f"gpu={med['gpu_s']:.3f}s, download={med['download_s']:.3f}s, "
            f"total={med['total_s']:.3f}s, max_launch={med['max_launch_s']:.3f}s, "
            f"rate={rate:.4f} bldg-yr/s, "
            f"vs_ep1={rate / eplus_1proc_rate:.2f}x, "
            f"vs_ep4={rate / eplus_4proc_rate:.2f}x, "
            f"vs_SA={rate / sa_rate:.2f}x"
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "batch_size",
        "compile_s",
        "upload_s",
        "gpu_s",
        "download_s",
        "total_s",
        "max_launch_s",
        "run_chunk_days",
        "building_years_per_s",
        "speedup_vs_eplus_1proc",
        "speedup_vs_eplus_4proc",
        "speedup_vs_stage_a",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"\nBaselines: E+ 1-proc measured={eplus_1proc_rate:.6f} bldg-yr/s "
        f"(median sizing_off wall={eplus_med_wall_s:.6f}s); "
        f"E+ 4-proc computed={eplus_4proc_rate:.6f} bldg-yr/s"
    )
    print(f"Wrote {OUT_CSV} ({len(rows)} rows)")
    return rows


if __name__ == "__main__":
    try:
        run_benchmark()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
