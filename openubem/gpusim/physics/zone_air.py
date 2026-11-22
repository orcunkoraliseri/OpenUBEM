from typing import Any

import numpy as np

from openubem.gpusim.physics.psychro import (
    psy_cp_air_fn_w,
    psy_h_fn_tdb_w,
    psy_rho_air_fn_pb_tdb_w,
    psy_w_fn_tdb_rh_pb,
)

SMALL_TEMP_DIFF: float = 1.0e-5
VERY_SMALL_MASS_FLOW: float = 1.0e-12


def calc_ventilation_mcp(
    vent_vol_flow: Any,
    out_dry_bulb_zone: Any,
    out_hum_rat: Any,
    baro_press: Any,
    xp: Any = np,
) -> tuple[Any, Any, Any]:
    """ZoneEquipmentManager.cc::CalcAirFlowSimple"""
    air_density = psy_rho_air_fn_pb_tdb_w(
        baro_press, out_dry_bulb_zone, out_hum_rat, xp=xp
    )
    cp_air = psy_cp_air_fn_w(out_hum_rat, xp=xp)
    vvf = xp.maximum(vent_vol_flow, 0.0)
    mcpv = xp.maximum(vvf * air_density * cp_air, 0.0)
    vamfl = mcpv / cp_air
    mcptv = mcpv * out_dry_bulb_zone
    return mcpv, vamfl, mcptv


def predict_zone_load(
    t_zone_mat: Any,
    hum_rat: Any,
    baro_press: Any,
    zone_vol: Any,
    dt_sys_sec: Any,
    ztm: Any,
    sum_ha: Any,
    sum_hat_surf: Any,
    sum_mcp: Any,
    sum_mcpt: Any,
    sum_int_gain: Any,
    heat_setpoint: Any,
    cool_setpoint: Any,
    xp: Any = np,
) -> tuple[Any, Any, Any]:
    """ZoneTempPredictorCorrector.cc::predictSystemLoad"""
    rho = psy_rho_air_fn_pb_tdb_w(baro_press, t_zone_mat, hum_rat, xp=xp)
    cp = psy_cp_air_fn_w(hum_rat, xp=xp)
    air_power_cap = zone_vol * rho * cp / dt_sys_sec

    temp_dep_coef = sum_ha + sum_mcp
    temp_ind_coef = sum_int_gain + sum_hat_surf + sum_mcpt
    temp_hist_term = air_power_cap * (
        3.0 * ztm[..., 0] - 1.5 * ztm[..., 1] + (1.0 / 3.0) * ztm[..., 2]
    )
    temp_dep_zn_ld = (11.0 / 6.0) * air_power_cap + temp_dep_coef
    temp_ind_zn_ld = temp_hist_term + temp_ind_coef

    load_to_heat = temp_dep_zn_ld * heat_setpoint - temp_ind_zn_ld
    load_to_cool = temp_dep_zn_ld * cool_setpoint - temp_ind_zn_ld
    return load_to_heat, load_to_cool, air_power_cap


def calc_ideal_loads_heating(
    q_heat_req: Any,
    t_zone_node: Any,
    w_zone_node: Any,
    zone_hum_rat: Any,
    baro_press: Any,
    max_heat_supply_temp: Any,
    heat_on: Any = True,
    xp: Any = np,
) -> tuple[Any, Any, Any, Any, Any]:
    """PurchasedAirManager.cc::CalcPurchAirLoads"""
    is_heating = heat_on & (q_heat_req > 0.0)
    cp_air = psy_cp_air_fn_w(zone_hum_rat, xp=xp)
    delta_t = max_heat_supply_temp - t_zone_node

    can_heat = is_heating & (delta_t > SMALL_TEMP_DIFF)
    safe_dt = xp.where(can_heat, delta_t, 1.0)
    m_dot_raw = xp.where(can_heat, q_heat_req / (cp_air * safe_dt), 0.0)
    m_dot_sup = xp.where(m_dot_raw <= VERY_SMALL_MASS_FLOW, 0.0, m_dot_raw)

    active = m_dot_sup > 0.0
    safe_mdot = xp.where(active, m_dot_sup, 1.0)
    t_sup_calc = xp.where(
        active,
        q_heat_req / (cp_air * safe_mdot) + t_zone_node,
        t_zone_node,
    )
    t_sup = xp.minimum(t_sup_calc, max_heat_supply_temp)
    t_sup = xp.maximum(t_sup, t_zone_node)

    w_sat = psy_w_fn_tdb_rh_pb(t_sup, 1.0, baro_press, xp=xp)
    w_sup = xp.where(active, xp.minimum(w_zone_node, w_sat), w_zone_node)

    h_sup = psy_h_fn_tdb_w(t_sup, w_sup, xp=xp)
    h_zone = psy_h_fn_tdb_w(t_zone_node, w_zone_node, xp=xp)

    sen_out = xp.where(active, m_dot_sup * cp_air * (t_sup - t_zone_node), 0.0)
    lat_out = xp.where(active, m_dot_sup * (h_sup - h_zone) - sen_out, 0.0)

    sen_heat_rate = xp.maximum(sen_out, 0.0)
    tot_heat_rate = sen_heat_rate + xp.maximum(lat_out, 0.0)
    return m_dot_sup, t_sup, w_sup, sen_heat_rate, tot_heat_rate


