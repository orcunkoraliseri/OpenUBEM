from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch

T_REF_C: float = 20.0
T_REF_K: float = 293.15
SPIKE_MAX_SURF: int = 16

ZF_COUNT: int = 6
SF_COUNT: int = 19
OF_COUNT: int = 5

FLAG_SURF_MASK: int = 1
FLAG_IS_WINDOW: int = 2
FLAG_IS_NON_WINDOW: int = 4
FLAG_IS_INTMASS: int = 8

HEADER_PATH: Path = Path(__file__).with_name("spike_common.h")

_METAL_PREFIX: str = """#include <metal_stdlib>
using namespace metal;
#define GPUSIM_FN inline
#define GPUSIM_GLOBAL device
#define GPUSIM_GLOBAL_CONST device const
#define GPUSIM_THREAD thread
#define GPUSIM_POW pow
#define GPUSIM_EXP exp
"""

_METAL_WRAPPER: str = """
kernel void inside_surface_iterate(
    device const float* zone_in [[buffer(0)]],
    device const float* surf_in [[buffer(1)]],
    device const int* surf_flags [[buffer(2)]],
    device const float* script_f_sigma [[buffer(3)]],
    device float* surf_out [[buffer(4)]],
    device int* iter_out [[buffer(5)]],
    constant int& b_size [[buffer(6)]],
    constant int& n_surf [[buffer(7)]],
    uint tid [[thread_position_in_grid]]
) {
    int b = (int)tid;
    if (b >= b_size) {
        return;
    }
    spike_inside_surface_iterate_core(
        b,
        b_size,
        n_surf,
        zone_in,
        surf_in,
        surf_flags,
        script_f_sigma,
        surf_out,
        iter_out
    );
}
"""


def _strip_batch_dim(arr: np.ndarray, expected_ndim: int) -> np.ndarray:
    """Drop a leading singleton batch axis when present.

    Args:
        arr: Input NumPy array from a saved capture.
        expected_ndim: Target number of dimensions without batch axis.

    Returns:
        Array with ``expected_ndim`` dimensions.
    """
    if arr.ndim == expected_ndim + 1 and arr.shape[0] == 1:
        return arr[0]
    if arr.ndim != expected_ndim:
        raise ValueError(
            f"Expected ndim {expected_ndim} (or singleton batch), got {arr.shape}"
        )
    return arr


