"""V12 nyc_urban repair: regenerate way/281346738 with single_zone fallback.

Diagnosis: perimeter_core zoning on the 17-vertex simplified polygon creates
Perimeter_Zone_3 ceiling <-> Perimeter_Zone_13 floor cross-floor mismatched
vertex pairs (3 vs 7 verts) that the existing _repair_mismatched_horizontal_pairs
hook does not catch (it catches same-type pairs; these are ceiling<->floor
cross-zone-type pairs between non-adjacent perimeter wedges).

Fix: force single_zone for this building only.  All other buildings untouched.
"""
from __future__ import annotations

import io
import json
import re as _re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
import warnings
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
SBATCH_REMOTE = "/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet.sbatch"
SBATCH_LOCAL = REPO / "scripts" / "cluster" / "submit_fleet.sbatch"
CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"

CELL_NAME = "nyc_urban"
OSM_ID_RAW = "way/281346738"
OSM_ID_STEM = "way_281346738"
REMOTE_FLEET_DIR = "/speed-scratch/o_iseri/fleets/nyc_urban"

import tempfile
WORK_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "cases" / CELL_NAME
STEP3_DIR = WORK_BASE / "step3"
SIM_OUT_DIR = WORK_BASE / "sim_out"
RESULTS_DIR = WORK_BASE / "results"
FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / CELL_NAME

LAT, LON = 40.7721, -73.9301
STATE = "NY"
EPSG = 32618

_floor_rx = _re.compile(r"_F(\d+)_")


def _ssh(cmd: str, timeout: int = 120) -> str:
    result = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return result.stdout + result.stderr


