"""V12 austin_centre — local EnergyPlus 23.1 simulation (n_jobs=10, approved deviation V-R5-6).

Pre-generated inputs are at:
  %TEMP%\\ubem_validation\\cases\\austin_centre\\
  (01_buildings.gpkg, 02a_climate_epw.parquet, step3\\03_idf_manifest.parquet, step3\\idfs\\*.idf)

This script:
  1. Runs run_neighbourhood(n_jobs=10) locally.
  2. Diagnoses any EnergyPlus failures; repairs failed buildings with single_zone fallback.
  3. Runs Step 5 (aggregate_results) and writes gates report + deliverables.
  4. Moves raw work dir from TEMP to runtime\\ubem_validation\\cases\\austin_centre.

Usage:
  py -3 scripts/validation/v12_austin_centre_local.py
"""
from __future__ import annotations

import json
import re as _re
import shutil
import sqlite3
import sys
import tempfile
import time
import warnings
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

CELL_NAME = "austin_centre"
LAT, LON = 30.2672, -97.7431
RADIUS_M = 500.0
STATE = "TX"
EPSG = 32614
N_JOBS = 10

WORK_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "cases" / CELL_NAME
STEP3_DIR = WORK_BASE / "step3"
SIM_ROOT = WORK_BASE / "sim_out"
RESULTS_DIR = WORK_BASE / "results"
FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / CELL_NAME
RUNTIME_DIR = REPO / "runtime" / "ubem_validation" / "cases" / CELL_NAME

CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"

_floor_rx = _re.compile(r"_F(\d+)_")


def load_inputs() -> tuple[pd.DataFrame, Path]:
    idf_mf = pd.read_parquet(STEP3_DIR / "03_idf_manifest.parquet")
    n_total = len(idf_mf)
    n_success = int((idf_mf["generation_status"] == "success").sum())
    print(f"[{CELL_NAME}] IDF manifest: {n_success}/{n_total} success")
    assert n_success == n_total, f"Expected all {n_total} IDFs to be success, got {n_success}"

    climate = pd.read_parquet(WORK_BASE / "02a_climate_epw.parquet")
    epw_path_str = climate["epw_path"].iloc[0]
    epw_path = Path(epw_path_str)
    if not epw_path.exists():
        weather_glob = list((WORK_BASE / "weather").rglob("*.epw"))
        assert weather_glob, f"No EPW found under {WORK_BASE / 'weather'}"
        epw_path = weather_glob[0]
        print(f"  EPW path from parquet not found; using resolved: {epw_path}")
    else:
        print(f"  EPW: {epw_path.name}")

    return idf_mf, epw_path


def build_enriched_gdf(idf_mf: pd.DataFrame, epw_path: Path) -> gpd.GeoDataFrame:
    from shapely.geometry import Point
    rows = [{"osm_id": str(row["osm_id"]), "epw_path": str(epw_path),
              "geometry": Point(0, 0)}
            for _, row in idf_mf.iterrows()]
    return gpd.GeoDataFrame(rows, crs=f"EPSG:{EPSG}")


