"""T11.8c-diag -- per-cell (PRODUCTION-granularity) raw-knn vs Phase-A
do-no-harm diagnostic on a floor-clearing cell.

The original CP-3 -5.51% NMBE was measured on a POOLED fit (all 12 cells,
2247 obs year_built) then sliced to nyc_centre -- but production imputes
PER-CELL (`enrich_semantics`/`impute_missing` runs on one cell's gdf at a
time; `build_ml_imputer` fits on THAT gdf's complete cases only). nyc_centre
alone has only 158 observed year_built -- below knn's >=200 floor -- so knn
never fires there in production; it falls through to Phase-A. This script
tests the one genuinely open question (manager reframe, PLAN_phaseC_ml_
imputer.md Sec8 "CP-3b-local AUDIT ... REFRAME", 2026-07-14): at PRODUCTION
(per-cell) granularity, on a cell that DOES clear the knn floor
(la_suburban, 1295 obs; la_urban, 542 obs), does raw knn (NO de-bias) do
harm vs Phase-A at all?

Method: subset the pooled 12-cell frame to ONE cell FIRST, then run
impute_missing on that single-cell frame alone (Phase-A vs raw-knn,
IMPUTE_DEBIAS_NEWERSKEW left at its all-False default). This reproduces
production granularity exactly -- knn (if it fires) fits only on that
cell's own complete cases, never a pooled cross-city donor pool.

Adapted (not rewritten) from t11_8_cp3b_local_field_diff.py: only change is
subset-to-cell-before-impute instead of pool-then-slice-after-impute, and
looping over multiple cells. `fill()`/`vintage_bin()`/`bin_rank()` bodies
are otherwise identical to the T11.8 script.

Report-only. Nothing here is fed back into any config/imputer setting.
NO de-bias (IMPUTE_DEBIAS_NEWERSKEW stays at its shipped all-False default).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from t11_cp3_leaderboard import load_pooled  # noqa: E402

from openubem import config
from openubem.semantic.construction_sets import _YEAR_BINS, _YEAR_LABELS
from openubem.semantic.imputation import ImputeConfig, impute_missing

SEED = 42
CELLS = ["la_suburban", "la_urban"]


def bin_rank(vintage_series):
    """Ordinal rank of each vintage label within _YEAR_LABELS (0=oldest ..
    4=newest) -- lets us compute a signed 'directional' mean bin-shift, not
    just a raw divergence count."""
    rank_map = {label: i for i, label in enumerate(_YEAR_LABELS)}
    return vintage_series.map(rank_map)


def fill(cell_gdf, method):
    """method=None -> Phase-A (spatial,statistical). method='knn' -> raw knn
    (spatial,ml,statistical), de-bias flag left at its all-False default
    (NOT touched here -- per T11.8c-diag binding rule 3)."""
    orig_method = dict(config.IMPUTE_ML_METHOD_BY_TARGET)
    assert all(v is False for v in config.IMPUTE_DEBIAS_NEWERSKEW.values()), (
        "IMPUTE_DEBIAS_NEWERSKEW must stay at its shipped all-False default for this diagnostic"
    )
    try:
        if method is None:
            cfg = ImputeConfig(enabled_tiers=("spatial", "statistical"))
        else:
            config.IMPUTE_ML_METHOD_BY_TARGET["year_built"] = method
            cfg = ImputeConfig(enabled_tiers=("spatial", "ml", "statistical"))
        out = impute_missing(cell_gdf, cfg=cfg, targets=["year_built"], rng=np.random.default_rng(SEED))
    finally:
        config.IMPUTE_ML_METHOD_BY_TARGET.clear()
        config.IMPUTE_ML_METHOD_BY_TARGET.update(orig_method)
    assert out["year_built"].notna().all()
    return out


def vintage_bin(series):
    import pandas as pd
    numeric = pd.to_numeric(series, errors="coerce")
    out = pd.cut(
        numeric.astype(float), bins=[-np.inf] + _YEAR_BINS + [np.inf],
        labels=_YEAR_LABELS, right=False, ordered=False,
    ).astype(str)
    return out


def main():
    pooled = load_pooled()

    for cell in CELLS:
        print("\n" + "#" * 78)
        print(f"# CELL: {cell} (production-granularity: subset BEFORE impute)")
        print("#" * 78)

        cell_gdf = pooled[pooled["city"] == cell].copy()
        n_cell = len(cell_gdf)
        n_obs = int(cell_gdf["year_built"].notna().sum())
        n_missing = n_cell - n_obs
        floor = config.IMPUTE_ML_FLOORS["knn"]
        print(f"n_total={n_cell}, observed year_built={n_obs}, missing={n_missing}, knn floor={floor}")
        print(f"floor cleared: {n_obs >= floor}")

        gdf_a = fill(cell_gdf, None)
        gdf_raw = fill(cell_gdf, "knn")

        # did knn actually fire per-cell? count ML_KNN_* provenance tokens
        prov_raw = gdf_raw["provenance_year_built"]
        ml_fired = int(prov_raw.fillna("").str.startswith("ML_KNN").sum())
        prov_counts_raw = prov_raw.fillna("<UNFILLED-OR-OBSERVED>").value_counts().to_dict()
        print(f"\nprovenance_year_built counts (raw-knn run):\n  {prov_counts_raw}")
        print(f"ML_KNN_* fired on {ml_fired}/{n_missing} originally-missing rows")

        vb_a = vintage_bin(gdf_a["year_built"])
        vb_raw = vintage_bin(gdf_raw["year_built"])

        rank_a = bin_rank(vb_a)
        rank_raw = bin_rank(vb_raw)

        gap_raw = float((rank_raw - rank_a).mean())
        n_diff_raw = int((vb_a.to_numpy() != vb_raw.to_numpy()).sum())

        print(f"\nvintage_bin distribution -- Phase-A:\n{vb_a.value_counts()}")
        print(f"\nvintage_bin distribution -- Phase-C knn RAW (production-granularity, no de-bias):\n{vb_raw.value_counts()}")

        print(f"\nvintage-bin divergence vs Phase-A: RAW={n_diff_raw}/{n_cell}")
        print(f"mean DIRECTIONAL vintage-bin gap vs Phase-A (positive = newer skew, bin-rank units): {gap_raw:+.4f}")

        print("\n" + "=" * 70)
        if ml_fired == 0:
            print(f"RESULT ({cell}): knn did NOT fire per-cell (0 ML_KNN_* tokens) -- "
                  f"floor not cleared or all missing rows fell through. Raw-knn is "
                  f"IDENTICAL to Phase-A here by construction (no ml fills occurred).")
        else:
            print(f"RESULT ({cell}): knn FIRED per-cell on {ml_fired} row(s). "
                  f"Directional gap vs Phase-A = {gap_raw:+.4f} bin-rank units.")
        print("=" * 70)


if __name__ == "__main__":
    main()
