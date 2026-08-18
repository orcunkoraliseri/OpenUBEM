"""T03 -- OPEN-08 vintage half: cross-generation vintage disagreement for data-poor buildings.

Plan: docs/docs_ACTIVE/openings/implemenation/PLAN_open-52-and-four-items-2026-08-18.md, T03.

Step 1 (hard gate): re-derive OPEN-30's own numbers directly from the 60 E02
03_manifest.parquet files (40,800 rows, 0 nulls, 5 distinct vintage_standard
values, DOERefPre1980 ~=93.44%). If this does not reproduce, everything below
is void.

Step 2: reproduce MEASUREMENT_open-28_harvest-generation-join.md's own T08 vs
T20 join exactly (same reproduction command, same files) to get the 4,530-row
shared population and its 13.40% archetype disagreement figure -- re-used, not
re-invented.

Step 3: vintage comparison on that same 4,530-row population. Neither T08's nor
T20's own provenance chain (docs/docs_VALIDATION/validations/overAll/results/
phaseE/<cell>/05_results.gpkg) carries vintage_standard at all (established in
MEASUREMENT_open-28, section 4) -- so a "prior generation" vintage source has to
come from elsewhere. The chosen "prior" source is
docs/docs_VALIDATION/validations/overAll/results/cases/<cell>/05_results.gpkg,
which MEASUREMENT_open-28 itself notes was "last touched by commit e063865
(T08's own pre-state commit, coincidentally)" -- i.e. it reflects the same code
state T08's archetype figures came from, which is the closest available "prior
generation" vintage source to T08 itself. This is NOT a claim that this file is
T08's own vintage (T08 has none) -- it is an independently-provenanced,
genuinely-earlier vintage assignment for the same buildings, used only to
measure generational drift against E02 (2026-08-09), never mixed with the T08 or
T20 harvest CSVs themselves.

The "current" source is the E02 manifest (2026-08-09), read directly, mode
'auto' (vintage and archetype are checked as mode-invariant within E02 below,
per OPEN-30's own finding).

Data-poor flag: provenance_levels == 'OSM_MISSING' OR provenance_height_m ==
'OSM_MISSING' OR provenance_year_built == 'OSM_MISSING', read from the same
cases-path gpkg (only source with these provenance columns).
"""

import csv
from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO_ROOT = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
FLEET_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_fleet")
CASES_ROOT = REPO_ROOT / "docs/docs_VALIDATION/validations/overAll/results/cases"

T08_CSV = REPO_ROOT / "openubem/outputs/comparisons/t08_all_modes_eui.csv"
T20_CSV = REPO_ROOT / "openubem/outputs/comparisons/t20_layout_assign_eui.csv"

OUT_DIR = REPO_ROOT / "openubem/outputs/comparisons"
OUT_CSV = OUT_DIR / "open08_vintage_reproducibility.csv"

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
MODES = ["auto", "building", "floor", "fast_zone", "layout_assign"]

T08_CELLS = ["la_centre", "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban"]


