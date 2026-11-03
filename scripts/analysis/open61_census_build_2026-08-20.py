"""T02 of PLAN_open61-census-open03-storeys-2026-08-20.md -- rebuild harness + stratified
pilot of 200, ahead of the 119-CPU-hour full census (T03, gated on CP-2).

Reuses (does not reimplement):
  * cell_context() / run_ep_isolated() from open35_storey_intervention_2026-08-19.py --
    cached step1 + fresh step2 pipeline context, and the isolated-cwd EnergyPlus runner
    (OPEN-58's shared-cwd ExpandObjects contamination fix). run_ep_isolated() has a
    documented relative-path trap (debug reference chapter 13): every idf/epw/outdir
    passed to it here is .resolve()'d to an absolute Path first.
  * openubem.idf.builder.BuildingIDF -- default trim_outputs=False (builder.py:219), never
    overridden here. This is the exact trap that cost the 2026-08-19 arc three
    measurements (plan §4): trim_outputs=True strips the per-zone Output:Variable block
    and parser.py's _check_zone_integrity (parser.py:203, called at :772-774) rejects it.
  * openubem.results.parser.parse_building() -- production's own EUI formula.
  * open61_census_read_2026-08-20.read_district_heating() -- T01's proven reader (108/108
    verified). manifest_row_for()-style construction mirrors
    open35_storey_intervention_2026-08-20.py:236-244 (inlined here, 6 lines, not imported,
    to avoid a doubly-nested importlib chain -- that file itself re-imports the
    2026-08-19 module under a different name).

C2b (added at CP-1): District-Heating "Water Systems" must equal "Total End Uses", and
every other end-use row must be ~0 for that column. T01's reader does not expose the
per-row breakdown (only the total and the reconciliation sum), so this script adds one
thin helper, _district_heating_row_breakdown(), that re-uses T01's own END_USE_ROWS
constant and issues the identical query T01's _abups_district_heating() already runs
internally -- it does not recompute the total independently, it only surfaces the rows
that function already touches. Not a second reader of the headline number.

Population: run 4 (open48_refleet4)'s own results/05_results.csv per cell,
simulation_status == "success" (8,153 of 8,160 -- F8's population). Stratified sample of
200: allocated across all 20 archetypes present in the fleet by fleet share (largest-
remainder method, minimum 1, capped by availability), then spread across cells within
each archetype (round-robin over the cells that carry that archetype).

Emits:
  openubem/outputs/comparisons/open61_census_pilot.csv            (one row per building,
                                                                     written incrementally)
  openubem/outputs/comparisons/open61_census_pilot_selection.csv  (how the 200 were chosen)

Scratch IDF/sim output goes OUTSIDE the repo tree -- the session scratchpad.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import random
import sqlite3
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "analysis"))

from openubem.idf.builder import BuildingIDF  # noqa: E402
from openubem.results.parser import parse_building  # noqa: E402
from openubem.semantic.building_classifier import _normalise_use_class  # noqa: E402

# -- reuse (not reimplement) T01's reader.
_spec_read = importlib.util.spec_from_file_location(
    "open61_census_read_20260820",
    REPO / "scripts" / "analysis" / "open61_census_read_2026-08-20.py",
)
_mod_read = importlib.util.module_from_spec(_spec_read)
sys.modules[_spec_read.name] = _mod_read
_spec_read.loader.exec_module(_mod_read)
read_district_heating = _mod_read.read_district_heating
END_USE_ROWS = _mod_read.END_USE_ROWS
GJ_TO_KWH = _mod_read.GJ_TO_KWH

# -- reuse (not reimplement) cell_context() / run_ep_isolated() from the 2026-08-19 script.
_spec19 = importlib.util.spec_from_file_location(
    "open35_t04_20260819_for_open61",
    REPO / "scripts" / "analysis" / "open35_storey_intervention_2026-08-19.py",
)
_mod19 = importlib.util.module_from_spec(_spec19)
sys.modules[_spec19.name] = _mod19
_spec19.loader.exec_module(_mod19)
cell_context = _mod19.cell_context
run_ep_isolated = _mod19.run_ep_isolated

RUN4 = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4")
CELLS = ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
         "la_centre", "la_urban", "la_suburban", "la_rural",
         "austin_centre", "austin_urban", "austin_suburban", "austin_rural"]

OUT = REPO / "openubem" / "outputs" / "comparisons"
PILOT_CSV = OUT / "open61_census_pilot.csv"
SELECTION_CSV = OUT / "open61_census_pilot_selection.csv"

SCRATCHPAD = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM"
    r"\89a28ab2-bc04-4d19-9e55-89a800c96691\scratchpad"
)
WORK = SCRATCHPAD / "open61_census_pilot_work"

SEED = 42
N_TARGET = 200
MAX_WORKERS = 4
C1_TOL_KWH_M2 = 0.01   # "machine precision" -- same EnergyPlus build, same parser, HEAD rebuild
C2B_TOL_GJ = 0.005     # same tolerance T01 used for its own reconciliation check

ROW_FIELDS = [
    "cell", "osm_id", "archetype_id",
    "footprint_area_m2", "recorded_floor_area_m2", "recorded_total_eui_kwh_m2",
    "recorded_dhw_eui_kwh_m2", "recorded_simulation_status",
    "generation_status", "zoning_strategy", "num_zones", "status", "elapsed_s",
    "dh_total_gj", "dh_total_kwh", "dh_a_reconciles", "dh_b_available",
    "dh_water_systems_gj", "dh_other_rows_sum_gj", "c2b_pass",
    "parsed_parse_status", "parsed_error_summary", "parsed_data_quality_flag",
    "parsed_floor_area_m2", "parsed_floor_area_provenance",
    "parsed_heating_eui_kwh_m2", "parsed_cooling_eui_kwh_m2", "parsed_lighting_eui_kwh_m2",
    "parsed_equipment_eui_kwh_m2", "parsed_fans_eui_kwh_m2", "parsed_pumps_eui_kwh_m2",
    "parsed_dhw_gas_eui_kwh_m2", "parsed_dhw_elec_eui_kwh_m2", "parsed_dhw_eui_kwh_m2",
    "parsed_cooking_eui_kwh_m2", "parsed_refrigeration_eui_kwh_m2",
    "parsed_elevators_eui_kwh_m2", "parsed_total_eui_kwh_m2", "parsed_iod",
    "c1_diff_kwh_m2", "c1_pass",
]


def load_population() -> pd.DataFrame:
    frames = []
    for cell in CELLS:
        p = RUN4 / cell / "results" / "05_results.csv"
        df = pd.read_csv(p, dtype={"osm_id": str})
        df["cell"] = cell
        frames.append(df)
    allf = pd.concat(frames, ignore_index=True)
    pop = allf[allf["simulation_status"] == "success"].copy()
    assert len(pop) == 8153, f"population drifted: {len(pop)} != 8153"
    return pop


def stratified_select(pop: pd.DataFrame, n_target: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = random.Random(seed)
    counts = pop["archetype_id"].value_counts()
    shares = counts / counts.sum() * n_target
    alloc = shares.apply(lambda x: max(1, int(x))).clip(upper=counts)
    remainder = n_target - int(alloc.sum())
    # Largest-remainder growth order: archetypes with the biggest fractional shortfall
    # get the next unit first. A single pass over 20 archetypes is not enough when
    # |remainder| exceeds 20 (small-n smoke tests, or a badly skewed n_target), so this
    # cycles the priority order repeatedly until the budget is exactly consumed or no
    # archetype has any more room to grow/shrink.
    if remainder > 0:
        order = (shares - alloc).sort_values(ascending=False).index.tolist()
        i, guard = 0, 0
        while remainder > 0 and guard < 1_000_000:
            arch = order[i % len(order)]
            if alloc[arch] < counts[arch]:
                alloc[arch] += 1
                remainder -= 1
            i += 1
            guard += 1
    elif remainder < 0:
        order = alloc.sort_values(ascending=False).index.tolist()
        i, guard = 0, 0
        while remainder < 0 and guard < 1_000_000:
            arch = order[i % len(order)]
            if alloc[arch] > 1:
                alloc[arch] -= 1
                remainder += 1
            i += 1
            guard += 1
    assert int(alloc.sum()) == n_target, f"allocation drifted: {int(alloc.sum())} != {n_target}"

    selected_rows = []
    selection_log = []
    for arch, n_i in alloc.items():
        n_i = int(n_i)
        sub = pop[pop["archetype_id"] == arch]
        cells_avail = sorted(sub["cell"].unique())
        pools = {c: sorted(sub.loc[sub["cell"] == c, "osm_id"].tolist()) for c in cells_avail}
        for c in pools:
            rng.shuffle(pools[c])
        picks = []
        ci = 0
        while len(picks) < n_i and any(pools.values()):
            c = cells_avail[ci % len(cells_avail)]
            if pools[c]:
                picks.append((c, pools[c].pop()))
            ci += 1
        for cell, osm_id in picks:
            selected_rows.append(
                pop[(pop["cell"] == cell) & (pop["osm_id"] == osm_id)].iloc[0]
            )
        selection_log.append({
            "archetype_id": arch, "fleet_n": int(counts[arch]), "target_n": n_i,
            "selected_n": len(picks), "n_cells_used": len(set(c for c, _ in picks)),
            "cells_used": ";".join(sorted(set(c for c, _ in picks))),
        })

    sel_df = pd.DataFrame(selected_rows).reset_index(drop=True)
    assert len(sel_df) == n_target, f"selection drifted: {len(sel_df)} != {n_target}"
    assert sel_df["osm_id"].duplicated().sum() == 0, "duplicate osm_id in selection"
    return sel_df, pd.DataFrame(selection_log)


def _district_heating_row_breakdown(sql_path: Path) -> tuple[float | None, float | None]:
    """Per-row District Heating column values (C2b). Re-uses T01's own END_USE_ROWS
    constant and the identical query T01's _abups_district_heating() already issues --
    surfaces rows that function computes internally but does not return.
    """
    conn = sqlite3.connect(str(sql_path))
    try:
        rows = conn.execute(
            "select RowName, Value from TabularDataWithStrings "
            "where ReportName='AnnualBuildingUtilityPerformanceSummary' "
            "and TableName='End Uses' and ColumnName='District Heating' "
            "and RowName in ({})".format(",".join("?" for _ in END_USE_ROWS)),
            END_USE_ROWS,
        ).fetchall()
    finally:
        conn.close()
    vals = {r: (float(v) if v not in (None, "") else 0.0) for r, v in rows}
    ws = vals.get("Water Systems")
    other_sum = sum(v for k, v in vals.items() if k != "Water Systems")
    return ws, other_sum


def manifest_row_for(row: pd.Series, mf: dict) -> pd.Series:
    """Mirrors open35_storey_intervention_2026-08-20.py:236-244 (inlined, not imported,
    to avoid a doubly-nested importlib chain)."""
    m = row.copy()
    m["num_zones"] = mf["num_zones"]
    m["data_quality_flag"] = mf["data_quality_flag"]
    m["resolution_mode"] = mf["resolution_mode"]
    m["_use_class"] = _normalise_use_class(row)[0]
    return m


def process_building(rec: dict, ctx: dict, work_dir: Path) -> dict:
    t0 = time.monotonic()
    out = {
        "cell": rec["cell"], "osm_id": rec["osm_id"], "archetype_id": rec["archetype_id"],
        "recorded_floor_area_m2": rec.get("floor_area_m2"),
        "recorded_total_eui_kwh_m2": rec.get("total_eui_kwh_m2"),
        "recorded_dhw_eui_kwh_m2": rec.get("dhw_eui_kwh_m2"),
        "recorded_simulation_status": rec.get("simulation_status"),
    }
    gdf_57 = ctx["gdf_57"]
    match = gdf_57[gdf_57["osm_id"] == rec["osm_id"]]
    if len(match) != 1:
        out["status"] = f"row_lookup_failed_n={len(match)}"
        out["elapsed_s"] = round(time.monotonic() - t0, 1)
        return out
    row = match.iloc[0]
    out["footprint_area_m2"] = float(row.get("footprint_area_m2", float("nan")))

    (work_dir / "idfs").mkdir(parents=True, exist_ok=True)
    mf = BuildingIDF(row, resolution_mode="auto").build(gdf_57, ctx["schedule_library"], work_dir)
    out["generation_status"] = mf["generation_status"]
    out["zoning_strategy"] = mf.get("zoning_strategy")
    out["num_zones"] = mf.get("num_zones")

    if mf["generation_status"] not in ("success", "fallback_bbox"):
        out["status"] = "idf_generation_failed"
        out["elapsed_s"] = round(time.monotonic() - t0, 1)
        return out

    idf_path = Path(mf["idf_path"]).resolve()
    epw_path = Path(ctx["epw_path"]).resolve()
    sim_out = (work_dir / "sim_out").resolve()
    run_ep_isolated(idf_path, epw_path, sim_out)
    sql_path = sim_out / "eplusout.sql"

    manifest_row = manifest_row_for(row, mf)
    metrics = parse_building(sql_path if sql_path.exists() else None, None, manifest_row)
    for k, v in metrics.items():
        if k in ("osm_id",):
            continue
        out[f"parsed_{k}"] = v

    if sql_path.exists():
        dh = read_district_heating(str(sql_path))
        out["dh_total_gj"] = dh.a_total_gj
        out["dh_total_kwh"] = dh.a_total_kwh
        out["dh_a_reconciles"] = dh.a_reconciles
        out["dh_b_available"] = dh.b_available
        ws_gj, other_sum_gj = _district_heating_row_breakdown(sql_path)
        out["dh_water_systems_gj"] = ws_gj
        out["dh_other_rows_sum_gj"] = other_sum_gj
        out["c2b_pass"] = bool(
            dh.a_total_gj is not None and ws_gj is not None
            and abs(dh.a_total_gj - ws_gj) < C2B_TOL_GJ
            and abs(other_sum_gj) < C2B_TOL_GJ
        )
        out["status"] = "ok"
    else:
        out["dh_total_gj"] = None
        out["status"] = "no_sql"

    if out.get("parsed_total_eui_kwh_m2") is not None and out.get("recorded_total_eui_kwh_m2") is not None:
        try:
            diff = float(out["parsed_total_eui_kwh_m2"]) - float(out["recorded_total_eui_kwh_m2"])
            out["c1_diff_kwh_m2"] = diff
            out["c1_pass"] = abs(diff) < C1_TOL_KWH_M2
        except (TypeError, ValueError):
            pass

    out["elapsed_s"] = round(time.monotonic() - t0, 1)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=N_TARGET)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--workers", type=int, default=MAX_WORKERS)
    args = ap.parse_args()

    t_start = time.monotonic()
    pop = load_population()
    print(f"population: {len(pop)} success-status buildings across {pop['cell'].nunique()} cells, "
          f"{pop['archetype_id'].nunique()} archetypes", flush=True)

    sel_df, sel_log = stratified_select(pop, args.n, args.seed)
    sel_log.to_csv(SELECTION_CSV, index=False)
    print(f"wrote {SELECTION_CSV} ({len(sel_log)} archetype rows)", flush=True)
    print(sel_log.to_string(), flush=True)

    if WORK.exists():
        import shutil
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)

    cells = sorted(sel_df["cell"].unique())
    ctx_by_cell = {}
    for cell in cells:
        print(f"[{cell}] building context (cached step1 + fresh step2) ...", flush=True)
        ctx_by_cell[cell] = cell_context(cell)

    PILOT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(PILOT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=ROW_FIELDS, extrasaction="ignore")
        writer.writeheader()
        fh.flush()

        tasks = []
        for i, (_, r) in enumerate(sel_df.iterrows()):
            safe_id = r["osm_id"].replace("/", "_").replace(":", "_")
            work_dir = WORK / r["cell"] / safe_id
            tasks.append((dict(r), ctx_by_cell[r["cell"]], work_dir))

        print(f"\n=== building + simulating {len(tasks)} buildings, {args.workers} concurrent max ===",
              flush=True)
        t_sim = time.monotonic()
        n_done = 0
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {pool.submit(process_building, rec, ctx, wd): (rec["osm_id"], rec["cell"], rec["archetype_id"])
                    for rec, ctx, wd in tasks}
            for fut in as_completed(futs):
                osm_id, cell, archetype_id = futs[fut]
                try:
                    row_out = fut.result()
                except Exception as exc:  # noqa: BLE001
                    row_out = {"osm_id": osm_id, "cell": cell, "archetype_id": archetype_id,
                               "status": f"exception:{exc}"[:200]}
                writer.writerow(row_out)
                fh.flush()
                n_done += 1
                print(f"  [{n_done}/{len(tasks)}] {row_out.get('cell')}/{osm_id}: "
                      f"status={row_out.get('status')} c1_pass={row_out.get('c1_pass')} "
                      f"dh_total_gj={row_out.get('dh_total_gj')} "
                      f"elapsed_s={row_out.get('elapsed_s')}", flush=True)

    print(f"\nsimulation wall clock: {time.monotonic() - t_sim:.1f}s", flush=True)
    print(f"total wall clock: {time.monotonic() - t_start:.1f}s", flush=True)
    print(f"wrote {PILOT_CSV}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
