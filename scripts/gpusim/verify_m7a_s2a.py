"""M7a Rung S2a verification: layered mass walls, thick XPS+concrete, ground BC, wind, schedules, internal gains.

Runs 5 S2a cases in parallel on native Windows EnergyPlus 23.1.0, then verifies
the unified CUDA modal-conduction kernel (general_cuda.py) against §4 S2a gates:
  - annual heating |rel| <= 1.5%
  - hourly CV(RMSE) <= 4.0%
  - thick wall (10 cm XPS + 25 cm concrete) shows ZERO float32 cancellation blow-up!
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


def _build_s2a_box_idf(
    epw_path: Path,
    *,
    name: str,
    wall_materials: str,
    wall_layers: str,
    roof_layers: str,
    floor_layers: str,
    floor_bc: str = "Ground",
    wind_exp: str = "WindExposed",
    use_compact_sched: bool = True,
    add_people_lights: bool = False,
) -> str:
    loc = epw_path.read_text(encoding="utf-8", errors="replace").splitlines()[0].split(",")
    city, lat, lon, tz, elev = loc[1].strip(), float(loc[6]), float(loc[7]), float(loc[8]), float(loc[9])
    heat_sp_block = (
        """Schedule:Compact,HeatSP,Any Number,
  Through: 12/31,
  For: Weekdays,
  Until: 07:00, 17.0,
  Until: 22:00, 21.0,
  Until: 24:00, 17.0,
  For: AllOtherDays,
  Until: 08:00, 18.0,
  Until: 23:00, 21.0,
  Until: 24:00, 18.0;"""
        if use_compact_sched
        else "Schedule:Constant,HeatSP,Any Number,20.0;"
    )
    gains_block = (
        """Schedule:Compact,OccSched,Any Number,
  Through: 12/31,
  For: AllDays,
  Until: 08:00, 0.8,
  Until: 18:00, 0.2,
  Until: 24:00, 1.0;
Lights,LT_1,ZONE_ONE,OccSched,Watts/Area,,6.0,,0.0,0.4,0.2,1.0;
ElectricEquipment,EQ_1,ZONE_ONE,OccSched,Watts/Area,,4.0,,0.0,0.3,0.0;
ZoneInfiltration:DesignFlowRate,INF_1,ZONE_ONE,AlwaysOn,AirChanges/Hour,,,,0.3,1,0,0,0;"""
        if add_people_lights
        else "OtherEquipment,INT_GAIN,None,ZONE_ONE,AlwaysOn,EquipmentLevel,200.0,,,0.0,0.0,0.0;"
    )
    floor_bc_line = (
        "Ground,,NoSun,NoWind,0.0,4,"
        if floor_bc == "Ground"
        else "OtherSideCoefficients,OSC_GND,NoSun,NoWind,0.0,4,"
    )
    return f"""Version,23.1;
SimulationControl,No,No,No,No,Yes;
Building,{name},0,Suburbs,0.04,0.4,FullExterior,25,1;
ShadowCalculation,PolygonClipping,Periodic,1;
Timestep,12;
HeatBalanceAlgorithm,ConductionTransferFunction,200,0.1,10000000;
Site:Location,{city},{lat},{lon},{tz},{elev};
Site:GroundTemperature:BuildingSurface,12,12,13,15,17,19,20,20,19,17,15,13;
RunPeriod,RunPeriod1,1,1,,12,31,,Sunday,No,No,No,Yes,Yes;
GlobalGeometryRules,UpperLeftCorner,CounterClockWise,World;
ScheduleTypeLimits,Any Number;
Schedule:Constant,AlwaysOn,Any Number,1.0;
Schedule:Constant,AlwaysOff,Any Number,0.0;
Schedule:Constant,CoolSP,Any Number,27.0;
{heat_sp_block}

{wall_materials}
WindowMaterial:SimpleGlazingSystem,WIN_MAT,2.4,0.62;

Construction,WALL_CON,{wall_layers};
Construction,ROOF_CON,{roof_layers};
Construction,FLOOR_CON,{floor_layers};
Construction,WIN_CON,WIN_MAT;

