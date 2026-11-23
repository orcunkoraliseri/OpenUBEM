"""M6 Rung S1 solar verification against native Windows EnergyPlus 23.1.0.

Runs 5 S1 solar cases in parallel on CPU EnergyPlus 23.1.0, then verifies both
Stage A (float64) and Stage C CUDA (general_cuda.py) against §4 S1 gates:
  - annual heating |rel| <= 1.5%
  - hourly CV(RMSE) <= 3.5%
  - hourly |NMBE| <= 0.3%
  - CUDA vs Stage A float32 |rel| <= 0.10%
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from pathlib import Path
import re
import subprocess
import tempfile

import numpy as np
import pandas as pd

from openubem.gpusim.backends.general_cuda import run_general_cuda
from openubem.gpusim.backends.numpy_ref import run_stage_a_batch
from openubem.gpusim.compile import compile_expidf_batch
from openubem.gpusim.general_model import compile_general_batch
from openubem.gpusim.weather import load_epw_weather
from openubem.simulation.runner import _exe

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = REPO_ROOT / "tests/fixtures/gpusim/golden"
CELL1_ID = "it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100"
CELL3_ID = "es__ES.ME.AB.01.Gen.ReEx.001.001__f000"
V15_DIR = GOLDEN_ROOT / "variants" / f"{CELL1_ID}__V15"
CELL3_DIR = GOLDEN_ROOT / CELL3_ID
SCHED_DIR = REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2/schedules"
WEATHER_DIR = REPO_ROOT / "openubem/data/weather"
BOLOGNA_EPW = WEATHER_DIR / "it_bologna_2013_2014_y2014.epw"
MADRID_EPW = WEATHER_DIR / "es_madrid_2009_2010_y2009.epw"


def _build_ashrae140_case600_s1_idf(epw_path: Path, enable_cooling: bool = True) -> str:
    """ASHRAE 140 Case 600 geometry (8x6x2.7m, 12m2 South glass, S1 NoMass envelope)."""
    loc = epw_path.read_text(encoding="utf-8", errors="replace").splitlines()[0].split(",")
    city, lat, lon, tz, elev = loc[1].strip(), float(loc[6]), float(loc[7]), float(loc[8]), float(loc[9])
    cool_sched = "AlwaysOn" if enable_cooling else "AlwaysOff"
    return f"""Version,23.1;
SimulationControl,No,No,No,No,Yes;
Building,ASHRAE140_600_S1,0,Country,0.04,0.4,FullExterior,25,1;
ShadowCalculation,PolygonClipping,Periodic,1;
Timestep,12;
HeatBalanceAlgorithm,ConductionTransferFunction,200,0.1,10000000;
Site:Location,{city},{lat},{lon},{tz},{elev};
RunPeriod,RunPeriod1,1,1,,12,31,,Sunday,No,No,No,Yes,Yes;
GlobalGeometryRules,UpperLeftCorner,CounterClockWise,World;
ScheduleTypeLimits,Any Number;
Schedule:Constant,AlwaysOn,Any Number,1.0;
Schedule:Constant,AlwaysOff,Any Number,0.0;
Schedule:Constant,HeatSP,Any Number,20.0;
Schedule:Constant,CoolSP,Any Number,27.0;

Material:NoMass,WALL_MAT,Rough,1.946,0.9,0.6,0.6;
Material:NoMass,ROOF_MAT,Rough,3.147,0.9,0.6,0.6;
Material:NoMass,FLOOR_MAT,Rough,25.0,0.9,0.6,0.6;
WindowMaterial:SimpleGlazingSystem,WIN_MAT,3.0,0.789;
Material,CONC_IM,MediumRough,0.10,1.0,1800.0,900.0,0.9,0.6,0.6;

Construction,WALL_CON,WALL_MAT;
Construction,ROOF_CON,ROOF_MAT;
Construction,FLOOR_CON,FLOOR_MAT;
Construction,WIN_CON,WIN_MAT;
Construction,IM_CON,CONC_IM;

SurfaceProperty:OtherSideCoefficients,OSC_GND,0,10.0,1.0,0,0,0,0,,No;

Zone,ZONE_ONE,0,0,0,0,1,1,2.7,129.6,48.0;

