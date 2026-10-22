"""Hourly and peak post-processor (IMP T08): hourly heating, cooling, electricity and gas
from an EnergyPlus eplusout.sql, average winter and summer day profiles, annual peak hour.

Only sqlite3, numpy and pandas are needed, so the file also runs on its own on Speed.
A series is NaN with source "absent" when the .sql holds nothing hourly for it.
T15: district_hot_water_kwh (hourly WaterSystems:DistrictHeating meter) is reported apart; the
adopted view is heating, cooling, electricity and gas (COLUMNS) with that series left out. The
sidecar also carries run_period_kwh, the same run's Run Period meters per series.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

J_TO_KWH = 1.0 / 3.6e6

COLUMNS = ("heating_kwh", "cooling_kwh", "electricity_kwh", "gas_kwh")
DISTRICT_COLUMN = "district_hot_water_kwh"
ALL_COLUMNS = COLUMNS + (DISTRICT_COLUMN,)

HEATING_METERS = ("Heating:Electricity", "Heating:NaturalGas", "Heating:DistrictHeating")
COOLING_METERS = ("Cooling:Electricity", "Cooling:DistrictCooling", "Cooling:DistrictHeating")
IDEAL_HEATING = "Zone Ideal Loads Zone Total Heating Energy"
IDEAL_COOLING = "Zone Ideal Loads Zone Total Cooling Energy"
ZONE_ELECTRICITY = ("Zone Lights Electricity Energy", "Zone Electric Equipment Electricity Energy")
FACILITY_ELECTRICITY = "Electricity:Facility"
FACILITY_GAS = "NaturalGas:Facility"
DISTRICT_HOT_WATER = "WaterSystems:DistrictHeating"

WINTER_MONTHS = (12, 1, 2)
SUMMER_MONTHS = (6, 7, 8)

_NAMES = (
    HEATING_METERS + COOLING_METERS + (IDEAL_HEATING, IDEAL_COOLING)
    + ZONE_ELECTRICITY + (FACILITY_ELECTRICITY, FACILITY_GAS, DISTRICT_HOT_WATER)
)

_SERIES_METERS = {
    "heating_kwh": HEATING_METERS,
    "cooling_kwh": COOLING_METERS,
    "electricity_kwh": (FACILITY_ELECTRICITY,),
    "gas_kwh": (FACILITY_GAS,),
    DISTRICT_COLUMN: (DISTRICT_HOT_WATER,),
}

_RUN_PERIOD_QUERY = """
SELECT d.Name AS name, SUM(r.Value) AS value
FROM   ReportData r
JOIN   ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
WHERE  d.ReportingFrequency = 'Run Period'
  AND  d.Name IN ({names})
GROUP BY d.Name
"""

_HOURLY_QUERY = """
SELECT t.TimeIndex AS time_index, t.Month AS month, t.Day AS day, t.Hour AS hour,
       d.Name AS name,
       SUM(r.Value * COALESCE(z.Multiplier, 1.0) * COALESCE(z.ListMultiplier, 1.0)) AS value
FROM   ReportData r
JOIN   ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
JOIN   Time t                 ON r.TimeIndex = t.TimeIndex
LEFT JOIN Zones z ON UPPER(z.ZoneName) = REPLACE(UPPER(d.KeyValue), ' IDEAL LOADS AIR SYSTEM', '')
WHERE  d.ReportingFrequency = 'Hourly'
  AND  d.Name IN ({names})
  AND  (t.WarmupFlag IS NULL OR t.WarmupFlag = 0)
