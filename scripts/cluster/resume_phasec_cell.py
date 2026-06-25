# -*- coding: utf-8 -*-
"""Resume a v12 cell pipeline AFTER an already-submitted SLURM array.

Recovery glue ONLY: the local driver (run_cell) was killed after
ship_to_cluster + submit_cluster_array, but the SLURM array is still running
on the cluster. This re-enters the pipeline at poll -> fetch -> repair ->
sim_manifest -> step5 -> copy_final using the EXISTING job_id, without
re-shipping or re-submitting a duplicate array.

It imports and calls the existing v12_cell_pipeline functions verbatim;
no core/builder/math module is modified. Inputs (state, epsg, dirs, remote
fleet dir) are derived exactly as run_cell derives them.

Usage:
    py -3 scripts/cluster/resume_phasec_cell.py <cell_name> <job_id> \
        [--output-subdir phaseC]
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "validation"))

import v12_cell_pipeline as P  # noqa: E402

EXCLUDE_GEOMETRY_FATAL = {"way_402036180", "relation_6374725"}


def resume_cell(cell_name: str, job_id: str, output_subdir: str = "phaseC") -> None:
    cfg_cell = P.CELL_CONFIGS[cell_name]
    lat = cfg_cell["lat"]
    lon = cfg_cell["lon"]
    radius_m = cfg_cell["radius_m"]
    state = cfg_cell["state"]
    epsg = cfg_cell["epsg"]

    work_base = Path(tempfile.gettempdir()) / "ubem_validation" / output_subdir / cell_name
    step3_dir = work_base / "step3"
    sim_out_dir = work_base / "sim_out"
    results_dir = work_base / "results"
    final_dir = P.REPO / "docs" / "validations" / "overAll" / "results" / output_subdir / cell_name
    fleet_tag = cell_name if output_subdir == "cases" else f"{output_subdir}_{cell_name}"
    remote_fleet_dir = f"/speed-scratch/o_iseri/fleets/{fleet_tag}"

    manifest_path = step3_dir / "03_idf_manifest.parquet"
    if not manifest_path.exists():
        print(f"[{cell_name}] FATAL: no step3 manifest at {manifest_path}. "
              f"Cannot resume — IDFs must already be generated.", file=sys.stderr)
        sys.exit(3)
    idf_manifest = pd.read_parquet(str(manifest_path))

    print(f"\n{'='*72}")
    print(f"[{cell_name}] RESUMING from job {job_id} (post-submit re-entry)")
    print(f"[{cell_name}] Working dir: {work_base}")
    print(f"[{cell_name}] Remote fleet: {remote_fleet_dir}")
    print(f"[{cell_name}] Final dir:   {final_dir}")
    print(f"{'='*72}\n")

    # EPW resolution reuses cached weather under work_base/weather (no re-download).
    epw_path, epw_station_name = P.resolve_epw(lat, lon, work_base / "weather")

    n_generated = int((idf_manifest["generation_status"] == "success").sum())
    n_gen_total = len(idf_manifest)
    print(f"[{cell_name}] Step 3 (cached): {n_generated}/{n_gen_total} generated")

    # n_fetched lower bound: recover from cached step1 buildings if present.
    n_fetched = n_gen_total
    b1 = work_base / "01_buildings.gpkg"
    if b1.exists():
        try:
            import geopandas as gpd
            n_fetched = len(gpd.read_file(str(b1)))
        except Exception:
            n_fetched = n_gen_total

    print(f"\n[{cell_name}] Polling existing job {job_id} ...")
    P.poll_cluster(job_id, cell_name, poll_interval_s=90)

    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    osm_ids = [Path(str(r["idf_path"])).stem for _, r in success_rows.iterrows()]

    print(f"\n[{cell_name}] Fetching results ...")
    P.fetch_results(osm_ids, remote_fleet_dir, sim_out_dir)

    repaired = P.verify_and_repair(osm_ids, sim_out_dir, step3_dir,
                                   remote_fleet_dir, cell_name, epw_path)
    if repaired:
        print(f"[{cell_name}] Repaired and resimulated: {repaired}")

    # Manager-approved geometry-fatal exclusion (logged, not silent).
    excl_mask = idf_manifest["idf_path"].apply(
        lambda p: Path(str(p)).stem in EXCLUDE_GEOMETRY_FATAL
    )
    n_excluded = int(excl_mask.sum())
    idf_manifest_sim = idf_manifest[~excl_mask].copy()
    print(f"[{cell_name}] EXCLUDED (geometry-fatal, manager-approved): "
          f"way_402036180 (non-planar/CheckConvexity), "
          f"relation_6374725 (interzone vertex mismatch)")

    print(f"\n[{cell_name}] Building simulation manifest ...")
    sim_mf = P.build_sim_manifest(idf_manifest_sim, sim_out_dir, epw_path, job_id,
                                  step3_dir, work_base)

    n_sim_total = len(sim_mf)
    n_sim_success_count = int((sim_mf["status"] == "success").sum())
    n_sim_fail = n_sim_total - n_sim_success_count
    print(f"[{cell_name}] Simulation: {n_sim_success_count}/{n_sim_total} success, {n_sim_fail} failed")
    if n_sim_fail > 0:
        failed_rows = sim_mf[sim_mf["status"] != "success"]
        for _, row in failed_rows.iterrows():
            print(f"  osm_id={row['osm_id']}, error={str(row['error_summary'])[:200]}")
        print(f"[{cell_name}] ZERO-FAIL: still {n_sim_fail} unresolved. STOP.", file=sys.stderr)
        sys.exit(2)

    print(f"\n[{cell_name}] Running Step 5 ...")
    results_gdf, cbecs_gates = P.step5_results(
        idf_manifest_sim, sim_mf, epw_path, results_dir, work_base, state, epsg, cell_name
    )

    gates_text = P.write_gates_report(
        idf_manifest_sim, sim_mf, results_gdf, cbecs_gates,
        epw_station_name=epw_station_name,
        gen_elapsed_s=0.0,
        job_id=job_id,
        gen_success=n_generated,
        gen_total=n_gen_total,
        fetched_count=n_fetched,
        cell_name=cell_name,
        cfg_lat=lat,
        cfg_lon=lon,
        cfg_radius=radius_m,
        results_dir=results_dir,
    )
    gates_report_path = results_dir / f"v12_{cell_name}_gates_report.txt"
    gates_report_path.write_text(gates_text, encoding="utf-8")

    n_sim_headline = n_sim_success_count
    n_total_headline = n_sim_headline + n_excluded
    exclusion_section = (
        f"\n\n{'='*72}\n"
        f"EXCLUSIONS (geometry-fatal, manager-approved 2026-06-18): "
        f"{n_excluded} buildings — way_402036180, relation_6374725\n"
        f"  way_402036180   : non-planar surfaces (CheckConvexity fatal)\n"
        f"  relation_6374725: core/perimeter interzone vertex-count mismatch fatal\n"
        f"HEADLINE: {n_sim_headline}/{n_total_headline} "
        f"({n_sim_headline} simulated, {n_excluded} excluded)\n"
        f"{'='*72}\n"
    )
    with open(gates_report_path, "a", encoding="utf-8") as fh:
        fh.write(exclusion_section)
    print(f"[{cell_name}] Gates report -> {gates_report_path}")
    print(f"[{cell_name}] HEADLINE: {n_sim_headline}/{n_total_headline} "
          f"({n_sim_headline} simulated, {n_excluded} excluded)")

    copied = P.copy_final_deliverables(results_dir, final_dir, work_base)
    print(f"[{cell_name}] Copied {len(copied)} files to {final_dir}")
    print(f"\n[{cell_name}] DONE (resumed).")
    print(f"  Generated: {n_generated}/{n_gen_total}")
    print(f"  Simulated: {n_sim_headline}/{n_total_headline} "
          f"({n_excluded} geometry-fatal excluded)")
    print(f"  Job ID:    {job_id}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cell_name", choices=list(P.CELL_CONFIGS))
    ap.add_argument("job_id")
    ap.add_argument("--output-subdir", default="phaseC")
    args = ap.parse_args()
    resume_cell(args.cell_name, args.job_id, output_subdir=args.output_subdir)
