"""Offline unit tests for Google Maps HTTP client, key resolution, and BQ scout."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest

from openubem.acquisition.gmaps_bigquery_scout import (
    build_places_insights_query,
    build_street_view_insights_query,
    execute_parameterized_bq_query,
    summarize_places_insights_df,
    summarize_svi_df,
    validate_bq_table_id,
)
from openubem.acquisition.gmaps_client import (
    GmapsApiError,
    GmapsAuthError,
    GmapsHttpClient,
    GmapsOfflineError,
    build_cache_key,
    resolve_gmaps_api_key,
)


def _mock_response(
    status_code: int = 200,
    json_data: dict[str, Any] | None = None,
    content: bytes = b"",
    text: str = "",
) -> MagicMock:
    """Creates a mocked HTTP response object for client tests.

    Args:
        status_code: HTTP status code returned by the mock.
        json_data: Optional decoded JSON payload.
        content: Optional raw response bytes.
        text: Optional raw response text snippet.

    Returns:
        Configured ``MagicMock`` mimicking ``requests.Response``.
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = content
    resp.text = text or (json.dumps(json_data) if json_data is not None else "")
    resp.json.return_value = json_data if json_data is not None else {}
    return resp


def test_resolve_api_key_precedence_and_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies explicit -> env var -> .env precedence and missing-key failure."""
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        '# comment line\nexport GOOGLE_MAPS_API_KEY="dotenv-secret-123"\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)

    assert resolve_gmaps_api_key(dotenv_paths=[dotenv]) == "dotenv-secret-123"
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "env-secret-456")
    assert resolve_gmaps_api_key(dotenv_paths=[dotenv]) == "env-secret-456"
    assert (
        resolve_gmaps_api_key(api_key="explicit-789", dotenv_paths=[dotenv])
        == "explicit-789"
    )

    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    empty_env = tmp_path / "missing.env"
    with pytest.raises(GmapsAuthError):
        resolve_gmaps_api_key(dotenv_paths=[empty_env])


def test_cache_key_excludes_api_credentials() -> None:
    """Ensures SHA-256 cache digests stay invariant when API credentials change."""
    k1 = build_cache_key(
        "GET",
        "https://solar.googleapis.com/v1/dataLayers:get?key=SECRET_A&radiusMeters=50",
        params={"key": "SECRET_A", "view": "FULL_LAYERS"},
        headers={"X-Goog-Api-Key": "SECRET_A", "X-Goog-FieldMask": "places.id"},
    )
    k2 = build_cache_key(
        "GET",
        "https://solar.googleapis.com/v1/dataLayers:get?key=SECRET_B&radiusMeters=50",
        params={"apiKey": "SECRET_B", "view": "FULL_LAYERS"},
        headers={"X-Goog-Api-Key": "SECRET_B", "X-Goog-FieldMask": "places.id"},
    )
    assert k1 == k2


def test_http_client_disk_cache_offline_and_errors(tmp_path: Path) -> None:
    """Checks GET/POST/binary disk caching, offline enforcement, and errors."""
    session = MagicMock()
    session.request.return_value = _mock_response(
        200,
        json_data={"solarPotential": {"maxArrayPanelsCount": 12}},
    )
    client = GmapsHttpClient(
        api_key="test-key-do-not-leak",
        cache_dir=tmp_path / "cache",
        offline=False,
        session=session,
    )

    first = client.get_json(
        "https://solar.googleapis.com/v1/buildingInsights:findClosest",
        params={"location.latitude": 41.0, "location.longitude": 29.0},
    )
    assert first["solarPotential"]["maxArrayPanelsCount"] == 12
    assert session.request.call_count == 1

    offline_client = GmapsHttpClient(
        api_key=None,
        cache_dir=tmp_path / "cache",
        offline=True,
        session=session,
    )
    second = offline_client.get_json(
        "https://solar.googleapis.com/v1/buildingInsights:findClosest",
        params={"location.latitude": 41.0, "location.longitude": 29.0},
    )
    assert second == first
    assert session.request.call_count == 1

    with pytest.raises(GmapsOfflineError):
        offline_client.post_json(
            "https://places.googleapis.com/v1/places:searchNearby",
            json_body={"maxResultCount": 5},
        )

    session.request.return_value = _mock_response(403, text="Forbidden")
    with pytest.raises(GmapsAuthError) as auth_exc:
        client.get_json("https://solar.googleapis.com/v1/uncached")
    assert "test-key-do-not-leak" not in str(auth_exc.value)

    session.request.return_value = _mock_response(500, text="Internal error")
    with pytest.raises(GmapsApiError) as api_exc:
        client.get_json("https://solar.googleapis.com/v1/server_err")
    assert api_exc.value.status_code == 500
    assert "test-key-do-not-leak" not in str(api_exc.value)

    session.request.return_value = _mock_response(200, content=b"TIFF_BYTES")
    out_bin = client.download_binary(
        "https://solar.googleapis.com/v1/geoTiff?id=123",
        dest_path=tmp_path / "dsm.tif",
    )
    assert out_bin.read_bytes() == b"TIFF_BYTES"
    cached_bin = offline_client.download_binary(
        "https://solar.googleapis.com/v1/geoTiff?id=123",
    )
    assert cached_bin.read_bytes() == b"TIFF_BYTES"


def test_bigquery_scout_validation_parameterized_sql_and_summaries() -> None:
    """Checks strict BQ identifier guards, bind-parameter SQL, and summaries."""
    assert (
        validate_bq_table_id("my_proj.places_insights.places_us")
        == "my_proj.places_insights.places_us"
    )
    for bad_id in (
        "proj.ds.tbl; DROP TABLE users",
        "proj.ds.tbl`",
        "singlepart",
        "bad space.ds.tbl",
    ):
        with pytest.raises(ValueError):
            validate_bq_table_id(bad_id)

    sql, params = build_places_insights_query(
        "proj.ds.places",
        min_lon=28.9,
        min_lat=41.0,
        max_lon=29.0,
        max_lat=41.1,
        included_types=["restaurant", "supermarket"],
    )
    assert "@min_lon" in sql and "@max_lat" in sql
    assert "28.9" not in sql
    assert "@included_types" in sql and "restaurant" not in sql
    assert params["min_lon"] == 28.9
    assert params["included_types"] == ["restaurant", "supermarket"]

    svi_sql, svi_params = build_street_view_insights_query(
        "proj.ds.svi",
        min_lon=-74.0,
        min_lat=40.7,
        max_lon=-73.9,
        max_lat=40.8,
    )
    assert "ST_MAKEENVELOPE(@min_lon, @min_lat, @max_lon, @max_lat)" in svi_sql
    assert svi_params["max_lat"] == 40.8

    places_df = pd.DataFrame(
        [
            {"primary_type": "restaurant", "place_count": 8},
            {"primary_type": "supermarket", "place_count": 2},
            {"primary_type": "apartment_building", "place_count": 30},
        ]
    )
    report = summarize_places_insights_df(places_df, process_load_threshold=0.15)
    assert report.total_places == 40
    assert report.food_service_count == 8
    assert report.supermarket_count == 2
    assert report.high_process_load_share == pytest.approx(0.25)
    assert report.high_process_load_alert is True

    svi_df = pd.DataFrame(
        {"wwr_observed": [0.25, 0.35], "levels_observed": [4, 6]}
    )
    svi_sum = summarize_svi_df(svi_df)
    assert svi_sum["n_assets"] == 2
    assert svi_sum["wwr_mean"] == pytest.approx(0.30)
    assert svi_sum["levels_median"] == pytest.approx(5.0)

    mock_client = MagicMock()
    mock_job = MagicMock()
    mock_job.to_dataframe.return_value = places_df
    mock_client.query.return_value = mock_job
    out_df = execute_parameterized_bq_query(sql, params, client=mock_client)
    assert len(out_df) == 3
    mock_client.query.assert_called_once_with(sql, job_config=params)
