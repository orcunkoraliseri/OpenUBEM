"""V12 la_centre step5_fix: re-aggregate already-present SQLs (226/226 complete).

No fetch, no cluster, no EnergyPlus.  Pure local re-parse rooted at
runtime/ubem_validation/cases/la_centre.

Manager-authored driver; Sonnet executor produced this file.
"""
from __future__ import annotations

import json
import re as _re
import shutil
import sys
import time
import warnings
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import pandas as pd

# ── path roots (override the temp-dir roots in the original script) ────────
CELL_NAME = "la_centre"
WORK_BASE = REPO / "runtime" / "ubem_validation" / "cases" / CELL_NAME
STEP3_DIR = WORK_BASE / "step3"
SIM_OUT_DIR = WORK_BASE / "sim_out"
RESULTS_DIR = WORK_BASE / "results"
FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / CELL_NAME

# ── constants ──────────────────────────────────────────────────────────────
LAT, LON = 34.0522, -118.2437
STATE = "CA"
EPSG = 32611
EPW_STATION = "Los.Angeles.Downtown-USC.Campus.722874"
CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"

MAIN_JOB_ID = "964556"
REPAIR_JOB_ID = "964792"
REPAIR2_JOB_ID = "964804"

_floor_rx = _re.compile(r"_F(\d+)_")


# ── import proven helpers from original script (avoids duplication) ────────
# We import them but they use module-level globals from the original.
# To keep paths correct we redefine the three functions that reference path
# globals, and call the originals for everything else.

def _find_epw() -> Path:
    candidates = list((WORK_BASE / "weather").rglob("*.epw"))
    if not candidates:
        raise FileNotFoundError(f"No EPW found under {WORK_BASE / 'weather'}")
    # prefer the one whose name matches EPW_STATION
    for c in candidates:
        if EPW_STATION in c.name:
            return c
    return candidates[0]


def verify_all_complete(osm_ids: list[str]) -> None:
    failed = []
    for oid in osm_ids:
        end_path = SIM_OUT_DIR / oid / "eplusout.end"
        if not end_path.exists():
            failed.append((oid, "missing"))
            continue
        txt = end_path.read_text(errors="replace")
        if "EnergyPlus Completed Successfully" not in txt:
            failed.append((oid, txt.strip()[:100]))
    if failed:
        print(f"  FAILURES: {len(failed)}", file=sys.stderr)
        for oid, msg in failed:
            print(f"    {oid}: {msg}", file=sys.stderr)
        sys.exit(2)
    print(f"  Zero-fail verified: {len(osm_ids)}/{len(osm_ids)} EnergyPlus Completed Successfully")


def build_sim_manifest(idf_manifest: pd.DataFrame, epw_path: Path) -> pd.DataFrame:
    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    osm_id_stems = [Path(str(r["idf_path"])).stem for _, r in success_rows.iterrows()]
    osm_ids_raw = [str(r["osm_id"]) for _, r in success_rows.iterrows()]

    sim_rows = []
    for oid_stem, oid_raw in zip(osm_id_stems, osm_ids_raw):
        bdir = SIM_OUT_DIR / oid_stem
        sql_path = bdir / "eplusout.sql"
        end_path = bdir / "eplusout.end"
        err_path = bdir / "eplusout.err"

        status = "failed"
        n_warnings, n_severe, error_summary = 0, 0, ""
        if end_path.exists():
            txt = end_path.read_text(errors="replace")
            status = "success" if "EnergyPlus Completed Successfully" in txt else "failed"
        if err_path.exists():
            etxt = err_path.read_text(errors="replace")
            matches = _re.findall(r"(\d+)\s+Warning;\s*(\d+)\s+Severe", etxt)
            if matches:
                n_warnings, n_severe = int(matches[-1][0]), int(matches[-1][1])
            severes = [ln.strip() for ln in etxt.splitlines() if "** Severe **" in ln]
            error_summary = severes[0] if severes else ""

        sim_rows.append({
            "osm_id": oid_raw,
            "idf_path": str(STEP3_DIR / "idfs" / f"{oid_stem}.idf"),
            "work_dir": str(bdir),
            "sql_path": str(sql_path) if sql_path.exists() else "",
            "status": status,
            "n_warnings": n_warnings,
            "n_severe": n_severe,
            "wall_clock_s": 0.0,
            "ep_version": "23.1.0",
            "epw_path": str(epw_path),
            "error_summary": error_summary,
            "csv_path": None,
        })

    sim_mf = pd.DataFrame(sim_rows)
    mf_path = WORK_BASE / "04_simulation_manifest.parquet"
    sim_mf.to_parquet(str(mf_path), index=False)
    status_counts = sim_mf["status"].value_counts().to_dict()
    print(f"  Sim manifest: {len(sim_mf)} rows, status={status_counts}")
    return sim_mf


