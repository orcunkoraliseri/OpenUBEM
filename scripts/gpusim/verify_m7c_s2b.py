"""M7c Rung S2b verification: multi-zone buildings (interzone Surface coupling, Adiabatic party walls, unconditioned core).

Runs 3 multi-zone buildings in parallel on Windows EnergyPlus 23.1.0:
  1. 2-zone stacked duplex (interzone floor/ceiling Surface coupling + Ground + Roof + Windows)
  2. 4-zone European apartment block (2 dwellings + unconditioned central staircase core + adiabatic party wall + neighbour shading!)
  3. 3-zone layered-wall office/residential with mixed setpoints (21 C vs 18 C + unconditioned corridor)
Verifies general_cuda.py against EnergyPlus 23.1.0 per-building & per-zone heating.
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


def _build_eu_3zone_apartment_idf(epw_path: Path, name: str, with_uncond_core: bool = True) -> str:
    """2-storey European block: South flat (20C), North flat (19C), optional unconditioned core, party wall, neighbour shade."""
    loc = epw_path.read_text(encoding="utf-8", errors="replace").splitlines()[0].split(",")
    city, lat, lon, tz, elev = loc[1].strip(), float(loc[6]), float(loc[7]), float(loc[8]), float(loc[9])
    core_hvac = "" if with_uncond_core else """
HVACTemplate:Thermostat,TSTAT_CORE,HeatSP_N,,CoolSP,;
HVACTemplate:Zone:IdealLoadsAirSystem,CORE_ZONE,TSTAT_CORE,AlwaysOn,50,13,0.0156,0.0077,NoLimit,,,NoLimit,,,AlwaysOn,AlwaysOff,ConstantSensibleHeatRatio,0.7,60,None,30,None,0,0,0,,None,NoEconomizer,None,0.70,0.65;
"""
    return f"""Version,23.1;
SimulationControl,No,No,No,No,Yes;
Building,{name},0,City,0.04,0.4,FullExterior,25,1;
ShadowCalculation,PolygonClipping,Periodic,20;
Timestep,12;
HeatBalanceAlgorithm,ConductionTransferFunction,200,0.1,10000000;
Site:Location,{city},{lat},{lon},{tz},{elev};
Site:GroundTemperature:BuildingSurface,13,13,14,15,17,19,20,20,19,17,15,14;
RunPeriod,RunPeriod1,1,1,,12,31,,Sunday,No,No,No,Yes,Yes;
GlobalGeometryRules,UpperLeftCorner,CounterClockWise,World;
ScheduleTypeLimits,Any Number;
Schedule:Constant,AlwaysOn,Any Number,1.0;
Schedule:Constant,AlwaysOff,Any Number,0.0;
Schedule:Constant,HeatSP_S,Any Number,20.0;
Schedule:Constant,HeatSP_N,Any Number,19.0;
Schedule:Constant,CoolSP,Any Number,50.0;

Material:NoMass,EXT_WALL_MAT,Rough,1.2,0.9,0.6,0.6;
Material:NoMass,ROOF_MAT,Rough,2.2,0.9,0.6,0.6;
Material:NoMass,FLOOR_MAT,Rough,1.8,0.9,0.6,0.6;
Material,INT_WALL_MAT,MediumRough,0.12,0.8,1600.0,900.0,0.9,0.6,0.6;
Material,CONC_IM,MediumRough,0.10,1.0,1800.0,900.0,0.9,0.6,0.6;
WindowMaterial:SimpleGlazingSystem,WIN_MAT,2.6,0.55;

Construction,EXT_WALL,EXT_WALL_MAT;
Construction,ROOF_CON,ROOF_MAT;
Construction,FLOOR_CON,FLOOR_MAT;
Construction,INT_WALL,INT_WALL_MAT;
Construction,IM_CON,CONC_IM;
Construction,WIN_CON,WIN_MAT;

! 3 side-by-side zones along Y: FLAT_SOUTH (y=0..5), CORE_ZONE (y=5..7), FLAT_NORTH (y=7..12), x=0..10, z=0..3
! West wall (x=0) is Adiabatic party wall to adjacent townhouse!
Zone,FLAT_SOUTH,0,0,0,0,1,1,3.0,150.0,50.0;
Zone,CORE_ZONE,0,0,0,0,1,1,3.0,60.0,20.0;
Zone,FLAT_NORTH,0,0,0,0,1,1,3.0,150.0,50.0;

InternalMass,IM_S,IM_CON,FLAT_SOUTH,,50.0;
InternalMass,IM_N,IM_CON,FLAT_NORTH,,50.0;

