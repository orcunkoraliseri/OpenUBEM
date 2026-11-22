import json
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch

from openubem.gpusim.backends.torch_batched import run_stage_b_batch
from openubem.gpusim.compile import compile_expidf_batch
from openubem.gpusim.weather import WeatherSeries, load_epw_weather

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = REPO_ROOT / "tests/fixtures/gpusim/golden"
SPIKE_FIXTURE_DIR = REPO_ROOT / "tests/fixtures/gpusim/spike"
REP2_SCHED_DIR = (
    REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2/schedules"
)
EPW_SEARCH_DIRS: tuple[Path, ...] = (
    REPO_ROOT / "openubem/data/weather",
    REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2/weather",
    REPO_ROOT / "tests/fixtures/gpusim/golden/weather",
    REPO_ROOT / "data/weather",
)
ENERGY_COL = (
    "EU_CELL_ZONE IDEAL LOADS AIR SYSTEM:"
    "Zone Ideal Loads Zone Total Heating Energy [J](TimeStep)"
)
CELL1_ID = "it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100"
SPIKE_FIXTURE_PATHS: tuple[Path, ...] = (
    GOLDEN_ROOT / CELL1_ID,
    GOLDEN_ROOT / "uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000",
    GOLDEN_ROOT / "es__ES.ME.AB.01.Gen.ReEx.001.001__f000",
    GOLDEN_ROOT / "variants" / f"{CELL1_ID}__V10",
    GOLDEN_ROOT / "variants" / f"{CELL1_ID}__V11",
)


def _resolve_epw(epw_file_name: str) -> Path:
    """Locate an EPW file across repository weather directories.

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


def _find_target_steps(fixture_dir: Path) -> list[int]:
    """Identify the three target run-period step indices for one golden cell.

    Selects step 0 (first step after warm-up), the first January step at 07:00
    with positive heating energy, and the first July step at 14:00.

    Args:
        fixture_dir: Golden fixture directory containing ``timestep.parquet``.

    Returns:
        Sorted list of three run-period step indices.
    """
    table = pq.read_table(
        fixture_dir / "timestep.parquet",
        columns=["month", "day", "hour", "minute", ENERGY_COL],
    )
    month = table["month"].to_numpy()
    hour = table["hour"].to_numpy()
    minute = table["minute"].to_numpy()
    energy = table[ENERGY_COL].to_numpy()

    jan_matches = np.flatnonzero(
        (month == 1) & (hour == 7) & (minute == 0) & (energy > 0.0)
    )
    if jan_matches.size == 0:
        raise ValueError(f"No January 07:00 step with heating > 0 in {fixture_dir}")
    jan_step = int(jan_matches[0])

    jul_matches = np.flatnonzero((month == 7) & (hour == 14) & (minute == 0))
    if jul_matches.size == 0:
        raise ValueError(f"No July 14:00 step found in {fixture_dir}")
    jul_step = int(jul_matches[0])

    return [0, jan_step, jul_step]


def capture_all_spike_inputs(output_dir: Path = SPIKE_FIXTURE_DIR) -> list[Path]:
    """Capture float64 Stage B step-5 inputs and outputs for the 5 spike cells.

    Args:
        output_dir: Destination directory for ``<cell>__<step>.npz`` files.

    Returns:
        List of written ``.npz`` file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    weather_cache: dict[str, WeatherSeries] = {}
    written_paths: list[Path] = []
    t_start = time.perf_counter()

    for fixture_dir in SPIKE_FIXTURE_PATHS:
        cell_id = fixture_dir.name
        meta = json.loads((fixture_dir / "meta.json").read_text(encoding="utf-8"))
        epw_name = str(meta["epw_file_name"])
        if epw_name not in weather_cache:
            weather_cache[epw_name] = load_epw_weather(
                _resolve_epw(epw_name), steps_per_hour=12
            )
        weather = weather_cache[epw_name]
        batch = compile_expidf_batch(
            [fixture_dir / "eplusout.expidf"],
            cell_ids=[cell_id],
            schedule_dirs=[REP2_SCHED_DIR],
        )
        steps_per_day = 24 * batch.steps_per_hour
        target_steps = _find_target_steps(fixture_dir)
        run_days = (max(target_steps) // steps_per_day) + 1
        captures: dict[int, dict[str, np.ndarray]] = {s: {} for s in target_steps}

        t_cell = time.perf_counter()
        result = run_stage_b_batch(
            batch=batch,
            weather=[weather],
            record_zone_temp=False,
            device="cpu",
            dtype=torch.float64,
            capture_steps=captures,
            run_days=run_days,
        )
        elapsed_cell = time.perf_counter() - t_cell

        jan_step = target_steps[1]
        jan_hour_j = float(result.hourly_heating_j[0, jan_step // batch.steps_per_hour])
        if jan_hour_j <= 0.0:
            raise RuntimeError(
                f"{cell_id}: expected heating > 0 at step {jan_step}, "
                f"got hourly_heating_j={jan_hour_j}"
            )

        for step_idx in target_steps:
            payload = captures[step_idx]
            if not payload:
                raise RuntimeError(f"{cell_id}: capture missing for step {step_idx}")
            out_path = output_dir / f"{cell_id}__{step_idx}.npz"
            save_dict: dict[str, np.ndarray] = dict(payload)
            save_dict["step_idx"] = np.asarray(step_idx, dtype=np.int32)
            np.savez(out_path, **save_dict)
            written_paths.append(out_path)
            iters = int(payload["iter_count"][0])
            print(
                f"captured {out_path.name}: S={payload['t_surf_in_init'].shape[1]} "
                f"iters={iters} begin_envrn={bool(payload['begin_envrn'])}"
            )

        print(
            f"finished {cell_id} (run_days={run_days}, "
            f"warmup={int(result.warmup_days[0])}) in {elapsed_cell:.2f}s"
        )

    total_bytes = sum(p.stat().st_size for p in written_paths)
    total_wall = time.perf_counter() - t_start
    print(
        f"wrote {len(written_paths)} files, total={total_bytes / 1024.0:.1f} KiB "
        f"in {total_wall:.2f}s"
    )
    return written_paths


def main() -> None:
    """Entry point for capturing M2 spike fixtures."""
    capture_all_spike_inputs()


if __name__ == "__main__":
    main()
