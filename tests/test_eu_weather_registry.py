"""Offline tests for the EU-07 weather registry pre-acquisition state."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from openubem.acquisition.european_weather import (
    cds_credentials_configured,
    ruled_not_pinned_registry,
    validate_epw_preflight,
    write_ruled_not_pinned_registry,
)


def _valid_epw(path: Path) -> None:
    header = [
        "LOCATION,Test,State,Country,Source,000000,40.0,-3.0,1.0,100.0",
        "DESIGN CONDITIONS,0", "TYPICAL/EXTREME PERIODS,0", "GROUND TEMPERATURES,0",
        "HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0", "COMMENTS 1,synthetic test only",
        "COMMENTS 2,no weather data claim", "DATA PERIODS,1,1,Data,Sunday,1/1,12/31",
    ]
    rows = []
    for stamp in __import__("pandas").date_range("2001-01-01", periods=8760, freq="h"):
        fields = ["2001", str(stamp.month), str(stamp.day), str(stamp.hour + 1), "60", "0",
                  "10", "5", "50", "101325", "0", "0", "0", "0", "0", "0", "0", "0",
                  "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
                  "0", "0", "0", "0"]
        rows.append(",".join(fields))
    path.write_text("\n".join(header + rows) + "\n", encoding="utf-8")


def test_registry_is_explicitly_ruled_not_pinned_and_has_three_targets():
    registry = ruled_not_pinned_registry()
    assert registry["status"] == "RULED_NOT_PINNED"
    assert [target["fold"] for target in registry["targets"]] == ["es", "uk", "it"]
    assert all(target["weather_file"] is None for target in registry["targets"])
    assert all(target["licence_status"] == "CAPTURE_AT_DOWNLOAD" for target in registry["targets"])


def test_credential_check_never_needs_to_read_a_secret(tmp_path: Path):
    assert not cds_credentials_configured(environ={}, home=tmp_path)
    assert cds_credentials_configured(environ={"CDSAPI_KEY": "configured"}, home=tmp_path)
    (tmp_path / ".cdsapirc").write_text("credentials exist", encoding="utf-8")
    assert cds_credentials_configured(environ={}, home=tmp_path)


def test_template_write_refuses_to_replace_an_acquired_registry(tmp_path: Path):
    path = write_ruled_not_pinned_registry(tmp_path / "weather_registry.json")
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "RULED_NOT_PINNED"
    path.write_text('{"status": "ACQUIRED"}', encoding="utf-8")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        write_ruled_not_pinned_registry(path)


def test_committed_registry_preserves_template_targets_and_records_lyon_promotion():
    committed = Path(__file__).parents[1] / "openubem" / "data" / "weather" / "weather_registry.json"
    registry = json.loads(committed.read_text(encoding="utf-8"))
    # FINDING EU-S2-09: the top-level status moves every time a fold is promoted, so
    # pinning its literal value couples this test to a mutable ruled data file. Assert
    # the invariant instead -- the label must agree with the per-fold statuses it
    # summarises. This is stricter than the literal, not weaker: it also fails on a
    # stale label, which a literal assertion silently permits after a promotion.
    pinned_statuses = {"RULED_PINNED", "RULED_PINNED_EXCEPTION"}
    pinned = [t for t in registry["targets"] if t["status"] in pinned_statuses]
    if len(pinned) == len(registry["targets"]):
        assert registry["status"] == "FULLY_PINNED"
    elif pinned:
        assert registry["status"] == "PARTIALLY_PINNED"
    else:
        assert registry["status"] == "RULED_NOT_PINNED"
    assert [target["fold"] for target in registry["targets"][:3]] == ["fr", "es", "uk"]
    lyon = registry["targets"][0]
    assert lyon["status"] == "RULED_PINNED_EXCEPTION"
    assert lyon["validation"]["gate_6_energyplus_smoke"] == "PASS"
    assert lyon["validation"]["gate_5_monthly_national_benchmark"] == "PASS_WITH_DOCUMENTED_NOVEMBER_EXCEPTION"
    template = ruled_not_pinned_registry()
    assert [target["fold"] for target in template["targets"]] == ["es", "uk", "it"]


def test_preflight_accepts_well_formed_nonleap_epw(tmp_path: Path):
    path = tmp_path / "valid.epw"
    _valid_epw(path)
    result = validate_epw_preflight(path)
    assert result["gate_1_header"] == "PASS"
    assert result["gate_4_physical_and_solar_bounds"] == "PASS"
    assert result["gate_5_monthly_national_benchmark"] == "PENDING_EXTERNAL_BENCHMARK"


def test_preflight_rejects_dewpoint_above_drybulb(tmp_path: Path):
    path = tmp_path / "invalid.epw"
    _valid_epw(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    fields = lines[8].split(",")
    fields[7] = "11"
    lines[8] = ",".join(fields)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="dew point"):
        validate_epw_preflight(path)
