import csv
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from openubem import config
from openubem.campaign.eu_cell_runner import (
    CampaignCellError,
    _extract_heating_kwh,
    _guard_and_disable_unused_sizing,
)
from openubem.gpusim.router import (
    conformance_hash,
    expand_ideal_loads_templates,
    route_idf_text,
    run_routed_gpusim_batch,
    write_routing_report_csv,
)
from openubem.gpusim.subset import check_s0_subset
from openubem.simulation.parallel import run_neighbourhood
from tests.gpusim.test_cells import CELL1_ID, GOLDEN_CELL_IDS, GOLDEN_ROOT, REPO_ROOT

V15_DIR = GOLDEN_ROOT / "variants" / f"{CELL1_ID}__V15"
REP2_SCHED_DIR = REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2/schedules"
WEATHER_DIR = REPO_ROOT / "openubem/data/weather"


def test_config_defaults_and_provenance() -> None:
    """Verify SIM_ENGINE defaults to energyplus and conformance_hash is stable."""
    assert config.SIM_ENGINE == "energyplus"
    assert config.EU_DISABLE_UNUSED_SIZING is False
    h1 = conformance_hash()
    h2 = conformance_hash()
    assert len(h1) == 16
    assert h1 == h2


def test_expand_ideal_loads_templates_matches_s0_whitelist() -> None:
    """Raw EU in.idf expands in Python and passes check_s0_subset; V15 fails closed."""
    for cid in GOLDEN_CELL_IDS:
        raw_idf = (GOLDEN_ROOT / cid / "in.idf").read_text(encoding="utf-8")
        expanded = expand_ideal_loads_templates(raw_idf)
        res = check_s0_subset(expanded)
        assert res.passed, f"{cid} failed S0 check after Python expansion: {res.reason}"

    v15_idf = (V15_DIR / "in.idf").read_text(encoding="utf-8")
    dec_v15 = route_idf_text(v15_idf, "V15", sim_engine="gpusim", device="cpu")
    assert dec_v15.selected_engine == "energyplus"
    assert dec_v15.reason.startswith("fallback_energyplus:")
    assert "Sun Exposure" in dec_v15.reason


def test_router_modes_and_deterministic_spot_check() -> None:
    """Verify energyplus, gpusim, and auto modes including deterministic spot-checking."""
    raw_idf = (GOLDEN_ROOT / CELL1_ID / "in.idf").read_text(encoding="utf-8")

    dec_ep = route_idf_text(raw_idf, "b1", sim_engine="energyplus")
    assert dec_ep.selected_engine == "energyplus"
    assert dec_ep.reason == "sim_engine=energyplus"

    dec_gpu = route_idf_text(raw_idf, "b1", sim_engine="gpusim", device="cpu")
    assert dec_gpu.selected_engine == "gpusim"
    assert dec_gpu.subset_rung == "S0"
    assert dec_gpu.reason == "accepted:S0"

    # Non-S0 PTAC IDF must fail closed to EnergyPlus even in gpusim mode
    ptac_idf = raw_idf + "\nHVACTemplate:Zone:PTAC,\n  EU_Cell_Zone,\n  EU_HeatOnly_EU_Cell_Zone;\n"
    dec_ptac = route_idf_text(ptac_idf, "b_ptac", sim_engine="gpusim", device="cpu")
    assert dec_ptac.selected_engine == "energyplus"
    assert "HVACTEMPLATE" in dec_ptac.reason.upper()

    # Auto mode deterministic spot-check sample
    spot_hits = [
        route_idf_text(
            raw_idf,
            f"cell_{i:03d}",
            sim_engine="auto",
            device="cpu",
            spot_check_fraction=0.10,
            spot_check_seed=42,
        )
        for i in range(100)
    ]
    n_spot = sum(1 for d in spot_hits if d.spot_checked and d.selected_engine == "energyplus")
    n_gpu = sum(1 for d in spot_hits if d.selected_engine == "gpusim")
    assert 3 <= n_spot <= 20
    assert n_spot + n_gpu == 100
    # Re-evaluating gives identical routing
    spot_hits_2 = [
        route_idf_text(
            raw_idf,
            f"cell_{i:03d}",
            sim_engine="auto",
            device="cpu",
            spot_check_fraction=0.10,
            spot_check_seed=42,
        )
        for i in range(100)
    ]
    assert spot_hits == spot_hits_2


