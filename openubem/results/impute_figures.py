"""Quantitative before/after + method-performance figures — input-imputation arc.

Complements the 20 existing (mostly schematic) phase figures under
`docs/docs_ACTIVE/input/imputation/results/phase_{A..E}/` with a purely
quantitative set built ONLY from the DATA constants below, each cited to its
source-of-record RESULTS doc line. No simulation, no cluster, no network, no
RNG — figures are a pure, deterministic function of DATA.

See docs/docs_ACTIVE/input/imputation/implementation/PLAN_figures_implementation.md
(binding spec: §2 design system, §5 DATA source-of-truth, §6 task list).

Status (this module is built incrementally, task-by-task):
- T01: scaffold, DATA, _style(), palette, stubs.
- T02: build_phaseA_provenance() implemented.
- T03: build_phaseB_accuracy() implemented.
- T04: build_phaseC_leaderboard() + build_phaseC_eui_beforeafter() implemented.
- T05: build_phaseD_fillrate() implemented.
- T06: build_phaseE_scalegap() implemented.
- T07: build_arc_summary() implemented; main() writes all 7 PNGs.
- T15 (plan §11, round 4): Phase-B ARC headline + build_phaseB_accuracy() suptitle
  reworded from "accurate" to "aggregate EUI unbiased" — framing only, every
  DATA["B"] number and the "PASS" status are unchanged (they overstated a
  mean-bias gate as per-building accuracy; see RESULTS_phaseB.md).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Paths (module-level; no side effects on import)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "docs" / "docs_ACTIVE" / "input" / "imputation" / "results"

# ---------------------------------------------------------------------------
# Palette (plan §2 — reserved semantics; never cycled arbitrarily)
# ---------------------------------------------------------------------------
PALETTE = {
    "surface": "#fcfcfb",
    "ink": "#0b0b0b",
    "ink_secondary": "#52514e",
    "ink_muted": "#898781",
    "grid": "#e1e0d9",
    "axis": "#c3c2b7",
    # status
    "pass": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "fail": "#d03b3b",
    # before/after (fixed mapping — identical across all figures)
    "before": "#898781",
    "after": "#2a78d6",
    # gate/threshold lines
    "gate": "#898781",
    # categorical (fixed order, never cycled)
    "categorical": [
        "#2a78d6", "#1baf7a", "#eda100", "#008300",
        "#4a3aa7", "#e34948", "#e87ba4", "#eb6834",
    ],
    # sequential (magnitude / fill-rate ramp, light -> dark)
    "sequential": ["#cde2fb", "#86b6ef", "#3987e5", "#2a78d6", "#1c5cab"],
}

# ---------------------------------------------------------------------------
# DATA — every number a figure may plot. Verbatim from the plan's §5
# "Source-of-truth verified facts" (manager-transcribed from the RESULTS
# docs). Do NOT add, round, or derive a number not present here.
# ---------------------------------------------------------------------------
DATA = {
    "A": {
        "tests_total": 76,  # RESULTS_phaseA.md L19
        "tests_pass": 76,  # RESULTS_phaseA.md L19
        "tests_suites": {  # RESULTS_phaseA.md L32-37
            "test_tierB_provenance": 23,
            "test_vintage_donor": 9,
            "test_levels_groupwise": 13,
            "test_spatial_impute": 10,
            "test_provenance": 21,
        },
        "idfs_byte_identical": 25,  # RESULTS_phaseA.md L22, L51
        "idfs_total": 25,  # RESULTS_phaseA.md L22, L51
        "eui_change_kwh_m2": 0.0,  # RESULTS_phaseA.md L22-24, L51
        # the three fills fixed (before -> after), plan §5-A L59-64
        # (short single-line labels for the chart; the full mechanism is
        # spelled out in prose in RESULTS_phaseA.md and the tokens table).
        "fills": [
            {
                "category": "year_built",
                "before_label": "biased oldest default (pre-1980)",
                "after_label": "donor/neighbour vintage (tokened)",
            },
            {
                "category": "levels",
                "before_label": "flat default: 1",
                "after_label": "group-wise median",
            },
            {
                "category": "HVAC / DHW / cooking",
                "before_label": "no flag (untraceable)",
                "after_label": "100% flagged",
            },
        ],
        # provenance coverage of unobserved fills, plan §5-A L172-174
        "provenance_coverage_before_pct": 0,
        "provenance_coverage_after_pct": 100,
    },
    "B": {
        "gate_nmbe_pct": 5.0,  # RESULTS_phaseB.md L33 (gate column, 5%/15%)
        "gate_cvrmse_pct": 15.0,  # RESULTS_phaseB.md L33
        "nyc_centre": {"n": 32, "nmbe": 0.49, "cvrmse": 1.71, "verdict": "PASS"},  # RESULTS_phaseB.md L35
        "la_urban": {"n": 124, "nmbe": 0.08, "cvrmse": 0.61, "verdict": "PASS"},  # RESULTS_phaseB.md L36
        "synthetic_live_smoke": {"n": 10, "nmbe": 0.04, "cvrmse": 3.1, "verdict": "PASS"},  # RESULTS_phaseB.md L37
        "fleet_synthetic_context": {"nmbe": 0.012, "cvrmse": 1.75},  # RESULTS_phaseB.md L39 (context only)
        "tests_total": 121,  # RESULTS_phaseB.md L63-73 ("121/121")
    },
    "C": {
        # year_built attribute leaderboard, n_holdout = 562, plan §5-C L188-198
        "year_built_n_holdout": 562,
        "year_built_methods": {
            "Phase-A": {"mae": 26.43, "rmse": 32.36, "ks": 0.509, "wasserstein": 26.21, "exact_bin": 456, "exact_bin_pct": 81.1, "note": "reference"},
            "knn": {"mae": 25.14, "rmse": 31.91, "ks": 0.343, "wasserstein": 18.05, "exact_bin": 449, "note": "winner — beats A on every continuous metric"},
            "missforest": {"mae": 31.5, "mae_delta": 5.1, "exact_bin_lo": 379, "exact_bin_hi": 382, "note": "mixed (worse bin)"},
            "rf": {"mae": 32.9, "mae_delta": 6.5, "exact_bin_lo": 379, "exact_bin_hi": 382, "note": "mixed (worse bin)"},
            "mice": {"mae": 1161, "note": "catastrophic extrapolation"},
            "linear": {"mae": 903, "note": "catastrophic extrapolation"},
            "histgbm": {"note": "= Phase-A (below floor -> falls back)"},
        },
        # levels attribute leaderboard, n_holdout = 134, plan §5-C L200-201
        "levels_n_holdout": 134,
        "levels_methods": {
            "Phase-A": {"mae": 9.18, "rmse": 15.06, "ks": 0.470},
            "knn": {"mae": 8.39, "mae_delta": -0.79, "rmse": 12.98, "rmse_delta": -2.08, "ks": 0.425, "fires_n": 117},
        },
        # EUI do-no-harm A/B, 167 nyc_centre buildings, plan §5-C L203-209
        "eui_n_buildings": 167,
        "eui_nmbe": -5.51,  # RESULTS_phaseC.md, gate |NMBE| < 5% -> FAIL
        "eui_nmbe_gate": 5.0,
        "eui_nmbe_verdict": "FAIL",
        "eui_cvrmse": 7.93,  # gate < 15% -> PASS
        "eui_cvrmse_gate": 15.0,
        "eui_cvrmse_verdict": "PASS",
        "eui_buildings_moved_down": 167,
        "eui_mean_before": 149.87,  # kWh/m2
        "eui_mean_after": 141.61,  # kWh/m2
        "eui_mbe": -8.26,
        "eui_delta_pct_median": -5.86,
        "eui_delta_pct_min": -15.85,
        # footgun, plan §5-C L207-209 / L113-118
        "footgun_ad_threshold": 5000,
        "footgun_mae_range": (903, 1161),
        "footgun_stamped_pct": 100,
    },
    "D": {
        # Real Overture LIVE_SMOKE, plan §5-D L211-222
        "release": "2026-06-17.0",
        "n_buildings": 1667,
        "cell": "NYC-centre",
        "fill_rates": {
            "height_m": {"pct": 87.6, "reason": "direct join, all FUSED_OVERTURE_HIGH; misses fall through"},
            "levels": {"pct": 0.0, "reason": "real coverage property of dense already-mapped Manhattan\n(Overture carries few)"},
            "use_class": {"pct": 0.0, "reason": "same; of class/subtype tokens present, 73.6% map\nthrough the crosswalk; 6 unmapped"},
            "year_built": {"pct": 0.0, "reason": "structural — Overture Buildings schema has\nno year_built column (caught by LIVE_SMOKE)"},
        },
        "use_class_crosswalk_map_pct": 73.6,
        "gate_pass": 171,
        "gate_fail": 0,
        "license_size_kb": 279,
        "license": "CDLA-Permissive-2.0",
        "byte_identical_tests_without_source": 2,
    },
    "E": {
        # Data-scale viability, plan §5-E L224-231
        "classical_dominates_below_n": 30_000,
        "tabddpm_wins_above_n": (10_000, 20_000),
        "gain_needs_above_n": 30_000,
        "ubem_deep_precedent_n": 2_200_000,  # Sinha 2026, ResStock
        "openubem_cell_size_range": (100, 3_000),  # "hundreds to low-thousands"
        "verdicts": {
            "deep-generative": "SKIP",
            "GNN": "REJECT",
            "LLM": "FIRM DISQUALIFICATION",
            "TabPFN": "NOT READY",
        },
    },
    # Arc summary (F00), plan §5 L233-236 — one headline per phase
    "ARC": {
        "phases": [
            {"phase": "A", "headline": "safe\n25/25 byte-identical", "status": "PASS"},
            {"phase": "B", "headline": "aggregate EUI unbiased\nNMBE +0.49% (not per-bldg accurate)", "status": "PASS"},
            {"phase": "C", "headline": "ML built-but-off (opt-in)\nattribute win; EUI-neutral per-cell", "status": "OFF"},
            {"phase": "D", "headline": "fusion shipped\nheight_m 87.6%", "status": "PASS"},
            {"phase": "E", "headline": "frontier ruled out\nnone ship", "status": "RULED_OUT"},
        ],
    },
}


# ---------------------------------------------------------------------------
# Shared style
# ---------------------------------------------------------------------------
def _style() -> None:
    """Apply the plan §2 rcParams. Safe to call repeatedly; no I/O."""
    plt.rcParams.update({
        "figure.facecolor": PALETTE["surface"],
        "axes.facecolor": PALETTE["surface"],
        "savefig.facecolor": PALETTE["surface"],
        "savefig.dpi": 200,
        "text.color": PALETTE["ink"],
        "axes.edgecolor": PALETTE["axis"],
        "axes.labelcolor": PALETTE["ink_secondary"],
        "xtick.color": PALETTE["ink_muted"],
        "ytick.color": PALETTE["ink_muted"],
        "grid.color": PALETTE["grid"],
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.grid": False,
    })


def _save(fig: plt.Figure, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(path), dpi=200, bbox_inches="tight", facecolor=PALETTE["surface"])
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# T02 — phaseA_quant_provenance.png
# ---------------------------------------------------------------------------
def build_phaseA_provenance() -> plt.Figure:
    """Two-panel: (left) provenance-coverage before/after per fill category,
    (right) hero stat panel (25/25 byte-identical -> 0.0 kWh/m2, 76/76 tests).
    """
    _style()
    d = DATA["A"]
    fills = d["fills"]
    n = len(fills)

    fig, (ax_l, ax_r) = plt.subplots(
        1, 2, figsize=(14, 5.2), gridspec_kw={"width_ratios": [2, 1]},
    )

    # ---- left: grouped before/after bars (provenance coverage %) ----
    # categories spaced 1.5 apart (rather than 1.0) so the merged
    # value+description labels have room and never touch the adjacent pair.
    spacing = 1.5
    x = [i * spacing for i in range(n)]
    width = 0.32
    before_vals = [d["provenance_coverage_before_pct"]] * n
    after_vals = [d["provenance_coverage_after_pct"]] * n

    bars_before = ax_l.bar(
        [xi - width / 2 for xi in x], before_vals, width,
        color=PALETTE["before"], label="before (untraceable / biased)",
    )
    bars_after = ax_l.bar(
        [xi + width / 2 for xi in x], after_vals, width,
        color=PALETTE["after"], label="after (tokened + confidence)",
    )

    # "after" bars get a merged value+description label floating in the
    # clear whitespace above the bar (never collides with anything). The
    # "before" 0% description instead rides inside the x-tick label, which
    # has dedicated below-axis space and so cannot graze either bar.
    for xi, fill in zip(x, fills):
        ax_l.text(
            xi + width / 2, after_vals[0] + 3, f"{after_vals[0]:.0f}% — {fill['after_label']}",
            ha="center", va="bottom", fontsize=7.3, color=PALETTE["ink_secondary"],
            linespacing=1.3,
        )
        # numeric value re-stated inside the after bar for scan-at-a-glance
        ax_l.text(
            xi + width / 2, after_vals[0] / 2, f"{after_vals[0]:.0f}%",
            ha="center", va="center", fontsize=9.5, color="white", fontweight="bold",
        )

    ax_l.set_xticks(x)
    ax_l.set_xticklabels(
        [f"{f['category']}\n0% — {f['before_label']}" for f in fills],
        fontsize=9.5, linespacing=1.8,
    )
    ax_l.set_xlim(x[0] - 0.75, x[-1] + 0.75)
    ax_l.set_ylabel("provenance coverage of unobserved fills (%)")
    ax_l.set_ylim(0, 145)
    ax_l.set_yticks([0, 25, 50, 75, 100])
    ax_l.spines[["top", "right"]].set_visible(False)
    ax_l.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False, fontsize=8.5)
    ax_l.set_title("Every unobserved fill now carries a token + confidence tier", fontsize=10.5, color=PALETTE["ink"])

    # ---- right: hero stat panel ----
    ax_r.axis("off")
    ax_r.set_xlim(0, 1)
    ax_r.set_ylim(0, 1)
    hero = [
        (f"{d['idfs_byte_identical']}/{d['idfs_total']}", "IDFs byte-identical"),
        (f"{d['eui_change_kwh_m2']:.1f} kWh/m²", "EUI change"),
        (f"{d['tests_pass']}/{d['tests_total']}", "unit tests green"),
    ]
    ys = [0.82, 0.5, 0.18]
    for (value, label), y in zip(hero, ys):
        ax_r.text(0.5, y + 0.07, value, ha="center", va="center", fontsize=22, fontweight="bold", color=PALETTE["pass"])
        ax_r.text(0.5, y - 0.05, label, ha="center", va="center", fontsize=10, color=PALETTE["ink_secondary"])
    ax_r.set_title("Added traceability, changed zero energy", fontsize=10.5, color=PALETTE["ink"])

    fig.suptitle(
        "Phase A — provenance added at zero EUI cost",
        fontsize=13, color=PALETTE["ink"], y=1.02,
    )
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# T03 — phaseB_quant_accuracy.png
# ---------------------------------------------------------------------------
def build_phaseB_accuracy() -> plt.Figure:
    """Two subplots (|NMBE| | CV(RMSE)), each with its own dashed gate line,
    one bar per cell (nyc_centre GATE, la_urban robustness, synthetic context).
    """
    _style()
    d = DATA["B"]

    rows = [
        ("nyc_centre\n(GATE, N=32)", d["nyc_centre"], PALETTE["pass"], 1.0),
        ("la_urban\n(robustness, N=124)", d["la_urban"], PALETTE["pass"], 1.0),
        ("synthetic\nLIVE_SMOKE (N=10)", d["synthetic_live_smoke"], PALETTE["pass"], 0.55),
    ]
    labels = [r[0] for r in rows]
    x = list(range(len(rows)))

    fig, (ax_n, ax_c) = plt.subplots(1, 2, figsize=(13, 5.2))

    # ---- NMBE panel ----
    nmbe_vals = [abs(r[1]["nmbe"]) for r in rows]
    colors = [r[2] for r in rows]
    alphas = [r[3] for r in rows]
    bars = ax_n.bar(x, nmbe_vals, width=0.5, color=colors)
    for b, a in zip(bars, alphas):
        b.set_alpha(a)
    for xi, v in zip(x, nmbe_vals):
        ax_n.text(xi, v + 0.08, f"{v:.2f}%", ha="center", va="bottom", fontsize=9.5, color=PALETTE["ink"])
    ax_n.axhline(d["gate_nmbe_pct"], color=PALETTE["gate"], linestyle="--", linewidth=1.5)
    ax_n.text(
        len(rows) - 0.5, d["gate_nmbe_pct"] + 0.1, f"gate {d['gate_nmbe_pct']:.0f}%",
        ha="right", va="bottom", fontsize=9, color=PALETTE["ink_muted"],
    )
    ax_n.set_xticks(x)
    ax_n.set_xticklabels(labels, fontsize=8.8)
    ax_n.set_ylabel("|NMBE| (%)")
    ax_n.set_ylim(0, d["gate_nmbe_pct"] * 1.35)
    ax_n.spines[["top", "right"]].set_visible(False)
    ax_n.set_title("Mean bias vs 5% gate", fontsize=10.5, color=PALETTE["ink"])

    # ---- CV(RMSE) panel ----
    cv_vals = [r[1]["cvrmse"] for r in rows]
    bars2 = ax_c.bar(x, cv_vals, width=0.5, color=colors)
    for b, a in zip(bars2, alphas):
        b.set_alpha(a)
    for xi, v in zip(x, cv_vals):
        ax_c.text(xi, v + 0.25, f"{v:.2f}%", ha="center", va="bottom", fontsize=9.5, color=PALETTE["ink"])
    ax_c.axhline(d["gate_cvrmse_pct"], color=PALETTE["gate"], linestyle="--", linewidth=1.5)
    ax_c.text(
        len(rows) - 0.5, d["gate_cvrmse_pct"] + 0.3, f"gate {d['gate_cvrmse_pct']:.0f}%",
        ha="right", va="bottom", fontsize=9, color=PALETTE["ink_muted"],
    )
    ax_c.set_xticks(x)
    ax_c.set_xticklabels(labels, fontsize=8.8)
    ax_c.set_ylabel("CV(RMSE) (%)")
    ax_c.set_ylim(0, d["gate_cvrmse_pct"] * 1.35)
    ax_c.spines[["top", "right"]].set_visible(False)
    ax_c.set_title("Scatter vs 15% gate", fontsize=10.5, color=PALETTE["ink"])

    # shared legend (cell kind), placed below both panels
    from matplotlib.patches import Patch
    legend_handles = [
        Patch(facecolor=PALETTE["pass"], alpha=1.0, label="real-city GATE / robustness (PASS)"),
        Patch(facecolor=PALETTE["pass"], alpha=0.55, label="synthetic context (PASS)"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.06))

    fig.suptitle(
        "Phase B — downstream-EUI aggregate bias, real cities: unbiased in the mean (both gates PASS)",
        fontsize=12.5, color=PALETTE["ink"], y=1.03,
    )
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# T04 — phaseC_quant_leaderboard.png (broken-axis method leaderboard)
# ---------------------------------------------------------------------------
def build_phaseC_leaderboard() -> plt.Figure:
    """Broken-axis year_built MAE leaderboard (near 0-40, far 800-1250 for the
    mice/linear catastrophic bars) + a small companion levels-MAE subplot.
    """
    _style()
    d = DATA["C"]
    m = d["year_built_methods"]
    phaseA_mae = m["Phase-A"]["mae"]

    # bottom -> top render order (barh: index 0 is bottom)
    order = ["linear", "mice", "rf", "missforest", "histgbm", "knn"]
    values = {
        "linear": m["linear"]["mae"],
        "mice": m["mice"]["mae"],
        "rf": m["rf"]["mae"],
        "missforest": m["missforest"]["mae"],
        "histgbm": phaseA_mae,  # DATA: histgbm "= Phase-A (below floor -> falls back)"
        "knn": m["knn"]["mae"],
    }
    colors = {
        "linear": PALETTE["fail"],
        "mice": PALETTE["fail"],
        "rf": PALETTE["categorical"][4],
        "missforest": PALETTE["categorical"][2],
        "histgbm": PALETTE["before"],
        "knn": PALETTE["after"],
    }
    y = list(range(len(order)))

    fig = plt.figure(figsize=(17, 6.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[2.3, 1.05, 1.35], wspace=0.10)
    ax_near = fig.add_subplot(gs[0, 0])
    ax_far = fig.add_subplot(gs[0, 1], sharey=ax_near)
    ax_lvl = fig.add_subplot(gs[0, 2])

    near_xlim = (0, 40)
    far_xlim = (800, 1250)

    for ax in (ax_near, ax_far):
        widths = [values[k] for k in order]
        bar_colors = [colors[k] for k in order]
        ax.barh(y, widths, height=0.58, color=bar_colors)

    ax_near.set_xlim(*near_xlim)
    ax_far.set_xlim(*far_xlim)
    # extra headroom above the top (knn) bar so the reference-line label sits
    # inside the data area, below the matplotlib-managed title band above it.
    ax_near.set_ylim(-0.7, len(order) + 0.85)

    # reference line: Phase-A baseline (near-axis range only)
    ax_near.axvline(phaseA_mae, color=PALETTE["gate"], linestyle="--", linewidth=1.5)
    ax_near.text(
        phaseA_mae, len(order) + 0.35, f"Phase-A ref {phaseA_mae:.2f}",
        ha="center", va="bottom", fontsize=8.3, color=PALETTE["ink_muted"],
    )

    # near-axis direct value labels (knn, histgbm, missforest, rf)
    for k in ("knn", "histgbm", "missforest", "rf"):
        yi = order.index(k)
        v = values[k]
        ax_near.text(v + 0.6, yi, f"{v:.2f}", ha="left", va="center", fontsize=9, color=PALETTE["ink"])

    # far-axis direct value labels (mice, linear)
    for k in ("mice", "linear"):
        yi = order.index(k)
        v = values[k]
        ax_far.text(v + 8, yi, f"{v:.0f}", ha="left", va="center", fontsize=9.5, color=PALETTE["ink"], fontweight="bold")

    ax_near.set_yticks(y)
    ax_near.set_yticklabels(
        [f"{'knn (winner)' if k == 'knn' else k}" for k in order], fontsize=9.5
    )
    ax_far.tick_params(labelleft=False, left=False)
    ax_near.set_xlabel("year_built MAE (years)")
    ax_far.set_xlabel("year_built MAE (years)")
    ax_near.spines[["top", "right"]].set_visible(False)
    ax_far.spines[["top", "left"]].set_visible(False)

    # fallback annotation (knn's win is already conveyed by the "(winner)"
    # tick label + blue highlight, so no extra arrow callout is needed here —
    # avoids crowding the reference-line label above it).
    ax_near.text(
        values["histgbm"] + 0.6, order.index("histgbm") - 0.42,
        "below floor -> falls back (=Phase-A)", fontsize=7.3, color=PALETTE["ink_muted"], ha="left",
    )

    # diagonal break marks between the two axes
    d_mark = 0.02
    kw = dict(transform=ax_near.transAxes, color=PALETTE["ink_muted"], clip_on=False, linewidth=1)
    ax_near.plot((1 - d_mark, 1 + d_mark), (-d_mark, +d_mark), **kw)
    ax_near.plot((1 - d_mark, 1 + d_mark), (1 - d_mark, 1 + d_mark), **kw)
    kw2 = dict(transform=ax_far.transAxes, color=PALETTE["ink_muted"], clip_on=False, linewidth=1)
    ax_far.plot((-d_mark, +d_mark), (-d_mark, +d_mark), **kw2)
    ax_far.plot((-d_mark, +d_mark), (1 - d_mark, 1 + d_mark), **kw2)

    # footgun annotation, far axis — centered in the empty upper region (rows
    # for knn/histgbm/missforest/rf have no bar mass on this axis) so its box
    # stays clear of both the near/far break and the ax_lvl companion panel.
    far_mid = (far_xlim[0] + far_xlim[1]) / 2
    ax_far.text(
        far_mid, 3.4,
        "AD 5000+ extrapolation\n(MAE 903-1161); stamped\nML_*_HIGH on 100%",
        ha="center", va="center", fontsize=8, color=PALETTE["fail"], fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", facecolor=PALETTE["surface"], edgecolor=PALETTE["fail"], linewidth=1.2),
    )

    ax_near.set_title(f"year_built MAE, n_holdout={d['year_built_n_holdout']}", fontsize=10.5, color=PALETTE["ink"])

    # ---- companion: levels MAE ----
    lvl = d["levels_methods"]
    lvl_order = ["Phase-A", "knn"]
    lvl_vals = [lvl["Phase-A"]["mae"], lvl["knn"]["mae"]]
    lvl_colors = [PALETTE["before"], PALETTE["after"]]
    y2 = list(range(len(lvl_order)))
    ax_lvl.barh(y2, lvl_vals, height=0.5, color=lvl_colors)
    for yi, v in zip(y2, lvl_vals):
        ax_lvl.text(v + 0.15, yi, f"{v:.2f}", ha="left", va="center", fontsize=9.5, color=PALETTE["ink"])
    ax_lvl.set_yticks(y2)
    ax_lvl.set_yticklabels(["Phase-A", f"knn (fires {lvl['knn']['fires_n']}/{d['levels_n_holdout']})"], fontsize=9)
    ax_lvl.set_xlim(0, max(lvl_vals) * 1.5)
    ax_lvl.set_xlabel("levels MAE")
    ax_lvl.spines[["top", "right"]].set_visible(False)
    ax_lvl.set_title(f"levels MAE, n_holdout={d['levels_n_holdout']}", fontsize=10.5, color=PALETTE["ink"])

    fig.suptitle(
        "Phase C — attribute-recovery leaderboard: knn wins marginally, mice/linear extrapolate catastrophically",
        fontsize=12.5, color=PALETTE["ink"], y=1.04,
    )
    return fig


# ---------------------------------------------------------------------------
# T04 — phaseC_quant_eui_beforeafter.png (EUI do-no-harm dumbbell + verdict chips)
# ---------------------------------------------------------------------------
def build_phaseC_eui_beforeafter() -> plt.Figure:
    """Dumbbell 149.87 -> 141.61 kWh/m2 (FAIL color) + two verdict chips
    (NMBE -5.51% FAIL / CV(RMSE) 7.93% PASS).
    """
    _style()
    d = DATA["C"]

    fig, (ax_db, ax_chip) = plt.subplots(1, 2, figsize=(14, 4.6), gridspec_kw={"width_ratios": [2.1, 1]})

    before = d["eui_mean_before"]
    after = d["eui_mean_after"]
    ax_db.scatter([before], [0], s=140, color=PALETTE["before"], zorder=3, label="before (Phase-A imputed)")
    ax_db.scatter([after], [0], s=140, color=PALETTE["fail"], zorder=3, label="after (Phase-C knn imputed)")
    ax_db.annotate(
        "", xy=(after, 0), xytext=(before, 0),
        arrowprops=dict(arrowstyle="-|>", color=PALETTE["fail"], lw=2.2), zorder=2,
    )
    ax_db.text(before, 0.12, f"{before:.2f} kWh/m²", ha="center", va="bottom", fontsize=10, color=PALETTE["ink_secondary"])
    ax_db.text(after, -0.16, f"{after:.2f} kWh/m²", ha="center", va="top", fontsize=10, color=PALETTE["fail"], fontweight="bold")
    ax_db.text(
        (before + after) / 2, 0.38,
        f"{d['eui_buildings_moved_down']}/{d['eui_n_buildings']} buildings ↓ — one-directional bias\n"
        f"median Δ {d['eui_delta_pct_median']:.2f}%, min {d['eui_delta_pct_min']:.2f}%",
        ha="center", va="bottom", fontsize=9.3, color=PALETTE["fail"], linespacing=1.4,
    )
    ax_db.set_xlim(after - 6, before + 6)
    ax_db.set_ylim(-0.6, 0.9)
    ax_db.set_yticks([])
    ax_db.spines[["top", "right", "left"]].set_visible(False)
    ax_db.set_xlabel("mean EUI, nyc_centre gate cell (kWh/m²)")
    ax_db.set_title(
        f"{d['eui_n_buildings']} buildings, real cluster A/B — all shift downward",
        fontsize=10.5, color=PALETTE["ink"],
    )
    ax_db.legend(loc="lower center", bbox_to_anchor=(0.5, -0.32), ncol=2, frameon=False, fontsize=8.8)

    # ---- verdict chips ----
    ax_chip.axis("off")
    ax_chip.set_xlim(0, 1)
    ax_chip.set_ylim(0, 1)
    chips = [
        (f"NMBE {d['eui_nmbe']:.2f}%", f"gate |NMBE| < {d['eui_nmbe_gate']:.0f}%", d["eui_nmbe_verdict"], PALETTE["fail"]),
        (f"CV(RMSE) {d['eui_cvrmse']:.2f}%", f"gate < {d['eui_cvrmse_gate']:.0f}%", d["eui_cvrmse_verdict"], PALETTE["pass"]),
    ]
    for (value, gate, verdict, color), y in zip(chips, (0.74, 0.26)):
        ax_chip.add_patch(plt.Rectangle(
            (0.05, y - 0.19), 0.9, 0.38, transform=ax_chip.transAxes,
            facecolor=PALETTE["surface"], edgecolor=color, linewidth=2, joinstyle="round",
        ))
        ax_chip.text(0.5, y + 0.09, value, ha="center", va="center", fontsize=14, fontweight="bold", color=PALETTE["ink"])
        ax_chip.text(0.5, y - 0.03, gate, ha="center", va="center", fontsize=8.5, color=PALETTE["ink_muted"])
        ax_chip.text(0.5, y - 0.13, verdict, ha="center", va="center", fontsize=10.5, fontweight="bold", color=color)
    ax_chip.set_title("do-no-harm gate", fontsize=10.5, color=PALETTE["ink"])

    fig.suptitle(
        "Phase C — EUI do-no-harm: a systematic downward bias, not scatter",
        fontsize=12.5, color=PALETTE["ink"], y=1.03,
    )
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# T05 — phaseD_quant_fillrate.png
# ---------------------------------------------------------------------------
def build_phaseD_fillrate() -> plt.Figure:
    """Horizontal fill-rate bars, sequential blue ramp by magnitude, each bar
    carrying its printed reason; footer chips with the LIVE_SMOKE context.
    """
    _style()
    d = DATA["D"]
    attrs = ["height_m", "levels", "use_class", "year_built"]
    seq = PALETTE["sequential"]

    fig, ax = plt.subplots(figsize=(14, 6.4))
    y = list(range(len(attrs)))[::-1]  # height_m on top
    for yi, attr in zip(y, attrs):
        pct = d["fill_rates"][attr]["pct"]
        reason = d["fill_rates"][attr]["reason"]
        # magnitude -> sequential ramp bucket (0% always lightest, 87.6% darkest)
        color = seq[-1] if pct >= 50 else (seq[1] if pct > 0 else seq[0])
        bar_len = max(pct, 1.2)  # near-zero bars keep a visible sliver
        ax.barh(yi, bar_len, height=0.5, color=color, edgecolor=PALETTE["axis"], linewidth=0.6)
        ax.text(bar_len + 2, yi, f"{pct:.1f}%", va="center", ha="left", fontsize=10.5, color=PALETTE["ink"], fontweight="bold")
        ax.text(bar_len + 14, yi, reason, va="center", ha="left", fontsize=8, color=PALETTE["ink_secondary"], linespacing=1.35)

    ax.set_yticks(y)
    ax.set_yticklabels(attrs, fontsize=10.5)
    ax.set_xlim(0, 150)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("fill rate (%)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(
        f"Phase D — fusion fill rate per attribute, {d['n_buildings']:,} {d['cell']} buildings "
        f"(Overture {d['release']})",
        fontsize=12, color=PALETTE["ink"],
    )

    footer = (
        f"{d['n_buildings']:,} buildings  ·  Overture {d['release']}  ·  "
        f"gate {d['gate_pass']}/{d['gate_fail']}  ·  byte-identical without a source  ·  "
        f"{d['license']} {d['license_size_kb']} KB"
    )
    fig.text(0.5, -0.02, footer, ha="center", va="top", fontsize=9, color=PALETTE["ink_muted"])
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# T06 — phaseE_quant_scalegap.png
# ---------------------------------------------------------------------------
def build_phaseE_scalegap() -> plt.Figure:
    """Log-scale dataset-size number line: OpenUBEM band vs method break-evens,
    plus a compact verdict strip.
    """
    _style()
    d = DATA["E"]

    fig, (ax_line, ax_chips) = plt.subplots(
        2, 1, figsize=(15, 5.6), gridspec_kw={"height_ratios": [3, 1]},
    )

    ax_line.set_xscale("log")
    ax_line.set_xlim(1e2, 1e7)
    ax_line.set_ylim(-1.1, 1.4)
    ax_line.axhline(0, color=PALETTE["axis"], linewidth=1.2, zorder=1)
    ax_line.set_yticks([])

    lo, hi = d["openubem_cell_size_range"]
    ax_line.axvspan(lo, hi, color=PALETTE["after"], alpha=0.16, zorder=0)
    ax_line.text(
        (lo * hi) ** 0.5, 1.05, "OpenUBEM cells\n(hundreds-low-thousands)\nwe live here",
        ha="center", va="bottom", fontsize=8.8, color=PALETTE["after"], fontweight="bold", linespacing=1.3,
    )

    classical_n = d["classical_dominates_below_n"]
    ax_line.annotate(
        "", xy=(classical_n, 0.42), xytext=(1e2, 0.42),
        arrowprops=dict(arrowstyle="<-", color=PALETTE["categorical"][1], lw=1.6),
    )
    ax_line.text(
        classical_n, 0.5, f"classical MissForest/MICE dominate below n≈{classical_n:,.0f}",
        ha="right", va="bottom", fontsize=8.5, color=PALETTE["categorical"][1],
    )

    tdlo, tdhi = d["tabddpm_wins_above_n"]
    ax_line.annotate(
        "", xy=(1e7, -0.42), xytext=(tdlo, -0.42),
        arrowprops=dict(arrowstyle="->", color=PALETTE["categorical"][2], lw=1.6),
    )
    ax_line.text(
        tdlo, -0.5, f"TabDDPM wins n>{tdlo:,.0f}-{tdhi:,.0f}",
        ha="left", va="top", fontsize=8.5, color=PALETTE["categorical"][2],
    )

    gain_n = d["gain_needs_above_n"]
    ax_line.annotate(
        "", xy=(1e7, -0.85), xytext=(gain_n, -0.85),
        arrowprops=dict(arrowstyle="->", color=PALETTE["categorical"][5], lw=1.6),
    )
    ax_line.text(
        gain_n, -0.93, f"GAIN needs n>{gain_n:,.0f}",
        ha="left", va="top", fontsize=8.5, color=PALETTE["categorical"][5],
    )

    precedent_n = d["ubem_deep_precedent_n"]
    ax_line.scatter([precedent_n], [0], marker="D", s=90, color=PALETTE["categorical"][4], zorder=4)
    ax_line.text(
        precedent_n, 0.18, f"UBEM deep precedent\n(Sinha 2026)\n~{precedent_n / 1e6:.1f}M ResStock",
        ha="center", va="bottom", fontsize=8.3, color=PALETTE["categorical"][4], linespacing=1.3,
    )

    ax_line.set_xlabel("dataset size (buildings, log scale)")
    ax_line.spines[["top", "right", "left"]].set_visible(False)
    ax_line.set_title(
        "Phase E — where deep imputation earns its keep vs. where OpenUBEM lives",
        fontsize=12, color=PALETTE["ink"],
    )

    # ---- verdict strip ----
    ax_chips.axis("off")
    ax_chips.set_xlim(0, 1)
    ax_chips.set_ylim(0, 1)
    verdict_colors = {
        "SKIP": PALETTE["warning"],
        "REJECT": PALETTE["fail"],
        "FIRM DISQUALIFICATION": PALETTE["fail"],
        "NOT READY": PALETTE["warning"],
    }
    families = list(d["verdicts"].items())
    n = len(families)
    xs = [ (i + 0.5) / n for i in range(n)]
    for (family, verdict), x in zip(families, xs):
        color = verdict_colors[verdict]
        ax_chips.add_patch(plt.Rectangle(
            (x - 0.115, 0.15), 0.23, 0.7, transform=ax_chips.transAxes,
            facecolor=PALETTE["surface"], edgecolor=color, linewidth=2,
        ))
        ax_chips.text(x, 0.58, family, ha="center", va="center", fontsize=9, color=PALETTE["ink"], fontweight="bold")
        ax_chips.text(x, 0.32, verdict, ha="center", va="center", fontsize=8, color=color, fontweight="bold")

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# T07 — arc_quant_summary.png
# ---------------------------------------------------------------------------
_ARC_CHIP_LABELS = {"A": "PASS", "B": "PASS", "C": "OFF", "D": "SHIP", "E": "RULED-OUT"}
_ARC_CHIP_COLOR_BY_STATUS = {"PASS": "pass", "OFF": "warning", "RULED_OUT": "ink_muted"}


def build_arc_summary() -> plt.Figure:
    """5-column storyboard A->E: one headline + PASS/SHIP/OFF/RULED-OUT chip
    per phase, reading safe -> accurate -> tested -> shipped -> ruled-out.
    """
    _style()
    phases = DATA["ARC"]["phases"]

    fig, axes = plt.subplots(1, len(phases), figsize=(18, 5.4))
    for ax, entry in zip(axes, phases):
        phase = entry["phase"]
        status = entry["status"]
        chip_label = _ARC_CHIP_LABELS[phase]
        color_key = _ARC_CHIP_COLOR_BY_STATUS[status]
        color = PALETTE[color_key]

        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.text(0.5, 0.92, phase, ha="center", va="top", fontsize=26, fontweight="bold", color=PALETTE["ink"])
        ax.text(
            0.5, 0.62, entry["headline"], ha="center", va="center", fontsize=9.3,
            color=PALETTE["ink_secondary"], linespacing=1.6,
        )
        ax.add_patch(plt.Rectangle(
            (0.14, 0.03), 0.72, 0.16, transform=ax.transAxes,
            facecolor=PALETTE["surface"], edgecolor=color, linewidth=2,
        ))
        ax.text(0.5, 0.11, chip_label, ha="center", va="center", fontsize=11, fontweight="bold", color=color)

    fig.suptitle("Input-imputation arc — quantitative summary", fontsize=14, color=PALETTE["ink"], y=1.05)
    fig.text(
        0.5, 0.99, "safe  →  unbiased  →  tested  →  shipped  →  ruled-out",
        ha="center", va="top", fontsize=10, color=PALETTE["ink_muted"],
    )
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# main — writes all 7 PNGs to the §3 paths.
# ---------------------------------------------------------------------------
def main() -> list[Path]:
    written: list[Path] = []
    written.append(_save(build_phaseA_provenance(), RESULTS_DIR / "phase_A" / "phaseA_quant_provenance.png"))
    written.append(_save(build_phaseB_accuracy(), RESULTS_DIR / "phase_B" / "phaseB_quant_accuracy.png"))
    written.append(_save(build_phaseC_leaderboard(), RESULTS_DIR / "phase_C" / "phaseC_quant_leaderboard.png"))
    written.append(_save(build_phaseC_eui_beforeafter(), RESULTS_DIR / "phase_C" / "phaseC_quant_eui_beforeafter.png"))
    written.append(_save(build_phaseD_fillrate(), RESULTS_DIR / "phase_D" / "phaseD_quant_fillrate.png"))
    written.append(_save(build_phaseE_scalegap(), RESULTS_DIR / "phase_E" / "phaseE_quant_scalegap.png"))
    written.append(_save(build_arc_summary(), RESULTS_DIR / "arc_quant_summary.png"))
    return written


if __name__ == "__main__":
    for p in main():
        print(f"wrote {p}")
