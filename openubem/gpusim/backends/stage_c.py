from collections.abc import Sequence
import time
from typing import Any, Callable

import numpy as np
import torch

from openubem.gpusim.backends.kernel.pack import (
    T_REF_C,
    WU_STAT_MAX_H_RATE,
    WU_STAT_MAX_T_DT,
    WU_STAT_MIN_T_DT,
    PackedBatch,
    deduplicate_weather,
    pack,
)
from openubem.gpusim.backends.kernel.s0_metal import (
    compile_metal_s0_shader,
    launch_s0_chunk_mps,
    update_active_mask_mps,
    upload_packed_to_mps,
)
from openubem.gpusim.backends.numpy_ref import (
    MIN_TIME_STEP_SYS_HR,
    WARMUP_MIN_LOAD,
    SimulationResult,
)
from openubem.gpusim.compile import BatchSpec
from openubem.gpusim.ctf import CtfCoefficients
from openubem.gpusim.weather import WeatherSeries


def _resolve_device_hooks(
    device: str,
) -> tuple[
    Callable[[], Any],
    Callable[[PackedBatch, bool], Any],
    Callable[[Any, np.ndarray], None],
    Callable[..., None],
    Callable[[], None],
]:
    """Return backend-specific compile, upload, mask, launch, and sync hooks."""
    if device == "mps":
        if not torch.backends.mps.is_available():
            raise RuntimeError("Stage C Metal backend requires Apple MPS")
        return (
            compile_metal_s0_shader,
            upload_packed_to_mps,
            update_active_mask_mps,
            lambda lib, bufs, **kw: launch_s0_chunk_mps(lib=lib, bufs=bufs, **kw),
            torch.mps.synchronize,
        )
    if device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("Stage C CUDA backend requires an available CUDA GPU")
        from openubem.gpusim.backends.kernel.s0_cuda import (
            compile_cuda_s0_kernel,
            launch_s0_chunk_cuda,
            update_active_mask_cuda,
            upload_packed_to_cuda,
        )

        return (
            compile_cuda_s0_kernel,
            upload_packed_to_cuda,
            update_active_mask_cuda,
            lambda lib, bufs, **kw: launch_s0_chunk_cuda(kernel=lib, bufs=bufs, **kw),
            torch.cuda.synchronize,
        )
    raise ValueError(f"Unsupported Stage C device {device!r}; expected 'mps' or 'cuda'")


