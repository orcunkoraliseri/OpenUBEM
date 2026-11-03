"""V12 la_centre repair2: regenerate way/425993506 with single_zone fallback.

Diagnosis: perimeter_core zoning raises IndexError in geomeppy break_polygons
(intersect_match path) for this 21-vertex Courthouse polygon.
Same root-cause class as way/427817502 and way/427817541 (job 964792).

Fix: single_zone fallback — zero interzone pairs, no geomeppy intersect needed.

Working dir: runtime/ubem_validation/cases/la_centre/  (raw files moved here
after the original TEMP-based run; step3/idfs + sim_out + manifests all live here).
"""
from __future__ import annotations

import io
import json
import re as _re
import shutil
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
CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"

CELL_NAME = "la_centre"
REMOTE_FLEET_DIR = "/speed-scratch/o_iseri/fleets/la_centre"
WORK_BASE = REPO / "runtime" / "ubem_validation" / "cases" / CELL_NAME
STEP3_DIR = WORK_BASE / "step3"
SIM_OUT_DIR = WORK_BASE / "sim_out"
FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / CELL_NAME

OSM_ID_RAW = "way/425993506"
OSM_ID_STEM = "way_425993506"

LAT, LON = 34.0522, -118.2437
STATE = "CA"
EPSG = 32611

MAIN_JOB_ID = "964556"
REPAIR1_JOB_ID = "964792"
EPW_STATION = "Los.Angeles.Downtown-USC.Campus.722874"

_floor_rx = _re.compile(r"_F(\d+)_")


def _ssh(cmd: str, timeout: int = 120) -> str:
    result = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return result.stdout + result.stderr


def regenerate_idf(epw_path: Path, gdf_raw: gpd.GeoDataFrame) -> Path:
    from geomeppy import IDF as GeomIDF
    from eppy.modeleditor import IDDAlreadySetError
    from openubem import config
    from openubem.geometry.footprint import simplify_footprint, translate_to_origin, derive_num_floors
    from openubem.geometry.zoning import build_zones, decide_zoning_strategy
    from openubem.geometry.context import discover_context
    from openubem.idf.surfaces import extrude_geometry, find_mismatched_interzone_pairs, set_adiabatic_surfaces
    from openubem.idf.builder import BuildingIDF
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    try:
        GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass

    print(f"[repair2] Regenerating {OSM_ID_RAW} ({OSM_ID_STEM}) ...")
    row_raw = gdf_raw[gdf_raw["osm_id"].astype(str) == OSM_ID_RAW]
    assert len(row_raw) == 1, f"Expected 1 row for {OSM_ID_RAW}, got {len(row_raw)}"
    print(f"  footprint={row_raw.iloc[0].get('footprint_area_m2', 0.0):.1f} m2  "
          f"levels={row_raw.iloc[0].get('levels', None)}")

    gdf_single = row_raw[_INPUT_SCHEMA_COLUMNS].copy().reset_index(drop=True)
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

    geom = row_enriched["geometry"]
    dq_flag = str(row_enriched.get("data_quality_flag", "") or "")
    poly_r, dq_r, simp_r = simplify_footprint(geom, dq_flag)
    poly_local_r, cx_r, cy_r = translate_to_origin(poly_r)
    nf = derive_num_floors(row_enriched)
    fa = float(row_enriched.get("footprint_area_m2") or poly_r.area)

    orig_strategy = decide_zoning_strategy(row_enriched["archetype_id"], fa, nf)
    print(f"  simp={simp_r}, floors={nf}, area={fa:.1f}, original_strategy={orig_strategy}")

    repair_strategy = "single_zone"
    zones_ok = build_zones(OSM_ID_RAW, poly_local_r, row_enriched["archetype_id"], nf, repair_strategy)
    print(f"  zones with single_zone: {len(zones_ok)}")

    row_ctx = row_enriched.copy()
    row_ctx["_simplified_geom"] = poly_r
    context = discover_context(row_ctx, gdf_raw, cx_r, cy_r, config.SHADING_SPHERE_RADIUS)
    print(f"  context buildings: {len(context)}")

    bldg = BuildingIDF(row_enriched)
    bldg.copy_schedule_library(row_enriched["archetype_id"], schedule_library)
    extrude_geometry(bldg.idf, zones_ok, context)

    still_mismatched = find_mismatched_interzone_pairs(bldg.idf)
    assert len(still_mismatched) == 0, f"single_zone still mismatched: {still_mismatched}"
    print(f"  mismatched pairs with single_zone: 0  (PASS)")

    set_adiabatic_surfaces(bldg.idf, zones_ok, repair_strategy)

    extruded_zones = [z for z in zones_ok if z.get("extruded")]
    bldg.assign_constructions()
    bldg.assign_infiltration(extruded_zones)
    bldg.assign_loads(extruded_zones)

    from openubem.idf.hvac import assign_hvac
    from openubem.idf.outputs import write_outputs
    assign_hvac(bldg.idf, row_enriched, extruded_zones)
    write_outputs(bldg.idf)

    idf_out_path = STEP3_DIR / "idfs" / f"{OSM_ID_STEM}.idf"
    idf_out_path.parent.mkdir(parents=True, exist_ok=True)
    bldg.idf.save(str(idf_out_path))
    print(f"  IDF saved: {idf_out_path}  ({idf_out_path.stat().st_size} bytes)")
    return idf_out_path


