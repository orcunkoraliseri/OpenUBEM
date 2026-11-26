"""Cross-platform automatic fastest-backend dispatch tests.

Validates hardware- and workload-aware backend selection across simulated
macOS Apple Silicon, Windows/Linux NVIDIA CUDA, and CPU-only hosts, as well as
explicit overrides and live pipeline integration.
"""

from __future__ import annotations

import numpy as np
import pytest

from openubem import config
from openubem.gpusim import dispatch as dispatch_mod
from openubem.gpusim.dispatch import (
    CUDA_S0_MIN_BATCH,
    MPS_S0_MIN_BATCH,
    HardwareProfile,
    probe_hardware,
    reset_hardware_cache,
    select_max_supported_rung,
    select_optimal_general_backend,
    select_optimal_s0_backend,
    select_optimal_shading_backend,
)
from openubem.gpusim.router import route_idf_text, select_device
from openubem.gpusim.shading import compute_exterior_shading
from tests.gpusim.test_cells import CELL1_ID, GOLDEN_ROOT

V15_DIR = GOLDEN_ROOT / "variants" / f"{CELL1_ID}__V15"

MAC_RUST = HardwareProfile(
    platform_system="Darwin",
    platform_machine="arm64",
    cpu_count=12,
    has_rust=True,
    rust_mode="on",
    has_cuda=False,
    has_mps=True,
)
MAC_NO_RUST = HardwareProfile(
    platform_system="Darwin",
    platform_machine="arm64",
    cpu_count=12,
    has_rust=False,
    rust_mode="off",
    has_cuda=False,
    has_mps=True,
)
WIN_CUDA_RUST = HardwareProfile(
    platform_system="Windows",
    platform_machine="AMD64",
    cpu_count=16,
    has_rust=True,
    rust_mode="on",
    has_cuda=True,
    has_mps=False,
    has_cupy=True,
    cuda_device_name="NVIDIA RTX A400",
)
WIN_CUDA_NO_RUST = HardwareProfile(
    platform_system="Windows",
    platform_machine="AMD64",
    cpu_count=16,
    has_rust=False,
    rust_mode="off",
    has_cuda=True,
    has_mps=False,
    has_cupy=True,
    cuda_device_name="NVIDIA RTX A400",
)
WIN_CUDA_NO_CUPY = HardwareProfile(
    platform_system="Windows",
    platform_machine="AMD64",
    cpu_count=16,
    has_rust=True,
    rust_mode="on",
    has_cuda=True,
    has_mps=False,
    has_cupy=False,
    cuda_device_name="NVIDIA RTX A400",
)
LINUX_CPU_RUST = HardwareProfile(
    platform_system="Linux",
    platform_machine="x86_64",
    cpu_count=32,
    has_rust=True,
    rust_mode="on",
    has_cuda=False,
    has_mps=False,
)
LINUX_CPU_NO_RUST = HardwareProfile(
    platform_system="Linux",
    platform_machine="x86_64",
    cpu_count=32,
    has_rust=False,
    rust_mode="off",
    has_cuda=False,
    has_mps=False,
)


def test_macos_apple_silicon_s0_crossover() -> None:
    """macOS with Rust chooses cpu_rust below MPS_S0_MIN_BATCH and mps at/above."""
    for b in (1, 10, 100, 1000, MPS_S0_MIN_BATCH - 1):
        choice = select_optimal_s0_backend(b, profile=MAC_RUST)
        assert choice.backend == "cpu_rust"
        assert choice.device == "cpu"

    for b in (MPS_S0_MIN_BATCH, 5000):
        choice = select_optimal_s0_backend(b, profile=MAC_RUST)
        assert choice.backend == "mps"
        assert choice.device == "mps"

    # Without Rust, Metal MPS beats pure Python NumPy for every batch size
    assert select_optimal_s0_backend(1, profile=MAC_NO_RUST).backend == "mps"
    assert select_optimal_s0_backend(100, profile=MAC_NO_RUST).backend == "mps"


def test_windows_cuda_s0_crossover() -> None:
    """Windows/Linux CUDA with Rust chooses cpu_rust < 200 and cuda >= 200."""
    for b in (1, 10, 50, CUDA_S0_MIN_BATCH - 1):
        choice = select_optimal_s0_backend(b, profile=WIN_CUDA_RUST)
        assert choice.backend == "cpu_rust"
        assert choice.device == "cpu"

    for b in (CUDA_S0_MIN_BATCH, 500, 10000):
        choice = select_optimal_s0_backend(b, profile=WIN_CUDA_RUST)
        assert choice.backend == "cuda"
        assert choice.device == "cuda"

    # Without Rust, CUDA beats pure Python NumPy even at B=1
    assert select_optimal_s0_backend(1, profile=WIN_CUDA_NO_RUST).backend == "cuda"


