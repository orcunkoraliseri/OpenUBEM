import argparse
import csv
import os
import re
import sqlite3
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

LOCALAPPDATA = Path(os.environ["LOCALAPPDATA"])
FLEET06B_OUT = LOCALAPPDATA / "Temp" / "ubem_validation" / "fleet06b_local_2026-09-18" / "out"
HARVEST_ROOT = LOCALAPPDATA / "Temp" / "ubem_validation" / "fleet06c_harvest_2026-09-24"
PV_SCAN_CSV = HARVEST_ROOT / "_pv_scan_2026-09-26.csv"
SUMMARY_CSV = Path("openubem") / "outputs" / "comparisons" / "fleet06c_scenario_summary_2026-09-25.csv"

CELLS = [
    "baseline",
    "lighting",
    "setback",
    "infiltration",
    "lighting+setback",
    "lighting+infiltration",
    "setback+infiltration",
    "lighting+setback+infiltration",
]

CITY_ZONES = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]

PV_ROW_RE = re.compile(r"Photovoltaic Power")
TD_VALUE_RE = re.compile(r"<td[^>]*>\s*([\-\d\.]+)\s*</td>")


def folder_to_osm_id(folder_name):
    return folder_name.replace("_", "/", 1)


def parse_pv_gj(htm_path):
    try:
        with open(htm_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if PV_ROW_RE.search(line):
                    value_line = f.readline()
                    m = TD_VALUE_RE.search(value_line)
                    if m:
                        return float(m.group(1)), "ok"
                    return None, "no_pv_row"
        return None, "no_pv_row"
    except FileNotFoundError:
        return None, "no_htm"
    except OSError:
        return None, "no_htm"


def parse_pv_gj_sql(sql_path):
    try:
        uri = sql_path.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        try:
            cur = conn.cursor()
            cur.execute(
                "select Value from TabularDataWithStrings where TableName='Electric Loads Satisfied' "
                "and RowName='Photovoltaic Power' and ColumnName='Electricity' and Units='GJ'"
            )
            row = cur.fetchone()
            if row is None:
                return None
            return float(row[0])
        finally:
            conn.close()
    except (sqlite3.Error, OSError, ValueError):
        return None


def scan_one_case(args):
    scenario_cell, case_dir_name, case_dir_path = args
    osm_id = folder_to_osm_id(case_dir_name)
    htm_path = case_dir_path / "eplustbl.htm"
    if htm_path.exists():
        pv_gj, status = parse_pv_gj(htm_path)
        if status == "ok":
            return (scenario_cell, osm_id, repr(pv_gj), status)
    else:
        status = "no_htm"

    sql_path = case_dir_path / "eplusout.sql"
    if sql_path.exists():
        pv_gj = parse_pv_gj_sql(sql_path)
        if pv_gj is not None:
            return (scenario_cell, osm_id, repr(pv_gj), "ok_sql")

    return (scenario_cell, osm_id, "", status)


def build_scan_tasks():
    tasks = []
    for cell in CELLS:
        cell_dir = FLEET06B_OUT / cell
        if not cell_dir.is_dir():
            print(f"missing cell dir: {cell_dir}", file=sys.stderr)
            continue
        for case_dir in sorted(cell_dir.iterdir()):
            if case_dir.is_dir():
                tasks.append((cell, case_dir.name, case_dir))
    return tasks


def run_pv_scan():
    tasks = build_scan_tasks()
    print(f"scanning {len(tasks)} cases across {len(CELLS)} cells with a pool of 16")
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=16) as pool:
        for row in pool.map(scan_one_case, tasks, chunksize=64):
            results.append(row)
    elapsed = time.time() - t0
    PV_SCAN_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(PV_SCAN_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["scenario_cell", "osm_id", "pv_gj", "status"])
        writer.writerows(results)
    print(f"wrote {len(results)} rows to {PV_SCAN_CSV} in {elapsed:.1f}s")


