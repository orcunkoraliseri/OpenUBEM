"""T04 of PLAN_four-board-items-2026-08-20.md -- OPEN-35 / board row C05: what the
single-storey fallback costs, measured with a within-building paired control.

Population: openubem/outputs/comparisons/open35_eui_consequence.csv (the register's own
evidence file for C05, all 8,160 fleet buildings with `neither` and on-record
`total_eui_kwh_m2`). Restricted here to the 8 cells the register names as containing BOTH
affected and unaffected buildings (austin_centre/suburban/urban/rural, la_centre/suburban/
urban, nyc_centre) -- nyc_suburban and nyc_rural are excluded because they have zero
unaffected buildings and cannot support a within-cell reading.

Two fallback sites (both file:line-cited, both read at HEAD 2026-08-20):
  * openubem/semantic/building_classifier.py:137-156  _impute_levels() -- archetype
    SELECTION stage. When both `levels` and `height_m` are missing (true for every
    candidate here, by the population's own definition -- `_impute_levels`'s HEURISTIC_HEIGHT
    branch, which divides height_m by floor-to-floor height, never fires for this
    population), it falls to `levels_group_median[use_class]`, then `levels_global_median`,
    then a flat `1` (LEVELS_DEFAULT_LOW).
  * openubem/geometry/footprint.py:58-90  derive_num_floors() -- geometry CONSTRUCTION
    stage. Pre-2026-08-19 this always fell flatly to `1`. As of the OPEN-35 T05/T06 Scope-B
    wiring fix (director ruling 4.4a) it is now GATED by `_archetype_consumed_group_median()`
    (footprint.py:91-95): for rows whose fired archetype rule actually consumed the group-
    median levels value (archetype_source carries a GROUPMEDIAN_LEVELS_MED token), geometry
    now ALSO builds at that same median -- i.e. production has partially self-healed a
    subset of the original 2,611/1,031 population since the register's citation. For rows
    where the token is absent, derive_num_floors still falls flatly to `1`, unconditionally,
    exactly as OPEN-35 originally described.

Consequence for sample selection (discovered by this script's own census, run before any
EnergyPlus compute -- see the selection table): a candidate is only usable for a clean paired
intervention if (a) _impute_levels() recovers a value > 1 (a genuine disagreement exists to
exploit) AND (b) _archetype_consumed_group_median(row) is False (today's production still
builds/parses the UNTREATED row at 1 floor, i.e. "base = as built today" is actually true).
Candidates where the wiring fix already applies are excluded -- treating them would build an
identical base/treated pair and trivially fail the storey-count-differs control.

Design (mirrors OPEN-56 / open35_storey_intervention_2026-08-19.py):
  base    = fresh BuildingIDF.build() on the row AS PERSISTED (levels/height still NaN ->
            derive_num_floors returns 1, verified per-building).
  treated = fresh BuildingIDF.build() on a COPY of the row with `levels` overridden to the
            value _impute_levels() recovers (the archetype-selection fallback). Nothing else
            changes.
  Both arms built and simulated in THIS session (no archived IDF/result is reused).
  EnergyPlus: run_ep_isolated, reused (imported, not reimplemented) from
            open35_storey_intervention_2026-08-19.py:82-98 -- gives every invocation its own
            cwd=outdir (OPEN-58's shared-cwd ExpandObjects contamination fix).
  EUI:      production openubem.results.parser.parse_building(), fed a manifest_row built the
            same way openubem/results/__init__.py:aggregate_results() builds one (osm_id,
            num_zones, data_quality_flag, resolution_mode, footprint_area_m2, levels,
            height_m, archetype_source, _use_class, _levels_group_median,
            _levels_global_median) -- NOT open56_zone_volume_experiment.py's hand-rolled
            "Total Site Energy" tabular read (OPEN-58's excludes-fans_eui_kwh_m2 defect).

Emits:
  openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_selection.csv
  openubem/outputs/comparisons/open35_storey_intervention_2026-08-20.csv
"""
from __future__ import annotations

import importlib.util
import os
import random
import shutil
import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "analysis"))

from openubem.semantic.building_classifier import (  # noqa: E402
    _INPUT_SCHEMA_COLUMNS, _normalise_use_class, _impute_levels, BuildingClassifier,
)
from openubem.geometry.footprint import _archetype_consumed_group_median  # noqa: E402
from openubem.idf.builder import BuildingIDF  # noqa: E402
from openubem.results.parser import parse_building  # noqa: E402

