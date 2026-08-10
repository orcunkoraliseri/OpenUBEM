"""T07b -- Re-run Step-3 for `auto` mode with the orient() gate fix, then run
EnergyPlus 23.1 locally and compare results against phaseE la_rural baseline.

This script:
  1. Loads the existing 21-building subset from the T07 pilot work directory.
  2. Re-runs Step 3 (IDF generation) for resolution_mode="auto" using the
     FIXED builder (orient() gated out of auto).
  3. Runs EnergyPlus on every IDF using installed EnergyPlus 23.1.
  4. Parses SQL outputs, computes per-end-use EUI.
  5. Compares against phaseE la_rural 05_results.gpkg.
  6. Writes results to openubem/outputs/comparisons/t07_auto_refit_eui.csv.
  7. Prints the 21-row auto-vs-phaseE match table.

Usage:
    py -3 scripts/cluster/t07b_run_auto_refit_local.py
"""
from __future__ import annotations

import re
import shutil
import sqlite3
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

EP_DIR = Path(r"C:\EnergyPlusV23-1-0")
EP_EXE = EP_DIR / "energyplus.exe"
EXPAND_EXE = EP_DIR / "ExpandObjects.exe"
EP_IDD = EP_DIR / "Energy+.idd"

WORK_BASE = Path(__file__).resolve().parent.parent.parent / "scripts" / "cluster"
# Re-use the T07 pilot work base
import tempfile
PILOT_BASE = Path(tempfile.gettempdir()) / "ubem_t07_pilot"

STEP3_OUT = PILOT_BASE / "step3_auto_refit"
SIM_OUT = PILOT_BASE / "sim_out_auto_refit"

_FIXTURE_DIR = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll"
    / "results" / "phaseE" / "la_rural"
)
OUTPUT_DIR = REPO / "openubem" / "outputs" / "comparisons"
OUTPUT_CSV = OUTPUT_DIR / "t07_auto_refit_eui.csv"

J_TO_KWH = 1.0 / 3.6e6

_METER_NAMES = (
    "Cooling:Electricity",
    "Heating:Electricity",
    "Heating:NaturalGas",
    "Fans:Electricity",
    "Pumps:Electricity",
    "WaterSystems:NaturalGas",
    "WaterSystems:Electricity",
    "InteriorEquipment:NaturalGas",
    "Refrigeration:Electricity",
)
_METER_SQL = (
    "SELECT d.Name, r.Value "
    "FROM ReportData r "
    "JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex "
    "WHERE d.ReportingFrequency = 'Run Period' "
    f"AND d.Name IN ({', '.join(repr(m) for m in _METER_NAMES)})"
)
_ZONE_SQL = (
    "SELECT d.Name, SUM(r.Value) "
    "FROM ReportData r "
    "JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex "
    "WHERE d.Name IN ('Zone Lights Electricity Energy', 'Zone Electric Equipment Electricity Energy') "
    "GROUP BY d.Name"
)


# ── Step 3 re-run (auto mode, fixed builder) ──────────────────────────────────

