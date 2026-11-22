from typing import Any

import numpy as np

ITER_DAMP_CONST: float = 5.0
ITERS_REEVAL_CONV_COEFF: int = 30
MAX_INSIDE_SURF_ITERS: int = 500
MAX_ALLOWED_DEL_TEMP: float = 0.002


def calc_osc_outside_temp(
    t_zone: Any,
    t_out_surf_air: Any,
    c_const: Any,
    t_const: Any,
    c_out: Any,
    c_zone: Any,
    xp: Any = np,
) -> Any:
    """HeatBalanceSurfaceManager.cc::CalcHeatBalanceOutsideSurf"""
    return c_zone * t_zone + c_out * t_out_surf_air + c_const * t_const


def calc_outdoors_outside_temp(
    t_zone: Any,
    t_out_surf_air: Any,
    t_sky: Any,
    t_ground_site: Any,
    t_in_prev: Any,
    ctf_out0: Any,
    ctf_cross0: Any,
    ctf_in0: Any,
    ctf_const_out: Any,
    ctf_const_in: Any,
    h_c_ext: Any,
    h_air_ext: Any,
    h_sky_ext: Any,
    h_grd_ext: Any,
    h_conv_in: Any,
    q_rad_net_lw_in: Any,
    xp: Any = np,
) -> Any:
    """HeatBalanceSurfaceManager.cc::CalcOutsideSurfTemp"""
    ext_num = (
        -ctf_const_out
        + (h_c_ext + h_air_ext) * t_out_surf_air
        + h_sky_ext * t_sky
        + h_grd_ext * t_ground_site
    )
    ext_den = ctf_out0 + h_c_ext + h_air_ext + h_sky_ext + h_grd_ext

    safe_in_den = xp.maximum(ctf_in0 + h_conv_in, 1.0e-12)
    f1 = ctf_cross0 / safe_in_den
    quick_num = ext_num + f1 * (ctf_const_in + h_conv_in * t_zone + q_rad_net_lw_in)
    quick_den = ext_den - f1 * ctf_cross0

    slow_num = ext_num + ctf_cross0 * t_in_prev
    slow_den = ext_den

    is_quick = ctf_cross0 > 0.01
    num = xp.where(is_quick, quick_num, slow_num)
    den = xp.where(is_quick, quick_den, slow_den)
    return num / xp.where(den == 0.0, 1.0, den)


def calc_ctf_const_parts(
    t_out_hist: Any,
    t_in_hist: Any,
    q_out_hist: Any,
    q_in_hist: Any,
    ctf_out_tail: Any,
    ctf_cross_tail: Any,
    ctf_in_tail: Any,
    ctf_flux_tail: Any,
    xp: Any = np,
) -> tuple[Any, Any]:
    """HeatBalanceSurfaceManager.cc::InitSurfaceHeatBalance"""
    const_in = xp.sum(
        ctf_cross_tail * t_out_hist
        - ctf_in_tail * t_in_hist
        + ctf_flux_tail * q_in_hist,
        axis=-1,
    )
    const_out = xp.sum(
        ctf_out_tail * t_out_hist
        - ctf_cross_tail * t_in_hist
        + ctf_flux_tail * q_out_hist,
        axis=-1,
    )
    return const_in, const_out


def calc_inside_surface_step(
    t_in_old: Any,
    t_out_curr: Any,
    t_zone: Any,
    h_conv_in: Any,
    q_rad_net_lw_in: Any,
    ctf_in0: Any,
    ctf_cross0: Any,
    ctf_const_in: Any,
    is_adiabatic: Any,
    iter_damp_const: float = ITER_DAMP_CONST,
    xp: Any = np,
) -> Any:
    """HeatBalanceSurfaceManager.cc::CalcHeatBalanceInsideSurf2"""
    temp_term = ctf_const_in + h_conv_in * t_zone + q_rad_net_lw_in
    num_ad = temp_term + iter_damp_const * t_in_old
    den_ad = ctf_in0 - ctf_cross0 + h_conv_in + iter_damp_const

    num_std = temp_term + iter_damp_const * t_in_old + ctf_cross0 * t_out_curr
    den_std = ctf_in0 + h_conv_in + iter_damp_const

    num = xp.where(is_adiabatic, num_ad, num_std)
    den = xp.where(is_adiabatic, den_ad, den_std)
    return num / xp.where(den == 0.0, 1.0, den)


def update_ctf_histories(
    t_out_curr: Any,
    t_in_curr: Any,
    ctf_const_in: Any,
    ctf_const_out: Any,
    ctf_out0: Any,
    ctf_cross0: Any,
    ctf_in0: Any,
    t_out_hist: Any,
    t_in_hist: Any,
    q_out_hist: Any,
    q_in_hist: Any,
    xp: Any = np,
) -> tuple[Any, Any, Any, Any]:
    """HeatBalanceSurfaceManager.cc::UpdateThermalHistories"""
    q_in_curr = t_out_curr * ctf_cross0 - t_in_curr * ctf_in0 + ctf_const_in
    q_out_curr = t_out_curr * ctf_out0 - t_in_curr * ctf_cross0 + ctf_const_out

    new_t_out = xp.concatenate([t_out_curr[..., None], t_out_hist[..., :-1]], axis=-1)
    new_t_in = xp.concatenate([t_in_curr[..., None], t_in_hist[..., :-1]], axis=-1)
    new_q_out = xp.concatenate([q_out_curr[..., None], q_out_hist[..., :-1]], axis=-1)
    new_q_in = xp.concatenate([q_in_curr[..., None], q_in_hist[..., :-1]], axis=-1)
    return new_t_out, new_t_in, new_q_out, new_q_in
