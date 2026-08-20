"""T18 side-check -- confirm that trim_outputs=True (used by every layout_assign
rebuild in this arc, including T05 and T15) is what strips the zone-level
Output:Variable objects _check_zone_integrity's layout_assign branch needs,
by rebuilding ONE small layout_assign building (la_urban/relation/6356887,
6 zones, SmallOffice prototype) with trim_outputs=False and re-checking
parse_building().
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

OUT_DIR = REPO / "scratchpad" / "open03-t18-trim-check"
FIXTURE_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet")
CELL = "la_urban"
TARGET = "relation/6356887"
CFG = {"lat": 34.0584, "lon": -118.3040, "state": "CA"}


def main():
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics
    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw
    from openubem.idf.builder import run_step3
    from openubem.simulation.parallel import SimTask
    from openubem.simulation.runner import run_energyplus, classify_outcome
    from openubem.results.parser import parse_building

    fixture = FIXTURE_ROOT / CELL / "01_buildings.gpkg"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    weather_dir = OUT_DIR / "weather"
    weather_dir.mkdir(parents=True, exist_ok=True)

    stations = load_stations()
    station, dist_km = resolve_station(CFG["lat"], CFG["lon"], stations)
    epw_path = fetch_epw(station, output_dir=weather_dir)

    gdf_raw = gpd.read_file(str(fixture))
    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")
    gdf_26 = BuildingClassifier().classify(gdf_in)
    hit = gdf_26[gdf_26["osm_id"].astype(str) == TARGET]
    print(f"classify(): {hit[['osm_id','archetype_id']].to_string()}")

    zone_df = assign_climate_zones(gdf_26)
    gdf_29 = gdf_26.copy()
    gdf_29["climate_zone"] = pd.Categorical(zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB))
    gdf_29["epw_path"] = str(epw_path)
    gdf_29["provenance_climate_zone"] = pd.Categorical(zone_df["provenance_climate_zone"].values, categories=["ASHRAE_STANDARD", "HEURISTIC"])
    gdf_57, schedule_library = enrich_semantics(gdf_29)
    gdf_sample = gdf_57[gdf_57["osm_id"].astype(str) == TARGET].copy()

    step3_dir = OUT_DIR / "step3_layout_assign"
    step3_dir.mkdir(parents=True, exist_ok=True)
    manifest = run_step3(gdf_sample, schedule_library, step3_dir, n_jobs=1,
                          resolution_mode="layout_assign", trim_outputs=False)
    print(manifest.to_string())
    mrow = manifest.iloc[0]

    safe_id = TARGET.replace("/", "_")
    run_dir = OUT_DIR / "sim" / safe_id
    run_dir.mkdir(parents=True, exist_ok=True)
    task = SimTask(osm_id=TARGET, idf_path=str(mrow["idf_path"]), epw_path=str(epw_path), work_dir=str(run_dir))
    raw = run_energyplus(task)
    outcome = classify_outcome(raw, run_dir)
    print(f"sim outcome: {outcome}")

    sql_path = run_dir / "eplusout.sql"
    manifest_row = pd.Series({
        "osm_id": TARGET, "num_zones": 6, "data_quality_flag": "",
        "resolution_mode": "layout_assign",
        "footprint_area_m2": float(gdf_sample.iloc[0]["footprint_area_m2"]),
        "levels": float(gdf_sample.iloc[0].get("levels", 1) or 1),
    })
    result = parse_building(sql_path if sql_path.exists() else None, None, manifest_row)
    print("\n=== parse_building() result, trim_outputs=False ===")
    for k, v in result.items():
        print(f"  {k} = {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
