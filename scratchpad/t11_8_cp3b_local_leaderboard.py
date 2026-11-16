"""T11.8 CP-3b-local -- pooled mask-and-recover leaderboard: de-biased-knn
vs raw-knn vs Phase-A baseline on year_built/levels (seed 42, T08 default
holdout). Reuses t11_cp3_leaderboard.py's load_pooled/run_one/
exact_bin_recovery machinery VERBATIM (not reimplemented).

Report-only, NO cluster, no EUI feedback into any config/imputer setting
(zero-fitted-params). Throwaway scratchpad driver -- NEVER under docs/.
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
TARGETS = ("year_built", "levels")


def main():
    pooled = load_pooled()
    print(f"pooled n={len(pooled)}")
    print(f"use_class in columns: {'use_class' in pooled.columns}")
    print(f"archetype_id in columns: {'archetype_id' in pooled.columns}")

    results = {}

    for target in TARGETS:
        print(f"\n{'='*70}\nTARGET: {target}\n{'='*70}")

        cfg_a = ImputeConfig(enabled_tiers=("spatial", "statistical"))
        base = run_one(pooled, target, cfg_a, seed=SEED)
        m0 = base["metrics"]
        base_hits, base_n = (None, None)
        if target == "year_built":
            base_hits, base_n = exact_bin_recovery(base["y_true"], base["y_pred"])
        print(f"[Phase-A]              mae={m0['mae']:.3f} rmse={m0['rmse']:.3f} "
              f"ks={m0['ks_stat']:.4f} wass={m0['wasserstein']:.3f} n_holdout={base['n_holdout']}"
              + (f" exact_bin={base_hits}/{base_n}" if target == "year_built" else ""))

        orig_method = dict(config.IMPUTE_ML_METHOD_BY_TARGET)
        orig_debias = dict(config.IMPUTE_DEBIAS_NEWERSKEW)
        target_results = {
            "phase_a": {"metrics": m0, "exact_bin_hits": base_hits, "exact_bin_n": base_n,
                        "n_holdout": base["n_holdout"]},
        }
        try:
            config.IMPUTE_ML_METHOD_BY_TARGET[target] = "knn"

            # raw knn (debias flag OFF -- the CP-3-shipped/failed config)
            config.IMPUTE_DEBIAS_NEWERSKEW[target] = False
            cfg_raw = ImputeConfig(enabled_tiers=("spatial", "ml", "statistical"))
            raw = run_one(pooled, target, cfg_raw, seed=SEED)
            mr_ = raw["metrics"]
            hits_r, n_r = (None, None)
            if target == "year_built":
                hits_r, n_r = exact_bin_recovery(raw["y_true"], raw["y_pred"])
            ml_fired_raw = sum(v for k, v in raw["prov_counts"].items() if k.startswith("ML_"))
            print(f"[Phase-C knn RAW]      mae={mr_['mae']:.3f} rmse={mr_['rmse']:.3f} "
                  f"ks={mr_['ks_stat']:.4f} wass={mr_['wasserstein']:.3f} ml_fired={ml_fired_raw}/{raw['n_holdout']}"
                  + (f" exact_bin={hits_r}/{n_r}" if target == "year_built" else ""))
            print(f"    prov_counts: {raw['prov_counts']}")

            # de-biased knn (T11.8 corrector, opt-in flag ON)
            config.IMPUTE_DEBIAS_NEWERSKEW[target] = True
            cfg_deb = ImputeConfig(enabled_tiers=("spatial", "ml", "statistical"))
            deb = run_one(pooled, target, cfg_deb, seed=SEED)
            md = deb["metrics"]
            hits_d, n_d = (None, None)
            if target == "year_built":
                hits_d, n_d = exact_bin_recovery(deb["y_true"], deb["y_pred"])
            ml_fired_deb = sum(v for k, v in deb["prov_counts"].items() if k.startswith("ML_"))
            print(f"[Phase-C knn DEBIASED] mae={md['mae']:.3f} rmse={md['rmse']:.3f} "
                  f"ks={md['ks_stat']:.4f} wass={md['wasserstein']:.3f} ml_fired={ml_fired_deb}/{deb['n_holdout']}"
                  + (f" exact_bin={hits_d}/{n_d}" if target == "year_built" else ""))
            print(f"    prov_counts: {deb['prov_counts']}")

            identical = (raw["y_pred"].to_numpy() == deb["y_pred"].to_numpy()).all()
            print(f"    RAW == DEBIASED predictions identical on every holdout row: {identical}")

            target_results["phase_c_knn_raw"] = {
                "metrics": mr_, "exact_bin_hits": hits_r, "exact_bin_n": n_r,
                "prov_counts": raw["prov_counts"], "ml_fired": ml_fired_raw,
            }
            target_results["phase_c_knn_debiased"] = {
                "metrics": md, "exact_bin_hits": hits_d, "exact_bin_n": n_d,
                "prov_counts": deb["prov_counts"], "ml_fired": ml_fired_deb,
            }
            target_results["raw_vs_debiased_predictions_identical"] = bool(identical)
        finally:
            config.IMPUTE_ML_METHOD_BY_TARGET.clear()
            config.IMPUTE_ML_METHOD_BY_TARGET.update(orig_method)
            config.IMPUTE_DEBIAS_NEWERSKEW.clear()
            config.IMPUTE_DEBIAS_NEWERSKEW.update(orig_debias)

        results[target] = target_results

    out_path = Path(__file__).parent / "t11_8_cp3b_local_leaderboard_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
