from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest

from openubem.gpusim.compile import (
    BOUND_DOOR,
    BOUND_OSC,
    BOUND_OUTDOORS,
    BOUND_WINDOW,
    BatchSpec,
    compile_expidf_batch,
)
from openubem.gpusim.physics.convection import (
    calc_inside_convection_opaque,
    calc_outside_convection_doe2,
    calc_outside_rad_coeffs,
    out_dry_bulb_temp_at,
)
from openubem.gpusim.physics.lwr import calc_interior_rad_exchange
from openubem.gpusim.physics.psychro import KELVIN_CONV, STEFAN_BOLTZMANN
from openubem.gpusim.physics.surface_hb import calc_osc_outside_temp
from openubem.gpusim.physics.window import (
    simple_glazing_layer_conductance,
    solve_simple_window,
)
from openubem.gpusim.physics.zone_air import calc_ventilation_mcp, predict_zone_load
from openubem.gpusim.schedules import expand_hourly_to_timestep
from openubem.gpusim.viewfactors import compute_batch_view_factors

REPO_ROOT = Path(__file__).resolve().parents[2]
REP2_SCHED_DIR = (
    REPO_ROOT / "openubem/outputs/eu_certified_rerun_2026-08-28/rep2/schedules"
)
GOLDEN_ROOT = REPO_ROOT / "tests/fixtures/gpusim/golden"

GOLDEN_CELL_IDS: tuple[str, ...] = (
    "it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100",
    "uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000",
    "es__ES.ME.AB.01.Gen.ReEx.001.001__f000",
)

P999_GATE: float = 1.0e-4
MAX_GATE: float = 1.0e-3


@pytest.fixture(scope="module")
def golden_context() -> tuple[BatchSpec, np.ndarray, list[dict[str, np.ndarray]]]:
    """Load compiled batch, ScriptF*sigma, and timestep tables for 3 golden cells.

    Returns:
        Tuple ``(batch, script_f_sigma, tables)``.
    """
    paths = [GOLDEN_ROOT / cid / "eplusout.expidf" for cid in GOLDEN_CELL_IDS]
    batch = compile_expidf_batch(
        paths,
        cell_ids=list(GOLDEN_CELL_IDS),
        schedule_dirs=[REP2_SCHED_DIR],
    )
    _, script_f = compute_batch_view_factors(batch)
    script_f_sigma = script_f * STEFAN_BOLTZMANN
    tables: list[dict[str, np.ndarray]] = []
    for cid in GOLDEN_CELL_IDS:
        tbl = pq.read_table(GOLDEN_ROOT / cid / "timestep.parquet")
        tables.append({name: tbl[name].to_numpy() for name in tbl.column_names})
    return batch, script_f_sigma, tables


def _assert_rel_gate(label: str, rel_err: np.ndarray) -> tuple[float, float]:
    """Assert T04 p99.9 and max relative difference gates on an error vector.

    Args:
        label: Check and cell label for diagnostic output.
        rel_err: Non-negative relative error array.

    Returns:
        Tuple ``(p999, max_err)``.
    """
    p999 = float(np.percentile(rel_err, 99.9))
    max_err = float(np.max(rel_err))
    assert p999 <= P999_GATE, f"{label} p99.9={p999:.3e} > {P999_GATE}"
    assert max_err <= MAX_GATE, f"{label} max={max_err:.3e} > {MAX_GATE}"
    return p999, max_err


def test_check1_inside_tarp_convection_opaque(
    golden_context: tuple[BatchSpec, np.ndarray, list[dict[str, np.ndarray]]],
) -> None:
    """Verify opaque inside TARP convection coefficient across all golden steps."""
    batch, _, tables = golden_context
    for bi, cid in enumerate(GOLDEN_CELL_IDS):
        cols = tables[bi]
        t_mat = cols["EU_CELL_ZONE:Zone Air Temperature [C](TimeStep)"]
        n_s = int(np.sum(batch.surf_mask[bi]))
        errs: list[np.ndarray] = []
        for si in range(n_s):
            if batch.surf_boundary[bi, si] == BOUND_WINDOW:
                continue
            nm = batch.surf_names[bi][si]
            ts = cols[f"{nm}:Surface Inside Face Temperature [C](TimeStep)"]
            hc_ref = cols[
                f"{nm}:Surface Inside Face Convection "
                "Heat Transfer Coefficient [W/m2-K](TimeStep)"
            ]
            hc_pred = calc_inside_convection_opaque(
                ts[:-1],
                t_mat[:-1],
                batch.surf_cos_tilt[bi, si],
                batch.h_conv_min[bi],
            )
            rel = np.abs(hc_pred - hc_ref[1:]) / np.maximum(np.abs(hc_ref[1:]), 1.0e-12)
            errs.append(rel)
        _assert_rel_gate(f"check1:{cid}", np.concatenate(errs))


