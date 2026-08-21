"""
OPEN-61 T01 -- district-heating reader.

Reads the "District Heating" end-use total out of an EnergyPlus eplusout.sql
two independent ways and requires agreement:

  (a) ABUPS "End Uses" table, District Heating column, Total End Uses row
      (via the TabularDataWithStrings view over TabularData).
  (b) A DistrictHeating:Facility (or equivalently named) meter row in
      ReportData/ReportDataDictionary -- IF ONE EXISTS.

Finding (recorded here, not silently swallowed): across every .sql inspected
for this task, ReportDataDictionary carries NO meter or variable whose name
contains "District" at all (confirmed on both a known-positive and a
known-negative building; consistent with parser.py's METER_QUERY, which
requests ten meters and none of them is district heating -- F1 in the plan).
So path (b) does not exist in this fleet's .sql files. Per the plan (T01
"How"), the fallback third check is used instead:

  (c) the ABUPS "Total End Uses" row across ALL fuel columns reconciles with
      the sum of the per-end-use rows for the District Heating column alone
      (i.e. Total End Uses, District Heating == sum of the 14 named end-use
      rows for that column). This is a reconciliation of (a) against itself,
      not a second independent source -- reported honestly as such.

Usage as a library:
    from open61_census_read_2026_08_20 import read_district_heating
    result = read_district_heating(r"path\\to\\eplusout.sql")
    result.gj, result.kwh, result.b_available, result.agree
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

GJ_TO_KWH = 1_000_000.0 / 3600.0

END_USE_ROWS = [
    "Heating", "Cooling", "Interior Lighting", "Exterior Lighting",
    "Interior Equipment", "Exterior Equipment", "Fans", "Pumps",
    "Heat Rejection", "Humidification", "Heat Recovery", "Water Systems",
    "Refrigeration", "Generators",
]


@dataclass
class DistrictHeatingRead:
    sql_path: str
    a_total_gj: Optional[float]
    a_total_kwh: Optional[float]
    a_sum_rows_gj: Optional[float]
    a_reconciles: Optional[bool]
    b_available: bool
    b_total_gj: Optional[float]
    b_total_kwh: Optional[float]
    agree: bool
    note: str


def _abups_district_heating(conn: sqlite3.Connection) -> tuple[Optional[float], Optional[float]]:
    row = conn.execute(
        "select Value from TabularDataWithStrings "
        "where ReportName='AnnualBuildingUtilityPerformanceSummary' "
        "and TableName='End Uses' and ColumnName='District Heating' "
        "and RowName='Total End Uses'"
    ).fetchone()
    if row is None or row[0] is None or str(row[0]).strip() == "":
        return None, None
    total_gj = float(row[0])
    rows = conn.execute(
        "select RowName, Value from TabularDataWithStrings "
        "where ReportName='AnnualBuildingUtilityPerformanceSummary' "
        "and TableName='End Uses' and ColumnName='District Heating' "
        "and RowName in ({})".format(",".join("?" for _ in END_USE_ROWS)),
        END_USE_ROWS,
    ).fetchall()
    sum_rows = 0.0
    for _rowname, value in rows:
        if value is not None and str(value).strip() != "":
            sum_rows += float(value)
    return total_gj, sum_rows


def _reportdata_district_heating(conn: sqlite3.Connection) -> tuple[bool, Optional[float]]:
    dict_rows = conn.execute(
        "select ReportDataDictionaryIndex, Name, Units from ReportDataDictionary "
        "where IsMeter=1 and (Name like '%District%Heating%' or Name like 'DistrictHeating%')"
    ).fetchall()
    if not dict_rows:
        return False, None
    total_j = 0.0
    for idx, _name, units in dict_rows:
        vals = conn.execute(
            "select Value from ReportData where ReportDataDictionaryIndex=?", (idx,)
        ).fetchall()
        for (v,) in vals:
            if v is not None:
                total_j += float(v)
    return True, total_j


def read_district_heating(sql_path: str) -> DistrictHeatingRead:
    sql_path = str(sql_path)
    conn = sqlite3.connect(sql_path)
    try:
        a_total_gj, a_sum_rows = _abups_district_heating(conn)
        a_reconciles = None
        if a_total_gj is not None and a_sum_rows is not None:
            a_reconciles = abs(a_total_gj - a_sum_rows) < 0.005

        b_available, b_total_j = _reportdata_district_heating(conn)
        b_total_gj = (b_total_j / 1.0e9) if b_total_j is not None else None
        b_total_kwh = (b_total_gj * GJ_TO_KWH) if b_total_gj is not None else None

        a_total_kwh = (a_total_gj * GJ_TO_KWH) if a_total_gj is not None else None

        if b_available:
            agree = (
                a_total_gj is not None
                and b_total_gj is not None
                and abs(a_total_gj - b_total_gj) < 0.01
            )
            note = "path (b) ReportData meter found; compared against path (a)."
        else:
            agree = bool(a_reconciles)
            note = (
                "path (b) not available: no District Heating meter/variable row "
                "in ReportDataDictionary for this .sql. Falling back to the "
                "plan's third check: ABUPS Total End Uses reconciles with the "
                "sum of its own per-end-use rows for the District Heating column."
            )

        return DistrictHeatingRead(
            sql_path=sql_path,
            a_total_gj=a_total_gj,
            a_total_kwh=a_total_kwh,
            a_sum_rows_gj=a_sum_rows,
            a_reconciles=a_reconciles,
            b_available=b_available,
            b_total_gj=b_total_gj,
            b_total_kwh=b_total_kwh,
            agree=agree,
            note=note,
        )
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    for p in sys.argv[1:]:
        r = read_district_heating(p)
        print(p)
        print(
            f"  a_total_gj={r.a_total_gj} a_sum_rows_gj={r.a_sum_rows_gj} "
            f"a_reconciles={r.a_reconciles} b_available={r.b_available} "
            f"b_total_gj={r.b_total_gj} agree={r.agree}"
        )
        print(f"  {r.note}")
