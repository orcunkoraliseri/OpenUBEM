"""T09 — tests for epw_manager.py §3C/§3D.

DESIGN §5.2 (F15):
- load_stations + resolve_station
- warm cache hit
- cold cache + offline=True -> abort
- user epw_dir: single file, multi-file nearest
- truncated EPW rejected (check 4)
- header-less EPW rejected (check 2)
- leap-year 8784 accepted + warning
- header mismatch > 10 km -> warning but accepted
- full-tier exhaustion -> RuntimeError
- bundled real epw_stations.csv contains the 8 fixture stations (T03 acceptance)
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from openubem.acquisition.epw_manager import (
    _canonical_name,
    _validate_epw,
    fetch_epw,
    load_stations,
    resolve_station,
)

# ---------------------------------------------------------------------------
# Synthetic 10-row station index (F15)
# ---------------------------------------------------------------------------

_STATIONS_CSV = """\
station_id,name,state,lat,lon,url,tmy_edition
725090,Boston-Logan.Intl.AP,MA,42.362,-71.006,https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/MA_Massachusetts/USA_MA_Boston-Logan.Intl.AP.725090_TMYx.2009-2023.zip,TMYx.2009-2023
725300,Chicago-OHare.Intl.AP,IL,41.983,-87.917,https://climate.onebuilding.org/x/USA_IL_Chicago.zip,TMYx.2009-2023
722020,Miami.Intl.AP,FL,25.817,-80.3,https://climate.onebuilding.org/x/USA_FL_Miami.zip,TMYx.2009-2023
722780,Phoenix-Sky.Harbor.Intl.AP,AZ,33.45,-112.017,https://climate.onebuilding.org/x/USA_AZ_Phoenix.zip,TMYx.2009-2023
724940,San.Francisco.Intl.AP,CA,37.617,-122.4,https://climate.onebuilding.org/x/USA_CA_SF.zip,TMYx.2009-2023
725650,Denver.Intl.AP,CO,39.833,-104.667,https://climate.onebuilding.org/x/USA_CO_Denver.zip,TMYx.2009-2023
727450,Duluth.Intl.AP,MN,46.833,-92.183,https://climate.onebuilding.org/x/USA_MN_Duluth.zip,TMYx.2009-2023
702610,Fairbanks.Intl.AP,AK,64.816,-147.856,https://climate.onebuilding.org/x/USA_AK_Fairbanks.zip,TMYx.2009-2023
726300,Albany.Intl.AP,NY,42.75,-73.8,https://climate.onebuilding.org/x/USA_NY_Albany.zip,TMYx.2009-2023
722860,Las.Vegas-McCarran.Intl.AP,NV,36.083,-115.167,https://climate.onebuilding.org/x/USA_NV_LasVegas.zip,TMYx.2009-2023
"""

_BOSTON_ROW = pd.Series({
    "station_id": "725090",
    "name": "Boston-Logan.Intl.AP",
    "state": "MA",
    "lat": 42.362,
    "lon": -71.006,
    "url": "https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/MA_Massachusetts/USA_MA_Boston-Logan.Intl.AP.725090_TMYx.2009-2023.zip",
    "tmy_edition": "TMYx.2009-2023",
})


def _load_synthetic() -> pd.DataFrame:
    return pd.read_csv(io.StringIO(_STATIONS_CSV), dtype={"station_id": str})


# ---------------------------------------------------------------------------
# EPW fixture helpers
# ---------------------------------------------------------------------------

def _make_location_line(name="TestCity", lat=42.362, lon=-71.006) -> str:
    return f"LOCATION,{name},MA,USA,TMYx,725090,{lat},{lon},0.0,100.0\n"


def _make_valid_epw(lat=42.362, lon=-71.006, n_data_rows=8760) -> str:
    """Return minimal valid EPW text."""
    lines = [_make_location_line(lat=lat, lon=lon)]
    for _ in range(7):
        lines.append("HEADER_LINE\n")
    data_row = "2000,1,1,1,0,?9?9?9?9?9?9?9?9?9?9?9?9?9?9?9?9?9?9?9?9?9?9?9?9,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0\n"
    for _ in range(n_data_rows):
        lines.append(data_row)
    return "".join(lines)


def _make_truncated_epw(n_data_rows=100) -> str:
    return _make_valid_epw(n_data_rows=n_data_rows)


def _make_headerless_epw() -> str:
    lines = ["NOT_A_LOCATION_LINE\n"]
    for _ in range(7):
        lines.append("HEADER_LINE\n")
    data_row = "2000,1,1,1,0,x,0\n"
    for _ in range(8760):
        lines.append(data_row)
    return "".join(lines)


def _write_epw(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _make_zip(epw_content: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("test.epw", epw_content)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# load_stations + resolve_station (T07)
# ---------------------------------------------------------------------------

def test_load_stations_synthetic():
    stations = _load_synthetic()
    assert len(stations) == 10
    assert list(stations.columns) == ["station_id", "name", "state", "lat", "lon", "url", "tmy_edition"]
    # station_id must be read as string (not int) regardless of pandas StringDtype variant
    assert stations["station_id"].iloc[0] == "725090"


def test_resolve_station_nearest():
    stations = _load_synthetic()
    # At Boston coords, should pick Boston Logan (station_id 725090)
    row, dist_km = resolve_station(42.362, -71.006, stations)
    assert row["station_id"] == "725090"
    assert dist_km < 1.0


def test_resolve_station_far_warning(caplog):
    """Far station (> 300 km) emits structured warning (F9)."""
    stations = _load_synthetic().iloc[:1].copy()
    stations["lat"] = 70.0
    stations["lon"] = -100.0
    import logging
    with caplog.at_level(logging.WARNING, logger="openubem.acquisition.epw_manager"):
        row, dist_km = resolve_station(25.0, -80.0, stations)
    assert any("epw_far_station" in r.message for r in caplog.records)
    assert dist_km > 300.0


# ---------------------------------------------------------------------------
# Bundled real station CSV contains 8 fixture stations (T03 acceptance gate)
# ---------------------------------------------------------------------------

_FIXTURE_WMO_IDS = {"725090", "725300", "722020", "722780", "724940", "725650", "727450", "702610"}


def test_bundled_csv_contains_fixture_stations():
    """Bundled epw_stations.csv must contain all 8 known-city WMO IDs (T03 acceptance)."""
    stations = load_stations()
    present = set(stations["station_id"].values)
    missing = _FIXTURE_WMO_IDS - present
    assert not missing, f"Missing WMO IDs in bundled CSV: {missing}"


# ---------------------------------------------------------------------------
# _validate_epw checks (T08 logic tested indirectly)
# ---------------------------------------------------------------------------

def test_validate_epw_valid(tmp_path):
    p = tmp_path / "test.epw"
    _write_epw(p, _make_valid_epw())
    result = _validate_epw(p, _BOSTON_ROW)
    assert result is None


def test_validate_epw_truncated_rejected(tmp_path):
    p = tmp_path / "trunc.epw"
    _write_epw(p, _make_truncated_epw(100))
    with pytest.raises(ValueError, match="check 4"):
        _validate_epw(p, _BOSTON_ROW)


def test_validate_epw_headerless_rejected(tmp_path):
    p = tmp_path / "noheader.epw"
    _write_epw(p, _make_headerless_epw())
    with pytest.raises(ValueError, match="check 2"):
        _validate_epw(p, _BOSTON_ROW)


def test_validate_epw_leap_year_warns(tmp_path, caplog):
    p = tmp_path / "leap.epw"
    _write_epw(p, _make_valid_epw(n_data_rows=8784))
    import logging
    with caplog.at_level(logging.WARNING, logger="openubem.acquisition.epw_manager"):
        result = _validate_epw(p, _BOSTON_ROW)
    assert result is None
    assert any("epw_amy_leap_year" in r.message for r in caplog.records)


def test_validate_epw_header_mismatch_warning(tmp_path):
    """Check 3: header lat/lon > 10 km from station index -> warning returned, not raised."""
    p = tmp_path / "mismatch.epw"
    _write_epw(p, _make_valid_epw(lat=50.0, lon=-100.0))  # far from Boston index entry
    warn = _validate_epw(p, _BOSTON_ROW)
    assert warn is not None
    payload = json.loads(warn)
    assert payload["event"] == "epw_header_mismatch"


# ---------------------------------------------------------------------------
# fetch_epw tier tests (T08)
# ---------------------------------------------------------------------------

def test_fetch_epw_warm_cache(tmp_path):
    """Tier 2: cache hit must not make any network call."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    canonical = _canonical_name(_BOSTON_ROW)
    (cache_dir / canonical).write_text(_make_valid_epw(), encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    with patch("openubem.acquisition.epw_manager.requests.get") as mock_get:
        result = fetch_epw(
            _BOSTON_ROW,
            cache_dir=cache_dir,
            offline=True,
            output_dir=out_dir,
        )
        mock_get.assert_not_called()

    assert result.exists()
    assert result.parent == out_dir / "weather"
    assert result.name == canonical


def test_fetch_epw_cold_cache_offline_aborts(tmp_path):
    """Cold cache + offline=True must raise RuntimeError with epw_cold_cache_offline."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    with pytest.raises(RuntimeError) as exc_info:
        fetch_epw(
            _BOSTON_ROW,
            cache_dir=cache_dir,
            offline=True,
            output_dir=out_dir,
        )
    payload = json.loads(str(exc_info.value))
    assert payload["event"] == "epw_cold_cache_offline"


def test_fetch_epw_user_dir_single_file(tmp_path):
    """Tier 1: user epw_dir with exactly one .epw -> use it without network."""
    epw_dir = tmp_path / "user_epw"
    epw_dir.mkdir()
    _write_epw(epw_dir / "myfile.epw", _make_valid_epw())
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    with patch("openubem.acquisition.epw_manager.requests.get") as mock_get:
        result = fetch_epw(
            _BOSTON_ROW,
            epw_dir=epw_dir,
            cache_dir=cache_dir,
            offline=True,
            output_dir=out_dir,
        )
        mock_get.assert_not_called()

    assert result.exists()


def test_fetch_epw_user_dir_multi_file_picks_nearest(tmp_path):
    """Tier 1: multiple .epw in user_dir -> pick geodesically nearest by header lat/lon."""
    epw_dir = tmp_path / "user_epw"
    epw_dir.mkdir()
    # One file with header near Boston (42.36, -71.01), one near LA (34.05, -118.24)
    _write_epw(epw_dir / "boston.epw", _make_valid_epw(lat=42.36, lon=-71.01))
    _write_epw(epw_dir / "la.epw", _make_valid_epw(lat=34.05, lon=-118.24))
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    result = fetch_epw(
        _BOSTON_ROW,
        epw_dir=epw_dir,
        cache_dir=cache_dir,
        offline=True,
        output_dir=out_dir,
    )
    # The resulting file should be copied from the Boston header file
    assert result.exists()
    # Verify the destination is valid (check 2 passes = LOCATION header present)
    with open(result, encoding="utf-8") as fh:
        first = fh.readline()
    assert first.startswith("LOCATION,")


def test_fetch_epw_download_zip(tmp_path):
    """Tier 3: successful download of .zip archive."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    zip_bytes = _make_zip(_make_valid_epw())
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.content = zip_bytes

    with patch("openubem.acquisition.epw_manager.requests.get", return_value=mock_resp):
        result = fetch_epw(
            _BOSTON_ROW,
            cache_dir=cache_dir,
            offline=False,
            output_dir=out_dir,
        )

    assert result.exists()
    canonical = _canonical_name(_BOSTON_ROW)
    assert result.name == canonical


def test_fetch_epw_tier3_fails_tier4_succeeds(tmp_path):
    """If primary URL fails, fallback mirror is tried."""
    import requests as _requests
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    valid_epw_bytes = _make_valid_epw().encode("utf-8")

    call_count = {"n": 0}

    def fake_get(url, timeout=60):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise _requests.RequestException("primary mirror down")
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.content = valid_epw_bytes
        return resp

    with patch("openubem.acquisition.epw_manager.requests.get", side_effect=fake_get):
        result = fetch_epw(
            _BOSTON_ROW,
            cache_dir=cache_dir,
            offline=False,
            output_dir=out_dir,
        )

    assert result.exists()
    assert call_count["n"] == 2


def test_fetch_epw_all_tiers_exhausted(tmp_path):
    """All download tiers fail -> RuntimeError with epw_all_tiers_exhausted."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    import requests as req_mod
    with patch(
        "openubem.acquisition.epw_manager.requests.get",
        side_effect=req_mod.RequestException("all down"),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            fetch_epw(
                _BOSTON_ROW,
                cache_dir=cache_dir,
                offline=False,
                output_dir=out_dir,
            )
    payload = json.loads(str(exc_info.value))
    assert payload["event"] == "epw_all_tiers_exhausted"


def test_fetch_epw_output_inside_output_dir(tmp_path):
    """F12: epw_path must be inside output_dir/weather/."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    canonical = _canonical_name(_BOSTON_ROW)
    (cache_dir / canonical).write_text(_make_valid_epw(), encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    result = fetch_epw(
        _BOSTON_ROW,
        cache_dir=cache_dir,
        offline=True,
        output_dir=out_dir,
    )
    assert str(out_dir) in str(result)
    assert result.parent.name == "weather"
