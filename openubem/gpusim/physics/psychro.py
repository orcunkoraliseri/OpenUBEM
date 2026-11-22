from typing import Any

KELVIN_CONV = 273.15
TRIPLE_POINT_WATER_K = 273.16
STEFAN_BOLTZMANN = 5.6697e-8


def psy_rho_air_fn_pb_tdb_w(pb: Any, tdb: Any, dw: Any, xp: Any) -> Any:
    """Psychrometrics.hh::PsyRhoAirFnPbTdbW"""
    w = xp.maximum(dw, 1.0e-5)
    return pb / (287.0 * (tdb + KELVIN_CONV) * (1.0 + 1.6077687 * w))


def psy_cp_air_fn_w(dw: Any, xp: Any) -> Any:
    """Psychrometrics.hh::PsyCpAirFnW"""
    w = xp.maximum(dw, 1.0e-5)
    return 1.00484e3 + w * 1.85895e3


def psy_h_fn_tdb_w(tdb: Any, dw: Any, xp: Any) -> Any:
    """Psychrometrics.hh::PsyHFnTdbW"""
    w = xp.maximum(dw, 1.0e-5)
    return 1.00484e3 * tdb + w * (2.50094e6 + 1.85895e3 * tdb)


def psy_tdb_fn_h_w(h: Any, dw: Any, xp: Any) -> Any:
    """Psychrometrics.hh::PsyTdbFnHW"""
    w = xp.maximum(dw, 1.0e-5)
    return (h - 2.50094e6 * w) / (1.00484e3 + 1.85895e3 * w)


def psy_psat_fn_temp(temp_c: Any, xp: Any) -> Any:
    """Psychrometrics.cc::PsyPsatFnTemp"""
    tkel = xp.asarray(temp_c, dtype=xp.float64) + KELVIN_CONV
    tkel_safe = xp.clip(tkel, 173.15, 473.15)
    log_t = xp.log(tkel_safe)

    ice_exp = (
        -5674.5359 / tkel_safe
        + 6.3925247
        + tkel_safe
        * (
            -0.9677843e-2
            + tkel_safe
            * (0.62215701e-6 + tkel_safe * (0.20747825e-8 - 0.9484024e-12 * tkel_safe))
        )
        + 4.1635019 * log_t
    )
    liq_exp = (
        -5800.2206 / tkel_safe
        + 1.3914993
        + tkel_safe
        * (
            -0.048640239
            + tkel_safe * (0.41764768e-4 - 0.14452093e-7 * tkel_safe)
        )
        + 6.5459673 * log_t
    )

    psat_ice = xp.exp(ice_exp)
    psat_liq = xp.exp(liq_exp)
    psat = xp.where(tkel < TRIPLE_POINT_WATER_K, psat_ice, psat_liq)
    psat = xp.where(tkel < 173.15, 0.001405102123874164, psat)
    psat = xp.where(tkel > 473.15, 1555073.745636215, psat)
    return psat


def psy_w_fn_tdp_pb(tdp: Any, pb: Any, xp: Any) -> Any:
    """Psychrometrics.hh::PsyWFnTdpPb"""
    tdp_adj = xp.asarray(tdp, dtype=xp.float64)
    pb_arr = xp.asarray(pb, dtype=xp.float64)
    pdew = psy_psat_fn_temp(tdp_adj, xp)
    while bool(xp.any(pdew >= pb_arr)):
        tdp_adj = xp.where(pdew >= pb_arr, tdp_adj - 1.0, tdp_adj)
        pdew = psy_psat_fn_temp(tdp_adj, xp)
    return pdew * 0.62198 / (pb_arr - pdew)


def psy_w_fn_tdb_rh_pb(tdb: Any, rh: Any, pb: Any, xp: Any) -> Any:
    """Psychrometrics.hh::PsyWFnTdbRhPb"""
    pdew = rh * psy_psat_fn_temp(tdb, xp)
    w = pdew * 0.62198 / xp.maximum(pb - pdew, 1000.0)
    return xp.maximum(w, 1.0e-5)
