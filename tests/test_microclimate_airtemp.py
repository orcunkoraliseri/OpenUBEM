import numpy as np
import pytest

from openubem.microclimate.airtemp import (
    DAY_HVAC_CANYON_CAP_C,
    NIGHT_HVAC_CANYON_CAP_C,
    air_temperature_field,
    air_temperature_field_tier0,
    air_temperature_field_tier1,
)


def test_tier0_equals_epw_value_everywhere():
    ta = air_temperature_field_tier0(35.0, (5, 5))
    assert np.all(ta == 35.0)


def test_tier1_offset_zero_when_svf_one_and_no_cooling():
    svf = np.ones((4, 4))
    ta_c, offset_c, flags = air_temperature_field_tier1(35.0, (4, 4), svf=svf, altitude_deg=60.0)
    assert np.allclose(offset_c, 0.0)
    assert np.allclose(ta_c, 35.0)
    assert np.all(flags == 0)


def test_tier1_day_offset_within_cited_envelope():
    svf = np.zeros((3, 3))  # fully enclosed canyon -> max canyon term
    cooling = np.full((3, 3), 100.0)
    ta_c, offset_c, flags = air_temperature_field_tier1(
        35.0, (3, 3), svf=svf, altitude_deg=60.0, cooling_energy_wm2=cooling
    )
    assert np.all(offset_c >= 0.0)
    assert np.all(offset_c <= DAY_HVAC_CANYON_CAP_C + 1e-9)


def test_tier1_night_offset_within_cited_envelope():
    svf = np.zeros((3, 3))
    cooling = np.full((3, 3), 100.0)
    ta_c, offset_c, flags = air_temperature_field_tier1(
        20.0, (3, 3), svf=svf, altitude_deg=-10.0, cooling_energy_wm2=cooling
    )
    assert np.all(offset_c >= 0.0)
    assert np.all(offset_c <= NIGHT_HVAC_CANYON_CAP_C + 1e-9)


def test_tier1_offset_clamp_flag_fires_at_full_enclosure_plus_hvac():
    svf = np.zeros((2, 2))
    cooling = np.full((2, 2), 100.0)
    ta_c, offset_c, flags = air_temperature_field_tier1(
        35.0, (2, 2), svf=svf, altitude_deg=60.0, cooling_energy_wm2=cooling
    )
    # canyon alone already reaches the cap (svf=0), so adding a positive hvac term must clamp.
    assert np.all(flags == 1)
    assert np.allclose(offset_c, DAY_HVAC_CANYON_CAP_C)


def test_tier1_reconstructs_tier0_plus_offset_exactly():
    svf = np.array([[1.0, 0.5], [0.2, 0.0]])
    ta_c, offset_c, flags = air_temperature_field_tier1(30.0, (2, 2), svf=svf, altitude_deg=45.0)
    ta0 = air_temperature_field_tier0(30.0, (2, 2))
    assert np.allclose(ta_c, ta0 + offset_c)


def test_hvac_offset_monotonic_in_relative_cooling_load():
    svf = np.ones((1, 3))  # isolate the hvac term -- canyon term is 0 at svf=1
    cooling = np.array([[0.0, 50.0, 100.0]])
    ta_c, offset_c, flags = air_temperature_field_tier1(35.0, (1, 3), svf=svf, altitude_deg=60.0, cooling_energy_wm2=cooling)
    assert offset_c[0, 0] < offset_c[0, 1] < offset_c[0, 2]
    assert offset_c[0, 2] == pytest.approx(DAY_HVAC_CANYON_CAP_C, abs=1e-9)


def test_dispatcher_tier0_default():
    ta_c, offset_c, flags = air_temperature_field(35.0, (3, 3))
    assert np.all(ta_c == 35.0)
    assert np.all(offset_c == 0.0)


def test_dispatcher_tier1_requires_svf_and_altitude():
    with pytest.raises(ValueError):
        air_temperature_field(35.0, (3, 3), tier="tier1")


def test_dispatcher_unknown_tier_raises():
    with pytest.raises(ValueError):
        air_temperature_field(35.0, (3, 3), tier="not_a_tier")
