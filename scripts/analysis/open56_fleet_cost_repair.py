"""X01 repair pass of PLAN_ten-items-2026-08-18-overnight.md.

The stratified run (`open56_fleet_cost_stratified.py`) executed 140 EnergyPlus runs through a
6-worker pool. Ten of the 70 buildings produced an EMPTY output directory in the baseline arm --
no `eplusout.err` at all, no severe, no volume warning, nothing. That is not a simulation result:
re-run serially, the identical `baseline.idf` completes in 18 seconds with 0 severe errors
(`nyc_centre/relation_11171793`, checked by hand before this script was written).

So it is a concurrency artifact of the harness, and it would have understated the control
(60/70 instead of 70/70) and dropped 10 buildings from the cost sample. This re-runs both arms
of exactly those buildings, one at a time, and merges the result over the original CSV.

Nothing about the treatment changes. Same IDFs, already on disk from the first pass.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from open56_fleet_cost_stratified import OUT, WORK, _n_converge  # noqa: E402
from open56_zone_volume_experiment import epw_for, read_run, run_ep  # noqa: E402

CSV = OUT / "open56_fleet_cost_stratified.csv"


def main() -> int:
    df = pd.read_csv(CSV)
    bad = df[(df["base_completed"] != True) | (df["treat_completed"] != True)]  # noqa: E712
    print("re-running %d buildings serially (both arms)\n" % len(bad))

    for i, (idx, r) in enumerate(bad.iterrows(), 1):
        cell, stem = r["cell"], r["stem"]
        d = WORK / ("%s__%s" % (cell, stem))
        epw = epw_for(cell)
        if epw is None or not (d / "baseline.idf").exists():
            print("  SKIP %s/%s (epw=%s idf=%s)"
                  % (cell, stem, epw is not None, (d / "baseline.idf").exists()))
            continue
        for arm, idf in (("base", d / "baseline.idf"), ("treat", d / "treated.idf")):
            run_ep(idf, epw, d / ("%s_out" % arm))
        b, t = read_run(d / "base_out"), read_run(d / "treat_out")
        df.at[idx, "base_n_converge"] = _n_converge(d / "base_out")
        df.at[idx, "treat_n_converge"] = _n_converge(d / "treat_out")
        for name, rec in (("base", b), ("treat", t)):
            for k, v in rec.items():
                col = "%s_%s" % (name, k)
                if col in df.columns:
                    df.at[idx, col] = v
        if b["eui_kwh_m2"] and t["eui_kwh_m2"]:
            df.at[idx, "delta_eui"] = t["eui_kwh_m2"] - b["eui_kwh_m2"]
            df.at[idx, "pct_change"] = 100.0 * (t["eui_kwh_m2"] - b["eui_kwh_m2"]) / b["eui_kwh_m2"]
        print("  %2d/%d %-12s %-24s base=%s(%s severe, %s volwarn)  treat=%s(%s severe, %s volwarn)"
              % (i, len(bad), cell, stem, b["completed"], b["n_severe"], b["vol_warnings"],
                 t["completed"], t["n_severe"], t["vol_warnings"]), flush=True)

    df.to_csv(CSV, index=False)
    print("\nmerged into %s\n" % CSV)

    print("=== X01 CONTROL, after repair ===")
    print("diff check OK                            : %d / %d"
          % (int(df["diff_check"].astype(str).str.startswith("OK").sum()), len(df)))
    print("baseline runs with the volume warning    : %d / %d"
          % (int((df["base_vol_warnings"] > 0).sum()), len(df)))
    print("treated  runs with the volume warning    : %d / %d"
          % (int((df["treat_vol_warnings"] > 0).sum()), len(df)))
    print("baseline completed / treated completed   : %d / %d  and  %d / %d"
          % (int((df["base_completed"] == True).sum()), len(df),                # noqa: E712
             int((df["treat_completed"] == True).sum()), len(df)))              # noqa: E712

    # A denominator that moves is not a cost: exclude and report separately.
    df["area_ratio"] = df["treat_floor_area_m2"] / df["base_floor_area_m2"]
    moved = df[df["area_ratio"].notna() & (abs(df["area_ratio"] - 1) >= 0.001)]
    print("\n=== buildings whose reported floor AREA moved (excluded from the cost) ===")
    print(moved[["cell", "stem", "n_zones", "base_floor_area_m2", "treat_floor_area_m2",
                 "area_ratio", "pct_change"]].to_string(index=False)
          if len(moved) else "  none")

    ok = df[df["pct_change"].notna() & (abs(df["area_ratio"] - 1) < 0.001)]
    print("\n=== X01 COST, like-for-like denominators only (n=%d) ===" % len(ok))
    print(ok.groupby("cell")["pct_change"]
          .agg(["count", "mean", "median", "min", "max"]).round(3).to_string())
    print("\npooled:")
    print(ok["pct_change"].describe().round(4).to_string())
    print("\nsame-direction: %d / %d positive (%.1f %%)"
          % (int((ok["pct_change"] > 0).sum()), len(ok),
             100.0 * (ok["pct_change"] > 0).mean()))
    print("absolute delta kWh/m2: mean %.4f  median %.4f  min %.4f  max %.4f"
          % (ok["delta_eui"].mean(), ok["delta_eui"].median(),
             ok["delta_eui"].min(), ok["delta_eui"].max()))

    print("\n=== X02 what the cost scales with (outlier-free) ===")
    for c in ("n_zones", "sum_written_volume_m3", "cov_levels",
              "base_floor_area_m2", "base_eui_kwh_m2"):
        if c in ok and ok[c].notna().sum() > 3:
            print("  corr(delta_eui, %-22s) = %+.3f    corr(pct_change) = %+.3f"
                  % (c, ok["delta_eui"].corr(ok[c]), ok["pct_change"].corr(ok[c])))
    import numpy as np
    la = np.log10(ok["base_floor_area_m2"])
    print("  corr(pct_change, log10 floor area)      = %+.3f" % ok["pct_change"].corr(la))
    per = ok["delta_eui"] / ok["n_zones"]
    print("\n  delta_eui           : mean %.4f  sd %.4f  cv %.3f"
          % (ok["delta_eui"].mean(), ok["delta_eui"].std(),
             ok["delta_eui"].std() / ok["delta_eui"].mean()))
    print("  delta_eui per zone  : mean %.4f  sd %.4f  cv %.3f"
          % (per.mean(), per.std(), per.std() / per.mean()))
    print("\n  pct_change by floor-area quartile:")
    q = pd.qcut(ok["base_floor_area_m2"], 4, labels=["Q1 smallest", "Q2", "Q3", "Q4 largest"])
    print(ok.groupby(q, observed=True)["pct_change"]
          .agg(["count", "median", "mean"]).round(3).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
