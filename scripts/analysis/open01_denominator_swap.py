"""OPEN-01 T07 -- before/after per building, all five modes, for the denominator swap.

Read-only. No cluster access, no re-simulation (ruling 4). Every number here comes
from two artifacts already on disk:
  - openubem/outputs/comparisons/open01_denominator_audit.csv (40,800 rows, the
    E02 T04 .eio audit: area_multiplier_aware_m2, declared_area_m2, error_factor
    per (cell, mode, osm_id))
  - docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.csv
    (the adopted "auto"-mode canonical Step-5 output, the only run with real
    total_eui_kwh_m2 on disk for any of these buildings)

Because footprint_area_m2/levels (and therefore declared_area_m2) are the
building's own geometry, not simulation output, the same declared_area_m2 --
and, here, the same "auto"-mode total_eui_kwh_m2 -- is shared across all five
per-building rows in the audit (one per mode). total_eui_kwh_m2 was measured
once, under whatever area the "auto" run actually divided by (its own
declared_area_m2, error_factor ~= 1.0000 -- see below). This script asks: if
that same simulated energy had been divided by each mode's own multiplier-aware
simulated area instead, what would the EUI read?

    old_eui_kwh_m2 = total_eui_kwh_m2 (from 05_results.csv, "auto" mode)
    new_eui_kwh_m2 = old_eui_kwh_m2 / error_factor          (error_factor =
                      area_multiplier_aware_m2 / declared_area_m2, per mode)

This is an exact algebraic transform (energy is invariant; only the area it is
divided by changes) and requires no new simulation. It is NOT a claim that
non-auto modes were literally re-parsed with new code -- ruling 4 forbids that.
For "auto" itself (the adopted, published mode) error_factor sits at 1.0000
median, so new_eui ~= old_eui and the published fleet figure (157.1 kWh/m2
pooled) is unaffected; see the .md this script also writes.

Usage:
    .venv/Scripts/python.exe scripts/analysis/open01_denominator_swap.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

AUDIT_CSV = Path("openubem/outputs/comparisons/open01_denominator_audit.csv")
PHASE_E_ROOT = Path("docs/docs_VALIDATION/validations/overAll/results/phaseE")
OUT_CSV = Path("openubem/outputs/comparisons/open01_denominator_swap.csv")

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
MODES = ["auto", "building", "fast_zone", "floor", "layout_assign"]

_TARGETS = {
    "auto": (1.0000, 99.63),
    "floor": (1.0000, 98.43),
    "fast_zone": (1.0000, 94.80),
    "layout_assign": (0.9999, 15.37),
    "building": (0.5000, 39.94),
}

_DECILES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def load_auto_eui() -> pd.DataFrame:
    frames = []
    for cell in CELLS:
        path = PHASE_E_ROOT / cell / "05_results.csv"
        df = pd.read_csv(path, usecols=["osm_id", "total_eui_kwh_m2", "simulation_status"])
        df["cell"] = cell
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out = out.rename(columns={"total_eui_kwh_m2": "auto_total_eui_kwh_m2"})
    dup = out.duplicated(subset=["cell", "osm_id"]).sum()
    if dup:
        print(f"WARNING: {dup} duplicate (cell, osm_id) rows in 05_results.csv", file=sys.stderr)
    return out


def main() -> None:
    if not AUDIT_CSV.exists():
        print(f"FATAL: {AUDIT_CSV} not found -- this script only reads it, never regenerates it", file=sys.stderr)
        sys.exit(1)

    audit = pd.read_csv(AUDIT_CSV)
    n_total = len(audit)
    if n_total != 40800:
        print(f"FATAL: expected 40,800 audit rows, found {n_total}", file=sys.stderr)
        sys.exit(1)

    eui = load_auto_eui()
    df = audit.merge(eui, on=["cell", "osm_id"], how="left", indicator="_eui_merge")

    n_unmatched_modes = {}
    for mode in MODES:
        sub = df[df["mode"] == mode]
        n_unmatched_modes[mode] = int((sub["_eui_merge"] != "both").sum())
    df = df.drop(columns=["_eui_merge"])

    df["old_eui_kwh_m2"] = df["auto_total_eui_kwh_m2"]
    df["new_eui_kwh_m2"] = df["old_eui_kwh_m2"] / df["error_factor"]
    df["eui_shift_pct"] = (df["new_eui_kwh_m2"] / df["old_eui_kwh_m2"] - 1.0) * 100.0

    out_cols = [
        "cell", "mode", "osm_id", "n_zones", "area_plain_m2", "area_multiplier_aware_m2",
        "declared_area_m2", "error_factor", "join_status", "parse_status",
        "auto_total_eui_kwh_m2", "old_eui_kwh_m2", "new_eui_kwh_m2", "eui_shift_pct",
    ]
    df[out_cols].to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV} ({len(df)} rows)", file=sys.stderr)

    print("\nper-mode summary (median error_factor / %% within +/-1%%, target vs reproduced):", file=sys.stderr)
    summary_rows = []
    for mode in MODES:
        sub = df[df["mode"] == mode]
        ef = sub["error_factor"].dropna()
        n_matched_ef = len(ef)
        n_unmatched_ef = int(sub["error_factor"].isna().sum())
        median_ef = float(ef.median())
        pct_within_1pct = float((((ef >= 0.99) & (ef <= 1.01)).sum() / len(ef)) * 100.0)
        target_med, target_pct = _TARGETS[mode]
        med_ok = abs(median_ef - target_med) < 1e-4
        pct_ok = abs(pct_within_1pct - target_pct) < 0.01

        shift = sub["eui_shift_pct"].dropna()
        deciles = np.quantile(shift, _DECILES) if len(shift) else np.full(len(_DECILES), np.nan)

        print(
            f"  {mode:>14s}: median_ef={median_ef:.4f} (target {target_med:.4f}, "
            f"{'OK' if med_ok else 'MISMATCH'})  within+/-1%={pct_within_1pct:.2f}% "
            f"(target {target_pct:.2f}%, {'OK' if pct_ok else 'MISMATCH'})  "
            f"n_matched_ef={n_matched_ef}  n_unmatched_ef={n_unmatched_ef}  "
            f"n_eui_unmatched={n_unmatched_modes[mode]}  n_eui_available={len(shift)}",
            file=sys.stderr,
        )
        summary_rows.append({
            "mode": mode,
            "n_matched_ef": n_matched_ef,
            "n_unmatched_ef": n_unmatched_ef,
            "median_error_factor": median_ef,
            "pct_within_1pct": pct_within_1pct,
            "n_eui_available": len(shift),
            "eui_shift_pct_p10": deciles[0], "eui_shift_pct_p20": deciles[1],
            "eui_shift_pct_p30": deciles[2], "eui_shift_pct_p40": deciles[3],
            "eui_shift_pct_p50": deciles[4], "eui_shift_pct_p60": deciles[5],
            "eui_shift_pct_p70": deciles[6], "eui_shift_pct_p80": deciles[7],
            "eui_shift_pct_p90": deciles[8],
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_path = OUT_CSV.with_name("open01_denominator_swap_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"\nwrote {summary_path}", file=sys.stderr)
    print("\ndeciles of eui_shift_pct per mode:", file=sys.stderr)
    print(summary_df.to_string(index=False), file=sys.stderr)


if __name__ == "__main__":
    main()
