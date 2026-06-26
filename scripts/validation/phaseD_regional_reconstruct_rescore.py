"""Phase-D2 regional-fraction re-score: national vs regional reconstruction (T05).

DD7: with OPENUBEM_PHASED_SUBDIR=phaseD2, score the 12 cells TWICE — national
fractions (current adopted) and DD3b regional fractions — head-to-head on the same
gpkgs.  Emits city anchors (all segments, 3 cities) + national CBECS gates
(NMBE/CV/KS/R² per region) for both.

Reporting-layer only: no resim, no IDF/DESIGN edit.  The reconstructed total is the
only quantity that changes between the two passes (regional mf_adj differs from
national mf_t4 for CBECS-covered groups).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.results import compute_validation_gates
from openubem.results.service_loads import load_coefficients, reconstruct_frame
from scripts.v19_rescore import build_city_table
from scripts.validation.phaseD_city_rescore import load_all_cells_phaseD, _SUCCESS_STATUSES
from scripts.validation.phaseD_national_cbecs_rescore import load_region_refs, _CITY_REGION

_TABLE4_JSON = ROOT / "openubem" / "data" / "service_loads" / "enduse_fractions_table4.json"
_REGIONAL_JSON = ROOT / "openubem" / "data" / "service_loads" / "enduse_fractions_regional.json"

_FOOD_ARCHETYPES = {"FullServiceRestaurant", "QuickServiceRestaurant", "SuperMarket"}


def _reconstruct(df: pd.DataFrame, coeffs: dict) -> pd.DataFrame:
    """reconstruct_frame derives per-row region from the 'city' column (national coeffs → national)."""
    return reconstruct_frame(df, coeffs)


def _city_tables(df_recon: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(all archetypes, excl. food-service) city-anchor tables on reconstructed total."""
    table_all = build_city_table(df_recon)
    df_excl = df_recon[~df_recon["archetype_id"].isin(_FOOD_ARCHETYPES)].copy()
    table_excl = build_city_table(df_excl)
    return table_all, table_excl


def _national_gates(df_recon: pd.DataFrame) -> pd.DataFrame:
    """National CBECS gates per region on total_eui_reconstructed_kwh_m2."""
    success = df_recon[df_recon["simulation_status"].isin(_SUCCESS_STATUSES)].copy()
    region_refs = load_region_refs()
    rows = []
    for city, region in _CITY_REGION.items():
        city_df = success[success["city"] == city].copy()
        city_df["eui_kwh_m2"] = city_df["total_eui_reconstructed_kwh_m2"]
        gates = compute_validation_gates(city_df, reference_table=region_refs[region])
        rows.append({
            "city": city, "region": region,
            "n": gates["n_sim_buildings"],
            "nmbe": gates["cbecs_nmbe"], "nmbe_pass": gates["cbecs_nmbe_pass"],
            "cv_rmse": gates["cbecs_cv_rmse"], "cv_rmse_pass": gates["cbecs_cv_rmse_pass"],
            "ks_d": gates["cbecs_ks_d"], "ks_d_pass": gates["cbecs_ks_d_pass"],
            "r2": gates["cbecs_r2"], "r2_pass": gates["cbecs_r2_pass"],
        })
    return pd.DataFrame(rows)


def _office_modeled_frac(coeffs: dict) -> dict:
    """Per-region large_office modeled_frac (sanity: regional ≠ national)."""
    keys = ("space_heat", "space_cool", "lighting", "equip_plug")
    nat = sum(coeffs["fractions"]["large_office"][k] for k in keys)
    out = {"national": round(nat, 4)}
    for region, groups in coeffs.get("fractions_by_region", {}).items():
        if "large_office" in groups:
            out[region] = round(sum(groups["large_office"][k] for k in keys), 4)
    return out


def main() -> dict:
    print("=== Phase-D2 Regional-Fraction Re-score (national vs regional) ===")

    df = load_all_cells_phaseD()
    n_success = df["simulation_status"].isin(_SUCCESS_STATUSES).sum()
    print(f"Loaded {len(df)} rows across {df['cell'].nunique()} cells; success={n_success}")

    coeffs_nat = load_coefficients(_TABLE4_JSON)
    coeffs_reg = load_coefficients(_REGIONAL_JSON)

    print("\nlarge_office modeled_frac:", _office_modeled_frac(coeffs_reg))

    df_nat = _reconstruct(df, coeffs_nat)
    df_reg = _reconstruct(df, coeffs_reg)

    # sanity: reconstructed >= raw both passes; deltas finite
    for label, d in (("national", df_nat), ("regional", df_reg)):
        s = d[d["simulation_status"].isin(_SUCCESS_STATUSES)]
        viol = (s["total_eui_reconstructed_kwh_m2"] < s["total_eui_kwh_m2"]).sum()
        finite = s["total_eui_reconstructed_kwh_m2"].notna().all()
        regional_applied = (d["reconstruction_basis"] == "regional_fraction_split").sum()
        print(f"[{label}] success={len(s)}, recon<raw violations={viol}, "
              f"all finite={finite}, regional_basis_rows={regional_applied}")

    city_all_nat, city_excl_nat = _city_tables(df_nat)
    city_all_reg, city_excl_reg = _city_tables(df_reg)
    nat_gates_nat = _national_gates(df_nat)
    nat_gates_reg = _national_gates(df_reg)

    print("\n--- City anchors (ALL archetypes) — NATIONAL fractions ---")
    print(city_all_nat[["city", "segment", "n", "model_recon_median", "measured",
                        "delta_vs_measured_pct"]].to_string(index=False))
    print("\n--- City anchors (ALL archetypes) — REGIONAL fractions ---")
    print(city_all_reg[["city", "segment", "n", "model_recon_median", "measured",
                        "delta_vs_measured_pct"]].to_string(index=False))

    print("\n--- National CBECS gates — NATIONAL fractions ---")
    print(nat_gates_nat[["city", "region", "n", "nmbe", "nmbe_pass",
                        "cv_rmse", "ks_d", "r2"]].to_string(index=False))
    print("\n--- National CBECS gates — REGIONAL fractions ---")
    print(nat_gates_reg[["city", "region", "n", "nmbe", "nmbe_pass",
                        "cv_rmse", "ks_d", "r2"]].to_string(index=False))

    return {
        "city_all_nat": city_all_nat, "city_all_reg": city_all_reg,
        "city_excl_nat": city_excl_nat, "city_excl_reg": city_excl_reg,
        "nat_gates_nat": nat_gates_nat, "nat_gates_reg": nat_gates_reg,
        "office_mf": _office_modeled_frac(coeffs_reg),
    }


if __name__ == "__main__":
    main()
