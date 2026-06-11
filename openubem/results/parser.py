"""Step-5 Module 13: SQL extraction, zone resolution, EUI, and IOD (DESIGN §3A-§3D)."""
from __future__ import annotations

import re
import sqlite3
import warnings
from pathlib import Path
from typing import Any

import pandas as pd

from openubem import config
from openubem.geometry.footprint import derive_num_floors

# ── §3A constants (DESIGN lines 45-57) ───────────────────────────────────────
HOURLY_QUERY = """
SELECT d.KeyValue       AS key_value,
       d.Name           AS variable_name,
       d.Units          AS units,
       t.Month, t.Day, t.Hour,
       r.Value          AS value
FROM   ReportData r
JOIN   ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
JOIN   Time t                 ON r.TimeIndex = t.TimeIndex
WHERE  d.ReportingFrequency = 'Hourly'
"""

J_TO_KWH = 1.0 / 3.6e6

# ── §3B zone regex (DESIGN lines 78-81) ──────────────────────────────────────
# PERIM\d* handles EnergyPlus perimeter-core sub-zones (perim1…perim4).
# IDEAL LOADS AIR SYSTEM suffix is stripped before matching (see _strip_ideal_loads).
ZONE_RX = re.compile(
    r"^(?:BLOCK\s+)?(?P<osm_id>.+?)_F(?P<floor>\d+)_(?P<label>WHOLE|CORE|PERIM\d*)"
    r"(?:\s+STOREY\s+\d+)?$"
)

# EnergyPlus appends this suffix to Zone Ideal Loads key values.
_IDEAL_LOADS_SUFFIX = re.compile(r"\s+IDEAL LOADS AIR SYSTEM$", re.IGNORECASE)


def _strip_ideal_loads(key_value: str) -> str:
    """Remove EnergyPlus ' IDEAL LOADS AIR SYSTEM' suffix before zone-regex matching."""
    return _IDEAL_LOADS_SUFFIX.sub("", key_value)

# ── F5 EUI variables ──────────────────────────────────────────────────────────
_EUI_VARS: dict[str, str] = {
    "heating_eui_kwh_m2": "Zone Ideal Loads Zone Total Heating Energy",
    "cooling_eui_kwh_m2": "Zone Ideal Loads Zone Total Cooling Energy",
    "lighting_eui_kwh_m2": "Zone Lights Electric Energy",
    "equipment_eui_kwh_m2": "Zone Electric Equipment Electric Energy",
}

# ── F6 IOD variables ──────────────────────────────────────────────────────────
_IOD_SITE_TEMP_VAR = "Site Outdoor Air Drybulb Temperature"
_IOD_OT_VAR = "Zone Operative Temperature"
_IOD_OCC_VAR = "Zone People Occupant Count"


# ── §3A: SQL parse (DESIGN lines 59-66) ──────────────────────────────────────

def parse_building_sql(sql_path: Path) -> pd.DataFrame:
    """Pull all hourly variables from eplusout.sql; convert J→kWh at the boundary."""
    with sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True) as conn:
        df = pd.read_sql_query(HOURLY_QUERY, conn)
    is_energy = df["units"] == "J"
    df.loc[is_energy, "value"] *= J_TO_KWH
    df.loc[is_energy, "units"] = "kWh"
    return df


def parse_building_csv(csv_path: Path) -> pd.DataFrame:
    """CSV fallback: readVarsESO headers KEY:Variable [Units](Hourly) → long frame.
    Returns a frame with the same columns as parse_building_sql.
    """
    raw = pd.read_csv(csv_path)
    records: list[dict] = []
    header_rx = re.compile(
        r"^(?P<key>[^:]+):(?P<var>.+?)\s+\[(?P<units>[^\]]*)\]\(Hourly\)\s*$"
    )
    # Parse Date/Time → Month, Day, Hour
    def _parse_dt(s: str):
        # EnergyPlus CSV date/time: " 1/ 1 01:00:00" or "01/01 01:00:00"
        s = s.strip()
        for fmt in ("%m/%d %H:%M:%S", "%m/ %d %H:%M:%S", " %m/%d %H:%M:%S"):
            try:
                from datetime import datetime
                dt = datetime.strptime(s, fmt)
                return dt.month, dt.day, dt.hour
            except ValueError:
                continue
        # Fallback regex
        m = re.match(r"\s*(\d+)/\s*(\d+)\s+(\d+):", s)
        if m:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))
        return None, None, None

    for col in raw.columns:
        if col == "Date/Time":
            continue
        m = header_rx.match(col)
        if not m:
            continue
        key_value = m.group("key").strip()
        var_name = m.group("var").strip()
        units_raw = m.group("units").strip()
        # J→kWh conversion
        to_kwh = units_raw == "J"
        for _, row in raw.iterrows():
            month, day, hour = _parse_dt(str(row["Date/Time"]))
            val = float(row[col]) * J_TO_KWH if to_kwh else float(row[col])
            records.append({
                "key_value": key_value,
                "variable_name": var_name,
                "units": "kWh" if to_kwh else units_raw,
                "Month": month,
                "Day": day,
                "Hour": hour,
                "value": val,
            })
    return pd.DataFrame(records) if records else pd.DataFrame(
        columns=["key_value", "variable_name", "units", "Month", "Day", "Hour", "value"]
    )


