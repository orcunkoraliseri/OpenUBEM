from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from openubem.gpusim.physics.psychro import (
    KELVIN_CONV,
    STEFAN_BOLTZMANN,
    psy_w_fn_tdb_rh_pb,
)
from openubem.gpusim.physics.solar import (
    calc_perez_sky_factors,
    calc_solar_direction_cosines,
    interpolate_epw_solar_to_timestep,
)

STD_PRESSURE_SEA_LEVEL = 101325.0


@dataclass(frozen=True)
class WeatherSeries:
    """Per-timestep weather arrays for one site run period and warm-up day."""

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
    latitude: float = 0.0
    longitude: float = 0.0
    time_zone: float = 0.0
    dni: np.ndarray | None = None
    dhi: np.ndarray | None = None
    wind_speed: np.ndarray | None = None
    wind_dir: np.ndarray | None = None
    wet_bulb: np.ndarray | None = None
    is_rain: np.ndarray | None = None
    solcos_x: np.ndarray | None = None
    solcos_y: np.ndarray | None = None
    solcos_z: np.ndarray | None = None
    perez_f1: np.ndarray | None = None
    perez_f2: np.ndarray | None = None
    warmup_dni: np.ndarray | None = None
    warmup_dhi: np.ndarray | None = None
    warmup_wind_speed: np.ndarray | None = None
    warmup_wind_dir: np.ndarray | None = None
    warmup_wet_bulb: np.ndarray | None = None
    warmup_is_rain: np.ndarray | None = None
    warmup_solcos_x: np.ndarray | None = None
    warmup_solcos_y: np.ndarray | None = None
    warmup_solcos_z: np.ndarray | None = None
    warmup_perez_f1: np.ndarray | None = None
    warmup_perez_f2: np.ndarray | None = None


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


