"""Module 06: KDE/PDE/ML imputation (DESIGN §3E). ML tier (T11) is opt-in only
-- see `_ml_tier`/`build_ml_imputer`; the default `enrich_semantics` path and
`config.IMPUTE_ENABLED_TIERS` are unaffected."""
from __future__ import annotations

import logging
from dataclasses import dataclass

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
    model_path=None,
) -> pd.Series:
    """
    Impute missing values in series using KDE, PDE, or ML (DESIGN §3E / F10/
    F11/F12, lines 120-130).

    method="kde"  → fit KDE on observed values, sample NaN positions.
    method="pde"  → sample from uniform(bounds) when there are no observed
                    values at all (PDE = Prior-Distribution Estimation).
    method="auto" → 0%<missing<100% -> KDE; 100% missing -> PDE;
                    `model_path` given -> ML (T11.4, joblib-loaded
                    `MLImputer`, T11.1/T11.5). `method="kde"`/`"pde"` are
                    UNCHANGED (byte-identical) by this branch -- it only
                    resolves the `"auto"` request into one of them.
    method="ml"   → joblib-load the `MLImputer` at `model_path` and predict
                    the NaN positions (T11.4). `impute_column` has no
                    feature-frame parameter (DESIGN's single-`series`
                    signature), so predictions fall back to the imputer's
                    own stored per-feature median/mode defaults -- callers
                    needing real per-row features should call
                    `build_ml_imputer`/`_ml_tier` directly instead.

    Bounds clamp sampled values to [bounds[0], bounds[1]] (kde/pde only).
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

    if method == "auto":
        if model_path is not None:
            method = "ml"
        elif nan_mask.all():
            method = "pde"
        else:
            method = "kde"

    observed = out[~nan_mask].dropna()
    n_fill = nan_mask.sum()

    if method == "ml":
        if model_path is None:
            raise ValueError(
                "impute_column: method='ml' requires model_path (DESIGN §3E line 128)."
            )
        imputer = load_ml_imputer(model_path)
        fill_index = out.index[nan_mask]
        X = pd.DataFrame(index=fill_index)
        for c in imputer.feature_cols:
            X[c] = np.nan
        preds = imputer.predict(X)
        samples = preds.to_numpy()
        if bounds is not None and not imputer.is_classifier:
            samples = np.clip(samples.astype(float), bounds[0], bounds[1])
        out[nan_mask] = samples
        return out

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


# ═══════════════════════════════════════════════════════════════════════════
# T11 — Phase C: classical-ML imputer (`build_ml_imputer` / §3E ML tier, F12).
# Input-Imputation arc, PLAN_phaseC_ml_imputer.md T11.1/T11.2/T11.5.
#
# Morphology/semantic targets ONLY (plan §2 rule 7): `year_built` (primary),
# `levels`, `height`/`height_m`, `use_class`. NEVER cooling_cop/heating_
# efficiency/U-values/SHGC/load densities/setpoints -- those stay on the
# PDE-from-standards path. Fits strictly on observed building attributes;
# `_assert_no_eui_leakage` structurally blocks any `*eui*` column from ever
# reaching a `.fit()` call (zero-fitted-params, plan §2 rule 3).
# ═══════════════════════════════════════════════════════════════════════════

_ML_METHOD_NAMES: tuple[str, ...] = ("missforest", "mice", "knn", "rf", "histgbm", "linear")

# Per-target complete-case floor (N observed) -- fixed convention, never swept
# (M04 §4 "below floor -> Phase-A fallback"; plan §4 dependency table). The
# authoritative values live in `config.IMPUTE_ML_FLOORS` (read lazily, at
# call time, so tests may monkeypatch it); this is only the built-in default.
_ML_FLOORS: dict = {
    "missforest": 1000,
    "mice": 200,
    "knn": 200,
    "rf": 1000,
    "histgbm": 5000,
    "linear": 1000,
}

# EUI-free default feature set (plan §4) -- geometry/morphology only, never a
# downstream sim column. `year_built` additionally gets a spatial-lag
# neighbour-vintage feature (`_spatial_lag`, below).
_DEFAULT_ML_FEATURE_COLS: tuple[str, ...] = (
    "footprint_area_m2", "centroid_x", "centroid_y", "use_class", "archetype_id",
)
_YEAR_BUILT_SPATIAL_LAG_COL = "__ml_year_built_spatial_lag__"

_ML_HIGH_THRESHOLD = 0.8  # same published convention as spatial_impute._confidence_tier (T06)
_ML_MED_THRESHOLD = 0.5


class BelowFloorError(ValueError):
    """Raised by `build_ml_imputer` when observed complete cases for
    `target_col` fall below the method's fixed floor (M04 §4). `_ml_tier`
    catches this and falls through to the statistical tier -- a legitimate,
    documented outcome on sub-floor single-city stock (plan §1)."""

    def __init__(self, method: str, n_observed: int, floor: int):
        self.method = method
        self.n_observed = n_observed
        self.floor = floor
        super().__init__(
            f"build_ml_imputer: method={method!r} needs >={floor} observed "
            f"complete cases, got {n_observed} -- below floor (M04 §4)."
        )


def _assert_no_eui_leakage(cols) -> None:
    """Zero-fitted-params structural guard (plan §2 rule 3): no EUI/`total_eui`/
    `*_eui_kwh_m2` column may ever reach an ML fit call graph."""
    leaked = [c for c in cols if "eui" in str(c).lower()]
    if leaked:
        raise ValueError(
            f"build_ml_imputer: zero-fitted-params violation -- EUI column(s) "
            f"{leaked} must never appear in an ML feature/fit call graph."
        )


def _tier_from_score(score: float) -> str:
    """score in [0,1] -> HIGH (>=0.8) / MEDIUM (>=0.5) / LOW (M09 §3A cut-points,
    same convention as `spatial_impute._confidence_tier`)."""
    if score >= _ML_HIGH_THRESHOLD:
        return "HIGH"
    if score >= _ML_MED_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def _spatial_lag(gdf, col: str, k: int = 10, radius: float = 100.0) -> pd.Series:
    """Distance-weighted mean of NEIGHBOURS' observed `col` values, for every
    row, excluding the row's own value (M04 §4 "spatial-lag neighbour
    vintage" feature) -- reuses the T06 KD-tree primitives (`_build_tree`/
    `_query_neighbours`, self-excluding by construction), so it is safe to
    use as a predictive feature for `col` itself (no self-leakage: only
    neighbours' values ever inform a row's own lag feature)."""
    n = len(gdf)
    out = pd.Series(np.nan, index=gdf.index, dtype=float)
    if n < 2 or "geometry" not in getattr(gdf, "columns", []) or col not in gdf.columns:
        return out

    from openubem.semantic.spatial_impute import _build_tree, _query_neighbours

    tree, xy = _build_tree(gdf)
    col_values = gdf[col].astype(float).to_numpy()
    for i in range(n):
        nbr_idx, nbr_dist = _query_neighbours(tree, xy, i, k, radius, n)
        if len(nbr_idx) == 0:
            continue
        donor_mask = ~np.isnan(col_values[nbr_idx])
        donors = col_values[nbr_idx[donor_mask]]
        if len(donors) == 0:
            continue
        dist = nbr_dist[donor_mask]
        weights = 1.0 / np.maximum(dist, 1e-6)
        out.iat[i] = float(np.average(donors, weights=weights))
    return out


def _build_supervised_estimator(method: str, is_classifier: bool, seed: int):
    """Single-target supervised estimator (frozen hyperparameters, plan §4 --
    no tuning code path exists). Used directly for `rf`/`histgbm`/`linear`
    (always), and as the classification fallback for `missforest`/`mice`/
    `knn` (IterativeImputer/KNNImputer cannot mix a classifier estimator with
    continuous feature columns in one joint matrix -- empirically verified;
    see T11.1 progress-log deviation)."""
    from sklearn.ensemble import (
        RandomForestClassifier, RandomForestRegressor,
        HistGradientBoostingClassifier, HistGradientBoostingRegressor,
    )
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.neighbors import KNeighborsClassifier

    if method in ("rf", "missforest"):
        return (RandomForestClassifier(n_estimators=100, max_depth=None, random_state=seed)
                if is_classifier else
                RandomForestRegressor(n_estimators=100, max_depth=None, random_state=seed))
    if method == "histgbm":
        return (HistGradientBoostingClassifier(random_state=seed) if is_classifier
                else HistGradientBoostingRegressor(random_state=seed))
    if method in ("linear", "mice"):
        # `mice` classification has no BayesianRidge analogue (regression-only
        # estimator) -- LogisticRegression is the natural probabilistic
        # single-target classifier fallback.
        return (LogisticRegression(random_state=seed, max_iter=1000) if is_classifier
                else Ridge(random_state=seed))
    if method == "knn":
        # classification only reaches here -- regression uses the genuine
        # KNNImputer matrix family (see `family` selection in build_ml_imputer).
        return KNeighborsClassifier(n_neighbors=5, weights="distance")
    raise ValueError(f"_build_supervised_estimator: unknown method {method!r}")


@dataclass
class MLImputer:
    """Fitted ML imputer (T11.1) -- `.predict(X)` / `.confidence(X)` (T11.2),
    `X` a DataFrame of `feature_cols` (raw, unencoded; preprocessing happens
    inside). Joblib-picklable as-is (T11.5)."""

    method: str
    target_col: str
    feature_cols: tuple
    is_classifier: bool
    floor: int
    n_observed: int
    family: str  # "matrix" (IterativeImputer/KNNImputer) | "supervised"
    numeric_features: tuple
    categorical_features: tuple
    feature_medians: dict
    feature_modes: dict
    estimator: object
    cat_encoders: dict
    seed: int
    train_residual_std: float = 0.0
    knn_index: object = None
    knn_train_target: "np.ndarray | None" = None

    def _prep(self, X: pd.DataFrame) -> pd.DataFrame:
        Xp = X.loc[:, list(self.feature_cols)].copy() if len(self.feature_cols) else X.iloc[:, :0].copy()
        for c in self.numeric_features:
            Xp[c] = pd.to_numeric(Xp[c], errors="coerce")
            Xp[c] = Xp[c].fillna(self.feature_medians.get(c, 0.0))
        for c in self.categorical_features:
            Xp[c] = Xp[c].fillna(self.feature_modes.get(c))
        return Xp

    def _encode_matrix(self, Xp: pd.DataFrame) -> np.ndarray:
        cols = [Xp[c].to_numpy(dtype=float) for c in self.numeric_features]
        for c in self.categorical_features:
            mapping = self.cat_encoders[c]
            fallback = mapping.get("__UNKNOWN__", 0.0)
            codes = Xp[c].map(mapping)
            codes = codes.fillna(fallback).to_numpy(dtype=float)
            cols.append(codes)
        return np.column_stack(cols) if cols else np.empty((len(Xp), 0))

    def _matrix_target_estimator(self):
        """The fitted per-target-column estimator IterativeImputer trained
        internally (last round's triplet for the target's column index --
        target is always the LAST column in the fit matrix)."""
        target_idx = len(self.numeric_features) + len(self.categorical_features)
        matches = [t for t in self.estimator.imputation_sequence_ if t.feat_idx == target_idx]
        return matches[-1].estimator

    def predict(self, X: pd.DataFrame) -> pd.Series:
        Xp = self._prep(X)
        if self.family == "matrix":
            mat = self._encode_matrix(Xp)
            full = np.column_stack([mat, np.full(len(Xp), np.nan)])
            out = self.estimator.transform(full)
            return pd.Series(out[:, -1], index=X.index, dtype=float)
        preds = self.estimator.predict(Xp)
        if self.is_classifier:
            return pd.Series(preds, index=X.index, dtype=object)
        return pd.Series(np.asarray(preds, dtype=float), index=X.index)

    def _rf_tree_dispersion(self, Xp: pd.DataFrame) -> np.ndarray:
        if self.family == "matrix":
            mat = self._encode_matrix(Xp)
            rf = self._matrix_target_estimator()
            return np.stack([t.predict(mat) for t in rf.estimators_])
        prep = self.estimator.named_steps["prep"]
        model = self.estimator.named_steps["model"]
        mat = prep.transform(Xp)
        return np.stack([t.predict(mat) for t in model.estimators_])

    def _mice_dispersion(self, Xp: pd.DataFrame) -> tuple:
        mat = self._encode_matrix(Xp)
        br = self._matrix_target_estimator()
        mean, std = br.predict(mat, return_std=True)
        return np.asarray(mean, dtype=float), np.asarray(std, dtype=float)

    def _knn_dispersion(self, Xp: pd.DataFrame) -> tuple:
        mat = self._encode_matrix(Xp)
        n_neighbors = min(5, len(self.knn_train_target))
        dist, idx = self.knn_index.kneighbors(mat, n_neighbors=n_neighbors)
        neighbours_y = self.knn_train_target[idx]
        weights = 1.0 / np.maximum(dist, 1e-6)
        mean = (neighbours_y * weights).sum(axis=1) / weights.sum(axis=1)
        var = (weights * (neighbours_y - mean[:, None]) ** 2).sum(axis=1) / weights.sum(axis=1)
        return mean, np.sqrt(np.maximum(var, 0.0))

    def confidence(self, X: pd.DataFrame) -> pd.Series:
        """Per-row HIGH/MEDIUM/LOW from model dispersion (T11.2, M04 §3):
        tree std (RF/MissForest), posterior std (MICE/BayesianRidge),
        neighbour dispersion (kNN), in-sample residual std (HistGBM/linear
        fallback -- no native per-row uncertainty API); classifier -> top-
        class predict_proba share. Mapped via `_tier_from_score`."""
        Xp = self._prep(X)

        if self.is_classifier:
            proba = self.estimator.predict_proba(Xp)
            top = proba.max(axis=1)
            return pd.Series([_tier_from_score(float(s)) for s in top], index=X.index, dtype=object)

        if self.method in ("missforest", "rf"):
            preds_per_tree = self._rf_tree_dispersion(Xp)
            mean = preds_per_tree.mean(axis=0)
            std = preds_per_tree.std(axis=0)
        elif self.method == "mice":
            mean, std = self._mice_dispersion(Xp)
        elif self.method == "knn" and self.family == "matrix":
            mean, std = self._knn_dispersion(Xp)
        else:  # histgbm, linear (regression) -- global in-sample residual-std fallback
            mean = self.predict(X).to_numpy(dtype=float)
            std = np.full(len(X), self.train_residual_std, dtype=float)

        with np.errstate(divide="ignore", invalid="ignore"):
            cv = np.where(mean != 0, np.abs(std / mean), np.where(std == 0, 0.0, np.inf))
        score = 1.0 / (1.0 + cv)
        return pd.Series([_tier_from_score(float(s)) for s in score], index=X.index, dtype=object)


def build_ml_imputer(
    gdf: pd.DataFrame,
    target_col: str,
    feature_cols: list[str],
    *,
    method: str = "missforest",
    rng: "np.random.Generator | None" = None,
) -> MLImputer:
    """
    Classical-ML imputer factory (DESIGN §3E / F12 -- T11.1). Fits `method`
    (one of the six-method registry, `_ML_METHOD_NAMES`) on the observed
    complete cases of `gdf[target_col]` against `feature_cols` (default = the
    EUI-free geometry/morphology set, `_DEFAULT_ML_FEATURE_COLS`), returning
    a fitted `MLImputer` with `.predict(X)`/`.confidence(X)`.

    Raises `BelowFloorError` when observed complete cases fall below the
    method's floor (`config.IMPUTE_ML_FLOORS`, M04 §4) -- callers (`_ml_tier`)
    catch this and fall through to the statistical tier.

    Zero-fitted-params (plan §2 rule 3): fits ONLY on `gdf[target_col].notna()`
    rows; `_assert_no_eui_leakage` blocks any EUI column in `feature_cols`/
    `target_col`. Determinism: `random_state=config.RANDOM_SEED` on every
    sklearn estimator that accepts one; frozen hyperparameters (plan §4) --
    no tuning code path exists.
    """
    if method not in _ML_METHOD_NAMES:
        raise ValueError(
            f"build_ml_imputer: unknown method {method!r}. Use one of {_ML_METHOD_NAMES}."
        )

    feature_cols = (
        list(feature_cols) if feature_cols
        else [c for c in _DEFAULT_ML_FEATURE_COLS if c in gdf.columns and c != target_col]
    )
    _assert_no_eui_leakage(list(feature_cols) + [target_col])

    from openubem import config
    seed = config.RANDOM_SEED
    floors = getattr(config, "IMPUTE_ML_FLOORS", _ML_FLOORS)
    floor = floors.get(method, _ML_FLOORS[method])

    observed_mask = gdf[target_col].notna()
    n_observed = int(observed_mask.sum())
    if n_observed < floor:
        raise BelowFloorError(method, n_observed, floor)

    is_classifier = not pd.api.types.is_numeric_dtype(gdf[target_col])
    numeric_features = tuple(c for c in feature_cols if pd.api.types.is_numeric_dtype(gdf[c]))
    categorical_features = tuple(c for c in feature_cols if c not in numeric_features)

    train = gdf.loc[observed_mask]
    feature_medians = {
        c: (float(train[c].median()) if train[c].notna().any() else 0.0)
        for c in numeric_features
    }
    feature_modes = {}
    for c in categorical_features:
        obs = train[c].dropna()
        feature_modes[c] = obs.mode().iat[0] if len(obs) else None

    Xp = train[list(feature_cols)].copy() if feature_cols else train.iloc[:, :0].copy()
    for c in numeric_features:
        Xp[c] = pd.to_numeric(Xp[c], errors="coerce").fillna(feature_medians[c])
    for c in categorical_features:
        Xp[c] = Xp[c].fillna(feature_modes[c])
    y = train[target_col]

    family = "matrix" if (method in ("missforest", "mice", "knn") and not is_classifier) else "supervised"
    cat_encoders: dict = {}
    train_residual_std = 0.0
    knn_index = None
    knn_train_target = None

    if family == "matrix":
        from sklearn.experimental import enable_iterative_imputer  # noqa: F401
        from sklearn.impute import IterativeImputer, KNNImputer
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.linear_model import BayesianRidge
        from sklearn.neighbors import NearestNeighbors

        for c in categorical_features:
            cats = sorted(Xp[c].dropna().unique().tolist())
            mapping = {cat: float(i) for i, cat in enumerate(cats)}
            mapping["__UNKNOWN__"] = float(len(cats))
            cat_encoders[c] = mapping

        feature_matrix_cols = [Xp[c].to_numpy(dtype=float) for c in numeric_features]
        feature_matrix_cols += [
            Xp[c].map(cat_encoders[c]).to_numpy(dtype=float) for c in categorical_features
        ]
        feature_matrix = (
            np.column_stack(feature_matrix_cols) if feature_matrix_cols
            else np.empty((len(Xp), 0))
        )
        fit_matrix = np.column_stack([feature_matrix, y.to_numpy(dtype=float)])

        if method == "missforest":
            base = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=seed)
            estimator = IterativeImputer(estimator=base, max_iter=10, random_state=seed)
        elif method == "mice":
            estimator = IterativeImputer(estimator=BayesianRidge(), max_iter=10, random_state=seed)
        else:  # knn
            estimator = KNNImputer(n_neighbors=5, weights="distance")
        estimator.fit(fit_matrix)

        if method == "knn":
            knn_index = NearestNeighbors(n_neighbors=min(5, len(y)))
            knn_index.fit(feature_matrix)
            knn_train_target = y.to_numpy(dtype=float)
    else:
        from sklearn.compose import ColumnTransformer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler

        preprocess = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), list(numeric_features)),
                ("cat", OneHotEncoder(handle_unknown="ignore"), list(categorical_features)),
            ],
            remainder="drop",
        )
        base = _build_supervised_estimator(method, is_classifier, seed)
        estimator = Pipeline([("prep", preprocess), ("model", base)])
        estimator.fit(Xp, y)

        if not is_classifier and method in ("histgbm", "linear"):
            in_sample = estimator.predict(Xp)
            resid = y.to_numpy(dtype=float) - np.asarray(in_sample, dtype=float)
            train_residual_std = float(np.std(resid)) if len(resid) else 0.0

    return MLImputer(
        method=method, target_col=target_col, feature_cols=tuple(feature_cols),
        is_classifier=is_classifier, floor=floor, n_observed=n_observed, family=family,
        numeric_features=numeric_features, categorical_features=categorical_features,
        feature_medians=feature_medians, feature_modes=feature_modes,
        estimator=estimator, cat_encoders=cat_encoders, seed=seed,
        train_residual_std=train_residual_std, knn_index=knn_index,
        knn_train_target=knn_train_target,
    )


def save_ml_imputer(imputer: MLImputer, path) -> None:
    """Persist a fitted `MLImputer` via joblib (T11.5, DESIGN §3E line 138)."""
    import joblib
    joblib.dump(imputer, path)


def load_ml_imputer(path) -> MLImputer:
    """Reload a joblib-persisted `MLImputer` (T11.5); frozen weights ->
    `.predict`/`.confidence` are byte-identical to the pre-persist model."""
    import joblib
    return joblib.load(path)


# ═══════════════════════════════════════════════════════════════════════════
# T07 — imputation routing subsystem + strict mode (Input-Imputation arc,
# Phase B PINNED CONTRACT). ADDITIVE / STANDALONE: `impute_missing` is a NEW
# entry point consumed directly by the T08/T09 validation harness. It does
# NOT reroute `enrich_semantics` (scope boundary, PINNED CONTRACT) -- the
# 3B->3G fill sequence in `openubem/semantic/__init__.py` is untouched.
#
# `impute_column` stays the low-level primitive; `impute_missing` is the
# router (fusion -> spatial -> ml -> statistical precedence -- reordered at
# T11.3 so the opt-in ML tier precedes the group-median fallback -- per-input
# tier selection, strict "impute-nothing, hard-fail" audit mode).
# ═══════════════════════════════════════════════════════════════════════════

_CANONICAL_TIER_ORDER: tuple[str, ...] = ("fusion", "spatial", "ml", "statistical")

# Continuous attributes impute_missing routes by default in Phase B -- the two
# named in the T07 PINNED CONTRACT ("resolve_vintage, the T05 group-median
# levels path"). `construction_sets.resolve_vintage` / `building_classifier.
# _impute_levels` are themselves monolithic (their own internal spatial-donor
# -> group-mode -> default fallthrough cannot be decomposed into independently
# togglable fusion/spatial/statistical/ml tiers without editing those modules,
# which are out of T07's file scope) -- see the T07 progress-log "Deviations"
# for the full rationale. `impute_missing` instead reimplements the same
# *concept* (spatial neighbour donor, then group-wise stratified fallback)
# generically over any continuous column, reusing the exact same registered
# §5 tokens (`HOTDECK_NEIGHBOR_HIGH`/`_MED`, `GROUPMODE_MED`) rather than
# calling those two functions directly, so every tier is independently
# enable/disable-able as the contract requires. Callers may pass `targets=`
# to route additional continuous columns through the same generic pipeline.
_DEFAULT_TARGETS: tuple[str, ...] = ("year_built", "levels")

_HOTDECK_NEIGHBOR_HIGH = "HOTDECK_NEIGHBOR_HIGH"
_HOTDECK_NEIGHBOR_MED = "HOTDECK_NEIGHBOR_MED"
_GROUPMODE_MED = "GROUPMODE_MED"


class StrictImputationError(RuntimeError):
    """Raised by `impute_missing` when `cfg.strict=True` and gaps remain.

    The "impute-nothing, hard-fail for auditing" mode (T07 PINNED CONTRACT):
    `impute_missing` fills NOTHING under strict mode; it scans the targeted
    attributes for NaN and raises this error listing every still-missing
    ``(attribute, row_index)`` pair in `.missing`.
    """

    def __init__(self, missing: list[tuple[str, object]]):
        self.missing = list(missing)
        preview = ", ".join(f"{attr}@{idx}" for attr, idx in self.missing[:20])
        more = "" if len(self.missing) <= 20 else f" (+{len(self.missing) - 20} more)"
        super().__init__(
            f"impute_missing: strict mode -- {len(self.missing)} residual "
            f"gap(s) would be imputed: {preview}{more}"
        )


@dataclass(frozen=True)
class ImputeConfig:
    """T07 routing config: per-input tier selection + strict/audit mode.

    `enabled_tiers` / `strict` default to `None` (sentinel) and are resolved
    from `openubem.config.IMPUTE_ENABLED_TIERS` / `IMPUTE_STRICT_MODE` at
    *call time* inside `impute_missing` (not at dataclass-construction /
    import time), so a test that monkeypatches those config constants is
    honoured even when the caller passed no explicit `ImputeConfig`.
    """

    enabled_tiers: "tuple[str, ...] | None" = None
    per_input_tiers: "dict[str, tuple[str, ...]] | None" = None
    strict: "bool | None" = None

    def tiers_for(self, attribute: str) -> tuple[str, ...]:
        """Tiers to try, in canonical order, for `attribute`."""
        if self.per_input_tiers and attribute in self.per_input_tiers:
            return self.per_input_tiers[attribute]
        if self.enabled_tiers is not None:
            return self.enabled_tiers
        from openubem import config
        return tuple(config.IMPUTE_ENABLED_TIERS)

    def is_strict(self) -> bool:
        if self.strict is not None:
            return self.strict
        from openubem import config
        return bool(config.IMPUTE_STRICT_MODE)


# E-UTCI-09 height-backfill sub-plan T07(c) -- minimum-height sanity floor.
# 2.1 m = 7 ft, the IRC/IBC (International Residential/Building Code) R305.1
# minimum finished-ceiling height for a habitable storey -- a cited physical
# constant, never swept against any simulated EUI/UTCI output (hard rule 7).
# A fused height/height_m below this floor (e.g. the 0.216 m Overture outlier
# found in the nyc_suburban slice, CP-B ruling) is left NaN for a later tier
# rather than filled -- fusion must never land a physically-impossible value.
_MIN_HEIGHT_FLOOR_M = 2.1
_HEIGHT_FUSION_ATTRS = ("height", "height_m")


def _fusion_tier(gdf, attr: str, mask: pd.Series, rng: np.random.Generator):
    """T07 -- external-data fusion tier (Phase D). Routes `attr` through
    `fusion.fuse` (F-A/F-B: registered `overture`/`lidar`/`assessor` sources,
    precedence read from `config.FUSION_SOURCES_BY_TARGET`). With the default
    config (`FUSION_SOURCES_BY_TARGET = {}`), `precedence_for` returns `[]`
    and this tier is a guaranteed no-op -- `fuse()` never raises and never
    calls out to any source (see F-C'/CP-A).

    Fills only rows in `mask` that fusion resolves to a non-null value,
    carrying the `FUSED_<SOURCE>_HIGH`/`_MED` provenance token `fuse()`
    already stamps (hard rule 6: no value lands without a token). For
    `height`/`height_m`, a fused value below `_MIN_HEIGHT_FLOOR_M` is
    discarded here (left NaN) so a later tier gets a chance instead of a
    physically-impossible height silently landing (CP-B ruling on T07(c)).
    """
    is_numeric = (
        pd.api.types.is_numeric_dtype(gdf[attr]) if attr in gdf.columns else True
    )
    value = (
        pd.Series(np.nan, index=gdf.index, dtype=float) if is_numeric
        else pd.Series([None] * len(gdf), index=gdf.index, dtype=object)
    )
    token = pd.Series([None] * len(gdf), index=gdf.index, dtype=object)
    if not mask.any():
        return value, token

    from openubem.semantic import fusion

    fused_value, fused_token = fusion.fuse(gdf, attr)
    hit = mask & fused_value.notna()
    if attr in _HEIGHT_FUSION_ATTRS and hit.any():
        below_floor = hit & (pd.to_numeric(fused_value, errors="coerce") < _MIN_HEIGHT_FLOOR_M)
        hit = hit & ~below_floor
    if not hit.any():
        return value, token

    value.loc[hit] = fused_value.loc[hit]
    token.loc[hit] = fused_token.loc[hit]
    return value, token


_ML_TOKEN_HIGH = "HIGH"
_ML_TOKEN_MED = "MED"


def _ml_method_for(attr: str) -> str:
    from openubem import config
    overrides = getattr(config, "IMPUTE_ML_METHOD_BY_TARGET", {})
    return overrides.get(attr, "missforest")


def _ml_feature_cols_for(gdf, attr: str) -> list:
    cols = [c for c in _DEFAULT_ML_FEATURE_COLS if c in gdf.columns and c != attr]
    if attr == "year_built" and "geometry" in getattr(gdf, "columns", []):
        cols = cols + [_YEAR_BUILT_SPATIAL_LAG_COL]
    return cols


def _ml_tier(gdf, attr: str, mask: pd.Series, rng: np.random.Generator):
    """T11.3 -- real classical-ML tier (Phase C, `build_ml_imputer`). Checks
    the per-target complete-case floor; below floor -> all-null `(value,
    token)` (fall through to statistical, M04 §4 -- a legitimate, documented
    outcome, not an error). Mirrors `_spatial_tier` (imputation.py §5-D):
    HIGH/MEDIUM confidence fills only, LOW discarded and left for the next
    tier. Opt-in only -- reached only when a caller explicitly enables `ml`
    for `attr` (never in `config.IMPUTE_ENABLED_TIERS`'s default tuple)."""
    is_numeric = pd.api.types.is_numeric_dtype(gdf[attr])
    value = (
        pd.Series(np.nan, index=gdf.index, dtype=float) if is_numeric
        else pd.Series([None] * len(gdf), index=gdf.index, dtype=object)
    )
    token = pd.Series([None] * len(gdf), index=gdf.index, dtype=object)
    if not mask.any():
        return value, token

    method = _ml_method_for(attr)
    feature_cols = _ml_feature_cols_for(gdf, attr)

    work = gdf
    if attr == "year_built" and _YEAR_BUILT_SPATIAL_LAG_COL in feature_cols:
        work = gdf.copy()
        work[_YEAR_BUILT_SPATIAL_LAG_COL] = _spatial_lag(gdf, "year_built")

    try:
        imputer = build_ml_imputer(work, attr, feature_cols, method=method, rng=rng)
    except BelowFloorError:
        return value, token

    rows = gdf.index[mask]
    X = work.loc[rows]
    preds = imputer.predict(X)
    confs = imputer.confidence(X)
    for idx in rows:
        conf = confs.loc[idx]
        val = preds.loc[idx]
        if conf in ("HIGH", "MEDIUM") and pd.notna(val):
            value.loc[idx] = val
            suffix = _ML_TOKEN_HIGH if conf == "HIGH" else _ML_TOKEN_MED
            token.loc[idx] = f"ML_{method.upper()}_{suffix}"
    return value, token


def _spatial_tier(gdf, attr: str, mask: pd.Series, rng: np.random.Generator):
    """Generic T06 spatial-donor fill, dispatched on `attr`'s dtype (T07.2).

    Continuous (``pd.api.types.is_numeric_dtype``) -- UNCHANGED from Phase B:
    direct consumption of the ratified T06 4-tuple interface (carry-forward
    #3): ``(value, dispersion, confidence, gdf_out)``, all aligned to
    ``gdf.index``. Fills only non-null ``value`` rows within ``mask``, HIGH/
    MEDIUM confidence only (LOW discarded -- matches the `resolve_vintage`
    precedent, `construction_sets.py`); MNAR-blocked/no-donor rows fall
    through untouched (does not re-run the MNAR filter -- trusts T06's
    output, per the PINNED CONTRACT).

    Categorical (else) -- T07.2: same precedent via T06's `neighbour_vote`
    (fixed `DEFAULT_K`/`DEFAULT_RADIUS_M`/`mnar_threshold`, never overridden),
    same HIGH/MEDIUM-only acceptance and MNAR fall-through.
    """
    if pd.api.types.is_numeric_dtype(gdf[attr]):
        value = pd.Series(np.nan, index=gdf.index, dtype=float)
        token = pd.Series([None] * len(gdf), index=gdf.index, dtype=object)
        if not mask.any() or "geometry" not in getattr(gdf, "columns", []):
            return value, token

        from openubem.semantic.spatial_impute import knn_fill

        s_value, _dispersion, s_confidence, _gdf_out = knn_fill(gdf, attr)
        for idx in gdf.index[mask]:
            conf = s_confidence.loc[idx]
            val = s_value.loc[idx]
            if conf in ("HIGH", "MEDIUM") and pd.notna(val):
                value.loc[idx] = val
                token.loc[idx] = (
                    _HOTDECK_NEIGHBOR_HIGH if conf == "HIGH" else _HOTDECK_NEIGHBOR_MED
                )
        return value, token

    value = pd.Series([None] * len(gdf), index=gdf.index, dtype=object)
    token = pd.Series([None] * len(gdf), index=gdf.index, dtype=object)
    if not mask.any() or "geometry" not in getattr(gdf, "columns", []):
        return value, token

    from openubem.semantic.spatial_impute import neighbour_vote

    s_value, _agreement, s_confidence, _gdf_out = neighbour_vote(gdf, attr, rng=rng)
    for idx in gdf.index[mask]:
        conf = s_confidence.loc[idx]
        val = s_value.loc[idx]
        if conf in ("HIGH", "MEDIUM") and pd.notna(val):
            value.loc[idx] = val
            token.loc[idx] = (
                _HOTDECK_NEIGHBOR_HIGH if conf == "HIGH" else _HOTDECK_NEIGHBOR_MED
            )
    return value, token


def _observed_mode(values, rng: np.random.Generator):
    """Mode of an observed-values collection; `None` if empty. Ties broken by
    `rng.choice` over the tied winners -- same pattern as `neighbour_vote`'s
    donor-vote tie-break (T04/T06 seeded-rng convention)."""
    arr = pd.Series(values).dropna().to_numpy()
    if arr.size == 0:
        return None
    uniq, counts = np.unique(arr, return_counts=True)
    winners = uniq[counts == counts.max()]
    return rng.choice(winners) if len(winners) > 1 else winners[0]


def _statistical_tier(gdf, attr: str, mask: pd.Series, rng: np.random.Generator):
    """Generic group-wise stratified fallback, dispatched on `attr`'s dtype
    (T07.2).

    Continuous (``pd.api.types.is_numeric_dtype``) -- UNCHANGED from Phase B:
    group-wise stratified MEDIAN (T04/T05 group-median concept), fit on
    observed rows only (no leakage), stratified by `use_class` if present
    else `archetype_id`, with a global-observed-median fallback for an
    empty/absent stratum. Reuses the registered `GROUPMODE_MED` token. If
    there are zero observed values for `attr` anywhere, this tier cannot help
    and leaves rows null (falls through to `ml`/remains unfilled).

    Categorical (else) -- T07.2: same concept, group-wise stratified MODE
    (not median) with a seeded-rng tie-break (`_observed_mode`), global-
    observed-mode fallback, same `GROUPMODE_MED` token. Self-stratification
    guard: when `attr` itself is a strat candidate (imputing `use_class`),
    that candidate is skipped -- stratifying a column by itself is circular/
    leaky (T07.2 PINNED CONTRACT).
    """
    if pd.api.types.is_numeric_dtype(gdf[attr]):
        value = pd.Series(np.nan, index=gdf.index, dtype=float)
        token = pd.Series([None] * len(gdf), index=gdf.index, dtype=object)
        if not mask.any():
            return value, token

        observed_mask = gdf[attr].notna()
        if not observed_mask.any():
            return value, token

        strat_col = None
        for candidate in ("use_class", "archetype_id"):
            if candidate in gdf.columns:
                strat_col = candidate
                break

        global_median = float(gdf.loc[observed_mask, attr].median())
        group_median: dict = {}
        if strat_col is not None:
            group_median = (
                gdf.loc[observed_mask].groupby(strat_col)[attr].median().to_dict()
            )

        for idx in gdf.index[mask]:
            stratum = gdf.at[idx, strat_col] if strat_col is not None else None
            value.loc[idx] = group_median.get(stratum, global_median)
            token.loc[idx] = _GROUPMODE_MED
        return value, token

    value = pd.Series([None] * len(gdf), index=gdf.index, dtype=object)
    token = pd.Series([None] * len(gdf), index=gdf.index, dtype=object)
    if not mask.any():
        return value, token

    observed_mask = gdf[attr].notna()
    if not observed_mask.any():
        return value, token

    strat_col = None
    for candidate in ("use_class", "archetype_id"):
        if candidate == attr:
            continue  # leakage guard -- never stratify a column by itself
        if candidate in gdf.columns:
            strat_col = candidate
            break

    global_mode = _observed_mode(gdf.loc[observed_mask, attr], rng)
    group_mode: dict = {}
    if strat_col is not None:
        for stratum, group in gdf.loc[observed_mask].groupby(strat_col)[attr]:
            group_mode[stratum] = _observed_mode(group, rng)

    for idx in gdf.index[mask]:
        stratum = gdf.at[idx, strat_col] if strat_col is not None else None
        chosen = group_mode.get(stratum, global_mode)
        if chosen is None:
            chosen = global_mode
        if chosen is None:
            continue
        value.loc[idx] = chosen
        token.loc[idx] = _GROUPMODE_MED
    return value, token


# Name-string registry (not direct function references) resolved via
# `globals()` at call time in `impute_missing`, so tests may monkeypatch the
# module-level `_spatial_tier`/`_statistical_tier`/etc. names directly.
_TIER_HANDLER_NAMES = {
    "fusion": "_fusion_tier",
    "spatial": "_spatial_tier",
    "statistical": "_statistical_tier",
    "ml": "_ml_tier",
}


def impute_missing(gdf, cfg: "ImputeConfig | None" = None, targets=None, rng=None):
    """T07 routing orchestrator (Phase B) -- ADDITIVE / STANDALONE.

    Per targeted attribute, chains fallbacks in the research-mandated
    precedence ``fusion -> spatial -> ml -> statistical`` (only the tiers in
    ``cfg.enabled_tiers`` / ``cfg.per_input_tiers[attr]``, tried in that
    canonical order); for each still-NaN row the first enabled tier
    returning a non-null value wins and stamps that tier's provenance token
    (via the §5 registry vocabulary); rows a tier leaves null fall through
    to the next tier. Disabled tiers are never called (no stub-fill).

    Does **not** reroute `enrich_semantics` (T07 PINNED CONTRACT scope
    boundary) -- this is a new entry point for the T08/T09 validation
    harness to call directly.

    Fit-on-complete-case-only / no leakage: every tier fits from observed
    rows only; nothing here reads EUI (zero-fitted-params). All stochastic
    draws flow through ``np.random.default_rng(config.RANDOM_SEED)``.

    Args:
        gdf: (Geo)DataFrame to fill (a copy is returned; `gdf` is untouched).
        cfg: `ImputeConfig`; `None` builds a default `ImputeConfig()`.
        targets: iterable of column names to route; `None` defaults to the
            Phase-B-known continuous attributes present in `gdf`
            (`year_built`, `levels`).
        rng: `np.random.Generator`; `None` uses
            `np.random.default_rng(config.RANDOM_SEED)`.

    Strict mode (`cfg.strict` / `config.IMPUTE_STRICT_MODE`): fills NOTHING --
    scans the targeted attributes for NaN and raises `StrictImputationError`
    listing every still-missing `(attribute, row_index)` pair; returns `gdf`
    unchanged (copy) if none are missing.
    """
    if cfg is None:
        cfg = ImputeConfig()
    if rng is None:
        from openubem.config import RANDOM_SEED
        rng = np.random.default_rng(RANDOM_SEED)
    if targets is None:
        targets = [t for t in _DEFAULT_TARGETS if t in gdf.columns]

    if cfg.is_strict():
        missing: list[tuple[str, object]] = []
        for attr in targets:
            for idx in gdf.index[gdf[attr].isna()]:
                missing.append((attr, idx))
        if missing:
            raise StrictImputationError(missing)
        return gdf.copy()

    from openubem.semantic import provenance as prov

    out = gdf.copy()
    for attr in targets:
        tiers = cfg.tiers_for(attr)
        remaining = out[attr].isna()
        if not remaining.any():
            continue

        prov_col = f"provenance_{attr}"
        if prov_col not in out.columns:
            out[prov_col] = pd.Series([""] * len(out), index=out.index, dtype=object)

        for tier in _CANONICAL_TIER_ORDER:
            if tier not in tiers or not remaining.any():
                continue
            handler = globals()[_TIER_HANDLER_NAMES[tier]]
            value, tok = handler(out, attr, remaining, rng)
            filled = remaining & value.notna()
            if not filled.any():
                continue
            out.loc[filled, attr] = value.loc[filled]
            out.loc[filled, prov_col] = tok.loc[filled]
            for tok_value in tok.loc[filled].unique():
                tok_mask = filled & (tok == tok_value)
                out = prov.append_flag(out, tok_value, mask=tok_mask)
            remaining = remaining & ~filled
    return out
