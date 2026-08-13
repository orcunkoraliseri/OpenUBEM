"""Step-5 Module 13: SQL extraction, zone resolution, EUI, and IOD (DESIGN §3A-§3D).
Phase-D (§0.1 authorized deviation): _EUI_VARS rewired to metered HVAC end-uses (T05).
Phase-E (T13): extended METER_QUERY with pumps/DHW/cooking/refrigeration meters;
_compute_eui adds pumps_eui, dhw_eui, cooking_eui, refrigeration_eui; D9 total includes all 9 end-uses.
Authorized deviation: DESIGN_step-3...md:H3/§3I — cooling/heating now from RunPeriod meters
(Cooling:Electricity, Heating:Electricity+NaturalGas) instead of ideal-loads thermal variables.

OPEN-46 (T05, 2026-08-12): elevators restored as a 10th reported end-use, GUARDED.
The reporting path is additive: when the Elevators:InteriorEquipment:Electricity meter is
present the elevator kWh is de-folded out of equipment into its own column; when it is
absent the column reads 0.0 and equipment is left untouched, so total_eui_kwh_m2 is
bit-identical to the 9-way total for every SQL written before this change.
"""
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

# T13 (Phase-E): RunPeriod meter query — all end-use meters.
METER_QUERY = """
SELECT d.Name AS meter_name,
       r.Value AS value_j
FROM   ReportData r
JOIN   ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
WHERE  d.ReportingFrequency = 'Run Period'
  AND  d.Name IN ('Cooling:Electricity', 'Heating:Electricity',
                  'Heating:NaturalGas', 'Fans:Electricity',
                  'Pumps:Electricity',
                  'WaterSystems:NaturalGas', 'WaterSystems:Electricity',
                  'InteriorEquipment:NaturalGas',
                  'Refrigeration:Electricity',
                  'Elevators:InteriorEquipment:Electricity')
"""

# OPEN-46 T05: the ElectricEquipment subcategory meter emitted by openubem/idf/elevators.py.
_ELEVATOR_METER = "Elevators:InteriorEquipment:Electricity"

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

# ── F5 EUI variables (Phase-D: metered HVAC end-uses) ────────────────────────
# lighting and equipment remain hourly zone variables (unchanged from Phase-C).
# cooling and heating are now RunPeriod meters read by _compute_eui_metered.
_EUI_ZONE_VARS: dict[str, str] = {
    "lighting_eui_kwh_m2": "Zone Lights Electricity Energy",
    "equipment_eui_kwh_m2": "Zone Electric Equipment Electricity Energy",
}
# Legacy alias kept for zone-integrity check (still looks for Ideal Loads variables to parse zones).
_EUI_VARS: dict[str, str] = _EUI_ZONE_VARS

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


