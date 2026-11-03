"""T14 — LayoutGenerator cluster pilot: zone vs floor vs building, fire-and-forget.

Recon-first: classifies all 12 phaseE cells for non-rect (L/U/T/CROSS/O)
MidriseApartment + SmallHotel + LargeHotel footprints, picks the 2 richest cells,
builds a <=80-building subset biased toward non-rect footprints, runs Steps 1-3
locally per (cell, mode), ships fleet dirs, submits sbatch --array jobs, and EXITS.

ABSOLUTE RULE: this script NEVER polls or blocks on cluster progress.
Only sbatch/scp/ssh (lightweight ops + fire-and-forget submit) touch the cluster.

After cluster completion, check with:
    ssh o_iseri@speed.encs.concordia.ca "squeue -u o_iseri"
Harvest is a separate later step (NOT run by this script).

Usage (local machine only):
    py -3 scripts/cluster/t14_layout_pilot.py
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

from scripts.validation.v12_cell_pipeline import CELL_CONFIGS  # source-of-truth cell lat/lon/state

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
SBATCH_REMOTE = "/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet.sbatch"
SBATCH_LOCAL = REPO / "scripts" / "cluster" / "submit_fleet.sbatch"

_PHASEE_DIR = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
)
_CELLS = list(CELL_CONFIGS.keys())  # all 12 phaseE cells

_RECON_ARCHETYPES = ["MidriseApartment", "SmallHotel", "LargeHotel"]
_NONRECT_SHAPES = {"L", "U", "T", "cross", "O"}  # ShapeClass values eligible for room_layout

_TARGET_COUNTS = {"MidriseApartment": 20, "SmallHotel": 10, "LargeHotel": 10}

MODES = ["zone", "floor", "building"]
_REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"
_FLEET_TAG = "t14"


# ── helpers ───────────────────────────────────────────────────────────────────

def _ssh(cmd: str, timeout: int = 120) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def _remote_fleet_dir(cell: str, mode: str) -> str:
    return f"{_REMOTE_FLEET_BASE}/{_FLEET_TAG}_{cell}_{mode}"


# ── Recon: classify all 12 cells for non-rect MidriseApartment/SmallHotel/LargeHotel ──

def recon_cell(cell: str) -> tuple[dict, pd.DataFrame]:
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.geometry.layoutGenerator import classify_footprint

    path = _PHASEE_DIR / cell / "01_buildings.gpkg"
    if not path.exists():
        sys.exit(f"FATAL: fixture not found: {path}")
    gdf_raw = gpd.read_file(str(path))
    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")
    gdf_26 = BuildingClassifier().classify(gdf_in)

    cand = gdf_26[gdf_26["archetype_id"].isin(_RECON_ARCHETYPES)].copy()
    shapes = []
    for _, r in cand.iterrows():
        shape_class, _metrics = classify_footprint(r.geometry)
        shapes.append(shape_class.value)
    cand["shape"] = shapes
    cand["nonrect"] = cand["shape"].isin(_NONRECT_SHAPES)

    row = {"cell": cell}
    for arch in _RECON_ARCHETYPES:
        sub = cand[cand["archetype_id"] == arch]
        row[f"{arch}_total"] = int(len(sub))
        row[f"{arch}_nonrect"] = int(sub["nonrect"].sum())
    row["combined_nonrect"] = sum(row[f"{a}_nonrect"] for a in _RECON_ARCHETYPES)
    return row, cand[["osm_id", "archetype_id", "shape", "nonrect"]]


# ── Subset selection: bias non-rect, log hotel gap-fill from MidriseApartment ──

def build_subset_selection(cand_df: pd.DataFrame) -> tuple[list[str], dict]:
    info: dict = {"targets": dict(_TARGET_COUNTS), "picked": {}, "gap_log": []}
    chosen: dict[str, list[str]] = {}
    gap_total = 0

    for arch in ["SmallHotel", "LargeHotel"]:
        target = _TARGET_COUNTS[arch]
        pool = cand_df[cand_df["archetype_id"] == arch]
        ordered = (
            pool[pool["nonrect"]]["osm_id"].tolist()
            + pool[~pool["nonrect"]]["osm_id"].tolist()
        )
        picked = ordered[:target]
        chosen[arch] = picked
        gap = target - len(picked)
        if gap > 0:
            gap_total += gap
            info["gap_log"].append(
                f"{arch}: wanted {target}, found {len(picked)}, gap {gap} (filled from MidriseApartment)"
            )

    ma_target = _TARGET_COUNTS["MidriseApartment"] + gap_total
    pool = cand_df[cand_df["archetype_id"] == "MidriseApartment"]
    ordered = (
        pool[pool["nonrect"]]["osm_id"].tolist()
        + pool[~pool["nonrect"]]["osm_id"].tolist()
    )
    picked_ma = ordered[:ma_target]
    chosen["MidriseApartment"] = picked_ma
    if len(picked_ma) < ma_target:
        info["gap_log"].append(
            f"MidriseApartment: wanted {ma_target} (incl. {gap_total} hotel gap-fill), "
            f"found {len(picked_ma)}, short {ma_target - len(picked_ma)} (no further fill available)"
        )

    info["picked"] = {a: len(v) for a, v in chosen.items()}
    all_ids = [i for v in chosen.values() for i in v]
    picked_df = cand_df[cand_df["osm_id"].isin(all_ids)]
    info["picked_nonrect"] = int(picked_df["nonrect"].sum())
    info["picked_rect"] = int(len(picked_df) - info["picked_nonrect"])
    return all_ids, info


# ── Step 2: semantic enrichment (mirrors t07_resolution_pilot.py run_step2) ──

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
    """Upload IDFs + EPW + fleet.lst for one (cell, mode). Returns n_jobs submitted."""
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
    """Submit sbatch --array for one (cell, mode). Returns job ID. NEVER polls."""
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
    work_base = Path(tempfile.gettempdir()) / "ubem_t14_pilot"
    work_base.mkdir(parents=True, exist_ok=True)
    print(f"T14 layout pilot — work dir: {work_base}")
    print(f"Modes: {MODES}")
    print(f"Target subset per cell: {_TARGET_COUNTS}")

    # ── Recon: all 12 phaseE cells ───────────────────────────────────────────
    print("\n=== Recon: classifying 12 phaseE cells ===")
    recon_rows: list[dict] = []
    cand_by_cell: dict[str, pd.DataFrame] = {}
    for cell in _CELLS:
        row, cand_df = recon_cell(cell)
        recon_rows.append(row)
        cand_by_cell[cell] = cand_df
        print(f"  {cell:16s} MA={row['MidriseApartment_total']:4d}/nonrect={row['MidriseApartment_nonrect']:4d}"
              f"  SH={row['SmallHotel_total']:3d}/nonrect={row['SmallHotel_nonrect']:3d}"
              f"  LH={row['LargeHotel_total']:3d}/nonrect={row['LargeHotel_nonrect']:3d}"
              f"  combined_nonrect={row['combined_nonrect']:4d}")

    recon_df = pd.DataFrame(recon_rows).sort_values("combined_nonrect", ascending=False)
    recon_df.to_csv(work_base / "t14_recon_table.csv", index=False)
    print("\n--- Recon table (sorted by combined_nonrect desc) ---")
    print(recon_df.to_string(index=False))

    winners = recon_df["cell"].head(2).tolist()
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
        chosen_ids, sel_info = build_subset_selection(cand_df)
        print(f"  Subset composition: {sel_info['picked']} "
              f"(non-rect={sel_info['picked_nonrect']}, rect={sel_info['picked_rect']})")
        for line in sel_info["gap_log"]:
            print(f"  GAP: {line}")
        subset_reports[cell] = sel_info

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
        subset_info.to_parquet(str(cell_work / "t14_subset_info.parquet"), index=False)
        print(f"  Subset info saved: {cell_work / 't14_subset_info.parquet'}")

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
    job_id_path = work_base / "t14_job_ids.json"
    job_id_path.write_text(json.dumps({
        "job_ids": job_ids,
        "n_submitted": n_submitted,
        "winners": winners,
        "recon_table": recon_df.to_dict(orient="records"),
        "subset_reports": subset_reports,
        "fleet_dirs": {k: _remote_fleet_dir(*k.rsplit("_", 1)) for k in job_ids},
    }, indent=2, default=str))

    print("\n" + "=" * 72)
    print("T14 FIRE-AND-FORGET SUBMISSION COMPLETE")
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
    print("Harvest (separate later step, NOT run by this script) writes:")
    print("  openubem/outputs/comparisons/t14_zone_vs_floor_vs_building.csv")
    print("=" * 72)
    print("STOPPED (no polling). Do not srun anything on the login node.")


if __name__ == "__main__":
    main()