def pack_captures_soa(
    captures: Sequence[dict[str, np.ndarray]],
    pad_surfaces: int | None = None,
) -> dict[str, Any]:
    """Pack step-5 float64 captures into ``[field, building]`` float32 SoA buffers.

    Temperatures are converted to deviations from 20 C and CTF constant parts
    are shifted in float64 before casting to float32.

    Args:
        captures: Sequence of per-building step-5 capture dictionaries.
        pad_surfaces: Optional padded surface count; defaults to max across captures.

    Returns:
        Dictionary with contiguous ``zone_in``, ``surf_in``, ``surf_flags``,
        ``script_f_sigma``, ``b_size``, and ``n_surf``.
    """
    b_size = len(captures)
    if b_size == 0:
        raise ValueError("captures must be non-empty")

    surf_counts = [
        _strip_batch_dim(np.asarray(cap["t_surf_in_init"]), 1).shape[0]
        for cap in captures
    ]
    n_surf = max(surf_counts) if pad_surfaces is None else int(pad_surfaces)
    if n_surf > SPIKE_MAX_SURF:
        raise ValueError(f"n_surf={n_surf} exceeds SPIKE_MAX_SURF={SPIKE_MAX_SURF}")

    zone_in = np.zeros((ZF_COUNT, b_size), dtype=np.float32)
    surf_in = np.zeros((SF_COUNT, n_surf, b_size), dtype=np.float32)
    surf_flags = np.zeros((n_surf, b_size), dtype=np.int32)
    script_f_sigma = np.zeros((n_surf, n_surf, b_size), dtype=np.float32)

    for b, cap in enumerate(captures):
        t_mat = float(np.asarray(cap["t_mat"], dtype=np.float64).reshape(-1)[0])
        w_avg = float(np.asarray(cap["w_zone_avg"], dtype=np.float64).reshape(-1)[0])
        pb = float(np.asarray(cap["pb_site"], dtype=np.float64).reshape(-1)[0])
        t_sky = float(np.asarray(cap["t_sky_site"], dtype=np.float64).reshape(-1)[0])
        h_min = float(np.asarray(cap["h_min"], dtype=np.float64).reshape(-1)[0])
        begin_envrn = bool(np.asarray(cap["begin_envrn"]).reshape(-1)[0])

        zone_in[0, b] = np.float32(t_mat - T_REF_C)
        zone_in[1, b] = np.float32(w_avg)
        zone_in[2, b] = np.float32(pb)
        zone_in[3, b] = np.float32(t_sky - T_REF_C)
        zone_in[4, b] = np.float32(h_min)
        zone_in[5, b] = np.float32(1.0 if begin_envrn else 0.0)

        t_in = _strip_batch_dim(np.asarray(cap["t_surf_in_init"], dtype=np.float64), 1)
        t_out = _strip_batch_dim(
            np.asarray(cap["t_surf_out_init"], dtype=np.float64), 1
        )
        h_in = _strip_batch_dim(np.asarray(cap["h_conv_in_init"], dtype=np.float64), 1)
        th1 = _strip_batch_dim(np.asarray(cap["theta1_init"], dtype=np.float64), 1)
        th2 = _strip_batch_dim(np.asarray(cap["theta2_init"], dtype=np.float64), 1)
        t_air = _strip_batch_dim(np.asarray(cap["t_out_surf_air"], dtype=np.float64), 1)
        eps_in = _strip_batch_dim(np.asarray(cap["surf_eps_in"], dtype=np.float64), 1)
        eps_out = _strip_batch_dim(np.asarray(cap["surf_eps_out"], dtype=np.float64), 1)
        cos_t = _strip_batch_dim(np.asarray(cap["surf_cos_tilt"], dtype=np.float64), 1)
        sin_t = _strip_batch_dim(np.asarray(cap["surf_sin_tilt"], dtype=np.float64), 1)
        tilt_d = _strip_batch_dim(
            np.asarray(cap["surf_tilt_deg"], dtype=np.float64), 1
        )
        height = _strip_batch_dim(np.asarray(cap["surf_height"], dtype=np.float64), 1)
        vf_sky = _strip_batch_dim(
            np.asarray(cap["surf_vf_sky_ir"], dtype=np.float64), 1
        )
        vf_grd = _strip_batch_dim(
            np.asarray(cap["surf_vf_ground_ir"], dtype=np.float64), 1
        )
        split = _strip_batch_dim(
            np.asarray(cap["surf_air_sky_rad_split"], dtype=np.float64), 1
        )
        scon = _strip_batch_dim(np.asarray(cap["scon_win"], dtype=np.float64), 1)
        ctf_in0 = _strip_batch_dim(np.asarray(cap["ctf_in0"], dtype=np.float64), 1)
        ctf_cr0 = _strip_batch_dim(np.asarray(cap["ctf_cross0"], dtype=np.float64), 1)
        ctf_cin = _strip_batch_dim(
            np.asarray(cap["ctf_const_in"], dtype=np.float64), 1
        )
        ctf_cin_shifted = ctf_cin + (ctf_cr0 - ctf_in0) * T_REF_C

        s_orig = t_in.shape[0]
        surf_in[0, :s_orig, b] = (t_in - T_REF_C).astype(np.float32)
        surf_in[1, :s_orig, b] = (t_out - T_REF_C).astype(np.float32)
        surf_in[2, :s_orig, b] = h_in.astype(np.float32)
        surf_in[3, :s_orig, b] = (th1 - T_REF_K).astype(np.float32)
        surf_in[4, :s_orig, b] = (th2 - T_REF_K).astype(np.float32)
        surf_in[5, :s_orig, b] = (t_air - T_REF_C).astype(np.float32)
        surf_in[6, :s_orig, b] = eps_in.astype(np.float32)
        surf_in[7, :s_orig, b] = eps_out.astype(np.float32)
        surf_in[8, :s_orig, b] = cos_t.astype(np.float32)
        surf_in[9, :s_orig, b] = sin_t.astype(np.float32)
        surf_in[10, :s_orig, b] = tilt_d.astype(np.float32)
        surf_in[11, :s_orig, b] = height.astype(np.float32)
        surf_in[12, :s_orig, b] = vf_sky.astype(np.float32)
        surf_in[13, :s_orig, b] = vf_grd.astype(np.float32)
        surf_in[14, :s_orig, b] = split.astype(np.float32)
        surf_in[15, :s_orig, b] = scon.astype(np.float32)
        surf_in[16, :s_orig, b] = ctf_in0.astype(np.float32)
        surf_in[17, :s_orig, b] = ctf_cr0.astype(np.float32)
        surf_in[18, :s_orig, b] = ctf_cin_shifted.astype(np.float32)

        s_mask = _strip_batch_dim(np.asarray(cap["surf_mask"], dtype=np.bool_), 1)
        is_win = _strip_batch_dim(np.asarray(cap["is_window"], dtype=np.bool_), 1)
        is_non = _strip_batch_dim(np.asarray(cap["is_non_window"], dtype=np.bool_), 1)
        is_im = _strip_batch_dim(np.asarray(cap["is_intmass"], dtype=np.bool_), 1)
        flags = (
            s_mask.astype(np.int32) * FLAG_SURF_MASK
            + is_win.astype(np.int32) * FLAG_IS_WINDOW
            + is_non.astype(np.int32) * FLAG_IS_NON_WINDOW
            + is_im.astype(np.int32) * FLAG_IS_INTMASS
        )
        surf_flags[:s_orig, b] = flags

        sf_mat = _strip_batch_dim(
            np.asarray(cap["script_f_sigma"], dtype=np.float64), 2
        )
        script_f_sigma[:s_orig, :s_orig, b] = sf_mat.astype(np.float32)

    return {
        "zone_in": np.ascontiguousarray(zone_in),
        "surf_in": np.ascontiguousarray(surf_in),
        "surf_flags": np.ascontiguousarray(surf_flags),
        "script_f_sigma": np.ascontiguousarray(script_f_sigma),
        "b_size": b_size,
        "n_surf": n_surf,
    }


