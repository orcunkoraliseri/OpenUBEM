import numpy as np

from openubem.gpusim._rust_compat import (
    dispatch_gpusim_rust,
    load_gpusim_rust_module,
)
from openubem.gpusim.compile import BatchSpec, SURF_FLOOR, SURF_INTMASS

SAME_ANGLE_LIMIT_DEG = 10.0
PRIMARY_CONVERGENCE = 0.001
DIFFERENCE_CONVERGENCE = 0.00001
MAX_FIX_ITERATIONS = 400
MAX_EMISS_LIMIT = 0.99999


def calc_approximate_view_factors(
    areas: np.ndarray,
    azimuths: np.ndarray,
    tilts: np.ndarray,
    surf_classes: np.ndarray,
) -> np.ndarray:
    """HeatBalanceIntRadExchange.cc::CalcApproximateViewFactors"""
    def _py() -> np.ndarray:
        n_surf = len(areas)
        f_mat = np.zeros((n_surf, n_surf), dtype=np.float64)

        for i in range(n_surf):
            is_floor_i = surf_classes[i] == SURF_FLOOR
            is_im_i = surf_classes[i] == SURF_INTMASS
            zone_area = 0.0
            can_see = np.zeros(n_surf, dtype=bool)
            for j in range(n_surf):
                is_floor_j = surf_classes[j] == SURF_FLOOR
                if i == j or (is_floor_i and is_floor_j):
                    continue
                is_im_j = surf_classes[j] == SURF_INTMASS
                az_diff = abs(float(azimuths[i]) - float(azimuths[j]))
                tilt_diff = abs(float(tilts[i]) - float(tilts[j]))
                if (
                    is_im_j
                    or is_im_i
                    or is_floor_j
                    or is_floor_i
                    or (
                        az_diff > SAME_ANGLE_LIMIT_DEG
                        and az_diff < 360.0 - SAME_ANGLE_LIMIT_DEG
                    )
                    or tilt_diff > SAME_ANGLE_LIMIT_DEG
                ):
                    can_see[j] = True
                    zone_area += float(areas[j])
            if zone_area > 0.0:
                f_mat[i, can_see] = areas[can_see] / zone_area
        return f_mat

    rust = load_gpusim_rust_module()
    rust_fn = (
        (
            lambda: rust.idf_calc_approximate_view_factors(
                np.ascontiguousarray(areas, dtype=np.float64),
                np.ascontiguousarray(azimuths, dtype=np.float64),
                np.ascontiguousarray(tilts, dtype=np.float64),
                np.ascontiguousarray(surf_classes, dtype=np.int32),
            )
        )
        if rust is not None and hasattr(rust, "idf_calc_approximate_view_factors")
        else None
    )
    return dispatch_gpusim_rust(
        "openubem.gpusim.viewfactors.calc_approximate_view_factors",
        _py,
        rust_fn,
        bucket="B2",
    )


def fix_view_factors(areas: np.ndarray, f_approx: np.ndarray) -> np.ndarray:
    """HeatBalanceIntRadExchange.cc::FixViewFactors"""
    def _py() -> np.ndarray:
        n_surf = len(areas)
        f_out = f_approx.astype(np.float64, copy=True)
        orig_check = abs(float(np.sum(f_out)) - float(n_surf))

        fixed_af = f_out.copy()
        total_area = float(np.sum(areas))
        largest_area = float(np.max(areas))

        if largest_area > 0.99 * (total_area - largest_area) and n_surf > 3:
            largest_idx = int(np.argmax(areas))
            fixed_af[largest_idx, largest_idx] = min(0.9, 1.2 * largest_area / total_area)

        af = fixed_af * areas[:, None]
        fixed_af = 0.5 * (af + af.T)

        if n_surf <= 3:
            fixed_f = fixed_af / areas[:, None]
            row_sum = float(np.sum(fixed_f))
            if row_sum > float(n_surf) + 0.01:
                max_row = float(np.max(np.sum(fixed_f, axis=1)))
                if max_row >= 1.0:
                    fixed_f *= 1.0 / max_row
            return fixed_f

        convrg_old = 10.0
        num_iter = 0
        fixed_f = np.zeros_like(f_out)

        while True:
            num_iter += 1
            for i in range(n_surf):
                row_sum_af = float(np.sum(fixed_af[i, :]))
                if abs(row_sum_af) > 1.0e-10:
                    row_coef = float(areas[i]) / row_sum_af
                else:
                    row_coef = 1.0
                fixed_af[i, :] *= row_coef

            fixed_af = 0.5 * (fixed_af + fixed_af.T)
            fixed_f = fixed_af / areas[:, None]
            tiny = np.abs(fixed_f) < 1.0e-10
            fixed_f[tiny] = 0.0
            fixed_af[tiny] = 0.0

            convrg_new = abs(float(np.sum(fixed_f)) - float(n_surf))
            if (
                abs(convrg_old - convrg_new) < DIFFERENCE_CONVERGENCE
                or convrg_new <= PRIMARY_CONVERGENCE
            ):
                break
            convrg_old = convrg_new

            if num_iter > MAX_FIX_ITERATIONS:
                fixed_af = 0.5 * (fixed_af + fixed_af.T)
                fixed_f = fixed_af / areas[:, None]
                fixed_check = abs(float(np.sum(fixed_f)) - float(n_surf))
                if fixed_check < orig_check:
                    return fixed_f
                return f_out

        fixed_check = convrg_new
        if fixed_check < orig_check:
            return fixed_f
        if abs(float(np.sum(fixed_f)) - float(n_surf)) < PRIMARY_CONVERGENCE:
            return fixed_f
        return f_out

    rust = load_gpusim_rust_module()
    rust_fn = (
        (
            lambda: rust.idf_fix_view_factors(
                np.ascontiguousarray(areas, dtype=np.float64),
                np.ascontiguousarray(f_approx, dtype=np.float64),
            )
        )
        if rust is not None and hasattr(rust, "idf_fix_view_factors")
        else None
    )
    return dispatch_gpusim_rust(
        "openubem.gpusim.viewfactors.fix_view_factors",
        _py,
        rust_fn,
        bucket="B2",
    )


