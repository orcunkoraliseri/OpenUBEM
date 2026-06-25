"""One-off recovery: fetch + parse + aggregate the Phase-D la_urban pilot.

The cluster array 987150 completed 618/618 (all "EnergyPlus Completed Successfully")
but the local fetch/aggregate never ran. Local intermediate state is intact:
  - <temp>/ubem_validation/phaseD/la_urban/step3/03_idf_manifest.parquet  (+ 618 IDFs)
  - 01_buildings.gpkg, 02a_climate_epw.parquet, cached EPW
Remote results sit at /speed-scratch/o_iseri/fleets/phaseD_la_urban/out/.

This driver replays ONLY the tail of run_cell (fetch -> verify -> sim manifest ->
step5 aggregate -> gates report -> copy final). It does NOT regenerate IDFs and does
NOT submit a new array.
"""
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "scripts" / "validation"))
import v12_cell_pipeline as P  # noqa: E402

CELL = "la_urban"
SUBDIR = "phaseD"
JOB_ID = "987150"

cfg_cell = P.CELL_CONFIGS[CELL]
lat, lon = cfg_cell["lat"], cfg_cell["lon"]
state, epsg = cfg_cell["state"], cfg_cell["epsg"]
radius_m = cfg_cell["radius_m"]

work_base = Path(tempfile.gettempdir()) / "ubem_validation" / SUBDIR / CELL
step3_dir = work_base / "step3"
sim_out_dir = work_base / "sim_out"
results_dir = work_base / "results"
final_dir = P.REPO / "docs" / "validations" / "overAll" / "results" / SUBDIR / CELL
remote_fleet_dir = f"/speed-scratch/o_iseri/fleets/{SUBDIR}_{CELL}"

print(f"[recover] work_base = {work_base}")
print(f"[recover] final_dir = {final_dir}")
print(f"[recover] remote    = {remote_fleet_dir}")

manifest_path = step3_dir / "03_idf_manifest.parquet"
if not manifest_path.exists():
    sys.exit(f"FATAL: manifest not found at {manifest_path} — cannot recover.")
idf_manifest = pd.read_parquet(manifest_path)

epw_path, epw_station_name = P.resolve_epw(lat, lon, work_base / "weather")

success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
n_generated = len(success_rows)
n_gen_total = len(idf_manifest)
osm_ids = [Path(str(r["idf_path"])).stem for _, r in success_rows.iterrows()]
print(f"[recover] manifest: {n_generated}/{n_gen_total} generation success")

print(f"\n[recover] Fetching results from cluster ...")
P.fetch_results(osm_ids, remote_fleet_dir, sim_out_dir)

# 0 fatals already confirmed on cluster; verify_and_repair returns [] when no fails.
repaired = P.verify_and_repair(osm_ids, sim_out_dir, step3_dir,
                               remote_fleet_dir, CELL, epw_path,
                               gdf=None, schedule_library=None)
if repaired:
    print(f"[recover] WARNING: repair path triggered: {repaired}")

print(f"\n[recover] Building simulation manifest ...")
sim_mf = P.build_sim_manifest(idf_manifest, sim_out_dir, epw_path, JOB_ID, step3_dir, work_base)
n_sim_total = len(sim_mf)
n_sim_success = int((sim_mf["status"] == "success").sum())
print(f"[recover] Simulation: {n_sim_success}/{n_sim_total} success")
if n_sim_success != n_sim_total:
    failed = sim_mf[sim_mf["status"] != "success"]
    for _, row in failed.iterrows():
        print(f"  FAIL osm_id={row['osm_id']} err={str(row['error_summary'])[:200]}")

print(f"\n[recover] Running Step 5 aggregate ...")
results_gdf, cbecs_gates = P.step5_results(
    idf_manifest, sim_mf, epw_path, results_dir, work_base, state, epsg, CELL
)

gates_text = P.write_gates_report(
    idf_manifest, sim_mf, results_gdf, cbecs_gates,
    epw_station_name=epw_station_name,
    gen_elapsed_s=0.0,
    job_id=JOB_ID,
    gen_success=n_generated,
    gen_total=n_gen_total,
    fetched_count=n_generated,
    cell_name=CELL,
    cfg_lat=lat,
    cfg_lon=lon,
    cfg_radius=radius_m,
    results_dir=results_dir,
)
(results_dir / f"v12_{CELL}_gates_report.txt").write_text(gates_text, encoding="utf-8")

copied = P.copy_final_deliverables(results_dir, final_dir, work_base)
print(f"\n[recover] Copied {len(copied)} files to {final_dir}")
print(f"[recover] DONE — Phase-D la_urban aggregated to {final_dir / '05_results.gpkg'}")
