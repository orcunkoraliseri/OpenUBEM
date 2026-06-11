"""Tests for openubem/semantic/imputation.py — plan T10."""

import numpy as np
import pandas as pd
import pytest

from openubem.semantic.imputation import build_ml_imputer, impute_column


def _rng():
    return np.random.default_rng(42)


# ── T10-1: KDE fills NaN values ───────────────────────────────────────────────

def test_kde_fills_nan_values():
    s = pd.Series([1.0, 2.0, 3.0, 4.0, np.nan, np.nan])
    result = impute_column(s, method="kde", rng=_rng())
    assert result.notna().all(), "KDE impute should fill all NaN values"
    assert result.iloc[4] != np.nan
    assert result.iloc[5] != np.nan


def test_kde_preserves_non_nan():
    s = pd.Series([1.0, 2.0, np.nan, 4.0])
    result = impute_column(s, method="kde", rng=_rng())
    assert result.iloc[0] == 1.0
    assert result.iloc[1] == 2.0
    assert result.iloc[3] == 4.0


def test_kde_bounds_clamp():
    s = pd.Series([10.0, 11.0, 12.0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan])
    bounds = (9.0, 13.0)
    result = impute_column(s, method="kde", bounds=bounds, rng=_rng())
    filled = result[s.isna()]
    assert (filled >= 9.0).all(), "Filled values should be >= lower bound"
    assert (filled <= 13.0).all(), "Filled values should be <= upper bound"


def test_kde_no_nan_passthrough():
    s = pd.Series([1.0, 2.0, 3.0])
    result = impute_column(s, method="kde", rng=_rng())
    pd.testing.assert_series_equal(result, s)


# ── T10-2: PDE fills from uniform distribution ───────────────────────────────

def test_pde_fills_nan_with_bounds():
    s = pd.Series([np.nan, np.nan, np.nan])
    bounds = (0.1, 0.9)
    result = impute_column(s, method="pde", bounds=bounds, rng=_rng())
    assert result.notna().all()
    assert (result >= 0.1).all()
    assert (result <= 0.9).all()


def test_pde_requires_bounds():
    s = pd.Series([np.nan])
    with pytest.raises(ValueError, match="bounds must be provided"):
        impute_column(s, method="pde", bounds=None, rng=_rng())


# ── T10-3: KDE falls back to PDE when all values are NaN ──────────────────────

def test_kde_falls_back_to_pde_when_all_nan(caplog):
    import logging
    s = pd.Series([np.nan, np.nan])
    bounds = (1.0, 5.0)
    with caplog.at_level(logging.WARNING, logger="openubem.semantic.imputation"):
        result = impute_column(s, method="kde", bounds=bounds, rng=_rng())
    assert result.notna().all()
    assert (result >= 1.0).all()
    assert (result <= 5.0).all()


# ── T10-4: unknown method raises ─────────────────────────────────────────────

def test_unknown_method_raises():
    s = pd.Series([np.nan])
    with pytest.raises(ValueError, match="unknown method"):
        impute_column(s, method="histogram", rng=_rng())


# ── T10-5: ML imputer stub raises NotImplementedError ────────────────────────

def test_ml_imputer_stub_raises():
    df = pd.DataFrame({"a": [1.0], "b": [2.0]})
    with pytest.raises(NotImplementedError, match="Phase-2"):
        build_ml_imputer(df, "a", ["b"])


# ── T10-6: reproducibility with fixed seed ───────────────────────────────────

def test_kde_reproducible_with_seed():
    s = pd.Series([1.0, 2.0, 3.0, np.nan, np.nan])
    r1 = impute_column(s.copy(), method="kde", rng=np.random.default_rng(99))
    r2 = impute_column(s.copy(), method="kde", rng=np.random.default_rng(99))
    pd.testing.assert_series_equal(r1, r2)
