import csv
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
    WGSL_PATH,
    benchmark_wgpu_launch,
    run_wgpu_spike,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPIKE_FIXTURE_DIR = REPO_ROOT / "tests/fixtures/gpusim/spike"
SPIKE_CSV_PATH = REPO_ROOT / "openubem/outputs/gpusim_m2_spike.csv"
METAL_DRIVER_PATH = (
    REPO_ROOT / "openubem/gpusim/backends/kernel/spike_metal.py"
)
WGPU_DRIVER_PATH = (
    REPO_ROOT / "openubem/gpusim/backends/kernel/spike_wgpu.py"
)

MAX_ALLOWED_DEL_TEMP_K: float = 0.002
MAX_ALLOWED_ITER_DIFF: int = 1
BENCH_RUNS: int = 20

CSV_FIELDS: tuple[str, ...] = (
    "candidate",
    "max_dt_k",
    "max_iter_diff",
    "gate_pass",
    "launch_ms_b346",
    "launch_ms_b10000",
    "kernel_lines",
    "driver_lines",
    "cuda_path",
    "install_notes",
)


def _count_lines(path: Path) -> int:
    """Count total lines in a UTF-8 source file.

    Args:
        path: File path to measure.

    Returns:
        Number of lines in the file.
    """
    return len(path.read_text(encoding="utf-8").splitlines())


def _load_captures(
    fixture_dir: Path = SPIKE_FIXTURE_DIR,
) -> list[tuple[str, dict[str, np.ndarray]]]:
    """Load all saved step-5 float64 captures sorted by filename.

    Args:
        fixture_dir: Directory containing ``<cell>__<step>.npz`` files.

    Returns:
        Sorted list of ``(capture_name, array_dict)`` pairs.
    """
    paths = sorted(fixture_dir.glob("*.npz"))
    if len(paths) != 15:
        raise FileNotFoundError(
            f"Expected 15 spike fixtures in {fixture_dir}, found {len(paths)}"
        )
    captures: list[tuple[str, dict[str, np.ndarray]]] = []
    for path in paths:
        with np.load(path) as data:
            captures.append((path.stem, {k: data[k] for k in data.files}))
    return captures


def _evaluate(
    captures: list[tuple[str, dict[str, np.ndarray]]],
    outputs: dict[str, np.ndarray],
) -> tuple[float, int]:
    """Compute worst inside-face temperature error and iteration-count delta.

    Args:
        captures: List of ``(name, capture_dict)`` pairs.
        outputs: Unpacked candidate output dictionary.

    Returns:
        Tuple ``(max_dt_k, max_iter_diff)``.
    """
    worst_dt = 0.0
    worst_iter_diff = 0
    for idx, (_, cap) in enumerate(captures):
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
        worst_dt = max(worst_dt, max_dt)
        worst_iter_diff = max(worst_iter_diff, abs(got_iters - ref_iters))
    return worst_dt, worst_iter_diff


def _check_portability_proxy() -> bool:
    """Run the clang++ C++17 syntax-only portability proxy on ``spike_common.h``.

    Returns:
        True if ``clang++`` exits with status 0.
    """
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
    return proc.returncode == 0


def run_spike_report(output_csv: Path = SPIKE_CSV_PATH) -> list[dict[str, str]]:
    """Run both spike candidates sequentially and write the M2 comparison CSV.

    Args:
        output_csv: Destination path for ``gpusim_m2_spike.csv``.

    Returns:
        List of two formatted CSV row dictionaries.
    """
    captures = _load_captures()
    packed_15 = pack_captures_soa([cap for _, cap in captures])
    packed_346 = tile_packed_soa(packed_15, 346)
    packed_10000 = tile_packed_soa(packed_15, 10000)

    proxy_ok = _check_portability_proxy()
    metal_out = run_metal_spike(packed_15)
    metal_dt, metal_iter_diff = _evaluate(captures, metal_out)
    metal_ms_346 = benchmark_metal_launch(packed_346, n_runs=BENCH_RUNS)
    metal_ms_10000 = benchmark_metal_launch(packed_10000, n_runs=BENCH_RUNS)
    metal_pass = (
        proxy_ok
        and metal_dt <= MAX_ALLOWED_DEL_TEMP_K
        and metal_iter_diff <= MAX_ALLOWED_ITER_DIFF
    )

    wgpu_out = run_wgpu_spike(packed_15)
    wgpu_dt, wgpu_iter_diff = _evaluate(captures, wgpu_out)
    wgpu_ms_346 = benchmark_wgpu_launch(packed_346, n_runs=BENCH_RUNS)
    wgpu_ms_10000 = benchmark_wgpu_launch(packed_10000, n_runs=BENCH_RUNS)
    wgpu_pass = (
        wgpu_dt <= MAX_ALLOWED_DEL_TEMP_K
        and wgpu_iter_diff <= MAX_ALLOWED_ITER_DIFF
    )

    rows: list[dict[str, str]] = [
        {
            "candidate": "a_pytorch_metal_header",
            "max_dt_k": f"{metal_dt:.6e}",
            "max_iter_diff": str(metal_iter_diff),
            "gate_pass": str(metal_pass),
            "launch_ms_b346": f"{metal_ms_346:.4f}",
            "launch_ms_b10000": f"{metal_ms_10000:.4f}",
            "kernel_lines": str(_count_lines(HEADER_PATH)),
            "driver_lines": str(_count_lines(METAL_DRIVER_PATH)),
            "cuda_path": "same header via load_inline",
            "install_notes": (
                "torch==2.7.1 wheel on macOS arm64; MPS compile_shader built-in; "
                "clang++ C++17 host proxy rc=0"
            ),
        },
        {
            "candidate": "b_wgpu_wgsl",
            "max_dt_k": f"{wgpu_dt:.6e}",
            "max_iter_diff": str(wgpu_iter_diff),
            "gate_pass": str(wgpu_pass),
            "launch_ms_b346": f"{wgpu_ms_346:.4f}",
            "launch_ms_b10000": f"{wgpu_ms_10000:.4f}",
            "kernel_lines": str(_count_lines(WGSL_PATH)),
            "driver_lines": str(_count_lines(WGPU_DRIVER_PATH)),
            "cuda_path": "WGSL via DX12/Vulkan, no CUDA",
            "install_notes": (
                "wgpu==0.31.0 wheel (newest Python >=3.10 release; "
                "0.31.1+ requires >=3.11); Metal adapter via wgpu-native"
            ),
        },
    ]

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    for row in rows:
        print(row)
    return rows


def main() -> None:
    """Entry point for generating ``openubem/outputs/gpusim_m2_spike.csv``."""
    run_spike_report()


if __name__ == "__main__":
    main()
