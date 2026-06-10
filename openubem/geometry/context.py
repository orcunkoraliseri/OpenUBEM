"""Context building discovery for shading (DESIGN §3C)."""
import pandas as pd
import geopandas as gpd
import shapely


def discover_context(
    target_row: pd.Series,
    gdf: gpd.GeoDataFrame,
    target_cx: float,
    target_cy: float,
    sphere_radius_m: float = 30.0,
) -> list[dict]:
    target_poly = target_row["_simplified_geom"]
    influence = target_poly.buffer(sphere_radius_m)
    candidate_idx = gdf.sindex.query(influence, predicate="intersects")

    result = []
    for idx in candidate_idx:
        ctx_row = gdf.iloc[idx]
        if ctx_row["osm_id"] == target_row["osm_id"]:
            continue

        ctx_box = ctx_row.geometry.minimum_rotated_rectangle
        raw_coords = list(ctx_box.exterior.coords)[:-1]
        coords = [(x - target_cx, y - target_cy) for x, y in raw_coords]

        height_m = ctx_row.get("height_m") if "height_m" in ctx_row.index else None
        levels = ctx_row.get("levels") if "levels" in ctx_row.index else None

        if pd.notna(height_m):
            h = float(height_m)
        elif pd.notna(levels):
            h = float(levels) * 3.5
        else:
            h = 3.5

        result.append({
            "name": f"shade_{ctx_row['osm_id']}",
            "coords": coords,
            "height": h,
        })

    return result
