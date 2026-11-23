import csv
import os
import re
import subprocess
from pathlib import Path

import cupy as cp
import numpy as np
import torch

from openubem.gpusim.backends.numpy_ref import run_stage_a_batch
from tests.gpusim.test_cells import CELL1_ID, CELLS_CSV_PATH, GOLDEN_CELL_IDS, GOLDEN_ROOT, REPO_ROOT
from tests.gpusim.test_stage_c import (
    STAGE_A_P1_CACHE_DIR,
    _load_batch_and_weather,
)

SPIKE_DIR = REPO_ROOT / "tests/fixtures/gpusim/spike"
REP2_DIR = REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2"
SETUP_CSV_PATH = REPO_ROOT / "openubem/outputs/gpusim_m4_setup.csv"

SETUP_FIELDS = [
    "gpu_name",
    "gpu_memory_gb",
    "compute_capability",
    "driver_version",
    "cuda_runtime",
    "torch_version",
    "cupy_version",
    "cpu_cores",
    "tdr_delay_s",
    "eplus_path",
    "eplus_build",
    "stage_a_rel_win_vs_mac",
]


def _query_driver_version() -> str:
    """Query the NVIDIA display driver version via nvidia-smi."""
    out = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-gpu=driver_version",
            "--format=csv,noheader",
        ],
        text=True,
    )
    return out.strip().splitlines()[0].strip()


