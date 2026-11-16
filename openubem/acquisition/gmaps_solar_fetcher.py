"""Google Maps Solar API client, DSM/nDSM processor, and roof/canopy extractors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import Resampling, reproject
from scipy.ndimage import minimum_filter

from openubem.acquisition.gmaps_client import (
    GmapsApiError,
    GmapsHttpClient,
    assert_no_eui_columns,
)
from openubem.semantic import provenance

_SOLAR_BASE_URL = "https://solar.googleapis.com/v1"
_BUILDING_INSIGHTS_URL = f"{_SOLAR_BASE_URL}/buildingInsights:findClosest"
_DATA_LAYERS_URL = f"{_SOLAR_BASE_URL}/dataLayers:get"
_NODATA_OUT = -9999.0


@dataclass(frozen=True)
class SolarBuildingSummary:
    """Normalized building rooftop attributes parsed from Solar buildingInsights.

    Attributes:
        roof_area_m2: Whole-roof horizontal projection area in square meters.
        sunshine_quantiles: Solar irradiance quantiles from wholeRoofStats.
        roof_pitch_deg: Area-weighted mean roof pitch angle in degrees.
        roof_azimuth_deg: Azimuth in degrees of the largest roof segment.
        roof_segment_count: Number of detected roof segments.
        max_panel_count: Maximum estimated solar array panel count.
        max_sunshine_hours_per_year: Peak annual sunshine hours across roof.
        roof_elevation_m: Mean plane elevation at segment centers in meters.
    """

    roof_area_m2: float | None
    sunshine_quantiles: list[float] | None
    roof_pitch_deg: float | None
    roof_azimuth_deg: float | None
    roof_segment_count: int
    max_panel_count: int | None
    max_sunshine_hours_per_year: float | None
    roof_elevation_m: float | None


def _opt_float(value: Any) -> float | None:
    """Safely converts an arbitrary JSON value to ``float`` or ``None``.

    Args:
        value: Input scalar value from decoded JSON.

    Returns:
        Finite Python ``float`` if convertible, otherwise ``None``.
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if np.isfinite(parsed) else None


