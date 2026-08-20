"""Re-parse the already-completed open35_storey_intervention EnergyPlus outputs with
PRODUCTION's own openubem.results.parser.parse_building(), instead of the ad hoc
Total-Site-Energy/Total-Building-Area read borrowed from open56_zone_volume_experiment.py.

Why: the first pass's fidelity control (fresh baseline vs archived run-2 EUI for the same
21 buildings) failed by a systematic +15% to +37% -- one-directional, not noise. Root cause,
found by diffing the archived run-2 IDF against this task's freshly-built baseline IDF
(byte-identical, md5 confirmed) and then reading production's own EUI formula
(openubem/results/parser.py:396-498): total_eui_kwh_m2 is NOT
"Total Site Energy" / "Total Building Area" from the ABUPS summary table (what
open56_zone_volume_experiment.py's read_run() computes) -- it is the SUM OF PER-END-USE
EUIs from custom RunPeriod meters, each divided by resolve_simulated_floor_area()'s
multiplier-aware .eio zone area. The two floor-area and energy definitions differ, so the
ad hoc read was never comparable to any other number in this arc. This script fixes that by
calling the exact same parse_building() production uses, on the same completed sql/eio
files (no re-simulation).

Reads the sim_out directories written by open35_storey_intervention_2026-08-19.py's
successful, isolated-cwd run (openubem/outputs/comparisons/open35_storey_intervention_prep.csv
for the IDF/manifest fields; the sim_out dirs are still on disk under
%TEMP%/open35_storey_intervention/<cell>/<safe_id>/{baseline,treated}/{base,treat}_sim_out/).

Emits openubem/outputs/comparisons/open35_storey_intervention_results_v2.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from openubem.results.parser import parse_building  # noqa: E402

WORK = Path(r"C:\Users\o_iseri\AppData\Local\Temp\open35_storey_intervention")
OUT = REPO / "openubem" / "outputs" / "comparisons"
POP_CSV = OUT / "open35_eui_consequence.csv"


def main() -> int:
    prep = pd.read_csv(OUT / "open35_storey_intervention_prep.csv")
    ok = prep[prep["prep_status"] == "ok"].copy()
    print(f"re-parsing {len(ok)} buildings x 2 arms with production parse_building() ...")

    rows = []
    for _, r in ok.iterrows():
        cell, osm_id = r["cell"], r["osm_id"]
        safe_id = osm_id.replace("/", "_").replace(":", "_")
        for arm, idf_key, simdir_name in (("base", "base_idf_path", "base_sim_out"),
                                           ("treat", "treat_idf_path", "treat_sim_out")):
            idf_path = Path(r[idf_key])
            sim_out = idf_path.parent.parent / simdir_name
            sql_path = sim_out / "eplusout.sql"
            levels = 1 if arm == "base" else int(r["recovered_levels"])
            manifest_row = pd.Series({
                "osm_id": osm_id,
                "num_zones": int(r[f"{arm}_num_zones"]),
                "data_quality_flag": "",
                "resolution_mode": "auto",
                "levels": levels,
                "height_m": float("nan"),
                "footprint_area_m2": float(r["footprint_area_m2"]),
            })
            metrics = parse_building(sql_path if sql_path.exists() else None, None, manifest_row)
            metrics["cell"] = cell
            metrics["osm_id_key"] = osm_id
            metrics["arm"] = arm
            metrics["arm_kind"] = r["arm_kind"]
            metrics["recovered_levels"] = r["recovered_levels"]
            rows.append(metrics)
            print(f"  {cell}/{osm_id}/{arm}: parse_status={metrics['parse_status']} "
                  f"floor_area_m2={metrics['floor_area_m2']:.2f} "
                  f"({metrics['floor_area_provenance']}) "
                  f"total_eui_kwh_m2={metrics['total_eui_kwh_m2']}")

    raw = pd.DataFrame(rows)
    base = raw[raw.arm == "base"].set_index(["cell", "osm_id_key"])
    treat = raw[raw.arm == "treat"].set_index(["cell", "osm_id_key"])
    joined = base.join(treat, lsuffix="_base", rsuffix="_treat", how="outer").reset_index()
    joined["delta_eui"] = joined["total_eui_kwh_m2_treat"] - joined["total_eui_kwh_m2_base"]
    joined["pct_change"] = 100.0 * joined["delta_eui"] / joined["total_eui_kwh_m2_base"]

    pop = pd.read_csv(POP_CSV)[["cell", "osm_id", "total_eui_kwh_m2"]].rename(
        columns={"osm_id": "osm_id_key", "total_eui_kwh_m2": "archived_run2_eui"}
    )
    joined = joined.merge(pop, on=["cell", "osm_id_key"], how="left")
    joined["fidelity_diff_pct"] = 100.0 * (
        joined["total_eui_kwh_m2_base"] - joined["archived_run2_eui"]
    ) / joined["archived_run2_eui"]

    out = OUT / "open35_storey_intervention_results_v2.csv"
    joined.to_csv(out, index=False)
    print(f"\nwrote {out}")

    print("\n=== FIDELITY CHECK v2 (production parse_building vs archived run-2) ===")
    print(joined[["cell", "osm_id_key", "arm_kind_base", "total_eui_kwh_m2_base",
                   "archived_run2_eui", "fidelity_diff_pct"]].to_string())
    print(f"\nmax |diff%| = {joined['fidelity_diff_pct'].abs().max():.4f}")
    print(f"mean |diff%| = {joined['fidelity_diff_pct'].abs().mean():.4f}")

    print("\n=== TREATMENT vs NEGATIVE CONTROL, v2 ===")
    print(joined[["cell", "osm_id_key", "arm_kind_base", "recovered_levels_base",
                   "total_eui_kwh_m2_base", "total_eui_kwh_m2_treat",
                   "delta_eui", "pct_change"]].to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
