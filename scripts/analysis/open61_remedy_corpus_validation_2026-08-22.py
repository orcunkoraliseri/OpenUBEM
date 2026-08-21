"""T02 of PLAN_open61-dh-remedy-2026-08-22.md -- prove T01 (the ABUPS-district-heating
fold into dhw_eui_kwh_m2 / total_eui_kwh_m2) against the preserved corpus.

No re-simulation. F8: 7,861 eplusout.sql, 121.9 GB, 12 cells, already on disk at
C:/Users/o_iseri/OpenUBEM_corpora/open61_census_2026-08-20, READ-ONLY under ruling R6.
Every sqlite read in this script -- and every one inside openubem.results.parser's own
functions that this script calls -- opens with `mode=ro`.

Method: draw a stratified sample of 200 osm_ids from the census population
(openubem/outputs/comparisons/open61_census_fleet.csv, status == "ok") restricted to
osm_ids that actually have a preserved .sql (F8's 96.4% overlap), proportional across the
12 cells, with an exact 20 forced from {SuperTallBuilding, TallBuilding} so the high-DH
class is represented (>= 20, per the plan). For each sampled building: reconstruct the
manifest_row parse_building() needs (num_zones, data_quality_flag, resolution_mode) the
SAME way openscripts/analysis/open61_census_build_2026-08-20.py did -- a fresh
BuildingIDF(...).build() call on the SAME frozen, cached step1/step2 inputs used to build
the corpus (deterministic; no EnergyPlus run, no write into the corpus) -- then call the
production openubem.results.parser.parse_building() over the EXISTING preserved .sql.

Reuses (does not reimplement):
  * cell_context() from open35_storey_intervention_2026-08-19.py -- cached step1 + fresh
    step2 pipeline context (frozen gpkg + cached EPW; no network).
  * manifest_row_for() / BuildingIDF(...).build() pattern from
    open61_census_build_2026-08-20.py (process_building()) -- IDENTICAL construction,
    minus the run_ep_isolated() call (F8: no re-simulation needed).
  * openubem.results.parser.parse_building() -- the fixed production route (T01).

Pre-registered pass conditions (plan T02 "How to test"), reported without adjustment:
  C1 -- >= 198/200 agree within 0.5% relative (or within 1 kWh absolute when
        dh_total_kwh < 1,000), comparing dhw_district_eui_kwh_m2 x parsed_floor_area_m2
        (this run) against dh_total_kwh (census CSV, T01's standalone reader).
  C2 -- every sampled building with dh_total_kwh == 0 (census CSV) reads
        dhw_district_eui_kwh_m2 == 0.0 exactly (this run).
  C3 -- total_eui_kwh_m2 (this run) == parsed_total_eui_kwh_m2 (census CSV) +
        dh_total_kwh / parsed_floor_area_m2 (census CSV), within 0.01 kWh/m2, on >= 198/200.

Emits: openubem/outputs/comparisons/open61_remedy_validation_2026-08-22.csv (one row per
sampled building). Scratch IDF output goes to the session scratchpad, never into the
corpus and never under docs/.
"""
from __future__ import annotations

import importlib.util
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "analysis"))

from openubem.idf.builder import BuildingIDF  # noqa: E402
from openubem.results.parser import parse_building  # noqa: E402
from openubem.semantic.building_classifier import _normalise_use_class  # noqa: E402

_spec19 = importlib.util.spec_from_file_location(
    "open35_t04_20260819_for_open61_t02",
    REPO / "scripts" / "analysis" / "open35_storey_intervention_2026-08-19.py",
)
_mod19 = importlib.util.module_from_spec(_spec19)
sys.modules[_spec19.name] = _mod19
_spec19.loader.exec_module(_mod19)
cell_context = _mod19.cell_context

CENSUS_CSV = REPO / "openubem" / "outputs" / "comparisons" / "open61_census_fleet.csv"
CORPUS = Path(r"C:\Users\o_iseri\OpenUBEM_corpora\open61_census_2026-08-20")
OUT_CSV = REPO / "openubem" / "outputs" / "comparisons" / "open61_remedy_validation_2026-08-22.csv"
SCRATCHPAD = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM"
    r"\ec98c284-d1f5-4cae-880a-8199d683efb6\scratchpad"
)
WORK = SCRATCHPAD / "open61_t02_work"

