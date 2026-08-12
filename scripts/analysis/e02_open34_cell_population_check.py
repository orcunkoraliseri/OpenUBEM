"""T06(a) -- OPEN-34's remaining measurement: was every adopted result cell-at-a-time?

Confirms that every adopted fleet artifact (phaseE/<cell>/05_results.csv) was produced
against that cell's FULL building population, by comparing its row count against the
row count of that cell's raw 01_buildings.gpkg (read directly with the stdlib sqlite3
module -- a GeoPackage is a SQLite database, so no new dependency is needed).

If every cell's counts match, OPEN-34's "was any published result produced from a batch
small enough for the batch-composition effect to matter" question is answered: no.

Plan: docs/docs_ACTIVE/openings/implemenation/PLAN_e02-audit-and-closure.md, T06(a).
This script performs part (a) ONLY -- no register/board/checklist edits.
"""

import csv
import os
import sqlite3

import pandas as pd

PHASE_E_ROOT = r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_VALIDATION\validations\overAll\results\phaseE"
OUT_CSV = r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open34_cell_population_check.csv"

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]


def count_gpkg_rows(gpkg_path):
    con = sqlite3.connect(gpkg_path)
    try:
        cur = con.cursor()
        cur.execute("SELECT table_name FROM gpkg_contents")
        tables = [r[0] for r in cur.fetchall()]
        if len(tables) != 1:
            raise RuntimeError(f"expected exactly one gpkg_contents table, found {tables} in {gpkg_path}")
        table = tables[0]
        cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        n = cur.fetchone()[0]
        return n, table
    finally:
        con.close()


def main():
    rows = []
    total_results = 0
    for cell in CELLS:
        cell_dir = os.path.join(PHASE_E_ROOT, cell)
        results_path = os.path.join(cell_dir, "05_results.csv")
        gpkg_path = os.path.join(cell_dir, "01_buildings.gpkg")

        if not os.path.isfile(results_path):
            print(f"{cell}: MISSING 05_results.csv at {results_path}")
            rows.append({
                "cell": cell,
                "n_rows_05_results": None,
                "n_buildings_gpkg": None,
                "difference": None,
                "whole": False,
                "gpkg_path": gpkg_path,
                "note": "05_results.csv NOT FOUND",
            })
            continue

        df = pd.read_csv(results_path)
        n_results = len(df)

        if not os.path.isfile(gpkg_path):
            print(f"{cell}: 01_buildings.gpkg NOT FOUND at {gpkg_path}")
            rows.append({
                "cell": cell,
                "n_rows_05_results": n_results,
                "n_buildings_gpkg": None,
                "difference": None,
                "whole": False,
                "gpkg_path": gpkg_path,
                "note": "01_buildings.gpkg NOT FOUND -- not substituted, not skipped",
            })
            total_results += n_results
            continue

        n_gpkg, table_name = count_gpkg_rows(gpkg_path)
        diff = n_results - n_gpkg
        whole = (diff == 0)

        print(f"{cell}: 05_results.csv rows={n_results}  01_buildings.gpkg[{table_name}] rows={n_gpkg}  "
              f"diff={diff}  whole={whole}  gpkg={gpkg_path}")

        rows.append({
            "cell": cell,
            "n_rows_05_results": n_results,
            "n_buildings_gpkg": n_gpkg,
            "difference": diff,
            "whole": whole,
            "gpkg_path": gpkg_path,
            "note": "",
        })
        total_results += n_results

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    fieldnames = ["cell", "n_rows_05_results", "n_buildings_gpkg", "difference", "whole", "gpkg_path", "note"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print()
    print("=== FLEET TOTAL (sum of n_rows_05_results across the 12 cells) ===")
    print(f"total = {total_results}")

    print()
    print("=== CELLS WHERE COUNTS DIFFER ===")
    diffs = [r for r in rows if r["difference"] not in (0, None)]
    if diffs:
        for r in diffs:
            print(f"  {r['cell']}: difference={r['difference']} (n_results={r['n_rows_05_results']}, "
                  f"n_gpkg={r['n_buildings_gpkg']})")
    else:
        print("  none")

    print()
    print("=== CELLS NOT FOUND / NOT WHOLE ===")
    not_whole = [r for r in rows if not r["whole"]]
    if not_whole:
        for r in not_whole:
            print(f"  {r['cell']}: {r['note'] or 'difference != 0'}")
    else:
        print("  none -- every cell is whole")


if __name__ == "__main__":
    main()