def _parse_meters_sql(sql_path: Path) -> dict[str, float]:
    """Read RunPeriod HVAC end-use meters from SQL; return {meter_name: kWh}.
    Missing meters (e.g. all-electric → no Heating:NaturalGas) return 0.0, not NaN.
    T05: Phase-D metered EUI source.

    OPEN-46: the elevator subcategory meter reads 0.0 for any SQL that does not carry it
    (every run built before the meter was added to HVAC_METERS). _compute_eui treats that
    0.0 as "meter absent" and performs no de-folding.
    """
    meters: dict[str, float] = {
        "Cooling:Electricity": 0.0,
        "Heating:Electricity": 0.0,
        "Heating:NaturalGas": 0.0,
        "Fans:Electricity": 0.0,
        "Pumps:Electricity": 0.0,
        "WaterSystems:NaturalGas": 0.0,
        "WaterSystems:Electricity": 0.0,
        "InteriorEquipment:NaturalGas": 0.0,
        "Refrigeration:Electricity": 0.0,
        _ELEVATOR_METER: 0.0,
    }
    try:
        with sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True) as conn:
            rows = conn.execute(METER_QUERY).fetchall()
        for name, value_j in rows:
            if name in meters and value_j is not None:
                meters[name] += float(value_j) * J_TO_KWH
    except Exception:
        pass
    return meters


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
    resolution_mode: str | None = None,
) -> tuple[str | None, str | None]:
    """Return (parse_status, error_summary) based on zone integrity checks.

    Returns (None, None) if OK, or ("failed_zone_mismatch", msg) for local mismatch,
    or raises RuntimeError for I2 breach (foreign osm_id → caller aborts whole run).
    Phase-D: uses Zone Lights Electricity Energy to find zone keys (PTAC has no Ideal Loads).
    Falls back to Zone Ideal Loads if Lights variable absent (backward-compat).

    resolution_mode=None (default) preserves the exact pre-T14 behavior for every mode
    other than layout_assign/layout_assigner (E-LA-05). For those two, ZONE_RX/resolve_zone
    matching (and therefore the I2 foreign-osm_id check) is skipped entirely and replaced by
    a light key-presence sanity check (see T14 in the LayoutAssigner plan).
    """
    lights_mask = df["variable_name"] == "Zone Lights Electricity Energy"
    if lights_mask.any():
        zone_keys = df.loc[lights_mask, "key_value"].str.upper().unique()
    else:
        ideal_loads_mask = df["variable_name"].str.startswith("Zone Ideal Loads")
        zone_keys = df.loc[ideal_loads_mask, "key_value"].str.upper().unique()

    if resolution_mode in ("layout_assign", "layout_assigner"):
        # DOE baseline zone names (e.g. "G SW APARTMENT") never encode an osm_id, so
        # ZONE_RX/resolve_zone (and the I2 foreign-osm_id check built on it) cannot apply here.
        distinct_keys = [kv for kv in zone_keys if isinstance(kv, str) and kv.strip() != ""]
        if len(distinct_keys) == 0:
            return (
                "failed_zone_mismatch",
                "layout_assign: zero zone-level keys found in SQL (corrupt/empty result)",
            )
        return None, None

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

    if len(resolved_zone_ids) == 0:
        return "failed_zone_mismatch", f"zone count mismatch: found 0, manifest says {num_zones}"

    return None, None


# ── §3C: EUI computation (Phase-D: metered HVAC + zone lighting/equipment) ───
# Authorized deviation per §0.1: cooling/heating from RunPeriod meters, not ideal-loads vars.
# fans_eui_kwh_m2 is separate and NOT in total_eui_kwh_m2 (manager decision at CP-4).