def test_cpu_only_hosts() -> None:
    """CPU-only machines select cpu_rust when compiled else cpu_python."""
    assert select_optimal_s0_backend(1, profile=LINUX_CPU_RUST).backend == "cpu_rust"
    assert select_optimal_s0_backend(5000, profile=LINUX_CPU_RUST).backend == "cpu_rust"
    assert (
        select_optimal_s0_backend(1, profile=LINUX_CPU_NO_RUST).backend == "cpu_python"
    )


def test_general_multizone_and_max_rung_selection() -> None:
    """General S1-S2b runs on CUDA hosts and fails closed to EnergyPlus elsewhere."""
    assert select_max_supported_rung(profile=WIN_CUDA_RUST) == "S2b"
    assert select_max_supported_rung(profile=WIN_CUDA_NO_RUST) == "S2b"
    assert select_max_supported_rung(profile=MAC_RUST) == "S0"
    assert select_max_supported_rung(profile=LINUX_CPU_RUST) == "S0"

    assert select_optimal_general_backend(5, profile=WIN_CUDA_RUST).backend == "cuda"
    assert (
        select_optimal_general_backend(5, profile=MAC_RUST).backend == "energyplus"
    )
    assert (
        select_optimal_general_backend(5, profile=LINUX_CPU_RUST).backend
        == "energyplus"
    )
    # Explicit cpu override restricts max rung to S0 even on CUDA host
    assert (
        select_max_supported_rung(requested_device="cpu", profile=WIN_CUDA_RUST) == "S0"
    )
    # Windows CUDA without CuPy fails closed safely instead of crashing on import
    assert select_max_supported_rung(profile=WIN_CUDA_NO_CUPY) == "S0"
    assert (
        select_optimal_s0_backend(500, profile=WIN_CUDA_NO_CUPY).backend == "cpu_rust"
    )
    assert (
        select_optimal_general_backend(5, profile=WIN_CUDA_NO_CUPY).backend
        == "energyplus"
    )


def test_shading_backend_prefers_rust_cwbvh8_everywhere() -> None:
    """Auto shading always prefers Rust CWBVH8 over MPS/CUDA/NumPy."""
    assert select_optimal_shading_backend(profile=MAC_RUST) == "cpu_rust"
    assert select_optimal_shading_backend(profile=WIN_CUDA_RUST) == "cpu_rust"
    assert select_optimal_shading_backend(profile=LINUX_CPU_RUST) == "cpu_rust"

    # Without Rust: CUDA > MPS > NumPy CPU
    assert select_optimal_shading_backend(profile=WIN_CUDA_NO_RUST) == "cuda"
    assert select_optimal_shading_backend(profile=MAC_NO_RUST) == "mps"
    assert select_optimal_shading_backend(profile=LINUX_CPU_NO_RUST) == "cpu_python"

    # Explicit GPU overrides honored when hardware exists
    assert (
        select_optimal_shading_backend(requested_device="mps", profile=MAC_RUST)
        == "mps"
    )
    assert (
        select_optimal_shading_backend(requested_device="cuda", profile=WIN_CUDA_RUST)
        == "cuda"
    )


def test_explicit_overrides_and_validation() -> None:
    """Explicit unavailable GPU or invalid device strings fail closed."""
    with pytest.raises(ValueError, match="Unsupported gpusim device"):
        select_optimal_s0_backend(1, requested_device="tpu", profile=MAC_RUST)

    with pytest.raises(RuntimeError, match="cuda"):
        select_optimal_s0_backend(1, requested_device="cuda", profile=MAC_RUST)

    with pytest.raises(RuntimeError, match="mps"):
        select_optimal_s0_backend(1, requested_device="mps", profile=WIN_CUDA_RUST)

    with pytest.raises(RuntimeError, match="cuda"):
        select_optimal_general_backend(1, requested_device="cuda", profile=MAC_RUST)

    assert (
        select_optimal_s0_backend(1, requested_device="mps", profile=MAC_RUST).backend
        == "mps"
    )
    assert (
        select_optimal_s0_backend(
            1, requested_device="cuda", profile=WIN_CUDA_RUST
        ).backend
        == "cuda"
    )


