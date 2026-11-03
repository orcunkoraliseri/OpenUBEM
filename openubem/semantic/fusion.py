"""External-data fusion precedence layer (Input-Imputation arc, Phase D, T12).

A fused value is an observation, not a fitted quantity -- zero-fitted-params
is satisfied by construction (plan §2 rule 3), but the discipline is still
test-guarded: no source may ever read an EUI column, and no source-order /
join-tolerance / confidence cut-point here is ever tuned to a simulated-EUI
target (all cited below, never swept).

`fuse(gdf, attr, cfg)` walks `precedence_for(attr, cfg)` -- the M07-ordered,
*available* sources for `attr` -- and returns the `(value, token)` two-Series
tier contract `imputation._fusion_tier` consumes directly (parent §5D).
Direct field join -> HIGH; a value *derived* from a joined one (e.g.
`levels = max(1, LiDAR_height // FLOOR_TO_FLOOR_M)`) -> MED; a miss returns
null and falls through -- fusion never emits LOW (plan §2 rule 4).

Targets = morphology/semantic only (identical to the Phase-C ML exclusion
set): `height`/`height_m`, `levels`, `year_built`, `use_class`. Footprint
completeness is out of scope (M07 Table 4 "do not impute geometry").
"""
from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd

from openubem.config import FLOOR_TO_FLOOR_M

# ── zero-fitted-params structural guard (plan §2 rule 3 / §5I) ──────────────

def _assert_no_eui_columns(columns) -> None:
    """Mirrors `imputation._assert_no_eui_leakage` -- no fusion adapter may
    ever read an EUI/`total_eui`/`*_eui*` column."""
    leaked = [c for c in columns if "eui" in str(c).lower()]
    if leaked:
        raise ValueError(
            f"fusion: zero-fitted-params violation -- EUI column(s) {leaked} "
            "must never be read by a fusion source (plan §2 rule 3)."
        )


# ── join geometry tolerance (M07 Table 1 join keys; cited, never EUI-swept) ─
# Centroid-within-polygon primary; else nearest-within-fixed-tolerance
# (plan §4 "Join geometry tolerance" row).
NEAREST_TOLERANCE_M = 10.0


def _spatial_join_positions(target_gdf, source_gdf) -> pd.Series:
    """Centroid-within-polygon primary, else nearest-within-tolerance.

    Returns a `pd.Series` aligned to `target_gdf.index` holding the matched
    row's *positional* index into `source_gdf` (float, NaN = no match).
    Reprojects `source_gdf` into `target_gdf`'s CRS first; if the working CRS
    is geographic, both layers are reprojected into a metric CRS estimated
    from `target_gdf` (mirrors `osm_fetcher.ingest_buildings`'s
    `estimate_utm_crs()` convention) so `NEAREST_TOLERANCE_M` means metres.
    """
    n = len(target_gdf)
    out = pd.Series(np.nan, index=target_gdf.index, dtype=float)
    if n == 0 or len(source_gdf) == 0:
        return out
    if "geometry" not in getattr(target_gdf, "columns", []):
        return out

    work = target_gdf
    src = source_gdf
    if work.crs is not None and src.crs is not None and work.crs != src.crs:
        src = src.to_crs(work.crs)
    work_crs = work.crs
    if work_crs is not None and work_crs.is_geographic:
        work_crs = work.estimate_utm_crs()
        work = work.to_crs(work_crs)
        src = src.to_crs(work_crs)

    centroids = gpd.GeoDataFrame(geometry=work.geometry.centroid, index=work.index, crs=work_crs)
    src_geom = src[["geometry"]].reset_index(drop=True)
    src_geom["_src_pos"] = np.arange(len(src_geom))

    within = gpd.sjoin(centroids, src_geom, predicate="within", how="left")
    within = within[~within.index.duplicated(keep="first")]
    matched = within["_src_pos"].reindex(target_gdf.index)

    miss_idx = matched.index[matched.isna()]
    if len(miss_idx) > 0:
        nearest = gpd.sjoin_nearest(
            centroids.loc[miss_idx], src_geom, max_distance=NEAREST_TOLERANCE_M,
            how="left", distance_col="_dist",
        )
        nearest = nearest[~nearest.index.duplicated(keep="first")]
        matched.loc[nearest.index] = nearest["_src_pos"]

    return matched


