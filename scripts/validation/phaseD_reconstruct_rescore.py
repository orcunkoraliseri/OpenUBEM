"""Phase-D service-loads re-combination + re-score (T13 / Phase-5).

W3: Phase-D total_eui_kwh_m2 = cooling+heating+lighting+equipment EXACTLY (fans excluded).
    reconstruct_frame() applies UNMODIFIED (R1) — no fans double-count.
R2: metered fans_eui_kwh_m2 NOT added to reconstructed total; reported as cross-check only.
R3: NO basis/COP transform (Phase-D is metered).
R5: Overall reported BOTH incl. and excl. food-service.
R6: OpenUBEMUnknown excluded from city-anchor scoring (handled inside build_city_table already).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.results.service_loads import reconstruct_frame, load_coefficients
from scripts.v19_rescore import CITY_ANCHORS, SEGMENT_ARCHETYPES, build_city_table, _df_to_md_table
from scripts.validation.phaseD_city_rescore import load_all_cells_phaseD, _SUCCESS_STATUSES
from scripts.validation.phaseD_national_cbecs_rescore import (
    load_region_refs,
    run_national_rescore,
    _CITY_REGION,
    _REPORTS_DIR,
)
from openubem.results import compute_validation_gates

_FOOD_ARCHETYPES = {"FullServiceRestaurant", "QuickServiceRestaurant", "SuperMarket"}

# R5: food-service excluded Overall segment label suffix
_EXCL_FOOD_SUFFIX = " (excl. food-service)"


def load_and_reconstruct() -> pd.DataFrame:
    """Load all 12 Phase-D cells + apply V16 reconstruct_frame (R1: UNMODIFIED)."""
    df = load_all_cells_phaseD()
    coeffs = load_coefficients()
    df = reconstruct_frame(df, coeffs)
    return df


def _alias_recon_for_city_table(df: pd.DataFrame) -> pd.DataFrame:
    """reconstruct_frame already writes total_eui_reconstructed_kwh_m2; build_city_table reads it."""
    return df.copy()


def run_city_rescore_reconstructed(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (table_all, table_excl_food) per R5.

    table_all:       scored on total_eui_reconstructed_kwh_m2 including food-service.
    table_excl_food: same, excluding FullServiceRestaurant/QuickServiceRestaurant/SuperMarket.
    """
    table_all = build_city_table(df)

    df_excl = df[~df["archetype_id"].isin(_FOOD_ARCHETYPES)].copy()
    table_excl = build_city_table(df_excl)

    return table_all, table_excl


def build_fans_crosscheck(df: pd.DataFrame) -> pd.DataFrame:
    """R2: per-archetype median metered fans vs vent_fans_eui_recon_kwh_m2 (success rows).

    Expected: metered PTAC fans ≪ reconstruction estimate (confirms PTAC under-captures
    continuous central fans; no double-count in the reconstructed total).
    """
    success = df[df["simulation_status"].isin(_SUCCESS_STATUSES)].copy()
    rows = []
    for arch in sorted(success["archetype_id"].unique()):
        arch_df = success[success["archetype_id"] == arch]
        n = len(arch_df)
        med_metered = arch_df["fans_eui_kwh_m2"].median()
        med_recon = arch_df["vent_fans_eui_recon_kwh_m2"].median()
        ratio = med_metered / med_recon if med_recon > 0 else float("nan")
        rows.append({
            "archetype_id":                  arch,
            "n":                             n,
            "median_metered_fans_kwh_m2":    round(med_metered, 3),
            "median_recon_vent_fans_kwh_m2": round(med_recon, 3),
            "ratio_metered_over_recon":      round(ratio, 3) if ratio == ratio else float("nan"),
        })
    return pd.DataFrame(rows)


