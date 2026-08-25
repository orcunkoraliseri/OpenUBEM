"""Deterministic registry and offline validation for the European AMY weather slice.

This module deliberately does *not* retrieve data at import time or during validation.  ERA5
retrieval is an explicit future operation which requires project-owned CDS credentials.  Until
then the registry records the ruled source, station candidates, and gates without pretending that
an EPW file or licence capture exists.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
from datetime import timezone, timedelta
from typing import Mapping

import numpy as np
import pandas as pd

from openubem.microclimate.epw_hourly import read_epw_hourly


@dataclass(frozen=True)
class EuropeanWeatherTarget:
    """A ruled ERA5 candidate, pending diary-date pinning and live acquisition."""

    fold: str
    city: str
    station: str
    wmo: str
    latitude: float
    longitude: float
    raw_era5_window: str
    local_standard_utc_offset: int
    output_filename: str


EUROPEAN_WEATHER_TARGETS: tuple[EuropeanWeatherTarget, ...] = (
    EuropeanWeatherTarget(
        fold="es", city="Madrid", station="Madrid Barajas/Retiro", wmo="08221",
        latitude=40.45, longitude=-3.55, raw_era5_window="2009-01-01/2010-12-31",
        local_standard_utc_offset=1, output_filename="es_madrid_2009_2010.epw",
    ),
    EuropeanWeatherTarget(
        fold="uk", city="London", station="London Heathrow", wmo="03772",
        latitude=51.48, longitude=-0.45, raw_era5_window="2014-01-01/2015-12-31",
        local_standard_utc_offset=0, output_filename="uk_london_2014_2015.epw",
    ),
    EuropeanWeatherTarget(
        fold="it", city="Bologna", station="Bologna Borgo Panigale/Marconi", wmo="16140",
        latitude=44.53, longitude=11.29, raw_era5_window="2013-01-01/2014-12-31",
        local_standard_utc_offset=1, output_filename="it_bologna_2013_2014.epw",
    ),
)

_REQUIRED_ERA5_VARIABLES = ("2t", "2d", "sp", "10u", "10v", "ssrd", "fdir", "tcc", "tp")
_REQUIRED_EPW_COLUMNS = (
    "dry_bulb_c", "dew_point_c", "relative_humidity_pct", "atmospheric_pressure_pa",
    "global_horizontal_wm2", "direct_normal_wm2", "diffuse_horizontal_wm2",
    "wind_speed_ms", "wind_direction_deg",
)


def cds_credentials_configured(
    *, environ: Mapping[str, str] | None = None, home: Path | None = None
) -> bool:
    """Return whether CDS configuration exists without opening or exposing a secret."""
    env = os.environ if environ is None else environ
    if env.get("CDSAPI_KEY"):
        return True
    if home is None:
        configured_home = env.get("USERPROFILE")
        if not configured_home:
            return False
        base = Path(configured_home)
    else:
        base = Path(home)
    return (base / ".cdsapirc").is_file()


def ruled_not_pinned_registry() -> dict[str, object]:
    """Return the JSON-safe registry state allowed before raw weather is acquired.

    The status is intentionally not promotable by this function: the diary-date pinning,
    licence text served by CDS, file digest, all six gates, and EnergyPlus smoke evidence are
    separate acceptance facts.
    """
    targets = []
    for target in EUROPEAN_WEATHER_TARGETS:
        row = asdict(target)
        row.update({
            "status": "RULED_NOT_PINNED",
            "weather_file": None,
            "sha256": None,
            "licence_text_at_download": None,
            "licence_status": "CAPTURE_AT_DOWNLOAD",
            "diary_window": None,
            "diary_window_status": "RULED_NOT_PINNED",
            "acquisition_status": "BLOCKED_NO_CDS_CREDENTIALS",
            "validation": {
                "gate_1_header": "PENDING_FILE",
                "gate_2_8760_continuity": "PENDING_FILE",
                "gate_3_no_missing_mandatory_fields": "PENDING_FILE",
                "gate_4_physical_and_solar_bounds": "PENDING_FILE",
                "gate_5_monthly_national_benchmark": "PENDING_FILE_AND_BENCHMARK",
                "gate_6_energyplus_smoke": "PENDING_FILE",
            },
        })
        targets.append(row)
    return {
        "schema_version": 1,
        "status": "RULED_NOT_PINNED",
        "source": "ERA5 (Copernicus Climate Change Service)",
        "conversion_route": "cdsapi -> pvlib; Perez/DISC; local standard time without DST",
        "required_era5_variables": list(_REQUIRED_ERA5_VARIABLES),
        "licence_requirement": "Capture the licence text served by CDS at download time; do not substitute a secondary quotation.",
        "targets": targets,
    }


def write_ruled_not_pinned_registry(path: Path | str) -> Path:
    """Write the deterministic pre-acquisition registry; never overwrite an acquired registry."""
    output = Path(path)
    if output.exists():
        existing = json.loads(output.read_text(encoding="utf-8"))
        if existing.get("status") != "RULED_NOT_PINNED":
            raise ValueError(f"refusing to overwrite non-template weather registry: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(ruled_not_pinned_registry(), indent=2) + "\n", encoding="utf-8")
    return output


def sha256_file(path: Path | str) -> str:
    """Return a content digest only after a weather file is actually present."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_epw_preflight(epw_path: Path | str) -> dict[str, object]:
    """Run offline DR08 gates 1--4 for an acquired, non-leap EPW file.

    Gate 5 needs an external national-station monthly benchmark and gate 6 needs an EnergyPlus
    invocation, so neither is represented as passed here.  The caller must attach those two
    evidence records before promoting a registry row.
    """
    epw_path = Path(epw_path)
    with epw_path.open(encoding="utf-8", errors="replace") as stream:
        header = [stream.readline().rstrip("\r\n") for _ in range(8)]
    if not header[0].startswith("LOCATION,"):
        raise ValueError("DR08 gate 1: first EPW header line must start with LOCATION,")
    if any(not line for line in header):
        raise ValueError("DR08 gate 1: EPW requires eight non-empty header lines")

    hourly = read_epw_hourly(epw_path)
    if len(hourly) != 8760:
        raise ValueError(f"DR08 gate 2: expected 8760 non-leap rows, found {len(hourly)}")
    expected = pd.date_range("2001-01-01", periods=8760, freq="h")
    if not hourly.index.equals(expected):
        raise ValueError("DR08 gate 2: month/day/hour rows are not continuous in EPW order")
    if hourly.loc[:, _REQUIRED_EPW_COLUMNS].isna().any().any():
        raise ValueError("DR08 gate 3: mandatory EPW fields contain a missing-value sentinel")

    _check_range(hourly, "dry_bulb_c", -30.0, 50.0)
    if (hourly["dew_point_c"] > hourly["dry_bulb_c"]).any():
        raise ValueError("DR08 gate 4: dew point exceeds dry-bulb temperature")
    _check_range(hourly, "relative_humidity_pct", 0.0, 100.0)
    _check_range(hourly, "atmospheric_pressure_pa", 85000.0, 106000.0)
    _check_range(hourly, "global_horizontal_wm2", 0.0, 1367.0)
    _check_range(hourly, "direct_normal_wm2", 0.0, 1200.0)
    if (hourly["diffuse_horizontal_wm2"] > hourly["global_horizontal_wm2"]).any():
        raise ValueError("DR08 gate 4: diffuse horizontal radiation exceeds global horizontal radiation")
    _check_range(hourly, "wind_speed_ms", 0.0, 45.0)
    _check_range(hourly, "wind_direction_deg", 0.0, 360.0)
    _check_solar_closure(hourly, header[0])

    return {
        "file": str(epw_path),
        "sha256": sha256_file(epw_path),
        "gate_1_header": "PASS",
        "gate_2_8760_continuity": "PASS",
        "gate_3_no_missing_mandatory_fields": "PASS",
        "gate_4_physical_and_solar_bounds": "PASS",
        "gate_5_monthly_national_benchmark": "PENDING_EXTERNAL_BENCHMARK",
        "gate_6_energyplus_smoke": "PENDING_ENERGYPLUS",
    }


