from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from openubem.gpusim.physics.psychro import (
    KELVIN_CONV,
    STEFAN_BOLTZMANN,
    psy_w_fn_tdb_rh_pb,
)

STD_PRESSURE_SEA_LEVEL = 101325.0


@dataclass(frozen=True)
class WeatherSeries:
    """Per-timestep weather arrays for one site run period and warm-up day.

    Attributes:
        dry_bulb: Outdoor dry-bulb temperature in degrees C, shape (N,).
        dew_point: Outdoor dew-point temperature in degrees C, shape (N,).
        rel_hum: Outdoor relative humidity fraction in [0, 1], shape (N,).
        baro_press: Outdoor barometric pressure in Pa, shape (N,).
        hum_rat: Outdoor humidity ratio in kgWater/kgDryAir, shape (N,).
        horiz_ir: Horizontal infrared radiation rate in W/m2, shape (N,).
        sky_temp: Sky temperature in degrees C, shape (N,).
        warmup_dry_bulb: Day-1 warm-up dry-bulb temperature in C, shape (D,).
        warmup_dew_point: Day-1 warm-up dew-point temperature in C, shape (D,).
        warmup_rel_hum: Day-1 warm-up relative humidity fraction, shape (D,).
        warmup_baro_press: Day-1 warm-up barometric pressure in Pa, shape (D,).
        warmup_hum_rat: Day-1 warm-up humidity ratio, shape (D,).
        warmup_horiz_ir: Day-1 warm-up horizontal IR in W/m2, shape (D,).
        warmup_sky_temp: Day-1 warm-up sky temperature in C, shape (D,).
        elevation: Site elevation in meters from the EPW LOCATION header.
        steps_per_hour: Number of zone timesteps per hour.
    """

    dry_bulb: np.ndarray
    dew_point: np.ndarray
    rel_hum: np.ndarray
    baro_press: np.ndarray
    hum_rat: np.ndarray
    horiz_ir: np.ndarray
    sky_temp: np.ndarray
    warmup_dry_bulb: np.ndarray
    warmup_dew_point: np.ndarray
    warmup_rel_hum: np.ndarray
    warmup_baro_press: np.ndarray
    warmup_hum_rat: np.ndarray
    warmup_horiz_ir: np.ndarray
    warmup_sky_temp: np.ndarray
    elevation: float
    steps_per_hour: int


def calc_sky_emissivity_clark_allen(
    opaque_sky_cover: Any, dry_bulb: Any, dew_point: Any, xp: Any
) -> Any:
    """WeatherManager.cc::CalcSkyEmissivity"""
    t_dew_k = xp.minimum(dry_bulb, dew_point) + KELVIN_CONV
    e_clear = 0.787 + 0.764 * xp.log(t_dew_k / KELVIN_CONV)
    n_cov = opaque_sky_cover
    return e_clear * (
        1.0 + 0.0224 * n_cov - 0.0035 * (n_cov * n_cov) + 0.00028 * (n_cov**3)
    )


def calc_horiz_ir_and_sky_temp(
    opaque_sky_cover: Any,
    dry_bulb: Any,
    dew_point: Any,
    ir_horiz: Any,
    xp: Any,
) -> tuple[Any, Any]:
    """WeatherManager.cc::calcSky"""
    ir_clean = xp.where(ir_horiz <= 0.0, 9999.0, ir_horiz)
    missing_mask = ir_clean >= 9999.0
    esky = calc_sky_emissivity_clark_allen(opaque_sky_cover, dry_bulb, dew_point, xp)
    t_dry_k = dry_bulb + KELVIN_CONV
    ir_model = esky * STEFAN_BOLTZMANN * (t_dry_k**4)
    horiz_ir = xp.where(missing_mask, ir_model, ir_clean)
    sky_temp_model = t_dry_k * (esky**0.25) - KELVIN_CONV
    sky_temp_obs = (xp.maximum(horiz_ir, 1.0e-12) / STEFAN_BOLTZMANN) ** 0.25 - (
        KELVIN_CONV
    )
    sky_temp = xp.where(missing_mask, sky_temp_model, sky_temp_obs)
    return horiz_ir, sky_temp


def setup_interpolation_weights(steps_per_hour: int, xp: Any) -> Any:
    """WeatherManager.cc::SetupInterpolationValues"""
    if steps_per_hour == 1:
        return xp.ones(1, dtype=xp.float64)
    idx = xp.arange(1, steps_per_hour + 1, dtype=xp.float64)
    return xp.minimum(1.0, idx / float(steps_per_hour))


