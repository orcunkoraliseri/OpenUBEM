"""Convert the acquired direct ERA5 archives for the es/uk/it folds into EPWs.

Generalises ``convert_era5_lyon_bron_2023_to_epw.py`` (the reference: ERA5
NetCDF inside monthly CDS zips -> pvlib Perez/DISC decomposition -> EPW in
fixed local standard time, no DST) to the three ``RULED_NOT_PINNED`` targets
of ``openubem/data/weather/weather_registry.json``: es/Madrid, uk/London,
it/Bologna. Fold, city, coordinates and the raw ERA5 window are read from the
registry -- never retyped. Station elevations are not in the registry; they
are taken from ``docs/docs_ACTIVE/europeanLocations/DeepResearch/
DR08_actual_year_weather_sources_and_licences.md`` (Madrid 609 m, London
Heathrow 25 m, Bologna 37 m) and asserted non-null.

Each of these three targets has a 24-month ``raw_era5_window`` (two calendar
years) plus one boundary day, because the fieldwork "diary window" itself
spans two years and ``diary_window_status`` is ``RULED_NOT_PINNED`` for all
three (only ``fr`` carries a pinned diary window). There is therefore no
ruled basis anywhere in the registry for preferring one window year over the
other, and this converter never picks one silently:

- ``--year YYYY`` converts exactly that year, validated against the fold's
  own window; a year outside the window is an error, not a clamp.
- ``--all-years`` converts every complete calendar year in the window (both
  years for es/uk/it), deferring the choice instead of making it.
- with neither flag, a fold whose ``diary_window_status`` is not
  ``RULED_PINNED`` prints ``YEAR_NOT_RULED <fold> <raw_era5_window>`` and is
  skipped -- skipping is not an error.

The output filename stem is taken verbatim from the registry's own
``output_filename`` field, with the emitted year inserted before the
extension (e.g. ``es_madrid_2009_2010.epw`` -> ``es_madrid_2009_2010_y2009.epw``),
so converting both window years never overwrites one with the other.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pvlib
import xarray as xr

REGISTRY_PATH = Path("openubem/data/weather/weather_registry.json")
RAW_ROOT = Path("openubem/data/weather/raw")
OUTPUT_ROOT = Path("openubem/data/weather")

# Not present in the registry; DR08's recommended-station elevations.
# (docs/docs_ACTIVE/europeanLocations/DeepResearch/DR08_actual_year_weather_sources_and_licences.md)
ELEVATIONS_M = {"es": 609.0, "uk": 25.0, "it": 37.0}
ISO3 = {"es": "ESP", "uk": "GBR", "it": "ITA"}

REQUIRED_VARIABLES = {"t2m", "d2m", "sp", "u10", "v10", "ssrd", "fdir", "tcc", "tp"}


def load_fold_targets(registry_path: Path = REGISTRY_PATH) -> dict[str, dict[str, object]]:
    """Read the three RULED_NOT_PINNED targets: fold, city, coordinates, window, filename."""
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    targets: dict[str, dict[str, object]] = {}
    for entry in registry["targets"]:
        if entry.get("status") != "RULED_NOT_PINNED":
            continue
        raw_window = str(entry["raw_era5_window"])
        start_str, end_str = raw_window.split("/")
        start_year = int(start_str[:4])
        end_year = int(end_str[:4])
        fold = str(entry["fold"])
        city = str(entry["city"])
        output_filename = entry.get("output_filename")
        if not output_filename:
            raise ValueError(f"registry entry for fold {fold!r} has no output_filename")
        elevation_m = ELEVATIONS_M.get(fold)
        if elevation_m is None:
            raise ValueError(f"no DR08-sourced elevation recorded for fold {fold!r}")
        targets[fold] = {
            "fold": fold,
            "city": city,
            "station": entry.get("station"),
            "latitude": float(entry["latitude"]),
            "longitude": float(entry["longitude"]),
            "elevation_m": float(elevation_m),
            "utc_offset_hours": int(entry["local_standard_utc_offset"]),
            "start_year": start_year,
            "end_year": end_year,
            "raw_era5_window": raw_window,
            "diary_window": entry.get("diary_window"),
            "diary_window_status": entry.get("diary_window_status"),
            "raw_dir": RAW_ROOT / f"era5_{city.lower()}_{start_year}_{end_year}",
            "output_filename": str(output_filename),
        }
    return targets


def window_years(target: dict[str, object]) -> tuple[int, int]:
    return int(target["start_year"]), int(target["end_year"])


def resolve_year(target: dict[str, object], requested_year: int | None) -> int | None:
    """Return the year to convert, or None if it is not ruled and must be refused."""
    start_year, end_year = window_years(target)
    if requested_year is not None:
        if requested_year not in (start_year, end_year):
            raise ValueError(
                f"--year {requested_year} is outside {target['fold']}'s window "
                f"{target['raw_era5_window']}"
            )
        return requested_year
    if target.get("diary_window_status") == "RULED_PINNED" and target.get("diary_window"):
        pinned_start = str(target["diary_window"]).split("/")[0]
        return int(pinned_start[:4])
    return None


def archives_for_year(target: dict[str, object], year: int) -> list[Path]:
    """The boundary-day archive plus this year's 12 months -- 13 archives, same as Lyon."""
    start_year, end_year = window_years(target)
    if year not in (start_year, end_year):
        raise ValueError(
            f"year {year} is outside {target['fold']}'s window {target['raw_era5_window']}"
        )
    raw_dir: Path = target["raw_dir"]
    city = str(target["city"]).lower()
    prior_year = year - 1
    if prior_year == start_year - 1:
        boundary = raw_dir / f"era5_{city}_{prior_year}-12-31.zip"
    elif prior_year in (start_year, end_year):
        boundary = raw_dir / f"era5_{city}_{prior_year}-12.zip"
    else:
        raise ValueError(f"no boundary archive defined for {target['fold']} year {year}")
    archives = [boundary]
    for month in range(1, 13):
        archives.append(raw_dir / f"era5_{city}_{year}-{month:02d}.zip")
    return archives


