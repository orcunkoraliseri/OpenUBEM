from collections.abc import Sequence

import numpy as np
import torch

from openubem.gpusim.backends.numpy_ref import (
    MAX_ZONE_TEMP_DIFF,
    MIN_TIME_STEP_SYS_HR,
    SURF_INITIAL_TEMP,
    WARMUP_MIN_LOAD,
    ZONE_INITIAL_TEMP,
    SimulationResult,
    _stack_weather,
)
from openubem.gpusim.backends.xp_torch import TorchNamespace
from openubem.gpusim.compile import (
    BOUND_DOOR,
    BOUND_INTMASS,
    BOUND_OSC,
    BOUND_OUTDOORS,
    BOUND_WINDOW,
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


def _to_f64_numpy(tensor: torch.Tensor) -> np.ndarray:
    """Move a PyTorch tensor to a host float64 NumPy array.

    Args:
        tensor: Input tensor on any device.

    Returns:
        Host ``np.float64`` array.
    """
    return tensor.detach().cpu().numpy().astype(np.float64, copy=False)


def _to_bool_numpy(tensor: torch.Tensor) -> np.ndarray:
    """Move a boolean PyTorch tensor to a host boolean NumPy array.

    Args:
        tensor: Input boolean tensor on any device.

    Returns:
        Host ``np.bool_`` array.
    """
    return tensor.detach().cpu().numpy().astype(np.bool_, copy=False)


def run_stage_b_batch(
    batch: BatchSpec,
    weather: WeatherSeries | list[WeatherSeries],
    ctf: CtfCoefficients | None = None,
    record_zone_temp: bool = False,
    device: str | torch.device = "mps",
    dtype: torch.dtype = torch.float32,
    force_warmup_days: Sequence[int] | np.ndarray | None = None,
    capture_steps: dict[int, dict[str, np.ndarray]] | None = None,
    run_days: int | None = None,
) -> SimulationResult:
    """Run batched Stage B heat-balance simulation via PyTorch and shared physics.

    Args:
        batch: Compiled ``BatchSpec`` of shape ``[B, S]``.
        weather: Shared ``WeatherSeries`` or list of ``B`` ``WeatherSeries``.
        ctf: Optional internal-mass CTF coefficients (defaults to golden ``.eio``).
        record_zone_temp: If True, record per-timestep zone temperatures ``[B, T]``.
        device: PyTorch target device (``mps``, ``cuda``, or ``cpu``).
        dtype: Working floating-point dtype (``torch.float32`` on MPS).
        force_warmup_days: Optional per-building warm-up day counts ``[B]``.
        capture_steps: Optional mapping keyed by run-period step indices; populated
            in-place with float64 NumPy inputs and outputs of the inside-surface
            iteration for each requested step.
        run_days: Optional run-period day limit; stops after this many run days
            with warm-up unchanged.

    Returns:
        ``SimulationResult`` with host float64 NumPy outputs and int32 warm-up days.
    """
    dev = torch.device(device)
    if dev.type == "mps" and dtype == torch.float64:
        raise ValueError("MPS does not support float64; use device='cpu' for float64")

    xp = TorchNamespace(device=dev, dtype=dtype)
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
    script_f_sigma = xp.asarray(script_f * STEFAN_BOLTZMANN, dtype=dtype)

    t_db_np, w_out_np, pb_np, t_sky_np, wu_db_np, wu_w_np, wu_pb_np, wu_sky_np = (
        _stack_weather(weather, b_size)
    )
    n_run_steps = t_db_np.shape[1]
    if run_days is not None:
        if run_days <= 0:
            raise ValueError(f"run_days must be positive, got {run_days}")
        n_run_steps = min(n_run_steps, run_days * steps_per_day)
    n_hours = n_run_steps // sph

    gain_ts_np = np.stack(
        [
            expand_hourly_to_timestep(batch.zone_gain_hourly_w[b], steps_per_hour=sph)
            for b in range(b_size)
        ],
        axis=0,
    )
    wu_gain_np = gain_ts_np[:, :steps_per_day]

    t_db_all = xp.asarray(t_db_np, dtype=dtype)
    w_out_all = xp.asarray(w_out_np, dtype=dtype)
    pb_all = xp.asarray(pb_np, dtype=dtype)
    t_sky_all = xp.asarray(t_sky_np, dtype=dtype)
    gain_ts = xp.asarray(gain_ts_np, dtype=dtype)

    wu_db = xp.asarray(wu_db_np, dtype=dtype)
    wu_w = xp.asarray(wu_w_np, dtype=dtype)
    wu_pb = xp.asarray(wu_pb_np, dtype=dtype)
    wu_sky = xp.asarray(wu_sky_np, dtype=dtype)
    wu_gain = xp.asarray(wu_gain_np, dtype=dtype)

    surf_mask_np = batch.surf_mask
    is_osc_np = (batch.surf_boundary == BOUND_OSC) & surf_mask_np
    is_outdoors_op_np = (
        (batch.surf_boundary == BOUND_OUTDOORS)
        | (batch.surf_boundary == BOUND_DOOR)
    ) & surf_mask_np
    is_intmass_np = (batch.surf_boundary == BOUND_INTMASS) & surf_mask_np
    is_window_np = (batch.surf_boundary == BOUND_WINDOW) & surf_mask_np
    is_non_window_np = surf_mask_np & (~is_window_np)
    has_window = bool(np.any(is_window_np))

    surf_mask = xp.asarray(surf_mask_np, dtype=torch.bool)
    is_osc = xp.asarray(is_osc_np, dtype=torch.bool)
    is_outdoors_op = xp.asarray(is_outdoors_op_np, dtype=torch.bool)
    is_intmass = xp.asarray(is_intmass_np, dtype=torch.bool)
    is_window = xp.asarray(is_window_np, dtype=torch.bool)
    is_non_window = xp.asarray(is_non_window_np, dtype=torch.bool)
    is_ext_env = is_outdoors_op | is_window

    surf_area = xp.asarray(batch.surf_area, dtype=dtype)
    surf_centroid_z = xp.asarray(batch.surf_centroid_z, dtype=dtype)
    surf_cos_tilt = xp.asarray(batch.surf_cos_tilt, dtype=dtype)
    surf_sin_tilt = xp.asarray(batch.surf_sin_tilt, dtype=dtype)
    surf_tilt_deg = xp.asarray(batch.surf_tilt_deg, dtype=dtype)
    surf_height = xp.asarray(batch.surf_height, dtype=dtype)
    surf_u_value = xp.asarray(batch.surf_u_value, dtype=dtype)
    surf_osc_c_const = xp.asarray(batch.surf_osc_c_const, dtype=dtype)
    surf_osc_t_const = xp.asarray(batch.surf_osc_t_const, dtype=dtype)
    surf_osc_c_out = xp.asarray(batch.surf_osc_c_out, dtype=dtype)
    surf_osc_c_zone = xp.asarray(batch.surf_osc_c_zone, dtype=dtype)
    surf_eps_in = xp.asarray(batch.surf_eps_in, dtype=dtype)
    surf_eps_out = xp.asarray(batch.surf_eps_out, dtype=dtype)
    surf_vf_sky_ir = xp.asarray(batch.surf_vf_sky_ir, dtype=dtype)
    surf_vf_ground_ir = xp.asarray(batch.surf_vf_ground_ir, dtype=dtype)
    surf_air_sky_rad_split = xp.asarray(batch.surf_air_sky_rad_split, dtype=dtype)

    zone_centroid_z = xp.asarray(batch.zone_centroid_z, dtype=dtype)
    zone_volume = xp.asarray(batch.zone_volume, dtype=dtype)
    zone_vent_flow_m3s = xp.asarray(batch.zone_vent_flow_m3s, dtype=dtype)
    zone_heat_setpoint = xp.asarray(batch.zone_heat_setpoint, dtype=dtype)
    zone_cool_setpoint = xp.asarray(batch.zone_cool_setpoint, dtype=dtype)
    zone_max_heat_supply_temp = xp.asarray(
        batch.zone_max_heat_supply_temp, dtype=dtype
    )
    h_min_1d = xp.asarray(batch.h_conv_min, dtype=dtype)
    h_min_2d = h_min_1d[:, None]
    temp_conv_tol = xp.asarray(batch.temp_conv_tol, dtype=dtype)
    loads_conv_tol = xp.asarray(batch.loads_conv_tol, dtype=dtype)
    wu_min_days_t = torch.as_tensor(batch.warmup_min_days, dtype=torch.int32).to(dev)
    wu_max_days_t = torch.as_tensor(batch.warmup_max_days, dtype=torch.int32).to(dev)

    zero_surf = torch.zeros((b_size, n_surf), dtype=dtype, device=dev)
    one_surf = torch.ones((b_size, n_surf), dtype=dtype, device=dev)
    area_masked = torch.where(surf_mask, surf_area, zero_surf)

    with torch.no_grad():
        scon_win = torch.where(
            is_window,
            simple_glazing_layer_conductance(surf_u_value, xp=xp),
            one_surf,
        )

        ctf_out0 = xp.asarray(
            np.where(is_intmass_np, ctf.outside[0], batch.surf_u_value), dtype=dtype
        )
        ctf_cross0 = xp.asarray(
            np.where(is_intmass_np, ctf.cross[0], batch.surf_u_value), dtype=dtype
        )
        ctf_in0 = xp.asarray(
            np.where(is_intmass_np, ctf.inside[0], batch.surf_u_value), dtype=dtype
        )
        ctf_out_tail = xp.asarray(
            np.where(is_intmass_np[:, :, None], ctf.outside[1:][None, None, :], 0.0),
            dtype=dtype,
        )
        ctf_cross_tail = xp.asarray(
            np.where(is_intmass_np[:, :, None], ctf.cross[1:][None, None, :], 0.0),
            dtype=dtype,
        )
        ctf_in_tail = xp.asarray(
            np.where(is_intmass_np[:, :, None], ctf.inside[1:][None, None, :], 0.0),
            dtype=dtype,
        )
        ctf_flux_tail = xp.asarray(
            np.where(is_intmass_np[:, :, None], ctf.flux[None, None, :], 0.0),
            dtype=dtype,
        )

        t_out_init_air = out_dry_bulb_temp_at(
            wu_db[:, 0:1], surf_centroid_z, xp=xp
        )
        t_surf_in = torch.full(
            (b_size, n_surf), SURF_INITIAL_TEMP, dtype=dtype, device=dev
        )
        t_surf_out = torch.where(is_ext_env, t_out_init_air, t_surf_in)

        t_in_hist = torch.full(
            (b_size, n_surf, n_ctf_hist), SURF_INITIAL_TEMP, dtype=dtype, device=dev
        )
        t_out_hist = t_surf_out[:, :, None].expand(b_size, n_surf, n_ctf_hist).clone()
        q_init = surf_u_value * (t_surf_out - SURF_INITIAL_TEMP)
        q_init = torch.where(is_intmass, zero_surf, q_init)
        q_out_hist = q_init[:, :, None].expand(b_size, n_surf, n_ctf_hist).clone()
        q_in_hist = q_out_hist.clone()

        t_mat = torch.full((b_size,), ZONE_INITIAL_TEMP, dtype=dtype, device=dev)
        xmat = torch.full((b_size, 4), ZONE_INITIAL_TEMP, dtype=dtype, device=dev)
        dsxmat = torch.full((b_size, 4), ZONE_INITIAL_TEMP, dtype=dtype, device=dev)
        w_zone = wu_w[:, 0].clone()
        w_zone_avg = wu_w[:, 0].clone()
        w_prev_ts = wu_w[:, 0:1].expand(b_size, 4).clone()
        dsw_prev_ts = w_prev_ts.clone()
        num_sys_last = torch.ones((b_size,), dtype=torch.int32, device=dev)

        theta1_win = t_surf_out + KELVIN_CONV
        theta2_win = t_surf_in + KELVIN_CONV
        ones_b_int = torch.ones((b_size,), dtype=torch.int32, device=dev)
        zeros_b = torch.zeros((b_size,), dtype=dtype, device=dev)

        def _step_one(
            t_site: torch.Tensor,
            w_site: torch.Tensor,
            pb_site: torch.Tensor,
            t_sky_site: torch.Tensor,
            gain_w: torch.Tensor,
            begin_envrn: bool,
            active_b: torch.Tensor | None,
            capture_step_idx: int | None = None,
        ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            nonlocal t_surf_in, t_surf_out, t_in_hist, t_out_hist
            nonlocal q_out_hist, q_in_hist, t_mat, xmat, dsxmat
            nonlocal w_zone, w_zone_avg, w_prev_ts, dsw_prev_ts
            nonlocal num_sys_last, theta1_win, theta2_win

            t_out_surf_air = out_dry_bulb_temp_at(
                t_site[:, None], surf_centroid_z, xp=xp
            )
            t_out_zone_air = out_dry_bulb_temp_at(t_site, zone_centroid_z, xp=xp)

            h_in_op = calc_inside_convection_opaque(
                t_surf_in, t_mat[:, None], surf_cos_tilt, h_min_2d, xp=xp
            )
            if has_window:
                h_in_win = calc_iso15099_window_int_conv_coeff(
                    t_surf_in,
                    t_mat[:, None],
                    w_zone_avg[:, None],
                    pb_site[:, None],
                    surf_height,
                    surf_tilt_deg,
                    surf_sin_tilt,
                    h_min=h_min_2d,
                    xp=xp,
                )
                h_conv_in = torch.where(is_window, h_in_win, h_in_op)
            else:
                h_conv_in = h_in_op
            h_conv_in = torch.where(surf_mask, h_conv_in, zero_surf)

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
                surf_eps_in,
                is_window,
                surf_mask,
                xp=xp,
            )

            t_out_osc = calc_osc_outside_temp(
                t_mat[:, None],
                t_out_surf_air,
                surf_osc_c_const,
                surf_osc_t_const,
                surf_osc_c_out,
                surf_osc_c_zone,
                xp=xp,
            )

            hc_ext_op = calc_outside_convection_doe2(
                t_surf_out, t_out_surf_air, surf_cos_tilt, xp=xp
            )
            hsky_op, hgrd_op, hair_op = calc_outside_rad_coeffs(
                t_surf_out,
                t_out_surf_air,
                t_sky_site[:, None],
                surf_eps_out,
                surf_vf_sky_ir,
                surf_vf_ground_ir,
                surf_air_sky_rad_split,
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
                xp=xp,
            )

            new_t_surf_out = torch.where(
                is_osc,
                t_out_osc,
                torch.where(
                    is_outdoors_op,
                    t_out_ext_op,
                    torch.where(is_intmass, t_surf_in, t_surf_out),
                ),
            )

            cur_t_in = t_surf_in.clone()
            cur_t_out = new_t_surf_out
            cur_h_in = h_conv_in
            new_theta1 = theta1_win
            new_theta2 = theta2_win

            do_capture = (
                capture_steps is not None
                and capture_step_idx is not None
                and capture_step_idx in capture_steps
            )
            if do_capture:
                cap_t_in_init = cur_t_in.clone()
                cap_t_out_init = cur_t_out.clone()
                cap_h_in_init = cur_h_in.clone()
                cap_th1_init = new_theta1.clone()
                cap_th2_init = new_theta2.clone()

            iters_taken = 0
            for it in range(MAX_INSIDE_SURF_ITERS):
                iters_taken = it + 1
                t_in_old = cur_t_in
                q_net_lw, ir_parent = calc_interior_rad_exchange(
                    cur_t_in,
                    script_f_sigma,
                    surf_eps_in,
                    is_window,
                    surf_mask,
                    xp=xp,
                )

                if it > 0 and (it % ITERS_REEVAL_CONV_COEFF == 0):
                    h_re_op = calc_inside_convection_opaque(
                        cur_t_in, t_mat[:, None], surf_cos_tilt, h_min_2d, xp=xp
                    )
                    cur_h_in = torch.where(is_non_window, h_re_op, cur_h_in)

                if it == 0 and has_window:
                    hc_ext_w = calc_outside_convection_doe2(
                        cur_t_out, t_out_surf_air, surf_cos_tilt, xp=xp
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

                    win_tin, win_tout, win_hin, _, (th1_s, th2_s) = (
                        solve_simple_window(
                            t_in_c=t_mat[:, None],
                            t_out_c=t_out_surf_air,
                            t_sky_c=t_sky_site[:, None],
                            hum_rat=w_zone_avg[:, None],
                            baro_press=pb_site[:, None],
                            h_out=hc_ext_w,
                            rmir=ir_parent,
                            scon=scon_win,
                            eps_out=surf_eps_out,
                            eps_in=surf_eps_in,
                            vf_sky_ir=surf_vf_sky_ir,
                            vf_ground_ir=surf_vf_ground_ir,
                            air_sky_split=surf_air_sky_rad_split,
                            height=surf_height,
                            tilt_deg=surf_tilt_deg,
                            sin_tilt=surf_sin_tilt,
                            h_min=h_min_2d,
                            theta1_init=th1_init,
                            theta2_init=th2_init,
                            win_mask=is_window,
                            xp=xp,
                        )
                    )
                    cur_t_in = torch.where(is_window, win_tin, cur_t_in)
                    cur_t_out = torch.where(is_window, win_tout, cur_t_out)
                    cur_h_in = torch.where(is_window, win_hin, cur_h_in)
                    new_theta1 = torch.where(is_window, th1_s, new_theta1)
                    new_theta2 = torch.where(is_window, th2_s, new_theta2)

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
                    iter_damp_const=ITER_DAMP_CONST,
                    xp=xp,
                )
                cur_t_in = torch.where(is_non_window, op_t_in, cur_t_in)

                del_t = torch.where(
                    is_non_window, torch.abs(cur_t_in - t_in_old), zero_surf
                )
                if active_b is not None:
                    del_t = torch.where(active_b[:, None], del_t, zero_surf)
                if float(torch.max(del_t).item()) <= MAX_ALLOWED_DEL_TEMP:
                    break

            if (
                do_capture
                and capture_steps is not None
                and capture_step_idx is not None
            ):
                capture_steps[capture_step_idx] = {
                    "t_surf_in_init": _to_f64_numpy(cap_t_in_init),
                    "t_surf_out_init": _to_f64_numpy(cap_t_out_init),
                    "h_conv_in_init": _to_f64_numpy(cap_h_in_init),
                    "theta1_init": _to_f64_numpy(cap_th1_init),
                    "theta2_init": _to_f64_numpy(cap_th2_init),
                    "t_mat": _to_f64_numpy(t_mat),
                    "w_zone_avg": _to_f64_numpy(w_zone_avg),
                    "pb_site": _to_f64_numpy(pb_site),
                    "t_sky_site": _to_f64_numpy(t_sky_site),
                    "t_out_surf_air": _to_f64_numpy(t_out_surf_air),
                    "script_f_sigma": _to_f64_numpy(script_f_sigma),
                    "surf_mask": _to_bool_numpy(surf_mask),
                    "is_window": _to_bool_numpy(is_window),
                    "is_non_window": _to_bool_numpy(is_non_window),
                    "is_intmass": _to_bool_numpy(is_intmass),
                    "surf_eps_in": _to_f64_numpy(surf_eps_in),
                    "surf_eps_out": _to_f64_numpy(surf_eps_out),
                    "surf_cos_tilt": _to_f64_numpy(surf_cos_tilt),
                    "surf_sin_tilt": _to_f64_numpy(surf_sin_tilt),
                    "surf_tilt_deg": _to_f64_numpy(surf_tilt_deg),
                    "surf_height": _to_f64_numpy(surf_height),
                    "surf_vf_sky_ir": _to_f64_numpy(surf_vf_sky_ir),
                    "surf_vf_ground_ir": _to_f64_numpy(surf_vf_ground_ir),
                    "surf_air_sky_rad_split": _to_f64_numpy(surf_air_sky_rad_split),
                    "h_min": _to_f64_numpy(h_min_1d),
                    "scon_win": _to_f64_numpy(scon_win),
                    "ctf_in0": _to_f64_numpy(ctf_in0),
                    "ctf_cross0": _to_f64_numpy(ctf_cross0),
                    "ctf_const_in": _to_f64_numpy(ctf_const_in),
                    "begin_envrn": np.asarray(begin_envrn, dtype=np.bool_),
                    "t_surf_in_out": _to_f64_numpy(cur_t_in),
                    "t_surf_out_out": _to_f64_numpy(cur_t_out),
                    "h_conv_in_out": _to_f64_numpy(cur_h_in),
                    "theta1_out": _to_f64_numpy(new_theta1),
                    "theta2_out": _to_f64_numpy(new_theta2),
                    "iter_count": np.full((b_size,), iters_taken, dtype=np.int32),
                }

            ha_s = cur_h_in * area_masked
            sum_ha = torch.sum(ha_s, dim=1)
            sum_hat = torch.sum(ha_s * cur_t_in, dim=1)
            mcpv, vamfl, mcptv = calc_ventilation_mcp(
                zone_vent_flow_m3s, t_out_zone_air, w_site, pb_site, xp=xp
            )

            q_load_h, _, _ = predict_zone_load(
                t_zone_mat=t_mat,
                hum_rat=w_zone,
                baro_press=pb_site,
                zone_vol=zone_volume,
                dt_sys_sec=dt_zone_sec,
                ztm=xmat,
                sum_ha=sum_ha,
                sum_hat_surf=sum_hat,
                sum_mcp=mcpv,
                sum_mcpt=mcptv,
                sum_int_gain=gain_w,
                heat_setpoint=zone_heat_setpoint,
                cool_setpoint=zone_cool_setpoint,
                xp=xp,
            )
            m_sup, t_sup, w_sup, sen_heat, tot_heat = calc_ideal_loads_heating(
                q_heat_req=q_load_h,
                t_zone_node=t_mat,
                w_zone_node=w_zone,
                zone_hum_rat=w_zone,
                baro_press=pb_site,
                max_heat_supply_temp=zone_max_heat_supply_temp,
                heat_on=True,
                xp=xp,
            )
            zt_new, w_new = correct_zone_air_temp_and_humrat(
                t_zone_mat=t_mat,
                hum_rat=w_zone,
                baro_press=pb_site,
                zone_vol=zone_volume,
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

            temp_change = torch.abs(zt_new - xmat[:, 0])
            needs_sub = temp_change > MAX_ZONE_TEMP_DIFF
            if active_b is not None:
                needs_sub = needs_sub & active_b

            ztav = zt_new.clone()
            w_avg = w_new.clone()
            heat_energy_j = tot_heat * dt_zone_sec
            sn_heat_rate = sen_heat.clone()
            new_num_sys = ones_b_int.clone()
            new_dsxmat = dsxmat.clone()
            new_dsw = dsw_prev_ts.clone()

            if bool(torch.any(needs_sub).item()):
                n_sub_raw = torch.clamp(
                    torch.trunc(temp_change / MAX_ZONE_TEMP_DIFF + 1.0).to(torch.int32),
                    max=limit_num_sys,
                )
                n_sub = torch.where(needs_sub, n_sub_raw, ones_b_int)
                max_n_sub = int(torch.max(n_sub).item())

                dt_sub_hr = torch.clamp(
                    dt_zone_hr / n_sub.to(dtype), min=MIN_TIME_STEP_SYS_HR
                )
                dt_sub_sec = dt_sub_hr * 3600.0
                frac_sub = dt_sub_hr / dt_zone_hr

                b_mat = xmat[:, 0].clone()
                b_w = w_prev_ts[:, 0].clone()
                b_dsx = dsxmat.clone()
                b_dsw = dsw_prev_ts.clone()

                diff_sub = needs_sub & (n_sub != num_sys_last)
                for k_sub in range(2, max_n_sub + 1):
                    k_mask = diff_sub & (n_sub == k_sub)
                    if bool(torch.any(k_mask).item()):
                        k_dt_hr = max(
                            dt_zone_hr / float(k_sub), MIN_TIME_STEP_SYS_HR
                        )
                        interp_x = down_interpolate_4_history_values(
                            dt_zone_hr, k_dt_hr, xmat, xp=xp
                        )
                        interp_w = down_interpolate_4_history_values(
                            dt_zone_hr, k_dt_hr, w_prev_ts, xp=xp
                        )
                        b_dsx = torch.where(k_mask[:, None], interp_x, b_dsx)
                        b_dsw = torch.where(k_mask[:, None], interp_w, b_dsw)

                acc_zt = zeros_b.clone()
                acc_w = zeros_b.clone()
                acc_e = zeros_b.clone()
                acc_sen = zeros_b.clone()

                for sub_idx in range(max_n_sub):
                    sub_active = needs_sub & (sub_idx < n_sub)
                    ql_s, _, _ = predict_zone_load(
                        t_zone_mat=b_mat,
                        hum_rat=b_w,
                        baro_press=pb_site,
                        zone_vol=zone_volume,
                        dt_sys_sec=dt_sub_sec,
                        ztm=b_dsx,
                        sum_ha=sum_ha,
                        sum_hat_surf=sum_hat,
                        sum_mcp=mcpv,
                        sum_mcpt=mcptv,
                        sum_int_gain=gain_w,
                        heat_setpoint=zone_heat_setpoint,
                        cool_setpoint=zone_cool_setpoint,
                        xp=xp,
                    )
                    ms_s, ts_s, ws_s, sh_s, th_s = calc_ideal_loads_heating(
                        q_heat_req=ql_s,
                        t_zone_node=b_mat,
                        w_zone_node=b_w,
                        zone_hum_rat=b_w,
                        baro_press=pb_site,
                        max_heat_supply_temp=zone_max_heat_supply_temp,
                        heat_on=True,
                        xp=xp,
                    )
                    zt_s, wn_s = correct_zone_air_temp_and_humrat(
                        t_zone_mat=b_mat,
                        hum_rat=b_w,
                        baro_press=pb_site,
                        zone_vol=zone_volume,
                        dt_sys_sec=dt_sub_sec,
                        ztm=b_dsx,
                        w_prev=b_dsw,
                        sum_ha=sum_ha,
                        sum_hat_surf=sum_hat,
                        sum_mcp=mcpv,
                        sum_mcpt=mcptv,
                        sum_int_gain=gain_w,
                        m_dot_sup=ms_s,
                        t_sup=ts_s,
                        w_sup=ws_s,
                        vamfl=vamfl,
                        out_hum_rat=w_site,
                        xp=xp,
                    )
                    b_mat = torch.where(sub_active, zt_s, b_mat)
                    b_w = torch.where(sub_active, wn_s, b_w)
                    b_dsx_next = torch.cat([b_mat[:, None], b_dsx[:, :-1]], dim=1)
                    b_dsw_next = torch.cat([b_w[:, None], b_dsw[:, :-1]], dim=1)
                    b_dsx = torch.where(sub_active[:, None], b_dsx_next, b_dsx)
                    b_dsw = torch.where(sub_active[:, None], b_dsw_next, b_dsw)
                    acc_zt = torch.where(sub_active, acc_zt + b_mat * frac_sub, acc_zt)
                    acc_w = torch.where(sub_active, acc_w + b_w * frac_sub, acc_w)
                    acc_e = torch.where(sub_active, acc_e + th_s * dt_sub_sec, acc_e)
                    acc_sen = torch.where(
                        sub_active, acc_sen + sh_s * frac_sub, acc_sen
                    )

                zt_new = torch.where(needs_sub, b_mat, zt_new)
                w_new = torch.where(needs_sub, b_w, w_new)
                ztav = torch.where(needs_sub, acc_zt, ztav)
                w_avg = torch.where(needs_sub, acc_w, w_avg)
                heat_energy_j = torch.where(needs_sub, acc_e, heat_energy_j)
                sn_heat_rate = torch.where(needs_sub, acc_sen, sn_heat_rate)
                new_num_sys = torch.where(needs_sub, n_sub, new_num_sys)
                new_dsxmat = torch.where(needs_sub[:, None], b_dsx, new_dsxmat)
                new_dsw = torch.where(needs_sub[:, None], b_dsw, new_dsw)

            next_xmat = torch.cat([ztav[:, None], xmat[:, :-1]], dim=1)
            next_w_prev = torch.cat([w_avg[:, None], w_prev_ts[:, :-1]], dim=1)

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
                t_surf_in = torch.where(m2, cur_t_in, t_surf_in)
                t_surf_out = torch.where(m2, cur_t_out, t_surf_out)
                theta1_win = torch.where(m2, new_theta1, theta1_win)
                theta2_win = torch.where(m2, new_theta2, theta2_win)
                t_out_hist = torch.where(m3, next_to_h, t_out_hist)
                t_in_hist = torch.where(m3, next_ti_h, t_in_hist)
                q_out_hist = torch.where(m3, next_qo_h, q_out_hist)
                q_in_hist = torch.where(m3, next_qi_h, q_in_hist)
                t_mat = torch.where(active_b, zt_new, t_mat)
                w_zone = torch.where(active_b, w_new, w_zone)
                w_zone_avg = torch.where(active_b, w_avg, w_zone_avg)
                xmat = torch.where(m2, next_xmat, xmat)
                w_prev_ts = torch.where(m2, next_w_prev, w_prev_ts)
                dsxmat = torch.where(m2, new_dsxmat, dsxmat)
                dsw_prev_ts = torch.where(m2, new_dsw, dsw_prev_ts)
                num_sys_last = torch.where(active_b, new_num_sys, num_sys_last)

            return heat_energy_j, ztav, sn_heat_rate

        if force_warmup_days is not None:
            force_wu_np = np.asarray(force_warmup_days, dtype=np.int32)
            if force_wu_np.shape != (b_size,):
                raise ValueError(
                    f"force_warmup_days shape {force_wu_np.shape} != ({b_size},)"
                )
            if int(np.min(force_wu_np)) < 1:
                raise ValueError("force_warmup_days entries must be >= 1")
            max_wu_days = int(np.max(force_wu_np))
            force_wu_t = torch.as_tensor(force_wu_np, dtype=torch.int32).to(dev)
        else:
            max_wu_days = int(np.max(batch.warmup_max_days))
            force_wu_t = None

        still_warming = torch.ones((b_size,), dtype=torch.bool, device=dev)
        warmup_days = torch.zeros((b_size,), dtype=torch.int32, device=dev)
        max_t_prev = torch.full((b_size,), -9999.0, dtype=dtype, device=dev)
        min_t_prev = torch.full((b_size,), 1000.0, dtype=dtype, device=dev)
        max_h_prev = torch.full((b_size,), -9999.0, dtype=dtype, device=dev)
        min_load_t = torch.full((b_size,), WARMUP_MIN_LOAD, dtype=dtype, device=dev)
        true_b = torch.ones((b_size,), dtype=torch.bool, device=dev)

        for day in range(1, max_wu_days + 1):
            if not bool(torch.any(still_warming).item()):
                break
            max_t_day = torch.full((b_size,), -9999.0, dtype=dtype, device=dev)
            min_t_day = torch.full((b_size,), 1000.0, dtype=dtype, device=dev)
            max_h_day = torch.full((b_size,), -9999.0, dtype=dtype, device=dev)

            for step in range(steps_per_day):
                _, ztav_step, sn_h_step = _step_one(
                    wu_db[:, step],
                    wu_w[:, step],
                    wu_pb[:, step],
                    wu_sky[:, step],
                    wu_gain[:, step],
                    begin_envrn=(day == 1 and step == 0),
                    active_b=still_warming,
                )
                max_t_day = torch.maximum(max_t_day, ztav_step)
                min_t_day = torch.minimum(min_t_day, ztav_step)
                max_h_day = torch.maximum(max_h_day, sn_h_step)

            if force_wu_t is not None:
                converged_now = still_warming & (day >= force_wu_t)
                eff_h_day = torch.abs(torch.maximum(max_h_day, min_load_t))
            else:
                pass_max_t = torch.abs(max_t_prev - max_t_day) <= temp_conv_tol
                pass_min_t = torch.abs(min_t_prev - min_t_day) <= temp_conv_tol
                eff_h_day = torch.abs(torch.maximum(max_h_day, min_load_t))
                eff_h_prev = torch.abs(torch.maximum(max_h_prev, min_load_t))
                rel_h_diff = torch.abs((eff_h_day - eff_h_prev) / eff_h_day)
                pass_h = torch.where(
                    max_h_day > 1.0e-4,
                    rel_h_diff <= loads_conv_tol,
                    true_b,
                )
                converged_now = still_warming & (
                    (pass_max_t & pass_min_t & pass_h & (day >= wu_min_days_t))
                    | (day >= wu_max_days_t)
                )

            day_t = torch.full((b_size,), day, dtype=torch.int32, device=dev)
            warmup_days = torch.where(converged_now, day_t, warmup_days)
            still_warming = still_warming & (~converged_now)

            max_t_prev = torch.where(still_warming, max_t_day, max_t_prev)
            min_t_prev = torch.where(still_warming, min_t_day, min_t_prev)
            max_h_prev = torch.where(still_warming, eff_h_day, max_h_prev)

        hourly_heating_j = torch.zeros((b_size, n_hours), dtype=dtype, device=dev)
        z_temp_rec = (
            torch.empty((b_size, n_run_steps), dtype=dtype, device=dev)
            if record_zone_temp
            else None
        )
        z_mean_rec = (
            torch.empty((b_size, n_run_steps), dtype=dtype, device=dev)
            if record_zone_temp
            else None
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
                capture_step_idx=step,
            )
            hourly_heating_j[:, step // sph] += heat_j
            if z_temp_rec is not None and z_mean_rec is not None:
                z_temp_rec[:, step] = t_mat
                z_mean_rec[:, step] = ztav_step

    hourly_np = _to_f64_numpy(hourly_heating_j)
    annual_kwh = np.sum(hourly_np, axis=1, dtype=np.float64) / 3.6e6
    warmup_np = warmup_days.detach().cpu().numpy().astype(np.int32, copy=False)
    z_temp_np = _to_f64_numpy(z_temp_rec) if z_temp_rec is not None else None
    z_mean_np = _to_f64_numpy(z_mean_rec) if z_mean_rec is not None else None

    return SimulationResult(
        cell_ids=list(batch.cell_ids),
        hourly_heating_j=hourly_np,
        annual_heating_kwh=annual_kwh,
        warmup_days=warmup_np,
        zone_air_temp_c=z_temp_np,
        zone_mean_air_temp_c=z_mean_np,
    )