def _opt_int(value: Any) -> int | None:
    """Safely converts an arbitrary JSON value to ``int`` or ``None``.

    Args:
        value: Input scalar value from decoded JSON.

    Returns:
        Python ``int`` if convertible, otherwise ``None``.
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_building_insights(payload: dict[str, Any]) -> SolarBuildingSummary:
    """Parses a Google Maps Solar API ``buildingInsights`` response payload.

    Args:
        payload: Decoded JSON response from ``buildingInsights:findClosest``.

    Returns:
        Structured :class:`SolarBuildingSummary` with normalized roof metrics.
    """
    potential = payload.get("solarPotential") or {}
    whole_stats = potential.get("wholeRoofStats") or {}
    segments = potential.get("roofSegmentStats") or []

    quantiles_raw = whole_stats.get("sunshineQuantiles")
    quantiles: list[float] | None = None
    if isinstance(quantiles_raw, list) and quantiles_raw:
        parsed_q = [_opt_float(val) for val in quantiles_raw]
        quantiles = [val for val in parsed_q if val is not None] or None

    roof_area_m2 = _opt_float(whole_stats.get("areaMeters2"))
    max_panel_count = _opt_int(potential.get("maxArrayPanelsCount"))
    max_sunshine = _opt_float(potential.get("maxSunshineHoursPerYear"))

    pitch_vals: list[float] = []
    pitch_weights: list[float] = []
    elev_vals: list[float] = []
    dominant_area = -1.0
    dominant_azimuth: float | None = None

    for seg in segments:
        if not isinstance(seg, dict):
            continue
        seg_stats = seg.get("stats") or {}
        seg_area = _opt_float(seg_stats.get("areaMeters2"))
        seg_pitch = _opt_float(seg.get("pitchDegrees"))
        seg_azimuth = _opt_float(seg.get("azimuthDegrees"))
        seg_elev = _opt_float(seg.get("planeHeightAtCenterMeters"))

        weight = seg_area if (seg_area is not None and seg_area > 0.0) else 1.0
        if seg_pitch is not None:
            pitch_vals.append(seg_pitch)
            pitch_weights.append(weight)
        if seg_elev is not None:
            elev_vals.append(seg_elev)
        if seg_azimuth is not None and weight > dominant_area:
            dominant_area = weight
            dominant_azimuth = seg_azimuth

    roof_pitch_deg: float | None = None
    if pitch_vals:
        roof_pitch_deg = float(np.average(pitch_vals, weights=pitch_weights))
    roof_elev_m: float | None = (
        float(np.mean(elev_vals)) if elev_vals else None
    )

    return SolarBuildingSummary(
        roof_area_m2=roof_area_m2,
        sunshine_quantiles=quantiles,
        roof_pitch_deg=roof_pitch_deg,
        roof_azimuth_deg=dominant_azimuth,
        roof_segment_count=len(segments),
        max_panel_count=max_panel_count,
        max_sunshine_hours_per_year=max_sunshine,
        roof_elevation_m=roof_elev_m,
    )


def fetch_building_insights(
    lat: float,
    lon: float,
    *,
    client: GmapsHttpClient | None = None,
    required_quality: str = "MEDIUM",
) -> dict[str, Any]:
    """Queries Solar API ``buildingInsights:findClosest`` for a building centroid.

    Args:
        lat: WGS 84 latitude in decimal degrees.
        lon: WGS 84 longitude in decimal degrees.
        client: Optional cached :class:`GmapsHttpClient` instance.
        required_quality: Minimum Solar imagery quality tier
            (``"LOW"``, ``"MEDIUM"``, or ``"HIGH"``).

    Returns:
        Raw JSON payload returned by the Solar API.
    """
    http = client or GmapsHttpClient()
    params = {
        "location.latitude": round(float(lat), 7),
        "location.longitude": round(float(lon), 7),
        "requiredQuality": required_quality,
    }
    return http.get_json(_BUILDING_INSIGHTS_URL, params=params, auth_mode="query")


def download_solar_datalayers(
    lat: float,
    lon: float,
    *,
    radius_meters: float = 100.0,
    view: str = "FULL_LAYERS",
    required_quality: str = "MEDIUM",
    pixel_size_meters: float = 0.5,
    out_dir: Path | None = None,
    client: GmapsHttpClient | None = None,
) -> dict[str, Path | str | None]:
    """Fetches and downloads Solar API ``dataLayers`` GeoTIFF rasters.

    Args:
        lat: Center WGS 84 latitude in decimal degrees.
        lon: Center WGS 84 longitude in decimal degrees.
        radius_meters: Search radius around centroid in meters.
        view: Solar ``dataLayers`` view selector (default ``"FULL_LAYERS"``).
        required_quality: Minimum acceptable Solar imagery quality.
        pixel_size_meters: Output ground pixel resolution in meters.
        out_dir: Optional directory in which to store named layer GeoTIFFs.
        client: Optional cached :class:`GmapsHttpClient` instance.

    Returns:
        Dictionary mapping layer keys (``dsm_path``, ``rgb_path``,
        ``mask_path``, ``annual_flux_path``, ``monthly_flux_path``,
        ``imagery_quality``) to downloaded ``Path`` objects or strings.
    """
    http = client or GmapsHttpClient()
    params = {
        "location.latitude": round(float(lat), 7),
        "location.longitude": round(float(lon), 7),
        "radiusMeters": float(radius_meters),
        "view": view,
        "requiredQuality": required_quality,
        "pixelSizeMeters": float(pixel_size_meters),
    }
    manifest = http.get_json(_DATA_LAYERS_URL, params=params, auth_mode="query")

    layer_map = {
        "dsmUrl": ("dsm_path", "solar_dsm.tif"),
        "rgbUrl": ("rgb_path", "solar_rgb.tif"),
        "maskUrl": ("mask_path", "solar_mask.tif"),
        "annualFluxUrl": ("annual_flux_path", "solar_annual_flux.tif"),
        "monthlyFluxUrl": ("monthly_flux_path", "solar_monthly_flux.tif"),
    }
    result: dict[str, Path | str | None] = {
        "imagery_quality": manifest.get("imageryQuality"),
        "dsm_path": None,
        "rgb_path": None,
        "mask_path": None,
        "annual_flux_path": None,
        "monthly_flux_path": None,
    }
    for api_key_name, (out_key, filename) in layer_map.items():
        url = manifest.get(api_key_name)
        if not url:
            continue
        dest = (Path(out_dir) / filename) if out_dir is not None else None
        result[out_key] = http.download_binary(
            str(url),
            dest_path=dest,
            suffix=".tif",
            auth_mode="query",
        )
    return result


def _read_dsm_array(dsm_path: Path) -> tuple[np.ndarray, dict[str, Any], np.ndarray]:
    """Reads a DSM GeoTIFF as float32 with a boolean validity mask.

    Args:
        dsm_path: Path to the DSM GeoTIFF raster.

    Returns:
        Tuple ``(dsm_float32, profile, valid_mask)``.
    """
    with rasterio.open(dsm_path) as src:
        dsm = src.read(1).astype(np.float32)
        profile = src.profile.copy()
        nodata = src.nodata
    valid = np.isfinite(dsm)
    if nodata is not None:
        valid &= dsm != np.float32(nodata)
    return dsm, profile, valid


def _compute_ndsm_array(
    dsm: np.ndarray,
    profile: dict[str, Any],
    valid: np.ndarray,
    *,
    dem_path: Path | None = None,
    ground_window_m: float = 35.0,
) -> tuple[np.ndarray, bool]:
    """Computes nDSM heights from a DSM via DEM subtraction or morphology.

    Args:
        dsm: DSM height array in meters above datum.
        profile: Rasterio profile dictionary defining CRS and transform.
        valid: Boolean mask of finite non-nodata DSM pixels.
        dem_path: Optional bare-earth DEM raster to reproject and subtract.
        ground_window_m: Sliding minimum window size in meters when
            ``dem_path`` is ``None``.

    Returns:
        Tuple ``(ndsm_float32, is_derived)`` where ``is_derived`` is ``False``
        when a true bare-earth DEM was subtracted and ``True`` for the
        morphological ``minimum_filter`` fallback.
    """
    out = np.full(dsm.shape, _NODATA_OUT, dtype=np.float32)
    if not valid.any():
        return out, dem_path is None

    if dem_path is not None:
        with rasterio.open(dem_path) as dem_src:
            dem_data = dem_src.read(1).astype(np.float32)
            dem_aligned = np.full(dsm.shape, np.nan, dtype=np.float32)
            reproject(
                source=dem_data,
                destination=dem_aligned,
                src_transform=dem_src.transform,
                src_crs=dem_src.crs,
                src_nodata=dem_src.nodata,
                dst_transform=profile["transform"],
                dst_crs=profile["crs"],
                dst_nodata=np.nan,
                resampling=Resampling.bilinear,
            )
        combined_valid = valid & np.isfinite(dem_aligned)
        ndsm_vals = np.maximum(dsm[combined_valid] - dem_aligned[combined_valid], 0.0)
        out[combined_valid] = ndsm_vals.astype(np.float32)
        return out, False

    pixel_m = max(abs(float(profile["transform"].a)), 0.1)
    win_px = max(3, int(round(float(ground_window_m) / pixel_m)))
    if win_px % 2 == 0:
        win_px += 1

    max_valid = float(np.nanmax(dsm[valid]))
    filled = np.where(valid, dsm, np.float32(max_valid + 100.0))
    ground = minimum_filter(filled, size=win_px, mode="nearest")
    ndsm_vals = np.maximum(dsm[valid] - ground[valid], 0.0)
    out[valid] = ndsm_vals.astype(np.float32)
    return out, True


def _write_float32_geotiff(
    out_path: Path,
    array: np.ndarray,
    template_profile: dict[str, Any],
    nodata: float = _NODATA_OUT,
) -> Path:
    """Writes a single-band float32 GeoTIFF matching ``template_profile``.

    Args:
        out_path: Output raster path.
        array: 2D array to write.
        template_profile: Rasterio profile dictionary supplying CRS/transform.
        nodata: Nodata sentinel value written into file metadata.

    Returns:
        Path to the written GeoTIFF file.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    profile = template_profile.copy()
    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        nodata=nodata,
    )
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(array.astype(np.float32), 1)
    return out_path


