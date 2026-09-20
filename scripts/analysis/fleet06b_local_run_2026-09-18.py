"""FLEET-06b local execution (techtransfer block-6 plan, section 2e local-only decision,
2026-09-18): run the 65,112-row scenario manifest through EnergyPlus locally, Speed
withdrawn per the user's decision recorded in
`docs/docs_ACTIVE/TechTransfer/implementation/PLAN_techtransfer-block6-2026-09-18.md`
section 2e.

Consumes, unmodified:
  - `%TEMP%\\ubem_validation\\fleet06a_campaign_2026-09-18\\manifest_65112.csv`
    (building_id, cell_name, output_idf_path) built by FLEET-06a. Not rebuilt here.
  - `openubem.simulation.parallel.SimTask` / `_purge_work_dir` / `is_completed` and
    `openubem.simulation.runner.run_energyplus` / `classify_outcome` / `_version_handshake`
    -- the codebase's actual local single-building EnergyPlus execution primitives.
    `openubem.scenarios.campaign_runner.run_campaign()` was checked first per the task
    spec ("run run_campaign() or the equivalent local-execution entry point") but its own
    module docstring says "No EnergyPlus run happens anywhere in this module" -- it only
    builds/saves IDFs (which FLEET-06a already did). `openubem.simulation.runner` is the
    equivalent local-execution entry point this task means; used unmodified.

Per-building weather: the manifest carries no epw_path column. Each building's EPW is
resolved via `openubem/outputs/comparisons/t08_restated_fleet_eui_2026-09-10.csv`
(columns `stem`, `cell` -- `cell` is the geographic cell, e.g. "austin_centre", one of
12), joined to that geographic cell's single EPW path recorded in
`fleet06a_rebuild_2026-09-18/<cell>/02a_climate_epw.parquet` (verified: exactly one
unique `epw_path` per geographic cell, 12/12). The same building's EPW is reused across
all 8 scenario cells (weather does not change with a measure package), including
`baseline` (fetched from an earlier T07 Speed run of the same building at the same
location).

Output convention (mirrors `scripts/cluster/submit_fleet06b.sbatch`'s
`out/<cell_name>/<building_id>/` layout, adapted to local disk): each case runs under
`<OUT_ROOT>/out/<cell_name>/<building_id>/`. After a case finishes, non-retained files
are purged via the existing `openubem.simulation.parallel._purge_work_dir` /
`config.SIM_RETAIN_FILES` convention (keeps eplusout.sql/.csv/.mtr/.err/.end,
eplustbl.htm, openubem_run.log) -- unmodified, to keep 65,112 cases' output within local
disk space.

Modes:
  benchmark   -- run a fixed-seed random sample of BENCH_N cases (default 30), full
                 EnergyPlus runs, report per-case wall time and achieved concurrency.
                 Writes `<OUT_ROOT>/benchmark_result.json`.
  full        -- run every remaining case in the manifest (skips any work_dir already
                 `is_completed`, including ones the benchmark already ran), same worker
                 cap, checkpointing `<OUT_ROOT>/progress.json` and appending
                 `<OUT_ROOT>/results.csv` after every case.

Usage:
  .venv\\Scripts\\python.exe scripts\\analysis\\fleet06b_local_run_2026-09-18.py benchmark
  .venv\\Scripts\\python.exe scripts\\analysis\\fleet06b_local_run_2026-09-18.py full
"""
from __future__ import annotations

import csv
import json
import os
import random
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from openubem.simulation.parallel import SimTask, _purge_work_dir, is_completed  # noqa: E402
from openubem.simulation.runner import (  # noqa: E402
    classify_outcome,
    run_energyplus,
    _version_handshake,
)

TEMP = Path(os.environ["TEMP"])
MANIFEST_CSV = TEMP / "ubem_validation" / "fleet06a_campaign_2026-09-18" / "manifest_65112.csv"
T08_CSV = REPO / "openubem" / "outputs" / "comparisons" / "t08_restated_fleet_eui_2026-09-10.csv"
REBUILD_BASE = TEMP / "ubem_validation" / "fleet06a_rebuild_2026-09-18"

GEO_CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]

OUT_ROOT = TEMP / "ubem_validation" / "fleet06b_local_2026-09-18"
OUT_DIR = OUT_ROOT / "out"
PROGRESS_JSON = OUT_ROOT / "progress.json"
RESULTS_CSV = OUT_ROOT / "results.csv"
BENCH_JSON = OUT_ROOT / "benchmark_result.json"
RUN_LOG = OUT_ROOT / "run_log.txt"

