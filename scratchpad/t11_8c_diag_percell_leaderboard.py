"""T11.8c-diag -- per-cell (PRODUCTION-granularity) mask-and-recover
attribute-recovery leaderboard: Phase-A vs raw-knn (NO de-bias) on
`year_built`, for a cell that clears knn's >=200 complete-case floor on its
OWN observed count (la_suburban=1295, la_urban=542 -- pooled CP-3 inventory,
PLAN_phaseC_ml_imputer.md Sec1).

Adapted (not rewritten) from t11_cp3_leaderboard.py's run_one/
exact_bin_recovery, reused VERBATIM (imported, not reimplemented). The only
change from the original T11.6/T11.8 drivers: subset the pooled frame to
ONE cell BEFORE calling run_one, instead of running mask_and_recover on the
full pooled 12-cell frame. This reproduces production granularity: knn (if
it fires at all) fits complete cases from that ONE cell only.

Report-only, NO cluster, no EUI feedback into any config/imputer setting
(zero-fitted-params). IMPUTE_DEBIAS_NEWERSKEW left at its shipped all-False
default throughout -- this diagnostic tests RAW knn only, not any
corrector. Throwaway scratchpad driver -- NEVER under docs/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from t11_cp3_leaderboard import exact_bin_recovery, load_pooled, run_one  # noqa: E402

from openubem import config
from openubem.semantic.imputation import ImputeConfig

SEED = 42
CELLS = ["la_suburban", "la_urban"]
TARGET = "year_built"


def main():
    pooled = load_pooled()
    assert all(v is False for v in config.IMPUTE_DEBIAS_NEWERSKEW.values()), (
        "IMPUTE_DEBIAS_NEWERSKEW must stay at its shipped all-False default for this diagnostic"
    )

    results = {}

    for cell in CELLS:
        print(f"\n{'='*70}\nCELL: {cell} (production granularity, target={TARGET})\n{'='*70}")
        cell_gdf = pooled[pooled["city"] == cell].copy()
        n_obs = int(cell_gdf[TARGET].notna().sum())
        floor = config.IMPUTE_ML_FLOORS["knn"]
        print(f"n_total={len(cell_gdf)}, observed {TARGET}={n_obs}, knn floor={floor}, cleared={n_obs >= floor}")

        cfg_a = ImputeConfig(enabled_tiers=("spatial", "statistical"))
        base = run_one(cell_gdf, TARGET, cfg_a, seed=SEED)
        m0 = base["metrics"]
        base_hits, base_n = exact_bin_recovery(base["y_true"], base["y_pred"])
        print(f"[Phase-A]         mae={m0['mae']:.3f} rmse={m0['rmse']:.3f} "
              f"ks={m0['ks_stat']:.4f} wass={m0['wasserstein']:.3f} n_holdout={base['n_holdout']} "
              f"exact_bin={base_hits}/{base_n}")
        print(f"    prov_counts: {base['prov_counts']}")

        orig_method = dict(config.IMPUTE_ML_METHOD_BY_TARGET)
        cell_results = {
            "n_total": int(len(cell_gdf)), "n_observed": n_obs, "knn_floor": floor,
            "floor_cleared": bool(n_obs >= floor),
            "phase_a": {"metrics": m0, "exact_bin_hits": base_hits, "exact_bin_n": base_n,
                        "n_holdout": base["n_holdout"], "prov_counts": base["prov_counts"]},
        }
        try:
            config.IMPUTE_ML_METHOD_BY_TARGET[TARGET] = "knn"
            cfg_raw = ImputeConfig(enabled_tiers=("spatial", "ml", "statistical"))
            raw = run_one(cell_gdf, TARGET, cfg_raw, seed=SEED)
            mr_ = raw["metrics"]
            hits_r, n_r = exact_bin_recovery(raw["y_true"], raw["y_pred"])
            ml_fired_raw = sum(v for k, v in raw["prov_counts"].items() if k.startswith("ML_"))
            print(f"[Phase-C knn RAW] mae={mr_['mae']:.3f} rmse={mr_['rmse']:.3f} "
                  f"ks={mr_['ks_stat']:.4f} wass={mr_['wasserstein']:.3f} "
                  f"ml_fired={ml_fired_raw}/{raw['n_holdout']} exact_bin={hits_r}/{n_r}")
            print(f"    prov_counts: {raw['prov_counts']}")

            cell_results["phase_c_knn_raw"] = {
                "metrics": mr_, "exact_bin_hits": hits_r, "exact_bin_n": n_r,
                "prov_counts": raw["prov_counts"], "ml_fired": ml_fired_raw,
                "n_holdout": raw["n_holdout"],
            }

            verdict_mae = ">= Phase-A (better-or-equal)" if mr_["mae"] <= m0["mae"] else "REGRESSES vs Phase-A"
            verdict_bin = ">= Phase-A (better-or-equal)" if hits_r >= base_hits else "REGRESSES vs Phase-A"
            print(f"    MAE raw-knn {mr_['mae']:.3f} vs Phase-A {m0['mae']:.3f} -> {verdict_mae}")
            print(f"    exact_bin raw-knn {hits_r}/{n_r} vs Phase-A {base_hits}/{base_n} -> {verdict_bin}")
        finally:
            config.IMPUTE_ML_METHOD_BY_TARGET.clear()
            config.IMPUTE_ML_METHOD_BY_TARGET.update(orig_method)

        results[cell] = cell_results

    out_path = Path(__file__).parent / "t11_8c_diag_percell_leaderboard_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
