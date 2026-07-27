"""T13 — Cross-mode comparison figures for the layoutAssigner post-closure addendum.

Builds figures + 1 summary CSV from data that already exists (no new EnergyPlus
runs): the T10 zone-count/EUI comparison CSV, the T08 12-cell 4-mode EUI harvest,
and the cluster-leg layout_assign harvest (ACTIVE_LAYOUT_ASSIGN_EUI_CSV, currently T19).

2026-07-26: repointed from the stale T17 harvest to T19 (2 rounds of defect fixes
since T17, incl. E-LA-10 DHW scaling). T17 constants kept only for provenance.
Prior T17 figures/CSV preserved in openubem/outputs/comparisons/previous/*_t17.*.

Usage:
    py -3 scripts/analysis/plot_layout_assign_vs_modes.py

Outputs (openubem/outputs/comparisons/):
    layout_assign_vs_modes_zone_fidelity.png
    layout_assign_vs_modes_eui_la.png
    layout_assign_vs_modes_severity.png        (NOT regenerated -- frozen 2026-07-23 spot-check)
    layout_assign_vs_modes_la_summary.csv
    layout_assign_vs_modes_cluster_eui.png     (only if ACTIVE_LAYOUT_ASSIGN_EUI_CSV exists)
    layout_assign_vs_modes_cluster_success.png (only if ACTIVE_LAYOUT_ASSIGN_EUI_CSV exists)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WORKSPACE_ROOT = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
COMPARISONS_DIR = WORKSPACE_ROOT / "openubem" / "outputs" / "comparisons"

ZONE_CSV = COMPARISONS_DIR / "layout_assign_vs_resolution_modes.csv"
ALL_MODES_EUI_CSV = COMPARISONS_DIR / "t08_all_modes_eui.csv"
LOCAL_REMAINDER_EUI_CSV = COMPARISONS_DIR / "t08_local_remainder_eui.csv"
# T17 (cluster leg, 2026-07-23): first real fleet-scale layout_assign harvest. Kept only
# for provenance/history -- superseded below, not read by any plot function anymore.
T17_LAYOUT_ASSIGN_EUI_CSV = COMPARISONS_DIR / "t17_layout_assign_eui.csv"
# T19 (2026-07-26): re-harvest after 2 rounds of defect fixes (T18: E-LA-10 DHW scaling
# + others; T19: further fixes). This is the ACTIVE source for all layout_assign figures
# below. Still pre-E-LA-20 (fixed 2026-07-25, never re-run at fleet scale) -- see the
# nyc_rural/SmallOffice caveat baked into plot_cluster_success().
T19_LAYOUT_ASSIGN_EUI_CSV = COMPARISONS_DIR / "t19_layout_assign_eui.csv"
ACTIVE_LAYOUT_ASSIGN_EUI_CSV = T19_LAYOUT_ASSIGN_EUI_CSV
ACTIVE_SOURCE_LABEL = "T19"
# T18 harvest -- read only by plot_cluster_success() to split the nyc_rural/SmallOffice
# T19 failures into the E-LA-20 set (failed T19, succeeded T18) vs. pre-existing failures
# (failed at both T18 and T19, un-investigated, predate E-LA-20).
T18_LAYOUT_ASSIGN_EUI_CSV = COMPARISONS_DIR / "t18_layout_assign_eui.csv"

OUT_ZONE_FIDELITY_PNG = COMPARISONS_DIR / "layout_assign_vs_modes_zone_fidelity.png"
OUT_EUI_LA_PNG = COMPARISONS_DIR / "layout_assign_vs_modes_eui_la.png"
OUT_SEVERITY_PNG = COMPARISONS_DIR / "layout_assign_vs_modes_severity.png"
OUT_LA_SUMMARY_CSV = COMPARISONS_DIR / "layout_assign_vs_modes_la_summary.csv"
# Full 12-cell / 5-mode cluster-scale figures (only emitted when ACTIVE_LAYOUT_ASSIGN_EUI_CSV
# exists -- this script stays runnable standalone before a cluster-leg harvest exists).
ALL_MODES_EUI_CSV_T17 = COMPARISONS_DIR / "t08_all_modes_eui.csv"
LOCAL_REMAINDER_EUI_CSV_T17 = COMPARISONS_DIR / "t08_local_remainder_eui.csv"
OUT_CLUSTER_EUI_PNG = COMPARISONS_DIR / "layout_assign_vs_modes_cluster_eui.png"
OUT_CLUSTER_SUCCESS_PNG = COMPARISONS_DIR / "layout_assign_vs_modes_cluster_success.png"
ALL_CELLS_ORDER = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]

# Same tab10-family convention already used by scripts/cluster/t08_harvest_results.py's
# make_figures() (t08_mode_cell_median_eui.png) -- reused here for cross-figure consistency;
# layout_assign extends the same family (tab10 C4, purple) since it has no prior color.
MODE_COLORS = {
    "auto": "#1f77b4",
    "building": "#ff7f0e",
    "floor": "#2ca02c",
    "fast_zone": "#d62728",
    "layout_assign": "#9467bd",
}

LA_CELLS = ["la_centre", "la_urban", "la_suburban", "la_rural"]
LA_FLEET_ARCHETYPES = ["MidriseApartment", "MediumOffice", "RetailStandalone", "FullServiceRestaurant"]

# Hardcoded per plan §5 T13 -- E-LA-06 diagnostic counts, verified in plan §8 T12 / §9 E-LA-06.
# (warnings, severe) at each archetype's T12-tested scale factor. Do not re-derive by parsing logs.
E_LA_06_COUNTS = {
    "MidriseApartment": (43, 0),
    "MediumOffice": (7_676_815, 73_803),
    "SmallHotel": (120_506_937, 0),
    "SecondarySchool": (15_759_336, 28),
    "RetailStandalone": (604_188, 0),
    "FullServiceRestaurant": (1_121_627, 2),
}


def plot_zone_fidelity(zone_df: pd.DataFrame) -> None:
    cols = ["building_mode_zones", "floor_mode_zones", "fast_zone_mode_zones", "layout_assign_mode_zones"]
    labels = {"building_mode_zones": "building", "floor_mode_zones": "floor",
              "fast_zone_mode_zones": "fast_zone", "layout_assign_mode_zones": "layout_assign"}

    df = zone_df.sort_values("layout_assign_mode_zones", ascending=True).reset_index(drop=True)
    split = len(df) // 2
    low_band, high_band = df.iloc[:split], df.iloc[split:]

    fig, axes = plt.subplots(2, 1, figsize=(15, 14))
    for ax, band, title in zip(
        axes, [low_band, high_band],
        [f"Low zone-count band (n={len(low_band)} archetypes)", f"High zone-count band (n={len(high_band)} archetypes)"],
    ):
        x = np.arange(len(band))
        bar_w = 0.2
        for i, col in enumerate(cols):
            ax.bar(x + i * bar_w, band[col].values, bar_w, label=labels[col], color=MODE_COLORS[labels[col]])
        ax.set_yscale("log")
        ax.set_xticks(x + bar_w * (len(cols) - 1) / 2)
        ax.set_xticklabels(band["archetype_id"].values, rotation=45, ha="right")
        ax.set_ylabel("Zone count (log scale)")
        ax.set_title(title)
        ax.legend(ncol=4, loc="upper left")
        ax.grid(axis="y", alpha=0.3, which="both")

    fig.suptitle("Zone-count fidelity by resolution mode, all 28 mapped archetypes\n"
                  "(source: layout_assign_vs_resolution_modes.csv, T10)")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(str(OUT_ZONE_FIDELITY_PNG), dpi=120)
    plt.close(fig)
    print(f"Saved: {OUT_ZONE_FIDELITY_PNG}")


def build_la_summary(zone_df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """Returns (summary_df, using_real_fleet_data).

    If the real cluster-scale layout_assign harvest CSV (ACTIVE_LAYOUT_ASSIGN_EUI_CSV,
    T19) exists, use its LA-cell fleet median (n>1 buildings per archetype) instead of
    the T12 single-building local-leg number. Falls back to the T12 number
    (n_buildings=1) only if that CSV is absent -- keeps this script runnable
    standalone even before a cluster-leg harvest exists, per T13's original design intent.
    """
    shared = ["cell", "city", "mode", "archetype_id", "total_eui"]
    all_modes = pd.read_csv(ALL_MODES_EUI_CSV)[shared]
    local_remainder = pd.read_csv(LOCAL_REMAINDER_EUI_CSV)[shared]
    fleet = pd.concat([all_modes, local_remainder], ignore_index=True)

    la_fleet = fleet[(fleet["city"] == "LA") & (fleet["cell"].isin(LA_CELLS))
                      & (fleet["archetype_id"].isin(LA_FLEET_ARCHETYPES))]

    using_real_fleet_data = ACTIVE_LAYOUT_ASSIGN_EUI_CSV.exists()
    if using_real_fleet_data:
        active = pd.read_csv(ACTIVE_LAYOUT_ASSIGN_EUI_CSV)
        active_succ = active[active["status"] == "success"]
        active_la = active_succ[(active_succ["city"] == "LA") & (active_succ["cell"].isin(LA_CELLS))]

    rows = []
    for archetype in LA_FLEET_ARCHETYPES:
        sub = la_fleet[la_fleet["archetype_id"] == archetype]
        for mode in ["auto", "building", "floor", "fast_zone"]:
            msub = sub[sub["mode"] == mode]
            rows.append({
                "archetype_id": archetype,
                "mode": mode,
                "median_total_eui_kwh_m2": msub["total_eui"].median(),
                "n_buildings": len(msub),
            })
        if using_real_fleet_data:
            la_sub = active_la[active_la["archetype_id"] == archetype]
            rows.append({
                "archetype_id": archetype,
                "mode": "layout_assign",
                "median_total_eui_kwh_m2": la_sub["total_eui"].median() if len(la_sub) > 0 else float("nan"),
                "n_buildings": len(la_sub),
            })
        else:
            la_eui_row = zone_df.loc[zone_df["archetype_id"] == archetype, "local_leg_total_eui_kwh_m2"]
            rows.append({
                "archetype_id": archetype,
                "mode": "layout_assign",
                "median_total_eui_kwh_m2": float(la_eui_row.iloc[0]),
                "n_buildings": 1,
            })
    return pd.DataFrame(rows), using_real_fleet_data


def plot_eui_la(summary_df: pd.DataFrame, using_real_fleet_data: bool) -> None:
    fig, ax = plt.subplots(figsize=(13, 7))
    modes = ["auto", "building", "floor", "fast_zone"]
    x = np.arange(len(LA_FLEET_ARCHETYPES))
    bar_w = 0.18
    group_x = x + bar_w * (len(modes) - 1) / 2

    for i, mode in enumerate(modes):
        msub = summary_df[summary_df["mode"] == mode].set_index("archetype_id")
        vals = [msub.loc[a, "median_total_eui_kwh_m2"] for a in LA_FLEET_ARCHETYPES]
        ax.bar(x + i * bar_w, vals, bar_w, label=mode, color=MODE_COLORS[mode])

    la_vals = summary_df[summary_df["mode"] == "layout_assign"].set_index("archetype_id")
    star_y = [la_vals.loc[a, "median_total_eui_kwh_m2"] for a in LA_FLEET_ARCHETYPES]
    la_ns = [int(la_vals.loc[a, "n_buildings"]) for a in LA_FLEET_ARCHETYPES]
    la_label = (f"layout_assign (real {ACTIVE_SOURCE_LABEL} cluster-leg fleet median)" if using_real_fleet_data
                else "layout_assign (single real T12 local-leg building)")
    ax.scatter(group_x, star_y, marker="*", s=400, color=MODE_COLORS["layout_assign"],
               edgecolor="black", linewidth=0.8, zorder=5, label=la_label)

    # n annotated at each group's own local max (not a global ymax) so it never collides
    # with a taller neighbouring group (FullServiceRestaurant is ~10x the others).
    ns = [int(summary_df.loc[(summary_df["archetype_id"] == a) & (summary_df["mode"] == "auto"), "n_buildings"].iloc[0])
          for a in LA_FLEET_ARCHETYPES]
    for xi, n, a in zip(group_x, ns, LA_FLEET_ARCHETYPES):
        local_max = summary_df.loc[summary_df["archetype_id"] == a, "median_total_eui_kwh_m2"].max()
        ax.text(xi, local_max * 1.04, f"n={n}", ha="center", va="bottom", fontsize=9, color="#333333")
    if using_real_fleet_data:
        for xi, la_n, a in zip(group_x, la_ns, LA_FLEET_ARCHETYPES):
            la_y = la_vals.loc[a, "median_total_eui_kwh_m2"]
            if pd.notna(la_y):
                ax.text(xi, la_y * 1.02, f"la_n={la_n}", ha="center", va="bottom",
                        fontsize=8, color=MODE_COLORS["layout_assign"], fontweight="bold")

    ax.set_xticks(group_x)
    ax.set_xticklabels(LA_FLEET_ARCHETYPES, rotation=20, ha="right")
    ax.set_ylabel("Total EUI [kWh/m2/yr]")
    valid_star_y = [v for v in star_y if pd.notna(v)]
    ymax = max(summary_df["median_total_eui_kwh_m2"].max(), max(valid_star_y) if valid_star_y else 0) * 1.15
    ax.set_ylim(0, ymax)
    if using_real_fleet_data:
        title = (f"LA-climate fleet median EUI by mode vs. REAL layout_assign fleet median ({ACTIVE_SOURCE_LABEL} cluster leg)\n"
                 "SUPERSEDES the T13/T12 single-building comparison. SmallHotel / SecondarySchool omitted -- no LA fleet comparator (0 rows)")
    else:
        title = ("LA-climate fleet median EUI by mode vs. single real layout_assign EUI (T12 local leg)\n"
                 "SmallHotel / SecondarySchool omitted -- no LA fleet comparator (0 rows)")
    ax.set_title(title)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=9, borderaxespad=0.0)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(str(OUT_EUI_LA_PNG), dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_EUI_LA_PNG}")


def plot_cluster_eui() -> None:
    """Full 12-cell, 5-mode (incl. real layout_assign) median EUI comparison.
    Only runs if ACTIVE_LAYOUT_ASSIGN_EUI_CSV exists (the actual full-cluster leg).

    The T17-era "clean" black-diamond series (median excluding MidriseApartment/
    SmallOffice) is gone: it existed only to work around E-LA-10 (unscaled DHW flow
    rate), which is fixed as of T18/T19. Keeping it would imply a live caveat that
    no longer applies.
    """
    if not ACTIVE_LAYOUT_ASSIGN_EUI_CSV.exists():
        print(f"Skipping cluster EUI figure -- {ACTIVE_LAYOUT_ASSIGN_EUI_CSV.name} not found.")
        return

    shared = ["cell", "city", "mode", "total_eui"]
    other_modes = pd.concat([
        pd.read_csv(ALL_MODES_EUI_CSV_T17)[shared],
        pd.read_csv(LOCAL_REMAINDER_EUI_CSV_T17)[shared],
    ], ignore_index=True)
    other_med = other_modes.groupby(["cell", "mode"])["total_eui"].median().unstack()

    active = pd.read_csv(ACTIVE_LAYOUT_ASSIGN_EUI_CSV)
    active_succ = active[active["status"] == "success"]
    la_med = active_succ.groupby("cell")["total_eui"].median()

    cells = [c for c in ALL_CELLS_ORDER if c in other_med.index]
    modes = ["auto", "building", "floor", "fast_zone"]
    x = np.arange(len(cells))
    bar_w = 0.14

    fig, ax = plt.subplots(figsize=(16, 7.5))
    for i, mode in enumerate(modes):
        vals = [other_med.loc[c, mode] if c in other_med.index else np.nan for c in cells]
        ax.bar(x + i * bar_w, vals, bar_w, label=mode, color=MODE_COLORS[mode])

    la_vals = [la_med.get(c, np.nan) for c in cells]
    ax.bar(x + 4 * bar_w, la_vals, bar_w, label="layout_assign (all archetypes)",
           color=MODE_COLORS["layout_assign"])

    ax.set_xticks(x + bar_w * 2)
    ax.set_xticklabels(cells, rotation=30, ha="right")
    ax.set_ylabel("Median Total EUI [kWh/m2/yr]")
    ax.set_title(f"Full 12-cell / 8,160-building median Total EUI by resolution mode ({ACTIVE_SOURCE_LABEL} cluster leg)\n"
                 "E-LA-10 (unscaled DHW flow rate) is fixed as of this harvest -- layout_assign is no longer\n"
                 "artificially inflated by that bug. layout_assign has not been validated against measured data.")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8, borderaxespad=0.0)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(str(OUT_CLUSTER_EUI_PNG), dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_CLUSTER_EUI_PNG}")


def plot_cluster_success() -> None:
    """Per-cell success/fail counts, full cluster leg (ACTIVE_LAYOUT_ASSIGN_EUI_CSV, T19).

    T19 was harvested BEFORE the E-LA-20 fix (landed 2026-07-25, never re-run at fleet
    scale) -- it still contains the nyc_rural/SmallOffice failed rows that fix addressed,
    plus a small pre-existing population that predates E-LA-20. The two are distinguished
    below by set-difference against the T18 harvest (failed T19 + succeeded T18 == E-LA-20;
    failed at both == pre-existing, different, un-investigated cause) and called out
    explicitly in the title so nyc_rural's column here is not mistaken for current behaviour.
    """
    if not ACTIVE_LAYOUT_ASSIGN_EUI_CSV.exists():
        print(f"Skipping cluster success figure -- {ACTIVE_LAYOUT_ASSIGN_EUI_CSV.name} not found.")
        return

    active = pd.read_csv(ACTIVE_LAYOUT_ASSIGN_EUI_CSV)
    tab = active.groupby("cell")["status"].value_counts().unstack(fill_value=0)
    cells = [c for c in ALL_CELLS_ORDER if c in tab.index]
    tab = tab.loc[cells]
    succ = tab.get("success", pd.Series(0, index=cells))
    fail = tab.get("failed", pd.Series(0, index=cells))

    rural_so = active[(active["cell"] == "nyc_rural") & (active["archetype_id"] == "SmallOffice")]
    rural_so_failed_ids = set(rural_so[rural_so["status"] == "failed"]["osm_id"])
    n_rural_fatal = len(rural_so_failed_ids)
    t18 = pd.read_csv(T18_LAYOUT_ASSIGN_EUI_CSV)
    t18_rural_so_succ_ids = set(t18[(t18["cell"] == "nyc_rural") & (t18["archetype_id"] == "SmallOffice")
                                     & (t18["status"] == "success")]["osm_id"])
    n_ela20 = len(rural_so_failed_ids & t18_rural_so_succ_ids)
    n_pre_existing = n_rural_fatal - n_ela20

    fig, ax = plt.subplots(figsize=(13, 6.5))
    x = np.arange(len(cells))
    ax.bar(x, succ, color="#2ca02c", label="success")
    ax.bar(x, fail, bottom=succ, color="#d62728", label="failed")
    for xi, s, f in zip(x, succ, fail):
        total = s + f
        pct = 100 * s / total if total else 0
        ax.text(xi, total + total * 0.01, f"{pct:.0f}%", ha="center", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(cells, rotation=30, ha="right")
    ax.set_ylabel("Building count")
    ax.set_title(f"layout_assign cluster-leg success/fail by cell ({ACTIVE_SOURCE_LABEL}, 8,160 buildings total)\n"
                 f"CAVEAT: nyc_rural includes {n_rural_fatal} failed SmallOffice rows, of which {n_ela20} are E-LA-20\n"
                 f"(fixed 2026-07-25, never re-run at fleet scale) and {n_pre_existing} pre-date it (different, un-investigated cause)")
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(str(OUT_CLUSTER_SUCCESS_PNG), dpi=120)
    plt.close(fig)
    print(f"Saved: {OUT_CLUSTER_SUCCESS_PNG}")


def plot_severity() -> None:
    archetypes = list(E_LA_06_COUNTS.keys())
    totals = [sum(E_LA_06_COUNTS[a]) for a in archetypes]
    severes = [E_LA_06_COUNTS[a][1] for a in archetypes]

    fig, ax = plt.subplots(figsize=(11, 6.5))
    x = np.arange(len(archetypes))
    bars = ax.bar(x, totals, color=MODE_COLORS["layout_assign"])
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(archetypes, rotation=20, ha="right")
    ax.set_ylabel("Warnings + Severe Errors (log scale)")
    ax.set_title("E-LA-06 diagnostic-severity: total warning+severe count at T12-tested scale factor\n"
                  "(hardcoded, plan §8 T12 / §9 E-LA-06 -- not re-derived from logs)")
    ax.grid(axis="y", alpha=0.3, which="both")

    for bar, total, severe in zip(bars, totals, severes):
        ax.annotate(f"{total:,}", (bar.get_x() + bar.get_width() / 2, total), xytext=(0, 5),
                    textcoords="offset points", ha="center", fontsize=8)
        if severe > 0:
            ax.annotate(f"{severe:,} severe", (bar.get_x() + bar.get_width() / 2, total), xytext=(0, 18),
                        textcoords="offset points", ha="center", fontsize=8, color="#d62728", fontweight="bold")

    fig.tight_layout()
    fig.savefig(str(OUT_SEVERITY_PNG), dpi=120)
    plt.close(fig)
    print(f"Saved: {OUT_SEVERITY_PNG}")


def main() -> None:
    COMPARISONS_DIR.mkdir(parents=True, exist_ok=True)
    zone_df = pd.read_csv(ZONE_CSV)

    plot_zone_fidelity(zone_df)

    summary_df, using_real_fleet_data = build_la_summary(zone_df)
    summary_df.to_csv(OUT_LA_SUMMARY_CSV, index=False)
    print(f"Saved: {OUT_LA_SUMMARY_CSV}")
    print(f"Using real {ACTIVE_SOURCE_LABEL} cluster-leg fleet data for layout_assign: {using_real_fleet_data}")

    plot_eui_la(summary_df, using_real_fleet_data)
    # plot_severity() intentionally NOT called: that figure is a frozen 2026-07-23
    # 6-building spot-check (hardcoded E-LA-06 counts unrelated to T17/T19) and must
    # be left exactly as it is -- see plan decision on the T19 regeneration task.
    plot_cluster_eui()
    plot_cluster_success()


if __name__ == "__main__":
    main()