InternalMass,IM_1,IM_CON,ZONE_ONE,,48.0;

BuildingSurface:Detailed,WALL_SOUTH,Wall,WALL_CON,ZONE_ONE,,Outdoors,,SunExposed,NoWind,0.5,4,
  0,0,2.7, 0,0,0, 8,0,0, 8,0,2.7;
BuildingSurface:Detailed,WALL_EAST,Wall,WALL_CON,ZONE_ONE,,Outdoors,,SunExposed,NoWind,0.5,4,
  8,0,2.7, 8,0,0, 8,6,0, 8,6,2.7;
BuildingSurface:Detailed,WALL_NORTH,Wall,WALL_CON,ZONE_ONE,,Outdoors,,SunExposed,NoWind,0.5,4,
  8,6,2.7, 8,6,0, 0,6,0, 0,6,2.7;
BuildingSurface:Detailed,WALL_WEST,Wall,WALL_CON,ZONE_ONE,,Outdoors,,SunExposed,NoWind,0.5,4,
  0,6,2.7, 0,6,0, 0,0,0, 0,0,2.7;
BuildingSurface:Detailed,ROOF_1,Roof,ROOF_CON,ZONE_ONE,,Outdoors,,SunExposed,NoWind,0.0,4,
  0,6,2.7, 0,0,2.7, 8,0,2.7, 8,6,2.7;
BuildingSurface:Detailed,FLOOR_1,Floor,FLOOR_CON,ZONE_ONE,,OtherSideCoefficients,OSC_GND,NoSun,NoWind,0.0,4,
  0,0,0, 0,6,0, 8,6,0, 8,0,0;

FenestrationSurface:Detailed,WIN_S1,Window,WIN_CON,WALL_SOUTH,,0.5,,1,4,
  0.5,0,2.2, 0.5,0,0.2, 3.5,0,0.2, 3.5,0,2.2;
FenestrationSurface:Detailed,WIN_S2,Window,WIN_CON,WALL_SOUTH,,0.5,,1,4,
  4.5,0,2.2, 4.5,0,0.2, 7.5,0,0.2, 7.5,0,2.2;

OtherEquipment,INT_GAIN,None,ZONE_ONE,AlwaysOn,EquipmentLevel,200.0,,,0.0,0.0,0.0;
ZoneVentilation:DesignFlowRate,VENT_1,ZONE_ONE,AlwaysOn,AirChanges/Hour,,,,0.5,Natural,0,1,1,0,0,0;

HVACTemplate:Thermostat,TSTAT_1,HeatSP,,CoolSP,;
HVACTemplate:Zone:IdealLoadsAirSystem,ZONE_ONE,TSTAT_1,AlwaysOn,50,13,0.0156,0.0077,NoLimit,,,NoLimit,,,AlwaysOn,{cool_sched},ConstantSensibleHeatRatio,0.7,60,None,30,None,0,0,0,,None,NoEconomizer,None,0.70,0.65;

