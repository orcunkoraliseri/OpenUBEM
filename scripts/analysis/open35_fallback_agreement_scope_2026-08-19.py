"""OPEN-35 T04 (PLAN_board-17-ready-2026-08-19.md): before touching any production code,
measure how many buildings' geometry would change if `derive_num_floors()`
(openubem/geometry/footprint.py) consumed the same group-/global-median fallback that
`_impute_levels()` (openubem/semantic/building_classifier.py) already computes for archetype
selection, instead of defaulting to 1 when both `levels` and `height_m` are missing.

Two scopes are measured, both fleet-wide (all 12 phaseE cells, 8,160 buildings), neither a
fleet re-run (no simulation, no classification change -- only recomputing existing functions
over the existing Step-1 gpkg files):

  SCOPE A (naive): apply the archetype-selection fallback to every building whose `levels`
  and `height_m` are both missing, regardless of whether the archetype decision itself ever
  consumed that imputed value. This changes geometry for buildings whose archetype was
  decided by a rule that never looks at `levels_imputed` at all (e.g. area-only office
  tiering with the default `use_floor_count=False`), which is not what OPEN-35 describes.

  SCOPE B (principled): apply the fallback only to buildings whose *actual fired rule*
  consumed the imputed value for its archetype decision -- detected directly from
  `archetype_source`'s first token being in `_LEVELS_CONSUMING`
  (`RULE_HIGHRISE`, `RULE_RESIDENTIAL_TIER`, `RULE_LODGING_TIER`) with `lev_src !=
  "OSM_OBSERVED"`, which is exactly the classifier's own bookkeeping test for "this archetype
  was chosen using an imputed floor count" (building_classifier.py:635-639). This is the
  narrowest defensible reading of section 4.4's "make both consume the same fallback."

Result reported at CP-2: Scope A changes 509 buildings; Scope B changes 21 -- both exceed
section 4.4's pinned ceiling of 11. All 11 of OPEN-35's own 2026-08-19 census
(open35_storey_intervention_results_v2.csv, arm_kind_base == "treatment") are a strict subset
of Scope B's 21; the extra 10 are `LargeHotel` archetypes assigned via `RULE_LODGING_TIER`
(2 in austin_centre, 8 in nyc_centre) that the census excluded because it scoped itself to
"buildings given a mid/high archetype" defined narrowly as MidriseApartment/HighriseApartment,
not lodging -- even though RULE_LODGING_TIER uses the identical `_LEVELS_CONSUMING` mechanism.

No production code changed. No fleet re-run. No simulation.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.semantic.building_classifier import (
    BuildingClassifier,
    _INPUT_SCHEMA_COLUMNS,
    _LEVELS_CONSUMING,
    _impute_levels,
    _normalise_use_class,
)
from openubem.geometry.footprint import derive_num_floors

ROOT = Path(__file__).resolve().parent.parent.parent
PHASEE = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
OPEN35_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open35_storey_intervention_results_v2.csv"
OUT_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open35_fallback_agreement_scope.csv"
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]


def load_cell(cell: str) -> pd.DataFrame:
    gdf = gpd.read_file(PHASEE / cell / "01_buildings.gpkg")
    gdf = gdf[_INPUT_SCHEMA_COLUMNS].copy()
    gdf["levels"] = gdf["levels"].astype("Int64")

    clf = BuildingClassifier()
    classified = clf.classify(gdf.copy())

    levels_group_median, levels_global_median = clf._build_levels_median_lookup(gdf)
    use_class = gdf.apply(lambda r: _normalise_use_class(r)[0], axis=1)
    imputed_pair = gdf.apply(
        lambda r: _impute_levels(
            r, use_class=use_class.loc[r.name],
            levels_group_median=levels_group_median,
            levels_global_median=levels_global_median,
        ), axis=1, result_type="expand",
    )

    old_num_floors = gdf.apply(lambda r: derive_num_floors(r), axis=1)
    head = classified["archetype_source"].str.split(",").str[0]
    lev_src = imputed_pair[1]
    levels_consuming = head.isin(_LEVELS_CONSUMING) & (lev_src != "OSM_OBSERVED")

    both_missing = gdf["levels"].isna() & gdf["height_m"].isna()

    new_num_floors_a = old_num_floors.copy()
    new_num_floors_a[both_missing] = imputed_pair[0][both_missing].clip(lower=1)

    new_num_floors_b = old_num_floors.copy()
    apply_b = both_missing & levels_consuming
    new_num_floors_b[apply_b] = imputed_pair[0][apply_b].clip(lower=1)

    return pd.DataFrame({
        "osm_id": gdf["osm_id"], "cell": cell,
        "use_class": use_class,
        "archetype_id": classified["archetype_id"],
        "archetype_source": classified["archetype_source"],
        "levels_source": lev_src,
        "old_num_floors": old_num_floors,
        "new_num_floors_scope_a": new_num_floors_a,
        "new_num_floors_scope_b": new_num_floors_b,
        "changed_scope_a": old_num_floors != new_num_floors_a,
        "changed_scope_b": old_num_floors != new_num_floors_b,
    })


def main() -> int:
    fleet = pd.concat([load_cell(c) for c in CELLS], ignore_index=True)
    print(f"n_total: {len(fleet)} (expected 8160)")

    n_a = int(fleet["changed_scope_a"].sum())
    n_b = int(fleet["changed_scope_b"].sum())
    print(f"SCOPE A (naive, all both-missing rows): {n_a} buildings changed")
    print(f"SCOPE B (principled, archetype actually consumed levels_imputed): {n_b} buildings changed")

    open35 = pd.read_csv(OPEN35_CSV)
    open35_ids = set(open35[open35["arm_kind_base"] == "treatment"]["osm_id_key"])
    print(f"OPEN-35 census population: {len(open35_ids)}")

    scope_b_ids = set(fleet[fleet["changed_scope_b"]]["osm_id"])
    missing_from_b = open35_ids - scope_b_ids
    extra_in_b = scope_b_ids - open35_ids
    print(f"OPEN-35's 11 all present in Scope B: {len(missing_from_b) == 0} (missing: {missing_from_b})")
    print(f"Scope B buildings NOT in OPEN-35's census: {len(extra_in_b)}")
    if extra_in_b:
        extra_rows = fleet[fleet["osm_id"].isin(extra_in_b)]
        print(extra_rows[["osm_id", "cell", "use_class", "archetype_id", "new_num_floors_scope_b"]].to_string(index=False))

    fleet.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
