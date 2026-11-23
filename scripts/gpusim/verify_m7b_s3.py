"""M7b Rung S3 verification: exterior shading (Shading:Site:Detailed street canyon & neighbour blocks).

Runs 3 shaded cases (+ unshaded baseline) in parallel on Windows EnergyPlus 23.1.0,
then verifies gpusim's ray-triangle exterior shading (shading.py + general_cuda.py)
against §4 S3 gates (annual heating |rel| <= 2.0%, hourly CV(RMSE) <= 6.0%).
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import pandas as pd

from openubem.gpusim.backends.general_cuda import run_general_cuda
from openubem.gpusim.general_model import compile_general_batch
from openubem.gpusim.weather import load_epw_weather
from openubem.simulation.runner import _exe

REPO_ROOT = Path(__file__).resolve().parents[2]
WEATHER_DIR = REPO_ROOT / "openubem/data/weather"
BOLOGNA_EPW = WEATHER_DIR / "it_bologna_2013_2014_y2014.epw"
MADRID_EPW = WEATHER_DIR / "es_madrid_2009_2010_y2009.epw"


def _build_shaded_box_idf(epw_path: Path, name: str, shading_blocks: str) -> str:
    loc = epw_path.read_text(encoding="utf-8", errors="replace").splitlines()[0].split(",")
    city, lat, lon, tz, elev = loc[1].strip(), float(loc[6]), float(loc[7]), float(loc[8]), float(loc[9])
    return f"""Version,23.1;
SimulationControl,No,No,No,No,Yes;
Building,{name},0,City,0.04,0.4,FullExterior,25,1;
ShadowCalculation,PolygonClipping,Periodic,20;
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

Material:NoMass,WALL_MAT,Rough,1.5,0.9,0.6,0.6;
Material:NoMass,ROOF_MAT,Rough,2.5,0.9,0.6,0.6;
Material:NoMass,FLOOR_MAT,Rough,10.0,0.9,0.6,0.6;
WindowMaterial:SimpleGlazingSystem,WIN_MAT,2.4,0.65;
Material,CONC_IM,MediumRough,0.10,1.0,1800.0,900.0,0.9,0.6,0.6;

Construction,WALL_CON,WALL_MAT;
Construction,ROOF_CON,ROOF_MAT;
Construction,FLOOR_CON,FLOOR_MAT;
Construction,WIN_CON,WIN_MAT;
Construction,IM_CON,CONC_IM;

SurfaceProperty:OtherSideCoefficients,OSC_GND,0,10.0,1.0,0,0,0,0,,No;

Zone,ZONE_ONE,0,0,0,0,1,1,3.0,180.0,60.0;
InternalMass,IM_1,IM_CON,ZONE_ONE,,60.0;

BuildingSurface:Detailed,WALL_SOUTH,Wall,WALL_CON,ZONE_ONE,,Outdoors,,SunExposed,WindExposed,0.5,4,
  0,0,3, 0,0,0, 10,0,0, 10,0,3;
BuildingSurface:Detailed,WALL_EAST,Wall,WALL_CON,ZONE_ONE,,Outdoors,,SunExposed,WindExposed,0.5,4,
  10,0,3, 10,0,0, 10,6,0, 10,6,3;
BuildingSurface:Detailed,WALL_NORTH,Wall,WALL_CON,ZONE_ONE,,Outdoors,,SunExposed,WindExposed,0.5,4,
  10,6,3, 10,6,0, 0,6,0, 0,6,3;
BuildingSurface:Detailed,WALL_WEST,Wall,WALL_CON,ZONE_ONE,,Outdoors,,SunExposed,WindExposed,0.5,4,
  0,6,3, 0,6,0, 0,0,0, 0,0,3;
BuildingSurface:Detailed,ROOF_1,Roof,ROOF_CON,ZONE_ONE,,Outdoors,,SunExposed,WindExposed,0.0,4,
  0,6,3, 0,0,3, 10,0,3, 10,6,3;
