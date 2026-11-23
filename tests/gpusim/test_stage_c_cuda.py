import csv
import time

import numpy as np
import pyarrow.parquet as pq

from openubem.gpusim.backends.kernel.pack import deduplicate_weather, pack
from openubem.gpusim.backends.stage_c import run_packed_stage_c, run_stage_c_batch
from tests.gpusim.test_cells import (
    ENERGY_COL,
    GOLDEN_CELL_IDS,
    GOLDEN_ROOT,
    REPO_ROOT,
    ZONE_MEAN_TEMP_COL,
)
from tests.gpusim.test_stage_c import (
    CELLS_M3_CSV_PATH,
    M3_CELLS_FIELDS,
    _format_first_exceed,
    _load_batch_and_weather,
    _load_or_build_stage_a_p1_cache,
    _p1_fixture_dirs,
)

CELLS_M4_CSV_PATH = REPO_ROOT / "openubem/outputs/gpusim_m4_cells.csv"
M4_CELLS_FIELDS = [
    *M3_CELLS_FIELDS,
    "annual_stage_c_metal_kwh",
    "rel_cuda_vs_metal",
]


def _load_metal_annual_map() -> dict[str, float]:
    """Load Mac Stage C Metal annual heating totals from M3 results CSV."""
    out: dict[str, float] = {}
    with CELLS_M3_CSV_PATH.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            out[row["cell"]] = float(row["annual_stage_c_kwh"])
    return out


def test_smoke() -> None:
    """Verify 3 golden cells run through Stage C CUDA with 8,760 finite hours."""
    dirs = tuple(GOLDEN_ROOT / cid for cid in GOLDEN_CELL_IDS)
    batch, weathers = _load_batch_and_weather(dirs)
    weather_by_site, site_index = deduplicate_weather(weathers, batch.batch_size)
    packed = pack(batch, weather_by_site, site_index)

    t0 = time.perf_counter()
    res, timings = run_packed_stage_c(
        packed=packed,
        cell_ids=batch.cell_ids,
        record_zone_temp=False,
        force_warmup_days=None,
        run_chunk_days=1,
        device="cuda",
    )
    wall_s = time.perf_counter() - t0

    assert res.hourly_heating_j.shape == (len(dirs), 8760)
    assert np.all(np.isfinite(res.hourly_heating_j))
    assert np.all(np.isfinite(res.annual_heating_kwh))
    assert np.all(res.annual_heating_kwh > 0.0)
    assert timings["max_launch_s"] < 0.2, (
        f"Longest launch {timings['max_launch_s']:.4f} s exceeds 0.2 s TDR budget"
    )

    print(
        f"T02 Stage C CUDA smoke (B={len(dirs)}): wall={wall_s:.3f} s, "
        f"gpu={timings['gpu_s']:.3f} s, max_launch={timings['max_launch_s']:.5f} s, "
        f"warmup_days={res.warmup_days.tolist()}, "
        f"annual_kwh={[round(float(x), 2) for x in res.annual_heating_kwh]}"
    )


def test_p1() -> None:
    """Verify Stage C CUDA passes float32 and S0 gates across all 12 P1 cases."""
    dirs = _p1_fixture_dirs()
    batch, weathers = _load_batch_and_weather(dirs)
    res_a = _load_or_build_stage_a_p1_cache(batch, weathers)
    assert res_a.zone_mean_air_temp_c is not None
    metal_annual = _load_metal_annual_map()

    t0 = time.perf_counter()
    res_locked = run_stage_c_batch(
        batch,
        weathers,
        record_zone_temp=True,
        force_warmup_days=res_a.warmup_days,
        run_chunk_days=1,
        device="cuda",
    )
    res_free = run_stage_c_batch(
        batch,
        weathers,
        record_zone_temp=True,
        force_warmup_days=None,
        run_chunk_days=1,
        device="cuda",
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

        ann_metal = metal_annual[cell]
        rel_cuda_vs_metal = (ann_c_locked - ann_metal) / ann_metal

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
                "annual_stage_c_metal_kwh": f"{ann_metal:.6f}",
                "rel_cuda_vs_metal": f"{rel_cuda_vs_metal:.8e}",
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
                "rel_cuda_vs_metal": abs(rel_cuda_vs_metal),
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

    CELLS_M4_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CELLS_M4_CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=M4_CELLS_FIELDS)
        writer.writeheader()
        writer.writerows(rows_csv)
    assert CELLS_M4_CSV_PATH.is_file()

    w_rel_ca = max(metrics, key=lambda r: float(r["rel_c_vs_a"]))
    w_p999_ca = max(metrics, key=lambda r: float(r["dt_p999_k"]))
    w_max_ca = max(metrics, key=lambda r: float(r["dt_max_k"]))
    w_rel_ep = max(metrics, key=lambda r: float(r["rel_c_vs_eplus"]))
    w_cv = max(metrics, key=lambda r: float(r["cv_rmse"]))
    w_nmbe = max(metrics, key=lambda r: float(r["nmbe"]))
    w_p999_ep = max(metrics, key=lambda r: float(r["dt_p999_eplus_k"]))
    w_max_ep = max(metrics, key=lambda r: float(r["dt_max_eplus_k"]))
    w_cm = max(metrics, key=lambda r: float(r["rel_cuda_vs_metal"]))

    print(
        f"T03 Stage C CUDA P1 (B=12, locked+free) wall={wall_s:.3f} s | "
        f"worst |rel_c_vs_a|={float(w_rel_ca['rel_c_vs_a']):.3e} ({w_rel_ca['cell']}), "
        f"worst dt_p999_k={float(w_p999_ca['dt_p999_k']):.6f} K ({w_p999_ca['cell']}), "
        f"worst dt_max_k={float(w_max_ca['dt_max_k']):.6f} K ({w_max_ca['cell']}), "
        f"worst |rel_c_vs_eplus|={float(w_rel_ep['rel_c_vs_eplus']):.3e} ({w_rel_ep['cell']}), "
        f"worst cv_rmse={float(w_cv['cv_rmse']):.3e} ({w_cv['cell']}), "
        f"worst |nmbe|={float(w_nmbe['nmbe']):.3e} ({w_nmbe['cell']}), "
        f"worst dt_p999_eplus_k={float(w_p999_ep['dt_p999_eplus_k']):.6f} K ({w_p999_ep['cell']}), "
        f"worst dt_max_eplus_k={float(w_max_ep['dt_max_eplus_k']):.6f} K ({w_max_ep['cell']}), "
        f"worst |rel_cuda_vs_metal|={float(w_cm['rel_cuda_vs_metal']):.3e} ({w_cm['cell']})"
    )

    assert not failures, "T03 Stage C CUDA P1 failures:\n" + "\n".join(failures)