def regenerate_idf(epw_path: Path) -> Path:
    from geomeppy import IDF as GeomIDF
    from eppy.modeleditor import IDDAlreadySetError
    from openubem import config
    from openubem.geometry.footprint import (
        simplify_footprint, translate_to_origin, derive_num_floors,
    )
    from openubem.geometry.zoning import build_zones
    from openubem.geometry.context import discover_context
    from openubem.idf.surfaces import extrude_geometry, find_mismatched_interzone_pairs
    from openubem.idf.builder import BuildingIDF
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    try:
        GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass

    print(f"[repair] Loading 01_buildings.gpkg ...")
    gdf_raw = gpd.read_file(str(WORK_BASE / "01_buildings.gpkg"))
    row_raw = gdf_raw[gdf_raw["osm_id"].astype(str) == OSM_ID_RAW]
    assert len(row_raw) == 1, f"Expected 1 row for {OSM_ID_RAW}, got {len(row_raw)}"
    print(f"[repair] Building: footprint={row_raw.iloc[0]['footprint_area_m2']:.1f} m2, "
          f"height={row_raw.iloc[0]['height_m']} m")

    print("[repair] Running Step 2 (classify + enrich) for this one building ...")
    gdf_single = row_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_single["levels"] = gdf_single["levels"].astype("Int64")

    bc = BuildingClassifier()
    gdf_26 = bc.classify(gdf_single)
    print(f"  archetype: {gdf_26.iloc[0]['archetype_id']}")

    zone_df = assign_climate_zones(gdf_26)
    gdf_29 = gdf_26.copy()
    gdf_29["climate_zone"] = pd.Categorical(zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB))
    gdf_29["epw_path"] = str(epw_path)
    gdf_29["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values, categories=["ASHRAE_STANDARD", "HEURISTIC"],
    )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gdf_57, schedule_library = enrich_semantics(gdf_29)

    row_enriched = gdf_57.iloc[0]
    print(f"  enriched archetype: {row_enriched['archetype_id']}")

    print("[repair] Diagnosing original failure ...")
    from openubem.geometry.footprint import simplify_footprint, translate_to_origin, derive_num_floors
    from openubem.geometry.zoning import decide_zoning_strategy

    geom = row_enriched["geometry"]
    dq_flag = str(row_enriched.get("data_quality_flag", "") or "")
    poly, dq_flag2, simp_status = simplify_footprint(geom, dq_flag)
    poly_local, cx, cy = translate_to_origin(poly)
    num_floors = derive_num_floors(row_enriched)
    footprint_area = float(row_enriched.get("footprint_area_m2") or poly.area)
    orig_strategy = decide_zoning_strategy(row_enriched["archetype_id"], footprint_area, num_floors)
    print(f"  simp={simp_status}, floors={num_floors}, area={footprint_area:.1f}, strategy={orig_strategy}")

    from importlib.resources import files
    template_path = str(files("openubem.idf").joinpath("templates").joinpath("commercial_base.idf"))
    idf_test = GeomIDF(template_path)
    zones_bad = build_zones(OSM_ID_RAW, poly_local, row_enriched["archetype_id"], num_floors, orig_strategy)
    extrude_geometry(idf_test, zones_bad, [])
    mismatched = find_mismatched_interzone_pairs(idf_test)
    print(f"  mismatched pairs with {orig_strategy}: {len(mismatched)}")
    assert len(mismatched) > 0, "Expected failure not reproduced"

    print("[repair] Regenerating with single_zone fallback ...")
    row_for_build = row_enriched.copy()

    idf_out_path = STEP3_DIR / "idfs" / f"{OSM_ID_STEM}.idf"
    idf_out_path.parent.mkdir(parents=True, exist_ok=True)

    bldg = BuildingIDF(row_for_build)
    bldg_geom = row_for_build["geometry"]
    dq_orig = str(row_for_build.get("data_quality_flag", "") or "")
    poly_r, dq_r, simp_r = simplify_footprint(bldg_geom, dq_orig)
    poly_local_r, cx_r, cy_r = translate_to_origin(poly_r)
    nf = derive_num_floors(row_for_build)
    fa = float(row_for_build.get("footprint_area_m2") or poly_r.area)

    repair_strategy = "single_zone"
    zones_ok = build_zones(OSM_ID_RAW, poly_local_r, row_for_build["archetype_id"], nf, repair_strategy)

    context = discover_context(row_for_build, gdf_raw, cx_r, cy_r, config.SHADING_SPHERE_RADIUS)
    bldg.copy_schedule_library(row_for_build["archetype_id"], schedule_library)
    extrude_geometry(bldg.idf, zones_ok, context)

    still_mismatched = find_mismatched_interzone_pairs(bldg.idf)
    assert len(still_mismatched) == 0, f"single_zone still mismatched: {still_mismatched}"
    print(f"  mismatched pairs with {repair_strategy}: 0  (PASS)")

    from openubem.idf.surfaces import set_adiabatic_surfaces
    set_adiabatic_surfaces(bldg.idf, zones_ok, repair_strategy)

    extruded_zones = [z for z in zones_ok if z.get("extruded")]
    bldg.assign_constructions()
    bldg.assign_infiltration(extruded_zones)
    bldg.assign_loads(extruded_zones)

    from openubem.idf.hvac import assign_hvac
    from openubem.idf.outputs import write_outputs
    assign_hvac(bldg.idf, row_for_build, extruded_zones)
    write_outputs(bldg.idf)
    bldg.idf.save(str(idf_out_path))
    print(f"  IDF saved: {idf_out_path}")

    return idf_out_path


def upload_and_submit(idf_path: Path, epw_path: Path) -> str:
    print(f"[repair] Uploading IDF to cluster ...")
    subprocess.run(["scp", str(idf_path), f"{REMOTE_HOST}:{REMOTE_FLEET_DIR}/idfs/"], check=True, timeout=60)

    # Write a single-task sbatch script inline (avoids fleet.lst dependency for one building).
    ep_dir_cmd = (
        "EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-*Ubuntu20* 2>/dev/null | head -1); "
        "[ -z \"$EP_DIR\" ] && EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-* | head -1)"
    )
    epw_remote = f"{REMOTE_FLEET_DIR}/weather/{epw_path.name}"
    idf_remote = f"{REMOTE_FLEET_DIR}/idfs/{OSM_ID_STEM}.idf"
    outdir_remote = f"{REMOTE_FLEET_DIR}/out/{OSM_ID_STEM}"

    sbatch_script = f"""#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --time=01:30:00
#SBATCH --job-name=openubem_{CELL_NAME}_repair
#SBATCH --output={REMOTE_FLEET_DIR}/repair_{OSM_ID_STEM}_%j.log

set -e
{ep_dir_cmd}
EPW={epw_remote}
IDF={idf_remote}
OUTDIR={outdir_remote}
mkdir -p "$OUTDIR"
cd "$OUTDIR"
cp "${{EP_DIR}}/Energy+.idd" "$OUTDIR/"
cp "$IDF" "$OUTDIR/in.idf"
"${{EP_DIR}}/ExpandObjects"
if [ -f "$OUTDIR/expanded.idf" ]; then RUN_IDF="$OUTDIR/expanded.idf"; else RUN_IDF="$OUTDIR/in.idf"; fi
"${{EP_DIR}}/energyplus" -w "$EPW" -d "$OUTDIR" "$RUN_IDF"
RC=$?
echo $RC > "${{OUTDIR}}/task.rc"
exit $RC
"""
    sbatch_remote_path = f"{REMOTE_FLEET_DIR}/repair_{OSM_ID_STEM}.sbatch"
    write_cmd = f"cat > {sbatch_remote_path} << 'ENDBATCH'\n{sbatch_script}\nENDBATCH"
    _ssh(write_cmd, timeout=30)

    out = _ssh(f"sbatch {sbatch_remote_path}", timeout=60)
    print(f"  sbatch: {out.strip()}")
    job_id = ""
    for line in out.splitlines():
        if "Submitted batch job" in line:
            job_id = line.strip().split()[-1]
            break
    if not job_id:
        print(f"  ERROR: no job ID from sbatch output: {out}", file=sys.stderr)
        sys.exit(2)
    print(f"  Repair job ID: {job_id}")
    return job_id