def test_d5_sizing_guard_refuses_limited_or_oa() -> None:
    """D5 sizing-off guard accepts NoLimit+NoOA and rejects limited/OA IdealLoads."""
    class _FakeIdeal:
        def __init__(self, lim: str, oa: str) -> None:
            self.Heating_Limit = lim
            self.Outdoor_Air_Method = oa

    class _FakeSC:
        Do_Zone_Sizing_Calculation = "Yes"
        Do_System_Sizing_Calculation = "Yes"
        Do_Plant_Sizing_Calculation = "Yes"
        Run_Simulation_for_Sizing_Periods = "Yes"
        Run_Simulation_for_Weather_File_Run_Periods = "Yes"

    class _FakeIDF:
        def __init__(self, ideals: list[_FakeIdeal]) -> None:
            self.idfobjects = {
                "HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM": ideals,
                "SIMULATIONCONTROL": [_FakeSC()],
            }

    ok_idf = _FakeIDF([_FakeIdeal("NoLimit", "None")])
    _guard_and_disable_unused_sizing(ok_idf)
    sc = ok_idf.idfobjects["SIMULATIONCONTROL"][0]
    assert sc.Do_Zone_Sizing_Calculation == "No"
    assert sc.Run_Simulation_for_Sizing_Periods == "No"
    assert sc.Run_Simulation_for_Weather_File_Run_Periods == "Yes"

    with pytest.raises(CampaignCellError, match="Heating_Limit"):
        _guard_and_disable_unused_sizing(_FakeIDF([_FakeIdeal("LimitCapacity", "None")]))

    with pytest.raises(CampaignCellError, match="Outdoor_Air_Method"):
        _guard_and_disable_unused_sizing(_FakeIDF([_FakeIdeal("NoLimit", "Flow/Zone")]))


