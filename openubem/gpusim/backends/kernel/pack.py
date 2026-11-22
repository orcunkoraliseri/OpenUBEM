from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from openubem.gpusim.backends.numpy_ref import SURF_INITIAL_TEMP, ZONE_INITIAL_TEMP
from openubem.gpusim.compile import (
    BOUND_DOOR,
    BOUND_INTMASS,
    BOUND_OSC,
    BOUND_OUTDOORS,
    BOUND_WINDOW,
    BatchSpec,
)
from openubem.gpusim.ctf import CtfCoefficients, load_ctf_from_eio
from openubem.gpusim.physics.convection import out_dry_bulb_temp_at
from openubem.gpusim.physics.psychro import KELVIN_CONV, STEFAN_BOLTZMANN
from openubem.gpusim.physics.window import simple_glazing_layer_conductance
from openubem.gpusim.viewfactors import compute_batch_view_factors
from openubem.gpusim.weather import WeatherSeries

T_REF_C: float = 20.0
T_REF_K: float = KELVIN_CONV + T_REF_C
MAX_SURF: int = 16
MAX_CTF_HIST: int = 8

FLAG_SURF_MASK: int = 1
FLAG_IS_OSC: int = 2
FLAG_IS_OUTDOORS_OP: int = 4
FLAG_IS_INTMASS: int = 8
FLAG_IS_WINDOW: int = 16
FLAG_IS_NON_WINDOW: int = 32

BF_ZONE_VOLUME: int = 0
BF_ZONE_FLOOR_AREA: int = 1
BF_ZONE_CENTROID_Z: int = 2
BF_ZONE_LAPSE_OFFSET: int = 3
BF_VENT_ACH: int = 4
BF_VENT_FLOW_M3S: int = 5
BF_HEAT_SP_DT: int = 6
BF_COOL_SP_DT: int = 7
BF_MAX_HEAT_SUP_DT: int = 8
BF_MAX_HEAT_SUP_HUMRAT: int = 9
BF_H_CONV_MIN: int = 10
BF_H_CONV_MAX: int = 11
BF_LOADS_CONV_TOL: int = 12
BF_TEMP_CONV_TOL: int = 13
BF_SITE_ELEVATION: int = 14
BF_COUNT: int = 15

BI_SITE_IDX: int = 0
BI_WU_MIN_DAYS: int = 1
BI_WU_MAX_DAYS: int = 2
BI_NUM_SURF: int = 3
BI_HAS_WINDOW: int = 4
BI_COUNT: int = 5

SS_AREA: int = 0
SS_COS_TILT: int = 1
SS_SIN_TILT: int = 2
SS_TILT_DEG: int = 3
SS_CENTROID_Z: int = 4
SS_LAPSE_OFFSET: int = 5
SS_U_VALUE: int = 6
SS_OSC_C_CONST: int = 7
SS_OSC_T_CONST_DT: int = 8
SS_OSC_C_OUT: int = 9
SS_OSC_C_ZONE: int = 10
SS_OSC_SHIFT: int = 11
SS_VF_SKY_IR: int = 12
SS_VF_GROUND_IR: int = 13
SS_AIR_SKY_SPLIT: int = 14
SS_EPS_IN: int = 15
SS_EPS_OUT: int = 16
SS_HEIGHT: int = 17
SS_SCON_WIN: int = 18
SS_CTF_OUT0: int = 19
SS_CTF_CROSS0: int = 20
SS_CTF_IN0: int = 21
SS_COUNT: int = 22

WF_DT_DB: int = 0
WF_HUM_RAT: int = 1
WF_BARO_PRESS: int = 2
WF_DT_SKY: int = 3
WF_COUNT: int = 4

ZS_T_MAT_DT: int = 0
ZS_W_ZONE: int = 1
ZS_W_ZONE_AVG: int = 2
ZS_XMAT0: int = 3
ZS_XMAT1: int = 4
ZS_XMAT2: int = 5
ZS_XMAT3: int = 6
ZS_DSXMAT0: int = 7
ZS_DSXMAT1: int = 8
ZS_DSXMAT2: int = 9
ZS_DSXMAT3: int = 10
ZS_W_PREV0: int = 11
ZS_W_PREV1: int = 12
ZS_W_PREV2: int = 13
ZS_W_PREV3: int = 14
ZS_DSW_PREV0: int = 15
ZS_DSW_PREV1: int = 16
ZS_DSW_PREV2: int = 17
ZS_DSW_PREV3: int = 18
ZS_COUNT: int = 19

ST_SURF_DT_IN: int = 0
ST_SURF_DT_OUT: int = 1
ST_DTH1_WIN: int = 2
ST_DTH2_WIN: int = 3
ST_COUNT: int = 4