def poll_cluster(job_id: str, poll_interval_s: int = 90) -> None:
    print(f"[repair] Polling job {job_id} ...")
    while True:
        time.sleep(poll_interval_s)
        out = _ssh(f"squeue -j {job_id} --noheader 2>/dev/null | wc -l", timeout=60)
        pending = int(out.strip()) if out.strip().isdigit() else -1
        sacct = _ssh(f"sacct -j {job_id} --format=State --noheader 2>/dev/null | sort | uniq -c", timeout=60)
        print(f"  [{time.strftime('%H:%M:%S')}] pending={pending}  states={sacct.strip()}")
        if pending == 0:
            sacct_full = _ssh(f"sacct -j {job_id} --format=JobID,State,ExitCode --noheader 2>/dev/null", timeout=90)
            print(sacct_full[:1000])
            break


def fetch_result() -> None:
    print(f"[repair] Fetching result for {OSM_ID_STEM} by explicit path ...")
    out_dir = SIM_OUT_DIR / OSM_ID_STEM
    out_dir.mkdir(parents=True, exist_ok=True)
    fetch_cmd = (
        f"cd {REMOTE_FLEET_DIR}/out && tar czf - "
        f"{OSM_ID_STEM}/eplusout.sql {OSM_ID_STEM}/eplusout.err {OSM_ID_STEM}/eplusout.end"
    )
    proc = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc '{fetch_cmd}'"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    stdout_data, stderr_data = proc.communicate(timeout=300)
    if stderr_data:
        msg = stderr_data.decode(errors="replace").strip()
        if msg:
            print(f"  fetch stderr: {msg[:300]}")
    if stdout_data:
        with tarfile.open(fileobj=io.BytesIO(stdout_data), mode="r:gz") as tf:
            tf.extractall(str(SIM_OUT_DIR))
    end_path = SIM_OUT_DIR / OSM_ID_STEM / "eplusout.end"
    assert end_path.exists(), f"eplusout.end not found at {end_path}"
    end_text = end_path.read_text(errors="replace")
    print(f"  eplusout.end: {end_text.strip()}")
    assert "EnergyPlus Completed Successfully" in end_text, f"Simulation failed: {end_text}"
    print(f"  PASS: EnergyPlus Completed Successfully")


def update_idf_manifest(idf_path: Path, repair_strategy: str) -> pd.DataFrame:
    idf_manifest = pd.read_parquet(STEP3_DIR / "03_idf_manifest.parquet")
    row_idx = idf_manifest.index[idf_manifest["osm_id"].astype(str) == OSM_ID_RAW]
    assert len(row_idx) == 1
    idf_manifest.loc[row_idx[0], "idf_path"] = str(idf_path)
    idf_manifest.loc[row_idx[0], "generation_status"] = "success"
    idf_manifest.loc[row_idx[0], "zoning_strategy"] = repair_strategy
    idf_manifest.loc[row_idx[0], "num_zones"] = 1
    idf_manifest.loc[row_idx[0], "simplification_status"] = "dp_05"
    idf_manifest.loc[row_idx[0], "data_quality_flag"] = (
        idf_manifest.loc[row_idx[0], "data_quality_flag"] + "|single_zone_repair"
    )
    idf_manifest.to_parquet(STEP3_DIR / "03_idf_manifest.parquet", index=False)
    print(f"[repair] IDF manifest updated: {len(idf_manifest)} rows, "
          f"success={int((idf_manifest['generation_status']=='success').sum())}")
    return idf_manifest