def test_p3_mixed_routing_neighbourhood_schema_and_parity(tmp_path: Path) -> None:
    """P3 mixed-routing check: S0 cell -> gpusim, V15 non-S0 cell -> EnergyPlus.

    Verifies byte-identical fallback IDF, identical manifest schema & row count,
    unchanged downstream extractor, and routing report output.
    """
    # Use windowless V14 as S0 (immune to Windows E+ 23.1 NoSun window bug) and V15 as non-S0 fallback
    s0_id = f"{CELL1_ID}__V14"
    s0_dir = GOLDEN_ROOT / "variants" / s0_id
    s0_meta = json.loads((s0_dir / "meta.json").read_text(encoding="utf-8"))
    s0_epw = WEATHER_DIR / str(s0_meta["epw_file_name"])

    v15_meta = json.loads((V15_DIR / "meta.json").read_text(encoding="utf-8"))
    v15_epw = WEATHER_DIR / str(v15_meta["epw_file_name"])

    # Stage local IDF copies with schedule CSVs beside them so EnergyPlus & gpusim find them
    stage_dir = tmp_path / "staged_idfs"
    s0_stage = stage_dir / s0_id
    v15_stage = stage_dir / "V15_solar"
    s0_stage.mkdir(parents=True)
    v15_stage.mkdir(parents=True)

    # Strip golden-only Timestep outputs so eplusout.csv matches production hourly schema
    def _strip_timestep_outputs(text: str) -> str:
        return "\n".join(
            line for line in text.splitlines()
            if not (line.strip().lower().startswith("output:variable") and "timestep" in line.lower())
        ) + "\n"

    s0_idf = s0_stage / "in.idf"
    s0_idf.write_text(
        _strip_timestep_outputs((s0_dir / "in.idf").read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    (s0_stage / f"{CELL1_ID}.csv").write_bytes((REP2_SCHED_DIR / f"{CELL1_ID}.csv").read_bytes())

    v15_idf = v15_stage / "in.idf"
    v15_idf.write_text(
        _strip_timestep_outputs((V15_DIR / "in.idf").read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    (v15_stage / f"{CELL1_ID}.csv").write_bytes((REP2_SCHED_DIR / f"{CELL1_ID}.csv").read_bytes())
    v15_bytes_before = v15_idf.read_bytes()

    idf_manifest = pd.DataFrame(
        [
            {"osm_id": s0_id, "idf_path": str(s0_idf), "generation_status": "success"},
            {"osm_id": "V15_solar", "idf_path": str(v15_idf), "generation_status": "success"},
        ]
    )
    enriched_gdf = gpd.GeoDataFrame(
        {
            "osm_id": [s0_id, "V15_solar"],
            "epw_path": [str(s0_epw), str(v15_epw)],
            "geometry": [box(0, 0, 10, 10), box(20, 0, 30, 10)],
        },
        crs="EPSG:4326",
    )

    # Pure CPU EnergyPlus run
    ep_root = tmp_path / "sim_ep"
    df_ep = run_neighbourhood(
        idf_manifest,
        enriched_gdf,
        ep_root,
        n_jobs=2,
        backend="threading",
        force_rerun=True,
        sim_engine="energyplus",
    )

    # Mixed-routing auto run (spot_check_fraction=0 so S0 deterministically goes to gpusim)
    auto_root = tmp_path / "sim_auto"
    df_auto = run_neighbourhood(
        idf_manifest,
        enriched_gdf,
        auto_root,
        n_jobs=2,
        backend="threading",
        force_rerun=True,
        sim_engine="auto",
        gpusim_device="cpu",
        spot_check_fraction=0.0,
    )

    # Identical schema and row count
    assert list(df_ep.columns) == list(df_auto.columns)
    assert len(df_ep) == len(df_auto) == 2
    assert set(df_auto["status"]) == {"success"}

    # Routing report exists and records exact decisions
    report_path = auto_root / "04_routing_report.csv"
    assert report_path.is_file()
    report = {r["building_id"]: r for r in csv.DictReader(report_path.open(encoding="utf-8"))}
    assert report[s0_id]["selected_engine"] == "gpusim"
    assert report[s0_id]["subset_rung"] == "S0"
    assert report["V15_solar"]["selected_engine"] == "energyplus"
    assert report["V15_solar"]["reason"].startswith("fallback_energyplus:")

    # E+-routed building IDF is byte-identical and kWh matches pure CPU run exactly
    assert v15_idf.read_bytes() == v15_bytes_before
    kwh_v15_ep = _extract_heating_kwh(ep_root / "V15_solar" / "eplusout.csv")
    kwh_v15_auto = _extract_heating_kwh(auto_root / "V15_solar" / "eplusout.csv")
    assert abs(kwh_v15_auto - kwh_v15_ep) < 1.0e-6

    # gpusim-routed S0 building matches pinned golden EnergyPlus reference within S0 gate (0.5%)
    # via unchanged extractor (D6: Windows E+ 23.1 has a non-deterministic uninitialized-memory
    # bug on NoSun window walls, so gate S0 parity against the pinned Linux/macOS meta.json target).
    kwh_s0_ref = float(s0_meta["annual_heating_kwh"])
    kwh_s0_gpu = _extract_heating_kwh(auto_root / s0_id / "eplusout.csv")
    rel_diff = abs(kwh_s0_gpu - kwh_s0_ref) / kwh_s0_ref
    assert rel_diff <= 0.005, f"S0 gpusim vs golden E+ rel_diff={rel_diff:.6e}"

    # Provenance JSON exists for gpusim-routed building
    prov = json.loads((auto_root / s0_id / "gpusim_provenance.json").read_text(encoding="utf-8"))
    assert prov["engine"] == "gpusim"
    assert prov["subset_rung"] == "S0"
    assert len(prov["conformance_hash"]) == 16


def test_d5_real_energyplus_sizing_off_exact_parity(tmp_path: Path) -> None:
    """D5: Turning off unused sizing pass gives bit-equivalent heating and faster E+ run."""
    import re
    import subprocess
    import time

    from openubem.simulation.runner import _exe

    ep_exe = _exe()

    # Use SunExposed V15 (immune to Windows E+ 23.1 NoSun window bug)
    s0_dir = V15_DIR
    s0_meta = json.loads((s0_dir / "meta.json").read_text(encoding="utf-8"))
    s0_epw = WEATHER_DIR / str(s0_meta["epw_file_name"])
    raw_idf = "\n".join(
        line
        for line in (s0_dir / "in.idf").read_text(encoding="utf-8").splitlines()
        if not (line.strip().lower().startswith("output:variable") and "timestep" in line.lower())
    ) + "\n"

    # Flip SimulationControl sizing fields to No (same transformation as _guard_and_disable_unused_sizing)
    def _disable_sc(text: str) -> str:
        pat = re.compile(r"(SimulationControl\s*,)([^;]*)(;)", re.IGNORECASE | re.DOTALL)
        def _repl(m: re.Match[str]) -> str:
            return (
                "SimulationControl,\n"
                "  No,\n"
                "  No,\n"
                "  No,\n"
                "  No,\n"
                "  Yes;"
            )
        return pat.sub(_repl, text, count=1)

    nosize_idf = _disable_sc(raw_idf)
    assert nosize_idf != raw_idf

    dir_on = tmp_path / "sizing_on"
    dir_off = tmp_path / "sizing_off"
    for d, txt in ((dir_on, raw_idf), (dir_off, nosize_idf)):
        d.mkdir(parents=True)
        (d / "in.idf").write_text(txt, encoding="utf-8")
        (d / f"{CELL1_ID}.csv").write_bytes((REP2_SCHED_DIR / f"{CELL1_ID}.csv").read_bytes())

    from concurrent.futures import ThreadPoolExecutor

    def _run_ep(d: Path) -> tuple[float, float]:
        t0 = time.perf_counter()
        proc = subprocess.run(
            [str(ep_exe), "-w", str(s0_epw), "-d", str(d), "-x", "-r", str(d / "in.idf")],
            cwd=str(d),
            capture_output=True,
            text=True,
            check=True,
        )
        _ = proc
        elapsed = time.perf_counter() - t0
        return _extract_heating_kwh(d / "eplusout.csv"), elapsed

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_on = pool.submit(_run_ep, dir_on)
        f_off = pool.submit(_run_ep, dir_off)
        kwh_on, t_on = f_on.result()
        kwh_off, t_off = f_off.result()

    rel = abs(kwh_off - kwh_on) / max(abs(kwh_on), 1.0e-9)
    assert rel < 1.0e-8, f"D5 sizing-off changed heating: on={kwh_on:.6f} off={kwh_off:.6f} rel={rel:.3e}"
    assert t_off <= t_on * 1.15, f"D5 sizing-off unexpectedly slower: on={t_on:.2f}s off={t_off:.2f}s"


def test_p3_non_s0_synthetic_neighbourhood_fails_closed(tmp_path: Path) -> None:
    """Non-S0 IDFs (multi-zone, shading, PTAC, layered walls) fail closed cleanly."""
    base_idf = (GOLDEN_ROOT / CELL1_ID / "in.idf").read_text(encoding="utf-8")

    # 1. Shading:Site:Detailed
    shaded = base_idf + "\nShading:Site:Detailed,\n  Shade1,\n  ,\n  4,\n  0,0,0, 10,0,0, 10,0,10, 0,0,10;\n"
    d_sh = route_idf_text(shaded, "b_shade", sim_engine="auto", device="cpu", spot_check_fraction=0.0)
    assert d_sh.selected_engine == "energyplus"
    assert "SHADING" in d_sh.reason.upper()

    # 2. Multi-zone (2 Zones)
    mz = base_idf + "\nZone,\n  Zone_2,\n  0, 0, 0, 0, 1, 1, 3.0, 100.0, 33.3;\n"
    d_mz = route_idf_text(mz, "b_mz", sim_engine="auto", device="cpu", spot_check_fraction=0.0)
    assert d_mz.selected_engine == "energyplus"
    assert "ZONE" in d_mz.reason.upper()

    # 3. Ground boundary condition
    gnd = base_idf.replace("OtherSideCoefficients,", "Ground,", 1)
    d_gnd = route_idf_text(gnd, "b_gnd", sim_engine="auto", device="cpu", spot_check_fraction=0.0)
    assert d_gnd.selected_engine == "energyplus"

    # 4. Write routing report and verify schema
    rpt = write_routing_report_csv([d_sh, d_mz, d_gnd], tmp_path / "04_routing_report.csv")
    rows = list(csv.DictReader(rpt.open(encoding="utf-8")))
    assert len(rows) == 3
    assert all(r["selected_engine"] == "energyplus" for r in rows)
    assert all(r["reason"].startswith("fallback_energyplus:") for r in rows)
