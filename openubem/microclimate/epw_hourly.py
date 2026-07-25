"""T02 — EPW hourly body parser (PLAN §7 T02, F-03: no such reader exists in epw_manager.py).

Field indices verified against a real downloaded EPW row (NYC TMYx, 2026-07-23) and the
EnergyPlus Auxiliary Programs "EnergyPlus Weather File (EPW) Data Dictionary" — not guessed,
and not the plan's own (self-flagged-approximate) prose numbering.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_HEADER_LINES = 8

# 1-based EPW data-field index -> (output column, missing-value sentinel).
# Sentinels per the EPW dictionary (each field has its own "missing" convention).
_FIELDS: list[tuple[int, str, float]] = [
    (1, "source_year", None),
    (2, "month", None),
    (3, "day", None),
    (4, "hour", None),
    (7, "dry_bulb_c", 99.9),
    (8, "dew_point_c", 99.9),
    (9, "relative_humidity_pct", 999.0),
    (10, "atmospheric_pressure_pa", 999999.0),
    (13, "horizontal_infrared_wm2", 9999.0),
    (14, "global_horizontal_wm2", 9999.0),
    (15, "direct_normal_wm2", 9999.0),
    (16, "diffuse_horizontal_wm2", 9999.0),
    (21, "wind_direction_deg", 999.0),
    (22, "wind_speed_ms", 999.0),
    (23, "total_sky_cover", 99.0),
    (24, "opaque_sky_cover", 99.0),
]


def read_epw_hourly(epw_path: "Path | str") -> pd.DataFrame:
    """Parse the 8760/8784-row EPW body into a typed hourly DataFrame.

    Index is a DatetimeIndex on a fixed nominal year (2001, or 2000 if the file is a leap
    year / 8784 rows) built from each row's own (month, day, hour) — NOT the EPW row's "year"
    field, which in TMY files is a per-month source-year annotation and is not chronologically
    monotonic across the file (verified: a real TMYx file mixes years 2013-2025 across months).
    EPW hour 1..24 maps to 00:00-23:00 of the stated day (hour 24 -> 23:00 of that day).
    """
    epw_path = Path(epw_path)
    with open(epw_path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()

    data_lines = lines[_HEADER_LINES:]
    n = len(data_lines)
    if n not in (8760, 8784):
        raise ValueError(f"read_epw_hourly: {n} data rows, expected 8760 or 8784: {epw_path}")
    nominal_year = 2000 if n == 8784 else 2001

    raw = np.empty((n, len(_FIELDS)), dtype=object)
    for i, line in enumerate(data_lines):
        parts = line.rstrip("\n").rstrip("\r").split(",")
        for j, (idx, _name, _sentinel) in enumerate(_FIELDS):
            raw[i, j] = parts[idx - 1]

    df = pd.DataFrame(raw, columns=[name for _idx, name, _s in _FIELDS])
    for _idx, name, _sentinel in _FIELDS:
        df[name] = pd.to_numeric(df[name], errors="coerce")

    dq_flag = pd.Series(False, index=df.index)
    for _idx, name, sentinel in _FIELDS:
        if sentinel is None:
            continue
        is_missing = np.isclose(df[name].to_numpy(dtype=float), sentinel, atol=1e-6)
        dq_flag |= is_missing
        df.loc[is_missing, name] = np.nan
    df["dq_flag"] = dq_flag

    month = df["month"].astype(int).to_numpy()
    day = df["day"].astype(int).to_numpy()
    hour_0based = df["hour"].astype(int).to_numpy() - 1
    ts = pd.to_datetime({
        "year": nominal_year,
        "month": month,
        "day": day,
        "hour": 0,
    }) + pd.to_timedelta(hour_0based, unit="h")
    df.index = pd.DatetimeIndex(ts, name="datetime")
    df = df.drop(columns=["month", "day", "hour"])
    return df