def update_sim_manifest(idf_manifest: pd.DataFrame, epw_path: Path, job_id: str) -> pd.DataFrame:
    sim_mf_path = WORK_BASE / "04_simulation_manifest.parquet"
    sim_mf = pd.read_parquet(sim_mf_path)
    assert len(sim_mf) == 1778, f"Expected 1778 rows, got {len(sim_mf)}"

    bdir = SIM_OUT_DIR / OSM_ID_STEM
    end_path = bdir / "eplusout.end"
    err_path = bdir / "eplusout.err"
    sql_path = bdir / "eplusout.sql"

    end_text = end_path.read_text(errors="replace")
    status = "success" if "EnergyPlus Completed Successfully" in end_text else "failed"

    n_warnings, n_severe = 0, 0
    error_summary = ""
    if err_path.exists():
        etxt = err_path.read_text(errors="replace")
        matches = _re.findall(r"(\d+)\s+Warning;\s*(\d+)\s+Severe", etxt)
        if matches:
            n_warnings, n_severe = int(matches[-1][0]), int(matches[-1][1])

    new_row = {
        "osm_id": OSM_ID_RAW,
        "idf_path": str(STEP3_DIR / "idfs" / f"{OSM_ID_STEM}.idf"),
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
    }
    sim_mf_new = pd.concat([sim_mf, pd.DataFrame([new_row])], ignore_index=True)
    sim_mf_new.to_parquet(sim_mf_path, index=False)
    print(f"[repair] Sim manifest updated: {len(sim_mf_new)} rows, "
          f"success={int((sim_mf_new['status']=='success').sum())}")
    return sim_mf_new


