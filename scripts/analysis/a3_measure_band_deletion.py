import os
import sys
import math
import shutil
import csv
import re
import subprocess
from pathlib import Path
from eppy.modeleditor import IDF
import pandas as pd

from openubem import config
from openubem.geometry.layout_assigner import ARCHETYPE_IDF_MAP, DEFAULT_BASELINE_AREAS

IDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))

def delete_middle_band_medium_office(idf_path: Path, planar_k: float) -> Tuple[IDF, List[str]]:
    idf = IDF(str(idf_path))
    
    mid_zones = ["MidFloor_Plenum", "Core_mid", "Perimeter_mid_ZN_1", "Perimeter_mid_ZN_2", "Perimeter_mid_ZN_3", "Perimeter_mid_ZN_4"]
    mid_zones_upper = set(z.upper() for z in mid_zones)

    # List dangling objects before deletion
    dangling_refs = []
    for obj_type in idf.idfobjects.keys():
        objs = idf.idfobjects[obj_type]
        for o in objs:
            ostr = str(o).upper()
            for mz in mid_zones_upper:
                if mz in ostr:
                    dangling_refs.append(f"{obj_type}: {getattr(o, 'Name', 'unnamed')} (refs {mz})")
                    break

    # 1. Delete all middle zones
    zones = idf.idfobjects["ZONE"]
    for z in list(zones):
        if z.Name.upper() in mid_zones_upper:
            idf.removeidfobject(z)

    # 2. Delete all surfaces belonging to middle zones
    surfaces = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    for s in list(surfaces):
        if s.Zone_Name.upper() in mid_zones_upper:
            idf.removeidfobject(s)
        else:
            # Apply planar scale to remaining surfaces
            verts = s.coords
            new_verts = [(x * planar_k, y * planar_k, z) for x, y, z in verts]
            for idx, nv in enumerate(new_verts):
                setattr(s, f"Vertex_{idx+1}_Xcoordinate", round(nv[0], 4))
                setattr(s, f"Vertex_{idx+1}_Ycoordinate", round(nv[1], 4))
                setattr(s, f"Vertex_{idx+1}_Zcoordinate", round(nv[2], 4))

    # 3. Repair surface adjacencies: Ground floor ceilings (Z=3.96m) were adjacent to MidFloor_Plenum.
    # Connect Ground floor ceiling surfaces to Top floor floor surfaces, or convert to Roof if no plenum.
    top_floors = {}
    for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if s.Zone_Name.upper().startswith("PERIMETER_TOP") or s.Zone_Name.upper().startswith("CORE_TOP"):
            if s.Surface_Type.upper() == "FLOOR":
                top_floors[s.Zone_Name.upper()] = s.Name

    for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if s.Outside_Boundary_Condition.upper() == "SURFACE":
            target_surf = s.Outside_Boundary_Condition_Object.upper()
            # If target surface was in a deleted middle zone, repair boundary condition
            if any(mz in target_surf for mz in mid_zones_upper):
                # If ground ceiling, make adjacent to top floor or outdoors
                if s.Surface_Type.upper() in ("CEILING", "ROOF"):
                    s.Outside_Boundary_Condition = "Outdoors"
                    s.Outside_Boundary_Condition_Object = ""
                    s.Sun_Exposure = "SunExposed"
                    s.Wind_Exposure = "WindExposed"
                elif s.Surface_Type.upper() == "FLOOR":
                    s.Outside_Boundary_Condition = "Ground"
                    s.Outside_Boundary_Condition_Object = ""
                    s.Sun_Exposure = "NoSun"
                    s.Wind_Exposure = "NoWind"

    # 4. Clean up HVAC / Sizing / Thermostat / Gain objects referencing deleted middle zones
    for obj_type in list(idf.idfobjects.keys()):
        if obj_type in ("BUILDINGSURFACE:DETAILED", "ZONE"):
            continue
        for o in list(idf.idfobjects[obj_type]):
            ostr = str(o).upper()
            if any(mz in ostr for mz in mid_zones_upper):
                try:
                    idf.removeidfobject(o)
                except Exception:
                    pass

    return idf, dangling_refs

