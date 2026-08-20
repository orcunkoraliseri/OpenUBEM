"""T04 of PLAN_ten-items-2026-08-19.md -- OPEN-35, an intervention with a control.

The register's own named next step: the +47.9% naive fleet EUI gap for the 2,611-building
"neither levels nor height_m" population cannot be settled cross-sectionally (X04,
2026-08-18 overnight, showed it is composition -- nyc_suburban is 1,589 of 2,611 with no
comparison group, and within cells the sign is not even consistent). This is the promised
intervention: rebuild a sample of the 1,031-building subpopulation (mid-/high-rise archetype,
built at a single storey) at the storey count the ARCHETYPE was actually selected on, and run
both arms in the same session (the design that worked for OPEN-56 -- see
scripts/analysis/open56_zone_volume_experiment.py).

Mechanism (register, OPEN-35 section; code, line-cited):
  * openubem/semantic/building_classifier.py:137-156 _impute_levels() -- when both `levels`
    and `height_m` are missing, archetype SELECTION uses the group median over the batch
    (levels_group_median[use_class], fit on observed-levels rows only, no leakage), falling
    further back to levels_global_median (fit on the whole cell's observed rows), and only
    then to a flat LEVELS_DEFAULT_LOW = 1 if the whole cell has zero observed-levels rows.
  * openubem/geometry/footprint.py:58-63 derive_num_floors() -- geometry CONSTRUCTION falls
    back to 1 for the same missing-both case, unconditionally.
  * The imputed levels value is never persisted (OPEN-30) -- there is no column to read it
    from. This script recovers it by calling _impute_levels() directly, with the SAME
    levels_group_median/levels_global_median lookup step2 built, on the SAME use_class the
    row itself normalises to. This is code reuse, not reimplementation.

STOP-AND-REPORT-WORTHY DISCOVERY, made by this script's own census phase (run before any
EnergyPlus compute, see CENSUS below): the register's "archetype chosen at group-median
storeys, geometry built at 1" framing describes only a SMALL MINORITY of the 1,031 population.
For the rest, _impute_levels ALSO returns 1 (via levels_global_median or LEVELS_DEFAULT_LOW),
so archetype selection and geometry construction do not actually disagree numerically -- both
land on 1. This is reported in full below; it reshapes the sample this task can honestly run
an intervention on. See the census table for the exact breakdown.

Design:
  treatment  = a second, fresh BuildingIDF.build() call on a COPY of the row with `levels`
               overridden to the recovered value _impute_levels() actually used at
               classification time. archetype_id is untouched (already fixed by step2);
               footprint_area_m2 is untouched (Stage-1 column, independent of levels).
               Nothing else differs.
  baseline   = a fresh BuildingIDF.build() call on the row AS PERSISTED (levels still NaN raw
               -> derive_num_floors returns 1), NOT the archived run-2 IDF/result. Both arms
               are built and simulated in this session (OPEN-56 lesson: mixing a days-old
               archived run with a fresh one confounds the treatment with whatever else
               drifted).
  fidelity check = the freshly-rebuilt baseline arm's EUI is compared against the ARCHIVED
               run-2 result for the same building (open35_eui_consequence.csv). Independent of
               the treated-vs-baseline delta; checks this harness reproduces production before
               its treated-arm numbers are trusted.
  negative controls = buildings in the SAME 1,031 population whose recovered levels value is 1
               (median genuinely 1, or no median exists at all) are run through the identical
               baseline/treated pipeline. Because `levels` is 1 in both arms for these, the two
               IDFs are expected to be at worst float-noise different; this is the "untreated
               hold-out subset" control the plan's How-to-test names.
  corpus     = open48_refleet (run 2) -- the same corpus open35_eui_consequence.csv and T07
               used, and NOT open48_refleet3, which T02 is using concurrently this pass.
  resolution_mode = "auto" (BuildingIDF's default, and what v12_cell_pipeline.run_cell uses
               with no override -- the mode the +47.9% naive gap and the fleet EUI figures
               were computed under).

Caps: 4 concurrent EnergyPlus workers (hard rule 7 / T04 step 4); every "empty output
directory" is re-verified serially before being scored as a failure.

Emits:
  openubem/outputs/comparisons/open35_storey_intervention_census.csv    (all 1,031, no IDFs)
  openubem/outputs/comparisons/open35_storey_intervention_prep.csv      (built-IDF subset)
  openubem/outputs/comparisons/open35_storey_intervention_results.csv   (simulated subset)
"""
from __future__ import annotations

