"""T05 (PLAN_ten-live-items-2026-08-21) — OPEN-35: how many buildings sit on the undecided branch?

Measurement only. No fallback is picked; this counts the population and states the floor-area /
denominator stakes of each candidate branch.

archetype_source for the fleet is not persisted in evidence/open48_refleet4's run-4 artifacts
(04_simulation_manifest.parquet and step3/03_idf_manifest.parquet were checked and do not carry it).
It IS on disk in openubem/outputs/comparisons/open35_fallback_agreement_scope.csv (8,160 rows,
produced 2026-08-19 from the identical fleet population -- verified: same osm_id sets and same
null-height_m counts per cell against evidence/open48_refleet4's own gpkgs). That is the on-disk
artifact this task locates and reuses, per the plan's instruction; the classifier is not re-run here
except through the identical, already-cached archetype_source values.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.geometry.footprint import _archetype_consumed_group_median, derive_num_floors
from openubem.idf.builder import _fleet_levels_medians
from openubem.semantic.building_classifier import _normalise_use_class

ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE = ROOT / "evidence" / "open48_refleet4"
ARCHETYPE_SRC_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open35_fallback_agreement_scope.csv"
OUT_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open35_fallback_population_2026-08-21.csv"

CELLS = [f"{city}_{kind}" for city in ("austin", "la", "nyc") for kind in ("centre", "rural", "suburban", "urban")]

archetype_src = pd.read_csv(ARCHETYPE_SRC_CSV, usecols=["osm_id", "cell", "archetype_source"])

rows = []
for cell in CELLS:
    gdf = gpd.read_file(EVIDENCE / cell / "01_buildings.gpkg")
    src_cell = archetype_src[archetype_src["cell"] == cell][["osm_id", "archetype_source"]]
    gdf = gdf.merge(src_cell, on="osm_id", how="left")

    consumed = gdf.apply(_archetype_consumed_group_median, axis=1)
    both_missing = gdf["levels"].isna() & gdf["height_m"].isna()

    # C11: assert consumed population is a subset of both_missing.
    n_consumed_not_both_missing = int((consumed & ~both_missing).sum())

    population_mask = consumed
    if not population_mask.any():
        continue

    levels_group_median, levels_global_median = _fleet_levels_medians(gdf)

    pop = gdf[population_mask].copy()
    use_classes = pop.apply(lambda r: _normalise_use_class(r)[0], axis=1)

    current_num_floors = []
    preopen35_num_floors = []
    for (_, row), uc in zip(pop.iterrows(), use_classes):
        current_num_floors.append(derive_num_floors(
            row, use_class=uc,
            levels_group_median=levels_group_median,
            levels_global_median=levels_global_median,
        ))
        preopen35_num_floors.append(derive_num_floors(row))

    pop["use_class"] = use_classes.values
    pop["current_num_floors"] = current_num_floors
    pop["preopen35_num_floors"] = preopen35_num_floors
    pop["current_floor_area_m2"] = pop["footprint_area_m2"] * pop["current_num_floors"]
    pop["preopen35_floor_area_m2"] = pop["footprint_area_m2"] * pop["preopen35_num_floors"]
    pop["n_consumed_not_both_missing_in_cell"] = n_consumed_not_both_missing

    rows.append(pop[[
        "osm_id", "levels", "height_m", "footprint_area_m2", "archetype_source", "use_class",
        "current_num_floors", "preopen35_num_floors",
        "current_floor_area_m2", "preopen35_floor_area_m2",
        "n_consumed_not_both_missing_in_cell",
    ]].assign(cell=cell))

fleet = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
fleet.to_csv(OUT_CSV, index=False)

n = len(fleet)
n_violating_c11 = int(fleet["n_consumed_not_both_missing_in_cell"].sum()) if n else 0
print(f"n_on_group_median_branch = {n}")
print(f"C11 check: consumed-but-not-both-missing rows across fleet = {n_violating_c11} (should be 0)")
print()
print("by cell:")
print(fleet.groupby("cell").size().to_string())
print()
cur_area = fleet["current_floor_area_m2"].sum()
pre_area = fleet["preopen35_floor_area_m2"].sum()
print(f"fleet floor_area_m2 at stake, current (group/global median) branch = {cur_area:,.1f}")
print(f"fleet floor_area_m2 at stake, pre-OPEN-35 (return 1) branch      = {pre_area:,.1f}")
print(f"delta (current - pre-OPEN-35) = {cur_area - pre_area:,.1f} m2")

# C12: the 21-building OPEN-35 sample vs this population.
sample_21 = archetype_src.copy()
scope_b = pd.read_csv(ARCHETYPE_SRC_CSV, usecols=["osm_id", "cell", "changed_scope_b"])
sample_21 = scope_b[scope_b["changed_scope_b"]][["osm_id", "cell"]]
found_keys = set(zip(fleet["osm_id"], fleet["cell"]))
sample_keys = set(zip(sample_21["osm_id"], sample_21["cell"]))
missing = sample_keys - found_keys
print()
print(f"C12: 21-building OPEN-35 sample size = {len(sample_keys)}")
print(f"C12: of those, inside this task's population = {len(sample_keys & found_keys)}")
print(f"C12: of those, NOT inside this task's population = {len(missing)}: {sorted(missing)}")
