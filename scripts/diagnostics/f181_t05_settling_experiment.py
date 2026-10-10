"""FINDING 181 / T05 — Settling experiment (D-EU-32 Option A).

Tests E1 (sizing disabled) and E2 (OMP_NUM_THREADS=1) plus E0 (baseline control)
across the 3 representative cells over 10 replicates each.

Writes:
  docs/docs_ACTIVE/europeanLocations/outputs/f181_t05_probes.csv
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.campaign.eu_cell_runner import (  # noqa: E402
    ENERGYPLUS_J_TO_KWH,
    _energyplus_exe,
    _extract_heating_kwh,
    run_campaign_cell,
)

SPEC_PATH = ROOT / "openubem/data/campaign/eu_campaign_cell_spec_v1.1.json"
SPEC_SHA256 = "16d3fbd62a9f79265c08c5746bbc70f5130cd30cb673c1a68c74755c79aa65f6"
GSS_ROOT = Path("C:/Users/o_iseri/Desktop/GSSCanada/GSSCanada-main/4J_docs_occ")
BINDING_PATH = GSS_ROOT / "Step10_docs/outputs_step10/eu_cell_presence_binding_v2.json"
NOTICE_PATH = GSS_ROOT / "Step10_docs/docs/2026-08-26_10.1_chaining-closure-notice.md"
SCHEDULES_ROOT = GSS_ROOT / "Step7_docs/outputs_step7/schedules"

BASE_RUN_ROOT = ROOT / "openubem/outputs/_tmp_f181/t05"
BUILD_ROOT = BASE_RUN_ROOT / "_built"
OUT_DIR = ROOT / "docs/docs_ACTIVE/europeanLocations/outputs"
OUTPUT_CSV = OUT_DIR / "f181_t05_probes.csv"

N_REPLICATES = 10

CELLS = [
    "uk__GB.ENG.AB.04.Gen.ReEx.001.001__f100",
    "it__IT.MidClim.SFH-TH.07.Gen.ReEx.001.001__f100",
    "it__IT.MidClim.SFH.07.Gen.ReEx.001.001__f000",
]

ARMS = ["E0", "E1", "E2"]

ERR_MARKERS = {
    "marker_psy": "Temperature out of range",
    "marker_inside_hb": "Inside surface heat balance did not converge",
    "marker_calchb": "CalcHeatBalanceInsideSurf",
}

FIELDS = [
    "cell_id", "survey_fold", "arm", "replicate", "applied",
    "completed", "completion_status", "return_code", "severe_count", "fatal_count",
    "heating_kwh", "runtime_s", "marker_psy", "marker_inside_hb", "marker_calchb", "error",
]


def _sha256_file_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(Path(path).read_bytes())
    return digest.hexdigest()


NOTICE_SHA256 = _sha256_file_bytes(NOTICE_PATH)


def _load_spec_cells() -> dict[str, dict]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert spec["spec_status"] == "FROZEN_PINNED"
    assert spec["n_cells"] == 510
    by_id = {c["cell_id"]: c for c in spec["cells"]}
    for cell_id in CELLS:
        assert cell_id in by_id, f"cell not in spec: {cell_id}"
    return by_id


def _err_markers(run_dir: Path) -> dict[str, bool]:
    err_path = run_dir / "eplusout.err"
    text = ""
    if err_path.exists():
        try:
            text = err_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
    return {name: (needle in text) for name, needle in ERR_MARKERS.items()}


def _build_once(cell: dict) -> tuple[Path, Path]:
    """Build the cell's IDF once via run_campaign_cell(dry_run=True). Returns (idf_path, epw_path)."""
    run_root = BUILD_ROOT / str(cell["cell_id"])
    manifest = run_campaign_cell(
        cell,
        spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
        binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
        chaining_notice_sha256=NOTICE_SHA256,
        schedules_root=SCHEDULES_ROOT,
        run_root=run_root, dry_run=True,
    )
    return Path(manifest["idf_path"]), Path(manifest["epw_path"])


