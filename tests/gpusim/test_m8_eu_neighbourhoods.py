"""M8 verification tests: Four European 3D Neighbourhoods GPU simulation & EU-11 parity."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from openubem.gpusim.backends.general_cuda import run_general_cuda
from openubem.gpusim.general_model import compile_general_batch
from openubem.gpusim.weather import load_epw_weather

ROOT = Path(__file__).resolve().parents[2]
M8_DISTRICTS_CSV = ROOT / "openubem" / "outputs" / "gpusim_m8_eu_districts.csv"
M8_PER_BLDG_CSV = ROOT / "openubem" / "outputs" / "gpusim_m8_eu_per_building.csv"

EXPECTED_DISTRICTS = (
    "ES-MAD-BERRUGUETE",
    "FR-LYO-HAUTCOEURPENTES",
    "GB-LDN-STDUNSTANS",
    "IT-BOL-GALVANI2",
)


def test_m8_four_districts_summary_present_and_accurate() -> None:
    """All 4 European neighbourhoods + pooled fleet row exist, cover >=95%, and track EU-11."""
    assert M8_DISTRICTS_CSV.exists(), f"Missing {M8_DISTRICTS_CSV}"
    df = pd.read_csv(M8_DISTRICTS_CSV)
    got = set(df["district"])
    for code in (*EXPECTED_DISTRICTS, "FLEET_4EU"):
        assert code in got, f"Missing district {code} in {M8_DISTRICTS_CSV}"

    for code in EXPECTED_DISTRICTS:
        row = df.loc[df["district"] == code].iloc[0]
        assert row["coverage_pct"] >= 95.0, f"{code} coverage too low: {row['coverage_pct']:.1f}%"
        assert row["n_zones"] > row["n_simulated_homes"], f"{code} must be multi-zone"
        assert row["gpu_eui_kwh_m2"] > 20.0 and row["gpu_eui_kwh_m2"] < 150.0
        # Pooled district EUI tracks published EU-11 EnergyPlus within 12%
        assert abs(row["rel_eui_diff_pct"]) < 12.0, (
            f"{code} EUI diff {row['rel_eui_diff_pct']:+.2f}% exceeds 12%"
        )
        # Per-building total heating kWh R^2 across full district
        assert row["r2_kwh"] >= 0.85, f"{code} R^2_kwh too low: {row['r2_kwh']:.4f}"
        # Zero Windows WDDM TDR violations (< 2.0 s)
        assert row["max_launch_s"] < 2.0, f"{code} max_launch_s={row['max_launch_s']:.3f}s"

    fleet = df.loc[df["district"] == "FLEET_4EU"].iloc[0]
    assert fleet["n_simulated_homes"] >= 3800
    assert fleet["n_zones"] >= 40000
    assert abs(fleet["rel_eui_diff_pct"]) < 10.0
    assert fleet["r2_kwh"] >= 0.90


def test_m8_per_building_csv_integrity() -> None:
    """Per-building M8 table has zero NaN/negative values and matches summary totals."""
    assert M8_PER_BLDG_CSV.exists(), f"Missing {M8_PER_BLDG_CSV}"
    per = pd.read_csv(M8_PER_BLDG_CSV)
    dist = pd.read_csv(M8_DISTRICTS_CSV)

    assert len(per) >= 3800
    assert not per["gpu_heating_kwh"].isna().any()
    assert not per["pub_heating_kwh"].isna().any()
    assert (per["gpu_heating_kwh"] >= 0.0).all()
    assert (per["n_zones"] >= 1).all()
    assert (per["n_surfaces"] >= 6).all()

    fleet = dist.loc[dist["district"] == "FLEET_4EU"].iloc[0]
    assert int(fleet["n_simulated_homes"]) == len(per)
    assert np.isclose(
        float(per["gpu_heating_kwh"].sum()),
        float(fleet["gpu_heating_kwh"]),
        rtol=1e-5,
    )


def test_zone_parallel_cuda_matches_building_parallel(tmp_path: Path) -> None:
    """Zone-parallel CUDA kernel matches building-parallel kernel to < 0.25% on multi-zone."""
    import scripts.gpusim.verify_m7c_s2b as m7c

    p1 = tmp_path / "3z_uncond.idf"
    p1.write_text(m7c._build_eu_3zone_apartment_idf(m7c.BOLOGNA_EPW, "3z_uncond"), encoding="utf-8")
    p2 = tmp_path / "duplex.idf"
    p2.write_text(m7c._build_2storey_duplex_idf(m7c.BOLOGNA_EPW, "duplex"), encoding="utf-8")
    w = load_epw_weather(m7c.BOLOGNA_EPW, steps_per_hour=12)
    batch = compile_general_batch(
        [p1, p2], [w, w], np.zeros(2, dtype=np.int32), ["3z_uncond", "duplex"], compute_shading=False
    )
    r_bldg = run_general_cuda(batch, [w], zone_parallel=False)
    r_zone = run_general_cuda(batch, [w], zone_parallel=True, run_chunk_steps=144)

    for i, bid in enumerate(batch.building_ids):
        rel = abs(r_zone.annual_heating_kwh[i] - r_bldg.annual_heating_kwh[i]) / r_bldg.annual_heating_kwh[i]
        assert rel < 0.0025, f"{bid}: zone_parallel rel diff {rel:.4%} >= 0.25%"
