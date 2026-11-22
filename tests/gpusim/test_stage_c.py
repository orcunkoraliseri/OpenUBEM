import csv
import json
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from openubem.gpusim.backends.numpy_ref import SimulationResult, run_stage_a_batch
from openubem.gpusim.backends.stage_c import run_stage_c_batch
from openubem.gpusim.compile import BatchSpec, compile_expidf_batch
from openubem.gpusim.weather import WeatherSeries
from tests.gpusim.test_cells import (
    CELL1_ID,
    ENERGY_COL,
    GOLDEN_CELL_IDS,
    GOLDEN_ROOT,
    REP2_SCHED_DIR,
    REPO_ROOT,
    S0_VARIANT_IDS,
    ZONE_MEAN_TEMP_COL,
    _load_weather_cached,
)

STAGE_A_P1_CACHE_DIR = REPO_ROOT / "tests/fixtures/gpusim/stage_a_p1"
CELLS_M3_CSV_PATH = REPO_ROOT / "openubem/outputs/gpusim_m3_cells.csv"

M3_CELLS_FIELDS = [
    "cell",
    "annual_stage_a_kwh",
    "annual_stage_c_kwh",
    "rel_c_vs_a",
    "dt_p999_k",
    "dt_max_k",
    "annual_eplus_kwh",
    "rel_c_vs_eplus",
    "cv_rmse",
    "nmbe",
    "dt_p999_eplus_k",
    "dt_max_eplus_k",
    "warmup_days_stage_a",
    "warmup_days_stage_c_free",
    "wall_seconds",
]


def _p1_fixture_dirs() -> tuple[Path, ...]:
    """Return the 12 P1 S0 golden fixture directories (3 cells + 9 variants).

    Returns:
        Tuple of 12 fixture directory paths.
    """
    cell_dirs = tuple(GOLDEN_ROOT / cid for cid in GOLDEN_CELL_IDS)
    var_dirs = tuple(
        GOLDEN_ROOT / "variants" / f"{CELL1_ID}__{vid}" for vid in S0_VARIANT_IDS
    )
    return cell_dirs + var_dirs


def _load_batch_and_weather(
    fixture_dirs: tuple[Path, ...],
) -> tuple[BatchSpec, list[WeatherSeries]]:
    """Compile a batch of fixture directories and load their weather series.

    Args:
        fixture_dirs: Tuple of golden fixture directories.

    Returns:
        Tuple ``(batch, weathers)``.
    """
    expidfs = [d / "eplusout.expidf" for d in fixture_dirs]
    cell_ids = [d.name for d in fixture_dirs]
    metas = [
        json.loads((d / "meta.json").read_text(encoding="utf-8"))
        for d in fixture_dirs
    ]
    weathers = [_load_weather_cached(str(m["epw_file_name"])) for m in metas]
    batch = compile_expidf_batch(
        expidfs,
        cell_ids=cell_ids,
        schedule_dirs=[REP2_SCHED_DIR],
    )
    return batch, weathers