def _load_idf(idf_path: Path):
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError
    from openubem.campaign.eu_cell_runner import ENERGYPLUS_IDD_PATH

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(str(idf_path))


def _apply_arm(arm: str, idf_path: Path) -> bool:
    """Mutate the copy at idf_path in place for the given arm. Returns applied (True/False)."""
    if arm in ("E0", "E2"):
        return True

    if arm == "E1":
        idf = _load_idf(idf_path)
        # Disable Zone, System, Plant sizing in SimulationControl
        sim_controls = idf.idfobjects["SIMULATIONCONTROL"]
        if sim_controls:
            sc = sim_controls[0]
            sc.Do_Zone_Sizing_Calculation = "No"
            sc.Do_System_Sizing_Calculation = "No"
            sc.Do_Plant_Sizing_Calculation = "No"
            sc.Run_Simulation_for_Sizing_Periods = "No"
            sc.Run_Simulation_for_Weather_File_Run_Periods = "Yes"
            sc.Do_HVAC_Sizing_Simulation_for_Sizing_Periods = "No"

        # Remove SizingPeriod:WeatherFileDays objects
        sizing_periods = list(idf.idfobjects["SIZINGPERIOD:WEATHERFILEDAYS"])
        for sp in sizing_periods:
            idf.removeidfobject(sp)

        # Remove SizingPeriod:DesignDay objects if any
        design_days = list(idf.idfobjects["SIZINGPERIOD:DESIGNDAY"])
        for dd in design_days:
            idf.removeidfobject(dd)

        idf.saveas(str(idf_path))
        return True

    raise ValueError(f"unknown arm: {arm}")


def _run_energyplus_custom(idf_path: Path, epw_path: Path, run_dir: Path, timeout: int = 900, extra_env: dict | None = None) -> dict:
    started = time.time()
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    result = subprocess.run(
        [str(_energyplus_exe()), "-x", "-r", "-w", str(epw_path), "-d", str(run_dir), str(idf_path)],
        cwd=run_dir, capture_output=True, text=True, timeout=timeout, env=env,
    )
    err_path = run_dir / "eplusout.err"
    err = err_path.read_text(encoding="utf-8", errors="replace") if err_path.exists() else ""
    csv_path = run_dir / "eplusout.csv"
    heating_kwh = _extract_heating_kwh(csv_path) if csv_path.exists() else None
    return {
        "return_code": result.returncode,
        "severe_count": err.count("** Severe  **"),
        "fatal_count": err.count("**  Fatal  **"),
        "runtime_s": round(time.time() - started, 3),
        "heating_kwh": heating_kwh,
    }


def _run_replicate(cell_id: str, survey_fold: str, arm: str, replicate: int,
                    built_idf_path: Path, epw_path: Path) -> dict:
    variant_dir = BASE_RUN_ROOT / arm / cell_id / f"rep{replicate}"
    variant_dir.mkdir(parents=True, exist_ok=True)
    idf_copy = variant_dir / built_idf_path.name
    shutil.copyfile(built_idf_path, idf_copy)

    row = {
        "cell_id": cell_id, "survey_fold": survey_fold, "arm": arm, "replicate": replicate,
        "applied": None,
        "completed": None, "completion_status": None, "return_code": None,
        "severe_count": None, "fatal_count": None, "heating_kwh": None, "runtime_s": None,
        "marker_psy": False, "marker_inside_hb": False, "marker_calchb": False, "error": "",
    }
    try:
        applied = _apply_arm(arm, idf_copy)
    except Exception as exc:
        row["applied"] = False
        row["error"] = f"APPLY_FAILED {type(exc).__name__}: {str(exc)[:300]}"
        return row

    row["applied"] = applied
    if not applied:
        row["completion_status"] = "NOT_APPLICABLE"
        return row

    extra_env = {"OMP_NUM_THREADS": "1"} if arm == "E2" else None

    try:
        energy = _run_energyplus_custom(idf_copy, epw_path, variant_dir, timeout=900, extra_env=extra_env)
        row["return_code"] = energy["return_code"]
        row["severe_count"] = energy["severe_count"]
        row["fatal_count"] = energy["fatal_count"]
        row["runtime_s"] = energy["runtime_s"]
        row["heating_kwh"] = repr(energy["heating_kwh"])
        if (
            energy["return_code"] != 0
            or energy["fatal_count"]
            or energy["heating_kwh"] is None
        ):
            row["completed"] = False
            row["completion_status"] = "ENGINE_FAILED"
        else:
            row["completed"] = True
            row["completion_status"] = "COMPLETED"
        row.update(_err_markers(variant_dir))
    except Exception as exc:
        row["error"] = f"RUN_FAILED {type(exc).__name__}: {str(exc)[:300]}"
        row["completed"] = False
        row["completion_status"] = "EXCEPTION"
        if variant_dir.exists():
            row.update(_err_markers(variant_dir))
    return row