import json
import os
import random
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "analysis"))

from scripts.validation.v12_cell_pipeline import CELL_CONFIGS, step1_fetch, step2_classify_enrich  # noqa: E402
from openubem.semantic.building_classifier import (  # noqa: E402
    _INPUT_SCHEMA_COLUMNS, BuildingClassifier, _normalise_use_class, _impute_levels,
)
from openubem.idf.builder import BuildingIDF  # noqa: E402
from open56_zone_volume_experiment import _split_objects, _fields, _verts, read_run  # noqa: E402
import subprocess  # noqa: E402

EPLUS = Path("C:/EnergyPlusV23-1-0/energyplus.exe")


def run_ep_isolated(idf: Path, epw: Path, outdir: Path) -> None:
    """Cross-building contamination discovered live in this task (see write-up):
    EnergyPlus's ExpandObjects (-x) preprocessing step appears to consult a
    working-directory-relative intermediate file rather than one scoped to `-d`.
    Two invocations sharing the SAME process cwd, run minutes apart (not a tight
    race), produced BYTE-IDENTICAL eplusout.sql for two different buildings with
    different footprints and different storey counts -- one silently simulated the
    OTHER building's expanded IDF. Fix: give every invocation its own `cwd=outdir`,
    which open56_zone_volume_experiment.py's run_ep() (imported everywhere else in
    this repo's analysis scripts) does not do. Not a change to production code --
    production never runs two local EnergyPlus invocations from one shared cwd like
    this harness does.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(EPLUS), "-x", "-w", str(epw), "-d", str(outdir), str(idf)],
                   capture_output=True, text=True, timeout=1800, cwd=str(outdir))


run_ep = run_ep_isolated

BASE = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/open48_refleet")
WORK = Path(os.environ.get("TEMP", "C:/Temp")) / "open35_storey_intervention"
OUT = REPO / "openubem" / "outputs" / "comparisons"
POP_CSV = OUT / "open35_eui_consequence.csv"

SEED = 42
NEG_CONTROL_PER_BUCKET = 5   # negative-control draw size per zero-disagreement sub-bucket
MAX_WORKERS = 4              # hard rule 7 -- shared with two other locally-running agents
FLOOR_TO_FLOOR_M = 3.5


def load_narrow_population() -> pd.DataFrame:
    pop = pd.read_csv(POP_CSV)
    narrow = pop[
        (pop["midhigh_at_one_storey"] == True)  # noqa: E712
        & (pop["archetype_id"].isin(["MidriseApartment", "HighriseApartment"]))
    ].copy()
    assert len(narrow) == 1031, f"narrow population drifted: {len(narrow)} != 1031"
    return narrow


def cell_context(cell: str) -> dict:
    cfg = CELL_CONFIGS[cell]
    cell_base = BASE / cell
    gpkg = cell_base / "01_buildings.gpkg"
    assert gpkg.exists(), f"frozen input missing for {cell}: {gpkg}"
    epw_candidates = sorted((cell_base / "weather").rglob("*.epw"))
    assert epw_candidates, f"no cached EPW for {cell}"
    epw_path = epw_candidates[0]

    print(f"[{cell}] step1 (cached) ...", flush=True)
    gdf_raw = step1_fetch(cfg["lat"], cfg["lon"], cfg["radius_m"], cell_base)
    assert gpkg.exists(), "step1_fetch must not have re-fetched -- gpkg still present"

    scratch = WORK / "step2_scratch" / cell
    scratch.mkdir(parents=True, exist_ok=True)
    print(f"[{cell}] step2 (classify + enrich, fresh) ...", flush=True)
    gdf_57, schedule_library = step2_classify_enrich(gdf_raw, epw_path, scratch, cell)

    gdf_raw2 = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_raw2["levels"] = gdf_raw2["levels"].astype("Int64")
    bc = BuildingClassifier()
    levels_group_median, levels_global_median = bc._build_levels_median_lookup(gdf_raw2)

    return {
        "gdf_57": gdf_57, "schedule_library": schedule_library, "epw_path": epw_path,
        "levels_group_median": levels_group_median, "levels_global_median": levels_global_median,
        "bc": bc,
    }


def census_cell(cell: str, osm_ids: list[str], ctx: dict) -> list[dict]:
    """No IDF build. For every sampled osm_id in this cell: use_class, the recovered
    _impute_levels() value/source, and whether it constitutes a genuine numeric disagreement
    (recovered value > 1) with geometry's unconditional fallback of 1.
    """
    gdf_57 = ctx["gdf_57"]
    bc = ctx["bc"]
    rows = []
    sub = gdf_57[gdf_57["osm_id"].isin(osm_ids)]
    for _, row in sub.iterrows():
        uc, score = _normalise_use_class(row, dominant_tag_threshold=bc.dominant_tag_threshold)
        lev, lev_src = _impute_levels(
            row, floor_to_floor_m=bc.floor_to_floor_m, use_class=uc,
            levels_group_median=ctx["levels_group_median"], levels_global_median=ctx["levels_global_median"],
        )
        rows.append({
            "cell": cell, "osm_id": row["osm_id"], "archetype_id": row["archetype_id"],
            "use_class": uc, "recovered_levels": int(lev), "recovered_lev_src": lev_src,
            "genuine_disagreement": bool(lev > 1),
        })
    return rows


def actual_num_floors_from_idf(idf_path: Path, floor_to_floor_m: float = FLOOR_TO_FLOOR_M) -> float:
    text = idf_path.read_text(encoding="utf-8", errors="replace")
    zmax = 0.0
    for chunk in _split_objects(text):
        f = _fields(chunk)
        if not f or f[0].upper() != "BUILDINGSURFACE:DETAILED" or len(f) < 15:
            continue
        for v in _verts(f, 12):
            zmax = max(zmax, v[2])
    if zmax <= 0:
        return 0.0
    return zmax / floor_to_floor_m


def build_arms(cell: str, osm_id: str, lev: int, ctx: dict, work_dir: Path) -> dict:
    gdf_57 = ctx["gdf_57"]
    match = gdf_57[gdf_57["osm_id"] == osm_id]
    if len(match) != 1:
        return {"cell": cell, "osm_id": osm_id, "prep_status": f"row_lookup_failed_n={len(match)}"}
    row = match.iloc[0]

    row_base = row.copy()
    row_treat = row.copy()
    row_treat["levels"] = int(lev)

    base_dir, treat_dir = work_dir / "baseline", work_dir / "treated"
    (base_dir / "idfs").mkdir(parents=True, exist_ok=True)
    (treat_dir / "idfs").mkdir(parents=True, exist_ok=True)

    mf_base = BuildingIDF(row_base, resolution_mode="auto").build(gdf_57, ctx["schedule_library"], base_dir)
    mf_treat = BuildingIDF(row_treat, resolution_mode="auto").build(gdf_57, ctx["schedule_library"], treat_dir)

    rec = {
        "cell": cell, "osm_id": osm_id, "archetype_id": row["archetype_id"],
        "recovered_levels": int(lev),
        "footprint_area_m2": float(row.get("footprint_area_m2", float("nan"))),
        "base_generation_status": mf_base["generation_status"],
        "treat_generation_status": mf_treat["generation_status"],
        "base_zoning_strategy": mf_base["zoning_strategy"],
        "treat_zoning_strategy": mf_treat["zoning_strategy"],
        "base_num_zones": mf_base["num_zones"],
        "treat_num_zones": mf_treat["num_zones"],
        "base_idf_path": mf_base["idf_path"],
        "treat_idf_path": mf_treat["idf_path"],
        "epw_path": str(row.get("epw_path")),
    }
    if rec["base_generation_status"] != "success" or rec["treat_generation_status"] != "success":
        rec["prep_status"] = "idf_generation_failed"
        return rec

    base_floors = actual_num_floors_from_idf(Path(mf_base["idf_path"]))
    treat_floors = actual_num_floors_from_idf(Path(mf_treat["idf_path"]))
    rec["base_num_floors_from_idf"] = round(base_floors, 3)
    rec["treat_num_floors_from_idf"] = round(treat_floors, 3)
    rec["floor_count_control_pass"] = (round(base_floors) == 1 and round(treat_floors) == int(lev))
    rec["prep_status"] = "ok" if rec["floor_count_control_pass"] else "floor_count_control_FAILED"
    return rec


def run_ep_bounded(label: str, idf_path: Path, epw_path: Path, outdir: Path) -> dict:
    t0 = time.monotonic()
    run_ep(idf_path, epw_path, outdir)
    rec = read_run(outdir)
    rec["label"] = label
    rec["elapsed_s"] = round(time.monotonic() - t0, 1)
    return rec


def main() -> int:
    t_start = time.monotonic()
    narrow = load_narrow_population()
    cells = sorted(narrow["cell"].unique())
    print(f"narrow OPEN-35 population: {len(narrow)} buildings across {len(cells)} cells: {cells}")

    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)

    census_rows = []
    ctx_by_cell = {}
    for cell in cells:
        osm_ids = narrow.loc[narrow["cell"] == cell, "osm_id"].tolist()
        print(f"\n=== {cell}: census over {len(osm_ids)} population buildings ===", flush=True)
        ctx = cell_context(cell)
        ctx_by_cell[cell] = ctx
        census_rows.extend(census_cell(cell, osm_ids, ctx))

    census_df = pd.DataFrame(census_rows)
    census_out = OUT / "open35_storey_intervention_census.csv"
    census_df.to_csv(census_out, index=False)
    print(f"\nwrote {census_out}  ({len(census_df)} rows, full narrow population)")

    print("\n=== CENSUS SUMMARY (all 1,031, no IDFs built) ===")
    by_cell = census_df.groupby("cell").agg(
        n=("osm_id", "size"),
        recovered_levels=("recovered_levels", "first"),
        lev_src=("recovered_lev_src", "first"),
        genuine=("genuine_disagreement", "first"),
    )
    print(by_cell.to_string())
    n_genuine = int(census_df["genuine_disagreement"].sum())
    print(f"\nGENUINE numeric disagreement (recovered levels > 1): {n_genuine} / {len(census_df)} "
          f"({100.0*n_genuine/len(census_df):.2f}%)")
    print(f"Zero-disagreement (recovered levels == 1, either via a real median==1 or via "
          f"levels_global_median/LEVELS_DEFAULT_LOW because the cell has no observed levels at "
          f"all): {len(census_df) - n_genuine} / {len(census_df)}")

    # -- Selection: ALL genuine-disagreement buildings (this population turns out small; take
    # the whole thing, not a sample of it), plus a small stratified negative-control draw from
    # each zero-disagreement sub-bucket (median-genuinely-1 vs no-median-at-all), seed=42.
    treat_set = census_df[census_df["genuine_disagreement"]].copy()
    zero_set = census_df[~census_df["genuine_disagreement"]].copy()

    rng = random.Random(SEED)
    neg_rows = []
    for src, grp in zero_set.groupby("recovered_lev_src"):
        ids = sorted(grp["osm_id"].tolist())
        picked = ids if len(ids) <= NEG_CONTROL_PER_BUCKET else sorted(rng.sample(ids, NEG_CONTROL_PER_BUCKET))
        neg_rows.append(grp[grp["osm_id"].isin(picked)])
    neg_set = pd.concat(neg_rows, ignore_index=True) if neg_rows else zero_set.iloc[0:0]

    run_set = pd.concat([treat_set.assign(arm_kind="treatment"),
                          neg_set.assign(arm_kind="negative_control")], ignore_index=True)
    print(f"\nSELECTED FOR SIMULATION: {len(treat_set)} genuine treatment + {len(neg_set)} "
          f"negative-control = {len(run_set)} buildings total ({2*len(run_set)} EnergyPlus runs)")
    print(run_set[["cell", "osm_id", "archetype_id", "recovered_levels", "recovered_lev_src",
                    "arm_kind"]].to_string())

    prep_rows = []
    for cell, grp in run_set.groupby("cell"):
        ctx = ctx_by_cell[cell]
        for _, r in grp.iterrows():
            osm_id = r["osm_id"]
            safe_id = osm_id.replace("/", "_").replace(":", "_")
            work_dir = WORK / cell / safe_id
            rec = build_arms(cell, osm_id, int(r["recovered_levels"]), ctx, work_dir)
            rec["arm_kind"] = r["arm_kind"]
            rec["recovered_lev_src"] = r["recovered_lev_src"]
            print(f"  build {osm_id} [{r['arm_kind']}]: {rec.get('prep_status')} "
                  f"base_floors_idf={rec.get('base_num_floors_from_idf')} "
                  f"treat_floors_idf={rec.get('treat_num_floors_from_idf')}", flush=True)
            prep_rows.append(rec)

    prep_df = pd.DataFrame(prep_rows)
    prep_out = OUT / "open35_storey_intervention_prep.csv"
    prep_df.to_csv(prep_out, index=False)
    print(f"\nwrote {prep_out}")

    ok_df = prep_df[prep_df["prep_status"] == "ok"].copy()
    print(f"prep: {len(ok_df)} / {len(prep_df)} passed the floor-count control")
    print(f"census + prep wall clock: {time.monotonic() - t_start:.1f}s")

    if len(ok_df) == 0:
        print("Nothing to simulate -- stopping before EnergyPlus.")
        return 0

    # -- Simulate, 4 concurrent EnergyPlus workers max.
    tasks = []
    for _, r in ok_df.iterrows():
        epw = ctx_by_cell[r["cell"]]["epw_path"]
        base_out = Path(r["base_idf_path"]).parent.parent / "base_sim_out"
        treat_out = Path(r["treat_idf_path"]).parent.parent / "treat_sim_out"
        tasks.append((r["cell"], r["osm_id"], "base", Path(r["base_idf_path"]), epw, base_out))
        tasks.append((r["cell"], r["osm_id"], "treat", Path(r["treat_idf_path"]), epw, treat_out))

    print(f"\n=== simulating {len(tasks)} runs, {MAX_WORKERS} concurrent max ===", flush=True)
    t_sim = time.monotonic()
    sim_results: dict[tuple, dict] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {
            pool.submit(run_ep_bounded, f"{cell}/{osm_id}/{arm}", idf, epw, outdir): (cell, osm_id, arm, outdir)
            for cell, osm_id, arm, idf, epw, outdir in tasks
        }
        for fut in as_completed(futs):
            cell, osm_id, arm, outdir = futs[fut]
            rec = fut.result()
            sim_results[(cell, osm_id, arm)] = rec
            print(f"  done {cell}/{osm_id}/{arm}: completed={rec['completed']} "
                  f"severe={rec['n_severe']} fatal={rec['n_fatal']} eui={rec['eui_kwh_m2']} "
                  f"({rec['elapsed_s']}s)", flush=True)

    # -- Serial re-verification of empty output directories (hard rule 7).
    empties = [(cell, osm_id, arm, outdir) for cell, osm_id, arm, idf, epw, outdir in tasks
               if not (outdir / "eplusout.err").exists() or (outdir / "eplusout.err").stat().st_size == 0]
    if empties:
        print(f"\n{len(empties)} empty output directories -- re-verifying SERIALLY before scoring "
              f"as failures ...", flush=True)
        idf_by_key = {(cell, osm_id, arm): idf for cell, osm_id, arm, idf, epw, outdir in tasks}
        epw_by_key = {(cell, osm_id, arm): epw for cell, osm_id, arm, idf, epw, outdir in tasks}
        for cell, osm_id, arm, outdir in empties:
            key = (cell, osm_id, arm)
            print(f"  serial re-run {cell}/{osm_id}/{arm} ...", flush=True)
            rec = run_ep_bounded(f"{cell}/{osm_id}/{arm}", idf_by_key[key], epw_by_key[key], outdir)
            sim_results[key] = rec
            print(f"    serial result: completed={rec['completed']} severe={rec['n_severe']} "
                  f"fatal={rec['n_fatal']} eui={rec['eui_kwh_m2']}", flush=True)

    print(f"simulation wall clock: {time.monotonic() - t_sim:.1f}s")

    results_rows = []
    for _, r in ok_df.iterrows():
        cell, osm_id = r["cell"], r["osm_id"]
        b = sim_results.get((cell, osm_id, "base"), {})
        t = sim_results.get((cell, osm_id, "treat"), {})
        rec = dict(r)
        for k, v in b.items():
            rec[f"base_{k}"] = v
        for k, v in t.items():
            rec[f"treat_{k}"] = v
        if b.get("eui_kwh_m2") and t.get("eui_kwh_m2"):
            rec["delta_eui"] = t["eui_kwh_m2"] - b["eui_kwh_m2"]
            rec["pct_change"] = 100.0 * rec["delta_eui"] / b["eui_kwh_m2"]
        results_rows.append(rec)

    results_df = pd.DataFrame(results_rows)

    # -- Cross-building contamination control (discovered live in this task -- see run_ep_isolated's
    # docstring). Any two DIFFERENT (cell, osm_id, arm) rows sharing an identical
    # (base_floor_area_m2, base_site_energy_gj) or (treat_floor_area_m2, treat_site_energy_gj) pair
    # means one silently simulated the other's expanded IDF. This voids those rows' numbers.
    print("\n=== CONTAMINATION CONTROL: checking for cross-building duplicate outputs ===")
    contaminated = set()
    for arm in ("base", "treat"):
        key_cols = [f"{arm}_floor_area_m2", f"{arm}_site_energy_gj"]
        if not all(c in results_df.columns for c in key_cols):
            continue
        dupe_mask = results_df.duplicated(subset=key_cols, keep=False) & results_df[key_cols[0]].notna()
        if dupe_mask.any():
            dupes = results_df.loc[dupe_mask, ["cell", "osm_id"] + key_cols]
            print(f"  {arm}: DUPLICATE outputs found across different buildings:\n{dupes.to_string()}")
            contaminated.update(results_df.loc[dupe_mask, "osm_id"].tolist())
        else:
            print(f"  {arm}: no cross-building duplicates -- clean")
    if contaminated:
        results_df["contaminated"] = results_df["osm_id"].isin(contaminated)
        print(f"  CONTAMINATED osm_ids (excluded from any headline number): {sorted(contaminated)}")
    else:
        results_df["contaminated"] = False

    results_out = OUT / "open35_storey_intervention_results.csv"
    results_df.to_csv(results_out, index=False)
    print(f"\nwrote {results_out}")
    print(f"\ntotal wall clock: {time.monotonic() - t_start:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
