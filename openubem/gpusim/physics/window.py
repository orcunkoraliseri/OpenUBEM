from typing import Any

import numpy as np

from openubem.gpusim.physics.convection import calc_iso15099_window_int_conv_coeff
from openubem.gpusim.physics.psychro import KELVIN_CONV, STEFAN_BOLTZMANN

WINDOW_MAX_ITER: int = 100
WINDOW_ERR_TOL: float = 0.02


def simple_glazing_layer_conductance(u_factor: Any, xp: Any = np) -> Any:
    """HeatBalanceManager.cc::ConvertSimpleGlazingSystem"""
    safe_u = xp.maximum(u_factor, 1.0e-6)
    r_iw = xp.where(
        safe_u < 5.85,
        1.0 / (0.359073 * xp.log(safe_u) + 6.949915),
        1.0 / (1.788041 * safe_u - 2.886625),
    )
    r_ow = 1.0 / (0.025342 * safe_u + 29.163853)
    r_lw = xp.maximum((1.0 / safe_u) - r_iw - r_ow, 0.001)
    return 1.0 / r_lw


def calc_window_outside_ir(
    t_out_k: Any,
    t_sky_k: Any,
    vf_sky_ir: Any,
    vf_ground_ir: Any,
    air_sky_split: Any,
    xp: Any = np,
) -> Any:
    """WindowManager.cc::CalcWindowHeatBalanceInternalRoutines"""
    eb_out = STEFAN_BOLTZMANN * (t_out_k**4)
    eb_sky = STEFAN_BOLTZMANN * (t_sky_k**4)
    return (
        vf_sky_ir * (air_sky_split * eb_sky + (1.0 - air_sky_split) * eb_out)
        + vf_ground_ir * eb_out
    )


def starting_window_temps(
    t_in_k: Any,
    t_out_k: Any,
    h_in: Any,
    h_out: Any,
    scon: Any,
    xp: Any = np,
) -> tuple[Any, Any]:
    """WindowManager.cc::StartingWindowTemps"""
    hrad = 5.3
    r1 = 1.0 / (h_out + hrad)
    r2 = 1.0 / xp.maximum(scon, 1.0e-6)
    r3 = 1.0 / (h_in + hrad)
    r_tot = r1 + r2 + r3
    temdiff = t_in_k - t_out_k
    temdiff = xp.where(xp.abs(temdiff) < 0.5, 2.0, temdiff)
    theta1 = (r1 / r_tot) * temdiff + t_out_k
    theta2 = ((r1 + r2) / r_tot) * temdiff + t_out_k
    return theta1, theta2


def solve_simple_window(
    t_in_c: Any,
    t_out_c: Any,
    t_sky_c: Any,
    hum_rat: Any,
    baro_press: Any,
    h_out: Any,
    rmir: Any,
    scon: Any,
    eps_out: Any,
    eps_in: Any,
    vf_sky_ir: Any,
    vf_ground_ir: Any,
    air_sky_split: Any,
    height: Any,
    tilt_deg: Any,
    sin_tilt: Any,
    h_min: Any,
    theta1_init: Any,
    theta2_init: Any,
    win_mask: Any,
    xp: Any = np,
) -> tuple[Any, Any, Any, Any, Any]:
    """WindowManager.cc::SolveForWindowTemperatures"""
    t_in_k = t_in_c + KELVIN_CONV
    t_out_k = t_out_c + KELVIN_CONV
    t_sky_k = t_sky_c + KELVIN_CONV
    out_ir = calc_window_outside_ir(
        t_out_k, t_sky_k, vf_sky_ir, vf_ground_ir, air_sky_split, xp=xp
    )

    theta1 = theta1_init
    theta2 = theta2_init
    h_in = xp.full_like(theta1, 3.0)
    active = win_mask

    for it in range(WINDOW_MAX_ITER):
        if not bool(xp.any(active)):
            break
        hr1 = eps_out * STEFAN_BOLTZMANN * (theta1 * theta1 * theta1)
        hr2 = eps_in * STEFAN_BOLTZMANN * (theta2 * theta2 * theta2)

        h_in_new = calc_iso15099_window_int_conv_coeff(
            theta2 - KELVIN_CONV,
            t_in_c,
            hum_rat,
            baro_press,
            height,
            tilt_deg,
            sin_tilt,
            h_min=h_min,
            xp=xp,
        )
        h_in = xp.where(active, h_in_new, h_in)

        a11 = hr1 + scon + h_out
        a22 = hr2 + scon + h_in
        b1 = out_ir * eps_out + h_out * t_out_k
        b2 = rmir * eps_in + h_in * t_in_k

        det = a11 * a22 - scon * scon
        safe_det = xp.where(active, det, 1.0)
        sol1 = (a22 * b1 + scon * b2) / safe_det
        sol2 = (scon * b1 + a11 * b2) / safe_det

        iter_idx = it + 1
        w_old = 0.5 if iter_idx < (WINDOW_MAX_ITER // 4) else 0.75
        w_new = 1.0 - w_old

        new_theta1 = w_old * theta1 + w_new * sol1
        new_theta2 = w_old * theta2 + w_new * sol2

        err = 0.5 * (xp.abs(new_theta1 - theta1) + xp.abs(new_theta2 - theta2))
        theta1 = xp.where(active, new_theta1, theta1)
        theta2 = xp.where(active, new_theta2, theta2)
        active = active & (err > WINDOW_ERR_TOL)

    t_out_surf_c = theta1 - KELVIN_CONV
    t_in_surf_c = theta2 - KELVIN_CONV
    q_conv_per_area = h_in * (theta2 - t_in_k)
    return t_in_surf_c, t_out_surf_c, h_in, q_conv_per_area, (theta1, theta2)