def run_packed_stage_c(
    packed: PackedBatch,
    cell_ids: list[str],
    record_zone_temp: bool = False,
    force_warmup_days: Sequence[int] | np.ndarray | None = None,
    run_chunk_days: int = 1,
    device: str = "mps",
) -> tuple[SimulationResult, dict[str, float]]:
    """Execute a packed Stage C batch on MPS or CUDA with phase and launch timings.

    Args:
        packed: Host ``PackedBatch`` built by ``pack``.
        cell_ids: Building identifiers matching batch order.
        record_zone_temp: If True, download per-timestep zone temperatures.
        force_warmup_days: Optional per-building warm-up day counts ``[B]``.
        run_chunk_days: Number of simulation days per run-period kernel launch.
        device: Target GPU backend (``"mps"`` or ``"cuda"``).

    Returns:
        Tuple ``(SimulationResult, timings_dict)`` where ``timings_dict``
        reports ``upload_s``, ``gpu_s``, ``download_s``, and ``max_launch_s``.

    Raises:
        RuntimeError: If the requested GPU device is unavailable.
        ValueError: If ``device``, ``run_chunk_days``, or ``force_warmup_days`` is invalid.
    """
    compile_fn, upload_fn, update_mask_fn, launch_fn, sync_fn = _resolve_device_hooks(
        device
    )
    if run_chunk_days <= 0:
        raise ValueError(f"run_chunk_days must be positive, got {run_chunk_days}")

    b_size = packed.batch_size
    sph = packed.steps_per_hour
    steps_per_day = 24 * sph
    dt_zone_hr = 1.0 / float(sph)
    limit_num_sys = max(1, int(round(dt_zone_hr / MIN_TIME_STEP_SYS_HR)))

    lib = compile_fn()
    sync_fn()
    t_up0 = time.perf_counter()
    bufs = upload_fn(packed, record_zone_temp)
    sync_fn()
    upload_s = time.perf_counter() - t_up0

    wu_min = packed.bldg_i[1]
    wu_max = packed.bldg_i[2]
    loads_tol = packed.bldg_f[12].astype(np.float64)
    temp_tol = packed.bldg_f[13].astype(np.float64)

    max_launch_s = 0.0
    t_gpu0 = time.perf_counter()

    if force_warmup_days is not None:
        forced = np.asarray(force_warmup_days, dtype=np.int32).reshape(-1)
        if forced.shape != (b_size,):
            raise ValueError(
                f"Expected force_warmup_days shape ({b_size},), got {forced.shape}"
            )
        warmup_days = forced.copy()
        max_wu_days = int(np.max(forced)) if b_size > 0 else 0
        for day in range(1, max_wu_days + 1):
            still_warming = forced >= day
            if not bool(np.any(still_warming)):
                break
            update_mask_fn(bufs, still_warming)
            t_l0 = time.perf_counter()
            launch_fn(
                lib,
                bufs,
                step_start=0,
                step_end=steps_per_day,
                is_warmup=True,
                warmup_day=day,
                record_zone_temp=False,
                rec_step_offset=0,
                limit_num_sys=limit_num_sys,
            )
            sync_fn()
            l_s = time.perf_counter() - t_l0
            if l_s > max_launch_s:
                max_launch_s = l_s
    else:
        max_wu_days = int(np.max(wu_max))
        still_warming = np.ones(b_size, dtype=bool)
        warmup_days = np.zeros(b_size, dtype=np.int32)
        max_t_prev = np.full(b_size, -9999.0, dtype=np.float64)
        min_t_prev = np.full(b_size, 1000.0, dtype=np.float64)
        max_h_prev = np.full(b_size, -9999.0, dtype=np.float64)

        for day in range(1, max_wu_days + 1):
            if not bool(np.any(still_warming)):
                break
            update_mask_fn(bufs, still_warming)
            t_l0 = time.perf_counter()
            launch_fn(
                lib,
                bufs,
                step_start=0,
                step_end=steps_per_day,
                is_warmup=True,
                warmup_day=day,
                record_zone_temp=False,
                rec_step_offset=0,
                limit_num_sys=limit_num_sys,
            )
            sync_fn()
            l_s = time.perf_counter() - t_l0
            if l_s > max_launch_s:
                max_launch_s = l_s

            stats_cpu = bufs.wu_stats.cpu().numpy().astype(np.float64)
            max_t_day = stats_cpu[WU_STAT_MAX_T_DT] + T_REF_C
            min_t_day = stats_cpu[WU_STAT_MIN_T_DT] + T_REF_C
            max_h_day = stats_cpu[WU_STAT_MAX_H_RATE]

            pass_max_t = np.abs(max_t_prev - max_t_day) <= temp_tol
            pass_min_t = np.abs(min_t_prev - min_t_day) <= temp_tol

            eff_h_day = np.abs(np.maximum(max_h_day, WARMUP_MIN_LOAD))
            eff_h_prev = np.abs(np.maximum(max_h_prev, WARMUP_MIN_LOAD))
            rel_h_diff = np.abs((eff_h_day - eff_h_prev) / eff_h_day)
            pass_h = np.where(
                max_h_day > 1.0e-4,
                rel_h_diff <= loads_tol,
                True,
            )

            converged_now = still_warming & (
                (pass_max_t & pass_min_t & pass_h & (day >= wu_min))
                | (day >= wu_max)
            )
            warmup_days = np.where(converged_now, day, warmup_days)
            still_warming = still_warming & (~converged_now)

            max_t_prev = np.where(still_warming, max_t_day, max_t_prev)
            min_t_prev = np.where(still_warming, min_t_day, min_t_prev)
            max_h_prev = np.where(still_warming, eff_h_day, max_h_prev)

    chunk_steps = run_chunk_days * steps_per_day
    n_run_steps = packed.n_run_steps
    for step_start in range(0, n_run_steps, chunk_steps):
        step_end = min(step_start + chunk_steps, n_run_steps)
        t_l0 = time.perf_counter()
        launch_fn(
            lib,
            bufs,
            step_start=step_start,
            step_end=step_end,
            is_warmup=False,
            warmup_day=0,
            record_zone_temp=record_zone_temp,
            rec_step_offset=0,
            limit_num_sys=limit_num_sys,
        )
        sync_fn()
        l_s = time.perf_counter() - t_l0
        if l_s > max_launch_s:
            max_launch_s = l_s

    gpu_s = time.perf_counter() - t_gpu0

    t_dl0 = time.perf_counter()
    hourly_heating_j = np.ascontiguousarray(
        bufs.hourly_heating_j.cpu().numpy().T.astype(np.float64)
    )
    annual_kwh = np.sum(hourly_heating_j, axis=1, dtype=np.float64) / 3.6e6
    z_temp_rec: np.ndarray | None = None
    z_mean_rec: np.ndarray | None = None
    if record_zone_temp:
        z_temp_rec = np.ascontiguousarray(
            bufs.zone_t_rec.cpu().numpy().T.astype(np.float64) + T_REF_C
        )
        z_mean_rec = np.ascontiguousarray(
            bufs.zone_ztav_rec.cpu().numpy().T.astype(np.float64) + T_REF_C
        )
    download_s = time.perf_counter() - t_dl0

    res = SimulationResult(
        cell_ids=list(cell_ids),
        hourly_heating_j=hourly_heating_j,
        annual_heating_kwh=annual_kwh,
        warmup_days=warmup_days,
        zone_air_temp_c=z_temp_rec,
        zone_mean_air_temp_c=z_mean_rec,
    )
    timings = {
        "upload_s": float(upload_s),
        "gpu_s": float(gpu_s),
        "download_s": float(download_s),
        "max_launch_s": float(max_launch_s),
    }
    return res, timings


