"""Offline tests for GMaps Weather, Air Quality, Stage 6 forecast, and 3D export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from openubem.microclimate.gmaps_air_quality import (
    AQ_AMBIENT_PROVENANCE,
    attach_ambient_air_quality,
    parse_air_quality_response,
)
from openubem.microclimate.gmaps_weather import (
    convert_wind_speed_to_ms,
    estimate_irradiance_from_cloud_cover,
    fetch_hourly_weather_forecast,
    parse_weather_forecast_to_df,
)
from openubem.microclimate.window import (
    AnnualEnergyPlusWindowRefusedError,
    select_window,
)
from openubem.viz.gmaps_web_export import (
    export_gmaps_companion_bundle,
    resolve_companion_output_dir,
)
from scripts.export_gmaps_3d_companion import main as companion_cli_main
from scripts.run_step6_gmaps_forecast import main as forecast_cli_main

_EXPECTED_EPW_COLUMNS = (
    "source_year",
    "dry_bulb_c",
    "dew_point_c",
    "relative_humidity_pct",
    "atmospheric_pressure_pa",
    "horizontal_infrared_wm2",
    "global_horizontal_wm2",
    "direct_normal_wm2",
    "diffuse_horizontal_wm2",
    "wind_direction_deg",
    "wind_speed_ms",
    "total_sky_cover",
    "opaque_sky_cover",
    "dq_flag",
)


def _weather_hour(
    iso_utc: str,
    *,
    temp_c: float = 34.0,
    rh_pct: float = 40.0,
    cloud_pct: float = 10.0,
    wind_kmh: float = 14.4,
    utc_offset: str = "10800s",
) -> dict[str, Any]:
    """Builds a synthetic Google Maps Weather API hourly forecast dictionary.

    Args:
        iso_utc: UTC interval start timestamp string.
        temp_c: Air temperature in Celsius.
        rh_pct: Relative humidity percentage.
        cloud_pct: Cloud cover percentage.
        wind_kmh: Wind speed in km/h.
        utc_offset: Google duration UTC offset string.

    Returns:
        Weather API ``forecastHours`` item dictionary.
    """
    return {
        "interval": {"startTime": iso_utc},
        "displayDateTime": {"utcOffset": utc_offset},
        "temperature": {"degrees": temp_c},
        "dewPoint": {"degrees": temp_c - 10.0},
        "relativeHumidity": rh_pct,
        "airPressure": {"meanSeaLevelMillibars": 1012.5},
        "wind": {
            "direction": {"degrees": 210},
            "speed": {"value": wind_kmh, "unit": "KILOMETERS_PER_HOUR"},
        },
        "cloudCover": cloud_pct,
    }


def _sample_aq_payload() -> dict[str, Any]:
    """Returns a representative mocked Google Maps Air Quality API payload.

    Returns:
        Decoded JSON payload dictionary.
    """
    return {
        "dateTime": "2026-07-15T12:00:00Z",
        "regionCode": "tr",
        "indexes": [
            {
                "code": "uaqi",
                "aqi": 68,
                "aqiDisplay": "68",
                "category": "Moderate air quality",
                "dominantPollutant": "pm25",
            }
        ],
        "pollutants": [
            {
                "code": "pm25",
                "concentration": {"value": 18.4, "units": "MICROGRAMS_PER_CUBIC_METER"},
            },
            {
                "code": "no2",
                "concentration": {"value": 26.0, "units": "PARTS_PER_BILLION"},
            },
        ],
        "healthRecommendations": {
            "generalPopulation": "Sensitive individuals should monitor haze."
        },
    }


def test_wind_unit_conversion_and_cloud_irradiance() -> None:
    """Checks wind speed unit conversion and physical solar irradiance bounds."""
    assert convert_wind_speed_to_ms(5.0, "METERS_PER_SECOND") == pytest.approx(5.0)
    assert convert_wind_speed_to_ms(36.0, "KILOMETERS_PER_HOUR") == pytest.approx(10.0)
    assert convert_wind_speed_to_ms(10.0, "MILES_PER_HOUR") == pytest.approx(4.4704)
    assert convert_wind_speed_to_ms(10.0, "KNOTS") == pytest.approx(5.14444)
    with pytest.raises(ValueError):
        convert_wind_speed_to_ms(3.0, "FURLONGS_PER_FORTNIGHT")

    # Midnight UTC + Solar noon UTC in Istanbul (lat=41.0, lon=29.0)
    dt_utc = pd.DatetimeIndex(["2026-07-15 22:00", "2026-07-15 10:00"])
    ghi_clr, dni_clr, dhi_clr = estimate_irradiance_from_cloud_cover(
        dt_utc,
        lat=41.0,
        lon=29.0,
        cloud_cover_pct=np.array([0.0, 0.0]),
    )
    ghi_ovc, _dni_ovc, _dhi_ovc = estimate_irradiance_from_cloud_cover(
        dt_utc,
        lat=41.0,
        lon=29.0,
        cloud_cover_pct=np.array([100.0, 100.0]),
    )
    assert ghi_clr[0] == 0.0 and dni_clr[0] == 0.0 and dhi_clr[0] == 0.0
    assert ghi_clr[1] > ghi_ovc[1] > 0.0
    assert dni_clr[1] > 0.0 and dhi_clr[1] >= 0.0


def test_weather_parsing_pagination_and_forecast_window() -> None:
    """Checks local-standard index shift, paginated fetch, and >240h refusal."""
    page1_hours = [
        _weather_hour(f"2026-07-15T{h:02d}:00:00Z") for h in range(0, 24)
    ]
    page2_hours = [
        _weather_hour(f"2026-07-16T{h:02d}:00:00Z") for h in range(0, 6)
    ]

    mock_client = MagicMock()
    mock_client.get_json.side_effect = [
        {"forecastHours": page1_hours, "nextPageToken": "page-2"},
        {"forecastHours": page2_hours},
    ]

    df, utc_offset_h = fetch_hourly_weather_forecast(
        lat=41.0,
        lon=29.0,
        hours=30,
        client=mock_client,
        page_size=24,
    )
    assert len(df) == 30
    assert utc_offset_h == pytest.approx(3.0)
    assert df.index[0] == pd.Timestamp("2026-07-15 03:00:00")
    assert df.index.tz is None
    assert all(col in df.columns for col in _EXPECTED_EPW_COLUMNS)

    # Forecast window accepts <= 240h cleanly
    sel = select_window(df, mode="forecast", wall_temp_tier="empirical")
    assert len(sel) == 30

    # Refuses > 240h when wall_temp_tier == "energyplus" without explicit override
    long_idx = pd.date_range("2026-07-01", periods=241, freq="h")
    long_df = pd.DataFrame({"dry_bulb_c": 30.0}, index=long_idx)
    with pytest.raises(AnnualEnergyPlusWindowRefusedError):
        select_window(long_df, mode="forecast", wall_temp_tier="energyplus")

    # Verify single payload parser directly
    parsed_df, _ = parse_weather_forecast_to_df(
        {"forecastHours": page1_hours[:3]},
        lat=41.0,
        lon=29.0,
    )
    assert parsed_df["dq_flag"].iloc[0] == "GMAPS_WEATHER_API"


def test_air_quality_parsing_and_parcel_annotation() -> None:
    """Checks ambient Air Quality provenance and parcel summary attachment."""
    aq = parse_air_quality_response(_sample_aq_payload())
    assert aq["aqi"] == 68
    assert aq["is_canyon_dispersed"] is False
    assert aq["aq_provenance"] == AQ_AMBIENT_PROVENANCE

    parcels = gpd.GeoDataFrame(
        {"osm_id": ["b1"], "data_quality_flag": ["BASELINE"]},
        geometry=[box(500000, 4500000, 500020, 4500020)],
        crs="EPSG:32636",
    )
    annotated = attach_ambient_air_quality(parcels, aq)
    assert annotated.loc[0, "aq_ambient_aqi"] == 68
    assert annotated.loc[0, "aq_pm25_ugm3"] == pytest.approx(18.4)
    assert annotated.loc[0, "aq_provenance"] == AQ_AMBIENT_PROVENANCE
    assert AQ_AMBIENT_PROVENANCE in str(annotated.loc[0, "data_quality_flag"])


def test_stage6_forecast_cli_and_3d_companion_bundle(tmp_path: Path) -> None:
    """Exercises end-to-end Stage 6 forecast CLI + 3D companion export offline."""
    run_dir = tmp_path / "cell_istanbul"
    out_dir = tmp_path / "stage6_out"
    comp_dir = tmp_path / "companion_out"
    run_dir.mkdir(parents=True)

    buildings = gpd.GeoDataFrame(
        {
            "osm_id": ["bld_1", "bld_2"],
            "height_m": [12.0, 12.0],
            "levels": [4, 4],
            "use_class": ["residential", "commercial"],
            "geometry": [
                box(500010.0, 4538000.0, 500030.0, 4538060.0),
                box(500050.0, 4538000.0, 500070.0, 4538060.0),
            ],
        },
        crs="EPSG:32636",
    )
    buildings.to_file(run_dir / "01_buildings_clean.gpkg", driver="GPKG")

    weather_json = tmp_path / "weather.json"
    weather_json.write_text(
        json.dumps(
            {
                "forecastHours": [
                    _weather_hour(
                        "2026-07-15T09:00:00Z",
                        temp_c=35.0,
                        rh_pct=35.0,
                        cloud_pct=5.0,
                    ),
                    _weather_hour(
                        "2026-07-15T10:00:00Z",
                        temp_c=38.0,
                        rh_pct=30.0,
                        cloud_pct=0.0,
                    ),
                ]
            }
        ),
        encoding="utf-8",
    )
    aq_json = tmp_path / "aq.json"
    aq_json.write_text(json.dumps(_sample_aq_payload()), encoding="utf-8")

    stage6_path = forecast_cli_main(
        [
            "--run-dir",
            str(run_dir),
            "--output-dir",
            str(out_dir),
            "--hours",
            "2",
            "--weather-json",
            str(weather_json),
            "--air-quality-json",
            str(aq_json),
            "--with-air-quality",
            "--res-m",
            "10",
            "--buffer-m",
            "20",
        ]
    )
    assert stage6_path == out_dir

    alerts = json.loads((out_dir / "06_mc_risk_alerts.json").read_text())
    assert alerts["risk_tier"] in {
        "No Thermal Stress",
        "Moderate Heat Stress",
        "Strong Heat Stress",
        "Very Strong Heat Stress",
        "Extreme Heat Stress",
    }
    assert alerts["air_quality"]["aq_provenance"] == AQ_AMBIENT_PROVENANCE

    metrics = json.loads((out_dir / "06_mc_exposure_metrics.json").read_text())
    assert metrics["air_quality"]["aqi"] == 68

    summary_gdf = gpd.read_file(out_dir / "06_mc_summary.gpkg")
    assert summary_gdf["aq_provenance"].iloc[0] == AQ_AMBIENT_PROVENANCE

    # Export 3D companion pointing at stage6 outputs
    bundle = companion_cli_main(
        ["--run-dir", str(out_dir), "--output-dir", str(comp_dir)]
    )
    assert bundle["geojson"].is_file()
    assert bundle["manifest"].is_file()
    assert bundle["html"].is_file()
    assert bundle["ai_studio_prompt"].is_file()

    manifest = json.loads(bundle["manifest"].read_text(encoding="utf-8"))
    assert manifest["building_count"] == 2
    assert manifest["api_key_embedded"] is False
    assert manifest["risk_tier"] == alerts["risk_tier"]

    html_text = bundle["html"].read_text(encoding="utf-8")
    assert "<gmp-map-3d" in html_text
    assert "?apiKey=" in html_text
    assert "AIza" not in html_text

    # Guard docs_VALIDATION against unintended writes
    fake_val_run = tmp_path / "docs_VALIDATION" / "phaseE" / "nyc_centre"
    redirected = resolve_companion_output_dir(fake_val_run, output_dir=None)
    assert "docs_VALIDATION" not in redirected.parts
    with pytest.raises(ValueError):
        export_gmaps_companion_bundle(
            out_dir,
            output_dir=fake_val_run / "out",
        )
