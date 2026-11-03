"""M09 mask-and-recover validation harness (Input-Imputation arc, T08).

Report, do NOT tune (M09 §4 / zero-fitted-params, PLAN §2 rule 4): every
metric here is reported to the user and MUST NEVER be fed back into any
`impute_missing`/`ImputeConfig` setting, threshold, or bound. No EUI is read
or produced here (that is T09's scope, gated LIVE_SMOKE).

Protocol (M09 Table 1 / Step A-B):
  1. Restrict to COMPLETE CASES on the targeted attributes (fit-on-complete-
     case-only / no leakage, PLAN §2 rule 6).
  2. Spatial-BLOCK 80/20 hold-out: group rows by a spatial block key (an
     existing postcode/block column if usably populated, else a
     deterministic quantile grid over geometry centroids) and hold out
     whole BLOCKS, never individual rows -- a random row split leaks via
     spatial autocorrelation (M09 Step A).
  3. Mask (set to NaN) the targeted attributes on the held-out rows.
  4. Run `openubem.semantic.imputation.impute_missing` (the T07 routing
     orchestrator) over the masked frame.
  5. Score recovery per input type against the TRUE (pre-mask) values:
       continuous  -- MAE, RMSE, KS statistic, Wasserstein distance
                       (distributional fidelity -- RMSE alone rewards
                       variance-collapse, M09 Table 1).
       categorical -- PFC (proportion falsely classified) + log-loss.

Interface note (superseded by T07.2 -- categorical IS now routed): earlier
(Phase B), `impute_missing`'s generic tiers (`_spatial_tier`/
`_statistical_tier`, `openubem/semantic/imputation.py`) were continuous-only,
and this module's categorical path always raised and reported a
`NOT_SCORABLE` marker instead of scoring. As of T07.2, both tiers dispatch on
dtype: a categorical (string) target such as `use_class` is routed through
`spatial_impute.neighbour_vote` (spatial tier) and a group-wise stratified
mode via `_observed_mode` (statistical tier), same HIGH/MEDIUM-confidence
acceptance and MNAR fall-through as the continuous path. This module
therefore now scores categorical targets the same way as continuous ones
(`score_categorical`: PFC + log-loss); the `NOT_SCORABLE` marker and its
`try/except` fallback remain only as a defensive guard for the (no longer
expected) case where `impute_missing` still raises on a given attribute.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from openubem.semantic.imputation import ImputeConfig, impute_missing

__all__ = [
    "DEFAULT_HOLDOUT_FRAC",
    "DEFAULT_N_GRID",
    "complete_cases",
    "assign_spatial_blocks",
    "spatial_block_holdout",
    "mask_targets",
    "mae",
    "rmse",
    "ks_statistic",
    "wasserstein",
    "pfc",
    "one_hot_proba",
    "log_loss",
    "score_continuous",
    "score_categorical",
    "mask_and_recover",
]

DEFAULT_HOLDOUT_FRAC = 0.20
# Fixed, cited convention (never swept against any metric/EUI -- mirrors T06's
# DEFAULT_K/DEFAULT_RADIUS_M fixed-convention pattern in spatial_impute.py):
# number of quantile bins per axis when no postcode/block column is usable
# and blocks must be derived from geometry centroids.
DEFAULT_N_GRID = 4
# Additive/Laplace smoothing epsilon for turning a deterministic point
# prediction into a log-loss-safe probability vector -- fixed, never swept.
_LOG_LOSS_EPS = 1e-3
NOT_SCORABLE = "NOT_SCORABLE: impute_missing has no categorical tier (T07 Phase-B scope)"


# ── complete-case filter (no leakage) ────────────────────────────────────────

def complete_cases(gdf, targets):
    """Rows with every column in `targets` observed (no leakage donor pool)."""
    targets = list(targets)
    mask = gdf[targets].notna().all(axis=1)
    return gdf.loc[mask].copy()


# ── spatial-block assignment (NOT a random row split) ────────────────────────

def _is_blank(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and pd.isna(v):
        return True
    if isinstance(v, str) and v.strip() == "":
        return True
    return False


def _usable_block_column(gdf, col: str) -> bool:
    if col not in gdf.columns:
        return False
    non_blank = ~gdf[col].map(_is_blank)
    if non_blank.mean() < 0.95:
        return False
    return gdf.loc[non_blank, col].nunique() >= 2


def assign_spatial_blocks(gdf, block_col: str | None = None, n_grid: int = DEFAULT_N_GRID):
    """Block-label Series aligned to `gdf.index` (M09 Step A: NOT random rows).

    Precedence: an explicit `block_col` is trusted as-is; else fall back to
    an existing `postcode` column if usably populated (>=95% non-blank, >=2
    distinct values); else derive a deterministic quantile grid over
    `geometry` centroids (a fixed spatial partition, not fitted against any
    outcome).
    """
    if block_col is not None:
        return gdf[block_col].astype(str)

    if _usable_block_column(gdf, "postcode"):
        return gdf["postcode"].astype(str)

    if not hasattr(gdf, "geometry") or "geometry" not in getattr(gdf, "columns", []):
        raise ValueError(
            "assign_spatial_blocks: no usable postcode/block column and no "
            "'geometry' column to derive blocks from -- T08 STOP-and-report "
            "condition (a)."
        )

    centroids = gdf.geometry.centroid
    n = len(gdf)
    n_grid_eff = max(1, min(n_grid, int(np.sqrt(max(n, 1)))))
    x_bins = pd.qcut(centroids.x, q=n_grid_eff, labels=False, duplicates="drop")
    y_bins = pd.qcut(centroids.y, q=n_grid_eff, labels=False, duplicates="drop")
    blocks = (
        pd.Series(x_bins, index=gdf.index).astype(str)
        + "_"
        + pd.Series(y_bins, index=gdf.index).astype(str)
    )
    return blocks


def spatial_block_holdout(
    gdf,
    block_col: str | None = None,
    n_grid: int = DEFAULT_N_GRID,
    holdout_frac: float = DEFAULT_HOLDOUT_FRAC,
    rng: "np.random.Generator | None" = None,
):
    """Assign spatial blocks, then withhold whole BLOCKS totalling
    ~`holdout_frac` of the ROWS (never individual rows).

    Returns (train_index, holdout_index, blocks) -- `blocks` is the full
    block-label Series for `gdf` (useful for asserting no block straddles
    both splits).
    """
    if rng is None:
        from openubem.config import RANDOM_SEED
        rng = np.random.default_rng(RANDOM_SEED)

    blocks = assign_spatial_blocks(gdf, block_col=block_col, n_grid=n_grid)
    block_sizes = blocks.value_counts()
    order = block_sizes.index.to_numpy().copy()
    rng.shuffle(order)

    target_n = holdout_frac * len(gdf)
    holdout_blocks: list = []
    running = 0
    for b in order:
        if running >= target_n:
            break
        holdout_blocks.append(b)
        running += int(block_sizes.loc[b])
    if not holdout_blocks and len(order) > 0 and holdout_frac > 0:
        holdout_blocks = [order[0]]

    holdout_mask = blocks.isin(holdout_blocks)
    holdout_index = gdf.index[holdout_mask]
    train_index = gdf.index[~holdout_mask]
    return train_index, holdout_index, blocks


def mask_targets(gdf, holdout_index, targets):
    """Copy of `gdf` with `targets` set to NaN on `holdout_index` rows, plus
    a DataFrame of the TRUE pre-mask values for those rows (ground truth)."""
    targets = list(targets)
    truth = gdf.loc[holdout_index, targets].copy()
    masked = gdf.copy()
    masked.loc[holdout_index, targets] = np.nan
    return masked, truth


# ── per-metric primitives (pure; standalone-testable) ────────────────────────

def mae(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def ks_statistic(y_true, y_pred) -> float:
    """Two-sample KS statistic between the TRUE and RECOVERED marginal
    distributions -- distributional fidelity, catches variance-collapse that
    RMSE alone rewards (M09 Table 1)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(stats.ks_2samp(y_true, y_pred).statistic)


