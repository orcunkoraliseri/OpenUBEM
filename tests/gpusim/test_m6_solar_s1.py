"""M6 Rung S1 (Solar Gains) verification test suite."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from openubem.gpusim.backends.general_cuda import run_general_cuda
from openubem.gpusim.general_model import compile_general_batch
from openubem.gpusim.physics.solar import (
    calc_perez_sky_factors,
    calc_solar_direction_cosines,
    calc_surface_incident_solar,
    simple_glazing_normal_optics,
)
from openubem.gpusim.router import route_idf_text
from openubem.gpusim.subset import check_s0_subset, check_s1_subset
from openubem.gpusim.weather import load_epw_weather

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = REPO_ROOT / "tests/fixtures/gpusim/golden"
CELL1_ID = "it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100"
V15_DIR = GOLDEN_ROOT / "variants" / f"{CELL1_ID}__V15"
SCHED_DIR = REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2/schedules"
BOLOGNA_EPW = REPO_ROOT / "openubem/data/weather/it_bologna_2013_2014_y2014.epw"
M6_CSV = REPO_ROOT / "openubem/outputs/gpusim_m6_s1.csv"


def test_s1_subset_accepts_v15_while_s0_rejects() -> None:
    v15_exp = (V15_DIR / "eplusout.expidf").read_text(encoding="utf-8")
    assert not check_s0_subset(v15_exp).passed
    assert check_s1_subset(v15_exp).passed
    dec = route_idf_text(v15_exp, "V15", sim_engine="gpusim", device="cuda", max_rung="S1")
    assert dec.selected_engine == "gpusim"
    assert dec.subset_rung == "S1"


def test_solar_geometry_and_glazing_optics_units() -> None:
    sx, sy, sz, iext = calc_solar_direction_cosines(44.5, 11.25, 1.0, steps_per_hour=12, n_days=365)
    assert sx.shape == (105120,)
    # Sun elevation peaks around ~69 deg on summer solstice at lat 44.5 N
    assert 0.90 < float(np.max(sz)) < 0.95
    assert 1320.0 < float(np.min(iext)) < 1330.0
    assert 1405.0 < float(np.max(iext)) < 1420.0

    t_sol, r_sol, a_sol = simple_glazing_normal_optics(np.array([4.56, 2.0]), np.array([0.357, 0.65]))
    assert np.allclose(t_sol + r_sol + a_sol, 1.0, atol=1e-12)
    assert 0.18 < t_sol[0] < 0.21
    assert 0.55 < t_sol[1] < 0.62


def test_v15_cuda_matches_golden_energyplus_within_s1_gate() -> None:
    w = load_epw_weather(BOLOGNA_EPW, steps_per_hour=12)
    gb = compile_general_batch(
        [V15_DIR / "in.idf"],
        [w],
        np.array([0], dtype=np.int32),
        ["V15"],
        [SCHED_DIR],
        compute_shading=False,
    )
    res = run_general_cuda(gb, [w], record_zone_temp=True, run_chunk_days=3)
    ts = pd.read_parquet(V15_DIR / "timestep.parquet")
    ep_h = (
        ts["EU_CELL_ZONE IDEAL LOADS AIR SYSTEM:Zone Ideal Loads Zone Total Heating Energy [J](TimeStep)"]
        .to_numpy(dtype=np.float64)
        .reshape(8760, 12)
        .sum(axis=1)
    )
    gpu_h = res.hourly_heating_j[0]
    ep_ann = float(ep_h.sum() / 3.6e6)
    gpu_ann = float(res.annual_heating_kwh[0])
    rel = abs(gpu_ann - ep_ann) / ep_ann
    cv_rmse = float(np.sqrt(np.mean((gpu_h - ep_h) ** 2)) / np.mean(ep_h))
    nmbe = abs(float(np.sum(gpu_h - ep_h) / np.sum(ep_h)))

    assert rel <= 0.015, f"V15 annual rel={rel:.4%}"
    assert cv_rmse <= 0.035, f"V15 CV(RMSE)={cv_rmse:.4%}"
    assert nmbe <= 0.003, f"V15 |NMBE|={nmbe:.4%}"


def test_m6_s1_summary_csv_gates() -> None:
    assert M6_CSV.is_file()
    rows = {r["case"]: r for r in csv.DictReader(M6_CSV.open(encoding="utf-8"))}
    for case in ("V15_FullExterior", "V15_MinimalShadowing", "EU_Cell1_D1_D2", "EU_Cell3_Madrid_D1_D2"):
        r = rows[case]
        assert abs(float(r["rel_cuda_vs_ep"])) <= 0.015
        assert float(r["cv_rmse"]) <= 0.035
        assert abs(float(r["nmbe"])) <= 0.003
        assert abs(float(r["rel_cuda_vs_sa"])) <= 0.001
