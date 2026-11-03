from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import scripts.convert_era5_eu_folds_to_epw as converter  # noqa: E402
from openubem.acquisition.european_weather import (  # noqa: E402
    EUROPEAN_WEATHER_TARGETS,
    NEW_SURVEY_YEARS,
    city_slug,
    validate_epw_preflight,
)

REGISTRY = ROOT / "openubem" / "data" / "weather" / "weather_registry.json"

EXPECTED = {
    "at": ("Vienna", 1, "2007-01-01/2008-12-31", "at_vienna_2007_2008.epw", 2008),
    "ca": ("Montreal", -5, "2010-01-01/2011-12-31", "ca_montreal_2010_2011.epw", 2010),
    "fi": ("Helsinki", 2, "2008-01-01/2009-12-31", "fi_helsinki_2008_2009.epw", 2009),
    "za": ("Cape Town", 2, "2009-01-01/2010-12-31", "za_capetown_2009_2010.epw", 2010),
    "hu": ("Budapest", 1, "2008-01-01/2009-12-31", "hu_budapest_2008_2009.epw", 2009),
    "am": ("Yerevan", 4, "2007-01-01/2008-12-31", "am_yerevan_2007_2008.epw", 2008),
}


def _target(fold: str, tmp_path: Path) -> dict:
    city, offset, window, output, survey = EXPECTED[fold]
    start = int(window[:4])
    end = int(window.split("/")[1][:4])
    return {
        "fold": fold, "city": city, "station": "x", "latitude": 48.0, "longitude": 16.5,
        "elevation_m": converter.ELEVATIONS_M[fold], "utc_offset_hours": offset,
        "start_year": start, "end_year": end, "raw_era5_window": window,
        "diary_window": f"{survey}-01-01/{survey}-12-31", "diary_window_status": "RULED_PINNED",
        "survey_year": NEW_SURVEY_YEARS[fold],
        "raw_dir": tmp_path / f"era5_{city_slug(city)}_{start}_{end}", "output_filename": output,
    }


def test_seven_targets_are_in_the_code_table_and_registry():
    code = {t.fold: t for t in EUROPEAN_WEATHER_TARGETS}
    registry = {t["fold"]: t for t in json.loads(REGISTRY.read_text(encoding="utf-8"))["targets"]}
    for fold, (city, offset, window, output, survey) in EXPECTED.items():
        assert code[fold].city == city
        assert code[fold].local_standard_utc_offset == offset
        assert code[fold].raw_era5_window == window
        assert code[fold].output_filename == output
        entry = registry[fold]
        assert entry["diary_window"] == f"{survey}-01-01/{survey}-12-31"
        assert entry["diary_window_status"] == "RULED_PINNED"
        assert entry["licence_status"] == "CAPTURED_AT_DOWNLOAD"
        assert entry["status"] in ("RULED_NOT_PINNED", "RULED_PINNED", "RULED_PINNED_EXCEPTION")


def test_archive_list_for_positive_offset_has_previous_december_day(tmp_path: Path):
    target = _target("at", tmp_path)
    names = [p.name for p in converter.archives_for_year(target, 2008)]
    assert names[0] == "era5_vienna_2007-12-31.zip"
    assert names[1:] == [f"era5_vienna_2008-{m:02d}.zip" for m in range(1, 13)]
    assert converter.candidate_years(target) == [2008]


def test_archive_list_for_negative_offset_has_next_january_day(tmp_path: Path):
    target = _target("ca", tmp_path)
    names = [p.name for p in converter.archives_for_year(target, 2010)]
    assert names[:12] == [f"era5_montreal_2010-{m:02d}.zip" for m in range(1, 13)]
    assert names[12] == "era5_montreal_2011-01-01.zip"
    assert len(names) == 13


def test_negative_offset_utc_slice_runs_into_next_year(tmp_path: Path):
    start, end = converter.diary_window(_target("ca", tmp_path), 2010)
    assert start == pd.Timestamp("2010-01-01 05:00")
    assert end == pd.Timestamp("2011-01-01 04:00")


def _fake_load(utc_start, utc_end):
    index = pd.date_range(utc_start, utc_end, freq="h", name="utc")
    n = len(index)
    return pd.DataFrame({
        "t2m": np.full(n, 285.0), "d2m": np.full(n, 280.0), "sp": np.full(n, 100000.0),
        "u10": np.full(n, 2.0), "v10": np.full(n, 1.0), "ssrd": np.full(n, 0.0),
        "fdir": np.zeros(n), "tcc": np.full(n, 0.5), "tp": np.zeros(n),
    }, index=index)


@pytest.mark.parametrize("fold,survey", [("at", 2008), ("ca", 2010)])
def test_converted_year_has_8760_rows_and_drops_29_february(fold, survey, tmp_path, monkeypatch):
    target = _target(fold, tmp_path)
    monkeypatch.setattr(converter, "OUTPUT_ROOT", tmp_path)

    def fake(archives, utc_start, utc_end):
        return _fake_load(utc_start, utc_end), 48.0, 16.5

    monkeypatch.setattr(converter, "load_era5_hourly", fake)
    output = converter.write_epw(target, survey)
    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 8 + 8760
    assert lines[0].startswith(f"LOCATION,{target['city']},{target['city']},{converter.ISO3[fold]},ERA5,")
    fields = lines[0].split(",")
    assert float(fields[8]) == float(target["utc_offset_hours"])
    assert float(fields[9]) == converter.ELEVATIONS_M[fold]
    days = {(int(r.split(",")[1]), int(r.split(",")[2])) for r in lines[8:]}
    assert (2, 29) not in days
    assert len(days) == 365
    result = validate_epw_preflight(output)
    assert result["gate_2_8760_continuity"] == "PASS"


def test_original_folds_keep_their_year_candidates():
    targets = converter.load_fold_targets()
    assert set(targets) <= set(EXPECTED)
    for fold in ("es", "uk", "it"):
        entry = {"start_year": 2009, "end_year": 2010, "survey_year": None}
        assert converter.candidate_years(entry) == [2009, 2010]
