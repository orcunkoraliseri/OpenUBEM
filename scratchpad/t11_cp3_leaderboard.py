"""T11.6 CP-3 headline -- pooled real-city attribute-recovery leaderboard.

Report-only (PLAN_phaseC_ml_imputer.md T11.6): builds a pooled real-city
complete-case frame from the committed phaseE 01_buildings.gpkg (12 cells),
runs `mask_and_recover` (T08 harness, REUSED not reimplemented) for Phase-A
(`spatial,statistical`) vs Phase-C (`spatial,ml,statistical`) per ML method,
same seed(42)/n_grid/holdout_frac (T08 defaults). NOTHING here is fed back
into any `ImputeConfig`/imputer setting (zero-fitted-params).

Throwaway scratchpad driver -- NEVER under docs/.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from openubem import config
from openubem.semantic.imputation import ImputeConfig, impute_missing, _ML_METHOD_NAMES
from openubem.semantic.construction_sets import _YEAR_BINS, _YEAR_LABELS
from openubem.validation import mask_recover as mr

REPO = Path(__file__).resolve().parents[1]
PHASEE_DIR = REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
COMMON_CRS = "EPSG:5070"  # NAD83 / Conus Albers -- meters, avoids cross-UTM-zone KNN corruption
SEED = 42
TARGETS = ("year_built", "levels")  # use_class NOT in 01_buildings.gpkg schema (Stage-1, pre-classification) -- skipped, noted


def load_pooled() -> gpd.GeoDataFrame:
    frames = []
    for cell in CELLS:
        g = gpd.read_file(PHASEE_DIR / cell / "01_buildings.gpkg")
        g = g.to_crs(COMMON_CRS)
        g["city"] = cell
        frames.append(g)
    pooled = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), geometry="geometry", crs=COMMON_CRS)
    centroids = pooled.geometry.centroid
    pooled["centroid_x"] = centroids.x
    pooled["centroid_y"] = centroids.y
    return pooled


def vintage_bin(series: pd.Series) -> pd.Series:
    """Reuse the production vintage-bin scheme (construction_sets._YEAR_BINS/
    _YEAR_LABELS) -- NOT a new scheme invented for this evaluation."""
    numeric = pd.to_numeric(series, errors="coerce")
    out = pd.Series(pd.NA, index=series.index, dtype=object)
    valid = numeric.notna()
    if valid.any():
        out.loc[valid] = pd.cut(
            numeric.loc[valid].astype(float),
            bins=[-np.inf] + _YEAR_BINS + [np.inf],
            labels=_YEAR_LABELS,
            right=False,
            ordered=False,
        ).astype(str)
    return out


def run_one(pooled, target, cfg, seed=SEED):
    """Mirrors `mask_and_recover`'s exact internal call sequence (same public
    functions, same order) so results are numerically identical to calling
    `mask_and_recover` directly -- but also returns the raw filled/truth
    series + provenance tokens for the exact-bin count and tier-diagnostics
    this leaderboard needs beyond mask_and_recover's aggregate dict."""
    rng = np.random.default_rng(seed)
    cc = mr.complete_cases(pooled, [target])
    train_idx, holdout_idx, blocks = mr.spatial_block_holdout(
        cc, block_col=None, n_grid=mr.DEFAULT_N_GRID, holdout_frac=mr.DEFAULT_HOLDOUT_FRAC, rng=rng,
    )
    masked, truth = mr.mask_targets(cc, holdout_idx, [target])
    filled = impute_missing(masked, cfg=cfg, targets=[target], rng=rng)
    y_true = truth.loc[holdout_idx, target]
    y_pred = filled.loc[holdout_idx, target]
    metrics = mr.score_continuous(y_true, y_pred)
    prov = filled.loc[holdout_idx, f"provenance_{target}"]
    return {
        "metrics": metrics,
        "prov_counts": prov.fillna("<UNFILLED>").value_counts().to_dict(),
        "n_complete_cases": int(len(cc)),
        "n_holdout": int(len(holdout_idx)),
        "y_true": y_true,
        "y_pred": y_pred,
    }


