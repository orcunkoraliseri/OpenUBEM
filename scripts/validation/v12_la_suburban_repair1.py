"""V12 la_suburban repair1: regenerate way/442763908 with single_zone fallback.

Failure: perimeter_core zoning (38 zones) raises vertex size mismatch between
ceiling/floor surfaces (6 vs 7 vertices). Same root-cause class as la_urban/la_centre repairs.
Fix: single_zone fallback — zero interzone pairs, no geomeppy intersect needed.

Working dir: %TEMP%/ubem_validation/cases/la_suburban/
"""
from __future__ import annotations

import io
import json
import re as _re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import warnings
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"

CELL_NAME = "la_suburban"
REMOTE_FLEET_DIR = "/speed-scratch/o_iseri/fleets/la_suburban"
REPAIR_DIR_REMOTE = REMOTE_FLEET_DIR + "_repair1"

WORK_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "cases" / CELL_NAME
STEP3_DIR = WORK_BASE / "step3"
SIM_OUT_DIR = WORK_BASE / "sim_out"
FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / CELL_NAME

OSM_ID_RAW = "way/442763908"
OSM_ID_STEM = "way_442763908"

LAT, LON = 33.8359, -118.3406
STATE = "CA"
EPSG = 32611

MAIN_JOB_ID = "965462"
EPW_STATION = "Torrance.Muni.AP-Zamperini.Field"

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

    print(f"[repair1] Regenerating {OSM_ID_RAW} ({OSM_ID_STEM}) ...")
    row_raw = gdf_raw[gdf_raw["osm_id"].astype(str) == OSM_ID_RAW]
    if len(row_raw) == 0:
        row_raw = gdf_raw[gdf_raw["osm_id"].astype(str) == OSM_ID_STEM]
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
    print(f"[repair1] Creating remote repair dir {REPAIR_DIR_REMOTE} ...")
    _ssh(f"mkdir -p {REPAIR_DIR_REMOTE}/idfs {REPAIR_DIR_REMOTE}/weather {REPAIR_DIR_REMOTE}/out")

    fleet_content = OSM_ID_STEM + "\n"
    fleet_remote = f"{REPAIR_DIR_REMOTE}/fleet.lst"
    fleet_local = STEP3_DIR / "repair1_fleet.lst"
    fleet_local.write_bytes(fleet_content.encode("utf-8"))
    subprocess.run(["scp", str(fleet_local), f"{REMOTE_HOST}:{fleet_remote}"],
                   check=True, timeout=30)

    print(f"[repair1] Uploading IDF via tar stream ...")
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz") as tf:
        tf.add(str(idf_path), arcname=f"idfs/{idf_path.name}")
    tar_buf.seek(0)
    proc2 = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc 'cd {REPAIR_DIR_REMOTE} && tar xz'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    proc2.stdin.write(tar_buf.read())
    proc2.stdin.close()
    proc2.wait(timeout=120)
    print(f"  IDF uploaded.")

    subprocess.run(["scp", str(epw_path), f"{REMOTE_HOST}:{REPAIR_DIR_REMOTE}/weather/"],
                   check=True, timeout=120)
    print(f"  EPW uploaded: {epw_path.name}")

    ep_dir_cmd = (
        "EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-*Ubuntu20* 2>/dev/null | head -1); "
        "[ -z \"$EP_DIR\" ] && EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-* | head -1)"
    )
    epw_remote = f"{REPAIR_DIR_REMOTE}/weather/{epw_path.name}"

    sbatch_script = f"""#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --time=01:30:00
#SBATCH --job-name=openubem_{CELL_NAME}_repair1
#SBATCH --output={REPAIR_DIR_REMOTE}/repair1_%A_%a.log

set -e
{ep_dir_cmd}
LINE=$(sed -n "${{SLURM_ARRAY_TASK_ID}}p" {fleet_remote})
IDF={REPAIR_DIR_REMOTE}/idfs/${{LINE}}.idf
OUTDIR={REPAIR_DIR_REMOTE}/out/${{LINE}}
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
    sbatch_remote_path = f"{REPAIR_DIR_REMOTE}/repair1_array.sbatch"
    with subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc 'cat > {sbatch_remote_path}'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ) as proc3:
        proc3.stdin.write(sbatch_script.encode("utf-8").replace(b"\r\n", b"\n"))
        proc3.stdin.close()
        proc3.wait(timeout=30)

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
    print(f"  Repair1 array job ID: {job_id}")
    return job_id


def poll_cluster(job_id: str, poll_interval_s: int = 60) -> None:
    print(f"[repair1] Polling job {job_id} (every {poll_interval_s}s) ...")
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


def fetch_result() -> None:
    print(f"[repair1] Fetching {OSM_ID_STEM} by explicit path ...")
    out_dir = SIM_OUT_DIR / OSM_ID_STEM
    out_dir.mkdir(parents=True, exist_ok=True)

    fetch_cmd = (
        f"cd {REPAIR_DIR_REMOTE}/out && tar czf - "
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
    print(f"[repair1] IDF manifest updated: {len(mf)} rows, "
          f"success={(mf['generation_status']=='success').sum()}")
    return mf


def update_sim_manifest(idf_manifest: pd.DataFrame, epw_path: Path) -> pd.DataFrame:
    old_mf = pd.read_parquet(WORK_BASE / "04_simulation_manifest.parquet")
    print(f"[repair1] Old sim manifest: {len(old_mf)} rows")

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

    # Replace the failed row in the old manifest
    old_idx = old_mf.index[old_mf["osm_id"].astype(str) == OSM_ID_RAW]
    if len(old_idx) > 0:
        sim_mf = old_mf.copy()
        i = old_idx[0]
        sim_mf.loc[i, "idf_path"] = str(STEP3_DIR / "idfs" / f"{OSM_ID_STEM}.idf")
        sim_mf.loc[i, "work_dir"] = str(bdir)
        sim_mf.loc[i, "sql_path"] = str(sql_path) if sql_path.exists() else ""
        sim_mf.loc[i, "status"] = status
        sim_mf.loc[i, "n_warnings"] = n_warnings
        sim_mf.loc[i, "n_severe"] = n_severe
        sim_mf.loc[i, "error_summary"] = error_summary
    else:
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
    print(f"[repair1] Sim manifest updated: {len(sim_mf)} rows, status={status_counts}")
    assert (sim_mf["status"] == "failed").sum() == 0, "Still have failed rows"
    return sim_mf


def main() -> None:
    print(f"[repair1] V12 la_suburban repair1: {OSM_ID_RAW}")
    print(f"[repair1] Working dir: {WORK_BASE}")
    assert WORK_BASE.exists(), f"Working dir not found: {WORK_BASE}"
    assert (WORK_BASE / "04_simulation_manifest.parquet").exists(), \
        "04_simulation_manifest.parquet not found — run main fetch first"

    epw_candidates = list((WORK_BASE / "weather").rglob("*.epw"))
    assert epw_candidates, f"No EPW found under {WORK_BASE / 'weather'}"
    epw_path = epw_candidates[0]
    print(f"[repair1] EPW: {epw_path.name}")

    gdf_raw = gpd.read_file(str(WORK_BASE / "01_buildings.gpkg"))
    print(f"[repair1] Loaded {len(gdf_raw)} buildings from 01_buildings.gpkg")

    idf_path = regenerate_idf(epw_path, gdf_raw)
    job_id = upload_and_submit(idf_path, epw_path)
    poll_cluster(job_id, poll_interval_s=60)
    fetch_result()
    idf_manifest = update_idf_manifest(idf_path)
    sim_mf = update_sim_manifest(idf_manifest, epw_path)

    print(f"\n[repair1] COMPLETE — way/442763908 repaired.")
    print(f"  Cluster job: {job_id}")
    print(f"  sim manifest: {len(sim_mf)} rows, all success")


if __name__ == "__main__":
    main()