def correct_zone_air_temp_and_humrat(
    t_zone_mat: Any,
    hum_rat: Any,
    baro_press: Any,
    zone_vol: Any,
    dt_sys_sec: Any,
    ztm: Any,
    w_prev: Any,
    sum_ha: Any,
    sum_hat_surf: Any,
    sum_mcp: Any,
    sum_mcpt: Any,
    sum_int_gain: Any,
    m_dot_sup: Any,
    t_sup: Any,
    w_sup: Any,
    vamfl: Any,
    out_hum_rat: Any,
    xp: Any = np,
) -> tuple[Any, Any]:
    """ZoneTempPredictorCorrector.cc::correctAirTemp"""
    rho = psy_rho_air_fn_pb_tdb_w(baro_press, t_zone_mat, hum_rat, xp=xp)
    cp = psy_cp_air_fn_w(hum_rat, xp=xp)
    air_power_cap = zone_vol * rho * cp / dt_sys_sec

    sum_sys_mcp = m_dot_sup * cp
    sum_sys_mcpt = sum_sys_mcp * t_sup

    temp_dep_coef = sum_ha + sum_mcp + sum_sys_mcp
    temp_ind_coef = sum_int_gain + sum_hat_surf + sum_mcpt + sum_sys_mcpt
    temp_hist = air_power_cap * (
        3.0 * ztm[..., 0] - 1.5 * ztm[..., 1] + (1.0 / 3.0) * ztm[..., 2]
    )
    zt_new = (temp_ind_coef + temp_hist) / (
        (11.0 / 6.0) * air_power_cap + temp_dep_coef
    )

    rho_w = psy_rho_air_fn_pb_tdb_w(baro_press, zt_new, hum_rat, xp=xp)
    c_w = rho_w * zone_vol / dt_sys_sec
    b_w = vamfl * out_hum_rat + m_dot_sup * w_sup
    a_w = m_dot_sup + vamfl
    w_hist = c_w * (
        3.0 * w_prev[..., 0] - 1.5 * w_prev[..., 1] + (1.0 / 3.0) * w_prev[..., 2]
    )
    w_new = (b_w + w_hist) / ((11.0 / 6.0) * c_w + a_w)
    w_new = xp.maximum(w_new, 0.0)
    w_sat = psy_w_fn_tdb_rh_pb(zt_new, 1.0, baro_press, xp=xp)
    w_new = xp.minimum(w_new, w_sat)
    return zt_new, w_new


def down_interpolate_4_history_values(
    old_dt: float,
    new_dt: float,
    old_vals: Any,
    xp: Any = np,
) -> Any:
    """ZoneTempPredictorCorrector.cc::DownInterpolate4HistoryValues"""
    ratio = old_dt / new_dt
    t_steps = xp.asarray([1.0, 2.0, 3.0, 4.0], dtype=xp.float64) * new_dt
    v0 = old_vals[..., 0]
    v1 = old_vals[..., 1]
    v2 = old_vals[..., 2]

    if abs(ratio - 2.0) < 0.01:
        d10 = v1 - v0
        d21 = v2 - v1
        n0 = v0 + d10 * (t_steps[0] / old_dt)
        n1 = v0 + d10 * (t_steps[1] / old_dt)
        n2 = v1 + d21 * ((t_steps[2] - old_dt) / old_dt)
        n3 = v1 + d21 * ((t_steps[3] - old_dt) / old_dt)
    elif abs(ratio - 3.0) < 0.01:
        d10 = v1 - v0
        d21 = (v2 - v1) / old_dt
        n0 = v0 + d10 * (t_steps[0] / old_dt)
        n1 = v0 + d10 * (t_steps[1] / old_dt)
        n2 = v0 + d10 * (t_steps[2] / old_dt)
        n3 = v1 + d21 * ((t_steps[3] - old_dt) / old_dt)
    else:
        d10 = v1 - v0
        n0 = v0 + d10 * (t_steps[0] / old_dt)
        n1 = v0 + d10 * (t_steps[1] / old_dt)
        n2 = v0 + d10 * (t_steps[2] / old_dt)
        n3 = v0 + d10 * (t_steps[3] / old_dt)

    return xp.stack([n0, n1, n2, n3], axis=-1)