BuildingSurface:Detailed,FLOOR_1,Floor,FLOOR_CON,ZONE_ONE,,OtherSideCoefficients,OSC_GND,NoSun,NoWind,0.0,4,
  0,0,0, 0,6,0, 10,6,0, 10,0,0;

FenestrationSurface:Detailed,WIN_S1,Window,WIN_CON,WALL_SOUTH,,0.5,,1,4,
  1.0,0,2.5, 1.0,0,0.5, 9.0,0,0.5, 9.0,0,2.5;

{shading_blocks}

OtherEquipment,INT_GAIN,None,ZONE_ONE,AlwaysOn,EquipmentLevel,200.0,,,0.0,0.0,0.0;
ZoneVentilation:DesignFlowRate,VENT_1,ZONE_ONE,AlwaysOn,AirChanges/Hour,,,,0.5,Natural,0,1,1,0,0,0;

HVACTemplate:Thermostat,TSTAT_1,HeatSP,,CoolSP,;
HVACTemplate:Zone:IdealLoadsAirSystem,ZONE_ONE,TSTAT_1,AlwaysOn,50,13,0.0156,0.0077,NoLimit,,,NoLimit,,,AlwaysOn,AlwaysOff,ConstantSensibleHeatRatio,0.7,60,None,30,None,0,0,0,,None,NoEconomizer,None,0.70,0.65;

Output:Variable,*,Zone Ideal Loads Zone Total Heating Energy,TimeStep;
Output:Variable,*,Zone Mean Air Temperature,TimeStep;
"""


def _run_ep(name: str, idf_text: str, epw_path: Path, work_dir: Path) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    idf_path = work_dir / "in.idf"
    idf_path.write_text(idf_text, encoding="utf-8")
    proc = subprocess.run(
        [str(_exe()), "-w", str(epw_path), "-d", str(work_dir), "-x", "-r", str(idf_path)],
        cwd=str(work_dir),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err = (work_dir / "eplusout.err").read_text(errors="replace") if (work_dir / "eplusout.err").is_file() else ""
        raise RuntimeError(f"{name} E+ failed:\n{err[-1200:]}")
    df = pd.read_csv(work_dir / "eplusout.csv")
    hc = [c for c in df.columns if "Total Heating Energy" in c and "(TimeStep)" in c][0]
    tc = [c for c in df.columns if "Zone Mean Air Temperature" in c and "(TimeStep)" in c][0]
    return {
        "case": name,
        "expidf": work_dir / "eplusout.expidf",
        "epw": epw_path,
        "ep_ts_j": df[hc].to_numpy(dtype=np.float64),
        "ep_ts_t": df[tc].to_numpy(dtype=np.float64),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "openubem/outputs/gpusim_m7b_s3.csv")
    args = parser.parse_args()

    # 1. Unshaded baseline
    shade_none = ""
    # 2. Deep European street canyon: 12 m tall building 8 m across the street to the South (y = -8 m)
    shade_canyon = """
Shading:Site:Detailed,NEIGHBOUR_SOUTH_WALL, , 4,
  -5,-8,12, -5,-8,0, 15,-8,0, 15,-8,12;
"""
    # 3. Urban courtyard: South (10 m tall @ y=-6 m) + East (12 m tall @ x=16 m) + West (12 m tall @ x=-6 m)
    shade_courtyard = """
Shading:Site:Detailed,NB_SOUTH, , 4,
  -6,-6,10, -6,-6,0, 16,-6,0, 16,-6,10;
Shading:Site:Detailed,NB_EAST, , 4,
  16,-6,12, 16,-6,0, 16,12,0, 16,12,12;
Shading:Site:Detailed,NB_WEST, , 4,
  -6,12,12, -6,12,0, -6,-6,0, -6,-6,12;
"""
    # 4. South balcony / deep 1.5 m overhang
    shade_overhang = """
