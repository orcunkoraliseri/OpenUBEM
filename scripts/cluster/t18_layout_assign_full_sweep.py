"""T18 — Full 12-cell layout_assign cluster sweep, post-debug-fix (Steps 1-3 locally + fire-and-forget sbatch).

Minimal derivative of t17_layout_assign_full_sweep.py (plan §5 T11: reuse T17's
proven infrastructure byte-for-byte, changing only the fleet tag / output paths
so this run's job-ids file and remote fleet dirs don't collide with T17's
already-completed ones -- same "minimal derivative" pattern T17 itself used
when it forked from t08_full_sweep.py).

Diffs vs. t17_layout_assign_full_sweep.py (all documented here, per the same
convention T17 used for its own diff-vs-t08 docstring):
  1. _FLEET_TAG "t17" -> "t18" (remote dir / job-name prefix only; the sbatch
     script itself, SBATCH_LOCAL/SBATCH_REMOTE, and its FLEET_DIR contract are
     UNCHANGED and byte-for-byte reused -- it is fleet-content-agnostic, so no
     new sbatch file is needed. Using a distinct tag avoids conflating this
     task's remote fleet dirs with T17's already-harvested ones; it does not
     change array sizing/node config/packaging mechanics in any way).
  2. work_base tmp dir "ubem_t17_sweep" -> "ubem_t18_sweep" (own job-ids file,
     does not collide with/overwrite T17's own sweep state).
  3. job_id_path filename "t17_job_ids.json" -> "t18_job_ids.json".
  4. CELL_CONFIGS, ALL_MODES (single-element ["layout_assign"]), _verify_orient_gate(),
     run_step2/run_step3_mode/ship_fleet/submit_array bodies: byte-for-byte identical
     to T17 -- this run applies plan §5 T01/T02/T04's layout_assigner.py fixes (DHW
     Peak_Use_Flow_Rate + 4 sibling fields, FluidCooler:TwoSpeed capacity fields),
     which are already live in the imported openubem package -- no script-level change
     needed to pick them up.

This run is against the SAME 12 cells / SAME 8,160-building fleet as T17, with
this plan's fixes applied; everything E-LA-07-class-2/08, E-LA-09/11/12/13,
E-LA-14 remain OPEN-BLOCKED/unfixed exactly as at T10's local-regression gate
(CP-D signed) -- this sweep does not change layout_assigner.py/builder.py, it
only re-runs the pipeline with the already-committed code from CP-D.

ABSOLUTE RULE: this script NEVER polls or blocks on cluster progress.
Cluster top-rule (no login-node compute): only sbatch is used on Speed.

After cluster completion, check with:
    ssh o_iseri@speed.encs.concordia.ca "squeue -u o_iseri"
Then harvest:
    py -3 scripts/cluster/t18_harvest_layout_assign.py

Usage (local machine only):
    py -3 scripts/cluster/t18_layout_assign_full_sweep.py
    py -3 scripts/cluster/t18_layout_assign_full_sweep.py --cells la_rural   (subset for testing)
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
SBATCH_REMOTE = "/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet_t08.sbatch"
SBATCH_LOCAL = REPO / "scripts" / "cluster" / "submit_fleet_t08.sbatch"
_FLEET_TAG = "t18"
_REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"

PHASED_RESULTS = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
)

ALL_MODES = ["layout_assign"]

# 12 validation cells (NYC 4A / LA 3B / Austin 2A). Coords from v12_cell_pipeline.py.
# Identical to t17_layout_assign_full_sweep.py's CELL_CONFIGS -- byte-for-byte.
CELL_CONFIGS: dict[str, dict] = {
    "nyc_centre":    {"lat": 40.7549, "lon": -73.9840, "state": "NY"},
    "nyc_urban":     {"lat": 40.7721, "lon": -73.9301, "state": "NY"},
    "nyc_suburban":  {"lat": 40.7052, "lon": -73.5985, "state": "NY"},
    "nyc_rural":     {"lat": 42.0396, "lon": -74.1143, "state": "NY"},
    "la_centre":     {"lat": 34.0522, "lon": -118.2437, "state": "CA"},
    "la_urban":      {"lat": 34.0584, "lon": -118.3040, "state": "CA"},
    "la_suburban":   {"lat": 33.8359, "lon": -118.3406, "state": "CA"},
    "la_rural":      {"lat": 34.7420, "lon": -118.2130, "state": "CA"},
    "austin_centre": {"lat": 30.2672, "lon": -97.7431, "state": "TX"},
    "austin_urban":  {"lat": 30.3072, "lon": -97.7400, "state": "TX"},
    "austin_suburban": {"lat": 30.5085, "lon": -97.6789, "state": "TX"},
    "austin_rural":  {"lat": 30.5788, "lon": -98.2700, "state": "TX"},
}


# ── safety gate ───────────────────────────────────────────────────────────────

def _verify_orient_gate() -> None:
    """AMENDMENT requirement (T08, still applicable to layout_assign): confirm
    the auto orient() gate is present in builder.py."""
    builder_path = REPO / "openubem" / "idf" / "builder.py"
    src = builder_path.read_text(encoding="utf-8")
    gate = 'if self.resolution_mode != "auto":'
    if gate not in src:
        sys.exit(
            "STOP: orient() gate not found in builder.py.\n"
            "Expected: `if self.resolution_mode != \"auto\":` before the orient() call.\n"
            "Per AMENDMENT 2026-06-29, this gate must be present. Aborting."
        )
    print("  [GATE OK] builder.py has the auto orient() gate.")


# ── helpers ───────────────────────────────────────────────────────────────────

def _ssh(cmd: str, timeout: int = 120) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def _remote_fleet_dir(cell: str, mode: str) -> str:
    return f"{_REMOTE_FLEET_BASE}/{_FLEET_TAG}_{cell}_{mode}"


# ── Step 2: semantic enrichment ───────────────────────────────────────────────

def run_step2(gdf_raw: gpd.GeoDataFrame, cell: str, cfg: dict,
              work_base: Path) -> tuple[gpd.GeoDataFrame, object, Path]:
    """Enrich buildings for one cell. Returns (gdf_enriched, schedule_library, epw_path)."""
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics
    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw

    weather_dir = work_base / cell / "weather"
    weather_dir.mkdir(parents=True, exist_ok=True)
    stations = load_stations()
    station, dist_km = resolve_station(cfg["lat"], cfg["lon"], stations)
    print(f"    EPW station: {station.get('station_id')} at {dist_km:.1f} km")
    epw_path = fetch_epw(station, output_dir=weather_dir)
    print(f"    EPW: {epw_path}")

    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")

    gdf_26 = BuildingClassifier().classify(gdf_in)
    zone_df = assign_climate_zones(gdf_26)
    gdf_29 = gdf_26.copy()
    gdf_29["climate_zone"] = pd.Categorical(
        zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB)
    )
    gdf_29["epw_path"] = str(epw_path)
    gdf_29["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values,
        categories=["ASHRAE_STANDARD", "HEURISTIC"],
    )
    pd.DataFrame({
        "osm_id": gdf_26["osm_id"].values,
        "climate_zone": zone_df["climate_zone"].values,
        "climate_zone_method": zone_df["climate_zone_method"].values,
        "county_geoid": zone_df["county_geoid"].values,
        "state": zone_df["state"].values,
        "epw_path": str(epw_path),
        "provenance_climate_zone": zone_df["provenance_climate_zone"].values,
    }).to_parquet(str(work_base / cell / "02a_climate_epw.parquet"), index=False)

    gdf_57, schedule_library = enrich_semantics(gdf_29)
    return gdf_57, schedule_library, epw_path


# ── Step 3: IDF generation for one (cell, mode) ───────────────────────────────

def run_step3_mode(gdf: gpd.GeoDataFrame, schedule_lib: object,
                   cell: str, mode: str, work_base: Path, n_jobs: int) -> pd.DataFrame:
    from openubem.idf.builder import run_step3

    mode_dir = work_base / cell / f"step3_{mode}"
    mode_dir.mkdir(parents=True, exist_ok=True)
    (mode_dir / "idfs").mkdir(exist_ok=True)

    print(f"    Step 3 [{cell}/{mode}] n={len(gdf)} n_jobs={n_jobs} trim_outputs=True ...")
    t0 = time.monotonic()
    manifest = run_step3(
        gdf, schedule_lib, mode_dir,
        n_jobs=n_jobs,
        resolution_mode=mode,
        trim_outputs=True,   # same as T17/T08: skip hourly zone variables to keep SQL small
    )
    elapsed = time.monotonic() - t0

    n_ok = int((manifest["generation_status"] == "success").sum())
    print(f"    [{cell}/{mode}] {n_ok}/{len(manifest)} success in {elapsed:.1f}s")
    manifest.to_parquet(str(mode_dir / "03_manifest.parquet"), index=False)

    if "zoning_strategy" in manifest.columns:
        la_rows = manifest[manifest["zoning_strategy"] == "layout_assign"]
        fb_rows = manifest[
            manifest.get("data_quality_flag", pd.Series(dtype=str)).astype(str)
            .str.contains("layout_assign_fallback_auto", na=False)
        ]
        print(f"    [{cell}/{mode}] layout_assign baseline-scaled: {len(la_rows)}/{len(manifest)}; "
              f"fallback-to-auto (no baseline): {len(fb_rows)}/{len(manifest)}")

    return manifest


# ── Cluster: ship one (cell, mode) fleet ─────────────────────────────────────

def ship_fleet(manifest: pd.DataFrame, epw_path: Path, cell: str, mode: str) -> int:
    """Upload IDFs + EPW + fleet.lst for one (cell, mode). Returns n_submitted."""
    remote_dir = _remote_fleet_dir(cell, mode)
    _ssh(f"mkdir -p {remote_dir}/idfs {remote_dir}/weather {remote_dir}/out")

    success = manifest[manifest["generation_status"] == "success"]
    stems = [Path(str(r["idf_path"])).stem for _, r in success.iterrows()]

    lst_bytes = ("\n".join(stems) + "\n").encode("utf-8")
    proc = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc 'cat > {remote_dir}/fleet.lst'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    proc.stdin.write(lst_bytes)
    proc.stdin.close()
    proc.wait(timeout=30)

    subprocess.run(
        ["scp", str(epw_path), f"{REMOTE_HOST}:{remote_dir}/weather/"],
        check=True, timeout=120,
    )

    print(f"    Uploading {len(stems)} IDFs for {cell}/{mode} ...")
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz") as tf:
        for _, row in success.iterrows():
            src = Path(str(row["idf_path"]))
            tf.add(str(src), arcname=f"idfs/{src.name}")
    tar_buf.seek(0)
    proc2 = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc 'cd {remote_dir} && tar xz'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    proc2.stdin.write(tar_buf.read())
    proc2.stdin.close()
    proc2.wait(timeout=600)
    print(f"    Upload complete: {cell}/{mode}")
    return len(stems)


# ── Cluster: submit sbatch array (fire-and-forget) ───────────────────────────

def submit_array(n_jobs: int, cell: str, mode: str) -> str:
    """Submit sbatch --array for one (cell, mode). Returns job ID. NEVER polls."""
    remote_dir = _remote_fleet_dir(cell, mode)
    job_name = f"{_FLEET_TAG}_{cell}_{mode}"

    subprocess.run(
        ["scp", str(SBATCH_LOCAL), f"{REMOTE_HOST}:{SBATCH_REMOTE}"],
        check=False, timeout=60,
    )

    cmd = (
        f"sbatch --array=1-{n_jobs}%16 "
        f"--export=FLEET_DIR={remote_dir} "
        f"--job-name={job_name} "
        f"--output={remote_dir}/{job_name}_%A_%a.log "
        f"{SBATCH_REMOTE}"
    )
    print(f"    Submitting [{cell}/{mode}]: {cmd}")
    out = _ssh(cmd, timeout=60)

    job_id = ""
    for line in out.splitlines():
        if "Submitted batch job" in line:
            job_id = line.strip().split()[-1]
            break
    if not job_id:
        print(f"  WARNING: no job ID from sbatch for {cell}/{mode}:\n{out}", file=sys.stderr)
        return "FAILED"
    print(f"    [{cell}/{mode}] Job ID: {job_id}")
    return job_id


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="T18 full layout_assign x 12-cell sweep (post-debug-fix)")
    parser.add_argument("--modes", nargs="+", default=ALL_MODES,
                        choices=ALL_MODES,
                        help="Which modes to run (default: layout_assign only)")
    parser.add_argument("--cells", nargs="+", default=list(CELL_CONFIGS.keys()),
                        choices=list(CELL_CONFIGS.keys()),
                        help="Which cells to run (default: all 12)")
    parser.add_argument("--n-jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2),
                        help="Worker processes for Step 3 (default: cpu_count-2)")
    args = parser.parse_args()

    modes = args.modes
    cells = args.cells
    n_jobs = args.n_jobs

    work_base = Path(tempfile.gettempdir()) / "ubem_t18_sweep"
    work_base.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(f"T18 layout_assign full sweep (post-debug-fix) — {len(cells)} cells x {len(modes)} mode(s)")
    print(f"  Work dir:  {work_base}")
    print(f"  Modes:     {modes}")
    print(f"  Cells:     {cells}")
    print(f"  n_jobs:    {n_jobs}")
    print(f"  Trimmed:   trim_outputs=True (no hourly zone variables)")
    print("=" * 72)

    print("\n[AMENDMENT CHECK] Verifying orient() gate in builder.py ...")
    _verify_orient_gate()

    job_ids: dict[str, str] = {}
    n_submitted: dict[str, int] = {}
    t_start = time.monotonic()

    for cell in cells:
        cfg = CELL_CONFIGS[cell]
        print(f"\n{'='*72}")
        print(f"  CELL: {cell}  (lat={cfg['lat']}, lon={cfg['lon']}, state={cfg['state']})")
        print(f"{'='*72}")

        fixture_dir = PHASED_RESULTS / cell
        buildings_path = fixture_dir / "01_buildings.gpkg"
        if not buildings_path.exists():
            print(f"  SKIP {cell}: 01_buildings.gpkg not found at {buildings_path}", file=sys.stderr)
            continue
        gdf_raw = gpd.read_file(str(buildings_path))
        print(f"  Loaded {len(gdf_raw)} buildings from {cell} fixture")

        cell_work = work_base / cell
        cell_work.mkdir(parents=True, exist_ok=True)

        print(f"  Step 2: semantic enrichment for {cell} ...")
        t2 = time.monotonic()
        gdf_57, schedule_library, epw_path = run_step2(gdf_raw, cell, cfg, work_base)
        print(f"  Step 2 complete in {time.monotonic()-t2:.1f}s, {len(gdf_57)} buildings")

        for mode in modes:
            key = f"{cell}_{mode}"
            print(f"\n  --- Mode: {mode} ---")

            manifest = run_step3_mode(gdf_57, schedule_library, cell, mode, work_base, n_jobs)
            n_ok = int((manifest["generation_status"] == "success").sum())

            if n_ok == 0:
                print(f"  [{key}] ZERO successful IDFs — skipping cluster submit.", file=sys.stderr)
                continue

            n_sub = ship_fleet(manifest, epw_path, cell, mode)
            job_id = submit_array(n_sub, cell, mode)
            job_ids[key] = job_id
            n_submitted[key] = n_sub

    job_id_path = work_base / "t18_job_ids.json"
    job_id_path.write_text(json.dumps({
        "job_ids": job_ids,
        "n_submitted": n_submitted,
        "modes": modes,
        "cells": cells,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }, indent=2))

    elapsed = time.monotonic() - t_start

    print("\n" + "=" * 72)
    print(f"T18 FIRE-AND-FORGET SUBMISSION COMPLETE ({elapsed/60:.1f} min total)")
    print(f"  Work dir:     {work_base}")
    print(f"  Job IDs file: {job_id_path}")
    print()
    total_submitted = sum(n_submitted.values())
    total_jobs = len(job_ids)
    print(f"  Total sbatch arrays submitted: {total_jobs} ({len(cells)} cells x {len(modes)} mode(s))")
    print(f"  Total buildings submitted: {total_submitted}")
    print()
    print(f"  {'cell_mode':35s}  {'job_id':>12}  {'n':>6}")
    for cell in cells:
        for mode in modes:
            key = f"{cell}_{mode}"
            jid = job_ids.get(key, "NOT_SUBMITTED")
            n = n_submitted.get(key, 0)
            print(f"  {key:35s}  {jid:>12}  {n:>6}")
    print()
    print("MONITORING: check with (MINIMUM 30-min interval per project rule)")
    print("  ssh o_iseri@speed.encs.concordia.ca 'squeue -u o_iseri'")
    print("After ALL arrays complete, run:")
    print("  py -3 scripts/cluster/t18_harvest_layout_assign.py")
    print("=" * 72)
    print("STOPPED (no polling). Never srun on the login node.")


if __name__ == "__main__":
    main()
