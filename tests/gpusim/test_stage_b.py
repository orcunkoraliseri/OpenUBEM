import csv
import json
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch

from openubem.gpusim.backends.numpy_ref import SimulationResult, run_stage_a_batch
from openubem.gpusim.backends.torch_batched import run_stage_b_batch
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

STAGE_B_CSV_PATH = REPO_ROOT / "openubem/outputs/gpusim_m2_stage_b.csv"
WEEK_DAYS = 7

STAGE_B_FIELDS = [
    "cell",
    "annual_stage_a_kwh",
    "annual_stage_b_kwh",
    "rel_b_vs_a",
    "dt_p999_k",
    "dt_max_k",
    "annual_eplus_kwh",
    "rel_b_vs_eplus",
    "cv_rmse",
    "nmbe",
    "week_stage_a_kwh",
    "week_mps_kwh",
    "week_rel_mps_vs_a",
    "week_dt_p999_k",
    "week_dt_max_k",
    "warmup_days_stage_a",
    "year_cpu_wall_seconds",
    "week_mps_wall_seconds",
]

_P1_REF_CACHE: dict[
    str,
    tuple[tuple[Path, ...], BatchSpec, list[WeatherSeries], SimulationResult],
] = {}


def _load_batch_and_weather(
    fixture_dirs: tuple[Path, ...],
) -> tuple[BatchSpec, list[WeatherSeries]]:
    """Compile a batch of golden fixture directories and load their weather.

    Args:
        fixture_dirs: Tuple of golden fixture directories.

    Returns:
        Tuple ``(batch, weathers)``.
    """
    expidf_paths = [d / "eplusout.expidf" for d in fixture_dirs]
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
    return batch, weathers


def _p1_fixture_dirs() -> tuple[Path, ...]:
    """Return the 12 P1 S0 golden fixture directories (3 cells + 9 variants).

    Returns:
        Tuple of 12 fixture paths in standard order.
    """
    cell_dirs = tuple(GOLDEN_ROOT / cid for cid in GOLDEN_CELL_IDS)
    var_dirs = tuple(
        GOLDEN_ROOT / "variants" / f"{CELL1_ID}__{vid}" for vid in S0_VARIANT_IDS
    )
    return cell_dirs + var_dirs


def _get_p1_reference() -> tuple[
    tuple[Path, ...], BatchSpec, list[WeatherSeries], SimulationResult
]:
    """Return compiled P1 batch, weather list, and cached Stage A reference.

    Returns:
        Tuple ``(dirs, batch, weathers, res_a)``.
    """
    cached = _P1_REF_CACHE.get("p1")
    if cached is None:
        dirs = _p1_fixture_dirs()
        batch, weathers = _load_batch_and_weather(dirs)
        res_a = run_stage_a_batch(batch, weathers, record_zone_temp=True)
        cached = (dirs, batch, weathers, res_a)
        _P1_REF_CACHE["p1"] = cached
    return cached


def _upsert_stage_b_csv(
    updates_by_cell: dict[str, dict[str, str]],
    cell_order: list[str],
) -> None:
    """Merge metric fields into ``openubem/outputs/gpusim_m2_stage_b.csv``.

    Args:
        updates_by_cell: Per-cell dict mapping CSV column names to formatted strings.
        cell_order: Ordered list of cell names to write as CSV rows.
    """
    existing: dict[str, dict[str, str]] = {}
    if STAGE_B_CSV_PATH.is_file():
        with STAGE_B_CSV_PATH.open("r", newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                cell_name = row.get("cell", "")
                if cell_name:
                    existing[cell_name] = {
                        k: str(row.get(k, "")) for k in STAGE_B_FIELDS
                    }

    STAGE_B_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STAGE_B_CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=STAGE_B_FIELDS)
        writer.writeheader()
        for cell in cell_order:
            merged = {k: "" for k in STAGE_B_FIELDS}
            if cell in existing:
                merged.update(existing[cell])
            merged["cell"] = cell
            merged.update(updates_by_cell[cell])
            writer.writerow(merged)