def _check_range(hourly: pd.DataFrame, column: str, lower: float, upper: float) -> None:
    values = hourly[column].to_numpy(dtype=float)
    if np.any((values < lower) | (values > upper)):
        raise ValueError(f"DR08 gate 4: {column} outside [{lower}, {upper}]")


def _check_solar_closure(hourly: pd.DataFrame, location_header: str) -> None:
    """Check DR08's daytime GHI = DHI + DNI cos(zenith) tolerance."""
    fields = location_header.split(",")
    try:
        latitude, longitude, utc_offset, elevation = map(float, fields[6:10])
    except (ValueError, IndexError) as exc:
        raise ValueError("DR08 gate 1: LOCATION coordinates/timezone/elevation are invalid") from exc
    from pvlib.solarposition import get_solarposition

    local_time = hourly.index.tz_localize(timezone(timedelta(hours=utc_offset)))
    position = get_solarposition(local_time, latitude=latitude, longitude=longitude, altitude=elevation)
    cosine_zenith = np.cos(np.deg2rad(position["apparent_zenith"].to_numpy()))
    daytime = cosine_zenith > 0.0
    predicted = hourly["diffuse_horizontal_wm2"].to_numpy() + (
        hourly["direct_normal_wm2"].to_numpy() * cosine_zenith
    )
    closure_error = np.abs(hourly["global_horizontal_wm2"].to_numpy() - predicted)
    if np.any(closure_error[daytime] > 5.0):
        raise ValueError("DR08 gate 4: daytime solar closure exceeds 5 W/m2")
