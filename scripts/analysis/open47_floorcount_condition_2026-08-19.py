"""OPEN-47 T03 (PLAN_board-17-ready-2026-08-19.md): size the floor-count divergence again,
independently, and answer two questions the 2026-08-18 measurement
(scripts/analysis/open47_floorcount_divergence.py) did not: how many of the changed buildings
have NO floor count at all (can never satisfy an AND rule), and what the overlap is with
OPEN-35's 11-building census (open35_storey_intervention_results_v2.csv).

Per plan section 4.6 ("independent re-derivation, not re-reading") this recomputes the
divergence from the raw per-building attributes (phaseE's 01_buildings.gpkg, cross-checked
against phaseE_elevrb's adopted 05_results.csv) rather than reading the existing
open47_floorcount_divergence.csv. Method is the same as that script and its predecessor
open47_floorcount_reclass.py, because the fact under test -- "does the fixed input reproduce
under the fixed method" -- is unchanged; only the two new cross-cuts are new code.

No re-classification run, no simulation, no fleet re-run, no file changed under openubem/.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.semantic.building_classifier import (
    BuildingClassifier,
    _INPUT_SCHEMA_COLUMNS,
    _impute_levels,
    _normalise_use_class,
)

ROOT = Path(__file__).resolve().parent.parent.parent
PHASEE = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
PHASEE_ELEVRB = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE_elevrb"
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
ELEVATORS_BY_ARCHETYPE_PATH = ROOT / "openubem" / "data" / "loads" / "elevators_by_archetype.json"
OPEN35_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open35_storey_intervention_results_v2.csv"
OUT_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open47_floorcount_condition.csv"

_OFFICE_TIER_HEADS = {"RULE_USE_CLASS_SIZE", "FALLBACK_SIZE_DEFAULT"}
_NO_FLOOR_COUNT_SOURCES = {"GROUPMEDIAN_LEVELS_MED", "LEVELS_DEFAULT_LOW"}

_CONTROL_CASES = {
    "way/99259744": ("SmallOffice", "MediumOffice"),
    "way/379165919": ("MediumOffice", "LargeOffice"),
    "way/379166276": ("SmallOffice", "LargeOffice"),
}


def load_cell(cell: str) -> pd.DataFrame:
    gdf = gpd.read_file(PHASEE / cell / "01_buildings.gpkg")
    gdf = gdf[_INPUT_SCHEMA_COLUMNS].copy()
    gdf["levels"] = gdf["levels"].astype("Int64")

    off = BuildingClassifier(use_floor_count=False).classify(gdf.copy())
    on = BuildingClassifier(use_floor_count=True).classify(gdf.copy())

    clf = BuildingClassifier()
    levels_group_median, levels_global_median = clf._build_levels_median_lookup(gdf)
    use_class = gdf.apply(lambda r: _normalise_use_class(r)[0], axis=1)
    levels_imputed_pair = gdf.apply(
        lambda r: _impute_levels(
            r,
            use_class=use_class.loc[r.name],
            levels_group_median=levels_group_median,
            levels_global_median=levels_global_median,
        ),
        axis=1,
        result_type="expand",
    )
    imputed = pd.DataFrame({
        "osm_id": gdf["osm_id"],
        "levels_imputed": levels_imputed_pair[0],
        "levels_source": levels_imputed_pair[1],
        "levels_raw_observed": gdf["levels"].notna().values,
        "height_m_raw": gdf["height_m"].values,
    })

    adopted = pd.read_csv(PHASEE_ELEVRB / cell / "05_results.csv")[
        ["osm_id", "footprint_area_m2", "archetype_id"]
    ].rename(columns={"archetype_id": "archetype_adopted"})

    merged = off[["osm_id", "footprint_area_m2", "archetype_id", "archetype_source"]].rename(
        columns={"archetype_id": "archetype_off"}
    ).merge(
        on[["osm_id", "archetype_id"]].rename(columns={"archetype_id": "archetype_on"}),
        on="osm_id",
    ).merge(imputed, on="osm_id").merge(adopted, on="osm_id", suffixes=("", "_adopted"))
    merged["cell"] = cell
    return merged


def main() -> int:
    fleet = pd.concat([load_cell(c) for c in CELLS], ignore_index=True)
    n_total = len(fleet)
    print(f"n_total_adopted_run: {n_total} (expected 8160)")

    reproduced = fleet[fleet["archetype_off"] == fleet["archetype_adopted"]].copy()
    unreproduced = fleet[fleet["archetype_off"] != fleet["archetype_adopted"]].copy()

    office_head = reproduced["archetype_source"].str.split(",").str[0].isin(_OFFICE_TIER_HEADS)
    candidates = reproduced[office_head].copy()

    changed = candidates[candidates["archetype_off"] != candidates["archetype_on"]].copy()

    elevator_archetypes = {
        k for k in json.loads(ELEVATORS_BY_ARCHETYPE_PATH.read_text(encoding="utf-8")).keys()
        if not k.startswith("_")
    }
    changed["elevator_off"] = changed["archetype_off"].isin(elevator_archetypes)
    changed["elevator_on"] = changed["archetype_on"].isin(elevator_archetypes)
    changed["elevator_eligibility_change"] = changed.apply(
        lambda r: (
            "gain" if (r["elevator_on"] and not r["elevator_off"])
            else ("lose" if (r["elevator_off"] and not r["elevator_on"]) else "none")
        ),
        axis=1,
    )
    changed["direction"] = changed["archetype_off"] + " -> " + changed["archetype_on"]

    changed["no_floor_count_at_all"] = (
        changed["levels_source"].isin(_NO_FLOOR_COUNT_SOURCES)
        & (~changed["levels_raw_observed"])
        & (changed["height_m_raw"].isna() | (changed["height_m_raw"] <= 0))
    )

    open35 = pd.read_csv(OPEN35_CSV)
    open35_treatment = open35[open35["arm_kind_base"] == "treatment"]
    open35_ids = set(open35_treatment["osm_id_key"])
    print(f"OPEN-35 11-building census loaded: {len(open35_ids)} ids")
    assert len(open35_ids) == 11, f"expected 11 OPEN-35 treatment ids, got {len(open35_ids)}"

    changed["in_open35_11"] = changed["osm_id"].isin(open35_ids)
    overlap = changed[changed["in_open35_11"]]

    out = changed[[
        "osm_id", "cell", "footprint_area_m2", "levels_imputed", "levels_source",
        "archetype_off", "archetype_on", "no_floor_count_at_all", "in_open35_11",
    ]].rename(columns={"footprint_area_m2": "area_m2", "levels_imputed": "levels"})
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    print("--- CONTROL: hand-verified transitions from T02 (must match) ---")
    for osm_id, (exp_off, exp_on) in _CONTROL_CASES.items():
        row = fleet[fleet["osm_id"] == osm_id]
        if row.empty:
            print(f"  {osm_id}: NOT FOUND in fleet")
            continue
        got_off = row.iloc[0]["archetype_off"]
        got_on = row.iloc[0]["archetype_on"]
        ok = (got_off, got_on) == (exp_off, exp_on)
        print(f"  {osm_id}: expected {exp_off}->{exp_on}, got {got_off}->{got_on} [{'MATCH' if ok else 'MISMATCH'}]")

    print(f"n_unreproduced: {len(unreproduced)}")
    print(f"n_reproduced: {len(reproduced)}")
    print(f"n_office_tier_candidates: {len(candidates)}")
    print(f"n_changed: {len(changed)} / {n_total} ({100 * len(changed) / n_total:.2f}%)")
    print("by direction:")
    for direction, n in changed["direction"].value_counts().items():
        print(f"  {direction}: {n}")
    print("levels_source breakdown of changed:")
    for src, n in changed["levels_source"].value_counts().items():
        print(f"  {src}: {n} ({100 * n / len(changed):.2f}%)")
    print(f"no_floor_count_at_all among changed: {changed['no_floor_count_at_all'].sum()} / {len(changed)}")
    print(f"overlap with OPEN-35's 11: {len(overlap)}")
    if len(overlap):
        print(overlap[["osm_id", "cell", "archetype_off", "archetype_on"]].to_string(index=False))
    print(f"wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
