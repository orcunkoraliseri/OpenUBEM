"""Overture Maps buildings fetcher (Input-Imputation arc, Phase D, T12.2).

Mirrors `osm_fetcher.ingest_buildings`'s fetch-normalize shape: a targeted
query returns a normalized `gpd.GeoDataFrame`, ready for `fusion.OvertureSource`
to spatially join against a target footprint layer.

Two query paths (plan §6 T12.2 / rule 6 -- no live network in the automated
suite):
  * `slice_path` (offline, test-covered): a small committed GeoParquet slice
    (`openubem/data/fixtures/fusion/overture_<cell>_slice.parquet`), read
    directly via geopandas -- no network, no DuckDB extension install.
  * `endpoint` (live, CP-4 LIVE_SMOKE / T12.6 ONLY -- never exercised by
    pytest): a DuckDB `read_parquet` spatial query against the real Overture
    cloud GeoParquet (S3/Azure), using `httpfs`+`spatial` (new dep `duckdb`,
    plan §4). DuckDB is deliberately reserved for this live-remote leg --
    the small offline slice needs no extension install (which itself would
    be a network call), keeping the automated suite genuinely network-free.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import geopandas as gpd

# Real Overture Buildings columns this adapter reads (plan §5E / §6 T12.2):
# height, num_floors -> levels, class/subtype -> use_class (RAW, not yet
# crosswalked to OpenUBEM's taxonomy -- `fusion.OvertureSource` does that),
# year_built (where populated -- not a universal Overture column).
_NORMALIZED_COLUMNS = ("id", "height", "levels", "use_class", "year_built", "geometry")


def fetch_overture(
    bbox: "tuple[float, float, float, float] | None" = None,
    *,
    endpoint: "str | None" = None,
    slice_path=None,
) -> gpd.GeoDataFrame:
    """Fetch + normalize Overture buildings.

    `bbox` = (minx, miny, maxx, maxy) in the source layer's native CRS
    (EPSG:4326 for the real live endpoint; whatever CRS the committed slice
    fixture carries for the offline path).

    Exactly one of `slice_path` / `endpoint` must be given.
    """
    if slice_path is not None:
        raw = gpd.read_parquet(slice_path)
    elif endpoint is not None:
        raw = _fetch_live(bbox, endpoint)
        bbox = None  # live query already applied the bbox filter server-side
    else:
        raise ValueError("fetch_overture: one of slice_path or endpoint must be given.")

    if bbox is not None and len(raw) > 0:
        minx, miny, maxx, maxy = bbox
        raw = raw.cx[minx:maxx, miny:maxy]

    return _normalize(raw)


def _fetch_live(bbox, endpoint: str) -> gpd.GeoDataFrame:
    """Live cloud leg -- DuckDB `httpfs`+`spatial` spatial query. ONLY reached
    manually by the CP-4 LIVE_SMOKE driver (T12.6); never called by the
    pytest suite (rule 6).

    T12.6 LIVE_SMOKE finding (2026-07-13, real query against
    `overturemaps-us-west-2` release 2026-06-17.0): the real Overture
    Buildings theme schema has NO `year_built` column at all (confirmed via
    `DESCRIBE`; columns are id/names/sources/level/height/min_height/
    is_underground/num_floors/num_floors_underground/min_floor/subtype/
    class/facade_*/roof_*/geometry/has_parts/version/bbox/theme/type) --
    the original SELECT list (written against the plan's §5E precedence
    table, which was itself written before this first live run) crashed
    with a Binder Error. Dropped from the query; `_normalize` already
    handles an absent `year_built` column gracefully (falls back to NaN),
    so Overture's `year_built` fusion source is a structural, permanent
    miss on real data -- reported to CP-4, not silently patched over.
    `ST_AsWKB` makes the geometry column's WKB-bytes shape explicit rather
    than relying on the spatial GEOMETRY type's implicit Arrow conversion.
    """
    import shapely
    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute("SET s3_region='us-west-2';")  # Overture's public bucket; anonymous/unsigned read

    where = ""
    if bbox is not None:
        minx, miny, maxx, maxy = bbox
        # Overture's `bbox` struct column enables predicate pushdown without
        # needing an ST_ function (real Overture partitioning convention).
        where = (
            f"WHERE bbox.xmin <= {maxx} AND bbox.xmax >= {minx} "
            f"AND bbox.ymin <= {maxy} AND bbox.ymax >= {miny}"
        )
    query = (
        "SELECT id, height, num_floors, class, subtype, ST_AsWKB(geometry) AS geometry "
        f"FROM read_parquet('{endpoint}') {where}"
    )
    try:
        arrow_tbl = con.execute(query).fetch_arrow_table()
    finally:
        con.close()
    df = arrow_tbl.to_pandas()
    geoms = shapely.from_wkb(df["geometry"].to_numpy())
    return gpd.GeoDataFrame(df.drop(columns=["geometry"]), geometry=geoms, crs="EPSG:4326")


def _normalize(raw: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = gpd.GeoDataFrame(index=raw.index, geometry=raw.geometry, crs=raw.crs)
    out["id"] = raw["id"].astype(str) if "id" in raw.columns else raw.index.astype(str)
    out["height"] = pd.to_numeric(raw["height"], errors="coerce") if "height" in raw.columns else np.nan
    out["levels"] = (
        pd.to_numeric(raw["num_floors"], errors="coerce") if "num_floors" in raw.columns else np.nan
    )
    use_class = raw["class"].astype(object) if "class" in raw.columns else pd.Series(
        [None] * len(raw), index=raw.index, dtype=object
    )
    if "subtype" in raw.columns:
        use_class = use_class.where(use_class.notna() & (use_class != ""), raw["subtype"])
    out["use_class"] = use_class
    out["year_built"] = (
        pd.to_numeric(raw["year_built"], errors="coerce") if "year_built" in raw.columns else np.nan
    )
    return out[list(_NORMALIZED_COLUMNS)]