# ── §3B: zone resolution (DESIGN lines 78-90) ────────────────────────────────

def resolve_zone(key_value: str) -> dict | None:
    """Parse zone key → {osm_id_uc, floor, label}, or None for site-level keys."""
    stripped = _strip_ideal_loads(key_value.strip())
    m = ZONE_RX.match(stripped.upper())
    if m is None:
        return None
    return {"osm_id_uc": m["osm_id"], "floor": int(m["floor"]), "label": m["label"]}


def _check_zone_integrity(
    df: pd.DataFrame,
    osm_id: str,
    num_zones: int,
) -> tuple[str | None, str | None]:
    """Return (parse_status, error_summary) based on zone integrity checks.

    Returns (None, None) if OK, or ("failed_zone_mismatch", msg) for local mismatch,
    or raises RuntimeError for I2 breach (foreign osm_id → caller aborts whole run).
    """
    ideal_loads_mask = df["variable_name"].str.startswith("Zone Ideal Loads")
    zone_keys = df.loc[ideal_loads_mask, "key_value"].str.upper().unique()

    # Resolve and check for foreign osm_id (I2 breach)
    foreign: list[str] = []
    resolved_zone_ids: set[str] = set()
    for kv in zone_keys:
        parsed = resolve_zone(kv)
        if parsed is None:
            continue  # site-level or ideal-loads system suffix
        if parsed["osm_id_uc"] != osm_id.upper():
            foreign.append(kv)
        else:
            # Canonical zone name without suffix
            resolved_zone_ids.add(f"{parsed['osm_id_uc']}_F{parsed['floor']}_{parsed['label']}")

    if foreign:
        raise RuntimeError(
            f"I2 breach: foreign osm_id in work dir for {osm_id!r}: "
            f"{foreign[:3]} (abort whole run)"
        )

    if len(resolved_zone_ids) != num_zones:
        msg = (
            f"zone count mismatch: found {len(resolved_zone_ids)}, "
            f"manifest says {num_zones}"
        )
        return "failed_zone_mismatch", msg

    return None, None


# ── §3C: EUI computation (DESIGN lines 96-111) ───────────────────────────────

def _compute_eui(
    df: pd.DataFrame,
    row: "pd.Series",
    data_quality_flag: str,
) -> tuple[dict[str, float], str]:
    """Compute 5 EUI columns; return (eui_dict, updated_dq_flag).

    Per PLAN P10 deviation: absent EUI variables → 0.0 + RESULTS_MISSING_VARIABLE_<name>
    token appended to data_quality_flag (never a NaN or silent zero).
    """
    num_floors = derive_num_floors(row)
    footprint_area = float(row["footprint_area_m2"])
    floor_area = footprint_area * num_floors

    eui: dict[str, float] = {}
    present_vars = df["variable_name"].unique()

    for col, var_name in _EUI_VARS.items():
        if var_name in present_vars:
            kwh = float(df[df["variable_name"] == var_name]["value"].sum())
        else:
            # PLAN P10 deviation: treat as 0.0 + flag
            kwh = 0.0
            token = f"RESULTS_MISSING_VARIABLE_{var_name.replace(' ', '_')}"
            data_quality_flag = _append_flag(data_quality_flag, token)
        eui[col] = kwh / floor_area

    eui["total_eui_kwh_m2"] = sum(eui[k] for k in _EUI_VARS)
    return eui, data_quality_flag


def _append_flag(dq_flag: str, token: str) -> str:
    import pandas as _pd
    if _pd.isna(dq_flag) or dq_flag == "":
        return token
    tokens = [t.strip() for t in dq_flag.split(",")]
    if token in tokens:
        return dq_flag
    return dq_flag + "," + token


# ── §3D: IOD computation (DESIGN lines 119-137) ──────────────────────────────

