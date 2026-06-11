"""Tests for openubem/semantic/construction_sets.py — plan T08."""

import math

import numpy as np
import pandas as pd
import pytest

from openubem.semantic.construction_sets import (
    VINTAGE_U_FACTORS,
    apply_nan_vintage_provenance,
    append_vintage_nan_flag,
    get_construction_set,
    resolve_vintage,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _gdf(rows):
    return pd.DataFrame(rows)


# ── T08-1: VINTAGE_U_FACTORS completeness and monotonicity ────────────────────

def test_vintage_u_factors_keys():
    expected = {
        "DOERefPre1980", "DOERef1980to2004",
        "90.1-2007", "90.1-2010", "90.1-2013", "90.1-2016", "90.1-2019",
    }
    assert set(VINTAGE_U_FACTORS.keys()) == expected


def test_vintage_u_factors_committed_values():
    assert VINTAGE_U_FACTORS["DOERefPre1980"] == pytest.approx(1.6, abs=1e-9)
    assert VINTAGE_U_FACTORS["DOERef1980to2004"] == pytest.approx(1.583, abs=1e-3)
    assert VINTAGE_U_FACTORS["90.1-2007"] == pytest.approx(1.309, abs=1e-3)
    assert VINTAGE_U_FACTORS["90.1-2010"] == pytest.approx(1.309, abs=1e-3)
    assert VINTAGE_U_FACTORS["90.1-2013"] == pytest.approx(1.0, abs=1e-9)
    assert VINTAGE_U_FACTORS["90.1-2016"] == pytest.approx(1.0, abs=1e-9)
    assert VINTAGE_U_FACTORS["90.1-2019"] == pytest.approx(1.0, abs=1e-9)


def test_vintage_u_factors_monotonicity():
    order = [
        "DOERefPre1980", "DOERef1980to2004",
        "90.1-2007", "90.1-2010", "90.1-2013", "90.1-2016", "90.1-2019",
    ]
    factors = [VINTAGE_U_FACTORS[k] for k in order]
    for i in range(len(factors) - 1):
        assert factors[i] >= factors[i + 1], (
            f"Monotonicity violated: {order[i]}={factors[i]} < {order[i+1]}={factors[i+1]}"
        )


# ── T08-2: resolve_vintage bin edges ─────────────────────────────────────────

@pytest.mark.parametrize("year,expected", [
    (1900, "DOERefPre1980"),
    (1979, "DOERefPre1980"),
    (1980, "DOERef1980to2004"),
    (2003, "DOERef1980to2004"),
    (2004, "90.1-2007"),
    (2009, "90.1-2007"),
    (2010, "90.1-2013"),
    (2015, "90.1-2013"),
    (2016, "90.1-2019"),
    (2024, "90.1-2019"),
])
def test_resolve_vintage_bin_edges(year, expected):
    df = _gdf([{"year_built": year, "archetype_id": "MediumOffice", "climate_zone": "1A"}])
    vintage, _, _ = resolve_vintage(df)
    assert vintage.iloc[0] == expected, f"year {year} → {vintage.iloc[0]} (expected {expected})"


# ── T08-3: NaN year_built → DOERefPre1980 + flags ────────────────────────────

def test_resolve_vintage_nan_year():
    df = _gdf([
        {"year_built": float("nan"), "archetype_id": "MediumOffice", "climate_zone": "1A"},
        {"year_built": 2020.0,        "archetype_id": "MediumOffice", "climate_zone": "1A"},
    ])
    vintage, nan_rows, _ = resolve_vintage(df)
    assert vintage.iloc[0] == "DOERefPre1980"
    assert vintage.iloc[1] == "90.1-2019"
    assert 0 in nan_rows
    assert 1 not in nan_rows


def test_append_vintage_nan_flag():
    df = _gdf([
        {"year_built": float("nan"), "data_quality_flag": ""},
        {"year_built": 2020.0,        "data_quality_flag": "OTHER_FLAG"},
    ])
    nan_rows = pd.Index([0])
    result = append_vintage_nan_flag(df, nan_rows)
    assert "VINTAGE_NAN_PERMISSIVE_DEFAULT" in result.at[0, "data_quality_flag"]
    assert result.at[1, "data_quality_flag"] == "OTHER_FLAG"


def test_append_vintage_nan_flag_idempotent():
    df = _gdf([{"year_built": float("nan"), "data_quality_flag": "VINTAGE_NAN_PERMISSIVE_DEFAULT"}])
    nan_rows = pd.Index([0])
    result = append_vintage_nan_flag(df, nan_rows)
    flag = result.at[0, "data_quality_flag"]
    assert flag.count("VINTAGE_NAN_PERMISSIVE_DEFAULT") == 1


# ── T08-4: golden fixture — MediumOffice@1A, 90.1-2019 ───────────────────────

def test_golden_medium_office_2019_baseline():
    """
    R-2.2-1/2/3/4 golden (90.1-2019, CZ1, MediumOffice):
      u_roof=0.273/IEAD, u_wall=0.704/SteelFramed, u_window=2.839/shgc=0.23,
      u_floor=1.828, infiltration=0.000285
    """
    df = _gdf([{
        "archetype_id": "MediumOffice",
        "climate_zone": "1A",
        "year_built": 2020.0,
    }])
    vintage, _, _ = resolve_vintage(df)
    env = get_construction_set(df, vintage)

    assert env.at[0, "vintage_standard"] == "90.1-2019"
    assert env.at[0, "u_roof_w_m2k"] == pytest.approx(0.273, abs=0.001)
    assert env.at[0, "assembly_roof"] == "IEAD"
    assert env.at[0, "u_wall_w_m2k"] == pytest.approx(0.704, abs=0.001)
    assert env.at[0, "assembly_wall"] == "SteelFramed"
    assert env.at[0, "u_window_w_m2k"] == pytest.approx(2.839, abs=0.001)
    assert env.at[0, "shgc_window"] == pytest.approx(0.23, abs=0.01)
    assert env.at[0, "u_floor_w_m2k"] == pytest.approx(1.828, abs=0.001)
    assert env.at[0, "infiltration_m3_s_m2"] == pytest.approx(0.000285, abs=1e-7)


# ── T08-5: pre-1980 ×1.6 derived golden (R-2.2-7) ────────────────────────────

def test_golden_medium_office_pre1980_derived():
    """
    R-2.2-7 pre-1980 derived values (×1.6 factor on 90.1-2019 baseline):
      u_roof = 0.273×1.6 = 0.437
      u_wall = 0.704×1.6 = 1.126  (note: plan states 1.122 which used 0.701×1.6)
      u_window = 2.839×1.6 = 4.542
      u_floor = 1.828×1.6 = 2.925
    SHGC and infiltration unchanged.
    """
    df = _gdf([{
        "archetype_id": "MediumOffice",
        "climate_zone": "1A",
        "year_built": 1960.0,
    }])
    vintage, _, _ = resolve_vintage(df)
    assert vintage.iloc[0] == "DOERefPre1980"
    env = get_construction_set(df, vintage)

    assert env.at[0, "vintage_standard"] == "DOERefPre1980"
    assert env.at[0, "u_roof_w_m2k"] == pytest.approx(0.273 * 1.6, abs=0.002)
    assert env.at[0, "u_wall_w_m2k"] == pytest.approx(0.704 * 1.6, abs=0.002)
    assert env.at[0, "u_window_w_m2k"] == pytest.approx(2.839 * 1.6, abs=0.002)
    assert env.at[0, "u_floor_w_m2k"] == pytest.approx(1.828 * 1.6, abs=0.002)
    # Invariants
    assert env.at[0, "shgc_window"] == pytest.approx(0.23, abs=0.01)
    assert env.at[0, "infiltration_m3_s_m2"] == pytest.approx(0.000285, abs=1e-7)


# ── T08-6: provenance tokens ─────────────────────────────────────────────────

def test_provenance_standard_rows():
    df = _gdf([{
        "archetype_id": "MediumOffice",
        "climate_zone": "3A",
        "year_built": 2010.0,
    }])
    vintage, _, _ = resolve_vintage(df)
    env = get_construction_set(df, vintage)
    prov_cols = [c for c in env.columns if c.startswith("provenance_")]
    assert len(prov_cols) == 5
    for col in prov_cols:
        assert env.at[0, col] == "ASHRAE_STANDARD"


def test_provenance_nan_vintage_becomes_heuristic():
    df = _gdf([{
        "archetype_id": "MediumOffice",
        "climate_zone": "3A",
        "year_built": float("nan"),
    }])
    vintage, nan_rows, _ = resolve_vintage(df)
    env = get_construction_set(df, vintage)
    env = apply_nan_vintage_provenance(env, nan_rows)
    prov_cols = [c for c in env.columns if c.startswith("provenance_")]
    for col in prov_cols:
        assert env.at[0, col] == "HEURISTIC"


# ── T08-7: gap guard (custom table missing a zone) ───────────────────────────

def test_gap_guard_warns_and_fills(recwarn):
    """A custom table with a missing (archetype, zone) entry triggers a warning."""
    from openubem.semantic.construction_sets import _get_ashrae_table
    base = _get_ashrae_table()
    import copy
    custom = copy.deepcopy(base)
    del custom["MediumOffice"]["8"]  # remove CZ8 entry for MediumOffice

    df = _gdf([{
        "archetype_id": "MediumOffice",
        "climate_zone": "8",
        "year_built": 2020.0,
    }])
    vintage, _, _ = resolve_vintage(df)
    with pytest.warns(UserWarning, match="construction_lookup_gap"):
        env = get_construction_set(df, vintage, custom_table=custom)
    # Gap-filled rows get KDE_IMPUTED provenance
    prov_cols = [c for c in env.columns if c.startswith("provenance_")]
    for col in prov_cols:
        assert env.at[0, col] == "KDE_IMPUTED"


# ── T08-8: 29 archetypes × 16 zones completeness ────────────────────────────

def test_all_archetypes_all_zones():
    """Bundled table has exactly 29×16=464 entries with no NaN u_roof."""
    from openubem.semantic.construction_sets import _get_ashrae_table, _build_flat_lookup
    table = _get_ashrae_table()
    flat = _build_flat_lookup(table)
    assert len(flat) == 29 * 16, f"Expected 464 entries, got {len(flat)}"
    assert flat["u_roof_w_m2k"].notna().all(), "Some entries have NaN u_roof"
