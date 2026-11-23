"""CUDA Stage C driver for the unified multi-rung flat-CSR kernel (S1/S2a/S3/S2b/M8)."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import time

import numpy as np

from openubem.gpusim.general_model import GeneralBatch
from openubem.gpusim.weather import WeatherSeries

_KERNEL_DIR = Path(__file__).resolve().parent / "kernel"
_HEADER_PATH = _KERNEL_DIR / "general_common.h"

_CUDA_WRAPPER_SRC = r"""
#include "general_common.h"

extern "C" {

__global__ void gen_init_kernel(
    int B,
    int n_wu_steps,
    const int *site_idx,
    const int *zone_offset,
    const int *surf_offset,
    const int *surf_boundary,
    const float *surf_centroid_z,
    const int *surf_n_modes,
    const float *surf_m_so,
    const float *surf_m_si,
    const float *wu_t_db,
    const float *wu_hum_rat,
    float *t_surf_in,
    float *t_surf_out,
    float *t_surf_in_prev,
    float *t_surf_out_prev,
    float *theta1_win,
    float *theta2_win,
    float *modal_z,
    float *t_mat,
    float *xmat,
    float *dsxmat,
    float *w_zone,
    float *w_zone_avg,
    float *w_prev,
    float *dsw_prev,
    int *num_sys_last,
    int *wu_still,
    int *wu_days,
    float *wu_max_t_prev,
    float *wu_min_t_prev,
    float *wu_max_h_prev
) {
    int b = (int)(blockIdx.x * blockDim.x + threadIdx.x);
    if (b >= B) return;

    int si = site_idx[b];
    float t0_site = wu_t_db[si * n_wu_steps];
    float w0_site = wu_hum_rat[si * n_wu_steps];

    int z0 = zone_offset[b];
    int z1 = zone_offset[b + 1];
    for (int z = z0; z < z1; ++z) {
        t_mat[z] = 23.0f;
        w_zone[z] = w0_site;
        w_zone_avg[z] = w0_site;
        num_sys_last[z] = 1;
        for (int k = 0; k < 4; ++k) {
            xmat[z * 4 + k] = 23.0f;
            dsxmat[z * 4 + k] = 23.0f;
            w_prev[z * 4 + k] = w0_site;
            dsw_prev[z * 4 + k] = w0_site;
        }
    }

    int s0 = surf_offset[b];
    int s1 = surf_offset[b + 1];
    for (int s = s0; s < s1; ++s) {
        int bnd = surf_boundary[s];
        float ti = 23.0f;
        float to = 23.0f;
        if (bnd == BOUND_OUTDOORS || bnd == BOUND_WINDOW || bnd == BOUND_DOOR) {
            to = gen_out_dry_bulb_at(t0_site, surf_centroid_z[s]);
        }
        t_surf_in[s] = ti;
        t_surf_out[s] = to;
        t_surf_in_prev[s] = ti;
        t_surf_out_prev[s] = to;
        theta1_win[s] = to + GEN_KELVIN;
        theta2_win[s] = ti + GEN_KELVIN;
        int nm = surf_n_modes[s];
        if (nm > 0) {
            int mbase = s * GEN_MAX_MODES;
            for (int k = 0; k < nm; ++k) {
                modal_z[mbase + k] = surf_m_so[mbase + k] * to + surf_m_si[mbase + k] * ti;
            }
        }
    }

    wu_still[b] = 1;
    wu_days[b] = 0;
    wu_max_t_prev[b] = -9999.0f;
    wu_min_t_prev[b] = 1000.0f;
    wu_max_h_prev[b] = -9999.0f;
}

__global__ void gen_warmup_day_kernel(
    int B,
    int day,
    int steps_per_day,
    int sph,
    int has_shading,
    const int *site_idx,
    const int *terrain_idx,
    const int *zone_offset,
    const int *surf_offset,
    const float *site_ground_temp,
    const int *warmup_min_days,
    const int *warmup_max_days,
    const float *loads_conv_tol,
    const float *temp_conv_tol,
    const float *h_conv_min,
    const int *zone_surf_offset,
    const int *zone_sf_offset,
    const float *zone_volume,
    const float *zone_centroid_z,
    const int *zone_has_hvac,
    const int *zone_has_cooling,
    const float *zone_max_heat_sup_t,
    const float *zone_min_cool_sup_t,
    const float *zone_heat_sp_hr,
    const float *zone_cool_sp_hr,
    const float *zone_gain_conv_hr,
    const float *zone_gain_rad_hr,
    const float *zone_vent_flow_hr,
    const float *zone_total_op_aa,
    const float *zone_floor_area_sw,
    const float *zone_floor_alpha_eff,
    const float *zone_total_eps_area,
    const int *surf_class,
    const int *surf_boundary,
    const int *surf_partner_idx,
    const float *surf_area,
    const float *surf_tilt_deg,
    const float *surf_cos_tilt,
    const float *surf_sin_tilt,
    const float *surf_azimuth_deg,
    const float *surf_nx,
    const float *surf_ny,
    const float *surf_nz,
    const float *surf_centroid_z,
    const float *surf_height,
    const float *surf_roughness_mult,
    const int *surf_sun_exposed,
    const int *surf_wind_exposed,
    const float *surf_solar_abs_out,
    const float *surf_solar_abs_in,
    const float *surf_eps_in,
    const float *surf_eps_out,
    const float *surf_vf_ground,
    const float *surf_vf_sky,
    const float *surf_vf_sky_ir,
    const float *surf_vf_ground_ir,
    const float *surf_air_sky_split,
    const float *surf_osc_c_const,
    const float *surf_osc_t_const,
    const float *surf_osc_c_out,
    const float *surf_osc_c_zone,
    const float *surf_scon,
    const float *surf_t_norm,
    const float *surf_a_norm,
    const float *surf_tau_diff,
    const float *surf_abs_diff,
    const int *surf_n_modes,
    const float *surf_ctf_out0,
    const float *surf_ctf_cross0,
    const float *surf_ctf_in0,
    const float *surf_lag_oo,
    const float *surf_lag_oi,
    const float *surf_lag_io,
    const float *surf_lag_ii,
    const float *surf_m_decay,
    const float *surf_m_gno,
    const float *surf_m_gni,
    const float *surf_m_goo,
    const float *surf_m_goi,
    const float *surf_m_co,
    const float *surf_m_ci,
    const float *script_f_sigma,
    const float *surf_dif_sky_shdg,
    const unsigned char *surf_sunlit_u8,
    const float *w_t_db,
    const float *w_hum_rat,
    const float *w_pb,
    const float *w_t_sky,
    const float *w_ws,
    const float *w_wd,
    const float *w_wb,
    const float *w_rain,
    const float *w_dni,
    const float *w_dhi,
    const float *w_sx,
    const float *w_sy,
    const float *w_sz,
    const float *w_f1,
    const float *w_f2,
    float *t_surf_in,
    float *t_surf_out,
    float *t_surf_in_prev,
    float *t_surf_out_prev,
    float *t_surf_in_old,
    float *theta1_win,
    float *theta2_win,
    float *h_conv_in,
    float *ctf_const_in,
    float *ctf_const_out,
    float *q_sol_out,
    float *q_sw_in,
    float *q_sol_win,
    float *modal_z,
    float *t_mat,
    float *xmat,
    float *dsxmat,
    float *w_zone,
    float *w_zone_avg,
    float *w_prev,
    float *dsw_prev,
    int *num_sys_last,
    float *hourly_heating_j,
    float *zone_annual_kwh,
    float *zone_temp_rec,
    int *wu_still,
    int *wu_days,
    float *wu_max_t_prev,
    float *wu_min_t_prev,
    float *wu_max_h_prev
) {
    int b = (int)(blockIdx.x * blockDim.x + threadIdx.x);
    if (b >= B || !wu_still[b]) return;

    float max_t = -9999.0f;
    float min_t = 1000.0f;
    float max_h = -9999.0f;

    for (int step = 0; step < steps_per_day; ++step) {
        int begin_env = (day == 1 && step == 0) ? 1 : 0;
        gen_step_building(
            b, step, 1, begin_env, sph, steps_per_day, has_shading, 0,
            site_idx, terrain_idx, zone_offset, surf_offset, site_ground_temp, h_conv_min,
            zone_surf_offset, zone_sf_offset, zone_volume, zone_centroid_z,
            zone_has_hvac, zone_has_cooling, zone_max_heat_sup_t, zone_min_cool_sup_t,
            zone_heat_sp_hr, zone_cool_sp_hr, zone_gain_conv_hr, zone_gain_rad_hr,
            zone_vent_flow_hr, zone_total_op_aa, zone_floor_area_sw, zone_floor_alpha_eff,
            zone_total_eps_area,
            surf_class, surf_boundary, surf_partner_idx, surf_area, surf_tilt_deg,
            surf_cos_tilt, surf_sin_tilt, surf_azimuth_deg, surf_nx, surf_ny, surf_nz,
            surf_centroid_z, surf_height, surf_roughness_mult, surf_sun_exposed,
            surf_wind_exposed, surf_solar_abs_out, surf_solar_abs_in, surf_eps_in,
            surf_eps_out, surf_vf_ground, surf_vf_sky, surf_vf_sky_ir, surf_vf_ground_ir,
            surf_air_sky_split, surf_osc_c_const, surf_osc_t_const, surf_osc_c_out,
            surf_osc_c_zone, surf_scon, surf_t_norm, surf_a_norm, surf_tau_diff,
            surf_abs_diff, surf_n_modes, surf_ctf_out0, surf_ctf_cross0, surf_ctf_in0,
            surf_lag_oo, surf_lag_oi, surf_lag_io, surf_lag_ii, surf_m_decay, surf_m_gno,
            surf_m_gni, surf_m_goo, surf_m_goi, surf_m_co, surf_m_ci,
            script_f_sigma, surf_dif_sky_shdg, surf_sunlit_u8,
            w_t_db, w_hum_rat, w_pb, w_t_sky, w_ws, w_wd, w_wb, w_rain, w_dni, w_dhi,
            w_sx, w_sy, w_sz, w_f1, w_f2,
            t_surf_in, t_surf_out, t_surf_in_prev, t_surf_out_prev, t_surf_in_old,
            theta1_win, theta2_win, h_conv_in, ctf_const_in, ctf_const_out,
            q_sol_out, q_sw_in, q_sol_win, modal_z,
            t_mat, xmat, dsxmat, w_zone, w_zone_avg, w_prev, dsw_prev, num_sys_last,
            hourly_heating_j, zone_annual_kwh, zone_temp_rec,
            &max_t, &min_t, &max_h
        );
    }

    int pass_max = (GPUSIM_FABS(wu_max_t_prev[b] - max_t) <= temp_conv_tol[b]);
    int pass_min = (GPUSIM_FABS(wu_min_t_prev[b] - min_t) <= temp_conv_tol[b]);
    float eff_h = GPUSIM_FABS(GPUSIM_FMAX(max_h, GEN_WARMUP_MIN_LOAD));
    float eff_hp = GPUSIM_FABS(GPUSIM_FMAX(wu_max_h_prev[b], GEN_WARMUP_MIN_LOAD));
    int pass_h = (max_h > 1.0e-4f) ? (GPUSIM_FABS((eff_h - eff_hp) / eff_h) <= loads_conv_tol[b]) : 1;

    if ((pass_max && pass_min && pass_h && day >= warmup_min_days[b]) || (day >= warmup_max_days[b])) {
        wu_days[b] = day;
        wu_still[b] = 0;
    } else {
        wu_max_t_prev[b] = max_t;
        wu_min_t_prev[b] = min_t;
        wu_max_h_prev[b] = eff_h;
    }
}

__global__ void gen_run_chunk_kernel(
    int B,
    int step_start,
    int step_end,
    int sph,
    int n_run_steps,
    int has_shading,
    int record_zone_temp,
    const int *site_idx,
    const int *terrain_idx,
    const int *zone_offset,
    const int *surf_offset,
    const float *site_ground_temp,
    const float *h_conv_min,
    const int *zone_surf_offset,
    const int *zone_sf_offset,
    const float *zone_volume,
    const float *zone_centroid_z,
    const int *zone_has_hvac,
    const int *zone_has_cooling,
    const float *zone_max_heat_sup_t,
    const float *zone_min_cool_sup_t,
    const float *zone_heat_sp_hr,
    const float *zone_cool_sp_hr,
    const float *zone_gain_conv_hr,
    const float *zone_gain_rad_hr,
    const float *zone_vent_flow_hr,
    const float *zone_total_op_aa,
    const float *zone_floor_area_sw,
    const float *zone_floor_alpha_eff,
    const float *zone_total_eps_area,
    const int *surf_class,
    const int *surf_boundary,
    const int *surf_partner_idx,
    const float *surf_area,
    const float *surf_tilt_deg,
    const float *surf_cos_tilt,
    const float *surf_sin_tilt,
    const float *surf_azimuth_deg,
    const float *surf_nx,
    const float *surf_ny,
    const float *surf_nz,
    const float *surf_centroid_z,
    const float *surf_height,
    const float *surf_roughness_mult,
    const int *surf_sun_exposed,
    const int *surf_wind_exposed,
    const float *surf_solar_abs_out,
    const float *surf_solar_abs_in,
    const float *surf_eps_in,
    const float *surf_eps_out,
    const float *surf_vf_ground,
    const float *surf_vf_sky,
    const float *surf_vf_sky_ir,
    const float *surf_vf_ground_ir,
    const float *surf_air_sky_split,
    const float *surf_osc_c_const,
    const float *surf_osc_t_const,
    const float *surf_osc_c_out,
    const float *surf_osc_c_zone,
    const float *surf_scon,
    const float *surf_t_norm,
    const float *surf_a_norm,
    const float *surf_tau_diff,
    const float *surf_abs_diff,
    const int *surf_n_modes,
    const float *surf_ctf_out0,
    const float *surf_ctf_cross0,
    const float *surf_ctf_in0,
    const float *surf_lag_oo,
    const float *surf_lag_oi,
    const float *surf_lag_io,
    const float *surf_lag_ii,
    const float *surf_m_decay,
    const float *surf_m_gno,
    const float *surf_m_gni,
    const float *surf_m_goo,
    const float *surf_m_goi,
    const float *surf_m_co,
    const float *surf_m_ci,
    const float *script_f_sigma,
    const float *surf_dif_sky_shdg,
    const unsigned char *surf_sunlit_u8,
    const float *w_t_db,
    const float *w_hum_rat,
    const float *w_pb,
    const float *w_t_sky,
    const float *w_ws,
    const float *w_wd,
    const float *w_wb,
    const float *w_rain,
    const float *w_dni,
    const float *w_dhi,
    const float *w_sx,
    const float *w_sy,
    const float *w_sz,
    const float *w_f1,
    const float *w_f2,
    float *t_surf_in,
    float *t_surf_out,
    float *t_surf_in_prev,
    float *t_surf_out_prev,
    float *t_surf_in_old,
    float *theta1_win,
    float *theta2_win,
    float *h_conv_in,
    float *ctf_const_in,
    float *ctf_const_out,
    float *q_sol_out,
    float *q_sw_in,
    float *q_sol_win,
    float *modal_z,
    float *t_mat,
    float *xmat,
    float *dsxmat,
    float *w_zone,
    float *w_zone_avg,
    float *w_prev,
    float *dsw_prev,
    int *num_sys_last,
    float *hourly_heating_j,
    float *zone_annual_kwh,
    float *zone_temp_rec
) {
    int b = (int)(blockIdx.x * blockDim.x + threadIdx.x);
    if (b >= B) return;

    float d1 = 0.0f, d2 = 0.0f, d3 = 0.0f;
    for (int step = step_start; step < step_end; ++step) {
        gen_step_building(
            b, step, 0, 0, sph, n_run_steps, has_shading, record_zone_temp,
            site_idx, terrain_idx, zone_offset, surf_offset, site_ground_temp, h_conv_min,
            zone_surf_offset, zone_sf_offset, zone_volume, zone_centroid_z,
            zone_has_hvac, zone_has_cooling, zone_max_heat_sup_t, zone_min_cool_sup_t,
            zone_heat_sp_hr, zone_cool_sp_hr, zone_gain_conv_hr, zone_gain_rad_hr,
            zone_vent_flow_hr, zone_total_op_aa, zone_floor_area_sw, zone_floor_alpha_eff,
            zone_total_eps_area,
            surf_class, surf_boundary, surf_partner_idx, surf_area, surf_tilt_deg,
            surf_cos_tilt, surf_sin_tilt, surf_azimuth_deg, surf_nx, surf_ny, surf_nz,
            surf_centroid_z, surf_height, surf_roughness_mult, surf_sun_exposed,
            surf_wind_exposed, surf_solar_abs_out, surf_solar_abs_in, surf_eps_in,
            surf_eps_out, surf_vf_ground, surf_vf_sky, surf_vf_sky_ir, surf_vf_ground_ir,
            surf_air_sky_split, surf_osc_c_const, surf_osc_t_const, surf_osc_c_out,
            surf_osc_c_zone, surf_scon, surf_t_norm, surf_a_norm, surf_tau_diff,
            surf_abs_diff, surf_n_modes, surf_ctf_out0, surf_ctf_cross0, surf_ctf_in0,
            surf_lag_oo, surf_lag_oi, surf_lag_io, surf_lag_ii, surf_m_decay, surf_m_gno,
            surf_m_gni, surf_m_goo, surf_m_goi, surf_m_co, surf_m_ci,
            script_f_sigma, surf_dif_sky_shdg, surf_sunlit_u8,
            w_t_db, w_hum_rat, w_pb, w_t_sky, w_ws, w_wd, w_wb, w_rain, w_dni, w_dhi,
            w_sx, w_sy, w_sz, w_f1, w_f2,
            t_surf_in, t_surf_out, t_surf_in_prev, t_surf_out_prev, t_surf_in_old,
            theta1_win, theta2_win, h_conv_in, ctf_const_in, ctf_const_out,
            q_sol_out, q_sw_in, q_sol_win, modal_z,
            t_mat, xmat, dsxmat, w_zone, w_zone_avg, w_prev, dsw_prev, num_sys_last,
            hourly_heating_j, zone_annual_kwh, zone_temp_rec,
            &d1, &d2, &d3
        );
    }
}

__global__ void gen_warmup_zone_day_kernel(
    int Z,
    int day,
    int steps_per_day,
    int sph,
    int has_shading,
    const int *site_idx,
    const int *terrain_idx,
    const float *site_ground_temp,
    const int *warmup_min_days,
    const int *warmup_max_days,
    const float *loads_conv_tol,
    const float *temp_conv_tol,
    const float *h_conv_min,
    const int *zone_bldg_idx,
    const int *zone_surf_offset,
    const int *zone_sf_offset,
    const float *zone_volume,
    const float *zone_centroid_z,
    const int *zone_has_hvac,
    const int *zone_has_cooling,
    const float *zone_max_heat_sup_t,
    const float *zone_min_cool_sup_t,
    const float *zone_heat_sp_hr,
    const float *zone_cool_sp_hr,
    const float *zone_gain_conv_hr,
    const float *zone_gain_rad_hr,
    const float *zone_vent_flow_hr,
    const float *zone_total_op_aa,
    const float *zone_floor_area_sw,
    const float *zone_floor_alpha_eff,
    const float *zone_total_eps_area,
    const int *surf_class,
    const int *surf_boundary,
    const int *surf_partner_idx,
    const float *surf_area,
    const float *surf_tilt_deg,
    const float *surf_cos_tilt,
    const float *surf_sin_tilt,
    const float *surf_azimuth_deg,
    const float *surf_nx,
    const float *surf_ny,
    const float *surf_nz,
    const float *surf_centroid_z,
    const float *surf_height,
    const float *surf_roughness_mult,
    const int *surf_sun_exposed,
    const int *surf_wind_exposed,
    const float *surf_solar_abs_out,
    const float *surf_solar_abs_in,
    const float *surf_eps_in,
    const float *surf_eps_out,
    const float *surf_vf_ground,
    const float *surf_vf_sky,
    const float *surf_vf_sky_ir,
    const float *surf_vf_ground_ir,
    const float *surf_air_sky_split,
    const float *surf_osc_c_const,
    const float *surf_osc_t_const,
    const float *surf_osc_c_out,
    const float *surf_osc_c_zone,
    const float *surf_scon,
    const float *surf_t_norm,
    const float *surf_a_norm,
    const float *surf_tau_diff,
    const float *surf_abs_diff,
    const int *surf_n_modes,
    const float *surf_ctf_out0,
    const float *surf_ctf_cross0,
    const float *surf_ctf_in0,
    const float *surf_lag_oo,
    const float *surf_lag_oi,
    const float *surf_lag_io,
    const float *surf_lag_ii,
    const float *surf_m_decay,
    const float *surf_m_gno,
    const float *surf_m_gni,
    const float *surf_m_goo,
    const float *surf_m_goi,
    const float *surf_m_co,
    const float *surf_m_ci,
    const float *script_f_sigma,
    const float *surf_dif_sky_shdg,
    const unsigned char *surf_sunlit_u8,
    const float *w_t_db,
    const float *w_hum_rat,
    const float *w_pb,
    const float *w_t_sky,
    const float *w_ws,
    const float *w_wd,
    const float *w_wb,
    const float *w_rain,
    const float *w_dni,
    const float *w_dhi,
    const float *w_sx,
    const float *w_sy,
    const float *w_sz,
    const float *w_f1,
    const float *w_f2,
    float *t_surf_in,
    float *t_surf_out,
    float *t_surf_in_prev,
    float *t_surf_out_prev,
    float *t_surf_in_old,
    float *theta1_win,
    float *theta2_win,
    float *h_conv_in,
    float *ctf_const_in,
    float *ctf_const_out,
    float *q_sol_out,
    float *q_sw_in,
    float *q_sol_win,
    float *modal_z,
    float *t_mat,
    float *xmat,
    float *dsxmat,
    float *w_zone,
    float *w_zone_avg,
    float *w_prev,
    float *dsw_prev,
    int *num_sys_last,
    float *zone_annual_kwh,
    float *zone_temp_rec,
    int *z_wu_still,
    int *z_wu_days,
    float *z_wu_max_t_prev,
    float *z_wu_min_t_prev,
    float *z_wu_max_h_prev
) {
    int z = (int)(blockIdx.x * blockDim.x + threadIdx.x);
    if (z >= Z || !z_wu_still[z]) return;
    int b = zone_bldg_idx[z];

    float max_t = -9999.0f;
    float min_t = 1000.0f;
    float max_h = -9999.0f;
    float dummy_hj = 0.0f;

    for (int step = 0; step < steps_per_day; ++step) {
        int begin_env = (day == 1 && step == 0) ? 1 : 0;
        gen_step_zone(
            z, step, 1, begin_env, sph, steps_per_day, has_shading, 0,
            site_idx, terrain_idx, site_ground_temp, h_conv_min,
            zone_bldg_idx, zone_surf_offset, zone_sf_offset, zone_volume, zone_centroid_z,
            zone_has_hvac, zone_has_cooling, zone_max_heat_sup_t, zone_min_cool_sup_t,
            zone_heat_sp_hr, zone_cool_sp_hr, zone_gain_conv_hr, zone_gain_rad_hr,
            zone_vent_flow_hr, zone_total_op_aa, zone_floor_area_sw, zone_floor_alpha_eff,
            zone_total_eps_area,
            surf_class, surf_boundary, surf_partner_idx, surf_area, surf_tilt_deg,
            surf_cos_tilt, surf_sin_tilt, surf_azimuth_deg, surf_nx, surf_ny, surf_nz,
            surf_centroid_z, surf_height, surf_roughness_mult, surf_sun_exposed,
            surf_wind_exposed, surf_solar_abs_out, surf_solar_abs_in, surf_eps_in,
            surf_eps_out, surf_vf_ground, surf_vf_sky, surf_vf_sky_ir, surf_vf_ground_ir,
            surf_air_sky_split, surf_osc_c_const, surf_osc_t_const, surf_osc_c_out,
            surf_osc_c_zone, surf_scon, surf_t_norm, surf_a_norm, surf_tau_diff,
            surf_abs_diff, surf_n_modes, surf_ctf_out0, surf_ctf_cross0, surf_ctf_in0,
            surf_lag_oo, surf_lag_oi, surf_lag_io, surf_lag_ii, surf_m_decay, surf_m_gno,
            surf_m_gni, surf_m_goo, surf_m_goi, surf_m_co, surf_m_ci,
            script_f_sigma, surf_dif_sky_shdg, surf_sunlit_u8,
            w_t_db, w_hum_rat, w_pb, w_t_sky, w_ws, w_wd, w_wb, w_rain, w_dni, w_dhi,
            w_sx, w_sy, w_sz, w_f1, w_f2,
            t_surf_in, t_surf_out, t_surf_in_prev, t_surf_out_prev, t_surf_in_old,
            theta1_win, theta2_win, h_conv_in, ctf_const_in, ctf_const_out,
            q_sol_out, q_sw_in, q_sol_win, modal_z,
            t_mat, xmat, dsxmat, w_zone, w_zone_avg, w_prev, dsw_prev, num_sys_last,
            zone_annual_kwh, zone_temp_rec,
            &dummy_hj, &max_t, &min_t, &max_h
        );
    }

    int pass_max = (GPUSIM_FABS(z_wu_max_t_prev[z] - max_t) <= temp_conv_tol[b]);
    int pass_min = (GPUSIM_FABS(z_wu_min_t_prev[z] - min_t) <= temp_conv_tol[b]);
    float eff_h = GPUSIM_FABS(GPUSIM_FMAX(max_h, GEN_WARMUP_MIN_LOAD));
    float eff_hp = GPUSIM_FABS(GPUSIM_FMAX(z_wu_max_h_prev[z], GEN_WARMUP_MIN_LOAD));
    int pass_h = (max_h > 1.0e-4f) ? (GPUSIM_FABS((eff_h - eff_hp) / eff_h) <= loads_conv_tol[b]) : 1;

    if ((pass_max && pass_min && pass_h && day >= warmup_min_days[b]) || (day >= warmup_max_days[b])) {
        z_wu_days[z] = day;
        z_wu_still[z] = 0;
    } else {
        z_wu_max_t_prev[z] = max_t;
        z_wu_min_t_prev[z] = min_t;
        z_wu_max_h_prev[z] = max_h;
    }
}

__global__ void gen_run_zone_chunk_kernel(
    int Z,
    int step_start,
    int step_end,
    int sph,
    int n_run_steps,
    int has_shading,
    int record_zone_temp,
    const int *site_idx,
    const int *terrain_idx,
    const float *site_ground_temp,
    const float *h_conv_min,
    const int *zone_bldg_idx,
    const int *zone_surf_offset,
    const int *zone_sf_offset,
    const float *zone_volume,
    const float *zone_centroid_z,
    const int *zone_has_hvac,
    const int *zone_has_cooling,
    const float *zone_max_heat_sup_t,
    const float *zone_min_cool_sup_t,
    const float *zone_heat_sp_hr,
    const float *zone_cool_sp_hr,
    const float *zone_gain_conv_hr,
    const float *zone_gain_rad_hr,
    const float *zone_vent_flow_hr,
    const float *zone_total_op_aa,
    const float *zone_floor_area_sw,
    const float *zone_floor_alpha_eff,
    const float *zone_total_eps_area,
    const int *surf_class,
    const int *surf_boundary,
    const int *surf_partner_idx,
    const float *surf_area,
    const float *surf_tilt_deg,
    const float *surf_cos_tilt,
    const float *surf_sin_tilt,
    const float *surf_azimuth_deg,
    const float *surf_nx,
    const float *surf_ny,
    const float *surf_nz,
    const float *surf_centroid_z,
    const float *surf_height,
    const float *surf_roughness_mult,
    const int *surf_sun_exposed,
    const int *surf_wind_exposed,
    const float *surf_solar_abs_out,
    const float *surf_solar_abs_in,
    const float *surf_eps_in,
    const float *surf_eps_out,
    const float *surf_vf_ground,
    const float *surf_vf_sky,
    const float *surf_vf_sky_ir,
    const float *surf_vf_ground_ir,
    const float *surf_air_sky_split,
    const float *surf_osc_c_const,
    const float *surf_osc_t_const,
    const float *surf_osc_c_out,
    const float *surf_osc_c_zone,
    const float *surf_scon,
    const float *surf_t_norm,
    const float *surf_a_norm,
    const float *surf_tau_diff,
    const float *surf_abs_diff,
    const int *surf_n_modes,
    const float *surf_ctf_out0,
    const float *surf_ctf_cross0,
    const float *surf_ctf_in0,
    const float *surf_lag_oo,
    const float *surf_lag_oi,
    const float *surf_lag_io,
    const float *surf_lag_ii,
    const float *surf_m_decay,
    const float *surf_m_gno,
    const float *surf_m_gni,
    const float *surf_m_goo,
    const float *surf_m_goi,
    const float *surf_m_co,
    const float *surf_m_ci,
    const float *script_f_sigma,
    const float *surf_dif_sky_shdg,
    const unsigned char *surf_sunlit_u8,
    const float *w_t_db,
    const float *w_hum_rat,
    const float *w_pb,
    const float *w_t_sky,
    const float *w_ws,
    const float *w_wd,
    const float *w_wb,
    const float *w_rain,
    const float *w_dni,
    const float *w_dhi,
    const float *w_sx,
    const float *w_sy,
    const float *w_sz,
    const float *w_f1,
    const float *w_f2,
    float *t_surf_in,
    float *t_surf_out,
    float *t_surf_in_prev,
    float *t_surf_out_prev,
    float *t_surf_in_old,
    float *theta1_win,
    float *theta2_win,
    float *h_conv_in,
    float *ctf_const_in,
    float *ctf_const_out,
    float *q_sol_out,
    float *q_sw_in,
    float *q_sol_win,
    float *modal_z,
    float *t_mat,
    float *xmat,
    float *dsxmat,
    float *w_zone,
    float *w_zone_avg,
    float *w_prev,
    float *dsw_prev,
    int *num_sys_last,
    float *hourly_heating_j,
    float *zone_annual_kwh,
    float *zone_temp_rec
) {
    int z = (int)(blockIdx.x * blockDim.x + threadIdx.x);
    if (z >= Z) return;
    int b = zone_bldg_idx[z];

    float d1 = 0.0f, d2 = 0.0f, d3 = 0.0f;
    int cur_hr = step_start / sph;
    float hr_acc = 0.0f;
    for (int step = step_start; step < step_end; ++step) {
        int hr = step / sph;
        if (hr != cur_hr) {
            if (hr_acc > 0.0f) atomicAdd(&hourly_heating_j[b * 8760 + cur_hr], hr_acc);
            cur_hr = hr;
            hr_acc = 0.0f;
        }
        float step_hj = 0.0f;
        gen_step_zone(
            z, step, 0, 0, sph, n_run_steps, has_shading, record_zone_temp,
            site_idx, terrain_idx, site_ground_temp, h_conv_min,
            zone_bldg_idx, zone_surf_offset, zone_sf_offset, zone_volume, zone_centroid_z,
            zone_has_hvac, zone_has_cooling, zone_max_heat_sup_t, zone_min_cool_sup_t,
            zone_heat_sp_hr, zone_cool_sp_hr, zone_gain_conv_hr, zone_gain_rad_hr,
            zone_vent_flow_hr, zone_total_op_aa, zone_floor_area_sw, zone_floor_alpha_eff,
            zone_total_eps_area,
            surf_class, surf_boundary, surf_partner_idx, surf_area, surf_tilt_deg,
            surf_cos_tilt, surf_sin_tilt, surf_azimuth_deg, surf_nx, surf_ny, surf_nz,
            surf_centroid_z, surf_height, surf_roughness_mult, surf_sun_exposed,
            surf_wind_exposed, surf_solar_abs_out, surf_solar_abs_in, surf_eps_in,
            surf_eps_out, surf_vf_ground, surf_vf_sky, surf_vf_sky_ir, surf_vf_ground_ir,
            surf_air_sky_split, surf_osc_c_const, surf_osc_t_const, surf_osc_c_out,
            surf_osc_c_zone, surf_scon, surf_t_norm, surf_a_norm, surf_tau_diff,
            surf_abs_diff, surf_n_modes, surf_ctf_out0, surf_ctf_cross0, surf_ctf_in0,
            surf_lag_oo, surf_lag_oi, surf_lag_io, surf_lag_ii, surf_m_decay, surf_m_gno,
            surf_m_gni, surf_m_goo, surf_m_goi, surf_m_co, surf_m_ci,
            script_f_sigma, surf_dif_sky_shdg, surf_sunlit_u8,
            w_t_db, w_hum_rat, w_pb, w_t_sky, w_ws, w_wd, w_wb, w_rain, w_dni, w_dhi,
            w_sx, w_sy, w_sz, w_f1, w_f2,
            t_surf_in, t_surf_out, t_surf_in_prev, t_surf_out_prev, t_surf_in_old,
            theta1_win, theta2_win, h_conv_in, ctf_const_in, ctf_const_out,
            q_sol_out, q_sw_in, q_sol_win, modal_z,
            t_mat, xmat, dsxmat, w_zone, w_zone_avg, w_prev, dsw_prev, num_sys_last,
            zone_annual_kwh, zone_temp_rec,
            &step_hj, &d1, &d2, &d3
        );
        hr_acc += step_hj;
    }
    if (hr_acc > 0.0f) atomicAdd(&hourly_heating_j[b * 8760 + cur_hr], hr_acc);
}

} // extern "C"
"""


@lru_cache(maxsize=1)
def _compile_general_cuda_module():
    import cupy as cp

    header_src = _HEADER_PATH.read_text(encoding="utf-8")
    full_src = _CUDA_WRAPPER_SRC.replace('#include "general_common.h"', header_src)
    options = ("--use_fast_math",)
    mod = cp.RawModule(code=full_src, options=options)
    return (
        mod.get_function("gen_init_kernel"),
        mod.get_function("gen_warmup_day_kernel"),
        mod.get_function("gen_run_chunk_kernel"),
        mod.get_function("gen_warmup_zone_day_kernel"),
        mod.get_function("gen_run_zone_chunk_kernel"),
    )


@dataclass(frozen=True)
class GeneralSimResult:
    """Outputs of the unified multi-rung CUDA simulation."""

    building_ids: list[str]
    rungs: list[str]
    hourly_heating_j: np.ndarray        # [B, 8760] float64
    annual_heating_kwh: np.ndarray      # [B] float64
    zone_names: list[str]
    zone_annual_kwh: np.ndarray         # [Z] float64
    warmup_days: np.ndarray             # [B] int32
    zone_mean_air_temp_c: np.ndarray | None  # [Z, T] float32 if recorded
    gpu_s: float
    max_launch_s: float


def _pack_site_weather_gpu(sites: list[WeatherSeries]):
    import cupy as cp

    def _stk(attr: str, fallback: float = 0.0) -> cp.ndarray:
        arrs = []
        n = len(sites[0].dry_bulb) if not attr.startswith("warmup_") else len(sites[0].warmup_dry_bulb)
        for s in sites:
            v = getattr(s, attr)
            arrs.append(np.full(n, fallback, dtype=np.float32) if v is None else np.asarray(v, dtype=np.float32))
        return cp.asarray(np.ascontiguousarray(np.stack(arrs, axis=0)))

    run_w = (
        _stk("dry_bulb"), _stk("hum_rat"), _stk("baro_press"), _stk("sky_temp"),
        _stk("wind_speed"), _stk("wind_dir"), _stk("wet_bulb"), _stk("is_rain"), _stk("dni"), _stk("dhi"),
        _stk("solcos_x"), _stk("solcos_y"), _stk("solcos_z"), _stk("perez_f1"), _stk("perez_f2"),
    )
    wu_w = (
        _stk("warmup_dry_bulb"), _stk("warmup_hum_rat"), _stk("warmup_baro_press"), _stk("warmup_sky_temp"),
        _stk("warmup_wind_speed"), _stk("warmup_wind_dir"), _stk("warmup_wet_bulb"), _stk("warmup_is_rain"), _stk("warmup_dni"), _stk("warmup_dhi"),
        _stk("warmup_solcos_x"), _stk("warmup_solcos_y"), _stk("warmup_solcos_z"), _stk("warmup_perez_f1"), _stk("warmup_perez_f2"),
    )
    return run_w, wu_w


def run_general_cuda(
    batch: GeneralBatch,
    site_weathers: list[WeatherSeries],
    *,
    record_zone_temp: bool = False,
    run_chunk_days: int = 1,
    run_chunk_steps: int | None = None,
    block_size: int = 32,
    zone_parallel: bool = False,
) -> GeneralSimResult:
    """Execute a ``GeneralBatch`` on CUDA via the flat-CSR multi-rung kernel."""
    import cupy as cp

    k_init, k_wu, k_run, k_wu_z, k_run_z = _compile_general_cuda_module()
    b_size = batch.batch_size
    z_tot = batch.n_zones_total
    s_tot = batch.n_surfs_total
    sph = batch.steps_per_hour
    steps_per_day = 24 * sph
    n_run_steps = len(site_weathers[0].dry_bulb)

    run_w, wu_w = _pack_site_weather_gpu(site_weathers)

    # Upload static CSR arrays
    g_site_idx = cp.asarray(batch.site_idx)
    g_terr = cp.asarray(batch.terrain_idx)
    g_zoff = cp.asarray(batch.zone_offset)
    g_soff = cp.asarray(batch.surf_offset)
    g_gnd = cp.asarray(batch.site_ground_temp)
    g_wumin = cp.asarray(batch.warmup_min_days)
    g_wumax = cp.asarray(batch.warmup_max_days)
    g_ltol = cp.asarray(batch.loads_conv_tol)
    g_ttol = cp.asarray(batch.temp_conv_tol)
    g_hmin = cp.asarray(batch.h_conv_min)

    g_zbidx = cp.asarray(batch.zone_bldg_idx)
    g_zsoff = cp.asarray(batch.zone_surf_offset)
    g_zsfoff = cp.asarray(batch.zone_sf_offset)
    g_zvol = cp.asarray(batch.zone_volume)
    g_zcz = cp.asarray(batch.zone_centroid_z)
    g_zhvac = cp.asarray(batch.zone_has_hvac)
    g_zcool = cp.asarray(batch.zone_has_cooling)
    g_zmht = cp.asarray(batch.zone_max_heat_supply_t)
    g_zmct = cp.asarray(batch.zone_min_cool_supply_t)
    g_zhsp = cp.asarray(batch.zone_heat_sp_hr)
    g_zcsp = cp.asarray(batch.zone_cool_sp_hr)
    g_zgc = cp.asarray(batch.zone_gain_conv_hr)
    g_zgr = cp.asarray(batch.zone_gain_rad_hr)
    g_zvf = cp.asarray(batch.zone_vent_flow_hr)
    g_zopaa = cp.asarray(batch.zone_total_op_aa)
    g_zflra = cp.asarray(batch.zone_floor_area_sw)
    g_zflralp = cp.asarray(batch.zone_floor_alpha_eff)
    g_zotea = cp.asarray(batch.zone_total_eps_area)

    g_scls = cp.asarray(batch.surf_class)
    g_sbnd = cp.asarray(batch.surf_boundary)
    g_spart = cp.asarray(batch.surf_partner_idx)
    g_sarea = cp.asarray(batch.surf_area)
    g_stilt = cp.asarray(batch.surf_tilt_deg)
    g_scost = cp.asarray(batch.surf_cos_tilt)
    g_ssint = cp.asarray(batch.surf_sin_tilt)
    g_saz = cp.asarray(batch.surf_azimuth_deg)
    g_snx = cp.asarray(batch.surf_nx)
    g_sny = cp.asarray(batch.surf_ny)
    g_snz = cp.asarray(batch.surf_nz)
    g_scz = cp.asarray(batch.surf_centroid_z)
    g_sh = cp.asarray(batch.surf_height)
    g_srm = cp.asarray(batch.surf_roughness_mult)
    g_ssun = cp.asarray(batch.surf_sun_exposed)
    g_swnd = cp.asarray(batch.surf_wind_exposed)
    g_ssao = cp.asarray(batch.surf_solar_abs_out)
    g_ssai = cp.asarray(batch.surf_solar_abs_in)
    g_sepsi = cp.asarray(batch.surf_eps_in)
    g_sepso = cp.asarray(batch.surf_eps_out)
    g_svfg = cp.asarray(batch.surf_vf_ground)
    g_svfs = cp.asarray(batch.surf_vf_sky)
    g_svfsir = cp.asarray(batch.surf_vf_sky_ir)
    g_svfgir = cp.asarray(batch.surf_vf_ground_ir)
    g_sas = cp.asarray(batch.surf_air_sky_split)
    g_socc = cp.asarray(batch.surf_osc_c_const)
    g_soct = cp.asarray(batch.surf_osc_t_const)
    g_soco = cp.asarray(batch.surf_osc_c_out)
    g_socz = cp.asarray(batch.surf_osc_c_zone)
    g_sscon = cp.asarray(batch.surf_scon)
    g_stn = cp.asarray(batch.surf_t_norm)
    g_san = cp.asarray(batch.surf_a_norm)
    g_std = cp.asarray(batch.surf_tau_diff)
    g_sad = cp.asarray(batch.surf_abs_diff)

    g_snm = cp.asarray(batch.surf_n_modes)
    g_sco0 = cp.asarray(batch.surf_ctf_out0)
    g_scy0 = cp.asarray(batch.surf_ctf_cross0)
    g_sci0 = cp.asarray(batch.surf_ctf_in0)
    g_sloo = cp.asarray(batch.surf_lag_oo)
    g_sloi = cp.asarray(batch.surf_lag_oi)
    g_slio = cp.asarray(batch.surf_lag_io)
    g_slii = cp.asarray(batch.surf_lag_ii)
    g_smd = cp.asarray(batch.surf_m_decay)
    g_smgno = cp.asarray(batch.surf_m_gno)
    g_smgni = cp.asarray(batch.surf_m_gni)
    g_smgoo = cp.asarray(batch.surf_m_goo)
    g_smgoi = cp.asarray(batch.surf_m_goi)
    g_smco = cp.asarray(batch.surf_m_co)
    g_smci = cp.asarray(batch.surf_m_ci)
    g_smso = cp.asarray(batch.surf_m_so)
    g_smsi = cp.asarray(batch.surf_m_si)

    g_sfs = cp.asarray(batch.script_f_sigma)
    g_sdsky = cp.asarray(batch.surf_dif_sky_shdg)
    g_ssunlit = cp.asarray(batch.surf_sunlit_u8)

    # Mutable state buffers
    g_tsi = cp.zeros(s_tot, dtype=cp.float32)
    g_tso = cp.zeros(s_tot, dtype=cp.float32)
    g_tsip = cp.zeros(s_tot, dtype=cp.float32)
    g_tsop = cp.zeros(s_tot, dtype=cp.float32)
    g_tsio = cp.zeros(s_tot, dtype=cp.float32)
    g_th1 = cp.zeros(s_tot, dtype=cp.float32)
    g_th2 = cp.zeros(s_tot, dtype=cp.float32)
    g_hci = cp.zeros(s_tot, dtype=cp.float32)
    g_cci = cp.zeros(s_tot, dtype=cp.float32)
    g_cco = cp.zeros(s_tot, dtype=cp.float32)
    g_qso = cp.zeros(s_tot, dtype=cp.float32)
    g_qswi = cp.zeros(s_tot, dtype=cp.float32)
    g_qsw = cp.zeros(s_tot, dtype=cp.float32)
    g_mz = cp.zeros((s_tot, 12), dtype=cp.float32)

    g_tmat = cp.zeros(z_tot, dtype=cp.float32)
    g_xmat = cp.zeros((z_tot, 4), dtype=cp.float32)
    g_dsx = cp.zeros((z_tot, 4), dtype=cp.float32)
    g_wz = cp.zeros(z_tot, dtype=cp.float32)
    g_wza = cp.zeros(z_tot, dtype=cp.float32)
    g_wp = cp.zeros((z_tot, 4), dtype=cp.float32)
    g_dsw = cp.zeros((z_tot, 4), dtype=cp.float32)
    g_nsys = cp.ones(z_tot, dtype=cp.int32)

    g_wustill = cp.ones(b_size, dtype=cp.int32)
    g_wudays = cp.zeros(b_size, dtype=cp.int32)
    g_wumaxt = cp.zeros(b_size, dtype=cp.float32)
    g_wumint = cp.zeros(b_size, dtype=cp.float32)
    g_wumaxh = cp.zeros(b_size, dtype=cp.float32)

    g_hr_j = cp.zeros((b_size, 8760), dtype=cp.float32)
    g_zkwh = cp.zeros(z_tot, dtype=cp.float32)
    g_ztemp = cp.zeros((z_tot, n_run_steps), dtype=cp.float32) if record_zone_temp else cp.zeros(1, dtype=cp.float32)

    grid = ((b_size + block_size - 1) // block_size,)
    block = (block_size,)

    cp.cuda.Stream.null.synchronize()
    t_gpu0 = time.perf_counter()
    max_launch = 0.0

    # 1. Init
    tl0 = time.perf_counter()
    k_init(
        grid, block,
        (
            np.int32(b_size), np.int32(steps_per_day),
            g_site_idx, g_zoff, g_soff, g_sbnd, g_scz, g_snm, g_smso, g_smsi,
            wu_w[0], wu_w[1],
            g_tsi, g_tso, g_tsip, g_tsop, g_th1, g_th2, g_mz,
            g_tmat, g_xmat, g_dsx, g_wz, g_wza, g_wp, g_dsw, g_nsys,
            g_wustill, g_wudays, g_wumaxt, g_wumint, g_wumaxh,
        ),
    )
    cp.cuda.Stream.null.synchronize()
    max_launch = max(max_launch, time.perf_counter() - tl0)

    # 2. Warmup days
    max_wu = int(np.max(batch.warmup_max_days))
    if zone_parallel:
        z_bs = max(block_size, 64)
        z_grid = ((z_tot + z_bs - 1) // z_bs,)
        z_block = (z_bs,)
        g_zwustill = cp.ones(z_tot, dtype=cp.int32)
        g_zwudays = cp.zeros(z_tot, dtype=cp.int32)
        g_zwumaxt = cp.zeros(z_tot, dtype=cp.float32)
        g_zwumint = cp.zeros(z_tot, dtype=cp.float32)
        g_zwumaxh = cp.zeros(z_tot, dtype=cp.float32)
        for day in range(1, max_wu + 1):
            tl0 = time.perf_counter()
            k_wu_z(
                z_grid, z_block,
                (
                    np.int32(z_tot), np.int32(day), np.int32(steps_per_day), np.int32(sph), np.int32(batch.has_shading),
                    g_site_idx, g_terr, g_gnd, g_wumin, g_wumax, g_ltol, g_ttol, g_hmin,
                    g_zbidx, g_zsoff, g_zsfoff, g_zvol, g_zcz, g_zhvac, g_zcool, g_zmht, g_zmct,
                    g_zhsp, g_zcsp, g_zgc, g_zgr, g_zvf, g_zopaa, g_zflra, g_zflralp, g_zotea,
                    g_scls, g_sbnd, g_spart, g_sarea, g_stilt, g_scost, g_ssint, g_saz, g_snx, g_sny, g_snz,
                    g_scz, g_sh, g_srm, g_ssun, g_swnd, g_ssao, g_ssai, g_sepsi, g_sepso,
                    g_svfg, g_svfs, g_svfsir, g_svfgir, g_sas, g_socc, g_soct, g_soco, g_socz,
                    g_sscon, g_stn, g_san, g_std, g_sad,
                    g_snm, g_sco0, g_scy0, g_sci0, g_sloo, g_sloi, g_slio, g_slii,
                    g_smd, g_smgno, g_smgni, g_smgoo, g_smgoi, g_smco, g_smci,
                    g_sfs, g_sdsky, g_ssunlit,
                    *wu_w,
                    g_tsi, g_tso, g_tsip, g_tsop, g_tsio, g_th1, g_th2, g_hci, g_cci, g_cco,
                    g_qso, g_qswi, g_qsw, g_mz,
                    g_tmat, g_xmat, g_dsx, g_wz, g_wza, g_wp, g_dsw, g_nsys,
                    g_zkwh, g_ztemp,
                    g_zwustill, g_zwudays, g_zwumaxt, g_zwumint, g_zwumaxh,
                ),
            )
            cp.cuda.Stream.null.synchronize()
            max_launch = max(max_launch, time.perf_counter() - tl0)
            if int(cp.sum(g_zwustill).get()) == 0:
                break

        # 3. Run period in TDR-safe chunks (zone-parallel)
        chunk_steps = (
            max(1, int(run_chunk_steps))
            if run_chunk_steps is not None
            else max(1, run_chunk_days) * steps_per_day
        )
        for st0 in range(0, n_run_steps, chunk_steps):
            st1 = min(st0 + chunk_steps, n_run_steps)
            tl0 = time.perf_counter()
            k_run_z(
                z_grid, z_block,
                (
                    np.int32(z_tot), np.int32(st0), np.int32(st1), np.int32(sph), np.int32(n_run_steps),
                    np.int32(batch.has_shading), np.int32(1 if record_zone_temp else 0),
                    g_site_idx, g_terr, g_gnd, g_hmin,
                    g_zbidx, g_zsoff, g_zsfoff, g_zvol, g_zcz, g_zhvac, g_zcool, g_zmht, g_zmct,
                    g_zhsp, g_zcsp, g_zgc, g_zgr, g_zvf, g_zopaa, g_zflra, g_zflralp, g_zotea,
                    g_scls, g_sbnd, g_spart, g_sarea, g_stilt, g_scost, g_ssint, g_saz, g_snx, g_sny, g_snz,
                    g_scz, g_sh, g_srm, g_ssun, g_swnd, g_ssao, g_ssai, g_sepsi, g_sepso,
                    g_svfg, g_svfs, g_svfsir, g_svfgir, g_sas, g_socc, g_soct, g_soco, g_socz,
                    g_sscon, g_stn, g_san, g_std, g_sad,
                    g_snm, g_sco0, g_scy0, g_sci0, g_sloo, g_sloi, g_slio, g_slii,
                    g_smd, g_smgno, g_smgni, g_smgoo, g_smgoi, g_smco, g_smci,
                    g_sfs, g_sdsky, g_ssunlit,
                    *run_w,
                    g_tsi, g_tso, g_tsip, g_tsop, g_tsio, g_th1, g_th2, g_hci, g_cci, g_cco,
                    g_qso, g_qswi, g_qsw, g_mz,
                    g_tmat, g_xmat, g_dsx, g_wz, g_wza, g_wp, g_dsw, g_nsys,
                    g_hr_j, g_zkwh, g_ztemp,
                ),
            )
            cp.cuda.Stream.null.synchronize()
            max_launch = max(max_launch, time.perf_counter() - tl0)

        gpu_s = time.perf_counter() - t_gpu0
        hr_j = g_hr_j.get().astype(np.float64)
        z_kwh = g_zkwh.get().astype(np.float64)
        ann_kwh = np.zeros(b_size, dtype=np.float64)
        np.add.at(ann_kwh, batch.zone_bldg_idx, z_kwh)
        zwu = g_zwudays.get().astype(np.int32)
        wu_days = np.zeros(b_size, dtype=np.int32)
        np.maximum.at(wu_days, batch.zone_bldg_idx, zwu)
        z_temp = g_ztemp.get() if record_zone_temp else None
        return GeneralSimResult(
            building_ids=list(batch.building_ids),
            rungs=list(batch.rungs),
            hourly_heating_j=hr_j,
            annual_heating_kwh=ann_kwh,
            zone_names=list(batch.zone_names),
            zone_annual_kwh=z_kwh,
            warmup_days=wu_days,
            zone_mean_air_temp_c=z_temp,
            gpu_s=gpu_s,
            max_launch_s=max_launch,
        )

    for day in range(1, max_wu + 1):
        tl0 = time.perf_counter()
        k_wu(
            grid, block,
            (
                np.int32(b_size), np.int32(day), np.int32(steps_per_day), np.int32(sph), np.int32(batch.has_shading),
                g_site_idx, g_terr, g_zoff, g_soff, g_gnd, g_wumin, g_wumax, g_ltol, g_ttol, g_hmin,
                g_zsoff, g_zsfoff, g_zvol, g_zcz, g_zhvac, g_zcool, g_zmht, g_zmct,
                g_zhsp, g_zcsp, g_zgc, g_zgr, g_zvf, g_zopaa, g_zflra, g_zflralp, g_zotea,
                g_scls, g_sbnd, g_spart, g_sarea, g_stilt, g_scost, g_ssint, g_saz, g_snx, g_sny, g_snz,
                g_scz, g_sh, g_srm, g_ssun, g_swnd, g_ssao, g_ssai, g_sepsi, g_sepso,
                g_svfg, g_svfs, g_svfsir, g_svfgir, g_sas, g_socc, g_soct, g_soco, g_socz,
                g_sscon, g_stn, g_san, g_std, g_sad,
                g_snm, g_sco0, g_scy0, g_sci0, g_sloo, g_sloi, g_slio, g_slii,
                g_smd, g_smgno, g_smgni, g_smgoo, g_smgoi, g_smco, g_smci,
                g_sfs, g_sdsky, g_ssunlit,
                *wu_w,
                g_tsi, g_tso, g_tsip, g_tsop, g_tsio, g_th1, g_th2, g_hci, g_cci, g_cco,
                g_qso, g_qswi, g_qsw, g_mz,
                g_tmat, g_xmat, g_dsx, g_wz, g_wza, g_wp, g_dsw, g_nsys,
                g_hr_j, g_zkwh, g_ztemp,
                g_wustill, g_wudays, g_wumaxt, g_wumint, g_wumaxh,
            ),
        )
        cp.cuda.Stream.null.synchronize()
        max_launch = max(max_launch, time.perf_counter() - tl0)
        if int(cp.sum(g_wustill).get()) == 0:
            break

    # 3. Run period in TDR-safe day/step chunks
    chunk_steps = (
        max(1, int(run_chunk_steps))
        if run_chunk_steps is not None
        else max(1, run_chunk_days) * steps_per_day
    )
    for st0 in range(0, n_run_steps, chunk_steps):
        st1 = min(st0 + chunk_steps, n_run_steps)
        tl0 = time.perf_counter()
        k_run(
            grid, block,
            (
                np.int32(b_size), np.int32(st0), np.int32(st1), np.int32(sph), np.int32(n_run_steps),
                np.int32(batch.has_shading), np.int32(1 if record_zone_temp else 0),
                g_site_idx, g_terr, g_zoff, g_soff, g_gnd, g_hmin,
                g_zsoff, g_zsfoff, g_zvol, g_zcz, g_zhvac, g_zcool, g_zmht, g_zmct,
                g_zhsp, g_zcsp, g_zgc, g_zgr, g_zvf, g_zopaa, g_zflra, g_zflralp, g_zotea,
                g_scls, g_sbnd, g_spart, g_sarea, g_stilt, g_scost, g_ssint, g_saz, g_snx, g_sny, g_snz,
                g_scz, g_sh, g_srm, g_ssun, g_swnd, g_ssao, g_ssai, g_sepsi, g_sepso,
                g_svfg, g_svfs, g_svfsir, g_svfgir, g_sas, g_socc, g_soct, g_soco, g_socz,
                g_sscon, g_stn, g_san, g_std, g_sad,
                g_snm, g_sco0, g_scy0, g_sci0, g_sloo, g_sloi, g_slio, g_slii,
                g_smd, g_smgno, g_smgni, g_smgoo, g_smgoi, g_smco, g_smci,
                g_sfs, g_sdsky, g_ssunlit,
                *run_w,
                g_tsi, g_tso, g_tsip, g_tsop, g_tsio, g_th1, g_th2, g_hci, g_cci, g_cco,
                g_qso, g_qswi, g_qsw, g_mz,
                g_tmat, g_xmat, g_dsx, g_wz, g_wza, g_wp, g_dsw, g_nsys,
                g_hr_j, g_zkwh, g_ztemp,
            ),
        )
        cp.cuda.Stream.null.synchronize()
        max_launch = max(max_launch, time.perf_counter() - tl0)

    gpu_s = time.perf_counter() - t_gpu0
    hr_j = g_hr_j.get().astype(np.float64)
    ann_kwh = np.sum(hr_j, axis=1, dtype=np.float64) / 3.6e6
    z_kwh = g_zkwh.get().astype(np.float64)
    wu_days = g_wudays.get().astype(np.int32)
    z_temp = g_ztemp.get() if record_zone_temp else None

    return GeneralSimResult(
        building_ids=list(batch.building_ids),
        rungs=list(batch.rungs),
        hourly_heating_j=hr_j,
        annual_heating_kwh=ann_kwh,
        zone_names=list(batch.zone_names),
        zone_annual_kwh=z_kwh,
        warmup_days=wu_days,
        zone_mean_air_temp_c=z_temp,
        gpu_s=gpu_s,
        max_launch_s=max_launch,
    )