SurfaceProperty:OtherSideCoefficients,OSC_GND,0,10.0,1.0,0,0,0,0,,No;

Zone,ZONE_ONE,0,0,0,0,1,1,2.7,129.6,48.0;

BuildingSurface:Detailed,WALL_SOUTH,Wall,WALL_CON,ZONE_ONE,,Outdoors,,SunExposed,{wind_exp},0.5,4,
  0,0,2.7, 0,0,0, 8,0,0, 8,0,2.7;
BuildingSurface:Detailed,WALL_EAST,Wall,WALL_CON,ZONE_ONE,,Outdoors,,SunExposed,{wind_exp},0.5,4,
  8,0,2.7, 8,0,0, 8,6,0, 8,6,2.7;
BuildingSurface:Detailed,WALL_NORTH,Wall,WALL_CON,ZONE_ONE,,Outdoors,,SunExposed,{wind_exp},0.5,4,
  8,6,2.7, 8,6,0, 0,6,0, 0,6,2.7;
BuildingSurface:Detailed,WALL_WEST,Wall,WALL_CON,ZONE_ONE,,Outdoors,,SunExposed,{wind_exp},0.5,4,
  0,6,2.7, 0,6,0, 0,0,0, 0,0,2.7;
BuildingSurface:Detailed,ROOF_1,Roof,ROOF_CON,ZONE_ONE,,Outdoors,,SunExposed,{wind_exp},0.0,4,
  0,6,2.7, 0,0,2.7, 8,0,2.7, 8,6,2.7;
BuildingSurface:Detailed,FLOOR_1,Floor,FLOOR_CON,ZONE_ONE,,{floor_bc_line}
  0,0,0, 0,6,0, 8,6,0, 8,0,0;

FenestrationSurface:Detailed,WIN_S1,Window,WIN_CON,WALL_SOUTH,,0.5,,1,4,
  1.0,0,2.2, 1.0,0,0.4, 3.5,0,0.4, 3.5,0,2.2;
FenestrationSurface:Detailed,WIN_S2,Window,WIN_CON,WALL_SOUTH,,0.5,,1,4,
  4.5,0,2.2, 4.5,0,0.4, 7.0,0,0.4, 7.0,0,2.2;

