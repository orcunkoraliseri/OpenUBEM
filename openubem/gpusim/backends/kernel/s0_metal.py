from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import torch

from openubem.gpusim.backends.kernel.pack import PackedBatch

HEADER_PATH: Path = Path(__file__).with_name("s0_common.h")

PI_COUNT: int = 13

_METAL_PREFIX: str = """#include <metal_stdlib>
using namespace metal;
#define GPUSIM_FN inline
#define GPUSIM_GLOBAL device
#define GPUSIM_GLOBAL_CONST device const
#define GPUSIM_THREAD thread
#define GPUSIM_POW pow
#define GPUSIM_EXP exp
#define GPUSIM_LOG log
"""

_METAL_WRAPPER: str = """
kernel void s0_run_chunk(
    device const float* bldg_f [[buffer(0)]],
    device const int* bldg_i [[buffer(1)]],
    device const float* surf_f [[buffer(2)]],
    device const int* surf_flags [[buffer(3)]],
    device const float* script_f_sigma [[buffer(4)]],
    device const float* ctf_vec [[buffer(5)]],
    device const float* weather_buf [[buffer(6)]],
    device const float* sched_gain_w [[buffer(7)]],
    device float* state_zone_f [[buffer(8)]],
    device int* state_num_sys_last [[buffer(9)]],
    device float* state_surf_f [[buffer(10)]],
    device float* state_ctf_hist [[buffer(11)]],
    device const int* active_mask [[buffer(12)]],
    device float* wu_stats [[buffer(13)]],
    device float* hourly_heating_j [[buffer(14)]],
    device float* zone_t_rec [[buffer(15)]],
    device float* zone_ztav_rec [[buffer(16)]],
    device const int* params_i [[buffer(17)]],
    uint tid [[thread_position_in_grid]]
) {
    int b = (int)tid;
    if (b >= params_i[PI_B_SIZE]) {
        return;
    }
    s0_run_chunk_core(
        b,
        bldg_f,
        bldg_i,
        surf_f,
        surf_flags,
        script_f_sigma,
        ctf_vec,
        weather_buf,
        sched_gain_w,
        state_zone_f,
        state_num_sys_last,
        state_surf_f,
        state_ctf_hist,
        active_mask,
        wu_stats,
        hourly_heating_j,
        zone_t_rec,
        zone_ztav_rec,
        params_i
    );
}
"""


@dataclass
class MetalDeviceBuffers:
    """Resident PyTorch MPS tensors for a packed Stage C simulation batch.

    Attributes:
        batch_size: Number of buildings in batch.
        max_surfaces: Padded surface count.
        n_sites: Distinct weather site count.
        n_ctf_hist: CTF history order.
        steps_per_hour: Zone timesteps per hour.
        n_run_steps: Number of run-period timesteps.
        n_wu_steps: Number of warm-up timesteps per day.
        bldg_f: Device tensor ``[BF_COUNT, B]``.
        bldg_i: Device tensor ``[BI_COUNT, B]``.
        surf_f: Device tensor ``[SS_COUNT, S, B]``.
        surf_flags: Device tensor ``[S, B]``.
        script_f_sigma: Device tensor ``[S, S, B]``.
        ctf_vec: Device tensor ``[4*M + 2]``.
        weather_run: Device tensor ``[WF_COUNT, T_run, K]``.
        weather_wu: Device tensor ``[WF_COUNT, T_wu, K]``.
        sched_gain_w: Device tensor ``[8760, B]``.
        state_zone_f: Device tensor ``[ZS_COUNT, B]``.
        state_num_sys_last: Device tensor ``[B]``.
        state_surf_f: Device tensor ``[ST_COUNT, S, B]``.
        state_ctf_hist: Device tensor ``[CH_COUNT, M, S, B]``.
        active_mask: Device int32 warm-up active mask ``[B]``.
        wu_stats: Device warm-up daily min/max buffer ``[WU_STAT_COUNT, B]``.
        hourly_heating_j: Device hourly output buffer ``[n_hours, B]``.
        zone_t_rec: Device zone MAT trajectory buffer (or 1-element dummy).
        zone_ztav_rec: Device zone ZTAV trajectory buffer (or 1-element dummy).
        params_i: Device integer launch parameter vector ``[PI_COUNT]``.
    """

    batch_size: int
    max_surfaces: int
    n_sites: int
    n_ctf_hist: int
    steps_per_hour: int
    n_run_steps: int
    n_wu_steps: int
    bldg_f: torch.Tensor
    bldg_i: torch.Tensor
    surf_f: torch.Tensor
    surf_flags: torch.Tensor
    script_f_sigma: torch.Tensor
    ctf_vec: torch.Tensor
    weather_run: torch.Tensor
    weather_wu: torch.Tensor
    sched_gain_w: torch.Tensor
    state_zone_f: torch.Tensor
    state_num_sys_last: torch.Tensor
    state_surf_f: torch.Tensor
    state_ctf_hist: torch.Tensor
    active_mask: torch.Tensor
    wu_stats: torch.Tensor
    hourly_heating_j: torch.Tensor
    zone_t_rec: torch.Tensor
    zone_ztav_rec: torch.Tensor
    params_i: torch.Tensor


def build_metal_s0_source() -> str:
    """Assemble the Stage C Metal shader source from ``s0_common.h``.

    Returns:
        Complete Metal Shading Language source string.
    """
    header_text = HEADER_PATH.read_text(encoding="utf-8")
    return f"{_METAL_PREFIX}\n{header_text}\n{_METAL_WRAPPER}"


@lru_cache(maxsize=1)
def compile_metal_s0_shader() -> Any:
    """Compile and cache the Stage C Metal kernel via PyTorch MPS.

    Returns:
        Compiled MPS shader library exposing ``s0_run_chunk``.
    """
    return torch.mps.compile_shader(build_metal_s0_source())