GROUP BY t.TimeIndex, d.Name
ORDER BY t.TimeIndex
"""


def _connect(sql_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)


def _wide(sql_path: Path) -> pd.DataFrame:
    query = _HOURLY_QUERY.format(names=",".join("?" * len(_NAMES)))
    conn = _connect(sql_path)
    try:
        long = pd.read_sql_query(query, conn, params=list(_NAMES))
    finally:
        conn.close()
    if long.empty:
        return pd.DataFrame(columns=["month", "day", "hour"])
    long["value"] = long["value"].astype(float) * J_TO_KWH
    wide = long.pivot(index="time_index", columns="name", values="value").sort_index()
    stamp = long.drop_duplicates("time_index").set_index("time_index")[["month", "day", "hour"]]
    return stamp.join(wide)


def _sum_present(wide: pd.DataFrame, names: tuple[str, ...]) -> pd.Series | None:
    present = [n for n in names if n in wide.columns]
    if not present:
        return None
    return wide[present].sum(axis=1, min_count=1)


def _pick(wide: pd.DataFrame, options: list[tuple[str, tuple[str, ...]]]) -> tuple[pd.Series, str]:
    for source, names in options:
        series = _sum_present(wide, names)
        if series is not None:
            return series, source
    return pd.Series(np.nan, index=wide.index), "absent"


def read_hourly(sql_path: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    wide = _wide(Path(sql_path))
    if wide.empty:
        frame = pd.DataFrame(columns=["month", "day", "hour", *ALL_COLUMNS])
        return frame, {c: "absent" for c in ALL_COLUMNS}

    heating, h_src = _pick(wide, [("meter", HEATING_METERS), ("ideal_loads_zone", (IDEAL_HEATING,))])
    cooling, c_src = _pick(wide, [("meter", COOLING_METERS), ("ideal_loads_zone", (IDEAL_COOLING,))])
    electricity, e_src = _pick(wide, [
        ("facility_meter", (FACILITY_ELECTRICITY,)),
        ("zone_lights_equipment", ZONE_ELECTRICITY),
    ])
    gas, g_src = _pick(wide, [("facility_meter", (FACILITY_GAS,))])
    district, d_src = _pick(wide, [("meter", (DISTRICT_HOT_WATER,))])

    frame = wide[["month", "day", "hour"]].copy()
    frame["heating_kwh"] = heating
    frame["cooling_kwh"] = cooling
    frame["electricity_kwh"] = electricity
    frame["gas_kwh"] = gas
    frame[DISTRICT_COLUMN] = district
    frame = frame.reset_index(drop=True)
    sources = {"heating_kwh": h_src, "cooling_kwh": c_src, "electricity_kwh": e_src, "gas_kwh": g_src,
               DISTRICT_COLUMN: d_src}
    return frame, sources


def run_period_kwh(sql_path: Path) -> dict[str, float]:
    names = sorted({m for ms in _SERIES_METERS.values() for m in ms})
    conn = _connect(Path(sql_path))
    try:
        rows = conn.execute(_RUN_PERIOD_QUERY.format(names=",".join("?" * len(names))), names).fetchall()
    finally:
        conn.close()
    by_meter = {n: float(v) * J_TO_KWH for n, v in rows if v is not None}
    out = {}
    for series, meters in _SERIES_METERS.items():
        present = [by_meter[m] for m in meters if m in by_meter]
        out[series] = float(sum(present)) if present else float("nan")
    return out


def annual_kwh(frame: pd.DataFrame) -> dict[str, float]:
    return {c: (float(frame[c].sum()) if frame[c].notna().any() else float("nan"))
            for c in ALL_COLUMNS if c in frame.columns}


def relative_difference(value: float, reference: float) -> float:
    if reference == 0:
        return 0.0 if value == 0 else float("inf")
    return abs(value - reference) / abs(reference)


def day_profile(frame: pd.DataFrame, months: tuple[int, ...]) -> pd.DataFrame:
    sub = frame[frame["month"].isin(months)]
    grouped = sub.groupby("hour")[list(COLUMNS)]
    profile = grouped.mean()
    profile.insert(0, "n_days", grouped.size())
    profile.index.name = "hour"
    return profile.reset_index()


def winter_profile(frame: pd.DataFrame, months: tuple[int, ...] = WINTER_MONTHS) -> pd.DataFrame:
    return day_profile(frame, months)


def summer_profile(frame: pd.DataFrame, months: tuple[int, ...] = SUMMER_MONTHS) -> pd.DataFrame:
    return day_profile(frame, months)


def peak_hour(frame: pd.DataFrame, column: str) -> dict | None:
    series = frame[column]
    if not series.notna().any():
        return None
    i = int(series.idxmax())
    return {
        "column": column,
        "month": int(frame.at[i, "month"]),
        "day": int(frame.at[i, "day"]),
        "hour": int(frame.at[i, "hour"]),
        "kwh": float(series.at[i]),
    }


def peaks(frame: pd.DataFrame) -> dict[str, dict | None]:
    return {c: peak_hour(frame, c) for c in COLUMNS}


def aggregate_site(frames: list[pd.DataFrame]) -> tuple[pd.DataFrame, dict[str, int]]:
    if not frames:
        raise ValueError("no frames to aggregate")
    keys = ["month", "day", "hour"]
    stacked = pd.concat([f.set_index(keys)[list(COLUMNS)] for f in frames])
    site = stacked.groupby(level=keys, sort=False).sum(min_count=1).reset_index()
    counts = {c: int(sum(f[c].notna().any() for f in frames)) for c in COLUMNS}
    return site, counts


def summarise(frame: pd.DataFrame, sources: dict[str, str]) -> dict:
    return {
        "hours": int(len(frame)),
        "sources": sources,
        "annual_kwh": annual_kwh(frame),
        "peak": peaks(frame),
    }



def extract(sql_path: Path, out_csv_gz: Path) -> dict:
    frame, sources = read_hourly(sql_path)
    out_csv_gz = Path(out_csv_gz)
    out_csv_gz.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out_csv_gz, index=False, compression="gzip")
    summary = summarise(frame, sources)
    summary["sql_path"] = str(sql_path)
    summary["run_period_kwh"] = run_period_kwh(sql_path)
    sidecar = out_csv_gz.with_name(out_csv_gz.name.removesuffix(".csv.gz") + ".json")
    sidecar.write_text(json.dumps(summary, indent=1, allow_nan=True), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hourly series from one eplusout.sql")
    sub = parser.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("extract")
    ex.add_argument("sql")
    ex.add_argument("out")
    args = parser.parse_args(argv)
    summary = extract(Path(args.sql), Path(args.out))
    print(json.dumps({"hours": summary["hours"], "sources": summary["sources"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
