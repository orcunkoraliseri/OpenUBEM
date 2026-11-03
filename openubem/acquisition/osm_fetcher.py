from __future__ import annotations

import json
import logging
import math
import re
from pathlib import Path

import geopandas as gpd
import osmnx as ox
import pandas as pd
import shapely
from packaging.version import Version

from openubem.acquisition.footprint_schema import (
    SCHEMA_COLUMNS as _SHARED_SCHEMA_COLUMNS,
    assign_provenance as _shared_assign_provenance,
    build_quality_flag as _shared_build_quality_flag,
    seven_step_clean as _shared_seven_step_clean,
    serialize as _shared_serialize,
    validate_schema as _shared_validate_schema,
)

assert Version("1.9") <= Version(ox.__version__) < Version("2.0"), (
    f"osmnx version out of pinned range [1.9, 2.0): {ox.__version__}"
)

logger = logging.getLogger("openubem.acquisition")


# ---------------------------------------------------------------------------
# T02 — Public API + dispatch + retry wiring
# ---------------------------------------------------------------------------

def ingest_buildings(
    location: str | tuple[float, float] | None = None,
    radius_m: float = 1000.0,
    bbox: tuple[float, float, float, float] | None = None,
    osm_path: Path | None = None,
    tags: dict | None = None,
    retry_policy: "tenacity.Retrying | None" = None,
    output_dir: Path | None = None,
    source: str = "osm",
    source_options: dict | None = None,
) -> gpd.GeoDataFrame:
    """Acquire primary footprints through the documented source dispatch.

    The historical OSM arguments retain their exact behaviour.  The two EU-02
    official adapters use the same frozen-schema tail and may be selected with
    ``source='bdtopo'`` or ``source='bologna'`` and a bbox.
    """
    if source != "osm":
        if bbox is None or any(value is not None for value in (location, osm_path)):
            raise ValueError("Non-OSM sources require bbox only.")
        options = source_options or {}
        if source == "bdtopo":
            from openubem.acquisition.bdtopo_fetcher import ingest_bdtopo
            return ingest_bdtopo(bbox=bbox, output_dir=output_dir, **options)
        if source == "bologna":
            from openubem.acquisition.bologna_fetcher import ingest_bologna
            return ingest_bologna(bbox=bbox, output_dir=output_dir, **options)
        raise ValueError(f"Unsupported primary acquisition source: {source!r}")
    if tags is None:
        tags = {"building": True}

    mode = _resolve_mode(location, bbox, osm_path)

    fetch_map = {
        "address": lambda: ox.features.features_from_address(location, tags=tags, dist=radius_m),
        "point":   lambda: ox.features.features_from_point(location, tags=tags, dist=radius_m),
        "bbox":    lambda: ox.features.features_from_bbox(bbox=bbox, tags=tags),
        "xml":     lambda: ox.features.features_from_xml(osm_path, tags=tags),
    }
    fetcher = fetch_map[mode]

    if retry_policy is not None and mode != "xml":
        raw = retry_policy(fetcher)
    else:
        raw = fetcher()

    gdf = _flatten_tags(raw)

    utm = gdf.estimate_utm_crs()
    gdf = gdf.to_crs(utm)
    gdf["crs_utm"] = utm.to_string()
    assert gdf.crs.is_projected

    gdf, _clean_log_lines = _seven_step_clean(gdf)

    # D8/W1.7 — vertex-count warning (§5.1 metric signal for Stage 3 simplify).
    if len(gdf) > 0:
        _vert_counts = gdf.geometry.apply(lambda g: len(g.exterior.coords))
        _p95 = int(_vert_counts.quantile(0.95))
        _clean_log_lines.append(json.dumps({"event": "vertex_p95", "p95_vertices": _p95}))
        if _p95 >= 80:
            logger.warning(
                json.dumps({"event": "high_vertex_count", "p95_vertices": _p95, "n_rows": len(gdf)})
            )

    gdf = _assign_provenance(gdf)
    gdf = _build_quality_flag(gdf)

    # Build WGS84 bbox for the warning payload (D5/W1.5): prefer caller-supplied bbox,
    # else derive from the projected GDF bounds converted back to geographic.
    if bbox is not None:
        _warning_bbox = list(bbox)
    elif len(gdf) > 0:
        _wgs84 = gdf.to_crs("EPSG:4326")
        b = _wgs84.total_bounds  # [minx, miny, maxx, maxy] = [W, S, E, N]
        _warning_bbox = [b[3], b[1], b[2], b[0]]  # (n, s, e, w) per DESIGN
    else:
        _warning_bbox = []

    if len(gdf) > 0 and gdf["data_quality_flag"].str.contains("generic_tag").all():
        logger.warning(
            json.dumps({
                "event": "all_generic_neighbourhood",
                "bbox": _warning_bbox,
                "n_rows": len(gdf),
            })
        )

    # Drop surplus raw OSM tag columns + enforce canonical column order before validation.
    # Live OSM fetches return ~150 extra tag columns that _flatten_tags preserves; they are
    # already captured in surplus_tags JSON and must not leak into the persisted 23-col schema.
    missing = [c for c in _SCHEMA_COLUMNS if c not in gdf.columns]
    if missing:
        raise ValueError(f"Schema error: required columns missing after pipeline: {missing}")
    gdf = gdf[_SCHEMA_COLUMNS]

    _validate_schema(gdf)

    if output_dir is not None:
        _serialize(gdf, Path(output_dir), log_lines=_clean_log_lines)

    return gdf