MAX_WORKERS = 10  # user directive 2026-09-18 (mid-run, after the benchmark and after the
                   # first ~30 s of the "full" run at 14 workers, before any full-run case
                   # had completed): cap at half of this machine's 20 logical CPUs, not the
                   # 14 used by the run_eu_certified_rerun.py precedent. The 14-worker value
                   # is left in the comment above for provenance only; do not restore it
                   # without a new instruction.
BENCH_N = 30
BENCH_SEED = 42

RESULTS_FIELDS = [
    "building_id", "cell_name", "geo_cell", "epw_path", "idf_path", "work_dir",
    "status", "n_warnings", "n_severe", "wall_clock_s", "error_summary",
]


def _log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def build_epw_map() -> dict[str, str]:
    import pandas as pd

    cell_epw: dict[str, str] = {}
    for cell in GEO_CELLS:
        p = REBUILD_BASE / cell / "02a_climate_epw.parquet"
        df = pd.read_parquet(p)
        uniq = df["epw_path"].unique()
        if len(uniq) != 1:
            raise SystemExit(f"STOP: {cell} has {len(uniq)} distinct epw_path values, expected 1: {uniq}")
        cell_epw[cell] = str(uniq[0])

    stem_epw: dict[str, str] = {}
    with T08_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stem = row["stem"]
            geo_cell = row["cell"]
            if geo_cell not in cell_epw:
                raise SystemExit(f"STOP: t08 row {stem} has unknown geo cell {geo_cell!r}")
            stem_epw[stem] = cell_epw[geo_cell]
    return stem_epw


def load_manifest() -> list[dict]:
    with MANIFEST_CSV.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _make_task(row: dict, epw_path: str) -> SimTask:
    work_dir = OUT_DIR / row["cell_name"] / row["building_id"]
    return SimTask(
        osm_id=row["building_id"],
        idf_path=row["output_idf_path"],
        epw_path=epw_path,
        work_dir=str(work_dir),
    )


def _run_case(args: tuple[dict, str]) -> dict:
    row, epw_path = args
    task = _make_task(row, epw_path)
    work_dir = Path(task.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    raw = run_energyplus(task)
    classified = classify_outcome(raw, work_dir)
    wall = time.time() - t0
    try:
        _purge_work_dir(work_dir)
    except OSError:
        pass
    return {
        "building_id": row["building_id"],
        "cell_name": row["cell_name"],
        "epw_path": epw_path,
        "idf_path": row["output_idf_path"],
        "work_dir": str(work_dir),
        "status": classified["status"],
        "n_warnings": classified.get("n_warnings"),
        "n_severe": classified.get("n_severe"),
        "wall_clock_s": round(wall, 3),
        "error_summary": classified.get("error_summary", ""),
    }


def _append_results(rows: list[dict]) -> None:
    new_file = not RESULTS_CSV.exists()
    with RESULTS_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RESULTS_FIELDS)
        if new_file:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in RESULTS_FIELDS})


