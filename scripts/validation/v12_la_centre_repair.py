"""V12 la_centre repair: regenerate way/427817502 and way/427817541 with single_zone fallback.

Diagnosis: perimeter_core zoning on simplified polygons creates interzone
vertex mismatches (ceiling<->floor cross-zone-type pairs between non-adjacent
perimeter wedges) that _repair_mismatched_horizontal_pairs does not catch.

Fix: force single_zone for these two buildings only.
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

REPAIR_TARGETS = ["way/427817502", "way/427817541"]

import tempfile
WORK_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "cases" / CELL_NAME
STEP3_DIR = WORK_BASE / "step3"
SIM_OUT_DIR = WORK_BASE / "sim_out"
RESULTS_DIR = WORK_BASE / "results"
FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / CELL_NAME

LAT, LON = 34.0522, -118.2437
STATE = "CA"
EPSG = 32611

_floor_rx = _re.compile(r"_F(\d+)_")


def _ssh(cmd: str, timeout: int = 120) -> str:
    result = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return result.stdout + result.stderr


def regenerate_idf(osm_id_raw: str, epw_path: Path, gdf_raw: gpd.GeoDataFrame) -> Path:
    from geomeppy import IDF as GeomIDF
    from eppy.modeleditor import IDDAlreadySetError
    from openubem import config
    from openubem.geometry.footprint import simplify_footprint, translate_to_origin, derive_num_floors
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

    osm_id_stem = osm_id_raw.replace("/", "_")
    print(f"[repair] Regenerating {osm_id_raw} ({osm_id_stem}) ...")

    row_raw = gdf_raw[gdf_raw["osm_id"].astype(str) == osm_id_raw]
    assert len(row_raw) == 1, f"Expected 1 row for {osm_id_raw}, got {len(row_raw)}"
    print(f"  footprint={row_raw.iloc[0].get('footprint_area_m2', 0.0):.1f} m2")

    # Reset index to 0-based so GeoDataFrame(geometry=geoseries) index-aligns correctly.
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

    from openubem.geometry.zoning import decide_zoning_strategy
    geom = row_enriched["geometry"]
    dq_flag = str(row_enriched.get("data_quality_flag", "") or "")
    poly, dq_flag2, simp_status = simplify_footprint(geom, dq_flag)
    poly_local, cx, cy = translate_to_origin(poly)
    num_floors = derive_num_floors(row_enriched)
    footprint_area = float(row_enriched.get("footprint_area_m2") or poly.area)
    orig_strategy = decide_zoning_strategy(row_enriched["archetype_id"], footprint_area, num_floors)
    print(f"  simp={simp_status}, floors={num_floors}, area={footprint_area:.1f}, original_strategy={orig_strategy}")

    from importlib.resources import files
    template_path = str(files("openubem.idf").joinpath("templates").joinpath("commercial_base.idf"))
    idf_test = GeomIDF(template_path)
    zones_bad = build_zones(osm_id_raw, poly_local, row_enriched["archetype_id"], num_floors, orig_strategy)
    extrude_geometry(idf_test, zones_bad, [])
    mismatched = find_mismatched_interzone_pairs(idf_test)
    print(f"  mismatched pairs with {orig_strategy}: {len(mismatched)}")

    print(f"[repair] Regenerating with single_zone fallback ...")
    repair_strategy = "single_zone"

    idf_out_path = STEP3_DIR / "idfs" / f"{osm_id_stem}.idf"
    idf_out_path.parent.mkdir(parents=True, exist_ok=True)

    bldg = BuildingIDF(row_enriched)
    bldg_geom = row_enriched["geometry"]
    dq_orig = str(row_enriched.get("data_quality_flag", "") or "")
    poly_r, dq_r, simp_r = simplify_footprint(bldg_geom, dq_orig)
    poly_local_r, cx_r, cy_r = translate_to_origin(poly_r)
    nf = derive_num_floors(row_enriched)
    fa = float(row_enriched.get("footprint_area_m2") or poly_r.area)

    zones_ok = build_zones(osm_id_raw, poly_local_r, row_enriched["archetype_id"], nf, repair_strategy)

    row_ctx = row_enriched.copy()
    row_ctx["_simplified_geom"] = poly_r
    context = discover_context(row_ctx, gdf_raw, cx_r, cy_r, config.SHADING_SPHERE_RADIUS)
    bldg.copy_schedule_library(row_enriched["archetype_id"], schedule_library)
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
    assign_hvac(bldg.idf, row_enriched, extruded_zones)
    write_outputs(bldg.idf)
    bldg.idf.save(str(idf_out_path))
    print(f"  IDF saved: {idf_out_path}")

    return idf_out_path


def upload_and_submit_repair_array(idf_paths: list[Path], epw_path: Path) -> str:
    print(f"[repair] Uploading {len(idf_paths)} repaired IDFs to cluster ...")
    for idf_path in idf_paths:
        subprocess.run(["scp", str(idf_path), f"{REMOTE_HOST}:{REMOTE_FLEET_DIR}/idfs/"],
                       check=True, timeout=60)
        print(f"  uploaded: {idf_path.name}")

    stems = [p.stem for p in idf_paths]
    ep_dir_cmd = (
        "EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-*Ubuntu20* 2>/dev/null | head -1); "
        "[ -z \"$EP_DIR\" ] && EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-* | head -1)"
    )
    epw_remote = f"{REMOTE_FLEET_DIR}/weather/{epw_path.name}"

    repair_fleet_dir = REMOTE_FLEET_DIR + "_repair"
    _ssh(f"mkdir -p {repair_fleet_dir}/idfs {repair_fleet_dir}/weather {repair_fleet_dir}/out")

    for idf_path in idf_paths:
        subprocess.run(["scp", str(idf_path), f"{REMOTE_HOST}:{repair_fleet_dir}/idfs/"],
                       check=True, timeout=60)

    subprocess.run(["scp", str(epw_path), f"{REMOTE_HOST}:{repair_fleet_dir}/weather/"],
                   check=True, timeout=120)

    fleet_content = "\n".join(stems) + "\n"
    fleet_remote = f"{repair_fleet_dir}/fleet.lst"
    write_cmd = f"printf '%s' '{fleet_content}' > {fleet_remote}"
    _ssh(write_cmd, timeout=30)

    n = len(stems)
    sbatch_script = f"""#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --time=01:30:00