def _empty_value(gdf, attr: str) -> pd.Series:
    is_numeric = attr in gdf.columns and pd.api.types.is_numeric_dtype(gdf[attr])
    if is_numeric:
        return pd.Series(np.nan, index=gdf.index, dtype=float)
    return pd.Series([None] * len(gdf), index=gdf.index, dtype=object)


# ── use_class raw-category crosswalk (reuses the existing OSM taxonomy --
# Overture's `class`/`subtype` vocabulary overlaps it; not a new invented
# mapping) ────────────────────────────────────────────────────────────────

def _load_use_class_crosswalk() -> dict:
    raw = json.loads(files("openubem.data").joinpath("osm_to_use_class.json").read_text(encoding="utf-8"))
    return raw["tag_to_use_class"]


_USE_CLASS_CROSSWALK = _load_use_class_crosswalk()


def _crosswalk_use_class(raw_series: pd.Series) -> pd.Series:
    return raw_series.astype(object).map(
        lambda v: _USE_CLASS_CROSSWALK.get(str(v).lower()) if pd.notna(v) else None
    )


# ── T12.1 -- FusionSource protocol + registry ────────────────────────────────

class FusionSource:
    """One external-data source in the fusion precedence chain (M07 Part C §1).

    `name` is the registry key / `config.FUSION_SOURCES_BY_TARGET` entry;
    `source_token` is the `FUSED_<SOURCE>_<TIER>` provenance-token segment.
    """

    name: str = ""
    source_token: str = ""

    def available(self, cfg) -> bool:
        raise NotImplementedError

    def join(self, gdf, attr: str, cfg) -> "tuple[pd.Series, pd.Series]":
        """Returns `(value, derived)`, both aligned to `gdf.index`. `value`
        is NaN/None where this source has no join for that row; `derived[i]`
        is True when `value[i]` is computed FROM a joined field (-> MED)
        rather than a direct field match (-> HIGH)."""
        raise NotImplementedError


_REGISTRY: "dict[str, type[FusionSource]]" = {}


def register_source(cls):
    _REGISTRY[cls.name] = cls
    return cls


def get_source(name: str) -> FusionSource:
    if name not in _REGISTRY:
        raise KeyError(f"fusion: unknown source {name!r}. Registered: {sorted(_REGISTRY)}")
    return _REGISTRY[name]()


def _resolve_cfg(cfg):
    if cfg is not None:
        return cfg
    from openubem import config
    return config


def precedence_for(attr: str, cfg=None) -> "list[FusionSource]":
    """M07-ordered, *available* sources for `attr` (plan §5E table), read
    from `cfg.FUSION_SOURCES_BY_TARGET` (config resolved at call time --
    rule/fact C)."""
    cfg = _resolve_cfg(cfg)
    order = getattr(cfg, "FUSION_SOURCES_BY_TARGET", {}).get(attr, ())
    out = []
    for name in order:
        src = get_source(name)
        if src.available(cfg):
            out.append(src)
    return out


# ── T12.2 -- Overture source ─────────────────────────────────────────────────

_OVERTURE_ATTR_COLUMN = {
    "height": "height", "height_m": "height", "levels": "levels",
    "year_built": "year_built", "use_class": "use_class",
}

# `fetch_overture()` unconditionally re-normalizes its input (E-UTCI-13):
# reading an already-normalized cache (e.g. the height-cache module's cached
# output) through it a second time nulls `levels`/`use_class`, since the
# raw-schema columns `_normalize()` looks for (`num_floors`, `class`) no
# longer exist. `height` alone survives because its column name is stable
# across both passes.
#
# OPEN-13: derived from the fetcher's own tuple (not hand-copied) so a future
# schema change there fails a test instead of silently disabling this guard.
from openubem.acquisition.overture_fetcher import _NORMALIZED_COLUMNS as _OVERTURE_FETCHER_COLUMNS
_NORMALIZED_OVERTURE_COLUMNS = set(_OVERTURE_FETCHER_COLUMNS)