def calc_script_f(
    areas: np.ndarray, f_mat: np.ndarray, emiss: np.ndarray
) -> np.ndarray:
    """HeatBalanceIntRadExchange.cc::CalcScriptF"""
    def _py() -> np.ndarray:
        n_surf = len(areas)
        eps = np.minimum(emiss.astype(np.float64, copy=True), MAX_EMISS_LIMIT)

        c_mat = areas[:, None] * f_mat.T
        inv_one_minus_eps = 1.0 / (1.0 - eps)
        excite = -eps * areas * inv_one_minus_eps
        idx = np.arange(n_surf)
        c_mat[idx, idx] -= areas * inv_one_minus_eps

        c_inv = np.linalg.inv(c_mat)
        j_mat = c_inv * excite[None, :]

        eps_fac = eps * inv_one_minus_eps
        script_f_raw = eps_fac[:, None] * (j_mat - np.diag(eps))
        return script_f_raw.T.copy()

    rust = load_gpusim_rust_module()
    rust_fn = (
        (
            lambda: rust.idf_calc_script_f(
                np.ascontiguousarray(areas, dtype=np.float64),
                np.ascontiguousarray(f_mat, dtype=np.float64),
                np.ascontiguousarray(emiss, dtype=np.float64),
            )
        )
        if rust is not None and hasattr(rust, "idf_calc_script_f")
        else None
    )
    return dispatch_gpusim_rust(
        "openubem.gpusim.viewfactors.calc_script_f",
        _py,
        rust_fn,
        bucket="B2",
    )


def compute_batch_view_factors(
    batch: BatchSpec,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute padded ``[B, S, S]`` view-factor and ScriptF matrices for a batch.

    Args:
        batch: Compiled ``BatchSpec`` for ``B`` buildings.

    Returns:
        Tuple ``(f_batch, script_f_batch)``, each float64 of shape ``[B, S, S]``.
    """
    n_bldg = batch.batch_size
    max_s = batch.max_surfaces

    def _py() -> tuple[np.ndarray, np.ndarray]:
        f_batch = np.zeros((n_bldg, max_s, max_s), dtype=np.float64)
        sf_batch = np.zeros((n_bldg, max_s, max_s), dtype=np.float64)

        for b_idx in range(n_bldg):
            n_surf = int(np.sum(batch.surf_mask[b_idx]))
            areas = batch.surf_area[b_idx, :n_surf]
            azimuths = batch.surf_azimuth_deg[b_idx, :n_surf]
            tilts = batch.surf_tilt_deg[b_idx, :n_surf]
            classes = batch.surf_class[b_idx, :n_surf]
            emiss = batch.surf_eps_in[b_idx, :n_surf]

            f_approx = calc_approximate_view_factors(areas, azimuths, tilts, classes)
            f_final = fix_view_factors(areas, f_approx)
            script_f = calc_script_f(areas, f_final, emiss)

            f_batch[b_idx, :n_surf, :n_surf] = f_final
            sf_batch[b_idx, :n_surf, :n_surf] = script_f

        return f_batch, sf_batch

    rust = load_gpusim_rust_module()
    rust_fn = None
    if rust is not None and hasattr(rust, "idf_calc_zone_view_and_script_f_batch"):
        def _rust() -> tuple[np.ndarray, np.ndarray]:
            z_areas: list[list[float]] = []
            z_az: list[list[float]] = []
            z_tilt: list[list[float]] = []
            z_cls: list[list[int]] = []
            z_emiss: list[list[float]] = []
            counts: list[int] = []
            for b_idx in range(n_bldg):
                n_surf = int(np.sum(batch.surf_mask[b_idx]))
                counts.append(n_surf)
                z_areas.append(batch.surf_area[b_idx, :n_surf].tolist())
                z_az.append(batch.surf_azimuth_deg[b_idx, :n_surf].tolist())
                z_tilt.append(batch.surf_tilt_deg[b_idx, :n_surf].tolist())
                z_cls.append([int(x) for x in batch.surf_class[b_idx, :n_surf]])
                z_emiss.append(batch.surf_eps_in[b_idx, :n_surf].tolist())

            pairs = rust.idf_calc_zone_view_and_script_f_batch(
                z_areas, z_az, z_tilt, z_cls, z_emiss
            )
            f_batch = np.zeros((n_bldg, max_s, max_s), dtype=np.float64)
            sf_batch = np.zeros((n_bldg, max_s, max_s), dtype=np.float64)
            for b_idx, (n_surf, (fm, sfm)) in enumerate(zip(counts, pairs)):
                f_batch[b_idx, :n_surf, :n_surf] = fm
                sf_batch[b_idx, :n_surf, :n_surf] = sfm
            return f_batch, sf_batch

        rust_fn = _rust

    return dispatch_gpusim_rust(
        "openubem.gpusim.viewfactors.compute_batch_view_factors",
        _py,
        rust_fn,
        bucket="B2",
    )