#SBATCH --job-name=openubem_{CELL_NAME}_repair
#SBATCH --output={repair_fleet_dir}/repair_%A_%a.log

set -e
{ep_dir_cmd}
LINE=$(sed -n "${{SLURM_ARRAY_TASK_ID}}p" {fleet_remote})
IDF={repair_fleet_dir}/idfs/${{LINE}}.idf
OUTDIR={repair_fleet_dir}/out/${{LINE}}
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
    sbatch_remote_path = f"{repair_fleet_dir}/repair_array.sbatch"
    write_sbatch_cmd = f"printf '%s\\n' {chr(39)}{sbatch_script}{chr(39)} > {sbatch_remote_path}"

    with subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc 'cat > {sbatch_remote_path}'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ) as proc:
        proc.stdin.write(sbatch_script.encode("utf-8").replace(b"\r\n", b"\n"))
        proc.stdin.close()
        proc.wait(timeout=30)

    out = _ssh(f"sbatch --array=1-{n}%32 {sbatch_remote_path}", timeout=60)
    print(f"  sbatch: {out.strip()}")
    job_id = ""
    for line in out.splitlines():
        if "Submitted batch job" in line:
            job_id = line.strip().split()[-1]
            break
    if not job_id:
        print(f"  ERROR: no job ID from sbatch: {out}", file=sys.stderr)
        sys.exit(2)
    print(f"  Repair array job ID: {job_id}")
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
            print(sacct_full[:2000])
            break