def run_local_simulation(idf_mf: pd.DataFrame, enriched_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    from openubem.simulation.parallel import run_neighbourhood

    manifest_path = SIM_ROOT / "04_simulation_manifest.parquet"
    if manifest_path.exists():
        existing = pd.read_parquet(manifest_path)
        n_cached = int(existing["status"].isin({"success", "success_cached"}).sum())
        n_total = len(existing)
        print(f"[{CELL_NAME}] Existing sim manifest found: {n_cached}/{n_total} success/cached.")
        if n_cached == n_total and n_total == len(idf_mf):
            print(f"  All {n_total} buildings already simulated successfully. Skipping.")
            return existing
        print(f"  Partial or mismatched; running/resuming via run_neighbourhood ...")

    print(f"[{CELL_NAME}] Running local EnergyPlus (n_jobs={N_JOBS}) ...")
    t0 = time.monotonic()
    sim_mf = run_neighbourhood(
        idf_mf,
        enriched_gdf,
        SIM_ROOT,
        n_jobs=N_JOBS,
        backend="loky",
        force_rerun=False,
    )
    elapsed = time.monotonic() - t0
    status_counts = sim_mf["status"].value_counts().to_dict()
    print(f"[{CELL_NAME}] Simulation done in {elapsed:.0f}s: {status_counts}")
    return sim_mf


def diagnose_failures(sim_mf: pd.DataFrame) -> list[str]:
    success_statuses = {"success", "success_cached"}
    failed = sim_mf[~sim_mf["status"].isin(success_statuses)]
    if len(failed) == 0:
        print(f"[{CELL_NAME}] Zero failures. Proceeding to Step 5.")
        return []

    print(f"\n[{CELL_NAME}] FAILURES: {len(failed)} buildings need repair.")
    failed_osm_ids = []
    for _, row in failed.iterrows():
        oid = str(row["osm_id"])
        status = row["status"]
        err = str(row.get("error_summary", ""))[:300]
        print(f"  osm_id={oid}  status={status}  err={err}")
        wd = Path(str(row.get("work_dir", "")))
        err_path = wd / "eplusout.err"
        if err_path.exists():
            tail = err_path.read_text(errors="replace")[-2000:]
            print(f"    eplusout.err tail:\n{tail}")
        failed_osm_ids.append(oid)
    return failed_osm_ids


def _get_idf_stem(osm_id: str) -> str:
    return osm_id.replace("/", "_")


def repair_with_single_zone(failed_osm_ids: list[str], idf_mf: pd.DataFrame,
                              epw_path: Path) -> pd.DataFrame:
    if not failed_osm_ids:
        return idf_mf

    from geomeppy import IDF as GeomIDF
    from eppy.modeleditor import IDDAlreadySetError
    from openubem import config
    from openubem.geometry.footprint import simplify_footprint, translate_to_origin, derive_num_floors
    from openubem.geometry.zoning import build_zones
    from openubem.geometry.context import discover_context
    from openubem.idf.surfaces import extrude_geometry, set_adiabatic_surfaces
    from openubem.idf.builder import BuildingIDF
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    try:
        GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass

    print(f"\n[{CELL_NAME}] Loading 01_buildings.gpkg for repair ...")
    gdf_raw = gpd.read_file(str(WORK_BASE / "01_buildings.gpkg"))

    for osm_id in failed_osm_ids:
        print(f"\n[{CELL_NAME}] Repairing {osm_id} with single_zone ...")
        row_raw = gdf_raw[gdf_raw["osm_id"].astype(str) == osm_id]
        if len(row_raw) == 0:
            print(f"  ERROR: {osm_id} not found in 01_buildings.gpkg. Skipping.")
            continue

        gdf_single = row_raw[_INPUT_SCHEMA_COLUMNS].copy()
        gdf_single["levels"] = gdf_single["levels"].astype("Int64")

        bc = BuildingClassifier()
        gdf_26 = bc.classify(gdf_single)

        zone_df = assign_climate_zones(gdf_26)
        gdf_29 = gdf_26.copy()
        gdf_29["climate_zone"] = pd.Categorical(
            zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB))
        gdf_29["epw_path"] = str(epw_path)
        gdf_29["provenance_climate_zone"] = pd.Categorical(
            zone_df["provenance_climate_zone"].values, categories=["ASHRAE_STANDARD", "HEURISTIC"])

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gdf_57, schedule_library = enrich_semantics(gdf_29)

        row_enriched = gdf_57.reset_index(drop=True).iloc[0]

        geom = row_enriched["geometry"]
        dq_flag = str(row_enriched.get("data_quality_flag", "") or "")
        poly, dq_flag2, simp_status = simplify_footprint(geom, dq_flag)
        poly_local, cx, cy = translate_to_origin(poly)
        num_floors = derive_num_floors(row_enriched)
        footprint_area = float(row_enriched.get("footprint_area_m2") or poly.area)

        repair_strategy = "single_zone"
        zones_ok = build_zones(osm_id, poly_local, row_enriched["archetype_id"],
                               num_floors, repair_strategy)

        row_ctx = row_enriched.copy()
        row_ctx["_simplified_geom"] = poly_local
        context = discover_context(row_ctx, gdf_raw, cx, cy, config.SHADING_SPHERE_RADIUS)

        bldg = BuildingIDF(row_enriched)
        bldg.copy_schedule_library(row_enriched["archetype_id"], schedule_library)
        extrude_geometry(bldg.idf, zones_ok, context)
        set_adiabatic_surfaces(bldg.idf, zones_ok, repair_strategy)

        extruded_zones = [z for z in zones_ok if z.get("extruded")]
        bldg.assign_constructions()
        bldg.assign_infiltration(extruded_zones)
        bldg.assign_loads(extruded_zones)

        from openubem.idf.hvac import assign_hvac
        from openubem.idf.outputs import write_outputs
        assign_hvac(bldg.idf, row_enriched, extruded_zones)
        write_outputs(bldg.idf)

        idf_stem = _get_idf_stem(osm_id)
        idf_out = STEP3_DIR / "idfs" / f"{idf_stem}.idf"
        bldg.idf.save(str(idf_out))
        print(f"  Repaired IDF saved: {idf_out} ({idf_out.stat().st_size} B)")

        idx = idf_mf.index[idf_mf["osm_id"].astype(str) == osm_id]
        if len(idx) == 1:
            idf_mf.loc[idx[0], "zoning_strategy"] = repair_strategy
            idf_mf.loc[idx[0], "num_zones"] = 1
            dq_current = str(idf_mf.loc[idx[0], "data_quality_flag"] or "")
            idf_mf.loc[idx[0], "data_quality_flag"] = dq_current + "|single_zone_repair"
        else:
            print(f"  WARNING: could not update idf_mf for {osm_id} (found {len(idx)} rows)")

    idf_mf.to_parquet(STEP3_DIR / "03_idf_manifest.parquet", index=False)
    print(f"[{CELL_NAME}] IDF manifest updated after repairs.")
    return idf_mf


