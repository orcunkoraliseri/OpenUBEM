"""Spatial neighbour-fill utility + MNAR density filter (Input-Imputation arc, T06).

Two zero-trainable-weight primitives — neighbour-vote for categorical attributes
(`use_class`, vintage bins) and distance-weighted kNN for continuous attributes
(`levels`, `height_m`) — consumed by T04 (`year_built` donor vintage) and T05
(`levels` group-wise fill). Deliberately NOT a GNN: no fitted weights, only a
geometric nearest-neighbour query (M06 Part C / Table 4 — neighbour-vote/kriging
capture ~80% of the spatial signal with zero trainable parameters).

Fixed, published-convention neighbourhood: k=10 nearest neighbours capped at a
100 m search radius (`DEFAULT_K` / `DEFAULT_RADIUS_M`) — cited, never swept
against simulated EUI (Rule 4 / M06 §2). Callers may override `k`/`radius` (e.g.
for a smaller synthetic fixture); the *production* default never changes.

MNAR guard (hard requirement, M06 §4): if the local neighbourhood is itself
>= 60% missing on the target column, the neighbourhood signal is unreliable
(spatial clustering of missingness is spatial fill's signature failure mode) —
the row is DEACTIVATED for spatial fill (`value` stays unset) and
`SPATIAL_CLUSTER_MNAR_BLOCKED` is appended to `data_quality_flag` via the T01
`provenance` module so the caller falls back to the aspatial (statistical/
group-wise) tier.

Centroids assumed already in a projected (metric) CRS — reprojection is the
caller's responsibility, out of scope here.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from openubem.config import RANDOM_SEED
from openubem.semantic import provenance

# ── fixed, published-convention neighbourhood (do not sweep against EUI) ─────
DEFAULT_K = 10
DEFAULT_RADIUS_M = 100.0
MNAR_THRESHOLD = 0.60
_K_SEARCH_MULTIPLIER = 3  # candidate pool oversampled vs k, so R is measured on a stable set

MNAR_BLOCKED_FLAG = "SPATIAL_CLUSTER_MNAR_BLOCKED"

_HIGH_THRESHOLD = 0.8
_MED_THRESHOLD = 0.5
_TIER_DOWNGRADE = {"HIGH": "MEDIUM", "MEDIUM": "LOW", "LOW": "LOW"}


def _confidence_tier(agreement_score: float) -> str:
    """Neighbour-agreement score in [0,1] -> HIGH (>=0.8) / MEDIUM (>=0.5) / LOW."""
    if agreement_score >= _HIGH_THRESHOLD:
        return "HIGH"
    if agreement_score >= _MED_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def _downgrade(tier: str) -> str:
    return _TIER_DOWNGRADE[tier]


def _is_edge_of_bbox(point_xy: tuple, bounds: np.ndarray, radius: float) -> bool:
    """True when the point's own neighbourhood is truncated by the dataset's bounding
    box (bounds = gdf.total_bounds), i.e. within `radius` of any bbox edge — the
    neighbour count there under-represents the true local density (M06 §5-F)."""
    x, y = point_xy
    minx, miny, maxx, maxy = bounds
    return (
        (x - minx) < radius or (maxx - x) < radius
        or (y - miny) < radius or (maxy - y) < radius
    )


def _build_tree(gdf) -> tuple[cKDTree, np.ndarray]:
    centroids = gdf.geometry.centroid
    xy = np.column_stack([centroids.x.to_numpy(), centroids.y.to_numpy()])
    return cKDTree(xy), xy


def _query_neighbours(
    tree: cKDTree, xy: np.ndarray, i: int, k: int, radius: float, n: int
) -> tuple[np.ndarray, np.ndarray]:
    """Up to `k * _K_SEARCH_MULTIPLIER` nearest neighbours of point i within `radius`,
    excluding the point itself. Returns (neighbour_positions, distances)."""
    k_search = min(n, max(k * _K_SEARCH_MULTIPLIER, k + 5) + 1)  # +1 to allow for self
    dist, idx = tree.query(xy[i], k=k_search, distance_upper_bound=radius)
    dist = np.atleast_1d(dist)
    idx = np.atleast_1d(idx)
    valid = (idx != i) & (idx < n) & np.isfinite(dist)
    return idx[valid], dist[valid]


def neighbour_vote(
    gdf,
    col: str,
    k: int = DEFAULT_K,
    radius: float = DEFAULT_RADIUS_M,
    rng: np.random.Generator | None = None,
    mnar_threshold: float = MNAR_THRESHOLD,
):
    """Categorical neighbour-vote fill (T06a) — `use_class`, vintage bins, etc.

    For each row with `col` missing, votes the mode of up to `k` nearest neighbours
    (within `radius`) that have `col` observed.

    Returns ``(value, agreement_ratio, confidence, gdf_out)``:
      * ``value``           — pandas Series aligned to ``gdf.index``; the voted fill
        for eligible missing rows, ``None`` elsewhere (observed / no donors / MNAR-blocked).
      * ``agreement_ratio``  — fraction of donors agreeing with ``value`` (``NaN`` where
        ``value`` is ``None``).
      * ``confidence``      — ``{HIGH, MEDIUM, LOW}`` from ``agreement_ratio``, downgraded
        one tier at the edge of the dataset's bounding box; ``None`` where unset.
      * ``gdf_out``         — copy of ``gdf`` with ``SPATIAL_CLUSTER_MNAR_BLOCKED``
        appended to ``data_quality_flag`` for rows whose local neighbourhood missingness
        ratio R >= ``mnar_threshold`` (M06 §4). Those rows' ``value`` is **not** set —
        callers must route them to the aspatial fallback tier.

    Deterministic mode-tie break via ``rng`` (default ``np.random.default_rng(RANDOM_SEED)``).
    """
    if rng is None:
        rng = np.random.default_rng(RANDOM_SEED)

    n = len(gdf)
    value = pd.Series([None] * n, index=gdf.index, dtype=object)
    agreement_ratio = pd.Series(np.nan, index=gdf.index, dtype=float)
    confidence = pd.Series([None] * n, index=gdf.index, dtype=object)
    blocked_mask = np.zeros(n, dtype=bool)

    missing_mask = gdf[col].isna().to_numpy()
    if n < 2 or not missing_mask.any():
        return value, agreement_ratio, confidence, provenance.append_flag(
            gdf, MNAR_BLOCKED_FLAG, mask=blocked_mask
        )

    tree, xy = _build_tree(gdf)
    bounds = gdf.total_bounds
    col_values = gdf[col].to_numpy()

    for i in np.flatnonzero(missing_mask):
        nbr_idx, nbr_dist = _query_neighbours(tree, xy, i, k, radius, n)
        if len(nbr_idx) == 0:
            continue
        nbr_missing = pd.isna(col_values[nbr_idx])
        r_missing = nbr_missing.mean()
        if r_missing >= mnar_threshold:
            blocked_mask[i] = True
            continue
        donor_idx = nbr_idx[~nbr_missing]
        donor_dist = nbr_dist[~nbr_missing]
        if len(donor_idx) == 0:
            continue
        order = np.argsort(donor_dist)[:k]
        donors = col_values[donor_idx[order]]

        uniq, counts = np.unique(donors, return_counts=True)
        top = counts.max()
        winners = uniq[counts == top]
        winner = rng.choice(winners) if len(winners) > 1 else winners[0]
        ratio = top / len(donors)

        tier = _confidence_tier(ratio)
        if _is_edge_of_bbox(xy[i], bounds, radius):
            tier = _downgrade(tier)

        value.iat[i] = winner
        agreement_ratio.iat[i] = ratio
        confidence.iat[i] = tier

    gdf_out = provenance.append_flag(gdf, MNAR_BLOCKED_FLAG, mask=blocked_mask)
    return value, agreement_ratio, confidence, gdf_out


def knn_fill(
    gdf,
    col: str,
    k: int = DEFAULT_K,
    radius: float = DEFAULT_RADIUS_M,
    mnar_threshold: float = MNAR_THRESHOLD,
):
    """Continuous distance-weighted kNN fill (T06b) — `levels`, `height_m`, etc.

    For each row with `col` missing, fills the inverse-distance-weighted mean of up
    to `k` nearest neighbours (within `radius`) that have `col` observed.

    Returns ``(value, dispersion, confidence, gdf_out)``:
      * ``value``       — distance-weighted mean fill, ``NaN`` where unset (observed /
        no donors / MNAR-blocked).
      * ``dispersion``  — donor weighted standard deviation (``NaN`` where unset); the
        continuous analogue of ``agreement_ratio``.
      * ``confidence``  — derived from an agreement-equivalent score
        ``1 / (1 + coefficient_of_variation)`` mapped through the same
        HIGH>=0.8 / MEDIUM>=0.5 / LOW thresholds as `neighbour_vote`, downgraded one
        tier at the edge of the bounding box; ``None`` where unset.
      * ``gdf_out``     — copy of ``gdf`` with ``SPATIAL_CLUSTER_MNAR_BLOCKED`` appended
        to ``data_quality_flag`` for MNAR-blocked rows (R >= ``mnar_threshold``) — those
        rows' ``value`` is **not** set; callers must use the aspatial fallback.

    Purely deterministic (distance-weighted mean has no tie-break / no `rng`).
    """
    n = len(gdf)
    value = pd.Series(np.nan, index=gdf.index, dtype=float)
    dispersion = pd.Series(np.nan, index=gdf.index, dtype=float)
    confidence = pd.Series([None] * n, index=gdf.index, dtype=object)
    blocked_mask = np.zeros(n, dtype=bool)

    col_numeric = gdf[col].astype(float)
    missing_mask = col_numeric.isna().to_numpy()
    if n < 2 or not missing_mask.any():
        return value, dispersion, confidence, provenance.append_flag(
            gdf, MNAR_BLOCKED_FLAG, mask=blocked_mask
        )

    tree, xy = _build_tree(gdf)
    bounds = gdf.total_bounds
    col_values = col_numeric.to_numpy()

    for i in np.flatnonzero(missing_mask):
        nbr_idx, nbr_dist = _query_neighbours(tree, xy, i, k, radius, n)
        if len(nbr_idx) == 0:
            continue
        nbr_missing = np.isnan(col_values[nbr_idx])
        r_missing = nbr_missing.mean()
        if r_missing >= mnar_threshold:
            blocked_mask[i] = True
            continue
        donor_idx = nbr_idx[~nbr_missing]
        donor_dist = nbr_dist[~nbr_missing]
        if len(donor_idx) == 0:
            continue
        order = np.argsort(donor_dist)[:k]
        donors = donor_idx[order]
        d = donor_dist[order]
        vals = col_values[donors]

        weights = 1.0 / np.maximum(d, 1e-6)
        w_mean = float(np.average(vals, weights=weights))
        w_var = float(np.average((vals - w_mean) ** 2, weights=weights))
        std = math.sqrt(max(w_var, 0.0))
        cv = std / abs(w_mean) if w_mean != 0 else (0.0 if std == 0 else float("inf"))
        agreement_equiv = 1.0 / (1.0 + cv)

        tier = _confidence_tier(agreement_equiv)
        if _is_edge_of_bbox(xy[i], bounds, radius):
            tier = _downgrade(tier)

        value.iat[i] = w_mean
        dispersion.iat[i] = std
        confidence.iat[i] = tier

    gdf_out = provenance.append_flag(gdf, MNAR_BLOCKED_FLAG, mask=blocked_mask)
    return value, dispersion, confidence, gdf_out