def rerun_step3_auto(pilot_base: Path, step3_out: Path) -> pd.DataFrame:
    """Re-run Step 3 for resolution_mode='auto' on the T07 pilot subset."""
    from openubem.idf.builder import run_step3

    subset_path = pilot_base / "t07_subset_info.parquet"
    if not subset_path.exists():
        sys.exit(f"FATAL: T07 subset not found at {subset_path}. Run t07_resolution_pilot.py first.")

    subset_info = pd.read_parquet(str(subset_path))
    print(f"  Loaded {len(subset_info)} buildings from T07 subset")

    # Load enriched GDF from T07 step3_auto (enrichment is the same regardless of resolution mode)
    # We re-use the original buildings file + re-enrich, or just use the cached step2 GDF.
    # The cleanest approach: reload raw buildings + re-run enrich (identical to T07 step2).
    buildings_path = _FIXTURE_DIR / "01_buildings.gpkg"
    if not buildings_path.exists():
        sys.exit(f"FATAL: la_rural buildings fixture not found at {buildings_path}")

    gdf_raw = gpd.read_file(str(buildings_path))
    print(f"  Loaded {len(gdf_raw)} raw buildings from la_rural fixture")

    # Resolve EPW
    epw_path = pilot_base / "weather" / "weather" / "USA_CA_Lancaster-Fox.Field.723816_TMYx.2011-2025.epw"
    if not epw_path.exists():
        # Try one level up
        epw_path = pilot_base / "weather" / "USA_CA_Lancaster-Fox.Field.723816_TMYx.2011-2025.epw"
    if not epw_path.exists():
        # Find any .epw in weather dir
        epw_candidates = list((pilot_base / "weather").rglob("*.epw"))
        if epw_candidates:
            epw_path = epw_candidates[0]
        else:
            sys.exit(f"FATAL: EPW not found under {pilot_base / 'weather'}")
    print(f"  EPW: {epw_path}")

    # Re-run semantic enrichment
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")

    print("  Classifying buildings ...")
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

    print("  Enriching semantics ...")
    gdf_57, schedule_library = enrich_semantics(gdf_29)
    print(f"  Enrichment complete: {len(gdf_57)} buildings")

    # Select the same 21-building subset as T07
    _TARGET_COUNTS = {
        "MidriseApartment": 5,
        "SmallOffice":      5,
        "MediumOffice":     5,
        "LargeOffice":      1,
        "Warehouse":        5,
    }
    parts = []
    for arch, count in _TARGET_COUNTS.items():
        cands = gdf_57[gdf_57["archetype_id"] == arch]
        taken = cands.head(count)
        print(f"  {arch}: selected {len(taken)} (requested {count})")
        parts.append(taken)
    subset_gdf = gpd.GeoDataFrame(
        pd.concat(parts, ignore_index=True), geometry="geometry", crs=gdf_57.crs
    )
    print(f"  Total subset: {len(subset_gdf)} buildings")

    # Run Step 3 with resolution_mode="auto" (the fixed builder)
    step3_out.mkdir(parents=True, exist_ok=True)
    (step3_out / "idfs").mkdir(exist_ok=True)

    print(f"  Running Step 3 (mode=auto, n={len(subset_gdf)}) with FIXED builder ...")
    t0 = time.monotonic()
    manifest = run_step3(subset_gdf, schedule_library, step3_out, n_jobs=1, resolution_mode="auto")
    elapsed = time.monotonic() - t0

    n_ok = int((manifest["generation_status"] == "success").sum())
    print(f"  Step 3 [auto-refit]: {n_ok}/{len(manifest)} success in {elapsed:.1f}s")
    manifest.to_parquet(str(step3_out / "03_manifest.parquet"), index=False)

    return manifest


# ── EnergyPlus runner (same as t07_run_fast_zone_local.py) ───────────────────

def run_one(args: tuple[str, str, str, str]) -> tuple[str, str, int]:
    idf_path_str, outdir_str, ep_exe_str, epw_str = args
    idf_path = Path(idf_path_str)
    outdir = Path(outdir_str)
    outdir.mkdir(parents=True, exist_ok=True)

    ep_idd = Path(ep_exe_str).parent / "Energy+.idd"
    shutil.copy(str(ep_idd), str(outdir / "Energy+.idd"))
    shutil.copy(str(idf_path), str(outdir / "in.idf"))

    expand_exe = Path(ep_exe_str).parent / "ExpandObjects.exe"
    subprocess.run([str(expand_exe)], cwd=str(outdir),
                   capture_output=True, text=True, timeout=300)
    run_idf = outdir / "expanded.idf"
    if not run_idf.exists():
        run_idf = outdir / "in.idf"

    proc = subprocess.run(
        [ep_exe_str, "-w", epw_str, "-d", str(outdir), str(run_idf)],
        cwd=str(outdir), capture_output=True, text=True, timeout=3600,
    )
    rc = proc.returncode
    (outdir / "task.rc").write_text(str(rc))

    status = "unknown"
    end_path = outdir / "eplusout.end"
    if end_path.exists():
        txt = end_path.read_text(errors="replace")
        status = "success" if "EnergyPlus Completed Successfully" in txt else "failed"
    else:
        status = f"no-end(rc={rc})"
    return idf_path.stem, status, rc


def run_simulations(manifest: pd.DataFrame, sim_out: Path, epw_path: Path) -> None:
    if not EP_EXE.exists():
        sys.exit(f"FATAL: EnergyPlus not found at {EP_EXE}")
    if not epw_path.exists():
        sys.exit(f"FATAL: EPW not found at {epw_path}")

    success_rows = manifest[manifest["generation_status"] == "success"]
    idfs = [Path(str(r["idf_path"])) for _, r in success_rows.iterrows() if pd.notna(r.get("idf_path"))]
    if not idfs:
        sys.exit("FATAL: no successful IDFs in manifest")

    sim_out.mkdir(parents=True, exist_ok=True)
    print(f"\nRunning {len(idfs)} auto-refit IDFs locally with EnergyPlus 23.1")
    print(f"  EP:  {EP_EXE}")
    print(f"  EPW: {epw_path}")
    print(f"  OUT: {sim_out}")

    args_list = [
        (str(idf), str(sim_out / idf.stem), str(EP_EXE), str(epw_path))
        for idf in idfs
    ]

    t0 = time.monotonic()
    results = []
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(run_one, a): a[0] for a in args_list}
        for fut in as_completed(futs):
            stem, status, rc = fut.result()
            results.append((stem, status, rc))
            print(f"  [{status:18s}] {stem} (rc={rc})")

    elapsed = time.monotonic() - t0
    n_ok = sum(1 for _, s, _ in results if s == "success")
    print(f"\nDone: {n_ok}/{len(results)} success in {elapsed:.1f}s")
    failed = [(s, st, rc) for s, st, rc in results if st != "success"]
    if failed:
        print("FAILED:")
        for s, st, rc in failed:
            print(f"  {s}: {st} (rc={rc})")