CH_T_OUT_DT: int = 0
CH_T_IN_DT: int = 1
CH_Q_OUT: int = 2
CH_Q_IN: int = 3
CH_COUNT: int = 4

WU_STAT_MAX_T_DT: int = 0
WU_STAT_MIN_T_DT: int = 1
WU_STAT_MAX_H_RATE: int = 2
WU_STAT_COUNT: int = 3


@dataclass
class PackedBatch:
    """Structure-of-arrays float32 and int32 host buffers for Stage C kernels.

    Attributes:
        batch_size: Number of buildings ``B``.
        max_surfaces: Padded surface count ``S``.
        n_sites: Number of distinct weather sites ``K``.
        n_ctf_hist: Internal-mass CTF history order ``M``.
        steps_per_hour: Zone timesteps per hour.
        n_run_steps: Number of run-period timesteps.
        n_wu_steps: Number of warm-up day timesteps.
        n_hours: Number of hourly output bins.
        bldg_f: Building float static parameters ``[BF_COUNT, B]``.
        bldg_i: Building int static parameters ``[BI_COUNT, B]``.
        surf_f: Surface float static parameters ``[SS_COUNT, S, B]``.
        surf_flags: Packed surface bit flags ``[S, B]``.
        script_f_sigma: Interior radiation exchange matrix ``[S, S, B]``.
        ctf_vec: Sum-preserving CTF coefficients and T_ref biases ``[4*M + 2]``.
        weather_run: Distinct-site run-period weather ``[WF_COUNT, T_run, K]``.
        weather_wu: Distinct-site warm-up weather ``[WF_COUNT, T_wu, K]``.
        sched_gain_w: Hourly internal gains ``[8760, B]``.
        state_zone_f: Mutable zone scalar/history state ``[ZS_COUNT, B]``.
        state_num_sys_last: Mutable previous sub-step counts ``[B]``.
        state_surf_f: Mutable surface temperatures ``[ST_COUNT, S, B]``.
        state_ctf_hist: Mutable CTF histories ``[CH_COUNT, M, S, B]``.
        hourly_heating_j: Output hourly heating buffer ``[n_hours, B]``.
        wu_stats: Output warm-up daily min/max buffer ``[WU_STAT_COUNT, B]``.
    """

    batch_size: int
    max_surfaces: int
    n_sites: int
    n_ctf_hist: int
    steps_per_hour: int
    n_run_steps: int
    n_wu_steps: int
    n_hours: int
    bldg_f: np.ndarray
    bldg_i: np.ndarray
    surf_f: np.ndarray
    surf_flags: np.ndarray
    script_f_sigma: np.ndarray
    ctf_vec: np.ndarray
    weather_run: np.ndarray
    weather_wu: np.ndarray
    sched_gain_w: np.ndarray
    state_zone_f: np.ndarray
    state_num_sys_last: np.ndarray
    state_surf_f: np.ndarray
    state_ctf_hist: np.ndarray
    hourly_heating_j: np.ndarray
    wu_stats: np.ndarray

    def total_bytes(self) -> int:
        """Return total packed buffer bytes across all host NumPy arrays.

        Returns:
            Sum of ``nbytes`` across every array buffer in this container.
        """
        arrays = (
            self.bldg_f,
            self.bldg_i,
            self.surf_f,
            self.surf_flags,
            self.script_f_sigma,
            self.ctf_vec,
            self.weather_run,
            self.weather_wu,
            self.sched_gain_w,
            self.state_zone_f,
            self.state_num_sys_last,
            self.state_surf_f,
            self.state_ctf_hist,
            self.hourly_heating_j,
            self.wu_stats,
        )
        return sum(int(arr.nbytes) for arr in arrays)

    def building_bytes(self) -> int:
        """Return packed bytes that scale per building (excluding shared weather).

        Returns:
            Sum of ``nbytes`` across per-building static, schedule, state, and
            hourly output arrays.
        """
        per_bldg_arrays = (
            self.bldg_f,
            self.bldg_i,
            self.surf_f,
            self.surf_flags,
            self.script_f_sigma,
            self.sched_gain_w,
            self.state_zone_f,
            self.state_num_sys_last,
            self.state_surf_f,
            self.state_ctf_hist,
            self.hourly_heating_j,
            self.wu_stats,
        )
        return sum(int(arr.nbytes) for arr in per_bldg_arrays)

    def bytes_per_building(self) -> float:
        """Return total packed bytes divided by ``batch_size``.

        Returns:
            Amortized packed buffer size per building in bytes.
        """
        return float(self.total_bytes()) / float(self.batch_size)


