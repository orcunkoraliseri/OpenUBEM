"""Run Step 5 only for la_suburban — sim_out already populated after repair1.

Call after v12_la_suburban_repair1.py completes and 04_simulation_manifest.parquet
is all-success (1343/1343).
"""
from __future__ import annotations

import json
import re as _re
import shutil
import sqlite3
import sys
import warnings
from pathlib import Path
import tempfile

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"
CELL_NAME = "la_suburban"
WORK_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "cases" / CELL_NAME
STEP3_DIR = WORK_BASE / "step3"
SIM_OUT_DIR = WORK_BASE / "sim_out"
FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / CELL_NAME

LAT, LON = 33.8359, -118.3406
STATE = "CA"
EPSG = 32611
MAIN_JOB_ID = "965462"
REPAIR1_JOB_ID = "REPAIR1_JOB"  # set at runtime
EPW_STATION = "Torrance.Muni.AP-Zamperini.Field"

_floor_rx = _re.compile(r"_F(\d+)_")


def build_enriched_gdf(idf_mf: pd.DataFrame, sim_mf: pd.DataFrame) -> gpd.GeoDataFrame:
    rows = []
    for _, idf_row in idf_mf.iterrows():
        osm_id = str(idf_row["osm_id"])
        osm_id_norm = osm_id.replace("_", "/", 1) if "_" in osm_id and "/" not in osm_id else osm_id
        sim_row = sim_mf[sim_mf["osm_id"].astype(str) == osm_id_norm]

        footprint_area_m2 = 200.0
        num_floors = 1.0
        height_m = 3.5
        centroid_x, centroid_y = 0.0, 0.0

        if len(sim_row) > 0 and sim_row.iloc[0]["status"] == "success":
            sql_p = Path(str(sim_row.iloc[0]["sql_path"]))
            if sql_p.exists():
                try:
                    conn = sqlite3.connect(f"file:{sql_p}?mode=ro", uri=True)
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
                            0, sum(floor_areas.values()) / max(1, len(floor_areas))
                        )
                        height_m = num_floors * 3.5
                        centroid_x = sum(float(zz[3]) for zz in zones) / len(zones)
                        centroid_y = sum(float(zz[4]) for zz in zones) / len(zones)
                    else:
                        z = zones[0]
                        footprint_area_m2 = float(z[2])
                        centroid_x, centroid_y = float(z[3]), float(z[4])
                except Exception as e:
                    print(f"  SQL error for {osm_id}: {e}")

        rows.append({
            "osm_id": osm_id_norm,
            "footprint_area_m2": footprint_area_m2,
            "levels": num_floors,
            "height_m": height_m,
            "archetype_id": idf_row["archetype_id"],
            "zoning_strategy": idf_row["zoning_strategy"],
            "data_quality_flag": idf_row.get("data_quality_flag", ""),
            "geometry": Point(centroid_x, centroid_y),
        })
    return gpd.GeoDataFrame(rows, crs=f"EPSG:{EPSG}")