def archive_completeness_for_year(target: dict[str, object], year: int) -> tuple[int, int, list[Path]]:
    """Return (have, need, missing) for converting one specific calendar year."""
    archives = archives_for_year(target, year)
    missing = [path for path in archives if not (path.is_file() and path.stat().st_size)]
    have = len(archives) - len(missing)
    return have, len(archives), missing


def required_archives(target: dict[str, object]) -> list[Path]:
    """The boundary day plus every month of both window years -- same layout as the acquirer."""
    start_year, end_year = window_years(target)
    seen: dict[Path, None] = {}
    for year in (start_year, end_year):
        for path in archives_for_year(target, year):
            seen[path] = None
    return list(seen)


def archive_completeness(target: dict[str, object]) -> tuple[int, int, list[Path]]:
    """Return (have, need, missing) counting only archives actually present on disk."""
    archives = required_archives(target)
    missing = [path for path in archives if not (path.is_file() and path.stat().st_size)]
    have = len(archives) - len(missing)
    return have, len(archives), missing


def _load_archive(path: Path) -> xr.Dataset:
    """Read the instantaneous and accumulated NetCDF streams inside one CDS archive."""
    with TemporaryDirectory(prefix="openubem_era5_") as temporary:
        directory = Path(temporary)
        with ZipFile(path) as archive:
            archive.extractall(directory)
        streams = []
        for netcdf in sorted(directory.glob("*.nc")):
            with xr.open_dataset(netcdf, engine="h5netcdf") as dataset:
                streams.append(dataset.load())
    if not streams:
        raise ValueError(f"CDS archive has no NetCDF stream: {path}")
    return xr.merge(streams, compat="no_conflicts")


