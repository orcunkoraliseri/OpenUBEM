"""Acceptance tests for the generated ES/GB/IT TABULA registry."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import pytest

from openubem.data.construction.tabula_registry import ATTRIBUTION, generate_registry
from openubem.semantic.construction_sets import select_tabula_archetype, tabula_period


REPOSITORY_ROOT = Path(__file__).parent.parent
DATA_DIR = REPOSITORY_ROOT / "openubem" / "data" / "construction"
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "eu" / "step8_outputs"
_REFERENCE_CSV_NAME = "tabula_102_extra_columns_2026-08-23.csv"
_REFERENCE_SEARCH_ROOT = (
    REPOSITORY_ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "debugs"
)


def _resolve_reference_csv() -> Path:
    """Resolve the reference table by FILENAME, not by a fixed path prefix.

    The archiving rule this repository adopted on 2026-08-09 requires resolving a
    moved document by its filename: an archive sweep renames the containing folder
    (``docs/`` -> ``DONE/`` -> ``DONE-docs/`` here, twice on 2026-08-26 alone), and
    a hard-coded prefix breaks each time without the file ever changing.
    """
    matches = sorted(_REFERENCE_SEARCH_ROOT.rglob(_REFERENCE_CSV_NAME))
    if not matches:
        raise FileNotFoundError(
            f"{_REFERENCE_CSV_NAME} not found anywhere under {_REFERENCE_SEARCH_ROOT}"
        )
    return matches[0]


REFERENCE_CSV = _resolve_reference_csv()
PARENT_WORKBOOK = Path(
    "C:/Users/o_iseri/Desktop/GSSCanada/GSSCanada-main/4J_docs_occ/"
    "Step8_docs/outputs_step8/raw/tabula-calculator.xlsx"
)


def _records() -> list[dict]:
    records: list[dict] = []
    for country, expected_count in {"es": 24, "gb": 36, "it": 42}.items():
        payload = json.loads((DATA_DIR / f"tabula_archetypes_{country}.json").read_text(encoding="utf-8"))
        assert payload["attribution"] == ATTRIBUTION
        assert len(payload["records"]) == expected_count
        records.extend(payload["records"])
    return records


def _reference_by_id() -> dict[str, dict[str, str]]:
    with REFERENCE_CSV.open(newline="", encoding="utf-8") as source:
        return {row["Code_BuildingVariant"]: row for row in csv.DictReader(source)}


def test_registry_counts_and_boundary_join():
    records = _records()
    assert len(records) == 102
    assert {record["boundary_condition"] for record in records} == {"EU.SUH", "EU.MUH"}
    assert {record["phi_int_w_m2"] for record in records} == {3.0}
    assert {record["c_m_wh_m2k"] for record in records} == {45.0}
    assert {record["n_air_use_h_1"] for record in records} == {0.4}
    assert all(record["license"]["status"] == "VERIFIED" for record in records)
    assert all(record["attribution"] == ATTRIBUTION for record in records)


def test_extracted_numeric_columns_match_102_row_reference():
    records = {record["archetype_id"]: record for record in _records()}
    reference = _reference_by_id()
    assert set(records) == set(reference)
    mappings = {
        "n_Apartment": lambda record: record["n_apartment"],
        "n_air_infiltration": lambda record: record["n_air_infiltration_h_1"],
        "g_gl_n_Window_1": lambda record: record["g_gl_window"],
        "g_gl_n_Window_2": lambda record: record["g_gl_n_window_2"],
        "F_red_temp": lambda record: record["f_red_temp"],
        "h_Transmission": lambda record: record["h_transmission_w_m2k"],
        "h_Ventilation": lambda record: record["h_ventilation_w_m2k"],
        "delta_U_ThermalBridging": lambda record: record["delta_u_tb_w_m2k"],
    }
    b_factor_columns = ("Roof_1", "Roof_2", "Wall_1", "Wall_2", "Wall_3", "Floor_1", "Floor_2")
    for archetype_id, row in reference.items():
        record = records[archetype_id]
        for source_column, lookup in mappings.items():
            assert lookup(record) == pytest.approx(float(row[source_column]))
        for suffix in b_factor_columns:
            generated_key = suffix.lower()
            assert record["transmission_b_factors"][generated_key] == pytest.approx(
                float(row[f"b_Transmission_{suffix}"])
            )


def test_air_and_glazing_invariants():
    records = _records()
    assert Counter(record["n_air_infiltration_h_1"] for record in records) == {
        0.05: 2,
        0.1: 37,
        0.2: 29,
        0.4: 34,
    }
    assert {record["g_gl_window"] for record in records} == {0.67, 0.72, 0.75, 0.76, 0.85}
    assert {record["g_gl_n_window_2"] for record in records} == {0.0}
    for record in records:
        geometry = record["geometry"]
        expected_h_ventilation = (
            0.34
            * (record["n_air_use_h_1"] + record["n_air_infiltration_h_1"])
            * geometry["h_room_m"]
        )
        assert record["h_ventilation_w_m2k"] == pytest.approx(expected_h_ventilation, rel=0.01)


def test_apartment_rounding_and_fold_country_pairs():
    records = _records()
    for record in records:
        if record["building_type"] in {"SFH", "TH"}:
            assert record["n_apartment"] == 1.0
    noninteger = [record for record in records if record["n_apartment"] != round(record["n_apartment"])]
    assert [(record["archetype_id"], record["n_apartment_rounded"]) for record in noninteger] == [
        ("GB.ENG.AB.01.ApartmentBuildings.SyAv.001.001", 7),
        ("GB.ENG.AB.02-03.ApartmentBuildings.SyAv.002.001", 14),
        ("GB.ENG.AB.04-08.ApartmentBuildings.SyAv.005.001", 17),
    ]
    assert {(record["survey_fold"], record["country_stock_code"]) for record in records} == {
        ("es", "ES"),
        ("uk", "GB"),
        ("it", "IT"),
    }


def test_unsourced_geometry_is_explicit_and_provenance_is_present():
    records = _records()
    assert all(
        all(assumption.startswith("UNSOURCED:") for assumption in record["parameter_assumptions"])
        for record in records
    )
    undefined_window_u = [record for record in records if isinstance(record["u_window_w_m2k"], str)]
    assert undefined_window_u
    assert all(record["u_window_w_m2k"].startswith("UNSOURCED:") for record in undefined_window_u)
    provenance = (DATA_DIR / "TABULA_PROVENANCE.md").read_text(encoding="utf-8")
    assert "intended and desired" in provenance
    assert ATTRIBUTION in provenance


@pytest.mark.skipif(not PARENT_WORKBOOK.exists(), reason="Pinned parent calculator workbook is unavailable")
def test_regeneration_is_byte_identical(tmp_path):
    generate_registry(FIXTURE_DIR, PARENT_WORKBOOK, tmp_path)
    for country in ("es", "gb", "it"):
        assert (tmp_path / f"tabula_archetypes_{country}.json").read_bytes() == (
            DATA_DIR / f"tabula_archetypes_{country}.json"
        ).read_bytes()


@pytest.mark.parametrize(
    ("country", "year", "expected"),
    [
        ("ES", 1900, "ES.01"), ("ES", 1901, "ES.02"), ("ES", 1936, "ES.02"),
        ("ES", 1937, "ES.03"), ("ES", 1959, "ES.03"), ("ES", 1960, "ES.04"),
        ("ES", 1979, "ES.04"), ("ES", 1980, "ES.05"), ("ES", 2006, "ES.05"),
        ("ES", 2007, "ES.06"),
        ("GB", 1918, "GB.01"), ("GB", 1919, "GB.02"), ("GB", 1944, "GB.02"),
        ("GB", 1945, "GB.03"), ("GB", 1964, "GB.03"), ("GB", 1965, "GB.04"),
        ("GB", 1980, "GB.04"), ("GB", 1981, "GB.05"), ("GB", 1990, "GB.05"),
        ("GB", 1991, "GB.06"), ("GB", 2003, "GB.06"), ("GB", 2004, "GB.07"),
        ("GB", 2009, "GB.07"), ("GB", 2010, "GB.08"),
        ("IT", 1900, "IT.01"), ("IT", 1901, "IT.02"), ("IT", 1920, "IT.02"),
        ("IT", 1921, "IT.03"), ("IT", 1945, "IT.03"), ("IT", 1946, "IT.04"),
        ("IT", 1960, "IT.04"), ("IT", 1961, "IT.05"), ("IT", 1975, "IT.05"),
        ("IT", 1976, "IT.06"), ("IT", 1990, "IT.06"), ("IT", 1991, "IT.07"),
        ("IT", 2005, "IT.07"), ("IT", 2006, "IT.08"),
    ],
)
def test_tabula_period_at_every_band_edge(country, year, expected):
    assert tabula_period(country, year) == expected


def test_tabula_period_rejects_unknown_country_and_non_integer_year():
    with pytest.raises(ValueError, match="Unsupported TABULA country"):
        tabula_period("DE", 2000)
    with pytest.raises(ValueError, match="year_built"):
        tabula_period("ES", 2000.0)


def test_archetype_selection_refuses_parallel_and_missing_source_cells():
    records = _records()
    with pytest.raises(ValueError, match="ARCHETYPE_NO_MATCH"):
        select_tabula_archetype(records, "GB", "OFFICE", 1920)
    ambiguous = [
        record
        for record in records
        if record["archetype_id"]
        in {
            "GB.ENG.SFH.01.Gen.ReEx.001.001",
            "GB.ENG.SFH.01.Detached.SyAv.001.001",
        }
    ]
    for record in ambiguous:
        record["source_building_code"] = record["source_building_code"].replace(".Gen.", ".Alt.")
    with pytest.raises(ValueError, match="ARCHETYPE_AMBIGUOUS"):
        select_tabula_archetype(ambiguous, "GB", "SFH", 1918)


def test_archetype_selection_recognises_composite_source_codes():
    records = [
        record for record in _records() if "MFH-AB" in record["source_building_type_code"]
    ]
    selected = select_tabula_archetype(records, "IT", "AB", 1921)
    assert selected["archetype_id"] == "IT.MidClim.MFH-AB.01-03.Gen.ReEx.001.001"