fetch_buildings = ingest_buildings


def _resolve_mode(
    location: str | tuple | None,
    bbox: tuple | None,
    osm_path: Path | None,
) -> str:
    non_none = sum(x is not None for x in (location, bbox, osm_path))
    if non_none != 1:
        raise ValueError(
            f"Exactly one of {{location, bbox, osm_path}} must be set; got {non_none} non-None."
        )
    if osm_path is not None:
        return "xml"
    if bbox is not None:
        return "bbox"
    if isinstance(location, str):
        return "address"
    if isinstance(location, tuple) and len(location) == 2:
        return "point"
    raise ValueError(f"Unrecognised location type: {type(location)}")


# ---------------------------------------------------------------------------
# T04 — _parse_height_to_m
# ---------------------------------------------------------------------------

_HEIGHT_RE = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*(ft|'|m)?\s*$")


def _parse_height_to_m(value) -> tuple[float, bool]:
    if not isinstance(value, str):
        return (float("nan"), False)
    m = _HEIGHT_RE.match(value)
    if m is None:
        return (float("nan"), False)
    num = float(m.group(1))
    unit = m.group(2)
    if unit in ("ft", "'"):
        return (num * 0.3048, True)
    return (num, False)


# ---------------------------------------------------------------------------
# T05 — _parse_year
# ---------------------------------------------------------------------------

_CENTURY_RE = re.compile(r"^[Cc](\d{1,2})$")


def _parse_year(value) -> int | pd.NA:
    if pd.isna(value):
        return pd.NA
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if re.match(r"^\d{4}", value):
        return int(value[:4])
    cm = _CENTURY_RE.match(value)
    if cm:
        n = int(cm.group(1))
        if n in (19, 20):
            return (n - 1) * 100 + 50
        return pd.NA
    return pd.NA


# ---------------------------------------------------------------------------
# T03 — _flatten_tags
# ---------------------------------------------------------------------------

_OSM_RENAME_SOURCES = {
    "building", "amenity", "shop", "office",
    "building:levels", "height", "start_date",
    "addr:postcode", "building:levels:underground",
    "roof:shape", "roof:height",
}


def _flatten_tags(gdf_raw: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf_raw.reset_index()

    # osm_id from index columns — check element_type+osmid co-presence FIRST (D2/R5)
    if "element_type" in gdf.columns and "osmid" in gdf.columns:
        gdf["osm_id"] = gdf["element_type"].astype(str) + "/" + gdf["osmid"].astype(str)
    elif "osmid" in gdf.columns:
        gdf["osm_id"] = gdf["osmid"].astype(str)
    else:
        gdf["osm_id"] = gdf.index.astype(str)

    # Preserve raw height string for surplus_tags
    raw_height = gdf.get("height", pd.Series(dtype=object))

    # building_tag
    if "building" in gdf.columns:
        gdf["building_tag"] = gdf["building"].fillna("").astype(str).str.lower()
    else:
        gdf["building_tag"] = ""

    # function_tag: amenity > shop > office
    def _first_non_null(*cols):
        result = pd.Series("", index=gdf.index, dtype=object)
        for col in reversed(cols):
            if col in gdf.columns:
                mask = gdf[col].notna() & (gdf[col].astype(str) != "")
                result[mask] = gdf.loc[mask, col].astype(str)
        return result

    gdf["function_tag"] = _first_non_null("amenity", "shop", "office")

    # levels
    if "building:levels" in gdf.columns:
        gdf["levels"] = pd.to_numeric(gdf["building:levels"], errors="coerce").round().astype("Int64")
    else:
        gdf["levels"] = pd.array([pd.NA] * len(gdf), dtype="Int64")

    # height_m + _height_was_ft
    if "height" in gdf.columns:
        parsed = gdf["height"].apply(_parse_height_to_m)
        gdf["height_m"] = parsed.apply(lambda x: x[0]).astype(float)
        gdf["_height_was_ft"] = parsed.apply(lambda x: x[1])
    else:
        gdf["height_m"] = float("nan")
        gdf["_height_was_ft"] = False

    # year_built
    if "start_date" in gdf.columns:
        gdf["year_built"] = pd.array(
            [_parse_year(v) for v in gdf["start_date"]], dtype="Int64"
        )
    else:
        gdf["year_built"] = pd.array([pd.NA] * len(gdf), dtype="Int64")

    # postcode
    if "addr:postcode" in gdf.columns:
        gdf["postcode"] = gdf["addr:postcode"].where(gdf["addr:postcode"].notna(), other=None)
    else:
        gdf["postcode"] = None

    # underground
    if "building:levels:underground" in gdf.columns:
        gdf["underground"] = (
            pd.to_numeric(gdf["building:levels:underground"], errors="coerce")
            .round()
            .fillna(0)
            .astype("Int64")
        )
    else:
        gdf["underground"] = pd.array([0] * len(gdf), dtype="Int64")

    # roof_shape
    if "roof:shape" in gdf.columns:
        gdf["roof_shape"] = gdf["roof:shape"].fillna("").astype(str)
    else:
        gdf["roof_shape"] = ""

    # roof_height_m
    if "roof:height" in gdf.columns:
        parsed_rh = gdf["roof:height"].apply(_parse_height_to_m)
        gdf["roof_height_m"] = parsed_rh.apply(lambda x: x[0]).astype(float)
    else:
        gdf["roof_height_m"] = float("nan")

    # surplus_tags: all columns not in rename sources + not canonical outputs + not geometry/osm_id
    canonical_out = {
        "geometry", "osm_id", "building_tag", "function_tag", "levels",
        "height_m", "year_built", "postcode", "underground", "roof_shape",
        "roof_height_m", "_height_was_ft",
        # index leftovers
        "element_type", "osmid",
    }

    def _make_surplus(row):
        surplus = {}
        _skip = canonical_out | _OSM_RENAME_SOURCES  # D6: source tags are already mapped
        for col in gdf.columns:
            if col in _skip:
                continue
            v = row[col]
            if pd.isna(v) if not isinstance(v, (list, dict)) else False:
                continue
            surplus[col] = str(v)
        # always include raw height string
        rh_val = raw_height.get(row.name) if hasattr(raw_height, "get") else None
        if rh_val is not None and not (isinstance(rh_val, float) and math.isnan(rh_val)):
            surplus["height_raw"] = str(rh_val)
        return json.dumps(surplus)

    gdf["surplus_tags"] = gdf.apply(_make_surplus, axis=1)

    return gdf


# ---------------------------------------------------------------------------
# T08 — _resolve_overlaps
# ---------------------------------------------------------------------------

def _resolve_overlaps(gdf: gpd.GeoDataFrame, iou_threshold: float = 0.95) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["_overlap_resolved"] = False

    drop_set = set()
    resolved_set = set()

    geoms = gdf.geometry.values
    idx_list = list(gdf.index)

    for pos_i, idx_i in enumerate(idx_list):
        if idx_i in drop_set:
            continue
        geom_i = geoms[pos_i]
        candidates = gdf.sindex.query(geom_i, predicate="intersects")
        for pos_j in candidates:
            idx_j = idx_list[pos_j]
            if pos_j <= pos_i or idx_j in drop_set:
                continue
            geom_j = geoms[pos_j]
            inter_area = geom_i.intersection(geom_j).area
            union_area = geom_i.union(geom_j).area
            if union_area == 0:
                continue
            iou = inter_area / union_area
            if iou > iou_threshold:
                area_i = gdf.at[idx_i, "footprint_area_m2"]
                area_j = gdf.at[idx_j, "footprint_area_m2"]
                if area_i >= area_j:
                    drop_set.add(idx_j)
                    resolved_set.add(idx_i)
                else:
                    drop_set.add(idx_i)
                    resolved_set.add(idx_j)

    for idx in resolved_set:
        if idx not in drop_set:
            gdf.at[idx, "_overlap_resolved"] = True

    return gdf.drop(index=list(drop_set))


def _seven_step_clean(gdf: gpd.GeoDataFrame) -> tuple["gpd.GeoDataFrame", list[str]]:
    """OSM-compatible entry point for the shared geometry-cleaning tail."""
    return _shared_seven_step_clean(
        gdf,
        overlap_resolver=_resolve_overlaps,
        log_sink=logger.info,
    )


# ---------------------------------------------------------------------------
# T09 — _assign_provenance + _build_quality_flag
# ---------------------------------------------------------------------------

def _assign_provenance(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return _shared_assign_provenance(gdf, source="OSM")


def _build_quality_flag(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return _shared_build_quality_flag(gdf, source="OSM")


# ---------------------------------------------------------------------------
# T10 — _validate_schema
# ---------------------------------------------------------------------------

_SCHEMA_COLUMNS = _SHARED_SCHEMA_COLUMNS


def _validate_schema(gdf: gpd.GeoDataFrame) -> None:
    _shared_validate_schema(gdf)


# ---------------------------------------------------------------------------
# T11 — _serialize
# ---------------------------------------------------------------------------

def _serialize(
    gdf: gpd.GeoDataFrame,
    output_dir: Path,
    log_lines: list[str] | None = None,
) -> None:
    _shared_serialize(gdf, output_dir, log_lines=log_lines)