def deduplicate_weather(
    weather: WeatherSeries | Sequence[WeatherSeries],
    batch_size: int,
) -> tuple[list[WeatherSeries], np.ndarray]:
    """Deduplicate weather inputs into unique sites and a per-building index.

    Args:
        weather: Shared ``WeatherSeries`` or sequence of length ``batch_size``.
        batch_size: Expected number of buildings in the batch.

    Returns:
        Tuple ``(weather_by_site, site_index)`` with int32 ``site_index`` ``[B]``.

    Raises:
        ValueError: If sequence length does not match ``batch_size``.
    """
    if isinstance(weather, WeatherSeries):
        return [weather], np.zeros(batch_size, dtype=np.int32)
    if len(weather) != batch_size:
        raise ValueError(f"Expected {batch_size} WeatherSeries, got {len(weather)}")
    by_site: list[WeatherSeries] = []
    seen_ids: dict[int, int] = {}
    site_idx = np.empty(batch_size, dtype=np.int32)
    for b_idx, series in enumerate(weather):
        key = id(series)
        mapped = seen_ids.get(key)
        if mapped is None:
            mapped = len(by_site)
            seen_ids[key] = mapped
            by_site.append(series)
        site_idx[b_idx] = mapped
    return by_site, site_idx


def _round_ctf_preserve_sum(arr: np.ndarray) -> np.ndarray:
    """Round a 1D float64 CTF vector to float32 while preserving its float64 sum.

    Args:
        arr: Input 1D float64 coefficient vector.

    Returns:
        Float32 array matching element values within ``5e-7`` relative error and
        minimizing sum drift.
    """
    target = float(np.sum(arr, dtype=np.float64))
    base = arr.astype(np.float32)
    best = base.copy()
    best_err = abs(float(np.sum(base, dtype=np.float64)) - target)
    base_sum = float(np.sum(base, dtype=np.float64))
    for idx in range(len(arr)):
        other = base_sum - float(base[idx])
        cand_val = np.float32(target - other)
        orig_val = float(arr[idx])
        rel = abs(float(cand_val) - orig_val) / max(abs(orig_val), 1.0e-12)
        if rel > 5.0e-7:
            continue
        cand = base.copy()
        cand[idx] = cand_val
        err = abs(float(np.sum(cand, dtype=np.float64)) - target)
        if err < best_err:
            best = cand
            best_err = err
    return best


def _pack_ctf_arrays(
    ctf: CtfCoefficients,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float]:
    """Round CTF arrays preserving sums and compute T_ref zero-bias terms.

    Args:
        ctf: Loaded float64 internal-mass ``CtfCoefficients``.

    Returns:
        Tuple ``(out_f32, cross_f32, in_f32, flux_f32, bias_in, bias_out)``.
    """
    out_f32 = _round_ctf_preserve_sum(ctf.outside)
    cross_f32 = _round_ctf_preserve_sum(ctf.cross)
    in_f32 = _round_ctf_preserve_sum(ctf.inside)
    flux_f32 = _round_ctf_preserve_sum(ctf.flux)
    sum_out = float(np.sum(ctf.outside, dtype=np.float64))
    sum_cross = float(np.sum(ctf.cross, dtype=np.float64))
    sum_in = float(np.sum(ctf.inside, dtype=np.float64))
    bias_in = (sum_cross - sum_in) * T_REF_C
    bias_out = (sum_out - sum_cross) * T_REF_C
    return out_f32, cross_f32, in_f32, flux_f32, bias_in, bias_out


