"""T19 — Harvest layout_assign cluster results, post-structural-fixes.

Run AFTER all 12 sbatch arrays (12 cells x layout_assign) submitted by
t19_layout_assign_full_sweep.py have completed on Speed. Fetches SQL+end+err
from each (cell, layout_assign) fleet, parses the 9-end-use EUI, and writes the
fleet-median table -- same meter-based methodology as T17's/T18's harvest,
applied to the T19 (post-structural-fixes) fleet so a real 3-way T17->T18->T19
comparison is possible.

Diffs vs. t18_harvest_layout_assign.py (all documented here, per structural-fixes
plan §5 T11 / hard rule 4 -- never overwrite T17's or T18's original harvest
artifacts):
  1. _FLEET_TAG "t18" -> "t19" (reads from the T19 remote fleet dirs that
     t19_layout_assign_full_sweep.py shipped to -- distinct from T17's/T18's, so
     this harvest cannot accidentally read T17's/T18's already-fetched output).
  2. OUTPUT_ALL_CSV / OUTPUT_SUMMARY_CSV -> t19_layout_assign_eui.csv /
     t19_layout_assign_cell_summary.csv (NEW filenames; T17's/T18's own
     t17_layout_assign_eui.csv/t18_layout_assign_eui.csv and their
     cell_summary siblings are never written to by this script).
  3. work_base tmp dir "ubem_t18_harvest" -> "ubem_t19_harvest"; sweep_work
     (for reading the local manifest, if present) "ubem_t18_sweep" ->
     "ubem_t19_sweep"; job_id_file "t18_job_ids.json" -> "t19_job_ids.json".
  4. _parse_sql/_METER_NAMES/_METER_SQL/_ZONE_SQL, parse_cell, build_cell_info:
     byte-for-byte identical to T18 -- same meter-based, mode-agnostic parser,
     proven immune to the E-LA-05 zone-naming mismatch (see T17's own docstring
     for the full rationale, unchanged and still applicable here). The
     n_warmup_convergence per-building counting Employee F added for T18
     (E-LA-14 fleet-prevalence tracking) is also carried forward unchanged --
     still directly relevant here since this plan's own T10 (E-LA-19) found
     that thermal_mass=True can shift which zones tip over 25-day warmup
     convergence, so fleet-scale prevalence should be re-measured, not assumed
     unchanged from T18's 1.29%.

METHODOLOGY NOTE (carried forward verbatim from T17's/T18's own docstring, still
applicable): this harvest uses the same independent, mode-agnostic
SQL-meter-summation parser (_parse_sql / parse_cell) that reads RunPeriod
Output:Meter values directly and never touches _check_zone_integrity()/ZONE_RX.
Since write_outputs() (openubem/idf/outputs.py) emits the identical HVAC_METERS
meter set for every resolution_mode including layout_assign, this method works
identically and correctly for layout_assign fleets, WITHOUT depending on
zone-name matching at all.

Usage:
    py -3 scripts/cluster/t19_harvest_layout_assign.py [--cells ...]

Outputs:
    openubem/outputs/comparisons/t19_layout_assign_eui.csv
    openubem/outputs/comparisons/t19_layout_assign_cell_summary.csv
"""
from __future__ import annotations

import argparse
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
import numpy as np
import pandas as pd

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
_REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"
_FLEET_TAG = "t19"
_MODE = "layout_assign"

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
OUTPUT_ALL_CSV = OUTPUT_DIR / "t19_layout_assign_eui.csv"
OUTPUT_SUMMARY_CSV = OUTPUT_DIR / "t19_layout_assign_cell_summary.csv"

J_TO_KWH = 1.0 / 3.6e6

# Identical meter set to t18_harvest_layout_assign.py -- write_outputs() (openubem/idf/
# outputs.py) is mode-agnostic and emits these RunPeriod meters for every mode.
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


def _remote_fleet_dir(cell: str) -> str:
    return f"{_REMOTE_FLEET_BASE}/{_FLEET_TAG}_{cell}_{_MODE}"


def fetch_cell(cell: str, fleet_lst: list[str], work_base: Path) -> Path:
    remote_dir = _remote_fleet_dir(cell)
    sim_out = work_base / f"{cell}_{_MODE}"
    sim_out.mkdir(parents=True, exist_ok=True)

    n = len(fleet_lst)
    print(f"  [{cell}] Fetching {n} buildings from {remote_dir}/out ...")
    remote_cmd = (
        f"cd {remote_dir}/out && "
        f"tar czf - --ignore-failed-read */eplusout.sql */eplusout.err */eplusout.end"
    )
    tgz = work_base / f"fetch_{cell}.tgz"

    with open(tgz, "wb") as fh:
        proc = subprocess.Popen(
            ["ssh", REMOTE_HOST, f"bash -lc '{remote_cmd}'"],
            stdout=fh, stderr=subprocess.PIPE, text=True,
        )
        _, err = proc.communicate(timeout=3600)

    if tgz.stat().st_size == 0:
        tgz.unlink(missing_ok=True)
        raise RuntimeError(
            f"empty fetch for {cell} (ssh rc={proc.returncode}); "
            f"{remote_dir}/out likely missing. remote stderr: {err.strip()[:400]}"
        )

    with tarfile.open(tgz, "r:gz") as tf:
        tf.extractall(str(sim_out))
    tgz.unlink(missing_ok=True)

    n_ends = len(list(sim_out.rglob("eplusout.end")))
    print(f"  [{cell}] {n_ends}/{n} .end files extracted")
    if n_ends == 0:
        print(f"  [{cell}] WARNING: 0 .end extracted; remote stderr: {err.strip()[:400]}",
              file=sys.stderr)
    return sim_out


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