def _write_progress(done: int, failed: int, total: int, extra: dict | None = None) -> None:
    payload = {
        "done": done, "failed": failed, "remaining": total - done,
        "total": total, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if extra:
        payload.update(extra)
    PROGRESS_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def cmd_benchmark() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    ep_version = _version_handshake()
    _log(f"EnergyPlus version handshake OK: {ep_version}")

    manifest = load_manifest()
    _log(f"manifest rows: {len(manifest)}")
    epw_map = build_epw_map()
    missing_epw = [r["building_id"] for r in manifest if r["building_id"] not in epw_map]
    if missing_epw:
        raise SystemExit(f"STOP: {len(missing_epw)} manifest rows have no epw mapping, e.g. {missing_epw[:5]}")

    rng = random.Random(BENCH_SEED)
    sample = rng.sample(manifest, BENCH_N)
    _log(f"benchmark sample: {BENCH_N} cases, random (seed={BENCH_SEED}) from all {len(manifest)} rows")

    jobs = [(row, epw_map[row["building_id"]]) for row in sample]

    t0 = time.time()
    results: list[dict] = []
    max_concurrent_observed = 0
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(_run_case, job): job for job in jobs}
        max_concurrent_observed = min(MAX_WORKERS, len(jobs))
        for i, fut in enumerate(as_completed(futures), start=1):
            r = fut.result()
            results.append(r)
            _log(f"  benchmark {i}/{len(jobs)}: {r['building_id']}/{r['cell_name']} "
                 f"status={r['status']} wall={r['wall_clock_s']:.1f}s")
    total_wall = time.time() - t0

    _append_results(results)

    times = [r["wall_clock_s"] for r in results]
    n_success = sum(1 for r in results if r["status"] == "success")
    n_failed = len(results) - n_success

    per_case_mean = statistics.mean(times)
    per_case_min = min(times)
    per_case_max = max(times)

    manifest_total = len(manifest)
    already_done_estimate = 0  # benchmark runs first, nothing pre-existing normally
    remaining_after_bench = manifest_total - len(results)
    extrapolated_total_wall_s = (remaining_after_bench * per_case_mean) / MAX_WORKERS

    summary = {
        "measured_not_guessed": True,
        "n_benchmark_cases": len(results),
        "sample_method": f"random.Random(seed={BENCH_SEED}).sample() over all {manifest_total} manifest rows",
        "max_workers": MAX_WORKERS,
        "n_success": n_success,
        "n_failed": n_failed,
        "per_case_wall_s_mean": round(per_case_mean, 2),
        "per_case_wall_s_min": round(per_case_min, 2),
        "per_case_wall_s_max": round(per_case_max, 2),
        "benchmark_batch_wall_s": round(total_wall, 2),
        "manifest_total_cases": manifest_total,
        "remaining_cases_after_benchmark": remaining_after_bench,
        "extrapolated_full_remaining_wall_s": round(extrapolated_total_wall_s, 1),
        "extrapolated_full_remaining_wall_h": round(extrapolated_total_wall_s / 3600.0, 2),
        "extrapolation_basis": "this machine's own freshly-measured per-case mean / MAX_WORKERS, per docs_EXPLANATION debug ref 1595 (no cross-machine extrapolation)",
    }
    BENCH_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _log("BENCHMARK SUMMARY: " + json.dumps(summary))
    _log("BENCHMARK DONE")


def cmd_full() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    ep_version = _version_handshake()
    _log(f"EnergyPlus version handshake OK: {ep_version}")

    manifest = load_manifest()
    total = len(manifest)
    epw_map = build_epw_map()
    missing_epw = [r["building_id"] for r in manifest if r["building_id"] not in epw_map]
    if missing_epw:
        raise SystemExit(f"STOP: {len(missing_epw)} manifest rows have no epw mapping, e.g. {missing_epw[:5]}")

    pending = []
    skipped_done = 0
    for row in manifest:
        work_dir = OUT_DIR / row["cell_name"] / row["building_id"]
        if is_completed(work_dir):
            skipped_done += 1
            continue
        pending.append(row)

    _log(f"full run: total={total} already_completed={skipped_done} pending={len(pending)} "
         f"max_workers={MAX_WORKERS}")

    jobs = [(row, epw_map[row["building_id"]]) for row in pending]

    done = skipped_done
    failed = 0
    last_checkpoint = time.time()
    CHECKPOINT_EVERY_S = 120
    CHECKPOINT_EVERY_N = 100

    _write_progress(done, failed, total, extra={"pending_at_start": len(pending), "max_workers": MAX_WORKERS})

    batch_results: list[dict] = []
    n_since_checkpoint = 0
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(_run_case, job): job for job in jobs}
        for fut in as_completed(futures):
            r = fut.result()
            batch_results.append(r)
            done += 1
            n_since_checkpoint += 1
            if r["status"] != "success":
                failed += 1
            now = time.time()
            if n_since_checkpoint >= CHECKPOINT_EVERY_N or (now - last_checkpoint) >= CHECKPOINT_EVERY_S:
                _append_results(batch_results)
                batch_results = []
                _write_progress(done, failed, total)
                _log(f"progress: done={done}/{total} failed={failed} remaining={total - done}")
                last_checkpoint = now
                n_since_checkpoint = 0

    if batch_results:
        _append_results(batch_results)
    _write_progress(done, failed, total)
    _log(f"FULL RUN DONE: done={done}/{total} failed={failed}")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("benchmark", "full"):
        raise SystemExit("usage: fleet06b_local_run_2026-09-18.py {benchmark|full}")
    if sys.argv[1] == "benchmark":
        cmd_benchmark()
    else:
        cmd_full()


if __name__ == "__main__":
    main()