def test_route_idf_text_adapts_between_macos_and_windows_cuda(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Router switches engine & rung automatically across macOS vs Windows CUDA."""
    s0_idf = (GOLDEN_ROOT / CELL1_ID / "in.idf").read_text(encoding="utf-8")
    v15_idf = (V15_DIR / "in.idf").read_text(encoding="utf-8")

    # 1. Simulate macOS Apple Silicon + Rust
    monkeypatch.setattr(dispatch_mod, "probe_hardware", lambda use_cache=True: MAC_RUST)
    dec_mac_s0_small = route_idf_text(
        s0_idf, "b_s0", sim_engine="auto", spot_check_fraction=0.0, batch_size=10
    )
    assert dec_mac_s0_small.selected_engine == "gpusim"
    assert dec_mac_s0_small.engine_version.endswith("-cpu_rust")

    dec_mac_s0_large = route_idf_text(
        s0_idf, "b_s0", sim_engine="auto", spot_check_fraction=0.0, batch_size=2000
    )
    assert dec_mac_s0_large.selected_engine == "gpusim"
    assert dec_mac_s0_large.engine_version.endswith("-mps")

    dec_mac_v15 = route_idf_text(
        v15_idf, "b_v15", sim_engine="auto", spot_check_fraction=0.0, batch_size=10
    )
    assert dec_mac_v15.selected_engine == "energyplus"
    assert dec_mac_v15.reason.startswith("fallback_energyplus:")

    # 2. Simulate Windows NVIDIA CUDA + Rust
    monkeypatch.setattr(
        dispatch_mod, "probe_hardware", lambda use_cache=True: WIN_CUDA_RUST
    )
    dec_win_s0_small = route_idf_text(
        s0_idf, "b_s0", sim_engine="auto", spot_check_fraction=0.0, batch_size=10
    )
    assert dec_win_s0_small.selected_engine == "gpusim"
    assert dec_win_s0_small.engine_version.endswith("-cpu_rust")

    dec_win_s0_large = route_idf_text(
        s0_idf, "b_s0", sim_engine="auto", spot_check_fraction=0.0, batch_size=500
    )
    assert dec_win_s0_large.selected_engine == "gpusim"
    assert dec_win_s0_large.engine_version.endswith("-cuda")

    dec_win_v15 = route_idf_text(
        v15_idf, "b_v15", sim_engine="auto", spot_check_fraction=0.0, batch_size=10
    )
    assert dec_win_v15.selected_engine == "gpusim"
    assert dec_win_v15.subset_rung == "S1"
    assert dec_win_v15.engine_version.endswith("-cuda")
    assert select_device("auto", batch_size=10, rung="S0") == "cpu"
    assert select_device("auto", batch_size=500, rung="S0") == "cuda"


def test_live_host_probe_and_shading_auto_parity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live host probe works and auto shading matches pure-Python NumPy."""
    reset_hardware_cache()
    prof = probe_hardware(use_cache=False)
    assert prof.cpu_count >= 1
    assert config.SIM_ENGINE == "auto"
    assert config.RUST_BACKEND == "auto"

    target = [
        np.array(
            [[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [4.0, 0.0, 3.0], [0.0, 0.0, 3.0]],
            dtype=np.float64,
        )
    ]
    normals = np.array([[0.0, -1.0, 0.0]], dtype=np.float64)
    sun_exp = np.array([True], dtype=bool)
    occluder = [
        np.array(
            [[0.0, -2.0, 0.0], [4.0, -2.0, 0.0], [4.0, -2.0, 4.0], [0.0, -2.0, 4.0]],
            dtype=np.float64,
        )
    ]
    solcos = np.zeros((8760, 3), dtype=np.float64)
    solcos[:, 1] = -0.6
    solcos[:, 2] = 0.8

    monkeypatch.setenv("OPENUBEM_RUST_BACKEND", "auto")
    sun_auto, dif_auto = compute_exterior_shading(
        target, normals, sun_exp, occluder, solcos, periodic_days=60, device="auto"
    )
    monkeypatch.setenv("OPENUBEM_RUST_BACKEND", "off")
    sun_py, dif_py = compute_exterior_shading(
        target, normals, sun_exp, occluder, solcos, periodic_days=60, device="cpu"
    )
    assert np.allclose(sun_auto, sun_py, atol=1e-4)
    assert np.allclose(dif_auto, dif_py, atol=1e-4)
