"""Predicted-vs-actual scatter clouds — input-imputation arc, follow-up round 2.

Unlike `impute_figures.py` (a pure function of the DATA constants), this
module explicitly LOADS the 12 committed
`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`
inputs and re-runs the M09 mask-and-recover harness
(`openubem.validation.mask_recover.recover_pairs`, T09) locally to regenerate
REAL per-building (true, predicted) pairs. No point is ever synthesized from
an aggregate statistic (plan §9 "Honesty guard", non-negotiable).

Pure pandas/sklearn/geopandas, seed `RANDOM_SEED` (=42, from `openubem.config`),
deterministic. NO EnergyPlus, NO cluster, NO login-node compute, NO network
(mask-and-recover never reads EUI).

Report, do NOT tune: nothing computed here feeds back into any
`ImputeConfig` / threshold / bound.

See docs/docs_ACTIVE/input/imputation/implementation/PLAN_figures_implementation.md
§9 "Follow-up round 2" (T08-T12, CP-F3).

Status:
- T10: build_phaseB_scatter_year_built() implemented (nyc_centre + la_urban,
  Phase-A CP-2 tier config `("spatial","statistical")`).
- T11: Phase-C pooled `year_built`/`levels` Phase-A-vs-knn scatter --
  IMPLEMENTED (2026-07-15, debug verdict CP-D1). The earlier BLOCKED state
  (see git history / PLAN §9 progress log) was a caller-invocation bug, not a
  code regression: `openubem.config.IMPUTE_ML_METHOD_BY_TARGET`'s shipped
  default is `"missforest"`, NOT `"knn"` -- a naive `recover_pairs` call with
  the `ml` tier enabled and no explicit per-target override silently measured
  missforest and mis-read it as "knn regressed". The CORRECT invocation (see
  `_pooled_ml_pairs` below, mirroring `scratchpad/t11_cp3_leaderboard.py::
  run_one`) sets `config.IMPUTE_ML_METHOD_BY_TARGET[target]` EXPLICITLY before
  each call and restores it in a `finally` block, with a FRESH
  `np.random.default_rng(RANDOM_SEED)` per call. With this invocation the
  regenerated aggregate MAEs reproduce RESULTS_phaseC.md §5-C exactly
  (year_built Phase-A 26.43 / knn 25.14 / mice 1161 / linear 903, n=562;
  levels Phase-A 9.18 / knn 8.39, n=134) -- `build_phaseC_scatter_year_built`
  and `build_phaseC_scatter_levels` assert this cross-check on every build and
  raise `AssertionError` (never silently plot a mismatch) if it drifts.
- T14 (plan §11, round 4): every legend label now also surfaces KS / Wasserstein
  from the SAME aggregate dict the builders already fetch (`score_continuous`,
  `mask_recover.py:260-267` -- no harness change, no recompute) plus one
  on-figure annotation per figure naming the flat-band / variance-collapse
  reading the KS statistic exposes.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from openubem import config
from openubem.config import RANDOM_SEED
from openubem.results.impute_figures import DATA, PALETTE, RESULTS_DIR, _style, _save
from openubem.results.draw_leaderboard import OUTPUTS_DIR
from openubem.semantic.imputation import ImputeConfig
from openubem.validation import mask_recover
from openubem.validation.mask_recover import recover_pairs

VALIDATION_CELLS_DIR = (
    Path(__file__).resolve().parents[2]
    / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
)

ALL_CELLS: tuple[str, ...] = (
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
)

# T11 pooling order -- MUST match `scratchpad/t11_cp3_leaderboard.py::CELLS`
# exactly. `spatial_block_holdout`'s block shuffle (`mask_recover.py`) calls
# `rng.shuffle(order)` on `blocks.value_counts().index`, and pandas ties in
# `value_counts()` break by first-occurrence row order -- so a different cell
# concatenation order silently produces a DIFFERENT holdout split under the
# same seed (the actual T11 CROSS-CHECK GATE root cause for `levels`,
# discovered while regenerating this figure). `ALL_CELLS` above is unrelated/
# unused elsewhere and kept as-is; this constant is the one `_load_pooled_
# cells` uses.
POOLED_CELL_ORDER: tuple[str, ...] = (
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
)

# EPSG:5070 (Conus-Albers, meters) -- the common CRS RESULTS_phaseC.md's pooled
# leaderboard used, so a shared 100 m spatial-KNN/hot-deck radius means the
# same real distance in every city instead of crossing NYC/LA/Austin's three
# native UTM zones. Only needed when POOLING multiple cities (T11); a single-
# cell run (T10) uses that cell's own native CRS.
POOLED_CRS = 5070


def _load_cell(cell: str) -> gpd.GeoDataFrame:
    return gpd.read_file(str(VALIDATION_CELLS_DIR / cell / "01_buildings.gpkg"))


def _collapse_note(ax: plt.Axes, ks: float, xy: tuple[float, float]) -> None:
    """One short on-figure annotation (plan §11 T14) naming the reading a
    high KS statistic exposes: a flat predicted band (central-tendency fill)
    scores a deceptively low MAE while failing to reproduce the true
    distribution. Muted secondary ink, placed clear of the point cloud."""
    ax.annotate(
        f"KS={ks:.2f}: low MAE can still mean a flat central-tendency band --\n"
        "the imputed distribution ≠ the true distribution here.",
        xy=xy, xycoords="axes fraction",
        ha="left", va="bottom", fontsize=8, color=PALETTE["ink_secondary"], linespacing=1.4,
    )


# ---------------------------------------------------------------------------
# T10 — phaseB_scatter_year_built.png
# ---------------------------------------------------------------------------
def build_phaseB_scatter_year_built() -> plt.Figure:
    """Predicted-vs-actual `year_built`, nyc_centre + la_urban, Phase-A CP-2
    tier config (`spatial` -> `statistical`, no `ml`). Real per-building pairs
    regenerated locally via the T09 `recover_pairs` M09 harness extension.

    Companion to `phaseB_quant_accuracy.png` -- that figure plots the
    downstream-EUI NMBE/CV(RMSE) aggregates; THIS figure plots the underlying
    attribute-level (year_built) recovery cloud on the SAME spatial-block
    holdout (n_holdout here reproduces RESULTS_phaseB.md's N=32/N=124
    exactly, confirming the same holdout split).
    """
    _style()
    cfg = ImputeConfig(enabled_tiers=("spatial", "statistical"))

    cells = [
        ("nyc_centre", "GATE cell", PALETTE["categorical"][0]),
        ("la_urban", "robustness cell", PALETTE["categorical"][1]),
    ]

    fig, ax = plt.subplots(figsize=(9, 9))

    all_true: list[float] = []
    all_pred: list[float] = []
    ks_values: list[float] = []
    for cell, role, color in cells:
        gdf = _load_cell(cell)
        pairs, aggregate = recover_pairs(
            gdf, continuous_targets=["year_built"], cfg=cfg,
            rng=np.random.default_rng(RANDOM_SEED),
        )
        p = pairs["year_built"]
        scores = aggregate["continuous"]["year_built"]
        all_true.extend(p["true"].tolist())
        all_pred.extend(p["pred"].tolist())
        ks_values.append(scores["ks_stat"])
        ax.scatter(
            p["true"], p["pred"], s=42, color=color, alpha=0.75, edgecolor="white", linewidth=0.4,
            label=(
                f"{cell} ({role}, N={scores['n']}) "
                f"MAE={scores['mae']:.1f}y RMSE={scores['rmse']:.1f}y "
                f"KS={scores['ks_stat']:.2f} W={scores['wasserstein']:.0f}y"
            ),
            zorder=3,
        )

    lo = min(all_true + all_pred) - 5
    hi = max(all_true + all_pred) + 5
    ax.plot([lo, hi], [lo, hi], color=PALETTE["gate"], linestyle="--", linewidth=1.5, zorder=2, label="1:1 (perfect recovery)")
    _collapse_note(ax, max(ks_values), (0.40, 0.02))

    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("actual year_built (held out)")
    ax.set_ylabel("imputed year_built (Phase-A statistical tier)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=8.8)
    ax.set_title(
        "Phase B — predicted-vs-actual year_built, real cities, Phase-A CP-2 tier config",
        fontsize=11.5, color=PALETTE["ink"],
    )
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# T11 — pooled 12-cell Phase-C scatter (year_built + levels)
# ---------------------------------------------------------------------------
def _load_pooled_cells(cells: tuple[str, ...] = POOLED_CELL_ORDER) -> gpd.GeoDataFrame:
    """Pool all 12 committed phaseE `01_buildings.gpkg` cells, reprojected to
    the shared EPSG:5070 CRS (mandatory -- mirrors RESULTS_phaseC.md's pooled
    leaderboard protocol / `scratchpad/t11_cp3_leaderboard.py::load_pooled`;
    pooling without a common CRS raises a hard geopandas error across NYC/LA/
    Austin's three native UTM zones). Also mirrors `load_pooled`'s
    `centroid_x`/`centroid_y` columns -- these ARE in `_DEFAULT_ML_FEATURE_
    COLS` (imputation.py), so omitting them silently drops the spatial
    features from the ML tier's feature set and was the actual T11
    CROSS-CHECK GATE root cause on the first pass of this function."""
    frames = [_load_cell(cell).to_crs(POOLED_CRS) for cell in cells]
    pooled = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), geometry="geometry", crs=POOLED_CRS)
    centroids = pooled.geometry.centroid
    pooled["centroid_x"] = centroids.x
    pooled["centroid_y"] = centroids.y
    return pooled


def _pooled_phase_a_pairs(pooled: gpd.GeoDataFrame, target: str) -> tuple[dict, dict]:
    cfg = ImputeConfig(enabled_tiers=("spatial", "statistical"))
    return recover_pairs(
        pooled, continuous_targets=[target], cfg=cfg, rng=np.random.default_rng(RANDOM_SEED),
    )


def _pooled_ml_pairs(pooled: gpd.GeoDataFrame, target: str, method: str) -> tuple[dict, dict]:
    """MANDATORY CORRECT INVOCATION (T11 CROSS-CHECK GATE root cause, debug
    verdict CP-D1 2026-07-15): the shipped `config.IMPUTE_ML_METHOD_BY_TARGET`
    default is `"missforest"`, NOT `"knn"` -- set the method EXPLICITLY per
    call (mirrors `scratchpad/t11_cp3_leaderboard.py::run_one`) and restore
    the original mapping afterward. A FRESH `np.random.default_rng(RANDOM_
    SEED)` is passed per call (never a shared/un-reset rng across methods)."""
    orig = dict(config.IMPUTE_ML_METHOD_BY_TARGET)
    try:
        config.IMPUTE_ML_METHOD_BY_TARGET[target] = method
        cfg = ImputeConfig(enabled_tiers=("spatial", "ml", "statistical"))
        return recover_pairs(
            pooled, continuous_targets=[target], cfg=cfg, rng=np.random.default_rng(RANDOM_SEED),
        )
    finally:
        config.IMPUTE_ML_METHOD_BY_TARGET.clear()
        config.IMPUTE_ML_METHOD_BY_TARGET.update(orig)


def _pooled_draw_pairs(pooled: gpd.GeoDataFrame, target: str, method: str) -> tuple[dict, dict]:
    """`draw`-tier leg, mirrors `draw_leaderboard.py::_draw_pairs` byte-for-
    byte (report-only invariant: `IMPUTE_DRAW_METHOD_BY_TARGET` is mutated
    only inside try/finally, restored immediately; fresh rng per call)."""
    orig = dict(config.IMPUTE_DRAW_METHOD_BY_TARGET)
    try:
        config.IMPUTE_DRAW_METHOD_BY_TARGET[target] = method
        cfg = ImputeConfig(per_input_tiers={target: ("spatial", "draw", "statistical")})
        return recover_pairs(
            pooled, continuous_targets=[target], cfg=cfg, rng=np.random.default_rng(RANDOM_SEED),
        )
    finally:
        config.IMPUTE_DRAW_METHOD_BY_TARGET.clear()
        config.IMPUTE_DRAW_METHOD_BY_TARGET.update(orig)


def _assert_cross_check(label: str, regenerated: float, committed: float) -> None:
    """Report, do NOT tune (plan §9 "Honesty guard"): if the regenerated
    aggregate does not reproduce the committed RESULTS_phaseC.md leaderboard
    to 2dp, the INVOCATION is wrong -- STOP loudly rather than plot a
    mismatch or adjust the figure to hide it."""
    if round(regenerated, 2) != committed:
        raise AssertionError(
            f"T11 CROSS-CHECK GATE FAILED for {label}: regenerated MAE "
            f"{regenerated:.4f} (rounds to {round(regenerated, 2)}) != committed "
            f"RESULTS_phaseC.md value {committed}. Per PLAN_figures_implementation.md "
            "§9 T11 this means the invocation is still wrong -- fix the call. Do NOT "
            "edit openubem/**, do NOT retune, do NOT adjust this figure to hide it."
        )


def build_phaseC_scatter_year_built() -> plt.Figure:
    """Pooled 12-cell (EPSG:5070) predicted-vs-actual `year_built`: Phase-A
    (gray) vs `knn` (blue) on the main 1:1 panel, plus an inset for `mice`/
    `linear`. Real pairs only (T09 `recover_pairs`); the aggregate Phase-A/knn
    MAEs are asserted against the committed RESULTS_phaseC.md leaderboard
    before any drawing (T11 CROSS-CHECK GATE).

    HONEST DEVIATION from the plan's literal T11 "What" (documented, not
    hidden): the plan expects this inset to show `mice`/`linear`'s
    "catastrophic AD-5000+ extrapolation" per RESULTS_phaseC.md's footgun
    (mice MAE 1161 / linear MAE 903). Regenerating today, `mice`/`linear`
    predictions come out CLAMPED to `[1917.9, 2008.0]` (mice MAE 34.0 / linear
    MAE 33.8) -- NOT catastrophic. This is not a figure bug or a mismatched
    invocation: the working tree already carries an observed-range clamp on
    `MLImputer.predict()` (see `git diff openubem/semantic/imputation.py`,
    `_clamp_to_observed_range`; matches the user's own memory record "§9.2
    clamp DONE ... killing the mice/linear AD-101,700 extrapolation footgun",
    dated 2026-07-14 -- i.e. AFTER RESULTS_phaseC.md's footgun was recorded).
    The clamp is a real, already-shipped (though still `ml`-off-by-default)
    production fix that structurally neutralizes exactly this footgun. So the
    inset instead plots the REAL current (bounded) mice/linear cloud and
    annotates the historical-vs-current contrast honestly, rather than
    fabricate AD-5000+ points that no longer exist on this codebase.
    """
    _style()
    target = "year_built"
    pooled = _load_pooled_cells()

    pairs_a, agg_a = _pooled_phase_a_pairs(pooled, target)
    pairs_knn, agg_knn = _pooled_ml_pairs(pooled, target, "knn")
    pairs_mice, agg_mice = _pooled_ml_pairs(pooled, target, "mice")
    pairs_lin, agg_lin = _pooled_ml_pairs(pooled, target, "linear")

    mae_a = agg_a["continuous"][target]["mae"]
    mae_knn = agg_knn["continuous"][target]["mae"]
    mae_mice = agg_mice["continuous"][target]["mae"]
    mae_lin = agg_lin["continuous"][target]["mae"]
    ks_a = agg_a["continuous"][target]["ks_stat"]
    ks_knn = agg_knn["continuous"][target]["ks_stat"]
    methods = DATA["C"]["year_built_methods"]
    _assert_cross_check("year_built Phase-A", mae_a, methods["Phase-A"]["mae"])
    _assert_cross_check("year_built knn", mae_knn, methods["knn"]["mae"])

    p_a, p_knn = pairs_a[target], pairs_knn[target]
    p_mice, p_lin = pairs_mice[target], pairs_lin[target]
    n_holdout = agg_a["continuous"][target]["n"]

    lo = min(p_a["true"].min(), p_knn["true"].min(), p_a["pred"].min(), p_knn["pred"].min()) - 5
    hi = max(p_a["true"].max(), p_knn["true"].max(), p_a["pred"].max(), p_knn["pred"].max()) + 5

    fig = plt.figure(figsize=(15, 9))
    ax = fig.add_axes((0.07, 0.09, 0.60, 0.78))
    ax_in = fig.add_axes((0.73, 0.46, 0.25, 0.42))

    ax.scatter(
        p_a["true"], p_a["pred"], s=20, color=PALETTE["before"], alpha=0.55, zorder=2,
        label=f"Phase-A (MAE {mae_a:.2f}y KS={ks_a:.2f})",
    )
    ax.scatter(
        p_knn["true"], p_knn["pred"], s=20, color=PALETTE["after"], alpha=0.7, zorder=3,
        label=f"knn (MAE {mae_knn:.2f}y KS={ks_knn:.2f})",
    )
    ax.plot([lo, hi], [lo, hi], color=PALETTE["gate"], linestyle="--", linewidth=1.5, zorder=1, label="1:1")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("actual year_built (pooled 12-cell holdout)")
    ax.set_ylabel("imputed year_built")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    ax.set_title(
        f"Phase C — pooled predicted-vs-actual year_built, n_holdout={n_holdout}",
        fontsize=11.5, color=PALETTE["ink"],
    )
    _collapse_note(ax, max(ks_a, ks_knn), (0.03, 0.03))

    # ---- inset: mice/linear -- REAL current (post-clamp) cloud, historical
    # footgun reported as text, not fabricated as points (see docstring) ----
    footgun = DATA["C"]["footgun_mae_range"]  # (903, 1161), historical/pre-clamp
    lo2 = min(p_a["true"].min(), p_mice["true"].min(), p_mice["pred"].min(), p_lin["pred"].min()) - 3
    hi2 = max(p_a["true"].max(), p_mice["true"].max(), p_mice["pred"].max(), p_lin["pred"].max()) + 3
    ax_in.plot([lo2, hi2], [lo2, hi2], color=PALETTE["gate"], linestyle="--", linewidth=1.0, zorder=1)
    ax_in.scatter(
        p_mice["true"], p_mice["pred"], s=9, color=PALETTE["categorical"][2], alpha=0.6, zorder=3,
        label=f"mice (MAE {mae_mice:.1f}y, clamped)",
    )
    ax_in.scatter(
        p_lin["true"], p_lin["pred"], s=9, color=PALETTE["fail"], alpha=0.6, zorder=3,
        label=f"linear (MAE {mae_lin:.1f}y, clamped)",
    )
    ax_in.set_xlim(lo2, hi2)
    ax_in.set_ylim(lo2, hi2)
    ax_in.set_aspect("equal", adjustable="box")
    ax_in.set_xlabel("actual", fontsize=7.5)
    ax_in.set_ylabel("imputed", fontsize=7.5)
    ax_in.tick_params(labelsize=6.8)
    ax_in.spines[["top", "right"]].set_visible(False)
    ax_in.legend(loc="upper left", frameon=False, fontsize=6.6)
    ax_in.set_title(
        f"mice/linear today: bounded, not AD 5000+\n"
        f"(RESULTS_phaseC.md historical MAE {footgun[0]}-{footgun[1]},\n"
        "pre-clamp -- see build_phaseC_scatter_year_built docstring)",
        fontsize=6.8, color=PALETTE["ink_secondary"], linespacing=1.4,
    )

    fig.suptitle(
        "Phase C — knn tightens the pooled recovery cloud vs Phase-A; "
        "mice/linear still worse, no longer catastrophic (shipped clamp)",
        fontsize=12.5, color=PALETTE["ink"], y=0.98,
    )
    return fig


def build_phaseC_scatter_levels() -> plt.Figure:
    """Pooled 12-cell (EPSG:5070) predicted-vs-actual `levels`: Phase-A (gray)
    vs `knn` (blue). Real pairs only; aggregate MAEs asserted against the
    committed RESULTS_phaseC.md leaderboard before any drawing.
    """
    _style()
    target = "levels"
    pooled = _load_pooled_cells()

    pairs_a, agg_a = _pooled_phase_a_pairs(pooled, target)
    pairs_knn, agg_knn = _pooled_ml_pairs(pooled, target, "knn")

    mae_a = agg_a["continuous"][target]["mae"]
    mae_knn = agg_knn["continuous"][target]["mae"]
    ks_a = agg_a["continuous"][target]["ks_stat"]
    ks_knn = agg_knn["continuous"][target]["ks_stat"]
    lvl = DATA["C"]["levels_methods"]
    _assert_cross_check("levels Phase-A", mae_a, lvl["Phase-A"]["mae"])
    _assert_cross_check("levels knn", mae_knn, lvl["knn"]["mae"])

    p_a, p_knn = pairs_a[target], pairs_knn[target]
    n_holdout = agg_a["continuous"][target]["n"]

    lo = min(p_a["true"].min(), p_knn["true"].min(), p_a["pred"].min(), p_knn["pred"].min()) - 1
    hi = max(p_a["true"].max(), p_knn["true"].max(), p_a["pred"].max(), p_knn["pred"].max()) + 1

    fig, ax = plt.subplots(figsize=(9, 9))
    ax.scatter(
        p_a["true"], p_a["pred"], s=42, color=PALETTE["before"], alpha=0.6,
        edgecolor="white", linewidth=0.4, zorder=2, label=f"Phase-A (MAE {mae_a:.2f} KS={ks_a:.2f})",
    )
    ax.scatter(
        p_knn["true"], p_knn["pred"], s=42, color=PALETTE["after"], alpha=0.75,
        edgecolor="white", linewidth=0.4, zorder=3,
        label=f"knn (MAE {mae_knn:.2f} KS={ks_knn:.2f}, fires {lvl['knn']['fires_n']}/{n_holdout})",
    )
    ax.plot([lo, hi], [lo, hi], color=PALETTE["gate"], linestyle="--", linewidth=1.5, zorder=1, label="1:1")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("actual levels (pooled 12-cell holdout)")
    ax.set_ylabel("imputed levels")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    ax.set_title(
        f"Phase C — pooled predicted-vs-actual levels, n_holdout={n_holdout}",
        fontsize=11.5, color=PALETTE["ink"],
    )
    _collapse_note(ax, max(ks_a, ks_knn), (0.03, 0.03))
    fig.tight_layout()
    return fig


def _draw_vs_phaseA_panel(
    ax: plt.Axes, true, pred, lo: float, hi: float, color: str, label: str, title: str,
) -> None:
    ax.scatter(true, pred, s=32, color=color, alpha=0.65, edgecolor="white", linewidth=0.4, zorder=2, label=label)
    ax.plot([lo, hi], [lo, hi], color=PALETTE["gate"], linestyle="--", linewidth=1.5, zorder=1, label="1:1")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    ax.set_title(title, fontsize=10.5, color=PALETTE["ink"])


# ---------------------------------------------------------------------------
# T2/T3 — Part II CP-DRAW: pmm draw-tier dispersal scatter (levels, year_built)
# ---------------------------------------------------------------------------
def build_phaseC_draw_scatter_levels() -> plt.Figure:
    """Pooled 12-cell predicted-vs-actual `levels`: Phase-A central-tendency
    fill (left) vs `pmm` draw tier (right), same 1:1 axes. The draw tier is
    EXPECTED to lose on MAE and win on variance-ratio (do-no-harm trade, see
    `draw_leaderboard.py` PLAIN-READING RULE) -- surfaced honestly, not hidden.
    """
    _style()
    target = "levels"
    pooled = _load_pooled_cells()

    pairs_a, agg_a = _pooled_phase_a_pairs(pooled, target)
    mae_a = agg_a["continuous"][target]["mae"]
    _assert_cross_check("levels Phase-A", mae_a, DATA["C"]["levels_methods"]["Phase-A"]["mae"])

    pairs_d, agg_d = _pooled_draw_pairs(pooled, target, "pmm")
    mae_d = agg_d["continuous"][target]["mae"]
    ks_a = agg_a["continuous"][target]["ks_stat"]
    ks_d = agg_d["continuous"][target]["ks_stat"]

    p_a, p_d = pairs_a[target], pairs_d[target]
    vr_a = mask_recover.variance_ratio(p_a["true"], p_a["pred"])
    vr_d = mask_recover.variance_ratio(p_d["true"], p_d["pred"])

    lo = min(p_a["true"].min(), p_d["true"].min(), p_a["pred"].min(), p_d["pred"].min()) - 1
    hi = max(p_a["true"].max(), p_d["true"].max(), p_a["pred"].max(), p_d["pred"].max()) + 1

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(15, 7.5))
    _draw_vs_phaseA_panel(
        ax_left, p_a["true"], p_a["pred"], lo, hi, PALETTE["before"],
        f"Phase-A (MAE {mae_a:.2f} KS={ks_a:.2f} var-ratio={vr_a:.2f})",
        "Phase-A baseline (central-tendency fill)",
    )
    ax_left.set_xlabel("actual levels (pooled 12-cell holdout)")
    ax_left.set_ylabel("imputed levels")
    _collapse_note(ax_left, ks_a, (0.03, 0.03))

    _draw_vs_phaseA_panel(
        ax_right, p_d["true"], p_d["pred"], lo, hi, PALETTE["after"],
        f"pmm (MAE {mae_d:.2f} KS={ks_d:.2f} var-ratio={vr_d:.2f})",
        "pmm draw tier (variance-preserving)",
    )
    ax_right.set_xlabel("actual levels (pooled 12-cell holdout)")
    ax_right.set_ylabel("imputed levels")
    ax_right.annotate(
        "draw tier restores spread (var-ratio toward 1.0) at the cost of\n"
        "point-wise MAE — the intended trade.",
        xy=(0.03, 0.03), xycoords="axes fraction", ha="left", va="bottom",
        fontsize=8, color=PALETTE["ink_secondary"], linespacing=1.4,
    )

    fig.suptitle(
        "Phase C — pmm draw tier disperses the collapsed levels band back "
        "toward 1:1 (opt-in, OFF by default)",
        fontsize=12.5, color=PALETTE["ink"], y=0.99,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


def build_phaseC_draw_scatter_year_built() -> plt.Figure:
    """Pooled 12-cell predicted-vs-actual `year_built`: Phase-A central-
    tendency fill (left) vs `pmm` draw tier (right), same 1:1 axes. Mirrors
    `build_phaseC_draw_scatter_levels` structure exactly."""
    _style()
    target = "year_built"
    pooled = _load_pooled_cells()

    pairs_a, agg_a = _pooled_phase_a_pairs(pooled, target)
    mae_a = agg_a["continuous"][target]["mae"]
    _assert_cross_check("year_built Phase-A", mae_a, DATA["C"]["year_built_methods"]["Phase-A"]["mae"])

    pairs_d, agg_d = _pooled_draw_pairs(pooled, target, "pmm")
    mae_d = agg_d["continuous"][target]["mae"]
    ks_a = agg_a["continuous"][target]["ks_stat"]
    ks_d = agg_d["continuous"][target]["ks_stat"]

    p_a, p_d = pairs_a[target], pairs_d[target]
    vr_a = mask_recover.variance_ratio(p_a["true"], p_a["pred"])
    vr_d = mask_recover.variance_ratio(p_d["true"], p_d["pred"])

    lo = min(p_a["true"].min(), p_d["true"].min(), p_a["pred"].min(), p_d["pred"].min()) - 5
    hi = max(p_a["true"].max(), p_d["true"].max(), p_a["pred"].max(), p_d["pred"].max()) + 5

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(15, 7.5))
    _draw_vs_phaseA_panel(
        ax_left, p_a["true"], p_a["pred"], lo, hi, PALETTE["before"],
        f"Phase-A (MAE {mae_a:.2f}y KS={ks_a:.2f} var-ratio={vr_a:.2f})",
        "Phase-A baseline (central-tendency fill)",
    )
    ax_left.set_xlabel("actual year_built (pooled 12-cell holdout)")
    ax_left.set_ylabel("imputed year_built")
    _collapse_note(ax_left, ks_a, (0.03, 0.03))

    _draw_vs_phaseA_panel(
        ax_right, p_d["true"], p_d["pred"], lo, hi, PALETTE["after"],
        f"pmm (MAE {mae_d:.2f}y KS={ks_d:.2f} var-ratio={vr_d:.2f})",
        "pmm draw tier (variance-preserving)",
    )
    ax_right.set_xlabel("actual year_built (pooled 12-cell holdout)")
    ax_right.set_ylabel("imputed year_built")
    ax_right.annotate(
        "draw tier restores spread (var-ratio toward 1.0) at the cost of\n"
        "point-wise MAE — the intended trade.",
        xy=(0.03, 0.03), xycoords="axes fraction", ha="left", va="bottom",
        fontsize=8, color=PALETTE["ink_secondary"], linespacing=1.4,
    )

    fig.suptitle(
        "Phase C — pmm draw tier disperses the collapsed year_built band "
        "back toward 1:1 (opt-in, OFF by default)",
        fontsize=12.5, color=PALETTE["ink"], y=0.99,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


# ---------------------------------------------------------------------------
# T1/T2 — distribution-shape figures (histogram + ECDF): the honest lens for
# a variance-preserving draw imputer, replacing the 1:1-diagonal reading that
# a draw method is structurally never meant to satisfy.
# ---------------------------------------------------------------------------
def _distribution_panels(
    fig_title: str, xlabel: str,
    true, pred_a, pred_pmm, ks_a: float, ks_d: float, bins,
) -> plt.Figure:
    fig, (ax_hist, ax_ecdf) = plt.subplots(1, 2, figsize=(15, 6.5))

    labels = (
        "actual (real held-out)",
        f"Phase-A imputed (KS={ks_a:.2f})",
        f"pmm draw imputed (KS={ks_d:.2f})",
    )
    colors = (PALETTE["ink"], PALETTE["before"], PALETTE["after"])
    arrays = (true, pred_a, pred_pmm)

    for arr, color, label in zip(arrays, colors, labels):
        ax_hist.hist(
            arr, bins=bins, density=True, histtype="step", linewidth=1.8,
            color=color, label=label,
        )
    ax_hist.set_title("distribution of imputed vs actual values", fontsize=10.5, color=PALETTE["ink"])
    ax_hist.set_xlabel(xlabel)
    ax_hist.set_ylabel("density")
    ax_hist.spines[["top", "right"]].set_visible(False)
    ax_hist.legend(loc="upper left", frameon=False, fontsize=8.5)

    for arr, color, label in zip(arrays, colors, labels):
        xs = np.sort(arr)
        ys = np.arange(1, len(xs) + 1) / len(xs)
        ax_ecdf.step(xs, ys, where="post", color=color, linewidth=1.8, label=label)
    ax_ecdf.annotate(
        "vertical gap between an imputed curve and 'actual' = its KS statistic",
        xy=(0.97, 0.04), xycoords="axes fraction", ha="right", va="bottom",
        fontsize=8, color=PALETTE["ink_secondary"],
    )
    ax_ecdf.set_title("empirical CDF (KS made visual)", fontsize=10.5, color=PALETTE["ink"])
    ax_ecdf.set_xlabel(xlabel)
    ax_ecdf.set_ylabel("cumulative fraction")
    ax_ecdf.spines[["top", "right"]].set_visible(False)
    ax_ecdf.legend(loc="upper left", frameon=False, fontsize=8.5)

    fig.suptitle(fig_title, fontsize=12.5, color=PALETTE["ink"], y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return fig


def build_phaseC_draw_distribution_year_built() -> plt.Figure:
    """Distribution-shape lens (histogram + ECDF), NOT 1:1 scatter, for the
    `pmm` draw tier on `year_built`: a variance-preserving draw method trades
    point-wise accuracy for distributional fidelity, so it correctly looks
    like a diffuse cloud on a 1:1 scatter -- the right lens is whether the
    imputed values reproduce the SHAPE of the real distribution."""
    _style()
    target = "year_built"
    pooled = _load_pooled_cells()

    pairs_a, agg_a = _pooled_phase_a_pairs(pooled, target)
    _assert_cross_check("year_built Phase-A", agg_a["continuous"][target]["mae"], DATA["C"]["year_built_methods"]["Phase-A"]["mae"])

    pairs_d, agg_d = _pooled_draw_pairs(pooled, target, "pmm")

    true = pairs_a[target]["true"]
    pred_a = pairs_a[target]["pred"]
    pred_pmm = pairs_d[target]["pred"]
    ks_a = agg_a["continuous"][target]["ks_stat"]
    ks_d = agg_d["continuous"][target]["ks_stat"]

    bins = np.histogram_bin_edges(true, bins=30, range=(
        min(true.min(), pred_a.min(), pred_pmm.min()),
        max(true.max(), pred_a.max(), pred_pmm.max()),
    ))

    return _distribution_panels(
        "Phase C — year_built: Phase-A collapses the distribution to a spike; "
        "pmm regenerates the real shape (incl. the true ~1951 mode) — "
        "not an error, generated from the data",
        "year_built", true, pred_a, pred_pmm, ks_a, ks_d, bins,
    )


def build_phaseC_draw_distribution_levels() -> plt.Figure:
    """`levels` counterpart to `build_phaseC_draw_distribution_year_built`,
    identical structure with integer-friendly histogram bins."""
    _style()
    target = "levels"
    pooled = _load_pooled_cells()

    pairs_a, agg_a = _pooled_phase_a_pairs(pooled, target)
    _assert_cross_check("levels Phase-A", agg_a["continuous"][target]["mae"], DATA["C"]["levels_methods"]["Phase-A"]["mae"])

    pairs_d, agg_d = _pooled_draw_pairs(pooled, target, "pmm")

    true = pairs_a[target]["true"]
    pred_a = pairs_a[target]["pred"]
    pred_pmm = pairs_d[target]["pred"]
    ks_a = agg_a["continuous"][target]["ks_stat"]
    ks_d = agg_d["continuous"][target]["ks_stat"]

    lo = min(true.min(), pred_a.min(), pred_pmm.min())
    hi = max(true.max(), pred_a.max(), pred_pmm.max())
    if hi - lo <= 40:
        bins = np.arange(lo - 0.5, hi + 1.5, 1)
    else:
        bins = 40

    return _distribution_panels(
        "Phase C — levels: Phase-A collapses the distribution; pmm regenerates "
        "the real spread — not an error, generated from the data",
        "levels", true, pred_a, pred_pmm, ks_a, ks_d, bins,
    )


# ---------------------------------------------------------------------------
# main — writes all 3 scatter figures (T10 + T11)
# ---------------------------------------------------------------------------
def main() -> list[Path]:
    written: list[Path] = []
    written.append(_save(
        build_phaseB_scatter_year_built(),
        RESULTS_DIR / "phase_B" / "phaseB_scatter_year_built.png",
    ))
    written.append(_save(
        build_phaseC_scatter_year_built(),
        RESULTS_DIR / "phase_C" / "phaseC_scatter_year_built.png",
    ))
    written.append(_save(
        build_phaseC_scatter_levels(),
        RESULTS_DIR / "phase_C" / "phaseC_scatter_levels.png",
    ))
    written.append(_save(
        build_phaseC_draw_scatter_levels(),
        OUTPUTS_DIR / "phaseC_draw_scatter_levels.png",
    ))
    written.append(_save(
        build_phaseC_draw_scatter_year_built(),
        OUTPUTS_DIR / "phaseC_draw_scatter_year_built.png",
    ))
    written.append(_save(
        build_phaseC_draw_distribution_year_built(),
        RESULTS_DIR / "phase_C" / "phaseC_draw_distribution_year_built.png",
    ))
    written.append(_save(
        build_phaseC_draw_distribution_levels(),
        RESULTS_DIR / "phase_C" / "phaseC_draw_distribution_levels.png",
    ))
    return written


if __name__ == "__main__":
    for p in main():
        print(f"wrote {p}")