! FLAT_SOUTH surfaces
BuildingSurface:Detailed,FS_SOUTH,Wall,EXT_WALL,FLAT_SOUTH,,Outdoors,,SunExposed,WindExposed,0.5,4, 0,0,3, 0,0,0, 10,0,0, 10,0,3;
BuildingSurface:Detailed,FS_EAST,Wall,EXT_WALL,FLAT_SOUTH,,Outdoors,,SunExposed,WindExposed,0.5,4, 10,0,3, 10,0,0, 10,5,0, 10,5,3;
BuildingSurface:Detailed,FS_WEST,Wall,EXT_WALL,FLAT_SOUTH,,Adiabatic,,NoSun,NoWind,0.5,4, 0,5,3, 0,5,0, 0,0,0, 0,0,3;
BuildingSurface:Detailed,FS_PART,Wall,INT_WALL,FLAT_SOUTH,,Surface,CZ_SOUTH,NoSun,NoWind,0.0,4, 10,5,3, 10,5,0, 0,5,0, 0,5,3;
BuildingSurface:Detailed,FS_ROOF,Roof,ROOF_CON,FLAT_SOUTH,,Outdoors,,SunExposed,WindExposed,0.0,4, 0,5,3, 0,0,3, 10,0,3, 10,5,3;
BuildingSurface:Detailed,FS_FLOOR,Floor,FLOOR_CON,FLAT_SOUTH,,Ground,,NoSun,NoWind,0.0,4, 0,0,0, 0,5,0, 10,5,0, 10,0,0;
FenestrationSurface:Detailed,WIN_FS,Window,WIN_CON,FS_SOUTH,,0.5,,1,4, 1,0,2.4, 1,0,0.6, 8,0,0.6, 8,0,2.4;

! CORE_ZONE surfaces
BuildingSurface:Detailed,CZ_SOUTH,Wall,INT_WALL,CORE_ZONE,,Surface,FS_PART,NoSun,NoWind,0.0,4, 0,5,3, 0,5,0, 10,5,0, 10,5,3;
BuildingSurface:Detailed,CZ_NORTH,Wall,INT_WALL,CORE_ZONE,,Surface,FN_PART,NoSun,NoWind,0.0,4, 10,7,3, 10,7,0, 0,7,0, 0,7,3;
BuildingSurface:Detailed,CZ_EAST,Wall,EXT_WALL,CORE_ZONE,,Outdoors,,SunExposed,WindExposed,0.5,4, 10,5,3, 10,5,0, 10,7,0, 10,7,3;
BuildingSurface:Detailed,CZ_WEST,Wall,EXT_WALL,CORE_ZONE,,Adiabatic,,NoSun,NoWind,0.5,4, 0,7,3, 0,7,0, 0,5,0, 0,5,3;
BuildingSurface:Detailed,CZ_ROOF,Roof,ROOF_CON,CORE_ZONE,,Outdoors,,SunExposed,WindExposed,0.0,4, 0,7,3, 0,5,3, 10,5,3, 10,7,3;
BuildingSurface:Detailed,CZ_FLOOR,Floor,FLOOR_CON,CORE_ZONE,,Ground,,NoSun,NoWind,0.0,4, 0,5,0, 0,7,0, 10,7,0, 10,5,0;

! FLAT_NORTH surfaces
BuildingSurface:Detailed,FN_PART,Wall,INT_WALL,FLAT_NORTH,,Surface,CZ_NORTH,NoSun,NoWind,0.0,4, 0,7,3, 0,7,0, 10,7,0, 10,7,3;
BuildingSurface:Detailed,FN_EAST,Wall,EXT_WALL,FLAT_NORTH,,Outdoors,,SunExposed,WindExposed,0.5,4, 10,7,3, 10,7,0, 10,12,0, 10,12,3;
BuildingSurface:Detailed,FN_NORTH,Wall,EXT_WALL,FLAT_NORTH,,Outdoors,,SunExposed,WindExposed,0.5,4, 10,12,3, 10,12,0, 0,12,0, 0,12,3;
BuildingSurface:Detailed,FN_WEST,Wall,EXT_WALL,FLAT_NORTH,,Adiabatic,,NoSun,NoWind,0.5,4, 0,12,3, 0,12,0, 0,7,0, 0,7,3;
BuildingSurface:Detailed,FN_ROOF,Roof,ROOF_CON,FLAT_NORTH,,Outdoors,,SunExposed,WindExposed,0.0,4, 0,12,3, 0,7,3, 10,7,3, 10,12,3;
BuildingSurface:Detailed,FN_FLOOR,Floor,FLOOR_CON,FLAT_NORTH,,Ground,,NoSun,NoWind,0.0,4, 0,7,0, 0,12,0, 10,12,0, 10,7,0;
FenestrationSurface:Detailed,WIN_FN,Window,WIN_CON,FN_NORTH,,0.5,,1,4, 8,12,2.4, 8,12,0.6, 2,12,0.6, 2,12,2.4;

