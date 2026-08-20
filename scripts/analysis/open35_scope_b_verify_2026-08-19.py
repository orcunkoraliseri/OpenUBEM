"""OPEN-35 T04 (PLAN_board-17-ready-2026-08-19.md, director ruling 4.4a): verify the
LANDED fix -- the now-modified `derive_num_floors()` in openubem/geometry/footprint.py --
changes EXACTLY the 21 buildings flagged `changed_scope_b` in
openubem/outputs/comparisons/open35_fallback_agreement_scope.csv, by set comparison of
osm_ids, not by comparing counts (hard bound, dispatch prompt).

Unlike the prior (pre-fix) scope-measurement script
(scripts/analysis/open35_fallback_agreement_scope_2026-08-19.py), this script calls the
PRODUCTION function directly -- `openubem.geometry.footprint.derive_num_floors` -- with
the same `use_class` / `levels_group_median` / `levels_global_median` keyword arguments
`_impute_levels()` receives, rather than re-implementing the gate. It is read-only reuse
of BuildingClassifier's own median lookup (`_build_levels_median_lookup`) and
`_normalise_use_class` -- no production code executed here is modified by this script.

Fleet-wide, all 12 phaseE cells, 8,160 buildings, existing Step-1 01_buildings.gpkg files
only. No re-classification run, no simulation, no fleet re-run, no re-publication.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.semantic.building_classifier import (
    BuildingClassifier,
    _INPUT_SCHEMA_COLUMNS,
    _normalise_use_class,
)
from openubem.geometry.footprint import derive_num_floors

ROOT = Path(__file__).resolve().parent.parent.parent
PHASEE = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
SCOPE_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open35_fallback_agreement_scope.csv"
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]


def changed_for_cell(cell: str) -> set[str]:
    gdf = gpd.read_file(PHASEE / cell / "01_buildings.gpkg")
    gdf = gdf[_INPUT_SCHEMA_COLUMNS].copy()
    gdf["levels"] = gdf["levels"].astype("Int64")

    clf = BuildingClassifier()
    classified = clf.classify(gdf.copy())
    levels_group_median, levels_global_median = clf._build_levels_median_lookup(gdf)
    use_class = gdf.apply(lambda r: _normalise_use_class(r)[0], axis=1)

    changed: set[str] = set()
    for idx in gdf.index:
        row = gdf.loc[idx].copy()
        row["archetype_source"] = classified.loc[idx, "archetype_source"]
        old = derive_num_floors(row)
        new = derive_num_floors(
            row,
            use_class=use_class.loc[idx],
            levels_group_median=levels_group_median,
            levels_global_median=levels_global_median,
        )
        if old != new:
            changed.add(str(gdf.loc[idx, "osm_id"]))
    return changed


def main() -> int:
    changed_all: set[str] = set()
    for cell in CELLS:
        c = changed_for_cell(cell)
        if c:
            print(f"{cell}: {len(c)} changed")
        changed_all |= c

    print(f"Total changed by the LANDED production fix: {len(changed_all)}")

    scope = pd.read_csv(SCOPE_CSV)
    expected = set(scope.loc[scope["changed_scope_b"] == True, "osm_id"].astype(str))
    print(f"Expected (changed_scope_b == True in {SCOPE_CSV.name}): {len(expected)}")

    missing = expected - changed_all
    extra = changed_all - expected
    print(f"Missing from landed fix (expected but not changed): {len(missing)} {sorted(missing)}")
    print(f"Extra in landed fix (changed but not expected): {len(extra)} {sorted(extra)}")
    print(f"EXACT MEMBERSHIP MATCH: {changed_all == expected}")

    return 0 if changed_all == expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
