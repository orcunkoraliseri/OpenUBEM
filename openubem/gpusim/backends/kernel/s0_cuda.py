from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import cupy as cp
import numpy as np
import torch

from openubem.gpusim.backends.kernel.pack import PackedBatch

HEADER_PATH: Path = Path(__file__).with_name("s0_common.h")

PI_COUNT: int = 13
THREADS_PER_BLOCK: int = 128

_CUDA_WRAPPER: str = """
// HeatBalanceSurfaceManager.cc::ManageSurfaceHeatBalance | s0_run_chunk
extern "C" __global__ void s0_run_chunk(
    const float* __restrict__ bldg_f,
    const int* __restrict__ bldg_i,
    const float* __restrict__ surf_f,
    const int* __restrict__ surf_flags,
    const float* __restrict__ script_f_sigma,
    const float* __restrict__ ctf_vec,
    const float* __restrict__ weather_buf,
    const float* __restrict__ sched_gain_w,
    float* __restrict__ state_zone_f,
    int* __restrict__ state_num_sys_last,
    float* __restrict__ state_surf_f,
    float* __restrict__ state_ctf_hist,
    const int* __restrict__ active_mask,
    float* __restrict__ wu_stats,
    float* __restrict__ hourly_heating_j,
    float* __restrict__ zone_t_rec,
    float* __restrict__ zone_ztav_rec,
    const int* __restrict__ params_i
) {
    int b = (int)(blockIdx.x * blockDim.x + threadIdx.x);
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
class CudaDeviceBuffers:
    """Resident PyTorch CUDA tensors and zero-copy CuPy DLPack views."""

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
    cp_bldg_f: cp.ndarray
    cp_bldg_i: cp.ndarray
    cp_surf_f: cp.ndarray
    cp_surf_flags: cp.ndarray
    cp_script_f_sigma: cp.ndarray
    cp_ctf_vec: cp.ndarray
    cp_weather_run: cp.ndarray
    cp_weather_wu: cp.ndarray
    cp_sched_gain_w: cp.ndarray
    cp_state_zone_f: cp.ndarray
    cp_state_num_sys_last: cp.ndarray
    cp_state_surf_f: cp.ndarray
    cp_state_ctf_hist: cp.ndarray
    cp_active_mask: cp.ndarray
    cp_wu_stats: cp.ndarray
    cp_hourly_heating_j: cp.ndarray
    cp_zone_t_rec: cp.ndarray
    cp_zone_ztav_rec: cp.ndarray
    cp_params_i: cp.ndarray


def build_cuda_s0_source() -> str:
    """Assemble the Stage C CUDA kernel source from ``s0_common.h``."""
    header_text = HEADER_PATH.read_text(encoding="utf-8")
    return f"{header_text}\n{_CUDA_WRAPPER}"


@lru_cache(maxsize=1)
def compile_cuda_s0_kernel() -> cp.RawKernel:
    """Compile and cache the Stage C CUDA kernel via CuPy NVRTC."""
    kernel = cp.RawKernel(build_cuda_s0_source(), "s0_run_chunk")
    kernel.compile()
    return kernel


def _to_cp_view(tensor: torch.Tensor) -> cp.ndarray:
    """Wrap a contiguous PyTorch CUDA tensor in a zero-copy CuPy DLPack view."""
    return cp.from_dlpack(tensor)


def upload_packed_to_cuda(
    packed: PackedBatch,
    record_zone_temp: bool = False,
) -> CudaDeviceBuffers:
    """Upload a ``PackedBatch`` once onto the active NVIDIA CUDA device."""
    dev = torch.device("cuda")
    b_size = packed.batch_size
    n_run = packed.n_run_steps
    if record_zone_temp:
        zone_t_rec = torch.empty((n_run, b_size), dtype=torch.float32, device=dev)
        zone_ztav_rec = torch.empty((n_run, b_size), dtype=torch.float32, device=dev)
    else:
        zone_t_rec = torch.empty((1,), dtype=torch.float32, device=dev)
        zone_ztav_rec = torch.empty((1,), dtype=torch.float32, device=dev)

    bldg_f = torch.from_numpy(packed.bldg_f).to(dev)
    bldg_i = torch.from_numpy(packed.bldg_i).to(dev)
    surf_f = torch.from_numpy(packed.surf_f).to(dev)
    surf_flags = torch.from_numpy(packed.surf_flags).to(dev)
    script_f_sigma = torch.from_numpy(packed.script_f_sigma).to(dev)
    ctf_vec = torch.from_numpy(packed.ctf_vec).to(dev)
    weather_run = torch.from_numpy(packed.weather_run).to(dev)
    weather_wu = torch.from_numpy(packed.weather_wu).to(dev)
    sched_gain_w = torch.from_numpy(packed.sched_gain_w).to(dev)
    state_zone_f = torch.from_numpy(packed.state_zone_f).to(dev)
    state_num_sys_last = torch.from_numpy(packed.state_num_sys_last).to(dev)
    state_surf_f = torch.from_numpy(packed.state_surf_f).to(dev)
    state_ctf_hist = torch.from_numpy(packed.state_ctf_hist).to(dev)
    active_mask = torch.ones((b_size,), dtype=torch.int32, device=dev)
    wu_stats = torch.from_numpy(packed.wu_stats).to(dev)
    hourly_heating_j = torch.from_numpy(packed.hourly_heating_j).to(dev)
    params_i = torch.zeros((PI_COUNT,), dtype=torch.int32, device=dev)

    return CudaDeviceBuffers(
        batch_size=b_size,
        max_surfaces=packed.max_surfaces,
        n_sites=packed.n_sites,
        n_ctf_hist=packed.n_ctf_hist,
        steps_per_hour=packed.steps_per_hour,
        n_run_steps=n_run,
        n_wu_steps=packed.n_wu_steps,
        bldg_f=bldg_f,
        bldg_i=bldg_i,
        surf_f=surf_f,
        surf_flags=surf_flags,
        script_f_sigma=script_f_sigma,
        ctf_vec=ctf_vec,
        weather_run=weather_run,
        weather_wu=weather_wu,
        sched_gain_w=sched_gain_w,
        state_zone_f=state_zone_f,
        state_num_sys_last=state_num_sys_last,
        state_surf_f=state_surf_f,
        state_ctf_hist=state_ctf_hist,
        active_mask=active_mask,
        wu_stats=wu_stats,
        hourly_heating_j=hourly_heating_j,
        zone_t_rec=zone_t_rec,
        zone_ztav_rec=zone_ztav_rec,
        params_i=params_i,
        cp_bldg_f=_to_cp_view(bldg_f),
        cp_bldg_i=_to_cp_view(bldg_i),
        cp_surf_f=_to_cp_view(surf_f),
        cp_surf_flags=_to_cp_view(surf_flags),
        cp_script_f_sigma=_to_cp_view(script_f_sigma),
        cp_ctf_vec=_to_cp_view(ctf_vec),
        cp_weather_run=_to_cp_view(weather_run),
        cp_weather_wu=_to_cp_view(weather_wu),
        cp_sched_gain_w=_to_cp_view(sched_gain_w),
        cp_state_zone_f=_to_cp_view(state_zone_f),
        cp_state_num_sys_last=_to_cp_view(state_num_sys_last),
        cp_state_surf_f=_to_cp_view(state_surf_f),
        cp_state_ctf_hist=_to_cp_view(state_ctf_hist),
        cp_active_mask=_to_cp_view(active_mask),
        cp_wu_stats=_to_cp_view(wu_stats),
        cp_hourly_heating_j=_to_cp_view(hourly_heating_j),
        cp_zone_t_rec=_to_cp_view(zone_t_rec),
        cp_zone_ztav_rec=_to_cp_view(zone_ztav_rec),
        cp_params_i=_to_cp_view(params_i),
    )


def update_active_mask_cuda(
    bufs: CudaDeviceBuffers,
    still_warming: np.ndarray,
) -> None:
    """Copy the CPU per-building warm-up active mask into CUDA memory."""
    mask_t = torch.from_numpy(still_warming.astype(np.int32))
    bufs.active_mask.copy_(mask_t)


class _TorchStreamWrapper:
    """Expose a PyTorch CUDA stream pointer via the CUDA stream protocol."""

    def __init__(self, stream_ptr: int) -> None:
        self._ptr = int(stream_ptr)

    def __cuda_stream__(self) -> tuple[int, int]:
        return (0, self._ptr)


def launch_s0_chunk_cuda(
    kernel: Any,
    bufs: CudaDeviceBuffers,
    step_start: int,
    step_end: int,
    is_warmup: bool,
    warmup_day: int,
    record_zone_temp: bool,
    rec_step_offset: int,
    limit_num_sys: int,
) -> None:
    """Launch ``s0_run_chunk`` on CUDA for one warm-up day or run-period chunk."""
    n_wsteps = bufs.n_wu_steps if is_warmup else bufs.n_run_steps
    cp_weather = bufs.cp_weather_wu if is_warmup else bufs.cp_weather_run
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
    grid_x = (bufs.batch_size + THREADS_PER_BLOCK - 1) // THREADS_PER_BLOCK
    torch_stream = torch.cuda.current_stream()
    with cp.cuda.Stream.from_external(_TorchStreamWrapper(torch_stream.cuda_stream)):
        kernel(
            (grid_x,),
            (THREADS_PER_BLOCK,),
            (
                bufs.cp_bldg_f,
                bufs.cp_bldg_i,
                bufs.cp_surf_f,
                bufs.cp_surf_flags,
                bufs.cp_script_f_sigma,
                bufs.cp_ctf_vec,
                cp_weather,
                bufs.cp_sched_gain_w,
                bufs.cp_state_zone_f,
                bufs.cp_state_num_sys_last,
                bufs.cp_state_surf_f,
                bufs.cp_state_ctf_hist,
                bufs.cp_active_mask,
                bufs.cp_wu_stats,
                bufs.cp_hourly_heating_j,
                bufs.cp_zone_t_rec,
                bufs.cp_zone_ztav_rec,
                bufs.cp_params_i,
            ),
        )
