"""Module 06: KDE/PDE imputation and ML imputer stub (DESIGN §3E)."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def impute_column(
    series: pd.Series,
    method: str = "kde",
    bounds: tuple[float, float] | None = None,
    rng: np.random.Generator | None = None,
    bw_method: str | float = "scott",
) -> pd.Series:
    """
    Impute missing values in series using KDE or PDE (DESIGN §3E / F10/F11).

    method="kde"  → fit KDE on observed values, sample NaN positions.
    method="pde"  → sample from uniform(bounds) when there are no observed
                    values at all (PDE = Prior-Distribution Estimation).

    Bounds clamp sampled values to [bounds[0], bounds[1]].
    If rng is None, uses numpy default_rng(42).

    Returns series with NaNs filled; dtype preserved where possible.
    """
    if rng is None:
        from openubem.config import RANDOM_SEED
        rng = np.random.default_rng(RANDOM_SEED)

    out = series.copy()
    nan_mask = out.isna()
    if not nan_mask.any():
        return out

    observed = out[~nan_mask].dropna()
    n_fill = nan_mask.sum()

    if method == "kde":
        if len(observed) == 0:
            logger.warning(
                "impute_column: no observed values for KDE on '%s'; "
                "falling back to PDE with bounds %s",
                series.name,
                bounds,
            )
            method = "pde"
        else:
            kde = stats.gaussian_kde(observed.astype(float), bw_method=bw_method)
            samples = kde.resample(n_fill, seed=rng)[0]
            if bounds is not None:
                samples = np.clip(samples, bounds[0], bounds[1])
            out[nan_mask] = samples
            return out

    if method == "pde":
        if bounds is None:
            raise ValueError(
                "impute_column: bounds must be provided for PDE imputation "
                f"on column '{series.name}'."
            )
        samples = rng.uniform(bounds[0], bounds[1], size=n_fill)
        out[nan_mask] = samples
        return out

    raise ValueError(f"impute_column: unknown method '{method}'. Use 'kde' or 'pde'.")


def build_ml_imputer(
    gdf: pd.DataFrame,
    target_col: str,
    feature_cols: list[str],
) -> object:
    """
    Stub: ML-based imputer (DESIGN §3E / F12 — Phase 2 only).

    In Phase 1 this stub raises NotImplementedError so callers
    can fall back to KDE/PDE without silent misuse.
    """
    raise NotImplementedError(
        "build_ml_imputer is a Phase-2 feature (DESIGN §3E / F12). "
        "Use impute_column(method='kde') for Phase 1."
    )