def _compute_eui(
    df: pd.DataFrame,
    row: "pd.Series",
    data_quality_flag: str,
    meters: dict[str, float] | None = None,
) -> tuple[dict[str, float] | None, str, str | None]:
    """Compute EUI columns using metered HVAC + hourly zone lighting/equipment.

    cooling_eui_kwh_m2       ← Cooling:Electricity meter
    heating_eui_kwh_m2       ← Heating:Electricity + Heating:NaturalGas meters (all-fuels site)
    lighting_eui_kwh_m2      ← Zone Lights Electricity Energy (hourly)
    equipment_eui_kwh_m2     ← Zone Electric Equipment Electricity Energy (hourly)
    fans_eui_kwh_m2          ← Fans:Electricity meter
    pumps_eui_kwh_m2         ← Pumps:Electricity meter
    dhw_eui_kwh_m2           ← WaterSystems:NaturalGas + WaterSystems:Electricity (all-fuel DHW)
    cooking_eui_kwh_m2       ← InteriorEquipment:NaturalGas (gas cooking; elec cooking in equipment)
    refrigeration_eui_kwh_m2 ← Refrigeration:Electricity (CompressorRack; lumped in equipment)
    elevators_eui_kwh_m2     ← Elevators:InteriorEquipment:Electricity (OPEN-46; see guard below)
    total_eui_kwh_m2         ← sum of the end-use EUIs (D9: Phase-E whole-building total)

    OPEN-46 elevator guard (PLAN_three-new-items-2026-08-12.md §3 decision 3):
    elevators are emitted as ElectricEquipment with EndUse_Subcategory="Elevators", so when
    the meter is present the elevator kWh is ALREADY inside the hourly equipment variable and
    is de-folded out of equipment_eui_kwh_m2 into its own column — ten mutually exclusive
    end-uses, total unchanged. When the meter is absent the column is 0.0 and NOTHING is
    subtracted from equipment, so the total is bit-identical to the pre-OPEN-46 9-way total.
    Ten end-uses are therefore reported for runs whose IDFs carry the elevator meter; runs
    built before it was added to HVAC_METERS report nine and an elevators column of 0.0.

    P10 (C3-enforced): missing lighting or equipment variable → failed_parse.
    Missing meters → 0.0 (not failed_parse).
    """
    num_floors = derive_num_floors(row)
    footprint_area = float(row["footprint_area_m2"])
    floor_area = footprint_area * num_floors

    # Zone-level lighting + equipment (must be present)
    present_vars = set(df["variable_name"].unique())
    for col, var_name in _EUI_ZONE_VARS.items():
        if var_name not in present_vars:
            return None, data_quality_flag, var_name

    eui: dict[str, float] = {}
    for col, var_name in _EUI_ZONE_VARS.items():
        kwh = float(df[df["variable_name"] == var_name]["value"].sum())
        eui[col] = kwh / floor_area

    # Metered end-uses (0.0 if meter absent — valid for all-electric or no-cooking buildings)
    if meters is None:
        meters = {}

    def _m(key: str) -> float:
        return meters.get(key, 0.0)

    cooling_kwh = _m("Cooling:Electricity")
    heating_kwh = _m("Heating:Electricity") + _m("Heating:NaturalGas")
    fans_kwh = _m("Fans:Electricity")
    pumps_kwh = _m("Pumps:Electricity")
    dhw_kwh = _m("WaterSystems:NaturalGas") + _m("WaterSystems:Electricity")
    cooking_kwh = _m("InteriorEquipment:NaturalGas")  # gas cooking; elec cooking lives in equipment
    refrigeration_kwh = _m("Refrigeration:Electricity")  # CompressorRack; lumped is in equipment

    dhw_gas_kwh = _m("WaterSystems:NaturalGas")
    dhw_elec_kwh = _m("WaterSystems:Electricity")

    eui["cooling_eui_kwh_m2"] = cooling_kwh / floor_area
    eui["heating_eui_kwh_m2"] = heating_kwh / floor_area
    eui["fans_eui_kwh_m2"] = fans_kwh / floor_area
    eui["pumps_eui_kwh_m2"] = pumps_kwh / floor_area
    eui["dhw_gas_eui_kwh_m2"] = dhw_gas_kwh / floor_area   # gas DHW (× f_gas in carbon.py)
    eui["dhw_elec_eui_kwh_m2"] = dhw_elec_kwh / floor_area  # elec DHW (× f_elec)
    eui["dhw_eui_kwh_m2"] = dhw_kwh / floor_area            # combined total for D9
    eui["cooking_eui_kwh_m2"] = cooking_kwh / floor_area    # gas only (InteriorEquipment:NaturalGas)
    eui["refrigeration_eui_kwh_m2"] = refrigeration_kwh / floor_area

    # OPEN-46 T05 — GUARDED, ADDITIVE elevator breakout.
    # De-folding is performed ONLY when the meter actually carried elevator energy.
    # A SQL without the meter yields 0.0 here, the branch is skipped, and
    # equipment_eui_kwh_m2 / total_eui_kwh_m2 come out bit-identical to the 9-way values.
    elevators_kwh = _m(_ELEVATOR_METER)
    eui["elevators_eui_kwh_m2"] = elevators_kwh / floor_area
    if elevators_kwh:
        eui["equipment_eui_kwh_m2"] -= eui["elevators_eui_kwh_m2"]

    # D9: total = all end-use EUIs summed (Phase-E whole-building site energy).
    # Invariant vs the pre-OPEN-46 9-way total: elevators_eui is subtracted from
    # equipment_eui above and re-added here, and is 0.0 when the meter is absent.
    eui["total_eui_kwh_m2"] = (
        eui["cooling_eui_kwh_m2"]
        + eui["heating_eui_kwh_m2"]
        + eui["lighting_eui_kwh_m2"]
        + eui["equipment_eui_kwh_m2"]
        + eui["fans_eui_kwh_m2"]
        + eui["pumps_eui_kwh_m2"]
        + eui["dhw_eui_kwh_m2"]
        + eui["cooking_eui_kwh_m2"]
        + eui["refrigeration_eui_kwh_m2"]
        + eui["elevators_eui_kwh_m2"]
    )
    return eui, data_quality_flag, None


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
        WHERE d.Name IN ('Zone Lights Electricity Energy', 'Zone Electric Equipment Electricity Energy')
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
        WHERE d.Name IN ('Zone Lights Electricity Energy', 'Zone Electric Equipment Electricity Energy')
          AND d.ReportingFrequency = 'Hourly'
        """
        zone_elec_j = conn.execute(zone_elec_q).fetchone()[0] or 0.0

        if facility_j > 0:
            diff = abs(zone_elec_j - facility_j) / facility_j
            result["meter_ok"] = diff <= 0.01
        else:
            result["meter_ok"] = zone_elec_j == 0.0

        # Gas-zero check (Phase-D PTAC: gas heating is expected; check is informational)
        gas_q = """
        SELECT COALESCE(SUM(r.Value), 0.0)
        FROM ReportData r
        JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
        WHERE d.Name = 'NaturalGas:Facility'
          AND d.ReportingFrequency = 'Run Period'
        """
        gas_j = conn.execute(gas_q).fetchone()[0] or 0.0
        result["gas_zero"] = gas_j == 0.0  # False is expected for gas-heat archetypes in Phase-D

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
    import math as _math
    sql_path = Path(sql_path) if (sql_path and not (isinstance(sql_path, float) and _math.isnan(sql_path))) else None
    csv_path = Path(csv_path) if (csv_path and not (isinstance(csv_path, float) and _math.isnan(csv_path))) else None

    osm_id: str = str(manifest_row["osm_id"])
    num_zones: int = int(manifest_row.get("num_zones", 1))
    dq_flag: str = str(manifest_row.get("data_quality_flag", "") or "")
    resolution_mode: str | None = manifest_row.get("resolution_mode")

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
        status, msg = _check_zone_integrity(df, osm_id, num_zones, resolution_mode=resolution_mode)
    except RuntimeError as exc:
        # I2 breach: re-raise to abort whole run
        raise

    if status is not None:
        return _failed_row(osm_id, status, msg or "", dq_flag)

    # §3C: EUI — read RunPeriod HVAC meters from SQL, then compute (T05 Phase-D)
    meters: dict[str, float] = {}
    if sql_path and sql_path.exists():
        meters = _parse_meters_sql(sql_path)

    eui, dq_flag, missing_var = _compute_eui(df, manifest_row, dq_flag, meters=meters)
    if eui is None:
        return _failed_row(osm_id, "failed_parse", f"missing required EUI variable: {missing_var}", dq_flag)

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
    }  # fans_eui_kwh_m2 is in **eui (not in total; flagged for CP-4)


def _failed_row(osm_id: str, status: str, error: str, dq_flag: str) -> dict[str, Any]:
    return {
        "osm_id": osm_id,
        "parse_status": status,
        "error_summary": error,
        "data_quality_flag": dq_flag,
        "heating_eui_kwh_m2": float("nan"),
        "cooling_eui_kwh_m2": float("nan"),
        "lighting_eui_kwh_m2": float("nan"),
        "equipment_eui_kwh_m2": float("nan"),
        "fans_eui_kwh_m2": float("nan"),
        "elevators_eui_kwh_m2": float("nan"),
        "total_eui_kwh_m2": float("nan"),
        "iod": float("nan"),
        "gwp_heating_kgco2_m2": None,
        "gwp_cooling_kgco2_m2": None,
        "gwp_lighting_kgco2_m2": None,
        "gwp_equipment_kgco2_m2": None,
        "gwp_total_kgco2_m2": None,
    }
