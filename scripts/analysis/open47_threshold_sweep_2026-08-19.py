"""OPEN-47 / T06 (PLAN_ten-items-2026-08-19.md) — sensitivity sweep of the office
size-tier thresholds against the tag-rich fixture.

OPEN-22's closure handed OPEN-47 its next measurement: the tag-rich exam scores 88.8%
fine / 100% coarse on 98 graded rows, all 11 fine errors sit inside the correct coarse
class, and the office size tier is what splits a coarse class into fine ones. This
script sweeps `_OFFICE_SMALL_MAX_M2` (2322.0) and `_OFFICE_MEDIUM_MAX_M2` (9290.0)
jointly and reports whether fine/coarse accuracy is flat (untraced provenance is
harmless) or sharply peaked at the current values (the untraced numbers are
load-bearing).

This script changes NO threshold in the shipped module and edits NO fixture. It
monkeypatches the module-level constants in-process, in a try/finally, purely to score
alternative settings; the constants are restored before the script exits, and a
restoration check is printed.

Mandatory control (must reproduce to four decimals before the sweep is trusted):
at today's values, fine top-1 = 87/98 = 0.8878 and coarse top-1 = 98/98 = 1.0000 on
tests/fixtures/labelled_archetypes_tagrich_v2.csv, matching
docs/docs_ACTIVE/openings/extra/FIX_open-22_tagrich-gate.md. If the control does not
reproduce, the script stops before sweeping — no other number in this task is
quotable.

Usage: python scripts/analysis/open47_threshold_sweep_2026-08-19.py
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

import openubem.semantic.building_classifier as bc_mod
from openubem.semantic.building_classifier import (
    BuildingClassifier,
    _INPUT_SCHEMA_COLUMNS,
    _VALID_30,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# Mirrors tests/test_building_classifier.py:1004-1008 exactly (_COARSE_CLASS_MAP is
# test-module-local, not exported by the classifier module -- reproduced here rather
# than importing from tests/, per OPEN-27's binding that this map is data, not logic).
_COARSE_CLASS_MAP: dict = {
    "MidriseApartment": "residential",
    "HighriseApartment": "residential",
    **{aid: "commercial" for aid in _VALID_30 - {"MidriseApartment", "HighriseApartment"}},
}
FIXTURE_PATH = REPO_ROOT / "tests/fixtures/labelled_archetypes_tagrich_v2.csv"
OUT_CSV = REPO_ROOT / "openubem/outputs/comparisons/open47_threshold_sweep.csv"
OUT_FIG = REPO_ROOT / "openubem/outputs/open47_threshold_sweep_surface.png"

_SMALL_BASE = bc_mod._OFFICE_SMALL_MAX_M2  # 2322.0
_MEDIUM_BASE = bc_mod._OFFICE_MEDIUM_MAX_M2  # 9290.0

FT2_TO_M2 = 0.09290304
# CBECS general size-category bin edges (EIA CBECS 2018 flipbook, p.9) bracketing the
# code's own 25,000 / 100,000 ft^2 edges: 10,000 / 25,000 / 50,000 / 100,000 / 200,000 ft^2.
_CBECS_EDGES_FT2 = [10_000, 25_000, 50_000, 100_000, 200_000]
_CBECS_EDGES_M2 = [round(e * FT2_TO_M2, 4) for e in _CBECS_EDGES_FT2]


def _reorder(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    geom_col = gdf.geometry.name
    cols = [geom_col] + [c for c in _INPUT_SCHEMA_COLUMNS if c != geom_col and c in gdf.columns]
    return gdf[cols]


def _load_fixture_gdfs() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    bos = gpd.read_file(REPO_ROOT / "tests/fixtures/boston_downtown_500m.gpkg")
    chi = gpd.read_file(REPO_ROOT / "tests/fixtures/chicago_loop_500m.gpkg")
    for gdf in (bos, chi):
        for col in ("levels", "year_built", "underground"):
            if col in gdf.columns:
                gdf[col] = gdf[col].astype("Int64")
    return _reorder(bos), _reorder(chi)


def _load_labels() -> pd.DataFrame:
    lab = pd.read_csv(FIXTURE_PATH, comment="#")
    lab["osm_id"] = lab["osm_id"].astype(str)
    return lab


def _classify_at(clf: BuildingClassifier, bos: gpd.GeoDataFrame, chi: gpd.GeoDataFrame,
                  small_max: float, medium_max: float) -> pd.DataFrame:
    bc_mod._OFFICE_SMALL_MAX_M2 = small_max
    bc_mod._OFFICE_MEDIUM_MAX_M2 = medium_max
    try:
        bos_out = clf.classify(bos)
        chi_out = clf.classify(chi)
    finally:
        bc_mod._OFFICE_SMALL_MAX_M2 = _SMALL_BASE
        bc_mod._OFFICE_MEDIUM_MAX_M2 = _MEDIUM_BASE
    results = pd.concat([
        bos_out[["osm_id", "archetype_id"]],
        chi_out[["osm_id", "archetype_id"]],
    ])
    results["osm_id"] = results["osm_id"].astype(str)
    return results


def _score(lab: pd.DataFrame, results: pd.DataFrame) -> dict:
    merged = lab.merge(results, on="osm_id", how="left")
    graded = merged[merged["expected_archetype"] != "UNDETERMINED"].copy()
    n_graded = len(graded)
    fine_match = graded["archetype_id"] == graded["expected_archetype"]
    fine_acc = fine_match.mean()

    pred_coarse = graded["archetype_id"].map(_COARSE_CLASS_MAP)
    coarse_match = pred_coarse == graded["expected_coarse_class"]
    coarse_acc = coarse_match.mean()

    return {
        "n_graded": n_graded,
        "fine_n_match": int(fine_match.sum()),
        "fine_acc": fine_acc,
        "coarse_n_match": int(coarse_match.sum()),
        "coarse_acc": coarse_acc,
        "graded": graded.assign(fine_match=fine_match.values, coarse_match=coarse_match.values),
    }


def main() -> int:
    lab = _load_labels()
    bos, chi = _load_fixture_gdfs()
    clf = BuildingClassifier()

    # ── Mandatory control ────────────────────────────────────────────────────
    print("=== Control: current thresholds (2322.0 / 9290.0) on the tag-rich fixture ===")
    base_results = _classify_at(clf, bos, chi, _SMALL_BASE, _MEDIUM_BASE)
    base_score = _score(lab, base_results)
    print(f"n_graded={base_score['n_graded']}  "
          f"fine={base_score['fine_n_match']}/{base_score['n_graded']} = {base_score['fine_acc']:.4f}  "
          f"coarse={base_score['coarse_n_match']}/{base_score['n_graded']} = {base_score['coarse_acc']:.4f}")

    control_fine_ok = base_score["n_graded"] == 98 and abs(base_score["fine_acc"] - 87 / 98) < 1e-9
    control_coarse_ok = abs(base_score["coarse_acc"] - 1.0) < 1e-9
    if not (control_fine_ok and control_coarse_ok):
        print("STOP: control did NOT reproduce 88.8% fine / 100% coarse on 98 graded rows "
              "to four decimals. Halting before the sweep -- no other number in this task "
              "is quotable.")
        return 1
    print("Control reproduces exactly: 87/98 = 0.8878 fine, 98/98 = 1.0000 coarse. Proceeding.\n")

    baseline_graded = base_score["graded"]
    baseline_errors = set(baseline_graded.loc[~baseline_graded["fine_match"], "osm_id"])
    assert len(baseline_errors) == 11, f"expected 11 baseline fine errors, found {len(baseline_errors)}"
    print(f"Baseline fine errors (11): {sorted(baseline_errors)}\n")

    # ── Grid ─────────────────────────────────────────────────────────────────
    n_pts = 25
    small_lo, small_hi = _SMALL_BASE * 0.5, _SMALL_BASE * 1.5
    medium_lo, medium_hi = _MEDIUM_BASE * 0.5, _MEDIUM_BASE * 1.5
    small_grid = sorted(set(
        [round(small_lo + i * (small_hi - small_lo) / (n_pts - 1), 4) for i in range(n_pts)]
        + _CBECS_EDGES_M2[:3]  # 10k, 25k, 50k ft^2 bracket the small edge
    ))
    medium_grid = sorted(set(
        [round(medium_lo + i * (medium_hi - medium_lo) / (n_pts - 1), 4) for i in range(n_pts)]
        + _CBECS_EDGES_M2[2:]  # 50k, 100k, 200k ft^2 bracket the medium edge
    ))
    print(f"small grid: {len(small_grid)} points in [{small_grid[0]}, {small_grid[-1]}] "
          f"(+/-50% of {_SMALL_BASE} plus CBECS 10k/25k/50k ft^2 edges)")
    print(f"medium grid: {len(medium_grid)} points in [{medium_grid[0]}, {medium_grid[-1]}] "
          f"(+/-50% of {_MEDIUM_BASE} plus CBECS 50k/100k/200k ft^2 edges)\n")

    rows = []
    n_skipped_invalid = 0
    resolved_ever: set = set()  # of the 11 baseline errors, ever fixed under some setting
    newly_broken_ever: set = set()  # previously-correct rows, ever broken under some setting
    beats_baseline = []

    for small_max in small_grid:
        for medium_max in medium_grid:
            if small_max >= medium_max:
                n_skipped_invalid += 1
                continue
            results = _classify_at(clf, bos, chi, small_max, medium_max)
            score = _score(lab, results)
            graded = score["graded"]
            errs_here = set(graded.loc[~graded["fine_match"], "osm_id"])
            resolved = baseline_errors - errs_here
            new_errs = errs_here - baseline_errors
            resolved_ever |= resolved
            newly_broken_ever |= new_errs
            rows.append({
                "small_max_m2": small_max,
                "medium_max_m2": medium_max,
                "is_baseline": small_max == _SMALL_BASE and medium_max == _MEDIUM_BASE,
                "fine_n_match": score["fine_n_match"],
                "n_graded": score["n_graded"],
                "fine_acc": score["fine_acc"],
                "coarse_n_match": score["coarse_n_match"],
                "coarse_acc": score["coarse_acc"],
                "n_baseline_errors_resolved": len(resolved),
                "n_new_errors_introduced": len(new_errs),
            })
            if score["fine_acc"] > base_score["fine_acc"] + 1e-9:
                beats_baseline.append((small_max, medium_max, score["fine_acc"]))

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV} ({len(df)} rows, {n_skipped_invalid} combos skipped for small>=medium)\n")

    # ── Restoration check ────────────────────────────────────────────────────
    restored_ok = (bc_mod._OFFICE_SMALL_MAX_M2 == _SMALL_BASE
                   and bc_mod._OFFICE_MEDIUM_MAX_M2 == _MEDIUM_BASE)
    print(f"module constants restored after sweep: {restored_ok} "
          f"(_OFFICE_SMALL_MAX_M2={bc_mod._OFFICE_SMALL_MAX_M2}, "
          f"_OFFICE_MEDIUM_MAX_M2={bc_mod._OFFICE_MEDIUM_MAX_M2})\n")

    # ── Plateau: contiguous region of grid points at fine_acc == baseline ─────
    at_baseline_acc = df[df["fine_acc"] >= base_score["fine_acc"] - 1e-9]
    print(f"grid points scoring >= baseline fine acc (0.8878): {len(at_baseline_acc)} / {len(df)} "
          f"({len(at_baseline_acc) / len(df):.1%})")
    if len(at_baseline_acc):
        print(f"  small_max range in plateau: [{at_baseline_acc['small_max_m2'].min()}, "
              f"{at_baseline_acc['small_max_m2'].max()}]")
        print(f"  medium_max range in plateau: [{at_baseline_acc['medium_max_m2'].min()}, "
              f"{at_baseline_acc['medium_max_m2'].max()}]")

    print(f"\nof the 11 baseline errors, {len(resolved_ever)} are fixed under at least one "
          f"swept setting: {sorted(resolved_ever)}")
    print(f"under at least one swept setting, {len(newly_broken_ever)} previously-correct rows "
          f"become wrong (net effect below):")
    if newly_broken_ever:
        print(f"  {sorted(newly_broken_ever)}")

    print(f"\nsettings beating baseline 88.8% fine top-1: {len(beats_baseline)}")
    if beats_baseline:
        best = max(beats_baseline, key=lambda t: t[2])
        print(f"  best: small_max={best[0]}, medium_max={best[1]}, fine_acc={best[2]:.4f}")
        for s, m, a in sorted(beats_baseline, key=lambda t: -t[2])[:10]:
            print(f"    small_max={s}  medium_max={m}  fine_acc={a:.4f}")
    else:
        print("  none -- 88.8% is the ceiling anywhere on this grid.")

    # ── Figure: accuracy surface ────────────────────────────────────────────
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        pivot = df.pivot_table(index="medium_max_m2", columns="small_max_m2", values="fine_acc")
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(
            pivot.values, aspect="auto", origin="lower", cmap="viridis",
            extent=[pivot.columns.min(), pivot.columns.max(), pivot.index.min(), pivot.index.max()],
        )
        ax.scatter([_SMALL_BASE], [_MEDIUM_BASE], marker="*", s=250, c="red",
                   label=f"current ({_SMALL_BASE}, {_MEDIUM_BASE})", zorder=5)
        for edge in _CBECS_EDGES_M2:
            ax.axvline(edge, color="white", alpha=0.25, lw=0.8, ls="--")
            ax.axhline(edge, color="white", alpha=0.25, lw=0.8, ls="--")
        ax.set_xlabel("_OFFICE_SMALL_MAX_M2")
        ax.set_ylabel("_OFFICE_MEDIUM_MAX_M2")
        ax.set_title("OPEN-47 T06: fine top-1 accuracy vs. office size-tier thresholds\n"
                      "(tests/fixtures/labelled_archetypes_tagrich_v2.csv, 98 graded rows)")
        ax.legend(loc="upper left", fontsize=8)
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label("fine top-1 accuracy")
        fig.tight_layout()
        fig.savefig(OUT_FIG, dpi=150)
        print(f"\nwrote {OUT_FIG}")
    except Exception as exc:  # pragma: no cover - figure is best-effort, not the measurement
        print(f"\nfigure not written ({exc!r}) -- CSV is the measurement of record")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