def tile_packed_soa(packed: dict[str, Any], target_b: int) -> dict[str, Any]:
    """Tile a packed SoA batch along the contiguous building axis to ``target_b``.

    Args:
        packed: Packed dictionary returned by ``pack_captures_soa``.
        target_b: Desired building batch size.

    Returns:
        New packed dictionary with ``b_size == target_b``.
    """
    src_b = int(packed["b_size"])
    idx = np.arange(target_b, dtype=np.int64) % src_b
    return {
        "zone_in": np.ascontiguousarray(packed["zone_in"][:, idx]),
        "surf_in": np.ascontiguousarray(packed["surf_in"][:, :, idx]),
        "surf_flags": np.ascontiguousarray(packed["surf_flags"][:, idx]),
        "script_f_sigma": np.ascontiguousarray(packed["script_f_sigma"][:, :, idx]),
        "b_size": int(target_b),
        "n_surf": int(packed["n_surf"]),
    }


def unpack_outputs_soa(
    surf_out: np.ndarray,
    iter_out: np.ndarray,
) -> dict[str, np.ndarray]:
    """Convert ``[field, surface, building]`` outputs back to ``[B, S]`` float64.

    Args:
        surf_out: Output buffer of shape ``(OF_COUNT, n_surf, b_size)``.
        iter_out: Iteration count buffer of shape ``(b_size,)``.

    Returns:
        Dictionary of host float64 arrays and int32 ``iter_count``.
    """
    surf_f64 = surf_out.astype(np.float64, copy=False)
    return {
        "t_surf_in_out": np.ascontiguousarray(surf_f64[0].T + T_REF_C),
        "t_surf_out_out": np.ascontiguousarray(surf_f64[1].T + T_REF_C),
        "h_conv_in_out": np.ascontiguousarray(surf_f64[2].T),
        "theta1_out": np.ascontiguousarray(surf_f64[3].T + T_REF_K),
        "theta2_out": np.ascontiguousarray(surf_f64[4].T + T_REF_K),
        "iter_count": np.ascontiguousarray(iter_out.astype(np.int32, copy=False)),
    }