def _load_or_build_stage_a_p1_cache(
    batch: BatchSpec,
    weathers: list[WeatherSeries],
) -> SimulationResult:
    """Load cached float64 Stage A P1 references or compute and cache them once.

    Args:
        batch: Compiled 12-case P1 ``BatchSpec``.
        weathers: List of 12 matching ``WeatherSeries``.

    Returns:
        ``SimulationResult`` containing float64 hourly heating and zone temps.
    """
    STAGE_A_P1_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_paths = [
        STAGE_A_P1_CACHE_DIR / f"{cid}.npz" for cid in batch.cell_ids
    ]
    if all(p.is_file() for p in cache_paths):
        hourly_list: list[np.ndarray] = []
        annual_list: list[float] = []
        wu_list: list[int] = []
        zair_list: list[np.ndarray] = []
        zmean_list: list[np.ndarray] = []
        for path in cache_paths:
            with np.load(path) as data:
                hourly_list.append(
                    np.asarray(data["hourly_heating_j"], dtype=np.float64)
                )
                annual_list.append(float(data["annual_heating_kwh"]))
                wu_list.append(int(data["warmup_days"]))
                zair_list.append(
                    np.asarray(data["zone_air_temp_c"], dtype=np.float64)
                )
                zmean_list.append(
                    np.asarray(data["zone_mean_air_temp_c"], dtype=np.float64)
                )
        return SimulationResult(
            cell_ids=list(batch.cell_ids),
            hourly_heating_j=np.stack(hourly_list, axis=0),
            annual_heating_kwh=np.asarray(annual_list, dtype=np.float64),
            warmup_days=np.asarray(wu_list, dtype=np.int32),
            zone_air_temp_c=np.stack(zair_list, axis=0),
            zone_mean_air_temp_c=np.stack(zmean_list, axis=0),
        )

    res_a = run_stage_a_batch(batch, weathers, record_zone_temp=True)
    assert res_a.zone_air_temp_c is not None
    assert res_a.zone_mean_air_temp_c is not None
    for bi, path in enumerate(cache_paths):
        np.savez_compressed(
            path,
            hourly_heating_j=res_a.hourly_heating_j[bi],
            annual_heating_kwh=np.asarray(
                res_a.annual_heating_kwh[bi], dtype=np.float64
            ),
            warmup_days=np.asarray(res_a.warmup_days[bi], dtype=np.int32),
            zone_air_temp_c=res_a.zone_air_temp_c[bi],
            zone_mean_air_temp_c=res_a.zone_mean_air_temp_c[bi],
        )
    return res_a


def _format_first_exceed(
    step_dt: np.ndarray,
    t_ref: np.ndarray,
    t_test: np.ndarray,
    h_ref: np.ndarray,
    h_test: np.ndarray,
    steps_per_hour: int,
    threshold_k: float = 0.02,
) -> str:
    """Format diagnostic values at the first timestep where ΔT exceeds limit.

    Args:
        step_dt: Absolute temperature differences ``[T]``.
        t_ref: Reference zone mean air temperature ``[T]``.
        t_test: Test zone mean air temperature ``[T]``.
        h_ref: Reference hourly heating energies ``[H]``.
        h_test: Test hourly heating energies ``[H]``.
        steps_per_hour: Number of timesteps per hour.
        threshold_k: Temperature exceedance threshold in Kelvin.

    Returns:
        Diagnostic summary string or empty string if within threshold.
    """
    over_idx = np.where(step_dt > threshold_k)[0]
    if over_idx.size == 0:
        return ""
    first_step = int(over_idx[0])
    hr = first_step // steps_per_hour
    return (
        f" first_step_gt_{threshold_k:.2f}K={first_step} (hr={hr}): "
        f"t_a={t_ref[first_step]:.6f} C, "
        f"t_c={t_test[first_step]:.6f} C, "
        f"dt={step_dt[first_step]:.6f} K, "
        f"h_a={h_ref[hr]:.2f} J, "
        f"h_c={h_test[hr]:.2f} J"
    )


