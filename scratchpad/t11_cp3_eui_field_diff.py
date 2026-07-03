"""T11.6 CP-3 EUI do-no-harm guard -- LOCAL vintage-bin field-diff (primary method).

Per PLAN_phaseC_ml_imputer.md T11.6 point 2: for the WINNING config (knn --
the only method that beats Phase-A on BOTH year_built and levels without a
catastrophic linear-extrapolation blowup, see t11_cp3_leaderboard.py), fill
the REAL missing `year_built` gaps on the pooled real-city frame (fit draws
on the pool to clear the floor -- same construction as the headline
leaderboard), slice to the gate cell (nyc_centre), and diff the imputed
values' VINTAGE BIN using the actual production `resolve_vintage` binning
(construction_sets._YEAR_BINS/_YEAR_LABELS via `pd.cut`, REUSED not
reimplemented) between Phase-A and Phase-C(knn).

Why vintage bin, not raw year_built: DESIGN §3B/F3-F4 -- `year_built` only
ever reaches an IDF-relevant field through `VINTAGE_U_FACTORS[vintage_standard]`
(construction_sets.py) -- envelope U-factors are a deterministic function of
the discrete 5-bin `vintage_standard` token, not the raw year. HVAC/DHW/
cooking/refrigeration do not depend on vintage at all (E-R3-3 baseline). So
identical vintage bins on every EUI-relevant row is a formally sufficient
condition for a zero downstream EUI delta -- no IDF build/cluster A/B needed
to additionally prove what is already a deterministic consequence of the
(unchanged) `VINTAGE_U_FACTORS` mapping.

Report-only. Nothing here is fed back into `ImputeConfig`/imputer settings.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from t11_cp3_leaderboard import load_pooled  # noqa: E402

from openubem import config
from openubem.semantic.imputation import ImputeConfig, impute_missing
from openubem.semantic.construction_sets import resolve_vintage

SEED = 42
WINNING_METHOD = "knn"
GATE_CELL = "nyc_centre"


def main():
    pooled = load_pooled()
    nyc_mask = (pooled["city"] == GATE_CELL).to_numpy()
    n_nyc = int(nyc_mask.sum())
    n_nyc_missing = int(pooled.loc[nyc_mask, "year_built"].isna().sum())
    print(f"gate cell = {GATE_CELL}: n={n_nyc}, originally-missing year_built={n_nyc_missing}")

    cfg_a = ImputeConfig(enabled_tiers=("spatial", "statistical"))
    gdf_a = impute_missing(pooled, cfg=cfg_a, targets=["year_built"], rng=np.random.default_rng(SEED))
    assert gdf_a["year_built"].notna().all(), "Phase-A left unfilled year_built gaps -- unexpected"

    orig_method = dict(config.IMPUTE_ML_METHOD_BY_TARGET)
    try:
        config.IMPUTE_ML_METHOD_BY_TARGET["year_built"] = WINNING_METHOD
        cfg_c = ImputeConfig(enabled_tiers=("spatial", "ml", "statistical"))
        gdf_c = impute_missing(pooled, cfg=cfg_c, targets=["year_built"], rng=np.random.default_rng(SEED))
    finally:
        config.IMPUTE_ML_METHOD_BY_TARGET.clear()
        config.IMPUTE_ML_METHOD_BY_TARGET.update(orig_method)
    assert gdf_c["year_built"].notna().all(), "Phase-C left unfilled year_built gaps -- unexpected"

    # "Everything else common-mode": both frames are the same pooled input,
    # differing ONLY in the imputed year_built column (+ its own provenance/
    # data_quality_flag bookkeeping) -- verify structurally.
    other_cols = [c for c in pooled.columns if c not in ("year_built", "provenance_year_built", "data_quality_flag")]
    for c in other_cols:
        a_vals = gdf_a[c]
        c_vals = gdf_c[c]
        if a_vals.dtype.kind in "fc":
            same = np.allclose(a_vals.to_numpy(dtype=float), c_vals.to_numpy(dtype=float), equal_nan=True)
        else:
            same = a_vals.astype(str).equals(c_vals.astype(str))
        assert same, f"common-mode violation on column {c!r} -- Phase-A/Phase-C frames diverge outside year_built"
    print("common-mode check: every column except year_built/provenance_year_built/data_quality_flag is IDENTICAL between Phase-A and Phase-C frames.")

    yb_a = gdf_a.loc[nyc_mask, "year_built"]
    yb_c = gdf_c.loc[nyc_mask, "year_built"]
    n_diff_raw = int((yb_a.to_numpy() != yb_c.to_numpy()).sum())
    print(f"\nraw year_built value differs on {n_diff_raw}/{n_nyc} nyc_centre rows (Phase-A vs Phase-C/{WINNING_METHOD})")

    prov_c = gdf_c.loc[nyc_mask, "provenance_year_built"]
    orig_missing_mask = pooled.loc[nyc_mask, "year_built"].isna().to_numpy()
    ml_fired = int(prov_c[orig_missing_mask].astype(str).str.startswith("ML_").sum())
    print(f"ML tier fired on {ml_fired}/{n_nyc_missing} of nyc_centre's originally-missing year_built rows "
          f"(rest filled by spatial donor or statistical fallback)")
    print("provenance_year_built distribution on originally-missing nyc_centre rows (Phase-C):")
    print(prov_c[orig_missing_mask].value_counts())

    # The formally load-bearing check: vintage BIN identity (production
    # resolve_vintage, reused verbatim -- both frames have zero remaining NaN
    # so resolve_vintage's own donor logic is a provable no-op / early-return).
    vintage_a, nan_rows_a, _ = resolve_vintage(gdf_a)
    vintage_c, nan_rows_c, _ = resolve_vintage(gdf_c)
    assert len(nan_rows_a) == 0 and len(nan_rows_c) == 0, "resolve_vintage saw residual NaN -- early-return path assumption violated"

    vb_a = vintage_a.loc[nyc_mask.nonzero()[0]] if not hasattr(vintage_a, "loc") else vintage_a[nyc_mask]
    vb_c = vintage_c[nyc_mask]
    n_diff_bin = int((np.asarray(vb_a) != np.asarray(vb_c)).sum())
    print(f"\nvintage_standard BIN differs on {n_diff_bin}/{n_nyc} nyc_centre rows (Phase-A vs Phase-C/{WINNING_METHOD})")

    if n_diff_bin > 0:
        diverge_idx = np.where(np.asarray(vb_a) != np.asarray(vb_c))[0]
        print("Diverging rows (index within nyc_centre slice, year_built A/C, bin A/C):")
        nyc_positions = np.where(nyc_mask)[0]
        for pos in diverge_idx[:20]:
            gi = nyc_positions[pos]
            print(f"  row {gi}: yb_A={gdf_a['year_built'].iat[gi]:.1f} yb_C={gdf_c['year_built'].iat[gi]:.1f} "
                  f"bin_A={vintage_a.iat[gi]} bin_C={vintage_c.iat[gi]}")

    print("\n" + "=" * 70)
    if n_diff_bin == 0:
        print("RESULT: zero vintage-bin divergence on the gate cell -- EUI delta is")
        print("provably 0 by construction (VINTAGE_U_FACTORS is a deterministic")
        print("function of the bin; HVAC/DHW/cooking/refrigeration do not depend on")
        print("vintage). NO CLUSTER ESCALATION NEEDED.")
    else:
        print(f"RESULT: {n_diff_bin} row(s) diverge at the vintage-BIN level -- material")
        print("divergence per the plan's escalation trigger. Cluster A/B escalation")
        print("would be required (NOT executed by this script).")
    print("=" * 70)


if __name__ == "__main__":
    main()