def derive_ndsm_from_solar_dsm(
    dsm_path: Path,
    out_ndsm_path: Path,
    *,
    dem_path: Path | None = None,
    ground_window_m: float = 35.0,
) -> tuple[Path, bool]:
    """Derives an nDSM height raster from a Google Solar API DSM GeoTIFF.

    Args:
        dsm_path: Input Solar API DSM GeoTIFF path.
        out_ndsm_path: Output nDSM GeoTIFF path.
        dem_path: Optional bare-earth DEM GeoTIFF path. When supplied, exact
            bilinear reprojection and subtraction yields ``is_derived=False``.
            When omitted, morphological ground estimation yields
            ``is_derived=True``.
        ground_window_m: Morphological ground filter window width in meters
            when ``dem_path`` is ``None``.

    Returns:
        Tuple ``(out_ndsm_path, is_derived)``.
    """
    dsm, profile, valid = _read_dsm_array(Path(dsm_path))
    ndsm, is_derived = _compute_ndsm_array(
        dsm,
        profile,
        valid,
        dem_path=Path(dem_path) if dem_path is not None else None,
        ground_window_m=ground_window_m,
    )
    written = _write_float32_geotiff(Path(out_ndsm_path), ndsm, profile)
    return written, is_derived


def extract_canopy_cdsm_tdsm(
    dsm_path: Path,
    mask_path: Path,
    out_cdsm_path: Path,
    *,
    out_tdsm_path: Path | None = None,
    dem_path: Path | None = None,
    ground_window_m: float = 35.0,
    min_canopy_height_m: float = 1.5,
    crown_depth_fraction: float = 0.6,
) -> tuple[Path, Path]:
    """Extracts tree canopy DSM (CDSM) and trunk-zone DSM (TDSM) from Solar layers.

    Non-building pixels (``mask == 0``) whose normalized height meets
    ``min_canopy_height_m`` populate the CDSM raster; TDSM is derived at
    ``cdsm * (1.0 - crown_depth_fraction)`` (matching Stage 6 defaults).

    Args:
        dsm_path: Input Solar DSM GeoTIFF path.
        mask_path: Input Solar building-footprint mask GeoTIFF path.
        out_cdsm_path: Output canopy DSM GeoTIFF path.
        out_tdsm_path: Optional output trunk-zone DSM GeoTIFF path. Defaults
            to ``<out_cdsm_path.stem>_tdsm.tif`` alongside ``out_cdsm_path``.
        dem_path: Optional bare-earth DEM raster path.
        ground_window_m: Morphological ground filter window size in meters.
        min_canopy_height_m: Minimum above-ground height kept as vegetation.
        crown_depth_fraction: Fraction of tree height occupied by the crown.

    Returns:
        Tuple ``(out_cdsm_path, out_tdsm_path)``.
    """
    dsm, profile, valid = _read_dsm_array(Path(dsm_path))
    ndsm, _is_derived = _compute_ndsm_array(
        dsm,
        profile,
        valid,
        dem_path=Path(dem_path) if dem_path is not None else None,
        ground_window_m=ground_window_m,
    )

    with rasterio.open(Path(mask_path)) as msrc:
        mask_raw = msrc.read(1).astype(np.float32)
        mask_aligned = np.zeros(dsm.shape, dtype=np.float32)
        reproject(
            source=mask_raw,
            destination=mask_aligned,
            src_transform=msrc.transform,
            src_crs=msrc.crs,
            src_nodata=msrc.nodata,
            dst_transform=profile["transform"],
            dst_crs=profile["crs"],
            dst_nodata=0.0,
            resampling=Resampling.nearest,
        )

    is_building = mask_aligned > 0.0
    valid_ndsm = valid & (ndsm != _NODATA_OUT)
    canopy_mask = valid_ndsm & (~is_building) & (ndsm >= float(min_canopy_height_m))

    cdsm = np.where(valid_ndsm, np.float32(0.0), np.float32(_NODATA_OUT))
    cdsm = np.where(canopy_mask, ndsm, cdsm).astype(np.float32)

    trunk_factor = float(max(0.0, min(1.0, 1.0 - crown_depth_fraction)))
    tdsm = np.where(valid_ndsm, np.float32(0.0), np.float32(_NODATA_OUT))
    tdsm = np.where(canopy_mask, cdsm * np.float32(trunk_factor), tdsm).astype(
        np.float32
    )

    cdsm_out = _write_float32_geotiff(Path(out_cdsm_path), cdsm, profile)
    target_tdsm = (
        Path(out_tdsm_path)
        if out_tdsm_path is not None
        else cdsm_out.with_name(f"{cdsm_out.stem}_tdsm.tif")
    )
    tdsm_out = _write_float32_geotiff(target_tdsm, tdsm, profile)
    return cdsm_out, tdsm_out


