"""T04 - solar position (PLAN §7 T04). No pvlib (plan §6) - NOAA/Michalsky algorithm,
transcribed from NOAA GML's own published spreadsheet formulas (gml.noaa.gov/grad/solcalc/
calcdetails.html: "based on equations from Astronomical Algorithms, by Jean Meeus"),
cross-checked against a live Excel recalculation of that spreadsheet -- see
tests/fixtures/README_solar_position.md for provenance.

Convention (binding, stated once): dt_index must be UTC (naive datetimes interpreted as
UTC), NOT local standard time. Solar geometry only needs UTC + longitude -- the discrete
"timezone" in the NOAA spreadsheet exists purely to convert a civil clock to true solar
time and cancels out entirely when the input is already UTC. Callers holding EPW local-
standard-time timestamps (epw_hourly.py) must subtract the station's UTC offset (EPW
LOCATION field 9) before calling this function.
Azimuth convention: degrees clockwise from true north, 0-360.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _julian_day(dt_index: pd.DatetimeIndex) -> np.ndarray:
    # Excel-serial-date equivalent (days since 1899-12-30) + 2415018.5 = Julian Date at UT.
    excel_epoch = pd.Timestamp("1899-12-30")
    delta = dt_index - excel_epoch
    serial = delta.total_seconds().to_numpy() / 86400.0
    return serial + 2415018.5


def solar_position(dt_index: pd.DatetimeIndex, lat: float, lon: float) -> tuple[np.ndarray, np.ndarray]:
    """Vectorised solar altitude & azimuth (deg) for a UTC DatetimeIndex at (lat, lon).

    Returns (altitude_deg, azimuth_deg). altitude <= 0 means night (§4.6 - downstream code
    treats that as zero shortwave). Includes the NOAA atmospheric-refraction correction.
    """
    jd = _julian_day(dt_index)
    t = (jd - 2451545.0) / 36525.0

    l0 = np.mod(280.46646 + t * (36000.76983 + t * 0.0003032), 360.0)
    m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    ecc = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)

    m_r = np.radians(m)
    c = (
        np.sin(m_r) * (1.914602 - t * (0.004817 + 0.000014 * t))
        + np.sin(2 * m_r) * (0.019993 - 0.000101 * t)
        + np.sin(3 * m_r) * 0.000289
    )
    true_long = l0 + c
    true_anom = m + c
    rad_vector = (1.000001018 * (1 - ecc * ecc)) / (1 + ecc * np.cos(np.radians(true_anom)))  # noqa: F841 (kept for provenance parity with the spreadsheet chain)

    app_long = true_long - 0.00569 - 0.00478 * np.sin(np.radians(125.04 - 1934.136 * t))

    mean_obliq = 23.0 + (26.0 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60.0) / 60.0
    obliq_corr = mean_obliq + 0.00256 * np.cos(np.radians(125.04 - 1934.136 * t))

    decl = np.degrees(np.arcsin(np.sin(np.radians(obliq_corr)) * np.sin(np.radians(app_long))))

    y = np.tan(np.radians(obliq_corr / 2.0)) ** 2
    eq_of_time = 4.0 * np.degrees(
        y * np.sin(2 * np.radians(l0))
        - 2 * ecc * np.sin(m_r)
        + 4 * ecc * y * np.sin(m_r) * np.cos(2 * np.radians(l0))
        - 0.5 * y * y * np.sin(4 * np.radians(l0))
        - 1.25 * ecc * ecc * np.sin(2 * m_r)
    )

    time_frac = (
        dt_index.hour.to_numpy() * 60.0
        + dt_index.minute.to_numpy()
        + dt_index.second.to_numpy() / 60.0
    ) / 1440.0
    true_solar_time = np.mod(time_frac * 1440.0 + eq_of_time + 4.0 * lon, 1440.0)
    hour_angle = np.where(true_solar_time / 4.0 < 0.0, true_solar_time / 4.0 + 180.0, true_solar_time / 4.0 - 180.0)

    lat_r = np.radians(lat)
    decl_r = np.radians(decl)
    ha_r = np.radians(hour_angle)

    zenith = np.degrees(np.arccos(
        np.clip(np.sin(lat_r) * np.sin(decl_r) + np.cos(lat_r) * np.cos(decl_r) * np.cos(ha_r), -1.0, 1.0)
    ))
    altitude_uncorrected = 90.0 - zenith
    altitude = altitude_uncorrected + _atm_refraction_deg(altitude_uncorrected)

    denom = np.cos(lat_r) * np.sin(np.radians(zenith))
    with np.errstate(divide="ignore", invalid="ignore"):
        arg = np.clip((np.sin(lat_r) * np.cos(np.radians(zenith)) - np.sin(decl_r)) / denom, -1.0, 1.0)
    az_base = np.degrees(np.arccos(arg))
    azimuth = np.where(
        hour_angle > 0.0,
        np.mod(az_base + 180.0, 360.0),
        np.mod(540.0 - az_base, 360.0),
    )
    # Polar case: denom -> 0 at lat=+-90; azimuth is undefined there, pin to 180 (harmless, altitude<0 gates it out).
    azimuth = np.where(np.isfinite(azimuth), azimuth, 180.0)

    return altitude, azimuth


def _atm_refraction_deg(altitude_deg):
    """NOAA piecewise atmospheric-refraction correction (arcseconds -> degrees)."""
    alt = np.asarray(altitude_deg, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        tan_alt = np.tan(np.radians(alt))
        high = (58.1 / tan_alt - 0.07 / tan_alt ** 3 + 0.000086 / tan_alt ** 5) / 3600.0
        low = (1735.0 + alt * (-518.2 + alt * (103.4 + alt * (-12.79 + alt * 0.711)))) / 3600.0
        very_low = (-20.774 / tan_alt) / 3600.0
    refr = np.select(
        [alt > 85.0, alt > 5.0, alt > -0.575],
        [np.zeros_like(alt), high, low],
        default=very_low,
    )
    return refr
