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
) -> gpd.GeoDataFrame:
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


# ---------------------------------------------------------------------------
# T07 — _seven_step_clean
# ---------------------------------------------------------------------------

def _seven_step_clean(gdf: gpd.GeoDataFrame) -> tuple["gpd.GeoDataFrame", list[str]]:
    # Returns (cleaned_gdf, log_lines) so _serialize can write non-empty log content.
    log_lines: list[str] = []

    def _emit(payload: dict) -> None:
        line = json.dumps(payload)
        logger.info(line)
        log_lines.append(line)

    # Step 1: drop null/empty geometry
    n_before = len(gdf)
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    _emit({"event": "cleaner_step", "step": 1, "dropped": n_before - len(gdf), "remaining": len(gdf)})

    # Step 2: keep only Polygon / MultiPolygon
    n_before = len(gdf)
    gdf = gdf[gdf.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    _emit({"event": "cleaner_step", "step": 2, "dropped": n_before - len(gdf), "remaining": len(gdf)})

    # Step 3: explode MultiPolygon → Polygon parts, re-key osm_id
    n_before = len(gdf)
    exploded_parts = []
    for orig_idx, row in gdf.iterrows():
        if row.geometry.geom_type == "MultiPolygon":
            for k, part in enumerate(row.geometry.geoms):
                new_row = row.copy()
                new_row["osm_id"] = f"{row['osm_id']}_part{k}"
                new_row["geometry"] = part
                exploded_parts.append(new_row)
        else:
            exploded_parts.append(row)
    if exploded_parts:
        gdf = gpd.GeoDataFrame(exploded_parts, crs=gdf.crs)
    gdf = gdf.reset_index(drop=True)

    # iterrows+stack demotes typed columns to object; restore the dtypes _flatten_tags set.
    if "levels" in gdf.columns:
        gdf["levels"] = pd.to_numeric(gdf["levels"], errors="coerce").astype("Int64")
    if "year_built" in gdf.columns:
        gdf["year_built"] = pd.to_numeric(gdf["year_built"], errors="coerce").astype("Int64")
    if "underground" in gdf.columns:
        gdf["underground"] = (
            pd.to_numeric(gdf["underground"], errors="coerce").fillna(0).astype("Int64")
        )
    if "height_m" in gdf.columns:
        gdf["height_m"] = pd.to_numeric(gdf["height_m"], errors="coerce").astype(float)
    if "roof_height_m" in gdf.columns:
        gdf["roof_height_m"] = pd.to_numeric(gdf["roof_height_m"], errors="coerce").astype(float)
    delta = len(gdf) - n_before
    _emit({"event": "cleaner_step", "step": 3, "added": max(delta, 0), "dropped": max(-delta, 0), "remaining": len(gdf)})

    # Step 4: buffer(0) repair
    gdf.geometry = gdf.geometry.buffer(0)
    n_before = len(gdf)
    gdf = gdf[gdf.geom_type == "Polygon"].copy()
    _emit({"event": "cleaner_step", "step": 4, "dropped": n_before - len(gdf), "remaining": len(gdf)})

    # Step 4b: validity re-filter
    n_before = len(gdf)
    gdf = gdf[gdf.geometry.is_valid].copy()
    _emit({"event": "cleaner_step", "step": "4b", "dropped": n_before - len(gdf), "remaining": len(gdf)})

    # Step 5: area / perimeter
    gdf["footprint_area_m2"] = gdf.geometry.area
    gdf["perimeter_m"] = gdf.geometry.length
    _emit({"event": "cleaner_step", "step": 5, "dropped": 0, "remaining": len(gdf)})

    # Step 6: min-area filter
    n_before = len(gdf)
    gdf = gdf[gdf["footprint_area_m2"] >= 20.0].copy()
    _emit({"event": "cleaner_step", "step": 6, "dropped": n_before - len(gdf), "remaining": len(gdf)})

    # Step 7: overlap resolve
    n_before = len(gdf)
    gdf = _resolve_overlaps(gdf, iou_threshold=0.95)
    _emit({"event": "cleaner_step", "step": 7, "dropped": n_before - len(gdf), "remaining": len(gdf)})

    return gdf.reset_index(drop=True), log_lines


# ---------------------------------------------------------------------------
# T09 — _assign_provenance + _build_quality_flag
# ---------------------------------------------------------------------------

def _assign_provenance(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()

    gdf["provenance_levels"] = gdf["levels"].apply(
        lambda v: "OSM_MISSING" if pd.isna(v) else "OSM_OBSERVED"
    )

    def _prov_height(row):
        if pd.isna(row["height_m"]) or (isinstance(row["height_m"], float) and math.isnan(row["height_m"])):
            return "OSM_MISSING"
        if row.get("_height_was_ft", False):
            return "OSM_OBSERVED_FT"
        return "OSM_OBSERVED"

    gdf["provenance_height_m"] = gdf.apply(_prov_height, axis=1)

    gdf["provenance_year_built"] = gdf["year_built"].apply(
        lambda v: "OSM_MISSING" if pd.isna(v) else "OSM_OBSERVED"
    )

    def _prov_building_tag(v):
        if v in ("yes", "", None):
            return "OSM_GENERIC"
        return "OSM_OBSERVED"

    gdf["provenance_building_tag"] = gdf["building_tag"].apply(_prov_building_tag)

    gdf["provenance_function_tag"] = gdf["function_tag"].apply(
        lambda v: "OSM_MISSING" if (v == "" or pd.isna(v)) else "OSM_OBSERVED"
    )

    gdf["provenance_postcode"] = gdf["postcode"].apply(
        lambda v: "OSM_MISSING" if (v is None or (isinstance(v, float) and math.isnan(v))) else "OSM_OBSERVED"
    )

    def _prov_geometry(row):
        if row.get("_overlap_resolved", False):
            return "OSM_OVERLAP_RESOLVED"
        return "OSM_OBSERVED"

    gdf["provenance_geometry"] = gdf.apply(_prov_geometry, axis=1)

    # Drop temp columns
    for col in ("_height_was_ft", "_overlap_resolved"):
        if col in gdf.columns:
            gdf = gdf.drop(columns=[col])

    return gdf


def _build_quality_flag(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()

    def _flags(row):
        tokens = []
        if pd.isna(row["levels"]):
            tokens.append("no_floors")
        if pd.isna(row["height_m"]) or (isinstance(row["height_m"], float) and math.isnan(row["height_m"])):
            tokens.append("no_height")
        if row["building_tag"] in ("yes", "", None):
            tokens.append("generic_tag")
        if row["function_tag"] == "" and row["building_tag"] in ("yes", "", None):
            tokens.append("no_function")
        if row["provenance_geometry"] == "OSM_OVERLAP_RESOLVED":
            tokens.append("overlap_resolved")
        if row["provenance_height_m"] == "OSM_OBSERVED_FT":
            tokens.append("height_only_ft")
        if pd.isna(row["year_built"]):
            tokens.append("no_year")
        return ",".join(sorted(tokens))

    gdf["data_quality_flag"] = gdf.apply(_flags, axis=1)
    return gdf


# ---------------------------------------------------------------------------
# T10 — _validate_schema
# ---------------------------------------------------------------------------

_SCHEMA_COLUMNS = [
    "geometry", "osm_id", "crs_utm",
    "building_tag", "function_tag", "levels", "height_m", "year_built",
    "postcode", "underground", "roof_shape", "roof_height_m",
    "footprint_area_m2", "perimeter_m",
    "surplus_tags",
    "provenance_levels", "provenance_height_m", "provenance_year_built",
    "provenance_building_tag", "provenance_function_tag", "provenance_postcode",
    "provenance_geometry",
    "data_quality_flag",
]


def _validate_schema(gdf: gpd.GeoDataFrame) -> None:
    cols = list(gdf.columns)
    if len(cols) != 23:
        raise ValueError(f"Schema error: expected 23 columns, got {len(cols)}. Columns: {cols}")
    if cols != _SCHEMA_COLUMNS:
        mismatches = [(i, a, b) for i, (a, b) in enumerate(zip(cols, _SCHEMA_COLUMNS)) if a != b]
        extra = set(cols) - set(_SCHEMA_COLUMNS)
        missing = set(_SCHEMA_COLUMNS) - set(cols)
        raise ValueError(
            f"Schema error: column order mismatch. Mismatches: {mismatches}. "
            f"Extra: {extra}. Missing: {missing}."
        )
    for col in ("levels", "year_built", "underground"):
        if str(gdf[col].dtype) != "Int64":
            raise ValueError(f"Schema error: column '{col}' must be Int64, got {gdf[col].dtype}.")
    for col in ("height_m", "roof_height_m", "footprint_area_m2", "perimeter_m"):
        if gdf[col].dtype != "float64":
            raise ValueError(f"Schema error: column '{col}' must be float64, got {gdf[col].dtype}.")
    if not hasattr(gdf["geometry"].dtype, "name") or "geom" not in str(gdf["geometry"].dtype).lower():
        raise ValueError(f"Schema error: 'geometry' must be geometry dtype, got {gdf['geometry'].dtype}.")
    if not gdf["osm_id"].is_unique:
        raise ValueError("Schema error: 'osm_id' column is not unique.")


# ---------------------------------------------------------------------------
# T11 — _serialize
# ---------------------------------------------------------------------------

def _serialize(
    gdf: gpd.GeoDataFrame,
    output_dir: Path,
    log_lines: list[str] | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write collected per-step log lines directly so the file is never 0 bytes (D4/W1.3).
    log_path = output_dir / "01_buildings_clean.log"
    lines = list(log_lines) if log_lines else []
    lines.append(json.dumps({"event": "serialize_complete", "n_rows": len(gdf)}))
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    gdf.to_file(output_dir / "01_buildings_clean.gpkg", layer="buildings", driver="GPKG")

    schema = []
    provenance_roles = {
        "geometry": "geometry", "osm_id": "identity", "crs_utm": "identity",
        "building_tag": "raw_tag", "function_tag": "raw_tag", "levels": "raw_tag",
        "height_m": "raw_tag", "year_built": "raw_tag", "postcode": "raw_tag",
        "underground": "raw_tag", "roof_shape": "raw_tag", "roof_height_m": "raw_tag",
        "footprint_area_m2": "computed", "perimeter_m": "computed",
        "surplus_tags": "surplus",
        "provenance_levels": "provenance", "provenance_height_m": "provenance",
        "provenance_year_built": "provenance", "provenance_building_tag": "provenance",
        "provenance_function_tag": "provenance", "provenance_postcode": "provenance",
        "provenance_geometry": "provenance",
        "data_quality_flag": "quality",
    }
    for col in _SCHEMA_COLUMNS:
        schema.append({
            "name": col,
            "dtype": str(gdf[col].dtype),
            "provenance_role": provenance_roles[col],
        })
    import json as _json
    (output_dir / "01_buildings_clean.schema.json").write_text(
        _json.dumps(schema, indent=2), encoding="utf-8"
    )
