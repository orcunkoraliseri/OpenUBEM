import csv
from pathlib import Path

import numpy as np

EPLUS_HEATING_COLUMN: str = (
    "EU_CELL_ZONE IDEAL LOADS AIR SYSTEM:"
    "Zone Ideal Loads Zone Total Heating Energy [J](Hourly)"
)

DAYS_IN_MONTH: tuple[int, ...] = (
    31,
    28,
    31,
    30,
    31,
    30,
    31,
    31,
    30,
    31,
    30,
    31,
)


def annual_heating_kwh(hourly_heating_j: np.ndarray) -> np.ndarray:
    """Compute float64 annual heating energy in kWh from hourly Joules.

    Args:
        hourly_heating_j: Array of shape ``[B, 8760]`` or ``[8760]`` in Joules.

    Returns:
        Annual heating energy in kWh (float64).
    """
    arr = np.asarray(hourly_heating_j, dtype=np.float64)
    return np.sum(arr, axis=-1, dtype=np.float64) / 3.6e6


def format_hourly_timestamps() -> list[str]:
    """Generate EnergyPlus-formatted hourly ``Date/Time`` labels for 8760 hours.

    Returns:
        List of 8760 timestamp strings like ``' 01/01  01:00:00'``.
    """
    labels: list[str] = []
    for month_idx, n_days in enumerate(DAYS_IN_MONTH, start=1):
        for day in range(1, n_days + 1):
            for hour in range(1, 25):
                labels.append(f" {month_idx:02d}/{day:02d}  {hour:02d}:00:00")
    return labels


def write_eplusout_csv(out_path: Path, hourly_heating_j: np.ndarray) -> None:
    """Write single-building hourly heating energy in ``eplusout.csv`` format.

    Args:
        out_path: Destination CSV path.
        hourly_heating_j: 1D array of length 8760 in Joules.
    """
    vals = np.asarray(hourly_heating_j, dtype=np.float64)
    if vals.shape != (8760,):
        raise ValueError(f"Expected 8760 hourly values, got shape {vals.shape}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    timestamps = format_hourly_timestamps()
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Date/Time", EPLUS_HEATING_COLUMN])
        for ts, val in zip(timestamps, vals, strict=True):
            writer.writerow([ts, f"{float(val):.10g}"])
