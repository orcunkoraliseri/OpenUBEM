"""
T06 — Deterministic unit tests for r6_4_basis_overlay.py.

No EnergyPlus, no network, no I/O.  Uses in-memory fixtures only.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts/validation to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "validation"))
from r6_4_basis_overlay import apply_basis, COOLING_COP, HEATING_FUEL_FACTOR


# ---------------------------------------------------------------------------
# apply_basis — exact arithmetic
# ---------------------------------------------------------------------------

class TestApplyBasisArithmetic:
    """Worked example from plan §4/§6 T04: cooling=350, heating=119."""

    def test_cooling_corrected(self):
        result = apply_basis(cooling_thermal=350, heating_thermal=119,
                             lighting=0, equipment=0, other=0)
        # 350 / 3.5 = 100.0 exactly
        assert result["cooling_corr"] == pytest.approx(100.0, abs=1e-9)

    def test_heating_corrected(self):
        result = apply_basis(cooling_thermal=350, heating_thermal=119,
                             lighting=0, equipment=0, other=0)
        # 119 * 1.19 = 141.61
        assert result["heating_corr"] == pytest.approx(141.61, abs=1e-9)

    def test_total_corrected(self):
        result = apply_basis(cooling_thermal=350, heating_thermal=119,
                             lighting=0, equipment=0, other=0)
        # 100.0 + 141.61 = 241.61
        assert result["total_corr"] == pytest.approx(241.61, abs=1e-9)

    def test_lighting_unchanged(self):
        result = apply_basis(cooling_thermal=100, heating_thermal=50,
                             lighting=30.5, equipment=20.0, other=5.0)
        assert result["lighting_corr"] == pytest.approx(30.5, abs=1e-9)

    def test_equipment_unchanged(self):
        result = apply_basis(cooling_thermal=100, heating_thermal=50,
                             lighting=30.5, equipment=20.0, other=5.0)
        assert result["equipment_corr"] == pytest.approx(20.0, abs=1e-9)

    def test_other_unchanged(self):
        result = apply_basis(cooling_thermal=100, heating_thermal=50,
                             lighting=30.5, equipment=20.0, other=5.0)
        assert result["other_corr"] == pytest.approx(5.0, abs=1e-9)

    def test_zero_cooling_zero_heating(self):
        result = apply_basis(cooling_thermal=0, heating_thermal=0,
                             lighting=10, equipment=5, other=2)
        assert result["cooling_corr"] == pytest.approx(0.0, abs=1e-9)
        assert result["heating_corr"] == pytest.approx(0.0, abs=1e-9)
        assert result["total_corr"] == pytest.approx(17.0, abs=1e-9)

    def test_custom_cop_and_fuel_factor(self):
        result = apply_basis(cooling_thermal=350, heating_thermal=100,
                             lighting=0, equipment=0, other=0,
                             cop=7.0, fuel_factor=2.0)
        assert result["cooling_corr"] == pytest.approx(50.0, abs=1e-9)
        assert result["heating_corr"] == pytest.approx(200.0, abs=1e-9)
        assert result["total_corr"] == pytest.approx(250.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Module constants match plan §4/F-5
# ---------------------------------------------------------------------------

class TestModuleConstants:
    def test_cop_value(self):
        assert COOLING_COP == 3.5

    def test_fuel_factor_value(self):
        # 1.19 exactly (NE fuel-mix factor from MEMO_phaseB_cbecs_diagnosis.md)
        assert HEATING_FUEL_FACTOR == pytest.approx(1.19, abs=1e-9)


# ---------------------------------------------------------------------------
# Decomposition contribution-sum invariant
# ---------------------------------------------------------------------------

class TestContributionSumInvariant:
    """contributions sum to total_dev by construction."""

    def _make_row(self, ref_heat, ref_cool, ref_light, ref_equip, ref_total,
                  ctr_heat, ctr_cool, ctr_light, ctr_equip, ctr_total):
        ref_other = ref_total - (ref_heat + ref_cool + ref_light + ref_equip)
        ctr_other = ctr_total - (ctr_heat + ctr_cool + ctr_light + ctr_equip)
        total_dev = (ctr_total - ref_total) / ref_total * 100
        contrib_heat = (ctr_heat - ref_heat) / ref_total * 100
        contrib_cool = (ctr_cool - ref_cool) / ref_total * 100
        contrib_light = (ctr_light - ref_light) / ref_total * 100
        contrib_equip = (ctr_equip - ref_equip) / ref_total * 100
        contrib_other = (ctr_other - ref_other) / ref_total * 100
        contrib_sum = contrib_heat + contrib_cool + contrib_light + contrib_equip + contrib_other
        return total_dev, contrib_sum

    def test_sum_equals_total_dev_positive(self):
        total_dev, contrib_sum = self._make_row(
            ref_heat=10, ref_cool=20, ref_light=30, ref_equip=15, ref_total=100,
            ctr_heat=15, ctr_cool=25, ctr_light=35, ctr_equip=20, ctr_total=120,
        )
        assert total_dev == pytest.approx(contrib_sum, abs=1e-6)

    def test_sum_equals_total_dev_negative(self):
        total_dev, contrib_sum = self._make_row(
            ref_heat=50, ref_cool=100, ref_light=200, ref_equip=300, ref_total=700,
            ctr_heat=10, ctr_cool=20, ctr_light=30, ctr_equip=40, ctr_total=150,
        )
        assert total_dev == pytest.approx(contrib_sum, abs=1e-6)

    def test_sum_equals_total_dev_mixed_signs(self):
        total_dev, contrib_sum = self._make_row(
            ref_heat=100, ref_cool=5, ref_light=50, ref_equip=200, ref_total=500,
            ctr_heat=50, ctr_cool=80, ctr_light=10, ctr_equip=150, ctr_total=400,
        )
        assert total_dev == pytest.approx(contrib_sum, abs=1e-6)


# ---------------------------------------------------------------------------
# N/A handling — data centres should not raise
# ---------------------------------------------------------------------------

class TestNAHandling:
    """Data-centre rows carry None end-uses; basis overlay should handle them
    if called explicitly; the producer script skips them at the loop level."""

    def test_zero_inputs_no_raise(self):
        # SmallDataCenterLowITE has zero heating — must not blow up
        result = apply_basis(cooling_thermal=1000, heating_thermal=0,
                             lighting=50, equipment=500, other=200)
        assert result["heating_corr"] == pytest.approx(0.0, abs=1e-9)
        assert result["cooling_corr"] == pytest.approx(1000 / 3.5, abs=1e-6)

    def test_pure_function_no_side_effects(self):
        r1 = apply_basis(cooling_thermal=100, heating_thermal=100,
                         lighting=10, equipment=10, other=5)
        r2 = apply_basis(cooling_thermal=100, heating_thermal=100,
                         lighting=10, equipment=10, other=5)
        assert r1 == r2