def pack(
    batch: BatchSpec,
    weather_by_site: Sequence[WeatherSeries],
    site_index: Sequence[int] | np.ndarray,
    ctf: CtfCoefficients | None = None,
) -> PackedBatch:
    """Pack BatchSpec, per-site weather, and CTF data into Stage C SoA buffers.

    Temperatures are stored as float32 deviations from ``20.0 C`` (or
    ``293.15 K`` for glazing node temperatures). Building and site dimensions
    are placed on the trailing contiguous axis.

    Args:
        batch: Compiled ``BatchSpec`` of shape ``[B, S]``.
        weather_by_site: Sequence of distinct ``WeatherSeries`` objects.
        site_index: Integer weather-site index ``[B]`` into ``weather_by_site``.
        ctf: Optional internal-mass CTF coefficients (defaults to golden ``.eio``).

    Returns:
        ``PackedBatch`` holding all static, weather, schedule, state, and output
        buffers.

    Raises:
        ValueError: If batch sizes, site indices, surface counts, or CTF order
            exceed Stage C kernel limits.
    """
    b_size = int(batch.batch_size)
    n_surf = int(batch.max_surfaces)
    sph = int(batch.steps_per_hour)
    if n_surf > MAX_SURF:
        raise ValueError(f"max_surfaces={n_surf} exceeds MAX_SURF={MAX_SURF}")

    site_idx_arr = np.asarray(site_index, dtype=np.int32).reshape(-1)
    if site_idx_arr.shape != (b_size,):
        raise ValueError(
            f"Expected site_index shape ({b_size},), got {site_idx_arr.shape}"
        )
    n_sites = len(weather_by_site)
    if n_sites == 0:
        raise ValueError("weather_by_site must not be empty")
    if int(np.min(site_idx_arr)) < 0 or int(np.max(site_idx_arr)) >= n_sites:
        raise ValueError("site_index contains out-of-range site indices")

    if ctf is None:
        ctf = load_ctf_from_eio(steps_per_hour=sph)
    n_ctf_hist = int(ctf.num_terms)
    if n_ctf_hist > MAX_CTF_HIST:
        raise ValueError(f"n_ctf_hist={n_ctf_hist} exceeds MAX_CTF_HIST={MAX_CTF_HIST}")

    n_run_steps = int(weather_by_site[0].dry_bulb.shape[0])
    n_wu_steps = int(weather_by_site[0].warmup_dry_bulb.shape[0])
    for w_item in weather_by_site:
        if w_item.steps_per_hour != sph:
            raise ValueError("All WeatherSeries must match batch steps_per_hour")
        if int(w_item.dry_bulb.shape[0]) != n_run_steps:
            raise ValueError("All WeatherSeries must share run-period length")
        if int(w_item.warmup_dry_bulb.shape[0]) != n_wu_steps:
            raise ValueError("All WeatherSeries must share warm-up length")
    n_hours = n_run_steps // sph

    bldg_f = np.zeros((BF_COUNT, b_size), dtype=np.float32)
    bldg_f[BF_ZONE_VOLUME] = batch.zone_volume.astype(np.float32)
    bldg_f[BF_ZONE_FLOOR_AREA] = batch.zone_floor_area.astype(np.float32)
    bldg_f[BF_ZONE_CENTROID_Z] = batch.zone_centroid_z.astype(np.float32)
    zone_lapse = out_dry_bulb_temp_at(
        np.zeros_like(batch.zone_centroid_z), batch.zone_centroid_z, xp=np
    )
    bldg_f[BF_ZONE_LAPSE_OFFSET] = zone_lapse.astype(np.float32)
    bldg_f[BF_VENT_ACH] = batch.zone_vent_ach.astype(np.float32)
    bldg_f[BF_VENT_FLOW_M3S] = batch.zone_vent_flow_m3s.astype(np.float32)
    bldg_f[BF_HEAT_SP_DT] = (batch.zone_heat_setpoint - T_REF_C).astype(np.float32)
    bldg_f[BF_COOL_SP_DT] = (batch.zone_cool_setpoint - T_REF_C).astype(np.float32)
    bldg_f[BF_MAX_HEAT_SUP_DT] = (batch.zone_max_heat_supply_temp - T_REF_C).astype(
        np.float32
    )
    bldg_f[BF_MAX_HEAT_SUP_HUMRAT] = batch.zone_max_heat_supply_humrat.astype(
        np.float32
    )
    bldg_f[BF_H_CONV_MIN] = batch.h_conv_min.astype(np.float32)
    bldg_f[BF_H_CONV_MAX] = batch.h_conv_max.astype(np.float32)
    bldg_f[BF_LOADS_CONV_TOL] = batch.loads_conv_tol.astype(np.float32)
    bldg_f[BF_TEMP_CONV_TOL] = batch.temp_conv_tol.astype(np.float32)
    bldg_f[BF_SITE_ELEVATION] = batch.site_elevation.astype(np.float32)

    surf_mask = batch.surf_mask
    is_osc = (batch.surf_boundary == BOUND_OSC) & surf_mask
    is_outdoors_op = (
        (batch.surf_boundary == BOUND_OUTDOORS) | (batch.surf_boundary == BOUND_DOOR)
    ) & surf_mask
    is_intmass = (batch.surf_boundary == BOUND_INTMASS) & surf_mask
    is_window = (batch.surf_boundary == BOUND_WINDOW) & surf_mask
    is_non_window = surf_mask & (~is_window)

    bldg_i = np.zeros((BI_COUNT, b_size), dtype=np.int32)
    bldg_i[BI_SITE_IDX] = site_idx_arr
    bldg_i[BI_WU_MIN_DAYS] = batch.warmup_min_days.astype(np.int32)
    bldg_i[BI_WU_MAX_DAYS] = batch.warmup_max_days.astype(np.int32)
    bldg_i[BI_NUM_SURF] = np.sum(surf_mask, axis=1, dtype=np.int32)
    bldg_i[BI_HAS_WINDOW] = np.any(is_window, axis=1).astype(np.int32)

    ctf_out_32, ctf_cross_32, ctf_in_32, ctf_flux_32, bias_in, bias_out = (
        _pack_ctf_arrays(ctf)
    )
    ctf_vec = np.empty(4 * n_ctf_hist + 2, dtype=np.float32)
    ctf_vec[0:n_ctf_hist] = ctf_out_32[1:]
    ctf_vec[n_ctf_hist : 2 * n_ctf_hist] = ctf_cross_32[1:]
    ctf_vec[2 * n_ctf_hist : 3 * n_ctf_hist] = ctf_in_32[1:]
    ctf_vec[3 * n_ctf_hist : 4 * n_ctf_hist] = ctf_flux_32
    ctf_vec[4 * n_ctf_hist] = np.float32(bias_in)
    ctf_vec[4 * n_ctf_hist + 1] = np.float32(bias_out)

    surf_lapse = out_dry_bulb_temp_at(
        np.zeros_like(batch.surf_centroid_z), batch.surf_centroid_z, xp=np
    )
    osc_shift = (
        batch.surf_osc_c_zone + batch.surf_osc_c_out + batch.surf_osc_c_const - 1.0
    ) * T_REF_C
    scon_win = np.where(
        is_window,
        simple_glazing_layer_conductance(batch.surf_u_value, xp=np),
        1.0,
    )

    surf_f = np.zeros((SS_COUNT, n_surf, b_size), dtype=np.float32)
    surf_f[SS_AREA] = batch.surf_area.T.astype(np.float32)
    surf_f[SS_COS_TILT] = batch.surf_cos_tilt.T.astype(np.float32)
    surf_f[SS_SIN_TILT] = batch.surf_sin_tilt.T.astype(np.float32)
    surf_f[SS_TILT_DEG] = batch.surf_tilt_deg.T.astype(np.float32)
    surf_f[SS_CENTROID_Z] = batch.surf_centroid_z.T.astype(np.float32)
    surf_f[SS_LAPSE_OFFSET] = surf_lapse.T.astype(np.float32)
    surf_f[SS_U_VALUE] = batch.surf_u_value.T.astype(np.float32)
    surf_f[SS_OSC_C_CONST] = batch.surf_osc_c_const.T.astype(np.float32)
    surf_f[SS_OSC_T_CONST_DT] = (batch.surf_osc_t_const - T_REF_C).T.astype(np.float32)
    surf_f[SS_OSC_C_OUT] = batch.surf_osc_c_out.T.astype(np.float32)
    surf_f[SS_OSC_C_ZONE] = batch.surf_osc_c_zone.T.astype(np.float32)
    surf_f[SS_OSC_SHIFT] = osc_shift.T.astype(np.float32)
    surf_f[SS_VF_SKY_IR] = batch.surf_vf_sky_ir.T.astype(np.float32)
    surf_f[SS_VF_GROUND_IR] = batch.surf_vf_ground_ir.T.astype(np.float32)
    surf_f[SS_AIR_SKY_SPLIT] = batch.surf_air_sky_rad_split.T.astype(np.float32)
    surf_f[SS_EPS_IN] = batch.surf_eps_in.T.astype(np.float32)
    surf_f[SS_EPS_OUT] = batch.surf_eps_out.T.astype(np.float32)
    surf_f[SS_HEIGHT] = batch.surf_height.T.astype(np.float32)
    surf_f[SS_SCON_WIN] = scon_win.T.astype(np.float32)

    u_bs = batch.surf_u_value.T.astype(np.float32)
    is_im_sb = is_intmass.T
    surf_f[SS_CTF_OUT0] = np.where(is_im_sb, ctf_out_32[0], u_bs)
    surf_f[SS_CTF_CROSS0] = np.where(is_im_sb, ctf_cross_32[0], u_bs)
    surf_f[SS_CTF_IN0] = np.where(is_im_sb, ctf_in_32[0], u_bs)

    surf_flags = (
        surf_mask.T.astype(np.int32) * FLAG_SURF_MASK
        + is_osc.T.astype(np.int32) * FLAG_IS_OSC
        + is_outdoors_op.T.astype(np.int32) * FLAG_IS_OUTDOORS_OP
        + is_intmass.T.astype(np.int32) * FLAG_IS_INTMASS
        + is_window.T.astype(np.int32) * FLAG_IS_WINDOW
        + is_non_window.T.astype(np.int32) * FLAG_IS_NON_WINDOW
    )

    _, script_f = compute_batch_view_factors(batch)
    script_f_sigma = np.transpose(
        (script_f * STEFAN_BOLTZMANN).astype(np.float32), (1, 2, 0)
    )

    weather_run = np.zeros((WF_COUNT, n_run_steps, n_sites), dtype=np.float32)
    weather_wu = np.zeros((WF_COUNT, n_wu_steps, n_sites), dtype=np.float32)
    wu_db0_site = np.empty(n_sites, dtype=np.float64)
    wu_w0_site = np.empty(n_sites, dtype=np.float64)
    for k_idx, w_series in enumerate(weather_by_site):
        weather_run[WF_DT_DB, :, k_idx] = (w_series.dry_bulb - T_REF_C).astype(
            np.float32
        )
        weather_run[WF_HUM_RAT, :, k_idx] = w_series.hum_rat.astype(np.float32)
        weather_run[WF_BARO_PRESS, :, k_idx] = w_series.baro_press.astype(np.float32)
        weather_run[WF_DT_SKY, :, k_idx] = (w_series.sky_temp - T_REF_C).astype(
            np.float32
        )

        weather_wu[WF_DT_DB, :, k_idx] = (w_series.warmup_dry_bulb - T_REF_C).astype(
            np.float32
        )
        weather_wu[WF_HUM_RAT, :, k_idx] = w_series.warmup_hum_rat.astype(np.float32)
        weather_wu[WF_BARO_PRESS, :, k_idx] = w_series.warmup_baro_press.astype(
            np.float32
        )
        weather_wu[WF_DT_SKY, :, k_idx] = (w_series.warmup_sky_temp - T_REF_C).astype(
            np.float32
        )

        wu_db0_site[k_idx] = float(w_series.warmup_dry_bulb[0])
        wu_w0_site[k_idx] = float(w_series.warmup_hum_rat[0])

    sched_gain_w = batch.zone_gain_hourly_w.T.astype(np.float32)

    wu_db0_b = wu_db0_site[site_idx_arr]
    wu_w0_b = wu_w0_site[site_idx_arr]
    t_out_init_air = out_dry_bulb_temp_at(
        wu_db0_b[:, None], batch.surf_centroid_z, xp=np
    )
    is_ext_env = is_outdoors_op | is_window
    t_surf_in_init = np.full((b_size, n_surf), SURF_INITIAL_TEMP, dtype=np.float64)
    t_surf_out_init = np.where(is_ext_env, t_out_init_air, SURF_INITIAL_TEMP)

    state_surf_f = np.zeros((ST_COUNT, n_surf, b_size), dtype=np.float32)
    state_surf_f[ST_SURF_DT_IN] = (t_surf_in_init - T_REF_C).T.astype(np.float32)
    state_surf_f[ST_SURF_DT_OUT] = (t_surf_out_init - T_REF_C).T.astype(np.float32)
    state_surf_f[ST_DTH1_WIN] = ((t_surf_out_init + KELVIN_CONV) - T_REF_K).T.astype(
        np.float32
    )
    state_surf_f[ST_DTH2_WIN] = ((t_surf_in_init + KELVIN_CONV) - T_REF_K).T.astype(
        np.float32
    )

    state_zone_f = np.zeros((ZS_COUNT, b_size), dtype=np.float32)
    z_dt0 = np.float32(ZONE_INITIAL_TEMP - T_REF_C)
    w0_f32 = wu_w0_b.astype(np.float32)
    state_zone_f[ZS_T_MAT_DT] = z_dt0
    state_zone_f[ZS_W_ZONE] = w0_f32
    state_zone_f[ZS_W_ZONE_AVG] = w0_f32
    for offset in range(4):
        state_zone_f[ZS_XMAT0 + offset] = z_dt0
        state_zone_f[ZS_DSXMAT0 + offset] = z_dt0
        state_zone_f[ZS_W_PREV0 + offset] = w0_f32
        state_zone_f[ZS_DSW_PREV0 + offset] = w0_f32
    state_num_sys_last = np.ones(b_size, dtype=np.int32)

    q_init = batch.surf_u_value * (t_surf_out_init - SURF_INITIAL_TEMP)
    q_init = np.where(is_intmass, 0.0, q_init)
    state_ctf_hist = np.zeros(
        (CH_COUNT, n_ctf_hist, n_surf, b_size), dtype=np.float32
    )
    state_ctf_hist[CH_T_IN_DT] = np.float32(SURF_INITIAL_TEMP - T_REF_C)
    dt_out_init_sb = (t_surf_out_init - T_REF_C).T.astype(np.float32)
    q_init_sb = q_init.T.astype(np.float32)
    for m_idx in range(n_ctf_hist):
        state_ctf_hist[CH_T_OUT_DT, m_idx] = dt_out_init_sb
        state_ctf_hist[CH_Q_OUT, m_idx] = q_init_sb
        state_ctf_hist[CH_Q_IN, m_idx] = q_init_sb

    hourly_heating_j = np.zeros((n_hours, b_size), dtype=np.float32)
    wu_stats = np.zeros((WU_STAT_COUNT, b_size), dtype=np.float32)

    return PackedBatch(
        batch_size=b_size,
        max_surfaces=n_surf,
        n_sites=n_sites,
        n_ctf_hist=n_ctf_hist,
        steps_per_hour=sph,
        n_run_steps=n_run_steps,
        n_wu_steps=n_wu_steps,
        n_hours=n_hours,
        bldg_f=np.ascontiguousarray(bldg_f),
        bldg_i=np.ascontiguousarray(bldg_i),
        surf_f=np.ascontiguousarray(surf_f),
        surf_flags=np.ascontiguousarray(surf_flags),
        script_f_sigma=np.ascontiguousarray(script_f_sigma),
        ctf_vec=np.ascontiguousarray(ctf_vec),
        weather_run=np.ascontiguousarray(weather_run),
        weather_wu=np.ascontiguousarray(weather_wu),
        sched_gain_w=np.ascontiguousarray(sched_gain_w),
        state_zone_f=np.ascontiguousarray(state_zone_f),
        state_num_sys_last=np.ascontiguousarray(state_num_sys_last),
        state_surf_f=np.ascontiguousarray(state_surf_f),
        state_ctf_hist=np.ascontiguousarray(state_ctf_hist),
        hourly_heating_j=np.ascontiguousarray(hourly_heating_j),
        wu_stats=np.ascontiguousarray(wu_stats),
    )


