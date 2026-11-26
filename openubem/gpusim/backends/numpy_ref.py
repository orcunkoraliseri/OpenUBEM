from dataclasses import dataclass
from typing import Any

import numpy as np

from openubem.gpusim._rust_compat import (
    dispatch_gpusim_rust,
    load_gpusim_rust_module,
)

from openubem.gpusim.compile import (
    BOUND_DOOR,
    BOUND_INTMASS,
    BOUND_OSC,
    BOUND_OUTDOORS,
    BOUND_WINDOW,
    SURF_FLOOR,
    BatchSpec,
)
from openubem.gpusim.ctf import CtfCoefficients, load_ctf_from_eio
from openubem.gpusim.physics.convection import (
    calc_inside_convection_opaque,
    calc_iso15099_window_int_conv_coeff,
    calc_outside_convection_doe2,
    calc_outside_rad_coeffs,
    out_dry_bulb_temp_at,
)
from openubem.gpusim.physics.lwr import calc_interior_rad_exchange
from openubem.gpusim.physics.psychro import KELVIN_CONV, STEFAN_BOLTZMANN
from openubem.gpusim.physics.solar import (
    calc_surface_incident_solar,
    distribute_full_exterior_interior_solar,
    simple_glazing_angular_factors,
)
from openubem.gpusim.physics.surface_hb import (
    ITER_DAMP_CONST,
    ITERS_REEVAL_CONV_COEFF,
    MAX_ALLOWED_DEL_TEMP,
    MAX_INSIDE_SURF_ITERS,
    calc_ctf_const_parts,
    calc_inside_surface_step,
    calc_osc_outside_temp,
    calc_outdoors_outside_temp,
    update_ctf_histories,
)
from openubem.gpusim.physics.window import (
    simple_glazing_layer_conductance,
    solve_simple_window,
    starting_window_temps,
)
from openubem.gpusim.physics.zone_air import (
    calc_ideal_loads_heating,
    calc_ventilation_mcp,
    correct_zone_air_temp_and_humrat,
    down_interpolate_4_history_values,
    predict_zone_load,
)
from openubem.gpusim.schedules import expand_hourly_to_timestep
from openubem.gpusim.viewfactors import compute_batch_view_factors
from openubem.gpusim.weather import WeatherSeries

SURF_INITIAL_TEMP: float = 23.0
ZONE_INITIAL_TEMP: float = 23.0
MAX_ZONE_TEMP_DIFF: float = 0.3
MIN_TIME_STEP_SYS_HR: float = 1.0 / 60.0
WARMUP_MIN_LOAD: float = 100.0


@dataclass(frozen=True)
class SimulationResult:
    """Outputs of a Stage A batched annual simulation.

    Attributes:
        cell_ids: Cell identifiers in batch order.
        hourly_heating_j: Ideal-loads zone total heating energy ``[B, 8760]`` in J.
        annual_heating_kwh: Float64 annual heating energy ``[B]`` in kWh.
        warmup_days: Number of warm-up days taken per building ``[B]``.
        zone_air_temp_c: Optional timestep zone air temperature ``[B, T]`` in C.
        zone_mean_air_temp_c: Optional timestep zone mean air temp ``[B, T]`` in C.
    """

    cell_ids: list[str]
    hourly_heating_j: np.ndarray
    annual_heating_kwh: np.ndarray
    warmup_days: np.ndarray
    zone_air_temp_c: np.ndarray | None
    zone_mean_air_temp_c: np.ndarray | None


