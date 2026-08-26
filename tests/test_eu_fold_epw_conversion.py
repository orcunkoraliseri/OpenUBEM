"""Synthetic-fixture tests for scripts/convert_era5_eu_folds_to_epw.py.

Never touches live data or the network: archive presence is checked by
writing empty placeholder files with the right names, the row-building
physics is exercised on a small synthetic hourly frame built in memory, and
the --all-years orchestration is exercised with write_epw/completeness
stubbed so it never needs a full 25-archive fixture.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.convert_era5_eu_folds_to_epw as module  # noqa: E402
from scripts.convert_era5_eu_folds_to_epw import (  # noqa: E402
    archive_completeness,
    archives_for_year,
    convert_fold,
    convert_fold_year,
    diary_window,
    epw_rows,
    load_fold_targets,
    output_path_for_year,
    required_archives,
    resolve_year,
)


def _synthetic_entry(
    fold: str,
    city: str,
    latitude: float,
    longitude: float,
    utc_offset_hours: int,
    start_year: int,
    end_year: int,
    output_filename: str,
    status: str = "RULED_NOT_PINNED",
    diary_window: str | None = None,
    diary_window_status: str = "RULED_NOT_PINNED",
) -> dict[str, object]:
    """A registry entry shaped like the real one (field names copied from the live file)."""
    return {
        "fold": fold,
        "city": city,
        "station": None,
        "latitude": latitude,
        "longitude": longitude,
        "local_standard_utc_offset": utc_offset_hours,
        "raw_era5_window": f"{start_year}-01-01/{end_year}-12-31",
        "output_filename": output_filename,
        "status": status,
        "diary_window": diary_window,
        "diary_window_status": diary_window_status,
    }


def _write_registry(tmp_path: Path, entries: list[dict[str, object]]) -> Path:
    registry_path = tmp_path / "synthetic_weather_registry.json"
    registry_path.write_text(json.dumps({"targets": entries}), encoding="utf-8")
    return registry_path


def test_output_filenames_match_registry(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [
            _synthetic_entry("es", "Madrid", 40.45, -3.55, 1, 2009, 2010, "es_madrid_2009_2010.epw"),
            _synthetic_entry("uk", "London", 51.48, -0.45, 0, 2014, 2015, "uk_london_2014_2015.epw"),
            _synthetic_entry("it", "Bologna", 44.53, 11.29, 1, 2013, 2014, "it_bologna_2013_2014.epw"),
        ],
    )
    targets = load_fold_targets(registry_path)
    assert targets["es"]["output_filename"] == "es_madrid_2009_2010.epw"
    assert targets["uk"]["output_filename"] == "uk_london_2014_2015.epw"
    assert targets["it"]["output_filename"] == "it_bologna_2013_2014.epw"


def test_required_archive_count_is_boundary_plus_24_months(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [_synthetic_entry("es", "Madrid", 40.45, -3.55, 1, 2009, 2010, "es_madrid_2009_2010.epw")],
    )
    targets = load_fold_targets(registry_path)
    archives = required_archives(targets["es"])
    assert len(archives) == 25


def test_incomplete_year_skips_without_writing_epw(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [
            _synthetic_entry(
                "uk",
                "London",
                51.48,
                -0.45,
                0,
                2014,
                2015,
                "uk_london_2014_2015.epw",
            )
        ],
    )
    targets = load_fold_targets(registry_path)
    target = dict(targets["uk"])
    target["raw_dir"] = tmp_path / "raw_uk"
    target["raw_dir"].mkdir()
    year = target["start_year"]
    archives = archives_for_year(target, year)
    for path in archives[:-1]:
        path.write_bytes(b"x")
    output_dir = tmp_path / "out"
    monkeypatch.setattr(module, "OUTPUT_ROOT", output_dir)

    have, need, missing = archive_completeness(target)
    assert need == 25
    assert have < need
    assert len(missing) >= 1

    result = convert_fold_year(target, year)
    assert result is None
    assert not any(output_dir.rglob("*.epw"))


def test_missing_year_flag_on_unruled_fold_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(module, "OUTPUT_ROOT", tmp_path / "out")
    registry_path = _write_registry(
        tmp_path,
        [
            _synthetic_entry(
                "uk",
                "London",
                51.48,
                -0.45,
                0,
                2014,
                2015,
                "uk_london_2014_2015.epw",
                diary_window=None,
                diary_window_status="RULED_NOT_PINNED",
            )
        ],
    )
    targets = load_fold_targets(registry_path)
    target = targets["uk"]
    assert target["diary_window_status"] != "RULED_PINNED"

    convert_fold(target, None, False)

    captured = capsys.readouterr()
    assert f"YEAR_NOT_RULED uk {target['raw_era5_window']}" in captured.out
    assert not (module.OUTPUT_ROOT).exists() or not any(module.OUTPUT_ROOT.rglob("uk_*.epw"))


def test_year_outside_window_is_an_error(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [_synthetic_entry("es", "Madrid", 40.45, -3.55, 1, 2009, 2010, "es_madrid_2009_2010.epw")],
    )
    targets = load_fold_targets(registry_path)
    target = targets["es"]
    with pytest.raises(ValueError):
        resolve_year(target, 2099)
    with pytest.raises(ValueError):
        archives_for_year(target, 2099)


def test_all_years_emits_one_file_per_year_with_y_suffix(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [_synthetic_entry("es", "Madrid", 40.45, -3.55, 1, 2009, 2010, "es_madrid_2009_2010.epw")],
    )
    targets = load_fold_targets(registry_path)
    target = targets["es"]
    monkeypatch.setattr(module, "OUTPUT_ROOT", tmp_path)
    monkeypatch.setattr(module, "archive_completeness_for_year", lambda _t, _y: (13, 13, []))

    written: list[int] = []

    def _fake_write_epw(t: dict[str, object], year: int) -> Path:
        written.append(year)
        path = output_path_for_year(t, year)
        path.write_text("stub", encoding="utf-8")
        return path

    monkeypatch.setattr(module, "write_epw", _fake_write_epw)

    convert_fold(target, None, True)

    assert sorted(written) == [target["start_year"], target["end_year"]]
    assert (tmp_path / "es_madrid_2009_2010_y2009.epw").is_file()
    assert (tmp_path / "es_madrid_2009_2010_y2010.epw").is_file()


def _synthetic_frame(utc_start: pd.Timestamp, utc_end: pd.Timestamp) -> pd.DataFrame:
    index = pd.date_range(utc_start, utc_end, freq="h")
    hours = np.arange(len(index))
    frame = pd.DataFrame(
        {
            "t2m": 283.0 + 5.0 * np.sin(2 * np.pi * hours / (24 * 365)),
            "d2m": 278.0,
            "sp": 101000.0,
            "u10": 1.0,
            "v10": 0.5,
            "ssrd": np.clip(1_000_000.0 * np.sin(np.pi * (hours % 24) / 24.0), 0.0, None),
            "fdir": 0.0,
            "tcc": 0.5,
            "tp": 0.0001,
        },
        index=index,
    )
    return frame


def test_epw_rows_full_year_has_8760_rows(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [_synthetic_entry("es", "Madrid", 40.45, -3.55, 1, 2009, 2010, "es_madrid_2009_2010.epw")],
    )
    target = load_fold_targets(registry_path)["es"]
    year = target["start_year"]
    utc_start, utc_end = diary_window(target, year)
    frame = _synthetic_frame(utc_start, utc_end)
    rows = epw_rows(frame, target["latitude"], target["longitude"], target["elevation_m"], 1)
    assert len(rows) == 8760
    assert rows[0][0] == year
    assert rows[-1][0] == year


def _reconstructed_offsets(rows: list[list[object]], utc_index: pd.DatetimeIndex) -> set[float]:
    """The (local - utc) gap implied by every EPW row; a single value proves no DST jump."""
    offsets = set()
    for row, utc_stamp in zip(rows, utc_index):
        year, month, day, hour_field = row[0], row[1], row[2], row[3]
        local_stamp = pd.Timestamp(year=year, month=month, day=day) + pd.Timedelta(hours=hour_field - 1)
        offsets.add((local_stamp - utc_stamp).total_seconds() / 3600.0)
    return offsets


def test_local_standard_time_offset_is_fixed_no_dst(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [
            _synthetic_entry("es", "Madrid", 40.45, -3.55, 1, 2009, 2010, "es_madrid_2009_2010.epw"),
            _synthetic_entry("uk", "London", 51.48, -0.45, 0, 2014, 2015, "uk_london_2014_2015.epw"),
        ],
    )
    targets = load_fold_targets(registry_path)
    target_es = targets["es"]
    target_uk = targets["uk"]
    utc_start_es, utc_end_es = diary_window(target_es, target_es["start_year"])
    frame_es = _synthetic_frame(utc_start_es, utc_end_es)
    rows_es = epw_rows(frame_es, target_es["latitude"], target_es["longitude"], target_es["elevation_m"], 1)

    utc_start_uk, utc_end_uk = diary_window(target_uk, target_uk["start_year"])
    frame_uk = _synthetic_frame(utc_start_uk, utc_end_uk)
    rows_uk = epw_rows(frame_uk, target_uk["latitude"], target_uk["longitude"], target_uk["elevation_m"], 0)

    assert _reconstructed_offsets(rows_es, frame_es.index) == {1.0}
    assert _reconstructed_offsets(rows_uk, frame_uk.index) == {0.0}