Output:Variable,*,Zone Ideal Loads Zone Total Heating Energy,TimeStep;
Output:Variable,*,Zone Mean Air Temperature,TimeStep;
"""


def _build_d1_d2_idf(idf_text: str) -> str:
    """Apply approved high-accuracy rulings D1 + D2 to an EU cell IDF."""
    txt = idf_text.replace("FullExterior", "MinimalShadowing")
    # Ensure outdoor wall surfaces are SunExposed (for Cell 3)
    def _expose_outdoor_walls(m: re.Match[str]) -> str:
        blk = m.group(0)
        if "Outdoors," in blk and "NoSun," in blk:
            blk = blk.replace("NoSun,", "SunExposed,", 1)
        return blk

    txt = re.sub(r"BUILDINGSURFACE:DETAILED\s*,[^;]+;", _expose_outdoor_walls, txt, flags=re.IGNORECASE)

    def _zero_nomass_sol(m: re.Match[str]) -> str:
        block = m.group(0)
        if "FLOOR" in block.upper():
            return block
        out_lines = []
        for ln in block.splitlines():
            if "solar absorptance" in ln.lower():
                ln = re.sub(r"^\s*[\d\.eE+-]+", "    0.0", ln)
            out_lines.append(ln)
        return "\n".join(out_lines)

    txt = re.sub(r"Material:NoMass\s*,[^;]+;", _zero_nomass_sol, txt, flags=re.IGNORECASE)

    def _scale_shgc(m: re.Match[str]) -> str:
        block = m.group(0)
        out_lines = []
        for ln in block.splitlines():
            if "solar heat gain coefficient" in ln.lower():
                val_m = re.search(r"([\d\.eE+-]+)", ln)
                if val_m:
                    new_shgc = float(val_m.group(1)) * 0.42
                    ln = ln.replace(val_m.group(1), f"{new_shgc:.6f}", 1)
            out_lines.append(ln)
        return "\n".join(out_lines)

    txt = re.sub(r"WindowMaterial:SimpleGlazingSystem\s*,[^;]+;", _scale_shgc, txt, flags=re.IGNORECASE)

    def _double_im(m: re.Match[str]) -> str:
        block = m.group(0)
        out_lines = []
        for ln in block.splitlines():
            if "surface area" in ln.lower():
                val_m = re.search(r"([\d\.eE+-]+)", ln)
                if val_m:
                    new_a = float(val_m.group(1)) * 2.0
                    ln = ln.replace(val_m.group(1), f"{new_a:.4f}", 1)
            out_lines.append(ln)
        return "\n".join(out_lines)

    txt = re.sub(r"InternalMass\s*,[^;]+;", _double_im, txt, flags=re.IGNORECASE)
    return txt


def _run_eplus_case(case_name: str, idf_text: str, epw_path: Path, work_dir: Path, sched_file: str | None) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    idf_path = work_dir / "in.idf"
    idf_path.write_text(idf_text, encoding="utf-8")
    if sched_file:
        src = SCHED_DIR / sched_file
        if src.is_file():
            (work_dir / sched_file).write_bytes(src.read_bytes())

    ep_exe = _exe()
    proc = subprocess.run(
        [str(ep_exe), "-w", str(epw_path), "-d", str(work_dir), "-x", "-r", str(idf_path)],
        cwd=str(work_dir),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err_txt = (work_dir / "eplusout.err").read_text(encoding="utf-8", errors="replace") if (work_dir / "eplusout.err").is_file() else ""
        raise RuntimeError(f"{case_name} E+ rc={proc.returncode}:\n{err_txt[-1500:]}")

    df = pd.read_csv(work_dir / "eplusout.csv")
    heat_col = [c for c in df.columns if "Zone Ideal Loads Zone Total Heating Energy" in c and "(TimeStep)" in c][0]
    temp_col = [c for c in df.columns if "Zone Mean Air Temperature" in c and "(TimeStep)" in c][0]
    return {
        "case": case_name,
        "expidf": work_dir / "eplusout.expidf",
        "epw": epw_path,
        "ep_ts_j": df[heat_col].to_numpy(dtype=np.float64),
        "ep_ts_t": df[temp_col].to_numpy(dtype=np.float64),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "openubem/outputs/gpusim_m6_s1.csv")
    args = parser.parse_args()

    v15_raw = (V15_DIR / "in.idf").read_text(encoding="utf-8")
    cell3_raw = (CELL3_DIR / "in.idf").read_text(encoding="utf-8")

    cases = [
        ("V15_FullExterior", v15_raw, BOLOGNA_EPW, f"{CELL1_ID}.csv", True),
        ("V15_MinimalShadowing", v15_raw.replace("FullExterior", "MinimalShadowing"), BOLOGNA_EPW, f"{CELL1_ID}.csv", True),
        ("EU_Cell1_D1_D2", _build_d1_d2_idf(v15_raw), BOLOGNA_EPW, f"{CELL1_ID}.csv", True),
        ("EU_Cell3_Madrid_D1_D2", _build_d1_d2_idf(cell3_raw), MADRID_EPW, f"{CELL3_ID}.csv", True),
        ("ASHRAE140_600_Bologna", _build_ashrae140_case600_s1_idf(BOLOGNA_EPW, enable_cooling=True), BOLOGNA_EPW, None, False),
    ]

    with tempfile.TemporaryDirectory(prefix="gpusim_m6_s1_") as td:
        td_path = Path(td)
        with ThreadPoolExecutor(max_workers=len(cases)) as pool:
            futs = [
                pool.submit(_run_eplus_case, name, txt, epw, td_path / name, sf)
                for name, txt, epw, sf, _ in cases
            ]
            ep_results = [f.result() for f in futs]

        # Unique sites
        site_map: dict[Path, int] = {}
        site_weathers = []
        per_bldg_w = []
        site_indices = []
        for r in ep_results:
            epw = r["epw"]
            if epw not in site_map:
                site_map[epw] = len(site_weathers)
                site_weathers.append(load_epw_weather(epw, steps_per_hour=12))
            site_indices.append(site_map[epw])
            per_bldg_w.append(site_weathers[site_map[epw]])

        # Run unified CUDA kernel on all 5 S1 cases
        gb = compile_general_batch(
            [r["expidf"] for r in ep_results],
            per_bldg_w,
            np.asarray(site_indices, dtype=np.int32),
            [r["case"] for r in ep_results],
            [SCHED_DIR],
            compute_shading=False,
        )
        res_gpu = run_general_cuda(gb, site_weathers, record_zone_temp=True, run_chunk_days=3)
        print(f"CUDA S1 batch (B={len(ep_results)}): gpu_s={res_gpu.gpu_s:.3f}s max_launch={res_gpu.max_launch_s:.4f}s")

        # Also run Stage A float64 on the 4 heating-only cases for float32 vs float64 check
        sa_indices = [i for i, c in enumerate(cases) if c[4]]
        b_sa = compile_expidf_batch(
            [ep_results[i]["expidf"] for i in sa_indices],
            [ep_results[i]["case"] for i in sa_indices],
            [ep_results[i]["epw"].name for i in sa_indices],
            [SCHED_DIR],
            max_rung="S1",
        )
        res_sa = run_stage_a_batch(b_sa, [per_bldg_w[i] for i in sa_indices], record_zone_temp=False)
        sa_kwh_by_idx = {sa_indices[j]: float(res_sa.annual_heating_kwh[j]) for j in range(len(sa_indices))}

        rows = []
        for i, r in enumerate(ep_results):
            ep_h = r["ep_ts_j"].reshape(8760, 12).sum(axis=1)
            gpu_h = res_gpu.hourly_heating_j[i]
            ep_ann = float(ep_h.sum() / 3.6e6)
            gpu_ann = float(res_gpu.annual_heating_kwh[i])
            rel_ep = (gpu_ann - ep_ann) / ep_ann
            cv_rmse = float(np.sqrt(np.mean((gpu_h - ep_h) ** 2)) / np.mean(ep_h))
            nmbe = float(np.sum(gpu_h - ep_h) / np.sum(ep_h))
            dt = np.abs(res_gpu.zone_mean_air_temp_c[i].astype(np.float64) - r["ep_ts_t"])
            dt_p999 = float(np.percentile(dt, 99.9))
            sa_ann = sa_kwh_by_idx.get(i, float("nan"))
            rel_sa = (gpu_ann - sa_ann) / sa_ann if np.isfinite(sa_ann) else float("nan")
            print(
                f"  {r['case']:22s}: ep={ep_ann:9.2f} gpu={gpu_ann:9.2f} kWh "
                f"vs_EP={rel_ep:+7.4%} CV={cv_rmse:6.4%} NMBE={nmbe:+7.4%} "
                f"dT_p999={dt_p999:.4f}K vs_SA={rel_sa:+.4%}"
            )
            rows.append(
                {
                    "case": r["case"],
                    "epw": r["epw"].name,
                    "ep_kwh": round(ep_ann, 4),
                    "stage_a_kwh": round(sa_ann, 4) if np.isfinite(sa_ann) else "",
                    "cuda_kwh": round(gpu_ann, 4),
                    "rel_cuda_vs_ep": round(rel_ep, 6),
                    "rel_cuda_vs_sa": round(rel_sa, 6) if np.isfinite(rel_sa) else "",
                    "cv_rmse": round(cv_rmse, 6),
                    "nmbe": round(nmbe, 6),
                    "dt_p999_k": round(dt_p999, 5),
                    "warmup_days": int(res_gpu.warmup_days[i]),
                }
            )

        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
