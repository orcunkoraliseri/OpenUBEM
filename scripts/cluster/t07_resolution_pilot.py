"""T07 — Resolution-mode pilot: Steps 1-3 locally + fire-and-forget sbatch submission.

Runs Steps 1-3 locally for a 21-building la_rural subset across all four modes
(auto / building / floor / fast_zone), ships 4 fleet dirs to the Speed cluster,
submits 4 sbatch --array jobs (one per mode), prints job IDs, and EXITS.

ABSOLUTE RULE: this script NEVER polls or blocks on cluster progress.
The cluster top-rule (no login-node compute) is obeyed: only sbatch is used.

After cluster completion, check with:
    ssh o_iseri@speed.encs.concordia.ca "squeue -u o_iseri"
Then harvest:
    py -3 scripts/cluster/t07_harvest_results.py

Usage (local machine only):
    py -3 scripts/cluster/t07_resolution_pilot.py
"""
from __future__ import annotations

import io
import json
import shutil
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
SBATCH_REMOTE = "/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet.sbatch"
SBATCH_LOCAL = REPO / "scripts" / "cluster" / "submit_fleet.sbatch"

# la_rural phaseE fixtures (all 149 buildings, all succeeded in phaseE)
_FIXTURE_DIR = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll"
    / "results" / "phaseE" / "la_rural"
)
_CELL_LAT = 34.7420
_CELL_LON = -118.2130
_CELL_STATE = "CA"

# Target subset: 21 buildings spanning all required archetypes
_TARGET_COUNTS = {
    "MidriseApartment": 5,
    "SmallOffice":      5,
    "MediumOffice":     5,
    "LargeOffice":      1,   # only 1 in la_rural
    "Warehouse":        5,
}

MODES = ["auto", "building", "floor", "fast_zone"]
_REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"
_FLEET_TAG = "t07"


# ── helpers ───────────────────────────────────────────────────────────────────

def _ssh(cmd: str, timeout: int = 120) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def _remote_fleet_dir(mode: str) -> str:
    return f"{_REMOTE_FLEET_BASE}/{_FLEET_TAG}_{mode}"


# ── Step 1: load raw buildings from phaseE fixture ────────────────────────────

def load_fixture_buildings() -> gpd.GeoDataFrame:
    path = _FIXTURE_DIR / "01_buildings.gpkg"
    if not path.exists():
        sys.exit(f"FATAL: fixture not found: {path}")
    gdf = gpd.read_file(str(path))
    print(f"  Loaded {len(gdf)} buildings from la_rural fixture")
    return gdf


# ── Step 2: semantic enrichment ───────────────────────────────────────────────

def run_step2(gdf_raw: gpd.GeoDataFrame, epw_path: Path,
              work_base: Path) -> tuple[gpd.GeoDataFrame, object]:
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")

    print(f"  Classifying {len(gdf_in)} buildings ...")
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
    }).to_parquet(str(work_base / "02a_climate_epw.parquet"), index=False)

    print("  Enriching semantics ...")
    gdf_57, schedule_library = enrich_semantics(gdf_29)
    print(f"  Enrichment complete: {len(gdf_57)} buildings")
    return gdf_57, schedule_library


# ── Subset selection ──────────────────────────────────────────────────────────

