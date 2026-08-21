"""OPEN-14 T08 -- fusion-tier yield measurement on nyc_centre (2026-08-20).

Yield measurement, NOT a promotion. `openubem/config.py` is never edited on
disk -- the two FUSION_* attributes are monkey-patched onto the imported
`openubem.config` module object inside this script and restored in a
`finally` block. Calls the production router
(`openubem.semantic.imputation.impute_missing`) directly -- no
re-implementation (plan D3).
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from openubem import config
from openubem.semantic import imputation

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDINGS_GPKG = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4\nyc_centre\01_buildings.gpkg"
)
OVERTURE_SLICE = REPO_ROOT / "openubem" / "data" / "fixtures" / "fusion" / "overture_nyc_centre_slice.parquet"
OUT_CSV = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open14_fusion_yield_nyc_centre_2026-08-20.csv"


def main() -> None:
    assert BUILDINGS_GPKG.exists(), f"missing input: {BUILDINGS_GPKG}"
    assert OVERTURE_SLICE.exists(), f"missing tracked slice: {OVERTURE_SLICE}"

    gdf = gpd.read_file(BUILDINGS_GPKG)
    n_total = len(gdf)
    null_before = gdf["height_m"].isna()
    n_null_before = int(null_before.sum())

    orig_sources = config.FUSION_SOURCES_BY_TARGET
    orig_slice_path = config.FUSION_OVERTURE_SLICE_PATH
    try:
        config.FUSION_SOURCES_BY_TARGET = {"height_m": ("overture",)}
        config.FUSION_OVERTURE_SLICE_PATH = OVERTURE_SLICE

        from openubem.semantic import fusion as fusion_mod
        overture_available = fusion_mod.get_source("overture").available(config)
        precedence = [s.name for s in fusion_mod.precedence_for("height_m", config)]

        fusion_only_cfg = imputation.ImputeConfig(enabled_tiers=("fusion",))
        out = imputation.impute_missing(gdf, cfg=fusion_only_cfg, targets=["height_m"])
    finally:
        config.FUSION_SOURCES_BY_TARGET = orig_sources
        config.FUSION_OVERTURE_SLICE_PATH = orig_slice_path

    filled_mask = null_before & out["height_m"].notna()
    n_filled = int(filled_mask.sum())
    prov_after = out["provenance_height_m"]
    token_counts = prov_after.loc[filled_mask].value_counts(dropna=False)

    still_null = null_before & out["height_m"].isna()
    n_still_null = int(still_null.sum())

    observed = gdf.loc[~null_before, "height_m"]
    filled_values = out.loc[filled_mask, "height_m"]

    rows = pd.DataFrame({
        "osm_id": gdf["osm_id"],
        "height_m_before": gdf["height_m"],
        "height_m_after": out["height_m"],
        "provenance_height_m_before": gdf["provenance_height_m"],
        "provenance_height_m_after": prov_after,
        "was_null": null_before,
        "filled_by_fusion": filled_mask,
    })
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(OUT_CSV, index=False)

    print(f"n_total={n_total}")
    print(f"n_null_before={n_null_before}")
    print(f"n_filled={n_filled}")
    print(f"n_still_null={n_still_null}")
    print(f"overture_available={overture_available}")
    print(f"precedence_for(height_m)={precedence}")
    print("token_counts:")
    print(token_counts.to_string())
    print("observed (non-null pre-existing) height_m describe:")
    print(observed.describe().to_string())
    if n_filled > 0:
        print("filled height_m describe:")
        print(filled_values.describe().to_string())
    else:
        print("filled height_m describe: n/a (0 filled)")


if __name__ == "__main__":
    main()
