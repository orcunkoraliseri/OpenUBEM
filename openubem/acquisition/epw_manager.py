"""Step 2.1 §3C/§3D — EPW station resolution, download, validation, and run-local copy."""
from __future__ import annotations

import io
import json
import logging
import os
import shutil
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
import requests

from openubem import config

logger = logging.getLogger("openubem.acquisition.epw_manager")


def load_stations(path: Path | None = None) -> pd.DataFrame:
    """Load the bundled epw_stations.csv (or a provided path for testing)."""
    if path is not None:
        return pd.read_csv(str(path), dtype={"station_id": str})
    from importlib.resources import files
    data = files("openubem.data").joinpath("epw_stations.csv")
    return pd.read_csv(io.StringIO(data.read_text(encoding="utf-8")), dtype={"station_id": str})


def resolve_station(
    lat: float,
    lon: float,
    stations: pd.DataFrame,
) -> tuple[pd.Series, float]:
    """Return (nearest station row, distance_km) via geodesic argmin (DESIGN lines 74-82, F8)."""
    geod = pyproj.Geod(ellps="WGS84")
    _, _, dist_m = geod.inv(
        np.full(len(stations), lon),
        np.full(len(stations), lat),
        stations["lon"].to_numpy(),
        stations["lat"].to_numpy(),
    )
    i = int(np.argmin(dist_m))
    dist_km = dist_m[i] / 1_000.0
    if dist_km > config.EPW_MAX_STATION_KM:
        logger.warning(
            json.dumps({
                "event": "epw_far_station",
                "station_id": stations.iloc[i]["station_id"],
                "distance_km": round(dist_km, 2),
            })
        )
    return stations.iloc[i], dist_km


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _canonical_name(station: pd.Series) -> str:
    """Canonical EPW filename: basename of url with .zip -> .epw (PLAN §5 P4)."""
    url = station["url"]
    name = url.rsplit("/", 1)[-1]
    if name.endswith(".zip"):
        name = name[:-4] + ".epw"
    return name


def _parse_location_line(line: str) -> tuple[str, float, float] | None:
    """Parse the LOCATION header line; return (name, lat, lon) or None on failure."""
    try:
        parts = line.strip().split(",")
        if len(parts) < 8:
            return None
        name = parts[1].strip()
        lat = float(parts[6])
        lon = float(parts[7])
        return name, lat, lon
    except (ValueError, IndexError):
        return None


def _validate_epw(tmp_path: Path, station: pd.Series) -> str | None:
    """Apply DESIGN §3D checks 2-4.

    Returns a warning string if check 3 fires (header/index mismatch > 10 km) or None.
    Raises ValueError (reject) on check 2 or 4 failures.
    """
    # Check 2: first line starts with LOCATION, and is parseable
    with open(tmp_path, encoding="utf-8", errors="replace") as fh:
        first_line = fh.readline()
        if not first_line.startswith("LOCATION,"):
            raise ValueError("EPW check 2: first line does not start with LOCATION,")
        parsed = _parse_location_line(first_line)
        if parsed is None:
            raise ValueError("EPW check 2: LOCATION line unparseable")
        _, hdr_lat, hdr_lon = parsed

        # Check 3: header lat/lon vs station index geodesic <= 10 km
        geod = pyproj.Geod(ellps="WGS84")
        _, _, dist_m = geod.inv(float(station["lon"]), float(station["lat"]), hdr_lon, hdr_lat)
        warning = None
        if dist_m / 1_000.0 > 10.0:
            warning = json.dumps({
                "event": "epw_header_mismatch",
                "station_id": station["station_id"],
                "header_lat": hdr_lat,
                "header_lon": hdr_lon,
                "index_lat": float(station["lat"]),
                "index_lon": float(station["lon"]),
                "dist_km": round(dist_m / 1_000.0, 2),
            })

        # Check 4: data row count must be 8760 or 8784
        # Skip the 8 header rows, then count data rows
        for _ in range(7):
            fh.readline()
        data_rows = sum(1 for _ in fh)

    if data_rows not in (8760, 8784):
        raise ValueError(
            f"EPW check 4: data row count {data_rows} not in {{8760, 8784}}"
        )
    if data_rows == 8784:
        logger.warning(
            json.dumps({"event": "epw_amy_leap_year", "station_id": station["station_id"]})
        )
    return warning


