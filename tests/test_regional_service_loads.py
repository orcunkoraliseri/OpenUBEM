"""Tests for DD3b region-aware service-loads reconstruction (T04).

Covers: regional JSON loads + all region×group sum to 1.0; NYC Office uses the
middle_atlantic mf_adj (≠ national) → different total; LA Multifamily falls back
to national (DD5) unchanged; unresolvable region → national path byte-identical;
thin-cell group uses national.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import pytest

from openubem.results.service_loads import (
    load_coefficients,
    reconstruct_building,
    reconstruct_frame,
    _MODELED_FRAC_KEYS,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REGIONAL_JSON = _REPO_ROOT / "openubem" / "data" / "service_loads" / "enduse_fractions_regional.json"
_TABLE4_JSON = _REPO_ROOT / "openubem" / "data" / "service_loads" / "enduse_fractions_table4.json"


def _office_row(city="nyc"):
    return {
        "osm_id": "way/office",
        "archetype_id": "LargeOffice",
        "city": city,
        "heating_eui_kwh_m2": 30.0,
        "cooling_eui_kwh_m2": 14.0,
        "lighting_eui_kwh_m2": 12.0,
        "equipment_eui_kwh_m2": 27.0,
        "total_eui_kwh_m2": 83.0,
        "simulation_status": "success",
    }


def _mf_row(city="la"):
    return {
        "osm_id": "way/mf",
        "archetype_id": "MidriseApartment",
        "city": city,
        "heating_eui_kwh_m2": 20.0,
        "cooling_eui_kwh_m2": 10.0,
        "lighting_eui_kwh_m2": 8.0,
        "equipment_eui_kwh_m2": 22.0,
        "total_eui_kwh_m2": 60.0,
        "simulation_status": "success",
    }


# ---------------------------------------------------------------------------
# (1) regional JSON loads; all region×group sum to 1.0
# ---------------------------------------------------------------------------

class TestRegionalJsonLoadsAndSums:
    def test_regional_json_exists(self):
        assert _REGIONAL_JSON.exists()

    def test_loads_with_validation(self):
        coeffs = load_coefficients(_REGIONAL_JSON)
        assert "fractions_by_region" in coeffs

    def test_all_region_group_sum_to_one(self):
        coeffs = load_coefficients(_REGIONAL_JSON)
        for region, groups in coeffs["fractions_by_region"].items():
            for group, fracs in groups.items():
                total = sum(fracs.values())
                assert abs(total - 1.0) < 1e-6, f"{region}/{group} sums to {total}"

    def test_national_block_verbatim_equals_table4(self):
        with open(_REGIONAL_JSON, encoding="utf-8") as fh:
            reg = json.load(fh)
        with open(_TABLE4_JSON, encoding="utf-8") as fh:
            t4 = json.load(fh)
        assert reg["fractions"] == t4["fractions"]
        assert reg["archetype_map"] == t4["archetype_map"]


# ---------------------------------------------------------------------------
# (2) NYC Office uses middle_atlantic mf_adj (≠ national) → different total
# ---------------------------------------------------------------------------

class TestNycOfficeUsesRegional:
    def _coeffs(self):
        return load_coefficients(_REGIONAL_JSON)

    def test_basis_is_regional(self):
        coeffs = self._coeffs()
        res = reconstruct_building(_office_row("nyc"), coeffs, region="middle_atlantic")
        assert res["reconstruction_basis"] == "regional_fraction_split"

    def test_modeled_frac_matches_ma_mf_adj(self):
        coeffs = self._coeffs()
        ma = coeffs["fractions_by_region"]["middle_atlantic"]["large_office"]
        mf = sum(ma[k] for k in _MODELED_FRAC_KEYS)
        # MA large_office mf_adj per derivation = 0.8633
        assert math.isclose(mf, 0.8633, abs_tol=1e-3)

    def test_total_differs_from_national(self):
        coeffs = self._coeffs()
        nat = reconstruct_building(_office_row("nyc"), coeffs, region=None)
        reg = reconstruct_building(_office_row("nyc"), coeffs, region="middle_atlantic")
        assert not math.isclose(
            nat["total_eui_reconstructed_kwh_m2"],
            reg["total_eui_reconstructed_kwh_m2"],
            rel_tol=1e-6,
        )

    def test_ma_total_lower_than_national(self):
        # MA mf_adj 0.8633 > national 0.83 → smaller uplift → lower reconstructed total
        coeffs = self._coeffs()
        nat = reconstruct_building(_office_row("nyc"), coeffs, region=None)
        reg = reconstruct_building(_office_row("nyc"), coeffs, region="middle_atlantic")
        assert reg["total_eui_reconstructed_kwh_m2"] < nat["total_eui_reconstructed_kwh_m2"]


# ---------------------------------------------------------------------------
# (3) LA Multifamily falls back to national (DD5) → total unchanged
# ---------------------------------------------------------------------------

class TestLaMultifamilyFallsBackToNational:
    def _coeffs(self):
        return load_coefficients(_REGIONAL_JSON)

    def test_mf_not_in_pacific_overrides(self):
        coeffs = self._coeffs()
        assert "mid_rise_apartment" not in coeffs["fractions_by_region"]["pacific"]

    def test_basis_is_national_even_with_region(self):
        coeffs = self._coeffs()
        res = reconstruct_building(_mf_row("la"), coeffs, region="pacific")
        assert res["reconstruction_basis"] == "table4_fraction_split"

    def test_total_equals_national_path(self):
        coeffs = self._coeffs()
        with_region = reconstruct_building(_mf_row("la"), coeffs, region="pacific")
        national = reconstruct_building(_mf_row("la"), coeffs, region=None)
        assert math.isclose(
            with_region["total_eui_reconstructed_kwh_m2"],
            national["total_eui_reconstructed_kwh_m2"],
            rel_tol=1e-12,
        )


# ---------------------------------------------------------------------------
# (4) Unresolvable region → national path, byte-identical to pre-change
# ---------------------------------------------------------------------------

class TestUnresolvableRegionNationalIdentity:
    def test_unknown_city_is_national(self):
        coeffs = load_coefficients(_REGIONAL_JSON)
        row = _office_row("chicago")  # not in F5 map
        reg_frame = reconstruct_frame(pd.DataFrame([row]), coeffs, force=True)
        national = reconstruct_building(row, coeffs, region=None)
        assert math.isclose(
            reg_frame.iloc[0]["total_eui_reconstructed_kwh_m2"],
            national["total_eui_reconstructed_kwh_m2"],
            rel_tol=1e-12,
        )

    def test_national_coeffs_identity_with_table4(self):
        """Reconstruct under regional JSON's national block reproduces table4 totals."""
        reg_coeffs = load_coefficients(_REGIONAL_JSON)
        t4_coeffs = load_coefficients(_TABLE4_JSON)
        row = _office_row("nyc")
        # region=None forces national path under both
        reg_nat = reconstruct_building(row, reg_coeffs, region=None)
        t4_res = reconstruct_building(row, t4_coeffs)
        assert math.isclose(
            reg_nat["total_eui_reconstructed_kwh_m2"],
            t4_res["total_eui_reconstructed_kwh_m2"],
            rel_tol=1e-12,
        )

    def test_no_region_col_is_national(self):
        """reconstruct_frame with no city column → national for all rows."""
        coeffs = load_coefficients(_REGIONAL_JSON)
        row = _office_row("nyc")
        del row["city"]
        out = reconstruct_frame(pd.DataFrame([row]), coeffs, force=True)
        assert out.iloc[0]["reconstruction_basis"] == "table4_fraction_split"


