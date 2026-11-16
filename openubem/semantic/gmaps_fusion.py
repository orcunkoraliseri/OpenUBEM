"""Opt-in Google Maps Platform fusion sources registered with ``fusion``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd

from openubem.acquisition.gmaps_places_fetcher import (
    fetch_places_nearby,
    match_places_to_buildings,
)
from openubem.acquisition.gmaps_solar_fetcher import derive_ndsm_from_solar_dsm
from openubem.semantic import fusion


def _cfg_get(cfg: Any, key: str, default: Any = None) -> Any:
    """Reads a configuration setting from either a mapping or attribute object.

    Args:
        cfg: Configuration module, ``SimpleNamespace``, or ``dict``.
        key: Configuration attribute or key name.
        default: Value returned when ``key`` is absent.

    Returns:
        Resolved configuration value or ``default``.
    """
    if isinstance(cfg, dict):
        return cfg.get(key, default)
    return getattr(cfg, key, default)


def _existing_file(path_like: Any) -> Path | None:
    """Converts a candidate path setting into an existing ``Path`` if present.

    Args:
        path_like: Path, string, or ``None``.

    Returns:
        Resolved ``Path`` if non-empty and pointing to an existing file, else
        ``None``.
    """
    if not path_like:
        return None
    candidate = Path(path_like)
    return candidate if candidate.is_file() else None


def _load_vector_layer(path: Path) -> gpd.GeoDataFrame:
    """Reads a vector layer from GeoParquet, GeoJSON, or GeoPackage formats.

    Args:
        path: Input vector file path.

    Returns:
        Loaded ``gpd.GeoDataFrame``.

    Raises:
        ValueError: If the file suffix is not supported.
    """
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return gpd.read_parquet(path)
    if suffix in {".geojson", ".gpkg", ".shp"}:
        return gpd.read_file(path)
    raise ValueError(f"Unsupported vector layer extension: {suffix!r}")


@fusion.register_source
class GmapsSolarSource(fusion.FusionSource):
    """Solar API DSM/nDSM height fusion source (opt-in ``gmaps_solar``)."""

    name = "gmaps_solar"
    source_token = "GMAPSSOLAR"

    def available(self, cfg: Any) -> bool:
        """Checks whether a Solar nDSM or DSM GeoTIFF is configured on disk.

        Args:
            cfg: Runtime configuration object or dictionary.

        Returns:
            ``True`` when either ``FUSION_GMAPS_SOLAR_NDSM_PATH`` or
            ``FUSION_GMAPS_SOLAR_DSM_PATH`` exists on disk.
        """
        ndsm_path = _existing_file(_cfg_get(cfg, "FUSION_GMAPS_SOLAR_NDSM_PATH"))
        dsm_path = _existing_file(_cfg_get(cfg, "FUSION_GMAPS_SOLAR_DSM_PATH"))
        return ndsm_path is not None or dsm_path is not None

    def join(
        self,
        gdf: gpd.GeoDataFrame,
        attr: str,
        cfg: Any,
    ) -> tuple[pd.Series, pd.Series]:
        """Joins building heights or derived floor counts from Solar DSM/nDSM.

        Args:
            gdf: Target building footprints GeoDataFrame.
            attr: Target semantic attribute (``height``, ``height_m``, ``levels``).
            cfg: Runtime configuration object or dictionary.

        Returns:
            Tuple ``(value_series, derived_series)`` aligned to ``gdf.index``.
        """
        value = fusion._empty_value(gdf, attr)
        derived = pd.Series(False, index=gdf.index, dtype="bool")
        if attr not in ("height", "height_m", "levels") or (
            "geometry" not in getattr(gdf, "columns", [])
        ):
            return value, derived

        fusion._assert_no_eui_columns(gdf.columns)
        ndsm_path = _existing_file(_cfg_get(cfg, "FUSION_GMAPS_SOLAR_NDSM_PATH"))
        is_derived = bool(_cfg_get(cfg, "FUSION_GMAPS_SOLAR_DERIVED", False))

        if ndsm_path is None:
            dsm_path = _existing_file(_cfg_get(cfg, "FUSION_GMAPS_SOLAR_DSM_PATH"))
            if dsm_path is None:
                return value, derived
            dem_path = _existing_file(_cfg_get(cfg, "FUSION_GMAPS_SOLAR_DEM_PATH"))
            cache_dir = Path(_cfg_get(cfg, "GMAPS_CACHE_DIR", dsm_path.parent))
            target_ndsm = cache_dir / f"{dsm_path.stem}_ndsm.tif"
            ndsm_path, is_derived = derive_ndsm_from_solar_dsm(
                dsm_path=dsm_path,
                out_ndsm_path=target_ndsm,
                dem_path=dem_path,
            )

        heights = fusion._zonal_mean_height(gdf, ndsm_path)
        hit = heights.notna() & (heights > 0.0)
        if not hit.any():
            return value, derived

        if attr == "levels":
            floors = np.maximum(
                1.0,
                np.floor(heights.loc[hit] / fusion.FLOOR_TO_FLOOR_M),
            )
            value.loc[hit] = floors
            derived.loc[hit] = True
        else:
            value.loc[hit] = heights.loc[hit]
            derived.loc[hit] = bool(is_derived)
        return value, derived


@fusion.register_source
class GmapsPlacesSource(fusion.FusionSource):
    """Places API (New) semantic class fusion source (``gmaps_places``)."""

    name = "gmaps_places"
    source_token = "GMAPSPLACES"

    def available(self, cfg: Any) -> bool:
        """Checks whether a local Google Places slice file exists.

        Args:
            cfg: Runtime configuration object or dictionary.

        Returns:
            ``True`` if ``FUSION_GMAPS_PLACES_PATH`` points to a file.
        """
        return _existing_file(_cfg_get(cfg, "FUSION_GMAPS_PLACES_PATH")) is not None

    def join(
        self,
        gdf: gpd.GeoDataFrame,
        attr: str,
        cfg: Any,
    ) -> tuple[pd.Series, pd.Series]:
        """Joins ``use_class`` or ``function_tag`` from Google Places POIs.

        Polygon containment yields ``derived=False`` (``FUSED_GMAPSPLACES_HIGH``)
        and ``10 m`` centroid fallback yields ``derived=True``
        (``FUSED_GMAPSPLACES_MED``), breaking ties by POI energy intensity.

        Args:
            gdf: Target building footprints GeoDataFrame.
            attr: Target semantic attribute (``use_class`` or ``function_tag``).
            cfg: Runtime configuration object or dictionary.

        Returns:
            Tuple ``(value_series, derived_series)`` aligned to ``gdf.index``.
        """
        value = fusion._empty_value(gdf, attr)
        derived = pd.Series(False, index=gdf.index, dtype="bool")
        if attr not in ("use_class", "function_tag") or (
            "geometry" not in getattr(gdf, "columns", [])
        ):
            return value, derived

        fusion._assert_no_eui_columns(gdf.columns)
        places_path = _existing_file(_cfg_get(cfg, "FUSION_GMAPS_PLACES_PATH"))
        if places_path is None:
            return value, derived

        places_gdf = fetch_places_nearby(slice_path=places_path)
        if places_gdf.empty:
            return value, derived

        matched_uc, matched_ft, _pt, _cnt, matched_derived = (
            match_places_to_buildings(
                gdf,
                places_gdf,
                tolerance_m=fusion.NEAREST_TOLERANCE_M,
            )
        )
        chosen = matched_uc if attr == "use_class" else matched_ft
        hit = chosen.notna()
        if not hit.any():
            return value, derived

        value.loc[hit] = chosen.loc[hit]
        derived.loc[hit] = matched_derived.loc[hit].astype(bool)
        if attr == "use_class":
            value = fusion._crosswalk_use_class(value)
        return value, derived


@fusion.register_source
class StreetViewInsightsSource(fusion.FusionSource):
    """Street View Insights facade/level fusion source (``gmaps_svi``)."""

    name = "gmaps_svi"
    source_token = "GMAPSSVI"

    def available(self, cfg: Any) -> bool:
        """Checks whether a local Street View Insights vector slice exists.

        Args:
            cfg: Runtime configuration object or dictionary.

        Returns:
            ``True`` when ``FUSION_GMAPS_SVI_PATH`` points to a file.
        """
        return _existing_file(_cfg_get(cfg, "FUSION_GMAPS_SVI_PATH")) is not None

    def join(
        self,
        gdf: gpd.GeoDataFrame,
        attr: str,
        cfg: Any,
    ) -> tuple[pd.Series, pd.Series]:
        """Joins facade attributes from Street View Insights vector slices.

        Street View-derived attributes are always flagged ``derived=True``
        (``FUSED_GMAPSSVI_MED``).

        Args:
            gdf: Target building footprints GeoDataFrame.
            attr: Target attribute requested by ``fusion.fuse()``.
            cfg: Runtime configuration object or dictionary.

        Returns:
            Tuple ``(value_series, derived_series)`` aligned to ``gdf.index``.
        """
        value = fusion._empty_value(gdf, attr)
        derived = pd.Series(False, index=gdf.index, dtype="bool")
        svi_path = _existing_file(_cfg_get(cfg, "FUSION_GMAPS_SVI_PATH"))
        if svi_path is None or "geometry" not in getattr(gdf, "columns", []):
            return value, derived

        fusion._assert_no_eui_columns(gdf.columns)
        layer = _load_vector_layer(svi_path)
        fusion._assert_no_eui_columns(layer.columns)
        if layer.empty:
            return value, derived

        default_fields = {
            "levels": "levels_observed",
            "wwr": "wwr_observed",
            "height_m": "height_m",
            "height": "height_m",
        }
        user_fields = _cfg_get(cfg, "FUSION_GMAPS_SVI_FIELDS", {}) or {}
        field_map = {**default_fields, **user_fields}
        col = field_map.get(attr, attr)
        if col not in layer.columns:
            return value, derived

        matched_pos = fusion._spatial_join_positions(gdf, layer)
        raw_col = layer[col].reset_index(drop=True)
        for idx in matched_pos.index[matched_pos.notna()]:
            pos = int(matched_pos.loc[idx])
            raw_val = raw_col.iloc[pos]
            if pd.notna(raw_val):
                value.loc[idx] = raw_val
                derived.loc[idx] = True

        return value, derived