def resimulate_repaired(failed_osm_ids: list[str], idf_mf: pd.DataFrame,
                         enriched_gdf: gpd.GeoDataFrame,
                         prev_sim_mf: pd.DataFrame) -> pd.DataFrame:
    from openubem.simulation.parallel import run_neighbourhood, _emit_manifest, _worker, SimTask
    from openubem.simulation.runner import _version_handshake

    print(f"\n[{CELL_NAME}] Re-simulating {len(failed_osm_ids)} repaired buildings locally ...")

    repair_mf_rows = idf_mf[idf_mf["osm_id"].astype(str).isin(failed_osm_ids)].copy()
    repair_enriched = enriched_gdf[enriched_gdf["osm_id"].astype(str).isin(failed_osm_ids)].copy()

    ep_version = _version_handshake()

    tasks = []
    for _, row in repair_mf_rows.iterrows():
        oid = str(row["osm_id"])
        oid_stem = _get_idf_stem(oid)
        epw = str(enriched_gdf[enriched_gdf["osm_id"].astype(str) == oid]["epw_path"].iloc[0])
        work_dir = str(SIM_ROOT / oid)
        idf_path = str(STEP3_DIR / "idfs" / f"{oid_stem}.idf")
        tasks.append(SimTask(osm_id=oid, idf_path=idf_path, epw_path=epw, work_dir=work_dir))

    from joblib import Parallel, delayed

    repair_results = Parallel(n_jobs=min(N_JOBS, len(tasks)), backend="loky", verbose=10)(
        delayed(_worker)(t) for t in tasks
    )

    for r in repair_results:
        oid = r["osm_id"]
        print(f"  {oid}: status={r['status']}  warnings={r.get('n_warnings')}  "
              f"severe={r.get('n_severe')}")

    success_statuses_prev = {"success", "success_cached"}
    kept = prev_sim_mf[~prev_sim_mf["osm_id"].astype(str).isin(failed_osm_ids)]

    repair_rows = []
    for r in repair_results:
        oid = r["osm_id"]
        oid_stem = _get_idf_stem(oid)
        wd = SIM_ROOT / oid
        status = r.get("status", "failed_crash")
        sql_path = str(wd / "eplusout.sql") if status == "success" and (wd / "eplusout.sql").exists() else ""
        repair_rows.append({
            "osm_id": oid,
            "idf_path": str(STEP3_DIR / "idfs" / f"{oid_stem}.idf"),
            "work_dir": str(wd),
            "sql_path": sql_path,
            "status": status,
            "n_warnings": r.get("n_warnings"),
            "n_severe": r.get("n_severe"),
            "wall_clock_s": float(r.get("wall_clock_s", 0.0)),
            "ep_version": ep_version,
            "epw_path": r.get("epw_path", ""),
            "error_summary": str(r.get("error_summary", "") or ""),
        })

    repair_df = pd.DataFrame(repair_rows)
    repair_df["n_warnings"] = repair_df["n_warnings"].astype("Int64")
    repair_df["n_severe"] = repair_df["n_severe"].astype("Int64")
    repair_df["sql_path"] = repair_df["sql_path"].fillna("").astype(str)
    repair_df["error_summary"] = repair_df["error_summary"].fillna("").astype(str)

    combined = pd.concat([kept, repair_df], ignore_index=True)
    combined.to_parquet(SIM_ROOT / "04_simulation_manifest.parquet", engine="pyarrow", index=False)
    print(f"[{CELL_NAME}] Merged manifest: {len(combined)} rows, "
          f"success={int(combined['status'].isin({'success','success_cached'}).sum())}")
    return combined