def test_check2_outdoor_face_coefficients(
    golden_context: tuple[BatchSpec, np.ndarray, list[dict[str, np.ndarray]]],
) -> None:
    """Verify outside convection and sky/air/ground radiation coefficients."""
    batch, _, tables = golden_context
    for bi, cid in enumerate(GOLDEN_CELL_IDS):
        cols = tables[bi]
        t_out_site = cols[
            "Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)"
        ]
        t_sky = cols["Environment:Site Sky Temperature [C](TimeStep)"]
        n_s = int(np.sum(batch.surf_mask[bi]))
        errs: list[np.ndarray] = []
        for si in range(n_s):
            bnd = int(batch.surf_boundary[bi, si])
            if bnd not in (BOUND_OUTDOORS, BOUND_DOOR, BOUND_WINDOW):
                continue
            nm = batch.surf_names[bi][si]
            ts_out = cols[f"{nm}:Surface Outside Face Temperature [C](TimeStep)"]
            t_air_s = out_dry_bulb_temp_at(
                t_out_site[1:], batch.surf_centroid_z[bi, si]
            )
            hc_pred = calc_outside_convection_doe2(
                ts_out[:-1],
                t_air_s,
                batch.surf_cos_tilt[bi, si],
            )
            hsky_pred, hgrd_pred, hair_pred = calc_outside_rad_coeffs(
                ts_out[:-1],
                t_air_s,
                t_sky[1:],
                batch.surf_eps_out[bi, si],
                batch.surf_vf_sky_ir[bi, si],
                batch.surf_vf_ground_ir[bi, si],
                batch.surf_air_sky_rad_split[bi, si],
            )
            pairs = [
                (
                    hc_pred,
                    f"{nm}:Surface Outside Face Convection "
                    "Heat Transfer Coefficient [W/m2-K](TimeStep)",
                ),
                (
                    hsky_pred,
                    f"{nm}:Surface Outside Face Thermal Radiation to Sky "
                    "Heat Transfer Coefficient [W/m2-K](TimeStep)",
                ),
            ]
            if bnd != BOUND_WINDOW:
                pairs.extend(
                    [
                        (
                            hair_pred,
                            f"{nm}:Surface Outside Face Thermal Radiation to Air "
                            "Heat Transfer Coefficient [W/m2-K](TimeStep)",
                        ),
                        (
                            hgrd_pred,
                            f"{nm}:Surface Outside Face Thermal Radiation to Ground "
                            "Heat Transfer Coefficient [W/m2-K](TimeStep)",
                        ),
                    ]
                )
            else:
                _, _, hair_win_curr = calc_outside_rad_coeffs(
                    ts_out[1:],
                    t_air_s,
                    t_sky[1:],
                    batch.surf_eps_out[bi, si],
                    batch.surf_vf_sky_ir[bi, si],
                    batch.surf_vf_ground_ir[bi, si],
                    batch.surf_air_sky_rad_split[bi, si],
                )
                pairs.append(
                    (
                        -hair_win_curr,
                        f"{nm}:Surface Outside Face Thermal Radiation to Air "
                        "Heat Transfer Coefficient [W/m2-K](TimeStep)",
                    )
                )
            for pred, col_key in pairs:
                if col_key in cols:
                    ref = cols[col_key][1:]
                    rel = np.abs(pred - ref) / np.maximum(np.abs(ref), 1.0e-12)
                    errs.append(rel)
        _assert_rel_gate(f"check2:{cid}", np.concatenate(errs))


