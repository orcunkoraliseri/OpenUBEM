"""T14-HOTELFIX recon — classify all 12 phaseE cells for recovered SmallHotel/LargeHotel
buildings (via the bt-or-ft classifier fix) and bucket each by footprint shape.

Hotels carry no complex_shapes_supported flag (layoutGenerator.py MODULE_SPECS), so
room_layout fires ONLY on simple footprints (COMPACT/SLAB/POINT). L/U/T/CROSS/O
(multi-wing) and RIBBON/IRREGULAR all degrade to one_zone_per_floor. This script
reports the per-cell simple-vs-complex split plus the levels_imputed distribution
of the recovered hotels, so the manager can decide whether to fire a hotel array.

Read-only recon: no cluster contact, no IDF generation, no fleet writes.

Usage (local machine only):
    py -3 scripts/cluster/t14_hotel_recon.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

from scripts.validation.v12_cell_pipeline import CELL_CONFIGS

_PHASEE_DIR = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
)
_CELLS = list(CELL_CONFIGS.keys())
_HOTEL_ARCHETYPES = ["SmallHotel", "LargeHotel"]
_SIMPLE_SHAPES = {"compact", "slab", "point"}  # room_layout-eligible for hotels
_COMPLEX_SHAPES = {"L", "U", "T", "cross", "O", "ribbon", "irregular"}  # degrade to per-floor


def recon_cell_hotels(cell: str) -> tuple[dict, pd.DataFrame]:
    from openubem.semantic.building_classifier import (
        _INPUT_SCHEMA_COLUMNS, BuildingClassifier, _impute_levels, _normalise_use_class,
    )
    from openubem.geometry.layoutGenerator import classify_footprint

    path = _PHASEE_DIR / cell / "01_buildings.gpkg"
    if not path.exists():
        sys.exit(f"FATAL: fixture not found: {path}")
    gdf_raw = gpd.read_file(str(path))
    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")
    clf = BuildingClassifier()
    gdf_26 = clf.classify(gdf_in)

    # levels_imputed isn't exposed on the classifier output; recompute it the same
    # way classify_building does internally (same group-median lookup, no leakage).
    levels_group_median, levels_global_median = clf._build_levels_median_lookup(gdf_in)

    cand = gdf_26[gdf_26["archetype_id"].isin(_HOTEL_ARCHETYPES)].copy()
    shapes, levels_imputed = [], []
    for _, r in cand.iterrows():
        shape_class, _metrics = classify_footprint(r.geometry)
        shapes.append(shape_class.value)
        uc, _score = _normalise_use_class(r)
        lev, _lev_src = _impute_levels(
            r, use_class=uc,
            levels_group_median=levels_group_median,
            levels_global_median=levels_global_median,
        )
        levels_imputed.append(lev)
    cand["shape"] = shapes
    cand["levels_imputed"] = levels_imputed
    cand["simple"] = cand["shape"].isin(_SIMPLE_SHAPES)

    row = {"cell": cell}
    for arch in _HOTEL_ARCHETYPES:
        sub = cand[cand["archetype_id"] == arch]
        row[f"{arch}_total"] = int(len(sub))
        row[f"{arch}_simple"] = int(sub["simple"].sum())
        row[f"{arch}_complex"] = int(len(sub) - sub["simple"].sum())
    row["combined_total"] = row["SmallHotel_total"] + row["LargeHotel_total"]
    row["combined_simple"] = row["SmallHotel_simple"] + row["LargeHotel_simple"]

    keep_cols = ["osm_id", "archetype_id", "shape", "simple", "levels", "levels_imputed"]
    return row, cand[keep_cols].assign(cell=cell)


def main() -> None:
    print("=== T14-HOTELFIX recon: 12 phaseE cells, SmallHotel/LargeHotel by shape ===\n")
    rows: list[dict] = []
    all_cand: list[pd.DataFrame] = []
    for cell in _CELLS:
        row, cand_df = recon_cell_hotels(cell)
        rows.append(row)
        all_cand.append(cand_df)
        print(
            f"  {cell:16s} SmallHotel total={row['SmallHotel_total']:3d} "
            f"simple={row['SmallHotel_simple']:3d} complex={row['SmallHotel_complex']:3d}  |  "
            f"LargeHotel total={row['LargeHotel_total']:3d} "
            f"simple={row['LargeHotel_simple']:3d} complex={row['LargeHotel_complex']:3d}  |  "
            f"combined_simple={row['combined_simple']:3d}"
        )

    df = pd.DataFrame(rows).sort_values("combined_simple", ascending=False)
    cand_all = pd.concat(all_cand, ignore_index=True) if all_cand else pd.DataFrame()

    print("\n--- Recon table (sorted by combined_simple desc) ---")
    print(df.to_string(index=False))

    print("\n--- Totals across all 12 cells ---")
    for arch in _HOTEL_ARCHETYPES:
        tot = df[f"{arch}_total"].sum()
        simp = df[f"{arch}_simple"].sum()
        comp = df[f"{arch}_complex"].sum()
        print(f"  {arch}: total={tot}  simple={simp}  complex={comp}")
    print(f"  combined total={df['combined_total'].sum()}  "
          f"combined simple={df['combined_simple'].sum()}")

    if not cand_all.empty:
        print("\n--- levels_imputed distribution (recovered hotels, all cells) ---")
        for arch in _HOTEL_ARCHETYPES:
            sub = cand_all[cand_all["archetype_id"] == arch]
            if sub.empty:
                print(f"  {arch}: (none)")
                continue
            print(f"  {arch} (n={len(sub)}):")
            print(sub["levels_imputed"].value_counts().sort_index().to_string())

        print("\n--- shape distribution (recovered hotels, all cells) ---")
        print(cand_all.groupby(["archetype_id", "shape"]).size().to_string())

    out_dir = REPO / "scratchpad"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "t14h_recon_table.csv", index=False)
    cand_all.to_csv(out_dir / "t14h_recon_candidates.csv", index=False)
    print(f"\nSaved: {out_dir / 't14h_recon_table.csv'}")
    print(f"Saved: {out_dir / 't14h_recon_candidates.csv'}")


if __name__ == "__main__":
    main()
