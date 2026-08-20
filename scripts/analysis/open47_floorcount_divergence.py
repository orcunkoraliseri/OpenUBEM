"""OPEN-47 T04 (PLAN_open-48-and-four-items-2026-08-18.md): re-derive, independently and
fresh, the numbers carried in the OPEN-47 ruling comment in
`openubem/semantic/building_classifier.py:167-189` (committed 6aeebb0, 2026-08-13, recording
a user ruling dated 2026-08-12). This is a measurement-only re-run of the same method OPEN-47's
own T02 used (`scripts/analysis/open47_floorcount_reclass.py`), executed independently in this
task rather than read off the archived CSV, per the plan's "re-derive; never inherit a number"
rule. It does not change any default and does not touch `openubone/outputs/comparisons/
open47_floorcount_reclass.csv`.

Method (identical in substance to T02, because the fact being tested is "does the fixed input
data reproduce the fixed comment numbers under the fixed method" -- changing the method would
not test that question):
  - Input: `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`
    (Step-1 acquisition output, 12 cells, the adopted run's own sibling).
  - Classify each cell twice: BuildingClassifier(use_floor_count=False) and (=True).
  - Cross-check archetype_off (flag OFF, today's default) against phaseE_elevrb's actual
    05_results.csv archetype_id (the adopted run). Rows whose archetype family disagrees
    outright are excluded and reported, not silently dropped.
  - Restrict to rows whose archetype_source head is RULE_USE_CLASS_SIZE or
    FALLBACK_SIZE_DEFAULT (the only two rule paths that call _office_size_tier).
  - Count archetype_off != archetype_on changes, their direction, their levels_source
    breakdown, and elevator-eligibility gain/loss via elevators_by_archetype.json.

Control (plan §2 rule 8): three specific buildings are hand-verified transitions quoted in the
T02 progress log (PLAN_three-rulings-2026-08-12.md:487-495). This script's output is checked
against all three by osm_id before the fleet-wide numbers are trusted.
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
OUT_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open47_floorcount_divergence.csv"

_OFFICE_TIER_HEADS = {"RULE_USE_CLASS_SIZE", "FALLBACK_SIZE_DEFAULT"}

# Control cases quoted verbatim in PLAN_three-rulings-2026-08-12.md:487-495.
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
    changed["total_floor_area_m2"] = changed["footprint_area_m2"] * changed["levels_imputed"].clip(lower=1)

    out = changed[[
        "osm_id", "cell", "footprint_area_m2", "levels_imputed", "levels_source",
        "archetype_off", "archetype_on",
    ]].rename(columns={"footprint_area_m2": "area_m2", "levels_imputed": "levels"})
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    gained = changed[changed["elevator_eligibility_change"] == "gain"]

    print("--- CONTROL: hand-verified transitions from T02 (must match) ---")
    changed_by_id = changed.set_index("osm_id")
    for osm_id, (exp_off, exp_on) in _CONTROL_CASES.items():
        row = fleet[fleet["osm_id"] == osm_id]
        if row.empty:
            print(f"  {osm_id}: NOT FOUND in fleet")
            continue
        got_off = row.iloc[0]["archetype_off"]
        got_on = row.iloc[0]["archetype_on"]
        ok = (got_off, got_on) == (exp_off, exp_on)
        print(f"  {osm_id}: expected {exp_off}->{exp_on}, got {got_off}->{got_on} [{'MATCH' if ok else 'MISMATCH'}]")

    print(f"n_unreproduced (archetype family disagreement vs adopted run): {len(unreproduced)}")
    print(f"n_reproduced: {len(reproduced)}")
    print(f"n_office_tier_candidates (RULE_USE_CLASS_SIZE / FALLBACK_SIZE_DEFAULT): {len(candidates)}")
    print(f"n_changed: {len(changed)} / {n_total} ({100 * len(changed) / n_total:.2f}%)")
    print("by direction:")
    for direction, n in changed["direction"].value_counts().items():
        print(f"  {direction}: {n}")
    print("elevator eligibility change among changed buildings:")
    for kind, n in changed["elevator_eligibility_change"].value_counts().items():
        print(f"  {kind}: {n}")
    print(f"total floor area affected (changed rows): {changed['total_floor_area_m2'].sum():.1f} m^2")
    print(f"levels_source breakdown, {len(changed)} changed buildings:")
    for src, n in changed["levels_source"].value_counts().items():
        print(f"  {src}: {n} ({100 * n / len(changed):.2f}%)")
    print(f"levels_source breakdown, {len(gained)} elevator-eligibility-gaining buildings:")
    for src, n in gained["levels_source"].value_counts().items():
        print(f"  {src}: {n}")
    print(f"wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