def _read_epw_hourly(
    epw_path: Path,
) -> tuple[dict[str, float], dict[str, np.ndarray]]:
    """Read 8,760 hourly EPW records with EnergyPlus missing-value substitution."""
    lines = epw_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) < 9:
        raise ValueError(f"{epw_path}: fewer than 9 lines")

    loc_cols = [part.strip() for part in lines[0].split(",")]
    if len(loc_cols) < 10 or loc_cols[0].upper() != "LOCATION":
        raise ValueError(f"{epw_path}: invalid LOCATION header")
    latitude = float(loc_cols[6])
    longitude = float(loc_cols[7])
    time_zone = float(loc_cols[8])
    elevation = float(loc_cols[9])
    std_baro = STD_PRESSURE_SEA_LEVEL * (1.0 - 2.25577e-05 * elevation) ** 5.2559

    miss_db = 6.0
    miss_dp = 3.0
    miss_rh = 50.0
    miss_pb = std_baro
    miss_osc = 5.0
    miss_ws = 0.0
    miss_wd = 0.0

    dry_bulb_list: list[float] = []
    dew_point_list: list[float] = []
    rel_hum_list: list[float] = []
    baro_press_list: list[float] = []
    ir_horiz_list: list[float] = []
    dni_list: list[float] = []
    dhi_list: list[float] = []
    ws_list: list[float] = []
    wd_list: list[float] = []
    osc_list: list[float] = []
    rain_list: list[float] = []

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
        dni = float(cols[14])
        dhi = float(cols[15])
        wd = float(cols[20])
        ws = float(cols[21])
        osc = float(cols[23])

        # EnergyPlus WeatherManager.cc rain flag from WMO present weather codes or liquid precip
        rain_flag = 0.0
        pwo = cols[26].strip() if len(cols) > 26 else "9"
        pwc = cols[27].strip() if len(cols) > 27 else "999999999"
        if pwo == "0" and len(pwc) >= 9:
            if pwc[1] in "012345678" or pwc[2] in "012345678":
                rain_flag = 1.0
        if len(cols) > 33:
            try:
                liq = float(cols[33])
                if 0.6 <= liq < 999.0:
                    rain_flag = 1.0
            except ValueError:
                pass

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
        if dni >= 9999.0 or dni < 0.0:
            dni = 0.0
        if dhi >= 9999.0 or dhi < 0.0:
            dhi = 0.0
        if ws >= 999.0 or ws < 0.0:
            ws = miss_ws
        if wd >= 999.0 or wd < 0.0:
            wd = miss_wd

        miss_db = db
        miss_dp = dp
        miss_rh = float(round(rh))
        miss_pb = pb
        miss_osc = osc
        miss_ws = ws
        miss_wd = wd

        dry_bulb_list.append(db)
        dew_point_list.append(dp)
        rel_hum_list.append(rh)
        baro_press_list.append(pb)
        ir_horiz_list.append(ir)
        dni_list.append(dni)
        dhi_list.append(dhi)
        ws_list.append(ws)
        wd_list.append(wd)
        osc_list.append(osc)
        rain_list.append(rain_flag)

    if len(dry_bulb_list) != 8760:
        raise ValueError(
            f"{epw_path}: expected 8760 hourly rows, got {len(dry_bulb_list)}"
        )

    loc = {
        "latitude": latitude,
        "longitude": longitude,
        "time_zone": time_zone,
        "elevation": elevation,
    }
    return loc, {
        "dry_bulb": np.asarray(dry_bulb_list, dtype=np.float64),
        "dew_point": np.asarray(dew_point_list, dtype=np.float64),
        "rel_hum_pct": np.asarray(rel_hum_list, dtype=np.float64),
        "baro_press": np.asarray(baro_press_list, dtype=np.float64),
        "ir_horiz": np.asarray(ir_horiz_list, dtype=np.float64),
        "dni": np.asarray(dni_list, dtype=np.float64),
        "dhi": np.asarray(dhi_list, dtype=np.float64),
        "wind_speed": np.asarray(ws_list, dtype=np.float64),
        "wind_dir": np.asarray(wd_list, dtype=np.float64),
        "opaque_sky": np.asarray(osc_list, dtype=np.float64),
        "is_rain": np.asarray(rain_list, dtype=np.float64),
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
    """Load an EPW file and interpolate to EnergyPlus zone-timestep arrays."""
    loc, hourly = _read_epw_hourly(epw_path)
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
    wind_speed = _interpolate_hourly_to_timestep(hourly["wind_speed"], wt_now)
    wind_dir = _interpolate_hourly_to_timestep(hourly["wind_dir"], wt_now)

    dni = interpolate_epw_solar_to_timestep(hourly["dni"], steps_per_hour=steps_per_hour)
    dhi = interpolate_epw_solar_to_timestep(hourly["dhi"], steps_per_hour=steps_per_hour)
    solcos_x, solcos_y, solcos_z, i_ext = calc_solar_direction_cosines(
        loc["latitude"],
        loc["longitude"],
        loc["time_zone"],
        steps_per_hour=steps_per_hour,
        n_days=365,
    )
    perez_f1, perez_f2 = calc_perez_sky_factors(dni, dhi, solcos_z, i_ext)

    horiz_ir, sky_temp = calc_horiz_ir_and_sky_temp(
        opaque_sky, dry_bulb, dew_point, horiz_ir_interp, np
    )
    rel_hum = rel_hum_pct / 100.0
    hum_rat = psy_w_fn_tdb_rh_pb(dry_bulb, rel_hum, baro_press, np)
    # Stull (2011) wet-bulb temperature approximation (within ~0.15 K)
    rh_c = np.clip(rel_hum_pct, 1.0, 100.0)
    wet_bulb = (
        dry_bulb * np.arctan(0.151977 * np.sqrt(rh_c + 8.313659))
        + np.arctan(dry_bulb + rh_c)
        - np.arctan(rh_c - 1.676331)
        + 0.00391838 * np.power(rh_c, 1.5) * np.arctan(0.023101 * rh_c)
        - 4.686035
    )
    wet_bulb = np.minimum(wet_bulb, dry_bulb)
    is_rain = np.repeat(hourly["is_rain"], steps_per_hour)

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
        elevation=loc["elevation"],
        steps_per_hour=steps_per_hour,
        latitude=loc["latitude"],
        longitude=loc["longitude"],
        time_zone=loc["time_zone"],
        dni=dni,
        dhi=dhi,
        wind_speed=wind_speed,
        wind_dir=wind_dir,
        wet_bulb=wet_bulb,
        is_rain=is_rain,
        solcos_x=solcos_x,
        solcos_y=solcos_y,
        solcos_z=solcos_z,
        perez_f1=perez_f1,
        perez_f2=perez_f2,
        warmup_dni=dni[:day_steps].copy(),
        warmup_dhi=dhi[:day_steps].copy(),
        warmup_wind_speed=wind_speed[:day_steps].copy(),
        warmup_wind_dir=wind_dir[:day_steps].copy(),
        warmup_wet_bulb=wet_bulb[:day_steps].copy(),
        warmup_is_rain=is_rain[:day_steps].copy(),
        warmup_solcos_x=solcos_x[:day_steps].copy(),
        warmup_solcos_y=solcos_y[:day_steps].copy(),
        warmup_solcos_z=solcos_z[:day_steps].copy(),
        warmup_perez_f1=perez_f1[:day_steps].copy(),
        warmup_perez_f2=perez_f2[:day_steps].copy(),
    )