def exact_bin_recovery(y_true, y_pred):
    tb = vintage_bin(y_true)
    pb = vintage_bin(y_pred)
    both = tb.notna() & pb.notna()
    n = int(both.sum())
    hits = int((tb[both] == pb[both]).sum())
    return hits, n


def main():
    pooled = load_pooled()
    print(f"pooled n={len(pooled)}")
    for t in TARGETS:
        n_obs = pooled[t].notna().sum()
        print(f"  {t}: observed N (raw, pre-holdout) = {n_obs}")

    results = {}

    for target in TARGETS:
        print(f"\n{'='*70}\nTARGET: {target}\n{'='*70}")
        cfg_a = ImputeConfig(enabled_tiers=("spatial", "statistical"))
        base = run_one(pooled, target, cfg_a, seed=SEED)
        base_metrics = base["metrics"]
        print(f"[Phase-A baseline] n_cc={base['n_complete_cases']} n_holdout={base['n_holdout']} "
              f"mae={base_metrics['mae']:.3f} rmse={base_metrics['rmse']:.3f} "
              f"ks={base_metrics['ks_stat']:.4f} wass={base_metrics['wasserstein']:.3f}")
        print(f"  prov_counts: {base['prov_counts']}")

        cross_check = mr.mask_and_recover(
            pooled, continuous_targets=(target,), block_col=None,
            n_grid=mr.DEFAULT_N_GRID, holdout_frac=mr.DEFAULT_HOLDOUT_FRAC,
            cfg=cfg_a, rng=np.random.default_rng(SEED),
        )
        direct_metrics = cross_check["continuous"][target]
        assert direct_metrics == base_metrics, (
            f"wrapper/mask_and_recover mismatch for {target}: {direct_metrics} vs {base_metrics}"
        )
        print("  [cross-check] run_one() metrics == mask_and_recover() direct call: MATCH")

        base_hits, base_n = (None, None)
        if target == "year_built":
            base_hits, base_n = exact_bin_recovery(base["y_true"], base["y_pred"])
            print(f"  exact-vintage-bin recovery: {base_hits}/{base_n}")

        target_results = {
            "phase_a": {
                "metrics": base_metrics, "prov_counts": base["prov_counts"],
                "exact_bin_hits": base_hits, "exact_bin_n": base_n,
                "n_complete_cases": base["n_complete_cases"], "n_holdout": base["n_holdout"],
            },
            "phase_c": {},
        }

        orig_method = dict(config.IMPUTE_ML_METHOD_BY_TARGET)
        try:
            for method in _ML_METHOD_NAMES:
                config.IMPUTE_ML_METHOD_BY_TARGET[target] = method
                cfg_c = ImputeConfig(enabled_tiers=("spatial", "ml", "statistical"))
                run = run_one(pooled, target, cfg_c, seed=SEED)
                m = run["metrics"]
                hits, n = (None, None)
                if target == "year_built":
                    hits, n = exact_bin_recovery(run["y_true"], run["y_pred"])
                ml_fired = sum(v for k, v in run["prov_counts"].items() if k.startswith("ML_"))
                print(f"[Phase-C {method:10s}] mae={m['mae']:.3f} rmse={m['rmse']:.3f} "
                      f"ks={m['ks_stat']:.4f} wass={m['wasserstein']:.3f} "
                      f"d_mae={m['mae']-base_metrics['mae']:+.3f} d_rmse={m['rmse']-base_metrics['rmse']:+.3f} "
                      f"ml_fired={ml_fired}/{run['n_holdout']} "
                      + (f"exact_bin={hits}/{n}" if target == "year_built" else ""))
                print(f"    prov_counts: {run['prov_counts']}")
                target_results["phase_c"][method] = {
                    "metrics": m, "prov_counts": run["prov_counts"],
                    "exact_bin_hits": hits, "exact_bin_n": n,
                    "ml_fired": ml_fired, "n_holdout": run["n_holdout"],
                }
        finally:
            config.IMPUTE_ML_METHOD_BY_TARGET.clear()
            config.IMPUTE_ML_METHOD_BY_TARGET.update(orig_method)

        results[target] = target_results

    out_path = Path(__file__).parent / "t11_cp3_leaderboard_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
