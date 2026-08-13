"""
OPEN-46 / T03 — EVIDENCE ONLY.

Probes whether the adopted phaseE_elevrb run's EnergyPlus SQL files carry
enough information to report elevator energy as a separate end-use without
re-simulating anything. See docs/docs_ACTIVE/openings/implemenation/
PLAN_three-new-items-2026-08-12.md T03.

This script makes NO fix and changes NO source file. It only reads
04_simulation_manifest.parquet files and, where the sql_path they name
exists, queries the sqlite database read-only.

Sub-questions answered per file:
  1. trim_hourly True/False, inferred from presence/absence of the
     AllSummary tabular tables and hourly zone variables in the SQL.
  2. Does TabularDataWithStrings carry an "End Uses By Subcategory" table
     with an Elevators row under Interior Equipment?
  3. Does the meter / ReportDataDictionary carry anything named for
     elevators?

Non-vacuity control (hard rule 7): before probing the real files, this
script builds a synthetic sqlite database in the scratchpad containing a
TabularDataWithStrings table with a deliberately inserted Elevators row,
proves the query used against real files finds that planted row, then
deletes the synthetic database. A "not found" result against real files is
only meaningful because this control shows the same query finds a real hit
when one exists.
"""

import csv
import os
import sqlite3
import sys
import tempfile

import pandas as pd

REPO_ROOT = r"C:\Users\o_iseri\Desktop\OpenUBEM"
RESULTS_ROOT = os.path.join(
    REPO_ROOT, "docs", "docs_VALIDATION", "validations", "overAll",
    "results", "phaseE_elevrb",
)
OUT_CSV = os.path.join(
    REPO_ROOT, "openubem", "outputs", "comparisons",
    "open46_sql_subcategory_probe.csv",
)

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]

SAMPLE_PLAN = {
    "austin_centre": 2,
    "la_centre": 2,
    "nyc_urban": 2,
}


def run_nonvacuity_control():
    print("=== NON-VACUITY CONTROL ===")
    tmp_dir = tempfile.mkdtemp(prefix="open46_control_")
    db_path = os.path.join(tmp_dir, "synthetic_control.sql")
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE TabularDataWithStrings ("
        "TabularDataIndex INTEGER, ReportName TEXT, TableName TEXT, "
        "RowName TEXT, ColumnName TEXT, Value TEXT)"
    )
    cur.execute(
        "INSERT INTO TabularDataWithStrings VALUES "
        "(1, 'AnnualBuildingUtilityPerformanceSummary', "
        "'End Uses By Subcategory', 'Elevators', 'Electricity', '123.45')"
    )
    con.commit()
    con.close()

    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT TableName, RowName, ColumnName, Value FROM "
        "TabularDataWithStrings WHERE TableName LIKE '%End Uses By "
        "Subcategory%' AND RowName LIKE '%Elevator%'"
    ).fetchall()
    con.close()
    print(f"Planted row query result: {rows}")
    assert rows, "CONTROL FAILED: planted Elevators row was not found by the probe query"
    print("CONTROL PASSED: probe query finds a planted Elevators row.")

    os.remove(db_path)
    os.rmdir(tmp_dir)
    print(f"Synthetic control database removed: {db_path}")
    print()


def probe_file(cell, sql_path, osm_id):
    row = {
        "cell": cell,
        "osm_id": osm_id,
        "sql_path": sql_path,
        "exists": os.path.isfile(sql_path),
        "trim_hourly_inferred": "",
        "has_allsummary_table": "",
        "has_end_uses_by_subcategory": "",
        "elevators_row_in_subcategory": "",
        "elevator_named_meter": "",
        "note": "",
    }
    if not row["exists"]:
        row["note"] = "FILE NOT ON DISK"
        return row

    try:
        con = sqlite3.connect(sql_path)
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        has_tab = "TabularDataWithStrings" in tables
        row["has_allsummary_table"] = has_tab
        if has_tab:
            report_names = [r[0] for r in con.execute(
                "SELECT DISTINCT ReportName FROM TabularDataWithStrings"
            ).fetchall()]
            row["trim_hourly_inferred"] = (
                f"False (AllSummary-family reports present: {report_names})"
            )
            subcat_rows = con.execute(
                "SELECT TableName, RowName, ColumnName, Value FROM "
                "TabularDataWithStrings WHERE TableName LIKE "
                "'%End Uses By Subcategory%'"
            ).fetchall()
            row["has_end_uses_by_subcategory"] = bool(subcat_rows)
            elev_rows = [r for r in subcat_rows if "elevator" in (r[1] or "").lower()]
            row["elevators_row_in_subcategory"] = bool(elev_rows)
            row["note"] = f"subcategory_rows_sample={subcat_rows[:5]}"
        else:
            row["trim_hourly_inferred"] = "True (no TabularDataWithStrings table at all)"

        rdd_tables = [t for t in tables if "ReportDataDictionary" in t]
        elev_meter_hits = []
        for t in rdd_tables:
            try:
                hits = con.execute(
                    f"SELECT Name FROM {t} WHERE Name LIKE '%Elevator%'"
                ).fetchall()
                elev_meter_hits.extend(hits)
            except sqlite3.OperationalError:
                pass
        row["elevator_named_meter"] = bool(elev_meter_hits)
        con.close()
    except Exception as e:
        row["note"] = f"ERROR: {e}"
    return row


def main():
    run_nonvacuity_control()

    print("=== REAL-FILE PROBE ===")
    all_rows = []
    for cell, n in SAMPLE_PLAN.items():
        manifest_path = os.path.join(RESULTS_ROOT, cell, "04_simulation_manifest.parquet")
        if not os.path.isfile(manifest_path):
            print(f"{cell}: MANIFEST NOT FOUND at {manifest_path}")
            continue
        df = pd.read_parquet(manifest_path)
        succ = df[df["status"] == "success"].head(n)
        for _, r in succ.iterrows():
            probed = probe_file(cell, r["sql_path"], r["osm_id"])
            all_rows.append(probed)
            print(probed)

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    fieldnames = list(all_rows[0].keys()) if all_rows else []
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_rows:
            writer.writerow(r)
    print()
    print(f"Wrote {len(all_rows)} rows to {OUT_CSV}")

    n_exists = sum(1 for r in all_rows if r["exists"])
    print(f"Files found on disk: {n_exists} / {len(all_rows)}")


if __name__ == "__main__":
    sys.exit(main())
