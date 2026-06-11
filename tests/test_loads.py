"""Tests for openubem/semantic/loads.py — plan T09."""

import pandas as pd
import pytest

from openubem.semantic.loads import get_loads, _get_flat_loads


def _gdf(archetypes):
    return pd.DataFrame([{"archetype_id": a} for a in archetypes])


# ── T09-1: golden MediumOffice values (R-2.2 loads table) ────────────────────

def test_golden_medium_office():
    """
    MediumOffice DOE prototype loads (PNNL-20405):
      lighting=10.76 W/m², equipment=10.76 W/m², Occ=18.58 m²/person
      HTG=21.1°C, CLG=23.9°C, setback=15.6°C, setup=29.4°C, WWR=0.40
    """
    df = _gdf(["MediumOffice"])
    result = get_loads(df)
    assert result.at[0, "lighting_w_m2"] == pytest.approx(10.76, abs=0.01)
    assert result.at[0, "equipment_w_m2"] == pytest.approx(10.76, abs=0.01)
    assert result.at[0, "occupant_m2_per_person"] == pytest.approx(18.58, abs=0.1)
    assert result.at[0, "heating_setpoint_c"] == pytest.approx(21.1, abs=0.1)
    assert result.at[0, "cooling_setpoint_c"] == pytest.approx(23.9, abs=0.1)
    assert result.at[0, "heating_setback_c"] == pytest.approx(15.6, abs=0.1)
    assert result.at[0, "cooling_setup_c"] == pytest.approx(29.4, abs=0.1)
    assert result.at[0, "wwr"] == pytest.approx(0.40, abs=0.01)


# ── T09-2: DataCenter equipment_w_m2 > 100 W/m² ──────────────────────────────

def test_datacenter_equipment_exceeds_100():
    """DataCenter ITE loads are very high; ensure they are present and > 100 W/m²."""
    df = _gdf(["LargeDataCenterHighITE"])
    result = get_loads(df)
    assert result.at[0, "equipment_w_m2"] > 100.0, (
        f"Expected equipment_w_m2 > 100 W/m² for LargeDataCenterHighITE, got {result.at[0, 'equipment_w_m2']}"
    )


# ── T09-3: all 29 archetypes present (no gap) ────────────────────────────────

def test_all_29_archetypes_present():
    """Combined DOE+OS loads table must cover all 29 archetypes."""
    flat = _get_flat_loads()
    assert len(flat) == 29, f"Expected 29 archetype rows, got {len(flat)}"
    assert flat["lighting_w_m2"].notna().all(), "Some archetype rows have NaN lighting_w_m2"


# ── T09-4: provenance tokens ──────────────────────────────────────────────────

def test_loads_provenance_columns():
    df = _gdf(["SmallOffice"])
    result = get_loads(df)
    prov_cols = [c for c in result.columns if c.startswith("provenance_")]
    assert len(prov_cols) == 6  # F17: 6 load provenance columns (setback/setup share setpoint prov)
    for col in prov_cols:
        assert result.at[0, col] == "ASHRAE_STANDARD"


# ── T09-5: setpoint inversion guard ──────────────────────────────────────────

def test_setpoint_inversion_guard():
    """Manually patched inversion should raise ValueError."""
    from openubem.semantic import loads as loads_mod
    import copy

    original_flat = loads_mod._get_flat_loads()
    # Build a modified table with inverted setpoints for SmallOffice
    bad_table = original_flat.copy()
    bad_table.at["SmallOffice", "heating_setpoint_c"] = 30.0
    bad_table.at["SmallOffice", "cooling_setpoint_c"] = 20.0

    # Monkey-patch temporarily
    original = loads_mod._FLAT_LOADS
    loads_mod._FLAT_LOADS = bad_table
    try:
        df = _gdf(["SmallOffice"])
        with pytest.raises(ValueError, match="Setpoint inversion"):
            get_loads(df)
    finally:
        loads_mod._FLAT_LOADS = original


# ── T09-6: missing archetype raises ValueError ────────────────────────────────

def test_missing_archetype_raises():
    df = _gdf(["NonExistentBuilding"])
    with pytest.raises(ValueError, match="Loads table gap"):
        get_loads(df)
