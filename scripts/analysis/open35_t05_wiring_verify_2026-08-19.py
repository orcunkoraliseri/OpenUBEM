"""OPEN-35 T05 (PLAN_board-17-ready-2026-08-19.md): verify that the two wired call
sites -- openubem.idf.builder._derive_num_floors_wired and
openubem.results.aggregator._derive_num_floors_wired -- reproduce EXACTLY the 21
buildings flagged `changed_scope_b` in
openubem/outputs/comparisons/open35_fallback_agreement_scope.csv, by set comparison of
osm_ids (not by count).

This calls the actual wired helper functions (not derive_num_floors() with manually
supplied kwargs, which scripts/analysis/open35_scope_b_verify_2026-08-19.py already
covers) -- proving the wiring itself, not just the underlying function T04 landed.

Fleet-wide, all 12 phaseE cells, 8,160 buildings, existing Step-1 01_buildings.gpkg
files only. No re-classification run, no simulation, no fleet re-run, no re-publication.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.semantic.building_classifier import BuildingClassifier, _INPUT_SCHEMA_COLUMNS
from openubem.geometry.footprint import derive_num_floors
from openubem.idf.builder import _derive_num_floors_wired as builder_wired
from openubem.results.aggregator import (
    _derive_num_floors_wired as agg_wired,
    _fleet_levels_medians as agg_medians,
)

ROOT = Path(__file__).resolve().parent.parent.parent
PHASEE = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
SCOPE_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open35_fallback_agreement_scope.csv"
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]


def changed_for_cell(cell: str) -> tuple[set[str], set[str]]:
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
    for idx in work.index:
        row = work.loc[idx]
        old = derive_num_floors(row)
        new_b = builder_wired(row, work)
        new_a = agg_wired(row, group_median, global_median)
        osm_id = str(work.loc[idx, "osm_id"])
        if old != new_b:
            changed_builder.add(osm_id)
        if old != new_a:
            changed_agg.add(osm_id)
    return changed_builder, changed_agg


def main() -> int:
    changed_builder_all: set[str] = set()
    changed_agg_all: set[str] = set()
    for cell in CELLS:
        cb, ca = changed_for_cell(cell)
        if cb or ca:
            print(f"{cell}: builder={len(cb)} aggregator={len(ca)}")
        changed_builder_all |= cb
        changed_agg_all |= ca

    scope = pd.read_csv(SCOPE_CSV)
    expected = set(scope.loc[scope["changed_scope_b"] == True, "osm_id"].astype(str))
    print(f"Expected (changed_scope_b == True in {SCOPE_CSV.name}): {len(expected)}")
    print(f"builder-wired changed: {len(changed_builder_all)}")
    print(f"aggregator-wired changed: {len(changed_agg_all)}")

    missing_b = expected - changed_builder_all
    extra_b = changed_builder_all - expected
    missing_a = expected - changed_agg_all
    extra_a = changed_agg_all - expected
    print(f"builder  missing={len(missing_b)} {sorted(missing_b)} extra={len(extra_b)} {sorted(extra_b)}")
    print(f"aggregator missing={len(missing_a)} {sorted(missing_a)} extra={len(extra_a)} {sorted(extra_a)}")
    print(f"builder EXACT MEMBERSHIP MATCH: {changed_builder_all == expected}")
    print(f"aggregator EXACT MEMBERSHIP MATCH: {changed_agg_all == expected}")
    print(f"builder == aggregator (same set): {changed_builder_all == changed_agg_all}")

    ok = (changed_builder_all == expected) and (changed_agg_all == expected)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
