"""T08 — Full 4-mode x 12-cell sweep: Steps 1-3 locally + fire-and-forget sbatch.

Runs Steps 1-3 locally for ALL 12 validation cells across all four modes
(auto / building / floor / fast_zone), ships each (mode x cell) fleet to Speed,
submits sbatch --array for each (48 jobs total), prints all job IDs, and EXITS.

ABSOLUTE RULE: this script NEVER polls or blocks on cluster progress.
Cluster top-rule (no login-node compute): only sbatch is used on Speed.

AMENDMENT 2026-06-29:
- The auto orient() gate is fixed but uncommitted. Confirm builder.py has
  `if self.resolution_mode != "auto":` before `orient()` before running.
- All IDFs regenerated from the CURRENT working tree (do NOT reuse T07 IDFs).
- Output trimming (trim_outputs=True): hourly per-zone Output:Variable skipped
  so SQL stays small for fast_zone city passes (else >800 GB per city).

After cluster completion, check with:
    ssh o_iseri@speed.encs.concordia.ca "squeue -u o_iseri"
Then harvest:
    py -3 scripts/cluster/t08_harvest_results.py

Usage (local machine only):
    py -3 scripts/cluster/t08_full_sweep.py [--modes auto building floor fast_zone]
    py -3 scripts/cluster/t08_full_sweep.py --cells la_rural nyc_rural   (subset for testing)
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
_FLEET_TAG = "t08"
_REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"

PHASED_RESULTS = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
)

ALL_MODES = ["auto", "building", "floor", "fast_zone"]

# 12 validation cells (NYC 4A / LA 3B / Austin 2A). Coords from v12_cell_pipeline.py.
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
    """AMENDMENT requirement: confirm the auto orient() gate is present in builder.py."""
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

    # Resolve EPW
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
        trim_outputs=True,   # T08: skip hourly zone variables to keep SQL small
    )
    elapsed = time.monotonic() - t0

    # R07 (RULING D, OPEN-30): copy vintage_standard from the frame the builder
    # was handed onto the manifest -- same process, same moment, nothing
    # recomputed -- so both harvests can read it without re-deriving it.
    vintage_lookup = pd.DataFrame({
        "osm_id": gdf["osm_id"].astype(str),
        "vintage_standard": gdf["vintage_standard"].astype(str),
    }).drop_duplicates(subset="osm_id")
    manifest["osm_id"] = manifest["osm_id"].astype(str)
    manifest = manifest.merge(vintage_lookup, on="osm_id", how="left")

    n_ok = int((manifest["generation_status"] == "success").sum())
    print(f"    [{cell}/{mode}] {n_ok}/{len(manifest)} success in {elapsed:.1f}s")
    manifest.to_parquet(str(mode_dir / "03_manifest.parquet"), index=False)

    if mode == "fast_zone":
        pc_rows = manifest[manifest["zoning_strategy"] == "perimeter_core"]
        fb = pc_rows[pc_rows["num_zones"] == 1]
        print(f"    [fast_zone/{cell}] perimeter_core fallbacks: {len(fb)}/{len(pc_rows)}")

    return manifest


# ── Cluster: ship one (cell, mode) fleet ─────────────────────────────────────

def ship_fleet(manifest: pd.DataFrame, epw_path: Path, cell: str, mode: str) -> int:
    """Upload IDFs + EPW + fleet.lst for one (cell, mode). Returns n_submitted."""
    remote_dir = _remote_fleet_dir(cell, mode)
    _ssh(f"mkdir -p {remote_dir}/idfs {remote_dir}/weather {remote_dir}/out")

    success = manifest[manifest["generation_status"] == "success"]
    # fleet.lst uses filesystem stems (osm_id with / replaced by _)
    stems = [Path(str(r["idf_path"])).stem for _, r in success.iterrows()]

    # Upload fleet.lst
    lst_bytes = ("\n".join(stems) + "\n").encode("utf-8")
    proc = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc 'cat > {remote_dir}/fleet.lst'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    proc.stdin.write(lst_bytes)
    proc.stdin.close()
    proc.wait(timeout=30)

    # Upload EPW
    subprocess.run(
        ["scp", str(epw_path), f"{REMOTE_HOST}:{remote_dir}/weather/"],
        check=True, timeout=120,
    )

    # Upload IDFs as tar stream
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

    # Ensure latest trimmed sbatch script is on cluster
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
    parser = argparse.ArgumentParser(description="T08 full 4-mode x 12-cell sweep")
    parser.add_argument("--modes", nargs="+", default=ALL_MODES,
                        choices=ALL_MODES + ["all"],
                        help="Which modes to run (default: all 4)")
    parser.add_argument("--cells", nargs="+", default=list(CELL_CONFIGS.keys()),
                        choices=list(CELL_CONFIGS.keys()),
                        help="Which cells to run (default: all 12)")
    parser.add_argument("--n-jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2),
                        help="Worker processes for Step 3 (default: cpu_count-2)")
    args = parser.parse_args()

    modes = [m for m in args.modes if m != "all"] or ALL_MODES
    cells = args.cells
    n_jobs = args.n_jobs

    work_base = Path(tempfile.gettempdir()) / "ubem_t08_sweep"
    work_base.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(f"T08 full sweep — {len(cells)} cells x {len(modes)} modes")
    print(f"  Work dir:  {work_base}")
    print(f"  Modes:     {modes}")
    print(f"  Cells:     {cells}")
    print(f"  n_jobs:    {n_jobs}")
    print(f"  Trimmed:   trim_outputs=True (no hourly zone variables)")
    print("=" * 72)

    # AMENDMENT gate: verify orient() fix is in the working tree
    print("\n[AMENDMENT CHECK] Verifying orient() gate in builder.py ...")
    _verify_orient_gate()

    job_ids: dict[str, str] = {}     # key: f"{cell}_{mode}"
    n_submitted: dict[str, int] = {}
    t_start = time.monotonic()

    for cell in cells:
        cfg = CELL_CONFIGS[cell]
        print(f"\n{'='*72}")
        print(f"  CELL: {cell}  (lat={cfg['lat']}, lon={cfg['lon']}, state={cfg['state']})")
        print(f"{'='*72}")

        # Load raw buildings from phaseE fixture
        fixture_dir = PHASED_RESULTS / cell
        buildings_path = fixture_dir / "01_buildings.gpkg"
        if not buildings_path.exists():
            print(f"  SKIP {cell}: 01_buildings.gpkg not found at {buildings_path}", file=sys.stderr)
            continue
        gdf_raw = gpd.read_file(str(buildings_path))
        print(f"  Loaded {len(gdf_raw)} buildings from {cell} fixture")

        # Step 2: enrich (once per cell, shared across modes)
        cell_work = work_base / cell
        cell_work.mkdir(parents=True, exist_ok=True)

        print(f"  Step 2: semantic enrichment for {cell} ...")
        t2 = time.monotonic()
        gdf_57, schedule_library, epw_path = run_step2(gdf_raw, cell, cfg, work_base)
        print(f"  Step 2 complete in {time.monotonic()-t2:.1f}s, {len(gdf_57)} buildings")

        # Step 3 + ship + submit: one per mode
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

    # Save job IDs
    job_id_path = work_base / "t08_job_ids.json"
    job_id_path.write_text(json.dumps({
        "job_ids": job_ids,
        "n_submitted": n_submitted,
        "modes": modes,
        "cells": cells,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }, indent=2))

    elapsed = time.monotonic() - t_start

    # Summary
    print("\n" + "=" * 72)
    print(f"T08 FIRE-AND-FORGET SUBMISSION COMPLETE ({elapsed/60:.1f} min total)")
    print(f"  Work dir:     {work_base}")
    print(f"  Job IDs file: {job_id_path}")
    print()
    total_submitted = sum(n_submitted.values())
    total_jobs = len(job_ids)
    print(f"  Total sbatch arrays submitted: {total_jobs} ({len(cells)} cells x {len(modes)} modes)")
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
    print("  py -3 scripts/cluster/t08_harvest_results.py")
    print("=" * 72)
    print("STOPPED (no polling). Never srun on the login node.")


if __name__ == "__main__":
    main()
