"""T11.6 CP-3 before/after compare: committed phaseE baseline vs phaseE_er33 (E-R3-3 classifier fix).

Read-only. Does NOT touch the committed baseline, does NOT write REPORT_phaseE_final.md.
Mirrors the loading/scoring idiom of scripts/validation/phaseE_rescore.py.

Usage:
    py -3 scratchpad/cp3_before_after_compare.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from openubem.results import compute_validation_gates

_BEFORE_DIR = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
_AFTER_DIR  = ROOT / "docs" / "validations" / "overAll" / "results" / "phaseE_er33"
_CBECS_DIR  = ROOT / "inputs" / "reports"

_CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre",  "la_urban",  "la_suburban",  "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]

_CITY_CBECS = {
    "nyc":    _CBECS_DIR / "cbecs_2018_middle_atlantic_eui.csv",
    "la":     _CBECS_DIR / "cbecs_2018_pacific_eui.csv",
    "austin": _CBECS_DIR / "cbecs_2018_west_south_central_eui.csv",
}

_CITY_MEASURED = {"nyc": 219.2, "la": 113.6, "austin": 162.0}

_SUCCESS_STATUSES = {"success", "success_cached", "success_csv_fallback"}

_OFFICE_ARCH = ["SmallOffice", "MediumOffice", "LargeOffice"]


def _load_cells(base_dir: Path) -> pd.DataFrame:
    missing, frames = [], []
    for cell in _CELLS:
        csv = base_dir / cell / "05_results.csv"
        if not csv.exists():
            missing.append(cell)
            continue
        df = pd.read_csv(csv, dtype={"osm_id": str})
        city, density = cell.split("_", 1)
        df["cell"] = cell
        df["city"] = city
        df["density"] = density
        frames.append(df)
    if missing:
        raise FileNotFoundError(f"Missing 05_results.csv for cells: {missing}")
    combined = pd.concat(frames, ignore_index=True)
    assert combined["cell"].nunique() == 12, f"Expected 12 cells, got {combined['cell'].nunique()}"
    return combined


def city_overall_median(df: pd.DataFrame) -> dict[str, dict]:
    success = df[df["simulation_status"].isin(_SUCCESS_STATUSES)].copy()
    out = {}
    for city in ("nyc", "la", "austin"):
        city_df = success[success["city"] == city]
        overall = city_df[city_df["archetype_id"] != "OpenUBEMUnknown"]
        med = float(overall["total_eui_kwh_m2"].median())
        measured = _CITY_MEASURED[city]
        out[city] = {
            "n": len(overall),
            "median_eui": round(med, 1),
            "measured": measured,
            "delta_pct": round((med - measured) / measured * 100, 1),
        }
    return out


def cbecs_gates_all_cities(df: pd.DataFrame) -> dict[str, dict]:
    success = df[df["simulation_status"].isin(_SUCCESS_STATUSES)].copy()
    out = {}
    for city, cbecs_path in _CITY_CBECS.items():
        city_df = success[success["city"] == city].copy()
        city_df["eui_kwh_m2"] = city_df["total_eui_kwh_m2"]
        ref = pd.read_csv(cbecs_path)
        out[city] = compute_validation_gates(city_df, reference_table=ref)
    return out


def office_mix(df: pd.DataFrame) -> dict[str, int]:
    success = df[df["simulation_status"].isin(_SUCCESS_STATUSES)].copy()
    counts = success["archetype_id"].value_counts()
    return {a: int(counts.get(a, 0)) for a in _OFFICE_ARCH}


def _g(v, prec=1):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "n/a"
    return f"{v:.{prec}f}"


def main() -> None:
    print("=" * 78)
    print("T11.6 CP-3 before/after compare: phaseE (committed) vs phaseE_er33")
    print("=" * 78)

    print("\n[1] Loading BEFORE (committed phaseE baseline) ...")
    df_before = _load_cells(_BEFORE_DIR)
    n_before = len(df_before)
    n_success_before = int(df_before["simulation_status"].isin(_SUCCESS_STATUSES).sum())
    print(f"  {n_before:,} buildings total, {n_success_before:,} success ({100*n_success_before/n_before:.1f}%)")

    print("\n[2] Loading AFTER (phaseE_er33, E-R3-3 classifier fix) ...")
    df_after = _load_cells(_AFTER_DIR)
    n_after = len(df_after)
    n_success_after = int(df_after["simulation_status"].isin(_SUCCESS_STATUSES).sum())
    print(f"  {n_after:,} buildings total, {n_success_after:,} success ({100*n_success_after/n_after:.1f}%)")

    print("\n[3] City Overall median total EUI (excl. OpenUBEMUnknown) ...")
    before_med = city_overall_median(df_before)
    after_med = city_overall_median(df_after)
    print(f"{'City':<8}{'n(before)':<11}{'n(after)':<10}{'before':<9}{'after':<9}{'measured':<10}{'d%(before)':<12}{'d%(after)':<11}")
    for city in ("nyc", "la", "austin"):
        b, a = before_med[city], after_med[city]
        bd = f"{b['delta_pct']:+.1f}%"
        ad = f"{a['delta_pct']:+.1f}%"
        print(f"{city.upper():<8}{b['n']:<11}{a['n']:<10}{b['median_eui']:<9}{a['median_eui']:<9}"
              f"{b['measured']:<10}{bd:<12}{ad:<11}")

    print("\n[4] CBECS 2018 regional gates ...")
    gates_before = cbecs_gates_all_cities(df_before)
    gates_after = cbecs_gates_all_cities(df_after)
    print(f"{'City':<8}{'metric':<12}{'before':<12}{'after':<12}")
    for city in ("nyc", "la", "austin"):
        gb, ga = gates_before[city], gates_after[city]
        print(f"{city.upper():<8}{'NMBE%':<12}{_g(gb['cbecs_nmbe']):<12}{_g(ga['cbecs_nmbe']):<12}")
        print(f"{'':<8}{'R2':<12}{_g(gb['cbecs_r2'],3):<12}{_g(ga['cbecs_r2'],3):<12}")
        print(f"{'':<8}{'CV(RMSE)%':<12}{_g(gb['cbecs_cv_rmse']):<12}{_g(ga['cbecs_cv_rmse']):<12}")
        print(f"{'':<8}{'KS_D':<12}{_g(gb['cbecs_ks_d'],4):<12}{_g(ga['cbecs_ks_d'],4):<12}")

    print("\n[5] Archetype-mix shift: office down-tiering (fleet-wide, success rows) ...")
    mix_before = office_mix(df_before)
    mix_after = office_mix(df_after)
    print(f"{'Archetype':<16}{'before':<10}{'after':<10}{'delta':<10}")
    for arch in _OFFICE_ARCH:
        b, a = mix_before[arch], mix_after[arch]
        print(f"{arch:<16}{b:<10}{a:<10}{a-b:+d}")

    print("\n" + "=" * 78)
    print("CP-3 compare complete (read-only). No baseline files modified.")
    print("=" * 78)


if __name__ == "__main__":
    main()
