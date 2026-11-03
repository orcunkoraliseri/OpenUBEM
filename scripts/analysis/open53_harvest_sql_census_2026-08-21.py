"""T01 (PLAN_ten-live-items-2026-08-21): census the SQL contents of every
directory in the E02 harvest. Standalone, read-only. No production code touched.
"""
import sqlite3
from pathlib import Path
import csv

HARVEST_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest")
OUT_CSV = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open53_harvest_sql_census_2026-08-21.csv")

MODES = ["fast_zone", "layout_assign", "building", "floor", "auto"]  # longest suffix first


def split_cell_mode(dirname: str):
    for m in MODES:
        suffix = "_" + m
        if dirname.endswith(suffix):
            return dirname[: -len(suffix)], m
    return dirname, "UNKNOWN"


def census_sql(sql_path: Path):
    row = {
        "n_dict_rows": None,
        "n_zone_keys": None,
        "n_abups_enduse_rows": None,
        "has_elec_facility": None,
        "has_gas_facility": None,
        "sql_open_error": "",
    }
    try:
        con = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM ReportDataDictionary")
        row["n_dict_rows"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM ReportDataDictionary WHERE Name LIKE 'Zone %'")
        row["n_zone_keys"] = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM TabularDataWithStrings "
            "WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' AND TableName='End Uses'"
        )
        row["n_abups_enduse_rows"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM ReportDataDictionary WHERE Name='Electricity:Facility'")
        row["has_elec_facility"] = cur.fetchone()[0] > 0
        cur.execute("SELECT COUNT(*) FROM ReportDataDictionary WHERE Name='NaturalGas:Facility'")
        row["has_gas_facility"] = cur.fetchone()[0] > 0
        con.close()
    except Exception as e:  # noqa: BLE001
        row["sql_open_error"] = f"{type(e).__name__}: {e}"
    return row


def main():
    rows = []
    cellmode_dirs = sorted([d for d in HARVEST_ROOT.iterdir() if d.is_dir()])
    for cm_dir in cellmode_dirs:
        cell, mode = split_cell_mode(cm_dir.name)
        stem_dirs = sorted([d for d in cm_dir.iterdir() if d.is_dir()])
        for stem_dir in stem_dirs:
            stem = stem_dir.name
            sql_p = stem_dir / "eplusout.sql"
            end_p = stem_dir / "eplusout.end"
            err_p = stem_dir / "eplusout.err"
            eio_p = stem_dir / "eplusout.eio"
            has_sql = sql_p.is_file()
            row = {
                "cell": cell,
                "mode": mode,
                "stem": stem,
                "has_sql": has_sql,
                "has_end": end_p.is_file(),
                "has_err": err_p.is_file(),
                "has_eio": eio_p.is_file(),
                "sql_bytes": sql_p.stat().st_size if has_sql else 0,
            }
            if has_sql:
                row.update(census_sql(sql_p))
            else:
                row.update(
                    {
                        "n_dict_rows": None,
                        "n_zone_keys": None,
                        "n_abups_enduse_rows": None,
                        "has_elec_facility": None,
                        "has_gas_facility": None,
                        "sql_open_error": "",
                    }
                )
            rows.append(row)

    fieldnames = [
        "cell", "mode", "stem", "has_sql", "has_end", "has_err", "has_eio", "sql_bytes",
        "n_dict_rows", "n_zone_keys", "n_abups_enduse_rows", "has_elec_facility",
        "has_gas_facility", "sql_open_error",
    ]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    # ---- summary ----
    n_total = len(rows)
    n_has_sql = sum(1 for r in rows if r["has_sql"])
    n_any_abups = sum(1 for r in rows if r["has_sql"] and (r["n_abups_enduse_rows"] or 0) > 0)
    n_any_zonekey = sum(1 for r in rows if r["has_sql"] and (r["n_zone_keys"] or 0) > 0)
    n_open_error = sum(1 for r in rows if r["sql_open_error"])
    n_end_missing = sum(1 for r in rows if not r["has_end"])
    n_end_missing_sql_present = sum(1 for r in rows if not r["has_end"] and r["has_sql"])
    n_end_missing_sql_absent = sum(1 for r in rows if not r["has_end"] and not r["has_sql"])

    print(f"n_total_dirs={n_total}")
    print(f"n_has_sql={n_has_sql}")
    print(f"n_sql_open_error={n_open_error}")
    print(f"n_any_abups_enduse_row={n_any_abups}")
    print(f"n_any_zone_key={n_any_zonekey}")
    print(f"n_end_missing={n_end_missing}")
    print(f"n_end_missing_and_sql_present={n_end_missing_sql_present}")
    print(f"n_end_missing_and_sql_absent={n_end_missing_sql_absent}")

    print("\n--- cross-tab by mode (has_sql / any_abups / any_zonekey) ---")
    modes_present = sorted(set(r["mode"] for r in rows))
    for m in modes_present:
        sub = [r for r in rows if r["mode"] == m]
        n = len(sub)
        hs = sum(1 for r in sub if r["has_sql"])
        ab = sum(1 for r in sub if r["has_sql"] and (r["n_abups_enduse_rows"] or 0) > 0)
        zk = sum(1 for r in sub if r["has_sql"] and (r["n_zone_keys"] or 0) > 0)
        print(f"mode={m:15s} n={n:5d} has_sql={hs:5d} any_abups={ab:5d} any_zonekey={zk:5d}")

    print("\n--- cross-tab by cell (has_sql / any_abups / any_zonekey) ---")
    cells_present = sorted(set(r["cell"] for r in rows))
    for c in cells_present:
        sub = [r for r in rows if r["cell"] == c]
        n = len(sub)
        hs = sum(1 for r in sub if r["has_sql"])
        ab = sum(1 for r in sub if r["has_sql"] and (r["n_abups_enduse_rows"] or 0) > 0)
        zk = sum(1 for r in sub if r["has_sql"] and (r["n_zone_keys"] or 0) > 0)
        print(f"cell={c:15s} n={n:5d} has_sql={hs:5d} any_abups={ab:5d} any_zonekey={zk:5d}")


if __name__ == "__main__":
    main()