def _format_first_exceed(
    step_dt: np.ndarray,
    t_ref: np.ndarray,
    t_test: np.ndarray,
    h_ref: np.ndarray,
    h_test: np.ndarray,
    steps_per_hour: int,
    threshold_k: float = 0.02,
) -> str:
    """Format diagnostic details for the first timestep exceeding ``threshold_k``.

    Args:
        step_dt: Absolute temperature differences ``[T]``.
        t_ref: Reference zone mean air temperatures ``[T]``.
        t_test: Test zone mean air temperatures ``[T]``.
        h_ref: Reference hourly heating energies ``[H]``.
        h_test: Test hourly heating energies ``[H]``.
        steps_per_hour: Number of timesteps per hour.
        threshold_k: Temperature threshold in Kelvin.

    Returns:
        Formatted diagnostic string or empty string if never exceeded.
    """
    over_idx = np.where(step_dt > threshold_k)[0]
    if over_idx.size == 0:
        return ""
    first_step = int(over_idx[0])
    hr = first_step // steps_per_hour
    return (
        f" first_step_gt_{threshold_k:.2f}K={first_step} (hr={hr}): "
        f"t_a={t_ref[first_step]:.6f} C, "
        f"t_b={t_test[first_step]:.6f} C, "
        f"dt={step_dt[first_step]:.6f} K, "
        f"h_a={h_ref[hr]:.2f} J, "
        f"h_b={h_test[hr]:.2f} J"
    )


def test_stage_b_cpu_float64_equals_stage_a() -> None:
    """Verify Stage B on CPU float64 matches Stage A on the 3 golden cells."""
    dirs = tuple(GOLDEN_ROOT / cid for cid in GOLDEN_CELL_IDS)
    batch, weathers = _load_batch_and_weather(dirs)

    res_a = run_stage_a_batch(batch, weathers, record_zone_temp=True)
    res_b = run_stage_b_batch(
        batch,
        weathers,
        record_zone_temp=True,
        device="cpu",
        dtype=torch.float64,
    )

    assert res_a.zone_air_temp_c is not None
    assert res_b.zone_air_temp_c is not None
    assert res_a.zone_mean_air_temp_c is not None
    assert res_b.zone_mean_air_temp_c is not None

    assert np.array_equal(res_b.warmup_days, res_a.warmup_days), (
        f"Warmup mismatch: B={res_b.warmup_days.tolist()} "
        f"vs A={res_a.warmup_days.tolist()}"
    )

    ann_rel = np.abs(res_b.annual_heating_kwh - res_a.annual_heating_kwh) / np.maximum(
        np.abs(res_a.annual_heating_kwh), 1.0e-12
    )
    hourly_abs = np.abs(res_b.hourly_heating_j - res_a.hourly_heating_j)
    dt_air = np.abs(res_b.zone_air_temp_c - res_a.zone_air_temp_c)
    dt_mean = np.abs(res_b.zone_mean_air_temp_c - res_a.zone_mean_air_temp_c)

    max_ann_rel = float(np.max(ann_rel))
    max_hourly_j = float(np.max(hourly_abs))
    max_dt_k = float(max(np.max(dt_air), np.max(dt_mean)))

    print(
        f"T02 CPU float64 vs Stage A: "
        f"max_ann_rel={max_ann_rel:.3e}, "
        f"max_hourly_j={max_hourly_j:.3e} J, "
        f"max_dt_k={max_dt_k:.3e} K, "
        f"warmup_days={res_b.warmup_days.tolist()}"
    )

    assert max_ann_rel <= 1.0e-9, f"Annual rel diff {max_ann_rel:.3e} > 1e-9"
    assert max_hourly_j <= 1.0e-3, f"Hourly abs diff {max_hourly_j:.3e} J > 1e-3 J"
    assert max_dt_k <= 1.0e-8, f"Zone air dT max {max_dt_k:.3e} K > 1e-8 K"