def parse_cell(cell: str, sim_out: Path, fleet_lst: list[str],
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
        n_severe = 0
        n_warmup_convergence = 0
        if end_path.exists():
            txt = end_path.read_text(errors="replace")
            status = "success" if "EnergyPlus Completed Successfully" in txt else "failed"
        if (bdir / "eplusout.err").exists():
            err = (bdir / "eplusout.err").read_text(errors="replace")
            has_fatal = re.search(r"\*\*\s+Fatal\s+\*\*", err) is not None
            n_severe = err.count("** Severe")
            # E-LA-14 prevalence flag (carried forward from T18's harvest, plan
            # §5 T11 / structural-fixes plan's E-LA-19): count
            # CheckWarmupConvergence Severe signatures in the fetched .err.
            n_warmup_convergence = err.count("CheckWarmupConvergence")

        row: dict = {
            "cell": cell, "city": CITY_OF.get(cell, cell),
            "mode": _MODE, "osm_id": osm_id, "archetype_id": archetype,
            "floor_area_m2": floor_area, "status": status, "has_fatal": has_fatal,
            "n_severe": n_severe, "n_warmup_convergence": n_warmup_convergence,
        }

        if manifest is not None:
            mrow = manifest[manifest["osm_id"].astype(str) == osm_id]
            if mrow.empty:
                mrow = manifest[manifest["osm_id"].astype(str).str.replace("/", "_", 1) == stem]
            if not mrow.empty:
                row["zoning_strategy"] = str(mrow.iloc[0].get("zoning_strategy", ""))
                row["num_zones"] = int(mrow.iloc[0].get("num_zones", 0))
                row["data_quality_flag"] = str(mrow.iloc[0].get("data_quality_flag", ""))

        if status == "success" and sql_path.exists():
            try:
                row.update(_parse_sql(sql_path, floor_area))
            except Exception as exc:
                row["parse_error"] = str(exc)

        rows.append(row)
    return pd.DataFrame(rows)


def build_cell_info(cell: str) -> pd.DataFrame:
    from openubem.geometry.footprint import derive_num_floors

    fixture_dir = PHASED_RESULTS / cell
    results_path = fixture_dir / "05_results.gpkg"
    buildings_path = fixture_dir / "01_buildings.gpkg"

    if results_path.exists():
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
    elif buildings_path.exists():
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


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="T19 harvest: fetch + parse layout_assign (post-structural-fixes)")
    parser.add_argument("--cells", nargs="+", default=ALL_CELLS, choices=ALL_CELLS)
    parser.add_argument("--local-work-dir", type=str, default=None,
                        help="Use existing local sim_out dirs (skip SSH fetch). "
                             "Dir must contain <cell>_layout_assign/ subdirs.")
    args = parser.parse_args()

    work_base = Path(tempfile.gettempdir()) / "ubem_t19_harvest"
    work_base.mkdir(parents=True, exist_ok=True)
    print(f"T19 harvest — work dir: {work_base}")
    print(f"  Cells: {args.cells}")

    local_work = Path(args.local_work_dir) if args.local_work_dir else work_base

    sweep_work = Path(tempfile.gettempdir()) / "ubem_t19_sweep"
    job_id_file = sweep_work / "t19_job_ids.json"
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

        sweep_manifest_path = sweep_work / cell / f"step3_{_MODE}" / "03_manifest.parquet"
        sim_out = local_work / f"{cell}_{_MODE}"

        if sweep_manifest_path.exists():
            mf = pd.read_parquet(str(sweep_manifest_path))
            succ_mf = mf[mf["generation_status"] == "success"]
            fleet_lst = [Path(str(r["idf_path"])).stem for _, r in succ_mf.iterrows()]
            print(f"  Fleet from local manifest: {len(fleet_lst)} buildings")
        else:
            remote_dir = _remote_fleet_dir(cell)
            raw = _ssh(f"cat {remote_dir}/fleet.lst", timeout=30)
            fleet_lst = [s.strip() for s in raw.splitlines() if s.strip()]
            print(f"  Fleet from remote: {len(fleet_lst)} buildings")

        if not fleet_lst:
            print(f"  [{cell}] Empty fleet — skipping.")
            continue

        if not sim_out.exists() or not list(sim_out.rglob("eplusout.end")):
            try:
                sim_out = fetch_cell(cell, fleet_lst, work_base)
            except Exception as exc:
                print(f"  [{cell}] fetch failed: {exc}", file=sys.stderr)
                continue
        else:
            n_end = len(list(sim_out.rglob("eplusout.end")))
            print(f"  [{cell}] using existing local results: {n_end} .end files")

        manifest = pd.read_parquet(str(sweep_manifest_path)) if sweep_manifest_path.exists() else None

        df = parse_cell(cell, sim_out, fleet_lst, cell_info, manifest)
        if "phaseE_total_eui" in cell_info.columns:
            df = df.merge(cell_info[["osm_id", "phaseE_total_eui"]], on="osm_id", how="left")

        n_ok = int((df["status"] == "success").sum())
        n_fat = int(df["has_fatal"].sum()) if "has_fatal" in df.columns else 0
        print(f"  [{cell}] parsed: {n_ok}/{len(df)} success, {n_fat} fatals")
        all_dfs.append(df)

    if not all_dfs:
        sys.exit("No cell results parsed — nothing to report.")

    results = pd.concat(all_dfs, ignore_index=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(str(OUTPUT_ALL_CSV), index=False)
    print(f"\nAll-buildings CSV: {OUTPUT_ALL_CSV}")

    succ = results[results["status"] == "success"]
    if "total_eui" in succ.columns:
        end_uses = [c for c in succ.columns if c.endswith("_eui")]
        summary = succ.groupby(["cell", "city", "archetype_id"])[end_uses].agg(["mean", "median", "count"]).reset_index()
        summary.to_csv(str(OUTPUT_SUMMARY_CSV), index=False)
        print(f"Summary CSV: {OUTPUT_SUMMARY_CSV}")

    # Row-count cross-check vs the other 4 modes' known per-cell counts
    print("\n### Row-count cross-check (vs auto/building/floor/fast_zone per-cell counts) ###")
    expected = {
        "nyc_centre": 738, "nyc_urban": 1779, "nyc_suburban": 1589, "nyc_rural": 198,
        "la_centre": 226, "la_urban": 618, "la_suburban": 1343, "la_rural": 149,
        "austin_centre": 413, "austin_urban": 425, "austin_suburban": 437, "austin_rural": 245,
    }
    for cell in args.cells:
        n_har = len(results[results["cell"] == cell])
        n_exp = expected.get(cell, "?")
        flag = "OK" if n_har == n_exp else "MISMATCH"
        print(f"  {cell:18s}  harvested={n_har:>6}  expected(other 4 modes)={n_exp!s:>6}  [{flag}]")
    total_har = len(results)
    print(f"  TOTAL harvested: {total_har} (expected 8,160 if all 12 cells run)")

    # Diagnostic severity summary (E-LA-06 residual + E-LA-14 carried-forward caveat)
    if "n_severe" in results.columns:
        print("\n### Severe-error counts by archetype (E-LA-06 residual / E-LA-14 carried-forward caveat check) ###")
        sev = results.groupby("archetype_id")["n_severe"].agg(["sum", "count"]).sort_values("sum", ascending=False)
        print(sev.head(20).to_string())

    # E-LA-14/E-LA-19 prevalence flag (structural-fixes plan §5 T11 / CP-D
    # directive): report CheckWarmupConvergence Severe prevalence in this
    # fleet-scale harvest, now with T01/T03/T06/T08 all live.
    if "n_warmup_convergence" in results.columns:
        print("\n### E-LA-14/E-LA-19 CheckWarmupConvergence prevalence (fleet-scale, this harvest's raw .err) ###")
        n_affected = int((results["n_warmup_convergence"] > 0).sum())
        n_total_hits = int(results["n_warmup_convergence"].sum())
        print(f"  Buildings with >=1 CheckWarmupConvergence Severe: {n_affected}/{len(results)}")
        print(f"  Total CheckWarmupConvergence hits (all buildings summed): {n_total_hits}")
        by_arch = results[results["n_warmup_convergence"] > 0].groupby("archetype_id")["n_warmup_convergence"].agg(["sum", "count"]).sort_values("sum", ascending=False)
        if not by_arch.empty:
            print(by_arch.to_string())
        else:
            print("  (none found in this harvest's fetched .err files)")

    print(f"\nRun date: {run_date}")
    print("Provenance: T19 full cluster sweep (post-structural-fixes), Speed/Linux, EnergyPlus 23.1, trim_outputs=True")
    print(f"Output CSV: {OUTPUT_ALL_CSV}")
    print(f"Summary CSV: {OUTPUT_SUMMARY_CSV}")


if __name__ == "__main__":
    main()