def _compute_iod(
    df: pd.DataFrame,
    data_quality_flag: str,
) -> tuple[float, str]:
    """Compute building IOD per DESIGN §3D formula; return (iod, updated_dq_flag).

    Returns (NaN, flag+IOD_NO_OCCUPIED_HOURS) when zero occupied summer hours.
    """
    import math

    summer_lo, summer_hi = config.IOD_SUMMER_MONTHS  # (6, 9) inclusive

    site_temp = df[df["variable_name"] == _IOD_SITE_TEMP_VAR][
        ["Month", "Day", "Hour", "value"]
    ]
    ot_df = df[df["variable_name"] == _IOD_OT_VAR][
        ["key_value", "Month", "Day", "Hour", "value"]
    ]
    occ_df = df[df["variable_name"] == _IOD_OCC_VAR][
        ["key_value", "Month", "Day", "Hour", "value"]
    ]

    if len(site_temp) == 0 or len(ot_df) == 0 or len(occ_df) == 0:
        data_quality_flag = _append_flag(data_quality_flag, "IOD_NO_OCCUPIED_HOURS")
        return float("nan"), data_quality_flag

    # Monthly mean outdoor temp from SQL site variable (never EPW)
    monthly_mean: dict[int, float] = (
        site_temp.groupby("Month")["value"].mean().to_dict()
    )

    summer_mask = (ot_df["Month"] >= summer_lo) & (ot_df["Month"] <= summer_hi)
    ot_summer = ot_df[summer_mask].copy()
    occ_summer = occ_df[
        (occ_df["Month"] >= summer_lo) & (occ_df["Month"] <= summer_hi)
    ].copy()

    ot_summer = ot_summer.copy()
    ot_summer["Tave"] = ot_summer["Month"].map(monthly_mean)
    ot_summer["Tn"] = 0.31 * ot_summer["Tave"] + 17.8
    ot_summer["Tcomf"] = ot_summer["Tn"] + 2.5

    merge_cols = ["key_value", "Month", "Day", "Hour"]
    ot_occ = ot_summer.merge(
        occ_summer.rename(columns={"value": "occ_count"}),
        on=merge_cols,
        how="left",
    )
    ot_occ["occ_count"] = ot_occ["occ_count"].fillna(0.0)
    occupied = ot_occ[ot_occ["occ_count"] > 0].copy()

    if len(occupied) == 0:
        data_quality_flag = _append_flag(data_quality_flag, "IOD_NO_OCCUPIED_HOURS")
        return float("nan"), data_quality_flag

    occupied = occupied.copy()
    occupied["exceedance"] = (occupied["value"] - occupied["Tcomf"]).clip(lower=0)

    # Occupant-count-weighted mean of per-zone IOD (DESIGN §3D)
    zone_iod = (
        occupied.groupby("key_value")
        .agg(mean_exc=("exceedance", "mean"), total_occ=("occ_count", "sum"))
        .reset_index()
    )
    total_weight = float(zone_iod["total_occ"].sum())
    if total_weight == 0:
        data_quality_flag = _append_flag(data_quality_flag, "IOD_NO_OCCUPIED_HOURS")
        return float("nan"), data_quality_flag

    iod = float(
        (zone_iod["mean_exc"] * zone_iod["total_occ"]).sum() / total_weight
    )
    return iod, data_quality_flag


# ── §5.1 P5: ABUPS / meter closure checks ───────────────────────────────────

def check_building_integrity(
    sql_path: Path,
    mtr_path: Path | None = None,
) -> dict[str, Any]:
    """DESIGN §5.1 P5 integrity gates for one building.

    Returns dict with keys: abups_ok, meter_ok, gas_zero.
    Requires TabularDataWithStrings (ABUPS) + RunPeriod meter rows in the SQL.
    """
    result: dict[str, Any] = {"abups_ok": None, "meter_ok": None, "gas_zero": None}

    if not sql_path.exists():
        return result

    try:
        conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)

        # ABUPS cross-check: compare hourly sum vs TabularDataWithStrings
        hourly_q = """
        SELECT COALESCE(SUM(r.Value), 0.0) AS total_j
        FROM ReportData r
        JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
        WHERE d.Name IN ('Zone Lights Electric Energy', 'Zone Electric Equipment Electric Energy')
          AND d.ReportingFrequency = 'Hourly'
        """
        hourly_j = conn.execute(hourly_q).fetchone()[0] or 0.0

        abups_q = """
        SELECT COALESCE(SUM(CAST(Value AS REAL)), 0.0)
        FROM TabularDataWithStrings
        WHERE ReportName = 'AnnualBuildingUtilityPerformanceSummary'
          AND TableName = 'End Uses'
          AND RowName IN ('Interior Lighting', 'Interior Equipment')
          AND ColumnName = 'Electricity'
          AND Units = 'GJ'
        """
        abups_gj = conn.execute(abups_q).fetchone()[0] or 0.0
        abups_j = abups_gj * 1e9

        if abups_j > 0:
            diff = abs(hourly_j - abups_j) / abups_j
            result["abups_ok"] = diff <= 0.005
        else:
            # Both zero is acceptable; if hourly_j > 0 but abups = 0 → fail
            result["abups_ok"] = hourly_j == 0.0

        # Meter closure: hourly zone-level elec vs Electricity:Facility RunPeriod
        meter_q = """
        SELECT COALESCE(SUM(r.Value), 0.0)
        FROM ReportData r
        JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
        WHERE d.Name = 'Electricity:Facility'
          AND d.ReportingFrequency = 'Run Period'
        """
        facility_j = conn.execute(meter_q).fetchone()[0] or 0.0

        zone_elec_q = """
        SELECT COALESCE(SUM(r.Value), 0.0)
        FROM ReportData r
        JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
        WHERE d.Name IN ('Zone Lights Electric Energy', 'Zone Electric Equipment Electric Energy')
          AND d.ReportingFrequency = 'Hourly'
        """
        zone_elec_j = conn.execute(zone_elec_q).fetchone()[0] or 0.0

        if facility_j > 0:
            diff = abs(zone_elec_j - facility_j) / facility_j
            result["meter_ok"] = diff <= 0.01
        else:
            result["meter_ok"] = zone_elec_j == 0.0

        # Gas-zero check (IdealAir IDFs have no gas equipment)
        gas_q = """
        SELECT COALESCE(SUM(r.Value), 0.0)
        FROM ReportData r
        JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
        WHERE d.Name = 'NaturalGas:Facility'
          AND d.ReportingFrequency = 'Run Period'
        """
        gas_j = conn.execute(gas_q).fetchone()[0] or 0.0
        result["gas_zero"] = gas_j == 0.0

        conn.close()
    except Exception as exc:
        warnings.warn(f"check_building_integrity failed for {sql_path}: {exc}")

    return result


