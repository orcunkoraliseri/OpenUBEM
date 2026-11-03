"""Convert the acquired direct ERA5 Lyon--Bron 2023 files into an EPW.

The output is a 2023 local-standard-time (CET, UTC+1) weather year.  ERA5 is
gridded reanalysis; the EPW LOCATION line uses the returned ERA5 grid point,
while the comment records Lyon--Bron WMO 07480 as the location reference.
"""
from __future__ import annotations

import argparse
from datetime import timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pvlib
import xarray as xr


RAW_DIR = Path("openubem/data/weather/raw/era5_lyon_bron_2023")
OUTPUT = Path("openubem/data/weather/fr_lyon_bron_2023_era5.epw")
UTC_START = pd.Timestamp("2022-12-31T23:00:00")
UTC_END = pd.Timestamp("2023-12-31T22:00:00")
ELEVATION_M = 198.0  # Lyon--Bron station elevation; ERA5 itself is a grid-point product.


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


def load_era5_hourly(raw_dir: Path = RAW_DIR) -> tuple[pd.DataFrame, float, float]:
    """Load all acquired CDS ZIP payloads and return one nearest-grid-point hourly table."""
    archives = sorted(raw_dir.glob("era5_lyon_bron_*.zip"))
    if len(archives) != 13:
        raise ValueError(f"expected 13 CDS archives (boundary day + 12 months), found {len(archives)}")
    merged = xr.concat([_load_archive(path) for path in archives], dim="valid_time")
    merged = merged.sortby("valid_time")
    if merged.sizes.get("latitude") != 1 or merged.sizes.get("longitude") != 1:
        raise ValueError("ERA5 request must resolve to exactly one grid point")
    latitude = float(merged.latitude.values.item())
    longitude = float(merged.longitude.values.item())
    frame = merged.squeeze(("latitude", "longitude"), drop=True).to_dataframe()
    frame.index = pd.DatetimeIndex(frame.index, name="utc")
    frame = frame.loc[~frame.index.duplicated(keep="first")].sort_index()
    frame = frame.loc[UTC_START:UTC_END]
    expected = pd.date_range(UTC_START, UTC_END, freq="h")
    if not frame.index.equals(expected):
        raise ValueError("raw ERA5 hours do not form the required 8,760-hour UTC boundary slice")
    required = {"t2m", "d2m", "sp", "u10", "v10", "ssrd", "fdir", "tcc", "tp"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"raw ERA5 payload omits required variables: {sorted(missing)}")
    return frame, latitude, longitude


def _relative_humidity_pct(dry_bulb_c: np.ndarray, dew_point_c: np.ndarray) -> np.ndarray:
    """Magnus relative humidity calculation from the downloaded temperature pair."""
    exponent = (17.625 * dew_point_c / (243.04 + dew_point_c)) - (
        17.625 * dry_bulb_c / (243.04 + dry_bulb_c)
    )
    return np.clip(100.0 * np.exp(exponent), 0.0, 100.0)


def _epw_rows(frame: pd.DataFrame, latitude: float, longitude: float) -> list[list[object]]:
    """Build EPW fields; DISC makes the three solar fields close by construction."""
    local = frame.copy()
    local.index = local.index + pd.Timedelta(hours=1)  # fixed CET, deliberately no DST.
    dry_bulb_c = local["t2m"].to_numpy(dtype=float) - 273.15
    dew_point_c = np.minimum(local["d2m"].to_numpy(dtype=float) - 273.15, dry_bulb_c)
    pressure_pa = local["sp"].to_numpy(dtype=float)
    ghi = np.clip(local["ssrd"].to_numpy(dtype=float) / 3600.0, 0.0, 1367.0)
    local_time = local.index.tz_localize(timezone(timedelta(hours=1)))
    solar_position = pvlib.solarposition.get_solarposition(
        local_time, latitude=latitude, longitude=longitude, altitude=ELEVATION_M
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


def write_epw(output: Path = OUTPUT, raw_dir: Path = RAW_DIR) -> Path:
    """Write and return the validated-format EPW; DR08 validation remains a separate step."""
    frame, latitude, longitude = load_era5_hourly(raw_dir)
    rows = _epw_rows(frame, latitude, longitude)
    if len(rows) != 8760:
        raise AssertionError(f"expected 8760 EPW rows, found {len(rows)}")
    header = [
        f"LOCATION,Lyon-Bron,Auvergne-Rhone-Alpes,FRA,ERA5,074800,{latitude:.2f},{longitude:.2f},1.0,{ELEVATION_M:.1f}",
        "DESIGN CONDITIONS,0",
        "TYPICAL/EXTREME PERIODS,0",
        "GROUND TEMPERATURES,0",
        "HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0",
        "COMMENTS 1,Direct ERA5 reanalysis; Lyon-Bron WMO 07480 reference; not station observations or TMY",
        "COMMENTS 2,UTC 2022-12-31 23:00 to 2023-12-31 22:00; fixed CET (UTC+1), no DST",
        "DATA PERIODS,1,1,Data,Sunday,1/1,12/31",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(header) + "\n")
        for row in rows:
            stream.write(",".join(str(value) for value in row) + "\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(write_epw(output=args.output, raw_dir=args.raw_dir))


if __name__ == "__main__":
    main()
