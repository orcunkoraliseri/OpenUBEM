"""One extra matched S=1 control for case D: HighriseApartment, n_real=n_proto=3
(identity, no multiplier), SAME footprint_area_m2=350.0 as case D so the
Electricity:Facility ratio vs case D (multiplier=18) is a genuine matched-plate
comparison, not confounded by the different plate size case A used (500 m2)."""
import sys
import time
from pathlib import Path

REPO = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "analysis"))
import c01_storey_matching_regression as c01
import geopandas as gpd
import pandas as pd

CASE_ID = "D_control_S1_highrise3"

def get_one_row():
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics
    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw

    weather_dir = c01.SCRATCH_DIR / "weather"
    stations = load_stations()
    station, dist_km = resolve_station(c01.CELL_CFG["lat"], c01.CELL_CFG["lon"], stations)
    epw_path = fetch_epw(station, output_dir=weather_dir)

    gdf_raw = gpd.read_file(str(c01.FIXTURE))
    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy().iloc[0:1].copy().reset_index(drop=True)
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")

    gdf_26 = BuildingClassifier().classify(gdf_in)
    gdf_26.loc[0, "osm_id"] = f"c01/{CASE_ID}"
    gdf_26.loc[0, "archetype_id"] = "HighriseApartment"
    gdf_26.loc[0, "levels"] = 3

    zone_df = assign_climate_zones(gdf_26)
    gdf_29 = gdf_26.copy()
    gdf_29["climate_zone"] = pd.Categorical(zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB))
    gdf_29["epw_path"] = str(epw_path)
    gdf_29["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values, categories=["ASHRAE_STANDARD", "HEURISTIC"]
    )
    gdf_57, schedule_library = enrich_semantics(gdf_29)
    gdf_57.loc[0, "footprint_area_m2"] = 350.0
    return gdf_57, schedule_library, epw_path


def main():
    gdf_57, schedule_library, epw_path = get_one_row()
    row = gdf_57.iloc[0].copy()

    reg = c01.layout_assigner.get_registry()
    from geomeppy import IDF as GeomIDF
    from openubem import config
    try:
        GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    except Exception:
        pass
    probe = GeomIDF(str(reg.get_baseline_idf("HighriseApartment")))
    band_map = c01.layout_assigner.compute_band_map(probe)
    match_result = c01.layout_assigner.match_storeys(probe, 3, band_map)
    print("pre-run:", band_map["n_proto"], match_result["status"], match_result["multiplier"])

    build_dir = c01.SCRATCH_DIR / CASE_ID
    (build_dir / "idfs").mkdir(parents=True, exist_ok=True)
    manifest_row = c01.build_one(row, gdf_57, schedule_library, build_dir)
    print("build:", manifest_row["generation_status"], manifest_row.get("data_quality_flag"))
    if manifest_row["generation_status"] != "success":
        return

    idf_path = Path(manifest_row["idf_path"])
    run_dir = c01.ARC_RESULTS / "c01_runs" / CASE_ID
    floor_area_m2 = 350.0 * 3
    t0 = time.monotonic()
    result, eui = c01.run_one(idf_path, epw_path, run_dir, row["osm_id"], floor_area_m2)
    print(f"RUN status={result['status']} n_severe={result.get('n_severe')} "
          f"elapsed={(time.monotonic()-t0)/60:.1f}min")
    print("total_eui=", eui.get("total_eui") if eui else None)


if __name__ == "__main__":
    main()
