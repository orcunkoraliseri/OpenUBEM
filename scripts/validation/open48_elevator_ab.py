"""OPEN-48 T03: single-cell live EnergyPlus A/B for the restored elevator wiring.

Arm A: current HEAD (openubem.idf.builder now calls assign_elevators — the T03 restore).
Arm B: identical code, assign_elevators monkeypatched to a no-op during Step 3 only
       (mirrors the archived scripts/validation/elevators_live_smoke.py isolation technique).

Steps 1+2 (fetch/classify/enrich) run ONCE and are shared by both arms so any
non-elevator code drift cancels out identically in A and B.

Uses a fresh work directory (not the pre-existing scripts/cluster/elevator_ab_*
cache under %TEMP%\\ubem_elev_ab, whose contents predate and are of unknown
provenance relative to this restore) so Arm A is guaranteed to be built from the
just-edited openubem/idf/builder.py, not a stale cached manifest.

Usage:
    .venv/Scripts/python.exe scripts/validation/open48_elevator_ab.py submit
    .venv/Scripts/python.exe scripts/validation/open48_elevator_ab.py harvest

submit: fire-and-forget — builds IDFs locally for both arms, ships both fleets,
        submits two sbatch arrays on Speed, records job IDs, and STOPS. Never
        runs EnergyPlus or python on the login node.
harvest: run only AFTER both arrays complete (check with squeue/sacct). Fetches
         results (scp/tar; no login-node compute) and reports the measured delta.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
import tempfile
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import numpy as np
import pandas as pd

from scripts.validation.v12_cell_pipeline import (
    CELL_CONFIGS, resolve_epw, step1_fetch, step2_classify_enrich,
    step3_generate, ship_to_cluster, submit_cluster_array, fetch_results,
)

CELL = "austin_urban"
FIXTURE_GPKG = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results"
    / "phaseE" / "austin_urban" / "01_buildings.gpkg"
)
WORK_BASE = Path(tempfile.gettempdir()) / "ubem_open48_ab" / CELL
REMOTE_FLEET_A = "/speed-scratch/o_iseri/fleets/open48ab_austin_urban_A"
REMOTE_FLEET_B = "/speed-scratch/o_iseri/fleets/open48ab_austin_urban_B"
INFO_PATH = WORK_BASE / "ab_job_info.json"
RESULT_PATH = WORK_BASE / "ab_result.json"


def submit() -> None:
    cfg = CELL_CONFIGS[CELL]
    WORK_BASE.mkdir(parents=True, exist_ok=True)

    print(f"=== OPEN-48 T03 elevator A/B — {CELL} ===")
    print(f"Work base: {WORK_BASE}")

    gpkg_dst = WORK_BASE / "01_buildings.gpkg"
    if not gpkg_dst.exists():
        shutil.copy2(FIXTURE_GPKG, gpkg_dst)
        print(f"  Copied fixture -> {gpkg_dst}")
    gdf_raw = step1_fetch(cfg["lat"], cfg["lon"], cfg["radius_m"], WORK_BASE)
    print(f"  Step 1: {len(gdf_raw)} buildings (shared by both arms)")

    epw_path, epw_station_name = resolve_epw(cfg["lat"], cfg["lon"], WORK_BASE / "weather")
    gdf_57, schedule_library = step2_classify_enrich(gdf_raw, epw_path, WORK_BASE, CELL)
    print(f"  Step 2: {len(gdf_57)} buildings enriched (shared by both arms)")

    arch_counts = gdf_57["archetype_id"].value_counts().to_dict()
    print(f"  Archetype mix: {arch_counts}")

    step3_a_dir = WORK_BASE / "step3_A"
    print(f"\n--- Arm A (elevators ACTIVE, current HEAD) Step 3 -> {step3_a_dir} ---")
    idf_manifest_a = step3_generate(gdf_57, schedule_library, step3_a_dir)
    n_ok_a = int((idf_manifest_a["generation_status"] == "success").sum())
    print(f"  Arm A generation: {n_ok_a}/{len(idf_manifest_a)} success")

    step3_b_dir = WORK_BASE / "step3_B"
    print(f"\n--- Arm B (elevators DISABLED, no-op monkeypatch) Step 3 -> {step3_b_dir} ---")
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

    if n_with_elev_a == 0:
        print("  FATAL: Arm A emits zero elevator objects — wiring did not take. STOP.", file=sys.stderr)
        sys.exit(1)
    if n_with_elev_b != 0:
        print("  FATAL: Arm B still emits elevator objects — isolation failed. STOP.", file=sys.stderr)
        sys.exit(1)

    print(f"\n--- Shipping Arm A -> {REMOTE_FLEET_A} ---")
    ship_to_cluster(idf_manifest_a, epw_path, REMOTE_FLEET_A, step3_a_dir.parent / "fleet_staging_A")
    job_a = submit_cluster_array(n_ok_a, REMOTE_FLEET_A, "open48abA_austin_urban")

    print(f"\n--- Shipping Arm B -> {REMOTE_FLEET_B} ---")
    ship_to_cluster(idf_manifest_b, epw_path, REMOTE_FLEET_B, step3_b_dir.parent / "fleet_staging_B")
    job_b = submit_cluster_array(n_ok_b, REMOTE_FLEET_B, "open48abB_austin_urban")

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
    INFO_PATH.write_text(json.dumps(info, indent=2))
    print("\n" + "=" * 72)
    print("FIRE-AND-FORGET SUBMISSION COMPLETE")
    print(json.dumps(info, indent=2))
    print("=" * 72)
    print("STOPPED. No polling performed. Poll with squeue/sacct, then run 'harvest'.")


def _floor_area_from_sql(sql_path: Path) -> float:
    try:
        conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
        rows = conn.execute("SELECT FloorArea FROM Zones").fetchall()
        conn.close()
        return float(sum(r[0] for r in rows if r[0] is not None))
    except Exception:
        return float("nan")


def harvest_arm(arm: str, step3_dir: Path, remote_fleet_dir: str) -> pd.DataFrame:
    from openubem.results.parser import parse_building

    manifest = pd.read_parquet(step3_dir / "03_idf_manifest.parquet")
    import geopandas as gpd

    bldgs = gpd.read_file(step3_dir.parent / "01_buildings.gpkg")[
        ["osm_id", "levels", "height_m", "footprint_area_m2"]
    ]
    bldgs["osm_id"] = bldgs["osm_id"].astype(str)
    manifest["osm_id"] = manifest["osm_id"].astype(str)
    manifest = manifest.merge(bldgs, on="osm_id", how="left")
    success = manifest[manifest["generation_status"] == "success"].copy()
    osm_stems = [Path(str(r["idf_path"])).stem for _, r in success.iterrows()]

    sim_out = step3_dir.parent / f"sim_out_{arm}"
    missing = [s for s in osm_stems if not (sim_out / s / "eplusout.sql").exists()]
    print(f"\n[Arm {arm}] {len(osm_stems)} total, {len(osm_stems) - len(missing)} cached, "
          f"fetching {len(missing)} -> {sim_out}", flush=True)
    if missing:
        fetch_results(missing, remote_fleet_dir, sim_out)

    rows = []
    n_ep_ok = 0
    for _, mrow in success.iterrows():
        stem = Path(str(mrow["idf_path"])).stem
        bdir = sim_out / stem
        sql_path = bdir / "eplusout.sql"
        end_path = bdir / "eplusout.end"
        ep_ok = end_path.exists() and "EnergyPlus Completed Successfully" in end_path.read_text(errors="replace")
        if ep_ok:
            n_ep_ok += 1
        if not sql_path.exists():
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            metrics = parse_building(sql_path, None, mrow)
        if metrics.get("parse_status") not in ("success", "success_cached", "success_csv_fallback"):
            continue
        metrics["floor_area_m2"] = _floor_area_from_sql(sql_path)
        metrics["archetype_id"] = mrow["archetype_id"]
        rows.append(metrics)

    df = pd.DataFrame(rows)
    print(f"[Arm {arm}] EnergyPlus success: {n_ep_ok}/{len(osm_stems)}; parsed OK: {len(df)}")
    return df


def cell_eui(df: pd.DataFrame) -> tuple[float, float]:
    valid = df[df["total_eui_kwh_m2"].notna() & df["floor_area_m2"].notna() & (df["floor_area_m2"] > 0)]
    median = float(valid["total_eui_kwh_m2"].median())
    w = valid["floor_area_m2"].values
    aw_mean = float(np.average(valid["total_eui_kwh_m2"].values, weights=w))
    return median, aw_mean


def harvest() -> None:
    if not INFO_PATH.exists():
        print(f"ERROR: {INFO_PATH} not found — run 'submit' first.", file=sys.stderr)
        sys.exit(1)
    info = json.loads(INFO_PATH.read_text())

    step3_a = Path(info["step3_a_dir"])
    step3_b = Path(info["step3_b_dir"])

    df_a = harvest_arm("A", step3_a, info["remote_fleet_a"])
    df_b = harvest_arm("B", step3_b, info["remote_fleet_b"])

    df_a.to_parquet(step3_a.parent / "parsed_A.parquet")
    df_b.to_parquet(step3_b.parent / "parsed_B.parquet")

    common = sorted(set(df_a["osm_id"]) & set(df_b["osm_id"]))
    a = df_a[df_a["osm_id"].isin(common)].set_index("osm_id").sort_index()
    b = df_b[df_b["osm_id"].isin(common)].set_index("osm_id").sort_index()
    print(f"\nCommon buildings parsed in BOTH arms: {len(common)} "
          f"(A={len(df_a)}, B={len(df_b)})")

    med_a, awm_a = cell_eui(a.reset_index())
    med_b, awm_b = cell_eui(b.reset_index())

    d_med = med_a - med_b
    d_awm = awm_a - awm_b
    pct_med = 100 * d_med / med_b
    pct_awm = 100 * d_awm / awm_b

    va = a[a["elevators_eui_kwh_m2"].notna() & (a["floor_area_m2"] > 0)]
    pure_elec_awm = (
        float(np.average(va["elevators_eui_kwh_m2"].values, weights=va["floor_area_m2"].values))
        if len(va) else 0.0
    )
    pure_elec_pct = 100 * pure_elec_awm / awm_b

    elev_a_nonzero = int((a["elevators_eui_kwh_m2"].fillna(0) > 0).sum())
    elev_b_nonzero = int((b["elevators_eui_kwh_m2"].fillna(0) > 0).sum())

    print("\n" + "=" * 72)
    print(f"OPEN-48 T03 ELEVATOR A/B RESULT — {info['cell']}")
    print("=" * 72)
    print(f"  Arm A (elevators): total EUI  median={med_a:.3f}  area-wt-mean={awm_a:.3f} kWh/m2")
    print(f"  Arm B (no elev):   total EUI  median={med_b:.3f}  area-wt-mean={awm_b:.3f} kWh/m2")
    print(f"  Delta (A-B):       median={d_med:+.3f} ({pct_med:+.2f}%)  "
          f"area-wt-mean={d_awm:+.3f} ({pct_awm:+.2f}%) kWh/m2")
    print(f"  Pure-electric adder (Arm A elevators_eui, area-wt): "
          f"{pure_elec_awm:.3f} kWh/m2 = {pure_elec_pct:+.2f}% of Arm B total")
    print(f"\n  elevators_eui_kwh_m2 > 0 count: Arm A = {elev_a_nonzero}/{len(a)}  "
          f"Arm B = {elev_b_nonzero}/{len(b)} (expect 0)")

    if d_awm == 0.0:
        print("\n  FLAG: delta is exactly zero — investigate, do NOT report as success.", file=sys.stderr)

    result = {
        "cell": info["cell"],
        "job_a": info["job_a"], "job_b": info["job_b"],
        "n_common": len(common), "n_parsed_a": len(df_a), "n_parsed_b": len(df_b),
        "median_a": med_a, "median_b": med_b,
        "awmean_a": awm_a, "awmean_b": awm_b,
        "delta_median_abs": d_med, "delta_median_pct": pct_med,
        "delta_awmean_abs": d_awm, "delta_awmean_pct": pct_awm,
        "pure_elec_adder_awm": pure_elec_awm, "pure_elec_adder_pct": pure_elec_pct,
        "elev_nonzero_a": elev_a_nonzero, "elev_nonzero_b": elev_b_nonzero,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2))
    print(f"\n  Result JSON -> {RESULT_PATH}")
    print("=" * 72)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["submit", "harvest"])
    args = ap.parse_args()
    if args.mode == "submit":
        submit()
    else:
        harvest()
