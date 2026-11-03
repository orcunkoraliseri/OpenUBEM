"""EU-06 schedule-file contract tests; all inputs are local synthetic fixtures."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from openubem.semantic.european_schedules import (
    BASE_GAIN_W_M2,
    HOURS_PER_YEAR,
    build_step8_gain_series,
    emit_step8_gain_schedule,
    read_presence_csv,
)


class FakeIDF:
    def __init__(self) -> None:
        self.objects: list[tuple[str, dict[str, object]]] = []

    def newidfobject(self, object_type: str, **fields: object) -> dict[str, object]:
        self.objects.append((object_type, fields))
        return fields


def test_f0_control_is_constant_and_does_not_need_diary_or_chaining_rule():
    values, zero_days = build_step8_gain_series(None, 0.0)
    assert len(values) == HOURS_PER_YEAR
    assert np.all(values == BASE_GAIN_W_M2)
    assert zero_days is None


def test_all_five_levels_conserve_annual_gain_and_keep_zero_presence_days():
    presence = np.ones(HOURS_PER_YEAR)
    presence[:48] = 0.0
    for f in (0.0, 0.15, 0.30, 0.50, 1.00):
        values, zero_days = build_step8_gain_series(presence, f, chaining_rule="RULED_TEST")
        assert values.mean() == pytest.approx(BASE_GAIN_W_M2)
        assert zero_days == 2
        if f > 0:
            assert np.all(values[:48] == pytest.approx((1.0 - f) * BASE_GAIN_W_M2))


def test_injected_series_is_blocked_without_named_chaining_rule():
    with pytest.raises(ValueError, match="chaining_rule"):
        build_step8_gain_series(np.ones(HOURS_PER_YEAR), 0.15)


@pytest.mark.parametrize("invalid", [np.ones(8759), np.r_[np.ones(8759), np.nan], -np.ones(HOURS_PER_YEAR)])
def test_presence_contract_rejects_invalid_annual_series(invalid: np.ndarray):
    with pytest.raises(ValueError):
        build_step8_gain_series(invalid, 0.15, chaining_rule="RULED_TEST")


def test_emitter_uses_any_number_schedule_file_no_interpolation_and_one_gain_assignment(tmp_path: Path):
    idf = FakeIDF()
    result = emit_step8_gain_schedule(
        idf, sensitivity_f=0.0, dwelling_zone="Dwelling_1", dwelling_id="dwelling_1",
        emitted_csv_path=tmp_path / "f000.csv",
    )
    assert result["mean_phi_int_w_m2"] == pytest.approx(3.0)
    assert len(result["sha256"]) == 64
    assert np.all(read_presence_csv(tmp_path / "f000.csv") == 3.0)
    objects = dict(idf.objects)
    schedule = objects["SCHEDULE:FILE"]
    gain = objects["OTHEREQUIPMENT"]
    assert schedule["Interpolate_to_Timestep"] == "No"
    assert schedule["Schedule_Type_Limits_Name"] != "Fractional"
    assert gain["Schedule_Name"] == schedule["Name"]
    assert gain["Zone_or_ZoneList_or_Space_or_SpaceList_Name"] == "Dwelling_1"
    assert gain["Power_per_Zone_Floor_Area"] == 1.0
    assert all(kind != "PEOPLE" for kind, _fields in idf.objects)
