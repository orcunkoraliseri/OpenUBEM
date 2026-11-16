"""Google Maps Weather API forecast ingestion, irradiance closure, and risk tiers."""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
from typing import Any

import numpy as np
import pandas as pd

from openubem.acquisition.gmaps_client import GmapsHttpClient
from openubem.microclimate import solar

_WEATHER_FORECAST_URL = "https://weather.googleapis.com/v1/forecast/hours:lookup"
_SOLAR_CONSTANT_WM2 = 1367.0
_MAX_FORECAST_HOURS = 240

_WIND_UNIT_TO_MS: dict[str, float] = {
    "METERS_PER_SECOND": 1.0,
    "M_PER_S": 1.0,
    "M/S": 1.0,
    "MS": 1.0,
    "KILOMETERS_PER_HOUR": 1.0 / 3.6,
    "KM_PER_H": 1.0 / 3.6,
    "KM/H": 1.0 / 3.6,
    "KPH": 1.0 / 3.6,
    "MILES_PER_HOUR": 0.44704,
    "MPH": 0.44704,
    "KNOTS": 0.514444,
    "KT": 0.514444,
}


def convert_wind_speed_to_ms(value: float, unit: str) -> float:
    """Converts a wind speed magnitude from API units into meters per second.

    Args:
        value: Numeric wind speed measurement.
        unit: Unit identifier reported by Weather API (e.g.,
            ``"KILOMETERS_PER_HOUR"``, ``"MILES_PER_HOUR"``,
            ``"METERS_PER_SECOND"``).

    Returns:
        Wind speed in meters per second.

    Raises:
        ValueError: If ``unit`` is empty or unrecognized.
    """
    norm_unit = str(unit or "").strip().upper()
    if norm_unit not in _WIND_UNIT_TO_MS:
        raise ValueError(f"Unsupported wind speed unit: {unit!r}")
    return float(value) * _WIND_UNIT_TO_MS[norm_unit]


def _parse_utc_offset_hours(raw_offset: Any, lon: float) -> float:
    """Parses a Google Maps ``utcOffset`` string or falls back to longitude.

    Args:
        raw_offset: Duration string such as ``"10800s"``, ``"-05:00"``, or numeric
            seconds/hours.
        lon: Site longitude in degrees used for 15-degree meridian fallback.

    Returns:
        UTC offset in decimal hours.
    """
    if raw_offset is None:
        return float(round(float(lon) / 15.0))
    if isinstance(raw_offset, (int, float)) and not isinstance(raw_offset, bool):
        val = float(raw_offset)
        return val / 3600.0 if abs(val) > 24.0 else val

    text = str(raw_offset).strip()
    sec_match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)s", text)
    if sec_match:
        return float(sec_match.group(1)) / 3600.0

    hhmm_match = re.fullmatch(r"([+-]?)(\d{1,2}):(\d{2})", text)
    if hhmm_match:
        sign = -1.0 if hhmm_match.group(1) == "-" else 1.0
        hrs = float(hhmm_match.group(2))
        mins = float(hhmm_match.group(3))
        return sign * (hrs + mins / 60.0)

    return float(round(float(lon) / 15.0))


def _extract_pressure_pa(hour_entry: dict[str, Any]) -> float:
    """Extracts mean sea-level air pressure in Pascals from a Weather API hour.

    Args:
        hour_entry: Single entry inside Weather API ``forecastHours``.

    Returns:
        Pressure in Pascals (defaults to 101325.0 Pa if absent).
    """
    air_p = hour_entry.get("airPressure")
    if isinstance(air_p, dict) and air_p.get("meanSeaLevelMillibars") is not None:
        return float(air_p["meanSeaLevelMillibars"]) * 100.0
    mslp = hour_entry.get("meanSeaLevelPressure")
    if isinstance(mslp, dict) and mslp.get("value") is not None:
        return float(mslp["value"]) * 100.0
    if isinstance(mslp, (int, float)):
        return float(mslp) * 100.0
    return 101325.0


def _magnus_dew_point_c(temp_c: float, rh_pct: float) -> float:
    """Computes approximate dew-point temperature in Celsius via Magnus formula.

    Args:
        temp_c: Dry-bulb air temperature in Celsius.
        rh_pct: Relative humidity in percent (1..100).

    Returns:
        Dew-point temperature in degrees Celsius.
    """
    rh = max(1.0, min(100.0, float(rh_pct)))
    a_coef = 17.625
    b_coef = 243.04
    gamma = math.log(rh / 100.0) + (a_coef * temp_c) / (b_coef + temp_c)
    return float((b_coef * gamma) / (a_coef - gamma))