def test_check3_window_inside_temp_and_convection_gain(
    golden_context: tuple[BatchSpec, np.ndarray, list[dict[str, np.ndarray]]],
) -> None:
    """Verify window inside-face temperature and glazing convection gain."""
    batch, script_f_sigma, tables = golden_context
    for bi, cid in enumerate(GOLDEN_CELL_IDS):
        cols = tables[bi]
        t_out_site = cols[
            "Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)"
        ]
        pb = cols["Environment:Site Outdoor Air Barometric Pressure [Pa](TimeStep)"]
        t_sky = cols["Environment:Site Sky Temperature [C](TimeStep)"]
        t_mat = cols["EU_CELL_ZONE:Zone Air Temperature [C](TimeStep)"]
        w_zone = cols["EU_CELL_ZONE:Zone Air Humidity Ratio [](TimeStep)"]

        n_s = int(np.sum(batch.surf_mask[bi]))
        names = batch.surf_names[bi][:n_s]
        n_steps = len(t_out_site)
        ts_in = np.stack(
            [
                cols[f"{nm}:Surface Inside Face Temperature [C](TimeStep)"]
                for nm in names
            ],
            axis=1,
        )
        ts_out = np.stack(
            [
                cols[f"{nm}:Surface Outside Face Temperature [C](TimeStep)"]
                for nm in names
            ],
            axis=1,
        )
        q_conv = np.stack(
            [
                cols[
                    f"{nm}:Surface Inside Face Convection Heat Gain Rate [W](TimeStep)"
                ]
                for nm in names
            ],
            axis=1,
        )

        is_win = batch.surf_boundary[bi, :n_s] == BOUND_WINDOW
        mask_s = np.ones((n_steps - 1, n_s), dtype=bool)
        sf_sub = script_f_sigma[bi, :n_s, :n_s][None, :, :]
        eps_sub = batch.surf_eps_in[bi, :n_s][None, :]
        _, rmir_all = calc_interior_rad_exchange(
            ts_in[:-1], sf_sub, eps_sub, is_win[None, :], mask_s
        )

        t_errs: list[np.ndarray] = []
        q_errs: list[np.ndarray] = []
        for wi in np.where(is_win)[0]:
            nm = names[wi]
            t_air_w = out_dry_bulb_temp_at(
                t_out_site[1:], batch.surf_centroid_z[bi, wi]
            )
            h_out_w = cols[
                f"{nm}:Surface Outside Face Convection "
                "Heat Transfer Coefficient [W/m2-K](TimeStep)"
            ][1:]
            scon_w = float(simple_glazing_layer_conductance(batch.surf_u_value[bi, wi]))
            tin_p, _, _, qconv_pa, _ = solve_simple_window(
                t_in_c=t_mat[:-1],
                t_out_c=t_air_w,
                t_sky_c=t_sky[1:],
                hum_rat=w_zone[:-1],
                baro_press=pb[1:],
                h_out=h_out_w,
                rmir=rmir_all[:, wi],
                scon=np.full(n_steps - 1, scon_w),
                eps_out=np.full(n_steps - 1, batch.surf_eps_out[bi, wi]),
                eps_in=np.full(n_steps - 1, batch.surf_eps_in[bi, wi]),
                vf_sky_ir=np.full(n_steps - 1, batch.surf_vf_sky_ir[bi, wi]),
                vf_ground_ir=np.full(n_steps - 1, batch.surf_vf_ground_ir[bi, wi]),
                air_sky_split=np.full(
                    n_steps - 1, batch.surf_air_sky_rad_split[bi, wi]
                ),
                height=np.full(n_steps - 1, batch.surf_height[bi, wi]),
                tilt_deg=np.full(n_steps - 1, batch.surf_tilt_deg[bi, wi]),
                sin_tilt=np.full(n_steps - 1, batch.surf_sin_tilt[bi, wi]),
                h_min=np.full(n_steps - 1, batch.h_conv_min[bi]),
                theta1_init=ts_out[:-1, wi] + KELVIN_CONV,
                theta2_init=ts_in[:-1, wi] + KELVIN_CONV,
                win_mask=np.ones(n_steps - 1, dtype=bool),
            )
            t_ref = ts_in[1:, wi]
            t_rel = np.abs(tin_p - t_ref) / np.maximum(
                np.abs(t_ref + KELVIN_CONV), 1.0e-12
            )
            t_errs.append(t_rel)

            q_pred = -batch.surf_area[bi, wi] * qconv_pa
            q_ref = q_conv[1:, wi]
            q_rel = np.abs(q_pred - q_ref) / np.maximum(np.abs(q_ref), 1.0)
            q_errs.append(q_rel)

        _assert_rel_gate(f"check3_tin:{cid}", np.concatenate(t_errs))
        _assert_rel_gate(f"check3_qconv:{cid}", np.concatenate(q_errs))