def step1_gate():
    print("=== STEP 1 -- HARD GATE: re-derive OPEN-30's own numbers ===")
    frames = []
    n_manifests_read = 0
    for cell in CELLS:
        for mode in MODES:
            mp = FLEET_ROOT / cell / f"step3_{mode}" / "03_manifest.parquet"
            if not mp.exists():
                print(f"MISSING manifest: {mp}")
                continue
            df = pd.read_parquet(mp, columns=["osm_id", "vintage_standard", "archetype_id"])
            df["_cell"] = cell
            df["_mode"] = mode
            frames.append(df)
            n_manifests_read += 1

    all_df = pd.concat(frames, ignore_index=True)
    n_rows = len(all_df)
    n_nulls = all_df["vintage_standard"].isna().sum()
    vc = all_df["vintage_standard"].value_counts()
    n_distinct = vc.shape[0]
    pre1980_pct = round(100.0 * vc.get("DOERefPre1980", 0) / n_rows, 4)

    print(f"manifests read: {n_manifests_read} / 60")
    print(f"fleet-wide rows: {n_rows} (expected 40,800)")
    print(f"nulls in vintage_standard: {n_nulls} (expected 0)")
    print(f"distinct vintage_standard values: {n_distinct} (expected 5)")
    print(f"value counts:\n{vc}")
    print(f"DOERefPre1980 share: {pre1980_pct}% (expected ~=93.44%)")

    ok = (
        n_manifests_read == 60
        and n_rows == 40800
        and n_nulls == 0
        and n_distinct == 5
        and abs(pre1980_pct - 93.44) < 0.05
    )
    print(f"GATE {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit("STEP 1 GATE FAILED -- premise not reproduced, stopping.")
    return all_df


def step1b_mode_invariance(all_df):
    print("\n=== STEP 1b -- vintage/archetype mode-invariance check (within E02) ===")
    pivot_v = all_df.pivot_table(index=["_cell", "osm_id"], columns="_mode",
                                  values="vintage_standard", aggfunc="first")
    pivot_a = all_df.pivot_table(index=["_cell", "osm_id"], columns="_mode",
                                  values="archetype_id", aggfunc="first")
    n_v_varies = (pivot_v.nunique(axis=1) > 1).sum()
    n_a_varies = (pivot_a.nunique(axis=1) > 1).sum()
    print(f"buildings where vintage_standard varies across the 5 E02 modes: {n_v_varies} / {len(pivot_v)}")
    print(f"buildings where archetype_id varies across the 5 E02 modes: {n_a_varies} / {len(pivot_a)}")


def step2_reproduce_open28_join():
    print("\n=== STEP 2 -- reproduce MEASUREMENT_open-28's own T08 vs T20 join ===")
    t08 = pd.read_csv(T08_CSV).drop_duplicates("osm_id")
    t20 = pd.read_csv(T20_CSV)
    merged = t08.merge(t20, on="osm_id", how="outer", indicator=True,
                        suffixes=("_t08", "_t20"))
    both = merged[merged["_merge"] == "both"].copy()
    n_both = len(both)
    n_t08_only = (merged["_merge"] == "left_only").sum()
    n_t20_only = (merged["_merge"] == "right_only").sum()
    print(f"rows_in_both: {n_both} (expected 4,530)")
    print(f"t08_only: {n_t08_only} (expected 0)")
    print(f"t20_only: {n_t20_only} (expected 3,630)")

    n_agree = (both["archetype_id_t08"] == both["archetype_id_t20"]).sum()
    n_disagree = n_both - n_agree
    disagree_pct = round(100.0 * n_disagree / n_both, 4)
    print(f"archetype agree: {n_agree} ({round(100.0*n_agree/n_both,4)}%)")
    print(f"archetype disagree: {n_disagree} ({disagree_pct}%)  (expected 13.40%)")

    ok = n_both == 4530 and n_t08_only == 0 and n_t20_only == 3630 and abs(disagree_pct - 13.40) < 0.01
    print(f"OPEN-28 REPRODUCTION {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit("STEP 2 FAILED to reproduce OPEN-28's own join -- stopping.")

    both = both.rename(columns={"cell_t08": "cell"})
    return both[["osm_id", "cell", "archetype_id_t08", "archetype_id_t20"]].copy(), disagree_pct


def step3a_schema_check():
    print("\n=== STEP 3a -- does the candidate 'prior generation' vintage source cover the "
          "T08 population? (schema check, all 5 T08 cells) ===")
    need = {"osm_id", "vintage_standard", "archetype_id", "levels", "height_m", "year_built",
            "provenance_levels", "provenance_height_m", "provenance_year_built"}
    cells_with_vintage = []
    for cell in T08_CELLS:
        p = CASES_ROOT / cell / "05_results.gpkg"
        gdf = gpd.read_file(str(p), rows=1)
        missing = need - set(gdf.columns)
        has_vintage = "vintage_standard" not in missing
        print(f"  {cell}: ncols={len(gdf.columns)}  missing={sorted(missing) if missing else '(none)'}"
              f"  has_vintage_standard={has_vintage}")
        if has_vintage:
            cells_with_vintage.append(cell)
    print(f"cells with a usable prior-generation vintage_standard: {cells_with_vintage} "
          f"({len(cells_with_vintage)} / {len(T08_CELLS)})")
    return cells_with_vintage


def step3_vintage(shared_osm_ids_df, prior_cells):
    print(f"\n=== STEP 3 -- vintage comparison, restricted to {prior_cells} "
          f"(only cells where a prior-generation vintage source exists) ===")

    prior_frames = []
    for cell in prior_cells:
        p = CASES_ROOT / cell / "05_results.gpkg"
        gdf = gpd.read_file(str(p))
        cols = ["osm_id", "vintage_standard", "archetype_id", "levels", "height_m", "year_built",
                "provenance_levels", "provenance_height_m", "provenance_year_built"]
        prior_frames.append(gdf[cols])
    prior = pd.concat(prior_frames, ignore_index=True)
    prior = prior.rename(columns={
        "vintage_standard": "vintage_prior", "archetype_id": "archetype_prior",
    })
    n_prior_dupes = prior["osm_id"].duplicated().sum()
    print(f"prior (cases-path, {prior_cells}) rows: {len(prior)}, duplicate osm_id: {n_prior_dupes}")

    current_frames = []
    for cell in prior_cells:
        mp = FLEET_ROOT / cell / "step3_auto" / "03_manifest.parquet"
        df = pd.read_parquet(mp, columns=["osm_id", "vintage_standard", "archetype_id"])
        current_frames.append(df)
    current = pd.concat(current_frames, ignore_index=True)
    current = current.rename(columns={
        "vintage_standard": "vintage_current", "archetype_id": "archetype_current",
    })
    n_current_dupes = current["osm_id"].duplicated().sum()
    print(f"current (E02 auto, {prior_cells}) rows: {len(current)}, duplicate osm_id: {n_current_dupes}")

    shared_ids = shared_osm_ids_df[shared_osm_ids_df["cell"].isin(prior_cells)][["osm_id"]].drop_duplicates()
    print(f"shared T08/T20 population restricted to {prior_cells}: {len(shared_ids)} rows")
    merged = shared_ids.merge(prior, on="osm_id", how="left", indicator="in_prior")
    merged = merged.merge(current, on="osm_id", how="left", indicator="in_current")

    n_total = len(merged)
    n_missing_prior = (merged["in_prior"] == "left_only").sum()
    n_missing_current = (merged["in_current"] == "left_only").sum()
    print(f"shared population (from step 2): {n_total}")
    print(f"of these, missing from prior (cases-path) source: {n_missing_prior}")
    print(f"of these, missing from current (E02 auto) source: {n_missing_current}")

    complete = merged[(merged["in_prior"] == "both") & (merged["in_current"] == "both")].copy()
    n_complete = len(complete)
    print(f"complete rows (present in both prior and current): {n_complete}")

    complete["vintage_agree"] = complete["vintage_prior"] == complete["vintage_current"]
    n_v_agree = complete["vintage_agree"].sum()
    n_v_disagree = n_complete - n_v_agree
    v_disagree_pct = round(100.0 * n_v_disagree / n_complete, 4)
    print(f"vintage agree: {n_v_agree} ({round(100.0*n_v_agree/n_complete,4)}%)")
    print(f"vintage disagree: {n_v_disagree} ({v_disagree_pct}%)")

    complete["archetype_agree"] = complete["archetype_prior"] == complete["archetype_current"]
    n_a_agree = complete["archetype_agree"].sum()
    n_a_disagree = n_complete - n_a_agree
    a_disagree_pct = round(100.0 * n_a_disagree / n_complete, 4)
    print(f"[context only, NOT the reused 13.40%] cases-vs-E02 archetype disagree: "
          f"{n_a_disagree} ({a_disagree_pct}%)")

    complete["data_poor"] = (
        (complete["provenance_levels"] == "OSM_MISSING")
        | (complete["provenance_height_m"] == "OSM_MISSING")
        | (complete["provenance_year_built"] == "OSM_MISSING")
    )
    n_data_poor = complete["data_poor"].sum()
    print(f"\ndata-poor buildings (missing levels, height_m, or year_built): "
          f"{n_data_poor} / {n_complete} ({round(100.0*n_data_poor/n_complete,4)}%)")

    for label, sub in [("data-poor", complete[complete["data_poor"]]),
                        ("data-rich (not data-poor)", complete[~complete["data_poor"]])]:
        n = len(sub)
        n_dis = (~sub["vintage_agree"]).sum()
        pct = round(100.0 * n_dis / n, 4) if n else float("nan")
        print(f"  {label}: n={n}, vintage disagree={n_dis} ({pct}%)")

    print("\n=== Non-vacuity control ===")
    print(f"shared-population count (complete rows): {n_complete}")
    print(f"vintage: some agree ({n_v_agree}) and some disagree ({n_v_disagree})? "
          f"{'YES' if n_v_agree > 0 and n_v_disagree > 0 else 'NO -- DEGENERATE'}")
    print(f"archetype (context check): some agree ({n_a_agree}) and some disagree ({n_a_disagree})? "
          f"{'YES' if n_a_agree > 0 and n_a_disagree > 0 else 'NO -- DEGENERATE'}")

    complete.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {OUT_CSV} ({len(complete)} rows)")

    return complete, v_disagree_pct, n_data_poor, n_complete


def main():
    all_df = step1_gate()
    step1b_mode_invariance(all_df)
    shared, archetype_disagree_pct = step2_reproduce_open28_join()
    prior_cells = step3a_schema_check()
    complete, vintage_disagree_pct, n_data_poor, n_complete = step3_vintage(shared, prior_cells)

    print("\n=== SUMMARY ===")
    print(f"archetype disagreement (reused OPEN-28 figure, 4,530 shared T08/T20 rows): "
          f"{archetype_disagree_pct}%")
    print(f"vintage disagreement (same population, restricted to {n_complete} rows with "
          f"both prior and current vintage available): {vintage_disagree_pct}%")
    print(f"data-poor share of that population: {n_data_poor}/{n_complete}")


if __name__ == "__main__":
    main()
