import json
from pathlib import Path

import numpy as np

from openubem.gpusim.backends.kernel.pack import (
    CH_T_IN_DT,
    FLAG_IS_INTMASS,
    SS_CTF_IN0,
    SS_CTF_OUT0,
    ST_SURF_DT_IN,
    ZS_T_MAT_DT,
    deduplicate_weather,
    pack,
    unpack_schedules,
    unpack_state,
    unpack_static,
    unpack_weather,
)
from openubem.gpusim.backends.numpy_ref import SURF_INITIAL_TEMP, ZONE_INITIAL_TEMP
from openubem.gpusim.compile import (
    BOUND_DOOR,
    BOUND_OUTDOORS,
    BOUND_WINDOW,
    compile_expidf_batch,
)
from openubem.gpusim.ctf import load_ctf_from_eio
from openubem.gpusim.physics.convection import out_dry_bulb_temp_at
from openubem.gpusim.physics.psychro import KELVIN_CONV, STEFAN_BOLTZMANN
from openubem.gpusim.viewfactors import compute_batch_view_factors
from tests.gpusim.test_cells import (
    CELL1_ID,
    GOLDEN_CELL_IDS,
    GOLDEN_ROOT,
    REP2_SCHED_DIR,
    _load_weather_cached,
)


def _assert_close_f32_roundtrip(
    actual: np.ndarray,
    expected: np.ndarray,
    name: str,
    is_temp: bool = False,
) -> None:
    """Assert packed float32 round-trip error stays within float32 tolerance.

    Args:
        actual: Unpacked float64 values.
        expected: Reference float64 values.
        name: Field name for assertion diagnostics.
        is_temp: If True, enforce absolute ``1e-5 K`` tolerance instead of rel.
    """
    abs_diff = np.abs(actual - expected)
    if is_temp:
        max_abs = float(np.max(abs_diff))
        assert max_abs <= 1.0e-5, (
            f"{name}: max temp round-trip diff {max_abs:.3e} K > 1e-5 K"
        )
        return
    scale = np.maximum(np.abs(expected), 1.0e-12)
    rel_diff = np.where(abs_diff == 0.0, 0.0, abs_diff / scale)
    zero_mask = np.abs(expected) == 0.0
    if np.any(zero_mask):
        max_zero = float(np.max(abs_diff[zero_mask]))
        assert max_zero <= 1.0e-7, (
            f"{name}: non-zero drift {max_zero:.3e} where expected is 0"
        )
    nz_mask = ~zero_mask
    if np.any(nz_mask):
        max_rel = float(np.max(rel_diff[nz_mask]))
        assert max_rel <= 1.0e-6, (
            f"{name}: max rel round-trip diff {max_rel:.3e} > 1e-6"
        )


def _load_pack_test_dirs() -> tuple[Path, ...]:
    """Return golden cell directories plus V10 and V11 extra-site variants.

    Returns:
        Tuple of 5 fixture directory paths.
    """
    cells = tuple(GOLDEN_ROOT / cid for cid in GOLDEN_CELL_IDS)
    v10 = GOLDEN_ROOT / "variants" / f"{CELL1_ID}__V10"
    v11 = GOLDEN_ROOT / "variants" / f"{CELL1_ID}__V11"
    return cells + (v10, v11)