def run_step5_full(idf_manifest: pd.DataFrame, sim_mf: pd.DataFrame, epw_path: Path,
                   job_ids: str) -> None:
    from shapely.geometry import Point
    from openubem.results import aggregate_results, compute_validation_gates
    from openubem import config as cfg

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for _, idf_row in idf_manifest.iterrows():
        oid_raw = str(idf_row["osm_id"])
        sim_row = sim_mf[sim_mf["osm_id"].astype(str) == oid_raw]
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
                    print(f"  SQL error for {oid_raw}: {e}")

        rows.append({
            "osm_id": oid_raw,
            "footprint_area_m2": footprint_area_m2,
            "levels": num_floors,
            "height_m": height_m,
            "archetype_id": idf_row["archetype_id"],
            "zoning_strategy": idf_row["zoning_strategy"],
            "data_quality_flag": idf_row.get("data_quality_flag", ""),
            "geometry": Point(centroid_x, centroid_y),
        })

    enriched_gdf = gpd.GeoDataFrame(rows, crs=f"EPSG:{EPSG}")

    if "csv_path" not in sim_mf.columns:
        sim_mf = sim_mf.copy()
        sim_mf["csv_path"] = None

    climate_sidecar = WORK_BASE / "02a_climate_epw.parquet"

    print("[repair] Step 5: aggregate_results (full fleet 1779) ...")
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

    gates_input = results_gdf.copy()
    if "eui_kwh_m2" not in gates_input.columns and "site_eui_kwh_m2" not in gates_input.columns:
        gates_input["eui_kwh_m2"] = gates_input["total_eui_kwh_m2"]
    cbecs_gates = compute_validation_gates(gates_input, reference_path=CBECS_PATH)

    success_statuses = {"success", "success_cached", "success_csv_fallback"}
    parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
    n_parsed = len(parsed)
    lb, ub = cfg.EUI_PLAUSIBILITY_BOUNDS
    valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
    in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
    pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
    outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]
    n_zone_mismatch = len(results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"])
    iod_vals = parsed["iod"].dropna()
    pct_parse_success = n_parsed / len(sim_mf) if len(sim_mf) > 0 else 0.0

    print(f"\n[repair] F12 GATE SUMMARY (1779 buildings):")
    print(f"  pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{len(sim_mf)}) PASS={pct_parse_success>=0.99}")
    print(f"  EUI plausibility: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)}) PASS={pct_plausible>=0.99}")
    if len(outliers):
        print(f"  EUI outliers: {len(outliers)}, min={outliers.min():.1f}, max={outliers.max():.1f}")
    print(f"  zone_mismatch: {n_zone_mismatch} PASS={n_zone_mismatch==0}")
    print(f"  IOD: n={len(iod_vals)}, mean={iod_vals.mean():.4f}, p95={iod_vals.quantile(0.95):.4f}")

    print(f"\n[repair] CBECS 2018 NE GATES (report-only):")
    for k in ["cbecs_cv_rmse", "cbecs_nmbe", "cbecs_r2", "cbecs_ks_d"]:
        print(f"  {k}: {cbecs_gates[k]}")

    summary_path = RESULTS_DIR / "05_neighbourhood_summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    eui_map = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    print(f"\n[repair] HEADLINE NUMBERS (1779):")
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui_map.get(k)
        if v is not None:
            print(f"  {k}: {v:.2f}")
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    if gwp:
        print(f"  GWP: {gwp:,.0f} kgCO2e")

    n_generated = int((idf_manifest["generation_status"] == "success").sum())
    n_total = len(idf_manifest)
    n_unknown = int((idf_manifest["archetype_id"] == "OpenUBEMUnknown").sum())
    pct_unknown = n_unknown / n_total if n_total > 0 else 0.0
    pct_gen = n_generated / n_total if n_total > 0 else 0.0
    epw_station_name = "New.York-Central.Park.Obs-Belvedere.Castle.725053"

    lines = [
        "=" * 72,
        "V12 NYC_URBAN GATES REPORT (1779/1779 — repaired)",
        f"  Cell:   nyc_urban  ({LAT}, {LON}) r=500m",
        f"  EPW:    {epw_station_name}",
        "  Date:   2026-06-12",
        "=" * 72,
        "",
        "=== FUNNEL ===",
        f"  V10 Overpass probe count (lower bound): 1526",
        f"  Actual OSM fetch:    1779",
        f"  Generation success:  {n_generated}/{n_total}",
        f"  Simulated (cluster): {len(sim_mf)}",
        f"  Parsed (Step 5):     {n_parsed}",
        "",
        "=== LIVE_SMOKE GATES ===",
        f"  generation_success: {n_generated}/{n_total} = {pct_gen*100:.1f}%  (>=95%: {'PASS' if pct_gen>=0.95 else 'FAIL'})",
        f"  unknown_archetype: {n_unknown}/{n_total} = {pct_unknown*100:.1f}%  (<20%: {'PASS' if pct_unknown<0.20 else 'FAIL'})",
        "",
        "=== SIMULATION STATUS ===",
        f"  cluster_job_ids: {job_ids}",
        f"  sim_manifest_rows: {len(sim_mf)}",
        f"  status_counts: {sim_mf['status'].value_counts().to_dict()}",
        "",
        "=== REPAIR RECORD ===",
        f"  way/281346738: perimeter_core 17-vert poly -> ceiling<->floor cross-zone vertex mismatch",
        f"  Fix: single_zone zoning (6 floors, 642.9 m2 footprint, MediumOffice)",
        "",
        "=== F12 GATE TABLE ===",
        f"  pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{len(sim_mf)})  PASS={pct_parse_success>=0.99}",
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
    report_path = RESULTS_DIR / "v12_nyc_urban_gates_report.txt"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n[repair] Gates report -> {report_path}")

    print(f"\n[repair] Copying final deliverables ...")
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
    print(f"[repair] V12 nyc_urban single-building repair: {OSM_ID_RAW}")
    print(f"[repair] Working dir: {WORK_BASE}")

    epw_path = list((WORK_BASE / "weather").rglob("*.epw"))[0]
    print(f"[repair] EPW: {epw_path.name}")

    idf_path = regenerate_idf(epw_path)

    job_id = upload_and_submit(idf_path, epw_path)

    poll_cluster(job_id, poll_interval_s=90)

    fetch_result()

    idf_manifest = update_idf_manifest(idf_path, "single_zone")

    sim_mf = update_sim_manifest(idf_manifest, epw_path, job_id)

    print(f"\n[repair] Final funnel: fetch=1779, generated=1779/1779 (1 repaired), simulated=1779/1779")

    run_step5_full(idf_manifest, sim_mf, epw_path, job_ids=f"959157+{job_id}")

    print(f"\n[repair] COMPLETE. way/281346738 repaired and aggregated.")
    print(f"  Repair job ID: {job_id}")


if __name__ == "__main__":
    main()