def run_table():
    import pandas as pd

    if not PV_SCAN_CSV.exists():
        print(f"missing pv scan file: {PV_SCAN_CSV}", file=sys.stderr)
        sys.exit(1)

    missing = []
    results_by_cell = {}
    for cell in CELLS:
        frames = []
        for zone in CITY_ZONES:
            p = HARVEST_ROOT / cell / zone / "05_results.csv"
            if not p.exists():
                missing.append(str(p))
                continue
            frames.append(pd.read_csv(p))
        if frames:
            results_by_cell[cell] = pd.concat(frames, ignore_index=True)

    if missing:
        print(f"refusing to run --table: {len(missing)} missing 05_results.csv files", file=sys.stderr)
        for m in missing:
            print(f"  missing: {m}", file=sys.stderr)
        sys.exit(1)

    excluded = set()
    per_cell_excluded = {}
    for cell, df in results_by_cell.items():
        bad = df[(df["floor_area_provenance"] == "footprint_fallback") | (df["total_eui_kwh_m2"].isna())]
        ids = set(bad["osm_id"])
        per_cell_excluded[cell] = ids
        excluded |= ids

    print(f"excluded population (union over 8 cells): {len(excluded)} ids")
    for oid in sorted(excluded):
        print(f"  excluded: {oid}")

    pv_scan = pd.read_csv(PV_SCAN_CSV)

    rows = []
    baseline_incl = None
    for cell in CELLS:
        df = results_by_cell[cell]
        df = df[~df["osm_id"].isin(excluded)].copy()
        n_buildings = len(df)
        fleet_area = df["floor_area_m2"].sum()
        kwh_incl = (df["total_eui_kwh_m2"] * df["floor_area_m2"]).sum()
        district_kwh = (df["dhw_district_eui_kwh_m2"].fillna(0) * df["floor_area_m2"]).sum()
        kwh_excl = kwh_incl - district_kwh
        eui_incl = kwh_incl / fleet_area
        eui_excl = kwh_excl / fleet_area

        pv_cell = pv_scan[pv_scan["scenario_cell"] == cell]
        pv_cell = pv_cell[pv_cell["osm_id"].isin(df["osm_id"])]
        n_pv_gt0 = (pv_cell["pv_gj"].apply(lambda v: pd.notna(v) and float(v) > 0)).sum()
        n_pv_unknown = (pv_cell["status"] != "ok").sum() + (n_buildings - len(pv_cell))

        if cell == "baseline":
            baseline_incl = eui_incl

        delta_kwh_m2 = eui_incl - baseline_incl if baseline_incl is not None else 0.0
        delta_pct = (delta_kwh_m2 / baseline_incl * 100.0) if baseline_incl else 0.0

        rows.append({
            "scenario_cell": cell,
            "n_buildings": n_buildings,
            "fleet_area_m2": fleet_area,
            "fleet_eui_incl_district_kwh_m2": eui_incl,
            "fleet_eui_excl_district_kwh_m2": eui_excl,
            "delta_vs_baseline_kwh_m2": delta_kwh_m2,
            "delta_vs_baseline_pct": delta_pct,
            "n_pv_gt0": int(n_pv_gt0),
            "n_pv_unknown": int(n_pv_unknown),
        })

    out_df = pd.DataFrame(rows, columns=[
        "scenario_cell", "n_buildings", "fleet_area_m2",
        "fleet_eui_incl_district_kwh_m2", "fleet_eui_excl_district_kwh_m2",
        "delta_vs_baseline_kwh_m2", "delta_vs_baseline_pct",
        "n_pv_gt0", "n_pv_unknown",
    ])
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(SUMMARY_CSV, index=False)
    print(out_df.to_string(index=False))
    print(f"wrote {SUMMARY_CSV}")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pv-scan", action="store_true")
    group.add_argument("--table", action="store_true")
    args = parser.parse_args()

    if args.pv_scan:
        run_pv_scan()
    elif args.table:
        run_table()


if __name__ == "__main__":
    main()