CELLS = ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
         "la_centre", "la_urban", "la_suburban", "la_rural",
         "austin_centre", "austin_urban", "austin_suburban", "austin_rural"]

TALL_ARCHETYPES = {"SuperTallBuilding", "TallBuilding"}
SEED = 42
N_TARGET = 200
N_TALL_FORCED = 20
C1_REL_TOL = 0.005
C1_ABS_TOL_KWH = 1.0
C1_ABS_THRESHOLD_KWH = 1000.0
C3_TOL_KWH_M2 = 0.01


def _safe_id(osm_id: str) -> str:
    return osm_id.replace("/", "_").replace(":", "_")


def _sql_path(cell: str, osm_id: str) -> Path:
    return CORPUS / cell / _safe_id(osm_id) / "sim_out" / "eplusout.sql"


def _largest_remainder(weights: pd.Series, total: int) -> pd.Series:
    """Proportional integer allocation of `total` across weights' index, summing exactly."""
    if weights.sum() == 0:
        return pd.Series(0, index=weights.index)
    raw = weights / weights.sum() * total
    floors = np.floor(raw).astype(int)
    remainder = total - floors.sum()
    fractional = (raw - floors).sort_values(ascending=False)
    bump_idx = fractional.index[:remainder]
    floors.loc[bump_idx] += 1
    return floors


def load_population() -> pd.DataFrame:
    census = pd.read_csv(CENSUS_CSV)
    ok = census[census["status"] == "ok"].copy()
    ok["_sql_path"] = ok.apply(lambda r: _sql_path(r["cell"], r["osm_id"]), axis=1)
    ok["_in_corpus"] = ok["_sql_path"].apply(lambda p: p.exists())
    pop = ok[ok["_in_corpus"]].copy()
    return pop


def stratified_select(pop: pd.DataFrame, rng: np.random.RandomState) -> pd.DataFrame:
    tall = pop[pop["archetype_id"].isin(TALL_ARCHETYPES)]
    rest_full = pop

    tall_by_cell = tall.groupby("cell").size()
    tall_quota = _largest_remainder(tall_by_cell, N_TALL_FORCED)
    tall_quota = tall_quota.reindex(tall_by_cell.index).fillna(0).astype(int)
    tall_quota = tall_quota.clip(upper=tall_by_cell)

    picked_frames = []
    for cell, n in tall_quota.items():
        if n <= 0:
            continue
        pool = tall[tall["cell"] == cell]
        picked_frames.append(pool.sample(n=int(n), random_state=rng.randint(0, 2**31 - 1)))
    tall_picked = pd.concat(picked_frames, axis=0) if picked_frames else pop.iloc[0:0]
    n_tall_picked = len(tall_picked)
    if n_tall_picked < N_TALL_FORCED:
        shortfall = N_TALL_FORCED - n_tall_picked
        remaining_tall = tall.drop(index=tall_picked.index)
        extra = remaining_tall.sample(
            n=min(shortfall, len(remaining_tall)), random_state=rng.randint(0, 2**31 - 1)
        )
        tall_picked = pd.concat([tall_picked, extra], axis=0)

    n_rest = N_TARGET - len(tall_picked)
    rest_pool = rest_full.drop(index=tall_picked.index)
    cell_counts = rest_pool.groupby("cell").size()
    rest_quota = _largest_remainder(cell_counts, n_rest)
    rest_quota = rest_quota.reindex(cell_counts.index).fillna(0).astype(int)
    rest_quota = rest_quota.clip(upper=cell_counts)
    deficit = n_rest - rest_quota.sum()
    if deficit > 0:
        headroom = (cell_counts - rest_quota).sort_values(ascending=False)
        for cell in headroom.index:
            if deficit <= 0:
                break
            add = min(deficit, int(headroom[cell]))
            rest_quota[cell] += add
            deficit -= add

    rest_frames = []
    for cell, n in rest_quota.items():
        if n <= 0:
            continue
        pool = rest_pool[rest_pool["cell"] == cell]
        rest_frames.append(pool.sample(n=int(n), random_state=rng.randint(0, 2**31 - 1)))
    rest_picked = pd.concat(rest_frames, axis=0) if rest_frames else pop.iloc[0:0]

    sel = pd.concat([tall_picked, rest_picked], axis=0)
    assert sel["osm_id"].duplicated().sum() == 0, "duplicate osm_id in selection"
    assert len(sel) == N_TARGET, f"selection drifted: {len(sel)} != {N_TARGET}"
    n_tall_final = sel["archetype_id"].isin(TALL_ARCHETYPES).sum()
    assert n_tall_final >= N_TALL_FORCED, f"tall class under target: {n_tall_final} < {N_TALL_FORCED}"
    return sel.reset_index(drop=True)


