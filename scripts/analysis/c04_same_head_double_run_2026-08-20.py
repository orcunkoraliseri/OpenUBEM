"""T10 (plan ten-live-items-2026-08-20-evening): same-HEAD double run of the C04 building.

Building identified at docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06_twentysix-
simulation-columns.md:230 -- nyc_centre / way/266034056, the sole simulation_status flip
(success -> not_simulated) carried as the "C04 leftover" alongside the iod movement.

Runs the SAME already-built IDF (D1 corpus layout: <cell>/fleet_staging/idfs/<stem>.idf)
through EnergyPlus twice, in two separate working directories, at the same git HEAD, with
cwd= passed explicitly to every EnergyPlus invocation (openubem.simulation.runner.
run_energyplus already does this -- OPEN-58 defect (a) fix). Parses both with
openubem.results.parser.parse_building (D3) and diffs every column.
"""
from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

REPO = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

from openubem.simulation.runner import run_energyplus, classify_outcome  # noqa: E402
from openubem.results.parser import parse_building  # noqa: E402
from openubem.results.aggregator import _STEP5_COLS  # noqa: E402

SCRATCH = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM"
    r"\b2049392-a165-43a8-b647-033b0e4621da\scratchpad"
)
WORK_A = SCRATCH / "c04_a"
WORK_B = SCRATCH / "c04_b"

CELL_DIR = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4\nyc_centre"
)
OSM_ID = "way/266034056"
IDF_PATH = CELL_DIR / "fleet_staging" / "idfs" / "way_266034056.idf"
EPW_PATH = (
    CELL_DIR
    / "fleet_staging"
    / "weather"
    / "USA_NY_New.York-Central.Park.Obs-Belvedere.Castle.725053_TMYx.2011-2025.epw"
)

SUCCESS_STATUSES = {"success", "success_cached"}

# Manifest row fields verified directly from the D1 corpus for this osm_id:
#   step3/03_idf_manifest.parquet -> num_zones=133, resolution_mode='auto',
#     data_quality_flag='no_floors,no_height'
#   01_buildings.gpkg -> footprint_area_m2=2932.4636722561927, levels=NaN, height_m=NaN
MANIFEST_ROW = pd.Series(
    {
        "osm_id": OSM_ID,
        "num_zones": 133,
        "data_quality_flag": "no_floors,no_height",
        "resolution_mode": "auto",
        "footprint_area_m2": 2932.4636722561927,
        "levels": float("nan"),
        "height_m": float("nan"),
    }
)


def _git_head() -> str:
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def run_one(work_dir: Path) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    task = types.SimpleNamespace(
        osm_id=OSM_ID,
        idf_path=str(IDF_PATH),
        epw_path=str(EPW_PATH),
        work_dir=str(work_dir),
    )
    raw = run_energyplus(task)  # cwd=task.work_dir passed explicitly inside runner.py:66
    outcome = classify_outcome(raw, work_dir)
    status = outcome["status"]

    sql_path = work_dir / "eplusout.sql"
    csv_path = work_dir / "eplusout.csv"
    sql_path = sql_path if sql_path.exists() else None
    csv_path = csv_path if csv_path.exists() else None

    if status in SUCCESS_STATUSES:
        parsed = parse_building(sql_path, csv_path, MANIFEST_ROW)
        parsed["simulation_status"] = parsed.pop("parse_status")
        row = parsed
    else:
        row = {"osm_id": OSM_ID, "simulation_status": status,
               "error_summary": outcome.get("error_summary", "")}
        for col in _STEP5_COLS:
            if col not in ("simulation_status", "error_summary"):
                row[col] = float("nan") if ("eui" in col or "gwp" in col or col == "iod") else None

    row["_raw_returncode"] = raw.get("returncode")
    row["_raw_n_warnings"] = outcome.get("n_warnings")
    row["_raw_n_severe"] = outcome.get("n_severe")
    return row


def main() -> None:
    head_before = _git_head()

    row_a = run_one(WORK_A)
    row_b = run_one(WORK_B)

    head_after = _git_head()

    def _values_equal(va, vb) -> bool:
        try:
            if pd.isna(va) and pd.isna(vb):
                return True
        except (TypeError, ValueError):
            pass
        return va == vb

    all_cols = sorted(set(row_a) | set(row_b))
    records = []
    n_diff = 0
    for col in all_cols:
        va = row_a.get(col, "<MISSING>")
        vb = row_b.get(col, "<MISSING>")
        eq = _values_equal(va, vb)
        if not eq:
            n_diff += 1
        records.append({"column": col, "value_a": va, "value_b": vb, "equal": eq})

    out_df = pd.DataFrame(records)
    out_path = REPO / "openubem" / "outputs" / "comparisons" / "c04_same_head_double_run_2026-08-20.csv"
    out_df.to_csv(out_path, index=False)

    head_stable = head_before == head_after
    n_cols = len(all_cols)

    if n_diff == 0:
        verdict = "identical -> the historical difference was code drift"
    else:
        diff_cols = out_df.loc[~out_df["equal"], "column"].tolist()
        verdict = f"differs -> the pipeline is non-deterministic, in these columns: {diff_cols}"

    iod_differs = bool(out_df.loc[out_df["column"] == "iod", "equal"].eq(False).any())
    sim_status_differs = bool(out_df.loc[out_df["column"] == "simulation_status", "equal"].eq(False).any())

    print(f"HEAD before: {head_before}")
    print(f"HEAD after:  {head_after}")
    print(f"HEAD stable: {head_stable}")
    print(f"columns compared: {n_cols}")
    print(f"columns differing: {n_diff}")
    print(f"verdict: {verdict}")
    print(f"iod differs: {iod_differs}")
    print(f"simulation_status differs: {sim_status_differs}")
    print(f"run A status: {row_a.get('simulation_status')}  returncode={row_a.get('_raw_returncode')}")
    print(f"run B status: {row_b.get('simulation_status')}  returncode={row_b.get('_raw_returncode')}")
    print(f"CSV written: {out_path}")


if __name__ == "__main__":
    main()