def upload_packed_to_mps(
    packed: PackedBatch,
    record_zone_temp: bool = False,
) -> MetalDeviceBuffers:
    """Upload a ``PackedBatch`` once onto the Apple MPS device.

    Args:
        packed: Host ``PackedBatch`` container.
        record_zone_temp: If True, allocate per-timestep zone temperature buffers.

    Returns:
        ``MetalDeviceBuffers`` holding resident MPS tensors.
    """
    dev = torch.device("mps")
    b_size = packed.batch_size
    n_run = packed.n_run_steps
    if record_zone_temp:
        zone_t_rec = torch.empty((n_run, b_size), dtype=torch.float32, device=dev)
        zone_ztav_rec = torch.empty((n_run, b_size), dtype=torch.float32, device=dev)
    else:
        zone_t_rec = torch.empty((1,), dtype=torch.float32, device=dev)
        zone_ztav_rec = torch.empty((1,), dtype=torch.float32, device=dev)

    return MetalDeviceBuffers(
        batch_size=b_size,
        max_surfaces=packed.max_surfaces,
        n_sites=packed.n_sites,
        n_ctf_hist=packed.n_ctf_hist,
        steps_per_hour=packed.steps_per_hour,
        n_run_steps=n_run,
        n_wu_steps=packed.n_wu_steps,
        bldg_f=torch.from_numpy(packed.bldg_f).to(dev),
        bldg_i=torch.from_numpy(packed.bldg_i).to(dev),
        surf_f=torch.from_numpy(packed.surf_f).to(dev),
        surf_flags=torch.from_numpy(packed.surf_flags).to(dev),
        script_f_sigma=torch.from_numpy(packed.script_f_sigma).to(dev),
        ctf_vec=torch.from_numpy(packed.ctf_vec).to(dev),
        weather_run=torch.from_numpy(packed.weather_run).to(dev),
        weather_wu=torch.from_numpy(packed.weather_wu).to(dev),
        sched_gain_w=torch.from_numpy(packed.sched_gain_w).to(dev),
        state_zone_f=torch.from_numpy(packed.state_zone_f).to(dev),
        state_num_sys_last=torch.from_numpy(packed.state_num_sys_last).to(dev),
        state_surf_f=torch.from_numpy(packed.state_surf_f).to(dev),
        state_ctf_hist=torch.from_numpy(packed.state_ctf_hist).to(dev),
        active_mask=torch.ones((b_size,), dtype=torch.int32, device=dev),
        wu_stats=torch.from_numpy(packed.wu_stats).to(dev),
        hourly_heating_j=torch.from_numpy(packed.hourly_heating_j).to(dev),
        zone_t_rec=zone_t_rec,
        zone_ztav_rec=zone_ztav_rec,
        params_i=torch.zeros((PI_COUNT,), dtype=torch.int32, device=dev),
    )


def update_active_mask_mps(
    bufs: MetalDeviceBuffers,
    still_warming: np.ndarray,
) -> None:
    """Copy the CPU per-building warm-up active mask into MPS memory.

    Args:
        bufs: Resident ``MetalDeviceBuffers``.
        still_warming: Host boolean mask of shape ``[B]``.
    """
    mask_t = torch.from_numpy(still_warming.astype(np.int32))
    bufs.active_mask.copy_(mask_t)


def launch_s0_chunk_mps(
    lib: Any,
    bufs: MetalDeviceBuffers,
    step_start: int,
    step_end: int,
    is_warmup: bool,
    warmup_day: int,
    record_zone_temp: bool,
    rec_step_offset: int,
    limit_num_sys: int,
) -> None:
    """Launch ``s0_run_chunk`` on MPS for one warm-up day or run-period chunk.

    Args:
        lib: Compiled MPS shader library from ``compile_metal_s0_shader``.
        bufs: Resident ``MetalDeviceBuffers``.
        step_start: Inclusive start timestep index in weather buffer.
        step_end: Exclusive end timestep index in weather buffer.
        is_warmup: True for a warm-up day launch, False for run period.
        warmup_day: 1-based warm-up day index (used for day-1 window init).
        record_zone_temp: Whether to write per-timestep zone temperatures.
        rec_step_offset: Destination offset when recording zone temperatures.
        limit_num_sys: Maximum HVAC sub-steps per zone timestep.
    """
    n_wsteps = bufs.n_wu_steps if is_warmup else bufs.n_run_steps
    weather_buf = bufs.weather_wu if is_warmup else bufs.weather_run
    params_np = np.asarray(
        [
            bufs.batch_size,
            bufs.max_surfaces,
            bufs.n_sites,
            bufs.n_ctf_hist,
            bufs.steps_per_hour,
            step_start,
            step_end,
            1 if is_warmup else 0,
            warmup_day,
            1 if (record_zone_temp and not is_warmup) else 0,
            rec_step_offset,
            limit_num_sys,
            n_wsteps,
        ],
        dtype=np.int32,
    )
    bufs.params_i.copy_(torch.from_numpy(params_np))
    lib.s0_run_chunk(
        bufs.bldg_f,
        bufs.bldg_i,
        bufs.surf_f,
        bufs.surf_flags,
        bufs.script_f_sigma,
        bufs.ctf_vec,
        weather_buf,
        bufs.sched_gain_w,
        bufs.state_zone_f,
        bufs.state_num_sys_last,
        bufs.state_surf_f,
        bufs.state_ctf_hist,
        bufs.active_mask,
        bufs.wu_stats,
        bufs.hourly_heating_j,
        bufs.zone_t_rec,
        bufs.zone_ztav_rec,
        bufs.params_i,
        threads=bufs.batch_size,
    )
