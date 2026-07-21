"""T10 -- CP-DRAW pooled + per-cell leaderboard (Input-Imputation arc, Part II).

See docs/docs_ACTIVE/input/imputation/implementation/IMPLEMENTATION_phaseC_
ml_imputer.md Part II §II.6 T10. Runs the M09 mask-and-recover harness
(`openubem.validation.mask_recover`, REUSED verbatim, not reimplemented) for
each of the six `draw` methods (`kde`, `pmm`, `hotdeck`, `resid`, `abb`
continuous + `catfreq` categorical) against the production group-median/mode
`statistical`-tier baseline, both POOLED (all 12 committed cells, EPSG:5070,
mirrors RESULTS_phaseC.md's protocol) and PER-CELL (production granularity).

    ****************************************************************
    PLAIN-READING RULE (state this before reading any table below):
    a good `draw` method is EXPECTED to LOSE on MAE and WIN on
    variance-ratio / IQR-ratio / Wasserstein / energy-distance versus
    the group-median baseline. That trade is the INTENDED result, not
    a regression -- the group median is optimal for point-error (MAE)
    by construction (it IS the conditional-mean estimator) and is
    exactly what collapses the variance (Part I of this same document).
    A draw method "wins" this leaderboard by moving variance-ratio/
    IQR-ratio toward 1.0 and Wasserstein/energy-distance down toward
    their bootstrap noise floor, while its MAE stays within the
    do-no-harm band (<=1.25x baseline MAE). Read the do-no-harm MAE
    column as a GUARDRAIL, never as the scoring criterion.
    ****************************************************************

Hard rules honoured here (Part II §II.1, non-negotiable):
  - Report-only / opt-in-OFF invariant: `config.IMPUTE_ENABLED_TIERS` is
    NEVER imported for write, NEVER touched. `config.IMPUTE_DRAW_METHOD_
    BY_TARGET` is mutated ONLY inside a try/finally around one call, restored
    immediately after (mirrors `scratchpad/t11_cp3_leaderboard.py::main`'s
    `IMPUTE_ML_METHOD_BY_TARGET` save/restore and `impute_scatter.py::
    _pooled_ml_pairs`). Nothing here can change `openubem/config.py` on disk.
  - Zero-fitted-parameters: every draw call uses the library/plan-fixed
    defaults already frozen in `draw_methods.py` (Scott's-rule KDE,
    `DEFAULT_K=10`, empirical residuals, ABB two-stage bootstrap) -- no knob
    is read from or tuned against any metric computed here.
  - Zero EnergyPlus / cluster / login-node / network: pandas/numpy/geopandas/
    scipy on the 12 committed `01_buildings.gpkg` cells only. No EUI column
    is read anywhere in this module (report-only, mirrors `mask_recover.py`).
  - Per-target evaluation calls use a FRESH `np.random.default_rng(RANDOM_
    SEED)` EVERY call (never a shared/reused rng across methods or targets)
    and set `config.IMPUTE_DRAW_METHOD_BY_TARGET[target]` EXPLICITLY before
    each draw-tier call -- the D04 debug doc (`docs/docs_ACTIVE/input/
    imputation/debugs/PLAN_phaseC_knn_repro_investigation.md`) diagnosed the
    exact caller mistakes ("shared rng", "default method not overridden",
    "targets pooled into one call") that silently produce a wrong number
    while looking like a real regression; this driver mirrors the CORRECT
    invocation pattern verified there and in `impute_scatter.py::
    _pooled_ml_pairs`/`_pooled_phase_a_pairs` byte-for-byte.
  - The baseline leg (`spatial` -> `statistical`, no `draw`) is asserted to
    reproduce the committed Phase-A pooled leaderboard (`RESULTS_phaseC.md`
    §5-C / `PLAN_phaseC_ml_imputer.md` T11.6): `year_built` MAE 26.43,
    `levels` MAE 9.18. If this drifts, the invocation is wrong -- this driver
    STOPS loudly (`AssertionError`) rather than ship a wrong leaderboard
    (mirrors `impute_scatter.py::_assert_cross_check`'s "honesty guard").

Figures -> `openubem/outputs/` (flat), per the project figure rule. A JSON
companion (`draw_leaderboard_results.json`) is written alongside the figures
so every number in the CP-DRAW progress-log table has a machine-readable
source.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from openubem import config
from openubem.config import RANDOM_SEED
from openubem.results.impute_figures import PALETTE, _save, _style
from openubem.semantic import draw_methods as dm
from openubem.semantic.imputation import ImputeConfig
from openubem.validation import mask_recover as mr
from openubem.validation.eui_impact import nmbe

REPO = Path(__file__).resolve().parents[2]
PHASEE_DIR = REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
OUTPUTS_DIR = REPO / "openubem" / "outputs"

# Cell pooling order -- MUST match `scratchpad/t11_cp3_leaderboard.py::CELLS`
# / `impute_scatter.py::POOLED_CELL_ORDER` exactly: `spatial_block_holdout`'s
# `rng.shuffle(blocks.value_counts().index)` ties break on first-occurrence
# row order, so a different concatenation order silently produces a
# DIFFERENT holdout split under the same seed (the actual T11 cross-check
# root cause the D04 debug doc documents).
POOLED_CELL_ORDER: tuple[str, ...] = (
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
)
COMMON_CRS = "EPSG:5070"  # NAD83 / Conus Albers, meters -- avoids cross-UTM-zone corruption

CONTINUOUS_TARGETS: tuple[str, ...] = ("year_built", "levels", "height_m")
# `use_class` is NOT present at the Stage-1 `01_buildings.gpkg` schema level
# (confirmed directly, matches T09's LOCAL_SMOKE finding + the arc's earlier
# `knn` reframe finding, MEMORY "KEY FINDING -- REVISED 2026-07-14"). `T09`
# hit the identical gap and substituted `function_tag` -- a real, densely
# populated categorical column -- masking REAL values synthetically per the
# same mask-and-recover convention the harness already uses for any complete
# column. This driver follows that precedent verbatim.
CATEGORICAL_TARGET = "function_tag"

CONTINUOUS_METHODS: tuple[str, ...] = tuple(m for m in dm.DRAW_METHODS if m != "catfreq")
CATEGORICAL_METHOD = "catfreq"

# Cross-check gate (Part II §II.6 T10 "How"): the baseline leg MUST reproduce
# these two committed Phase-A numbers exactly, or the invocation is wrong.
BASELINE_MAE_CROSSCHECK = {"year_built": 26.43, "levels": 9.18}

# Data-adequacy floor for a PER-CELL continuous evaluation (NOT a tuned
# metric knob -- a floor on how much data must exist before a mask-recover
# comparison is meaningful at all; mirrors the spirit of `IMPUTE_ML_FLOORS`
# without borrowing its literal values). Below this, the cell/target
# combination is reported as `insufficient_data` rather than computing a
# metric on a handful of points.
PER_CELL_MIN_N = 30

# Part II §II.3 "Evaluation priority per target" -- a RANKING TO TEST, not a
# shipped default (II.3 table, last row). All methods are still run and
# reported for every target; this only annotates which method(s) are the
# ELIGIBLE PRIMARY candidate per target's discrete/continuous support.
PRIMARY_PRIORITY: dict[str, tuple[str, ...]] = {
    "year_built": ("hotdeck", "pmm", "resid"),
    "levels": ("pmm", "hotdeck"),  # integer-donor only; kde/resid disallowed as primary
    "height_m": ("resid", "kde"),
    CATEGORICAL_TARGET: ("catfreq",),
}

DO_NO_HARM_MULTIPLIER = 1.25


# ─────────────────────────────────────────────────────────────────────────
# Data loading (mirrors `impute_scatter.py::_load_pooled_cells` verbatim)
# ─────────────────────────────────────────────────────────────────────────

def _load_cell(cell: str) -> gpd.GeoDataFrame:
    return gpd.read_file(str(PHASEE_DIR / cell / "01_buildings.gpkg"))


def _load_pooled_cells(cells: tuple[str, ...] = POOLED_CELL_ORDER) -> gpd.GeoDataFrame:
    frames = [_load_cell(cell).to_crs(COMMON_CRS) for cell in cells]
    pooled = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), geometry="geometry", crs=COMMON_CRS)
    centroids = pooled.geometry.centroid
    pooled["centroid_x"] = centroids.x
    pooled["centroid_y"] = centroids.y
    return pooled


# ─────────────────────────────────────────────────────────────────────────
# Caller-correct harness invocation (D04 debug doc / impute_scatter.py
# `_pooled_ml_pairs` pattern, mirrored for the `draw` tier)
# ─────────────────────────────────────────────────────────────────────────

def _baseline_pairs(gdf: gpd.GeoDataFrame, target: str, categorical: bool = False) -> tuple[dict, dict]:
    """Phase-A leg: `spatial` -> `statistical`, `draw` never enabled."""
    cfg = ImputeConfig(enabled_tiers=("spatial", "statistical"))
    kwargs = {"categorical_targets": [target]} if categorical else {"continuous_targets": [target]}
    return mr.recover_pairs(gdf, cfg=cfg, rng=np.random.default_rng(RANDOM_SEED), **kwargs)


def _draw_pairs(gdf: gpd.GeoDataFrame, target: str, method: str, categorical: bool = False) -> tuple[dict, dict]:
    """`draw`-tier leg: `IMPUTE_DRAW_METHOD_BY_TARGET[target]` set EXPLICITLY
    before the call and restored in `finally` (never persisted -- rule 1).
    `per_input_tiers` (not the global `enabled_tiers`) is the opt-in surface,
    per the kickoff's hard rule 1, and inserts `draw` in its canonical
    position between `spatial` and `statistical` (Part II §II.3)."""
    orig = dict(config.IMPUTE_DRAW_METHOD_BY_TARGET)
    try:
        config.IMPUTE_DRAW_METHOD_BY_TARGET[target] = method
        cfg = ImputeConfig(per_input_tiers={target: ("spatial", "draw", "statistical")})
        kwargs = {"categorical_targets": [target]} if categorical else {"continuous_targets": [target]}
        return mr.recover_pairs(gdf, cfg=cfg, rng=np.random.default_rng(RANDOM_SEED), **kwargs)
    finally:
        config.IMPUTE_DRAW_METHOD_BY_TARGET.clear()
        config.IMPUTE_DRAW_METHOD_BY_TARGET.update(orig)


def _joint_draw_pairs(gdf: gpd.GeoDataFrame, targets: tuple[str, ...], method: str) -> tuple[dict, dict]:
    """Both `targets` drawn by the SAME method in ONE call (joint holdout,
    complete-case-on-BOTH) -- needed for the joint/multivariate energy-
    distance bonus check (V03 §II.5: energy distance's whole point is
    catching a covariance collapse a marginal metric misses)."""
    orig = dict(config.IMPUTE_DRAW_METHOD_BY_TARGET)
    try:
        for t in targets:
            config.IMPUTE_DRAW_METHOD_BY_TARGET[t] = method
        cfg = ImputeConfig(per_input_tiers={t: ("spatial", "draw", "statistical") for t in targets})
        return mr.recover_pairs(gdf, continuous_targets=list(targets), cfg=cfg, rng=np.random.default_rng(RANDOM_SEED))
    finally:
        config.IMPUTE_DRAW_METHOD_BY_TARGET.clear()
        config.IMPUTE_DRAW_METHOD_BY_TARGET.update(orig)


def _joint_baseline_pairs(gdf: gpd.GeoDataFrame, targets: tuple[str, ...]) -> tuple[dict, dict]:
    cfg = ImputeConfig(enabled_tiers=("spatial", "statistical"))
    return mr.recover_pairs(gdf, continuous_targets=list(targets), cfg=cfg, rng=np.random.default_rng(RANDOM_SEED))


# ─────────────────────────────────────────────────────────────────────────
# Metric assembly (T09b CP-DRAW metric set, reused verbatim from mask_recover.py)
# ─────────────────────────────────────────────────────────────────────────

def _continuous_row(true: np.ndarray, pred: np.ndarray, baseline_mae: float, eligible_primary: bool, priority_rank) -> dict:
    scores = mr.score_continuous(true, pred)
    var_ci = mr.variance_ratio_bootstrap_ci(true, pred, rng=np.random.default_rng(RANDOM_SEED))
    return {
        **scores,
        "variance_ratio": mr.variance_ratio(true, pred),
        "iqr_ratio": mr.iqr_ratio(true, pred),
        "energy_distance": mr.energy_distance(true, pred),
        "variance_ratio_ci90": list(var_ci),
        "nmbe_proxy_pct": nmbe(true, pred),
        "do_no_harm_mae_pass": bool(scores["mae"] <= DO_NO_HARM_MULTIPLIER * baseline_mae),
        "eligible_primary": eligible_primary,
        "priority_rank": priority_rank,
    }


def _categorical_row(true, pred, baseline_pfc: float, eligible_primary: bool, priority_rank) -> dict:
    cat = mr.score_categorical(true, pred)
    tv = mr.score_categorical_tv(true, pred)
    return {
        **cat,
        "tv": tv["tv"],
        "do_no_harm_pfc_pass": bool(cat["pfc"] <= DO_NO_HARM_MULTIPLIER * baseline_pfc),
        "eligible_primary": eligible_primary,
        "priority_rank": priority_rank,
    }


def _noise_floors(true_holdout: np.ndarray) -> dict:
    return {
        "wasserstein": mr.bootstrap_noise_floor(true_holdout, metric_fn=mr.wasserstein, rng=np.random.default_rng(RANDOM_SEED)),
        "energy": mr.bootstrap_noise_floor(true_holdout, metric_fn=mr.energy_distance, rng=np.random.default_rng(RANDOM_SEED)),
    }


def _priority_rank(target: str, method: str):
    order = PRIMARY_PRIORITY.get(target, ())
    if method not in order:
        return False, None
    return True, order.index(method) + 1


# ─────────────────────────────────────────────────────────────────────────
# One target's full leaderboard row-set (baseline + all methods + noise floor)
# ─────────────────────────────────────────────────────────────────────────

def _continuous_leaderboard_for_target(gdf: gpd.GeoDataFrame, target: str) -> dict:
    pairs_base, agg_base = _baseline_pairs(gdf, target)
    p = pairs_base[target]
    n_cc = agg_base["n_complete_cases"]
    n_ho = agg_base["n_holdout"]
    baseline_mae = agg_base["continuous"][target]["mae"]
    baseline_row = _continuous_row(
        p["true"].to_numpy(), p["pred"].to_numpy(), baseline_mae,
        *_priority_rank(target, "__baseline__"),
    )

    out = {
        "n_complete_cases": n_cc, "n_holdout": n_ho,
        "baseline": baseline_row,
        "noise_floor": _noise_floors(p["true"].to_numpy()),
        "methods": {},
    }

    for method in CONTINUOUS_METHODS:
        pairs, agg = _draw_pairs(gdf, target, method)
        pm = pairs[target]
        elig, rank = _priority_rank(target, method)
        out["methods"][method] = _continuous_row(
            pm["true"].to_numpy(), pm["pred"].to_numpy(), baseline_mae, elig, rank,
        )
    return out


def _categorical_leaderboard(gdf: gpd.GeoDataFrame) -> dict:
    target = CATEGORICAL_TARGET
    pairs_base, agg_base = _baseline_pairs(gdf, target, categorical=True)
    if target not in pairs_base:
        return {"status": agg_base["categorical"].get(target, "NOT_SCORABLE")}
    p = pairs_base[target]
    baseline_pfc = agg_base["categorical"][target]["pfc"]
    elig, rank = _priority_rank(target, "__baseline__")
    baseline_row = _categorical_row(p["true"], p["pred"], baseline_pfc, elig, rank)

    out = {
        "n": agg_base["categorical"][target]["n"],
        "n_complete_cases": agg_base["n_complete_cases"],
        "baseline": baseline_row,
        "methods": {},
    }
    pairs_m, agg_m = _draw_pairs(gdf, target, CATEGORICAL_METHOD, categorical=True)
    pm = pairs_m[target]
    elig, rank = _priority_rank(target, CATEGORICAL_METHOD)
    out["methods"][CATEGORICAL_METHOD] = _categorical_row(pm["true"], pm["pred"], baseline_pfc, elig, rank)
    return out


# ─────────────────────────────────────────────────────────────────────────
# Pooled leaderboard
# ─────────────────────────────────────────────────────────────────────────

def run_pooled_leaderboard() -> dict:
    pooled = _load_pooled_cells()
    print(f"[pooled] n={len(pooled)}")

    result: dict = {"continuous": {}, "categorical": {}, "joint_energy_distance": {}}

    for target in CONTINUOUS_TARGETS:
        n_obs = int(pooled[target].notna().sum())
        print(f"[pooled] {target}: observed N (raw) = {n_obs}")
        row = _continuous_leaderboard_for_target(pooled, target)
        result["continuous"][target] = row
        if target in BASELINE_MAE_CROSSCHECK:
            committed = BASELINE_MAE_CROSSCHECK[target]
            regenerated = row["baseline"]["mae"]
            if round(regenerated, 2) != committed:
                raise AssertionError(
                    f"T10 CROSS-CHECK GATE FAILED for {target}: regenerated baseline MAE "
                    f"{regenerated:.4f} (rounds to {round(regenerated, 2)}) != committed "
                    f"RESULTS_phaseC.md value {committed}. STOP -- do not ship this leaderboard."
                )
            print(f"[pooled] {target} baseline cross-check: {regenerated:.3f} rounds to "
                  f"{round(regenerated, 2)} == committed {committed}  MATCH")

    result["categorical"][CATEGORICAL_TARGET] = _categorical_leaderboard(pooled)

    # Joint (levels, height_m) energy distance -- catches a covariance
    # collapse a marginal metric misses (V03 §II.5); pooled only (per-cell
    # complete-case-on-both is too thin, see run_percell_leaderboard).
    joint_targets = ("levels", "height_m")
    pairs_base, agg_base = _joint_baseline_pairs(pooled, joint_targets)
    base_true = np.column_stack([pairs_base[t]["true"].to_numpy() for t in joint_targets])
    base_pred = np.column_stack([pairs_base[t]["pred"].to_numpy() for t in joint_targets])
    joint_out = {
        "n_complete_cases": agg_base["n_complete_cases"],
        "n_holdout": agg_base["n_holdout"],
        "baseline_joint_energy_distance": mr.energy_distance(base_true, base_pred),
        "methods": {},
    }
    for method in CONTINUOUS_METHODS:
        pairs_m, agg_m = _joint_draw_pairs(pooled, joint_targets, method)
        m_true = np.column_stack([pairs_m[t]["true"].to_numpy() for t in joint_targets])
        m_pred = np.column_stack([pairs_m[t]["pred"].to_numpy() for t in joint_targets])
        joint_out["methods"][method] = mr.energy_distance(m_true, m_pred)
    result["joint_energy_distance"]["levels_height_m"] = joint_out

    return result


# ─────────────────────────────────────────────────────────────────────────
# Per-cell leaderboard (production granularity)
# ─────────────────────────────────────────────────────────────────────────

def run_percell_leaderboard() -> dict:
    result: dict = {}
    for cell in POOLED_CELL_ORDER:
        gdf = _load_cell(cell).to_crs(COMMON_CRS)
        cell_out: dict = {"continuous": {}, "categorical": {}}

        for target in CONTINUOUS_TARGETS:
            n_obs = int(gdf[target].notna().sum())
            if n_obs < PER_CELL_MIN_N:
                cell_out["continuous"][target] = f"insufficient_data (n_observed={n_obs} < floor {PER_CELL_MIN_N})"
                continue
            cell_out["continuous"][target] = _continuous_leaderboard_for_target(gdf, target)

        cell_out["categorical"][CATEGORICAL_TARGET] = _categorical_leaderboard(gdf)
        result[cell] = cell_out
        print(f"[per-cell] {cell} done")
    return result


# ─────────────────────────────────────────────────────────────────────────
# Figures (openubem/outputs/, flat)
# ─────────────────────────────────────────────────────────────────────────

def _method_colors() -> dict:
    names = ("baseline",) + CONTINUOUS_METHODS
    colors = [PALETTE["gate"]] + PALETTE["categorical"][: len(CONTINUOUS_METHODS)]
    return dict(zip(names, colors))


def _bar_grid(pooled: dict, value_fn, ylabel: str, title: str, hline_fn=None) -> plt.Figure:
    _style()
    colors = _method_colors()
    fig, axes = plt.subplots(1, len(CONTINUOUS_TARGETS), figsize=(15, 5), sharey=False)
    for ax, target in zip(axes, CONTINUOUS_TARGETS):
        row = pooled["continuous"][target]
        names = ["baseline"] + list(CONTINUOUS_METHODS)
        values = [value_fn(row["baseline"])] + [value_fn(row["methods"][m]) for m in CONTINUOUS_METHODS]
        bars = ax.bar(names, values, color=[colors[n] for n in names], zorder=3)
        for b, n in zip(bars, names):
            if row.get("methods", {}).get(n, {}).get("eligible_primary") or (n == "baseline"):
                b.set_edgecolor(PALETTE["ink"])
                b.set_linewidth(1.4 if n != "baseline" else 0.6)
        if hline_fn is not None:
            hv = hline_fn(row)
            if hv is not None:
                ax.axhline(hv, color=PALETTE["fail"], linestyle="--", linewidth=1.2, zorder=2)
        ax.set_title(target, fontsize=10.5, color=PALETTE["ink"])
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=35, ha="right", fontsize=8.5)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel(ylabel)
    fig.suptitle(title, fontsize=12, color=PALETTE["ink"])
    fig.tight_layout()
    return fig


def build_variance_ratio_figure(pooled: dict) -> plt.Figure:
    fig = _bar_grid(
        pooled, value_fn=lambda r: r["variance_ratio"],
        ylabel="variance ratio (sigma_imputed / sigma_observed)",
        title="CP-DRAW pooled -- variance ratio by method (target = 1.0, dashed)",
        hline_fn=lambda row: 1.0,
    )
    return fig


def build_wasserstein_vs_floor_figure(pooled: dict) -> plt.Figure:
    _style()
    colors = _method_colors()
    fig, axes = plt.subplots(1, len(CONTINUOUS_TARGETS), figsize=(15, 5), sharey=False)
    for ax, target in zip(axes, CONTINUOUS_TARGETS):
        row = pooled["continuous"][target]
        names = ["baseline"] + list(CONTINUOUS_METHODS)
        values = [row["baseline"]["wasserstein"]] + [row["methods"][m]["wasserstein"] for m in CONTINUOUS_METHODS]
        ax.bar(names, values, color=[colors[n] for n in names], zorder=3)
        floor = row["noise_floor"]["wasserstein"]["floor_median"]
        ax.axhline(floor, color=PALETTE["fail"], linestyle="--", linewidth=1.2, zorder=2,
                    label=f"bootstrap noise floor (median)={floor:.2f}")
        ax.set_title(target, fontsize=10.5, color=PALETTE["ink"])
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=35, ha="right", fontsize=8.5)
        ax.legend(fontsize=7.5, frameon=False, loc="upper right")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Wasserstein distance (true vs recovered)")
    fig.suptitle("CP-DRAW pooled -- Wasserstein vs bootstrap noise floor (dashed)", fontsize=12, color=PALETTE["ink"])
    fig.tight_layout()
    return fig


def build_mae_donoharm_figure(pooled: dict) -> plt.Figure:
    fig = _bar_grid(
        pooled, value_fn=lambda r: r["mae"],
        ylabel="MAE (true vs recovered)",
        title="CP-DRAW pooled -- MAE do-no-harm guard (<=1.25x baseline, dashed)",
        hline_fn=lambda row: DO_NO_HARM_MULTIPLIER * row["baseline"]["mae"],
    )
    return fig


def build_categorical_figure(pooled: dict) -> plt.Figure:
    _style()
    cat = pooled["categorical"][CATEGORICAL_TARGET]
    fig, axes = plt.subplots(1, 2, figsize=(9, 5))
    labels = ["baseline (mode)", "catfreq (draw)"]
    colors = [PALETTE["gate"], PALETTE["categorical"][0]]

    pfc_vals = [cat["baseline"]["pfc"], cat["methods"][CATEGORICAL_METHOD]["pfc"]]
    axes[0].bar(labels, pfc_vals, color=colors, zorder=3)
    axes[0].axhline(DO_NO_HARM_MULTIPLIER * cat["baseline"]["pfc"], color=PALETTE["fail"], linestyle="--", linewidth=1.2)
    axes[0].set_title("PFC (proportion falsely classified, do-no-harm guard)", fontsize=9.5)
    axes[0].spines[["top", "right"]].set_visible(False)

    tv_vals = [cat["baseline"]["tv"], cat["methods"][CATEGORICAL_METHOD]["tv"]]
    axes[1].bar(labels, tv_vals, color=colors, zorder=3)
    axes[1].set_title("Total-Variation distance (distribution-shape fidelity, lower=better)", fontsize=9.5)
    axes[1].spines[["top", "right"]].set_visible(False)

    fig.suptitle(f"CP-DRAW pooled -- categorical ({CATEGORICAL_TARGET}, substituting for use_class)", fontsize=11.5)
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────

def main() -> dict:
    print("=" * 70)
    print("T10 CP-DRAW leaderboard -- pooled")
    print("=" * 70)
    pooled = run_pooled_leaderboard()

    print("=" * 70)
    print("T10 CP-DRAW leaderboard -- per-cell")
    print("=" * 70)
    per_cell = run_percell_leaderboard()

    results = {"pooled": pooled, "per_cell": per_cell}

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUTS_DIR / "draw_leaderboard_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Wrote {json_path}")

    _save(build_variance_ratio_figure(pooled), OUTPUTS_DIR / "draw_leaderboard_variance_ratio_pooled.png")
    _save(build_wasserstein_vs_floor_figure(pooled), OUTPUTS_DIR / "draw_leaderboard_wasserstein_vs_floor_pooled.png")
    _save(build_mae_donoharm_figure(pooled), OUTPUTS_DIR / "draw_leaderboard_mae_donoharm_pooled.png")
    _save(build_categorical_figure(pooled), OUTPUTS_DIR / "draw_leaderboard_categorical_pooled.png")
    print(f"Wrote 4 figures to {OUTPUTS_DIR}")

    return results


if __name__ == "__main__":
    main()
