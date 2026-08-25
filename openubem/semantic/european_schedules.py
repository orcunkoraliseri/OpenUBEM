"""External-file internal-gain schedules for the European Step 8 campaign.

The module is deliberately independent of the legacy DOE ``Schedule:Compact`` library.  It emits
hourly *power-density* values (W/m2) through an ``Any Number`` Schedule:File and a 1 W/m2
OtherEquipment design level, so EnergyPlus receives ``phi_int(t)`` exactly once.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Iterable

import numpy as np


F_LEVELS = (0.00, 0.15, 0.30, 0.50, 1.00)
HOURS_PER_YEAR = 8760
BASE_GAIN_W_M2 = 3.0


def build_step8_gain_series(
    presence: Iterable[float] | None,
    sensitivity_f: float,
    *,
    chaining_rule: str | None = None,
) -> tuple[np.ndarray, int | None]:
    """Transform an annual presence series into the ruled conserved gain series.

    ``f=0`` intentionally needs no diary or chaining convention, allowing the Q1--Q3 and FR-B
    controls to use exactly the same Schedule:File path.  Any injected ``f>0`` series requires a
    named chaining rule and an annual, non-negative, non-zero 8,760-hour presence series.
    """
    if sensitivity_f not in F_LEVELS:
        raise ValueError(f"sensitivity_f must be one of {F_LEVELS}, got {sensitivity_f}")
    if sensitivity_f == 0.0 and presence is None:
        return np.full(HOURS_PER_YEAR, BASE_GAIN_W_M2), None
    if presence is None:
        raise ValueError("presence is required for f>0")

    values = np.asarray(list(presence), dtype=float)
    if values.shape != (HOURS_PER_YEAR,):
        raise ValueError(f"presence must contain exactly {HOURS_PER_YEAR} hourly values")
    if not np.isfinite(values).all():
        raise ValueError("presence must contain only finite values")
    if (values < 0.0).any():
        raise ValueError("presence must be non-negative")
    zero_presence_days = int(np.sum(values.reshape(-1, 24).sum(axis=1) == 0.0))

    if sensitivity_f > 0.0:
        if not chaining_rule or not chaining_rule.strip():
            raise ValueError("f>0 emission is blocked until a named chaining_rule is supplied")
        annual_mean = float(values.mean())
        if annual_mean <= 0.0:
            raise ValueError("annual mean presence must be > 0 for f>0")
        values = BASE_GAIN_W_M2 * ((1.0 - sensitivity_f) + sensitivity_f * (values / annual_mean))
    else:
        values = np.full(HOURS_PER_YEAR, BASE_GAIN_W_M2)

    if not np.isclose(float(values.mean()), BASE_GAIN_W_M2, rtol=1e-8, atol=1e-10):
        raise AssertionError("Step 8 annual gain conservation failed")
    return values, zero_presence_days


def read_presence_csv(path: Path | str) -> np.ndarray:
    """Read the one-column, headerless annual presence artefact without network access."""
    try:
        values = np.loadtxt(Path(path), delimiter=",", ndmin=1)
    except OSError as exc:
        raise ValueError(f"presence CSV cannot be read: {path}") from exc
    return np.asarray(values, dtype=float)


def write_gain_csv_atomic(values: Iterable[float], path: Path | str) -> tuple[Path, str]:
    """Atomically persist a one-column hourly W/m2 series and return its SHA-256 digest."""
    output = Path(path)
    array = np.asarray(list(values), dtype=float)
    if array.shape != (HOURS_PER_YEAR,):
        raise ValueError(f"gain schedule must contain exactly {HOURS_PER_YEAR} values")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    np.savetxt(temporary, array, fmt="%.12g", delimiter=",")
    os.replace(temporary, output)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return output, digest


def emit_step8_gain_schedule(
    idf: Any,
    *,
    sensitivity_f: float,
    dwelling_zone: str,
    dwelling_id: str,
    emitted_csv_path: Path | str,
    presence: Iterable[float] | None = None,
    chaining_rule: str | None = None,
) -> dict[str, object]:
    """Emit the external-file schedule and its sole matching dwelling gain object.

    The function never creates a ``People`` object: the diary series is an internal-gain signal,
    not an occupancy fraction.  Callers must remove/avoid legacy DOE gain objects for the dwelling
    before adding this object, then use saved-IDF read-back to audit assignment.
    """
    values, zero_presence_days = build_step8_gain_series(
        presence, sensitivity_f, chaining_rule=chaining_rule
    )
    output, digest = write_gain_csv_atomic(values, emitted_csv_path)
    suffix = f"{dwelling_id}_f{int(round(sensitivity_f * 100)):03d}"
    type_limits_name = "EU_Step8_AnyNumber_Wm2"
    schedule_name = f"EU_Step8_GainSchedule_{suffix}"
    gain_name = f"EU_Step8_InternalGain_{suffix}"
    idf.newidfobject(
        "SCHEDULETYPELIMITS", Name=type_limits_name, Numeric_Type="Continuous", Unit_Type="Dimensionless"
    )
    idf.newidfobject(
        "SCHEDULE:FILE",
        Name=schedule_name,
        Schedule_Type_Limits_Name=type_limits_name,
        File_Name=str(output),
        Column_Number=1,
        Rows_to_Skip_at_Top=0,
        Number_of_Hours_of_Data=HOURS_PER_YEAR,
        Column_Separator="Comma",
        Interpolate_to_Timestep="No",
    )
    idf.newidfobject(
        "OTHEREQUIPMENT",
        Name=gain_name,
        Fuel_Type="Electricity",
        Zone_or_ZoneList_or_Space_or_SpaceList_Name=dwelling_zone,
        Schedule_Name=schedule_name,
        Design_Level_Calculation_Method="Watts/Area",
        Power_per_Zone_Floor_Area=1.0,
        Fraction_Latent=0.0,
        Fraction_Radiant=0.0,
        Fraction_Lost=0.0,
        EndUse_Subcategory="EU_Step8_InternalGains",
    )
    return {
        "schedule_name": schedule_name,
        "gain_name": gain_name,
        "csv_path": str(output),
        "sha256": digest,
        "mean_phi_int_w_m2": float(values.mean()),
        "zero_presence_days": zero_presence_days,
        "sensitivity_f": sensitivity_f,
    }
