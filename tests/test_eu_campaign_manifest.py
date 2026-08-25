"""EU-08 campaign-plan tests; no weather retrieval or simulation submission occurs."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from openubem.validation.european_campaign import (
    build_campaign_cells,
    cache_record_is_current,
    dependency_digest,
    dependency_fingerprints,
    load_campaign_archetypes,
    resumable_cache_hit,
    validate_campaign_cells,
    write_campaign_lists,
)


ROOT = Path(__file__).parents[1]
REGISTRIES = [
    ROOT / "openubem" / "data" / "construction" / f"tabula_archetypes_{fold}.json"
    for fold in ("es", "gb", "it")
]


def test_campaign_is_exactly_102_archetypes_by_five_levels_with_controls_first():
    records = load_campaign_archetypes(REGISTRIES)
    cells = build_campaign_cells(records)
    assert len(records) == 102
    assert len(cells) == 510
    assert sum(cell["sensitivity_f"] == 0.0 for cell in cells) == 102
    assert sum(cell["schedule_status"] == "BLOCKED_CHAINING_RULE" for cell in cells) == 408
    assert all(cell["weather_status"] == "RULED_NOT_PINNED" for cell in cells)
    for index in range(0, 510, 5):
        assert cells[index]["sensitivity_f"] == 0.0
        assert all(cell["control_cell_id"] == cells[index]["cell_id"] for cell in cells[index:index + 5])


def test_q3_and_q4_lists_have_the_pre_registered_counts(tmp_path: Path):
    lists = write_campaign_lists(build_campaign_cells(load_campaign_archetypes(REGISTRIES)), tmp_path)
    with lists["q3_control_cells.tsv"].open(encoding="utf-8", newline="") as stream:
        q3 = list(csv.DictReader(stream, delimiter="\t"))
    with lists["q4_injected_cells.tsv"].open(encoding="utf-8", newline="") as stream:
        q4 = list(csv.DictReader(stream, delimiter="\t"))
    assert len(q3) == 102
    assert len(q4) == 408
    assert all(row["epw_path"] == "PENDING_EU07_WEATHER" for row in q3 + q4)


def test_validation_rejects_a_duplicate_cell_id():
    cells = build_campaign_cells(load_campaign_archetypes(REGISTRIES))
    cells[1] = {**cells[1], "cell_id": cells[0]["cell_id"]}
    with pytest.raises(ValueError, match="unique"):
        validate_campaign_cells(cells)


def test_dependency_digest_measures_file_contents_and_all_declared_nonfile_dependencies(tmp_path: Path):
    idf = tmp_path / "case.idf"
    schedule = tmp_path / "case.csv"
    weather = tmp_path / "case.epw"
    idf.write_text("idf-v1", encoding="utf-8")
    schedule.write_text("schedule-v1", encoding="utf-8")
    weather.write_text("weather-v1", encoding="utf-8")
    kwargs = {
        "idf_path": idf,
        "schedule_path": schedule,
        "weather_path": weather,
        "energyplus_build": "EnergyPlus 23.1.0 build-abc",
        "adapter_config": {"timestep": 4, "gain_mode": "four_end_use_tabula_dhw"},
        "source_commit": "019ae9f",
    }
    initial = dependency_digest(**kwargs)
    assert initial == dependency_digest(**kwargs)
    fingerprints = dependency_fingerprints(**kwargs)
    assert fingerprints["idf_sha256"] != fingerprints["weather_sha256"]
    assert dependency_digest(**{**kwargs, "energyplus_build": "EnergyPlus 23.1.0 build-def"}) != initial
    assert dependency_digest(**{**kwargs, "adapter_config": {"timestep": 6}}) != initial
    assert dependency_digest(**{**kwargs, "source_commit": "different-commit"}) != initial
    idf.write_text("idf-v2", encoding="utf-8")
    assert dependency_digest(**kwargs) != initial
    idf.write_text("idf-v1", encoding="utf-8")
    weather.write_text("weather-v2", encoding="utf-8")
    assert dependency_digest(**kwargs) != initial
    weather.write_text("weather-v1", encoding="utf-8")
    schedule.write_text("schedule-v2", encoding="utf-8")
    assert dependency_digest(**kwargs) != initial
    with pytest.raises(ValueError, match="existing file"):
        dependency_digest(**{**kwargs, "weather_path": tmp_path / "missing.epw"})


def test_cache_hit_requires_legacy_success_status_and_exact_dependency_digest(tmp_path: Path):
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    (work_dir / "eplusout.end").write_text("EnergyPlus Completed Successfully", encoding="utf-8")
    (work_dir / "eplusout.sql").write_text("placeholder", encoding="utf-8")
    record = {"status": "success", "dependency_digest": "a" * 64}
    assert cache_record_is_current(record, expected_dependency_digest="a" * 64, legacy_is_completed=True)
    assert not cache_record_is_current(record, expected_dependency_digest="b" * 64, legacy_is_completed=True)
    assert not cache_record_is_current({**record, "status": "failed"}, expected_dependency_digest="a" * 64, legacy_is_completed=True)
    assert not cache_record_is_current(record, expected_dependency_digest="a" * 64, legacy_is_completed=False)
    assert resumable_cache_hit(work_dir, record, expected_dependency_digest="a" * 64)
    (work_dir / "eplusout.sql").unlink()
    assert not resumable_cache_hit(work_dir, record, expected_dependency_digest="a" * 64)
