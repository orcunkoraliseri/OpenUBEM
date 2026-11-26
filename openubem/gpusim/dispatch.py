"""Hardware- and workload-aware backend auto-dispatch for ``openubem.gpusim``.

Selects the empirically fastest execution backend across macOS (Apple Silicon
CPU + Metal MPS), Windows/Linux (x86_64/arm64 CPU + NVIDIA CUDA), and CPU-only
hosts based on verified benchmark crossover thresholds:

- **S0 single-zone thermal simulation**:
  - Windows/Linux with NVIDIA CUDA + Rust: ``cpu_rust`` for ``B < 200`` (avoids
    4-15 s CUDA compile/upload latency), ``cuda`` for ``B >= 200``.
  - macOS Apple Silicon with Metal MPS + Rust: ``cpu_rust`` for ``B < 1500``
    (M2 Pro 12-core f64 ``0.33-52.40 s`` beats Metal f32 ``19.77-62.65 s``),
    ``mps`` for ``B >= 1500``.
  - Without compiled Rust: ``cuda`` -> ``mps`` -> ``cpu_python``.
- **General multi-zone / solar / layered / shaded (S1..S2b)**:
  - ``cuda`` when NVIDIA CUDA is available and allowed, else fail-closed
    ``energyplus`` fallback.
- **Exterior ray shading**:
  - ``cpu_rust`` (CWBVH8, 460x vs Python CPU, 42.9x vs Mac MPS) whenever Rust
    is active, else ``cuda`` -> ``mps`` -> ``cpu_python``.

Strictly isolated from non-``gpusim`` ``openubem.*`` imports to preserve
``tests/gpusim/test_isolation.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import platform
from typing import Literal

from openubem.gpusim._rust_compat import (
    get_gpusim_rust_mode,
    is_gpusim_rust_available,
)

BackendName = Literal["cpu_rust", "cpu_python", "cuda", "mps", "energyplus"]
DeviceName = Literal["cpu", "cuda", "mps", "energyplus"]
ShadingBackendName = Literal["cpu_rust", "cuda", "mps", "cpu_python"]

CUDA_S0_MIN_BATCH: int = 200
MPS_S0_MIN_BATCH: int = 1500
VALID_REQUESTED_DEVICES: frozenset[str] = frozenset({"auto", "cuda", "mps", "cpu"})

_CACHED_GPU_PROBE: tuple[bool, bool, bool, str | None] | None = None


@dataclass(frozen=True)
class HardwareProfile:
    """Snapshot of host compute capabilities for automatic backend dispatch.

    Attributes:
        platform_system: OS name from ``platform.system()`` (e.g., ``"Darwin"``,
            ``"Windows"``, ``"Linux"``).
        platform_machine: CPU architecture (e.g., ``"arm64"``, ``"x86_64"``).
        cpu_count: Logical CPU core count (>= 1).
        has_rust: ``True`` when compiled ``_openubem_rust`` is loadable and not
            forced off via ``OPENUBEM_RUST_BACKEND=off``.
        rust_mode: Active Rust dispatch mode (``"off"``, ``"shadow"``, ``"on"``).
        has_cuda: ``True`` when PyTorch reports an available NVIDIA CUDA device.
        has_mps: ``True`` when PyTorch reports an available Apple Metal MPS device.
        has_cupy: ``True`` when ``cupy`` is importable (required for CUDA S0
            and general S1-S2b custom kernels).
        cuda_device_name: Optional CUDA GPU device name when ``has_cuda`` is True.
    """

    platform_system: str
    platform_machine: str
    cpu_count: int
    has_rust: bool
    rust_mode: str
    has_cuda: bool
    has_mps: bool
    has_cupy: bool = False
    cuda_device_name: str | None = None

    @property
    def has_cuda_kernels(self) -> bool:
        """Return ``True`` when both CUDA GPU and CuPy NVRTC kernels work."""
        return self.has_cuda and self.has_cupy


@dataclass(frozen=True)
class ExecutionChoice:
    """Resolved backend selection and human-readable rationale.

    Attributes:
        backend: Concrete execution kernel (``cpu_rust``, ``cpu_python``,
            ``cuda``, ``mps``, or ``energyplus``).
        device: Execution device category (``cpu``, ``cuda``, ``mps``, or
            ``energyplus``).
        reason: Short machine-readable explanation for provenance logs.
        profile: ``HardwareProfile`` used to reach the decision.
    """

    backend: BackendName
    device: DeviceName
    reason: str
    profile: HardwareProfile


def reset_hardware_cache() -> None:
    """Clear the cached GPU availability probe (primarily for unit tests)."""
    global _CACHED_GPU_PROBE
    _CACHED_GPU_PROBE = None


def _probe_torch_accelerators() -> tuple[bool, bool, bool, str | None]:
    """Detect NVIDIA CUDA, CuPy, and Apple Metal MPS without raising.

    Returns:
        Tuple ``(has_cuda, has_mps, has_cupy, cuda_device_name)``.
    """
    has_cuda = False
    has_mps = False
    cuda_name: str | None = None
    try:
        import torch

        has_cuda = bool(torch.cuda.is_available())
        if has_cuda:
            try:
                cuda_name = str(torch.cuda.get_device_name(0))
            except Exception:
                cuda_name = "CUDA GPU"
        mps_backend = getattr(torch.backends, "mps", None)
        has_mps = bool(mps_backend is not None and mps_backend.is_available())
    except Exception:
        pass

    has_cupy = False
    if has_cuda:
        try:
            import cupy  # noqa: F401

            has_cupy = True
        except Exception:
            has_cupy = False
    return has_cuda, has_mps, has_cupy, cuda_name


def probe_hardware(*, use_cache: bool = True) -> HardwareProfile:
    """Inspect host OS, CPU, Rust extension, and GPU accelerator availability.

    The PyTorch CUDA/MPS and CuPy probe is cached across calls when
    ``use_cache=True``, while the active ``OPENUBEM_RUST_BACKEND`` mode is
    always read dynamically so environment overrides take effect immediately.

    Args:
        use_cache: Reuse the cached GPU probe when available.

    Returns:
        Populated ``HardwareProfile`` describing the current machine.
    """
    global _CACHED_GPU_PROBE
    if use_cache and _CACHED_GPU_PROBE is not None:
        has_cuda, has_mps, has_cupy, cuda_name = _CACHED_GPU_PROBE
    else:
        has_cuda, has_mps, has_cupy, cuda_name = _probe_torch_accelerators()
        if use_cache:
            _CACHED_GPU_PROBE = (has_cuda, has_mps, has_cupy, cuda_name)

    rust_mode = get_gpusim_rust_mode()
    has_rust = rust_mode != "off" and is_gpusim_rust_available()

    return HardwareProfile(
        platform_system=platform.system() or "Unknown",
        platform_machine=platform.machine() or "Unknown",
        cpu_count=max(1, int(os.cpu_count() or 1)),
        has_rust=has_rust,
        rust_mode=rust_mode,
        has_cuda=has_cuda,
        has_mps=has_mps,
        has_cupy=has_cupy,
        cuda_device_name=cuda_name,
    )


def _normalize_device(requested_device: str) -> str:
    """Validate and normalize a requested device selector string.

    Args:
        requested_device: One of ``"auto"``, ``"cuda"``, ``"mps"``, ``"cpu"``.

    Returns:
        Lowercase stripped device selector.

    Raises:
        ValueError: If ``requested_device`` is not supported.
    """
    req = requested_device.strip().lower()
    if req not in VALID_REQUESTED_DEVICES:
        raise ValueError(f"Unsupported gpusim device {requested_device!r}")
    return req


def select_optimal_s0_backend(
    batch_size: int,
    *,
    requested_device: str = "auto",
    profile: HardwareProfile | None = None,
) -> ExecutionChoice:
    """Choose the fastest execution backend for an S0 thermal batch.

    Args:
        batch_size: Number of S0 buildings to execute in this batch (>= 1).
        requested_device: Caller preference (``"auto"``, ``"cuda"``, ``"mps"``,
            or ``"cpu"``).
        profile: Optional pre-probed ``HardwareProfile`` (defaults to live host).

    Returns:
        ``ExecutionChoice`` indicating concrete backend, device, and rationale.

    Raises:
        ValueError: If ``requested_device`` is invalid.
        RuntimeError: If an explicitly requested GPU backend is unavailable.
    """
    req = _normalize_device(requested_device)
    prof = probe_hardware() if profile is None else profile
    eff_b = max(1, int(batch_size))

    if req == "cpu":
        if prof.has_rust:
            return ExecutionChoice("cpu_rust", "cpu", "explicit:cpu_rust", prof)
        return ExecutionChoice("cpu_python", "cpu", "explicit:cpu_python", prof)

    if req == "cuda":
        if not prof.has_cuda_kernels:
            raise RuntimeError("Requested gpusim device 'cuda' is unavailable")
        return ExecutionChoice("cuda", "cuda", "explicit:cuda", prof)

    if req == "mps":
        if not prof.has_mps:
            raise RuntimeError("Requested gpusim device 'mps' is unavailable")
        return ExecutionChoice("mps", "mps", "explicit:mps", prof)

    # Automatic cross-platform fastest-option policy
    if prof.has_cuda_kernels:
        if prof.has_rust and eff_b < CUDA_S0_MIN_BATCH:
            return ExecutionChoice(
                "cpu_rust",
                "cpu",
                f"auto:rust_cpu_faster_for_batch<{CUDA_S0_MIN_BATCH}",
                prof,
            )
        reason = (
            f"auto:cuda_batch>={CUDA_S0_MIN_BATCH}"
            if prof.has_rust
            else "auto:cuda_no_rust"
        )
        return ExecutionChoice("cuda", "cuda", reason, prof)

    if prof.has_mps:
        if prof.has_rust and eff_b < MPS_S0_MIN_BATCH:
            return ExecutionChoice(
                "cpu_rust",
                "cpu",
                f"auto:rust_cpu_faster_for_batch<{MPS_S0_MIN_BATCH}",
                prof,
            )
        reason = (
            f"auto:mps_batch>={MPS_S0_MIN_BATCH}"
            if prof.has_rust
            else "auto:mps_no_rust"
        )
        return ExecutionChoice("mps", "mps", reason, prof)

    if prof.has_rust:
        return ExecutionChoice("cpu_rust", "cpu", "auto:cpu_only_rust", prof)
    return ExecutionChoice("cpu_python", "cpu", "auto:cpu_only_python", prof)


def select_optimal_general_backend(
    batch_size: int,
    *,
    requested_device: str = "auto",
    profile: HardwareProfile | None = None,
) -> ExecutionChoice:
    """Choose the fastest valid backend for general S1/S2a/S3/S2b buildings.

    The general multi-zone/solar/layered/shaded GPU kernel currently requires
    NVIDIA CUDA. On macOS or CPU-only hosts, automatic selection fails closed
    to EnergyPlus rather than attempting an unsupported GPU launch.

    Args:
        batch_size: Number of general-rung buildings in the batch.
        requested_device: Caller preference (``"auto"``, ``"cuda"``, ``"mps"``,
            or ``"cpu"``).
        profile: Optional pre-probed ``HardwareProfile`` (defaults to live host).

    Returns:
        ``ExecutionChoice`` selecting either ``"cuda"`` or ``"energyplus"``.

    Raises:
        ValueError: If ``requested_device`` is invalid.
        RuntimeError: If ``requested_device="cuda"`` was explicitly forced on a
            host without CUDA.
    """
    _ = max(1, int(batch_size))
    req = _normalize_device(requested_device)
    prof = probe_hardware() if profile is None else profile

    if req == "cuda":
        if not prof.has_cuda_kernels:
            raise RuntimeError("Requested gpusim device 'cuda' is unavailable")
        return ExecutionChoice("cuda", "cuda", "explicit:general_cuda", prof)

    if req == "auto" and prof.has_cuda_kernels:
        return ExecutionChoice("cuda", "cuda", "auto:general_cuda", prof)

    if req in {"cpu", "mps"}:
        return ExecutionChoice(
            "energyplus",
            "energyplus",
            f"fallback:general_requires_cuda_not_{req}",
            prof,
        )
    return ExecutionChoice(
        "energyplus",
        "energyplus",
        "fallback:general_requires_cuda",
        prof,
    )


def select_optimal_shading_backend(
    *,
    requested_device: str = "auto",
    profile: HardwareProfile | None = None,
) -> ShadingBackendName:
    """Choose the fastest ray-triangle backend for exterior shading.

    Compiled Rust CWBVH8 ray tracing outperforms both Python CPU (~460x) and
    macOS Metal MPS (~42.9x) with zero host-to-GPU upload latency, so ``"auto"``
    always prefers ``"cpu_rust"`` whenever Rust is active.

    Args:
        requested_device: Caller preference (``"auto"``, ``"cuda"``, ``"mps"``,
            or ``"cpu"``).
        profile: Optional pre-probed ``HardwareProfile`` (defaults to live host).

    Returns:
        Concrete shading backend: ``"cpu_rust"``, ``"cuda"``, ``"mps"``, or
        ``"cpu_python"``.

    Raises:
        ValueError: If ``requested_device`` is invalid.
        RuntimeError: If an explicitly requested GPU backend is unavailable.
    """
    req = _normalize_device(requested_device)
    prof = probe_hardware() if profile is None else profile

    if req == "cpu":
        return "cpu_rust" if prof.has_rust else "cpu_python"
    if req == "cuda":
        if not prof.has_cuda:
            raise RuntimeError("Requested shading device 'cuda' is unavailable")
        return "cuda"
    if req == "mps":
        if not prof.has_mps:
            raise RuntimeError("Requested shading device 'mps' is unavailable")
        return "mps"

    # Auto mode: Rust CWBVH8 > CUDA > MPS > Python NumPy
    if prof.has_rust:
        return "cpu_rust"
    if prof.has_cuda:
        return "cuda"
    if prof.has_mps:
        return "mps"
    return "cpu_python"


def select_max_supported_rung(
    *,
    requested_device: str = "auto",
    profile: HardwareProfile | None = None,
) -> str:
    """Return the highest gpusim physics rung executable on the current host.

    Args:
        requested_device: Caller preference (``"auto"``, ``"cuda"``, ``"mps"``,
            or ``"cpu"``).
        profile: Optional pre-probed ``HardwareProfile`` (defaults to live host).

    Returns:
        ``"S2b"`` when CUDA is available and permitted by ``requested_device``,
        otherwise ``"S0"``.
    """
    req = _normalize_device(requested_device)
    prof = probe_hardware() if profile is None else profile
    if req in {"auto", "cuda"} and prof.has_cuda_kernels:
        return "S2b"
    return "S0"