def fetch_repaired_results(stems: list[str]) -> None:
    repair_fleet_dir = REMOTE_FLEET_DIR + "_repair"
    print(f"[repair] Fetching repaired results by explicit path ...")
    for stem in stems:
        out_dir = SIM_OUT_DIR / stem
        out_dir.mkdir(parents=True, exist_ok=True)
        fetch_cmd = (
            f"cd {repair_fleet_dir}/out && tar czf - "
            f"{stem}/eplusout.sql {stem}/eplusout.err {stem}/eplusout.end"
        )
        proc = subprocess.Popen(
            ["ssh", REMOTE_HOST, f"bash -lc '{fetch_cmd}'"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout_data, stderr_data = proc.communicate(timeout=300)
        if stderr_data:
            msg = stderr_data.decode(errors="replace").strip()
            if msg:
                print(f"  fetch stderr for {stem}: {msg[:300]}")
        if stdout_data:
            with tarfile.open(fileobj=io.BytesIO(stdout_data), mode="r:gz") as tf:
                tf.extractall(str(SIM_OUT_DIR))
        end_path = SIM_OUT_DIR / stem / "eplusout.end"
        assert end_path.exists(), f"eplusout.end not found for {stem}"
        end_text = end_path.read_text(errors="replace")
        print(f"  {stem} eplusout.end: {end_text.strip()}")
        assert "EnergyPlus Completed Successfully" in end_text, f"Simulation still failed: {stem}: {end_text}"
        print(f"  PASS: {stem} EnergyPlus Completed Successfully")


def update_idf_manifest(repair_map: dict[str, str]) -> pd.DataFrame:
    """Update manifest entries for repaired buildings (osm_id_raw -> idf_path)."""
    idf_manifest = pd.read_parquet(STEP3_DIR / "03_idf_manifest.parquet")
    for osm_id_raw, idf_path_str in repair_map.items():
        row_idx = idf_manifest.index[idf_manifest["osm_id"].astype(str) == osm_id_raw]
        assert len(row_idx) == 1, f"Expected 1 row for {osm_id_raw}"
        idf_manifest.loc[row_idx[0], "idf_path"] = idf_path_str
        idf_manifest.loc[row_idx[0], "generation_status"] = "success"
        idf_manifest.loc[row_idx[0], "zoning_strategy"] = "single_zone"
        idf_manifest.loc[row_idx[0], "num_zones"] = 1
        idf_manifest.loc[row_idx[0], "data_quality_flag"] = (
            str(idf_manifest.loc[row_idx[0], "data_quality_flag"] or "") + "|single_zone_repair"
        )
    idf_manifest.to_parquet(STEP3_DIR / "03_idf_manifest.parquet", index=False)
    print(f"[repair] IDF manifest updated: {len(idf_manifest)} rows, "
          f"success={(idf_manifest['generation_status']=='success').sum()}")
    return idf_manifest


def main() -> None:
    print(f"[repair] V12 la_centre two-building repair: {REPAIR_TARGETS}")
    print(f"[repair] Working dir: {WORK_BASE}")

    epw_path = list((WORK_BASE / "weather").rglob("*.epw"))[0]
    print(f"[repair] EPW: {epw_path.name}")

    print(f"[repair] Loading 01_buildings.gpkg ...")
    gdf_raw = gpd.read_file(str(WORK_BASE / "01_buildings.gpkg"))
    print(f"  Loaded {len(gdf_raw)} buildings")

    idf_paths = []
    repair_map = {}
    for osm_id_raw in REPAIR_TARGETS:
        idf_path = regenerate_idf(osm_id_raw, epw_path, gdf_raw)
        idf_paths.append(idf_path)
        repair_map[osm_id_raw] = str(idf_path)

    job_id = upload_and_submit_repair_array(idf_paths, epw_path)

    poll_cluster(job_id, poll_interval_s=90)

    stems = [p.stem for p in idf_paths]
    fetch_repaired_results(stems)

    idf_manifest = update_idf_manifest(repair_map)

    print(f"\n[repair] COMPLETE. Both buildings repaired.")
    print(f"  Repair job ID: {job_id}")


if __name__ == "__main__":
    main()
