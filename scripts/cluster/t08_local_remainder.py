"""T08 local remainder — run 12 cells x 5 modes on Windows desktop EnergyPlus 23.1.

Covers: nyc_centre, nyc_urban, nyc_suburban, nyc_rural, la_centre, la_urban,
        la_suburban, la_rural, austin_centre, austin_urban, austin_suburban,
        austin_rural — all 5 modes each (auto, building, floor, fast_zone,
        layout_assign).

Reuses t08_full_sweep.run_step2 / run_step3_mode for Steps 1-3.
Runs EnergyPlus locally (mirrors t07b_run_auto_refit_local.py runner).
Harvests to t08_local_remainder_eui.csv (or --output-csv) matching
t08_harvest_results.py schema.
Provenance: platform=Windows-local.

Auto regression check is STRICT (<1 kWh/m2) — same Windows platform as phaseE baseline.

Usage:
    py -3 scripts/cluster/t08_local_remainder.py [--cells ...] [--modes ...]
    py -3 scripts/cluster/t08_local_remainder.py --cells la_urban la_rural --modes auto building
    py -3 scripts/cluster/t08_local_remainder.py --output-csv <path> --work-base <path>

Resumable: skip (cell, mode) pairs where sim_done.txt is already present in the sim_out dir.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

EP_DIR = Path(r"C:\EnergyPlusV23-1-0")
EP_EXE = EP_DIR / "energyplus.exe"
EP_IDD = EP_DIR / "Energy+.idd"

PHASED_RESULTS = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
)
OUTPUT_DIR = REPO / "openubem" / "outputs" / "comparisons"
OUTPUT_CSV = OUTPUT_DIR / "t08_local_remainder_eui.csv"

LOCAL_CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]
ALL_MODES = ["auto", "building", "floor", "fast_zone", "layout_assign"]

CITY_OF = {
    "nyc_centre": "NYC", "nyc_urban": "NYC", "nyc_suburban": "NYC", "nyc_rural": "NYC",
    "la_centre": "LA", "la_urban": "LA", "la_suburban": "LA", "la_rural": "LA",
    "austin_centre": "AUS", "austin_urban": "AUS",
    "austin_suburban": "AUS", "austin_rural": "AUS",
}

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

# ── output trimming (E01) ──────────────────────────────────────────────────
# Reference delete list: scripts/cluster/submit_fleet_t08.sbatch:62-80, minus *.eio.
# eplusout.eio must never be deleted — it is the only record of simulated floor area.
RETAIN_FILENAMES = ("eplusout.eio", "eplusout.sql", "eplusout.err", "eplusout.end", "task.rc")

TRIM_DELETE_GLOBS = (
    "*.eso", "*.mtd", "*.rdd", "*.mdd", "*.htm", "*.tab", "*.csv",
    "in.idf", "expanded.idf", "Energy+.idd",
    "eplusout.dxf", "eplusout.audit", "eplusout.bnd", "eplusout.dbg",
    "eplusout.sln", "eplusout.rvaudit", "eplusmtr.*", "eplusout.mtr",
)

DISK_FLOOR_BYTES = 50 * 1_000_000_000  # 50 GB floor (decimal GB), E01 spec

_CUMULATIVE_RETAINED_BYTES = 0  # accumulated across the whole local pass (main process only)


def trim_output_dir(outdir: Path) -> int:
    """Delete bulk EnergyPlus output, scoped to outdir only (never above it, never recursive).
    Idempotent: re-running on an already-trimmed dir deletes nothing and raises nothing.
    Returns bytes of everything left in outdir after trimming (F2) — i.e. what this building
    actually costs on disk, not just the sum of RETAIN_FILENAMES. EnergyPlus leaves files
    outside both the delete list and RETAIN_FILENAMES (e.g. eplusout.shd, sqlite.err); those
    are correctly kept (cluster parity — submit_fleet_t08.sbatch does not delete them either)
    and must be counted, not silently dropped from the reported budget."""
    for pattern in TRIM_DELETE_GLOBS:
        for f in outdir.glob(pattern):
            if f.is_file():
                try:
                    f.unlink()
                except FileNotFoundError:
                    pass
    return sum(f.stat().st_size for f in outdir.iterdir() if f.is_file())


def free_disk_bytes(path: Path) -> int:
    return shutil.disk_usage(str(path)).free


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
    "InteriorLights:Electricity",
    "InteriorEquipment:Electricity",
    "Cooking:InteriorEquipment:Electricity",
    "Refrigeration:InteriorEquipment:Electricity",
)
_METER_SQL = (
    "SELECT d.Name, r.Value "
    "FROM ReportData r "
    "JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex "
    "WHERE d.ReportingFrequency = 'Run Period' "
    "AND d.Name IN ({meters})"
).format(meters=", ".join(repr(m) for m in _METER_NAMES))

_ZONE_SQL = (
    "SELECT d.Name, SUM(r.Value) "
    "FROM ReportData r "
    "JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex "
    "WHERE d.Name IN ('Zone Lights Electricity Energy', 'Zone Electric Equipment Electricity Energy') "
    "GROUP BY d.Name"
)


# ── safety gate ───────────────────────────────────────────────────────────────

def _verify_orient_gate() -> None:
    builder_path = REPO / "openubem" / "idf" / "builder.py"
    src = builder_path.read_text(encoding="utf-8")
    gate = 'if self.resolution_mode != "auto":'
    if gate not in src:
        sys.exit(
            "STOP: orient() gate not found in builder.py.\n"
            "Expected: `if self.resolution_mode != \"auto\":` before the orient() call.\n"
            "Aborting — do not generate any IDF."
        )
    print("  [GATE OK] builder.py has the auto orient() gate.")


# ── done markers (resume support) ────────────────────────────────────────────

def _done_path(cell: str, mode: str, work_base: Path) -> Path:
    return work_base / cell / f"sim_out_{mode}" / "sim_done.txt"


def is_done(cell: str, mode: str, work_base: Path) -> bool:
    return _done_path(cell, mode, work_base).exists()


def mark_done(cell: str, mode: str, work_base: Path, n_ok: int, n_total: int) -> None:
    p = _done_path(cell, mode, work_base)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"{cell}/{mode}: {n_ok}/{n_total} success\n"
        f"platform=Windows-local\n"
        f"timestamp={time.strftime('%Y-%m-%dT%H:%M:%S')}\n"
    )


# ── cell metadata from phaseE fixture ────────────────────────────────────────

def build_cell_info(cell: str) -> pd.DataFrame:
    fixture_dir = PHASED_RESULTS / cell
    results_path = fixture_dir / "05_results.gpkg"
    if not results_path.exists():
        return pd.DataFrame(columns=["osm_id", "archetype_id", "floor_area_m2", "phaseE_total_eui"])
    gdf = gpd.read_file(str(results_path))
    rows = []
    for _, r in gdf.iterrows():
        fa = float(r.get("footprint_area_m2", 0)) * max(1, int(r.get("levels", 1) or 1))
        rows.append({
            "osm_id": str(r["osm_id"]),
            "archetype_id": str(r.get("archetype_id", "")),
            "floor_area_m2": fa,
            "phaseE_total_eui": float(r.get("total_eui_kwh_m2", float("nan"))),
        })
    return pd.DataFrame(rows)


# ── EnergyPlus runner (local, mirrors submit_fleet.sbatch) ───────────────────

def _run_one_ep(args: tuple[str, str, str, str]) -> tuple[str, str, int, int]:
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
        cwd=str(outdir), capture_output=True, text=True, timeout=7200,
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

    # Trim immediately, success or failure — peak disk is the constraint (E01).
    retained_bytes = trim_output_dir(outdir)
    return idf_path.stem, status, rc, retained_bytes


def run_simulations(manifest: pd.DataFrame, cell: str, mode: str,
                    work_base: Path, epw_path: Path, n_workers: int) -> Path:
    """Run EnergyPlus on all successful IDFs for one (cell, mode). Returns sim_out dir."""
    if not EP_EXE.exists():
        sys.exit(f"FATAL: EnergyPlus not found at {EP_EXE}")

    sim_out = work_base / cell / f"sim_out_{mode}"
    sim_out.mkdir(parents=True, exist_ok=True)

    success_rows = manifest[manifest["generation_status"] == "success"]
    idfs = [
        Path(str(r["idf_path"]))
        for _, r in success_rows.iterrows()
        if pd.notna(r.get("idf_path"))
    ]
    if not idfs:
        print(f"  [{cell}/{mode}] no successful IDFs to simulate")
        return sim_out

    # Skip already-simulated buildings (resume within a mode)
    pending = [p for p in idfs if not (sim_out / p.stem / "eplusout.end").exists()]
    already_done = len(idfs) - len(pending)
    if already_done > 0:
        print(f"  [{cell}/{mode}] resuming: {already_done} already simulated, {len(pending)} pending")

    if not pending:
        print(f"  [{cell}/{mode}] all {len(idfs)} already simulated")
        return sim_out

    print(f"  [{cell}/{mode}] running {len(pending)} simulations (n_workers={n_workers}) ...")
    args_list = [
        (str(idf), str(sim_out / idf.stem), str(EP_EXE), str(epw_path))
        for idf in pending
    ]

    global _CUMULATIVE_RETAINED_BYTES
    last_completed_stem: str | None = None
    disk_guard_tripped = False

    t0 = time.monotonic()
    results = []
    pending_iter = iter(args_list)

    # F1: submission is throttled to at most n_workers in flight so the disk guard observes
    # real disk state (ProcessPoolExecutor.submit() is non-blocking with an unbounded queue —
    # handing it every pending building up front meant every guard check ran before any
    # simulation had written a byte). The initial window is submitted unconditionally (nothing
    # has run yet, so there is no completed building to name even if disk were already low);
    # every submission after that happens only inside the completion loop, immediately after a
    # real completion, so `last_completed_stem` is guaranteed real whenever the guard trips.
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        futs: dict = {}
        for _ in range(n_workers):
            a = next(pending_iter, None)
            if a is None:
                break
            futs[ex.submit(_run_one_ep, a)] = a[0]

        while futs:
            done, _ = wait(list(futs.keys()), return_when=FIRST_COMPLETED)
            for fut in done:
                futs.pop(fut)
                stem, status, rc, retained_bytes = fut.result()
                results.append((stem, status, rc))
                _CUMULATIVE_RETAINED_BYTES += retained_bytes
                last_completed_stem = stem
                print(f"    [{stem}] status={status} retained={retained_bytes:,}B "
                      f"cumulative_retained={_CUMULATIVE_RETAINED_BYTES:,}B")
                if status != "success":
                    print(f"    [WARN] {stem}: {status} (rc={rc})")

            if disk_guard_tripped:
                continue  # already stopped submitting; drain the rest of the in-flight work

            for _ in range(len(done)):
                a = next(pending_iter, None)
                if a is None:
                    break
                free_b = free_disk_bytes(work_base)
                if free_b < DISK_FLOOR_BYTES:
                    print(f"  [DISK GUARD] free space {free_b / 1e9:.1f} GB < 50 GB floor on "
                          f"{work_base} — stopping before submitting {a[0]}. "
                          f"Last completed building: {last_completed_stem}")
                    disk_guard_tripped = True
                    break
                futs[ex.submit(_run_one_ep, a)] = a[0]

    if disk_guard_tripped:
        sys.exit(
            f"STOP: free disk space fell below the 50 GB floor during {cell}/{mode}. "
            f"Last completed building: {last_completed_stem}. "
            f"Pass stopped cleanly and is resumable."
        )

    elapsed = time.monotonic() - t0
    n_ok = sum(1 for _, s, _ in results if s == "success")
    total_ok = n_ok + already_done
    print(f"  [{cell}/{mode}] E+ done: {n_ok}/{len(pending)} new + {already_done} prior = "
          f"{total_ok}/{len(idfs)} total success in {elapsed:.1f}s")
    return sim_out


# ── SQL parser (matches t08_harvest_results.py schema exactly) ───────────────

def _parse_sql(sql_path: Path, floor_area: float) -> dict[str, float]:
    meters: dict[str, float] = dict.fromkeys(_METER_NAMES, 0.0)
    zone_kwh: dict[str, float] = {"lights": 0.0, "equip": 0.0}

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

    lights_kwh = (meters["InteriorLights:Electricity"]
                  if meters["InteriorLights:Electricity"] > 0 else zone_kwh["lights"])
    equip_kwh = (meters["InteriorEquipment:Electricity"]
                 if meters["InteriorEquipment:Electricity"] > 0 else zone_kwh["equip"])

    heating_kwh = meters["Heating:Electricity"] + meters["Heating:NaturalGas"]
    dhw_kwh = meters["WaterSystems:NaturalGas"] + meters["WaterSystems:Electricity"]
    cooking_kwh = (meters["InteriorEquipment:NaturalGas"]
                   + meters["Cooking:InteriorEquipment:Electricity"])
    refrig_kwh = (meters["Refrigeration:Electricity"]
                  + meters["Refrigeration:InteriorEquipment:Electricity"])

    total_kwh = (
        heating_kwh + meters["Cooling:Electricity"] + lights_kwh + equip_kwh
        + meters["Fans:Electricity"] + meters["Pumps:Electricity"]
        + dhw_kwh + cooking_kwh + refrig_kwh
    )
    fa = float(floor_area)
    return {
        "heating_eui":   heating_kwh / fa,
        "cooling_eui":   meters["Cooling:Electricity"] / fa,
        "lighting_eui":  lights_kwh / fa,
        "equipment_eui": equip_kwh / fa,
        "fans_eui":      meters["Fans:Electricity"] / fa,
        "pumps_eui":     meters["Pumps:Electricity"] / fa,
        "dhw_eui":       dhw_kwh / fa,
        "cooking_eui":   cooking_kwh / fa,
        "refrig_eui":    refrig_kwh / fa,
        "total_eui":     total_kwh / fa,
    }


# ── harvest one (cell, mode) ──────────────────────────────────────────────────

def harvest_cell_mode(cell: str, mode: str, sim_out: Path,
                      manifest: pd.DataFrame, cell_info: pd.DataFrame,
                      build_date: str) -> pd.DataFrame:
    rows = []
    for _, mrow in manifest.iterrows():
        if mrow.get("generation_status") != "success":
            continue
        osm_id = str(mrow["osm_id"])
        stem = osm_id.replace("/", "_", 1)

        bld = cell_info[cell_info["osm_id"] == osm_id]
        if bld.empty:
            continue
        bld_row = bld.iloc[0]
        floor_area = float(bld_row["floor_area_m2"])
        archetype = str(bld_row.get("archetype_id", ""))
        phase_e_eui = float(bld_row.get("phaseE_total_eui", float("nan")))

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
            "cell": cell,
            "city": CITY_OF.get(cell, cell),
            "mode": mode,
            "platform": "Windows-local",
            "build_date": build_date,
            "osm_id": osm_id,
            "archetype_id": archetype,
            "floor_area_m2": floor_area,
            "status": status,
            "has_fatal": has_fatal,
            "zoning_strategy": str(mrow.get("zoning_strategy", "")),
            "num_zones": int(mrow.get("num_zones", 0)) if pd.notna(mrow.get("num_zones")) else 0,
            "phaseE_total_eui": phase_e_eui,
        }

        if status == "success" and sql_path.exists():
            try:
                row.update(_parse_sql(sql_path, floor_area))
            except Exception as exc:
                row["parse_error"] = str(exc)

        rows.append(row)
    return pd.DataFrame(rows)


# ── CP4 local report ──────────────────────────────────────────────────────────

def print_cp4_local_report(results: pd.DataFrame) -> None:
    print("\n" + "=" * 80)
    print("CP4 LOCAL REPORT -- T08 local remainder (7 cells, Windows-local platform)")
    print("=" * 80)
    print("Auto regression: STRICT <1 kWh/m2 (same platform as phaseE baseline).\n")

    succ = results[results["status"] == "success"]

    # 1. Completion
    print("### 1. Completion summary ###")
    print(f"  {'cell':18s}  {'mode':10s}  {'ok':>6}  {'fail':>6}  {'fatal':>6}  {'total':>6}")
    any_fatal = False
    for cell in LOCAL_CELLS:
        for mode in ALL_MODES:
            mdf = results[(results["cell"] == cell) & (results["mode"] == mode)]
            if mdf.empty:
                continue
            n_ok = int((mdf["status"] == "success").sum())
            n_fail = int((mdf["status"] != "success").sum())
            n_fat = int(mdf["has_fatal"].sum()) if "has_fatal" in mdf.columns else 0
            if n_fat:
                any_fatal = True
            print(f"  {cell:18s}  {mode:10s}  {n_ok:>6}  {n_fail:>6}  {n_fat:>6}  {len(mdf):>6}")
    print(f"\n  Fatal-free: {'YES' if not any_fatal else 'NO -- see rows above'}")

    # 2. Auto regression vs phaseE (STRICT)
    print("\n### 2. Auto regression vs phaseE (strict <1 kWh/m2 — Windows vs Windows) ###")
    auto_succ = succ[(succ["mode"] == "auto") & succ["total_eui"].notna() & succ["phaseE_total_eui"].notna()]
    regressions: list[str] = []
    for cell in LOCAL_CELLS:
        cell_auto = auto_succ[auto_succ["cell"] == cell].copy()
        if cell_auto.empty:
            print(f"  {cell}: no auto data")
            continue
        deltas = (cell_auto["total_eui"] - cell_auto["phaseE_total_eui"]).abs()
        n_ok = int((deltas < 1.0).sum())
        n_fail = int((deltas >= 1.0).sum())
        mean_d = float((cell_auto["total_eui"] - cell_auto["phaseE_total_eui"]).mean())
        max_d = float(deltas.max())
        tag = "PASS" if n_fail == 0 else f"FAIL ({n_fail} buildings > 1 kWh/m2)"
        print(f"  {cell:18s}  {n_ok:>4}/{len(cell_auto):<4} within 1  "
              f"mean_delta={mean_d:+.3f}  max_abs={max_d:.3f}  [{tag}]")
        if n_fail > 0:
            bad = cell_auto[deltas >= 1.0][["osm_id", "archetype_id", "total_eui", "phaseE_total_eui"]]
            for _, r in bad.iterrows():
                d = float(r["total_eui"]) - float(r["phaseE_total_eui"])
                regressions.append(f"  {cell}/{r['archetype_id']}/{r['osm_id']}: "
                                   f"auto={r['total_eui']:.1f} phaseE={r['phaseE_total_eui']:.1f} d={d:+.2f}")
    if regressions:
        print("\n  STRICT REGRESSION FAILURES:")
        for r in regressions:
            print(r)
    else:
        print("\n  All auto cells pass strict <1 kWh/m2 gate.")

    # 3. Per-mode x per-cell mean total EUI
    print("\n### 3. Per-mode x per-cell mean total EUI [kWh/m2] ###")
    if "total_eui" in succ.columns:
        modes_present = [m for m in ALL_MODES if m in succ["mode"].unique()]
        print(f"  {'cell':18s}  " + "  ".join(f"{m:>10s}" for m in modes_present))
        for cell in LOCAL_CELLS:
            vals = []
            for mode in modes_present:
                mdf = succ[(succ["cell"] == cell) & (succ["mode"] == mode)]
                v = mdf["total_eui"].mean() if len(mdf) > 0 else float("nan")
                vals.append(f"{v:10.1f}" if not (v != v) else "       n/a")
            print(f"  {cell:18s}  " + "  ".join(vals))

    # 4. Per-mode x per-cell 9-end-use split (median)
    end_uses = ["heating_eui", "cooling_eui", "lighting_eui", "equipment_eui",
                "fans_eui", "pumps_eui", "dhw_eui", "cooking_eui", "refrig_eui"]
    present = [eu for eu in end_uses if eu in succ.columns]
    if present:
        print("\n### 4. Per-mode x per-cell median 9-end-use EUI [kWh/m2] ###")
        modes_present = [m for m in ALL_MODES if m in succ["mode"].unique()]
        for cell in LOCAL_CELLS:
            cell_succ = succ[succ["cell"] == cell]
            if cell_succ.empty:
                continue
            print(f"\n  Cell: {cell}")
            print(f"  {'end_use':14s}  " + "  ".join(f"{m:>10s}" for m in modes_present))
            for eu in present:
                vals = []
                for mode in modes_present:
                    mdf = cell_succ[cell_succ["mode"] == mode]
                    v = mdf[eu].median() if len(mdf) > 0 and eu in mdf.columns else float("nan")
                    vals.append(f"{v:10.2f}" if not (v != v) else "       n/a")
                print(f"  {eu:14s}  " + "  ".join(vals))

    # 5. fast_zone fallback counts
    if "num_zones" in succ.columns and "zoning_strategy" in succ.columns:
        print("\n### 5. fast_zone fallback counts (perimeter_core -> one_zone_per_floor) ###")
        print(f"  {'cell':18s}  {'fz_total':>10}  {'fz_fallback':>12}  {'pct':>7}")
        fz = succ[succ["mode"] == "fast_zone"]
        for cell in LOCAL_CELLS:
            cfz = fz[fz["cell"] == cell]
            if cfz.empty:
                continue
            n_total = len(cfz)
            n_fb = int((cfz["num_zones"] == 1).sum())
            pct = 100.0 * n_fb / n_total if n_total else 0.0
            print(f"  {cell:18s}  {n_total:>10}  {n_fb:>12}  {pct:>6.1f}%")

    print("\n" + "=" * 80)
    print("STOP AT CP4 — report table to manager. Do NOT start T09.")
    print("=" * 80)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="T08 local remainder: 12 cells x 5 modes on Windows")
    parser.add_argument("--cells", nargs="+", default=LOCAL_CELLS,
                        choices=LOCAL_CELLS,
                        help="Cells to run (default: all 12 local cells)")
    parser.add_argument("--modes", nargs="+", default=ALL_MODES,
                        choices=ALL_MODES,
                        help="Modes to run (default: all 5)")
    parser.add_argument("--n-jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2),
                        help="Step-3 worker processes (default: cpu_count-2)")
    parser.add_argument("--n-ep-workers", type=int, default=max(4, (os.cpu_count() or 8) - 2),
                        help="EnergyPlus parallel workers (default: cpu_count-2)")
    parser.add_argument("--output-csv", type=Path, default=OUTPUT_CSV,
                        help="Output CSV path (default: t08_local_remainder_eui.csv)")
    parser.add_argument("--work-base", type=Path,
                        default=Path(tempfile.gettempdir()) / "ubem_t08_local",
                        help="Work base dir for resumable sim_out trees "
                             "(default: %%TEMP%%/ubem_t08_local)")
    args = parser.parse_args()

    cells = args.cells
    modes = args.modes
    n_jobs = args.n_jobs
    n_ep_workers = args.n_ep_workers
    build_date = time.strftime("%Y-%m-%d")

    output_csv = args.output_csv
    work_base = args.work_base
    work_base.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(f"T08 local remainder — {len(cells)} cells x {len(modes)} modes")
    print(f"  Work dir:    {work_base}")
    print(f"  Output CSV:  {output_csv}")
    print(f"  Cells:       {cells}")
    print(f"  Modes:       {modes}")
    print(f"  n_jobs:      {n_jobs}  (Step 3)")
    print(f"  n_ep_workers:{n_ep_workers}  (EnergyPlus)")
    print(f"  Build date:  {build_date}")
    print(f"  EnergyPlus:  {EP_EXE}")
    print("=" * 72)

    if not EP_EXE.exists():
        sys.exit(f"FATAL: EnergyPlus 23.1 not found at {EP_EXE}")

    print("\n[AMENDMENT CHECK] Verifying orient() gate in builder.py ...")
    _verify_orient_gate()

    # Import helpers from t08_full_sweep (Steps 2 and 3)
    sys.path.insert(0, str(REPO / "scripts" / "cluster"))
    from t08_full_sweep import run_step2, run_step3_mode  # type: ignore

    all_dfs: list[pd.DataFrame] = []

    for cell in cells:
        cfg = CELL_CONFIGS[cell]
        print(f"\n{'='*72}")
        print(f"  CELL: {cell}  (lat={cfg['lat']}, lon={cfg['lon']}, state={cfg['state']})")
        print(f"{'='*72}")

        modes_needed = [m for m in modes if not is_done(cell, m, work_base)]
        if not modes_needed:
            print(f"  All modes done for {cell} — loading existing harvest ...")
            # Load existing harvest rows for this cell from output CSV if present
            if output_csv.exists():
                existing = pd.read_csv(str(output_csv))
                cell_rows = existing[existing["cell"] == cell]
                if not cell_rows.empty:
                    all_dfs.append(cell_rows)
                    print(f"  Loaded {len(cell_rows)} rows from {output_csv}")
            continue

        # Build cell metadata from phaseE fixture
        cell_info = build_cell_info(cell)
        if cell_info.empty:
            print(f"  SKIP {cell}: no phaseE fixture found", file=sys.stderr)
            continue

        # Load raw buildings
        buildings_path = PHASED_RESULTS / cell / "01_buildings.gpkg"
        if not buildings_path.exists():
            print(f"  SKIP {cell}: 01_buildings.gpkg not found", file=sys.stderr)
            continue
        gdf_raw = gpd.read_file(str(buildings_path))
        print(f"  Loaded {len(gdf_raw)} raw buildings")

        # Step 2: semantic enrichment (once per cell)
        cell_work = work_base / cell
        cell_work.mkdir(parents=True, exist_ok=True)
        print(f"  Step 2: semantic enrichment ...")
        t2 = time.monotonic()
        gdf_57, schedule_library, epw_path = run_step2(gdf_raw, cell, cfg, work_base)
        print(f"  Step 2 done in {time.monotonic()-t2:.1f}s, {len(gdf_57)} buildings, EPW: {epw_path}")

        for mode in modes_needed:
            print(f"\n  --- Mode: {mode} ---")
            t_mode = time.monotonic()

            # Step 3: IDF generation
            manifest = run_step3_mode(gdf_57, schedule_library, cell, mode, work_base, n_jobs)
            n_ok_step3 = int((manifest["generation_status"] == "success").sum())

            if n_ok_step3 == 0:
                print(f"  [{cell}/{mode}] ZERO successful IDFs — skipping simulation.", file=sys.stderr)
                continue

            # Step 4: EnergyPlus simulation (local)
            sim_out = run_simulations(manifest, cell, mode, work_base, epw_path, n_ep_workers)

            # Step 5: Harvest
            df = harvest_cell_mode(cell, mode, sim_out, manifest, cell_info, build_date)
            n_sim_ok = int((df["status"] == "success").sum()) if not df.empty else 0
            print(f"  [{cell}/{mode}] harvested: {n_sim_ok}/{len(df)} success")

            if not df.empty:
                all_dfs.append(df)

            # Save done marker
            mark_done(cell, mode, work_base, n_sim_ok, len(df))

            elapsed_mode = time.monotonic() - t_mode
            print(f"  [{cell}/{mode}] done in {elapsed_mode/60:.1f} min")

        # Write incremental CSV after each cell (safe against crashes)
        if all_dfs:
            interim = pd.concat(all_dfs, ignore_index=True)
            output_csv.parent.mkdir(parents=True, exist_ok=True)
            interim.to_csv(str(output_csv), index=False)
            print(f"\n  [CSV] Incremental write: {len(interim)} rows -> {output_csv}")

    # Final assembly
    if not all_dfs:
        print("No results to report.", file=sys.stderr)
        sys.exit(1)

    results = pd.concat(all_dfs, ignore_index=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(str(output_csv), index=False)
    n_succ = int((results["status"] == "success").sum())
    print(f"\nFinal CSV: {output_csv}  ({n_succ}/{len(results)} success rows)")
    print(f"Total retained bytes this run (trim, cumulative): {_CUMULATIVE_RETAINED_BYTES:,}")

    # CP4 local report
    print_cp4_local_report(results)


if __name__ == "__main__":
    main()
