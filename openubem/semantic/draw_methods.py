"""Variance-preserving `draw` tier (Input-Imputation arc, Part II of
`docs/docs_ACTIVE/input/imputation/implementation/IMPLEMENTATION_phaseC_ml_imputer.md`).

Opt-in / OFF by construction (Part II §II.1 rule 4): this module is imported
by nothing in the default `impute_missing` call graph until a future task
(T07) wires `_draw_tier` into `openubem/semantic/imputation.py`'s
`_CANONICAL_TIER_ORDER` / `_TIER_HANDLER_NAMES`. Until then, importing this
file or setting `config.IMPUTE_DRAW_METHOD_BY_TARGET` has zero effect on any
production path -- `config.IMPUTE_ENABLED_TIERS` is untouched (§II.1 rule 4).

Every function here is a pure draw over OBSERVED values only (§II.1 rule 6),
zero-fitted-parameters (§II.1 rule 3): no bandwidth/donor-k/residual-scale
knob is ever tuned against a target; callers must pass an already-seeded
`np.random.Generator` (convention: `np.random.default_rng(config.RANDOM_SEED)`).

`DRAW_METHODS` is the T02-T06b registry (mirrors the Phase-C 6-method
pattern, `imputation.py`'s `_ML_METHOD_NAMES`) -- T01 introduces it typed and
empty; each subsequent task registers one more pure draw function.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable

import numpy as np
import pandas as pd

# T03/T04/T06b reuse the T06 fixed neighbourhood convention verbatim (§II.1
# rule 3: "k = DEFAULT_K = 10 ... import them, never redefine").
from openubem.semantic.spatial_impute import DEFAULT_K, DEFAULT_RADIUS_M

# ═══════════════════════════════════════════════════════════════════════════
# T01 — registry scaffold + `DRAW_<METHOD>_<TIER>` token constants.
#
# Manager-ratification request (T01 "How", parent §5G token registry): the
# exact strings below are the new provenance tokens this arc introduces.
# Wiring (which tokens a given draw function actually emits) lands with the
# function itself (T02+); T01 only reserves the vocabulary so it is fixed
# before any method exists.
# ═══════════════════════════════════════════════════════════════════════════

DRAW_KDE_HIGH = "DRAW_KDE_HIGH"
DRAW_KDE_MED = "DRAW_KDE_MED"
DRAW_PMM_HIGH = "DRAW_PMM_HIGH"
DRAW_PMM_MED = "DRAW_PMM_MED"
DRAW_HOTDECK_HIGH = "DRAW_HOTDECK_HIGH"
DRAW_HOTDECK_MED = "DRAW_HOTDECK_MED"
DRAW_RESID_HIGH = "DRAW_RESID_HIGH"
DRAW_RESID_MED = "DRAW_RESID_MED"
DRAW_ABB_HIGH = "DRAW_ABB_HIGH"
DRAW_ABB_MED = "DRAW_ABB_MED"
DRAW_CATFREQ_HIGH = "DRAW_CATFREQ_HIGH"
DRAW_CATFREQ_MED = "DRAW_CATFREQ_MED"

# Typed, name -> pure-draw-function registry (T01: empty; T02 registers "kde").
DRAW_METHODS: dict[str, Callable] = {}

# Small-stratum abstain floor shared by the seeded draw methods (T02 "How to
# test" example value; below this a stratum abstains -> null -> falls through
# to the next enabled tier, mirroring `_spatial_tier`'s LOW-discard contract).
_MIN_STRATUM_N = 5


# ═══════════════════════════════════════════════════════════════════════════
# T02 — M1 `kde` draw (reuses the audited `impute_column(method="kde")`
# primitive at `imputation.py:96-97`; does NOT reimplement KDE sampling,
# per §II.4).
# ═══════════════════════════════════════════════════════════════════════════

def draw_kde(
    observed_by_stratum: dict,
    targets,
    rng: np.random.Generator,
    bounds: "tuple[float, float] | None" = None,
    min_stratum_n: int = _MIN_STRATUM_N,
) -> np.ndarray:
    """Variance-preserving KDE donor draw, one sample per missing row.

    Args:
        observed_by_stratum: `{stratum_key: array-like of that stratum's
            OBSERVED values}` (fit-on-observed-only, §II.1 rule 6).
        targets: sequence of stratum keys, one per row needing a draw
            (output is aligned to this sequence, index-for-index).
        rng: a seeded `np.random.Generator` (never constructed here).
        bounds: optional global `(lo, hi)` clamp; `None` clamps each stratum
            to its own observed `(min, max)` (the KDE/PDE convention,
            `impute_column`'s existing `np.clip` guard).
        min_stratum_n: strata with fewer observed values abstain (return
            `NaN` for every row in that stratum) rather than fit a KDE on a
            near-degenerate sample -- falls through to the next tier.

    Returns:
        `np.ndarray` of length `len(targets)`; `NaN` where the row's stratum
        abstained.

    Zero-fitted-params: KDE bandwidth is the library default (Scott's rule,
    unchanged from `impute_column`'s own default `bw_method="scott"`) --
    never swept. Determinism: the SAME `rng` instance is consumed once per
    stratum in `targets`' first-seen order, so two calls with fresh
    generators seeded from the same value produce byte-identical draws.
    """
    from openubem.semantic.imputation import impute_column

    targets = list(targets)
    draws = np.full(len(targets), np.nan, dtype=float)

    idx_by_stratum: dict = defaultdict(list)
    for i, stratum in enumerate(targets):
        idx_by_stratum[stratum].append(i)

    for stratum, idxs in idx_by_stratum.items():
        observed = pd.Series(observed_by_stratum.get(stratum, [])).dropna().astype(float)
        if len(observed) < min_stratum_n:
            continue  # abstain -- stays NaN, falls through to the next tier

        clamp = bounds if bounds is not None else (float(observed.min()), float(observed.max()))
        series = pd.concat(
            [observed.reset_index(drop=True), pd.Series([np.nan] * len(idxs))],
            ignore_index=True,
        )
        filled = impute_column(series, method="kde", bounds=clamp, rng=rng)
        stratum_draws = filled.iloc[len(observed):].to_numpy(dtype=float)
        for j, i in enumerate(idxs):
            draws[i] = stratum_draws[j]

    return draws


DRAW_METHODS["kde"] = draw_kde


# ═══════════════════════════════════════════════════════════════════════════
# T03 — M2 `pmm` (predictive-mean-matching donor draw).
#
# Deviation note (cited in II.9 progress log): mirrors `draw_kde`'s
# `(observed_by_stratum, targets, rng)` pure signature rather than the plan's
# illustrative `draw_pmm(gdf, attr, mask, rng, k=DEFAULT_K)` -- the file-layout
# comment at the top of this module frames every T02-T06b function as "pure
# draw functions over observed Series/frames"; T02 already established (CP-A
# audited, accepted) that the dict/targets form is the concretization used
# here. The cheap zero-fitted-params predictor is each stratum's OBSERVED
# median (same concept `_statistical_tier` already uses) -- PMM's donor pool
# is NOT confined to one stratum: every observed value across every stratum
# is a candidate, ranked by |its stratum's predicted value - the target
# stratum's predicted value|, so a thin stratum can still borrow its k
# nearest-predicted donors from neighbouring strata instead of abstaining.
# ═══════════════════════════════════════════════════════════════════════════

def draw_pmm(
    observed_by_stratum: dict,
    targets,
    rng: np.random.Generator,
    k: int = DEFAULT_K,
) -> np.ndarray:
    """Predictive-mean-matching donor draw, one REAL observed value per row.

    Args:
        observed_by_stratum: `{stratum_key: array-like of that stratum's
            OBSERVED values}` (fit-on-observed-only, §II.1 rule 6).
        targets: sequence of stratum keys, one per row needing a draw.
        rng: a seeded `np.random.Generator` (never constructed here).
        k: donor-neighbourhood size; fixed `DEFAULT_K=10` (T06 convention,
            imported, never redefined -- §II.1 rule 3).

    Returns:
        `np.ndarray` of length `len(targets)`; every non-NaN entry equals
        some value in `observed_by_stratum` (real-donor invariant, §II.1).
        `NaN` when there is no observed value anywhere (nothing to match
        against) -- the only abstain condition, since PMM's cross-stratum
        borrowing means even a single-member stratum can still be served by
        its k nearest-predicted donors elsewhere.

    Zero-fitted-params: the "predictor" is the stratum's observed median --
    a group statistic, not a fitted model; `k` is the fixed T06 convention.
    Determinism: one `rng.choice` call per target, in `targets`' first-seen
    order (matches `draw_kde`'s consumption discipline).
    """
    targets = list(targets)
    draws = np.full(len(targets), np.nan, dtype=float)

    donor_values_parts = []
    donor_predicted_parts = []
    stratum_median: dict = {}
    for stratum, values in observed_by_stratum.items():
        vals = pd.Series(values).dropna().astype(float).to_numpy()
        if len(vals) == 0:
            continue
        median = float(np.median(vals))
        stratum_median[stratum] = median
        donor_values_parts.append(vals)
        donor_predicted_parts.append(np.full(len(vals), median))

    if not donor_values_parts:
        return draws  # abstain -- no observed values anywhere

    donor_values = np.concatenate(donor_values_parts)
    donor_predicted = np.concatenate(donor_predicted_parts)
    global_median = float(np.median(donor_values))

    for i, stratum in enumerate(targets):
        predicted_target = stratum_median.get(stratum, global_median)
        dist = np.abs(donor_predicted - predicted_target)
        k_eff = min(k, len(donor_values))
        # Tie-inclusive k-NN: the group-median predictor is CONSTANT within a
        # stratum, so every same-stratum donor ties at distance 0. Truncating
        # to the first k by a stable sort would silently pin every draw to
        # the SAME arbitrary k-subset (array order), collapsing variance
        # instead of preserving it. Include every donor at or below the k-th
        # smallest distance, then draw uniformly among all of them.
        threshold = np.partition(dist, k_eff - 1)[k_eff - 1]
        eligible = donor_values[dist <= threshold]
        draws[i] = rng.choice(eligible)

    return draws


DRAW_METHODS["pmm"] = draw_pmm


# ═══════════════════════════════════════════════════════════════════════════
# T04 — M3 `hotdeck` (spatial donor draw).
#
# Deviation note (cited in II.9 progress log): II.1 rule ("Real-donor
# invariant for pmm/hotdeck/abb: every filled value must equal some observed
# value") is a hard requirement. The PUBLIC `spatial_impute.knn_fill`
# aggregates its k donors into a distance-WEIGHTED MEAN and `neighbour_vote`
# aggregates into the donor MODE -- neither output is, in general, a real
# observed value, so calling either one directly and using its `value`
# output as the draw would violate the real-donor invariant. This function
# instead reuses the lower-level T06 neighbour-query engine those two public
# functions are themselves built on (`_build_tree`/`_query_neighbours`,
# `spatial_impute.py:75-91`) to gather each missing row's donor pool, then
# draws ONE of those real donor values -- `DEFAULT_K`/`DEFAULT_RADIUS_M`
# unchanged, never overridden (§II.1 rule 3).
# ═══════════════════════════════════════════════════════════════════════════

def draw_hotdeck(
    gdf,
    attr: str,
    mask,
    rng: np.random.Generator,
    k: int = DEFAULT_K,
    radius: float = DEFAULT_RADIUS_M,
):
    """Spatial donor draw: for each `mask` row, draw ONE real observed value
    from its k-nearest spatial neighbours within `radius` (T06 machinery).

    Args:
        gdf: (Geo)DataFrame with a `geometry` column and `attr` column.
        attr: column to fill.
        mask: boolean Series/array aligned to `gdf.index`, True for rows
            needing a draw.
        rng: a seeded `np.random.Generator` (never constructed here).
        k / radius: fixed T06 neighbourhood convention (`DEFAULT_K=10`,
            `DEFAULT_RADIUS_M=100`), imported, never redefined.

    Returns:
        `pd.Series` aligned to `gdf.index`; `NaN`/`None` (dtype-dependent)
        for every row not in `mask`, and for `mask` rows with no observed
        neighbour within `radius` (abstain -- falls through to the next
        tier). Every filled value equals a real observed neighbour value
        (real-donor invariant).

    Fit-on-observed-only: only OBSERVED (`attr` non-null) neighbours are
    ever donors. Determinism: one `rng.choice` call per missing row, visited
    in `gdf`'s row order.
    """
    from openubem.semantic.spatial_impute import _build_tree, _query_neighbours

    n = len(gdf)
    is_numeric = pd.api.types.is_numeric_dtype(gdf[attr])
    value = (
        pd.Series(np.nan, index=gdf.index, dtype=float) if is_numeric
        else pd.Series([None] * n, index=gdf.index, dtype=object)
    )
    mask_arr = np.asarray(mask.to_numpy() if hasattr(mask, "to_numpy") else mask, dtype=bool)
    if n < 2 or "geometry" not in getattr(gdf, "columns", []) or not mask_arr.any():
        return value

    tree, xy = _build_tree(gdf)
    col_values = gdf[attr].to_numpy()

    for i in np.flatnonzero(mask_arr):
        nbr_idx, _nbr_dist = _query_neighbours(tree, xy, i, k, radius, n)
        if len(nbr_idx) == 0:
            continue  # abstain -- no neighbour within radius at all

        donor_mask = ~pd.isna(col_values[nbr_idx])
        donors = col_values[nbr_idx[donor_mask]]
        if len(donors) == 0:
            continue  # abstain -- no OBSERVED neighbour within radius

        value.iat[i] = rng.choice(donors)

    return value


DRAW_METHODS["hotdeck"] = draw_hotdeck


# ═══════════════════════════════════════════════════════════════════════════
# T05 — M4 `resid` (stochastic residual draw).
# ═══════════════════════════════════════════════════════════════════════════

def draw_resid(
    observed_by_stratum: dict,
    targets,
    rng: np.random.Generator,
    bounds: "tuple[float, float] | None" = None,
    min_stratum_n: int = _MIN_STRATUM_N,
) -> np.ndarray:
    """Group-median + a residual drawn from the stratum's own empirical
    observed residual distribution -- keeps the median's central accuracy
    while re-injecting exactly the observed within-stratum spread.

    Args:
        observed_by_stratum: `{stratum_key: array-like of OBSERVED values}`.
        targets: sequence of stratum keys, one per row needing a draw.
        rng: a seeded `np.random.Generator` (never constructed here).
        bounds: optional global `(lo, hi)` clamp; `None` clamps each
            stratum's draw to its own observed `(min, max)` (the KDE/PDE
            clamp convention).
        min_stratum_n: strata with fewer observed values abstain (the same
            fixed floor T02's `draw_kde` uses) rather than draw a residual
            from a near-degenerate empirical distribution.

    Returns:
        `np.ndarray` of length `len(targets)`; `NaN` where the row's stratum
        abstained.

    Zero-fitted-params: no parametric residual scale -- the residual
    distribution is the OBSERVED `(value - stratum_median)` array itself,
    resampled empirically. Determinism: one `rng.choice` call per row,
    visited in `targets`' first-seen-stratum order.
    """
    targets = list(targets)
    draws = np.full(len(targets), np.nan, dtype=float)

    idx_by_stratum: dict = defaultdict(list)
    for i, stratum in enumerate(targets):
        idx_by_stratum[stratum].append(i)

    for stratum, idxs in idx_by_stratum.items():
        observed = pd.Series(observed_by_stratum.get(stratum, [])).dropna().astype(float).to_numpy()
        if len(observed) < min_stratum_n:
            continue  # abstain -- falls through to the next tier

        median = float(np.median(observed))
        residuals = observed - median
        clamp = bounds if bounds is not None else (float(observed.min()), float(observed.max()))

        for i in idxs:
            draw = median + rng.choice(residuals)
            draws[i] = float(np.clip(draw, clamp[0], clamp[1]))

    return draws


DRAW_METHODS["resid"] = draw_resid


# ═══════════════════════════════════════════════════════════════════════════
# T06 — M5 `catfreq` (categorical empirical-frequency draw).
#
# Deliberately gdf/attr/mask-shaped (not the dict/targets form) because the
# self-stratification leakage guard it must implement (§II.6 T06 "How":
# "never stratify a column by itself, mirror `_statistical_tier`
# `imputation.py:935`") is a property of WHICH column is chosen as the
# stratifier from `gdf`'s own columns -- it only exists to check when this
# function picks its own `strat_col`, so it must own that selection itself,
# exactly mirroring `_statistical_tier`'s categorical branch structure.
# ═══════════════════════════════════════════════════════════════════════════

def _empirical_freqs(values) -> "tuple[np.ndarray, np.ndarray] | tuple[None, None]":
    counts = pd.Series(values).dropna().value_counts()
    if counts.empty:
        return None, None
    return counts.index.to_numpy(), (counts / counts.sum()).to_numpy()


def draw_catfreq(
    gdf,
    attr: str,
    mask,
    rng: np.random.Generator,
    min_stratum_n: int = _MIN_STRATUM_N,
):
    """Categorical empirical-frequency draw (the draw-tier analogue of
    `_statistical_tier`'s group MODE): draws a category per row from the
    OBSERVED within-stratum proportions instead of always returning the
    single most common one -- restores minority categories the mode erases.

    Args:
        gdf: DataFrame with `attr` and (optionally) `use_class`/
            `archetype_id` stratifier columns.
        attr: categorical column to fill.
        mask: boolean Series/array aligned to `gdf.index`, True for rows
            needing a draw.
        rng: a seeded `np.random.Generator` (never constructed here).
        min_stratum_n: a stratum's (or the global pool's) empirical
            frequency table is used only once it has at least this many
            OBSERVED rows; below that, falls through to the next candidate
            (stratum -> global) or abstains if even the global pool is thin.

    Returns:
        `pd.Series` (object dtype) aligned to `gdf.index`; `None` for rows
        outside `mask` and for `mask` rows where neither the stratum nor the
        global observed pool clears `min_stratum_n` (abstain).

    Self-stratification leakage guard: when `attr` itself is a strat
    candidate (imputing `use_class`), that candidate is skipped -- mirrors
    `_statistical_tier` (`imputation.py:933-936`).
    """
    n = len(gdf)
    value = pd.Series([None] * n, index=gdf.index, dtype=object)
    mask_arr = np.asarray(mask.to_numpy() if hasattr(mask, "to_numpy") else mask, dtype=bool)
    if not mask_arr.any():
        return value

    observed_mask = gdf[attr].notna()
    if not observed_mask.any():
        return value  # abstain -- no observed values anywhere

    strat_col = None
    for candidate in ("use_class", "archetype_id"):
        if candidate == attr:
            continue  # self-stratification leakage guard
        if candidate in gdf.columns:
            strat_col = candidate
            break

    global_cats, global_probs = None, None
    if int(observed_mask.sum()) >= min_stratum_n:
        global_cats, global_probs = _empirical_freqs(gdf.loc[observed_mask, attr])

    group_freqs: dict = {}
    if strat_col is not None:
        for stratum, group in gdf.loc[observed_mask].groupby(strat_col)[attr]:
            if len(group) >= min_stratum_n:
                group_freqs[stratum] = _empirical_freqs(group)

    for idx in gdf.index[mask_arr]:
        stratum = gdf.at[idx, strat_col] if strat_col is not None else None
        cats, probs = group_freqs.get(stratum, (None, None))
        if cats is None:
            cats, probs = global_cats, global_probs
        if cats is None:
            continue  # abstain -- neither stratum nor global pool clears the floor
        value.loc[idx] = rng.choice(cats, p=probs)

    return value


DRAW_METHODS["catfreq"] = draw_catfreq


# ═══════════════════════════════════════════════════════════════════════════
# T06b — M6 `abb` (approximate-Bayesian-bootstrap donor draw, Rubin &
# Schenker 1986; V01 §II.5 must-add small-n upgrade).
# ═══════════════════════════════════════════════════════════════════════════

def draw_abb(
    observed_by_stratum: dict,
    targets,
    rng: np.random.Generator,
    min_stratum_n: int = _MIN_STRATUM_N,
) -> np.ndarray:
    """Two-stage approximate-Bayesian-bootstrap donor draw: per stratum,
    first draw ONE bootstrap resample (with replacement, size = n observed)
    of that stratum's observed values -- injecting donor-POOL sampling
    uncertainty -- then draw each missing row's fill from that shared
    resample. Resists the donor depletion a plain fixed-donor draw shows at
    small n (the same handful of values repeated for every missing row).

    Args:
        observed_by_stratum: `{stratum_key: array-like of OBSERVED values}`.
        targets: sequence of stratum keys, one per row needing a draw.
        rng: a seeded `np.random.Generator` (never constructed here).
        min_stratum_n: strata with fewer observed values abstain (same
            fixed floor as `draw_kde`/`draw_resid`).

    Returns:
        `np.ndarray` of length `len(targets)`; every non-NaN entry equals
        some value in `observed_by_stratum` (real-donor invariant -- the
        resample is drawn FROM the observed array, and each row's fill is
        drawn FROM the resample, so both stages only ever copy real
        observed values). `NaN` where the stratum abstained.

    Zero-fitted-params: no knob -- `size=n_observed` and `replace=True` are
    the ABB definition itself, not tuned parameters. Determinism: one
    `rng.choice` call to build the per-stratum resample, then one more per
    row, all consumed in `targets`' first-seen-stratum order.
    """
    targets = list(targets)
    draws = np.full(len(targets), np.nan, dtype=float)

    idx_by_stratum: dict = defaultdict(list)
    for i, stratum in enumerate(targets):
        idx_by_stratum[stratum].append(i)

    for stratum, idxs in idx_by_stratum.items():
        observed = pd.Series(observed_by_stratum.get(stratum, [])).dropna().astype(float).to_numpy()
        if len(observed) < min_stratum_n:
            continue  # abstain -- falls through to the next tier

        resample = rng.choice(observed, size=len(observed), replace=True)  # stage 1
        for i in idxs:
            draws[i] = rng.choice(resample)  # stage 2

    return draws


DRAW_METHODS["abb"] = draw_abb
