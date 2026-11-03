"""T10 - sky view factor & horizon angles (PLAN §7 T10).

Static geometry: computed once per domain and cached (§4.9 / U03 §3.1 line 177). Horizon-angle
method, Lindberg (2008) / P-14: Psi_sky = (1/N) * sum(cos^2(gamma_i)) over N azimuths, gamma_i
the max obstacle elevation angle in azimuth i. Vectorised as shifted-array sweeps over the whole
raster per azimuth (the standard SOLWEIG formulation) -- never a per-cell Python loop. Step
distances use geometric spacing (dense near-field, sparse far-field) to bound cost independent
of domain size while keeping the analytic gate (CP-2) accurate.
"""
from __future__ import annotations

import hashlib

import numpy as np

from openubem import config


def _step_distances(max_radius_px: int) -> np.ndarray:
    """Every integer pixel distance out to max_radius_px.

    Earlier draft used geometric (log) spacing to bound cost independent of domain size, but at
    oblique azimuths a thin wall (a few pixels along-ray) can sit entirely inside a skipped gap,
    silently under-detecting the true horizon angle -> SVF biased high. Measured against the
    analytic canyon gate (CP-2): geometric spacing missed by up to 0.33 at H/W=0.5; dense integer
    stepping matches to <0.005. Cost is a report-only metric at CP-2, not a gate."""
    if max_radius_px < 1:
        return np.array([], dtype=int)
    return np.arange(1, max_radius_px + 1, dtype=int)


def compute_svf(domain, n_azimuths: int = None, max_radius_px: "int | None" = None):
    """Returns (svf, horizon_angles): svf shape = domain.shape (float32, 0-1);
    horizon_angles shape = (n_azimuths, *domain.shape) (float32, degrees, floored at 0)."""
    if n_azimuths is None:
        n_azimuths = config.UTCI_SVF_AZIMUTHS
    dsm = domain.dsm.astype(np.float64)
    res = domain.res_m
    rows, cols = dsm.shape
    z_obs = domain.dem.astype(np.float64) + config.UTCI_PEDESTRIAN_HEIGHT_M

    if max_radius_px is None:
        max_radius_px = int(np.ceil(np.hypot(rows, cols)))
    pad = max_radius_px
    padded = np.pad(dsm, pad, mode="constant", constant_values=-1.0e6)

    azimuths = np.linspace(0.0, 360.0, n_azimuths, endpoint=False)
    horizon_angles = np.zeros((n_azimuths, rows, cols), dtype=np.float32)
    distances = _step_distances(max_radius_px)

    for k, az in enumerate(azimuths):
        az_r = np.radians(az)
        sin_a, cos_a = np.sin(az_r), np.cos(az_r)
        max_angle = np.zeros((rows, cols), dtype=np.float64)
        for d in distances:
            drow = -int(round(d * cos_a))  # north (+y) -> row decreases (transform origin at max y)
            dcol = int(round(d * sin_a))   # east (+x) -> col increases
            window = padded[pad + drow: pad + drow + rows, pad + dcol: pad + dcol + cols]
            elev_angle = np.degrees(np.arctan2(window - z_obs, d * res))
            np.maximum(max_angle, elev_angle, out=max_angle)
        horizon_angles[k] = np.maximum(max_angle, 0.0).astype(np.float32)

    svf = np.mean(np.cos(np.radians(horizon_angles)) ** 2, axis=0).astype(np.float32)
    svf = np.clip(svf, 0.0, 1.0)
    return svf, horizon_angles


def domain_hash(domain, n_azimuths: int) -> str:
    """Cache key for (geometry, res, n_azimuths) -- T18 keys the .npz horizon cache with this."""
    h = hashlib.sha256()
    h.update(domain.dsm.tobytes())
    h.update(str(domain.res_m).encode())
    h.update(str(domain.shape).encode())
    h.update(str(n_azimuths).encode())
    return h.hexdigest()[:16]
