"""T11 - per-hour shadow rasters (PLAN §7 T11).

Sign convention (binding, stated once): `sh_building` is a SUNLIT indicator, not a "shadow"
flag, matching U03 §2.3's own usage of `S_bldg` as a direct multiplicative gate on `K_dir`
(`K_dir = I_dir,horiz / sinθ * S_bldg * [...]`) -- S_bldg=1 where the direct beam is unobstructed,
0 where a building blocks it. This mirrors `sh_veg`'s own fractional-transmission semantics
exactly, so T14 can gate direct beam with a single expression and no inversion:
`K_dir_effective = K_dir * sh_building * sh_veg`. (Chosen deliberately opposite to a literal
reading of the variable name -- documented here once, loudly, precisely because the name alone
is misleading.)

Building sunlit/shadow reuses T10's precomputed horizon-angle stack (same z_obs = DEM +
UTCI_PEDESTRIAN_HEIGHT_M): a cell is shadowed by buildings iff the sun's altitude is at or
below the horizon angle in the sun's azimuth direction. This is the same 2.5D geometry a fresh
ray march would compute -- the horizon stack already answers "is anything blocking this
direction above angle X", so re-marching per hour would be redundant work (plan §7 T11 "How":
"Reuse the T10 horizon stack where it short-circuits the march"). Interpolated linearly between
the two bracketing azimuth bins so the result is continuous across the 32-bin resolution and
across the 0/360 wrap. A direct DSM-vs-observer-height check adds self-occlusion for footprint
interior pixels, which the horizon stack (built from distances >= 1 pixel, never d=0) cannot
represent on its own -- at high sun altitude the nearest ray sample is still 1 pixel away, so
the horizon angle asymptotes below 90 degrees even directly over a tall obstruction.

Vegetation transmission is a fresh per-hour computation (CDSM/TDSM are not part of T10's DSM):
Beer-Lambert path length through the crown, using the tier's cited reference transmissivity
(P-09, U03 Table 4) as the value at normal incidence -- avoids inventing separate k_ext/LAD
constants not cited anywhere in the plan. The ray is partitioned into per-pixel-step height
bands (mirroring the horizon-angle sweep's own step structure); each band's overlap with the
local canopy layer [TDSM, CDSM] contributes log(tau_ref) * (band_overlap / crown_depth) to the
accumulated log-transmission, so at normal incidence through a single homogeneous crown the
result reduces exactly to tau_ref.
"""
from __future__ import annotations

import numpy as np

from openubem import config
from openubem.microclimate.svf import compute_svf


def cast_shadows(
    domain,
    altitude_deg: float,
    azimuth_deg: float,
    *,
    horizon_angles: "np.ndarray | None" = None,
    n_azimuths: "int | None" = None,
    cdsm: "np.ndarray | None" = None,
    tdsm: "np.ndarray | None" = None,
    canopy_tau: "float | None" = None,
):
    """Returns (sh_building, sh_veg).

    sh_building: bool, domain.shape. True = SUNLIT (direct beam reaches this cell), False =
    blocked by a building (see module docstring for the sign-convention rationale).
    sh_veg: float32, domain.shape, in [0, 1]. Fractional direct-beam transmission through
    vegetation along the path to the sun (1.0 = no canopy in the path / fully transmissive).
    Combined direct-beam gate for T14: K_dir_effective = K_dir * sh_building * sh_veg.

    altitude_deg <= 0 (sun below horizon, §4.6) -> fully shaded, zero transmission everywhere.
    """
    rows, cols = domain.shape
    if altitude_deg <= 0.0:
        return np.zeros((rows, cols), dtype=bool), np.zeros((rows, cols), dtype=np.float32)

    if horizon_angles is None:
        if n_azimuths is None:
            n_azimuths = config.UTCI_SVF_AZIMUTHS
        _svf, horizon_angles = compute_svf(domain, n_azimuths=n_azimuths)
    else:
        n_azimuths = horizon_angles.shape[0]

    sh_building = _building_shadow_from_horizon(domain, altitude_deg, azimuth_deg, horizon_angles, n_azimuths)
    sh_veg = _vegetation_transmission(domain, altitude_deg, azimuth_deg, cdsm, tdsm, canopy_tau)
    return sh_building, sh_veg


def _building_shadow_from_horizon(domain, altitude_deg, azimuth_deg, horizon_angles, n_azimuths):
    bin_step = 360.0 / n_azimuths
    az = azimuth_deg % 360.0
    idx_f = az / bin_step
    idx0 = int(np.floor(idx_f)) % n_azimuths
    idx1 = (idx0 + 1) % n_azimuths
    frac = idx_f - np.floor(idx_f)
    horizon_interp = (1.0 - frac) * horizon_angles[idx0] + frac * horizon_angles[idx1]

    z_obs = domain.dem.astype(np.float64) + config.UTCI_PEDESTRIAN_HEIGHT_M
    self_occluded = domain.dsm.astype(np.float64) > z_obs
    blocked = (altitude_deg <= horizon_interp) | self_occluded

    return ~blocked  # sh_building is a SUNLIT indicator (module docstring) -> invert "blocked"


def _vegetation_transmission(domain, altitude_deg, azimuth_deg, cdsm, tdsm, canopy_tau):
    rows, cols = domain.shape
    if cdsm is None or tdsm is None or canopy_tau is None or not np.any(cdsm > 0):
        return np.ones((rows, cols), dtype=np.float32)

    res = domain.res_m
    z_obs = domain.dem.astype(np.float64) + config.UTCI_PEDESTRIAN_HEIGHT_M
    alt_r = np.radians(altitude_deg)
    az_r = np.radians(azimuth_deg)
    sin_a, cos_a = np.sin(az_r), np.cos(az_r)
    tan_alt = np.tan(alt_r)

    cdsm64 = cdsm.astype(np.float64)
    tdsm64 = tdsm.astype(np.float64)
    crown_depth = np.clip(cdsm64 - tdsm64, 1e-6, None)
    log_tau_ref = float(np.log(canopy_tau))
    canopy_top = float(cdsm64.max())

    max_radius_px = int(np.ceil(np.hypot(rows, cols)))
    pad = max_radius_px
    padded_cdsm = np.pad(cdsm64, pad, mode="constant", constant_values=0.0)
    padded_tdsm = np.pad(tdsm64, pad, mode="constant", constant_values=0.0)
    padded_depth = np.pad(crown_depth, pad, mode="constant", constant_values=1e-6)

    accum_log_t = np.zeros((rows, cols), dtype=np.float64)
    ray_h_prev = z_obs.copy()

    for d in range(0, max_radius_px + 1):
        drow = -int(round(d * cos_a))  # same convention as svf.py: north (+y) -> row decreases
        dcol = int(round(d * sin_a))
        ray_h_next = z_obs + (d + 1) * res * tan_alt

        cwin = padded_cdsm[pad + drow: pad + drow + rows, pad + dcol: pad + dcol + cols]
        twin = padded_tdsm[pad + drow: pad + drow + rows, pad + dcol: pad + dcol + cols]
        dwin = padded_depth[pad + drow: pad + drow + rows, pad + dcol: pad + dcol + cols]

        top = np.minimum(cwin, ray_h_next)
        bottom = np.maximum(ray_h_prev, twin)
        seg = np.where(cwin > 0, np.maximum(top - bottom, 0.0), 0.0)
        accum_log_t += (seg / dwin) * log_tau_ref

        ray_h_prev = ray_h_next
        if float(ray_h_next.min()) > canopy_top:
            break

    return np.exp(accum_log_t).astype(np.float32)