def unpack_state(packed: PackedBatch) -> dict[str, np.ndarray]:
    """Unpack mutable simulation state buffers back to float64/int32 ``[B, ...]``.

    Args:
        packed: ``PackedBatch`` returned by ``pack``.

    Returns:
        Dictionary of host NumPy arrays matching Stage A state shapes and units
        (temperatures in degrees C or Kelvin as in Stage A).
    """
    zf = packed.state_zone_f.astype(np.float64)
    sf = packed.state_surf_f.astype(np.float64)
    cf = packed.state_ctf_hist.astype(np.float64)
    return {
        "t_mat": np.ascontiguousarray(zf[ZS_T_MAT_DT] + T_REF_C),
        "w_zone": np.ascontiguousarray(zf[ZS_W_ZONE]),
        "w_zone_avg": np.ascontiguousarray(zf[ZS_W_ZONE_AVG]),
        "xmat": np.ascontiguousarray(zf[ZS_XMAT0 : ZS_XMAT3 + 1].T + T_REF_C),
        "dsxmat": np.ascontiguousarray(zf[ZS_DSXMAT0 : ZS_DSXMAT3 + 1].T + T_REF_C),
        "w_prev_ts": np.ascontiguousarray(zf[ZS_W_PREV0 : ZS_W_PREV3 + 1].T),
        "dsw_prev_ts": np.ascontiguousarray(zf[ZS_DSW_PREV0 : ZS_DSW_PREV3 + 1].T),
        "num_sys_last": np.ascontiguousarray(
            packed.state_num_sys_last.astype(np.int32, copy=True)
        ),
        "t_surf_in": np.ascontiguousarray(sf[ST_SURF_DT_IN].T + T_REF_C),
        "t_surf_out": np.ascontiguousarray(sf[ST_SURF_DT_OUT].T + T_REF_C),
        "theta1_win": np.ascontiguousarray(sf[ST_DTH1_WIN].T + T_REF_K),
        "theta2_win": np.ascontiguousarray(sf[ST_DTH2_WIN].T + T_REF_K),
        "t_out_hist": np.ascontiguousarray(
            np.transpose(cf[CH_T_OUT_DT], (2, 1, 0)) + T_REF_C
        ),
        "t_in_hist": np.ascontiguousarray(
            np.transpose(cf[CH_T_IN_DT], (2, 1, 0)) + T_REF_C
        ),
        "q_out_hist": np.ascontiguousarray(np.transpose(cf[CH_Q_OUT], (2, 1, 0))),
        "q_in_hist": np.ascontiguousarray(np.transpose(cf[CH_Q_IN], (2, 1, 0))),
    }