def _query_tdr_delay_s() -> int:
    """Read Windows GraphicsDrivers TdrDelay in seconds (default 2 if absent)."""
    proc = subprocess.run(
        [
            "reg",
            "query",
            r"HKLM\System\CurrentControlSet\Control\GraphicsDrivers",
            "/v",
            "TdrDelay",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return 2
    match = re.search(r"TdrDelay\s+REG_DWORD\s+0x([0-9a-fA-F]+)", proc.stdout)
    if not match:
        return 2
    return int(match.group(1), 16)


def _find_eplus_231() -> tuple[Path, str]:
    """Locate native Windows EnergyPlus 23.1.0 and return its path and build string."""
    candidates = [
        Path(r"C:\EnergyPlusV23-1-0\energyplus.exe"),
        Path(r"C:\EnergyPlus-23-1-0\energyplus.exe"),
    ]
    for cand in candidates:
        if cand.is_file():
            out = subprocess.check_output([str(cand), "--version"], text=True).strip()
            return cand, out
    raise FileNotFoundError("EnergyPlus 23.1.0 executable not found on Windows")


def _load_mac_stage_a_cell1_kwh() -> float:
    """Read the Mac Stage A float64 annual heating for Cell 1 from M1 CSV (B=3)."""
    with CELLS_CSV_PATH.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["cell"] == CELL1_ID:
                return float(row["annual_stage_a_kwh"])
    raise KeyError(f"{CELL1_ID} not found in {CELLS_CSV_PATH}")


def test_windows_setup() -> None:
    """Verify CUDA torch, CuPy NVRTC, required files, EnergyPlus, and Stage A parity."""
    assert torch.cuda.is_available(), "torch.cuda.is_available() returned False"

    props = torch.cuda.get_device_properties(0)
    gpu_name = str(props.name)
    gpu_mem_gb = float(props.total_memory) / (1024.0**3)
    cc_str = f"{props.major}.{props.minor}"
    driver_version = _query_driver_version()
    cuda_runtime = str(torch.version.cuda or "")
    torch_version = str(torch.__version__)
    cupy_version = str(cp.__version__)
    cpu_cores = int(os.cpu_count() or 1)
    tdr_delay_s = _query_tdr_delay_s()
    eplus_path, eplus_build = _find_eplus_231()
    assert "23.1.0" in eplus_build, f"Unexpected EnergyPlus version: {eplus_build}"

    add_kernel = cp.RawKernel(
        r"""
        extern "C" __global__ void add_one(const float* x, float* y, int n) {
            int i = blockIdx.x * blockDim.x + threadIdx.x;
            if (i < n) y[i] = x[i] + 1.0f;
        }
        """,
        "add_one",
    )
    x_t = torch.arange(16, dtype=torch.float32, device="cuda")
    y_t = torch.empty_like(x_t)
    stream_ptr = int(torch.cuda.current_stream().cuda_stream)

    class _StreamProto:
        def __cuda_stream__(self) -> tuple[int, int]:
            return (0, stream_ptr)

    with cp.cuda.Stream.from_external(_StreamProto()):
        add_kernel((1,), (16,), (cp.from_dlpack(x_t), cp.from_dlpack(y_t), np.int32(16)))
    torch.cuda.synchronize()
    np.testing.assert_allclose(
        y_t.cpu().numpy(),
        np.arange(1, 17, dtype=np.float32),
        rtol=0.0,
        atol=0.0,
    )

    spike_npz = list(SPIKE_DIR.glob("*.npz"))
    stage_a_npz = list(STAGE_A_P1_CACHE_DIR.glob("*.npz"))
    manifest_files = list((REP2_DIR / "manifests").iterdir())
    sched_files = list((REP2_DIR / "schedules").iterdir())
    complete_cells = [
        d
        for d in REP2_DIR.iterdir()
        if d.is_dir()
        and (d / "eplusout.expidf").is_file()
        and (d / "eplusout.csv").is_file()
        and (d / "eplusout.eio").is_file()
    ]
    assert len(spike_npz) == 15, f"Expected 15 spike .npz, found {len(spike_npz)}"
    assert len(stage_a_npz) == 12, f"Expected 12 stage_a_p1 .npz, found {len(stage_a_npz)}"
    assert len(manifest_files) == 395, f"Expected 395 manifests, found {len(manifest_files)}"
    assert len(complete_cells) == 346, f"Expected 346 complete cells, found {len(complete_cells)}"
    assert len(sched_files) > 0, "Expected rep2/schedules to be non-empty"

    batch, weathers = _load_batch_and_weather(
        tuple(GOLDEN_ROOT / cid for cid in GOLDEN_CELL_IDS)
    )
    res_win = run_stage_a_batch(batch, weathers, record_zone_temp=False)
    win_kwh = float(res_win.annual_heating_kwh[0])
    mac_kwh = _load_mac_stage_a_cell1_kwh()
    rel_win_vs_mac = (win_kwh - mac_kwh) / mac_kwh
    assert abs(rel_win_vs_mac) <= 1.0e-6, (
        f"Stage A Windows ({win_kwh:.6f}) vs Mac ({mac_kwh:.6f}) rel={rel_win_vs_mac:.3e}"
    )

    row = {
        "gpu_name": gpu_name,
        "gpu_memory_gb": f"{gpu_mem_gb:.3f}",
        "compute_capability": cc_str,
        "driver_version": driver_version,
        "cuda_runtime": cuda_runtime,
        "torch_version": torch_version,
        "cupy_version": cupy_version,
        "cpu_cores": str(cpu_cores),
        "tdr_delay_s": str(tdr_delay_s),
        "eplus_path": str(eplus_path),
        "eplus_build": eplus_build,
        "stage_a_rel_win_vs_mac": f"{rel_win_vs_mac:.8e}",
    }
    SETUP_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETUP_CSV_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=SETUP_FIELDS)
        writer.writeheader()
        writer.writerow(row)
    assert SETUP_CSV_PATH.is_file()

    print(
        f"T01 Windows setup OK: {gpu_name} ({gpu_mem_gb:.2f} GB, cc {cc_str}, "
        f"driver {driver_version}, CUDA {cuda_runtime}, torch {torch_version}, "
        f"cupy {cupy_version}, cpu_cores={cpu_cores}, tdr={tdr_delay_s}s) | "
        f"E+={eplus_build} | stage_a_rel_win_vs_mac={rel_win_vs_mac:.3e}"
    )