def test_check4_osc_outside_face_temp(
    golden_context: tuple[BatchSpec, np.ndarray, list[dict[str, np.ndarray]]],
) -> None:
    """Verify OSC outside-face temperature from previous zone temperature."""
    batch, _, tables = golden_context
    for bi, cid in enumerate(GOLDEN_CELL_IDS):
        cols = tables[bi]
        t_out_site = cols[
            "Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)"
        ]
        t_mat = cols["EU_CELL_ZONE:Zone Air Temperature [C](TimeStep)"]
        n_s = int(np.sum(batch.surf_mask[bi]))
        errs: list[np.ndarray] = []
        for si in range(n_s):
            if batch.surf_boundary[bi, si] != BOUND_OSC:
                continue
            nm = batch.surf_names[bi][si]
            ts_out = cols[f"{nm}:Surface Outside Face Temperature [C](TimeStep)"]
            t_air_s = out_dry_bulb_temp_at(
                t_out_site[1:], batch.surf_centroid_z[bi, si]
            )
            pred = calc_osc_outside_temp(
                t_mat[:-1],
                t_air_s,
                batch.surf_osc_c_const[bi, si],
                batch.surf_osc_t_const[bi, si],
                batch.surf_osc_c_out[bi, si],
                batch.surf_osc_c_zone[bi, si],
            )
            rel = np.abs(pred - ts_out[1:]) / np.maximum(
                np.abs(ts_out[1:] + KELVIN_CONV), 1.0e-12
            )
            errs.append(rel)
        _assert_rel_gate(f"check4:{cid}", np.concatenate(errs))


def test_check5_zone_predictor_ideal_loads(
    golden_context: tuple[BatchSpec, np.ndarray, list[dict[str, np.ndarray]]],
) -> None:
    """Verify zone predictor sensible heating rate against golden ideal loads."""
    batch, _, tables = golden_context
    for bi, cid in enumerate(GOLDEN_CELL_IDS):
        cols = tables[bi]
        t_out_site = cols[
            "Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)"
        ]
        w_out = cols[
            "Environment:Site Outdoor Air Humidity Ratio [kgWater/kgDryAir](TimeStep)"
        ]
        pb = cols["Environment:Site Outdoor Air Barometric Pressure [Pa](TimeStep)"]
        t_mat = cols["EU_CELL_ZONE:Zone Air Temperature [C](TimeStep)"]
        t_ztav = cols["EU_CELL_ZONE:Zone Mean Air Temperature [C](TimeStep)"]
        w_zone = cols["EU_CELL_ZONE:Zone Air Humidity Ratio [](TimeStep)"]
        q_ref_all = cols[
            "EU_CELL_ZONE IDEAL LOADS AIR SYSTEM:"
            "Zone Ideal Loads Zone Sensible Heating Rate [W](TimeStep)"
        ]

        n_s = int(np.sum(batch.surf_mask[bi]))
        names = batch.surf_names[bi][:n_s]
        ts_in = np.stack(
            [
                cols[f"{nm}:Surface Inside Face Temperature [C](TimeStep)"]
                for nm in names
            ],
            axis=1,
        )
        hc_in = np.stack(
            [
                cols[
                    f"{nm}:Surface Inside Face Convection "
                    "Heat Transfer Coefficient [W/m2-K](TimeStep)"
                ]
                for nm in names
            ],
            axis=1,
        )
        areas = batch.surf_area[bi, :n_s]
        sum_ha = np.sum(hc_in[3:] * areas[None, :], axis=1)
        sum_hat = np.sum(hc_in[3:] * areas[None, :] * ts_in[3:], axis=1)

        t_out_z = out_dry_bulb_temp_at(t_out_site[3:], batch.zone_centroid_z[bi])
        mcpv, _, mcptv = calc_ventilation_mcp(
            batch.zone_vent_flow_m3s[bi],
            t_out_z,
            w_out[3:],
            pb[3:],
        )
        gain_ts = expand_hourly_to_timestep(
            batch.zone_gain_hourly_w[bi],
            steps_per_hour=batch.steps_per_hour,
        )[3:]
        ztm = np.stack([t_ztav[2:-1], t_ztav[1:-2], t_ztav[0:-3]], axis=1)
        dt_sec = 3600.0 / float(batch.steps_per_hour)
        q_load_h, _, _ = predict_zone_load(
            t_zone_mat=t_mat[2:-1],
            hum_rat=w_zone[2:-1],
            baro_press=pb[3:],
            zone_vol=batch.zone_volume[bi],
            dt_sys_sec=dt_sec,
            ztm=ztm,
            sum_ha=sum_ha,
            sum_hat_surf=sum_hat,
            sum_mcp=mcpv,
            sum_mcpt=mcptv,
            sum_int_gain=gain_ts,
            heat_setpoint=batch.zone_heat_setpoint[bi],
            cool_setpoint=batch.zone_cool_setpoint[bi],
        )
        q_pred = np.maximum(q_load_h, 0.0)
        q_ref = q_ref_all[3:]
        active = (q_ref > 1.0) | (q_pred > 1.0)
        rel = np.abs(q_pred[active] - q_ref[active]) / np.maximum(
            np.abs(q_ref[active]), 1.0
        )
        _assert_rel_gate(f"check5:{cid}", rel)
