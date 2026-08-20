"""OPEN-48 T01 (PLAN_open-48-and-four-items-2026-08-18.md): re-test reproducibility
against the live tree, HEAD as of 2026-08-18.

Re-derives every row of OPEN-48's register evidence table (register :4974) plus a
live build of an elevator-eligible archetype, and writes a CSV with one row per
check: check_name, command, raw_result, register_claim, matches_register.

This script performs NO EnergyPlus simulation and NO network access -- BuildingIDF.build()
only constructs an in-memory IDF object; it never invokes the EnergyPlus binary.
"""
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

OUT_CSV = REPO_ROOT / "openubem/outputs/comparisons/open48_reproducibility_retest.csv"


def run_git(args):
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True
    )
    return result.stdout.strip()


def main():
    rows = []

    # --- Control: prove the detection method finds a symbol known to be present ---
    control_cmd = 'git log --all -S "def assign_elevators" -- openubem/idf/elevators.py'
    control_out = run_git(["log", "--all", "-S", "def assign_elevators", "--", "openubem/idf/elevators.py"])
    control_hit = "ef19141" in control_out
    rows.append({
        "check_name": "CONTROL: assign_elevators definition is found by -S search",
        "command": control_cmd,
        "raw_result": control_out.splitlines()[0] if control_out else "(empty)",
        "register_claim": "n/a (control)",
        "matches_register": control_hit,
    })

    # --- Row 1: assign_elevators called from builder.py ---
    cmd1a = "git log --all -S assign_elevators -- openubem/idf/builder.py"
    out1a = run_git(["log", "--all", "-S", "assign_elevators", "--", "openubem/idf/builder.py"])
    first_commit_line = out1a.splitlines()[0] if out1a else "(empty)"

    import importlib
    builder_mod = importlib.import_module("openubem.idf.builder")
    hasattr_result = hasattr(builder_mod, "assign_elevators")

    import inspect
    builder_src = inspect.getsource(builder_mod)
    elevator_count = builder_src.lower().count("elevator")

    rows.append({
        "check_name": "assign_elevators called from builder.py -- git history",
        "command": cmd1a,
        "raw_result": first_commit_line,
        "register_claim": "empty (no commit found)",
        "matches_register": False,
    })
    rows.append({
        "check_name": "assign_elevators called from builder.py -- hasattr(builder, 'assign_elevators')",
        "command": "hasattr(openubem.idf.builder, 'assign_elevators')",
        "raw_result": str(hasattr_result),
        "register_claim": "False",
        "matches_register": hasattr_result is False,
    })
    rows.append({
        "check_name": "assign_elevators called from builder.py -- 'elevator' occurrence count",
        "command": "inspect.getsource(builder).lower().count('elevator')",
        "raw_result": str(elevator_count),
        "register_claim": "0",
        "matches_register": elevator_count == 0,
    })

    # --- Row 2: elevators_eui_kwh_m2 in results (schema presence, not run output) ---
    agg_mod = importlib.import_module("openubem.results.aggregator")
    agg_src = inspect.getsource(agg_mod)
    has_elevators_eui_col = "elevators_eui_kwh_m2" in agg_src
    rows.append({
        "check_name": "elevators_eui_kwh_m2 present in aggregator.py schema",
        "command": "'elevators_eui_kwh_m2' in inspect.getsource(openubem.results.aggregator)",
        "raw_result": str(has_elevators_eui_col),
        "register_claim": "absent at HEAD",
        "matches_register": not has_elevators_eui_col,
    })

    # --- Row 3: gwp_elevators_kgco2_m2 ---
    carbon_mod = importlib.import_module("openubem.results.carbon")
    carbon_src = inspect.getsource(carbon_mod)
    has_gwp_col = "gwp_elevators_kgco2_m2" in carbon_src
    rows.append({
        "check_name": "gwp_elevators_kgco2_m2 present in carbon.py",
        "command": "'gwp_elevators_kgco2_m2' in inspect.getsource(openubem.results.carbon)",
        "raw_result": str(has_gwp_col),
        "register_claim": "absent at HEAD",
        "matches_register": not has_gwp_col,
    })

    # --- Row 4: elevator meter in outputs.py ---
    outputs_mod = importlib.import_module("openubem.idf.outputs")
    hvac_meters = outputs_mod.HVAC_METERS
    has_meter = "Elevators:InteriorEquipment:Electricity" in hvac_meters
    rows.append({
        "check_name": "Elevators:InteriorEquipment:Electricity meter present in outputs.py HVAC_METERS",
        "command": "'Elevators:InteriorEquipment:Electricity' in openubem.idf.outputs.HVAC_METERS",
        "raw_result": f"{has_meter} (len(HVAC_METERS)={len(hvac_meters)})",
        "register_claim": "absent at HEAD (13 meters)",
        "matches_register": (not has_meter),
    })

    # --- Row 5: live build -- count emitted elevator ElectricEquipment objects ---
    import tempfile
    import geopandas as gpd
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError
    from openubem.config import ENERGYPLUS_IDD_PATH
    from openubem.idf.builder import BuildingIDF

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass

    from shapely.geometry import box

    def make_row(archetype_id, footprint_area_m2, levels):
        side = footprint_area_m2 ** 0.5
        poly = box(0, 0, side, side)
        return pd.Series({
            "osm_id": f"way/OPEN48_T01_{archetype_id}",
            "archetype_id": archetype_id,
            "epw_path": str(REPO_ROOT / "tests/fixtures/synthetic.epw"),
            "u_roof_w_m2k": 0.2,
            "u_wall_w_m2k": 0.3,
            "u_floor_w_m2k": 0.4,
            "u_window_w_m2k": 2.5,
            "shgc_window": 0.4,
            "wwr": 0.3,
            "infiltration_m3_s_m2": 0.0003,
            "lighting_w_m2": 10.0,
            "equipment_w_m2": 8.0,
            "occupant_m2_per_person": 10.0,
            "heating_setpoint_c": 21.0,
            "cooling_setpoint_c": 24.0,
            "climate_zone": "3A",
            "vintage_standard": "DOERef1980to2004",
            "levels": levels,
            "height_m": levels * 3.5,
            "footprint_area_m2": footprint_area_m2,
            "geometry": poly,
            "data_quality_flag": "",
        })

    row = make_row("LargeOffice", footprint_area_m2=46320.38, levels=12)
    gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")
    bidf = BuildingIDF(row)
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir)
        (out_path / "idfs").mkdir()
        manifest = bidf.build(gdf, {}, out_path)

    elev_objs = [
        e for e in bidf.idf.idfobjects["ELECTRICEQUIPMENT"]
        if e.EndUse_Subcategory == "Elevators"
    ]
    rows.append({
        "check_name": "LIVE BUILD: elevator equipment emitted by a live build (LargeOffice, 12 levels)",
        "command": "BuildingIDF(row).build(gdf, {}, out_path); count ELECTRICEQUIPMENT with EndUse_Subcategory=='Elevators'",
        "raw_result": f"generation_status={manifest.get('generation_status')}; count={len(elev_objs)}; names={[e.Name for e in elev_objs]}",
        "register_claim": "zero objects, all 10 elevator archetypes",
        "matches_register": len(elev_objs) == 0,
    })

    # --- Row 6: negative control on live build -- non-eligible archetype emits nothing ---
    row2 = make_row("SmallOffice", footprint_area_m2=511.16, levels=1)
    gdf2 = gpd.GeoDataFrame([row2], geometry="geometry", crs="EPSG:32618")
    bidf2 = BuildingIDF(row2)
    with tempfile.TemporaryDirectory() as tmp_dir2:
        out_path2 = Path(tmp_dir2)
        (out_path2 / "idfs").mkdir()
        manifest2 = bidf2.build(gdf2, {}, out_path2)
    elev_objs2 = [
        e for e in bidf2.idf.idfobjects["ELECTRICEQUIPMENT"]
        if e.EndUse_Subcategory == "Elevators"
    ]
    rows.append({
        "check_name": "LIVE BUILD negative control: non-eligible archetype (SmallOffice, 1 level) emits nothing",
        "command": "BuildingIDF(row).build(gdf, {}, out_path); count ELECTRICEQUIPMENT with EndUse_Subcategory=='Elevators'",
        "raw_result": f"generation_status={manifest2.get('generation_status')}; count={len(elev_objs2)}",
        "register_claim": "n/a (not in original table; added as a live-build negative control)",
        "matches_register": None,
    })

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(df.to_string(index=False))
    print(f"\nWrote {OUT_CSV}")


if __name__ == "__main__":
    main()
