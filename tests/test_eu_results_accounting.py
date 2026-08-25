"""EU-10 four-end-use accounting guard tests."""
from __future__ import annotations

import csv

import pytest

from openubem.results.european_campaign import (
    NON_LEAP_MONTH_HOURS,
    aggregate_european_fold_results,
    assemble_european_cell_result,
    assemble_european_cell_result_from_eplus_csv,
    assemble_four_end_use_result,
    build_european_dossier_report,
    extract_four_end_use_eplus_csv,
    export_european_dossier_report,
    export_european_result_bundle,
)


def test_tabula_dhw_is_labelled_once_and_not_mixed_with_generic_reconstruction():
    result = assemble_four_end_use_result(
        {"heating": 50.0, "cooling": 0.0, "lighting": 10.0, "equipment": 15.0},
        q_w_nd_kwh_m2a=12.0,
    )
    assert result["eui_accounting_mode"] == "four_end_use_tabula_dhw"
    assert result["simulated_four_end_use_eui_kwh_m2"] == 75.0
    assert result["tabula_dhw_eui_kwh_m2"] == 12.0
    assert result["reported_total_eui_kwh_m2"] == 87.0


def test_physical_service_loads_are_rejected_to_prevent_double_counting():
    with pytest.raises(ValueError, match="forbids"):
        assemble_four_end_use_result(
            {"heating": 1.0, "cooling": 0.0, "lighting": 1.0, "equipment": 1.0},
            q_w_nd_kwh_m2a=1.0, physical_service_loads_present=True,
        )


def _consistent_series():
    monthly = [0.0] * 12
    hourly = [0.0] * sum(NON_LEAP_MONTH_HOURS)
    # 75 kWh annual simulated energy, with a 2 kW hourly peak.
    hourly[:37] = [2.0] * 37
    hourly[37] = 1.0
    monthly[0] = 75.0
    return monthly, hourly


def _cell_record(*, cell_id="ES:SFH:01:f0", sensitivity_f=0.0, weather_id="es_madrid_2009_2010"):
    monthly, hourly = _consistent_series()
    return assemble_european_cell_result(
        cell_id=cell_id, archetype_id="ES.N.SFH.01", survey_fold="es", weather_id=weather_id,
        weather_window="2009-2010", sensitivity_f=sensitivity_f, denominator_area_m2=1.0, coefficient_table_checksum="abc123",
        simulated_eui_kwh_m2={"heating": 50.0, "cooling": 0.0, "lighting": 10.0, "equipment": 15.0},
        q_w_nd_kwh_m2a=12.0, monthly_simulated_kwh=monthly, hourly_simulated_kwh=hourly,
    )


def test_cell_result_record_names_weather_window_denominator_and_all_required_time_outputs():
    record = _cell_record()
    assert record["weather_window"] == "2009-2010"
    assert record["annual_simulated_four_end_use_kwh"] == 75.0
    assert len(record["monthly_simulated_four_end_use_kwh"]) == 12
    assert len(record["hourly_simulated_four_end_use_kwh"]) == 8760
    assert record["peak_simulated_four_end_use_kw"] == pytest.approx(2.0)
    assert record["tabula_dhw_eui_kwh_m2"] == 12.0


def test_cell_result_record_rejects_nonclosing_time_series_and_missing_weather_identity():
    monthly, hourly = _consistent_series()
    with pytest.raises(ValueError, match="totals must close"):
        assemble_european_cell_result(
            cell_id="ES:SFH:01:f0", archetype_id="ES.N.SFH.01", survey_fold="es", weather_id="es_madrid_2009_2010",
            weather_window="2009-2010", sensitivity_f=0.0, denominator_area_m2=1.0, coefficient_table_checksum="abc123",
            simulated_eui_kwh_m2={"heating": 50.0, "cooling": 0.0, "lighting": 10.0, "equipment": 15.0},
            q_w_nd_kwh_m2a=12.0, monthly_simulated_kwh=[74.0] + [0.0] * 11, hourly_simulated_kwh=hourly,
        )
    with pytest.raises(ValueError, match="identifiers"):
        assemble_european_cell_result(
            cell_id="ES:SFH:01:f0", archetype_id="ES.N.SFH.01", survey_fold="es", weather_id="",
            weather_window="2009-2010", sensitivity_f=0.0, denominator_area_m2=1.0, coefficient_table_checksum="abc123",
            simulated_eui_kwh_m2={"heating": 50.0, "cooling": 0.0, "lighting": 10.0, "equipment": 15.0},
            q_w_nd_kwh_m2a=12.0, monthly_simulated_kwh=monthly, hourly_simulated_kwh=hourly,
        )


def test_fold_aggregate_and_json_bundle_keep_the_weather_window_and_dhw_separate(tmp_path):
    records = [_cell_record(), _cell_record(cell_id="ES:SFH:01:f015", sensitivity_f=0.15)]
    aggregate = aggregate_european_fold_results(records)
    assert aggregate["cell_count"] == 2
    assert aggregate["weather_window"] == "2009-2010"
    assert aggregate["annual_simulated_four_end_use_kwh"] == 150.0
    assert aggregate["tabula_dhw_eui_kwh_m2"] == 12.0
    path = export_european_result_bundle(records, tmp_path / "result_bundle.json")
    assert path.is_file()
    assert '"schema_version": 1' in path.read_text(encoding="utf-8")


