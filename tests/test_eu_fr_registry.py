"""France physical-registry checks for X-08."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import pytest

from openubem.data.construction.tabula_registry import generate_fr_registry
from openubem.semantic.construction_sets import tabula_period


ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "openubem" / "data" / "construction"
WORKBOOK = Path("C:/Users/o_iseri/Desktop/GSSCanada/GSSCanada-main/4J_docs_occ/Step8_docs/outputs_step8/raw/tabula-calculator.xlsx")


def _records():
    return json.loads((DATA_DIR / "tabula_archetypes_fr.json").read_text(encoding="utf-8"))["records"]


def test_fr_registry_is_the_40_row_national_grid():
    records = _records()
    assert len(records) == 40
    assert Counter(record["building_type"] for record in records) == {"AB": 10, "MFH": 10, "SFH": 10, "TH": 10}
    assert {record["construction_period"] for record in records} == {f"FR.{index:02d}" for index in range(1, 11)}
    assert {record["boundary_condition"] for record in records} == {"EU.SUH", "EU.MUH"}
    assert all(record["survey_fold"] == "fr" for record in records)


def test_fr_ophm_rows_are_excluded_with_reasons():
    with (DATA_DIR / "tabula_archetypes_fr_exclusions.csv").open(newline="", encoding="utf-8") as source:
        exclusions = list(csv.DictReader(source))
    assert len(exclusions) == 10
    assert all(row["archetype_id"].startswith("FR.OPHM.") for row in exclusions)
    assert all("FR.MUH-DPE1" in row["reason"] for row in exclusions)


def test_fr_mfh_08_native_anomaly_is_preserved_literally():
    record = next(record for record in _records() if record["archetype_id"] == "FR.N.MFH.08.Gen.ReEx.001.001")
    assert record["n_apartment"] == 1.0
    assert record["geometry"]["n_storey"] == 1.0
    assert record["geometry"]["a_c_ref_m2"] == pytest.approx(497.2)


@pytest.mark.parametrize("year, expected", [(1914, "FR.01"), (1915, "FR.02"), (1999, "FR.07"), (2000, "FR.08"), (2012, "FR.09"), (2013, "FR.10")])
def test_fr_period_boundaries(year, expected):
    assert tabula_period("FR", year) == expected


@pytest.mark.skipif(not WORKBOOK.exists(), reason="Pinned parent calculator workbook is unavailable")
def test_fr_regeneration_is_byte_identical(tmp_path):
    generated = generate_fr_registry(WORKBOOK, tmp_path)
    assert generated.read_bytes() == (DATA_DIR / "tabula_archetypes_fr.json").read_bytes()