! Neighbour building shading across South street
Shading:Site:Detailed,NEIGHBOUR_S, , 4, -4,-10,10, -4,-10,0, 14,-10,0, 14,-10,10;

OtherEquipment,GAIN_S,None,FLAT_SOUTH,AlwaysOn,Watts/Area,,3.5,,0,0,0;
OtherEquipment,GAIN_N,None,FLAT_NORTH,AlwaysOn,Watts/Area,,3.5,,0,0,0;
ZoneVentilation:DesignFlowRate,VENT_S,FLAT_SOUTH,AlwaysOn,AirChanges/Hour,,,,0.5,Natural,0,1,1,0,0,0;
ZoneVentilation:DesignFlowRate,VENT_N,FLAT_NORTH,AlwaysOn,AirChanges/Hour,,,,0.5,Natural,0,1,1,0,0,0;
ZoneInfiltration:DesignFlowRate,INF_CORE,CORE_ZONE,AlwaysOn,Flow/Area,,0.0005,,,1,0,0,0;

HVACTemplate:Thermostat,TSTAT_S,HeatSP_S,,CoolSP,;
HVACTemplate:Thermostat,TSTAT_N,HeatSP_N,,CoolSP,;
HVACTemplate:Zone:IdealLoadsAirSystem,FLAT_SOUTH,TSTAT_S,AlwaysOn,50,13,0.0156,0.0077,NoLimit,,,NoLimit,,,AlwaysOn,AlwaysOff,ConstantSensibleHeatRatio,0.7,60,None,30,None,0,0,0,,None,NoEconomizer,None,0.70,0.65;
HVACTemplate:Zone:IdealLoadsAirSystem,FLAT_NORTH,TSTAT_N,AlwaysOn,50,13,0.0156,0.0077,NoLimit,,,NoLimit,,,AlwaysOn,AlwaysOff,ConstantSensibleHeatRatio,0.7,60,None,30,None,0,0,0,,None,NoEconomizer,None,0.70,0.65;
{core_hvac}
Output:Variable,*,Zone Ideal Loads Zone Total Heating Energy,TimeStep;
Output:Variable,*,Zone Mean Air Temperature,TimeStep;
"""


def _build_2storey_duplex_idf(epw_path: Path, name: str) -> str:
    """2-storey stacked duplex with interfloor Surface coupling (GROUND_FLR <-> UPPER_FLR)."""
    loc = epw_path.read_text(encoding="utf-8", errors="replace").splitlines()[0].split(",")
    city, lat, lon, tz, elev = loc[1].strip(), float(loc[6]), float(loc[7]), float(loc[8]), float(loc[9])
    return f"""Version,23.1;
SimulationControl,No,No,No,No,Yes;
Building,{name},0,City,0.04,0.4,FullExterior,25,1;
ShadowCalculation,PolygonClipping,Periodic,20;
Timestep,12;
HeatBalanceAlgorithm,ConductionTransferFunction,200,0.1,10000000;
Site:Location,{city},{lat},{lon},{tz},{elev};
Site:GroundTemperature:BuildingSurface,13,13,14,15,17,19,20,20,19,17,15,14;
RunPeriod,RunPeriod1,1,1,,12,31,,Sunday,No,No,No,Yes,Yes;
GlobalGeometryRules,UpperLeftCorner,CounterClockWise,World;
ScheduleTypeLimits,Any Number;
Schedule:Constant,AlwaysOn,Any Number,1.0;
Schedule:Constant,AlwaysOff,Any Number,0.0;
Schedule:Constant,HeatSP_1,Any Number,21.0;
Schedule:Constant,HeatSP_2,Any Number,18.0;
Schedule:Constant,CoolSP,Any Number,50.0;

Material:NoMass,EXT_WALL_MAT,Rough,1.5,0.9,0.6,0.6;
Material:NoMass,ROOF_MAT,Rough,2.8,0.9,0.6,0.6;
Material:NoMass,FLOOR_MAT,Rough,2.0,0.9,0.6,0.6;
Material,SLAB_INTER,MediumRough,0.18,1.4,2200.0,1000.0,0.9,0.6,0.6;
WindowMaterial:SimpleGlazingSystem,WIN_MAT,2.2,0.58;

