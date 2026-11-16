"""Google Maps Air Quality API context ingestion and parcel annotation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd

from openubem.acquisition.gmaps_client import GmapsHttpClient
from openubem.semantic import provenance

_AQ_CURRENT_URL = (
    "https://airquality.googleapis.com/v1/currentConditions:lookup"
)
AQ_AMBIENT_PROVENANCE = "GMAPS_AIR_QUALITY_AMBIENT_NOT_DISPERSED"


def parse_air_quality_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Parses a Google Maps Air Quality API ``currentConditions`` response.

    Explicitly tags results with ``GMAPS_AIR_QUALITY_AMBIENT_NOT_DISPERSED`` so
    macro-scale ambient metrics are never mistaken for street-canyon CFD
    dispersion fields.

    Args:
        payload: Decoded JSON response from ``currentConditions:lookup``.

    Returns:
        Normalized ambient air-quality context dictionary.
    """
    indexes = payload.get("indexes") or []
    chosen_idx: dict[str, Any] = {}
    for entry in indexes:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("code", "")).lower() == "uaqi":
            chosen_idx = entry
            break
    if not chosen_idx and indexes and isinstance(indexes[0], dict):
        chosen_idx = indexes[0]

    concentrations: dict[str, float] = {}
    units: dict[str, str] = {}
    for pol in payload.get("pollutants") or []:
        if not isinstance(pol, dict):
            continue
        code = str(pol.get("code") or "").strip().lower()
        conc = pol.get("concentration") or {}
        val = conc.get("value")
        if code and val is not None:
            concentrations[code] = float(val)
            if conc.get("units"):
                units[code] = str(conc["units"])

    health_raw = payload.get("healthRecommendations") or {}
    general_rec = (
        health_raw.get("generalPopulation")
        if isinstance(health_raw, dict)
        else None
    )

    return {
        "date_time": payload.get("dateTime"),
        "region_code": payload.get("regionCode"),
        "aqi": chosen_idx.get("aqi"),
        "aqi_display": chosen_idx.get("aqiDisplay"),
        "aqi_category": chosen_idx.get("category"),
        "dominant_pollutant": chosen_idx.get("dominantPollutant"),
        "pollutant_concentrations": concentrations,
        "pollutant_units": units,
        "health_recommendation_general": general_rec,
        "aq_provenance": AQ_AMBIENT_PROVENANCE,
        "is_canyon_dispersed": False,
    }


def fetch_ambient_air_quality(
    lat: float,
    lon: float,
    *,
    client: GmapsHttpClient | None = None,
    json_path: Path | None = None,
) -> dict[str, Any]:
    """Fetches ambient air quality context from disk JSON or Air Quality API.

    Args:
        lat: Site WGS 84 latitude in decimal degrees.
        lon: Site WGS 84 longitude in decimal degrees.
        client: Optional cached :class:`GmapsHttpClient` instance.
        json_path: Optional pre-downloaded Air Quality JSON file path.

    Returns:
        Normalized ambient air-quality context dictionary with explicit
        non-dispersed provenance.
    """
    if json_path is not None:
        payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
        return parse_air_quality_response(payload)

    http = client or GmapsHttpClient()
    body = {
        "location": {
            "latitude": round(float(lat), 7),
            "longitude": round(float(lon), 7),
        },
        "extraComputations": [
            "HEALTH_RECOMMENDATIONS",
            "DOMINANT_POLLUTANT_CONCENTRATION",
            "POLLUTANT_CONCENTRATION",
            "LOCAL_AQI",
        ],
    }
    payload = http.post_json(_AQ_CURRENT_URL, json_body=body, auth_mode="query")
    return parse_air_quality_response(payload)


def attach_ambient_air_quality(
    parcel_gdf: gpd.GeoDataFrame,
    aq_context: dict[str, Any],
) -> gpd.GeoDataFrame:
    """Attaches non-dispersed ambient air-quality attributes to parcel summaries.

    Args:
        parcel_gdf: Parcel-level Stage 6 summary GeoDataFrame.
        aq_context: Ambient air-quality dictionary returned by
            :func:`fetch_ambient_air_quality` or
            :func:`parse_air_quality_response`.

    Returns:
        Copy of ``parcel_gdf`` annotated with ambient AQI attributes and
        ``aq_provenance``.
    """
    out = parcel_gdf.copy()
    concentrations = aq_context.get("pollutant_concentrations") or {}
    out["aq_ambient_aqi"] = aq_context.get("aqi")
    out["aq_ambient_category"] = aq_context.get("aqi_category")
    out["aq_dominant_pollutant"] = aq_context.get("dominant_pollutant")
    out["aq_pm25_ugm3"] = concentrations.get("pm25")
    prov = str(aq_context.get("aq_provenance") or AQ_AMBIENT_PROVENANCE)
    out["aq_provenance"] = prov

    if "data_quality_flag" in out.columns:
        out = provenance.append_flag(out, prov)
    return out