# -- reuse (not reimplement) the 2026-08-19 script's cell_context / run_ep_isolated /
# actual_num_floors_from_idf. The filename has dashes, so import by file path.
_spec = importlib.util.spec_from_file_location(
    "open35_t04_20260819", REPO / "scripts" / "analysis" / "open35_storey_intervention_2026-08-19.py"
)
_mod19 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod19)
cell_context = _mod19.cell_context
run_ep_isolated = _mod19.run_ep_isolated
actual_num_floors_from_idf = _mod19.actual_num_floors_from_idf

OUT = REPO / "openubem" / "outputs" / "comparisons"
POP_CSV = OUT / "open35_eui_consequence.csv"
WORK = Path(os.environ.get("TEMP", "C:/Temp")) / "open35_storey_intervention_2026-08-20"

TARGET_CELLS = [
    "austin_centre", "austin_suburban", "austin_urban", "austin_rural",
    "la_centre", "la_suburban", "la_urban", "nyc_centre",
]
NARROW_MIDHIGH = {"MidriseApartment", "HighriseApartment"}
WIDE_MIDHIGH = {"MidriseApartment", "HighriseApartment", "LargeOffice", "LargeHotel", "Hospital"}
N_PER_CELL = 3
SEED = 42
FLOOR_TO_FLOOR_M = 3.5


def tier_of(archetype_id: str) -> int:
    if archetype_id in NARROW_MIDHIGH:
        return 0
    if archetype_id in WIDE_MIDHIGH:
        return 1
    return 2