def _read_epw_hourly(epw_path: Path) -> tuple[float, dict[str, np.ndarray]]:
    """Read 8,760 hourly EPW records with EnergyPlus missing-value substitution.

    Args:
        epw_path: Path to the EPW weather file.

    Returns:
        Tuple of ``(elevation_m, hourly_arrays_dict)``.

    Raises:
        ValueError: If the EPW header or row count is invalid.
    """
    lines = epw_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) < 9:
        raise ValueError(f"{epw_path}: fewer than 9 lines")

    loc_cols = [part.strip() for part in lines[0].split(",")]
    if len(loc_cols) < 10 or loc_cols[0].upper() != "LOCATION":
        raise ValueError(f"{epw_path}: invalid LOCATION header")
    elevation = float(loc_cols[9])
    std_baro = STD_PRESSURE_SEA_LEVEL * (1.0 - 2.25577e-05 * elevation) ** 5.2559

    miss_db = 6.0
    miss_dp = 3.0
    miss_rh = 50.0
    miss_pb = std_baro
    miss_osc = 5.0

    dry_bulb_list: list[float] = []
    dew_point_list: list[float] = []
    rel_hum_list: list[float] = []
    baro_press_list: list[float] = []
    ir_horiz_list: list[float] = []
    osc_list: list[float] = []

    for line in lines[8:]:
        stripped = line.strip()
        if not stripped:
            continue
        cols = stripped.split(",")
        month = int(cols[1])
        day = int(cols[2])
        if month == 2 and day == 29:
            continue

        db = float(cols[6])
        dp = float(cols[7])
        rh = float(cols[8])
        pb = float(cols[9])
        ir = float(cols[12])
        osc = float(cols[23])

        if db >= 99.9:
            db = miss_db
        if dp >= 99.9:
            dp = miss_dp
        if rh >= 999.0:
            rh = miss_rh
        if pb >= 999999.0 or pb <= 31000.0 or pb > 120000.0:
            pb = miss_pb
        if osc >= 99.0:
            osc = miss_osc
        if ir <= 0.0:
            ir = 9999.0

        miss_db = db
        miss_dp = dp
        miss_rh = float(round(rh))
        miss_pb = pb
        miss_osc = osc

        dry_bulb_list.append(db)
        dew_point_list.append(dp)
        rel_hum_list.append(rh)
        baro_press_list.append(pb)
        ir_horiz_list.append(ir)
        osc_list.append(osc)

    if len(dry_bulb_list) != 8760:
        raise ValueError(
            f"{epw_path}: expected 8760 hourly rows, got {len(dry_bulb_list)}"
        )

    return elevation, {
        "dry_bulb": np.asarray(dry_bulb_list, dtype=np.float64),
        "dew_point": np.asarray(dew_point_list, dtype=np.float64),
        "rel_hum_pct": np.asarray(rel_hum_list, dtype=np.float64),
        "baro_press": np.asarray(baro_press_list, dtype=np.float64),
        "ir_horiz": np.asarray(ir_horiz_list, dtype=np.float64),
        "opaque_sky": np.asarray(osc_list, dtype=np.float64),
    }


def _interpolate_hourly_to_timestep(
    hourly: np.ndarray, wt_now: np.ndarray
) -> np.ndarray:
    """WeatherManager.cc::ReadEPlusWeatherForDay"""
    prev = np.empty_like(hourly)
    prev[0] = hourly[23]
    prev[1:] = hourly[:-1]
    wt_prev = 1.0 - wt_now
    interp = prev[:, None] * wt_prev[None, :] + hourly[:, None] * wt_now[None, :]
    return interp.reshape(-1)


def load_epw_weather(epw_path: Path, steps_per_hour: int = 12) -> WeatherSeries:
    """Load an EPW file and interpolate to EnergyPlus zone-timestep arrays.

    Args:
        epw_path: Path to the EPW weather file.
        steps_per_hour: Number of zone timesteps per hour (default 12).

    Returns:
        ``WeatherSeries`` containing 105,120 run-period steps and Day-1 warm-up steps.
    """
    elevation, hourly = _read_epw_hourly(epw_path)
    horiz_ir_hr, _ = calc_horiz_ir_and_sky_temp(
        hourly["opaque_sky"],
        hourly["dry_bulb"],
        hourly["dew_point"],
        hourly["ir_horiz"],
        np,
    )

    wt_now = setup_interpolation_weights(steps_per_hour, np)
    dry_bulb = _interpolate_hourly_to_timestep(hourly["dry_bulb"], wt_now)
    dew_point = _interpolate_hourly_to_timestep(hourly["dew_point"], wt_now)
    rel_hum_pct = _interpolate_hourly_to_timestep(hourly["rel_hum_pct"], wt_now)
    baro_press = _interpolate_hourly_to_timestep(hourly["baro_press"], wt_now)
    opaque_sky = _interpolate_hourly_to_timestep(hourly["opaque_sky"], wt_now)
    horiz_ir_interp = _interpolate_hourly_to_timestep(horiz_ir_hr, wt_now)

    horiz_ir, sky_temp = calc_horiz_ir_and_sky_temp(
        opaque_sky, dry_bulb, dew_point, horiz_ir_interp, np
    )
    rel_hum = rel_hum_pct / 100.0
    hum_rat = psy_w_fn_tdb_rh_pb(dry_bulb, rel_hum, baro_press, np)

    day_steps = 24 * steps_per_hour
    return WeatherSeries(
        dry_bulb=dry_bulb,
        dew_point=dew_point,
        rel_hum=rel_hum,
        baro_press=baro_press,
        hum_rat=hum_rat,
        horiz_ir=horiz_ir,
        sky_temp=sky_temp,
        warmup_dry_bulb=dry_bulb[:day_steps].copy(),
        warmup_dew_point=dew_point[:day_steps].copy(),
        warmup_rel_hum=rel_hum[:day_steps].copy(),
        warmup_baro_press=baro_press[:day_steps].copy(),
        warmup_hum_rat=hum_rat[:day_steps].copy(),
        warmup_horiz_ir=horiz_ir[:day_steps].copy(),
        warmup_sky_temp=sky_temp[:day_steps].copy(),
        elevation=elevation,
        steps_per_hour=steps_per_hour,
    )