Construction,EXT_WALL,EXT_WALL_MAT;
Construction,ROOF_CON,ROOF_MAT;
Construction,FLOOR_CON,FLOOR_MAT;
Construction,INTER_SLAB,SLAB_INTER;
Construction,WIN_CON,WIN_MAT;

Zone,GROUND_FLR,0,0,0,0,1,1,3.0,180.0,60.0;
Zone,UPPER_FLR,0,0,0,0,1,1,3.0,180.0,60.0;

! GROUND_FLR (z=0..3)
BuildingSurface:Detailed,GF_S,Wall,EXT_WALL,GROUND_FLR,,Outdoors,,SunExposed,WindExposed,0.5,4, 0,0,3, 0,0,0, 10,0,0, 10,0,3;
BuildingSurface:Detailed,GF_E,Wall,EXT_WALL,GROUND_FLR,,Outdoors,,SunExposed,WindExposed,0.5,4, 10,0,3, 10,0,0, 10,6,0, 10,6,3;
BuildingSurface:Detailed,GF_N,Wall,EXT_WALL,GROUND_FLR,,Outdoors,,SunExposed,WindExposed,0.5,4, 10,6,3, 10,6,0, 0,6,0, 0,6,3;
BuildingSurface:Detailed,GF_W,Wall,EXT_WALL,GROUND_FLR,,Outdoors,,SunExposed,WindExposed,0.5,4, 0,6,3, 0,6,0, 0,0,0, 0,0,3;
BuildingSurface:Detailed,GF_FLR,Floor,FLOOR_CON,GROUND_FLR,,Ground,,NoSun,NoWind,0.0,4, 0,0,0, 0,6,0, 10,6,0, 10,0,0;
BuildingSurface:Detailed,GF_CEIL,Ceiling,INTER_SLAB,GROUND_FLR,,Surface,UF_FLR,NoSun,NoWind,0.0,4, 0,6,3, 0,0,3, 10,0,3, 10,6,3;
FenestrationSurface:Detailed,WIN_GF,Window,WIN_CON,GF_S,,0.5,,1,4, 1,0,2.4, 1,0,0.6, 7,0,0.6, 7,0,2.4;

! UPPER_FLR (z=3..6)
BuildingSurface:Detailed,UF_S,Wall,EXT_WALL,UPPER_FLR,,Outdoors,,SunExposed,WindExposed,0.5,4, 0,0,6, 0,0,3, 10,0,3, 10,0,6;
BuildingSurface:Detailed,UF_E,Wall,EXT_WALL,UPPER_FLR,,Outdoors,,SunExposed,WindExposed,0.5,4, 10,0,6, 10,0,3, 10,6,3, 10,6,6;
BuildingSurface:Detailed,UF_N,Wall,EXT_WALL,UPPER_FLR,,Outdoors,,SunExposed,WindExposed,0.5,4, 10,6,6, 10,6,3, 0,6,3, 0,6,6;
BuildingSurface:Detailed,UF_W,Wall,EXT_WALL,UPPER_FLR,,Outdoors,,SunExposed,WindExposed,0.5,4, 0,6,6, 0,6,3, 0,0,3, 0,0,6;
BuildingSurface:Detailed,UF_FLR,Floor,INTER_SLAB,UPPER_FLR,,Surface,GF_CEIL,NoSun,NoWind,0.0,4, 0,0,3, 0,6,3, 10,6,3, 10,0,3;
BuildingSurface:Detailed,UF_ROOF,Roof,ROOF_CON,UPPER_FLR,,Outdoors,,SunExposed,WindExposed,0.0,4, 0,6,6, 0,0,6, 10,0,6, 10,6,6;
FenestrationSurface:Detailed,WIN_UF,Window,WIN_CON,UF_S,,0.5,,1,4, 1,0,5.4, 1,0,3.6, 7,0,3.6, 7,0,5.4;

OtherEquipment,GAIN_GF,None,GROUND_FLR,AlwaysOn,Watts/Area,,4.0,,0,0,0;
OtherEquipment,GAIN_UF,None,UPPER_FLR,AlwaysOn,Watts/Area,,3.0,,0,0,0;
ZoneVentilation:DesignFlowRate,VENT_GF,GROUND_FLR,AlwaysOn,AirChanges/Hour,,,,0.5,Natural,0,1,1,0,0,0;
ZoneVentilation:DesignFlowRate,VENT_UF,UPPER_FLR,AlwaysOn,AirChanges/Hour,,,,0.5,Natural,0,1,1,0,0,0;