def census_and_select() -> tuple[pd.DataFrame, dict]:
    pop = pd.read_csv(POP_CSV)
    affected = pop[
        (pop["neither"] == True)  # noqa: E712
        & (pop["levels"] == 1.0)
        & (pop["cell"].isin(TARGET_CELLS))
    ].copy()
    print(f"affected (neither, persisted levels=1.0) in the 8 target cells: {len(affected)}")

    all_rows = []
    ctx_by_cell = {}
    rng = random.Random(SEED)

    for cell in TARGET_CELLS:
        osm_ids = affected.loc[affected["cell"] == cell, "osm_id"].tolist()
        print(f"\n=== {cell}: {len(osm_ids)} affected candidates, computing both fallback "
              f"candidates for each ===", flush=True)
        ctx = cell_context(cell)
        ctx_by_cell[cell] = ctx
        gdf_57 = ctx["gdf_57"]
        bc: BuildingClassifier = ctx["bc"]
        sub = gdf_57[gdf_57["osm_id"].isin(osm_ids)]
        for _, row in sub.iterrows():
            use_class, _score = _normalise_use_class(row)
            recovered_levels, lev_src = _impute_levels(
                row, floor_to_floor_m=FLOOR_TO_FLOOR_M, use_class=use_class,
                levels_group_median=ctx["levels_group_median"],
                levels_global_median=ctx["levels_global_median"],
            )
            consumed = _archetype_consumed_group_median(row)
            genuine = bool(recovered_levels > 1)
            eligible = bool(genuine and not consumed)
            on_record = pop.loc[pop["osm_id"] == row["osm_id"], "total_eui_kwh_m2"]
            all_rows.append({
                "cell": cell, "osm_id": row["osm_id"], "archetype_id": row["archetype_id"],
                "use_class": use_class,
                "base_storeys_geometry_fallback": 1,
                "treated_storeys_archetype_fallback": int(recovered_levels),
                "recovered_lev_src": lev_src,
                "archetype_consumed_group_median_today": consumed,
                "genuine_disagreement": genuine,
                "eligible_for_intervention": eligible,
                "tier": tier_of(row["archetype_id"]),
                "footprint_area_m2": float(row.get("footprint_area_m2", float("nan"))),
                "on_record_total_eui_kwh_m2": float(on_record.iloc[0]) if len(on_record) else float("nan"),
            })

    census_df = pd.DataFrame(all_rows)

    # -- selection: 3 per cell, eligible only, preferring lower tier (narrow midhigh first),
    # seeded shuffle within tier for a reproducible but non-cherry-picked draw.
    selected = []
    for cell in TARGET_CELLS:
        pool = census_df[(census_df["cell"] == cell) & census_df["eligible_for_intervention"]].copy()
        pool = pool.sort_values(["tier", "osm_id"]).reset_index(drop=True)
        # seeded shuffle within each tier, then take tiers in order until N_PER_CELL reached
        picks = []
        for t in sorted(pool["tier"].unique()):
            tier_ids = pool.loc[pool["tier"] == t, "osm_id"].tolist()
            tier_ids_sorted = sorted(tier_ids)
            rng.shuffle(tier_ids_sorted)
            picks.extend(tier_ids_sorted)
            if len(picks) >= N_PER_CELL:
                break
        picks = picks[:N_PER_CELL]
        chosen = pool[pool["osm_id"].isin(picks)]
        print(f"{cell}: eligible pool={len(pool)}, selected={len(chosen)}")
        selected.append(chosen)

    sel_df = pd.concat(selected, ignore_index=True) if selected else census_df.iloc[0:0]
    return sel_df, ctx_by_cell, census_df


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
        "treated_levels": int(lev),
        "footprint_area_m2": float(row.get("footprint_area_m2", float("nan"))),
        "base_generation_status": mf_base["generation_status"],
        "treat_generation_status": mf_treat["generation_status"],
        "base_num_zones": mf_base["num_zones"],
        "treat_num_zones": mf_treat["num_zones"],
        "base_idf_path": mf_base["idf_path"],
        "treat_idf_path": mf_treat["idf_path"],
        "base_data_quality_flag": mf_base["data_quality_flag"],
        "treat_data_quality_flag": mf_treat["data_quality_flag"],
        "base_resolution_mode": mf_base["resolution_mode"],
        "treat_resolution_mode": mf_treat["resolution_mode"],
        "epw_path": str(ctx["epw_path"]),
        "row_base": row_base, "row_treat": row_treat,
    }
    if rec["base_generation_status"] not in ("success", "fallback_bbox") or \
       rec["treat_generation_status"] not in ("success", "fallback_bbox"):
        rec["prep_status"] = "idf_generation_failed"
        return rec

    base_floors = actual_num_floors_from_idf(Path(mf_base["idf_path"]))
    treat_floors = actual_num_floors_from_idf(Path(mf_treat["idf_path"]))
    rec["base_num_floors_from_idf"] = round(base_floors, 3)
    rec["treat_num_floors_from_idf"] = round(treat_floors, 3)
    rec["floor_count_control_pass"] = (round(base_floors) == 1 and round(treat_floors) == int(lev))
    rec["prep_status"] = "ok" if rec["floor_count_control_pass"] else "floor_count_control_FAILED"
    return rec


def manifest_row_for(row: pd.Series, mf: dict, ctx: dict) -> pd.Series:
    m = row.copy()
    m["num_zones"] = mf["num_zones"]
    m["data_quality_flag"] = mf["data_quality_flag"]
    m["resolution_mode"] = mf["resolution_mode"]
    m["_use_class"] = _normalise_use_class(row)[0]
    m["_levels_group_median"] = ctx["levels_group_median"]
    m["_levels_global_median"] = ctx["levels_global_median"]
    return m


def main() -> int:
    t0 = time.monotonic()
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)

    sel_df, ctx_by_cell, census_df = census_and_select()

    census_out = OUT / "open35_storey_intervention_2026-08-20_census.csv"
    census_df.to_csv(census_out, index=False)
    print(f"\nwrote {census_out} ({len(census_df)} rows)")

    sel_out = OUT / "open35_storey_intervention_2026-08-20_selection.csv"
    sel_df.to_csv(sel_out, index=False)
    print(f"wrote {sel_out} ({len(sel_df)} rows)")

    print(f"\nSELECTED {len(sel_df)} buildings:")
    print(sel_df[["cell", "osm_id", "archetype_id", "tier", "base_storeys_geometry_fallback",
                   "treated_storeys_archetype_fallback", "recovered_lev_src"]].to_string())

    if len(sel_df) != 24:
        print(f"\n!!! SELECTION DID NOT REACH 24 (got {len(sel_df)}) -- STOP before building/"
              f"simulating.", flush=True)
        return 1

    print(f"\ncensus+selection wall clock: {time.monotonic()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
