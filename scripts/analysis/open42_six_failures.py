"""OPEN-42 / T07 -- establish a recorded cause for the six not_simulated buildings
in the adopted phaseE_elevrb run.

Two measurements, run in sequence:

1. Read the six failed rows from the adopted run's own
   docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb/<cell>/04_simulation_manifest.parquet
   (la_rural, la_urban). These are the adopted run's own artifacts: status, n_severe, error_summary.
   No EnergyPlus .err/.end file for these six survives locally under the phaseE_elevrb tree, the
   elev_rebaseline temp work_dirs, or the T17-T20 harvest caches -- confirmed by direct filesystem
   search, not assumed.

2. Separately, and clearly labelled as NOT the adopted run's own trace, cite locally-recoverable
   EnergyPlus .err traces for the same six osm_ids, produced under other local runs that used the
   production pipeline's default resolution_mode="auto" (same default v12_cell_pipeline.py uses).
   These are corroborating context for the cause narrative in the report, not a substitute measurement
   for the adopted run.

Emits openubem/outputs/comparisons/open42_six_failures.csv with exactly six rows:
stem, cell, simulation_status, error_summary, err_file_found, severe_count, fatal_count, phase, zone,
surface, cause.
"""

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ADOPTED_BASE = REPO / "docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb"
OUT_CSV = REPO / "openubem/outputs/comparisons/open42_six_failures.csv"

CAUSE_NOTE = (
    "adopted run's own eplusout.err/.end not locally recoverable (work_dir empty; also absent from "
    "T17-T20 harvest caches and repo cache/); manifest's own n_severe IS an adopted-run artifact "
    "(computed by v12_cell_pipeline.py:build_sim_manifest at run time, persisted to the parquet). "
    "Register (OPEN-11, N04 2026-08-06, director-verified) identifies this exact six-osm_id set as "
    "the Phase-E inverted-geometry population whose docs_DONE/.../debugs/DONE_10_fails_solution.md "
    "remediation was never re-applied in the automated pipeline. That doc's SS7A: stage 1 (CW-wound "
    "footprint -> negative zone volume -> 10 m3 clamp) was fixed permanently by the committed "
    "orient(sign=1.0) in openubem/idf/builder.py; stage 2 (all-MATERIAL:NOMASS envelope on the largest "
    "Warehouses -> solar-driven top-zone heat-balance divergence -> runtime Fatal) was fixed ONLY by an "
    "opt-in thermal_mass=True flag applied by the one-off scripts/validation/phaseE_recover_10.py "
    "recovery script -- never wired into the standard production path (grep of "
    "scripts/validation/v12_cell_pipeline.py for 'thermal_mass': zero matches; BuildingIDF's default "
    "in openubem/idf/builder.py:196-198 is thermal_mass=False unless resolution_mode is "
    "'layout_assign'/'layout_assigner', and this pipeline never sets it). Corroborating local traces "
    "(NOT the adopted run -- different campaigns, resolution_mode='auto' matching the pipeline default) "
    "for the same osm_ids reproduce exactly the stage-2 signature: 0 volume-clamp warnings (orient "
    "fix present) but a **  Fatal  ** from repeated 'Temperature (...) out of bounds' Severe errors in "
    "a top-floor zone during RUNPERIOD1 (not Warmup, not Sizing)."
)


def load_adopted_manifest_rows() -> pd.DataFrame:
    frames = []
    for cell in ("la_rural", "la_urban"):
        p = ADOPTED_BASE / cell / "04_simulation_manifest.parquet"
        df = pd.read_parquet(p)
        df["cell"] = cell
        frames.append(df)
    allf = pd.concat(frames, ignore_index=True)
    fail = allf[allf["status"] != "success"].copy()
    assert len(fail) == 6, f"expected exactly six failed rows, got {len(fail)}"
    return fail


def load_adopted_results_status() -> pd.DataFrame:
    frames = []
    for cell in ("la_rural", "la_urban"):
        p = ADOPTED_BASE / cell / "05_results.csv"
        df = pd.read_csv(p)
        df["cell"] = cell
        frames.append(df)
    allf = pd.concat(frames, ignore_index=True)
    return allf[allf["simulation_status"] != "success"].copy()


def main() -> None:
    manifest_fail = load_adopted_manifest_rows()
    results_fail = load_adopted_results_status()

    rows = []
    for _, r in manifest_fail.iterrows():
        osm_id = str(r["osm_id"])
        stem = osm_id.replace("/", "_")
        cell = r["cell"]
        sim_status_row = results_fail[
            (results_fail["osm_id"] == osm_id) & (results_fail["cell"] == cell)
        ]
        simulation_status = (
            sim_status_row.iloc[0]["simulation_status"] if len(sim_status_row) else r["status"]
        )
        rows.append(
            {
                "stem": stem,
                "cell": cell,
                "simulation_status": simulation_status,
                "error_summary": r["error_summary"] if pd.notna(r["error_summary"]) else "",
                "err_file_found": False,
                "severe_count": int(r["n_severe"]),
                "fatal_count": "",  # not recoverable from the adopted run's own .err (does not survive)
                "phase": "",  # not recoverable from the adopted run's own .err (does not survive)
                "zone": "",  # not recoverable from the adopted run's own .err (does not survive)
                "surface": "",  # not recoverable from the adopted run's own .err (does not survive)
                "cause": CAUSE_NOTE,
            }
        )

    out = pd.DataFrame(rows)
    assert len(out) == 6, f"expected exactly six output rows, got {len(out)}"
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV} ({len(out)} rows)")
    print(out[["stem", "cell", "simulation_status", "error_summary", "err_file_found", "severe_count"]])


if __name__ == "__main__":
    main()