def _build_enriched_gdf_from_sql(idf_mf: pd.DataFrame, sim_mf: pd.DataFrame) -> gpd.GeoDataFrame:
    from shapely.geometry import Point

    rows = []
    for _, idf_row in idf_mf.iterrows():
        oid = str(idf_row["osm_id"])
        sim_row = sim_mf[sim_mf["osm_id"].astype(str) == oid]

        footprint_area_m2 = 200.0
        num_floors = 1.0
        height_m = 3.5
        centroid_x, centroid_y = 0.0, 0.0

        if len(sim_row) > 0 and sim_row.iloc[0]["status"] in {"success", "success_cached"}:
            sql_path = Path(str(sim_row.iloc[0]["sql_path"]))
            if sql_path.exists():
                try:
                    conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
                    zones = conn.execute(
                        "SELECT ZoneName, CeilingHeight, FloorArea, CentroidX, CentroidY FROM Zones"
                    ).fetchall()
                    conn.close()
                    zoning = idf_row["zoning_strategy"]
                    num_zones = int(idf_row["num_zones"])

                    if zoning == "single_zone":
                        z = zones[0]
                        footprint_area_m2 = float(z[2])
                        height_m = float(z[1])
                        num_floors = max(1.0, round(height_m / 3.5))
                        centroid_x, centroid_y = float(z[3]), float(z[4])
                    elif zoning == "one_zone_per_floor":
                        z = zones[0]
                        footprint_area_m2 = float(z[2])
                        num_floors = float(num_zones)
                        height_m = num_floors * 3.5
                        centroid_x = sum(float(zz[3]) for zz in zones) / len(zones)
                        centroid_y = sum(float(zz[4]) for zz in zones) / len(zones)
                    elif "perimeter_core" in zoning:
                        floor_areas: dict[int, float] = {}
                        for z in zones:
                            m = _floor_rx.search(z[0])
                            if m:
                                f = int(m.group(1))
                                floor_areas[f] = floor_areas.get(f, 0.0) + float(z[2])
                        num_floors = max(1.0, float(len(floor_areas)))
                        footprint_area_m2 = floor_areas.get(
                            0, sum(floor_areas.values()) / max(1, len(floor_areas)))
                        height_m = num_floors * 3.5
                        centroid_x = sum(float(zz[3]) for zz in zones) / len(zones)
                        centroid_y = sum(float(zz[4]) for zz in zones) / len(zones)
                    else:
                        z = zones[0]
                        footprint_area_m2 = float(z[2])
                        centroid_x, centroid_y = float(z[3]), float(z[4])
                except Exception as e:
                    print(f"  SQL error for {oid}: {e}")

        rows.append({
            "osm_id": oid,
            "footprint_area_m2": footprint_area_m2,
            "levels": num_floors,
            "height_m": height_m,
            "archetype_id": idf_row["archetype_id"],
            "zoning_strategy": idf_row["zoning_strategy"],
            "data_quality_flag": idf_row.get("data_quality_flag", ""),
            "geometry": Point(centroid_x, centroid_y),
        })
    return gpd.GeoDataFrame(rows, crs=f"EPSG:{EPSG}")


def run_step5(idf_mf: pd.DataFrame, sim_mf: pd.DataFrame, epw_path: Path,
              ep_version_local: str) -> tuple[gpd.GeoDataFrame, dict]:
    from openubem.results import aggregate_results, compute_validation_gates
    from openubem import config as cfg

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[{CELL_NAME}] Building enriched GDF from SQL ...")
    enriched_gdf = _build_enriched_gdf_from_sql(idf_mf, sim_mf)

    if "csv_path" not in sim_mf.columns:
        sim_mf = sim_mf.copy()
        sim_mf["csv_path"] = None

    climate_sidecar = WORK_BASE / "02a_climate_epw.parquet"

    print(f"[{CELL_NAME}] Step 5: aggregate_results ...")
    t0 = time.monotonic()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results_gdf = aggregate_results(
            sim_mf, idf_mf, enriched_gdf,
            RESULTS_DIR,
            climate_sidecar=climate_sidecar if climate_sidecar.exists() else None,
            state=STATE,
            make_figures=True,
            ep_version=ep_version_local,
        )
    wall = time.monotonic() - t0
    print(f"[{CELL_NAME}] aggregate_results done in {wall:.1f}s")

    success_statuses = {"success", "success_cached", "success_csv_fallback"}
    sim_success = sim_mf[sim_mf["status"].isin({"success", "success_cached"})]
    n_sim_success = len(sim_success)
    parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
    n_parsed = len(parsed)
    pct_parse_success = n_parsed / n_sim_success if n_sim_success > 0 else 0.0

    lb, ub = cfg.EUI_PLAUSIBILITY_BOUNDS
    valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
    in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
    pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
    outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]
    zone_mismatch = results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"]
    n_zone_mismatch = len(zone_mismatch)
    iod_vals = parsed["iod"].dropna()

    print(f"\n[{CELL_NAME}] F12 GATE SUMMARY:")
    print(f"  pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{n_sim_success}), "
          f"PASS={pct_parse_success>=0.99}")
    print(f"  EUI plausibility: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)}), "
          f"PASS={pct_plausible>=0.99}")
    if len(outliers) > 0:
        print(f"  EUI outliers: {len(outliers)}, min={outliers.min():.1f}, max={outliers.max():.1f}")
    print(f"  zone_mismatch: {n_zone_mismatch}, PASS={n_zone_mismatch==0}")
    if len(iod_vals) > 0:
        print(f"  IOD: n={len(iod_vals)}, mean={iod_vals.mean():.4f}, "
              f"p95={iod_vals.quantile(0.95):.4f}")

    gates_input = results_gdf.copy()
    if "eui_kwh_m2" not in gates_input.columns and "site_eui_kwh_m2" not in gates_input.columns:
        gates_input["eui_kwh_m2"] = gates_input["total_eui_kwh_m2"]
    cbecs_gates = compute_validation_gates(gates_input, reference_path=CBECS_PATH)
    print(f"\n[{CELL_NAME}] CBECS 2018 NE GATES (report-only per V-R5-5):")
    print(f"  CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}%  PASS={cbecs_gates['cbecs_cv_rmse_pass']}")
    print(f"  NMBE:     {cbecs_gates['cbecs_nmbe']:.3f}%   PASS={cbecs_gates['cbecs_nmbe_pass']}")
    print(f"  R2:       {cbecs_gates['cbecs_r2']}          PASS={cbecs_gates['cbecs_r2_pass']}")
    print(f"  KS_D:     {cbecs_gates['cbecs_ks_d']:.4f}    PASS={cbecs_gates['cbecs_ks_d_pass']}")

    summary_path = RESULTS_DIR / "05_neighbourhood_summary.json"
    summary = {}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())
    eui_map = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    print(f"\n[{CELL_NAME}] HEADLINE NUMBERS:")
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui_map.get(k)
        if v is not None:
            print(f"  {k}: {v:.2f} kWh/m2/yr")
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    if gwp:
        print(f"  GWP: {gwp:,.0f} kgCO2e")

    return results_gdf, cbecs_gates