# ── Parse SQL + compare ───────────────────────────────────────────────────────

def _parse_sql(sql_path: Path, floor_area: float) -> dict[str, float]:
    meters = dict.fromkeys(_METER_NAMES, 0.0)
    zone_kwh = {"lights": 0.0, "equip": 0.0}

    with sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True) as conn:
        for name, val_j in conn.execute(_METER_SQL).fetchall():
            if name in meters and val_j is not None:
                meters[name] += float(val_j) * J_TO_KWH
        for name, total_j in conn.execute(_ZONE_SQL).fetchall():
            if total_j is not None:
                if "Lights" in name:
                    zone_kwh["lights"] = float(total_j) * J_TO_KWH
                elif "Electric Equipment" in name:
                    zone_kwh["equip"] = float(total_j) * J_TO_KWH

    heating_kwh = meters["Heating:Electricity"] + meters["Heating:NaturalGas"]
    dhw_kwh = meters["WaterSystems:NaturalGas"] + meters["WaterSystems:Electricity"]
    total_kwh = (
        heating_kwh
        + meters["Cooling:Electricity"]
        + zone_kwh["lights"]
        + zone_kwh["equip"]
        + meters["Fans:Electricity"]
        + meters["Pumps:Electricity"]
        + dhw_kwh
        + meters["InteriorEquipment:NaturalGas"]
        + meters["Refrigeration:Electricity"]
    )
    fa = float(floor_area)
    return {
        "heating_eui_kwh_m2":   heating_kwh / fa,
        "cooling_eui_kwh_m2":   meters["Cooling:Electricity"] / fa,
        "lighting_eui_kwh_m2":  zone_kwh["lights"] / fa,
        "equipment_eui_kwh_m2": zone_kwh["equip"] / fa,
        "fans_eui_kwh_m2":      meters["Fans:Electricity"] / fa,
        "pumps_eui_kwh_m2":     meters["Pumps:Electricity"] / fa,
        "dhw_eui_kwh_m2":       dhw_kwh / fa,
        "total_eui_kwh_m2":     total_kwh / fa,
    }


def harvest_and_compare(manifest: pd.DataFrame, sim_out: Path,
                        subset_info: pd.DataFrame) -> pd.DataFrame:
    baseline_gdf = gpd.read_file(str(_FIXTURE_DIR / "05_results.gpkg"))

    rows = []
    for _, mrow in manifest.iterrows():
        osm_id = str(mrow["osm_id"])
        status_gen = str(mrow.get("generation_status", "unknown"))

        sub = subset_info[subset_info["osm_id"] == osm_id]
        if sub.empty:
            continue
        sub_row = sub.iloc[0]
        floor_area = float(sub_row["footprint_area_m2"]) * float(sub_row["num_floors"])
        archetype = str(sub_row["archetype_id"])

        stem = osm_id.replace("/", "_", 1)
        bdir = sim_out / stem
        end_path = bdir / "eplusout.end"
        sql_path = bdir / "eplusout.sql"

        sim_status = "missing"
        has_fatal = False
        if end_path.exists():
            txt = end_path.read_text(errors="replace")
            sim_status = "success" if "EnergyPlus Completed Successfully" in txt else "failed"
        if (bdir / "eplusout.err").exists():
            err = (bdir / "eplusout.err").read_text(errors="replace")
            has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None

        row: dict = {
            "mode":             "auto",
            "osm_id":           osm_id,
            "archetype_id":     archetype,
            "floor_area_m2":    floor_area,
            "generation_status": status_gen,
            "zoning_strategy":  str(mrow.get("zoning_strategy", "")),
            "num_zones":        int(mrow.get("num_zones", 0)) if pd.notna(mrow.get("num_zones")) else 0,
            "status":           sim_status,
            "has_fatal":        has_fatal,
        }

        if sim_status == "success" and sql_path.exists():
            try:
                eui_dict = _parse_sql(sql_path, floor_area)
                row.update(eui_dict)
            except Exception as exc:
                row["parse_error"] = str(exc)

        # phaseE baseline
        bl = baseline_gdf[baseline_gdf["osm_id"] == osm_id]
        if not bl.empty:
            row["phaseE_total_eui"] = float(bl["total_eui_kwh_m2"].iloc[0])
            row["phaseE_heating_eui"] = float(bl.get("heating_eui_kwh_m2", pd.Series([float("nan")])).iloc[0]) if "heating_eui_kwh_m2" in bl.columns else float("nan")

        rows.append(row)

    return pd.DataFrame(rows)