def build_metal_source() -> str:
    """Assemble the Metal compute shader source from ``spike_common.h``.

    Returns:
        Complete Metal Shading Language source string.
    """
    header_text = HEADER_PATH.read_text(encoding="utf-8")
    return f"{_METAL_PREFIX}\n{header_text}\n{_METAL_WRAPPER}"


@lru_cache(maxsize=1)
def compile_metal_spike_shader() -> Any:
    """Compile and cache the Metal spike compute shader via PyTorch MPS.

    Returns:
        Compiled MPS shader library exposing ``inside_surface_iterate``.
    """
    return torch.mps.compile_shader(build_metal_source())


def run_metal_spike(packed: dict[str, Any]) -> dict[str, np.ndarray]:
    """Run ``inside_surface_iterate`` on MPS for a packed SoA batch.

    Args:
        packed: Packed dictionary returned by ``pack_captures_soa``.

    Returns:
        Unpacked float64 host outputs and int32 iteration counts.
    """
    lib = compile_metal_spike_shader()
    b_size = int(packed["b_size"])
    n_surf = int(packed["n_surf"])
    dev = torch.device("mps")

    zone_in_t = torch.from_numpy(packed["zone_in"]).to(dev)
    surf_in_t = torch.from_numpy(packed["surf_in"]).to(dev)
    surf_flags_t = torch.from_numpy(packed["surf_flags"]).to(dev)
    script_f_t = torch.from_numpy(packed["script_f_sigma"]).to(dev)
    surf_out_t = torch.empty(
        (OF_COUNT, n_surf, b_size), dtype=torch.float32, device=dev
    )
    iter_out_t = torch.empty((b_size,), dtype=torch.int32, device=dev)

    lib.inside_surface_iterate(
        zone_in_t,
        surf_in_t,
        surf_flags_t,
        script_f_t,
        surf_out_t,
        iter_out_t,
        b_size,
        n_surf,
        threads=b_size,
    )
    torch.mps.synchronize()

    return unpack_outputs_soa(surf_out_t.cpu().numpy(), iter_out_t.cpu().numpy())


def benchmark_metal_launch(
    packed: dict[str, Any],
    n_runs: int = 20,
    n_warmup: int = 10,
) -> float:
    """Measure median Metal kernel launch time in milliseconds on pre-staged buffers.

    Args:
        packed: Packed SoA batch dictionary.
        n_runs: Number of timed launches.
        n_warmup: Number of untimed warmup launches.

    Returns:
        Median launch wall time in milliseconds.
    """
    lib = compile_metal_spike_shader()
    b_size = int(packed["b_size"])
    n_surf = int(packed["n_surf"])
    dev = torch.device("mps")

    zone_in_t = torch.from_numpy(packed["zone_in"]).to(dev)
    surf_in_t = torch.from_numpy(packed["surf_in"]).to(dev)
    surf_flags_t = torch.from_numpy(packed["surf_flags"]).to(dev)
    script_f_t = torch.from_numpy(packed["script_f_sigma"]).to(dev)
    surf_out_t = torch.empty(
        (OF_COUNT, n_surf, b_size), dtype=torch.float32, device=dev
    )
    iter_out_t = torch.empty((b_size,), dtype=torch.int32, device=dev)
    torch.mps.synchronize()

    for _ in range(n_warmup):
        lib.inside_surface_iterate(
            zone_in_t,
            surf_in_t,
            surf_flags_t,
            script_f_t,
            surf_out_t,
            iter_out_t,
            b_size,
            n_surf,
            threads=b_size,
        )
        torch.mps.synchronize()

    times_ms: list[float] = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        lib.inside_surface_iterate(
            zone_in_t,
            surf_in_t,
            surf_flags_t,
            script_f_t,
            surf_out_t,
            iter_out_t,
            b_size,
            n_surf,
            threads=b_size,
        )
        torch.mps.synchronize()
        times_ms.append((time.perf_counter() - t0) * 1000.0)

    return float(np.median(np.asarray(times_ms, dtype=np.float64)))