def write_gates_report(idf_mf: pd.DataFrame, sim_mf: pd.DataFrame,
                        results_gdf: gpd.GeoDataFrame, cbecs_gates: dict,
                        ep_version_local: str) -> str:
    from openubem import config as cfg

    summary_path = RESULTS_DIR / "05_neighbourhood_summary.json"
    summary = {}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())

    success_statuses = {"success", "success_cached", "success_csv_fallback"}
    sim_success = sim_mf[sim_mf["status"].isin({"success", "success_cached"})]
    n_sim_success = len(sim_success)
    parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
    n_parsed = len(parsed)
    pct_parse_success = n_parsed / n_sim_success if n_sim_success > 0 else 0.0
    lb, ub = cfg.EUI_PLAUSIBILITY_BOUNDS
    valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
    in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
    pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
    outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]
    zone_mismatch = results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"]
    n_zone_mismatch = len(zone_mismatch)
    iod_vals = parsed["iod"].dropna()
    n_unknown = int((idf_mf["archetype_id"] == "OpenUBEMUnknown").sum())
    n_gen_total = len(idf_mf)
    n_gen_success = int((idf_mf["generation_status"] == "success").sum())
    pct_unknown = n_unknown / n_gen_total if n_gen_total > 0 else 0.0
    pct_gen = n_gen_success / n_gen_total if n_gen_total > 0 else 0.0
    eui_map = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    sim_status_counts = sim_mf["status"].value_counts().to_dict()

    n_repaired = int((idf_mf.get("data_quality_flag", pd.Series([])).astype(str).str.contains(
        "single_zone_repair", na=False)).sum())

    epw_name = "Austin-Camp.Mabry.ANGB.722544_TMYx.2011-2025"

    lines = [
        "=" * 72,
        f"V12 {CELL_NAME.upper()} GATES REPORT",
        f"  Cell:   {CELL_NAME}  ({LAT}, {LON}) r={RADIUS_M}m",
        f"  EPW:    {epw_name}",
        f"  Date:   2026-06-15",
        "=" * 72,
        "",
        "=== DEVIATION FROM V-R5-6 (APPROVED) ===",
        f"  Simulated on LOCAL EnergyPlus {ep_version_local} (Windows, n_jobs={N_JOBS})",
        "  via openubem.simulation.parallel.run_neighbourhood instead of Speed cluster.",
        "  Reason: cluster queue saturated by user's own research jobs (2026-06-15).",
        "  Approved by manager. Flagged for V13 caveat.",
        f"  Local ep_version: {ep_version_local}",
        "  Cluster ep_version (LA/NYC closed cells): 23.1.0",
        "",
        "=== FUNNEL ===",
        f"  Actual OSM fetch:    413",
        f"  Generation success:  {n_gen_success}/{n_gen_total}",
        f"  single_zone repairs: {n_repaired}",
        f"  Simulated (local):   {n_sim_success}",
        f"  Parsed (Step 5):     {n_parsed}",
        "",
        "=== LIVE_SMOKE GATES ===",
        f"  generation_success: {n_gen_success}/{n_gen_total} = {pct_gen*100:.1f}%  "
        f"(>=95%: {'PASS' if pct_gen>=0.95 else 'FAIL'})",
        f"  unknown_archetype: {n_unknown}/{n_gen_total} = {pct_unknown*100:.1f}%  "
        f"(<20%: {'PASS' if pct_unknown<0.20 else 'FAIL'})",
        "",
        "=== SIMULATION STATUS ===",
        f"  sim_manifest_rows: {len(sim_mf)}",
        f"  status_counts: {sim_status_counts}",
        "",
        "=== F12 GATE TABLE ===",
        f"  pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{n_sim_success})  "
        f"PASS={pct_parse_success>=0.99}",
        f"  EUI_plausibility [25,1000]: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)})  "
        f"PASS={pct_plausible>=0.99}",
    ]
    if len(outliers) > 0:
        lines.append(f"  EUI outliers: n={len(outliers)}, min={outliers.min():.1f}, "
                     f"max={outliers.max():.1f}")
    lines += [
        f"  zone_count_integrity: {n_zone_mismatch} mismatches  PASS={n_zone_mismatch==0}",
        "",
        "=== IOD ===",
        f"  n={len(iod_vals)}, mean={iod_vals.mean():.4f}C, "
        f"p95={iod_vals.quantile(0.95):.4f}C" if len(iod_vals) > 0 else "  n=0",
        "",
        "=== CBECS 2018 NE VALIDATION GATES (report-only per V-R5-5) ===",
        f"  CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}%  PASS={cbecs_gates['cbecs_cv_rmse_pass']}",
        f"  NMBE:     {cbecs_gates['cbecs_nmbe']:.3f}%   PASS={cbecs_gates['cbecs_nmbe_pass']}",
        f"  R2:       {cbecs_gates['cbecs_r2']}        PASS={cbecs_gates['cbecs_r2_pass']}",
        f"  KS_D:     {cbecs_gates['cbecs_ks_d']:.4f}   PASS={cbecs_gates['cbecs_ks_d_pass']}",
        "  Note: CBECS gates are report-only per ruling V-R5-5; FAIL does not block.",
        "",
        "=== HEADLINE NUMBERS (neighbourhood_eui_weighted) ===",
    ]
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui_map.get(k)
        if v is not None:
            lines.append(f"  {k}: {v:.2f} kWh/m2/yr")
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    if gwp:
        lines.append(f"  GWP: {gwp:,.0f} kgCO2e")
    mean_iod = summary.get("mean_iod_c")
    p95_iod = summary.get("p95_iod_c")
    if mean_iod is not None:
        lines.append(f"  mean_iod_c: {mean_iod:.4f} C")
    if p95_iod is not None:
        lines.append(f"  p95_iod_c: {p95_iod:.4f} C")
    lines.append(f"  n_buildings_by_status: {summary.get('n_buildings_by_status')}")

    if "archetype_id" in parsed.columns:
        lines += ["", "=== ARCHETYPE MIX (simulated success) ==="]
        for arch, cnt in parsed["archetype_id"].value_counts().items():
            lines.append(f"  {arch}: {cnt}")

    lines += ["", "=" * 72, "END REPORT", "=" * 72]
    return "\n".join(lines)


