"""T01 of PLAN_five-items-2026-08-20-late.md -- OPEN-61: where does the District Heating
column come from, and how big is it on the 48 surviving untrimmed `layout_assign` samples?

Two parts, per the plan:
  (a) mechanism -- tested directly with a one-building scratch IDF edit (not part of this
      script's run; see scratchpad/open61_c2_experiment/ and the T01 report for that result).
  (b) sizing -- this script. For each of the 48 buildings in
      scratchpad/open03-untrimmed-sample/<cell>/sim/<osm_id>/eplusout.sql, read the ABUPS
      `End Uses` table for every fuel column, and read the same building's production total
      through openubem.results.parser.parse_building() (never a formula written here).

Controls (pre-registered in the T01 report before this script ran):
  C1 -- way_1008727470 (austin_centre) reproduces 0.72 GJ District Heating at both the
        Water Systems row and the Total End Uses row.
  C2 -- for every building and every fuel column, the individual end-use rows sum to the
        Total End Uses row for that column within 0.5%. Failing buildings are named and
        excluded from the per-cell statistics.
  C3 -- the count of buildings whose District Heating Total End Uses is exactly 0.00 GJ.

Output: openubem/outputs/comparisons/open61_district_source.csv, one row per building
(48 rows, all attempted; a `c2_pass` column flags exclusions -- none are dropped from the
CSV itself, only from the report's per-cell statistics).
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from openubem.results.parser import parse_building  # noqa: E402

SAMPLE_ROOT = REPO / "scratchpad" / "open03-untrimmed-sample"
OUT_CSV = REPO / "openubem" / "outputs" / "comparisons" / "open61_district_source.csv"

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]

GJ_TO_KWH = 1e9 / 3.6e6  # 277.7778
FUEL_COLUMNS = [
    "Electricity", "Natural Gas", "Gasoline", "Diesel", "Coal", "Fuel Oil No 1",
    "Fuel Oil No 2", "Propane", "Other Fuel 1", "Other Fuel 2",
    "District Cooling", "District Heating",
]
END_USE_ROWS = [
    "Heating", "Cooling", "Interior Lighting", "Exterior Lighting", "Interior Equipment",
    "Exterior Equipment", "Fans", "Pumps", "Heat Rejection", "Humidification",
    "Heat Recovery", "Water Systems", "Refrigeration", "Generators",
]


def read_end_uses(sql_path: Path) -> dict[str, dict[str, float]]:
    """Return {fuel_column: {row_name: value_gj}} for the ABUPS `End Uses` table,
    including the `Total End Uses` row, read straight from TabularDataWithStrings."""
    con = sqlite3.connect(str(sql_path))
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT RowName, ColumnName, Value FROM TabularDataWithStrings "
            "WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' "
            "AND TableName='End Uses' AND ColumnName != 'Water'"
        )
        rows = cur.fetchall()
    finally:
        con.close()
    out: dict[str, dict[str, float]] = {c: {} for c in FUEL_COLUMNS}
    for row_name, col_name, value in rows:
        if col_name not in out or not row_name:
            continue
        try:
            out[col_name][row_name] = float(value)
        except ValueError:
            continue
    return out


def check_c2(end_uses: dict[str, dict[str, float]]) -> tuple[bool, list[str]]:
    """Per fuel column: individual END_USE_ROWS must sum to Total End Uses within 0.5%."""
    failures = []
    for col in FUEL_COLUMNS:
        rows = end_uses.get(col, {})
        total = rows.get("Total End Uses")
        if total is None:
            failures.append(f"{col}: no Total End Uses row")
            continue
        individual_sum = sum(rows.get(r, 0.0) for r in END_USE_ROWS)
        if total == 0.0:
            if abs(individual_sum) > 1e-6:
                failures.append(f"{col}: total=0.00 but rows sum to {individual_sum:.4f}")
            continue
        rel_err = abs(individual_sum - total) / abs(total)
        if rel_err > 0.005:
            failures.append(f"{col}: rows sum {individual_sum:.4f} vs total {total:.4f} ({rel_err:.2%})")
    return (len(failures) == 0), failures


def build_manifest_row(cell: str, osm_id_dir: str) -> pd.Series | None:
    manifest_path = SAMPLE_ROOT / cell / "step3_layout_assign" / "03_idf_manifest.parquet"
    manifest = pd.read_parquet(manifest_path)
    osm_id_slash = osm_id_dir.replace("_", "/", 1)
    match = manifest[manifest["osm_id"] == osm_id_slash]
    if match.empty:
        return None
    row = match.iloc[0].copy()
    row["levels"] = float("nan")
    row["height_m"] = float("nan")
    row["footprint_area_m2"] = 1.0  # unused: .eio present -> resolve_simulated_floor_area uses eio_simulated
    return row


def main() -> None:
    records = []
    c1_pass = None
    for cell in CELLS:
        sim_dir = SAMPLE_ROOT / cell / "sim"
        building_dirs = sorted(p for p in sim_dir.iterdir() if p.is_dir())
        for bdir in building_dirs:
            osm_id_dir = bdir.name
            sql_path = bdir / "eplusout.sql"
            rec = {
                "cell": cell, "osm_id": osm_id_dir, "sql_path": str(sql_path),
            }
            if not sql_path.exists():
                rec["status"] = "no_sql"
                records.append(rec)
                continue

            end_uses = read_end_uses(sql_path)
            dh_water_gj = end_uses["District Heating"].get("Water Systems", 0.0)
            dh_total_gj = end_uses["District Heating"].get("Total End Uses", 0.0)

            if cell == "austin_centre" and osm_id_dir == "way_1008727470":
                c1_pass = (round(dh_water_gj, 2) == 0.72) and (round(dh_total_gj, 2) == 0.72)

            c2_pass, c2_failures = check_c2(end_uses)

            total_end_uses_all_fuels_gj = sum(
                end_uses[c].get("Total End Uses", 0.0) for c in FUEL_COLUMNS
            )
            dh_share_of_total_end_uses = (
                dh_total_gj / total_end_uses_all_fuels_gj if total_end_uses_all_fuels_gj else 0.0
            )

            manifest_row = build_manifest_row(cell, osm_id_dir)
            if manifest_row is None:
                rec.update({
                    "status": "no_manifest_row",
                    "dh_water_gj": dh_water_gj, "dh_total_gj": dh_total_gj,
                    "dh_total_kwh": dh_total_gj * GJ_TO_KWH,
                    "total_end_uses_all_fuels_gj": total_end_uses_all_fuels_gj,
                    "dh_share_of_total_end_uses": dh_share_of_total_end_uses,
                    "c2_pass": c2_pass, "c2_failures": "; ".join(c2_failures),
                })
                records.append(rec)
                continue

            parsed = parse_building(sql_path, None, manifest_row)
            parser_total_eui = parsed.get("total_eui_kwh_m2")
            parser_status = parsed.get("parse_status")
            floor_area_m2 = parsed.get("floor_area_m2")
            parser_total_kwh = (
                parser_total_eui * floor_area_m2
                if (parser_total_eui is not None and floor_area_m2)
                else None
            )
            dh_share_of_parser_total = (
                (dh_total_gj * GJ_TO_KWH) / parser_total_kwh
                if parser_total_kwh else None
            )

            rec.update({
                "status": "ok",
                "dh_water_gj": dh_water_gj,
                "dh_total_gj": dh_total_gj,
                "dh_total_kwh": dh_total_gj * GJ_TO_KWH,
                "total_end_uses_all_fuels_gj": total_end_uses_all_fuels_gj,
                "dh_share_of_total_end_uses": dh_share_of_total_end_uses,
                "parser_status": parser_status,
                "parser_total_eui_kwh_m2": parser_total_eui,
                "parser_floor_area_m2": floor_area_m2,
                "parser_total_kwh": parser_total_kwh,
                "dh_share_of_parser_total": dh_share_of_parser_total,
                "c2_pass": c2_pass,
                "c2_failures": "; ".join(c2_failures),
            })
            records.append(rec)

    df = pd.DataFrame.from_records(records)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    print(f"C1 (way_1008727470 reproduces 0.72/0.72): {c1_pass}")
    print(f"total buildings: {len(df)}")
    print(f"c2_pass count: {int(df['c2_pass'].sum()) if 'c2_pass' in df else 'n/a'}")
    n_zero = int((df["dh_total_gj"].round(2) == 0.0).sum()) if "dh_total_gj" in df else -1
    print(f"C3 (count with District Heating Total End Uses == 0.00 GJ): {n_zero} / {len(df)}")
    print("\nPer-cell district-heating share of Total End Uses (c2_pass rows only):")
    ok = df[(df["status"] == "ok") & (df["c2_pass"])]
    for cell, grp in ok.groupby("cell"):
        print(
            f"  {cell}: n={len(grp)}, median share={grp['dh_share_of_total_end_uses'].median():.4%}, "
            f"n_zero={(grp['dh_total_gj'].round(2) == 0.0).sum()}"
        )
    print(f"\nWrote {OUT_CSV}")


if __name__ == "__main__":
    main()
