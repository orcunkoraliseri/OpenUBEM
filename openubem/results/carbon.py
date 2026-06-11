"""Step-5 Module 14: GWP calculation per DESIGN §3E (load_referenced_v1)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from openubem import config

_EGRID_PATH = Path(__file__).parent.parent / "data" / "carbon" / "egrid_2022.json"


@lru_cache(maxsize=1)
def load_egrid() -> dict[str, dict]:
    """Return egrid_2022.json as {state_abbr: {"factor_kgco2_kwh": float, ...}}."""
    with open(_EGRID_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def get_elec_factor(state: str) -> float:
    """Lookup eGRID electricity emission factor (kg CO₂e / kWh) by two-letter state code.

    Raises KeyError if state is not in egrid_2022.json.
    """
    egrid = load_egrid()
    return float(egrid[state.upper()]["factor_kgco2_kwh"])


def compute_gwp(
    row: "pd.Series | dict[str, Any]",
    state: str,
) -> dict[str, float]:
    """Compute five GWP columns per DESIGN §3E (load_referenced_v1, no η/COP).

    Heating is gas × 0.181 kg CO₂e/kWh (DESIGN line 142).
    Cooling/lighting/equipment are electricity × eGRID factor for `state`.
    Returns dict with gwp_heating/cooling/lighting/equipment/total_kgco2_m2.
    """
    if isinstance(row, dict):
        get = row.get
    else:
        get = lambda k, d=None: (row[k] if k in row.index else d)  # noqa: E731

    def _safe(key: str) -> float:
        v = get(key)
        if v is None:
            return float("nan")
        try:
            return float(v)
        except (TypeError, ValueError):
            return float("nan")

    heating_eui = _safe("heating_eui_kwh_m2")
    cooling_eui = _safe("cooling_eui_kwh_m2")
    lighting_eui = _safe("lighting_eui_kwh_m2")
    equipment_eui = _safe("equipment_eui_kwh_m2")

    import math
    if any(math.isnan(v) for v in [heating_eui, cooling_eui, lighting_eui, equipment_eui]):
        nan = float("nan")
        return {
            "gwp_heating_kgco2_m2": nan,
            "gwp_cooling_kgco2_m2": nan,
            "gwp_lighting_kgco2_m2": nan,
            "gwp_equipment_kgco2_m2": nan,
            "gwp_total_kgco2_m2": nan,
        }

    f_gas = config.GWP_NATURAL_GAS_KGCO2_KWH
    f_elec = get_elec_factor(state)

    gwp_h = heating_eui * f_gas
    gwp_c = cooling_eui * f_elec
    gwp_l = lighting_eui * f_elec
    gwp_e = equipment_eui * f_elec

    return {
        "gwp_heating_kgco2_m2": gwp_h,
        "gwp_cooling_kgco2_m2": gwp_c,
        "gwp_lighting_kgco2_m2": gwp_l,
        "gwp_equipment_kgco2_m2": gwp_e,
        "gwp_total_kgco2_m2": gwp_h + gwp_c + gwp_l + gwp_e,
    }


def attach_gwp(
    parsed_row: dict[str, Any],
    state: str,
) -> dict[str, Any]:
    """In-place update parsed_row with GWP columns; return the row."""
    parsed_row.update(compute_gwp(parsed_row, state))
    return parsed_row
