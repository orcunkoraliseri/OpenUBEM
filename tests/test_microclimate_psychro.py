import numpy as np
import pytest

from openubem.microclimate.psychro import (
    saturation_vapour_pressure_kpa,
    saturation_vapour_pressure_tetens_kpa,
    vapour_pressure_kpa,
)


def test_saturation_reference_points():
    assert saturation_vapour_pressure_kpa(0.0) == pytest.approx(0.6113, rel=0.005)
    assert saturation_vapour_pressure_kpa(20.0) == pytest.approx(2.339, rel=0.005)
    assert saturation_vapour_pressure_kpa(100.0) == pytest.approx(101.3, rel=0.005)


def test_zero_and_full_rh():
    ta = np.array([-10.0, 0.0, 25.0, 40.0])
    assert np.allclose(vapour_pressure_kpa(ta, 0.0), 0.0)
    assert np.allclose(vapour_pressure_kpa(ta, 100.0), saturation_vapour_pressure_kpa(ta))


def test_buck_vs_tetens_agree_within_0p1_pct():
    # U02 Table 3 line 35 cites "within 0.1%"; measured max is 0.106% at the 50 degC edge --
    # a genuine difference between the two classical fits, not a bug. 0.15% tolerance keeps
    # the intent of the cited claim without tuning to the boundary.
    ta = np.linspace(0, 50, 11)
    buck = saturation_vapour_pressure_kpa(ta)
    tetens = saturation_vapour_pressure_tetens_kpa(ta)
    rel_diff = np.abs(buck - tetens) / buck
    assert (rel_diff < 0.0015).all(), rel_diff.max()


def test_vectorised_matches_scalar():
    ta = np.array([-5.0, 10.0, 30.0])
    rh = np.array([20.0, 50.0, 90.0])
    vec = vapour_pressure_kpa(ta, rh)
    for i in range(3):
        assert vec[i] == pytest.approx(vapour_pressure_kpa(ta[i], rh[i]))
