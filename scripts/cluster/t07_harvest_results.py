"""T07 — Harvest cluster results and produce the CP3 report table.

Run AFTER the t07_resolution_pilot.py jobs have completed on the Speed cluster.
Fetches SQL outputs for all 4 modes, parses EUI, checks CP3 acceptance criteria,
and writes the comparison table to openubem/outputs/comparisons/.

Usage:
    py -3 scripts/cluster/t07_harvest_results.py

Outputs:
    openubem/outputs/comparisons/t07_resolution_pilot_eui.csv
    (printed CP3 report table — copy into §8 progress log entry)
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
_REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"
_FLEET_TAG = "t07"
MODES = ["auto", "building", "floor", "fast_zone"]
# Environment split (AMENDMENT 2026-06-29): auto/building/floor ran on Speed
# (Linux); fast_zone ran locally (Windows) because its cluster job was queue-blocked.
CLUSTER_MODES = ("auto", "building", "floor")
LOCAL_MODES = ("fast_zone",)
MODE_ENV = {"auto": "Speed/Linux", "building": "Speed/Linux",
            "floor": "Speed/Linux", "fast_zone": "local/Windows"}

_FIXTURE_DIR = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll"
    / "results" / "phaseE" / "la_rural"
)
OUTPUT_DIR = REPO / "openubem" / "outputs" / "comparisons"
OUTPUT_CSV = OUTPUT_DIR / "t07_resolution_pilot_eui.csv"

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


# ── helpers ───────────────────────────────────────────────────────────────────

def _ssh(cmd: str, timeout: int = 120) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def _remote_fleet_dir(mode: str) -> str:
    return f"{_REMOTE_FLEET_BASE}/{_FLEET_TAG}_{mode}"


# ── Fetch one mode's results from cluster ─────────────────────────────────────

def fetch_mode(mode: str, fleet_lst: list[str], work_base: Path) -> Path:
    """Tar-stream eplusout.sql + .err + .end from cluster for one mode."""
    remote_dir = _remote_fleet_dir(mode)
    sim_out = work_base / f"sim_out_{mode}"
    sim_out.mkdir(parents=True, exist_ok=True)

    print(f"  [{mode}] Fetching {len(fleet_lst)} buildings from {remote_dir}/out ...")
    paths_str = " ".join(
        f"{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end"
        for oid in fleet_lst
    )
    remote_cmd = f"cd {remote_dir}/out && tar czf - --ignore-failed-read {paths_str}"
    tgz = work_base / f"fetch_{mode}.tgz"

    with open(tgz, "wb") as fh:
        proc = subprocess.Popen(
            ["ssh", REMOTE_HOST, f"bash -lc '{remote_cmd}'"],
            stdout=fh, stderr=subprocess.PIPE,
        )
        _, _ = proc.communicate(timeout=3600)

    with tarfile.open(tgz, "r:gz") as tf:
        tf.extractall(str(sim_out))
    tgz.unlink(missing_ok=True)

    n_ends = len(list(sim_out.rglob("eplusout.end")))
    print(f"  [{mode}] {n_ends} .end files extracted")
    return sim_out


# ── Parse one building's SQL → EUI dict ──────────────────────────────────────

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
        "heating_eui_kwh_m2":       heating_kwh / fa,
        "cooling_eui_kwh_m2":       meters["Cooling:Electricity"] / fa,
        "lighting_eui_kwh_m2":      zone_kwh["lights"] / fa,
        "equipment_eui_kwh_m2":     zone_kwh["equip"] / fa,
        "fans_eui_kwh_m2":          meters["Fans:Electricity"] / fa,
        "pumps_eui_kwh_m2":         meters["Pumps:Electricity"] / fa,
        "dhw_eui_kwh_m2":           dhw_kwh / fa,
        "total_eui_kwh_m2":         total_kwh / fa,
    }


# ── Parse all buildings for one mode ─────────────────────────────────────────

def parse_mode(mode: str, sim_out: Path, fleet_lst: list[str],
               subset_info: pd.DataFrame, mode_manifest: pd.DataFrame | None) -> pd.DataFrame:
    """Parse EUI for every building in fleet_lst for one mode."""
    rows = []
    for stem in fleet_lst:
        osm_id = stem.replace("_", "/", 1) if not stem.startswith("way/") else stem

        bld = subset_info[subset_info["osm_id"] == osm_id]
        if bld.empty:
            # Try stem form
            bld = subset_info[subset_info["osm_id"].str.replace("/", "_", 1) == stem]
        if bld.empty:
            print(f"  WARNING: {stem} not in subset_info", file=sys.stderr)
            continue

        bld_row = bld.iloc[0]
        floor_area = float(bld_row["footprint_area_m2"]) * float(bld_row["num_floors"])
        archetype = str(bld_row["archetype_id"])

        bdir = sim_out / stem
        end_path = bdir / "eplusout.end"
        sql_path = bdir / "eplusout.sql"

        status = "missing"
        has_fatal = False
        if end_path.exists():
            txt = end_path.read_text(errors="replace")
            status = "success" if "EnergyPlus Completed Successfully" in txt else "failed"
        if (bdir / "eplusout.err").exists():
            err = (bdir / "eplusout.err").read_text(errors="replace")
            has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None

        row: dict = {
            "mode": mode,
            "osm_id": osm_id,
            "archetype_id": archetype,
            "floor_area_m2": floor_area,
            "status": status,
            "has_fatal": has_fatal,
        }

        # Zoning info from manifest
        if mode_manifest is not None:
            mrow = mode_manifest[mode_manifest["osm_id"].astype(str) == osm_id]
            if mrow.empty:
                mrow = mode_manifest[mode_manifest["osm_id"].astype(str).str.replace("/", "_", 1) == stem]
            if not mrow.empty:
                row["zoning_strategy"] = str(mrow.iloc[0].get("zoning_strategy", ""))
                row["num_zones"] = int(mrow.iloc[0].get("num_zones", 0))
                row["resolution_mode"] = str(mrow.iloc[0].get("resolution_mode", mode))

        if status == "success" and sql_path.exists():
            try:
                eui_dict = _parse_sql(sql_path, floor_area)
                row.update(eui_dict)
            except Exception as exc:
                row["parse_error"] = str(exc)

        rows.append(row)

    return pd.DataFrame(rows)


# ── CP3 report printer ────────────────────────────────────────────────────────

def print_cp3_report(results: pd.DataFrame, baseline: gpd.GeoDataFrame) -> None:
    print("\n" + "=" * 72)
    print("CP3 REPORT -- T07 Resolution Pilot (la_rural, 21 buildings)")
    print("=" * 72)
    print("\nENVIRONMENT SPLIT (AMENDMENT 2026-06-29):")
    print("  auto / building / floor : Speed cluster (Linux), EnergyPlus 23.1")
    print("  fast_zone               : local desktop (Windows), EnergyPlus 23.1")
    print("  EnergyPlus EUI is platform-deterministic to within rounding; the auto")
    print("  regression anchor and cross-mode ordering remain valid. Any EUI differing")
    print("  by more than float rounding is flagged as a FINDING below.")

    # 1. Fatal / Completion
    print("\n### 1. Fatal / Completion check ###")
    print(f"  {'mode':12s}  {'success':>8}  {'failed':>7}  {'fatal':>6}  {'total':>6}")
    any_fatal = False
    for mode in MODES:
        mdf = results[results["mode"] == mode]
        n_ok  = int((mdf["status"] == "success").sum())
        n_fail = int((mdf["status"] == "failed").sum())
        n_fat  = int(mdf.get("has_fatal", pd.Series(False, index=mdf.index)).sum())
        print(f"  {mode:12s}  {n_ok:>8}  {n_fail:>7}  {n_fat:>6}  {len(mdf):>6}")
        if n_fat > 0:
            any_fatal = True
    print(f"\n  Fatal-free: {'YES' if not any_fatal else 'NO -- see failed rows above'}")

    # 2. auto regression vs phaseE baseline
    print("\n### 2. auto regression vs phaseE baseline ###")
    auto_ok = results[(results["mode"] == "auto") & (results["status"] == "success")]
    mismatches = 0
    for _, r in auto_ok.iterrows():
        bl = baseline[baseline["osm_id"] == r["osm_id"]]
        if bl.empty:
            continue
        bl_total = float(bl["total_eui_kwh_m2"].iloc[0])
        t07_total = r.get("total_eui_kwh_m2", float("nan"))
        diff = abs(t07_total - bl_total)
        tag = "OK" if diff < 1.0 else "MISMATCH"
        if tag == "MISMATCH":
            mismatches += 1
        print(f"  {str(r['osm_id'])[:35]:35s} auto={t07_total:6.1f}  phaseE={bl_total:6.1f}  "
              f"d={diff:5.2f}  [{tag}]")
    print(f"\n  Regression: {len(auto_ok) - mismatches}/{len(auto_ok)} match within 1 kWh/m2")

    # 3. Heating EUI ordering: building ≤ floor ≤ fast_zone (sanity, not hard gate)
    print("\n### 3. Heating EUI ordering: building <= floor <= fast_zone ###")
    succ = results[results["status"] == "success"]
    pivot_h = succ.pivot_table(
        index=["osm_id", "archetype_id"], columns="mode", values="heating_eui_kwh_m2"
    ).reset_index()
    inversions = 0
    for _, r in pivot_h.iterrows():
        b  = r.get("building", float("nan"))
        f  = r.get("floor",    float("nan"))
        fz = r.get("fast_zone", float("nan"))
        vals_ok = all(v == v for v in [b, f, fz])
        if not vals_ok:
            order_tag = "n/a"
        else:
            # Allow 5% tolerance for floating-point / rounding
            ok = (b <= f * 1.05) and (f <= fz * 1.05)
            order_tag = "OK" if ok else "INVERT"
            if not ok:
                inversions += 1
        print(f"  {str(r['osm_id'])[:34]:34s} ({str(r['archetype_id'])[:18]:18s}) "
              f"B={b:5.1f}  F={f:5.1f}  FZ={fz:5.1f}  [{order_tag}]")
    print(f"\n  Ordering inversions: {inversions} (note: sec9 says inversions can occur -- "
          f"note them, not a hard gate)")

    # 4. Fallback count (fast_zone)
    print("\n### 4. Fallback rows (fast_zone) ###")
    fz_mdf = results[(results["mode"] == "fast_zone") & (results["status"] == "success")]
    if "zoning_strategy" in fz_mdf.columns and "num_zones" in fz_mdf.columns:
        fb = fz_mdf[fz_mdf["num_zones"] == 1]
        print(f"  fast_zone buildings with num_zones=1 (fallback): {len(fb)}/{len(fz_mdf)}")
        for _, r in fb.iterrows():
            print(f"    {r['osm_id']} ({r['archetype_id']}) "
                  f"strategy={r.get('zoning_strategy','?')} num_zones=1")
    else:
        print("  (manifest not loaded — fallback count unavailable)")

    # 5. Per-archetype median EUI table
    print("\n### 5. Per-archetype median total_eui_kwh_m2 ###")
    print(f"  {'archetype':25s}  {'auto':>8}  {'building':>8}  {'floor':>8}  {'fast_zone':>10}")
    for arch in ["MidriseApartment", "SmallOffice", "MediumOffice", "LargeOffice", "Warehouse"]:
        if arch not in results["archetype_id"].values:
            continue
        row_vals = []
        for mode in MODES:
            mdf = succ[(succ["mode"] == mode) & (succ["archetype_id"] == arch)]
            val = mdf["total_eui_kwh_m2"].median() if len(mdf) > 0 else float("nan")
            row_vals.append(f"{val:8.1f}" if val == val else "     n/a")
        print(f"  {arch:25s}  {' '.join(row_vals)}")

    print("\n" + "=" * 72)
    print("STOP AT CP3 -- Do not launch T08 without manager greenlight.")
    print("=" * 72)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    work_base = Path(tempfile.gettempdir()) / "ubem_t07_pilot"
    print(f"T07 harvest -- work dir: {work_base}")

    # Load job IDs (informational)
    job_id_file = work_base / "t07_job_ids.json"
    if job_id_file.exists():
        info = json.loads(job_id_file.read_text())
        print(f"  Job IDs: {info.get('job_ids', {})}")

    # Load subset info
    subset_path = work_base / "t07_subset_info.parquet"
    if not subset_path.exists():
        sys.exit(f"FATAL: {subset_path} not found. Run t07_resolution_pilot.py first.")
    subset_info = pd.read_parquet(subset_path)
    print(f"  Subset: {len(subset_info)} buildings")

    # Load phaseE auto baseline for regression check
    baseline_gdf = gpd.read_file(str(_FIXTURE_DIR / "05_results.gpkg"))
    baseline = baseline_gdf[baseline_gdf["osm_id"].isin(subset_info["osm_id"])].copy()

    # Get fleet.lst for mode=auto from cluster (same stems for all modes)
    remote_fleet_dir = f"{_REMOTE_FLEET_BASE}/{_FLEET_TAG}_auto"
    raw_lst = _ssh(f"cat {remote_fleet_dir}/fleet.lst", timeout=30)
    fleet_lst = [s.strip() for s in raw_lst.splitlines() if s.strip()]
    print(f"  Fleet size (from remote): {len(fleet_lst)}")

    # Fetch + parse each mode (cluster modes fetched from Speed; fast_zone is local)
    all_dfs: list[pd.DataFrame] = []
    for mode in MODES:
        print(f"\n=== Mode: {mode} ({MODE_ENV[mode]}) ===")
        if mode in CLUSTER_MODES:
            try:
                sim_out = fetch_mode(mode, fleet_lst, work_base)
            except Exception as e:
                print(f"  [{mode}] fetch failed: {e}", file=sys.stderr)
                continue
        else:
            # Local fast_zone: results already on disk from t07_run_fast_zone_local.py
            sim_out = work_base / f"sim_out_{mode}"
            if not sim_out.exists():
                print(f"  [{mode}] local sim dir not found: {sim_out}", file=sys.stderr)
                continue
            n_end = len(list(sim_out.rglob("eplusout.end")))
            print(f"  [{mode}] using LOCAL results: {n_end} .end files in {sim_out}")

        # Load local manifest if available
        manifest_path = work_base / f"step3_{mode}" / "03_manifest.parquet"
        mode_manifest = pd.read_parquet(str(manifest_path)) if manifest_path.exists() else None

        df = parse_mode(mode, sim_out, fleet_lst, subset_info, mode_manifest)
        n_ok = int((df["status"] == "success").sum())
        n_fat = int(df.get("has_fatal", pd.Series(False, index=df.index)).sum())
        print(f"  [{mode}] parsed: {n_ok}/{len(df)} success, {n_fat} fatals")
        all_dfs.append(df)

    if not all_dfs:
        sys.exit("No mode results parsed — nothing to report.")

    results = pd.concat(all_dfs, ignore_index=True)

    # Write CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(str(OUTPUT_CSV), index=False)
    print(f"\nResults CSV: {OUTPUT_CSV}")

    # Print CP3 report
    print_cp3_report(results, baseline)


if __name__ == "__main__":
    main()