def _try_download(url: str, tmp_path: Path, station: pd.Series) -> bool:
    """Download URL to tmp_path (handling .zip), run validation gate.

    Returns True on success, False if the validation gate rejects it.
    Raises requests.RequestException on network errors (caller catches).
    """
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    if url.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            epw_names = [n for n in zf.namelist() if n.lower().endswith(".epw")]
            if not epw_names:
                return False
            with zf.open(epw_names[0]) as src, open(tmp_path, "wb") as dst:
                dst.write(src.read())
    else:
        tmp_path.write_bytes(resp.content)

    try:
        warn = _validate_epw(tmp_path, station)
    except ValueError:
        tmp_path.unlink(missing_ok=True)
        return False
    if warn:
        logger.warning(warn)
    return True


def _epw_from_user_dir(
    epw_dir: Path,
    station: pd.Series,
) -> Path | None:
    """Tier 1 of F10: user-provided directory.

    Exactly one .epw -> use it; several -> geodesically nearest by header lat/lon.
    """
    candidates = list(epw_dir.glob("*.epw"))
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    geod = pyproj.Geod(ellps="WGS84")
    best: Path | None = None
    best_dist = float("inf")
    for cand in candidates:
        try:
            with open(cand, encoding="utf-8", errors="replace") as fh:
                first_line = fh.readline()
            parsed = _parse_location_line(first_line)
            if parsed is None:
                continue
            _, hdr_lat, hdr_lon = parsed
            _, _, dist_m = geod.inv(
                float(station["lon"]), float(station["lat"]), hdr_lon, hdr_lat
            )
            if dist_m < best_dist:
                best_dist = dist_m
                best = cand
        except OSError:
            continue
    return best


def fetch_epw(
    station: pd.Series,
    *,
    epw_dir: Path | None = None,
    cache_dir: Path | None = None,
    offline: bool = False,
    output_dir: Path,
) -> Path:
    """Resolve, validate, and copy EPW for station to output_dir/weather/.

    Resolution order (DESIGN lines 86-87, F10):
      1. user epw_dir
      2. EPW_CACHE_DIR / canonical filename (cache hit)
      3. climate.onebuilding.org (primary mirror)
      4. energyplus.net/weather (fallback mirror)
    With offline=True, tiers 3-4 are skipped.

    Returns the run-local copy path (inside output_dir/weather/).
    """
    if cache_dir is None:
        cache_dir = config.EPW_CACHE_DIR
    cache_dir = Path(cache_dir)
    canonical = _canonical_name(station)
    weather_dir = Path(output_dir) / "weather"
    weather_dir.mkdir(parents=True, exist_ok=True)
    dest = weather_dir / canonical

    # Tier 1: user epw_dir
    if epw_dir is not None:
        src = _epw_from_user_dir(Path(epw_dir), station)
        if src is not None:
            tmp = dest.with_suffix(".epw.tmp")
            shutil.copy2(src, tmp)
            try:
                warn = _validate_epw(tmp, station)
            except ValueError:
                tmp.unlink(missing_ok=True)
            else:
                if warn:
                    logger.warning(warn)
                os.replace(tmp, dest)
                return dest

    # Tier 2: cache hit
    cached = cache_dir / canonical
    if cached.exists():
        shutil.copy2(cached, dest)
        return dest

    if offline:
        raise RuntimeError(
            json.dumps({
                "event": "epw_cold_cache_offline",
                "station_id": station["station_id"],
                "canonical": canonical,
                "message": "offline=True and no cached EPW found.",
            })
        )

    # Tiers 3 & 4: download
    cache_dir.mkdir(parents=True, exist_ok=True)
    tmp = cache_dir / (canonical + ".tmp")

    mirrors = [
        station["url"],  # primary (P3: may be .zip)
        f"{config.EPW_FALLBACK_MIRROR}/{canonical}",  # energyplus.net bare .epw
    ]
    for url in mirrors:
        try:
            if _try_download(url, tmp, station):
                os.replace(tmp, cached)
                shutil.copy2(cached, dest)
                return dest
        except (requests.RequestException, OSError):
            tmp.unlink(missing_ok=True)

    raise RuntimeError(
        json.dumps({
            "event": "epw_all_tiers_exhausted",
            "station_id": station["station_id"],
            "canonical": canonical,
            "message": "All EPW resolution tiers exhausted with no valid EPW.",
        })
    )