def test_stage_c_pack_roundtrip_and_site_mapping() -> None:
    """Verify float32 SoA packing round-trip, site indexing, and byte footprint."""
    dirs = _load_pack_test_dirs()
    expidfs = [d / "eplusout.expidf" for d in dirs]
    cell_ids = [d.name for d in dirs]
    metas = [
        json.loads((d / "meta.json").read_text(encoding="utf-8")) for d in dirs
    ]
    epw_names = [str(m["epw_file_name"]) for m in metas]
    weathers_in = [_load_weather_cached(name) for name in epw_names]

    batch = compile_expidf_batch(
        expidfs,
        cell_ids=cell_ids,
        epw_ids=epw_names,
        schedule_dirs=[REP2_SCHED_DIR],
    )
    ctf = load_ctf_from_eio(steps_per_hour=batch.steps_per_hour)

    weather_by_site, site_index = deduplicate_weather(weathers_in, batch.batch_size)
    assert len(weather_by_site) == len(set(epw_names)) == 5
    for b_idx, w_src in enumerate(weathers_in):
        assert weather_by_site[int(site_index[b_idx])] is w_src

    packed = pack(batch, weather_by_site, site_index, ctf)

    assert packed.batch_size == 5
    assert packed.n_sites == 5
    assert packed.bldg_f.dtype == np.float32
    assert packed.surf_f.dtype == np.float32
    assert packed.weather_run.dtype == np.float32
    assert packed.sched_gain_w.dtype == np.float32
    assert packed.state_zone_f.dtype == np.float32
    assert packed.state_surf_f.dtype == np.float32
    assert packed.state_ctf_hist.dtype == np.float32
    assert packed.hourly_heating_j.dtype == np.float32
    assert packed.bldg_i.dtype == np.int32
    assert packed.surf_flags.dtype == np.int32
    assert packed.state_num_sys_last.dtype == np.int32

    assert np.isclose(
        float(packed.state_zone_f[ZS_T_MAT_DT, 0]),
        ZONE_INITIAL_TEMP - 20.0,
        atol=1.0e-6,
    )
    assert np.isclose(
        float(packed.state_surf_f[ST_SURF_DT_IN, 0, 0]),
        SURF_INITIAL_TEMP - 20.0,
        atol=1.0e-6,
    )
    assert np.isclose(
        float(packed.state_ctf_hist[CH_T_IN_DT, 0, 0, 0]),
        SURF_INITIAL_TEMP - 20.0,
        atol=1.0e-6,
    )

    st = unpack_static(packed)
    assert np.array_equal(st["site_index"], site_index)
    assert np.array_equal(st["surf_mask"], batch.surf_mask)
    assert np.array_equal(st["warmup_min_days"], batch.warmup_min_days)
    assert np.array_equal(st["warmup_max_days"], batch.warmup_max_days)

    bldg_rel_fields = (
        "zone_volume",
        "zone_floor_area",
        "zone_centroid_z",
        "zone_vent_ach",
        "zone_vent_flow_m3s",
        "zone_max_heat_supply_humrat",
        "h_conv_min",
        "h_conv_max",
        "loads_conv_tol",
        "temp_conv_tol",
        "site_elevation",
    )
    for fname in bldg_rel_fields:
        _assert_close_f32_roundtrip(st[fname], getattr(batch, fname), fname)

    bldg_temp_fields = (
        "zone_heat_setpoint",
        "zone_cool_setpoint",
        "zone_max_heat_supply_temp",
    )
    for fname in bldg_temp_fields:
        _assert_close_f32_roundtrip(
            st[fname], getattr(batch, fname), fname, is_temp=True
        )

    surf_rel_fields = (
        "surf_area",
        "surf_cos_tilt",
        "surf_sin_tilt",
        "surf_tilt_deg",
        "surf_centroid_z",
        "surf_u_value",
        "surf_osc_c_const",
        "surf_osc_c_out",
        "surf_osc_c_zone",
        "surf_vf_sky_ir",
        "surf_vf_ground_ir",
        "surf_air_sky_rad_split",
        "surf_eps_in",
        "surf_eps_out",
        "surf_height",
    )
    for fname in surf_rel_fields:
        _assert_close_f32_roundtrip(st[fname], getattr(batch, fname), fname)
    _assert_close_f32_roundtrip(
        st["surf_osc_t_const"],
        batch.surf_osc_t_const,
        "surf_osc_t_const",
        is_temp=True,
    )

    _, script_f = compute_batch_view_factors(batch)
    _assert_close_f32_roundtrip(
        st["script_f_sigma"],
        script_f * STEFAN_BOLTZMANN,
        "script_f_sigma",
    )

    wu = unpack_weather(packed)
    for k_idx, w_src in enumerate(weather_by_site):
        _assert_close_f32_roundtrip(
            wu["dry_bulb"][k_idx], w_src.dry_bulb, f"site[{k_idx}].dry_bulb", True
        )
        _assert_close_f32_roundtrip(
            wu["sky_temp"][k_idx], w_src.sky_temp, f"site[{k_idx}].sky_temp", True
        )
        _assert_close_f32_roundtrip(
            wu["hum_rat"][k_idx], w_src.hum_rat, f"site[{k_idx}].hum_rat"
        )
        _assert_close_f32_roundtrip(
            wu["baro_press"][k_idx], w_src.baro_press, f"site[{k_idx}].baro_press"
        )
        _assert_close_f32_roundtrip(
            wu["warmup_dry_bulb"][k_idx],
            w_src.warmup_dry_bulb,
            f"site[{k_idx}].warmup_dry_bulb",
            True,
        )
        _assert_close_f32_roundtrip(
            wu["warmup_sky_temp"][k_idx],
            w_src.warmup_sky_temp,
            f"site[{k_idx}].warmup_sky_temp",
            True,
        )
        _assert_close_f32_roundtrip(
            wu["warmup_hum_rat"][k_idx],
            w_src.warmup_hum_rat,
            f"site[{k_idx}].warmup_hum_rat",
        )
        _assert_close_f32_roundtrip(
            wu["warmup_baro_press"][k_idx],
            w_src.warmup_baro_press,
            f"site[{k_idx}].warmup_baro_press",
        )

    sched = unpack_schedules(packed)
    _assert_close_f32_roundtrip(sched, batch.zone_gain_hourly_w, "zone_gain_hourly_w")

    state = unpack_state(packed)
    db0 = np.asarray(
        [weathers_in[b].warmup_dry_bulb[0] for b in range(batch.batch_size)],
        dtype=np.float64,
    )
    w0 = np.asarray(
        [weathers_in[b].warmup_hum_rat[0] for b in range(batch.batch_size)],
        dtype=np.float64,
    )
    t_out_air0 = out_dry_bulb_temp_at(db0[:, None], batch.surf_centroid_z, xp=np)
    is_ext_env = (
        (batch.surf_boundary == BOUND_OUTDOORS)
        | (batch.surf_boundary == BOUND_DOOR)
        | (batch.surf_boundary == BOUND_WINDOW)
    ) & batch.surf_mask
    expected_tout = np.where(is_ext_env, t_out_air0, SURF_INITIAL_TEMP)

    _assert_close_f32_roundtrip(
        state["t_mat"],
        np.full(batch.batch_size, ZONE_INITIAL_TEMP),
        "state.t_mat",
        True,
    )
    _assert_close_f32_roundtrip(state["w_zone"], w0, "state.w_zone")
    _assert_close_f32_roundtrip(
        state["t_surf_out"], expected_tout, "state.t_surf_out", True
    )
    _assert_close_f32_roundtrip(
        state["theta1_win"],
        expected_tout + KELVIN_CONV,
        "state.theta1_win",
        True,
    )

    m = packed.n_ctf_hist
    im_indices = np.where((packed.surf_flags[:, 0] & FLAG_IS_INTMASS) != 0)[0]
    assert im_indices.size >= 1
    im_s = int(im_indices[0])
    ctf_out_full = np.concatenate(
        [
            packed.surf_f[SS_CTF_OUT0, im_s : im_s + 1, 0],
            packed.ctf_vec[0:m],
        ]
    ).astype(np.float64)
    ctf_in_full = np.concatenate(
        [
            packed.surf_f[SS_CTF_IN0, im_s : im_s + 1, 0],
            packed.ctf_vec[2 * m : 3 * m],
        ]
    ).astype(np.float64)
    ctf_flux_f64 = packed.ctf_vec[3 * m : 4 * m].astype(np.float64)
    assert abs(float(np.sum(ctf_out_full)) - float(np.sum(ctf.outside))) <= 5.0e-7
    assert abs(float(np.sum(ctf_in_full)) - float(np.sum(ctf.inside))) <= 5.0e-7
    assert abs(float(np.sum(ctf_flux_f64)) - float(np.sum(ctf.flux))) <= 5.0e-7

    bldg_bytes_per = packed.building_bytes() / float(packed.batch_size)
    total_bytes_per = packed.bytes_per_building()
    weather_bytes_per_site = (
        packed.weather_run.nbytes + packed.weather_wu.nbytes
    ) / float(packed.n_sites)
    print(
        f"T01 Pack: B={packed.batch_size}, S={packed.max_surfaces}, "
        f"K={packed.n_sites}, M={packed.n_ctf_hist} | "
        f"building_bytes_per_bldg={bldg_bytes_per:.1f} B, "
        f"amortized_total_bytes_per_bldg={total_bytes_per:.1f} B, "
        f"weather_bytes_per_site={weather_bytes_per_site:.1f} B"
    )
