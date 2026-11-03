"""Shared frozen footprint schema for every primary acquisition adapter.

OSM retains its tag parser; source adapters supply normalized raw values here and
then use this module for cleaning, provenance, validation, and serialization.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import geopandas as gpd
import pandas as pd


SCHEMA_COLUMNS = [
    "geometry", "osm_id", "crs_utm", "building_tag", "function_tag", "levels", "height_m", "year_built",
    "postcode", "underground", "roof_shape", "roof_height_m", "footprint_area_m2", "perimeter_m",
    "surplus_tags", "provenance_levels", "provenance_height_m", "provenance_year_built",
    "provenance_building_tag", "provenance_function_tag", "provenance_postcode", "provenance_geometry",
    "data_quality_flag",
]


def _resolve_overlaps(gdf: gpd.GeoDataFrame, iou_threshold: float = 0.95) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["_overlap_resolved"] = False
    drop, kept = set(), set()
    indices = list(gdf.index)
    for i, idx in enumerate(indices):
        if idx in drop:
            continue
        for pos in gdf.sindex.query(gdf.at[idx, "geometry"], predicate="intersects"):
            other = indices[pos]
            if pos <= i or other in drop:
                continue
            a, b = gdf.at[idx, "geometry"], gdf.at[other, "geometry"]
            union = a.union(b).area
            if union and a.intersection(b).area / union > iou_threshold:
                winner, loser = (idx, other) if gdf.at[idx, "footprint_area_m2"] >= gdf.at[other, "footprint_area_m2"] else (other, idx)
                kept.add(winner); drop.add(loser)
    for idx in kept - drop:
        gdf.at[idx, "_overlap_resolved"] = True
    return gdf.drop(index=list(drop))


def seven_step_clean(
    gdf: gpd.GeoDataFrame,
    *,
    overlap_resolver: Callable[[gpd.GeoDataFrame, float], gpd.GeoDataFrame] | None = None,
    log_sink: Callable[[str], None] | None = None,
) -> tuple[gpd.GeoDataFrame, list[str]]:
    """Apply the identical geometry-cleaning sequence used by primary sources."""
    messages: list[str] = []
    def emit(payload: dict) -> None:
        line = json.dumps(payload)
        if log_sink is not None:
            log_sink(line)
        messages.append(line)
    before = len(gdf); gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy(); emit({"event": "cleaner_step", "step": 1, "dropped": before - len(gdf), "remaining": len(gdf)})
    before = len(gdf); gdf = gdf[gdf.geom_type.isin(["Polygon", "MultiPolygon"])].copy(); emit({"event": "cleaner_step", "step": 2, "dropped": before - len(gdf), "remaining": len(gdf)})
    before = len(gdf)
    parts = []
    for _, row in gdf.iterrows():
        if row.geometry.geom_type == "MultiPolygon":
            for part_number, part in enumerate(row.geometry.geoms):
                part_row = row.copy(); part_row["osm_id"] = f"{row['osm_id']}_part{part_number}"; part_row["geometry"] = part; parts.append(part_row)
        else:
            parts.append(row)
    if parts:
        gdf = gpd.GeoDataFrame(parts, crs=gdf.crs)
    gdf = gdf.reset_index(drop=True)
    for column in ("levels", "year_built", "underground"):
        if column in gdf:
            values = pd.to_numeric(gdf[column], errors="coerce")
            gdf[column] = values.fillna(0).astype("Int64") if column == "underground" else values.astype("Int64")
    for column in ("height_m", "roof_height_m"):
        if column in gdf:
            gdf[column] = pd.to_numeric(gdf[column], errors="coerce").astype(float)
    delta = len(gdf) - before
    emit({"event": "cleaner_step", "step": 3, "added": max(delta, 0), "dropped": max(-delta, 0), "remaining": len(gdf)})
    gdf.geometry = gdf.geometry.buffer(0)
    before = len(gdf); gdf = gdf[gdf.geom_type == "Polygon"].copy(); emit({"event": "cleaner_step", "step": 4, "dropped": before - len(gdf), "remaining": len(gdf)})
    before = len(gdf); gdf = gdf[gdf.geometry.is_valid].copy(); emit({"event": "cleaner_step", "step": "4b", "dropped": before - len(gdf), "remaining": len(gdf)})
    gdf["footprint_area_m2"] = gdf.geometry.area.astype(float); gdf["perimeter_m"] = gdf.geometry.length.astype(float)
    emit({"event": "cleaner_step", "step": 5, "dropped": 0, "remaining": len(gdf)})
    before = len(gdf); gdf = gdf[gdf["footprint_area_m2"] >= 20.0].copy(); emit({"event": "cleaner_step", "step": 6, "dropped": before - len(gdf), "remaining": len(gdf)})
    before = len(gdf); resolver = overlap_resolver or _resolve_overlaps; gdf = resolver(gdf, 0.95); emit({"event": "cleaner_step", "step": 7, "dropped": before - len(gdf), "remaining": len(gdf)})
    return gdf.reset_index(drop=True), messages


def assign_provenance(gdf: gpd.GeoDataFrame, *, source: str) -> gpd.GeoDataFrame:
    gdf = gdf.copy(); prefix = source.upper()
    missing = lambda value: pd.isna(value) or value == ""
    gdf["provenance_levels"] = gdf["levels"].map(lambda x: f"{prefix}_MISSING" if missing(x) else f"{prefix}_OBSERVED")
    if prefix == "OSM":
        gdf["provenance_height_m"] = gdf.apply(
            lambda row: "OSM_MISSING" if missing(row["height_m"]) else "OSM_OBSERVED_FT" if row.get("_height_was_ft", False) else "OSM_OBSERVED", axis=1
        )
    else:
        gdf["provenance_height_m"] = gdf["height_m"].map(lambda x: f"{prefix}_MISSING" if missing(x) else f"{prefix}_OBSERVED")
    gdf["provenance_year_built"] = gdf["year_built"].map(lambda x: f"{prefix}_MISSING" if missing(x) else f"{prefix}_OBSERVED")
    if prefix == "OSM":
        gdf["provenance_building_tag"] = gdf["building_tag"].map(lambda x: "OSM_GENERIC" if x in ("yes", "", None) else "OSM_OBSERVED")
    else:
        gdf["provenance_building_tag"] = gdf["building_tag"].map(lambda x: f"{prefix}_MISSING" if missing(x) else f"{prefix}_OBSERVED")
    gdf["provenance_function_tag"] = gdf["function_tag"].map(lambda x: f"{prefix}_MISSING" if missing(x) else f"{prefix}_OBSERVED")
    gdf["provenance_postcode"] = gdf["postcode"].map(lambda x: f"{prefix}_MISSING" if missing(x) else f"{prefix}_OBSERVED")
    gdf["provenance_geometry"] = gdf.get("_overlap_resolved", pd.Series(False, index=gdf.index)).map(lambda x: f"{prefix}_OVERLAP_RESOLVED" if x else f"{prefix}_OBSERVED")
    return gdf.drop(columns=[c for c in ("_height_was_ft", "_overlap_resolved") if c in gdf])


def build_quality_flag(gdf: gpd.GeoDataFrame, *, source: str | None = None) -> gpd.GeoDataFrame:
    def flags(row: pd.Series) -> str:
        out = []
        if pd.isna(row.levels): out.append("no_floors")
        if pd.isna(row.height_m): out.append("no_height")
        if source == "OSM":
            if row.building_tag in ("yes", "", None): out.append("generic_tag")
            if row.function_tag == "" and row.building_tag in ("yes", "", None): out.append("no_function")
            if row.provenance_geometry == "OSM_OVERLAP_RESOLVED": out.append("overlap_resolved")
            if row.provenance_height_m == "OSM_OBSERVED_FT": out.append("height_only_ft")
        elif not row.building_tag:
            out.append("no_building_tag")
        if pd.isna(row.year_built): out.append("no_year")
        return ",".join(sorted(out))
    out = gdf.copy(); out["data_quality_flag"] = out.apply(flags, axis=1); return out


def validate_schema(gdf: gpd.GeoDataFrame) -> None:
    cols = list(gdf.columns)
    if len(cols) != 23:
        raise ValueError(f"Schema error: expected 23 columns, got {len(cols)}. Columns: {cols}")
    if cols != SCHEMA_COLUMNS:
        mismatches = [(i, actual, expected) for i, (actual, expected) in enumerate(zip(cols, SCHEMA_COLUMNS)) if actual != expected]
        extra = set(cols) - set(SCHEMA_COLUMNS)
        missing = set(SCHEMA_COLUMNS) - set(cols)
        raise ValueError(f"Schema error: column order mismatch. Mismatches: {mismatches}. Extra: {extra}. Missing: {missing}.")
    for col in ("levels", "year_built", "underground"):
        if str(gdf[col].dtype) != "Int64": raise ValueError(f"Schema error: {col} must be Int64.")
    for col in ("height_m", "roof_height_m", "footprint_area_m2", "perimeter_m"):
        if gdf[col].dtype != "float64": raise ValueError(f"Schema error: {col} must be float64.")
    if not hasattr(gdf["geometry"].dtype, "name") or "geom" not in str(gdf["geometry"].dtype).lower():
        raise ValueError(f"Schema error: 'geometry' must be geometry dtype, got {gdf['geometry'].dtype}.")
    if not gdf["osm_id"].is_unique:
        raise ValueError("Schema error: 'osm_id' column is not unique.")


def serialize(gdf: gpd.GeoDataFrame, output_dir: Path | str, *, log_lines: list[str] | None = None) -> None:
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    (output / "01_buildings_clean.log").write_text("\n".join((log_lines or []) + [json.dumps({"event": "serialize_complete", "n_rows": len(gdf)})]) + "\n", encoding="utf-8")
    gdf.to_file(output / "01_buildings_clean.gpkg", layer="buildings", driver="GPKG")
    roles = {c: "raw_tag" for c in SCHEMA_COLUMNS}
    roles.update({
        "geometry": "geometry", "osm_id": "identity", "crs_utm": "identity",
        "footprint_area_m2": "computed", "perimeter_m": "computed",
        "surplus_tags": "surplus", "provenance_levels": "provenance",
        "provenance_height_m": "provenance", "provenance_year_built": "provenance",
        "provenance_building_tag": "provenance", "provenance_function_tag": "provenance",
        "provenance_postcode": "provenance", "provenance_geometry": "provenance",
        "data_quality_flag": "quality",
    })
    (output / "01_buildings_clean.schema.json").write_text(json.dumps([{"name": c, "dtype": str(gdf[c].dtype), "provenance_role": roles[c]} for c in SCHEMA_COLUMNS], indent=2), encoding="utf-8")


def finalize_footprints(gdf: gpd.GeoDataFrame, *, source: str, output_dir: Path | str | None = None) -> gpd.GeoDataFrame:
    if gdf.crs is None: raise ValueError("Source frame must have a CRS.")
    utm = gdf.estimate_utm_crs(); gdf = gdf.to_crs(utm); gdf["crs_utm"] = utm.to_string()
    gdf, logs = seven_step_clean(gdf); gdf = assign_provenance(gdf, source=source); gdf = build_quality_flag(gdf, source=source)
    missing = [c for c in SCHEMA_COLUMNS if c not in gdf]
    if missing: raise ValueError(f"Schema error: missing required columns {missing}")
    gdf = gdf[SCHEMA_COLUMNS]; validate_schema(gdf)
    if output_dir is not None: serialize(gdf, output_dir, log_lines=logs)
    return gdf
