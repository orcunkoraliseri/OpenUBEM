"""T11 (plan ten-live-items-2026-08-20-evening): finish T10's job -- prove determinism on a
run that COMPLETES, and test the two-IDF hypothesis for the C04 building.

T10 (scripts/analysis/c04_same_head_double_run_2026-08-20.py) ran nyc_centre/way/266034056
twice at the same HEAD and found 0 of 33 columns differing -- but BOTH runs terminated
failed_fatal at warmup, so every EUI column was NaN in both arms and NaN == NaN counted as
agreement. This script has two parts:

(a) Repeat T10's method on a building that SUCCEEDS. Picked at random (numpy seed 42, index 0
    of a 15-row sample) from openubem/outputs/comparisons/open61_census_fleet.csv where
    recorded_simulation_status == "success" and parsed_total_eui_kwh_m2 is non-null, restricted
    to archetype_id in {SmallOffice, MidriseApartment} for a short run. Chosen:
    austin_rural / way/1480414365 (SmallOffice, 1 zone, IDF 48,100 B). Two runs, same HEAD,
    separate working directories, cwd= passed explicitly (inside run_energyplus, runner.py:66).

(b) Run the C04 building's step3 IDF (nyc_centre/step3/idfs/way_266034056.idf, the "later,
    repaired version" T10 found) ONCE and compare its simulation_status/error_summary against
    T10's already-recorded fleet_staging-IDF result (failed_fatal, "**  Fatal  ** Program
    terminates due to preceding condition.", read from T10's own CSV -- not re-run, to avoid a
    redundant EnergyPlus process).

EnergyPlus is run strictly one process at a time, serially, in this order: (a) run A, (a) run B,
(b) step3 run. Every EnergyPlus invocation passes cwd= explicitly via run_energyplus.
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
WORK_A = SCRATCH / "c04b_completing_a"
WORK_B = SCRATCH / "c04b_completing_b"
WORK_STEP3 = SCRATCH / "c04b_step3"

SUCCESS_STATUSES = {"success", "success_cached"}

CORPUS = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4")

# --- Part (a): a building that succeeds ---
CELL_A = "austin_rural"
OSM_ID_A = "way/1480414365"
STEM_A = "way_1480414365"
CELL_DIR_A = CORPUS / CELL_A
IDF_PATH_A = CELL_DIR_A / "fleet_staging" / "idfs" / (STEM_A + ".idf")
EPW_PATH_A = CELL_DIR_A / "fleet_staging" / "weather" / (
    "USA_TX_Horseshoe.Bay.Resort.AP.720639_TMYx.2011-2025.epw"
)
N_CANDIDATES_TRIED = 1  # first sampled candidate; already SUCCEEDS in both arms, see report

# Manifest row fields verified directly from the D1 corpus for this osm_id
# (austin_rural/step3/03_idf_manifest.parquet + austin_rural/01_buildings.gpkg):
MANIFEST_ROW_A = pd.Series(
    {
        "osm_id": OSM_ID_A,
        "num_zones": 1,
        "data_quality_flag": "generic_tag,no_floors,no_function,no_height,no_year|VINTAGE_NAN_PERMISSIVE_DEFAULT",
        "resolution_mode": "auto",
        "footprint_area_m2": 287.0961565458416,
        "levels": float("nan"),
        "height_m": float("nan"),
    }
)

# --- Part (b): C04 building's two IDFs ---
CELL_B = "nyc_centre"
OSM_ID_B = "way/266034056"
STEM_B = "way_266034056"
CELL_DIR_B = CORPUS / CELL_B
STEP3_IDF_PATH = CELL_DIR_B / "step3" / "idfs" / (STEM_B + ".idf")
FLEET_IDF_PATH = CELL_DIR_B / "fleet_staging" / "idfs" / (STEM_B + ".idf")
EPW_PATH_B = (
    CELL_DIR_B
    / "fleet_staging"
    / "weather"
    / "USA_NY_New.York-Central.Park.Obs-Belvedere.Castle.725053_TMYx.2011-2025.epw"
)
T10_CSV = REPO / "openubem" / "outputs" / "comparisons" / "c04_same_head_double_run_2026-08-20.csv"
# T10's own completed work dir (this session's scratchpad, per c04_same_head_double_run_2026-08-20.py
# WORK_A) -- read-only here, not re-run, to get the actual first "** Severe **" line (classify_
# outcome's error_summary only captures the FATAL_RE trailer line, which is the generic, uninformative
# "Program terminates due to preceding condition." per F9; the specific severe cause is a separate line).
T10_WORK_A = SCRATCH / "c04_a"


def _first_severe_line(work_dir: Path) -> str:
    err_path = work_dir / "eplusout.err"
    if not err_path.exists():
        return ""
    for line in err_path.read_text(errors="replace").splitlines():
        if "** Severe" in line and "**" in line.split("** Severe", 1)[1]:
            return line.strip()
    return ""

MANIFEST_ROW_B = pd.Series(
    {
        "osm_id": OSM_ID_B,
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


def run_one(work_dir: Path, osm_id: str, idf_path: Path, epw_path: Path, manifest_row: pd.Series) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    task = types.SimpleNamespace(
        osm_id=osm_id,
        idf_path=str(idf_path),
        epw_path=str(epw_path),
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
        parsed = parse_building(sql_path, csv_path, manifest_row)
        parsed["simulation_status"] = parsed.pop("parse_status")
        row = parsed
    else:
        row = {"osm_id": osm_id, "simulation_status": status,
               "error_summary": outcome.get("error_summary", "")}
        for col in _STEP5_COLS:
            if col not in ("simulation_status", "error_summary"):
                row[col] = float("nan") if ("eui" in col or "gwp" in col or col == "iod") else None

    row["_raw_returncode"] = raw.get("returncode")
    row["_raw_n_warnings"] = outcome.get("n_warnings")
    row["_raw_n_severe"] = outcome.get("n_severe")
    return row


def _values_equal(va, vb) -> bool:
    try:
        if pd.isna(va) and pd.isna(vb):
            return True
    except (TypeError, ValueError):
        pass
    return va == vb


def main() -> None:
    head_before = _git_head()

    # --- Part (a): serial, one EnergyPlus process at a time ---
    row_a = run_one(WORK_A, OSM_ID_A, IDF_PATH_A, EPW_PATH_A, MANIFEST_ROW_A)
    row_b = run_one(WORK_B, OSM_ID_A, IDF_PATH_A, EPW_PATH_A, MANIFEST_ROW_A)

    # --- Part (b): step3 IDF, run once, after part (a) finishes ---
    row_step3 = run_one(WORK_STEP3, OSM_ID_B, STEP3_IDF_PATH, EPW_PATH_B, MANIFEST_ROW_B)

    head_after = _git_head()
    head_stable = head_before == head_after

    # --- Part (a) diff ---
    all_cols = sorted(set(row_a) | set(row_b))
    records = []
    n_diff = 0
    n_nonnull_both = 0
    for col in all_cols:
        va = row_a.get(col, "<MISSING>")
        vb = row_b.get(col, "<MISSING>")
        eq = _values_equal(va, vb)
        try:
            nonnull_both = not (pd.isna(va) or pd.isna(vb))
        except (TypeError, ValueError):
            nonnull_both = True
        if nonnull_both:
            n_nonnull_both += 1
        if not eq:
            n_diff += 1
        records.append({
            "part": "a_double_run",
            "column": col,
            "value_a": va,
            "value_b": vb,
            "equal": eq,
            "nonnull_both": nonnull_both,
        })

    n_diff_nonnull = sum(
        1 for r in records if r["nonnull_both"] and not r["equal"]
    )

    out_df = pd.DataFrame(records)

    # --- Part (b) row: step3 vs fleet_staging (fleet_staging read from T10's CSV) ---
    t10_df = pd.read_csv(T10_CSV)
    fleet_status = t10_df.loc[t10_df["column"] == "simulation_status", "value_a"].iloc[0]
    fleet_error = t10_df.loc[t10_df["column"] == "error_summary", "value_a"].iloc[0]

    step3_status = row_step3.get("simulation_status")
    step3_error = str(row_step3.get("error_summary", ""))[:200]
    fleet_error_trunc = str(fleet_error)[:200]

    fleet_severe = _first_severe_line(T10_WORK_A)[:200]
    step3_severe = _first_severe_line(WORK_STEP3)[:200]

    idfs_identical = step3_status == fleet_status and step3_severe == fleet_severe

    step3_stat = STEP3_IDF_PATH.stat()
    fleet_stat = FLEET_IDF_PATH.stat()

    part_b_rows = [
        {
            "part": "b_step3_vs_fleet_staging",
            "column": "simulation_status",
            "value_a": fleet_status,
            "value_b": step3_status,
            "equal": step3_status == fleet_status,
            "nonnull_both": True,
        },
        {
            "part": "b_step3_vs_fleet_staging",
            "column": "severe_text_200c",
            "value_a": fleet_severe,
            "value_b": step3_severe,
            "equal": step3_severe == fleet_severe,
            "nonnull_both": True,
        },
    ]
    out_df = pd.concat([out_df, pd.DataFrame(part_b_rows)], ignore_index=True)

    out_path = REPO / "openubem" / "outputs" / "comparisons" / "c04_determinism_completing_2026-08-20.csv"
    out_df.to_csv(out_path, index=False)

    if n_diff == 0:
        verdict_a = (
            f"identical on a COMPLETING building -> the historical difference was code drift "
            f"({n_nonnull_both} of {len(all_cols)} compared columns were non-null in both arms; "
            f"0 of those differ)"
        )
    else:
        diff_cols = out_df.loc[
            (out_df["part"] == "a_double_run") & (~out_df["equal"]), "column"
        ].tolist()
        verdict_a = (
            f"differs -> the pipeline is non-deterministic, in these columns: {diff_cols} "
            f"({n_nonnull_both} of {len(all_cols)} compared columns were non-null in both arms; "
            f"{n_diff_nonnull} of those differ)"
        )

    iod_a = out_df.loc[(out_df["part"] == "a_double_run") & (out_df["column"] == "iod")]
    sim_status_a = out_df.loc[(out_df["part"] == "a_double_run") & (out_df["column"] == "simulation_status")]

    print(f"HEAD before: {head_before}")
    print(f"HEAD after:  {head_after}")
    print(f"HEAD stable: {head_stable}")
    print(f"--- Part (a): {OSM_ID_A} ({CELL_A}), archetype SmallOffice, candidates tried: {N_CANDIDATES_TRIED} ---")
    print(f"columns compared: {len(all_cols)}")
    print(f"columns non-null in both arms: {n_nonnull_both}")
    print(f"columns differing overall: {n_diff}")
    print(f"columns differing among non-null-both: {n_diff_nonnull}")
    print(f"verdict: {verdict_a}")
    if not iod_a.empty:
        print(f"iod: A={iod_a['value_a'].iloc[0]}  B={iod_a['value_b'].iloc[0]}  equal={iod_a['equal'].iloc[0]}")
    if not sim_status_a.empty:
        print(
            f"simulation_status: A={sim_status_a['value_a'].iloc[0]}  "
            f"B={sim_status_a['value_b'].iloc[0]}  equal={sim_status_a['equal'].iloc[0]}"
        )
    print(f"run A status: {row_a.get('simulation_status')}  returncode={row_a.get('_raw_returncode')}")
    print(f"run B status: {row_b.get('simulation_status')}  returncode={row_b.get('_raw_returncode')}")
    print(f"--- Part (b): {OSM_ID_B} ({CELL_B}) -- step3 IDF vs fleet_staging IDF ---")
    print(f"fleet_staging IDF: {FLEET_IDF_PATH}  size={fleet_stat.st_size}B  mtime={fleet_stat.st_mtime}")
    print(f"step3 IDF:         {STEP3_IDF_PATH}  size={step3_stat.st_size}B  mtime={step3_stat.st_mtime}")
    print(f"fleet_staging status (from T10 CSV): {fleet_status}")
    print(f"fleet_staging error_summary (200c, generic trailer): {fleet_error_trunc}")
    print(f"fleet_staging first severe line (200c, from T10's own work dir): {fleet_severe}")
    print(f"step3 status (this run):             {step3_status}")
    print(f"step3 error_summary (200c, generic trailer): {step3_error}")
    print(f"step3 first severe line (200c):      {step3_severe}")
    print(f"idfs give identical status+severe: {idfs_identical}")
    print(f"CSV written: {out_path}")


if __name__ == "__main__":
    main()
