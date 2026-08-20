"""T01 of PLAN_gap-decomposition-2026-08-19.md.

Decompose the 48 layout_assign .sql files on disk (scratchpad/open03-untrimmed-sample/)
by EnergyPlus end use, reconcile each building's end-use total against the join CSV's
total_eui_kwh_m2 * floor_area_m2 within 2%, then report the sample-wide split and the
MidriseApartment vs office comparison.

Reads only. Writes:
  - openubem/outputs/comparisons/open03_enduse_by_building.csv
Reuses the production ABUPS "End Uses" query pattern at
openubem/results/parser.py:629-637 (TabularDataWithStrings, ReportName=
'AnnualBuildingUtilityPerformanceSummary', TableName='End Uses'), extended here to sum
across all fuel columns per RowName (that function only sums Electricity for two rows;
this script needs the full per-end-use energy total across all fuels).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
JOIN_CSV = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open03_untrimmed_sample_join.csv"
SQL_ROOT = REPO_ROOT / "scratchpad" / "open03-untrimmed-sample"
OUT_CSV = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open03_enduse_by_building.csv"

GJ_TO_KWH = 277.7778

END_USE_ROWS = [
    "Heating", "Cooling", "Interior Lighting", "Interior Equipment",
    "Water Systems", "Fans", "Pumps",
]

# Query pattern reused from openubem/results/parser.py:629-637 (ABUPS "End Uses"
# cross-check), extended to all RowName categories and all fuel ColumnNames (that
# function's query is scoped to two RowNames and ColumnName='Electricity' only).
END_USE_QUERY = """
SELECT RowName, COALESCE(SUM(CAST(Value AS REAL)), 0.0) AS gj
FROM TabularDataWithStrings
WHERE ReportName = 'AnnualBuildingUtilityPerformanceSummary'
  AND TableName = 'End Uses'
  AND Units = 'GJ'
  AND RowName IN ({placeholders})
GROUP BY RowName
"""


def extract_end_uses(sql_path: Path) -> dict[str, float] | None:
    if not sql_path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
        rows = ["Total End Uses"] + END_USE_ROWS
        placeholders = ",".join("?" for _ in rows)
        q = END_USE_QUERY.format(placeholders=placeholders)
        result = dict(conn.execute(q, rows).fetchall())
        conn.close()
    except sqlite3.Error as exc:
        return {"_error": str(exc)}
    out = {}
    for r in END_USE_ROWS:
        out[r] = result.get(r, 0.0) * GJ_TO_KWH
    out["Total End Uses"] = result.get("Total End Uses", 0.0) * GJ_TO_KWH
    return out


def main() -> None:
    join = pd.read_csv(JOIN_CSV)
    print(f"[T01] join CSV rows: {len(join)}")

    records = []
    n_reconciled = 0
    worst_err = 0.0
    worst_row = None
    n_extract_fail = 0

    for _, row in join.iterrows():
        osm_id = row["osm_id"]
        cell = row["cell"]
        safe_id = osm_id.replace("/", "_")
        sql_path = SQL_ROOT / cell / "sim" / safe_id / "eplusout.sql"

        eu = extract_end_uses(sql_path)
        rec = {
            "cell": cell,
            "osm_id": osm_id,
            "archetype_id": row["archetype_id"],
            "floor_area_m2": row["floor_area_m2"],
            "total_eui_kwh_m2": row["total_eui_kwh_m2"],
            "gap_pct": row["gap_pct"],
        }

        if eu is None:
            rec["extract_status"] = "file_missing"
            n_extract_fail += 1
            records.append(rec)
            continue
        if "_error" in eu:
            rec["extract_status"] = f"sql_error:{eu['_error']}"
            n_extract_fail += 1
            records.append(rec)
            continue

        expected_kwh = row["total_eui_kwh_m2"] * row["floor_area_m2"]
        extracted_total = eu["Total End Uses"]
        if expected_kwh > 0:
            rel_err = abs(extracted_total - expected_kwh) / expected_kwh
        else:
            rel_err = float("nan")

        rec["extract_status"] = "ok"
        rec["extracted_total_kwh"] = extracted_total
        rec["expected_total_kwh"] = expected_kwh
        rec["reconcile_rel_err_pct"] = rel_err * 100 if rel_err == rel_err else None
        rec["reconciled_within_2pct"] = bool(rel_err <= 0.02) if rel_err == rel_err else False
        for r in END_USE_ROWS:
            rec[r.replace(" ", "_")] = eu[r]

        if rec["reconciled_within_2pct"]:
            n_reconciled += 1
        if rel_err == rel_err and rel_err > worst_err:
            worst_err = rel_err
            worst_row = f"{cell}/{osm_id}"

        records.append(rec)

    df = pd.DataFrame.from_records(records)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    n_total = len(df)
    print(f"[T01] extraction failures (file missing / sql error): {n_extract_fail}/{n_total}")
    print(f"[T01] RECONCILIATION: {n_reconciled}/{n_total - n_extract_fail} extracted rows reconcile "
          f"within 2% (Total End Uses vs total_eui_kwh_m2 * floor_area_m2)")
    print(f"[T01] worst reconciliation error: {worst_err*100:.4f}% at {worst_row}")

    ok = df[df["extract_status"] == "ok"].copy()
    end_use_cols = [r.replace(" ", "_") for r in END_USE_ROWS]

    def split_pct(sub: pd.DataFrame, label: str) -> None:
        n = len(sub)
        total = sub[end_use_cols].sum().sum()
        print(f"[T01] --- {label} (n={n}) --- total kWh = {total:.1f}")
        for c in end_use_cols:
            s = sub[c].sum()
            pct = 100 * s / total if total > 0 else float("nan")
            print(f"[T01]   {c}: {pct:.2f}%  ({s:.1f} kWh)")

    split_pct(ok, "ALL 48 (extracted rows)")

    midrise = ok[ok["archetype_id"] == "MidriseApartment"]
    office = ok[ok["archetype_id"].isin(["SmallOffice", "MediumOffice", "LargeOffice"])]
    split_pct(midrise, "MidriseApartment")
    split_pct(office, "Office (Small+Medium+Large)")

    li_eq_pct_all = 100 * (ok["Interior_Lighting"].sum() + ok["Interior_Equipment"].sum()) / ok[end_use_cols].sum().sum()
    print(f"[T01] lighting+equipment share of total, all extracted (n={len(ok)}): {li_eq_pct_all:.2f}%")

    print(f"[T01] wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