def print_match_table(df: pd.DataFrame) -> None:
    print("\n" + "=" * 80)
    print("CP3b REPORT -- T07b auto-refit vs phaseE (21 buildings, la_rural)")
    print("=" * 80)
    print(f"\n{'osm_id':35s}  {'archetype':20s}  {'auto':>7}  {'phaseE':>7}  {'delta':>7}  result")
    print("-" * 90)
    n_ok = 0
    n_total = 0
    for _, r in df.iterrows():
        osm_id = str(r["osm_id"])
        arch = str(r["archetype_id"])
        auto_total = r.get("total_eui_kwh_m2", float("nan"))
        phase_e = r.get("phaseE_total_eui", float("nan"))
        if auto_total != auto_total or phase_e != phase_e:
            tag = "MISSING"
        else:
            delta = abs(auto_total - phase_e)
            tag = "OK" if delta < 1.0 else "MISMATCH"
            if tag == "OK":
                n_ok += 1
            n_total += 1
            delta_str = f"{auto_total - phase_e:+.2f}"
            print(f"{osm_id[:35]:35s}  {arch[:20]:20s}  {auto_total:7.1f}  {phase_e:7.1f}  {delta_str:>7}  {tag}")
            continue
        print(f"{osm_id[:35]:35s}  {arch[:20]:20s}  {'n/a':>7}  {'n/a':>7}  {'n/a':>7}  {tag}")

    print("-" * 90)
    print(f"\n  TOTAL: {n_ok}/{n_total} match within 1 kWh/m2 total EUI")
    all_ok = (n_ok == n_total)
    print(f"  ACCEPTANCE: {'PASS' if all_ok else 'FAIL -- see MISMATCH rows above'}")

    # Highlight office rows specifically
    print("\n  Office rows (MediumOffice + LargeOffice):")
    office_rows = df[df["archetype_id"].isin(["MediumOffice", "LargeOffice"])]
    for _, r in office_rows.iterrows():
        auto_t = r.get("total_eui_kwh_m2", float("nan"))
        phase_t = r.get("phaseE_total_eui", float("nan"))
        if auto_t == auto_t and phase_t == phase_t:
            delta = auto_t - phase_t
            tag = "OK" if abs(delta) < 1.0 else "MISMATCH"
            print(f"    {str(r['osm_id'])[:40]:40s}  {str(r['archetype_id']):14s}  "
                  f"auto={auto_t:.1f}  phaseE={phase_t:.1f}  d={delta:+.2f}  [{tag}]")

    print("\n" + "=" * 80)
    print("STOP AT CP3b -- await manager confirmation before T08.")
    print("=" * 80)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("T07b -- auto-refit pilot (local EnergyPlus 23.1)")
    print(f"  PILOT_BASE: {PILOT_BASE}")
    print(f"  STEP3_OUT:  {STEP3_OUT}")
    print(f"  SIM_OUT:    {SIM_OUT}")
    print(f"  OUTPUT_CSV: {OUTPUT_CSV}")

    if not EP_EXE.exists():
        sys.exit(f"FATAL: EnergyPlus 23.1 not found at {EP_EXE}")

    # 1. Re-run Step 3 for auto mode with fixed builder
    print("\n=== Step 1: Re-run Step 3 (auto, fixed builder) ===")
    manifest = rerun_step3_auto(PILOT_BASE, STEP3_OUT)

    # 2. Run EnergyPlus locally
    epw_path = None
    for candidate in [
        PILOT_BASE / "weather" / "weather" / "USA_CA_Lancaster-Fox.Field.723816_TMYx.2011-2025.epw",
        PILOT_BASE / "weather" / "USA_CA_Lancaster-Fox.Field.723816_TMYx.2011-2025.epw",
    ]:
        if candidate.exists():
            epw_path = candidate
            break
    if epw_path is None:
        epw_candidates = list((PILOT_BASE / "weather").rglob("*.epw"))
        if epw_candidates:
            epw_path = epw_candidates[0]
        else:
            sys.exit("FATAL: No EPW found in pilot weather dir")

    print("\n=== Step 2: EnergyPlus simulation ===")
    run_simulations(manifest, SIM_OUT, epw_path)

    # 3. Parse + compare
    print("\n=== Step 3: Parse results + compare with phaseE ===")
    subset_info = pd.read_parquet(str(PILOT_BASE / "t07_subset_info.parquet"))
    results_df = harvest_and_compare(manifest, SIM_OUT, subset_info)

    # 4. Write CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(str(OUTPUT_CSV), index=False)
    print(f"\nResults written to: {OUTPUT_CSV}")

    # 5. Print match table
    print_match_table(results_df)


if __name__ == "__main__":
    main()
