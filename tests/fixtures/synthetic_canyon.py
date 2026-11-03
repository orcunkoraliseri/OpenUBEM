"""Shared builder for the T08/T10/T11 synthetic street-canyon fixture.

Two parallel rectangular blocks of height H separated by a canyon of width W, long enough
(relative to W) that the mid-canyon point behaves like the infinite 2D canyon the analytic
SVF check (P-14) assumes.
"""
import geopandas as gpd
from shapely.geometry import box

CRS = "EPSG:32618"


def build_canyon_gdf(height_m: float, width_m: float, block_len: float = 200.0, block_depth: float = 30.0) -> gpd.GeoDataFrame:
    half_w = width_m / 2.0
    north = box(-block_len / 2, half_w, block_len / 2, half_w + block_depth)
    south = box(-block_len / 2, -half_w - block_depth, block_len / 2, -half_w)
    return gpd.GeoDataFrame(
        {
            "osm_id": ["canyon_north", "canyon_south"],
            "height_m": [height_m, height_m],
            "levels": [round(height_m / 3.5), round(height_m / 3.5)],
        },
        geometry=[north, south],
        crs=CRS,
    )
