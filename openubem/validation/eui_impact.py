"""T09 -- Mandatory downstream-EUI impact check (Input-Imputation arc, M09 Step C).

Report, do NOT tune (M09 §4 / zero-fitted-params, PLAN §2 rule 4): every
number this module produces is a reporting artefact for the user/manager.
**Read-only on the imputer.** This module never imports
`openubem.semantic.imputation` and never receives an `ImputeConfig` -- the
EUI error it reports is NEVER fed back into any `impute_missing`/
`ImputeConfig` setting, threshold, or bound. This is a validation utility,
not a pipeline stage.

Protocol (M09 Step C): for a complete-case validation set, run Stage-3->4
**twice** -- Simulation A on OBSERVED inputs (the measured/reference series)
vs Simulation B on IMPUTED inputs (the predicted series) -- on the identical
building set, then compare annual EUI (+ peak load) pairwise per building:
  - MBE / NMBE  -- target |NMBE| < 5% at neighbourhood scale.
  - CV(RMSE)    -- target < 15% per-building.
  - peak-load deviation.
Input-reconstruction accuracy alone (T08 mask-and-recover) is NOT sufficient
validation -- an imputer with low input-RMSE that shifts city EUI 15% is a
failure this module exists to catch.

Existing-convention check (done before writing anything fresh, per plan):
`openubem/results/__init__.py::compute_validation_gates` already defines a
NMBE/CV(RMSE) pair, but for a DIFFERENT comparison structure -- an UNPAIRED
simulated-fleet-distribution vs an external CBECS survey, matched by weighted
quantiles (`_weighted_quantiles`/`_weighted_mean`), because CBECS has no
building-for-building correspondence to this project's fleet. T09 compares
Simulation A and Simulation B on the SAME buildings (same osm_id, same
order), so a genuine PAIRED per-building difference is available and is the
correct (stronger, less noisy) computation -- reusing the quantile-matching
machinery would throw that pairing away. This module therefore REUSES the
existing convention's *form* (RMSE, normalized by the reference/measured
mean, x100 -- i.e. ASHRAE Guideline 14 style) but implements fresh paired-data
functions, per the plan's "implement fresh if none exist, and say so" rule.
The T09 thresholds (5% / 15%) are also distinct from and MUST NOT be confused
with the CBECS-gate thresholds in `openubem/results/__init__.py`
(`_NMBE_THRESHOLD = 10.0`, `_CV_RMSE_THRESHOLD = 30.0`) -- different gate,
different targets (M09 Step C vs DESIGN §5.1 CBECS gate).

CARRY-FORWARD (from CP-1, §5G R4): the Tier-B instrumentation deliberately
diverges from the `e063865` idiom in exactly two ways -- a stored literal `0`
is KEPT (not promoted to the default) and a `NaN` no longer leaks through
truthiness. Both are correct behaviour. If this harness is ever run on a
dataset whose COP/area fields carry 0/NaN, Simulation-B deltas traceable to
those two paths are EXPECTED, not a Tier-B regression -- check the
`SUSPECT_ZERO_*` / `DEFAULT_*` provenance flags before diagnosing a delta.

SCAFFOLD NOTICE (T09 scope, this task): `compare_ab` below is structure
only. It is NOT called anywhere in this module, in its test file, or by any
other code in this task. The live Simulation-A/B run is a SINGLE later call
the manager authorizes explicitly (LIVE_SMOKE, PLAN §7 CP-2) -- no
EnergyPlus run happens as part of building or testing this file.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import numpy as np

__all__ = [
    "EUI_NMBE_THRESHOLD_PCT",
    "EUI_CVRMSE_THRESHOLD_PCT",
    "mbe",
    "nmbe",
    "cv_rmse",
    "peak_load_deviation",
    "eui_impact_report",
    "compare_ab",
]

# M09 Step C targets (distinct from the CBECS-gate thresholds in
# openubem/results/__init__.py -- see module docstring).
EUI_NMBE_THRESHOLD_PCT = 5.0
EUI_CVRMSE_THRESHOLD_PCT = 15.0


# ── comparator math (pure, paired-by-building) ───────────────────────────────
# Convention: `observed` = measured/reference = Simulation A (observed
# inputs); `predicted` = Simulation B (imputed inputs). Arrays MUST already
# be paired (same building, same order) by the caller.

def mbe(observed, predicted) -> float:
    """Mean Bias Error, predicted (B) minus observed (A), same units as input."""
    observed = np.asarray(observed, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return float(np.mean(predicted - observed))


def nmbe(observed, predicted) -> float:
    """Normalized MBE (%), ASHRAE G14 style: mean(pred-obs)/mean(obs) * 100."""
    observed = np.asarray(observed, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return float(mbe(observed, predicted) / np.mean(observed) * 100.0)


def cv_rmse(observed, predicted) -> float:
    """CV(RMSE) (%), ASHRAE G14 style: sqrt(mean((pred-obs)**2))/mean(obs) * 100."""
    observed = np.asarray(observed, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    rmse = float(np.sqrt(np.mean((predicted - observed) ** 2)))
    return float(rmse / np.mean(observed) * 100.0)


def peak_load_deviation(peak_observed, peak_imputed) -> dict[str, Any]:
    """Per-building peak-demand deviation, imputed (B) vs observed (A).

    The aggregate figures reuse `mbe`/`nmbe`/`cv_rmse` (same ASHRAE-G14-style
    convention as annual EUI) so they are directly comparable across the two
    metrics; `peak_max_abs_pct_deviation` additionally reports the single
    worst-case building, since HVAC-sizing risk lives in the tail, not the
    mean.
    """
    peak_observed = np.asarray(peak_observed, dtype=float)
    peak_imputed = np.asarray(peak_imputed, dtype=float)
    per_building_pct = (peak_imputed - peak_observed) / peak_observed * 100.0
    return {
        "n": int(len(peak_observed)),
        "peak_mbe": mbe(peak_observed, peak_imputed),
        "peak_nmbe_pct": nmbe(peak_observed, peak_imputed),
        "peak_cv_rmse_pct": cv_rmse(peak_observed, peak_imputed),
        "peak_max_abs_pct_deviation": float(np.max(np.abs(per_building_pct))),
        "per_building_pct_deviation": per_building_pct,
    }


def eui_impact_report(
    eui_observed,
    eui_imputed,
    peak_observed=None,
    peak_imputed=None,
) -> dict[str, Any]:
    """Full T09 comparator on paired per-building annual EUI (+ optional peak).

    `eui_observed`/`eui_imputed` MUST be paired by building (same osm_id,
    same order) -- Simulation A (observed inputs) vs Simulation B (imputed
    inputs) on the identical building set (M09 Step C). Report-only: nothing
    returned here is ever consumed by an imputer.
    """
    eui_observed = np.asarray(eui_observed, dtype=float)
    eui_imputed = np.asarray(eui_imputed, dtype=float)
    if eui_observed.shape != eui_imputed.shape:
        raise ValueError(
            "eui_impact_report: observed/imputed arrays must be paired "
            f"(same shape); got {eui_observed.shape} vs {eui_imputed.shape}"
        )

    eui_nmbe_pct = nmbe(eui_observed, eui_imputed)
    eui_cvrmse_pct = cv_rmse(eui_observed, eui_imputed)

    report: dict[str, Any] = {
        "n_buildings": int(len(eui_observed)),
        "eui_mbe": mbe(eui_observed, eui_imputed),
        "eui_nmbe_pct": eui_nmbe_pct,
        "eui_nmbe_pass": abs(eui_nmbe_pct) < EUI_NMBE_THRESHOLD_PCT,
        "eui_cv_rmse_pct": eui_cvrmse_pct,
        "eui_cv_rmse_pass": eui_cvrmse_pct < EUI_CVRMSE_THRESHOLD_PCT,
        "peak": None,
    }
    if peak_observed is not None and peak_imputed is not None:
        report["peak"] = peak_load_deviation(peak_observed, peak_imputed)
    return report


# ── A/B harness scaffold (structure only -- NOT executed by this task) ───────

def compare_ab(
    gdf_observed,
    gdf_imputed,
    schedule_library: dict,
    out_dir: "Path | str",
    *,
    resolution_mode: str = "auto",
    n_jobs: int = 1,
    simulate_fn: "Callable | None" = None,
    make_figures: bool = False,
) -> dict[str, Any]:
    """SCAFFOLD -- Simulation-A-vs-B downstream-EUI check (M09 Step C, T09).

    Wraps the EXISTING Stage-3->5 harness -- does NOT reimplement simulation
    or parsing:
      Stage 3 -- `openubem.idf.builder.run_step3`            (IDF generation)
      Stage 4 -- `simulate_fn` (default `openubem.simulation.run_neighbourhood`,
                  injectable so a cluster-side runner can be substituted later
                  without editing this module -- CLAUDE.md forbids compute on
                  the Speed login node; a future cluster `simulate_fn` would
                  itself have to go through `sbatch`)
      Stage 5 -- `openubem.results.aggregate_results`         (EUI parse)
    run ONCE on `gdf_observed` (Simulation A) and ONCE on `gdf_imputed`
    (Simulation B), into `out_dir/simA` and `out_dir/simB` respectively. The
    two `total_eui_kwh_m2` series are paired by `osm_id` (inner join --
    buildings that failed in either run are dropped and counted, not
    silently misaligned) and handed to `eui_impact_report`.

    READ-ONLY ON THE IMPUTER (zero-fitted-params, PLAN §2 rule 4): this
    function never imports `openubem.semantic.imputation` and never receives
    an `ImputeConfig`. `gdf_imputed` is an already-materialized frame the
    CALLER produced upstream (e.g. via `impute_missing`, elsewhere); the
    numbers this function returns are a REPORTING artefact only and are NEVER
    fed back into any imputer setting/threshold/bound.

    NOT CALLED ANYWHERE in this task (comparator-math + scaffold only, PLAN
    §6 T09). The live A/B run is a SINGLE later call the manager authorizes
    explicitly as LIVE_SMOKE (PLAN §7 CP-2) -- calling this launches
    EnergyPlus via `simulate_fn` and must never happen from a test or from
    default-path code before that authorization.

    Peak-load wiring: as of this task, `aggregate_results`/`parse_building`
    (`openubem/results/parser.py`) expose only annual end-use EUI columns --
    no peak-demand column exists yet. This scaffold therefore calls
    `eui_impact_report` with `peak_observed=None, peak_imputed=None` until a
    peak column lands; `peak_load_deviation` itself is fully implemented and
    unit-tested on hand-built arrays so it is ready the moment that column
    exists (wiring it in is not a math change, just adding the column name
    below).
    """
    from openubem.idf.builder import run_step3
    from openubem.results import aggregate_results

    if simulate_fn is None:
        from openubem.simulation import run_neighbourhood as simulate_fn

    out_dir = Path(out_dir)
    sim_a_dir = out_dir / "simA"
    sim_b_dir = out_dir / "simB"

    idf_manifest_a = run_step3(
        gdf_observed, schedule_library, sim_a_dir / "step3",
        n_jobs=n_jobs, resolution_mode=resolution_mode,
    )
    idf_manifest_b = run_step3(
        gdf_imputed, schedule_library, sim_b_dir / "step3",
        n_jobs=n_jobs, resolution_mode=resolution_mode,
    )

    sim_manifest_a = simulate_fn(idf_manifest_a, gdf_observed, sim_a_dir / "step4", n_jobs=n_jobs)
    sim_manifest_b = simulate_fn(idf_manifest_b, gdf_imputed, sim_b_dir / "step4", n_jobs=n_jobs)

    results_a = aggregate_results(
        sim_manifest_a, idf_manifest_a, gdf_observed, sim_a_dir / "step5", make_figures=make_figures,
    )
    results_b = aggregate_results(
        sim_manifest_b, idf_manifest_b, gdf_imputed, sim_b_dir / "step5", make_figures=make_figures,
    )

    eui_col = "total_eui_kwh_m2"
    a = results_a[["osm_id", eui_col]].dropna(subset=[eui_col]).rename(columns={eui_col: "eui_a"})
    b = results_b[["osm_id", eui_col]].dropna(subset=[eui_col]).rename(columns={eui_col: "eui_b"})
    paired = a.merge(b, on="osm_id", how="inner")

    report = eui_impact_report(paired["eui_a"].to_numpy(), paired["eui_b"].to_numpy())

    return {
        "osm_ids": paired["osm_id"].tolist(),
        "eui_observed": paired["eui_a"].to_numpy(),
        "eui_imputed": paired["eui_b"].to_numpy(),
        "n_dropped_a": int(len(results_a) - len(a)),
        "n_dropped_b": int(len(results_b) - len(b)),
        "report": report,
    }
