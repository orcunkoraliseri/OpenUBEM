"""B08b: verify the D8 re-centring translation is energy-null. Same ~10 real
nyc_suburban buildings B05e used, EnergyPlus before/after, EUI reported both
ways -- PLAN_storey-matching_implementation.md B08b acceptance ("re-run B05e's
~10-building before/after and report the deltas").

"Before" is produced by monkeypatching layout_assigner.scale_baseline_idf back
to its pre-B08b body -- an EXACT copy of the current function's own code,
stopping at `return idf` right after the B06 Boiler/Chiller/Humidifier loop,
i.e. everything through B05/B06 but WITHOUT the new re-centring translation
block this task adds. "After" is the real (current HEAD) function, unpatched.

Control-differs check (E-LA-31 standing rule, three prior failures in this
arc): before running the before/after set, this script builds ONE building
with each variant and asserts the two produced IDFs are NOT geometrically
identical (Zone Origins must differ) -- if they came back identical the
control would silently be a copy of the treatment, exactly the failure mode
this arc has hit three times.

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

sys.path.insert(0, str(REPO / "scripts" / "cluster"))
from t19_harvest_layout_assign import _parse_sql  # noqa: E402

OUT_DIR = REPO / "openubem" / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
ARC_RESULTS = (
    REPO / "docs" / "docs_ACTIVE" / "simulation-Resolution" / "layoutAssigner"
    / "debug" / "storey-Matching" / "results"
)
SCRATCH_DIR = REPO / "scratchpad" / "b08b_work"
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

FIXTURE = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results"
    / "phaseE" / "nyc_suburban" / "01_buildings.gpkg"
)
CELL_CFG = {"lat": 40.7052, "lon": -73.5985, "state": "NY"}  # nyc_suburban, t19 CELL_CONFIGS

# Same 10 buildings B05e used (t19_layout_assign_eui.csv real successes: 8
# MidriseApartment spanning floor_area_m2 23-153, plus 2 SmallOffice).
TARGET_IDS = [
    "way/1014146287", "way/1108091110", "way/1108091236", "way/1108092667",
    "way/1108092665", "way/1108091399", "way/1108091564", "way/845749027",
    "way/1108091546", "way/815835740",
]


# ── pre-B08b body: current HEAD's scale_baseline_idf(), verbatim, MINUS the
# new re-centring translation block this task adds after the B06 loop. ──────
def _scale_baseline_idf_pre_b08b(idf, scale_factor_dict, archetype_id=None):
    planar_k = scale_factor_dict["planar_scale_factor"]
    area_s = scale_factor_dict["area_scale_ratio"]
    transformer_s = scale_factor_dict.get("transformer_scale_ratio", area_s)

    for cls in layout_assigner._GEOMETRY_SURFACE_CLASSES:
        for surf in idf.idfobjects.get(cls, []):
            scaled_coords = [(x * planar_k, y * planar_k, z) for x, y, z in surf.coords]
            surf.setcoords(scaled_coords)

    for z in idf.idfobjects.get("ZONE", []):
        x0, y0 = z.X_Origin, z.Y_Origin
        if not layout_assigner._is_blank_or_autosize(x0):
            z.X_Origin = float(x0) * planar_k
        if not layout_assigner._is_blank_or_autosize(y0):
            z.Y_Origin = float(y0) * planar_k

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

    for obj in idf.idfobjects.get("ELECTRICLOADCENTER:TRANSFORMER", []):
        val = obj.Rated_Capacity
        if layout_assigner._is_blank_or_autosize(val):
            continue
        obj.Rated_Capacity = float(val) * transformer_s

    for cls, obj_name, value_field, s1_value in layout_assigner._MEASURED_S1_ABSOLUTE_SPECS.get(archetype_id, ()):
        for obj in idf.idfobjects.get(cls, []):
            if str(obj.Name).strip() != obj_name:
                continue
            setattr(obj, value_field, s1_value * area_s)

    # (B08b's new re-centring translation block deliberately OMITTED here --
    # this is the "before" replica.)
    return idf


def _control_differs_check():
    """Build ONE MidriseApartment IDF with each variant and assert the Zone
    Origins actually differ -- E-LA-31 standing rule, must run before any
    energy comparison is trusted."""
    from geomeppy import IDF as GeomIDF
    try:
        GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    except Exception:
        pass

    path = layout_assigner.get_registry().get_baseline_idf("MidriseApartment")
    band_map_idf = GeomIDF(str(path))
    recomputed_area = layout_assigner.compute_band_map(band_map_idf)["recomputed_area_m2"]
    scale = layout_assigner.calculate_scaling_factor(150.0, recomputed_area)

    idf_before = GeomIDF(str(path))
    _scale_baseline_idf_pre_b08b(idf_before, scale, archetype_id="MidriseApartment")
    origins_before = sorted((z.X_Origin, z.Y_Origin) for z in idf_before.idfobjects["ZONE"])

    idf_after = GeomIDF(str(path))
    layout_assigner.scale_baseline_idf(idf_after, scale, archetype_id="MidriseApartment")
    origins_after = sorted((z.X_Origin, z.Y_Origin) for z in idf_after.idfobjects["ZONE"])

    print(f"control-differs check: before[0]={origins_before[0]} after[0]={origins_after[0]}")
    if origins_before == origins_after:
        raise RuntimeError(
            "CONTROL-DIFFERS CHECK FAILED: pre-B08b replica produced IDENTICAL "
            "Zone Origins to the real post-B08b function. The 'before' control "
            "is silently a copy of the 'after' treatment (E-LA-31 pattern) -- "
            "STOP, do not trust any energy delta from this run."
        )
    print("control-differs check PASSED: pre-B08b and post-B08b geometries differ, as expected.")


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
        layout_assigner.scale_baseline_idf = _scale_baseline_idf_pre_b08b
    try:
        bidf = BuildingIDF(row, thermal_mass=True, resolution_mode="layout_assign", trim_outputs=True)
        manifest_row = bidf.build(gdf_sample, schedule_library, build_dir)
    finally:
        layout_assigner.scale_baseline_idf = real_fn
    return manifest_row


def run_one(idf_path: Path, epw_path, run_dir: Path, osm_id: str, floor_area_m2: float):
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
    print("=== control-differs check ===")
    _control_differs_check()

    print("\nLoading base data for nyc_suburban ...")
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

        for before, tag in [(True, "before_B08b"), (False, "after_B08b")]:
            build_dir = SCRATCH_DIR / clean / tag
            (build_dir / "idfs").mkdir(parents=True, exist_ok=True)
            manifest_row = build_one(row, gdf_57, schedule_library, build_dir, before=before)
            if manifest_row["generation_status"] != "success":
                print(f"  [{tag}] BUILD FAILED: {manifest_row['generation_status']}")
                rows.append({"osm_id": osm_id, "archetype_id": arch, "variant": tag,
                             "build_status": manifest_row["generation_status"]})
                continue
            idf_path = Path(manifest_row["idf_path"])
            run_dir = ARC_RESULTS / "b08b_runs" / clean / tag
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
                row_out.update(eui)
            rows.append(row_out)

    elapsed = time.monotonic() - t0
    df = pd.DataFrame(rows)
    out_csv = ARC_RESULTS / "b08b_energy_delta.csv"
    df.to_csv(out_csv, index=False)
    df.to_csv(OUT_DIR / "comparisons" / "b08b_energy_delta.csv", index=False)
    print(f"\nWrote {out_csv} ({elapsed/60:.1f} min total)")

    if "total_eui" in df.columns:
        piv = df.pivot_table(index=["osm_id", "archetype_id"], columns="variant",
                              values="total_eui", aggfunc="first")
        if "before_B08b" in piv.columns and "after_B08b" in piv.columns:
            piv["delta_eui"] = piv["after_B08b"] - piv["before_B08b"]
            piv["delta_pct"] = 100.0 * piv["delta_eui"] / piv["before_B08b"]
            piv_path = ARC_RESULTS / "b08b_energy_delta_pivot.csv"
            piv.to_csv(piv_path)
            print(f"Wrote pivot to {piv_path}")
            print(piv)
    print("DONE")


if __name__ == "__main__":
    main()