def estimate_irradiance_from_cloud_cover(
    dt_utc_index: pd.DatetimeIndex,
    lat: float,
    lon: float,
    cloud_cover_pct: np.ndarray | pd.Series,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Derives hourly GHI, DNI, and DHI from solar altitude and cloud fraction.

    Combines the Haurwitz (1945) clear-sky global irradiance model, Kasten &
    Czeplak (1980) cloud attenuation, and the Erbs et al. (1982) diffuse
    fraction split.

    Args:
        dt_utc_index: Naive UTC ``DatetimeIndex`` matching OpenUBEM solar calls.
        lat: Site latitude in decimal degrees.
        lon: Site longitude in decimal degrees.
        cloud_cover_pct: Total sky cloud cover percentage (0..100).

    Returns:
        Tuple ``(ghi_wm2, dni_wm2, dhi_wm2)`` of non-negative ``float64`` arrays.
    """
    alt_deg, _az = solar.solar_position(dt_utc_index, float(lat), float(lon))
    cloud_frac = np.clip(
        np.asarray(cloud_cover_pct, dtype=np.float64) / 100.0,
        0.0,
        1.0,
    )
    sunlit = alt_deg > 0.0
    sin_h = np.where(sunlit, np.sin(np.deg2rad(np.clip(alt_deg, 0.0, 90.0))), 0.0)

    ghi = np.zeros_like(sin_h, dtype=np.float64)
    dni = np.zeros_like(sin_h, dtype=np.float64)
    dhi = np.zeros_like(sin_h, dtype=np.float64)
    if not sunlit.any():
        return ghi, dni, dhi

    ghi_clear = np.zeros_like(sin_h, dtype=np.float64)
    ghi_clear[sunlit] = (
        1098.0
        * sin_h[sunlit]
        * np.exp(-0.057 / np.maximum(sin_h[sunlit], 1e-4))
    )
    ghi[sunlit] = ghi_clear[sunlit] * (1.0 - 0.75 * (cloud_frac[sunlit] ** 3.4))
    ghi = np.maximum(0.0, ghi)

    doy = dt_utc_index.day_of_year.to_numpy(dtype=np.float64)
    eccentricity = 1.0 + 0.033 * np.cos(2.0 * np.pi * doy / 365.0)
    i0n = _SOLAR_CONSTANT_WM2 * eccentricity
    i0h = np.maximum(i0n * sin_h, 1e-6)

    kt = np.zeros_like(sin_h, dtype=np.float64)
    kt[sunlit] = np.clip(ghi[sunlit] / i0h[sunlit], 0.0, 1.2)

    kd = np.ones_like(kt, dtype=np.float64)
    low = sunlit & (kt <= 0.22)
    mid = sunlit & (kt > 0.22) & (kt <= 0.80)
    high = sunlit & (kt > 0.80)

    kd[low] = 1.0 - 0.09 * kt[low]
    kd[mid] = (
        0.9511
        - 0.1604 * kt[mid]
        + 4.388 * (kt[mid] ** 2)
        - 16.638 * (kt[mid] ** 3)
        + 12.336 * (kt[mid] ** 4)
    )
    kd[high] = 0.165
    kd = np.clip(kd, 0.0, 1.0)

    dhi[sunlit] = kd[sunlit] * ghi[sunlit]
    direct_h = np.maximum(0.0, ghi[sunlit] - dhi[sunlit])
    dni[sunlit] = np.minimum(
        i0n[sunlit],
        direct_h / np.maximum(sin_h[sunlit], 0.05),
    )
    return ghi, dni, dhi


def parse_weather_forecast_to_df(
    payload: dict[str, Any],
    *,
    lat: float,
    lon: float,
) -> tuple[pd.DataFrame, float]:
    """Converts Google Weather API hourly payload into Stage-6 EPW DataFrame schema.

    Timestamps are shifted by the parsed ``displayDateTime.utcOffset`` into a
    naive local-standard ``DatetimeIndex`` matching ``read_epw_hourly()`` while
    evaluating solar geometry against the true UTC instants.

    Args:
        payload: Decoded Weather API payload containing ``forecastHours`` or
            ``historyHours``.
        lat: Site WGS 84 latitude in decimal degrees.
        lon: Site WGS 84 longitude in decimal degrees.

    Returns:
        Tuple ``(epw_style_df, utc_offset_h)``.

    Raises:
        ValueError: If no hourly entries exist or required fields are missing.
    """
    hours_list = payload.get("forecastHours") or payload.get("historyHours") or []
    if not hours_list:
        raise ValueError("Weather API payload contains no hourly forecast entries.")

    utc_times: list[pd.Timestamp] = []
    offsets_h: list[float] = []
    dry_bulbs: list[float] = []
    dew_points: list[float] = []
    rhs: list[float] = []
    pressures: list[float] = []
    wind_dirs: list[float] = []
    wind_speeds: list[float] = []
    clouds_pct: list[float] = []

    for entry in hours_list:
        interval = entry.get("interval") or {}
        start_raw = interval.get("startTime")
        if not start_raw:
            raise ValueError("Weather hour entry missing interval.startTime.")
        ts_utc = pd.Timestamp(start_raw)
        if ts_utc.tzinfo is None:
            ts_utc = ts_utc.tz_localize("UTC")
        else:
            ts_utc = ts_utc.tz_convert("UTC")
        utc_times.append(ts_utc.tz_localize(None))

        disp = entry.get("displayDateTime") or {}
        offsets_h.append(_parse_utc_offset_hours(disp.get("utcOffset"), lon))

        temp_c = float((entry.get("temperature") or {}).get("degrees"))
        rh_val = float(entry.get("relativeHumidity", 50.0))
        dp_raw = (entry.get("dewPoint") or {}).get("degrees")
        dp_val = (
            float(dp_raw)
            if dp_raw is not None
            else _magnus_dew_point_c(temp_c, rh_val)
        )
        wind_obj = entry.get("wind") or {}
        wdir = float((wind_obj.get("direction") or {}).get("degrees", 0.0)) % 360.0
        wspeed_obj = wind_obj.get("speed") or {}
        wspd_ms = convert_wind_speed_to_ms(
            float(wspeed_obj.get("value", 0.0)),
            str(wspeed_obj.get("unit", "METERS_PER_SECOND")),
        )
        cloud_val = float(entry.get("cloudCover", 0.0))

        dry_bulbs.append(temp_c)
        dew_points.append(dp_val)
        rhs.append(rh_val)
        pressures.append(_extract_pressure_pa(entry))
        wind_dirs.append(wdir)
        wind_speeds.append(wspd_ms)
        clouds_pct.append(cloud_val)

    utc_offset_h = float(offsets_h[0])
    dt_utc_index = pd.DatetimeIndex(utc_times, name="datetime")
    local_index = pd.DatetimeIndex(
        dt_utc_index + pd.Timedelta(hours=utc_offset_h),
        name="datetime",
    )

    ghi, dni, dhi = estimate_irradiance_from_cloud_cover(
        dt_utc_index,
        lat=lat,
        lon=lon,
        cloud_cover_pct=np.asarray(clouds_pct, dtype=np.float64),
    )
    sky_tenths = np.clip(np.asarray(clouds_pct, dtype=np.float64) / 10.0, 0.0, 10.0)

    df = pd.DataFrame(
        {
            "source_year": local_index.year.to_numpy(dtype=np.int64),
            "dry_bulb_c": np.asarray(dry_bulbs, dtype=np.float64),
            "dew_point_c": np.asarray(dew_points, dtype=np.float64),
            "relative_humidity_pct": np.asarray(rhs, dtype=np.float64),
            "atmospheric_pressure_pa": np.asarray(pressures, dtype=np.float64),
            "horizontal_infrared_wm2": np.full(len(local_index), np.nan),
            "global_horizontal_wm2": ghi,
            "direct_normal_wm2": dni,
            "diffuse_horizontal_wm2": dhi,
            "wind_direction_deg": np.asarray(wind_dirs, dtype=np.float64),
            "wind_speed_ms": np.asarray(wind_speeds, dtype=np.float64),
            "total_sky_cover": sky_tenths,
            "opaque_sky_cover": sky_tenths,
            "dq_flag": ["GMAPS_WEATHER_API"] * len(local_index),
        },
        index=local_index,
    )
    df = df[~df.index.duplicated(keep="first")].sort_index()
    return df, utc_offset_h


def fetch_hourly_weather_forecast(
    lat: float,
    lon: float,
    *,
    hours: int = 24,
    client: GmapsHttpClient | None = None,
    json_path: Path | None = None,
    page_size: int = 24,
) -> tuple[pd.DataFrame, float]:
    """Fetches hourly Weather API forecast (up to 240 h) or loads a local JSON file.

    Args:
        lat: Site WGS 84 latitude in decimal degrees.
        lon: Site WGS 84 longitude in decimal degrees.
        hours: Requested forecast horizon in hours (clamped to ``1..240``).
        client: Optional cached :class:`GmapsHttpClient` instance.
        json_path: Optional pre-downloaded Weather API JSON response path.
        page_size: Hourly page size requested per paginated GET call.

    Returns:
        Tuple ``(weather_df, utc_offset_h)`` ready for ``run_step6``.
    """
    target_hours = max(1, min(int(hours), _MAX_FORECAST_HOURS))
    if json_path is not None:
        payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
        df, offset = parse_weather_forecast_to_df(payload, lat=lat, lon=lon)
        return df.iloc[:target_hours].copy(), offset

    http = client or GmapsHttpClient()
    collected: list[dict[str, Any]] = []
    page_token: str | None = None

    while len(collected) < target_hours:
        params: dict[str, Any] = {
            "location.latitude": round(float(lat), 7),
            "location.longitude": round(float(lon), 7),
            "hours": target_hours,
            "pageSize": min(int(page_size), target_hours),
        }
        if page_token:
            params["pageToken"] = page_token
        page = http.get_json(_WEATHER_FORECAST_URL, params=params, auth_mode="query")
        entries = page.get("forecastHours") or []
        if not entries:
            break
        collected.extend(entries)
        page_token = page.get("nextPageToken")
        if not page_token:
            break

    combined = {"forecastHours": collected[:target_hours]}
    df, offset = parse_weather_forecast_to_df(combined, lat=lat, lon=lon)
    return df.iloc[:target_hours].copy(), offset


def classify_municipal_risk_tier(utci_c: float) -> str:
    """Classifies a peak UTCI temperature (C) into standard thermal stress tiers.

    Args:
        utci_c: Universal Thermal Climate Index value in degrees Celsius.

    Returns:
        Standard UTCI stress category string.
    """
    val = float(utci_c)
    if val >= 46.0:
        return "Extreme Heat Stress"
    if val >= 38.0:
        return "Very Strong Heat Stress"
    if val >= 32.0:
        return "Strong Heat Stress"
    if val >= 26.0:
        return "Moderate Heat Stress"
    return "No Thermal Stress"


def build_municipal_risk_report(
    exposure_metrics: dict[str, Any],
    *,
    utci_series: pd.Series | None = None,
    air_quality_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Builds a structured municipal heat-risk advisory report from Stage 6 results.

    Args:
        exposure_metrics: Dictionary written to ``06_mc_exposure_metrics.json``.
        utci_series: Optional hourly spatially representative UTCI series.
        air_quality_context: Optional ambient Air Quality API summary dictionary.

    Returns:
        Structured risk report dictionary suitable for ``06_mc_risk_alerts.json``.
    """
    peak_val = exposure_metrics.get("utci_peak_max_c")
    if peak_val is None and utci_series is not None and not utci_series.empty:
        peak_val = float(utci_series.max())

    risk_tier = (
        classify_municipal_risk_tier(float(peak_val))
        if peak_val is not None
        else "Unknown"
    )

    exceedance_hours: dict[str, int] = {
        "moderate_ge_26c": 0,
        "strong_ge_32c": 0,
        "very_strong_ge_38c": 0,
        "extreme_ge_46c": 0,
    }
    if utci_series is not None and not utci_series.empty:
        arr = pd.to_numeric(utci_series, errors="coerce").dropna()
        exceedance_hours["moderate_ge_26c"] = int((arr >= 26.0).sum())
        exceedance_hours["strong_ge_32c"] = int((arr >= 32.0).sum())
        exceedance_hours["very_strong_ge_38c"] = int((arr >= 38.0).sum())
        exceedance_hours["extreme_ge_46c"] = int((arr >= 46.0).sum())

    advisories: list[str] = []
    if peak_val is not None and float(peak_val) >= 46.0:
        advisories.append(
            "Activate extreme-heat cooling centers; UTCI reached >= 46.0 C."
        )
    elif peak_val is not None and float(peak_val) >= 38.0:
        advisories.append(
            "Issue very-strong outdoor heat warning; schedule outdoor work early."
        )
    elif peak_val is not None and float(peak_val) >= 32.0:
        advisories.append(
            "Strong heat stress forecast; prioritize shaded transit corridors."
        )
    else:
        advisories.append("Standard thermal monitoring.")

    if air_quality_context is not None:
        advisories.append(
            "Ambient AQI attached from Google Air Quality API (macro-scale "
            "ambient condition, not canyon-dispersed)."
        )

    pheh_total = next(
        (val for key, val in exposure_metrics.items() if key.startswith("pheh_")),
        None,
    )
    return {
        "utci_peak_max_c": float(peak_val) if peak_val is not None else None,
        "risk_tier": risk_tier,
        "pheh_total": pheh_total,
        "ctsi_mean_degc_h": exposure_metrics.get("ctsi_mean_degc_h"),
        "ctsi_max_degc_h": exposure_metrics.get("ctsi_max_degc_h"),
        "exceedance_hours": exceedance_hours,
        "air_quality": air_quality_context,
        "advisories": advisories,
    }