HVACTemplate:Thermostat,TSTAT_1,HeatSP_1,,CoolSP,;
HVACTemplate:Thermostat,TSTAT_2,HeatSP_2,,CoolSP,;
HVACTemplate:Zone:IdealLoadsAirSystem,GROUND_FLR,TSTAT_1,AlwaysOn,50,13,0.0156,0.0077,NoLimit,,,NoLimit,,,AlwaysOn,AlwaysOff,ConstantSensibleHeatRatio,0.7,60,None,30,None,0,0,0,,None,NoEconomizer,None,0.70,0.65;
HVACTemplate:Zone:IdealLoadsAirSystem,UPPER_FLR,TSTAT_2,AlwaysOn,50,13,0.0156,0.0077,NoLimit,,,NoLimit,,,AlwaysOn,AlwaysOff,ConstantSensibleHeatRatio,0.7,60,None,30,None,0,0,0,,None,NoEconomizer,None,0.70,0.65;

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
    hcols = [c for c in df.columns if "Total Heating Energy" in c and "(TimeStep)" in c]
    ep_ts_j = sum(df[c].to_numpy(dtype=np.float64) for c in hcols)
    zone_kwh = {c.split(" IDEAL")[0].strip().upper(): float(df[c].sum() / 3.6e6) for c in hcols}
    return {
        "case": name,
        "expidf": work_dir / "eplusout.expidf",
        "epw": epw_path,
        "ep_ts_j": ep_ts_j,
        "zone_kwh": zone_kwh,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "openubem/outputs/gpusim_m7c_s2b.csv")
    args = parser.parse_args()

    cases = [
        ("EU_3Zone_UncondCore_Bol", _build_eu_3zone_apartment_idf(BOLOGNA_EPW, "EU3Z_UC_BOL", True), BOLOGNA_EPW),
        ("EU_3Zone_AllCond_Bol", _build_eu_3zone_apartment_idf(BOLOGNA_EPW, "EU3Z_AC_BOL", False), BOLOGNA_EPW),
        ("EU_3Zone_UncondCore_Mad", _build_eu_3zone_apartment_idf(MADRID_EPW, "EU3Z_UC_MAD", True), MADRID_EPW),
        ("Duplex_2Storey_Slab_Bol", _build_2storey_duplex_idf(BOLOGNA_EPW, "DUPLEX_BOL"), BOLOGNA_EPW),
    ]

    with tempfile.TemporaryDirectory(prefix="gpusim_m7c_s2b_") as td:
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
        res = run_general_cuda(gb, site_weathers, record_zone_temp=False, run_chunk_days=3)
        print(f"CUDA S2b multi-zone batch (B={len(ep_results)}, Z={gb.n_zones_total}, S={gb.n_surfs_total}): gpu_s={res.gpu_s:.3f}s max_launch={res.max_launch_s:.4f}s rungs={res.rungs}")

        rows = []
        for i, r in enumerate(ep_results):
            ep_h = r["ep_ts_j"].reshape(8760, 12).sum(axis=1)
            gpu_h = res.hourly_heating_j[i]
            ep_ann = float(ep_h.sum() / 3.6e6)
            gpu_ann = float(res.annual_heating_kwh[i])
            rel = (gpu_ann - ep_ann) / ep_ann
            cv = float(np.sqrt(np.mean((gpu_h - ep_h) ** 2)) / np.mean(ep_h))
            nmbe = float(np.sum(gpu_h - ep_h) / np.sum(ep_h))
            z0, z1 = int(gb.zone_offset[i]), int(gb.zone_offset[i + 1])
            z_detail = ", ".join(
                f"{res.zone_names[z].split('::')[1]}={res.zone_annual_kwh[z]:.0f}(ep={r['zone_kwh'].get(res.zone_names[z].split('::')[1], 0.0):.0f})"
                for z in range(z0, z1)
            )
            print(
                f"  {r['case']:25s}: ep={ep_ann:8.2f} gpu={gpu_ann:8.2f} kWh "
                f"rel={rel:+7.4%} CV={cv:6.4%} | {z_detail}"
            )
            rows.append(
                {
                    "case": r["case"],
                    "epw": r["epw"].name,
                    "n_zones": z1 - z0,
                    "ep_kwh": round(ep_ann, 4),
                    "cuda_kwh": round(gpu_ann, 4),
                    "rel_cuda_vs_ep": round(rel, 6),
                    "cv_rmse": round(cv, 6),
                    "nmbe": round(nmbe, 6),
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