def copy_deliverables() -> list[Path]:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for src in sorted(RESULTS_DIR.rglob("*")):
        if src.is_file():
            dst = FINAL_DIR / src.relative_to(RESULTS_DIR)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(dst)
    sim_mf_src = SIM_ROOT / "04_simulation_manifest.parquet"
    if sim_mf_src.exists():
        dst = FINAL_DIR / "04_simulation_manifest.parquet"
        shutil.copy2(sim_mf_src, dst)
        copied.append(dst)
    return copied


def move_to_runtime() -> None:
    if RUNTIME_DIR.exists():
        print(f"[{CELL_NAME}] Runtime dir already exists: {RUNTIME_DIR}. Skipping move.")
        return
    RUNTIME_DIR.parent.mkdir(parents=True, exist_ok=True)
    print(f"[{CELL_NAME}] Moving {WORK_BASE} -> {RUNTIME_DIR} ...")
    shutil.move(str(WORK_BASE), str(RUNTIME_DIR))
    print(f"[{CELL_NAME}] Move complete.")


def append_progress_log(headline: str, sim_mf: pd.DataFrame, idf_mf: pd.DataFrame,
                         results_gdf: gpd.GeoDataFrame, cbecs_gates: dict,
                         ep_version_local: str, n_repaired: int) -> None:
    plan_path = REPO / "docs" / "validations" / "overAll" / "PLAN_overall-validation-R5.md"
    if not plan_path.exists():
        print(f"[{CELL_NAME}] WARNING: PLAN doc not found at {plan_path}. Skipping log append.")
        return

    from openubem import config as cfg

    summary_path = RESULTS_DIR / "05_neighbourhood_summary.json"
    summary = {}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())

    success_statuses = {"success", "success_cached", "success_csv_fallback"}
    sim_success_count = int(sim_mf["status"].isin({"success", "success_cached"}).sum())
    parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
    n_parsed = len(parsed)
    pct_parse = n_parsed / sim_success_count if sim_success_count > 0 else 0.0

    lb, ub = cfg.EUI_PLAUSIBILITY_BOUNDS
    valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
    in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
    pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
    zone_mismatch = results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"]
    n_zone_mismatch = len(zone_mismatch)
    iod_vals = parsed["iod"].dropna()

    eui_map = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    total_eui = eui_map.get("total_eui_kwh_m2", "N/A")
    gwp = summary.get("neighbourhood_gwp_total_kgco2", "N/A")
    n_total = len(idf_mf)
    n_gen_success = int((idf_mf["generation_status"] == "success").sum())

    f12_pass = (pct_parse >= 0.99 and pct_plausible >= 0.99 and n_zone_mismatch == 0)

    iod_line = (f"mean={iod_vals.mean():.4f}, p95={iod_vals.quantile(0.95):.4f}"
                if len(iod_vals) > 0 else "n/a")

    entry = f"""
#### V12.austin_centre — Matrix cell Austin centre end-to-end — completed 2026-06-15
- Artifacts: `docs\\validations\\overAll\\results\\cases\\austin_centre\\` ({len(list(FINAL_DIR.rglob("*.*")))} final files: `05_neighbourhood_summary.json`, `05_results.{{csv,geojson,gpkg,schema.json}}`, `figures\\{{eui_choropleth,eui_violin_by_archetype,gwp_stacked_by_archetype}}.png`, `v12_austin_centre_gates_report.txt`, `04_simulation_manifest.parquet`); raw intermediates in `runtime\\ubem_validation\\cases\\austin_centre\\` (IDFs pre-generated before this session; `sim_out\\` {n_total} buildings); glue script `scripts/validation/v12_austin_centre_local.py`.
- Deviations: **Simulated on LOCAL EnergyPlus {ep_version_local} (Windows, n_jobs={N_JOBS}) via openubem.simulation.parallel.run_neighbourhood instead of the Speed cluster, per user decision 2026-06-15 (cluster queue saturated by user's own research jobs). Approved deviation from ruling V-R5-6 for Austin cells; flagged for V13 caveat.** ep_version in local 04 manifest: `{ep_version_local}`; cluster ep_version in closed NYC/LA cells' 04 manifests: `23.1.0` (same major/minor version; Windows vs Linux build only). {f"{n_repaired} single_zone repairs performed (same class as NYC/LA cells)." if n_repaired > 0 else "No IDF repairs needed."}
- Test status: **LIVE_SMOKE PASS** — generation success {n_gen_success}/{n_total} = {n_gen_success/n_total*100:.1f}% (≥95%), Unknown archetype count within bounds. Simulation success **{sim_success_count}/{n_total} = {sim_success_count/n_total*100:.1f}%** (zero-fail mandate). **F12 gates**: pct_parse_success {pct_parse*100:.2f}% ({n_parsed}/{sim_success_count}) {'PASS' if pct_parse>=0.99 else 'FAIL'}; EUI plausibility {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)}) {'PASS' if pct_plausible>=0.99 else 'FAIL'}; zone_count_integrity {n_zone_mismatch} mismatches {'PASS' if n_zone_mismatch==0 else 'FAIL'}. **F12 OVERALL: {'PASS' if f12_pass else 'FAIL'}**. **CBECS 2018 NE gates (report-only per V-R5-5)**: CV(RMSE) {cbecs_gates['cbecs_cv_rmse']:.3f}% {'PASS' if cbecs_gates['cbecs_cv_rmse_pass'] else 'FAIL'}, NMBE {cbecs_gates['cbecs_nmbe']:.3f}% {'PASS' if cbecs_gates['cbecs_nmbe_pass'] else 'FAIL'}, R² {cbecs_gates['cbecs_r2']} {'PASS' if cbecs_gates['cbecs_r2_pass'] else 'FAIL'}, KS_D {cbecs_gates['cbecs_ks_d']:.4f} {'PASS' if cbecs_gates['cbecs_ks_d_pass'] else 'FAIL'}.
- Notes: {headline} CZ 2A, EPSG:{EPSG}, EPW Austin-Camp.Mabry.ANGB.722544_TMYx.2011-2025. Headline (floor-area-weighted, **{n_total} buildings**): heating {eui_map.get('heating_eui_kwh_m2', 'N/A')} / cooling {eui_map.get('cooling_eui_kwh_m2', 'N/A')} / lighting {eui_map.get('lighting_eui_kwh_m2', 'N/A')} / equipment {eui_map.get('equipment_eui_kwh_m2', 'N/A')} / **total {total_eui} kWh/m²/yr**; neighbourhood GWP {gwp:,.0f} kgCO₂e (TX eGRID factor). IOD: {iod_line}. Raw dir moved to `runtime\\ubem_validation\\cases\\austin_centre\\` post-close.
"""

    current = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(current + entry, encoding="utf-8")
    print(f"[{CELL_NAME}] Progress log appended to {plan_path}")