def _load_overture_layer(cfg) -> gpd.GeoDataFrame:
    """Idempotent load for `OvertureSource.join`. If `FUSION_OVERTURE_SLICE_PATH`
    already carries normalized schema on disk, read it directly and skip the
    second normalization pass; a raw-schema slice or a live `endpoint` pull
    still goes through `fetch_overture()` exactly as before."""
    from openubem.acquisition.overture_fetcher import fetch_overture

    slice_path = getattr(cfg, "FUSION_OVERTURE_SLICE_PATH", None)
    if slice_path is not None:
        raw = gpd.read_parquet(slice_path)
        if set(raw.columns) == _NORMALIZED_OVERTURE_COLUMNS:
            return raw

    return fetch_overture(
        slice_path=slice_path,
        endpoint=getattr(cfg, "FUSION_OVERTURE_ENDPOINT", None),
    )


@register_source
class OvertureSource(FusionSource):
    name = "overture"
    source_token = "OVERTURE"

    def available(self, cfg) -> bool:
        return bool(getattr(cfg, "FUSION_OVERTURE_SLICE_PATH", None)) or bool(
            getattr(cfg, "FUSION_OVERTURE_ENDPOINT", None)
        )

    def join(self, gdf, attr: str, cfg):
        value = _empty_value(gdf, attr)
        derived = pd.Series(False, index=gdf.index)
        col = _OVERTURE_ATTR_COLUMN.get(attr)
        if col is None or "geometry" not in getattr(gdf, "columns", []):
            return value, derived

        layer = _load_overture_layer(cfg)
        _assert_no_eui_columns(list(gdf.columns) + list(layer.columns))
        if len(layer) == 0:
            return value, derived

        matched_pos = _spatial_join_positions(gdf, layer)
        raw_col = layer[col].reset_index(drop=True)
        hit_idx = matched_pos.index[matched_pos.notna()]
        for idx in hit_idx:
            pos = int(matched_pos.loc[idx])
            v = raw_col.iloc[pos]
            if pd.notna(v):
                value.loc[idx] = v

        if attr == "use_class":
            value = _crosswalk_use_class(value)

        return value, derived


# ── T12.3 -- LiDAR nDSM zonal source ─────────────────────────────────────────

def _zonal_mean_height(gdf, raster_path) -> pd.Series:
    """Per-footprint zonal mean height from an nDSM raster -- manual
    `rasterio.mask` + numpy (no `rasterstats`, plan §2 rule 8)."""
    import rasterio
    from rasterio.mask import mask as rio_mask

    out = pd.Series(np.nan, index=gdf.index, dtype=float)
    with rasterio.open(raster_path) as src:
        work = gdf
        if gdf.crs is not None and src.crs is not None and gdf.crs != src.crs:
            work = gdf.to_crs(src.crs)
        for idx, geom in zip(work.index, work.geometry):
            if geom is None or geom.is_empty:
                continue
            try:
                data, _ = rio_mask(src, [geom.__geo_interface__], crop=True, nodata=src.nodata)
            except ValueError:
                continue  # geometry does not overlap the raster extent
            arr = data[0].astype(float)
            if src.nodata is not None:
                arr = np.where(arr == src.nodata, np.nan, arr)
            valid = arr[~np.isnan(arr)]
            if valid.size == 0:
                continue
            out.loc[idx] = float(valid.mean())
    return out


@register_source
class LidarSource(FusionSource):
    name = "lidar"
    source_token = "LIDAR"

    def available(self, cfg) -> bool:
        path = getattr(cfg, "FUSION_LIDAR_NDSM_PATH", None)
        return bool(path) and Path(path).exists()

    def join(self, gdf, attr: str, cfg):
        value = _empty_value(gdf, attr)
        derived = pd.Series(False, index=gdf.index)
        if attr not in ("height", "height_m", "levels") or "geometry" not in getattr(gdf, "columns", []):
            return value, derived

        _assert_no_eui_columns(gdf.columns)
        heights = _zonal_mean_height(gdf, getattr(cfg, "FUSION_LIDAR_NDSM_PATH"))
        hit = heights.notna()
        if not hit.any():
            return value, derived

        if attr == "levels":
            floors = np.maximum(1.0, np.floor(heights.loc[hit] / FLOOR_TO_FLOOR_M))
            value.loc[hit] = floors
            derived.loc[hit] = True  # levels-from-height -> MED (plan §2 rule 4)
        else:
            value.loc[hit] = heights.loc[hit]
        return value, derived


