"""T11.8 -- reusable, tier-agnostic newer-skew de-bias corrector (Phase C,
PLAN_phaseC_ml_imputer.md T11.8, docs_ACTIVE/input/imputation/docs_Done/).

CP-3's EUI do-no-harm leg failed at NMBE -5.51% because the winning `knn`
tier neighbour-averages `year_built` toward the denser/newer urban-core
stock -- a one-directional systematic bias, not scatter. The fix here
corrects the SHAPE of the imputed marginal via stratified empirical
quantile-mapping: transport each raw fill onto the observed-donor
distribution at the SAME rank the fill holds within the raw-fill set.

Zero-fitted-params (plan §2 rule 3 / T11.8 "How"): the transform is
determined ONLY by two empirical CDFs of OBSERVED data (the fill ranks and
the observed-donor marginal); nothing here ever reads an EUI/`total_eui`/
`*_eui_kwh_m2` column. `min_donors=30` is a fixed convention, never swept
against EUI. Pure functions over `pd.Series`; no side effects.

Consumed by `imputation._ml_tier`'s opt-in `config.IMPUTE_DEBIAS_NEWERSKEW`
hook -- default all-False, so every existing run (including opt-in-`ml`
runs that do not set the flag) is byte-identical to pre-T11.8.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Fixed convention (T11.8 "How") -- never swept against EUI or any other
# downstream signal.
DEFAULT_MIN_DONORS = 30


def debias_newer_skew(
    raw_fills: pd.Series,
    observed_donors: pd.Series,
    *,
    rng: "np.random.Generator | None" = None,
    min_donors: int = DEFAULT_MIN_DONORS,
) -> pd.Series:
    """Empirical quantile-mapping: for each raw fill `f`, compute its rank
    within the raw-fill set (`ECDF_fills(f)`, pandas `.rank(pct=True)`,
    deterministic average tie-break) and return the SAME quantile of the
    observed-donor distribution (linear interpolation over the sorted donor
    array, `np.interp`). This transports the fills onto the observed
    marginal while PRESERVING the neighbour-vote's rank order (the signal
    `knn` did capture) and simultaneously undoes both the newer-shift and
    the variance-compression of averaging.

    `rng` is accepted for API symmetry with the other tier handlers and the
    project's determinism convention (`np.random.default_rng(config.
    RANDOM_SEED)`), but is not consumed: rank-with-average-tie-break and
    linear-interpolation quantile mapping have no free/random component --
    the output is deterministic by construction for a given
    (raw_fills, observed_donors) pair (T11.8 "Determinism").

    Below `min_donors` observed donors -> returns `raw_fills` UNCHANGED (a
    thin-donor-pool decline; never fabricate a transform from a handful of
    points). Rows where `raw_fills` is NaN are left NaN.
    """
    donors = observed_donors.dropna().astype(float)
    out = raw_fills.copy()
    if len(donors) < min_donors:
        return out

    fills = raw_fills.dropna().astype(float)
    if len(fills) == 0:
        return out

    donors_sorted = np.sort(donors.to_numpy())
    n_d = len(donors_sorted)
    pct_rank = fills.rank(method="average", pct=True).to_numpy()  # in (0, 1]
    positions = pct_rank * (n_d - 1)
    mapped = np.interp(positions, np.arange(n_d), donors_sorted)
    out.loc[fills.index] = mapped
    return out


def _thin_strata(
    observed_donors: pd.Series,
    strata: pd.Series,
    min_donors: int = DEFAULT_MIN_DONORS,
) -> set:
    """Stratum labels whose observed-donor count (donors grouped by `strata`,
    reindexed onto `observed_donors`' rows) is below `min_donors`. Shared by
    `debias_stratified` (skip logic, below) and `imputation._ml_tier`
    (per-row `DEBIAS_NEWERSKEW_QMAP` vs `DEBIAS_SKIPPED_THINSTRATUM`
    provenance tagging) so both use the IDENTICAL thin-stratum
    classification -- never re-derived independently."""
    donors = observed_donors.dropna()
    donor_strata = strata.reindex(donors.index)
    counts = donor_strata.value_counts(dropna=True)
    all_labels = set(strata.dropna().unique())
    return {s for s in all_labels if counts.get(s, 0) < min_donors}


def debias_stratified(
    raw_fills: pd.Series,
    observed_donors: pd.Series,
    strata: pd.Series,
    *,
    rng: "np.random.Generator | None" = None,
    min_donors: int = DEFAULT_MIN_DONORS,
) -> pd.Series:
    """`debias_newer_skew` applied WITHIN each stratum. `strata` is index-
    aligned pd.Series covering BOTH `raw_fills.index` and
    `observed_donors.index` (the same stratifier the fill used --
    `use_class` if present else `archetype_id`, T11.8). A stratum with
    `< min_donors` observed donors is skipped (every row in that stratum
    keeps its raw fill, unchanged) -- never fabricate a transform from a
    handful of points. Rows whose stratum is NaN (missing stratifier) are
    left unchanged (cannot be safely stratified).
    """
    out = raw_fills.copy()
    fill_strata = strata.reindex(raw_fills.index)
    donor_strata = strata.reindex(observed_donors.index)
    for stratum in fill_strata.dropna().unique():
        fill_idx = fill_strata.index[fill_strata == stratum]
        donor_idx = donor_strata.index[donor_strata == stratum]
        stratum_fills = raw_fills.loc[fill_idx]
        stratum_donors = observed_donors.loc[donor_idx]
        corrected = debias_newer_skew(
            stratum_fills, stratum_donors, rng=rng, min_donors=min_donors
        )
        out.loc[fill_idx] = corrected
    return out