Shading:Site:Detailed,SOUTH_OVERHANG, , 4,
  0,-1.5,2.7, 0,0,2.7, 10,0,2.7, 10,-1.5,2.7;
"""

    cases = [
        ("Unshaded_Ref_Bologna", _build_shaded_box_idf(BOLOGNA_EPW, "UNSHADED", shade_none), BOLOGNA_EPW),
        ("Canyon_H12_W8_Bologna", _build_shaded_box_idf(BOLOGNA_EPW, "CANYON_BOL", shade_canyon), BOLOGNA_EPW),
        ("Courtyard_3Side_Bologna", _build_shaded_box_idf(BOLOGNA_EPW, "COURT_BOL", shade_courtyard), BOLOGNA_EPW),
        ("Overhang_1p5m_Madrid", _build_shaded_box_idf(MADRID_EPW, "OVERHANG_MAD", shade_overhang), MADRID_EPW),
    ]

    with tempfile.TemporaryDirectory(prefix="gpusim_m7b_s3_") as td:
        td_path = Path(td)
        with ThreadPoolExecutor(max_workers=len(cases)) as pool:
            ep_results = [
                f.result()
                for f in [pool.submit(_run_ep, n, t, e, td_path / n) for n, t, e in cases]
            ]

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

        gb = compile_general_batch(
            [r["expidf"] for r in ep_results],
            per_bldg_w,
            np.asarray(site_indices, dtype=np.int32),
            [r["case"] for r in ep_results],
            compute_shading=True,
            shading_device="cuda",
            max_workers=1,
        )
        res = run_general_cuda(gb, site_weathers, record_zone_temp=True, run_chunk_days=3)
        print(f"CUDA S3 shading batch (B={len(ep_results)}): gpu_s={res.gpu_s:.3f}s max_launch={res.max_launch_s:.4f}s rungs={res.rungs}")

        rows = []
        ep_unsh = float(ep_results[0]["ep_ts_j"].sum() / 3.6e6)
        gpu_unsh = float(res.annual_heating_kwh[0])
        for i, r in enumerate(ep_results):
            ep_h = r["ep_ts_j"].reshape(8760, 12).sum(axis=1)
            gpu_h = res.hourly_heating_j[i]
            ep_ann = float(ep_h.sum() / 3.6e6)
            gpu_ann = float(res.annual_heating_kwh[i])
            rel = (gpu_ann - ep_ann) / ep_ann
            cv = float(np.sqrt(np.mean((gpu_h - ep_h) ** 2)) / np.mean(ep_h))
            nmbe = float(np.sum(gpu_h - ep_h) / np.sum(ep_h))
            dt = np.abs(res.zone_mean_air_temp_c[i].astype(np.float64) - r["ep_ts_t"])
            dt_p999 = float(np.percentile(dt, 99.9))
            ep_d = (ep_ann - ep_unsh) / ep_unsh if i in (1, 2) else 0.0
            gpu_d = (gpu_ann - gpu_unsh) / gpu_unsh if i in (1, 2) else 0.0
            print(
                f"  {r['case']:25s}: ep={ep_ann:8.2f} gpu={gpu_ann:8.2f} kWh "
                f"rel={rel:+7.4%} CV={cv:6.4%} dT_p999={dt_p999:.3f}K "
                + (f"(shade delta: ep={ep_d:+.1%} gpu={gpu_d:+.1%})" if i in (1, 2) else "")
            )
            rows.append(
                {
                    "case": r["case"],
                    "epw": r["epw"].name,
                    "ep_kwh": round(ep_ann, 4),
                    "cuda_kwh": round(gpu_ann, 4),
                    "rel_cuda_vs_ep": round(rel, 6),
                    "cv_rmse": round(cv, 6),
                    "nmbe": round(nmbe, 6),
                    "dt_p999_k": round(dt_p999, 5),
                    "warmup_days": int(res.warmup_days[i]),
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