# ---------------------------------------------------------------------------
# (5) Thin-cell-fallback group uses national
# ---------------------------------------------------------------------------

class TestThinCellGroupUsesNational:
    def _coeffs(self):
        return load_coefficients(_REGIONAL_JSON)

    def test_supermarket_not_in_any_region(self):
        coeffs = self._coeffs()
        for region in ("middle_atlantic", "pacific", "west_south_central"):
            assert "supermarket" not in coeffs["fractions_by_region"][region]

    def test_supermarket_uses_national(self):
        coeffs = self._coeffs()
        row = {
            "osm_id": "way/sm",
            "archetype_id": "SuperMarket",
            "city": "la",
            "heating_eui_kwh_m2": 10.0,
            "cooling_eui_kwh_m2": 8.0,
            "lighting_eui_kwh_m2": 30.0,
            "equipment_eui_kwh_m2": 20.0,
            "total_eui_kwh_m2": 68.0,
            "simulation_status": "success",
        }
        res = reconstruct_building(row, coeffs, region="pacific")
        assert res["reconstruction_basis"] == "table4_fraction_split"


# ---------------------------------------------------------------------------
# (6) reconstruct_frame end-to-end region derivation
# ---------------------------------------------------------------------------

class TestReconstructFrameRegionDerivation:
    def test_nyc_office_row_regional_la_mf_national(self):
        coeffs = load_coefficients(_REGIONAL_JSON)
        df = pd.DataFrame([_office_row("nyc"), _mf_row("la")])
        out = reconstruct_frame(df, coeffs, force=True)
        office = out[out["osm_id"] == "way/office"].iloc[0]
        mf = out[out["osm_id"] == "way/mf"].iloc[0]
        assert office["reconstruction_basis"] == "regional_fraction_split"
        assert mf["reconstruction_basis"] == "table4_fraction_split"

    def test_frame_no_regional_block_is_national(self):
        """coeffs WITHOUT fractions_by_region → all rows national (byte-identical path)."""
        t4 = load_coefficients(_TABLE4_JSON)
        df = pd.DataFrame([_office_row("nyc")])
        out = reconstruct_frame(df, t4, force=True)
        assert out.iloc[0]["reconstruction_basis"] == "table4_fraction_split"