# ── Top-level per-building parse ──────────────────────────────────────────────

def parse_building(
    sql_path: "Path | str | None",
    csv_path: "Path | str | None",
    manifest_row: "pd.Series",
) -> dict[str, Any]:
    """Parse one building's SQL (or CSV fallback); return a metrics dict.

    Keys: 5 EUI, 5 GWP placeholders (filled by carbon.py), iod, parse_status,
          error_summary, data_quality_flag (updated).
    """
    sql_path = Path(sql_path) if sql_path else None
    csv_path = Path(csv_path) if csv_path else None

    osm_id: str = str(manifest_row["osm_id"])
    num_zones: int = int(manifest_row.get("num_zones", 1))
    dq_flag: str = str(manifest_row.get("data_quality_flag", "") or "")

    parse_status = "success"
    error_summary = ""
    df: pd.DataFrame | None = None

    # §3A: try SQL first
    if sql_path and sql_path.exists():
        try:
            df = parse_building_sql(sql_path)
        except Exception as exc:
            error_summary = str(exc)[:500]
            df = None

    # CSV fallback
    if df is None and csv_path and csv_path.exists():
        try:
            df = parse_building_csv(csv_path)
            parse_status = "success_csv_fallback"
            dq_flag = _append_flag(dq_flag, "RESULTS_CSV_FALLBACK")
        except Exception as exc:
            error_summary = str(exc)[:500]
            df = None

    if df is None:
        return _failed_row(osm_id, "failed_parse", error_summary or "no SQL or CSV", dq_flag)

    # §3B: zone integrity
    try:
        status, msg = _check_zone_integrity(df, osm_id, num_zones)
    except RuntimeError as exc:
        # I2 breach: re-raise to abort whole run
        raise

    if status is not None:
        return _failed_row(osm_id, status, msg or "", dq_flag)

    # §3C: EUI
    eui, dq_flag = _compute_eui(df, manifest_row, dq_flag)

    # §3D: IOD
    iod, dq_flag = _compute_iod(df, dq_flag)

    return {
        "osm_id": osm_id,
        "parse_status": parse_status,
        "error_summary": error_summary,
        "data_quality_flag": dq_flag,
        **eui,
        "iod": iod,
        # GWP columns filled by carbon.py
        "gwp_heating_kgco2_m2": None,
        "gwp_cooling_kgco2_m2": None,
        "gwp_lighting_kgco2_m2": None,
        "gwp_equipment_kgco2_m2": None,
        "gwp_total_kgco2_m2": None,
    }


def _failed_row(osm_id: str, status: str, error: str, dq_flag: str) -> dict[str, Any]:
    import math
    return {
        "osm_id": osm_id,
        "parse_status": status,
        "error_summary": error,
        "data_quality_flag": dq_flag,
        "heating_eui_kwh_m2": float("nan"),
        "cooling_eui_kwh_m2": float("nan"),
        "lighting_eui_kwh_m2": float("nan"),
        "equipment_eui_kwh_m2": float("nan"),
        "total_eui_kwh_m2": float("nan"),
        "iod": float("nan"),
        "gwp_heating_kgco2_m2": None,
        "gwp_cooling_kgco2_m2": None,
        "gwp_lighting_kgco2_m2": None,
        "gwp_equipment_kgco2_m2": None,
        "gwp_total_kgco2_m2": None,
    }
