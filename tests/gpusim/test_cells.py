import csv
import json
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from openubem.gpusim.backends.numpy_ref import SimulationResult, run_stage_a_batch
from openubem.gpusim.compile import BatchSpec, compile_expidf_batch
from openubem.gpusim.weather import WeatherSeries, load_epw_weather
from openubem.gpusim.writer import (
    EPLUS_HEATING_COLUMN,
    annual_heating_kwh,
    write_eplusout_csv,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REP2_SCHED_DIR = (
    REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2/schedules"
)
GOLDEN_ROOT = REPO_ROOT / "tests/fixtures/gpusim/golden"
CELLS_CSV_PATH = REPO_ROOT / "openubem/outputs/gpusim_m1_cells.csv"

CELL1_ID = "it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100"
GOLDEN_CELL_IDS: tuple[str, ...] = (
    CELL1_ID,
    "uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000",
    "es__ES.ME.AB.01.Gen.ReEx.001.001__f000",
)
S0_VARIANT_IDS: tuple[str, ...] = (
    "V01",
    "V03",
    "V04",
    "V06",
    "V07",
    "V09",
    "V10",
    "V11",
    "V14",
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
ZONE_MEAN_TEMP_COL = "EU_CELL_ZONE:Zone Mean Air Temperature [C](TimeStep)"


def _resolve_epw(epw_file_name: str) -> Path:
    """Locate an EPW file across known repository weather directories.

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


@lru_cache(maxsize=16)
def _load_weather_cached(epw_file_name: str) -> WeatherSeries:
    """Load and cache a WeatherSeries by EPW filename.

    Args:
        epw_file_name: Basename of the EPW file.

    Returns:
        Loaded ``WeatherSeries`` at 12 steps/hour.
    """
    return load_epw_weather(_resolve_epw(epw_file_name), steps_per_hour=12)


def _parse_eio_warmup_days(eio_path: Path) -> int:
    """Parse ``Environment:WarmupDays`` from ``eplusout.eio``.

    Args:
        eio_path: Path to EnergyPlus ``eplusout.eio``.

    Returns:
        Number of warm-up days reported by EnergyPlus.
    """
    for line in eio_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("Environment:WarmupDays,"):
            return int(line.split(",")[1].strip())
    raise ValueError(f"Environment:WarmupDays not found in {eio_path}")


def _evaluate_fixture_batch(
    fixture_dirs: tuple[Path, ...],
) -> tuple[BatchSpec, SimulationResult, list[dict[str, object]], float]:
    """Run Stage A on a batch of golden fixture directories and compute metrics.

    Args:
        fixture_dirs: Tuple of golden cell or variant directories.

    Returns:
        Tuple ``(batch, sim_result, metric_rows, wall_seconds)``.
    """
    expidf_paths = [d / "eplusout.expidf" for d in fixture_dirs]
    for path in expidf_paths:
        assert path.is_file(), f"Missing fixture expidf: {path}"
    cell_ids = [d.name for d in fixture_dirs]
    metas = [
        json.loads((d / "meta.json").read_text(encoding="utf-8"))
        for d in fixture_dirs
    ]
    weathers = [_load_weather_cached(str(m["epw_file_name"])) for m in metas]
    batch = compile_expidf_batch(
        expidf_paths,
        cell_ids=cell_ids,
        schedule_dirs=[REP2_SCHED_DIR],
    )

    t0 = time.perf_counter()
    res = run_stage_a_batch(batch, weathers, record_zone_temp=True)
    wall_s = time.perf_counter() - t0

    assert res.zone_mean_air_temp_c is not None
    rows: list[dict[str, object]] = []
    for bi, fdir in enumerate(fixture_dirs):
        tbl = pq.read_table(fdir / "timestep.parquet")
        e_ts = tbl[ENERGY_COL].to_numpy()
        t_ep = tbl[ZONE_MEAN_TEMP_COL].to_numpy()
        h_ep = e_ts.reshape(8760, batch.steps_per_hour).sum(axis=1)
        h_sa = res.hourly_heating_j[bi]

        ann_ep = float(np.sum(h_ep, dtype=np.float64) / 3.6e6)
        ann_sa = float(res.annual_heating_kwh[bi])
        floor_area = float(batch.zone_floor_area[bi])
        rel_diff = (ann_sa - ann_ep) / ann_ep
        abs_kwh_m2 = abs(ann_sa - ann_ep) / floor_area

        thr_j = 1.0 * floor_area * 3600.0
        active = (h_ep > thr_j) | (h_sa > thr_j)
        diff_h = h_sa[active] - h_ep[active]
        mean_ep = float(np.mean(h_ep[active]))
        cv_rmse = float(np.sqrt(np.mean(diff_h * diff_h)) / mean_ep)
        nmbe = float(np.mean(diff_h) / mean_ep)

        dt_air = np.abs(res.zone_mean_air_temp_c[bi] - t_ep)
        dt_p999 = float(np.percentile(dt_air, 99.9))
        dt_max = float(np.max(dt_air))

        wu_ep = _parse_eio_warmup_days(fdir / "eplusout.eio")
        wu_sa = int(res.warmup_days[bi])

        rows.append(
            {
                "cell": fdir.name,
                "annual_eplus_kwh": ann_ep,
                "annual_stage_a_kwh": ann_sa,
                "rel_diff": rel_diff,
                "abs_kwh_m2": abs_kwh_m2,
                "cv_rmse": cv_rmse,
                "nmbe": nmbe,
                "dt_p999_k": dt_p999,
                "dt_max_k": dt_max,
                "warmup_days_eplus": wu_ep,
                "warmup_days_stage_a": wu_sa,
                "wall_seconds": wall_s,
            }
        )
    return batch, res, rows, wall_s


@lru_cache(maxsize=1)
def run_golden_b3_cached() -> tuple[
    BatchSpec, SimulationResult, list[dict[str, object]], float
]:
    """Run and cache the B=3 golden cells Stage A batch.

    Returns:
        Output of ``_evaluate_fixture_batch`` for the 3 golden cells.
    """
    dirs = tuple(GOLDEN_ROOT / cid for cid in GOLDEN_CELL_IDS)
    return _evaluate_fixture_batch(dirs)


@lru_cache(maxsize=1)
def run_variants_b9_cached() -> tuple[
    BatchSpec, SimulationResult, list[dict[str, object]], float
]:
    """Run and cache the B=9 S0 variants Stage A batch.

    Returns:
        Output of ``_evaluate_fixture_batch`` for the 9 S0 variants.
    """
    dirs = tuple(
        GOLDEN_ROOT / "variants" / f"{CELL1_ID}__{vid}" for vid in S0_VARIANT_IDS
    )
    return _evaluate_fixture_batch(dirs)


def assert_t05_gates(rows: list[dict[str, object]]) -> None:
    """Assert every T05 conformance gate on each cell/variant metric row.

    Args:
        rows: Metric dictionaries returned by ``_evaluate_fixture_batch``.
    """
    for row in rows:
        cell = str(row["cell"])
        rel_diff = abs(float(row["rel_diff"]))
        abs_kwh_m2 = float(row["abs_kwh_m2"])
        cv_rmse = float(row["cv_rmse"])
        nmbe = abs(float(row["nmbe"]))
        dt_p999 = float(row["dt_p999_k"])
        dt_max = float(row["dt_max_k"])

        assert rel_diff <= 0.005 or abs_kwh_m2 <= 0.05, (
            f"{cell} annual heating gate failed: rel={rel_diff:.6f}, "
            f"abs={abs_kwh_m2:.6f} kWh/m2"
        )
        assert cv_rmse <= 0.01, f"{cell} CV(RMSE)={cv_rmse:.6f} > 0.01"
        assert nmbe <= 0.001, f"{cell} |NMBE|={nmbe:.6f} > 0.001"
        assert dt_p999 <= 0.03, f"{cell} dT p99.9={dt_p999:.6f} K > 0.03 K"
        assert dt_max <= 0.25, f"{cell} dT max={dt_max:.6f} K > 0.25 K"


def write_cells_report_csv(rows: list[dict[str, object]]) -> None:
    """Write ``openubem/outputs/gpusim_m1_cells.csv`` from metric rows.

    Args:
        rows: Combined golden cell and variant metric rows.
    """
    fieldnames = [
        "cell",
        "annual_eplus_kwh",
        "annual_stage_a_kwh",
        "rel_diff",
        "cv_rmse",
        "nmbe",
        "dt_p999_k",
        "dt_max_k",
        "warmup_days_eplus",
        "warmup_days_stage_a",
        "wall_seconds",
    ]
    CELLS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CELLS_CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "cell": row["cell"],
                    "annual_eplus_kwh": f"{float(row['annual_eplus_kwh']):.6f}",
                    "annual_stage_a_kwh": f"{float(row['annual_stage_a_kwh']):.6f}",
                    "rel_diff": f"{float(row['rel_diff']):.8e}",
                    "cv_rmse": f"{float(row['cv_rmse']):.8e}",
                    "nmbe": f"{float(row['nmbe']):.8e}",
                    "dt_p999_k": f"{float(row['dt_p999_k']):.6f}",
                    "dt_max_k": f"{float(row['dt_max_k']):.6f}",
                    "warmup_days_eplus": int(row["warmup_days_eplus"]),
                    "warmup_days_stage_a": int(row["warmup_days_stage_a"]),
                    "wall_seconds": f"{float(row['wall_seconds']):.3f}",
                }
            )


def test_golden_cells_and_s0_variants_conformance(tmp_path: Path) -> None:
    """Verify all 3 golden cells and 9 S0 variants pass T05 gates and writer."""
    _, res_b3, rows_b3, _ = run_golden_b3_cached()
    _, _, rows_b9, _ = run_variants_b9_cached()

    assert_t05_gates(rows_b3)
    assert_t05_gates(rows_b9)
    write_cells_report_csv(rows_b3 + rows_b9)
    assert CELLS_CSV_PATH.is_file()

    csv_out = tmp_path / "eplusout.csv"
    write_eplusout_csv(csv_out, res_b3.hourly_heating_j[0])
    with csv_out.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        data_rows = list(reader)
    assert header == ["Date/Time", EPLUS_HEATING_COLUMN]
    assert len(data_rows) == 8760
    reloaded = np.array([float(r[1]) for r in data_rows], dtype=np.float64)
    assert np.isclose(
        float(annual_heating_kwh(reloaded)),
        float(res_b3.annual_heating_kwh[0]),
        rtol=1.0e-9,
    )
