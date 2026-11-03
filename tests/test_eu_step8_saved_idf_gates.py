"""Independent saved-IDF G8.12/G8.13 audit tests."""
from __future__ import annotations

import hashlib
from pathlib import Path

from openubem.validation.step8_gates import evaluate_saved_idf_schedule_gates


def _write_fixture(tmp_path: Path, *, assigned_schedule="gain_schedule", interpolate="No"):
    tmp_path.mkdir(parents=True, exist_ok=True)
    schedule = tmp_path / "gain.csv"
    schedule.write_text("3.0\n" * 8760, encoding="utf-8")
    idf = tmp_path / "saved.idf"
    idf.write_text(
        """Schedule:File,
  gain_schedule,
  Any Number,
  {schedule},
  1,
  1,
  8760,
  Comma,
  {interpolate},
  60,
  Yes;
OtherEquipment,
  gain_load,
  Zone One,
  {assigned_schedule},
  EquipmentLevel,
  1.0;
""".format(schedule=schedule.as_posix(), interpolate=interpolate, assigned_schedule=assigned_schedule),
        encoding="utf-8",
    )
    return idf, schedule


def _report(tmp_path: Path, **kwargs):
    idf, schedule = _write_fixture(tmp_path, **kwargs)
    checksum = hashlib.sha256(schedule.read_bytes()).hexdigest()
    return {finding.gate: finding for finding in evaluate_saved_idf_schedule_gates(
        idf, schedule_name="gain_schedule", schedule_path=schedule, schedule_sha256=checksum,
        assignment_object_type="OtherEquipment", assignment_object_name="gain_load",
    )}


def test_saved_idf_null_and_mutations(tmp_path: Path):
    clean = _report(tmp_path / "clean")
    assert clean["G8.12"].passed and clean["G8.13"].passed

    assignment = _report(tmp_path / "assignment", assigned_schedule="other_schedule")
    assert not assignment["G8.12"].passed and assignment["G8.13"].passed

    interpolation = _report(tmp_path / "interpolation", interpolate="Yes")
    assert interpolation["G8.12"].passed and not interpolation["G8.13"].passed
