"""T07 (PLAN_twenty-items-2026-08-19.md) -- OPEN-14 config-gate localisation.

Constructs the smallest local case where the config gate (`config.py:141`,
`FUSION_SOURCES_BY_TARGET = {}`) is satisfied, using the real, tracked
`overture_nyc_centre_slice.parquet` fixture (not the synthetic testcell
fixture), and checks whether a `FUSED_*` provenance token then appears.
"""
from types import SimpleNamespace

import numpy as np
import geopandas as gpd
from shapely.geometry import box

from openubem import config
from openubem.semantic import fusion
from openubem.semantic.imputation import ImputeConfig, impute_missing

SLICE = r"openubem/data/fixtures/fusion/overture_nyc_centre_slice.parquet"


def main():
    layer = gpd.read_parquet(SLICE)
    print("slice shape:", layer.shape, "columns:", list(layer.columns))
    print("slice CRS:", layer.crs.to_epsg() if layer.crs else None)

    # pick a real building footprint from inside the slice's own bbox, in
    # the slice's own CRS (EPSG:4326, as read above), small box centred on
    # the centroid of a slice geometry that carries a non-null height (so
    # the spatial join has a guaranteed real, non-null target to hit).
    has_height = layer["height"].notna()
    row0 = layer.loc[has_height].iloc[0]
    print("chosen source row height (raw m):", row0["height"])
    g0 = row0.geometry
    cx, cy = g0.centroid.x, g0.centroid.y
    eps = 0.00002
    footprint = box(cx - eps, cy - eps, cx + eps, cy + eps)

    target = gpd.GeoDataFrame(
        [{"height_m": np.nan, "geometry": footprint}],
        geometry="geometry", crs=layer.crs,
    )

    cfg_closed = SimpleNamespace(
        FUSION_SOURCES_BY_TARGET={},  # the shipped default, config.py:141
        FUSION_OVERTURE_SLICE_PATH=SLICE,
        FUSION_OVERTURE_ENDPOINT=None,
        FUSION_LIDAR_NDSM_PATH=None,
        FUSION_ASSESSOR_PATH=None,
        FUSION_ASSESSOR_FIELDS={},
    )
    value_closed, token_closed = fusion.fuse(target, "height_m", cfg_closed)
    print("\n-- gate CLOSED (FUSION_SOURCES_BY_TARGET={}) --")
    print("value:", value_closed.tolist(), "token:", token_closed.tolist())

    cfg_open = SimpleNamespace(
        FUSION_SOURCES_BY_TARGET={"height_m": ("overture",)},
        FUSION_OVERTURE_SLICE_PATH=SLICE,
        FUSION_OVERTURE_ENDPOINT=None,
        FUSION_LIDAR_NDSM_PATH=None,
        FUSION_ASSESSOR_PATH=None,
        FUSION_ASSESSOR_FIELDS={},
    )
    value_open, token_open = fusion.fuse(target, "height_m", cfg_open)
    print("\n-- gate OPEN (FUSION_SOURCES_BY_TARGET={'height_m': ('overture',)}) --")
    print("value:", value_open.tolist(), "token:", token_open.tolist())

    # also route through the full impute_missing() orchestrator, since that
    # (not fuse() directly) is the actual entry point mask_recover.py calls.
    # `_fusion_tier` calls `fusion.fuse(gdf, attr)` with no cfg, so it
    # resolves from the `openubem.config` module globals -- patch those
    # directly (this is what mask_recover.py's caller would have to do too).
    orig_sources = config.FUSION_SOURCES_BY_TARGET
    orig_slice = config.FUSION_OVERTURE_SLICE_PATH
    try:
        config.FUSION_SOURCES_BY_TARGET = {"height_m": ("overture",)}
        config.FUSION_OVERTURE_SLICE_PATH = SLICE
        out = impute_missing(
            target.copy(), targets=["height_m"],
            cfg=ImputeConfig(per_input_tiers={"height_m": ("fusion",)}),
        )
    finally:
        config.FUSION_SOURCES_BY_TARGET = orig_sources
        config.FUSION_OVERTURE_SLICE_PATH = orig_slice
    print("\n-- via impute_missing(), gate open, real nyc_centre slice --")
    print("height_m:", out["height_m"].tolist())
    print("provenance_height_m:", out["provenance_height_m"].tolist())


if __name__ == "__main__":
    main()