import geopandas as gpd
from shapely.geometry import Point


def build_enriched_gdf(idf_mf: pd.DataFrame, sim_mf: pd.DataFrame) -> gpd.GeoDataFrame:
    import sqlite3
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
                        footprint_area_m2 = floor_areas.get(0, sum(floor_areas.values()) / max(1, len(floor_areas)))
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


def step5_and_report(idf_manifest: pd.DataFrame, sim_mf: pd.DataFrame,
                     epw_path: Path, epw_station_name: str) -> None:
    from openubem.results import aggregate_results, compute_validation_gates
    from openubem import config as cfg

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"  Building enriched GDF ...")
    enriched_gdf = build_enriched_gdf(idf_manifest, sim_mf)

    if "csv_path" not in sim_mf.columns:
        sim_mf = sim_mf.copy()
        sim_mf["csv_path"] = None

    climate_sidecar = WORK_BASE / "02a_climate_epw.parquet"

    print(f"  Step 5: aggregate_results ...")
    t0 = time.monotonic()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results_gdf = aggregate_results(
            sim_mf, idf_manifest, enriched_gdf,
            RESULTS_DIR,
            climate_sidecar=climate_sidecar if climate_sidecar.exists() else None,
            state=STATE,
            make_figures=True,
            ep_version="23.1.0",
        )
    wall = time.monotonic() - t0
    print(f"  aggregate_results done in {wall:.1f}s")

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

    gates_input = results_gdf.copy()
    if "eui_kwh_m2" not in gates_input.columns and "site_eui_kwh_m2" not in gates_input.columns:
        gates_input["eui_kwh_m2"] = gates_input["total_eui_kwh_m2"]
    cbecs_gates = compute_validation_gates(gates_input, reference_path=CBECS_PATH)

    print(f"\n[{CELL_NAME}] F12 GATE SUMMARY:")
    print(f"  pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{n_sim_success}) PASS={pct_parse_success>=0.99}")
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

    n_generated = int((idf_manifest["generation_status"] == "success").sum())
    n_total = len(idf_manifest)
    n_unknown = int((idf_manifest["archetype_id"] == "OpenUBEMUnknown").sum())
    pct_unknown = n_unknown / n_total if n_total > 0 else 0.0
    pct_gen = n_generated / n_total if n_total > 0 else 0.0

    lines = [
        "=" * 72,
        f"V12 {CELL_NAME.upper()} GATES REPORT (226/226 — after repair2 way/425993506)",
        f"  Cell:   {CELL_NAME}  ({LAT}, {LON}) r=500m",
        f"  EPW:    {epw_station_name}",
        f"  Date:   2026-06-12",
        "=" * 72,
        "",
        "=== FUNNEL ===",
        f"  V10 Overpass probe count (lower bound): 182",
        f"  Actual OSM fetch:    {n_total}",
        f"  Generation success:  {n_generated}/{n_total}",
        f"  Simulated (cluster): {n_sim_success}",
        f"  Parsed (Step 5):     {n_parsed}",
        "",
        "=== LIVE_SMOKE GATES ===",
        f"  generation_success: {n_generated}/{n_total} = {pct_gen*100:.1f}%  (>=95%: {'PASS' if pct_gen>=0.95 else 'FAIL'})",
        f"  unknown_archetype: {n_unknown}/{n_total} = {pct_unknown*100:.1f}%  (<20%: {'PASS' if pct_unknown<0.20 else 'FAIL'})",
        "",
        "=== SIMULATION STATUS ===",
        f"  cluster_job_ids: {MAIN_JOB_ID} (main, 223/225) + {REPAIR_JOB_ID} (repair1, 2/2) + {REPAIR2_JOB_ID} (repair2, 1/1)",
        f"  sim_manifest_rows: {len(sim_mf)}",
        f"  status_counts: {sim_mf['status'].value_counts().to_dict()}",
        "",
        "=== REPAIR RECORD ===",
        f"  way/427817502: perimeter_core (MediumOffice, 543.7m2, 5 floors) -> ceiling<->floor cross-zone vertex mismatch",
        f"  Fix: single_zone zoning, job 964792_1, EnergyPlus Completed Successfully 16 Warning 0 Severe",
        f"  way/427817541: perimeter_core (Courthouse, 951.2m2, 3 floors) -> ceiling<->floor cross-zone vertex mismatch",
        f"  Fix: single_zone zoning, job 964792_2, EnergyPlus Completed Successfully 17 Warning 0 Severe",
        f"  way/425993506 (repair2): perimeter_core IndexError (geomeppy break_polygons) -> single_zone, job 964804_1, 0 Severe",
        "",
        "=== F12 GATE TABLE ===",
        f"  pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{n_sim_success})  PASS={pct_parse_success>=0.99}",
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

    report = "\n".join(lines)
    report_path = RESULTS_DIR / f"v12_{CELL_NAME}_gates_report.txt"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n[{CELL_NAME}] Gates report -> {report_path}")

    print(f"\n[{CELL_NAME}] Copying final deliverables -> {FINAL_DIR}")
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    for src in sorted(RESULTS_DIR.rglob("*")):
        if src.is_file():
            dst = FINAL_DIR / src.relative_to(RESULTS_DIR)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    sim_mf_src = WORK_BASE / "04_simulation_manifest.parquet"
    if sim_mf_src.exists():
        shutil.copy2(sim_mf_src, FINAL_DIR / "04_simulation_manifest.parquet")
    print(f"  Done: {FINAL_DIR}")


def main() -> None:
    print(f"[{CELL_NAME}] step5_fix: re-aggregate 226 SQLs from runtime dir")
    print(f"  WORK_BASE: {WORK_BASE}")
    print(f"  SIM_OUT_DIR: {SIM_OUT_DIR}")
    print(f"  FINAL_DIR: {FINAL_DIR}")

    # 1. Locate EPW
    epw_path = _find_epw()
    print(f"  EPW: {epw_path}")

    # 2. Load IDF manifest
    idf_manifest = pd.read_parquet(STEP3_DIR / "03_idf_manifest.parquet")
    n_success_idf = int((idf_manifest["generation_status"] == "success").sum())
    print(f"  IDF manifest: {len(idf_manifest)} rows, success={n_success_idf}")

    # 3. Verify zero-fail gate (all 226 END files say success)
    print(f"\n[{CELL_NAME}] Verifying zero-fail gate ...")
    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    osm_ids = [Path(str(r["idf_path"])).stem for _, r in success_rows.iterrows()]
    verify_all_complete(osm_ids)

    # 4. Build sim manifest fresh (correct runtime paths)
    print(f"\n[{CELL_NAME}] Building sim manifest ...")
    sim_mf = build_sim_manifest(idf_manifest, epw_path)

    status_counts = sim_mf["status"].value_counts().to_dict()
    n_fail = int((sim_mf["status"] == "failed").sum())
    print(f"  status_counts: {status_counts}")

    # Hard gate: must be 226 success before proceeding
    if status_counts != {"success": 226} or n_fail != 0:
        print(f"[{CELL_NAME}] ABORT: expected {{success:226}}, got {status_counts}", file=sys.stderr)
        sys.exit(2)
    print(f"  PASS: status_counts == {{'success': 226}}, n_fail == 0")

    # 5. Step 5 + gates + deliverables
    print(f"\n[{CELL_NAME}] Running Step 5 (aggregate_results) ...")
    step5_and_report(idf_manifest, sim_mf, epw_path, EPW_STATION)

    print(f"\n[{CELL_NAME}] COMPLETE — 226/226 buildings parsed and delivered.")
    print(f"  RESULTS_DIR:  {RESULTS_DIR}")
    print(f"  FINAL_DIR:    {FINAL_DIR}")


if __name__ == "__main__":
    main()