{gains_block}
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
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "openubem/outputs/gpusim_m7a_s2a.csv")
    args = parser.parse_args()

    # Case 1: ASHRAE 140 Case 900 heavyweight (10 cm concrete block + 6.15 cm foam + wood siding; 8 cm concrete floor)
    mats_900 = """
Material,WOOD_SIDING,Rough,0.009,0.14,530.0,900.0,0.9,0.6,0.6;
Material,FOAM_INS,Rough,0.0615,0.04,10.0,1400.0,0.9,0.6,0.6;
Material,CONC_BLK,Rough,0.100,0.51,1400.0,1000.0,0.9,0.6,0.6;
Material,ROOF_DECK,Rough,0.019,0.14,530.0,900.0,0.9,0.6,0.6;
Material,FIBERGLASS,Rough,0.1118,0.04,12.0,840.0,0.9,0.6,0.6;
Material,PLASTER,Rough,0.010,0.16,950.0,840.0,0.9,0.6,0.6;
Material,CONC_SLAB,Rough,0.080,1.13,1400.0,1000.0,0.9,0.6,0.6;
Material:NoMass,GND_INS,Rough,25.0,0.9,0.6,0.6;
"""
    # Case 2: Dreaded thick insulated wall (10 cm XPS + 25 cm heavy concrete) that blew up float32 CTF by -29%!
    mats_thick = """
Material,PLASTER_EXT,Rough,0.020,0.87,1800.0,1000.0,0.9,0.6,0.6;
Material,XPS_10CM,Rough,0.100,0.034,35.0,1400.0,0.9,0.6,0.6;
Material,CONC_25CM,MediumRough,0.250,1.40,2300.0,1000.0,0.9,0.6,0.6;
Material,ROOF_XPS,Rough,0.140,0.034,35.0,1400.0,0.9,0.6,0.6;
Material,ROOF_CONC,MediumRough,0.200,1.40,2300.0,1000.0,0.9,0.6,0.6;
Material,FLR_CONC,MediumRough,0.150,1.40,2300.0,1000.0,0.9,0.6,0.6;
Material,FLR_INS,Rough,0.080,0.035,30.0,1400.0,0.9,0.6,0.6;
"""
    # Case 3: Thick TABULA historic masonry (38 cm solid brick + plaster + air gap)
    mats_brick = """
Material,EXT_RENDER,Rough,0.020,0.80,1600.0,1000.0,0.9,0.65,0.65;
Material,SOLID_BRICK_38,Rough,0.380,0.77,1700.0,840.0,0.9,0.65,0.65;
Material,INT_GYPSUM,Smooth,0.015,0.35,1000.0,1000.0,0.9,0.5,0.5;
Material:AirGap,CAVITY_AIR,0.18;
Material,MIN_WOOL,Rough,0.120,0.040,40.0,840.0,0.9,0.6,0.6;
Material,SLAB_20,MediumRough,0.200,1.40,2200.0,1000.0,0.9,0.6,0.6;
"""

    cases = [
        (
            "ASHRAE140_900_Heavy_NoWind",
            _build_s2a_box_idf(
                BOLOGNA_EPW, name="C900_NW", wall_materials=mats_900,
                wall_layers="WOOD_SIDING,FOAM_INS,CONC_BLK",
                roof_layers="ROOF_DECK,FIBERGLASS,PLASTER",
                floor_layers="GND_INS,CONC_SLAB",
                floor_bc="OSC", wind_exp="NoWind", use_compact_sched=False, add_people_lights=False,
            ),
            BOLOGNA_EPW,
        ),
        (
            "Thick_10XPS_25Conc_Ground",
            _build_s2a_box_idf(
                BOLOGNA_EPW, name="THICK_XPS", wall_materials=mats_thick,
                wall_layers="PLASTER_EXT,XPS_10CM,CONC_25CM",
                roof_layers="ROOF_XPS,ROOF_CONC",
                floor_layers="FLR_INS,FLR_CONC",
                floor_bc="Ground", wind_exp="WindExposed", use_compact_sched=False, add_people_lights=False,
            ),
            BOLOGNA_EPW,
        ),
        (
            "TABULA_38cmBrick_Sched_Gains",
            _build_s2a_box_idf(
                BOLOGNA_EPW, name="BRICK_38", wall_materials=mats_brick,
                wall_layers="EXT_RENDER,SOLID_BRICK_38,CAVITY_AIR,INT_GYPSUM",
                roof_layers="MIN_WOOL,SLAB_20",
                floor_layers="MIN_WOOL,SLAB_20",
                floor_bc="Ground", wind_exp="WindExposed", use_compact_sched=True, add_people_lights=True,
            ),
            BOLOGNA_EPW,
        ),
        (
            "Thick_10XPS_25Conc_Madrid",
            _build_s2a_box_idf(
                MADRID_EPW, name="THICK_MAD", wall_materials=mats_thick,
                wall_layers="PLASTER_EXT,XPS_10CM,CONC_25CM",
                roof_layers="ROOF_XPS,ROOF_CONC",
                floor_layers="FLR_INS,FLR_CONC",
                floor_bc="Ground", wind_exp="WindExposed", use_compact_sched=True, add_people_lights=True,
            ),
            MADRID_EPW,
        ),
    ]

    with tempfile.TemporaryDirectory(prefix="gpusim_m7a_s2a_") as td:
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
            compute_shading=False,
        )
        res = run_general_cuda(gb, site_weathers, record_zone_temp=True, run_chunk_days=3)
        print(f"CUDA S2a batch (B={len(ep_results)}): gpu_s={res.gpu_s:.3f}s max_launch={res.max_launch_s:.4f}s rungs={res.rungs}")

        rows = []
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
            print(
                f"  {r['case']:28s}: ep={ep_ann:8.2f} gpu={gpu_ann:8.2f} kWh "
                f"rel={rel:+7.4%} CV={cv:6.4%} NMBE={nmbe:+7.4%} dT_p999={dt_p999:.3f}K wu={int(res.warmup_days[i])}"
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
