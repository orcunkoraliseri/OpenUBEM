"""Elevator A/B validity check — austin_urban only, single-cell.

Arm A: current HEAD (assign_elevators active).
Arm B: identical code, assign_elevators monkeypatched to a no-op during Step 3
       only (mirrors scripts/validation/elevators_live_smoke.py's isolation technique).

Steps 1+2 (fetch/classify/enrich) run ONCE and are shared by both arms so any
non-elevator code drift cancels out identically in A and B.

Fire-and-forget: builds IDFs locally, ships both fleets, submits two sbatch
arrays, records job IDs, and STOPS. Polling/harvest done by a separate script.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd

from scripts.validation.v12_cell_pipeline import (
    CELL_CONFIGS, resolve_epw, step1_fetch, step2_classify_enrich,
    step3_generate, ship_to_cluster, submit_cluster_array,
)

CELL = "austin_urban"
FIXTURE_GPKG = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results"
    / "phaseE" / "austin_urban" / "01_buildings.gpkg"
)
WORK_BASE = Path(tempfile.gettempdir()) / "ubem_elev_ab" / CELL
REMOTE_FLEET_A = "/speed-scratch/o_iseri/fleets/elevab_austin_urban_A"
REMOTE_FLEET_B = "/speed-scratch/o_iseri/fleets/elevab_austin_urban_B"


def main() -> None:
    cfg = CELL_CONFIGS[CELL]
    WORK_BASE.mkdir(parents=True, exist_ok=True)

    print(f"=== Elevator A/B — {CELL} ===")
    print(f"Work base: {WORK_BASE}")

    # ---- shared Step 1 (cached fixture, no network) ----
    gpkg_dst = WORK_BASE / "01_buildings.gpkg"
    if not gpkg_dst.exists():
        shutil.copy2(FIXTURE_GPKG, gpkg_dst)
        print(f"  Copied fixture -> {gpkg_dst}")
    gdf_raw = step1_fetch(cfg["lat"], cfg["lon"], cfg["radius_m"], WORK_BASE)
    print(f"  Step 1: {len(gdf_raw)} buildings (shared by both arms)")

    # ---- shared EPW + Step 2 (classify/enrich, no elevator involvement) ----
    epw_path, epw_station_name = resolve_epw(cfg["lat"], cfg["lon"], WORK_BASE / "weather")
    gdf_57, schedule_library = step2_classify_enrich(gdf_raw, epw_path, WORK_BASE, CELL)
    print(f"  Step 2: {len(gdf_57)} buildings enriched (shared by both arms)")

    arch_counts = gdf_57["archetype_id"].value_counts().to_dict()
    print(f"  Archetype mix: {arch_counts}")

    # ---- Arm A: Step 3 with elevators ACTIVE (current HEAD, unmodified) ----
    step3_a_dir = WORK_BASE / "step3_A"
    print(f"\n--- Arm A (elevators ACTIVE) Step 3 -> {step3_a_dir} ---")
    idf_manifest_a = step3_generate(gdf_57, schedule_library, step3_a_dir)
    n_ok_a = int((idf_manifest_a["generation_status"] == "success").sum())
    print(f"  Arm A generation: {n_ok_a}/{len(idf_manifest_a)} success")

    # ---- Arm B: Step 3 with elevators DISABLED (local monkeypatch, reverted after) ----
    step3_b_dir = WORK_BASE / "step3_B"
    print(f"\n--- Arm B (elevators DISABLED) Step 3 -> {step3_b_dir} ---")
    import openubem.idf.builder as builder_mod
    _orig_assign_elevators = builder_mod.assign_elevators
    builder_mod.assign_elevators = lambda idf, row, zones: []
    try:
        idf_manifest_b = step3_generate(gdf_57, schedule_library, step3_b_dir)
    finally:
        builder_mod.assign_elevators = _orig_assign_elevators
    n_ok_b = int((idf_manifest_b["generation_status"] == "success").sum())
    print(f"  Arm B generation: {n_ok_b}/{len(idf_manifest_b)} success")

    if n_ok_a != n_ok_b:
        print(f"  WARNING: generation success counts differ A={n_ok_a} B={n_ok_b}", file=sys.stderr)

    # ---- sanity: confirm elevator objects present in A, absent in B ----
    from geomeppy import IDF as GeomIDF
    from eppy.modeleditor import IDDAlreadySetError
    from openubem import config as ubem_cfg
    try:
        GeomIDF.setiddname(str(ubem_cfg.ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass

    success_a = idf_manifest_a[idf_manifest_a["generation_status"] == "success"]
    n_with_elev_a = 0
    for _, r in success_a.iterrows():
        idf = GeomIDF(str(r["idf_path"]))
        elevs = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"] if e.EndUse_Subcategory == "Elevators"]
        if elevs:
            n_with_elev_a += 1
    print(f"\n  Arm A: {n_with_elev_a}/{len(success_a)} built IDFs contain an Elevators object.")

    success_b = idf_manifest_b[idf_manifest_b["generation_status"] == "success"]
    n_with_elev_b = 0
    for _, r in success_b.iterrows():
        idf = GeomIDF(str(r["idf_path"]))
        elevs = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"] if e.EndUse_Subcategory == "Elevators"]
        if elevs:
            n_with_elev_b += 1
    print(f"  Arm B: {n_with_elev_b}/{len(success_b)} built IDFs contain an Elevators object (expect 0).")

    if n_with_elev_b != 0:
        print("  FATAL: Arm B still emits elevator objects — isolation failed. STOP.", file=sys.stderr)
        sys.exit(1)

    # ---- ship + submit both arms (fire-and-forget) ----
    print(f"\n--- Shipping Arm A -> {REMOTE_FLEET_A} ---")
    ship_to_cluster(idf_manifest_a, epw_path, REMOTE_FLEET_A, step3_a_dir.parent / "fleet_staging_A")
    job_a = submit_cluster_array(n_ok_a, REMOTE_FLEET_A, "elevabA_austin_urban")

    print(f"\n--- Shipping Arm B -> {REMOTE_FLEET_B} ---")
    ship_to_cluster(idf_manifest_b, epw_path, REMOTE_FLEET_B, step3_b_dir.parent / "fleet_staging_B")
    job_b = submit_cluster_array(n_ok_b, REMOTE_FLEET_B, "elevabB_austin_urban")

    info = {
        "cell": CELL,
        "job_a": job_a, "job_b": job_b,
        "remote_fleet_a": REMOTE_FLEET_A, "remote_fleet_b": REMOTE_FLEET_B,
        "n_ok_a": n_ok_a, "n_ok_b": n_ok_b,
        "n_total_a": len(idf_manifest_a), "n_total_b": len(idf_manifest_b),
        "n_with_elev_a": n_with_elev_a, "n_with_elev_b": n_with_elev_b,
        "arch_counts": arch_counts,
        "epw_station_name": epw_station_name,
        "epw_path": str(epw_path),
        "work_base": str(WORK_BASE),
        "step3_a_dir": str(step3_a_dir),
        "step3_b_dir": str(step3_b_dir),
    }
    (WORK_BASE / "ab_job_info.json").write_text(json.dumps(info, indent=2))
    print("\n" + "=" * 72)
    print("FIRE-AND-FORGET SUBMISSION COMPLETE")
    print(json.dumps(info, indent=2))
    print("=" * 72)
    print("STOPPED. No polling performed. Poll with a separate script >=30 min apart.")


if __name__ == "__main__":
    main()