def _stack_weather(
    weather: WeatherSeries | list[WeatherSeries],
    batch_size: int,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """Pack single or per-building WeatherSeries into ``[B, T]`` arrays.

    Args:
        weather: Shared ``WeatherSeries`` or list of length ``B``.
        batch_size: Number of buildings in batch.

    Returns:
        Tuple of run-period ``(t_db, w_out, pb, t_sky)`` and warmup-day-1
        ``(wu_t_db, wu_w_out, wu_pb, wu_t_sky)`` arrays, each ``[B, T]``.
    """
    if isinstance(weather, WeatherSeries):
        w_list = [weather] * batch_size
    else:
        if len(weather) != batch_size:
            raise ValueError(
                f"Expected {batch_size} WeatherSeries, got {len(weather)}"
            )
        w_list = weather

    t_db = np.stack([w.dry_bulb for w in w_list], axis=0)
    w_out = np.stack([w.hum_rat for w in w_list], axis=0)
    pb = np.stack([w.baro_press for w in w_list], axis=0)
    t_sky = np.stack([w.sky_temp for w in w_list], axis=0)
    wu_t_db = np.stack([w.warmup_dry_bulb for w in w_list], axis=0)
    wu_w_out = np.stack([w.warmup_hum_rat for w in w_list], axis=0)
    wu_pb = np.stack([w.warmup_baro_press for w in w_list], axis=0)
    wu_t_sky = np.stack([w.warmup_sky_temp for w in w_list], axis=0)
    return t_db, w_out, pb, t_sky, wu_t_db, wu_w_out, wu_pb, wu_t_sky


def _precompute_batch_solar(
    batch: BatchSpec,
    weather: WeatherSeries | list[WeatherSeries],
    is_outdoors_op: np.ndarray,
    is_window: np.ndarray,
    is_non_window: np.ndarray,
    sunlit_frac: np.ndarray | None = None,
    wu_sunlit_frac: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Precompute per-building, per-timestep solar fluxes for S1/S3 Stage A.

    Returns ``(q_out, q_in, q_win, wu_q_out, wu_q_in, wu_q_win)`` with shapes
    ``[B, T, S]`` and ``[B, D, S]``.
    """
    b_size = batch.batch_size
    n_surf = batch.max_surfaces
    w_list = [weather] * b_size if isinstance(weather, WeatherSeries) else weather
    n_run = len(w_list[0].dry_bulb)
    n_wu = len(w_list[0].warmup_dry_bulb)

    q_out = np.zeros((b_size, n_run, n_surf), dtype=np.float64)
    q_in = np.zeros((b_size, n_run, n_surf), dtype=np.float64)
    q_win = np.zeros((b_size, n_run, n_surf), dtype=np.float64)
    wu_q_out = np.zeros((b_size, n_wu, n_surf), dtype=np.float64)
    wu_q_in = np.zeros((b_size, n_wu, n_surf), dtype=np.float64)
    wu_q_win = np.zeros((b_size, n_wu, n_surf), dtype=np.float64)

    sun_exp = (
        batch.surf_sun_exposed
        if batch.surf_sun_exposed is not None
        else np.zeros((b_size, n_surf), dtype=bool)
    )
    alpha_out = (
        batch.surf_solar_abs_out
        if batch.surf_solar_abs_out is not None
        else np.full((b_size, n_surf), 0.7, dtype=np.float64)
    )
    alpha_in = (
        batch.surf_solar_abs_in
        if batch.surf_solar_abs_in is not None
        else np.full((b_size, n_surf), 0.7, dtype=np.float64)
    )
    is_floor = (batch.surf_class == SURF_FLOOR) & batch.surf_mask

    for b in range(b_size):
        if not bool(np.any(sun_exp[b] & batch.surf_mask[b])):
            continue
        w = w_list[b]
        if w.dni is None or w.dhi is None or w.solcos_x is None:
            raise ValueError("WeatherSeries missing solar arrays required for S1")

        def _compute_period(
            dni: np.ndarray,
            dhi: np.ndarray,
            sx: np.ndarray,
            sy: np.ndarray,
            sz: np.ndarray,
            f1: np.ndarray,
            f2: np.ndarray,
            sf: np.ndarray | None,
        ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
            i_beam, i_dsky, i_dgnd, cos_inc = calc_surface_incident_solar(
                dni,
                dhi,
                sx,
                sy,
                sz,
                f1,
                f2,
                batch.surf_tilt_deg[b],
                batch.surf_azimuth_deg[b],
                batch.surf_vf_ground[b],
                sun_exp[b] & batch.surf_mask[b],
                sunlit_frac=sf,
            )
            i_tot = i_beam + i_dsky + i_dgnd
            i_diff = i_dsky + i_dgnd
            op_mask = (is_outdoors_op[b] & sun_exp[b])[None, :]
            qo = np.where(op_mask, i_tot * alpha_out[b][None, :], 0.0)

            win_m = (is_window[b] & sun_exp[b])[None, :]
            if bool(np.any(win_m)):
                tau_b, abs_b, tau_d, abs_d = simple_glazing_angular_factors(
                    cos_inc, batch.surf_u_value[b], batch.surf_shgc[b]
                )
                qw = np.where(win_m, i_beam * abs_b + i_diff * abs_d, 0.0)
                areas = np.where(batch.surf_mask[b], batch.surf_area[b], 0.0)
                q_tb = np.sum(np.where(win_m, i_beam * tau_b, 0.0) * areas[None, :], axis=1)
                q_td = np.sum(np.where(win_m, i_diff * tau_d, 0.0) * areas[None, :], axis=1)
                win_loss_area = float(
                    np.sum(
                        np.where(
                            is_window[b] & batch.surf_mask[b],
                            areas * (tau_d[0] + abs_d[0]),
                            0.0,
                        )
                    )
                )
                qi, q_diff_inc = distribute_full_exterior_interior_solar(
                    q_tb,
                    q_td,
                    areas,
                    alpha_in[b],
                    is_floor[b],
                    is_non_window[b],
                    win_back_loss_area=win_loss_area,
                )
                qw = qw + np.where(win_m, q_diff_inc[:, None] * abs_d, 0.0)
            else:
                qw = np.zeros_like(qo)
                qi = np.zeros_like(qo)
            return qo, qi, qw

        q_out[b], q_in[b], q_win[b] = _compute_period(
            w.dni,
            w.dhi,
            w.solcos_x,
            w.solcos_y,
            w.solcos_z,
            w.perez_f1,
            w.perez_f2,
            sunlit_frac[b] if sunlit_frac is not None else None,
        )
        wu_q_out[b], wu_q_in[b], wu_q_win[b] = _compute_period(
            w.warmup_dni,
            w.warmup_dhi,
            w.warmup_solcos_x,
            w.warmup_solcos_y,
            w.warmup_solcos_z,
            w.warmup_perez_f1,
            w.warmup_perez_f2,
            wu_sunlit_frac[b] if wu_sunlit_frac is not None else None,
        )
    return q_out, q_in, q_win, wu_q_out, wu_q_in, wu_q_win


def run_stage_a_batch(
    batch: BatchSpec,
    weather: WeatherSeries | list[WeatherSeries],
    ctf: CtfCoefficients | None = None,
    record_zone_temp: bool = False,
    sunlit_frac: np.ndarray | None = None,
    wu_sunlit_frac: np.ndarray | None = None,
    xp: Any = np,
) -> SimulationResult:
    """Run batched S0 warm-up and annual heat-balance simulation.

    Args:
        batch: Compiled ``BatchSpec`` of shape ``[B, S]``.
        weather: Shared ``WeatherSeries`` or list of ``B`` ``WeatherSeries``.
        ctf: Optional internal-mass CTF coefficients (defaults to golden ``.eio``).
        record_zone_temp: If True, record per-timestep zone temperatures ``[B, T]``.
        xp: Array namespace (defaults to NumPy).

    Returns:
        ``SimulationResult`` with hourly/annual heating, warm-up days, and
        optional zone temperature trajectories.
    """
    b_size = batch.batch_size
    n_surf = batch.max_surfaces
    sph = batch.steps_per_hour
    dt_zone_hr = 1.0 / float(sph)
    dt_zone_sec = 3600.0 / float(sph)
    steps_per_day = 24 * sph
    limit_num_sys = max(1, int(round(dt_zone_hr / MIN_TIME_STEP_SYS_HR)))

    if ctf is None:
        ctf = load_ctf_from_eio(steps_per_hour=sph)
    n_ctf_hist = ctf.num_terms

    _, script_f = compute_batch_view_factors(batch)
    script_f_sigma = script_f * STEFAN_BOLTZMANN

    t_db_all, w_out_all, pb_all, t_sky_all, wu_db, wu_w, wu_pb, wu_sky = (
        _stack_weather(weather, b_size)
    )
    n_run_steps = t_db_all.shape[1]
    n_hours = n_run_steps // sph

    gain_ts = np.stack(
        [
            expand_hourly_to_timestep(batch.zone_gain_hourly_w[b], steps_per_hour=sph)
            for b in range(b_size)
        ],
        axis=0,
    )
    wu_gain = gain_ts[:, :steps_per_day]

    surf_mask = batch.surf_mask
    is_osc = (batch.surf_boundary == BOUND_OSC) & surf_mask
    is_outdoors_op = (
        (batch.surf_boundary == BOUND_OUTDOORS) | (batch.surf_boundary == BOUND_DOOR)
    ) & surf_mask
    is_intmass = (batch.surf_boundary == BOUND_INTMASS) & surf_mask
    is_window = (batch.surf_boundary == BOUND_WINDOW) & surf_mask
    is_non_window = surf_mask & (~is_window)
    has_window = bool(np.any(is_window))
    has_solar = (
        batch.surf_sun_exposed is not None
        and bool(np.any(batch.surf_sun_exposed & surf_mask))
    )
    if has_solar:
        q_sol_out_all, q_sw_in_all, q_sol_win_all, wu_q_out, wu_q_in, wu_q_win = (
            _precompute_batch_solar(
                batch,
                weather,
                is_outdoors_op,
                is_window,
                is_non_window,
                sunlit_frac=sunlit_frac,
                wu_sunlit_frac=wu_sunlit_frac,
            )
        )
    else:
        q_sol_out_all = q_sw_in_all = q_sol_win_all = None
        wu_q_out = wu_q_in = wu_q_win = None

    def _run_py() -> SimulationResult:
        nonlocal ctf
        return _run_stage_a_numpy_loop(
            batch=batch,
            ctf=ctf,
            script_f=script_f,
            script_f_sigma=script_f_sigma,
            t_db_all=t_db_all,
            w_out_all=w_out_all,
            pb_all=pb_all,
            t_sky_all=t_sky_all,
            wu_db=wu_db,
            wu_w=wu_w,
            wu_pb=wu_pb,
            wu_sky=wu_sky,
            gain_ts=gain_ts,
            wu_gain=wu_gain,
            surf_mask=surf_mask,
            is_osc=is_osc,
            is_outdoors_op=is_outdoors_op,
            is_intmass=is_intmass,
            is_window=is_window,
            is_non_window=is_non_window,
            has_window=has_window,
            q_sol_out_all=q_sol_out_all,
            q_sw_in_all=q_sw_in_all,
            q_sol_win_all=q_sol_win_all,
            wu_q_out=wu_q_out,
            wu_q_in=wu_q_in,
            wu_q_win=wu_q_win,
            record_zone_temp=record_zone_temp,
            xp=xp,
        )

    rust = load_gpusim_rust_module()
    rust_fn = None
    if xp is np and rust is not None and hasattr(rust, "sim_run_stage_a_batch"):
        def _run_rust() -> SimulationResult:
            payload: dict[str, Any] = {
                "b_size": int(b_size),
                "n_surf_max": int(n_surf),
                "steps_per_hour": int(sph),
                "n_run_steps": int(n_run_steps),
                "ctf_n_terms": int(n_ctf_hist),
                "record_zone_temp": bool(record_zone_temp),
                "has_solar": bool(has_solar),
                "warmup_min_days": np.ascontiguousarray(batch.warmup_min_days, dtype=np.int32),
                "warmup_max_days": np.ascontiguousarray(batch.warmup_max_days, dtype=np.int32),
                "temp_conv_tol": np.ascontiguousarray(batch.temp_conv_tol, dtype=np.float64),
                "loads_conv_tol": np.ascontiguousarray(batch.loads_conv_tol, dtype=np.float64),
                "h_conv_min": np.ascontiguousarray(batch.h_conv_min, dtype=np.float64),
                "zone_volume": np.ascontiguousarray(batch.zone_volume, dtype=np.float64),
                "zone_centroid_z": np.ascontiguousarray(batch.zone_centroid_z, dtype=np.float64),
                "zone_vent_flow_m3s": np.ascontiguousarray(batch.zone_vent_flow_m3s, dtype=np.float64),
                "zone_heat_setpoint": np.ascontiguousarray(batch.zone_heat_setpoint, dtype=np.float64),
                "zone_cool_setpoint": np.ascontiguousarray(batch.zone_cool_setpoint, dtype=np.float64),
                "zone_max_heat_supply_temp": np.ascontiguousarray(
                    batch.zone_max_heat_supply_temp, dtype=np.float64
                ),
                "surf_mask": np.ascontiguousarray(batch.surf_mask, dtype=bool),
                "surf_boundary": np.ascontiguousarray(batch.surf_boundary, dtype=np.int32),
                "surf_area": np.ascontiguousarray(batch.surf_area, dtype=np.float64),
                "surf_u_value": np.ascontiguousarray(batch.surf_u_value, dtype=np.float64),
                "surf_centroid_z": np.ascontiguousarray(batch.surf_centroid_z, dtype=np.float64),
                "surf_cos_tilt": np.ascontiguousarray(batch.surf_cos_tilt, dtype=np.float64),
                "surf_sin_tilt": np.ascontiguousarray(batch.surf_sin_tilt, dtype=np.float64),
                "surf_tilt_deg": np.ascontiguousarray(batch.surf_tilt_deg, dtype=np.float64),
                "surf_height": np.ascontiguousarray(batch.surf_height, dtype=np.float64),
                "surf_eps_out": np.ascontiguousarray(batch.surf_eps_out, dtype=np.float64),
                "surf_eps_in": np.ascontiguousarray(batch.surf_eps_in, dtype=np.float64),
                "surf_vf_sky_ir": np.ascontiguousarray(batch.surf_vf_sky_ir, dtype=np.float64),
                "surf_vf_ground_ir": np.ascontiguousarray(batch.surf_vf_ground_ir, dtype=np.float64),
                "surf_air_sky_rad_split": np.ascontiguousarray(
                    batch.surf_air_sky_rad_split, dtype=np.float64
                ),
                "surf_osc_c_const": np.ascontiguousarray(batch.surf_osc_c_const, dtype=np.float64),
                "surf_osc_t_const": np.ascontiguousarray(batch.surf_osc_t_const, dtype=np.float64),
                "surf_osc_c_out": np.ascontiguousarray(batch.surf_osc_c_out, dtype=np.float64),
                "surf_osc_c_zone": np.ascontiguousarray(batch.surf_osc_c_zone, dtype=np.float64),
                "script_f": np.ascontiguousarray(script_f, dtype=np.float64),
                "ctf_outside": np.ascontiguousarray(ctf.outside, dtype=np.float64),
                "ctf_cross": np.ascontiguousarray(ctf.cross, dtype=np.float64),
                "ctf_inside": np.ascontiguousarray(ctf.inside, dtype=np.float64),
                "ctf_flux": np.ascontiguousarray(ctf.flux, dtype=np.float64),
                "t_db_all": np.ascontiguousarray(t_db_all, dtype=np.float64),
                "w_out_all": np.ascontiguousarray(w_out_all, dtype=np.float64),
                "pb_all": np.ascontiguousarray(pb_all, dtype=np.float64),
                "t_sky_all": np.ascontiguousarray(t_sky_all, dtype=np.float64),
                "wu_db": np.ascontiguousarray(wu_db, dtype=np.float64),
                "wu_w": np.ascontiguousarray(wu_w, dtype=np.float64),
                "wu_pb": np.ascontiguousarray(wu_pb, dtype=np.float64),
                "wu_sky": np.ascontiguousarray(wu_sky, dtype=np.float64),
                "gain_ts": np.ascontiguousarray(gain_ts, dtype=np.float64),
                "wu_gain": np.ascontiguousarray(wu_gain, dtype=np.float64),
            }
            if has_solar:
                payload["q_sol_out_all"] = np.ascontiguousarray(q_sol_out_all, dtype=np.float64)
                payload["q_sw_in_all"] = np.ascontiguousarray(q_sw_in_all, dtype=np.float64)
                payload["q_sol_win_all"] = np.ascontiguousarray(q_sol_win_all, dtype=np.float64)
                payload["wu_q_out"] = np.ascontiguousarray(wu_q_out, dtype=np.float64)
                payload["wu_q_in"] = np.ascontiguousarray(wu_q_in, dtype=np.float64)
                payload["wu_q_win"] = np.ascontiguousarray(wu_q_win, dtype=np.float64)

            h_arr, a_arr, w_arr, zt_opt, zm_opt = rust.sim_run_stage_a_batch(payload, False)
            return SimulationResult(
                cell_ids=list(batch.cell_ids),
                hourly_heating_j=h_arr,
                annual_heating_kwh=a_arr,
                warmup_days=w_arr,
                zone_air_temp_c=zt_opt,
                zone_mean_air_temp_c=zm_opt,
            )

        rust_fn = _run_rust

    return dispatch_gpusim_rust(
        "openubem.gpusim.backends.numpy_ref.run_stage_a_batch",
        _run_py,
        rust_fn,
        bucket="B2",
        rtol=1e-9 if b_size == 1 else 1e-4,
        atol=1e-4 if b_size == 1 else 1e-1,
    )


def _run_stage_a_numpy_loop(
    *,
    batch: BatchSpec,
    ctf: CtfCoefficients,
    script_f: np.ndarray,
    script_f_sigma: np.ndarray,
    t_db_all: np.ndarray,
    w_out_all: np.ndarray,
    pb_all: np.ndarray,
    t_sky_all: np.ndarray,
    wu_db: np.ndarray,
    wu_w: np.ndarray,
    wu_pb: np.ndarray,
    wu_sky: np.ndarray,
    gain_ts: np.ndarray,
    wu_gain: np.ndarray,
    surf_mask: np.ndarray,
    is_osc: np.ndarray,
    is_outdoors_op: np.ndarray,
    is_intmass: np.ndarray,
    is_window: np.ndarray,
    is_non_window: np.ndarray,
    has_window: bool,
    q_sol_out_all: np.ndarray | None,
    q_sw_in_all: np.ndarray | None,
    q_sol_win_all: np.ndarray | None,
    wu_q_out: np.ndarray | None,
    wu_q_in: np.ndarray | None,
    wu_q_win: np.ndarray | None,
    record_zone_temp: bool,
    xp: Any,
) -> SimulationResult:
    b_size = batch.batch_size
    n_surf = batch.max_surfaces
    sph = batch.steps_per_hour
    dt_zone_hr = 1.0 / float(sph)
    dt_zone_sec = 3600.0 / float(sph)
    steps_per_day = 24 * sph
    limit_num_sys = max(1, int(round(dt_zone_hr / MIN_TIME_STEP_SYS_HR)))
    n_ctf_hist = ctf.num_terms
    n_run_steps = t_db_all.shape[1]
    n_hours = n_run_steps // sph

    area_masked = np.where(surf_mask, batch.surf_area, 0.0)
    h_min_2d = batch.h_conv_min[:, None]
    scon_win = np.where(
        is_window,
        simple_glazing_layer_conductance(batch.surf_u_value, xp=xp),
        1.0,
    )

    ctf_out0 = np.where(is_intmass, ctf.outside[0], batch.surf_u_value)
    ctf_cross0 = np.where(is_intmass, ctf.cross[0], batch.surf_u_value)
    ctf_in0 = np.where(is_intmass, ctf.inside[0], batch.surf_u_value)
    ctf_out_tail = np.where(
        is_intmass[:, :, None],
        ctf.outside[1:][None, None, :],
        0.0,
    )
    ctf_cross_tail = np.where(
        is_intmass[:, :, None],
        ctf.cross[1:][None, None, :],
        0.0,
    )
    ctf_in_tail = np.where(
        is_intmass[:, :, None],
        ctf.inside[1:][None, None, :],
        0.0,
    )
    ctf_flux_tail = np.where(
        is_intmass[:, :, None],
        ctf.flux[None, None, :],
        0.0,
    )

    t_out_init_air = out_dry_bulb_temp_at(
        wu_db[:, 0:1], batch.surf_centroid_z, xp=xp
    )
    is_ext_env = is_outdoors_op | is_window

    t_surf_in = np.full((b_size, n_surf), SURF_INITIAL_TEMP, dtype=np.float64)
    t_surf_out = np.where(is_ext_env, t_out_init_air, SURF_INITIAL_TEMP)

    t_in_hist = np.full(
        (b_size, n_surf, n_ctf_hist), SURF_INITIAL_TEMP, dtype=np.float64
    )
    t_out_hist = np.broadcast_to(
        t_surf_out[:, :, None], (b_size, n_surf, n_ctf_hist)
    ).copy()
    q_init = batch.surf_u_value * (t_surf_out - SURF_INITIAL_TEMP)
    q_init = np.where(is_intmass, 0.0, q_init)
    q_out_hist = np.broadcast_to(
        q_init[:, :, None], (b_size, n_surf, n_ctf_hist)
    ).copy()
    q_in_hist = q_out_hist.copy()

    t_mat = np.full(b_size, ZONE_INITIAL_TEMP, dtype=np.float64)
    xmat = np.full((b_size, 4), ZONE_INITIAL_TEMP, dtype=np.float64)
    dsxmat = np.full((b_size, 4), ZONE_INITIAL_TEMP, dtype=np.float64)
    w_zone = wu_w[:, 0].copy()
    w_zone_avg = wu_w[:, 0].copy()
    w_prev_ts = np.broadcast_to(wu_w[:, 0:1], (b_size, 4)).copy()
    dsw_prev_ts = w_prev_ts.copy()
    num_sys_last = np.ones(b_size, dtype=np.int32)

    theta1_win = t_surf_out + KELVIN_CONV
    theta2_win = t_surf_in + KELVIN_CONV

    def _step_one(
        t_site: np.ndarray,
        w_site: np.ndarray,
        pb_site: np.ndarray,
        t_sky_site: np.ndarray,
        gain_w: np.ndarray,
        begin_envrn: bool,
        active_b: np.ndarray | None,
        q_sol_out: Any = 0.0,
        q_sw_in: Any = 0.0,
        q_sol_win: Any = 0.0,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        nonlocal t_surf_in, t_surf_out, t_in_hist, t_out_hist, q_out_hist, q_in_hist
        nonlocal t_mat, xmat, dsxmat, w_zone, w_zone_avg, w_prev_ts, dsw_prev_ts
        nonlocal num_sys_last, theta1_win, theta2_win

        t_out_surf_air = out_dry_bulb_temp_at(
            t_site[:, None], batch.surf_centroid_z, xp=xp
        )
        t_out_zone_air = out_dry_bulb_temp_at(t_site, batch.zone_centroid_z, xp=xp)

        h_in_op = calc_inside_convection_opaque(
            t_surf_in, t_mat[:, None], batch.surf_cos_tilt, h_min_2d, xp=xp
        )
        if has_window:
            h_in_win = calc_iso15099_window_int_conv_coeff(
                t_surf_in,
                t_mat[:, None],
                w_zone_avg[:, None],
                pb_site[:, None],
                batch.surf_height,
                batch.surf_tilt_deg,
                batch.surf_sin_tilt,
                h_min=h_min_2d,
                xp=xp,
            )
            h_conv_in = np.where(is_window, h_in_win, h_in_op)
        else:
            h_conv_in = h_in_op
        h_conv_in = np.where(surf_mask, h_conv_in, 0.0)

        ctf_const_in, ctf_const_out = calc_ctf_const_parts(
            t_out_hist,
            t_in_hist,
            q_out_hist,
            q_in_hist,
            ctf_out_tail,
            ctf_cross_tail,
            ctf_in_tail,
            ctf_flux_tail,
            xp=xp,
        )

        q_lw_out_pass, _ = calc_interior_rad_exchange(
            t_surf_in,
            script_f_sigma,
            batch.surf_eps_in,
            is_window,
            surf_mask,
            xp=xp,
        )

        t_out_osc = calc_osc_outside_temp(
            t_mat[:, None],
            t_out_surf_air,
            batch.surf_osc_c_const,
            batch.surf_osc_t_const,
            batch.surf_osc_c_out,
            batch.surf_osc_c_zone,
            xp=xp,
        )

        hc_ext_op = calc_outside_convection_doe2(
            t_surf_out, t_out_surf_air, batch.surf_cos_tilt, xp=xp
        )
        hsky_op, hgrd_op, hair_op = calc_outside_rad_coeffs(
            t_surf_out,
            t_out_surf_air,
            t_sky_site[:, None],
            batch.surf_eps_out,
            batch.surf_vf_sky_ir,
            batch.surf_vf_ground_ir,
            batch.surf_air_sky_rad_split,
            xp=xp,
        )
        t_out_ext_op = calc_outdoors_outside_temp(
            t_mat[:, None],
            t_out_surf_air,
            t_sky_site[:, None],
            t_site[:, None],
            t_surf_in,
            ctf_out0,
            ctf_cross0,
            ctf_in0,
            ctf_const_out,
            ctf_const_in,
            hc_ext_op,
            hair_op,
            hsky_op,
            hgrd_op,
            h_conv_in,
            q_lw_out_pass,
            q_sol_out_abs=q_sol_out,
            q_sw_in_abs=q_sw_in,
            xp=xp,
        )

        new_t_surf_out = np.where(
            is_osc,
            t_out_osc,
            np.where(
                is_outdoors_op,
                t_out_ext_op,
                np.where(is_intmass, t_surf_in, t_surf_out),
            ),
        )

        cur_t_in = t_surf_in.copy()
        cur_t_out = new_t_surf_out
        cur_h_in = h_conv_in
        new_theta1 = theta1_win
        new_theta2 = theta2_win

        for it in range(MAX_INSIDE_SURF_ITERS):
            t_in_old = cur_t_in
            q_net_lw, ir_parent = calc_interior_rad_exchange(
                cur_t_in,
                script_f_sigma,
                batch.surf_eps_in,
                is_window,
                surf_mask,
                xp=xp,
            )

            if it > 0 and (it % ITERS_REEVAL_CONV_COEFF == 0):
                h_re_op = calc_inside_convection_opaque(
                    cur_t_in, t_mat[:, None], batch.surf_cos_tilt, h_min_2d, xp=xp
                )
                cur_h_in = np.where(is_non_window, h_re_op, cur_h_in)

            if it == 0 and has_window:
                hc_ext_w = calc_outside_convection_doe2(
                    cur_t_out, t_out_surf_air, batch.surf_cos_tilt, xp=xp
                )
                if begin_envrn:
                    th1_init, th2_init = starting_window_temps(
                        t_mat[:, None] + KELVIN_CONV,
                        t_out_surf_air + KELVIN_CONV,
                        cur_h_in,
                        hc_ext_w,
                        scon_win,
                        xp=xp,
                    )
                else:
                    th1_init = theta1_win
                    th2_init = theta2_win

                win_tin, win_tout, win_hin, _, (th1_s, th2_s) = solve_simple_window(
                    t_in_c=t_mat[:, None],
                    t_out_c=t_out_surf_air,
                    t_sky_c=t_sky_site[:, None],
                    hum_rat=w_zone_avg[:, None],
                    baro_press=pb_site[:, None],
                    h_out=hc_ext_w,
                    rmir=ir_parent,
                    scon=scon_win,
                    eps_out=batch.surf_eps_out,
                    eps_in=batch.surf_eps_in,
                    vf_sky_ir=batch.surf_vf_sky_ir,
                    vf_ground_ir=batch.surf_vf_ground_ir,
                    air_sky_split=batch.surf_air_sky_rad_split,
                    height=batch.surf_height,
                    tilt_deg=batch.surf_tilt_deg,
                    sin_tilt=batch.surf_sin_tilt,
                    h_min=h_min_2d,
                    theta1_init=th1_init,
                    theta2_init=th2_init,
                    win_mask=is_window,
                    q_sol_win_abs_w_m2=q_sol_win,
                    xp=xp,
                )
                cur_t_in = np.where(is_window, win_tin, cur_t_in)
                cur_t_out = np.where(is_window, win_tout, cur_t_out)
                cur_h_in = np.where(is_window, win_hin, cur_h_in)
                new_theta1 = np.where(is_window, th1_s, new_theta1)
                new_theta2 = np.where(is_window, th2_s, new_theta2)

            op_t_in = calc_inside_surface_step(
                t_in_old=t_in_old,
                t_out_curr=cur_t_out,
                t_zone=t_mat[:, None],
                h_conv_in=cur_h_in,
                q_rad_net_lw_in=q_net_lw,
                ctf_in0=ctf_in0,
                ctf_cross0=ctf_cross0,
                ctf_const_in=ctf_const_in,
                is_adiabatic=is_intmass,
                q_sw_in_abs=q_sw_in,
                iter_damp_const=ITER_DAMP_CONST,
                xp=xp,
            )
            cur_t_in = np.where(is_non_window, op_t_in, cur_t_in)

            del_t = np.where(is_non_window, np.abs(cur_t_in - t_in_old), 0.0)
            if active_b is not None:
                del_t = np.where(active_b[:, None], del_t, 0.0)
            if float(np.max(del_t)) <= MAX_ALLOWED_DEL_TEMP:
                break

        ha_s = cur_h_in * area_masked
        sum_ha = np.sum(ha_s, axis=1)
        sum_hat = np.sum(ha_s * cur_t_in, axis=1)
        mcpv, vamfl, mcptv = calc_ventilation_mcp(
            batch.zone_vent_flow_m3s, t_out_zone_air, w_site, pb_site, xp=xp
        )

        q_load_h, _, _ = predict_zone_load(
            t_zone_mat=t_mat,
            hum_rat=w_zone,
            baro_press=pb_site,
            zone_vol=batch.zone_volume,
            dt_sys_sec=dt_zone_sec,
            ztm=xmat,
            sum_ha=sum_ha,
            sum_hat_surf=sum_hat,
            sum_mcp=mcpv,
            sum_mcpt=mcptv,
            sum_int_gain=gain_w,
            heat_setpoint=batch.zone_heat_setpoint,
            cool_setpoint=batch.zone_cool_setpoint,
            xp=xp,
        )
        m_sup, t_sup, w_sup, sen_heat, tot_heat = calc_ideal_loads_heating(
            q_heat_req=q_load_h,
            t_zone_node=t_mat,
            w_zone_node=w_zone,
            zone_hum_rat=w_zone,
            baro_press=pb_site,
            max_heat_supply_temp=batch.zone_max_heat_supply_temp,
            heat_on=True,
            xp=xp,
        )
        zt_new, w_new = correct_zone_air_temp_and_humrat(
            t_zone_mat=t_mat,
            hum_rat=w_zone,
            baro_press=pb_site,
            zone_vol=batch.zone_volume,
            dt_sys_sec=dt_zone_sec,
            ztm=xmat,
            w_prev=w_prev_ts,
            sum_ha=sum_ha,
            sum_hat_surf=sum_hat,
            sum_mcp=mcpv,
            sum_mcpt=mcptv,
            sum_int_gain=gain_w,
            m_dot_sup=m_sup,
            t_sup=t_sup,
            w_sup=w_sup,
            vamfl=vamfl,
            out_hum_rat=w_site,
            xp=xp,
        )

        temp_change = np.abs(zt_new - xmat[:, 0])
        needs_sub = temp_change > MAX_ZONE_TEMP_DIFF
        if active_b is not None:
            needs_sub = needs_sub & active_b

        ztav = zt_new.copy()
        w_avg = w_new.copy()
        heat_energy_j = tot_heat * dt_zone_sec
        sn_heat_rate = sen_heat.copy()
        new_num_sys = np.ones(b_size, dtype=np.int32)
        new_dsxmat = dsxmat.copy()
        new_dsw = dsw_prev_ts.copy()

        if bool(np.any(needs_sub)):
            for b_idx in np.where(needs_sub)[0]:
                n_sub = min(
                    int(temp_change[b_idx] / MAX_ZONE_TEMP_DIFF + 1.0),
                    limit_num_sys,
                )
                dt_sub_hr = max(dt_zone_hr / float(n_sub), MIN_TIME_STEP_SYS_HR)
                dt_sub_sec = dt_sub_hr * 3600.0
                frac_sub = dt_sub_hr / dt_zone_hr
                new_num_sys[b_idx] = n_sub

                b_mat = float(xmat[b_idx, 0])
                b_w = float(w_prev_ts[b_idx, 0])
                if n_sub != int(num_sys_last[b_idx]):
                    b_dsx = down_interpolate_4_history_values(
                        dt_zone_hr, dt_sub_hr, xmat[b_idx], xp=np
                    )
                    b_dsw = down_interpolate_4_history_values(
                        dt_zone_hr, dt_sub_hr, w_prev_ts[b_idx], xp=np
                    )
                else:
                    b_dsx = dsxmat[b_idx].copy()
                    b_dsw = dsw_prev_ts[b_idx].copy()

                acc_zt = 0.0
                acc_w = 0.0
                acc_e = 0.0
                acc_sen = 0.0
                for _ in range(n_sub):
                    ql_s, _, _ = predict_zone_load(
                        t_zone_mat=b_mat,
                        hum_rat=b_w,
                        baro_press=pb_site[b_idx],
                        zone_vol=batch.zone_volume[b_idx],
                        dt_sys_sec=dt_sub_sec,
                        ztm=b_dsx,
                        sum_ha=sum_ha[b_idx],
                        sum_hat_surf=sum_hat[b_idx],
                        sum_mcp=mcpv[b_idx],
                        sum_mcpt=mcptv[b_idx],
                        sum_int_gain=gain_w[b_idx],
                        heat_setpoint=batch.zone_heat_setpoint[b_idx],
                        cool_setpoint=batch.zone_cool_setpoint[b_idx],
                        xp=np,
                    )
                    ms_s, ts_s, ws_s, sh_s, th_s = calc_ideal_loads_heating(
                        q_heat_req=ql_s,
                        t_zone_node=b_mat,
                        w_zone_node=b_w,
                        zone_hum_rat=b_w,
                        baro_press=pb_site[b_idx],
                        max_heat_supply_temp=batch.zone_max_heat_supply_temp[b_idx],
                        heat_on=True,
                        xp=np,
                    )
                    zt_s, wn_s = correct_zone_air_temp_and_humrat(
                        t_zone_mat=b_mat,
                        hum_rat=b_w,
                        baro_press=pb_site[b_idx],
                        zone_vol=batch.zone_volume[b_idx],
                        dt_sys_sec=dt_sub_sec,
                        ztm=b_dsx,
                        w_prev=b_dsw,
                        sum_ha=sum_ha[b_idx],
                        sum_hat_surf=sum_hat[b_idx],
                        sum_mcp=mcpv[b_idx],
                        sum_mcpt=mcptv[b_idx],
                        sum_int_gain=gain_w[b_idx],
                        m_dot_sup=ms_s,
                        t_sup=ts_s,
                        w_sup=ws_s,
                        vamfl=vamfl[b_idx],
                        out_hum_rat=w_site[b_idx],
                        xp=np,
                    )
                    b_mat = float(zt_s)
                    b_w = float(wn_s)
                    b_dsx = np.array([b_mat, b_dsx[0], b_dsx[1], b_dsx[2]])
                    b_dsw = np.array([b_w, b_dsw[0], b_dsw[1], b_dsw[2]])
                    acc_zt += b_mat * frac_sub
                    acc_w += b_w * frac_sub
                    acc_e += float(th_s) * dt_sub_sec
                    acc_sen += float(sh_s) * frac_sub

                zt_new[b_idx] = b_mat
                w_new[b_idx] = b_w
                ztav[b_idx] = acc_zt
                w_avg[b_idx] = acc_w
                heat_energy_j[b_idx] = acc_e
                sn_heat_rate[b_idx] = acc_sen
                new_dsxmat[b_idx] = b_dsx
                new_dsw[b_idx] = b_dsw

        next_xmat = np.concatenate([ztav[:, None], xmat[:, :-1]], axis=1)
        next_w_prev = np.concatenate([w_avg[:, None], w_prev_ts[:, :-1]], axis=1)

        next_to_h, next_ti_h, next_qo_h, next_qi_h = update_ctf_histories(
            cur_t_out,
            cur_t_in,
            ctf_const_in,
            ctf_const_out,
            ctf_out0,
            ctf_cross0,
            ctf_in0,
            t_out_hist,
            t_in_hist,
            q_out_hist,
            q_in_hist,
            xp=xp,
        )

        if active_b is None:
            t_surf_in = cur_t_in
            t_surf_out = cur_t_out
            theta1_win = new_theta1
            theta2_win = new_theta2
            t_out_hist = next_to_h
            t_in_hist = next_ti_h
            q_out_hist = next_qo_h
            q_in_hist = next_qi_h
            t_mat = zt_new
            w_zone = w_new
            w_zone_avg = w_avg
            xmat = next_xmat
            w_prev_ts = next_w_prev
            dsxmat = new_dsxmat
            dsw_prev_ts = new_dsw
            num_sys_last = new_num_sys
        else:
            m2 = active_b[:, None]
            m3 = active_b[:, None, None]
            t_surf_in = np.where(m2, cur_t_in, t_surf_in)
            t_surf_out = np.where(m2, cur_t_out, t_surf_out)
            theta1_win = np.where(m2, new_theta1, theta1_win)
            theta2_win = np.where(m2, new_theta2, theta2_win)
            t_out_hist = np.where(m3, next_to_h, t_out_hist)
            t_in_hist = np.where(m3, next_ti_h, t_in_hist)
            q_out_hist = np.where(m3, next_qo_h, q_out_hist)
            q_in_hist = np.where(m3, next_qi_h, q_in_hist)
            t_mat = np.where(active_b, zt_new, t_mat)
            w_zone = np.where(active_b, w_new, w_zone)
            w_zone_avg = np.where(active_b, w_avg, w_zone_avg)
            xmat = np.where(m2, next_xmat, xmat)
            w_prev_ts = np.where(m2, next_w_prev, w_prev_ts)
            dsxmat = np.where(m2, new_dsxmat, dsxmat)
            dsw_prev_ts = np.where(m2, new_dsw, dsw_prev_ts)
            num_sys_last = np.where(active_b, new_num_sys, num_sys_last)

        return heat_energy_j, ztav, sn_heat_rate

    max_wu_days = int(np.max(batch.warmup_max_days))
    still_warming = np.ones(b_size, dtype=bool)
    warmup_days = np.zeros(b_size, dtype=np.int32)
    max_t_prev = np.full(b_size, -9999.0, dtype=np.float64)
    min_t_prev = np.full(b_size, 1000.0, dtype=np.float64)
    max_h_prev = np.full(b_size, -9999.0, dtype=np.float64)

    for day in range(1, max_wu_days + 1):
        if not bool(np.any(still_warming)):
            break
        max_t_day = np.full(b_size, -9999.0, dtype=np.float64)
        min_t_day = np.full(b_size, 1000.0, dtype=np.float64)
        max_h_day = np.full(b_size, -9999.0, dtype=np.float64)

        for step in range(steps_per_day):
            _, ztav_step, sn_h_step = _step_one(
                wu_db[:, step],
                wu_w[:, step],
                wu_pb[:, step],
                wu_sky[:, step],
                wu_gain[:, step],
                begin_envrn=(day == 1 and step == 0),
                active_b=still_warming,
                q_sol_out=wu_q_out[:, step, :] if wu_q_out is not None else 0.0,
                q_sw_in=wu_q_in[:, step, :] if wu_q_in is not None else 0.0,
                q_sol_win=wu_q_win[:, step, :] if wu_q_win is not None else 0.0,
            )
            max_t_day = np.maximum(max_t_day, ztav_step)
            min_t_day = np.minimum(min_t_day, ztav_step)
            max_h_day = np.maximum(max_h_day, sn_h_step)

        pass_max_t = np.abs(max_t_prev - max_t_day) <= batch.temp_conv_tol
        pass_min_t = np.abs(min_t_prev - min_t_day) <= batch.temp_conv_tol

        eff_h_day = np.abs(np.maximum(max_h_day, WARMUP_MIN_LOAD))
        eff_h_prev = np.abs(np.maximum(max_h_prev, WARMUP_MIN_LOAD))
        rel_h_diff = np.abs((eff_h_day - eff_h_prev) / eff_h_day)
        pass_h = np.where(
            max_h_day > 1.0e-4,
            rel_h_diff <= batch.loads_conv_tol,
            True,
        )

        converged_now = (
            still_warming
            & (
                (pass_max_t & pass_min_t & pass_h & (day >= batch.warmup_min_days))
                | (day >= batch.warmup_max_days)
            )
        )
        warmup_days = np.where(converged_now, day, warmup_days)
        still_warming = still_warming & (~converged_now)

        max_t_prev = np.where(still_warming, max_t_day, max_t_prev)
        min_t_prev = np.where(still_warming, min_t_day, min_t_prev)
        max_h_prev = np.where(still_warming, eff_h_day, max_h_prev)

    hourly_heating_j = np.zeros((b_size, n_hours), dtype=np.float64)
    z_temp_rec = (
        np.empty((b_size, n_run_steps), dtype=np.float64) if record_zone_temp else None
    )
    z_mean_rec = (
        np.empty((b_size, n_run_steps), dtype=np.float64) if record_zone_temp else None
    )

    for step in range(n_run_steps):
        heat_j, ztav_step, _ = _step_one(
            t_db_all[:, step],
            w_out_all[:, step],
            pb_all[:, step],
            t_sky_all[:, step],
            gain_ts[:, step],
            begin_envrn=False,
            active_b=None,
            q_sol_out=q_sol_out_all[:, step, :] if q_sol_out_all is not None else 0.0,
            q_sw_in=q_sw_in_all[:, step, :] if q_sw_in_all is not None else 0.0,
            q_sol_win=q_sol_win_all[:, step, :] if q_sol_win_all is not None else 0.0,
        )
        hourly_heating_j[:, step // sph] += heat_j
        if z_temp_rec is not None and z_mean_rec is not None:
            z_temp_rec[:, step] = t_mat
            z_mean_rec[:, step] = ztav_step

    annual_kwh = np.sum(hourly_heating_j, axis=1, dtype=np.float64) / 3.6e6
    return SimulationResult(
        cell_ids=list(batch.cell_ids),
        hourly_heating_j=hourly_heating_j,
        annual_heating_kwh=annual_kwh,
        warmup_days=warmup_days,
        zone_air_temp_c=z_temp_rec,
        zone_mean_air_temp_c=z_mean_rec,
    )