def test_stage_c_p1() -> None:
    """Verify Stage C Metal passes float32 and S0 gates across all 12 P1 cases."""
    dirs = _p1_fixture_dirs()
    batch, weathers = _load_batch_and_weather(dirs)
    res_a = _load_or_build_stage_a_p1_cache(batch, weathers)
    assert res_a.zone_mean_air_temp_c is not None

    t0 = time.perf_counter()
    res_locked = run_stage_c_batch(
        batch,
        weathers,
        record_zone_temp=True,
        force_warmup_days=res_a.warmup_days,
        run_chunk_days=1,
    )
    res_free = run_stage_c_batch(
        batch,
        weathers,
        record_zone_temp=True,
        force_warmup_days=None,
        run_chunk_days=1,
    )
    wall_s = time.perf_counter() - t0

    assert res_locked.zone_mean_air_temp_c is not None
    assert res_free.zone_mean_air_temp_c is not None
    assert np.array_equal(res_locked.warmup_days, res_a.warmup_days)

    rows_csv: list[dict[str, str]] = []
    metrics: list[dict[str, float | str]] = []
    failures: list[str] = []

    for bi, fdir in enumerate(dirs):
        cell = fdir.name
        floor_area = float(batch.zone_floor_area[bi])
        wu_a = int(res_a.warmup_days[bi])
        wu_c_free = int(res_free.warmup_days[bi])

        ann_a = float(res_a.annual_heating_kwh[bi])
        ann_c_locked = float(res_locked.annual_heating_kwh[bi])
        denom_a = ann_a if abs(ann_a) > 1.0e-12 else 1.0e-12
        rel_c_vs_a = (ann_c_locked - ann_a) / denom_a
        abs_ca_kwh_m2 = abs(ann_c_locked - ann_a) / floor_area

        dt_ca = np.abs(
            res_locked.zone_mean_air_temp_c[bi] - res_a.zone_mean_air_temp_c[bi]
        )
        dt_p999_ca = float(np.percentile(dt_ca, 99.9))
        dt_max_ca = float(np.max(dt_ca))

        tbl = pq.read_table(fdir / "timestep.parquet")
        e_ts = tbl[ENERGY_COL].to_numpy()
        t_ep = tbl[ZONE_MEAN_TEMP_COL].to_numpy()
        h_ep = e_ts.reshape(8760, batch.steps_per_hour).sum(axis=1)
        h_c_free = res_free.hourly_heating_j[bi]

        ann_ep = float(np.sum(h_ep, dtype=np.float64) / 3.6e6)
        ann_c_free = float(res_free.annual_heating_kwh[bi])
        rel_c_vs_ep = (ann_c_free - ann_ep) / ann_ep
        abs_ce_kwh_m2 = abs(ann_c_free - ann_ep) / floor_area

        thr_j = 1.0 * floor_area * 3600.0
        active = (h_ep > thr_j) | (h_c_free > thr_j)
        diff_h = h_c_free[active] - h_ep[active]
        mean_ep = float(np.mean(h_ep[active]))
        cv_rmse = float(np.sqrt(np.mean(diff_h * diff_h)) / mean_ep)
        nmbe = float(np.mean(diff_h) / mean_ep)

        dt_ep = np.abs(res_free.zone_mean_air_temp_c[bi] - t_ep)
        dt_p999_ep = float(np.percentile(dt_ep, 99.9))
        dt_max_ep = float(np.max(dt_ep))

        rows_csv.append(
            {
                "cell": cell,
                "annual_stage_a_kwh": f"{ann_a:.6f}",
                "annual_stage_c_kwh": f"{ann_c_locked:.6f}",
                "rel_c_vs_a": f"{rel_c_vs_a:.8e}",
                "dt_p999_k": f"{dt_p999_ca:.6f}",
                "dt_max_k": f"{dt_max_ca:.6f}",
                "annual_eplus_kwh": f"{ann_ep:.6f}",
                "rel_c_vs_eplus": f"{rel_c_vs_ep:.8e}",
                "cv_rmse": f"{cv_rmse:.8e}",
                "nmbe": f"{nmbe:.8e}",
                "dt_p999_eplus_k": f"{dt_p999_ep:.6f}",
                "dt_max_eplus_k": f"{dt_max_ep:.6f}",
                "warmup_days_stage_a": str(wu_a),
                "warmup_days_stage_c_free": str(wu_c_free),
                "wall_seconds": f"{wall_s:.3f}",
            }
        )
        metrics.append(
            {
                "cell": cell,
                "rel_c_vs_a": abs(rel_c_vs_a),
                "dt_p999_k": dt_p999_ca,
                "dt_max_k": dt_max_ca,
                "rel_c_vs_eplus": abs(rel_c_vs_ep),
                "cv_rmse": cv_rmse,
                "nmbe": abs(nmbe),
                "dt_p999_eplus_k": dt_p999_ep,
                "dt_max_eplus_k": dt_max_ep,
            }
        )

        if not (abs(rel_c_vs_a) <= 5.0e-4 or abs_ca_kwh_m2 <= 0.01):
            failures.append(
                f"{cell} float32 annual gate: rel={rel_c_vs_a:.6e}, "
                f"abs={abs_ca_kwh_m2:.6f} kWh/m2"
            )
        if dt_p999_ca > 0.02 or dt_max_ca > 0.10:
            extra = _format_first_exceed(
                dt_ca,
                res_a.zone_mean_air_temp_c[bi],
                res_locked.zone_mean_air_temp_c[bi],
                res_a.hourly_heating_j[bi],
                res_locked.hourly_heating_j[bi],
                batch.steps_per_hour,
            )
            failures.append(
                f"{cell} float32 dT gate: p99.9={dt_p999_ca:.6f} K, "
                f"max={dt_max_ca:.6f} K.{extra}"
            )
        if wu_c_free != wu_a:
            failures.append(
                f"{cell} free warmup mismatch: C={wu_c_free} vs A={wu_a}"
            )
        if not (abs(rel_c_vs_ep) <= 0.005 or abs_ce_kwh_m2 <= 0.05):
            failures.append(
                f"{cell} S0 annual vs E+ gate: rel={rel_c_vs_ep:.6e}, "
                f"abs={abs_ce_kwh_m2:.6f} kWh/m2"
            )
        if cv_rmse > 0.01:
            failures.append(f"{cell} S0 CV(RMSE)={cv_rmse:.6f} > 0.01")
        if abs(nmbe) > 0.001:
            failures.append(f"{cell} S0 |NMBE|={abs(nmbe):.6f} > 0.001")
        if dt_p999_ep > 0.03 or dt_max_ep > 0.25:
            failures.append(
                f"{cell} S0 dT vs E+ gate: p99.9={dt_p999_ep:.6f} K, "
                f"max={dt_max_ep:.6f} K"
            )

    CELLS_M3_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CELLS_M3_CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=M3_CELLS_FIELDS)
        writer.writeheader()
        writer.writerows(rows_csv)
    assert CELLS_M3_CSV_PATH.is_file()

    w_rel_ca = max(metrics, key=lambda r: float(r["rel_c_vs_a"]))
    w_p999_ca = max(metrics, key=lambda r: float(r["dt_p999_k"]))
    w_max_ca = max(metrics, key=lambda r: float(r["dt_max_k"]))
    w_rel_ep = max(metrics, key=lambda r: float(r["rel_c_vs_eplus"]))
    w_cv = max(metrics, key=lambda r: float(r["cv_rmse"]))
    w_nmbe = max(metrics, key=lambda r: float(r["nmbe"]))
    w_p999_ep = max(metrics, key=lambda r: float(r["dt_p999_eplus_k"]))
    w_max_ep = max(metrics, key=lambda r: float(r["dt_max_eplus_k"]))

    print(
        f"T03 Stage C P1 (B=12, locked+free) wall={wall_s:.3f} s | "
        f"worst |rel_c_vs_a|={float(w_rel_ca['rel_c_vs_a']):.3e} "
        f"({w_rel_ca['cell']}), "
        f"worst dt_p999_k={float(w_p999_ca['dt_p999_k']):.6f} K "
        f"({w_p999_ca['cell']}), "
        f"worst dt_max_k={float(w_max_ca['dt_max_k']):.6f} K "
        f"({w_max_ca['cell']}), "
        f"worst |rel_c_vs_eplus|={float(w_rel_ep['rel_c_vs_eplus']):.3e} "
        f"({w_rel_ep['cell']}), "
        f"worst cv_rmse={float(w_cv['cv_rmse']):.3e} ({w_cv['cell']}), "
        f"worst |nmbe|={float(w_nmbe['nmbe']):.3e} ({w_nmbe['cell']}), "
        f"worst dt_p999_eplus_k={float(w_p999_ep['dt_p999_eplus_k']):.6f} K "
        f"({w_p999_ep['cell']}), "
        f"worst dt_max_eplus_k={float(w_max_ep['dt_max_eplus_k']):.6f} K "
        f"({w_max_ep['cell']})"
    )

    assert not failures, "T03 Stage C P1 failures:\n" + "\n".join(failures)
