from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

EVIDENCE = REPO / "evidence" / "open48_refleet"
ADOPTED = REPO / "openubem" / "outputs" / "comparisons" / "open65_reparse_fleet_eui_2026-09-29.csv"
OUT = REPO / "openubem" / "outputs" / "comparisons" / "open35_blast_radius_2026-09-30.csv"


def do_cell(cell: str) -> pd.DataFrame:
    import geopandas as gpd
    from openubem.idf.builder import _derive_num_floors_wired
    from openubem.semantic.building_classifier import (
        _INPUT_SCHEMA_COLUMNS, BuildingClassifier, _impute_levels, _normalise_use_class)

    adopted = set(pd.read_csv(ADOPTED, usecols=["osm_id", "cell"]).query("cell == @cell")["osm_id"].astype(str))
    gdf_raw = gpd.read_file(str(EVIDENCE / cell / "01_buildings.gpkg"))
    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")
    gdf = BuildingClassifier().classify(gdf_in)
    lgm, lglob = BuildingClassifier()._build_levels_median_lookup(gdf)
    rows = []
    for _, r in gdf.iterrows():
        oid = str(r["osm_id"])
        if oid not in adopted:
            continue
        uc, _ = _normalise_use_class(r)
        imp, src = _impute_levels(r, use_class=uc, levels_group_median=lgm, levels_global_median=lglob)
        today = _derive_num_floors_wired(r, gdf)
        both_missing = bool(pd.isna(r["levels"]) and pd.isna(r["height_m"]))
        optA = max(1, int(imp)) if both_missing else today
        rows.append(dict(osm_id=oid, cell=cell, archetype_id=r["archetype_id"], use_class=uc,
                         levels=r["levels"], height_m=r["height_m"], both_missing=both_missing,
                         imputed_levels=imp, imputed_source=src, floors_today=today,
                         floors_option_a=optA, changes=today != optA))
    return pd.DataFrame(rows)


def main() -> None:
    cells = sorted(pd.read_csv(ADOPTED, usecols=["cell"])["cell"].unique())
    with Pool(6) as p:
        dfs = p.map(do_cell, cells)
    df = pd.concat(dfs, ignore_index=True)
    df.to_csv(OUT, index=False)
    print(len(df))


if __name__ == "__main__":
    main()
