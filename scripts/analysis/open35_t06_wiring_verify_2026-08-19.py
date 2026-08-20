"""OPEN-35 T06 (PLAN_board-17-ready-2026-08-19.md): verify that the parser-path wiring
-- openubem.results.parser._derive_num_floors_wired -- reproduces EXACTLY the same 21
buildings flagged `changed_scope_b` in
openubem/outputs/comparisons/open35_fallback_agreement_scope.csv as the T05-wired
builder and aggregator paths, by set comparison of osm_ids (not by count), and that all
three sets are mutually identical.

This calls the actual wired helper functions (openubem.idf.builder,
openubem.results.aggregator, openubem.results.parser -- all three
`_derive_num_floors_wired`), feeding the parser one the same manifest_row shape
aggregate_results() (openubem/results/__init__.py) now builds: archetype_source,
_use_class (from the classifier's own `_normalise_use_class`), _levels_group_median /
_levels_global_median (from the classifier's own `_build_levels_median_lookup`).

Fleet-wide, all 12 phaseE cells, 8,160 buildings, existing Step-1 01_buildings.gpkg
files only. No re-classification run, no simulation, no fleet re-run, no re-publication.
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
from openubem.idf.builder import _derive_num_floors_wired as builder_wired
from openubem.results.aggregator import (
    _derive_num_floors_wired as agg_wired,
    _fleet_levels_medians as agg_medians,
)
from openubem.results.parser import _derive_num_floors_wired as parser_wired

ROOT = Path(__file__).resolve().parent.parent.parent
PHASEE = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
SCOPE_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open35_fallback_agreement_scope.csv"
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]


def changed_for_cell(cell: str) -> tuple[set[str], set[str], set[str]]:
    gdf = gpd.read_file(PHASEE / cell / "01_buildings.gpkg")
    gdf = gdf[_INPUT_SCHEMA_COLUMNS].copy()
    gdf["levels"] = gdf["levels"].astype("Int64")

    clf = BuildingClassifier()
    classified = clf.classify(gdf.copy())

    work = gdf.copy()
    work["archetype_source"] = classified["archetype_source"]

    group_median, global_median = agg_medians(work)

    changed_builder: set[str] = set()
    changed_agg: set[str] = set()
    changed_parser: set[str] = set()
    for idx in work.index:
        row = work.loc[idx]
        old = derive_num_floors(row)
        new_b = builder_wired(row, work)
        new_a = agg_wired(row, group_median, global_median)

        parser_row = row.copy()
        parser_row["_use_class"] = _normalise_use_class(row)[0]
        parser_row["_levels_group_median"] = group_median
        parser_row["_levels_global_median"] = global_median
        new_p = parser_wired(parser_row)

        osm_id = str(work.loc[idx, "osm_id"])
        if old != new_b:
            changed_builder.add(osm_id)
        if old != new_a:
            changed_agg.add(osm_id)
        if old != new_p:
            changed_parser.add(osm_id)
    return changed_builder, changed_agg, changed_parser


def main() -> int:
    changed_builder_all: set[str] = set()
    changed_agg_all: set[str] = set()
    changed_parser_all: set[str] = set()
    for cell in CELLS:
        cb, ca, cp = changed_for_cell(cell)
        if cb or ca or cp:
            print(f"{cell}: builder={len(cb)} aggregator={len(ca)} parser={len(cp)}")
        changed_builder_all |= cb
        changed_agg_all |= ca
        changed_parser_all |= cp

    scope = pd.read_csv(SCOPE_CSV)
    expected = set(scope.loc[scope["changed_scope_b"] == True, "osm_id"].astype(str))
    print(f"Expected (changed_scope_b == True in {SCOPE_CSV.name}): {len(expected)}")
    print(f"builder-wired changed: {len(changed_builder_all)}")
    print(f"aggregator-wired changed: {len(changed_agg_all)}")
    print(f"parser-wired changed: {len(changed_parser_all)}")

    for name, changed in (
        ("builder", changed_builder_all),
        ("aggregator", changed_agg_all),
        ("parser", changed_parser_all),
    ):
        missing = expected - changed
        extra = changed - expected
        print(f"{name} missing={len(missing)} {sorted(missing)} extra={len(extra)} {sorted(extra)}")
        print(f"{name} EXACT MEMBERSHIP MATCH vs expected: {changed == expected}")

    three_way = changed_builder_all == changed_agg_all == changed_parser_all
    print(f"builder == aggregator == parser (three-way agreement): {three_way}")

    ok = (
        changed_builder_all == expected
        and changed_agg_all == expected
        and changed_parser_all == expected
        and three_way
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