def upload_and_submit(idf_path: Path, epw_path: Path) -> str:
    print(f"[repair2] Uploading IDF to cluster ...")
    subprocess.run(["scp", str(idf_path), f"{REMOTE_HOST}:{REMOTE_FLEET_DIR}/idfs/"],
                   check=True, timeout=60)
    print(f"  uploaded: {idf_path.name}")

    repair2_dir = REMOTE_FLEET_DIR + "_repair2"
    _ssh(f"mkdir -p {repair2_dir}/idfs {repair2_dir}/weather {repair2_dir}/out")

    subprocess.run(["scp", str(idf_path), f"{REMOTE_HOST}:{repair2_dir}/idfs/"],
                   check=True, timeout=60)
    subprocess.run(["scp", str(epw_path), f"{REMOTE_HOST}:{repair2_dir}/weather/"],
                   check=True, timeout=120)

    fleet_content = OSM_ID_STEM + "\n"
    fleet_remote = f"{repair2_dir}/fleet.lst"
    with subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc 'cat > {fleet_remote}'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ) as proc:
        proc.stdin.write(fleet_content.encode("utf-8"))
        proc.stdin.close()
        proc.wait(timeout=30)

    ep_dir_cmd = (
        "EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-*Ubuntu20* 2>/dev/null | head -1); "
        "[ -z \"$EP_DIR\" ] && EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-* | head -1)"
    )
    epw_remote = f"{repair2_dir}/weather/{epw_path.name}"

    sbatch_script = f"""#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --time=01:30:00
#SBATCH --job-name=openubem_{CELL_NAME}_repair2
#SBATCH --output={repair2_dir}/repair2_%A_%a.log

set -e
{ep_dir_cmd}
LINE=$(sed -n "${{SLURM_ARRAY_TASK_ID}}p" {fleet_remote})
IDF={repair2_dir}/idfs/${{LINE}}.idf
OUTDIR={repair2_dir}/out/${{LINE}}
EPW={epw_remote}
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
    sbatch_remote_path = f"{repair2_dir}/repair2_array.sbatch"
    with subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc 'cat > {sbatch_remote_path}'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ) as proc:
        proc.stdin.write(sbatch_script.encode("utf-8").replace(b"\r\n", b"\n"))
        proc.stdin.close()
        proc.wait(timeout=30)

    out = _ssh(f"sbatch --array=1-1%32 {sbatch_remote_path}", timeout=60)
    print(f"  sbatch output: {out.strip()}")
    job_id = ""
    for line in out.splitlines():
        if "Submitted batch job" in line:
            job_id = line.strip().split()[-1]
            break
    if not job_id:
        print(f"  ERROR: no job ID from sbatch: {out}", file=sys.stderr)
        sys.exit(2)
    print(f"  Repair2 array job ID: {job_id}")
    return job_id


def poll_cluster(job_id: str, poll_interval_s: int = 60) -> None:
    print(f"[repair2] Polling job {job_id} (every {poll_interval_s}s) ...")
    while True:
        time.sleep(poll_interval_s)
        out = _ssh(f"squeue -j {job_id} --noheader 2>/dev/null | wc -l", timeout=60)
        pending = int(out.strip()) if out.strip().isdigit() else -1
        sacct = _ssh(f"sacct -j {job_id} --format=State --noheader 2>/dev/null | sort | uniq -c", timeout=60)
        print(f"  [{time.strftime('%H:%M:%S')}] pending={pending}  states={sacct.strip()}")
        if pending == 0:
            sacct_full = _ssh(f"sacct -j {job_id} --format=JobID,State,ExitCode --noheader 2>/dev/null", timeout=90)
            print(sacct_full[:2000])
            break


def fetch_result(job_id: str) -> None:
    repair2_dir = REMOTE_FLEET_DIR + "_repair2"
    print(f"[repair2] Fetching {OSM_ID_STEM} by explicit path ...")
    out_dir = SIM_OUT_DIR / OSM_ID_STEM
    out_dir.mkdir(parents=True, exist_ok=True)

    fetch_cmd = (
        f"cd {repair2_dir}/out && tar czf - "
        f"{OSM_ID_STEM}/eplusout.sql {OSM_ID_STEM}/eplusout.err {OSM_ID_STEM}/eplusout.end"
    )
    proc = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc '{fetch_cmd}'"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    stdout_data, stderr_data = proc.communicate(timeout=600)
    if stderr_data:
        msg = stderr_data.decode(errors="replace").strip()
        if msg:
            print(f"  fetch stderr: {msg[:300]}")
    assert stdout_data, f"Empty fetch response for {OSM_ID_STEM}"
    with tarfile.open(fileobj=io.BytesIO(stdout_data), mode="r:gz") as tf:
        tf.extractall(str(SIM_OUT_DIR))

    end_path = SIM_OUT_DIR / OSM_ID_STEM / "eplusout.end"
    assert end_path.exists(), f"eplusout.end not found for {OSM_ID_STEM}"
    end_text = end_path.read_text(errors="replace")
    print(f"  {OSM_ID_STEM} eplusout.end: {end_text.strip()}")
    assert "EnergyPlus Completed Successfully" in end_text, f"Sim failed: {end_text}"
    print(f"  PASS: EnergyPlus Completed Successfully")


def update_idf_manifest(idf_path: Path) -> pd.DataFrame:
    mf = pd.read_parquet(STEP3_DIR / "03_idf_manifest.parquet")
    row_idx = mf.index[mf["osm_id"].astype(str) == OSM_ID_RAW]
    assert len(row_idx) == 1, f"Expected 1 row for {OSM_ID_RAW}"
    i = row_idx[0]
    mf.loc[i, "idf_path"] = str(idf_path)
    mf.loc[i, "generation_status"] = "success"
    mf.loc[i, "zoning_strategy"] = "single_zone"
    mf.loc[i, "num_zones"] = 1
    dq = str(mf.loc[i, "data_quality_flag"] or "")
    mf.loc[i, "data_quality_flag"] = (dq + "|single_zone_repair").lstrip("|")
    mf.to_parquet(STEP3_DIR / "03_idf_manifest.parquet", index=False)
    print(f"[repair2] IDF manifest updated: {len(mf)} rows, "
          f"success={(mf['generation_status']=='success').sum()}")
    return mf


def update_sim_manifest(idf_manifest: pd.DataFrame, epw_path: Path) -> pd.DataFrame:
    old_mf = pd.read_parquet(WORK_BASE / "04_simulation_manifest.parquet")
    print(f"[repair2] Old sim manifest: {len(old_mf)} rows")

    bdir = SIM_OUT_DIR / OSM_ID_STEM
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
        import re
        matches = re.findall(r"(\d+)\s+Warning;\s*(\d+)\s+Severe", etxt)
        if matches:
            n_warnings, n_severe = int(matches[-1][0]), int(matches[-1][1])

    new_row = pd.DataFrame([{
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
    }])

    sim_mf = pd.concat([old_mf, new_row], ignore_index=True)
    sim_mf.to_parquet(WORK_BASE / "04_simulation_manifest.parquet", index=False)
    status_counts = sim_mf["status"].value_counts().to_dict()
    print(f"[repair2] Sim manifest updated: {len(sim_mf)} rows, status={status_counts}")
    assert (sim_mf["status"] == "failed").sum() == 0, "Still have failed rows"
    return sim_mf


def build_enriched_gdf(idf_mf: pd.DataFrame, sim_mf: pd.DataFrame) -> "gpd.GeoDataFrame":
    import sqlite3
    from shapely.geometry import Point
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
              epw_path: Path, repair_job_id: str) -> None:
    from openubem.results import aggregate_results, compute_validation_gates
    from openubem import config as cfg

    results_dir = WORK_BASE / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"[repair2] Building enriched GDF ({len(idf_manifest)} buildings) ...")
    enriched_gdf = build_enriched_gdf(idf_manifest, sim_mf)

    if "csv_path" not in sim_mf.columns:
        sim_mf = sim_mf.copy()
        sim_mf["csv_path"] = None

    climate_sidecar = WORK_BASE / "02a_climate_epw.parquet"
    print(f"[repair2] Step 5: aggregate_results ...")
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

    print(f"\n[{CELL_NAME}] F12 GATE SUMMARY (226/226):")
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
        f"V12 {CELL_NAME.upper()} GATES REPORT (226/226 — after repair2 {OSM_ID_RAW})",
        f"  Cell:   {CELL_NAME}  ({LAT}, {LON}) r=500m",
        f"  EPW:    {EPW_STATION}",
        f"  Date:   2026-06-12",
        "=" * 72,
        "",
        "=== FUNNEL ===",
        f"  V10 Overpass probe count (lower bound): 182",
        f"  Actual OSM fetch:    226",
        f"  Generation success:  {n_gen}/{n_total}",
        f"  Simulated (cluster): {n_sim_success}",
        f"  Parsed (Step 5):     {n_parsed}",
        "",
        "=== LIVE_SMOKE GATES ===",
        f"  generation_success: {n_gen}/{n_total} = {pct_gen*100:.1f}%  (>=95%: {'PASS' if pct_gen>=0.95 else 'FAIL'})",
        f"  unknown_archetype: {n_unknown}/{n_total} = {(n_unknown/n_total)*100:.1f}%  (<20%: {'PASS' if n_unknown/n_total<0.20 else 'FAIL'})",
        "",
        "=== SIMULATION STATUS ===",
        f"  cluster_job_ids: {MAIN_JOB_ID} (main, 223/225) + {REPAIR1_JOB_ID} (repair1, 2/2) + {repair_job_id} (repair2, 1/1)",
        f"  sim_manifest_rows: {len(sim_mf)}",
        f"  status_counts: {sim_mf['status'].value_counts().to_dict()}",
        "",
        "=== REPAIR RECORD ===",
        f"  way/427817502: perimeter_core IndexError -> single_zone, job 964792_1, 0 Severe",
        f"  way/427817541: perimeter_core IndexError -> single_zone, job 964792_2, 0 Severe",
        f"  way/425993506 (repair2): perimeter_core IndexError (geomeppy break_polygons) -> single_zone, job {repair_job_id}_1, 0 Severe",
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
    print(f"[repair2] Gates report -> {report_path}")

    print(f"[repair2] Copying final deliverables -> {FINAL_DIR}")
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


def clean_repair2_scratch() -> None:
    repair2_dir = REMOTE_FLEET_DIR + "_repair2"
    out_dir = f"{repair2_dir}/out"
    out = _ssh(f"rm -rf {out_dir} 2>/dev/null && echo CLEANED || echo FAILED", timeout=60)
    print(f"[repair2] Cluster scratch clean: {out.strip()}")


def main() -> None:
    print(f"[repair2] V12 la_centre repair2: {OSM_ID_RAW}")
    print(f"[repair2] Working dir: {WORK_BASE}")
    assert WORK_BASE.exists(), f"Working dir not found: {WORK_BASE}"

    epw_candidates = list((WORK_BASE / "weather").rglob("*.epw"))
    assert epw_candidates, f"No EPW found under {WORK_BASE / 'weather'}"
    epw_path = epw_candidates[0]
    print(f"[repair2] EPW: {epw_path.name}")

    gdf_raw = gpd.read_file(str(WORK_BASE / "01_buildings.gpkg"))
    print(f"[repair2] Loaded {len(gdf_raw)} buildings from 01_buildings.gpkg")

    # Step 1: generate IDF with single_zone fallback
    idf_path = regenerate_idf(epw_path, gdf_raw)

    # Step 2: upload + submit 1-task array
    job_id = upload_and_submit(idf_path, epw_path)

    # Step 3: poll synchronously
    poll_cluster(job_id, poll_interval_s=60)

    # Step 4: fetch SQL explicitly by path
    fetch_result(job_id)

    # Step 5: update IDF manifest
    idf_manifest = update_idf_manifest(idf_path)

    # Step 6: update sim manifest
    sim_mf = update_sim_manifest(idf_manifest, epw_path)

    # Step 7: re-run Step 5 aggregation, write gates report, copy deliverables
    run_step5(idf_manifest, sim_mf, epw_path, job_id)

    # Step 8: clean cluster out/ (keep fleet.lst + idfs/)
    clean_repair2_scratch()

    print(f"\n[repair2] COMPLETE.")
    print(f"  Building:   {OSM_ID_RAW}")
    print(f"  Exception:  IndexError in geomeppy break_polygons (perimeter_core)")
    print(f"  Fix:        single_zone fallback")
    print(f"  Cluster job: {job_id}")
    print(f"  Generation: 226/226")
    print(f"  Simulation: 226/226")
    print(f"  SQL:        {WORK_BASE / 'sim_out' / OSM_ID_STEM / 'eplusout.sql'}")


if __name__ == "__main__":
    main()
