"""T15 of PLAN_twenty-items-2026-08-19.md -- rebuild nyc_rural/way_965718401
(the one OPEN-38 layout_assign malformed-door building that COMPLETES and
publishes results) through the real, unmodified pipeline, so its EUI can be
computed by the project's own production parser (openubem.results.parser).

Why a rebuild is needed rather than reading the existing E02 harvest artifact
directly: the existing eplusout.sql at
%LOCALAPPDATA%/Temp/ubem_e02_harvest/nyc_rural_layout_assign/way_965718401/
has an EMPTY ReportDataDictionary (no hourly variables were captured), so
openubem.results.parser.parse_building() returns failed_zone_mismatch /
"zero zone-level keys found in SQL" on it -- it cannot deliver a production
EUI. This mirrors OPEN-38 T05's precedent exactly (same fixture family, same
real pipeline, no production code touched, local EnergyPlus only, no cluster).

Fixture: %LOCALAPPDATA%/Temp/ubem_validation/open48_refleet/nyc_rural/01_buildings.gpkg
(same one T05 used, already verified present).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

OUT_DIR = REPO / "scratchpad" / "open38-t15-rebuild"
FIXTURE_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet")
CELL = "nyc_rural"
TARGET = "way/965718401"
CFG = {"lat": 42.0396, "lon": -74.1143, "state": "NY"}


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
    print(f"fixture: {fixture} exists={fixture.exists()}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    weather_dir = OUT_DIR / "weather"
    weather_dir.mkdir(parents=True, exist_ok=True)

    stations = load_stations()
    station, dist_km = resolve_station(CFG["lat"], CFG["lon"], stations)
    epw_path = fetch_epw(station, output_dir=weather_dir)
    print(f"EPW: {epw_path} (station dist {dist_km:.1f} km)")

    gdf_raw = gpd.read_file(str(fixture))
    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")
    gdf_26 = BuildingClassifier().classify(gdf_in)

    hit = gdf_26[gdf_26["osm_id"].astype(str) == TARGET]
    print(f"classify() output for {TARGET}:\n{hit[['osm_id','archetype_id']].to_string()}")
    if hit.empty:
        print("NOT FOUND in fixture -- stop.")
        return 1

    zone_df = assign_climate_zones(gdf_26)
    gdf_29 = gdf_26.copy()
    gdf_29["climate_zone"] = pd.Categorical(
        zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB)
    )
    gdf_29["epw_path"] = str(epw_path)
    gdf_29["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values,
        categories=["ASHRAE_STANDARD", "HEURISTIC"],
    )
    gdf_57, schedule_library = enrich_semantics(gdf_29)
    gdf_sample = gdf_57[gdf_57["osm_id"].astype(str) == TARGET].copy()

    step3_dir = OUT_DIR / "step3_layout_assign"
    step3_dir.mkdir(parents=True, exist_ok=True)
    manifest = run_step3(
        gdf_sample, schedule_library, step3_dir,
        n_jobs=1, resolution_mode="layout_assign", trim_outputs=True,
    )
    manifest.to_csv(OUT_DIR / "idf_manifest.csv", index=False)
    print(manifest.to_string())

    mrow = manifest.iloc[0]
    if str(mrow["generation_status"]) != "success":
        print(f"IDF generation FAILED: {mrow['generation_status']}")
        return 1

    safe_id = TARGET.replace("/", "_")
    run_dir = OUT_DIR / "sim" / safe_id
    run_dir.mkdir(parents=True, exist_ok=True)
    task = SimTask(osm_id=TARGET, idf_path=str(mrow["idf_path"]),
                    epw_path=str(epw_path), work_dir=str(run_dir))
    t0 = time.monotonic()
    raw = run_energyplus(task)
    elapsed = time.monotonic() - t0
    outcome = classify_outcome(raw, run_dir)
    print(f"sim outcome: {outcome} elapsed={elapsed:.1f}s")

    err_path = run_dir / "eplusout.err"
    err_text = err_path.read_text(errors="replace") if err_path.exists() else ""
    print("tail of err:\n" + "\n".join(err_text.splitlines()[-15:]))

    sql_path = run_dir / "eplusout.sql"
    manifest_row = pd.Series({
        "osm_id": TARGET,
        "num_zones": int(gdf_sample.iloc[0].get("num_zones", 67)) if "num_zones" in gdf_sample.columns else 67,
        "data_quality_flag": str(gdf_sample.iloc[0].get("data_quality_flag", "") or ""),
        "resolution_mode": "layout_assign",
        "footprint_area_m2": float(gdf_sample.iloc[0]["footprint_area_m2"]) if "footprint_area_m2" in gdf_sample.columns else 34.160848,
        "levels": float(gdf_sample.iloc[0].get("levels", 1) or 1),
    })
    result = parse_building(sql_path if sql_path.exists() else None, None, manifest_row)
    print("\n=== production parse_building() result ===")
    for k, v in result.items():
        print(f"  {k} = {v}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
