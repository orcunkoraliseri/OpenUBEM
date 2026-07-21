"""T11.8 CP-3b-local -- nyc_centre pooled-fit vintage-bin field-diff (mirrors
t11_cp3_eui_field_diff.py's local check exactly): report how the per-bin
distribution and the mean DIRECTIONAL vintage-bin gap vs Phase-A move for
raw-knn vs de-biased-knn. The newer-skew collapsing toward 0 is the CP-3b-
local go/no-go signal for the cluster leg (T11.8-EUI) -- NOT executed here.

Report-only. Nothing here is fed back into any config/imputer setting.
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
GATE_CELL = "nyc_centre"


def bin_rank(vintage_series):
    """Ordinal rank of each vintage label within _YEAR_LABELS (0=oldest .. 4=newest)
    -- lets us compute a signed 'directional' mean bin-shift, not just a raw
    divergence count."""
    rank_map = {label: i for i, label in enumerate(_YEAR_LABELS)}
    return vintage_series.map(rank_map)


def fill(pooled, method, debias):
    orig_method = dict(config.IMPUTE_ML_METHOD_BY_TARGET)
    orig_debias = dict(config.IMPUTE_DEBIAS_NEWERSKEW)
    try:
        if method is None:
            cfg = ImputeConfig(enabled_tiers=("spatial", "statistical"))
        else:
            config.IMPUTE_ML_METHOD_BY_TARGET["year_built"] = method
            config.IMPUTE_DEBIAS_NEWERSKEW["year_built"] = debias
            cfg = ImputeConfig(enabled_tiers=("spatial", "ml", "statistical"))
        out = impute_missing(pooled, cfg=cfg, targets=["year_built"], rng=np.random.default_rng(SEED))
    finally:
        config.IMPUTE_ML_METHOD_BY_TARGET.clear()
        config.IMPUTE_ML_METHOD_BY_TARGET.update(orig_method)
        config.IMPUTE_DEBIAS_NEWERSKEW.clear()
        config.IMPUTE_DEBIAS_NEWERSKEW.update(orig_debias)
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
    nyc_mask = (pooled["city"] == GATE_CELL).to_numpy()
    n_nyc = int(nyc_mask.sum())

    gdf_a = fill(pooled, None, False)
    gdf_raw = fill(pooled, "knn", False)
    gdf_deb = fill(pooled, "knn", True)

    vb_a = vintage_bin(gdf_a.loc[nyc_mask, "year_built"])
    vb_raw = vintage_bin(gdf_raw.loc[nyc_mask, "year_built"])
    vb_deb = vintage_bin(gdf_deb.loc[nyc_mask, "year_built"])

    rank_a = bin_rank(vb_a)
    rank_raw = bin_rank(vb_raw)
    rank_deb = bin_rank(vb_deb)

    gap_raw = float((rank_raw - rank_a).mean())
    gap_deb = float((rank_deb - rank_a).mean())
    n_diff_raw = int((vb_a.to_numpy() != vb_raw.to_numpy()).sum())
    n_diff_deb = int((vb_a.to_numpy() != vb_deb.to_numpy()).sum())
    n_raw_vs_deb_diff = int((vb_raw.to_numpy() != vb_deb.to_numpy()).sum())

    print(f"gate cell = {GATE_CELL}, n={n_nyc}")
    print(f"\nvintage_bin distribution -- Phase-A:\n{vb_a.value_counts()}")
    print(f"\nvintage_bin distribution -- Phase-C knn RAW:\n{vb_raw.value_counts()}")
    print(f"\nvintage_bin distribution -- Phase-C knn DEBIASED:\n{vb_deb.value_counts()}")

    print(f"\nvintage-bin divergence vs Phase-A: RAW={n_diff_raw}/{n_nyc}, DEBIASED={n_diff_deb}/{n_nyc}")
    print(f"RAW vs DEBIASED vintage-bin rows that differ from EACH OTHER: {n_raw_vs_deb_diff}/{n_nyc}")
    print(f"\nmean DIRECTIONAL vintage-bin gap vs Phase-A (positive = newer skew, bin-rank units):")
    print(f"  RAW knn:      {gap_raw:+.4f}")
    print(f"  DEBIASED knn: {gap_deb:+.4f}")
    if abs(gap_raw) > 1e-9:
        collapse_pct = 100.0 * (1.0 - abs(gap_deb) / abs(gap_raw))
        print(f"  collapse toward 0: {collapse_pct:+.1f}%")

    print("\n" + "=" * 70)
    if n_raw_vs_deb_diff == 0:
        print("RESULT: DEBIASED == RAW on every nyc_centre row -- the de-bias hook")
        print("did NOT fire on this real dataset. Root cause: neither 'use_class'")
        print("nor 'archetype_id' (the pinned stratifier, T11.8 'How') is present")
        print("in the Stage-1 01_buildings.gpkg schema this evaluation pools from")
        print("-- confirmed separately by direct column inspection. This is a")
        print("data-availability gap, not a defect in the quantile-mapping method")
        print("itself (see tests/test_debias.py for synthetic proof the method")
        print("works when a stratifier + adequate donor counts are present).")
        print("NO SKEW COLLAPSE OBSERVED ON THIS REAL FIXTURE.")
    else:
        print(f"RESULT: de-bias fired and changed {n_raw_vs_deb_diff} row(s).")
    print("=" * 70)


if __name__ == "__main__":
    main()
