"""V03 part C: Extract reference EUIs from fetched cluster SQL results.

Reads ref_out/<stem>/eplusout.sql for each entry in fleet.lst.
Uses TabularDataWithStrings AnnualBuildingUtilityPerformanceSummary per-end-use rows
divided by conditioned floor area from ref_inventory.csv.
Output: %TEMP%/ubem_validation/level2/reference_eui.parquet
        (filename, total_site_eui_kwh_m2, heating_eui, cooling_eui,
         lighting_eui, equipment_eui, other_eui, n_severe, status)
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

OUT_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "level2"
REF_OUT = OUT_BASE / "ref_out"
INVENTORY_CSV = OUT_BASE / "ref_inventory.csv"
OUT_PARQUET = OUT_BASE / "reference_eui.parquet"

GJ_TO_KWH = 1e9 / 3.6e6

END_USE_ROW_MAP = {
    "heating_gj": "Heating",
    "cooling_gj": "Cooling",
    "lighting_gj": "Interior Lighting",
    "equipment_gj": "Interior Equipment",
}

FUEL_COLS = ["Electricity", "Natural Gas", "Additional Fuel", "District Cooling",
             "District Heating Water", "District Heating Steam",
             "Steam", "Water"]


def _query_end_uses(sql_path: Path) -> dict[str, float]:
    conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
    try:
        rows = conn.execute("""
            SELECT RowName, ColumnName, CAST(Value AS REAL)
            FROM TabularDataWithStrings
            WHERE ReportName = 'AnnualBuildingUtilityPerformanceSummary'
              AND TableName = 'End Uses'
              AND Units = 'GJ'
        """).fetchall()
    finally:
        conn.close()

    totals: dict[str, float] = {}
    for row_name, col_name, val in rows:
        if col_name not in FUEL_COLS:
            continue
        totals[row_name] = totals.get(row_name, 0.0) + (val or 0.0)
    return totals


def _parse_err_severe(err_path: Path) -> int:
    if not err_path.exists():
        return -1
    text = err_path.read_text(errors="replace")
    import re
    matches = re.findall(r"(\d+)\s+Severe", text)
    return int(matches[-1]) if matches else 0


def main() -> None:
    inv = pd.read_csv(INVENTORY_CSV)
    inv = inv.set_index("filename")

    fleet_lst = REF_OUT / "fleet.lst"
    if not fleet_lst.exists():
        print(f"[V03-eui] ERROR: {fleet_lst} not found — run v03_fetch.py first.")
        return

    stems = [l.strip() for l in fleet_lst.read_text().splitlines() if l.strip()]
    print(f"[V03-eui] {len(stems)} buildings to process")

    records = []
    for stem in stems:
        fname = stem + ".idf"
        bdir = REF_OUT / stem
        sql_path = bdir / "eplusout.sql"
        end_path = bdir / "eplusout.end"
        err_path = bdir / "eplusout.err"

        status = "failed"
        if end_path.exists() and "Completed Successfully" in end_path.read_text(errors="replace"):
            status = "success"

        n_severe = _parse_err_severe(err_path)

        if fname not in inv.index:
            print(f"  [WARN] {fname} not in inventory — skipping")
            continue
        floor_area = float(inv.loc[fname, "conditioned_floor_area_m2"])

        if status != "success" or not sql_path.exists():
            records.append({
                "filename": fname, "status": status,
                "conditioned_floor_area_m2": floor_area, "n_severe": n_severe,
                "heating_eui_kwh_m2": None, "cooling_eui_kwh_m2": None,
                "lighting_eui_kwh_m2": None, "equipment_eui_kwh_m2": None,
                "other_eui_kwh_m2": None, "total_site_eui_kwh_m2": None,
            })
            continue

        try:
            eu = _query_end_uses(sql_path)
        except Exception as exc:
            print(f"  [ERROR] {stem}: {exc}")
            records.append({
                "filename": fname, "status": "parse_error",
                "conditioned_floor_area_m2": floor_area, "n_severe": n_severe,
                "heating_eui_kwh_m2": None, "cooling_eui_kwh_m2": None,
                "lighting_eui_kwh_m2": None, "equipment_eui_kwh_m2": None,
                "other_eui_kwh_m2": None, "total_site_eui_kwh_m2": None,
            })
            continue

        def _eui(row_name: str) -> float:
            return eu.get(row_name, 0.0) * GJ_TO_KWH / floor_area

        heat = _eui("Heating")
        cool = _eui("Cooling")
        light = _eui("Interior Lighting")
        equip = _eui("Interior Equipment")

        known_rows = {"Heating", "Cooling", "Interior Lighting", "Interior Equipment"}
        other_gj = sum(v for k, v in eu.items() if k not in known_rows)
        other = other_gj * GJ_TO_KWH / floor_area
        total = heat + cool + light + equip + other

        records.append({
            "filename": fname, "status": status,
            "conditioned_floor_area_m2": floor_area, "n_severe": n_severe,
            "heating_eui_kwh_m2": round(heat, 3),
            "cooling_eui_kwh_m2": round(cool, 3),
            "lighting_eui_kwh_m2": round(light, 3),
            "equipment_eui_kwh_m2": round(equip, 3),
            "other_eui_kwh_m2": round(other, 3),
            "total_site_eui_kwh_m2": round(total, 3),
        })
        print(f"  {stem}: total={total:.1f} kWh/m2  (H={heat:.1f} C={cool:.1f} L={light:.1f} E={equip:.1f} O={other:.1f})")

    df = pd.DataFrame(records)
    success_count = (df["status"] == "success").sum()
    print(f"\n[V03-eui] {success_count}/{len(df)} successful")

    fail_mask = df["status"] != "success"
    if fail_mask.any():
        print("[V03-eui] FAILURES:")
        for _, r in df[fail_mask].iterrows():
            print(f"  {r['filename']}  status={r['status']}  n_severe={r['n_severe']}")

    eui_vals = df["total_site_eui_kwh_m2"].dropna()
    if len(eui_vals) > 0:
        out_of_range = eui_vals[(eui_vals < 10) | (eui_vals > 3000)]
        if len(out_of_range) > 0:
            print(f"[V03-eui] WARNING: {len(out_of_range)} EUI values outside [10, 3000]:")
            print(out_of_range.to_string())

    df.to_parquet(OUT_PARQUET, index=False)
    print(f"\n[V03-eui] Parquet written: {OUT_PARQUET}  ({len(df)} rows)")
    print("[V03-eui] DONE")


if __name__ == "__main__":
    main()
