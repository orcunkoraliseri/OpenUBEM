"""T04b of PLAN_four-board-items-2026-08-20.md -- run the intervention on the 21 buildings
CP-3 froze in openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_selection.csv.

Selection is FROZEN: no re-census, no re-selection, no substitution. This script only builds
and simulates the base/treated arms for the 21 rows already there and parses the results.

Reuses (does not reimplement):
  * build_arms(), manifest_row_for(), cell_context() -- all from
    open35_storey_intervention_2026-08-20.py (imported by file path; that module itself
    re-exports run_ep_isolated from the 2026-08-19 script under the same name).
  * run_ep_isolated() -- gives every EnergyPlus invocation its own cwd=outdir (hard rule 5 /
    OPEN-58's shared-cwd ExpandObjects contamination fix). Never open56_zone_volume_experiment's
    run_ep().
  * openubem.results.parser.parse_building() -- production's own EUI formula, for both arms of
    every building. Never the open56 hand-rolled Total-Site-Energy/Total-Building-Area read
    (OPEN-58's second defect: excludes fans_eui_kwh_m2).

Known contamination, stated not fixed (OPEN-61, opened 2026-08-20 from T01): parser.py's
METER_QUERY omits WaterSystems:DistrictHeating, undercounting total_eui_kwh_m2 by ~1-1.1% for
any building with district-heating-served DHW/heating/cooling. Both arms of every pair here go
through the identical parse_building() path, so the *paired* difference is unaffected; only the
*absolute* EUI in each arm is biased low by the same ~1%. Control 1's tolerance is widened to
1.5% (abs(delta) <= 1.5%) for this reason, stated per-row in the output.

Three pre-registered controls (§6 T04b of the plan), all reported whether they pass or fail:
  1. every one of the 21 base-arm EUIs reproduces on_record_total_eui_kwh_m2 within 1.5%
     (widened from 1% for the known DHW contamination above).
  2. at least 18 of 21 treated runs complete with no severe error.
  3. every treated IDF's storey count differs from its base IDF's -- verified by reading the
     built IDFs (build_arms()'s own actual_num_floors_from_idf check), not by trusting the
     selection table.
A failed control stops the task and is reported; it is never worked around.

Emits: openubem/outputs/comparisons/open35_storey_intervention_runs_2026-08-20.csv
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "analysis"))

from openubem.results.parser import parse_building  # noqa: E402

# -- reuse (not reimplement) T04's own build_arms / manifest_row_for / cell_context /
# run_ep_isolated. Filename has dashes-in-date style, import by file path.
_spec = importlib.util.spec_from_file_location(
    "open35_t04_20260820", REPO / "scripts" / "analysis" / "open35_storey_intervention_2026-08-20.py"
)
_mod20 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod20)
build_arms = _mod20.build_arms
manifest_row_for = _mod20.manifest_row_for
cell_context = _mod20.cell_context
run_ep_isolated = _mod20.run_ep_isolated

OUT = REPO / "openubem" / "outputs" / "comparisons"
SEL_CSV = OUT / "open35_storey_intervention_2026-08-20_selection.csv"
OUT_CSV = OUT / "open35_storey_intervention_runs_2026-08-20.csv"
WORK = Path(os.environ.get("TEMP", "C:/Temp")) / "open35_storey_intervention_runs_2026-08-20"

MAX_WORKERS = 3
FIDELITY_TOL_PCT = 1.5
MIN_CLEAN_TREATED = 18

_SEVERE = re.compile(r"\*\* Severe")
_FATAL = re.compile(r"\*\*\s+Fatal")


def err_stats(outdir: Path) -> dict:
    err = outdir / "eplusout.err"
    txt = err.read_text(encoding="utf-8", errors="replace") if err.exists() else ""
    return {
        "completed": "EnergyPlus Completed Successfully" in txt,
        "n_severe": len(_SEVERE.findall(txt)),
        "n_fatal": len(_FATAL.findall(txt)),
        "err_exists": err.exists(),
    }


def run_arm(idf_path: Path, epw_path: Path, sim_out: Path) -> dict:
    t0 = time.monotonic()
    run_ep_isolated(idf_path, epw_path, sim_out)
    stats = err_stats(sim_out)
    stats["elapsed_s"] = round(time.monotonic() - t0, 1)
    stats["sim_out"] = str(sim_out)
    return stats


def main() -> int:
    t0 = time.monotonic()
    sel = pd.read_csv(SEL_CSV)
    assert len(sel) == 21, f"selection drifted from the frozen 21: got {len(sel)} rows"
    print(f"loaded frozen selection: {len(sel)} rows across {sel['cell'].nunique()} cells")

    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)

    cells = sorted(sel["cell"].unique())
    ctx_by_cell = {}
    for cell in cells:
        print(f"[{cell}] building context (cached step1 + fresh step2) ...", flush=True)
        ctx_by_cell[cell] = cell_context(cell)

    # -- build both IDF arms for all 21, per hard rule 5 with a unique work_dir per building.
    prep_rows = []
    for _, r in sel.iterrows():
        cell, osm_id = r["cell"], r["osm_id"]
        lev = int(r["treated_storeys_archetype_fallback"])
        safe_id = osm_id.replace("/", "_").replace(":", "_")
        work_dir = WORK / cell / safe_id
        ctx = ctx_by_cell[cell]
        rec = build_arms(cell, osm_id, lev, ctx, work_dir)
        rec["on_record_total_eui_kwh_m2"] = float(r["on_record_total_eui_kwh_m2"])
        rec["archetype_id"] = r.get("archetype_id", rec.get("archetype_id"))
        print(f"  build {cell}/{osm_id}: prep_status={rec.get('prep_status')} "
              f"base_floors_idf={rec.get('base_num_floors_from_idf')} "
              f"treat_floors_idf={rec.get('treat_num_floors_from_idf')} "
              f"floor_count_control_pass={rec.get('floor_count_control_pass')}", flush=True)
        prep_rows.append(rec)

    ok_rows = [r for r in prep_rows if r.get("prep_status") == "ok"]
    print(f"\nprep: {len(ok_rows)} / {len(prep_rows)} passed IDF generation + floor-count build check")

    # -- simulate both arms for every prep-ok building, unique cwd per invocation (hard rule 5).
    tasks = []
    for rec in ok_rows:
        cell, osm_id = rec["cell"], rec["osm_id"]
        epw = ctx_by_cell[cell]["epw_path"]
        base_out = Path(rec["base_idf_path"]).parent.parent / "base_sim_out"
        treat_out = Path(rec["treat_idf_path"]).parent.parent / "treat_sim_out"
        tasks.append((cell, osm_id, "base", Path(rec["base_idf_path"]), epw, base_out))
        tasks.append((cell, osm_id, "treat", Path(rec["treat_idf_path"]), epw, treat_out))

    print(f"\n=== simulating {len(tasks)} EnergyPlus runs, {MAX_WORKERS} concurrent max ===", flush=True)
    t_sim = time.monotonic()
    sim_results: dict[tuple, dict] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {
            pool.submit(run_arm, idf, epw, outdir): (cell, osm_id, arm)
            for cell, osm_id, arm, idf, epw, outdir in tasks
        }
        for fut in as_completed(futs):
            key = futs[fut]
            rec = fut.result()
            sim_results[key] = rec
            print(f"  done {key[0]}/{key[1]}/{key[2]}: completed={rec['completed']} "
                  f"severe={rec['n_severe']} fatal={rec['n_fatal']} ({rec['elapsed_s']}s)", flush=True)
    print(f"simulation wall clock: {time.monotonic() - t_sim:.1f}s")

    # -- serial re-verification of empty output dirs before scoring as failures.
    empties = [(cell, osm_id, arm, idf, epw, outdir) for cell, osm_id, arm, idf, epw, outdir in tasks
               if not (outdir / "eplusout.err").exists() or (outdir / "eplusout.err").stat().st_size == 0]
    if empties:
        print(f"\n{len(empties)} empty output dirs -- re-verifying SERIALLY ...", flush=True)
        for cell, osm_id, arm, idf, epw, outdir in empties:
            print(f"  serial re-run {cell}/{osm_id}/{arm} ...", flush=True)
            sim_results[(cell, osm_id, arm)] = run_arm(idf, epw, outdir)

    # -- parse EUI through production parse_building(), both arms, every ok building.
    results = []
    for rec in ok_rows:
        cell, osm_id = rec["cell"], rec["osm_id"]
        ctx = ctx_by_cell[cell]
        row = {"cell": cell, "osm_id": osm_id, "archetype_id": rec["archetype_id"],
               "base_storeys": 1, "treated_storeys": rec["treated_levels"],
               "on_record_total_eui_kwh_m2": rec["on_record_total_eui_kwh_m2"],
               "floor_count_control_pass": rec.get("floor_count_control_pass"),
               "base_num_floors_from_idf": rec.get("base_num_floors_from_idf"),
               "treat_num_floors_from_idf": rec.get("treat_num_floors_from_idf")}

        for arm, row_key, mf_prefix, sim_key in (("base", "row_base", "base", "base"),
                                                   ("treat", "row_treat", "treat", "treat")):
            sim = sim_results.get((cell, osm_id, sim_key), {})
            sim_out = Path(sim.get("sim_out", "")) if sim.get("sim_out") else None
            sql_path = (sim_out / "eplusout.sql") if sim_out else None
            manifest_row = manifest_row_for(
                rec[row_key],
                {"num_zones": rec[f"{mf_prefix}_num_zones"],
                 "data_quality_flag": rec[f"{mf_prefix}_data_quality_flag"],
                 "resolution_mode": rec[f"{mf_prefix}_resolution_mode"]},
                ctx,
            )
            metrics = parse_building(sql_path if (sql_path and sql_path.exists()) else None, None, manifest_row)
            row[f"{arm}_parse_status"] = metrics["parse_status"]
            row[f"{arm}_eui_kwh_m2"] = metrics["total_eui_kwh_m2"]
            row[f"{arm}_completed"] = sim.get("completed")
            row[f"{arm}_n_severe"] = sim.get("n_severe")
            row[f"{arm}_n_fatal"] = sim.get("n_fatal")

        row["base_fidelity_diff_pct"] = (
            100.0 * (row["base_eui_kwh_m2"] - row["on_record_total_eui_kwh_m2"]) / row["on_record_total_eui_kwh_m2"]
            if pd.notna(row["base_eui_kwh_m2"]) and row["on_record_total_eui_kwh_m2"] else float("nan")
        )
        both_parsed = (row["base_parse_status"] in ("success", "success_csv_fallback")
                        and row["treat_parse_status"] in ("success", "success_csv_fallback")
                        and pd.notna(row["base_eui_kwh_m2"]) and pd.notna(row["treat_eui_kwh_m2"]))
        if both_parsed:
            row["delta_eui_kwh_m2"] = row["treat_eui_kwh_m2"] - row["base_eui_kwh_m2"]
            row["pct_change"] = 100.0 * row["delta_eui_kwh_m2"] / row["base_eui_kwh_m2"]
            row["run_status"] = "ok"
        else:
            row["delta_eui_kwh_m2"] = float("nan")
            row["pct_change"] = float("nan")
            row["run_status"] = f"base={row['base_parse_status']}|treat={row['treat_parse_status']}"
        results.append(row)

    # -- rows that never got an IDF built at all (prep_status != ok) still appear, run_status names why.
    for rec in prep_rows:
        if rec.get("prep_status") == "ok":
            continue
        results.append({
            "cell": rec["cell"], "osm_id": rec["osm_id"], "archetype_id": rec.get("archetype_id"),
            "base_storeys": 1, "treated_storeys": rec.get("treated_levels"),
            "on_record_total_eui_kwh_m2": rec.get("on_record_total_eui_kwh_m2"),
            "floor_count_control_pass": rec.get("floor_count_control_pass"),
            "base_num_floors_from_idf": rec.get("base_num_floors_from_idf"),
            "treat_num_floors_from_idf": rec.get("treat_num_floors_from_idf"),
            "base_parse_status": None, "treat_parse_status": None,
            "base_eui_kwh_m2": float("nan"), "treat_eui_kwh_m2": float("nan"),
            "base_fidelity_diff_pct": float("nan"), "delta_eui_kwh_m2": float("nan"),
            "pct_change": float("nan"), "run_status": f"prep_failed:{rec.get('prep_status')}",
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {OUT_CSV} ({len(results_df)} rows)")

    # ================= controls =================
    print("\n=== CONTROL 1: base-arm fidelity vs on_record_total_eui_kwh_m2 (tol=1.5%) ===")
    print(results_df[["cell", "osm_id", "base_eui_kwh_m2", "on_record_total_eui_kwh_m2",
                       "base_fidelity_diff_pct"]].to_string())
    c1_fail = results_df[results_df["base_fidelity_diff_pct"].abs() > FIDELITY_TOL_PCT]
    control1_pass = len(c1_fail) == 0 and results_df["base_fidelity_diff_pct"].notna().all()
    print(f"CONTROL 1 {'PASS' if control1_pass else 'FAIL'}: "
          f"{len(results_df) - len(c1_fail)}/{len(results_df)} within {FIDELITY_TOL_PCT}%; "
          f"{len(c1_fail)} outside tolerance or unparseable")

    print("\n=== CONTROL 2: treated runs completing clean (no severe error) ===")
    treat_clean = results_df[(results_df["treat_completed"] == True) & (results_df["treat_n_severe"] == 0)]  # noqa: E712
    control2_pass = len(treat_clean) >= MIN_CLEAN_TREATED
    print(f"CONTROL 2 {'PASS' if control2_pass else 'FAIL'}: "
          f"{len(treat_clean)}/{len(results_df)} treated runs clean (need >= {MIN_CLEAN_TREATED})")

    print("\n=== CONTROL 3: treated IDF storey count differs from base (read from built IDFs) ===")
    print(results_df[["cell", "osm_id", "base_num_floors_from_idf", "treat_num_floors_from_idf",
                       "treated_storeys", "floor_count_control_pass"]].to_string())
    control3_pass = bool(results_df["floor_count_control_pass"].fillna(False).all()) and len(results_df) == 21
    n_diff = int(results_df["floor_count_control_pass"].fillna(False).sum())
    print(f"CONTROL 3 {'PASS' if control3_pass else 'FAIL'}: {n_diff}/{len(results_df)} rows confirm "
          f"a storey-count difference in the built IDFs")

    print("\n=== PAIRED DIFFERENCE (successfully parsed pairs only) ===")
    ok_pairs = results_df[results_df["run_status"] == "ok"].copy()
    print(f"{len(ok_pairs)}/{len(results_df)} rows have a usable paired difference")
    if len(ok_pairs) > 0:
        print(ok_pairs[["cell", "osm_id", "archetype_id", "base_eui_kwh_m2", "treat_eui_kwh_m2",
                         "delta_eui_kwh_m2", "pct_change"]].to_string())
        n_up = int((ok_pairs["delta_eui_kwh_m2"] > 0).sum())
        n_down = int((ok_pairs["delta_eui_kwh_m2"] < 0).sum())
        n_zero = int((ok_pairs["delta_eui_kwh_m2"] == 0).sum())
        print(f"\nsign split: {n_up} up / {n_down} down / {n_zero} exactly zero (of {len(ok_pairs)})")
        print("\nwithin-cell medians (absolute kWh/m2 and %):")
        by_cell = ok_pairs.groupby("cell").agg(
            n=("osm_id", "size"),
            median_delta_kwh_m2=("delta_eui_kwh_m2", "median"),
            median_pct_change=("pct_change", "median"),
        )
        print(by_cell.to_string())

    print(f"\ntotal wall clock: {time.monotonic() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
