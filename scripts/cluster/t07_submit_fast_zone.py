"""T07 recovery: re-run Steps 1-3 for fast_zone only, then ship + submit.

The previous pilot run crashed BEFORE saving the fast_zone manifest (Unicode
encode error on Windows). The other 3 modes (auto, building, floor) were
already submitted. This script handles only fast_zone.

Usage:
    py -3 scripts/cluster/t07_submit_fast_zone.py
"""
from __future__ import annotations

import io
import json
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
_REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"
MODE = "fast_zone"

_FIXTURE_DIR = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll"
    / "results" / "phaseE" / "la_rural"
)
_CELL_LAT = 34.7420
_CELL_LON = -118.2130

_TARGET_COUNTS = {
    "MidriseApartment": 5,
    "SmallOffice":      5,
    "MediumOffice":     5,
    "LargeOffice":      1,
    "Warehouse":        5,
}


def _ssh(cmd: str, timeout: int = 120) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def main() -> None:
    work_base = Path(tempfile.gettempdir()) / "ubem_t07_pilot"
    work_base.mkdir(parents=True, exist_ok=True)
    mode_dir = work_base / f"step3_{MODE}"
    mode_dir.mkdir(parents=True, exist_ok=True)
    (mode_dir / "idfs").mkdir(exist_ok=True)

    # Steps 1-2: reload fixture + re-enrich
    print("=== Step 1: load la_rural fixture ===")
    gdf_raw = gpd.read_file(str(_FIXTURE_DIR / "01_buildings.gpkg"))
    print(f"  {len(gdf_raw)} buildings")

    print("=== Resolve EPW ===")
    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw
    _stations = load_stations()
    _station, _dist = resolve_station(_CELL_LAT, _CELL_LON, _stations)
    epw_dir = work_base / "weather" / "weather"
    epw_dir.mkdir(parents=True, exist_ok=True)
    epw_path = fetch_epw(_station, output_dir=epw_dir)
    print(f"  EPW: {epw_path}")

    print("=== Step 2: semantic enrichment ===")
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

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
    gdf_57, schedule_library = enrich_semantics(gdf_29)
    print(f"  Enrichment: {len(gdf_57)} buildings")

    # Select same 21-building subset
    parts = []
    for arch, count in _TARGET_COUNTS.items():
        cands = gdf_57[gdf_57["archetype_id"] == arch]
        parts.append(cands.head(count))
    subset = gpd.GeoDataFrame(
        pd.concat(parts, ignore_index=True), geometry="geometry", crs=gdf_57.crs
    )
    print(f"  Subset: {len(subset)} buildings")

    # Step 3: fast_zone only
    print(f"=== Step 3 (mode={MODE}) ===")
    from openubem.idf.builder import run_step3
    t0 = time.monotonic()
    manifest = run_step3(subset, schedule_library, mode_dir, n_jobs=1, resolution_mode=MODE)
    elapsed = time.monotonic() - t0
    n_ok = int((manifest["generation_status"] == "success").sum())
    print(f"  Step 3: {n_ok}/{len(manifest)} success in {elapsed:.1f}s")

    # Save manifest (before any Unicode-risky prints)
    manifest.to_parquet(str(mode_dir / "03_manifest.parquet"), index=False)
    print(f"  Manifest saved: {mode_dir / '03_manifest.parquet'}")

    # Count fallbacks
    pc_rows = manifest[manifest["zoning_strategy"] == "perimeter_core"]
    fallbacks = pc_rows[pc_rows["num_zones"] == 1]
    print(f"  Fallbacks (perimeter_core -> 1 zone): {len(fallbacks)}")
    for _, r in fallbacks.iterrows():
        print(f"    fallback: {r['osm_id']} ({r.get('archetype_id','?')}) num_zones=1")

    if n_ok == 0:
        sys.exit("FATAL: zero successful IDFs for fast_zone — cannot submit.")

    # Ship
    success = manifest[manifest["generation_status"] == "success"]
    stems = [Path(str(r["idf_path"])).stem for _, r in success.iterrows()]
    remote_dir = f"{_REMOTE_FLEET_BASE}/t07_{MODE}"
    _ssh(f"mkdir -p {remote_dir}/idfs {remote_dir}/weather {remote_dir}/out")

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

    print(f"  Uploading {len(stems)} IDFs ...")
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
    print("  IDFs uploaded.")

    # Submit sbatch
    subprocess.run(
        ["scp", str(SBATCH_LOCAL), f"{REMOTE_HOST}:{SBATCH_REMOTE}"],
        check=False, timeout=60,
    )
    cmd = (
        f"sbatch --array=1-{len(stems)}%16 "
        f"--export=FLEET_DIR={remote_dir} "
        f"--job-name=t07_{MODE} "
        f"--output={remote_dir}/t07_{MODE}_%A_%a.log "
        f"{SBATCH_REMOTE}"
    )
    print(f"  Submitting: {cmd}")
    out = _ssh(cmd, timeout=60)
    job_id = ""
    for line in out.splitlines():
        if "Submitted batch job" in line:
            job_id = line.strip().split()[-1]
            break
    if not job_id:
        sys.exit(f"ERROR: no job ID:\n{out}")
    print(f"  Job ID: {job_id}")

    # Save subset info if not already there (in case pilot crashed before saving it)
    subset_path = work_base / "t07_subset_info.parquet"
    if not subset_path.exists():
        from openubem.geometry.footprint import derive_num_floors
        subset_info = pd.DataFrame({
            "osm_id":            subset["osm_id"].values,
            "archetype_id":      subset["archetype_id"].values,
            "footprint_area_m2": subset["footprint_area_m2"].values,
            "levels":            subset["levels"].values,
            "height_m":          subset["height_m"].values,
            "num_floors":        [derive_num_floors(row) for _, row in subset.iterrows()],
        })
        subset_info.to_parquet(str(subset_path), index=False)
        print(f"  Subset info saved: {subset_path}")

    # Append job ID
    job_id_path = work_base / "t07_job_ids.json"
    if job_id_path.exists():
        info = json.loads(job_id_path.read_text())
    else:
        info = {"job_ids": {}, "n_submitted": {}}
    info["job_ids"][MODE] = job_id
    info["n_submitted"][MODE] = len(stems)
    job_id_path.write_text(json.dumps(info, indent=2))
    print(f"  Job IDs: {job_id_path}")

    print("\n" + "=" * 60)
    print(f"fast_zone submitted: job={job_id}, n={len(stems)}")
    print(f"Fleet: {remote_dir}")
    print("Check: ssh o_iseri@speed.encs.concordia.ca 'squeue -u o_iseri'")
    print("Minimum monitoring interval: 30 min.")
    print("After completion: py -3 scripts/cluster/t07_harvest_results.py")
    print("=" * 60)
    print("STOPPED (fire-and-forget). Do not poll or srun on login node.")


if __name__ == "__main__":
    main()
