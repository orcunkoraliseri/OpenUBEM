"""M7b Rung S3: Batched ray-triangle exterior shading (beam sunlit fraction & sky diffuse).

Computes per-surface beam sunlit fractions ``sunlit_frac[H, S]`` and isotropic
sky diffuse shading ratios ``dif_shdg_iso_sky[S]`` against ``Shading:Site:Detailed``
(and optional building self-shading polygons) using vectorized Möller-Trumbore
ray-triangle intersection on CUDA (via PyTorch) or NumPy CPU.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from openubem.gpusim._rust_compat import (
    dispatch_gpusim_rust,
    load_gpusim_rust_module,
)
from openubem.gpusim.dispatch import select_optimal_shading_backend


def _triangulate_polygon(verts: np.ndarray) -> np.ndarray:
    """Fan-triangulate a planar polygon ``[V, 3]`` into ``[V-2, 3, 3]`` triangles."""
    n = len(verts)
    if n < 3:
        return np.zeros((0, 3, 3), dtype=np.float64)
    tris = np.empty((n - 2, 3, 3), dtype=np.float64)
    v0 = verts[0]
    for i in range(n - 2):
        tris[i, 0] = v0
        tris[i, 1] = verts[i + 1]
        tris[i, 2] = verts[i + 2]
    return tris


def _sample_polygon_points(verts: np.ndarray, n_grid: int = 3) -> np.ndarray:
    """Generate stratified interior sample points on a 3D polygon ``[V, 3]``.

    Uses a ``(n_grid x n_grid)`` bilinear grid for quads (the 99% case for
    building walls/windows) and area-weighted barycentric sampling for general
    n-gons.
    """
    n = len(verts)
    if n == 4:
        u_vals = (np.arange(n_grid, dtype=np.float64) + 0.5) / float(n_grid)
        pts = []
        v0, v1, v2, v3 = verts[0], verts[1], verts[2], verts[3]
        for u in u_vals:
            for v in u_vals:
                p = (
                    (1.0 - u) * (1.0 - v) * v0
                    + u * (1.0 - v) * v1
                    + u * v * v2
                    + (1.0 - u) * v * v3
                )
                pts.append(p)
        return np.asarray(pts, dtype=np.float64)

    tris = _triangulate_polygon(verts)
    if len(tris) == 0:
        return verts[:1].copy()
    # Triangle centroids + edge midpoints weighted by area
    pts_list = []
    for tri in tris:
        a, b, c = tri[0], tri[1], tri[2]
        pts_list.append((a + b + c) / 3.0)
        if n_grid >= 3:
            pts_list.append(0.6 * a + 0.2 * b + 0.2 * c)
            pts_list.append(0.2 * a + 0.6 * b + 0.2 * c)
            pts_list.append(0.2 * a + 0.2 * b + 0.6 * c)
    return np.asarray(pts_list, dtype=np.float64)


def _ray_triangle_any_hit_numpy(
    origins: np.ndarray,   # [P, 3]
    dirs: np.ndarray,      # [R, 3]
    v0: np.ndarray,        # [M, 3]
    e1: np.ndarray,        # [M, 3]
    e2: np.ndarray,        # [M, 3]
    t_eps: float = 1.0e-3,
) -> np.ndarray:
    """Return boolean occluded mask ``[R, P]`` via Möller-Trumbore (NumPy)."""
    n_rays = dirs.shape[0]
    n_pts = origins.shape[0]
    n_tris = v0.shape[0]
    if n_tris == 0 or n_rays == 0 or n_pts == 0:
        return np.zeros((n_rays, n_pts), dtype=bool)

    occluded = np.zeros((n_rays, n_pts), dtype=bool)
    # Process rays in chunks to bound peak RAM
    chunk = 64
    for r0 in range(0, n_rays, chunk):
        r1 = min(r0 + chunk, n_rays)
        d = dirs[r0:r1]  # [C, 3]
        # pvec = cross(d, e2): [C, M, 3]
        pvec = np.cross(d[:, None, :], e2[None, :, :])
        det = np.sum(e1[None, :, :] * pvec, axis=-1)  # [C, M]
        valid_det = np.abs(det) > 1.0e-9
        inv_det = np.where(valid_det, 1.0 / np.where(valid_det, det, 1.0), 0.0)

        for p_idx in range(n_pts):
            tvec = origins[p_idx][None, :] - v0  # [M, 3]
            u = np.sum(tvec[None, :, :] * pvec, axis=-1) * inv_det  # [C, M]
            m1 = valid_det & (u >= -1.0e-5) & (u <= 1.0 + 1.0e-5)
            if not np.any(m1):
                continue
            qvec = np.cross(tvec, e1)  # [M, 3]
            v = np.sum(d[:, None, :] * qvec[None, :, :], axis=-1) * inv_det
            m2 = m1 & (v >= -1.0e-5) & (u + v <= 1.0 + 1.0e-5)
            if not np.any(m2):
                continue
            t = np.sum(e2 * qvec, axis=-1)[None, :] * inv_det
            hit = m2 & (t > t_eps)
            occluded[r0:r1, p_idx] = np.any(hit, axis=1)
    return occluded


def _ray_triangle_any_hit_torch(
    origins: np.ndarray,
    dirs: np.ndarray,
    v0: np.ndarray,
    e1: np.ndarray,
    e2: np.ndarray,
    device: str = "cuda",
    t_eps: float = 1.0e-3,
) -> np.ndarray:
    """Return boolean occluded mask ``[R, P]`` via batched Möller-Trumbore on PyTorch."""
    import torch

    n_rays = dirs.shape[0]
    n_pts = origins.shape[0]
    n_tris = v0.shape[0]
    if n_tris == 0 or n_rays == 0 or n_pts == 0:
        return np.zeros((n_rays, n_pts), dtype=bool)

    dev = torch.device(device)
    o_t = torch.as_tensor(origins, dtype=torch.float32, device=dev)  # [P, 3]
    d_t = torch.as_tensor(dirs, dtype=torch.float32, device=dev)     # [R, 3]
    v0_t = torch.as_tensor(v0, dtype=torch.float32, device=dev)      # [M, 3]
    e1_t = torch.as_tensor(e1, dtype=torch.float32, device=dev)      # [M, 3]
    e2_t = torch.as_tensor(e2, dtype=torch.float32, device=dev)      # [M, 3]

    # tvec: [P, M, 3], qvec: [P, M, 3], t_num: [P, M]
    # Chunk over P and M to keep VRAM tiny (< 64 MB)
    out = torch.zeros((n_rays, n_pts), dtype=torch.bool, device=dev)
    p_chunk = 128
    m_chunk = 512
    for m0 in range(0, n_tris, m_chunk):
        m1 = min(m0 + m_chunk, n_tris)
        v0c = v0_t[m0:m1]  # [Mc, 3]
        e1c = e1_t[m0:m1]
        e2c = e2_t[m0:m1]
        # pvec = cross(d[:, None], e2c[None, :]): [R, Mc, 3]
        pvec = torch.linalg.cross(d_t[:, None, :], e2c[None, :, :], dim=-1)
        det = torch.sum(e1c[None, :, :] * pvec, dim=-1)  # [R, Mc]
        valid = torch.abs(det) > 1.0e-7
        inv_det = torch.where(valid, 1.0 / torch.where(valid, det, torch.ones_like(det)), torch.zeros_like(det))

        for p0 in range(0, n_pts, p_chunk):
            p1 = min(p0 + p_chunk, n_pts)
            oc = o_t[p0:p1]  # [Pc, 3]
            tvec = oc[:, None, :] - v0c[None, :, :]  # [Pc, Mc, 3]
            qvec = torch.linalg.cross(tvec, e1c[None, :, :], dim=-1)  # [Pc, Mc, 3]
            t_num = torch.sum(e2c[None, :, :] * qvec, dim=-1)  # [Pc, Mc]

            # Process rays in subchunks for [Rc, Pc, Mc]
            r_chunk = 64
            for r0 in range(0, n_rays, r_chunk):
                r1 = min(r0 + r_chunk, n_rays)
                pv = pvec[r0:r1]       # [Rc, Mc, 3]
                id_ = inv_det[r0:r1]   # [Rc, Mc]
                val = valid[r0:r1]     # [Rc, Mc]
                dc = d_t[r0:r1]        # [Rc, 3]

                # u = einsum('pmi,rmi->rpm', tvec, pv) * id_[:, None, :]
                u = torch.einsum("pmi,rmi->rpm", tvec, pv) * id_[:, None, :]
                v = torch.einsum("ri,pmi->rpm", dc, qvec) * id_[:, None, :]
                t = t_num[None, :, :] * id_[:, None, :]
                hit = (
                    val[:, None, :]
                    & (u >= -1.0e-4)
                    & (v >= -1.0e-4)
                    & (u + v <= 1.0 + 1.0e-4)
                    & (t > t_eps)
                )
                out[r0:r1, p0:p1] |= torch.any(hit, dim=2)

    return out.cpu().numpy()


def _fibonacci_hemisphere_dirs(n_dirs: int = 64) -> np.ndarray:
    """Generate ``n_dirs`` quasi-uniform unit vectors on the upper hemisphere (z > 0)."""
    idx = np.arange(n_dirs, dtype=np.float64) + 0.5
    z = idx / float(n_dirs)  # uniform in (0, 1)
    r = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    golden = math.pi * (3.0 - math.sqrt(5.0))
    phi = golden * idx
    return np.stack([r * np.cos(phi), r * np.sin(phi), z], axis=1)


def _flatten_poly_seq(
    polys: Sequence[np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """Flatten a sequence of ``[V_i, 3]`` polygons into ``(verts_flat, offsets)``."""
    arrays = [
        (
            np.zeros((0, 3), dtype=np.float64)
            if len(v) == 0
            else np.ascontiguousarray(v, dtype=np.float64)
        )
        for v in polys
    ]
    offsets = np.zeros(len(arrays) + 1, dtype=np.uint32)
    if arrays:
        lengths = np.fromiter(
            (len(a) for a in arrays), dtype=np.uint32, count=len(arrays)
        )
        np.cumsum(lengths, out=offsets[1:])
        verts_flat = np.concatenate(arrays, axis=0)
    else:
        verts_flat = np.zeros((0, 3), dtype=np.float64)
    return verts_flat, offsets


def compute_exterior_shading(
    target_verts: Sequence[np.ndarray],
    target_normals: np.ndarray,      # [S, 3]
    target_sun_exposed: np.ndarray,  # [S] bool
    occluder_verts: Sequence[np.ndarray],
    solcos_hourly: np.ndarray,       # [8760, 3] (East, North, Up)
    *,
    periodic_days: int = 20,
    n_grid: int = 3,
    n_sky_rays: int = 64,
    device: str = "auto",
) -> tuple[np.ndarray, np.ndarray]:
    """Compute hourly sunlit fractions ``[8760, S]`` and sky diffuse factors ``[S]``.

    Matches EnergyPlus ``ShadowCalculation, PolygonClipping, Periodic, 20`` by
    evaluating representative solar positions every ``periodic_days`` days (or
    every day when ``periodic_days=1``) and broadcasting to each period.
    In ``device="auto"`` mode, automatically picks the fastest available
    backend: Rust CWBVH8 (``cpu_rust``) > CUDA > MPS > NumPy CPU.
    """
    n_surf = len(target_verts)
    sunlit_hr = np.ones((8760, n_surf), dtype=np.float32)
    dif_sky = np.ones(n_surf, dtype=np.float64)

    if not occluder_verts or n_surf == 0 or not np.any(target_sun_exposed):
        return sunlit_hr, dif_sky

    backend = select_optimal_shading_backend(requested_device=device)

    def _run_py() -> tuple[np.ndarray, np.ndarray]:
        tri_chunks = [_triangulate_polygon(np.asarray(v, dtype=np.float64)) for v in occluder_verts]
        tri_chunks = [t for t in tri_chunks if len(t) > 0]
        if not tri_chunks:
            return sunlit_hr.copy(), dif_sky.copy()
        tris = np.concatenate(tri_chunks, axis=0)  # [M, 3, 3]
        v0 = tris[:, 0, :]
        e1 = tris[:, 1, :] - v0
        e2 = tris[:, 2, :] - v0

        # Sample origins for all sun-exposed target surfaces, nudged 2 mm along outward normal
        pt_origins_list: list[np.ndarray] = []
        surf_pt_slices: list[tuple[int, int, int]] = []  # (s_idx, start, end)
        offset = 0
        for s_idx in range(n_surf):
            if not target_sun_exposed[s_idx]:
                continue
            verts = np.asarray(target_verts[s_idx], dtype=np.float64)
            if len(verts) < 3:
                continue
            pts = _sample_polygon_points(verts, n_grid=n_grid)
            pts = pts + 2.0e-3 * target_normals[s_idx][None, :]
            pt_origins_list.append(pts)
            surf_pt_slices.append((s_idx, offset, offset + len(pts)))
            offset += len(pts)

        if not pt_origins_list:
            return sunlit_hr.copy(), dif_sky.copy()
        origins = np.concatenate(pt_origins_list, axis=0)  # [P, 3]

        # Build representative solar ray set matching EnergyPlus Periodic shadow update
        rep_days = list(range(0, 365, max(1, periodic_days)))
        rep_hours = []
        for d in rep_days:
            for h in range(24):
                idx_h = d * 24 + h
                if solcos_hourly[idx_h, 2] > 0.01:
                    rep_hours.append((d, h, idx_h))

        sky_dirs = _fibonacci_hemisphere_dirs(n_sky_rays)
        beam_dirs = (
            solcos_hourly[[x[2] for x in rep_hours]]
            if rep_hours
            else np.zeros((0, 3), dtype=np.float64)
        )
        all_dirs = np.concatenate([beam_dirs, sky_dirs], axis=0)  # [R_beam + R_sky, 3]

        use_torch = backend in ("cuda", "mps")
        if use_torch:
            occ = _ray_triangle_any_hit_torch(origins, all_dirs, v0, e1, e2, device=backend)
        else:
            occ = _ray_triangle_any_hit_numpy(origins, all_dirs, v0, e1, e2)

        n_beam = len(rep_hours)
        occ_beam = occ[:n_beam]       # [R_beam, P]
        occ_sky = occ[n_beam:]        # [R_sky, P]

        # Map representative-day beam sunlit fractions to all 365 days
        # Build [len(rep_days), 24, S] table
        day_to_rep = {d: i for i, d in enumerate(rep_days)}
        rep_sunlit = np.ones((len(rep_days), 24, n_surf), dtype=np.float32)
        for r_i, (d, h, idx_h) in enumerate(rep_hours):
            di = day_to_rep[d]
            ray = solcos_hourly[idx_h]
            for s_idx, p0, p1 in surf_pt_slices:
                if float(np.dot(ray, target_normals[s_idx])) <= 0.0:
                    continue
                rep_sunlit[di, h, s_idx] = float(1.0 - np.mean(occ_beam[r_i, p0:p1]))

        out_sunlit = sunlit_hr.copy()
        out_dif = dif_sky.copy()
        for d in range(365):
            di = min(d // max(1, periodic_days), len(rep_days) - 1)
            out_sunlit[d * 24 : (d + 1) * 24, :] = rep_sunlit[di]

        # Sky diffuse shading factor: cosine-weighted fraction of visible upper hemisphere
        for s_idx, p0, p1 in surf_pt_slices:
            nrm = target_normals[s_idx]
            cos_w = np.maximum(0.0, sky_dirs @ nrm)  # [R_sky]
            denom = float(np.sum(cos_w))
            if denom > 1.0e-9:
                vis = 1.0 - np.mean(occ_sky[:, p0:p1], axis=1)  # [R_sky]
                out_dif[s_idx] = float(np.sum(cos_w * vis) / denom)

        return out_sunlit, out_dif

    rust = load_gpusim_rust_module()
    rust_fn = None
    if (
        backend == "cpu_rust"
        and rust is not None
        and hasattr(rust, "shading_compute_exterior")
    ):
        def _run_rust() -> tuple[np.ndarray, np.ndarray]:
            t_flat, t_off = _flatten_poly_seq(target_verts)
            o_flat, o_off = _flatten_poly_seq(occluder_verts)
            return rust.shading_compute_exterior(
                t_flat,
                t_off,
                np.ascontiguousarray(target_normals, dtype=np.float64),
                np.ascontiguousarray(target_sun_exposed, dtype=bool),
                o_flat,
                o_off,
                np.ascontiguousarray(solcos_hourly, dtype=np.float64),
                int(max(1, periodic_days)),
                int(n_grid),
                int(n_sky_rays),
            )

        rust_fn = _run_rust

    return dispatch_gpusim_rust(
        "openubem.gpusim.shading.compute_exterior_shading",
        _run_py,
        rust_fn,
        bucket="B3",
    )
