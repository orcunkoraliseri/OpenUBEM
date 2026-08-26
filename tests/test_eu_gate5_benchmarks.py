"""DR08 gate-5 monthly-GHI benchmark register (FINDING EU-S2-04)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.acquire_pvgis_monthly_ghi_benchmarks import main as acquire_main

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = REPO_ROOT / "openubem" / "data" / "weather" / "benchmarks"
REGISTRY_PATH = REPO_ROOT / "openubem" / "data" / "weather" / "weather_registry.json"

RULED_FRANCE_MONTHLY = [
    37.42, 74.04, 107.01, 134.95, 172.81, 206.59,
    208.6, 171.72, 145.6, 88.91, 42.69, 33.68,
]


def _required_fold_years() -> list[tuple[str, int]]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    required: list[tuple[str, int]] = []
    for target in registry["targets"]:
        start, _, end = target["raw_era5_window"].partition("/")
        for year in range(int(start[:4]), int(end[:4]) + 1):
            required.append((target["fold"], year))
    return required


def test_every_registry_fold_year_has_a_benchmark():
    missing = [
        (fold, year)
        for fold, year in _required_fold_years()
        if not (BENCHMARK_DIR / f"{fold}_{year}_monthly_ghi_benchmark.json").is_file()
    ]
    assert missing == []


@pytest.mark.parametrize("path", sorted(BENCHMARK_DIR.glob("*_monthly_ghi_benchmark.json")))
def test_benchmark_satisfies_the_gate_5_contract(path: Path):
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["schema_version"] == "eu-monthly-ghi-benchmark/1.0"
    assert isinstance(document["source"], str) and document["source"].strip()
    assert document["source_endpoint"].startswith("https://re.jrc.ec.europa.eu/")
    monthly = document["monthly_ghi_kwh_m2"]
    assert len(monthly) == 12
    assert all(isinstance(value, (int, float)) and value > 0 for value in monthly)
    assert path.name == f"{document['fold']}_{document['year']}_monthly_ghi_benchmark.json"


@pytest.mark.parametrize("path", sorted(BENCHMARK_DIR.glob("*_monthly_ghi_benchmark.json")))
def test_benchmark_coordinates_match_the_registry_verbatim(path: Path):
    document = json.loads(path.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    target = next(t for t in registry["targets"] if t["fold"] == document["fold"])
    assert (document["latitude"], document["longitude"]) == (
        target["latitude"], target["longitude"],
    )


def test_the_ruled_france_benchmark_is_unchanged():
    document = json.loads(
        (BENCHMARK_DIR / "fr_2023_monthly_ghi_benchmark.json").read_text(encoding="utf-8")
    )
    assert document["monthly_ghi_kwh_m2"] == RULED_FRANCE_MONTHLY
    assert document["approved_exception_months"] == [11]


def test_acquisition_refuses_to_requery_the_ruled_france_benchmark(capsys):
    assert acquire_main(["--folds", "fr"]) == 1
    assert "RULED_TRANSCRIBED_BENCHMARK_NOT_REQUERIED" in capsys.readouterr().out


def test_acquisition_does_not_touch_the_network_when_files_exist(capsys):
    assert acquire_main([]) == 0
    output = capsys.readouterr().out
    assert output.count("SKIP") == 6
    assert "WROTE" not in output


def test_gate_5_reproduces_the_ruled_france_verdict():
    """The ruling recorded 11 of 12 within 10 %, November 13.8 %, annual 3.2 %."""
    from openubem.acquisition import european_weather as ew

    result = ew.evaluate_monthly_benchmark_gate(
        REPO_ROOT / "openubem" / "data" / "weather" / "fr_lyon_bron_2023_era5.epw",
        BENCHMARK_DIR / "fr_2023_monthly_ghi_benchmark.json",
        tolerance_pct=10.0,
        approved_exception_months=[11],
    )
    assert result["verdict"] == "PASS_WITH_DOCUMENTED_EXCEPTION"
    months = result["monthly"]
    assert [row["month"] for row in months] == list(range(1, 13))
    assert result["offending_months"] == [11]
    assert result["approved_exception_months"] == [11]
    november = next(row for row in months if row["month"] == 11)
    assert november["pct_difference"] == pytest.approx(13.8, abs=0.1)
    epw_annual = sum(row["epw_ghi_kwh_m2"] for row in months)
    benchmark_annual = sum(row["benchmark_ghi_kwh_m2"] for row in months)
    annual_pct = abs(epw_annual - benchmark_annual) / benchmark_annual * 100.0
    assert annual_pct == pytest.approx(3.2, abs=0.1)