def test_stage_b_cpu_float32_year_p1() -> None:
    """Verify full-year Stage B CPU float32 passes float32 and S0 gates on P1."""
    dirs, batch, weathers, res_a = _get_p1_reference()

    t0 = time.perf_counter()
    res_b = run_stage_b_batch(
        batch,
        weathers,
        record_zone_temp=True,
        device="cpu",
        dtype=torch.float32,
        force_warmup_days=res_a.warmup_days,
    )
    year_wall_s = time.perf_counter() - t0

    assert res_a.zone_mean_air_temp_c is not None
    assert res_b.zone_mean_air_temp_c is not None
    assert np.array_equal(res_b.warmup_days, res_a.warmup_days), (
        f"Warmup days not locked: B={res_b.warmup_days.tolist()} "
        f"vs A={res_a.warmup_days.tolist()}"
    )

    updates: dict[str, dict[str, str]] = {}
    metrics: list[dict[str, float | str]] = []
    failures: list[str] = []

    for bi, fdir in enumerate(dirs):
        cell = fdir.name
        floor_area = float(batch.zone_floor_area[bi])

        ann_a = float(res_a.annual_heating_kwh[bi])
        ann_b = float(res_b.annual_heating_kwh[bi])
        denom_a = ann_a if abs(ann_a) > 1.0e-12 else 1.0e-12
        rel_b_vs_a = (ann_b - ann_a) / denom_a
        abs_b_vs_a_kwh_m2 = abs(ann_b - ann_a) / floor_area

        dt_ba = np.abs(res_b.zone_mean_air_temp_c[bi] - res_a.zone_mean_air_temp_c[bi])
        dt_p999_ba = float(np.percentile(dt_ba, 99.9))
        dt_max_ba = float(np.max(dt_ba))

        tbl = pq.read_table(fdir / "timestep.parquet")
        e_ts = tbl[ENERGY_COL].to_numpy()
        t_ep = tbl[ZONE_MEAN_TEMP_COL].to_numpy()
        h_ep = e_ts.reshape(8760, batch.steps_per_hour).sum(axis=1)
        h_b = res_b.hourly_heating_j[bi]

        ann_ep = float(np.sum(h_ep, dtype=np.float64) / 3.6e6)
        rel_b_vs_ep = (ann_b - ann_ep) / ann_ep
        abs_b_vs_ep_kwh_m2 = abs(ann_b - ann_ep) / floor_area

        thr_j = 1.0 * floor_area * 3600.0
        active = (h_ep > thr_j) | (h_b > thr_j)
        diff_h = h_b[active] - h_ep[active]
        mean_ep = float(np.mean(h_ep[active]))
        cv_rmse = float(np.sqrt(np.mean(diff_h * diff_h)) / mean_ep)
        nmbe = float(np.mean(diff_h) / mean_ep)

        dt_ep = np.abs(res_b.zone_mean_air_temp_c[bi] - t_ep)
        dt_p999_ep = float(np.percentile(dt_ep, 99.9))
        dt_max_ep = float(np.max(dt_ep))

        updates[cell] = {
            "annual_stage_a_kwh": f"{ann_a:.6f}",
            "annual_stage_b_kwh": f"{ann_b:.6f}",
            "rel_b_vs_a": f"{rel_b_vs_a:.8e}",
            "dt_p999_k": f"{dt_p999_ba:.6f}",
            "dt_max_k": f"{dt_max_ba:.6f}",
            "annual_eplus_kwh": f"{ann_ep:.6f}",
            "rel_b_vs_eplus": f"{rel_b_vs_ep:.8e}",
            "cv_rmse": f"{cv_rmse:.8e}",
            "nmbe": f"{nmbe:.8e}",
            "warmup_days_stage_a": str(int(res_a.warmup_days[bi])),
            "year_cpu_wall_seconds": f"{year_wall_s:.3f}",
        }
        metrics.append(
            {
                "cell": cell,
                "rel_b_vs_a": abs(rel_b_vs_a),
                "dt_p999_k": dt_p999_ba,
                "dt_max_k": dt_max_ba,
                "rel_b_vs_eplus": abs(rel_b_vs_ep),
                "cv_rmse": cv_rmse,
                "nmbe": abs(nmbe),
                "dt_p999_ep_k": dt_p999_ep,
                "dt_max_ep_k": dt_max_ep,
            }
        )

        if not (abs(rel_b_vs_a) <= 5.0e-4 or abs_b_vs_a_kwh_m2 <= 0.01):
            failures.append(
                f"{cell} float32 annual gate: rel={rel_b_vs_a:.6e}, "
                f"abs={abs_b_vs_a_kwh_m2:.6f} kWh/m2"
            )
        if dt_p999_ba > 0.02 or dt_max_ba > 0.10:
            extra = _format_first_exceed(
                dt_ba,
                res_a.zone_mean_air_temp_c[bi],
                res_b.zone_mean_air_temp_c[bi],
                res_a.hourly_heating_j[bi],
                h_b,
                batch.steps_per_hour,
            )
            failures.append(
                f"{cell} float32 dT gate: p99.9={dt_p999_ba:.6f} K, "
                f"max={dt_max_ba:.6f} K.{extra}"
            )
        if not (abs(rel_b_vs_ep) <= 0.005 or abs_b_vs_ep_kwh_m2 <= 0.05):
            failures.append(
                f"{cell} S0 annual vs E+ gate: rel={rel_b_vs_ep:.6e}, "
                f"abs={abs_b_vs_ep_kwh_m2:.6f} kWh/m2"
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

    _upsert_stage_b_csv(updates, [d.name for d in dirs])
    assert STAGE_B_CSV_PATH.is_file()

    w_rel_ba = max(metrics, key=lambda r: float(r["rel_b_vs_a"]))
    w_p999_ba = max(metrics, key=lambda r: float(r["dt_p999_k"]))
    w_max_ba = max(metrics, key=lambda r: float(r["dt_max_k"]))
    w_rel_ep = max(metrics, key=lambda r: float(r["rel_b_vs_eplus"]))
    w_cv = max(metrics, key=lambda r: float(r["cv_rmse"]))
    w_nmbe = max(metrics, key=lambda r: float(r["nmbe"]))
    w_p999_ep = max(metrics, key=lambda r: float(r["dt_p999_ep_k"]))
    w_max_ep = max(metrics, key=lambda r: float(r["dt_max_ep_k"]))

    print(
        f"T03 CPU float32 year P1 (B=12) wall={year_wall_s:.3f} s | "
        f"worst |rel_b_vs_a|={float(w_rel_ba['rel_b_vs_a']):.3e} "
        f"({w_rel_ba['cell']}), "
        f"worst dt_p999_ba={float(w_p999_ba['dt_p999_k']):.6f} K "
        f"({w_p999_ba['cell']}), "
        f"worst dt_max_ba={float(w_max_ba['dt_max_k']):.6f} K "
        f"({w_max_ba['cell']}), "
        f"worst |rel_b_vs_eplus|={float(w_rel_ep['rel_b_vs_eplus']):.3e} "
        f"({w_rel_ep['cell']}), "
        f"worst cv_rmse={float(w_cv['cv_rmse']):.3e} ({w_cv['cell']}), "
        f"worst |nmbe|={float(w_nmbe['nmbe']):.3e} ({w_nmbe['cell']}), "
        f"worst dt_p999_ep={float(w_p999_ep['dt_p999_ep_k']):.6f} K "
        f"({w_p999_ep['cell']}), "
        f"worst dt_max_ep={float(w_max_ep['dt_max_ep_k']):.6f} K "
        f"({w_max_ep['cell']})"
    )

    assert not failures, "T03 year CPU float32 failures:\n" + "\n".join(failures)


def test_stage_b_mps_float32_week_p1() -> None:
    """Verify 7-day Stage B MPS float32 passes the float32 gate on all 12 P1."""
    assert torch.backends.mps.is_available(), "MPS device is required for T03"
    dirs, batch, weathers, res_a = _get_p1_reference()

    week_hours = WEEK_DAYS * 24
    week_steps = week_hours * batch.steps_per_hour

    torch.mps.synchronize()
    t0 = time.perf_counter()
    res_mps = run_stage_b_batch(
        batch,
        weathers,
        record_zone_temp=True,
        device="mps",
        dtype=torch.float32,
        force_warmup_days=res_a.warmup_days,
        run_days=WEEK_DAYS,
    )
    torch.mps.synchronize()
    week_wall_s = time.perf_counter() - t0

    assert res_a.zone_mean_air_temp_c is not None
    assert res_mps.zone_mean_air_temp_c is not None
    assert res_mps.hourly_heating_j.shape == (len(dirs), week_hours)
    assert res_mps.zone_mean_air_temp_c.shape == (len(dirs), week_steps)
    assert np.array_equal(res_mps.warmup_days, res_a.warmup_days), (
        f"Warmup days not locked: B={res_mps.warmup_days.tolist()} "
        f"vs A={res_a.warmup_days.tolist()}"
    )

    updates: dict[str, dict[str, str]] = {}
    metrics: list[dict[str, float | str]] = []
    failures: list[str] = []

    for bi, fdir in enumerate(dirs):
        cell = fdir.name
        floor_area = float(batch.zone_floor_area[bi])

        h_a_week = res_a.hourly_heating_j[bi, :week_hours]
        h_mps_week = res_mps.hourly_heating_j[bi]
        week_a_kwh = float(np.sum(h_a_week, dtype=np.float64) / 3.6e6)
        week_mps_kwh = float(res_mps.annual_heating_kwh[bi])
        denom_a = week_a_kwh if abs(week_a_kwh) > 1.0e-12 else 1.0e-12
        week_rel = (week_mps_kwh - week_a_kwh) / denom_a
        week_abs_kwh_m2 = abs(week_mps_kwh - week_a_kwh) / floor_area

        t_a_week = res_a.zone_mean_air_temp_c[bi, :week_steps]
        t_mps_week = res_mps.zone_mean_air_temp_c[bi]
        dt_week = np.abs(t_mps_week - t_a_week)
        week_dt_p999 = float(np.percentile(dt_week, 99.9))
        week_dt_max = float(np.max(dt_week))

        updates[cell] = {
            "week_stage_a_kwh": f"{week_a_kwh:.6f}",
            "week_mps_kwh": f"{week_mps_kwh:.6f}",
            "week_rel_mps_vs_a": f"{week_rel:.8e}",
            "week_dt_p999_k": f"{week_dt_p999:.6f}",
            "week_dt_max_k": f"{week_dt_max:.6f}",
            "warmup_days_stage_a": str(int(res_a.warmup_days[bi])),
            "week_mps_wall_seconds": f"{week_wall_s:.3f}",
        }
        metrics.append(
            {
                "cell": cell,
                "week_rel_mps_vs_a": abs(week_rel),
                "week_dt_p999_k": week_dt_p999,
                "week_dt_max_k": week_dt_max,
            }
        )

        if not (abs(week_rel) <= 5.0e-4 or week_abs_kwh_m2 <= 0.01):
            failures.append(
                f"{cell} MPS week heating gate: rel={week_rel:.6e}, "
                f"abs={week_abs_kwh_m2:.6f} kWh/m2"
            )
        if week_dt_p999 > 0.02 or week_dt_max > 0.10:
            extra = _format_first_exceed(
                dt_week,
                t_a_week,
                t_mps_week,
                h_a_week,
                h_mps_week,
                batch.steps_per_hour,
            )
            failures.append(
                f"{cell} MPS week dT gate: p99.9={week_dt_p999:.6f} K, "
                f"max={week_dt_max:.6f} K.{extra}"
            )

    _upsert_stage_b_csv(updates, [d.name for d in dirs])
    assert STAGE_B_CSV_PATH.is_file()

    w_rel = max(metrics, key=lambda r: float(r["week_rel_mps_vs_a"]))
    w_p999 = max(metrics, key=lambda r: float(r["week_dt_p999_k"]))
    w_max = max(metrics, key=lambda r: float(r["week_dt_max_k"]))

    print(
        f"T03 MPS float32 week P1 (B=12, 7d) wall={week_wall_s:.3f} s | "
        f"worst |week_rel_mps_vs_a|={float(w_rel['week_rel_mps_vs_a']):.3e} "
        f"({w_rel['cell']}), "
        f"worst week_dt_p999={float(w_p999['week_dt_p999_k']):.6f} K "
        f"({w_p999['cell']}), "
        f"worst week_dt_max={float(w_max['week_dt_max_k']):.6f} K "
        f"({w_max['cell']})"
    )

    assert not failures, "T03 week MPS float32 failures:\n" + "\n".join(failures)