def test_fold_aggregate_rejects_cross_weather_mixing():
    with pytest.raises(ValueError, match="one named fold and weather window"):
        aggregate_european_fold_results([
            _cell_record(), _cell_record(cell_id="ES:SFH:01:f015", sensitivity_f=0.15, weather_id="another_weather"),
        ])


def _write_retained_eplus_csv(path, *, drop_variable=False):
    fields = ["Date/Time"]
    values_by_end_use = {
        "Zone Ideal Loads Zone Total Heating Energy": 3_600_000.0,
        "Zone Ideal Loads Zone Total Cooling Energy": 0.0,
        "Zone Lights Electricity Energy": 1_800_000.0,
        "Zone Electric Equipment Electricity Energy": 1_800_000.0,
    }
    for variable in values_by_end_use:
        if not (drop_variable and variable.startswith("Zone Lights")):
            fields.append("Zone One:{} [J](Hourly)".format(variable))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for month, hours in enumerate(NON_LEAP_MONTH_HOURS, start=1):
            for hour in range(hours):
                row = {"Date/Time": "{:02d}/{:02d}  {:02d}:00:00".format(month, hour // 24 + 1, hour % 24 + 1)}
                for variable, value in values_by_end_use.items():
                    key = "Zone One:{} [J](Hourly)".format(variable)
                    if key in fields:
                        row[key] = value
                writer.writerow(row)


def test_retained_energyplus_csv_extracts_only_four_simulated_end_uses(tmp_path):
    path = tmp_path / "eplusout.csv"
    _write_retained_eplus_csv(path)
    extracted = extract_four_end_use_eplus_csv(path)
    assert extracted["simulated_end_use_kwh"] == pytest.approx({
        "heating": 8760.0, "cooling": 0.0, "lighting": 4380.0, "equipment": 4380.0,
    })
    assert len(extracted["hourly_simulated_four_end_use_kwh"]) == 8760
    assert sum(extracted["monthly_simulated_four_end_use_kwh"]) == pytest.approx(17_520.0)


def test_retained_energyplus_csv_builds_a_validated_cell_record_and_fails_closed(tmp_path):
    path = tmp_path / "eplusout.csv"
    _write_retained_eplus_csv(path)
    record = assemble_european_cell_result_from_eplus_csv(
        path, cell_id="ES:SFH:01:f0", archetype_id="ES.N.SFH.01", survey_fold="es",
        weather_id="es_madrid_2009_2010", weather_window="2009-2010", sensitivity_f=0.0,
        denominator_area_m2=100.0, coefficient_table_checksum="abc123", q_w_nd_kwh_m2a=12.0,
    )
    assert record["simulated_four_end_use_eui_kwh_m2"] == pytest.approx(175.2)
    assert record["peak_simulated_four_end_use_kw"] == pytest.approx(2.0)
    _write_retained_eplus_csv(path, drop_variable=True)
    with pytest.raises(ValueError, match="Zone Lights Electricity Energy"):
        extract_four_end_use_eplus_csv(path)


def _passing_gate_report():
    return [
        {"gate": "G8.{}".format(index), "passed": True, "detail": "fixture", "severity": "hard"}
        for index in (0, *range(1, 17))
    ]


def test_dossier_export_requires_complete_hard_gate_report_and_measured_digests(tmp_path):
    records = [_cell_record()]
    digest = "a" * 64
    report = build_european_dossier_report(
        records, _passing_gate_report(), campaign_manifest_sha256=digest,
        result_bundle_sha256=digest, evidence_scope="local_fixture_contract",
    )
    assert report["schema_version"] == "eu10-dossier/1"
    assert report["evidence_scope"] == "local_fixture_contract"
    assert len(report["gate_report"]) == 17
    path = export_european_dossier_report(
        records, _passing_gate_report(), tmp_path / "dossier.json", campaign_manifest_sha256=digest,
        result_bundle_sha256=digest, evidence_scope="local_fixture_contract",
    )
    assert '"evidence_scope": "local_fixture_contract"' in path.read_text(encoding="utf-8")


def test_dossier_rejects_missing_failed_or_nonhard_gate_results():
    digest = "b" * 64
    incomplete = _passing_gate_report()[:-1]
    with pytest.raises(ValueError, match="missing=G8.16"):
        build_european_dossier_report(
            [_cell_record()], incomplete, campaign_manifest_sha256=digest,
            result_bundle_sha256=digest, evidence_scope="local_fixture_contract",
        )
    failed = _passing_gate_report()
    failed[1]["passed"] = False
    with pytest.raises(ValueError, match="failed=G8.1"):
        build_european_dossier_report(
            [_cell_record()], failed, campaign_manifest_sha256=digest,
            result_bundle_sha256=digest, evidence_scope="local_fixture_contract",
        )
