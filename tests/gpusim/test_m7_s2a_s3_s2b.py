"""M7a/M7b/M7c (S2a layered walls, S3 exterior shading, S2b multi-zone) test suite."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from openubem.gpusim.ctf import LayerSpec, build_modal_conduction
from openubem.gpusim.general_model import check_general_subset
from openubem.gpusim.schedules import compile_schedule_compact_hourly

REPO_ROOT = Path(__file__).resolve().parents[2]
M7A_CSV = REPO_ROOT / "openubem/outputs/gpusim_m7a_s2a.csv"
M7B_CSV = REPO_ROOT / "openubem/outputs/gpusim_m7b_s3.csv"
M7C_CSV = REPO_ROOT / "openubem/outputs/gpusim_m7c_s2b.csv"


def test_modal_conduction_thick_wall_zero_float32_cancellation() -> None:
    """10 cm XPS + 25 cm heavy concrete must stay within 0.01% in float32 vs float64."""
    thick = [
        LayerSpec("xps", False, 0.0, 0.10, 0.034, 35.0, 1400.0),
        LayerSpec("conc", False, 0.0, 0.25, 1.4, 2300.0, 1000.0),
    ]
    m = build_modal_conduction(thick, dt_sec=300.0, construction_name="THICK_XPS_CONC")

    def _run(dtype):
        n = 4000
        t = np.arange(n, dtype=dtype)
        t_out = (dtype(5.0) + dtype(12.0) * np.sin(dtype(2 * np.pi / 288.0) * t)).astype(dtype)
        t_in = np.full(n, dtype(20.0), dtype=dtype)
        dec = m.decay.astype(dtype)
        gno, gni = m.g_new_out.astype(dtype), m.g_new_in.astype(dtype)
        goo, goi = m.g_old_out.astype(dtype), m.g_old_in.astype(dtype)
        ci = m.c_in.astype(dtype)
        z = (m.steady_out.astype(dtype) * dtype(20.0) + m.steady_in.astype(dtype) * dtype(20.0)).astype(dtype)
        to_p = dtype(20.0)
        ti_p = dtype(20.0)
        qin = np.empty(n, dtype=dtype)
        for i in range(n):
            zf = dec * z + goo * to_p + goi * ti_p
            const_in = np.sum(ci * zf)
            qin[i] = dtype(m.ctf_cross0) * t_out[i] - dtype(m.ctf_in0) * t_in[i] + const_in
            z = zf + gno * t_out[i] + gni * t_in[i]
            to_p, ti_p = t_out[i], t_in[i]
        return qin

    q64 = _run(np.float64)
    q32 = _run(np.float32).astype(np.float64)
    rel = abs(q32.sum() - q64.sum()) / abs(q64.sum())
    assert rel < 1.0e-4, f"Float32 modal conduction drift too high: {rel:.3e}"


def test_schedule_compact_compiler_weekdays_weekends() -> None:
    fields = [
        "HeatSP", "Any Number",
        "Through: 12/31",
        "For: Weekdays",
        "Until: 07:00", "17.0",
        "Until: 22:00", "21.0",
        "Until: 24:00", "17.0",
        "For: AllOtherDays",
        "Until: 24:00", "19.0",
    ]
    arr = compile_schedule_compact_hourly(fields, start_day_of_week=0)  # Jan 1 = Sunday
    assert arr.shape == (8760,)
    # Day 0 = Sunday -> 19.0 all day
    assert np.allclose(arr[:24], 19.0)
    # Day 1 = Monday -> 17.0 (0..6), 21.0 (7..21), 17.0 (22..23)
    assert np.allclose(arr[24:31], 17.0)
    assert np.allclose(arr[31:46], 21.0)
    assert np.allclose(arr[46:48], 17.0)


def test_general_subset_fails_closed_on_packaged_hvac() -> None:
    ptac = "Version,23.1;\nZone,Z1;\nHVACTemplate:Zone:PTAC,Z1,T1;\n"
    rung, res = check_general_subset(ptac)
    assert rung is None
    assert not res.passed
    assert "PTAC" in (res.reason or "").upper()


def test_m7_verified_csv_outputs() -> None:
    assert M7A_CSV.is_file()
    assert M7B_CSV.is_file()
    assert M7C_CSV.is_file()

    r_a = {r["case"]: r for r in csv.DictReader(M7A_CSV.open(encoding="utf-8"))}
    assert abs(float(r_a["ASHRAE140_900_Heavy_NoWind"]["rel_cuda_vs_ep"])) <= 0.025
    assert abs(float(r_a["Thick_10XPS_25Conc_Madrid"]["rel_cuda_vs_ep"])) <= 0.03
    assert abs(float(r_a["TABULA_38cmBrick_Sched_Gains"]["rel_cuda_vs_ep"])) <= 0.03

    r_b = {r["case"]: r for r in csv.DictReader(M7B_CSV.open(encoding="utf-8"))}
    assert abs(float(r_b["Unshaded_Ref_Bologna"]["rel_cuda_vs_ep"])) <= 0.015
    assert abs(float(r_b["Canyon_H12_W8_Bologna"]["rel_cuda_vs_ep"])) <= 0.025
    assert abs(float(r_b["Courtyard_3Side_Bologna"]["rel_cuda_vs_ep"])) <= 0.035
    assert abs(float(r_b["Overhang_1p5m_Madrid"]["rel_cuda_vs_ep"])) <= 0.025

    r_c = {r["case"]: r for r in csv.DictReader(M7C_CSV.open(encoding="utf-8"))}
    for case in ("EU_3Zone_UncondCore_Bol", "EU_3Zone_AllCond_Bol", "EU_3Zone_UncondCore_Mad", "Duplex_2Storey_Slab_Bol"):
        assert abs(float(r_c[case]["rel_cuda_vs_ep"])) <= 0.025