def load_era5_hourly(
    archives: list[Path], utc_start: pd.Timestamp, utc_end: pd.Timestamp
) -> tuple[pd.DataFrame, float, float]:
    """Load exactly the given on-disk archives and return the hourly slice for one year."""
    present = [path for path in archives if path.is_file() and path.stat().st_size]
    merged = xr.concat([_load_archive(path) for path in present], dim="valid_time")
    merged = merged.sortby("valid_time")
    if merged.sizes.get("latitude") != 1 or merged.sizes.get("longitude") != 1:
        raise ValueError("ERA5 request must resolve to exactly one grid point")
    latitude = float(merged.latitude.values.item())
    longitude = float(merged.longitude.values.item())
    frame = merged.squeeze(("latitude", "longitude"), drop=True).to_dataframe()
    frame.index = pd.DatetimeIndex(frame.index, name="utc")
    frame = frame.loc[~frame.index.duplicated(keep="first")].sort_index()
    frame = frame.loc[utc_start:utc_end]
    expected = pd.date_range(utc_start, utc_end, freq="h")
    if not frame.index.equals(expected):
        raise ValueError("raw ERA5 hours do not form the required 8,760-hour UTC boundary slice")
    missing = REQUIRED_VARIABLES - set(frame.columns)
    if missing:
        raise ValueError(f"raw ERA5 payload omits required variables: {sorted(missing)}")
    return frame, latitude, longitude


def _relative_humidity_pct(dry_bulb_c: np.ndarray, dew_point_c: np.ndarray) -> np.ndarray:
    """Magnus relative humidity calculation from the downloaded temperature pair."""
    exponent = (17.625 * dew_point_c / (243.04 + dew_point_c)) - (
        17.625 * dry_bulb_c / (243.04 + dry_bulb_c)
    )
    return np.clip(100.0 * np.exp(exponent), 0.0, 100.0)


def epw_rows(
    frame: pd.DataFrame, latitude: float, longitude: float, elevation_m: float, utc_offset_hours: int
) -> list[list[object]]:
    """Build EPW fields at a fixed local-standard-time offset; DISC makes the solar fields close."""
    local = frame.copy()
    local.index = local.index + pd.Timedelta(hours=utc_offset_hours)  # fixed offset, no DST.
    dry_bulb_c = local["t2m"].to_numpy(dtype=float) - 273.15
    dew_point_c = np.minimum(local["d2m"].to_numpy(dtype=float) - 273.15, dry_bulb_c)
    pressure_pa = local["sp"].to_numpy(dtype=float)
    ghi = np.clip(local["ssrd"].to_numpy(dtype=float) / 3600.0, 0.0, 1367.0)
    local_time = local.index.tz_localize(timezone(timedelta(hours=utc_offset_hours)))
    solar_position = pvlib.solarposition.get_solarposition(
        local_time, latitude=latitude, longitude=longitude, altitude=elevation_m
    )
    zenith = solar_position["apparent_zenith"].to_numpy(dtype=float)
    cosine_zenith = np.maximum(np.cos(np.deg2rad(zenith)), 0.0)
    dni = pvlib.irradiance.disc(ghi, zenith, local_time, pressure=pressure_pa)["dni"].to_numpy(dtype=float)
    dni = np.nan_to_num(np.clip(dni, 0.0, 1200.0), nan=0.0)
    dhi = np.clip(ghi - dni * cosine_zenith, 0.0, 1367.0)
    wind_u = local["u10"].to_numpy(dtype=float)
    wind_v = local["v10"].to_numpy(dtype=float)
    wind_speed = np.hypot(wind_u, wind_v)
    wind_direction = np.mod(270.0 - np.degrees(np.arctan2(wind_v, wind_u)), 360.0)
    sky_cover = np.clip(np.rint(local["tcc"].to_numpy(dtype=float) * 10.0), 0, 10).astype(int)
    liquid_precip_mm = np.maximum(local["tp"].to_numpy(dtype=float) * 1000.0, 0.0)
    rh = _relative_humidity_pct(dry_bulb_c, dew_point_c)

    rows: list[list[object]] = []
    for index, stamp in enumerate(local.index):
        rows.append([
            stamp.year, stamp.month, stamp.day, stamp.hour + 1, 60, 0,
            round(dry_bulb_c[index], 1), round(dew_point_c[index], 1), round(rh[index]), round(pressure_pa[index]),
            0, 0, 0, round(ghi[index], 1), round(dni[index], 1), round(dhi[index], 1),
            0, 0, 0, 0, round(wind_direction[index]), round(wind_speed[index], 1),
            sky_cover[index], sky_cover[index], 0, 0, 0, 0, 0, 0, 0, 0, 0, round(liquid_precip_mm[index], 3), 1,
        ])
    return rows