def select_subset(gdf_57: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Pick _TARGET_COUNTS buildings per archetype."""
    parts: list[pd.DataFrame] = []
    for arch, count in _TARGET_COUNTS.items():
        cands = gdf_57[gdf_57["archetype_id"] == arch]
        taken = cands.head(count)
        print(f"  {arch}: selected {len(taken)} (requested {count})")
        parts.append(taken)
    subset = pd.concat(parts, ignore_index=True)
    return gpd.GeoDataFrame(subset, geometry="geometry", crs=gdf_57.crs)


# ── Step 3: IDF generation for one mode ──────────────────────────────────────

def run_step3_mode(gdf: gpd.GeoDataFrame, schedule_lib: object,
                   mode: str, work_base: Path) -> pd.DataFrame:
    from openubem.idf.builder import run_step3

    mode_dir = work_base / f"step3_{mode}"
    mode_dir.mkdir(parents=True, exist_ok=True)
    (mode_dir / "idfs").mkdir(exist_ok=True)

    print(f"  Running Step 3 (mode={mode}, n={len(gdf)}) ...")
    t0 = time.monotonic()
    manifest = run_step3(gdf, schedule_lib, mode_dir, n_jobs=1, resolution_mode=mode)
    elapsed = time.monotonic() - t0

    n_ok = int((manifest["generation_status"] == "success").sum())
    print(f"  Step 3 [{mode}]: {n_ok}/{len(manifest)} success in {elapsed:.1f}s")

    # Save manifest alongside IDFs for harvest step (before any print that could fail on Windows)
    manifest.to_parquet(str(mode_dir / "03_manifest.parquet"), index=False)

    # Log fallbacks for fast_zone: perimeter_core rows that fell back (num_zones == 1)
    if mode == "fast_zone":
        pc_rows = manifest[manifest["zoning_strategy"] == "perimeter_core"]
        fallbacks = pc_rows[pc_rows["num_zones"] == 1]
        print(f"  [fast_zone] fallback rows (perimeter_core -> 1 zone): {len(fallbacks)}")
        for _, r in fallbacks.iterrows():
            print(f"    fallback: {r['osm_id']} ({r.get('archetype_id','?')}) num_zones=1")
    return manifest


# ── Cluster: ship one fleet dir ───────────────────────────────────────────────

def ship_fleet(manifest: pd.DataFrame, epw_path: Path, mode: str) -> int:
    """Upload IDFs + EPW + fleet.lst for one mode. Returns n_jobs submitted."""
    remote_dir = _remote_fleet_dir(mode)
    _ssh(f"mkdir -p {remote_dir}/idfs {remote_dir}/weather {remote_dir}/out")

    success = manifest[manifest["generation_status"] == "success"]
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
    print(f"  Uploading {len(stems)} IDFs for mode={mode} ...")
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
    proc2.wait(timeout=300)
    print(f"  Upload complete for mode={mode}.")
    return len(stems)


# ── Cluster: submit sbatch array (fire-and-forget) ───────────────────────────

def submit_array(n_jobs: int, mode: str) -> str:
    """Submit sbatch --array for one mode. Returns job ID. NEVER polls."""
    remote_dir = _remote_fleet_dir(mode)

    # Ensure latest sbatch script is on cluster
    subprocess.run(
        ["scp", str(SBATCH_LOCAL), f"{REMOTE_HOST}:{SBATCH_REMOTE}"],
        check=False, timeout=60,
    )

    cmd = (
        f"sbatch --array=1-{n_jobs}%16 "
        f"--export=FLEET_DIR={remote_dir} "
        f"--job-name={_FLEET_TAG}_{mode} "
        f"--output={remote_dir}/{_FLEET_TAG}_{mode}_%A_%a.log "
        f"{SBATCH_REMOTE}"
    )
    print(f"  Submitting [{mode}]: {cmd}")
    out = _ssh(cmd, timeout=60)

    job_id = ""
    for line in out.splitlines():
        if "Submitted batch job" in line:
            job_id = line.strip().split()[-1]
            break
    if not job_id:
        sys.exit(f"ERROR: no job ID from sbatch for mode={mode}:\n{out}")
    print(f"  [{mode}] Job ID: {job_id}")
    return job_id


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    work_base = Path(tempfile.gettempdir()) / "ubem_t07_pilot"
    work_base.mkdir(parents=True, exist_ok=True)
    print(f"T07 resolution pilot — work dir: {work_base}")
    print(f"Modes: {MODES}")
    print(f"Target subset: {_TARGET_COUNTS}")

    # Step 1
    print("\n=== Step 1: Load la_rural raw buildings ===")
    gdf_raw = load_fixture_buildings()

    # EPW
    print("\n=== Resolve EPW for la_rural ===")
    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw
    _stations = load_stations()
    _station, _dist_km = resolve_station(_CELL_LAT, _CELL_LON, _stations)
    print(f"  Resolved station: {_station['station_id']} at {_dist_km:.1f} km")
    (work_base / "weather").mkdir(parents=True, exist_ok=True)
    epw_path = fetch_epw(_station, output_dir=work_base / "weather")
    epw_station = _station.get("name", str(_station["station_id"]))
    print(f"  EPW: {epw_path}")
    print(f"  EPW: {epw_path}")

    # Step 2
    print("\n=== Step 2: Semantic enrichment ===")
    gdf_57, schedule_library = run_step2(gdf_raw, epw_path, work_base)

    # Select 21-building subset
    print("\n=== Select pilot subset ===")
    subset = select_subset(gdf_57)
    print(f"  Total: {len(subset)} buildings")

    # Save subset metadata for harvest step (include levels + height for floor-area calc)
    from openubem.geometry.footprint import derive_num_floors
    subset_info = pd.DataFrame({
        "osm_id":            subset["osm_id"].values,
        "archetype_id":      subset["archetype_id"].values,
        "footprint_area_m2": subset["footprint_area_m2"].values,
        "levels":            subset["levels"].values,
        "height_m":          subset["height_m"].values,
        "num_floors":        [derive_num_floors(row) for _, row in subset.iterrows()],
    })
    subset_info.to_parquet(str(work_base / "t07_subset_info.parquet"), index=False)
    print(f"  Subset info saved: {work_base / 't07_subset_info.parquet'}")

    # Step 3 + ship + submit: one per mode
    job_ids: dict[str, str] = {}
    n_submitted: dict[str, int] = {}

    for mode in MODES:
        print(f"\n{'='*60}")
        print(f"  MODE: {mode}")
        print(f"{'='*60}")

        manifest = run_step3_mode(subset, schedule_library, mode, work_base)
        n_ok = int((manifest["generation_status"] == "success").sum())

        if n_ok == 0:
            print(f"  [mode={mode}] ZERO successful IDFs — skipping cluster submit.", file=sys.stderr)
            continue

        n_submitted[mode] = ship_fleet(manifest, epw_path, mode)
        job_ids[mode] = submit_array(n_submitted[mode], mode)

    # Save job IDs for harvest step
    job_id_path = work_base / "t07_job_ids.json"
    job_id_path.write_text(json.dumps({"job_ids": job_ids, "n_submitted": n_submitted}, indent=2))

    # Summary
    print("\n" + "=" * 72)
    print("T07 FIRE-AND-FORGET SUBMISSION COMPLETE")
    print(f"  Work dir:     {work_base}")
    print(f"  Job IDs file: {job_id_path}")
    print()
    for mode in MODES:
        jid = job_ids.get(mode, "NOT_SUBMITTED")
        n   = n_submitted.get(mode, 0)
        fleet = _remote_fleet_dir(mode)
        print(f"  {mode:12s}: job={jid}  n={n}  fleet={fleet}")
    print()
    print("MONITORING: check with")
    print("  ssh o_iseri@speed.encs.concordia.ca 'squeue -u o_iseri'")
    print("MINIMUM monitoring interval: 30 min (per project rule).")
    print("After completion, run:")
    print("  py -3 scripts/cluster/t07_harvest_results.py")
    print("=" * 72)
    print("STOPPED (no polling). Do not srun anything on the login node.")


if __name__ == "__main__":
    main()