def wasserstein(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(stats.wasserstein_distance(y_true, y_pred))


def pfc(y_true, y_pred) -> float:
    """Proportion falsely classified (categorical recovery error)."""
    y_true = np.asarray(list(y_true), dtype=object)
    y_pred = np.asarray(list(y_pred), dtype=object)
    return float(np.mean(y_true != y_pred))


def one_hot_proba(y_pred, classes, eps: float = _LOG_LOSS_EPS):
    """Smoothed one-hot probability matrix for a deterministic point-
    predicted categorical fill (fixed additive/Laplace smoothing `eps`,
    never swept against any metric): the predicted class gets `1 - eps`,
    the remaining classes share `eps` uniformly, so a wrong point prediction
    scores a large-but-finite log-loss instead of -inf."""
    classes = list(classes)
    k = len(classes)
    idx = {c: i for i, c in enumerate(classes)}
    n = len(y_pred)
    other = eps / max(k - 1, 1)
    proba = np.full((n, k), other, dtype=float)
    for row, pred in enumerate(y_pred):
        proba[row, idx[pred]] = 1.0 - eps
    return proba


def log_loss(y_true, proba, classes) -> float:
    """Standard multiclass log-loss: -mean(log P(true class)). `proba` is an
    (n, len(classes)) probability matrix -- see `one_hot_proba` for scoring a
    deterministic point-predicted fill."""
    classes = list(classes)
    idx = {c: i for i, c in enumerate(classes)}
    proba = np.clip(np.asarray(proba, dtype=float), 1e-12, 1.0)
    y_true = list(y_true)
    rows = np.arange(len(y_true))
    cols = np.array([idx[t] for t in y_true])
    return float(-np.mean(np.log(proba[rows, cols])))


def score_continuous(y_true, y_pred) -> dict:
    return {
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "ks_stat": ks_statistic(y_true, y_pred),
        "wasserstein": wasserstein(y_true, y_pred),
        "n": int(len(y_true)),
    }


def score_categorical(y_true, y_pred, classes=None) -> dict:
    y_true = list(y_true)
    y_pred = list(y_pred)
    if classes is None:
        classes = sorted(set(y_true) | set(y_pred))
    proba = one_hot_proba(y_pred, classes)
    return {
        "pfc": pfc(y_true, y_pred),
        "log_loss": log_loss(y_true, proba, classes),
        "n": int(len(y_true)),
    }


# ── top-level M09 protocol runner ────────────────────────────────────────────

def mask_and_recover(
    gdf,
    continuous_targets=(),
    categorical_targets=(),
    block_col: str | None = None,
    n_grid: int = DEFAULT_N_GRID,
    holdout_frac: float = DEFAULT_HOLDOUT_FRAC,
    cfg: "ImputeConfig | None" = None,
    rng: "np.random.Generator | None" = None,
) -> dict:
    """Run the full M09 mask-and-recover protocol (T08).

    Report, do NOT tune: nothing returned here may be fed back into
    `cfg`/`impute_missing` (zero-fitted-params). No EUI.

    Returns a dict:
        {
          "n_complete_cases": int, "n_holdout": int,
          "n_blocks_total": int, "n_blocks_holdout": int,
          "continuous": {attr: {"mae", "rmse", "ks_stat", "wasserstein", "n"}},
          "categorical": {attr: {"pfc", "log_loss", "n"} | NOT_SCORABLE str},
        }
    """
    if rng is None:
        from openubem.config import RANDOM_SEED
        rng = np.random.default_rng(RANDOM_SEED)
    if cfg is None:
        cfg = ImputeConfig()

    all_targets = list(continuous_targets) + list(categorical_targets)
    cc = complete_cases(gdf, all_targets)
    train_index, holdout_index, blocks = spatial_block_holdout(
        cc, block_col=block_col, n_grid=n_grid, holdout_frac=holdout_frac, rng=rng,
    )
    masked, truth = mask_targets(cc, holdout_index, all_targets)

    result: dict = {
        "n_complete_cases": int(len(cc)),
        "n_holdout": int(len(holdout_index)),
        "n_blocks_total": int(blocks.nunique()),
        "n_blocks_holdout": int(blocks.loc[holdout_index].nunique()) if len(holdout_index) else 0,
        "continuous": {},
        "categorical": {},
    }

    if continuous_targets:
        filled = impute_missing(masked, cfg=cfg, targets=list(continuous_targets), rng=rng)
        for attr in continuous_targets:
            result["continuous"][attr] = score_continuous(
                truth.loc[holdout_index, attr], filled.loc[holdout_index, attr]
            )

    for attr in categorical_targets:
        try:
            filled = impute_missing(masked, cfg=cfg, targets=[attr], rng=rng)
        except (TypeError, ValueError) as exc:
            result["categorical"][attr] = f"{NOT_SCORABLE} ({exc})"
            continue
        result["categorical"][attr] = score_categorical(
            truth.loc[holdout_index, attr], filled.loc[holdout_index, attr]
        )

    return result