# ── T12.3 -- Assessor / municipal join source ────────────────────────────────

def _load_assessor(path):
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return gpd.read_file(path)


_ASSESSOR_ATTRS = ("year_built", "use_class", "levels")


@register_source
class AssessorSource(FusionSource):
    name = "assessor"
    source_token = "ASSESSOR"

    def available(self, cfg) -> bool:
        path = getattr(cfg, "FUSION_ASSESSOR_PATH", None)
        return bool(path) and Path(path).exists()

    def join(self, gdf, attr: str, cfg):
        value = _empty_value(gdf, attr)
        derived = pd.Series(False, index=gdf.index)
        if attr not in _ASSESSOR_ATTRS:
            return value, derived

        field_map = getattr(cfg, "FUSION_ASSESSOR_FIELDS", {}) or {}
        field = field_map.get(attr)
        if field is None:
            return value, derived

        assessor = _load_assessor(getattr(cfg, "FUSION_ASSESSOR_PATH"))
        _assert_no_eui_columns(list(gdf.columns) + list(assessor.columns))
        if field not in assessor.columns:
            return value, derived

        pin_field = field_map.get("pin")
        pin_gdf_col = field_map.get("pin_gdf_col", pin_field)
        if pin_field and pin_field in assessor.columns and pin_gdf_col in getattr(gdf, "columns", []):
            lookup = assessor.drop_duplicates(subset=[pin_field]).set_index(pin_field)[field]
            for idx in gdf.index:
                pin = gdf.at[idx, pin_gdf_col]
                if pd.notna(pin) and pin in lookup.index:
                    v = lookup.loc[pin]
                    if pd.notna(v):
                        value.loc[idx] = v
        elif isinstance(assessor, gpd.GeoDataFrame) and "geometry" in getattr(gdf, "columns", []):
            matched_pos = _spatial_join_positions(gdf, assessor)
            raw_col = assessor[field].reset_index(drop=True)
            hit_idx = matched_pos.index[matched_pos.notna()]
            for idx in hit_idx:
                pos = int(matched_pos.loc[idx])
                v = raw_col.iloc[pos]
                if pd.notna(v):
                    value.loc[idx] = v

        return value, derived


# ── T12.4 -- fuse() precedence walk (consumed by imputation._fusion_tier) ───

def fuse(gdf, attr: str, cfg=None) -> "tuple[pd.Series, pd.Series]":
    """Walk `precedence_for(attr, cfg)`; first available source with a
    non-null join wins per row. Returns the `(value, token)` two-Series tier
    contract (parent §5D) -- `FUSED_<SOURCE>_HIGH` (direct) or
    `FUSED_<SOURCE>_MED` (derived); never `_LOW` (plan §2 rule 4)."""
    cfg = _resolve_cfg(cfg)
    _assert_no_eui_columns(gdf.columns)

    value = _empty_value(gdf, attr)
    token = pd.Series([None] * len(gdf), index=gdf.index, dtype=object)
    remaining = pd.Series(True, index=gdf.index)

    for source in precedence_for(attr, cfg):
        if not remaining.any():
            break
        src_value, src_derived = source.join(gdf, attr, cfg)
        hit = remaining & src_value.notna()
        if not hit.any():
            continue
        value.loc[hit] = src_value.loc[hit]
        for idx in gdf.index[hit]:
            suffix = "MED" if bool(src_derived.loc[idx]) else "HIGH"
            token.loc[idx] = f"FUSED_{source.source_token}_{suffix}"
        remaining = remaining & ~hit

    return value, token
