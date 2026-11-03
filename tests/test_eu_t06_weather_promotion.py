"""Synthetic-fixture tests for scripts/run_eu_t06_weather_promotion.py (EU-07/T06).

No network, no live EnergyPlus: gate 6 is stubbed to a fixed verdict, and archive
completeness/conversion are stubbed the way test_eu_fold_epw_conversion.py stubs
scripts/convert_era5_eu_folds_to_epw.py, so no real ERA5 archive or EnergyPlus run is needed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import scripts.convert_era5_eu_folds_to_epw as convert_module
import scripts.run_eu_t06_weather_promotion as orchestrator

_HOURS = pd.date_range("2001-01-01", periods=8760, freq="h")
_HOURS_IN_MONTH = {m: int((_HOURS.month == m).sum()) for m in range(1, 13)}
_GATE5_MONTHS_KEY = "monthly_ghi_kwh_m2"


def _write_epw(path: Path, ghi_wm2: float = 200.0) -> None:
    header = [
        "LOCATION,Test,State,Country,ERA5,000000,45.72,4.95,1.0,200.0",
        "DESIGN CONDITIONS,0", "TYPICAL/EXTREME PERIODS,0", "GROUND TEMPERATURES,0",
        "HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0", "COMMENTS 1,synthetic test only",
        "COMMENTS 2,no weather data claim", "DATA PERIODS,1,1,Data,Sunday,1/1,12/31",
    ]
    rows = []
    for stamp in _HOURS:
        f = ["2001", str(stamp.month), str(stamp.day), str(stamp.hour + 1), "60", "0", "10", "5",
             "50", "101325", "0", "0", "0", str(ghi_wm2), "0", str(ghi_wm2), "0", "0", "0", "0",
             "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]
        rows.append(",".join(f))
    path.write_text("\n".join(header + rows) + "\n", encoding="utf-8")


def _write_benchmark(path: Path, ghi_wm2: float = 200.0) -> None:
    monthly = [_HOURS_IN_MONTH[m] * ghi_wm2 / 1000.0 for m in range(1, 13)]
    path.write_text(json.dumps({"source": "synthetic benchmark", _GATE5_MONTHS_KEY: monthly}), encoding="utf-8")


def _registry(tmp_path: Path, raw_era5_window: str) -> Path:
    entry = {
        "fold": "es", "city": "Madrid", "station": "Madrid Barajas/Retiro", "wmo": "08221",
        "latitude": 40.45, "longitude": -3.55, "raw_era5_window": raw_era5_window,
        "local_standard_utc_offset": 1, "output_filename": "es_madrid_test.epw",
        "status": "RULED_NOT_PINNED", "weather_file": None, "sha256": None,
        "licence_text_at_download": None, "licence_status": "CAPTURE_AT_DOWNLOAD",
        "diary_window": None, "diary_window_status": "RULED_NOT_PINNED",
        "acquisition_status": "IN_PROGRESS_ERA5_DOWNLOAD",
        "validation": {
            "gate_1_header": "PENDING_FILE", "gate_2_8760_continuity": "PENDING_FILE",
            "gate_3_no_missing_mandatory_fields": "PENDING_FILE",
            "gate_4_physical_and_solar_bounds": "PENDING_FILE",
            "gate_5_monthly_national_benchmark": "PENDING_FILE_AND_BENCHMARK",
            "gate_6_energyplus_smoke": "PENDING_FILE",
        },
        "acquisition_status_note": "pre-T06 placeholder",
    }
    registry = {"schema_version": 1, "status": "PARTIALLY_PINNED", "targets": [entry]}
    path = tmp_path / "weather_registry.json"
    path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    return path


def _setup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, raw_era5_window: str, have_need: tuple[int, int]):
    """Wire up a fold ready for process_fold: registry, completeness, conversion, gate 6."""
    registry_path = _registry(tmp_path, raw_era5_window)
    target = convert_module.load_fold_targets(registry_path)["es"]
    monkeypatch.setattr(convert_module, "archive_completeness", lambda _t: (have_need[0], have_need[1], []))
    monkeypatch.setattr(convert_module, "OUTPUT_ROOT", tmp_path / "epw_out")
    monkeypatch.setattr(convert_module, "archive_completeness_for_year", lambda _t, _y: (13, 13, []))

    def _fake_write_epw(t: dict[str, object], year: int) -> Path:
        path = convert_module.output_path_for_year(t, year)
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_epw(path)
        return path

    monkeypatch.setattr(convert_module, "write_epw", _fake_write_epw)
    monkeypatch.setattr(orchestrator.ew, "evaluate_energyplus_smoke_gate", lambda *a, **k: {"verdict": "PASS"})
    return registry_path, target


def _process(tmp_path: Path, target, registry_path: Path, *, commit: bool, benchmark_dir: Path | None = None):
    return orchestrator.process_fold(
        "es", target,
        benchmark_dir=benchmark_dir or tmp_path / "no_benchmarks",
        energyplus_root=tmp_path / "no_such_energyplus",
        tolerance_pct=10.0, approved_months={},
        evidence_dir=tmp_path / "evidence", registry_path=registry_path, commit=commit,
    )


def test_incomplete_archives_skip_and_never_convert(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    registry_path, target = _setup(monkeypatch, tmp_path, "2020-01-01/2020-12-31", (5, 13))

    def _fail(_t, _y):
        raise AssertionError("convert_fold_year must not be called when archives are incomplete")

    monkeypatch.setattr(convert_module, "convert_fold_year", _fail)

    decision = _process(tmp_path, target, registry_path, commit=False)

    assert decision == "SKIP_INCOMPLETE"
    assert not (tmp_path / "evidence").exists()


def test_missing_benchmark_pends_gate5_and_blocks_promotion(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    registry_path, target = _setup(monkeypatch, tmp_path, "2020-01-01/2020-12-31", (13, 13))

    decision = _process(tmp_path, target, registry_path, commit=True, benchmark_dir=tmp_path / "no_such_dir")

    assert decision == "STOP"
    report = json.loads((tmp_path / "evidence" / "t06_es_2020_six_gates.json").read_text())
    assert report["gate_5_monthly_national_benchmark"] == "PENDING_FILE_AND_BENCHMARK"
    after = json.loads(registry_path.read_text())["targets"][0]
    assert after["status"] == "RULED_NOT_PINNED"
    assert after["weather_file"] is None


def test_two_candidate_years_all_gates_pass_still_stops(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    registry_path, target = _setup(monkeypatch, tmp_path, "2009-01-01/2010-12-31", (25, 25))
    assert target["diary_window_status"] != "RULED_PINNED"
    benchmark_dir = tmp_path / "benchmarks"
    benchmark_dir.mkdir()
    _write_benchmark(benchmark_dir / "es_2009_monthly_ghi_benchmark.json")
    _write_benchmark(benchmark_dir / "es_2010_monthly_ghi_benchmark.json")

    decision = _process(tmp_path, target, registry_path, commit=True, benchmark_dir=benchmark_dir)

    assert decision == "STOP"
    gate_keys = (
        "gate_1_header", "gate_2_8760_continuity", "gate_3_no_missing_mandatory_fields",
        "gate_4_physical_and_solar_bounds", "gate_5_monthly_national_benchmark", "gate_6_energyplus_smoke",
    )
    for year in (2009, 2010):
        report = json.loads((tmp_path / "evidence" / f"t06_es_{year}_six_gates.json").read_text())
        assert all(report[key] in ("PASS", "PASS_WITH_DOCUMENTED_EXCEPTION") for key in gate_keys)
    assert json.loads(registry_path.read_text())["targets"][0]["status"] == "RULED_NOT_PINNED"


def test_single_ruled_year_all_pass_and_commit_promotes_preserving_fields(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    registry_path, target = _setup(monkeypatch, tmp_path, "2020-01-01/2020-12-31", (13, 13))
    benchmark_dir = tmp_path / "benchmarks"
    benchmark_dir.mkdir()
    _write_benchmark(benchmark_dir / "es_2020_monthly_ghi_benchmark.json")
    before = json.loads(registry_path.read_text())["targets"][0]

    decision = _process(tmp_path, target, registry_path, commit=True, benchmark_dir=benchmark_dir)

    assert decision == "PROMOTED"
    after = json.loads(registry_path.read_text())["targets"][0]
    assert after["status"] == "RULED_PINNED"
    assert after["diary_window_status"] == "RULED_PINNED"
    assert after["diary_window"] == "2020-01-01/2020-12-31"
    assert after["weather_file"] and after["sha256"]
    assert after["validation"]["gate_1_header"] == "PASS"
    assert after["validation"]["gate_6_energyplus_smoke"] == "PASS"
    for key in before:
        assert key in after
    assert after["latitude"] == before["latitude"]
    assert after["acquisition_status_note"] == before["acquisition_status_note"]


def test_dry_run_never_touches_registry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    registry_path, target = _setup(monkeypatch, tmp_path, "2020-01-01/2020-12-31", (13, 13))
    benchmark_dir = tmp_path / "benchmarks"
    benchmark_dir.mkdir()
    _write_benchmark(benchmark_dir / "es_2020_monthly_ghi_benchmark.json")
    before_mtime = registry_path.stat().st_mtime_ns
    before_text = registry_path.read_text()

    decision = _process(tmp_path, target, registry_path, commit=False, benchmark_dir=benchmark_dir)

    assert decision == "WOULD_PROMOTE"
    assert registry_path.stat().st_mtime_ns == before_mtime
    assert registry_path.read_text() == before_text


def test_gate5_approval_is_addressable_per_fold_year():
    from scripts.run_eu_t06_weather_promotion import _approved_for, _parse_approved_exceptions

    approved = _parse_approved_exceptions([["es:2009", "12"], ["es:2010", "1"], ["fr", "11"]])
    assert _approved_for(approved, "es", 2009) == [12]
    assert _approved_for(approved, "es", 2010) == [1]
    assert _approved_for(approved, "fr", 2023) == [11]
    assert _approved_for(approved, "uk", 2014) == []


def test_fold_year_approval_overrides_a_fold_wide_one():
    from scripts.run_eu_t06_weather_promotion import _approved_for, _parse_approved_exceptions

    approved = _parse_approved_exceptions([["es", "11"], ["es:2010", "1"]])
    assert _approved_for(approved, "es", 2010) == [1]
    assert _approved_for(approved, "es", 2009) == [11]


def test_malformed_gate5_approval_is_refused():
    import pytest as _pytest

    from scripts.run_eu_t06_weather_promotion import _parse_approved_exceptions

    for bad in ([["es"]], [["es:notayear", "1"]], [["es", "13"]], [["es", "0"]]):
        with _pytest.raises(SystemExit):
            _parse_approved_exceptions(bad)