def diary_window(target: dict[str, object], year: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """UTC boundary slice for the given explicit year, at this fold's fixed local offset."""
    offset = int(target["utc_offset_hours"])
    utc_start = pd.Timestamp(f"{year}-01-01T00:00:00") - pd.Timedelta(hours=offset)
    utc_end = pd.Timestamp(f"{year}-12-31T23:00:00") - pd.Timedelta(hours=offset)
    return utc_start, utc_end


def output_path_for_year(target: dict[str, object], year: int) -> Path:
    """Insert the emitted year before the extension of the registry's output_filename."""
    stem_path = Path(str(target["output_filename"]))
    return OUTPUT_ROOT / f"{stem_path.stem}_y{year}{stem_path.suffix}"


def write_epw(target: dict[str, object], year: int) -> Path:
    """Write and return the validated-format EPW for one complete (fold, year)."""
    archives = archives_for_year(target, year)
    utc_start, utc_end = diary_window(target, year)
    frame, latitude, longitude = load_era5_hourly(archives, utc_start, utc_end)
    elevation_m = float(target["elevation_m"])
    offset = int(target["utc_offset_hours"])
    rows = epw_rows(frame, latitude, longitude, elevation_m, offset)
    if len(rows) != 8760:
        raise AssertionError(f"expected 8760 EPW rows, found {len(rows)}")
    fold = str(target["fold"])
    city = str(target["city"])
    wmo = str(target.get("station") or "")
    first_weekday = pd.Timestamp(year, 1, 1).day_name()
    header = [
        f"LOCATION,{city},{city},{ISO3[fold]},ERA5,000000,{latitude:.2f},{longitude:.2f},"
        f"{offset:.1f},{elevation_m:.1f}",
        "DESIGN CONDITIONS,0",
        "TYPICAL/EXTREME PERIODS,0",
        "GROUND TEMPERATURES,0",
        "HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0",
        f"COMMENTS 1,Direct ERA5 reanalysis; {wmo} reference; not station observations or TMY",
        f"COMMENTS 2,UTC {year - 1}-12-31 23:00 to {year}-12-31 22:00; fixed UTC+{offset}, no DST",
        f"DATA PERIODS,1,1,Data,{first_weekday},1/1,12/31",
    ]
    output = output_path_for_year(target, year)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(header) + "\n")
        for row in rows:
            stream.write(",".join(str(value) for value in row) + "\n")
    return output


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def convert_fold_year(target: dict[str, object], year: int) -> Path | None:
    """Convert one (fold, year) if, and only if, its 13 required archives are on disk."""
    have, need, _missing = archive_completeness_for_year(target, year)
    if have < need:
        print(f"INCOMPLETE {target['fold']} {year} {have}/{need}")
        return None
    output = write_epw(target, year)
    print(f"EPW_SHA256 {target['fold']} {year} {sha256_of(output)}")
    return output


def convert_fold(target: dict[str, object], requested_year: int | None, all_years: bool) -> None:
    fold = str(target["fold"])
    if all_years:
        start_year, end_year = window_years(target)
        for year in (start_year, end_year):
            convert_fold_year(target, year)
        return
    year = resolve_year(target, requested_year)
    if year is None:
        print(f"YEAR_NOT_RULED {fold} {target['raw_era5_window']}")
        return
    convert_fold_year(target, year)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fold", action="append", choices=["es", "uk", "it"], help="repeatable")
    parser.add_argument("--all", action="store_true")
    year_group = parser.add_mutually_exclusive_group()
    year_group.add_argument("--year", type=int)
    year_group.add_argument("--all-years", action="store_true")
    args = parser.parse_args()
    if not args.all and not args.fold:
        parser.error("pass --all or at least one --fold")

    targets = load_fold_targets()
    folds = list(targets) if args.all else list(dict.fromkeys(args.fold or []))
    for fold in folds:
        convert_fold(targets[fold], args.year, args.all_years)
    return 0


if __name__ == "__main__":
    sys.exit(main())
