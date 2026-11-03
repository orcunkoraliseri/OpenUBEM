"""X-04 saved-IDF arithmetic fixtures for D-EU-02.

These tests intentionally inspect a newly saved and independently reopened
IDF.  The dynamic EnergyPlus R3/R5/R7 fixtures are kept in the companion
integration test slice because they require the local engine executable.
"""
from __future__ import annotations

import pytest
from eppy.modeleditor import IDF

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.european_physics import (
    EU_INTERNAL_MASS_WH_M2K,
    add_b_factor_other_side_coefficients,
    add_european_internal_mass,
    add_nomass_construction,
    effective_u,
    internal_mass_capacity_j_k,
    r3_free_float_temperature_celsius,
    r3_time_constant_hours,
)


@pytest.fixture(autouse=True)
def _idd() -> None:
    IDF.setiddname(str(ENERGYPLUS_IDD_PATH))


@pytest.fixture
def blank_idf(tmp_path):
    path = tmp_path / "fixture.idf"
    path.write_text("Version,23.1;\nZone,Fixture Zone;\n", encoding="utf-8")
    return IDF(str(path))


def _reopen(idf, path):
    idf.saveas(str(path))
    return IDF(str(path))


def test_nomass_readback_realises_u_plus_delta_u(blank_idf, tmp_path):
    name = add_nomass_construction(blank_idf, "Wall", 0.70, 0.15)
    saved = _reopen(blank_idf, tmp_path / "saved.idf")
    construction = saved.getobject("CONSTRUCTION", name)
    material = saved.getobject("MATERIAL:NOMASS", construction.Outside_Layer)
    assert 1.0 / float(material.Thermal_Resistance) == pytest.approx(0.85, abs=1e-12)
    assert effective_u(0.70, 0.15) == pytest.approx(0.85)


def test_internal_mass_readback_equals_declared_cm_times_floor_area(blank_idf, tmp_path):
    mass_name = add_european_internal_mass(blank_idf, "Fixture Zone", 100.0)
    saved = _reopen(blank_idf, tmp_path / "saved.idf")
    assert internal_mass_capacity_j_k(saved, mass_name) == pytest.approx(
        EU_INTERNAL_MASS_WH_M2K * 3600.0 * 100.0, abs=1e-6
    )
    mass = saved.getobject("INTERNALMASS", mass_name)
    assert float(mass.Surface_Area) == pytest.approx(100.0)


def test_other_side_coefficients_readback_is_half_zone_and_half_outdoor(blank_idf, tmp_path):
    name = add_b_factor_other_side_coefficients(blank_idf, "HalfBoundary")
    saved = _reopen(blank_idf, tmp_path / "saved.idf")
    coeff = saved.getobject("SURFACEPROPERTY:OTHERSIDECOEFFICIENTS", name)
    assert float(coeff.Zone_Air_Temperature_Coefficient) == pytest.approx(0.5)
    assert float(coeff.External_DryBulb_Temperature_Coefficient) == pytest.approx(0.5)
    assert 0.5 * 20.0 + 0.5 * 0.0 == pytest.approx(10.0)


@pytest.mark.parametrize(("b_factor", "zone_coefficient", "outdoor_coefficient"), [(0.0, 1.0, 0.0), (1.0, 0.0, 1.0)])
def test_b_factor_endpoints_preserve_tabula_loss_semantics(
    blank_idf, tmp_path, b_factor, zone_coefficient, outdoor_coefficient
):
    name = add_b_factor_other_side_coefficients(blank_idf, f"Boundary{b_factor:g}", b_factor)
    saved = _reopen(blank_idf, tmp_path / f"boundary_{b_factor:g}.idf")
    coeff = saved.getobject("SURFACEPROPERTY:OTHERSIDECOEFFICIENTS", name)
    assert float(coeff.Zone_Air_Temperature_Coefficient) == pytest.approx(zone_coefficient)
    assert float(coeff.External_DryBulb_Temperature_Coefficient) == pytest.approx(outdoor_coefficient)


@pytest.mark.parametrize("u,delta", [(0.0, 0.0), (0.2, -0.3)])
def test_effective_u_rejects_nonpositive_realisations(u, delta):
    with pytest.raises(ValueError, match="must be positive"):
        effective_u(u, delta)


def test_r3_reference_time_constant_and_temperature():
    """DR11 R3 reference: 1.62e7 J/K and 320 W/K cool to 20/e at tau."""
    tau = r3_time_constant_hours(1.62e7, 320.0)
    assert tau == pytest.approx(14.0625)
    assert r3_free_float_temperature_celsius(20.0, 0.0, tau, 1.62e7, 320.0) == pytest.approx(
        7.3576, abs=0.0001
    )