def unpack_static(packed: PackedBatch) -> dict[str, np.ndarray]:
    """Unpack static building, surface, and view-factor buffers to float64/int32.

    Args:
        packed: ``PackedBatch`` returned by ``pack``.

    Returns:
        Dictionary of ``BatchSpec``-aligned float64/int32/bool arrays.
    """
    bf = packed.bldg_f.astype(np.float64)
    sf = packed.surf_f.astype(np.float64)
    flags = packed.surf_flags.T
    return {
        "zone_volume": np.ascontiguousarray(bf[BF_ZONE_VOLUME]),
        "zone_floor_area": np.ascontiguousarray(bf[BF_ZONE_FLOOR_AREA]),
        "zone_centroid_z": np.ascontiguousarray(bf[BF_ZONE_CENTROID_Z]),
        "zone_vent_ach": np.ascontiguousarray(bf[BF_VENT_ACH]),
        "zone_vent_flow_m3s": np.ascontiguousarray(bf[BF_VENT_FLOW_M3S]),
        "zone_heat_setpoint": np.ascontiguousarray(bf[BF_HEAT_SP_DT] + T_REF_C),
        "zone_cool_setpoint": np.ascontiguousarray(bf[BF_COOL_SP_DT] + T_REF_C),
        "zone_max_heat_supply_temp": np.ascontiguousarray(
            bf[BF_MAX_HEAT_SUP_DT] + T_REF_C
        ),
        "zone_max_heat_supply_humrat": np.ascontiguousarray(
            bf[BF_MAX_HEAT_SUP_HUMRAT]
        ),
        "h_conv_min": np.ascontiguousarray(bf[BF_H_CONV_MIN]),
        "h_conv_max": np.ascontiguousarray(bf[BF_H_CONV_MAX]),
        "loads_conv_tol": np.ascontiguousarray(bf[BF_LOADS_CONV_TOL]),
        "temp_conv_tol": np.ascontiguousarray(bf[BF_TEMP_CONV_TOL]),
        "site_elevation": np.ascontiguousarray(bf[BF_SITE_ELEVATION]),
        "site_index": np.ascontiguousarray(packed.bldg_i[BI_SITE_IDX]),
        "warmup_min_days": np.ascontiguousarray(packed.bldg_i[BI_WU_MIN_DAYS]),
        "warmup_max_days": np.ascontiguousarray(packed.bldg_i[BI_WU_MAX_DAYS]),
        "surf_mask": np.ascontiguousarray((flags & FLAG_SURF_MASK) != 0),
        "surf_area": np.ascontiguousarray(sf[SS_AREA].T),
        "surf_cos_tilt": np.ascontiguousarray(sf[SS_COS_TILT].T),
        "surf_sin_tilt": np.ascontiguousarray(sf[SS_SIN_TILT].T),
        "surf_tilt_deg": np.ascontiguousarray(sf[SS_TILT_DEG].T),
        "surf_centroid_z": np.ascontiguousarray(sf[SS_CENTROID_Z].T),
        "surf_u_value": np.ascontiguousarray(sf[SS_U_VALUE].T),
        "surf_osc_c_const": np.ascontiguousarray(sf[SS_OSC_C_CONST].T),
        "surf_osc_t_const": np.ascontiguousarray(sf[SS_OSC_T_CONST_DT].T + T_REF_C),
        "surf_osc_c_out": np.ascontiguousarray(sf[SS_OSC_C_OUT].T),
        "surf_osc_c_zone": np.ascontiguousarray(sf[SS_OSC_C_ZONE].T),
        "surf_vf_sky_ir": np.ascontiguousarray(sf[SS_VF_SKY_IR].T),
        "surf_vf_ground_ir": np.ascontiguousarray(sf[SS_VF_GROUND_IR].T),
        "surf_air_sky_rad_split": np.ascontiguousarray(sf[SS_AIR_SKY_SPLIT].T),
        "surf_eps_in": np.ascontiguousarray(sf[SS_EPS_IN].T),
        "surf_eps_out": np.ascontiguousarray(sf[SS_EPS_OUT].T),
        "surf_height": np.ascontiguousarray(sf[SS_HEIGHT].T),
        "script_f_sigma": np.ascontiguousarray(
            np.transpose(packed.script_f_sigma.astype(np.float64), (2, 0, 1))
        ),
    }