def run_ep(idf_obj: IDF, run_dir: Path, epw_path: Path) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    idf_path = run_dir / "in.idf"
    idf_obj.saveas(str(idf_path))
    
    ep_exe = config.ENERGYPLUS_PATH / ("energyplus.exe" if sys.platform == "win32" else "energyplus")
    cmd = [
        str(ep_exe),
        "-w", str(epw_path),
        "-d", str(run_dir),
        "-x",
        "-r",
        str(idf_path)
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    end_file = run_dir / "eplusout.end"
    end_text = end_file.read_text() if end_file.exists() else ""
    
    err_file = run_dir / "eplusout.err"
    err_text = err_file.read_text() if err_file.exists() else ""
    
    severe_lines = [line.strip() for line in err_text.splitlines() if "**  Severe  **" in line]
    fatal_lines = [line.strip() for line in err_text.splitlines() if "**  Fatal  **" in line]

    return {
        "run_dir": str(run_dir),
        "returncode": res.returncode,
        "end_text": end_text.strip(),
        "severe_count": len(severe_lines),
        "fatal_count": len(fatal_lines),
        "severe_lines": severe_lines,
        "fatal_lines": fatal_lines,
        "err_text": err_text
    }

def main():
    archetype = "MediumOffice"
    baseline_idf_path = config.BASELINE_IDF_DIR / ARCHETYPE_IDF_MAP[archetype]
    epw_path = Path(r"C:\Users\o_iseri\.openubem\epw\USA_NY_Buffalo.Niagara.Intl.AP.725280_TMYx.2011-2025.epw")

    # Real building shorter than prototype: n_real = 2 storeys (prototype has 3 storeys).
    # Target floor area = 2000 m2 (footprint = 1000 m2, 2 storeys).
    # Prototype plate = 1660.73 m2. Target plate = 1000 m2.
    plate_ratio = 1000.0 / 1660.73
    planar_k = math.sqrt(plate_ratio) # 0.7760

    idf_shorter, dangling_refs = delete_middle_band_medium_office(baseline_idf_path, planar_k)

    base_results_dir = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\results")
    run_dir = base_results_dir / "a3_run_shorter_deletion"

    print(f"=== A3 MEASUREMENT: SHORTER CASE BAND DELETION ({archetype} 3 storeys -> 2 storeys) ===")
    print(f"Encountered {len(dangling_refs)} dangling references before deletion:")
    for ref in dangling_refs[:15]:
        print(f"  {ref}")
    if len(dangling_refs) > 15:
        print(f"  ... and {len(dangling_refs) - 15} more")

    print("\nRunning EnergyPlus 23.1 on deleted band model...")
    res = run_ep(idf_shorter, run_dir, epw_path)

    print("\n=== EnergyPlus Execution Outcome ===")
    print(f"Return Code: {res['returncode']}")
    print(f"Fatal Count: {res['fatal_count']}, Severe Count: {res['severe_count']}")
    if res['fatal_lines']:
        print("Fatal lines:")
        for line in res['fatal_lines']:
            print(f"  {line}")
    if res['severe_lines']:
        print("Severe lines (verbatim):")
        for line in res['severe_lines']:
            print(f"  {line}")

    # Write summary CSV artifact
    summary_path = base_results_dir / "a3_shorter_deletion_summary.csv"
    summary_data = [
        {
            "archetype": archetype,
            "proto_storeys": 3,
            "target_storeys": 2,
            "dangling_ref_count": len(dangling_refs),
            "returncode": res["returncode"],
            "fatal_count": res["fatal_count"],
            "severe_count": res["severe_count"],
            "fatal_lines": "; ".join(res["fatal_lines"]) if res["fatal_lines"] else "None",
            "severe_lines": "; ".join(res["severe_lines"]) if res["severe_lines"] else "None",
        }
    ]
    df_sum = pd.DataFrame(summary_data)
    df_sum.to_csv(summary_path, index=False)
    df_sum.to_csv(Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\a3_shorter_deletion_summary.csv"), index=False)
    print(f"\nWrote summary CSV to {summary_path}")

if __name__ == "__main__":
    main()