def manifest_row_for(row: pd.Series, mf: dict) -> pd.Series:
    """Verbatim copy of open61_census_build_2026-08-20.py:227-233."""
    m = row.copy()
    m["num_zones"] = mf["num_zones"]
    m["data_quality_flag"] = mf["data_quality_flag"]
    m["resolution_mode"] = mf["resolution_mode"]
    m["_use_class"] = _normalise_use_class(row)[0]
    return m


def main() -> int:
    t_start = time.monotonic()
    pop = load_population()
    print(f"population (status=='ok', preserved .sql present): {len(pop)} of "
          f"{pd.read_csv(CENSUS_CSV)['status'].eq('ok').sum()} ok census rows", flush=True)

    rng = np.random.RandomState(SEED)
    sel = stratified_select(pop, rng)
    print(f"selected {len(sel)}, tall class = "
          f"{sel['archetype_id'].isin(TALL_ARCHETYPES).sum()}", flush=True)
    print(sel.groupby("cell").size().to_string(), flush=True)

    if WORK.exists():
        import shutil
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)

    cells_needed = sorted(sel["cell"].unique())
    ctx_by_cell = {}
    for cell in cells_needed:
        ctx_by_cell[cell] = cell_context(cell)

    rows_out = []
    for i, (_, rec) in enumerate(sel.iterrows()):
        osm_id, cell = rec["osm_id"], rec["cell"]
        out = {
            "cell": cell, "osm_id": osm_id, "archetype_id": rec["archetype_id"],
            "census_dh_total_kwh": rec["dh_total_kwh"],
            "census_parsed_floor_area_m2": rec["parsed_floor_area_m2"],
            "census_parsed_total_eui_kwh_m2": rec["parsed_total_eui_kwh_m2"],
        }
        ctx = ctx_by_cell[cell]
        gdf_57 = ctx["gdf_57"]
        match = gdf_57[gdf_57["osm_id"] == osm_id]
        if len(match) != 1:
            out["status"] = f"row_lookup_failed_n={len(match)}"
            rows_out.append(out)
            continue
        row = match.iloc[0]

        work_dir = WORK / cell / _safe_id(osm_id)
        (work_dir / "idfs").mkdir(parents=True, exist_ok=True)
        try:
            mf = BuildingIDF(row, resolution_mode="auto").build(
                gdf_57, ctx["schedule_library"], work_dir
            )
        except Exception as exc:  # noqa: BLE001
            out["status"] = f"idf_build_exception:{exc}"[:200]
            rows_out.append(out)
            continue
        out["generation_status"] = mf.get("generation_status")
        if mf.get("generation_status") not in ("success", "fallback_bbox"):
            out["status"] = "idf_generation_failed"
            rows_out.append(out)
            continue

        manifest_row = manifest_row_for(row, mf)
        sql_path = _sql_path(cell, osm_id)
        metrics = parse_building(sql_path, None, manifest_row)
        out["parse_status"] = metrics.get("parse_status")
        out["new_floor_area_m2"] = metrics.get("floor_area_m2")
        out["new_dhw_district_eui_kwh_m2"] = metrics.get("dhw_district_eui_kwh_m2")
        out["new_total_eui_kwh_m2"] = metrics.get("total_eui_kwh_m2")

        if out["new_dhw_district_eui_kwh_m2"] is None or pd.isna(out["new_dhw_district_eui_kwh_m2"]):
            out["status"] = "failed_parse"
            rows_out.append(out)
            continue

        new_dh_kwh = out["new_dhw_district_eui_kwh_m2"] * rec["parsed_floor_area_m2"]
        out["new_dh_kwh_at_census_area"] = new_dh_kwh
        census_dh = rec["dh_total_kwh"]

        # C1
        if pd.isna(census_dh):
            out["c1_pass"] = None
        else:
            diff = abs(new_dh_kwh - census_dh)
            out["c1_diff_kwh"] = diff
            if census_dh < C1_ABS_THRESHOLD_KWH:
                out["c1_pass"] = diff <= C1_ABS_TOL_KWH
            else:
                out["c1_pass"] = (diff / census_dh) <= C1_REL_TOL if census_dh != 0 else diff <= C1_ABS_TOL_KWH

        # C2
        if pd.isna(census_dh):
            out["c2_pass"] = None
        elif census_dh == 0:
            out["c2_pass"] = out["new_dhw_district_eui_kwh_m2"] == 0.0
        else:
            out["c2_pass"] = None  # not applicable

        # C3
        if pd.isna(rec["parsed_total_eui_kwh_m2"]) or pd.isna(census_dh) or pd.isna(rec["parsed_floor_area_m2"]):
            out["c3_pass"] = None
        else:
            expected_total = rec["parsed_total_eui_kwh_m2"] + census_dh / rec["parsed_floor_area_m2"]
            c3_diff = abs(out["new_total_eui_kwh_m2"] - expected_total)
            out["c3_expected_total_eui_kwh_m2"] = expected_total
            out["c3_diff_kwh_m2"] = c3_diff
            out["c3_pass"] = c3_diff <= C3_TOL_KWH_M2

        out["status"] = "ok"
        rows_out.append(out)

        if (i + 1) % 25 == 0:
            print(f"  [{i + 1}/{len(sel)}] done", flush=True)

    df_out = pd.DataFrame(rows_out)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV} ({len(df_out)} rows)", flush=True)

    n = len(df_out)
    c1_evaluated = df_out["c1_pass"].notna().sum() if "c1_pass" in df_out else 0
    c1_pass_n = int(df_out["c1_pass"].sum()) if "c1_pass" in df_out else 0
    c2_evaluated = df_out["c2_pass"].notna().sum() if "c2_pass" in df_out else 0
    c2_pass_n = int(df_out["c2_pass"].sum()) if "c2_pass" in df_out else 0
    c3_evaluated = df_out["c3_pass"].notna().sum() if "c3_pass" in df_out else 0
    c3_pass_n = int(df_out["c3_pass"].sum()) if "c3_pass" in df_out else 0

    print(f"\nn sampled = {n}", flush=True)
    print(f"C1: {c1_pass_n}/{n} pass (evaluated on {c1_evaluated}); "
          f"threshold >= 198/200", flush=True)
    print(f"C2: {c2_pass_n}/{c2_evaluated} pass (zero-dh subset only)", flush=True)
    print(f"C3: {c3_pass_n}/{n} pass (evaluated on {c3_evaluated}); "
          f"threshold >= 198/200", flush=True)

    if "c1_pass" in df_out:
        c1_fail = df_out[df_out["c1_pass"] == False]  # noqa: E712
        if len(c1_fail):
            print("\nC1 failures (osm_id, cell, new_dh_kwh_at_census_area, census_dh_total_kwh):", flush=True)
            for _, r in c1_fail.iterrows():
                print(f"  {r['osm_id']}, {r['cell']}, {r.get('new_dh_kwh_at_census_area')}, "
                      f"{r.get('census_dh_total_kwh')}", flush=True)
    if "c2_pass" in df_out:
        c2_fail = df_out[df_out["c2_pass"] == False]  # noqa: E712
        if len(c2_fail):
            print("\nC2 failures (osm_id, cell, new_dhw_district_eui_kwh_m2, census_dh_total_kwh):", flush=True)
            for _, r in c2_fail.iterrows():
                print(f"  {r['osm_id']}, {r['cell']}, {r.get('new_dhw_district_eui_kwh_m2')}, "
                      f"{r.get('census_dh_total_kwh')}", flush=True)
    if "c3_pass" in df_out:
        c3_fail = df_out[df_out["c3_pass"] == False]  # noqa: E712
        if len(c3_fail):
            print("\nC3 failures (osm_id, cell, new_total_eui_kwh_m2, c3_expected_total_eui_kwh_m2):", flush=True)
            for _, r in c3_fail.iterrows():
                print(f"  {r['osm_id']}, {r['cell']}, {r.get('new_total_eui_kwh_m2')}, "
                      f"{r.get('c3_expected_total_eui_kwh_m2')}", flush=True)

    non_ok = df_out[df_out["status"] != "ok"]
    if len(non_ok):
        print(f"\n{len(non_ok)} buildings did not reach status=='ok':", flush=True)
        print(non_ok[["osm_id", "cell", "status"]].to_string(), flush=True)

    print(f"\ntotal wall clock: {time.monotonic() - t_start:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
