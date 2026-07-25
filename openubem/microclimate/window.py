"""T17 - analysis window selection (PLAN §7 T17).

Implements §4.9's scoping decision: Stage 6 runs over a selected analysis window, not the full
8760 h by default (a 1 km^2 cell at 1 m resolution is 10^6 cells; annual would be 8.76e9 UTCI
evaluations plus 8760 shadow rasters, per cell, across 12 cells -- not the right default).

Three modes, matching config.UTCI_ANALYSIS_WINDOW:
- "hottest_week" (default): the contiguous 168 h window maximising mean dry-bulb, deterministic
  tie-break on the earliest start (rolling mean over epw_df["dry_bulb_c"]).
- "design_hours": an explicit list of (month, day, hour) tuples, resolved against epw_df's own
  index (each tuple's nominal year is ignored -- matched on (month, day, hour) only, since
  epw_hourly.py's DatetimeIndex uses a fixed nominal year, T02's own progress-log note).
- "annual": the full epw_df index, unchanged.

T13's trap (this task's own "How"): refuse "annual" combined with
config.UTCI_WALL_TEMP_TIER == "energyplus" unless an explicit override is passed -- annual +
per-surface-per-hour EnergyPlus re-simulation across a layout_assign fleet is the same
multi-terabyte trap resim.py's own ResimRefusedError guards against (T13 module docstring), just
caught one layer earlier, at window-selection time, before any IDF is even touched.
"""
from __future__ import annotations

import pandas as pd

from openubem import config


class AnnualEnergyPlusWindowRefusedError(RuntimeError):
    """Raised when select_window(mode="annual") is requested while
    config.UTCI_WALL_TEMP_TIER == "energyplus", without override_annual_energyplus=True --
    T17's own structural trap guard (mirrors resim.py's ResimRefusedError, T13)."""


def _hottest_week(epw_df: pd.DataFrame) -> pd.DatetimeIndex:
    dry_bulb = epw_df["dry_bulb_c"]
    rolling_mean = dry_bulb.rolling(window=168).mean()
    # rolling(window=168) labels each window by its LAST timestamp; the window ending at
    # rolling_mean.idxmax() therefore starts 167 steps earlier. idxmax() itself already breaks
    # ties on the FIRST occurrence (pandas convention) -- the earliest-start tie-break the plan
    # requires.
    end_ts = rolling_mean.idxmax()
    end_pos = epw_df.index.get_loc(end_ts)
    start_pos = end_pos - 167
    return epw_df.index[start_pos : end_pos + 1]


def _design_hours(epw_df: pd.DataFrame, hours: "list[tuple[int, int, int]]") -> pd.DatetimeIndex:
    mmdh = list(zip(epw_df.index.month, epw_df.index.day, epw_df.index.hour))
    lookup = {key: ts for key, ts in zip(mmdh, epw_df.index)}
    missing = [h for h in hours if h not in lookup]
    if missing:
        raise ValueError(f"select_window(mode='design_hours'): not found in epw_df index: {missing}")
    return pd.DatetimeIndex([lookup[h] for h in hours])


def select_window(
    epw_df: pd.DataFrame,
    mode: str = None,
    *,
    design_hours: "list[tuple[int, int, int]] | None" = None,
    wall_temp_tier: str = None,
    override_annual_energyplus: bool = False,
) -> pd.DatetimeIndex:
    """Returns the DatetimeIndex of the selected analysis window, a subset of epw_df.index."""
    mode = mode or config.UTCI_ANALYSIS_WINDOW
    wall_temp_tier = wall_temp_tier if wall_temp_tier is not None else config.UTCI_WALL_TEMP_TIER

    if mode == "hottest_week":
        return _hottest_week(epw_df)
    if mode == "design_hours":
        if not design_hours:
            raise ValueError("select_window(mode='design_hours') requires design_hours=[(month, day, hour), ...]")
        return _design_hours(epw_df, design_hours)
    if mode == "annual":
        if wall_temp_tier == "energyplus" and not override_annual_energyplus:
            raise AnnualEnergyPlusWindowRefusedError(
                "select_window(mode='annual') refused while UTCI_WALL_TEMP_TIER='energyplus': "
                "a full-year Tier-2 EnergyPlus resim leg is a multi-terabyte trap (T13's own "
                "ResimRefusedError guards the same thing one layer later). Pass "
                "override_annual_energyplus=True only if you have deliberately sized for it."
            )
        return epw_df.index
    raise ValueError(f"select_window: unknown mode {mode!r}")