def run_packed_stage_c_mps(
    packed: PackedBatch,
    cell_ids: list[str],
    record_zone_temp: bool = False,
    force_warmup_days: Sequence[int] | np.ndarray | None = None,
    run_chunk_days: int = 1,
) -> tuple[SimulationResult, dict[str, float]]:
    """Execute a packed Stage C batch on MPS with phase and launch timings."""
    return run_packed_stage_c(
        packed=packed,
        cell_ids=cell_ids,
        record_zone_temp=record_zone_temp,
        force_warmup_days=force_warmup_days,
        run_chunk_days=run_chunk_days,
        device="mps",
    )


def run_packed_stage_c_cuda(
    packed: PackedBatch,
    cell_ids: list[str],
    record_zone_temp: bool = False,
    force_warmup_days: Sequence[int] | np.ndarray | None = None,
    run_chunk_days: int = 1,
) -> tuple[SimulationResult, dict[str, float]]:
    """Execute a packed Stage C batch on CUDA with phase and launch timings."""
    return run_packed_stage_c(
        packed=packed,
        cell_ids=cell_ids,
        record_zone_temp=record_zone_temp,
        force_warmup_days=force_warmup_days,
        run_chunk_days=run_chunk_days,
        device="cuda",
    )


def run_stage_c_batch(
    batch: BatchSpec,
    weather: WeatherSeries | list[WeatherSeries],
    ctf: CtfCoefficients | None = None,
    record_zone_temp: bool = False,
    force_warmup_days: Sequence[int] | np.ndarray | None = None,
    run_chunk_days: int = 1,
    device: str = "mps",
) -> SimulationResult:
    """Run batched S0 simulation using the chunked Stage C kernel (MPS or CUDA).

    Args:
        batch: Compiled ``BatchSpec`` of shape ``[B, S]``.
        weather: Shared ``WeatherSeries`` or list of ``B`` ``WeatherSeries``.
        ctf: Optional internal-mass CTF coefficients (defaults to golden ``.eio``).
        record_zone_temp: If True, record per-timestep zone temperatures ``[B, T]``.
        force_warmup_days: Optional per-building warm-up day counts ``[B]``.
        run_chunk_days: Number of simulation days per run-period GPU launch.
        device: Target GPU backend (``"mps"`` or ``"cuda"``).

    Returns:
        ``SimulationResult`` matching Stage A outputs.
    """
    weather_by_site, site_index = deduplicate_weather(weather, batch.batch_size)
    packed = pack(batch, weather_by_site, site_index, ctf=ctf)
    res, _ = run_packed_stage_c(
        packed=packed,
        cell_ids=batch.cell_ids,
        record_zone_temp=record_zone_temp,
        force_warmup_days=force_warmup_days,
        run_chunk_days=run_chunk_days,
        device=device,
    )
    return res
