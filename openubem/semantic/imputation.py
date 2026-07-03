"""Module 06: KDE/PDE imputation and ML imputer stub (DESIGN §3E)."""
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


# ═══════════════════════════════════════════════════════════════════════════
# T07 — imputation routing subsystem + strict mode (Input-Imputation arc,
# Phase B PINNED CONTRACT). ADDITIVE / STANDALONE: `impute_missing` is a NEW
# entry point consumed directly by the T08/T09 validation harness. It does
# NOT reroute `enrich_semantics` (scope boundary, PINNED CONTRACT) -- the
# 3B->3G fill sequence in `openubem/semantic/__init__.py` is untouched.
#
# `impute_column` stays the low-level primitive; `impute_missing` is the
# router (fusion -> spatial -> statistical -> ml precedence, per-input tier
# selection, strict "impute-nothing, hard-fail" audit mode).
# ═══════════════════════════════════════════════════════════════════════════

_CANONICAL_TIER_ORDER: tuple[str, ...] = ("fusion", "spatial", "statistical", "ml")

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


def _fusion_tier(gdf, attr: str, mask: pd.Series, rng: np.random.Generator):
    """Phase-D skeleton hook (external-data fusion precedence layer, T12) --
    NOT built. Raises when force-enabled; never called by default (`fusion`
    is excluded from `config.IMPUTE_ENABLED_TIERS`)."""
    raise NotImplementedError("fusion tier is Phase D")


def _ml_tier(gdf, attr: str, mask: pd.Series, rng: np.random.Generator):
    """Phase-C skeleton hook (classical-ML imputer, T11) -- `build_ml_imputer`
    still raises `NotImplementedError`; NOT caught/swallowed here (the tier
    honestly isn't built yet). Never called by default."""
    return build_ml_imputer(gdf, attr, [])


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
    precedence ``fusion -> spatial -> statistical -> ml`` (only the tiers in
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
