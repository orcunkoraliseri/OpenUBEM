from pathlib import Path
import subprocess

import numpy as np

from openubem.gpusim.backends.kernel.spike_metal import (
    HEADER_PATH,
    benchmark_metal_launch,
    pack_captures_soa,
    run_metal_spike,
    tile_packed_soa,
)
from openubem.gpusim.backends.kernel.spike_wgpu import (
    benchmark_wgpu_launch,
    run_wgpu_spike,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPIKE_FIXTURE_DIR = REPO_ROOT / "tests/fixtures/gpusim/spike"
MAX_ALLOWED_DEL_TEMP_K: float = 0.002
MAX_ALLOWED_ITER_DIFF: int = 1
EXPECTED_CAPTURE_COUNT: int = 15
MAX_FIXTURE_TOTAL_BYTES: int = 20 * 1024 * 1024


def load_spike_captures(
    fixture_dir: Path = SPIKE_FIXTURE_DIR,
) -> list[tuple[str, dict[str, np.ndarray]]]:
    """Load all saved step-5 float64 captures sorted by filename.

    Args:
        fixture_dir: Directory containing ``<cell>__<step>.npz`` files.

    Returns:
        Sorted list of ``(capture_name, array_dict)`` pairs.
    """
    paths = sorted(fixture_dir.glob("*.npz"))
    assert len(paths) == EXPECTED_CAPTURE_COUNT, (
        f"Expected {EXPECTED_CAPTURE_COUNT} captures in {fixture_dir}, "
        f"found {len(paths)}"
    )
    total_bytes = sum(p.stat().st_size for p in paths)
    assert total_bytes <= MAX_FIXTURE_TOTAL_BYTES, (
        f"Spike fixtures total {total_bytes} bytes > {MAX_FIXTURE_TOTAL_BYTES}"
    )
    captures: list[tuple[str, dict[str, np.ndarray]]] = []
    for path in paths:
        with np.load(path) as data:
            captures.append((path.stem, {k: data[k] for k in data.files}))
    return captures


def evaluate_spike_outputs(
    captures: list[tuple[str, dict[str, np.ndarray]]],
    outputs: dict[str, np.ndarray],
) -> tuple[float, int, list[tuple[str, float, int, int, int]]]:
    """Compare candidate kernel outputs against float64 Stage B captures.

    Args:
        captures: List of ``(name, capture_dict)`` pairs.
        outputs: Unpacked kernel output dictionary for the matching batch.

    Returns:
        Tuple ``(worst_dt_k, worst_iter_diff, per_capture_rows)``.
    """
    worst_dt = 0.0
    worst_iter_diff = 0
    rows: list[tuple[str, float, int, int, int]] = []
    for idx, (name, cap) in enumerate(captures):
        ref_t_in = np.asarray(cap["t_surf_in_out"], dtype=np.float64)
        if ref_t_in.ndim == 2:
            ref_t_in = ref_t_in[0]
        mask = np.asarray(cap["surf_mask"], dtype=np.bool_)
        if mask.ndim == 2:
            mask = mask[0]
        s_orig = ref_t_in.shape[0]
        got_t_in = outputs["t_surf_in_out"][idx, :s_orig]
        max_dt = float(np.max(np.abs(got_t_in[mask] - ref_t_in[mask])))
        ref_iters = int(np.asarray(cap["iter_count"]).reshape(-1)[0])
        got_iters = int(outputs["iter_count"][idx])
        iter_diff = got_iters - ref_iters
        worst_dt = max(worst_dt, max_dt)
        worst_iter_diff = max(worst_iter_diff, abs(iter_diff))
        rows.append((name, max_dt, ref_iters, got_iters, iter_diff))
    return worst_dt, worst_iter_diff, rows


def test_spike_metal() -> None:
    """Verify Metal spike kernel accuracy, C++17 portability proxy, and launch speed."""
    proc = subprocess.run(
        [
            "clang++",
            "-std=c++17",
            "-fsyntax-only",
            "-x",
            "c++",
            "-DGPUSIM_HOST",
            str(HEADER_PATH),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"clang++ portability proxy failed (rc={proc.returncode}): {proc.stderr}"
    )

    captures = load_spike_captures()
    packed_15 = pack_captures_soa([cap for _, cap in captures])
    outputs = run_metal_spike(packed_15)
    worst_dt, worst_iter_diff, rows = evaluate_spike_outputs(captures, outputs)

    for name, max_dt, ref_it, got_it, diff in rows:
        print(
            f"[metal] {name}: max_dt={max_dt:.6e} K "
            f"iters={got_it} (ref={ref_it}, diff={diff:+d})"
        )

    packed_346 = tile_packed_soa(packed_15, 346)
    packed_10000 = tile_packed_soa(packed_15, 10000)
    ms_346 = benchmark_metal_launch(packed_346, n_runs=20)
    ms_10000 = benchmark_metal_launch(packed_10000, n_runs=20)
    print(
        f"[metal] summary: worst_dt={worst_dt:.6e} K "
        f"max_abs_iter_diff={worst_iter_diff} "
        f"median_ms_b346={ms_346:.4f} median_ms_b10000={ms_10000:.4f}"
    )

    assert worst_dt <= MAX_ALLOWED_DEL_TEMP_K, (
        f"Metal max |dT|={worst_dt:.6e} K exceeds {MAX_ALLOWED_DEL_TEMP_K} K"
    )
    assert worst_iter_diff <= MAX_ALLOWED_ITER_DIFF, (
        f"Metal max |iter_diff|={worst_iter_diff} exceeds {MAX_ALLOWED_ITER_DIFF}"
    )


def test_spike_wgpu() -> None:
    """Verify wgpu/WGSL spike kernel accuracy and launch speed on Metal adapter."""
    captures = load_spike_captures()
    packed_15 = pack_captures_soa([cap for _, cap in captures])
    outputs = run_wgpu_spike(packed_15)
    worst_dt, worst_iter_diff, rows = evaluate_spike_outputs(captures, outputs)

    for name, max_dt, ref_it, got_it, diff in rows:
        print(
            f"[wgpu] {name}: max_dt={max_dt:.6e} K "
            f"iters={got_it} (ref={ref_it}, diff={diff:+d})"
        )

    packed_346 = tile_packed_soa(packed_15, 346)
    packed_10000 = tile_packed_soa(packed_15, 10000)
    ms_346 = benchmark_wgpu_launch(packed_346, n_runs=20)
    ms_10000 = benchmark_wgpu_launch(packed_10000, n_runs=20)
    print(
        f"[wgpu] summary: worst_dt={worst_dt:.6e} K "
        f"max_abs_iter_diff={worst_iter_diff} "
        f"median_ms_b346={ms_346:.4f} median_ms_b10000={ms_10000:.4f}"
    )

    assert worst_dt <= MAX_ALLOWED_DEL_TEMP_K, (
        f"wgpu max |dT|={worst_dt:.6e} K exceeds {MAX_ALLOWED_DEL_TEMP_K} K"
    )
    assert worst_iter_diff <= MAX_ALLOWED_ITER_DIFF, (
        f"wgpu max |iter_diff|={worst_iter_diff} exceeds {MAX_ALLOWED_ITER_DIFF}"
    )
