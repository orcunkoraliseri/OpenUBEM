"""European Step 8 four-end-use accounting safeguards."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Iterable, Mapping


EUROPEAN_ACCOUNTING_MODE = "four_end_use_tabula_dhw"
SIMULATED_END_USES = ("heating", "cooling", "lighting", "equipment")
NON_LEAP_MONTH_HOURS = (744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744)
EUROPEAN_GATE_IDS = ("G8.0",) + tuple("G8.{}".format(index) for index in range(1, 17))
DOSSIER_EVIDENCE_SCOPES = ("local_fixture_contract", "retained_campaign")
ENERGYPLUS_J_TO_KWH = 1.0 / 3.6e6
FOUR_END_USE_OUTPUT_VARIABLES = {
    "heating": "Zone Ideal Loads Zone Total Heating Energy",
    "cooling": "Zone Ideal Loads Zone Total Cooling Energy",
    "lighting": "Zone Lights Electricity Energy",
    "equipment": "Zone Electric Equipment Electricity Energy",
}


def _energyplus_columns(fieldnames: Iterable[str], variable_name: str) -> tuple[str, ...]:
    """Select retained hourly EnergyPlus J columns for one exact output variable."""
    required = variable_name.casefold()
    columns = tuple(
        field for field in fieldnames
        if required in field.casefold() and "[j]" in field.casefold() and "(hourly)" in field.casefold()
    )
    if not columns:
        raise ValueError("retained EnergyPlus CSV lacks hourly J output: {}".format(variable_name))
    return columns


def extract_four_end_use_eplus_csv(csv_path: Path | str) -> dict[str, object]:
    """Read the ruled four simulated end uses from a retained ``eplusout.csv``.

    The extractor is deliberately read-only and does not use facility or
    service-load meters.  It sums every retained zone column for each of the
    four configured EnergyPlus variables, converts J to kWh at the boundary,
    and rejects a non-hourly/non-leap result before it can enter EU-10.
    """
    source = Path(csv_path)
    if not source.is_file():
        raise ValueError("retained EnergyPlus CSV does not exist: {}".format(source))
    with source.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "Date/Time" not in reader.fieldnames:
            raise ValueError("retained EnergyPlus CSV requires a Date/Time column")
        columns = {
            end_use: _energyplus_columns(reader.fieldnames, variable)
            for end_use, variable in FOUR_END_USE_OUTPUT_VARIABLES.items()
        }
        monthly_by_end_use = {end_use: [0.0] * 12 for end_use in SIMULATED_END_USES}
        hourly_total: list[float] = []
        for row_number, row in enumerate(reader, start=2):
            timestamp = str(row.get("Date/Time", "")).strip()
            try:
                month = int(timestamp[:2])
            except ValueError as exc:
                raise ValueError("row {} has invalid EnergyPlus Date/Time: {!r}".format(row_number, timestamp)) from exc
            if month not in range(1, 13):
                raise ValueError("row {} has invalid EnergyPlus month: {!r}".format(row_number, timestamp))
            end_use_values: dict[str, float] = {}
            for end_use, matching_columns in columns.items():
                try:
                    value_j = sum(float(row[column]) for column in matching_columns)
                except (TypeError, ValueError) as exc:
                    raise ValueError("row {} has invalid {} energy value".format(row_number, end_use)) from exc
                if not math.isfinite(value_j) or value_j < 0:
                    raise ValueError("row {} has invalid {} energy value".format(row_number, end_use))
                value_kwh = value_j * ENERGYPLUS_J_TO_KWH
                end_use_values[end_use] = value_kwh
                monthly_by_end_use[end_use][month - 1] += value_kwh
            hourly_total.append(sum(end_use_values.values()))
    if len(hourly_total) != sum(NON_LEAP_MONTH_HOURS):
        raise ValueError("retained EnergyPlus CSV requires exactly 8760 hourly rows")
    monthly_total = tuple(sum(monthly_by_end_use[end_use][month] for end_use in SIMULATED_END_USES) for month in range(12))
    expected_month_hours = tuple(NON_LEAP_MONTH_HOURS)
    observed_month_hours = [0] * 12
    # The timestamp month was already validated while streaming. Reopen only
    # for a cheap, explicit calendar count instead of retaining 8,760 labels.
    with source.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            observed_month_hours[int(str(row["Date/Time"]).strip()[:2]) - 1] += 1
    if tuple(observed_month_hours) != expected_month_hours:
        raise ValueError("retained EnergyPlus CSV month row counts are not the required non-leap calendar")
    annual_by_end_use = {
        end_use: sum(monthly_by_end_use[end_use])
        for end_use in SIMULATED_END_USES
    }
    return {
        "source_csv": str(source),
        "simulated_end_use_kwh": annual_by_end_use,
        "monthly_simulated_four_end_use_kwh": monthly_total,
        "hourly_simulated_four_end_use_kwh": tuple(hourly_total),
    }


def assemble_european_cell_result_from_eplus_csv(
    csv_path: Path | str,
    *,
    cell_id: str,
    archetype_id: str,
    survey_fold: str,
    weather_id: str,
    weather_window: str,
    sensitivity_f: float,
    denominator_area_m2: float,
    coefficient_table_checksum: str,
    q_w_nd_kwh_m2a: float,
) -> dict[str, object]:
    """Extract one retained output and build its validated EU-10 cell record."""
    extracted = extract_four_end_use_eplus_csv(csv_path)
    area = float(denominator_area_m2)
    if not math.isfinite(area) or area <= 0:
        raise ValueError("denominator_area_m2 must be finite and positive")
    end_uses = {
        end_use: float(extracted["simulated_end_use_kwh"][end_use]) / area
        for end_use in SIMULATED_END_USES
    }
    return assemble_european_cell_result(
        cell_id=cell_id,
        archetype_id=archetype_id,
        survey_fold=survey_fold,
        weather_id=weather_id,
        weather_window=weather_window,
        sensitivity_f=sensitivity_f,
        denominator_area_m2=area,
        coefficient_table_checksum=coefficient_table_checksum,
        simulated_eui_kwh_m2=end_uses,
        q_w_nd_kwh_m2a=q_w_nd_kwh_m2a,
        monthly_simulated_kwh=extracted["monthly_simulated_four_end_use_kwh"],
        hourly_simulated_kwh=extracted["hourly_simulated_four_end_use_kwh"],
    )


def assemble_four_end_use_result(
    simulated_eui_kwh_m2: Mapping[str, float], *, q_w_nd_kwh_m2a: float,
    physical_service_loads_present: bool = False,
) -> dict[str, object]:
    """Return a labelled Step 8 result without reconstructing service loads.

    The accepted European accounting ruling keeps the four simulated end uses
    separate and reports TABULA ``q_w_nd`` as a DHW post-processed column.  It
    must not be combined with physical service loads or a generic fraction
    reconstruction, both of which would double-count energy.
    """
    if physical_service_loads_present:
        raise ValueError("four_end_use_tabula_dhw forbids physically modelled service loads")
    if set(simulated_eui_kwh_m2) != set(SIMULATED_END_USES):
        raise ValueError("simulated EUI must contain exactly heating, cooling, lighting, and equipment")
    values = {key: float(simulated_eui_kwh_m2[key]) for key in SIMULATED_END_USES}
    dhw = float(q_w_nd_kwh_m2a)
    if not all(math.isfinite(value) and value >= 0 for value in (*values.values(), dhw)):
        raise ValueError("all simulated end uses and q_w_nd must be finite and non-negative")
    simulated_total = sum(values.values())
    return {
        "eui_accounting_mode": EUROPEAN_ACCOUNTING_MODE,
        "simulated_end_uses": SIMULATED_END_USES,
        "reconstructed_end_uses": ("tabula_dhw",),
        **{f"{key}_eui_kwh_m2": value for key, value in values.items()},
        "simulated_four_end_use_eui_kwh_m2": simulated_total,
        "tabula_dhw_eui_kwh_m2": dhw,
        "reported_total_eui_kwh_m2": simulated_total + dhw,
    }


def assemble_european_cell_result(
    *,
    cell_id: str,
    archetype_id: str,
    survey_fold: str,
    weather_id: str,
    weather_window: str,
    sensitivity_f: float,
    denominator_area_m2: float,
    coefficient_table_checksum: str,
    simulated_eui_kwh_m2: Mapping[str, float],
    q_w_nd_kwh_m2a: float,
    monthly_simulated_kwh: tuple[float, ...] | list[float],
    hourly_simulated_kwh: tuple[float, ...] | list[float],
    physical_service_loads_present: bool = False,
) -> dict[str, object]:
    """Assemble a self-describing EU-10 cell record from retained result series.

    Monthly and hourly series deliberately cover only the four simulated end
    uses.  TABULA DHW remains a separately labelled post-processing result, so
    its annual intensity cannot silently appear in a simulated peak or time
    series.  This is a contract layer, not a SQL extractor: callers must pass
    the actual retained EnergyPlus series.
    """
    identifiers = {
        "cell_id": str(cell_id).strip(),
        "archetype_id": str(archetype_id).strip(),
        "survey_fold": str(survey_fold).strip().casefold(),
        "weather_id": str(weather_id).strip(),
        "weather_window": str(weather_window).strip(),
        "coefficient_table_checksum": str(coefficient_table_checksum).strip(),
    }
    if not all(identifiers.values()):
        raise ValueError("cell, archetype, fold, weather window, and coefficient checksum identifiers are required")
    sensitivity = float(sensitivity_f)
    if not math.isfinite(sensitivity) or not 0 <= sensitivity <= 1:
        raise ValueError("sensitivity_f must be finite and between zero and one")
    area = float(denominator_area_m2)
    if not math.isfinite(area) or area <= 0:
        raise ValueError("denominator_area_m2 must be finite and positive")
    monthly = tuple(float(value) for value in monthly_simulated_kwh)
    hourly = tuple(float(value) for value in hourly_simulated_kwh)
    if len(monthly) != 12 or len(hourly) != sum(NON_LEAP_MONTH_HOURS):
        raise ValueError("EU-10 requires 12 monthly and 8760 hourly non-leap simulated-energy values")
    if not all(math.isfinite(value) and value >= 0 for value in monthly + hourly):
        raise ValueError("monthly and hourly simulated-energy values must be finite and non-negative")
    if not math.isclose(sum(monthly), sum(hourly), rel_tol=1e-9, abs_tol=1e-6):
        raise ValueError("monthly and hourly simulated-energy totals must close")
    accounting = assemble_four_end_use_result(
        simulated_eui_kwh_m2,
        q_w_nd_kwh_m2a=q_w_nd_kwh_m2a,
        physical_service_loads_present=physical_service_loads_present,
    )
    annual_simulated = float(accounting["simulated_four_end_use_eui_kwh_m2"]) * area
    if not math.isclose(sum(hourly), annual_simulated, rel_tol=1e-9, abs_tol=1e-6):
        raise ValueError("hourly simulated-energy total must equal four-end-use annual EUI times denominator")
    return {
        **identifiers,
        "sensitivity_f": sensitivity,
        "denominator_area_m2": area,
        **accounting,
        "annual_simulated_four_end_use_kwh": annual_simulated,
        "monthly_simulated_four_end_use_kwh": monthly,
        "hourly_simulated_four_end_use_kwh": hourly,
        "peak_simulated_four_end_use_kw": max(hourly),
    }


def aggregate_european_fold_results(records: Iterable[Mapping[str, object]]) -> dict[str, object]:
    """Aggregate validated cell records for exactly one fold and weather window.

    This enforces the pre-registered reporting rule: headline occupant effects
    are within fold.  Cross-fold absolute comparisons must be made explicitly
    elsewhere with their weather windows named, never by this convenience
    aggregator.
    """
    rows = list(records)
    if not rows:
        raise ValueError("at least one validated European cell result is required")
    cell_ids = [str(row.get("cell_id", "")) for row in rows]
    if any(not cell_id for cell_id in cell_ids) or len(set(cell_ids)) != len(cell_ids):
        raise ValueError("aggregate records require unique non-empty cell_id values")
    contexts = {
        (str(row.get("survey_fold", "")), str(row.get("weather_id", "")), str(row.get("weather_window", "")))
        for row in rows
    }
    if len(contexts) != 1 or not all(contexts.pop()):
        raise ValueError("aggregate is restricted to one named fold and weather window")
    fold, weather_id, weather_window = next(iter({
        (str(row["survey_fold"]), str(row["weather_id"]), str(row["weather_window"])) for row in rows
    }))
    if any(row.get("eui_accounting_mode") != EUROPEAN_ACCOUNTING_MODE for row in rows):
        raise ValueError("aggregate records must use the ruled four_end_use_tabula_dhw mode")
    areas = [float(row["denominator_area_m2"]) for row in rows]
    annual = [float(row["annual_simulated_four_end_use_kwh"]) for row in rows]
    monthly = [tuple(float(value) for value in row["monthly_simulated_four_end_use_kwh"]) for row in rows]
    hourly = [tuple(float(value) for value in row["hourly_simulated_four_end_use_kwh"]) for row in rows]
    if not all(math.isfinite(value) and value > 0 for value in areas + annual):
        raise ValueError("aggregate areas and annual simulated energy must be finite and positive")
    if any(len(values) != 12 for values in monthly) or any(len(values) != 8760 for values in hourly):
        raise ValueError("aggregate records must retain 12 monthly and 8760 hourly values")
    total_area = sum(areas)
    monthly_total = tuple(sum(values[index] for values in monthly) for index in range(12))
    hourly_total = tuple(sum(values[index] for values in hourly) for index in range(8760))
    if not math.isclose(sum(annual), sum(hourly_total), rel_tol=1e-9, abs_tol=1e-6):
        raise ValueError("aggregate annual and hourly simulated energy must close")
    return {
        "survey_fold": fold,
        "weather_id": weather_id,
        "weather_window": weather_window,
        "cell_count": len(rows),
        "denominator_area_m2": total_area,
        "annual_simulated_four_end_use_kwh": sum(annual),
        "simulated_four_end_use_eui_kwh_m2": sum(annual) / total_area,
        "tabula_dhw_eui_kwh_m2": sum(float(row["tabula_dhw_eui_kwh_m2"]) * area for row, area in zip(rows, areas)) / total_area,
        "reported_total_eui_kwh_m2": sum(float(row["reported_total_eui_kwh_m2"]) * area for row, area in zip(rows, areas)) / total_area,
        "monthly_simulated_four_end_use_kwh": monthly_total,
        "hourly_simulated_four_end_use_kwh": hourly_total,
        "peak_simulated_four_end_use_kw": max(hourly_total),
    }


def export_european_result_bundle(records: Iterable[Mapping[str, object]], destination: Path | str) -> Path:
    """Write a deterministic JSON bundle after within-fold aggregation validates it."""
    rows = list(records)
    aggregate = aggregate_european_fold_results(rows)
    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(
        json.dumps({"schema_version": 1, "aggregate": aggregate, "cells": rows}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
    return output


def _required_sha256(value: str, label: str) -> str:
    digest = str(value).strip().casefold()
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("{} must be a measured SHA-256 hex digest".format(label))
    return digest


def build_european_dossier_report(
    records: Iterable[Mapping[str, object]],
    gate_findings: Iterable[Mapping[str, object]],
    *,
    campaign_manifest_sha256: str,
    result_bundle_sha256: str,
    evidence_scope: str,
) -> dict[str, object]:
    """Build a fail-closed, machine-readable EU-10 dossier report.

    A fixture-contract report is useful for testing the schema but is not a
    campaign claim.  A caller may use ``retained_campaign`` only after the
    supplied digests are measured from its retained campaign manifest and
    result bundle.  This function never infers either scope from filenames.
    """
    scope = str(evidence_scope).strip()
    if scope not in DOSSIER_EVIDENCE_SCOPES:
        raise ValueError("evidence_scope must be local_fixture_contract or retained_campaign")
    aggregate = aggregate_european_fold_results(records)
    report: dict[str, dict[str, object]] = {}
    for finding in gate_findings:
        gate = str(finding.get("gate", "")).strip()
        if not gate or gate in report:
            raise ValueError("dossier requires one non-empty gate finding per gate")
        report[gate] = {
            "gate": gate,
            "passed": bool(finding.get("passed", False)),
            "detail": str(finding.get("detail", "")),
            "severity": str(finding.get("severity", "")),
        }
    if set(report) != set(EUROPEAN_GATE_IDS):
        missing = ", ".join(sorted(set(EUROPEAN_GATE_IDS) - set(report))) or "none"
        extra = ", ".join(sorted(set(report) - set(EUROPEAN_GATE_IDS))) or "none"
        raise ValueError("dossier gate report must contain G8.0-G8.16 exactly; missing={} extra={}".format(missing, extra))
    non_passing = sorted(gate for gate, finding in report.items() if not finding["passed"])
    non_hard = sorted(gate for gate, finding in report.items() if finding["severity"] != "hard")
    if non_passing or non_hard:
        raise ValueError("dossier requires all hard gates to pass; failed={} non_hard={}".format(
            ", ".join(non_passing) or "none", ", ".join(non_hard) or "none",
        ))
    return {
        "schema_version": "eu10-dossier/1",
        "evidence_scope": scope,
        "campaign_manifest_sha256": _required_sha256(campaign_manifest_sha256, "campaign_manifest_sha256"),
        "result_bundle_sha256": _required_sha256(result_bundle_sha256, "result_bundle_sha256"),
        "aggregate": aggregate,
        "gate_report": tuple(report[gate] for gate in EUROPEAN_GATE_IDS),
    }


def export_european_dossier_report(
    records: Iterable[Mapping[str, object]],
    gate_findings: Iterable[Mapping[str, object]],
    destination: Path | str,
    *,
    campaign_manifest_sha256: str,
    result_bundle_sha256: str,
    evidence_scope: str,
) -> Path:
    """Atomically write a deterministic machine-readable EU-10 dossier report."""
    report = build_european_dossier_report(
        records,
        gate_findings,
        campaign_manifest_sha256=campaign_manifest_sha256,
        result_bundle_sha256=result_bundle_sha256,
        evidence_scope=evidence_scope,
    )
    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    return output