def enrich_buildings_with_solar_insights(
    buildings_gdf: gpd.GeoDataFrame,
    *,
    client: GmapsHttpClient | None = None,
    insights_by_id: dict[str, dict[str, Any]] | None = None,
    id_col: str = "osm_id",
    pitch_threshold_deg: float = 5.0,
    update_roof_shape: bool = True,
) -> gpd.GeoDataFrame:
    """Enriches building footprints with Solar API rooftop geometry & PV potential.

    Updates ``roof_shape`` only when missing/flat and observed ``roof_pitch_deg``
    exceeds ``pitch_threshold_deg``, and stamps ``FUSED_GMAPSSOLAR_HIGH`` or
    ``FUSED_GMAPSSOLAR_MED`` provenance tokens.

    Args:
        buildings_gdf: Input building footprints GeoDataFrame.
        client: Optional cached :class:`GmapsHttpClient` for live queries.
        insights_by_id: Optional pre-fetched mapping of string building ID to
            decoded Solar API ``buildingInsights`` payload.
        id_col: Column name identifying individual buildings.
        pitch_threshold_deg: Minimum roof pitch angle (degrees) treated as pitched.
        update_roof_shape: When ``True``, updates missing or ``"flat"``
            ``roof_shape`` entries to ``"pitched"`` when pitched.

    Returns:
        Copy of ``buildings_gdf`` enriched with ``gmaps_solar_*`` columns.

    Raises:
        ValueError: If ``buildings_gdf`` has no CRS set and live lookups are needed.
    """
    assert_no_eui_columns(buildings_gdf.columns)
    out = buildings_gdf.copy()
    if out.empty:
        return out

    if out.crs is None and insights_by_id is None:
        raise ValueError(
            "buildings_gdf requires a CRS when querying live Solar insights."
        )

    centroids_wgs84 = (
        out.geometry.centroid
        if out.crs is None
        else gpd.GeoSeries(out.geometry.centroid, crs=out.crs).to_crs(epsg=4326)
    )

    solar_cols = {
        "gmaps_solar_roof_area_m2": np.nan,
        "gmaps_solar_pitch_deg": np.nan,
        "gmaps_solar_azimuth_deg": np.nan,
        "gmaps_solar_max_panels": np.nan,
        "gmaps_solar_sunshine_h_yr": np.nan,
    }
    for col, default in solar_cols.items():
        if col not in out.columns:
            out[col] = default

    high_mask = pd.Series(False, index=out.index)
    med_mask = pd.Series(False, index=out.index)
    pitched_high_mask = pd.Series(False, index=out.index)
    pitched_med_mask = pd.Series(False, index=out.index)

    for idx in out.index:
        raw_payload: dict[str, Any] | None = None
        if insights_by_id is not None and id_col in out.columns:
            key = str(out.loc[idx, id_col])
            raw_payload = insights_by_id.get(key)
        elif insights_by_id is None:
            pt = centroids_wgs84.loc[idx]
            try:
                raw_payload = fetch_building_insights(
                    float(pt.y),
                    float(pt.x),
                    client=client,
                )
            except GmapsApiError as exc:
                if exc.status_code == 404:
                    raw_payload = None
                else:
                    raise

        if not raw_payload:
            continue

        summary = parse_building_insights(raw_payload)
        if summary.roof_area_m2 is not None:
            out.loc[idx, "gmaps_solar_roof_area_m2"] = summary.roof_area_m2
        if summary.roof_pitch_deg is not None:
            out.loc[idx, "gmaps_solar_pitch_deg"] = summary.roof_pitch_deg
        if summary.roof_azimuth_deg is not None:
            out.loc[idx, "gmaps_solar_azimuth_deg"] = summary.roof_azimuth_deg
        if summary.max_panel_count is not None:
            out.loc[idx, "gmaps_solar_max_panels"] = float(summary.max_panel_count)
        if summary.max_sunshine_hours_per_year is not None:
            out.loc[idx, "gmaps_solar_sunshine_h_yr"] = (
                summary.max_sunshine_hours_per_year
            )

        is_high = summary.roof_segment_count > 0 and summary.roof_pitch_deg is not None
        if is_high:
            high_mask.loc[idx] = True
        else:
            med_mask.loc[idx] = True

        if (
            update_roof_shape
            and summary.roof_pitch_deg is not None
            and summary.roof_pitch_deg > float(pitch_threshold_deg)
        ):
            existing_shape = (
                str(out.loc[idx, "roof_shape"]).strip().lower()
                if "roof_shape" in out.columns
                and pd.notna(out.loc[idx, "roof_shape"])
                else ""
            )
            if existing_shape in {"", "nan", "none", "flat", "unknown"}:
                if "roof_shape" not in out.columns:
                    out["roof_shape"] = pd.Series(pd.NA, index=out.index)
                out.loc[idx, "roof_shape"] = "pitched"
                if is_high:
                    pitched_high_mask.loc[idx] = True
                else:
                    pitched_med_mask.loc[idx] = True

    if high_mask.any():
        out = provenance.append_flag(out, "FUSED_GMAPSSOLAR_HIGH", mask=high_mask)
    if med_mask.any():
        out = provenance.append_flag(out, "FUSED_GMAPSSOLAR_MED", mask=med_mask)
    if pitched_high_mask.any():
        out = provenance.set_provenance(
            out,
            "roof_shape",
            "FUSED_GMAPSSOLAR_HIGH",
            mask=pitched_high_mask,
            confidence="HIGH",
        )
    if pitched_med_mask.any():
        out = provenance.set_provenance(
            out,
            "roof_shape",
            "FUSED_GMAPSSOLAR_MED",
            mask=pitched_med_mask,
            confidence="MED",
        )

    assert_no_eui_columns(out.columns)
    return out
