"""Context building discovery for shading (DESIGN §3C)."""
import pandas as pd
import geopandas as gpd
import shapely

EUROPEAN_CONTEXT_FLOOR_TO_FLOOR_M = 3.0


def resolve_european_context_height(
    height_m: object,
    levels: object,
    district_median_height_m: float,
    *,
    floor_to_floor_m: float = EUROPEAN_CONTEXT_FLOOR_TO_FLOOR_M,
) -> tuple[float, str]:
    """European (D-EU-40 R4) context-building height precedence, fail-soft:

    ``height_m`` -> ``levels * floor_to_floor_m`` (3.0 m, the European
    floor-to-floor, not the 3.5 m NA default this module otherwise uses) ->
    the district's median residential height. Returns (height, tier) so the
    caller can count which tier each context building used. Does not alter
    ``discover_context`` -- callers override its returned ``"height"`` entry
    with this result.
    """
    if pd.notna(height_m) and float(height_m) > 0.0:
        return float(height_m), "height_m"
    if pd.notna(levels) and float(levels) > 0.0:
        return float(levels) * floor_to_floor_m, "levels_x_floor_to_floor_m"
    return float(district_median_height_m), "district_median_residential_height"


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