def unpack_weather(packed: PackedBatch) -> dict[str, np.ndarray]:
    """Unpack per-site run and warm-up weather buffers back to float64 ``[K, T]``.

    Args:
        packed: ``PackedBatch`` returned by ``pack``.

    Returns:
        Dictionary of float64 arrays indexed ``[site, step]``.
    """
    wr = packed.weather_run.astype(np.float64)
    ww = packed.weather_wu.astype(np.float64)
    return {
        "dry_bulb": np.ascontiguousarray(wr[WF_DT_DB].T + T_REF_C),
        "hum_rat": np.ascontiguousarray(wr[WF_HUM_RAT].T),
        "baro_press": np.ascontiguousarray(wr[WF_BARO_PRESS].T),
        "sky_temp": np.ascontiguousarray(wr[WF_DT_SKY].T + T_REF_C),
        "warmup_dry_bulb": np.ascontiguousarray(ww[WF_DT_DB].T + T_REF_C),
        "warmup_hum_rat": np.ascontiguousarray(ww[WF_HUM_RAT].T),
        "warmup_baro_press": np.ascontiguousarray(ww[WF_BARO_PRESS].T),
        "warmup_sky_temp": np.ascontiguousarray(ww[WF_DT_SKY].T + T_REF_C),
    }


def unpack_schedules(packed: PackedBatch) -> np.ndarray:
    """Unpack hourly internal gains schedule back to float64 ``[B, 8760]``.

    Args:
        packed: ``PackedBatch`` returned by ``pack``.

    Returns:
        Float64 array of hourly internal gains in Watts with shape ``[B, 8760]``.
    """
    return np.ascontiguousarray(packed.sched_gain_w.T.astype(np.float64))