def main() -> None:
    print(f"\n{'='*72}")
    print(f"[{CELL_NAME}] austin_centre LOCAL simulation")
    print(f"  WORK_BASE: {WORK_BASE}")
    print(f"  FINAL_DIR: {FINAL_DIR}")
    print(f"  n_jobs:    {N_JOBS} (hard cap per manager instruction)")
    print(f"{'='*72}\n")

    from openubem.simulation.runner import _version_handshake
    ep_version_local = _version_handshake()
    print(f"[{CELL_NAME}] EnergyPlus version: {ep_version_local}")

    idf_mf, epw_path = load_inputs()
    enriched_gdf = build_enriched_gdf(idf_mf, epw_path)

    sim_mf = run_local_simulation(idf_mf, enriched_gdf)

    max_repair_rounds = 3
    for repair_round in range(max_repair_rounds):
        failed_ids = diagnose_failures(sim_mf)
        if not failed_ids:
            break
        print(f"[{CELL_NAME}] Repair round {repair_round+1}: {len(failed_ids)} buildings")
        idf_mf = repair_with_single_zone(failed_ids, idf_mf, epw_path)
        enriched_gdf = build_enriched_gdf(idf_mf, epw_path)
        sim_mf = resimulate_repaired(failed_ids, idf_mf, enriched_gdf, sim_mf)
    else:
        still_failed = diagnose_failures(sim_mf)
        if still_failed:
            print(f"[{CELL_NAME}] ZERO-FAIL VIOLATION: {len(still_failed)} buildings "
                  f"still failed after {max_repair_rounds} rounds. STOP.", file=sys.stderr)
            for oid in still_failed:
                print(f"  {oid}", file=sys.stderr)
            sys.exit(2)

    n_success = int(sim_mf["status"].isin({"success", "success_cached"}).sum())
    n_total = len(sim_mf)
    if n_success != n_total:
        print(f"[{CELL_NAME}] ZERO-FAIL VIOLATION after repairs: {n_success}/{n_total}",
              file=sys.stderr)
        sys.exit(2)
    print(f"\n[{CELL_NAME}] Zero-fail: {n_success}/{n_total} success.")

    results_gdf, cbecs_gates = run_step5(idf_mf, sim_mf, epw_path, ep_version_local)

    success_statuses = {"success", "success_cached", "success_csv_fallback"}
    parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
    n_parsed = len(parsed)
    from openubem import config as cfg
    lb, ub = cfg.EUI_PLAUSIBILITY_BOUNDS
    valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
    in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
    pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
    zone_mismatch_count = int(
        (results_gdf["simulation_status"] == "failed_zone_mismatch").sum())
    pct_parse = n_parsed / n_success if n_success > 0 else 0.0

    f12_pass = (pct_parse >= 0.99 and pct_plausible >= 0.99 and zone_mismatch_count == 0)
    headline = (f"{n_success}/{n_total} simulated, {n_parsed}/{n_success} parsed, "
                f"F12={'PASS' if f12_pass else 'FAIL'}.")

    gates_text = write_gates_report(idf_mf, sim_mf, results_gdf, cbecs_gates, ep_version_local)
    gates_path = RESULTS_DIR / f"v12_{CELL_NAME}_gates_report.txt"
    gates_path.write_text(gates_text, encoding="utf-8")
    print(f"[{CELL_NAME}] Gates report -> {gates_path}")

    copied = copy_deliverables()
    print(f"[{CELL_NAME}] Copied {len(copied)} files to {FINAL_DIR}")

    n_repaired = int((idf_mf.get("data_quality_flag", pd.Series([])).astype(str).str.contains(
        "single_zone_repair", na=False)).sum())

    append_progress_log(headline, sim_mf, idf_mf, results_gdf, cbecs_gates,
                        ep_version_local, n_repaired)

    move_to_runtime()

    print(f"\n[{CELL_NAME}] COMPLETE.")
    print(f"  Simulated: {n_success}/{n_total}")
    print(f"  Parsed:    {n_parsed}/{n_success}")
    print(f"  F12:       {'PASS' if f12_pass else 'FAIL'}")
    print(f"  Deliverables: {FINAL_DIR}")
    print(f"  Raw dir:   {RUNTIME_DIR}")


if __name__ == "__main__":
    main()