def run_national_rescore_reconstructed(df: pd.DataFrame) -> pd.DataFrame:
    """Score total_eui_reconstructed_kwh_m2 against per-region CBECS refs."""
    success = df[df["simulation_status"].isin(_SUCCESS_STATUSES)].copy()
    region_refs = load_region_refs()

    rows = []
    for city, region in _CITY_REGION.items():
        city_df = success[success["city"] == city].copy()
        city_df["eui_kwh_m2"] = city_df["total_eui_reconstructed_kwh_m2"]
        gates = compute_validation_gates(city_df, reference_table=region_refs[region])
        rows.append({
            "city":         city,
            "region":       region,
            "n":            gates["n_sim_buildings"],
            "nmbe":         gates["cbecs_nmbe"],
            "nmbe_pass":    gates["cbecs_nmbe_pass"],
            "cv_rmse":      gates["cbecs_cv_rmse"],
            "cv_rmse_pass": gates["cbecs_cv_rmse_pass"],
            "ks_d":         gates["cbecs_ks_d"],
            "ks_d_pass":    gates["cbecs_ks_d_pass"],
            "r2":           gates["cbecs_r2"],
            "r2_pass":      gates["cbecs_r2_pass"],
            "n_excluded":   gates["n_excluded_all_gates"],
        })
    return pd.DataFrame(rows)


def _check_sanity(df: pd.DataFrame) -> dict:
    """Assertions per plan: report anomalies, do not raise."""
    success = df[df["simulation_status"].isin(_SUCCESS_STATUSES)]
    n_total = len(success)

    violations = (success["total_eui_reconstructed_kwh_m2"] < success["total_eui_kwh_m2"]).sum()
    passthrough_n = (success["archetype_mapped_to"] == "passthrough").sum()
    food_mask = success["archetype_id"].isin(_FOOD_ARCHETYPES)
    food_n = food_mask.sum()
    food_median_recon = success.loc[food_mask, "total_eui_reconstructed_kwh_m2"].median() if food_n > 0 else float("nan")
    food_above_1000 = (success.loc[food_mask, "total_eui_reconstructed_kwh_m2"] > 1000).sum() if food_n > 0 else 0

    return {
        "n_success":           n_total,
        "violations_recon_lt_raw": int(violations),
        "passthrough_n":       int(passthrough_n),
        "food_n":              int(food_n),
        "food_median_recon":   float(food_median_recon),
        "food_above_1000":     int(food_above_1000),
    }


def main() -> None:
    print("=== Phase-D + V16 Service-Loads Re-combination + Re-score ===")

    print("\n[1] Loading 12 Phase-D cells + applying reconstruct_frame (R1: UNMODIFIED)...")
    df = load_and_reconstruct()
    print(f"    Total rows: {len(df)}")
    print(f"    Cells: {df['cell'].nunique()}")

    sanity = _check_sanity(df)
    print(f"\n[SANITY] n_success: {sanity['n_success']}")
    print(f"[SANITY] (a) reconstructed < raw violations: {sanity['violations_recon_lt_raw']}")
    print(f"[SANITY] (b) passthrough buildings: {sanity['passthrough_n']}")
    print(f"[SANITY] (c) food-service n={sanity['food_n']}; "
          f"median recon EUI={sanity['food_median_recon']:.1f} kWh/m² "
          f"({'FLAG: >1000 plausibility band' if sanity['food_median_recon'] > 1000 else 'within band'}) "
          f"; n_above_1000={sanity['food_above_1000']}")

    print("\n[2] Fans cross-check (R2) — metered PTAC fans vs reconstructed vent_fans...")
    fans_df = build_fans_crosscheck(df)
    print(fans_df.to_string(index=False))

    print("\n[3] City-anchor re-score on reconstructed total (R5: incl. + excl. food-service)...")
    table_all, table_excl_food = run_city_rescore_reconstructed(df)

    print("\n--- Table E: city-anchor score on total_eui_RECONSTRUCTED (ALL archetypes) ---")
    print(table_all[["city", "segment", "n", "model_recon_median", "measured",
                      "delta_vs_measured_pct"]].to_string(index=False))

    print("\n--- Table F: city-anchor score on total_eui_RECONSTRUCTED (EXCL. food-service) ---")
    print(table_excl_food[["city", "segment", "n", "model_recon_median", "measured",
                            "delta_vs_measured_pct"]].to_string(index=False))

    print("\n[4] National CBECS re-score on reconstructed total...")
    national_df = run_national_rescore_reconstructed(df)

    print("\n--- Table G: national gates on total_eui_RECONSTRUCTED ---")
    print(national_df[["city", "region", "n", "nmbe", "nmbe_pass",
                        "cv_rmse", "cv_rmse_pass", "ks_d", "ks_d_pass",
                        "r2", "r2_pass"]].to_string(index=False))

    print("\n=== Done. STOP at CP-6 — manager writes verdict. ===")


if __name__ == "__main__":
    main()
