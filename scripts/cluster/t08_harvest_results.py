"""T08 — Harvest cluster results and produce CP4 report.

Run AFTER all 48 sbatch arrays (12 cells x 4 modes) have completed on Speed.
Fetches SQL+end+err from each (cell, mode) fleet, parses 9-end-use EUI,
assembles the cross-mode comparison, generates figures, and prints the CP4 table.

Platform-aware auto regression (AMENDMENT 2026-06-29):
  phaseE baselines may be Windows- or Linux-generated. A uniform offset <=2 kWh/m2
  is accepted as platform rounding. Only structural per-archetype deltas (tens of
  kWh/m2 concentrated in one archetype) are flagged as real regressions.

Usage:
    py -3 scripts/cluster/t08_harvest_results.py [--cells ...] [--modes ...]

Outputs:
    openubem/outputs/comparisons/t08_all_modes_eui.csv
    openubem/outputs/comparisons/t08_mode_cell_summary.csv
    openubem/outputs/comparisons/t08_*.png  (per-mode x per-cell figures)
    (progress log entry printed at the end for §8 of the PLAN)
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import numpy as np
import pandas as pd

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
_REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"
_FLEET_TAG = "t08"

ALL_MODES = ["auto", "building", "floor", "fast_zone"]
ALL_CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]
CITY_OF = {
    "nyc_centre": "NYC", "nyc_urban": "NYC", "nyc_suburban": "NYC", "nyc_rural": "NYC",
    "la_centre": "LA", "la_urban": "LA", "la_suburban": "LA", "la_rural": "LA",
    "austin_centre": "AUS", "austin_urban": "AUS", "austin_suburban": "AUS", "austin_rural": "AUS",
}

PHASED_RESULTS = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
)
OUTPUT_DIR = REPO / "openubem" / "outputs" / "comparisons"
OUTPUT_ALL_CSV = OUTPUT_DIR / "t08_all_modes_eui.csv"
OUTPUT_SUMMARY_CSV = OUTPUT_DIR / "t08_mode_cell_summary.csv"

J_TO_KWH = 1.0 / 3.6e6

# 9 end-uses parsed from RunPeriod meters (T08 trimmed IDFs: no hourly zone variables).
# InteriorLights:Electricity and InteriorEquipment:Electricity were added to HVAC_METERS
# in outputs.py (T08 change) so trimmed IDFs have them as RunPeriod meters.
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
    f"AND d.Name IN ({', '.join(repr(m) for m in _METER_NAMES)})"
)
# Fallback: zone variables (present in untrimmed IDFs / phaseE SQL)
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


def _remote_fleet_dir(cell: str, mode: str) -> str:
    return f"{_REMOTE_FLEET_BASE}/{_FLEET_TAG}_{cell}_{mode}"


# ── Fetch one (cell, mode) from cluster ──────────────────────────────────────

def fetch_mode_cell(cell: str, mode: str, fleet_lst: list[str], work_base: Path) -> Path:
    """Download sql+end+err for one (cell, mode) fleet.

    The file list is expanded REMOTELY by the login shell glob, so hundreds of
    paths never reach the local Windows command line (CreateProcess caps argv at
    ~32 KB → WinError 206 on the large cells).
    """
    remote_dir = _remote_fleet_dir(cell, mode)
    sim_out = work_base / f"{cell}_{mode}"
    sim_out.mkdir(parents=True, exist_ok=True)

    n = len(fleet_lst)
    print(f"  [{cell}/{mode}] Fetching {n} buildings from {remote_dir}/out ...")
    remote_cmd = (
        f"cd {remote_dir}/out && "
        f"tar czf - --ignore-failed-read */eplusout.sql */eplusout.err */eplusout.end"
    )
    tgz = work_base / f"fetch_{cell}_{mode}.tgz"

    with open(tgz, "wb") as fh:
        proc = subprocess.Popen(
            ["ssh", REMOTE_HOST, f"bash -lc '{remote_cmd}'"],
            stdout=fh, stderr=subprocess.PIPE, text=True,
        )
        _, err = proc.communicate(timeout=3600)

    if tgz.stat().st_size == 0:
        tgz.unlink(missing_ok=True)
        raise RuntimeError(
            f"empty fetch for {cell}/{mode} (ssh rc={proc.returncode}); "
            f"{remote_dir}/out likely missing. remote stderr: {err.strip()[:400]}"
        )

    with tarfile.open(tgz, "r:gz") as tf:
        tf.extractall(str(sim_out))
    tgz.unlink(missing_ok=True)

    n_ends = len(list(sim_out.rglob("eplusout.end")))
    print(f"  [{cell}/{mode}] {n_ends}/{n} .end files extracted")
    if n_ends == 0:
        print(f"  [{cell}/{mode}] WARNING: 0 .end extracted; remote stderr: {err.strip()[:400]}",
              file=sys.stderr)
    return sim_out


# ── Parse one building's SQL → 9-end-use EUI ─────────────────────────────────

def _parse_sql(sql_path: Path, floor_area: float) -> dict[str, float]:
    """Parse RunPeriod meters from SQL. Returns per-m2 EUI for 9 end-uses."""
    meters: dict[str, float] = dict.fromkeys(_METER_NAMES, 0.0)
    zone_kwh: dict[str, float] = {"lights": 0.0, "equip": 0.0}

    with sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True) as conn:
        for name, val_j in conn.execute(_METER_SQL).fetchall():
            if name in meters and val_j is not None:
                meters[name] += float(val_j) * J_TO_KWH
        # Fallback: zone variables (untrimmed IDFs)
        for name, total_j in conn.execute(_ZONE_SQL).fetchall():
            if total_j is not None:
                if "Lights" in name:
                    zone_kwh["lights"] = float(total_j) * J_TO_KWH
                elif "Electric Equipment" in name:
                    zone_kwh["equip"] = float(total_j) * J_TO_KWH

    # Prefer RunPeriod meter over zone variable (trimmed IDFs have the meter)
    lights_kwh = meters["InteriorLights:Electricity"] if meters["InteriorLights:Electricity"] > 0 else zone_kwh["lights"]
    equip_kwh = meters["InteriorEquipment:Electricity"] if meters["InteriorEquipment:Electricity"] > 0 else zone_kwh["equip"]

    heating_kwh = meters["Heating:Electricity"] + meters["Heating:NaturalGas"]
    dhw_kwh = meters["WaterSystems:NaturalGas"] + meters["WaterSystems:Electricity"]
    cooking_kwh = meters["InteriorEquipment:NaturalGas"] + meters["Cooking:InteriorEquipment:Electricity"]
    refrig_kwh = meters["Refrigeration:Electricity"] + meters["Refrigeration:InteriorEquipment:Electricity"]

    total_kwh = (
        heating_kwh
        + meters["Cooling:Electricity"]
        + lights_kwh
        + equip_kwh
        + meters["Fans:Electricity"]
        + meters["Pumps:Electricity"]
        + dhw_kwh
        + cooking_kwh
        + refrig_kwh
    )
    fa = float(floor_area)
    if fa <= 0:
        raise ValueError(f"non-positive floor_area_m2={fa} for {sql_path.parent.name}")
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


# ── Parse all buildings for one (cell, mode) ─────────────────────────────────

def parse_cell_mode(cell: str, mode: str, sim_out: Path, fleet_lst: list[str],
                    cell_info: pd.DataFrame, manifest: pd.DataFrame | None) -> pd.DataFrame:
    rows = []
    for stem in fleet_lst:
        osm_id = stem.replace("_", "/", 1)

        bld = cell_info[cell_info["osm_id"] == osm_id]
        if bld.empty:
            bld = cell_info[cell_info["osm_id"].str.replace("/", "_", 1) == stem]
        if bld.empty:
            continue

        bld_row = bld.iloc[0]
        floor_area = float(bld_row["floor_area_m2"])
        archetype = str(bld_row.get("archetype_id", ""))

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
            has_fatal = "** Fatal **" in err

        row: dict = {
            "cell": cell, "city": CITY_OF.get(cell, cell),
            "mode": mode, "osm_id": osm_id, "archetype_id": archetype,
            "floor_area_m2": floor_area, "status": status, "has_fatal": has_fatal,
        }

        if manifest is not None:
            mrow = manifest[manifest["osm_id"].astype(str) == osm_id]
            if mrow.empty:
                mrow = manifest[manifest["osm_id"].astype(str).str.replace("/", "_", 1) == stem]
            if not mrow.empty:
                row["zoning_strategy"] = str(mrow.iloc[0].get("zoning_strategy", ""))
                row["num_zones"] = int(mrow.iloc[0].get("num_zones", 0))

        if status == "success" and sql_path.exists():
            try:
                row.update(_parse_sql(sql_path, floor_area))
            except Exception as exc:
                row["parse_error"] = str(exc)

        rows.append(row)
    return pd.DataFrame(rows)


# ── Build cell_info (osm_id, floor_area, archetype) from phaseE fixture ──────

def build_cell_info(cell: str) -> pd.DataFrame:
    """Load building metadata (osm_id, floor_area_m2, archetype_id) from phaseE fixture."""
    from openubem.geometry.footprint import derive_num_floors

    fixture_dir = PHASED_RESULTS / cell
    results_path = fixture_dir / "05_results.gpkg"
    buildings_path = fixture_dir / "01_buildings.gpkg"

    if results_path.exists():
        gdf = gpd.read_file(str(results_path))
        rows = []
        for _, r in gdf.iterrows():
            # Mirror t08_local_remainder.build_cell_info: conditioned area =
            # footprint x levels (the same area phaseE_total_eui was normalised by).
            fa = float(r.get("footprint_area_m2", 0)) * max(1, int(r.get("levels", 1) or 1))
            rows.append({
                "osm_id": str(r["osm_id"]),
                "archetype_id": str(r.get("archetype_id", "")),
                "floor_area_m2": fa,
                "phaseE_total_eui": float(r.get("total_eui_kwh_m2", float("nan"))),
            })
        return pd.DataFrame(rows)
    elif buildings_path.exists():
        # Fallback: derive floor area from 01_buildings.gpkg
        gdf = gpd.read_file(str(buildings_path))
        rows = []
        for _, r in gdf.iterrows():
            fa = float(r.get("footprint_area_m2", 0)) * max(1, derive_num_floors(r))
            rows.append({
                "osm_id": str(r["osm_id"]),
                "archetype_id": str(r.get("archetype_id", "")),
                "floor_area_m2": fa,
                "phaseE_total_eui": float("nan"),
            })
        return pd.DataFrame(rows)
    else:
        return pd.DataFrame(columns=["osm_id", "archetype_id", "floor_area_m2", "phaseE_total_eui"])


# ── CP4 report ────────────────────────────────────────────────────────────────

def print_cp4_report(results: pd.DataFrame) -> None:
    print("\n" + "=" * 80)
    print("CP4 REPORT -- T08 Full 4-mode x 12-cell sweep")
    print("=" * 80)
    print("\nAMENDMENT: auto regression check is PLATFORM-AWARE.")
    print("  phaseE baseline may be Windows-generated; this sweep is Speed/Linux.")
    print("  Uniform offset <=2 kWh/m2 is accepted as platform rounding.")
    print("  Only structural per-archetype deltas (tens of kWh/m2) are flagged.")

    succ = results[results["status"] == "success"]

    # 1. Completion table
    print("\n### 1. Completion summary ###")
    print(f"  {'cell':18s}  {'mode':10s}  {'success':>8}  {'failed':>7}  {'fatal':>6}  {'total':>6}")
    any_fatal = False
    for cell in ALL_CELLS:
        for mode in ALL_MODES:
            mdf = results[(results["cell"] == cell) & (results["mode"] == mode)]
            if mdf.empty:
                continue
            n_ok = int((mdf["status"] == "success").sum())
            n_fail = int((mdf["status"] != "success").sum())
            n_fat = int(mdf["has_fatal"].sum()) if "has_fatal" in mdf.columns else 0
            print(f"  {cell:18s}  {mode:10s}  {n_ok:>8}  {n_fail:>7}  {n_fat:>6}  {len(mdf):>6}")
            if n_fat > 0:
                any_fatal = True
    print(f"\n  Fatal-free: {'YES' if not any_fatal else 'NO -- see rows above'}")

    # 2. Auto regression vs phaseE
    print("\n### 2. Auto regression vs phaseE baseline (platform-aware) ###")
    auto_succ = succ[succ["mode"] == "auto"]
    if "phaseE_total_eui" in auto_succ.columns:
        structural_regressions: list[str] = []
        platform_offsets: list[float] = []
        for cell in ALL_CELLS:
            cell_auto = auto_succ[auto_succ["cell"] == cell].copy()
            cell_auto = cell_auto.dropna(subset=["total_eui", "phaseE_total_eui"])
            if cell_auto.empty:
                print(f"  {cell}: no auto data")
                continue
            deltas = cell_auto["total_eui"] - cell_auto["phaseE_total_eui"]
            mean_d = float(deltas.mean())
            max_abs_d = float(deltas.abs().max())
            platform_offsets.append(mean_d)
            # Check per-archetype for structural divergence
            arch_deltas = cell_auto.groupby("archetype_id")["total_eui"].mean() - \
                          cell_auto.groupby("archetype_id")["phaseE_total_eui"].mean()
            structural = arch_deltas[arch_deltas.abs() > 10]
            if len(structural) > 0:
                for arch, d in structural.items():
                    structural_regressions.append(f"{cell}/{arch}: {d:+.1f} kWh/m2")
            platform_tag = "PLATFORM_OFFSET" if abs(mean_d) <= 2 else ("STRUCT?" if len(structural) == 0 else "STRUCT")
            print(f"  {cell:18s}  mean_delta={mean_d:+5.2f}  max_abs={max_abs_d:5.2f}  [{platform_tag}]")
        print()
        if structural_regressions:
            print("  STRUCTURAL regressions (>10 kWh/m2 per-archetype mean):")
            for s in structural_regressions:
                print(f"    {s}")
        else:
            print("  No structural per-archetype regressions detected.")
        if platform_offsets:
            overall_mean = float(np.mean(platform_offsets))
            print(f"  Overall mean auto delta vs phaseE: {overall_mean:+.2f} kWh/m2")
            if abs(overall_mean) <= 2:
                print("  => WITHIN platform-offset tolerance (<= 2 kWh/m2). Gate PASSED.")
            else:
                print("  => OUTSIDE tolerance. Investigate archetype-level breakdown.")

    # 3. Per-mode x per-cell mean/median EUI
    print("\n### 3. Per-mode x per-cell mean EUI [kWh/m2] ###")
    if "total_eui" in succ.columns:
        pivot = succ.groupby(["cell", "mode"])["total_eui"].mean().unstack("mode")
        print(f"  {'cell':18s}  " + "  ".join(f"{m:>10s}" for m in ALL_MODES if m in pivot.columns))
        for cell in ALL_CELLS:
            if cell not in pivot.index:
                continue
            vals = [f"{pivot.loc[cell, m]:>10.1f}" if m in pivot.columns and not pd.isna(pivot.loc[cell, m]) else "       n/a"
                    for m in ALL_MODES if m in pivot.columns]
            print(f"  {cell:18s}  " + "  ".join(vals))

    # 4. Per-mode x per-city 9-end-use split (median)
    end_uses = ["heating_eui", "cooling_eui", "lighting_eui", "equipment_eui",
                "fans_eui", "pumps_eui", "dhw_eui", "cooking_eui", "refrig_eui"]
    present = [eu for eu in end_uses if eu in succ.columns]
    if present:
        print("\n### 4. Per-mode x per-city median 9-end-use EUI [kWh/m2] ###")
        for city in ["NYC", "LA", "AUS"]:
            city_succ = succ[succ["city"] == city]
            if city_succ.empty:
                continue
            print(f"\n  City: {city}")
            print(f"  {'end_use':14s}  " + "  ".join(f"{m:>10s}" for m in ALL_MODES))
            for eu in present:
                row_vals = []
                for mode in ALL_MODES:
                    mdf = city_succ[city_succ["mode"] == mode]
                    val = mdf[eu].median() if len(mdf) > 0 else float("nan")
                    row_vals.append(f"{val:10.2f}" if not np.isnan(val) else "       n/a")
                print(f"  {eu:14s}  " + "  ".join(row_vals))

    # 5. Fallback counts (fast_zone)
    if "num_zones" in succ.columns and "zoning_strategy" in succ.columns:
        print("\n### 5. fast_zone fallback counts per cell ###")
        print(f"  {'cell':18s}  {'fz_total':>10}  {'fz_fallback':>12}  {'pct':>7}")
        fz = succ[(succ["mode"] == "fast_zone")]
        for cell in ALL_CELLS:
            cfz = fz[fz["cell"] == cell]
            if cfz.empty:
                continue
            n_total = len(cfz)
            n_fb = int((cfz["num_zones"] == 1).sum())
            pct = 100.0 * n_fb / n_total if n_total > 0 else 0.0
            print(f"  {cell:18s}  {n_total:>10}  {n_fb:>12}  {pct:>6.1f}%")

    print("\n" + "=" * 80)
    print("STOP AT CP4. Report these tables to the manager before any interpretation.")
    print("Do NOT start T09 until manager confirms deltas read as §9 physics (not bugs).")
    print("=" * 80)


# ── Comparison figures ────────────────────────────────────────────────────────

def make_figures(results: pd.DataFrame, run_date: str) -> None:
    """Generate per-mode x per-cell EUI comparison figures."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("  [figures] matplotlib not available; skipping figure generation.")
        return

    succ = results[results["status"] == "success"]
    if "total_eui" not in succ.columns or succ.empty:
        print("  [figures] No successful results to plot.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mode_colors = {"auto": "#1f77b4", "building": "#ff7f0e", "floor": "#2ca02c", "fast_zone": "#d62728"}
    modes_present = [m for m in ALL_MODES if m in succ["mode"].unique()]

    # Figure 1: Per-mode x per-cell median EUI (grouped bar)
    fig, ax = plt.subplots(figsize=(18, 6))
    cells_present = [c for c in ALL_CELLS if c in succ["cell"].unique()]
    x = np.arange(len(cells_present))
    bar_w = 0.18
    for i, mode in enumerate(modes_present):
        mdf = succ[succ["mode"] == mode]
        medians = [mdf[mdf["cell"] == c]["total_eui"].median() if c in mdf["cell"].values else float("nan")
                   for c in cells_present]
        ax.bar(x + i * bar_w, medians, bar_w, label=mode, color=mode_colors.get(mode))
    ax.set_xticks(x + bar_w * (len(modes_present) - 1) / 2)
    ax.set_xticklabels(cells_present, rotation=45, ha="right")
    ax.set_ylabel("Median total EUI [kWh/m2]")
    ax.set_title(f"T08 Resolution-mode sweep — per-cell median EUI\nProvenance: {run_date}, Speed/Linux, EnergyPlus 23.1, trim_outputs=True")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out1 = OUTPUT_DIR / "t08_mode_cell_median_eui.png"
    fig.savefig(str(out1), dpi=120)
    plt.close(fig)
    print(f"  [figures] Saved: {out1}")

    # Figure 2: Per-city per-mode EUI boxplots (3x4 grid: city rows x mode cols)
    cities = ["NYC", "LA", "AUS"]
    fig, axes = plt.subplots(len(cities), len(modes_present), figsize=(5 * len(modes_present), 4 * len(cities)),
                              sharey=False, squeeze=False)
    for row_i, city in enumerate(cities):
        city_data = succ[succ["city"] == city]
        for col_i, mode in enumerate(modes_present):
            ax = axes[row_i][col_i]
            mdf = city_data[city_data["mode"] == mode]
            if mdf.empty:
                ax.text(0.5, 0.5, "no data", ha="center", va="center", transform=ax.transAxes)
                continue
            by_cell = [mdf[mdf["cell"] == c]["total_eui"].dropna().values
                       for c in ALL_CELLS if c in mdf["cell"].unique() and CITY_OF.get(c) == city]
            cell_labels = [c.replace(city.lower() + "_", "") for c in ALL_CELLS
                           if c in mdf["cell"].unique() and CITY_OF.get(c) == city]
            ax.boxplot(by_cell, labels=cell_labels, showfliers=False)
            ax.set_title(f"{city} — {mode}")
            ax.set_ylabel("EUI [kWh/m2]")
            ax.grid(axis="y", alpha=0.3)
    fig.suptitle(f"T08 Resolution-mode EUI distributions by city and mode\nProvenance: {run_date}, Speed/Linux", fontsize=12)
    fig.tight_layout()
    out2 = OUTPUT_DIR / "t08_mode_city_eui_boxplots.png"
    fig.savefig(str(out2), dpi=100)
    plt.close(fig)
    print(f"  [figures] Saved: {out2}")

    # Figure 3: Per-city stacked 9-end-use median bar (one bar per mode)
    end_uses = ["heating_eui", "cooling_eui", "lighting_eui", "equipment_eui",
                "fans_eui", "pumps_eui", "dhw_eui", "cooking_eui", "refrig_eui"]
    eu_colors = ["#d62728", "#1f77b4", "#ffff00", "#ff7f0e", "#9467bd",
                 "#8c564b", "#17becf", "#e377c2", "#7f7f7f"]
    eu_labels = ["Heating", "Cooling", "Lighting", "Equipment", "Fans",
                 "Pumps", "DHW", "Cooking", "Refrigeration"]
    eu_present = [eu for eu in end_uses if eu in succ.columns]
    if eu_present:
        fig, axes = plt.subplots(1, len(cities), figsize=(6 * len(cities), 6), sharey=False)
        for ci, city in enumerate(cities):
            ax = axes[ci] if len(cities) > 1 else axes
            city_data = succ[succ["city"] == city]
            x = np.arange(len(modes_present))
            bottoms = np.zeros(len(modes_present))
            for ei, eu in enumerate(eu_present):
                vals = []
                for mode in modes_present:
                    mdf = city_data[city_data["mode"] == mode]
                    vals.append(mdf[eu].median() if len(mdf) > 0 and eu in mdf.columns else 0.0)
                vals = np.array([v if not np.isnan(v) else 0.0 for v in vals])
                ax.bar(x, vals, bottom=bottoms, label=eu_labels[eu_present.index(eu)],
                       color=eu_colors[eu_present.index(eu)])
                bottoms += vals
            ax.set_xticks(x)
            ax.set_xticklabels(modes_present, rotation=30, ha="right")
            ax.set_ylabel("Median EUI [kWh/m2]")
            ax.set_title(f"{city} — 9-end-use breakdown by mode")
            if ci == 0:
                ax.legend(loc="upper left", fontsize=8)
        fig.suptitle(f"T08 Resolution-mode sweep — 9-end-use median EUI by city\nProvenance: {run_date}, Speed/Linux, EnergyPlus 23.1", fontsize=11)
        fig.tight_layout()
        out3 = OUTPUT_DIR / "t08_enduse_by_mode_city.png"
        fig.savefig(str(out3), dpi=100)
        plt.close(fig)
        print(f"  [figures] Saved: {out3}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="T08 harvest: fetch + parse + CP4 report")
    parser.add_argument("--cells", nargs="+", default=ALL_CELLS, choices=ALL_CELLS)
    parser.add_argument("--modes", nargs="+", default=ALL_MODES, choices=ALL_MODES)
    parser.add_argument("--local-work-dir", type=str, default=None,
                        help="Use existing local sim_out dirs (skip SSH fetch). "
                             "Dir must contain <cell>_<mode>/ subdirs.")
    args = parser.parse_args()

    work_base = Path(tempfile.gettempdir()) / "ubem_t08_harvest"
    work_base.mkdir(parents=True, exist_ok=True)
    print(f"T08 harvest — work dir: {work_base}")
    print(f"  Cells: {args.cells}")
    print(f"  Modes: {args.modes}")

    local_work = Path(args.local_work_dir) if args.local_work_dir else work_base

    # Load job IDs (informational)
    sweep_work = Path(tempfile.gettempdir()) / "ubem_t08_sweep"
    job_id_file = sweep_work / "t08_job_ids.json"
    if job_id_file.exists():
        info = json.loads(job_id_file.read_text())
        print(f"  Submitted job IDs: {info.get('job_ids', {})}")

    import time as _time
    run_date = _time.strftime("%Y-%m-%d")

    all_dfs: list[pd.DataFrame] = []

    for cell in args.cells:
        print(f"\n=== Cell: {cell} ===")
        cell_info = build_cell_info(cell)
        if cell_info.empty:
            print(f"  WARNING: no building info for {cell}; skipping.")
            continue
        print(f"  Building info: {len(cell_info)} buildings")

        for mode in args.modes:
            print(f"\n  --- Mode: {mode} ---")

            # Get fleet.lst from remote (or derive from local manifest)
            sweep_manifest_path = sweep_work / cell / f"step3_{mode}" / "03_manifest.parquet"
            sim_out = local_work / f"{cell}_{mode}"

            if sweep_manifest_path.exists():
                mf = pd.read_parquet(str(sweep_manifest_path))
                succ_mf = mf[mf["generation_status"] == "success"]
                fleet_lst = [Path(str(r["idf_path"])).stem for _, r in succ_mf.iterrows()]
                print(f"  Fleet from local manifest: {len(fleet_lst)} buildings")
            else:
                # Fallback: read fleet.lst from cluster
                remote_dir = _remote_fleet_dir(cell, mode)
                raw = _ssh(f"cat {remote_dir}/fleet.lst", timeout=30)
                fleet_lst = [s.strip() for s in raw.splitlines() if s.strip()]
                print(f"  Fleet from remote: {len(fleet_lst)} buildings")

            if not fleet_lst:
                print(f"  [{cell}/{mode}] Empty fleet — skipping.")
                continue

            # Fetch from cluster (or use local sim_out)
            if not sim_out.exists() or not list(sim_out.rglob("eplusout.end")):
                try:
                    sim_out = fetch_mode_cell(cell, mode, fleet_lst, work_base)
                except Exception as exc:
                    print(f"  [{cell}/{mode}] fetch failed: {exc}", file=sys.stderr)
                    continue
            else:
                n_end = len(list(sim_out.rglob("eplusout.end")))
                print(f"  [{cell}/{mode}] using existing local results: {n_end} .end files")

            # Load manifest if available
            manifest = pd.read_parquet(str(sweep_manifest_path)) if sweep_manifest_path.exists() else None

            # Merge cell_info with phaseE baseline
            ci = cell_info.copy()

            df = parse_cell_mode(cell, mode, sim_out, fleet_lst, ci, manifest)
            # Attach phaseE baseline total
            if "phaseE_total_eui" in ci.columns:
                df = df.merge(ci[["osm_id", "phaseE_total_eui"]], on="osm_id", how="left")

            n_ok = int((df["status"] == "success").sum())
            n_fat = int(df["has_fatal"].sum()) if "has_fatal" in df.columns else 0
            print(f"  [{cell}/{mode}] parsed: {n_ok}/{len(df)} success, {n_fat} fatals")
            all_dfs.append(df)

    if not all_dfs:
        sys.exit("No mode/cell results parsed — nothing to report.")

    results = pd.concat(all_dfs, ignore_index=True)

    # Write CSVs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(str(OUTPUT_ALL_CSV), index=False)
    print(f"\nAll-buildings CSV: {OUTPUT_ALL_CSV}")

    # Summary CSV (per-cell x per-mode mean/median)
    succ = results[results["status"] == "success"]
    if "total_eui" in succ.columns:
        end_uses = [c for c in succ.columns if c.endswith("_eui")]
        summary = succ.groupby(["cell", "city", "mode"])[end_uses].agg(["mean", "median"]).reset_index()
        summary.to_csv(str(OUTPUT_SUMMARY_CSV), index=False)
        print(f"Summary CSV: {OUTPUT_SUMMARY_CSV}")

    # Figures
    print("\nGenerating comparison figures ...")
    make_figures(results, run_date)

    # CP4 report
    print_cp4_report(results)

    print(f"\nRun date: {run_date}")
    print("Provenance: T08 full sweep, Speed/Linux, EnergyPlus 23.1, trim_outputs=True")
    print(f"Output CSV: {OUTPUT_ALL_CSV}")
    print(f"Summary CSV: {OUTPUT_SUMMARY_CSV}")
    print(f"Figures: {OUTPUT_DIR}/t08_*.png")


if __name__ == "__main__":
    main()