def run_step5(idf_manifest: pd.DataFrame, sim_mf: pd.DataFrame,
              epw_path: Path, repair1_job_id: str) -> None:
    from openubem.results import aggregate_results, compute_validation_gates
    from openubem import config as cfg

    results_dir = WORK_BASE / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"[{CELL_NAME}] Building enriched GDF ({len(idf_manifest)} buildings) ...")
    enriched_gdf = build_enriched_gdf(idf_manifest, sim_mf)

    if "csv_path" not in sim_mf.columns:
        sim_mf = sim_mf.copy()
        sim_mf["csv_path"] = None

    climate_sidecar = WORK_BASE / "02a_climate_epw.parquet"
    print(f"[{CELL_NAME}] Step 5: aggregate_results ...")
    import time
    t0 = time.monotonic()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results_gdf = aggregate_results(
            sim_mf, idf_manifest, enriched_gdf,
            results_dir,
            climate_sidecar=climate_sidecar if climate_sidecar.exists() else None,
            state=STATE,
            make_figures=True,
            ep_version="23.1.0",
        )
    wall = time.monotonic() - t0
    print(f"  aggregate_results done in {wall:.1f}s ({len(results_gdf)} rows)")

    success_statuses = {"success", "success_cached", "success_csv_fallback"}
    sim_success = sim_mf[sim_mf["status"].isin({"success", "success_cached"})]
    n_sim_success = len(sim_success)
    parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
    n_parsed = len(parsed)
    pct_parse = n_parsed / n_sim_success if n_sim_success > 0 else 0.0

    lb, ub = cfg.EUI_PLAUSIBILITY_BOUNDS
    valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
    in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
    pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
    outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]
    zone_mismatch = results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"]
    n_zone_mismatch = len(zone_mismatch)
    iod_vals = parsed["iod"].dropna()

    gates_input = results_gdf.copy()
    if "eui_kwh_m2" not in gates_input.columns and "site_eui_kwh_m2" not in gates_input.columns:
        gates_input["eui_kwh_m2"] = gates_input["total_eui_kwh_m2"]
    cbecs_gates = compute_validation_gates(gates_input, reference_path=CBECS_PATH)

    n_gen = int((idf_manifest["generation_status"] == "success").sum())
    n_total = len(idf_manifest)
    n_unknown = int((idf_manifest["archetype_id"] == "OpenUBEMUnknown").sum())
    pct_gen = n_gen / n_total if n_total > 0 else 0.0

    summary_path = results_dir / "05_neighbourhood_summary.json"
    summary = {}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())

    eui_map = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    mean_iod = summary.get("mean_iod_c")
    p95_iod = summary.get("p95_iod_c")

    print(f"\n[{CELL_NAME}] F12 GATE SUMMARY ({n_parsed}/{n_sim_success}):")
    print(f"  pct_parse_success: {pct_parse*100:.2f}% ({n_parsed}/{n_sim_success}) PASS={pct_parse>=0.99}")
    print(f"  EUI plausibility: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)}) PASS={pct_plausible>=0.99}")
    if len(outliers):
        print(f"  EUI outliers: {len(outliers)}, min={outliers.min():.1f}, max={outliers.max():.1f}")
    print(f"  zone_mismatch: {n_zone_mismatch} PASS={n_zone_mismatch==0}")
    print(f"  IOD: n={len(iod_vals)}, mean={iod_vals.mean():.4f}, p95={iod_vals.quantile(0.95):.4f}")
    print(f"\n[{CELL_NAME}] CBECS 2018 NE VALIDATION GATES (report-only):")
    print(f"  CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}%  PASS={cbecs_gates['cbecs_cv_rmse_pass']}")
    print(f"  NMBE:     {cbecs_gates['cbecs_nmbe']:.3f}%   PASS={cbecs_gates['cbecs_nmbe_pass']}")
    print(f"  R2:       {cbecs_gates['cbecs_r2']}        PASS={cbecs_gates['cbecs_r2_pass']}")
    print(f"  KS_D:     {cbecs_gates['cbecs_ks_d']:.4f}   PASS={cbecs_gates['cbecs_ks_d_pass']}")
    print(f"\n[{CELL_NAME}] HEADLINE NUMBERS:")
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui_map.get(k)
        if v is not None:
            print(f"  {k}: {v:.2f} kWh/m2/yr")
    if gwp:
        print(f"  GWP: {gwp:,.0f} kgCO2e")

    lines = [
        "=" * 72,
        f"V12 {CELL_NAME.upper()} GATES REPORT ({n_parsed}/{n_sim_success} — after repair1 way/442763908)",
        f"  Cell:   {CELL_NAME}  ({LAT}, {LON}) r=500m",
        f"  EPW:    {EPW_STATION}",
        f"  Date:   2026-06-12",
        "=" * 72,
        "",
        "=== FUNNEL ===",
        f"  V10 Overpass probe count (lower bound): 1054",
        f"  Actual OSM fetch:    {n_total}",
        f"  Generation success:  {n_gen}/{n_total}",
        f"  Simulated (cluster): {n_sim_success}",
        f"  Parsed (Step 5):     {n_parsed}",
        "",
        "=== LIVE_SMOKE GATES ===",
        f"  generation_success: {n_gen}/{n_total} = {pct_gen*100:.1f}%  (>=95%: {'PASS' if pct_gen>=0.95 else 'FAIL'})",
        f"  unknown_archetype: {n_unknown}/{n_total} = {(n_unknown/n_total)*100:.1f}%  (<20%: {'PASS' if n_unknown/n_total<0.20 else 'FAIL'})",
        "",
        "=== SIMULATION STATUS ===",
        f"  cluster_job_ids: {MAIN_JOB_ID} (main, 1342 COMPLETED + 1 FAILED) + {repair1_job_id} (repair1, 1/1)",
        f"  sim_manifest_rows: {len(sim_mf)}",
        f"  status_counts: {sim_mf['status'].value_counts().to_dict()}",
        "",
        "=== REPAIR RECORD ===",
        f"  way/442763908: perimeter_core 38-zone vertex size mismatch (6 vs 7 vertices) -> single_zone, job {repair1_job_id}_1, 0 Severe",
        "",
        "=== F12 GATE TABLE ===",
        f"  pct_parse_success: {pct_parse*100:.2f}% ({n_parsed}/{n_sim_success})  PASS={pct_parse>=0.99}",
        f"  EUI_plausibility [25,1000]: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)})  PASS={pct_plausible>=0.99}",
    ]
    if len(outliers):
        lines.append(f"  EUI outliers: n={len(outliers)}, min={outliers.min():.1f}, max={outliers.max():.1f}")
    lines += [
        f"  zone_count_integrity: {n_zone_mismatch} mismatches  PASS={n_zone_mismatch==0}",
        "",
        "=== IOD ===",
        f"  n={len(iod_vals)}, mean={iod_vals.mean():.4f}C, p95={iod_vals.quantile(0.95):.4f}C",
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
    if gwp:
        lines.append(f"  GWP: {gwp:,.0f} kgCO2e")
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
    report = "\n".join(lines)

    report_path = results_dir / f"v12_{CELL_NAME}_gates_report.txt"
    report_path.write_text(report, encoding="utf-8")
    print(f"[{CELL_NAME}] Gates report -> {report_path}")

    print(f"[{CELL_NAME}] Copying final deliverables -> {FINAL_DIR}")
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    for src in sorted(results_dir.rglob("*")):
        if src.is_file():
            dst = FINAL_DIR / src.relative_to(results_dir)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    sim_mf_src = WORK_BASE / "04_simulation_manifest.parquet"
    if sim_mf_src.exists():
        shutil.copy2(sim_mf_src, FINAL_DIR / "04_simulation_manifest.parquet")
    print(f"  Done.")


def main() -> None:
    import sys
    repair1_job_id = sys.argv[1] if len(sys.argv) > 1 else "UNKNOWN"

    print(f"[{CELL_NAME}] step5_only: sim_out pre-populated (1343/1343)")
    print(f"  work_base: {WORK_BASE}")
    assert WORK_BASE.exists(), f"Working dir not found: {WORK_BASE}"

    epw_path = list((WORK_BASE / "weather").rglob("*.epw"))[0]
    print(f"  EPW: {epw_path.name}")

    idf_manifest = pd.read_parquet(STEP3_DIR / "03_idf_manifest.parquet")
    sim_mf = pd.read_parquet(WORK_BASE / "04_simulation_manifest.parquet")

    print(f"  IDF manifest: {len(idf_manifest)} rows, success={(idf_manifest['generation_status']=='success').sum()}")
    print(f"  Sim manifest: {len(sim_mf)} rows, {sim_mf['status'].value_counts().to_dict()}")

    n_fail = int((sim_mf["status"] == "failed").sum())
    if n_fail > 0:
        print(f"[{CELL_NAME}] ZERO-FAIL VIOLATION: {n_fail} failed", file=sys.stderr)
        sys.exit(2)

    run_step5(idf_manifest, sim_mf, epw_path, repair1_job_id)

    print(f"\n[{CELL_NAME}] COMPLETE.")
    print(f"  Simulated: 1343/1343 (1 repaired via single_zone, job {repair1_job_id})")
    print(f"  Main array job: {MAIN_JOB_ID}")


if __name__ == "__main__":
    main()
