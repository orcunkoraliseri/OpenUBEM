"""B05e: is the E-LA-28 envelope defect (unscaled Zone X/Y Origin) visible in
energy? Same ~10 real buildings, EnergyPlus before and after B05, EUI reported
both ways -- PLAN_storey-matching_implementation.md B05e.

"Before" is produced by monkeypatching layout_assigner.scale_baseline_idf back
to its pre-B05 body (no Zone Origin loop) for the duration of one build call,
then restoring the real (post-B05) function for the "after" build of the same
building. This avoids git stash / touching any committed file -- the entire
plan explicitly forbids production code changes outside this dispatch, and B05
itself is not to be reverted on disk.

Throwaway diagnostic script (scripts/analysis/, not shipped). Real EnergyPlus
23.1 runs only, via the production openubem.simulation.runner path.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

from openubem import config
from openubem.geometry import layout_assigner
from openubem.geometry.footprint import derive_num_floors
from openubem.simulation.runner import run_energyplus, classify_outcome

# Reuse the exact SQL-based EUI parser T19's harvest used for trim_outputs=True
# runs (RunPeriod meters + hourly-zone-var fallback) -- eplustbl.csv/htm are
# NOT written when trim_outputs=True (write_outputs() skips
# OUTPUT:TABLE:SUMMARYREPORTS under trim_hourly=True), so a tabular-CSV parser
# would silently return nothing for every run in this task.
sys.path.insert(0, str(REPO / "scripts" / "cluster"))
from t19_harvest_layout_assign import _parse_sql  # noqa: E402

OUT_DIR = REPO / "openubem" / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
ARC_RESULTS = (
    REPO / "docs" / "docs_ACTIVE" / "simulation-Resolution" / "layoutAssigner"
    / "debug" / "storey-Matching" / "results"
)
SCRATCH_DIR = REPO / "scratchpad" / "b05e_work"
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

FIXTURE = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results"
    / "phaseE" / "nyc_suburban" / "01_buildings.gpkg"
)
CELL_CFG = {"lat": 40.7052, "lon": -73.5985, "state": "NY"}  # nyc_suburban, t19 CELL_CONFIGS

# 10 real nyc_suburban buildings, real layout_assign successes (status=success,
# zoning_strategy=layout_assign) from t19_layout_assign_eui.csv: 8 MidriseApartment
# (the dominant/headline archetype, F-08/F-09) spanning floor_area_m2 23-153,
# plus 2 SmallOffice for archetype variety.
TARGET_IDS = [
    "way/1014146287", "way/1108091110", "way/1108091236", "way/1108092667",
    "way/1108092665", "way/1108091399", "way/1108091564", "way/845749027",
    "way/1108091546", "way/815835740",
]

# ── the pre-B05 body of scale_baseline_idf() -- identical to the current
# function's own code, minus the Zone X/Y Origin loop this task added. ──
def _scale_baseline_idf_pre_b05(idf, scale_factor_dict):
    planar_k = scale_factor_dict["planar_scale_factor"]
    area_s = scale_factor_dict["area_scale_ratio"]

    for cls in layout_assigner._GEOMETRY_SURFACE_CLASSES:
        for surf in idf.idfobjects.get(cls, []):
            scaled_coords = [(x * planar_k, y * planar_k, z) for x, y, z in surf.coords]
            surf.setcoords(scaled_coords)

    # (B05's new Zone Origin loop deliberately OMITTED here -- this is the "before" replica.)

    for cls, x_field, y_field in layout_assigner._GEOMETRY_POINT_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            x_val, y_val = getattr(obj, x_field), getattr(obj, y_field)
            if not layout_assigner._is_blank_or_autosize(x_val):
                setattr(obj, x_field, float(x_val) * planar_k)
            if not layout_assigner._is_blank_or_autosize(y_val):
                setattr(obj, y_field, float(y_val) * planar_k)

    for cls, method_field, value_field, absolute_method in layout_assigner._ABSOLUTE_LOAD_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            if str(getattr(obj, method_field, "")).strip() != absolute_method:
                continue
            val = getattr(obj, value_field)
            if layout_assigner._is_blank_or_autosize(val):
                continue
            setattr(obj, value_field, float(val) * area_s)

    for cls, value_field in layout_assigner._UNCONDITIONAL_ABSOLUTE_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            val = getattr(obj, value_field)
            if layout_assigner._is_blank_or_autosize(val):
                continue
            setattr(obj, value_field, float(val) * area_s)

    for cls, obj_name, value_field, s1_value in layout_assigner._NAMED_ABSOLUTE_SPECS:
        for obj in idf.idfobjects.get(cls, []):
            if str(obj.Name).strip() != obj_name:
                continue
            val = getattr(obj, value_field)
            if not layout_assigner._is_blank_or_autosize(val):
                continue
            setattr(obj, value_field, s1_value * area_s)

    return idf


def get_base_data():
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics
    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw

    weather_dir = SCRATCH_DIR / "weather"
    weather_dir.mkdir(parents=True, exist_ok=True)
    stations = load_stations()
    station, dist_km = resolve_station(CELL_CFG["lat"], CELL_CFG["lon"], stations)
    epw_path = fetch_epw(station, output_dir=weather_dir)
    print(f"EPW station: {station.get('station_id')} at {dist_km:.1f} km -> {epw_path}")

    gdf_raw = gpd.read_file(str(FIXTURE))
    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")

    gdf_26 = BuildingClassifier().classify(gdf_in)
    zone_df = assign_climate_zones(gdf_26)
    gdf_29 = gdf_26.copy()
    gdf_29["climate_zone"] = pd.Categorical(zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB))
    gdf_29["epw_path"] = str(epw_path)
    gdf_29["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values, categories=["ASHRAE_STANDARD", "HEURISTIC"]
    )
    gdf_57, schedule_library = enrich_semantics(gdf_29)
    return gdf_57, schedule_library, epw_path


def build_one(row, gdf_sample, schedule_library, build_dir, before: bool):
    from openubem.idf.builder import BuildingIDF

    real_fn = layout_assigner.scale_baseline_idf
    if before:
        layout_assigner.scale_baseline_idf = _scale_baseline_idf_pre_b05
    try:
        bidf = BuildingIDF(row, thermal_mass=True, resolution_mode="layout_assign", trim_outputs=True)
        manifest_row = bidf.build(gdf_sample, schedule_library, build_dir)
    finally:
        layout_assigner.scale_baseline_idf = real_fn
    return manifest_row


def run_one(idf_path: Path, epw_path, run_dir: Path, osm_id: str, floor_area_m2: float):
    """Run one real EnergyPlus 23.1 job and parse EUI with T19's own SQL-meter
    parser (_parse_sql) -- the tabular eplustbl.csv/.htm files do not exist
    under trim_outputs=True (write_outputs() skips OUTPUT:TABLE:SUMMARYREPORTS
    when trim_hourly=True), so this is the only correct EUI source here."""
    run_dir.mkdir(parents=True, exist_ok=True)
    task = SimpleNamespace(osm_id=osm_id, epw_path=str(epw_path), work_dir=str(run_dir), idf_path=str(idf_path))
    raw = run_energyplus(task, timeout_s=300)
    result = classify_outcome(raw, run_dir)
    eui = None
    if result["status"] == "success":
        sql_path = run_dir / "eplusout.sql"
        if sql_path.exists():
            eui = _parse_sql(sql_path, floor_area_m2)
    return result, eui


def main():
    print("Loading base data for nyc_suburban ...")
    gdf_57, schedule_library, epw_path = get_base_data()
    print(f"Loaded {len(gdf_57)} buildings.")

    rows = []
    t0 = time.monotonic()
    for osm_id in TARGET_IDS:
        sample = gdf_57[gdf_57["osm_id"].astype(str) == osm_id]
        if sample.empty:
            print(f"  SKIP {osm_id}: not found in gdf_57")
            continue
        row = sample.iloc[0].copy()
        arch = row["archetype_id"]
        clean = osm_id.replace("/", "_")
        print(f"\n=== {osm_id} ({arch}) ===")

        for before, tag in [(True, "before_B05"), (False, "after_B05")]:
            build_dir = SCRATCH_DIR / clean / tag
            (build_dir / "idfs").mkdir(parents=True, exist_ok=True)
            manifest_row = build_one(row, gdf_57, schedule_library, build_dir, before=before)
            if manifest_row["generation_status"] != "success":
                print(f"  [{tag}] BUILD FAILED: {manifest_row['generation_status']}")
                rows.append({"osm_id": osm_id, "archetype_id": arch, "variant": tag,
                             "build_status": manifest_row["generation_status"]})
                continue
            idf_path = Path(manifest_row["idf_path"])
            run_dir = ARC_RESULTS / "b05e_runs" / clean / tag
            floor_area_m2 = float(row["footprint_area_m2"]) * derive_num_floors(row)
            result, eui = run_one(idf_path, epw_path, run_dir, osm_id, floor_area_m2)
            status = result["status"]
            n_sev = result.get("n_severe")
            print(f"  [{tag}] {status}, severe={n_sev}, "
                  f"total_eui={eui.get('total_eui') if eui else None}")
            row_out = {
                "osm_id": osm_id, "archetype_id": arch, "variant": tag,
                "build_status": "success", "run_status": status,
                "n_warnings": result.get("n_warnings"), "n_severe": n_sev,
                "error_summary": result.get("error_summary", ""),
                "floor_area_m2": floor_area_m2,
            }
            if eui:
                row_out.update(eui)  # heating_eui, cooling_eui, ..., total_eui (T19's own key set)
            rows.append(row_out)

    elapsed = time.monotonic() - t0
    df = pd.DataFrame(rows)
    out_csv = ARC_RESULTS / "b05e_energy_delta.csv"
    df.to_csv(out_csv, index=False)
    df.to_csv(OUT_DIR / "comparisons" / "b05e_energy_delta.csv", index=False)
    print(f"\nWrote {out_csv} ({elapsed/60:.1f} min total)")

    # Pivot to a before/after/delta table for the progress log.
    if "total_eui" in df.columns:
        piv = df.pivot_table(index=["osm_id", "archetype_id"], columns="variant",
                              values="total_eui", aggfunc="first")
        if "before_B05" in piv.columns and "after_B05" in piv.columns:
            piv["delta_eui"] = piv["after_B05"] - piv["before_B05"]
            piv["delta_pct"] = 100.0 * piv["delta_eui"] / piv["before_B05"]
            piv_path = ARC_RESULTS / "b05e_energy_delta_pivot.csv"
            piv.to_csv(piv_path)
            print(f"Wrote pivot to {piv_path}")
            print(piv)


if __name__ == "__main__":
    main()