def write_csv(rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def print_summary(rows: list[dict]) -> None:
    by_key: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        by_key.setdefault((r["cell_id"], r["arm"]), []).append(r)

    print("\n" + "=" * 105)
    print(f"{'cell_id':<48} | {'arm':<4} | {'completed':<10} | {'distinct_kwh':<12} | {'spread_%':<10} | {'status'}")
    print("=" * 105)
    for (cell_id, arm), group in sorted(by_key.items()):
        completed_reps = [r for r in group if r["completed"] is True]
        n_comp = len(completed_reps)
        vals = [float(r["heating_kwh"]) for r in completed_reps if r["heating_kwh"] not in (None, "None")]
        unique_vals = sorted(set(vals))
        n_distinct = len(unique_vals)
        if len(vals) >= 2 and sum(vals) > 0:
            spread_pct = ((max(vals) - min(vals)) / (sum(vals) / len(vals))) * 100.0
        else:
            spread_pct = 0.0
        
        status = "PERFECT_IDENTICAL" if (n_comp == N_REPLICATES and n_distinct == 1) else ("DIVERGENT" if n_distinct > 1 else f"FAILED_{N_REPLICATES-n_comp}")
        print(f"{cell_id:<48} | {arm:<4} | {n_comp:>2}/{N_REPLICATES:<7} | {n_distinct:>2} states     | {spread_pct:>8.4f} % | {status}")
    print("=" * 105 + "\n")


def main() -> int:
    spec_cells = _load_spec_cells()
    print(f"Loaded {len(spec_cells)} spec cells.")
    print(f"Target cells ({len(CELLS)}): {CELLS}")
    print(f"Arms: {ARMS}, Replicates: {N_REPLICATES}")

    built_info: dict[str, tuple[Path, Path]] = {}
    for cell_id in CELLS:
        print(f"Building cell {cell_id} ...")
        built_info[cell_id] = _build_once(spec_cells[cell_id])

    all_rows: list[dict] = []
    total_runs = len(CELLS) * len(ARMS) * N_REPLICATES
    run_idx = 0

    print(f"Starting {total_runs} runs...")
    start_time = time.time()

    for arm in ARMS:
        for cell_id in CELLS:
            cell = spec_cells[cell_id]
            fold = cell["survey_fold"]
            built_idf, epw_path = built_info[cell_id]
            for rep in range(1, N_REPLICATES + 1):
                run_idx += 1
                row = _run_replicate(cell_id, fold, arm, rep, built_idf, epw_path)
                all_rows.append(row)
                kwh_str = f"{float(row['heating_kwh']):.2f} kWh" if row['completed'] else "FAILED"
                print(f"[{run_idx:02d}/{total_runs:02d}] Arm {arm} | {cell_id.split('__')[1][:25]} | rep {rep:02d}: {row['completion_status']} ({row['runtime_s']}s) -> {kwh_str}")

    write_csv(all_rows)
    elapsed = round(time.time() - start_time, 2)
    print(f"\nAll {total_runs} runs finished in {elapsed} s.")
    print_summary(all_rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
