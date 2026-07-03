"""T14-HOTELFIX — hotel-only cluster pilot: zone vs floor vs building, fire-and-forget.

Sibling of t14_layout_pilot.py (which fired the apartment-only arrays under fleet tag
`t14_*`, jobs 1064082-1064231, still running and untouched by this script). This
script re-recons the 12 phaseE cells for SmallHotel/LargeHotel (recovered via the
building_classifier bt-or-ft fix, T14-HOTELFIX), picks the hotel-rich cell(s), builds
a subset biased toward SIMPLE footprints (compact/slab/point — hotels have no
complex_shapes_supported flag, so L/U/T/CROSS/O/ribbon/irregular degrade to
one_zone_per_floor with zero room_layout signal), runs Steps 1-3 locally, ships fleet
dirs, and submits sbatch --array jobs under a DISTINCT fleet tag `t14h_<cell>_<mode>`.

ABSOLUTE RULE: this script NEVER polls or blocks on cluster progress.
Only sbatch/scp/ssh (lightweight ops + fire-and-forget submit) touch the cluster.

Usage (local machine only):
    py -3 scripts/cluster/t14_hotel_pilot.py
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

from scripts.validation.v12_cell_pipeline import CELL_CONFIGS

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
SBATCH_REMOTE = "/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet.sbatch"
SBATCH_LOCAL = REPO / "scripts" / "cluster" / "submit_fleet.sbatch"

_PHASEE_DIR = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
)
_CELLS = list(CELL_CONFIGS.keys())

_HOTEL_ARCHETYPES = ["SmallHotel", "LargeHotel"]
_SIMPLE_SHAPES = {"compact", "slab", "point"}  # room_layout-eligible for hotels (no multi-wing support)

_TARGET_PER_ARCH_PER_CELL = 10
_N_WINNER_CELLS = 2  # matches the apartment pilot's top-2-richest selection convention

MODES = ["zone", "floor", "building"]
_REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"
_FLEET_TAG = "t14h"  # DISTINCT from the running t14_* apartment fleets


# ── helpers ───────────────────────────────────────────────────────────────────

def _ssh(cmd: str, timeout: int = 120) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def _remote_fleet_dir(cell: str, mode: str) -> str:
    return f"{_REMOTE_FLEET_BASE}/{_FLEET_TAG}_{cell}_{mode}"


# ── Recon: classify all 12 cells for SmallHotel/LargeHotel, bucket by shape ────

def recon_cell(cell: str) -> tuple[dict, pd.DataFrame]:
    from openubem.semantic.building_classifier import (
        _INPUT_SCHEMA_COLUMNS, BuildingClassifier,
    )
    from openubem.geometry.layoutGenerator import classify_footprint

    path = _PHASEE_DIR / cell / "01_buildings.gpkg"
    if not path.exists():
        sys.exit(f"FATAL: fixture not found: {path}")
    gdf_raw = gpd.read_file(str(path))
    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")
    gdf_26 = BuildingClassifier().classify(gdf_in)

    cand = gdf_26[gdf_26["archetype_id"].isin(_HOTEL_ARCHETYPES)].copy()
    shapes = []
    for _, r in cand.iterrows():
        shape_class, _metrics = classify_footprint(r.geometry)
        shapes.append(shape_class.value)
    cand["shape"] = shapes
    cand["simple"] = cand["shape"].isin(_SIMPLE_SHAPES)

    row = {"cell": cell}
    for arch in _HOTEL_ARCHETYPES:
        sub = cand[cand["archetype_id"] == arch]
        row[f"{arch}_total"] = int(len(sub))
        row[f"{arch}_simple"] = int(sub["simple"].sum())
    row["combined_simple"] = sum(row[f"{a}_simple"] for a in _HOTEL_ARCHETYPES)
    row["combined_total"] = sum(row[f"{a}_total"] for a in _HOTEL_ARCHETYPES)
    return row, cand[["osm_id", "archetype_id", "shape", "simple"]]


# ── Subset selection: simple-shape first, complex fill only if short, LOG gaps ──

def build_hotel_subset(cand_df: pd.DataFrame) -> tuple[list[str], dict]:
    info: dict = {"targets": {a: _TARGET_PER_ARCH_PER_CELL for a in _HOTEL_ARCHETYPES},
                  "picked": {}, "gap_log": []}
    chosen: dict[str, list[str]] = {}

    for arch in _HOTEL_ARCHETYPES:
        target = _TARGET_PER_ARCH_PER_CELL
        pool = cand_df[cand_df["archetype_id"] == arch]
        ordered = (
            pool[pool["simple"]]["osm_id"].tolist()
            + pool[~pool["simple"]]["osm_id"].tolist()
        )
        picked = ordered[:target]
        chosen[arch] = picked
        gap = target - len(picked)
        if gap > 0:
            info["gap_log"].append(
                f"{arch}: wanted {target}, found {len(picked)} (no cross-archetype "
                f"fill for hotels — no substitute lodging pool), gap {gap}"
            )

    info["picked"] = {a: len(v) for a, v in chosen.items()}
    all_ids = [i for v in chosen.values() for i in v]
    picked_df = cand_df[cand_df["osm_id"].isin(all_ids)]
    info["picked_simple"] = int(picked_df["simple"].sum())
    info["picked_complex"] = int(len(picked_df) - info["picked_simple"])
    return all_ids, info


# ── Step 2: semantic enrichment (mirrors t14_layout_pilot.py run_step2) ────────

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


# ── Step 3: IDF generation for one (cell, mode) ──────────────────────────────

def run_step3_mode(gdf: gpd.GeoDataFrame, schedule_lib: object,
                    mode: str, cell: str, cell_work: Path) -> pd.DataFrame:
    from openubem.idf.builder import run_step3

    mode_dir = cell_work / f"step3_{mode}"
    mode_dir.mkdir(parents=True, exist_ok=True)
    (mode_dir / "idfs").mkdir(exist_ok=True)

    print(f"  Running Step 3 (cell={cell}, mode={mode}, n={len(gdf)}) ...")
    t0 = time.monotonic()
    manifest = run_step3(gdf, schedule_lib, mode_dir, n_jobs=1, resolution_mode=mode)
    elapsed = time.monotonic() - t0

    n_ok = int((manifest["generation_status"] == "success").sum())
    print(f"  Step 3 [{cell}/{mode}]: {n_ok}/{len(manifest)} success in {elapsed:.1f}s")

    manifest.to_parquet(str(mode_dir / "03_manifest.parquet"), index=False)

    status_counts = manifest["generation_status"].value_counts()
    for status, n in status_counts.items():
        if status != "success":
            print(f"    {status}: {n}")
    if mode == "zone" and "zoning_strategy" in manifest.columns:
        strat_counts = manifest["zoning_strategy"].value_counts()
        print(f"  [zone] zoning_strategy breakdown: {strat_counts.to_dict()}")
    return manifest


# ── Cluster: ship one fleet dir ───────────────────────────────────────────────

def ship_fleet(manifest: pd.DataFrame, epw_path: Path, cell: str, mode: str) -> int:
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

    print(f"  Uploading {len(stems)} IDFs for cell={cell} mode={mode} ...")
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
    print(f"  Upload complete for cell={cell} mode={mode}.")
    return len(stems)


# ── Cluster: submit sbatch array (fire-and-forget) ───────────────────────────

def submit_array(n_jobs: int, cell: str, mode: str) -> str:
    remote_dir = _remote_fleet_dir(cell, mode)

    subprocess.run(
        ["scp", str(SBATCH_LOCAL), f"{REMOTE_HOST}:{SBATCH_REMOTE}"],
        check=False, timeout=60,
    )

    job_name = f"{_FLEET_TAG}_{cell}_{mode}"
    cmd = (
        f"sbatch --array=1-{n_jobs}%16 "
        f"--export=FLEET_DIR={remote_dir} "
        f"--job-name={job_name} "
        f"--output={remote_dir}/{job_name}_%A_%a.log "
        f"{SBATCH_REMOTE}"
    )
    print(f"  Submitting [{cell}/{mode}]: {cmd}")
    out = _ssh(cmd, timeout=60)

    job_id = ""
    for line in out.splitlines():
        if "Submitted batch job" in line:
            job_id = line.strip().split()[-1]
            break
    if not job_id:
        sys.exit(f"ERROR: no job ID from sbatch for cell={cell} mode={mode}:\n{out}")
    print(f"  [{cell}/{mode}] Job ID: {job_id}")
    return job_id


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    work_base = Path(tempfile.gettempdir()) / "ubem_t14h_pilot"
    work_base.mkdir(parents=True, exist_ok=True)
    print(f"T14-HOTELFIX pilot — work dir: {work_base}")
    print(f"Modes: {MODES}")
    print(f"Target subset per cell: {_TARGET_PER_ARCH_PER_CELL} per archetype (simple-shape biased)")

    # ── Recon: all 12 phaseE cells ───────────────────────────────────────────
    print("\n=== Recon: classifying 12 phaseE cells for SmallHotel/LargeHotel ===")
    recon_rows: list[dict] = []
    cand_by_cell: dict[str, pd.DataFrame] = {}
    for cell in _CELLS:
        row, cand_df = recon_cell(cell)
        recon_rows.append(row)
        cand_by_cell[cell] = cand_df
        print(f"  {cell:16s} SH={row['SmallHotel_total']:3d}/simple={row['SmallHotel_simple']:3d}"
              f"  LH={row['LargeHotel_total']:3d}/simple={row['LargeHotel_simple']:3d}"
              f"  combined_simple={row['combined_simple']:3d}")

    recon_df = pd.DataFrame(recon_rows).sort_values("combined_simple", ascending=False)
    recon_df.to_csv(work_base / "t14h_recon_table.csv", index=False)
    print("\n--- Recon table (sorted by combined_simple desc) ---")
    print(recon_df.to_string(index=False))

    total_simple = int(recon_df["combined_simple"].sum())
    print(f"\nTotal simple-shape hotels across all 12 cells: {total_simple}")
    if total_simple < 5:
        print("STOP-IF-USELESS gate: <5 simple-shape hotels found. Not firing.", file=sys.stderr)
        sys.exit(0)

    winners = recon_df["cell"].head(_N_WINNER_CELLS).tolist()
    print(f"\nSelected cells: {winners}")

    # ── Per-winning-cell: subset -> Step 2 -> Step 3 x modes -> ship -> submit ──
    job_ids: dict[str, str] = {}
    n_submitted: dict[str, int] = {}
    subset_reports: dict[str, dict] = {}

    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw
    from openubem.geometry.footprint import derive_num_floors

    for cell in winners:
        print(f"\n{'='*72}")
        print(f"  CELL: {cell}")
        print(f"{'='*72}")
        cell_work = work_base / cell
        cell_work.mkdir(parents=True, exist_ok=True)

        cand_df = cand_by_cell[cell]
        chosen_ids, sel_info = build_hotel_subset(cand_df)
        print(f"  Subset composition: {sel_info['picked']} "
              f"(simple={sel_info['picked_simple']}, complex={sel_info['picked_complex']})")
        for line in sel_info["gap_log"]:
            print(f"  GAP: {line}")
        subset_reports[cell] = sel_info

        if not chosen_ids:
            print(f"  [{cell}] zero hotels selected — skipping cell.", file=sys.stderr)
            continue

        gdf_raw_full = gpd.read_file(str(_PHASEE_DIR / cell / "01_buildings.gpkg"))
        gdf_subset_raw = gdf_raw_full[gdf_raw_full["osm_id"].isin(chosen_ids)].reset_index(drop=True)
        print(f"  Total subset: {len(gdf_subset_raw)} buildings")

        cfg = CELL_CONFIGS[cell]
        print(f"  Resolving EPW for ({cfg['lat']}, {cfg['lon']}) [{cfg['state']}] ...")
        stations = load_stations()
        station, dist_km = resolve_station(cfg["lat"], cfg["lon"], stations)
        print(f"  Resolved station: {station['station_id']} at {dist_km:.1f} km")
        (cell_work / "weather").mkdir(parents=True, exist_ok=True)
        epw_path = fetch_epw(station, output_dir=cell_work / "weather")
        print(f"  EPW: {epw_path}")

        gdf_57, schedule_library = run_step2(gdf_subset_raw, epw_path, cell_work)

        subset_info = pd.DataFrame({
            "osm_id":            gdf_57["osm_id"].values,
            "archetype_id":      gdf_57["archetype_id"].values,
            "footprint_area_m2": gdf_57["footprint_area_m2"].values,
            "levels":            gdf_57["levels"].values,
            "height_m":          gdf_57["height_m"].values,
            "num_floors":        [derive_num_floors(r) for _, r in gdf_57.iterrows()],
        })
        subset_info.to_parquet(str(cell_work / "t14h_subset_info.parquet"), index=False)
        print(f"  Subset info saved: {cell_work / 't14h_subset_info.parquet'}")

        for mode in MODES:
            manifest = run_step3_mode(gdf_57, schedule_library, mode, cell, cell_work)
            n_ok = int((manifest["generation_status"] == "success").sum())
            key = f"{cell}_{mode}"

            if n_ok == 0:
                print(f"  [{key}] ZERO successful IDFs — skipping cluster submit.", file=sys.stderr)
                continue

            n_submitted[key] = ship_fleet(manifest, epw_path, cell, mode)
            job_ids[key] = submit_array(n_submitted[key], cell, mode)

    # ── Save job IDs + recon + subset composition for harvest step ──────────
    job_id_path = work_base / "t14h_job_ids.json"
    job_id_path.write_text(json.dumps({
        "job_ids": job_ids,
        "n_submitted": n_submitted,
        "winners": winners,
        "recon_table": recon_df.to_dict(orient="records"),
        "subset_reports": subset_reports,
        "fleet_dirs": {k: _remote_fleet_dir(*k.rsplit("_", 1)) for k in job_ids},
    }, indent=2, default=str))

    print("\n" + "=" * 72)
    print("T14-HOTELFIX FIRE-AND-FORGET SUBMISSION COMPLETE")
    print(f"  Work dir:     {work_base}")
    print(f"  Job IDs file: {job_id_path}")
    print()
    for cell in winners:
        for mode in MODES:
            key = f"{cell}_{mode}"
            jid = job_ids.get(key, "NOT_SUBMITTED")
            n = n_submitted.get(key, 0)
            fleet = _remote_fleet_dir(cell, mode)
            print(f"  {key:28s}: job={jid}  n={n}  fleet={fleet}")
    print()
    print("MONITORING: check with")
    print("  ssh o_iseri@speed.encs.concordia.ca 'squeue -u o_iseri'")
    print("MINIMUM monitoring interval: 30 min (per project rule).")
    print("Does NOT touch the running t14_* apartment fleets (jobs 1064082-1064231).")
    print("=" * 72)
    print("STOPPED (no polling). Do not srun anything on the login node.")


if __name__ == "__main__":
    main()
