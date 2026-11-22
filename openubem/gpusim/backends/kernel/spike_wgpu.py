from functools import lru_cache
from pathlib import Path
import time
from typing import Any

import numpy as np
import wgpu

from openubem.gpusim.backends.kernel.spike_metal import (
    OF_COUNT,
    unpack_outputs_soa,
)

WGSL_PATH: Path = Path(__file__).with_name("spike_iter.wgsl")
WORKGROUP_SIZE: int = 64


@lru_cache(maxsize=1)
def get_wgpu_pipeline() -> tuple[Any, Any, Any]:
    """Initialize the wgpu Metal device and compiled compute pipeline.

    Returns:
        Tuple ``(device, pipeline, bind_group_layout)``.
    """
    adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
    if adapter is None:
        raise RuntimeError("No wgpu adapter available")
    device = adapter.request_device_sync()
    shader_src = WGSL_PATH.read_text(encoding="utf-8")
    shader = device.create_shader_module(code=shader_src)
    pipeline = device.create_compute_pipeline(
        layout="auto",
        compute={"module": shader, "entry_point": "inside_surface_iterate"},
    )
    bind_group_layout = pipeline.get_bind_group_layout(0)
    return device, pipeline, bind_group_layout


def _create_wgpu_buffers(
    device: Any,
    bind_group_layout: Any,
    packed: dict[str, Any],
) -> tuple[Any, Any, Any, list[Any]]:
    """Allocate GPU buffers and a bind group for one packed SoA batch.

    Args:
        device: Active wgpu device.
        bind_group_layout: Compute pipeline bind group layout at index 0.
        packed: Packed dictionary returned by ``pack_captures_soa``.

    Returns:
        Tuple ``(bind_group, surf_out_buf, iter_out_buf, all_buffers)``.
    """
    b_size = int(packed["b_size"])
    n_surf = int(packed["n_surf"])
    params_arr = np.array([b_size, n_surf, 0, 0], dtype=np.int32)

    params_buf = device.create_buffer_with_data(
        data=params_arr,
        usage=wgpu.BufferUsage.UNIFORM,
    )
    zone_buf = device.create_buffer_with_data(
        data=np.ascontiguousarray(packed["zone_in"], dtype=np.float32),
        usage=wgpu.BufferUsage.STORAGE,
    )
    surf_buf = device.create_buffer_with_data(
        data=np.ascontiguousarray(packed["surf_in"], dtype=np.float32),
        usage=wgpu.BufferUsage.STORAGE,
    )
    flags_buf = device.create_buffer_with_data(
        data=np.ascontiguousarray(packed["surf_flags"], dtype=np.int32),
        usage=wgpu.BufferUsage.STORAGE,
    )
    sf_buf = device.create_buffer_with_data(
        data=np.ascontiguousarray(packed["script_f_sigma"], dtype=np.float32),
        usage=wgpu.BufferUsage.STORAGE,
    )
    surf_out_buf = device.create_buffer(
        size=OF_COUNT * n_surf * b_size * 4,
        usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_SRC,
    )
    iter_out_buf = device.create_buffer(
        size=b_size * 4,
        usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_SRC,
    )

    entries = [
        {"binding": 0, "resource": {"buffer": params_buf}},
        {"binding": 1, "resource": {"buffer": zone_buf}},
        {"binding": 2, "resource": {"buffer": surf_buf}},
        {"binding": 3, "resource": {"buffer": flags_buf}},
        {"binding": 4, "resource": {"buffer": sf_buf}},
        {"binding": 5, "resource": {"buffer": surf_out_buf}},
        {"binding": 6, "resource": {"buffer": iter_out_buf}},
    ]
    bind_group = device.create_bind_group(
        layout=bind_group_layout,
        entries=entries,
    )
    all_buffers = [
        params_buf,
        zone_buf,
        surf_buf,
        flags_buf,
        sf_buf,
        surf_out_buf,
        iter_out_buf,
    ]
    return bind_group, surf_out_buf, iter_out_buf, all_buffers


def _dispatch_once(
    device: Any,
    pipeline: Any,
    bind_group: Any,
    b_size: int,
) -> None:
    """Encode, submit, and synchronize one compute pass for ``b_size`` buildings.

    Args:
        device: Active wgpu device.
        pipeline: Compiled compute pipeline.
        bind_group: Bound resource group for the batch.
        b_size: Number of buildings in the batch.
    """
    n_groups = (b_size + WORKGROUP_SIZE - 1) // WORKGROUP_SIZE
    encoder = device.create_command_encoder()
    compute_pass = encoder.begin_compute_pass()
    compute_pass.set_pipeline(pipeline)
    compute_pass.set_bind_group(0, bind_group)
    compute_pass.dispatch_workgroups(n_groups, 1, 1)
    compute_pass.end()
    device.queue.submit([encoder.finish()])
    device.queue.on_submitted_work_done_sync()


def run_wgpu_spike(packed: dict[str, Any]) -> dict[str, np.ndarray]:
    """Run ``inside_surface_iterate`` via wgpu-py / WGSL on a packed SoA batch.

    Args:
        packed: Packed dictionary returned by ``pack_captures_soa``.

    Returns:
        Unpacked float64 host outputs and int32 iteration counts.
    """
    device, pipeline, bind_group_layout = get_wgpu_pipeline()
    b_size = int(packed["b_size"])
    n_surf = int(packed["n_surf"])
    bind_group, surf_out_buf, iter_out_buf, all_buffers = _create_wgpu_buffers(
        device, bind_group_layout, packed
    )
    try:
        _dispatch_once(device, pipeline, bind_group, b_size)
        surf_raw = device.queue.read_buffer(surf_out_buf)
        iter_raw = device.queue.read_buffer(iter_out_buf)
        surf_out_np = (
            np.frombuffer(surf_raw, dtype=np.float32)
            .reshape((OF_COUNT, n_surf, b_size))
            .copy()
        )
        iter_out_np = np.frombuffer(iter_raw, dtype=np.int32).copy()
        return unpack_outputs_soa(surf_out_np, iter_out_np)
    finally:
        for buf in all_buffers:
            buf.destroy()


def benchmark_wgpu_launch(
    packed: dict[str, Any],
    n_runs: int = 20,
    n_warmup: int = 10,
) -> float:
    """Measure median wgpu compute launch time in ms on pre-staged buffers.

    Args:
        packed: Packed SoA batch dictionary.
        n_runs: Number of timed launches.
        n_warmup: Number of untimed warmup launches.

    Returns:
        Median launch wall time in milliseconds.
    """
    device, pipeline, bind_group_layout = get_wgpu_pipeline()
    b_size = int(packed["b_size"])
    bind_group, _, _, all_buffers = _create_wgpu_buffers(
        device, bind_group_layout, packed
    )
    try:
        for _ in range(n_warmup):
            _dispatch_once(device, pipeline, bind_group, b_size)

        times_ms: list[float] = []
        for _ in range(n_runs):
            t0 = time.perf_counter()
            _dispatch_once(device, pipeline, bind_group, b_size)
            times_ms.append((time.perf_counter() - t0) * 1000.0)

        return float(np.median(np.asarray(times_ms, dtype=np.float64)))
    finally:
        for buf in all_buffers:
            buf.destroy()
