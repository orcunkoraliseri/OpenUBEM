"""Single source of fixed numeric Step 8 gate bands (V8.c)."""
from __future__ import annotations

from types import MappingProxyType


# These limits are the fixed parent Step 8 contract, not fitted values.  G8.7
# bands are archetype-specific inputs and therefore deliberately do not live
# here as a generic constant.
STEP8_GATE_BANDS = MappingProxyType({
    "G8.1.monthly_nmbe_pct": 5.0,
    "G8.2.hourly_nmbe_pct": 10.0,
    "G8.3.monthly_cvrmse_pct": 15.0,
    "G8.4.hourly_cvrmse_pct": 30.0,
    "G8.5.peak_relative_difference": 0.15,
    "G8.6.peak_timing_hours": 1,
    "G8.10.meter_balance_relative_difference": 0.005,
})
